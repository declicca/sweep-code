# L'app dans le temps : 3 semaines de vie simulées (1er nov. 2026, pour la session App)

**Demande de Mateo (1er nov.)** : « Analyse l'app d'un point de vue complètement nouveau, qu'on n'a jamais exploré : tous les petits détails à développer ou à améliorer, de nouvelles fonctionnalités, des fonctionnalités qu'on peut enlever. »

**L'angle** : tous les tours précédents regardaient **un instant** (un écran, une journée, un geste). Celui-ci regarde **la durée**. Deux traders vivent 3 semaines dans l'app, en avançant l'horloge du serveur (`SWEEP_GAME_NOW`) et des pages, le matin à 8 h 45, à 10 h 20 et à 16 h 40 (heure de New York), plus le samedi. On note ce que l'app leur dit chaque jour : ce qui se répète, ce qui s'accumule, ce qui devient faux, et ce qui manque.

Version : `149e91b`. Téléphone 390, en français, foncé. Les deux traders s'inscrivent le dimanche 1er nov. avec un Topstep 50K en évaluation, et tout passe par l'interface (inscription, plan, trade sans capture, revue).
- **Sam, irrégulier** (15 jours, du 2 au 21 nov.) : il ne fait jamais son plan ni sa revue. Il a un jour de tilt (−1 050 $, sa marge descend à 950 $), deux jours d'absence, puis il atteint l'objectif de 3 000 $ le 19 nov.
- **Léo, discipliné** (10 jours, du 2 au 14 nov.) : plan et revue chaque jour, 1 ou 2 trades.

Aucune erreur JavaScript. **Limite** : les notifications du serveur, les courriels et les rappels sur le téléphone suivent l'heure réelle. On ne les a donc pas vus vieillir.

---

## A — Ce que l'app dit de faux

| # | Ce qu'on a vu | Correction |
|---|---|---|
| A1 | Sam n'a jamais fait de plan. Sa cloche dit pourtant **« Une semaine entière dans ton plan. Pas un seul trade hors plan la semaine dernière. C'est ça, la discipline. »** La semaine comptée n'avait aucun trade : l'éloge est vrai par défaut. | Pas d'éloge de discipline sans au moins un jour de trading avec un plan dans la semaine. Un test : 0 trade, ou des trades sans plan, donc aucune notification « dans ton plan ». |
| A2 | Réussite de l'évaluation : **« Objectif de profit atteint · 11 jours, sans toucher au drawdown »**. Sa marge était pourtant descendue à 950 $ sur 2 000 $ le 12 nov. | « sans dépasser ton drawdown ». Et si la marge est passée sous la moitié, on le dit : « ta marge est descendue à 950 $ le 12 nov. ». |
| A3 | Léo, le 12 nov. : 0 trade sur 2 dans son plan, note D, −350 $. Après sa revue, l'app affiche **« Journée réussie »**. | « Journée complète » (le plan et la revue sont faits). « Réussie » se lit comme un jour gagnant. |
| A4 | Sans plan du jour, **« Ton risque permis aujourd'hui »** est la perte max du dernier plan (500 $) pendant 6 jours. Ensuite, sans rien changer, il passe à **toute la marge de drawdown** : 2 000 $, puis 950 $ le lendemain du tilt, puis 3 000 $. Dire à un trader qu'il peut risquer toute sa marge, c'est l'inviter à brûler son compte. | Sans plan, on garde la dernière perte max choisie (500 $), sans date limite. La marge de drawdown reste une limite affichée, jamais un « risque permis ». |

## B — Ce qui s'accumule

| # | Ce qu'on a vu | Correction |
|---|---|---|
| B1 | **« X missions à rattraper », en or**, ne fait que monter : 1, 3, 6… **18** pour Sam, et **10 pour Léo**, qui fait pourtant tout ce que l'app demande. Le parcours de 90 jours avance au calendrier (« Jour 20 sur 90 »), week-ends compris, que la personne le suive ou non. | Le parcours avance quand la personne fait sa mission, pas au calendrier : « Jour 4 sur 90 » veut dire 4 missions faites. Plus de compteur de retard. L'or reste réservé aux pertes. |
| B2 | Inscrit depuis une heure, Sam voit **« Quoi de neuf »** en plein écran sur sa première page Aujourd'hui, puis **4 notifications d'annonces** dans sa cloche. Par exemple « Plusieurs comptes d'un coup » alors qu'il a un compte. La pastille « 1 » de la cloche reste là 3 semaines. | Quoi de neuf et les annonces seulement pour ce qui est sorti **après** l'inscription. La pastille compte ce qui concerne le trader, pas les annonces. |
| B3 | La bande des jours d'Aujourd'hui montre **3 semaines vides avant l'inscription** (du 12 au 30 oct.). | La bande commence au premier jour de la personne (ou à son premier trade importé). |

## C — Ce qui se répète jusqu'à devenir du décor

