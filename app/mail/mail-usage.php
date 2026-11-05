<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — what each trader uses (feedback brief, step 2, 5 Nov. 2026). Only what the app already keeps, sample data never:
 *   journal   trades logged (game_analytics trade_logged)        plan     morning plans saved (plan_saved)
 *   review    evening reviews (review_saved)                     weekly   weekly recaps opened (weekly_opened)
 *   stats     the Stats page opened (stats_viewed, once a day)   sync     trades imported or synced (trade_logged, not by hand)
 *   payouts   payouts recorded (documents)                       rules    an account on a firm's preset: Sweep follows its rules
 *   coach     the AI coach (ai_log: chat, ask, debriefs, reviews) share   a card shared (share_card_created / shared)
 * A profile = the days each one was used in the last 30 days (New York days), the ones ever used, the most used (rules
 * aside: it works on its own), trades of the last 7 days (a copy once), the streak of the game (days in a row).
 * Kept in mail_usage: every trader at the daily run (7:30 New York, mail/mail-auto.php ma_cron), and one trader again when
 * an email that uses its values leaves (ml_compose). The values of the texts: {top_feature}, {trades_week}, {streak},
 * {progress} (a sentence from the real numbers, empty when there is nothing true to say).
 */

const MU_FEATURES = ['journal', 'plan', 'review', 'weekly', 'stats', 'sync', 'payouts', 'rules', 'coach', 'share'];
const MU_COACH = ['chat', 'ask', 'day_debrief', 'health', 'trade_feedback', 'weekly_review', 'month_review'];
const MU_T = [
    'en' => ['name' => ['journal' => 'Journal', 'plan' => 'Morning plan', 'review' => 'Evening review', 'weekly' => 'Weekly recap', 'stats' => 'Stats', 'sync' => 'Import and sync',
                        'payouts' => 'Payouts (money received from a firm)', 'rules' => 'Firm rules', 'coach' => 'AI coach', 'share' => 'Sharing'],
             'in' => ['journal' => 'your journal', 'plan' => 'the morning plan', 'review' => 'the evening review', 'weekly' => 'the weekly recap', 'stats' => 'the stats', 'sync' => 'import and sync',
                      'payouts' => 'payouts', 'rules' => 'the firm rules', 'coach' => 'the AI coach', 'share' => 'sharing'],
             'week' => 'This week: {n} trades journaled', 'week1' => 'This week: 1 trade journaled', 'row' => ', {s} days in a row', 'streak' => '{s} days in a row in Sweep.',
             'top' => 'This month you used {f} on {d} days.'],
    'fr' => ['name' => ['journal' => 'Journal', 'plan' => 'Plan du matin', 'review' => 'Revue du soir', 'weekly' => 'Bilan de la semaine', 'stats' => 'Stats', 'sync' => 'Import et synchro',
                        'payouts' => 'Payouts (argent reçu d’une firme)', 'rules' => 'Règles de firme', 'coach' => 'Coach IA', 'share' => 'Partage'],
             'in' => ['journal' => 'ton journal', 'plan' => 'le plan du matin', 'review' => 'la revue du soir', 'weekly' => 'le bilan de la semaine', 'stats' => 'les stats', 'sync' => 'l’import et la synchro',
                      'payouts' => 'les payouts', 'rules' => 'les règles de firme', 'coach' => 'le coach IA', 'share' => 'le partage'],
             'week' => 'Cette semaine : {n} trades journalisés', 'week1' => 'Cette semaine : 1 trade journalisé', 'row' => ', {s} jours d’affilée', 'streak' => '{s} jours d’affilée sur Sweep.',
             'top' => 'Ce mois-ci, tu as utilisé {f} {d} jours.'],
    'es' => ['name' => ['journal' => 'Diario', 'plan' => 'Plan de la mañana', 'review' => 'Revisión de la tarde', 'weekly' => 'Resumen semanal', 'stats' => 'Estadísticas', 'sync' => 'Importación y sincronización',
                        'payouts' => 'Payouts (dinero recibido de una firma)', 'rules' => 'Reglas de la firma', 'coach' => 'Coach IA', 'share' => 'Compartir'],
             'in' => ['journal' => 'tu diario', 'plan' => 'el plan de la mañana', 'review' => 'la revisión de la tarde', 'weekly' => 'el resumen semanal', 'stats' => 'las estadísticas', 'sync' => 'la importación y sincronización',
                      'payouts' => 'los payouts', 'rules' => 'las reglas de la firma', 'coach' => 'el coach IA', 'share' => 'compartir'],
             'week' => 'Esta semana: {n} operaciones registradas', 'week1' => 'Esta semana: 1 operación registrada', 'row' => ', {s} días seguidos', 'streak' => '{s} días seguidos en Sweep.',
             'top' => 'Este mes usaste {f} {d} días.'],
];

