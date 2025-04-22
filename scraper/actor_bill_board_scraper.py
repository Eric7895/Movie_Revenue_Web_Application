import pandas as pd
import requests
import queue
import os
import pickle
from bs4 import BeautifulSoup

# ==============================
#           HELPERS
# ==============================

def save_requested_data(data: list, filename: str) -> None:
    '''
    Save scraped HTML content using pickle.
    '''
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)  # Ensure the directory exists
    
    with open(filename, 'wb') as file:
        pickle.dump(data, file)
    print(f"Data saved to {filename}.")


def load_requested_data(filename: str) -> list:
    '''
    Load previously saved HTML content.
    '''
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            data = pickle.load(file)
        print(f"Data loaded from {filename}.")
        return data
    print(f"File {filename} not found. Please scrape data first.")
    return []

# ==============================
#       WEB SCRAPING
# ==============================

def request_all_table(year: int = 2025) -> list:
    '''
    Fetch Actor billboard
    '''
    q = queue.Queue()

    result = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    base_url = f"https://www.the-numbers.com/box-office-star-records/worldwide/yearly-acting/highest-grossing-{year}-stars"
    # Add first two pages
    q.put(base_url)
    q.put(f"{base_url}/101")

    num = 2  # Next page starts from 201

    while not q.empty():
        url = q.get()
        print(f'working on {url}')
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Find the div containing the message
            
                divs = soup.find_all(id="page_filling_chart")
                
                # Check if it contains the "no movies" message
                for div in divs:
                    if "*** There are no movies yet meeting the requirements for this record list ***" in div.get_text():
                        print("Reached an empty page. Stopping.")
                        return result
                
                result.append(response.text)
                
                # Queue the next page
                next_page = f"{base_url}/{num}01"
                q.put(next_page)
                num += 1
            elif response.status_code == 404:
                print(f"Page not found: {url}")
                break  # Stop if a page is not found
        except requests.ConnectionError:
            print(f"Connection error occurred while accessing: {url}")
            break  # Stop if connection fails
    
    return result

# ==============================
#       HTML PARSING
# ==============================

def parse_single_html(html: str) -> list | None:
    '''
    Extract actor information from single html page
    '''
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    data = tables[-1].find_all("tr")

    full_list = []

    if not tables:
        return None  # No infobox found, likely an incorrect page
    
    for i in data:

        record = i.find_all("td")

        if len(record) == 5:

            rank = record[0].text.strip()
            name = record[1].text.strip()
            star_score = record[2].text.strip()
            movies = record[3].text.strip()
            average_billing = record[4].text.strip()

            actor_info = {
                "rank": rank,
                "name": name,
                "star_score": star_score,
                "movies": movies,
                "average_billing": average_billing
            }

            full_list.append(actor_info)

    return full_list

# ==============================
#       MAIN SCRAPER
# ==============================

def scraper(year: int) -> None:
    '''
    Main scraping function: retrieves actor data and saves HTML pages.
    '''

    filename = r"actor data/scraped_data.pkl"
    scraped_data = load_requested_data(filename)

    if not scraped_data:
        scraped_data = request_all_table(year)
        save_requested_data(scraped_data, filename)  # Save after scraping
        print(f'\nScraping completed.\n')
    else:
        print(f'\nScraping completed.\n')

def parser(year: int) -> None:
    '''
    Parse HTML content and store extracted actor data.
    '''
    filename = r"actor data/scraped_data.pkl"
    scraped_data = load_requested_data(filename)
    actor_path = f"actor data/actor_{year}.csv"

    df = []
    existing_names = set()
    
    for i, html in enumerate(scraped_data):
        records = parse_single_html(html) # records being list of dictionaries
        for record in records:
            df.append(record)
            existing_names.add(record["name"])
    
    actor = pd.DataFrame(df)
    actor.to_csv(actor_path, index=False)
    print(f"Successfully parsed actor data. Total records: {len(actor)}")

def actor_scraper(year):
    scraper(year)
    parser(year)

if __name__ == "__main__":
    actor_scraper(year=2025)