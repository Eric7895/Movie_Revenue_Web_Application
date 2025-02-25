import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import pickle

def get_movie_name() -> list:
    """
    This function gets all movie names from balanced.csv
    """
    path = 'data/balanced.csv'
    df = pd.read_csv(path)

    return list(df['primaryTitle'])

def format_movie_name(title: str) -> str:
    """
    This function replaces spaces with underscores and special characters
    with their URL-encoded equivalents.
    """
    title = title.replace(" ", "_")  # Replace spaces with underscores
    title = title.replace("&", "%26")  # Replace ampersands with %26
    title = title.replace("'", "%27")  # Replace apostrophes with %27
    title = title.replace(",", "%2C")  # Replace commas with %2C
    title = title.replace(":", "%3A")  # Replace colons with %3A
    title = title.replace("#", "%23")   # Replace hash symbol with %23
    title = title.replace("$", "%24")   # Replace dollar symbol with %24
    title = title.replace("%", "%25")   # Replace percent symbol with %25
    title = title.replace("(", "%28")   # Replace open parenthesis with %28
    title = title.replace(")", "%29")   # Replace close parenthesis with %29
    title = title.replace("*", "%2A")   # Replace asterisk with %2A
    title = title.replace("+", "%2B")   # Replace plus with %2B
    title = title.replace("=", "%3D")   # Replace equal sign with %3D
    title = title.replace("?", "%3F")   # Replace question mark with %3F
    title = title.replace("@", "%40")   # Replace @ symbol with %40
    title = title.replace("/", "%2F")   # Replace forward slash with %2F
    title = title.replace("[", "%5B")   # Replace open bracket with %5B
    title = title.replace("]", "%5D")   # Replace close bracket with %5D
    title = title.replace("^", "%5E")   # Replace caret with %5E
    title = title.replace("{", "%7B")   # Replace open curly bracket with %7B
    title = title.replace("}", "%7D")   # Replace close curly bracket with %7D
    title = title.replace("|", "%7C")   # Replace pipe symbol with %7C
    title = title.replace("~", "%7E")   # Replace tilde with %7E
    return title

def request_all_movie(names: list) -> list:
    """
    This function requestes all destinated wikipedia page. 
    """
    result = []
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    i = 0
    for name in names:
        url = f'https://en.wikipedia.org/wiki/{name}'
        r = requests.get(url, headers=header)
        if r.status_code != 200:
            print(f"Movie not found: {name}")
            # Try appending '_(film)' to the name if the movie is not found
            url = f'https://en.wikipedia.org/wiki/{name}_%28film%29'
            r = requests.get(url, headers=header)
            if r.status_code != 200:
                print(f"Also not found with '_(film)' added: {name}")
            else:
                print(f"Index {i} - Found movie with '_(film)' added: {name}")
                i += 1
        else:
            result.append(r.text)
            print(f"Index {i} - Found movie: {name}")
            i += 1

        time.sleep(1)  # Introduce a delay of 1 second between requests to avoid rate limiting

    return result


def save_requested_data(data: list, filename: str):
    """
    This function saves the scraped data to an external file (using pickle).
    """
    with open(filename, 'wb') as file:
        pickle.dump(data, file)
    print(f"Data has been saved to {filename}.")

def load_requested_data(filename: str) -> list:
    """
    This function loads the scraped data from an external file.
    """
    try:
        with open(filename, 'rb') as file:
            data = pickle.load(file)
        print(f"Data has been loaded from {filename}.")
        return data
    except FileNotFoundError:
        print(f"File {filename} not found. Please scrape the data first.")
        return []

def parse_single_html(html: str) -> str:
    '''
    This function acts as an html parser for the webpages.
    '''
    soup = BeautifulSoup(html, "html.parser")
    data = []
    table_section = (
        soup.find_all("table", class_ = "infobox vevent")
    )

    table_section = soup.find_all("table", class_="infobox vevent")

    for table in table_section:  # Iterate through the tables
        title = table.find("th", class_="infobox-above summary")
        if title:
            movie_name = title.get_text()

            starring_header = soup.find("th", string="Starring")

            if starring_header:
                starring_data = starring_header.find_next_sibling("td")
    
                if starring_data:
                    # Step 3: Extract actor names (from <a> tags inside <li>)
                    actors = [a.get_text() for a in starring_data.find_all("a")]

                data.append({
                    'name': movie_name,
                    'actors': actors
                })
        
    return data
    
def scraper():
    '''
    This function tries to scrap as much as web page as possible - First attempt
    '''
    names = get_movie_name()
    formatted_names = [format_movie_name(name) for name in names]
    
    # Try to load previously scraped data, if available
    filename = "scraped_data.pkl"
    requested_list = load_requested_data(filename)

    # If data is empty (not loaded), scrape the data
    if not requested_list:
        requested_list = request_all_movie(formatted_names)
        # Save the scraped data for future use
        save_requested_data(requested_list, filename)

    # Debug: Print movies that weren't scraped successfully
    for i, name in enumerate(formatted_names):
        if i >= len(requested_list):
            print(f"Movie not found: {name}")

    # Proceed with the next steps (e.g., process the scraped data)
    if len(requested_list) == len(formatted_names):
        print('All movies captured successfully.')
    else:
        print(f"Some movies were not captured. Total found: {len(requested_list)}, Total expected: {len(formatted_names)}")

def process_scraper():
    '''
    This function process the html page that we scraped. 
    '''
    # Read the requested data into a list
    filename = "scraped_data.pkl"
    requested_list = load_requested_data(filename)

    data = []

    for movie in requested_list:
        data.extend(parse_single_html(movie))
    
    df = pd.DataFrame(data)
    print(f'Shape of the data: {df.shape}')
    temp_actor = df.to_csv('temp_actor.csv')

if __name__ == '__main__':
    process_scraper()