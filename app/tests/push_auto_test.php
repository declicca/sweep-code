<?php
declare(strict_types=1);
/**
 * Sweep — one message, the best channel (push/push-auto.php, brief « Notifications », 5 Nov. 2026), on a throwaway SQLite
 * database; the push service replaced by a file (SWEEP_PUSH_MOCK: no message leaves), test keys made here, no email sent:
 *   php tests/push_auto_test.php
 *  - the slot: never in the phone's quiet hours (21:00 to 7:00 on its own clock), never in the session except an account alert;
 *  - the phone first: the email waits 24 h and does not leave once the notification was opened or the trader came back; it
 *    leaves at once without a device, when the message is off, or for the account and its money (both at once);
 *  - the caps: 2 a day with the bell's reminders (then the next day), 5 a week, a group ignored 4 times (1 a week), 30 days away;
 *  - the four switches of the device (a group off: nothing), the language of each device, a device asleep skipped;
 *  - the account's moments: payout possible once per cycle, target reached with what is left, then « passed » once; in the bell too;
 *  - Sweep's news once in 28 days; the open link; an account deleted; « Sweep on your phone » (day 3) and its QR block.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-push-auto-' . bin2hex(random_bytes(4)); mkdir($tmp);
ini_set('error_log', $tmp . '/php.log'); putenv('SWEEP_TEST_DB=' . $tmp . '/t.db');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, first_name TEXT, last_name TEXT, lang TEXT, created_at TEXT, last_login TEXT, disabled INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, is_internal INTEGER NOT NULL DEFAULT 0)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool { return false; }
$GLOBALS['cfg'] = ['app_url' => 'https://app.makeitsweep.com', 'notifications' => []];
putenv('SWEEP_PUSH_MOCK=' . $tmp . '/sent.jsonl');
require $app . '/push/web-push.php';
require_once __DIR__ . '/push_ua.php';
file_put_contents($tmp . '/push-config.php', '<?php return ' . var_export(wp_new_keys(), true) . ";\n");
define('SWEEP_PUSH_CONFIG', $tmp . '/push-config.php');
require $app . '/notify/notify.php';
require $app . '/game/game.php';
require $app . '/push/push-auto.php';
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-auto.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema();
ml_schema($pdo); ma_schema(); Notify::schema();
ml_set_setting($pdo, 'mail_auto_since', '1');   // the first run is done (mail/mail-auto.php ma_init)
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$iso = fn(int $t) => gmdate('Y-m-d\TH:i:s\Z', $t);
$at = function (string $ny): int { $t = (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp(); putenv('SWEEP_PUSH_NOW=' . $t); return $t; };
$user = function (string $id, array $x = []) use ($pdo, $iso) {
    $t = (int) (getenv('SWEEP_PUSH_NOW') ?: time());
    $pdo->prepare('INSERT INTO users (id, username, email, first_name, lang, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?, ?)')
        ->execute([$id, $id, "$id@t.dev", 'Alex', $x['lang'] ?? 'en', $iso($x['created'] ?? $t - 86400), $iso($x['seen'] ?? $t - 3600)]);
};
$keys = [];
$device = function (string $uid, string $lang = 'en', ?string $tz = 'America/New_York', string $ep = '') use ($pdo, &$keys) {
    $k = ua_keys(); $ep = $ep ?: 'https://fcm.googleapis.com/fcm/send/' . $uid . bin2hex(random_bytes(3)); $keys[$ep] = $k;
    wp_subscribe($pdo, $uid, ['endpoint' => $ep, 'keys' => ['p256dh' => $k['p256dh'], 'auth' => $k['auth']], 'lang' => $lang, 'tz' => $tz]);
    return $ep;
};
// the messages the push service received for a device, decrypted
$got = function (string $ep) use ($tmp, &$keys): array {
    $out = [];
    foreach (is_file($tmp . '/sent.jsonl') ? file($tmp . '/sent.jsonl', FILE_IGNORE_NEW_LINES) : [] as $l) {
        $m = json_decode($l, true); if (($m['endpoint'] ?? '') !== $ep) continue;
        $out[] = json_decode((string) ua_decrypt(base64_decode($m['body']), $keys[$ep]['pem'], wp_b64u_d($keys[$ep]['auth'])), true);
    }
    return $out;
};
$on = fn(string $key, bool $v = true) => pa_save($key, ['on' => $v]);
$mailOn = fn(string $key) => $pdo->prepare("UPDATE mail_campaigns SET status = 'active' WHERE auto = ?")->execute([$key]);
$queue = fn(string $uid) => $pdo->query('SELECT q.id, q.state, q.next_at, c.auto FROM mail_queue q JOIN mail_campaigns c ON c.id = q.campaign_id WHERE q.user_id = ' . $pdo->quote($uid) . ' ORDER BY q.id')->fetchAll();
$msgs = fn(string $uid) => $pdo->query('SELECT * FROM push_msgs WHERE user_id = ' . $pdo->quote($uid) . ' ORDER BY id')->fetchAll();
$sent = []; $send = function ($to, $s, $t, $h, $hd, $tok) use (&$sent) { $sent[] = [$to, $s, $tok]; return true; };
ma_seed($pdo);

// 1. the slot
$tue = $at('2026-11-03 10:00');   // Tuesday, in the session
$ok(pa_slot('America/New_York', $tue, false) === $at('2026-11-03 16:00') && pa_slot('America/New_York', $tue, true) === $tue, 'in the session: at 16:00 ET; an account alert at once');
$t = $at('2026-11-03 17:30');   // 23:30 in Paris
$ok(pa_slot('Europe/Paris', $t, false) === (new DateTimeImmutable('2026-11-04 07:00', new DateTimeZone('Europe/Paris')))->getTimestamp(), 'Europe: 23:30 on the phone waits until 7:00 on its clock');
$t = $at('2026-11-04 01:30');   // 7:30 in Paris, before the open: allowed
$ok(pa_slot('Europe/Paris', $t, false) === $t && pa_slot('America/New_York', $at('2026-11-07 11:00'), false) === $at('2026-11-07 11:00'), 'the morning on its clock, and a Saturday at 11:00: at once');
$ok(wp_quiet('Europe/Paris', $at('2026-11-03 17:30')) && !wp_quiet('America/New_York', $at('2026-11-03 17:30')) && wp_quiet('Not/AZone', $at('2026-11-03 22:00')), 'quiet hours: each phone\'s own clock (New York without a valid zone)');

// 2. the phone first, the email 24 h later; off / no device: the email at once
$now = $at('2026-11-03 18:00');
$user('a'); $epA = $device('a', 'fr');
$mailOn('inactive3d');
ma_send('a', 'inactive3d');
$q = $queue('a');
$ok(count($q) === 1 && $q[0]['next_at'] <= time() + 1 && !$msgs('a'), 'the notification off (every one starts off): the email at once, nothing queued for the phone');
$pdo->exec('DELETE FROM mail_queue');
$on('inactive3d'); $on('inactive7d');
ma_send('a', 'inactive3d');
$q = $queue('a'); $m = $msgs('a');
$ok(count($m) === 1 && $m[0]['state'] === 'queued' && (int) $m[0]['mail_qid'] === (int) $q[0]['id'] && (int) $q[0]['next_at'] >= time() + 86400 - 5 && (int) $q[0]['next_at'] <= time() + 86400 + 5,
    'switched on, with a device: the notification queued, its email linked and 24 h later');
$r = pa_run($now);
$g = $got($epA);
$ok($r['sent'] === 1 && count($g) === 1 && $g[0]['title'] === 'Ta discipline t’attend' && $g[0]['url'] === '#dashboard' && preg_match('#^/api/p/o/[a-f0-9]{24}$#', (string) $g[0]['track']) === 1,
    'sent in the device\'s language (FR), its link, and the address the service worker calls when it is opened');
$row = $msgs('a')[0];
$ok(pa_hold(['id' => $row['mail_qid']]) === null, 'not opened, not back: its email will leave');
pa_open($row['token']);
$ok(pa_hold(['id' => $row['mail_qid']]) === 'hold', 'opened (api/p/o/<token>): its email is not sent');
$r2 = ml_run($pdo, $send, time() + 86400 + 60);
$ok(!$sent && $queue('a')[0]['state'] === 'pushed' && pa_stats('inactive3d', 0)['spared'] === 1 && pa_stats('inactive3d', 0)['opened'] === 1, 'the email held at its time (« pushed »), counted as spared, the open counted');
// came back instead of opening it
$user('b'); $epB = $device('b');
ma_send('b', 'inactive3d'); pa_run($now);
$pdo->exec("UPDATE users SET last_login = '" . $iso($now + 3600) . "' WHERE id = 'b'");
$ok(pa_hold(['id' => $msgs('b')[0]['mail_qid']]) === 'hold', 'the trader came back to the app after the notification: its email is not sent');
// not opened, not back: the email goes after 24 h
$user('c'); $device('c');
ma_send('c', 'inactive3d'); pa_run($now);
ml_run($pdo, $send, time() + 86400 + 60);
$ok(count($sent) === 1 && $sent[0][0] === 'c@t.dev' && pa_stats('inactive3d', 0)['relayed'] === 1, 'not opened and not back: the email leaves 24 h later (« relayed »)');
// without a device
$user('d'); $sent = [];
ma_send('d', 'inactive3d');
$ok(!$msgs('d') && (int) $queue('d')[0]['next_at'] <= time() + 1, 'no device: the email at once');
// the account and its money: both at once
$user('e'); $epE = $device('e'); $on('paymentFailed');
ma_send('e', 'paymentFailed', ['plan' => 'pro']); pa_run($now);
$ok((int) $queue('e')[0]['next_at'] <= time() + 1 && count($got($epE)) === 1 && $got($epE)[0]['body'] === 'Update your card to keep Pro: it takes a minute.' && pa_hold(['id' => $queue('e')[0]['id']]) === null,
    'payment failed: the phone and the email at once, never held');
// in the app at that moment (push_away): the email as before, no phone
$on('tradesMilestone'); $GLOBALS['UID'] = 'e';
$ok(pa_dispatch('e', 'tradesMilestone', ['milestone' => 10]) === ['delay' => 0, 'pid' => null], 'a milestone while the trader is in the app: no phone, the email as before');
unset($GLOBALS['UID']);
$ok(pa_dispatch('e', 'tradesMilestone', ['milestone' => 10])['pid'] !== null, 'the same reached by the add-on (not in the app): the phone first');
$pdo->exec("DELETE FROM push_msgs WHERE user_id = 'e' AND auto = 'tradesMilestone'");

// the feedback emails (other session, 5 Nov.): « You asked, it's done » both at once; a feature to discover opens its own page
$on('feedbackShipped'); $on('featureDiscover');
$fb = pa_dispatch('e', 'feedbackShipped', ['request' => 'x', 'reply' => 'y']);
$fd = pa_queue('e', 'featureDiscover', ['feature' => 'Stats', 'feature_button' => 'Open my stats', 'feature_link' => 'https://app.makeitsweep.com/#analytics']);
$ok($fb['delay'] === 0 && $fb['pid'] !== null && pa_q('SELECT url FROM push_msgs WHERE id = ?', [$fd])->fetchColumn() === '#analytics', '« You asked, it\'s done »: phone and email at once; a feature to discover: its in-app page (#analytics)');
$pdo->exec("DELETE FROM push_msgs WHERE user_id = 'e' AND auto IN ('feedbackShipped', 'featureDiscover')");

// 3. the session and the night: held for the slot, the email after it
$now = $at('2026-11-04 10:30');   // Wednesday, in the session
$user('f'); $epF = $device('f');
ma_send('f', 'inactive7d');
$m = $msgs('f')[0];
$ok((int) $m['due_at'] === $at('2026-11-04 16:00') && (int) $queue('f')[0]['next_at'] >= time() + ($at('2026-11-04 16:00') - $now) + 86400 - 5, 'in the session: the notification at 16:00 ET, its email 24 h after that');
pa_run($now);
$ok(!$got($epF) && $msgs('f')[0]['state'] === 'queued', 'not sent before its slot');
$ok(is_int(pa_hold(['id' => $m['mail_qid']])), 'its email, if due earlier, waits for it');
pa_run($at('2026-11-04 16:01'));
$ok(count($got($epF)) === 1, 'sent at 16:00');

// 4. the caps
$now = $at('2026-11-05 18:00');
$user('g'); $device('g');
for ($i = 0; $i < 5; $i++) $pdo->prepare("INSERT INTO push_msgs (user_id, auto, grp, counted, token, state, due_at, sent_at, opened_at, created_at) VALUES ('g', 'inactive3d', 'routine', 1, ?, 'sent', 0, ?, ?, 0)")->execute([bin2hex(random_bytes(12)), $now - ($i + 1) * 86400, $now - ($i + 1) * 86400 + 60]);
$sent = []; ma_send('g', 'inactive7d'); pa_run($now);
$mg = $msgs('g'); $last = end($mg);
$ok($last['state'] === 'skipped' && $last['why'] === 'week' && (int) $pdo->query("SELECT next_at FROM mail_queue WHERE id = " . (int) $last['mail_qid'])->fetchColumn() <= $now, '5 in 7 days: not sent, its email released at once');
$user('h'); $device('h');
for ($i = 0; $i < 4; $i++) $pdo->prepare("INSERT INTO push_msgs (user_id, auto, grp, counted, token, state, due_at, sent_at, created_at) VALUES ('h', 'inactive3d', 'routine', 1, ?, 'sent', 0, ?, 0)")->execute([bin2hex(random_bytes(12)), $now - (10 - $i) * 86400 + ($i === 3 ? 8 * 86400 : 0)]);
ma_send('h', 'inactive7d'); pa_run($now);
$mh = $msgs('h'); $ok(end($mh)['why'] === 'tired', 'the last 4 of a group ignored, one of them this week: that group waits (1 a week)');
$user('i'); $epI = $device('i');
Notify::send('i', 'g_plan', [], ['dedupe_key' => 'x1']); Notify::send('i', 'g_review', [], ['dedupe_key' => 'x2']);
ma_send('i', 'inactive7d'); pa_run($now);
$mi = $msgs('i')[0];
$ok($mi['state'] === 'queued' && (int) $mi['tries'] === 1 && (int) $mi['due_at'] > $now && !$got($epI), '2 notifications today already (the bell\'s reminders count): the next day');
$user('j', ['seen' => $now - 31 * 86400]); $device('j');
ma_send('j', 'inactive7d');
$ok(!$msgs('j'), '30 days away: no notification any more');
$user('k'); $device('k'); wp_set_pref($pdo, 'k', 'routine', ['on' => false]);
ma_send('k', 'inactive7d');
$ok(!$msgs('k') && !wp_groups(wp_prefs($pdo, 'k'))['routine'] && !wp_prefs($pdo, 'k')['streak']['on'] && wp_prefs($pdo, 'k')['lock']['on'], '« My routine » off: none of its notifications, its kinds off together, the others kept');
$ok(!wp_set_pref($pdo, 'k', 'routine', ['at' => '08:00']), 'a group takes on / off only');
// a device asleep (Paris at 23:00) skipped, the other one gets it
$now = $at('2026-11-05 17:00');
$user('l'); $epL1 = $device('l', 'en', 'Europe/Paris'); $epL2 = $device('l', 'es', 'America/Chicago');
pa_queue('l', 'inactive7d'); $pdo->exec("UPDATE push_msgs SET due_at = $now WHERE user_id = 'l'");
pa_run($now);
$ok(!$got($epL1) && count($got($epL2)) === 1 && $got($epL2)[0]['title'] === 'Retoma donde lo dejaste', 'two phones: the one at night in Paris skipped, the one in Chicago gets it in Spanish');

// 5. the account's moments
$now = $at('2026-11-05 14:00');   // in the session: an alert goes at once
$user('m', ['lang' => 'fr']); $epM = $device('m', 'fr');
foreach (['payoutReady', 'goalReached', 'evalPassed'] as $k) $on($k);
$put = function (string $uid, string $col, string $id, array $d) use ($pdo, $iso) { $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $id, json_encode($d), $iso(time()), $iso(time())]); GameEngine::forget($uid); };
$put('m', 'accounts', 'f1', ['id' => 'f1', 'name' => 'Topstep 50K', 'phase' => 'funded', 'starting_balance_c' => 5000000, 'rules' => ['payout_win_days' => 2, 'payout_win_min_c' => 10000, 'payout_min_c' => 50000]]);
$put('m', 'trades', 't1', ['id' => 't1', 'account_id' => 'f1', 'date' => '2026-11-03', 'pnl_c' => 60000, 'fees_c' => 0]);
pa_account_moments('m');
$ok(!$msgs('m'), 'one winning day of 2: no payout yet');
$put('m', 'trades', 't2', ['id' => 't2', 'account_id' => 'f1', 'date' => '2026-11-04', 'pnl_c' => 40000, 'fees_c' => 0]);
pa_account_moments('m'); pa_account_moments('m');
$mm = $msgs('m');
$ok(count($mm) === 1 && $mm[0]['auto'] === 'payoutReady' && $mm[0]['url'] === '#account/f1' && (int) $mm[0]['counted'] === 0, 'every condition met: « payout possible » once, its account\'s page, outside the week\'s 5');
pa_run($now);
$gm = $got($epM); $bell = $pdo->query("SELECT params, category FROM notifications WHERE user_id = 'm' AND type = 'pa_alert'")->fetchAll();
$ok(count($gm) === 1 && $gm[0]['title'] === 'Topstep 50K peut demander un payout' && count($bell) === 1 && $bell[0]['category'] === 'prop_alerts' && json_decode($bell[0]['params'], true)['t_fr'] === 'Topstep 50K peut demander un payout',
    'sent during the session (an account alert), and in the bell in the 3 languages');
$put('m', 'payouts', 'p1', ['id' => 'p1', 'account_id' => 'f1', 'status' => 'requested', 'request_date' => '2026-11-05', 'amount_c' => 50000]);
pa_account_moments('m');
$ok(count($msgs('m')) === 1, 'a payout asked: the next cycle starts from zero (nothing until its conditions are met again)');
$put('m', 'trades', 't3', ['id' => 't3', 'account_id' => 'f1', 'date' => '2026-11-06', 'pnl_c' => 20000]); $put('m', 'trades', 't4', ['id' => 't4', 'account_id' => 'f1', 'date' => '2026-11-09', 'pnl_c' => 70000]);
pa_account_moments('m');
$ok(count($msgs('m')) === 2, 'the next cycle met: « payout possible » again, once');
$put('m', 'accounts', 'e1', ['id' => 'e1', 'name' => 'Apex 50K', 'phase' => 'eval', 'starting_balance_c' => 5000000, 'rules' => ['target_c' => 300000, 'min_days' => 3, 'consistency_pct' => 50]]);
$put('m', 'trades', 'e-1', ['id' => 'e-1', 'account_id' => 'e1', 'date' => '2026-11-03', 'pnl_c' => 200000]); $put('m', 'trades', 'e-2', ['id' => 'e-2', 'account_id' => 'e1', 'date' => '2026-11-04', 'pnl_c' => 110000]);
pa_account_moments('m');
$mm = $msgs('m'); $gr = end($mm);
$ok($gr['auto'] === 'goalReached' && json_decode($gr['vars_json'], true)['left'] === '1 jour de trading de plus et la consistance (meilleur jour ≤ 50 % du profit)', 'target reached: what is left, in the trader\'s words (1 day, consistency 50 %)');
$put('m', 'trades', 'e-3', ['id' => 'e-3', 'account_id' => 'e1', 'date' => '2026-11-05', 'pnl_c' => 150000]);
pa_account_moments('m'); pa_account_moments('m');
$mm = $msgs('m');
$ok(count(array_filter($mm, fn($x) => $x['auto'] === 'evalPassed')) === 1 && count(array_filter($mm, fn($x) => $x['auto'] === 'goalReached')) === 1, 'target, days and consistency met: « evaluation passed » once');
$put('m', 'accounts', 'e2', ['id' => 'e2', 'name' => 'Demo', 'phase' => 'eval', 'demo' => true, 'starting_balance_c' => 0, 'rules' => ['target_c' => 1]]);
$put('m', 'trades', 'd-1', ['id' => 'd-1', 'account_id' => 'e2', 'date' => '2026-11-03', 'pnl_c' => 500]);
$n = count($msgs('m')); pa_account_moments('m');
$ok(count($msgs('m')) === $n, 'sample data: never');
foreach (['payoutReady', 'goalReached', 'evalPassed'] as $k) $on($k, false);

// 6. Sweep's news, once in 28 days
$now = $at('2026-11-06 12:00');
$on('news', false);
$r = pa_news_send(['en' => ['Sync with Quantower', 'Your trades arrive on their own.'], 'fr' => ['Synchro avec Quantower', 'Tes trades arrivent tout seuls.'], 'es' => ['', '']]);
$devs = (int) $pdo->query("SELECT COUNT(DISTINCT user_id) FROM push_subscriptions WHERE user_id NOT IN ('k')")->fetchColumn();
$ok(($r['ok'] ?? false) && $r['queued'] >= 1 && !pa_setting('news')['on'], 'the news queued for the phones with « News » on, then switched off again (sent by hand only)');
$nq = (int) $pdo->query("SELECT COUNT(*) FROM push_msgs WHERE auto = 'news' AND state = 'queued'")->fetchColumn();
pa_run($at('2026-11-06 16:01'));   // a Friday at noon: after the session
$ok($nq >= 1 && (int) $pdo->query("SELECT COUNT(*) FROM push_msgs WHERE auto = 'news' AND state = 'sent'")->fetchColumn() >= 1 && !(int) $pdo->query("SELECT COUNT(*) FROM push_msgs WHERE auto = 'news' AND why = 'off'")->fetchColumn(),
    'the news queued is sent after the session (its switch back off does not stop it; each trader\'s caps still apply)');
$ok((pa_news_send(['en' => ['Again', 'Again']])['error'] ?? '') === 'too_soon', 'a second one within 28 days: refused');
$ok((pa_save('payoutReady', ['on' => true, 'text' => ['en' => ['', '']]])['error'] ?? '') === 'text', 'never switched on without an English title and line');

// 7. the streak reminder on the phone: its number, and never at night on that phone
$now = time();
$user('s'); $epS = $device('s', 'fr', 'America/New_York'); $epS2 = $device('s', 'en', 'Asia/Tokyo');
$quietTokyo = wp_quiet('Asia/Tokyo', $now); $quietNy = wp_quiet('America/New_York', $now);
wp_notify($pdo, 's', 'streak', '#dashboard', ['n' => 4]);
$gs = $got($epS);
$ok(($quietNy ? !$gs : ($gs && $gs[0]['title'] === 'Ton streak de 4 jours est encore sauvable.')) && ($quietTokyo ? !$got($epS2) : count($got($epS2)) === 1), 'the streak with its number, each phone outside its night');
wp_notify($pdo, 's', 'plan', '#dashboard');
$ok(count($got($epS)) === ($quietNy ? 1 : 2) || count($got($epS2)) >= 1, 'the plan reminder (its time chosen by the trader) is never held by the night');

// the plan reminder names the day's big release (the economic calendar the app shows)
$cpi = null; foreach ((array) json_decode((string) file_get_contents($app . '/econ-us-2026-2027.json'), true)['events'] as $e) if ($e['event'] === 'CPI m/m' && $e['date'] >= '2026-11-01') { $cpi = $e; break; }
$ok($cpi && wp_econ_line('fr', $cpi['date']) === 'Annonce importante aujourd’hui : CPI à 8 h 30. Prévois-la dans ton plan.' && wp_econ_line('en', $cpi['date']) === 'Big release today: CPI at 8:30 AM. Plan around it.'
    && wp_econ_line('es', $cpi['date']) === 'Dato importante hoy: CPI a las 8:30. Tenlo en tu plan.' && wp_econ_line('en', '2026-11-07') === null, 'the plan reminder on a CPI day: « CPI at 8:30 AM », in the 3 languages; a Saturday: nothing (' . ($cpi['date'] ?? '') . ')');

// 8. the open link, an account deleted, « Sweep on your phone »
$tok = $msgs('a')[0]['token'];
$ok(!pa_q('SELECT 1 FROM push_msgs WHERE token = ? AND opened_at IS NULL', [$tok])->fetchColumn(), 'api/p/o/<token> marks it opened (once)');
pa_forget('a');
$ok(!$msgs('a'), 'an account deleted: its notifications go');
$v = ['subject' => 'S', 'preheader' => '', 'body' => "Hi\n\n[[qr]]\n\n[[Open|{app}?i=qr]]"];
[, $txt, $html] = ml_render($pdo, $v, 'en', 'Alex', '', false);
$ok(strpos($html, 'https://app.makeitsweep.com/img/qr-app.png') !== false && strpos($html, 'href="https://app.makeitsweep.com/?i=qr"') !== false && strpos($txt, '[[qr]]') === false, 'the email\'s QR block: the image of the code, and the link that opens Sweep on the phone');
$now = $at('2026-11-10 08:00');
$user('p', ['created' => $now - 3 * 86400 - 600]); $user('p2', ['created' => $now - 3 * 86400 - 600]); $user('p3', ['created' => $now - 3 * 86400 - 600]);
$put('p', 'trades', 'x', ['id' => 'x', 'account_id' => 'a', 'date' => '2026-11-07', 'pnl_c' => 100]); $put('p2', 'trades', 'x', ['id' => 'x', 'account_id' => 'a', 'date' => '2026-11-07', 'pnl_c' => 100]); $device('p2');
$due = fn(string $id) => array_column(ma_daily_due($pdo->query("SELECT * FROM users WHERE id = '$id'")->fetch(), ['live' => false, 'trial_end' => null], $now - 86400, $now), 1);
$ok(in_array('phoneInstall', $due('p'), true) && !in_array('phoneInstall', $due('p2'), true) && !in_array('phoneInstall', $due('p3'), true), '« Sweep on your phone »: day 3, with a trade and no phone receiving notifications (none without a trade, none with a phone)');
$ok(ma_info('phoneInstall') !== null && (string) $pdo->query("SELECT status FROM mail_campaigns WHERE auto = 'phoneInstall'")->fetchColumn() === 'off', 'its automation exists in Admin, off at the start');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
