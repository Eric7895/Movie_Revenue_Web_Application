import pandas as pd 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker  # Import sessionmaker
from models import Movies, Base  # Import Base instead of metadata
from db import get_engine

# Create engine and create tables
engine = get_engine()
Base.metadata.create_all(engine)  # Use Base.metadata to create tables

# Create a session
Session = sessionmaker(bind=engine)  # Create a session factory
session = Session()  # Create a session instance

# Load data from CSV
file_path = 'data/movie_data.csv'
df = pd.read_csv(file_path)

# Replace NaN values with None - MySQL does not accept NaN
df = df.where(pd.notna(df), None)

# Convert 'release_date' column to datetime
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce').dt.date


for index, row in df.iterrows():
    # Insert only if the movie is not already in the database (based on name and release_date)
    existing_movie = session.query(Movies).filter(
        Movies.primaryTitle == row['primaryTitle'], 
        Movies.release_date == row['release_date']
    ).first()  # Using .first() instead of .fetchone() for SQLAlchemy ORM queries

    if not existing_movie:
        
        new_movie = Movies(
            primaryTitle=row['primaryTitle'],
            titleType=row['titleType'],
            genres=row['genres'],
            directors=row['directors'],
            writers=row['writers'],
            averageRating=row['averageRating'],
            numVotes=row['numVotes'],
            actors=row['actors'],
            original_language=row['original_language'],
            production_companies=row['production_companies'],
            release_date=row['release_date'],
            budget=row['budget'],
            revenue=row['revenue'],
            runtime=row['runtime'],
            keywords=row['keywords'],
            trailer_views=row['trailer_views'],
            trailer_likes=row['trailer_likes']
        )
        session.add(new_movie)  # Add the new object to the session

# Commit the changes    
session.commit()

# Close the session
session.close()