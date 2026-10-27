# SWEEP.md — la carte du parcours (référence)

Rédigé le 20 octobre 2026, **approuvé par Mateo le 21 octobre** avec 4 ajustements : mesure d'abord, nouvel ordre des étapes, comptes existants gardés, missions cochées par un comportement. Version analysée : `origin/main` au commit `590bd3f`.

**Avancement (27 oct.)** : étapes 0 et 1 en ligne (le commit vert `ade074b` est servi par app.makeitsweep.com ; date exacte du déploiement à confirmer par Mateo, puis à noter dans `docs/parcours/MESURE-0.md`). Étape 2 faite, en attente de la semaine de mesure. Étape 3 en cours (lots a et b faits). Étapes 4 à 6 à faire (section 7).

**Priorité de Mateo (27 oct.)** : garder les traders actuels, avec l'utilisation la plus simple et la plus rapide. L'ordre des travaux est donc :
1. `briefs/brief-app-activation-2026-10-27.md`, étape A (les défauts) ;
2. `briefs/brief-app-boucle-quotidienne-2026-10-27.md` (une journée à 2 trades passe d'environ 35 touchers à 15 : plan express, plus d'interruption après un trade, « Fermer ma journée », puis « Maintenant ») ;
3. `briefs/brief-app-nouveau-trader-2026-10-27.md` (étapes 1 et 2 faites, revue : corriger R1 ; accompagner un nouveau trader : 8 petites corrections, les garde-fous de la mission deviennent les valeurs du plan, chaque terme expliqué, Stats sans tuiles vides) ;
4. les étapes C à F du brief d'activation.

**Statut** : c'est la référence de tous les développements à venir sur l'app. En cas de désaccord avec un brief plus ancien, ce fichier gagne sur le **parcours** (ce qui est visible, où, quand). `app/CONTEXTE-APP.md` reste la référence des **règles** : calculs, argent, prop firms, tests, design.

---

## 0. Le principe

**Gel des nouvelles fonctions.** On ne travaille que le parcours : ranger, fusionner, cacher, faire découvrir. Une demande de nouvelle fonction attend la fin du chantier.

**Chaque écran, chaque carte, chaque bouton sert un des 3 moments, ou il quitte la vue** : il va dans Réglages, dans sa page, ou il attend une mission.

