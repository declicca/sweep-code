<?php
/**
 * Sweep — a stand-in for the Loops API (tests only), served by php -S:
 *   LOOPS_MOCK_DIR=/tmp/x php -S 127.0.0.1:8099 tests/loops_mock.php
 * Every call is written to $LOOPS_MOCK_DIR/calls.jsonl (method, path, key, body). The key « test-key » is accepted, any other
 * gets 401 like Loops. Contact properties created are kept in props.json; « slow » in the body waits 5 s (timeouts).
 */
$dir = rtrim((string) getenv('LOOPS_MOCK_DIR'), '/') ?: sys_get_temp_dir();
$path = (string) parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH);
$q = (string) parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_QUERY);
$raw = (string) file_get_contents('php://input');
$body = json_decode($raw, true);
$key = preg_replace('/^Bearer\s+/', '', (string) ($_SERVER['HTTP_AUTHORIZATION'] ?? ''));
file_put_contents($dir . '/calls.jsonl', json_encode(['method' => $_SERVER['REQUEST_METHOD'] ?? '', 'path' => $path . ($q !== '' ? '?' . $q : ''), 'key' => $key, 'body' => $body, 'at' => microtime(true)]) . "\n", FILE_APPEND | LOCK_EX);
header('Content-Type: application/json');
$out = function (int $code, $data) { http_response_code($code); echo json_encode($data); exit; };
if ($key !== 'test-key') $out(401, ['success' => false, 'message' => 'Invalid API key']);
if (is_array($body) && !empty($body['slow'])) sleep(5);
$propsFile = $dir . '/props.json';
$props = is_file($propsFile) ? (json_decode((string) file_get_contents($propsFile), true) ?: []) : [];
$m = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($path === '/api/v1/contacts/properties' && $m === 'GET') $out(200, array_map(fn($k, $t) => ['key' => $k, 'label' => $k, 'type' => $t], array_keys($props), $props));
if ($path === '/api/v1/contacts/properties' && $m === 'POST') {
    if (isset($props[$body['name'] ?? ''])) $out(400, ['success' => false, 'message' => 'Property already exists.']);
    $props[(string) $body['name']] = (string) $body['type']; file_put_contents($propsFile, json_encode($props)); $out(200, ['success' => true]);
}
if ($path === '/api/v1/events/send' && $m === 'POST') {
    if (empty($body['eventName']) || (empty($body['email']) && empty($body['userId']))) $out(400, ['success' => false, 'message' => 'eventName and email or userId are required']);
    foreach ($body as $k => $v) if (!in_array($k, ['email', 'userId', 'eventName', 'eventProperties', 'mailingLists', 'firstName', 'lastName'], true) && !isset($props[$k]))
        $out(400, ['success' => false, 'message' => "Contact property $k does not exist"]);
    $out(200, ['success' => true]);
}
if ($path === '/api/v1/contacts/update' && $m === 'PUT') $out(200, ['success' => true, 'id' => 'c_' . md5((string) ($body['userId'] ?? ''))]);
if ($path === '/api/v1/contacts/delete' && $m === 'POST') $out(200, ['success' => true, 'message' => 'Contact deleted.']);
$out(404, ['success' => false, 'message' => 'Not found']);
