# Audit de l'app — 18 octobre 2026

**Version auditée** : f60ecf7 (en ligne).

**Méthode** : un passage automatique sur **toutes les pages** et sur les **4 feuilles principales**.
- Pages : Aujourd'hui, Trades, Calendrier, Journal, bilan de la semaine, Stats, Progression, Comptes, Mon argent, Annonces, Réglages, Import, Abonnement, Parrainage, Feedback, Admin, la page d'un trade, la page d'un compte.
- Feuilles : nouveau trade avant et après la capture, formulaire manuel, plan.
- Formats : téléphone 390 × 844 et ordinateur 1300 × 850, en français, thème foncé (et clair pour 5 pages).
- Données : les données d'exemple (115 trades, 5 comptes).

Le passage relève :
- les erreurs JavaScript et les requêtes en échec ;
- le débordement horizontal et les éléments qui sortent de l'écran ;
- les zones tactiles trop petites et les textes coupés ;
- l'anglais resté en français.

Il prend aussi une capture de chaque page, que j'ai ensuite relue.

Les mesures brutes sont dans `mesures.json`, les captures dans `captures/`.

## Ce qui va bien

- **Aucune erreur JavaScript** et **aucune requête en échec**, sur aucune page, dans les deux tailles et les deux thèmes.
- **Aucun débordement horizontal** de page.
- **Français complet**. Les seuls mots anglais sont du vocabulaire de trading : « Profit factor », « Payout », et « Break of structure », un nom de setup des données d'exemple.
- Le nouveau « Nouveau trade » (capture d'abord) est propre aux deux tailles.

## 1. À corriger : ce qui se voit mal ou est caché

| # | Où | Ce qui ne va pas | Capture |
|---|---|---|---|
| 1 | Stats › Analyse détaillée › « Processus vs résultat » (téléphone) | Les montants se coupent sur deux lignes (« +72 78 / 1,60 $ », « +4 203 / $ »). C'est contraire à la règle « un montant clé n'est jamais coupé ». | `stats-processus-390.png` |
| 2 | Stats › « Règles suivies vs enfreintes », et la même table dans Progression (téléphone) | Le tableau fait 416 px dans un écran de 390. La 2ᵉ colonne est coupée (« −9 212,60 », « 33 », « 0,3 ») et rien n'indique qu'on peut la faire défiler. | `stats-regles-390.png` |
| 3 | Le bouton Sweep AI, au repos | Il couvre du contenu : sur téléphone, l'interrupteur « Profil public » (Réglages) et le badge « Payé » (Mon argent) ; sur ordinateur, le texte de « La tendance de la semaine » (Aujourd'hui) et la barre de progression du dernier compte (Comptes). | `reglages-390.png`, `mon-argent-390.png`, `aujourdhui-1300.png`, `comptes-1300.png` |
| 4 | Réglages (téléphone) | « Español » coupé dans le choix de la langue (« Españ »), le texte d'aide du nouveau mot de passe coupé (« 10 caractères ou… »), et 3 questions de la checklist coupées dans leur champ. | `reglages-langue-390.png` |

## 2. Plus simple : les pages trop longues (le fil « minimaliste »)

| # | Où | Constat | Proposition |
|---|---|---|---|
| 5 | Page d'un compte (téléphone) | Environ **4 800 px**. Les formulaires « Règles de la firme », « Règles de payout », « Recalibrer » et « Détails » sont tous ouverts au-dessus des trades et des payouts. | Montrer d'abord le statut, le capital, les trades et les payouts, et regrouper les 4 formulaires sous un seul « Réglages du compte » replié. |
| 6 | Stats (téléphone) | Environ **5 800 px** et plus de 15 blocs : « Ce qui fonctionne pour toi », 4 indicateurs, le score, la courbe, 6 tuiles, le drawdown, les durées, la répartition, les tendances, le mois, l'analyse détaillée, les tableaux. | Garder en tête « Ce qui fonctionne pour toi », les 4 indicateurs et la courbe, et replier le reste sous « Analyse détaillée ». |
| 7 | Aujourd'hui (téléphone) | 8 blocs : routine, jour / semaine, annonces, Mon argent, comptes, tendance, accès rapide, courriel. « Accès rapide » refait ce que font le bouton « + » et les menus (importer, payout, calendrier, partager). | Retirer « Accès rapide ». |
| 8 | Mon argent | Trois rangées de sélecteurs empilées : Comptes / Mon argent, puis les filtres, puis Mes entrées / Analyse. | Mettre « Mes entrées / Analyse » dans la rangée des filtres, ou en onglets du bloc. |
| 9 | Page d'un compte › Trades | Chaque ligne répète « Topstep — Compte 1 », alors qu'on est déjà sur ce compte, ce qui coupe la ligne (« Topste… »). | Ne pas répéter le compte sur sa propre page. |

## 3. Petits détails

| # | Où | Constat |
|---|---|---|
| 10 | Zones tactiles (téléphone), sous 44 px | L'avatar en haut (32 × 28, sur toutes les pages) ; les liens « Calendrier › », « Journal › » et « Tout voir › » (20 px de haut) ; « Marquer payé » et « Partager » (24 px) ; « Long / Short » sur la feuille rapide (27 px) ; les liens légaux de Réglages (21 px). |
| 11 | Stats › « P&L net sans eux » | Deux polices dans la même phrase : « +48 726,80 $ » en Geist, « +39 437,60 $ réel » en Geist Mono. |
| 12 | Aujourd'hui (ordinateur) | La colonne de droite s'arrête après « La tendance de la semaine » et laisse un grand vide à côté du calendrier et de Mon argent. |
| 13 | Données d'exemple | Deux « Compte 1 » et deux « Compte 2 » (chez Topstep et chez Lucid), ce qui prête à confusion dans les listes et les captures. |

## Ordre proposé

1. **Lot 1 : points 1 à 4, 10 et 11.** Ce sont des corrections sûres, sans changement de parcours.
2. **Lot 2 : points 5 et 9**, la page d'un compte. C'est le plus gros gain de simplicité.
3. **Lot 3 : points 6, 7 et 8.** Stats, Aujourd'hui et Mon argent plus courts.
4. **Lot 4 : points 12 et 13.**

Chaque lot : tests à 390 et 1300, puis ton accord avant le déploiement.

## Suivi

Les 4 lots sont faits et en ligne (18 et 19 oct.). Le détail de chaque lot est dans `app/CONTEXTE-APP.md`.
