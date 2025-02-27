import os
import time
import pickle
import urllib.parse
import requests
import openpyxl
import pandas as pd
from bs4 import BeautifulSoup


# ==============================
#           HELPERS
# ==============================

def get_stopping_point() -> int:
    """Retrieve the last stopping index to resume scraping after failure."""
    filename = "wikipedia scraper/stopping_point.txt"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            try:
                return int(file.read().strip())  # Read last index
            except ValueError:
                return 0  # Default to 0 if file is corrupted
    return 0  # Start fresh if file doesn't exist


def save_stopping_point(index: int) -> None:
    """Save the current stopping point to allow resumption after failure."""
    filename = "wikipedia scraper/stopping_point.txt"
    with open(filename, "w") as file:
        file.write(str(index))


def save_requested_data(data: list, filename: str) -> None:
    """Save scraped HTML content using pickle."""
    with open(filename, 'wb') as file:
        pickle.dump(data, file)
    print(f"Data saved to {filename}.")


def load_requested_data(filename: str) -> list:
    """Load previously saved HTML content."""
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            data = pickle.load(file)
        print(f"Data loaded from {filename}.")
        return data
    print(f"File {filename} not found. Please scrape data first.")
    return []


def get_movie_list() -> tuple[pd.DataFrame, set]:
    """Retrieve movie names and years from balanced.csv, filtering out already scraped movies."""
    path_movies = 'data/balanced.csv'
    df_movies = pd.read_csv(path_movies)

    path_scraped = 'wikipedia scraper/temp_actor.csv'
    if os.path.exists(path_scraped):
        df_scraped = pd.read_csv(path_scraped)
        scraped_movies = set(df_scraped['name'].astype(str))  # Convert to set for fast lookup
    else:
        print("temp_actor.csv not found. Scraping all movies.")
        scraped_movies = set()

    target_movies = df_movies[['primaryTitle', 'startYear']].drop_duplicates()
    target_movies = target_movies[~target_movies['primaryTitle'].isin(scraped_movies)]

    return target_movies, scraped_movies


def format_movie_name(title: str) -> str:
    """Format movie title by replacing spaces with underscores and encoding special characters."""
    return urllib.parse.quote(title.replace(" ", "_"), safe="_")


# ==============================
#       WEB SCRAPING
# ==============================

def request_all_movies(movies: pd.DataFrame, start_index: int = 0) -> list:
    """Fetch Wikipedia pages for each movie, trying three URL variations."""
    result = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    for i in range(start_index, len(movies)):
        name, year = movies.iloc[i, 0], movies.iloc[i, 1]
        urls = [
            f'https://en.wikipedia.org/wiki/{name}',
            f'https://en.wikipedia.org/wiki/{name}_%28film%29',
            f'https://en.wikipedia.org/wiki/{name}_%28{year}_film%29'
        ]

        for url in urls:
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    result.append(response.text)
                    print(f"Index {i}: Found movie page - {url}")
                    save_stopping_point(i)  # Save progress
                    break  # Stop trying once a valid page is found
                else:
                    print(f"Index {i}: Movie not found - {url}")
            except requests.ConnectionError:
                print(f"Index {i}: Connection error. Stopping...")
                save_stopping_point(i)
                return result  # Stop and save progress

        time.sleep(1)  # Delay to avoid rate limiting

    return result


# ==============================
#       HTML PARSING
# ==============================

def parse_movie_html(html: str) -> dict | None:
    """Extract movie name and cast from Wikipedia infobox."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_="infobox vevent")

    if not tables:
        return None  # No infobox found, likely an incorrect page

    for table in tables:
        title = table.find("th", class_="infobox-above summary")
        if title:
            movie_name = title.get_text()
            starring_headers = ["Starring", "Cast"]

            for keyword in starring_headers:
                starring_header = soup.find("th", string=keyword)
                if starring_header:
                    starring_data = starring_header.find_next_sibling("td")
                    if starring_data:
                        actors = [li.get_text(strip=True) for li in starring_data.find_all("li")]
                        return {'name': movie_name, 'actors': actors}

            return {'name': movie_name, 'actors': []}  # No actors found

    return None  # No valid movie title found


# ==============================
#       MAIN SCRAPER
# ==============================

def scraper() -> None:
    """Main scraping function: retrieves movie data and saves HTML pages."""
    target_movies, _ = get_movie_list()
    target_movies['primaryTitle'] = target_movies['primaryTitle'].map(format_movie_name)

    filename = 'wikipedia scraper/scraped_data.pkl'
    scraped_data = load_requested_data(filename)
    start_index = get_stopping_point()

    if not scraped_data:
        scraped_data = request_all_movies(target_movies, start_index)
    else:
        print(f"Resuming scraping from index {start_index}...")
        new_data = request_all_movies(target_movies, start_index)
        scraped_data.extend(new_data)

    save_requested_data(scraped_data, filename)
    print("\nScraping completed.\n")


def parser() -> None:
    """Parse HTML content and store extracted movie-actor data."""
    filename = "wikipedia scraper/scraped_data.pkl"
    scraped_data = load_requested_data(filename)
    temp_actor_path = "wikipedia scraper/temp_actor.csv"

    if os.path.exists(temp_actor_path):
        df_existing = pd.read_csv(temp_actor_path)
        existing_names = set(df_existing['name'])
    else:
        df_existing = pd.DataFrame(columns=['name', 'actors'])
        existing_names = set()

    new_data = []
    for index, html in enumerate(scraped_data):
        print(f'Processing index: {index}')
        record = parse_movie_html(html)

        if record and record["name"] not in existing_names:
            new_data.append(record)
            existing_names.add(record["name"])

    if new_data:
        df_new = pd.DataFrame(new_data)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True).drop_duplicates(subset='name')
        df_combined.to_csv(temp_actor_path, index=False)
        print(f"Updated actor dataset. Total records: {len(df_combined)}")
    else:
        print("No new data to append.")


# ==============================
#   CLEANING & FINAL DATASET
# ==============================

def clean_dataset() -> None:
    """Merge scraped actor data with balanced dataset and generate the final dataset."""
    df_movies = pd.read_csv("data/balanced.csv")
    df_actors = pd.read_csv("wikipedia scraper/temp_actor.csv")

    merged_df = df_movies.merge(df_actors, left_on="primaryTitle", right_on="name", how="left")
    merged_df = merged_df.drop(columns=['name'])
    
    merged_df.to_excel('data/final_dataset.xlsx', index=False)
    merged_df.to_csv('data/final_dataset.csv', index=False)
    print("\nFinal dataset saved as 'final_dataset.csv'.\n")


def dataset_summary() -> None:
    """Print summary statistics of the final dataset."""
    df = pd.read_csv('data/final_dataset.csv')
    print(df.info())
    print(df.describe())


if __name__ == '__main__':
    #scraper()
    #parser()
    #clean_dataset()
    dataset_summary()
