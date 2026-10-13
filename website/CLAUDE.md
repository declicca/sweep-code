# Site vitrine — makeitsweep.com

## Technique
- Générateur de site statique en Python, 180+ pages en EN / FR / ES.
- Sources dans `src/` : `core.py` (structure, nav, footer, réglages comme `COHORT_FLOOR`, `STATS_MIN`, `UTM_CAMPAIGN`), `pages1.py` à `pages20.py` (contenu ; `pages17.py` : comparatifs ; `pages18.py` : pages des firmes et changements de règles ; `pages19.py` : règles comparées ; `pages20.py` : journal gratuit et suivis), `legal.py` (confidentialité, conditions, risques), `build.py` (build), `styles.css`, `site.js`. `src/data/` : calendrier économique 2026-2027, `robots.txt`, `llms.txt`.
- `src/presets.py` : règles des prop firms lues au build depuis l'app (`https://app.makeitsweep.com/api/presets`, vérifiées chaque semaine), jamais retapées dans le site. Copie dans `src/data/presets.json` (build sans réseau) et journal des changements de règles dans `src/data/presets-changes.json` : les committer quand ils changent. Seule une vérification plus récente que la copie est inscrite au journal ; quand l'app corrige son catalogue (seed vérifié à la main, même vérification ou plus ancienne), la copie suit sans rien inscrire. Le site n'affiche que les valeurs modifiées (ni ajoutées ni retirées), sur chaque page de firme et sur `/prop-firm-rule-changes`, avec son flux RSS `prop-firm-rule-changes.xml` écrit par `build.py`. `SWEEP_PRESETS_OFFLINE=1` pour un build sans réseau.
- `static/` : fichiers copiés tels quels (img, video, fonts, icons, social, press, templates, `site.webmanifest`).
- Images de partage par page (`og:image` des firmes, comparatifs, règles comparées et calculateurs) : `tools/og_images.py` les génère avec Playwright dans `static/social/og/<lang>/` (+ `manifest.json`). Outil de développement seulement. Le build signale quand une date de vérification a changé : relancer l'outil, puis committer les images.
- `legacy/` : anciens `styles.css` et `site.js` non versionnés, recopiés dans `dist/assets/` pour les pages encore en cache chez certains visiteurs.
- Build : `cd src && python3 build.py` → résultat dans `dist/` (recréé à chaque build, `.htaccess` compris ; les images et vidéos de `static/` qu'aucune page n'utilise sont retirées de `dist/`). Ne jamais modifier `dist/` à la main.
- Python 3.12 ou plus récent requis (f-strings avec guillemets échappés), aucune dépendance externe.
- Déploiement : `./deploy.sh website` depuis la racine du dépôt (racine du site sur le serveur : `/home/matnsabc/makeitsweep.com/`). Le cache NGINX est vidé automatiquement après un déploiement réel.
- `sweep-count.php` lit le nombre de traders dans la base de l'app (compteur de la cohorte fondatrice).
- Permissions : dossiers 755, fichiers 644.

## SEO
- URLs propres sans `.html`, sitemap, hreflang, données structurées.
- Cibles : « trading journal », « best trading journal », « alternative à TradeZella » et autres plateformes, y compris dans les réponses des IA.

## Avant chaque livraison
Lancer l'audit Playwright de toutes les pages (mobile et ordinateur) : erreurs console, ressources brisées, débordement horizontal, ID en double, ancres brisées, alt manquants, longueur des titres et descriptions.
