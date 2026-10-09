# Site vitrine — makeitsweep.com

## Technique
- Générateur de site statique en Python, 180+ pages en EN / FR / ES.
- Sources dans `src/` : `core.py` (structure, nav, footer), `pages*.py` (contenu), `build.py` (build), `styles.css`, `site.js`. Fichiers statiques dans `static/`.
- Build : `cd src && python3 build.py` → résultat dans `dist/`. Ne jamais modifier `dist/` à la main.
- `sweep-count.php` lit le nombre de traders dans la base de l'app (compteur de la cohorte fondatrice).
- Permissions : dossiers 755, fichiers 644.

## SEO
- URLs propres sans `.html`, sitemap, hreflang, données structurées.
- Cibles : « trading journal », « best trading journal », « alternative à TradeZella » et autres plateformes, y compris dans les réponses des IA.

## Avant chaque livraison
Lancer l'audit Playwright de toutes les pages (mobile et ordinateur) : erreurs console, ressources brisées, débordement horizontal, ID en double, ancres brisées, alt manquants, longueur des titres et descriptions.

## À faire connu
Le footer et la page d'accueil utilisent encore les anciens slogans : remplacer par « Your edge, finally in one place. »
