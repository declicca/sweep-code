<?php
/**
 * Trading Journal — economic event engine.
 * Raw economic data (provider) · deterministic calculations (surprise, revision, NQ reaction) · knowledge base · history.
 */
const REACT_MUTED_PTS = 15;     // largest move in the first 5 minutes below this = muted
const REACT_FLAT_PTS  = 8;      // a 30-minute change smaller than this counts as flat
const REACT_SUSTAIN   = 0.75;   // 30-minute move keeps at least 75% of the initial move = sustained
const REACT_OFFSETS   = [1, 5, 15, 30, 60];

if (!function_exists('mb_substr')) { function mb_substr($s, $start, $len = null) { return $len === null ? substr($s, $start) : substr($s, $start, $len); } }
if (!function_exists('mb_strlen')) { function mb_strlen($s) { return strlen($s); } }
function econ_schema(): void {
    static $done = false; if ($done) return; $done = true;
    $pdo = db(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $pdo->exec('DROP TABLE IF EXISTS econ_ai');   // leftover from the removed AI analysis
    $pdo->exec($my
        ? 'CREATE TABLE IF NOT EXISTS econ_reaction (event_id CHAR(40) NOT NULL PRIMARY KEY, provider VARCHAR(20) NOT NULL, computed_at INT NOT NULL, complete TINYINT NOT NULL, json TEXT NOT NULL) DEFAULT CHARSET=utf8mb4'
        : 'CREATE TABLE IF NOT EXISTS econ_reaction (event_id TEXT PRIMARY KEY, provider TEXT NOT NULL, computed_at INTEGER NOT NULL, complete INTEGER NOT NULL, json TEXT NOT NULL)');
    $cols = [];
    if ($my) { foreach ($pdo->query('SHOW COLUMNS FROM econ_events') as $c) $cols[] = $c['Field']; }
    else { foreach ($pdo->query('PRAGMA table_info(econ_events)') as $c) $cols[] = $c['name']; }
    foreach (['revised' => 'VARCHAR(40)', 'unit' => 'VARCHAR(20)', 'ticker' => 'VARCHAR(60)', 'provider_event_id' => 'VARCHAR(60)', 'provider_updated' => 'VARCHAR(40)', 'reference' => 'VARCHAR(40)'] as $c => $t)
        if (!in_array($c, $cols, true)) $pdo->exec("ALTER TABLE econ_events ADD COLUMN $c " . ($my ? "$t NULL" : 'TEXT'));
}

/* ---------------- deterministic numbers ---------------- */
/** "0.4%" → [0.4, '%'], "220K" → [220, 'K'], "-1.2B" → [-1.2, 'B']; null when not numeric. */
function econ_num(?string $v): ?array {
    if ($v === null) return null; $v = trim(str_replace([',', ' '], '', $v));
    if (!preg_match('/^([+-]?\d+(?:\.\d+)?)(%|K|M|B|T)?$/i', $v, $m)) return null;
    return [(float)$m[1], strtoupper($m[2] ?? '')];
}
function econ_diff(?string $a, ?string $b): ?array {
    $x = econ_num($a); $y = econ_num($b);
    if (!$x || !$y || $x[1] !== $y[1]) return null;
    $d = round($x[0] - $y[0], 4); $unit = $x[1] === '%' ? 'pp' : $x[1];
    $dec = max(strlen(explode('.', (string)$x[0] . '.')[1] ?? ''), strlen(explode('.', (string)$y[0] . '.')[1] ?? ''));
    $txt = ($d > 0 ? '+' : ($d < 0 ? '−' : '')) . number_format(abs($d), min(3, $dec)) . ($unit === 'pp' ? ' pp' : $unit);
    return ['value' => $d, 'unit' => $unit, 'text' => $d == 0 ? 'In line (0' . ($unit === 'pp' ? ' pp' : $unit) . ')' : $txt, 'direction' => $d > 0 ? 'above' : ($d < 0 ? 'below' : 'in_line')];
}
function econ_calc(array $e): array {
    $c = ['vs_forecast' => econ_diff($e['actual'] ?? null, $e['forecast'] ?? null), 'vs_previous' => econ_diff($e['actual'] ?? null, $e['previous'] ?? null), 'revision' => null];
    $rev = trim((string)($e['revised'] ?? ''));
    if ($rev !== '' && $rev !== trim((string)($e['previous'] ?? ''))) $c['revision'] = ['reported' => $rev, 'current' => $e['previous'], 'change' => econ_diff($e['previous'] ?? null, $rev)];
    return $c;
}
function econ_state(array $e): string {
    $now = time(); $ts = (int)$e['ts'];
    if ($ts > $now) return 'before';
    if (($e['actual'] ?? null) === null || $e['actual'] === '') return in_array($e['source'] ?? '', ['schedule', 'manual'], true) && $now - $ts > 86400 ? 'past_no_data' : 'awaiting';
    return $now - $ts >= 3600 ? 'post' : 'released';
}

/* ---------------- knowledge base ---------------- */
function econ_profiles(): array { static $p = null; if ($p === null) { $d = json_decode((string)@file_get_contents(__DIR__ . '/econ-profiles.json'), true); $p = $d['profiles'] ?? []; } return $p; }
function econ_profile(string $name): ?array { foreach (econ_profiles() as $p) if (preg_match('/' . $p['match'] . '/i', $name)) return $p; return null; }

/* ---------------- NQ reaction (deterministic) ---------------- */
function econ_reaction(array $e): ?array {
    global $MARKET_PROVIDER, $MARKET_KEY, $MARKET_SYMBOL;
    $ts = (int)$e['ts']; $now = time();
    if ($MARKET_PROVIDER !== 'databento' || $MARKET_KEY === '') return ['available' => false, 'reason' => 'no_market_data'];
    if ($now < $ts + 60) return ['available' => false, 'reason' => 'too_early'];
    $row = q('SELECT json, complete FROM econ_reaction WHERE event_id = ?', [$e['id']])->fetch();
    if ($row && (int)$row['complete'] === 1) return json_decode($row['json'], true);
    try { candles_sync($ts - 300, min($now, $ts + 3660)); } catch (Throwable $x) { error_log('reaction candles: ' . $x->getMessage()); }
    $bars = q('SELECT t, o, h, l, c FROM candles WHERE symbol = ? AND t BETWEEN ? AND ? ORDER BY t', [$MARKET_SYMBOL, $ts - 60, $ts + 3600])->fetchAll(PDO::FETCH_NUM);
    $bars = array_map(fn($b) => [(int)$b[0], (float)$b[1], (float)$b[2], (float)$b[3], (float)$b[4]], $bars);
    $first = null; foreach ($bars as $b) if ($b[0] >= $ts - 59) { $first = $b; break; }
    if (!$first) return ['available' => false, 'reason' => 'no_bars'];
    $ref = $first[1]; $out = ['available' => true, 'provider' => 'databento', 'symbol' => $MARKET_SYMBOL, 'ref_ts' => $first[0], 'release_price' => $ref, 'offsets' => []];
    foreach (REACT_OFFSETS as $m) {
        $end = $ts + $m * 60; if ($end > $now) break;
        $win = array_values(array_filter($bars, fn($b) => $b[0] >= $first[0] && $b[0] < $first[0] + $m * 60));
        if (!$win) break;
        $last = end($win); $hi = max(array_column($win, 2)); $lo = min(array_column($win, 3));
        $out['offsets'][] = ['minutes' => $m, 'price' => $last[4], 'change' => round($last[4] - $ref, 2), 'max_up' => round($hi - $ref, 2), 'max_down' => round($lo - $ref, 2)];
    }
    $out['classification'] = econ_classify($out['offsets']);
    $complete = count($out['offsets']) === count(REACT_OFFSETS);
    $out['complete'] = $complete; $out['computed_at'] = $now;
    $j = json_encode($out);
    if (q('UPDATE econ_reaction SET provider = ?, computed_at = ?, complete = ?, json = ? WHERE event_id = ?', ['databento', $now, $complete ? 1 : 0, $j, $e['id']])->rowCount() === 0)
        q('INSERT INTO econ_reaction (event_id, provider, computed_at, complete, json) VALUES (?, ?, ?, ?, ?)', [$e['id'], 'databento', $now, $complete ? 1 : 0, $j]);
    return $out;
}
/** Quantitative labels only; see the thresholds at the top of this file. */
function econ_classify(array $off): ?array {
    $by = []; foreach ($off as $o) $by[$o['minutes']] = $o;
    if (!isset($by[5])) return null;
    $ex = max(abs($by[5]['max_up']), abs($by[5]['max_down']));
    $rule = 'Initial move = change after 5 min (or the larger excursion if flat); muted below ' . REACT_MUTED_PTS . ' pts; sustained if the 30-min change keeps ' . (REACT_SUSTAIN * 100) . '% of it; reversal if the 30-min change is at least ' . REACT_FLAT_PTS . ' pts the other way.';
    if ($ex < REACT_MUTED_PTS) return ['label' => 'MUTED REACTION', 'key' => 'muted', 'rule' => $rule];
    $init = abs($by[5]['change']) >= REACT_FLAT_PTS ? $by[5]['change'] : (abs($by[5]['max_up']) >= abs($by[5]['max_down']) ? $by[5]['max_up'] : $by[5]['max_down']);
    $dir = $init > 0 ? 1 : -1; $word = $dir > 0 ? 'RALLY' : 'SELL-OFF';
    if (!isset($by[30])) return ['label' => 'INITIAL ' . $word, 'key' => 'initial', 'rule' => $rule];
    $c30 = $by[30]['change'];
    if ($c30 * $dir > 0 && abs($c30) >= REACT_SUSTAIN * abs($init)) return ['label' => 'SUSTAINED ' . $word, 'key' => 'sustained', 'rule' => $rule];
    if ($c30 * $dir < 0 && abs($c30) >= REACT_FLAT_PTS) return ['label' => 'REVERSAL AFTER INITIAL MOVE', 'key' => 'reversal', 'rule' => $rule];
    return ['label' => 'INITIAL ' . $word, 'key' => 'initial', 'rule' => $rule];
}

/* ---------------- history ---------------- */
function econ_history(array $e, int $n = 8): array {
    global $ECON_PROVIDER, $ECON_KEY;
    if ($ECON_PROVIDER === 'tradingeconomics' && $ECON_KEY !== '' && !empty($e['ticker'])) {
        $k = 'hist:' . $e['ticker'];
        if (time() - (int)setting($k, '0') > 86400) {
            $from = gmdate('Y-m-d', time() - 400 * 86400); $to = gmdate('Y-m-d');
            [$code, $body] = http_get('https://api.tradingeconomics.com/calendar/ticker/' . rawurlencode($e['ticker']) . '/' . $from . '/' . $to . '?c=' . urlencode($ECON_KEY) . '&f=json');
            $rows = $code === 200 ? json_decode($body, true) : null;
            if (is_array($rows)) { econ_store(array_filter(array_map('te_row', $rows)), 'tradingeconomics'); save_setting($k, (string)time()); }
        }
        $rows = q('SELECT id, ts, event, actual, forecast, previous, revised FROM econ_events WHERE ticker = ? AND ts < ? ORDER BY ts DESC LIMIT ' . $n, [$e['ticker'], (int)$e['ts']])->fetchAll();
    } else {
        $rows = q('SELECT id, ts, event, actual, forecast, previous, revised FROM econ_events WHERE event = ? AND ts < ? ORDER BY ts DESC LIMIT ' . $n, [$e['event'], (int)$e['ts']])->fetchAll();
    }
    foreach ($rows as &$r) {
        $r['ts'] = (int)$r['ts']; $r['surprise'] = econ_diff($r['actual'], $r['forecast']);
        $rx = q('SELECT json FROM econ_reaction WHERE event_id = ?', [$r['id']])->fetchColumn();
        $r['reaction'] = $rx ? json_decode($rx, true) : null;
    }
    return $rows;
}
/** Trading Economics row → normalized event (US, high/medium only). */
function te_row(array $r): ?array {
    if (strtolower((string)($r['Country'] ?? '')) !== 'united states') return null;
    $imp = (int)($r['Importance'] ?? 0); if ($imp < 2) return null;
    $v = fn($k) => (isset($r[$k]) && trim((string)$r[$k]) !== '') ? trim((string)$r[$k]) : null;
    return ['country' => 'US', 'time' => str_replace('T', ' ', substr((string)$r['Date'], 0, 19)), 'event' => (string)$r['Event'], 'impact' => $imp >= 3 ? 'high' : 'medium', 'unit' => '',
            'actual' => $v('Actual'), 'forecast' => $v('Forecast'), 'previous' => $v('Previous'), 'revised' => $v('Revised'), 'ticker' => $v('Ticker'),
            'provider_event_id' => $v('CalendarId'), 'provider_updated' => $v('LastUpdate'), 'reference' => $v('Reference'), 'raw' => true];
}

/* ---------------- event context ---------------- */
function econ_event_row(string $id): ?array {
    $e = q('SELECT * FROM econ_events WHERE id = ?', [$id])->fetch();
    if (!$e) return null; $e['ts'] = (int)$e['ts']; return $e;
}
function econ_context(array $e, bool $withReaction = true): array {
    $p = econ_profile($e['event']); $calc = econ_calc($e);
    $ctx = ['event' => ['name' => $e['event'], 'country' => 'United States', 'currency' => 'USD', 'impact' => $e['impact'],
            'release_time_et' => (new DateTime('@' . $e['ts']))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d H:i') . ' ET', 'state' => econ_state($e)],
        'values' => ['actual' => $e['actual'] ?? null, 'forecast' => $e['forecast'] ?? null, 'previous' => $e['previous'] ?? null, 'revised_previous' => $e['revised'] ?? null, 'unit' => $e['unit'] ?? null],
        'computed' => $calc, 'primary_instrument' => 'NQ (E-mini Nasdaq-100 futures)',
        'profile' => $p ? array_diff_key($p, ['match' => 1, 'key' => 1]) : null];
    $h = econ_history($e, 6);
    $ctx['history'] = array_map(fn($r) => ['date' => gmdate('Y-m-d', $r['ts']), 'actual' => $r['actual'], 'forecast' => $r['forecast'], 'surprise' => $r['surprise']['text'] ?? null,
        'nq_reaction' => ($r['reaction']['available'] ?? false) ? ['label' => $r['reaction']['classification']['label'] ?? null, 'offsets' => $r['reaction']['offsets']] : null], $h);
    if ($withReaction) { $rx = econ_reaction($e); $ctx['nq_reaction'] = ($rx['available'] ?? false) ? $rx : null; }
    return $ctx;
}
function econ_detail(string $id): ?array {
    global $ECON_PROVIDER, $ECON_KEY;
    econ_schema(); $e = econ_event_row($id); if (!$e) return null;
    $ctx = econ_context($e);
    $prov = $ECON_KEY !== '' && in_array($ECON_PROVIDER, ['tradingeconomics', 'fmp', 'finnhub'], true) ? $ECON_PROVIDER : 'manual';
    return ['event' => ['id' => $e['id'], 'ts' => $e['ts'], 'event' => $e['event'], 'impact' => $e['impact'], 'actual' => $e['actual'], 'forecast' => $e['forecast'], 'previous' => $e['previous'],
                'revised' => $e['revised'] ?? null, 'unit' => $e['unit'] ?? null, 'status' => $e['status'] ?? null, 'reference' => $e['reference'] ?? null],
        'state' => econ_state($e), 'computed' => $ctx['computed'], 'profile' => $ctx['profile'], 'history' => econ_history($e, 6), 'reaction' => $ctx['nq_reaction'] ?? econ_reaction($e),
        'provenance' => ['economic_data_provider' => $e['source'] === 'schedule' ? 'schedule file' : ($e['source'] ?? $prov), 'economic_data_last_updated' => $e['provider_updated'] ?: gmdate('c', (int)$e['updated_at']),
            'market_data_provider' => ($ctx['nq_reaction']['provider'] ?? null), 'market_data_timestamp' => isset($ctx['nq_reaction']['computed_at']) ? gmdate('c', $ctx['nq_reaction']['computed_at']) : null]];
}
