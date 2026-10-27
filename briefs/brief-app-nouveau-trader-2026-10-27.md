# Brief pour la session App : accompagner un nouveau trader dès la première heure (27 oct. 2026)

**De** : la session stratégie et tests. **Pour** : la session d'exécution.

**Demande de Mateo (27 oct.)** : « trouver des choses à simplifier, améliorer et accompagner le plus possible un nouveau trader ».

**Place dans l'ordre** : après `brief-app-boucle-quotidienne-2026-10-27.md` (fait jusqu'à l'étape 3), avant les étapes C à F de `brief-app-activation-2026-10-27.md`. L'étape 1 ci-dessous est un lot de petites corrections ; elle peut passer tout de suite.

Les règles de travail restent les mêmes : une étape à la fois, la suite complète à 0 échec, la CI verte, `CONTEXTE-APP.md` à jour, EN / FR / ES, 390 et 1300, et aucun déploiement sans l'accord de Mateo.

---

## Le tour (27 oct., `main` à `8df8fe0`)

- **Le trader** : Léa, téléphone 390 px, français, « Moins de 6 mois », Topstep Trading Combine 50K, 10 h 05 à New York (marché ouvert).
- **Le parcours** : inscription, compte, plan du jour, un trade à la main (« Pas de capture »), Aujourd'hui, mission du jour, « Fermer ma journée », puis chaque page.
- Aucune erreur JavaScript.
- Les défauts A2 et A4 du premier tour sont corrigés : la checklist est en français et la barre du bas n'est plus sur la page de bienvenue.

**Le constat principal** : l'app dit trois choses différentes à un débutant le même jour.

| Où | Ce qu'elle dit |
|---|---|
| La mission du jour 1, « Fixe tes garde-fous » | « 1 micro-contrat », « 3 trades maximum », « fini après 2 pertes ou −2R » |
| Le plan du jour | Perte max **1 000 $** (toute la limite du compte), nombre de trades **vide** |
| La feuille de trade | **NQ** par défaut (un mini, pas un micro) ; « soit 100 points de NQ à 1 contrat » |

Un débutant qui suit l'app plutôt que la mission peut perdre 1 000 $ sur un NQ le jour 1. Pourtant la mission lui dit le contraire. **Les garde-fous de la mission doivent devenir les valeurs de l'app.**

---

## Étape 1 — Les petites corrections (un lot)

