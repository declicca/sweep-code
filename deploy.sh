#!/bin/bash
# Usage : ./deploy.sh app|website        -> simulation (rien n'est envoyé)
#         ./deploy.sh app|website --go   -> déploiement réel
set -e
export PATH="$HOME/.local/bin:$PATH"   # Python 3.12+ installed by uv
HOST="sweep"   # alias défini dans ~/.ssh/config
APP_REMOTE="/home/matnsabc/app.makeitsweep.com/"
WEBSITE_REMOTE="/home/matnsabc/makeitsweep.com/"

DRY="--dry-run"; [ "$2" = "--go" ] && DRY=""

# app --go: only a committed, pushed commit whose GitHub Actions « Tests » run succeeded (brief 01, step 2)
if [ "$1" = "app" ] && [ -z "$DRY" ]; then
  [ -z "$(git status --porcelain -- app)" ] || { echo "REFUS : app/ a des changements non commités."; exit 1; }
  git fetch -q origin || { echo "REFUS : GitHub inaccessible (git fetch)."; exit 1; }
  BR=$(git rev-parse --abbrev-ref HEAD)
  [ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$BR" 2>/dev/null)" ] || { echo "REFUS : ce commit n'est pas poussé sur origin/$BR."; exit 1; }
  CI=0; python3 -I app/tools/ci-status.py "$(git rev-parse HEAD)" || CI=$?
  [ $CI -eq 0 ] || { [ $CI -eq 2 ] && echo "REFUS : attends la fin des tests sur GitHub." || echo "REFUS : les tests de ce commit n'ont pas réussi sur GitHub."; exit 1; }
fi

case "$1" in
  app)
    rsync -avz $DRY \
      --exclude 'config.php' --exclude 'data/' --exclude 'error_log' \
      --exclude 'CLAUDE.md' --exclude 'CONTEXTE-APP.md' --exclude 'NOTES.md' --exclude '.ftp-deploy-sync-state.json' \
      --exclude 'src/' --exclude 'tests/' --exclude 'tools/' \
      app/ "$HOST:$APP_REMOTE" ;;
  website)
    (cd website/src && python3 build.py)
    rsync -avz $DRY --exclude 'sweep-count.php' website/dist/ "$HOST:$WEBSITE_REMOTE"
    # the build keeps a copy of the app's prop firm rules: commit it when it changed (it is the rules' history)
    git status --porcelain website/src/data/presets.json website/src/data/presets-changes.json | grep -q . \
      && echo "Règles des prop firms mises à jour : committer website/src/data/presets*.json." ;;
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
