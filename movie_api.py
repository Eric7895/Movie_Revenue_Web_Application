from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
from models import Movies, Base
from db import get_engine
from urllib.parse import unquote
import pandas as pd
import math       
import pandas as pd
import prediction as ml_pred

import uvicorn

app = FastAPI(
    title = 'Movie API'
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize the database
engine = get_engine()
Base.metadata.create_all(engine)

local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Integrate populate_database.py
def update(): 
    temp = input('Do you want to update the database? (y/n) ')
    if temp == 'y':
        from populate_database import populate
        populate()

# Dependency for database session
def get_db():
    db = local_session()
    try:
        yield db
    finally:
        db.close()

# Routes 

@app.get("/", include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard/", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/notebook/", include_in_schema=False)
async def notebook(request: Request):
    return templates.TemplateResponse("notebook.html", {"request": request})

@app.get("/movies_basic/")
def get_movies_basic(db: Session = Depends(get_db)):
    '''
    Query all movies
    '''
    movies = db.query(Movies).all()
    return [{"Title": movie.primaryTitle, "Release_date": movie.release_date, "genres": movie.genres, 
             "Rating": movie.averageRating, "Votes": movie.numVotes, "original_language": movie.original_language, 
             "Production_companies": movie.production_companies, 
             "Budget": movie.budget, "Revenue": movie.revenue, "Runtime": movie.runtime, "status": movie.status, "keywords": movie.keywords,
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
    return [{"Title": movie.primaryTitle, "Release_date": movie.release_date, "Genres": movie.genres, 
             "Rating": movie.averageRating, "Votes": movie.numVotes, "Original_Language": movie.original_language, 
             "Production_Companies": movie.production_companies, 
             "Budget": movie.budget, "Revenue": movie.revenue, "Runtime": movie.runtime, "status": movie.status, "Keywords": movie.keywords,
             "Trailer_Views": movie.trailer_views, "Trailer_Likes": movie.trailer_likes} 
            for movie in movies]

@app.get("/movies_search/find/")
def query_movies_by_parameters(
    title: str | None = None,
    release_date: str | None = None,  # YYYY-MM-DD
    genres: str | None = None,
    production_companies: str | None = None,
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
    status: str | None = None,
    titleType: str | None = None,
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
    
    if production_companies is not None:
        query = query.filter(Movies.production_companies.contains(production_companies))

    if status is not None:
        query = query.filter(Movies.status == status)

    if titleType is not None:
        query = query.filter(Movies.titleType == titleType)

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
        'Genres': movie.genres,
        'Rating': movie.averageRating,
        'Votes': movie.numVotes,
        'Original_Language': movie.original_language,
        'Production_Companies': movie.production_companies,
        'Budget': movie.budget,
        'Revenue': movie.revenue,
        'Runtime': movie.runtime,
        'Status': movie.status,
        'Title_Type': movie.titleType,  
        'Keywords': movie.keywords,
        'Trailer_Views': movie.trailer_views,
        'Trailer_Likes': movie.trailer_likes
    } for movie in results
    ]


    return {
        "Query_Parameters": {
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
        'Matching_Movies': movies
    }

@app.post("/movies/upload/")
def upload_movies(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"Received upload request")  # Check if API receives request
    try:
        print(f"Received file: {file.filename}")  # Ensure file is read
        df = pd.read_csv(file.file, parse_dates=["release_date"])
        
        df["release_date"] = df["release_date"].dt.date  # Ensure date format
        
        record_added = 0
        skipped = 0

        for _, row in df.iterrows():
            # convert each value: if it’s NA-like → None, else leave it
            movie_data = {
                k: (None if pd.isna(v) or (isinstance(v, float) and math.isnan(v)) else v)
                for k, v in row.items()
            }

            if db.query(Movies).filter(
                Movies.primaryTitle == movie_data["primaryTitle"]).first():
                skipped += 1
                continue

            db.add(Movies(**movie_data))
            record_added += 1
        
        db.commit()
        print(f"Added: {record_added}, Skipped: {skipped}")  # Ensure commit happens

        return {"message": "Upload complete", "added": record_added, "skipped": skipped}
    
    except Exception as e:
        print("Error:", e)  # Log error in terminal
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.put("/movies/{title}/")
def update_movie(title: str,
                 titleType: str | None = None,
                 release_date: str | None = None,
                 genres: str | None = None,
                 directors: str | None = None,
                 writers: str | None = None,
                 actors: str | None = None,
                 status: str | None = None,
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

    if directors is not None:
        movie.directors = directors

    if writers is not None:
        movie.writers = writers

    if actors is not None:
        movie.actors = actors

    if status is not None:
        movie.status = status

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
                'status': movie.status,
                'keywords': movie.keywords,
                'trailer_views': movie.trailer_views,
                'trailer_likes': movie.trailer_likes    
            }}

@app.delete("/delete/")
def delete_movie(title: str, 
                 release_date: str,
                 db: Session = Depends(get_db)):
    """
    Delete a movie by title and release date
    """
    movie = db.query(Movies).filter(Movies.primaryTitle == title).filter(Movies.release_date == release_date).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db.delete(movie)
    db.commit()

    return {"message": "Movie deleted successfully"}

@app.post("/predict/{model_parameter}")
def prediction(model_parameter: str):
    try:
        cap_model = model_parameter.upper()
        msg = ml_pred.predict_revenue(cap_model)  # returns a str message
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return {"message": msg}

# Fixed vs code path error using "set PATH=%CONDA_PREFIX%\Scripts;%PATH%"
# Kill the app using "taskkill /IM uvicorn.exe /F"
# Checked registered API routes using "curl http://127.0.0.1:8000/openapi.json"

if __name__ == "__main__":
    uvicorn.run("movie_api:app", host="127.0.0.1", port=8000, reload=True, workers=1)