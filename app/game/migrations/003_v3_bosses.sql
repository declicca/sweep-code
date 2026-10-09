-- Sweep · Gamification V3 · step 1 (bosses) · SQLite
-- Created automatically on first use (game/boss.php → GameBoss::schema()). Reference / manual run only. No existing table is altered.
CREATE TABLE IF NOT EXISTS user_bosses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, boss_id VARCHAR(30) NOT NULL, variant VARCHAR(20) NOT NULL DEFAULT 'normal',
  hp_max INT NOT NULL, hp INT NOT NULL, evidence_json TEXT NOT NULL, intro_text TEXT NULL, intro_lang VARCHAR(2) NULL, status VARCHAR(10) NOT NULL,
  started_at INT NOT NULL, defeated_at INT NULL, checked_at INT NULL);
CREATE TABLE IF NOT EXISTS boss_hits (boss_row_id BIGINT NOT NULL, trading_day VARCHAR(10) NOT NULL, delta INT NOT NULL, PRIMARY KEY (boss_row_id, trading_day));
-- DOWN: DROP TABLE IF EXISTS boss_hits; DROP TABLE IF EXISTS user_bosses;
