import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sqlalchemy import create_engine

# --- Load data from MySQL ---
engine = create_engine("mysql+pymysql://root:YOUR_PASSWORD@localhost/bundesliganeu")
df_raw = pd.read_sql("SELECT * FROM regression_dataset", engine)

value_cols = ['goalkeeper_val','centre_back_val','full_back_val',
              'def_mid_val','central_mid_val','winger_val','forward_val']

print(f"Raw row count: {len(df_raw)}")
df = df_raw.dropna()
print(f"After dropna: {len(df)}  (dropped: {len(df_raw) - len(df)})")

df[value_cols] = df[value_cols] / 1_000_000

# --- Total value and shares (from RAW values) ---
df['total_value'] = df[value_cols].sum(axis=1)
df['log_total_value'] = np.log(df['total_value'])

share_cols = []
for c in value_cols:
    share_name = f'share_{c}'
    df[share_name] = df[c] / df['total_value']
    share_cols.append(share_name)

share_cols_model = [c for c in share_cols if c != 'share_goalkeeper_val']

formula_shares = "points ~ log_total_value + " + " + ".join(share_cols_model) + " + C(season)"

model_shares = smf.ols(formula_shares, data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']}
)
print(model_shares.summary())

X_shares = df[['log_total_value'] + share_cols_model]
vif_shares = pd.DataFrame()
vif_shares['feature'] = X_shares.columns
vif_shares['VIF'] = [variance_inflation_factor(X_shares.values, i) for i in range(X_shares.shape[1])]
print(vif_shares)