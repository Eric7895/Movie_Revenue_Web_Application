from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
from models import Movies, Base
from db import get_engine
from pydantic import BaseModel

app = FastAPI(
    title = 'Movie API'
)

# Initialize the database
engine = get_engine()
Base.metadata.create_all(engine)

local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for database session
def get_db():
    db = local_session()
    try:
        yield db
    finally:
        db.close()

# Routes 

@app.get("/")
def main():
    '''
    Print an index page
    '''
    main = {
        'Welcoming_message': 'Finally working',
        '/movies_basic/': 'Query all movies with basic informations',
        '/movies_actors/': 'Query all movies with actors',
        '/movies_directors/': 'Query all movies with directors',
        '/movies_writers/': 'Query all movies with writers',
        '/movies_search/{title}': 'Query all movies by a title string using wild card',
    }
    return {"message": main}

@app.get("/movies_basic/")
def get_movies_basic(db: Session = Depends(get_db)):
    '''
    Query all movies
    '''
    movies = db.query(Movies).all()
    return [{"Title": movie.primaryTitle, "Release_date": movie.release_date, "genres": movie.genres, 
             "Rating": movie.averageRating, "Votes": movie.numVotes, "original_language": movie.original_language, 
             "Production_companies": movie.production_companies, 
             "Budget": movie.budget, "Revenue": movie.revenue, "Runtime": movie.runtime, "keywords": movie.keywords,
             "Trailer_Views": movie.trailer_views, "Trailer_Likes": movie.trailer_likes} 
            for movie in movies]

@app.get("/movies_actors/")
def get_movies_actors(db: Session = Depends(get_db)):
    '''
    Query all movies with actors
    '''
    movies = db.query(Movies).all()
    return [{"Title": movie.primaryTitle, "Actors": movie.actors} for movie in movies]

@app.get("/movies_directors/")
def get_movies_directors(db: Session = Depends(get_db)):
    '''
    Query all movies with directors
    '''
    movies = db.query(Movies).all()
    return [{"Title": movie.primaryTitle, "Directors": movie.directors} for movie in movies]

@app.get("/movies_writers/")
def get_movies_writers(db: Session = Depends(get_db)):
    '''
    Query all movies with writers
    '''
    movies = db.query(Movies).all()
    return [{"Title": movie.primaryTitle, "Writers": movie.writers} for movie in movies]

@app.get("/movies_search/{title}")
def get_movies_search(title: str, db: Session = Depends(get_db)):
    '''
    Query all movies by a title string using wild card
    '''
    movies = db.query(Movies).filter(Movies.primaryTitle.contains(title)).all()
    return [{"Title": movie.primaryTitle, "Release_date": movie.release_date, "genres": movie.genres, 
             "Rating": movie.averageRating, "Votes": movie.numVotes, "original_language": movie.original_language, 
             "Production_companies": movie.production_companies, 
             "Budget": movie.budget, "Revenue": movie.revenue, "Runtime": movie.runtime, "keywords": movie.keywords,
             "Trailer_Views": movie.trailer_views, "Trailer_Likes": movie.trailer_likes} 
            for movie in movies]

@app.get("/movies_search/find/")
def query_movies_by_parameters(
    title: str | None = None,
    release_date: str | None = None,  # YYYY-MM-DD
    genres: str | None = None,
    averageRating: float | None = None,
    rating_condition: str | None = None,
    numVotes: float | None = None,
    votes_condition: str | None = None,
    budget: float | None = None,
    budget_condition: str | None = None,
    revenue: float | None = None,
    revenue_condition: str | None = None,
    runtime: float | None = None,
    runtime_condition: str | None = None,
    trailer_views: float | None = None,
    views_condition: str | None = None,
    trailer_likes: float | None = None,
    likes_condition: str | None = None,
    db: Session = Depends(get_db)
):
    '''
    Query all movies by parameters 
    Example -http://127.0.0.1:8000/movies_search/find/?title=star war&genres=Action
    '''
    query = db.query(Movies)

    if title is not None:
        query = query.filter(Movies.primaryTitle.contains(title))

    if release_date is not None:
        try:
            release_date = datetime.strptime(release_date, "%Y-%m-%d").date()
            query = query.filter(Movies.release_date == release_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

    if genres is not None:
        query = query.filter(Movies.genres.contains(genres))

    # Apply conditions separately
    def apply_condition(field, value, condition):
        if condition == 'G':
            return field > value
        elif condition == 'L':
            return field < value
        elif condition == 'E':
            return field == value
        elif condition == 'GE':
            return field >= value
        elif condition == 'LE':
            return field <= value
        return field == value  # Default to E

    if averageRating is not None and rating_condition:
        query = query.filter(apply_condition(Movies.averageRating, averageRating, rating_condition))

    if numVotes is not None and votes_condition:
        query = query.filter(apply_condition(Movies.numVotes, numVotes, votes_condition))

    if budget is not None and budget_condition:
        query = query.filter(apply_condition(Movies.budget, budget, budget_condition))

    if revenue is not None and revenue_condition:
        query = query.filter(apply_condition(Movies.revenue, revenue, revenue_condition))

    if runtime is not None and runtime_condition:
        query = query.filter(apply_condition(Movies.runtime, runtime, runtime_condition))

    if trailer_views is not None and views_condition:
        query = query.filter(apply_condition(Movies.trailer_views, trailer_views, views_condition))

    if trailer_likes is not None and likes_condition:
        query = query.filter(apply_condition(Movies.trailer_likes, trailer_likes, likes_condition))

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="No movies found matching the query")

    movies = [
        {
            'Title': movie.primaryTitle,
            'Release_date': movie.release_date,
            'genres': movie.genres,
            'averageRating': movie.averageRating,
            'numVotes': movie.numVotes,
            'original_language': movie.original_language,
            'production_companies': movie.production_companies,
            'budget': movie.budget,
            'revenue': movie.revenue,
            'runtime': movie.runtime,
            'keywords': movie.keywords,
            'trailer_views': movie.trailer_views,
            'trailer_likes': movie.trailer_likes
        }
        for movie in results
    ]

    return {
        "query_parameters": {
            "title": title,
            "release_date": release_date,
            "genres": genres,
            "averageRating": averageRating,
            "numVotes": numVotes,
            "budget": budget,
            "revenue": revenue,
            "runtime": runtime,
            "trailer_views": trailer_views,
            "trailer_likes": trailer_likes
        },
        'Matching Movies': movies
    }

    
# Run the app using "uvicorn movie_api:app --reload"