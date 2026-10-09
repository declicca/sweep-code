<?php
/*
 * Sweep — backups. Copy to /home/matnsabc/sweep-private/backup-config.php
 * The passphrase encrypts every backup: keep a copy somewhere safe OUTSIDE the server (password manager).
 * Without it, backups cannot be read — by anyone, including you.
 */
return [
    'passphrase' => '',                 // long random phrase, e.g. 6+ random words
    'dir' => '/home/matnsabc/sweep-backups',   // outside the web root
    // Off-site copy (recommended): any S3-compatible storage. Example Backblaze B2:
    //   endpoint https://s3.us-west-004.backblazeb2.com, region us-west-004, bucket sweep-backups, key = keyID, secret = applicationKey
    // Then add a lifecycle rule on the bucket (e.g. keep files 365 days).
    's3' => ['endpoint' => '', 'region' => 'auto', 'bucket' => '', 'key' => '', 'secret' => '', 'prefix' => 'sweep'],
];
