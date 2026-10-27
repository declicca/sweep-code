# Brief pour la session App : les premières minutes et le retour du lendemain (27 oct. 2026)

**De** : la session stratégie et tests (SWEEP.md). **Pour** : la session d'exécution (le code de l'app). Décision de Mateo du 27 oct. : une session pense et vérifie, l'autre code.

**À lire d'abord**
- `SWEEP.md` : la carte du parcours. Les règles de la section 6 valent pour chaque étape ci-dessous.
- `docs/parcours/TOUR-2026-10-27.md` : le tour de l'app qui fonde les étapes A et F.
- `docs/parcours/MESURE-0.md` : le point de départ.

**Pourquoi ce brief** : les premières minutes décident si un trader revient. Le « déclic » de Sweep, c'est le moment où le trader sent que l'app le protège : **« Ton risque permis aujourd'hui »** avant de trader, puis **« Il te reste X $ »** après son premier trade. Point de départ (MESURE-0) : 11 touchers jusqu'au risque permis, 16 jusqu'au premier trade. Tout ce qui suit sert l'un de ces trois objectifs :
- amener chaque nouveau trader à ce déclic dès sa première visite ;
- lui donner un rendez-vous pour le lendemain ;
- ne jamais le perdre sur un défaut.

**Règles de travail** (celles de `CLAUDE.md`, `app/CLAUDE.md` et `SWEEP.md` section 7) :
- une étape à la fois, dans l'ordre ;
- tests ciblés, puis la suite complète (`python3 tools/par.py 4`) à 0 échec, puis le push et la CI verte (`python3 -I app/tools/ci-status.py $(git rev-parse HEAD)`) ;
- `CONTEXTE-APP.md` mis à jour dans le même commit ;
- EN / FR / ES, 390 × 844 tactile et 1300 × 850, clair et foncé ;
- **aucun déploiement sans l'accord de Mateo** ;
- chaque terme de trading s'explique là où il s'affiche ;
- pas de « facultatif » à côté d'un champ.

À la fin de chaque étape : la liste exacte des fichiers, la migration SQL et la tâche cron s'il y en a, et le sha vert. La session stratégie et tests vérifie ensuite les critères « Fini quand » et met `SWEEP.md` à jour.

---

## Étape A — Les défauts qui font perdre un nouveau trader (un seul lot)

**But** : rien, dans les premières minutes, ne doit faire perdre un trade, parler anglais à un francophone ou bloquer l'écran. Détails et captures dans `docs/parcours/TOUR-2026-10-27.md`, section A.

