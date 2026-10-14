<?php
// Sweep — notifications on the phone, local tests only (tools/run.sh, tools/par.py): a key pair made once on this machine,
// in the temporary folder (never in git, never the server's). Messages go to SWEEP_PUSH_MOCK, never to a push service.
$f = sys_get_temp_dir() . '/sweep-push-test-keys.php';
if (!is_file($f)) {
    if (!function_exists('wp_new_keys')) require_once dirname(__DIR__) . '/push/web-push.php';   // (the served copy has already loaded its own)
    $tmp = $f . '.' . getmypid();
    file_put_contents($tmp, '<?php return ' . var_export(wp_new_keys(), true) . ";\n");
    rename($tmp, $f);   // atomic: the test groups may start at the same time
}
return (array) require $f;
