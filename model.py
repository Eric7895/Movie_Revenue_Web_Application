import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stats
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
from statsmodels.stats.anova import anova_lm
from scipy.stats import randint, uniform
import scipy.sparse
from pygam import LinearGAM, s, f

df = pd.read_csv("data/movie_data_encoded.csv")

def handle_outliers(df, columns, method='cap'):
    df_clean = df.copy()
    for col in columns:
        Q1 = df_clean[col].quantile(0.05)
        Q3 = df_clean[col].quantile(0.95)
        IQR = Q3 - Q1
        lower_bound = Q1 - 2 * IQR
        upper_bound = Q3 + 2 * IQR

        if method == 'cap':
            df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)
    return df_clean

df_clean = df[(df['trailer_views'] >= 0) & (df['trailer_likes'] >= 0)].copy() # Remove negative values
#df_clean = handle_outliers(df_clean, df_clean.select_dtypes(include=['int64', 'float64']).columns.tolist()) # Remove outlier

df_clean['release_year'] = pd.to_datetime(df_clean['release_date']).dt.year # Add temporal feature because there's an trend in residual versus observation order
df_clean['release_year_centered'] = df_clean['release_year'] - df_clean['release_year'].mean() 

df_sorted_asc = df_clean.sort_values(by='release_date')

important_feature_based_on_domain_expertise = ['budget', 'actor_score', 'star_score', 'trailer_views', 'trailer_likes', 'revenue', 'release_year', 'release_year_centered']
test = df_sorted_asc[important_feature_based_on_domain_expertise].copy()

test['revenue'] = np.log1p(test['revenue'])
test['trailer_likes_log'] = np.log1p(test['trailer_likes'])
test['trailer_views_log'] = np.log1p(test['trailer_views'])
test['budget_log'] = np.log1p(test['budget'])
test['actor_score_log'] = np.log1p(test['actor_score'])
test['budget_actor_interaction'] = test['budget_log'] * test['actor_score_log']

test = test[['trailer_views_log', 'trailer_likes_log', 'budget_log', 'budget_actor_interaction',
              'release_year_centered', 'revenue']]

X = test.drop('revenue', axis=1)
y = df_sorted_asc['revenue']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
y_train_log = np.log1p(y_train)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train, y_train_log)
y_pred_log = model.predict(X_test)
y_pred = np.expm1(y_pred_log)
rmse = np.sqrt(mean_squared_error(y_test, y_pred)) / 1e6
r2 = r2_score(y_test, y_pred)
print(f"MLR RMSE: {round(rmse, 2)} Millions")
print(f"MLR R-squared: {round(r2, 2)}")

EL_tune = ElasticNet(max_iter=20000, random_state=42)

search_space = {
    'alpha': np.logspace(-4, 2, 50),  # Regularization strength (L1 + L2)
    'l1_ratio': np.linspace(0, 1, 21),  # Balance between L1 (lasso) and L2 (ridge)
}

grid_search = GridSearchCV(
    estimator=EL_tune,
    param_grid=search_space,
    cv=KFold(n_splits=5),
    scoring='neg_mean_squared_error',
    n_jobs=-1  # Optional: speeds things up if you have multiple cores
)

grid_search.fit(X_train, y_train_log)

best_params = grid_search.best_params_
print("Best Parameters:", best_params)

best_model = grid_search.best_estimator_

y_pred_log = best_model.predict(X_test)
y_pred = np.expm1(y_pred_log)
rmse = np.sqrt(mean_squared_error(y_test, y_pred)) / 1e6
r2 = r2_score(y_test, y_pred)
print(f"ELN RMSE: {round(rmse, 2)} Millions")
print(f"ELN R-squared: {round(r2, 2)}")

np.int = int
scipy.sparse.csr_matrix.A = property(lambda self: self.toarray())

gam = LinearGAM(
    s(0) +  # trailer_views_log
    s(1) +  # trailer_likes_log
    s(2) +  # budget_log
    s(3) +  # budget_actor_interaction
    s(4)    # release_year_centered
).fit(X_train, y_train_log)

y_pred_log = gam.predict(X_test)
y_pred = np.expm1(y_pred_log)
rmse = np.sqrt(mean_squared_error(y_test, y_pred)) / 1e6
r2 = r2_score(y_test, y_pred)
print(f"GAM RMSE: {round(rmse, 2)} Millions")
print(f"GAM R-squared: {round(r2, 2)}")