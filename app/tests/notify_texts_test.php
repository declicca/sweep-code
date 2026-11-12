<?php
/* Sweep — every notification type the server registers has its words in the app, in EN, FR and ES (11 Nov.):
 *   php tests/notify_texts_test.php
 * The bell shows "<type>.title" / "<type>.body" from the app's dictionaries (src/*.js). On 10 Nov. the reminders' words
 * (g_plan, g_review, g_streak, g_weekly, g_intention) left with the Wrapped module: the list showed « g_plan.title ».
 * Static: it reads the sources only. Types that send their own keys or words (news, prop_limit, pa_alert) are left out. */
$root = dirname(__DIR__); $fails = 0;
$ok = function (bool $c, string $what) use (&$fails) { $fails += (int) !$c; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; };
$types = [];
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS));
foreach ($it as $f) {
    $p = str_replace($root . '/', '', (string) $f);
    if (substr($p, -4) !== '.php' || strpos($p, 'tests/') === 0) continue;
    $s = (string) file_get_contents((string) $f);
    if (preg_match_all("/Notify::register\\('([a-z0-9_]+)'/", $s, $m)) foreach ($m[1] as $t) $types[$t] = 1;
    if (preg_match_all('/foreach \\(\\[([^\\]]+)\\] as \\$type( => \\$\\w+)?\\) \\{?\\s*Notify::register\\(\\$type/', $s, $m, PREG_SET_ORDER)) {
        foreach ($m as $g) {
            $keyed = !empty($g[2]);   // ['type' => 'category', …] or ['type', …]
            preg_match_all($keyed ? "/'([a-z0-9_]+)' =>/" : "/'([a-z0-9_]+)'/", $g[1], $k);
            foreach ($k[1] as $t) $types[$t] = 1;
        }
    }
}
foreach (['news', 'prop_limit', 'pa_alert'] as $own) unset($types[$own]);
$js = '';
foreach (glob($root . '/src/*.js') as $f) $js .= file_get_contents($f);
$ok(count($types) >= 30, count($types) . ' notification types found in the server code');
$missing = [];
foreach (array_keys($types) as $t) {
    foreach (['title', 'body'] as $k) if (substr_count($js, "'$t.$k'") < 3) $missing[] = "$t.$k";
}
$ok(!$missing, 'each one has its title and its text in EN, FR and ES (' . implode(', ', $missing) . ')');
foreach (['g_plan', 'g_review', 'g_streak', 'g_weekly', 'g_intention'] as $t) $ok(isset($types[$t]), "$t is checked");
echo $fails ? "$fails failed\n" : "all passed\n";
exit($fails ? 1 : 0);
