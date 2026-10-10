# Sweep — contexte du projet

Sweep (Sweep Inc., Laval, Québec) : journal et système de performance pour traders futures / prop firms.
Slogan : « Your edge, finally in one place. » — soutien : hello@makeitsweep.com

## Structure du dépôt
- `app/` → app web, en ligne sur app.makeitsweep.com (voir app/CLAUDE.md et app/CONTEXTE-APP.md, qui fait foi pour l'app)
- `website/` → site vitrine makeitsweep.com (voir website/CLAUDE.md)
- `deploy.sh` → déploiement SSH vers le serveur (simulation par défaut)
- `marketing/` → textes et images pour les annuaires et lancements (non déployé)

## Serveur
- HostArmada, VPS Web Raider (cPanel/WHM), utilisateur cPanel `matnsabc`
- PHP seulement. Pas de Node.js, aucune étape de build npm, ne pas changer la stack.
- Secrets hors du web dans le dossier privé (`sweep-private`) : clés Gemini, Stripe, Databento. Ne jamais les lire, les afficher ni les mettre dans le dépôt. Fournir un fichier d'exemple avec des emplacements vides.

## Façon de travailler (Mateo)
- Langue : français. Code, noms de fichiers et commentaires en anglais.
- Proposer UNE seule option, la meilleure, pas un menu de choix.
- Aucun ajout non demandé. Évolution de l'existant, jamais une refonte.
- Gros chantiers : brief organisé en étapes, une étape développée à la fois.
- Prendre les décisions raisonnables soi-même plutôt que poser beaucoup de questions.
- Toujours tester sur ordinateur ET sur mobile avant de dire que c'est fini (voir « Tests »).
- Ne jamais présenter un travail comme final sans avoir relancé tous les tests.
- Fin de chaque tâche : liste exacte des fichiers créés/modifiés, migration SQL et tâche cron s'il y en a.
- Ne jamais déployer sans mon accord explicite.

## Design (identique app et site)
- Design system iOS, mobile d'abord : feuilles qui se ferment en glissant, filtres sur une ligne défilante.
- Palette : noirs neutres (ink #08080A), bleu #4C8DFF = gains et actions, or #D4A24C = pertes.
- Polices Geist / Geist Mono. Rayons : 10 / 14 / 20 / 26 / 32 px. Une seule courbe d'animation (spring).
- Thème clair/foncé selon le navigateur. Dégradés de fond très subtils. Pas de halo qui suit la souris.
- Épuré : peu de boutons, peu d'onglets, peu de clics.

## Langues
EN / FR / ES, choisie automatiquement selon le navigateur. Tout nouveau texte doit exister dans les 3 langues.

## Tests
- Playwright (Chromium) à deux tailles : mobile 390×844 (tactile) et ordinateur 1300×850, locale fr-CA.
- Vérifier : erreurs console, ressources brisées, débordement horizontal, rendu visuel par capture d'écran.
