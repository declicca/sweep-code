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

// (1.3.0) the key of the download: empty in the source (each download writes its own), used at start when none is saved
ok(substr_count($cs, 'public const string EmbeddedKey = "";') === 1 && str_contains($store, 'public const string EmbeddedKey = "";'), 'EmbeddedKey: empty in the source, the exact line the server fills in');
ok(str_contains($cs, 'Regex.IsMatch(EmbeddedKey, "^swk_[0-9a-f]{40}$") && (string.IsNullOrEmpty(Key) || Seed != EmbeddedKey)'), 'the add-on takes the key of its download when none is saved, or when the download is newer');

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
// (1.2.0, 2 Nov.) never a silent failure: every one is written in NinjaScript Output with the HTTP code, Sweep's message and the
// URL, the key's last 4 characters only; a hello as soon as a key is saved; « Test connection » sends one now
ok(str_contains($cs, 'Log((code == 0 ? "cannot reach " : "HTTP " + code + " from ") + Url + " (key ..." + Hint + "): " + message)') && preg_match_all('/Log\([^;]*\bKey\b/', $cs) === 0, 'every failure is written in NinjaScript Output (code, message, URL), never the whole key');
ok(preg_match('/SetKey\(string key\)[\s\S]*?nextHello = DateTime\.MinValue;[\s\S]*?\n\t\t}/', $cs) === 1 && str_contains($cs, 'public static void TestNow()') && str_contains($cs, 'SweepSyncEngine.TestNow()'), 'a hello right after a key is saved, and a « Test connection » button');
foreach (['En', 'Fr', 'Es'] as $lg) ok(preg_match('/string\[\] ' . $lg . ' = \{(.*)\};/', $cs, $m) === 1 && substr_count($m[1], '", "') === 15, "window texts in $lg: the same 16 lines");
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
    // until it is built again with Plan Sync (tools/addon-quantower.py): the panel alone, unzipped into « plug-ins »; once built: the
    // panel and the indicator in Quantower's folders, unzipped into « Scripts » — the « Connect Quantower » sheet must say so
    $ux = (string) file_get_contents($app . '/src/ux.js');
    $plan = ['Indicators/SweepPlan/SweepPlan.dll', 'plug-ins/SweepSync/SweepSync.dll'];
    $sorted = array_values($names); sort($sorted);
    ok(array_values($names) === ['SweepSync/SweepSync.dll'] ? str_contains($ux, 'Settings › Scripts › plug-ins') : ($sorted === $plan && !str_contains($ux, 'Settings › Scripts › plug-ins')),
        'Quantower: the zip holds the compiled add-on only (' . implode(', ', $names) . '), and the « Connect Quantower » sheet says where to unzip it');
} else echo "--   Quantower: no zip yet (built at step 3 with tools/addon-quantower.py)\n";

// Plan Sync (step 3): the Sweep Plan indicator, its shared logic, the same key and server, never an order, no market data out
$pi = (string) file_get_contents($app . '/sync/addon/quantower-plan/SweepPlan.cs');
$pp = (string) file_get_contents($app . '/sync/addon/quantower-plan/SweepPlan.csproj');
$pc = (string) file_get_contents($app . '/sync/addon/plan/PlanCore.cs');
$ps = (string) file_get_contents($app . '/sync/plan-sync.php');
$tool = (string) file_get_contents($app . '/tools/addon-quantower.py');
ok(str_contains($pi, 'class SweepPlanIndicator : Indicator') && str_contains($pp, '<Compile Include="..\\plan\\PlanCore.cs"') && str_contains($pp, '<Private>false</Private>') && str_contains($pp, 'ExcludeAssets="runtime"'), 'Plan Sync: an indicator, with the shared logic (plan/PlanCore.cs), Quantower\'s library referenced, never shipped');
ok(str_contains($tool, "'Indicators/SweepPlan/SweepPlan.dll'") && str_contains($tool, "'plug-ins/SweepSync/SweepSync.dll'"), 'Plan Sync: the add-on tool builds the panel and the indicator into one zip');
ok(preg_match('/\b(PlaceOrder|CancelOrder|ModifyOrder|ClosePosition|SendCustomRequest|Core\.Instance\.(Orders|Positions))\b|\.(Close|Cancel)\s*\(/', $pi . $pc) === 0, 'Plan Sync: never an order call (no PlaceOrder, CancelOrder, ModifyOrder, Close)');
ok(str_contains($pi, '"/api/plan-sync/today?instrument="') && str_contains($pi, '"/api/plan-sync/events"') && str_contains($pi, 'TryAddWithoutValidation("X-Sweep-Key", k)') && str_contains($pi, '"If-None-Match"'), 'Plan Sync: the plan read with the sync key and its ETag, the events sent to their route');
ok(str_contains($pi, '"Sweep Quantower Plan " + Version') && str_contains($store, "'Sweep Quantower' => 'quantower'") && str_contains($pi, '"https://app.makeitsweep.com"') && str_contains($pi, '"config.txt"'), 'Plan Sync: it names itself « Sweep Quantower … » (a Quantower key only), app.makeitsweep.com, the panel\'s key (config.txt)');
preg_match_all("/'([a-z_]+)'/", (string) (preg_match('/PS_EVENT_TYPES = \[([^\]]*)\]/', $ps, $m) ? $m[1] : ''), $types);
ok(str_contains($pc, '"zone_approached"') && str_contains($pc, '"zone_entered"') && str_contains($pc, '"rule_triggered"') && !array_diff(['zone_approached', 'zone_entered', 'rule_triggered'], $types[1] ?? []), 'Plan Sync: the event types are the server\'s');
preg_match_all('/"(approach|enter|close_above|close_below|sweep|time)"/', (string) (preg_match('/Triggers = \{([^}]*)\}/', $pc, $m2) ? $m2[1] : ''), $tr);
ok(($tr[1] ?? []) === ['approach', 'enter', 'close_above', 'close_below', 'sweep', 'time'] && str_contains((string) file_get_contents($app . '/game/chart-plan.php'), "TRIGGERS = ['approach', 'enter', 'close_above', 'close_below', 'sweep', 'time']"), 'Plan Sync: the V1 triggers, the same as the app\'s');
// the app's default approach distances (src/game.js PC_ROOTS) = the add-on's
$gjs = (string) file_get_contents($app . '/src/game.js');
preg_match_all('/\b\'?([0-9A-Z]{1,4})\'?: \{ (?:m: \'[0-9A-Z]+\', )?prox: (\d+) \}/', (string) (preg_match('/const PC_ROOTS = \{(.*?)\};/s', $gjs, $m3) ? $m3[1] : ''), $js);
preg_match_all('/\{ "([0-9A-Z]+)", (\d+) \}/', (string) (preg_match('/Prox = new Dictionary<string, int>\s*\{(.*?)\};/s', $pc, $m4) ? $m4[1] : ''), $cs2);
ok(count($js[1]) >= 10 && array_combine($js[1], $js[2]) == array_combine($cs2[1], $cs2[2]), 'Plan Sync: the default approach distances are the app\'s (' . count($js[1]) . ' roots)');
ok(str_contains($pc, 'public static string NoPlan(string l) { return Pick(l, "No plan') && preg_match_all('/Pick\((?:lang|l), "/', $pc) >= 20, 'Plan Sync: the add-on\'s texts in English, French and Spanish');

