"""Result of the GitHub Actions « Tests » run for one commit (used by ./deploy.sh app --go).
   python3 -I tools/ci-status.py <commit sha> [<sha> …]
Several commits = the same app/ (the last commit of the app, then the website commits after it): GitHub runs the tests on
the last commit of each push only, so the run that tested this app/ can belong to a later website commit. The latest run
among them counts; a cancelled one (replaced by a later push) is skipped.
Exit 0 = the run succeeded · 2 = running or queued · 1 = failed, missing or unreadable.
Reads the public API without a token; if the repository is private, uses the GitHub CLI (gh) when it is signed in."""
import json, shutil, subprocess, sys, urllib.request, urllib.error
REPO, WORKFLOW = 'declicca/sweep-code', 'Tests'
shas = sys.argv[1:]; sha = shas[0]
def runs(sha):
    path = f'repos/{REPO}/actions/runs?head_sha={sha}&per_page=30'
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
every = [r for x in shas for r in runs(x) if r.get('name') == WORKFLOW]; rs = [r for r in every if r.get('conclusion') != 'cancelled']
if not rs: print(f'passage des tests annulé pour {sha[:7]} (un push plus récent l’a remplacé) : repousse ce commit' if every else f'aucun passage des tests pour {sha[:7]} (pas encore poussé, ou GitHub ne l’a pas encore lancé)'); sys.exit(1)
r = max(rs, key=lambda r: r.get('run_number', 0))
if r['head_sha'][:7] != sha[:7]: print(f'(passage du commit {r["head_sha"][:7]}, poussé avec {sha[:7]} : même app/)')
url = r.get('html_url', '')
if r['status'] != 'completed': print(f'tests en cours ({r["status"]}) pour {sha[:7]} : {url}'); sys.exit(2)
if r['conclusion'] == 'success': print(f'tests réussis pour {sha[:7]} : {url}'); sys.exit(0)
print(f'tests {r["conclusion"]} pour {sha[:7]} : {url}')
try:   # why: the annotations written by tools/par.py (one per failed test), readable without signing in
    jobs = json.load(urllib.request.urlopen(urllib.request.Request(r['jobs_url'], headers={'User-Agent': 'sweep-deploy'}), timeout=20))['jobs']
    for j in jobs:
        ann = json.load(urllib.request.urlopen(urllib.request.Request(j['check_run_url'] + '/annotations', headers={'User-Agent': 'sweep-deploy'}), timeout=20))
        for x in ann:
            if x.get('annotation_level') == 'failure' and x.get('title'): print(f"  ✗ {x['title']} : {x.get('message', '').strip()}")
except Exception: pass
sys.exit(1)
