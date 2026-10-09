-- Sweep · Gamification V2 · step 2 (weekly review, chest, cosmetics, Edge Reveal, comeback quest) · SQLite
-- Created automatically on first use (game/v2b.php → GameV2b::schema()). Reference / manual run only.
CREATE TABLE IF NOT EXISTS weekly_reviews (user_id TEXT NOT NULL, week_start VARCHAR(10) NOT NULL, data_json TEXT NOT NULL, completed_at INT NOT NULL, chest_opened_at INT NULL, PRIMARY KEY (user_id, week_start));
CREATE TABLE IF NOT EXISTS edge_reveals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, week_start VARCHAR(10) NOT NULL, slot INT NOT NULL DEFAULT 1, insight_key VARCHAR(40) NOT NULL, data_json TEXT NOT NULL, text_json TEXT NULL, ai_used INT NOT NULL DEFAULT 0, revealed_at INT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS uq_reveal ON edge_reveals (user_id, week_start, slot);
CREATE TABLE IF NOT EXISTS user_cosmetics (user_id TEXT NOT NULL, cosmetic_id VARCHAR(40) NOT NULL, equipped INT NOT NULL DEFAULT 0, PRIMARY KEY (user_id, cosmetic_id));
CREATE TABLE IF NOT EXISTS user_quests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, kind VARCHAR(20) NOT NULL, started_on VARCHAR(10) NOT NULL, ends_on VARCHAR(10) NOT NULL, lost_streak INT NOT NULL DEFAULT 0, completed_at INT NULL, created_at INT NOT NULL);
-- DOWN: DROP TABLE IF EXISTS weekly_reviews; DROP TABLE IF EXISTS edge_reveals; DROP TABLE IF EXISTS user_cosmetics; DROP TABLE IF EXISTS user_quests;
