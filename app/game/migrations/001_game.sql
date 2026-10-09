-- Sweep · Gamification V1 « Sweep the day » · SQLite
-- The app creates these tables by itself on first use (game/game.php → GameEngine::schema()).
-- This file is the same thing, for reference or to run by hand. No existing table is altered:
-- plans and reviews live in the existing journal documents, journaling fields in the trade documents.

-- ===== UP =====
CREATE TABLE IF NOT EXISTS user_game_profile (
  user_id TEXT NOT NULL PRIMARY KEY, xp_total INT NOT NULL DEFAULT 0, level INT NOT NULL DEFAULT 1, rank_key VARCHAR(20) NOT NULL DEFAULT 'rookie',
  streak_current INT NOT NULL DEFAULT 0, streak_best INT NOT NULL DEFAULT 0, streak_start TEXT NULL, streak_last_day TEXT NULL,
  freezes_available INT NOT NULL DEFAULT 1, freezes_reset_on TEXT NULL, last_locked_day TEXT NULL, started_on TEXT NOT NULL,
  goal VARCHAR(30) NULL, trading_style VARCHAR(20) NULL, instruments VARCHAR(255) NULL, onboarding_json TEXT NULL,
  sound_enabled INT NOT NULL DEFAULT 0, default_max_loss INT NULL, updated_at INT NOT NULL);
CREATE TABLE IF NOT EXISTS game_days (
  user_id TEXT NOT NULL, trading_day TEXT NOT NULL, ring_plan INT NOT NULL DEFAULT 0, ring_execution INT NOT NULL DEFAULT 0, ring_review INT NOT NULL DEFAULT 0,
  trades_count INT NOT NULL DEFAULT 0, compliant_count INT NOT NULL DEFAULT 0, journaled_count INT NOT NULL DEFAULT 0, is_swept INT NOT NULL DEFAULT 0,
  is_valid_streak INT NOT NULL DEFAULT 0, review_done INT NOT NULL DEFAULT 0, day_off INT NOT NULL DEFAULT 0, plan_valid INT NOT NULL DEFAULT 0,
  plan_at INT NULL, plan_bias VARCHAR(12) NULL, guardrail INT NOT NULL DEFAULT 0, freeze_used INT NOT NULL DEFAULT 0, activity INT NOT NULL DEFAULT 0,
  net_c INT NOT NULL DEFAULT 0, detail_json TEXT NULL, locked_at INT NULL, updated_at INT NOT NULL, PRIMARY KEY (user_id, trading_day));
CREATE TABLE IF NOT EXISTS xp_events (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, event_key VARCHAR(120) NOT NULL, xp INT NOT NULL, meta_json TEXT NULL, created_at INT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS uq_xp ON xp_events (user_id, event_key);
CREATE TABLE IF NOT EXISTS user_badges (user_id TEXT NOT NULL, badge_id VARCHAR(40) NOT NULL, unlocked_at INT NOT NULL, PRIMARY KEY (user_id, badge_id));
CREATE TABLE IF NOT EXISTS game_celebrations (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, type VARCHAR(30) NOT NULL, payload_json TEXT NOT NULL, created_at INT NOT NULL, seen_at INT NULL);
CREATE INDEX IF NOT EXISTS idx_celeb_unseen ON game_celebrations (user_id, seen_at);
CREATE TABLE IF NOT EXISTS market_holidays (day TEXT NOT NULL PRIMARY KEY, label VARCHAR(80) NULL);
CREATE TABLE IF NOT EXISTS game_analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, event VARCHAR(40) NOT NULL, meta_json TEXT NULL, created_at INT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_game_an ON game_analytics (user_id, event);

-- U.S. market holidays, next 12 months (neutral days for the streak). Add next year's dates the same way.
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2026-11-26', 'Thanksgiving');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2026-12-25', 'Christmas');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-01-01', 'New Year''s Day');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-01-18', 'Martin Luther King Jr. Day');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-02-15', 'Presidents'' Day');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-03-26', 'Good Friday');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-05-31', 'Memorial Day');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-06-18', 'Juneteenth (observed)');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-07-05', 'Independence Day (observed)');
INSERT OR IGNORE INTO market_holidays (day, label) VALUES ('2027-09-06', 'Labor Day');

-- ===== DOWN (rollback) =====
-- DROP TABLE IF EXISTS user_game_profile; DROP TABLE IF EXISTS game_days; DROP TABLE IF EXISTS xp_events; DROP TABLE IF EXISTS user_badges;
-- DROP TABLE IF EXISTS game_celebrations; DROP TABLE IF EXISTS market_holidays; DROP TABLE IF EXISTS game_analytics;
