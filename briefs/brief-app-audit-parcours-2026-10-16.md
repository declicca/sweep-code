# Brief App — corrections issues de l'audit des parcours (16 oct. 2026)

À l'attention de la conversation App. Source complète : `docs/audit-parcours/AUDIT-PARCOURS.md` (journal de friction, captures dans `docs/audit-parcours/captures/`).

## Contexte

Un audit a fait vivre Sweep à deux traders simulés.
- **Environnement** : copie locale, base vide, Playwright, iPhone 390 px et ordinateur 1440 px, semaine du 19 au 23 oct. simulée par l'horloge.
- **Alex** : débutant, LucidPro 50K, iPhone.
- **Sam** : 3 comptes financés et des payouts, ordinateur.
- **Langues** : refait en FR (iPhone) et en ES (ordinateur).

**Ce qui marche et ne doit pas bouger** : choix guidé des comptes, plan repris de la veille, alertes 75 % / 94 % de la limite du jour, « Journée balayée », bascule à 18 h ET, « Ton vrai net », payout / dépense / compte en 4 à 5 clics, « Aussi sur », fin d'essai sobre, bilan du vendredi.

## Règles pour ce chantier

- **Une étape à la fois.** À la fin de chaque étape :
  - tests ciblés + vérification à 390 × 844 et 1300 × 850 ;
  - liste des fichiers modifiés ;
  - attendre mon accord avant l'étape suivante.
- **Textes** : tout texte nouveau ou modifié existe en EN / FR / ES.
- **Code** : modifier `src/`, puis `sh tools/build.sh` ; jamais les fichiers de `assets/`.
- **Données** : aucune modification des trades existants des traders. Les corrections valent pour les nouveaux enregistrements et l'affichage.
- **Règles décidées** : mettre `CONTEXTE-APP.md` à jour (et sa Passation) dans le même commit quand une règle change.
- **Avant de coder** : si une solution ci-dessous contredit une règle décidée, le dire avant de coder.
- **Déploiement** : jamais sans mon accord explicite.

---

## Étape 1 — Saisie rapide fiable (bloquant, effort S)

**Problème observé**
- Sur la feuille « Nouveau trade / par capture », un trader qui tape seulement son P&L net obtient un trade « Long · 1 contrat · sans heure ».
- Conséquences :
  - le coach dit « Contre ton biais » à un trader short (vu en EN et en ES) ;
  - la revanche (« dernière perte il y a moins de 10 min ») ne se déclenche jamais ;
  - le « il te reste X $ » de la page du trade oublie le trade sans heure (900 $ affichés au lieu de 500 $) ;
  - le 2ᵉ trade rapide de la journée est pris pour un doublon et **n'est pas enregistré** : « Ce trade ressemble à celui de . », avec une heure vide ;
  - les stats indiquent « Long 90 % ».

**Causes**
- `src/nav.js` `saveOne()` l. 2419-2430 :
  - `SH.dir` vide devient `'long'` (l. 2424) ;
  - les contrats valent 1 (l. 2422) ;
  - `entry_time` reste vide (l. 2427).
- `dupTrade` / `SweepDupOf` l. 2213-2219 :
  - une heure vide vaut 00:00 ;
  - les prix vides sont ignorés ;
  - le P&L n'est jamais comparé.
- Le message est construit l. 2435 avec l'heure vide.

