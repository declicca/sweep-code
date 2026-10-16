# Ton edge — réflexion et tâches (16 oct. 2026)

Réflexion produit à partir de l'app existante. Elle ne contient aucun code. Les tâches de la fin sont prêtes à donner aux conversations de développement, une à la fois.

## 1. Ce que Mateo veut

1. **Révéler l'edge du trader le plus tôt possible**, à partir de ses meilleurs trades, de ses séries gagnantes et des setups qui marchent pour lui.
2. **Le rappeler au bon moment : avant le prochain trade.** « Voici ce qui a fonctionné pour toi jusqu'ici. Keep doing what works. » Le trader se sent accompagné.
3. **Adapter les questions** (avant, pendant et après le trade, et dans la revue) au trader, pour que ses analyses et ses bilans deviennent de plus en plus pertinents.
4. **Évoluer en continu.** Le marché change et l'edge aussi : ce qui marchait peut s'user, de nouvelles pistes apparaissent.

## 2. Ce qui existe déjà

L'app calcule déjà beaucoup de choses, mais à des endroits séparés, avec des règles différentes, et presque toujours **après** le trade.

| Élément | Ce qu'il fait | Où on le voit | Limite |
|---|---|---|---|
| Force du coach (`strength`, `src/coach.js` l. 492-505) | Meilleure situation parmi : dans le plan / hors plan, meilleur setup, meilleur créneau de 30 min. Seuil : 5 trades de chaque côté, écart d'au moins 5 points | Tête de Stats (28 jours), bilan du vendredi | **Taux de gain seulement** (ni $ ni R), jamais avant un trade |
| Edge Reveal (`game/v2b.php` l. 180-295) | Meilleur créneau, setup, jour, effet du plan, conformité ; **R moyen**, 56 jours ; texte écrit une fois par Sweep AI | Écran 3 sur 4 du bilan hebdo (carte à retourner) | Il faut **20 trades avec stop** avant toute révélation. Free : une fois par mois. Bien caché |
| Wrapped mensuel (`game/v2c.php`) | Setup signature, créneau en or, émotion dominante | Pastille, le 1er du mois | Une fois par mois |
| Stats › Analyse détaillée (`src/app.js` ~l. 1136-1816) | Tables par setup, séance, heure, jour, émotions, discipline ; « À surveiller » (au moins 5 par groupe) | Page Stats | Il faut aller la chercher ; surtout des alertes |
| Tes propres chiffres (`own()`, coach l. 269-303) | Revanche, après 2 pertes, taille après des gains, 5 premières minutes | Avant le trade | **Uniquement ce qui coûte** |
| Séries gagnantes (`stats()`, `src/app.js` l. 641-651) | Série en cours, plus longue série gagnante (`maxWS`) et perdante | Seule la série en cours est affichée, dans « plus de chiffres » | `maxWS` calculé et jamais montré ; les **jours** gagnants de suite n'existent pas |
| Réponds au coach (`askHtml`, coach l. 629-643) | Une question ciblée selon ce que le coach a vu (stop, taille, émotion) | Page du trade | Seul endroit adaptatif |
| Checklist (`settings.questions`) | 13 questions par défaut, 5 actives, les 3 premières montrées | Formulaires | Fixe, la même pour tous les setups |
| Leçons (`ruleFor`, coach l. 378-384) | La dernière « chose à améliorer demain » devient la règle du plan suivant (7 jours) | Plan, Aujourd'hui | La leçon d'un **trade** ne revient jamais au prochain trade semblable |
| Sweep AI | Avis sur le trade (`setup_context`), analyse de la semaine, débrief du jour, Ask | Boutons « Aller plus loin » | Ses réponses ne sont pas réutilisées par l'app |

## 3. Diagnostic

1. **Quatre « edges » différents.** Le coach (taux de gain, 28 j), Edge Reveal (R moyen, 56 j), le Wrapped et Stats peuvent désigner des gagnants différents. Le trader ne sait pas lequel croire.
2. **L'edge n'apparaît jamais avant le trade.** Avant un trade, le coach ne dit que des avertissements. Le « keep doing what works » n'existe nulle part.
3. **Les données qui nourrissent l'edge manquent pour la plupart des trades** (voir l'audit des parcours) :
   - la saisie rapide n'a ni setup, ni stop, ni heure, ni sens fiable ;
   - Edge Reveal attend 20 trades avec stop ;
   - un trader comme Alex (saisie rapide) **ne verra jamais son edge**.
