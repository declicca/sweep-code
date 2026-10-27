<?php
// Release dates pages (makeitsweep.com/cpi-release-dates, /fr/…, /es/…): the page with the next release in its title.
// The build writes each page with placeholders and, for every upcoming release, the texts that fill them (_nx/, never served);
// this script picks the first release that hasn't happened yet, in New York time, and fills the page. No database, no network.
// The economic calendar (/economic-calendar) works the same way: one text per week, the week under way (from Saturday, the next one).
$p = isset($_GET['p']) ? (string) $_GET['p'] : '';
if (!preg_match('~^(?:(fr|es)/)?((?:cpi|ppi|nfp|pce|gdp|retail-sales|ism-manufacturing)-release-dates|fomc-meeting-dates|economic-calendar)$~', $p, $m)) {
    http_response_code(404); header('Content-Type: text/html; charset=utf-8'); readfile(__DIR__ . '/404.html'); exit;
}
$lang = $m[1] !== '' ? $m[1] : 'en';
$page = ($m[1] !== '' ? $m[1] . '/' : '') . $m[2] . '.html';
$tpl = @file_get_contents(__DIR__ . '/_nx/' . $lang . '-' . $m[2] . '.html');
$nx = json_decode((string) @file_get_contents(__DIR__ . '/_nx/' . $lang . '-' . $m[2] . '.json'), true);
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, must-revalidate');
if ($tpl === false || !is_array($nx) || !$nx) { readfile(__DIR__ . '/' . $page); exit; }   // the page as built
$now = (new DateTime('now', new DateTimeZone('America/New_York')))->format('Y-m-d\TH:i');
$v = end($nx);   // past the last known release: the last one
foreach ($nx as $x) { if ($x['at'] >= $now) { $v = $x; break; } }
unset($v['at']);
echo strtr($tpl, $v);
