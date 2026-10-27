"""
Sweep — no page jump (20 Oct., Mateo: « still page jumps »), phone 390 and computer 1300, the installed app too:
  python3 tests/e2e_page_shift.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the page header has one height on every page (it changed with the page's buttons and with Today's greeting line):
    the content starts at the same place on every page
 2  from one page to another, nothing moves after it is drawn (layout shift under 0.005)
 3  Today with the 90-day gameplan's card, a trader coming back: the card is there from the first paint, nothing pushed down
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
OBS = """window.__ls = []; new PerformanceObserver((l) => { for (const e of l.getEntries()) { if (e.hadRecentInput) continue; window.__ls.push({ v: +e.value.toFixed(4), t: Math.round(e.startTime), s: (e.sources || []).slice(0, 3).map((x) => { const n = x.node; if (!n || !n.tagName) return '?'; return (n.tagName + '.' + String(n.className || '').split(' ').slice(0, 2).join('.') + (n.id ? '#' + n.id : '')).slice(0, 50) + ' ' + Math.round(x.previousRect.y) + '→' + Math.round(x.currentRect.y); }) }); } }).observe({ type: 'layout-shift', buffered: true });"""
CLS = "Math.round(window.__ls.reduce((a, x) => a + x.v, 0) * 10000) / 10000"
PAGES = ['dashboard', 'trades', 'journal', 'calendar', 'analytics', 'accounts', 'payouts', 'settings', 'news', 'dashboard']
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, pwa in ((390, True, False), (390, True, True), (1300, False, False)):
    tag = f"{w}{' installed' if pwa else ''}"
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'));" + ("Object.defineProperty(navigator, 'standalone', { get: () => true });" if pwa else '') + OBS)
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(3500)
    tops, shifts = {}, {}
    for r in PAGES:
      pg.evaluate("window.__ls = []"); pg.evaluate(f"location.hash = '#{r}'"); pg.wait_for_timeout(2200)
      tops[r] = pg.evaluate("Math.round(document.getElementById('main').getBoundingClientRect().top + scrollY)")
      shifts[r] = pg.evaluate(CLS)
    ok(len(set(tops.values())) == 1, f'1 {tag}: the content starts at the same place on every page ({tops})')
    ok(max(shifts.values()) < 0.005, f'2 {tag}: nothing moves once a page is drawn ({ {k: v for k, v in shifts.items() if v} })')
    # 3. the gameplan's card, coming back
    pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(800)
    pg.evaluate("fetch('api/game/gameplan/start', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}, body: '{}'})"); pg.wait_for_timeout(600)
    pg.reload(); pg.wait_for_timeout(3500); pg.reload(); pg.wait_for_timeout(4500)
    ok(pg.locator('#gpLine').count() == 1 and pg.evaluate(CLS) < 0.005, f'3 {tag}: Today with the gameplan line in « Now », coming back: nothing pushed down ({pg.evaluate(CLS)} {pg.evaluate("window.__ls.filter((x) => x.v > 0.0005)")})')   # (21 Oct.: what moved, in the failure line — the only one GitHub shows)
    pg.evaluate("fetch('api/game/gameplan/stop', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}, body: '{}'})"); pg.wait_for_timeout(600)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
