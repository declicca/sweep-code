# Brief pour la session App : la journée d'un trader actuel en deux fois moins de gestes (27 oct. 2026)

**De** : la session stratégie et tests. **Pour** : la session d'exécution.

**Priorité de Mateo (27 oct.)** : « on commence à avoir plusieurs utilisateurs et je veux les garder ; la meilleure expérience, la plus simple ». Ce brief passe **avant** les étapes C à F de `brief-app-activation-2026-10-27.md`. L'étape A de ce brief-là (les défauts qui font perdre un trade) reste la toute première chose à faire.

Les règles de travail sont celles du brief d'activation : une étape à la fois, la suite complète à 0 échec, la CI verte, `CONTEXTE-APP.md` à jour, EN / FR / ES, 390 et 1300, et aucun déploiement sans l'accord de Mateo.

---

## Le point de départ, mesuré le 27 oct.

Mesure sur `main`, en local, sur téléphone, en vrais touchers. Le trader a déjà un vrai compte (Topstep 50K) et 10 trades.

| Geste | Touchers | Champs | Écrans | Ce qui coûte |
|---|---|---|---|---|
| Le plan du jour | 16 | 7 | 7 | Le pré-marché guidé s'ouvre par défaut (London high et low, PDH et PDL, prix, scénarios). |
| Un trade par capture | 7 | 1 | 2 | Après « Enregistrer », la feuille « Ce trade, c'est quel scénario de ta fiche ? (A, B, Hors fiche) » s'ouvre **à chaque trade**. |
| Un trade à la main | 7 | 2 | 3 | La même feuille, puis l'app part sur la page du trade, alors que la capture revient sur Aujourd'hui. |
| Fermer la journée (la revue) | 5 | 0 | 1 | 3 réponses obligatoires, puis « Enregistrer ». |
| **Une journée à 2 trades** | **≈ 35** | **≈ 10** | **≈ 13** | |

**Cible** : **une journée à 2 trades en 15 touchers au plus, sans champ de prix, sans quitter Aujourd'hui.**

**Mesure** : `app/tools/parcours-baseline.py` reçoit un cas « journée d'un trader actuel » (plan, 2 trades, fermer la journée). Il est refait après chaque étape et noté dans `docs/parcours/MESURE-BOUCLE.md`.

---

## Étape 1 — Le plan en 30 secondes pour tous

**C'est l'étape 2 de `SWEEP.md`**, déjà faite et testée sur la branche locale `parcours-3b` (commit `14176c9`, l'étape 2 rebasée) :
- le plan express par défaut pour qui n'a jamais choisi le guidé ;
- « Pas de capture ? Entre ton P&L » dans la feuille « + ».

Elle attendait la fin de la semaine de mesure de l'étape 0 : **le mardi 28 octobre à 20 h 17 (heure de New York)**.

**À faire** : la livrer seule, sans les lots de l'étape 3. Il faut donc la séparer de `parcours-3b`, sur une branche partie de `main`, puis faire tourner la suite complète. **Ajouter** : un trader qui a déjà enregistré des fiches guidées, mais n'en a pas fait depuis 10 séances, se voit aussi proposer l'express. Un toucher : « Garder le plan guidé ».

**Fini quand** : le plan d'un trader actuel prend **6 touchers au plus** (express), et le guidé reste à un toucher pour qui le veut.

---

## Étape 2 — Un trade, puis on continue (plus d'interruption après chaque trade)

1. **La feuille « quel scénario ? » ne s'ouvre plus après le trade.** Le lien avec la fiche se fait tout seul quand il n'y a pas de doute :
   - un seul scénario dans le sens du trade (A long, B short) : lien automatique ;
   - les deux dans le même sens, ou un trade hors des deux : une rangée de puces « Scénario A · B · Hors fiche » **dans le formulaire**, au-dessus d'« Enregistrer » ;
   - sans réponse : « Hors fiche », comme aujourd'hui avec « Plus tard ».

   Code concerné : `SweepFiche.markTrade`, dans `src/game.js`, appelé depuis `tkSave` et `saveOne`.
2. **Après un trade à la main, on reste sur Aujourd'hui**, comme après une capture : le message « Trade enregistré · {le coach} » avec un lien « Voir le trade ». Aujourd'hui, l'app ouvre la page du trade.
3. **« 1 trades sur 2 »** : le pluriel dans les phrases du coach (`src/coach.js`, `lMix` et voisines), en EN, FR et ES.

**Tests** : `e2e_premarket_session` (le lien automatique, les puces), `e2e_trade_form` (retour à Aujourd'hui) et `e2e_coach` (singulier et pluriel).

**Fini quand** : un trade par capture prend 5 touchers au plus, un trade sans capture 4 (étape 1), et aucune feuille ne s'ouvre après « Enregistrer ».

---

## Étape 3 — Fermer la journée en un toucher

**C'est l'étape 4 de `SWEEP.md`**, avancée pour les traders actuels :
- la revue s'ouvre **pré-remplie** par ce que Sweep sait : le plan ou la fiche suivi d'après la conformité du jour, la discipline d'après le score du coach, une note proposée, et les règles enfreintes déjà pré-cochées ;
- un seul bouton : **« Fermer ma journée »** ;
- chaque réponse se change d'un toucher avant de fermer ;
- un lien « J'ai fini pour aujourd'hui » sous l'étape Exécution, dès le premier trade, la propose tout de suite.

**Tests** : `e2e_close_day` (nouveau : 3 journées types, une propre, une de tilt, une sans plan, avec des réponses pré-remplies justes), puis `e2e_routine_parity`, `e2e_premarket_post` et `e2e_coach`.

**Fini quand** : une journée se ferme en **2 touchers** (ouvrir, fermer) et les réponses pré-remplies sont justes sur les 3 journées types.

---

## Étape 4 — « Maintenant » (l'étape 3 de SWEEP.md)

Tout est dans `SWEEP.md`, section 7, « Relais vers la session d'exécution », et l'étape B du brief d'activation. Elle passe ici après « Fermer ma journée », parce que les deux se partagent la carte de la routine.

---

## Ce qui reste après

L'étape A du brief d'activation (les défauts) passe **avant** tout ce brief.

Ensuite, dans l'ordre :
1. les mesures et la première visite (brief d'activation, étapes C, D, E) ;
2. les pages longues (étape F) ;
3. les étapes 5 et 6 de SWEEP.md.

**Le résultat attendu** : une journée à 2 trades passe d'environ **35 touchers à 15**, sans champ de prix, sans quitter Aujourd'hui, et sans fenêtre qui s'ouvre toute seule.
