-- test queries
SELECT * FROM player_season_value WHERE player_id = 4257 ORDER BY season;

SELECT DISTINCT position FROM players;

SELECT * FROM club_season_region_value
WHERE club_id = 27 AND season = 2012
ORDER BY region;

-- club-season points

CREATE VIEW club_season_points AS
SELECT club_games.club_id, games.season,
       SUM(CASE
             WHEN own_goals > opponent_goals THEN 3
             WHEN own_goals = opponent_goals THEN 1
             ELSE 0
           END) AS points
FROM club_games
INNER JOIN games
ON club_games.game_id = games.game_id
WHERE competition_id = 'L1'
GROUP BY club_id, games.season;

-- player market value per season

CREATE VIEW player_season_value AS
SELECT player_id,
    CASE
        WHEN MONTH(date) >= 7 THEN YEAR(date)
        ELSE YEAR(date) - 1
    END AS season,
    AVG(market_value_in_eur) AS avg_value
FROM player_valuations
GROUP BY
    player_id,
    CASE
        WHEN MONTH(date) >= 7 THEN YEAR(date)
        ELSE YEAR(date) - 1
    END;


-- player values joined with position.

CREATE VIEW player_position_value AS
SELECT p.name, p.position,
       psv.avg_value, psv.season
FROM players p
INNER JOIN player_season_value psv
ON p.player_id = psv.player_id;

-- weighted regional value per club-season
CREATE VIEW club_season_region_value AS
SELECT
    player_club_id AS club_id,
    season,
    region,
    SUM(minutes_played * avg_value) / SUM(minutes_played) AS weighted_avg_value
FROM (
    SELECT
        app.player_club_id,
        g.season,
        app.minutes_played,
        psv.avg_value,
        CASE
            WHEN p.sub_position = 'Goalkeeper' THEN 'Goalkeeper'
            WHEN p.sub_position = 'Centre-Back' THEN 'Centre-Back'
            WHEN p.sub_position IN ('Left-Back', 'Right-Back') THEN 'Full-Back'
            WHEN p.sub_position = 'Defensive Midfield' THEN 'Defensive Midfield'
            WHEN p.sub_position IN ('Central Midfield', 'Attacking Midfield', 'Left Midfield', 'Right Midfield') THEN 'Central Midfield'
            WHEN p.sub_position IN ('Left Winger', 'Right Winger') THEN 'Winger'
            WHEN p.sub_position IN ('Centre-Forward', 'Second Striker') THEN 'Forward'
        END AS region
    FROM appearances app
    INNER JOIN games g ON app.game_id = g.game_id
    INNER JOIN players p ON app.player_id = p.player_id
    INNER JOIN player_season_value psv
        ON app.player_id = psv.player_id AND g.season = psv.season
    WHERE g.competition_id = 'L1'
) AS match_player_data
WHERE region IS NOT NULL
GROUP BY player_club_id, season, region;

-- final wide-format dataset for regression analysis

CREATE VIEW regression_dataset AS
SELECT
    rv.club_id,
    rv.season,
    MAX(CASE WHEN rv.region = 'Goalkeeper' THEN rv.weighted_avg_value END) AS goalkeeper_val,
    MAX(CASE WHEN rv.region = 'Centre-Back' THEN rv.weighted_avg_value END) AS centre_back_val,
    MAX(CASE WHEN rv.region = 'Full-Back' THEN rv.weighted_avg_value END) AS full_back_val,
    MAX(CASE WHEN rv.region = 'Defensive Midfield' THEN rv.weighted_avg_value END) AS def_mid_val,
    MAX(CASE WHEN rv.region = 'Central Midfield' THEN rv.weighted_avg_value END) AS central_mid_val,
    MAX(CASE WHEN rv.region = 'Winger' THEN rv.weighted_avg_value END) AS winger_val,
    MAX(CASE WHEN rv.region = 'Forward' THEN rv.weighted_avg_value END) AS forward_val,
    csp.points
FROM club_season_region_value rv
INNER JOIN club_season_points csp
    ON rv.club_id = csp.club_id AND rv.season = csp.season
GROUP BY rv.club_id, rv.season, csp.points;


-- null investigation:

SELECT season,
       COUNT(*) AS total,
       SUM(CASE WHEN goalkeeper_val IS NULL THEN 1 ELSE 0 END) AS gk_null,
       SUM(CASE WHEN forward_val IS NULL THEN 1 ELSE 0 END) AS fw_null
FROM regression_dataset
GROUP BY season
ORDER BY season;

SELECT club_id, season
FROM regression_dataset
WHERE season = 2013 AND goalkeeper_val IS NULL;

SELECT app.player_id, p.name, p.sub_position,
       app.minutes_played, psv.avg_value
FROM appearances app
INNER JOIN games g ON app.game_id = g.game_id
INNER JOIN players p ON app.player_id = p.player_id
LEFT JOIN player_season_value psv
    ON app.player_id = psv.player_id AND g.season = psv.season
WHERE app.player_club_id = 60
  AND g.season = 2013
  AND g.competition_id = 'L1'
  AND p.sub_position = 'Goalkeeper';