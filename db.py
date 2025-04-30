from sqlalchemy import create_engine

def get_engine():
    username = ''
    password = ''
    host = 'localhost' 
    database = 'movie_API'
    return create_engine(f'mysql+pymysql://{username}:{password}@{host}/{database}')
