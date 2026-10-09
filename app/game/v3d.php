<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V3, last steps: Discord rank roles (no Node, no gateway) and the annual Wrapped.
 *
 * Discord: OAuth2 (scope identify) links the account; the hourly cron gives the Discord role matching the Sweep rank
 * (and removes the previous one) through the REST API with the bot token; an optional webhook posts the big moments
 * (boss beaten, new rank, crew goal) of traders who opted in. Never P&L or amounts. Config and token live in the
 * private folder: /home/<user>/sweep-private/discord-config.php (template: game/discord-config.sample.php).
 * Annual Wrapped: same story player as the monthly one, built from Dec 15 (preview) and on Jan 1.
 */

final class GameDiscord
{
    private static ?array $cfg = null;
    public static function cfg(): array
    {
        if (self::$cfg !== null) return self::$cfg;
        $c = [];
        foreach (array_filter([defined('SWEEP_DISCORD_CONFIG') ? (string) SWEEP_DISCORD_CONFIG : '', dirname(__DIR__, 2) . '/sweep-private/discord-config.php', dirname(__DIR__, 3) . '/sweep-private/discord-config.php']) as $p) {
            if (@is_readable($p)) { $x = require $p; if (is_array($x)) { $c = $x; break; } }
        }
        $c += ['client_id' => '', 'client_secret' => '', 'bot_token' => '', 'guild_id' => '', 'redirect_uri' => '', 'rank_roles' => [], 'moments_webhook' => ''];
        $c['enabled'] = $c['client_id'] !== '' && $c['client_secret'] !== '' && $c['redirect_uri'] !== '';
        $c['roles_on'] = $c['enabled'] && $c['bot_token'] !== '' && $c['guild_id'] !== '' && array_filter((array) $c['rank_roles']);
        return self::$cfg = $c;
    }

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        GameSocial::schema();
        $pdo = GameEngine::pdo(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $have = $my ? array_column($pdo->query('SHOW COLUMNS FROM social_profile')->fetchAll(PDO::FETCH_ASSOC), 'Field') : array_column($pdo->query('PRAGMA table_info(social_profile)')->fetchAll(PDO::FETCH_ASSOC), 'name');
        foreach (['discord_user_id' => 'VARCHAR(30) NULL', 'discord_name' => 'VARCHAR(60) NULL', 'discord_share' => 'INT NOT NULL DEFAULT 0', 'discord_rank_synced' => 'VARCHAR(20) NULL', 'discord_synced_at' => 'INT NULL'] as $col => $type)
            if (!in_array($col, $have, true)) $pdo->exec("ALTER TABLE social_profile ADD COLUMN $col $type");
        $AI = $my ? 'BIGINT AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
        $pdo->exec("CREATE TABLE IF NOT EXISTS discord_queue (id $AI, content TEXT NOT NULL, created_at INT NOT NULL, sent_at INT NULL)" . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
    }

    private static function http(string $method, string $url, array $headers = [], ?string $body = null): array
    {
        for ($try = 1; $try <= 3; $try++) {
            if (function_exists('curl_init')) {
                $ch = curl_init($url);
                curl_setopt_array($ch, [CURLOPT_CUSTOMREQUEST => $method, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20, CURLOPT_HTTPHEADER => $headers]);
                if ($body !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
                $out = (string) curl_exec($ch); $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
            } else {
                $ctx = stream_context_create(['http' => ['method' => $method, 'header' => implode("\r\n", $headers), 'content' => (string) $body, 'timeout' => 20, 'ignore_errors' => true]]);
                $out = (string) @file_get_contents($url, false, $ctx); $code = 0;
                foreach ($http_response_header ?? [] as $h) if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $m)) $code = (int) $m[1];
            }
            if ($code !== 429 && $code < 500) return [$code, $out];
            $wait = (float) ((json_decode($out, true) ?: [])['retry_after'] ?? 1);   // Discord rate limit: wait as asked
            usleep((int) (min(5, max(0.5, $wait)) * 1000000));
        }
        return [$code ?? 0, $out ?? ''];
    }

    /* ───────────── OAuth2 link (scope identify) ───────────── */

