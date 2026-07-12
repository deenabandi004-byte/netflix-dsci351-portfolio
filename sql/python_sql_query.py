import os
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_CSV = DATA_DIR / "cleaned_netflix_movies.csv"

DB_USER = os.environ.get("NETFLIX_DB_USER", "")
DB_PASSWORD = os.environ.get("NETFLIX_DB_PASSWORD", "")
DB_HOST = os.environ.get("NETFLIX_DB_HOST", "")
DB_NAME = os.environ.get("NETFLIX_DB_NAME", "")

def get_connection():
    
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(connection_string)
    return engine

def question1_sql(engine):
    """SQL Solution: Top genres by number of shows"""
    query = """
    SELECT g.name AS genre, COUNT(*) AS show_count
    FROM Genre g
    JOIN ShowGenre sg ON g.genre_id = sg.genre_id
    GROUP BY g.genre_id, g.name
    ORDER BY show_count DESC;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
    
    print("\n=== QUESTION 1: Top Genres by Content Count (SQL) ===")
    print(f"{'Genre':<40} {'Count':<10}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<40} {row[1]:<10}")
    
    return rows


def question1_pandas(csv_file=None):
    
    df = pd.read_csv(csv_file or DEFAULT_CSV)
    
    # Get genres column (could be listed_in or genres)
    genres_col = 'listed_in' if 'listed_in' in df.columns else 'genres'
    if genres_col not in df.columns:
        genres_col = 'listed_in_netflix'
    
    # Explode genres and count
    genres = df[genres_col].dropna().str.split(',').explode()
    genres = genres.str.strip()
    genre_counts = genres.value_counts()
    
    print("\n=== QUESTION 1: Top Genres by Content Count (Pandas) ===")
    print(genre_counts.head(15))
    
    return genre_counts


def question1_with_index(engine):
    """SQL Solution with INDEX"""
    
    # Create index
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX idx_showgenre_genre ON ShowGenre(genre_id);"))
            conn.commit()
            print("Index idx_showgenre_genre created.")
        except:
            print("Index idx_showgenre_genre already exists.")
    
    query = """
    SELECT g.name AS genre, COUNT(*) AS show_count
    FROM Genre g
    JOIN ShowGenre sg ON g.genre_id = sg.genre_id
    GROUP BY g.genre_id, g.name
    ORDER BY show_count DESC;
    """
    
    # Run with EXPLAIN
    explain_query = "EXPLAIN " + query
    
    with engine.connect() as conn:
        result = conn.execute(text(explain_query))
        explain_result = result.fetchall()
    
    print("\n=== QUESTION 1: EXPLAIN Output (with INDEX) ===")
    for row in explain_result:
        print(row)
    
    return explain_result


def question2_sql(engine):
    """SQL Solution: Most prolific directors"""
    query = """
    SELECT p.name AS director, COUNT(*) AS show_count
    FROM Person p
    JOIN Director d ON p.person_id = d.person_id
    JOIN ShowDirector sd ON d.director_id = sd.director_id
    GROUP BY p.person_id, p.name
    ORDER BY show_count DESC
    LIMIT 10;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
    
    print("\n=== QUESTION 2: Most Prolific Directors (SQL) ===")
    print(f"{'Director':<40} {'Shows':<10}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<40} {row[1]:<10}")
    
    return rows


def question2_pandas(csv_file=None):
    """Pandas Solution: Most prolific directors"""
    df = pd.read_csv(csv_file or DEFAULT_CSV)
    
    # Get director column
    director_col = 'director' if 'director' in df.columns else 'director_netflix'
    
    # Count directors
    directors = df[director_col].dropna()
    directors = directors[directors != 'Not Specified']
    directors = directors.str.split(',').str[0].str.strip()  # Take first director
    director_counts = directors.value_counts()
    
    print("\n=== QUESTION 2: Most Prolific Directors (Pandas) ===")
    print(director_counts.head(10))
    
    return director_counts


def question2_with_index(engine):
    """SQL Solution with INDEX"""
    
    # Create index
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX idx_showdirector_director ON ShowDirector(director_id);"))
            conn.commit()
            print("Index idx_showdirector_director created.")
        except:
            print("Index idx_showdirector_director already exists.")
    
    query = """
    SELECT p.name AS director, COUNT(*) AS show_count
    FROM Person p
    JOIN Director d ON p.person_id = d.person_id
    JOIN ShowDirector sd ON d.director_id = sd.director_id
    GROUP BY p.person_id, p.name
    ORDER BY show_count DESC
    LIMIT 10;
    """
    
    # Run with EXPLAIN
    explain_query = "EXPLAIN " + query
    
    with engine.connect() as conn:
        result = conn.execute(text(explain_query))
        explain_result = result.fetchall()
    
    print("\n=== QUESTION 2: EXPLAIN Output (with INDEX) ===")
    for row in explain_result:
        print(row)
    
    return explain_result


