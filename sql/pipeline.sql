USE bundesliganeu;
-- Pipeline integrity
SELECT COUNT(*) AS total_rows,
       SUM(goalkeeper_val  IS NULL) AS gk,
       SUM(centre_back_val IS NULL) AS cb,
       SUM(full_back_val   IS NULL) AS fb,
       SUM(def_mid_val     IS NULL) AS dm,
       SUM(central_mid_val IS NULL) AS cm,
       SUM(winger_val      IS NULL) AS wg,
       SUM(forward_val     IS NULL) AS fw
FROM regression_dataset;

SELECT season, COUNT(*) AS clubs FROM regression_dataset GROUP BY season ORDER BY season;

SELECT COUNT(*) AS unmatched
FROM club_season_region_value rv
LEFT JOIN club_season_points csp
       ON rv.club_id = csp.club_id AND rv.season = csp.season
WHERE csp.club_id IS NULL;

SELECT COUNT(*) AS total, SUM(date IS NULL) AS null_dates, MIN(date) AS earliest, MAX(date) AS latest
FROM player_valuations;

-- Rows pandas dropna() would remove
SELECT COUNT(*) AS rows_with_any_null
FROM regression_dataset
WHERE goalkeeper_val IS NULL OR centre_back_val IS NULL OR full_back_val IS NULL
   OR def_mid_val    IS NULL OR central_mid_val IS NULL OR winger_val IS NULL
   OR forward_val    IS NULL;

-- Duplicate (player_id, season) rows in the as-of value table — should be zero
SELECT player_id, season, COUNT(*) c
FROM player_season_value
GROUP BY player_id, season
HAVING c > 1
ORDER BY c DESC LIMIT 20;

-- Sub-position / missing-region diagnostics
SELECT sub_position, COUNT(*) AS n FROM players GROUP BY sub_position ORDER BY n DESC;

SELECT COUNT(*) AS unlabeled_but_played
FROM appearances app
INNER JOIN players p ON app.player_id = p.player_id
WHERE p.sub_position IS NULL AND app.minutes_played > 0;

-- Season breakdown of unlabeled-position minutes (STRAIGHT_JOIN avoids a
-- cartesian-explosion query plan seen with a plain INNER JOIN here)
SELECT g.season,
       COUNT(*) AS total_minute_rows,
       SUM(p.sub_position IS NULL AND app.minutes_played > 0) AS unlabeled,
       SUM(p.sub_position IS NULL AND app.minutes_played > 0) / COUNT(*) * 100 AS percentage
FROM appearances app
STRAIGHT_JOIN players p ON app.player_id = p.player_id
STRAIGHT_JOIN games g ON app.game_id = g.game_id
GROUP BY g.season ORDER BY g.season;

-- Panel structure
SELECT COUNT(DISTINCT club_id) FROM regression_dataset;

SELECT club_id, COUNT(*) AS n_seasons
FROM regression_dataset GROUP BY club_id ORDER BY n_seasons;

-- Dependent-variable validation
SELECT season, COUNT(*) AS n_matches
FROM games WHERE competition_id='L1' GROUP BY season ORDER BY season;

SELECT club_id, AVG(points) AS avg_points, COUNT(*) AS n_seasons
FROM regression_dataset GROUP BY club_id ORDER BY avg_points DESC LIMIT 5;

-- Valuation staleness (corrected: restricted to active players)
SELECT g.season,
       COUNT(DISTINCT psv.player_id) AS active_players,
       ROUND(AVG(psv.staleness_days)) AS avg_staleness_active
FROM player_season_value psv
JOIN appearances app ON app.player_id = psv.player_id
JOIN games g ON app.game_id = g.game_id AND g.season = psv.season
WHERE g.competition_id = 'L1'
GROUP BY g.season ORDER BY g.season;

-- Valuation-date month distribution (raw table — transfer-window batching check)
SELECT MONTH(date) AS month, COUNT(*) AS n
FROM player_valuations
GROUP BY month ORDER BY month;

-- Valuation record density by calendar year
SELECT YEAR(date) AS valuation_year, COUNT(*) AS n
FROM player_valuations
GROUP BY YEAR(date) ORDER BY valuation_year;