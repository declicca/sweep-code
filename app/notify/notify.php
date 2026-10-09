<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Notification center + event system (Feature 0).
 *
 * Sweep sends no product email, so this is the one channel to talk to traders inside the app.
 *
 *   Events::on('trade.created', function (array $p) { ... });   // register a listener (notify/listeners.php)
 *   Events::fire('trade.created', ['uid' => ..., 'id' => ..., 'doc' => [...], 'prev' => null]);
 *   Notify::send($uid, 'payout_ready', ['account' => 'Apex 50K'], ['dedupe_key' => 'payout_ready:acc1:2026-10']);
 *
 * Rules:
 *  - A listener that throws is logged and skipped: it never breaks the trader's original action.
 *  - Notify::send never throws either; it returns the new id, or null when skipped
 *    (category turned off, duplicate dedupe_key, daily limit reached, or not allowed by the plan).
 *  - Celebrations bypass the daily limit, never the dedupe.
 *  - Text is never stored: only i18n keys + params. The app translates them (EN / FR / ES).
 *  - Times are stored as UTC epoch seconds.
 */

final class Events
{
    /** @var array<string, callable[]> */
    private static array $listeners = [];

    public static function on(string $name, callable $listener): void
    {
        self::$listeners[$name][] = $listener;
    }

    /** Runs every listener for $name. Never throws. */
    public static function fire(string $name, array $payload = []): void
    {
        foreach (self::$listeners[$name] ?? [] as $listener) {
            try {
                $listener($payload, $name);
            } catch (Throwable $e) {
                error_log('[Sweep events] ' . $name . ': ' . $e->getMessage() . ' @ ' . basename($e->getFile()) . ':' . $e->getLine());
            }
        }
    }
}

final class Notify
{
    public const CATEGORIES = ['product_updates', 'achievements', 'prop_alerts', 'streaks', 'system'];
    public const PRIORITIES = ['normal', 'celebration'];

    /** @var array<string, array> type => [category, title_key, body_key, icon, priority, action_url] */
    private static array $types = [];

    /** Declare a notification type once (notify/listeners.php). */
    public static function register(string $type, array $def): void
    {
        self::$types[$type] = $def + ['category' => 'system', 'priority' => 'normal', 'icon' => 'bell',
            'title_key' => $type . '.title', 'body_key' => $type . '.body', 'action_url' => null];
    }

    /** Settings from config.php → 'notifications' (all optional). */
    public static function cfg(): array
    {
        global $cfg;
        $c = is_array($cfg['notifications'] ?? null) ? $cfg['notifications'] : [];
        return $c + ['daily_limit' => 5, 'list_limit' => 60];
    }

    public static function pdo(): PDO { return db(); }

    private static function q(string $sql, array $a = []): PDOStatement
    {
        $st = self::pdo()->prepare($sql);
        $st->execute($a);
        return $st;
    }

