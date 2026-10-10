# CONTEXTE-APP — Sweep (app.makeitsweep.com)

Référence pour démarrer une nouvelle conversation.
Version : dépôt git `declicca/sweep-code`, dossier `app/` (9 octobre 2026 : étape 1 du brief + lot A UI/UX + étapes 1 et 2 de l'audit) — point de départ de la prochaine conversation. État des tests : voir « Passation » à la fin.
⚠️ = information que je ne peux pas garantir à jour : vérifie dans le code.

---

## 1. Architecture

- **Stack** : PHP 8.1 + SQLite (`data/journal.db`), sans framework. Hébergement HostArmada (cPanel, `/home/matnsabc/app.makeitsweep.com`). Mise en ligne par `./deploy.sh app` à la racine du dépôt (rsync par SSH, simulation par défaut, `--go` pour envoyer ; il vide le cache NGINX), seulement avec l'accord de Mateo.
- **Front** : `app.html` charge le cœur `assets/app.<hash>.js`, **compilé depuis `src/app.js`** comme les autres modules (depuis le 9 oct., brief 01 étape 3 : version lisible du cœur ; les noms de fonctions sont d'origine, les petites variables locales `e, t, a…` viennent de l'ancien minifieur). **Modifier `src/app.js`, puis `sh tools/build.sh`** ; ne plus jamais patcher `assets/app.*.js` (l'empreinte du nom change toute seule au build). Les modules ci-dessous l'enrichissent : ils enveloppent `render()`, `submitAccount()`, `payoutForm()`, `acctTable()`, etc., et observent le DOM.

| Élément | Rôle |
|---|---|
| `api.php` | Routeur API (`/api/...`), auth, migrations, données, partage public, SMTP, CSP. Aussi : migrations automatiques au chargement de `api/data` (date de séance, types de comptes, abonnements mensuels), envoi groupé `api/docs/batch`, admin préréglages |
| `src/nav.js` / `nav.css` | La majorité de l'UI : Aujourd'hui, routine, formulaires, partage, gestes, design system, lecture de captures (« X trades trouvés »), suppression avec Annuler, équilibrage des colonnes |
| `src/ux.js` | Préréglages et ajout de compte guidé, imports CSV (Tradovate, Rithmic, TopstepX, TradingView), admin, **Mon argent** (`moneyOf`, sections 24-27), sélecteur de type de compte, changement de type d'un compte (section 28), **vrai net dès l'arrivée** (section 29, `SweepRealNet`) |
| `src/game.js` | Anneaux, plan, revue, progression, célébrations (`SweepGame`) |
| `src/guide.js`, `src/chart.js`, `src/notify.js` | Guide, graphique TradingView (chargé à la demande), centre de notifications |
| `assets/` | Fichiers servis : un seul CSS `bundle.<hash>.css`, JS hachés, `fonts/` (Geist local, plus de Google Fonts) |
| `game/game.php` | Règles du jeu serveur (anneaux, « dans ton plan », journée réussie, date de séance) |
| `game/cron.php` | Jeu (toutes les 15 min). Le 1er du mois, il envoie aussi « La réalité du mois » via `money/money.php` ; le vendredi dès 17 h 30 ET, le courriel « Ta semaine » (`game/weekly-mail.php`) |
| `money/money.php` | Calcul serveur de l'argent réel du mois, mêmes règles que `moneyOf()` (test de parité) |
| `presets/` | `seed.json` (catalogue), `presets-lib.php` (fusion, validation), `check.php` (vérification d'une firme), `cron.php` (vérification hebdomadaire) |
| `ai/` | Sweep AI (Gemini) : `ai-core.php`, `ai-features.php`, `ai-routes.php`, `ai-stats.php` (table des contrats), `shot-trades.php` (construction des trades depuis une capture), `econ-ai.php` |
| `notify/`, `chart/`, `billing/`, `growth/`, `econ.php` | Notifications et envoi des courriels (`notify/mail.php` : `sweep_mail()`, partagée par `api.php` et les tâches cron), bougies (cron horaire), forfaits Free/Pro/Elite + Stripe, partage public, calendrier économique |
| `ops/` | `build-assets.sh`, `css-order.txt`, `tests.php`, `metrics.php`, sauvegardes |
| `tests/` | `run-all.sh`, tests PHP (`presets_test.php`, `shot_trades_test.php`), Playwright `e2e_*.py`, `samples/` |

## 2. Build et livraison

- **Build** : `sh ops/build-assets.sh` (ou `sh tools/build.sh`, qui vérifie d'abord la syntaxe). Il minifie les JS de `src/` (dont `app.js`, le cœur) en `assets/<nom>.<hash10>.js`, regroupe tous les CSS dans **un seul** `assets/bundle.<hash>.css` (ordre dans `ops/css-order.txt`, `nav.css` en dernier ; `app.*.css` n'a pas de source dans `src/`) et réécrit `app.html`.
- **Avant un déploiement** :
  - `node --check` sur chaque JS de `assets/` ;
  - `php -l` sur les PHP modifiés ;
  - `tests/run-all.sh` complet ;
  - vérifier que `app.html` est identique à celui qui a été testé.
- **Commits du site d'une autre session** : depuis le 10 oct., ils ne bloquent plus `deploy.sh app` (avant : refus « ce commit n'est pas poussé », contourné une fois par une copie propre `git worktree`). Ne jamais pousser leur travail sans l'accord de Mateo.
- **Déploiement** : `./deploy.sh app` n'envoie ni `config.php`, ni `data/`, ni `src/`, `tests/`, `tools/`, `CLAUDE.md`, `CONTEXTE-APP.md`. Ne jamais laisser de zip du code dans le dossier web (un `sweep-app-base.zip` y était téléchargeable publiquement ; supprimé le 9 oct.).

## 3. Environnement local (Mac de Mateo, depuis le 9 octobre)

- **Outils** (Homebrew) : `php` (8.5 en local, 8.1 en production), `coreutils` et `gnu-sed` (le build utilise `md5sum` et `sed -i` de Linux), Node avec `terser` et `csso-cli` (`npm install -g`). Python : environnement `~/.venvs/sweep` (Playwright + Chromium, fonttools, brotli, Pillow, uharfbuzz), créé avec `uv`.
- **Scripts dans `app/tools/`** (jamais dans `/tmp`, exclus du déploiement) :
  - `sync.sh [dossier]` : copie `app/` vers la copie servie (`/tmp/g` par défaut) sans `data/` ni `config.php`, puis installe `router.php` et `config.local.php` (mateo, mot de passe de test local, SMTP vide) ;
  - `router.php` : routeur de `php -S` qui reproduit le `.htaccess` ;
  - `run.sh <commande>` : démarre `php -S 127.0.0.1:8095` sur la copie servie (`PORT=`, `DEST=` pour une autre), avec préréglages et Sweep AI simulés (`ai-config.local.php`, `SWEEP_AI_MOCK`), lance la commande, puis arrête le serveur ;
  - `fresh.sh` (base vide), `full.sh` (fresh + `run-all.sh`) ; la préparation des tests est dans `tests/setup.py` (voir section 4) ;
  - `ci-status.py` : résultat du passage « Tests » de GitHub Actions pour un commit (utilisé par `deploy.sh`) ;
  - `build.sh` : `node --check` de chaque `src/*.js` puis `ops/build-assets.sh` (le build reproduit exactement les empreintes d'App 3) ;
  - mesures : `gzproxy.py` (relais gzip devant `php -S`), `perf.py` (A/B en alternance, médiane : FCP, LCP, TBT, temps script / style / mise en page, CLS, poids), `profile.py` (profil CPU d'un chargement), `shifts.py` (décalages de mise en page élément par élément), `pixdiff.py` (captures A/B comparées au pixel) ;
  - `subset-fonts.py` : sous-ensemble des polices à partir des originaux de `tools/fonts-src/`.
  - `game-now.py` : pendant la fin de semaine du marché (vendredi 17 h → dimanche 18 h ET), `run.sh` et `par.py` fixent l'heure du jeu côté serveur au vendredi 15 h ET (`SWEEP_GAME_NOW`, déjà prévu dans `game/game.php`). Sans ça, `e2e_clarity`, `e2e_session_parity`, `e2e_plan_journal` et `e2e_lot_a` échouent le week-end (aucune séance ouverte). Les autres jours : heure réelle.
- **Suite complète** : `sh tools/sync.sh && sh tools/run.sh sh tools/full.sh > log 2>&1` (~35 min, en arrière-plan).
- **Comparer l'ancien et le nouveau code** : une deuxième copie (`sh tools/sync.sh /tmp/g2` depuis l'ancien code) avec **la même base** (`cp -R /tmp/g/data /tmp/g2/`), servies sur 8095 et 8096, chacune derrière `gzproxy.py` (9095, 9096). La session de test vaut pour les deux, mais `localStorage` dépend du port : `perf.py` et `pixdiff.py` recopient celui de la session pour chaque adresse (sans ça, les deux copies n'affichent pas la même période).
- **Compte de test** : `/tmp/show_state.json` (Mateo, données d'exemple). Pour un nouveau compte dans un test : `POST /api/auth/register` puis `/api/me/profile`. Toutes les requêtes `POST /api/...` portent l'en-tête `X-Requested-With: fetch`.
- `e2e_no_jumps` et `e2e_acceptance` sont câblés sur le port 8095 (ils ne lisent pas l'adresse passée en argument).
- Les captures pleine page (`full_page=True`) peuvent laisser des zones vides dans les longues listes : vérifier à l'écran en faisant défiler avant de conclure à un bug.
- Une optimisation de `app.css` (`.tbl tbody tr{content-visibility:auto;contain-intrinsic-size:auto 60px}`) fait sauter les listes dont les lignes ne font pas ~60 px : les comptes en sont exclus, les trades réservent 43 px sur ordinateur.
- **Pièges** :
  - **limiteur de tentatives** : `run-all.sh` vide la table `attempts` avant chaque test si `SWEEP_TEST_DB` est défini (c'est le cas dans `full.sh`) ;
  - **ne jamais écrire `pkill -f "php -S"` dans une commande** : ça tue la commande elle-même (arrêter par port : `lsof -ti tcp:8095 -sTCP:LISTEN | xargs kill`) ;
  - **`sessionStorage sw.modal=1`** supprime les fenêtres de première visite ;
  - **`await pg.evaluate("impGo()")`** échoue parfois (passage à #trades pendant l'attente) : utiliser `void impGo()`.
  - **`html, body { overflow-x: clip }`** (`app.css`) : un élément qui dépasse à droite est coupé, sans défilement. Sur le Mac, `document.documentElement.scrollWidth` ne voit pas ce dépassement ; sur Linux (GitHub), si. Pour savoir ce qui dépasse, mesurer les éléments, le texte et les pseudo-éléments (fonction `WIDE` de `tests/e2e_weekly_share.py`).

## 4. Tests

- **Préparation** : `tests/setup.py` (lancé par `run-all.sh`, sauf `SWEEP_NO_SETUP=1`) connecte le trader de test « mateo » avec le mot de passe local de `tools/config.local.php`, remplit son profil, ajoute les données d'exemple une seule fois et enregistre la session (`/tmp/show_state.json`). Aucun test ne dépend plus d'un fichier qui pourrait manquer. Son navigateur ignore la CSP de l'app (`bypass_csp`) : les attentes de Playwright évaluent leur condition.
- **GitHub Actions** (`.github/workflows/tests.yml`) : à chaque push **qui touche `app/`** (ou ce fichier ; un commit du site ne lance ni n'annule rien), `tools/par.py 3` sur Ubuntu avec **PHP 8.1** (comme la production) ; une **annotation par test échoué** (lisible sans identification, affichée par `tools/ci-status.py` et donc par `deploy.sh` quand il refuse) ; journaux en pièce jointe si échec. Un push plus récent annule le passage en cours (« cancelled ») : c'est le passage du dernier commit qui compte. Un test ne doit pas dépendre des comptes laissés par les autres tests du même groupe (la carte Comptes d'Aujourd'hui en montre 6 au plus) : créer son propre trader si besoin. **`./deploy.sh app --go` refuse** : changements non commités dans `app/`, `app/` différent sur GitHub (commit de l'app pas poussé), ou tests en cours / en échec pour **le dernier commit qui a modifié `app/`** (`tools/ci-status.py`). GitHub ne teste que le dernier commit de chaque push : si un commit du site a été poussé avec celui de l'app (même `app/`), c'est son passage qui compte (avant le 10 oct., `deploy.sh` refusait à tort dans ce cas) ; un passage annulé est ignoré. Les commits du site, poussés ou non, ne comptent pas.
- **Suite répartie (à préférer)** : `python3 tools/par.py 3` lance la suite sur 3 copies en même temps (`/tmp/g`, `/tmp/g_2`, `/tmp/g_3` ; ports 8095, 8295, 8395), chacune avec sa base et sa session ; les adresses écrites en dur dans les tests sont réécrites dans la copie de chaque groupe seulement. Groupes équilibrés sur les durées du passage précédent (`tools/test-times.json`). **31/31 en 9 min 38 s** (contre ~35 min en série) ; les serveurs locaux tournent avec `PHP_CLI_SERVER_WORKERS=4` (sinon une requête lente bloque la page).
- **Suite complète** : `tests/run-all.sh BASE STATE` → « N réussis, N échoués ». 42 tests au 10 octobre (`ops/tests.php` + 4 tests PHP + 37 Playwright, dont `e2e_rule_parity`, `e2e_drawdown_kinds`, `e2e_money_views`, `e2e_admin_metrics`, `e2e_weekly_card`, `e2e_weekly_content`, `e2e_weekly_parity` et `e2e_weekly_share`) :
  - **serveur** : `ops/tests.php` (20 : forfaits, essai, gel des comptes après un passage à Free, garde d'écriture, parrainage, déblocage du jeu) ;
  - **PHP** : `presets_test.php` (41), `shot_trades_test.php` (32) ;
  - **Playwright** :
    - `e2e_session_parity`, `e2e_accuracy`, `e2e_clarity`, `e2e_a11y_names` ;
    - `e2e_import_session_day`, `e2e_delete_undo_copy_dates`, `e2e_session_news_ui` ;
    - `e2e_presets_firms`, `e2e_prop_rules`, `e2e_isolation`, `e2e_eval_to_funded`, `e2e_payout_conditions`, `e2e_live_accounts` ;
    - `e2e_acceptance`, `e2e_no_english_in_fr_es`, `e2e_redraw_no_replay`, `e2e_no_jumps`, `e2e_quiet_sync`, `e2e_history_back` ;
    - `e2e_rows_open`, `e2e_plan_journal`, `e2e_import_tradingview`, `e2e_visual_fit` ;
    - `e2e_money`, `e2e_money_parity`, `e2e_shot_multi` (nécessite `run_ai.sh`), `e2e_scroll_stable`, `e2e_realnet`, `e2e_lot_a`.
  - Les 111 anciens scripts d'exploration (aucune vérification) ont été **retirés** le 9 oct. : liste dans `tests/RETIRED.md`, récupérables dans git. `--all` n'existe plus.
- **Tests par sujet** :

| Sujet | Tests |
|---|---|
| Préréglages, règles | `presets_test.php`, `e2e_presets_firms`, `e2e_prop_rules`, `e2e_eval_to_funded`, `e2e_payout_conditions` |
| Date de séance, news | `e2e_session_parity`, `e2e_import_session_day`, `e2e_session_news_ui` |
| Mon argent | `e2e_money`, `e2e_money_parity` |
| Bilan de la semaine (moment, contenu, courriel, partage) | `weekly_test.php`, `e2e_weekly_card`, `e2e_weekly_content`, `e2e_weekly_parity`, `e2e_weekly_share` |
| Captures multi-trades | `shot_trades_test.php`, `e2e_shot_multi` |
| Imports CSV | `e2e_accuracy`, `e2e_import_tradingview` |
| Visuel, stabilité | `e2e_visual_fit`, `e2e_scroll_stable`, `e2e_no_jumps`, `e2e_redraw_no_replay` |
| Langues, accessibilité | `e2e_no_english_in_fr_es`, `e2e_a11y_names` |
| Parcours clés (6 × 3 langues × 2 tailles) | `e2e_acceptance` (~5 min) |
| Arrivée, rattrapage, vrai net, « Estimé » | `e2e_realnet` (~2 min, crée ses propres traders, vide le limiteur d'inscription via `SWEEP_TEST_DB`) |
| Lot A UI/UX (routine, news, boutons, comptes, Net P&L, recherche, espacements, Calendrier, coins, CSV) | `e2e_lot_a` (~2 min) |

- `php ops/tests.php` fait partie de la suite depuis le 9 oct. (20/20).

## 5. Règles produit décidées

- **Journée de séance en heure de New York.** À 17 h la journée est finie ; **à 18 h ET, toute l'app passe au lendemain** : en-tête, news, journal, plan, ajout de trade, calendrier.
  - Chaque trade a une date de séance. Ceux enregistrés depuis le 8 octobre portent `session_date: true`. Le serveur (`api.php` → `sweep_session_dates`) range une seule fois les anciens trades pris à 18 h ou plus tard dans la séance du lendemain.
  - Un trade du soir s'affiche « séance du 8 oct. · entré le 7 à 23:36 ». Les exécutions gardent leur heure réelle.
  - Entre 16 h et 18 h ET (et la fin de semaine), l'étape Plan et le Journal visent la séance suivante (`SweepNextSession`, nav.js).
- **News après 18 h ET** : la carte du jour montre la nouvelle séance. L'onglet Semaine montre toutes les annonces de la semaine, les passées estompées.
- **Routine** : Plan · Exécution · Revue, **ouverte à chaque séance**, avec l'étape suivante mise en avant. Un chevron à côté du titre la replie ; elle reste repliée jusqu'à la fin de la séance (`localStorage sw.rtClosedDay`), puis se rouvre. Faire l'étape ferme son anneau ; les 3 faites = journée réussie.
- **« Dans ton plan »** : sens du biais, setup du plan (si choisi), avant la perte max et le nombre max, pas de « non » à la checklist. Un stop manquant n'est pas une faute. **Heure du plan** = heure d'enregistrement.
- **Plan ↔ Journal** : mêmes données (`journals/<jour>.pre`), y compris les setups prévus et « Pas de trade ».
- **Couleurs du P&L** : bleu pour les gains, or pour les pertes.
- **Argent : 3 couches jamais mélangées** :
  - **performance** : P&L des trades, toutes phases ; un trade copié compte une fois ;
  - **progression** : objectif des évaluations, profit simulé et retirable des comptes financés ;
  - **argent réel** : payouts nets payés + P&L réalisé des comptes live et perso − dépenses.
  - Chaque compte a un `money_type` : eval / funded (simulés) ou live / personal (réels). Les montants simulés portent « Simulé », les réels « Réel ». Aucun total n'additionne du simulé et du réel.
  - **Sélecteur « Type de compte : Tout · Évaluations · Financés · Live · Perso »**, un seul choix mémorisé (`U.mtype`), affiché et appliqué sur Aujourd'hui (Jour/Semaine), Trades, Calendrier, Stats et Mon argent. Le Journal montre toujours tous les trades. Jamais de filtre caché : partout où il s'applique, le sélecteur est visible.
  - **Changer le type d'un compte** : page du compte → Détails → « Type de compte ». Seuls `money_type` et `phase` changent ; trades, règles, payouts et stats restent intacts. « Passer en financé » (nouveau compte après une évaluation réussie) et le passage en live (nouveau compte) restent des parcours séparés.
- **Payouts** : `gross_c`, `split_pct`, `fees_c`, `net_c`, statut. Payé = argent réel ; Prévu, Demandé ou Approuvé = en attente ; Rejeté = 0.
- **Dépenses** : 7 catégories ; remboursement = montant négatif ; abonnement mensuel arrêté automatiquement quand le compte se termine.
- **ROI prop** = (payouts nets − dépenses) / dépenses, sans le P&L live.
- **Copy trading** : un groupe de copies compte une fois, avec le P&L de la copie principale (la plus ancienne). Option Stats « par contrat ».
- **Drawdown par type de compte** (demande de Mateo, 9 oct. ; `tests/e2e_drawdown_kinds.py`) :
  - **challenges et funded en drawdown suiveur** (fin de journée ou temps réel) : la limite suit le meilleur solde puis **s'arrête au solde de départ** (+ décalage de la firme : Apex 100 $). Avec 2 000 $ de drawdown et +6 000 $ de profit, le pire est de revenir au départ : marge **6 000 $**. Un compte affiché à partir de 0 $ suit la même règle (limite bloquée à 0 $). Déjà juste avant le 9 oct., maintenant verrouillé par le test.
  - **live sans règles de firme** : la limite est **0 $** et la marge = **le solde live actuel** (certains live commencent à 0 $), jamais négative ; statut « En règle » (avant : « Aucune règle », sans marge). Info-bulle : « Ton solde live : le plus que tu peux perdre sur ce compte. » Un live avec ses propres règles (Topstep Live : plancher fixe) les garde. `acctState` : `lv`, `live: true`, `dd` = solde.
  - ⚠️ « Pire recul » désigne deux choses : la tuile du haut de la page d'un compte (plus gros recul déjà vécu) et, dans les règles, le drawdown permis (`dd_c`, ex. 2 000 $, fixe).
- **Comptes dépassés** : étiquette or **« Drawdown dépassé »** (ES « Drawdown superado », EN « Drawdown exceeded ») ou « Limite du jour atteinte », partout (Aujourd'hui, liste Comptes, page du compte) ; marge affichée à 0 $ **et barre vide**, même si le solde est remonté au-dessus du seuil ; placés en bas des listes. « Réussi » seulement si objectif, consistance et jours minimum sont remplis ; sinon « Objectif atteint · il manque : consistance 67 % (max 55 %) / 1 jour sur 3 » (brief 01, 1.3).
- **Suppression** : toujours dans l'app (jamais `confirm()` du navigateur), avec un toast « Annuler » pendant 5 s (`SweepUndo.del`, `SweepUndo.toast`). Ça vaut pour un trade, toutes ses copies, une capture, une question de la checklist, les données d'exemple et un lot importé.
- **Import sans frais** (Tradovate, Rithmic) : la commission par contrat du compte (`fee_rt_c`, aller-retour × contrats) est appliquée (`fees_auto`) ; sans commission sur le compte, l'aperçu dit « Frais non inclus dans ce rapport ».
- **Ajout de trade** : la capture d'abord. Une capture avec plusieurs trades ouvre « X trades trouvés » ; avec un seul trade, l'écran habituel s'affiche.
- **Langues** : EN / FR / ES ; montants au format de la langue (FR « 1 688 $ »).
- **Nombres en FR / ES** (étape 4 de l'audit) : espace fine insécable avant « % » (« 52 % »), virgule décimale pour les ratios, les R et les abréviations (« 1,52 », « +0,85R », « +1,6k »). Les **prix** d'entrée et de sortie gardent leur point (« 21366.00 »), comme sur les plateformes. Les pourcentages sont corrigés **après** la traduction (`trText` dans `app.js` : textes traduits et textes faits d'un seul nombre ; les notes des traders ne sont jamais touchées), parce que des phrases anglaises avec « 52% » servent de modèles de traduction. Les ratios et les R le sont à la source (`decl()`). Contrôle : `python3 tools/numfmt.py`.
- **Chiffres clés qui ne rentrent pas** (cases KPI : Net P&L, soldes…) : d'abord arrondis au dollar, puis abrégés (« −12,3 k $ », « 1,23 M $ »), et seulement ensuite police réduite. Le montant exact reste dans le libellé (`title`, `aria-label`). Ailleurs, un chiffre trop long rétrécit au lieu d'être coupé.
- **Page « Mon argent » en deux vues** (Mateo, 9 oct. ; `tests/e2e_money_views.py`) : filtres et export en haut, puis **« Mes entrées »** (vue par défaut : deux gros boutons « + Ajouter un payout », bleu, et « + Ajouter une dépense », gris — « + Payout » / « + Dépense » sur téléphone —, le formulaire ouvert juste dessous, puis les listes Payouts et Dépenses) et **« Analyse »** (Net réel, Par mois, Indicateurs, Par firme). Le choix est mémorisé (`U.mview`). Le raccourci « payout » d'Aujourd'hui ouvre « Mes entrées » puis le formulaire.
- **Export CSV de Mon argent** : il contient exactement ce que montre la page (période active, type de compte, firme, compte), via le même `moneyOf`. Nom du fichier : période + filtres. Il n'existe pas de filtre « statut » sur Mon argent.
- **À surveiller** : les onglets Jour et Semaine montrent Réel · Prév. · Préc. sur chaque annonce (« Sans chiffre » pour les minutes et discours). La carte ne quitte jamais sa place sous la journée (l'équilibrage des colonnes ne la déplace pas).
- **Comptes** : le glisser-déposer (ordinateur) et « Modifier l'ordre » (téléphone) marchent dans chaque groupe (Live, Financés, Évaluations, Perso), uniquement à l'intérieur du groupe ; l'ordre est enregistré pour tous les comptes.
- **Forfait Free** : Mon argent n'y est pas. Le rattrapage du vrai net ne s'ouvre pas et l'invitation « Complète ton historique » ne s'affiche pas en Free (un nouveau trader est en essai Pro de 14 jours, donc il l'a).
- **Compte live** : sans préréglage, avec le choix « live de la firme / perso (courtier) ».
- **Essai Pro** : **60 jours** en ligne (`sweep-private/billing-config.php`) ; le défaut du code (`billing/billing-core.php`) dit 14 jours et ne sert que sans ce fichier.
- **Arrivée d'un nouveau trader** (étape 1 du brief) : inscription → « Complète ton profil » → dans la même fenêtre, « Tu trades depuis combien de temps ? » (Je commence · Moins d'un an · Plus d'un an, ou Passer) → premier compte → **« Compte ajouté »** (Continuer · + Ajouter un autre compte ; jamais la fenêtre d'ajout de trade pendant ce parcours) → rattrapage → écran du vrai net → Aujourd'hui.
  - Le niveau d'expérience est gardé sur le serveur (`users.experience` : `new` / `lt1` / `gt1`, renvoyé dans `user.experience`). Il servira aux règles par défaut de l'étape 2.
  - **Rattrapage** : « Depuis quand veux-tu suivre ton argent ? » (Ce mois-ci · Depuis janvier · Une date) → achats par firme des comptes du trader (évaluations, resets, activations, compteurs +/−, prix du catalogue pré-remplis et modifiables ; Topstep : « Mois d'abonnement ») → payouts nets reçus (un seul montant) → vrai net.
  - Pour chaque firme, « Déjà dans Mon argent : X $ » affiche les dépenses déjà saisies dans la période (frais ajoutés avec le compte), et les compteurs servent à ajouter des achats en plus : jamais de double comptage.
  - **Écran du vrai net** : dépensé, reçu, vrai net, calculés par `moneyOf` sur la même période (donc le même chiffre que Mon argent). Net positif : « Tu es rentable de X $ depuis … » ; sinon : « C'est ton point de départ… ». Jamais de reproche.
  - « Je le ferai plus tard » sur chaque écran. Ensuite, la carte Mon argent d'Aujourd'hui propose « Ton vrai net en 1 minute » jusqu'à ce que ce soit fait ou masqué (✕).
  - **Trader existant** : la carte propose « Complète ton historique en 1 minute » un seul jour (le premier où il la voit).
  - État dans les réglages synchronisés : `S.settings.realnet = { state: 'done' | 'later' | 'hidden', shown_on, at }`.
  - Pendant le parcours, les fenêtres automatiques (célébrations, installation) attendent (`sw.modal`).
- **Entrées estimées** : dépenses et payout du rattrapage sont des entrées normales de Mon argent avec `estimated: true`, une par firme et par catégorie (ids `est-<firme>-<catégorie>`, un nouveau rattrapage les remplace), datées au début de la période ; le payout estimé (`est-payouts`) n'a ni firme ni compte.
  - Elles comptent comme de l'argent réel (net réel, ROI, par firme, « La réalité du mois »).
  - Étiquette « Estimé » dans Mon argent, « estimé » dans l'export CSV. Elles se modifient dans un petit formulaire (montant, date) ou se suppriment comme les autres.
  - Un payout estimé n'a pas de bouton « Partager ».
  - Un achat précis enregistré dans la période d'une estimation (même firme, même catégorie) : rien n'est fusionné, un rappel « ajuste-la si besoin » propose « Ajuster ».
- **Le partage met la discipline en avant.** La carte « argent » montre seulement des payouts nets et le net réel. La carte « Ma semaine » (bilan du vendredi) : prénom, semaine, anneaux des 5 jours, streak, discipline, journées balayées ; **aucun montant**, sauf les payouts reçus si le trader active « Ajouter mes payouts reçus » (désactivé par défaut).

## 6. Préréglages des prop firms

- **Catalogue** : `presets/seed.json`, version `2026-10-08c` (règles vérifiées le 7 octobre). Points notables :
  - Topstep : Combine à 55 % ; financé « Standard » ou « Consistance » ; split 90 %.
  - Apex : programme « Legacy (avant mars 2026) » ; seuil bloqué au départ + 100 $.
  - TPT : 3 jours minimum. MFFU : Builder 25K, règles de payout du Rapid EOD. Lucid : limite journalière du 150K.
  - Tradeify et Alpha : vides, absents du sélecteur.
- **Vérification hebdomadaire** : `presets/cron.php` (le lundi à 5 h) relit les pages officielles via `check.php`, une firme à la fois.
  - Options : `--dry-run`, `--firm=x`. Test sans réseau ni IA : `SWEEP_PRESETS_MOCK`.
  - Un changement validé crée une nouvelle version du catalogue (fusion, avec l'ancienne gardée).
- **Tableau Admin « Préréglages »** (admin seulement, `api/admin/presets`) : date de la dernière vérification complète, état par firme, bouton « Vérifier maintenant ».
  - Alerte si aucune vérification depuis 8 jours.
- **Notifications de changement de règles** (`rules_changed`) : les traders dont un compte utilise une règle modifiée sont prévenus. Sur le compte, ils choisissent « Appliquer les nouvelles règles » ou « Garder mes règles ».
- **Valeurs non publiées en texte** (frais d'évaluation et d'activation Apex, Lucid, TPT, MFFU) : non saisies. Split : seulement Topstep (90 %) ; 100 % par défaut ailleurs, modifiable.

## 7. Captures avec plusieurs trades (Sweep AI)

- Gemini **recopie le tableau tel qu'il est écrit** : titres, cellules, couleur du P&L, et le symbole écrit ailleurs (`symbol_shown` : titre du graphique, en-tête). Une page d'un seul trade en champs étiquetés est lue comme une ligne. Un appel, un crédit par capture, température 0. `model_vision` dans la config permet un modèle plus fort pour les captures.
- `ai/shot-trades.php` déduit tout le reste :
  - colonnes reconnues même coupées (FR/EN/ES) ; symboles reconnus par code ou par nom (« Gold (GCZ6) » → GC, « Micro Gold » → MGC) ;
  - heures dans tous les formats courants, jour/mois décidé pour tout le tableau, aucune heure inventée ;
  - FIFO pour les fills ; sens vérifié par les prix et le P&L quand le signe est vraiment écrit ;
  - P&L brut ou net, frais ; conversion à l'heure de New York et séance de 18 h.
- **Enregistrement** : `api/docs/batch`, une transaction, `import_batch_id` ; Annuler retire le lot. Le jeu se recalcule une fois par séance touchée. Une capture partagée n'est effacée que si plus aucun trade ne l'utilise.
- **Limites** : NinjaTrader, ProjectX et les graphiques se lisent moins bien. Les tests utilisent des réponses simulées : la vraie lecture par Gemini reste à valider avec des captures réelles.

## 8. Design system (« Sweep Glass »)

- **Couleurs (foncé)** : encre #08080A / #0B0B0C, surfaces #151518 / #1C1C20, ligne #2A2A30, texte #F2F2F3, gris #9A9AA2, gris secondaire (`--faint`) #8A8A93. Bleu #4C8DFF (gains), or #D4A24C (pertes, alertes).
- **Couleurs (clair)** : gains #2862D0, pertes #8A600F, gris secondaire #66666F.
- **Fond bleu sous un texte ou une icône blanche** (boutons principaux, puces actives, pastilles) : `--pos-fill` #2F6FE4 (foncé) / #2862D0 (clair), et le dégradé du bouton principal #2F6FE4 → #2A66D6. Le bleu des chiffres reste #4C8DFF en foncé. Les éléments concernés redéfinissent leur propre `--pos` (liste dans `nav.css`, section « Audit, step 1 ») : pour un nouveau fond bleu avec texte blanc, l'ajouter à cette liste.
- **Contraste** : tout texte à 4,5:1 minimum (WCAG AA), vérifié avec axe-core sur ordinateur, iPhone et Android, en clair et en foncé. Seule exception volontaire : les jours hors du mois du Calendrier (éléments inactifs). ⚠️ Les jetons du thème foncé existent aussi dans `app.css` (plus ancien) sous `@media (prefers-color-scheme:dark){:root:not([data-theme=light])}` : pour changer un jeton foncé, le redéfinir avec ce même sélecteur dans `nav.css`, sinon il ne s'applique pas quand le thème suit le navigateur.
- **Zoom** : permis (pas de `maximum-scale`). Tout champ fait au moins 16 px sur téléphone (sinon l'iPhone zoome tout seul au toucher).
- **Matière** : un seul verre ; barres et fenêtres en encre translucide floutée.
- **Polices** : Geist et Geist Mono, servies par l'app (aucune police externe), **en sous-ensemble** (latin, accents FR/ES, ponctuation, symboles monétaires et tout caractère présent dans le code ; plus de cyrillique) : 141 → 79 Ko. Un nouveau caractère spécial dans un texte de l'app → relancer `python3 -I tools/subset-fonts.py` (sinon il s'affiche dans la police du système).
- **Rayons** : 14 (champs) · 20 (tuiles) · 26 (cartes) · 32 (grands blocs, fenêtres) · capsule pour les boutons.
- **Tailles** :
  - champs à 42 px sur ordinateur, 44 px sur téléphone ; texte des champs ≥ 16 px sur téléphone ;
  - un petit lien ou bouton sur téléphone (« Tout voir › », plis) garde une zone tactile de 44 px par un `::after` invisible ;
  - boutons à 40 px (petits : 34 px) sur ordinateur, cibles tactiles d'au moins 44 px sur téléphone.
- **Espacements** : 28 px entre les blocs, 12 px entre un titre et sa carte. Rien ne dépasse d'une carte (test `e2e_visual_fit`).
- **Lignes repliables** : petite flèche, pas de triangle du navigateur.
- **Colonnes d'Aujourd'hui (ordinateur)** : équilibrées à l'affichage ; une carte (Mon argent, À surveiller, Ce mois-ci, Tendances) ne bouge qu'une fois, n'est jamais reprise par le bloc fusionné et revient directement à sa place quand la page se redessine.
- **Mouvement** : courbe `cubic-bezier(.32,.72,0,1)`, une entrée par page, « Réduire les animations » respecté. Un seul bouton principal par écran.
- **Boutons** : bleu réservé au seul bouton principal de l'écran, survol discret (légèrement plus lumineux, jamais un fond sombre) ; tous les autres en gris neutre (ex. « Ajouter un trade ce jour-là »). Bouton pleine largeur des fenêtres (« Enregistrer le trade », Continuer…) : 44 px sur ordinateur, 48 px sur téléphone, 15 px semi-gras.
- **Sections repliables** (Pré-marché, Après-marché) : l'en-tête garde ses coins arrondis, ouvert ou fermé ; la fiche ouverte est une carte séparée.
- **Champs de recherche** : une seule boîte (le champ est transparent dans son cadre) ; si la recherche est masquée (moins de 10 trades), le cadre entier l'est aussi.

## 9. Préférences de travail de Mateo

- Une seule option plutôt que plusieurs ; trancher quand c'est raisonnable.
- Pas d'ajouts non demandés ; ne toucher qu'à ce qui est demandé.
- Tester sur ordinateur ET téléphone, avec captures quand c'est visuel.
- Réponses en français, claires, sans jargon ; dire honnêtement ce qui n'est pas fait ou pas vérifié.

## 10. Méthode de travail

- **Pendant les itérations**, lancer seulement les tests liés aux fichiers modifiés (voir le tableau de la section 4). Toute la suite (`/tmp/full.sh`) uniquement avant le zip final.
- **Un seul zip par lot de demandes**, pas un zip par point.
- **Les règles des firmes sont vérifiées ailleurs** et fournies confirmées. Ne refaire la vérification web que si une valeur semble contradictoire.
- **Rapport de livraison en 3 lignes** : ce qui change, les fichiers modifiés, les tests passés.

## Passation (9 octobre — audit visuel / animations / vitesse, étapes 1 à 4 livrées)

### Où on en est
- **Audit avant mise en ligne** (demandé le 9 oct. : visuel, animations, vitesse ; aucune refonte, rien ne doit briser) : récapitulatif validé par Mateo. Plan en 6 étapes, **une à la fois, approuvée avant la suivante** ; à chaque étape : fichiers complets modifiés avec leur chemin, tests ordinateur + mobile, clair + foncé, nouvelles mesures de vitesse.
  1. **Bloquants visuels : livrée et en ligne** (contrastes AA, bouton principal, Comptes qui sautent, nom du bouton Progression, zoom permis, zones tactiles 44 px, montants clés jamais coupés).
  2. **Vitesse côté navigateur : livrée et en ligne** (voir « Étape 2 de l'audit » plus bas : polices en sous-ensemble, Aujourd'hui sans décalage au chargement ; trois points du plan abandonnés après mesure). Réglages serveur (compression NGINX, HTTP/2, OPcache) : **mis de côté par Mateo le 9 oct.** ; le support HostArmada a répondu que la compression était active, mais la mesure en ligne montre le contraire (HTML, CSS et JS servis sans `Content-Encoding`). Un message prêt à leur envoyer a été donné à Mateo. Le plus gros gain de vitesse restant.
  3. **Vitesse côté serveur : livrée et en ligne** (voir « Étape 3 de l'audit » : cache de `img/` et `icons/` ; migrations laissées telles quelles après mesure ; compression impossible sans root).
  4. **Finitions visuelles : livrée** (formats de nombres FR/ES, « Bonjour Mateo · Vendredi 9 octobre » sans virgule).
  5. Animations : une seule courbe iOS, 150-350 ms ; 13 animations à réécrire en transform/opacity ; 18 animations infinies à arrêter hors écran.
  6. Lot B (Stats, Deep Dive, Mon argent, filtres harmonisés).
- **Serveur (mesuré le 9 oct.)** : aucune compression (NGINX a `gzip` désactivé pour tout le VPS : CSS 434 Ko et JS 339 Ko envoyés bruts), HTTP/1.1 (`http2 off` : ea-nginx ne l'active que si `/etc/nginx/conf.d/http2.conf` existe), PHP 8.1 sans OPcache (mod_lsapi). Le cache des `assets/` est bon (1 an, `immutable`). Les réglages demandent root (WHM → Terminal) ; les commandes ont été données à Mateo le 9 oct. : `/etc/nginx/conf.d/sweep-gzip.conf`, `touch /etc/nginx/conf.d/http2.conf`, `dnf install ea-php81-php-opcache`, `ea-nginx config --all`, rechargement de NGINX et d'Apache. Mon accès SSH (`matnsabc`) ne peut pas les faire.
- Étape 2 du brief d'évolution (règles et journée en trois temps) : après l'audit.

### Mesures (local, relais gzip, Lighthouse simulé)
- Avant l'audit : Aujourd'hui mobile perf 55, LCP 5,3 s, TBT 1 136 ms ; Stats mobile 54 / 5,5 s / 1 242 ms ; Comptes mobile CLS 0,382 ; ordinateur 85-96. Poids d'une page : 622 Ko (JS 383, CSS 77, polices 138).
- Après l'étape 1, comparaison A/B sur la même machine (ancien et nouveau code servis côte à côte, 3 passages, médiane) : pas de régression ; Aujourd'hui mobile TBT 2 146 → 1 994 ms, Trades mobile 1 657 → 909 ms (cette machine est plus lente que celle des mesures « avant » : comparer seulement en A/B). Comptes : CLS 0,69 → 0,067.
- Contrastes sous 4,5:1 : ~1 100 éléments → 0 (hors jours hors du mois du Calendrier, exemptés).
- Étape 2 (Mac de Mateo, `tools/perf.py` et `tools/shifts.py`, A/B) : polices 141 → 79 Ko (poids d'une page avec compression 624 → ~561 Ko) ; Aujourd'hui ordinateur CLS 0,089-0,22 → 0,0002-0,035 ; mobile déjà à 0 partout. Temps de calcul inchangés (aucune modification du JS de rendu).

### Étape 2 de l'audit — ce qui a été mesuré et décidé
- **Polices** : sous-ensemble (`tools/subset-fonts.py`, originaux dans `tools/fonts-src/`). Largeurs et crénage vérifiés identiques (HarfBuzz, graisses 400/500/600) ; captures A/B identiques sur téléphone ; sur ordinateur (densité 1×) seul le lissage des lettres diffère, à moins de 0,4 % des pixels, sans aucun déplacement.
- **Routine qui sautait (ordinateur)** : l'étiquette « Pour la prochaine séance » était ajoutée à la carte de chargement ; ses étapes n'ont pas de titre, donc l'étiquette tombait à côté de l'étape, comme 4ᵉ case de la grille. Elle ne s'ajoute plus aux étapes `.sk`.
- **En-tête d'Aujourd'hui (ordinateur)** : il passait de la taille simple à celle à 3 lignes (`.nav-3l`, posée par `nav.js`) après le premier affichage. Les mêmes règles s'appliquent maintenant dès `html[data-home]`, posé dans le `<head>` d'`app.html`.
- **Abandonnés après mesure** (ne pas les refaire sans nouvelle mesure) :
  - **un seul observateur au lieu de 39** : tous les observateurs réunis coûtent ~15 ms sur ~650 ms de calcul au chargement d'Aujourd'hui (mobile, CPU ×4) ; le gain ne vaut pas le risque ;
  - **charger la gamification et le guide après le premier affichage** : `game.js` (anneaux, routine) et `guide.js` (carte de départ) dessinent une partie d'Aujourd'hui au premier rendu ; les retarder ferait apparaître ces cartes en retard (sauts) ;
  - **purger le CSS « écrasé »** : les déclarations réellement écrasées (même sélecteur, même contexte, plus loin) ne sont que 413 sur 15 820 (−3 %). Les « ~85 % inutilisés » sont des règles que la page affichée n'utilise pas (survols, fenêtres, états rares) : les retirer par couverture divise le temps de style par deux sur Aujourd'hui (254 → 120 ms, mobile CPU ×4) mais risque de casser des états rares. À ne reprendre qu'avec une couverture de tous les états.
  - Le profil CPU attribue ~250 ms à `fitOne` (`nav.js`) : c'est le recalcul de style de la page, déclenché par sa première mesure, pas un emballement (35 mises en page avant comme après une réécriture en lecture groupée, abandonnée).
### Étape 3 de l'audit — ce qui a été mesuré et décidé
- **Migrations d'`api/data`** (dates de séance, types d'argent, abonnements mensuels) : **laissées telles quelles**. Avec 5 000 trades et 20 abonnements, `api/data` répond en 40-70 ms avec ou sans elles (écart dans le bruit) ; les abonnements mensuels doivent de toute façon tourner (dépense de chaque nouveau mois).
- **Le vrai coût d'`api/data`** : la réponse elle-même (105 Ko avec les données d'exemple, **4,9 Mo pour 5 000 trades**), envoyée sans compression.
- **Pourquoi rien n'est compressé** : NGINX (devant Apache) a `gzip` désactivé et efface l'en-tête du navigateur `Accept-Encoding` avant de passer la requête à Apache (`proxy_set_header Accept-Encoding ""` dans `/etc/nginx/conf.d/includes-optional/cpanel-proxy.conf`). Apache (`mod_deflate`, `mod_brotli` présents) et PHP (`zlib`) ne savent donc jamais si le navigateur accepte la compression : les règles de `.htaccess` ne s'appliquent pas, et compresser d'office serait faux pour les clients qui ne la demandent pas. **Seul root peut le régler** (`gzip on` dans NGINX).
- **Cache** : `img/.htaccess` (30 jours ; les images sont appelées avec `?v=…`, à changer quand une image change) et `icons/.htaccess` (7 jours ; noms sans empreinte). `assets/` garde 1 an `immutable`.
- ⚠️ `assets/.htaccess` met aussi 1 an `immutable` sur `assets/fonts/` et `assets/vendor/`, dont les noms n'ont pas d'empreinte : **pour changer une police, il faut changer son nom de fichier** (et le `@font-face` de `nav.css` + le `preload` d'`app.html`), sinon les visiteurs déjà venus gardent l'ancienne un an. Les polices allégées de l'étape 2 gardent leur nom : les anciens visiteurs ont encore la version complète, qui contient tous les mêmes caractères (sans conséquence).

- **Le vrai coût restant au chargement** : style (~250 ms) et script (~270 ms) sur Aujourd'hui mobile CPU ×4, pour ~9 300 éléments dans la page.

### Étape 1 de l'audit — causes trouvées
- Gris secondaire foncé : l'ancienne règle de `app.css` (`prefers-color-scheme:dark` + `:root:not([data-theme=light])`) avait le sélecteur le plus fort ; la valeur de `nav.css` ne s'appliquait qu'au thème foncé choisi à la main.
- Comptes qui sautent : `content-visibility:auto` réservait 60 px par ligne, une carte de compte en fait ~140 sur téléphone.
- Montant clé coupé un instant : l'ajustement passait à l'image suivante après chaque redessin ; les cases clés sont maintenant ajustées avant l'affichage (observateur natif limité à ces cases).

### Lot A — causes trouvées (pour ne pas les réintroduire)
- 1.2 : l'équilibrage des colonnes déplaçait « À surveiller » ; au redessin, la carte revenait à sa place du gabarit (haut de la colonne droite). Elle n'est plus jamais déplacée.
- 1.1 : le bouton de repli avait été retiré et l'état forcé à « ouvert » par plusieurs couches de CSS (`nav.css`, règles « A1 », « B9 ») ; une règle finale plus précise les remplace.
- 3 : une ancienne règle de survol (`.nav-rt-s:hover .nav-rt-sa .btn.primary{background:none}`) donnait le fond sombre.
- 10 : `decorate()` ne préparait que le premier tableau de la page Comptes (Live).
- 11 : l'ajustement des montants posait une taille inline sans `!important`, battue par le CSS.
- 12 : le champ de recherche recevait le style général des champs (boîte dans la boîte) ; sous 10 trades, le champ était caché mais pas son cadre.
- 15.2/15.3 : l'en-tête ouvert perdait ses coins du bas, au-dessus d'une fiche séparée. 17.2/17.3 : bordure du bas de la dernière ligne qui dépassait sous la carte.
- 1.3 : l'onglet Semaine n'avait jamais affiché les chiffres (seul l'onglet Jour). En local, les valeurs sont vides (calendrier économique manuel).

### Ce qui a changé à l'étape 2 de l'audit (depuis le commit « App 3 : version finale », en ligne)
- Modifiés : `src/nav.js` (pas d'étiquette « prochaine séance » sur la routine en chargement), `src/nav.css` (en-tête d'Aujourd'hui à sa taille finale dès `html[data-home]`), `assets/fonts/Geist-Variable.woff2` et `GeistMono-Variable.woff2` (sous-ensemble), `app.html` (nouveaux noms de fichiers), `CONTEXTE-APP.md`.
- Recompilés : `assets/bundle.7cfeabbae3.css`, `assets/nav.656d6b8284.js`, `assets/nav.a7bef0aeac.css` (remplacent `bundle.22e4b3842c.css`, `nav.6a0187b7d5.js`, `nav.d03abd2926.css`, qui peuvent rester sur le serveur).
- Nouveau : `tools/` (environnement local, mesures, suite répartie `par.py`, originaux des polices).

### Brief 01 — étape 5 (bilan du vendredi), en lots
- **Lot 1 : le moment** (`GameV2b::openWeek($uid)`, `tests/weekly_test.php`, `tests/e2e_weekly_card.py`). Le bilan d'une semaine est prêt à la fin de son **dernier jour de trading** (vendredi, ou jeudi si le vendredi est férié) : **dès que la revue de ce jour est faite**, sinon à la **clôture de 17 h ET** ; il reste jusqu'au dimanche 23 h 59 ET, heure de New York quel que soit le fuseau du trader. **Seulement s'il y a au moins un trade dans la semaine.** Il prend la place de l'étape suivante dans « Ta routine du jour » (« Ta semaine est prête · Voir mon bilan », seul bouton bleu ; aussi sur la carte « marché fermé » du week-end). **Une seule notification** « Ta semaine est prête » par semaine (`g:g_weekly:<semaine>:<jour>`), aucune si le bilan a déjà été ouvert ; plus de condition de déblocage pour le bilan lui-même (le questionnaire, la découverte et le coffre gardent leur déblocage). Ouvrir le bilan (`GET api/game/weekly`) le marque vu (`game_analytics` `weekly_opened`).
- **Lot 2 : le contenu** du premier écran (`weekBrief()` dans `game.js`, `tests/e2e_weekly_content.py`) : streak de journées balayées, **score de discipline de la semaine** (moyenne des scores de checklist des trades, `tDisc`), **journées balayées sur jours tradés**, **meilleure habitude** (question de la checklist la plus souvent « oui », 2 réponses au moins), **un point à travailler** (la moins souvent « oui », formulé « Vise un « oui » à … »), **payouts reçus** de la semaine (payés, argent réel), plus les anneaux des 5 jours. **Plus aucun P&L** sur cet écran (avant : P&L net, taux de réussite, meilleur / pire jour en dollars) : aucun montant simulé présenté comme de l'argent gagné. Le questionnaire, la découverte et le coffre suivent, inchangés.
- **Lot 3 : le courriel « Ta semaine »** (`game/weekly-mail.php`, classe `GameWeeklyMail`, appelée par `game/cron.php` toutes les 15 min ; `tests/weekly_test.php`, `tests/e2e_weekly_parity.py`).
  - **Quand** : dès **17 h 30 ET le dernier jour de trading** de la semaine (jeudi si le vendredi est férié), ou plus tard jusqu'au dimanche 23 h 59 si le cron l'a manqué ; **seulement si le bilan est prêt (au moins un trade) et pas encore ouvert dans l'app** ; **une fois par semaine** (table `weekly_emails`, écrite avant l'envoi : jamais deux courriels, même si deux passages du cron se chevauchent ; un envoi raté est noté dans le journal d'erreurs et n'est pas relancé). Sans adresse ou compte désactivé : rien. Langue : `users.lang`.
  - **Contenu** : les chiffres du premier écran du bilan (streak, discipline, journées balayées sur jours tradés, meilleure habitude, point à travailler, payouts reçus), calculés côté serveur par `GameWeeklyMail::brief()` avec les règles de `weekBrief()` ; `e2e_weekly_parity` compare les deux sur les mêmes trades, en FR / EN / ES. Aucun P&L. Bouton « Voir mon bilan » vers Aujourd'hui. Les questions par défaut sont traduites par la table `QS_TR` (reprise des fichiers de langue) : **à mettre à jour si une question par défaut change**. Égalité entre deux questions : départagée par l'identifiant de la question, des deux côtés (avant, par l'ordre des trades dans l'app).
  - **Lien « Ne plus recevoir le bilan par courriel »** en bas, exigé par la LCAP (loi canadienne anti-pourriel) pour ce type de courriel, et en-tête `List-Unsubscribe` (désinscription en un clic des applications de courriel) : `api/email/weekly?t=<jeton>` (table `email_prefs`, un jeton par trader, sans connexion) affiche une page avec un seul bouton, puis « La recevoir à nouveau ». La route est placée avant le contrôle CSRF : les applications de courriel postent sans l'en-tête de l'app.
  - `sweep_mail()` a quitté `api.php` pour `notify/mail.php` (avec un 5ᵉ paramètre pour des en-têtes en plus) ; le courriel de mot de passe ne change pas. Tables créées toutes seules : `weekly_emails`, `email_prefs`.
- **Lot 4 : partager sa semaine** (`shareCard('week')` dans `game.js`, `tests/e2e_weekly_share.py`). Sur le premier écran du bilan, un bouton gris « Partager ma semaine » (« Analyser ma semaine » reste le seul bouton bleu) et, seulement s'il y a des payouts reçus dans la semaine, l'interrupteur « Ajouter mes payouts reçus », **désactivé par défaut**. La carte (image 1080 × 1920, même style que les autres cartes de partage) : « La semaine de <prénom> » (« Ma semaine » sans prénom), la semaine, les anneaux des 5 jours, le streak, la discipline, les journées balayées sur jours tradés ; aucun montant, sauf la ligne « Payouts reçus cette semaine » si l'interrupteur est activé. Téléphone : la feuille de partage du système ; ordinateur : l'image est téléchargée (`sweep-week.png`). Compté comme les autres cartes (`api/game/share`, `week`).
- En passant : sur le premier écran du bilan, les puces bleues de la liste tombaient sur le bord des cases (retirées) ; en français, espaces insécables dans « » et avant « ? » (le « » » ne commence plus une ligne), comme dans le courriel.
- **Calendrier « Ce mois-ci » d'Aujourd'hui** (trouvé par `e2e_weekly_share` sur GitHub) : ses 5 colonnes (`repeat(5,1fr)`) prenaient la largeur de leur contenu ; dans la colonne étroite d'un ordinateur à 1300 px, le nom d'une annonce (« Nonfarm Payrolls ») les rendait inégales et la grille sortait de sa carte d'environ 50 px. Colonnes égales (`minmax(0,1fr)`) et nom terminé par « … » (la ligne de l'annonce n'est plus un conteneur flex, sinon `text-overflow` ne s'applique pas).
- **Étape 5 terminée** (lots 1 à 4).

### Brief 01 — étape 4 (voir ce qui se passe chez les traders)
- **Erreurs JS** : déjà envoyées par `ux.js` §15 (`api/client-error`, 5 par page au plus : message, fichier:ligne, page, navigateur, version de l'app ; jamais de contenu de trade). Nouveau : Admin › Tableau de bord les **regroupe par message sur 30 jours** (traders touchés, nombre de fois, dernière fois, pages, navigateurs résumés « Safari iOS 17 », versions).
- **Indicateurs** (`ops/metrics.php`, bloc `brief`) pour la **semaine d'inscription** (lundi, New York) et la **source** (« Où as-tu trouvé Sweep ? », `users.found_via`) choisies — `api/admin/metrics?cohort=AAAA-MM-JJ&source=…` : médiane inscription → premier trade ; **activation** = un trade le jour de l'inscription (New York ; l'inscription du jour attend) ; **rétention J7 / J30** = un trade ou une revue les jours 7 à 13 / 30 à 36 (seuls les traders dont la fenêtre est passée) ; **journées balayées** = séances avec trades des 30 derniers jours où les 3 anneaux sont fermés ; recherches sans résultat (top 20, inchangé). Les anciens indicateurs (activation en 24 h, « aha », semaine 2) restent et suivent les mêmes filtres.
- Tests : `tests/metrics_test.php` (14, base jetable, chiffres calculés à la main) et `tests/e2e_admin_metrics.py`.

### Brief 01 — étape 3 (ordre dans le code), en lots
- **Lot 1 : `src/app.js`** (cœur lisible, 9 974 lignes) compilé par `ops/build-assets.sh`. Vérifié : 32/32, captures A/B identiques au pixel (8 pages × 2 tailles × FR foncé / ES clair), vitesse identique (−3 Ko).
- **Inventaire** : 25 fonctions du cœur remplacées ou enveloppées à 59 endroits (`render` × 23 : chaque module y ajoute sa partie de l'écran ; `payoutForm`, `expenseForm`, `submitExpense` × 3 ; `submitPayout`, `vPayouts`, `submitAccount`, `openTicket`, `calDays` × 2 ; `acctTable`, `acctOK`, `parseTradovate`, `impGo`, `deleteAccount`…). Les formulaires de payout / dépense et `vPayouts` sont ceux de « Mon argent » (`ux.js`, chantier séparé selon le brief 02).

- **Lot 2 : règles partagées verrouillées** (le navigateur et le serveur ne partagent pas de code) : `tests/e2e_rule_parity.py` compare les deux côtés — séance du moment (90 instants : 0 h → 23 h 59, vendredi, dimanche, changements d'heure 2026), séance d'un trade selon son heure d'entrée (90 cas), `hasSessionDate` (9 trades), montants en dollars EN / FR / ES (`SweepMoneyServer::dollars()`, sorti de `monthly()` sans changer ce qu'il produit). Aucun écart trouvé ; un écart volontaire (+7 h côté serveur) fait bien échouer le test. Le statut des comptes n'est calculé que dans le navigateur (`acctState`) : l'export copie les règles et le statut enregistrés, rien à mettre en parité. Notification « La réalité du mois » : espace insécable avant « $ » en FR / ES.
- **Point 3.2 du brief (réintégrer les corrections de `nav.js` / `ux.js` dans le cœur) : écarté avec Mateo** le 9 oct. Les 23 enveloppes de `render` sont le mécanisme normal des modules ; les fonctions remplacées en couches sont celles de « Mon argent » (brief 02 : ne pas y toucher). L'inventaire ci-dessus sert de carte.
- **Vitesse (téléphone simulé du brief : CPU ×4, 1,6 Mbit/s, 150 ms, cache vide ; `tools/perf-net.py`)** :

  | | Avant l'audit (commit `ec5a837`) | Maintenant, sans compression (comme en ligne) | Maintenant, **avec gzip** (relais local) |
  |---|---|---|---|
  | Premier affichage | 3,2 s | 2,9 s | **1,2 s** |
  | Page prête | 9,7 – 10,2 s | 9,4 – 9,9 s | **3,5 – 4,0 s** |
  | Ko transférés | 1 917 | 1 852 | **578** |

  Le reste de la liste du brief était déjà fait (une seule langue chargée, graphique à la demande, plus de Google Fonts, un seul CSS) ; `game` et `guide` restent chargés au départ (ils dessinent Aujourd'hui). **La compression NGINX (HostArmada, root) est le seul gain important restant.**

### Brief 01 — étape 2 (suite de tests qui protège)
- `tests/setup.py` remplace `tools/prof.py` ; `run-all.sh` le lance, puis `ops/tests.php` (nouveau dans la suite), les tests PHP et les 29 tests Playwright : **32 au total**.
- 111 scripts d'exploration retirés (`tests/RETIRED.md`) ; les 2 mentions du README pointent vers les tests qui couvrent ces sujets.
- GitHub Actions à chaque push (PHP 8.1) et verrou dans `deploy.sh` (voir section 4). `gh` n'est pas installé sur le Mac : le dépôt étant public, `tools/ci-status.py` lit l'API sans identification.
- Les scénarios de l'étape 1 sont des tests permanents (`e2e_accuracy` A2-A8, A5b, A6b).

### Brief 01 « Fondations » (reçu le 9 oct.) — étape 1
- Le brief décrit un état plus ancien : ses scénarios de l'étape 1 existaient déjà comme tests (`e2e_accuracy` A2-A8, `e2e_session_parity`, `e2e_import_session_day`). Ajoutés : A3 avec la formulation exacte, A5b (compte dépassé puis remonté), A6b (commission Tradovate appliquée).
- Corrigé : étiquette « Drawdown dépassé » (avant « Dépassé »), texte de ce qui manque, marge 0 $ et barre vide sur la page du compte et sur Aujourd'hui pour un compte dépassé puis remonté (avant : marge réelle, barre pleine).
- Prix des firmes (1.7) : passés (Mateo n'a pas les montants). Environnement de test : **local seulement** (choix de Mateo ; trade.agencedeclic.ca garde sa redirection vers l'app, c'est l'ancienne adresse du journal).
- Points vus en passant : `NOTES.md` (non déployé).
- Écarts du brief déjà tranchés : ne pas charger `game` / `guide` à la demande (ils dessinent Aujourd'hui, mesuré à l'étape 2 de l'audit) ; Google Fonts déjà retirées ; une seule langue chargée ; CSS déjà en un fichier.

### Ce qui a changé à l'étape 4 de l'audit
- `assets/app.de47127496.js` → `assets/app.708d6fa5c5.js` (patché : `trText` + `pctSp`, `decl` dans `pf`, `rfmt`, gain/perte moyen, « Plus actif », abréviations « k »), `src/nav.js` (message d'accueil), `app.html`, recompilé `assets/nav.*.js`. Nouveau : `tools/numfmt.py`.

### Ce qui a changé à l'étape 3 de l'audit
- Nouveaux : `img/.htaccess` et `icons/.htaccess` (durée de cache). Aucun code PHP ou JS modifié.

### État des tests
- PHP : `presets_test.php` 41/41, `shot_trades_test.php` 32/32.
- **Brief 01, étape 5, lot 4 : 42/42** (suite répartie sur une copie propre du commit, sans le travail en cours de la session synchro, 8 min 46 s, un samedi avec `SWEEP_GAME_NOW` = vendredi 15 h ET), sans « RETRY ». Puis avec la correction du calendrier : 42/42 (8 min 46 s), sans « RETRY ».
- **Brief 01, étape 5, lots 1 à 3 : tous réussis** (suite répartie, 8 min 41 s, un samedi avec `SWEEP_GAME_NOW` = vendredi 15 h ET), sans « RETRY » ; `weekly_test.php` 44/44, `e2e_weekly_parity` identique en FR / EN / ES.
- **Série complète sur base neuve (Mac, PHP 8.5) : 31/31 avant l'étape 2 et 31/31 après** (en série puis en suite répartie), sans « RETRY ».
- **Étape 4 : 31/31** (suite répartie, 8 min 11 s), sans « RETRY » ; `tools/numfmt.py` ne trouve plus de format anglais en FR/ES (hors prix et numéro de version) ; aucune boucle de réécriture (mutations au repos identiques en EN, FR, ES).
- **Brief 01, étape 1 : 31/31** (suite répartie, 8 min 14 s, un vendredi soir avec `SWEEP_GAME_NOW` = vendredi 15 h ET), sans « RETRY ». `e2e_presets_firms` a échoué une fois sous la charge des 3 groupes (clic pendant une transition), puis passé seul 2 fois et dans la suite complète suivante : à surveiller.
- Étape 2 : captures A/B au pixel (8 pages × téléphone / ordinateur × FR foncé / ES clair) ; décalages mesurés sur 7 pages × 2 tailles ; aucune erreur JS.
- `run-all.sh --all` et `ops/tests.php` : non lancés.

### Bugs connus et points à surveiller
- Saisie du profil perdue (2 fois sur ~25 passages de `e2e_realnet`, jamais reproduit à la main ; le test ressaisit une fois et l'écrit « RETRY »). Aucun « RETRY » dans la dernière série complète.
- Un compte dépassé glissé en tête retombe en bas (règle « comptes dépassés en bas ») : voulu, mais peut surprendre.
- La fenêtre d'ajout de trade s'ouvre avec un léger délai après le toucher ; la célébration unique d'un lot importé n'a été vérifiée qu'un jour sans célébration.
- Une dizaine de scripts `tests/e2e_*` hors suite principale pointent encore vers `/home/claude/media/…`.

### Questions ouvertes (décision de Mateo)
1. **« Voir tout » (17.1)** : non identifié. Hypothèse : même cause que le point 10 (sur téléphone, « Modifier l'ordre » ne marchait que dans Live), corrigée. Sinon, demander une capture.
2. **Filtre « statut » (Actif) sur Mon argent** : il n'existe pas ; l'exemple du document (« Évaluation + TopStep + Actif + Trimestre ») le suppose. À ajouter au lot B ?
3. **Prix des firmes** : Mateo ne les a pas ; on garde Topstep seul au catalogue, le trader tape les autres.
4. Toujours ouvertes : `model_vision` (modèle Gemini des captures), « La réalité du mois » en grande fenêtre ou cloche seulement, définition des copies « par contrat ».
5. Questions de l'étape 2 (brief, section 8) : définition exacte de la journée propre, journée sans trade, valeurs des 3 règles du débutant, check-in obligatoire ou non.

### Décisions prises le 8-9 octobre
- **Routine** : on garde le chevron pour la replier (brief 02 §5.1 « toujours dépliée » écarté par Mateo le 9 oct.).
- **Essai Pro : 60 jours**, déjà appliqué en ligne par `sweep-private/billing-config.php` (confirmé par Mateo le 9 oct.) ; le défaut du code (`billing/billing-core.php`, 14 jours) ne sert que sans ce fichier. Reste à faire avec le brief 02 §13 : rappel au jour 50 (aujourd'hui 3 jours avant la fin, `nav.js`), texte du site « Essai Pro de 14 jours » (`website/src/pages4.py`).
- Forfait Free : pas de Mon argent (donc ni rattrapage ni invitation en Free).
- Les estimations du rattrapage comptent comme de l'argent réel partout, y compris dans les cartes « argent » partagées ; seul le bouton « Partager » d'un payout estimé est retiré.
- Routine repliable, sélecteur sur le Calendrier, boutons (bleu = seul bouton principal) : voir sections 5 et 8.

### Demandes non terminées ou mises en pause
- Aucune modification à moitié faite dans le code.
- Captures réelles (Lucid, Tradesea) à essayer en ligne ; import « Performance » de Tradovate sans la règle de 18 h ET.

### En ligne, de ton côté
- SMTP dans `config.php` (le courriel « Ta semaine » passe aussi par lui) ; `app_url` dans `config.php` sert aux liens du courriel (sinon https://app.makeitsweep.com).
- Tâches Cron : `game/cron.php` toutes les 15 min, `chart/cron.php` toutes les heures, `presets/cron.php` le lundi à 5 h.
- `GAME_RELEASE_DATE` et `backup-config.php`.
- Clé Gemini et `model_vision` dans `sweep-private/ai-config.php`.
- La colonne `users.experience` s'ajoute toute seule au premier chargement.
