import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
import cpi 
import os
from scraper.actor_bill_board_scraper import actor_scraper

# ==============================
#           HELPERS
# ==============================

def CPI_adjustment(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Convert budget and revenue to real dollar (CPI conversion)
    '''
    for i in range(len(df)):
        year = int(df['release_date'].iloc[i].split('-')[0])
        budget = df['budget'].iloc[i]
        revenue = df['revenue'].iloc[i]
        df.loc[i, 'budget'] = cpi.inflate(budget, year)
        df.loc[i, 'revenue'] = cpi.inflate(revenue, year)

    return df

def encoding_people(df: pd.DataFrame, name_list: list, column_name: str, score_name: str, if_actor=False) -> pd.DataFrame:
    '''
    This function helps to encode all director, writer, and actor information by computing a score for total famous people.
    If if_actor is True, it also adds a binary column 'is_documentary' that is 1 if actor information is missing (indicating a documentary)
    and 0 otherwise.
    '''
    output_df = []
    for i in range(len(df)):
        movie_title = df['primaryTitle'].iloc[i]
        # For actor information, check if the value is missing or empty
        if if_actor:
            # Here we assume actor info is stored as a list
            actor_info = df[column_name].iloc[i]
            if pd.isnull(actor_info) or (isinstance(actor_info, list) and len(actor_info) == 0):
                output_df.append({'name': movie_title, score_name: 0, 'is_documentary': 1})
                continue
            else:
                is_documentary_flag = 0
                names = actor_info
        else:
            # For director/writer, assume the info is a comma-separated string
            if pd.isnull(df[column_name].iloc[i]):
                output_df.append({'name': movie_title, score_name: np.nan})
                continue
            names = df[column_name].iloc[i].split(',')
        
        score = 0
        for name in names:
            if name_list.count(name) > 0:
                score += 1
        
        if if_actor:
            output_df.append({'name': movie_title, score_name: score, 'is_documentary': is_documentary_flag})
        else:
            output_df.append({'name': movie_title, score_name: score})
            
    return pd.DataFrame(output_df).drop_duplicates(['name'])

def encoding_genre(df: pd.DataFrame) -> pd.DataFrame:
    '''
    This function helps to encode genre information based on the first genre information (Probably primary genre)
    '''

    category_df = []

    for i in range(len(df)):
        movie_title = df['primaryTitle'].iloc[i]
        genres = df['genres'].iloc[i].split(',')
            
        if genres[0] == '\\N':
            category_df.append({'name': movie_title, 'genres': np.nan})
            continue
        category_df.append({'name': movie_title, 'genres': genres[0]})
    
    return pd.get_dummies(pd.DataFrame(category_df), columns=['genres'], dtype=float).drop_duplicates(['name'])

def encoding_date(df: pd.DataFrame) -> pd.DataFrame:
    '''
    This function helps to encode date information.
    '''

    output_df = []

    month_dict = {
        '01': 'January',
        '02': 'February',
        '03': 'March',
        '04': 'April',
        '05': 'May',
        '06': 'June',
        '07': 'July',
        '08': 'August',
        '09': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December'
    }

    for i in range(len(df)):
        name = df['primaryTitle'].iloc[i]
        month = df['release_date'].iloc[i].split('-')[1]
        if month in month_dict:
            output_df.append({'name': name, 'month': month_dict[month]})

    return pd.get_dummies(pd.DataFrame(output_df), columns=['month'], dtype=float)

def encoding_production_companies(df: pd.DataFrame, top_companies: list = None,
                                        column_name: str = 'production_companies',
                                        score_name: str = 'production_popular') -> pd.DataFrame:
    '''
    This function help encode whether a movie is from a well-known production company. (0/1)
    '''
    if top_companies is None:
        top_companies = [
            'Warner Bros', 'Universal Pictures', 'Walt Disney',
            'Columbia Pictures', '20th Century Fox', 'Paramount',
            'Marvel Studios', 'New Line', 'DreamWorks', 'Lionsgate',
            'MGM', 'Sony Pictures', 'Lucasfilm',
            'Pixar', 'Legendary', 'A24', 'Focus Features',
            'Amblin', 'Working Title', 'StudioCanal', 'Castle Rock'
        ]

    match_count = 0
    total_count = 0

    output_df = []
    for i in range(len(df)):
        movie_title = df.iloc[i, 0]

        if pd.isna(df[column_name].iloc[i]) or not isinstance(df[column_name].iloc[i], str):
            output_df.append({'name': movie_title, score_name: 0})
            continue

        total_count += 1
        companies_text = df[column_name].iloc[i]

        companies = companies_text.split(',')

        score = 0
        for company in companies:
            company = company.strip()
            for top_company in top_companies:
                if top_company.lower() in company.lower():
                    score += 1
                    break

        if score == 0:
            for top_company in top_companies:
                if top_company.lower() in companies_text.lower():
                    score += 1

        if score > 0:
            match_count += 1

        output_df.append({'name': movie_title, score_name: score})

    return pd.DataFrame(output_df).drop_duplicates(['name'])

def encoding_top_languages(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    '''
    This function helps to encode language information by selecting the top N most frequent languages
    from the 'original_language' column and one-hot encoding them. Languages not in the top N are grouped 
    into an 'other' category.

    '''
    # Fill missing values
    df['original_language'] = df['original_language'].fillna('unknown')
    
    # Count frequency of each language and get the top N languages
    language_counts = df['original_language'].value_counts()
    top_languages = list(language_counts.head(top_n).index)
    
    # Initialize new columns for the top languages and an "other" column
    for lang in top_languages:
        df[f'lang_{lang}'] = 0.0
    df['lang_other'] = 0.0
    
    # Iterate over each row and assign one-hot encoding values based on the language
    for index, row in df.iterrows():
        lang = row['original_language']
        if lang in top_languages:
            df.at[index, f'lang_{lang}'] = 1.0
        else:
            df.at[index, 'lang_other'] = 1.0
            
    return df

def encode_keyword(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    '''
    This function uses a pre-trained BERT model to generate high-dimensional semantic embeddings
    from the 'keywords' column. It applies max pooling to aggregate multiple phrase embeddings into a single
    representation per row, then uses PCA to reduce the dimensionality and selects the primary principal component
    as the final encoding. Additionally, it adds a binary column 'has_keywords' indicating whether keywords exist (1)
    or are missing (0).
    '''
    # Create a binary indicator for keywords before filling null values
    df['has_keywords'] = df['keywords'].notnull().astype(int)
    df['keywords'] = df['keywords'].fillna('no_keywords')

    model = SentenceTransformer('all-mpnet-base-v2')

    def get_embeddings(keyword_string: str) -> np.ndarray:
        phrases = keyword_string.split('-')
        embeddings = model.encode(phrases)
        return np.max(embeddings, axis=0)  # Max pooling - Aggregation

    df['embedding'] = df['keywords'].apply(get_embeddings)

    # Convert embeddings to matrix
    embedding_matrix = np.vstack(df['embedding'].values)

    pca = PCA()
    pca.fit(embedding_matrix)

    # Print variance ratio
    if verbose:
        print(f"Variance explained by first component: {pca.explained_variance_ratio_[0]:.2%}")
        print(f"Cumulative variance for first 3 components: {pca.explained_variance_ratio_[:3].sum():.2%}")

    final_pca = PCA(n_components=1)

    pca_features = final_pca.fit_transform(embedding_matrix)

    pca_columns = [f'keyword_embedding' for _ in range(1)]
    pca_df = pd.DataFrame(pca_features, columns=pca_columns, index=df.index)
    result = df.join(pca_df).drop(['embedding'], axis=1)

    return result

# ==============================
#           Main
# ==============================

def main(verbose=False, year: int = 2025):
    path1 = 'data/movie_data.csv'
    path2 = 'raw data/the_most_popular_director_imdb.csv'

    year_list = [year - i for i in range(5)]

    actor_list = []

    for year in year_list:
        actor_list.append((f'actor scraper/actor_{year}.csv', year))

    for table, year in actor_list:
        if not os.path.exists(table):
            actor_scraper(year)
    
    actor1 = pd.read_csv(actor_list[0][0])
    actor2 = pd.read_csv(actor_list[1][0])
    actor3 = pd.read_csv(actor_list[2][0])
    actor4 = pd.read_csv(actor_list[3][0])
    actor5 = pd.read_csv(actor_list[4][0])

    director_writer_names = list(pd.read_csv(path2)['Name'].drop_duplicates())
    actors = pd.concat([actor1, actor2, actor3, actor4, actor5], ignore_index=True)
    movie_stg0 = pd.read_csv(path1)

    # Movie_stg0 has the following column and index
    # Index 0: primaryTitle
    # Index 1: titleType
    # Index 2: genres
    # Index 3: directors
    # Index 4: writers
    # Index 5: averageRating
    # Index 6: numVotes
    # Index 7: actors
    # Index 8: original_language
    # Index 9: production_companies
    # Index 10: release_date
    # Index 11: budget
    # Index 12: revenue
    # Index 13: runtime
    # Index 14: keywords
    # Index 15: trailer_views
    # Index 16: trailer_likes

    # Phase 1: Initial encoding of categorical variables and features (movie_stg1)
    movie_type = pd.get_dummies(movie_stg0, columns=['titleType'], dtype=float)
    director = encoding_people(movie_stg0, director_writer_names, 'directors', 'director_score')
    writer = encoding_people(movie_stg0, director_writer_names, 'writers', 'writer_score')
    actor = encoding_people(movie_stg0, actors['name'].to_list(), 'actors', 'actor_score', if_actor=True)
    genre = encoding_genre(movie_stg0)
    date = encoding_date(movie_stg0)
    production = encoding_production_companies(movie_stg0)
    language = encoding_top_languages(movie_stg0)

    # Aggregate all the encoded features into movie_stg1
    movie_type.rename(columns={'primaryTitle': 'name'}, inplace=True)
    movie_stg1 = movie_type.merge(director, on='name', how='left')\
                            .merge(writer, on='name', how='left')\
                            .merge(actor, on='name', how='left')\
                            .merge(genre, on='name', how='left')\
                            .merge(date, on='name', how='left')\
                            .merge(production, on='name', how='left')
    
    # We merge the language columns. Assume language columns are those starting with 'lang_'.
    language_cols = [col for col in language.columns if col.startswith('lang_')]
    movie_stg1 = movie_stg1.merge(language[['primaryTitle'] + language_cols].rename(columns={'primaryTitle':'name'}), on='name', how='left')

    if verbose:
        print("Phase 1 completed: Aggregated all encoded features into movie_stg1")

    # Phase 2: CPI adjustment (movie_stg2)
    movie_stg2 = CPI_adjustment(movie_stg1.copy())
    if verbose:
        print("Phase 2 completed: Applied CPI adjustment to create movie_stg2")

    # Phase 3: Keyword encoding using BERT (movie_stg3)
    movie_stg3 = encode_keyword(movie_stg2.copy(), verbose=verbose).drop_duplicates(['name'])
    if verbose:
        print("Phase 3 completed: Applied keyword encoding to create movie_stg3")

    # Return final DataFrame
    return movie_stg3

if __name__ == '__main__':
    final_df = main(verbose=True)
    final_df.to_csv('data/movie_data_encoded.csv')
