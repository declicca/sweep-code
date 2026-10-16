<?php
declare(strict_types=1);
/**
 * Sweep — the test servers never call Google (brief 00, phase 1.3, 16 Oct.), without network:
 *   php tests/ai_offline_test.php
 * SWEEP_AI_OFFLINE=1 (set by tools/run.sh and tools/par.py, never on the server): sai_http sends nothing — the economic
 * calendar's AI, which has no mock, answered « API key not valid » from Google at every test run. A local server stands for
 * Google here and counts the requests: none with the switch, one without it (the switch is what stops it).
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
require $app . '/ai/ai-core.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$tmp = sys_get_temp_dir() . '/sweep-offline-' . bin2hex(random_bytes(4)); mkdir($tmp);
file_put_contents("$tmp/google.php", '<?php file_put_contents(__DIR__ . "/hits", "x", FILE_APPEND); header("Content-Type: application/json"); echo "{}";');
$port = 20000 + random_int(0, 9999);
$srv = proc_open([PHP_BINARY, '-S', "127.0.0.1:$port", "$tmp/google.php"], [['file', '/dev/null', 'r'], ['file', '/dev/null', 'w'], ['file', '/dev/null', 'w']], $pp);
for ($i = 0; $i < 50 && !@fsockopen('127.0.0.1', $port); $i++) usleep(100000);
$cfg = ['endpoint' => "http://127.0.0.1:$port/{model}", 'model' => 'm', 'api_key' => 'test', 'timeout_seconds' => 3];
$hits = function () use ($tmp) { clearstatcache(); return is_file("$tmp/hits") ? strlen((string) file_get_contents("$tmp/hits")) : 0; };
putenv('SWEEP_AI_OFFLINE=1');
[$st] = sai_http($cfg, ['contents' => []]);
$ok($st === 0 && $hits() === 0, "SWEEP_AI_OFFLINE=1: nothing sent, a network error for the caller ($st, {$hits()} request)");
putenv('SWEEP_AI_OFFLINE');
[$st2] = sai_http($cfg, ['contents' => []]);
$ok($st2 === 200 && $hits() === 1, "without it: the request goes out ($st2, {$hits()} request) — the switch is what stops it");
foreach (['tools/run.sh', 'tools/par.py'] as $f) $ok(strpos((string) file_get_contents("$app/$f"), 'SWEEP_AI_OFFLINE') !== false, "$f starts the test servers with SWEEP_AI_OFFLINE");
proc_terminate($srv); proc_close($srv);
foreach (glob("$tmp/*") as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
