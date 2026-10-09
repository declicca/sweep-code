#!/bin/bash
# Usage : ./deploy.sh app|website        -> simulation (rien n'est envoyé)
#         ./deploy.sh app|website --go   -> déploiement réel
set -e
export PATH="$HOME/.local/bin:$PATH"   # Python 3.12+ installed by uv
HOST="sweep"   # alias défini dans ~/.ssh/config
APP_REMOTE="/home/matnsabc/app.makeitsweep.com/"
WEBSITE_REMOTE="/home/matnsabc/makeitsweep.com/"

DRY="--dry-run"; [ "$2" = "--go" ] && DRY=""

case "$1" in
  app)
    rsync -avz $DRY \
      --exclude 'config.php' --exclude 'data/' --exclude 'error_log' \
      --exclude 'CLAUDE.md' --exclude 'CONTEXTE-APP.md' --exclude '.ftp-deploy-sync-state.json' \
      --exclude 'src/' --exclude 'tests/' --exclude 'tools/' \
      app/ "$HOST:$APP_REMOTE" ;;
  website)
    (cd website/src && python3 build.py)
    rsync -avz $DRY --exclude 'sweep-count.php' website/dist/ "$HOST:$WEBSITE_REMOTE" ;;
  *) echo "Usage : ./deploy.sh app|website [--go]"; exit 1 ;;
esac
if [ -n "$DRY" ]; then
  echo "Simulation seulement. Ajoute --go pour déployer."
else
  # Clear the cPanel NGINX cache (whole account) so visitors get the new files
  ssh "$HOST" 'uapi NginxCaching clear_cache' | grep -q '^ *status: 1$' \
    && echo "Cache NGINX vidé." \
    || { echo "ERREUR : le cache NGINX n'a pas pu être vidé (cPanel > NGINX Manager)."; exit 1; }
fi
