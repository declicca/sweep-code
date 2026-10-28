# Brief pour la session App : mise à jour visuelle « iOS 27.2 » (28 oct. 2026)

**De** : la session stratégie et tests. **Pour** : la session d'exécution.

**Demande de Mateo (28 oct.)** : « refais une analyse visuelle de l'app et fais une mise à jour visuelle en mode iOS 27.2 ».

**Le cadre**
- C'est une évolution du design « esprit iOS 27 » du 15 oct. (`docs/analyse/design-ios27-rapport.md`) et du design system de `CONTEXTE-APP.md` (section 8). Ce n'est pas une refonte.
- On garde la palette, Geist et Geist Mono, les rayons 10 / 14 / 20 / 26 / 32, la courbe unique et un seul bouton bleu par écran.
- Pas de nouvelle fonction, pas d'information retirée.

**Ce qu'iOS 27 change au design, d'après Apple et la presse** (rien de précis n'est publié sur 27.2 ; on suit donc iOS 27) :
1. **Le verre est plus lisible** : l'arrière-plan est plus diffusé sous le verre, un **bord assombri** entoure les éléments en verre, et les **reflets sont plus vifs** sur leurs arêtes.
2. **Sous une barre, le défilement passe derrière une barre uniforme** en haut, pour garder le texte lisible.
3. **Le réglage de transparence** (plus clair, normal, plus teinté) est respecté par les apps. Pour nous, ce sont « Réduire la transparence » et « Contraste élevé », déjà respectés : il faut que ça reste vrai.
4. **Des icônes plus nettes.**

Sources : [MacRumors, juin 2026](https://www.macrumors.com/2026/06/10/how-liquid-glass-is-changing-in-ios-27/), [Tom's Guide](https://www.tomsguide.com/phones/iphones/ios-27-has-a-bunch-of-changes-including-a-refined-liquid-glass-design-but-how-much-has-changed-from-ios-26), [MacStories](https://www.macstories.net/stories/ios-and-ipados-27-review/2/).

Les règles de travail restent les mêmes : un lot à la fois, la suite complète à 0 échec, la CI verte, `CONTEXTE-APP.md` à jour, EN / FR / ES, 390 et 1300, clair et foncé, captures avant et après, et aucun déploiement sans l'accord de Mateo.

---

## L'analyse visuelle (28 oct., `058bf24`)

**Conditions** : en anglais (la langue de 7 traders actifs sur 8), avec les données d'exemple, sur ordinateur 1300 et téléphone 390, en clair et en foncé, sur 11 écrans (Aujourd'hui, Trades, un trade, Stats, Calendrier, Journal, Comptes, un compte, Mon argent, Réglages, la feuille « New trade »). 45 captures, aucune erreur JavaScript.

**Ce qui est déjà bien** :
- la barre d'onglets flottante du téléphone ;
- la feuille « New trade » (une poignée, le fond flouté, une seule zone d'action) ;
- le grand titre, « Now » et le rythme des cartes ;
- le thème clair cohérent avec le foncé.

**Ce qui ne va pas** : le lot 1 ci-dessous.

---

## Lot 1 — Les défauts visuels vus dans l'analyse

| # | Écran | Défaut | Correction |
|---|---|---|---|
| V1 | Aujourd'hui, ordinateur (clair et foncé) | **La carte « My money » a les coins du haut carrés et un trait plat en haut**, contrairement à toutes les autres cartes. C'est sans doute la carte déplacée par l'équilibre des colonnes. | Le même rayon de 26 px partout, sans trait. Vérifier aussi « À surveiller », « Ce mois-ci » et « Tendances », qui sont déplacées de la même façon. |
| V2 | Partout en anglais | **« 75 % », « 0 % »** : l'espace avant « % » est français. En anglais, on écrit « 75% ». | Le pourcentage suit la langue : « 75% » en anglais, « 75 % » en français, « 75 % » en espagnol. |
| V3 | Aujourd'hui, la routine | **Les trois pastilles n'ont pas la même mise en page.** « Discipline » a son libellé au-dessus et un fond bleu, la série a l'icône et le chiffre sur une ligne (« 0 day streak »), « Level » a son libellé au-dessus. | Une seule mise en page : le libellé au-dessus, la valeur en dessous, sans fond de couleur. |
| V4 | La page d'un trade | **Des phrases en police à chasse fixe** : « the 16th at 19:14 - 19:30 », « session of Aug 17 · entered on the 16th at 19:14 ». | Geist Mono seulement pour les nombres, et Geist pour les phrases. Vérifier les autres valeurs texte de cette grille (Session, Setup, Tags). |
| V5 | La page d'un trade, ordinateur | **La colonne de gauche est vide sous « Full review »**, alors que celle de droite (« Setup & costs », « Economic context ») descend de 600 px. | Les deux colonnes s'équilibrent, comme sur Aujourd'hui. Le setup ne se choisit qu'à un seul endroit (le point C3 du tour du 27 oct.). |
| V6 | Stats, ordinateur | **« Performance score » est un graphique en barres 3D**, le seul objet en relief de l'app. | Des barres plates, du même style que les autres graphiques de Stats. |
| V7 | Stats, ordinateur | **« P&L breakdown » s'étire à la hauteur de « Patterns to watch »** et laisse environ 400 px vides. | Chaque carte garde sa hauteur naturelle, ou l'espace se remplit par l'équilibre des colonnes. Ce n'est pas un vide dans une carte. |
| V8 | Calendrier de Stats | **Les jours de perte sont remplis d'un or brun opaque**, beaucoup plus lourd que le bleu des jours de gain. | Un or aussi léger que le bleu (même opacité), avec le montant en or. |

**Fini quand** : les 8 points ont disparu sur les captures avant et après, en EN, FR et ES, à 390 et 1300, en clair et en foncé. `e2e_design_shared` (ou un nouveau test) vérifie V1 (rayon de toutes les cartes d'Aujourd'hui), V2 (« % » selon la langue) et V4 (aucune phrase en Geist Mono sur la page d'un trade).

---

## Lot 2 — Le verre d'iOS 27

Ça concerne : la barre d'onglets du téléphone, la barre du haut, les feuilles (« New trade », plan, revue, filtres), les menus et la barre latérale de l'ordinateur.

1. **Un bord assombri** : un trait intérieur de 1 px, plus foncé que le verre (en foncé, noir à environ 35 % ; en clair, encre à environ 12 %). Il détache le verre du contenu qui défile dessous.
2. **Un reflet plus vif** : sur l'arête du haut seulement, un dégradé de 1 px blanc (environ 18 % en foncé, 60 % en clair) qui s'efface vers les côtés. Pas de halo, pas de reflet qui suit la souris (règle de `CLAUDE.md`).
3. **Le fond plus diffusé** : plus de flou et un peu plus de saturation sous le verre, pour que le texte posé dessus reste à 4,5:1 quel que soit le contenu en dessous. On le mesure sur la barre d'onglets au-dessus d'une carte bleue et d'une carte or.
4. **Une barre uniforme quand on défile** : sur téléphone, dès que le contenu passe sous la barre du haut, elle devient une barre de verre pleine largeur avec le titre en petit (comme iOS). Sur ordinateur, même chose pour les en-têtes collants (filtres de Stats et de Trades).
5. **« Réduire la transparence » et « Contraste élevé »** : le verre devient opaque, et le bord se renforce. C'est déjà testé par `e2e_design_motion` ; on ajoute le bord.
6. **Les icônes** de la barre d'onglets et de la barre latérale : un trait de la même épaisseur partout, alignées sur la grille de pixels (pas de demi-pixel flou à 1x).

**Fini quand** :
- les captures avant et après sur Aujourd'hui, Stats et la feuille « New trade », téléphone et ordinateur, en clair et en foncé, montrent le bord et le reflet ;
- le texte de la barre d'onglets est à 4,5:1 au-dessus de n'importe quel contenu (axe-core) ;
- la vitesse d'un changement de page sur un téléphone lent ne bouge pas (même mesure A/B que le 15 oct.).

---

## Lot 3 — Moins de couches (thème clair surtout)

Sur Aujourd'hui en clair, il y a trois couches : le fond gris, la carte blanche, puis des tuiles grises dans la carte (P&L, Trades, Win rate ; les trois étapes de la routine ; les comptes). iOS 27 garde deux couches : le fond, puis la carte.

- **Dans une carte**, les tuiles n'ont plus de fond. Elles sont séparées par un trait fin (les séparateurs en retrait existent déjà), ou par l'espace seul.
- **Exception** : les trois étapes de la routine (Plan, Execution, Review) gardent leur forme de tuile, parce qu'elles se touchent comme des boutons. Mais leur fond est plus proche de celui de la carte.
- **En foncé**, on applique la même règle ; la différence s'y voit moins.

**Fini quand** : Aujourd'hui, Stats et la page d'un compte n'ont nulle part trois niveaux de fond, en clair et en foncé, et `e2e_visual_fit` passe toujours.

---

## Ordre

1. **Lot 1** tout de suite : ce sont des défauts, et il peut partir avec l'étape 2 du brief « pertes oubliées ».
2. **Lot 2**, puis **lot 3**, après l'étape 2 des pertes oubliées.

Captures de l'analyse : gardées hors du dépôt, dans le dossier temporaire de la session stratégie et tests. Elles se refont sur demande.
