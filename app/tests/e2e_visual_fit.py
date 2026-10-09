"""
Sweep — visual pass: nothing sticks out of its card, fields have one height, foldable rows have no browser triangle,
the account page has no empty hole between its cards (phone 390 px and computer 1440 px).
  python3 tests/e2e_visual_fit.py http://127.0.0.1:8095 /tmp/show_state.json
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
PAGES = ['#dashboard', '#trades', '#analytics', '#accounts', '#payouts', '#calendar', '#journal', '#news', '#settings', '#import', 'ACCOUNT', 'TRADE']
CHECK = """(()=>{
  const vis=e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
  const over=[];
  document.querySelectorAll('#main .surface').forEach(c=>{ if(!vis(c)) return; const cr=c.getBoundingClientRect();
    c.querySelectorAll('input,select,textarea,.btn,.seg').forEach(e=>{ if(!vis(e)||e.closest('.scroll-x')) return; const p=e.parentElement; if(p&&getComputedStyle(p).overflowX==='auto') return;
      if(e.closest('.nav-ra-row, .trow, .nav-fstrip, .ux-setups')) return;   // swipe actions and scrolling strips live outside on purpose
      const r=e.getBoundingClientRect(); if(r.right>cr.right+1||r.left<cr.left-1) over.push(e.tagName+'.'+String(e.className).split(' ')[0]+' +'+Math.round(Math.max(r.right-cr.right, cr.left-r.left))); }); });
  const hs=[...new Set([...document.querySelectorAll('#main .surface input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file]), #main .surface select:not([multiple])')].filter(vis).map(e=>Math.round(e.getBoundingClientRect().height)))];
  const marker=[...document.querySelectorAll('#main details>summary')].filter(vis).filter(s=>{const c=getComputedStyle(s); return c.display==='list-item'&&c.listStyleType!=='none'}).length;
  return {over, hs, marker};
})()"""
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for name, kw in [('computer', {'viewport': {'width': 1440, 'height': 900}}), ('phone', {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True})]:
      ctx = await br.new_context(**kw, locale='fr-CA', storage_state=STATE)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      pg = await ctx.new_page(); await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      acc = await pg.evaluate("(S.accounts.find(a=>a.status!=='archived'&&a.rules&&a.rules.target_c)||S.accounts[0]||{}).id"); tr = await pg.evaluate("(S.trades.find(t=>!t.demo)||S.trades[0]||{}).id")
      bad = []; heights = set(); markers = 0
      for h in PAGES:
        hh = f'#account/{acc}' if h == 'ACCOUNT' else f'#trade/{tr}' if h == 'TRADE' else h
        await pg.evaluate(f"location.hash='{hh}'"); await pg.wait_for_timeout(1400)
        r = await pg.evaluate(CHECK)
        bad += [f'{h}: {x}' for x in r['over']]; heights |= set(r['hs']); markers += r['marker']
      ok(not bad, f'[{name}] nothing sticks out of its card ({bad[:4]})')
      want = {42} if name == 'computer' else {44}
      ok(heights <= want | {x for x in heights if x > 60}, f'[{name}] one field height ({sorted(heights)})')
      ok(markers == 0, f'[{name}] no browser triangle on foldable rows ({markers})')
      if name == 'computer':
        await pg.evaluate(f"location.hash='#account/{acc}'"); await pg.wait_for_timeout(1500)
        holes = await pg.evaluate("""(()=>{const m=document.querySelector('#main > .acc-mas'); if(!m) return ['no two-column layout']; const o=[]; [...m.children].forEach(col=>{const k=[...col.children].filter(x=>x.getClientRects().length); for(let i=1;i<k.length;i++){const g=k[i].getBoundingClientRect().top-k[i-1].getBoundingClientRect().bottom; if(g>40) o.push(Math.round(g));}}); return o})()""")
        ok(not holes, f'[computer] account page: no hole between its cards ({holes})')
      await ctx.close()
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
