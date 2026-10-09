<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep AI — core.
 * The ONLY place that talks to the AI provider (Google Gemini).
 * Handles: config, quotas, global daily budget, throttling, result cache, cost log.
 * Works with both SQLite and MySQL (same PDO the app already uses).
 */

/* Fallbacks if the server's PHP has no mbstring extension (UTF-8 safe). */
if (!function_exists('mb_strlen')) {
    function mb_strlen(string $s): int { return (int) preg_match_all('/./us', $s); }
}
if (!function_exists('mb_substr')) {
    function mb_substr(string $s, int $start, ?int $len = null): string
    {
        preg_match_all('/./us', $s, $m);
        return implode('', array_slice($m[0], $start, $len));
    }
}
if (!function_exists('mb_strtolower')) {
    function mb_strtolower(string $s): string { return strtolower($s); }
}

final class SaiError extends RuntimeException
{
    public string $sai;
    public int $http;
    public array $extra = [];   // e.g. billing: feature, used, limit, reset_at, upgrade_to
    public function __construct(string $code, int $http = 400, string $detail = '')
    {
        parent::__construct($detail !== '' ? $detail : $code);
        $this->sai = $code;
        $this->http = $http;
    }
}

/* ---------------- config ---------------- */

function sai_defaults(): array
{
    return [
        'enabled'                   => true,
        'api_key'                   => '',
        'model'                     => 'gemini-3.1-flash-lite',
        'model_vision'              => '',   // reading screenshots with many trades: a stronger model if set (else « model »)
        'endpoint'                  => 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        'price_input_per_m'         => 0.25,
        'price_output_per_m'        => 1.50,
        'thinking_level'            => 'minimal',
        'user_daily_limit'          => 25,
        'global_daily_budget_usd'   => 2.00,
        'max_output_tokens'         => 900,
        'timeout_seconds'           => 40,
        'min_seconds_between_calls' => 2,
        'cache_days'                => 30,
        'max_image_mb'              => 6,
    ];
}

function sai_config(): array
{
    static $cfg = null;
    if ($cfg !== null) return $cfg;
    $candidates = [];
    if (defined('SWEEP_AI_CONFIG')) $candidates[] = (string) SWEEP_AI_CONFIG;
    $env = getenv('SWEEP_AI_CONFIG');
    if (is_string($env) && $env !== '') $candidates[] = $env;
    $candidates[] = dirname(__DIR__, 2) . '/sweep-private/ai-config.php';
    $candidates[] = dirname(__DIR__, 3) . '/sweep-private/ai-config.php';
    foreach ($candidates as $p) {
        if (@is_readable($p)) {
            $c = require $p;
            if (is_array($c)) {
                $cfg = $c + sai_defaults();
                $key = trim((string) $cfg['api_key']);
                if ($key === '' || stripos($key, 'PASTE_') === 0) $cfg['enabled'] = false;
                $cfg['_found'] = $p;
                return $cfg;
            }
        }
    }
    $cfg = ['enabled' => false, '_found' => null] + sai_defaults();
    return $cfg;
}

/* ---------------- time ---------------- */

function sai_now(): string { return gmdate('Y-m-d H:i:s'); }

function sai_ny(): DateTimeZone { static $z = null; return $z ??= new DateTimeZone('America/New_York'); }

function sai_today_ny(): string { return (new DateTime('now', sai_ny()))->format('Y-m-d'); }

/** Start of the current New York day, expressed in UTC (quotas reset at midnight New York time). */
function sai_day_start_utc(): string
{
    $d = new DateTime('today', sai_ny());
    $d->setTimezone(new DateTimeZone('UTC'));
    return $d->format('Y-m-d H:i:s');
}

/* ---------------- tables (auto-created) ---------------- */

function sai_init_db(PDO $pdo): void
{
    static $done = false;
    if ($done) return;
    $done = true;
    $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);
    if ($driver === 'mysql') {
        $sql = [
            'CREATE TABLE IF NOT EXISTS ai_log (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(64) NOT NULL, task VARCHAR(40) NOT NULL,
               input_tokens INT NOT NULL DEFAULT 0, output_tokens INT NOT NULL DEFAULT 0, cost_usd DOUBLE NOT NULL DEFAULT 0, created_at VARCHAR(20) NOT NULL,
               INDEX ai_log_user (user_id, created_at), INDEX ai_log_day (created_at)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS ai_cache (user_id VARCHAR(64) NOT NULL, k CHAR(40) NOT NULL, task VARCHAR(40) NOT NULL, v MEDIUMTEXT NOT NULL,
               created_at VARCHAR(20) NOT NULL, PRIMARY KEY (user_id, k)) DEFAULT CHARSET=utf8mb4',
        ];
    } else {
        $sql = [
            'CREATE TABLE IF NOT EXISTS ai_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, task TEXT NOT NULL,
               input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0, cost_usd REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL)',
            'CREATE INDEX IF NOT EXISTS ai_log_user ON ai_log(user_id, created_at)',
            'CREATE INDEX IF NOT EXISTS ai_log_day ON ai_log(created_at)',
            'CREATE TABLE IF NOT EXISTS ai_cache (user_id TEXT NOT NULL, k TEXT NOT NULL, task TEXT NOT NULL, v TEXT NOT NULL, created_at TEXT NOT NULL,
               PRIMARY KEY (user_id, k))',
        ];
    }
    foreach ($sql as $s) $pdo->exec($s);
}

