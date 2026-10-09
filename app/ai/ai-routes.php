<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep AI — routes.
 * Called from the app's main PHP router AFTER the user is signed in:
 *
 *     if (strpos($route, 'api/ai/') === 0) {
 *         require_once __DIR__ . '/ai/ai-routes.php';
 *         sweep_ai_route($route, $method, (string) $UID, db());
 *     }
 *
 * Every route answers JSON. Errors: {"error": "...", "code": "daily_limit|budget|..."}.
 */

require_once __DIR__ . '/ai-core.php';
require_once __DIR__ . '/ai-stats.php';
require_once __DIR__ . '/ai-features.php';

function sai_out(int $code, array $data): void
{
    if (function_exists('json_out')) { json_out($code, $data); }
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function sai_body(int $maxBytes): array
{
    $raw = file_get_contents('php://input');
    if ($raw === false || strlen($raw) > $maxBytes) throw new SaiError('image_too_big', 413);
    $d = json_decode($raw === '' ? '{}' : $raw, true);
    if (!is_array($d)) throw new SaiError('bad_input', 400);
    return $d;
}

function sweep_ai_route(string $route, string $method, string $uid, PDO $pdo): void
{
    try {
        sai_init_db($pdo);
        $cfg = sai_config();
        $imgMax = (int) ($cfg['max_image_mb'] * 1048576 * 1.4) + 65536;
        $post = $method === 'POST';
        $b = $post ? sai_body($imgMax) : [];
        $lang = sai_lang($b['lang'] ?? $_GET['lang'] ?? 'en');
        $image = fn() => !empty($b['image']) ? sai_image($b['image'], $b['mime'] ?? '') : null;
        $withUsage = fn(array $r) => $r + ['usage' => sai_usage($pdo, $uid)];

        switch ($route) {
            case 'api/ai/status':
                sai_out(200, ['enabled' => (bool) $cfg['enabled'], 'usage' => sai_usage($pdo, $uid)]);

            case 'api/ai/health':
                if (!$post) break;
                $r = sai_call($pdo, $uid, 'health', 'Return JSON {"ok":true,"greeting":string} where greeting is a 5-word hello to a futures trader.',
                    ['system' => sai_system($lang), 'max_tokens' => 60, 'cache' => false]);
                sai_out(200, $withUsage(['ok' => true, 'model' => $cfg['model'], 'answer' => $r['data']]));

            case 'api/ai/parse-trades':
                if (!$post) break;
                sai_out(200, $withUsage(sai_parse_trades($pdo, $uid, (string) ($b['text'] ?? ''), $lang)));

            case 'api/ai/import':
                if (!$post) break;
                $img = $image();
                if (!$img) throw new SaiError('image', 400);
                if (($b['mode'] ?? '') === 'shot') {   // several trades from one screenshot (one call, one credit)
                    $r = sai_shot_read($pdo, $uid, $img, $lang);
                    sai_out(200, $withUsage(sai_shot_trades($pdo, $uid, (array) ($r['data'] ?? []), $b) + ['cached' => $r['cached'] ?? false]));
                }
                $mode = ($b['mode'] ?? 'trades') === 'receipt' ? 'receipt' : 'trades';
                sai_out(200, $withUsage($mode === 'receipt' ? sai_scan_receipt($pdo, $uid, $img, $lang) : sai_import_trades_image($pdo, $uid, $img, $lang)));

            case 'api/ai/shot-build':   // the same rows again, for another account or time zone: no AI, no credit
                if (!$post) break;
                sai_out(200, sai_shot_trades($pdo, $uid, ['source_type' => (string) ($b['source_type'] ?? 'unknown'), 'timezone_shown' => (string) ($b['timezone_shown'] ?? 'unknown'), 'account_label' => $b['account_label'] ?? null, 'rows' => array_slice((array) ($b['rows'] ?? []), 0, 300), 'columns' => array_slice((array) ($b['columns'] ?? []), 0, 40), 'table' => array_slice((array) ($b['table'] ?? []), 0, 300), 'pnl_colors' => array_slice((array) ($b['pnl_colors'] ?? []), 0, 300), 'date_shown' => $b['date_shown'] ?? null, 'symbol_shown' => $b['symbol_shown'] ?? null], $b));

            case 'api/ai/ask':
                if (!$post) break;
                sai_out(200, $withUsage(sai_ask($pdo, $uid, (string) ($b['question'] ?? ''), $lang)));

            case 'api/ai/weekly-review':
                if (!$post) break;
                sai_out(200, $withUsage(sai_weekly_review($pdo, $uid, isset($b['week_start']) ? (string) $b['week_start'] : null, $lang)));

            case 'api/ai/day-debrief':
                if (!$post) break;
                sai_out(200, $withUsage(sai_day_debrief($pdo, $uid, (string) ($b['date'] ?? sai_today_ny()), $lang)));

            case 'api/ai/trade-feedback':
                if (!$post) break;
                sai_out(200, $withUsage(sai_trade_feedback($pdo, $uid, (string) ($b['trade_id'] ?? ''), $image(), $lang)));

            case 'api/ai/suggest-tags':
                if (!$post) break;
                sai_out(200, $withUsage(sai_suggest_tags($pdo, $uid, (string) ($b['trade_id'] ?? ''), $image(), $lang)));
        }
        sai_out(404, ['error' => 'Not found', 'code' => 'not_found']);
    } catch (SaiError $e) {
        if ($e->extra) sai_out($e->http, $e->extra + ['code' => $e->sai, 'usage' => sai_usage($pdo, $uid)]);
        sai_out($e->http, ['error' => $e->getMessage(), 'code' => $e->sai]);
    } catch (Throwable $e) {
        error_log('[Sweep AI] ' . $e->getMessage() . ' @ ' . $e->getFile() . ':' . $e->getLine());
        sai_out(500, ['error' => 'AI error', 'code' => 'server']);
    }
}
