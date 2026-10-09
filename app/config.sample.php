<?php
/*
 * Sweep — configuration for app.makeitsweep.com
 * Copy this file to config.php and fill in the values marked "CHANGE".
 * This file is never sent to the browser (blocked in .htaccess and executed as PHP).
 */
return [
    // Administrator account, created ONLY the very first time (when no account exists yet).
    // Afterwards, change the password from Settings in the app.
    'user'     => 'mateo',                                   // CHANGE
    'password' => 'change-me-to-a-long-random-password',     // CHANGE — 10+ characters

    // Public sign-up: 'open' (anyone), 'invite' (needs a code) or 'closed'.
    // Can also be changed later in the app (Traders page, administrator only).
    'registration' => 'open',
    'invite_code'  => '',

    // Public address of the app and email settings (password reset links).
    'app_url'       => 'https://app.makeitsweep.com/',
    'mail_from'     => 'hello@makeitsweep.com',              // the sender of every email (password reset…)
    'support_email' => 'hello@makeitsweep.com',              // shown in the app (help, settings) and as « Reply-To »
    // send through the mailbox itself (best delivery). cPanel → Email Accounts → hello@ → Connect Devices shows these values.
    'smtp'          => ['host' => 'mail.makeitsweep.com', 'port' => 465, 'user' => 'hello@makeitsweep.com', 'pass' => ''],
    'support_email' => 'hello@makeitsweep.com',              // replies to reset emails go here

    // Where the database and screenshots are stored.
    // Recommended: a folder OUTSIDE the web folder, for example '/home/CPANELUSER/sweep-data'   // CHANGE
    'data_dir' => __DIR__ . '/data',

    // Sweep AI (optional). The private AI settings and Gemini key live OUTSIDE the web folder:
    // /home/CPANELUSER/sweep-private/ai-config.php is found automatically. Set a full path here only if it lives elsewhere.
    'ai_config' => '',

    // Campaign counter for makeitsweep.com/100 (public endpoint /api/cohort-count.php, cached 60 s, CORS: makeitsweep.com).
    // count: 'signups' (every new trader) or 'activated' (has an account and a first trade). Internal/test accounts are excluded (Traders page → Manage).
    'cohort' => ['start' => '2026-10-11T04:00:00Z', 'total' => 100, 'count' => 'signups'],

    // Billing (optional). sweep-private/billing-config.php next to ai-config.php is found automatically; set a full path only if it lives elsewhere.
    'billing_config' => '',

    // Market context (optional). Leave keys empty to disable.
    // Economic calendar: 'manual' (bundled 2026–2027 schedule + admin), 'tradingeconomics', 'fmp' or 'finnhub'.
    'econ_provider'   => 'manual',
    'econ_api_key'    => '',
    // Market data for the trade chart: 'none' or 'databento' (CME Globex 1-minute bars).
    'market_provider' => 'none',
    'market_api_key'  => '',
    'market_symbol'   => 'NQ.v.0',

    // In-app notifications (optional). daily_limit = normal notifications per trader per 24 h; celebrations are not counted.
    'notifications' => ['daily_limit' => 5],

    // Limits
    'max_users'            => 5000,    // maximum number of trader accounts
    'upload_quota_mb'      => 200,     // screenshot storage per trader
    'max_records_per_user' => 50000,   // trades + journals + other records per trader

    // Database. 'sqlite' needs no setup. Use 'mysql' only if SQLite is unavailable.
    'db' => [
        'driver'   => 'sqlite',
        'host'     => 'localhost',
        'name'     => '',
        'user'     => '',
        'password' => '',
    ],
];
