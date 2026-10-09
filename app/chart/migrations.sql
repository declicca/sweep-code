-- Sweep · real charts · Phase 1 · created automatically on first use (chart/chart.php → ChartData::schema()).
-- SQLite (current database). MySQL equivalent: same columns with BIGINT AUTO_INCREMENT and DATETIME.
CREATE TABLE IF NOT EXISTS chart_fetch_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_root VARCHAR(10) NOT NULL,      -- NQ, ES…
  schema_name VARCHAR(12) NOT NULL,    -- ohlcv-1m / ohlcv-1s
  start_utc TEXT NOT NULL, end_utc TEXT NOT NULL,
  bytes INT NULL, cost_usd DECIMAL(10,4) NULL,
  status VARCHAR(20) NOT NULL,         -- ok | error | budget
  created_at TEXT NOT NULL
);
-- DOWN: DROP TABLE IF EXISTS chart_fetch_log;
-- No change to the trades: they are JSON documents. contract (optional expiry), stop, target and entry/exit times already exist.
