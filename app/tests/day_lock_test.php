<?php
declare(strict_types=1);
/**
 * Sweep — the end-of-day lock (1 Nov., brief avance 4), on a throwaway SQLite database, the clock pinned (SWEEP_GAME_NOW), the push
 * service replaced by a file (SWEEP_PUSH_MOCK: no message leaves):
 *   php tests/day_lock_test.php
 *  - the lock is reached by the max loss (the tightest of the plan, the standing limits and the account's daily limit), by the
 *    max number of trades, by a copied trade (a copy group counts once) and by a synced trade (the add-on's own path);
 *  - it is kept until the day ends at 18:00 ET, even if a trade is deleted or edited, then lifted (the next session starts free);
 *  - edited limits apply from the next session only (settings.day_lock: from / was); recomputeDay flags the trades past the plan;
 *  - at the moment it locks: one notification (g_lock, never capped) and one push (kind « lock », the device's language), once a day;
 *  - closing a locked day (the review, the platform balance checked) counts for the streak.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-lock-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$cfg = ['notifications' => []];
putenv('SWEEP_PUSH_MOCK=' . $tmp . '/sent.jsonl');
require $app . '/push/web-push.php';
require_once __DIR__ . '/push_ua.php';
file_put_contents($tmp . '/push-config.php', '<?php return ' . var_export(wp_new_keys(), true) . ";\n");
define('SWEEP_PUSH_CONFIG', $tmp . '/push-config.php');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require_once $app . '/notify/notify.php';   // (with its listeners: the game recomputes the day on each saved trade, as in api.php)
require $app . '/game/game.php';
require $app . '/sync/sync-store.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema(); Notify::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
// a document saved the way api.php saves it: written, then its event (the game recomputes the day)
$save = function (string $uid, string $col, array $d) use ($pdo) {
    $prev = $pdo->query('SELECT data FROM documents WHERE user_id = ' . $pdo->quote($uid) . ' AND collection = ' . $pdo->quote($col) . ' AND id = ' . $pdo->quote($d['id']))->fetchColumn();
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $d['id'], json_encode($d), $d['created_at'] ?? '2026-10-30T14:00:00Z', '2026-10-30T14:00:00Z']);
    nt_doc_event($uid, $col, $d['id'], $d, $prev === false ? null : json_decode((string) $prev, true));
};
$del = function (string $uid, string $col, string $id) use ($pdo) {
    $prev = $pdo->query('SELECT data FROM documents WHERE user_id = ' . $pdo->quote($uid) . ' AND collection = ' . $pdo->quote($col) . ' AND id = ' . $pdo->quote($id))->fetchColumn();
    $pdo->prepare('DELETE FROM documents WHERE user_id = ? AND collection = ? AND id = ?')->execute([$uid, $col, $id]);
    nt_doc_event($uid, $col, $id, null, json_decode((string) $prev, true));
};
$tr = fn(string $id, string $acc, int $pnl, string $hm, array $x = []) => $x + ['id' => $id, 'account_id' => $acc, 'instrument' => 'NQ', 'direction' => 'long', 'contracts' => 1, 'pnl_c' => $pnl, 'date' => '2026-10-30', 'entry_time' => $hm, 'exit_time' => $hm, 'session_date' => true];
$lock = fn(string $uid, string $d) => GameEngine::dayState($uid, $d)['lock'];
$bell = fn(string $uid) => $pdo->query("SELECT type, category, dedupe_key, quiet FROM notifications WHERE user_id = " . $pdo->quote($uid) . " AND type = 'g_lock'")->fetchAll();
$sent = function (): array { global $tmp; $l = is_file("$tmp/sent.jsonl") ? file("$tmp/sent.jsonl", FILE_IGNORE_NEW_LINES) : []; @unlink("$tmp/sent.jsonl"); return array_map(fn($x) => json_decode($x, true), $l); };
$open = fn(array $x, array $k) => json_decode((string) ua_decrypt(base64_decode($x['body']), $k['pem'], wp_b64u_d($k['auth'])), true);
$D = '2026-10-30'; $N = '2026-11-02';   // Friday; the next session: Monday
$acc = fn(string $uid, string $id, int $dll) => $save($uid, 'accounts', ['id' => $id, 'name' => 'Apex ' . $id, 'status' => 'active', 'rules' => $dll ? ['dll_c' => $dll, 'dd_c' => 250000] : ['dd_c' => 250000]]);

// 0. the limits in force on a day
$s = ['day_lock' => ['loss_c' => 20000, 'trades' => 2, 'from' => $N, 'was' => ['loss_c' => 50000, 'trades' => 0]]];
// (3 Nov., the account guardian's stop rule) losing trades in a row: 2 unless set (0 = off), with the same from / was
$ok(GameEngine::standingLimits($s, $D) === ['loss_c' => 50000, 'trades' => 0, 'losses' => 2] && GameEngine::standingLimits($s, $N) === ['loss_c' => 20000, 'trades' => 2, 'losses' => 2]
    && GameEngine::standingLimits(['day_lock' => ['loss_c' => 30000, 'from' => '']], $D) === ['loss_c' => 30000, 'trades' => 0, 'losses' => 2] && GameEngine::standingLimits([], $D) === ['loss_c' => 0, 'trades' => 0, 'losses' => 2]
    && GameEngine::standingLimits(['day_lock' => ['losses' => 0, 'from' => $N, 'was' => ['losses' => 3]]], $D)['losses'] === 3 && GameEngine::standingLimits(['day_lock' => ['losses' => 0, 'from' => $N, 'was' => ['losses' => 3]]], $N)['losses'] === 0,
    'standing limits: the edited values from the next session (from), the values they replaced before it (was), none when never set (2 losses in a row by default)');

// 1. the max loss: the plan's $500, tighter than the account's $1,000
$at("$D 08:00"); GameEngine::profile('u1');
$k = ua_keys(); wp_subscribe($pdo, 'u1', ['endpoint' => 'https://fcm.googleapis.com/fcm/send/u1', 'keys' => ['p256dh' => $k['p256dh'], 'auth' => $k['auth']], 'lang' => 'fr']);
$acc('u1', 'a1', 100000);
$save('u1', 'journals', ['id' => $D, 'pre' => ['bias' => 'bullish', 'max_loss' => '500', 'max_trades' => '5', 'saved_at' => GameEngine::ts()]]);
$at("$D 10:05"); $save('u1', 'trades', $tr('t1', 'a1', -30000, '10:00'));
$ok($lock('u1', $D) === null && !$bell('u1') && !$sent(), 'a −$300 trade, max loss $500: not locked, nothing sent');
$at("$D 10:35"); $save('u1', 'trades', $tr('t2', 'a1', -25000, '10:30'));
$l = $lock('u1', $D);
$ok(($l['why'] ?? '') === 'loss' && $l['loss_c'] === 50000 && $l['n'] === 2 && $l['net_c'] === -55000 && $l['at'] === GameEngine::ts(), 'a −$250 trade: the day locks by the max loss ($500, the plan tighter than the account), at that moment (' . json_encode($l) . ')');
$b = $bell('u1');
$ok(count($b) === 1 && $b[0]['category'] === 'prop_alerts' && $b[0]['dedupe_key'] === "lock:$D" && (int) $b[0]['quiet'] === 0, 'one notification in the bell (g_lock, with the prop firm alerts: never capped nor quiet)');
$p = $sent(); $m = $p ? $open($p[0], $k) : null;
$ok(count($p) === 1 && ($m['title'] ?? '') === 'Journée fermée : ta limite est atteinte.' && ($m['tag'] ?? '') === 'sweep-lock' && ($m['url'] ?? '') === '#dashboard' && ($p[0]['headers']['Topic'] ?? '') === 'lock', 'one push to the phone, kind « lock », in the device\'s language (' . json_encode($m, JSON_UNESCAPED_UNICODE) . ')');
$at("$D 10:50"); $save('u1', 'trades', $tr('t3', 'a1', 100000, '10:45'));
$det = array_column(GameEngine::dayState('u1', $D)['detail'], 'v', 'id');
$ok(in_array('over_max_loss', $det['t3'] ?? [], true) && !in_array('over_max_loss', $det['t2'] ?? [], true), 'recomputeDay flags the trade taken past the max loss (over_max_loss), not the one that reached it');
$ok(($lock('u1', $D)['why'] ?? '') === 'loss' && count($bell('u1')) === 1 && !$sent(), 'a winning trade after it: still locked, nothing sent again (the entry is never blocked)');
$del('u1', 'trades', 't2'); $save('u1', 'trades', $tr('t1', 'a1', 50000, '10:00'));
$ok(($lock('u1', $D)['why'] ?? '') === 'loss' && $lock('u1', $D)['n'] === 2, 'the losing trade deleted, the first one edited to a win: the lock reached stays (kept as it was)');
$at("$D 17:59"); GameEngine::recomputeDay('u1', $D);
$ok(GameEngine::today() === $D && $lock('u1', $D) !== null, '17:59 ET: the day is still locked');
// closing the locked day: the review and the account checked on its platform → it counts for the streak
$at("$D 17:20"); $save('u1', 'journals', ['id' => $D, 'pre' => ['bias' => 'bullish', 'max_loss' => '500', 'max_trades' => '5'], 'post' => ['followed' => 'partly', 'discipline' => 3, 'grade' => 'C', 'reviewed_at' => '2026-10-30T21:20:00Z', 'bal' => [['acc' => 'a1', 'bal_c' => 5000000]]]]);
$g = $pdo->query("SELECT is_valid_streak, review_done FROM game_days WHERE user_id = 'u1' AND trading_day = '$D'")->fetch();
$ok((int) $g['review_done'] === 1 && (int) $g['is_valid_streak'] === 1 && $lock('u1', $D) !== null, 'closing the locked day (review, balance checked): the day counts for the streak, the lock unchanged');
$at("$D 18:00");
$ok(GameEngine::today() === '2026-10-31' && GameEngine::dayState('u1', GameEngine::today())['lock'] === null, '18:00 ET: the next trading day starts without the lock (lifted)');
GameEngine::recomputeDay('u1', $D);
$ok(count($bell('u1')) === 1 && $lock('u1', $D)['why'] === 'loss', 'the closed day keeps its record (one notification in all)');

// 2. the max number of trades: the standing limit (2) tighter than the plan's (3), never a day off counted
$at("$D 08:00"); GameEngine::profile('u2'); $acc('u2', 'b1', 0);
$save('u2', 'meta', ['id' => 'settings', 'day_lock' => ['loss_c' => 0, 'trades' => 2, 'from' => '']]);
$save('u2', 'journals', ['id' => $D, 'pre' => ['bias' => 'bullish', 'max_loss' => '900', 'max_trades' => '3']]);
$at("$D 10:05"); $save('u2', 'trades', $tr('s1', 'b1', 10000, '10:00'));
$ok($lock('u2', $D) === null, '1 trade of 2: not locked');
$at("$D 10:35"); $save('u2', 'trades', $tr('s2', 'b1', 15000, '10:30'));
$l = $lock('u2', $D);
$ok(($l['why'] ?? '') === 'trades' && $l['trades'] === 2 && $l['loss_c'] === 90000 && count($bell('u2')) === 1, 'the 2nd trade: locked by the number of trades (Settings 2, tighter than the plan\'s 3), even on winning trades');
$sent();

// 3. edited limits apply from the next session only
$at("$D 08:00"); GameEngine::profile('u3'); $acc('u3', 'c1', 0);
$save('u3', 'meta', ['id' => 'settings', 'day_lock' => ['loss_c' => 20000, 'trades' => 0, 'from' => '2026-10-31', 'was' => ['loss_c' => 100000, 'trades' => 0]]]);
$at("$D 10:05"); $save('u3', 'trades', $tr('r1', 'c1', -30000, '10:00'));
$ok($lock('u3', $D) === null, 'the max loss lowered to $200 today: today keeps $1,000, a −$300 day is not locked');
$at("$N 10:05"); $save('u3', 'trades', $tr('r2', 'c1', -30000, '10:00', ['date' => $N]));
$ok(($lock('u3', $N)['why'] ?? '') === 'loss' && $lock('u3', $N)['loss_c'] === 20000, 'the next session (Monday): the new $200 applies, a −$300 trade locks');
$at("$N 10:20"); $save('u3', 'trades', $tr('r3', 'c1', -90000, '11:00'));
$ok($lock('u3', $D) === null && GameEngine::dayState('u3', $D)['trades'] === 2, 'a loss added later to Friday (−$1,200 of $1,000): a past day never locks afterwards');
$sent();

// 4. a copied trade: one decision on two accounts counts once (trades and P&L)
$at("$D 08:00"); GameEngine::profile('u4'); $acc('u4', 'd1', 0); $acc('u4', 'd2', 0);
$save('u4', 'meta', ['id' => 'settings', 'day_lock' => ['loss_c' => 50000, 'trades' => 2]]);
$at("$D 10:05"); $save('u4', 'trades', $tr('k1', 'd1', -30000, '10:00', ['copy_group' => 'g1', 'created_at' => '2026-10-30T14:00:00Z'])); $save('u4', 'trades', $tr('k2', 'd2', -30000, '10:00', ['copy_group' => 'g1', 'created_at' => '2026-10-30T14:00:01Z']));
$ok($lock('u4', $D) === null, 'a −$300 trade copied on 2 accounts: 1 trade of 2 and −$300 of $500 (once), not locked');
$at("$D 10:35"); $save('u4', 'trades', $tr('k3', 'd1', -25000, '10:30', ['copy_group' => 'g2'])); $save('u4', 'trades', $tr('k4', 'd2', -25000, '10:30', ['copy_group' => 'g2']));
$l = $lock('u4', $D);
$ok(($l['why'] ?? '') === 'loss' && $l['n'] === 2 && $l['net_c'] === -55000 && count($bell('u4')) === 1, 'its copied loss of −$250: locked by the max loss (−$550, each copy once), one notification for the group (' . json_encode($l) . ')');
$sent();

// 5. a synced trade (NinjaTrader add-on: received, rebuilt and written by sync/, the game hears it like a typed one)
$at("$D 08:00"); GameEngine::profile('u5'); $pdo->exec("INSERT INTO users (id) VALUES ('u5')"); $acc('u5', 'e1', 0);
$save('u5', 'meta', ['id' => 'settings', 'day_lock' => ['loss_c' => 20000, 'trades' => 0]]);
$conn = sync_auth($pdo, sync_new_key($pdo, 'u5', 'ninjatrader')['key']);
$T = fn(string $ny) => (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp() * 1000;
$fl = fn(string $id, string $side, float $px, string $ny) => ['id' => $id, 'account' => 'APEX-9-01', 'contract' => 'NQ 12-26', 'side' => $side, 'qty' => 1, 'price' => $px, 'ts' => $T($ny), 'point_value' => 20];
sync_receive($pdo, $conn, ['accounts' => [['name' => 'APEX-9-01']], 'fills' => [$fl('f1', 'buy', 21000, "$D 10:00:00"), $fl('f2', 'sell', 21010, "$D 10:04:00")]]);
$sid = (string) $pdo->query("SELECT id FROM sync_accounts WHERE user_id = 'u5'")->fetchColumn();
$at("$D 10:06"); sync_link($pdo, 'u5', $sid, 'e1');
$ok($lock('u5', $D) === null, 'a synced +$200 trade: not locked');
$at("$D 10:41"); sync_receive($pdo, $conn, ['fills' => [$fl('f3', 'buy', 21020, "$D 10:30:00"), $fl('f4', 'sell', 21000, "$D 10:40:00"), $fl('f5', 'buy', 21000, "$D 10:50:00"), $fl('f6', 'sell', 20990, "$D 10:52:00")]]);
$l = $lock('u5', $D); $src = array_values(array_unique(array_map(fn($t) => $t['source'] ?? '', GameEngine::docs('u5', 'trades'))));
$ok(($l['why'] ?? '') === 'loss' && $l['net_c'] <= -20000 && count($bell('u5')) === 1 && $src === ['ninjatrader'], 'synced losses past the $200 max loss: locked by the add-on\'s own path, one notification (' . json_encode($l) . ')');

// 6. the phone: the lock's switch (on by default, no time), off = no push, the bell still says it
$ok(wp_prefs($pdo, 'u1')['lock'] === ['on' => true, 'at' => ''] && wp_times('lock') === [] && !wp_set_pref($pdo, 'u1', 'lock', ['at' => '17:00']), 'push « lock »: on by default, no time to choose');
$at("$D 08:00"); GameEngine::profile('u6'); $acc('u6', 'h1', 10000);
wp_subscribe($pdo, 'u6', ['endpoint' => 'https://fcm.googleapis.com/fcm/send/u6', 'keys' => ['p256dh' => $k['p256dh'], 'auth' => $k['auth']], 'lang' => 'es']);
wp_set_pref($pdo, 'u6', 'lock', ['on' => false]);
$at("$D 10:05"); $save('u6', 'trades', $tr('w1', 'h1', -12000, '10:00'));
$ok(($lock('u6', $D)['why'] ?? '') === 'loss' && $lock('u6', $D)['loss_c'] === 10000 && count($bell('u6')) === 1 && !$sent(), 'the account\'s own daily limit ($100, its preset) locks too; its push switched off: the bell only');

// 7. (3 Nov., the account guardian's stop rule) two losing trades in a row lock the day, under every money limit; kept (the day
//    closed with no new losing trade after it): the guardrail's reward; another loss saved after it: none; 0 in Settings: off
$xp = fn(string $uid, string $d) => (int) $pdo->query("SELECT COUNT(*) FROM xp_events WHERE user_id = " . $pdo->quote($uid) . " AND event_key = " . $pdo->quote("guardrail:$d"))->fetchColumn();
$review = fn(string $uid) => $save($uid, 'journals', ['id' => $D, 'post' => ['followed' => 'yes', 'discipline' => 4, 'grade' => 'B', 'reviewed_at' => '2026-10-30T21:20:00Z', 'tomorrow' => 'Smaller after a loss.']]);
foreach (['u7' => false, 'u8' => true] as $u => $more) {
    $at("$D 08:00"); GameEngine::profile($u); $acc($u, $u . 'a', 100000);
    $at("$D 10:05"); $save($u, 'trades', $tr($u . 't1', $u . 'a', -10000, '10:00', ['created_at' => '2026-10-30T14:05:00.000Z']));
    $ok($lock($u, $D) === null, "$u one loss of \$100 (daily limit \$1,000): not locked");
    $at("$D 10:20"); $save($u, 'trades', $tr($u . 't2', $u . 'a', -15000, '10:15', ['created_at' => '2026-10-30T14:20:00.000Z']));
    $l = $lock($u, $D);
    $ok(($l['why'] ?? '') === 'losses' && $l['losses'] === 2 && $l['n'] === 2, "$u a second loss in a row: the day locks by the stop rule (" . json_encode($l) . ')');
    if ($more) { $at("$D 10:40"); $save($u, 'trades', $tr($u . 't3', $u . 'a', -5000, '10:35', ['created_at' => '2026-10-30T14:40:00.000Z'])); }
    $at("$D 17:20"); $review($u);
    $ok($xp($u, $D) === ($more ? 0 : 1), $more ? "$u a loss saved after the stop: no reward for the stop rule" : "$u the day closed without a new loss: the guardrail's reward (kept its stop rule)");
}
$at("$D 08:00"); GameEngine::profile('u9'); $acc('u9', 'u9a', 100000); $save('u9', 'meta', ['id' => 'settings', 'day_lock' => ['losses' => 0]]);
$at("$D 10:05"); $save('u9', 'trades', $tr('u9t1', 'u9a', -10000, '10:00')); $save('u9', 'trades', $tr('u9t2', 'u9a', -10000, '10:10'));
$ok($lock('u9', $D) === null, 'the stop rule set to 0 in Settings: two losses do not lock');

echo "\n$pass passed, $fail failed\n";
if ($fail) echo "failed\n";
exit($fail ? 1 : 0);
