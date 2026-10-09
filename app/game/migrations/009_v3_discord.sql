-- Sweep · Gamification V3 · Discord rank roles + annual Wrapped · SQLite. Applied automatically (game/v3d.php → GameDiscord::schema()).
ALTER TABLE social_profile ADD COLUMN discord_user_id VARCHAR(30) NULL;
ALTER TABLE social_profile ADD COLUMN discord_name VARCHAR(60) NULL;
ALTER TABLE social_profile ADD COLUMN discord_share INT NOT NULL DEFAULT 0;
ALTER TABLE social_profile ADD COLUMN discord_rank_synced VARCHAR(20) NULL;
ALTER TABLE social_profile ADD COLUMN discord_synced_at INT NULL;
CREATE TABLE IF NOT EXISTS discord_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, created_at INT NOT NULL, sent_at INT NULL);
-- The annual Wrapped reuses monthly_wrapped (month = "YYYY-AN").
