import math
import pickle
from pathlib import Path
from typing import Literal, Tuple, Callable

import numpy as np
import pandas as pd
from joblib import load
from xgboost import XGBRegressor
from sklearn.decomposition import PCA

from db import get_engine
from feature_engineering import main as fe_main

from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from models import Movies


Session_Local = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)

# -----------------------------------------------------------------------------
# numpy >= 1.24 removed the deprecated alias `np.int` — patch once, safe forever
# -----------------------------------------------------------------------------
if not hasattr(np, "int"):
    np.int = int  # type: ignore[attr-defined]

# -----------------------------------------------------------------------------
# constants & helpers
# -----------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
MODEL_DIR = ROOT_DIR / "model parameters"

# --------------------
# model wrappers
# --------------------

def _pred_from_log(joblib_path: Path, X: np.ndarray) -> np.ndarray:
    model = load(joblib_path)
    log_pred = model.predict(X)
    return np.expm1(log_pred)


def predict_mlr(X: np.ndarray) -> np.ndarray:
    return _pred_from_log(MODEL_DIR / "linear_model.joblib", X)


def predict_elastic_net(X: np.ndarray) -> np.ndarray:
    return _pred_from_log(MODEL_DIR / "elastic_net.joblib", X)


def predict_random_forest(X: np.ndarray) -> np.ndarray:
    return _pred_from_log(MODEL_DIR / "random_forest.joblib", X)


def predict_gam(X: np.ndarray) -> np.ndarray:
    with open(MODEL_DIR / "gam_model.pkl", "rb") as fh:
        gam = pickle.load(fh)
    log_pred = gam.predict(X)
    return np.expm1(log_pred)


def predict_xgboost(X: np.ndarray) -> np.ndarray:
    bst = XGBRegressor()
    bst.load_model(MODEL_DIR / "xgboost_model.json")
    return bst.predict(X)  # model was trained on natural‑scale revenue

def update_revenue(session, df: pd.DataFrame):
    """
    Update the database with predicted revenues, df must contain the models primary_key column(s) plus the new revenue
    """
    payload = df.to_dict(orient='records')
    session.bulk_update_mappings(Movies, payload)
    session.commit()

# (function, expects_poly)
Predictor = Tuple[Callable[[np.ndarray], np.ndarray], bool]

PREDICTORS: dict[str, Predictor] = {
    "MLR": (predict_mlr, False),     
    "EN": (predict_elastic_net, False),
    "RF": (predict_random_forest, True),
    "GAM": (predict_gam, False),
    "XG": (predict_xgboost, False),
}

# -----------------------------------------------------------------------------
# main driver
# -----------------------------------------------------------------------------

def predict_revenue(model_name: Literal["MLR", "EN", "RF", "GAM", "XG"], verbose: bool = False):
    if model_name not in PREDICTORS:
        raise ValueError(f"Unknown model option: {model_name}")

    pred_fn, needs_poly = PREDICTORS[model_name]

    engine = get_engine()
    unreleased_df = pd.read_sql("SELECT * FROM movie WHERE status != 'Released'", engine)

    full_df = pd.read_sql("SELECT * FROM movie", engine)

    if unreleased_df.empty:
        print("No unreleased movies found – nothing to predict.")
        return

    # ---------------------------------------------------------
    # universal feature engineering / encoding
    # ---------------------------------------------------------
    encoded_df = fe_main(unreleased_df, adjust_cpi=False)

    if verbose:
        print("Encoding complete.")

    df_clean = encoded_df[(encoded_df['trailer_views'] >= 0) & (encoded_df['trailer_likes'] >= 0)].copy()
    df_clean = df_clean.dropna(subset=['release_date', 'budget', 'actor_score'])  # Avoid null values

    df_clean['release_date'] = pd.to_datetime(df_clean['release_date'], errors='coerce')
    full_df['release_date'] = pd.to_datetime(full_df['release_date'], errors='coerce')

    df_clean['release_year'] = df_clean['release_date'].dt.year
    full_df['release_year'] = full_df['release_date'].dt.year

    df_clean['release_year_centered'] = df_clean['release_year'] - full_df['release_year'].mean()
    df_sorted_asc = df_clean.sort_values(by='release_date')

    important_feature_based_on_domain_expertise = ['budget', 'actor_score', 'star_score', 'trailer_views', 'trailer_likes', 'revenue', 'release_year', 'release_year_centered']
    test = df_sorted_asc[important_feature_based_on_domain_expertise].copy()

    test['trailer_likes_log'] = np.log1p(test['trailer_likes'])
    test['trailer_views_log'] = np.log1p(test['trailer_views'])
    test['budget_log'] = np.log1p(test['budget'])
    test['actor_score_log'] = np.log1p(test['actor_score'])
    test['budget_actor_interaction'] = test['budget_log'] * test['actor_score_log']

    test = test[['trailer_views_log', 'trailer_likes_log', 'budget_log', 'budget_actor_interaction', 'release_year_centered',
                'revenue']]

    pca = PCA()
    trailer_matrix = test[['trailer_views_log', 'trailer_likes_log']].values
    pca.fit(trailer_matrix)

    final_pca = PCA(n_components=1)

    pca_features = final_pca.fit_transform(trailer_matrix)
    test['trailer_pca'] = pca_features

    test.drop(columns=['trailer_views_log', 'trailer_likes_log'], inplace=True)

    try:
        X = test.drop('revenue', axis=1)
        if needs_poly:
            poly = load(MODEL_DIR / "poly_features.joblib")
            poly_features = poly.transform(X)
            X = poly_features # Convert df to darray
        
        y_pred = np.round(pred_fn(X), 2)

    except Exception as e:
        return f"Error: {e}"

    # ---------------------------------------------------------
    # predict & persist
    # ---------------------------------------------------------

    pred_df = unreleased_df.loc[df_sorted_asc.index].copy()
    pred_df["revenue"] = y_pred

    pred_df.drop(['is_holiday_release', 'is_competitive_month', 'lang_en', 'lang_other'], axis=1, inplace=True)

    # overwrite / merge back to DB 
    with Session_Local() as session:  
        update_revenue(session, pred_df[["primaryTitle", "release_date", "revenue"]])

    return f"[{model_name}] – wrote {len(pred_df)} predictions to DB"

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    for mdl in PREDICTORS.keys():
        print(f"Predicting {mdl}")
        msg = predict_revenue(mdl, verbose=True)
        print(msg)