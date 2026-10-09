<?php
/*
 * Sweep — Discord rank roles. Copy to the PRIVATE folder, next to ai-config.php:
 *   /home/matnsabc/sweep-private/discord-config.php
 *
 * 1. https://discord.com/developers/applications → New Application → OAuth2: copy Client ID and Client Secret,
 *    add the redirect https://app.makeitsweep.com/api/game/discord/callback
 * 2. Bot → Reset Token (copy it). Invite the bot to your server with the « Manage Roles » permission.
 *    In Server Settings → Roles, drag the bot's role ABOVE the rank roles (Discord only lets it manage roles below it).
 * 3. Create one role per rank and paste their IDs (right-click a role → Copy Role ID, with Developer Mode on).
 * 4. Optional: a webhook URL of the channel where big moments are posted (traders choose to share in Settings).
 */
return [
    'client_id'       => '',
    'client_secret'   => '',
    'redirect_uri'    => 'https://app.makeitsweep.com/api/game/discord/callback',
    'bot_token'       => '',
    'guild_id'        => '',     // your server ID
    'rank_roles'      => [       // Sweep rank → Discord role ID
        'rookie' => '', 'apprentice' => '', 'disciplined' => '', 'consistent' => '', 'seasoned' => '', 'master' => '', 'sweeper' => '',
    ],
    'moments_webhook' => '',     // optional
];
