import streamlit as st
import pickle
import pandas as pd
import requests 

# --- Configuration ---
# Your TMDB API Key
TMDB_API_KEY = "a1e923f47a11306f96049e7589ae47e7"

# Configure the Streamlit page layout to wide mode for a cinematic look
st.set_page_config(page_title="Netflix Clone Recommender", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS for Netflix UI ---
# This CSS changes the background to dark, text to white, and highlights to Netflix Red
st.markdown("""
    <style>
    /* Main background color */
    .stApp {
        background-color: #141414;
        color: white;
    }
    
    /* Headings styling (Netflix Red) */
    h1, h2, h3 {
        color: #E50914 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
    }
    
    /* Movie Titles below posters */
    .movie-title {
        text-align: center;
        font-size: 14px;
        font-weight: bold;
        color: #E5E5E5;
        margin-top: 5px;
    }
    
    /* Hide default Streamlit header and footer for a cleaner look */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 1. Load Data ---
# Using caching so data is loaded only once, improving app speed
@st.cache_data
def load_data():
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies_df = pd.DataFrame(movies_dict)
    sim_matrix = pickle.load(open('similarity.pkl', 'rb'))
    return movies_df, sim_matrix

movies, similarity = load_data()

# --- 2. Fetch Poster Function (Safe & Cached) ---
# Caching prevents calling the API multiple times for the same poster
@st.cache_data
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        # 3-second timeout added to prevent app freezing if network fails
        response = requests.get(url, timeout=3)
        data = response.json()
        
        if 'poster_path' in data and data['poster_path'] is not None:
            return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        else:
            return "https://placehold.co/500x750/141414/E50914?text=No+Poster"
            
    except Exception as e:
        return "https://placehold.co/500x750/141414/E50914?text=Network+Error"

# --- 3. Recommendation Engine ---
def recommend(movie_title):
    # Find the index of the selected movie
    movie_index = movies[movies['title'] == movie_title].index[0]
    distances = similarity[movie_index]
    
    # Sort and get the top 5 similar movies (excluding the movie itself)
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_titles = []
    recommended_posters = []
    
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_titles.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))
        
    return recommended_titles, recommended_posters

# --- 4. Application UI ---

st.title('🎬 NETFLIX')

# Search bar layout
st.markdown("### Find your next favorite movie")
movie_list = ["-- Select a Movie --"] + list(movies['title'].values)
selected_movie = st.selectbox("", movie_list, label_visibility="collapsed")

# --- Recommendation Section (Shows when a movie is selected) ---
if selected_movie != "-- Select a Movie --":
    st.markdown("---")
    st.markdown(f"### Because you watched **{selected_movie}**")
    st.markdown("<h4 style='color: white;'>More Like This:</h4>", unsafe_allow_html=True)
    
    names, posters = recommend(selected_movie)
    
    # Create 5 columns for the recommended movies
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.image(posters[idx], use_container_width=True)
            st.markdown(f"<div class='movie-title'>{names[idx]}</div>", unsafe_allow_html=True)

# --- Home Page Section (Shows 20 Trending Movies by default) ---
else:
    st.markdown("---")
    st.markdown("### Trending Now")
    
    # Get the first 20 movies from your dataset
    trending_movies = movies.head(20)
    
    # Create a 4x5 grid layout (4 rows, 5 columns)
    for row in range(4):
        cols = st.columns(5)
        for col_idx in range(5):
            # Calculate the actual index in the dataset (0 to 19)
            movie_idx = row * 5 + col_idx
            
            movie_id = trending_movies.iloc[movie_idx].movie_id
            title = trending_movies.iloc[movie_idx].title
            poster = fetch_poster(movie_id)
            
            # Display image and title in the respective column
            with cols[col_idx]:
                st.image(poster, use_container_width=True)
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)
                st.write("") # Add a little space below each row
