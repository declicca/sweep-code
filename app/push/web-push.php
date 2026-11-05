<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — notifications on the phone (web push, brief 02 part 10): the plan reminder before the open, the review reminder
 * after the close, the week's recap. Each one can be turned off and has its time (New York), never during the session.
 * They are the bell's reminders (game/v2c.php GameNotifyService), sent from the scheduled task only, so within the day's
 * 2 notifications (notify/notify.php) and never while the trader is in the app.
 *
 * Standard Web Push (RFC 8030), VAPID (RFC 8292) and message encryption aes128gcm (RFC 8291), in plain PHP (openssl,
 * hash_hkdf): no library. Keys: sweep-private/push-config.php, made on the server by ops/push-keys.php (never in git,
 * never printed); push/push-config.sample.php shows its shape. Without keys nothing shows in the app and nothing is sent.
 * Tests: SWEEP_PUSH_MOCK (a file) receives each message instead of the push service (tests/push_test.php, tests/e2e_push.py).
 */

/** [default time, earliest, latest] of each reminder, New York time (the bell's windows end at 9:30, the open, and 21:00) */
const WP_KINDS = ['plan' => ['08:45', '07:00', '09:15'], 'review' => ['17:15', '17:00', '20:45'], 'weekly' => ['17:00', '17:00', '20:45'],   // (1 Nov.) the review after the 17:00 close (the CME reopens at 18:00)
    'lock' => ['', '', ''], 'guard' => ['', '', ''],   // (3 Nov.) the account guardian at « watch » then « danger »: at that moment   // (1 Nov., brief avance 4) the day's lock: at the moment the limit is reached, no time to choose
    // (5 Nov., brief notifications) the streak still savable (19:30 New York), a payout that can be asked for, an evaluation's goal,
    // then the automatic messages (push/push-auto.php): what the trader achieved, and Sweep's news and account
    'streak' => ['', '', ''], 'payout' => ['', '', ''], 'goal' => ['', '', ''], 'progress' => ['', '', ''], 'news' => ['', '', '']];
/** (5 Nov.) the four switches of Settings › Notifications › On this device: each one turns its kinds on or off together */
const WP_GROUPS = ['routine' => ['plan', 'review', 'weekly', 'streak'], 'accounts' => ['lock', 'guard', 'payout', 'goal'], 'progress' => ['progress'], 'news' => ['news']];
/** (5 Nov.) quiet hours on the phone's own clock: nothing from 21:00 to 7:00 (a trader in Europe is never woken up). The plan
 *  reminder (before the open, at the time the trader chose) and the account alerts (they answer a trade) are not held. */
const WP_QUIET = [21, 7];
const WP_QUIET_FREE = ['plan', 'lock', 'guard'];
/** push services only: the server never posts anywhere else (a subscription is an address the browser gives) */
const WP_HOSTS = ['fcm.googleapis.com', 'android.googleapis.com', 'updates.push.services.mozilla.com', 'web.push.apple.com'];
const WP_HOST_SUFFIXES = ['.push.apple.com', '.notify.windows.com', '.push.services.mozilla.com'];
const WP_MAX_DEVICES = 10;
/** the bell's own words (src/game.js, g_plan / g_review / g_weekly; src/coach.js, g_lock; src/nav.js, the guardian's g_guard_*) */
const WP_TEXT = [
    'en' => ['plan' => ['Your plan of the day is waiting.', '30 seconds before the open.'],
             'review' => ['Close your day in 2 taps.', 'Journal and review while it is fresh.'],
             'weekly' => ['Your week is ready.', 'Your streak, your discipline and your swept days, in one place.'],
             'lock' => ['Day closed: your limit is reached.', 'Your account is protected. Grade your trades and close your day.'],
             'guard' => ['Account guardian: your room is shrinking.', 'See what you can still lose today, and protect your account.'],
             'streak' => ['Your {n}-day streak can still be saved.', 'A review is all it takes.']],
    'fr' => ['plan' => ['Ton plan du jour t’attend.', '30 secondes avant l’ouverture.'],
             'review' => ['Ferme ta journée en 2 touchers.', 'Journalise et fais ta revue tant que c’est frais.'],
             'weekly' => ['Ta semaine est prête.', 'Ton streak, ta discipline et tes journées balayées, au même endroit.'],
             'lock' => ['Journée fermée : ta limite est atteinte.', 'Ton compte est protégé. Note tes trades et ferme ta journée.'],
             'guard' => ['Gardien de compte : ta marge diminue.', 'Vois ce que tu peux encore perdre aujourd’hui, et protège ton compte.'],
             'streak' => ['Ton streak de {n} jours est encore sauvable.', 'Une revue suffit.']],
    'es' => ['plan' => ['Tu plan del día te espera.', '30 segundos antes de la apertura.'],
             'review' => ['Cierra tu día en 2 toques.', 'Registra y revisa mientras está fresco.'],
             'weekly' => ['Tu semana está lista.', 'Tu racha, tu disciplina y tus días barridos, en un solo lugar.'],
             'lock' => ['Día cerrado: alcanzaste tu límite.', 'Tu cuenta está protegida. Califica tus operaciones y cierra tu día.'],
             'guard' => ['Guardián de cuenta: tu margen se reduce.', 'Mira lo que aún puedes perder hoy, y protege tu cuenta.'],
             'streak' => ['Tu racha de {n} días aún se puede salvar.', 'Basta con una revisión.']],
];

