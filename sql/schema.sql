-- ============================================================
-- Schema DDL for the five Transfermarkt tables this pipeline uses.
-- Source: dcaribou/transfermarkt-datasets (Kaggle)
-- NOTE: column lists below cover what the pipeline actually reads.
-- The real CSVs have additional columns (player names, nationalities,
-- contract details, etc.) not listed here — load the full CSV headers
-- as-is; MySQL will happily hold extra columns the pipeline ignores.
-- Verify exact column names/types against your CSV headers before
-- loading, since the dataset has had minor schema revisions over time.
-- ============================================================

CREATE TABLE IF NOT EXISTS games (
    game_id           INT PRIMARY KEY,
    competition_id    VARCHAR(10),
    season            INT,
    date              DATE,
    home_club_id      INT,
    away_club_id      INT,
    home_club_goals   INT,
    away_club_goals   INT
);

CREATE TABLE IF NOT EXISTS club_games (
    game_id           INT,
    club_id           INT,
    own_goals         INT,
    opponent_goals    INT,
    own_position      INT,
    opponent_position INT,
    hosting           VARCHAR(10),
    PRIMARY KEY (game_id, club_id)
);

CREATE TABLE IF NOT EXISTS players (
    player_id         INT PRIMARY KEY,
    sub_position      VARCHAR(50),
    position          VARCHAR(50),
    name              VARCHAR(255),
    date_of_birth     DATE,
    country_of_birth  VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS player_valuations (
    player_id             INT,
    date                  DATE,
    market_value_in_eur   BIGINT,
    player_club_domestic_competition_id VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS appearances (
    appearance_id     VARCHAR(50) PRIMARY KEY,
    game_id           INT,
    player_id         INT,
    player_club_id    INT,
    date              DATE,
    minutes_played    INT,
    goals             INT,
    assists           INT
);

-- Indexes the pipeline relies on for performance
CREATE INDEX idx_pv_player_date ON player_valuations (player_id, date);