import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

# 1. Load Data
df = pd.read_csv('data/movie_data_encoded.csv')

# 2. Extract the relevant columns (rename as needed)
x = df['averageRating']
y = df['revenue']

# 3. Drop any rows with NaN (optional but recommended)
mask = ~x.isna() & ~y.isna()
x = x[mask]
y = y[mask]

# 4. Fit a linear regression with StatsModels
#    Add a constant to include an intercept in the model
X = sm.add_constant(x)  # shape: (n,2)
model = sm.OLS(y, X).fit()

# 5. Prepare a grid of x-values for smooth plotting
x_pred = np.linspace(x.min(), x.max(), 100)
X_pred = sm.add_constant(x_pred)

# 6. Get predictions (including confidence & prediction intervals)
predictions = model.get_prediction(X_pred)
pred_summary = predictions.summary_frame(alpha=0.05)
# pred_summary has columns:
# ['mean', 'mean_se', 'mean_ci_lower', 'mean_ci_upper',
#  'obs_ci_lower', 'obs_ci_upper']

y_pred      = pred_summary['mean']             # regression line
conf_lower  = pred_summary['mean_ci_lower']    # 95% CI (lower)
conf_upper  = pred_summary['mean_ci_upper']    # 95% CI (upper)
pred_lower  = pred_summary['obs_ci_lower']     # 95% prediction interval (lower)
pred_upper  = pred_summary['obs_ci_upper']     # 95% prediction interval (upper)

# 7. Plotting
plt.figure(figsize=(10, 6))

# 7a. Scatter plot of data
plt.scatter(x, y, alpha=0.1, color='purple', label='Data')

# 7b. Regression line (green)
plt.plot(x_pred, y_pred, color='green', linewidth=2, label='Regression line')

# 7c. 95% confidence band (red dashed)
plt.plot(x_pred, conf_lower, 'r--', label='95% conf. band')
plt.plot(x_pred, conf_upper, 'r--')

# 7d. 95% prediction band (red dotted)
plt.plot(x_pred, pred_lower, 'r:', label='95% pred. band')
plt.plot(x_pred, pred_upper, 'r:')

# 8. Customize labels, title, legend
slope = model.params[1]
intercept = model.params[0]
plt.xlabel('IMDb rating (Normalized)')
plt.ylabel('Revenue (Normalized)')
plt.title(f'Figure 9: IMDb rating vs Revenue\nslope={slope:.2f}, intercept={intercept:.2f}')
plt.legend()
plt.grid(True)

plt.show()


