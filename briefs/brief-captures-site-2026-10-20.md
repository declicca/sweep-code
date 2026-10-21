# Brief — captures et vidéos de l'app pour le site et le kit d'inscription (20 octobre 2026)

**À qui** : la session App (ou Mateo).

**Ce brief est complet** : il remplace ceux du 13 et du 16 octobre (`brief-captures-site-2026-10-13.md`, `brief-captures-site-2026-10-16.md`). Il n'y a rien d'autre à lire.

**Pourquoi** : depuis le 15 octobre au soir, l'app a son look « esprit iOS ». Toutes les captures et vidéos du site montrent encore l'ancienne interface. Un visiteur voit une app sur le site, puis en découvre une autre en s'inscrivant.

**L'inventaire** vient du site construit, revérifié le 20 oct. : chaque fichier listé est réellement affiché, sur au moins une page. Les seuls ajouts sont 4 écrans nouveaux, pour des pages qui n'ont aucune image. Rien d'autre n'est demandé.

Travaille en autonomie et livre en une fois, ou par lots (voir « Livraison »). Ne touche pas au code du site.

## Quand les faire

**Après le chantier design de l'app** (l'alignement sur le site), s'il est en cours ou prévu. Sinon, il faudrait refaire les 100 et quelques fichiers à la fin du chantier. Si aucun chantier design n'est prévu, fais-les maintenant.

## Règles pour tout ce qui suit

- **Interface actuelle** (après la refonte du 15 oct.), **thème foncé**.
- **Données d'exemple** : le trader « Alex », les comptes de démonstration (Topstep XFA 50K, Apex PA 50K, LucidFlex 50K, Trading Combine 150K…). Aucun vrai nom, courriel ni chiffre d'un vrai trader.
- **Langues** :
  - fichiers des dossiers `captures/en` et `captures/fr` : en anglais et en français (l'espagnol reprend l'anglais) ;
  - fichiers `mobile-…` et `desktop-…` du dossier `img/` : en anglais, en français et en espagnol.
  - Chaque version est entièrement dans sa langue, avec les montants au format de la langue (« 1 571,60 $ » en français).
- **Même nom de fichier, même taille exacte** que l'actuel : le code du site ne change pas.
- **Format** : WebP, qualité visuelle équivalente. Les actuels pèsent environ 50 à 60 Ko pour un téléphone et 80 à 100 Ko pour un ordinateur.
- **Taille pleine seulement** : la session Site fait les copies réduites (`-600`, `-1200`, `-540`, `-960`) avec `cwebp`.
- **Heures crédibles** : un jour de semaine, pendant la séance de New York. Les heures du calendrier économique doivent être cohérentes avec les annonces montrées.
- **Quantower peut être montré.** Le site l'annonce partout depuis le 18 oct. (`/quantower`).
- **Les forfaits** : si un écran montre la page des forfaits ou une fenêtre de mise à niveau, il suit les limites du site (brief des forfaits du 18 oct.) :
  - Free garde 2 comptes ; Pro et Elite ont des comptes illimités ;
  - messages Sweep AI : 3, 50 et 200 par jour ;
  - trades lus depuis une capture : 3 par jour en Free, sans limite en Pro et Elite.
