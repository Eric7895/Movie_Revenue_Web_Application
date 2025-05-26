# Movie Revenue Web Application

![Alt text](image/website_screenshot_new.png)

## Objective ✔️

The main objectives are:
- Be able to make prediction on the revenue of movies that will be released in the next 5-6 months. 
- To experience on predicting box office revenue for movies using different approaches including sentiment analysis on user comments.
- To experience with API production and dashboard integration.

End Project: To deliver a web application supporting CRUD operation from data sources and can review revenue prediction results.

## Research Question:
- How can we control the inflation rate if we want to use early movies? (Using the Consumer Price Index could be a solution.) ✔️
- How do we standardize movie revenue? (The revenue variable we have is probably gross revenue since the movie's release, we can try to classified movie revenue into categories to standardized it to certain extent)
- Using information from five years earlier might not be reliable. (We can probably solve this issue by including more covariates) ✔️
---
## Data Source:
- https://www.imdb.com/list/ls026411399 (A director billboard)
- https://www.the-numbers.com/movies/release-schedule (For future movie release)
- https://developer.imdb.com/non-commercial-datasets/ (Official data provided by imdb)
- https://arxiv.org/pdf/2405.11651v1
- https://github.com/vikranth3140/movie-revenue-prediction
- https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies
- https://github.com/arnab-api/movie-analysis
- https://arxiv.org/pdf/2110.07039
---
## File Description:
- populate_data.py - Create the movie_data.csv file, by requesting downloadable IMDB official data, and integrated it with a pre-existing movie dataset for more featuring.
- data_encoding.py - Encoded qualitative variables of the movie_data.csv file and outputs the encoded file as a csv file.
- db.py - Set up the database connection (mysql in particular)
- models.py - Set up the table class
- populate_database - Imports movie_data.csv into the designated mysql database.
  - Requires mysql server, a database schema named 'movie_API', and your mysql key and password
- movie_api.py - RESTApi supporting Create, Read, Update, and Delete capability. 
---
## How to run the application
1) Create a virutal environment for this application, and ran pip install requirements.txt to install all the dependencies.
2) Fill out your MySQL username and password in db.py, and create a movie_API database using MySQL workbench. 
3) Run populate_data.py to get the latest information (Restricted by our raw file, we should be able to re-update the information once we figure out the source of the raw data file 'Movie_data.csv').
4) Run populate_database.py to populate (insert) the data to the MySQL database.
5) Run movie_API.py
---
## How to access prediction result
1) Upload a csv file align with database properties (Should be "Not released" movies)
2) Choose a predictive button
3) Search for "Not released" movie in parameter search 
