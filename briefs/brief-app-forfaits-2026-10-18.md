# Brief pour la session App : les forfaits, vus du site (18 oct. 2026)

Mateo a donné carte blanche le 18 oct. : « pour les plans et forfaits je te laisse définir les plans selon ce qui est mieux au niveau marketing […] optimal pour la conversion du client et pensé pour qu'il upgrade subtilement ».

Travaille en autonomie : ne demande pas de validation étape par étape. Livre une seule fois, avec les tests, puis demande une seule fois l'accord pour déployer.

## Décision

**Prix et règles inchangés.** Les règles sont déjà bien construites : Free bloque exactement au moment où le trader grandit (3ᵉ compte, premier payout, plus de 30 jours d'historique, 4ᵉ capture du jour), et l'app a déjà les messages de ces moments (`h_add_account`, `h_payouts_n`, `h_analytics_history`, `h_shot_quota`).

Ce qui freinait la conversion, c'était la présentation :
- des quantités floues (« Limité / Plus / Le plus », « quota de base / élargi / maximal ») ;
- 22 lignes au même niveau, où le jeu noyait l'essentiel ;
- un Elite vendu par ses gels de streak et ses boss ;
- l'offre fondateur affichée à des visiteurs qui ne peuvent pas l'avoir.

Le site est refait dans ce sens (`website/src/pages6.py`, `page_pricing`).

## Ce que le site affiche maintenant (limites publiques)

| | Free | Pro | Elite |
|---|---|---|---|
| Comptes prop | 2 | Illimité | Illimité |
| Historique des stats | 30 derniers jours | Complet | Complet |
| Mon argent | — | ✓ | ✓ |
| Messages Sweep AI | 3 par jour | 50 par jour | 200 par jour |
| Trades lus depuis une capture | 3 par jour | Illimité | Illimité |
| Avis IA sur un trade | — | 3 par mois | Chaque trade |
| Notes du calendrier | Titres | Titres | Notes complètes |
| Rapport IA de la semaine | — | — | ✓ |
| Soutien prioritaire | — | — | ✓ |

Le jeu reste dans le tableau, regroupé en dernier.

**À vérifier par Mateo** (`sweep-private/billing-config.php`, que personne d'autre ne lit) : `plans.free.accounts` = 2 et `plans.pro.accounts` = `null` (illimité). L'app le dit déjà (« Pro has no limit », « Unlimited trading accounts »), mais la configuration de test (`tools/billing-config.local.php`, `ops/tests.php`) a encore `pro.accounts` = 5 : à mettre à `null` pour que les tests suivent la règle.

## La page des forfaits de l'app : mêmes mots que le site

Le trader doit retrouver dans l'app ce qu'il a lu sur le site.

1. **Une phrase par forfait** (remplace `free_desc` et les sous-titres actuels) :
   - Free : EN « To build the habit on your first accounts. » · FR « Pour bâtir l'habitude sur tes premiers comptes. » · ES « Para crear el hábito con tus primeras cuentas. »
   - Pro : EN « For traders running several prop accounts. » · FR « Pour les traders qui gèrent plusieurs comptes prop. » · ES « Para traders con varias cuentas prop. »
   - Elite : EN « For an AI review on every trade and a report every week. » · FR « Pour un avis de l'IA sur chaque trade et un rapport chaque semaine. » · ES « Para una opinión de la IA en cada operación y un informe cada semana. »
2. **Le tableau de comparaison** : mêmes lignes et même ordre que ci-dessus, avec les vrais chiffres lus dans la configuration (`f_accounts`, `f_history`, `f_ai_daily`…) et une ligne pour les captures (« 3 par jour » / « Illimité »).
3. **Le prix annuel** : le prix mensuel barré à côté du prix annuel ramené au mois (« ~~19 $~~ 13,25 $/mois »), et l'économie en dollars (« 69 $ d'économie », « 139 $ » pour Elite) plutôt qu'en pourcentage seulement.
4. **Pendant l'essai** : le bouton de Pro dit « Garder Pro » ; la ligne sous le bouton rappelle qu'à la fin de l'essai, on passe à Free tout seul, sans rien payer (déjà dans `trial_next`).
5. **Les trois raisons de passer à Pro** (même texte que le site, section « Pourquoi les traders passent à Pro ») peuvent servir de texte aux fenêtres de mise à niveau qui n'ont pas de chiffre du trader :
   - « Tous tes comptes, au même endroit » : Free suit 2 comptes. Quand tu grandis, Pro les suit tous, chacun avec les règles de sa firme.
   - « Ton vrai net » : les payouts d'un côté ; les évaluations, les resets et les frais de l'autre. Mon argent montre ce que le trading te rapporte vraiment.
   - « Tout ton historique » : Free montre tes 30 derniers jours. Chaque trade plus ancien reste gardé, et Pro le remet dans tes stats.

   EN et ES : reprendre les textes de `website/src/pages6.py`, liste `why`.

## Ce qui ne change pas

- Les prix (Pro 19 $ / 159 $, Elite 39 $ / 329 $), l'essai de 60 jours, le parrainage (14 jours d'Elite), Stripe.
- L'offre fondateur (50 % à vie pour les inscrits de l'accès anticipé, jusqu'au 1er déc.) reste dans l'app, avec son compte à rebours. Le site ne l'affiche plus sur la page Tarifs : un nouveau visiteur ne peut pas l'avoir.
