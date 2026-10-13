<?php
declare(strict_types=1);
/**
 * Sweep — automatic sync, server side, on a throwaway SQLite database (never the live one):
 *   php tests/sync_store_test.php
 * The personal key, executions received (replayed, amended, removed), accounts found, linking with a trade typed by
 * hand, the trader's notes kept, a deleted trade never written again (Undo brings it back), a late execution, copy groups
 * across accounts, the plan's write guard, the record limit, one game event per trading day touched.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-sync-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, disabled INTEGER NOT NULL DEFAULT 0)');
$pdo->exec("INSERT INTO users (id) VALUES ('u1'), ('u2')");
// what api.php provides around a write: the plan's guard, the game / notification events, the referral check
$FROZEN = []; $EVENTS = []; $REF = 0;
function billing_on(): bool { return true; }
function billing_account_ids(string $uid): array { return []; }
function sb_guard(PDO $pdo, string $uid, string $what, array $ctx): ?array { global $FROZEN; return in_array($ctx['account_id'] ?? '', $FROZEN, true) ? ['error' => 'Upgrade', 'code' => 'frozen_account'] : null; }
function nt_doc_event(string $uid, string $col, string $id, ?array $doc, ?array $prev): void { global $EVENTS; $EVENTS[] = [$col, $id, $doc['date'] ?? null, $prev === null]; }
function ref_check_user(PDO $pdo, string $uid): void { global $REF; $REF++; }
final class Notify { public static array $sent = []; public static function send(string $uid, string $type, array $params = [], array $opts = []): ?int { self::$sent[] = [$uid, $type, $params, $opts]; return count(self::$sent); } }   // the bell (notify/notify.php)
require $app . '/sync/sync-store.php';

$n = 0; $f = 0;
function ok($c, $what) { global $n, $f; $n++; if (!$c) $f++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
$T = fn(string $ny) => (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp() * 1000;
$fill = fn(string $id, string $acct, string $side, int $qty, float $px, string $ny, array $x = []) => $x + ['id' => $id, 'account' => $acct, 'contract' => 'NQ 12-26', 'side' => $side, 'qty' => $qty, 'price' => $px, 'ts' => $T($ny), 'point_value' => 20];
$put = function (string $uid, string $col, array $d) use ($pdo) {
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $d['id'], json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z']);
};
$trades = function (string $uid) use ($pdo) { $o = []; foreach ($pdo->query("SELECT id, data FROM documents WHERE collection = 'trades' AND user_id = " . $pdo->quote($uid) . ' ORDER BY id') as $r) $o[$r['id']] = json_decode($r['data'], true); return $o; };
$raw = fn(string $uid, string $id) => (string) $pdo->query("SELECT data FROM documents WHERE collection = 'trades' AND user_id = " . $pdo->quote($uid) . ' AND id = ' . $pdo->quote($id))->fetchColumn();
$sa = fn(string $uid, string $name) => $pdo->query('SELECT * FROM sync_accounts WHERE user_id = ' . $pdo->quote($uid) . ' AND ext_id = ' . $pdo->quote($name))->fetch();

// 1. the personal key
$k1 = sync_new_key($pdo, 'u1', 'ninjatrader');
ok(preg_match('/^swk_[0-9a-f]{40}$/', $k1['key']) === 1 && $k1['hint'] === substr($k1['key'], -4) && sync_auth($pdo, $k1['key'])['user_id'] === 'u1', 'a new key (swk_ + 40 hex) opens the sync for its trader');
ok((int) $pdo->query("SELECT COUNT(*) FROM sync_connections WHERE key_hash = '" . hash('sha256', $k1['key']) . "'")->fetchColumn() === 1 && !$pdo->query("SELECT 1 FROM sync_connections WHERE key_hash = '" . $k1['key'] . "'")->fetch(), 'only the key\'s hash is stored, never the key');
$k2 = sync_new_key($pdo, 'u1', 'ninjatrader');
ok(sync_auth($pdo, $k1['key']) === null && sync_auth($pdo, $k2['key']) !== null, 'a new key stops the previous one at once');
ok(sync_auth($pdo, 'swk_' . str_repeat('0', 40)) === null && sync_auth($pdo, 'abc') === null, 'an unknown or malformed key opens nothing');
$pdo->exec("UPDATE users SET disabled = 1 WHERE id = 'u1'"); $dis = sync_auth($pdo, $k2['key']); $pdo->exec("UPDATE users SET disabled = 0 WHERE id = 'u1'");
ok($dis === null, 'a disabled trader\'s key opens nothing');
$conn = sync_auth($pdo, $k2['key']);

// 2. executions of an account not linked yet: kept, nothing written
$day1 = [
    $fill('e1', 'APEX-123-01', 'buy', 1, 21000, '2026-10-07 10:00:00'), $fill('e2', 'APEX-123-01', 'sell', 1, 21010, '2026-10-07 10:05:00'),
    $fill('e3', 'APEX-123-01', 'sell', 2, 21020, '2026-10-07 11:00:00'), $fill('e4', 'APEX-123-01', 'buy', 2, 21000, '2026-10-07 11:20:00'),
    $fill('e5', 'APEX-123-01', 'buy', 1, 21050, '2026-10-07 14:00:00'),   // still open
];
$r = sync_receive($pdo, $conn, ['client' => 'Sweep NT8 1.0', 'accounts' => [['name' => 'APEX-123-01', 'connection' => 'Apex Rithmic', 'provider' => 'Rithmic', 'currency' => 'usd', 'cash' => 50210.5]], 'fills' => $day1]);
$st = sync_status($pdo, 'u1'); $a = $st['accounts'][0] ?? [];
ok($r['ok'] && $r['new'] === 5 && $r['trades']['created'] === 0 && !$trades('u1'), 'executions of an account not linked yet: 5 kept, no trade written');
ok($a['name'] === 'APEX-123-01' && $a['state'] === 'new' && $a['guess'] === ['firm' => 'apex', 'phase' => 'eval'] && $a['info']['connection'] === 'Apex Rithmic' && $a['info']['currency'] === 'USD' && $a['info']['cash'] === 50210.5, 'the account found: state new, « APEX- » → Apex evaluation, what NinjaTrader says about it');
ok($st['connections'][0]['client'] === 'Sweep NT8 1.0' && $st['connections'][0]['last_push_at'] > 0 && $st['connections'][0]['hint'] === $k2['hint'], 'the connection: add-on version, last push, key hint');
$r = sync_receive($pdo, $conn, ['fills' => $day1]);
ok($r['new'] === 0 && $r['changed'] === 0, 'the same executions sent again: nothing new, nothing changed');
$r = sync_receive($pdo, $conn, ['accounts' => [['name' => 'Sim101'], ['name' => 'Playback101']], 'fills' => []]);
ok($r['accounts'] === [['name' => 'Sim101', 'state' => 'ignored'], ['name' => 'Playback101', 'state' => 'ignored']], 'NinjaTrader\'s simulation accounts (Sim101, Playback101) start « ignored »');
$nf = array_values(array_filter(Notify::$sent, fn($x) => $x[1] === 'sync_found'));
ok(count($nf) === 1 && $nf[0][0] === 'u1' && $nf[0][2] === ['n' => 1, 'platform' => 'NinjaTrader 8'] && $nf[0][3]['action_url'] === '#settings/sync' && $nf[0][3]['dedupe_key'] === 'sync_found:ninjatrader:' . gmdate('Y-m-d'),
    'a new account to link → one bell notification « NinjaTrader 8: 1 account found », opening the link sheet (none for the same executions again, none for simulation accounts)');

// 3. linking: preview, then the trade typed by hand is completed (its notes and screenshot stay), the others are added
$put('u1', 'accounts', ['id' => 'acc1', 'name' => 'Apex 1', 'fee_rt_c' => 400]);
$put('u1', 'trades', ['id' => 'man1', 'account_id' => 'acc1', 'instrument' => 'NQ', 'date' => '2026-10-07', 'session_date' => true, 'entry_time' => '10:01', 'direction' => 'long', 'contracts' => 1,
    'entry' => 21000, 'exit' => 21010, 'pnl_c' => 20000, 'notes' => 'Clean break', 'shots' => ['up1'], 'review' => new stdClass(), 'import_key' => 'tv:NQZ6:123']);
$put('u1', 'trades', ['id' => 'man2', 'account_id' => 'acc1', 'instrument' => 'NQ', 'date' => '2026-10-07', 'session_date' => true, 'entry_time' => '15:30', 'direction' => 'long', 'contracts' => 1, 'pnl_c' => 5000]);
$pv = sync_preview($pdo, 'u1', $a['id'], 'acc1');
ok($pv === ['add' => 1, 'complete' => 1, 'manual' => 1, 'open' => 1] && count($trades('u1')) === 2, 'preview: 1 to add, 1 typed by hand to complete, 1 typed by hand with no equivalent, 1 position open; nothing written');
$EVENTS = []; $REF = 0;
$r = sync_link($pdo, 'u1', $a['id'], 'acc1');
$all = $trades('u1'); $m1 = $all['man1'];
ok($r['ok'] && $r['created'] === 1 && $r['merged'] === 1 && count($all) === 3 && $sa('u1', 'APEX-123-01')['state'] === 'linked', 'linked: 1 trade added, 1 completed, the one typed by hand without equivalent stays (3 trades, no double)');
ok($m1['notes'] === 'Clean break' && $m1['shots'] === ['up1'] && $m1['source'] === 'ninjatrader' && count($m1['executions']) === 2 && $m1['entry_time'] === '10:00' && $m1['import_key'] === 'tv:NQZ6:123', 'completed trade: notes, screenshot and CSV import key kept; platform fields written (source, executions, 10:00)');
ok(strpos($raw('u1', 'man1'), '"review":{}') !== false, 'an empty review stays {} (not [])');
$sy = array_values(array_filter($all, fn($t) => str_starts_with($t['id'], 'sy-')))[0] ?? [];
ok(($sy['direction'] ?? '') === 'short' && $sy['contracts'] === 2 && $sy['pnl_c'] === 80000 && $sy['fees_c'] === 800 && $sy['fees_auto'] === true && $sy['account_id'] === 'acc1' && $sy['user_id'] === 'u1' && $sy['notes'] === '' && $sy['discipline'] === [] && strpos($raw('u1', $sy['id']), '"discipline":{}') !== false, 'added trade: short 2, +$800, fees from the account ($4 × 2), empty journal fields ready ({} for the checklist)');
ok(count($EVENTS) === 1 && $EVENTS[0][2] === '2026-10-07' && $REF === 1, 'one game event for the trading day touched (not one per trade), referral check once');
ok($all['man2']['pnl_c'] === 5000 && !isset($all['man2']['source']), 'the trade typed by hand with no equivalent is not touched');

// 4. sent again → nothing rewritten
$before = $pdo->query("SELECT GROUP_CONCAT(updated_at) FROM documents WHERE collection = 'trades'")->fetchColumn(); $EVENTS = [];
$r = sync_receive($pdo, $conn, ['fills' => $day1]);
ok($r['trades'] === ['created' => 0, 'updated' => 0, 'merged' => 0] && !$EVENTS && $pdo->query("SELECT GROUP_CONCAT(updated_at) FROM documents WHERE collection = 'trades'")->fetchColumn() === $before, 'the same executions after linking: nothing rewritten, no event');

// 5. the trader writes notes, then an amended execution arrives: the platform's fields change, the notes stay
$doc = json_decode($raw('u1', $sy['id'])); $doc->notes = 'Faded the open'; $doc->tags = ['A+']; $doc->stop = 21040;
$pdo->prepare("UPDATE documents SET data = ? WHERE user_id = 'u1' AND collection = 'trades' AND id = ?")->execute([json_encode($doc, JSON_UNESCAPED_SLASHES), $sy['id']]);
$r = sync_receive($pdo, $conn, ['fills' => [$fill('e4', 'APEX-123-01', 'buy', 2, 21005, '2026-10-07 11:20:00')]]);
$t = $trades('u1')[$sy['id']];
ok($r['changed'] === 1 && $r['trades']['updated'] === 1 && $t['exit'] == 21005 && $t['pnl_c'] === 60000 && $t['notes'] === 'Faded the open' && $t['tags'] === ['A+'] && $t['stop'] === 21040, 'amended execution (exit 21,005): P&L +$600, the trader\'s notes, tags and stop kept');

// 6. the trader deletes a synced trade: never written again; Undo puts it back and it is followed again
$keep = $raw('u1', $sy['id']);
$pdo->exec("DELETE FROM documents WHERE collection = 'trades' AND id = '" . $sy['id'] . "'");
$r = sync_receive($pdo, $conn, ['fills' => [$fill('e4', 'APEX-123-01', 'buy', 2, 21004, '2026-10-07 11:20:00')]]);
ok($r['trades']['created'] === 0 && $r['trades']['updated'] === 0 && !isset($trades('u1')[$sy['id']]), 'a synced trade deleted by the trader is not written again, even when its executions change');
$pdo->prepare("INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES ('u1', 'trades', ?, ?, 'x', 'x')")->execute([$sy['id'], $keep]);   // Undo
$r = sync_receive($pdo, $conn, ['fills' => [$fill('e4', 'APEX-123-01', 'buy', 2, 21003, '2026-10-07 11:20:00')]]);
$t = $trades('u1')[$sy['id']];
ok($r['trades']['updated'] === 1 && $t['exit'] == 21003 && $t['notes'] === 'Faded the open', 'Undo puts it back: followed again, notes kept');

// 7. a removed execution leaves the trade as it is (the trader's data); the open position closes into a new trade
$r = sync_receive($pdo, $conn, ['fills' => [$fill('e6', 'APEX-123-01', 'sell', 1, 21060, '2026-10-07 14:10:00')]]);
ok($r['trades']['created'] === 1 && count($trades('u1')) === 4, 'the open position is closed by a new execution → a new trade');

// 8. an earlier execution arrives late: the same document takes the trade (no double, notes kept)
$late = array_values(array_filter($trades('u1'), fn($t) => ($t['executions'][0]['id'] ?? '') === 'e5'))[0];
$doc = json_decode($raw('u1', $late['id'])); $doc->notes = 'Breakout'; $pdo->prepare("UPDATE documents SET data = ? WHERE user_id = 'u1' AND collection = 'trades' AND id = ?")->execute([json_encode($doc, JSON_UNESCAPED_SLASHES), $late['id']]);
$r = sync_receive($pdo, $conn, ['fills' => [$fill('e5b', 'APEX-123-01', 'buy', 1, 21040, '2026-10-07 13:59:00'), $fill('e6b', 'APEX-123-01', 'sell', 1, 21062, '2026-10-07 14:11:00')]]);
$t = $trades('u1')[$late['id']] ?? [];
ok(count($trades('u1')) === 4 && $r['trades']['updated'] === 1 && ($t['contracts'] ?? 0) === 2 && ($t['executions'][0]['id'] ?? '') === 'e5b' && ($t['notes'] ?? '') === 'Breakout', 'an earlier execution arrives late (with its exit): same document updated (2 contracts, starts at 13:59), notes kept, no double');

// 9. copy trading: the same trade on a second linked account → one copy group on both documents
$put('u1', 'accounts', ['id' => 'acc2', 'name' => 'Apex 2']);
sync_receive($pdo, $conn, ['fills' => [$fill('c1', 'APEX-123-02', 'buy', 1, 21000, '2026-10-07 10:00:20'), $fill('c2', 'APEX-123-02', 'sell', 1, 21010, '2026-10-07 10:05:00')]]);
$r = sync_link($pdo, 'u1', $sa('u1', 'APEX-123-02')['id'], 'acc2');
$all = $trades('u1'); $c = array_values(array_filter($all, fn($t) => ($t['account_id'] ?? '') === 'acc2'))[0];
ok($r['created'] === 1 && !empty($c['copy_group']) && str_starts_with($c['copy_group'], 'cg-') && ($all['man1']['copy_group'] ?? '') === $c['copy_group'], 'same minute, instrument and side on two accounts → one copy group, written on both documents');
ok(sync_link($pdo, 'u1', $sa('u1', 'APEX-123-02')['id'], 'acc1')['error'] === 'taken', 'a Sweep account fed by one platform account only (« taken »)');

// 10. the plan: a frozen account receives nothing; its executions wait and are written once it is allowed
$put('u1', 'accounts', ['id' => 'acc3', 'name' => 'Lucid 1']); $FROZEN = ['acc3'];
sync_receive($pdo, $conn, ['fills' => [$fill('z1', 'LUCID-9', 'buy', 1, 100, '2026-10-08 10:00:00'), $fill('z2', 'LUCID-9', 'sell', 1, 101, '2026-10-08 10:01:00')]]);
$r = sync_link($pdo, 'u1', $sa('u1', 'LUCID-9')['id'], 'acc3');
ok($r['ok'] && ($r['error'] ?? '') === 'plan' && $sa('u1', 'LUCID-9')['last_error'] === 'plan' && !array_filter($trades('u1'), fn($t) => ($t['account_id'] ?? '') === 'acc3'), 'frozen account (Free plan): link kept, nothing written, error « plan »');
$FROZEN = [];
$r = sync_receive($pdo, $conn, ['fills' => [$fill('z3', 'LUCID-9', 'buy', 1, 100, '2026-10-08 10:30:00'), $fill('z4', 'LUCID-9', 'sell', 1, 102, '2026-10-08 10:31:00')]]);
ok($r['trades']['created'] === 2 && $sa('u1', 'LUCID-9')['last_error'] === null, 'allowed again: the next push writes the waiting trades too (2)');

// 11. the record limit: all or nothing
$put('u1', 'accounts', ['id' => 'acc4', 'name' => 'TPT 1']);
sync_receive($pdo, $conn, ['fills' => [$fill('l1', 'TPT-1', 'buy', 1, 100, '2026-10-08 10:00:00'), $fill('l2', 'TPT-1', 'sell', 1, 101, '2026-10-08 10:01:00')]]);
$GLOBALS['MAX_DOCS'] = (int) $pdo->query("SELECT COUNT(*) FROM documents WHERE user_id = 'u1'")->fetchColumn();
$cnt = $GLOBALS['MAX_DOCS'];
$r = sync_link($pdo, 'u1', $sa('u1', 'TPT-1')['id'], 'acc4');
ok(($r['error'] ?? '') === 'limit' && (int) $pdo->query("SELECT COUNT(*) FROM documents WHERE user_id = 'u1'")->fetchColumn() === $cnt && $sa('u1', 'TPT-1')['last_error'] === 'limit', 'record limit reached: nothing written (rolled back), error « limit »');
unset($GLOBALS['MAX_DOCS']);

// 12. the Sweep account is deleted: the link drops, nothing is written
$pdo->exec("DELETE FROM documents WHERE collection = 'accounts' AND id = 'acc2'");
$r = sync_receive($pdo, $conn, ['fills' => [$fill('c3', 'APEX-123-02', 'buy', 1, 1, '2026-10-08 10:00:00'), $fill('c4', 'APEX-123-02', 'sell', 1, 2, '2026-10-08 10:01:00')]]);
$x = $sa('u1', 'APEX-123-02');
ok($x['state'] === 'new' && $x['account_id'] === null && $x['last_error'] === 'account_gone' && $r['trades']['created'] === 0, 'Sweep account deleted: back to « new », nothing written');

// 13. ignored: kept, never written
sync_set_state($pdo, 'u1', $x['id'], 'ignored');
$r = sync_receive($pdo, $conn, ['fills' => [$fill('c5', 'APEX-123-02', 'buy', 1, 1, '2026-10-09 10:00:00'), $fill('c6', 'APEX-123-02', 'sell', 1, 2, '2026-10-09 10:01:00')]]);
ok($r['new'] === 2 && $r['trades']['created'] === 0 && $sa('u1', 'APEX-123-02')['state'] === 'ignored', 'ignored account: executions kept, nothing written');

// 14. another trader never sees or receives anything of u1; limits and bad executions
$put('u2', 'accounts', ['id' => 'acc1', 'name' => 'Same id, other trader']);
ok(sync_link($pdo, 'u2', $a['id'], 'acc1')['error'] === 'not_found' && array_slice(sync_status($pdo, 'u2'), 0, 2) === ['connections' => [], 'accounts' => []], 'another trader cannot link or see u1\'s accounts');
$big = []; for ($i = 0; $i <= SYNC_MAX_FILLS; $i++) $big[] = $fill("b$i", 'APEX-123-01', 'buy', 1, 1, '2026-10-09 10:00:00');
ok((sync_receive($pdo, $conn, ['fills' => $big])['error'] ?? '') === 'too_many', 'more than ' . SYNC_MAX_FILLS . ' executions in one push → refused whole');
$r = sync_receive($pdo, $conn, ['fills' => [$fill('v1', 'APEX-123-01', 'buy', 1, 1, '2019-12-31 10:00:00'), $fill('v2', 'APEX-123-01', 'buy', 1, 1, '2099-01-01 10:00:00'), ['id' => 'v3', 'contract' => 'NQ 12-26'], 'x', $fill('v4', '', 'buy', 1, 1, '2026-10-09 10:00:00')]]);
ok($r['skipped'] === 5 && $r['new'] === 0, 'executions before 2020, in the future, without account or fields → skipped (5)');

// 14b. a second platform (Quantower): its own key and accounts, its trades say « quantower »
ok(sync_client_platform('Sweep NT8 1.0.0') === 'ninjatrader' && sync_client_platform('Sweep Quantower 1.0.0') === 'quantower' && sync_client_platform('') === null && sync_client_platform('Other 1.0') === null, 'each add-on names its platform (« Sweep NT8 … », « Sweep Quantower … »)');
$kq = sync_new_key($pdo, 'u1', 'quantower'); $cq = sync_auth($pdo, $kq['key']);
ok($cq['platform'] === 'quantower' && sync_auth($pdo, $k2['key'])['platform'] === 'ninjatrader', 'one key per platform: a Quantower key leaves the NinjaTrader 8 key working');
$r = sync_receive($pdo, $cq, ['client' => 'Sweep Quantower test', 'accounts' => [['name' => 'Sim202', 'connection' => 'Simulator'], ['name' => 'PA-APEX-9-01', 'connection' => 'Rithmic']], 'fills' => [$fill('q1', 'PA-APEX-9-01', 'buy', 1, 21000, '2026-10-09 10:00:00'), $fill('q2', 'PA-APEX-9-01', 'sell', 1, 21004, '2026-10-09 10:03:00')]]);
$st = sync_status($pdo, 'u1'); $q = []; foreach ($st['accounts'] as $x) if ($x['platform'] === 'quantower') $q[$x['name']] = $x;
ok(count($q) === 2 && $q['Sim202']['state'] === 'new' && $q['Sim202']['guess'] === null && $q['PA-APEX-9-01']['guess'] === ['firm' => 'apex', 'phase' => 'funded'], 'Quantower accounts listed under Quantower: « Sim202 » is not taken for a NinjaTrader simulation there, Apex still guessed');
ok(array_keys($st['addons']) === ['ninjatrader', 'quantower'] && ($st['addons']['ninjatrader']['url'] ?? '') === 'api/sync/addon?platform=ninjatrader', 'status: each platform\'s add-on (download address, or null while it does not exist)');
$put('u1', 'accounts', ['id' => 'accq', 'name' => 'Apex PA 9']);
$r = sync_link($pdo, 'u1', $q['PA-APEX-9-01']['id'], 'accq'); $tq = array_values(array_filter($trades('u1'), fn($x) => ($x['account_id'] ?? '') === 'accq'));
ok(($r['created'] ?? 0) === 1 && count($tq) === 1 && $tq[0]['source'] === 'quantower' && $tq[0]['pnl_c'] === 8000 && str_starts_with($tq[0]['import_key'], 'sync:quantower:'), 'linked: the Quantower trade (+$80) says source « quantower », import key sync:quantower:…');

// 14c. Admin › Sync: per platform, then one row per key with where the trader is (never a key or an execution)
foreach (['username', 'email', 'first_name', 'last_name'] as $col) $pdo->exec("ALTER TABLE users ADD COLUMN $col TEXT");
$pdo->exec("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"); $pdo->exec("ALTER TABLE users ADD COLUMN is_internal INTEGER NOT NULL DEFAULT 0");
$pdo->exec("UPDATE users SET username = 'lea@t.dev', email = 'lea@t.dev', first_name = 'Lea', last_name = 'Test' WHERE id = 'u1'");
$pdo->exec("UPDATE users SET username = 'max@t.dev', email = 'max@t.dev', is_internal = 1 WHERE id = 'u2'");
$k3 = sync_new_key($pdo, 'u2', 'quantower');
$ad = sync_admin($pdo); $row = function (string $uid, string $pl) use ($ad) { foreach ($ad['rows'] as $r) if ($r['user_id'] === $uid && $r['platform'] === $pl) return $r; return null; };
$q1 = $row('u1', 'quantower'); $n1 = $row('u1', 'ninjatrader'); $q2 = $row('u2', 'quantower');
ok($q1 && $q1['state'] === 'ok' && $q1['name'] === 'Lea Test' && $q1['email'] === 'lea@t.dev' && $q1['client'] === 'Sweep Quantower test' && $q1['accounts'] === ['new' => 1, 'linked' => 1, 'ignored' => 0] && $q1['trades'] === 1 && $q1['trades_7d'] === 1 && $q1['last_seen_at'] > 0, 'Admin › Sync: Quantower, linked and writing trades → « ok » (1 linked, 1 to link, 1 trade)');
ok($n1 && $n1['state'] === 'error' && in_array('limit', $n1['errors'], true), 'Admin › Sync: NinjaTrader 8 with an account over the record limit → « error » (limit)');
ok($q2 && $q2['state'] === 'never' && $q2['last_seen_at'] === null && $q2['team'] === true && $q2['name'] === 'max@t.dev', 'Admin › Sync: a key never used by the add-on → « never »; an internal trader is marked team');
ok(array_search($q2, $ad['rows'], true) > array_search($q1, $ad['rows'], true) && $ad['platforms']['quantower'] === ['traders' => 2, 'seen_24h' => 1, 'linked' => 1, 'trades_7d' => 1] && $ad['platforms']['ninjatrader']['traders'] === 1, 'Admin › Sync: most recently seen first; per platform: traders, seen within 24 h, accounts linked, trades in 7 days');
$js = json_encode($ad);
ok(!str_contains($js, 'swk_') && !str_contains($js, $k3['hint']) && !str_contains($js, 'key_hash') && !str_contains($js, '21004'), 'Admin › Sync: never a key, a key hint or an execution');
$pdo->exec("UPDATE sync_connections SET last_seen_at = 1 WHERE user_id = 'u2'"); $pdo->exec("INSERT INTO sync_accounts (id, user_id, platform, ext_id, state, created_at, updated_at) VALUES ('sa_x', 'u2', 'quantower', 'X-1', 'new', 1, 1)");
ok(($row2 = (function () use ($pdo) { foreach (sync_admin($pdo)['rows'] as $r) if ($r['user_id'] === 'u2') return $r; })()) && $row2['state'] === 'to_link', 'Admin › Sync: accounts found, none linked → « to_link »');
$pdo->exec("DELETE FROM sync_accounts WHERE id = 'sa_x'");
ok((function () use ($pdo) { foreach (sync_admin($pdo)['rows'] as $r) if ($r['user_id'] === 'u2') return $r['state']; })() === 'no_accounts', 'Admin › Sync: add-on seen, no account found → « no_accounts »');
ok(($q1c = $row('u1', 'quantower')['contracts'] ?? null) && $q1c[0]['contract'] === 'NQ 12-26' && $q1c[0]['instrument'] === 'NQ' && $q1c[0]['known'] === true && $q1c[0]['n'] === 2 && $ad['unknown'] === [], 'Admin › Sync: the contracts received (30 days) with the instrument Sweep reads (« NQ 12-26 » → NQ, 2 executions); none unknown');
sync_receive($pdo, sync_auth($pdo, $k3['key']), ['fills' => [$fill('w1', 'TX-1', 'buy', 1, 21000, '2026-10-09 10:00:00', ['contract' => 'CON.F.US.MNQ.Z25'])]]);
$ad2 = sync_admin($pdo); $u2c = null; foreach ($ad2['rows'] as $r) if ($r['user_id'] === 'u2') $u2c = $r['contracts'];
ok($u2c && $u2c[0]['contract'] === 'CON.F.US.MNQ.Z25' && $u2c[0]['known'] === false && $ad2['unknown'] === [['platform' => 'quantower', 'contract' => 'CON.F.US.MNQ.Z25', 'instrument' => 'CON.F.US.MNQ.']], 'Admin › Sync: a contract Sweep does not recognize (« CON.F.US.MNQ.Z25 ») is flagged on its row and listed apart');

// 15. a trader deletes their Sweep account: everything of the sync goes
sync_delete_user($pdo, 'u1');
$left = 0; foreach (['sync_fills', 'sync_trades', 'sync_accounts', 'sync_connections'] as $tb) $left += (int) $pdo->query("SELECT COUNT(*) FROM $tb WHERE user_id = 'u1'")->fetchColumn();
ok($left === 0 && sync_auth($pdo, $k2['key']) === null, 'account deleted: keys, executions, accounts found and links removed');

array_map('unlink', glob($tmp . '/*')); rmdir($tmp);
echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