function mu_schema(PDO $pdo): void
{
    static $done = false; if ($done) return;
    $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $pdo->exec($my ? 'CREATE TABLE IF NOT EXISTS mail_usage (user_id VARCHAR(120) NOT NULL PRIMARY KEY, data_json TEXT NOT NULL, updated_at INT NOT NULL) DEFAULT CHARSET=utf8mb4'
        : 'CREATE TABLE IF NOT EXISTS mail_usage (user_id TEXT PRIMARY KEY, data_json TEXT NOT NULL, updated_at INTEGER NOT NULL)');
    $done = true;
}
/** rows of a query, [] when its table is not there yet (a new install, a test database) */
function mu_rows(PDO $pdo, string $sql, array $args): array
{
    try { $st = $pdo->prepare($sql); $st->execute($args); return $st->fetchAll(PDO::FETCH_ASSOC); } catch (Throwable $e) { return []; }
}
function mu_day(int $ts): string { return (new DateTimeImmutable('@' . $ts))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d'); }

/** A trader's profile now: ['days' => [feature => days used in 30], 'ever' => [features], 'top', 'trades_week', 'streak', 'at'] */
function mu_profile(PDO $pdo, string $uid, ?int $now = null): array
{
    $now = $now ?? time(); $from = $now - 30 * 86400;
    $days = array_fill_keys(MU_FEATURES, []); $ever = [];
    $ev = ['plan_saved' => 'plan', 'review_saved' => 'review', 'weekly_opened' => 'weekly', 'stats_viewed' => 'stats', 'share_card_created' => 'share', 'share_card_shared' => 'share'];
    foreach (mu_rows($pdo, 'SELECT event, meta_json, created_at FROM game_analytics WHERE user_id = ?', [$uid]) as $r) {
        $e = (string) $r['event'];
        if ($e === 'trade_logged') { $m = (string) ((json_decode((string) $r['meta_json'], true) ?: [])['method'] ?? 'manual'); $fs = $m === 'manual' ? ['journal'] : ['journal', 'sync']; }
        elseif (isset($ev[$e])) $fs = [$ev[$e]];
        else continue;
        foreach ($fs as $f) { $ever[$f] = true; if ((int) $r['created_at'] > $from) $days[$f][mu_day((int) $r['created_at'])] = true; }
    }
    foreach (mu_rows($pdo, 'SELECT task, created_at FROM ai_log WHERE user_id = ?', [$uid]) as $r) {
        if (!in_array((string) $r['task'], MU_COACH, true)) continue;
        $t = (int) strtotime((string) $r['created_at'] . ' UTC'); $ever['coach'] = true;
        if ($t > $from) $days['coach'][mu_day($t)] = true;
    }
    $since = gmdate('Y-m-d', $now - 8 * 86400); $wk = mu_day($now - 6 * 86400); $seen = []; $week = 0;
    foreach (mu_rows($pdo, "SELECT collection, data, created_at FROM documents WHERE user_id = ? AND collection IN ('payouts', 'accounts', 'trades')", [$uid]) as $r) {
        $col = (string) $r['collection'];
        if ($col === 'trades' && strcmp((string) $r['created_at'], $since) < 0) continue;   // a trade of the last 7 days was written after it happened
        $d = json_decode((string) $r['data'], true); if (!is_array($d) || !empty($d['demo'])) continue;
        if ($col === 'payouts') { $ever['payouts'] = true; $t = (int) strtotime((string) $r['created_at']); if ($t > $from) $days['payouts'][mu_day($t)] = true; }
        elseif ($col === 'accounts') { if (trim((string) ($d['preset'] ?? '')) !== '' && empty($d['archived'])) { $ever['rules'] = true; $days['rules']['on'] = true; } }
        elseif (strcmp((string) ($d['date'] ?? ''), $wk) >= 0) {
            $g = (string) ($d['copy_group'] ?? ''); if ($g !== '') { if (isset($seen[$g])) continue; $seen[$g] = true; }
            $week++;
        }
    }
    $n = array_map('count', $days); $rank = $n; unset($rank['rules']);
    arsort($rank); $top = (string) array_key_first($rank); if (!$rank[$top]) $top = '';
    $streak = 0; foreach (mu_rows($pdo, 'SELECT streak_current FROM user_game_profile WHERE user_id = ?', [$uid]) as $r) $streak = (int) $r['streak_current'];
    return ['days' => $n, 'ever' => array_values(array_intersect(MU_FEATURES, array_keys($ever))), 'top' => $top, 'trades_week' => $week, 'streak' => $streak, 'at' => $now];
}
/** the profile computed and kept */
function mu_save(PDO $pdo, string $uid, ?int $now = null): array
{
    mu_schema($pdo); $p = mu_profile($pdo, $uid, $now);
    $j = json_encode($p);
    try { $pdo->prepare('INSERT INTO mail_usage (user_id, data_json, updated_at) VALUES (?, ?, ?)')->execute([$uid, $j, $p['at']]); }
    catch (Throwable $e) { $pdo->prepare('UPDATE mail_usage SET data_json = ?, updated_at = ? WHERE user_id = ?')->execute([$j, $p['at'], $uid]); }   // already there
    return $p;
}
/** {progress}: the trades of the week (and the streak), else the streak, else the most used feature; '' when nothing is true */
function mu_progress(array $p, string $lang): string
{
    $L = MU_T[$lang] ?? MU_T['en']; $s = (int) $p['streak'];
    if ($p['trades_week'] > 0) return ($p['trades_week'] === 1 ? $L['week1'] : str_replace('{n}', (string) $p['trades_week'], $L['week'])) . ($s >= 2 ? str_replace('{s}', (string) $s, $L['row']) : '') . '.';
    if ($s >= 2) return str_replace('{s}', (string) $s, $L['streak']);
    if ($p['top'] !== '' && ($d = (int) $p['days'][$p['top']]) >= 2) return strtr($L['top'], ['{f}' => $L['in'][$p['top']], '{d}' => (string) $d]);
    return '';
}
/** the values of the texts in this language */
function mu_vars(array $p, string $lang): array
{
    $L = MU_T[$lang] ?? MU_T['en'];
    return ['top_feature' => $p['top'] !== '' ? $L['in'][$p['top']] : '', 'trades_week' => (string) $p['trades_week'], 'streak' => (string) $p['streak'], 'progress' => mu_progress($p, $lang)];
}
/** the example of the preview and the test email */
function mu_example(string $lang): array
{
    return mu_vars(['days' => ['plan' => 8] + array_fill_keys(MU_FEATURES, 0), 'ever' => [], 'top' => 'plan', 'trades_week' => 12, 'streak' => 4], $lang);
}
function mu_uses(string $s): bool { return (bool) preg_match('/\{(top_feature|trades_week|streak|progress)\}/', $s); }

/** The daily run: every trader who can sign in (not disabled). Returns how many profiles were kept. */
function mu_daily(PDO $pdo, ?int $now = null): int
{
    mu_schema($pdo); $now = $now ?? time(); $n = 0;
    foreach (mu_rows($pdo, 'SELECT id FROM users WHERE disabled = 0', []) as $u) { try { mu_save($pdo, (string) $u['id'], $now); $n++; } catch (Throwable $e) { error_log('[Sweep usage] ' . $u['id'] . ': ' . $e->getMessage()); } }
    $pdo->prepare('DELETE FROM mail_usage WHERE updated_at < ?')->execute([$now - 3 * 86400]);   // a deleted or disabled trader
    return $n;
}
/**
 * Admin › Emails « What they use »: among the active traders (a feature used in the last 30 days; Sweep's own accounts
 * aside), the share who used each one. The first time (no daily run yet), computed now.
 */
function mu_summary(PDO $pdo, ?int $now = null): array
{
    mu_schema($pdo); $now = $now ?? time();
    if (!mu_rows($pdo, 'SELECT 1 FROM mail_usage LIMIT 1', [])) mu_daily($pdo, $now);
    $skip = []; foreach (mu_rows($pdo, 'SELECT id FROM users WHERE is_internal = 1 OR is_admin = 1 OR disabled = 1', []) as $u) $skip[(string) $u['id']] = true;
    $active = 0; $used = array_fill_keys(MU_FEATURES, 0); $at = 0;
    foreach (mu_rows($pdo, 'SELECT user_id, data_json, updated_at FROM mail_usage', []) as $r) {
        if (isset($skip[(string) $r['user_id']])) continue;
        $p = json_decode((string) $r['data_json'], true); if (!is_array($p)) continue;
        $d = (array) ($p['days'] ?? []); $own = $d; unset($own['rules']);
        if (!array_filter($own)) continue;
        $active++; $at = max($at, (int) $r['updated_at']);
        foreach (MU_FEATURES as $f) if (!empty($d[$f])) $used[$f]++;
    }
    arsort($used);
    $rows = []; foreach ($used as $f => $c) $rows[] = ['key' => $f, 'name' => array_map(fn($L) => $L['name'][$f], MU_T), 'n' => $c, 'pct' => $active ? (int) round($c / $active * 100) : 0];
    return ['active' => $active, 'features' => $rows, 'at' => $at ?: null];
}
