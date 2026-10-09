# Sweep — installation complète (app.makeitsweep.com)

Version complète de l'app au 3 octobre 2026. Ce zip **ne contient jamais** `config.php`, le dossier `data/` ni les fichiers propres au serveur (`.user.ini`, `php.ini`, `cgi-bin`, `.well-known`) : ils restent intacts sur le serveur.

---

## 1. Mettre à jour le serveur

1. **Sauvegarde** : cPanel → Gestionnaire de fichiers → clic droit sur `data` → Compresser → télécharger le zip.
2. Téléverser `sweep-app-complet.zip` dans `app.makeitsweep.com`, puis **Extraire** en acceptant de remplacer les fichiers.
3. Supprimer le zip téléversé.
4. Ouvrir l'app, se connecter, vérifier l'Aperçu (voir la liste du point 5).

> Conseil : extraire d'abord sur le site de test (`trade.agencedeclic.ca`) avec une copie anonymisée de la base (`ops/staging-copy.php`, point 4), puis en production.

---

## 2. Fichiers privés (`/home/matnsabc/sweep-private/`, hors du dossier web)

| Fichier | Modèle dans le zip | Rôle | Obligatoire |
|---|---|---|---|
| `ai-config.php` | — (déjà en place) | Clé Gemini, Sweep AI | Oui |
| `billing-config.php` | — (déjà en place) | Stripe, forfaits, essai 60 jours, bonus de campagne (`campaign_grants`) | Oui |
| `chart-config.php` | `chart/chart-config.sample.php` | Clé Databento, budget quotidien, délai de 24 h | Oui (graphiques) |
| `backup-config.php` | `ops/backup-config.sample.php` | Phrase de passe des sauvegardes, copie hors serveur S3 | **Oui** |
| `discord-config.php` | `game/discord-config.sample.php` | Bot des rangs Discord | Non |

⚠️ La phrase de passe des sauvegardes doit aussi être gardée **hors du serveur** (gestionnaire de mots de passe).

---

## 3. Tâches planifiées (cPanel → Cron Jobs)

Mettre ton courriel dans « Cron Email » pour recevoir les rapports et les alertes.

| Fréquence | Commande | Rôle |
|---|---|---|
| Toutes les 15 min (`*/15 * * * *`) | `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/game/cron.php >/dev/null 2>&1` | Journées, streaks, ligues, Wrapped, rappels, fin d'essai, moments « wow », Discord |
| Toutes les heures (`0 * * * *`) | `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/chart/cron.php >/dev/null 2>&1` | Téléchargement des graphiques, « Ton graphique est prêt » |
| Le lundi à 5 h (`0 5 * * 1`) | `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/presets/cron.php >/dev/null 2>&1` | Vérification des préréglages prop firms sur les pages officielles (Gemini + Google Search), mise à jour automatique |
| Chaque jour 3 h 30 (`30 3 * * *`) | `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/backup.php` | Sauvegarde chiffrée (silencieuse si tout va bien) |
| Chaque lundi 6 h (`0 6 * * 1`) | `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/restore-test.php` | Test de restauration + intégrité (rapport par courriel) |

---

## 4. Outils (terminal cPanel)

```
# Tests automatiques (base jetable) : doit afficher « 20 passed, 0 failed »
/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/tests.php

# Copie anonymisée de la production vers le site de test
/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/staging-copy.php /home/matnsabc/trade.agencedeclic.ca/data/journal.db

# Restaurer une sauvegarde (voir les instructions dans le fichier)
/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/restore.php <fichier.enc> <sortie>
```

---

## 5. Vérification après chaque mise à jour (5 minutes)

1. Connexion, puis l'Aperçu s'affiche (anneaux, raccourcis, aucune erreur).
2. Ajouter un trade avec le graphique (un jour de semaine de plus de 24 h).
3. Ouvrir le récap d'un trade : bougies, entrée, sortie, stop, objectif.
4. Faire la revue de 60 secondes : la journée se balaie.
5. Importer un fichier CSV (exemples dans `tests/samples/`).
6. Avis de l'IA ou Ask Sweep répond.
7. Cloche : les notifications s'ouvrent.
8. Réglages → Tout exporter (ZIP) se télécharge.
9. Changer de langue (FR / EN / ES) : rien ne reste dans l'autre langue.
10. Admin → Tableau de bord : les chiffres s'affichent, « Erreurs (24 h) » est à 0 ou presque.