    /** Creates the two tables when missing (same pattern as feedback and billing). */
    public static function schema(): void
    {
        static $done = false;
        if ($done) return;
        $done = true;
        $pdo = self::pdo();
        if ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql') {
            $pdo->exec('CREATE TABLE IF NOT EXISTS notifications (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(120) NOT NULL, type VARCHAR(48) NOT NULL, category VARCHAR(24) NOT NULL,
                title_key VARCHAR(96) NOT NULL, body_key VARCHAR(96) NULL, params TEXT NULL, icon VARCHAR(24) NULL, action_url VARCHAR(255) NULL,
                priority VARCHAR(12) NOT NULL DEFAULT \'normal\', dedupe_key VARCHAR(160) NULL, read_at INT NULL, shown_as_modal_at INT NULL,
                created_at INT NOT NULL, expires_at INT NULL,
                INDEX notif_unread (user_id, read_at, created_at), INDEX notif_list (user_id, created_at), UNIQUE KEY notif_dedupe (user_id, dedupe_key)
            ) DEFAULT CHARSET=utf8mb4');
            $pdo->exec('CREATE TABLE IF NOT EXISTS notification_prefs (
                user_id VARCHAR(120) NOT NULL, category VARCHAR(24) NOT NULL, enabled TINYINT NOT NULL DEFAULT 1, PRIMARY KEY (user_id, category)
            ) DEFAULT CHARSET=utf8mb4');
            return;
        }
        $pdo->exec('CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, type TEXT NOT NULL, category TEXT NOT NULL,
            title_key TEXT NOT NULL, body_key TEXT NULL, params TEXT NULL, icon TEXT NULL, action_url TEXT NULL,
            priority TEXT NOT NULL DEFAULT \'normal\', dedupe_key TEXT NULL, read_at INTEGER NULL, shown_as_modal_at INTEGER NULL,
            created_at INTEGER NOT NULL, expires_at INTEGER NULL)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS notif_unread ON notifications (user_id, read_at, created_at)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS notif_list ON notifications (user_id, created_at)');
        $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS notif_dedupe ON notifications (user_id, dedupe_key)');   // NULL keys never collide
        $pdo->exec('CREATE TABLE IF NOT EXISTS notification_prefs (
            user_id TEXT NOT NULL, category TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, PRIMARY KEY (user_id, category))');
    }

    /** Entitlement check. The notification center is on every plan; the key only exists so it can be changed in billing-config.php. */
    public static function allowed(string $uid): bool
    {
        try {
            if (function_exists('billing_on') && billing_on() && function_exists('sb_can')) return sb_can(self::pdo(), $uid, 'notifications');
        } catch (Throwable $e) {
            error_log('[Sweep notify] entitlement: ' . $e->getMessage());
        }
        return true;
    }

    /** @return array<string, bool> every category, on by default */
    public static function prefs(string $uid): array
    {
        self::schema();
        $out = array_fill_keys(self::CATEGORIES, true);
        foreach (self::q('SELECT category, enabled FROM notification_prefs WHERE user_id = ?', [$uid]) as $r) {
            if (isset($out[$r['category']])) $out[$r['category']] = (int) $r['enabled'] === 1;
        }
        return $out;
    }

    public static function setPref(string $uid, string $category, bool $enabled): bool
    {
        if (!in_array($category, self::CATEGORIES, true)) return false;
        self::schema();
        if (self::q('UPDATE notification_prefs SET enabled = ? WHERE user_id = ? AND category = ?', [$enabled ? 1 : 0, $uid, $category])->rowCount() === 0
            && !self::q('SELECT 1 FROM notification_prefs WHERE user_id = ? AND category = ?', [$uid, $category])->fetchColumn()) {
            self::q('INSERT INTO notification_prefs (user_id, category, enabled) VALUES (?, ?, ?)', [$uid, $category, $enabled ? 1 : 0]);
        }
        return true;
    }

    /**
     * Send one notification.
     * $opts: dedupe_key, action_url, priority (normal|celebration), icon, category, expires_at (epoch) or expires_in (seconds),
     *        title_key, body_key (override the type's keys).
     * Returns the new id, or null when skipped. Never throws.
     */
    public static function send(string $uid, string $type, array $params = [], array $opts = []): ?int
    {
        try {
            self::schema();
            $def = self::$types[$type] ?? ['category' => 'system', 'priority' => 'normal', 'icon' => 'bell',
                'title_key' => $type . '.title', 'body_key' => $type . '.body', 'action_url' => null];
            $category = (string) ($opts['category'] ?? $def['category']);
            if (!in_array($category, self::CATEGORIES, true)) $category = 'system';
            $priority = (string) ($opts['priority'] ?? $def['priority']);
            if (!in_array($priority, self::PRIORITIES, true)) $priority = 'normal';
            $dedupe = isset($opts['dedupe_key']) ? substr((string) $opts['dedupe_key'], 0, 160) : null;

            if (!self::allowed($uid)) return null;
            if (!(self::prefs($uid)[$category] ?? true)) return null;
            if ($dedupe !== null && self::q('SELECT 1 FROM notifications WHERE user_id = ? AND dedupe_key = ?', [$uid, $dedupe])->fetchColumn()) return null;
            if ($priority === 'normal') {
                $limit = (int) self::cfg()['daily_limit'];
                $sent = (int) self::q("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND priority = 'normal' AND created_at > ?", [$uid, time() - 86400])->fetchColumn();
                if ($limit > 0 && $sent >= $limit) { error_log('[Sweep notify] daily limit reached for ' . $uid . ' (' . $type . ')'); return null; }
            }
            $json = $params ? json_encode($params, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : null;
            if ($json !== null && strlen($json) > 4096) $json = null;   // params are placeholders, never documents
            $expires = isset($opts['expires_at']) ? (int) $opts['expires_at'] : (isset($opts['expires_in']) ? time() + (int) $opts['expires_in'] : null);
            $url = self::safeUrl($opts['action_url'] ?? $def['action_url']);

            self::q('INSERT INTO notifications (user_id, type, category, title_key, body_key, params, icon, action_url, priority, dedupe_key, created_at, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [
                $uid, substr($type, 0, 48), $category,
                (string) ($opts['title_key'] ?? $def['title_key']), $opts['body_key'] ?? $def['body_key'],
                $json, (string) ($opts['icon'] ?? $def['icon']), $url, $priority, $dedupe, time(), $expires,
            ]);
            return (int) self::pdo()->lastInsertId();
        } catch (Throwable $e) {
            // A unique-key race on dedupe_key lands here too: that is a normal skip.
            if (stripos($e->getMessage(), 'UNIQUE') === false && stripos($e->getMessage(), 'Duplicate') === false) {
                error_log('[Sweep notify] send ' . $type . ': ' . $e->getMessage());
            }
            return null;
        }
    }

    /** In-app links only: a hash route (#payouts) or a path on this site. */
    private static function safeUrl($u): ?string
    {
        $u = trim((string) ($u ?? ''));
        if ($u === '') return null;
        if (preg_match('~^#[A-Za-z0-9_./:%-]{0,200}$~', $u) || preg_match('~^/(?!/)[A-Za-z0-9_./?=&%#:-]{0,200}$~', $u)) return $u;
        return null;
    }

    private static function out(array $r): array
    {
        return [
            'id' => (int) $r['id'], 'type' => $r['type'], 'category' => $r['category'],
            'title_key' => $r['title_key'], 'body_key' => $r['body_key'],
            'params' => $r['params'] ? (json_decode((string) $r['params'], true) ?: new stdClass()) : new stdClass(),
            'icon' => $r['icon'] ?: 'bell', 'action_url' => $r['action_url'], 'priority' => $r['priority'],
            'read' => $r['read_at'] !== null, 'created_at' => gmdate('Y-m-d\TH:i:s\Z', (int) $r['created_at']),
        ];
    }

    /** Everything the bell needs in one call: recent items, unread count, and the next celebration to show as a modal. */
    public static function inbox(string $uid): array
    {
        self::schema();
        $now = time();
        $live = '(expires_at IS NULL OR expires_at > ?)';
        $limit = max(10, min(200, (int) self::cfg()['list_limit']));
        $items = self::q("SELECT * FROM notifications WHERE user_id = ? AND $live ORDER BY created_at DESC, id DESC LIMIT $limit", [$uid, $now])->fetchAll(PDO::FETCH_ASSOC);
        $unread = (int) self::q("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read_at IS NULL AND $live", [$uid, $now])->fetchColumn();
        $modal = self::q("SELECT * FROM notifications WHERE user_id = ? AND priority = 'celebration' AND shown_as_modal_at IS NULL AND read_at IS NULL AND $live
                          ORDER BY created_at ASC, id ASC LIMIT 1", [$uid, $now])->fetch(PDO::FETCH_ASSOC);
        return ['items' => array_map([self::class, 'out'], $items), 'unread' => $unread, 'modal' => $modal ? self::out($modal) : null];
    }

    public static function markRead(string $uid, int $id): void
    {
        self::schema();
        self::q('UPDATE notifications SET read_at = ? WHERE id = ? AND user_id = ? AND read_at IS NULL', [time(), $id, $uid]);
    }

    public static function markAllRead(string $uid): int
    {
        self::schema();
        return self::q('UPDATE notifications SET read_at = ? WHERE user_id = ? AND read_at IS NULL', [time(), $uid])->rowCount();
    }

    public static function markShown(string $uid, int $id): void
    {
        self::schema();
        self::q('UPDATE notifications SET shown_as_modal_at = ? WHERE id = ? AND user_id = ? AND shown_as_modal_at IS NULL', [time(), $id, $uid]);
    }

    /** Account deletion only (the trader asked for everything to go). */
    public static function deleteUser(string $uid): void
    {
        self::schema();
        self::q('DELETE FROM notifications WHERE user_id = ?', [$uid]);
        self::q('DELETE FROM notification_prefs WHERE user_id = ?', [$uid]);
    }
}

