<?php
declare(strict_types=1);
/**
 * Sweep — sends the queued emails (Admin › Emails), every minute:
 *   * * * * *  /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/mail/send-cron.php >/dev/null 2>&1
 * The timed automatic emails first (mail/mail-auto.php: the evening of day one; from 7:30 New York, once a day, the absences
 * and the Pro trial), then the campaigns that are due, then sends within the hourly cap (mail_per_hour in config.php,
 * doubled each week from the first email; the emails about the account are not counted). One run at a time (a lock file).
 * Admin › Health shows its last run.
 *   php mail/send-cron.php --dry-run   what is due and the cap, nothing sent
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/boot.php';
require_once __DIR__ . '/mail-auto.php';
require_once $root . '/ops/cron-lib.php';
// (5 Nov., brief notifications) the phone notifications of the automatic messages (push/push-auto.php), sent before the emails
if (!empty($cfg['push_config']) && !defined('SWEEP_PUSH_CONFIG')) define('SWEEP_PUSH_CONFIG', (string) $cfg['push_config']);
require_once $root . '/notify/notify.php';
require_once $root . '/push/web-push.php';
require_once $root . '/push/push-auto.php';
$dry = in_array('--dry-run', $argv, true);
ml_schema($pdo);
if ($dry) { echo json_encode(['cap' => ml_cap($pdo), 'left' => ml_left($pdo), 'due' => ml_q($pdo, "SELECT id, name FROM mail_campaigns WHERE status = 'scheduled' AND scheduled_at <= ?", [time()])->fetchAll()]) . "\n"; exit; }
$lock = @fopen($DATA . '/mail-send.lock', 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) exit;   // the previous run is still sending
sweep_cron_start($pdo, 'mail');
$smtp = new MlSmtp((array) ($cfg['smtp'] ?? []));
try {
    $auto = ma_cron($pdo);
    $pa = pa_run();
    if ($pa['sent'] || $pa['skipped']) $auto .= ($auto !== '' ? ', ' : '') . $pa['sent'] . ' notifications' . ($pa['skipped'] ? ' (' . $pa['skipped'] . ' held back)' : '');
    $r = ml_run($pdo, fn($to, $s, $t, $h, $hd, $tok) => $smtp->send($to, $s, $t, $h, $hd, $tok));
    $smtp->close();
    sweep_cron_note(($auto !== '' ? $auto . ' · ' : '') . $r['sent'] . ' sent' . ($r['failed'] ? ', ' . $r['failed'] . ' failed' : '') . ' · ' . $r['left'] . ' queued · ' . $r['hour'] . ' of ' . $r['cap'] . ' this hour');
} catch (Throwable $e) {
    $smtp->close(); sweep_cron_fail($e->getMessage()); fwrite(STDERR, '[Sweep mail] ' . $e->getMessage() . "\n"); exit(1);
}
