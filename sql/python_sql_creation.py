import os
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
    """Create database connection using sqlalchemy"""
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(connection_string)
    return engine

def drop_tables(engine):
    """Drop all tables if they exist (in correct order due to FK constraints)"""
    drop_statements = [
        "DROP TABLE IF EXISTS ShowGenre;",
        "DROP TABLE IF EXISTS ShowDirector;",
        "DROP TABLE IF EXISTS ShowCast;",
        "DROP TABLE IF EXISTS NetflixShow;",
        "DROP TABLE IF EXISTS Director;",
        "DROP TABLE IF EXISTS Cast_Member;",
        "DROP TABLE IF EXISTS Genre;",
        "DROP TABLE IF EXISTS Person;"
    ]
    
    with engine.connect() as conn:
        for stmt in drop_statements:
            conn.execute(text(stmt))
        conn.commit()
    print("All tables dropped successfully.")

def create_tables(engine):
    """Create all tables following the relational model"""
    
    create_statements = [
        
        """
        CREATE TABLE IF NOT EXISTS Person (
            person_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL
        );
        """,
        
       
        """
        CREATE TABLE IF NOT EXISTS Genre (
            genre_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL
        );
        """,
        
   
        """
        CREATE TABLE IF NOT EXISTS Director (
            director_id INT PRIMARY KEY AUTO_INCREMENT,
            person_id INT,
            FOREIGN KEY (person_id) REFERENCES Person(person_id)
        );
        """,
        
        
        """
        CREATE TABLE IF NOT EXISTS Cast_Member (
            cast_id INT PRIMARY KEY AUTO_INCREMENT,
            person_id INT,
            actor_rating DECIMAL(4,2),
            FOREIGN KEY (person_id) REFERENCES Person(person_id)
        );
        """,
        

        """
        CREATE TABLE IF NOT EXISTS NetflixShow (
            show_id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            type VARCHAR(50),
            rating VARCHAR(20),
            release_year INT,
            description TEXT,
            country VARCHAR(255)
        );
        """,
        
        
        """
        CREATE TABLE IF NOT EXISTS ShowGenre (
            show_id INT,
            genre_id INT,
            PRIMARY KEY (show_id, genre_id),
            FOREIGN KEY (show_id) REFERENCES NetflixShow(show_id),
            FOREIGN KEY (genre_id) REFERENCES Genre(genre_id)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ShowDirector (
            show_id INT,
            director_id INT,
            PRIMARY KEY (show_id, director_id),
            FOREIGN KEY (show_id) REFERENCES NetflixShow(show_id),
            FOREIGN KEY (director_id) REFERENCES Director(director_id)
        );
        """,
        
  
        """
        CREATE TABLE IF NOT EXISTS ShowCast (
            show_id INT,
            cast_id INT,
            PRIMARY KEY (show_id, cast_id),
            FOREIGN KEY (show_id) REFERENCES NetflixShow(show_id),
            FOREIGN KEY (cast_id) REFERENCES Cast_Member(cast_id)
        );
        """
    ]
    
    with engine.connect() as conn:
        for stmt in create_statements:
            conn.execute(text(stmt))
        conn.commit()
    print("All tables created successfully.")

