# Audit du site makeitsweep.com — 18 octobre 2026

Audit complet fait sur le build local du site : 261 pages, 88 par langue en EN, FR et ES.

**Ce qui a été vérifié** :
- l'exactitude face à l'app (`origin/main`, CONTEXTE-APP.md, code, commits jusqu'au 18 oct. à 8 h 34) ;
- les textes dans les 3 langues ;
- la technique (poids, accessibilité, SEO avancé, serveur) ;
- le rendu visuel, page par page, à 390 et 1300 px.

Aucune requête n'a été envoyée au serveur, sauf 2 requêtes douces pour confirmer que la dernière version de l'app est en ligne.

**Déjà au vert avant l'audit** :
- `qa.py all` : mise en page des 261 pages à 6 largeurs, en clair et en sombre, aucun problème ;
- SEO de base : aucun problème ;
- 60 vérifications fonctionnelles sur 60 ;
- 64 vérifications au clavier sur 64.

L'audit cherche donc ce que ces tests ne voient pas.

**Déjà corrigé pendant l'audit** (commit local 81ec616) : sur ordinateur, à l'accueil, la partie « Payouts » collait aux liens de la partie « Prop firms » (10 px). Il y a maintenant 80 px entre deux parties hautes de la narration.

## Avancement (18 oct., en ligne)

- Étape 1 (faits faux, textes légaux), étape 2 (ce que le site ne disait pas), étape 3 (textes et traductions) : faites.
- Étape 4 : 4a serveur et performance, 4b accessibilité et visuel, 4c SEO : faites ; aussi une CSP sur les pages et le préchargement de Geist Mono.
- Vidéo de l'accueil réencodée en 1080p (`ffmpeg`) : WebM 3,8 → 1,5 Mo, MP4 5,6 → 1,8 Mo, même qualité visible.
- Les 5 décisions, tranchées par Mateo le 18 oct. et en ligne : Quantower partout ; captures en Free, 3 par jour ; synchro Rithmic/Tradovate « prévue plus tard » ; bleu des boutons foncé (#2F6FE8) et boutons refaits. Comptes en Pro : carte blanche, « illimité » comme l'app (brief `briefs/brief-app-forfaits-2026-10-18.md`).
- Ajoutés le 18 oct. au soir : animations pilotées par le défilement (comme apple.com) ; page `/quantower` ; page Tarifs refaite pour la conversion (limites chiffrées, une raison par forfait, « Pourquoi les traders passent à Pro », tableau groupé, offre fondateur retirée de la page publique).
- Reste à Mateo : la compression du serveur (cPanel › Optimiser le site Web › Compresser tout le contenu) ; vérifier dans `sweep-private/billing-config.php` que Free garde 2 comptes et que Pro est illimité.
- Reste en attente : étape 5 (captures et vidéos de la session App).
- Laissés volontairement : copies de 300 px des vignettes de téléphone (gain seulement sur les écrans 1x), textes des paires firme contre firme (proches par construction, déjà chiffrés), HSTS `includeSubDomains` (sous-domaines cPanel non vérifiés), Geist Mono réduite (elle n'a que 440 glyphes latins : 1,2 Ko de gagné seulement, et « chiffres seulement » casserait les dates en chasse fixe ; elle est préchargée).

Gravité : **haute** = un fait faux ou un texte légal inexact ; **moyenne** = un manque visible ou une incohérence ; **basse** = de la finition.

---

## Étape 1 — Faits faux et textes légaux (haute)

| # | Où | Le site dit | La réalité (app) | Correction |
|---|---|---|---|---|
| 1.1 | /pricing, tableau (`pages6.py:211-241`) | « Journal, calendrier, analyses ✓✓✓ » ; Sweep AI « quota de base » | Free : Stats limité aux derniers jours (`app.js:7408`) ; avis IA d'un trade en Pro (3/mois) et Elite ; rapport IA de la semaine et notes complètes du calendrier en Elite seulement | Reprendre les lignes de la page des forfaits de l'app (historique, messages IA, import IA, avis IA, notes du calendrier, rapport de la semaine) ; ajouter « Ton coach » et « Ton edge » ✓✓✓ |
| 1.2 | /pricing (`pages6.py:261`) et /terms (`legal.py:147, 175, 203`) | Le filleul reçoit « 30 jours de Pro » | 14 jours d'**Elite** en plus de l'essai Pro (`growth/referral.php:13`) | Corriger les deux pages, Conditions comprises |
| 1.3 | /ninjatrader (`pages20.py:226`), /import (`pages11.py:29-33`) | Exporter un CSV depuis Trade Performance de NinjaTrader et l'importer | L'import ne lit que Tradovate, Rithmic, TopstepX et TradingView (`ux.js:1193`) : un CSV NinjaTrader est refusé | Retirer ces étapes ; pour l'historique : une capture de l'historique, ou l'export du courtier |
| 1.4 | /privacy (`legal.py:22, 64, 106`), /security (`pages2.py:175`) | L'app charge sa police depuis Google Fonts | Polices servies par l'app, la CSP refuse Google Fonts (16 oct.) | Retirer la mention et la ligne « Tiers » |
| 1.5 | /privacy (`legal.py:11-46`), /security (tableau) | Un seul témoin (`tj_session`) ; compte = nom d'utilisateur, courriel… | Manquent : le témoin `tj_dev` (appareil reconnu 30 jours), la liste des appareils reconnus, les codes de connexion, la clé publique Face ID, les appareils abonnés aux notifications, le prénom et l'expérience, les courriels de code, « Nouvelle connexion » et « Ta semaine » | Compléter « Ce que nous recueillons », « Sur ton appareil » et « Courriels » (Loi 25) |
| 1.6 | /features (`pages1.py:81`), /terms (`legal.py:156, 184, 212`), comparatifs (`pages17.py:46`) | Les 8 actions IA sont incluses dans tous les forfaits | Le scan d'un reçu, les avis IA et le rapport de la semaine sont payants | « Sweep AI dans tous les forfaits, certaines actions en Pro ou Elite », en marquant lesquelles ; corriger la clause des Conditions |
| 1.7 | /free-trading-journal (`pages20.py:13, 89, 96`) | Gratuit pour toujours : journal, calendrier, analyses… | L'historique des analyses est limité en Free | « Tes N derniers jours d'analyses » ; ajouter à « Ce que Pro ajoute » : Mon argent, l'historique complet, l'IA |
| 1.8 | Pages des firmes (Topstep, Lucid, TPT, MFF) dans les 3 langues | « Dernière vérification : 7 oct. » plus haut, puis « depuis notre première vérification, le 9 oct. » ; le hub dit « 14 oct. » | La « première » vérification tombe après la « dernière », et « vérifiées chaque semaine » ne colle pas avec un 7 oct. (`pages18.py:8, 45-47, 299-306`) | Écrire « depuis le début de notre journal des changements, le 9 oct. » et afficher la même date que le hub (ou revérifier ces 4 firmes) |
| 1.9 | /security (`pages2.py:164-168`) | Connexion protégée : HTTPS, limites de tentatives | La double authentification existe depuis le 17 oct. (code par courriel, appareils reconnus, « Nouvelle connexion », Face ID) | Une carte « Double authentification et appareils », plus une ligne dans la FAQ |
| 1.10 | /faq (`pages2.py:59-61`), /security, /privacy (`legal.py:33`) | « Les autres peuvent-ils voir mes résultats ? Jamais » | Le profil public de discipline existe (éteint par défaut, jamais un montant) | Le mentionner (« jamais sans ton accord, jamais un montant ») |
| 1.11 | /features (`pages1.py:127`), /privacy (`legal.py:39`) | Partage : « rien n'est téléversé » | « Créer un lien » garde l'image sur Sweep jusqu'à sa suppression (`growth/share-links.php`) | « Images faites sur ton appareil ; un lien que tu crées est gardé sur Sweep jusqu'à ce que tu le supprimes » |

**Plus petits, même étape** :
- **« Plus de 35 badges »** (`pages6.py:55-57`, ancienne entrée de /changelog) : il y en a 31 (`game/catalog.php`).
- **Copy trading « avec le total de tous les comptes »** (FAQ `pages2.py:22-24`, aussi dans son JSON-LD ; lexique `pages13.py:245`) : un groupe de copies compte une fois, comme le trade d'origine ; chaque compte suiveur a sa propre taille.
- **Calendrier : « notes IA avant chaque annonce »** (`pages3.py:51, 114`, `pages1.py:71-75`, accueil) : titre et résumé pour tous, rapport complet en Elite.
- **« Budget de risque du jour avant et après ce trade »** (`pages1.py:25`) : la case a été retirée le 17 oct. ; il reste la ligne du coach « il te reste X ».
- **« Checklist de discipline (5 questions) »** (/how-it-works `pages6.py:23`) : 13 questions, dont 3 sur le formulaire (/features dit déjà 13).
- **Instruments** (FAQ `pages2.py:51-53`) : P&L automatique sur 22 instruments, graphiques sur 14.
- **« Un boss chaque semaine »** (accueil `pages16.py:83`) : les boss viennent de tes mauvaises habitudes et restent jusqu'à ce que tu les battes.
- **« Export JSON »** (méta de /security) : c'est un export ZIP (JSON, CSV et captures).
- **/import** (`pages11.py:59`) dit « un compte à la fois » et, plus haut, que Rithmic répartit plusieurs comptes. Écrire « un compte à la fois, sauf Rithmic ».
- **Rattrapage du vrai net « au démarrage »** (`pages20.py:180`) : il s'ouvre la première fois que tu ouvres Mon argent, en Pro.

### À trancher par Mateo avant d'écrire

1. **Quantower** : la synchro est ouverte à tous depuis le 13 oct. et les Nouveautés l'annoncent. Mais la FAQ, /ninjatrader, les comparatifs, /100 et llms.txt disent « NinjaTrader 8 seulement », et conseillent même un autre journal pour toute autre synchro. Faut-il l'ajouter partout, ou retirer l'annonce des Nouveautés ?
2. **Lecture des captures en Free** : l'app se contredit. Sa page des forfaits dit « import IA » non inclus en Free, mais la feuille par capture marche en Free (quota du jour). La règle se décide dans l'app, puis le site suit (/pricing la coche en Free).
3. **Comptes en Pro** : l'app dit « Pro has no limit » (`app.js:7400`), alors que la configuration de test dit 5. Le site écrit « Plus ». Quelle valeur en production ?
4. **« Synchro Rithmic et Tradovate en développement »** (FAQ, /import, /ninjatrader, llms.txt, comparatifs) : d'après CONTEXTE-APP, c'est « plus tard ». Écrire « prévue plus tard », ou retirer ?
5. **Contraste des boutons bleus** (T8, étape 4) : le blanc sur #4C8DFF ne passe pas le niveau AA. Faut-il foncer le bleu des boutons seulement ? C'est une décision de palette.

---

## Étape 2 — Ce que l'app fait et que le site ne dit pas (moyenne)

- **« Ton coach »**, gratuit et sans IA, présent sur chaque trade, avant le trade, dans la revue et dans les alertes à 75 % et 100 %. Absent de /features, de l'accueil, de /how-it-works et de /pricing.
- **« Ton edge »**, gratuit pour tous depuis le 16 oct. : setup en un toucher, « Dans ton edge » avant un trade, séries expliquées, carte du profil, questions qui s'adaptent, leçons qui reviennent. Le slogan est « Ton edge, enfin au même endroit » et la fonction existe maintenant sous ce nom : c'est la meilleure histoire à raconter sur l'accueil et dans /features. Il faut aussi une ligne ✓✓✓ dans /pricing et une phrase dans llms.txt.
- **Notifications** : rappels du plan et de la revue, bilan de la semaine, alertes de limite ; au plus 2 par jour. À ajouter dans /features et /install.
- **/install** dit qu'« un nouveau téléphone n'a besoin que d'une connexion ». Il faut maintenant le code par courriel ; Face ID est proposé dans l'app installée ; les rappels sur iPhone demandent l'installation.
- **/features** n'a pas de section « Ajouter tes trades » (imports CSV, NinjaTrader 8, captures), qui renverrait vers /import et /ninjatrader.
- **/how-it-works** : les étapes et le JSON-LD HowTo ne suivent pas le démarrage en 3 étapes de l'app (compte, plan prérempli, premier trade), et le coach n'y est pas. La carte Edge Reveal ne dit pas « chaque semaine en Pro » et cite des exemples remplacés par le profil edge.
- **Comparatifs** (`pages17.py:48, 198, 247, 260-262`) : on crédite Edgewonk d'un « edge finder chaque semaine » et on conseille TraderSync « si tu veux un coach IA », alors que Sweep a maintenant un coach et un profil edge gratuits.
- **Cartes de partage** (/features `pages1.py:122-126`, FAQ `pages2.py:72`) : chaque partage s'ouvre sur la carte Discipline, avec les montants masqués par défaut, et un lien est un instantané (pas « un lien vers ta page Stats »).
- **Révision d'un trade** (/features `pages1.py:43-48`) : la page du trade s'ouvre sur « Réponds au coach », avec la revue complète repliée dessous.

---

## Étape 3 — Textes et traductions (moyenne à basse)

**Restes d'anglais et termes**
1. **Calendrier économique FR/ES** : les 12 indicateurs sont en anglais (`pages2.py:100`, liste EN seulement). La même section annonce « 19 indicateurs » mais en liste 17 (`pages3.py:138`, `pages1.py:77`).
2. **Pages de dates PIB et ventes au détail FR/ES** :
   - H1 et titre : « Dates de publication GDP », « Dates Retail Sales » (`pages13.py:25, 28`) ;
   - lignes du tableau : « GDP (Advance)… » (`pages13.py:141`).
3. **/pricing FR/ES** : « Log with AI » (`pages6.py:213, 239`) doit devenir « Saisie avec l'IA » / « Registro con IA ».
4. **/es/pricing** : « Pro $19/mes » (`pages6.py:246`) doit suivre le format du site : « 19 $/mes ».
5. **Libellés d'accessibilité FR/ES** : « Sweep on Instagram / TikTok / Facebook » (`core.py:659`), « Menu » en ES (`core.py:406, 408`), « Langue: Français » sans espace (`core.py:352`).
6. **ES** : « cuenta fondeada » (58 fois) et « cuenta financiada » (160 fois) sont mélangés. Garder « financiada », le terme de l'app.
7. **Liens « Sources » construits à partir des URL**, avec une casse cassée : « Eod payouts », « Consistency at topstep », « My funded futures launches builder 25k… » (`pages18.py:38-44`). Il faut une table de casse (EOD, PA, Topstep, 25K…).
8. **FR** : « tableau de bord » plutôt que « dashboard » à l'accueil ; « objectif de profit » plutôt que « cible de profit » ; « crews » plutôt qu'« équipes » ; « streak » pour la discipline ; « par an » ou « par année », pas les deux sur /pricing.
9. **ES** :
   - « añadir » plutôt qu'« agregar » ;
   - « coste » plutôt que « costo » ;
   - « lo cerca que está » plutôt que « qué tan cerca » ;
   - « operaciones compartidas » ;
   - « la Oficina del Censo » (« la Census Bureau »).
10. **Kit presse** : « Contact : » en EN et « Contacto : » en ES (`pages13.py:431`) ; noms des couleurs non traduits (`pages13.py:427`).
11. **JSON-LD** des offres en anglais sur FR/ES : « Pro monthly… » (`pages6.py:265`, `core.py:310`).

**Typographie et grammaire FR**
12. **Élision manquante** : « Les règles de Alpha Futures », « le site officiel de Apex Trader Funding » (gabarit `de {name}`, une vingtaine de lignes de `pages18.py`), « Qu'est-ce que Ask Sweep ». Un petit utilitaire « d' devant une voyelle » règle tout.
13. **Espace avant « ? » et « ; »** : manque dans 43 phrases (/contact, /faq, /fr/100, /ai, /changelog, /security, /features, /terms, /privacy).
14. **Espaces insécables absentes** des titres, méta descriptions, `alt` et `aria-label` (25 titres, 33 méta) : `nbsp()` (`core.py:614`) ne les traite pas.
15. **Majuscule après le deux-points dans les H1 composés FR/ES** (`ui.py:169`) : « Apex vs Lucid : Les règles… ».
16. **Double espace** dans le titre de /fr/trading-journal-routine (`core.py:252`).
17. **Une page, trois noms** : « Comment ça marche » (menu), « Comment Sweep fonctionne » (H1), « Comment marche Sweep » (titre).
18. **Tournures** : « Mon P&L dans Sweep diffère de ma plateforme ? » (`pages2.py:43`) ; le seul vouvoiement du site, « Offrez-vous des remboursements ? » (`pages2.py:15`).
19. **EN** : « The first 100 is full. » (`pages5.py:11`) doit devenir « The first 100 spots are taken. »

---

## Étape 4 — Visuel, parcours et technique

- **Tableau « Compare les forfaits » sur téléphone** : 4 colonnes à 390 px, et la première coupe ses mots (« ca-lendrier », « hebdoma-daires »). Proposition : sur téléphone, mettre le libellé de chaque ligne au-dessus de ses trois valeurs.
- **Pied de page sur téléphone** : environ 1,5 écran de liens (5 groupes, plus de 35 liens). Proposition : replier chaque groupe sur téléphone.
- **Hub /prop-firms/** : beaucoup de lignes « — » (partage, évaluation la moins chère, consistance), qui font vide. Proposition : cacher une ligne quand la firme n'a pas la valeur (la note du bas l'explique déjà).
- **/import sur téléphone** : « colle-la avec Ctrl+V ». L'app dit maintenant « Touche pour choisir une capture » sur téléphone.

### Technique

Mesuré sur les 261 pages, à deux formats : mobile 390×844 et ordinateur 1300×850. Les pages clés ont aussi été mesurées en « 4G lente ».

**Déjà bon** :
- CLS de 0 partout ;
- LCP mobile de 0,94 à 1,26 s en 4G lente ;
- une seule feuille qui bloque l'affichage (10,6 Ko compressée) et un JS de 7,9 Ko ;
- toutes les images en WebP, avec leurs dimensions ;
- 0 image sans `alt` et 0 lien sans nom ;
- hreflang réciproques et JSON-LD valide ;
- toutes les pages à 2 clics au plus de l'accueil.

**Performance**

| # | Constat | Mesure | Correction |
|---|---|---|---|
| T1 | La vidéo de l'accueil se télécharge en entier à la première visite, dès que la page est inactive (`site.js:255`, `pages6.py:113-115`) | 1,3 Mo sur mobile, 3,9 Mo sur ordinateur (5,7 Mo en mp4 pour Safari). L'accueil pèse 4,2 Mo sur ordinateur ; les autres pages ont une médiane de 175 Ko | Charger la vidéo seulement quand elle est visible (jamais en mode économie de données) et la réencoder vers 1 Mb/s (environ 1,5 Mo) |
| T2 | L'image principale du héros est marquée `fetchpriority="low"` (`ui.py:174`, `core.py:642`) sur 21 pages : /features, /ai, /import, /payout-tracker, /prop-firm-tracker, /free-trading-journal, /economic-calendar | Le LCP baisse de 140 à 190 ms avec `high` (test A/B en 4G lente) | Passer en `high` |
| T3 | Des blocs déjà à l'écran restent invisibles jusqu'à 400 ms après le chargement (`site.js:240-249`, `system.css:989`) : les chiffres clés des firmes, « Les différences en un coup d'œil », /contact, /guides | /sweep-vs-tradezella : LCP à 984 ms pour un premier affichage à 80 ms | Avant de masquer, marquer comme vu tout ce qui est déjà à l'écran |
| T4 | Image LCP en `loading="lazy"` sur /changelog et /install (ordinateur) | Visuel en haut de l'écran | `eager` et priorité haute |
| T5 | Images plus grandes que leur affichage | Héros d'ordinateur : le fichier de 2400 px pour 1204 px affichés. /changelog : 1200 px pour 387. /how-it-works : 600 px pour 184 | `sizes` exacts, et des variantes de 1600 et 600 px |
| T6 | Geist Mono (36 Ko) est chargée sur toutes les pages sans préchargement | En 4G lente, elle finit de charger entre 1,3 et 1,5 s | La réduire aux chiffres et aux symboles (environ 6 Ko) |
| T7 | Préconnexion à app.makeitsweep.com sur les 264 pages (`core.py:367`) | Seul l'accueil appelle l'app | Préconnexion sur l'accueil seulement |

**Accessibilité**

| # | Constat | Correction |
|---|---|---|
| T8 | Texte blanc sur le bleu #4C8DFF des boutons principaux : contraste de 3,2:1 (2,7:1 en haut du dégradé), pour 4,5:1 demandés. Toutes les pages | **À trancher** (palette) : un bleu plus foncé pour le fond des boutons seulement (#2F6FE8 = 4,6:1), en gardant #4C8DFF pour les gains et les liens |
| T9 | Anneau de focus #4C8DFF sur le fond clair : 2,9:1 (3:1 demandé, `system.css:80`) | `var(--blue-text)` en thème clair |
| T10 | Saut de niveau h1 → h3 sur 33 pages (des cartes juste après le héros, `ui.py:90`) | Un niveau de titre réglable dans `ui.card()` |
| T11 | Cibles tactiles sous 44 px : bouton du menu (40), icônes sociales (38), croix du bandeau de langue (30), puces des outils liés (32) | 44 px minimum |
| T12 | Même texte de lien pour des pages différentes : « Toutes les firmes, comparées », « Le guide pas à pas », « Télécharger le PDF » | Ajouter le nom de la cible, réservé aux lecteurs d'écran |
| T13 | Le bandeau « Cette page existe aussi en… » n'a pas d'attribut `lang` (lu avec la mauvaise voix) ; le H1 découpé en mots pour l'animation risque d'être lu mot par mot par VoiceOver ; 107 tableaux sans légende | `lang` sur le bandeau, `aria-label` sur le H1, `caption` réservé aux lecteurs d'écran |

**SEO**

| # | Constat | Correction |
|---|---|---|
| T14 | Le guide pilier `/trading-journal-guide` est presque orphelin : seules /guides et /glossary le relient. `website/CLAUDE.md` affirme le contraire | L'ajouter aux « À lire aussi » de Routine, Modèles, Import et des 5 guides de règles, et au pied de page |
| T15 | Les 4 comparatifs « Sweep vs » reçoivent 4 ou 5 liens chacun, les guides d'export 3 | Un groupe « Comparer » dans le pied de page |
| T16 | `llms.txt` : 37 pages anglaises manquent (/import, /faq, /install, calculateurs, contrats, dates…), sans date ni entrée FR/ES | Générer la liste au build à partir des pages |
| T17 | Données structurées `Article` (42) sans `image` ; leur `dateModified` est codé en dur et diffère du sitemap sur 36 pages | Prendre l'image de partage et la date de `lastmod.json` |
| T18 | Pages proches : contrats mini et micro (51 à 54 % de texte commun), paires firme contre firme (41 à 49 %), /prop-firms/tradeify (402 mots) | Un paragraphe propre à chaque jumeau ; étoffer Tradeify |
| T19 | 47 pages × 3 utilisent l'image de partage générique (contrats, dates, lexique, /how-it-works, /import…) | Étendre `tools/og_images.py` |
| T20 | `robots.txt` : les groupes des robots IA remplacent le groupe `*` (le `Disallow` des utm ne s'applique pas à eux) ; `/search` n'existe pas | Un seul groupe `*` ; retirer `/search` |

**Serveur (`.htaccess` écrit par `build.py`)**

| # | Constat | Correction |
|---|---|---|
| T21 | Images, vidéos et icônes sans empreinte gardées 30 jours en `immutable` (`build.py:187`). Avec la refonte des captures et des vidéos qui arrive, les visiteurs qui reviennent garderaient les anciennes | `max-age` sans `immutable` pour les noms sans empreinte, ou de nouveaux noms à chaque refonte. **À faire avant l'étape 5** |
| T22 | Compression : il manque `text/javascript`, `application/json` et RSS/XML, et il n'y a pas de Brotli (`build.py:200`) | Ajouter ces types (vérifier une fois en ligne que le JS part compressé) |
| T23 | Deux redirections de suite (`http://www` → `https://www` → `https://makeitsweep.com`) ; `/pricing/` répond 200 en double de `/pricing` ; `/404` répond 200 | Une seule redirection ; 301 qui retire la barre oblique finale ; exclure `404` de la réécriture |
| T24 | Pas de CSP ; HSTS sans `includeSubDomains` ; `.txt` et `.xml` sans charset ; une règle morte (`build.py:154`) | CSP d'abord en mode « rapport seulement », `AddCharset utf-8`, retirer la ligne morte |

---

## Étape 5 — Captures et vidéos (en attente de la session App)

Les captures et les vidéos montrent l'app d'avant la refonte iOS, avec des écrans en anglais sur les pages FR/ES : vidéo de l'accueil (« Good afternoon, Alex », « Today »), affiche de /how-it-works (« Your day, one screen. »), calendrier économique, montants au format « $34,550 ». C'est déjà prévu dans `briefs/brief-captures-site-2026-10-16.md` ; il faut attendre que la session App produise les nouvelles captures.

---

## Points forts

- Aucun titre de plus de 60 caractères, toutes les méta descriptions entre 70 et 160, aucun doublon, un seul H1 par page, `lang` juste partout.
- Tutoiement tenu partout en FR et tuteo en ES (un seul « vous »), ¿ et ¡ présents, montants bien formatés, aucun reste (TODO, NaN, undefined, 2025…).
- Les 2 719 chaînes existent dans les 3 langues et leurs chiffres concordent.
- Exacts face à l'app :
  - essai de 60 jours ;
  - Mon argent en Pro et Elite ;
  - tout le jeu (gels, missions, boss, parcours, Edge Reveal, saisons, crews, rangs) ;
  - conditions du parrainage pour le parrain ;
  - checklist de 13 questions ;
  - graphiques CME (14 contrats, de 15 s à 1 h) ;
  - imports CSV ;
  - add-on NinjaTrader 8 ;
  - 6 firmes préremplies vérifiées chaque semaine ;
  - export et suppression ;
  - raccourcis clavier.

## Ordre proposé

1. **Étape 1** d'abord : faits faux et textes légaux, sans attendre les 5 décisions (les points qui en dépendent restent tels quels).
2. **Étape 3**, que je peux faire seul et en un lot : textes et traductions.
3. **Étape 2** : présenter le coach et « Ton edge », la plus grosse valeur pour l'inscription.
4. **Étape 4** : visuel et technique.
5. **Étape 5**, dès que les captures arrivent.
