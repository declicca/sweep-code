"""
Sweep — the bell shows the reminders' words, never their keys (11 Nov.), dev environment:
  python3 tests/e2e_bell_texts.py http://127.0.0.1:8095 [storage_state, unused: it signs up its own traders]
On 10 Nov. the words of the routine's reminders left with the Wrapped module: a trader's list read « g_plan.title »,
« g_plan.body ». A trader of its own per language gets one notification of each type the server still sends for the routine
(written in the test database, as game/v2c.php does), plus two older ones (Wrapped, buddy); the list opens at 390 and 1300:
no row shows a key, the plan reminder has its words in EN, FR and ES, nothing is wider than the list.
"""
import json, os, random, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
SHOTS = os.environ.get('SWEEP_SHOTS')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():   # the tests create many traders: the sign-up attempts are cleared
  try: d = sqlite3.connect(DB, timeout=20); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
TYPES = [('g_plan', 'streaks', {}), ('g_review', 'streaks', {}), ('g_streak', 'streaks', {'n': 4}), ('g_weekly', 'achievements', {}),
         ('g_intention', 'achievements', {'intention': 'One setup'}), ('g_wrapped', 'achievements', {}), ('buddy_swept', 'achievements', {'handle': 'nq_max'})]
PLAN = {'en': 'Your plan of the day is waiting.', 'fr': 'Ton plan du jour t’attend.', 'es': 'Tu plan del día te espera.'}
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, h, scheme in (('fr', 390, 844, 'dark'), ('en', 1300, 850, 'light'), ('es', 390, 844, 'light')):
    tag = f'{w}-{lang}'
    ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=w < 500, is_mobile=w < 500, color_scheme=scheme, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    unthrottle(); mail = 'bt%06d@t.dev' % random.randint(0, 999999)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': mail, 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.ok, f'{tag} a trader of its own ({r.status})')
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('[data-nt=bell]', timeout=20000); pg.wait_for_timeout(1500)
    d = sqlite3.connect(DB, timeout=20); uid = d.execute("SELECT id FROM users WHERE email = ?", (mail,)).fetchone()
    ok(bool(uid), f'{tag} the trader found in the test database')
    if not uid: d.close(); ctx.close(); continue
    for i, (t, cat, params) in enumerate(TYPES):
      d.execute("INSERT INTO notifications (user_id, type, category, title_key, body_key, params, icon, action_url, priority, dedupe_key, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (uid[0], t, cat, t + '.title', t + '.body', json.dumps(params), 'flame' if cat == 'streaks' else 'star', '#dashboard', 'normal', 'bt:%s:%d' % (t, random.randint(0, 10**9)), int(time.time()) - 60 * (i + 1)))
    d.commit(); d.close()
    pg.reload(); pg.wait_for_selector('[data-nt=bell]', timeout=20000); pg.wait_for_timeout(1500)
    pg.locator('[data-nt=bell]').first.click(); pg.wait_for_selector('.nt-item', timeout=10000); pg.wait_for_timeout(900)
    rows = pg.evaluate("[...document.querySelectorAll('.nt-item .nt-txt')].map((e) => [e.querySelector('b')?.textContent || '', e.querySelector('span')?.textContent || ''])")
    raw = [x for x in rows if any(k.endswith('.title') or k.endswith('.body') or k == '' for k in x)]
    ok(len(rows) >= len(TYPES) and not raw, f'{tag} {len(rows)} rows, none shows a key or is empty ({raw[:3]})')
    ok(any(a == PLAN[lang] for a, _ in rows), f'{tag} the plan reminder in its language ({[a for a, _ in rows][:3]})')
    ok(not any('{' in a + b for a, b in rows), f'{tag} every value is filled ({[x for x in rows if "{" in x[0] + x[1]][:2]})')
    wide = pg.evaluate("(() => { const l = document.querySelector('.nt-item').closest('ul') || document.body, r = l.getBoundingClientRect(); return [...document.querySelectorAll('.nt-item')].filter((e) => e.getBoundingClientRect().right > r.right + 1 || e.scrollWidth > e.clientWidth + 1).length; })()")
    ok(wide == 0 and pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no row wider than the list, no sideways scroll ({wide})')
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'bell-{tag}-{scheme}.png'))
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
