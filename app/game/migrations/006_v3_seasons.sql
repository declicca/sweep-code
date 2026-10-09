-- Sweep · Gamification V3 · seasons and pass · SQLite. Created automatically (game/v3s.php → GameSeason::schema()).
CREATE TABLE IF NOT EXISTS user_season (user_id TEXT NOT NULL, season CHAR(7) NOT NULL, claimed_free TEXT NULL, claimed_premium TEXT NULL, PRIMARY KEY (user_id, season));
-- Season points come from xp_events (rewards excluded). DOWN: DROP TABLE IF EXISTS user_season;
