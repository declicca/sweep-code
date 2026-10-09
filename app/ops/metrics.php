<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — admin dashboard numbers (Settings → Admin). Everything comes from Sweep's own database.
 * North star: traders who swept 3+ days in the last 7 days. Activation: first trade within 24 h of sign-up.
 * « Aha »: first swept day within 7 days. Week-2 retention: 3+ swept days during days 8-14.
 */
function sweep_metrics(PDO $pdo, string $app): array
{
    $q = function (string $sql, array $a = []) use ($pdo) { $s = $pdo->prepare($sql); $s->execute($a); return $s; };
    $now = time(); $day = 86400;
    $has = fn(string $t) => (bool) $q("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", [$t])->fetchColumn();
    $users = $q('SELECT id, created_at, utm_source, utm_campaign, is_internal FROM users WHERE disabled = 0')->fetchAll(PDO::FETCH_ASSOC);
    $users = array_values(array_filter($users, fn($u) => !(int) ($u['is_internal'] ?? 0)));
    foreach ($users as &$u) $u['ts'] = strtotime((string) $u['created_at']) ?: 0; unset($u);
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
    return [
        'generated_at' => gmdate('c'), 'users' => count($users),
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
