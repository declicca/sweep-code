# Tour du 31 oct. 2026 : navigation, compréhension, utilisation (pour la session App)

**Demande de Mateo (31 oct.)** : « Refais le tour complet pour simplifier et améliorer la navigation, compréhension et utilisation de l'app. Le but c'est que ce soit simple, intuitif et naturel. »

Version testée : `1e47629` (W1 à W5 du 30 oct. compris), **en pleine séance** (vendredi 30 oct., 10 h 15 à New York, `SWEEP_GAME_NOW` et `tools/clientclock`).

Deux traders :
- Léa, débutante, en français sur téléphone : inscription, compte Topstep 50K, plan, 3 trades sans capture, puis chaque page ;
- Alex, avec les données d'exemple, en anglais sur ordinateur et téléphone.

Aucune erreur JavaScript.

**Vérifié et bon** : W1 à W5 ; le plan du débutant à 500 $ et 3 trades ; « Maintenant » ; le coach du premier trade ; Réglages tous repliés ; Stats sous 5 trades.

Le cadre ne change pas : une évolution, pas de refonte, pas de nouvelle fonction. Tout texte en EN, FR et ES ; 390 et 1300 ; clair et foncé.

---

## A — Naviguer

| # | Où | Défaut | Correction |
|---|---|---|---|
| A1 | Comptes et Mon argent | Tant que la mission « Mon argent » n'est pas faite, l'onglet « Mon argent » est caché (`body.disc-no-money`). Il reste alors **une barre d'onglets avec un seul onglet, « Comptes »**, même sur la page Mon argent ouverte par un lien. | Une barre d'onglets à un seul onglet ne s'affiche pas. Sur la page Mon argent, les deux onglets s'affichent toujours. |
| A2 | Ordinateur, barre latérale | **Des icônes sans nom** (Aujourd'hui, Trades, Stats, Comptes), alors que le téléphone a les noms sous les icônes. Il faut survoler pour savoir où on va. | Le nom à côté de chaque icône dès 1100 px de large, comme la barre latérale d'iPad. En dessous, les icônes seules, comme aujourd'hui. |
| A3 | Ordinateur, Aujourd'hui | **Trois boutons « Ajouter un trade » sur le même écran** : le « + » de la barre latérale, « Add a trade » en haut à droite, et « Add a trade › » dans l'étape Exécution. | On retire le bouton du haut à droite d'Aujourd'hui. Le « + » (touche N) et l'étape Exécution suffisent. |
| A4 | Page d'un compte | **Tous les trades du compte** (28 dans l'exemple, 2 000 px sur téléphone). Leurs lignes disent encore « session of Oct 23 · entered … » au lieu de l'heure et du setup (le T5 du 29 oct. corrigé sur Aujourd'hui seulement). | Les 5 derniers trades, puis « Voir ses 28 trades › » qui ouvre Trades filtré sur ce compte. La ligne d'un trade est la même partout : l'heure, puis le setup. |

## B — Comprendre