---

## 6. Ce que contient cette version

- **Journal** : saisie au toucher sur de vrais graphiques CME (Databento, délai de 24 h), Log with AI, imports CSV Tradovate, Rithmic R|Trader Pro et TopstepX (détection automatique, frais conservés), copie sur plusieurs comptes.
- **Prop firms** : préréglages (à vérifier), drawdown fin de journée (dépassement en cours de journée détecté), fixe ou par trade, consistance, compteur « prêt pour le payout », payouts et dépenses.
- **Discipline gamifiée** : anneaux, streak et gels, XP, rangs, badges, parcours, missions, boss, revue du vendredi et coffre, Edge Reveal, Wrapped mensuel et annuel, saisons, ligues, crew, buddy, Discord. Déblocage progressif (`game/catalog.php`, `GAME_UNLOCKS`).
- **Prise en charge** : visite guidée, checklist en 3 étapes, astuces, centre d'aide, états vides, onboarding après le premier trade.
- **Forfaits** : Free pour toujours, Pro 60 jours offerts, bonus cohorte 100 (30 jours d'Elite), parrainage (14 jours d'Elite pour le filleul), comptes gelés (jamais supprimés) après l'essai, rappels aux jours 50 et 58.
- **Fiabilité** : sauvegardes chiffrées et test de restauration, tests automatiques, erreurs navigateur remontées, tableau de bord admin (étoile polaire, activation, rétention, coût IA, erreurs, revenu).
- **Navigation téléphone** : Accueil · Trades (Trades, Calendrier, Journal) · + · Analyses · Plus. En haut : recherche (pages, trades, fonctions, réglages), cloche, avatar (Progression, Réglages, Forfait, Guide, Déconnexion).
- **Progression** : une seule page pour toute la gamification (raccourcis, ce qui se débloque ensuite, collection).
- **Saisie rapide** : 10 setups populaires en un toucher (tes propres setups en premier).

Le détail technique de chaque module est dans `README.md`.

---

## 7. En attente (hors de l'app)

- Réponse de ProjectX / Topstep pour la synchronisation TopstepX par clé API.
- Candidature à l'écosystème NinjaTrader pour Tradovate.
- Vérifier les valeurs des préréglages de prop firm sur les sites des firmes.
- Faire valider la Loi 25 et les taxes (TPS/TVQ) par un professionnel.

## Vérifier qu'une mise à jour est en ligne

- Réglages → À propos affiche « Version xxxxxxx · date ». Après chaque extraction, ce code change.
- Les traders n'ont rien à faire : une page déjà ouverte vérifie la version quand ils reviennent sur l'app, quand ils changent de page et toutes les 10 minutes. Si une nouvelle version est en ligne, l'app se recharge d'elle-même (ou propose « Mettre à jour » s'ils sont en train d'écrire).
- Pour tester toi-même : https://app.makeitsweep.com/api/version affiche le code de la version en ligne.

## Préréglages prop firms (firme → type de compte → taille → phase)