4. **Le taux de gain seul trompe.** Un setup à 70 % de gains avec de petits gains et de grosses pertes n'est pas un edge. Il faut le **résultat moyen par trade** (en R quand le stop est connu, sinon en $) et le nombre de trades.
5. **Rien ne vieillit.** Un setup excellent il y a trois mois et perdant depuis trois semaines reste « le meilleur ». Rien ne détecte une nouvelle piste non plus.
6. **Les séries gagnantes ne sont pas analysées.** Ce sont pourtant les moments où le trader « sent » son edge.
7. **Les questions ne s'adaptent pas.** Une question toujours « oui » depuis un mois reste en tête ; celle qui sépare les gagnants des perdants n'est pas mise en avant ; aucun setup n'a ses propres critères.

## 4. Principes

- **Une seule source de vérité.** Un seul calcul « Ton edge », utilisé partout : avant le trade, plan, Aujourd'hui, Stats, bilan, Edge Reveal, Wrapped.
- **Honnête sur l'échantillon.** Toujours le nombre de trades à côté du chiffre. Trois niveaux de confiance :
  - **Piste** : au moins 5 trades ;
  - **Tendance** : au moins 10 trades ;
  - **Confirmé** : au moins 20 trades, et positif sur les deux moitiés de la période.

  Jamais de promesse ni de prédiction : on décrit le passé du trader (cohérent avec « Not financial advice »).
- **Mesure** : résultat moyen par trade (R si stop, sinon $ par contrat) et taux de gain, sur une **fenêtre glissante de 8 semaines** avec plus de poids aux 4 dernières.
- **Sans IA, instantané, pour tous**, comme le coach. L'IA ne sert qu'à reformuler, en option, comme Edge Reveal aujourd'hui.
- **Positif d'abord, avant le trade.** Ce qui marche pour lui, puis l'avertissement s'il y en a un. Une ligne chacun.
- **Ne jamais bloquer** et ne rien écrire dans les trades sans l'accord du trader (règles décidées).

## 5. Le concept : « Ton edge », un profil vivant

### 5.1 Ce qu'est un edge

Une **condition gagnante** est une combinaison simple, d'une ou deux dimensions, qui donne un résultat moyen nettement meilleur que la moyenne du trader.

**Dimensions déjà disponibles** :
- setup ;
- créneau de 30 min ;
- séance ;
- jour de la semaine ;
- sens ;
- dans le plan / hors plan ;
- émotion avant ;
- premier ou deuxième trade de la journée ;
- après un gain ou après une perte ;
- instrument.

**Exemples** :
- « Opening range breakout entre 9 h 30 et 10 h »
- « Ton 1er trade du jour, dans ton plan »
- « NQ long quand tu es calme »

Le profil garde **3 conditions gagnantes au plus** et **1 fuite** (la condition la plus coûteuse, déjà calculée par le coach). Chacune a :
- son niveau (Piste / Tendance / Confirmé) ;
- son nombre de trades ;
- son résultat moyen ;
- la date de son dernier trade.

### 5.2 Où il apparaît

| Moment | Ce que voit le trader |
|---|---|
| **Plan du matin** | « Ce qui marche pour toi : ORB 9 h 30-10 h, +0,8 R en moyenne sur 14 trades. » Les setups gagnants sont proposés en premier dans « Mes setups ». |
| **Formulaire, avant le trade** | Ligne verte avant les avertissements. Si le trade en cours correspond (setup choisi, heure actuelle) : « Dans ton edge : ORB du matin, 9 gagnants sur 14. Garde ta taille habituelle. » Sinon, et seulement si l'edge est au moins « Tendance » : « Hors de ton edge habituel. » Sans reproche. |
| **Après le trade** | « Trade dans ton edge » rejoint la liste « ce qui était bien » du coach. |
| **Aujourd'hui** (carte du coach, matin) | La condition gagnante n° 1 et sa règle : « Keep doing what works : ton ORB avant 10 h. » |
| **Série gagnante** (3 trades gagnants de suite ou 3 jours verts de suite) | « Ta série : 4 gagnants de suite. Point commun : tous avant 10 h, tous dans ton plan. » |
| **Stats et bilan du vendredi** | La même carte, plus l'évolution : « Nouvelle piste : VWAP reclaim (6 trades, +0,6 R) », « En baisse : ton ORB, +0,1 R sur les 4 dernières semaines contre +0,9 R avant ». |
| **Edge Reveal** | Il lit le même profil au lieu de son propre calcul : moins de code, un seul edge. |

### 5.3 Évolution continue

