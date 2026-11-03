<?php
declare(strict_types=1);
/**
 * Sweep — sends the queued emails (campaigns of Admin › Emails), every minute:
 *   * * * * *  /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/mail/send-cron.php >/dev/null 2>&1
 * Starts the campaigns that are due, then sends within the hourly cap (mail_per_hour in config.php, doubled each week
 * from the first email). One run at a time (a lock file). Admin › Health shows its last run.
 *   php mail/send-cron.php --dry-run   what is due and the cap, nothing sent
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/boot.php';
require_once $root . '/ops/cron-lib.php';
$dry = in_array('--dry-run', $argv, true);
ml_schema($pdo);
if ($dry) { echo json_encode(['cap' => ml_cap($pdo), 'left' => ml_left($pdo), 'due' => ml_q($pdo, "SELECT id, name FROM mail_campaigns WHERE status = 'scheduled' AND scheduled_at <= ?", [time()])->fetchAll()]) . "\n"; exit; }
$lock = @fopen($DATA . '/mail-send.lock', 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) exit;   // the previous run is still sending
sweep_cron_start($pdo, 'mail');
$smtp = new MlSmtp((array) ($cfg['smtp'] ?? []));
try {
    $r = ml_run($pdo, fn($to, $s, $t, $h, $hd, $tok) => $smtp->send($to, $s, $t, $h, $hd, $tok));
    $smtp->close();
    sweep_cron_note($r['sent'] . ' sent' . ($r['failed'] ? ', ' . $r['failed'] . ' failed' : '') . ' · ' . $r['left'] . ' queued · ' . $r['hour'] . ' of ' . $r['cap'] . ' this hour');
} catch (Throwable $e) {
    $smtp->close(); sweep_cron_fail($e->getMessage()); fwrite(STDERR, '[Sweep mail] ' . $e->getMessage() . "\n"); exit(1);
}
