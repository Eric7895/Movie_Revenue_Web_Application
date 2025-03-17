from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
from models import Movies, Base
from db import get_engine
from pydantic import BaseModel
import json

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

@app.post("/movies/upload/")
async def upload_movies(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a JSON file of movies and add them to the database.
    """

    # Read the JSON data from the file
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8")) 
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON data must be an array")
    
    added_movies = []
    skipped_movies = []

    for movie in data:
        try:
            required_fields = [
                "primaryTitle", "titleType", "genres", "directors", "writers", "release_date",
                "averageRating", "numVotes", "original_language", "production_companies",
                "budget", "runtime"
            ]
        
            # Check all required fields at once
            missing_fields = [field for field in required_fields if field not in movie]
            if missing_fields:
                skipped_movies.append({"movie": movie, "reason": f"Missing fields: {', '.join(missing_fields)}"})
                continue  # Skip this movie entirely
        
            # Extract and validate fields
            title = movie["primaryTitle"]
            release_date_str = movie["release_date"]

            # Convert date field 
            try:
                release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
            except ValueError:
                skipped_movies.append({"movie": movie, "reason": "Invalid date format (YYYY-MM-DD required)"})
                continue 

            # Check for duplicate
            if db.query(Movies).filter(Movies.primaryTitle == title, Movies.release_date == release_date).first():
                skipped_movies.append({"movie": movie, "reason": "Duplicate movie"})
                continue  

            # Create new movie object
            new_movie = Movies(
                primaryTitle=movie["primaryTitle"],  # Already checked
                titleType=movie["titleType"],
                genres=movie["genres"],
                directors=movie["directors"],
                writers=movie["writers"],
                averageRating=movie["averageRating"],  # No default; should be in JSON
                numVotes=movie["numVotes"],
                original_language=movie["original_language"],
                production_companies=movie["production_companies"],
                release_date=release_date,  # Already converted
                budget=movie["budget"],
               revenue=movie.get("revenue"),  # Optional
                runtime=movie["runtime"],
                keywords=movie.get("keywords"),  # Nullable; should be None if missing
               trailer_views=movie.get("trailer_views"),  # Nullable
               trailer_likes=movie.get("trailer_likes"),  # Nullable
            )


            db.add(new_movie)
            added_movies.append(title)
        except Exception as e:
            skipped_movies.append({"movie": movie, "reason": str(e)})
            continue 
    
    db.commit()  # Commit once at the end

    return {
        "message": "Movies upload complete",
        "added_movies": added_movies,
        "skipped_movies": skipped_movies
    }

@app.put("/movies/{title}/")
def update_movie(title: str,
                 titleType: str | None = None,
                 release_date: str | None = None,
                 genres: str | None = None,
                 direcors: str | None = None,
                 writers: str | None = None,
                 actors: str | None = None,
                 keywords: str | None = None,
                 production_companies: str | None = None,
                 original_language: str | None = None,
                 averageRating: float | None = None,
                 numVotes: float | None = None,
                 budget: float | None = None,
                 revenue: float | None = None,
                 runtime: float | None = None,
                 trailer_views: float | None = None,
                 trailer_likes: float | None = None,
                 db: Session = Depends(get_db)
                 ):
    """
    Update a movie by title and parameters
    """
    movie = db.query(Movies).filter(Movies.primaryTitle == title).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if titleType is not None:
        movie.titleType = titleType
    
    if release_date is not None:
        movie.release_date = release_date

    if genres is not None:
        movie.genres = genres

    if direcors is not None:
        movie.directors = direcors

    if writers is not None:
        movie.writers = writers

    if actors is not None:
        movie.actors = actors

    if keywords is not None:
        movie.keywords = keywords

    if production_companies is not None:
        movie.production_companies = production_companies

    if original_language is not None:
        movie.original_language = original_language

    if averageRating is not None:
        movie.averageRating = averageRating

    if numVotes is not None:
        movie.numVotes = numVotes

    if budget is not None:
        movie.budget = budget

    if revenue is not None:
        movie.revenue = revenue

    if runtime is not None:
        movie.runtime = runtime

    if trailer_views is not None:
        movie.trailer_views = trailer_views

    if trailer_likes is not None:
        movie.trailer_likes = trailer_likes

    db.commit()

    return {"message": "Movie {movie.primaryTitle} updated successfully",
            "Updated Movie": {
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
            }}

# Fixed vs code path error using "set PATH=%CONDA_PREFIX%\Scripts;%PATH%"
# Run the app using "uvicorn movie_api:app --reload"