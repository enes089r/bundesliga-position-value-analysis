import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

engine = create_engine("mysql+pymysql://root:YOUR_PASSWORD@localhost/bundesliganeu")
df_raw = pd.read_sql("SELECT * FROM regression_dataset", engine)
value_cols = ['goalkeeper_val','centre_back_val','full_back_val',
              'def_mid_val','central_mid_val','winger_val','forward_val']
df = df_raw.dropna()
df[value_cols] = df[value_cols] / 1_000_000
formula_regions = ' + '.join(value_cols)

# Non-FE model (reference, between-club)
model = smf.ols(f'points ~ {formula_regions} + C(season)', data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})

# Club-FE model, correct cluster SE
model_clubfe = smf.ols(
    f'points ~ {formula_regions} + C(season) + C(club_id)', data=df
).fit(cov_type='cluster', cov_kwds={'groups': df['club_id']})

ci_fe = model_clubfe.conf_int()
print("FE model - coefficient + CI:")
print(pd.DataFrame({
    'coef': model_clubfe.params[value_cols],
    'se': model_clubfe.bse[value_cols],
    'ci_low': ci_fe.loc[value_cols, 0],
    'ci_high': ci_fe.loc[value_cols, 1],
    'p': model_clubfe.pvalues[value_cols]
}))

# Compute within-R^2 correctly (nested model comparison)

model_restricted = smf.ols('points ~ C(season) + C(club_id)', data=df).fit()
model_full_ols = smf.ols(f'points ~ {formula_regions} + C(season) + C(club_id)', data=df).fit()

within_r2 = 1 - model_full_ols.ssr / model_restricted.ssr
print("\nCorrect within-R^2:", within_r2)

f_result = model_full_ols.compare_f_test(model_restricted)
print("Classical F-test (OLS, no clustering):", f_result)

hyp = ' , '.join([f'{c} = 0' for c in value_cols])
print("\nCluster-robust Wald (same model, for comparison):")
print(model_clubfe.wald_test(hyp, scalar=True))

for c in value_cols:
    df[f'{c}_clubmean'] = df.groupby('club_id')[c].transform('mean')
    df[f'{c}_dev'] = df[c] - df[f'{c}_clubmean']

formula_mundlak = ('points ~ ' +
    ' + '.join([f'{c}_dev' for c in value_cols]) + ' + ' +
    ' + '.join([f'{c}_clubmean' for c in value_cols]) + ' + C(season)')

model_mundlak = smf.ols(formula_mundlak, data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})
print(model_mundlak.summary())

# Attack (Forward+Winger) vs Defense (CB+FB) joint contrast
hyp_contrast = 'forward_val + winger_val = centre_back_val + full_back_val'
print(model_clubfe.wald_test(hyp_contrast, scalar=True))