// Plan Sync (step 4): NinjaTrader 8's Sweep Plan indicator, the same shared logic, Sweep Sync's key, never an order
$ni = (string) file_get_contents($app . '/sync/addon/ninjatrader-plan/SweepPlan.cs');
$zt = (string) file_get_contents($app . '/tools/addon-zip.py');
ok(str_contains($ni, 'public class SweepPlan : Indicator') && str_contains($ni, 'using SP = SweepPlanSync;') && str_contains($zt, "('AddOns/SweepPlanCore.cs', os.path.join('plan', 'PlanCore.cs'))") && str_contains($zt, "('Indicators/SweepPlan.cs', os.path.join('ninjatrader-plan', 'SweepPlan.cs'))"), 'Plan Sync NT8: an indicator, with the shared logic (plan/PlanCore.cs), both in the import zip (tools/addon-zip.py --plan)');
ok(preg_match('/\b(Submit\w*|CreateOrder|Enter(Long|Short)\w*|Exit(Long|Short)\w*|Flatten|CancelAllOrders|Change(Order)?)\s*\(|\.Cancel\s*\(|AccountItem/', $ni) === 0, 'Plan Sync NT8: never an order call, never an account read');
ok(str_contains($ni, 'k = SweepSyncEngine.Key ?? ""') && str_contains($ni, '"Sweep NT8 Plan " + Version') && str_contains($store, "'Sweep NT8' => 'ninjatrader'") && str_contains($ni, 'req.Headers["X-Sweep-Key"] = k') && str_contains($ni, 'req.Headers["If-None-Match"]'), 'Plan Sync NT8: Sweep Sync\'s key, named « Sweep NT8 … » (a NinjaTrader 8 key only), the plan\'s ETag');
ok(preg_match('/public static string Key = "";/', $cs) === 1 && preg_match('/public static string Url = DefaultUrl;/', $cs) === 1, 'Plan Sync NT8: Sweep Sync\'s key and server are public (the indicator reads them, same NinjaScript assembly)');
ok(str_contains($ni, '"https://app.makeitsweep.com"') && str_contains($ni, '"/api/plan-sync/today?instrument="') && str_contains($ni, '"/api/plan-sync/events"') && str_contains($ni, 'NinjaTrader.NinjaScript.Alert.AlertCallback(') && str_contains($ni, 'SetZOrder(-1)'), 'Plan Sync NT8: app.makeitsweep.com, the two routes, NinjaTrader\'s Alerts window, drawn behind the bars');
ok(!str_contains($ni, '$"') && !str_contains($ni, '?.') && !preg_match('/\bout var\b|\bnameof\(|=>\s*[^{(]*;\s*$/m', preg_replace('/\([^()]*=>[^;]*\)/', '', $ni)), 'Plan Sync NT8: plain C# 5 (no $"…", ?., out var, nameof), what NinjaTrader 8 compiles');

echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
