<?php
// Sweep — local test configuration (copied to /tmp/g/config.php by tools/sync.sh). Test values only.
$c = require __DIR__ . '/config.sample.php';
return array_replace($c, [
    'user'     => 'mateo',
    'password' => 'sweep-local-test-1',
    'app_url'  => 'http://127.0.0.1:8095/',
    'smtp'     => ['host' => '', 'port' => 465, 'user' => '', 'pass' => ''],
    'data_dir' => __DIR__ . '/data',
]);
