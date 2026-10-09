SWEEP — makeitsweep.com · sources du site (v15)

Contenu
  src/      générateur Python : build.py, core.py, pages1…16.py, legal.py, styles.css, site.js
            src/data/ : calendrier économique 2026-2027, robots.txt, llms.txt
  static/   fichiers copiés tels quels : img/ (captures EN et FR), video/, fonts/, icons/,
            social/ (images de partage), press/ (kit presse), templates/ (PDF)
  legacy/   anciens styles.css et site.js non versionnés, recopiés par build.py
            pour les pages HTML encore en cache chez certains visiteurs

Générer le site
  Python 3.12 ou plus récent, aucune dépendance externe.
    cd src
    python3 build.py
  Le site est écrit dans ../dist/ (dossier recréé à chaque génération).
  Les fichiers de static/img et static/video qu'aucune page n'utilise sont retirés
  de dist/ à la fin de la génération (static/ n'est jamais modifié).

Mettre en ligne
  Envoyer le contenu de dist/ dans /home/matnsabc/makeitsweep.com/ (fichiers cachés
  compris : .htaccess, fr/.htaccess, es/.htaccess), puis vider le cache NGINX.
  Depuis la racine du dépôt, ./deploy.sh website --go fait les deux.

Réglages utiles (src/core.py)
  COHORT_FLOOR   minimum affiché par le compteur de la cohorte (0 = valeur réelle seulement)
  STATS_MIN      nombre de trades à partir duquel la bande d'activité apparaît (250)
  UTM_CAMPAIGN   valeur utm_campaign ajoutée aux liens d'inscription
  src/pages9.py  GAME_LIVE : False affiche « Bientôt » sur la gamification
  src/pages11.py IMPORT_CSV : plateformes présentées avec un import CSV
