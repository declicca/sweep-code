<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Face ID in the app added to the Home Screen (17 Oct., step 2 of the second step at log-in).
 *  - Once, in the installed app: « Unlock Sweep with Face ID » makes a passkey (WebAuthn, the phone's own authenticator; Sweep
 *    keeps only its public key, never a face). It belongs to this phone (its remembered browser, auth/twofa.php).
 *  - Then the sessions of this phone lock after 12 hours without using the app: the server answers 423 to every data request
 *    until Face ID signs a fresh challenge (api/auth/unlock). « Use my password »: sign out and log in again.
 *  - Verified here with OpenSSL only: ES256 (P-256), the RP id hash, the « user present » and « user verified » flags, the
 *    challenge and the origin of the request.
 */
const PK_IDLE = 12 * 3600;

function pk_schema(): void {
    static $done = false; if ($done) return; $done = true;
    tf_schema();
    $pdo = db(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    if ($my) {
        $pdo->exec('CREATE TABLE IF NOT EXISTS passkeys (cred_id VARCHAR(255) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, device CHAR(64) NOT NULL, public_key TEXT NOT NULL, sign_count BIGINT NOT NULL DEFAULT 0, created_at INT NOT NULL, last_used INT NULL, INDEX (user_id)) DEFAULT CHARSET=utf8mb4');
        $pdo->exec('CREATE TABLE IF NOT EXISTS passkey_challenges (user_id VARCHAR(120) NOT NULL, kind VARCHAR(10) NOT NULL, challenge CHAR(64) NOT NULL, expires_at INT NOT NULL, PRIMARY KEY (user_id, kind)) DEFAULT CHARSET=utf8mb4');
        foreach (['passkey' => 'TINYINT NOT NULL DEFAULT 0', 'active_at' => 'INT NULL'] as $c => $t) if (!$pdo->query("SHOW COLUMNS FROM sessions LIKE '$c'")->fetch()) $pdo->exec("ALTER TABLE sessions ADD COLUMN $c $t");
    } else {
        $pdo->exec('CREATE TABLE IF NOT EXISTS passkeys (cred_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, device TEXT NOT NULL, public_key TEXT NOT NULL, sign_count INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL, last_used INTEGER)');
        $pdo->exec('CREATE TABLE IF NOT EXISTS passkey_challenges (user_id TEXT NOT NULL, kind TEXT NOT NULL, challenge TEXT NOT NULL, expires_at INTEGER NOT NULL, PRIMARY KEY (user_id, kind))');
        $cols = array_column($pdo->query('PRAGMA table_info(sessions)')->fetchAll(PDO::FETCH_ASSOC), 'name');
        if (!in_array('passkey', $cols, true)) $pdo->exec('ALTER TABLE sessions ADD COLUMN passkey INTEGER NOT NULL DEFAULT 0');
        if (!in_array('active_at', $cols, true)) $pdo->exec('ALTER TABLE sessions ADD COLUMN active_at INTEGER');
    }
}
function pk_b64u(string $b): string { return rtrim(strtr(base64_encode($b), '+/', '-_'), '='); }
function pk_unb64u(string $s): string { return (string) base64_decode(strtr($s, '-_', '+/') . str_repeat('=', (4 - strlen($s) % 4) % 4)); }
function pk_rp(): string { return strtolower(preg_replace('/:\d+$/', '', (string) ($_SERVER['HTTP_HOST'] ?? 'localhost'))); }
function pk_origin(): string { global $HTTPS; return ($HTTPS ? 'https://' : 'http://') . strtolower((string) ($_SERVER['HTTP_HOST'] ?? 'localhost')); }
function pk_session(): ?array {
    $t = (string) ($_COOKIE[COOKIE] ?? ''); if (!preg_match('/^[a-f0-9]{64}$/', $t)) return null;
    pk_schema();
    $r = q('SELECT token_hash, user_id, device, passkey, active_at FROM sessions WHERE token_hash = ?', [hash('sha256', $t)])->fetch();
    return $r ?: null;
}
/** a new session on a phone that has its passkey: it locks too (create_session) */
function pk_bind(string $tokenHash, ?string $device): void {
    if (!$device) return; pk_schema();
    if (q('SELECT 1 FROM passkeys WHERE device = ?', [$device])->fetchColumn()) q('UPDATE sessions SET passkey = 1, active_at = ? WHERE token_hash = ?', [time(), $tokenHash]);
}
/** true when this session must be unlocked by Face ID first; otherwise its activity is noted (every 5 minutes at most) */
function pk_locked(): bool {
    $s = pk_session(); if (!$s || (int) $s['passkey'] !== 1) return false;
    $a = (int) ($s['active_at'] ?? 0);
    if ($a < time() - PK_IDLE) return true;
    if ($a < time() - 300) q('UPDATE sessions SET active_at = ? WHERE token_hash = ?', [time(), $s['token_hash']]);
    return false;
}
function pk_challenge(string $uid, string $kind): string {
    $c = random_bytes(32);
    q('DELETE FROM passkey_challenges WHERE user_id = ? AND kind = ?', [$uid, $kind]);
    q('INSERT INTO passkey_challenges (user_id, kind, challenge, expires_at) VALUES (?, ?, ?, ?)', [$uid, $kind, bin2hex($c), time() + 300]);
    return pk_b64u($c);
}
function pk_take(string $uid, string $kind): ?string {
    $r = q('SELECT challenge, expires_at FROM passkey_challenges WHERE user_id = ? AND kind = ?', [$uid, $kind])->fetch();
    q('DELETE FROM passkey_challenges WHERE user_id = ? AND kind = ?', [$uid, $kind]);
    return $r && (int) $r['expires_at'] >= time() ? pk_b64u((string) hex2bin((string) $r['challenge'])) : null;
}
/** clientDataJSON: the right type, challenge and origin */
function pk_client(string $json, string $type, string $challenge): bool {
    $c = json_decode($json, true);
    return is_array($c) && ($c['type'] ?? '') === $type && hash_equals($challenge, (string) ($c['challenge'] ?? '')) && strtolower((string) ($c['origin'] ?? '')) === pk_origin();
}
/* a small CBOR reader: what an attestation object holds (maps, arrays, byte and text strings, integers) */
function pk_cbor(string $d, int &$i) {
    $b = ord($d[$i++]); $mt = $b >> 5; $ai = $b & 31;
    if ($ai < 24) $n = $ai;
    elseif ($ai === 24) $n = ord($d[$i++]);
    elseif ($ai === 25) { $n = unpack('n', substr($d, $i, 2))[1]; $i += 2; }
    elseif ($ai === 26) { $n = unpack('N', substr($d, $i, 4))[1]; $i += 4; }
    elseif ($ai === 27) { $n = unpack('J', substr($d, $i, 8))[1]; $i += 8; }
    else throw new RuntimeException('cbor');
    switch ($mt) {
        case 0: return $n;
        case 1: return -1 - $n;
        case 2: case 3: $v = substr($d, $i, $n); $i += $n; return $v;
        case 4: $a = []; for ($k = 0; $k < $n; $k++) $a[] = pk_cbor($d, $i); return $a;
        case 5: $m = []; for ($k = 0; $k < $n; $k++) { $key = pk_cbor($d, $i); $m[$key] = pk_cbor($d, $i); } return $m;
        case 7: return $ai === 20 ? false : ($ai === 21 ? true : null);
    }
    throw new RuntimeException('cbor');
}
/** authenticator data: the RP id, « present » and « verified », the counter (and, when registering, the credential and its key) */
function pk_auth(string $ad, bool $withCred): ?array {
    if (strlen($ad) < 37 || !hash_equals(hash('sha256', pk_rp(), true), substr($ad, 0, 32))) return null;
    $flags = ord($ad[32]); if (!($flags & 0x01) || !($flags & 0x04)) return null;
    $out = ['count' => unpack('N', substr($ad, 33, 4))[1]];
    if ($withCred) {
        if (!($flags & 0x40) || strlen($ad) < 55) return null;
        $len = unpack('n', substr($ad, 53, 2))[1]; $out['cred'] = substr($ad, 55, $len);
        $i = 55 + $len; $k = pk_cbor($ad, $i);
        if (($k[1] ?? null) !== 2 || ($k[3] ?? null) !== -7 || ($k[-1] ?? null) !== 1 || strlen((string) ($k[-2] ?? '')) !== 32 || strlen((string) ($k[-3] ?? '')) !== 32) return null;   // ES256 on P-256 only
        $der = hex2bin('3059301306072a8648ce3d020106082a8648ce3d030107034200') . "\x04" . $k[-2] . $k[-3];
        $out['pem'] = "-----BEGIN PUBLIC KEY-----\n" . chunk_split(base64_encode($der), 64, "\n") . "-----END PUBLIC KEY-----\n";
    }
    return $out;
}
function pk_route(string $route, string $method, ?array $me): void {
    pk_schema();
    $b = $method === 'POST' ? body_json(65536) : [];
    $s = pk_session();
    if ($route === 'api/me/passkey' && $method === 'GET') {
        $has = $s && $s['device'] && q('SELECT 1 FROM passkeys WHERE user_id = ? AND device = ?', [$me['id'], $s['device']])->fetchColumn();
        json_out(200, ['on' => tf_on() && (bool) ($s['device'] ?? null), 'has' => (bool) $has]);
    }
    if ($route === 'api/me/passkey/options' && $method === 'POST') {
        if (!$s || !$s['device']) json_out(400, ['error' => 'Log in again on this phone first.']);
        $ex = array_map(fn($r) => ['type' => 'public-key', 'id' => $r['cred_id']], q('SELECT cred_id FROM passkeys WHERE user_id = ?', [$me['id']])->fetchAll());
        json_out(200, ['challenge' => pk_challenge((string) $me['id'], 'create'), 'rp' => ['id' => pk_rp(), 'name' => 'Sweep'], 'user' => ['id' => pk_b64u(hash('sha256', 'sweep|' . $me['id'], true)), 'name' => (string) ($me['email'] ?: $me['username']), 'displayName' => (string) ($me['first_name'] ?: $me['username'])], 'exclude' => $ex]);
    }
    if ($route === 'api/me/passkey/register' && $method === 'POST') {
        if (!$s || !$s['device']) json_out(400, ['error' => 'Log in again on this phone first.']);
        $ch = pk_take((string) $me['id'], 'create'); $cd = pk_unb64u((string) ($b['clientDataJSON'] ?? ''));
        if (!$ch || !pk_client($cd, 'webauthn.create', $ch)) json_out(400, ['error' => 'Face ID could not be set up. Try again.']);
        try { $i = 0; $att = pk_cbor(pk_unb64u((string) ($b['attestationObject'] ?? '')), $i); } catch (Throwable $e) { json_out(400, ['error' => 'Face ID could not be set up. Try again.']); }
        $a = pk_auth((string) ($att['authData'] ?? ''), true);
        if (!$a || !hash_equals($a['cred'], pk_unb64u((string) ($b['id'] ?? '')))) json_out(400, ['error' => 'Face ID could not be set up. Try again.']);
        q('DELETE FROM passkeys WHERE user_id = ? AND device = ?', [$me['id'], $s['device']]);   // one per phone
        q('INSERT INTO passkeys (cred_id, user_id, device, public_key, sign_count, created_at) VALUES (?, ?, ?, ?, ?, ?)', [pk_b64u($a['cred']), $me['id'], $s['device'], $a['pem'], $a['count'], time()]);
        q('UPDATE sessions SET passkey = 1, active_at = ? WHERE token_hash = ?', [time(), $s['token_hash']]);
        json_out(200, ['ok' => true]);
    }
    if ($route === 'api/me/passkey/remove' && $method === 'POST') {
        if ($s && $s['device']) { q('DELETE FROM passkeys WHERE user_id = ? AND device = ?', [$me['id'], $s['device']]); q('UPDATE sessions SET passkey = 0 WHERE user_id = ? AND device = ?', [$me['id'], $s['device']]); }
        json_out(200, ['ok' => true]);
    }
    // a locked session: the challenge, then Face ID's answer
    if ($route === 'api/auth/unlock/options' && $method === 'POST') {
        if (!$s) json_out(401, ['error' => 'Signed out.']);
        $creds = q('SELECT cred_id FROM passkeys WHERE user_id = ? AND device = ?', [$s['user_id'], (string) $s['device']])->fetchAll();
        if (!$creds) json_out(404, ['error' => 'No Face ID on this phone.']);
        json_out(200, ['challenge' => pk_challenge((string) $s['user_id'], 'get'), 'rpId' => pk_rp(), 'allow' => array_map(fn($r) => ['type' => 'public-key', 'id' => $r['cred_id']], $creds)]);
    }
    if ($route === 'api/auth/unlock' && $method === 'POST') {
        if (!$s) json_out(401, ['error' => 'Signed out.']);
        throttle(['pk:' . $s['user_id']], 20, 900);
        $fail = function () use ($s) { record_attempt(['pk:' . $s['user_id']]); json_out(401, ['error' => 'Face ID did not unlock Sweep. Try again, or use your password.']); };
        $ch = pk_take((string) $s['user_id'], 'get'); $cd = pk_unb64u((string) ($b['clientDataJSON'] ?? ''));
        if (!$ch || !pk_client($cd, 'webauthn.get', $ch)) $fail();
        $k = q('SELECT * FROM passkeys WHERE cred_id = ? AND user_id = ? AND device = ?', [(string) ($b['id'] ?? ''), $s['user_id'], (string) $s['device']])->fetch();
        $ad = pk_unb64u((string) ($b['authenticatorData'] ?? '')); $a = pk_auth($ad, false);
        if (!$k || !$a) $fail();
        if (openssl_verify($ad . hash('sha256', $cd, true), pk_unb64u((string) ($b['signature'] ?? '')), (string) $k['public_key'], OPENSSL_ALGO_SHA256) !== 1) $fail();
        if ((int) $k['sign_count'] > 0 && $a['count'] > 0 && $a['count'] <= (int) $k['sign_count']) $fail();   // a copied key
        q('UPDATE passkeys SET sign_count = ?, last_used = ? WHERE cred_id = ?', [$a['count'], time(), $k['cred_id']]);
        q('UPDATE sessions SET active_at = ? WHERE token_hash = ?', [time(), $s['token_hash']]);
        json_out(200, ['ok' => true]);
    }
}
