<?php
// Sweep billing — local test settings, test values only (tests/e2e_billing.py runs a second copy of the local server with
// SWEEP_BILLING_CONFIG pointing here). No Stripe key: Stripe is never called; the test sends webhooks signed with this test secret.
return [
    'live' => true, 'launch_at' => '2026-01-01T00:00:00Z', 'trial' => ['plan' => 'pro', 'days' => 60], 'campaign_grants' => [],
    'plans' => [
        'free'  => ['accounts' => 2, 'analytics_days' => 30, 'payouts' => false, 'ai_daily' => 3, 'ai_import' => false, 'ai_reviews' => 0, 'calendar_notes' => 'preview', 'weekly_report' => false, 'priority_support' => false],
        'pro'   => ['accounts' => 5, 'analytics_days' => null, 'payouts' => true, 'ai_daily' => 50, 'ai_import' => true, 'ai_reviews' => 3, 'calendar_notes' => 'preview', 'weekly_report' => false, 'priority_support' => false],
        'elite' => ['accounts' => null, 'analytics_days' => null, 'payouts' => true, 'ai_daily' => 200, 'ai_import' => true, 'ai_reviews' => null, 'calendar_notes' => 'full', 'weekly_report' => true, 'priority_support' => true],
    ],
    'display_prices' => ['pro' => ['month' => 29, 'year' => 290], 'elite' => ['month' => 59, 'year' => 590]],
    'stripe_prices' => ['pro' => ['month' => 'price_local_pro_m', 'year' => 'price_local_pro_y'], 'elite' => ['month' => 'price_local_elite_m', 'year' => 'price_local_elite_y']],
    'stripe_secret_key' => '', 'stripe_webhook_secret' => 'whsec_local_test_only',
];