def question3_sql(engine):
    """SQL Solution: Content distribution by release year"""
    query = """
    SELECT release_year, COUNT(*) AS show_count
    FROM NetflixShow
    WHERE release_year IS NOT NULL
    GROUP BY release_year
    ORDER BY release_year DESC
    LIMIT 15;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
    
    print("\n=== QUESTION 3: Content by Release Year (SQL) ===")
    print(f"{'Year':<10} {'Count':<10}")
    print("-" * 20)
    for row in rows:
        print(f"{row[0]:<10} {row[1]:<10}")
    
    return rows


def question3_pandas(csv_file=None):
    """Pandas Solution: Content distribution by release year"""
    df = pd.read_csv(csv_file or DEFAULT_CSV)
    
    year_counts = df['release_year'].dropna().astype(int).value_counts().sort_index(ascending=False)
    
    print("\n=== QUESTION 3: Content by Release Year (Pandas) ===")
    print(year_counts.head(15))
    
    return year_counts


def question3_with_index(engine):
    """SQL Solution with INDEX"""
    
    # Create index
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX idx_show_year ON NetflixShow(release_year);"))
            conn.commit()
            print("Index idx_show_year created.")
        except:
            print("Index idx_show_year already exists.")
    
    query = """
    SELECT release_year, COUNT(*) AS show_count
    FROM NetflixShow
    WHERE release_year IS NOT NULL
    GROUP BY release_year
    ORDER BY release_year DESC
    LIMIT 15;
    """
    
    # Run with EXPLAIN
    explain_query = "EXPLAIN " + query
    
    with engine.connect() as conn:
        result = conn.execute(text(explain_query))
        explain_result = result.fetchall()
    
    print("\n=== QUESTION 3: EXPLAIN Output (with INDEX) ===")
    for row in explain_result:
        print(row)
    
    return explain_result

def question4_sql(engine):
    """SQL Solution: Most frequent actors"""
    query = """
    SELECT p.name AS actor, COUNT(*) AS appearance_count
    FROM Person p
    JOIN Cast_Member c ON p.person_id = c.person_id
    JOIN ShowCast sc ON c.cast_id = sc.cast_id
    GROUP BY p.person_id, p.name
    ORDER BY appearance_count DESC
    LIMIT 10;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
    
    print("\n=== QUESTION 4: Most Frequent Actors (SQL) ===")
    print(f"{'Actor':<40} {'Appearances':<10}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<40} {row[1]:<10}")
    
    return rows


def question4_pandas(csv_file=None):
    """Pandas Solution: Most frequent actors"""
    df = pd.read_csv(csv_file or DEFAULT_CSV)
    
    # Get cast column
    cast_col = 'cast' if 'cast' in df.columns else 'cast_netflix'
    
    # Explode cast and count
    cast = df[cast_col].dropna()
    cast = cast[cast != 'Not Specified']
    cast = cast.str.split(',').explode().str.strip()
    cast_counts = cast.value_counts()
    
    print("\n=== QUESTION 4: Most Frequent Actors (Pandas) ===")
    print(cast_counts.head(10))
    
    return cast_counts


def question4_with_index(engine):
    """SQL Solution with INDEX"""
    
    # Create index
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX idx_showcast_cast ON ShowCast(cast_id);"))
            conn.commit()
            print("Index idx_showcast_cast created.")
        except:
            print("Index idx_showcast_cast already exists.")
    
    query = """
    SELECT p.name AS actor, COUNT(*) AS appearance_count
    FROM Person p
    JOIN Cast_Member c ON p.person_id = c.person_id
    JOIN ShowCast sc ON c.cast_id = sc.cast_id
    GROUP BY p.person_id, p.name
    ORDER BY appearance_count DESC
    LIMIT 10;
    """
    
    # Run with EXPLAIN
    explain_query = "EXPLAIN " + query
    
    with engine.connect() as conn:
        result = conn.execute(text(explain_query))
        explain_result = result.fetchall()
    
    print("\n=== QUESTION 4: EXPLAIN Output (with INDEX) ===")
    for row in explain_result:
        print(row)
    
    return explain_result



def run_all_queries():
    """Run all questions with SQL, Pandas, and INDEX analysis"""
    
    engine = get_connection()
    csv_file = DEFAULT_CSV
    
    print("=" * 60)
    print("PART 4.2: Business Questions Analysis")
    print("=" * 60)
    
    # Question 1
    print("\n" + "=" * 60)
    print("QUESTION 1: Which genres have the most content on Netflix?")
    print("=" * 60)
    question1_sql(engine)
    question1_pandas(csv_file)
    question1_with_index(engine)
    
    # Question 2
    print("\n" + "=" * 60)
    print("QUESTION 2: Which directors are most prolific on Netflix?")
    print("=" * 60)
    question2_sql(engine)
    question2_pandas(csv_file)
    question2_with_index(engine)
    
    # Question 3
    print("\n" + "=" * 60)
    print("QUESTION 3: What is the distribution of content by release year?")
    print("=" * 60)
    question3_sql(engine)
    question3_pandas(csv_file)
    question3_with_index(engine)
    
    # Question 4
    print("\n" + "=" * 60)
    print("QUESTION 4: Which actors appear in the most Netflix content?")
    print("=" * 60)
    question4_sql(engine)
    question4_pandas(csv_file)
    question4_with_index(engine)
    
    print("\n" + "=" * 60)
    print("All queries completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_queries()