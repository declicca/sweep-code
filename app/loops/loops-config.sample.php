<?php
/**
 * Sweep — Loops (automatic emails). Copy to the PRIVATE folder, next to billing-config.php:
 *   /home/matnsabc/sweep-private/loops-config.php
 * Loops → Settings → API → Generate key, then paste it below. Empty key = off: no contact, no event, the app works as before.
 * Then the first run of loops/cron.php (ops/CRON.md) creates the contact properties in Loops and the events start.
 */
return [
    'api_key' => '',
];
