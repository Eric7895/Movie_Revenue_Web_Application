import pandas as pd
from sqlalchemy.orm import sessionmaker
from models import Movies, Base
from db import get_engine
from feature_engineering import features_encoding
import os

engine = get_engine()
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Check if there's encoded data
if not os.path.exists('data/movie_data_encoded.csv'):
    features_encoding()

df = pd.read_csv('data/movie_data_encoded.csv')