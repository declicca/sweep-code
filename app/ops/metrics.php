<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — admin dashboard numbers (Settings → Admin). Everything comes from Sweep's own database.
 * North star: traders who swept 3+ days in the last 7 days. Activation: first trade within 24 h of sign-up.
 * « Aha »: first swept day within 7 days. Week-2 retention: 3+ swept days during days 8-14.
 * Brief 01 step 4 (block « brief »), for the traders of the chosen sign-up week (cohort, Monday New York) and source
 * (« Where did you find Sweep? », users.found_via): median sign-up → first trade, activation (a trade on the sign-up day,
 * New York), retention D7 / D30 (a trade or a review during days 7-13 / 30-36, only traders whose window is over),
 * swept days (sessions with trades where the 3 rings are closed, last 30 days). JS errors grouped by message (30 days):
 * occurrences, traders affected, last seen, pages, browsers, versions — never any trade content.
 */
function sweep_metrics(PDO $pdo, string $app, array $f = []): array
{
    $q = function (string $sql, array $a = []) use ($pdo) { $s = $pdo->prepare($sql); $s->execute($a); return $s; };
    $now = time(); $day = 86400;
    $has = fn(string $t) => (bool) $q("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", [$t])->fetchColumn();
    $users = $q('SELECT id, created_at, utm_source, utm_campaign, is_internal FROM users WHERE disabled = 0')->fetchAll(PDO::FETCH_ASSOC);
    $users = array_values(array_filter($users, fn($u) => !(int) ($u['is_internal'] ?? 0)));
    $ny = new DateTimeZone('America/New_York');
    $nyDay = fn(int $ts) => (new DateTimeImmutable('@' . $ts))->setTimezone($ny)->format('Y-m-d');
    $monday = fn(string $d) => (new DateTimeImmutable($d . ' 12:00', $ny))->modify('monday this week')->format('Y-m-d');
    $via = []; foreach ($q("SELECT id, COALESCE(NULLIF(found_via, ''), 'none') v FROM users") as $r) $via[$r['id']] = $r['v'];
    foreach ($users as &$u) { $u['ts'] = strtotime((string) $u['created_at']) ?: 0; $u['d0'] = $nyDay($u['ts']); $u['week'] = $monday($u['d0']); $u['via'] = $via[$u['id']] ?? 'none'; } unset($u);
    // the filters (brief 01 step 4): the lists of weeks and sources are counted on every trader, the numbers on the chosen ones
    $weeks = []; $sources = [];
    foreach ($users as $u) { $weeks[$u['week']] = ($weeks[$u['week']] ?? 0) + 1; $sources[$u['via']] = ($sources[$u['via']] ?? 0) + 1; }
    krsort($weeks); arsort($sources);
    $fc = (string) ($f['cohort'] ?? ''); $fs = (string) ($f['source'] ?? '');
    $all = $users;
    $users = array_values(array_filter($users, fn($u) => ($fc === '' || $u['week'] === $fc) && ($fs === '' || $u['via'] === $fs)));
    $first = []; if ($has('game_analytics')) foreach ($q("SELECT user_id, MIN(created_at) t FROM game_analytics WHERE event = 'trade_logged' GROUP BY user_id") as $r) $first[$r['user_id']] = (int) $r['t'];
    $swept = []; if ($has('game_days')) foreach ($q('SELECT user_id, trading_day FROM game_days WHERE is_swept = 1') as $r) $swept[$r['user_id']][] = $r['trading_day'];
    $rate = fn(int $a, int $b) => $b ? (int) round($a / $b * 100) : null;
    $act = $actN = $aha = $ahaN = $w2 = $w2N = 0; $src = [];
    foreach ($users as $u) {
        $age = $now - $u['ts'];
        if ($age <= 30 * $day) { $k = $u['utm_campaign'] ?: ($u['utm_source'] ?: 'direct'); $src[$k] = ($src[$k] ?? 0) + 1; }
        if ($age >= $day && $age <= 60 * $day) { $actN++; if (isset($first[$u['id']]) && $first[$u['id']] - $u['ts'] <= $day) $act++; }
        $d0 = gmdate('Y-m-d', $u['ts']);
        if ($age >= 7 * $day && $age <= 60 * $day) { $ahaN++; foreach ($swept[$u['id']] ?? [] as $d) if ($d <= gmdate('Y-m-d', $u['ts'] + 7 * $day)) { $aha++; break; } }
        if ($age >= 14 * $day && $age <= 90 * $day) { $w2N++; $n = 0; foreach ($swept[$u['id']] ?? [] as $d) if ($d > gmdate('Y-m-d', $u['ts'] + 7 * $day) && $d <= gmdate('Y-m-d', $u['ts'] + 14 * $day)) $n++; if ($n >= 3) $w2++; }
    }
    arsort($src);
    $since7 = gmdate('Y-m-d', $now - 7 * $day);
    $north = 0; foreach ($swept as $uid => $ds) { if (count(array_filter($ds, fn($d) => $d > $since7)) >= 3) $north++; }
    $active7 = $has('game_days') ? (int) $q('SELECT COUNT(DISTINCT user_id) FROM game_days WHERE activity = 1 AND trading_day > ?', [$since7])->fetchColumn() : 0;
    $ai = ['today' => 0.0, 'd7' => 0.0, 'calls_today' => 0];
    if ($has('ai_log')) {
        $r = $q('SELECT COALESCE(SUM(cost_usd), 0) c, COUNT(*) n FROM ai_log WHERE created_at >= ?', [gmdate('Y-m-d')])->fetch(PDO::FETCH_ASSOC);
        $ai = ['today' => round((float) $r['c'], 3), 'calls_today' => (int) $r['n'], 'd7' => round((float) $q('SELECT COALESCE(SUM(cost_usd), 0) FROM ai_log WHERE created_at >= ?', [gmdate('Y-m-d', $now - 7 * $day)])->fetchColumn(), 3)];
    }
    $methods = []; if ($has('game_analytics')) foreach ($q("SELECT meta_json FROM game_analytics WHERE event = 'trade_logged' AND created_at > ?", [$now - 30 * $day]) as $r) { $m = (json_decode((string) $r['meta_json'], true) ?: [])['method'] ?? 'manual'; $methods[$m] = ($methods[$m] ?? 0) + 1; }
    $errs = ['js_24h' => 0, 'top' => [], 'php_24h' => 0];
    if ($has('client_errors')) {
        $errs['js_24h'] = (int) $q('SELECT COUNT(*) FROM client_errors WHERE created_at > ?', [$now - $day])->fetchColumn();
        $errs['top'] = $q('SELECT msg, COUNT(*) n FROM client_errors WHERE created_at > ? GROUP BY msg ORDER BY n DESC LIMIT 5', [$now - 7 * $day])->fetchAll(PDO::FETCH_ASSOC);
    }
    $log = $app . '/error_log';
    if (is_file($log) && filesize($log) < 50 * 1048576) {
        $tags = ['[' . gmdate('d-M-Y', $now), '[' . gmdate('d-M-Y', $now - $day)];
        $fh = fopen($log, 'r'); if ($fh) { fseek($fh, max(0, filesize($log) - 2 * 1048576)); while (($line = fgets($fh)) !== false) foreach ($tags as $tg) if (strpos($line, $tg) === 0) { $errs['php_24h']++; break; } fclose($fh); }
    }
    $rev = ['subs' => [], 'mrr' => null];
    if ($has('billing_subs')) {
        $price = ['pro' => ['month' => 19, 'year' => 159], 'elite' => ['month' => 39, 'year' => 329]];
        $mrr = 0.0;
        foreach ($q("SELECT plan, billing_interval i, founding, COUNT(*) n FROM billing_subs WHERE status IN ('active','trialing','past_due') GROUP BY plan, billing_interval, founding") as $r) {
            $rev['subs'][] = $r;
            $p = $price[$r['plan']][$r['i'] === 'year' ? 'year' : 'month'] ?? 0; $m = $r['i'] === 'year' ? $p / 12 : $p;
            $mrr += $m * (int) $r['n'] * ((int) $r['founding'] ? 0.5 : 1);
        }
        $rev['mrr'] = round($mrr, 2);
    }
    $miss = [];
    if ($has('game_analytics')) foreach ($q("SELECT meta_json FROM game_analytics WHERE event = 'search_no_result' AND created_at > ?", [$now - 30 * $day]) as $r) {
        $mm = json_decode((string) $r['meta_json'], true) ?: []; $k = ($mm['q'] ?? '') . ' (' . ($mm['lang'] ?? '?') . ')'; $miss[$k] = ($miss[$k] ?? 0) + 1;
    }
    arsort($miss);
    // ── brief 01 step 4 ──
    $ids = array_flip(array_column($users, 'id'));
    $activeDays = []; $sess = 0; $sweptS = 0;
    if ($has('game_days')) {
        foreach ($q('SELECT user_id, trading_day, trades_count, review_done, is_swept FROM game_days WHERE trades_count > 0 OR review_done = 1') as $r) {
            if (!isset($ids[$r['user_id']])) continue;
            $activeDays[$r['user_id']][] = $r['trading_day'];
            if ((int) $r['trades_count'] > 0 && $r['trading_day'] > gmdate('Y-m-d', $now - 30 * $day)) { $sess++; if ((int) $r['is_swept'] === 1) $sweptS++; }
        }
    }
    $addD = fn(string $d, int $n) => (new DateTimeImmutable($d . ' 12:00', $ny))->modify(($n >= 0 ? '+' : '') . $n . ' days')->format('Y-m-d');
    $today = $nyDay($now);
    $retention = function (int $from, int $to) use ($users, $activeDays, $addD, $today, $rate) {   // active (trade or review) during days from..to
        $n = 0; $k = 0;
        foreach ($users as $u) {
            if ($addD($u['d0'], $to) >= $today) continue;   // the window is not over yet
            $n++; $a = $addD($u['d0'], $from); $b = $addD($u['d0'], $to);
            foreach ($activeDays[$u['id']] ?? [] as $d) if ($d >= $a && $d <= $b) { $k++; break; }
        }
        return ['pct' => $rate($k, $n), 'of' => $n];
    };
    $d0n = 0; $d0k = 0; $ft = [];
    foreach ($users as $u) {
        if (isset($first[$u['id']])) $ft[] = max(0, $first[$u['id']] - $u['ts']);
        if ($u['d0'] >= $today) continue;   // signed up today: the day is not over
        $d0n++; if (isset($first[$u['id']]) && $nyDay($first[$u['id']]) === $u['d0']) $d0k++;
    }
    sort($ft);
    $brief = [
        'filters' => ['cohort' => $fc, 'source' => $fs, 'weeks' => array_slice($weeks, 0, 16, true), 'sources' => $sources, 'traders' => count($users), 'of' => count($all)],
        'first_trade_median_min' => $ft ? (int) round($ft[intdiv(count($ft), 2)] / 60) : null, 'first_trade_of' => count($ft),
        'activation_day0' => ['pct' => $rate($d0k, $d0n), 'of' => $d0n],
        'retention_d7' => $retention(7, 13), 'retention_d30' => $retention(30, 36),
        'swept_sessions_30d' => ['pct' => $rate($sweptS, $sess), 'of' => $sess],
    ];
    if ($has('client_errors')) {   // grouped by message, last 30 days
        $g = [];
        foreach ($q('SELECT user_id, msg, src, line, page, ua, ver, created_at FROM client_errors WHERE created_at > ? ORDER BY created_at', [$now - 30 * $day]) as $r) {
            $k = (string) $r['msg']; $x = $g[$k] ?? ['msg' => $k, 'n' => 0, 'users' => [], 'last' => 0, 'pages' => [], 'browsers' => [], 'versions' => [], 'where' => ''];
            $x['n']++; $x['users'][(string) $r['user_id']] = 1; $x['last'] = max($x['last'], (int) $r['created_at']);
            if ($r['page'] !== '') $x['pages'][$r['page']] = 1;
            $x['browsers'][sweep_browser((string) $r['ua'])] = 1; if ($r['ver'] !== '') $x['versions'][$r['ver']] = 1;
            if ($r['src'] !== '') $x['where'] = $r['src'] . ':' . (int) $r['line'];
            $g[$k] = $x;
        }
        $g = array_map(fn($x) => ['msg' => $x['msg'], 'n' => $x['n'], 'traders' => count($x['users']), 'last' => gmdate('c', $x['last']), 'pages' => array_keys($x['pages']),
            'browsers' => array_keys($x['browsers']), 'versions' => array_keys($x['versions']), 'where' => $x['where']], array_values($g));
        usort($g, fn($a, $b) => [$b['traders'], $b['n']] <=> [$a['traders'], $a['n']]);
        $errs['groups_30d'] = array_slice($g, 0, 20);
    }
    return [
        'generated_at' => gmdate('c'), 'users' => count($users), 'brief' => $brief,
        'signups' => ['d7' => count(array_filter($users, fn($u) => $now - $u['ts'] <= 7 * $day)), 'd30' => count(array_filter($users, fn($u) => $now - $u['ts'] <= 30 * $day)), 'by_source_30d' => array_slice($src, 0, 8, true)],
        'north_star' => $north, 'active_7d' => $active7,
        'first_trade' => (function () use ($users, $first) {   // time from sign-up to the first trade (median), and how many log it on day 1
            $d = []; $d1 = 0; $n = 0;
            foreach ($users as $u) { $n++; if (!isset($first[$u['id']])) continue; $x = max(0, $first[$u['id']] - $u['ts']); $d[] = $x; if ($x <= 86400) $d1++; }
            sort($d); $m = $d ? $d[intdiv(count($d), 2)] : null;
            return ['median_min' => $m === null ? null : round($m / 60), 'day1_pct' => $n ? round($d1 / $n * 100) : 0, 'of' => $n];
        })(),
        'activation_24h' => ['pct' => $rate($act, $actN), 'of' => $actN], 'aha_7d' => ['pct' => $rate($aha, $ahaN), 'of' => $ahaN], 'retention_w2' => ['pct' => $rate($w2, $w2N), 'of' => $w2N],
        'trade_methods_30d' => $methods, 'search_misses_30d' => array_slice($miss, 0, 20, true), 'ai' => $ai, 'errors' => $errs, 'revenue' => $rev,
        'presets' => (function () { require_once dirname(__DIR__) . '/presets/presets-lib.php'; $c = pr_current(); return ['version' => $c['version'] ?? '', 'checked_at' => $c['checked_at'] ?? null, 'origin' => $c['origin'] ?? '', 'status' => pr_status()]; })(),
    ];
}

/** « Safari iOS 18 », « Chrome Android », « Firefox macOS »: enough to group errors, nothing personal */
function sweep_browser(string $ua): string
{
    $os = preg_match('/iPhone|iPad|iPod/', $ua) ? 'iOS' : (stripos($ua, 'Android') !== false ? 'Android' : (stripos($ua, 'Mac OS X') !== false ? 'macOS' : (stripos($ua, 'Windows') !== false ? 'Windows' : (stripos($ua, 'Linux') !== false ? 'Linux' : '?'))));
    $b = preg_match('/Edg\//', $ua) ? 'Edge' : (preg_match('/CriOS|Chrome\//', $ua) ? 'Chrome' : (preg_match('/FxiOS|Firefox\//', $ua) ? 'Firefox' : (stripos($ua, 'Safari') !== false ? 'Safari' : '?')));
    $v = $os === 'iOS' && preg_match('/OS (\d+)_/', $ua, $m) ? ' ' . $m[1] : '';
    return "$b $os$v";
}
