import requests

url = "http://127.0.0.1:8000/movies/upload/"
file_path = "data/movies.json"

with open(file_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

print(response.json())  # Check the response