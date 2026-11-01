# Tour visuel « iOS 27.2 » : formes, cohérence, barre du bas fixe (1er nov. 2026, pour la session App)

**Demande de Mateo (1er nov.)** : « Refais le tour visuel pour s'assurer que tout soit comme sur iOS 27.2, que tous les boutons soient similaires, par exemple tout ronds, pas carrés. Aussi, sur mobile, dans l'app, l'espace en bas n'est pas pareil selon le contenu : le menu doit toujours être au même endroit, peu importe la hauteur de la page. »

Version vue : `149e91b` (fluidité iOS 27 comprise), données d'exemple, téléphone 390 en foncé, 11 écrans. Plus les deux captures de Mateo, prises sur son iPhone dans l'app installée. Aucune erreur JavaScript.

Le cadre ne change pas : une évolution, pas de refonte, pas de nouvelle fonction. Tout texte en EN, FR et ES ; 390 et 1300 ; clair et foncé.

---

## 1 — La barre du bas et l'en-tête toujours à la même place (app installée sur iPhone)

**Ce qu'on voit sur l'iPhone de Mateo** :
- Trades, en haut de la page : le bas de la barre d'onglets est à **78 pt** du bas de l'écran. Une bande noire de 55 pt est sous la barre, et le fond de la page s'arrête au-dessus.
- Aujourd'hui, après avoir défilé : **23 pt**. C'est la bonne place (la règle `html.pwa body .bottomnav` donne 26 pt).
- En haut de Trades, le logo est à 121 pt du haut de l'écran, alors que sous la barre défilée il est à 72 pt : il y a un grand vide sous l'heure, et l'en-tête saute quand on défile.

L'écart, environ 55 pt, est la zone de l'heure (safe area du haut). Dans Chromium, la barre est au même endroit sur les 11 écrans (760 à 826 px) : le défaut n'existe que dans l'app installée sur iOS.

