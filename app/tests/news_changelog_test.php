<?php
/**
 * Sweep — every delivery says what traders are told (14 Nov., Mateo: « chaque nouveauté ajoutée automatiquement dans les
 * nouveautés, avec les notifications »):
 *   php tests/news_changelog_test.php
 * From 14 Nov. 2026, each line of CHANGELOG.md ends with one marker:
 *   [news: id, …]  the « What's new » entries (NEWS, src/game.js) that announce it: the window once, and the bell (Nouveautés);
 *   (correctif)    a fix of something that should already work: nothing new to announce;
 *   (interne)      nothing a trader sees (tools, tests, admin, code not served yet).
 * Checked: the marker is there; each id exists in NEWS, with its title, sentence and button in EN, FR and ES, an icon, an action
 * and a date (YYYY-MM-DD); no id twice in NEWS.
 */
$root = dirname(__DIR__);
$fails = 0;
function ok(bool $c, string $what): void { global $fails; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; if (!$c) $fails++; }

const FROM = '2026-11-14';
const MONTHS = ['janv' => 1, 'févr' => 2, 'mars' => 3, 'avr' => 4, 'mai' => 5, 'juin' => 6, 'juil' => 7, 'août' => 8, 'sept' => 9, 'oct' => 10, 'nov' => 11, 'déc' => 12];

// NEWS in src/game.js: one entry per « { id: '…', d: '…', … } » block, up to the next entry or the end of the list
$js = file_get_contents("$root/src/game.js");
$start = strpos($js, 'const NEWS = [');
$end = strpos($js, "\n  ];", $start);
ok($start !== false && $end !== false, 'NEWS is in src/game.js');
$list = substr($js, $start, $end - $start);
preg_match_all("/\\{ id: '([a-z0-9-]+)', d: '([^']*)'/", $list, $m, PREG_OFFSET_CAPTURE);
$news = [];
foreach ($m[1] as $i => [$id, $pos]) {
    $next = $m[0][$i + 1][1] ?? strlen($list);
    ok(!isset($news[$id]), "NEWS: « $id » only once");
    $news[$id] = ['d' => $m[2][$i][0], 'body' => substr($list, $pos, $next - $pos)];
}
ok(count($news) >= 4, 'NEWS: ' . count($news) . ' entries read');
foreach ($news as $id => $n) {
    $b = $n['body'];
    $langs = true;
    foreach (['t', 's', 'b'] as $k) {
        if (!preg_match("/\\b$k: \\{ en: '[^']+', fr: '[^']+', es: '[^']+' \\}/u", $b)) $langs = false;
    }
    ok($langs, "NEWS « $id »: title, sentence and button in EN, FR and ES");
    ok((bool) preg_match('/^\d{4}-\d{2}-\d{2}$/', $n['d']) && (bool) preg_match("/ ic: '[a-z]+'/", $b) && (bool) preg_match("/ act: '[^']+'/", $b), "NEWS « $id »: a date, an icon, an action");
}

// CHANGELOG.md: the lines from FROM on
$lines = preg_grep('/^- \*\*\d{1,2} \S+ \d{4} — /u', file("$root/CHANGELOG.md", FILE_IGNORE_NEW_LINES));
$seen = 0;
foreach ($lines as $l) {
    if (!preg_match('/^- \*\*(\d{1,2}) (\S+?)\.? (\d{4}) — (.*?)\*\*/u', $l, $h)) continue;
    $mo = MONTHS[rtrim($h[2], '.')] ?? null;
    if (!$mo) { ok(false, "CHANGELOG: month « {$h[2]} » read"); continue; }
    $day = sprintf('%04d-%02d-%02d', $h[3], $mo, $h[1]);
    if ($day < FROM) continue;
    $seen++;
    $title = mb_substr($h[4], 0, 60);
    $tail = rtrim($l);
    if (preg_match('/\[news: ([a-z0-9, -]+)\]$/', $tail, $nm)) {
        $ids = array_filter(array_map('trim', explode(',', $nm[1])));
        $missing = array_values(array_filter($ids, fn($id) => !isset($news[$id])));
        ok($ids && !$missing, "CHANGELOG « $title » ($day): announced by " . implode(', ', $ids) . ($missing ? ' — not in NEWS: ' . implode(', ', $missing) : ''));
    } else {
        ok((bool) preg_match('/\((correctif|interne)\)$/u', $tail), "CHANGELOG « $title » ($day): ends with [news: id], (correctif) or (interne) — add its « What's new » entry to NEWS (src/game.js)");
    }
}
ok($seen > 0, "CHANGELOG: $seen lines from " . FROM . ' checked');
echo $fails ? "$fails failed\n" : "all passed\n";
exit($fails ? 1 : 0);
