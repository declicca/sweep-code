<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the campaign sender: ONE authenticated SMTP connection to the mailbox (config 'smtp', like sweep_mail()) for a
 * whole batch, RSET between emails. Returns true, « soft: … » (4xx, connection lost: retried later) or « hard: … »
 * (5xx on the address: never written to again). Envelope sender bounces@ (config 'mail_bounce'), so what comes back
 * reaches mail/bounce.php; if the server refuses it, the From address is used instead (bounces then land in that mailbox).
 * A dev copy (SWEEP_TEST_DB) never sends: each email goes to data/mail-sent.jsonl; an address starting with
 * « bounce-hard » or « bounce-soft » answers like a refusing server (tests).
 */
final class MlSmtp
{
    private $fp = null; private string $envelope; private int $n = 0;

    public function __construct(private array $cfg) { $this->envelope = ml_bounce_addr(); }

    public static function message(string $to, string $subject, string $text, string $html, array $headers, string $token): string
    {
        $from = ml_from(); $support = trim((string) (ml_cfg()['support_email'] ?? '')) ?: $from;
        $bnd = 'sw' . bin2hex(random_bytes(8));
        $extra = ''; foreach ($headers as $k => $v) $extra .= preg_replace('/[^A-Za-z-]/', '', (string) $k) . ': ' . str_replace(["\r", "\n"], '', (string) $v) . "\r\n";
        $body = $html === '' ? chunk_split(base64_encode($text))
            : "--$bnd\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text))
            . "--$bnd\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) . "--$bnd--\r\n";
        $ctype = $html === '' ? "Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64" : "Content-Type: multipart/alternative; boundary=\"$bnd\"";
        return "To: <$to>\r\nFrom: Sweep <$from>\r\nReply-To: $support\r\nSubject: =?UTF-8?B?" . base64_encode($subject) . "?=\r\nDate: " . date('r')
            . "\r\nMessage-ID: <$token.m@makeitsweep.com>\r\n" . $extra . "MIME-Version: 1.0\r\n" . $ctype . "\r\n\r\n" . $body;
    }

    public function send(string $to, string $subject, string $text, string $html, array $headers, string $token)
    {
        if (getenv('SWEEP_TEST_DB')) {
            if (strpos($to, 'bounce-hard') === 0) return 'hard: 550 5.1.1 user unknown (test)';
            if (strpos($to, 'bounce-soft') === 0) return 'soft: 451 4.3.0 try again later (test)';
            @file_put_contents(dirname((string) getenv('SWEEP_TEST_DB')) . '/mail-sent.jsonl', json_encode(['to' => $to, 'subject' => $subject, 'text' => $text, 'html' => $html, 'headers' => $headers, 'token' => $token, 'at' => time()], JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
            return true;
        }
        if (empty($this->cfg['host']) || empty($this->cfg['user']) || empty($this->cfg['pass'])) return 'soft: no mailbox (smtp) in config.php';
        $msg = self::message($to, $subject, $text, $html, $headers, $token);
        try {
            if (!$this->fp || $this->n >= 50) $this->open();   // a fresh connection every 50 emails
            else $this->cmd('RSET', [250]);
            $r = $this->cmd('MAIL FROM:<' . $this->envelope . '>', [250], false);
            if ((int) substr($r, 0, 3) >= 500 && $this->envelope !== ml_from()) {
                error_log('[Sweep mail] envelope ' . $this->envelope . ' refused (' . trim($r) . '), using ' . ml_from());
                $this->envelope = ml_from(); $this->cmd('RSET', [250]); $this->cmd('MAIL FROM:<' . $this->envelope . '>', [250]);
            } elseif ((int) substr($r, 0, 3) !== 250) throw new RuntimeException(trim($r));
            $r = $this->cmd('RCPT TO:<' . $to . '>', [250, 251], false);
            $code = (int) substr($r, 0, 3);
            if ($code >= 500) return 'hard: ' . trim($r);
            if ($code !== 250 && $code !== 251) return 'soft: ' . trim($r);
            $this->cmd('DATA', [354]);
            $this->cmd(preg_replace('/^\./m', '..', str_replace(["\r\n", "\n"], ["\n", "\r\n"], $msg)) . "\r\n.", [250]);
            $this->n++;
            return true;
        } catch (Throwable $e) {
            $this->close();
            return 'soft: ' . $e->getMessage();
        }
    }

    private function open(): void
    {
        $this->close();
        $port = (int) ($this->cfg['port'] ?? 465);
        $fp = @stream_socket_client(($port === 465 ? 'ssl://' : 'tcp://') . $this->cfg['host'] . ':' . $port, $en, $es, 15);
        if (!$fp) throw new RuntimeException("connect $es");
        stream_set_timeout($fp, 20); $this->fp = $fp; $this->n = 0;
        $this->read();
        $this->cmd('EHLO makeitsweep.com', [250]);
        if ($port === 587) { $this->cmd('STARTTLS', [220]); stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT); $this->cmd('EHLO makeitsweep.com', [250]); }
        $this->cmd('AUTH LOGIN', [334]); $this->cmd(base64_encode((string) $this->cfg['user']), [334]); $this->cmd(base64_encode((string) $this->cfg['pass']), [235]);
    }
    private function read(): string
    {
        $o = ''; while (($l = fgets($this->fp, 515)) !== false) { $o .= $l; if (isset($l[3]) && $l[3] === ' ') break; }
        if ($o === '') throw new RuntimeException('connection closed');
        return $o;
    }
    private function cmd(string $c, array $ok, bool $strict = true): string
    {
        fwrite($this->fp, $c . "\r\n"); $r = $this->read();
        if ($strict && !in_array((int) substr($r, 0, 3), $ok, true)) throw new RuntimeException(trim($r));
        return $r;
    }
    public function close(): void
    {
        if ($this->fp) { @fwrite($this->fp, "QUIT\r\n"); @fclose($this->fp); }
        $this->fp = null;
    }
}
