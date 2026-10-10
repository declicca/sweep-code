<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the « Your week » email (brief 01 step 5, lot 3), sent by game/cron.php (every 15 minutes):
 *  - from 17:30 ET on the week's last trading day (Friday, or Thursday when Friday is a market holiday) until Sunday 23:59 ET;
 *  - only when the recap is ready (GameV2b::openWeek: at least one trade in the week) and was not opened in the app;
 *  - once per week (table weekly_emails, written before sending: never twice, even when two cron runs overlap);
 *  - never to a trader who stopped it (link at the bottom of the email → api/email/weekly, no sign-in needed).
 * The numbers are the recap's first screen, computed like weekBrief() in src/game.js (tests/e2e_weekly_parity.py):
 * swept-day streak, discipline score, swept days out of days traded, best habit, one point to work on, payouts received.
 * No P&L: no simulated amount shown as money earned.
 */
final class GameWeeklyMail
{
    /** tests: replaces sweep_mail(to, subject, text, html, headers) */
    public static $mailer = null;

    /** the default checklist (DEFAULT_QS in src/app.js) and its words in FR / ES (assets/i18n-fr.js, i18n-es.js) */
    private const QS = [
        'plan' => 'Was this trade part of my trading plan?', 'confirm' => 'Did I wait for confirmation?', 'entry' => 'Was my entry valid?',
        'size' => 'Did I respect my maximum position size?', 'risk' => 'Did I define my risk before entering?', 'stop' => 'Did I respect my stop?',
        'widen' => 'Did I avoid moving my stop to increase risk?', 'addloser' => 'Did I avoid adding to a losing trade?', 'revenge' => 'Did I avoid revenge trading?',
        'chase' => 'Did I avoid chasing price?', 'dll' => 'Did I respect my daily loss limit?', 'emotion' => 'Was my emotional state appropriate for trading?',
        'exit' => 'Did I follow my exit plan?',
    ];
    private const QS_TR = [
        'Was this trade part of my trading plan?' => ['fr' => 'Ce trade faisait-il partie de mon plan de trading ?', 'es' => '¿Esta operación formaba parte de mi plan?'],
        'Did I wait for confirmation?' => ['fr' => 'Ai-je attendu la confirmation ?', 'es' => '¿Esperé la confirmación?'],
        'Was my entry valid?' => ['fr' => 'Mon entrée était-elle valide ?', 'es' => '¿Mi entrada era válida?'],
        'Did I respect my maximum position size?' => ['fr' => 'Ai-je respecté ma taille de position maximale ?', 'es' => '¿Respeté mi tamaño máximo de posición?'],
        'Did I define my risk before entering?' => ['fr' => 'Ai-je défini mon risque avant d\'entrer ?', 'es' => '¿Definí mi riesgo antes de entrar?'],
        'Did I respect my stop?' => ['fr' => 'Ai-je respecté mon stop ?', 'es' => '¿Respeté mi stop?'],
        'Did I avoid moving my stop to increase risk?' => ['fr' => 'Ai-je évité de déplacer mon stop pour augmenter le risque ?', 'es' => '¿Evité mover mi stop para aumentar el riesgo?'],
        'Did I avoid adding to a losing trade?' => ['fr' => 'Ai-je évité d\'ajouter à un trade perdant ?', 'es' => '¿Evité aumentar una operación perdedora?'],
        'Did I avoid revenge trading?' => ['fr' => 'Ai-je évité le revenge trading ?', 'es' => '¿Evité el revenge trading?'],
        'Did I avoid chasing price?' => ['fr' => 'Ai-je évité de courir après le prix ?', 'es' => '¿Evité perseguir el precio?'],
        'Did I respect my daily loss limit?' => ['fr' => 'Ai-je respecté ma limite de perte quotidienne ?', 'es' => '¿Respeté mi límite de pérdida diaria?'],
        'Was my emotional state appropriate for trading?' => ['fr' => 'Mon état émotionnel était-il approprié pour trader ?', 'es' => '¿Mi estado emocional era adecuado para operar?'],
        'Did I follow my exit plan?' => ['fr' => 'Ai-je suivi mon plan de sortie ?', 'es' => '¿Seguí mi plan de salida?'],
    ];
    /** the recap's words (WQ in src/game.js) + the email's own */
    private const W = [
        'en' => ['s' => 'Your week: {range}', 'hi' => 'Hi {first},', 'p1' => 'Your week is ready. Here is what it says.',
            'streak' => 'Swept-day streak', 'streak_1' => '{n} day in a row', 'streak_v' => '{n} days in a row', 'disc' => 'Discipline this week',
            'swept' => 'Swept days', 'swept_v' => '{a} of {b} days traded', 'habit' => 'Your best habit', 'habit_v' => '« {q} » — yes {y} times out of {n}',
            'work' => 'For next week', 'work_v' => 'Aim for a « yes » to « {q} » on every trade.', 'pay' => 'Payouts received this week',
            'nodisc' => 'Answer the checklist on your trades to get a discipline score.', 'btn' => 'See my week', 'colon' => ': ',
            'why' => 'You get this email because you traded this week with Sweep.', 'off' => 'Stop the weekly email',
            'help' => 'A question? Reply to this email or write to', 'sig' => 'The Sweep team',
            'pg_on_t' => 'Your week by email', 'pg_on_p' => 'Sweep sends you your week on Friday after the close, when you traded that week.', 'pg_on_b' => 'Stop the weekly email',
            'pg_off_t' => 'Done', 'pg_off_p' => 'You will no longer get your week by email. It stays in the app every Friday.', 'pg_off_b' => 'Get it again',
            'pg_bad' => 'This link is no longer valid.'],
        'fr' => ['s' => 'Ta semaine du {range}', 'hi' => 'Salut {first},', 'p1' => 'Ta semaine est prête. Voici ce qu’elle dit.',
            'streak' => 'Streak de journées balayées', 'streak_1' => '{n} jour d’affilée', 'streak_v' => '{n} jours d’affilée', 'disc' => 'Discipline de la semaine',
            'swept' => 'Journées balayées', 'swept_v' => '{a} sur {b} jours tradés', 'habit' => 'Ta meilleure habitude', 'habit_v' => '« {q} » — oui {y} fois sur {n}',
            'work' => 'Pour la semaine prochaine', 'work_v' => 'Vise un « oui » à « {q} » sur chaque trade.', 'pay' => 'Payouts reçus cette semaine',
            'nodisc' => 'Réponds à la checklist de tes trades pour avoir un score de discipline.', 'btn' => 'Voir mon bilan', 'colon' => "\u{00A0}: ",
            'why' => 'Tu reçois ce courriel parce que tu as tradé cette semaine avec Sweep.', 'off' => 'Ne plus recevoir le bilan par courriel',
            'help' => 'Une question ? Réponds à ce courriel ou écris à', 'sig' => 'L’équipe Sweep',
            'pg_on_t' => 'Ta semaine par courriel', 'pg_on_p' => 'Sweep t’envoie ta semaine le vendredi après la clôture, quand tu as tradé dans la semaine.', 'pg_on_b' => 'Ne plus la recevoir',
            'pg_off_t' => 'C’est fait', 'pg_off_p' => 'Tu ne recevras plus ta semaine par courriel. Elle reste dans l’app, chaque vendredi.', 'pg_off_b' => 'La recevoir à nouveau',
            'pg_bad' => 'Ce lien n’est plus valide.'],
        'es' => ['s' => 'Tu semana del {range}', 'hi' => 'Hola {first},', 'p1' => 'Tu semana está lista. Esto es lo que dice.',
            'streak' => 'Racha de días barridos', 'streak_1' => '{n} día seguido', 'streak_v' => '{n} días seguidos', 'disc' => 'Disciplina de la semana',
            'swept' => 'Días barridos', 'swept_v' => '{a} de {b} días operados', 'habit' => 'Tu mejor hábito', 'habit_v' => '« {q} » — sí {y} veces de {n}',
            'work' => 'Para la próxima semana', 'work_v' => 'Apunta a un « sí » en « {q} » en cada operación.', 'pay' => 'Payouts recibidos esta semana',
            'nodisc' => 'Responde la checklist de tus operaciones para tener un puntaje de disciplina.', 'btn' => 'Ver mi semana', 'colon' => ': ',
            'why' => 'Recibes este correo porque operaste esta semana con Sweep.', 'off' => 'No recibir más el resumen por correo',
            'help' => '¿Una pregunta? Responde a este correo o escribe a', 'sig' => 'El equipo de Sweep',
            'pg_on_t' => 'Tu semana por correo', 'pg_on_p' => 'Sweep te envía tu semana el viernes después del cierre, cuando operaste esa semana.', 'pg_on_b' => 'No recibirla más',
            'pg_off_t' => 'Listo', 'pg_off_p' => 'Ya no recibirás tu semana por correo. Sigue en la app cada viernes.', 'pg_off_b' => 'Recibirla de nuevo',
            'pg_bad' => 'Este enlace ya no es válido.'],
    ];
    private const MONTHS = [
        'en' => ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'fr' => ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
        'es' => ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
    ];

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $pdo = GameEngine::pdo(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $T = $my ? 'VARCHAR(120)' : 'TEXT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
        $pdo->exec("CREATE TABLE IF NOT EXISTS weekly_emails (user_id $T NOT NULL, week_start VARCHAR(10) NOT NULL, sent_at INT NOT NULL, ok INT NOT NULL DEFAULT 0, PRIMARY KEY (user_id, week_start))$cs");
        $pdo->exec("CREATE TABLE IF NOT EXISTS email_prefs (user_id $T NOT NULL PRIMARY KEY, token VARCHAR(40) NOT NULL, weekly_off INT NOT NULL DEFAULT 0, updated_at INT NOT NULL)$cs");
        if ($my) { try { $pdo->exec('ALTER TABLE email_prefs ADD UNIQUE KEY uq_email_token (token)'); } catch (Throwable $e) { /* exists */ } }
        else $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS uq_email_token ON email_prefs (token)');
    }

    private static function docs(string $uid, string $col): array
    {
        $out = [];
        foreach (GameEngine::q('SELECT id, data FROM documents WHERE user_id = ? AND collection = ?', [$uid, $col])->fetchAll(PDO::FETCH_ASSOC) as $r) {
            $d = json_decode((string) $r['data'], true); if (is_array($d)) { $d['id'] = $d['id'] ?? $r['id']; $out[] = $d; }
        }
        return $out;
    }
    private static function lang($l): string { $l = strtolower(substr((string) $l, 0, 2)); return in_array($l, ['fr', 'es'], true) ? $l : 'en'; }

    /**
     * The recap's first screen for the week of $mon, the same numbers as weekBrief() in src/game.js: trades of Monday-Friday
     * (session date, example data left out), discipline = average of the trades' checklist scores (yes / (yes + no)), best habit
     * and point to work on among the questions answered twice or more, payouts paid Monday-Sunday (real money).
     */
    public static function brief(string $uid, string $mon, string $lang = 'en'): array
    {
        $fri = GameEngine::addDays($mon, 4); $sun = GameEngine::addDays($mon, 6);
        $in = fn($d, string $a, string $b) => is_string($d) && $d !== '' && strcmp($d, $a) >= 0 && strcmp($d, $b) <= 0;
        $tr = array_values(array_filter(self::docs($uid, 'trades'), fn($t) => empty($t['demo']) && $in($t['date'] ?? null, $mon, $fri)));
        $traded = count(array_unique(array_map(fn($t) => (string) $t['date'], $tr)));
        $ds = []; $per = [];
        foreach ($tr as $t) {
            $y = 0; $n = 0;
            foreach ((array) ($t['discipline'] ?? []) as $k => $v) {
                if ($v !== 'y' && $v !== 'n') continue;
                $n++; if ($v === 'y') $y++;
                $k = (string) $k; $per[$k] = $per[$k] ?? ['y' => 0, 'n' => 0]; $per[$k][$v]++;
            }
            if ($n) $ds[] = $y / $n * 100;
        }
        $disc = $ds ? (int) floor(array_sum($ds) / count($ds) + 0.5) : null;   // Math.round
        $rows = [];
        foreach ($per as $k => $o) { $n = $o['y'] + $o['n']; if ($n >= 2) $rows[] = ['k' => (string) $k, 'y' => $o['y'], 'n' => $n, 'rate' => $o['y'] / $n]; }
        $best = $rows; usort($best, fn($a, $b) => ($b['rate'] <=> $a['rate']) ?: (($b['n'] <=> $a['n']) ?: strcmp($a['k'], $b['k']))); $best = $best[0] ?? null;
        $work = array_values(array_filter($rows, fn($r) => $r['y'] < $r['n']));
        usort($work, fn($a, $b) => ($a['rate'] <=> $b['rate']) ?: (($b['n'] <=> $a['n']) ?: strcmp($a['k'], $b['k']))); $work = $work[0] ?? null;
        $qs = null; foreach (self::docs($uid, 'meta') as $m) if (($m['id'] ?? '') === 'settings') $qs = (array) ($m['questions'] ?? []);
        $qText = function (string $k) use ($qs, $lang): string {
            $t = $k;
            if ($qs === null) $t = self::QS[$k] ?? $k;   // never saved: the app's default checklist
            else foreach ($qs as $q) if (is_array($q) && (string) ($q['id'] ?? '') === $k) { $t = (string) ($q['text'] ?? ''); break; }
            return self::QS_TR[$t][$lang] ?? $t;
        };
        $pay = 0;
        foreach (self::docs($uid, 'payouts') as $p) {
            if (($p['status'] ?? '') !== 'paid') continue;
            $d = ($p['paid_on'] ?? '') ?: (($p['payment_date'] ?? '') ?: (($p['approval_date'] ?? '') ?: ($p['request_date'] ?? '')));
            if ($in($d, $mon, $sun)) $pay += isset($p['net_c']) ? (int) $p['net_c'] : (int) ($p['amount_c'] ?? 0);
        }
        $sm = GameV2b::weekSummary($uid, $mon); $sw = (int) $sm['swept'];
        return ['week' => $mon, 'traded' => $traded, 'swept' => min($sw, $traded ?: $sw), 'streak' => (int) $sm['streak'], 'disc' => $disc,
            'best' => $best ? ['q' => $qText($best['k']), 'y' => $best['y'], 'n' => $best['n']] : null,
            'work' => $work && (!$best || $work['k'] !== $best['k']) ? ['q' => $qText($work['k'])] : null, 'payouts' => $pay];
    }

    /** the trader's token for the link at the bottom of the email, and whether the email is stopped */
    private static function prefs(string $uid): array
    {
        self::schema();
        $r = GameEngine::q('SELECT token, weekly_off FROM email_prefs WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        if ($r) return ['token' => (string) $r['token'], 'off' => (int) $r['weekly_off'] === 1];
        $t = bin2hex(random_bytes(16));
        GameEngine::q('INSERT INTO email_prefs (user_id, token, weekly_off, updated_at) VALUES (?, ?, 0, ?)', [$uid, $t, time()]);
        return ['token' => $t, 'off' => false];
    }
    private static function base(): string
    {
        $u = rtrim((string) (($GLOBALS['cfg'] ?? [])['app_url'] ?? ''), '/');
        return ($u !== '' ? $u : 'https://app.makeitsweep.com') . '/';
    }

    /** cron: send this week's email if it is time, once. True when an email was sent. */
    public static function run(string $uid): bool
    {
        $mon = GameV2b::openWeek($uid); if ($mon === null) return false;   // no recap (yet), or no trade this week
        $now = (new DateTimeImmutable('@' . GameEngine::ts()))->setTimezone(new DateTimeZone('America/New_York'));
        $last = $mon; for ($i = 4; $i >= 0; $i--) { $d = GameEngine::addDays($mon, $i); if (GameEngine::isMarketDay($d)) { $last = $d; break; } }
        if ($now->format('Y-m-d') === $last && $now->format('H:i') < '17:30') return false;   // 17:30 ET on the week's last trading day
        if (GameV2b::seen($uid, $mon)) return false;   // already opened in the app
        self::schema();
        if (GameEngine::q('SELECT 1 FROM weekly_emails WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetchColumn()) return false;
        $u = GameEngine::q('SELECT * FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        $to = trim((string) ($u['email'] ?? ''));
        if (!$u || !empty($u['disabled']) || !filter_var($to, FILTER_VALIDATE_EMAIL)) return false;
        $pref = self::prefs($uid); if ($pref['off']) return false;
        try { GameEngine::q('INSERT INTO weekly_emails (user_id, week_start, sent_at, ok) VALUES (?, ?, ?, 0)', [$uid, $mon, time()]); }
        catch (Throwable $e) { return false; }   // another run is sending it
        $lang = self::lang($u['lang'] ?? 'en');
        $off = self::base() . 'api/email/weekly?t=' . $pref['token'];
        [$subject, $text, $html] = self::compose(self::brief($uid, $mon, $lang), $lang, trim((string) ($u['first_name'] ?? '')) ?: (string) ($u['username'] ?? ''), $mon, $last, $off);
        $send = self::$mailer ?? (function_exists('sweep_mail') ? 'sweep_mail' : null);
        $ok = $send !== null && (bool) $send($to, $subject, $text, $html, ['List-Unsubscribe' => '<' . $off . '>', 'List-Unsubscribe-Post' => 'List-Unsubscribe=One-Click']);
        if ($ok) GameEngine::q('UPDATE weekly_emails SET ok = 1 WHERE user_id = ? AND week_start = ?', [$uid, $mon]);
        else error_log('[Sweep weekly email] not sent: ' . $uid . ' ' . $mon);
        return $ok;
    }

    /** « October 5–9 » · « 5 au 9 octobre » · « 5 al 9 de octubre » */
    private static function range(string $a, string $b, string $lang): string
    {
        $M = self::MONTHS[$lang]; $da = (int) substr($a, 8, 2); $db = (int) substr($b, 8, 2); $ma = (int) substr($a, 5, 2) - 1; $mb = (int) substr($b, 5, 2) - 1;
        $fa = $lang === 'fr' && $da === 1 ? '1er' : (string) $da; $fb = $lang === 'fr' && $db === 1 ? '1er' : (string) $db;
        if ($lang === 'fr') return $ma === $mb ? "$fa au $fb {$M[$mb]}" : "$fa {$M[$ma]} au $fb {$M[$mb]}";
        if ($lang === 'es') return $ma === $mb ? "$da al $db de {$M[$mb]}" : "$da de {$M[$ma]} al $db de {$M[$mb]}";
        return $ma === $mb ? "{$M[$mb]} {$da}–{$db}" : "{$M[$ma]} {$da} – {$M[$mb]} {$db}";
    }
    /** the app's money format: $1,200 · 1 200 $ · 1.200 $ (cents only when there are some) */
    private static function money(int $c, string $lang): string
    {
        $v = abs($c) / 100; $dec = $c % 100 ? 2 : 0; $sign = $c < 0 ? '−' : '';
        if ($lang === 'en') return $sign . '$' . number_format($v, $dec, '.', ',');
        return $sign . number_format($v, $dec, ',', $lang === 'fr' ? "\u{202F}" : '.') . "\u{00A0}$";
    }

    /** [subject, text, html] */
    public static function compose(array $b, string $lang, string $first, string $mon, string $last, string $offUrl): array
    {
        $L = self::W[$lang] ?? self::W['en'];
        $f = fn(string $k, array $p = []) => strtr($L[$k], array_combine(array_map(fn($x) => '{' . $x . '}', array_keys($p)), array_map('strval', array_values($p))) ?: []);
        $rows = [[$L['streak'], $f($b['streak'] === 1 ? 'streak_1' : 'streak_v', ['n' => $b['streak']])],
                 [$L['disc'], $b['disc'] !== null ? $b['disc'] . "\u{202F}%" : '—'],
                 [$L['swept'], $f('swept_v', ['a' => $b['swept'], 'b' => $b['traded']])]];
        $notes = [];
        if ($b['best']) $notes[] = [$L['habit'], $f('habit_v', ['q' => $b['best']['q'], 'y' => $b['best']['y'], 'n' => $b['best']['n']])];
        elseif ($b['disc'] === null) $notes[] = ['', $L['nodisc']];
        if ($b['work']) $notes[] = [$L['work'], $f('work_v', ['q' => $b['work']['q']])];
        if ($b['payouts'] > 0) $notes[] = [$L['pay'], self::money((int) $b['payouts'], $lang)];
        $range = self::range($mon, $last, $lang); $app = self::base() . '#dashboard';
        $sup = trim((string) (($GLOBALS['cfg'] ?? [])['support_email'] ?? '')) ?: 'hello@makeitsweep.com';
        $subject = $f('s', ['range' => $range]);
        $hi = $f('hi', ['first' => $first !== '' ? $first : 'trader']);
        $line = fn(array $r) => ($r[0] !== '' ? $r[0] . $L['colon'] : '') . $r[1];
        $text = $hi . "\n\n" . $L['p1'] . "\n\n" . implode("\n", array_map($line, array_merge($rows, $notes))) . "\n\n"
            . $L['btn'] . $L['colon'] . $app . "\n\n" . $L['why'] . "\n" . $L['off'] . $L['colon'] . $offUrl . "\n\n" . $L['help'] . ' ' . $sup . "\n\n— " . $L['sig'];
        // French: no-break spaces inside « » and before ? : ! (a lone « » » or « ? » never starts a line)
        $nb = fn(string $x) => $lang === 'fr' ? str_replace(['« ', ' »', ' ?', ' :', ' !'], ["«\u{00A0}", "\u{00A0}»", "\u{00A0}?", "\u{00A0}:", "\u{00A0}!"], $x) : $x;
        $text = $nb($text);
        $h = fn($x) => htmlspecialchars($nb((string) $x), ENT_QUOTES, 'UTF-8');
        $tiles = '';
        foreach ($rows as $i => $r) $tiles .= '<tr><td style="padding:12px 0;' . ($i ? 'border-top:1px solid #2a2a30;' : '') . 'font-size:14px;color:#9a9aa2">' . $h($r[0]) . '</td>'
            . '<td align="right" style="padding:12px 0 12px 12px;' . ($i ? 'border-top:1px solid #2a2a30;' : '') . 'font-size:15px;font-weight:600;color:#f2f2f3;white-space:nowrap">' . $h($r[1]) . '</td></tr>';
        $list = '';
        foreach ($notes as $i => $r) $list .= '<tr><td style="padding:12px 0;' . ($i ? 'border-top:1px solid #2a2a30' : '') . '">' . ($r[0] !== '' ? '<div style="font-size:13px;font-weight:600;color:#f2f2f3;margin-bottom:4px">' . $h($r[0]) . '</div>' : '')
            . '<div style="font-size:14px;line-height:1.5;color:' . ($r[0] === $L['pay'] ? '#4c8dff' : '#b9b9c2') . '">' . $h($r[1]) . '</div></td></tr>';
        $html = '<!doctype html><html lang="' . $lang . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' . $h($subject) . '</title></head><body style="margin:0;background:#0b0b0c;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;color:#e9e9ee">'
            . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="100%" style="max-width:520px;background:#141416;border:1px solid #26262a;border-radius:20px" cellpadding="0" cellspacing="0"><tr><td style="padding:32px 28px 28px">'
            . '<div style="font-size:18px;font-weight:700;letter-spacing:-.01em;margin-bottom:24px">sweep</div>'
            . '<p style="margin:0 0 6px;font-size:16px">' . $h($hi) . '</p><p style="margin:0 0 20px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($L['p1']) . '</p>'
            . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#1c1c20;border-radius:14px;padding:4px 16px">' . $tiles . '</table>'
            . ($list !== '' ? '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:12px 0 0">' . $list . '</table>' : '')
            . '<div style="margin:24px 0 0"><a href="' . $h($app) . '" style="display:inline-block;background:#4c8dff;color:#0b0b0c;font-weight:600;font-size:15px;text-decoration:none;padding:13px 24px;border-radius:999px">' . $h($L['btn']) . '</a></div>'
            . '<p style="margin:24px 0 0;font-size:13px;color:#8a8a94">' . $h($L['help']) . ' <a href="mailto:' . $h($sup) . '" style="color:#4c8dff">' . $h($sup) . '</a></p>'
            . '</td></tr></table><p style="font-size:12px;line-height:1.5;color:#6c6c76;margin:16px 0 0;max-width:520px">' . $h($L['why']) . ' <a href="' . $h($offUrl) . '" style="color:#8a8a94">' . $h($L['off']) . '</a><br>' . $h($L['sig']) . ' · makeitsweep.com</p></td></tr></table></body></html>';
        return [$subject, $text, $html];
    }

    /** the link's token → user_id, weekly_off, lang; null when unknown */
    private static function byToken(string $token): ?array
    {
        if (!preg_match('/^[a-f0-9]{32}$/', $token)) return null;
        self::schema();
        return GameEngine::q('SELECT p.user_id, p.weekly_off, u.lang FROM email_prefs p LEFT JOIN users u ON u.id = p.user_id WHERE p.token = ?', [$token])->fetch(PDO::FETCH_ASSOC) ?: null;
    }
    /** stop (true) or start again (false) the email of the link's trader; false when the link is unknown */
    public static function setOff(string $token, bool $off): bool
    {
        if (!self::byToken($token)) return false;
        GameEngine::q('UPDATE email_prefs SET weekly_off = ?, updated_at = ? WHERE token = ?', [$off ? 1 : 0, time(), $token]);
        return true;
    }
    /** the trader's link token (created the first time) — tests and the email itself */
    public static function token(string $uid): string { return self::prefs($uid)['token']; }

    /**
     * api/email/weekly?t=<token> — the link at the bottom of the email, no sign-in: GET shows a page with one button, POST stops
     * the email (also the mail apps' one-click « Unsubscribe », List-Unsubscribe-Post); on=1 starts it again.
     */
    public static function page(string $method, string $token): void
    {
        $r = self::byToken($token);
        $lang = self::lang($r['lang'] ?? substr((string) ($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? 'en'), 0, 2));
        if ($r && $method === 'POST') { $off = (string) ($_POST['on'] ?? '') !== '1'; self::setOff($token, $off); $r['weekly_off'] = $off ? 1 : 0; }
        $L = self::W[$lang]; $h = fn($x) => htmlspecialchars((string) $x, ENT_QUOTES, 'UTF-8');
        $off = $r && (int) $r['weekly_off'] === 1;
        [$t, $p, $label] = !$r ? ['Sweep', $L['pg_bad'], ''] : ($off ? [$L['pg_off_t'], $L['pg_off_p'], $L['pg_off_b']] : [$L['pg_on_t'], $L['pg_on_p'], $L['pg_on_b']]);
        http_response_code($r ? 200 : 404);
        header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-store'); header('X-Robots-Tag: noindex');
        header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");
        header('Referrer-Policy: no-referrer');
        $form = $label === '' ? '' : '<form method="post" action="">' . ($off ? '<input type="hidden" name="on" value="1">' : '')
            . '<button type="submit" style="font:inherit;font-size:15px;font-weight:600;border:0;border-radius:999px;padding:13px 24px;cursor:pointer;background:' . ($off ? '#4c8dff;color:#0b0b0c' : '#2a2a30;color:#f2f2f3') . '">' . $h($label) . '</button></form>';
        echo '<!doctype html><html lang="' . $lang . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>' . $h($t) . ' · Sweep</title></head>'
            . '<body style="margin:0;min-height:100vh;background:#0b0b0c;color:#f2f2f3;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;display:flex;align-items:center;justify-content:center;padding:24px 16px;box-sizing:border-box">'
            . '<main style="max-width:420px;width:100%;background:#141416;border:1px solid #26262a;border-radius:26px;padding:32px 28px;box-sizing:border-box">'
            . '<div style="font-size:18px;font-weight:700;margin-bottom:24px">sweep</div><h1 style="font-size:22px;line-height:1.25;margin:0 0 10px">' . $h($t) . '</h1>'
            . '<p style="margin:0 0 24px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($p) . '</p>' . $form . '</main></body></html>';
        exit;
    }
}
