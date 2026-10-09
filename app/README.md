# Sweep — app.makeitsweep.com

Application web de Sweep : journal, habitudes, edge, comptes de prop firms, payouts et dépenses.
Stack : `app.html` + `api.php` + SQLite, sur hébergement cPanel avec PHP 8.1 ou plus récent (aucun Node.js requis).

## Contenu du dossier

| Fichier ou dossier | Rôle |
|---|---|
| `app.html` | Coquille de l'application, servie seulement aux personnes connectées |
| `auth.html` | Écran de connexion, d'inscription et de réinitialisation |
| `assets/` | Code et style de l'application ; les noms changent à chaque version, et le navigateur les garde en cache |
| `api.php`, `econ.php` | Serveur : comptes, données, calendrier économique |
| `growth/` | Parrainage (/r/CODE) et Feedback |
| `billing/` | Forfaits Free / Pro / Elite et paiements Stripe, actifs seulement si `sweep-private/billing-config.php` existe |
| `ai/` | Module Sweep AI (serveur), activé seulement si `sweep-private/ai-config.php` contient une clé |
| `icons/`, `social/`, `site.webmanifest` | Icônes, image de partage, installation sur l'écran d'accueil |
| `img/` | Aperçus de l'app (EN/FR/ES) montrés sur l'écran de connexion sur grand écran |
| `econ-us-2026-2027.json`, `econ-profiles.json` | Calendrier économique américain et fiches des indicateurs |
| `config.sample.php` | Modèle de configuration à copier en `config.php` |
| `.htaccess` | Redirection HTTPS, réécriture des adresses, protection des fichiers sensibles |

## Installation sur app.makeitsweep.com

1. **cPanel → Domains → Create a new domain** : `app.makeitsweep.com`, avec son propre dossier, par exemple `/home/USER/app.makeitsweep.com`.
2. **cPanel → SSL/TLS Status** : lance AutoSSL pour le sous-domaine.
3. **MultiPHP Manager** : choisis PHP 8.1 ou plus récent pour le sous-domaine.
4. Envoie le zip dans ce dossier, puis **Extraire**.
5. **Crée le dossier de données hors du web**, par exemple `/home/USER/sweep-data`.
6. **Copie `config.sample.php` en `config.php`** et remplis-le :
   - `user` et `password` : le compte administrateur, créé au premier lancement ;
   - `data_dir` : le dossier créé à l'étape 5 ;
   - `mail_from` et `support_email`.
7. **Courriels** :
   - crée l'adresse `no-reply@makeitsweep.com` (cPanel → Email Accounts) ;
   - vérifie que **Email Deliverability** est au vert (DKIM et SPF) pour `makeitsweep.com`.

   Sans ça, les liens de réinitialisation risquent d'arriver dans les indésirables, ou pas du tout.
8. Ouvre https://app.makeitsweep.com, connecte-toi avec le compte administrateur, et vérifie tout.

## Reprendre les données de trade.agencedeclic.ca

- Copie le dossier `data/` de l'ancien site (`journal.db` et `uploads/`) dans le nouveau `data_dir`.
- Les comptes et l'historique sont conservés. La base se met à jour automatiquement au premier chargement (courriel, consentement, jetons de réinitialisation).
- Les anciens comptes n'ont pas de courriel : chaque trader peut l'ajouter dans **Réglages → Ton compte**. Sans courriel, la réinitialisation se fait avec un code de récupération ou par l'administrateur.
- Pour rediriger l'ancienne adresse, place ce fichier `.htaccess` à la racine de l'ancien site :
  ```
  RewriteEngine On
  RewriteRule ^(.*)$ https://app.makeitsweep.com/$1 [R=301,L]
  ```

## Comptes publics

