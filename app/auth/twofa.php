<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — a second step at log-in, on a browser Sweep does not know yet (17 Oct., Mateo: « secure, but not an irritant »).
 *  - After the right password on a new browser: a 6-digit code by email (10 minutes, 5 tries, 3 sends), then this browser is
 *    remembered 30 days, renewed at each log-in (cookie tj_dev; only its hash is stored). A known browser: the password only.
 *  - Signing up, a password reset by the email link and a recovery code already prove the trader: that browser is trusted.
 *  - Settings › « Your devices »: each remembered browser, « Sign out » ends its sessions and forgets it.
 *  - Off when no mailbox is set ($cfg['smtp']: the code could not arrive), or with $cfg['twofa'] = false (emergency switch in
 *    config.php). The dev copy (SWEEP_TEST_DB) writes its emails to data/outbox.jsonl (notify/mail.php) and keeps it on.
 */
const TF_DEV = 'tj_dev';
const TF_PENDING = 'tj_2fa';
const TF_DEV_TTL = 30 * 86400;
const TF_CODE_TTL = 600;

function tf_schema(): void {
    static $done = false; if ($done) return; $done = true;
    $pdo = db(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    if ($my) {
        $pdo->exec('CREATE TABLE IF NOT EXISTS trusted_devices (token_hash CHAR(64) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, label VARCHAR(120) NOT NULL, created_at INT NOT NULL, last_seen INT NOT NULL, expires_at INT NOT NULL, INDEX (user_id)) DEFAULT CHARSET=utf8mb4');
        $pdo->exec('CREATE TABLE IF NOT EXISTS login_codes (pending_hash CHAR(64) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, code_hash CHAR(64) NOT NULL, created_at INT NOT NULL, sent_at INT NOT NULL, expires_at INT NOT NULL, tries INT NOT NULL DEFAULT 0, sends INT NOT NULL DEFAULT 1, INDEX (user_id)) DEFAULT CHARSET=utf8mb4');
        if (!$pdo->query("SHOW COLUMNS FROM sessions LIKE 'device'")->fetch()) $pdo->exec('ALTER TABLE sessions ADD COLUMN device CHAR(64) NULL');
    } else {
        $pdo->exec('CREATE TABLE IF NOT EXISTS trusted_devices (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, label TEXT NOT NULL, created_at INTEGER NOT NULL, last_seen INTEGER NOT NULL, expires_at INTEGER NOT NULL)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS trusted_devices_user ON trusted_devices(user_id)');
        $pdo->exec('CREATE TABLE IF NOT EXISTS login_codes (pending_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, code_hash TEXT NOT NULL, created_at INTEGER NOT NULL, sent_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, tries INTEGER NOT NULL DEFAULT 0, sends INTEGER NOT NULL DEFAULT 1)');
        $cols = array_column($pdo->query('PRAGMA table_info(sessions)')->fetchAll(PDO::FETCH_ASSOC), 'name');
        if (!in_array('device', $cols, true)) $pdo->exec('ALTER TABLE sessions ADD COLUMN device TEXT');
    }
}
function tf_on(): bool {
    global $cfg;
    if (isset($cfg['twofa']) && $cfg['twofa'] === false) return false;
    if (getenv('SWEEP_TEST_DB')) return true;
    $sc = (array) ($cfg['smtp'] ?? []);
    return !empty($sc['host']) && !empty($sc['user']) && !empty($sc['pass']);
}
function tf_cookie(string $name, string $value, int $expires): void {
    global $HTTPS;
    setcookie($name, $value, ['expires' => $expires, 'path' => cookie_path(), 'secure' => $HTTPS, 'httponly' => true, 'samesite' => 'Lax']);
}
/** a short name for the browser, for « Your devices » (never the full user agent) */
function tf_label(): string {
    $ua = (string) ($_SERVER['HTTP_USER_AGENT'] ?? '');
    $os = preg_match('/iPhone/', $ua) ? 'iPhone' : (preg_match('/iPad/', $ua) ? 'iPad' : (preg_match('/Android/', $ua) ? 'Android' : (preg_match('/Mac OS X|Macintosh/', $ua) ? 'Mac' : (preg_match('/Windows/', $ua) ? 'Windows' : (preg_match('/Linux/', $ua) ? 'Linux' : '')))));
    $br = preg_match('/Edg\//', $ua) ? 'Edge' : (preg_match('/Firefox\//', $ua) ? 'Firefox' : (preg_match('/CriOS|Chrome\//', $ua) ? 'Chrome' : (preg_match('/Safari\//', $ua) ? 'Safari' : '')));
    return trim($br . ($br && $os ? ' · ' : '') . $os) ?: 'Browser';
}
/** this browser, remembered for this trader: its hash (the remembrance renewed), else null */
function tf_device_ok(string $uid): ?string {
    tf_schema();
    $t = (string) ($_COOKIE[TF_DEV] ?? ''); if (!preg_match('/^[a-f0-9]{64}$/', $t)) return null;
    $h = hash('sha256', $t);
    $r = q('SELECT user_id, expires_at FROM trusted_devices WHERE token_hash = ?', [$h])->fetch();
    if (!$r || (string) $r['user_id'] !== $uid || (int) $r['expires_at'] < time()) return null;
    $exp = time() + TF_DEV_TTL;
    q('UPDATE trusted_devices SET last_seen = ?, expires_at = ? WHERE token_hash = ?', [time(), $exp, $h]);
    tf_cookie(TF_DEV, $t, $exp);
    return $h;
}
/** remember this browser for the trader (30 days): its hash */
function tf_trust(string $uid): string {
    tf_schema();
    $t = bin2hex(random_bytes(32)); $h = hash('sha256', $t); $exp = time() + TF_DEV_TTL;
    q('INSERT INTO trusted_devices (token_hash, user_id, label, created_at, last_seen, expires_at) VALUES (?, ?, ?, ?, ?, ?)', [$h, $uid, tf_label(), time(), time(), $exp]);
    tf_cookie(TF_DEV, $t, $exp);
    if (random_int(1, 20) === 1) { q('DELETE FROM trusted_devices WHERE expires_at < ?', [time()]); q('DELETE FROM login_codes WHERE expires_at < ?', [time() - 3600]); }
    return $h;
}
function tf_mask(string $email): string {
    [$a, $d] = array_pad(explode('@', $email, 2), 2, '');
    return mb_substr($a, 0, 1) . str_repeat('•', max(2, min(5, mb_strlen($a) - 1))) . '@' . $d;
}
function tf_send(string $uid, string $code): bool {
    $u = q('SELECT email, first_name, username, lang FROM users WHERE id = ?', [$uid])->fetch();
    if (!$u || !$u['email']) return false;
    $l = lang_code($u['lang'] ?? 'en'); $first = (string) ($u['first_name'] ?: $u['username']);
    $L = ['en' => ['s' => "Your Sweep code: $code", 'hi' => "Hi $first,", 'p' => 'Your code to log in to Sweep on a new browser:', 'p2' => 'It works for 10 minutes. If you did not try to log in, change your password: someone knows it.'],
          'fr' => ['s' => "Ton code Sweep : $code", 'hi' => "Salut $first,", 'p' => 'Ton code pour te connecter à Sweep sur un nouveau navigateur :', 'p2' => 'Il est valable 10 minutes. Si ce n’est pas toi qui essaies de te connecter, change ton mot de passe : quelqu’un le connaît.'],
          'es' => ['s' => "Tu código de Sweep: $code", 'hi' => "Hola $first,", 'p' => 'Tu código para entrar en Sweep desde un navegador nuevo:', 'p2' => 'Vale 10 minutos. Si no fuiste tú, cambia tu contraseña: alguien la conoce.']][$l];
    $h = fn($x) => htmlspecialchars($x, ENT_QUOTES, 'UTF-8');
    $text = $L['hi'] . "\n\n" . $L['p'] . "\n\n$code\n\n" . $L['p2'] . "\n\n— Sweep";
    $html = '<!doctype html><html><body style="margin:0;background:#0b0b0c;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;color:#e9e9ee">'
      . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="100%" style="max-width:520px;background:#141416;border:1px solid #26262a;border-radius:18px" cellpadding="32"><tr><td>'
      . '<div style="font-size:18px;font-weight:700;letter-spacing:-.01em;margin-bottom:24px">sweep</div>'
      . '<p style="margin:0 0 12px;font-size:16px">' . $h($L['hi']) . '</p><p style="margin:0 0 16px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($L['p']) . '</p>'
      . '<div style="font-family:ui-monospace,Menlo,monospace;font-size:32px;font-weight:700;letter-spacing:.18em;color:#ffffff;margin:0 0 20px">' . $h($code) . '</div>'
      . '<p style="margin:0;font-size:13px;line-height:1.55;color:#8a8a94">' . $h($L['p2']) . '</p></td></tr></table></td></tr></table></body></html>';
    return sweep_mail((string) $u['email'], $L['s'], $text, $html);
}
/** after the code: « New log-in to your Sweep account » — the browser, the time (New York), what to do if it was not him */
function tf_notice(string $uid): void {
    global $APP_URL;
    try {
        $u = q('SELECT email, first_name, username, lang FROM users WHERE id = ?', [$uid])->fetch(); if (!$u || !$u['email']) return;
        $l = lang_code($u['lang'] ?? 'en'); $first = (string) ($u['first_name'] ?: $u['username']);
        $at = new DateTimeImmutable('now', new DateTimeZone('America/New_York'));
        $when = $l === 'fr' ? $at->format('j') . ' ' . ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'][(int) $at->format('n')] . ' à ' . $at->format('G') . ' h ' . $at->format('i')
            : ($l === 'es' ? $at->format('j') . ' de ' . ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'][(int) $at->format('n')] . ' a las ' . $at->format('G:i') : $at->format('F j \a\t g:i A'));
        $base = $APP_URL !== '/' ? rtrim((string) $APP_URL, '/') . '/' : ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' ? 'https://' : 'http://') . ($_SERVER['HTTP_HOST'] ?? 'localhost') . '/');
        $link = $base . '#settings'; $dev = tf_label();
        $L = ['en' => ['s' => 'New log-in to your Sweep account', 'hi' => "Hi $first,", 'p' => "Your account was just opened on a new browser: $dev, on $when (New York time).", 'p2' => 'If it was you, there is nothing to do. If not: change your password now, then sign this device out in Settings › Your devices.', 'b' => 'Open my devices'],
              'fr' => ['s' => 'Nouvelle connexion à ton compte Sweep', 'hi' => "Salut $first,", 'p' => "Ton compte vient d’être ouvert sur un nouveau navigateur : $dev, le $when (heure de New York).", 'p2' => 'Si c’est toi, rien à faire. Sinon : change ton mot de passe tout de suite, puis déconnecte cet appareil dans Réglages › Tes appareils.', 'b' => 'Voir mes appareils'],
              'es' => ['s' => 'Nuevo inicio de sesión en tu cuenta de Sweep', 'hi' => "Hola $first,", 'p' => "Tu cuenta se acaba de abrir en un navegador nuevo: $dev, el $when (hora de Nueva York).", 'p2' => 'Si fuiste tú, no hay nada que hacer. Si no: cambia tu contraseña ahora y cierra la sesión de este dispositivo en Ajustes › Tus dispositivos.', 'b' => 'Ver mis dispositivos']][$l];
        $h = fn($x) => htmlspecialchars($x, ENT_QUOTES, 'UTF-8');
        $text = $L['hi'] . "\n\n" . $L['p'] . "\n\n" . $L['p2'] . "\n\n" . $link . "\n\n— Sweep";
        $html = '<!doctype html><html><body style="margin:0;background:#0b0b0c;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;color:#e9e9ee">'
          . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="100%" style="max-width:520px;background:#141416;border:1px solid #26262a;border-radius:18px" cellpadding="32"><tr><td>'
          . '<div style="font-size:18px;font-weight:700;letter-spacing:-.01em;margin-bottom:24px">sweep</div>'
          . '<p style="margin:0 0 12px;font-size:16px">' . $h($L['hi']) . '</p><p style="margin:0 0 12px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($L['p']) . '</p>'
          . '<p style="margin:0 0 24px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($L['p2']) . '</p>'
          . '<a href="' . $h($link) . '" style="display:inline-block;background:#4c8dff;color:#0b0b0c;font-weight:600;font-size:15px;text-decoration:none;padding:13px 24px;border-radius:999px">' . $h($L['b']) . '</a>'
          . '</td></tr></table></td></tr></table></body></html>';
        sweep_mail((string) $u['email'], $L['s'], $text, $html);
    } catch (Throwable $e) { error_log('[Sweep 2fa] notice: ' . $e->getMessage()); }   // never blocks the log-in
}
/** the right password on a new browser: a code by email; the answer the log-in page shows */
function tf_start(string $uid, string $email): array {
    tf_schema();
    $p = bin2hex(random_bytes(32)); $code = str_pad((string) random_int(0, 999999), 6, '0', STR_PAD_LEFT);
    q('DELETE FROM login_codes WHERE user_id = ?', [$uid]);   // one code at a time
    q('INSERT INTO login_codes (pending_hash, user_id, code_hash, created_at, sent_at, expires_at, tries, sends) VALUES (?, ?, ?, ?, ?, ?, 0, 1)',
      [hash('sha256', $p), $uid, hash('sha256', $p . '|' . $code), time(), time(), time() + TF_CODE_TTL]);
    tf_cookie(TF_PENDING, $p, time() + TF_CODE_TTL);
    if (!tf_send($uid, $code)) json_out(503, ['error' => 'Your code could not be sent. Try again in a minute, or use a recovery code.']);
    return ['code' => true, 'to' => tf_mask($email)];
}
function tf_pending(): ?array {
    tf_schema();
    $p = (string) ($_COOKIE[TF_PENDING] ?? ''); if (!preg_match('/^[a-f0-9]{64}$/', $p)) return null;
    $r = q('SELECT * FROM login_codes WHERE pending_hash = ?', [hash('sha256', $p)])->fetch();
    return $r ? $r + ['_p' => $p] : null;
}
/** the 6 digits: right → the trader's id (the row gone), wrong → null (5 tries, then a new log-in is needed) */
function tf_check(string $code): ?string {
    $r = tf_pending();
    if (!$r || (int) $r['expires_at'] < time() || (int) $r['tries'] >= 5) return null;
    $code = preg_replace('/\D/', '', $code);
    if (strlen($code) === 6 && hash_equals((string) $r['code_hash'], hash('sha256', $r['_p'] . '|' . $code))) {
        q('DELETE FROM login_codes WHERE pending_hash = ?', [$r['pending_hash']]);
        tf_cookie(TF_PENDING, '', time() - 3600);
        return (string) $r['user_id'];
    }
    q('UPDATE login_codes SET tries = tries + 1 WHERE pending_hash = ?', [$r['pending_hash']]);
    return null;
}
/** routes before the session: the code, a new code */
function tf_route(string $route): void {
    if ($route === 'api/auth/code') {
        $b = body_json(1024);
        throttle(['2fa:' . client_ip()], 20, 900);
        $uid = tf_check((string) ($b['code'] ?? ''));
        if (!$uid) {
            record_attempt(['2fa:' . client_ip()]);
            $r = tf_pending();
            if (!$r || (int) $r['expires_at'] < time() || (int) $r['tries'] >= 5) json_out(410, ['error' => 'This code has expired. Log in again to get a new one.']);
            json_out(401, ['error' => 'Wrong code. Check the last email from Sweep.']);
        }
        $d = q('SELECT disabled FROM users WHERE id = ?', [$uid])->fetchColumn();
        if ((int) $d === 1) json_out(403, ['error' => 'This account is disabled. Contact Sweep support.']);
        create_session($uid, tf_trust($uid));
        tf_notice($uid);   // step 3: « New log-in to your Sweep account », with what to do if it was not him
        if (function_exists('nt_fire')) nt_fire('user.signed_in', ['uid' => $uid]);
        json_out(200, ['ok' => true]);
    }
    if ($route === 'api/auth/code/resend') {
        $r = tf_pending();
        if (!$r || (int) $r['expires_at'] < time()) json_out(410, ['error' => 'This code has expired. Log in again to get a new one.']);
        if ((int) $r['sends'] >= 3 || time() - (int) $r['sent_at'] < 30) json_out(429, ['error' => 'Wait a little before asking for another code.']);
        $code = str_pad((string) random_int(0, 999999), 6, '0', STR_PAD_LEFT);
        q('UPDATE login_codes SET code_hash = ?, sent_at = ?, sends = sends + 1, tries = 0, expires_at = ? WHERE pending_hash = ?', [hash('sha256', $r['_p'] . '|' . $code), time(), time() + TF_CODE_TTL, $r['pending_hash']]);
        tf_cookie(TF_PENDING, $r['_p'], time() + TF_CODE_TTL);
        if (!tf_send((string) $r['user_id'], $code)) json_out(503, ['error' => 'Your code could not be sent. Try again in a minute, or use a recovery code.']);
        json_out(200, ['ok' => true]);
    }
}
/** Settings › « Your devices »: the remembered browsers; « Sign out » one of them */
function tf_devices_route(string $route, string $method, string $uid): void {
    tf_schema();
    $mine = (string) ($_COOKIE[TF_DEV] ?? ''); $mineH = preg_match('/^[a-f0-9]{64}$/', $mine) ? hash('sha256', $mine) : '';
    if ($route === 'api/me/devices' && $method === 'GET') {
        $rows = q('SELECT token_hash, label, created_at, last_seen FROM trusted_devices WHERE user_id = ? AND expires_at > ? ORDER BY last_seen DESC LIMIT 20', [$uid, time()])->fetchAll();
        json_out(200, ['on' => tf_on(), 'devices' => array_map(fn($r) => ['id' => substr((string) $r['token_hash'], 0, 16), 'label' => (string) $r['label'], 'since' => (int) $r['created_at'], 'seen' => (int) $r['last_seen'], 'this' => $r['token_hash'] === $mineH], $rows)]);
    }
    if ($route === 'api/me/devices/forget' && $method === 'POST') {
        $id = preg_replace('/[^a-f0-9]/', '', (string) (body_json(512)['id'] ?? ''));
        if (strlen($id) !== 16) json_out(400, ['error' => 'Unknown device.']);
        foreach (q('SELECT token_hash FROM trusted_devices WHERE user_id = ?', [$uid])->fetchAll() as $r) {
            if (strpos((string) $r['token_hash'], $id) !== 0) continue;
            q('DELETE FROM sessions WHERE user_id = ? AND device = ?', [$uid, $r['token_hash']]);
            q('DELETE FROM trusted_devices WHERE token_hash = ?', [$r['token_hash']]);
        }
        json_out(200, ['ok' => true]);
    }
}
