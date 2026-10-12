"""
Sweep — Admin › Health (brief 02 step 0), dev environment with Playwright:
  python3 tests/e2e_admin_health.py http://127.0.0.1:8095 /tmp/show_state.json      (SWEEP_TEST_DB: the dev server's SQLite file)
The last runs of the scheduled tasks are set in the dev database (the recording itself is tested in tests/cron_health_test.php):
the game task fine, the charts failed, the presets check never ran, the backup late, the restore test running.
 - Health comes first on the Admin page, one line per task: OK, Failed (with its error), Never ran, Late, Running;
 - each line gives its cPanel line; the services say « Set » or « Missing », never a value;
 - only administrators can read it; FR words, phone and computer, no horizontal scroll, no page error.
"""
import asyncio, json, os, random, re, subprocess, sys, time
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
now = int(time.time())
SEED = """require '%s/ops/cron-lib.php'; $p = new PDO('sqlite:%s'); $p->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); sweep_cron_schema($p);
$p->exec('DELETE FROM cron_runs'); $n = %d; $i = $p->prepare('INSERT INTO cron_runs (task, started_at, finished_at, duration_ms, ok, error, note, last_ok_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
$i->execute(['game', $n - 120, $n - 118, 2300, 1, null, '12 player(s)', $n - 118]);
$i->execute(['chart', $n - 1800, $n - 1790, 9800, 0, 'Databento: 401 Unauthorized', null, $n - 90000]);
$i->execute(['backup', $n - 3 * 86400, $n - 3 * 86400 + 4, 4100, 1, null, 'sweep-db-x.sqlite.gz.enc (no off-site copy)', $n - 3 * 86400 + 4]);
$i->execute(['restore_test', $n - 30, null, null, null, null, null, $n - 7 * 86400]);""" % (APP, DB, now)
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  r = subprocess.run(['php', '-r', SEED], capture_output=True, text=True)
  ok(r.returncode == 0, 'the last runs are set in the dev database' + (' — ' + r.stderr[:200] if r.returncode else ''))
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for w, h, mob in ((1440, 900, False), (390, 844, True)):
      tag = f'{w}px'
      ctx = await br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#admin'); await pg.wait_for_selector('#main .ux-health-admin .ux-hl-list li', timeout=15000); await pg.wait_for_timeout(600)
      first = await pg.evaluate("(()=>{const h=document.querySelector('#main .ux-health-admin'), m=document.querySelector('#main .ux-metrics'); return !m || !!(h.compareDocumentPosition(m) & Node.DOCUMENT_POSITION_FOLLOWING)})()")
      ok(first and await pg.evaluate("document.querySelector('#main .ux-health-admin h2').textContent") == 'Santé', f'{tag} « Santé » comes first on the Admin page')
      rows = await pg.evaluate("[...document.querySelectorAll('#main .ux-hl-list li')].map(l=>({c:l.className, b:l.querySelector('b').textContent, chip:l.querySelector('.ux-pr-chip').textContent, t:l.innerText.replace(/\\s+/g,' ')}))")
      want = [('ux-hl-ok', 'Jeu, rappels, courriel « Ta semaine »', 'OK'), ('ux-hl-bad', 'Graphiques des trades', 'Échec'), ('ux-hl-bad', 'Vérification des règles des firmes', 'Jamais exécutée'),
              ('ux-hl-late', 'Sauvegarde', 'En retard'), ('ux-hl-ok', 'Test de restauration', 'En cours')]
      got = [(r['c'], r['b'], r['chip']) for r in rows]
      ok(got == want, f'{tag} one line per task: OK, Échec, Jamais exécutée, En retard, En cours ({got})')
      ok('Databento: 401 Unauthorized' in rows[1]['t'] and 'toutes les heures' in rows[1]['t'], f'{tag} the failed task shows its error and its schedule')
      ok('12 player(s)' in rows[0]['t'] and re.search(r'il y a \d+ min|à l’instant', rows[0]['t']) and '2,3 s' in rows[0]['t'], f'{tag} last run, how long ago, duration ({rows[0]["t"][:110]})')
      cmd = await pg.evaluate("document.querySelector('#main .ux-hl-list li code').textContent")
      ok(cmd.startswith('*/15 * * * *  /usr/local/bin/php ') and cmd.endswith('/game/cron.php >/dev/null 2>&1'), f'{tag} the cPanel line ({cmd[:60]}…)')
      svc = await pg.evaluate("[...document.querySelectorAll('#main .ux-hl-cfg li')].map(l=>[l.dataset.hl, l.querySelector('b').textContent])")
      ok(len(svc) == 8 and all(v in ('Réglé', 'Manquant') for _, v in svc) and dict(svc).get('smtp') == 'Manquant', f'{tag} services: « Réglé » or « Manquant » only, local SMTP missing ({svc})')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      if not mob: await pg.screenshot(path=os.path.join(os.environ.get('TMPDIR', '/tmp'), 'admin-health-1440.png'))
      else:
        await pg.evaluate("document.querySelector('#main .ux-health-admin').scrollIntoView()"); await pg.screenshot(path=os.path.join(os.environ.get('TMPDIR', '/tmp'), 'admin-health-390.png'))
      await ctx.close()
    # a trader who is not an administrator
    ctx = await br.new_context(base_url=B)
    H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}; n = 'ah%06d' % random.randint(0, 999999)
    await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
    r = await ctx.request.get(B + '/api/admin/health')
    ok(r.status == 403, f'a trader who is not an administrator cannot read it ({r.status})')
    await ctx.close(); await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