| # | Où | Défaut | Correction |
|---|---|---|---|
| B1 | Calendrier, bande des jours d'Aujourd'hui | **Des points or sans légende.** Ce sont les annonces économiques fortes, expliquées seulement au survol (rien sur téléphone). Mais l'or est la couleur des pertes : un débutant lit « jours perdants ». | Des points gris (`--muted`), et une ligne de légende sous le calendrier : « • Annonce économique forte ». Un toucher sur un jour montre déjà ses annonces. |
| B2 | Aujourd'hui, Stats | **La pastille « Performance » à côté de « P&L net ».** Personne ne sait ce qu'elle veut dire. | On retire la pastille. Le « i » de « P&L net » dit : « Ton habileté, pas de l'argent gagné : l'argent réel est dans Mon argent. » (le texte existe déjà, `ux.js`, `note`). |
| B3 | Plan, Journal, coach | **Deux mots pour le même biais.** Le plan dit « Long / Short », alors que le Journal dit « Plan : Haussier » et que le coach dit « ton biais (haussier) ». | Les mots du plan partout : Long, Short, Neutre. |
| B4 | Journal et Aujourd'hui, le même jour | **Deux chiffres différents** : Aujourd'hui dit « 1 sur 2 trades dans ton plan », alors que le Journal dit « Dans ton plan 0 / 2 ». | Le Journal compte comme Aujourd'hui (une seule fonction). Un test : 1 trade dans le biais, 1 contre, donc « 1 / 2 » aux deux endroits. |
| B5 | Aujourd'hui, la liste des trades du jour | **« Checklist à faire » en or sur chaque trade.** L'or veut dire perte, et le rappel se répète sur toutes les lignes. | En gris, et seulement sur le dernier trade du jour sans checklist. |
| B6 | Page d'un trade, téléphone | **Le signe « − » du P&L est seul sur sa ligne**, et « $837.60 » est en dessous. | Le signe et le montant ne se coupent jamais (`white-space: nowrap`, ou le montant un peu plus petit). |

## C — Utiliser

| # | Où | Défaut | Correction |
|---|---|---|---|
| C1 | Feuille « Nouveau trade » sur téléphone | **« Colle ou dépose ta capture (Ctrl+V) »** : il n'y a pas de Ctrl+V sur un téléphone. Il y a aussi **deux chemins pour le même geste** : « Pas de capture ? Entre ton P&L » et « Saisir à la main ». Une fois dans la saisie du P&L, la zone de capture revient en haut. | Sur téléphone : « Choisir une capture », qui ouvre les photos. En dessous, un seul lien, « Sans capture › », qui ouvre la saisie du P&L. Le formulaire complet reste dans cette saisie (« + Ajouter le contexte »). « Importer un CSV » reste. La zone de capture n'apparaît pas une seconde fois. |
| C2 | Bienvenue, l'étape « Ton compte » | **Deux liens « Plus d'options »** dans la même étape : un sous la firme, un sous le nom du compte. | Un seul « Plus d'options », qui contient les deux. |
| C3 | Feuille de trade, le coach | Un trader qui note ses trades après coup lit : **« Ta dernière perte date de 0 min : attends encore 10 min avant d'entrer. »** | Le délai d'attente seulement si le trade est noté pendant la séance, sans heure tapée. Le texte dit « à l'instant » au lieu de « 0 min ». |
| C4 | Données d'exemple | **Elles contredisent l'app** : « Mission 1 sur 15 : ajoute ton compte » à côté de 5 comptes ; l'étape Exécution dit « Pas encore de trade » alors que 3 trades sont listés juste en dessous ; 4 comptes sur 5 sont « Drawdown dépassé ». | Pendant l'exemple : les missions sont cachées ; la routine compte les trades d'exemple ; un seul compte d'exemple dépasse son drawdown, les autres sont en règle. |
| C5 | Aujourd'hui, la carte de la routine | **Six blocs dans une carte** : 4 pastilles (Discipline, Jours complets, Niveau, « ? »), « Maintenant », le parcours de 90 jours, le coach, les 3 étapes, puis **deux chemins vers la revue** (« Réviser » et « J'ai fini pour aujourd'hui › »). | Les 4 pastilles deviennent une seule ligne sous le titre : « Niveau 2 · 0 jour complet › », qui ouvre Ma progression. On garde un seul chemin vers la revue : l'étape Revue. « J'ai fini pour aujourd'hui » n'apparaît qu'à l'arrêt annoncé par « Maintenant ». |

---

**Fini quand** : les 15 points ne se voient plus, en EN, FR et ES, à 390 et 1300, en clair et en foncé. `e2e_visual_fit` et la suite complète passent. Un test couvre A1 (aucune barre à un seul onglet), B4 (le même compte aux deux endroits) et C1 (un seul lien sans capture sur téléphone).
