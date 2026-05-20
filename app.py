import streamlit as st
import pickle
import pandas as pd
import requests 

# ⚠️ Yahan apni copied TMDB API Key paste karein
tmdb_api_key = "a1e923f47a11306f96049e7589ae47e7"

# --- 1. .pkl files ko load karein ---
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# --- 2. Movie ID se Poster fetch karne ka function ---
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb_api_key}&language=en-US"
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

# --- 3. Recommend karne ka Updated function ---
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    
    # Top 5 movies ki list [(index, score), ...]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_movies_titles = []
    recommended_movies_posters = []
    
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id # Model se movie ID nikalein
        
        recommended_movies_titles.append(movies.iloc[i[0]].title)
        # API se poster ka link fetch karke save karein
        recommended_movies_posters.append(fetch_poster(movie_id))
        
    return recommended_movies_titles, recommended_movies_posters

# --- 4. Streamlit Website UI ka naya Layout ---
st.set_page_config(layout="wide") # App ko poori width me dikhane ke liye

st.title('🎬 Movie Recommender System')

selected_movie_name = st.selectbox(
    'Select a movie to get recommendations:',
    movies['title'].values
)

if st.button('Get Recommendations'):
    # Dono lists nikaal lein: titles aur posters ke links
    names, posters = recommend(selected_movie_name)
    
    st.subheader('Top Recommendations For You:')
    
    # Grid layout banane ke liye columns use karein
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Har column me movie poster aur title dikhayein
    with col1:
        st.text(names[0])
        st.image(posters[0])
    with col2:
        st.text(names[1])
        st.image(posters[1])
    with col3:
        st.text(names[2])
        st.image(posters[2])
    with col4:
        st.text(names[3])
        st.image(posters[3])
    with col5:
        st.text(names[4])
        st.image(posters[4])