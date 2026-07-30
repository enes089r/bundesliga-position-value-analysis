USE bundesliganeu;

-- ============================================================
-- Bundesliga pipeline — single, idempotent script
-- Every intermediate step is a TABLE (source data is a static
-- snapshot, so views bought nothing but repeated computation).
-- ============================================================

DROP VIEW  IF EXISTS player_position_value;
DROP VIEW  IF EXISTS club_season_region_value;
DROP VIEW  IF EXISTS player_season_value;
DROP VIEW  IF EXISTS club_season_points;

DROP TABLE IF EXISTS regression_dataset;
DROP TABLE IF EXISTS csrv_table;
DROP TABLE IF EXISTS club_season_region_value;
DROP TABLE IF EXISTS player_season_value;
DROP TABLE IF EXISTS season_calendar;
DROP TABLE IF EXISTS club_season_points;

-- Rename guard: drop the index if it already exists from a prior run
SET @idx_exists = (
  SELECT COUNT(1) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'player_valuations' AND index_name = 'idx_pv_player_date'
);
SET @sql = IF(@idx_exists > 0, 'DROP INDEX idx_pv_player_date ON player_valuations', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Y(club-season points)
CREATE TABLE club_season_points AS
SELECT cg.club_id,
       g.season,
       SUM(CASE WHEN cg.own_goals > cg.opponent_goals THEN 3
                WHEN cg.own_goals = cg.opponent_goals THEN 1
                ELSE 0 END) AS points
FROM club_games cg
INNER JOIN games g ON cg.game_id = g.game_id
WHERE g.competition_id = 'L1'
GROUP BY cg.club_id, g.season;

-- Season calendar (start date per season, for the as-of join)
CREATE TABLE season_calendar AS
SELECT DISTINCT season,
       MAKEDATE(season, 1) + INTERVAL 6 MONTH AS season_start
FROM club_season_points;

-- Player-season value: last valuation before the season start (as-of, not an average)

CREATE TABLE player_season_value AS
SELECT pv.player_id, sc.season,
       pv.market_value_in_eur AS asof_value,
       pv.date AS val_date,
       DATEDIFF(sc.season_start, pv.date) AS staleness_days
FROM season_calendar sc
JOIN player_valuations pv
  ON pv.date = (
       SELECT MAX(pv2.date)
       FROM player_valuations pv2
       WHERE pv2.player_id = pv.player_id
         AND pv2.date < sc.season_start
     );

-- Club-season-region value, minute-weighted
-- NOTE: index on appearances join columns previously caused a bad
-- query plan (20+ minute runs), do not add one without re-measuring.
CREATE TABLE club_season_region_value AS
SELECT player_club_id AS club_id, season, region,
       SUM(minutes_played * asof_value) / SUM(minutes_played) AS weighted_avg_value
FROM (
    SELECT app.player_club_id, g.season, app.minutes_played, psv.asof_value,
           CASE
             WHEN p.sub_position = 'Goalkeeper'         THEN 'Goalkeeper'
             WHEN p.sub_position = 'Centre-Back'        THEN 'Centre-Back'
             WHEN p.sub_position IN ('Left-Back','Right-Back') THEN 'Full-Back'
             WHEN p.sub_position = 'Defensive Midfield' THEN 'Defensive Midfield'
             WHEN p.sub_position IN ('Central Midfield','Attacking Midfield',
                                     'Left Midfield','Right Midfield') THEN 'Central Midfield'
             WHEN p.sub_position IN ('Left Winger','Right Winger')     THEN 'Winger'
             WHEN p.sub_position IN ('Centre-Forward','Second Striker') THEN 'Forward'
           END AS region
    FROM appearances app
    INNER JOIN games   g ON app.game_id   = g.game_id
    INNER JOIN players p ON app.player_id = p.player_id
    INNER JOIN player_season_value psv
           ON app.player_id = psv.player_id AND g.season = psv.season
    WHERE g.competition_id = 'L1'
) AS match_player_data
WHERE region IS NOT NULL
GROUP BY player_club_id, season, region;

-- Wide-format regression dataset
CREATE TABLE regression_dataset AS
SELECT rv.club_id, rv.season,
       MAX(CASE WHEN rv.region='Goalkeeper'         THEN rv.weighted_avg_value END) AS goalkeeper_val,
       MAX(CASE WHEN rv.region='Centre-Back'        THEN rv.weighted_avg_value END) AS centre_back_val,
       MAX(CASE WHEN rv.region='Full-Back'          THEN rv.weighted_avg_value END) AS full_back_val,
       MAX(CASE WHEN rv.region='Defensive Midfield' THEN rv.weighted_avg_value END) AS def_mid_val,
       MAX(CASE WHEN rv.region='Central Midfield'   THEN rv.weighted_avg_value END) AS central_mid_val,
       MAX(CASE WHEN rv.region='Winger'             THEN rv.weighted_avg_value END) AS winger_val,
       MAX(CASE WHEN rv.region='Forward'            THEN rv.weighted_avg_value END) AS forward_val,
       csp.points
FROM club_season_region_value rv
INNER JOIN club_season_points csp
       ON rv.club_id = csp.club_id AND rv.season = csp.season
GROUP BY rv.club_id, rv.season, csp.points;

SELECT COUNT(*) FROM regression_dataset;