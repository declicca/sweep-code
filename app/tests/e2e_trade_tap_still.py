"""
Sweep — a trade's page, an answer tapped never moves the page (10 Nov., the « tapped set » jump of 9 Nov., an iPhone 393 x 695):
  python3 tests/e2e_trade_tap_still.py http://127.0.0.1:8095 /tmp/show_state.json
Phone 393 x 695 (touch, light then dark), Safari-like (no scroll anchoring), the server a little slow (0.2 s per save):
each « set » control of the page (the grade A–F, the coach's Yes / No, the full review's checklist, opened) is tapped; for
0.7 s, image by image, the tapped control stays where it was on the screen (a move of 6 px or more, even one image, is a
jump), and the page sends no « Trade page jump » report. Also: the AI in the « ⋯ » menu, no sticky Chart · Details · Review · Setup bar, no
« x of n » counter in the review, no floating AI button, the grade on one line under the discipline, no page error.
"""
import sys, json
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
# watches the tapped control image by image for 0.7 s after the tap
WATCH = """(i) => { window.__moved = undefined; const res = (v) => { window.__moved = v; }; const el0 = document.querySelector(`[data-qa="${i}"]`); if (!el0) return res(null);
  const sel = ['data-act', 'data-path', 'data-v', 'data-id', 'data-col'].filter((a) => el0.hasAttribute(a)).map((a) => `[${a}="${CSS.escape(el0.getAttribute(a))}"]`).join('');
  const y0 = el0.getBoundingClientRect().top; let worst = 0; const t0 = performance.now();
  const find = () => document.contains(el0) ? el0 : [...document.querySelectorAll('#main ' + sel)].sort((a, b) => Math.abs(a.getBoundingClientRect().top - y0) - Math.abs(b.getBoundingClientRect().top - y0))[0];
  const tick = () => { const el = find(); if (el) { const d = el.getBoundingClientRect().top - y0; if (Math.abs(d) > Math.abs(worst)) worst = d; }
    if (performance.now() - t0 < 700) requestAnimationFrame(tick); else res(Math.round(worst)); };
  requestAnimationFrame(tick); }"""
MARK = """(() => { const out = []; document.querySelectorAll('[data-qa]').forEach((x) => x.removeAttribute('data-qa'));
  for (const b of document.querySelectorAll('#main [data-act="set"]')) { if (!b.checkVisibility()) continue; const r = b.getBoundingClientRect();
    if (r.top < 90 || r.bottom > innerHeight - 110) continue;   // under the bars: not tappable as such
    b.dataset.qa = out.length; out.push((b.dataset.path || '') + '=' + (b.dataset.v || b.textContent.trim())); } return out; })()"""
with sync_playwright() as p:
  br = p.chromium.launch()
  for cs in ('light', 'dark'):
    ctx = br.new_context(storage_state=STATE, viewport={'width': 393, 'height': 695}, is_mobile=True, has_touch=True, device_scale_factor=2, color_scheme=cs, locale='fr-CA')
    ctx.add_init_script("""sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'));
      document.addEventListener('DOMContentLoaded', () => { const st = document.createElement('style'); st.textContent = '*{overflow-anchor:none!important}'; document.head.append(st); });""")
    pg = ctx.new_page(); errs = []; reps = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.on('request', lambda r: reps.append(r.post_data or '') if r.url.endswith('/api/client-error') else None)
    def slow(route):
      if route.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'): pg.wait_for_timeout(200)
      route.continue_()
    pg.route('**/api/**', slow)
    pg.goto(B + '/#trades'); pg.wait_for_function("() => typeof S !== 'undefined' && (S.trades || []).length > 0", timeout=20000); pg.wait_for_timeout(800)
    tid = pg.evaluate("(S.trades.find((t) => !t.demo) || S.trades[0]).id")
    pg.evaluate(f"location.hash = '#trade/{tid}'"); pg.wait_for_selector('#main .th-head', timeout=15000); pg.wait_for_timeout(1500)
    page = pg.evaluate("""(() => { const m = document.getElementById('main'), g = m.querySelector('.th-head > div:has(> .seg[role=group])'), d = m.querySelector('.th-head .nav-tdisc');
      const fab = document.getElementById('askFab');
      return { tnav: !!m.querySelector('.nav-tnav'), counter: /\\b\\d+ (of|sur|de) \\d+\\b/.test((m.querySelector('.co-ask .co-h') || {}).textContent || '') || /\\d+ (of|sur|de) 4/.test((m.querySelector('details.co-full > summary') || {}).textContent || ''),
        fab: !!(fab && fab.checkVisibility()), aiMenu: document.body.classList.contains('ask-on') ? !!m.querySelector('details.menu .menu-pop .nav-ask-m') : 'AI off',
        grade: g && d ? { below: g.getBoundingClientRect().top >= d.getBoundingClientRect().bottom - 1, oneLine: (() => { const l = g.querySelector('.lbl').getBoundingClientRect(), r = g.querySelector('.seg').getBoundingClientRect(), mid = (l.top + l.bottom) / 2; return mid > r.top && mid < r.bottom; })() } : null } })()""")
    ok(not page['tnav'], f'{cs} no sticky Chart · Details · Review · Setup bar')
    ok(not page['counter'], f'{cs} no « x of n » counter in the review')
    ok(not page['fab'], f'{cs} no floating AI button on the phone')
    ok(page['aiMenu'] is True, f'{cs} the AI in the page\'s « ⋯ » menu ({page["aiMenu"]})')
    ok(page['grade'] and page['grade']['below'] and page['grade']['oneLine'], f'{cs} the grade under the discipline, on one line ({page["grade"]})')
    # the controls, page top first, then the full review opened
    tapped = 0
    for phase in ('top', 'coach', 'full'):
      if phase == 'coach':
        pg.evaluate("(() => { const c = document.querySelector('#main .co-ask'); if (c) { c.scrollIntoView({ block: 'start' }); scrollBy(0, -120); } })()"); pg.wait_for_timeout(700)
      elif phase == 'full':
        pg.evaluate("(() => { const d = document.querySelector('#main details.co-full'); if (d) { d.open = true; d.scrollIntoView({ block: 'start' }); scrollBy(0, -100); } })()"); pg.wait_for_timeout(700)
      else:
        pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(400)
      for n in range(6 if phase != 'coach' else 4):
        labels = pg.evaluate(MARK)
        if n >= len(labels): break
        i = len(labels) - 1 - n if phase == 'full' else n
        pg.evaluate(WATCH, i)
        pg.locator(f'[data-qa="{i}"]').tap(); tapped += 1
        pg.wait_for_function("() => window.__moved !== undefined", timeout=5000); moved = pg.evaluate("window.__moved")
        ok(moved is not None and abs(moved) < 6, f'{cs} {phase} « {labels[i]} » tapped: stays under the finger (moved {moved} px)')
        pg.wait_for_timeout(500)
    ok(tapped >= 6, f'{cs} {tapped} answers tapped')
    pg.wait_for_timeout(600)
    jumps = [r for r in reps if 'Trade page jump' in r]
    ok(not jumps, f'{cs} no « Trade page jump » report ({jumps[:1]})')
    ok(not errs, f'{cs} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    ctx.close()
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
