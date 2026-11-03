#!/usr/local/bin/php -q
<?php
declare(strict_types=1);
/**
 * Sweep — what comes back to bounces@makeitsweep.com (cPanel › Forwarders › « Pipe to a Program »: mail/bounce.php,
 * from the home folder, with this file executable): bounce reports, spam complaints (feedback loops) and the mail apps'
 * « Unsubscribe » by email. Reads the message on stdin, records it, never answers: any output would bounce back.
 *   php mail/bounce.php < message.eml
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
ob_start();
try {
    require __DIR__ . '/boot.php';
    $raw = (string) stream_get_contents(STDIN, 2 * 1024 * 1024);
    if ($r = ml_parse_return($raw)) ml_apply_return($pdo, $r);
} catch (Throwable $e) { error_log('[Sweep bounce] ' . $e->getMessage()); }
ob_end_clean();
exit(0);