- **Inscription ouverte** : nom d'utilisateur, courriel, mot de passe (10 caractères ou plus) et case obligatoire « 18 ans ou plus + Conditions et Politique de confidentialité ». La date d'acceptation est enregistrée.
- `https://app.makeitsweep.com/?signup=1` ouvre directement l'inscription. C'est le lien du bouton « Créer un compte » du site.
- **Connexion** avec le nom d'utilisateur ou le courriel.
- **Mot de passe oublié** : un lien valide une heure, utilisable une seule fois, est envoyé par courriel dans la langue du trader. Le code de récupération reste une alternative.
- **Protections** :
  - limite de tentatives (connexion, inscription, réinitialisation) ;
  - champ piège anti-robots et délai minimum avant l'envoi du formulaire ;
  - mots de passe chiffrés avec `password_hash()` ;
  - chaque trader ne voit que ses propres données.
- **Suppression de compte** : chaque trader peut supprimer lui-même son compte et toutes ses données (Réglages). **Export** de toutes ses données en JSON.
- Le mode d'inscription (ouvert, sur invitation, fermé) se change dans la page **Traders**, réservée à l'administrateur.

## Sweep AI (optionnel)

- **Fichiers** :
  - le module serveur est dans `ai/` ; son `.htaccess` bloque tout accès direct ;
  - l'interface fait partie de `assets/`.
- **Réglages privés et clé Gemini** : dans `/home/USER/sweep-private/ai-config.php`, **hors** du dossier web. Ce fichier est trouvé automatiquement si le dossier de l'app est directement dans le dossier personnel (`/home/USER/app.makeitsweep.com`). Sinon, mets son chemin complet dans `config.php` → `'ai_config'`.
- **Sans clé** (ou avec `'enabled' => false`), aucun bouton IA n'apparaît.
- **Points d'entrée** :

  | Où | Action |
  |---|---|
  | Ticket (nouveau trade) | « Saisir avec l'IA » |
  | Fiche d'un trade | « Avis de l'IA », « Suggérer un setup » |
  | Bilan de la semaine | « Bilan IA » |
  | Journal du jour | « Débriefer ma journée » |
  | Payouts et dépenses | « Scanner un reçu » |
  | Menu More, palette ⌘K | Accès à Sweep AI |