| # | Défaut | Correction attendue |
|---|---|---|
| A1 | **Formulaire manuel (`#tkSlide`)** : le prix d'entrée montre « 21845.25 » en texte indicatif gris, le champ a l'air rempli. « Enregistrer » refuse, avec « Ajoute le prix d'entrée » tout en bas, et **le trade n'est pas enregistré**. | Pas de nombre en texte indicatif (le vrai prix en valeur s'il est connu, sinon vide). À une erreur : défiler jusqu'au champ, le cadre en or, le curseur dedans (comme le pré-marché : « Il manque : … »). |
| A2 | La checklist du formulaire de trade est **en anglais pour un trader français** (questions par défaut). | Les questions par défaut dans la langue du trader partout : formulaire manuel, feuille par capture, page du trade. Réglages le fait déjà (18 oct.). |
| A3 | « **1 nouveautés** · Voir Progression ». | Singulier et pluriel, dans les 3 langues. |
| A4 | Page de bienvenue : **la barre du bas reste affichée** et cache une tuile du choix de compte. | Cachée sur cette page, comme le « + ». |
| A5 | Page de bienvenue : « Ajoute Sweep à l'écran d'accueil : Safari → Partager… » dès le jour 1. | Retirée de cette page (règle : jamais le jour de l'inscription). |
| A6 | Le coach dit « Pas de setup choisi » à un trader « Moins de 6 mois », alors qu'il ne réclame pas de setup à un débutant (brief 03). Cause probable : `S.me.experience` pas relu après l'inscription. | À vérifier, puis le ton débutant dès le premier plan. |
| A7 | **« Ton vrai net »** s'ouvre seul à la 1ʳᵉ visite de Mon argent, même sans payout ni trade. Il bloque ensuite le menu tant qu'il reste ouvert, avec un cadre de focus bleu sur son titre. | Ouverture automatique seulement à partir d'un premier payout enregistré. Avant, l'invitation reste dans la carte. Aucun cadre de focus visible sur un titre. |

**Tests**
- Un test qui échoue sur l'ancien code pour chaque défaut ; les tests existants touchés : `e2e_first_run`, `e2e_realnet`, `e2e_trade_form`, `e2e_no_english_in_fr_es`.
- Le parcours de `tools/parcours-baseline.py` passe sans erreur, y compris un cas « prix d'entrée oublié » qui doit aboutir.

**Fini quand** : un nouveau trader au téléphone en français ne voit plus un mot d'anglais, ne perd aucun trade, et rien ne s'ouvre par-dessus sans raison.

---

## Étape B — Finir l'étape 3 de SWEEP.md (« Maintenant »)

Tout est dans `SWEEP.md`, section 7, « Étape 3 », **« Relais vers la session d'exécution (27 oct.) »**. En résumé :
- rebaser la branche locale `parcours-3b` sur `main` ;
- corriger la fenêtre d'installation qui ne s'ouvre plus le 2ᵉ jour sur téléphone (diagnostic dans le relais) ;
- mettre à jour `e2e_first_run`, `e2e_session_news_ui`, `e2e_lot_a` (1.2, 1.3) et `e2e_copy_once` ;
- ajouter la ligne de mission.

**À ajouter** (tour du 27 oct.) : **avant le premier trade, la routine ne montre ni « Discipline — », ni la série « 0 », ni le niveau**. Ces chiffres n'ont pas de sens le premier jour. Ils apparaissent avec le premier trade.

**Fini quand** : les critères « Fini quand » de l'étape 3 dans SWEEP.md, plus ces chiffres cachés avant le premier trade.

---

## Étape C — Mesurer les premières minutes (avant de les changer)

**But** : savoir où et quand les nouveaux traders décrochent, pour décider de l'étape D sur des chiffres. Lecture seule, dans Admin › Métriques (`ops/metrics.php`, bloc `brief` ; `src/ux.js` section 15), avec les mêmes filtres (semaine d'inscription, source).

**Trois indicateurs de plus :**
1. **Quand on s'inscrit** : la répartition des inscriptions selon l'heure de New York au moment de l'inscription, en 4 cases :
   - avant l'ouverture (18 h la veille → 9 h 30) ;
   - séance (9 h 30 → 16 h) ;
   - soir (16 h → 18 h) ;
   - fin de semaine (vendredi 17 h → dimanche 18 h).
   Pour chaque case : combien d'inscrits, et quelle part fait un premier plan ou un premier trade le jour même.
2. **Le retour du lendemain (J1)** : la part des inscrits qui reviennent le jour de trading suivant l'inscription. Revenir veut dire une visite (`users.last_login` change aussi au retour), un plan ou un trade. Seulement les traders dont ce jour est passé.
3. **Le risque permis vu le jour même** : la part des inscrits dont le premier plan, ou le premier trade, a lieu le jour de l'inscription, c'est-à-dire qui ont vu le risque permis ou « il te reste ». Calculé sur ce qui est déjà enregistré : aucun nouvel événement n'est nécessaire.

**Tests** : `metrics_test.php` (chiffres calculés à la main, base jetable) et `e2e_admin_metrics`.

**Fini quand** : les 3 indicateurs sont dans Admin › Métriques, à 390 et 1300.

Une fois déployés, la session stratégie et tests relève les chiffres réels dans `docs/parcours/MESURE-0.md`. **Ce relevé décide de l'ordre des cas de l'étape D.**

---

## Étape D — La première visite qui s'adapte au moment

**But** : chaque nouveau trader repart de sa première visite avec quelque chose d'utile, même s'il ne trade pas à ce moment-là.

**Le constat** : le démarrage actuel (compte → plan → premier trade) suppose que le trader vient de trader. Inscrit un soir ou un week-end, il n'a rien à saisir et repart sans avoir rien vu. L'étape C dira dans quelle proportion.

**Un démarrage, trois fins selon le moment et le trader.** Les deux premiers écrans restent les mêmes : le prénom, l'expérience et le compte.

| Cas | Quand | Après « Créer le compte » |
|---|---|---|
| **Séance ouverte** | 9 h 30 → 16 h ET, jour de trading | Comme aujourd'hui : le plan court (risque permis), puis le premier trade (étape 2 : sans capture en 4 touchers). |
| **Marché fermé** | Le reste du temps | **« Prépare ta séance de demain »**. Le plan court pour la séance suivante (`SweepNextSession`), son risque permis, la grande annonce de cette séance s'il y en a une, puis **le rendez-vous** (étape E). Pas de formulaire de trade. Un lien discret reste : « J'ai tradé aujourd'hui : ajouter mon trade ». |
| **Trader déjà en activité** | « Plus d'un an », ou un compte « déjà en cours » | Après le plan court : **« Ramène ton historique »**. La synchro NinjaTrader 8 ou Quantower, ou l'import CSV de la feuille « + », en un écran. « Plus tard » mène au cas du moment. Avec un historique, Aujourd'hui, Stats et « Ton edge » sont remplis dès la première visite. |

**Règles**
- La page de bienvenue annonce la bonne fin : « Ton compte · Ton plan · Ton premier trade », ou « Ton compte · Ton plan de demain », ou « Ton compte · Ton plan · Ton historique ».
- Rien n'est ajouté au premier écran.
- Les touchers jusqu'au risque permis ne doivent pas augmenter (11 au départ).
- Admin › Métriques › « Le démarrage » suit les trois cas : chaque inscrit est rangé dans un cas selon l'heure de son inscription.

**Tests** : `e2e_first_run` (les trois cas, horloge fixée : un mardi 10 h 30, un mardi 20 h, un samedi 11 h) et `tools/parcours-baseline.py` (les trois cas). Fichiers concernés : `src/nav.js` (page de bienvenue, `stage()`), `src/game.js` (`openPlan(…, { then })`), `src/ux.js` section 30 (synchro).

**Fini quand** :
- dans les trois cas, le trader voit son risque permis à la première visite ;
- le marché fermé ne montre jamais un formulaire de trade vide ;
- le trader « déjà en activité » se voit proposer son historique avant son premier trade.

---

## Étape E — Le rendez-vous du lendemain

**But** : chaque nouveau trader quitte sa première visite avec un rendez-vous.

1. **Juste après le premier plan, le rappel du lendemain.**
   - Dans la feuille du plan, après « Enregistrer » : « Je te rappelle demain à 8 h 45 pour ton plan ? » (l'heure du réglage existant, modifiable). Un toucher l'active.
   - Le chemin est celui de Réglages › Notifications : `SweepNotify.push.on()`.
   - Sur iPhone, hors écran d'accueil : on explique les 3 gestes d'ajout, au lieu d'un refus.
   - Cette proposition remplace, pour un nouveau trader, la suggestion « rappels » du 2ᵉ jour. Une seule fois.
2. **Les courriels partent déjà** : Loops est actif en ligne (Mateo, 27 oct.). Les événements utiles existent (`signedUp`, `firstAccountAdded`, `firstTradeLogged`). Rien à coder, sauf si le courriel du soir doit savoir si un plan est fait : alors un événement `firstPlanSaved`, une fois par trader, comme les autres.
3. **Le texte des courriels** se rédige dans Loops, pas dans l'app. Deux courriels sont à proposer à Mateo, en EN / FR / ES, dans `ops/NOTIFICATIONS.md` :
   - « Ta séance de demain en 30 secondes » : le soir du jour 1, s'il n'y a pas encore de plan pour le lendemain ;
   - celui du 3ᵉ jour d'absence (`inactive3d`, déjà prévu).

**Tests** : `e2e_push` (la proposition après le premier plan, une seule fois ; iPhone hors écran d'accueil) et, s'il est ajouté, `loops_test.php` pour `firstPlanSaved`.

**Fini quand** :
- après son premier plan, un nouveau trader au téléphone peut activer le rappel du lendemain en un toucher ;
- les deux textes de courriels sont proposés à Mateo.

---

## Étape F — Les pages longues (après l'étape 4 de SWEEP.md)

D'après le tour (section C de `TOUR-2026-10-27.md`) :
- **C1** : pour un trader « Moins de 6 mois », la perte max proposée est la moitié de la limite du jour du compte, avec « Commence petit : tu pourras la monter ». C'est la même règle que le plafond par la marge de drawdown. **À faire avec l'étape 2 de SWEEP.md**, quand elle partira.
- **C2** : la liste des trades groupée par jour (date, P&L, nombre de trades), les 2 dernières semaines, puis « Voir plus » (aujourd'hui : une ligne par trade, par tranches de 100 ; 7 887 px sur téléphone pour 130 trades).
- **C3** : la page d'un trade. Un seul endroit pour le setup ; « Contexte économique » seulement s'il y a une annonce ; les frais dans « Plus de détails ».
- **C4** : le formulaire manuel n'ouvre que ses champs. « Saisir avec l'IA », « Par capture d'écran » et « Importer un CSV » sont déjà dans la feuille « + ».

**Fini quand** : la liste des trades et la page d'un trade font au moins un tiers de hauteur en moins sur téléphone, sans perdre d'information.

---

## Ordre et ce qui attend Mateo

**Ordre** :
1. A ;
2. B ;
3. C, puis son déploiement (avec l'accord de Mateo) et le relevé des chiffres réels ;
4. D, dans l'ordre que les chiffres de C indiquent ;
5. E ;
6. F, après l'étape 4 de SWEEP.md.

L'étape 2 de SWEEP.md reste en attente de la semaine de mesure de l'étape 0.

**De Mateo** :
- la date du déploiement de `ade074b`, pour MESURE-0 ;
- son accord pour chaque déploiement.
