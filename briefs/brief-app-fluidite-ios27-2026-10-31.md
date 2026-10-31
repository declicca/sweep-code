# Fluidité « iOS 27 » : boutons, défilement, passages entre les pages (31 oct. 2026, pour la session App)

**Demande de Mateo (31 oct.)** : « se concentrer sur la fluidité des boutons, scroll, interactions entre pages et fonctions pour rendre ça le plus intuitif et similaire au dernier iOS 27.2. Que ce soit fluide, que les mouvements se suivent […] minimaliste et bien clair, ultra allégé. »

Version mesurée : `82a2a6c` (les 15 points du 31 oct. compris), en pleine séance (`SWEEP_GAME_NOW` vendredi 10 h 15, `tools/clientclock`).
- Données d'exemple, en anglais.
- Téléphone 390 tactile **avec le processeur ralenti 4 fois** (un téléphone moyen), et ordinateur 1300.
- Mesures dans la page : images par seconde (rAF), tâches longues, décalages de mise en page, `document.getAnimations()`, gestes tactiles par CDP.

Aucune erreur JavaScript, aucun décalage de mise en page (CLS 0).

## Ce qui est déjà bien

- Une seule courbe (`--spring`).
- Le grand titre qui passe dans la barre du haut au défilement.
- Les feuilles : poignée, fond flouté, la page qui recule derrière, et la fermeture en glissant (plan, revue, nouveau trade, cloche, filtres).
- Le défilement à 60 images par seconde.
- Toucher l'onglet actif remonte en haut.

## Ce qui casse la fluidité

