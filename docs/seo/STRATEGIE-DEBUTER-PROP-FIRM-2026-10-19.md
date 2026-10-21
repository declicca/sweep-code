# Stratégie SEO : « débuter en prop firm » et le plan de 90 jours (19 oct. 2026)

Source : les trois PDF « Sweep 90-Day Gameplan » de Mateo (mois 1, 2 et 3, en anglais).

Objectif : faire de makeitsweep.com la réponse de référence pour un trader qui veut commencer en prop firm, sur Google et dans les réponses des IA. Le chemin visé : un trader trouve le plan, le suit avec Sweep, puis passe à Pro quand il gère plusieurs comptes.

## 1. Les intentions de recherche visées

| Intention | Requêtes types (EN) | FR | ES | Page |
|---|---|---|---|---|
| Débuter | how to start prop firm trading, best way to start prop firm trading, prop firm trading for beginners, futures prop firm beginner | comment commencer en prop firm, débuter le trading en prop firm | cómo empezar en prop firms, prop firm para principiantes | `/how-to-start-prop-firm-trading` (pilier) |
| Plan concret | prop firm trading plan, 90 day trading plan, futures trading plan for beginners | plan de trading prop firm, plan de 90 jours | plan de trading prop firm, plan de 90 días | les 3 pages mensuelles |
| Gestion du risque débutant | prop firm risk management, daily loss limit strategy, how many trades per day prop firm | gestion du risque prop firm | gestión del riesgo prop firm | mois 1 (garde-fous) |
| Méthode et données | how to find your edge trading, trading journal tags, how to review trades | trouver son edge, étiqueter ses trades | encontrar tu ventaja, etiquetar operaciones | mois 2 |
| Évaluation et compte financé | how to pass a prop firm evaluation, when to size up prop firm, funded account rules after passing | réussir une évaluation prop firm, augmenter sa taille | aprobar una evaluación prop firm | mois 3, puis phase 2 |

Pas d'outil de volumes de recherche dans cette session : les requêtes viennent des formulations courantes des traders et des pages qui se classent déjà sur ces sujets. Les vrais volumes se liront dans la Search Console après la mise en ligne (section 5).

## 2. Architecture : un pilier, trois mois, puis des pages satellites

- **Pilier** : `/how-to-start-prop-firm-trading`.
  - Contenu : le pourquoi, le fonctionnement, les deux parcours, ce qu'il faut, les trois portes et une FAQ (données `FAQPage`).
  - Fil d'Ariane : Accueil › Guides › Débuter en prop firm.
- **Les trois mois**, une page chacun, toutes les missions dans les 3 langues :
  - `/prop-firm-gameplan-month-1` : les garde-fous, le Sweep Setup, l'aide-mémoire MES/MNQ, la routine, le vocabulaire, 30 missions, le journal, la porte.
  - `/prop-firm-gameplan-month-2` : garde-fous v2, étiquettes, tendances, le seul ajustement, 30 missions, journal v2, la porte.
  - `/prop-firm-gameplan-month-3` : garde-fous v3, échelle de taille, plan d'évaluation, playbook de compte financé, 30 missions, plan d'une page, la porte finale.
  - Chaque mois a la navigation entre les mois, un sommaire collant, les données `Article` (`isPartOf` vers le pilier) et le fil d'Ariane : Accueil › Débuter en prop firm › Mois n.
- **Maillage interne** :
  - le menu Ressources (en premier) et le pied de page (Ressources, en premier) ;
  - le hub Guides : une rangée « Débuter en prop firm » en tête, et « Nouveau dans les prop firms ? » qui pointe vers le plan ;
  - `llms.txt` ;
  - les pages du plan pointent vers le calculateur de taille de position, les fiches contrats, les pages des prop firms, les modèles gratuits et Mon argent.
- **Satellites** (phase 2) : des pages courtes sur une seule requête, qui renvoient au mois concerné.

## 3. Ce qui est fait (phase 1, 19 oct.)

