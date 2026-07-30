import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:YOUR_PASSWORD@localhost/bundesliganeu")
df_raw = pd.read_sql("SELECT * FROM regression_dataset", engine)
value_cols = ['goalkeeper_val','centre_back_val','full_back_val',
              'def_mid_val','central_mid_val','winger_val','forward_val']
df = df_raw.dropna()
df[value_cols] = df[value_cols] / 1_000_000

print(f"{'Region':<20}{'within/(within+between)':>25}")
for c in value_cols:
    resid = smf.ols(f'{c} ~ C(season)', data=df).fit().resid
    df[f'{c}_resid'] = resid
    w = df.groupby('club_id')[f'{c}_resid'].var(ddof=0).mean()
    b = df.groupby('club_id')[f'{c}_resid'].mean().var(ddof=0)
    ratio = w / (w + b)
    print(f"{c:<20}{ratio:>25.4f}")