/* ───────────── keys ───────────── */

function wp_b64u(string $s): string { return rtrim(strtr(base64_encode($s), '+/', '-_'), '='); }
function wp_b64u_d(string $s): string { return (string) base64_decode(strtr($s, '-_', '+/') . str_repeat('=', (4 - strlen($s) % 4) % 4), true); }

/** P-256 public key: raw (65 bytes, 0x04 x y) → PEM, for openssl */
function wp_pub_pem(string $raw): string
{
    return "-----BEGIN PUBLIC KEY-----\n" . chunk_split(base64_encode(hex2bin('3059301306072a8648ce3d020106082a8648ce3d030107034200') . $raw), 64, "\n") . "-----END PUBLIC KEY-----\n";
}

/** the raw public point of an openssl EC key */
function wp_pub_raw($key): string
{
    $d = openssl_pkey_get_details($key)['ec'] ?? [];
    $pad = fn($v) => str_pad((string) $v, 32, "\0", STR_PAD_LEFT);
    return "\x04" . $pad($d['x'] ?? '') . $pad($d['y'] ?? '');
}

/** a new VAPID key pair (ops/push-keys.php; tools/push-config.local.php for the tests) */
function wp_new_keys(): array
{
    $k = openssl_pkey_new(['private_key_type' => OPENSSL_KEYTYPE_EC, 'curve_name' => 'prime256v1']);
    if (!$k || !openssl_pkey_export($k, $pem)) throw new RuntimeException('openssl could not make a P-256 key');
    return ['public_key' => wp_b64u(wp_pub_raw($k)), 'private_key' => $pem, 'subject' => 'mailto:hello@makeitsweep.com'];
}

/** the keys, or null (then push is off: nothing in the app, nothing sent) */
function wp_config(): ?array
{
    static $c = false;
    if ($c !== false) return $c;
    // a path given (config.php › push_config, or the tests) is the only one looked at; else the private folder
    $e = getenv('SWEEP_PUSH_CONFIG');
    $cands = defined('SWEEP_PUSH_CONFIG') ? [(string) SWEEP_PUSH_CONFIG] : (is_string($e) && $e !== '' ? [$e]
        : [dirname(__DIR__, 2) . '/sweep-private/push-config.php', dirname(__DIR__, 3) . '/sweep-private/push-config.php']);   // /home/USER/<app>/push → /home/USER/sweep-private
    $x = null;
    foreach ($cands as $p) if (is_file($p)) { $x = (array) require $p; break; }
    $pub = wp_b64u_d((string) ($x['public_key'] ?? ''));
    if (!$x || strlen($pub) !== 65 || $pub[0] !== "\x04" || !openssl_pkey_get_private((string) ($x['private_key'] ?? ''))) return $c = null;
    $sub = (string) ($x['subject'] ?? '');
    return $c = ['public_key' => (string) $x['public_key'], 'private_key' => (string) $x['private_key'],
        'subject' => preg_match('~^(mailto:|https://)~', $sub) ? $sub : 'mailto:hello@makeitsweep.com'];
}

/* ───────────── one message ───────────── */

