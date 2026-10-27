<?php
declare(strict_types=1);
/**
 * Sweep — how the app is used (ops/usage.php) and Admin › « Export for Claude » (ops/report.php), on a throwaway SQLite
 * database (never the live one):
 *   php tests/usage_report_test.php
 *  1  a report adds up per New York day, trader, key and device; wrong keys and too-big numbers are left out
 *  2  the summary: traders, share, opens, minutes, phone / computer; Mateo's and test accounts are not counted
 *  3  the language, theme and last device of each trader
 *  4  the export: its 13 sections, the start step by step, usage, feedback without email, link or phone number, the errors;
 *     never a trader's name or email
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-usage-' . bin2hex(random_bytes(4)); mkdir($tmp);
$GLOBALS['DATA'] = $tmp;
putenv('SWEEP_BACKUP_CONFIG=' . $tmp . '/none.php');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, created_at TEXT, utm_source TEXT, utm_campaign TEXT, is_internal INT DEFAULT 0, is_admin INT DEFAULT 0, disabled INT DEFAULT 0, found_via TEXT, first_name TEXT)');
$pdo->exec('CREATE TABLE game_analytics (user_id TEXT, event TEXT, created_at INT, meta_json TEXT)');
$pdo->exec('CREATE TABLE game_days (user_id TEXT, trading_day TEXT, trades_count INT DEFAULT 0, review_done INT DEFAULT 0, is_swept INT DEFAULT 0, activity INT DEFAULT 0)');
$pdo->exec('CREATE TABLE documents (user_id TEXT, collection TEXT, id TEXT, data TEXT, created_at TEXT)');
$pdo->exec('CREATE TABLE feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, type TEXT NOT NULL, rating INTEGER NULL, message TEXT NOT NULL, page TEXT NULL, context TEXT NULL, screenshot TEXT NULL, status TEXT NOT NULL, reply TEXT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NULL)');
require $app . '/ops/report.php';
$fails = 0;
function ok(bool $c, string $what): void { global $fails; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $fails += $c ? 0 : 1; }

$now = time(); $u = fn(string $id, int $admin = 0, int $internal = 0) => $pdo->prepare("INSERT INTO users (id, username, email, created_at, found_via, is_admin, is_internal, first_name) VALUES (?, ?, ?, ?, 'tiktok', ?, ?, 'Zoé')")->execute([$id, 'name_' . $id, $id . '@secret.test', gmdate('Y-m-d H:i:s', $now - 3 * 86400), $admin, $internal]);
$u('a'); $u('b'); $u('boss', 1, 1); $u('staff', 0, 1);

// 1
$n = sweep_usage_record($pdo, 'a', ['dev' => 'phone', 'app' => true, 'lang' => 'fr', 'theme' => 'dark', 'p' => ['p:dashboard' => [2, 120], 's:nav-am-shot' => [1, 30], 'bad key' => [1, 1], 'p:<x>' => [1, 1], 'p:trades' => [9999, 999999]]], $now);
sweep_usage_record($pdo, 'a', ['dev' => 'phone', 'app' => true, 'lang' => 'fr', 'theme' => 'dark', 'p' => ['p:dashboard' => [1, 60]]], $now);
ok($n === 3, "1 the valid keys are kept ($n)");
$r = $pdo->query("SELECT opens, secs, device FROM usage_daily WHERE user_id = 'a' AND k = 'p:dashboard'")->fetch();
ok($r && (int) $r['opens'] === 3 && (int) $r['secs'] === 180 && $r['device'] === 'phone-app', '1 two reports add up on the same row, « phone-app » once installed (' . json_encode($r) . ')');
$r = $pdo->query("SELECT opens, secs FROM usage_daily WHERE user_id = 'a' AND k = 'p:trades'")->fetch();
ok($r && (int) $r['opens'] === 500 && (int) $r['secs'] === 86400, '1 too-big numbers are capped (' . json_encode($r) . ')');
sweep_usage_record($pdo, 'b', ['dev' => 'desktop', 'lang' => 'en', 'p' => ['p:dashboard' => [1, 600]]], $now);
sweep_usage_record($pdo, 'boss', ['dev' => 'desktop', 'p' => ['p:admin' => [5, 600]]], $now);
sweep_usage_record($pdo, 'staff', ['dev' => 'desktop', 'p' => ['p:dashboard' => [5, 600]]], $now);

// 2, 3
$real = ['a' => true, 'b' => true];
$s = sweep_usage_summary($pdo, $now, $real);
$d = $s['keys']['p:dashboard'] ?? null;
ok($s['traders'] === 2 && $d && $d['traders'] === 2 && $d['pct'] === 100 && $d['opens'] === 4 && $d['minutes'] === 13 && $d['phone'] === 3 && $d['desktop'] === 1, '2 the dashboard: 2 traders, 100 %, 4 opens, 13 min, 3 on the phone / 1 on the computer (' . json_encode($d) . ')');
ok(!isset($s['keys']['p:admin']), '2 Mateo\'s and test accounts are not counted');
ok(($s['keys']['s:nav-am-shot']['pct'] ?? 0) === 50, '2 a sheet: 1 trader of 2');
ok($s['env']['lang'] == ['fr' => 1, 'en' => 1] && $s['env']['theme'] == ['dark' => 1, 'light' => 1] && $s['env']['device'] == ['phone-app' => 1, 'desktop' => 1], '3 language, theme, device (' . json_encode($s['env']) . ')');

// 4
$pdo->prepare("INSERT INTO feedback (user_id, type, rating, message, page, status, created_at) VALUES ('a', 'idea', 4, 'Write me at zoe@mail.com or +1 514 555 0199, see https://x.io/a', '#trades', 'new', ?)")->execute([$now]);
$pdo->prepare("INSERT INTO feedback (user_id, type, message, status, created_at) VALUES ('boss', 'bug', 'Admin note', 'new', ?)")->execute([$now]);
sweep_errors_schema($pdo);
$pdo->prepare("INSERT INTO client_errors (user_id, msg, src, line, page, ua, ver, created_at) VALUES ('a', 'Boom 12', 'app.js', 3, '#trades', 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) Safari/604.1', 'app.x', ?)")->execute([$now - 60]);
$md = sweep_full_report($pdo, [], $app, $now);
$secs = []; for ($i = 1; $i <= 13; $i++) if (!preg_match('/^## ' . $i . '\. /m', $md) && $i !== 8) $secs[] = $i;
ok(!$secs, '4 the sections 1 to 13 (8, sync, only once it is used) (missing: ' . implode(', ', $secs) . ')');
ok(str_starts_with($md, '# Sweep — tout Admin, pour Claude') && str_contains($md, '2 traders comptés'), '4 the title and the traders counted');
ok(str_contains($md, '| Premier compte |') && str_contains($md, '| p:dashboard | 2 | 100 % | 4 | 3 / 1 | 13 |'), '4 the start and the usage table');
ok(str_contains($md, '[courriel]') && str_contains($md, '[numéro]') && str_contains($md, '[lien]') && !str_contains($md, 'zoe@mail.com') && !str_contains($md, '555 0199') && !str_contains($md, 'Admin note'), '4 the feedback: email, phone and link taken out, Mateo\'s left out');
ok(str_contains($md, '### 1. Boom #') || str_contains($md, '### 1. Boom 12'), '4 the JS errors');
ok(!str_contains($md, 'secret.test') && !str_contains($md, 'name_a') && !str_contains($md, 'Zoé'), '4 never a trader\'s name or email');

echo $fails ? "$fails failed\n" : "all passed\n";
exit($fails ? 1 : 0);
