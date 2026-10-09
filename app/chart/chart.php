<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — real candle charts, Phase 1: Databento client, shared file cache and the /api/chart/bars endpoint.
 *
 * Databento historical API (checked against the official docs):
 *  - base URL https://hist.databento.com/v0, HTTP Basic auth with the API key as user name and an empty password;
 *  - timeseries.get_range (GET or POST, POST recommended): dataset, symbols, schema, start, end (end is exclusive), stype_in,
 *    encoding=json (one JSON record per line), pretty_px (prices as decimal strings instead of 1e-9 fixed point),
 *    pretty_ts (ISO strings instead of UNIX nanoseconds);
 *  - continuous symbology [ROOT].[c|n|v].[RANK]: "NQ.v.0" = the NQ contract with the most volume on the previous day;
 *    prices are original, unadjusted. The real contract comes from symbology.resolve (free):
 *    continuous → instrument_id, then instrument_id → raw_symbol;
 *  - metadata.get_cost (free) returns the USD cost of a request before running it;
 *  - an OHLCV bar only exists when there was a trade in that interval: gaps are kept, never filled.
 *
 * Licence guard: no bar younger than chart_data_min_age_hours (default 24) ever leaves this module, whatever the
 * parameters: the session must be fully older than the delay to be downloaded, and every response is filtered again.
 * The API key lives in the private folder outside the web root and never reaches the browser.
 */

const CHART_TFS = ['15s' => 15, '30s' => 30, '1m' => 60, '5m' => 300, '15m' => 900, '1h' => 3600];

/** typed root → [data root, tick size, decimals]. Micros trade at the same price as the full contract. */
const CHART_INSTRUMENTS = [
    'NQ' => ['NQ', 0.25, 2], 'MNQ' => ['NQ', 0.25, 2], 'ES' => ['ES', 0.25, 2], 'MES' => ['ES', 0.25, 2],
    'YM' => ['YM', 1.0, 0], 'MYM' => ['YM', 1.0, 0], 'RTY' => ['RTY', 0.10, 2], 'M2K' => ['RTY', 0.10, 2],
    'CL' => ['CL', 0.01, 2], 'MCL' => ['CL', 0.01, 2], 'GC' => ['GC', 0.10, 2], 'MGC' => ['GC', 0.10, 2],
    'SI' => ['SI', 0.005, 3], '6E' => ['6E', 0.00005, 5],
];
/** CME month codes, to recognise an exact expiry typed by the trader (NQZ6, NQZ26, MNQH7…) */
const CHART_MONTHS = 'FGHJKMNQUVXZ';

final class ChartData
{
    private static ?array $cfg = null;

    /* ───────────── configuration (private folder, outside the web root) ───────────── */

    public static function cfg(): array
    {
        if (self::$cfg !== null) return self::$cfg;
        $defaults = ['databento_api_key' => '', 'databento_dataset' => 'GLBX.MDP3', 'chart_data_min_age_hours' => 24, 'chart_cache_dir' => '',
                     'chart_daily_budget_usd' => 2.00, 'chart_enabled' => true, 'databento_base_url' => 'https://hist.databento.com/v0'];
        $c = [];
        foreach (array_filter([defined('SWEEP_CHART_CONFIG') ? (string) SWEEP_CHART_CONFIG : '', (string) getenv('SWEEP_CHART_CONFIG'),
                               dirname(__DIR__, 2) . '/sweep-private/chart-config.php', dirname(__DIR__, 3) . '/sweep-private/chart-config.php']) as $p) {
            if (@is_readable($p)) { $x = require $p; if (is_array($x)) { $c = $x; $c['_found'] = $p; break; } }
        }
        $c += $defaults;
        $key = trim((string) $c['databento_api_key']);
        $c['_has_key'] = $key !== '' && stripos($key, 'PASTE') === false && stripos($key, 'db-...') === false;
        $c['chart_data_min_age_hours'] = max(0, (int) $c['chart_data_min_age_hours']);
        if ($c['chart_cache_dir'] === '') $c['chart_cache_dir'] = (!empty($c['_found']) ? dirname((string) $c['_found']) : dirname(__DIR__, 2) . '/sweep-private') . '/bars';
        return self::$cfg = $c;
    }
    public static function enabled(): bool { $c = self::cfg(); return !empty($c['chart_enabled']) && $c['_has_key']; }
    public static function minAge(): int { return (int) self::cfg()['chart_data_min_age_hours'] * 3600; }
    /** the newest timestamp that may ever be served */
    public static function horizon(): int { return time() - self::minAge(); }