    private static function state(string $uid, int $t): string { return $t . '.' . substr(hash_hmac('sha256', $uid . '|' . $t, (string) self::cfg()['client_secret']), 0, 32); }
    public static function authorizeUrl(string $uid): ?string
    {
        $c = self::cfg(); if (!$c['enabled']) return null;
        return 'https://discord.com/oauth2/authorize?' . http_build_query(['client_id' => $c['client_id'], 'redirect_uri' => $c['redirect_uri'], 'response_type' => 'code', 'scope' => 'identify', 'state' => self::state($uid, time()), 'prompt' => 'none']);
    }
    public static function callback(string $uid, string $code, string $state): bool
    {
        $c = self::cfg(); if (!$c['enabled']) return false;
        [$t] = explode('.', $state . '.'); $t = (int) $t;
        if ($t < time() - 900 || !hash_equals(self::state($uid, $t), $state)) return false;       // CSRF + 15-minute window
        [$code1, $tok] = self::http('POST', 'https://discord.com/api/oauth2/token', ['Content-Type: application/x-www-form-urlencoded'],
            http_build_query(['client_id' => $c['client_id'], 'client_secret' => $c['client_secret'], 'grant_type' => 'authorization_code', 'code' => $code, 'redirect_uri' => $c['redirect_uri']]));
        $access = (json_decode($tok, true) ?: [])['access_token'] ?? null;
        if ($code1 !== 200 || !$access) { error_log('[Sweep discord] token HTTP ' . $code1); return false; }
        [$code2, $me] = self::http('GET', 'https://discord.com/api/users/@me', ['Authorization: Bearer ' . $access]);
        $u = json_decode($me, true) ?: [];
        if ($code2 !== 200 || empty($u['id'])) return false;
        self::schema();
        if (!GameEngine::q('SELECT 1 FROM social_profile WHERE user_id = ?', [$uid])->fetchColumn()) GameEngine::q('INSERT INTO social_profile (user_id, updated_at) VALUES (?, ?)', [$uid, time()]);
        GameEngine::q('UPDATE social_profile SET discord_user_id = ?, discord_name = ?, discord_rank_synced = NULL WHERE user_id = ?', [(string) $u['id'], substr((string) ($u['global_name'] ?? $u['username'] ?? ''), 0, 60), $uid]);
        GameEngine::track($uid, 'discord_linked');
        return true;
    }
    public static function unlink(string $uid): void
    {
        self::schema();
        $r = GameEngine::q('SELECT discord_user_id FROM social_profile WHERE user_id = ?', [$uid])->fetchColumn();
        if ($r) self::setRoles((string) $r, null);   // take the rank role back
        GameEngine::q('UPDATE social_profile SET discord_user_id = NULL, discord_name = NULL, discord_rank_synced = NULL, discord_share = 0 WHERE user_id = ?', [$uid]);
    }
    public static function state_(string $uid): array
    {
        self::schema(); $c = self::cfg();
        $r = GameEngine::q('SELECT discord_user_id, discord_name, discord_share FROM social_profile WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
        return ['enabled' => $c['enabled'], 'linked' => !empty($r['discord_user_id']), 'name' => $r['discord_name'] ?? null, 'share' => !empty($r['discord_share'])];
    }
    public static function setShare(string $uid, bool $on): void { self::schema(); GameEngine::q('UPDATE social_profile SET discord_share = ? WHERE user_id = ?', [$on ? 1 : 0, $uid]); }

    /* ───────────── roles (cron, REST only) ───────────── */

    /** give the role of $rank (null = none) and remove the other rank roles */
    private static function setRoles(string $did, ?string $rank): bool
    {
        $c = self::cfg(); if (!$c['roles_on']) return false;
        $roles = array_filter((array) $c['rank_roles']); $base = 'https://discord.com/api/v10/guilds/' . $c['guild_id'] . '/members/' . $did;
        $h = ['Authorization: Bot ' . $c['bot_token'], 'X-Audit-Log-Reason: Sweep rank sync'];
        [$code, $body] = self::http('GET', $base, $h);
        if ($code === 404) return true;                       // not on the server (yet): nothing to do
        if ($code !== 200) { error_log('[Sweep discord] member HTTP ' . $code); return false; }
        $has = (json_decode($body, true) ?: [])['roles'] ?? [];
        foreach ($roles as $rk => $roleId) {
            $want = $rank !== null && $rk === $rank;
            if ($want && !in_array($roleId, $has, true)) self::http('PUT', "$base/roles/$roleId", $h);
            if (!$want && in_array($roleId, $has, true)) self::http('DELETE', "$base/roles/$roleId", $h);
        }
        return true;
    }
    /** cron: sync ranks that changed (or every 24 h), then flush the moments queue */
    public static function cron(): void
    {
        $c = self::cfg(); if (!$c['enabled']) return;
        self::schema();
        if ($c['roles_on']) {
            $rows = GameEngine::q('SELECT sp.user_id, sp.discord_user_id, sp.discord_rank_synced, sp.discord_synced_at, gp.rank_key FROM social_profile sp JOIN user_game_profile gp ON gp.user_id = sp.user_id WHERE sp.discord_user_id IS NOT NULL')->fetchAll(PDO::FETCH_ASSOC);
            foreach ($rows as $r) {
                if ($r['discord_rank_synced'] === $r['rank_key'] && (int) $r['discord_synced_at'] > time() - 86400) continue;
                if (self::setRoles((string) $r['discord_user_id'], (string) $r['rank_key'])) GameEngine::q('UPDATE social_profile SET discord_rank_synced = ?, discord_synced_at = ? WHERE user_id = ?', [$r['rank_key'], time(), $r['user_id']]);
                usleep(250000);
            }
        }
        if ($c['moments_webhook'] !== '') {
            foreach (GameEngine::q('SELECT * FROM discord_queue WHERE sent_at IS NULL ORDER BY id LIMIT 20')->fetchAll(PDO::FETCH_ASSOC) as $m) {
                [$code] = self::http('POST', (string) $c['moments_webhook'], ['Content-Type: application/json'], json_encode(['content' => $m['content'], 'allowed_mentions' => ['parse' => []]]));
                if ($code >= 200 && $code < 300) GameEngine::q('UPDATE discord_queue SET sent_at = ? WHERE id = ?', [time(), $m['id']]);
            }
        }
    }
    /** big moments of traders who opted in (called from GameEngine::celebrate) */
    public static function onCelebrate(string $uid, string $type, array $p): void
    {
        if (!in_array($type, ['boss_defeated', 'level', 'crew_goal'], true) || ($type === 'level' && empty($p['rank_up']))) return;
        $c = self::cfg(); if (!$c['enabled'] || $c['moments_webhook'] === '') return;
        self::schema();
        $r = GameEngine::q('SELECT handle, discord_share FROM social_profile WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        if (!$r || !(int) $r['discord_share'] || !$r['handle']) return;
        $h = str_replace(['@', '`', '*', '_'], '', (string) $r['handle']);
        $bn = ['revenge' => 'Le Revenge', 'fomo_open' => "Le FOMO de l'ouverture", 'cursed_day' => 'Le Jour maudit', 'oversize' => "L'Oversize", 'moving_stop' => 'Le Stop fuyant', 'overtrader' => 'Le Surchauffe', 'offplan' => "L'Improvisateur", 'no_plan' => 'Le Sans-plan'][$p['boss'] ?? ''] ?? 'un boss';
        $rn = ['rookie' => 'Recrue', 'apprentice' => 'Apprenti', 'disciplined' => 'Discipliné', 'consistent' => 'Constant', 'seasoned' => 'Aguerri', 'master' => 'Maître', 'sweeper' => 'Sweeper'][$p['rank'] ?? ''] ?? '';
        $txt = $type === 'boss_defeated' ? "🕯️ **$h** a battu $bn." : ($type === 'level' ? "🕯️ **$h** est maintenant $rn." : "🕯️ Le crew de **$h** a atteint son objectif de la semaine.");
        GameEngine::q('INSERT INTO discord_queue (content, created_at) VALUES (?, ?)', [$txt, time()]);
    }
}

/** annual Wrapped: built from Dec 15 (preview) and on Jan 1 for the year just ended; stored as month "YYYY-AN" */
final class GameWrappedYear
{
    public static function ensure(string $uid): void
    {
        GameWrapped::schema();
        $today = GameEngine::today(); $md = substr($today, 5); $yNow = (int) substr($today, 0, 4);
        if ($md >= '12-15') { $year = $yNow; $rebuildBefore = 0; }                                   // preview
        elseif ($md <= '01-31') { $year = $yNow - 1; $rebuildBefore = (new DateTimeImmutable("$yNow-01-01"))->getTimestamp(); }   // final version
        else return;
        $key = $year . '-AN';
        $row = GameEngine::q('SELECT created_at FROM monthly_wrapped WHERE user_id = ? AND month = ?', [$uid, $key])->fetchColumn();
        if ($row !== false && (int) $row >= $rebuildBefore) return;
        $data = self::build($uid, $year); if (!$data) return;
        GameEngine::q('DELETE FROM monthly_wrapped WHERE user_id = ? AND month = ?', [$uid, $key]);
        GameEngine::q('INSERT INTO monthly_wrapped (user_id, month, data_json, created_at) VALUES (?, ?, ?, ?)', [$uid, $key, json_encode($data), GameEngine::ts()]);
    }

    public static function build(string $uid, int $y): ?array
    {
        $from = "$y-01-01"; $to = "$y-12-31";
        $days = GameEngine::q('SELECT trading_day, is_swept, is_valid_streak, activity FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ? ORDER BY trading_day', [$uid, $from, $to])->fetchAll(PDO::FETCH_ASSOC);
        if (count(array_filter($days, fn($d) => (int) $d['activity'])) < 10) return null;
        $by = []; foreach ($days as $d) $by[$d['trading_day']] = $d;
        $swept = 0; $run = 0; $best = 0; $first = $days[0]['trading_day'];
        for ($d = $first; $d <= min($to, GameEngine::today()); $d = GameEngine::addDays($d, 1)) {
            if (!GameEngine::isMarketDay($d)) continue;
            $g = $by[$d] ?? null; if ($g && (int) $g['is_swept']) $swept++;
            $run = $g && (int) $g['is_valid_streak'] ? $run + 1 : 0; $best = max($best, $run);
        }
        $tz = new DateTimeZone('America/New_York');
        [$s, $e] = [(new DateTimeImmutable("$from 00:00", $tz))->getTimestamp(), (new DateTimeImmutable("$to 23:59:59", $tz))->getTimestamp()];
        $bosses = []; try { $bosses = GameEngine::q('SELECT boss_id FROM user_bosses WHERE user_id = ? AND defeated_at BETWEEN ? AND ?', [$uid, $s, $e])->fetchAll(PDO::FETCH_COLUMN); } catch (Throwable $x) { /* none */ }
        $chapters = (int) GameEngine::q("SELECT COUNT(*) FROM xp_events WHERE user_id = ? AND event_key LIKE 'chapter:%' AND created_at BETWEEN ? AND ?", [$uid, $s, $e])->fetchColumn();
        $xp = (int) GameEngine::q('SELECT COALESCE(SUM(xp), 0) FROM xp_events WHERE user_id = ? AND created_at BETWEEN ? AND ?', [$uid, $s, $e])->fetchColumn();
        // signature setup and golden slot of the year (R, counts), reusing the monthly builder's logic month by month
        $setups = []; $slots = [];
        foreach (GameEngine::docs($uid, 'trades') as $t) {
            if (($t['date'] ?? '') < $from || ($t['date'] ?? '') > $to || !empty($t['demo'])) continue;
            $st = trim((string) ($t['setup'] ?? '')); if ($st !== '') $setups[$st] = ($setups[$st] ?? 0) + 1;
            $r = GameV2b::rOf($t);
            if ($r !== null && preg_match('/^(\d{2}):(\d{2})/', (string) ($t['entry_time'] ?? ''), $x)) { $k = intdiv((int) $x[1] * 60 + (int) $x[2], 30) * 30; $slots[$k][] = $r; }
        }
        arsort($setups);
        $slots = array_filter($slots, fn($v) => count($v) >= 5);
        uasort($slots, fn($a, $b) => array_sum($b) / count($b) <=> array_sum($a) / count($a));
        $gold = $slots ? (function ($k, $v) { return ['start' => sprintf('%02d:%02d', intdiv($k, 60), $k % 60), 'end' => sprintf('%02d:%02d', intdiv($k + 30, 60), ($k + 30) % 60), 'r' => round(array_sum($v) / count($v), 2), 'n' => count($v)]; })(array_key_first($slots), reset($slots)) : null;
        $tier = 1; try { $tier = (int) (GameEngine::q('SELECT league_tier FROM social_profile WHERE user_id = ?', [$uid])->fetchColumn() ?: 1); } catch (Throwable $x) { /* no leagues */ }
        $p = GameEngine::profile($uid, false);
        return ['kind' => 'year', 'month' => "$y-AN", 'year' => $y, 'swept' => $swept, 'best_streak' => $best, 'bosses' => $bosses, 'chapters' => $chapters,
                'signature' => $setups ? ['setup' => array_key_first($setups), 'n' => reset($setups)] : null, 'gold_slot' => $gold, 'xp' => $xp, 'level' => (int) $p['level'], 'rank' => $p['rank_key'], 'league_tier' => $tier];
    }
}
