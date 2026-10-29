"""
Sweep — the 6 points of the 29 Oct. tour (briefs/brief-app-tour-2026-10-29.md), Playwright:
  python3 tests/e2e_tour_1029.py http://127.0.0.1:8095
A trader of its own; phone 390 (fr, touch, dark) and computer 1300 (en, light).
 T1 the welcome before the open (a Tuesday 8:00 New York): « Prépare ta séance d'aujourd'hui », « Ton plan du jour » (not tomorrow)
 T2 the review: « Did you follow your plan? » and the balance; the discipline and the grade, filled in, under « + Details » (folded)
 T3 the coach: « No trade without a mistake today (1 trade) », never « 0 trades of 1 »
 T4 Today: Discipline « — » while no checklist is filled (not « 0 % »)
 T5 Today: an evening trade's line is the clock time, like the others (no « session of … entered on … »)
 T6 the trade page: the setup with its chips only (written one way), « + Other » opens the field
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'pre': 'Prépare ta séance d’aujourd’hui.', 'st2': 'Ton plan du jour', 'more': '+ Détails', 'none': 'Aucun trade sans erreur aujourd’hui (1 trade)', 'other': '+ Autre'},
     'en': {'pre': 'Prepare today’s session.', 'st2': 'Your plan for the day', 'more': '+ Details', 'none': 'No trade without a mistake today (1 trade)', 'other': '+ Other'}}
FLUSH = "Promise.all(Object.values(chains)).then(() => true)"
SWC = "document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme in (('fr', True, 'dark'), ('en', False, 'light')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    # T1 (its own context: the clock of the first visit, a Tuesday 8:00 New York)
    c1 = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US'}[lang])
    c1.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('%s')); window.__swNow = '2026-10-27T08:00:00-04:00'" % lang)
    c1.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tq%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    p1 = c1.new_page(); p1.on('pageerror', lambda e: errs.append(str(e)[:160])); p1.goto(B + '/'); p1.wait_for_selector('#main .onb', timeout=20000); p1.wait_for_timeout(800)
    txt = p1.locator('#main .onb').inner_text(); steps = p1.evaluate("[...document.querySelectorAll('#main .onb-steps li')].map((l) => l.textContent.replace(/^\\d+/, '').trim())")
    ok(x['pre'] in txt and steps[-1:] == [x['st2']], f'T1 {tag}: before the open, « {x["pre"]} », « {x["st2"]} » ({steps})')
    c1.close()
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tr%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    day = pg.evaluate("todayStr()")
    pg.evaluate("put('accounts', { id: 'tq-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bearish', max_loss: '500', max_trades: '3', saved_at: Math.floor(Date.now() / 1000) - 3600 } })", day)
    # an evening trade (23:10 the day before, session of today), against the bias: a mistake; no checklist answered
    pg.evaluate("(d) => put('trades', { id: 'tq-t1', account_id: 'tq-a', instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -4000, pnl_manual: true, date: d, session_date: true, entry_time: '23:10', exit_time: '23:20', setup: 'Liquidity sweep' })", day)
    pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500); pg.evaluate("render()"); pg.wait_for_timeout(1000); pg.evaluate(SWC)
    # T4, T5
    disc = pg.evaluate("(document.querySelector('#main .nav-rt-disc b') || {}).textContent || null")
    ok(disc in (None, '—'), f'T4 {tag}: no checklist filled: Discipline « — » ({disc!r})')
    row = pg.evaluate("[...document.querySelectorAll('#main .nav-tr small')].map((s) => s.textContent.trim())")
    ok(row and row[0].startswith('23:10') and 'entered' not in row[0] and 'saisi' not in row[0], f'T5 {tag}: the evening trade\'s line: the time, then the setup ({row[:1]})')
    # T2, T3
    pg.evaluate("(d) => SweepGame.openReview(d)", day); pg.wait_for_selector('#gSheet [data-g=save-review]', timeout=8000); pg.wait_for_timeout(500)
    more = pg.evaluate("(() => { const d = document.querySelector('#gSheet details.g-rv-more'); return d ? [d.open, d.querySelector('summary').textContent.trim(), !!d.querySelector('[data-g=r-score]'), !!d.querySelector('[data-g=r-grade]')] : null })()")
    asked = pg.evaluate("[...document.querySelectorAll('#gSheet .g-f > span')].filter((s) => s.getClientRects().length).map((s) => s.textContent.trim())")
    ok(more and more[0] is False and more[1] == x['more'] and more[2] and more[3], f'T2 {tag}: discipline and grade under « {x["more"]} », folded ({more}; shown: {asked})')
    lesson = pg.evaluate("SweepCoach.lesson(todayStr()).text")
    ok(lesson.startswith(x['none']), f'T3 {tag}: « {x["none"]} » ({lesson[:70]!r})')
    if not pg.locator('#gSheet [data-g=r-followed].on').count(): pg.locator('#gSheet [data-g=r-followed]').first.click(); pg.wait_for_timeout(150)
    for b in pg.locator('#gSheet [data-bal-same]').all(): b.click(); pg.wait_for_timeout(100)
    pg.locator('#gSheet [data-g=save-review]').click(); pg.wait_for_timeout(1200)
    post = pg.evaluate("(d) => { const j = getDoc('journals', d) || {}; return j.post ? [j.post.followed, j.post.discipline, j.post.grade] : null }", day)
    ok(post and post[0] and post[1] and post[2], f'T2 {tag}: the day closes without opening « {x["more"]} » ({post})')
    # T6
    pg.evaluate(SWC); pg.evaluate("location.hash = '#trade/tq-t1'"); pg.wait_for_timeout(2000)
    st = pg.evaluate("""(() => { const i = document.querySelector('#main input[data-bind$="|setup"]'), l = i && i.closest('label'); const chips = [...document.querySelectorAll('#main .ux-setups .ux-setup')].map((b) => b.textContent + (b.classList.contains('on') ? '*' : '')); return [l ? !!l.getClientRects().length : null, chips] })()""")
    ok(st[0] is False and 'Liquidity sweep*' in st[1] and not any(c.lower().startswith('liquidity sweep') and c != 'Liquidity sweep*' for c in st[1]) and st[1][-1] == x['other'], f'T6 {tag}: the setup with its chips only, written one way, « {x["other"]} » last ({st[1][:4]}…)')
    pg.locator('#main [data-ux-other]').click(); pg.wait_for_timeout(300)
    ok(pg.evaluate("""(() => { const i = document.querySelector('#main input[data-bind$="|setup"]'); return !!i && !!i.closest('label').getClientRects().length })()"""), f'T6 {tag}: « {x["other"]} » opens the field')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    pg.evaluate(FLUSH)
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
