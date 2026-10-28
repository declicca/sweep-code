# Brief pour la session App : un journal complet, même quand le trader ne note pas ses pertes (27 oct. 2026)

**De** : la session stratégie et tests. **Pour** : la session d'exécution.

**Le problème (Mateo, 27 oct.)** : un des problèmes les plus fréquents, c'est que les traders notent leurs trades gagnants, mais pas leurs trades perdants.

**Pourquoi** : noter une perte, c'est la revivre et la rendre officielle. Tant que le journal dépend de ce choix, il restera trop beau. Il est alors faux partout où il compte : « Il te reste… », la marge de drawdown, la consistance, les stats et le coach.

**Le principe** : le journal se complète sans demander de courage. **Un seul chiffre par jour, le solde de la plateforme, ferme l'écart.** Le détail des trades reste bienvenu, mais il n'est plus nécessaire pour que les chiffres soient justes.

**Ce qui existe déjà** :
- « Recalibrer sur ta plateforme » (`src/nav.js`, la section « account: recalibrate ») : le trader tape le solde de sa plateforme, et Sweep enregistre la différence comme un ajustement daté (`account.adjustments`).
- Cet ajustement compte dans le solde, le P&L du compte et la marge. Il ne compte pas dans les stats des trades.
- Il est caché dans les réglages d'un compte. Personne ne le voit.

**Place dans l'ordre** : après la correction R1 du brief « nouveau trader ». Avant ses étapes 3 et 4, et avant les étapes C à F du brief d'activation.

Les règles de travail restent les mêmes : une étape à la fois, la suite complète à 0 échec, la CI verte, `CONTEXTE-APP.md` à jour, EN / FR / ES, 390 et 1300, et aucun déploiement sans l'accord de Mateo.

---

## Étape 1 — Mesurer avant de changer

Dans Admin › Métriques, une carte « Journal complet », sur 7 et 30 jours :

| Indicateur | Ce qu'il dit |
|---|---|
| Part des traders d'au moins 20 trades avec plus de 80 % de réussite | Le signe le plus simple de pertes oubliées. |
| Part des trades perdants parmi tous les trades | Chez des traders réels, on attend 40 à 55 %. |
| Part des jours de trading sans aucun trade perdant | Idem, jour par jour. |

À partir de l'étape 2, on ajoute :
- la part des journées fermées avec un écart ;
- le montant total des écarts ;
- la part des écarts que le trader a détaillés en trades.

Ces chiffres sont aussi dans « Exporter pour Claude ». Pas de nom de trader.

**Fini quand** : la carte affiche les trois premiers chiffres sur la base de démonstration, avec un test calculé à la main (comme `metrics_test.php`).

---

## Étape 2 — « Fermer ma journée » vérifie le solde de la plateforme

**À la fermeture de la journée**, pour chaque compte actif qui a eu des trades aujourd'hui (ou, au plus une fois par semaine, un compte qui n'en a pas eu depuis 3 jours de trading) :

1. **Une ligne de plus dans la revue** : « Ton solde sur Topstep ? », préremplie avec le solde dans Sweep.
   - **« C'est le même »** : un toucher, le cas normal.
   - **Un autre solde** : le trader le corrige, ou colle une capture de la page du compte de sa plateforme ; la lecture des captures existe déjà.
2. **S'il y a un écart**, la feuille dit, sans juger : « Il manque −340 $ entre ta plateforme et ton journal. C'était quoi ? » Puis trois puces :
   - **Des trades pas notés** : l'écart devient un trade « Trades non détaillés », daté du jour, sur ce compte.
     - Il compte dans le P&L, le calendrier, le taux de réussite du jour et les règles de la firme : marge, consistance, objectif, jours gagnants.
     - Il n'a ni instrument, ni setup, ni checklist.
     - Il se détaille plus tard (« Ajouter le détail »), et ce qui est détaillé sort de la ligne.
   - **Des frais** : un ajustement de frais (le recalibrage actuel), qui va aussi dans Mon argent.
   - **Un payout** : on ouvre l'ajout de payout prérempli.
