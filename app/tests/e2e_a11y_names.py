"""
Sweep — B18 accessibility: every clickable element has a name, every field a label (dev environment with Playwright):
  python3 tests/e2e_a11y_names.py http://127.0.0.1:8095 /tmp/show_state.json
Counts, on the 15 main pages (phone, French), the visible elements without a name: target 0.
Also checks that the main buttons are at least 44 px high on a phone.
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
PAGES = ['#dashboard', '#trades', '#analytics', '#accounts', '#payouts', '#calendar', '#journal', '#news', '#settings', '#progress', '#plan', '#import', '#admin', 'ACCOUNT', 'TRADE']
COUNT = """(() => {
  const vis = (e) => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  const nameOf = (e) => {
    const lb = e.getAttribute('aria-labelledby'); if (lb) return lb.split(' ').map((i) => (document.getElementById(i) || {}).textContent || '').join(' ').trim();
    return (e.getAttribute('aria-label') || '').trim() || (e.labels && [...e.labels].map((l) => l.textContent).join(' ').trim()) || (e.matches('input,select,textarea') ? '' : ((e.innerText || '').trim() || (e.textContent || '').trim()))
      || (e.getAttribute('title') || '').trim() || [...e.querySelectorAll('img[alt]')].map((i) => i.alt).join(' ').trim() || ((e.querySelector('svg title') || {}).textContent || '').trim();
  };
  const sel = 'a[href], button, [role=button], summary, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"])';
  const bad = [...document.querySelectorAll(sel)].filter((e) => vis(e) && !e.closest('[aria-hidden=true]') && !nameOf(e));
  return bad.map((e) => e.outerHTML.slice(0, 110));
})()"""
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    acc = await pg.evaluate("(S.accounts.find(a=>a.status!=='archived')||{}).id"); tr = await pg.evaluate("(S.trades[0]||{}).id")
    total = 0; detail = []
    for h in PAGES:
      hh = f'#account/{acc}' if h == 'ACCOUNT' else f'#trade/{tr}' if h == 'TRADE' else h
      await pg.evaluate(f"location.hash='{hh}'"); await pg.wait_for_timeout(1600)
      bad = await pg.evaluate(COUNT); total += len(bad)
      if bad: detail.append(f'{hh}: {len(bad)} → ' + ' | '.join(bad[:3]))
    print('\n'.join(detail))
    small = await pg.evaluate("""(()=>{location.hash='#dashboard'; return 0})()"""); await pg.wait_for_timeout(1500)
    tiny = await pg.evaluate("[...document.querySelectorAll('#main .btn, .bottomnav a, .bottomnav button')].filter(e=>e.getClientRects().length && e.getBoundingClientRect().height < 43.5).map(e=>e.textContent.trim().slice(0,20)+':'+Math.round(e.getBoundingClientRect().height))")
    print(f'elements without a name: {total}')
    print(f'buttons under 44 px on a phone (Today): {len(tiny)} {tiny[:6]}')
    await br.close()
  ok = total == 0 and not tiny
  print('all passed' if ok else 'failed'); sys.exit(0 if ok else 1)
asyncio.run(main())
