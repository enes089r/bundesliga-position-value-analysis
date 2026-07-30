"""
Bundesliga Position-Value Analysis
-----------------------------------
Loads regression_dataset from MySQL and runs every specification
described in README.md. Edit the connection string below.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

# --- Connect and load ---
engine = create_engine("mysql+pymysql://root:YOUR_PASSWORD@localhost/bundesliganeu")
df_raw = pd.read_sql("SELECT * FROM regression_dataset", engine)

value_cols = ['goalkeeper_val', 'centre_back_val', 'full_back_val',
              'def_mid_val', 'central_mid_val', 'winger_val', 'forward_val']

print(f"Raw row count: {len(df_raw)}")
df = df_raw.dropna()
print(f"After dropna: {len(df)}  (dropped: {len(df_raw) - len(df)})")

df[value_cols] = df[value_cols] / 1_000_000
formula_regions = ' + '.join(value_cols)

# 1) Linear values (non-FE, between-club reference)
model = smf.ols(f'points ~ {formula_regions} + C(season)', data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})
print("\n=== 1) Linear values (non-FE) ===")
print(model.summary())

# 2) VIF check
X = df[value_cols]
vif = pd.DataFrame()
vif['feature'] = X.columns
vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print("\n=== 2) VIF (linear model) ===")
print(vif)

# 3) Log-transformed values
log_cols = [f'log_{c}' for c in value_cols]
for c, lc in zip(value_cols, log_cols):
    df[lc] = np.log(df[c])
formula_log = 'points ~ ' + ' + '.join(log_cols) + ' + C(season)'
model_log = smf.ols(formula_log, data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})
print("\n=== 3) Log-transformed values ===")
print(model_log.summary())

# 4) Total value + regional shares
df['total_value'] = df[value_cols].sum(axis=1)
df['log_total_value'] = np.log(df['total_value'])
share_cols = []
for c in value_cols:
    sc = f'share_{c}'
    df[sc] = df[c] / df['total_value']
    share_cols.append(sc)
share_cols_model = [c for c in share_cols if c != 'share_goalkeeper_val']  # goalkeeper = reference

formula_shares = "points ~ log_total_value + " + " + ".join(share_cols_model) + " + C(season)"
model_shares = smf.ols(formula_shares, data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})
print("\n=== 4) Total value + regional shares ===")
print(model_shares.summary())

hyp_shares = ', '.join([f'{c} = 0' for c in share_cols_model])
print("\nJoint Wald test: are all shares zero?")
print(model_shares.wald_test(hyp_shares, scalar=True))

# Baseline: total value only, for comparison
model_total = smf.ols('points ~ log_total_value + C(season)', data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})
print(f"\nR2 - total value only:  {model_total.rsquared:.4f}")
print(f"R2 - 7 regions (linear): {model.rsquared:.4f}")

# 5) Club fixed effects — the decisive within-club test
# Cluster SE (not HC1): club FE absorbs time-invariant error, not serial correlation
model_clubfe = smf.ols(
    f'points ~ {formula_regions} + C(season) + C(club_id)', data=df
).fit(cov_type='cluster', cov_kwds={'groups': df['club_id']})

ci_fe = model_clubfe.conf_int()
coef_table_fe = pd.DataFrame({
    'coef': model_clubfe.params[value_cols],
    'se': model_clubfe.bse[value_cols],
    'ci_low': ci_fe.loc[value_cols, 0],
    'ci_high': ci_fe.loc[value_cols, 1],
    'p': model_clubfe.pvalues[value_cols]
})
print("\n=== 5) Club fixed effects — coefficients + 95% CI ===")
print(coef_table_fe)

# 6) Classical F-test (cross-check against the cluster-robust Wald test below)
model_restricted = smf.ols('points ~ C(season) + C(club_id)', data=df).fit()
model_full_ols = smf.ols(f'points ~ {formula_regions} + C(season) + C(club_id)', data=df).fit()
within_r2 = 1 - model_full_ols.ssr / model_restricted.ssr
print(f"\n=== 6) Classical F-test (cross-check) ===")
print(f"Within-R2: {within_r2:.4f}")
print("F-test:", model_full_ols.compare_f_test(model_restricted))

# 7) Cluster-robust joint Wald test, same model
hyp_regions = ' , '.join([f'{c} = 0' for c in value_cols])
print("\n=== 7) Cluster-robust joint Wald (club-FE model) ===")
print(model_clubfe.wald_test(hyp_regions, scalar=True))

# 8) Attack vs. Defense contrast
print("\n=== 8) Attack vs. Defense contrast ===")
print(model_clubfe.wald_test(
    'forward_val + winger_val = centre_back_val + full_back_val', scalar=True))

# 9) Mundlak decomposition (within terms should match club-FE coefficients)
for c in value_cols:
    df[f'{c}_clubmean'] = df.groupby('club_id')[c].transform('mean')
    df[f'{c}_dev'] = df[c] - df[f'{c}_clubmean']

formula_mundlak = ('points ~ ' +
    ' + '.join([f'{c}_dev' for c in value_cols]) + ' + ' +
    ' + '.join([f'{c}_clubmean' for c in value_cols]) + ' + C(season)')
model_mundlak = smf.ols(formula_mundlak, data=df).fit(
    cov_type='cluster', cov_kwds={'groups': df['club_id']})
print("\n=== 9) Mundlak / correlated random effects ===")
print(model_mundlak.summary())

# 10) Per-region within/between variance share (season-adjusted)
print("\n=== 10) Within/between variance share, by region ===")
print(f"{'Region':<20}{'within/(within+between)':>25}")
for c in value_cols:
    resid = smf.ols(f'{c} ~ C(season)', data=df).fit().resid
    df[f'{c}_resid'] = resid
    w = df.groupby('club_id')[f'{c}_resid'].var(ddof=0).mean()
    b = df.groupby('club_id')[f'{c}_resid'].mean().var(ddof=0)
    print(f"{c:<20}{w / (w + b):>25.4f}")

# 11) Effect size in points (range x coefficient, non-FE model)
print("\n=== 11) Effect size (range x coefficient, in points) ===")
for col in value_cols:
    rng = df[col].max() - df[col].min()
    print(f"{col}: {rng * model.params[col]:.1f} points")

# 12) Staleness-filtered robustness check + Cook's distance
staleness = pd.read_sql("""
    SELECT g.season, cg.club_id, AVG(psv.staleness_days) AS avg_staleness
    FROM appearances app
    JOIN games g ON app.game_id = g.game_id
    JOIN club_games cg ON app.game_id = cg.game_id AND app.player_club_id = cg.club_id
    JOIN player_season_value psv ON app.player_id = psv.player_id AND g.season = psv.season
    WHERE g.competition_id = 'L1'
    GROUP BY g.season, cg.club_id
