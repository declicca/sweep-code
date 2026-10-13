<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — automatic sync, HTTP routes (loaded by api.php only for api/sync…).
 *   POST   api/sync/push                    an add-on (NinjaTrader 8, Quantower): accounts and executions, key in the X-Sweep-Key header (no session)
 *   GET    api/sync                         connections and accounts found (the Connections screen)
 *   POST   api/sync/key {platform}          a new personal key, shown once (the previous one stops working)
 *   DELETE api/sync/key?platform=…          stop the sync (the trades already written stay)
 *   GET    api/sync/accounts/ID/preview?account_id=…   what linking would do: trades to add, typed by hand to complete
 *   POST   api/sync/accounts/ID {action: link, account_id} | {action: ignore} | {action: unlink}
 *   GET    api/sync/addon?platform=…        a platform's add-on (zip; NinjaTrader 8 by default), for a signed-in trader
 */
require_once __DIR__ . '/sync-store.php';

function sync_push_route(string $method): void
{
    if ($method !== 'POST') json_out(405, ['error' => 'method not allowed']);
    $ip = 'syncip:' . hash('sha256', client_ip());
    throttle([$ip], 20, 900);   // wrong keys from one address
    $conn = sync_auth(db(), trim((string) ($_SERVER['HTTP_X_SWEEP_KEY'] ?? '')));
    if (!$conn) { record_attempt([$ip]); json_out(401, ['error' => 'Unknown or revoked key. Create a new one in Sweep: Settings, Connections.', 'code' => 'key']); }
    $p = body_json(2 * 1048576);
    // a key pasted in the other platform's add-on: refused, else its accounts and trades would show under the wrong platform
    $cp = sync_client_platform((string) ($p['client'] ?? ''));
    if ($cp !== null && $cp !== $conn['platform']) {
        $nm = ['ninjatrader' => 'NinjaTrader 8', 'quantower' => 'Quantower'];
        json_out(401, ['error' => 'This key is for ' . $nm[$conn['platform']] . '. Create a ' . $nm[$cp] . ' key in Sweep: Settings, Connections.', 'code' => 'platform']);
    }
    if (count((array) ($p['fills'] ?? [])) > SYNC_MAX_FILLS) json_out(413, ['error' => 'Too many executions in one request.', 'max' => SYNC_MAX_FILLS]);
    try { $r = sync_receive(db(), $conn, $p); }
    catch (Throwable $e) { error_log('[Sweep sync] push: ' . $e->getMessage()); json_out(503, ['error' => 'Not saved. Send again.', 'code' => 'retry']); }
    json_out(isset($r['error']) ? 413 : 200, $r);
}

function sync_route(string $route, string $method, string $uid): void
{
    $pdo = db(); sync_schema($pdo);
    if ($route === 'api/sync' && $method === 'GET') json_out(200, sync_status($pdo, $uid));
    if ($route === 'api/sync/addon' && $method === 'GET') {
        $f = SYNC_ADDONS[(string) ($_GET['platform'] ?? 'ninjatrader')] ?? null;
        if ($f === null) json_out(400, ['error' => 'Unknown platform.']);
        if (!is_file($f)) json_out(404, ['error' => 'Not available yet.']);
        header('Content-Type: application/zip'); header('Content-Disposition: attachment; filename="' . basename($f) . '"'); header('Content-Length: ' . filesize($f)); header('Cache-Control: no-store');
        readfile($f); exit;
    }
    if ($route === 'api/sync/key' && in_array($method, ['POST', 'DELETE'], true)) {
        $platform = $method === 'POST' ? (string) (body_json(4096)['platform'] ?? '') : (string) ($_GET['platform'] ?? '');
        if (!in_array($platform, SYNC_PLATFORMS, true)) json_out(400, ['error' => 'Unknown platform.']);
        if ($method === 'DELETE') json_out(200, ['ok' => true, 'revoked' => sync_revoke($pdo, $uid, $platform)]);
        throttle(['synckey:' . $uid], 10, 3600); record_attempt(['synckey:' . $uid]);
        json_out(200, sync_new_key($pdo, $uid, $platform));
    }
    if (preg_match('#^api/sync/accounts/(sa_[0-9a-f]{16})(/preview)?$#', $route, $m)) {
        if (!empty($m[2]) && $method === 'GET') {
            $r = sync_preview($pdo, $uid, $m[1], (string) ($_GET['account_id'] ?? ''));
            json_out(isset($r['error']) ? ($r['error'] === 'not_found' ? 404 : 400) : 200, $r);
        }
        if (empty($m[2]) && $method === 'POST') {
            $b = body_json(4096); $act = (string) ($b['action'] ?? '');
            if ($act === 'link') $r = sync_link($pdo, $uid, $m[1], (string) ($b['account_id'] ?? ''));
            elseif ($act === 'ignore' || $act === 'unlink') $r = sync_set_state($pdo, $uid, $m[1], $act === 'ignore' ? 'ignored' : 'new');
            else json_out(400, ['error' => 'Unknown action.']);
            // a link is saved even when the plan or the record limit holds the trades back (they are written as soon as it allows)
            json_out(empty($r['ok']) ? ($r['error'] === 'not_found' ? 404 : 409) : 200, $r);
        }
    }
    json_out(404, ['error' => 'not found']);
}
