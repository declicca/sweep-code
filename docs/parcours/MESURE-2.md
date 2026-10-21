# Mesure 2 — après l'étape 2 (saisie sans capture, plan express par défaut)

21 oct., en local, avec le même outil et le même parcours que `MESURE-0.md` (`app/tools/parcours-baseline.py`, Topstep 50K, téléphone 390 FR et ordinateur 1300 EN). Le nouveau chemin est « Pas de capture ? Entre ton P&L ».

| Cas | Jusqu'au risque permis | Jusqu'au premier trade | Écrans | Temps humain estimé (trade) |
|---|---|---|---|---|
| Départ (MESURE-0), sans capture (« Saisir à la main ») | 11 touchers · 3 champs | 16 touchers · 5 champs | 5 | ~65 s |
| **Étape 2, « Pas de capture ? Entre ton P&L »** | 11 · 3 | **14 touchers · 4 champs** | **4** | **~55 s** |
| Étape 2, avec capture (inchangé) | 11 · 3 | 16 · 4 | 5 | ~60 s |
| Étape 2, « Saisir à la main » (inchangé) | 11 · 3 | 16 · 5 | 5 | ~65 s |

Chiffres identiques au téléphone et à l'ordinateur.

**Ce qui fait la différence** : le P&L reçoit le focus au toucher, donc il n'y a pas de champ à toucher, et la saisie se fait sans aucun prix d'entrée ni de sortie.

**Critère de l'étape 2** (« 4 écrans et 14 touchers au plus, sans champ de prix ») : **atteint**.

Le plan du premier jour ne change pas : c'est le plan court, 2 touchers. Le plan express par défaut joue à partir du plan suivant, et ne se mesure pas dans M1.

Résultats bruts : `mesure-2-local.json`.

Les chiffres en ligne (Admin › Métriques) se comparent après le déploiement de l'étape 2. Celui-ci attend une semaine de mesures de l'étape 0 en ligne (décision de Mateo du 21 oct.).