3. **Les comptes synchronisés** (add-ons NinjaTrader 8 et Quantower) sautent cette ligne s'ils ont reçu des exécutions aujourd'hui.

**« Recalibrer » dans les réglages du compte** reste, pour les cas hors journée, et il propose les mêmes trois puces.

**Fini quand** :
- une journée sans écart ne coûte qu'**un toucher de plus** (mesuré dans `MESURE-BOUCLE.md`) ;
- une journée avec un gain noté de +150 $ et un solde de plateforme de −190 $ donne une ligne « Trades non détaillés −340 $ ». Le P&L du jour, la marge, la consistance et « Maintenant » sont alors justes ;
- un compte synchronisé ne voit pas la ligne ;
- c'est vérifié en EN, FR et ES, à 390 et 1300.

---

## Étape 3 — Montrer ce que les pertes oubliées faussent

1. **Les stats** : tant qu'un écart reste « non détaillé », Stats et la page du compte affichent une ligne grise : « 340 $ non détaillés : ton taux de réussite et ta force/fuite ne les comptent pas. Ajouter le détail › ». Pas d'alerte or : c'est une information, pas une faute.
2. **Le coach**, quand le solde de la plateforme révèle un écart pour la première fois : « Ton journal disait qu'il te restait 1 150 $ avant ta perte max. Ta plateforme dit 810 $. C'est pour ça que chaque trade compte : je ne peux te protéger que de ce que je vois. » Une fois, pas à chaque écart.

**Fini quand** : avec un écart non détaillé, la ligne grise est sur Stats et sur la page du compte. Elle disparaît une fois l'écart détaillé. Le coach ne parle de l'écart qu'une fois par trader.

---

## Étape 4 — Noter une perte devient récompensé, et rapide

1. **La série et l'expérience (XP)** comptent les **journées fermées complètes** (solde vérifié, ou synchro), pas les journées gagnantes. Le texte de la série le dit : « Jours complets ».
2. **Le coach après une perte notée** :
   - dans le plan, avec le stop respecté : « Perte dans ton plan, stop respecté : c'est un bon trade. » ;
   - hors du plan : la phrase actuelle, sans parler du montant.
3. **Le formulaire après une perte** : quand le P&L tapé est négatif, la checklist et les émotions se replient sous « + Ajouter le contexte (facultatif) ». Le trade s'enregistre avec le seul montant.
4. **Un badge « Journal honnête »** : 5 journées de suite où le solde de la plateforme et le journal sont d'accord. Les badges existent déjà ; c'est une ligne de plus.

**Fini quand** :
- une perte se note en autant de touchers qu'un gain, ou moins ;
- la série d'un trader qui perd mais ferme sa journée continue ;
- le badge se débloque au 5ᵉ jour d'accord, dans le test.

---

## Après le brief

Deux semaines après la mise en ligne de l'étape 2 : comparer la carte « Journal complet » à la mesure de l'étape 1. La session stratégie et tests en fait le point dans `docs/parcours/`.

---

## Revue de l'étape 1 (28 oct., `fa916db` dans `058bf24`, CI verte)

**Validée** sur le rapport : la carte « Journal complet » existe sur 7 et 30 jours. `metrics_test.php` vérifie 4 traders calculés à la main : la copie comptée une fois, les données d'exemple et le compte interne exclus, et l'écart entre 7 et 30 jours.

**Le point de départ** : la fenêtre de 30 jours se calcule sur l'historique déjà en base. Les chiffres réels sont donc disponibles dès la mise en ligne de `058bf24`. Mateo les colle, et la session stratégie et tests les note dans `docs/parcours/MESURE-PERTES.md` avant de mettre l'étape 2 en ligne. L'étape 2 peut être développée en local tout de suite.
