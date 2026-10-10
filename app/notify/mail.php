<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Emails from hello@makeitsweep.com.
 * With config 'smtp' => ['host' => 'mail.makeitsweep.com', 'port' => 465, 'user' => 'hello@makeitsweep.com', 'pass' => '…']
 * the email is sent through the mailbox (SMTP over SSL, authenticated: best delivery, lands in « Sent »).
 * Without it, PHP mail() is used from the same address.
 * Shared by api.php and the cron jobs (game/cron.php: the « Your week » email). $headers: extra headers (List-Unsubscribe…).
 */
function sweep_mail(string $to, string $subject, string $text, string $html = '', array $headers = []): bool {
    global $cfg;
    $from = trim((string)($cfg['mail_from'] ?? '')) ?: 'hello@makeitsweep.com';
    $support = trim((string)($cfg['support_email'] ?? '')) ?: 'hello@makeitsweep.com';
    $sc = (array)($cfg['smtp'] ?? []);
    $bnd = 'sw' . bin2hex(random_bytes(8));
    $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $body = $html === '' ? $text
        : "--$bnd\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text))
        . "--$bnd\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) . "--$bnd--\r\n";
    $ctype = $html === '' ? "Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit" : "Content-Type: multipart/alternative; boundary=\"$bnd\"";
    $extra = ''; foreach ($headers as $k => $v) $extra .= preg_replace('/[^A-Za-z-]/', '', (string)$k) . ': ' . str_replace(["\r", "\n"], '', (string)$v) . "\r\n";
    $hdr = "From: Sweep <$from>\r\nReply-To: " . $support . "\r\n" . $extra . "MIME-Version: 1.0\r\n" . $ctype;
    if (!empty($sc['host']) && !empty($sc['user']) && !empty($sc['pass'])) {
        try {
            $port = (int)($sc['port'] ?? 465);
            $fp = @stream_socket_client(($port === 465 ? 'ssl://' : 'tcp://') . $sc['host'] . ':' . $port, $en, $es, 15);
            if (!$fp) throw new RuntimeException("connect $es");
            stream_set_timeout($fp, 15);
            $rd = function () use ($fp) { $o = ''; while (($l = fgets($fp, 515)) !== false) { $o .= $l; if (isset($l[3]) && $l[3] === ' ') break; } return $o; };
            $cmd = function (string $c, array $ok) use ($fp, $rd) { fwrite($fp, $c . "\r\n"); $r = $rd(); if (!in_array((int)substr($r, 0, 3), $ok, true)) throw new RuntimeException(trim($r)); return $r; };
            $rd();
            $cmd('EHLO makeitsweep.com', [250]);
            if ($port === 587) { $cmd('STARTTLS', [220]); stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT); $cmd('EHLO makeitsweep.com', [250]); }
            $cmd('AUTH LOGIN', [334]); $cmd(base64_encode($sc['user']), [334]); $cmd(base64_encode($sc['pass']), [235]);
            $cmd('MAIL FROM:<' . $from . '>', [250]); $cmd('RCPT TO:<' . $to . '>', [250, 251]); $cmd('DATA', [354]);
            $msg = "To: <$to>\r\nSubject: $subj\r\nDate: " . date('r') . "\r\nMessage-ID: <" . bin2hex(random_bytes(12)) . "@makeitsweep.com>\r\n" . $hdr . "\r\n\r\n" . $body;
            $msg = preg_replace('/^\./m', '..', str_replace(["\r\n", "\n"], ["\n", "\r\n"], $msg));
            $cmd($msg . "\r\n.", [250]); @fwrite($fp, "QUIT\r\n"); fclose($fp);
            return true;
        } catch (Throwable $e) { error_log('Sweep: SMTP failed (' . $e->getMessage() . '), falling back to mail()'); }
    }
    $ok = function_exists('mail') && @mail($to, $subj, $body, $hdr, '-f' . $from);
    if (!$ok) error_log('Sweep: email could not be sent to ' . $to);
    return $ok;
}
