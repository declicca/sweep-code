"""
Sweep — Admin readable on a phone (13 Nov., brief « Admin lisible sur téléphone », step 2), dev environment:
  python3 tests/e2e_admin_phone.py http://127.0.0.1:8095 /tmp/show_state.json        (the test trader is the admin)
 - « To look at », first in Admin (above « Export for Claude », Health and the dashboard): a scheduled task made red in the test database is listed in one sentence, and a
   tap goes to the Health block; when nothing asks for an action (the answer of api/admin/watch given empty; the server side is
   in metrics_test.php), one line: « Nothing to look at »;
 - at 390, no Admin table is wider than its card, no cell's text is cut, no sideways scroll: a table too wide is drawn as stacked
   rows (each value under the name of its column); a table that fits stays a table;
 - at 1300 nothing changed: no stacked table, the tables are tables;
 - FR, EN and ES words, light and dark, no page error. SWEEP_SHOTS=<folder> saves the screenshots.
"""
import json, os, subprocess, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.environ.get('SWEEP_SHOTS')
# every task green, but the game's: failed
SEED = """require '%s/ops/cron-lib.php'; $p = new PDO('sqlite:%s'); $p->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); sweep_cron_schema($p);
$p->exec('DELETE FROM cron_runs'); $n = time(); $i = $p->prepare('INSERT INTO cron_runs (task, started_at, finished_at, duration_ms, ok, error, last_ok_at) VALUES (?, ?, ?, 10, ?, ?, ?)');
foreach (array_keys(SWEEP_CRON_TASKS) as $t) $i->execute([$t, $n - 30, $n - 20, $t === 'game' ? 0 : 1, $t === 'game' ? 'boom' : null, $n - 20]);""" % (APP, DB)
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'h': 'À regarder', 'task': '1 tâche planifiée en échec ou en retard', 'none': 'Rien à regarder', 'firms': 'Comptes par firme', 'acc': 'Comptes'},
     'en': {'h': 'To look at', 'task': '1 scheduled task failed or late', 'none': 'Nothing to look at', 'firms': 'Accounts by firm', 'acc': 'Accounts'},
     'es': {'h': 'Para revisar', 'task': '1 tarea programada con error o con retraso', 'none': 'Nada que revisar', 'firms': 'Cuentas por firma', 'acc': 'Cuentas'}}
TABLES = """() => [...document.querySelectorAll('#main table.tbl')].filter((t) => t.checkVisibility()).map((t) => { const w = t.closest('.scroll-x') || t.parentElement, card = t.closest('.surface, .sec, section') || w;
  const cut = [...t.querySelectorAll('td, th')].filter((c) => c.checkVisibility() && c.scrollWidth > c.clientWidth + 1 && getComputedStyle(c).overflow !== 'visible').length;
  return { cls: t.className, stacked: t.classList.contains('ux-stack'), display: getComputedStyle(t).display, over: Math.round(t.getBoundingClientRect().right - card.getBoundingClientRect().right), scroll: Math.round(w.scrollWidth - w.clientWidth), cut,
    labels: t.classList.contains('ux-stack') ? [...t.tBodies[0].rows[0].cells].slice(1).filter((c, i) => c.textContent.trim() && t.tHead.rows[0].cells[i + 1] && t.tHead.rows[0].cells[i + 1].textContent.trim()).every((c) => (c.getAttribute('data-l') || '') !== '' && getComputedStyle(c, '::before').content.length > 2) : true }; })"""