**À faire**
1. Sur la feuille rapide, « Long / Short » devient obligatoire, en un toucher, à côté du P&L. Sans sens choisi, « Enregistrer » le demande, comme pour le P&L.
2. Si l'heure d'entrée est vide à l'enregistrement, noter l'heure actuelle de New York (même règle de date de séance qu'ailleurs).
3. `dupTrade` :
   - ne comparer l'heure que si les deux trades en ont une ;
   - sans prix, exiger le même P&L ;
   - le message ne s'affiche jamais avec une heure vide.

**Tests**
- Étendre `e2e_trade_dup` et `e2e_trade_form` :
  - 2 trades rapides de P&L différents ⇒ 2 trades enregistrés sans alerte ;
  - un trade short rapide ⇒ `direction: short` et pas de « contre ton biais » avec un biais baissier ;
  - un trade rapide ⇒ `entry_time` rempli ;
  - un vrai doublon ⇒ toujours détecté.

## Étape 2 — La marge réelle dans le plan et le coach (bloquant, effort M)

**Problème observé** : Alex (LucidPro 50K) a 870 $, puis 90 $ de marge de drawdown.
- Le plan propose « Perte max 1 200 $ · Plan clair… à la limite, tu arrêtes ».
- Le coach dit « Il te reste 800 $ / 1 460 $ avant ta perte max ».
- À 90 $, il conseille « Réduis ta taille ».
- La règle de demain est « Même plan, même discipline ».
- En suivant l'app, il perd son évaluation.

**Causes**
- Plan : `src/game.js` `openPlan` l. 472-473, `dailyLimit()` l. 448-451, `defaultMaxLoss()` l. 452-458. Seule la limite du jour (`dll_c`) sert de plafond, jamais la marge (`acctState`).
- Coach : `src/coach.js`
  - `beforeHtml` l. 422-439 : X = perte max du plan + net du jour ;
  - `session()` l. 342-352 ;
  - `limits()` l. 448-462 ne prend le dessus qu'à 75 % et plus.

**À faire**
1. La perte max proposée par le plan est plafonnée au plus petit de :
   - la limite du jour la plus stricte (comme aujourd'hui) ;
   - **la marge de drawdown** du compte (`acctState`, le chiffre de la page du compte).

   Le texte sous le champ dit lequel s'applique, par exemple « Marge de drawdown de LucidPro 50K : 870 $ ».
2. Les lignes « Il te reste X $ » (avant le trade, message « Trade enregistré », page du trade) utilisent le même plafond.
3. Sous 25 % de marge (ou sous ~1 point de l'instrument le plus tradé à sa taille habituelle) :
   - la ligne devient « Marge : 90 $. Arrête pour aujourd'hui. » au lieu de « Réduis ta taille » ;
   - la règle de demain proposée devient « Perte max {marge} $ ou pas de trade ».
4. Compte sans limite du jour (Topstep Combine sans l'option) : aujourd'hui la perte max reste **vide** et le plan du démarrage est refusé (vu en ES). Préremplir avec le plus petit de :
   - 50 % du drawdown permis ;
   - la marge.

**Tests**
- Étendre `e2e_coach` et `e2e_first_run` (ajouter un cas Topstep sans limite du jour).
- Nouveau cas : compte à 870 $ de marge ⇒ plan prérempli à 870 et coach à 870 ; à 90 $ ⇒ « Arrête pour aujourd'hui ».
- Garder la parité avec le serveur (`e2e_rule_parity`, `e2e_routine_parity`) si les règles serveur sont touchées.

## Étape 3 — Retirer les interruptions du 1er trade (gênant, effort S)

**Problème observé** : juste après le 1er trade, deux fenêtres s'ouvrent en même temps.
- « Ajoute Sweep à l'écran d'accueil ».
- Une bannière « Bonne semaine. Passe à Pro » :
  - à un trader **déjà en essai Pro** ;
  - après un seul trade ;
  - puis chaque jour gagnant pendant 60 jours.

La bannière cache « Compris ». Le message du coach « Trade enregistré · … » n'est jamais vu. Même chose sur ordinateur, où la fenêtre d'installation donne des consignes iPhone / Android.

**Causes**
- `src/app.js` l. 7892 : la condition `i.plan !== "free" && !i.trial` laisse passer un essai Pro ; déclenchée par `billNudge` l. 8231.
- Fenêtre d'installation : `src/nav.js` vers l. 4070-4098.

**À faire**
1. `green_week` seulement pour les traders en Free.
2. La fenêtre d'installation n'apparaît jamais le jour de l'inscription ni sur ordinateur : au plus tôt au 2ᵉ jour d'utilisation, sur téléphone.

**Tests** : `e2e_first_run` — après le 1er trade, aucune bannière Pro et aucune fenêtre d'installation ; le message du coach est visible.

## Étape 4 — Copies comptées une fois, voile bloquant (effort S)

**Problème observé**
- **Copies** : un trade copié sur 3 comptes s'affiche sur le même écran comme :
  - « +450 $ · 1 trade » (règle décidée : une copie compte une fois) ;
  - « 1,4 k$ · 3 trades » dans le calendrier du mois ;
  - « ES · 2 +2 … +1 350 $ » dans la ligne du jour.
- **Voile** : pendant le partage d'un payout, le bouton Retour (ou le geste retour) ferme le panneau mais laisse le voile. L'app est inutilisable jusqu'au rechargement.

**Causes**
- `src/nav.js` : `calCard` l. 822-842, `feedStrip` (~l. 790) et `byDecision` l. 281-291 / `tradesHtml` l. 347-361 additionnent les copies, sans `mergeCopies`.
- `closeTop()` l. 177-186 : pour `#shPanel`, il retire seulement `open`, sans `closeShare()`.

**À faire**
1. Ces trois vues comptent les copies comme `mergeCopies` (P&L de la copie principale, n = 1). Le badge « +2 » reste.
2. `closeTop()` appelle `closeShare()` pour le panneau de partage.

**Tests**
- `e2e_money_parity` ou nouveau test : trade copié sur 3 comptes ⇒ mêmes chiffres dans le calendrier, la bande des jours, la ligne du jour et la performance.
- `e2e_history_back` : ouvrir le partage, Retour ⇒ aucun `#shScrim.open`, la page répond.

## Étape 5 — Le coach et la routine ne disent plus « dans ton plan » à tort (effort S)

**Problème observé**
- Après 2 pertes dont une contre le biais, la carte du coach d'Aujourd'hui dit « Dans ton plan. Rien à corriger. Refais exactement pareil. ».
- Sans plan, la routine affiche « Exécution : 1 trade sur 1 dans ton plan », alors que le coach dit juste en dessous « Pas de plan pour cette séance ».

**Causes**
- `src/coach.js` l. 596 : le « dernier trade » est le dernier après un tri par heure (`'99:99'` pour les trades sans heure, l. 243).
- `game/game.php` l. 432-454 : sans plan valide, tout trade compte « dans le plan ».

**À faire**
1. Le « dernier trade » est le plus récent par heure d'entrée, sinon par `created_at`. La carte ne dit jamais « Rien à corriger » si un trade du jour a un défaut.
2. Sans plan valide, la routine affiche « n trades · pas de plan » au lieu de « dans ton plan ». À garder identique côté serveur et côté navigateur.

**Tests** : `e2e_coach`, `e2e_routine_parity`.

---

## Après ces 5 étapes (ne pas commencer sans mon accord)

Liste dans l'ordre, détails et fichiers dans `AUDIT-PARCOURS.md`, section 4 :
- **R10** : tuile Discipline calculée comme le coach. Elle affiche 100 % après un tilt car elle ne lit que la checklist (`discScore`, `nav.js` l. 4353).
- **R11** : objectif de l'évaluation sur la carte Comptes d'Aujourd'hui (« 1 085 $ / 3 000 $ · marge 870 $ »).
- **R13 / R14** : choix guidé « Financé ».
  - Nom et étiquette du financé (« Topstep XFA 50K », pas « Trading Combine 50K » ; « Apex … PA 50K », pas « EOD Trail 50K »).
  - « Neuf ou déjà en cours ? » sorti de « Plus d'options », frais décochés si « déjà en cours ».
- **R19 / R20** : forfaits.
  - La fenêtre de fin d'essai dit « 1 compte actif » en dur alors que la limite configurée en garde 2 (à vérifier avec la config de production).
  - La page des forfaits ne dit pas ce qui se passe au 61ᵉ jour.
- **R15, R16, R17, R18, R21, R22** : petites cohérences.
  - Deux chiffres de risque contradictoires dans le formulaire manuel.
  - « Ctrl+V » sur téléphone.
  - « Mon argent : 0 $ ce mois-ci » juste après le vrai net.
  - Comptes absents d'Aujourd'hui avant le 1er trade.
  - Journée sans trade.
  - Règle du jour perdue.
- **R23 / R24** : finition.
  - Liste « Symbole » qui déborde, badge « Real money » coupé, toast Progression qui recouvre les feuilles.
  - « 1 weeks ago », anglais restant en ES (« Search notes… », « win rate »), apostrophes FR.

## À ne pas faire

- Pas de refonte des formulaires (les deux formulaires manuels restent ; on retire seulement la case de risque en double, plus tard).
- Pas de nouvelle fonction qui ne répond pas à un problème listé ici.
- Ne pas toucher à la règle « Mon argent n'est pas dans Free ».
