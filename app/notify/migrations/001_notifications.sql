-- Sweep · Feature 0 · notification center
-- The app creates these tables by itself on first use (notify/notify.php → Notify::schema()).
-- This file is the same thing, for reference or to run by hand in phpLiteAdmin / sqlite3. SQLite syntax.

-- ===== UP =====
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  type TEXT NOT NULL,
  category TEXT NOT NULL,              -- product_updates | achievements | prop_alerts | streaks | system
  title_key TEXT NOT NULL,
  body_key TEXT NULL,
  params TEXT NULL,                    -- JSON, i18n placeholders
  icon TEXT NULL,
  action_url TEXT NULL,                -- in-app link, e.g. #payouts
  priority TEXT NOT NULL DEFAULT 'normal',   -- normal | celebration
  dedupe_key TEXT NULL,
  read_at INTEGER NULL,                -- UTC epoch seconds
  shown_as_modal_at INTEGER NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NULL
);
CREATE INDEX IF NOT EXISTS notif_unread ON notifications (user_id, read_at, created_at);
CREATE INDEX IF NOT EXISTS notif_list ON notifications (user_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS notif_dedupe ON notifications (user_id, dedupe_key);

CREATE TABLE IF NOT EXISTS notification_prefs (
  user_id TEXT NOT NULL,
  category TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (user_id, category)
);

-- ===== DOWN (rollback) =====
-- Only these two new tables are touched. No existing table is altered by Feature 0.
-- DROP INDEX IF EXISTS notif_unread;
-- DROP INDEX IF EXISTS notif_list;
-- DROP INDEX IF EXISTS notif_dedupe;
-- DROP TABLE IF EXISTS notifications;
-- DROP TABLE IF EXISTS notification_prefs;
