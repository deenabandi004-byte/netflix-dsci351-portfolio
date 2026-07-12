from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def clean_and_merge_data():
    # 1. Read in the datasets
    movies = pd.read_csv(DATA_DIR / "movies.csv")
    tv_shows = pd.read_csv(DATA_DIR / "tv_shows.csv")
    netflix_titles = pd.read_csv(DATA_DIR / "_netflix_titles.csv")
    
    # 2. Handle missing values
    # Drop duration column from all dataframes
    if 'duration' in movies.columns:
        movies = movies.drop(columns=['duration'])
    if 'duration' in tv_shows.columns:
        tv_shows = tv_shows.drop(columns=['duration'])
    if 'duration' in netflix_titles.columns:
        netflix_titles = netflix_titles.drop(columns=['duration'])
    
    # Fill missing values
    for df in [movies, tv_shows, netflix_titles]:
        if 'description' in df.columns:
            df['description'] = df['description'].fillna('')
        if 'country' in df.columns:
            df['country'] = df['country'].fillna('Not Specified')
        if 'director' in df.columns:
            df['director'] = df['director'].fillna('Not Specified')
        if 'cast' in df.columns:
            df['cast'] = df['cast'].fillna('Not Specified')
        if 'rating' in df.columns:
            df['rating'] = df['rating'].fillna('Not Rated')
    
    # 3. Type conversion
    for df in [movies, tv_shows, netflix_titles]:
        # Convert date_added to datetime and keep only date part
        if 'date_added' in df.columns:
            df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
            df['date_added'] = df['date_added'].dt.date
        
        # Standardize categorical text to lowercase
        if 'type' in df.columns:
            df['type'] = df['type'].str.lower()
        if 'title' in df.columns:
            df['title'] = df['title'].str.lower()
    
    # 4. Concatenate movies and tv_shows vertically
    combined = pd.concat([movies, tv_shows], ignore_index=True)
    
    # 5. Outer join with netflix_titles on title and release_year
    merged = pd.merge(
        netflix_titles,
        combined,
        left_on=['title', 'release_year'],
        right_on=['title', 'release_year'],
        how='outer',
        suffixes=('_netflix', '_collected')
    )
    
    # 6. Extra cleaning steps
    merged = extra_cleaning(merged)
    
    # 7. Export the unified data
    merged.to_csv(DATA_DIR / "cleaned_netflix_movies.csv", index=False)
    
    print(f"Cleaned data saved. Shape: {merged.shape}")
    return merged


def extra_cleaning(df):
    """
    Extra cleaning steps for the merged dataset
    """
    # Remove duplicate rows
    df = df.drop_duplicates()
    
    # Check for type mismatches between netflix and collected data
    if 'type_netflix' in df.columns and 'type_collected' in df.columns:
        # Find titles with different types
        type_mismatch = df[
            (df['type_netflix'].notna()) & 
            (df['type_collected'].notna()) & 
            (df['type_netflix'] != df['type_collected'])
        ]
        if len(type_mismatch) > 0:
            print(f"Found {len(type_mismatch)} titles with type mismatches:")
            print(type_mismatch[['title', 'type_netflix', 'type_collected']].head())
        
        # Create unified type column (prefer netflix type)
        df['type'] = df['type_netflix'].fillna(df['type_collected'])
    
    # Standardize country names (trim whitespace)
    for col in df.columns:
        if 'country' in col.lower() and df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    
    # Fill remaining NaN values in text columns with empty string
    text_columns = df.select_dtypes(include=['object']).columns
    for col in text_columns:
        df[col] = df[col].fillna('')
    
    return df


if __name__ == "__main__":
    merged_df = clean_and_merge_data()