- **Recalcul** à chaque trade (navigateur) et une fois par semaine côté serveur, pour le bilan et pour qu'un trader le retrouve identique sur tous ses appareils.
- **En baisse** : une condition qui passe sous la moitié de son résultat moyen sur les 4 dernières semaines (au moins 5 trades récents) est signalée, jamais retirée en silence.
- **Nouvelle piste** : une condition qui atteint 5 trades avec un écart net est annoncée une fois.

### 5.4 Questions qui s'adaptent

1. **Critères par setup.** Chaque setup peut avoir 1 à 3 critères d'entrée, écrits par le trader ou suggérés (« Cassure du range des 15 premières minutes », « Volume au-dessus de la moyenne »). Quand le trader choisit un setup sur le formulaire, ses critères remplacent les 3 questions génériques.
2. **Questions qui comptent.** Pour chaque question, on compare le résultat moyen des trades « oui » et « non » (au moins 5 de chaque). La question qui sépare le plus les gagnants des perdants passe en tête, avec la mention « Cette question sépare tes gagnants de tes perdants ».
3. **Questions acquises.** Une question répondue « oui » sur 95 % des trades depuis 4 semaines passe sous « Voir plus » avec la mention « acquise ». Elle revient si un « non » apparaît.
4. **Revue de trade orientée edge** (« Réponds au coach ») :
   - trade **dans** l'edge : « Qu'est-ce qui était pareil que d'habitude ? » ;
   - trade **hors** de l'edge : « Pourquoi ce trade hors de ton edge ? » ;
   - trade d'une **série** : « Qu'est-ce qui t'a mis dans cette série ? ».
5. **Leçons qui reviennent.** Avant un trade sur le setup X, la dernière leçon écrite sur un trade X : « Ta leçon du 14 oct. sur l'ORB : attendre la clôture de la bougie. »

## 6. Prérequis : des trades bien remplis

Sans données, il n'y a pas d'edge. Deux conditions passent avant tout le reste :
1. **L'étape 1 du brief de l'audit** (sens et heure sur la saisie rapide) : `briefs/brief-app-audit-parcours-2026-10-16.md`.
2. **Le setup en un toucher sur la saisie rapide** : une rangée de puces avec les setups du plan du jour d'abord, puis les autres. Facultatif, mais visible. C'est la donnée la plus utile à l'edge, et c'est aujourd'hui la plus souvent vide.

Le stop reste facultatif. L'edge se calcule en $ par contrat quand le R n'est pas connu, ce qui retire la barrière des « 20 trades avec stop ».

## 7. Tâches pour les conversations de développement

Ordre conseillé. Une tâche à la fois, avec l'accord de Mateo entre chacune.

Règles pour chaque tâche :
- textes en EN / FR / ES ;
- tests à 390 × 844 et 1300 × 850 ;
- `CONTEXTE-APP.md` mis à jour ;
- aucun déploiement sans accord.

