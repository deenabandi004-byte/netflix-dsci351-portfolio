from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

st.title("Netflix Data Visualization")

netflix = pd.read_csv(DATA_DIR / "_netflix_titles.csv")
movies = pd.read_csv(DATA_DIR / "movies.csv")

option = st.radio(
    "Select a visualization:",
    [
        "1. Movies vs TV Shows",
        "2. Vote Average Histogram",
        "3. Popularity vs Rating",
        "4. Top 10 Genres",
        "5. Movie Ratings Pie Chart"
    ]
)

if option == "1. Movies vs TV Shows":
    counts = netflix["type"].value_counts()
    fig, ax = plt.subplots()
    ax.bar(counts.index, counts.values, color=["#E50914", "#221F1F"])
    ax.set_xlabel("Type")
    ax.set_ylabel("Count")
    ax.set_title("Movies vs TV Shows")
    st.pyplot(fig)

elif option == "2. Vote Average Histogram":
    fig, ax = plt.subplots()
    ax.hist(movies["vote_average"].dropna(), bins=20, color="#E50914", edgecolor="black")
    ax.set_xlabel("Vote Average")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Vote Average")
    st.pyplot(fig)

elif option == "3. Popularity vs Rating":
    fig, ax = plt.subplots()
    ax.scatter(movies["popularity"], movies["vote_average"], alpha=0.5, color="#E50914", s=10)
    ax.set_xlabel("Popularity")
    ax.set_ylabel("Vote Average")
    ax.set_title("Popularity vs Rating")
    st.pyplot(fig)

elif option == "4. Top 10 Genres":
    genres = movies["genres"].dropna().str.split(", ").explode()
    top_genres = genres.value_counts().head(10)
    fig, ax = plt.subplots()
    ax.barh(top_genres.index, top_genres.values, color="#E50914")
    ax.set_xlabel("Count")
    ax.set_ylabel("Genre")
    ax.set_title("Top 10 Genres")
    ax.invert_yaxis()
    st.pyplot(fig)

elif option == "5. Movie Ratings Pie Chart":
    movies_only = netflix[netflix["type"] == "Movie"]
    rating_counts = movies_only["rating"].value_counts()
    top5 = rating_counts.head(5)
    other = rating_counts[5:].sum()
    if other > 0:
        top5["Other"] = other
    fig, ax = plt.subplots()
    ax.pie(top5.values, labels=top5.index, autopct="%1.1f%%")
    ax.set_title("Movie Ratings Distribution")
    st.pyplot(fig)