def insert_data(engine, csv_file=None):
    """Insert 30-100 entity instances to each table from merged csv"""

    csv_file = csv_file or DEFAULT_CSV
    df = pd.read_csv(csv_file)
    

    df = df.head(100)
    
  
    persons = {}   
    genres = {}    
    directors = {}   
    cast_members = {}   
    
    with engine.connect() as conn:
        person_id = 1
        genre_id = 1
        director_id = 1
        cast_id = 1
        show_id = 1
        
        # Process each row
        for idx, row in df.iterrows():
            # Get title (handle both column names)
            title = row.get('title', row.get('title_netflix', 'Unknown'))
            if pd.isna(title):
                title = 'Unknown'
            
            # Get type
            show_type = row.get('type', row.get('type_netflix', ''))
            if pd.isna(show_type):
                show_type = ''
            
            # Get rating
            rating = row.get('rating', row.get('rating_netflix', ''))
            if pd.isna(rating):
                rating = ''
            
            # Get release_year
            release_year = row.get('release_year', None)
            if pd.isna(release_year):
                release_year = None
            else:
                release_year = int(release_year)
            
            # Get description
            description = row.get('description', row.get('description_netflix', ''))
            if pd.isna(description):
                description = ''
            
            # Get country
            country = row.get('country', row.get('country_netflix', ''))
            if pd.isna(country):
                country = ''
            
            # Insert NetflixShow
            conn.execute(text("""
                INSERT INTO NetflixShow (show_id, title, type, rating, release_year, description, country)
                VALUES (:show_id, :title, :type, :rating, :release_year, :description, :country)
            """), {
                'show_id': show_id,
                'title': str(title)[:255],
                'type': str(show_type)[:50],
                'rating': str(rating)[:20],
                'release_year': release_year,
                'description': str(description)[:5000],
                'country': str(country)[:255]
            })
            
            # Process director
            director_name = row.get('director', row.get('director_netflix', ''))
            if pd.notna(director_name) and director_name != '' and director_name != 'Not Specified':
                # Take only first director if multiple
                director_name = str(director_name).split(',')[0].strip()
                
                if director_name not in persons:
                    # Insert into Person
                    conn.execute(text("""
                        INSERT INTO Person (person_id, name)
                        VALUES (:person_id, :name)
                    """), {'person_id': person_id, 'name': director_name[:255]})
                    persons[director_name] = person_id
                    
                    # Insert into Director
                    conn.execute(text("""
                        INSERT INTO Director (director_id, person_id)
                        VALUES (:director_id, :person_id)
                    """), {'director_id': director_id, 'person_id': person_id})
                    directors[director_name] = director_id
                    
                    person_id += 1
                    director_id += 1
                
                # Insert into ShowDirector
                if director_name in directors:
                    try:
                        conn.execute(text("""
                            INSERT INTO ShowDirector (show_id, director_id)
                            VALUES (:show_id, :director_id)
                        """), {'show_id': show_id, 'director_id': directors[director_name]})
                    except:
                        pass  # Skip duplicates
            
            # Process cast (take first 3 cast members)
            cast_str = row.get('cast', row.get('cast_netflix', ''))
            if pd.notna(cast_str) and cast_str != '' and cast_str != 'Not Specified':
                cast_list = str(cast_str).split(',')[:3]  # Limit to first 3
                
                for cast_name in cast_list:
                    cast_name = cast_name.strip()
                    if cast_name and cast_name not in cast_members:
                        # Check if person already exists
                        if cast_name not in persons:
                            conn.execute(text("""
                                INSERT INTO Person (person_id, name)
                                VALUES (:person_id, :name)
                            """), {'person_id': person_id, 'name': cast_name[:255]})
                            persons[cast_name] = person_id
                            person_id += 1
                        
                        # Insert into Cast_Member
                        conn.execute(text("""
                            INSERT INTO Cast_Member (cast_id, person_id, actor_rating)
                            VALUES (:cast_id, :person_id, :actor_rating)
                        """), {
                            'cast_id': cast_id,
                            'person_id': persons[cast_name],
                            'actor_rating': None
                        })
                        cast_members[cast_name] = cast_id
                        cast_id += 1
                    
                    # Insert into ShowCast
                    if cast_name in cast_members:
                        try:
                            conn.execute(text("""
                                INSERT INTO ShowCast (show_id, cast_id)
                                VALUES (:show_id, :cast_id)
                            """), {'show_id': show_id, 'cast_id': cast_members[cast_name]})
                        except:
                            pass  # Skip duplicates
            
            # Process genres
            genres_str = row.get('listed_in', row.get('genres', row.get('listed_in_netflix', '')))
            if pd.notna(genres_str) and genres_str != '':
                genre_list = str(genres_str).split(',')
                
                for genre_name in genre_list:
                    genre_name = genre_name.strip()
                    if genre_name and genre_name not in genres:
                        conn.execute(text("""
                            INSERT INTO Genre (genre_id, name)
                            VALUES (:genre_id, :name)
                        """), {'genre_id': genre_id, 'name': genre_name[:100]})
                        genres[genre_name] = genre_id
                        genre_id += 1
                    
                    # Insert into ShowGenre
                    if genre_name in genres:
                        try:
                            conn.execute(text("""
                                INSERT INTO ShowGenre (show_id, genre_id)
                                VALUES (:show_id, :genre_id)
                            """), {'show_id': show_id, 'genre_id': genres[genre_name]})
                        except:
                            pass  # Skip duplicates
            
            show_id += 1
        
        conn.commit()
    
    print(f"Data inserted successfully!")
    print(f"  - {show_id - 1} shows")
    print(f"  - {len(persons)} persons")
    print(f"  - {len(directors)} directors")
    print(f"  - {len(cast_members)} cast members")
    print(f"  - {len(genres)} genres")

def setup_database(csv_file=None):
    """Main function to setup the database"""
    engine = get_connection()
    drop_tables(engine)
    create_tables(engine)
    insert_data(engine, csv_file)
    return engine

if __name__ == "__main__":
    setup_database()