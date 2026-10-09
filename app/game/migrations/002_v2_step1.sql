-- Sweep · Gamification V2 · step 1 (journey map + weekly missions) · SQLite
-- Created automatically on first use (game/v2.php → GameV2::schema()). Reference / manual run only. No existing table is altered.
CREATE TABLE IF NOT EXISTS user_map_nodes (user_id TEXT NOT NULL, node_id VARCHAR(40) NOT NULL, progress INT NOT NULL DEFAULT 0, target INT NOT NULL, completed_at INT NULL, PRIMARY KEY (user_id, node_id));
CREATE TABLE IF NOT EXISTS user_missions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, week_start VARCHAR(10) NOT NULL, mission_id VARCHAR(40) NOT NULL, difficulty INT NOT NULL, progress INT NOT NULL DEFAULT 0, target INT NOT NULL, completed_at INT NULL, rerolled INT NOT NULL DEFAULT 0);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mission ON user_missions (user_id, week_start, mission_id);
CREATE TABLE IF NOT EXISTS user_rewards (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, source VARCHAR(30) NOT NULL, reward_type VARCHAR(30) NOT NULL, reward_value VARCHAR(80) NOT NULL, created_at INT NOT NULL, used_at INT NULL);
-- DOWN: DROP TABLE IF EXISTS user_map_nodes; DROP TABLE IF EXISTS user_missions; DROP TABLE IF EXISTS user_rewards;
