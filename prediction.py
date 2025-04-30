import math
import pickle
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from joblib import load
from sqlalchemy.orm import Session, sessionmaker
from xgboost import XGBRegressor
from sklearn.decomposition import PCA

from db import get_engine
from feature_engineering import main as fe_main
from models import Movies, Base

MODEL_DIR = Path("model parameters")

# ==============================
#           Models
# ==============================

def pred_from_log_model(model_path: Path, X: np.ndarray) -> np.ndarray:
    """
    Load a scikit‑learn model saved with *joblib* and return *revenue* predictions.

    The model is assumed to have been trained on ``log1p(revenue)``; we therefore apply
    ``np.expm1`` to get back to the original scale.
    """
    model = load(model_path)
    log_pred = model.predict(X)
    return np.expm1(log_pred)

def predict_mlr(X_poly: np.ndarray) -> np.ndarray:
    return pred_from_log_model(MODEL_DIR / "linear_model.joblib", X_poly)

def predict_elastic_net(X_poly: np.ndarray) -> np.ndarray:
    return pred_from_log_model(MODEL_DIR / "elastic_net_model.joblib", X_poly)


def predict_random_forest(X: np.ndarray) -> np.ndarray:
    return pred_from_log_model(Path("random_forest_model.joblib"), X)


def predict_gam(X: np.ndarray) -> np.ndarray:
    with open(MODEL_DIR / "gam_model.pkl", "rb") as fh:
        gam = pickle.load(fh)
    log_pred = gam.predict(X)
    return np.expm1(log_pred)

def predict_xgboost(X: np.ndarray) -> np.ndarray:
    bst = XGBRegressor()
    bst.load_model("xgboost_model.json")
    pred = bst.predict(X)
    # XGBoost was trained on revenue directly (not log‑scaled)
    return pred

# Map option strings to the corresponding prediction function and whether the model expects polynomial features.
PREDICTORS: dict[str, tuple[callable, bool]] = {
    "MLR": (predict_mlr, True),
    "elastic_net": (predict_elastic_net, True),
    "rf": (predict_random_forest, False),
    "GAM": (predict_gam, False),
    "XGBoost": (predict_xgboost, False),
}

def predict_revenue(model_name: Literal["MLR", "elastic_net", "rf", "GAM", "XGBoost"]):
    """
    Predict revenues for movies whose *status* is "Not Released" and persist them.
    """
    if model_name not in PREDICTORS:
        raise ValueError(f"Unknown model option: {model_name}")
    
    pred_model, needs_poly = PREDICTORS[model_name]

    engine = get_engine()
    query = "SELECT * FROM movie WHERE status != 'Released'"
    unreleased_df = pd.read_sql(query, engine)

    if unreleased_df.empty:
        print("No unreleased movies found – nothing to predict.")
        return
    
    encoded_df = fe_main(unreleased_df, adjust_cpi=False) # Encode all features
    
    df_clean = encoded_df[(unreleased_df['trailer_views'] >= 0) & (unreleased_df['trailer_likes'] >= 0)].copy()
    df_clean['release_date'] = pd.to_datetime(df_clean['release_date'], errors='coerce')

    # Feature engineering
    df_clean['release_year'] = df_clean['release_date'].dt.year
    df_clean['release_year_centered'] = df_clean['release_year'] - df_clean['release_year'].mean()

    # Select important features 
    df_selected = df_clean[['budget', 'actor_score', 'star_score', 'trailer_views', 'trailer_likes', 'release_year', 'release_year_centered']]

    df_selected['trailer_likes_log'] = np.log1p(df_selected['trailer_likes'])
    df_selected['trailer_views_log'] = np.log1p(df_selected['trailer_views'])
    df_selected['budget_log'] = np.log1p(df_selected['budget'])
    df_selected['actor_score_log'] = np.log1p(df_selected['actor_score'])
    df_selected['budget_actor_interaction'] = df_selected['budget_log'] * df_selected['actor_score_log']
    df_selected = df_selected[['trailer_views_log', 'trailer_likes_log', 'budget_log', 'budget_actor_interaction',
              'release_year_centered']]
    
    # PCA for trailer views and likes
    pca = PCA(n_components=1)
    trailer_matrix = df_selected[['trailer_views_log', 'trailer_likes_log']].values
    pca_features = pca.fit_transform(trailer_matrix)
    df_selected['trailer_pca'] = pca_features

    df_selected.drop(columns=['trailer_views_log', 'trailer_likes_log'], inplace=True)

    if needs_poly:
        poly = load(MODEL_DIR / "poly_features.joblib")
        poly_features = poly.transform(df_selected)
        df_selected = pd.DataFrame(poly_features, columns=poly.get_feature_names_out(['trailer_pca', 'budget_log', 'budget_actor_interaction', 'release_year_centered']))
    
    # Predict revenues
    pred = pred_model(df_selected)
    print(pred)

if __name__ == "__main__":
    predict_revenue("MLR")