| # | Ce qu'on a vu | Correction |
|---|---|---|
| C1 | Le coach du matin dit la même chose **chaque jour** pendant 3 semaines : « Avant ta séance : ton plan. Ensuite, je te dis trade par trade si tu le respectes. » Pour Sam, après chaque trade, 15 jours de suite : « Pas de plan pour cette séance. Fais ton plan avant le prochain trade : 30 secondes. » | Une phrase déjà dite 3 jours de suite ne revient pas telle quelle. Le coach change d'approche. Pour Sam, au 3ᵉ jour sans plan : « Reprends ton plan d'hier ? » en un toucher (D2). La phrase d'explication (« Ensuite, je te dis… ») ne s'affiche que la première semaine. |
| C2 | **Des fenêtres en pleine séance**, juste après l'enregistrement d'un trade : « Ajoute Sweep à ton écran d'accueil » (le 3 nov. ; et pour Léo le 10, puis encore le 11 après « Plus tard »), « Ton plan avant ton prochain trade » (le 9 et le 11 nov.). La fenêtre de réussite de l'évaluation revient à chaque ouverture après « Pas encore » (le 19, le 20 et le 21). | **Rien ne s'ouvre par-dessus l'app entre le premier trade et la revue** (sauf le trader lui-même). Ces messages attendent la revue ou le lendemain matin. « Plus tard » veut dire 7 jours. Après « Pas encore », la réussite devient une ligne sur la carte du compte, pas une fenêtre. |
| C3 | Chaque matin, un toast de récompense : « Nouveau badge débloqué · +50 XP », « Débloqué : Bilan de la semaine et coffre », « Niveau 6 atteint », « Streak de 7 jours · +100 XP », « Mission accomplie · +100 XP », « Nouveau rang Apprenti »… Sam, qui ne fait rien de la routine, reçoit aussi « Débloqué : Les boss », « Débloqué : Les saisons » et « Nouveau boss ». | Voir E1. |

## D — Ce qui manque (nouvelles fonctions, petites)

| # | Le moment | Ce qu'il faut |
|---|---|---|
| D1 | **Le lendemain d'un mauvais jour.** Sam a perdu 1 050 $ et il lui reste 950 $ de marge. Le matin suivant, le coach lui dit : **« Continue ce qui marche : Long »**, et « Ton risque permis : 950 $ ». | **Le mode prudence** : quand la marge est sous la moitié, ou après un jour au-delà de la perte max du plan, le matin suivant affiche une ligne « Marge à 950 $ : risque réduit de moitié aujourd'hui (250 $) ». Le plan est prérempli avec cette perte max, et le coach parle de protéger le compte, pas de « ce qui marche ». Il en sort après 2 jours verts. EN, FR et ES. |
| D2 | **Le plan de chaque jour.** Le plan de l'inscription prend 30 secondes (biais et perte max). Le « Plan express » de chaque jour a **2 étapes et 3 champs à écrire obligatoires** (niveaux, scénario attendu, scénario alternatif). La perte max n'est pas préremplie, et le premier jour on redemande l'instrument. Léo réécrit les mêmes phrases tous les jours ; Sam n'en fait aucun. | **« Reprendre mon plan d'hier »** : un toucher, puis on change ce qu'on veut. Seuls le biais et la perte max sont obligatoires, comme à l'inscription. Les scénarios restent proposés, pas imposés. |
| D3 | **La revue de chaque soir.** Elle ne se ferme pas sans confirmer le solde Topstep (« Confirme ton solde sur Topstep »), même quand rien n'a bougé. C'est un toucher de plus, tous les soirs. | « C'est le même » est choisi d'avance. On ne demande que si un trade du jour n'a pas de capture ou si le solde calculé paraît faux. |
| D4 | **La règle de demain.** Léo écrit « Attendre la confirmation » dans sa revue. Le lendemain matin, Aujourd'hui ne la montre pas : elle n'apparaît que dans le plan, et seulement si on l'ouvre. | Une ligne dans « Maintenant » le matin : « Ta règle d'aujourd'hui : attendre la confirmation ». |

## E — Ce qu'on peut enlever

**E1. Une seule couche de récompense visible.** En 3 semaines, nos deux traders ont croisé **11 systèmes** de progression : niveaux, XP, rangs, badges, série (streak), jours complets, missions de découverte, parcours de 90 jours, boss, saisons et coffre. Chacun a son toast. Pour un trader, l'essentiel est « ai-je fait ma routine ? », soit les jours complets.
- **On garde à l'écran** : « Niveau N · X jours complets › » (déjà là) et le parcours.
- **On n'annonce plus** : XP, badges, rangs, boss, saisons et coffre ne font plus de toast ni de fenêtre. Ils restent dans Ma progression pour qui va les voir. Le site les présente toujours ; rien n'est supprimé du code.
- **Au plus une récompense par jour, après la revue**, jamais le matin ni en séance. Rien n'est « débloqué » pour quelqu'un qui n'a pas encore 3 jours complets.

**E2.** Le compteur « missions à rattraper » disparaît (B1).

**E3.** « Quoi de neuf » n'apparaît plus aux nouveaux inscrits (B2).

## F — Détails

- « Pris 0 min après une perte » (toast et coach) : « Pris tout de suite après une perte ». Le C3 du 31 oct. l'avait corrigé dans la feuille de trade, pas ici.
- Le compte qui a atteint son objectif reste en « Évaluation » tant qu'on répond « Pas encore » : la carte dit « Objectifs atteints · en attente de ta firme ».

---

**Fini quand** :
- Un nouveau test, `e2e_life_weeks`, refait cette simulation : 2 traders, au moins 10 jours de marché, l'horloge avancée par `SWEEP_GAME_NOW` et `tools/clientclock`. Il vérifie :
  - aucun éloge de discipline sans plan (A1) ;
  - le « risque permis » ne dépasse jamais la dernière perte max choisie (A4) ;
  - aucun compteur de retard (B1) ;
  - aucune fenêtre entre le premier trade et la revue (C2) ;
  - le coach ne répète pas la même phrase 3 jours de suite (C1) ;
  - au plus un toast de récompense par jour, jamais avant la revue (E1) ;
  - le mode prudence s'allume après le jour de tilt et s'éteint après 2 jours verts (D1).
- Tout nouveau texte en EN, FR et ES ; 390 et 1300 ; clair et foncé. La suite complète passe.
