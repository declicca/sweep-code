# Audit des parcours — Sweep (app/)

16 octobre 2026. Phase d'audit seulement : aucune ligne de code modifiée.

**Environnement**
- Copie locale isolée de `app/` (port 8097) avec une base SQLite vide.
- Facturation de test : essai Pro de 60 jours comme en production, aucune clé Stripe, Loops coupé (aucun courriel).
- Playwright Chromium à deux tailles :
  - iPhone 390 × 844, tactile ;
  - ordinateur 1440 × 900.
- L'horloge du navigateur et celle du serveur (`SWEEP_GAME_NOW`) ont été réglées pour chaque jour de la semaine simulée, du lundi 19 au vendredi 23 octobre.

**Traders simulés**
- **Alex** : iPhone, anglais, LucidPro 50K.
- **Sam** : ordinateur, anglais, Topstep XFA, Apex PA et Lucid Flex financés, puis un nouveau Combine 100K. Ses écrans clés ont aussi été vérifiés sur iPhone.
- **Léa** : iPhone, français. **Diego** : ordinateur, espagnol.

**Captures** : `captures/` (le numéro est cité entre crochets, ex. [07]).

---

## 1. Résumé en 10 lignes

**Les 3 plus gros freins**
1. **Le coach et le plan peuvent faire échouer l'évaluation.** La perte max proposée et le « il te reste X $ » ne tiennent jamais compte de la marge de drawdown. Alex, à 90 $ de son seuil, se voit proposer « Perte max 1 200 $ · Plan clair » [20][23].
2. **La saisie rapide (P&L seulement) invente des données.** Elle enregistre « Long · 1 contrat · sans heure ». Conséquences :
   - le coach accuse à tort (« contre ton biais ») ;
   - de faux doublons bloquent chaque trade suivant [14] ;
   - l'avertissement de revanche ne se déclenche pas ;
   - les stats sont fausses (« Long 90 % »).
3. **Des chiffres se contredisent sur le même écran** :
   - les copies : +450 $ · 1 trade, et 1,4 k$ · 3 trades à côté [38] ;
   - la discipline : 100 % après une journée de tilt ;
   - le coach : « Rien à corriger, refais pareil » après 2 pertes [15].

**Les 3 meilleures opportunités**
1. **Mettre la marge réelle partout où le trader décide** : plan, coach avant le trade, règle de demain. C'est le moment « wow » qui manque à Alex : « l'app m'a empêché de perdre mon éval ».
2. **Fiabiliser la saisie en 3 touchers** pour qu'elle demande le sens (1 toucher) et note l'heure. Le chemin le plus utilisé devient celui qui nourrit le coach.
3. **Le parcours est déjà bon et motivant.** Exemples :
   - premier trade en 13 touchers ;
   - « Journée balayée » même un jour perdant ;
   - « Ton vrai net : +3 013 $ » pour Sam [35] ;
   - bilan du vendredi [24].

   Retirer les interruptions (bannière Pro pendant l'essai, fenêtre d'installation au 1er trade) laisserait voir ce qui marche.

---

## 2. Mesures

| Parcours | Touchers / clics | Temps humain estimé |
|---|---|---|
| Alex (iPhone, EN) : inscription → 1er trade enregistré | 15, dont 2 de curiosité (« More options ») ; minimum 13 | ~1 min 30 |
| Léa (iPhone, FR) : même parcours | 13 | ~1 min 20 |
| Diego (ordinateur, ES) : même parcours, Topstep | 18 (plan refusé : perte max vide) | ~2 min |
| Sam (ordinateur) : inscription → 1er compte | 15 | ~1 min 30 |
| Sam : 2 comptes de plus « déjà en cours » | ~10 par compte | ~1 min chacun |
| Sam : 1er trade copié sur 3 comptes, avec détails | 7 + saisie | ~45 s |
| Journée complète d'Alex, lundi (plan, 2 trades détaillés, revue) | ~20 | ~2 min |
| Journée de tilt, mardi (plan, 4 trades rapides, revue) | ~22, dont 2 « Ajouter quand même » | ~2 min |
| Journée sans trade, mercredi | 8 | ~30 s |
| Payout / dépense / nouveau compte (Sam) | 4 / 5 / 5 | ~20 s chacun |

Les temps du robot sont plus longs que ceux d'un humain : l'estimation ci-dessus compte ~2 à 3 s par geste.

---

## 3. Journal de friction

