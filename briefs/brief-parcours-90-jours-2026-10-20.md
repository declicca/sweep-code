# Brief — Le parcours de 90 jours dans l'app (20 oct. 2026)

Demande de Mateo : à l'inscription, un trader qui a moins de 6 mois d'expérience reçoit un plan de formation complet
avec la plateforme, tiré des trois PDF « Sweep 90-Day Gameplan — Learning Edition ». Inclus dans le premier forfait
payant (Pro, et Elite), pas dans Free. En mode jeu : interactif, fluide, qui donne envie d'avancer et d'apprendre.

## Ce qui existe déjà
- Le contenu complet des PDF, en EN / FR / ES, sur le site (`website/src/pages21.py`) : 90 missions sur 12 semaines
  (type Apprendre / Pratique / Revue, marché ouvert / fermé / journée légère, durée, « C'est fait quand »), les 3 portes
  de fin de mois, le Sweep Setup, les règles, la routine, le vocabulaire, les étiquettes, l'échelle de taille, le playbook.
- Le jeu : XP attribuée par le serveur avec une clé unique (`GameEngine::awardXp`, jamais deux fois), célébrations,
  niveaux, streak, badges.
- L'inscription : premier compte → plan → trade (brief 03, étape 1). La mission 1 du parcours (« Fixe tes garde-fous :
  ajoute ta firme et ton compte ») est exactement le premier écran.
- Les forfaits : Pro = premier forfait payant ; l'essai donne Pro.

## Décisions
- **Accès** : la fonction `gameplan` est vraie pour Pro et Elite, fausse pour Free, par défaut dans le code (la
  configuration privée peut la changer). Free voit le parcours verrouillé (aperçu et mise à niveau), pas les missions.
  Facturation pas encore en ligne : comme le reste, tout le monde y a accès.
- **Calendrier** : comme les PDF, le parcours commence un lundi ; le jour N a sa date. Une mission en retard reste
  faisable (« à rattraper »), sans pénalité. Une seule mission nouvelle s'ouvre par jour de trading.
- **Validation** : Sweep coche seul ce qu'il peut mesurer (compte et limites enregistrés, trade avec stop et cible,
  séance notée au journal, bilan de la semaine, zéro écart) ; le reste, le trader le coche lui-même devant son
  « C'est fait quand ».
- **Portes** : à la fin de chaque mois, les critères des PDF, mesurés quand Sweep le peut ; le trader décide : passer
  au mois suivant, ou refaire les semaines 3 et 4 (le parcours se décale, rien n'est perdu).
- **Données** : une table `game_gameplan` (uid, départ, parcours A ou B, missions faites, portes), créée seule comme les
  autres tables du jeu. Aucune donnée de trade modifiée.

## Étapes (une à la fois, tests à chaque étape)
1. **Le modèle** : le contenu dans l'app (3 langues, extrait du site), la table, l'état (`GET api/game/gameplan`),
   démarrer, cocher une mission, l'XP, l'accès Pro. Tests PHP.
2. **L'inscription** : une question, « Depuis combien de temps tu trades ? » ; moins de 6 mois → le parcours proposé,
   avec le choix A (simulation) ou B (déjà en évaluation), puis le premier compte comme avant.
3. **Le parcours en mode jeu** : la mission du jour sur Aujourd'hui ; la feuille de mission (ce qu'il faut faire, la
   notion qui sert ce jour-là, « C'est fait quand », XP) ; la carte des 90 jours (mois, semaines, jours faits, à
   rattraper, à venir) ; les célébrations.
4. **Sweep valide seul** les missions mesurables, et **les portes** de fin de mois.
5. **Free et réglages** : l'aperçu verrouillé et la mise à niveau ; arrêter ou recommencer le parcours (Réglages).
6. **Apprendre en jouant** : de courts quiz sur les missions « Apprendre » (le setup, les maths du risque, les règles
   de la firme), corrigés tout de suite.
7. **Finition** : 390 et 1300, 3 langues, suite complète, CI, livraison.