| # | Constat | Correction |
|---|---|---|
| N1 | **Page Compte : « +150 $ today »** (de l'anglais au milieu du français). | Traduire. Chercher les autres « today » non traduits dans les cartes de compte. |
| N2 | **« 1 sur 1 trades dans ton plan »** : le pluriel est faux. | Singulier et pluriel, en EN, FR et ES. |
| N3 | **Consistance « 100 % · max 55 % », barre or pleine, après un seul trade gagnant.** Pour un débutant, ça ressemble à une faute. | Sous le nombre de jours requis (ou tant que le profit est sous l'objectif), afficher « Se calcule à partir de 2 jours gagnants » en gris, sans barre or. |
| N4 | **Page Compte : le formulaire « Règles de payout » est ouvert, avec des cases vides**, sur un compte en évaluation. | Le replier par défaut tant que le compte n'est pas financé. Il reste ouvrable. |
| N5 | **Le coach dit « Rien à corriger sur ce trade. Refais exactement pareil » après le tout premier trade.** | Avant 3 trades, une phrase de débutant : « Premier trade noté. Tu as suivi ton plan : c'est ça qui compte, pas le résultat. » |
| N6 | **La mission du jour 1 demande des choses déjà faites** (« Ajoute ta firme et ton compte… Remplis tes garde-fous ») sans montrer qu'elles le sont. | Chaque action déjà faite est cochée dans la mission (règle : cochée par un geste, jamais par l'ouverture d'une page). |
| N7 | **Stats : « Profit factor », « Session »** en anglais dans l'interface française ; « Pas encore de perte » sous Profit factor. | Traduire (« Facteur de profit », « Séance ») avec une ligne d'explication en « i ». |
| N8 | **L'aide n'a pas pu s'ouvrir dans le tour** (`SweepGuide.open()` n'a rien affiché). | À vérifier : si c'est un vrai défaut, le corriger ; sinon, rien à faire. |

**Fini quand** : le tour refait ne montre aucun de ces 8 points, en EN, FR et ES.

---

## Étape 2 — Les garde-fous du débutant deviennent les valeurs de l'app

Pour un trader « Moins de 6 mois », pendant le premier mois (semaine 1 à 4 du parcours de 90 jours) :

1. **Le plan du jour est prérempli avec les règles de la mission.**
   - Nombre max de trades : **3**.
   - Perte max du jour : **la moitié de la limite du compte** (500 $ sur un 50K), avec la phrase « Commence petit : tu pourras la monter. » (C'est le point C1 du premier tour.)
   - Le trader peut changer les deux valeurs. Ce qu'il choisit est gardé pour les jours suivants.
2. **La feuille de trade propose le micro du contrat habituel** (MNQ plutôt que NQ). Si le trader choisit un mini, une ligne grise : « Ta règle ce mois-ci : 1 micro-contrat. » Pas de blocage.
3. **La mission et le plan disent la même chose.** La règle « fini après 2 pertes ou −2R » devient « fini après 2 pertes ou ta perte max du jour ». « Maintenant » montre déjà ce qui reste, donc le débutant n'a pas à calculer un R.
4. **« Maintenant » annonce l'arrêt.** Après la 2e perte ou au nombre max de trades : « Fini pour aujourd'hui, c'était ta règle. Fermer ma journée ». C'est le même bouton que le soir.

Les comptes existants et les traders « 6 mois et plus » ne changent pas.

**Fini quand** :
- un débutant neuf, sans rien taper, a un plan à 3 trades et 500 $, et un trade proposé sur MNQ ;
- la mission du jour 1 et le plan affichent les mêmes nombres ;
- après 2 pertes, « Maintenant » propose de fermer la journée ;
- un trader « Plus d'un an » voit exactement ce qu'il voyait avant.

---

## Étape 3 — Chaque mot de trading s'explique là où il s'affiche

La règle existe déjà (« chaque terme s'explique là où il s'affiche »), mais le tour en trouve encore sans explication sur le chemin du premier jour :

| Où | Termes |
|---|---|
| Bienvenue / compte | Drawdown, payout, « coussin », « Option du compte financé Standard / Consistance », « option de limite journalière » |
| Plan du jour | Biais, Marge de drawdown |
| Feuille de trade | Les setups (Liquidity sweep, Break & retest, Opening range, VWAP reclaim, Fair value gap…), « R » |
| Page Compte | Consistance, Pire recul, Profit factor |

**Ce qu'il faut faire** :
- Un « i » discret, ou une ligne grise sous le terme, avec une phrase simple dans la langue du trader. Exemple pour Biais : « Ce que tu penses que le marché va faire aujourd'hui : monter (Long), descendre (Short), ou tu ne sais pas (Neutre). »
- Les setups gardent leur nom anglais (c'est le vocabulaire des traders), avec une phrase en touchant longtemps ou en « i ».
- **À l'étape « Ton compte », pour un débutant en évaluation**, le choix « Option du compte financé » et l'interrupteur « option de limite journalière » passent dans « Plus d'options ». Le compte se crée avec les valeurs par défaut de la firme. Ces choix servent seulement au passage en financé.

**Fini quand** : sur le chemin du jour 1 (bienvenue, compte, plan, trade, Aujourd'hui, Compte), chaque terme de la liste a son explication, en EN, FR et ES.

---

## Étape 4 — Stats : une page qui accompagne au lieu d'une page vide

Avec 1 trade, Stats fait 3 941 px sur téléphone, avec une dizaine de tuiles « Pas assez de données » ou « Dès 5 trades ».

**Ce qu'il faut faire** :
- **Sous 5 trades** : en haut, une seule carte « Tes stats arrivent : 1 trade sur 5 », avec une barre de progression et ce qui se débloque à 5 (ta force, ta fuite), puis à 10 (score de performance). En dessous : P&L, taux de réussite, et le calendrier.
- Les tuiles vides sont cachées tant qu'elles n'ont pas de données. Elles apparaissent quand elles en ont.

**Fini quand** : un trader avec 1 trade voit une page Stats de moins de 2 écrans sur téléphone, sans aucune tuile vide. Avec 20 trades, la page est la même qu'aujourd'hui.

---

## Hors de ce brief (noté pour plus tard)

- « Graphique disponible mercredi 22 h 00 » sur la page d'un trade du jour : c'est juste, mais ça sonne comme une panne. À reformuler dans le lot « pages longues » (activation F).
- La feuille de trade commence par « le P&L de ta plateforme » sous le titre. C'est à revoir avec le lot capture.

---

## Revue des étapes 1 et 2 (session stratégie et tests, 27 oct., `d43254e`, CI verte)

Tour refait avec Léa (« Moins de 6 mois », Topstep 50K, téléphone, français), sur une base neuve. Aucune erreur JavaScript.

**Étape 1 : validée.** « +30 $ aujourd'hui », la consistance « se calcule à partir de 2 jours gagnants » sans barre or, « Règles de payout » replié, « La mission du jour est faite », « Facteur de profit », plus d'anglais dans Stats, et l'aide s'ouvre (N8 n'était pas un défaut).

**Étape 2 : une correction avant de la dire finie.**

| # | Constat | Correction |
|---|---|---|
| R1 | **Topstep n'a pas de limite du jour** (l'étape « Ton compte » affiche « Perte du jour : aucune »). La moitié de la limite du jour ne s'applique donc pas, et le plan du débutant reste à **1 000 $**, soit la moitié de toute sa marge de drawdown (2 000 $) en une journée. `e2e_rookie` ne le voit pas, parce que son compte Topstep a une limite du jour inventée (`dll_c: 100000`). | Sans limite du jour : **le quart de la marge de drawdown** (500 $ sur un 50K), avec la même phrase « Commence petit ». `e2e_rookie` : le compte de test reprend les vraies règles du préréglage Topstep (sans limite du jour), et on ajoute un cas avec une limite du jour. |

Le micro proposé (MNQ), les 3 trades et la mission (« ta perte max du jour ») sont bons. L'arrêt après 2 pertes est couvert par `e2e_rookie`. Le tour ne l'a pas revu, parce qu'il a été fait après la fermeture (voir R2).

**Pour l'étape D du brief d'activation (première visite selon le moment).** Après la fermeture (tour fait à 16 h 45, heure de New York), le plan de l'inscription est enregistré pour le lendemain (« Plan du jour mercredi 28 octobre »). Mais « Enregistrer et ajouter mon trade » enregistre le trade aujourd'hui, et le coach répond aussitôt « À améliorer : pas de plan pour cette séance ». **(R2)** Un trader qui s'inscrit le soir pour noter sa journée se fait donc reprocher, dès son premier trade, de ne pas avoir fait un plan qu'il vient de faire. Le soir, la première visite doit commencer par le trade du jour, puis le plan de demain, et le coach ne doit pas reprocher l'absence de plan le jour de l'inscription.
