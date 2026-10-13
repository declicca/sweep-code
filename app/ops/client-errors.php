<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the JS errors seen on traders' devices (table client_errors, Admin › Errors), 13 Oct.:
 *  - one error = one message with its numbers (and their sign) taken out (« moved -364px at 621ms » and « moved +25px at
 *    84ms » are the same report): sweep_err_key();
 *  - sweep_err_groups(): the list of the last 30 days, most traders first (Admin › Errors);
 *  - sweep_errors_report(): the same list as Markdown, ready to give to Claude (Admin › Errors › Export). Never any trader
 *    data: message, where, how often, how many traders, first and last time, pages, browsers, versions, the last occurrences;
 *  - sweep_error_alert(): an error not seen for 7 days → one email to the support address with its block, at most 10 a day.
 */
require_once __DIR__ . '/metrics.php';   // sweep_browser()

const SWEEP_ERR_ALERTS_PER_DAY = 10;

function sweep_err_key(string $msg): string { return trim((string) preg_replace('/[+-]?\d+(?:\.\d+)?/', '#', $msg)); }

function sweep_errors_schema(PDO $pdo): void
{
    $pdo->exec('CREATE TABLE IF NOT EXISTS client_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, msg TEXT, src TEXT, line INT, page TEXT, ua TEXT, ver TEXT, created_at INT NOT NULL)');
    $pdo->exec('CREATE TABLE IF NOT EXISTS client_error_alerts (err_key TEXT PRIMARY KEY, sent_at INT NOT NULL)');
}

/** The errors of the last $days days grouped by key, most traders first. Each group: the latest message, counts, dates (epoch), pages… and the last 3 occurrences. */
function sweep_err_groups(PDO $pdo, int $now, int $days = 30, ?string $only = null): array
{
    $st = $pdo->prepare('SELECT user_id, msg, src, line, page, ua, ver, created_at FROM client_errors WHERE created_at > ? ORDER BY created_at');
    $st->execute([$now - $days * 86400]);
    $g = [];
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) {
        $k = sweep_err_key((string) $r['msg']); if ($only !== null && $k !== $only) continue;
        $x = $g[$k] ?? ['key' => $k, 'msg' => '', 'n' => 0, 'users' => [], 'first' => (int) $r['created_at'], 'last' => 0, 'pages' => [], 'browsers' => [], 'versions' => [], 'where' => '', 'samples' => []];
        $x['n']++; $x['users'][(string) $r['user_id']] = 1; $x['last'] = (int) $r['created_at']; $x['msg'] = (string) $r['msg'];
        $br = sweep_browser((string) $r['ua']);
        if ((string) $r['page'] !== '') $x['pages'][(string) $r['page']] = 1;
        $x['browsers'][$br] = 1; if ((string) $r['ver'] !== '') $x['versions'][(string) $r['ver']] = 1;
        $where = (string) $r['src'] !== '' ? $r['src'] . ':' . (int) $r['line'] : '';
        if ($where !== '') $x['where'] = $where;
        $x['samples'][] = ['at' => (int) $r['created_at'], 'msg' => (string) $r['msg'], 'page' => (string) $r['page'], 'browser' => $br, 'ua' => (string) $r['ua'], 'ver' => (string) $r['ver'], 'where' => $where];
        if (count($x['samples']) > 3) array_shift($x['samples']);
        $g[$k] = $x;
    }
    $g = array_map(fn($x) => ['key' => $x['key'], 'msg' => $x['msg'], 'n' => $x['n'], 'traders' => count($x['users']), 'first' => $x['first'], 'last' => $x['last'],
        'pages' => array_keys($x['pages']), 'browsers' => array_keys($x['browsers']), 'versions' => array_keys($x['versions']), 'where' => $x['where'], 'samples' => array_reverse($x['samples'])], array_values($g));
    usort($g, fn($a, $b) => [$b['traders'], $b['n'], $b['last']] <=> [$a['traders'], $a['n'], $a['last']]);
    return $g;
}

