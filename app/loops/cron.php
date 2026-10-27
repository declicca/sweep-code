<?php
declare(strict_types=1);
/**
 * Sweep — the daily Loops events (loops/loops.php). cPanel → Cron Jobs, every hour at :30 (ops/CRON.md):
 *   30 * * * *  /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/loops/cron.php >/dev/null 2>&1
 * It works once a New York day, from 7:30 (America/New_York: summer time follows by itself), so the follow-ups leave before
 * the session, while the trader gets ready. The other hourly runs do nothing, except catch up a day the server missed and
 * retry what Loops refused.
 *   inactive3d, inactive7d, inactive14d, inactive30d   3, 7, 14 and 30 days without coming back to the app, once per absence
 *   proTrialDaysLeft (daysLeft 30, 10, 3)  before the end of the 60 days of Pro, once per step
 *   proTrialEnded                          the 60 days just ended and the trader did not pay, once
 * Never for the Discord crew (Elite for life) nor a trader who pays. A step comes due at a moment (last visit + 7 days, end
 * of the trial − 10 days…); a run sends the steps that came due since the previous successful run, so a missed day is
 * caught up, never twice (email_events_log); several steps of one kind due together: only the latest.
 * The first run (any hour) prepares Loops: it creates the contact properties there and marks what existing traders already
 * did; the app sends its own events from then on.
 *
 *   php loops/cron.php                                             the hourly run
 *   php loops/cron.php --dry-run                                   what the daily run would send now: nothing sent or recorded
 *   php loops/cron.php --now="2026-12-01 07:30" --user=u_abc       test: a New York time, one trader (not recorded as the daily run)
 *   php loops/cron.php --all-events --user=u_abc                   each of the 16 events once to this test trader, example
 *                                                                  properties, nothing recorded: Loops then offers them all as triggers
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
require_once $root . '/ops/cron-lib.php';
require_once __DIR__ . '/loops.php';

$o = getopt('', ['dry-run', 'now:', 'user:', 'all-events']);
$dry = isset($o['dry-run']); $user = isset($o['user']) ? (string) $o['user'] : null; $test = isset($o['now']) || $user !== null;
if (isset($o['all-events']) && $user === null) { fwrite(STDERR, "--all-events needs --user=<id> (a test trader).\n"); exit(2); }
if (isset($o['now']) && $user === null && !$dry) { fwrite(STDERR, "--now needs --user=<id> (or --dry-run): a pretended date never goes to every trader.\n"); exit(2); }
if (!$test && !$dry) sweep_cron_start($pdo, 'emails');

if (!loops_on()) { sweep_cron_note('off: no Loops key (sweep-private/loops-config.php)'); echo "Loops is off: no key in sweep-private/loops-config.php.\n"; exit(0); }
$NY = new DateTimeZone('America/New_York');
try { $now = isset($o['now']) ? (new DateTimeImmutable((string) $o['now'], $NY))->getTimestamp() : time(); }
catch (Throwable $e) { fwrite(STDERR, "--now: not a date (« 2026-12-01 07:30 », New York time).\n"); exit(2); }
if ($test) $GLOBALS['SB_NOW'] = $now;

// first run: the contact properties in Loops, what existing traders already did; the app sends its events from then on
if (!loops_ready()) {
    if ($dry) echo "First run not done yet: it will create the contact properties in Loops and mark what existing traders already did.\n";
    else {
        $r = loops_init();
        if ($r['error'] !== null) { sweep_cron_fail('first run: ' . $r['error']); fwrite(STDERR, "Loops not ready: {$r['error']}\n"); exit(1); }
        echo 'Loops ready: ' . ($r['created'] ? 'properties created (' . implode(', ', $r['created']) . '), ' : 'properties already there, ') . "{$r['marked']} past step(s) marked as done.\n";
    }
}

if (isset($o['all-events'])) {   // every event once to a test trader (example properties), so each one can be picked as a trigger in Loops
    if (!loops_q('SELECT 1 FROM users WHERE id = ?', [$user])->fetchColumn()) { fwrite(STDERR, "No trader $user.\n"); exit(2); }
    $bad = 0;
    foreach (['signedUp' => fn(array $c) => ['language' => $c['language'], 'plan' => $c['plan']], 'profileCompleted' => [], 'firstAccountAdded' => ['propFirm' => 'Topstep'], 'firstPlanSaved' => [],
              'firstTradeLogged' => [], 'tradesMilestone' => ['milestone' => 10], 'firstPayoutLogged' => [], 'subscriptionStarted' => ['plan' => 'pro', 'interval' => 'month'],
              'subscriptionCanceled' => ['plan' => 'pro'], 'paymentFailed' => ['plan' => 'pro'], 'referralRewarded' => [], 'inactive3d' => [], 'inactive7d' => [], 'inactive14d' => [], 'inactive30d' => [],
              'proTrialDaysLeft' => ['daysLeft' => 30], 'proTrialEnded' => []] as $name => $props) {
        $sent = loops_send($user, $name, $props); $bad += $sent ? 0 : 1;
        echo ($sent ? 'sent: ' : 'NOT sent: ') . $name . "\n"; usleep(120000);
    }
    exit($bad ? 1 : 0);
}
$local = (new DateTimeImmutable('@' . $now))->setTimezone($NY);
$day = $local->format('Y-m-d');
if (!$test && !$dry) {
    if ($local->format('H:i') < '07:30') { sweep_cron_note(loops_setting('loops_daily_note') ?? 'waits for 7:30 New York time'); echo "$day " . $local->format('H:i') . " in New York: the daily events leave from 7:30.\n"; exit(0); }
    if (loops_setting('loops_daily_day') === $day) { sweep_cron_note(loops_setting('loops_daily_note') ?? "$day: done"); echo "Already done today ($day).\n"; exit(0); }
}
$at = $test && $user !== null ? 'loops_test_at:' . $user : 'loops_daily_at';   // a test run keeps its own previous run
$prev = (int) (loops_setting($at) ?? 0);
$from = $prev > 0 && $prev < $now ? $prev : $now - 86400;   // what came due since the previous successful run (a whole day the first time)

if ($user !== null && !loops_q('SELECT 1 FROM users WHERE id = ?', [$user])->fetchColumn()) { fwrite(STDERR, "No trader $user.\n"); exit(2); }
$ids = $user !== null ? [$user] : loops_q('SELECT id FROM users WHERE disabled = 0 ORDER BY created_at')->fetchAll(PDO::FETCH_COLUMN);
['sent' => $sent, 'failed' => $failed, 'error' => $err] = loops_daily_run($ids, $from, $now, $dry, function (string $s): void { echo $s . "\n"; });

$sum = $sent ? array_sum($sent) . ' event(s): ' . implode(', ', array_map(fn($k, $v) => "$v $k", array_keys($sent), $sent)) : 'nothing due';
if ($dry) { echo "Dry run ($day " . $local->format('H:i') . " New York): nothing sent.\n"; exit(0); }
if ($failed) {
    sweep_cron_fail("$failed event(s) not sent (tried again at the next run): $err");
    fwrite(STDERR, "$sum; $failed not sent: $err\n"); exit(1);
}
loops_save_setting($at, (string) $now);
if ($test) { echo "Test ($day " . $local->format('H:i') . " New York, $user): $sum.\n"; exit(0); }
$note = "$day: $sum";
loops_save_setting('loops_daily_day', $day); loops_save_setting('loops_daily_note', $note);
sweep_cron_note($note);
echo "$note\n";
