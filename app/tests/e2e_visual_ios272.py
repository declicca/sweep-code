"""
Sweep — the visual tour « iOS 27.2 » (briefs/brief-app-visuel-ios27-2026-11-01.md), Playwright:
  python3 tests/e2e_visual_ios272.py http://127.0.0.1:8095 /tmp/show_state.json
The shared trader and its sample data, 11 screens (Today, Trades, a trade, Calendar, Stats, Accounts, an account, My money,
Settings, News, My progress): phone 390 (en, dark, the installed app), computer 1300 (fr, light), phone 390 (es, light).
 1  the installed app: no safe area on html or body; the tab bar at one place on every screen, at the top and at the bottom of
    each page; the header too
 2  every button with a background or an outline is round (radius at least half its height: a capsule or a circle), except the
    cards, the tiles and the form fields; the capsules have three heights only: 44, 38 and 34
 3  C1 the back link is above the large title, blue, on every sub-page (a trade, an account, Settings), the page's own hidden;
    C2 a fold has one chevron, after its label; C4 Settings is one grouped list (no gap between its rows); C5 the sample data's
    line is one line with a « Remove » capsule
No page error, nothing wider than the window.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
SHAPES = r"""() => { const bad = [], hs = new Set();
  const els = document.querySelectorAll('#main button, #main a.btn, #main .chip, #main [role=button], #main .pill, #main .pz-pill, #main .mny-tag, #main .nav-live, .main-wrap .top button, .main-wrap .top a.btn, #bottomnav .plus');
  for (const e of els) { const r = e.getBoundingClientRect(); if (r.width < 8 || r.height < 14 || r.height > 64 || r.bottom < 0 || r.top > innerHeight * 4) continue;
    const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    if (e.closest('.csel, .nav-ra, .tile, .surface > .ik, .cal, .nav-fstrip, .evp, .wheel, .nav-rt-s, .co-full, .tr-tabs') || e.matches('.csel, .del, .nav-tdisc, .trow, .acard')) continue;
    const bg = cs.backgroundColor, bw = parseFloat(cs.borderTopWidth) || 0;
    const has = (bg && !/rgba\(0, 0, 0, 0\)|transparent/.test(bg)) || (bw > 0 && cs.borderTopStyle !== 'none') || /inset/.test(cs.boxShadow || '');
    if (!has) continue;
    const name = (e.className || e.tagName).toString().split(' ').slice(0, 2).join('.') + ' «' + (e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 14) + '»';
    if ((parseFloat(cs.borderTopLeftRadius) || 0) + 0.5 < r.height / 2) bad.push(name + ' ' + Math.round(r.height) + ' r' + cs.borderTopLeftRadius);
    else if (r.width > r.height + 2 && !e.matches('.pill, .pz-pill, .mny-tag, .nav-live, .info')) hs.add(Math.round(r.height) + ':' + name.slice(0, 24)); }
  return [bad, [...hs]] }"""
BAR = "(() => { const b = document.getElementById('bottomnav').getBoundingClientRect(), s = document.querySelector('aside.side').getBoundingClientRect(); return [Math.round(innerHeight - b.bottom), Math.round(s.top)] })()"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme, pwa in (('en', True, 'dark', True), ('fr', False, 'light', False), ('es', True, 'light', False)):
    w = 390 if phone else 1300; tag = f'{w}-{lang}-{scheme}{"-installed" if pwa else ""}'
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, storage_state=STATE, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-MX'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang + ("Object.defineProperty(navigator, 'standalone', { get: () => true });" if pwa else ''))
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=20000); pg.wait_for_timeout(2500)
    tid = pg.evaluate("(S.trades.filter((t) => !t.untracked).slice(-1)[0] || {}).id"); acc = pg.evaluate("(S.accounts.find((a) => a.status !== 'archived') || {}).id")
    bad, heights, places, wide = {}, set(), set(), []
    for h in ('#dashboard', '#trades', '#trade/' + tid, '#calendar', '#analytics', '#accounts', '#account/' + acc, '#payouts', '#settings', '#news', '#progress'):
      pg.evaluate("(h) => { location.hash = h }", h); pg.wait_for_timeout(1600); pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(250)
      if pwa:
        places.add(tuple(pg.evaluate(BAR)))
        pg.evaluate("scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(450)
        places.add((pg.evaluate(BAR)[0], 'end')); pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(300)
      b, hs = pg.evaluate(SHAPES)
      if b: bad[h.split('/')[0]] = b[:4]
      heights.update(hs)
      if pg.evaluate("document.documentElement.scrollWidth - innerWidth") > 0: wide.append(h)
    if pwa:
      pad = pg.evaluate("[getComputedStyle(document.documentElement).paddingTop, getComputedStyle(document.documentElement).paddingBottom, getComputedStyle(document.body).paddingTop, getComputedStyle(document.body).paddingBottom]")
      bars = {x[0] for x in places}; tops = {x[1] for x in places if x[1] != 'end'}
      ok(pad == ['0px'] * 4 and len(bars) == 1 and len(tops) == 1, f'1 {tag}: no safe area on html or body ({pad}); the tab bar {bars} and the header {tops} at one place on the 11 screens, top and bottom of each page')
    ok(not bad, f'2 {tag}: every button with a background is a capsule or a circle ({bad})')
    hh = sorted({int(x.split(':')[0]) for x in heights})
    ok(set(hh) <= {34, 38, 44}, f'2 {tag}: the capsules have three heights, 44, 38, 34 ({hh}: {sorted(x for x in heights if int(x.split(":")[0]) not in (34, 38, 44))[:6]})')
    # 3. C1 the back link above the large title
    for h in ('#trade/' + tid, '#account/' + acc):   # (2 Nov.) Settings: its parent is Today, a tab — no back link (it showed over the logo)
      pg.evaluate("(h) => { location.hash = h }", h); pg.wait_for_timeout(1400)
      r = pg.evaluate("(() => { const b = document.querySelector('.top-back'), t = document.getElementById('title'); if (!b || b.classList.contains('off')) return null; const own = [...document.querySelectorAll('#main .nav-back, #main .tr-top > a.back')].filter((x) => x.getClientRects().length).length; return [b.getBoundingClientRect().bottom <= t.getBoundingClientRect().top + 1, getComputedStyle(b).color === getComputedStyle(document.documentElement).getPropertyValue('--pos').trim() || /76, 141, 255|47, 111, 228|0, 113, 227/.test(getComputedStyle(b).color), own, b.textContent.trim()] })()")
      ok(r and r[0] and r[2] == 0, f'3 {tag} C1 {h.split("/")[0]}: « ‹ {r and r[3]} » above the large title, the page\'s own hidden ({r})')
    # C2 one chevron after the label; C4 one grouped list
    pg.evaluate("location.hash = '#settings'"); pg.wait_for_timeout(1400)
    ok(pg.evaluate("!!document.querySelector('.top-back:not(.off)')") is False, f'3 {tag} C1 Settings: no back link (Today is a tab)')
    sg = pg.evaluate("(() => { const a = [...document.querySelectorAll('#main .nav-sgd')]; const gaps = a.slice(1).map((d, i) => Math.round(d.getBoundingClientRect().top - a[i].getBoundingClientRect().bottom)); const s = a[0] && a[0].querySelector('summary'); return [a.length, gaps, s ? getComputedStyle(s, '::before').content : null, s ? getComputedStyle(s, '::after').borderTopStyle : null] })()")
    ok(sg[0] >= 4 and all(g <= 1 for g in sg[1]) and sg[2] in ('none', 'normal') and sg[3] == 'solid', f'3 {tag} C2/C4 Settings: one grouped list, no gap between its rows, one chevron after the label ({sg})')
    # C5 the sample data's line
    pg.evaluate("location.hash = '#trades'"); pg.wait_for_timeout(1500)
    dm = pg.evaluate("(() => { const d = document.querySelector('#main .ux-empty.demo'); if (!d) return null; const s = d.querySelector(':scope > span'), b = d.querySelector('.ux-demo-rm'); return [Math.round(s.getBoundingClientRect().height) <= 24, !!b && Math.abs(b.getBoundingClientRect().top + b.getBoundingClientRect().height / 2 - (s.getBoundingClientRect().top + s.getBoundingClientRect().height / 2)) < 3, b && parseFloat(getComputedStyle(b).borderTopLeftRadius) >= b.getBoundingClientRect().height / 2 - 0.5, s.textContent.trim(), b && b.textContent.trim()] })()")
    ok(dm and dm[0] and dm[1] and dm[2], f'3 {tag} C5: the sample data on one line with a « Remove » capsule ({dm})')
    ok(not wide, f'{tag}: nothing wider than the window ({wide})')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