/** Fire an event from api.php. Safe even if this module failed to load. */
function nt_fire(string $name, array $payload): void
{
    try {
        if (class_exists('Events', false)) Events::fire($name, $payload);
    } catch (Throwable $e) {
        error_log('[Sweep events] fire ' . $name . ': ' . $e->getMessage());
    }
}

/**
 * Event for a saved or deleted document (api/docs/...). Sample data never fires events.
 * $prev is the stored document before the change (null when new), $doc the new one (null on delete).
 */
function nt_doc_event(string $uid, string $col, string $id, ?array $doc, ?array $prev): void
{
    if (!empty(($doc ?? $prev ?? [])['demo'])) return;
    $base = ['uid' => $uid, 'id' => $id, 'doc' => $doc, 'prev' => $prev];
    $created = $prev === null && $doc !== null;
    $deleted = $doc === null;
    switch ($col) {
        case 'trades':
            nt_fire($deleted ? 'trade.deleted' : ($created ? 'trade.created' : 'trade.updated'), $base);
            break;
        case 'accounts':
            nt_fire($deleted ? 'account.deleted' : ($created ? 'account.created' : 'account.updated'), $base);
            break;
        case 'journals':
            nt_fire($deleted ? 'journal.deleted' : 'journal.saved', $base);
            break;
        case 'payouts':
            if ($deleted) { nt_fire('payout.deleted', $base); break; }
            nt_fire($created ? 'payout.recorded' : 'payout.updated', $base);
            // Marked paid (on creation or later): the moment money actually arrives.
            if (($doc['status'] ?? '') === 'paid' && ($prev['status'] ?? '') !== 'paid') nt_fire('payout.paid', $base);
            break;
    }
}

