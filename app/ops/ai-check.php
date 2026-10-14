<?php
declare(strict_types=1);
/**
 * Sweep — « Ask Sweep » with the real key, 20 typical questions of traders (brief 02 part 9, « Vérifier »), on the server:
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/ai-check.php <username> [fr|en|es]
 * Use a Pro or Elite test account (its plan's AI allowance is used: 20 questions ≈ $0.02; Free has 3 a day). For each
 * question: the time to answer, the answer, the screen it offers, the data it says it used (« based on N trades… », counted
 * by Sweep), and what a good answer must contain — to grade each one (0 wrong, 1 partly, 2 right; ops/PROD-CHECK.md,
 * « Sweep AI »). Never prints a key.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root = dirname(__DIR__);
$cfg = require $root . '/config.php';
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
$c = $cfg['db'] ?? [];
$opts = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC];
$pdo = ($c['driver'] ?? 'sqlite') === 'mysql'
    ? new PDO('mysql:host=' . $c['host'] . ';dbname=' . $c['name'] . ';charset=utf8mb4', (string) $c['user'], (string) $c['password'], $opts)
    : new PDO('sqlite:' . $DATA . '/journal.db', null, null, $opts);
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool {
    static $on = null; if ($on !== null) return $on;
    global $cfg, $root;
    if (!empty($cfg['billing_config']) && !defined('SWEEP_BILLING_CONFIG')) define('SWEEP_BILLING_CONFIG', (string) $cfg['billing_config']);
    if (!is_file($root . '/billing/billing-core.php')) return $on = false;
    require_once $root . '/billing/billing-core.php';
    try { sb_config(); return $on = true; } catch (Throwable $e) { return $on = false; }
}
if (!empty($cfg['ai_config']) && !defined('SWEEP_AI_CONFIG')) define('SWEEP_AI_CONFIG', (string) $cfg['ai_config']);
require_once $root . '/ai/chat.php';

$user = (string) ($argv[1] ?? ''); $lang = in_array($argv[2] ?? 'fr', ['fr', 'en', 'es'], true) ? ($argv[2] ?? 'fr') : 'fr';
$uid = $user !== '' ? (string) $pdo->query('SELECT id FROM users WHERE username = ' . $pdo->quote($user))->fetchColumn() : '';
if ($uid === '') { fwrite(STDERR, "usage: php ops/ai-check.php <username of a test account> [fr|en|es]\n"); exit(2); }
$ai = sai_config();
echo "Sweep AI: " . ($ai['enabled'] ? 'on' : 'OFF') . " · model " . $ai['model'] . " · budget of the day $" . number_format((float) $ai['global_daily_budget_usd'], 2) . " · spent so far $" . number_format(sai_spent_today($pdo), 4) . "\n\n";

// [question fr, en, es, what a good answer has]
$Q = [
    ['Comment ajouter un payout ?', 'How do I add a payout?', '¿Cómo añado un payout?', 'Mon argent › « + Ajouter un payout » (ou « Enregistrer ma demande » sur la page du compte) ; écran : payouts'],
    ['Pourquoi mon compte est rouge ?', 'Why is my account red?', '¿Por qué mi cuenta está en rojo?', 'perte max / limite du jour de la firme ; écran : comptes ; pas de chiffre inventé'],
    ['Quelles sont mes pires heures ?', 'What are my worst hours?', '¿Cuáles son mis peores horas?', 'une heure précise (calculée), « d’après N trades »'],
    ['Combien j’ai gagné ce mois-ci ?', 'How much did I make this month?', '¿Cuánto gané este mes?', 'le net du mois, « d’après N trades du … au … »'],
    ['Quel est mon meilleur setup ?', 'What is my best setup?', '¿Cuál es mi mejor setup?', 'un setup nommé (calculé), « d’après N trades »'],
    ['Comment importer mes trades de Tradovate ?', 'How do I import my Tradovate trades?', '¿Cómo importo mis operaciones de Tradovate?', 'Import › CSV (Tradovate) ; écran : import'],
    ['Comment connecter NinjaTrader ?', 'How do I connect NinjaTrader?', '¿Cómo conecto NinjaTrader?', 'Réglages › Données › Connexions (synchro automatique)'],
    ['Est-ce que je trade mieux le matin ou l’après-midi ?', 'Do I trade better in the morning or the afternoon?', '¿Opero mejor por la mañana o por la tarde?', 'les deux sessions comparées (calculées), « d’après N trades »'],
    ['Combien de trades j’ai pris cette semaine ?', 'How many trades did I take this week?', '¿Cuántas operaciones hice esta semana?', 'un nombre, « d’après … » les 7 derniers jours'],
    ['Comment fonctionne le copy trading ?', 'How does copy trading work?', '¿Cómo funciona el copy trading?', 'copier un trade sur ses comptes, « Copier sur mon groupe », taille des copies par compte'],
    ['Quand est-ce que je peux demander un payout ?', 'When can I request a payout?', '¿Cuándo puedo pedir un payout?', 'le compteur « Prêt pour un payout » de la page du compte, ce qui manque ; écran : comptes'],
    ['Quelle est ma série actuelle ?', 'What is my current streak?', '¿Cuál es mi racha actual?', 'pas de chiffre inventé (ses données ne l’ont pas) : la Progression le montre'],
    ['Comment changer la langue ?', 'How do I change the language?', '¿Cómo cambio el idioma?', 'Réglages › Langue ; écran : réglages'],
    ['Explique-moi le profit factor', 'Explain the profit factor', 'Explícame el profit factor', 'profit brut ÷ perte brute, au-dessus de 1 = rentable ; sans conseil'],
    ['Pourquoi mon R est indisponible ?', 'Why is my R unavailable?', '¿Por qué mi R no está disponible?', 'il manque le stop (ou le risque) sur le trade'],
    ['Combien me coûtent les frais ?', 'How much do fees cost me?', '¿Cuánto me cuestan las comisiones?', 'le total des frais, « d’après N trades »'],
    ['Est-ce que le NQ va monter demain ?', 'Will NQ go up tomorrow?', '¿El NQ va a subir mañana?', 'refuse de prédire, gentiment ; pas de conseil'],
    ['Quelles annonces économiques aujourd’hui ?', 'Which economic releases today?', '¿Qué noticias económicas hay hoy?', 'les annonces du jour (ou aucune), heures ET ; écran : nouvelles'],
    ['Comment exporter toutes mes données ?', 'How do I export all my data?', '¿Cómo exporto todos mis datos?', 'Réglages › Données › Exporter (ZIP)'],
    ['Mon taux de réussite quand je suis en FOMO ?', 'My win rate when I feel FOMO?', '¿Mi tasa de acierto cuando siento FOMO?', 'un taux calculé ou « pas de données », « d’après N trades » ; pas de chiffre inventé'],
];
$left = sai_usage($pdo, $uid)['remaining'];
if ($left !== null && $left < count($Q)) { fwrite(STDERR, "$user has $left AI actions left today, " . count($Q) . " needed: use a Pro or Elite test account (Free: 3 a day), or run it tomorrow.\n"); exit(2); }
$col = ['fr' => 0, 'en' => 1, 'es' => 2][$lang];
$times = []; $errs = 0; $spent0 = sai_spent_today($pdo);
foreach ($Q as $i => $q) {
    if ($i) sleep(max(0, (int) $ai['min_seconds_between_calls']) + 1);   // the pause Sweep AI keeps between two questions
    $t0 = microtime(true);
    try { $r = sweep_chat($pdo, $uid, ['message' => $q[$col], 'history' => []], $lang); $err = null; }
    catch (SaiError $e) { $r = null; $err = $e->sai . ' (' . $e->http . ')'; $errs++; }
    $ms = (int) round((microtime(true) - $t0) * 1000); $times[] = $ms;
    $b = $r['basis'] ?? null;
    printf("%2d. %s\n    %d ms%s\n", $i + 1, $q[$col], $ms, $err ? ' · ERROR ' . $err : '');
    if ($r) {
        echo '    ' . str_replace("\n", "\n    ", wordwrap((string) $r['reply'], 110)) . "\n";
        echo '    screen: ' . ($r['action'] ?? '—') . ' · data: ' . ($b ? $b['trades'] . ' trades, ' . $b['from'] . ' → ' . $b['to'] : '—') . "\n";
    }
    echo "    a good answer: {$q[3]}\n    grade (0/1/2): __\n\n";
}
sort($times);
printf("%d questions · %d errors · median %d ms · slowest %d ms · cost $%.4f · AI left today for this trader: %s\n", count($Q), $errs, $times[intdiv(count($times), 2)], end($times), sai_spent_today($pdo) - $spent0,
    json_encode(sai_usage($pdo, $uid)));
