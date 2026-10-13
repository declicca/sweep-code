# NOTES — points vus en passant, à reprendre plus tard

Règle du brief 01 : ce qui n'est pas dans le brief est noté ici au lieu d'être fait.

- **Info-bulle « Marge de drawdown »** (page d'un compte) : le texte mélange les langues en FR/ES (« trailing — end of day », vient de `DD_TYPES` dans `app.js`, non traduit dans la phrase).
- **`ops/staging-copy.php`** copie la base de production vers un site de test : courriels et mots de passe sont masqués, mais les noms, trades et notes des traders restent. Contraire à la règle « ne jamais copier `data/` ». Environnement de test choisi par Mateo le 9 oct. : local seulement.
- **Compression** : NGINX efface `Accept-Encoding` et n'a pas `gzip` (voir CONTEXTE-APP.md, étape 3 de l'audit). Root seulement (HostArmada).
- **`assets/fonts/` et `assets/vendor/`** : cache 1 an `immutable` alors que les noms n'ont pas d'empreinte (changer le nom pour changer une police).
- **Prix des firmes** (brief 01, 1.7) : Apex, Lucid, TPT et MFFU sans prix ; Mateo n'a pas les montants (9 oct.), point passé.
- **« Constance »** (règle de la page du compte) contre **« Consistance »** ailleurs (formulaires, préréglages, ce qui manque pour réussir) : un seul mot à choisir.
- **Tests qui dépendent du jour** (réglé le 9 oct. pour la fin de semaine : `tools/game-now.py`) : `e2e_clarity`, `e2e_session_parity`, `e2e_plan_journal` et `e2e_lot_a` supposent une séance ouverte ; les jours fériés du marché ne sont pas couverts. À revoir à l'étape 2 du brief (`tests/setup.py`).
- **Dépôt GitHub `declicca/sweep-code` public** (vu le 9 oct. : l'API répond sans identification) : tout le code de l'app et du site y est lisible. Aucun secret dedans (`config.php`, `data/`, `sweep-private` hors du dépôt), mais c'est l'équivalent du zip retiré du serveur le même jour. À décider par Mateo (privé = GitHub Actions limité à 2 000 minutes par mois sur le plan gratuit, ~10 min par passage ; `tools/ci-status.py` passe alors par `gh`, à installer et connecter).
- **Positions ouvertes** (brief 02, partie 5, 13 oct.) : Sweep ne les voit pas. La synchro NinjaTrader les compte (`sync_apply` → `open`, `sync/sync-store.php`) sans les garder. La revue est donc proposée à la clôture de 16 h ET, ou plus tôt une fois un trade enregistré et la dernière annonce du jour passée : un trade saisi est un trade fermé. À brancher quand la synchro exposera les positions ouvertes (chantier de la session « Synchronisation automatique »).
- **Notification de revue** (`g_review`, `game/v2c.php`) : toujours de 16 h 30 à 21 h ET, elle ne suit pas encore le moment de la carte (dernière annonce passée). Point laissé tel quel.
- **Paliers Apex** (financé EOD et Intraday) : la limite du jour et les contrats montent avec le profit (4 à 5 paliers). L'app ne garde qu'une valeur (palier 1, la plus stricte) : un trader au palier 3 verra « Limite du jour atteinte » trop tôt. À modéliser si les traders Apex le demandent.
