<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — how the app is used (27 Oct.), for Admin › « Export for Claude ». The app sends, every few minutes and when it
 * is hidden, how many times each page (« p:dashboard ») and each sheet (« s:nav-am-shot ») was opened and the seconds it
 * was in front of the trader, with the device (phone / tablet / desktop, « -app » once installed), the language and the
 * theme. Counted per New York day, trader and key: never a trade, an amount, a text typed or an address.
 *  - usage_daily: day, user_id, k, device, opens, secs (one row per day × trader × key × device)
 *  - usage_env: the last device, installed or not, language and theme of each trader
 * Kept 180 days.
 */
const SWEEP_USAGE_KEYS = 60;      // keys per report
const SWEEP_USAGE_DAYS = 180;

function sweep_usage_schema(PDO $pdo): void
{
    $pdo->exec('CREATE TABLE IF NOT EXISTS usage_daily (day VARCHAR(10) NOT NULL, user_id VARCHAR(120) NOT NULL, k VARCHAR(44) NOT NULL, device VARCHAR(16) NOT NULL,
        opens INTEGER NOT NULL DEFAULT 0, secs INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, user_id, k, device))');
    $pdo->exec('CREATE TABLE IF NOT EXISTS usage_env (user_id VARCHAR(120) NOT NULL PRIMARY KEY, device VARCHAR(16) NOT NULL, lang VARCHAR(4) NOT NULL, theme VARCHAR(8) NOT NULL, seen_at INTEGER NOT NULL)');
}

/** One report from the app: ['dev' => 'phone', 'app' => true, 'lang' => 'fr', 'theme' => 'dark', 'p' => ['p:dashboard' => [opens, secs], …]]. Returns the keys kept. */
function sweep_usage_record(PDO $pdo, string $uid, array $b, int $now): int
{
    sweep_usage_schema($pdo);
    $dev = in_array($b['dev'] ?? '', ['phone', 'tablet', 'desktop'], true) ? $b['dev'] : 'desktop';
    if (!empty($b['app'])) $dev .= '-app';
    $lang = in_array($b['lang'] ?? '', ['en', 'fr', 'es'], true) ? $b['lang'] : 'en';
    $theme = in_array($b['theme'] ?? '', ['light', 'dark'], true) ? $b['theme'] : 'light';
    $day = (new DateTimeImmutable('@' . $now))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d');
    $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $up = $pdo->prepare($my
        ? 'INSERT INTO usage_daily (day, user_id, k, device, opens, secs) VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE opens = opens + VALUES(opens), secs = secs + VALUES(secs)'
        : 'INSERT INTO usage_daily (day, user_id, k, device, opens, secs) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (day, user_id, k, device) DO UPDATE SET opens = opens + excluded.opens, secs = secs + excluded.secs');
    $n = 0;
    foreach ((array) ($b['p'] ?? []) as $k => $v) {
        if ($n >= SWEEP_USAGE_KEYS || !is_string($k) || !preg_match('/^[ps]:[a-z0-9_-]{1,40}$/', $k) || !is_array($v)) continue;
        $o = max(0, min(500, (int) ($v[0] ?? 0))); $s = max(0, min(86400, (int) ($v[1] ?? 0)));
        if (!$o && !$s) continue;
        $up->execute([$day, $uid, $k, $dev, $o, $s]); $n++;
    }
    $env = $pdo->prepare($my
        ? 'INSERT INTO usage_env (user_id, device, lang, theme, seen_at) VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE device = VALUES(device), lang = VALUES(lang), theme = VALUES(theme), seen_at = VALUES(seen_at)'
        : 'INSERT INTO usage_env (user_id, device, lang, theme, seen_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT (user_id) DO UPDATE SET device = excluded.device, lang = excluded.lang, theme = excluded.theme, seen_at = excluded.seen_at');
    $env->execute([$uid, $dev, $lang, $theme, $now]);
    if (random_int(1, 200) === 1) $pdo->prepare('DELETE FROM usage_daily WHERE day < ?')->execute([gmdate('Y-m-d', $now - SWEEP_USAGE_DAYS * 86400)]);
    return $n;
}

/**
 * The last $days days, for the traders of $real (ids => true; Mateo's and test accounts aside): per key, the traders who
 * opened it, the opens and the median minutes a day per trader; the devices of the last 30 days; the languages and themes.
 */
function sweep_usage_summary(PDO $pdo, int $now, array $real, int $days = 30): array
{
    sweep_usage_schema($pdo);
    $since = (new DateTimeImmutable('@' . ($now - $days * 86400)))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d');
    $st = $pdo->prepare('SELECT day, user_id, k, device, opens, secs FROM usage_daily WHERE day > ?'); $st->execute([$since]);
    $keys = []; $who = []; $dev = [];
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) {
        if (!isset($real[$r['user_id']])) continue;
        $who[$r['user_id']] = true;
        $x = &$keys[$r['k']]; $x ??= ['users' => [], 'opens' => 0, 'secs' => 0, 'days' => [], 'phone' => 0, 'desktop' => 0];
        $x['users'][$r['user_id']] = true; $x['opens'] += (int) $r['opens']; $x['secs'] += (int) $r['secs'];
        $x['days'][$r['user_id'] . '|' . $r['day']] = ($x['days'][$r['user_id'] . '|' . $r['day']] ?? 0) + (int) $r['secs'];
        $x[str_starts_with((string) $r['device'], 'desktop') ? 'desktop' : 'phone'] += (int) $r['opens'];
        unset($x);
        $dev[$r['device']][$r['user_id']] = true;
    }
    $n = count($who); $out = [];
    foreach ($keys as $k => $x) {
        $d = array_values($x['days']); sort($d);
        $out[$k] = ['traders' => count($x['users']), 'pct' => $n ? (int) round(count($x['users']) / $n * 100) : 0, 'opens' => $x['opens'],
            'minutes' => (int) round($x['secs'] / 60), 'median_min_day' => $d ? round($d[intdiv(count($d), 2)] / 60, 1) : 0.0, 'phone' => $x['phone'], 'desktop' => $x['desktop']];
    }
    uasort($out, fn($a, $b) => [$b['traders'], $b['opens']] <=> [$a['traders'], $a['opens']]);
    $env = ['lang' => [], 'theme' => [], 'device' => []];
    foreach ($pdo->query('SELECT user_id, device, lang, theme FROM usage_env')->fetchAll(PDO::FETCH_ASSOC) as $r) {
        if (!isset($real[$r['user_id']])) continue;
        foreach (['lang', 'theme', 'device'] as $c) $env[$c][$r[$c]] = ($env[$c][$r[$c]] ?? 0) + 1;
    }
    foreach ($env as &$e) arsort($e); unset($e);
    $devices = array_map('count', $dev); arsort($devices);
    return ['days' => $days, 'traders' => $n, 'keys' => $out, 'devices_30d' => $devices, 'env' => $env];
}
