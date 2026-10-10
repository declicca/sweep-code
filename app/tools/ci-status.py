"""Result of the GitHub Actions « Tests » run for one commit (used by ./deploy.sh app --go).
   python3 -I tools/ci-status.py <commit sha>
Exit 0 = the run succeeded · 2 = running or queued · 1 = failed, cancelled, missing or unreadable.
Reads the public API without a token; if the repository is private, uses the GitHub CLI (gh) when it is signed in."""
import json, shutil, subprocess, sys, urllib.request, urllib.error
REPO, WORKFLOW = 'declicca/sweep-code', 'Tests'
sha = sys.argv[1]
path = f'repos/{REPO}/actions/runs?head_sha={sha}&per_page=30'
def runs():
    try:
        req = urllib.request.Request('https://api.github.com/' + path, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'sweep-deploy'})
        return json.load(urllib.request.urlopen(req, timeout=20))['workflow_runs']
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 404) and shutil.which('gh'):
            r = subprocess.run(['gh', 'api', path], capture_output=True, text=True)
            if r.returncode == 0: return json.loads(r.stdout)['workflow_runs']
        raise SystemExit(f'GitHub inaccessible ({e.code}) : impossible de lire le résultat des tests.')
    except OSError as e:
        raise SystemExit(f'GitHub inaccessible ({e}) : impossible de lire le résultat des tests.')
rs = [r for r in runs() if r.get('name') == WORKFLOW]
if not rs: print(f'aucun passage des tests pour {sha[:7]} (pas encore poussé, ou GitHub ne l’a pas encore lancé)'); sys.exit(1)
r = max(rs, key=lambda r: r.get('run_number', 0))
url = r.get('html_url', '')
if r['status'] != 'completed': print(f'tests en cours ({r["status"]}) pour {sha[:7]} : {url}'); sys.exit(2)
if r['conclusion'] == 'success': print(f'tests réussis pour {sha[:7]} : {url}'); sys.exit(0)
print(f'tests {r["conclusion"]} pour {sha[:7]} : {url}'); sys.exit(1)
