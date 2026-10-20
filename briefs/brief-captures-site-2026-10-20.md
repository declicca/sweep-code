# Brief : nouvelles captures pour le site (mise à jour du 20 octobre 2026)

**À qui** : la session App.

**Base** : `briefs/brief-captures-site-2026-10-16.md` reste la liste à produire : ses règles, ses tableaux de fichiers, ses tailles, ses noms. Revérifiée aujourd'hui sur le site construit : les mêmes 71 fichiers sont affichés, rien de plus, rien de moins. Ce brief ne dit que ce qui change.

Travaille en autonomie et livre en une fois (ou par lots, voir l'ordre dans le brief du 16 oct.). Ne touche pas au code du site.

## 1. Quand les faire

**Après le chantier design de l'app** (l'alignement sur le site), s'il est en cours ou prévu. Sinon, il faudrait refaire les 100 et quelques fichiers à la fin du chantier. Si aucun chantier design n'est prévu, fais-les maintenant.

## 2. Ce qui change par rapport au brief du 16 oct.

- **Quantower peut être montré.** Le site l'annonce partout depuis le 18 oct. (`/quantower`). La règle « pas de Quantower à l'écran » est levée.
- **Les forfaits** : si un écran montre la page des forfaits ou une fenêtre de mise à niveau, il doit suivre le brief des forfaits du 18 oct. :
  - Free garde 2 comptes ;
  - Pro et Elite ont des comptes illimités ;
  - messages Sweep AI : 3, 50 et 200 par jour ;
  - captures lues : 3 par jour en Free, sans limite en Pro et Elite.
- **Les vidéos** : la session Site a maintenant `ffmpeg`. Livre une seule source par vidéo, en MP4 1920 × 1080, H.264, sans son. La session Site fait le 720p, le WebM et les aperçus.
  - `video/hero-loop` : environ 14 s, en boucle ;
  - `video/tour` : 60 s ;
  - `captures/{en,fr}/v6-video-today-phone` : 780 × 1688, environ 24 s.
- **Le Plan du jour et le coach** : depuis le 17 oct., la case « budget de risque du jour » n'est plus dans le formulaire. Il reste la ligne du coach, « il te reste X ». Aucune capture ne doit montrer l'ancienne case.

## 3. Écrans nouveaux (les pages qui n'ont aucune image)

Même règles que le reste : thème foncé, trader « Alex », données d'exemple, montants au format de la langue, en EN et en FR.

| Fichier | Taille | Pages du site | Ce qu'il doit montrer |
|---|---|---|---|
| `captures/{en,fr}/ecran-connexions.webp` | 900 × 1948 (téléphone) | `/quantower`, `/ninjatrader`, Importer | Réglages › Données › Connexions : NinjaTrader 8 et Quantower connectés (« Add-on vu il y a 2 min »), 3 comptes trouvés, dont 2 reliés à leur compte Sweep |
| `captures/{en,fr}/v6-26-connections-d.webp` | 2400 × 1500 (ordinateur) | `/quantower`, `/ninjatrader` | La même chose sur ordinateur, avec la feuille « Relier mes comptes » ouverte (tous d'un coup) |
| `captures/{en,fr}/ecran-coach.webp` | 900 × 1948 | Fonctionnalités (section « Ton coach ») | Le coach au moment d'ajouter un trade : la ligne « Dans ton edge » et « il te reste X » avant la limite du jour |
| `captures/{en,fr}/ecran-edge-profil.webp` | 900 × 1948 | Fonctionnalités (section « Ton coach », point « Ton edge ») et le coach de l'accueil | La carte du profil edge dans Stats : les conditions où Alex gagne, tirées de ses 8 dernières semaines |

La session Site place ces 4 écrans dans les pages à l'intégration. Ils ne remplacent aucun fichier.

## 4. Livraison

- **Où** : sous les mêmes noms, dans `website/static/img/captures/en/`, `.../fr/`, `website/static/img/` et `website/static/video/`. Sinon, envoie-les à Mateo.
- **Ce que fait la session Site** :
  - les copies réduites, le 720p, le WebM et les aperçus des vidéos ;
  - la place des 4 nouveaux écrans ;
  - les 5 images du kit d'inscription ;
  - la vérification sur téléphone et sur ordinateur, en clair et en sombre ;
  - la mise en ligne, avec l'accord de Mateo.
- **Total** : celui du brief du 16 oct., plus les 4 nouveaux écrans en 2 langues (8 fichiers). Les vidéos ne demandent plus qu'une source chacune.
