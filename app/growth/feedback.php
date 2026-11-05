<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Feedback (ported from the feedback module to Sweep's database, sessions and data folder).
 * Types: experience (rating 1-5), idea, bug. 2000 characters max. Optional screenshot (PNG/JPG/WebP, 5 MB),
 * stored in the data folder with a random name. Statuses: new, planned, in_progress, shipped, declined.
 * 10 sends per trader per day. Email to the support address on each send (sweep_mail: the SMTP mailbox, like every other email).
 * A one-click answer in an email (mail/mail-admin.php, api/m/r/…) is a line here too: src_queue (the email), src_q (its
 * question), answer and answer_i (the choice and its place), type experience (a note from 1 to 5) or answer.
 */
const FB_TYPES = ['bug', 'idea', 'experience'], FB_STATUSES = ['new', 'planned', 'in_progress', 'shipped', 'declined'];
const FB_MAX_CHARS = 2000, FB_MAX_SHOT = 5 * 1048576, FB_MAX_PER_DAY = 10;

function fb_schema(PDO $pdo): void
{
    static $done = false; if ($done) return; $done = true;
    $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $id = $my ? 'INT UNSIGNED AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
    $k = $my ? 'VARCHAR(64)' : 'TEXT'; $txt = $my ? 'MEDIUMTEXT' : 'TEXT';
    $pdo->exec("CREATE TABLE IF NOT EXISTS feedback (id $id, user_id $k NOT NULL, type $k NOT NULL, rating INTEGER NULL, message $txt NOT NULL, page $k NULL,
        context $txt NULL, screenshot $k NULL, status $k NOT NULL, reply $txt NULL, created_at INTEGER NOT NULL, updated_at INTEGER NULL)" . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
    foreach (['src_queue' => 'INTEGER NULL', 'src_campaign' => 'INTEGER NULL', 'src_q' => 'INTEGER NULL', 'question' => "$txt NULL", 'answer' => 'VARCHAR(120) NULL', 'answer_i' => 'INTEGER NULL'] as $c => $t) {
        try { $pdo->exec("ALTER TABLE feedback ADD COLUMN $c $t"); } catch (Throwable $e) { /* already there */ }
    }
}
function fb_q(PDO $pdo, string $sql, array $a = []): PDOStatement { $st = $pdo->prepare($sql); $st->execute($a); return $st; }
function fb_dir(): string { global $DATA; return $DATA . '/feedback'; }

function fb_create(PDO $pdo, string $uid, array $in, ?string $plan): array
{
    fb_schema($pdo);
    if ((int) fb_q($pdo, 'SELECT COUNT(*) FROM feedback WHERE user_id = ? AND created_at > ?', [$uid, time() - 86400])->fetchColumn() >= FB_MAX_PER_DAY) return ['error' => 'limit'];
    $type = in_array($in['type'] ?? '', FB_TYPES, true) ? $in['type'] : null;
    $msg = trim((string) ($in['message'] ?? ''));
    if (!$type || $msg === '') return ['error' => 'invalid'];
    $msg = g_sub($msg, 0, FB_MAX_CHARS);
    $rating = null;
    if ($type === 'experience' && isset($in['rating'])) { $r = (int) $in['rating']; if ($r >= 1 && $r <= 5) $rating = $r; }
    $shot = null;
    if (!empty($in['shot'])) { $shot = fb_store_shot((string) $in['shot']); if ($shot === false) return ['error' => 'file']; }
    $ctx = ['ua' => g_sub((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 300), 'screen' => g_sub((string) ($in['screen'] ?? ''), 0, 20),
        'lang' => g_sub((string) ($in['lang'] ?? ''), 0, 10), 'version' => g_sub((string) ($in['version'] ?? ''), 0, 20), 'plan' => $plan];
    fb_q($pdo, 'INSERT INTO feedback (user_id, type, rating, message, page, context, screenshot, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [$uid, $type, $rating, $msg, g_sub((string) ($in['page'] ?? ''), 0, 120) ?: null, json_encode($ctx, JSON_UNESCAPED_UNICODE), $shot, 'new', time()]);
    $id = (int) $pdo->lastInsertId();
    fb_notify($pdo, $id, $type, $rating, $msg, $uid);
    return ['ok' => true, 'id' => $id];
}
/** data:image/...;base64 → a random file in the data folder (checked by its real content type). */
function fb_store_shot(string $dataUrl)
{
    if (!preg_match('#^data:image/(png|jpeg|webp);base64,(.+)$#s', $dataUrl, $m)) return false;
    $bin = base64_decode($m[2], true);
    if ($bin === false || strlen($bin) > FB_MAX_SHOT || strlen($bin) < 64) return false;
    $mime = function_exists('finfo_buffer') ? (new finfo(FILEINFO_MIME_TYPE))->buffer($bin) : 'image/' . $m[1];
    $ext = ['image/png' => 'png', 'image/jpeg' => 'jpg', 'image/webp' => 'webp'][$mime] ?? null;
    if (!$ext) return false;
    $dir = fb_dir(); if (!is_dir($dir)) @mkdir($dir, 0750, true);
    $name = bin2hex(random_bytes(16)) . '.' . $ext;
    return @file_put_contents($dir . '/' . $name, $bin) !== false ? $name : false;
}
function fb_notify(PDO $pdo, int $id, string $type, ?int $rating, string $msg, string $uid): void
{
    global $SUPPORT, $APP_URL;
    $to = (string) ($SUPPORT ?? ''); if ($to === '' || !function_exists('sweep_mail')) return;
    $u = fb_q($pdo, 'SELECT username, email FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
    $who = ($u['username'] ?? $uid) . (!empty($u['email']) ? ' <' . $u['email'] . '>' : '');
    $subj = '[Sweep] Feedback ' . $type . ($rating ? ' ' . $rating . '/5' : '') . ' #' . $id;
    $body = "From: $who\n\n$msg\n\n" . rtrim((string) $APP_URL, '/') . "/#admin";
    try { sweep_mail($to, $subj, $body); } catch (Throwable $e) { error_log('[Sweep feedback] email #' . $id . ': ' . $e->getMessage()); }   // the feedback is saved either way
}
function fb_out(array $r, bool $admin = false): array
{
    $o = ['id' => (int) $r['id'], 'type' => $r['type'], 'rating' => $r['rating'] !== null ? (int) $r['rating'] : null, 'message' => $r['message'], 'status' => $r['status'],
        'reply' => $r['reply'], 'created' => gmdate('c', (int) $r['created_at']), 'shot' => $r['screenshot'] ? 'api/feedback/shot/' . (int) $r['id'] : null];
    if ($admin) { $o['page'] = $r['page']; $o['context'] = json_decode((string) $r['context'], true); $o['user'] = $r['username'] ?? null; $o['email'] = $r['email'] ?? null; }
    if (($r['src_queue'] ?? null) !== null) $o['mail'] = ['question' => $r['question'], 'answer' => $r['answer'], 'campaign' => $r['src_campaign'] !== null ? (int) $r['src_campaign'] : null];
    return $o;
}
function fb_list_mine(PDO $pdo, string $uid): array { fb_schema($pdo); return array_map('fb_out', fb_q($pdo, 'SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 50', [$uid])->fetchAll(PDO::FETCH_ASSOC)); }
/**
 * $f, the filters of « What traders say » (Admin › Feedback): camp (an email), q and a (one of its questions, one option),
 * nps (p 9-10, pa 7-8, d 0-6: the « Day 30 » email's notes), notes (only the lines with a comment).
 */
function fb_admin_list(PDO $pdo, ?string $status, ?string $type, array $f = []): array
{
    fb_schema($pdo);
    $sql = 'SELECT f.*, u.username, u.email FROM feedback f LEFT JOIN users u ON u.id = f.user_id WHERE 1=1'; $a = [];
    if (isset($f['camp']) && $f['camp'] !== '') { $sql .= ' AND f.src_campaign = ?'; $a[] = (int) $f['camp'];
        if (isset($f['q']) && $f['q'] !== '') { $sql .= ' AND f.src_q = ?'; $a[] = (int) $f['q']; }
        if (isset($f['a']) && $f['a'] !== '') { $sql .= ' AND f.answer_i = ?'; $a[] = (int) $f['a']; } }
    $np = ['p' => [9, 10], 'pa' => [7, 8], 'd' => [0, 6]][$f['nps'] ?? ''] ?? null;
    if ($np) { $sql .= " AND f.src_campaign IN (SELECT id FROM mail_campaigns WHERE auto = 'nps30') AND f.answer_i BETWEEN ? AND ?"; array_push($a, ...$np); }
    if (!empty($f['notes'])) $sql .= " AND f.message <> ''";
    if ($status && in_array($status, FB_STATUSES, true)) { $sql .= ' AND f.status = ?'; $a[] = $status; }
    if ($type && in_array($type, FB_TYPES, true)) { $sql .= ' AND f.type = ? AND f.src_queue IS NULL'; $a[] = $type; }
    if ($type === 'mail') $sql .= ' AND f.src_queue IS NOT NULL';   // the one-click answers in the emails
    $rows = fb_q($pdo, $sql . ' ORDER BY COALESCE(f.updated_at, f.created_at) DESC LIMIT 300', $a)->fetchAll(PDO::FETCH_ASSOC);
    // an answer's email: its name (an automation's in the three languages)
    $names = [];
    try {
        foreach (fb_q($pdo, 'SELECT id, name, auto FROM mail_campaigns')->fetchAll(PDO::FETCH_ASSOC) as $c)
            $names[(int) $c['id']] = $c['auto'] !== null && function_exists('ma_info') && ($i = ma_info($c['auto'])) ? $i['name'] : ['en' => $c['name']];
    } catch (Throwable $e) { /* no email sent yet */ }
    $avg = fb_q($pdo, 'SELECT AVG(rating) FROM feedback WHERE rating IS NOT NULL AND created_at > ?', [time() - 30 * 86400])->fetchColumn();
    $new = (int) fb_q($pdo, "SELECT COUNT(*) FROM feedback WHERE status = 'new'")->fetchColumn();
    $items = array_map(function ($r) use ($names) { $o = fb_out($r, true); if (isset($o['mail'])) $o['mail']['name'] = $names[$o['mail']['campaign'] ?? 0] ?? null; return $o; }, $rows);
    return ['items' => $items, 'avg_rating_30d' => $avg !== null && $avg !== false ? round((float) $avg, 2) : null, 'new' => $new];
}
function fb_update(PDO $pdo, int $id, string $status, ?string $reply): bool
{
    fb_schema($pdo);
    if (!in_array($status, FB_STATUSES, true)) return false;
    $reply = $reply !== null ? g_sub(trim($reply), 0, FB_MAX_CHARS) : null;
    fb_q($pdo, 'UPDATE feedback SET status = ?, reply = ?, updated_at = ? WHERE id = ?', [$status, $reply !== '' ? $reply : null, time(), $id]);
    return true;
}
/** Serve a screenshot to its author or an administrator. */
function fb_serve_shot(PDO $pdo, int $id, string $uid, bool $isAdmin): void
{
    fb_schema($pdo);
    $r = fb_q($pdo, 'SELECT user_id, screenshot FROM feedback WHERE id = ?', [$id])->fetch(PDO::FETCH_ASSOC);
    if (!$r || !$r['screenshot'] || ($r['user_id'] !== $uid && !$isAdmin)) { http_response_code(404); exit; }
    $f = fb_dir() . '/' . basename((string) $r['screenshot']);
    if (!is_file($f)) { http_response_code(404); exit; }
    $ext = pathinfo($f, PATHINFO_EXTENSION);
    header('Content-Type: ' . (['png' => 'image/png', 'jpg' => 'image/jpeg', 'webp' => 'image/webp'][$ext] ?? 'application/octet-stream'));
    header('Cache-Control: private, max-age=3600'); header('X-Content-Type-Options: nosniff');
    readfile($f); exit;
}
/** Account deletion: remove the trader's feedback and screenshots, and referral rows. */
function growth_delete_user(PDO $pdo, string $uid): void
{
    try { fb_schema($pdo); foreach (fb_q($pdo, 'SELECT screenshot FROM feedback WHERE user_id = ? AND screenshot IS NOT NULL', [$uid]) as $r) @unlink(fb_dir() . '/' . basename((string) $r['screenshot']));
        fb_q($pdo, 'DELETE FROM feedback WHERE user_id = ?', [$uid]); } catch (Throwable $e) {}
    try { ref_schema($pdo); fb_q($pdo, 'DELETE FROM ref_users WHERE uid = ?', [$uid]); fb_q($pdo, 'DELETE FROM referral_clicks WHERE referrer_id = ?', [$uid]);
        fb_q($pdo, "UPDATE referrals SET status = 'rejected' WHERE referee_id = ? AND status IN ('pending','review')", [$uid]); } catch (Throwable $e) {}
    if (function_exists('cr_delete_user')) { try { cr_delete_user($pdo, $uid); } catch (Throwable $e) {} }   // creators (growth/creators.php)
}
