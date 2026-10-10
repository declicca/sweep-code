<?php
declare(strict_types=1);
/**
 * Sweep — the server's side of tests/e2e_weekly_parity.py, on the dev server's database (never the live one):
 *   php tests/weekly_brief.php <sqlite file> <trader id> <monday> <lang>
 * Prints, as JSON: the « Your week » numbers (GameWeeklyMail::brief), the week's summary the app receives, the trader's
 * link token for the « stop the email » page, and whether the email is stopped.
 */
if (PHP_SAPI !== 'cli' || $argc < 5) { fwrite(STDERR, "usage: php tests/weekly_brief.php <db> <uid> <monday> <lang>\n"); exit(2); }
$app = dirname(__DIR__);
$pdo = new PDO('sqlite:' . $argv[1], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('PRAGMA busy_timeout = 5000');
function db() { global $pdo; return $pdo; }
require $app . '/notify/notify.php';
require $app . '/game/game.php';
GameEngine::setPdo($pdo);
[$uid, $mon, $lang] = [$argv[2], $argv[3], $argv[4]];
$tok = GameWeeklyMail::token($uid);
echo json_encode(['brief' => GameWeeklyMail::brief($uid, $mon, $lang), 'summary' => GameV2b::weekSummary($uid, $mon), 'token' => $tok,
    'off' => (int) $pdo->query('SELECT weekly_off FROM email_prefs WHERE token = ' . $pdo->quote($tok))->fetchColumn() === 1], JSON_UNESCAPED_UNICODE) . "\n";
