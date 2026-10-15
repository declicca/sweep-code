"""
Sweep — design « iOS 27 », lot 3: motion, with Playwright:
  python3 tests/e2e_design_motion.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Phone 390 and computer 1300, dark.
 1  one curve: on the main pages, at least 97 % of the transitions use cubic-bezier(.32,.72,0,1)
 2  short: no transition over 350 ms on the main pages; sheets 340 ms; the page entrance ≤ 350 ms
 3  the decorative loops stop by themselves (the Sweep AI star: 3 rounds, not forever)
 4  transform / opacity: Wrapped's story bar scales (no width), the skeletons breathe in opacity, the entrance has no blur
 5  « Reduce motion »: transitions and animations are instant
 6  « Reduce transparency »: the bottom bar and the sheets are opaque, without blur
 7  « More contrast »: the secondary grey is as dark as the grey, lines stronger
"""
import sys, re
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def page(br, w, phone, **kw):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme='dark', **kw)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
  return c, pg, errs

SCAN = r"""()=>{let n=0,one=0;const long=[];for(const e of document.querySelectorAll('body *')){const s=getComputedStyle(e);if(s.transitionDuration==='0s')continue;
  const du=s.transitionDuration.split(', ').map(x=>parseFloat(x)*(x.endsWith('ms')?1:1000)), tf=s.transitionTimingFunction.split(/,\s(?![^(]*\))/), pr=s.transitionProperty.split(', ');
  du.forEach((d,i)=>{if(!d||pr[i%pr.length]==='visibility')return;n++;if((tf[i%tf.length]||'')==='cubic-bezier(0.32, 0.72, 0, 1)')one++;if(d>350)long.push([(e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className)+'',pr[i%pr.length],d])})}
  return {n,one,long:long.slice(0,6)}}"""

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for w, phone in [(390, True), (1300, False)]:
    c, pg, errs = page(br, w, phone)
    tot = {'n': 0, 'one': 0}; longs = []
    for h in ['dashboard', 'trades', 'journal', 'calendar', 'accounts', 'payouts', 'analytics', 'settings']:
      pg.evaluate(f"location.hash='#{h}'"); pg.wait_for_timeout(1500)
      r = pg.evaluate(SCAN); tot['n'] += r['n']; tot['one'] += r['one']; longs += [[h] + x for x in r['long']]
    share = tot['one'] / max(1, tot['n'])
    ok(share >= .97, f'1 {w}: {round(share * 100, 1)} % of {tot["n"]} transitions on the one curve')
    ok(not longs, f'2 {w}: no transition over 350 ms ({longs[:4]})')
    ent = pg.evaluate("(()=>{const r=document.createElement('div');r.className='sw-in';document.getElementById('main').append(r);const d=getComputedStyle(r).animationDuration;r.remove();return d})()")
    ok(ent and float(ent.rstrip('s')) <= .35, f'2 {w}: the page entrance lasts {ent}')
    sh = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--dur-sheet').trim()")
    ok(sh == '340ms', f'2 {w}: sheets {sh}')
    tw = pg.evaluate("(()=>{const i=document.querySelector('.ask-fab-ic i'); return i?getComputedStyle(i).animationIterationCount:null})()")
    ok(tw == '3', f'3 {w}: the Sweep AI star twinkles {tw} rounds, then stops')
    kf = pg.evaluate("""(()=>{const out={};for(const sh of document.styleSheets){let rs;try{rs=sh.cssRules}catch(e){continue}for(const r of rs){if(r.type===7&&['wr-fill','shimmer','nav-sk','sc-sh','sw-rise'].includes(r.name))out[r.name]=r.cssText}}return out})()""")
    bad = {k: v for k, v in kf.items() if re.search(r'width|background-position|filter', v)}
    ok(len(kf) >= 4 and not bad, f'4 {w}: {sorted(kf)} move only transform / opacity ({list(bad)})')
    allerr += errs; c.close()
  c, pg, errs = page(br, 390, True, reduced_motion='reduce')
  r = pg.evaluate("(()=>{const b=document.querySelector('.bottomnav'); const s=getComputedStyle(b); return [s.transitionDuration.split(', ').map(parseFloat).every(x=>x<0.02), document.getAnimations().every(a=>(a.effect.getComputedTiming().duration||0)<20)]})()")
  ok(r[0] and r[1], f'5 reduce motion: instant ({r})')
  allerr += errs; c.close()
  # (Chromium has no switch for « reduce transparency » / « more contrast »: the rules are read from the style sheets)
  c, pg, errs = page(br, 390, True)
  mq = pg.evaluate("""(()=>{const o={t:'',c:''};for(const sh of document.styleSheets){let rs;try{rs=sh.cssRules}catch(e){continue}for(const r of rs){if(r.type===4&&/reduced-transparency/.test(r.conditionText))o.t+=r.cssText;if(r.type===4&&/prefers-contrast/.test(r.conditionText))o.c+=r.cssText}}return o})()""")
  ok('bottomnav' in mq['t'] and 'backdrop-filter: none' in mq['t'] and '.evp' in mq['t'], '6 reduce transparency: the bottom bar and the sheets turn opaque, without blur')
  ok('--faint: var(--muted)' in mq['c'] and '--hair: var(--line2)' in mq['c'], '7 more contrast: stronger grey and lines')
  allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
