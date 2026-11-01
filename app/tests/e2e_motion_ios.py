"""
Sweep — moving like iOS 27 (briefs/brief-app-fluidite-ios27-2026-10-31.md), Playwright:
  python3 tests/e2e_motion_ios.py http://127.0.0.1:8095 /tmp/show_state.json
The shared trader and its sample data; phone 390 (en, touch, dark) and computer 1300 (fr, light), phone 390 (es, light).
 1  a tab change starts no entry animation
 2  each tab keeps its scroll (Trades → Stats → Trades)
 3  back puts the scroll back exactly (Trades → a trade → back; Today → an account → back)
 6  phone: the tab bar shrinks while scrolling down (the active tab and « + »), and comes back scrolling up
 8  the CSS has two reactions to a touch: scale(.97), or a background for rows; no other scale, no opacity
 10 on a phone, no touch target under 44 × 44 px (its own box or an invisible area around it) on Today, Trades, a trade and an
    account; never an area that would make a scrolling box scroll (a scrollbar takes room on Linux and Windows)
No page error.
"""
import json, re, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
# the animations running in the page, but never one that runs for ever (a loading spinner) or a transition
ANIMS = "document.getAnimations().filter((a) => a.playState === 'running' && a.constructor.name === 'CSSAnimation' && a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('#main') && (a.effect.getTiming().iterations !== Infinity)).map((a) => a.animationName + ' ' + (a.effect.target.className || a.effect.target.tagName).toString().slice(0, 40))"
PRESS = r"""(() => { const bad = [], seen = new Set();
  const walk = (rules) => { for (const r of rules) { if (r.cssRules && !r.selectorText) { walk(r.cssRules); continue; } if (!r.selectorText || !/:active/.test(r.selectorText)) continue;
    const t = r.style.transform || '', o = r.style.opacity || '';
    const m = t.match(/scale\(([\d.]+)\)/); if (m && +m[1] !== 0.97) bad.push(r.selectorText.slice(0, 60) + ' ' + t);
    if (o && +o < 1) bad.push(r.selectorText.slice(0, 60) + ' opacity ' + o); } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules); } catch (e) {} } return bad })()"""
