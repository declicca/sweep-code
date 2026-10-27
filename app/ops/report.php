<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Admin › « Export for Claude » (27 Oct.): everything Admin shows, in one Markdown file to give to Claude.
 * The dashboard, the start, retention, sources, how the app is used (ops/usage.php), trade entry, the game, searches
 * with no result, unfinished sign-ups (a count), sync, Sweep AI, revenue, health, presets, traders' feedback and the
 * JS errors. Only counts and shares, never a name, an email, a trade or an amount of a trader; the feedback texts are
 * given with any email address, link or phone number taken out.
 */
require_once __DIR__ . '/metrics.php';
require_once __DIR__ . '/health.php';
require_once __DIR__ . '/usage.php';
require_once __DIR__ . '/client-errors.php';

function sweep_report_redact(string $s): string
{
    $s = (string) preg_replace('/[^\s@]+@[^\s@]+\.[a-z]{2,}/i', '[courriel]', $s);
    $s = (string) preg_replace('#https?://\S+|www\.\S+#i', '[lien]', $s);
    return trim((string) preg_replace('/\+?\d[\d ().-]{8,}\d/', '[numéro]', $s));
}

function sweep_full_report(PDO $pdo, array $cfg, string $app, int $now): string
{
    $q = function (string $sql, array $a = []) use ($pdo) { $s = $pdo->prepare($sql); $s->execute($a); return $s; };
    $try = function (callable $f, $or = null) { try { return $f(); } catch (Throwable $e) { return $or; } };
    $has = fn(string $t) => (bool) $q("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", [$t])->fetchColumn();
    $pc = fn($o) => is_array($o) ? (($o['pct'] ?? null) === null ? '—' : $o['pct'] . ' %') . (isset($o['of']) ? ' (sur ' . $o['of'] . ')' : '') : '—';
    $dur = fn($m) => $m === null ? '—' : ($m < 120 ? $m . ' min' : ($m < 2880 ? round($m / 60) . ' h' : round($m / 1440) . ' j'));
    $at = fn($ts) => $ts ? sweep_err_time((int) (is_numeric($ts) ? $ts : strtotime((string) $ts))) : '—';
    $tbl = function (array $head, array $rows): string {
        if (!$rows) return "_Rien._\n\n";
        $c = fn($v) => str_replace(["|", "\n"], ['\\|', ' '], (string) $v);
        $o = '| ' . implode(' | ', $head) . " |\n|" . str_repeat(' --- |', count($head)) . "\n";
        foreach ($rows as $r) $o .= '| ' . implode(' | ', array_map($c, $r)) . " |\n";
        return $o . "\n";
    };
    $real = [];   // the traders counted, as on the dashboard (ops/metrics.php): not disabled, not one of Mateo's or a test account (« internal »)
    foreach ($q('SELECT id FROM users WHERE disabled = 0 AND COALESCE(is_internal, 0) = 0') as $r) $real[$r['id']] = true;
    $m = sweep_metrics($pdo, $app); $b = $m['brief'];

    $md = "# Sweep — tout Admin, pour Claude\n\nExporté le " . sweep_err_time($now) . " depuis app.makeitsweep.com › Admin. " . count($real) . " traders comptés (comptes de Mateo et de test à part, comme sur le tableau de bord). "
        . "Seulement des nombres et des parts : aucun nom, courriel, trade ni montant d'un trader. Jours : heure de New York. J = jours.\n\n";

    $md .= "## 1. En bref\n\n" . $tbl(['Indicateur', 'Valeur'], [
        ['Traders avec 3+ journées balayées (7 j), l\'étoile du nord', $m['north_star']],
        ['Traders actifs (7 j)', $m['active_7d']],
        ['Inscriptions 7 j / 30 j', $m['signups']['d7'] . ' / ' . $m['signups']['d30']],
        ['Inscription → premier trade (médiane)', $dur($m['first_trade']['median_min']) . ' ; ' . $m['first_trade']['day1_pct'] . ' % le 1er jour (sur ' . $m['first_trade']['of'] . ')'],
        ['Activation : 1er trade en 24 h', $pc($m['activation_24h'])],
        ['Activation : un trade le jour de l\'inscription', $pc($b['activation_day0'])],
        ['1re journée balayée en 7 jours', $pc($m['aha_7d'])],
        ['Semaine 2 : 3+ journées balayées', $pc($m['retention_w2'])],
        ['Rétention J7 (trade ou revue, jours 7 à 13)', $pc($b['retention_d7'])],
        ['Rétention J30 (jours 30 à 36)', $pc($b['retention_d30'])],
        ['Journées balayées (séances avec trades, 3 anneaux, 30 j)', $pc($b['swept_sessions_30d'])],
        ['Journées fermées (revue faite, 30 j)', $pc($b['closed_sessions_30d'])],
        ['Bilans du vendredi ouverts (8 semaines)', $pc($b['weekly_opened_8w'])],
        ['MRR', $m['revenue']['mrr'] !== null ? '$' . $m['revenue']['mrr'] : '—'],
        ['Abonnements', implode(' · ', array_map(fn($s) => $s['plan'] . ' ' . $s['i'] . ($s['founding'] ? ' fondateur' : '') . ' ×' . $s['n'], $m['revenue']['subs'])) ?: '—'],
        ['Coût IA aujourd\'hui / 7 j', '$' . $m['ai']['today'] . ' (' . $m['ai']['calls_today'] . ' appels) / $' . $m['ai']['d7']],
        ['Erreurs 24 h (JS / PHP)', $m['errors']['js_24h'] . ' / ' . $m['errors']['php_24h']],
    ]);

    $s = $b['start']; $all = max(1, (int) $s['signed_up']);
    $md .= "## 2. Le démarrage : inscription → premier trade\n\nNombre d'inscrits qui atteignent chaque étape, part des inscrits, temps médian depuis l'inscription (données d'exemple à part).\n\n"
        . $tbl(['Étape', 'Traders', 'Part', 'Médiane'], [
            ['Inscrits', $s['signed_up'], '100 %', '—'], ['Prénom', $s['first_name']['n'], round($s['first_name']['n'] / $all * 100) . ' %', '—'],
            ['Premier compte', $s['account']['n'], round($s['account']['n'] / $all * 100) . ' %', $dur($s['account']['median_min'])],
            ['Premier plan', $s['plan']['n'], round($s['plan']['n'] / $all * 100) . ' %', $dur($s['plan']['median_min'])],
            ['Premier trade', $s['trade']['n'], round($s['trade']['n'] / $all * 100) . ' %', $dur($s['trade']['median_min'])]]);
    $sk = ['before' => 'Avant l\'ouverture (18 h → 9 h 30)', 'session' => 'Séance (9 h 30 → 16 h)', 'evening' => 'Soir (16 h → 18 h)', 'weekend' => 'Fin de semaine (vendredi 17 h → dimanche 18 h)'];
    $md .= "**Quand ils s'inscrivent** (heure de New York) et la part qui fait un premier plan ou un premier trade pendant cette séance :\n\n"
        . $tbl(['Moment', 'Inscrits', 'Premier plan ou trade ce jour-là'], array_map(fn($k) => [$sk[$k], $b['signup_slots'][$k]['n'], $pc(['pct' => $b['signup_slots'][$k]['day0_pct']])], array_keys($sk)))
        . $tbl(['Indicateur', 'Valeur'], [['De retour le jour de trading suivant (visite, plan ou trade)', $pc($b['return_d1'])], ['Risque permis vu le jour de l\'inscription (premier plan ou trade)', $pc($b['risk_seen_day0'])]]);
    if (!empty($m['journal'])) {   // brief « pertes oubliées », step 1
        $j = $m['journal']; $jr = fn(string $k, string $l) => [$l, $pc($j['d7'][$k]), $pc($j['d30'][$k])];
        $md .= "**Journal complet** (des pertes non notées rendent le journal trop beau ; chez de vrais traders, 40 à 55 % des trades sont perdants) :\n\n"
            . $tbl(['Indicateur', '7 jours', '30 jours'], [$jr('high_win_20', 'Traders de 20 trades et plus avec plus de 80 % de gagnants'), $jr('losing_trades', 'Trades perdants'), $jr('days_without_loss', 'Jours de trading sans perte')]);
    }

    $md .= "## 3. D'où viennent les traders\n\n**Inscriptions par semaine** (lundi, New York) :\n\n" . $tbl(['Semaine', 'Inscrits'], array_map(null, array_keys($b['filters']['weeks']), array_values($b['filters']['weeks'])))
        . "**« Où as-tu trouvé Sweep ? »** (tous) :\n\n" . $tbl(['Réponse', 'Inscrits'], array_map(null, array_keys($b['filters']['sources']), array_values($b['filters']['sources'])))
        . "**Campagne ou source du lien** (30 j) :\n\n" . $tbl(['Source', 'Inscrits'], array_map(null, array_keys($m['signups']['by_source_30d']), array_values($m['signups']['by_source_30d'])));
    $byVia = [];   // the start, per answer: where each source stops
    foreach (array_keys($b['filters']['sources']) as $v) {
        $x = sweep_metrics($pdo, $app, ['source' => (string) $v])['brief']; $n = max(1, (int) $x['start']['signed_up']);
        $byVia[] = [$v, $x['start']['signed_up'], round($x['start']['account']['n'] / $n * 100) . ' %', round($x['start']['trade']['n'] / $n * 100) . ' %', $pc($x['activation_day0']), $pc($x['retention_d7'])];
    }
    $md .= "**Par réponse, jusqu'où ils vont** :\n\n" . $tbl(['Réponse', 'Inscrits', '1er compte', '1er trade', 'Activation jour 0', 'Rétention J7'], $byVia);
    $lead = $try(function () use ($q, $has) { if (!$has('signup_leads')) return null; return $q('SELECT SUM(completed_at IS NULL) u, SUM(completed_at IS NOT NULL) d, SUM(completed_at IS NULL AND created_at > ?) u30 FROM signup_leads', [time() - 30 * 86400])->fetch(PDO::FETCH_ASSOC); }, null);
    if ($lead) $md .= "**Inscriptions commencées (courriel et mot de passe) mais pas finies** : " . (int) $lead['u'] . ' (' . (int) $lead['u30'] . ' en 30 j) ; finies : ' . (int) $lead['d'] . ".\n\n";

    $u = sweep_usage_summary($pdo, $now, $real);
    $md .= "## 4. Comment l'app est utilisée (30 j)\n\n" . ($u['traders'] ? $u['traders'] . " traders mesurés (la mesure existe depuis le 27 oct.). Pages = `p:`, feuilles et fenêtres = `s:`. Part = traders qui l'ont ouvert, sur les traders mesurés. Minutes : temps à l'écran, total et médiane par trader et par jour où il l'a ouvert.\n\n" : "_Pas encore de mesure (elle existe depuis le 27 oct.)._\n\n")
        . $tbl(['Page ou feuille', 'Traders', 'Part', 'Ouvertures', 'Téléphone / ordi', 'Minutes', 'Médiane min/jour'], array_map(fn($k, $x) => [$k, $x['traders'], $x['pct'] . ' %', $x['opens'], $x['phone'] . ' / ' . $x['desktop'], $x['minutes'], $x['median_min_day']], array_keys($u['keys']), $u['keys']))
        . "**Appareils (30 j, traders)** : " . (implode(' · ', array_map(fn($k, $v) => "$k $v", array_keys($u['devices_30d']), $u['devices_30d'])) ?: '—')
        . "\n\n**Dernier appareil, langue, thème de chaque trader** : " . (implode(' · ', array_map(fn($k, $v) => "$k $v", array_keys($u['env']['device']), $u['env']['device'])) ?: '—') . ' ; '
        . (implode(' · ', array_map(fn($k, $v) => "$k $v", array_keys($u['env']['lang']), $u['env']['lang'])) ?: '—') . ' ; ' . (implode(' · ', array_map(fn($k, $v) => "$k $v", array_keys($u['env']['theme']), $u['env']['theme'])) ?: '—') . "\n\n";

    $md .= "## 5. Saisie des trades (30 j)\n\n" . $tbl(['Façon', 'Trades'], array_map(null, array_keys($m['trade_methods_30d']), array_values($m['trade_methods_30d'])));
    $md .= "## 6. Recherches sans résultat (30 j)\n\n" . $tbl(['Recherche (langue)', 'Fois'], array_map(null, array_keys($m['search_misses_30d']), array_values($m['search_misses_30d'])));

    if ($g = $m['game']) {
        $gr = fn(array $o) => array_map(fn($k, $v) => [$k, $v['pct'] . ' %', $v['n']], array_keys($o), $o);
        $md .= "## 7. Le jeu (30 j)\n\nSur les " . $g['active_30d'] . " traders actifs (un trade, un plan ou une revue en 30 jours).\n\n**Utilisé (une action du trader)** :\n\n" . $tbl(['Fonction', 'Part', 'Traders'], $gr($g['used']))
            . "**Atteint (en tenant son journal)** :\n\n" . $tbl(['Fonction', 'Part', 'Traders'], $gr($g['reached']));
    }

    $sy = $try(function () use ($q, $has, $real) {
        if (!$has('sync_connections')) return null;
        $o = [];
        foreach ($q('SELECT user_id, platform, status, last_push_at FROM sync_connections WHERE revoked_at IS NULL') as $r) { if (!isset($real[$r['user_id']])) continue; $x = &$o[$r['platform']]; $x ??= ['t' => [], 'p7' => []]; $x['t'][$r['user_id']] = 1; if ((int) $r['last_push_at'] > time() - 7 * 86400) $x['p7'][$r['user_id']] = 1; unset($x); }
        $acc = []; foreach ($q('SELECT user_id, platform, state FROM sync_accounts') as $r) if (isset($real[$r['user_id']])) $acc[$r['platform']][$r['state']] = ($acc[$r['platform']][$r['state']] ?? 0) + 1;
        $tr = []; foreach ($q('SELECT t.user_id, a.platform, t.created_at FROM sync_trades t JOIN sync_accounts a ON a.id = t.sync_account_id') as $r) if (isset($real[$r['user_id']])) { $tr[$r['platform']][0] = ($tr[$r['platform']][0] ?? 0) + 1; if ((int) $r['created_at'] > time() - 7 * 86400) $tr[$r['platform']][1] = ($tr[$r['platform']][1] ?? 0) + 1; }
        $rows = []; foreach (array_unique(array_merge(array_keys($o), array_keys($acc))) as $p) $rows[] = [$p, count($o[$p]['t'] ?? []), count($o[$p]['p7'] ?? []), json_encode($acc[$p] ?? []), (int) ($tr[$p][0] ?? 0) . ' / ' . (int) ($tr[$p][1] ?? 0)];
        return $rows;
    });
    if ($sy !== null) $md .= "## 8. Synchronisation automatique\n\n" . $tbl(['Plateforme', 'Traders connectés', 'Envoi en 7 j', 'Comptes trouvés', 'Trades écrits (total / 7 j)'], $sy);

    $ai = $try(fn() => $q('SELECT SUBSTR(created_at, 1, 10) AS day, COUNT(*) AS calls, COUNT(DISTINCT user_id) AS users, ROUND(SUM(cost_usd), 4) AS usd FROM ai_log GROUP BY day ORDER BY day DESC LIMIT 14')->fetchAll(PDO::FETCH_NUM), []);
    $md .= "## 9. Sweep AI (14 derniers jours)\n\n" . $tbl(['Jour (UTC)', 'Appels', 'Traders', 'Coût $'], $ai);

    $h = sweep_health($pdo, $cfg, $app); $c = $h['config'];
    $yn = fn($v) => $v ? 'oui' : 'NON';
    $md .= "## 10. Santé\n\n**Services** : courriel SMTP " . $yn($c['smtp']) . ' · code par courriel ' . $yn($c['twofa']) . ' · Sweep AI ' . $yn($c['ai']) . (isset($c['ai_spent_usd']) ? ' ($' . $c['ai_spent_usd'] . ' sur ' . $c['ai_budget_usd'] . ' aujourd\'hui)' : '')
        . ' · Stripe ' . $yn($c['billing']) . ($c['billing'] ? ($c['billing_live'] ? ' (réel)' : ' (test)') : '') . ' · webhook ' . $yn($c['webhook']) . ' · graphiques ' . $yn($c['chart']) . ' · calendrier économique ' . $yn($c['econ']) . ' (' . ($c['econ_n'] ?? 0) . ' annonces fortes en 14 j)'
        . ' · notifications ' . $yn($c['push']) . ' · sauvegarde ' . $yn($c['backup']) . ' · copie hors serveur ' . $yn($c['offsite']) . "\n\n**Tâches planifiées** :\n\n"
        . $tbl(['Tâche', 'Quand', 'État', 'Dernière fin', 'Durée', 'Dernière réussite', 'Erreur ou note'], array_map(fn($t) => [$t['task'], $t['schedule'], $t['color'] . ' · ' . $t['state'], $at($t['finished_at']), $t['duration_ms'] !== null ? round($t['duration_ms'] / 1000, 1) . ' s' : '—', $at($t['last_ok_at']), sweep_report_redact((string) ($t['error'] ?: $t['note'] ?: ''))], $h['tasks']));

    $pr = $try(function () use ($app) { require_once $app . '/presets/check.php'; return pr_admin_summary(); });
    if ($pr) $md .= "## 11. Préréglages des prop firms\n\nCatalogue v" . $pr['version'] . ', dernière vérification complète : ' . ($pr['last_run'] ? $at($pr['last_run']) . ' (il y a ' . $pr['days_since'] . ' j)' : 'jamais') . ($pr['stale'] ? ' — **en retard**' : '') . ".\n\n"
        . $tbl(['Firme', 'Programmes', 'État', 'Vérifiée', 'Changements trouvés', 'Erreurs'], array_map(fn($f) => [$f['name'], $f['programs'], $f['status'], $at($f['checked_at']), implode(' ; ', $f['changes']), implode(' ; ', $f['errors'])], $pr['firms']));

    $fb = $try(fn() => $q('SELECT user_id, type, rating, message, page, status, created_at FROM feedback ORDER BY created_at DESC LIMIT 40')->fetchAll(PDO::FETCH_ASSOC), []);
    $fb = array_values(array_filter($fb, fn($r) => isset($real[$r['user_id']])));
    $md .= "## 12. Avis des traders (40 derniers)\n\nCourriels, liens et numéros retirés des textes.\n\n" . $tbl(['Date', 'Type', 'Note', 'Page', 'État', 'Texte'], array_map(fn($r) => [$at($r['created_at']), $r['type'], $r['rating'] ?? '—', $r['page'] ?: '—', $r['status'], mb_substr(sweep_report_redact((string) $r['message']), 0, 600)], $fb));

    sweep_errors_schema($pdo);
    $eg = sweep_err_groups($pdo, $now);
    $md .= "## 13. Erreurs JS chez les traders (30 j)\n\n" . ($eg ? '' : "Aucune erreur en 30 jours.\n\n");
    foreach ($eg as $i => $e) $md .= str_replace("\n## ", "\n### ", "\n" . sweep_err_block($e, $i + 1));
    return $md;
}
