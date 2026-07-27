import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

df = pd.read_csv('regression_dataset.csv')
df = df.dropna()

value_cols = ['goalkeeper_val','centre_back_val','full_back_val',
              'def_mid_val','central_mid_val','winger_val','forward_val']
df[value_cols] = df[value_cols] / 1_000_000

model = smf.ols(
    'points ~ goalkeeper_val + centre_back_val + full_back_val + '
    'def_mid_val + central_mid_val + winger_val + forward_val + C(season)',
    data=df
).fit()

print(model.summary())

X = df[['goalkeeper_val','centre_back_val','full_back_val',
        'def_mid_val','central_mid_val','winger_val','forward_val']]
vif = pd.DataFrame()
vif['feature'] = X.columns
vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif)