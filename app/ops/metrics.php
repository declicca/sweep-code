<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — admin dashboard numbers (Settings → Admin). Everything comes from Sweep's own database.
 * North star: traders who swept 3+ days in the last 7 days. Activation: first trade within 24 h of sign-up.
 * « Aha »: first swept day within 7 days. Week-2 retention: 3+ swept days during days 8-14.
 * Brief 01 step 4 (block « brief »), for the traders of the chosen sign-up week (cohort, Monday New York) and source
 * (« Where did you find Sweep? », users.found_via): median sign-up → first trade, activation (a trade on the sign-up day,
 * New York), retention D7 / D30 (a trade or a review during days 7-13 / 30-36, only traders whose window is over),
 * swept days (sessions with trades where the 3 rings are closed, last 30 days). JS errors grouped by message (30 days):
 * occurrences, traders affected, last seen, pages, browsers, versions — never any trade content.
 * Brief 03 step 1 (block « start »), same traders: signed up → first name → first account → first plan → first trade,
 * how many reached each step and the median time from the sign-up (sample-data accounts are not counted).
 * The journey's baseline (SWEEP.md, step 0), same traders: closed days (sessions with trades of the last 30 days whose
 * review is done) and Friday recaps opened (the 8 last finished weeks with a trade, recap opened: « weekly_opened »).
 * Brief activation of 27 Oct., step C (same traders): the sign-ups by New York time of day (before the open, session, evening,
 * weekend) with the share that made a first plan or trade on that session; the return on the next trading day (a visit, a plan
 * or a trade; usage_daily, game_days, users.last_login); the risk allowed seen on the session of the sign-up (a first plan or trade).
 */
function sweep_metrics(PDO $pdo, string $app, array $f = []): array
{
    $q = function (string $sql, array $a = []) use ($pdo) { $s = $pdo->prepare($sql); $s->execute($a); return $s; };
    $now = time(); $day = 86400;
    $has = fn(string $t) => (bool) $q("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", [$t])->fetchColumn();
    $users = $q('SELECT id, created_at, utm_source, utm_campaign, is_internal FROM users WHERE disabled = 0')->fetchAll(PDO::FETCH_ASSOC);
    $users = array_values(array_filter($users, fn($u) => !(int) ($u['is_internal'] ?? 0)));
    $ny = new DateTimeZone('America/New_York');
    $nyDay = fn(int $ts) => (new DateTimeImmutable('@' . $ts))->setTimezone($ny)->format('Y-m-d');
    $monday = fn(string $d) => (new DateTimeImmutable($d . ' 12:00', $ny))->modify('monday this week')->format('Y-m-d');
    $via = []; foreach ($q("SELECT id, COALESCE(NULLIF(found_via, ''), 'none') v FROM users") as $r) $via[$r['id']] = $r['v'];
    foreach ($users as &$u) { $u['ts'] = strtotime((string) $u['created_at']) ?: 0; $u['d0'] = $nyDay($u['ts']); $u['week'] = $monday($u['d0']); $u['via'] = $via[$u['id']] ?? 'none'; } unset($u);
    // the filters (brief 01 step 4): the lists of weeks and sources are counted on every trader, the numbers on the chosen ones
    $weeks = []; $sources = [];
    foreach ($users as $u) { $weeks[$u['week']] = ($weeks[$u['week']] ?? 0) + 1; $sources[$u['via']] = ($sources[$u['via']] ?? 0) + 1; }
    krsort($weeks); arsort($sources);
    $fc = (string) ($f['cohort'] ?? ''); $fs = (string) ($f['source'] ?? '');
    $all = $users;
    $users = array_values(array_filter($users, fn($u) => ($fc === '' || $u['week'] === $fc) && ($fs === '' || $u['via'] === $fs)));
    $first = []; if ($has('game_analytics')) foreach ($q("SELECT user_id, MIN(created_at) t FROM game_analytics WHERE event = 'trade_logged' GROUP BY user_id") as $r) $first[$r['user_id']] = (int) $r['t'];
    $swept = []; if ($has('game_days')) foreach ($q('SELECT user_id, trading_day FROM game_days WHERE is_swept = 1') as $r) $swept[$r['user_id']][] = $r['trading_day'];
    $rate = fn(int $a, int $b) => $b ? (int) round($a / $b * 100) : null;
    $act = $actN = $aha = $ahaN = $w2 = $w2N = 0; $src = [];
    foreach ($users as $u) {
        $age = $now - $u['ts'];
        if ($age <= 30 * $day) { $k = $u['utm_campaign'] ?: ($u['utm_source'] ?: 'direct'); $src[$k] = ($src[$k] ?? 0) + 1; }
        if ($age >= $day && $age <= 60 * $day) { $actN++; if (isset($first[$u['id']]) && $first[$u['id']] - $u['ts'] <= $day) $act++; }
        $d0 = gmdate('Y-m-d', $u['ts']);
        if ($age >= 7 * $day && $age <= 60 * $day) { $ahaN++; foreach ($swept[$u['id']] ?? [] as $d) if ($d <= gmdate('Y-m-d', $u['ts'] + 7 * $day)) { $aha++; break; } }
        if ($age >= 14 * $day && $age <= 90 * $day) { $w2N++; $n = 0; foreach ($swept[$u['id']] ?? [] as $d) if ($d > gmdate('Y-m-d', $u['ts'] + 7 * $day) && $d <= gmdate('Y-m-d', $u['ts'] + 14 * $day)) $n++; if ($n >= 3) $w2++; }
    }
    arsort($src);
    $since7 = gmdate('Y-m-d', $now - 7 * $day);
    $north = 0; foreach ($swept as $uid => $ds) { if (count(array_filter($ds, fn($d) => $d > $since7)) >= 3) $north++; }
    $active7 = $has('game_days') ? (int) $q('SELECT COUNT(DISTINCT user_id) FROM game_days WHERE activity = 1 AND trading_day > ?', [$since7])->fetchColumn() : 0;
    $ai = ['today' => 0.0, 'd7' => 0.0, 'calls_today' => 0];
    if ($has('ai_log')) {
        $r = $q('SELECT COALESCE(SUM(cost_usd), 0) c, COUNT(*) n FROM ai_log WHERE created_at >= ?', [gmdate('Y-m-d')])->fetch(PDO::FETCH_ASSOC);
        $ai = ['today' => round((float) $r['c'], 3), 'calls_today' => (int) $r['n'], 'd7' => round((float) $q('SELECT COALESCE(SUM(cost_usd), 0) FROM ai_log WHERE created_at >= ?', [gmdate('Y-m-d', $now - 7 * $day)])->fetchColumn(), 3)];
    }
    $methods = []; if ($has('game_analytics')) foreach ($q("SELECT meta_json FROM game_analytics WHERE event = 'trade_logged' AND created_at > ?", [$now - 30 * $day]) as $r) { $m = (json_decode((string) $r['meta_json'], true) ?: [])['method'] ?? 'manual'; $methods[$m] = ($methods[$m] ?? 0) + 1; }
    $errs = ['js_24h' => 0, 'top' => [], 'php_24h' => 0];
    if ($has('client_errors')) {
        $errs['js_24h'] = (int) $q('SELECT COUNT(*) FROM client_errors WHERE created_at > ?', [$now - $day])->fetchColumn();
        $errs['top'] = $q('SELECT msg, COUNT(*) n FROM client_errors WHERE created_at > ? GROUP BY msg ORDER BY n DESC LIMIT 5', [$now - 7 * $day])->fetchAll(PDO::FETCH_ASSOC);
    }
    $log = $app . '/error_log';
    if (is_file($log) && filesize($log) < 50 * 1048576) {
        $tags = ['[' . gmdate('d-M-Y', $now), '[' . gmdate('d-M-Y', $now - $day)];
        $fh = fopen($log, 'r'); if ($fh) { fseek($fh, max(0, filesize($log) - 2 * 1048576)); while (($line = fgets($fh)) !== false) foreach ($tags as $tg) if (strpos($line, $tg) === 0) { $errs['php_24h']++; break; } fclose($fh); }
    }
    $rev = ['subs' => [], 'mrr' => null];
    if ($has('billing_subs')) {
        $price = ['pro' => ['month' => 19, 'year' => 159], 'elite' => ['month' => 39, 'year' => 329]];
        $mrr = 0.0;
        foreach ($q("SELECT plan, billing_interval i, founding, COUNT(*) n FROM billing_subs WHERE status IN ('active','trialing','past_due') GROUP BY plan, billing_interval, founding") as $r) {
            $rev['subs'][] = $r;
            $p = $price[$r['plan']][$r['i'] === 'year' ? 'year' : 'month'] ?? 0; $m = $r['i'] === 'year' ? $p / 12 : $p;
            $mrr += $m * (int) $r['n'] * ((int) $r['founding'] ? 0.5 : 1);
        }
        $rev['mrr'] = round($mrr, 2);
    }
    $miss = [];
    if ($has('game_analytics')) foreach ($q("SELECT meta_json FROM game_analytics WHERE event = 'search_no_result' AND created_at > ?", [$now - 30 * $day]) as $r) {
        $mm = json_decode((string) $r['meta_json'], true) ?: []; $k = ($mm['q'] ?? '') . ' (' . ($mm['lang'] ?? '?') . ')'; $miss[$k] = ($miss[$k] ?? 0) + 1;
    }
    arsort($miss);
    // ── brief 01 step 4 ──
    $ids = array_flip(array_column($users, 'id'));
    $activeDays = []; $sess = 0; $sweptS = 0; $closedS = 0; $tradedWeeks = [];
    // the journey's baseline (SWEEP.md, step 0): closed days = sessions with trades whose review is done; the weeks a
    // Friday recap was ready for (a trade that week), to compare with the ones opened
    $wkLast = $monday($nyDay($now)); $wkFirst = (new DateTimeImmutable($wkLast . ' 12:00', $ny))->modify('-8 weeks')->format('Y-m-d');
    if ($has('game_days')) {
        foreach ($q('SELECT user_id, trading_day, trades_count, review_done, is_swept FROM game_days WHERE trades_count > 0 OR review_done = 1') as $r) {
            if (!isset($ids[$r['user_id']])) continue;
            $activeDays[$r['user_id']][] = $r['trading_day'];
            if ((int) $r['trades_count'] > 0 && $r['trading_day'] > gmdate('Y-m-d', $now - 30 * $day)) { $sess++; if ((int) $r['is_swept'] === 1) $sweptS++; if ((int) $r['review_done'] === 1) $closedS++; }
            if ((int) $r['trades_count'] > 0) { $w = $monday($r['trading_day']); if ($w >= $wkFirst && $w < $wkLast) $tradedWeeks[$r['user_id'] . '|' . $w] = true; }   // the 8 last finished weeks
        }
    }
    $openedW = 0;
    if ($tradedWeeks && $has('game_analytics')) foreach ($q("SELECT DISTINCT user_id, meta_json FROM game_analytics WHERE event = 'weekly_opened'") as $r) {
        $w = (json_decode((string) $r['meta_json'], true) ?: [])['week'] ?? ''; if (isset($tradedWeeks[$r['user_id'] . '|' . $w])) $openedW++;
    }
    $addD = fn(string $d, int $n) => (new DateTimeImmutable($d . ' 12:00', $ny))->modify(($n >= 0 ? '+' : '') . $n . ' days')->format('Y-m-d');
    $today = $nyDay($now);
    $retention = function (int $from, int $to) use ($users, $activeDays, $addD, $today, $rate) {   // active (trade or review) during days from..to
        $n = 0; $k = 0;
        foreach ($users as $u) {
            if ($addD($u['d0'], $to) >= $today) continue;   // the window is not over yet
            $n++; $a = $addD($u['d0'], $from); $b = $addD($u['d0'], $to);
            foreach ($activeDays[$u['id']] ?? [] as $d) if ($d >= $a && $d <= $b) { $k++; break; }
        }
        return ['pct' => $rate($k, $n), 'of' => $n];
    };
    $d0n = 0; $d0k = 0; $ft = [];
    foreach ($users as $u) {
        if (isset($first[$u['id']])) $ft[] = max(0, $first[$u['id']] - $u['ts']);
        if ($u['d0'] >= $today) continue;   // signed up today: the day is not over
        $d0n++; if (isset($first[$u['id']]) && $nyDay($first[$u['id']]) === $u['d0']) $d0k++;
    }
    sort($ft);
    // brief 03 step 1: where the new traders stop on the way to their first trade
    $cols = array_column($q('PRAGMA table_info(users)')->fetchAll(PDO::FETCH_ASSOC), 'name');
    $named = []; if (in_array('first_name', $cols, true)) foreach ($q("SELECT id FROM users WHERE COALESCE(first_name, '') <> ''") as $r) $named[$r['id']] = true;
    $acc1 = []; if ($has('documents')) foreach ($q("SELECT user_id, MIN(created_at) t FROM documents WHERE collection = 'accounts' AND data NOT LIKE '%\"demo\":true%' GROUP BY user_id") as $r) $acc1[$r['user_id']] = strtotime((string) $r['t']) ?: 0;
    // the first plan: when the journal's plan was saved (a plan made in the evening for the next session counts at once;
    // the « plan_saved » event waits for that day) — the event when this SQLite cannot read JSON
    $plan1 = [];
    try {
        if ($has('documents')) foreach ($q("SELECT user_id, MIN(COALESCE(CAST(json_extract(data, '$.pre.saved_at') AS INTEGER), CAST(strftime('%s', created_at) AS INTEGER))) t FROM documents WHERE collection = 'journals' AND json_extract(data, '$.pre.bias') IS NOT NULL AND COALESCE(json_extract(data, '$.demo'), 0) = 0 GROUP BY user_id") as $r) $plan1[$r['user_id']] = (int) $r['t'];
    } catch (Throwable $e) { $plan1 = []; }
    if (!$plan1 && $has('game_analytics')) foreach ($q("SELECT user_id, MIN(created_at) t FROM game_analytics WHERE event = 'plan_saved' GROUP BY user_id") as $r) $plan1[$r['user_id']] = (int) $r['t'];
    $step = function (array $at, bool $timed = true) use ($users) {
        $n = 0; $d = [];
        foreach ($users as $u) { if (!isset($at[$u['id']])) continue; $n++; if ($timed) $d[] = max(0, $at[$u['id']] - $u['ts']); }
        sort($d); return ['n' => $n, 'median_min' => $d ? (int) round($d[intdiv(count($d), 2)] / 60) : null];
    };
    // brief activation of 27 Oct., step C: when traders sign up (New York time), who comes back on the next trading day, and
    // who saw the risk allowed (a first plan) or « left today » (a first trade) on the session of the sign-up. A session runs
    // from 18:00 ET the day before (the app's todayStr): its day = the New York date 6 hours later.
    $sday = fn(int $ts) => $nyDay($ts + 6 * 3600);
    $nextTd = function (string $d) use ($addD) { do { $d = $addD($d, 1); $w = (int) (new DateTimeImmutable($d . ' 12:00'))->format('N'); } while ($w >= 6); return $d; };
    $slot = function (int $ts) use ($ny) {   // before the open (18:00 → 9:30), session (9:30 → 16:00), evening (16:00 → 18:00), weekend (Friday 17:00 → Sunday 18:00)
        $t = (new DateTimeImmutable('@' . $ts))->setTimezone($ny); $w = (int) $t->format('N'); $hm = $t->format('H:i');
        if (($w === 5 && $hm >= '17:00') || $w === 6 || ($w === 7 && $hm < '18:00')) return 'weekend';
        return $hm >= '09:30' && $hm < '16:00' ? 'session' : ($hm >= '16:00' && $hm < '18:00' ? 'evening' : 'before');
    };
    $todayS = $sday($now);
    $seen = [];   // the days a trader was there: a visit (usage of the app, the last sign-in), an activity of the game, a first plan or trade
    if ($has('usage_daily')) foreach ($q('SELECT DISTINCT user_id, day FROM usage_daily') as $r) $seen[$r['user_id']][$r['day']] = true;
    foreach ($activeDays as $uid => $ds) foreach ($ds as $d) $seen[$uid][$d] = true;
    if (in_array('last_login', $cols, true)) foreach ($q('SELECT id, last_login FROM users WHERE last_login IS NOT NULL') as $r) { $t = strtotime((string) $r['last_login']); if ($t) $seen[$r['id']][$sday($t)] = true; }
    $slots = []; foreach (['before', 'session', 'evening', 'weekend'] as $k) $slots[$k] = ['n' => 0, 'day0' => 0];
    $d1n = $d1k = $rsN = $rsK = 0;
    // (28 Oct., activation D) the three endings of the first visit: « active » (More than a year), else « open » (signed up during the
    // session, 9:30 → 16:00 ET on a weekday) or « closed » (the rest of the time); with each, who saw his risk allowed that session
    $xp = []; if (in_array('experience', $cols, true)) foreach ($q("SELECT id, experience FROM users WHERE experience IS NOT NULL") as $r) $xp[$r['id']] = (string) $r['experience'];
    // an account added « already running » (its balance moved by an adjustment) makes an active trader too
    if ($has('documents')) foreach ($q("SELECT user_id, data FROM documents WHERE collection = 'accounts'") as $r) {
        $a = json_decode((string) $r['data'], true); if (!is_array($a) || !empty($a['demo'])) continue;
        foreach ((array) ($a['adjustments'] ?? []) as $x) if (is_array($x) && (int) ($x['amount_c'] ?? 0) !== 0 && ($x['kind'] ?? '') !== 'fees') { $xp[$r['user_id']] = 'gt1'; break; }
    }
    $cases = []; foreach (['open', 'closed', 'active'] as $k) $cases[$k] = ['n' => 0, 'day0' => 0];
    foreach ($users as $u) {
        $s0 = $sday($u['ts']); $k = $slot($u['ts']); $slots[$k]['n']++;
        $day0 = (isset($plan1[$u['id']]) && $sday($plan1[$u['id']]) === $s0) || (isset($first[$u['id']]) && $sday($first[$u['id']]) === $s0);
        if ($day0) $slots[$k]['day0']++;
        $c = ($xp[$u['id']] ?? '') === 'gt1' ? 'active' : ($k === 'session' ? 'open' : 'closed'); $cases[$c]['n']++; if ($day0) $cases[$c]['day0']++;
        if ($s0 < $todayS) { $rsN++; if ($day0) $rsK++; }   // the session of the sign-up is over
        $j1 = $nextTd($s0);
        if ($j1 < $todayS) {   // that next trading day is over
            $d1n++;
            $back = isset($seen[$u['id']][$j1]) || (isset($plan1[$u['id']]) && $sday($plan1[$u['id']]) === $j1) || (isset($first[$u['id']]) && $sday($first[$u['id']]) === $j1);
            if ($back) $d1k++;
        }
    }
    foreach ($slots as &$x) $x['day0_pct'] = $rate($x['day0'], $x['n']); unset($x);
    foreach ($cases as &$x) $x['day0_pct'] = $rate($x['day0'], $x['n']); unset($x);
    $start = ['signed_up' => count($users), 'first_name' => $step($named, false), 'account' => $step($acc1), 'plan' => $step($plan1), 'trade' => $step($first)];
    $brief = [
        'start' => $start,
        'filters' => ['cohort' => $fc, 'source' => $fs, 'weeks' => array_slice($weeks, 0, 16, true), 'sources' => $sources, 'traders' => count($users), 'of' => count($all)],
        'first_trade_median_min' => $ft ? (int) round($ft[intdiv(count($ft), 2)] / 60) : null, 'first_trade_of' => count($ft),
        'activation_day0' => ['pct' => $rate($d0k, $d0n), 'of' => $d0n],
        'retention_d7' => $retention(7, 13), 'retention_d30' => $retention(30, 36),
        'swept_sessions_30d' => ['pct' => $rate($sweptS, $sess), 'of' => $sess],
        'closed_sessions_30d' => ['pct' => $rate($closedS, $sess), 'of' => $sess],
        'weekly_opened_8w' => ['pct' => $rate($openedW, count($tradedWeeks)), 'of' => count($tradedWeeks)],
        'signup_slots' => $slots, 'start_cases' => $cases, 'return_d1' => ['pct' => $rate($d1k, $d1n), 'of' => $d1n], 'risk_seen_day0' => ['pct' => $rate($rsK, $rsN), 'of' => $rsN],
    ];
    if ($has('client_errors')) {   // grouped by message, its numbers taken out (ops/client-errors.php), last 30 days
        require_once __DIR__ . '/client-errors.php';
        $errs['groups_30d'] = array_map(fn($x) => ['msg' => $x['msg'], 'n' => $x['n'], 'traders' => $x['traders'], 'first' => gmdate('c', $x['first']), 'last' => gmdate('c', $x['last']),
            'pages' => $x['pages'], 'browsers' => $x['browsers'], 'versions' => $x['versions'], 'where' => $x['where']], array_slice(sweep_err_groups($pdo, $now), 0, 20));
    }
    // the game's use over 30 days (brief 02 part 11): among the active traders (a trade, a plan or a review on a session of
    // the last 30 days; Mateo's and test accounts aside), those who used each feature (an action of theirs) or reached it
    // (given by journaling: missions, badges, levels…). After 30 days of data, the ones under 10 % go to NOTES.md.
    $game = null;
    if ($has('game_days') && $has('game_analytics')) {
        $real = array_fill_keys(array_column($all, 'id'), true);
        $act30 = [];
        foreach ($q('SELECT DISTINCT user_id FROM game_days WHERE activity = 1 AND trading_day >= ?', [$nyDay($now - 30 * $day)])->fetchAll(PDO::FETCH_COLUMN) as $u) if (isset($real[$u])) $act30[$u] = true;
        $ev = [];
        foreach ($q('SELECT DISTINCT user_id, event FROM game_analytics WHERE created_at > ?', [$now - 30 * $day]) as $r) if (isset($act30[$r['user_id']])) $ev[$r['event']][$r['user_id']] = true;
        $rows = function (string $sql) use ($q, $has, $act30): array { try { $o = []; foreach ($q($sql)->fetchAll(PDO::FETCH_COLUMN) as $u) if (isset($act30[$u])) $o[$u] = true; return $o; } catch (Throwable $e) { return []; } };
        $any = function (array $events, array ...$more) use ($ev): array { $o = []; foreach ($events as $e) $o += $ev[$e] ?? []; foreach ($more as $m) $o += $m; return $o; };
        $used = [
            'share' => $any(['share_card_created', 'share_card_shared']),
            'weekly_recap' => $any(['weekly_opened']), 'weekly_review' => $any(['weekly_review_done']), 'chest' => $any(['chest_opened']), 'edge_reveal' => $any(['edge_reveal_viewed']),
            'wrapped' => $any(['wrapped_viewed']), 'season' => $any(['season_tier_claimed']),
            'league' => $any(['league_joined'], $has('social_profile') ? $rows('SELECT user_id FROM social_profile WHERE league_opt_in = 1') : []),
            'crew' => $any(['crew_created', 'crew_joined'], $has('crew_members') ? $rows('SELECT user_id FROM crew_members') : []),
            'buddy' => $any(['buddy_linked', 'buddy_encourage']),
            'discord' => $any(['discord_linked'], $has('social_profile') ? $rows("SELECT user_id FROM social_profile WHERE discord_user_id IS NOT NULL AND discord_user_id <> ''") : []),
            'theme' => $any(['cosmetic_equipped'], $has('user_cosmetics') ? $rows('SELECT user_id FROM user_cosmetics WHERE equipped = 1') : []),
            'mission_reroll' => $any(['mission_rerolled']), 'locked_tap' => $any(['locked_feature_tapped']),
        ];
        $reached = [
            'mission' => $any(['mission_completed']), 'badge' => $any(['badge_unlocked']), 'level' => $any(['level_up']), 'swept' => $any(['day_swept']),
            'streak3' => $has('user_game_profile') ? $rows('SELECT user_id FROM user_game_profile WHERE streak_current >= 3') : [], 'freeze' => $any(['freeze_used']),
            'map' => $any(['map_node_completed']), 'boss' => $any(['boss_defeated']), 'comeback' => $any(['comeback_started']), 'wow' => $any(['wow_moment']),
        ];
        $n = count($act30); $pc = fn(array $x) => ['n' => count($x), 'pct' => $n ? (int) round(count($x) / $n * 100) : 0];
        $game = ['active_30d' => $n, 'used' => array_map($pc, $used), 'reached' => array_map($pc, $reached)];
    }
    return [
        'generated_at' => gmdate('c'), 'users' => count($users), 'brief' => $brief, 'game' => $game,
        'signups' => ['d7' => count(array_filter($users, fn($u) => $now - $u['ts'] <= 7 * $day)), 'd30' => count(array_filter($users, fn($u) => $now - $u['ts'] <= 30 * $day)), 'by_source_30d' => array_slice($src, 0, 8, true)],
        'north_star' => $north, 'active_7d' => $active7,
        'first_trade' => (function () use ($users, $first) {   // time from sign-up to the first trade (median), and how many log it on day 1
            $d = []; $d1 = 0; $n = 0;
            foreach ($users as $u) { $n++; if (!isset($first[$u['id']])) continue; $x = max(0, $first[$u['id']] - $u['ts']); $d[] = $x; if ($x <= 86400) $d1++; }
            sort($d); $m = $d ? $d[intdiv(count($d), 2)] : null;
            return ['median_min' => $m === null ? null : round($m / 60), 'day1_pct' => $n ? round($d1 / $n * 100) : 0, 'of' => $n];
        })(),
        'activation_24h' => ['pct' => $rate($act, $actN), 'of' => $actN], 'aha_7d' => ['pct' => $rate($aha, $ahaN), 'of' => $ahaN], 'retention_w2' => ['pct' => $rate($w2, $w2N), 'of' => $w2N],
        'journal' => (function () use ($pdo, $all, $now, $has) { if (!$has('documents')) return null; $real = array_fill_keys(array_column($all, 'id'), true); return ['d7' => sweep_journal_metrics($pdo, $real, $now, 7), 'd30' => sweep_journal_metrics($pdo, $real, $now, 30)]; })(),
        'trade_methods_30d' => $methods, 'search_misses_30d' => array_slice($miss, 0, 20, true), 'ai' => $ai, 'errors' => $errs, 'revenue' => $rev,
        'presets' => (function () { require_once dirname(__DIR__) . '/presets/presets-lib.php'; $c = pr_current(); return ['version' => $c['version'] ?? '', 'checked_at' => $c['checked_at'] ?? null, 'origin' => $c['origin'] ?? '', 'status' => pr_status()]; })(),
    ];
}

