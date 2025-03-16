from sqlalchemy import create_engine
import os

def get_user_and_password():
    if os.path.exists('mysql_password.txt'):
        with open('mysql_password.txt', 'r') as file:
            for line in file:
                if 'username' in line:
                    username = line.split('=')[1].strip()
                elif 'password' in line:
                    password = line.split('=')[1].strip()

        return username, password
    else:
        return 'File not found', 0
    
def get_engine():
    username, password = get_user_and_password()

    if username == 'File not found':
        return 'Create mysql_password.txt first'

    host = 'localhost'  
    database = 'movie_API'
    return create_engine(f'mysql+pymysql://{username}:{password}@{host}/{database}')
