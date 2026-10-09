# CONTEXTE-APP — Sweep (app.makeitsweep.com)

Référence pour démarrer une nouvelle conversation.
Version : `sweep-app-base.zip` du 9 octobre 2026 (étape 1 du brief + lot A du document UI/UX) — point de départ de la prochaine conversation. État des tests : voir « Passation » à la fin.
⚠️ = information que je ne peux pas garantir à jour : vérifie dans le code.

---

## 1. Architecture

- **Stack** : PHP 8.1 + SQLite (`data/journal.db`), sans framework. Hébergement HostArmada (cPanel, `/home/matnsabc/app.makeitsweep.com`). Mise en ligne par zip téléversé puis « Extraire ».
- **Front** : `app.html` charge le bundle principal (`assets/app.de47127496.js`, minifié). Ce fichier est parfois patché directement par remplacement de chaînes exactes : titres, `ft()`, `mergeCopies`, partage, données d'exemple. Les modules ci-dessous l'enrichissent : ils enveloppent `render()`, `submitAccount()`, `payoutForm()`, `acctTable()`, etc., et observent le DOM.

| Élément | Rôle |
|---|---|
| `api.php` | Routeur API (`/api/...`), auth, migrations, données, partage public, SMTP, CSP. Aussi : migrations automatiques au chargement de `api/data` (date de séance, types de comptes, abonnements mensuels), envoi groupé `api/docs/batch`, admin préréglages |
| `src/nav.js` / `nav.css` | La majorité de l'UI : Aujourd'hui, routine, formulaires, partage, gestes, design system, lecture de captures (« X trades trouvés »), suppression avec Annuler, équilibrage des colonnes |
| `src/ux.js` | Préréglages et ajout de compte guidé, imports CSV (Tradovate, Rithmic, TopstepX, TradingView), admin, **Mon argent** (`moneyOf`, sections 24-27), sélecteur de type de compte, changement de type d'un compte (section 28), **vrai net dès l'arrivée** (section 29, `SweepRealNet`) |
| `src/game.js` | Anneaux, plan, revue, progression, célébrations (`SweepGame`) |
| `src/guide.js`, `src/chart.js`, `src/notify.js` | Guide, graphique TradingView (chargé à la demande), centre de notifications |
| `assets/` | Fichiers servis : un seul CSS `bundle.<hash>.css`, JS hachés, `fonts/` (Geist local, plus de Google Fonts) |
| `game/game.php` | Règles du jeu serveur (anneaux, « dans ton plan », journée réussie, date de séance) |
| `game/cron.php` | Jeu (toutes les 15 min). Le 1er du mois, il envoie aussi « La réalité du mois » via `money/money.php` |
| `money/money.php` | Calcul serveur de l'argent réel du mois, mêmes règles que `moneyOf()` (test de parité) |
| `presets/` | `seed.json` (catalogue), `presets-lib.php` (fusion, validation), `check.php` (vérification d'une firme), `cron.php` (vérification hebdomadaire) |
| `ai/` | Sweep AI (Gemini) : `ai-core.php`, `ai-features.php`, `ai-routes.php`, `ai-stats.php` (table des contrats), `shot-trades.php` (construction des trades depuis une capture), `econ-ai.php` |
| `notify/`, `chart/`, `billing/`, `growth/`, `econ.php` | Notifications, bougies (cron horaire), forfaits Free/Pro/Elite + Stripe, partage public, calendrier économique |
| `ops/` | `build-assets.sh`, `css-order.txt`, `tests.php`, `metrics.php`, sauvegardes |
| `tests/` | `run-all.sh`, tests PHP (`presets_test.php`, `shot_trades_test.php`), Playwright `e2e_*.py`, `samples/` |

## 2. Build et livraison

- **Build** : `sh ops/build-assets.sh`. Il minifie les JS de `src/` en `assets/<nom>.<hash10>.js`, regroupe tous les CSS dans **un seul** `assets/bundle.<hash>.css` (ordre dans `ops/css-order.txt`, `nav.css` en dernier) et réécrit `app.html`. Le bundle principal `app.*.js` garde son nom.
- **Avant le zip** :
  - `node --check` sur chaque JS de `assets/` ;
  - `php -l` sur les PHP modifiés ;
  - `tests/run-all.sh` complet ;
  - vérifier que `app.html` est identique à celui qui a été testé.
- **Zip** : tout le dossier sauf `data/` et `config.php` (`zip -qr … . -x 'data/*' 'config.php'`). Vérifier ensuite que le zip n'en contient aucun.

## 3. Environnement local ⚠️ (le conteneur peut être réinitialisé)

- **Après une réinitialisation (vécu le 8 octobre)** : rien n'existe, il faut tout recréer.
  - `apt-get install -y php-cli php-sqlite3 php-curl php-mbstring` (PHP 8.3 en local, 8.1 en production) et `npm install -g terser csso-cli` (pour le build).
  - `/tmp/g/config.php` : il reprend `config.sample.php` avec `user` = mateo, un mot de passe local, `data_dir` = `/tmp/g/data`, SMTP vide.
  - `/tmp/router.php` : routeur de `php -S` qui reproduit le `.htaccess` (`/` → `api.php?r=app`, `/api/x` → `api.php?r=api/x`, `/r/`, `/s/`, `/uploads/`, et 403 sur `src/`, `tests/`, `config.php`…).
  - Les scripts `run.sh` / `run_ai.sh` exportent `SWEEP_PRESETS_MOCK=/tmp/g/tests/presets_mock.json` et `SWEEP_TEST_DB=/tmp/g/data/journal.db` (+ `SWEEP_AI_CONFIG`, `SWEEP_AI_MOCK` pour `run_ai.sh`).
  - `prof.sh` est devenu `/tmp/prof.py` : connexion de mateo, profil (`POST /api/me/profile`), puis `loadDemo()` **et un clic sur la fenêtre de confirmation** `aside.nav-ask.open [data-ask="1"]` (sinon aucune donnée d'exemple n'est ajoutée).
  - Toutes les requêtes `POST /api/...` doivent porter l'en-tête `X-Requested-With: fetch`.
  - Pour essayer du code sans perturber une suite en cours : une deuxième copie `/tmp/g2` servie sur le port 8096.
  - **Build** : toujours vérifier `node --check src/*.js` **avant** `ops/build-assets.sh` (il s'arrête à la première erreur et laisse les anciens fichiers compilés : une erreur de syntaxe passe inaperçue). Un script `/tmp/build.sh` le fait.
  - Les captures pleine page (`full_page=True`) peuvent laisser des zones vides dans les longues listes : vérifier à l'écran en faisant défiler avant de conclure à un bug.

- **Sources** : `/home/claude/src`. **Copie servie** : `/tmp/g`, copiée par `tar --exclude=./data --exclude=./config.php -cf - . | (cd /tmp/g && tar xf -)`.
- **Serveur** :
  - `/tmp/run.sh <commande>` démarre `php -S 127.0.0.1:8095` (préréglages simulés), lance la commande, puis arrête le serveur.
  - `/tmp/run_ai.sh` fait la même chose avec Sweep AI activé et des réponses simulées : `SWEEP_AI_CONFIG=/tmp/ai-config.php` (n'importe quelle clé) et `SWEEP_AI_MOCK=tests/samples/shot-ai-mock.json`.
- **Base neuve + suite complète** : `/tmp/full.sh` enchaîne `fresh.sh` (base vide), `prof.sh` (profil), `demo.py` (données d'exemple) et `run-all.sh`. Le lancer avec `(setsid nohup /tmp/run_ai.sh /tmp/full.sh > /tmp/full.log 2>&1 &)`, puis lire le log par étapes de moins de 300 s.
- **Compte de test** : `/tmp/show_state.json` (Mateo, données d'exemple). Pour un nouveau compte dans un test : `POST /api/auth/register` puis `/api/me/profile`.
- **Pièges** :
  - **limiteur de tentatives** : `run-all.sh` vide la table `attempts` avant chaque test si `SWEEP_TEST_DB` est défini (c'est le cas dans `full.sh`) ;
  - **ne jamais écrire `pkill -f "php -S"` dans une commande** : ça tue la commande elle-même ;
  - **chaque appel d'outil est limité à 300 s** : la suite complète prend environ 35 min ;
  - **`sessionStorage sw.modal=1`** supprime les fenêtres de première visite ;
  - **`await pg.evaluate("impGo()")`** échoue parfois (passage à #trades pendant l'attente) : utiliser `void impGo()`.

## 4. Tests

- **Suite complète** : `tests/run-all.sh BASE STATE` → « N passed, N failed ». 31 tests au 9 octobre :
  - **PHP** : `presets_test.php` (41), `shot_trades_test.php` (32) ;
  - **Playwright** :
    - `e2e_session_parity`, `e2e_accuracy`, `e2e_clarity`, `e2e_a11y_names` ;
    - `e2e_import_session_day`, `e2e_delete_undo_copy_dates`, `e2e_session_news_ui` ;
    - `e2e_presets_firms`, `e2e_prop_rules`, `e2e_isolation`, `e2e_eval_to_funded`, `e2e_payout_conditions`, `e2e_live_accounts` ;
    - `e2e_acceptance`, `e2e_no_english_in_fr_es`, `e2e_redraw_no_replay`, `e2e_no_jumps`, `e2e_quiet_sync`, `e2e_history_back` ;
    - `e2e_rows_open`, `e2e_plan_journal`, `e2e_import_tradingview`, `e2e_visual_fit` ;
    - `e2e_money`, `e2e_money_parity`, `e2e_shot_multi` (nécessite `run_ai.sh`), `e2e_scroll_stable`, `e2e_realnet`, `e2e_lot_a`.
  - `run-all.sh --all` ajoute les autres scripts `e2e_*` (plus de 100, surtout des captures). ⚠️ Pas relancé récemment ; une dizaine pointent encore vers `/home/claude/media/…` (ancien conteneur).
- **Tests par sujet** :

| Sujet | Tests |
|---|---|
| Préréglages, règles | `presets_test.php`, `e2e_presets_firms`, `e2e_prop_rules`, `e2e_eval_to_funded`, `e2e_payout_conditions` |
| Date de séance, news | `e2e_session_parity`, `e2e_import_session_day`, `e2e_session_news_ui` |
| Mon argent | `e2e_money`, `e2e_money_parity` |
| Captures multi-trades | `shot_trades_test.php`, `e2e_shot_multi` |
| Imports CSV | `e2e_accuracy`, `e2e_import_tradingview` |
| Visuel, stabilité | `e2e_visual_fit`, `e2e_scroll_stable`, `e2e_no_jumps`, `e2e_redraw_no_replay` |
| Langues, accessibilité | `e2e_no_english_in_fr_es`, `e2e_a11y_names` |
| Parcours clés (6 × 3 langues × 2 tailles) | `e2e_acceptance` (~5 min) |
| Arrivée, rattrapage, vrai net, « Estimé » | `e2e_realnet` (~2 min, crée ses propres traders, vide le limiteur d'inscription via `SWEEP_TEST_DB`) |
| Lot A UI/UX (routine, news, boutons, comptes, Net P&L, recherche, espacements, Calendrier, coins, CSV) | `e2e_lot_a` (~2 min) |

- `php ops/tests.php` (suite serveur historique) existe. ⚠️ Pas lancé dans cette série de changements.

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
- **Comptes dépassés** : étiquette or partout, marge affichée à 0 $, placés en bas des listes. « Objectif atteint » seulement si objectif, consistance et jours minimum sont remplis.
- **Suppression** : toujours dans l'app (jamais `confirm()` du navigateur), avec un toast « Annuler » pendant 5 s (`SweepUndo.del`, `SweepUndo.toast`). Ça vaut pour un trade, toutes ses copies, une capture, une question de la checklist, les données d'exemple et un lot importé.
- **Ajout de trade** : la capture d'abord. Une capture avec plusieurs trades ouvre « X trades trouvés » ; avec un seul trade, l'écran habituel s'affiche.
- **Langues** : EN / FR / ES ; montants au format de la langue (FR « 1 688 $ »).
- **Chiffres clés qui ne rentrent pas** (cases KPI : Net P&L, soldes…) : d'abord arrondis au dollar, puis abrégés (« −12,3 k $ », « 1,23 M $ »), et seulement ensuite police réduite. Le montant exact reste dans le libellé (`title`, `aria-label`). Ailleurs, un chiffre trop long rétrécit au lieu d'être coupé.
- **Export CSV de Mon argent** : il contient exactement ce que montre la page (période active, type de compte, firme, compte), via le même `moneyOf`. Nom du fichier : période + filtres. Il n'existe pas de filtre « statut » sur Mon argent.
- **À surveiller** : les onglets Jour et Semaine montrent Réel · Prév. · Préc. sur chaque annonce (« Sans chiffre » pour les minutes et discours). La carte ne quitte jamais sa place sous la journée (l'équilibrage des colonnes ne la déplace pas).
- **Comptes** : le glisser-déposer (ordinateur) et « Modifier l'ordre » (téléphone) marchent dans chaque groupe (Live, Financés, Évaluations, Perso), uniquement à l'intérieur du groupe ; l'ordre est enregistré pour tous les comptes.
- **Forfait Free** : Mon argent n'y est pas. Le rattrapage du vrai net ne s'ouvre pas et l'invitation « Complète ton historique » ne s'affiche pas en Free (un nouveau trader est en essai Pro de 14 jours, donc il l'a).
- **Compte live** : sans préréglage, avec le choix « live de la firme / perso (courtier) ».
- **Essai Pro** : 14 jours (`billing/billing-core.php`).
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
- **Le partage met la discipline en avant.** La carte « argent » montre seulement des payouts nets et le net réel.

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

- **Couleurs (foncé)** : encre #08080A / #0B0B0C, surfaces #151518 / #1C1C20, ligne #2A2A30, texte #F2F2F3, gris #9A9AA2. Bleu #4C8DFF (gains, action), or #D4A24C (pertes, alertes). Le thème clair a ses valeurs.
- **Matière** : un seul verre ; barres et fenêtres en encre translucide floutée.
- **Polices** : Geist et Geist Mono, servies par l'app (aucune police externe).
- **Rayons** : 14 (champs) · 20 (tuiles) · 26 (cartes) · 32 (grands blocs, fenêtres) · capsule pour les boutons.
- **Tailles** :
  - champs à 42 px sur ordinateur, 44 px sur téléphone ;
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

## Passation (9 octobre — étape 1 du brief + lot A du document UI/UX)

### Où on en est
- **Brief d'évolution** (5 étapes, une à la fois) : **étape 1 livrée** (vrai net dès l'arrivée). Étape 2 (règles et journée en trois temps) : pas commencée.
- **Document UI/UX** (« Make It Sweep — UI/UX Improvements & Bug Fixes », 25 points) découpé en 2 lots :
  - **Lot A (corrections ciblées) : livré dans ce zip** — 1.1, 1.2, 1.3, 2, 3, 5, 9, 10, 11, 12, 13, 14, 15.1-15.3, 16.1, 16.2, 17.2, 17.3, 18.1 + Forfait Free.
  - **Lot B (raffinements)** : pas commencé — Stats et Deep Dive (6, 7), Mon argent (8, 18.2), filtres harmonisés sur 7 pages (19 : montrer des captures à Mateo avant de l'étendre partout), boutons/cartes/détails (20-22).
  - Ordre convenu : lot A → lot B → étape 2 du brief.

### Lot A — causes trouvées (pour ne pas les réintroduire)
- 1.2 : l'équilibrage des colonnes déplaçait « À surveiller » ; au redessin, la carte revenait à sa place du gabarit (haut de la colonne droite). Elle n'est plus jamais déplacée.
- 1.1 : le bouton de repli avait été retiré et l'état forcé à « ouvert » par plusieurs couches de CSS (`nav.css`, règles « A1 », « B9 ») ; une règle finale plus précise les remplace.
- 3 : une ancienne règle de survol (`.nav-rt-s:hover .nav-rt-sa .btn.primary{background:none}`) donnait le fond sombre.
- 10 : `decorate()` ne préparait que le premier tableau de la page Comptes (Live).
- 11 : l'ajustement des montants posait une taille inline sans `!important`, battue par le CSS.
- 12 : le champ de recherche recevait le style général des champs (boîte dans la boîte) ; sous 10 trades, le champ était caché mais pas son cadre.
- 15.2/15.3 : l'en-tête ouvert perdait ses coins du bas, au-dessus d'une fiche séparée. 17.2/17.3 : bordure du bas de la dernière ligne qui dépassait sous la carte.
- 1.3 : l'onglet Semaine n'avait jamais affiché les chiffres (seul l'onglet Jour). En local, les valeurs sont vides (calendrier économique manuel).

### Ce qui a changé dans ce zip (depuis le zip de l'étape 1)
- `src/nav.js`, `src/nav.css`, `src/ux.js` (sections 24, 25, 27, 29) ; `assets/` et `app.html` recompilés.
- Tests : `e2e_lot_a.py` (nouveau, suite principale) ; `e2e_money.py` (le Calendrier suit maintenant le sélecteur) ; `e2e_realnet.py` (ressaisie « RETRY » du profil).

### État des tests
- PHP : `presets_test.php` 41/41, `shot_trades_test.php` 32/32.
- **Série complète sur base neuve avec ce zip : 29/31.** Les 2 échecs venaient des tests, corrigés puis relancés seuls : **tous passent**.
  - `e2e_money` vérifiait l'ancienne règle « le Calendrier montre tout » (changée au point 14).
  - `e2e_lot_a` glissait un compte dépassé, que la règle produit garde toujours en bas.
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
- Forfait Free : pas de Mon argent (donc ni rattrapage ni invitation en Free).
- Les estimations du rattrapage comptent comme de l'argent réel partout, y compris dans les cartes « argent » partagées ; seul le bouton « Partager » d'un payout estimé est retiré.
- Routine repliable, sélecteur sur le Calendrier, boutons (bleu = seul bouton principal) : voir sections 5 et 8.

### Demandes non terminées ou mises en pause
- Aucune modification à moitié faite dans le code.
- Captures réelles (Lucid, Tradesea) à essayer en ligne ; import « Performance » de Tradovate sans la règle de 18 h ET.

### En ligne, de ton côté
- SMTP dans `config.php`.
- Tâches Cron : `game/cron.php` toutes les 15 min, `chart/cron.php` toutes les heures, `presets/cron.php` le lundi à 5 h.
- `GAME_RELEASE_DATE` et `backup-config.php`.
- Clé Gemini et `model_vision` dans `sweep-private/ai-config.php`.
- La colonne `users.experience` s'ajoute toute seule au premier chargement.