/**
 * Brief « pertes oubliées » of 27 Oct., step 1 — a complete journal, measured before changing anything. Over the last $days
 * days (the trade's session date, New York), the real traders' trades (sample data aside, a trade copied on several accounts
 * once): the share of traders with 20 trades or more and over 80 % winners (the plainest sign of losses not logged), the share
 * of losing trades, the share of trading days (a trader, a day) without a single losing trade. Net = pnl_c − fees_c.
 */
function sweep_journal_metrics(PDO $pdo, array $real, int $now, int $days): array
{
    $from = (new DateTimeImmutable('@' . ($now - $days * 86400)))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d');
    $st = $pdo->prepare("SELECT user_id, data FROM documents WHERE collection = 'trades'"); $st->execute();
    $per = []; $seen = []; $lines = $gapAbs = $detAbs = 0;
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) {
        if (!isset($real[$r['user_id']])) continue;
        $t = json_decode((string) $r['data'], true); if (!is_array($t) || !empty($t['demo'])) continue;
        $d = (string) ($t['date'] ?? ''); if ($d === '' || $d < $from) continue;
        if (!empty($t['copy_group'])) { $k = $r['user_id'] . '|' . $t['copy_group']; if (isset($seen[$k])) continue; $seen[$k] = true; }
        $net = (int) ($t['pnl_c'] ?? 0) - (int) ($t['fees_c'] ?? 0);
        $u = &$per[$r['user_id']]; $u ??= ['n' => 0, 'w' => 0, 'l' => 0, 'days' => []];
        $u['n']++; if ($net > 0) $u['w']++; elseif ($net < 0) $u['l']++;
        $u['days'][$d] = ($u['days'][$d] ?? false) || $net < 0;
        unset($u);
        if (!empty($t['untracked']) && is_array($t['untracked'])) { $lines++; $gapAbs += abs((int) ($t['untracked']['gap_c'] ?? 0)); $detAbs += abs((int) ($t['untracked']['detailed_c'] ?? 0)); }
    }
    // (step 2) the days closed on the platform's balance: with a gap, the gaps' total, the share detailed in trades since
    $st = $pdo->prepare("SELECT user_id, id, data FROM documents WHERE collection = 'journals'"); $st->execute();
    $closed = $withGap = $gapSum = 0;
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) {
        if (!isset($real[$r['user_id']]) || (string) $r['id'] < $from) continue;
        $j = json_decode((string) $r['data'], true); $bal = is_array($j) && empty($j['demo']) ? ($j['post']['bal'] ?? null) : null;
        if (!is_array($bal) || !$bal) continue;
        $closed++; $g = 0;
        foreach ($bal as $b) $g += abs((int) ($b['gap_c'] ?? 0));
        if ($g) { $withGap++; $gapSum += $g; }
    }
    $rate = fn(int $a, int $b) => $b ? (int) round($a / $b * 100) : null;
    $t20 = $hi = $n = $l = $dn = $dk = 0;
    foreach ($per as $u) {
        $n += $u['n']; $l += $u['l'];
        if ($u['n'] >= 20) { $t20++; if ($u['w'] / $u['n'] > 0.8) $hi++; }
        foreach ($u['days'] as $lost) { $dn++; if (!$lost) $dk++; }
    }
    return ['days' => $days, 'traders' => count($per), 'high_win_20' => ['pct' => $rate($hi, $t20), 'of' => $t20], 'losing_trades' => ['pct' => $rate($l, $n), 'of' => $n],
        'days_without_loss' => ['pct' => $rate($dk, $dn), 'of' => $dn],
        'gap_days' => ['pct' => $rate($withGap, $closed), 'of' => $closed], 'gap_total_c' => $gapSum, 'gap_detailed' => ['pct' => $gapAbs ? (int) round($detAbs / $gapAbs * 100) : null, 'of' => $lines]];
}

/** « Safari iOS 18 », « Chrome Android », « Firefox macOS »: enough to group errors, nothing personal */
function sweep_browser(string $ua): string
{
    $os = preg_match('/iPhone|iPad|iPod/', $ua) ? 'iOS' : (stripos($ua, 'Android') !== false ? 'Android' : (stripos($ua, 'Mac OS X') !== false ? 'macOS' : (stripos($ua, 'Windows') !== false ? 'Windows' : (stripos($ua, 'Linux') !== false ? 'Linux' : '?'))));
    $b = preg_match('/Edg\//', $ua) ? 'Edge' : (preg_match('/CriOS|Chrome\//', $ua) ? 'Chrome' : (preg_match('/FxiOS|Firefox\//', $ua) ? 'Firefox' : (stripos($ua, 'Safari') !== false ? 'Safari' : '?')));
    $v = $os === 'iOS' && preg_match('/OS (\d+)_/', $ua, $m) ? ' ' . $m[1] : '';
    return "$b $os$v";
}
