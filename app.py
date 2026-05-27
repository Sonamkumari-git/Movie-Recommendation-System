import streamlit as st
import pickle
import pandas as pd
import requests 
from concurrent.futures import ThreadPoolExecutor # For Super Fast Parallel Fetching

# --- Configuration ---
TMDB_API_KEY = "88ce67a5b71f14307410e80933b2ce81"

st.set_page_config(page_title="NetMirror Reel", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS for Premium UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0b0b; color: white; }
    h1, h2, h3 { color: #E50914 !important; font-weight: 700; }
    .movie-title { text-align: center; font-size: 15px; font-weight: bold; color: #ffffff; margin-top: 8px; }
    .movie-details { text-align: center; font-size: 13px; color: #aaaaaa; margin-bottom: 10px; }
    .banner-container { width: 100%; max-height: 400px; overflow: hidden; border-radius: 10px; margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(229, 9, 20, 0.3); }
    .banner-img { width: 100%; object-fit: cover; opacity: 0.8; }
    div[data-testid="stButton"] button { width: 100%; background-color: #333333; color: white; border: none; border-radius: 5px; }
    div[data-testid="stButton"] button:hover { background-color: #E50914; color: white; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
# This keeps track of which movie the user clicked on
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None

def set_movie(movie_name):
    st.session_state.selected_movie = movie_name

def go_home():
    st.session_state.selected_movie = None

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

# --- 2. Fast API Fetching using ThreadPoolExecutor ---
def fetch_movie_details(movie_data):
    """Helper function to fetch details for a single movie"""
    movie_id, title = movie_data
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=3).json()
        poster_path = response.get('poster_path')
        backdrop_path = response.get('backdrop_path')
        
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://placehold.co/500x750/141414/E50914?text=No+Poster"
        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
        
        rating = round(response.get('vote_average', 0.0), 1)
        year = response.get('release_date', 'N/A').split('-')[0]
        
        return {"id": movie_id, "title": title, "poster": poster_url, "banner": backdrop_url, "rating": rating, "year": year}
    except Exception:
        return {"id": movie_id, "title": title, "poster": "https://placehold.co/500x750/141414/E50914?text=Error", "banner": None, "rating": 0.0, "year": "N/A"}

@st.cache_data
def get_parallel_movie_data(movie_list):
    """Fetches movie data in parallel for super fast loading"""
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(fetch_movie_details, movie_list))
    return results

# --- 3. Recommendation Engine ---
def get_recommendations(movie_title):
    movie_index = movies[movies['title'] == movie_title].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    # Prepare list for parallel fetching
    to_fetch = [(movies.iloc[i[0]].movie_id, movies.iloc[i[0]].title) for i in movies_list]
    return get_parallel_movie_data(to_fetch)

# --- 4. Application UI Routing ---
st.title('🎬 NETMIRROR REEL')

# Search bar layout
movie_list = ["-- Select a Movie --"] + list(movies['title'].values)
search_selection = st.selectbox("Search your favorite movie", movie_list, key="search_box")

# If user searches from dropdown, update session state
if search_selection != "-- Select a Movie --" and search_selection != st.session_state.selected_movie:
    st.session_state.selected_movie = search_selection
    st.rerun()

# ---------------------------------------------------------
# VIEW 1: MOVIE DETAILS & RECOMMENDATIONS (Netflix Style)
# ---------------------------------------------------------
if st.session_state.selected_movie:
    st.button("⬅️ Back to Home", on_click=go_home)
    
    selected = st.session_state.selected_movie
    selected_id = movies[movies['title'] == selected].iloc[0].movie_id
    
    # Get details for the main banner
    main_movie = fetch_movie_details((selected_id, selected))
    
    if main_movie["banner"]:
        st.markdown(f"""
            <div class="banner-container">
                <img src="{main_movie['banner']}" class="banner-img">
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"### Because you watched **{selected}**")
    st.markdown("<h4 style='color: white;'>More Like This:</h4>", unsafe_allow_html=True)
    
    # Get and show recommendations
    recs = get_recommendations(selected)
    
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.image(recs[idx]["poster"], use_container_width=True)
            st.markdown(f"<div class='movie-title'>{recs[idx]['title']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='movie-details'>⭐ {recs[idx]['rating']} | 📅 {recs[idx]['year']}</div>", unsafe_allow_html=True)
            # Clicking a recommendation updates the screen to that movie
            st.button("View", key=f"rec_{idx}", on_click=set_movie, args=(recs[idx]["title"],))

# ---------------------------------------------------------
# VIEW 2: HOME DASHBOARD (Trending Grid)
# ---------------------------------------------------------
else:
    st.markdown("---")
    st.markdown("### 🍿 Trending Now")
    
    # Pick top 20 movies
    trending_df = movies.head(20)
    to_fetch = [(row.movie_id, row.title) for index, row in trending_df.iterrows()]
    
    # Fetch all 20 movies instantly using parallel threads
    trending_data = get_parallel_movie_data(to_fetch)
    
    for row in range(4):
        cols = st.columns(5)
        for col_idx in range(5):
            idx = row * 5 + col_idx
            movie = trending_data[idx]
            
            with cols[col_idx]:
                st.image(movie["poster"], use_container_width=True)
                st.markdown(f"<div class='movie-title'>{movie['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-details'>⭐ {movie['rating']} | 📅 {movie['year']}</div>", unsafe_allow_html=True)
                # This button makes the movie clickable and acts like a popup
                st.button("More Like This", key=f"trend_{idx}", on_click=set_movie, args=(movie["title"],))