| Mesure | Aujourd'hui | iOS |
|---|---|---|
| Changer d'onglet | 8 à 34 éléments remontent en fondu (`sw-rise-m`), **environ 400 ms** avant que la page soit immobile. Ça recommence à chaque changement. | Instantané, sans animation. |
| Revenir à un onglet | **La position est perdue** : Trades descendu à 900 px, aller sur Stats, revenir : 0. | Chaque onglet garde sa position et sa page ouverte. |
| Retour en arrière | Trades à 641 px, puis un trade, puis Retour : **0**. Aujourd'hui à 700 px, puis un compte, puis Retour : **0**. | Retour exactement où on était. |
| Ouvrir un trade | La page se construit comme un onglet (les blocs remontent). **525 ms de tâches longues** sur le téléphone ralenti, plus 320 ms d'animation. | La page arrive de la droite, et la précédente glisse un peu à gauche. Retour : l'inverse. |
| Glisser depuis le bord gauche | Rien (testé sur la page d'un trade). Dans l'app installée sur l'écran d'accueil, il n'y a pas de geste de retour. | Le geste de retour, qui suit le doigt. |
| Barre d'onglets | Toujours pleine taille. | Elle se réduit quand on descend et revient quand on remonte. |
| Réaction au toucher | 8 valeurs de rétrécissement (.9 à .99), plus une opacité à .6 et une à .7 selon les éléments. Les lignes rétrécissent et changent de fond. | Deux réactions seulement : un bouton rétrécit légèrement ; une ligne s'éclaire. |
| Taille des boutons | La page d'un trade a **13 styles de bouton** et 67 cibles de moins de 40 px (des boutons de 32 px, des « i » de 16 px). Sur Aujourd'hui, les liens « Calendar › », « Journal › » et « Level… » font 19 px de haut. | 3 styles. Une zone touchable de 44 px. |
| Longueur | Stats fait **5 757 px** sur téléphone, soit 7 écrans, avec « Deep dive » (9 onglets et des tableaux). | L'essentiel sur un écran, le détail un niveau plus bas. |
| Recherche (téléphone) | La palette de l'ordinateur : une carte centrée, avec « Switch to dark theme », « Share net after fees »… | Une feuille, le champ prêt, les pages. |

---

## Lot 1 — Les mouvements (le cœur de la demande)

1. **Changer d'onglet est instantané.** Plus d'animation d'entrée (`sw-enter`, `sw-in`, `sw-rise-*`, `nav-in`) au changement d'onglet ni au retour en arrière. N'animent que les éléments qui *apparaissent* dans une page déjà affichée : un trade ajouté, un toast, une carte qui se déplie.
2. **Chaque onglet garde sa mémoire** : sa position, et la sous-page ouverte. Toucher l'onglet actif remonte en haut ; le toucher encore revient à la racine de l'onglet.
3. **Le retour en arrière remet la position exacte** (`history.scrollRestoration = 'manual'`, la position gardée par adresse, remise après le premier dessin).
4. **Aller vers une sous-page glisse** : un trade, un compte, Réglages, Quoi de neuf, Ma progression, l'analyse détaillée de Stats (voir le lot 3). La nouvelle page arrive de la droite, et la précédente part d'environ 30 % à gauche, un peu assombrie. Le retour fait l'inverse.
   - Avec `document.startViewTransition` quand le navigateur le connaît ; sinon, sans animation.
   - La courbe `--spring`, environ 350 ms.
5. **Le geste de retour dans l'app installée** (`html.pwa`) : glisser depuis le bord gauche (moins de 20 px). La page suit le doigt, revient en arrière au-delà d'un tiers ou si le geste est rapide, et reste sinon. Dans Safari, rien (Safari a déjà son geste).
6. **La barre d'onglets se réduit en descendant** (téléphone) : il ne reste que l'onglet actif et le « + ». Elle revient en remontant ou en haut de la page. Le « + » reste toujours touchable.
7. **« Réduire les animations »** : les glissements deviennent un fondu de 150 ms ; le geste de retour suit toujours le doigt. `e2e_design_motion` le vérifie.

## Lot 2 — Le toucher

8. **Deux réactions au toucher, pas plus.**
   - Boutons, puces, onglets, le « + » : `scale(.97)` avec `--spring`.
   - Lignes de liste et cartes qui ouvrent une page : le fond `--fill`, sans rétrécir.
   - Les autres valeurs (.9, .92, .94, .96, .98, .985, .99, les opacités .6 et .7) disparaissent.
9. **Trois styles de bouton dans toute l'app** : le bouton principal en pilule de 44 px (un seul bleu par écran), le bouton secondaire en pilule de 44 px, et la puce ou le segment de 38 px. On commence par la page d'un trade (13 styles aujourd'hui).
10. **Toute cible touchable fait au moins 44 × 44 px de zone**, sans changer le dessin (marge invisible ou `::after`). Sont concernés : « Calendar › », « Journal › », « Level… », les « i », les boutons de 32 px de la checklist, « ‹ Trades ».

## Lot 3 — Alléger

11. **Ouvrir une page ne bloque pas le doigt.** Sur le téléphone ralenti 4 fois, la page est dessinée **moins de 150 ms** après le toucher. Le graphique, le contexte économique et les cartes sous l'écran se remplissent après la première image. Aujourd'hui : un trade 525 ms, Aujourd'hui 244 ms, Stats 150 ms.
12. **Stats tient sur environ 2 écrans** sur téléphone : les 4 chiffres, le score, la courbe, « À surveiller » et le calendrier. « Analyse détaillée › » ouvre une sous-page (point 4) avec les 9 onglets et les tableaux. Rien n'est retiré, tout est un niveau plus bas.
13. **La recherche sur téléphone est une feuille** : poignée, glisser pour fermer, le champ prêt. Elle propose les pages et l'aide. Les commandes de thème et de partage sortent de la recherche sur téléphone (le thème est dans Réglages, le partage sur sa page).
14. **Les menus vont à l'essentiel.**
    - Le menu du profil passe de 7 lignes à 4 : Ma progression, Quoi de neuf, Réglages, Aide.
    - « Parrainage » et « Donner mon avis » vont dans Réglages ; « Déconnexion » y est déjà.
    - La feuille « Filtres » n'a plus « Importer un CSV », qui est déjà dans « Nouveau trade » et en haut de Trades.

---

**Fini quand** (refait avec le même script de mesure, téléphone ralenti 4 fois et ordinateur, EN, FR et ES, en clair et en foncé) :
- un changement d'onglet ne lance **aucune** animation d'entrée ;
- la position est gardée au changement d'onglet et au retour (Trades, Aujourd'hui, Stats) ;
- un trade s'ouvre en glissant et se dessine en moins de 150 ms ;
- dans l'app installée, le geste depuis le bord revient en arrière ;
- la barre d'onglets se réduit en descendant ;
- le CSS ne contient plus que deux réactions au toucher ;
- aucune cible de moins de 44 px de zone sur Aujourd'hui, Trades, un trade et un compte ;
- Stats fait moins de 2 500 px sur téléphone avec les données d'exemple.

Un nouveau test, `e2e_motion_ios`, vérifie les points 1, 2, 3, 6, 8 et 10. La suite complète passe.
