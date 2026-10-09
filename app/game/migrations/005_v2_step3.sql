-- Sweep · Gamification V2 · step 3 (monthly Wrapped) · SQLite. Created automatically (game/v2c.php → GameWrapped::schema()).
CREATE TABLE IF NOT EXISTS monthly_wrapped (user_id TEXT NOT NULL, month CHAR(7) NOT NULL, data_json TEXT NOT NULL, created_at INT NOT NULL, viewed_at INT NULL, PRIMARY KEY (user_id, month));
-- Reminders use the existing notifications table (notify/). DOWN: DROP TABLE IF EXISTS monthly_wrapped;