    /* ───────────── instruments, contracts, sessions ───────────── */

    /** "MNQ" / "NQZ6" / "mnqz26" → [data root, contract or null, tick, decimals] or null when unsupported */
    public static function instrument(string $typed): ?array
    {
        $s = strtoupper(preg_replace('/[^A-Za-z0-9]/', '', $typed));
        if (isset(CHART_INSTRUMENTS[$s])) return [CHART_INSTRUMENTS[$s][0], null, CHART_INSTRUMENTS[$s][1], CHART_INSTRUMENTS[$s][2]];
        if (preg_match('/^([A-Z0-9]{1,4}?)([' . CHART_MONTHS . '])(\d{1,2})$/', $s, $m) && isset(CHART_INSTRUMENTS[$m[1]])) {
            $root = CHART_INSTRUMENTS[$m[1]][0];
            // the bars of a micro come from the full contract of the same expiry
            return [$root, $root . $m[2] . substr($m[3], -1), CHART_INSTRUMENTS[$m[1]][1], CHART_INSTRUMENTS[$m[1]][2]];
        }
        return null;
    }

    private static function tz(): DateTimeZone { static $z = null; return $z ??= new DateTimeZone('America/New_York'); }
    /** session day of a timestamp: New York time + 6 h (18:00 ET belongs to the next day), same rule as the game */
    public static function sessionDay(int $ts): string { return (new DateTimeImmutable('@' . $ts))->setTimezone(self::tz())->modify('+6 hours')->format('Y-m-d'); }
    /** [start, end) of a CME session day in UTC seconds: 18:00 ET the day before → 17:00 ET */
    public static function sessionBounds(string $day): array
    {
        $d = new DateTimeImmutable($day . ' 17:00', self::tz());
        return [$d->modify('-1 day')->modify('+1 hour')->getTimestamp(), $d->getTimestamp()];
    }
    /** when a session day becomes old enough to be shown */
    public static function availableAt(string $day): int { return self::sessionBounds($day)[1] + self::minAge(); }

    /* ───────────── cache files ───────────── */

    private static function path(string $tf, string $root, string $name): string
    {
        $dir = rtrim((string) self::cfg()['chart_cache_dir'], '/') . "/$tf/" . preg_replace('/[^A-Z0-9]/', '', $root);
        if (!is_dir($dir)) @mkdir($dir, 0750, true);
        return $dir . '/' . preg_replace('/[^A-Za-z0-9_\-]/', '', $name) . '.json.gz';
    }
    private static function readGz(string $file): ?array
    {
        if (!is_file($file)) return null;
        $raw = @gzdecode((string) file_get_contents($file));
        $d = $raw ? json_decode($raw, true) : null;
        return is_array($d) ? $d : null;
    }
    private static function writeGz(string $file, array $data): void
    {
        $tmp = $file . '.' . getmypid() . '.tmp';
        file_put_contents($tmp, gzencode(json_encode($data, JSON_UNESCAPED_SLASHES), 6));
        rename($tmp, $file);
    }
    public static function cached(string $root, string $day, ?string $contract = null): ?array
    {
        $d = self::readGz(self::path('1m', $root, $day . ($contract ? '_' . $contract : '')));
        return $d && !empty($d['complete']) ? $d : null;
    }

