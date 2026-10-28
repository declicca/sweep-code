# MESURE-BOUCLE — la journée d'un trader actuel, en touchers

Brief : `briefs/brief-app-boucle-quotidienne-2026-10-27.md`. Cible : **une journée à 2 trades en 15 touchers au plus**, sans champ de prix, sans quitter Aujourd'hui.

**Comment on mesure** : `app/tools/parcours-baseline.py`, cas « journée d'un trader actuel » (`BASELINE_PATHS=day`), en local, téléphone 390 FR et ordinateur 1300 EN (mêmes chiffres). Un nouveau trader avec un vrai compte (Topstep 50K) et 10 trades passés ; puis le plan, 2 trades par capture, fermer la journée. Les deux captures sont de vraies captures d'un trade (`tests/samples/shot-topstepx-one-trade.png`, `shot-tradesea-one-trade.png`), lues par les réponses de test de Sweep AI ; leurs trades sont remis sur le jour.

| Date (27 oct.) | Commit | Plan | 2 trades | Fermer la journée | **Journée** | Champs | Écrans |
|---|---|---|---|---|---|---|---|
| Départ (mesure de la session stratégie, sur `main` du 27 oct.) | `995c6a0` | 16 | 7 + 7 | 5 | **≈ 35** | ≈ 10 | ≈ 13 |
| Étape 1 : plan express pour tous | `34d630a` | 6 | 6 + 6 | 5 | **23** | 4 | 7 |
| Étape 2 : plus de feuille après un trade | `f679f2c` | 6 | 4 + 4 | 5 | **19** | 2 | 7 |
| Étape 3 : « Fermer ma journée » | `a964323` | 6 | 4 + 4 | 2 | **16** | 2 | 7 |
| 28 oct. — Pertes oubliées, étape 2 : « Ton solde sur Topstep ? » | `1a73d77` | 6 | 4 + 4 | 3 | **17** | 2 | 7 |

**À savoir**
- La ligne de l'étape 1 a été mesurée avec une image que les réponses de test ne lisent pas (`tests/fixture-shot.png`) : le P&L et le sens y sont tapés à la main (6 touchers par trade). Avec une capture lue, la même étape donne 5 touchers par trade (la feuille « quel scénario ? » en plus). Les lignes suivantes utilisent les vraies captures.
- L'étape 4 (« Maintenant ») est en ligne depuis `ba82619`, avant ces mesures : elle ne change pas le nombre de touchers de ce cas.
- Il reste 1 toucher pour la cible de 15. Le plan express compte 6 touchers (biais, instrument, niveaux, scénario, Continuer, Enregistrer).
