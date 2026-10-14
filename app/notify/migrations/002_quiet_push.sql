-- Sweep · brief 02 part 10 · at most 2 notifications a day, notifications on the phone (14 Oct. 2026)
-- The app does this by itself on first use: Notify::schema() (notify/notify.php) adds the column, wp_schema()
-- (push/web-push.php) creates the two tables. This file is the same thing, for reference or to run by hand. SQLite syntax
-- (MySQL: the same names, see the two functions).

-- ===== UP =====
-- a notification over the day's 2: in the list, already read, never a toast or a push
ALTER TABLE notifications ADD COLUMN quiet INTEGER NOT NULL DEFAULT 0;

-- each device that turned notifications on (the browser's push address and keys; never a key of Sweep)
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,              -- the push service's address (FCM, Apple, Mozilla, Windows only)
  endpoint_h TEXT NOT NULL,            -- sha1(endpoint)
  p256dh TEXT NOT NULL,                -- the browser's public key, base64url
  auth TEXT NOT NULL,                  -- the browser's secret, base64url
  lang TEXT NOT NULL DEFAULT 'en',     -- the device's language: en | fr | es
  created_at INTEGER NOT NULL,         -- UTC epoch seconds
  seen_at INTEGER NOT NULL,
  ok_at INTEGER NULL,
  fails INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS push_ep ON push_subscriptions (endpoint_h);
CREATE INDEX IF NOT EXISTS push_user ON push_subscriptions (user_id);

-- each reminder on the phone (plan, review, weekly): on / off and its time, New York
CREATE TABLE IF NOT EXISTS push_prefs (
  user_id TEXT NOT NULL PRIMARY KEY,
  prefs TEXT NOT NULL,                 -- JSON {"plan":{"on":true,"at":"08:45"},"review":{…},"weekly":{…}}
  updated_at INTEGER NOT NULL
);

-- ===== DOWN (rollback) =====
-- DROP TABLE IF EXISTS push_prefs;
-- DROP TABLE IF EXISTS push_subscriptions;
-- (the quiet column can stay: 0 everywhere means the old behaviour)