SMALL = r"""(() => { const out = [];
  const hit = (e) => { const r = e.getBoundingClientRect(); let w = r.width, h = r.height;
    for (const ps of ['::after', '::before']) { const c = getComputedStyle(e, ps); if (c.content && c.content !== 'none' && c.content !== 'normal' && c.position === 'absolute' && c.pointerEvents !== 'none') { w = Math.max(w, parseFloat(c.width) || 0); h = Math.max(h, parseFloat(c.height) || 0); } }
    return [w, h]; };
  document.querySelectorAll('#main a[href], #main button, #main [role=button], #main summary, #main [data-act], .main-wrap .top a, .main-wrap .top button').forEach((e) => {
    if (!e.getClientRects().length || e.closest('[hidden], .nav-sgd:not([open]) > :not(summary)')) return;
    const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.pointerEvents === 'none' || +cs.opacity === 0) return;
    const r = e.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight * 3 || r.width < 1) return;
    if (e.parentElement && e.parentElement.closest('a[href], button, [role=button], summary')) return;   // inside a bigger target
    const [w, h] = hit(e); if (w < 43.5 || h < 43.5) out.push((e.className || e.tagName).toString().slice(0, 30) + ' ' + Math.round(w) + '×' + Math.round(h) + ' «' + (e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 18) + '»'); });
  return out })()"""
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme in (('en', True, 'dark'), ('fr', False, 'light'), ('es', True, 'light')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}-{scheme}'
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, storage_state=STATE, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-MX'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=20000); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())")
    tabs = '#bottomnav' if phone else 'aside.side .nav'
    def tab(v):
      if phone and pg.evaluate("document.body.classList.contains('bn-mini')"): pg.locator('#bottomnav a.on').first.tap(); pg.wait_for_timeout(450)   # the small bar opens first
      (pg.locator(f'{tabs} a[data-v={v}]').first.tap() if phone else pg.locator(f'{tabs} a[data-v={v}]').first.click())
    # 1
    tab('trades'); pg.wait_for_timeout(60); a1 = pg.evaluate(ANIMS); pg.wait_for_timeout(600)
    tab('analytics'); pg.wait_for_timeout(60); a2 = pg.evaluate(ANIMS); pg.wait_for_timeout(600)
    tab('dashboard'); pg.wait_for_timeout(60); a3 = pg.evaluate(ANIMS); pg.wait_for_timeout(600)
    ok(not a1 and not a2 and not a3, f'1 {tag}: a tab change starts no entry animation ({(a1 + a2 + a3)[:4]})')
    # 2
    tab('trades'); pg.wait_for_timeout(900)
    tall = pg.evaluate("document.documentElement.scrollHeight - innerHeight"); y0 = min(900, tall - 10)
    pg.evaluate("(y) => scrollTo(0, y)", y0); pg.wait_for_timeout(400)
    tab('analytics'); pg.wait_for_timeout(900); tab('trades'); pg.wait_for_timeout(900)
    y1 = pg.evaluate("scrollY")
    ok(y0 > 100 and abs(y1 - y0) <= 4, f'2 {tag}: Trades keeps its scroll ({y0} → Stats → {y1})')
    # 3
    pg.evaluate("scrollTo(0, Math.min(641, document.documentElement.scrollHeight - innerHeight - 10))"); pg.wait_for_timeout(400); y0 = pg.evaluate("scrollY")
    tid = pg.evaluate("(S.trades.filter((t) => !t.untracked).slice(-1)[0] || {}).id")
    pg.evaluate("(id) => { location.hash = '#trade/' + id }", tid); pg.wait_for_timeout(1200)
    top = pg.evaluate("scrollY"); pg.go_back(); pg.wait_for_timeout(1200); y1 = pg.evaluate("scrollY")
    ok(top < 5 and abs(y1 - y0) <= 4, f'3 {tag}: a trade opens at its top ({top}), back: Trades where it was ({y0} → {y1})')
    tab('dashboard'); pg.wait_for_timeout(900)
    pg.evaluate("scrollTo(0, Math.min(700, document.documentElement.scrollHeight - innerHeight - 10))"); pg.wait_for_timeout(400); y0 = pg.evaluate("scrollY")
    acc = pg.evaluate("(S.accounts.find((a) => a.status !== 'archived') || {}).id")
    pg.evaluate("(id) => { location.hash = '#account/' + id }", acc); pg.wait_for_timeout(1200); pg.go_back(); pg.wait_for_timeout(1200); y1 = pg.evaluate("scrollY")
    ok(abs(y1 - y0) <= 4, f'3 {tag}: Today → an account → back: where it was ({y0} → {y1})')
    # 6
    if phone:
      tab('trades'); pg.wait_for_timeout(800); pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(300)
      for k in range(6): pg.mouse.wheel(0, 120); pg.wait_for_timeout(80)
      pg.wait_for_timeout(500)
      mini = pg.evaluate("[document.body.classList.contains('bn-mini'), [...document.querySelectorAll('#bottomnav a')].filter((a) => a.getBoundingClientRect().width > 4).length, !!document.querySelector('#bottomnav .plus').getBoundingClientRect().width]")
      for k in range(3): pg.mouse.wheel(0, -120); pg.wait_for_timeout(80)
      pg.wait_for_timeout(500)
      back = pg.evaluate("[document.body.classList.contains('bn-mini'), [...document.querySelectorAll('#bottomnav a')].filter((a) => a.getBoundingClientRect().width > 4).length]")
      ok(mini == [True, 1, True] and back == [False, 4], f'6 {tag}: scrolling down, the tab bar shrinks to the active tab and « + » ({mini}); up, it comes back ({back})')
    # 8
    if lang == 'en': bad = pg.evaluate(PRESS); ok(not bad, f'8 {tag}: two reactions to a touch only ({len(bad)}: {bad[:5]})')
    # 10
    small = []
    if not phone: ctx.close(); continue   # (10 is about touch: a computer has a mouse; its filter chips stay 36 px)
    for h in ('#dashboard', '#trades', '#trade/' + tid, '#account/' + acc):
      pg.evaluate("(h) => { location.hash = h }", h); pg.wait_for_timeout(1500); pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(200)
      small += [f'{h.split("/")[0]}: {x}' for x in pg.evaluate(SMALL)]
    ok(not small, f'10 {tag}: no touch target under 44 px ({len(small)}: {small[:8]})')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
