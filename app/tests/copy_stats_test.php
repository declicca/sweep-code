<?php
declare(strict_types=1);
/**
 * Sweep — copies with their own size (brief 02 part 4) count once, as their original (the earliest created), on the server too:
 *   php tests/copy_stats_test.php
 * The game's day (its discipline rules, streaks) and the trades Sweep AI reads: a group of 3 copies (2, 2 and 1 contracts)
 * is one trade, the original's P&L, with its 3 accounts — like the app's Stats, Journal and My money.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-copies-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require $app . '/notify/notify.php';
require $app . '/game/game.php';
require_once $app . '/ai/ai-core.php';   // (sai_q; nothing read until an AI call)
require_once $app . '/ai/ai-stats.php';
GameEngine::setPdo($pdo); GameEngine::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$put = function (string $id, array $d) use ($pdo) { $pdo->prepare('INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute(['u1', 'trades', $id, json_encode($d + ['id' => $id]), $d['created_at'], $d['created_at']]); };
$base = ['instrument' => 'MNQ', 'direction' => 'long', 'date' => '2026-10-07', 'session_date' => true, 'entry_time' => '10:00:00', 'exit_time' => '10:05:00', 'entry' => 100, 'exit' => 110, 'copy_group' => 'g1'];
// saved in this order on purpose: the copies first, the original (the earliest created) last
$put('c2', $base + ['account_id' => 'a3', 'contracts' => 1, 'pnl_c' => 2000, 'fees_c' => 500, 'created_at' => '2026-10-07T14:05:00.002Z']);
$put('c1', $base + ['account_id' => 'a2', 'contracts' => 2, 'pnl_c' => 4000, 'fees_c' => 800, 'created_at' => '2026-10-07T14:05:00.001Z']);
$put('o', $base + ['account_id' => 'a1', 'contracts' => 2, 'pnl_c' => 4000, 'fees_c' => 1000, 'created_at' => '2026-10-07T14:05:00.000Z']);
$put('solo', array_diff_key($base, ['copy_group' => 1]) + ['account_id' => 'a1', 'contracts' => 1, 'pnl_c' => -1000, 'fees_c' => 500, 'entry_time' => '11:00:00', 'created_at' => '2026-10-07T15:00:00.000Z']);
$m = new ReflectionMethod('GameEngine', 'dayTrades');
$day = array_map(fn($t) => $t['id'], $m->invoke(null, 'u1', '2026-10-07'));
$ok($day === ['o', 'solo'], 'the game\'s day: the group is one trade, its original (' . implode(', ', $day) . ')');
$all = new ReflectionMethod('GameEngine', 'allTradesChrono');
$ok(array_map(fn($t) => $t['id'], $all->invoke(null, 'u1')) === ['o', 'solo'], 'every trade in order: the same');
$ai = sai_trades($pdo, 'u1');
$g = array_values(array_filter($ai, fn($t) => ($t['accounts'] ?? 1) > 1))[0] ?? [];
$ok(count($ai) === 2 && ($g['pnl_c'] ?? null) === 4000 && ($g['fees_c'] ?? null) === 1000 && ($g['contracts'] ?? null) === 2 && ($g['accounts'] ?? null) === 3,
    'Sweep AI reads the group once: the original\'s P&L, fees and size, on 3 accounts (' . json_encode(['pnl' => $g['pnl_c'] ?? null, 'fees' => $g['fees_c'] ?? null, 'n' => $g['contracts'] ?? null, 'acc' => $g['accounts'] ?? null]) . ')');
$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
