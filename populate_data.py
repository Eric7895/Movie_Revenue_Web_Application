import pandas as pd
import numpy as np
import os
import requests
import gzip
import shutil

# ==============================
#           HELPERS
# ==============================
def make_dict(df: pd.DataFrame, key_index: int, value_index: int) -> dict:
    """
    Create a dictionary mapping IDs (from key_index) to names (from value_index).
    """
    result = {}
    for i in range(len(df)):
        result[df.iloc[i, key_index]] = df.iloc[i, value_index]
    return result

def convert_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a year-only variable from a year-month-day string.
    """
    years = []
    for i in range(df.shape[0]):
        try:
            years.append(df.iloc[i, 7][:4])
        except Exception:
            years.append(None)
    df['year_released'] = years
    return df

def load_imdb(filename: str) -> pd.DataFrame | None:
    """
    Load processed IMDb data from a CSV file.
    """
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        print(f"File {filename} not found. Please use imdb_data() to create the file.")
        return None

def unmasked_director_writer(df: pd.DataFrame, name_dict: dict) -> pd.DataFrame:
    """
    Unmask both the directors and writers of the IMDb dataset using name_dict.
    """
    df_copy = df.copy(deep=True).reset_index(drop=True)
    for i in range(len(df_copy)):
        directors = df_copy.iloc[i, 6]  # Column 6: 'directors'
        writers = df_copy.iloc[i, 7]    # Column 7: 'writers'

        directors_list = [] if pd.isna(directors) or directors == '\\\\N' else directors.split(',')
        writers_list = [] if pd.isna(writers) or writers == '\\\\N' else writers.split(',')

        # Map IDs to names (strip whitespace)
        directors_list = [name_dict.get(d.strip(), d) for d in directors_list]
        writers_list = [name_dict.get(w.strip(), w) for w in writers_list]

        df_copy.at[i, 'directors'] = ','.join(directors_list) if directors_list else np.nan
        df_copy.at[i, 'writers'] = ','.join(writers_list) if writers_list else np.nan

    return df_copy

def get_actor_info(df: pd.DataFrame, name_dict: dict, title_dict: dict) -> pd.DataFrame:
    """
    Retrieve actor information for each movie using principals.tsv.
    """
    df_copy = df.copy(deep=True).reset_index(drop=True)
    actors_df = df_copy[df_copy['category'].isin(['actor', 'actress'])]
    actor_dict = {}
    for _, row in actors_df.iterrows():
        movie_title = row['tconst']
        actor_id = row['nconst']
        # Map actor and title IDs to unmasked names
        unmasked_actor = name_dict.get(actor_id, actor_id)
        unmasked_title = title_dict.get(movie_title, movie_title)
        if unmasked_title not in actor_dict:
            actor_dict[unmasked_title] = [unmasked_actor]
        else:
            actor_dict[unmasked_title].append(unmasked_actor)
    return pd.DataFrame(actor_dict.items(), columns=['title', 'actors'])

def download_and_extract_imdb_data(url: str, dest_folder: str) -> None:
    """
    Download and extract a gzipped TSV file from the given URL into dest_folder.
    If the extracted file already exists, the function skips downloading.
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    filename = os.path.basename(url)
    gz_path = os.path.join(dest_folder, filename)
    extracted_path = os.path.join(dest_folder, filename[:-3])  # Remove '.gz'

    # Check if extracted file exists
    if os.path.exists(extracted_path):
        print(f"{extracted_path} already exists. Skipping download and extraction.")
        return

    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(gz_path, 'wb') as f:
            f.write(response.raw.read())
        print(f"Downloaded {filename} successfully.")
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")
        return

    print(f"Extracting {filename}...")
    with gzip.open(gz_path, 'rb') as f_in, open(extracted_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"Extracted to {extracted_path}.")

    # Remove the gz file to save space
    os.remove(gz_path)
    print(f"Removed the compressed file {gz_path}.")

