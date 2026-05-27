from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pickle
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor  # Parallel fetching ke liye

app = FastAPI(title="Movie Recommender API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model load karna
try:
    new_df = pickle.load(open('movies.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    print("✅ Models loaded successfully!")
except Exception as e:
    print("⚠️ Error: Check if movies.pkl and similarity.pkl are in the same folder.")

TMDB_API_KEY = "88ce67a5b71f14307410e80933b2ce81"

def fetch_poster_and_details(movie_name):
    """Single movie ke details fetch karne ka helper function"""
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    try:
        response = requests.get(url).json()
        if response.get("results"):
            best_match = response["results"][0]
            return {
                "title": movie_name,
                "poster_path": best_match.get("poster_path"),
                "vote_average": float(best_match.get("vote_average", 7.4)),
                "release_date": best_match.get("release_date", "2025-01-01"),
                "backdrop_path": best_match.get("backdrop_path")
            }
    except Exception:
        pass
    return {"title": movie_name, "poster_path": None, "vote_average": 7.4, "release_date": "2025-01-01", "backdrop_path": None}

@app.get("/")
def home():
    return {"message": "Movie Recommendation API is running successfully! 🚀"}

# 🔥 UPDATED: Ab ye tumhare khud ke database se 50 random movies nikalega
@app.get("/trending")
def get_trending_movies():
    try:
        # Database se 75 movies ka random sample lete hain (taaki poster na hone par backup rahe)
        sample_size = min(75, len(new_df))
        random_titles = new_df.sample(n=sample_size)['title'].tolist()
        
        # ThreadPoolExecutor se 10-10 requests ek saath parallel chalengi (Super Fast ⚡)
        with ThreadPoolExecutor(max_workers=15) as executor:
            results = list(executor.map(fetch_poster_and_details, random_titles))
        
        # Jin movies ke posters mil gaye hain, unhe filter karke sahi 50 select kar lo
        valid_movies = [m for m in results if m["poster_path"] is not None]
        return valid_movies[:50]
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/recommend")
def recommend_movie(movie: str):
    try:
        movie_index = new_df[new_df['title'].str.lower() == movie.lower()].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        recommended_movies = []
        for i in movies_list:
            movie_name = new_df.iloc[i[0]].title
            url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
            try:
                res = requests.get(url).json()
                if res.get("results"):
                    best_match = res["results"][0]
                    poster_path = best_match.get("poster_path")
                    recommended_movies.append({
                        "name": movie_name,
                        "poster": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                        "rating": round(best_match.get("vote_average", 7.4), 1),
                        "year": best_match.get("release_date", "AI").split("-")[0]
                    })
            except Exception:
                recommended_movies.append({"name": movie_name, "poster": None, "rating": "8.0", "year": "AI"})
                
        return {"searched_movie": movie, "recommendations": recommended_movies}
    except IndexError:
        return {"error": f"Bhai, '{movie}' hamare database me nahi mili! Koi aur Hollywood movie try karo."}