- `website/src/pages21.py` : le pilier et les 3 mois, en EN, FR et ES (12 pages).
- Inscription dans le build, le plan du site (priorité 0,9 pour le pilier, 0,8 pour les mois), le fil d'Ariane, « À lire aussi », le menu, le pied de page, le hub Guides et `llms.txt`.
- Le menu Ressources garde 8 entrées sur ordinateur : « Nouveautés » en sort (il reste dans le pied de page et le menu du téléphone).
- Choix de contenu :
  - **Aucune vérification automatique annoncée.** Les PDF marquent des missions « Sweep · auto », mais l'app n'a pas encore d'écran du plan. Le site garde chaque « C'est fait quand » sans dire que Sweep le vérifie.
  - **Incohérence des PDF corrigée sur le site.** Le PDF du mois 1 dit que le parcours A peut acheter une évaluation après la porte du mois 1 ; ceux des mois 2 et 3 disent qu'il reste en simulation jusqu'au mois 3. Le site suit les mois 2 et 3 : une évaluation devient une option au mois 3.
  - **Les noms des badges de la semaine ne sont pas repris** : ils n'existent pas dans l'app.
  - **Un avertissement éducatif sur chaque page** (risque, outil d'apprentissage, règles officielles de la firme).
- **Les PDF ne sont pas en téléchargement** : ils sont en anglais seulement et annoncent la vérification automatique. Voir la section 6.

## 4. Phase 2 : les pages satellites (faites et en local le 19 oct.)

Faites dans `pages21.py`, dans les 3 langues :
- les 5 pages du tableau ci-dessous ;
- leurs images de partage ;
- 3 termes au lexique (PDH / PDL, liquidity sweep, échelle de taille), chacun relié à sa page ;
- une rangée « Une question à la fois » sur le pilier ;
- des liens depuis les mois 1 et 3.

Le tableau de `/pass-prop-firm-evaluation` se calcule à partir du catalogue de l'app : objectif en R et mauvaises journées absorbables, pour chaque type de compte de 50K. Il suit donc la vérification hebdomadaire. Les schémas du sweep sont dessinés par le build en SVG, sans capture de plateforme.

Aussi : un lien vers le pilier depuis le guide du journal, le journal gratuit, la page Routine et les modèles.

| Page | Requête principale | Angle | Renvoie vers |
|---|---|---|---|
| `/pass-prop-firm-evaluation` | how to pass a prop firm evaluation | le plan d'évaluation en R : objectif en R, plafond du jour tiré de la consistance, mauvaises journées absorbables, délai après un échec ; exemples chiffrés par firme, tirés des règles vérifiées chaque semaine | mois 3, pages des firmes, calculateurs |
| `/prop-firm-position-sizing` | when to size up prop firm account | l'échelle de taille : quand monter, quand redescendre, et pourquoi le drawdown doit contenir 2 journées de stop | mois 3, calculateur de taille |
| `/funded-account-playbook` | what to do after passing prop firm evaluation | les 5 règles du compte financé, la règle de payout, le vrai net | mois 3, Mon argent, règles de payout |
| `/liquidity-sweep` (le 20 oct., ancien `/liquidity-sweep-setup`, redirigé) | liquidity sweep, liquidity sweep strategy, PDH PDL strategy | le Sweep Setup en détail, avec des schémas (SVG faits par le build, pas de captures de plateforme) et les cas à passer | mois 1 |
| `/mes-vs-mnq` | MES vs MNQ for beginners | valeurs de tick et de point, le même stop en dollars sur chacun, pourquoi commencer avec 1 micro | mois 1, fiches contrats |



## 5. Mesure

- **Search Console** : les requêtes et les clics des 4 pages, à 4 puis 8 semaines. On ajoute une page satellite quand une requête obtient des impressions sans clic.
- **Inscriptions** : chaque bouton d'inscription porte sa page dans son adresse (`utm_source=site&utm_medium=<page>`, par exemple `prop-firm-gameplan-month-1`). L'app ne les enregistre pas encore pour un visiteur venu de Google : le correctif est demandé à la session App (`briefs/brief-app-attribution-site-2026-10-21.md`), puis le décompte par page se lira dans Admin › Attribution. Les attributs `data-track` des boutons ne sont lus par aucun outil de mesure : le site n'en charge aucun.
- **IA** : vérifier tous les mois si les réponses de ChatGPT, Perplexity et Google citent le pilier pour « how to start prop firm trading ».

## 6. Pour aller plus loin

1. **Le plan dans l'app : fait le 20 oct.** (`54f4228` dans l'app, Pro et Elite).
   - Le site marque « Sweep · auto » les 35 missions que l'app coche seule. Elles sont calculées comme dans l'app : les missions 1, 2 et 52, puis les « C'est fait quand » « séance notée », « zéro écart » et « bilan de la semaine ».
   - Une légende explique la marque sur chaque mois.
   - Un bandeau « Fais ce plan dans Sweep » est sur le pilier et sur les 3 mois.
   - Une question est dans la FAQ du pilier.
   - Le parcours est dans Pro sur la page Tarifs.
2. **Les PDF** : leurs marques « Sweep · auto » ne correspondent pas aux 35 de l'app. Par exemple, le jour 7 est marqué automatique dans le PDF, mais pas dans l'app. Donc :
   - soit les PDF sont refaits à partir des pages (en EN, FR et ES, avec les mêmes marques que l'app) ;
   - soit on garde les pages comme seule version.