/** ECDSA signature, DER (openssl) → the 64 raw bytes r ‖ s of a JWT */
function wp_der2raw(string $der): string
{
    $o = 2; if (ord($der[1]) & 0x80) $o += ord($der[1]) & 0x7f;
    $rl = ord($der[$o + 1]); $r = substr($der, $o + 2, $rl); $o += 2 + $rl;
    $sl = ord($der[$o + 1]); $s = substr($der, $o + 2, $sl);
    $pad = fn($v) => str_pad(ltrim($v, "\0"), 32, "\0", STR_PAD_LEFT);
    return $pad($r) . $pad($s);
}

/** VAPID (RFC 8292): « vapid t=<JWT ES256>, k=<public key> », for the push service that hosts the endpoint */
function wp_vapid(string $endpoint, array $cfg, ?int $now = null): string
{
    $u = parse_url($endpoint);
    $aud = 'https://' . $u['host'];
    $h = wp_b64u('{"typ":"JWT","alg":"ES256"}');
    $p = wp_b64u(json_encode(['aud' => $aud, 'exp' => ($now ?? time()) + 12 * 3600, 'sub' => $cfg['subject']], JSON_UNESCAPED_SLASHES));
    if (!openssl_sign("$h.$p", $der, openssl_pkey_get_private($cfg['private_key']), OPENSSL_ALGO_SHA256)) throw new RuntimeException('VAPID signature failed');
    return 'vapid t=' . "$h.$p." . wp_b64u(wp_der2raw($der)) . ', k=' . $cfg['public_key'];
}

/**
 * The message for one browser (RFC 8291, aes128gcm): salt ‖ record size ‖ key id (our one-time public key) ‖ ciphertext.
 * $ua: the browser's public key (65 bytes), $auth: its secret (16 bytes). $fixed (tests only): the RFC's one-time key and salt.
 */
function wp_encrypt(string $plain, string $ua, string $auth, ?array $fixed = null): string
{
    $as = $fixed ? openssl_pkey_get_private($fixed['private_pem']) : openssl_pkey_new(['private_key_type' => OPENSSL_KEYTYPE_EC, 'curve_name' => 'prime256v1']);
    $asPub = wp_pub_raw($as);
    $secret = openssl_pkey_derive(openssl_pkey_get_public(wp_pub_pem($ua)), $as);
    if (!is_string($secret) || strlen($secret) !== 32) throw new RuntimeException('ECDH failed');
    $salt = $fixed['salt'] ?? random_bytes(16);
    $ikm = hash_hkdf('sha256', $secret, 32, "WebPush: info\0" . $ua . $asPub, $auth);
    $cek = hash_hkdf('sha256', $ikm, 16, "Content-Encoding: aes128gcm\0", $salt);
    $nonce = hash_hkdf('sha256', $ikm, 12, "Content-Encoding: nonce\0", $salt);
    $ct = openssl_encrypt($plain . "\x02", 'aes-128-gcm', $cek, OPENSSL_RAW_DATA, $nonce, $tag, '', 16);   // 0x02: the last (only) record
    return $salt . pack('N', 4096) . chr(65) . $asPub . $ct . $tag;
}

/** POST one message; the HTTP status (201 sent, 404 / 410 the subscription is gone). SWEEP_PUSH_MOCK: written to a file. */
function wp_post(string $endpoint, array $headers, string $body): int
{
    $mock = (string) getenv('SWEEP_PUSH_MOCK');
    if ($mock !== '') {
        file_put_contents($mock, json_encode(['endpoint' => $endpoint, 'headers' => $headers, 'body' => base64_encode($body), 'at' => time()], JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
        return strpos($endpoint, '/gone') !== false ? 410 : 201;
    }
    $h = []; foreach ($headers as $k => $v) $h[] = "$k: $v";
    $ch = curl_init($endpoint);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => $body, CURLOPT_HTTPHEADER => $h, CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 6, CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_FOLLOWLOCATION => false, CURLOPT_PROTOCOLS => CURLPROTO_HTTPS]);
    curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    return $code;
}

