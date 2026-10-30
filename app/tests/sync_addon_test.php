<?php
declare(strict_types=1);
/**
 * Sweep — the add-ons (NinjaTrader 8, Quantower) and the server speak the same language (no C# compiler here):
 *   php tests/sync_addon_test.php
 * NinjaTrader 8: the import zip is up to date with sync/addon/SweepSync.cs. Both: the add-on sends the fields, header, key
 * and name (« client ») the server reads, it never calls an order function, and it sends to app.makeitsweep.com.
 * Quantower: a panel (Plugin) whose page (HTML/layout.html) is built in; its zip holds the compiled add-on only, once built.
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
ok(preg_match('/\bPassword\b/', $cs) === 0, 'it never reads a password');
// (1.1.0, 30 Oct.) the balance of each account, for Sweep's balance to follow the platform: the cash value only, no other account item
ok(preg_match_all('/AccountItem\.(\w+)/', $cs, $m) === 1 && $m[1] === ['CashValue'] && strpos($cs, '\\"cash\\":') !== false, 'it sends the balance of each account (its cash value), nothing else of the account');
ok(str_contains($cs, 'J("Sweep NT8 " + Version)') && str_contains($store, "'Sweep NT8' => 'ninjatrader'"), 'it names itself « Sweep NT8 … », the name the server ties to NinjaTrader 8');

// Quantower: the same language, from a panel
$q = (string) file_get_contents($app . '/sync/addon/quantower/SweepSync.cs');
$qp = (string) file_get_contents($app . '/sync/addon/quantower/SweepSync.csproj');
$qh = (string) file_get_contents($app . '/sync/addon/quantower/HTML/layout.html');
ok(str_contains($q, 'class SweepSyncPanel : Plugin') && str_contains($q, 'TemplateName = "layout.html"') && str_contains($qp, '<EmbeddedResource Include="HTML\layout.html" LogicalName="SweepSync.HTML.layout.html" />'), 'Quantower: a panel (Plugin, not a Strategy) whose page is built into the add-on');
ok(substr_count($qp, '<Private>false</Private>') === 2 && str_contains($qp, '$(QuantowerBin)\TradingPlatform.BusinessLayer.dll') && str_contains($qp, '$(QuantowerBin)\TradingPlatform.PresentationLayer.Plugins.dll'), 'Quantower: its two libraries are referenced, never shipped with the add-on');
foreach (['id', 'account', 'contract', 'side', 'qty', 'price', 'ts', 'fee', 'point_value'] as $k) ok(str_contains($q, '\"' . $k . '\":'), "Quantower: execution field « $k » sent");
foreach (['name', 'connection', 'provider', 'currency'] as $k) ok(str_contains($q, '\"' . $k . '\":'), "Quantower: account field « $k » sent");
foreach (['client', 'accounts', 'fills'] as $k) ok(str_contains($q, '\"' . $k . '\":'), "Quantower: request part « $k » sent");
ok(str_contains($q, '? "buy" : "sell"') && str_contains($q, 'TryAddWithoutValidation("X-Sweep-Key", Key)') && str_contains($q, '^swk_[0-9a-f]{40}$'), 'Quantower: sides buy / sell, the key in X-Sweep-Key, the same key format');
ok(str_contains($q, 'J("Sweep Quantower " + Version)') && str_contains($store, "'Sweep Quantower' => 'quantower'"), 'Quantower: it names itself « Sweep Quantower … », the name the server ties to Quantower (a NinjaTrader key is refused)');
ok(preg_match('/MaxPerPush = (\d+)/', $q, $m) === 1 && (int) $m[1] <= (int) $m2[1] && str_contains($q, '"https://app.makeitsweep.com/api/sync/push"'), 'Quantower: never more executions per request than the server takes, sent to app.makeitsweep.com');
ok(preg_match('/\b(PlaceOrder|CancelOrder|ModifyOrder|ClosePosition|SendCustomRequest)\b|\.(Close|Cancel)\s*\(/', $q) === 0, 'Quantower: read-only, no PlaceOrder, CancelOrder, ModifyOrder or Close');
ok(preg_match('/\bPassword\b/', $q) === 0, 'Quantower: it never reads a password');
ok(substr_count($q, '.Balance') === 1 && strpos($q, '\\"cash\\":') !== false, 'Quantower: it sends the balance of each account (1.1.0)');
ok(preg_match_all('/public static readonly string\[\] (En|Fr|Es) = \{(.*)\};/', $q, $tx) === 3 && count(array_unique(array_map(fn($x) => preg_match_all('/"(?:[^"\\\\]|\\\\.)*"/', $x), $tx[2]))) === 1, 'Quantower: the panel\'s texts in English, French and Spanish, as many in each');
foreach (['intro', 'label', 'key', 'save', 'status'] as $id) ok(str_contains($qh, 'id="' . $id . '"') && (in_array($id, ['key', 'save'], true) ? str_contains($q, '"' . $id . '"') : true), "Quantower: the panel's page has « $id »");
ok(str_contains($qh, 'paint: function (intro, label, save, status)') && str_contains($q, '"sweep.paint("'), 'Quantower: the add-on writes the page through sweep.paint');
$qz = $app . '/sync/addon/SweepSync-Quantower.zip';
if (is_file($qz)) {
    $names = []; if (class_exists('ZipArchive')) { $z = new ZipArchive(); if ($z->open($qz) === true) { for ($i = 0; $i < $z->numFiles; $i++) $names[] = $z->getNameIndex($i); $z->close(); } }
    else $names = array_filter(array_map('trim', explode("\n", (string) shell_exec('unzip -Z1 ' . escapeshellarg($qz) . ' 2>/dev/null'))));
    ok(array_values($names) === ['SweepSync/SweepSync.dll'], 'Quantower: the zip holds the compiled add-on only (SweepSync/SweepSync.dll)');
} else echo "--   Quantower: no zip yet (built at step 3 with tools/addon-quantower.py)\n";

echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
