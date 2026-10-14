<?php
/**
 * Sweep — notifications on the phone (web push, VAPID keys). The real file is in the PRIVATE folder:
 *   /home/matnsabc/sweep-private/push-config.php
 * Never by hand and never in git: on the server, once, `php ops/push-keys.php` makes the keys and writes that file (readable
 * by this user only), printing the public key only. No file = off: nothing shows in the app, nothing is sent.
 */
return [
    'public_key'  => '',   // base64url, the uncompressed P-256 point (65 bytes)
    'private_key' => '',   // PEM, EC P-256
    'subject'     => 'mailto:hello@makeitsweep.com',
];
