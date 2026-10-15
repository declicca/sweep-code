"""
Sweep — the errors of Admin › Errors, 15 Oct., with Playwright:
  python3 tests/e2e_errors_oct15.py http://127.0.0.1:8095 /tmp/show_state.json
The signed-in trader is an administrator (tests/setup.py); sample data. Phone 390 / 440 and computer 1300.
 1  a keydown without a key (a browser's autofill: « Cannot read properties of undefined (reading 'startsWith') ») throws nothing
 2  the trade page, without scroll anchoring (as on iOS Safari): answering the checklist (Yes / No / N/A, « Mark the rest as
    Yes ») does not move the questions — the score block keeps its height (« 0 of 5 answered » from the start)
 3  the jump report: a tap followed by the trader's own scrolling, or a tap that opens another page, sends nothing
 4  Admin › Errors › « Clear »: the app's window first, then the list is empty
"""
import sys, json
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

MOVE = r"""async (sel)=>{const e=[...document.querySelectorAll(sel)].filter(x=>x.getClientRects().length)[0]; if(!e) return null;
  e.scrollIntoView({block:'center'}); await new Promise(r=>setTimeout(r,400)); const k=[...e.attributes].filter(a=>/^data-(act|path|v|id)$/.test(a.name)).map(a=>`[${a.name}="${CSS.escape(a.value)}"]`).join('');
  const y0=e.getBoundingClientRect().top; e.click(); let worst=0; const t0=performance.now();
  while(performance.now()-t0<900){await new Promise(r=>requestAnimationFrame(r)); const n=document.contains(e)?e:document.querySelector(k); if(n){const d=n.getBoundingClientRect().top-y0; if(Math.abs(d)>Math.abs(worst)) worst=d}}
  return Math.round(worst)}"""

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for w in [390, 440]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 836}, is_mobile=True, has_touch=True)
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    sent = []; pg.on('request', lambda r: 'client-error' in r.url and sent.append(r.post_data or ''))
    pg.goto(B + '/#settings'); pg.wait_for_timeout(2400)
    pg.evaluate("document.querySelector('#main input').dispatchEvent(new KeyboardEvent('keydown', {bubbles: true}))"); pg.wait_for_timeout(300)
    pg.evaluate("(()=>{const e=new Event('keydown',{bubbles:true}); document.dispatchEvent(e)})()"); pg.wait_for_timeout(300)
    ok(not errs, f'1 {w}: a keydown without a key throws nothing ({errs[:1]})')
    t = pg.evaluate("(S.trades.find(t=>!t.copy_group)||S.trades[0]).id")
    pg.evaluate(f"location.hash='#trade/{t}'"); pg.wait_for_timeout(2400)
    pg.add_style_tag(content='html,body,*{overflow-anchor:none!important}')
    moves = {s: pg.evaluate(MOVE, s) for s in ['#main .seg.yn button[data-v="y"]', '#main .seg.yn button[data-v="n"]', '#main .seg.yn button[data-v="na"]', '#main [data-act="all-yes"]']}
    ok(all(v in (0, None) for v in moves.values()) and any(v == 0 for v in moves.values()), f'2 {w}: the checklist answers move nothing ({moves})')
    cnt = pg.evaluate("(()=>{const s=document.querySelector('#main .score .ux-score-n'); return s?s.textContent:''})()")
    ok('sur' in cnt, f'2 {w}: the score always says how many are answered ({cnt})')
    sent.clear()
    pg.evaluate("(async()=>{const b=document.querySelector('#main textarea')||document.querySelector('#main .q span'); b.scrollIntoView({block:'center'}); await new Promise(r=>setTimeout(r,300)); b.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})); b.click(); for(let i=0;i<10;i++){scrollBy(0,120); await new Promise(r=>setTimeout(r,40))}})()")
    pg.wait_for_timeout(1300)
    jumps = [x for x in sent if 'Trade page jump' in x]
    ok(not jumps, f'3 {w}: a tap then the trader\'s own scroll sends no jump report ({jumps[:1]})')
    allerr += errs; c.close()
  # 4. Admin › Errors › Clear
  c = br.new_context(storage_state=STATE, viewport={'width': 1300, 'height': 850})
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2400)
  pg.evaluate("fetch('api/client-error',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Requested-With':'fetch'},body:JSON.stringify({msg:'Test error for the clear button',page:'#dashboard',src:'e2e'})})"); pg.wait_for_timeout(800)
  pg.evaluate("location.hash='#admin'"); pg.wait_for_timeout(3000)
  b = pg.locator('#main [data-ux-errclr]')
  ok(b.count() == 1, f'4 Admin › Errors: « Effacer » next to « Exporter » ({b.count()})')
  if b.count():
    b.click(); pg.wait_for_timeout(500)
    dlg = pg.evaluate("(()=>{const d=document.querySelector('.nav-dlg.open, [role=dialog].open'); return d?d.textContent.slice(0,80):null})()")
    ok(bool(dlg) and 'Effacer' in dlg, f'4 it asks first, in the app\'s window ({dlg})')
    pg.locator('.nav-dlg.open button', has_text='Effacer').last.click(); pg.wait_for_timeout(1800)
    g = pg.evaluate("apiJSON('api/admin/metrics').then(d=>((d.errors||{}).groups_30d||[]).length)")
    ok(g == 0, f'4 the list is empty ({g})')
  allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
