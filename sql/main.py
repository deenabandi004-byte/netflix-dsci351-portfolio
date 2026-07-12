# Import functions from other files
from data_cleaning import clean_and_merge_data
from python_sql_creation import setup_database


def main():
    print("=" * 60)
    print("DSCI 351 - Netflix Data Pipeline")
    print("=" * 60)
    
    # Step 1: Clean and merge CSV files
    print("\n[Step 1] Cleaning and merging CSV files...")
    print("-" * 40)
    merged_df = clean_and_merge_data()
    print(f"Data cleaning complete. Output: cleaned_netflix_movies.csv")
    
    # Step 2: Create tables and insert data
    print("\n[Step 2] Setting up database tables...")
    print("-" * 40)
    setup_database()
    
    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()