function sai_q(PDO $pdo, string $sql, array $args = []): PDOStatement
{
    $st = $pdo->prepare($sql);
    $st->execute($args);
    return $st;
}

/* ---------------- quotas & budget ---------------- */

function sai_usage(PDO $pdo, string $uid): array
{
    sai_init_db($pdo);
    $cfg = sai_config();
    if (sai_billing()) {
        $used = sb_usage($pdo, $uid, 'ai_daily'); $limit = sb_limit($pdo, $uid, 'ai_daily');
        return ['used' => $used, 'limit' => $limit, 'remaining' => $limit === null ? null : max(0, (int) $limit - $used)];
    }
    $used = (int) sai_q($pdo, 'SELECT COUNT(*) FROM ai_log WHERE user_id = ? AND created_at >= ?', [$uid, sai_day_start_utc()])->fetchColumn();
    $limit = (int) $cfg['user_daily_limit'];
    return ['used' => $used, 'limit' => $limit, 'remaining' => max(0, $limit - $used)];
}

function sai_spent_today(PDO $pdo): float
{
    return (float) sai_q($pdo, 'SELECT COALESCE(SUM(cost_usd), 0) FROM ai_log WHERE created_at >= ?', [sai_day_start_utc()])->fetchColumn();
}

function sai_guard(PDO $pdo, string $uid): void
{
    $cfg = sai_config();
    if (!$cfg['enabled']) throw new SaiError('disabled', 503);
    if (!sai_billing()) {   // with billing, the plan's quotas apply instead (sai_call → sb_ai_consume)
        $u = sai_usage($pdo, $uid);
        if ($u['remaining'] <= 0) throw new SaiError('daily_limit', 429);
    }
    $last = sai_q($pdo, 'SELECT MAX(created_at) FROM ai_log WHERE user_id = ?', [$uid])->fetchColumn();
    if ($last && (time() - strtotime($last . ' UTC')) < (int) $cfg['min_seconds_between_calls']) throw new SaiError('throttle', 429);
    if (sai_spent_today($pdo) >= (float) $cfg['global_daily_budget_usd']) throw new SaiError('budget', 503);
}

/* ---------------- cache ---------------- */

function sai_cache_get(PDO $pdo, string $uid, string $key): ?array
{
    $cfg = sai_config();
    $min = gmdate('Y-m-d H:i:s', time() - 86400 * (int) $cfg['cache_days']);
    $v = sai_q($pdo, 'SELECT v FROM ai_cache WHERE user_id = ? AND k = ? AND created_at >= ?', [$uid, $key, $min])->fetchColumn();
    if (!is_string($v)) return null;
    $d = json_decode($v, true);
    return is_array($d) ? $d : null;
}