function sweep_err_time(int $ts): string { return (new DateTimeImmutable('@' . $ts))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d H:i') . ' ET'; }

/** One error as a Markdown block (the export and the alert email). */
function sweep_err_block(array $e, int $i): string
{
    $md = "## $i. " . str_replace("\n", ' ', $e['msg']) . "\n\n";
    if ($e['where'] !== '') $md .= "- Où : `{$e['where']}`\n";
    $md .= "- {$e['n']} fois, " . $e['traders'] . ' trader' . ($e['traders'] > 1 ? 's' : '') . ' ; première ' . sweep_err_time($e['first']) . ', dernière ' . sweep_err_time($e['last']) . "\n";
    $md .= '- Pages : ' . (implode(', ', $e['pages']) ?: '—') . ' ; navigateurs : ' . (implode(', ', $e['browsers']) ?: '—') . ' ; versions : ' . (implode(', ', $e['versions']) ?: '—') . "\n";
    $md .= "- Dernières occurrences :\n";
    foreach ($e['samples'] as $s) $md .= '  - ' . sweep_err_time($s['at']) . ' · ' . ($s['page'] ?: '—') . ' · ' . $s['browser'] . ($s['ver'] !== '' ? ' · ' . $s['ver'] : '') . ($s['msg'] !== $e['msg'] ? ' · « ' . str_replace("\n", ' ', $s['msg']) . ' »' : '') . "\n    `" . $s['ua'] . "`\n";
    return $md . "\n";
}

/** Admin › Errors › Export: the errors of the last 30 days, ready to give to Claude. */
function sweep_errors_report(PDO $pdo, int $now): string
{
    sweep_errors_schema($pdo);
    $g = sweep_err_groups($pdo, $now);
    $md = "# Sweep — erreurs chez les traders (30 derniers jours)\n\nExporté le " . sweep_err_time($now) . ' depuis app.makeitsweep.com › Admin › Erreurs. '
        . count($g) . ' erreur' . (count($g) > 1 ? 's' : '') . ' (un message, ses chiffres mis à part). Aucune donnée de trader : message, endroit, fréquence, pages, navigateurs, versions.' . "\n\n";
    if (!$g) return $md . "Aucune erreur en 30 jours.\n";
    foreach ($g as $i => $e) $md .= sweep_err_block($e, $i + 1);
    return $md;
}

/**
 * Right after an error is recorded: if its key had no alert in the last 7 days, one email to the support address
 * (at most SWEEP_ERR_ALERTS_PER_DAY a day). $mail(subject, text) returns true when sent. Returns true when an email went.
 */
function sweep_error_alert(PDO $pdo, string $msg, callable $mail, ?int $now = null): bool
{
    $now = $now ?? time(); sweep_errors_schema($pdo);
    $k = sweep_err_key($msg); if ($k === '') return false;
    $st = $pdo->prepare('SELECT sent_at FROM client_error_alerts WHERE err_key = ?'); $st->execute([$k]);
    $last = $st->fetchColumn();
    if ($last !== false && (int) $last > $now - 7 * 86400) return false;
    $st = $pdo->prepare('SELECT COUNT(*) FROM client_error_alerts WHERE sent_at > ?'); $st->execute([$now - 86400]);
    if ((int) $st->fetchColumn() >= SWEEP_ERR_ALERTS_PER_DAY) return false;
    $g = sweep_err_groups($pdo, $now, 30, $k); if (!$g) return false;
    $text = "Une nouvelle erreur est apparue chez un trader (ou n'avait pas été vue depuis 7 jours).\n\n" . sweep_err_block($g[0], 1)
        . "Pour la faire corriger : colle ce courriel à Claude, ou Admin › Erreurs › Exporter pour la liste complète.\n";
    try { $ok = (bool) $mail('Sweep : nouvelle erreur — ' . mb_substr(str_replace("\n", ' ', $g[0]['msg']), 0, 80), $text); } catch (Throwable $e) { $ok = false; error_log('[Sweep errors] alert: ' . $e->getMessage()); }
    if ($ok) {
        $u = $pdo->prepare('UPDATE client_error_alerts SET sent_at = ? WHERE err_key = ?'); $u->execute([$now, $k]);
        if (!$u->rowCount()) $pdo->prepare('INSERT INTO client_error_alerts (err_key, sent_at) VALUES (?, ?)')->execute([$k, $now]);
    }
    return $ok;
}
