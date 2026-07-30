import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:YOUR_PASSWORD@localhost/bundesliganeu")

# --- Main data ---
df_raw = pd.read_sql("SELECT * FROM regression_dataset", engine)
value_cols = ['goalkeeper_val','centre_back_val','full_back_val',
              'def_mid_val','central_mid_val','winger_val','forward_val']

df = df_raw.dropna()
df[value_cols] = df[value_cols] / 1_000_000

# --- Staleness data ---
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

print(f"Excluded due to staleness>730: {len(df_stale) - len(df_clean)} rows")

model_robust = smf.ols(
    'points ~ goalkeeper_val + centre_back_val + full_back_val + '
    'def_mid_val + central_mid_val + winger_val + forward_val + C(season)',
    data=df_clean
).fit(cov_type='cluster', cov_kwds={'groups': df_clean['club_id']})

print(model_robust.summary())

# --- Influence diagnostics ---
influence = model_robust.get_influence()
cooks_d = influence.cooks_distance[0]

df_clean['cooks_d'] = cooks_d

threshold = 4 / len(df_clean)
print(f"\nThreshold (4/n): {threshold:.4f}")

influential = df_clean.sort_values('cooks_d', ascending=False).head(10)[['club_id','season','points','cooks_d']]
print(influential)

print(f"\nObservations exceeding threshold: {(df_clean['cooks_d'] > threshold).sum()}")

df_no27 = df[df['club_id'] != 27]

model_no27 = smf.ols(
    'points ~ goalkeeper_val + centre_back_val + full_back_val + '
    'def_mid_val + central_mid_val + winger_val + forward_val + C(season)',
    data=df_no27
).fit(cov_type='cluster', cov_kwds={'groups': df_no27['club_id']})

print(model_no27.summary())