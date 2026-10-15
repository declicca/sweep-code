<?php
declare(strict_types=1);
/**
 * Sweep — no browser confirm() / alert() windows anywhere in the app (brief 02 part 14): the app asks with its own window
 * (nav.js SweepUndo.ask), in the trader's language, and reports errors with a toast.
 *   php tests/no_native_dialogs_test.php
 * Scans the app's sources (src/*.js, the pages, the PHP that prints scripts), comments left out; fails on any call that remains.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$files = array_merge(glob($app . '/src/*.js') ?: [], glob($app . '/*.html') ?: [], glob($app . '/*.php') ?: [], glob($app . '/*/*.php') ?: []);
$files = array_filter($files, fn($f) => !preg_match('#/(tests|vendor|data|node_modules)/#', $f));
$hits = []; $n = 0;
foreach ($files as $f) {
    $s = (string) file_get_contents($f); $n++;
    $s = preg_replace_callback('#/\*.*?\*/#s', fn($c) => str_repeat("\n", substr_count($c[0], "\n")), $s);   // block comments (their lines kept)
    $s = preg_replace('#(^|\s)//[^\n]*#', '$1', $s);         // line comments (not the « // » inside a URL)
    if (preg_match_all('#(?<![\w.$])(?:window\.)?(confirm|alert)\s*\(#', $s, $m, PREG_OFFSET_CAPTURE)) {
        foreach ($m[0] as [$txt, $at]) $hits[] = substr($f, strlen($app) + 1) . ':' . (substr_count(substr($s, 0, $at), "\n") + 1) . ' ' . trim($txt);
    }
}
$ok = !$hits;
echo ($ok ? 'ok   ' : 'FAIL ') . "no confirm() / alert() in the app ($n files" . ($hits ? ': ' . implode(', ', $hits) : '') . ")\n";
echo "\n" . ($ok ? 1 : 0) . ' passed, ' . ($ok ? 0 : 1) . " failed\n";
exit($ok ? 0 : 1);