function sai_cache_put(PDO $pdo, string $uid, string $key, string $task, array $value): void
{
    $json = json_encode($value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    sai_q($pdo, 'DELETE FROM ai_cache WHERE user_id = ? AND k = ?', [$uid, $key]);
    sai_q($pdo, 'INSERT INTO ai_cache (user_id, k, task, v, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, $key, $task, $json, sai_now()]);
    // Light housekeeping: 1 request in 50 purges expired cache rows.
    if (random_int(1, 50) === 1) {
        $min = gmdate('Y-m-d H:i:s', time() - 86400 * (int) sai_config()['cache_days']);
        sai_q($pdo, 'DELETE FROM ai_cache WHERE created_at < ?', [$min]);
    }
}

/* ---------------- provider call ---------------- */

/**
 * Ask the AI. Always returns decoded JSON (every Sweep feature asks for JSON).
 *
 * $opts: system (string), image (['data' => base64, 'mime' => 'image/jpeg']), max_tokens (int), cache (bool, default true)
 * Returns ['data' => array, 'cached' => bool]
 */
function sai_call(PDO $pdo, string $uid, string $task, string $prompt, array $opts = []): array
{
    sai_init_db($pdo);
    $cfg = sai_config();
    if (!$cfg['enabled']) throw new SaiError('disabled', 503);
    if (!empty($opts['model'])) $cfg['model'] = (string) $opts['model'];   // a task can ask for a stronger model (screenshots: model_vision)

    $system = (string) ($opts['system'] ?? '');
    $image = $opts['image'] ?? null;
    $useCache = ($opts['cache'] ?? true) !== false;
    $key = sha1($task . "\n" . $cfg['model'] . "\n" . $system . "\n" . $prompt . "\n" . ($image ? sha1((string) $image['data']) : ''));

    if ($useCache && ($hit = sai_cache_get($pdo, $uid, $key)) !== null) {
        return ['data' => $hit, 'cached' => true];
    }

    sai_guard($pdo, $uid);
    $kind = sai_billing() ? sai_kind($task) : null;
    if ($kind !== null) {
        if ($task === 'weekly_review' && !sb_can($pdo, $uid, 'weekly_report')) {
            $x = new SaiError('upgrade_required', 402); $x->extra = ['error' => 'upgrade_required', 'feature' => 'weekly_report', 'trigger' => 'weekly_report', 'upgrade_to' => sb_plan_for('weekly_report')]; throw $x;
        }
        $q = sb_ai_consume($pdo, $uid, $kind);
        if (!$q['ok']) { $x = new SaiError((string) $q['code'], 402); $x->extra = $q + ['error' => 'upgrade_required']; throw $x; }
    }
    try {
        return sai_call_run($pdo, $uid, $task, $prompt, $opts, $cfg, $system, $image, $useCache, $key);
    } catch (SaiError $e) {
        if ($kind !== null && in_array($e->sai, ['network', 'provider', 'provider_busy', 'bad_output'], true)) sb_ai_refund($pdo, $uid, $kind);
        throw $e;
    }
}

/** Which plan quota an AI task uses (null = not counted). */
function sai_kind(string $task): ?string
{
    if ($task === 'health' || str_starts_with($task, 'game_')) return null;   // short game texts (boss intro…) never use the trader's AI allowance
    if ($task === 'trade_feedback') return 'review';
    if (in_array($task, ['trade_import', 'receipt_scan'], true)) return 'import';
    return 'chat';
}
function sai_billing(): bool { return function_exists('billing_on') && billing_on(); }

function sai_call_run(PDO $pdo, string $uid, string $task, string $prompt, array $opts, array $cfg, string $system, $image, bool $useCache, string $key): array
{
    $parts = [['text' => $prompt]];
    if ($image) $parts[] = ['inlineData' => ['mimeType' => $image['mime'], 'data' => $image['data']]];
    $body = [
        'contents' => [['role' => 'user', 'parts' => $parts]],
        'generationConfig' => [
            'maxOutputTokens'  => (int) ($opts['max_tokens'] ?? $cfg['max_output_tokens']),
            'temperature'      => (float) ($opts['temperature'] ?? 0.3),
            'responseMimeType' => 'application/json',
        ],
    ];
    if ($system !== '') $body['systemInstruction'] = ['parts' => [['text' => $system]]];
    if (!empty($cfg['thinking_level'])) $body['generationConfig']['thinkingConfig'] = ['thinkingLevel' => (string) $cfg['thinking_level']];

    [$status, $raw] = sai_http($cfg, $body);
    // Some models don't accept a thinking setting: retry once without it.
    if ($status === 400 && isset($body['generationConfig']['thinkingConfig']) && stripos((string) $raw, 'thinking') !== false) {
        unset($body['generationConfig']['thinkingConfig']);
        [$status, $raw] = sai_http($cfg, $body);
    }
    if ($status === 0) throw new SaiError('network', 502);
    $res = json_decode((string) $raw, true);
    if ($status !== 200 || !is_array($res)) {
        error_log('[Sweep AI] HTTP ' . $status . ' ' . substr((string) $raw, 0, 800));
        if ($status === 429) throw new SaiError('provider_busy', 503);
        throw new SaiError('provider', 502, 'HTTP ' . $status);
    }

    $text = '';
    foreach ($res['candidates'][0]['content']['parts'] ?? [] as $p) {
        if (isset($p['text']) && empty($p['thought'])) $text .= $p['text'];
    }

    // Log the cost even if the answer is unusable: Google still billed it.
    $u = $res['usageMetadata'] ?? [];
    $in = (int) ($u['promptTokenCount'] ?? 0);
    $out = (int) ($u['candidatesTokenCount'] ?? 0) + (int) ($u['thoughtsTokenCount'] ?? 0);
    $cost = $in / 1e6 * (float) $cfg['price_input_per_m'] + $out / 1e6 * (float) $cfg['price_output_per_m'];
    sai_q($pdo, 'INSERT INTO ai_log (user_id, task, input_tokens, output_tokens, cost_usd, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [$uid, substr($task, 0, 40), $in, $out, round($cost, 6), sai_now()]);

    $data = sai_json($text);
    if ($data === null) {
        error_log('[Sweep AI] Unparseable answer for ' . $task . ': ' . substr($text, 0, 500));
        throw new SaiError('bad_output', 502);
    }
    if ($useCache) sai_cache_put($pdo, $uid, $key, $task, $data);
    return ['data' => $data, 'cached' => false];
}

function sai_http(array $cfg, array $body): array
{
    $url = str_replace('{model}', rawurlencode((string) $cfg['model']), (string) $cfg['endpoint']);
    if (!function_exists('curl_init')) {
        // Fallback for hosts without the cURL extension: PHP streams
        $ctx = stream_context_create(['http' => [
            'method' => 'POST', 'ignore_errors' => true, 'timeout' => (int) $cfg['timeout_seconds'],
            'header' => "Content-Type: application/json\r\nx-goog-api-key: " . $cfg['api_key'] . "\r\n",
            'content' => json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        ]]);
        $raw = @file_get_contents($url, false, $ctx);
        $status = 0;
        foreach (($http_response_header ?? []) as $h) if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $m)) $status = (int) $m[1];
        if ($raw === false) { error_log('[Sweep AI] HTTP stream failed'); return [0, false]; }
        return [$status, $raw];
    }
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 8,
        CURLOPT_TIMEOUT        => (int) $cfg['timeout_seconds'],
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'x-goog-api-key: ' . $cfg['api_key']],
        CURLOPT_POSTFIELDS     => json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    ]);
    $raw = curl_exec($ch);
    $status = $raw === false ? 0 : (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    if ($raw === false) error_log('[Sweep AI] cURL: ' . curl_error($ch));
    curl_close($ch);
    return [$status, $raw];
}

