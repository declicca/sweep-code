<?php
declare(strict_types=1);
/**
 * Sweep — admin indicators (brief 01 step 4), on a throwaway SQLite database (never the live one):
 *   php tests/metrics_test.php
 * Known traders, hand-computed numbers: activation on the sign-up day, retention D7 / D30 (a trade or a review), swept
 * sessions, median sign-up → first trade, the cohort and source filters, JS errors grouped with the traders affected,
 * the start step by step (brief 03 step 1), closed days and Friday recaps opened (SWEEP.md, step 0); the sign-ups by time of day,
 * the return on the next trading day and the risk allowed seen on the session of the sign-up (brief activation, step C); the first
 * plan screen by screen, by start and device, and in « Export for Claude » (brief « premier plan », step 1).
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
// the journey's baseline (SWEEP.md, step 0): closed days and Friday recaps opened
$ok($b['closed_sessions_30d'] === ['pct' => 50, 'of' => 2], 'closed days: 1 of 2 sessions with trades has its review done: ' . json_encode($b['closed_sessions_30d']));
$mon = fn(string $d) => (new DateTimeImmutable($d . ' 12:00', $ny))->modify('monday this week')->format('Y-m-d');
$w8 = $mon($day($t1 + 8 * $D)); $w10 = $mon($day($t1 + 10 * $D)); $nW = $w8 === $w10 ? 1 : 2;
$pdo->prepare("INSERT INTO game_analytics VALUES ('u1', 'weekly_opened', ?, ?)")->execute([$now - $D, json_encode(['week' => $w8])]);
$pdo->prepare("INSERT INTO game_analytics VALUES ('u2', 'weekly_opened', ?, ?)")->execute([$now - $D, json_encode(['week' => $w8])]);   // a week without a trade of u2: not counted
$pdo->prepare("INSERT INTO game_analytics VALUES ('u1', 'weekly_opened', ?, ?)")->execute([$now - $D, json_encode(['week' => $w8])]);   // opened twice: once
$wo = sweep_metrics($pdo, $app)['brief']['weekly_opened_8w'];
$ok($wo === ['pct' => (int) round(100 / $nW), 'of' => $nW], "Friday recaps opened: 1 of the $nW weeks with a trade (the current week and a week without a trade left out): " . json_encode($wo));
$gd('u1', $day(time()), 1, 0, 0);   // a trade this week: the week is not over, not counted
$ok(sweep_metrics($pdo, $app)['brief']['weekly_opened_8w']['of'] === $nW, 'the current week is not counted yet');
$pdo->exec("DELETE FROM game_days WHERE user_id = 'u1' AND trading_day = '" . $day(time()) . "'");
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

// brief 03 step 1: the start, step by step (signed up → first name → first account → first plan → first trade)
$s0 = sweep_metrics($pdo, $app)['brief']['start'];
$ok($s0['first_name']['n'] === 0 && $s0['account']['n'] === 0 && $s0['trade']['n'] === 2, 'start: no first_name column nor documents table yet → 0, no error; trades 2: ' . json_encode($s0));
$pdo->exec('ALTER TABLE users ADD COLUMN first_name TEXT');
$pdo->exec('CREATE TABLE documents (user_id TEXT, collection TEXT, id TEXT, data TEXT, created_at TEXT, updated_at TEXT)');
$pdo->exec("UPDATE users SET first_name = 'Léa' WHERE id IN ('u1', 'u2', 'u4', 'staff')");
$doc = fn(string $u, string $coll, string $id, string $data, int $ts) => $pdo->prepare('INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?)')->execute([$u, $coll, $id, $data, gmdate('Y-m-d H:i:s', $ts), gmdate('Y-m-d H:i:s', $ts)]);
$doc('u1', 'accounts', 'a1', '{"name":"Apex"}', $t1 + 120);                // 2 min after signing up
$doc('u1', 'accounts', 'a2', '{"name":"Topstep"}', $t1 + 9000);            // a later account: the first one counts
$doc('u2', 'accounts', 'a3', '{"name":"Lucid"}', $t2 + 600);               // 10 min
$doc('u3', 'accounts', 'd1', '{"name":"Sample","demo":true}', $t3 + 60);   // sample data: not an account
$doc('u1', 'journals', 'j1', '{"pre":{"bias":"bullish","max_loss":"1000","saved_at":' . ($t1 + 300) . '}}', $t1 + 300);   // the first plan 5 min after signing up (even for the next session)
$doc('u1', 'journals', 'j2', '{"pre":{"bias":"neutral","saved_at":' . ($t1 + 2 * $D) . '}}', $t1 + 2 * $D);
$doc('u2', 'journals', 'j3', '{"post":{"lesson":"x"}}', $t2 + 60);                        // a review, no plan: not a plan
$doc('u3', 'journals', 'j4', '{"pre":{"bias":"bearish"},"demo":true}', $t3 + 60);        // sample data: not a plan
$s = sweep_metrics($pdo, $app)['brief']['start'];
$ok($s['signed_up'] === 4 && $s['first_name']['n'] === 3, 'start: 4 signed up, 3 with a first name (the internal trader left out): ' . json_encode([$s['signed_up'], $s['first_name']]));
$ok($s['account'] === ['n' => 2, 'median_min' => 10], 'first account: u1 (2 min) and u2 (10 min), the sample-data account left out: ' . json_encode($s['account']));
$ok($s['plan'] === ['n' => 1, 'median_min' => 5] && $s['trade'] === ['n' => 2, 'median_min' => 2880], 'first plan: u1 at 5 min (a review is not a plan); first trade: 2, median 2 days: ' . json_encode([$s['plan'], $s['trade']]));
$st = sweep_metrics($pdo, $app, ['source' => 'tiktok'])['brief']['start'];
$ok($st['signed_up'] === 3 && $st['first_name']['n'] === 2 && $st['account'] === ['n' => 1, 'median_min' => 2], 'source « tiktok »: 3 signed up, 2 first names, 1 account at 2 min: ' . json_encode($st));

// the game's use over 30 days (brief 02 part 11): active traders = a trade, a plan or a review on a session of the last 30 days
$user('ga', $at(50), 'x'); $user('gb', $at(50), 'x'); $user('gc', $at(50), 'x'); $user('gold', $at(90), 'x'); $user('gstaff', $at(50), 'x', 1);
foreach (['ga', 'gb', 'gc', 'gstaff'] as $u) $gd($u, $day($at(3)), 1, 1, 0);
$gd('gold', $day($at(60)), 1, 1, 0);   // not active for 30 days
$ev = fn(string $u, string $e, int $ts) => $pdo->prepare('INSERT INTO game_analytics VALUES (?, ?, ?, ?)')->execute([$u, $e, $ts, '{}']);
$ev('ga', 'share_card_shared', $at(2)); $ev('ga', 'share_card_created', $at(2)); $ev('gstaff', 'share_card_shared', $at(2)); $ev('gold', 'share_card_shared', $at(2));
$ev('gb', 'chest_opened', $at(40)); $ev('gc', 'mission_completed', $at(5)); $ev('ga', 'mission_completed', $at(6));
$g = sweep_metrics($pdo, $app)['game'];
$n = $g['active_30d'];
$ok($n >= 3 && $g['used']['share']['n'] === 1 && $g['used']['share']['pct'] === (int) round(100 / $n) && $g['reached']['mission']['n'] === 2
    && array_keys($g['used']) === ['share', 'weekly_recap', 'weekly_review'] && array_keys($g['reached']) === ['mission', 'badge', 'swept', 'streak3', 'freeze', 'map', 'wow'],
    "the game's use: of the $n active traders, 1 shared a card (Mateo's account and an inactive trader aside, twice counted once), 2 missions; nothing of what was removed on 10 Nov. (chest, season, league, crew, Wrapped, theme, Discord, boss, level…) is listed: " . json_encode([$g['used']['share'], array_keys($g['used']), array_keys($g['reached'])]));

// brief activation of 27 Oct., step C, on a second throwaway database: when they sign up, the return on the next trading day,
// the risk allowed seen on the session of the sign-up. Tuesday 1 Sept. 2026, New York time.
$p2 = new PDO('sqlite:' . $tmp . '/c.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$p2->exec('CREATE TABLE users (id TEXT PRIMARY KEY, created_at TEXT, utm_source TEXT, utm_campaign TEXT, is_internal INT DEFAULT 0, disabled INT DEFAULT 0, found_via TEXT, first_name TEXT, last_login TEXT)');
$p2->exec('CREATE TABLE game_analytics (user_id TEXT, event TEXT, created_at INT, meta_json TEXT)');
$p2->exec('CREATE TABLE game_days (user_id TEXT, trading_day TEXT, trades_count INT DEFAULT 0, review_done INT DEFAULT 0, is_swept INT DEFAULT 0, activity INT DEFAULT 0)');
$p2->exec('CREATE TABLE documents (user_id TEXT, collection TEXT, id TEXT, data TEXT, created_at TEXT, updated_at TEXT)');
$et = fn(string $s) => (new DateTimeImmutable($s, $ny))->getTimestamp();
$u2 = fn(string $id, int $ts, int $internal = 0, ?int $login = null) => $p2->prepare('INSERT INTO users (id, created_at, found_via, is_internal, last_login) VALUES (?, ?, ?, ?, ?)')->execute([$id, gmdate('Y-m-d H:i:s', $ts), 'x', $internal, $login ? gmdate('Y-m-d\TH:i:s\Z', $login) : null]);
$u2('s1', $et('2026-09-01 10:00'));                                  // session (Tuesday 10:00)
$u2('s2', $et('2026-09-01 20:00'));                                  // before the open (Tuesday evening 20:00: Wednesday's session)
$u2('s3', $et('2026-09-04 17:30'), 0, $et('2026-09-07 10:00'));      // weekend (Friday 17:30); signed in again on Monday
$u2('s4', $et('2026-09-02 17:30'));                                  // the market closed (Wednesday 17:30: closes at 17:00, reopens at 18:00)
$u2('s5', $et('2026-09-01 10:00'), 1);                               // Mateo's: left out
$p2->prepare("INSERT INTO game_analytics VALUES ('s1', 'trade_logged', ?, '{}')")->execute([$et('2026-09-01 11:00')]);   // s1: a trade the same session
$p2->prepare("INSERT INTO game_days VALUES ('s1', '2026-09-02', 0, 1, 0, 1)")->execute();                                // s1: back on Wednesday (a review)
$p2->prepare("INSERT INTO documents VALUES ('s2', 'journals', 'j', ?, ?, ?)")->execute(['{"pre":{"bias":"bullish","max_loss":"500","saved_at":' . $et('2026-09-02 08:00') . '}}', '2026-09-02 12:00:00', '2026-09-02 12:00:00']);   // s2: the plan before Wednesday's open
$b2 = sweep_metrics($p2, $app)['brief'];
$sl = array_map(fn($x) => [$x['n'], $x['day0_pct']], $b2['signup_slots']);
$ok($sl === ['before' => [1, 100], 'session' => [1, 100], 'evening' => [1, 0], 'weekend' => [1, 0]], 'when they sign up: one trader in each slot, a first plan or trade on that session for « before » and « session »: ' . json_encode($sl));
$ok($b2['return_d1'] === ['pct' => 50, 'of' => 4], 'back on the next trading day: s1 (a review on Wednesday), s3 (signed in on Monday after a Friday-evening sign-up); not s2 nor s4: ' . json_encode($b2['return_d1']));
$ok($b2['risk_seen_day0'] === ['pct' => 50, 'of' => 4], 'the risk allowed seen on the session of the sign-up: s1 (a trade), s2 (the plan before the open of its session): ' . json_encode($b2['risk_seen_day0']));

// brief « pertes oubliées », step 1: a complete journal, on a third throwaway database (7 and 30 days)
$p3 = new PDO('sqlite:' . $tmp . '/j.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$p3->exec('CREATE TABLE users (id TEXT PRIMARY KEY, created_at TEXT, utm_source TEXT, utm_campaign TEXT, is_internal INT DEFAULT 0, disabled INT DEFAULT 0, found_via TEXT, first_name TEXT, last_login TEXT)');
$p3->exec('CREATE TABLE documents (user_id TEXT, collection TEXT, id TEXT, data TEXT, created_at TEXT, updated_at TEXT)');
foreach (['j1' => 0, 'j2' => 0, 'j3' => 0, 'jx' => 1] as $id => $int) $p3->prepare('INSERT INTO users (id, created_at, is_internal) VALUES (?, ?, ?)')->execute([$id, '2026-09-01 12:00:00', $int]);
$jd = fn(int $ago) => (new DateTimeImmutable('today 12:00', $ny))->modify("-$ago days")->format('Y-m-d');
$tr = function (string $u, string $id, int $ago, int $c, array $more = []) use ($p3, $jd) { $p3->prepare("INSERT INTO documents VALUES (?, 'trades', ?, ?, '', '')")->execute([$u, $id, json_encode(array_merge(['date' => $jd($ago), 'pnl_c' => $c, 'fees_c' => 0], $more))]); };
// j1: 25 trades over 5 days, 22 winners, the 3 losers on one day; a winner copied on a 2nd account counts once
for ($i = 0; $i < 25; $i++) $tr('j1', "j1-$i", 1 + intdiv($i, 5), $i < 3 ? -5000 : 8000);
$tr('j1', 'j1-copy', 5, 8000, ['copy_group' => 'g1']); $tr('j1', 'j1-copy2', 5, 8000, ['copy_group' => 'g1']);   // (the 25th day-5 trade replaced below)
$p3->exec("DELETE FROM documents WHERE id = 'j1-24'");
// j2: 20 trades over 4 days, 14 winners, a loser every day
for ($i = 0; $i < 20; $i++) $tr('j2', "j2-$i", 1 + intdiv($i, 5), $i % 5 < 2 && $i < 10 ? -3000 : ($i % 5 === 0 ? -3000 : 6000));
// j3: 5 trades in a day, 3 losers (under 20 trades: not in the first figure); a sample trade and an old loser (20 days ago)
for ($i = 0; $i < 5; $i++) $tr('j3', "j3-$i", 2, $i < 3 ? -2000 : 4000);
$tr('j3', 'j3-demo', 2, 9000, ['demo' => true]); $tr('j3', 'j3-old', 20, -1000);
for ($i = 0; $i < 30; $i++) $tr('jx', "jx-$i", 1, 5000);   // Mateo's: left out
// step 2: the days closed on the platform's balance (journal.post.bal) and a « Trades not detailed » line, half detailed since
$jn = fn(string $u, int $ago, array $gaps) => $p3->prepare("INSERT INTO documents VALUES (?, 'journals', ?, ?, '', '')")->execute([$u, $jd($ago), json_encode(['post' => ['reviewed_at' => 'x', 'bal' => array_map(fn($g) => ['acc' => 'a', 'gap_c' => $g], $gaps)]])]);
$jn('j1', 1, [0]); $jn('j1', 2, [-34000]); $jn('j2', 3, [-10000, 5000]); $jn('j3', 20, [-2000]); $jn('jx', 1, [-9000]);   // (Mateo's: left out)
$tr('j3', 'j3-line', 2, -17000, ['untracked' => ['gap_c' => -34000, 'detailed_c' => -17000]]);   // j3: 6 trades, 4 losers on day 2
$jm = sweep_metrics($p3, $app)['journal'];
$w2 = array_sum(array_map(fn($i) => ($i % 5 < 2 && $i < 10) || $i % 5 === 0 ? 0 : 1, range(0, 19)));
$ok($jm['d7']['high_win_20'] === ['pct' => 50, 'of' => 2], "7 days: 1 of the 2 traders with 20+ trades over 80 % winners (j1: 22/25; j2: $w2/20): " . json_encode($jm['d7']['high_win_20']));
$l7 = 3 + (20 - $w2) + 4;
$ok($jm['d7']['losing_trades'] === ['pct' => (int) round($l7 / 51 * 100), 'of' => 51], "7 days: $l7 losing trades of 51 (a copy once, the sample trade and Mateo's left out, the « Trades not detailed » line in): " . json_encode($jm['d7']['losing_trades']));
$ok($jm['d7']['days_without_loss'] === ['pct' => 40, 'of' => 10], '7 days: 4 of the 10 trading days without a loser (j1: 4 of 5, j2: 0 of 4, j3: 0 of 1): ' . json_encode($jm['d7']['days_without_loss']));
$ok($jm['d30']['losing_trades'] === ['pct' => (int) round(($l7 + 1) / 52 * 100), 'of' => 52] && $jm['d30']['days_without_loss'] === ['pct' => 36, 'of' => 11], '30 days: the old loser of j3 too: ' . json_encode([$jm['d30']['losing_trades'], $jm['d30']['days_without_loss']]));

$ok($jm['d7']['gap_days'] === ['pct' => 67, 'of' => 3] && $jm['d7']['gap_total_c'] === 49000, '7 days: 2 of 3 days closed with a gap (j1 day 2, j2 day 3), $490 in all (|−100| + |+50| for j2), Mateo\'s left out: ' . json_encode([$jm['d7']['gap_days'], $jm['d7']['gap_total_c']]));
$ok($jm['d30']['gap_days'] === ['pct' => 75, 'of' => 4] && $jm['d30']['gap_total_c'] === 51000, '30 days: j3\'s old gap too (3 of 4, $510): ' . json_encode([$jm['d30']['gap_days'], $jm['d30']['gap_total_c']]));
// (13 Nov., step 3.1) a gap larger than the account's maximum loss: a balance to check, apart from the total
$p3->prepare("INSERT INTO documents VALUES ('j1', 'accounts', 'big', ?, '', '')")->execute([json_encode(['starting_balance_c' => 5000000, 'rules' => ['dd_c' => 200000]])]);
$p3->prepare("INSERT INTO documents VALUES ('j2', 'accounts', 'plain', ?, '', '')")->execute([json_encode(['starting_balance_c' => 5000000])]);
$p3->prepare("INSERT INTO documents VALUES ('j1', 'journals', ?, ?, '', '')")->execute([$jd(4), json_encode(['post' => ['bal' => [['acc' => 'big', 'gap_c' => 5000000], ['acc' => 'big', 'gap_c' => -150000]]]])]);
$p3->prepare("INSERT INTO documents VALUES ('j2', 'journals', ?, ?, '', '')")->execute([$jd(5), json_encode(['post' => ['bal' => [['acc' => 'plain', 'gap_c' => -500100]]]])]);
$jc = sweep_metrics($p3, $app)['journal']['d7'];
$ok($jc['gap_check'] === ['n' => 2, 'c' => 5500100] && $jc['gap_total_c'] === 49000 + 150000 && $jc['gap_days'] === ['pct' => 60, 'of' => 5],
    'balances to check: a $50,000 gap on an account that can lose $2,000, and $5,001 on a 50K without a rule (10 % of its size) are counted apart (2, $55,001), not in the total ($490 + the $1,500 gap under the limit): ' . json_encode([$jc['gap_check'], $jc['gap_total_c'], $jc['gap_days']]));
$p3->exec("DELETE FROM documents WHERE id IN ('big', 'plain') OR (collection = 'journals' AND id IN ('" . $jd(4) . "', '" . $jd(5) . "'))");
$ok($jm['d7']['gap_detailed'] === ['pct' => 50, 'of' => 1], 'the « Trades not detailed » line: half of its $340 detailed in trades since: ' . json_encode($jm['d7']['gap_detailed']));

// (5 Nov., brief monétisation, étape 1) « 5 trades in 7 days » by week of sign-up: copies once, sample data and later trades aside
$fs = $at(16);
$user('f5a', $fs, 'x'); $user('f5b', $fs, 'x'); $user('f5c', $fs, 'x');
for ($i = 0; $i < 5; $i++) $doc('f5a', 'trades', "t$i", '{"pnl_c":100}', $fs + 3600 * ($i + 1));                          // 5 in its first week
for ($i = 0; $i < 5; $i++) $doc('f5b', 'trades', "c$i", '{"copy_group":"g1"}', $fs + 3600);                              // one trade copied on 5 accounts
for ($i = 0; $i < 4; $i++) $doc('f5b', 'trades', "s$i", '{"demo":true}', $fs + 3600);                                    // sample data
for ($i = 0; $i < 5; $i++) $doc('f5c', 'trades', "l$i", '{}', $fs + 8 * $D + $i);                                        // after its first week
$wk = (new DateTimeImmutable('@' . $fs))->setTimezone($ny)->modify('monday this week')->format('Y-m-d');
$f7 = array_values(array_filter(sweep_metrics($pdo, $app)['five_in_7'] ?? [], fn($r) => $r['week'] === $wk))[0] ?? null;
$ok($f7 !== null && $f7['k'] === 1 && $f7['n'] >= 3 && !$f7['open'], '5 trades in 7 days: the 3 traders of that week, 1 of them (copies once, no sample data, not after day 7) ' . json_encode($f7));

// (7 Nov., brief « premier plan », step 1) the first plan, screen by screen, hand-computed: 3 traders of a week of their own (Tuesday 4 March
// 2025, New York): pA at 10:00 (market open) saves the short form on a computer; pB at 20:00 (market closed) goes through 2 screens of the
// guided plan on a phone, back to the first and on to the second again, then closes it; pC (« More than a year »: active) leaves the page
// on the quick plan, on a phone. Sent as the app sends them (ops/usage.php): a second plan, or another ending of an ended plan, is not kept.
require_once $app . '/ops/usage.php';
$pdo->exec('ALTER TABLE users ADD COLUMN experience TEXT');
$tue = fn(string $hm) => (new DateTimeImmutable('2025-03-04 ' . $hm, $ny))->getTimestamp();
$user('pA', $tue('10:00'), 'x'); $user('pB', $tue('20:00'), 'x'); $user('pC', $tue('20:30'), 'x'); $pdo->exec("UPDATE users SET experience = 'gt1' WHERE id = 'pC'");
$rep = fn(string $u, string $dev, array $fp) => sweep_usage_record($pdo, $u, ['dev' => $dev, 'lang' => 'en', 'theme' => 'dark', 'p' => [], 'fp' => $fp], $tue('22:00'));
$rep('pA', 'desktop', ['id' => 'aaaa1', 'end' => 'saved', 's' => [['form', 40]]]);
$rep('pA', 'desktop', ['id' => 'aaaa2', 'end' => 'closed', 's' => [['express', 5]]]);                                         // a second plan: not kept
$rep('pB', 'phone', ['id' => 'bbbb1', 'end' => 'left', 's' => [['base', 30]]]);                                               // the app hidden a moment…
$rep('pB', 'phone', ['id' => 'bbbb1', 'end' => 'closed', 's' => [['base', 30], ['pos', 50], ['base', 10], ['pos', 20]]]);    // …then closed on screen 2
$rep('pB', 'phone', ['id' => 'bbbb1', 'end' => 'saved', 's' => [['base', 30]]]);                                              // already ended: not kept
$rep('pC', 'phone', ['id' => 'cccc1', 'end' => 'left', 's' => [['express', 20]]]);
$rep('pC', 'phone', ['id' => 'cccc1', 'end' => 'saved', 's' => [['bad screen!', 1]]]);                                        // not a screen name: refused
$fp = sweep_metrics($pdo, $app, ['cohort' => '2025-03-03'])['brief']['first_plan'];
$sc = fn(array $x) => array_map(fn($r) => [$r['screen'], $r['reached'], $r['left'], $r['median_s']], $x['screens']);
$ok($fp['all']['all']['n'] === 3 && $fp['all']['all']['end'] === ['saved' => 1, 'closed' => 1, 'skipped' => 0, 'left' => 1], 'first plan: 3 measured, 1 saved, 1 closed, 1 page left ' . json_encode($fp['all']['all']['end']));
$ok($sc($fp['all']['all']) === [['form', 1, 0, 40], ['express', 1, 1, 20], ['base', 1, 0, 40], ['pos', 1, 1, 70]], 'first plan, every screen: reached, left on it (the last screen, not saved), median seconds (a screen seen twice added up) ' . json_encode($sc($fp['all']['all'])));
$ok($sc($fp['open']['all']) === [['form', 1, 0, 40]] && $sc($fp['closed']['phone']) === [['base', 1, 0, 40], ['pos', 1, 1, 70]] && $sc($fp['active']['phone']) === [['express', 1, 1, 20]], 'first plan by start: market open (pA), market closed (pB), active trader (pC)');
$ok($fp['all']['desktop']['n'] === 1 && $fp['all']['phone']['n'] === 2 && $fp['closed']['desktop']['n'] === 0 && $sc($fp['all']['phone']) === [['express', 1, 1, 20], ['base', 1, 0, 40], ['pos', 1, 1, 70]], 'first plan by device: 1 computer, 2 phones');
$ok(sweep_metrics($pdo, $app, ['cohort' => '2025-03-10'])['brief']['first_plan']['all']['all']['n'] === 0, 'first plan: another week, none measured');
require_once $app . '/ops/report.php';
$md = sweep_full_report($pdo, [], $app, time());
$ok(str_contains($md, 'Le premier plan, écran par écran') && str_contains($md, '| Tous | tous appareils | 3 | 1 | 1 | 0 | 1 |') && str_contains($md, '| Marché fermé | téléphone | Plan guidé : position | 1 | 1 | 70 s |'), 'Export for Claude: the first plan, by start and device');

// (13 Nov., brief « comptes par firme ») accounts by firm, on a fourth throwaway database — every number counted by hand:
//  f1: a Topstep evaluation by its preset (a1), and an archived Topstep account (a2: left out)
//  f2: a funded account whose firm is named « TopstepX » (b1: the catalogue's alias → Topstep), a live account at a firm that is
//      not in the catalogue (b2: other), a personal account with no firm (b3)
//  f3: an Apex account with a profit target and no type stored (c1: an evaluation), and a sample account (left out)
//  fx: Mateo's own Topstep account (internal: left out)
$p4 = new PDO('sqlite:' . $tmp . '/f.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$p4->exec('CREATE TABLE users (id TEXT PRIMARY KEY, created_at TEXT, utm_source TEXT, utm_campaign TEXT, is_internal INT DEFAULT 0, disabled INT DEFAULT 0, found_via TEXT, first_name TEXT, last_login TEXT)');
$p4->exec('CREATE TABLE documents (user_id TEXT, collection TEXT, id TEXT, data TEXT, created_at TEXT, updated_at TEXT)');
foreach (['f1' => 0, 'f2' => 0, 'f3' => 0, 'fx' => 1] as $id => $int) $p4->prepare('INSERT INTO users (id, created_at, is_internal) VALUES (?, ?, ?)')->execute([$id, '2026-09-01 12:00:00', $int]);
$fd = function (string $u, string $col, string $id, array $d) use ($p4) { $p4->prepare("INSERT INTO documents VALUES (?, ?, ?, ?, '', '')")->execute([$u, $col, $id, json_encode($d)]); };
$fd('f1', 'accounts', 'a1', ['preset' => 'topstep|combine|50000', 'firm_id' => 'x1', 'money_type' => 'eval', 'status' => 'active']);
$fd('f1', 'accounts', 'a2', ['preset' => 'topstep|combine|50000', 'firm_id' => 'x1', 'money_type' => 'eval', 'status' => 'archived']);
$fd('f2', 'firms', 'x2', ['name' => 'TopstepX']); $fd('f2', 'firms', 'x3', ['name' => 'Bulenox']);
$fd('f2', 'accounts', 'b1', ['firm_id' => 'x2', 'phase' => 'funded', 'status' => 'active']);
$fd('f2', 'accounts', 'b2', ['firm_id' => 'x3', 'money_type' => 'live', 'status' => 'active']);
$fd('f2', 'accounts', 'b3', ['money_type' => 'personal', 'status' => 'active']);
$fd('f3', 'accounts', 'c1', ['preset' => 'apex|eod|50000', 'rules' => ['target_c' => 300000], 'status' => 'active']);
$fd('f3', 'accounts', 'c9', ['preset' => 'apex|eod|50000', 'demo' => true, 'status' => 'active']);
$fd('fx', 'accounts', 'z1', ['preset' => 'topstep|combine|50000', 'money_type' => 'funded', 'status' => 'active']);
$n4 = 0; $ft = function (string $u, string $acc, int $ago, array $more = []) use ($fd, $jd, &$n4) { $fd($u, 'trades', 't' . (++$n4), array_merge(['account_id' => $acc, 'date' => $jd($ago), 'pnl_c' => 1000], $more)); };
$ft('f1', 'a1', 1); $ft('f1', 'a1', 3); $ft('f1', 'a1', 2, ['import_key' => 'tv:1']); $ft('f1', 'a1', 2, ['import_key' => 'sync:nt8:1']);   // a1: 2 by hand, 1 CSV, 1 sync
$ft('f1', 'a1', 1, ['demo' => true]); $ft('f1', 'a1', 40); $ft('f1', 'a2', 1);   // a sample trade, one 40 days old, one on the archived account: left out
$ft('f2', 'b1', 5, ['import_key' => 'sync:qt:9']); $ft('f2', 'b2', 5, ['import_key' => 'tx:800001']); $ft('f2', 'b3', 5); $ft('f2', 'gone', 5);   // « gone »: an account that no longer exists
$ft('fx', 'z1', 1); $ft('fx', 'z1', 1, ['import_key' => 'sync:nt8:2']);   // Mateo's: left out
$fm = sweep_metrics($p4, $app)['brief']['firms']; $fr = array_column($fm['rows'], null, 'id');
$pick = fn(array $r) => [$r['accounts'], $r['traders'], $r['eval'], $r['funded'], $r['live'], $r['trades'], $r['manual'], $r['csv'], $r['sync']];
$ok(array_keys($fr) === ['lucid', 'topstep', 'apex', 'tpt', 'mffu', 'tradeify', 'alpha', 'other', 'personal'], 'firms: one row per firm of the catalogue, then « other » and « personal » (' . implode(', ', array_keys($fr)) . ')');
$ok($pick($fr['topstep']) === [2, 2, 1, 1, 0, 5, 2, 1, 2], 'firms, Topstep: 2 accounts of 2 traders (the preset, and « TopstepX » by its alias), 1 evaluation 1 funded, 5 trades = 2 by hand + 1 CSV + 2 sync: ' . json_encode($pick($fr['topstep'])));
$ok($pick($fr['apex']) === [1, 1, 1, 0, 0, 0, 0, 0, 0], 'firms, Apex: 1 account, an evaluation by its profit target, no trade; the sample account is left out: ' . json_encode($pick($fr['apex'])));
$ok($pick($fr['other']) === [1, 1, 0, 0, 1, 1, 0, 1, 0] && $pick($fr['personal']) === [1, 1, 0, 0, 0, 1, 1, 0, 0], 'firms: a firm outside the catalogue → « other » (live, 1 CSV trade); no firm → « personal » (1 trade by hand)');
$ok($pick($fm['total']) === [5, 3, 2, 1, 1, 7, 3, 2, 2] && $fm['of'] === 3 && $pick($fr['lucid']) === [0, 0, 0, 0, 0, 0, 0, 0, 0],
    'firms, total: 5 accounts of 3 traders (the archived, the sample and Mateo\'s accounts left out), 7 trades = 3 by hand + 2 CSV + 2 sync: ' . json_encode($pick($fm['total'])));
$ok(sweep_metrics($pdo, $app)['brief']['firms'] !== null && sweep_metrics($pdo, $app)['brief']['firms']['total']['accounts'] >= 0, 'firms: the first database (accounts with no firm) gives the table too, no error');
$cronSql = (string) $pdo->query("SELECT sql FROM sqlite_master WHERE name = 'cron_runs'")->fetchColumn();   // the tasks' table is made once per run (the first database has it)
$p4->exec($cronSql);
$md4 = sweep_full_report($p4, [], $app, time());
$ok(str_contains($md4, '**Comptes par firme**') && str_contains($md4, '| Topstep | 2 | 2 | 1 | 1 | 0 | 5 | 40 % | 20 % | 40 % |') && str_contains($md4, '| Autre firme | 1 | 1 | 0 | 0 | 1 | 1 | 0 % | 100 % | 0 % |')
    && str_contains($md4, '| Compte personnel ou simulation | 1 | 1 | 0 | 0 | 0 | 1 | 100 % | 0 % | 0 % |') && str_contains($md4, '| Total | 5 | 3 | 2 | 1 | 1 | 7 | 43 % | 29 % | 29 % |'), 'firms: the table is in « Export for Claude », with the shares');
// (13 Nov., step 2) behind « other »: the names typed, one spelling each; a name typed by one trader only is not shown
$ok($fm['other_names'] === [] && $fm['other_rest'] === ['names' => 1, 'accounts' => 1, 'traders' => 1], 'other firms: « Bulenox », typed by one trader, is not shown: counted in the rest (' . json_encode($fm['other_rest']) . ')');
foreach (['g1', 'g2', 'g3', 'g4'] as $id) $p4->prepare('INSERT INTO users (id, created_at, is_internal) VALUES (?, ?, 0)')->execute([$id, '2026-09-01 12:00:00']);
$fd('g1', 'firms', 'y1', ['name' => 'Bulenox']); $fd('g1', 'accounts', 'd1', ['firm_id' => 'y1', 'status' => 'active']); $fd('g1', 'accounts', 'd2', ['firm_id' => 'y1', 'status' => 'active']);
$fd('g2', 'firms', 'y2', ['name' => '  bulenox  LLC ']); $fd('g2', 'accounts', 'd3', ['firm_id' => 'y2', 'status' => 'active']);
$fd('g3', 'firms', 'y3', ['name' => 'Blue Guardian, Inc.']); $fd('g3', 'accounts', 'd4', ['firm_id' => 'y3', 'status' => 'active']);
$fd('g4', 'firms', 'y4', ['name' => 'BLUE  GUARDIAN']); $fd('g4', 'accounts', 'd5', ['firm_id' => 'y4', 'status' => 'active']);
$fd('g4', 'firms', 'y5', ['name' => 'Chez Jean Tremblay']); $fd('g4', 'accounts', 'd6', ['firm_id' => 'y5', 'status' => 'active']);
$fd('g4', 'accounts', 'd7', ['firm_id' => 'gone', 'status' => 'active']);   // a firm that no longer exists: « other », with no name
$fm2 = sweep_metrics($p4, $app)['brief']['firms'];
$ok($fm2['other_names'] === [['name' => 'Bulenox', 'accounts' => 4, 'traders' => 3], ['name' => 'BLUE  GUARDIAN', 'accounts' => 2, 'traders' => 2]] || $fm2['other_names'] === [['name' => 'Bulenox', 'accounts' => 4, 'traders' => 3], ['name' => 'BLUE GUARDIAN', 'accounts' => 2, 'traders' => 2]] || $fm2['other_names'] === [['name' => 'Bulenox', 'accounts' => 4, 'traders' => 3], ['name' => 'Blue Guardian, Inc.', 'accounts' => 2, 'traders' => 2]],
    'other firms: « Bulenox », « bulenox LLC » → one name, 4 accounts of 3 traders; « Blue Guardian, Inc. » and « BLUE GUARDIAN » → one name, 2 of 2; the most accounts first: ' . json_encode($fm2['other_names']));
$ok($fm2['other_rest'] === ['names' => 2, 'accounts' => 2, 'traders' => 1] && !str_contains(json_encode($fm2), 'Tremblay'), 'other firms: a name typed by one trader only and an account with no firm name → « rest » (2 accounts of 1 trader), never shown: ' . json_encode($fm2['other_rest']));
$p4->exec('CREATE TABLE feedback (id INTEGER PRIMARY KEY, user_id TEXT, type TEXT, rating INT, message TEXT, page TEXT, status TEXT, created_at INT, question TEXT, answer TEXT)');
$p4->exec("INSERT INTO feedback (user_id, type, rating, message, page, status, created_at, question, answer) VALUES ('f1', 'answer', NULL, '', 'email', 'new', " . time() . ", 'What stopped you?', 'Too long to fill in'), ('f2', 'answer', NULL, 'Too many taps', 'email', 'new', " . time() . ", 'What stopped you?', 'Other'), ('f1', 'idea', NULL, 'A dark chart', 'stats', 'new', " . time() . ", NULL, NULL)");
$md5 = sweep_full_report($p4, [], $app, time());
$ok(str_contains($md5, '**Dans « Autre firme »**') && str_contains($md5, '| Bulenox | 4 | 3 |') && str_contains($md5, '| autres (2 noms tapés par un seul trader, ou sans nom) | 2 | 1 |') && !str_contains($md5, 'Tremblay'), 'other firms: the same table in « Export for Claude », nothing personal in it');
$ok(str_contains($md5, '| answer | — | email | new | « What stopped you? » → Too long to fill in |') && str_contains($md5, '« What stopped you? » → Other — Too many taps |') && str_contains($md5, '| idea | — | stats | new | A dark chart |'),
    'feedback in the export: an answer given in one tap from an email shows its question and the answer chosen (its text was empty), a comment follows; a written feedback as before');
foreach (['g1', 'g2', 'g3', 'g4'] as $id) { $p4->exec("DELETE FROM users WHERE id = '$id'"); $p4->exec("DELETE FROM documents WHERE user_id = '$id'"); }

// (13 Nov., brief « Admin lisible sur téléphone », 2.1) « To look at »: only what asks for an action
require $app . '/ops/watch.php';
$p5 = new PDO('sqlite:' . $tmp . '/w.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$wapp = $tmp . '/wapp'; mkdir($wapp);   // an app folder of its own: its error_log
$T0 = time(); $kinds = fn(array $w) => array_column($w['items'], null, 'k');
$p5->exec($cronSql);
$green = function () use ($p5, $T0) { $p5->exec('DELETE FROM cron_runs'); foreach (array_keys(SWEEP_CRON_TASKS) as $t) $p5->prepare('INSERT INTO cron_runs (task, started_at, finished_at, duration_ms, ok, last_ok_at) VALUES (?, ?, ?, 10, 1, ?)')->execute([$t, $T0 - 30, $T0 - 20, $T0 - 20]); };
$green();
file_put_contents(pr_status_path(), json_encode(['last_run' => gmdate('c', $T0 - 3600), 'firms' => []]));
$wcfg = []; file_put_contents($tmp . '/backup-cfg.php', "<?php return ['passphrase' => 'x', 's3' => ['bucket' => 'b']];"); $envB = getenv('SWEEP_BACKUP_CONFIG'); putenv('SWEEP_BACKUP_CONFIG=' . $tmp . '/backup-cfg.php');   // backups set up, with a copy outside
$w = sweep_watch($p5, $wcfg, $app, $T0, $wapp . '/error_log');
$ok($w['items'] === [], 'to look at: every task green, rules checked an hour ago, no error, no sync, no lead → nothing (' . json_encode(array_column($w['items'], 'k')) . ')');
$p5->exec("UPDATE cron_runs SET ok = 0, error = 'boom' WHERE task = 'game'"); $p5->exec('UPDATE cron_runs SET last_ok_at = ' . ($T0 - 40 * 86400) . ", finished_at = " . ($T0 - 20) . " WHERE task = 'backup'");
$k = $kinds(sweep_watch($p5, $wcfg, $app, $T0, $wapp . '/error_log'));
$ok(($k['task']['n'] ?? 0) === 2 && $k['task']['red'] === 1 && in_array('game', $k['task']['tasks'], true), 'to look at: a failed task and a late one → one line, 2 tasks, 1 red: ' . json_encode($k['task'] ?? null));
$green();
$p5->exec('CREATE TABLE client_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, msg TEXT, src TEXT, line INT, page TEXT, ua TEXT, ver TEXT, created_at INT NOT NULL)');
$we = fn(string $m, int $ts) => $p5->prepare("INSERT INTO client_errors (user_id, msg, created_at) VALUES ('u', ?, ?)")->execute([$m, $ts]);
$we('old one', $T0 - 20 * 86400); $we('old one', $T0 - 3600); $we('new one', $T0 - 2 * 86400); $we('new one', $T0 - 60); $we('newer', $T0 - 30);
file_put_contents($wapp . '/error_log', '[' . gmdate('d-M-Y H:i:s', $T0 - 20 * 86400) . " UTC] PHP Warning:  known thing on line 12\n[" . gmdate('d-M-Y H:i:s', $T0 - 3600) . " UTC] PHP Warning:  known thing on line 48\n["
    . gmdate('d-M-Y H:i:s', $T0 - 7200) . " UTC] PHP Fatal error:  brand new failure\n[" . gmdate('d-M-Y H:i:s', $T0 - 60) . " UTC] PHP Fatal error:  brand new failure\n");
$k = $kinds(sweep_watch($p5, $wcfg, $app, $T0, $wapp . '/error_log'));
$ok(($k['error']['js'] ?? 0) === 2 && $k['error']['php'] === 1 && $k['error']['n'] === 3, 'to look at: 2 JS messages first seen this week (the one known for 20 days is not new) and 1 new PHP error (the known warning is not): ' . json_encode($k['error'] ?? null));
$p5->exec('DELETE FROM client_errors'); unlink($wapp . '/error_log');
file_put_contents(pr_status_path(), json_encode(['last_run' => gmdate('c', $T0 - 3600), 'firms' => ['apex' => ['status' => 'review', 'errors' => ['not applied (not confirmed by a second reading, read again next week): eod 50K dd_c 2000 → 9000'], 'changes' => []], 'topstep' => ['status' => 'unchanged', 'errors' => ['page not reachable'], 'changes' => []]]]));
$k = $kinds(sweep_watch($p5, $wcfg, $app, $T0, $wapp . '/error_log'));
$ok(($k['rules']['n'] ?? 0) === 1 && $k['rules']['firms'] === ['Apex Trader Funding'] && $k['rules']['stale'] === false, 'to look at: rules read and not applied at one firm (another error is not one): ' . json_encode($k['rules'] ?? null));
file_put_contents(pr_status_path(), json_encode(['last_run' => gmdate('c', $T0 - 12 * 86400), 'firms' => []]));
$k = $kinds(sweep_watch($p5, $wcfg, $app, $T0, $wapp . '/error_log'));
$ok(($k['rules']['stale'] ?? false) === true && $k['rules']['n'] === 0 && $k['rules']['days'] === 12, 'to look at: no check of the rules for 12 days: ' . json_encode($k['rules'] ?? null));
file_put_contents(pr_status_path(), json_encode(['last_run' => gmdate('c', $T0 - 3600), 'firms' => []]));
$p5->exec('CREATE TABLE signup_leads (email_lc TEXT PRIMARY KEY, created_at INT NOT NULL, updated_at INT NOT NULL, completed_at INT NULL)');
$p5->exec("INSERT INTO signup_leads VALUES ('a@t.dev', " . ($T0 - 86400) . ", 0, NULL), ('b@t.dev', " . ($T0 - 2 * 86400) . ", 0, " . ($T0 - 86400) . "), ('c@t.dev', " . ($T0 - 9 * 86400) . ", 0, NULL)");
$k = $kinds(sweep_watch($p5, $wcfg, $app, $T0, $wapp . '/error_log'));
$ok(($k['signups']['n'] ?? 0) === 1, 'to look at: 1 sign-up started and not finished in 7 days (one finished, one older: not counted): ' . json_encode($k['signups'] ?? null));
file_put_contents($tmp . '/backup-cfg.php', "<?php return ['passphrase' => 'x'];");
$k = $kinds(sweep_watch($p5, [], $app, $T0, $wapp . '/error_log'));
$ok(isset($k['backup']) && $k['backup']['none'] === false, 'to look at: backups with no copy outside the server → its line');
putenv('SWEEP_BACKUP_CONFIG=' . $tmp . '/none.php');
$k = $kinds(sweep_watch($p5, [], $app, $T0, $wapp . '/error_log'));
$ok(isset($k['backup']) && $k['backup']['none'] === true, 'to look at: no backup set up → its line');
putenv('SWEEP_BACKUP_CONFIG' . ($envB !== false ? '=' . $envB : ''));
$p5 = null; @unlink($tmp . '/backup-cfg.php'); @rmdir($wapp);

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
