<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the automatic emails' earlier texts, as fingerprints (ma_text_sig in mail/mail-auto.php), by version then automation:
 * [en, fr, es]. A text still equal to one of these was never touched in Admin: ma_upgrade puts the new one in its place. Any
 * other text is Mateo's: the new one is only proposed. When the texts change, add the fingerprints of the ones replaced here.
 */
return [
    // version 1 (4 Nov. 2026, c713dab): before the encouragement line and the one-click questions (brief « Courriels de feedback », step 3)
    1 => [
        'signedUp' => ['039743b13868d195', 'a600d1da039868f1', 'e8d414b8e2467c54'],
        'day1Evening' => ['e623d2be8f0f8332', 'd5ccf8a624ed95b4', '09cfd5f95700b3c5'],
        'profileCompleted' => ['5fe25645a0b639dc', 'ed9d4f1d776ccf34', 'a8ca189289bf62ac'],
        'firstAccountAdded' => ['e0abfb8ad5d91af3', '2d9cd60dfaadd880', '233aa9860ced61a6'],
        'firstPlanSaved' => ['556ad1cd8d92f633', '78c1bec3a00f1430', '8adb0958c403e825'],
        'firstTradeLogged' => ['c5b022804fcfe234', '325809279eb47d49', 'a19f093ce6857544'],
        'tradesMilestone' => ['fad72262ccb846eb', '84973747a03acfeb', '3af5e3f37a74024d'],
        'firstPayoutLogged' => ['d66498ee83042be1', '5b6d2a196226903e', '86408b17e103c4fc'],
        'inactive3d' => ['4ea5044365d958c9', 'bdf34ab94eade4cb', 'd4030cf1864837b2'],
        'inactive7d' => ['576464d39559e80e', '1af7fd9bb244f445', '2c8c470c2a64128e'],
        'inactive14d' => ['bd8fb003e72437df', '7ceada1c4bd72507', '8dacae6e4a99936e'],
        'inactive30d' => ['d510d3810757a3d2', '341d4766f81e33e5', '5ea294e37e80f33a'],
        'proTrialDaysLeft' => ['d7de64d656e24006', '4a564d1247f37486', '1a191a69736ec1d8'],
        'proTrialEnded' => ['882a461960ffe791', '65194089044a2855', '536d75137b85eabe'],
        'subscriptionStarted' => ['801db17c1e05fa8d', 'bfeb7e9871766ca7', 'be78644e9e8a7730'],
        'subscriptionCanceled' => ['2607746482de734f', '352c9fa32a4b1538', '51e5131330dbf0a5'],
        'paymentFailed' => ['84af7b86b9189787', 'eee086ab9da054a5', '5b7d12bd84629c1b'],
        'referralRewarded' => ['412e43840bbff597', '24cc43667b87451e', 'bd3922a6f13c38ac'],
    ],
];