    /* ───────────── budget and log ───────────── */

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $pdo = db(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $pdo->exec($my
            ? 'CREATE TABLE IF NOT EXISTS chart_fetch_log (id BIGINT AUTO_INCREMENT PRIMARY KEY, data_root VARCHAR(10) NOT NULL, schema_name VARCHAR(12) NOT NULL, start_utc DATETIME NOT NULL, end_utc DATETIME NOT NULL, bytes INT NULL, cost_usd DECIMAL(10,4) NULL, status VARCHAR(20) NOT NULL, created_at DATETIME NOT NULL) DEFAULT CHARSET=utf8mb4'
            : 'CREATE TABLE IF NOT EXISTS chart_fetch_log (id INTEGER PRIMARY KEY AUTOINCREMENT, data_root VARCHAR(10) NOT NULL, schema_name VARCHAR(12) NOT NULL, start_utc TEXT NOT NULL, end_utc TEXT NOT NULL, bytes INT NULL, cost_usd DECIMAL(10,4) NULL, status VARCHAR(20) NOT NULL, created_at TEXT NOT NULL)');
    }
    private static function log(string $root, string $schema, int $start, int $end, ?int $bytes, ?float $cost, string $status): void
    {
        self::schema();
        db()->prepare('INSERT INTO chart_fetch_log (data_root, schema_name, start_utc, end_utc, bytes, cost_usd, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
            ->execute([$root, $schema, gmdate('Y-m-d H:i:s', $start), gmdate('Y-m-d H:i:s', $end), $bytes, $cost, $status, gmdate('Y-m-d H:i:s')]);
    }
    public static function spentToday(): float
    {
        self::schema();
        return (float) db()->query("SELECT COALESCE(SUM(cost_usd), 0) FROM chart_fetch_log WHERE status = 'ok' AND created_at >= '" . gmdate('Y-m-d') . " 00:00:00'")->fetchColumn();
    }

    /* ───────────── HTTP (cURL, Basic auth, 3 tries with growing delay) ───────────── */

    private static function call(string $endpoint, array $params): array
    {
        $c = self::cfg();
        $url = rtrim((string) $c['databento_base_url'], '/') . '/' . $endpoint;
        for ($try = 1; $try <= 3; $try++) {
            if (!function_exists('curl_init')) {   // hosts without cURL: same request with PHP streams
                $ctx = stream_context_create(['http' => ['method' => 'POST', 'timeout' => 60, 'ignore_errors' => true, 'content' => http_build_query($params),
                    'header' => "Content-Type: application/x-www-form-urlencoded\r\nAuthorization: Basic " . base64_encode(trim((string) $c['databento_api_key']) . ':')]]);
                $body = @file_get_contents($url, false, $ctx); $code = 0;
                foreach ($http_response_header ?? [] as $h) if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $m)) $code = (int) $m[1];
                if ($code === 200) return [200, (string) $body];
                if ($code !== 0 && $code !== 429 && $code < 500) return [$code, (string) $body];
                if ($try < 3) usleep((int) (500000 * (2 ** ($try - 1))));
                continue;
            }
            $ch = curl_init($url);
            curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => http_build_query($params), CURLOPT_RETURNTRANSFER => true,
                CURLOPT_USERPWD => trim((string) $c['databento_api_key']) . ':', CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
                CURLOPT_TIMEOUT => 60, CURLOPT_CONNECTTIMEOUT => 10, CURLOPT_ENCODING => '']);
            $body = curl_exec($ch); $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
            if ($code === 200) return [200, (string) $body];
            if ($code !== 0 && $code !== 429 && $code < 500) return [$code, (string) $body];   // 4xx: no point retrying
            if ($try < 3) usleep((int) (500000 * (2 ** ($try - 1))));
        }
        return [$code ?? 0, (string) ($body ?? '')];
    }

    /** contract really traded on a session day for a continuous symbol (free symbology.resolve, two hops) */
    private static function resolveContract(string $root, string $day): ?string
    {
        $c = self::cfg(); $next = (new DateTimeImmutable($day))->modify('+1 day')->format('Y-m-d');
        [$code, $body] = self::call('symbology.resolve', ['dataset' => $c['databento_dataset'], 'symbols' => "$root.v.0", 'stype_in' => 'continuous', 'stype_out' => 'instrument_id', 'start_date' => $day, 'end_date' => $next]);
        $r = $code === 200 ? json_decode($body, true) : null;
        $id = $r['result']["$root.v.0"][0]['s'] ?? null;
        if (!$id) return null;
        [$code, $body] = self::call('symbology.resolve', ['dataset' => $c['databento_dataset'], 'symbols' => (string) $id, 'stype_in' => 'instrument_id', 'stype_out' => 'raw_symbol', 'start_date' => $day, 'end_date' => $next]);
        $r = $code === 200 ? json_decode($body, true) : null;
        return $r['result'][(string) $id][0]['s'] ?? null;
    }

    /** one get_range call, budget-checked and logged. @return array{0:string,1:array} [status, bars] */
    private static function fetchRange(string $root, ?string $contract, string $schema, int $start, int $end): array
    {
        $c = self::cfg();
        $params = ['dataset' => $c['databento_dataset'], 'symbols' => $contract ?: "$root.v.0", 'stype_in' => $contract ? 'raw_symbol' : 'continuous',
                   'schema' => $schema, 'start' => gmdate('Y-m-d\TH:i:s\Z', $start), 'end' => gmdate('Y-m-d\TH:i:s\Z', $end)];
        // free cost estimate first; the daily budget is a hard stop
        [$cc, $cb] = self::call('metadata.get_cost', $params);
        $cost = $cc === 200 && is_numeric(trim($cb)) ? (float) trim($cb) : null;
        if ($cost !== null && self::spentToday() + $cost > (float) $c['chart_daily_budget_usd']) {
            error_log(sprintf('[Sweep chart] daily budget reached (%.2f USD): %s %s skipped', (float) $c['chart_daily_budget_usd'], $root, $schema));
            self::log($root, $schema, $start, $end, null, $cost, 'budget');
            return ['budget', []];
        }
        [$code, $body] = self::call('timeseries.get_range', $params + ['encoding' => 'json', 'pretty_px' => 'true', 'pretty_ts' => 'false', 'map_symbols' => 'false']);
        if ($code !== 200) {
            error_log('[Sweep chart] Databento HTTP ' . $code . ' ' . substr($body, 0, 200));
            self::log($root, $schema, $start, $end, strlen($body), null, 'error');
            return ['error', []];
        }
        $bars = [];
        foreach (preg_split('/\r?\n/', $body) as $line) {
            if ($line === '') continue;
            $r = json_decode($line, true); if (!is_array($r)) continue;
            $ts = $r['hd']['ts_event'] ?? null;
            $t = is_numeric($ts) ? intdiv((int) $ts, 1000000000) : (is_string($ts) ? strtotime($ts) : 0);
            if (!$t) continue;
            $bars[] = [$t, (float) $r['open'], (float) $r['high'], (float) $r['low'], (float) $r['close'], (int) ($r['volume'] ?? 0)];
        }
        usort($bars, fn($a, $b) => $a[0] <=> $b[0]);
        self::log($root, $schema, $start, $end, strlen($body), $cost, 'ok');
        return ['ok', $bars];
    }

    /**
     * One session day of 1-minute bars, from the shared cache or Databento (once for everybody).
     * @return array{status:string, contract?:string, bars?:array, available_at?:int}
     */
    public static function day(string $root, string $day, ?string $contract = null): array
    {
        if ($hit = self::cached($root, $day, $contract)) return ['status' => 'ok', 'contract' => $hit['contract'], 'bars' => $hit['bars']];
        $avail = self::availableAt($day);
        if (time() < $avail) return ['status' => 'too_recent', 'available_at' => $avail];
        if (!self::enabled()) return ['status' => 'unavailable'];
        $file = self::path('1m', $root, $day . ($contract ? '_' . $contract : ''));
        $lock = fopen($file . '.lock', 'c');
        if (!$lock || !flock($lock, LOCK_EX)) return ['status' => 'unavailable'];
        try {
            if ($hit = self::cached($root, $day, $contract)) return ['status' => 'ok', 'contract' => $hit['contract'], 'bars' => $hit['bars']];   // fetched while we waited
            [$s, $e] = self::sessionBounds($day);
            [$st, $bars] = self::fetchRange($root, $contract, 'ohlcv-1m', $s, $e);
            if ($st !== 'ok') return ['status' => $st === 'budget' ? 'soon' : 'unavailable'];
            $con = $contract ?: (self::resolveContract($root, $day) ?: "$root.v.0");
            // complete only because the whole session is older than the delay (checked above)
            self::writeGz($file, ['contract' => $con, 'tf' => '1m', 'fetched_at' => gmdate('c'), 'complete' => true, 'bars' => $bars]);
            return ['status' => 'ok', 'contract' => $con, 'bars' => $bars];
        } finally { flock($lock, LOCK_UN); fclose($lock); @unlink($file . '.lock'); }
    }

    /** 1-second bars for a short window (trade under 2 h, ±15 min), cached per window */
    public static function seconds(string $root, int $from, int $to, ?string $contract = null): array
    {
        $from -= 900; $to += 900;
        if ($to - $from > 3 * 3600) return ['status' => 'unsupported'];
        if ($to > self::horizon()) return ['status' => 'too_recent', 'available_at' => $to + self::minAge()];
        if (!self::enabled()) return ['status' => 'unavailable'];
        $name = gmdate('Y-m-d\TH-i', $from) . '_' . gmdate('H-i', $to) . ($contract ? '_' . $contract : '');
        $file = self::path('1s', $root, $name);
        if (($d = self::readGz($file)) && !empty($d['complete'])) return ['status' => 'ok', 'contract' => $d['contract'], 'bars' => $d['bars']];
        [$st, $bars] = self::fetchRange($root, $contract, 'ohlcv-1s', $from, $to);
        if ($st !== 'ok') return ['status' => $st === 'budget' ? 'soon' : 'unavailable'];
        $con = $contract ?: (self::cached($root, self::sessionDay($from))['contract'] ?? "$root.v.0");
        self::writeGz($file, ['contract' => $con, 'tf' => '1s', 'fetched_at' => gmdate('c'), 'complete' => true, 'bars' => $bars]);
        return ['status' => 'ok', 'contract' => $con, 'bars' => $bars];
    }

    /** aggregate bars to a larger unit, on the fly; empty intervals stay empty */
    public static function aggregate(array $bars, int $sec): array
    {
        $out = []; $cur = null;
        foreach ($bars as [$t, $o, $h, $l, $c, $v]) {
            $b = $t - ($t % $sec);
            if (!$cur || $cur[0] !== $b) { if ($cur) $out[] = $cur; $cur = [$b, $o, $h, $l, $c, $v]; }
            else { $cur[2] = max($cur[2], $h); $cur[3] = min($cur[3], $l); $cur[4] = $c; $cur[5] += $v; }
        }
        if ($cur) $out[] = $cur;
        return $out;
    }

    /** bars between from and to (UTC seconds) for a timeframe; never newer than the horizon */
    public static function bars(string $typed, int $from, int $to, string $tf): array
    {
        $inst = self::instrument($typed);
        if (!$inst) return ['status' => 'unsupported'];
        [$root, $contract, $tick, $dec] = $inst;
        if (!isset(CHART_TFS[$tf])) $tf = '1m';
        $sec = CHART_TFS[$tf];
        if ($sec < 60) {
            $r = self::seconds($root, $from, $to, $contract);
            if ($r['status'] !== 'ok') return $r + ['tick_size' => $tick];
            $bars = self::aggregate($r['bars'], $sec); $con = $r['contract'];
        } else {
            $bars = []; $con = null;
            for ($d = self::sessionDay($from); $d <= self::sessionDay($to); $d = (new DateTimeImmutable($d))->modify('+1 day')->format('Y-m-d')) {
                if ((int) (new DateTimeImmutable($d))->format('N') > 5) continue;      // CME futures: no Saturday or Sunday session day
                $r = self::day($root, $d, $contract);
                if ($r['status'] !== 'ok') return $r + ['tick_size' => $tick];
                $bars = array_merge($bars, $r['bars']); $con = $r['contract'];
            }
            if ($sec > 60) $bars = self::aggregate($bars, $sec);
        }
        $h = self::horizon();
        $bars = array_values(array_filter($bars, fn($b) => $b[0] >= $from - $sec && $b[0] <= $to && $b[0] + $sec <= $h));   // licence guard, again
        return ['status' => 'ok', 'available_at' => null, 'contract' => $con, 'tick_size' => $tick, 'decimals' => $dec, 'tf' => $tf, 'bars' => $bars];
    }

    /* ───────────── trade window ───────────── */

    private static function epochEt(string $date, string $time): int { return (new DateTimeImmutable($date . ' ' . $time, self::tz()))->getTimestamp(); }

    /** UTC seconds of a trade's entry and exit, from its executions or its entry/exit times (New York) */
    public static function tradeSpan(array $t): ?array
    {
        $ts = [];
        foreach ((array) ($t['executions'] ?? []) as $x) if (!empty($x['t']) && preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/', (string) $x['t'])) $ts[] = self::epochEt(substr((string) $x['t'], 0, 10), substr((string) $x['t'], 11));
        if (!$ts && !empty($t['date']) && !empty($t['entry_time'])) {
            // the trade's date is its session: from 18:00 ET the clock time is the evening before
            // same rule as GameEngine::hasSessionDate (game/game.php)
            $x0 = $t['executions'][0]['t'] ?? null;
            $sess = !empty($t['session_date']) || substr((string) $t['entry_time'], 0, 5) < '18:00' || (is_string($x0) && substr($x0, 0, 10) < (string) $t['date']);
            $wall = fn(string $hm) => $sess && substr($hm, 0, 2) >= '18' ? (new DateTimeImmutable((string) $t['date']))->modify('-1 day')->format('Y-m-d') : (string) $t['date'];
            $ts[] = self::epochEt($wall((string) $t['entry_time']), (string) $t['entry_time']);
            if (!empty($t['exit_time'])) { $x = self::epochEt($wall((string) $t['exit_time']), (string) $t['exit_time']); if ($x < $ts[0]) $x += 86400; $ts[] = $x; }
        }
        return $ts ? [min($ts), max($ts)] : null;
    }
    /** default unit and context for a trade: < 15 min → 1m, < 2 h → 5m, else 15m; 60 bars before, 30 after */
    public static function tradeWindow(int $in, int $out, ?string $tf = null): array
    {
        $dur = max(0, $out - $in);
        $tf = $tf && isset(CHART_TFS[$tf]) ? $tf : ($dur < 900 ? '1m' : ($dur < 7200 ? '5m' : '15m'));
        if (CHART_TFS[$tf] < 60 && $dur >= 7200) $tf = '1m';   // seconds only for trades under 2 h
        $sec = CHART_TFS[$tf];
        return [$tf, $in - 60 * $sec, $out + 30 * $sec];
    }
}

