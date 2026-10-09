<?php
// Sweep — router for `php -S`, mirrors app/.htaccess (local tests only).
$path = rawurldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$rel = ltrim($path, '/');
if (preg_match('#^(app\.html|auth\.html|config(\.sample)?\.php|econ\.php|README\.md|NOTES\.md|error_log|ai/.*|billing/.*|growth/.*|notify/.*|game/.*|chart/.*|export/.*|ops/.*|tests/.*|presets/.*|src/.*|tools/.*|data(/.*)?)$#', $rel)) { http_response_code(403); exit; }
$route = null;
if ($rel === '' || preg_match('#^index\.html?$#', $rel)) $route = 'app';
elseif (preg_match('#^api/(.*)$#', $rel, $m)) $route = 'api/' . $m[1];
elseif (preg_match('#^r/([A-Za-z0-9]{3,16})/?$#', $rel, $m)) $route = 'ref/' . $m[1];
elseif (preg_match('#^s/([A-Za-z0-9]{10,24}(\.png)?)$#', $rel, $m)) $route = 's/' . $m[1];
elseif (preg_match('#^uploads/([A-Za-z0-9-]+)$#', $rel, $m)) $route = 'uploads/' . $m[1];
if ($route === null) {
    if (is_file(__DIR__ . '/' . $rel) || $rel === 'api.php') return false;   // static file served by php -S
    http_response_code(404); exit;
}
$_GET['r'] = $route; $_REQUEST['r'] = $route;
$_SERVER['SCRIPT_NAME'] = '/api.php'; $_SERVER['SCRIPT_FILENAME'] = __DIR__ . '/api.php';
chdir(__DIR__);
require __DIR__ . '/api.php';
