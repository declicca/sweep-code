# Mesure 0 — le point de départ du parcours

Étape 0 de `SWEEP.md`. Mesuré sur l'app telle qu'elle est (`origin/main` au commit `590bd3f`), avant toute modification du parcours. Chaque étape suivante refait ces mesures et les compare à celles-ci.

## 1. M1 en local : touchers, champs, écrans

**Comment c'est mesuré**
- Outil : `app/tools/parcours-baseline.py`.
- Un robot fait le parcours d'un nouveau trader avec de vrais touchers, depuis l'écran d'inscription.
- Compte choisi : Évaluation › Topstep › Trading Combine › 50K.
- Expérience : « Moins de 6 mois » sur le téléphone, « Plus d'un an » sur l'ordinateur.

**Conventions de comptage**
- Un **toucher** est tout geste : un bouton, ou un champ qu'on touche avant d'écrire.
- Un **champ** est un texte tapé.
- Le **temps humain estimé** compte 2,5 s par toucher et 5 s par champ, la même échelle que l'audit des parcours du 16 oct.
- Le temps du robot est donné comme repère seulement : c'est la machine, sans ses propres pauses.

**Les deux points d'arrivée**
- **(a) Risque permis vu** : le plan est enregistré, et sa perte max (préremplie à 1 000 $) a été montrée.
- **(b) Premier trade enregistré** : le message « Trade enregistré · Il te reste 1 200 $ avant ta perte max. » s'affiche.

Les chiffres sont cumulés depuis l'écran d'inscription.

| Cas | (a) Touchers | (a) Champs | (a) Écrans | (a) Temps humain estimé | (b) Touchers | (b) Champs | (b) Écrans | (b) Temps humain estimé |
|---|---|---|---|---|---|---|---|---|
| Téléphone 390 FR, sans capture (« Saisir à la main ») | 11 | 3 | 3 | ~42 s | 16 | 5 | 5 | ~65 s |
| Téléphone 390 FR, avec capture | 11 | 3 | 3 | ~42 s | 16 | 4 | 5 | ~60 s |
| Ordinateur 1300 EN, sans capture | 11 | 3 | 3 | ~42 s | 16 | 5 | 5 | ~65 s |
| Ordinateur 1300 EN, avec capture | 11 | 3 | 3 | ~42 s | 16 | 4 | 5 | ~60 s |

**Les écrans dans l'ordre**
1. Inscription.
2. Bienvenue (« Trois étapes et tu trades »).
3. Plan du jour.
4. Feuille « Nouveau trade ».
5. Formulaire manuel, ou capture lue.

**Où partent les touchers**
- **Inscription** : 3 touchers et 2 champs (courriel, mot de passe, bouton).
- **Bienvenue** : 6 touchers et 1 champ (prénom, expérience, Évaluation, Topstep, 50K, « Créer le compte » ; Trading Combine est choisi seul, c'est le seul programme).
- **Plan** : 2 touchers (biais, enregistrer).
- **Trade sans capture** : 5 touchers et 2 champs (« Saisir à la main », Long, prix d'entrée, prix de sortie, Enregistrer).
- **Trade avec capture** : 5 touchers et 1 champ (la zone, la photo choisie, le P&L net, Long, Enregistrer).
  - Le P&L a été tapé parce que la lecture de Sweep AI est simulée en local.
  - Avec la vraie lecture, ce chemin peut tomber à 4 touchers et 0 champ.

**Ce que la mesure montre déjà**
- Au jour 1, **le risque permis apparaît après 11 touchers**, et le premier trade après 16.
- Sans capture, le trader doit trouver « Saisir à la main » : un toucher et un formulaire de plus, ce qui donne 5 écrans.
- Aucune erreur de page dans les 4 cas.

**Pour relancer la mesure**

```bash
sh tools/sync.sh /tmp/gpar && DEST=/tmp/gpar PORT=8495 sh tools/run.sh python3 tools/parcours-baseline.py http://127.0.0.1:8495 --json /tmp/mesure.json
```

Les résultats bruts sont dans `mesure-0-local.json`.

## 2. En ligne : les vrais traders

Ces chiffres se lisent dans Admin › Métriques. Les deux dernières lignes sont nouvelles : elles sont lisibles une fois ce lot déployé (accord de Mateo).

| Indicateur | Définition | Où le lire | Valeur au départ |
|---|---|---|---|
| Temps de M1 | Médianes depuis l'inscription : prénom, premier compte, premier plan, premier trade | « Le démarrage » (déjà en ligne) | _à relever_ |
| Journées fermées | Séances avec au moins un trade sur 30 jours, dont la revue est faite | « Journées fermées » (nouveau) | _à relever après déploiement_ |
| Bilans ouverts | Semaines terminées avec au moins un trade, sur les 8 dernières, dont le bilan du vendredi a été ouvert | « Bilans de la semaine ouverts » (nouveau) | _à relever après déploiement_ |

**Les filtres** : semaine d'inscription et source, comme pour les autres indicateurs. Les comptes internes sont exclus.

**À noter**
- Le bilan ouvert est compté à partir de l'événement `weekly_opened`, qui existe depuis le 10 oct. (brief 01, étape 5, lot 1). Les semaines plus anciennes peuvent donc être sous-comptées.
- Le relevé est à faire le jour du déploiement de ce lot, puis à noter ici, avec la date.