# ==============================
#           Merge
# ==============================
def imdb_data(verbose=False):
    """
    Process all IMDb data files, merging them into one DataFrame.
    Downloads and extracts data if necessary.
    """
    if verbose:
        print("Starting IMDb data merge...")

    # Define file paths for extracted TSV files
    base_folder = 'IMDB_Official_Data'
    path1 = os.path.join(base_folder, 'name.basics.tsv')
    path2 = os.path.join(base_folder, 'title.akas.tsv')
    path3 = os.path.join(base_folder, 'title.basics.tsv')
    path4 = os.path.join(base_folder, 'title.crew.tsv')
    path5 = os.path.join(base_folder, 'title.principals.tsv')
    path6 = os.path.join(base_folder, 'title.ratings.tsv')

    # Download and extract files if any are missing
    if not (os.path.exists(path1) and os.path.exists(path2) and os.path.exists(path3) and
            os.path.exists(path4) and os.path.exists(path5) and os.path.exists(path6)):
        download_and_extract_imdb_data('https://datasets.imdbws.com/name.basics.tsv.gz', base_folder)
        download_and_extract_imdb_data('https://datasets.imdbws.com/title.akas.tsv.gz', base_folder)
        download_and_extract_imdb_data('https://datasets.imdbws.com/title.basics.tsv.gz', base_folder)
        download_and_extract_imdb_data('https://datasets.imdbws.com/title.crew.tsv.gz', base_folder)
        download_and_extract_imdb_data('https://datasets.imdbws.com/title.principals.tsv.gz', base_folder)
        download_and_extract_imdb_data('https://datasets.imdbws.com/title.ratings.tsv.gz', base_folder)

    # Load TSV files into DataFrames
    people = pd.read_csv(path1, sep='\t', low_memory=False)
    skeleton_1 = pd.read_csv(path2, sep='\t', low_memory=False)
    skeleton_2 = pd.read_csv(path3, sep='\t', low_memory=False)
    crew = pd.read_csv(path4, sep='\t', low_memory=False)
    principals = pd.read_csv(path5, sep='\t', low_memory=False)
    rating = pd.read_csv(path6, sep='\t', low_memory=False)

    if verbose:
        print("Finished reading IMDb data files.")

    # Build lookup dictionaries
    name_dict = make_dict(people, 0, 1)
    title_dict = make_dict(skeleton_2, 0, 2)

    actors = get_actor_info(principals, name_dict, title_dict)

    # Merge datasets
    imdb_stg0 = skeleton_1.join(
        skeleton_2.set_index('tconst'), on='titleId'
    ).join(
        crew.set_index('tconst'), on='titleId'
    ).join(
        rating.set_index('tconst'), on='titleId'
    )
    
    if verbose:
        print("Finished initial merge (stage 0).")

    imdb_stg0 = imdb_stg0[['titleId', 'primaryTitle', 'originalTitle', 'titleType', 
                             'startYear', 'genres', 'directors', 'writers', 
                             'averageRating', 'numVotes']].drop_duplicates(subset=['titleId']).dropna()

    imdb_stg1 = unmasked_director_writer(imdb_stg0, name_dict)
    if verbose:
        print("Finished unmasking directors and writers (stage 1).")

    imdb_stg2 = imdb_stg1.join(actors.set_index('title'), on='primaryTitle')
    if verbose:
        print("Finished merging actor information (stage 2).")

    imdb_stg3 = imdb_stg2[imdb_stg2['titleType'].isin(['movie', 'tvMovie'])]
    if verbose:
        print("Filtered for movies and TV movies (stage 3).")

    # Save the merged DataFrame to CSV
    os.makedirs('data', exist_ok=True)
    imdb_stg3.to_csv('data/imdb.csv', index=False)

    return imdb_stg3

def main_merge():
    """
    Merge IMDb data with Movie_data.csv after initial cleaning.
    """
    imdb = load_imdb('data/imdb.csv')
    if imdb is None or imdb.empty:
        imdb = imdb_data(verbose=True)

    second_df = pd.read_csv('raw data/Movie_data.csv')
    second_df_with_year = convert_year(second_df)

    movie_stg0 = imdb.merge(second_df_with_year, 
                            left_on=['primaryTitle', 'startYear'],
                            right_on=['title', 'year_released'])
    
    movie_stg1 = movie_stg0.drop(['titleId', 'originalTitle', 'startYear', 'id', 'title', 'genres_y',
                                  'overview', 'popularity', 'status', 'tagline', 'vote_average', 'vote_count',
                                  'credits', 'poster_path', 'backdrop_path', 'recommendations',
                                  'year_released'], axis=1
                                  ).drop_duplicates(['primaryTitle', 'release_date']
                                  ).dropna(subset=['production_companies', 'runtime']
                                  ).rename(columns={'genres_x': 'genres'})
    
    os.makedirs('data', exist_ok=True)
    movie_stg1.to_csv('data/movie_data.csv', index=False)

if __name__ == '__main__':
    main_merge()