/** Routes under api/notifications. Called only for signed-in traders. */
function nt_route(string $route, string $method, string $uid, bool $isAdmin): void
{
    if ($route === 'api/notifications' && $method === 'GET') {
        // First visit: a short note explaining where updates will appear.
        // (no welcome note: the bell shows a badge only for something real)
        json_out(200, Notify::inbox($uid));
    }
    if ($route === 'api/notifications/read-all' && $method === 'POST') {
        Notify::markAllRead($uid);
        json_out(200, ['ok' => true, 'unread' => 0]);
    }
    if (preg_match('#^api/notifications/(\d{1,12})/(read|shown)$#', $route, $m) && $method === 'POST') {
        $m[2] === 'read' ? Notify::markRead($uid, (int) $m[1]) : Notify::markShown($uid, (int) $m[1]);
        json_out(200, ['ok' => true]);
    }
    if ($route === 'api/notifications/prefs' && $method === 'GET') {
        json_out(200, ['prefs' => Notify::prefs($uid)]);
    }
    if ($route === 'api/notifications/prefs' && $method === 'POST') {
        $b = body_json(2048);
        if (!Notify::setPref($uid, (string) ($b['category'] ?? ''), !empty($b['enabled']))) json_out(400, ['error' => 'Unknown category.']);
        json_out(200, ['prefs' => Notify::prefs($uid)]);
    }
    // Administrator only: send yourself a test, to check the bell, the sheet and the celebration modal.
    if ($route === 'api/notifications/test' && $method === 'POST') {
        if (!$isAdmin) json_out(403, ['error' => 'Administrators only.']);
        $b = body_json(1024);
        $celebration = ($b['kind'] ?? '') === 'celebration';
        $id = Notify::send($uid, $celebration ? 'test_celebration' : 'test_normal', [], ['dedupe_key' => 'test:' . bin2hex(random_bytes(6))]);
        json_out(200, ['ok' => $id !== null, 'id' => $id]);
    }
    json_out(404, ['error' => 'not found']);
}

require_once __DIR__ . '/listeners.php';