/** Decode a JSON answer, tolerating ```json fences or text around it. */
function sai_json(string $text): ?array
{
    $t = trim($text);
    $t = preg_replace('/^```(?:json)?\s*|\s*```$/i', '', $t) ?? $t;
    $d = json_decode($t, true);
    if (is_array($d)) return $d;
    $a = strpos($t, '{');
    $b = strrpos($t, '}');
    if ($a !== false && $b !== false && $b > $a) {
        $d = json_decode(substr($t, $a, $b - $a + 1), true);
        if (is_array($d)) return $d;
    }
    return null;
}

/* ---------------- small helpers ---------------- */

function sai_lang($v): string
{
    $v = strtolower(substr((string) $v, 0, 2));
    return in_array($v, ['en', 'fr', 'es'], true) ? $v : 'en';
}

function sai_lang_rule(string $lang): string
{
    return [
        'en' => 'Write every human-readable string in English.',
        'fr' => 'Write every human-readable string in French (Québec-friendly, neutral), addressing the trader informally with "tu".',
        'es' => 'Write every human-readable string in Spanish, addressing the trader informally with "tú".',
    ][$lang];
}

function sai_str($v, int $max = 200): ?string
{
    if (!is_string($v) && !is_numeric($v)) return null;
    $s = trim((string) $v);
    if ($s === '') return null;
    return mb_substr($s, 0, $max);
}

function sai_num($v): ?float
{
    if (is_int($v) || is_float($v)) return is_finite((float) $v) ? (float) $v : null;
    if (is_string($v)) {
        $s = str_replace([',', '$', ' '], '', $v);
        return is_numeric($s) ? (float) $s : null;
    }
    return null;
}

function sai_id(string $prefix = 'ai'): string
{
    return $prefix . '-' . base_convert((string) time(), 10, 36) . '-' . bin2hex(random_bytes(4));
}

/** Validate a base64 image from the browser. Returns ['data' => base64, 'mime' => ...]. */
function sai_image($b64, $mime): array
{
    if (!is_string($b64) || $b64 === '') throw new SaiError('image', 400);
    $b64 = preg_replace('#^data:[^;]+;base64,#', '', $b64) ?? '';
    $max = (int) sai_config()['max_image_mb'] * 1048576;
    if (strlen($b64) > $max * 1.4) throw new SaiError('image_too_big', 413);
    $raw = base64_decode($b64, true);
    if ($raw === false || $raw === '') throw new SaiError('image', 400);
    $info = @getimagesizefromstring($raw);
    $type = $info['mime'] ?? '';
    if (!in_array($type, ['image/png', 'image/jpeg', 'image/webp'], true)) throw new SaiError('image', 415);
    return ['data' => base64_encode($raw), 'mime' => $type];
}
