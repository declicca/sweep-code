<?php
declare(strict_types=1);
/**
 * Sweep — admin indicators (brief 01 step 4), on a throwaway SQLite database (never the live one):
 *   php tests/metrics_test.php
 * Known traders, hand-computed numbers: activation on the sign-up day, retention D7 / D30 (a trade or a review), swept
 * sessions, median sign-up → first trade, the cohort and source filters, JS errors grouped with the traders affected.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-metrics-' . bin2hex(random_bytes(4)); mkdir($tmp);
$GLOBALS['DATA'] = $tmp;   // the presets block reads its files there (nothing written to the app)
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, created_at TEXT, utm_source TEXT, utm_campaign TEXT, is_internal INT DEFAULT 0, disabled INT DEFAULT 0, found_via TEXT)');
$pdo->exec('CREATE TABLE game_analytics (user_id TEXT, event TEXT, created_at INT, meta_json TEXT)');
$pdo->exec('CREATE TABLE game_days (user_id TEXT, trading_day TEXT, trades_count INT DEFAULT 0, review_done INT DEFAULT 0, is_swept INT DEFAULT 0, activity INT DEFAULT 0)');
$pdo->exec('CREATE TABLE client_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, msg TEXT, src TEXT, line INT, page TEXT, ua TEXT, ver TEXT, created_at INT NOT NULL)');
require $app . '/ops/metrics.php';

$ny = new DateTimeZone('America/New_York'); $now = time(); $D = 86400;
$at = fn(int $daysAgo) => (new DateTimeImmutable('today 10:00', $ny))->modify("-$daysAgo days")->getTimestamp();   // 10:00 New York, n days ago
$day = fn(int $ts) => (new DateTimeImmutable('@' . $ts))->setTimezone($ny)->format('Y-m-d');
$user = fn(string $id, int $ts, string $via, int $internal = 0) => $pdo->prepare('INSERT INTO users (id, created_at, found_via, is_internal) VALUES (?, ?, ?, ?)')->execute([$id, gmdate('Y-m-d H:i:s', $ts), $via, $internal]);
$trade = fn(string $id, int $ts) => $pdo->prepare("INSERT INTO game_analytics VALUES (?, 'trade_logged', ?, '{}')")->execute([$id, $ts]);
$gd = fn(string $id, string $d, int $trades, int $review, int $swept) => $pdo->prepare('INSERT INTO game_days VALUES (?, ?, ?, ?, ?, 1)')->execute([$id, $d, $trades, $review, $swept]);
$err = fn(string $id, string $msg, string $ua, int $ts) => $pdo->prepare("INSERT INTO client_errors (user_id, msg, src, line, page, ua, ver, created_at) VALUES (?, ?, 'app.js', 12, '#dashboard', ?, 'app.abc', ?)")->execute([$id, $msg, $ua, $ts]);

$t1 = $at(20); $t2 = $at(40); $t3 = $at(40); $t4 = time();
$user('u1', $t1, 'tiktok'); $user('u2', $t2, 'friend'); $user('u3', $t3, 'tiktok'); $user('u4', $t4, 'tiktok'); $user('staff', $at(40), 'friend', 1);
$trade('u1', $t1 + 3600);                 // first trade 1 h after signing up, the same day
$trade('u2', $t2 + 2 * $D);               // first trade 2 days later
$trade('staff', $at(40) + 60);            // internal: never counted
$d1 = $day($t1); $d2 = $day($t2);
$gd('u1', $day($t1 + 8 * $D), 2, 1, 1);   // u1: day 8, trades, swept
$gd('u1', $day($t1 + 10 * $D), 1, 0, 0);  // u1: day 10, trades, not swept
$gd('u2', $day($t2 + 31 * $D), 0, 1, 0);  // u2: day 31, a review only (active, no trade)
$ios = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1';
$win = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36';
$err('u1', 'A is undefined', $ios, $now - 3600); $err('u1', 'A is undefined', $ios, $now - 1800); $err('u2', 'A is undefined', $win, $now - 600); $err('u3', 'B failed', $win, $now - 60);
$err('u1', 'old error', $ios, $now - 40 * $D);   // older than 30 days: not listed

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };

$m = sweep_metrics($pdo, $app); $b = $m['brief'];
$ok($b['filters']['traders'] === 4 && $b['filters']['of'] === 4, "4 traders (the internal one is left out): {$b['filters']['traders']}");
$ok($b['activation_day0'] === ['pct' => 33, 'of' => 3], 'activation: 1 of 3 logs a trade on the sign-up day (today\'s sign-up waits): ' . json_encode($b['activation_day0']));
$ok($b['retention_d7'] === ['pct' => 33, 'of' => 3], 'retention D7: 1 of 3 active during days 7-13: ' . json_encode($b['retention_d7']));
$ok($b['retention_d30'] === ['pct' => 50, 'of' => 2], 'retention D30: 1 of 2 (a review counts), only traders whose window is over: ' . json_encode($b['retention_d30']));
$ok($b['swept_sessions_30d'] === ['pct' => 50, 'of' => 2], 'swept: 1 of 2 sessions with trades (a review-only day is not a session with trades): ' . json_encode($b['swept_sessions_30d']));
$ok($b['first_trade_median_min'] === 2880 && $b['first_trade_of'] === 2, "median sign-up → first trade: 2 days ({$b['first_trade_median_min']} min)");
$ok(($b['filters']['sources']['tiktok'] ?? 0) === 3 && ($b['filters']['sources']['friend'] ?? 0) === 1, 'sources: tiktok 3, friend 1: ' . json_encode($b['filters']['sources']));
$wk = (new DateTimeImmutable($d1 . ' 12:00', $ny))->modify('monday this week')->format('Y-m-d');
$ok(isset($b['filters']['weeks'][$wk]), "the sign-up week of u1 ($wk) is offered");

$t = sweep_metrics($pdo, $app, ['source' => 'tiktok'])['brief'];
$ok($t['filters']['traders'] === 3 && $t['activation_day0'] === ['pct' => 50, 'of' => 2] && $t['retention_d30'] === ['pct' => 0, 'of' => 1], 'source « tiktok »: 3 traders, activation 1 of 2, D30 0 of 1');
$c = sweep_metrics($pdo, $app, ['cohort' => $wk])['brief'];
$ok($c['filters']['traders'] >= 1 && $c['activation_day0']['pct'] === 100, "cohort $wk: u1, activation 100 %: " . json_encode($c['activation_day0']));

$g = $m['errors']['groups_30d'] ?? [];
$ok(count($g) === 2, 'errors of the last 30 days, grouped by message: ' . count($g));
$ok(($g[0]['msg'] ?? '') === 'A is undefined' && $g[0]['traders'] === 2 && $g[0]['n'] === 3, 'first: « A is undefined », 2 traders, 3 times');
$ok(in_array('Safari iOS 17', $g[0]['browsers'] ?? [], true) && in_array('Chrome Windows', $g[0]['browsers'] ?? [], true) && ($g[0]['pages'] ?? []) === ['#dashboard'] && ($g[0]['versions'] ?? []) === ['app.abc'],
    'browsers, page and version of the first: ' . json_encode([$g[0]['browsers'] ?? [], $g[0]['pages'] ?? [], $g[0]['versions'] ?? []]));
$ok(!array_filter($g, fn($x) => $x['msg'] === 'old error'), 'an error older than 30 days is not listed');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