- **Le Plan du jour et le coach** : depuis le 17 oct., la case « budget de risque du jour » n'est plus dans le formulaire. Il reste la ligne du coach, « il te reste X ». Aucune capture ne doit montrer l'ancienne case.
- **Montrer ce que la page dit** (colonne « Ce qu'il doit montrer ») : c'est la phrase à côté de laquelle la capture est affichée.

---

## 1. Téléphone — 900 × 1948 px, `website/static/img/captures/en/` et `/fr/` (33 écrans × 2 langues)

| Fichier | Pages du site | Ce qu'il doit montrer |
|---|---|---|
| `v6-01-today-m.webp` | Accueil, Fonctionnalités, À propos, Nouveautés… | Aujourd'hui : la journée, la routine du jour avec le coach, les comptes |
| `v6-03-log-by-screenshot-m.webp` | Fonctionnalités, Nouveautés, /100 | Un trade ajouté depuis une capture d'écran, prérempli, à vérifier |
| `v6-04-discipline-psychology-m.webp` | Fonctionnalités, Suivi des comptes prop | La revue de 60 secondes (discipline et psychologie) |
| `v6-05-log-by-hand-m.webp` | Fonctionnalités | Le formulaire de trade à la main (« un ticket qui fait les calculs ») |
| `v6-06-trade-review-m.webp` | Fonctionnalités, Sweep AI, Comment ça marche | La fiche d'un trade avec l'avis sur le trade (« Réponds au coach ») |
| `v6-07-stats-m.webp` | Fonctionnalités, /100 | Les statistiques sur téléphone (filtres sur une ligne) |
| `v6-08-payout-conditions-m.webp` | Accueil, Suivi des comptes prop, Nouveautés, pages des firmes… | Les conditions de payout d'un compte prop, avec le compteur « prêt pour le payout » et « Payout 3 sur 6 » |
| `v6-10-journal-m.webp` | Fonctionnalités | Le journal : le plan avant l'ouverture, la revue après la clôture |
| `v6-11-calendar-m.webp` | Journal gratuit, /100 | Le calendrier P&L |
| `v6-12-payouts-m.webp` | Accueil, Fonctionnalités, Nouveautés | Mon argent : payouts, dépenses, net réel |
| `v6-13-accounts-m.webp` | Fonctionnalités, Comment ça marche, Suivi des comptes prop | Les comptes, chacun avec les règles de sa firme |
| `v6-17b-share-one-payout-m.webp` | Suivi des payouts | Un payout reçu, prêt à partager |
| `v6-18-add-trade-choice-m.webp` | Importer tes trades | Le choix : par capture, avec tes mots ou par fichier |
| `v6-20-signup-m.webp` | Comment ça marche, Installer sur ton téléphone | La création de compte |
| `v6-22-today-swept-m.webp` | Accueil, Comment ça marche | Aujourd'hui avec les 3 étapes faites : « Journée balayée » |
| `v6-23-discipline-checklist-m.webp` | Fonctionnalités | La revue d'un trade en 4 étapes (checklist de discipline) |
| `v6-24-new-trade-filled-m.webp` | Accueil, Sweep AI, Fonctionnalités | Sweep AI qui transforme une phrase en brouillon de trade |
| `v6-25-new-trade-empty-m.webp` | Sweep AI | Un nouveau trade, avant d'être rempli (même écran que le précédent, vide) |
| `ecran-parcours.webp` | Comment ça marche | Le parcours : XP, niveaux, rangs |
| `ecran-boss-revenge.webp` | Comment ça marche | Un boss tiré des habitudes (ex. « Le Revenge »), pourquoi, comment le battre |
| `ecran-revue-semaine.webp` | Comment ça marche, Sweep AI | Le bilan du vendredi et son coffre |
| `ecran-edge-reveal.webp` | Accueil, Comment ça marche | Edge Reveal : une vérité tirée des trades (ex. le meilleur créneau) |
| `ecran-saison.webp` | Comment ça marche | La saison du mois, ses paliers et ses récompenses |
| `ecran-badges.webp` | Comment ça marche | Les badges débloqués et à débloquer |
| `ecran-ligue.webp` | Comment ça marche | Le classement de la ligue de la semaine, avec la zone de promotion (Alex dans la liste) |
| `ecran-crew.webp` | Comment ça marche | La crew : l'objectif de la semaine et le fil d'activité |
| `ecran-plan-du-jour.webp` | Fonctionnalités | La feuille « Plan du jour » : biais, setups, perte max, niveaux (sans l'ancienne case « budget de risque du jour ») |
| `ecran-wrapped-1.webp`, `-2`, `-3` | Comment ça marche | Les 3 premiers écrans du Wrapped du mois |
| **Nouveau** `ecran-connexions.webp` | `/quantower`, `/ninjatrader`, Importer | Réglages › Données › Connexions : NinjaTrader 8 et Quantower connectés (« Add-on vu il y a 2 min »), 3 comptes trouvés, dont 2 reliés à leur compte Sweep |
| **Nouveau** `ecran-coach.webp` | Fonctionnalités (section « Ton coach ») | Le coach au moment d'ajouter un trade : la ligne « Dans ton edge » et « il te reste X » avant la limite du jour |
| **Nouveau** `ecran-edge-profil.webp` | Fonctionnalités (section « Ton coach », point « Ton edge ») et le coach de l'accueil | La carte du profil edge dans Stats : les conditions où Alex gagne, tirées de ses 8 dernières semaines |

## 2. Ordinateur — 2400 × 1500 px, `website/static/img/captures/en/` et `/fr/` (15 écrans × 2 langues)

| Fichier | Pages du site | Ce qu'il doit montrer |
|---|---|---|
| `v6-01-today-d.webp` | Accueil, Fonctionnalités, À propos, Nouveautés… | Aujourd'hui sur ordinateur, avec un trade copié sur plusieurs comptes |
| `v6-04-discipline-psychology-d.webp` | Fonctionnalités, Suivi des comptes prop | Les analyses de discipline |
| `v6-05-log-by-hand-d.webp` | Fonctionnalités | Le formulaire de trade à la main |
| `v6-06-trade-review-d.webp` | Fonctionnalités | Un trade sur un vrai graphique CME (entrée, sortie, stop, cible, résultat en R) |
| `v6-07-stats-d.webp` | Fonctionnalités, Kit presse | Les statistiques (« trouve ton edge dans tes chiffres ») |
| `v6-08-payout-conditions-d.webp` | Accueil, Kit presse, Nouveautés, pages des firmes… | Les conditions de payout d'un compte prop (comme sur téléphone) |
| `v6-11-calendar-d.webp` | Journal gratuit | Le calendrier P&L et le journal du jour |
| `v6-12-payouts-d.webp` | Accueil, Fonctionnalités, Nouveautés | Mon argent : payouts, dépenses, net réel, « Exporter » en haut |
| `v6-13-accounts-d.webp` | Fonctionnalités, Suivi des comptes prop, pages des firmes | Les comptes avec les règles de leur firme |
| `v6-17b-share-one-payout-d.webp` | Suivi des payouts | Un payout reçu, prêt à partager |
| `v6-18-add-trade-choice-d.webp` | Importer tes trades | Le choix : par capture, avec tes mots ou par fichier |
| `v6-22-today-swept-d.webp` | Accueil | Aujourd'hui, la journée balayée, le coach dans la routine |
| `v6-24-new-trade-filled-d.webp` | Accueil, Sweep AI, Fonctionnalités | Le trade rempli par Sweep AI |
| `v6-25-new-trade-empty-d.webp` | Accueil, Sweep AI | Le même écran, vide |
| **Nouveau** `v6-26-connections-d.webp` | `/quantower`, `/ninjatrader` | Les connexions sur ordinateur (comme `ecran-connexions`), avec la feuille « Relier mes comptes » ouverte (tous d'un coup) |

Sur l'accueil, les n° 25 puis 24 se succèdent, en fondu, au défilement : ils doivent être exactement le même écran, vide puis rempli.

## 3. Captures `mobile-…` (786 × 1704) et `desktop-…` (2400 × 1500), `website/static/img/`, en EN, FR et ES

| Fichier (`{en,fr,es}`) | Pages du site | Ce qu'il doit montrer |
|---|---|---|
| `mobile-{lang}-dark-ask-sweep-786.webp` | Accueil, Sweep AI, Fonctionnalités | Ask Sweep qui répond à partir des trades |
| `mobile-{lang}-dark-calendar-786.webp` | Calendrier économique | Le calendrier P&L avec les annonces du jour |
| `mobile-{lang}-dark-economic-calendar-786.webp` | Accueil, Calendrier économique | Les annonces économiques de la semaine (**FR et ES manquants aujourd'hui**) |
| `mobile-{lang}-dark-news-impact-report-786.webp` | Calendrier économique, Sweep AI, Fonctionnalités | Le récap d'une annonce, une minute après sa publication |
| `desktop-{lang}-dark-calendar-2400.webp` | Calendrier économique | Le calendrier P&L avec les annonces |
| `desktop-{lang}-dark-economic-calendar-2400.webp` | Calendrier économique | Le calendrier économique (**FR et ES manquants aujourd'hui**) |
| `desktop-{lang}-dark-news-impact-report-2400.webp` | Calendrier économique, Sweep AI | Le récap d'une annonce |

Les versions FR et ES manquantes :
- sur la page Calendrier économique, le site les prendra tout seul dès qu'elles existent (il retombe sur l'anglais sinon) ;
- sur l'accueil, l'image vise le fichier anglais : la session Site changera cette ligne à l'intégration.

## 4. Cartes de partage

| Fichier | Taille | Où | Ce qu'elle doit montrer |
|---|---|---|---|
| `captures/{en,fr}/carte-journee-balayee.webp` | 900 × 1600 | Fonctionnalités | La carte « Journée balayée » |
| `captures/{en,fr}/carte-payout.webp` | 900 × 1600 | Fonctionnalités | La carte « Prêt pour le payout » |
| `captures/{en,fr}/carte-wrapped.webp` | 900 × 1600 | Fonctionnalités | La carte Wrapped, sans montants |
| `img/share-net-1080.webp` | 1080 × 1920 | Suivi des comptes prop | La carte « Net après frais », données d'exemple |
| `img/share-payout-1080.webp` | 1080 × 1350 | Fonctionnalités, Suivi des comptes prop | La carte « Payout reçu » |
| `img/share-trade-1080.webp` | 1080 × 608 | Fonctionnalités | La carte d'un trade, format large |
| `img/share-weekly-hidden-1080.webp` | 1080 × 1350 | Fonctionnalités | Le bilan de la semaine, montants masqués |

Depuis le 14 octobre, chaque fenêtre de partage s'ouvre sur la carte Discipline, avec « Afficher les montants » éteint. Si le dessin des cartes a changé avec la refonte, refais-les ; sinon, ces 7 fichiers peuvent rester.

## 5. Vidéos (sans son)

**Une seule source par vidéo** : MP4, H.264, sans son. La session Site a `ffmpeg` : elle fait le 720p, le WebM et les aperçus (`-poster.webp`).

| Fichier à livrer | Taille, durée | Où | Ce qu'elle doit montrer |
|---|---|---|---|
| `video/hero-loop.mp4` | 1920 × 1080, environ 14 s, en boucle | Accueil, en haut | Sweep en action : ta journée, un trade ajouté en quelques secondes, tes règles, chaque trade, payout prêt, ta progression |
| `video/tour.mp4` | 1920 × 1080, 60 s | Accueil, Fonctionnalités, Comment ça marche (« Voir la visite en 1 min ») | La visite du produit en une minute |
| `captures/{en,fr}/v6-video-today-phone.mp4` | 780 × 1688, environ 24 s | Comment ça marche (« Balaye ta journée ») | Aujourd'hui sur téléphone : anneaux, jours, annonces |

**Facultatif** : une vidéo des anneaux, `captures/{en,fr}/v6-video-rings-phone.mp4`, en 780 × 1688, de 8 à 15 s. Elle montre la carte Aujourd'hui, la revue de 60 secondes enregistrée, puis les 3 anneaux fermés et « Journée balayée ». Le site la mettrait à la place de la vidéo d'Aujourd'hui dans « Balaye ta journée ».

## 6. Kit d'inscription (`marketing/listing-kit/images/`)

Rien à faire de plus : la session Site tire les 5 images (PNG, 1270 × 793) des nouvelles captures d'ordinateur, qui ont les mêmes proportions.
- 01 ← `v6-01-today-d`
- 02 ← `v6-08-payout-conditions-d`
- 03 ← `v6-24-new-trade-filled-d`
- 04 ← `v6-13-accounts-d`
- 05 ← `v6-07-stats-d`

## 7. N'est plus demandé

- `ecran-trades-ordi.webp` (brief du 13 oct.) : le site ne l'affiche plus.

---

## Livraison

- **Où déposer** : les fichiers, sous les mêmes noms, dans `website/static/img/captures/en/`, `.../fr/`, `website/static/img/` et `website/static/video/`. Sinon, envoie-les à Mateo. Ne touche pas au code du site.
- **Ce que fait la session Site** :
  - les copies réduites des images ;
  - le 720p, le WebM et les aperçus des vidéos ;
  - la place des 4 nouveaux écrans dans les pages ;
  - les 5 images du kit d'inscription ;
  - la vérification de chaque page sur téléphone et sur ordinateur, en clair et en sombre ;
  - la mise en ligne, avec l'accord de Mateo.
- **En une fois ou par lots** : les deux marchent. Si tu fais des lots, commence par les écrans les plus vus :
  - `v6-08-payout-conditions` (30 pages) ;
  - `v6-01-today` (15) ;
  - `v6-12-payouts` (15) ;
  - `v6-13-accounts` ;
  - `v6-24` et `v6-25` (l'accueil) ;
  - puis la vidéo du haut de l'accueil.
- **Total** :
  - 66 écrans de téléphone et 30 d'ordinateur (dont 4 écrans nouveaux en 2 langues) ;
  - 21 captures `mobile-` et `desktop-`, dont 4 qui n'existent pas encore (FR et ES du calendrier économique) ;
  - jusqu'à 7 cartes de partage ;
  - 3 vidéos, une source chacune (plus la vidéo facultative des anneaux).
