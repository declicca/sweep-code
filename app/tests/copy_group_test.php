<?php
declare(strict_types=1);
/**
 * Sweep — copy groups with a master account (brief « avance concurrentielle », step 2), server side, on a throwaway SQLite
 * database (never the live one):
 *   php tests/copy_group_test.php
 * A master account and its followers (multiplier ×1, ×2 with a commission, a follower synced itself, an archived one): a trade
 * the sync writes on the master is copied on each follower (size × multiplier, P&L, commission, the notes of the moment,
 * the original counted first), never on the synced follower, whose own trade joins the group; a platform correction moves the
 * copies (the trader's notes on a copy stay); a deleted copy is never written again; a follower linked later: its synced trade
 * takes the copy's place (no double, even at another size); the plan (Pro and Elite: copy_groups); Free's limit.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-cg-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, disabled INTEGER NOT NULL DEFAULT 0)');
$pdo->exec("INSERT INTO users (id) VALUES ('u1')");
// what api.php provides around a write: the plan (guard and features), the game events
$FROZEN = []; $CAN = true; $EVENTS = [];
function billing_on(): bool { return true; }
function billing_account_ids(string $uid): array { return []; }
function sb_live(string $uid = ''): bool { return true; }
function sb_can(PDO $pdo, string $uid, string $feature): bool { global $CAN; return $feature === 'copy_groups' ? $CAN : true; }
function sb_guard(PDO $pdo, string $uid, string $what, array $ctx): ?array { global $FROZEN; return in_array($ctx['account_id'] ?? '', $FROZEN, true) ? ['error' => 'Upgrade', 'code' => 'frozen_account'] : null; }
function nt_doc_event(string $uid, string $col, string $id, ?array $doc, ?array $prev): void { global $EVENTS; $EVENTS[] = [$id, $doc['account_id'] ?? null, $doc['date'] ?? null]; }
final class Notify { public static function send(string $uid, string $type, array $params = [], array $opts = []): ?int { return 1; } }
require $app . '/sync/sync-store.php';

$n = 0; $f = 0;
function ok($c, $what) { global $n, $f; $n++; if (!$c) $f++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
$T = fn(string $ny) => (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp() * 1000;
$fill = fn(string $id, string $acct, string $side, int $qty, float $px, string $ny) => ['id' => $id, 'account' => $acct, 'contract' => 'NQ 12-26', 'side' => $side, 'qty' => $qty, 'price' => $px, 'ts' => $T($ny), 'point_value' => 20];
$put = function (string $col, array $d) use ($pdo) {
    $pdo->prepare("INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES ('u1', ?, ?, ?, ?, ?)")->execute([$col, $d['id'], json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z']);
};
$trades = function () use ($pdo) { $o = []; foreach ($pdo->query("SELECT id, data FROM documents WHERE collection = 'trades' AND user_id = 'u1' ORDER BY id") as $r) $o[$r['id']] = json_decode($r['data'], true); return $o; };
$on = fn(string $acc) => array_values(array_filter($trades(), fn($t) => ($t['account_id'] ?? '') === $acc));
$raw = fn(string $id) => (string) $pdo->query("SELECT data FROM documents WHERE collection = 'trades' AND user_id = 'u1' AND id = " . $pdo->quote($id))->fetchColumn();
$sa = fn(string $name) => $pdo->query('SELECT * FROM sync_accounts WHERE user_id = ' . $pdo->quote('u1') . ' AND ext_id = ' . $pdo->quote($name))->fetch();
$edit = function (string $id, callable $fn) use ($pdo, $raw) { $d = json_decode($raw($id)); $fn($d); $pdo->prepare("UPDATE documents SET data = ? WHERE user_id = 'u1' AND collection = 'trades' AND id = ?")->execute([json_encode($d, JSON_UNESCAPED_SLASHES), $id]); };

// the group: master M, followers F1 (×1), F2 (×2, $4 commission), F3 (synced itself), F4 (archived); X outside
$put('accounts', ['id' => 'M', 'name' => 'Apex 1', 'group_id' => 'grp-1', 'copy_lead' => true]);
$put('accounts', ['id' => 'F1', 'name' => 'Apex 2', 'group_id' => 'grp-1']);
$put('accounts', ['id' => 'F2', 'name' => 'Apex 3', 'group_id' => 'grp-1', 'copy_pct' => 200, 'fee_rt_c' => 400]);
$put('accounts', ['id' => 'F3', 'name' => 'Apex 4', 'group_id' => 'grp-1']);
$put('accounts', ['id' => 'F4', 'name' => 'Apex 5', 'group_id' => 'grp-1', 'status' => 'archived']);
$put('accounts', ['id' => 'X', 'name' => 'Topstep']);
$conn = sync_auth($pdo, sync_new_key($pdo, 'u1', 'ninjatrader')['key']);

// 1. the synced follower first: linked, one trade at 10:00
sync_receive($pdo, $conn, ['accounts' => [['name' => 'APEX-4'], ['name' => 'APEX-1']], 'fills' => [$fill('f1', 'APEX-4', 'buy', 1, 21000, '2026-10-07 10:00:10'), $fill('f2', 'APEX-4', 'sell', 1, 21010, '2026-10-07 10:05:00')]]);
sync_link($pdo, 'u1', $sa('APEX-4')['id'], 'F3');
ok(count($on('F3')) === 1 && !$on('F1') && !$on('M'), 'a follower synced itself: its trade, nothing copied anywhere');

// 2. the master linked: its trade at 10:00 → a copy on F1 (×1) and F2 (×2), none on F3 (its own trade), F4 (archived), X
$put('trades', ['id' => 'keep', 'account_id' => 'X', 'instrument' => 'NQ', 'date' => '2026-10-07', 'direction' => 'long', 'contracts' => 1, 'pnl_c' => 100]);
sync_receive($pdo, $conn, ['fills' => [$fill('m1', 'APEX-1', 'buy', 1, 21000, '2026-10-07 10:00:00'), $fill('m2', 'APEX-1', 'sell', 1, 21010, '2026-10-07 10:05:00')]]);
$EVENTS = [];
$r = sync_link($pdo, 'u1', $sa('APEX-1')['id'], 'M');
$m = $on('M')[0] ?? []; $c1 = $on('F1')[0] ?? []; $c2 = $on('F2')[0] ?? [];
ok($r['created'] === 1 && count($on('M')) === 1 && count($on('F1')) === 1 && count($on('F2')) === 1 && count($on('F3')) === 1 && !$on('F4') && count($on('X')) === 1, 'the master\'s synced trade: one copy on each follower, none on the synced follower, the archived one or another account');
$g = $m['copy_group'] ?? '';
ok($g !== '' && ($c1['copy_group'] ?? '') === $g && ($c2['copy_group'] ?? '') === $g && ($on('F3')[0]['copy_group'] ?? '') === $g, 'one group: the master\'s trade, its 2 copies and the synced follower\'s own trade (« ×4 accounts »)');
ok(($c1['contracts'] ?? 0) === 1 && ($c1['pnl_c'] ?? 0) === 20000 && ($c2['contracts'] ?? 0) === 2 && ($c2['pnl_c'] ?? 0) === 40000 && ($c2['fees_c'] ?? 0) === 800 && ($c2['fees_auto'] ?? false) === true
    && array_sum(array_column($c2['executions'] ?? [], 'qty')) === 4, 'sizes: ×1 → 1 contract, +$200; ×2 → 2 contracts, +$400, its own $4 commission per contract ($8), executions at 2');
ok(($c1['copy_src'] ?? '') === $m['id'] && !isset($c1['import_key']) && !isset($c1['source']) && strcmp((string) $c1['created_at'], (string) ($m['created_at'] ?? '')) > 0 && str_starts_with((string) $c1['id'], 'cp-'), 'a copy: made by Sweep (copy_src, no import key, no platform), created after the original (the group counts as its original)');
ok(strpos($raw((string) $c1['id']), '"discipline":{}') !== false, 'an empty checklist stays {} on a copy (not [])');
ok(in_array('F1', array_column($EVENTS, 1), true) && in_array('F2', array_column($EVENTS, 1), true), 'the game and the prop alerts hear of the followers\' day too');

// 3. the trader writes notes on a copy; the platform corrects the master's exit → the copies follow (P&L), the notes stay
$edit((string) $c2['id'], function ($d) { $d->notes = 'Size up on 3'; });
sync_receive($pdo, $conn, ['fills' => [$fill('m2', 'APEX-1', 'sell', 1, 21020, '2026-10-07 10:05:00')]]);
$c1 = $on('F1')[0]; $c2 = $on('F2')[0];
ok($c1['pnl_c'] === 40000 && $c2['pnl_c'] === 80000 && $c2['exit'] == 21020 && $c2['notes'] === 'Size up on 3' && count($on('F2')) === 1, 'a platform correction (exit 21,020): copies at +$400 and +$800, the copy\'s notes kept, no new copy');

// 4. a copy deleted by the trader is never written again
$pdo->exec("DELETE FROM documents WHERE collection = 'trades' AND id = " . $pdo->quote((string) $c1['id']));
sync_receive($pdo, $conn, ['fills' => [$fill('m2', 'APEX-1', 'sell', 1, 21015, '2026-10-07 10:05:00')]]);
ok(!$on('F1') && $on('F2')[0]['pnl_c'] === 60000, 'the copy deleted on Apex 2 stays deleted; Apex 3 still follows (+$600)');

// 5. a follower linked later: its synced trade takes the copy's place, even at another size (no double)
sync_receive($pdo, $conn, ['accounts' => [['name' => 'APEX-3']], 'fills' => [$fill('g1', 'APEX-3', 'buy', 3, 21000, '2026-10-07 10:00:05'), $fill('g2', 'APEX-3', 'sell', 3, 21015, '2026-10-07 10:05:00')]]);
$r = sync_link($pdo, 'u1', $sa('APEX-3')['id'], 'F2');
$t = $on('F2');
ok($r['merged'] === 1 && $r['created'] === 0 && count($t) === 1 && $t[0]['contracts'] === 3 && $t[0]['notes'] === 'Size up on 3' && ($t[0]['copy_group'] ?? '') === $g && ($t[0]['source'] ?? '') === 'ninjatrader', 'Apex 3 linked: its synced trade (3 contracts) completes the copy (notes and group kept), no double');
sync_receive($pdo, $conn, ['fills' => [$fill('m2', 'APEX-1', 'sell', 1, 21012, '2026-10-07 10:05:00')]]);
ok($on('F2')[0]['contracts'] === 3 && $on('F2')[0]['exit'] == 21015, 'then a correction on the master never rewrites the follower\'s platform trade');

// 6. a new master trade: copied on the followers not synced (Apex 2), never on the synced ones; one group with their own trades
sync_receive($pdo, $conn, ['fills' => [$fill('m3', 'APEX-1', 'sell', 2, 21100, '2026-10-07 11:00:00'), $fill('m4', 'APEX-1', 'buy', 2, 21090, '2026-10-07 11:10:00'),
    $fill('f3', 'APEX-4', 'sell', 2, 21100, '2026-10-07 11:00:30'), $fill('f4', 'APEX-4', 'buy', 2, 21090, '2026-10-07 11:10:00')]]);
$m2 = array_values(array_filter($on('M'), fn($x) => $x['direction'] === 'short'))[0] ?? [];
$f3 = array_values(array_filter($on('F3'), fn($x) => $x['direction'] === 'short'))[0] ?? [];
$k1 = array_values(array_filter($on('F1'), fn($x) => $x['direction'] === 'short'));
ok(count($k1) === 1 && $k1[0]['contracts'] === 2 && $k1[0]['pnl_c'] === 40000 && count(array_filter($on('F2'), fn($x) => $x['direction'] === 'short')) === 0, 'the next master trade: Apex 2 gets its copy (2 short, +$400), Apex 3 (synced now) gets none');
ok(($m2['copy_group'] ?? '') !== '' && ($f3['copy_group'] ?? '') === $m2['copy_group'] && ($k1[0]['copy_group'] ?? '') === $m2['copy_group'], 'one group again: master, copy, the synced follower\'s own trade');

// 7. the plan: without copy groups (Free), nothing is copied; a frozen follower gets nothing
$CAN = false;
sync_receive($pdo, $conn, ['fills' => [$fill('m5', 'APEX-1', 'buy', 1, 21000, '2026-10-08 10:00:00'), $fill('m6', 'APEX-1', 'sell', 1, 21005, '2026-10-08 10:01:00')]]);
ok(count(array_filter($on('F1'), fn($x) => $x['date'] === '2026-10-08')) === 0 && count(array_filter($on('M'), fn($x) => $x['date'] === '2026-10-08')) === 1, 'Free (no copy_groups): the master\'s trade is written, nothing copied');
$CAN = true; $FROZEN = ['F1'];
sync_receive($pdo, $conn, ['fills' => [$fill('m7', 'APEX-1', 'buy', 1, 21000, '2026-10-08 11:00:00'), $fill('m8', 'APEX-1', 'sell', 1, 21005, '2026-10-08 11:01:00')]]);
ok(count(array_filter($on('F1'), fn($x) => $x['date'] === '2026-10-08')) === 0, 'a follower paused by the plan gets no copy');
$FROZEN = [];

// 8. a group without a master (brief 02 part 4): nothing copied by the server
$pdo->exec("UPDATE documents SET data = json_remove(data, '$.copy_lead') WHERE collection = 'accounts' AND id = 'M'");
sync_receive($pdo, $conn, ['fills' => [$fill('m9', 'APEX-1', 'buy', 1, 21000, '2026-10-09 10:00:00'), $fill('m10', 'APEX-1', 'sell', 1, 21005, '2026-10-09 10:01:00')]]);
ok(count(array_filter($on('F1'), fn($x) => $x['date'] === '2026-10-09')) === 0, 'a group without a master account: the server copies nothing (the app\'s « Copy to my group » as before)');

// 9. the plans: copy groups for Pro and Elite, not Free, unless the config says otherwise (billing-core.php)
$php = escapeshellarg(PHP_BINARY);
$code = 'require ' . var_export($app . '/billing/billing-core.php', true) . '; sb_set_config(["plans" => ["free" => [], "pro" => [], "elite" => []]]); echo json_encode([sb_plan_limits("free")["copy_groups"], sb_plan_limits("pro")["copy_groups"], sb_plan_limits("elite")["copy_groups"]]);';
ok(trim((string) shell_exec("$php -r " . escapeshellarg($code))) === '[false,true,true]', 'the plans: copy groups with Pro and Elite, not Free');

// 10. account deleted: the copies' memory too
sync_delete_user($pdo, 'u1');
ok((int) $pdo->query("SELECT COUNT(*) FROM sync_copies WHERE user_id = 'u1'")->fetchColumn() === 0, 'account deleted: the copies made by the sync are forgotten too');

array_map('unlink', glob($tmp . '/*')); rmdir($tmp);
echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