- **Calendrier économique avec l'IA** :
  - après chaque publication américaine (élevée ou moyenne), Sweep AI cherche sur Google les valeurs officielles (réel, consensus, précédent, révision) et les enregistre ;
  - il remplit aussi le consensus des 7 prochains jours ;
  - **1 minute après la publication**, il rédige un récap éclair (le chiffre, l'écart avec les attentes, ce que ça signifie) ; **à 30 minutes**, un rapport complet avec la réaction du marché (NQ, ES, taux 10 ans, dollar) ; une dernière mise à jour à 3 heures. Le tout avec les sources, mis en cache pour tous et dans chaque langue.
  - La mise à jour se déclenche quand un trader ouvre l'app. Plafond : 60 recherches par jour (`'econ_daily_calls'` dans `ai-config.php`), en plus du budget global.
  - Google offre 5 000 recherches par mois, puis facture 14 $ les 1 000.
- **Ask Sweep** : la bulle en bas à droite répond aux questions sur les trades du trader, les nouvelles du jour et l'utilisation de l'app. Chaque message compte comme une action IA dans la limite quotidienne.
- **Coûts** :
  - les limites (par trader et par jour, budget global quotidien, cache de 30 jours) se règlent dans `ai-config.php` ;
  - la page **Traders** (administrateur) montre les appels et le coût des 14 derniers jours.
- **Confidentialité** :
  - rien n'est envoyé à Google Gemini tant que le trader ne touche pas une action IA ;
  - **Réglages → Sweep AI** l'explique au trader ;
  - supprimer un compte supprime aussi son historique IA.

## Synchronisation entre appareils

L'app recharge les données quand elle revient au premier plan, puis toutes les 60 secondes tant qu'elle est visible. Sur téléphone, on peut aussi tirer l'écran vers le bas pour actualiser. Ça ne se déclenche jamais pendant une saisie ou un enregistrement en cours.

## Forfaits et paiements (Stripe)

- **Fichiers** :
  - le module serveur est dans `billing/` ; son `.htaccess` bloque l'accès direct ;
  - l'interface (paywalls, bannière, écran Forfait) fait partie de `assets/`.
- **Réglages privés** : `/home/USER/sweep-private/billing-config.php`, à côté de `ai-config.php`. Ce fichier contient les prix, les dates, les limites et les clés Stripe. Sans lui, l'app fonctionne comme avant, sans forfaits.
- **Avant le lancement** : avec `'live' => false`, tout le monde a Elite, aucun paywall ne s'affiche et aucun appel Stripe n'est fait.
- **Tester sans toucher aux autres** : mets ton identifiant dans `'test_users' => ['ton-id']`. La facturation est active seulement pour toi : paywalls, paiement Stripe en mode test, et la raison exacte d'une erreur Stripe affichée sous le bouton.
- **Webhook Stripe** : `https://app.makeitsweep.com/api/billing/webhook`. Les événements à cocher sont :
  - `checkout.session.completed`
  - `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`
  - `invoice.paid`, `invoice.payment_failed`
- **Les règles sont appliquées par le serveur** :
  - comptes au-delà de la limite mis en pause (lecture seule, jamais supprimés) ;
  - payouts et dépenses ;
  - quotas Sweep AI selon le forfait (le budget global quotidien reste le plafond de sécurité).

  Les suppressions ne sont jamais bloquées, et les données d'exemple ne comptent pas.
- **Suppression d'un compte Sweep** : son abonnement Stripe est annulé et ses données de facturation sont effacées.

## Parrainage et feedback

- **Fichiers** : le module serveur est dans `growth/` (son `.htaccess` bloque l'accès direct). Les tables se créent seules : `ref_users`, `referrals`, `referral_clicks`, `feedback`.
- **Lien d'invitation** : `https://app.makeitsweep.com/r/CODE`. Il pose un témoin de 60 jours, valable aussi sur makeitsweep.com, puis ouvre l'inscription avec « Invité par … ».
- **Règles** :
  - l'ami reçoit 30 jours de Pro à l'inscription ;
  - le parrain gagne un mois quand l'ami ajoute 10 trades sur 3 jours dans ses 30 premiers jours, ou paie une première facture ;
  - un parrain payant reçoit un crédit Stripe d'un mois sur sa prochaine facture, un parrain gratuit reçoit 30 jours de Pro ;
  - maximum 12 mois par année ;
  - même connexion que le parrain → à vérifier dans la page Traders.

  Ces valeurs sont modifiables en haut de `growth/referral.php`.
- **Vérification quotidienne** (rattrapage et expiration) : lancée automatiquement par l'utilisation de l'app. Aucune tâche cron n'est nécessaire.
- **Feedback** :
  - captures d'écran stockées dans le dossier de données (`data_dir/feedback/`) ;
  - un courriel est envoyé à `support_email` à chaque envoi ;
  - les réponses et les statuts se gèrent dans la page Traders, section Feedback.
- **Optionnel** : `'referral_salt'` dans `config.php` (sel pour hacher les adresses IP ; par défaut, un sel dérivé de ta configuration).

## Gamification « Sweep the day » (V1)

- **Fichiers** : moteur serveur dans `game/` (`game.php`, `catalog.php`, `cron.php`, `migrations/`), interface dans `assets/game.*.js` et `assets/game.*.css`.
- **Tables** : `user_game_profile`, `game_days`, `xp_events`, `user_badges`, `game_celebrations`, `market_holidays`, `game_analytics`, créées toutes seules au premier usage. Aucune table existante n'est modifiée.
- **Plan et revue** : enregistrés dans la page de journal du jour (`pre` et `post`), donc visibles aussi dans l'onglet Journal. La journalisation d'un trade (setup, émotion, règles suivies) est enregistrée dans le trade.
- **Journée de trading** : un trade pris à 18 h ET ou plus tard compte pour le lendemain. Week-ends et fériés (table `market_holidays`) sont neutres.
- **Verrouillage** : chaque journée reste modifiable jusqu'au lendemain 23 h 59 ET. Le verrouillage et le streak sont calculés à l'ouverture de l'app et par la tâche cron (même résultat).
- **Cron (recommandé)** : cPanel → Cron Jobs → une fois par heure : `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/game/cron.php >/dev/null 2>&1`
- **Jours fériés** : 12 mois déjà inclus. Pour l'année suivante, ajoute les dates dans la table `market_holidays` (voir `game/migrations/001_game.sql`).
- **Forfaits** : tout est gratuit. Seul le nombre de gels par semaine dépend du forfait (Gratuit 1, Pro 2, Elite 3 ; Pro pendant l'accès anticipé).

## Prise en charge des nouveaux utilisateurs (guide)

`assets/guide.*.js` / `guide.*.css` : visite guidée de l'Aperçu (une fois, après le premier compte ; relançable dans Réglages → Guide et aide), astuce à la première visite de chaque page, checklist « Bien démarrer » (7 étapes détectées automatiquement), centre d'aide avec recherche (bouton « ? » à côté de la cloche). Articles en FR/EN/ES dans la constante `A`. État gardé sur l'appareil (`localStorage`, clé `sw.guide`).

## Export complet et préréglages de prop firm

- **Export en un clic** : Réglages → « Tout exporter (ZIP) » → `api/export/full` (code : `export/export.php`). Contient `sweep-backup.json` (réimportable), `trades.csv`, `accounts.csv`, `payouts.csv`, `expenses.csv`, `journals.csv` et `screenshots/` (si ≤ 200 Mo). Aucune extension PHP zip nécessaire. Limite : 6 exports par heure.
- **Préréglages** : dans le formulaire « Ajouter un compte » et sur la page d'un compte (« Appliquer un préréglage »). Valeurs de la phase d'évaluation, **à vérifier** auprès de chaque firme ; elles sont dans `assets/ux.*.js` (section 11, constante `P`).

## Graphiques réels (Databento + Lightweight Charts)

- **Code** : `chart/` (client Databento, cache, API `api/chart/bars`, cron). **Clé** : `/home/<user>/sweep-private/chart-config.php` uniquement (modèle : `chart/chart-config.sample.php`).
- **Délai de licence** : `chart_data_min_age_hours` = 24 tant que la licence de redistribution CME n'est pas confirmée. Aucune barre plus récente n'est servie.
- **Cache** : `sweep-private/bars/` (un fichier par instrument et par journée de séance, partagé par tous). Budget quotidien : `chart_daily_budget_usd`. Journal des appels : table `chart_fetch_log`.
- **Cron (toutes les heures)** : `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/chart/cron.php >/dev/null 2>&1`
- **Librairie** : `assets/vendor/lightweight-charts.5.2.1.standalone.production.js` (Apache-2.0, version épinglée). Le logo d'attribution TradingView reste affiché ; mention dans le bas des Réglages.

### Checklist de test (section 12)
1. Trade NQ d'il y a 3 jours : bougies, entrée, sortie, stop, objectif et zone au bon endroit.
2. Trade MNQ : barres NQ ; contrat affiché correct, y compris pendant une semaine de roulement (vérifier sous le graphique).
3. Deux comptes avec un trade NQ le même jour : un seul appel `get_range` dans `chart_fetch_log`.
4. Trade d'il y a 2 h : carte « disponible {date} » ; le graphique apparaît après le cron une fois le délai passé.
5. `api/chart/bars?symbol=NQ&from=…&to=<maintenant>` : aucune barre de moins de 24 h.
6. Formulaire : toucher une bougie remplit heure + prix au tick ; glisser le stop met à jour le champ ; taper un prix déplace la ligne.
7. Budget à 0.01 dans la config : état « bientôt », alerte dans `error_log`, aucun appel.
8. Logo TradingView visible ; lien tradingview.com en bas des Réglages.
9. Clair / foncé, iPhone Safari et ordinateur ; pincer pour zoomer fluide.
10. Rechercher la clé dans les réponses de l'API et les fichiers publics : jamais présente.
11. Retirer temporairement la clé : récap et formulaire fonctionnent sans graphique.

## Couche d'expérience (design et animations)

- **Fichiers** : `assets/ux.*.css` et `assets/ux.*.js`, chargés après l'app. Ils ne touchent ni aux données ni à la logique : si un navigateur ne supporte pas une fonction, l'app se comporte comme avant.
- **Téléphone** : barre d'onglets qui se compacte quand on fait défiler vers le bas (style iOS), cachée pendant la saisie pour que le clavier ne la pousse pas sur un champ, menu « Plus » en feuille du bas avec tuiles, ligne de séparation du haut seulement quand le contenu passe dessous, toucher l'onglet actif remonte en haut.
- **Transitions entre les pages** (Safari 18+, Chrome) : glissement dans le sens de la navigation ; fondu sur ordinateur.
- **Performance** : le flou d'arrière-plan est retiré des cartes sur téléphone (principale cause de saccades au défilement) ; il reste sur la barre du haut, la barre d'onglets et les feuilles.
- **Écran de connexion** : sous-titre de valeur, entrée animée, onglets à indicateur glissant, et sur téléphone un aperçu de l'app et les 3 bénéfices sous le formulaire.
- Tout respecte « Réduire les animations » du téléphone.

## Notifications dans l'app

- **Fichiers** : le module serveur est dans `notify/` (son `.htaccess` bloque l'accès direct) ; l'interface est dans `assets/notify.*.js` et `assets/notify.*.css`.
- **Tables** : `notifications` et `notification_prefs`, créées toutes seules au premier usage (le SQL est aussi dans `notify/migrations/`).
- **Cloche** en haut de l'app, avec le nombre de non-lues ; la liste s'ouvre en feuille (Aujourd'hui / Cette semaine / Plus tôt).
- **Célébrations** : affichées une seule fois en fenêtre au centre, à la prochaine ouverture de l'app (une seule par ouverture, les autres restent dans la liste).
- **Réglages → Notifications** : un interrupteur par catégorie (nouveautés, accomplissements, alertes prop firm, séries, compte et données).
- **Limite** : 5 notifications normales par trader par 24 h (`config.php` → `'notifications' => ['daily_limit' => 5]`) ; les célébrations ne comptent pas.
- **Événements** : `api.php` déclenche `trade.created/updated/deleted`, `account.*`, `journal.saved`, `payout.recorded/updated/paid/deleted`, `feedback.status_changed` et `user.signed_in`. Les écouteurs sont dans `notify/listeners.php` ; une erreur dans un écouteur est notée dans le journal d'erreurs et ne bloque jamais l'enregistrement.
- **Test** (administrateur) : Réglages → Notifications → « Envoyer une notification » ou « Envoyer une célébration ».
- Aucune tâche cron n'est nécessaire.

## Campagne « 100 traders »

- **Attribution** : à l'inscription, les tags UTM du témoin `sweep_utm` posé par le site sont enregistrés sur le trader (première visite seulement ; jamais bloquant). Les deux questions facultatives aussi : « Où as-tu découvert Sweep ? » et « Combien de comptes… ».
- **Compteur public** : `https://app.makeitsweep.com/api/cohort-count.php` → `{"taken": 37, "total": 100}`.
  - Mis en cache 60 s et lisible seulement depuis makeitsweep.com.
  - Réglages dans `config.php` → `'cohort'` (date de départ, total, et compter les inscriptions ou les traders activés).
- **Comptes internes ou de test** : Traders → Gérer → « Compte interne / de test ». Ils sont exclus du compteur et du rapport.
- **Rapport d'attribution** : page Traders → « Attribution des campagnes », avec par publication les inscriptions, les activés, 3 jours ou plus, J7 et J14. Le bouton « Copier pour le tableur » copie le tableau.

## Mise à jour

Envoie le nouveau zip et clique **Extraire** : `config.php` et le dossier de données ne sont jamais remplacés. Les anciens fichiers de `assets/` peuvent être supprimés.

## Sauvegardes

Le dossier `data_dir` contient tout : `journal.db` et `uploads/`. Compresse-le et télécharge-le régulièrement (cPanel → File Manager → Compress), ou programme une tâche cron.

## Fournisseurs optionnels (`config.php`)

| Service | Réglages | Rôle |
|---|---|---|
| Calendrier économique | `econ_provider` (`manual` par défaut, `tradingeconomics`, `fmp`, `finnhub`) et `econ_api_key` | Valeurs réelles des annonces |
| Données de marché | `market_provider => 'databento'` et `market_api_key` | Chandelles et réaction du NQ |

## Sauvegardes (ops/)

- `ops/backup.php` (cron **chaque jour**, ex. 3 h 30) : copie à chaud de SQLite (`VACUUM INTO`), vérification d'intégrité, compression, chiffrement AES-256-GCM, rotation 7 jours / 4 semaines / 12 mois dans `/home/<user>/sweep-backups`, archive hebdomadaire des captures et de la config privée, copie hors serveur S3 compatible (facultative).
- `ops/restore-test.php` (cron **chaque semaine**) : déchiffre la dernière sauvegarde, vérifie qu'elle s'ouvre et contient les mêmes utilisateurs, et contrôle l'intégrité de la base en production. Le rapport envoyé par courriel par cPanel sert de preuve.
- `ops/restore.php <fichier.enc> <sortie>` : restauration manuelle.
- Config : `sweep-private/backup-config.php` (modèle `ops/backup-config.sample.php`). **Garde la phrase de passe hors du serveur** : sans elle, aucune sauvegarde n'est lisible.

## Offres de campagne, parrainage et déblocage progressif

- **Cohorte « 100 traders »** : à l'inscription, `utm_campaign` (normalisé : minuscules, lettres et chiffres) donne un bonus en plus de l'essai Pro pour tous. Par défaut : `100`, `100traders`, `100futurestraders`, `lookingfor100`, `lookingfor100futurestraders`, `founding100` → **30 jours d'Elite**. Modifiable dans `billing-config.php` (`campaign_grants`).
- **Parrainage** : le filleul reçoit **14 jours d'Elite** en plus de l'essai Pro (`growth/referral.php`, `REF_REFEREE_DAYS`, `REF_REFEREE_PLAN`). Le parrain gagne toujours un mois.
- **Déblocage progressif** (`game/catalog.php`, `GAME_UNLOCKS`) : missions après la 1re journée balayée, revue du vendredi après 2, boss au niveau 3 ou après 10 trades, saisons, ligues et crew après 7 jours. Les traders déjà actifs gardent tout. Les limites des forfaits s'appliquent toujours en plus.

## Tests et tableau de bord

- `php ops/tests.php` (sur le serveur, base jetable, jamais la vraie) : forfaits dans le temps (essai, bonus de campagne, jour 61), comptes gelés après une rétrogradation, garde d'écriture, bonus de parrainage, déblocage progressif.
- `tests/e2e_prop_rules.py` et `tests/e2e_isolation.py` (environnement de développement avec Playwright, pas sur le serveur) : calculs de drawdown et de consistance dans le navigateur, isolation des données entre deux traders. Lancés avant chaque livraison.
- **Admin → Tableau de bord** (`api/admin/metrics`, `ops/metrics.php`) : étoile polaire (traders avec 3+ journées balayées sur 7 jours), activation 24 h, 1re journée balayée en 7 jours, rétention semaine 2, inscriptions par source, saisie des trades, coût IA, erreurs navigateur et serveur, revenu mensuel estimé.
- Les erreurs JavaScript des traders sont envoyées à `api/client-error` (5 par page au maximum, 30 par heure par compte).

## Préproduction, rappels de fin d'essai, « graphique prêt »

- **Préproduction** : `php ops/staging-copy.php /home/matnsabc/trade.agencedeclic.ca/data/journal.db` copie la base de production vers le site de test, **anonymisée** (courriels remplacés, mots de passe des traders remplacés, sessions, Stripe et Discord retirés ; les administrateurs gardent leur mot de passe). Refuse d'écrire sur la base de production. Teste chaque zip sur le site de test avant la production.
- **Migrations** : chaque module crée et complète ses tables tout seul, une seule fois (`CREATE TABLE IF NOT EXISTS`, colonnes ajoutées si absentes) ; les fichiers `game/migrations/*.sql` documentent chaque étape.
- **Fin d'essai** : rappels in-app aux jours 50 et 58 (10 et 2 jours restants) avec ce que le trader a utilisé ; jamais pendant les heures de marché ; rien n'est supprimé au jour 61.
- **« Ton graphique NQ est prêt »** : envoyé par le cron des graphiques, une fois par trader et par journée, quand le graphique devient disponible (après 16 h ET si c'est pendant la séance).
- **Tests d'interface** : `tests/e2e_ui.py` (toutes les pages, 4 configurations, textes anglais oubliés en français).

## Imports CSV (Tradovate, Rithmic, TopstepX)

La page Importer détecte le format toute seule : rapport « Performance » de Tradovate, export « Orders History → Completed Orders » de Rithmic R|Trader Pro (exécutions regroupées en allers-retours, sorties partielles et frais compris), export « Trades » de TopstepX (heures UTC converties à l'heure de New York). Les frais du fichier sont conservés. Réimporter le même fichier ne crée aucun doublon. Fichiers d'exemple fictifs : `tests/samples/`.

## Navigation (livraison A de la refonte)

- `assets/nav.*.js` / `nav.*.css` : segments Trades (Liste · Calendrier · Journal) et Comptes (Comptes · Payouts et dépenses), chevron de retour des sous-pages, menu de l'avatar (téléphone et ordinateur), Progression dans la barre latérale, alias d'adresses (`#today`, `#stats`, `#subscription`, `#progress`), retour Android / iOS qui ferme d'abord la feuille ouverte, recherche des fonctions et réglages.
- `app.html` : barre d'onglets Aujourd'hui · Trades · + · Stats · Comptes ; barre latérale + Ajouter un trade, Aujourd'hui, Trades, Stats, Comptes, Progression ; pied : recherche, cloche, avatar. La feuille « Plus » n'existe plus.
- Les adresses existantes restent les adresses officielles : les anciens liens fonctionnent sans redirection.
- Glossaire (une seule étiquette par chose) en tête de `assets/i18n-fr.*.js` et `assets/i18n-es.*.js`.
- Livraison B : Aujourd'hui (une action selon l'état de la journée, puis checklist, chiffres du jour et de la semaine, rang et streak, contexte économique), recherche « Rechercher ou demander à Sweep » (dernière ligne : Demander à Sweep ; recherches sans résultat comptées, top 20 dans l'admin), une seule modale automatique par session (le reste en toasts de 3 s), visite en bulles et astuces automatiques retirées.
- Livraison C : Progression allégée (parcours dans la Saison, boss en mission spéciale, collection et profil social dans Progression), Réglages en 4 groupes (Compte, Discipline, Notifications, Données), mini-navigation collante du Bilan du trade, dernier compte et instrument pré-remplis à l'ajout d'un trade.
- `tests/e2e_acceptance.py` : les 6 tâches en 2 touchers ou moins (3 pour l'export), anciennes routes, éléments flottants, à 390 et 1440 px en EN, FR et ES.

## Design tokens and motion

One scale for every stylesheet added on top of the app (reference at the top of `assets/ux.*.css`): radius 4 · 8 · 12 · 16 · 20 · 24 · 999; type 11–17, 20, 22, 24, 30, 36 (16 for form fields); spacing in steps of 2 up to 16, then 4; motion `--sw-ease` / `--sw-spring`, 150 / 250 / 400 ms.

## Stabilité visuelle (tests)
- `tests/e2e_no_jumps.py` : touche les contrôles de chaque page (comme Safari, sans ancrage du défilement, enregistrements lents) et signale tout saut, animation rejouée ou graphique reconstruit.
- `tests/e2e_redraw_no_replay.py` : un redessin de la même page ne rejoue aucune animation.
- `tests/e2e_trade_nojump.py` : le Bilan du trade ne saute pas pendant les réponses.
- Sur téléphone, la page Bilan envoie un « Trade page jump » au tableau de bord admin (Erreurs) si un élément touché bouge.
