<?php
declare(strict_types=1);
/**
 * Sweep — the NinjaTrader 8 add-on and the server speak the same language (no C# compiler here: NinjaTrader compiles it):
 *   php tests/sync_addon_test.php
 * The import zip is up to date with sync/addon/SweepSync.cs, the add-on sends the fields, header and key the server reads,
 * it never calls an order function, and it sends to app.makeitsweep.com.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$n = 0; $f = 0;
function ok($c, $what) { global $n, $f; $n++; if (!$c) $f++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
$cs = (string) file_get_contents($app . '/sync/addon/SweepSync.cs');
$store = (string) file_get_contents($app . '/sync/sync-store.php') . file_get_contents($app . '/sync/sync-engine.php');
$routes = (string) file_get_contents($app . '/sync/sync-routes.php');
$zip = $app . '/sync/addon/SweepSync.zip';

// the import file: Info.xml + AddOns/SweepSync.cs, the same code as the source (Windows line endings)
$entries = [];
if (class_exists('ZipArchive')) { $z = new ZipArchive(); if ($z->open($zip) === true) { for ($i = 0; $i < $z->numFiles; $i++) { $nm = $z->getNameIndex($i); $entries[$nm] = $z->getFromName($nm); } $z->close(); } }
else foreach (['Info.xml', 'AddOns/SweepSync.cs'] as $nm) { $out = shell_exec('unzip -p ' . escapeshellarg($zip) . ' ' . escapeshellarg($nm) . ' 2>/dev/null'); if (is_string($out) && $out !== '') $entries[$nm] = $out; }
ok(array_keys($entries) === ['Info.xml', 'AddOns/SweepSync.cs'] || (isset($entries['Info.xml'], $entries['AddOns/SweepSync.cs']) && count($entries) === 2), 'the zip holds Info.xml and AddOns/SweepSync.cs');
ok(str_contains($entries['Info.xml'] ?? '', '<Version>8.1.0.0</Version>'), 'Info.xml: made for NinjaTrader 8.1');
ok(($entries['AddOns/SweepSync.cs'] ?? '') === str_replace("\n", "\r\n", str_replace("\r\n", "\n", $cs)), 'the zip is up to date with sync/addon/SweepSync.cs (else: python3 -I tools/addon-zip.py)');

// what the add-on sends = what the server reads
foreach (['id', 'account', 'contract', 'side', 'qty', 'price', 'ts', 'fee', 'point_value'] as $k)
    ok(str_contains($cs, '\"' . $k . '\":') && preg_match("/\\['" . $k . "'\\]/", $store) === 1, "execution field « $k »: sent by the add-on, read by the server");
foreach (['name', 'connection', 'provider', 'currency'] as $k)
    ok(str_contains($cs, '\"' . $k . '\":') && preg_match("/\\['" . $k . "'\\]/", $store) === 1, "account field « $k »: sent and read");
foreach (['client', 'accounts', 'fills'] as $k) ok(str_contains($cs, '\"' . $k . '\":') && str_contains($store, "\$p['$k']"), "request part « $k »: sent and read");
ok(str_contains($cs, '"buy"') || str_contains($cs, '? "buy" : "sell"'), 'sides « buy » / « sell », as the engine reads them');
ok(str_contains($cs, 'req.Headers["X-Sweep-Key"]') && str_contains($routes, "HTTP_X_SWEEP_KEY"), 'the key travels in X-Sweep-Key on both sides');
ok(str_contains($cs, '^swk_[0-9a-f]{40}$') && str_contains($store, '^swk_[0-9a-f]{40}$'), 'same key format on both sides (swk_ + 40 hex)');
ok(preg_match('/MaxPerPush = (\d+)/', $cs, $m) === 1 && preg_match('/SYNC_MAX_FILLS = (\d+)/', $store, $m2) === 1 && (int) $m[1] <= (int) $m2[1], 'the add-on never sends more executions per request than the server takes');
ok(str_contains($cs, '"https://app.makeitsweep.com/api/sync/push"'), 'it sends to app.makeitsweep.com');

// read-only: no order function of NinjaTrader is ever called
ok(preg_match('/\.(Submit|CreateOrder|Cancel|CancelAllOrders|Change|Flatten)\s*\(/', $cs) === 0, 'read-only: no Submit, CreateOrder, Cancel, Change or Flatten');
ok(preg_match('/\bPassword\b|AccountItem\./', $cs) === 0, 'it never reads a password or an account balance');

echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