**Cause** : la safe area est comptée deux fois.
- `:root` a `padding-top` et `padding-bottom: env(safe-area-inset-*)`, avec `html { height: 100% }` (`app.css`, lignes 378 et 384).
- L'en-tête (`html.pwa body aside.side`) et la barre (`html.pwa body .bottomnav`) ajoutent leur propre safe area (`nav.css`, vers la ligne 2745).
- Tant que la page n'a pas défilé, iOS calcule la zone visible sans la bande de l'heure. La barre fixée en bas monte alors de cette hauteur ([WebKit 301994](https://bugs.webkit.org/show_bug.cgi?id=301994), et d'autres apps installées ont le même défaut).

**Correction** :
- La safe area à **un seul endroit** : plus de `padding` sur `:root` dans l'app installée. L'en-tête garde la sienne en haut, la barre d'onglets en bas, et le bas du contenu (`main`) laisse la place de la barre.
- La page fait toujours **au moins la hauteur de l'écran entier** (`min-height: 100lvh`, safe areas comprises), quelle que soit sa longueur. Le fond de la page descend jusqu'au bas de l'écran.
- La barre d'onglets, le bouton du coach et les toasts gardent **la même distance au bas de l'écran** sur toutes les pages, en haut de page comme après avoir défilé. L'en-tête ne saute pas au premier défilement.

**Fini quand** :
- un test vérifie, sur les 11 écrans, en haut et en bas de chaque page, que la barre est à la même place et qu'aucune safe area n'est sur `html` ou `body` ;
- **Mateo confirme sur son iPhone**, dans l'app installée, sur Trades vide, Aujourd'hui et Mon argent. Le défaut ne se voit que là, donc c'est son test qui fait foi.

## 2 — Tout ce qui se touche est rond

Comme sur iOS 27 : un bouton avec du texte est une **capsule**, un bouton avec une seule icône est un **cercle**. Les cartes et les tuiles gardent leurs rayons (14 / 20 / 26 / 32).

| # | Où | Aujourd'hui | Correction |
|---|---|---|---|
| R1 | Barre d'onglets | Le « + » est un carré arrondi (46 px, rayon 14). Le fond de l'onglet actif est un rectangle arrondi. | Le « + » est un cercle. Le fond de l'onglet actif est une capsule. |
| R2 | Trades, en haut | « CSV » est un rectangle arrondi (40 px, rayon 14). C'est le seul bouton de titre qui n'est pas une capsule (« Export », « Share my stats » le sont). | Une capsule, comme « Export ». |
| R3 | Page d'un trade | Les puces d'émotion (« Frustrated »…) ont un rayon de 10, contrairement à toutes les autres puces. Le bouton plein écran du graphique est un carré arrondi (34 px, rayon 10). | Les puces sont des capsules ; le bouton plein écran est un cercle. |
| R4 | Réglages, Apparence | Le choix du thème (« Match my device ») a un rayon de 14 dans un segment en capsule. | Une capsule dans la capsule, comme les autres segments. |
| R5 | Mon argent, Comptes, un compte | Les étiquettes : « Requested » et « LIVE » sont des rectangles arrondis, alors que « Paid », « Real » et « Simulated » sont des capsules. | Toutes les étiquettes sont des capsules, de la même hauteur. |
| R6 | Page d'un trade | La case « Checklist 100% » a un contour bleu : elle ressemble à un champ à remplir. | La même tuile que « R multiple » à côté, sans contour ; le bleu seulement sur le chiffre. |

**Les tailles** : les boutons en capsule ont aujourd'hui 7 hauteurs (34, 36, 38, 40, 42, 46 et 48 px). Il en reste trois : 44 (bouton), 38 (puce ou segment) et 34 (bouton d'icône dans une barre). « + Payout » et « + Expense » passent de 50 à 44.

## 3 — Le même geste a la même apparence partout

| # | Où | Aujourd'hui | Correction |
|---|---|---|---|
| C1 | Retour en arrière | Trois styles : « ‹ Trades » en gris, sous le titre (un trade) ; « ‹ Accounts » et « ‹ Today » en bleu, sous le titre (un compte, Réglages). | Comme sur iOS : « ‹ Trades » en bleu, **au-dessus** du grand titre, à gauche, partout pareil. |
| C2 | Ce qui se déplie | Réglages : une flèche ⌄ à droite. Page d'un trade : « › Full review · 2 of 4 ▾ » (deux flèches) et « › More details ». | Une seule forme : le libellé, puis un chevron à droite qui tourne de 90° à l'ouverture. |
| C3 | Les « i » | Stats : dans le coin de la tuile. Un compte : au-dessus de la ligne du libellé (« Profit factor ⁱ », « Worst drawdown ⁱ »). Aujourd'hui : juste après le libellé. | Toujours juste après le libellé, centré sur sa ligne, de la même taille. |
| C4 | Réglages | Cinq cartes séparées (« My routine », « Notifications », « Data »…), chacune avec sa flèche. | Une seule liste groupée, comme Réglages sur iPhone : des lignes séparées par un trait fin, dans une carte. |
| C5 | Trades, Calendrier, Stats | « You are looking at sample data. » sur deux lignes, avec « Remove sample data » en lien sur deux lignes dans le cadre or. | Une ligne : « Sample data » puis une capsule « Remove » à droite. Le texte complet reste dans le « i » ou dans l'aide. |
| C6 | Page d'un trade, « Your lesson » | Le texte d'exemple est coupé (« Make your plan before the next trade: 30 seconds » ne tient pas). | Le champ s'agrandit avec le texte, et l'exemple tient en entier. |
| C7 | Page d'un trade, graphique | Les durées (15s, 30s, 1m…) sont coupées par le bord, avec un « ! » à moitié visible. | La ligne défile sans rien couper, avec un fondu au bord comme les autres lignes défilantes. |

---

**Fini quand** :
- un test (`e2e_visual_fit` ou un nouveau) compte, sur les 11 écrans : aucun bouton avec du fond ou un contour dont le rayon est plus petit que la moitié de sa hauteur (sauf les tuiles et les cartes) ; les boutons en capsule n'ont que 3 hauteurs ; la barre est à la même place sur toutes les pages ;
- les captures avant et après, en EN, FR et ES, à 390 et 1300, en clair et en foncé ;
- Mateo valide la barre du bas sur son iPhone.