### T1 — Le setup en un toucher sur la saisie rapide (S)
- **Problème** : la plupart des trades n'ont pas de setup, donc aucun edge par setup.
- **À faire** : une rangée de puces de setups sous le P&L de la feuille rapide (setups du plan du jour d'abord). Facultatif. Aussi sur le formulaire complet s'il ne l'a pas déjà en évidence.
- **Fichiers** : `src/nav.js` (feuille rapide, `saveOne`), `src/game.js` (`SUGGESTED_SETUPS`).
- **Test** : un trade rapide avec setup ⇒ `setup` enregistré, en 1 toucher de plus au plus.
- **Dépend de** : l'étape 1 du brief de l'audit.

### T2 — Le moteur « Ton edge », source unique (M)
- **À faire** :
  - fonction pure `SweepEdge.profile(trades, plans)` dans `src/coach.js` ;
  - jumelle PHP dans `game/`, pour la parité, sur le modèle `e2e_rule_parity`.
- **Calcul** :
  - conditions à 1 ou 2 dimensions (liste du § 5.1) ;
  - résultat moyen (R sinon $ par contrat) et taux de gain ;
  - fenêtre de 8 semaines, les 4 dernières pondérées ;
  - score « écart × √n » ;
  - niveaux Piste (5) / Tendance (10) / Confirmé (20, et positif sur les deux moitiés) ;
  - au plus 3 conditions gagnantes et 1 fuite ;
  - drapeaux « nouvelle » et « en baisse » (§ 5.3).

  Les copies comptent une fois. Les données d'exemple sont exclues.
- **Remplace** le calcul de `strength()` (coach) et de `candidates()` (Edge Reveal), qui lisent désormais le profil. Les textes et l'emplacement restent les mêmes.
- **Tests** : unitaires PHP sur des jeux de trades écrits pour le test, parité navigateur / serveur, et « pas assez de trades » en dessous de 5.

### T3 — L'edge avant le trade (S)
- **À faire** : dans `beforeHtml` (`src/coach.js` l. 419-444), une ligne positive **avant** les avertissements.
  - « Dans ton edge… » si le trade en cours correspond (setup choisi, heure de New York, plan) ;
  - sinon « Ce qui marche pour toi : … » ;
  - « Hors de ton edge habituel » seulement au niveau Tendance ou plus.
- Sur les deux formulaires, mise à jour quand le setup change.
- **Test** : `e2e_coach` — profil avec un ORB du matin ⇒ ligne verte sur un trade ORB à 9 h 45, ligne neutre à 14 h.
- **Dépend de** : T1 et T2.

### T4 — L'edge dans le plan et sur Aujourd'hui (S)
- **À faire** :
  - plan du matin : la ligne « Ce qui marche pour toi » et les setups gagnants en premier dans « Mes setups » (`src/game.js`, `openPlan`) ;
  - carte du coach d'Aujourd'hui avant la 1ʳᵉ séance : « Keep doing what works : … » (`src/coach.js`, carte Aujourd'hui).
- **Test** : `e2e_coach` et `e2e_plan_journal`.
- **Dépend de** : T2.

### T5 — Séries gagnantes expliquées (S)
- **À faire** :
  - à 3 trades gagnants de suite ou 3 jours verts de suite, une ligne du coach donne le point commun le plus fort (mêmes dimensions que T2) ;
  - afficher la plus longue série gagnante (`maxWS`, déjà calculée) dans Stats ;
  - ajouter les jours verts de suite.
- **Fichiers** : `src/coach.js`, `src/app.js` (`stats`, `metricsGrid`).
- **Test** : jeu de 4 gagnants avant 10 h ⇒ « Point commun : avant 10 h ».

### T6 — Évolution de l'edge dans Stats et le bilan (S)
- **À faire** :
  - tête de Stats et étape 0 du bilan du vendredi : la carte du profil (3 conditions, niveaux, n) et les lignes « Nouvelle piste » / « En baisse » ;
  - Edge Reveal reprend la même source.

  Le verrou Free d'Edge Reveal reste comme décidé. La carte du coach reste gratuite pour tous (règle « le coach est pour tous »).
- **Test** : `e2e_weekly_content` et `e2e_coach`.
- **Dépend de** : T2.

### T7 — Questions qui s'adaptent (M)
- **À faire** :
  1. **Critères par setup** : `settings.setup_rules = {setup: [{id, text}]}` (au plus 3), modifiables dans Réglages › Setups et en ligne sur le formulaire. Setup choisi ⇒ ses critères remplacent les 3 questions génériques. Les réponses vont dans `discipline.*`, comme aujourd'hui.
  2. **Ordre des questions** : la question qui sépare le plus les gagnants des perdants passe en tête, avec sa mention. Les questions « acquises » passent sous « Voir plus » (§ 5.4). Calculé, jamais enregistré : rien ne change dans les réglages du trader sans lui.
  3. **« Réponds au coach »** : la question de revue suit l'edge (dans / hors / série).
- **Fichiers** : `src/nav.js` (formulaires, `checklist`), `src/app.js` (Réglages), `src/coach.js` (`askHtml`).
- **Tests** : `e2e_trade_checklist` et `e2e_coach`.
- **Dépend de** : T2.

### T8 — Leçons qui reviennent au bon trade (S)
- **À faire** : avant un trade sur le setup X (ou au même créneau si pas de setup), la dernière leçon écrite (`review.lesson`) sur un trade semblable, dans les 30 derniers jours, sur une ligne de la carte « Avant ce trade ».
- **Fichiers** : `src/coach.js`.
- **Test** : une leçon écrite sur un ORB ⇒ visible sur le prochain ORB, pas sur un autre setup.

## 8. Décision de Mateo (16 oct.)

**« Ton edge » est gratuit pour tous**, comme le coach, dans tous les forfaits :
- la ligne avant le trade (T3) ;
- le plan et Aujourd'hui (T4) ;
- les séries gagnantes (T5) ;
- la carte du profil dans Stats et le bilan (T6) ;
- les questions adaptées (T7) ;
- les leçons qui reviennent (T8).

Ce qui reste payant, sans changement :
- Edge Reveal hebdomadaire (Free : une fois par mois) et sa formulation par l'IA ;
- l'historique complet dans Stats ;
- l'analyse IA de la semaine.

À noter dans `CONTEXTE-APP.md` (règles produit, forfaits) avec la tâche T3.