""", engine)

df_stale = df.merge(staleness, on=['season', 'club_id'], how='left')
df_clean = df_stale[df_stale['avg_staleness'] <= 730].copy()
print(f"\n=== 12) Staleness-filtered robustness check ===")
print(f"Excluded (staleness>730): {len(df_stale) - len(df_clean)} rows")

model_robust = smf.ols(f'points ~ {formula_regions} + C(season)', data=df_clean).fit(
    cov_type='cluster', cov_kwds={'groups': df_clean['club_id']})
print(model_robust.summary())

influence = model_robust.get_influence()
df_clean['cooks_d'] = influence.cooks_distance[0]
threshold = 4 / len(df_clean)
print(f"\nCook's distance threshold (4/n): {threshold:.4f}")
print(df_clean.sort_values('cooks_d', ascending=False).head(10)[['club_id', 'season', 'points', 'cooks_d']])
print(f"Exceeding threshold: {(df_clean['cooks_d'] > threshold).sum()}")

# 13) Exclude club_id 27 (most influential club)
df_no27 = df[df['club_id'] != 27]
model_no27 = smf.ols(f'points ~ {formula_regions} + C(season)', data=df_no27).fit(
    cov_type='cluster', cov_kwds={'groups': df_no27['club_id']})
print("\n=== 13) Excluding club_id 27 ===")
print(model_no27.summary())

# 14) Coefficient comparison plot
ci_nonfe = model.conf_int()
fig, ax = plt.subplots(figsize=(8, 6))
yp = np.arange(len(value_cols))
ax.errorbar(model.params[value_cols], yp - 0.15,
            xerr=[model.params[value_cols] - ci_nonfe.loc[value_cols, 0],
                  ci_nonfe.loc[value_cols, 1] - model.params[value_cols]],
            fmt='o', label='Non-FE (between-club)', color='tab:blue')
ax.errorbar(model_clubfe.params[value_cols], yp + 0.15,
            xerr=[model_clubfe.params[value_cols] - ci_fe.loc[value_cols, 0],
                  ci_fe.loc[value_cols, 1] - model_clubfe.params[value_cols]],
            fmt='o', label='Club FE (within-club)', color='tab:red')
ax.axvline(0, color='gray', linestyle='--')
ax.set_yticks(yp)
ax.set_yticklabels(value_cols)
ax.set_xlabel('Coefficient (points per million EUR)')
ax.legend()
plt.tight_layout()
plt.savefig('coef_comparison.png', dpi=150)
print("\nPlot saved: coef_comparison.png")