/** an address of a push service, in https (never a page of the server or of the network) */
function wp_endpoint_ok(string $e): bool
{
    $u = parse_url($e);
    if (!$u || ($u['scheme'] ?? '') !== 'https' || isset($u['user']) || isset($u['pass']) || (isset($u['port']) && (int) $u['port'] !== 443) || strlen($e) > 600) return false;
    $h = strtolower((string) ($u['host'] ?? ''));
    if (in_array($h, WP_HOSTS, true)) return true;
    foreach (WP_HOST_SUFFIXES as $s) if (str_ends_with($h, $s)) return true;
    return false;
}

/* ───────────── storage ───────────── */

function wp_schema(PDO $pdo): void
{
    static $done = false;
    if ($done) return;
    $done = true;
    if ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql') {
        $pdo->exec('CREATE TABLE IF NOT EXISTS push_subscriptions (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(120) NOT NULL,
            endpoint VARCHAR(600) NOT NULL, endpoint_h CHAR(40) NOT NULL, p256dh VARCHAR(120) NOT NULL, auth VARCHAR(40) NOT NULL, lang VARCHAR(5) NOT NULL DEFAULT \'en\',
            created_at INT NOT NULL, seen_at INT NOT NULL, ok_at INT NULL, fails INT NOT NULL DEFAULT 0, UNIQUE KEY push_ep (endpoint_h), INDEX push_user (user_id)) DEFAULT CHARSET=utf8mb4');
        $pdo->exec('CREATE TABLE IF NOT EXISTS push_prefs (user_id VARCHAR(120) NOT NULL PRIMARY KEY, prefs TEXT NOT NULL, updated_at INT NOT NULL) DEFAULT CHARSET=utf8mb4');
        wp_schema_tz($pdo);
        return;
    }
    $pdo->exec('CREATE TABLE IF NOT EXISTS push_subscriptions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, endpoint TEXT NOT NULL,
        endpoint_h TEXT NOT NULL, p256dh TEXT NOT NULL, auth TEXT NOT NULL, lang TEXT NOT NULL DEFAULT \'en\', created_at INTEGER NOT NULL, seen_at INTEGER NOT NULL,
        ok_at INTEGER NULL, fails INTEGER NOT NULL DEFAULT 0)');
    $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS push_ep ON push_subscriptions (endpoint_h)');
    $pdo->exec('CREATE INDEX IF NOT EXISTS push_user ON push_subscriptions (user_id)');
    $pdo->exec('CREATE TABLE IF NOT EXISTS push_prefs (user_id TEXT NOT NULL PRIMARY KEY, prefs TEXT NOT NULL, updated_at INTEGER NOT NULL)');
    wp_schema_tz($pdo);
}
/** (5 Nov.) the device's time zone (quiet hours on the phone's own clock) */
function wp_schema_tz(PDO $pdo): void
{
    try { $pdo->exec('ALTER TABLE push_subscriptions ADD COLUMN tz ' . ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql' ? 'VARCHAR(64)' : 'TEXT') . ' NULL'); } catch (Throwable $e) { /* already there */ }
}

function wp_q(PDO $pdo, string $sql, array $a = []): PDOStatement { wp_schema($pdo); $st = $pdo->prepare($sql); $st->execute($a); return $st; }

/** every 15 minutes from the earliest to the latest time of a reminder */
function wp_times(string $kind): array
{
    [, $from, $to] = WP_KINDS[$kind];
    $out = [];
    if ($from === '') return $out;   // (the day's lock: sent when it happens)
    for ($m = (int) substr($from, 0, 2) * 60 + (int) substr($from, 3); $m <= (int) substr($to, 0, 2) * 60 + (int) substr($to, 3); $m += 15) $out[] = sprintf('%02d:%02d', intdiv($m, 60), $m % 60);
    return $out;
}

/** each reminder: on (push to the phone) and its time (New York; the bell's reminder too) */
function wp_prefs(PDO $pdo, string $uid): array
{
    $saved = json_decode((string) wp_q($pdo, 'SELECT prefs FROM push_prefs WHERE user_id = ?', [$uid])->fetchColumn(), true) ?: [];
    $out = [];
    foreach (WP_KINDS as $k => [$def]) {
        $p = (array) ($saved[$k] ?? []);
        $out[$k] = ['on' => array_key_exists('on', $p) ? (bool) $p['on'] : true, 'at' => in_array($p['at'] ?? '', wp_times($k), true) ? $p['at'] : $def];
    }
    return $out;
}

function wp_set_pref(PDO $pdo, string $uid, string $kind, array $in): bool
{
    if (!isset(WP_KINDS[$kind]) && !isset(WP_GROUPS[$kind])) return false;
    $all = wp_prefs($pdo, $uid);
    if (isset(WP_GROUPS[$kind])) {   // (5 Nov.) a group: its kinds together (on or off only)
        if (!array_key_exists('on', $in) || array_key_exists('at', $in)) return false;
        foreach (WP_GROUPS[$kind] as $k) $all[$k]['on'] = (bool) $in['on'];
        $kind = WP_GROUPS[$kind][0]; $in = [];
    }
    if (array_key_exists('on', $in)) $all[$kind]['on'] = (bool) $in['on'];
    if (array_key_exists('at', $in)) { if (!in_array($in['at'], wp_times($kind), true)) return false; $all[$kind]['at'] = $in['at']; }
    $j = json_encode($all);
    if (wp_q($pdo, 'UPDATE push_prefs SET prefs = ?, updated_at = ? WHERE user_id = ?', [$j, time(), $uid])->rowCount() === 0
        && !wp_q($pdo, 'SELECT 1 FROM push_prefs WHERE user_id = ?', [$uid])->fetchColumn())
        wp_q($pdo, 'INSERT INTO push_prefs (user_id, prefs, updated_at) VALUES (?, ?, ?)', [$uid, $j, time()]);
    return true;
}
/** a group is on when one of its kinds is (a trader who turned off one kind before 5 Nov. keeps that choice until he touches the group) */
function wp_groups(array $prefs): array
{
    $out = []; foreach (WP_GROUPS as $g => $ks) { $out[$g] = false; foreach ($ks as $k) if (!empty($prefs[$k]['on'])) $out[$g] = true; }
    return $out;
}
/** a valid time zone name (Intl, « Europe/Paris »), else null */
function wp_tz(?string $tz): ?string
{
    $tz = trim((string) $tz);
    if ($tz === '' || strlen($tz) > 64) return null;
    try { new DateTimeZone($tz); return $tz; } catch (Throwable $e) { return null; }
}
/** quiet hours on a device's clock (21:00 to 7:00); without its zone, New York's */
function wp_quiet(?string $tz, int $now): bool
{
    $h = (int) (new DateTimeImmutable('@' . $now))->setTimezone(new DateTimeZone(wp_tz($tz) ?? 'America/New_York'))->format('G');
    return $h >= WP_QUIET[0] || $h < WP_QUIET[1];
}

/** this device's subscription (the browser's endpoint and keys); the same device on another account moves to it */
function wp_subscribe(PDO $pdo, string $uid, array $b): bool
{
    $ep = (string) ($b['endpoint'] ?? ''); $k = (array) ($b['keys'] ?? []);
    $p256 = wp_b64u_d((string) ($k['p256dh'] ?? '')); $auth = wp_b64u_d((string) ($k['auth'] ?? ''));
    if (!wp_endpoint_ok($ep) || strlen($p256) !== 65 || $p256[0] !== "\x04" || strlen($auth) !== 16) return false;
    $lang = in_array($b['lang'] ?? '', ['en', 'fr', 'es'], true) ? $b['lang'] : 'en';
    $tz = wp_tz(is_string($b['tz'] ?? null) ? $b['tz'] : null);   // (5 Nov.) the phone's own clock, for the quiet hours
    $h = sha1($ep); $t = time();
    if (wp_q($pdo, 'UPDATE push_subscriptions SET user_id = ?, endpoint = ?, p256dh = ?, auth = ?, lang = ?, tz = COALESCE(?, tz), seen_at = ?, fails = 0 WHERE endpoint_h = ?', [$uid, $ep, wp_b64u($p256), wp_b64u($auth), $lang, $tz, $t, $h])->rowCount() === 0
        && !wp_q($pdo, 'SELECT 1 FROM push_subscriptions WHERE endpoint_h = ?', [$h])->fetchColumn())
        wp_q($pdo, 'INSERT INTO push_subscriptions (user_id, endpoint, endpoint_h, p256dh, auth, lang, tz, created_at, seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [$uid, $ep, $h, wp_b64u($p256), wp_b64u($auth), $lang, $tz, $t, $t]);
    $ids = wp_q($pdo, 'SELECT id FROM push_subscriptions WHERE user_id = ? ORDER BY seen_at DESC, id DESC', [$uid])->fetchAll(PDO::FETCH_COLUMN);
    foreach (array_slice($ids, WP_MAX_DEVICES) as $id) wp_q($pdo, 'DELETE FROM push_subscriptions WHERE id = ?', [$id]);   // the oldest devices
    return true;
}

function wp_unsubscribe(PDO $pdo, string $uid, string $endpoint): void
{
    wp_q($pdo, 'DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint_h = ?', [$uid, sha1($endpoint)]);
}

/** account deleted (api.php): its devices and settings go too */
function wp_delete_user(PDO $pdo, string $uid): void
{
    wp_q($pdo, 'DELETE FROM push_subscriptions WHERE user_id = ?', [$uid]);
    wp_q($pdo, 'DELETE FROM push_prefs WHERE user_id = ?', [$uid]);
}

function wp_devices(PDO $pdo, string $uid): int
{
    return (int) wp_q($pdo, 'SELECT COUNT(*) FROM push_subscriptions WHERE user_id = ?', [$uid])->fetchColumn();
}

/* ───────────── sending ───────────── */

/**
 * One message to one device; true when the push service took it. A gone subscription (404, 410, or failing for days) is
 * forgotten. $msg: title, body, url, tag (and track: the address the service worker calls when it is opened).
 */
function wp_deliver(PDO $pdo, array $s, array $msg, string $topic, array $cfg): bool
{
    $body = json_encode($msg, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    try {
        $code = wp_post($s['endpoint'], ['Authorization' => wp_vapid($s['endpoint'], $cfg), 'TTL' => '14400', 'Urgency' => 'normal', 'Topic' => substr(preg_replace('/[^A-Za-z0-9_-]/', '', $topic), 0, 32) ?: 'sweep',
            'Content-Encoding' => 'aes128gcm', 'Content-Type' => 'application/octet-stream'], wp_encrypt($body, wp_b64u_d($s['p256dh']), wp_b64u_d($s['auth'])));
    } catch (Throwable $e) { error_log('[Sweep push] ' . $e->getMessage()); $code = 0; }
    if ($code >= 200 && $code < 300) { wp_q($pdo, 'UPDATE push_subscriptions SET ok_at = ?, fails = 0 WHERE id = ?', [time(), $s['id']]); return true; }
    if ($code === 404 || $code === 410 || (int) $s['fails'] >= 9) wp_q($pdo, 'DELETE FROM push_subscriptions WHERE id = ?', [$s['id']]);   // gone, or failing for days
    else wp_q($pdo, 'UPDATE push_subscriptions SET fails = fails + 1 WHERE id = ?', [$s['id']]);
    return false;
}

/**
 * (5 Nov., brief notifications) the day's big release for the plan reminder: the first high-impact US event of the New York date
 * between 7:00 and 16:00 (econ-us-2026-2027.json, the calendar the app shows), as its line: « Big release today: CPI at 8:30 AM.
 * Plan around it. » Null without one.
 */
function wp_econ_line(string $lang, string $date): ?string
{
    static $ev = null;
    if ($ev === null) { $ev = []; foreach ((array) ((json_decode((string) @file_get_contents(dirname(__DIR__) . '/econ-us-2026-2027.json'), true) ?: [])['events'] ?? []) as $e) if (($e['impact'] ?? '') === 'high') $ev[(string) $e['date']][] = $e; }
    $day = array_values(array_filter($ev[$date] ?? [], fn($e) => ($e['time'] ?? '') >= '07:00' && ($e['time'] ?? '') < '16:00'));
    if (!$day) return null;
    usort($day, fn($a, $b) => strcmp((string) $a['time'], (string) $b['time']));
    $name = trim(preg_replace('~ (m/m|q/q)~', '', (string) $day[0]['event'])); [$H, $M] = array_map('intval', explode(':', (string) $day[0]['time']));
    $at = ['fr' => sprintf('%d h %02d', $H, $M), 'es' => sprintf('%d:%02d', $H, $M), 'en' => sprintf('%d:%02d %s', $H % 12 ?: 12, $M, $H < 12 ? 'AM' : 'PM')][$lang] ?? sprintf('%d:%02d', $H, $M);
    return strtr(['en' => 'Big release today: {e} at {t}. Plan around it.', 'fr' => 'Annonce importante aujourd’hui : {e} à {t}. Prévois-la dans ton plan.',
        'es' => 'Dato importante hoy: {e} a las {t}. Tenlo en tu plan.'][$lang] ?? 'Big release today: {e} at {t}. Plan around it.', ['{e}' => $name, '{t}' => $at]);
}

/** one reminder to each of the trader's devices, in the device's language, outside its quiet hours (except the plan and the
 *  account alerts); $params fill the text ({n}: the streak). Never throws. */
function wp_notify(PDO $pdo, string $uid, string $kind, string $url, array $params = []): int
{
    try {
        $cfg = wp_config();
        if (!$cfg || !isset(WP_KINDS[$kind]) || !isset(WP_TEXT['en'][$kind]) || empty(wp_prefs($pdo, $uid)[$kind]['on'])) return 0;
        $n = 0; $now = time();
        foreach (wp_q($pdo, 'SELECT * FROM push_subscriptions WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_ASSOC) as $s) {
            if (!in_array($kind, WP_QUIET_FREE, true) && wp_quiet($s['tz'] ?? null, $now)) continue;   // (5 Nov.) never at night on that phone
            $fill = fn(string $x) => strtr($x, array_combine(array_map(fn($k) => '{' . $k . '}', array_keys($params)), array_map('strval', $params)) ?: []);
            [$title, $body] = array_map($fill, (WP_TEXT[$s['lang']] ?? WP_TEXT['en'])[$kind]);
            if ($kind === 'plan') {   // (5 Nov.) the plan reminder says the day's big release, when there is one (the game's clock: its New York date)
                $d = (new DateTimeImmutable('@' . (class_exists('GameEngine', false) ? GameEngine::ts() : $now)))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d');
                $body = wp_econ_line(in_array($s['lang'], ['en', 'fr', 'es'], true) ? $s['lang'] : 'en', $d) ?? $body;
            }
            if (wp_deliver($pdo, $s, ['title' => $title, 'body' => $body, 'url' => $url, 'tag' => 'sweep-' . $kind], $kind, $cfg)) $n++;
        }
        return $n;
    } catch (Throwable $e) {
        error_log('[Sweep push] ' . $kind . ': ' . $e->getMessage());
        return 0;
    }
}

/* ───────────── routes (signed-in trader) ───────────── */

function wp_state(PDO $pdo, string $uid): array
{
    $cfg = wp_config();
    if (!$cfg) return ['available' => false];
    $times = []; foreach (array_keys(WP_KINDS) as $k) $times[$k] = wp_times($k);
    $prefs = wp_prefs($pdo, $uid);
    return ['available' => true, 'key' => $cfg['public_key'], 'prefs' => $prefs, 'groups' => wp_groups($prefs), 'times' => $times, 'devices' => wp_devices($pdo, $uid)];
}

function wp_route(string $route, string $method, string $uid): void
{
    $pdo = db();
    if ($route === 'api/push' && $method === 'GET') json_out(200, wp_state($pdo, $uid));
    if ($method !== 'POST') json_out(404, ['error' => 'not found']);
    if (!wp_config()) json_out(503, ['error' => 'Notifications are not set up yet.', 'code' => 'push_off']);
    $b = body_json(4096);
    if ($route === 'api/push/subscribe') { if (!wp_subscribe($pdo, $uid, $b)) json_out(400, ['error' => 'Unknown subscription.']); json_out(200, wp_state($pdo, $uid)); }
    if ($route === 'api/push/unsubscribe') { wp_unsubscribe($pdo, $uid, (string) ($b['endpoint'] ?? '')); json_out(200, wp_state($pdo, $uid)); }
    if ($route === 'api/push/prefs') {
        $in = array_intersect_key($b, ['on' => 1, 'at' => 1]);
        if (!wp_set_pref($pdo, $uid, (string) ($b['kind'] ?? ''), $in)) json_out(400, ['error' => 'Unknown reminder or time.']);
        json_out(200, wp_state($pdo, $uid));
    }
    json_out(404, ['error' => 'not found']);
}
