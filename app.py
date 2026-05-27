import streamlit as st
import pickle
import pandas as pd
import requests 

# --- Configuration ---
# Your TMDB API Key
TMDB_API_KEY = "88ce67a5b71f14307410e80933b2ce81"

# Configure the Streamlit page layout to wide mode for a cinematic look
st.set_page_config(page_title="Netflix Clone Recommender", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS for Premium UI ---
st.markdown("""
    <style>
    /* Main background color */
    .stApp {
        background-color: #0b0b0b;
        color: white;
    }
    
    /* Headings styling (Netflix Red) */
    h1, h2, h3 {
        color: #E50914 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
    }
    
    /* Movie Titles and Details */
    .movie-title {
        text-align: center;
        font-size: 15px;
        font-weight: bold;
        color: #ffffff;
        margin-top: 8px;
    }
    
    .movie-details {
        text-align: center;
        font-size: 13px;
        color: #aaaaaa;
        margin-bottom: 15px;
    }
    
    /* Banner Image Styling */
    .banner-container {
        width: 100%;
        max-height: 400px;
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0px 4px 15px rgba(229, 9, 20, 0.3);
    }
    
    .banner-img {
        width: 100%;
        object-fit: cover;
        opacity: 0.8;
    }
    
    /* Hide default Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 1. Load Data ---
@st.cache_data
def load_data():
    try:
        movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
        movies_df = pd.DataFrame(movies_dict)
        sim_matrix = pickle.load(open('similarity.pkl', 'rb'))
        return movies_df, sim_matrix
    except Exception as e:
        st.error("⚠️ Error: Check if movie_dict.pkl and similarity.pkl are in the folder.")
        return None, None

movies, similarity = load_data()

# --- 2. Fetch Advanced Movie Details ---
# Cached to avoid hitting the API multiple times for the same movie
@st.cache_data
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=3).json()
        
        # Extracting details with fallbacks
        poster_path = response.get('poster_path')
        backdrop_path = response.get('backdrop_path')
        
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://placehold.co/500x750/141414/E50914?text=No+Poster"
        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
        
        rating = round(response.get('vote_average', 0.0), 1)
        release_date = response.get('release_date', 'N/A')
        year = release_date.split('-')[0] if release_date != 'N/A' else 'N/A'
        
        return poster_url, backdrop_url, rating, year
        
    except Exception as e:
        return "https://placehold.co/500x750/141414/E50914?text=Network+Error", None, 0.0, "N/A"

# --- 3. Recommendation Engine ---
def recommend(movie_title):
    movie_index = movies[movies['title'] == movie_title].index[0]
    distances = similarity[movie_index]
    
    # Top 5 similar movies
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommendations = []
    
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        poster, _, rating, year = fetch_movie_details(movie_id)
        
        recommendations.append({
            "title": title,
            "poster": poster,
            "rating": rating,
            "year": year
        })
        
    return recommendations

# --- 4. Application UI ---

st.title('🎬MOVIE RECOMMENDATION')

# Search bar layout
movie_list = ["-- Select a Movie --"] + list(movies['title'].values)
selected_movie = st.selectbox("Find your next favorite movie", movie_list)

# --- Recommendation Section ---
if selected_movie != "-- Select a Movie --":
    
    # Fetch details for the selected movie to get the background banner
    selected_movie_id = movies[movies['title'] == selected_movie].iloc[0].movie_id
    _, banner_img, _, _ = fetch_movie_details(selected_movie_id)
    
    # Display the Banner Image if available
    if banner_img:
        st.markdown(f"""
            <div class="banner-container">
                <img src="{banner_img}" class="banner-img">
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"### Because you watched **{selected_movie}**")
    st.markdown("<h4 style='color: white;'>More Like This:</h4>", unsafe_allow_html=True)
    
    recs = recommend(selected_movie)
    
    # Display 5 recommendations in a grid
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.image(recs[idx]["poster"], use_container_width=True)
            st.markdown(f"<div class='movie-title'>{recs[idx]['title']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='movie-details'>⭐ {recs[idx]['rating']} | 📅 {recs[idx]['year']}</div>", unsafe_allow_html=True)

# --- Home Page Section (Trending Now) ---
else:
    st.markdown("---")
    st.markdown("### 🍿 Trending Now")
    
    # Display top 20 movies
    trending_movies = movies.head(20)
    
    for row in range(4):
        cols = st.columns(5)
        for col_idx in range(5):
            movie_idx = row * 5 + col_idx
            movie_id = trending_movies.iloc[movie_idx].movie_id
            title = trending_movies.iloc[movie_idx].title
            
            poster, _, rating, year = fetch_movie_details(movie_id)
            
            with cols[col_idx]:
                st.image(poster, use_container_width=True)
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-details'>⭐ {rating} | 📅 {year}</div>", unsafe_allow_html=True)
