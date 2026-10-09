-- Sweep · Gamification V3 · crews and buddy · SQLite. Created automatically (game/v3c.php → GameCrew::schema()).
CREATE TABLE IF NOT EXISTS crews (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(40) NOT NULL, invite_code VARCHAR(12) NOT NULL, owner_id TEXT NOT NULL, goal_factor INT NOT NULL DEFAULT 3, streak_weeks INT NOT NULL DEFAULT 0, last_goal_week VARCHAR(10) NULL, created_at INT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS uq_code ON crews (invite_code);
CREATE TABLE IF NOT EXISTS crew_members (crew_id BIGINT NOT NULL, user_id TEXT NOT NULL, joined_at INT NOT NULL, PRIMARY KEY (crew_id, user_id));
CREATE UNIQUE INDEX IF NOT EXISTS uq_member ON crew_members (user_id);
CREATE TABLE IF NOT EXISTS crew_events (id INTEGER PRIMARY KEY AUTOINCREMENT, crew_id BIGINT NOT NULL, user_id TEXT NOT NULL, type VARCHAR(30) NOT NULL, payload_json TEXT NULL, created_at INT NOT NULL);
CREATE TABLE IF NOT EXISTS crew_reactions (event_id BIGINT NOT NULL, user_id TEXT NOT NULL, emoji VARCHAR(8) NOT NULL, PRIMARY KEY (event_id, user_id));
CREATE TABLE IF NOT EXISTS buddies (user_a TEXT NOT NULL, user_b TEXT NOT NULL, status VARCHAR(10) NOT NULL, created_at INT NOT NULL, PRIMARY KEY (user_a, user_b));
CREATE TABLE IF NOT EXISTS buddy_cheers (from_id TEXT NOT NULL, to_id TEXT NOT NULL, day VARCHAR(10) NOT NULL, PRIMARY KEY (from_id, day));
-- DOWN: DROP TABLE crews, crew_members, crew_events, crew_reactions, buddies, buddy_cheers (one by one in SQLite).
