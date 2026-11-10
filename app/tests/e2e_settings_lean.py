"""
Sweep — Settings, lean (10 Nov., brief « produit final » step 6), dev environment with Playwright:
  python3 tests/e2e_settings_lean.py http://127.0.0.1:8095 /tmp/show_state.json
Phone 390 x 844 (touch, light and dark) and computer 1300 x 850:
 - the 5 groups closed on arrival; phone: everything ends within one and a half screens (1,266 px);
 - no « Follow Sweep », no slogan, no separate Help block: the support email, the referral and the feedback are in « About Sweep »;
 - Sweep AI (in « Advanced »): one line and « Learn more », which opens the detail;
 - the language is one picker; the search finds no removed feature (season, league, crew, Wrapped, public profile, Discord);
 - no horizontal overflow, no page error.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
with sync_playwright() as p:
  br = p.chromium.launch()
  for w, h, mob, cs in ((390, 844, True, 'light'), (390, 844, True, 'dark'), (1300, 850, False, 'dark')):
    tag = f'{w}-{cs}'
    ctx = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, color_scheme=cs, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); sessionStorage.removeItem('sw.sgd'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#settings'); pg.wait_for_selector('#main details.nav-sgd', timeout=20000); pg.wait_for_timeout(2000)
    r = pg.evaluate("""(() => { const m = document.getElementById('main'), g = [...m.querySelectorAll('details.nav-sgd')], vis = [...m.children].filter((e) => e.checkVisibility());
      const about = m.querySelector('section.about'), at = (about || {}).textContent || '';
      const ai = m.querySelector('details.ai-more'), aiSec = ai && ai.closest('details.nav-sgd');
      return { groups: g.length, open: g.filter((d) => d.open).length, bottom: Math.round(vis.pop().getBoundingClientRect().bottom + scrollY),
        social: !!m.querySelector('.social, .social-icons'), slogan: /Sweep down\\. Jump up\\./.test(m.textContent), help: !!m.querySelector('.nav-set-help'),
        aboutRows: /hello@makeitsweep\\.com/.test(at) && /Parrainage/.test(at) && /Donner mon avis/.test(at),
        ai: ai ? { inAdvanced: !!aiSec && aiSec.dataset.i === '4', line: ai.previousElementSibling && ai.previousElementSibling.textContent.length < 120 } : 'AI off',
        lang: !!m.querySelector('select[data-act-change="lang"]') && !m.querySelector('[data-act="lang"]'),
        over: document.documentElement.scrollWidth > innerWidth } })()""")
    ok(r['groups'] == 5 and r['open'] == 0, f'{tag} the 5 groups closed ({r["groups"]}, {r["open"]} open)')
    if mob: ok(r['bottom'] <= 1266, f'{tag} everything within one and a half screens ({r["bottom"]} px)')
    ok(not r['social'] and not r['slogan'] and not r['help'], f'{tag} no « Follow Sweep », slogan or separate Help block')
    ok(r['aboutRows'], f'{tag} « About Sweep »: support email, referral, feedback')
    ok(r['ai'] == 'AI off' or (r['ai']['inAdvanced'] and r['ai']['line']), f'{tag} Sweep AI: one line in « Advanced » ({r["ai"]})')
    if r['ai'] != 'AI off':
      pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"4\"]').open = true"); pg.wait_for_timeout(300)
      pg.locator('#main details.ai-more > summary').click(); pg.wait_for_timeout(300)
      ok(pg.evaluate("document.querySelector('#main details.ai-more').open && /Gemini/.test(document.querySelector('#main details.ai-more').textContent)"), f'{tag} « En savoir plus » opens the detail')
    ok(r['lang'], f'{tag} the language in one picker')
    ok(not r['over'], f'{tag} no horizontal overflow')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    ctx.close()
  # the search finds none of the removed features
  ctx = br.new_context(storage_state=STATE, viewport={'width': 1300, 'height': 850}, locale='en-US')
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
  pg = ctx.new_page(); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
  for q in ('season', 'league', 'crew', 'wrapped', 'public profile', 'discord', 'boss', 'chest'):
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(300)
    inp = pg.locator('#cmd input').first
    if not inp.count(): pg.keyboard.press('Meta+k'); pg.wait_for_timeout(300)
    inp.fill(q); pg.wait_for_timeout(400)
    hits = pg.evaluate("[...document.querySelectorAll('#cmd [data-i], #cmd .cmd-item, #cmd li')].map((x) => x.textContent.trim()).filter((t) => t && !/^(Ask Sweep|Demander à Sweep|Preguntar a Sweep)/.test(t) && !/Sweep AI/.test(t))")
    bad = [x for x in hits if any(k in x.lower() for k in ('season', 'league', 'crew', 'buddy', 'wrapped', 'public', 'discord', 'boss', 'chest'))]
    ok(not bad, f'search « {q} »: no removed feature ({bad[:2]})')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
