-- Sweep · Gamification V3 · social profile + weekly leagues · SQLite. Created automatically (game/v3l.php → GameSocial::schema()).
CREATE TABLE IF NOT EXISTS social_profile (user_id TEXT NOT NULL PRIMARY KEY, handle VARCHAR(20) NULL, handle_lc VARCHAR(20) NULL, league_opt_in INT NOT NULL DEFAULT 0, league_tier INT NOT NULL DEFAULT 1, updated_at INT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS uq_handle ON social_profile (handle_lc);
CREATE TABLE IF NOT EXISTS league_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, week_start VARCHAR(10) NOT NULL, tier INT NOT NULL, finalized_at INT NULL, created_at INT NOT NULL);
CREATE TABLE IF NOT EXISTS league_members (group_id BIGINT NOT NULL, user_id TEXT NOT NULL, week_xp INT NOT NULL DEFAULT 0, final_rank INT NULL, outcome VARCHAR(10) NULL, PRIMARY KEY (group_id, user_id));
CREATE TABLE IF NOT EXISTS moderation_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, reporter_id TEXT NOT NULL, target_type VARCHAR(20) NOT NULL, target_id VARCHAR(120) NOT NULL, reason VARCHAR(200) NULL, created_at INT NOT NULL, resolved_at INT NULL);
-- DOWN: DROP TABLE IF EXISTS league_members; DROP TABLE IF EXISTS league_groups; DROP TABLE IF EXISTS social_profile; DROP TABLE IF EXISTS moderation_reports;