Gravité : **B** bloquant, **G** gênant, **m** mineur.

### Alex — débutant, iPhone, LucidPro 50K

| Étape | Ce qu'Alex a fait / pensé | Capture | Gravité |
|---|---|---|---|
| Inscription | « Clair : promesse, Pro 60 jours sans carte, 2 champs. » Bouton visible sans défiler. | [01] | ✓ |
| Bienvenue | « 3 étapes, 2 minutes : OK. » Le gros « + » bleu de la barre du bas attire l'œil. | [02] | ✓ |
| « + » avant d'avoir un compte | Il touche « + » : une 2ᵉ feuille « Ajoute d'abord un compte » repart de zéro (Évaluation / Financé / Live), alors qu'il a déjà tout choisi dessous. Le toast d'avertissement porte une coche ✓ et cache les choix. | [04] | G |
| Choix guidé | Lucid › LucidPro › 50K en 3 touchers, règles résumées (objectif, perte max, perte du jour). Préréglages évidents. | [03] | ✓ |
| Plan | « Biais ? » : jargon non expliqué pour un débutant. Perte max préremplie à 1 200 $, toute la limite du compte, même pour « Je commence ». | [05] | m |
| Formulaire de trade (iPhone) | « Colle ou dépose ta capture (Ctrl+V) » : ni Ctrl+V ni glisser-déposer sur un téléphone. | [06] | G |
| Après le 1er trade | Deux fenêtres en même temps : « Ajoute Sweep à l'écran d'accueil » et la bannière « Bonne semaine. Passe à Pro ». Or Alex est **déjà en Pro** (essai, 60 jours restants), après **un seul** trade. La bannière cache « Compris ». Le message du coach « Trade enregistré · … » passe derrière : Alex ne le voit jamais. | [07] | G |
| Aujourd'hui | La bande des jours montre 28 sept.–2 oct., aujourd'hui (+185 $) est hors écran. Corrigé au rechargement. | [08] | m |
| Aujourd'hui | Sélecteur « Type de compte : Tout · Évaluations · Financés · Live · Perso » affiché avec un seul compte : du bruit. | [15] | m |
| Revue | 4 touchers, puis « Journée balayée · +80 XP » : moment « wow ». | [09] | ✓ |
| Revue | Il note sa discipline 5/5 ; la tuile « Discipline » reste « — ». | — | G |
| Lundi, plan | Repris de vendredi, confirmé en 3 touchers. Le coach dit « 2 trades max », mais le champ « Trades max » reste vide. Le toast « 2 nouveaux · Voir Progression » recouvre le texte du coach. | [10] | m |
| Lundi, trade détaillé | P&L calculé tout seul (+740 $, juste). Le champ « Symbole » déborde de la carte (aussi sur ordinateur) et la date est coupée (« 10/19/202 »). | [11] | m |
| Lundi, 2ᵉ trade | « Saisir à la main » ouvre un **2ᵉ formulaire** différent : « Comme le dernier », heure de sortie, +/−, « Achat/Long ». Deux chiffres s'y contredisent : « Risque du jour restant 1 200 $ » et « Il te reste 1 940 $ avant ta perte max ». Après l'enregistrement, ce formulaire mène à la page du trade, l'autre revenait à Aujourd'hui. | [12] | G |
| Objectif | « Je veux passer mon éval » : Aujourd'hui montre « Marge de drawdown », jamais « 1 085 $ sur 3 000 $ ». Il faut ouvrir le compte. | [22] | G |
| Mardi, 1ʳᵉ perte en saisie rapide | 3 touchers, mais enregistré en « Long · 1 · sans heure » alors qu'il était short 2. | — | B |
| Mardi, revanche 3 min plus tard | Le coach ne dit rien de la revanche : la perte précédente n'a pas d'heure. Après −400 $ puis −300 $, la page du trade dit « Il te reste 900 $ » (vrai reste : 500 $), car le trade sans heure n'est pas compté. | [13] | B |
| Mardi, trades 3 et 4 | « Trade enregistré » s'affiche, mais le trade **n'est pas enregistré** : faux doublon « Ce trade ressemble à celui de . » (heure vide), message en bas de la feuille. Alex doit toucher « Ajouter quand même » à chaque trade. | [14] | B |
| Mardi, Aujourd'hui | Après 2 pertes dont une contre le biais, la carte du coach dit « Dans ton plan. Rien à corriger. Refais exactement pareil. » Elle prend le trade sans heure comme « dernier trade ». | [15] | B |
| Mardi, alertes | Bien : « 82 % de ta limite du jour utilisée (980 $ sur 1 200 $) », puis 94 %, avec notification. | [16] | ✓ |
| Mardi, revue | Bonne leçon (« ce qui t'a coûté le plus : dépasser ton nombre de trades, −430 $ »), mais la revanche n'est pas vue. « Journée balayée », même célébration qu'un jour parfait : ça pousse à loguer la journée perdante (bien), sans un mot pour la reconnaître. | [17] | m |
| Discipline | Tuile à 100 % après la pire journée. Elle ne lit que les réponses de checklist ; les trades sans checklist, la note de revue (2/5) et les règles cassées ne comptent pas. | [15] | G |
| Mercredi sans trade | « Pas de trading aujourd'hui » : le coach rassure (bien). La routine affiche encore « Exécution · Aucun trade · + Trade ». Il faut 3 questions de revue (8 touchers) pour clore un jour où il a décidé de ne pas trader. Sa règle de mardi (« Arrête après 2 trades ») disparaît du plan de jeudi. | [18] | m |
| Bascule de New York | 17 h 30 : mercredi. 18 h 05 : « Bonsoir Alex · jeudi 22 octobre », routine remise à zéro. Correct. | [19] | ✓ |
| Jeudi, plan | **Marge de drawdown : 870 $. Plan proposé : perte max 1 200 $, « Plan clair… à la limite, tu arrêtes ».** En suivant son plan, Alex perd son évaluation. | [20] | B |
| Jeudi, trades | Avant le 2ᵉ trade : « Il te reste 800 $ » (vraie marge : 470 $). Après : « 96 % du drawdown utilisé, 90 $ de marge. Réduis ta taille. » À 90 $ sur NQ (4 points), le seul conseil utile est d'arrêter. Juste dessous : « Rien à corriger. Refais pareil. » | [21] | B |
| Jeudi, revue | « Règle de demain : même plan, même discipline. » | — | B |
| Vendredi, plan | Encore 1 200 $ et « Plan clair », pour 90 $ de marge. | [23] | B |
| Page du compte | Haut de page clair (marge 90 $ « soit 4 points de NQ », objectif 0 / 3 000 $). Le bouton flottant Sweep AI masque la valeur de l'objectif. Juste dessous, toutes les règles de la firme sont modifiables (« Enregistré pendant la frappe ») avec « Appliquer un préréglage » déjà fait : intimidant et risqué. | [22] | m |
| Bilan du vendredi | Beau visuel (anneaux, force, fuite, règle). « Discipline cette semaine 100 % » en haut et « cette semaine : 78 % » en bas. « 1 weeks ago » (faute d'anglais). Le toast Progression recouvre le texte. Rien sur l'évaluation (0 / 3 000 $, drawdown à 96 %). | [24] | G |
| Stats | « Long 90 % » et des durées absurdes, à cause des valeurs devinées de la saisie rapide. | [25] | G |

### Sam — trader établi, ordinateur (et iPhone)

| Étape | Ce que Sam a fait / pensé | Capture | Gravité |
|---|---|---|---|
| Inscription | Claire. L'aperçu de droite montre une ancienne app (« Overview », « Season 1 »). | [30] | m |
| Bienvenue | Badge « Real money » coupé sur 2 lignes. Carte « Live » entourée de bleu comme si elle était choisie. Colonne de droite presque vide. | [31] | m |
| Choix guidé | « Financé › Topstep › **Trading Combine** » et nom proposé « Trading Combine 50K » pour un XFA. Apex : « EOD Trail 50K », sans le nom de la firme. Sam renomme chaque compte. | [32] | G |
| Compte déjà en cours | Solde actuel et plus haut solde, l'info la plus importante pour lui, cachés sous « Plus d'options ». Les frais d'activation (149 $) restent cochés pour un compte ouvert il y a des mois. | [32] | G |
| 3 comptes | ~10 clics par compte, marges cohérentes (Topstep bloquée au départ, Apex départ + 100 $). | [33] | ✓ |
| Ton vrai net | Rattrapage efficace (compteurs par firme), résultat « +3 013 $ depuis janvier », calcul juste : vrai « wow ». Les 2 payouts passés se saisissent en un seul montant, sans firme : l'analyse par firme ne les voit pas. | [34][35] | m |
| Aujourd'hui | Juste après « +3 013 $ », la carte « Mon argent » affiche **0 $ ce mois-ci**. Ses 3 comptes n'apparaissent pas avant le 1er trade ; il reste une bande blanche vide. | [36] | G |
| Trade copié | « Aussi sur » (puces) : parfait pour lui. | [37] | ✓ |
| Copies | Sur le même écran : « +450 $ · 1 trade » (règle : une copie compte une fois), calendrier « 1,4 k$ · 3 trades », ligne du jour « ES · 2 +2 … +1 350 $ ». | [38][39] | B |
| Sans plan | « Exécution : 1 trade sur 1 dans ton plan » alors que Sam n'a pas de plan (le coach le dit juste en dessous). | [38] | G |
| Bannière Pro | « Bonne semaine · Passe à Pro » au 1er trade, pendant l'essai Pro. | [38] | G |
| Payout | 4 clics, split 90 % prérempli. Un payout « demandé » ne réserve rien : le « retirable » reste à 1 425 $. | — | m |
| Partage du payout | Panneau de partage ouvert, puis bouton Retour du navigateur (ou geste retour) : le panneau se ferme, **le voile reste**. L'app est inutilisable jusqu'au rechargement. | [40] | B |
| Dépense | 5 clics, mensuelle. Aucun champ pour noter « TradingView ». | [41] | m |
| Nouveau compte | 5 clics, frais de 99 $ annoncés. Le rattrapage classe les mois Topstep en « évaluation », le nouveau Combine en « abonnement ». | — | m |
| Bilan | Maigre pour lui : ni P&L par compte, ni argent réel (sauf les payouts). | [42] | m |
| iPhone | Comptes, Mon argent et Trades : pas de débordement de page. | [53] | ✓ |

### Forfaits

| Constat | Capture | Gravité |
|---|---|---|
| Essai visible et clair (« Pro · 60 jours restants » dans le menu, badge Pro). | [43] | ✓ |
| La bannière « Passe à Pro » apparaît pendant l'essai Pro, chaque jour gagnant. C'est le seul endroit agressif. | [07][38] | G |
| La page des forfaits ne dit pas ce qui se passe au 61ᵉ jour. Sam (4 comptes) ne sait pas qu'il en gardera 2. Aucun bouton pour garder Pro, seulement « Passer à Elite ». Le prix annuel s'affiche par mois (13,25 $) sans le total facturé (159 $). | [43] | G |
| Fin d'essai : bandeau « Ton essai Pro est terminé. Tes données sont en sécurité. » et choix des comptes. Sobre. | [44] | ✓ |
| La fenêtre dit « Free inclut **1** compte actif » et ne laisse en garder qu'un. Le serveur en garde **2** (limite de la config). Texte et choix sont figés dans le code. | [44] | G (à confirmer avec la config de production) |
| En Free, « Mon argent » est entièrement flouté, y compris les payouts saisis par Sam. C'est la règle décidée ; je le note seulement. | [45] | — |
| Lignes « true » et « AI import » du tableau : elles viennent de ma config de test, non jugées. | [43] | — |

### Langues

| Constat | Capture | Gravité |
|---|---|---|
| Français (Léa, iPhone) : inscription → 1er trade en 13 touchers. Aucun anglais oublié sur Aujourd'hui, Trades, Stats, Comptes, Mon argent. Mêmes interruptions qu'en anglais. Apostrophes droites et courbes mélangées (« d'abord », « aujourd'hui », « d'entrer »). | [50] | m |
| Espagnol (Diego, ordinateur) : Topstep sans limite du jour, donc perte max **vide** dans le plan du démarrage et enregistrement refusé. Le test automatique `e2e_first_run` ne couvre qu'Apex, qui a une limite. | [52] | G |
| Espagnol : restent en anglais « Search notes, setups, tags… » et « — win rate » (page Operaciones). « Importar CSV » apparaît deux fois. | [51] | m |
| Espagnol : « Operación guardada · Contra tu sesgo (bajista) » pour un trade short, enregistré « long » par la saisie rapide. | — | B |

---

## 4. Recommandations (une solution par problème)

| # | Problème | Solution | Impact sur l'usage | Effort | Fichiers |
|---|---|---|---|---|---|
| R1 | Plan et coach ignorent la marge de drawdown | Plafonner la perte max proposée, le « il te reste X $ » (avant et après le trade) et la règle de demain au plus petit de : limite du jour, marge de drawdown du compte (`acctState`). Sous 25 % de marge, la ligne devient « Marge : 90 $. Arrête pour aujourd'hui. » | Évite la perte d'une éval en suivant l'app ; cœur de la promesse | M | `src/game.js` (`openPlan`, `dailyLimit`, `defaultMaxLoss` l. 448-473), `src/coach.js` (`beforeHtml` l. 422-439, `session` l. 342-352, règle de demain) |
| R2 | La saisie rapide enregistre « Long · 1 · sans heure » | Rendre « Long / Short » obligatoire en un toucher sur la feuille rapide (comme le P&L), et noter l'heure de New York de l'enregistrement quand l'heure est vide | Coach juste, revanche détectée, stats exactes, plus de faux doublons | S | `src/nav.js` (`saveOne` l. 2419-2430, `verifyLine` l. 2357) |
| R3 | Faux doublons sur les trades sans heure ni prix | Dans `dupTrade`, ne comparer l'heure que si les deux trades en ont une, et exiger le même P&L quand il n'y a pas de prix | Plus de trades perdus ni de « Ajouter quand même » à répétition | S | `src/nav.js` l. 2213-2219, 2435 |
| R4 | Copies comptées 3 fois sur Aujourd'hui | Appliquer `mergeCopies` dans la carte du mois, la bande des jours et la ligne du jour (garder le badge « +2 ») | Un seul chiffre partout pour Sam | S | `src/nav.js` (`calCard` l. 822-842, `feedStrip` ~l. 790, `tradesHtml`/`byDecision` l. 281-361) |
| R5 | Voile bloquant après Retour sur le partage | Dans `closeTop()`, fermer `#shPanel` avec `closeShare()` | Plus d'app figée (Android, geste retour iPhone) | S | `src/nav.js` l. 177-186 |
| R6 | Bannière « Passe à Pro » pendant l'essai Pro | Ne montrer `green_week` qu'aux traders en Free | Fin du message contradictoire, forfaits « clairs sans être agressifs » | S | `src/app.js` l. 7892 |
| R7 | Deux fenêtres + coach caché après le 1er trade | Repousser la fenêtre d'installation au 2ᵉ jour d'utilisation (jamais le jour de l'inscription, jamais sur ordinateur) | Le 1er retour du coach est vu | S | `src/nav.js` (`install`, l. ~4070-4098) |
| R8 | Coach « Rien à corriger » sur le mauvais trade | Choisir le « dernier trade » par heure d'enregistrement (`created_at`) quand l'heure manque, et ne jamais dire « Rien à corriger » si un trade du jour a un défaut | Le coach ne contredit plus la journée | S | `src/coach.js` l. 241-248, 596 |
| R9 | « Exécution : dans ton plan » sans plan | Sans plan valide, afficher « n trades · pas de plan » au lieu de « dans ton plan » | Cohérence avec le coach | S | `game/game.php` l. 432-454, `src/nav.js` l. 3858 |
| R10 | Tuile Discipline à 100 % après un tilt | Calculer la tuile avec les mêmes règles que le coach (trades « sans erreur » / trades), checklist incluse | Le chiffre le plus visible devient crédible | M | `src/nav.js` (`discScore` l. 4353), bilan hebdo |
| R11 | Objectif de l'éval absent d'Aujourd'hui | Sur la carte Comptes d'Aujourd'hui, pour une évaluation, remplacer la 2ᵉ ligne par « Objectif 1 085 $ / 3 000 $ · marge 870 $ » | Progrès visible, envie de revenir | S | `src/nav.js` (carte `.d-acc`) |
| R12 | Plan vide pour un compte sans limite du jour (Topstep) | Préremplir la perte max avec 50 % du drawdown permis (ou de la marge si plus petite) quand aucune limite du jour n'existe | Démarrage sans blocage pour la firme la plus courante | S | `src/game.js` (`defaultMaxLoss` l. 452-458), `tests/e2e_first_run.py` (cas Topstep) |
| R13 | Nom et étiquette « Trading Combine » pour un compte financé ; nom sans firme | Dans le choix guidé « Financé », afficher et nommer avec le nom du financé (`fundedName` existe déjà : « Topstep XFA 50K », « Apex … PA 50K ») | Moins de renommage, listes lisibles | S | `src/nav.js` (choix guidé, `fundedName`) |
| R14 | Solde actuel caché sous « Plus d'options » | Pour un compte « Financé », poser « Neuf ou déjà en cours ? » dans le choix guidé (avant « Plus d'options ») et décocher les frais si « déjà en cours » | Sam entre ses vrais comptes du premier coup | S | `src/nav.js` (formulaire de compte) |
| R15 | Deux formulaires manuels, deux chiffres de risque | Supprimer la case « Risque du jour restant » du formulaire complet : la ligne du coach (corrigée par R1) suffit | Un seul chiffre | S | `src/nav.js` (ticket manuel) |
| R16 | « Ctrl+V / dépose » sur téléphone | Sur écran tactile : « Touche pour choisir une capture » | Le chemin capture devient compréhensible sur iPhone | S | `src/nav.js` (feuille capture), 3 langues |
| R17 | Mon argent « 0 $ ce mois-ci » après le vrai net | Sur la carte Mon argent d'Aujourd'hui, afficher la période du vrai net tant que le mois en cours est vide (« Depuis janvier : +3 013 $ ») | Le « wow » ne disparaît pas | S | `src/nav.js` (carte `.d-pay`) |
| R18 | Comptes absents d'Aujourd'hui avant le 1er trade | Montrer la carte Comptes dès qu'un compte a un solde différent du départ (compte « déjà en cours ») | Écran utile pour un trader établi dès le 1er jour | S | `src/nav.js` (`stage()`) |
| R19 | Fenêtre de fin d'essai « 1 compte » | Lire la limite Free réelle (`SweepBilling.limit('accounts')`) dans le texte et permettre d'en choisir autant | Texte vrai, aucun compte gelé par erreur | S | `src/app.js` l. 7244 (3 langues), 8059-8069 |
| R20 | Page des forfaits muette sur le jour 61 | Pendant l'essai, une ligne sous « Ton forfait » : « Le 15 déc., tu passes à Free : tu gardes 2 comptes sur 4. Rien n'est facturé. » et un bouton « Garder Pro » | Décision claire, sans pression | S | `src/app.js` (`renderPlans`) |
| R21 | Mercredi sans trade : routine incomplète et revue de 3 questions | Avec « Pas de trading aujourd'hui », marquer Exécution « Journée de repos » et clore la journée sans revue | Le repos compte sans effort | S | `src/nav.js` (routine), `game/game.php` |
| R22 | Règle de mardi perdue après un jour sans trade | Reprendre la dernière règle écrite dans les 7 jours, en sautant les plans « Pas de trading » | La leçon du tilt suit le trader | S | `src/game.js` (`openPlan`, règle du jour) |
| R23 | Petits défauts d'affichage | Liste « Symbole » qui déborde, date coupée, badge « Real money » coupé, toast Progression qui recouvre les feuilles, bande des jours décalée au 1er affichage, bouton flottant sur la valeur de l'objectif | Finition | S | `src/nav.css`, `src/game.js` (`summaryToast`), `src/nav.js` (`feedStrip`) |
| R24 | Textes | « 1 weeks ago » ; anglais restant en ES (« Search notes… », « win rate ») ; apostrophes droites en FR ; prénom au lieu de l'identifiant dans le menu | Qualité perçue | S | `src/coach.js`, `src/app.js`, `src/nav.js` |

---

## 5. À faire maintenant (meilleur rapport impact / effort, dans l'ordre)

1. **R2 + R3 : saisie rapide fiable.** Sens obligatoire en un toucher, heure notée, doublons corrigés. Effort S. Ces deux changements règlent à eux seuls 6 constats : faux doublons, trades perdus, coach qui accuse à tort, revanche non vue, « il te reste » faux, stats fausses.
2. **R1 : la marge réelle dans le plan et le coach.** Effort M. C'est le seul frein qui peut coûter son évaluation à un trader qui suit l'app.
3. **R6 + R7 : retirer les deux interruptions du 1er trade.** Effort S, 2 conditions. Le coach devient visible et les forfaits cessent d'être contradictoires.
4. **R4 + R5 : copies comptées une fois, voile bloquant corrigé.** Effort S chacun. Ce sont deux bugs visibles par tout trader multi-comptes ou mobile.
5. **R8 + R9 : le coach et la routine cessent de dire « dans ton plan / rien à corriger » à tort.** Effort S.

---

## 6. Bugs (séparés du reste)

| # | Bug | Reproduction | Cause | Gravité |
|---|---|---|---|---|
| 1 | Trade non enregistré (faux doublon) | 2 trades en saisie rapide (P&L seulement), même jour, même compte | `dupTrade` : heure vide = 00:00, prix vides ignorés, P&L non comparé (`nav.js` l. 2213-2219) ; message « celui de . » (l. 2435) | B |
| 2 | Sens « long » et 1 contrat inventés | Saisie rapide sans détails | `saveOne`, `nav.js` l. 2422-2427 | B |
| 3 | Voile bloquant | Partager un payout, puis Retour du navigateur ou geste retour | `closeTop()` retire `open` du panneau sans `closeShare()` (`nav.js` l. 184) | B |
| 4 | « Il te reste 900 $ » au lieu de 500 $ sur la page d'un trade | Un trade sans heure, puis un trade avec heure | Tri par heure, les trades sans heure vont en dernier (`coach.js` l. 243) | G |
| 5 | Le coach d'Aujourd'hui commente le mauvais trade (« Rien à corriger ») ; en-tête « Dernier trade · » vide | Un trade sans heure dans la journée | `coach.js` l. 596 | G |
| 6 | Copies additionnées (calendrier, bande des jours, ligne du jour) | Un trade « Aussi sur » 2 comptes | Pas de `mergeCopies` dans `calCard`, `feedStrip`, `byDecision` | G |
| 7 | « Passe à Pro » montré aux traders en essai Pro | N'importe quel trade gagnant pendant l'essai | `app.js` l. 7892 (`!i.trial`) | G |
| 8 | « Free inclut 1 compte actif » alors que la limite est de 2 | Fin d'essai avec 3 comptes ou plus | Texte et choix unique figés (`app.js` l. 7244, 8069) | G (à confirmer avec la config de production) |
| 9 | « Exécution : x sur x dans ton plan » sans plan | Trader sans plan | `game.php` l. 432-454 : sans plan valide, tout trade est « dans le plan » | G |
| 10 | Plan du démarrage refusé, perte max vide | Topstep Combine sans option de limite du jour | `defaultMaxLoss` renvoie '' (`game.js` l. 452-458) | G |
| 11 | Bande des jours sur la mauvaise semaine | Premier affichage, juste après le 1er trade (iPhone) ; rien au rechargement | `feedStrip` défile pendant qu'une fenêtre couvre la page | m |
| 12 | Liste « Symbole » plus large que sa carte | Formulaire rapide › « Vérifier le trade » (iPhone et ordinateur) | CSS `.nav-am-sel` | m |
| 13 | Badge « Real money » coupé sur 2 lignes | Page Bienvenue sur ordinateur | CSS | m |
| 14 | « 1 weeks ago » | Bilan / Stats, 1ʳᵉ semaine | Pluriel anglais | m |
| 15 | Anglais en espagnol : « Search notes, setups, tags… », « — win rate » | Operaciones (ordinateur, ES) | Textes non traduits | m |
| 16 | Les raccourcis clavier (chiffres) changent de page pendant une saisie hors champ | Ordinateur : taper un nombre sans curseur dans un champ ferme la feuille ouverte | Raccourcis actifs alors qu'une feuille est ouverte | m |

---

## 7. Ce qui marche (à garder tel quel)

- Choix guidé des comptes : Lucid en premier, règles résumées, marges exactes pour Topstep, Apex et Lucid.
- Plan repris de la veille et confirmé en 2 touchers.
- Alertes 75 % / 94 % de la limite du jour, avec notification.
- « Journée balayée » qui récompense aussi la journée perdante et le jour de repos.
- Bascule de journée à 18 h (heure de New York).
- « Ton vrai net » : rapide, juste et marquant.
- Payout, dépense et nouveau compte en 4 à 5 clics.
- « Aussi sur » pour les trades copiés.
- Fin d'essai sobre : « tes données sont en sécurité ».
- Bilan du vendredi visuel, avec force, fuite et règle.
- Aucune erreur console ni requête en échec pendant tous les parcours.

---

## Limites de l'audit

- Pas de Safari réel : Chromium simule l'iPhone.
- Sweep AI et la lecture de captures n'ont pas été testés (réponses simulées en local).
- Stripe n'a pas été testé : aucune clé de test n'est disponible dans la copie locale, donc le passage payant à Pro/Elite (Stripe Checkout) n'a pas pu être fait.
- Les règles des firmes n'ont pas été revérifiées.
- Les notifications affichent « il y a 4 jours » à cause du décalage d'horloge du test : ce n'est pas un bug de l'app.