| # | Moment | Quand (heure de New York) | Ce que le trader doit obtenir |
|---|---|---|---|
| **M1** | **Les premières minutes** | Inscription → premier compte → première chose utile | En moins de 2 min : son compte, son **risque permis aujourd'hui** (en $), et une première action faite (plan ou trade) |
| **M2** | **La boucle quotidienne** | La journée de séance : 18 h la veille → 18 h | **Avant** (jusqu'à 9 h 30) : risque permis + mission du jour. **Pendant** : « il te reste X $ », ajouter un trade. **Après** : fermer la journée en **un toucher** |
| **M3** | **Le vendredi** | Dernier jour de trading, dès la revue ou 17 h, jusqu'au dimanche 23 h 59 | Le bilan de la semaine, puis la règle de la semaine suivante |

**Aujourd'hui dit quoi faire maintenant.** Une seule carte en tête, qui change selon le moment : une phrase, un chiffre, **un seul bouton bleu**. Le reste est secondaire, plus bas ou ailleurs.

**La gamification sert d'onboarding.** Chaque mission fait découvrir **une** fonction, avec un bouton qui l'ouvre. Une fonction non encore découverte n'est pas montrée au jour 1. Elle apparaît quand sa mission arrive, ou quand le contexte la rend utile (ex. le copy trading au 2ᵉ compte).

---

## 1. Inventaire : tout ce que l'app montre, et le moment servi

Légende de la colonne **Moment** : M1 / M2 / M3, ou **—** si l'élément ne sert aucun des trois.

Légende de la colonne **Cible** :
- **Garder** : reste visible tel quel.
- **Fusion** : rejoint un autre élément.
- **Page** : reste dans sa page, sort d'Aujourd'hui.
- **Réglages** : déplacé dans les réglages.
- **Mission** : caché jusqu'à sa mission.
- **Retirer** : code mort, ou doublon sans valeur.

### 1.1 Navigation globale

| Élément | Où (code) | Moment | Cible |
|---|---|---|---|
| Barre du bas (téléphone) : Aujourd'hui · Trades · **+** · Stats · Comptes | `app.html:58` | M2 | **Garder** |
| Menu de gauche (ordinateur) : Nouveau trade, Aujourd'hui, Trades, Stats, Comptes, Progression, recherche, cloche, avatar | `app.html:30` | M2 | Garder. **Progression sort du menu** (voir 4.4) |
| Menu de l'avatar : en-tête (forfait) → `#plan`, Progression, Quoi de neuf, Réglages, Abonnement, Parrainage, Donner mon avis, Aide, Traders (admin), Déconnexion | `nav.js:102` | — | Garder, allégé : **« Abonnement » en double** avec l'en-tête (en garder un) ; Progression devient « Ma progression » (voir 4.4) |
| Sous-onglets Trades : Liste · Calendrier · Journal | `nav.js:69` | M2 | Garder |
| Sous-onglets Comptes : Comptes · Mon argent | `nav.js:69` | M2 / M3 | Garder |
| Recherche et palette de commandes (fonctions, aide, Sweep AI) | `app.js:3094`, `nav.js:217` | — | Garder (filet de sécurité, aucun coût visuel) |
| Raccourcis clavier N, 1–7, /, j/k | `app.js:10304` | M2 | Réglages › Avancé (déjà) |
| Cloche (notifications) | `notify.js:240` | M2 / M3 | Garder |
| Sweep AI : bouton flottant (téléphone), menu de gauche (ordinateur) | `ux.js` §23 | — | **Mission** (voir 5) : pas au jour 1 |
| Gestes : retour ferme la feuille, tirer pour actualiser, glisser pour supprimer, glisser pour fermer | `nav.js` | M2 | Garder |

### 1.2 Arrivée (M1)

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Inscription (courriel, mot de passe), code par courriel sur un nouvel appareil | `auth.html`, `auth/twofa.php` | M1 | Garder |
| Page « Bienvenue · Trois étapes et tu trades » : prénom, « Tu trades depuis combien de temps ? », choix guidé Simulation / Évaluation / Financé / Live → firme → programme → taille | `nav.js:3620`, `ux.js` §11 | M1 | **Garder** (le cœur de M1) |
| « Moins de 6 mois » → le parcours de 90 jours est proposé | `nav.js:3646` | M1 | Garder |
| « Neuf ou déjà en cours ? » (solde actuel, plus haut solde) | `nav.js:4346` | M1 | Garder |
| « Plus d'options » (où as-tu trouvé Sweep, coût, nombre de comptes, frais) | `nav.js:3856` | M1 | Garder replié |
| « Explorer avec des données d'exemple » | `nav.js:6514`, `chart.js:576` | M1 | Garder, mais **ne plus compter les trades d'exemple dans `stage()`** (voir 3) |
| Plan court « Avant ton premier trade : 30 secondes » | `game.js` (`openPlan(…, {then})`) | M1 | **Garder** : c'est là que naît le « risque permis » |
| Formulaire du premier trade | `nav.js:2199` | M1 | Garder (voir 2.3, le chemin « sans capture ») |
| Toast « Ajoute d'abord ton compte » sur « + » sans compte | `nav.js:2638` | M1 | Garder, et cacher « + » sur la page Bienvenue (déjà : `sw-onb`) |
| Tiroir « Ajoute d'abord un compte » (`#drawer`) | `app.js:9271` | M1 | **Retirer** : doublon du toast et de la page Bienvenue |
| Ancien écran `onboarding()` (puces firme / solde) | `app.js:1512` | M1 | Retirer s'il n'est plus atteignable (remplacé par la page Bienvenue) |
| « Ton vrai net » (rattrapage, 4 écrans), ouvert seul la 1ʳᵉ fois sur Mon argent | `ux.js` §29 | — | **Mission** (voir 5, semaine 2) |
| « Classe tes comptes » (fenêtre une fois) | `ux.js` §27 | — | Garder (seulement pour les anciens comptes sans type) |
| Fenêtre « Quoi de neuf » | `game.js:1665` | — | Garder (jamais le jour de l'inscription : déjà) |
| Suggestions « fais-le maintenant » : écran d'accueil, rappels, plan | `nav.js:4440` | M2 | **Fusion** dans les missions (voir 5) : une seule voix qui dit quoi faire |

### 1.3 Aujourd'hui (`#dashboard`)

| Élément | Où | Moment | Cible |
|---|---|---|---|
| En-tête « Bonjour {prénom} · date » | `nav.js:551` | M2 | Garder ; **le « Bonjour / Bonsoir » doit suivre l'heure de New York**, comme la date (voir 3) |
| Bouton bleu « Ajouter un trade » de l'en-tête (ordinateur) | `nav.js:1527` | M2 | **Gris** : le bleu revient au seul bouton de la carte « Maintenant » |
| Pastille streak et anneau du téléphone (`headDay`, toujours caché) | `nav.js:613` | — | Retirer (code qui tourne pour rien) |
| **Carte « Ta routine du jour »** Plan · Exécution · Revue, étape suivante en bleu | `nav.js:4135` | **M2** | **Devient la carte « Maintenant »** (voir 4.2) |
| Pastille Discipline → « Ton score de discipline » | `nav.js:4794` | M2 / M3 | Garder dans la carte, **une seule formule partout** (voir 2.1) |
| Streak, anneau de niveau, « ? » dans la carte | `nav.js:4146` | M3 | Garder petit (le niveau ouvre « Ma progression ») |
| « Pas de trading aujourd'hui » (lien de l'étape Plan) | `nav.js:4175` | M2 | Garder |
| « Terminer hier › » | `nav.js:4135` | M2 | Garder |
| Carte du coach (dans la routine) : règle du jour, dernier trade, leçon, « il te reste », alertes 75 / 100 %, habitude de la semaine, série de l'edge | `coach.js:648` | M2 | **Fusion** dans la carte « Maintenant » : **une phrase** selon le moment, pas un bloc |
| Carte du parcours de 90 jours (jour N, mission du jour, à rattraper) | `gameplan.js:102` | M1 / M2 | **Fusion** : devient la ligne « Mission du jour » de la carte « Maintenant » |
| Carte de fin d'essai Pro (jour 50) | `nav.js:4869` | — | Garder (rare, utile, 10 jours) |
| Carte « Jour / Semaine » (téléphone) : sélecteur de type de compte, bande des jours, P&L, trades, taux de réussite, « Annonces », 5 trades | `nav.js:457` | M2 | **Garder**, allégée : sans « Annonces » (fusion avec À surveiller) ; sélecteur de type seulement à partir de 2 types de comptes |
| Performance (ordinateur) : Jour / Semaine, « Tout voir › » | `nav.js:397` | M2 | Garder (même contenu que la carte Jour du téléphone) |
| « À surveiller » (annonces du jour, compte à rebours) | `nav.js:764` | M2 (avant) | **Fusion** dans la carte « Maintenant » avant la séance (« 10 h 00 · CPI : pas de trade de 9 h 55 à 10 h 15 ») ; la liste complète reste `#news` |
| « Ce mois-ci » (bande et grille du mois) | `nav.js:824` | — | **Page** : Trades › Calendrier (la bande des jours suffit sur Aujourd'hui) |
| « Comptes » (solde, marge, objectif, « Prêt pour le payout ») | `nav.js:691` | M2 | **Garder** dès le premier compte, **même avant le 1er trade** : la marge, c'est le risque permis |
| « Mon argent » (net réel, retirable, dépenses, en attente) | `nav.js:715` | M3 | **Mission** (semaine 2), puis visible dès un payout |
| Carte de rang (téléphone) | `nav.js:516` | — | Retirer d'Aujourd'hui (le niveau est déjà dans la carte) |
| « La tendance de la semaine » | `nav.js:853` | M3 | **Page** : Stats (et le bilan du vendredi) |
| « Données d'exemple masquées · Les retirer » | `nav.js:5808` | M1 | Garder |
| Pastille de filtre de compte « ✕ » | `nav.js:4752` | M2 | Garder |
| Carte du jeu `.g-today` (missions, intention, garde-fou, `nextAction`) — **toujours cachée** | `game.js:343`, `nav.css:1043` | — | **Retirer**, en sauvant ce qui y était seulement : l'intention de la semaine (voir 3) |
| `vDashboard` du cœur (redessiné par `nav.js`) | `app.js:1527` | — | Retirer à terme (double rendu) |

### 1.4 Ajouter un trade (M2, pendant la séance)

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Feuille « Nouveau trade · par capture » (zone de capture, « Saisir à la main », « Importer un CSV ») | `nav.js:2199` | M2 | Garder |
| Après la capture : compte, « Aussi sur », P&L net, Long/Short, setup en un toucher, risque, « Vérifier le trade », 3 questions, émotions, Enregistrer | `nav.js:2219` | M2 | Garder |
| « Ton coach · Avant ce trade » (perte max, pause après une perte, edge, leçon qui revient) | `coach.js:460` | M2 | **Garder** : c'est le « il te reste X $ » de M2 |
| « X trades trouvés » (une capture, plusieurs trades) | `nav.js:2342` | M2 | Garder |
| Formulaire manuel `#tkSlide` (prix ou montant, partiels, P&L plateforme, « Plus de détails », « Comme le dernier ») | `app.js:4407`, `nav.js` | M2 | Garder |
| Étape 2 « Comment ça s'est passé ? » | `app.js:4459` | M2 | Garder |
| Message « Trade enregistré · {phrase du coach} » | `coach.js:791` | M2 | Garder |
| « Ce trade, c'est quel scénario de ta fiche ? » (A, B, Hors fiche) | `game.js` | M2 | Garder, **seulement si la fiche guidée existe** (déjà) |
| Feuille « Importer un CSV » | `nav.js:2668` | M2 | Garder (une des 2 entrées d'import, voir 2.1) |
| Avertissement de doublon (écrit 2 fois dans le code) | `nav.js:2559`, `nav.js:5402` | M2 | Garder, **une seule fonction** (`SweepDupOf`) |
| Choix « Mois du contrat » (Options avancées) | `chart.js:432` | — | Garder replié |

### 1.5 Plan et revue (M2, avant / après)

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Plan **guidé** (pré-marché : niveaux Londres / PDH / PDL, lecture, scénarios A/B, 2R, limites, ~6 écrans, 10–15 touchers) | `game.js:1014` | M2 | **Mission** (semaine 2) : pas le plan par défaut d'un nouveau trader |
| Plan **express** (instrument, biais, niveaux en mots, scénarios en mots, perte max) | `game.js` | M2 | **Le plan par défaut** jusqu'à la mission « plan guidé » |
| Offre automatique du plan express une fois par jour après 9 h 25 | `game.js:1479` | M2 | Garder |
| Verrouillage de la fiche, vue séance (checklist dans l'ordre, Invalider, bandeau de news) | `game.js` | M2 | Garder pour qui a fait le plan guidé |
| Phrase du coach dans la feuille du plan (`paintPlan`) — **jamais atteinte** (le plan est toujours le questionnaire) | `coach.js:750` | — | Retirer, ou la ramener dans l'express (voir 3) |
| « Ce qui marche pour toi » en tête du plan, setups gagnants en tête | `coach.js` T4 | M2 | Garder |
| Revue : plan suivi (O/P/N), discipline 1–5, note A–F, règles enfreintes, note pour demain ; leçon du coach | `game.js:1557`, `coach.js:761` | M2 | **Devient « Fermer ma journée »** (voir 4.3) |
| Carrousel de journal rapide (setup, émotion, règles, par trade) | `game.js:1516` | M2 | Fusion dans « Fermer ma journée » (les trades sans réponse) |
| « Débriefer ma journée » (Sweep AI) | `app.js` (`ai-day`) | M2 | **Mission** (semaine 3) |

### 1.6 Trades, Calendrier, Journal

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Liste des trades (filtres, recherche, tri, chiffres) | `app.js:1550` | M2 | Garder |
| Page d'un trade : graphique, « Ce trade » (coach), « Réponds au coach », revue complète repliée, captures, exécutions, ⋯ (partager, copier, supprimer) | `app.js:1588`, `coach.js:699` | M2 | Garder |
| Calendrier du mois | `app.js:1713` | M2 / M3 | Garder (reçoit « Ce mois-ci ») |
| Journal du jour : récap, Pré-marché, Post-marché, graphique, « Ajouter un trade ce jour-là » | `app.js:1651`, `nav.js:1659` | M2 | Garder (même document que le plan et la revue) |
| Journal de la semaine (`#journal/weekly`) : chiffres, jours, setups, émotions, leçons, « Ta revue de la semaine » (6 questions), « Bilan IA » | `app.js:1690`, `nav.js:4005` | M3 | **Fusion** avec le bilan du vendredi (voir 2.1) |
| Page d'import `#import` (« Comment exporter », plusieurs comptes) | `app.js:2873`, `ux.js` §17-18 | M2 | Garder comme suite de la feuille d'import |
| Calendrier économique `#news` | `app.js:4528` | M2 | Garder ; seulement par « Tout le calendrier › » de la ligne news |

### 1.7 Stats

| Élément | Où | Moment | Cible |
|---|---|---|---|
| « Ce qui fonctionne pour toi » (force, fuite, règle, progression par habitude, « Ton edge ») | `coach.js:604` | M3 | **Garder en tête** |
| KPI, courbe, tuiles, durées, répartition, motifs, carte calendrier, « Analyse détaillée » (9 onglets) | `app.js:3304` | — | Garder (page de consultation ; Mateo veut tout voir) |
| Carte de rang, gels, « Voir la suite › » | `game.js:1949` | — | Fusion dans « Ma progression » |
| Lien « Patterns to watch » → `#analytics/insights` (onglet inexistant) | `app.js:1546` | — | Retirer ou corriger |

### 1.8 Comptes et Mon argent

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Liste des comptes par groupe (Live, Financés, Évaluations, Perso, Simulation), « Modifier », archivés, fermés, actions groupées | `ux.js` §26, `nav.js` | M2 | Garder |
| Page d'un compte : statut, marge (en $ et en points), objectif, payout, trades, payouts, « Réglages du compte » replié | `app.js:1766`, `nav.js:6417` | M2 | Garder |
| « Tu as réussi ! Passer en financé », passage en live, marquer échoué | `nav.js:2963`, `nav.js:4741` | M2 | Garder |
| Bandeau « {firme} a changé ses règles » | `ux.js:633` | M2 | Garder |
| Choix du type de compte (5 endroits : choix guidé, « Classe tes comptes », page du compte, bascule de phase, devinette de la synchro) | `ux.js` | — | Garder le choix guidé et la page du compte ; les 3 autres sont des cas rares |
| Mon argent : Mes entrées / Analyse, payouts, dépenses, export CSV, filtres | `ux.js` §25 | M3 | **Mission** (semaine 2) ; Free : verrouillé (règle actuelle) |
| Ancienne page Payouts (`vPayouts` du cœur, `ux.js` §5 en partie) | `app.js:1820`, `ux.js:58` | — | **Retirer** (code mort écrasé) |
| « Partager mes payouts » | `nav.js:3138` | M3 | Garder |

### 1.9 Jeu, progression, coach long terme

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Anneaux Plan / Exécution / Revue, « Journée balayée », XP, niveaux, rangs, streak, gels | `game/game.php`, `game.js` | M2 | **Garder** (les anneaux sont les 3 étapes de la boucle) |
| Célébrations (une fenêtre par séance, le reste en toasts), « {n} nouveautés · Voir Progression » | `game.js:1795` | M2 | Garder ; une célébration n'arrive jamais par-dessus « Maintenant » |
| Progression (feuille : « Ton parcours » 5 chapitres, raccourcis, « À débloquer », collection) | `game.js:3008` | — | **Devient « Ma progression »** : niveau, badges, collection, saison. Les chapitres deviennent les missions de découverte (voir 5) |
| « Ton parcours » à 5 chapitres (`GAME_MAP`, Free : 1–2) | `game/v2.php` | — | **Fusion** dans les missions de découverte |
| Liste « Démarrage » (`GAME_START_STEPS`) | `game/catalog.php` | M1 | **Fusion** dans les missions de découverte |
| Missions de la semaine (3, relance, coffre) | `game/v2.php:32` | — | **Mission** : débloquées après la découverte (semaine 3) ; renommées **« Défis de la semaine »** (le mot « mission » est réservé au parcours) |
| Boss (« Mission spéciale »), saison, ligues, crew, binôme, Wrapped, rôles Discord, thèmes d'anneaux, son | `game/*.php`, `game.js` | — | **Mission** : rien avant la semaine 3 ; ensuite dans « Ma progression » seulement. Décision par l'usage le 13 nov. (Admin › Métriques › Jeu, fonctions sous 10 %) |
| Bilan du vendredi : 1. la semaine (streak, discipline, jours balayés, meilleure habitude, point à travailler, payouts, coach, partager) ; 2. questions ; 3. Edge Reveal ; 4. coffre | `game.js:2528` | **M3** | **Garder** : c'est M3. Écran 2 reçoit la « revue de la semaine » du Journal |
| Rappels plan / revue / semaine (cloche et téléphone), courriel « Ta semaine » | `game/v2c.php`, `weekly-mail.php` | M2 / M3 | Garder |
| Coach : règle du jour, règle de demain, habitude de la semaine, alertes 75 / 100 % | `coach.js` | M2 | Garder (une phrase dans « Maintenant ») |
| Parcours de 90 jours : feuille de mission, carte des 90 jours, portes, quiz | `gameplan.js` | M1 / M2 | Garder (voir 5) |
| Partage : carte Discipline d'abord, liens, profil public | `nav.js:4850`, `growth/` | M3 | Garder ; profil public dans Réglages (déjà) |
| Guide et aide (22 articles) | `guide.js:143` | — | Garder dans l'avatar et la recherche ; corriger les articles périmés (voir 2.2) |

### 1.10 Réglages et le reste

| Élément | Où | Moment | Cible |
|---|---|---|---|
| Groupes Compte, Discipline (checklist, setups, critères), Notifications, Données (export, import, Connexions, exemple), Avancé (prop firms, copies, raccourcis) | `nav.js:932` | — | Garder |
| Sections sans groupe sous les groupes : parcours de 90 jours, forfait, Sweep AI, À propos | `nav.js:963` | — | **Ranger** : parcours → groupe « Discipline » (renommé **« Ma routine »**), forfait → Compte, Sweep AI et À propos en bas |
| Règles de risque (heure de verrouillage du plan, tampons) | `app.js:1997` | M2 | Garder dans « Ma routine » |
| Tes appareils, Face ID, double authentification | `nav.js:6287` | — | Garder (Compte) |
| Connexions NinjaTrader 8 / Quantower (feuille `#sySheet`, 5 vues) | `ux.js` §30 | M2 | Garder dans Données, **et une mission** (semaine 1) qui l'ouvre |
| Abonnement `#plan`, Parrainage, Feedback | `app.js` | — | Garder (avatar) |
| Bannière « Belle semaine · Passe à Pro » (Free seulement) | `app.js:8661` | — | Garder (jamais pendant l'essai : déjà) |
| Admin (Traders, Santé, Métriques, Erreurs, Préréglages, Synchro) | `app.js:2048`, `ux.js` §15 | — | Garder (administrateurs) |
| Restes de `#moreSheet` (éléments absents d'`app.html`) | `app.js:9948` | — | Retirer |

---

## 2. Doublons, choses introuvables, impasses

### 2.1 Doublons à résoudre (une seule version gagne)

| Doublon | Gagnant | Le perdant devient |
|---|---|---|
| **Score de discipline** : règles du coach (`discScore`, routine, bilan, courriel) contre moyenne de checklist (`tDisc` : page du trade, Journal semaine, cartes de partage de payout) | **Les règles du coach** partout | `tDisc` ne sert plus qu'à l'intérieur de la checklist d'un trade (« 3 sur 4 »), sans le mot « discipline » |
| **Le P&L du jour sur téléphone, 3 fois** (bande de la carte Jour, « Ce mois-ci », chiffres de la carte) | La carte Jour (bande + chiffres) | « Ce mois-ci » va dans Trades › Calendrier |
| **Les annonces, 2 fois** (« Annonces » de la carte Jour, « À surveiller ») | Une ligne dans « Maintenant » avant la séance | `#news` pour la liste complète |
| **Revue de la semaine, 3 noms et 2 formulaires** (« Voir mon bilan », « Bilan de la semaine », « Ta revue de la semaine » du Journal avec 6 questions) | **« Bilan de la semaine »**, écran 2 du bilan du vendredi | Le Journal semaine garde ses chiffres et un lien « Ouvrir le bilan de la semaine » |
| **« Ton parcours »** (5 chapitres du jeu) contre **« Ton parcours de 90 jours »** ; **« missions »** (jeu) contre missions du parcours | « Missions » = parcours (de découverte, ou de 90 jours) | Les chapitres sont fusionnés ; les missions du jeu deviennent « Défis de la semaine » |
| **Qui dit quoi faire ensuite** : étape suivante de la routine, coach, carte du parcours, ligne du bilan, suggestions (installation, rappels, plan), Quoi de neuf, Progression (prochaine étape, missions, boss, quête de retour), carte du jeu cachée (`nextAction`) | **La carte « Maintenant »** (étape + mission du jour) | Les suggestions deviennent des missions ; Progression ne propose plus d'étape |
| **Ajouter un trade, 7 entrées** (+ du bas, bouton de l'en-tête sur ordinateur, « + Trade » de la routine, ligne de Trades, Journal du jour, recherche, N) | Garder les entrées, mais **une seule bleue** à la fois | Bouton de l'en-tête en gris ; « + » du téléphone caché et jamais vu : retiré du code |
| **Import CSV, 4 entrées** (bouton de Trades, feuille capture, formulaire manuel, `#import`) | La feuille « + » et le bouton de Trades | `#import` = la suite (plusieurs comptes) ; retiré du formulaire manuel |
| **Ajouter un compte, 3 formulaires** (page Bienvenue, page Comptes, tiroir) | Le choix guidé (Bienvenue et Comptes) | Tiroir retiré |
| **Vérification de doublon écrite 2 fois** | `SweepDupOf` | La copie du formulaire manuel l'appelle |
| **Pages Payouts mortes** (`vPayouts` du cœur, `ux.js` §5) | `ux.js` §25 | Retirées |
| **Abonnement 2 fois dans l'avatar** | La ligne d'en-tête (prénom · forfait) | L'entrée « Abonnement » retirée |
| **Streak, niveau, rang en 4 endroits** (routine, anneau Lv, carte de rang, pastille cachée) | La routine (streak + niveau) | Carte de rang et pastille retirées d'Aujourd'hui |
| **La règle, en 5 endroits** (règle de demain de la revue, règle du coach, question « règle » du bilan, règle de la semaine du coach, règles du parcours) | Règle **du jour** (revue → plan suivant) et règle **de la semaine** (bilan du vendredi), rien d'autre | La règle de la semaine du coach pré-remplit la question du bilan |

### 2.2 Difficile à trouver (et pourtant utile)

- **Saisir un P&L sans capture** : « + » → « Saisir à la main » → « J'ai le P&L de ma plateforme ». La feuille capture n'a pas de champ P&L avant une image. → Dans la feuille « + », sous la zone de capture, une ligne **« Pas de capture ? Entre ton P&L »** qui ouvre la saisie rapide sans image (même champs : compte, P&L net, Long/Short).
- **Le calendrier économique** (`#news`) : aucun menu. → « Tout le calendrier › » sur la ligne news de « Maintenant ».
- **Connexions** (synchro NinjaTrader 8 / Quantower) : dans un groupe replié de Réglages. → Mission de la semaine 1.
- **Les badges, la saison, la ligue, la crew, le Wrapped** : seulement par Progression. → Voulu jusqu'à la semaine 3 (voir 5).
- **Le guide** : avatar ou recherche. Ses articles « Bien démarrer » (checklist sur Aujourd'hui) et « XP » (badges dans Réglages) sont **périmés**.
- **Les dépenses mensuelles, les remboursements** (montant négatif), le fuseau d'un fichier TradingView, « Voir toutes les règles » : bien rangés pour un expert, rien à changer.
- **Recalibrer un compte, la commission** : dans « Réglages du compte », replié. Voulu.

### 2.3 Où un nouveau trader ne sait pas quoi faire ensuite

| Moment | Ce qu'il voit | Le problème |
|---|---|---|
| M1, après « Créer le compte » | Le plan court, puis la feuille de trade | **Sans capture sous la main**, la feuille montre une zone vide : il doit trouver « Saisir à la main ». |
| M1, sur téléphone, avant le 1er trade | La routine (et la carte du parcours de 90 jours pour un débutant) | Les annonces et la marge de son compte, utiles **avant** de trader, sont cachées jusqu'au 1er trade. |
| M1, après les données d'exemple | Aujourd'hui complet | Tout disparaît au 1er vrai trade (`stage()` compte les trades d'exemple). |
| M2, ordinateur | 2 ou 3 boutons bleus (en-tête, étape suivante, « Voir les forfaits ») | L'étape suivante perd son sens. |
| M2, le plan | 6 écrans de pré-marché (London high / low, PDH / PDL, 2R) | Trop pour un débutant le jour 2 : il saute le plan, donc l'anneau Plan et le « risque permis ». |
| M2, fin de séance à 11 h | « Exécution » reste en bleu jusqu'à 16 h (ou la dernière annonce) | Rien ne lui dit de fermer sa journée. |
| M2, la revue | 3 questions obligatoires + règles + note | Pas « un toucher ». Rien ne dit « journée fermée ». |
| M2, le soir | « Bonsoir » à l'heure de l'appareil au-dessus de la date de demain (New York) | Confusion sur la journée concernée. |
| M3 | « Ta semaine est prête » arrive bien | L'**intention de la semaine** écrite dans le bilan n'est jamais réaffichée (elle vivait dans la carte cachée du jeu). |
| Partout | Missions, défis, parcours, chapitres, boss, quête de retour | Trop de voix et de mots pour la même idée. |

---

## 3. Défauts trouvés pendant l'inventaire (qui cassent le parcours)

À corriger dans le premier lot (ce ne sont pas de nouvelles fonctions).

| # | Défaut | Cause (code) | Certitude |
|---|---|---|---|
| ~~D1~~ | ~~Carte du parcours de 90 jours cachée sur téléphone~~ — **faux, vérifié à l'écran le 21 oct.** (étape 0) : à 390 px, la carte est visible en tête d'Aujourd'hui (`nav.js` la sort de `.d-today`) | — | Retiré |
| D2 | **Corrigé (étape 1, 21 oct.)** — missions « Zéro écart » (23–25, 46, 74, 81, 88) jamais cochées sur une journée propre | `game/gameplan.php` exigeait l'XP `guardrail:` (perte max atteinte puis respectée) ; maintenant : plan valide (pas un jour de repos), revue faite, chaque trade dans le plan | Vérifié (test) |
| D3 | **Corrigé (étape 1)** — une porte de fin de mois se passait sans cocher ses critères | « Passer au mois N » grisé tant que chaque critère n'est pas coché ; « Refaire les semaines 3 et 4 » toujours possible (`gameplan.js`) | Vérifié (test) |
| ~~D4~~ | ~~Un déblocage n'ouvre jamais sa fiche~~ — **pas un défaut** : le toast est voulu (une seule fenêtre par séance, `isMajor`), la branche de la fiche est restée morte ; l'ouvrir ajouterait une interruption. Les déblocages deviennent des missions à l'étape 5 | — | Retiré |
| D5 | **Corrigé (étape 1)** — l'intention de la semaine n'était jamais affichée | Une ligne « Ton intention cette semaine · … » dans la carte de la routine, toute la semaine (sauf quand le bilan est prêt) | Vérifié (test, captures) |
| D6 | La phrase du coach dans la feuille du plan n'apparaît jamais | `coach.js:750` s'arrête si `g-pm` ; le plan est toujours le questionnaire (`game.js:466`) | Rapport d'inventaire |
| D7 | Deux calculs sous le même mot « discipline » | **D7a corrigé (étape 1)** : sur la page d'un trade, la tuile s'appelle « Checklist » et sa fenêtre explique ce chiffre-là (avant : le texte du score sur 30 jours). **D7b → étape 6** : les autres libellés « Discipline » qui montrent la moyenne de checklist (chiffres du jour, Journal, cartes de partage jour / semaine / trade, tableaux de Stats : `stats().disc`, `dayMap`) | D7a vérifié |
| ~~D8~~ | ~~`stage()` compte les trades d'exemple~~ — **pas un défaut** : voulu, « Explorer avec des données d'exemple » montre Aujourd'hui complet | — | Retiré |
| ~~D9~~ | ~~« Bonjour / Bonsoir » à l'heure de l'appareil~~ — **pas un défaut** : saluer à l'heure du trader est juste (Paris à 15 h : « Bon après-midi ») ; la date suit la séance de New York, voulu | — | Retiré |
| D10 | Badges : la branche « Réglages » de `paintSections` ne s'exécute jamais | `game.js:1991` | Laissé : « Ma progression » (étape 6) range les badges |
| D11 | Code mort | **Retiré (étape 1)** : `sessionDay()` (règle de 16 h, jamais appelée). **Gardés** : `headDay()` (invisible, mais une règle CSS `:has(.nav-hday)` en tire la marge du titre sur téléphone), `#moreSheet` (appels déjà protégés), `vPayouts` du cœur et `ux.js` §5 (enveloppés par `ux.js`), le lien `insights` (Aujourd'hui est redessiné par `nav.js`) : risque sans gain pour le parcours | — |

---

## 4. La carte cible de l'app

### 4.1 Navigation (inchangée dans sa forme)

- **Téléphone** : Aujourd'hui · Trades · **+** · Stats · Comptes.
- **Ordinateur** : Nouveau trade (gris) · Aujourd'hui · Trades · Stats · Comptes · recherche · cloche · avatar. Progression quitte le menu.
- **Avatar** : (prénom · forfait → Abonnement) · Ma progression · Quoi de neuf · Réglages · Parrainage · Donner mon avis · Aide · (Traders) · Déconnexion.
- **Sous-onglets** : Trades = Liste · Calendrier · Journal ; Comptes = Comptes · Mon argent (Mon argent visible dès sa mission ou un payout).

### 4.2 Aujourd'hui = « Maintenant », puis le reste

**En tête, une seule carte : « Maintenant »** (la routine actuelle, refaite par évolution : mêmes 3 étapes, même anneaux). Elle a 3 lignes au plus : ce qu'il faut faire, le chiffre qui compte, la mission du jour. Elle a **un seul bouton bleu**.

| État (heure de New York) | Phrase et chiffre | Bouton bleu | Ligne mission |
|---|---|---|---|
| **Avant la séance**, plan pas fait (18 h la veille → 9 h 30) | « Ton risque permis aujourd'hui : **450 $** » (le plus petit de la perte max du dernier plan, de la limite du jour et de la marge de drawdown des comptes actifs, déjà calculés par le coach) ; annonce à fort impact : « 10 h 00 · CPI : pas de trade de 9 h 55 à 10 h 15 » | **Faire mon plan** (express par défaut) | Mission du jour |
| Avant la séance, plan fait | « Plan prêt · perte max 450 $ · 2 trades max » + règle du jour | — (« + » suffit) | Mission du jour |
| **Pendant la séance** | « Il te reste **300 $** · trade 1 sur 2 » ; la phrase du coach du moment (pause, arrêt, edge) | **Ajouter un trade** | Mission du jour |
| Signal d'arrêt (perte max, marge sous 25 %, trades prévus faits) | « Journée terminée selon ton plan. » | **Fermer ma journée** | — |
| **Après la séance** : dès 16 h, ou dès que le trader le décide (lien « J'ai fini pour aujourd'hui » sous l'étape Exécution dès un trade) | « 2 trades · +180 $ · 1 hors plan » | **Fermer ma journée** | — |
| Journée fermée | « Journée balayée » ou « Journée fermée » + leçon + « Règle de demain » | — | Prochaine mission (demain) |
| Jour sans trade choisi (« Pas de trading aujourd'hui ») | « Journée de repos · comptée dans ta série » | — | — |
| **Vendredi**, bilan prêt (M3) | « Ta semaine est prête » | **Voir mon bilan** | — |
| Fin de semaine | L'intention de la semaine (enfin visible) + « Lundi : prépare ton plan dès dimanche 18 h » | — | — |

**Sous « Maintenant »**, dans cet ordre, rien d'autre :
1. **Comptes** (dès le premier compte, même sans trade) : marge ou objectif de chaque compte, « Prêt pour le payout ».
2. **Jour / Semaine** (dès le 1er vrai trade) : bande des jours, P&L, trades, taux de réussite, les trades du jour.
3. **Mon argent** (dès sa mission faite ou un premier payout).
4. **Fin de l'essai Pro** (jour 50 seulement).

**Ce qui quitte Aujourd'hui** : « Ce mois-ci » (→ Trades › Calendrier), « À surveiller » (→ une ligne dans « Maintenant » + `#news`), « La tendance de la semaine » (→ Stats, bilan), la carte de rang, la carte du jeu cachée, le parcours en carte séparée (→ ligne mission), les suggestions en fenêtre (→ missions).

**Ordinateur** : même contenu, en 2 colonnes : « Maintenant » et Jour / Semaine à gauche, Comptes et Mon argent à droite. Le bouton « Ajouter un trade » de l'en-tête est gris.

### 4.3 « Fermer ma journée » en un toucher (évolution de la revue)

C'est la revue actuelle (`openReview`), **pré-remplie** par ce que Sweep sait déjà :
- **« As-tu suivi ton plan ? »** ← la conformité du jour (anneau Exécution, `compliant_count`, fiche) : Oui / En partie / Non.
- **« Discipline »** ← le score du coach du jour (trades sans erreur / trades), ramené sur 1–5.
- **« Note du jour »** ← proposée d'après les deux, modifiable.
- **« Règles enfreintes »** ← déjà pré-cochées (hors fiche, trop de trades).
- **« Une chose pour demain »** ← la règle proposée par le coach, en indication.

Un seul bouton **« Fermer ma journée »** enregistre tout (mêmes champs `post.*`, même serveur, même XP). Chaque réponse se change d'un toucher avant. Les trades sans réponse à la checklist sont proposés en dessous, en option (le carrousel de journal rapide). Ensuite : la célébration « Journée balayée » ou « Journée fermée », la leçon et la règle de demain sur « Maintenant ».

Ce qui ne change pas : la revue reste possible plus tard le soir (jusqu'au verrouillage de la journée), et « Terminer hier › ».

### 4.4 « Ma progression » (l'ancienne Progression)

Une feuille ouverte par l'anneau de niveau de « Maintenant » et par l'avatar. Elle contient : niveau et rang, streak et gels, badges, collection, thèmes d'anneaux, son. À partir de la semaine 3 s'y ajoutent : défis de la semaine, boss, saison, ligue, crew, binôme, Wrapped.

Elle **ne propose plus d'étape** : les chapitres « Ton parcours » et « Démarrage » sont fusionnés dans les missions (section 5).

### 4.5 Ce qui va dans Réglages (groupes)

| Groupe | Contenu |
|---|---|
| **Compte** | Profil, courriel, mot de passe, tes appareils, Face ID, forfait, profil public, supprimer |
| **Ma routine** (ancien « Discipline ») | Parcours de 90 jours, plan guidé ou express (`pm_mode`), heure de verrouillage, règles de risque, checklist, setups et critères |
| **Notifications** | Catégories, rappels sur le téléphone et leurs heures |
| **Données** | Connexions (NinjaTrader 8, Quantower), export ZIP / JSON, import JSON, données d'exemple |
| **Avancé** | Prop firms, trades copiés, raccourcis clavier |
| (bas de page) | Apparence (thème, langue), Sweep AI, À propos, Déconnexion |

### 4.6 Les fusions, en une liste

1. Routine + coach d'Aujourd'hui + carte du parcours + ligne du bilan + À surveiller → **« Maintenant »**.
2. Revue + carrousel de journal rapide → **« Fermer ma journée »**.
3. Revue de la semaine du Journal → **écran 2 du bilan du vendredi**.
4. Chapitres « Ton parcours » + « Démarrage » + suggestions (installation, rappels, plan) → **missions de découverte**.
5. Progression + carte de rang + collection → **« Ma progression »**.
6. Missions de la semaine du jeu → **« Défis de la semaine »** (dans « Ma progression »).
7. Deux formules de discipline → **une** (règles du coach).
8. Trois formulaires d'ajout de compte → **le choix guidé** (deux endroits, même code).

---

## 5. L'ordre de découverte : les missions

### 5.1 Une seule carte de mission, deux sources

- **Tout trader** (Free compris) suit les **missions de découverte** : 15 missions sur ~3 semaines. Elles réutilisent le moteur existant : chapitres `GAME_MAP` et `GAME_START_STEPS`, XP par `awardXp` avec une clé unique, célébrations. Elles remplacent les chapitres actuels.
- **Un trader du parcours de 90 jours** (moins de 6 mois, Pro / Elite) voit **la mission du jour du parcours**. Les missions de découverte qu'il n'a pas encore faites sont cochées par le parcours quand une mission du parcours fait faire la même chose. Elles apparaissent sinon dans la feuille de mission, sous « Découvre aussi ».
- **Chaque mission a un bouton « Faire maintenant »** qui ouvre la fonction (aujourd'hui, aucune mission du parcours n'ouvre quoi que ce soit). Elle se coche seule quand Sweep peut le mesurer.
- **Une mission par jour de trading au plus.** Une mission en retard reste faisable, sans pénalité, comme le parcours.
- **Une mission se coche par un comportement, jamais en ouvrant une page.** La discipline se construit en pratiquant : chaque mission demande une action du trader (enregistrer, fermer, respecter, répondre), mesurée par Sweep. « Faire maintenant » ouvre la bonne page, mais l'ouvrir ne coche rien.
- **Une fonction non encore découverte n'est pas montrée.** Exceptions par le contexte : copy trading au 2ᵉ compte, Mon argent au 1er payout, plan guidé si le trader le choisit dans Réglages.
- **Les comptes existants ne perdent rien.** Tout compte qui existe au moment où les missions sont mises en ligne est traité comme ayant fait **toutes** les missions de découverte : il garde tout ce qu'il voit aujourd'hui (Sweep AI, Mon argent, plan guidé, « Ma progression » complète). Seuls les traders inscrits **après** cette mise en ligne suivent les missions. La marque est posée une fois par le serveur (ex. `users.created_at` avant la date de mise en ligne), jamais retirée.

### 5.2 L'ordre

| # | Quand | Mission | Fonction découverte | Bouton « Faire maintenant » | Cochée seule par |
|---|---|---|---|---|---|
| 1 | Jour 1 (M1) | Ajoute ton compte | Choix guidé, règles de la firme | (fait à l'inscription) | compte créé |
| 2 | Jour 1 (M1) | Ton risque permis | Plan express, perte max | Faire mon plan | plan enregistré |
| 3 | Jour 1 (M1) | Ton premier trade | Feuille « + » (capture ou P&L) | Ajouter un trade | 1er vrai trade |
| 4 | Jour 1 (M2) | Ferme ta journée | « Fermer ma journée » | Fermer ma journée | revue faite |
| 5 | Jour 2 | Un trade dans ton plan | « Avant ce trade », « il te reste » | Ajouter un trade | un trade enregistré **dans le plan du jour** (sens du biais, sous la perte max et le nombre max : la règle « dans ton plan » du serveur) |
| 6 | Jour 2 | Ton setup en un toucher | Setups, checklist adaptée | Ajouter un trade | trade avec setup |
| 7 | Jour 3 | Réponds au coach | Page du trade, « Réponds au coach » | Ouvrir mon dernier trade | leçon du trade écrite (`review.lesson`) |
| 8 | Jour 3 | Tes trades arrivent seuls | Connexions (NinjaTrader 8, Quantower) ou import CSV | Connecter ma plateforme | clé active ou import fait |
| 9 | Jour 4 | Reste dans ta marge | Page du compte (marge en $ et en points, objectif, « Prêt pour le payout »), risque permis | Ouvrir mon compte | une **journée fermée** dont la perte du jour n'a pas dépassé le risque permis du matin (perte max du plan, limite du jour et marge de drawdown) |
| 10 | Jour 4 (téléphone) | Sweep sur ton écran d'accueil, rappels | Installation, notifications | Installer / Activer | fait sur l'appareil |
| 11 | 1er vendredi (M3) | Ton bilan de la semaine | Bilan du vendredi, règle de la semaine | Voir mon bilan | bilan enregistré |
| 12 | Semaine 2 | Ton vrai net | Mon argent, rattrapage, payouts, dépenses | Calculer mon vrai net | rattrapage fait ou 1er payout (Free : aperçu verrouillé) |
| 13 | Semaine 2 | Trade ton edge | Stats, « Ce qui fonctionne pour toi », « Ton edge » | Voir ce qui marche pour moi | un trade enregistré **dans ton edge** (la ligne bleue « Dans ton edge » d'« Avant ce trade ») et dans ton plan ; sans edge encore (moins de 5 trades dans une même situation), un plan qui reprend la règle proposée par Stats |
| 14 | Semaine 2 | Le plan guidé | Pré-marché (niveaux, scénarios, 2R, verrouillage, vue séance) | Essayer le plan guidé | fiche guidée enregistrée |
| 15 | Semaine 3 | Trois journées de suite | « Ma progression » : streak, badges, défis, saison, ligue | Fermer ma journée | **3 journées fermées de suite** (jours de trading ; une journée de repos compte, comme le streak) ; la célébration ouvre « Ma progression » |
| — | Semaine 3+ | (quand utile) Sweep AI : débrief, avis sur un trade | Sweep AI | Débriefer ma journée | 1ʳᵉ utilisation |
| — | Au 2ᵉ compte | (contexte) Copie sur tes comptes | « Aussi sur », groupes de copies | Ouvrir mon dernier trade | 1ʳᵉ copie |
| — | Semaine 3+ | (quand utile) Partage ta discipline | Carte Discipline, profil public | Partager ma semaine | 1er partage |

**Ce qui n'apparaît pas avant sa mission** : Sweep AI (bouton flottant et menu), Mon argent (onglet et carte), le plan guidé, « Ma progression » au-delà du niveau et du streak, les défis, le boss, la saison, la ligue, la crew, le Wrapped.

**Un trader expérimenté** (« Plus d'un an ») fait les mêmes missions, mais elles sont groupées par 2 (le jour 1 couvre 1–4, le jour 2 couvre 5–8…). Un « Tout montrer » dans Réglages › Ma routine les coche toutes et affiche tout.

---

## 6. Règles pour tout développement suivant

Avant de coder, chaque demande répond à ces questions, dans le brief ou le commit :

1. **Quel moment sert-elle ?** M1, M2 (avant / pendant / après) ou M3. Si aucun : Réglages, sa page, ou non.
2. **Comment le trader la découvre-t-il ?** Par quelle mission ou quel contexte. Jamais en plus sur Aujourd'hui au jour 1. Sa mission se coche par un comportement du trader, jamais en ouvrant une page.
3. **Les comptes existants ne perdent rien** : ce qu'un trader voit déjà reste visible pour lui.
4. **Un seul bouton bleu** par écran, et sur Aujourd'hui celui de « Maintenant ».
5. **Aucune nouvelle carte sur Aujourd'hui.** On améliore une phrase de « Maintenant » ou une des 3 cartes du dessous.
6. **Un seul mot par idée** : « Mission » (parcours), « Défi » (jeu), « Bilan de la semaine » (vendredi), « Fermer ma journée » (revue), « Risque permis », « Discipline » (règles du coach). Chaque terme de trading s'explique là où il s'affiche.
7. **Une seule formule** par chiffre affiché à deux endroits (discipline, copies, marge).
8. **Le jour, c'est New York** (18 h → lendemain), y compris le « Bonjour ».
9. **Tests** : 390 × 844 tactile et 1300 × 850, FR / EN / ES, clair / foncé ; un test e2e qui vérifie qu'un élément est **visible** (`is_visible`), pas seulement présent dans le texte.
10. **Mettre ce fichier à jour** dans le même commit quand la carte change.

---

## 7. Mise en œuvre : étapes, une à la fois

**Règles de chaque étape**
- **Deux sessions, deux rôles** (décision de Mateo, 27 oct. ; remplace la règle « une seule session sur l'app » du 21 oct.) :
  - la **session stratégie et tests** (celle qui a écrit ce fichier) : `SWEEP.md`, les briefs de chaque étape, les mesures (`docs/parcours/`), la revue des tests et de la CI, la vérification que chaque étape tient ses critères « Fini quand ». Elle ne modifie pas le code de l'app ;
  - la **session d'exécution** : le code de l'app (`app/`), ses tests, la suite complète, le push et la CI verte, puis le déploiement avec l'accord de Mateo.
  - Une seule suite complète à la fois sur le Mac : la session d'exécution utilise `/tmp/g*` (ports 8095 à 8498) ; la session stratégie et tests, si elle lance la suite, `SWEEP_PAR_SLOT=b` (`/tmp/gb_*`, ports 9195, 9295…).
- Elle part d'`origin/main` à jour, dans sa propre branche, une étape à la fois, jamais deux en même temps.
- Tests ciblés pendant le travail, puis la suite complète (`python3 tools/par.py 3`), et des captures à 390 × 844 tactile et 1300 × 850, en FR / EN / ES, clair et foncé.
- Une suite complète à la fois sur la machine : les copies `/tmp/g*` et les ports 8095 à 8395 sont partagés entre les conversations.
- `CONTEXTE-APP.md` est mis à jour dans le même commit (règles et Passation), et ce fichier aussi si la carte change.
- **Aucun déploiement sans l'accord explicite de Mateo**, donné dans la conversation qui déploie.
- Les mesures de l'étape 0 sont refaites à la fin (`tools/parcours-baseline.py`, puis Admin › Métriques une fois en ligne) et ajoutées à `docs/parcours/MESURE-<n>.md`.
- Une étape est finie quand ses critères « Fini quand » sont vrais et que la suite complète passe.

### Étape 0 — Mesurer avant de toucher · **faite (21 oct.)**, pas déployée

**Livré** (branche locale `parcours-0-mesure`, commit `600f135`, non poussé) :
- **Admin › Métriques**, deux indicateurs : « Journées fermées » (séances avec trades des 30 derniers jours dont la revue est faite) et « Bilans de la semaine ouverts » (les 8 dernières semaines terminées avec au moins un trade, bilan ouvert).
- `app/tools/parcours-baseline.py` : M1 en vrais touchers.
- `docs/parcours/MESURE-0.md` : le point de départ.

**Point de départ en local** (Topstep 50K, téléphone FR et ordinateur EN, mêmes chiffres) :

| Jusqu'à | Touchers | Champs | Écrans | Temps estimé |
|---|---|---|---|---|
| Risque permis vu (plan enregistré) | 11 | 3 | 3 | ~42 s |
| Premier trade, sans capture | 16 | 5 | 5 | ~65 s |
| Premier trade, avec capture | 16 | 4 | 5 | ~60 s |

**Reste à faire, hors de cette conversation** : pousser `600f135` et déployer avec l'accord de Mateo, puis relever dans Admin › Métriques le temps de M1 (« Le démarrage »), les journées fermées et les bilans ouverts. Les noter dans `MESURE-0.md` avec la date. Sans ce relevé, les étapes suivantes se comparent seulement aux chiffres locaux.

### Étape 1 — Les défauts qui cassent le parcours · **faite en local (21 oct.)**, déployable dès l'accord

**Fait** (branche locale `parcours-1-defauts`, partie de l'étape 0) : D2, D3, D5, D7a et D11 en partie (`sessionDay()` retiré). Le détail est dans la section 3.

**Barrés après vérification** : D1, D4, D8 et D9 (pas des défauts). D7b passe à l'étape 6 et D10 à « Ma progression » (étape 6).

**Tests** :
- `gameplan_test.php` (2c : « Zéro écart », il échoue sur l'ancien code) ;
- `e2e_gameplan` (la porte) ;
- `e2e_parcours_defauts` (nouveau : D5 et D7a, à 390 FR et 1300 EN) ;
- la suite complète.

**Outil** : `tools/par.py` accepte `SWEEP_PAR_SLOT=b`. La suite tourne alors sur ses propres copies et ports (`/tmp/gb_*`, ports 9195, 9295…), sans gêner celle d'une autre conversation sur le même Mac (deux collisions le 21 oct.).

**M1 inchangé** (rien de ce lot ne touche à l'arrivée) : 11 touchers jusqu'au risque permis, 16 jusqu'au premier trade.

### Étape 2 — La saisie sans capture et le plan express par défaut

**But** : M1 sans obstacle, que le trader ait une capture ou pas.

**Saisie sans capture** : dans la feuille « + » (`shotForm`, `nav.js:2199`), sous la zone de capture, une ligne « Pas de capture ? Entre ton P&L ».
- Elle ouvre la même feuille, sans image : compte, P&L net, Long / Short, setup en un toucher, « Vérifier le trade », questions, émotions, Enregistrer.
- Mêmes règles que la saisie rapide d'aujourd'hui : sens obligatoire, heure de New York, doublons.
- « Saisir à la main » reste pour le formulaire complet avec les prix.

**Plan express par défaut** : un trader sans fiche guidée enregistrée ouvre « Faire mon plan » sur la version express (`settings.pm_mode` absent → `express`). Le plan guidé reste à un toucher (« Plan guidé ») et devient la mission 14. Un trader qui a déjà choisi garde son choix. Le plan court du tout premier trade ne change pas.

**Tests** : `e2e_trade_form`, `e2e_first_run` (nouveau cas sans capture), `e2e_premarket_mode`, `e2e_premarket_express`.

**Fini quand** : avec `parcours-baseline.py` (en ajoutant le cas « sans capture » par la nouvelle ligne), le premier trade sans capture se fait en **4 écrans au plus et 14 touchers au plus** (16 au départ), sans champ de prix.

### Étape 3 — « Maintenant »

**Relais vers la session d'exécution (27 oct.)**

- **Ce qui existe** : la branche locale `parcours-3b`, sur `ade074b`, avec 3 commits, ni poussés ni déployés :
  - `14176c9` : l'étape 2, rebasée ;
  - `fcf50b8` : le lot a, le bandeau « Maintenant » en tête de la routine. Il montre le risque permis et sa source avant le premier trade, plus la prochaine annonce à fort impact avec sa fenêtre sans trade. Pendant la séance, il montre ce qu'il reste et « trade n sur m ». Au signal d'arrêt, il affiche « Journée terminée selon ton plan ». Un seul calcul, `SweepCoach.riskNow`, le même chiffre que « Avant ce trade ». La carte du coach ne répète plus la ligne de séance ;
  - `5f55cb8` : le lot b, la page Aujourd'hui allégée. Comptes est visible dès le premier compte. « Ce mois-ci », « À surveiller », les annonces de la carte Jour, la tendance et le rang sont retirés. Le sélecteur de type n'apparaît qu'à partir de 2 types de comptes ou d'un filtre actif. Sur téléphone, l'ordre est : la routine (avec Maintenant), Comptes, Jour/Semaine, Mon argent. Test nouveau : `e2e_now`.
- **À faire d'abord** : rebaser `parcours-3b` sur le `main` actuel. Il contient `0526a3a` (le rééquilibrage des colonnes d'Aujourd'hui) et `03e5abb`. Recompiler `app.html` et les assets à chaque commit.
- **Un vrai défaut à corriger** (`e2e_first_run`) : sur téléphone, avec l'étape 3, la fenêtre « Ajoute Sweep à ton écran d'accueil » ne s'ouvre plus le 2ᵉ jour, après un trade. Avec l'étape 2 seule, elle s'ouvre.
  - Ce qui est établi : dans `suggest()` (`src/nav.js`, section 7), `phone()` devient faux pendant le test, parce que `matchMedia('(pointer: coarse)')` passe de vrai à faux après le premier appel.
  - Une sonde courte, sans les clics du test, garde `pointer: coarse` à vrai.
  - Il reste à comparer, avec le même marquage, l'étape 2 seule et l'étape 3. Les clics souris de `e2e_first_run` (`click()` au lieu de `tap()`) sont une piste.
  - Note : « Quoi de neuf » prend aussi la fenêtre automatique de la séance le 2ᵉ jour. Le test doit marquer les nouveautés comme vues (`settings.news_seen` = tous les ids de `SweepNews.list`) avant de tester l'installation.
- **Tests à mettre à jour pour la nouvelle page Aujourd'hui** :
  - `e2e_first_run` : après inscription, les cartes sont `['today', 'acc']` ; après le 1er trade, `today`, `perf`, `acc`, sans `cal` ni `news` ; à partir du 5ᵉ trade, `pay`, sans `rank`.
  - `e2e_session_news_ui` et `e2e_lot_a` 1.2 et 1.3 : la carte « À surveiller » n'est plus sur Aujourd'hui. On vérifie maintenant la ligne d'annonce de « Maintenant » (avant le 1er trade) et la page `#news` (onglet Semaine, Réel · Prév. · Préc.).
  - `e2e_copy_once` : la carte du mois a quitté Aujourd'hui. Les chiffres d'une copie comptée une fois se vérifient sur Trades › Calendrier.
  - Sous la charge de la suite (machine en veille la nuit), d'autres échecs ont été des délais dépassés. Chacun repasse seul.
- **Ajouté le 27 oct.** (tour de l'app) : avant le premier trade, la routine ne montre ni « Discipline — », ni la série « 0 », ni le niveau : ces chiffres apparaissent avec le premier trade.
- **Encore à faire dans l'étape 3** :
  - la ligne mission dans « Maintenant », avec « Voir les 90 jours › » ; la carte du parcours devient cette ligne ;
  - puis la suite complète à 0 échec, la CI verte, et la mise à jour de `CONTEXTE-APP.md` (règles d'Aujourd'hui) et de cette section.


**But** : Aujourd'hui dit quoi faire maintenant (section 4.2).

**La carte de la routine** (`card()`, `nav.js:4135`) devient « Maintenant » : mêmes 3 étapes et mêmes anneaux, avec les états de 4.2 (avant, pendant, signal d'arrêt, après, fermée, repos, vendredi, fin de semaine).

**Le risque permis**
- C'est le plus petit de trois montants : perte max du plan du jour (ou du dernier plan), limite du jour la plus stricte des comptes actifs, marge de drawdown.
- Il est calculé par une seule fonction, réutilisée par le coach (`coach.js`, `limits()` et `beforeHtml`).
- Il est affiché avant la séance et dans « il te reste » pendant la séance.

**Les lignes de la carte**
- Ligne news : la prochaine annonce à fort impact du jour et sa fenêtre de non-trade, avant 9 h 30.
- Ligne mission : la mission du jour du parcours de 90 jours, si le trader l'a démarré. À l'étape 5, elle prend aussi la mission de découverte.
- La carte du coach se réduit à une phrase dans « Maintenant ».
- La carte du parcours (`gameplan.js`) devient la ligne mission ; « Voir les 90 jours › » reste.

**Ce qui quitte Aujourd'hui** :
- « Ce mois-ci » va dans Trades › Calendrier (rien à ajouter là-bas, la grille y est déjà) ;
- « À surveiller » et « Annonces » de la carte Jour sont remplacés par la ligne news ;
- « La tendance de la semaine » va dans Stats ;
- la carte de rang et la carte du jeu cachée sont retirées.

**Ce qui reste ou change**
- La carte Comptes est visible dès le premier compte.
- Le sélecteur de type de compte n'apparaît qu'à partir de 2 types de comptes.
- Le bouton « Ajouter un trade » de l'en-tête (ordinateur) passe au gris : un seul bleu, celui de « Maintenant ».

**Tests**
- Nouveau : `e2e_now`. Il pose les horloges du serveur et du navigateur sur chaque état (8 h, 10 h 30, signal d'arrêt, 16 h 30, journée fermée, jour de repos, vendredi 17 h, samedi). Il vérifie la phrase, le chiffre, le seul bouton bleu (`is_visible`), à 390 et 1300, en FR / EN / ES.
- À mettre à jour : `e2e_first_run` (les cartes par stade), `e2e_routine_parity`, `e2e_lot_a`, `e2e_page_shift`, `e2e_no_jumps`.

**Fini quand**
- Aujourd'hui a « Maintenant » et 3 cartes au plus dessous.
- Il y a un seul bouton bleu par état, aux deux tailles.
- Le risque permis est le même chiffre dans « Maintenant », dans « Avant ce trade » et dans le message « Trade enregistré ».

### Étape 4 — « Fermer ma journée »

**But** : fermer la journée en un toucher (section 4.3).

**La revue** (`openReview`, `game.js:1557`) s'ouvre pré-remplie :
- le plan suivi, d'après la conformité du jour ;
- la discipline sur 1 à 5, d'après le score du coach du jour ;
- la note du jour proposée ;
- les règles enfreintes, déjà pré-cochées aujourd'hui ;
- la règle du coach en indication.

Un bouton « Fermer ma journée » enregistre les mêmes champs (`post.*`) et donne la même XP. Les trades sans réponse à la checklist sont proposés dessous, en option.

**Le lien « J'ai fini pour aujourd'hui »** sous l'étape Exécution, dès un trade, rend « Fermer ma journée » bleu tout de suite (`reviewTime`, `nav.js:4127`). Le signal d'arrêt du coach fait de même.

**Après** : la célébration « Journée balayée », ou « Journée fermée » si les 3 anneaux ne sont pas fermés. Puis la leçon et la règle de demain sur « Maintenant ».

**Rien ne change** : la revue détaillée reste possible (toucher une réponse la modifie), ainsi que « Terminer hier » et la revue du soir jusqu'au verrouillage de la journée.

**Tests** : `e2e_close_day` (nouveau : 1 toucher de la carte à la journée fermée, réponses pré-remplies justes sur 3 journées types : propre, tilt, sans plan) ; `e2e_routine_parity`, `e2e_coach`, `e2e_premarket_post`.

**Fini quand** : une journée se ferme en **1 toucher** depuis « Maintenant » (la feuille ouverte compte pour 1, la confirmation pour 1 : 2 touchers en tout au plus). En ligne, la part des journées fermées se compare à celle de l'étape 0 après deux semaines.

### Étape 5 — Les missions de découverte

**But** : chaque mission fait découvrir une fonction en la pratiquant (section 5).

**Le contenu** : les 15 missions de 5.2 et leurs 3 missions de contexte, en EN / FR / ES. Pour chacune : titre, phrase « pourquoi », bouton « Faire maintenant » (la page ou la feuille à ouvrir), comportement qui la coche.

**Le moteur**
- Les chapitres `GAME_MAP` et `GAME_START_STEPS` sont remplacés par les missions de découverte.
- XP par `awardXp` avec une clé unique (`disc:N`).
- Chaque mission est vérifiée par le serveur, en lecture seule, comme les missions automatiques du parcours (`game/gameplan.php`).
- Les suggestions d'installation, de rappels et de plan deviennent les missions 2 et 10.

**La visibilité** : une fonction est cachée tant que sa mission n'est pas faite.
- Fonctions concernées : Sweep AI, Mon argent (onglet et carte), plan guidé, défis, boss, saison, ligue, crew, Wrapped.
- Le contexte peut l'ouvrir plus tôt : 2ᵉ compte, premier payout, choix dans Réglages.
- « Tout montrer » (Réglages › Ma routine) coche tout.

**Les comptes existants**
- Une marque serveur `users.discovery_done`, posée une fois à la mise en ligne pour tout compte créé avant, donne toutes les missions faites. Elle n'est jamais retirée.
- **Aucun trader actuel ne perd une fonction** : c'est vérifié par un test sur une base avec des traders d'avant.

**Le parcours de 90 jours** : un bouton « Faire maintenant » sur ses missions qui touchent une fonction (compte, trade, revue, bilan, limites). Les missions de découverte équivalentes se cochent en même temps.

**La migration** : la colonne `users.discovery_done` (et la table de progression si le moteur du jeu n'en a pas déjà une qui convient), créées seules au premier appel comme les autres tables du jeu. Elle est à décrire dans la livraison.

**Tests**
- `discovery_test.php` (chaque comportement coche, ouvrir une page ne coche rien, comptes existants) ;
- `e2e_discovery` (jours 1 à 5 simulés, 390 FR et 1300 EN : une mission par jour, « Faire maintenant », fonctions cachées puis montrées) ;
- `e2e_gameplan`.

**Fini quand** : un nouveau trader ne voit au jour 1 que ce qui sert M1, chaque mission se coche par son comportement, et un trader existant voit exactement ce qu'il voyait avant.

### Étape 6 — « Ma progression », Réglages et bilan du vendredi

**But** : finir le ménage du vocabulaire et des doublons (sections 2.1 et 4.4 à 4.6).

**« Ma progression »** (l'ancienne feuille Progression, `game.js:3008`) :
- elle contient niveau, streak, gels, badges, collection, puis les défis et le jeu avancé dès la semaine 3 ;
- elle ne propose plus d'étape ;
- elle sort du menu de gauche ; dans l'avatar, elle s'appelle « Ma progression » ;
- les missions du jeu deviennent « Défis de la semaine ».

**Réglages** : les groupes de 4.5. « Discipline » devient « Ma routine » et reçoit le parcours de 90 jours, le mode de plan, l'heure de verrouillage et les règles de risque. Plus de section sans groupe.

**Bilan du vendredi** : l'écran 2 reprend les questions de « Ta revue de la semaine » du Journal. Le Journal semaine garde ses chiffres et un lien vers le bilan. Un seul nom partout : « Bilan de la semaine ». La règle de la semaine pré-remplit sa question.

**Avatar** : l'entrée « Abonnement » en double est retirée.

**Discipline (D7b)** : les libellés « Discipline » qui montrent la moyenne de checklist (chiffres du jour, Journal, cartes de partage jour / semaine / trade, tableaux de Stats) deviennent « Checklist ». Le score du coach garde seul le mot « Discipline ». Les textes sont à traduire en FR / ES, dans des dictionnaires du code : les fichiers de traduction ne se recompilent pas.

**Guide** : les articles périmés sont mis à jour (« Bien démarrer », « XP »), avec les mots de la section 6.

**Tests** : `e2e_clarity`, `e2e_weekly_content`, `e2e_weekly_card`, `e2e_news`, `e2e_a11y_names`, `e2e_no_english_in_fr_es`.

**Fini quand** : chaque idée a un seul nom dans l'app et dans le guide. Réglages n'a plus de section hors groupe. La part des bilans ouverts se compare à celle de l'étape 0 après deux vendredis.

### Après le chantier

- **Brief du 27 oct. pour la session d'exécution** : `briefs/brief-app-activation-2026-10-27.md`. Il contient :
- A, les défauts du tour ;
- B, la fin de l'étape 3 ;
- C, les mesures des premières minutes ;
- D, la première visite qui s'adapte au moment (séance ouverte, marché fermé, historique à ramener) ;
- E, le rendez-vous du lendemain ;
- F, les pages longues.

C'est dans cet ordre qu'il s'enchaîne avec les étapes de cette section. D et E précisent l'étape 5 (les missions) pour les premières minutes.

**Le 13 novembre** : la liste des fonctions du jeu utilisées par moins de 10 % des traders actifs (Admin › Métriques › Jeu), pour la décision de Mateo (garder, cacher plus longtemps, retirer).
- **Fin du gel** : quand les étapes 0 à 6 sont en ligne et que les mesures M1, journées fermées et bilans ouverts sont relevées. Toute nouvelle fonction passe alors par la section 6.