/* ───────────── route: GET api/chart/bars ───────────── */

function chart_route(string $route, string $method, string $uid): void
{
    if ($route !== 'api/chart/bars' || $method !== 'GET') json_out(404, ['error' => 'not found']);
    // 60 requests a minute per trader
    if (function_exists('throttle')) { throttle(['chart:' . $uid], 60, 60); record_attempt(['chart:' . $uid]); }
    $tf = (string) ($_GET['tf'] ?? '');
    if (!empty($_GET['trade_id'])) {
        $st = db()->prepare("SELECT data FROM documents WHERE user_id = ? AND collection = 'trades' AND id = ?");
        $st->execute([$uid, (string) $_GET['trade_id']]);
        $t = json_decode((string) $st->fetchColumn(), true);
        if (!is_array($t)) json_out(404, ['status' => 'unavailable']);                       // only your own trades
        $span = ChartData::tradeSpan($t);
        if (!$span) json_out(200, ['status' => 'unavailable']);
        [$tf, $from, $to] = ChartData::tradeWindow($span[0], $span[1], $tf ?: null);
        $typed = (string) ($t['contract'] ?? '') ?: (string) ($t['instrument'] ?? 'NQ');
        $r = ChartData::bars($typed, $from, $to, $tf);
        json_out(200, $r + ['entry_ts' => $span[0], 'exit_ts' => $span[1]]);
    }
    // free window for the add-trade form: 8 hours at most
    $from = (int) ($_GET['from'] ?? 0); $to = (int) ($_GET['to'] ?? 0);
    if ($from <= 0 || $to <= $from || $to - $from > 8 * 3600) json_out(400, ['status' => 'unavailable', 'error' => 'Invalid window (8 h max).']);
    $sym = (string) ($_GET['symbol'] ?? 'NQ');
    if ($tf && isset(CHART_TFS[$tf]) && CHART_TFS[$tf] < 60 && $to - $from > 7200) $tf = '1m';
    json_out(200, ChartData::bars($sym, $from, $to, $tf ?: '1m'));
}
