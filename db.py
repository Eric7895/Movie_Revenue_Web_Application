from sqlalchemy import create_engine
    
def get_engine():
    username = 'N/A'
    password = 'N/A'
    host = 'localhost'  
    database = 'movie_API'
    return create_engine(f'mysql+pymysql://{username}:{password}@{host}/{database}')