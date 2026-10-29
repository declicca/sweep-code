# Tour du 29 oct. 2026 : à corriger (pour la session App)

Version testée : `b035b6d`, celle qui est en ligne.

Conditions :
- un nouveau trader en français sur téléphone (Topstep 50K, « Moins de 6 mois », 3 h 49 à New York, avant l'ouverture) ;
- un trader avec historique en anglais, sur ordinateur et téléphone, en clair et en foncé, sur 11 écrans.

Aucune erreur JavaScript.

**Vérifié et bon** :
- le plan du débutant à 500 $ et 3 trades ;
- la liste des trades par jour (1 557 px au lieu de 7 822) ;
- « Ton solde sur Topstep ? » dans la revue ;
- Stats sous 5 trades ;
- le lot 1 du design : coins de « My money », « 67% », les trois pastilles, barres plates ;
- l'émotion qui reste cochée ;
- la page d'un trade plus courte.

| # | Où | Défaut | Correction |
|---|---|---|---|
| T1 | Bienvenue, de minuit à 9 h 30 (heure de New York) | « Prépare ta séance de demain », « Ton plan de demain », alors que le plan qui s'ouvre est celui d'aujourd'hui (« Plan du jour jeudi 29 octobre »). | Avant l'ouverture, le même jour : « ta séance d'aujourd'hui », « Ton plan du jour ». « Demain » seulement après la fermeture. |
| T2 | Revue du jour (« Fermer ma journée ») | 4 questions, dont 3 disent la même chose : « As-tu suivi ton plan ? », « Discipline 1 à 5 », « Ta note A à F », puis le solde. | On garde « As-tu suivi ton plan ? » et le solde. La discipline et la note restent préremplies d'après la journée, sous « + Détails ». Un toucher de moins à chaque fermeture, si rien n'est changé. |
| T3 | Revue du jour, le coach | « 0 trade sur 1 sans erreur. » | « Aucun trade sans erreur aujourd'hui (1 trade). » Et au singulier comme au pluriel, en EN, FR et ES. |
| T4 | Aujourd'hui, après le premier trade | « Discipline 0 % » quand la checklist du trade n'est pas faite : ça ressemble à une note, alors que rien n'a été répondu. | « — » tant qu'aucune checklist n'est remplie, comme avant le premier trade. |
| T5 | Aujourd'hui sur téléphone, un trade de la nuit | La ligne du trade affiche « session of Oct 29 · entered on t… » au lieu de l'heure et du setup. | La même ligne que les autres trades : l'heure, puis le setup. |
| T6 | La page d'un trade | Le setup se choisit encore dans un champ texte (« Liquidity sweep ») ET dans les puces (« Liquidity Sweep », avec une autre majuscule). | Les puces seulement, avec « + Autre » pour en taper un. Une seule écriture du nom. |

**Fini quand** : les 6 points ne se voient plus, en EN, FR et ES, à 390 et 1300, en clair et en foncé.