- Catalogue livré : `presets/seed.json`. Chaque type de compte indique dans `verified` les pages consultées et la date. Version tenue à jour : `data/presets-live.json` (écrite par la vérification). Un nouveau `seed.json` livré dans une mise à jour remplace toujours une version vérifiée plus ancienne.
- Chaque lundi, `presets/cron.php` relit les pages officielles de chaque firme : limites, **règles de payout** (jours gagnants et minimum par jour, plafond par demande ou échelle, consistance, filet de sécurité, nombre max de payouts) et **prix** (évaluation, activation). Chaque chiffre est validé. Un changement douteux (plafond ou prix qui change de plus de la moitié, échelle qui change de longueur, moitié des comptes disparus…) n'est jamais appliqué : la firme passe « à revoir ». Une valeur absente de la page est gardée.
- **Admin → Préréglages** : date de la dernière vérification complète, statut par firme (inchangé / mis à jour / à revoir / erreur), changements et erreurs, bouton « Vérifier maintenant » (une firme à la fois, réservé aux administrateurs).
- **Alerte 8 jours** : sans vérification complète depuis 8 jours, une alerte rouge s'affiche dans Admin et un courriel part vers `support_email` (au plus une fois par jour). C'est l'app qui surveille (une fois par heure), donc l'alerte fonctionne même si la tâche cPanel est arrêtée. Les courriels passent par le réglage `smtp` de `config.php`.
- **Changement de règles** : quand une firme passe « mis à jour », chaque trader qui a un compte actif fait avec ce préréglage reçoit une notification qui résume ce qui change pour son compte. Le compte garde ses règles ; sur sa page, le trader choisit « Appliquer les nouvelles règles » ou « Garder mes règles ».
- Choix à l'achat : Topstep « Standard / Consistance » (au compte financé ou au passage en financé), Apex « Règles d'avant mars 2026 » (type de compte Legacy, gardé tel quel par la vérification).
- Tester sans réseau ni IA : `php tests/presets_test.php` (dossier temporaire, données réelles intactes). Vérification simulée sur une copie : `SWEEP_PRESETS_MOCK=tests/presets_mock.json php presets/cron.php --firm=apex --dry-run`.
- Tester sans rien changer : `php presets/cron.php --dry-run` (une seule firme : `--firm=lucid`). Revenir à la version précédente : `php presets/cron.php --rollback`.
- Ajouter une firme : ajoute-la dans `presets/seed.json` avec son `id`, son `name` et ses `sources` (pages officielles) et une liste `programs` vide ; la vérification suivante la remplit. Une firme sans compte n'est pas proposée aux traders.

## Fichiers sources et construction

- Les modules de Sweep (`nav`, `game`, `ux`, `guide`, `notify`, `chart`) sont servis **minifiés** depuis `assets/`. Leurs versions lisibles sont dans `src/` (non accessibles depuis le web).
- Après une modification dans `src/`, reconstruire : `sh ops/build-assets.sh` (nécessite Node avec `npm install -g terser csso-cli`). Le script minifie, renomme chaque fichier avec son empreinte et met `app.html` à jour.

## Tests (environnement de développement)

- `sh tests/run-all.sh [url] [session]` : lance le test serveur (préréglages) et tous les tests de bout en bout qui vérifient leur propre résultat, puis affiche « N passed, N failed » (détails dans `/tmp/sweep-run-all.log`). `--all` ajoute les anciens scripts de captures, comptés en échec seulement s'ils plantent.
- Il faut l'app servie localement (`php -S`) avec une session administrateur enregistrée (Playwright `storage_state`).

## Construction des fichiers servis

- `sh ops/build-assets.sh` : minifie les modules de `src/`, les nomme avec une empreinte, et réunit toutes les feuilles de style en un seul fichier (`assets/bundle.<empreinte>.css`, ordre dans `ops/css-order.txt`). Le module des graphiques (`chart.js`) se charge à la demande (`window.SWEEP_LAZY` dans `app.html`).
- La date d'un trade est sa séance (18 h ET = lendemain). Au premier chargement après la mise à jour, le serveur marque une fois les trades existants (`session_date: true`) et déplace les anciens trades du soir datés du calendrier.

## Plusieurs trades sur une capture (Sweep AI)

- Une capture d'historique (fills ou trades fermés) donne tous ses trades dans « X trades trouvés » ; une capture d'un seul trade garde l'écran habituel. Gemini recopie les lignes, `ai/shot-trades.php` calcule (FIFO, P&L, frais, fuseau, séance de 18 h).
- Enregistrement en une transaction (`api/docs/batch`), avec `import_batch_id` sur chaque trade ; « Annuler » retire le lot. Aucune migration SQL : le champ est dans les données du trade.
- Tests : `php tests/shot_trades_test.php` ; `tests/e2e_shot_multi.py` avec un serveur lancé avec `SWEEP_AI_CONFIG` (n'importe quelle clé) et `SWEEP_AI_MOCK=tests/samples/shot-ai-mock.json` (réponses simulées, aucun crédit).
