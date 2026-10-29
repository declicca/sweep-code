<?php
declare(strict_types=1);
/**
 * Sweep — notifications (brief 02 part 10), on a throwaway SQLite database; the push service replaced by a file
 * (SWEEP_PUSH_MOCK: no message leaves), test keys made here:
 *   php tests/push_test.php
 *  - the message encryption gives RFC 8291's own example, byte for byte; the VAPID signature checks with the public key;
 *  - only the addresses of push services are accepted (never a page of the server or of the network); a device's keys checked;
 *  - at most 2 notifications a day (New York) that alert: beyond, « quiet » (in the list, read, no toast), or skipped for a
 *    reminder; prop firm alerts neither capped nor counted; config.php can only lower it;
 *  - the plan, review and week reminders reach each device in its language, at the trader's time (never before, never during
 *    the session), each one switchable, not from the app (the trader is in it), a gone device forgotten; no keys → no push;
 *  - « your best month »: only for the best month (before 14 Oct., every month with data).
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$scenario = $argv[1] ?? 'main';
$tmp = getenv('PUSH_TEST_DIR') ?: sys_get_temp_dir() . '/sweep-push-' . bin2hex(random_bytes(4));
@mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$cfg = ['notifications' => []];
putenv('SWEEP_PUSH_MOCK=' . $tmp . '/sent.jsonl');
require $app . '/push/web-push.php';
require_once __DIR__ . '/push_ua.php';
if ($scenario === 'nokeys') {   // a separate process: wp_config() is read once
    define('SWEEP_PUSH_CONFIG', $tmp . '/missing.php');
    require $app . '/notify/notify.php'; require $app . '/game/game.php';
    GameEngine::setPdo($pdo); GameEngine::schema();
    putenv('SWEEP_GAME_NOW=2026-10-19 08:45');
    GameEngine::profile('nk');
    $pdo->exec("INSERT INTO game_days (user_id, trading_day, activity, updated_at) VALUES ('nk', '2026-10-16', 1, 0)");
    $k = ua_keys();
    wp_subscribe($pdo, 'nk', ['endpoint' => 'https://fcm.googleapis.com/fcm/send/nk', 'keys' => ['p256dh' => $k['p256dh'], 'auth' => $k['auth']], 'lang' => 'fr']);
    GameNotifyService::run('nk', true);
    echo json_encode(['state' => wp_state($pdo, 'nk'), 'bell' => $pdo->query("SELECT type FROM notifications WHERE user_id = 'nk'")->fetchAll(PDO::FETCH_COLUMN), 'sent' => is_file($tmp . '/sent.jsonl')]);
    exit;
}
file_put_contents($tmp . '/push-config.php', '<?php return ' . var_export(wp_new_keys(), true) . ";\n");
define('SWEEP_PUSH_CONFIG', $tmp . '/push-config.php');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require_once $app . '/notify/notify.php';
require_once $app . '/notify/listeners.php';
require $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$C = wp_config();

// 1. the message encryption: RFC 8291, Appendix A, byte for byte
$d = wp_b64u_d('yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw'); $asPub = wp_b64u_d('BP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A8');
$pem = "-----BEGIN EC PRIVATE KEY-----\n" . chunk_split(base64_encode(hex2bin('30770201010420') . $d . hex2bin('a00a06082a8648ce3d030107a144034200') . $asPub), 64, "\n") . "-----END EC PRIVATE KEY-----\n";
$body = wp_encrypt('When I grow up, I want to be a watermelon', wp_b64u_d('BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4'),
    wp_b64u_d('BTBZMqHH6r4Tts7J_aSIgg'), ['private_pem' => $pem, 'salt' => wp_b64u_d('DGv6ra1nlYgDCS1FRnbzlw')]);
$ok(wp_b64u($body) === 'DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A_yl95bQpu6cVPTpK4Mqgkf1CXztLVBSt2Ks3oZwbuwXPXLWyouBWLVWGNWQexSgSxsj_Qulcy4a-fN',
    'encryption: RFC 8291 Appendix A, byte for byte');
$k = ua_keys();
$ok(ua_decrypt(wp_encrypt('{"a":1}', wp_b64u_d($k['p256dh']), wp_b64u_d($k['auth'])), $k['pem'], wp_b64u_d($k['auth'])) === '{"a":1}', 'a new message opens with the browser\'s key (one-time key each time)');
// 2. VAPID: aud = the push service, 12 h, our address; the signature checks with the public key
$v = wp_vapid('https://web.push.apple.com/QGu7abc', $C, 1_800_000_000);
preg_match('~^vapid t=([^.]+)\.([^.]+)\.([^,]+), k=(.+)$~', $v, $m);
$claims = json_decode(wp_b64u_d($m[2] ?? ''), true);
$sig = wp_b64u_d($m[3] ?? ''); $int = fn($x) => (ord(($x = ltrim($x, "\0"))[0]) & 0x80 ? "\0" . $x : $x);
$r = $int(substr($sig, 0, 32)); $s = $int(substr($sig, 32)); $seq = "\x02" . chr(strlen($r)) . $r . "\x02" . chr(strlen($s)) . $s;
$ok(($claims ?? null) === ['aud' => 'https://web.push.apple.com', 'exp' => 1_800_000_000 + 43200, 'sub' => 'mailto:hello@makeitsweep.com'] && ($m[4] ?? '') === $C['public_key']
    && openssl_verify(($m[1] ?? '') . '.' . ($m[2] ?? ''), "\x30" . chr(strlen($seq)) . $seq, wp_pub_pem(wp_b64u_d($C['public_key'])), OPENSSL_ALGO_SHA256) === 1 && strlen($sig) === 64,
    'VAPID: aud of the push service, 12 hours, hello@makeitsweep.com; ES256 signature checks with the public key');

// 3. only push services; a device's keys checked; the same device on another account moves; 10 devices at most
$bad = ['http://fcm.googleapis.com/x', 'https://127.0.0.1/x', 'https://evil.example/x', 'https://fcm.googleapis.com:8443/x', 'https://u:p@fcm.googleapis.com/x', 'https://fcm.googleapis.com.evil.example/x', 'https://app.makeitsweep.com/api/x'];
$good = ['https://fcm.googleapis.com/fcm/send/abc', 'https://web.push.apple.com/QG', 'https://updates.push.services.mozilla.com/wpush/v2/x', 'https://wns2-par02p.notify.windows.com/w/?token=x'];
$ok(!array_filter($bad, 'wp_endpoint_ok') && count(array_filter($good, 'wp_endpoint_ok')) === 4, 'addresses: FCM, Apple, Mozilla, Windows only, in https on 443 (never the server, the network or a look-alike)');
$sub = fn(string $uid, string $ep, array $k, string $lang) => wp_subscribe($pdo, $uid, ['endpoint' => $ep, 'keys' => ['p256dh' => $k['p256dh'], 'auth' => $k['auth']], 'lang' => $lang]);
$ok(!$sub('x1', 'https://evil.example/a', $k, 'fr') && !wp_subscribe($pdo, 'x1', ['endpoint' => 'https://fcm.googleapis.com/fcm/send/a', 'keys' => ['p256dh' => 'abc', 'auth' => $k['auth']]]) && wp_devices($pdo, 'x1') === 0,
    'a wrong address or key: refused');
$sub('x1', 'https://fcm.googleapis.com/fcm/send/shared', $k, 'fr'); $sub('x2', 'https://fcm.googleapis.com/fcm/send/shared', $k, 'en');
$ok(wp_devices($pdo, 'x1') === 0 && wp_devices($pdo, 'x2') === 1, 'the same phone signed in to another account: it follows that account');
for ($i = 0; $i < 12; $i++) $sub('x3', "https://fcm.googleapis.com/fcm/send/d$i", $k, 'en');
$ok(wp_devices($pdo, 'x3') === 10, 'at most 10 devices: the oldest go');
// 4. each reminder's time: 15-minute steps inside its window; on by default
$ok(wp_prefs($pdo, 'x3') === ['plan' => ['on' => true, 'at' => '08:45'], 'review' => ['on' => true, 'at' => '16:30'], 'weekly' => ['on' => true, 'at' => '17:00']]
    && wp_times('plan')[0] === '07:00' && array_slice(wp_times('plan'), -1) === ['09:15'] && array_slice(wp_times('review'), -1) === ['20:45'], 'defaults 8:45, 16:30, 17:00; plan 7:00 to 9:15 (before the 9:30 open), review and week until 20:45');
$ok(!wp_set_pref($pdo, 'x3', 'plan', ['at' => '10:00']) && !wp_set_pref($pdo, 'x3', 'plan', ['at' => '08:50']) && !wp_set_pref($pdo, 'x3', 'streak', ['on' => false])
    && wp_set_pref($pdo, 'x3', 'review', ['on' => false]) && wp_prefs($pdo, 'x3')['review'] === ['on' => false, 'at' => '16:30'], 'a time in the session or off the steps, an unknown reminder: refused; off kept');

// 5. at most 2 a day that alert (New York day)
$send = fn(string $type, array $o = []) => Notify::send('c1', $type, [], ['dedupe_key' => $type . ':' . bin2hex(random_bytes(4))] + $o);
$a = $send('fb_planned'); $qa = Notify::$quiet; $b = $send('fb_shipped'); $qb = Notify::$quiet; $c = $send('chart_ready'); $qc = Notify::$quiet;
$row = $pdo->query("SELECT * FROM notifications WHERE id = $c")->fetch();
$in = Notify::inbox('c1');
$ok($a && $b && !$qa && !$qb && $c && $qc && $row['read_at'] !== null && (int) $row['quiet'] === 1 && $in['unread'] === 2 && count($in['items']) === 3,
    '2 alert (a celebration counts); the 3rd lands quiet: in the list, already read, no badge');
$ok($send('g_review', ['over_cap' => 'skip']) === null, 'a reminder over the day\'s 2: skipped (it waits)');
$p = Notify::send('c1', 'prop_limit', [], ['dedupe_key' => 'prop:a:dll:75:x', 'title_key' => 'prop_dll75.title']);
$ok($p && !Notify::$quiet && Notify::alertsToday('c1') === 2 && Notify::inbox('c1')['unread'] === 3, 'a prop firm alert (the trader\'s trade): alerts anyway, not counted');
$e = $send('fb_shipped', ['priority' => 'celebration']); $mod = Notify::inbox('c1')['modal'];
$ok($e && Notify::$quiet && ($mod['id'] ?? 0) === $b, 'a quiet celebration never shows as the celebration toast');
$pdo->exec("UPDATE notifications SET created_at = created_at - 86400 WHERE user_id = 'c1'");
$ok($send('fb_planned') && !Notify::$quiet, 'the next New York day: alerts again');
$cfg['notifications'] = ['daily_limit' => 5]; $five = Notify::dailyMax(); $cfg['notifications'] = ['daily_limit' => 1]; $one = Notify::dailyMax(); $cfg['notifications'] = [];
$ok($five === 2 && $one === 1 && Notify::dailyMax() === 2, 'config.php: 5 stays 2 (it can only lower it), 1 is 1');

// 6. the reminders on the phone (Monday 2026-10-19, a market day; the trader used Sweep on Friday)
$sent = function (): array { global $tmp; $l = is_file("$tmp/sent.jsonl") ? file("$tmp/sent.jsonl", FILE_IGNORE_NEW_LINES) : []; @unlink("$tmp/sent.jsonl"); return array_map(fn($x) => json_decode($x, true), $l); };
$open = fn(array $x, array $k) => json_decode((string) ua_decrypt(base64_decode($x['body']), $k['pem'], wp_b64u_d($k['auth'])), true);
$trader = function (string $u, array $days = [['2026-10-16', 0, 0]]) use ($pdo, $at) {
    $at('2026-10-12 08:00'); GameEngine::profile($u);
    foreach ($days as [$dd, $tr, $rv]) $pdo->prepare('INSERT OR REPLACE INTO game_days (user_id, trading_day, trades_count, review_done, activity, updated_at) VALUES (?, ?, ?, ?, 1, 0)')->execute([$u, $dd, $tr, $rv]);
};
$bell = fn(string $u) => $pdo->query("SELECT type FROM notifications WHERE user_id = " . $pdo->quote($u) . " ORDER BY id")->fetchAll(PDO::FETCH_COLUMN);
$kfr = ua_keys(); $ken = ua_keys();
$trader('p1'); $sub('p1', 'https://fcm.googleapis.com/fcm/send/p1-fr', $kfr, 'fr'); $sub('p1', 'https://web.push.apple.com/p1-en', $ken, 'en');
$at('2026-10-19 08:30'); GameNotifyService::run('p1', true);
$ok($bell('p1') === [] && $sent() === [], '8:30: nothing (before the trader\'s 8:45)');
$at('2026-10-19 08:45'); GameNotifyService::run('p1', true); $s = $sent();
$by = []; foreach ($s as $x) $by[$x['endpoint']] = $x;
$fr = $open($by['https://fcm.googleapis.com/fcm/send/p1-fr'] ?? ['body' => ''], $kfr); $en = $open($by['https://web.push.apple.com/p1-en'] ?? ['body' => ''], $ken);
$h = $by['https://web.push.apple.com/p1-en']['headers'] ?? [];
$ok($bell('p1') === ['g_plan'] && count($s) === 2 && ($fr['title'] ?? '') === 'Ton plan du jour t’attend.' && ($fr['body'] ?? '') === '30 secondes avant l’ouverture.' && ($fr['url'] ?? '') === '#dashboard'
    && ($en['title'] ?? '') === 'Your plan of the day is waiting.' && ($en['tag'] ?? '') === 'sweep-plan', '8:45: the bell, and each phone in its language (FR, EN), opening Today (' . json_encode([$fr, $en], JSON_UNESCAPED_UNICODE) . ')');
$ok(($h['TTL'] ?? '') === '14400' && ($h['Topic'] ?? '') === 'plan' && ($h['Content-Encoding'] ?? '') === 'aes128gcm' && strpos($h['Authorization'] ?? '', 'vapid t=') === 0
    && json_decode(wp_b64u_d(explode('.', substr($h['Authorization'], 8))[1] ?? ''), true)['aud'] === 'https://web.push.apple.com', 'its headers: 4 hours to live, topic, aes128gcm, VAPID for Apple\'s service');
$at('2026-10-19 09:00'); GameNotifyService::run('p1', true);
$ok($bell('p1') === ['g_plan'] && $sent() === [], '9:00: not twice');
$trader('p2'); $sub('p2', 'https://fcm.googleapis.com/fcm/send/p2', $kfr, 'es'); wp_set_pref($pdo, 'p2', 'plan', ['at' => '09:00']);
$at('2026-10-19 08:45'); GameNotifyService::run('p2', true); $early = $bell('p2'); $sent();
$at('2026-10-19 09:00'); GameNotifyService::run('p2', true); $s = $sent();
$ok($early === [] && $bell('p2') === ['g_plan'] && count($s) === 1 && ($open($s[0], $kfr)['title'] ?? '') === 'Tu plan del día te espera.', 'plan at 9:00 (Spanish): nothing at 8:45 (bell either), sent at 9:00');
$trader('p3'); $sub('p3', 'https://fcm.googleapis.com/fcm/send/p3', $kfr, 'fr'); wp_set_pref($pdo, 'p3', 'plan', ['on' => false]);
$at('2026-10-19 08:45'); GameNotifyService::run('p3', true);
$ok($bell('p3') === ['g_plan'] && $sent() === [], 'plan off on the phone: the bell only');
$trader('p4'); $sub('p4', 'https://fcm.googleapis.com/fcm/send/p4', $kfr, 'fr');
$at('2026-10-19 08:45'); GameNotifyService::run('p4');
$ok($bell('p4') === ['g_plan'] && $sent() === [], 'from the app (the trader is in it): the bell, no push');
$trader('p5'); $sub('p5', 'https://fcm.googleapis.com/fcm/send/p5', $kfr, 'fr');
foreach (['2026-10-19 10:00', '2026-10-19 15:59', '2026-10-24 08:45', '2026-10-19 21:30'] as $t) { $at($t); GameNotifyService::run('p5', true); }
$ok($bell('p5') === [] && $sent() === [], 'during the session (10:00, 15:59), Saturday 8:45, 21:30: nothing');
// review: 16:30 by default; a gone device is forgotten; over the day's 2, the review waits (no bell, no push)
$trader('p6', [['2026-10-16', 0, 0], ['2026-10-19', 2, 0]]); $sub('p6', 'https://fcm.googleapis.com/fcm/send/p6', $kfr, 'fr'); $sub('p6', 'https://fcm.googleapis.com/fcm/send/gone-p6', $ken, 'en');
$at('2026-10-19 16:15'); GameNotifyService::run('p6', true); $early = $bell('p6'); $sent();
$at('2026-10-19 16:30'); GameNotifyService::run('p6', true); $s = $sent();
$ok($early === [] && $bell('p6') === ['g_review'] && count($s) === 2 && ($open($s[0], $kfr)['title'] ?? $open($s[1], $kfr)['title'] ?? '') === 'Ferme ta journée en 2 touchers.' && wp_devices($pdo, 'p6') === 1,
    'review at 16:30 (not 16:15), in French; the device the push service says gone (410) is forgotten');
$trader('p6b', [['2026-10-16', 0, 0], ['2026-10-19', 2, 0]]); $sub('p6b', 'https://fcm.googleapis.com/fcm/send/p6b', $kfr, 'fr'); wp_set_pref($pdo, 'p6b', 'review', ['at' => '18:30']);
$at('2026-10-19 18:30'); GameNotifyService::run('p6b', true); $s = $sent();
$ok($bell('p6b') === ['g_review'] && count($s) === 1, 'review at 18:30 (after the next session began at 18:00): the day that closed, reminded (before 14 Oct.: nothing)');
$trader('p7', [['2026-10-16', 0, 0], ['2026-10-19', 2, 0]]); $sub('p7', 'https://fcm.googleapis.com/fcm/send/p7', $kfr, 'fr');
Notify::send('p7', 'fb_planned', [], ['dedupe_key' => 'x7a']); Notify::send('p7', 'chart_ready', [], ['dedupe_key' => 'x7b']);
$at('2026-10-19 16:30'); GameNotifyService::run('p7', true);
$ok($bell('p7') === ['fb_planned', 'chart_ready'] && $sent() === [], 'already 2 notifications today: the review waits (no bell, no push)');
// the week's recap: Friday, from 17:00 (or the trader's time), once
$trader('p8', [['2026-10-16', 0, 0], ['2026-10-20', 1, 1]]); $sub('p8', 'https://fcm.googleapis.com/fcm/send/p8', $kfr, 'en');
$at('2026-10-23 16:45'); GameNotifyService::run('p8', true); $early = $bell('p8'); $sent();
$at('2026-10-23 17:00'); GameNotifyService::run('p8', true); $s = $sent();
$at('2026-10-24 17:00'); GameNotifyService::run('p8', true);
$ok($early === [] && $bell('p8') === ['g_weekly'] && count($s) === 1 && ($open($s[0], $kfr)['title'] ?? '') === 'Your week is ready.' && $sent() === [], 'the week: nothing at 16:45, sent Friday 17:00, once');
$trader('p9', [['2026-10-16', 0, 0], ['2026-10-20', 1, 1]]); $sub('p9', 'https://fcm.googleapis.com/fcm/send/p9', $kfr, 'fr'); wp_set_pref($pdo, 'p9', 'weekly', ['at' => '18:30']);
$at('2026-10-23 17:00'); GameNotifyService::run('p9', true); $early = $bell('p9');
$at('2026-10-23 18:30'); GameNotifyService::run('p9', true); $s = $sent();
$ok($early === [] && $bell('p9') === ['g_weekly'] && count($s) === 1 && ($open($s[0], $kfr)['title'] ?? '') === 'Ta semaine est prête.', 'the week at 18:30: not at 17:00, sent at 18:30');
// no keys on the server: nothing to turn on, nothing sent (the bell as before)
$off = json_decode((string) shell_exec('PUSH_TEST_DIR=' . escapeshellarg($tmp) . ' ' . escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg(__FILE__) . ' nokeys 2>&1'), true);
$ok(($off['state'] ?? null) === ['available' => false] && ($off['bell'] ?? null) === ['g_plan'] && ($off['sent'] ?? true) === false, 'no keys: « available » false, the bell as before, nothing sent');

// 7. « your best month »: only the best (the 1st of the month, months of 10+ market days)
$month = function (string $u, string $ym, int $valid) use ($pdo) {
    $n = 0;
    for ($dd = new DateTimeImmutable("$ym-01"); $dd->format('Y-m') === $ym; $dd = $dd->modify('+1 day')) {
        if ((int) $dd->format('N') > 5) continue;
        $pdo->prepare('INSERT OR REPLACE INTO game_days (user_id, trading_day, is_valid_streak, activity, updated_at) VALUES (?, ?, ?, 1, 0)')->execute([$u, $dd->format('Y-m-d'), $n++ < $valid ? 1 : 0]);
    }
};
foreach (['w1' => [5, 18], 'w2' => [18, 5]] as $u => [$aug, $sep]) {
    $at('2026-08-01 10:00'); GameEngine::profile($u); GameWow::check($u);   // the first check records silently
    $month($u, '2026-08', $aug); $month($u, '2026-09', $sep);
    $at('2026-10-01 17:00'); GameWow::check($u);
}
$bm = fn(string $u) => $pdo->query("SELECT params FROM notifications WHERE user_id = " . $pdo->quote($u) . " AND type = 'wow_best_month'")->fetchAll(PDO::FETCH_COLUMN);
$w1 = $bm('w1');
$ok(count($w1) === 1 && (json_decode($w1[0], true)['month_fr'] ?? '') === 'septembre' && $bm('w2') === [], 'best month: September told when it beats August; not when it is worse (before: told « best » anyway)');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
