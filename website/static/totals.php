<?php
// Home page (makeitsweep.com/, /fr/, /es/): the live totals banner under the hero (brief « avance concurrentielle », step 9).
// The totals come from the app (api/public-totals: four counts, nothing personal) and are kept here for an hour.
// The banner (_nx/<lang>-totals.html, written by the build) replaces the page's <!--totals--> mark only once every
// threshold is reached, so a number is in the HTML from the first byte and never reads 0; otherwise the page as built.
const TOTALS_URL = 'https://app.makeitsweep.com/api/public-totals';
const TOTALS_MIN = ['traders' => 250, 'trades' => 1000, 'payouts' => 25, 'evals_passed' => 1];
const TOTALS_TTL = 3600;   // seconds a fetch is kept
const TOTALS_RETRY = 600;  // after a failed fetch, the last totals are kept this long before trying again

$p = isset($_GET['p']) ? (string) $_GET['p'] : '';
if (!preg_match('~^(?:(fr|es)/)?$~', $p, $m)) {
    http_response_code(404); header('Content-Type: text/html; charset=utf-8'); readfile(__DIR__ . '/404.html'); exit;
}
$lang = isset($m[1]) && $m[1] !== '' ? $m[1] : 'en';
$page = __DIR__ . '/' . ($lang === 'en' ? '' : $lang . '/') . 'index.html';
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, must-revalidate');

function sweep_totals() {
    $file = __DIR__ . '/_nx/totals-cache.json';
    $c = json_decode((string) @file_get_contents($file), true);
    if (is_array($c) && isset($c['until']) && $c['until'] > time()) return $c['totals'] ?? null;
    $lock = @fopen($file . '.lock', 'c');
    if ($lock && !flock($lock, LOCK_EX | LOCK_NB)) return is_array($c) ? ($c['totals'] ?? null) : null;   // another request is fetching
    $raw = @file_get_contents(TOTALS_URL, false, stream_context_create(['http' => ['timeout' => 2, 'ignore_errors' => false, 'header' => "Accept: application/json\r\n"]]));
    $d = json_decode((string) $raw, true);
    $ok = is_array($d);
    foreach (array_keys(TOTALS_MIN) as $k) $ok = $ok && isset($d[$k]) && is_int($d[$k]) && $d[$k] >= 0;
    $totals = $ok ? array_intersect_key($d, TOTALS_MIN) : (is_array($c) ? ($c['totals'] ?? null) : null);
    @file_put_contents($file, json_encode(['until' => time() + ($ok ? TOTALS_TTL : TOTALS_RETRY), 'totals' => $totals]), LOCK_EX);
    if ($lock) { flock($lock, LOCK_UN); fclose($lock); }
    return $totals;
}

function sweep_num($n, $lang) {
    if ($lang === 'fr') return number_format($n, 0, ',', "\u{202F}");
    if ($lang === 'es') return $n < 10000 ? (string) $n : number_format($n, 0, ',', '.');   // Spanish groups from 10 000, as the browser does
    return number_format($n);
}

$html = @file_get_contents($page);
if ($html === false) { http_response_code(404); readfile(__DIR__ . '/404.html'); exit; }
$t = sweep_totals();
$live = is_array($t);
foreach (TOTALS_MIN as $k => $min) $live = $live && isset($t[$k]) && $t[$k] >= $min;
$tpl = $live ? @file_get_contents(__DIR__ . '/_nx/' . $lang . '-totals.html') : false;
if ($tpl !== false) {
    $v = [];
    foreach (TOTALS_MIN as $k => $min) $v['{' . $k . '}'] = sweep_num($t[$k], $lang);
    $html = str_replace('<!--totals-->', strtr($tpl, $v), $html);
}
echo $html;
