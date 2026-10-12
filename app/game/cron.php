<?php
declare(strict_types=1);
/**
 * Sweep — gamification cron (optional but recommended). Locks the days whose grace period is over,
 * evaluates streaks, uses freezes and refills them on Mondays. The same work also runs when a trader opens the app,
 * so a missed cron run never changes anyone's result.
 *
 * cPanel → Cron Jobs → every 15 minutes (reminders need it; locking/streaks only need hourly):
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/game/cron.php >/dev/null 2>&1
 *
 *   php game/cron.php            lock + streaks for every player, reminders, the « Your week » email (Friday 17:30 ET)
 *   php game/cron.php backfill   (re)run the history backfill for every player (idempotent)
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }

$root = dirname(__DIR__);
$cfg = require $root . '/config.php';
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
$c = $cfg['db'] ?? [];
$opts = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC];
if (($c['driver'] ?? 'sqlite') === 'mysql') {
    $pdo = new PDO('mysql:host=' . $c['host'] . ';dbname=' . $c['name'] . ';charset=utf8mb4', (string) $c['user'], (string) $c['password'], $opts);
} else {
    $pdo = new PDO('sqlite:' . $DATA . '/journal.db', null, null, $opts);
    $pdo->exec('PRAGMA busy_timeout = 5000');
}
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool {
    static $on = null; if ($on !== null) return $on;
    global $cfg, $root;
    if (!empty($cfg['billing_config']) && !defined('SWEEP_BILLING_CONFIG')) define('SWEEP_BILLING_CONFIG', (string) $cfg['billing_config']);
    if (!is_file($root . '/billing/billing-core.php')) return $on = false;
    require_once $root . '/billing/billing-core.php';
    try { sb_config(); return $on = true; } catch (Throwable $e) { return $on = false; }
}

foreach (['/notify/notify.php', '/notify/listeners.php', '/notify/mail.php'] as $f) if (is_file($root . $f)) require_once $root . $f;   // reminders go through the notification center
require_once __DIR__ . '/game.php';
if (is_file($root . '/money/money.php')) require_once $root . '/money/money.php';
GameEngine::setPdo($pdo);
GameEngine::schema();

$mode = $argv[1] ?? 'lock';
require_once $root . '/ops/cron-lib.php';   // Admin › Health: last run, duration, success or error (brief 02 step 0)
if ($mode === 'lock') sweep_cron_start($pdo, 'game');
try { GameDiscord::cron(); } catch (Throwable $e) { fwrite(STDERR, '[Sweep discord] ' . $e->getMessage() . "\n"); }
try { GameSocial::ensureWeek(); } catch (Throwable $e) { fwrite(STDERR, '[Sweep league] ' . $e->getMessage() . "\n"); }   // Monday: close last week, form this week
$users = $pdo->query('SELECT user_id FROM user_game_profile')->fetchAll(PDO::FETCH_COLUMN);
$n = 0;
foreach ($users as $uid) {
    try {
        if ($mode === 'backfill') { GameEngine::backfill((string) $uid); GameV2::backfillMap((string) $uid); } else { GameEngine::catchUp((string) $uid); GameV2::ensureMissions((string) $uid); GameWrapped::ensure((string) $uid); GameWrappedYear::ensure((string) $uid); GameWow::check((string) $uid); GameNotifyService::run((string) $uid); }
        if ($mode !== 'backfill') { try { GameWeeklyMail::run((string) $uid); } catch (Throwable $e) { fwrite(STDERR, "[Sweep weekly email] $uid: " . $e->getMessage() . "\n"); } }   // Friday 17:30 ET: « Your week », if not opened in the app
        try { if (class_exists('SweepMoneyServer')) SweepMoneyServer::monthly($pdo, (string) $uid); } catch (Throwable $e) { fwrite(STDERR, "[Sweep money] $uid: " . $e->getMessage() . "\n"); }   // the 1st: « The reality of the month »
        GameEngine::forget((string) $uid);
        $n++;
    } catch (Throwable $e) {
        fwrite(STDERR, "[Sweep game] $uid: " . $e->getMessage() . "\n");
    }
}
// an update shipped new prop firm rules: check them once against the official pages (until then, the shipped seed is used)
if ($mode === 'lock' && is_file($root . '/presets/check.php')) {
    try { require_once $root . '/presets/check.php'; require_once $root . '/ai/ai-core.php'; $r = pr_recheck_if_seed_changed($pdo); if ($r !== null) echo date('c') . ' Sweep presets: new shipped rules, ' . count($r) . " firm(s) checked\n"; }
    catch (Throwable $e) { fwrite(STDERR, '[Sweep presets recheck] ' . $e->getMessage() . "\n"); }
}
sweep_cron_note("$n player(s)");
// a task red for more than one cycle → one email to the support address (this one included, by the app itself if it stops)
if ($mode === 'lock') { try { sweep_cron_watch($pdo, fn(string $s, string $t) => function_exists('sweep_mail') && sweep_mail(trim((string) ($cfg['support_email'] ?? '')) ?: 'hello@makeitsweep.com', $s, $t)); } catch (Throwable $e) { fwrite(STDERR, '[Sweep cron watch] ' . $e->getMessage() . "\n"); } }
echo date('c') . " Sweep game $mode: $n player(s)\n";