r = subprocess.run(['php', '-r', SEED], capture_output=True, text=True)
ok(r.returncode == 0, 'the tasks seeded: all green but one, failed ' + r.stderr[:200])
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, h, scheme in (('fr', 390, 844, 'dark'), ('es', 390, 844, 'light'), ('en', 1300, 850, 'light'), ('fr', 1300, 850, 'dark')):
    tag = f'{w}-{lang}-{scheme}'; mob = w < 500; x = X[lang]
    ctx = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, color_scheme=scheme, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#admin'); pg.wait_for_selector('#main .ux-watch [data-wt]', timeout=20000); pg.wait_for_selector('#main table.ux-firms', timeout=20000); pg.wait_for_timeout(1500)
    wt = pg.evaluate("""(() => { const b = document.querySelector('#main .ux-watch');
      return { h: b.querySelector('h2').textContent, first: !![...document.querySelectorAll('#main .ux-rep-bar, #main .ux-health-admin, #main .ux-metrics, #main .ux-presets-admin, #main .ux-sync-admin, #main table')].every((e) => b.compareDocumentPosition(e) & 4) && b.nextElementSibling.classList.contains('ux-rep-bar'), rows: [...b.querySelectorAll('li')].map((l) => [l.dataset.wt, l.querySelector('span').textContent]), top: Math.round(b.getBoundingClientRect().top),
        wide: [...b.querySelectorAll('.ux-wt-row')].filter((r) => r.scrollWidth > r.clientWidth + 1 || r.getBoundingClientRect().right > innerWidth).length, small: [...b.querySelectorAll('.ux-wt-row')].filter((r) => r.getBoundingClientRect().height < 44).length }; })()""")
    ok(wt['h'] == x['h'] and wt['first'] and wt['top'] < h, f'{tag} « {x["h"]} » above everything else in Admin, on the first screen ({wt["h"]}, top {wt["top"]})')
    ok(['task', x['task']] in wt['rows'], f'{tag} the failed task, one sentence ({wt["rows"][:3]})')
    ok(wt['wide'] == 0 and wt['small'] == 0, f'{tag} each line fits and is 44 px high or more ({wt["wide"]}, {wt["small"]})')
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'admin-watch-{tag}.png'))
    pg.locator('#main .ux-watch li[data-wt=task] .ux-wt-row').click(); pg.wait_for_timeout(600)
    top = pg.evaluate("Math.round(document.querySelector('#main .ux-health-admin').getBoundingClientRect().top)")
    ok(-5 <= top < h * 0.6, f'{tag} a tap goes to the Health block (its top at {top} px)')
    # every table
    pg.evaluate("document.querySelectorAll('#main details').forEach((d) => { d.open = true; })"); pg.wait_for_timeout(700)
    tb = pg.evaluate(TABLES)
    bad = [t for t in tb if (t['over'] > 1 or t['cut'] or (mob and t['scroll'] > 1) or not t['labels']) and not (not mob and 'trd-tbl' in t['cls'])]   # the traders' list scrolls sideways on a computer, as before
    ok(len(tb) >= 6 and not bad, f'{tag} {len(tb)} tables, none wider than its card, no text cut{", no sideways scroll" if mob else ""} ({bad[:3]})')
    stacked = [t['cls'] for t in tb if t['stacked']]
    if mob:
      ok(len(stacked) >= 4 and any('ux-firms' in c for c in stacked) and any('ux-slots' in c for c in stacked) and any('ux-cases' in c for c in stacked) and any('ux-journal' in c for c in stacked), f'{tag} the wide tables are stacked rows ({len(stacked)})')
      ok(any(not t['stacked'] and t['display'] == 'table' for t in tb), f'{tag} a table that fits stays a table')
      lab = pg.evaluate("(() => { const c = document.querySelector('#main table.ux-firms tbody tr:not(.muted) td:nth-child(2)') || document.querySelector('#main table.ux-firms tr.ux-firms-t td:nth-child(2)'); return [c.getAttribute('data-l'), getComputedStyle(c, '::before').content]; })()")
      ok(lab[0] == x['acc'] and x['acc'] in lab[1], f'{tag} each value under the name of its column ({lab})')
    else:
      ok(not stacked and all(t['display'] == 'table' for t in tb), f'{tag} nothing changed at 1300: no stacked table ({stacked})')
    ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no sideways scroll of the page')
    if SHOTS:
      pg.locator('#main table.ux-firms').scroll_into_view_if_needed(); pg.wait_for_timeout(500); pg.screenshot(path=os.path.join(SHOTS, f'admin-firms-{tag}.png'))
      pg.locator('#main table.ux-slots').scroll_into_view_if_needed(); pg.wait_for_timeout(500); pg.screenshot(path=os.path.join(SHOTS, f'admin-slots-{tag}.png'))
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()
    # nothing to look at
    ctx = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, color_scheme=scheme, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = ctx.new_page()
    pg.route('**/api/admin/watch', lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps({'now': int(time.time()), 'items': []})))
    pg.goto(B + '/#admin'); pg.wait_for_selector('#main .ux-watch [data-wt]', timeout=20000); pg.wait_for_timeout(500)
    none = pg.evaluate("[...document.querySelectorAll('#main .ux-watch [data-wt]')].map((e) => [e.dataset.wt, e.textContent])")
    ok(none == [['none', x['none']]], f'{tag} nothing asks for an action: one line, « {x["none"]} » ({none})')
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'admin-watch-none-{tag}.png'))
    ctx.close()
  br.close()
subprocess.run(['php', '-r', "$p = new PDO('sqlite:%s'); $p->exec('DELETE FROM cron_runs');" % DB], capture_output=True)   # as the other tests find it
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
