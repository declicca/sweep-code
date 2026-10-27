"""
Sweep — the new day starts at 18:00 New York time (dev environment with Playwright):
  python3 tests/e2e_session_news_ui.py http://127.0.0.1:8095 /tmp/show_state.json
 - Wednesday Oct 7, 17:30 ET: the day is over but still Wednesday → Wednesday's releases (Announcements › Today), header « mercredi 7 octobre »;
 - 18:30 ET: the new day → Thursday's releases, header « jeudi 8 octobre », journal and trade form on Thursday;
 - « Maintenant » before the session (SWEEP.md step 3): the next big release and its no-trade window;
 - computer, Announcements › « This week »: every release of the week, past ones dimmed, upcoming ones bright;
 - computer: room above the greeting, the menu of your name has the light veil of the phone;
 - accounts / payouts / expenses: the ✕ is centered in its circle.
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

async def page(br, now, desk=True):
  kw = {'viewport': {'width': 1440, 'height': 900}} if desk else {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True}
  ctx = await br.new_context(**kw, locale='fr-CA', timezone_id='Europe/Paris', storage_state=STATE)
  await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.setItem('sw.kpiTab','day')")
  pg = await ctx.new_page(); await pg.clock.install(time=now)
  return ctx, pg

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    econ = None
    for now, want, wday in [('2026-10-07T21:30:00Z', '2026-10-07', 'mercredi 7 octobre'), ('2026-10-07T22:30:00Z', '2026-10-08', 'jeudi 8 octobre')]:
      for desk in (True, False):
        ctx, pg = await page(br, now, desk)
        await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(3200)
        if econ is None:
          econ = await pg.evaluate("fetch('api/econ?from=2026-10-05&to=2026-10-09',{credentials:'same-origin'}).then(r=>r.json()).catch(()=>null)")
        hdr = await pg.evaluate("((document.querySelector('.main-wrap .top #title')||{}).dataset||{}).hi||''")
        # (SWEEP.md step 3) « À surveiller » left Today: the day's releases are on the Announcements page, « Today »
        await pg.evaluate("location.hash = '#news/today'"); await pg.wait_for_timeout(1800)
        names = await pg.evaluate("[...document.querySelectorAll('#main .ff-row .ff-n')].map(e=>e.textContent.trim())")
        exp = await pg.evaluate(f"(ECON.days['{want}']||[]).filter(e=>e.impact==='high'||e.impact==='medium').map(e=>tr(e.event))")   # (shown in the trader's language, brief 02 part 7)
        tag = ('ordinateur' if desk else 'téléphone') + ' ' + now[11:16] + 'Z'
        ok(wday in hdr.lower(), f'[{tag}] header « {hdr.strip()} »')
        ok(len(exp) > 0 and all(any(n.startswith(e) for n in names) for e in exp), f'[{tag}] Announcements › Today shows the releases of {want}: {names[:3]} (expected {exp[:3]})')
        ok(await pg.evaluate('todayStr()') == want, f'[{tag}] the app’s day is {want} (journal, plan, trade form)')
        await ctx.close()
    # « Now », before the session: the next high-impact release and its no-trade window (Wednesday Oct 7, 09:00 ET; FOMC minutes at 14:00)
    # (the game's day comes from the server, not pinned here: the routine's own day is the one compared) — a high-impact release
    # added on that day at 23:30 ET, before the page opens (still ahead of the browser's clock)
    ctx, pg = await page(br, '2026-10-07T13:00:00Z', False)
    hd = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
    rday = ((await (await ctx.request.get(B + '/api/game/today', headers=hd)).json()).get('today') or {}).get('day', '')
    ev = await (await ctx.request.post(B + '/api/admin/econ', data={'date': rday, 'time': '23:30', 'event': 'Sweep test release', 'impact': 'high'}, headers=hd)).json() if rday else {}
    await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    for _ in range(20):   # the day's releases are asked by « Now » itself when missing (27 Oct.), then it is redrawn
      if await pg.evaluate("(d) => !!(ECON.days && ECON.days[d])", rday): break
      await pg.wait_for_timeout(300)
    await pg.wait_for_timeout(800)
    line = await pg.evaluate("(document.querySelector('#main .nav-rt .nav-now-news')||{}).textContent||''")
    hi = await pg.evaluate("(d) => (ECON.days[d]||[]).filter(e=>e.impact==='high' && e.ts + 15*60 > Date.now()/1000).sort((a,b)=>a.ts-b.ts).map(e=>tr(e.event))", rday)
    state = await pg.evaluate("(document.querySelector('#main .nav-rt .nav-now')||{dataset:{}}).dataset.now||''")
    if ev.get('id'): await ctx.request.delete(B + '/api/admin/econ/' + ev['id'], headers=hd)
    ok(state != 'before' or (hi and hi[0] in line and 'pas de trade' in line), f'« Maintenant » before the session ({rday}): the next big release and its window ({state}: {line!r}, expected {hi[:1]})')
    await ctx.close()
    # computer, Announcements › « This week »: every release of the week, past ones dimmed
    ctx, pg = await page(br, '2026-10-07T22:30:00Z', True)
    await pg.goto(B + '/?x=1#news/week'); await pg.wait_for_timeout(3000)
    rows = await pg.evaluate("[...document.querySelectorAll('#main .ff-row')].map(b=>({n:b.querySelector('.ff-n').textContent.trim(), past:b.classList.contains('past'), o:+getComputedStyle(b).opacity}))")
    exp = await pg.evaluate("['2026-10-05','2026-10-06','2026-10-07','2026-10-08','2026-10-09'].flatMap(d=>(ECON.days[d]||[]).filter(e=>e.impact==='high'||e.impact==='medium').map(e=>tr(e.event)))")
    ok(len(exp) > 0 and all(any(r['n'].startswith(e) for r in rows) for e in exp), f'« Cette semaine »: every release of the week ({len(rows)} rows / {len(exp)} expected)')
    ok(all((r['o'] < 1) == r['past'] for r in rows) and any(r['past'] for r in rows) and any(not r['past'] for r in rows), 'past releases dimmed, upcoming ones bright')
    await pg.evaluate("location.hash = '#dashboard'"); await pg.wait_for_timeout(1500)
    await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(200)
    top = await pg.evaluate("document.querySelector('.main-wrap .top #title').getBoundingClientRect().top")
    ok(top >= 32, f'computer: room above the greeting (title at {round(top)} px)')
    await pg.evaluate("document.querySelector('aside.side .who').click()"); await pg.wait_for_timeout(600)
    bg = await pg.evaluate("getComputedStyle(document.getElementById('navMenu')).backgroundColor")
    ok(bg.replace(' ', '') in ('rgba(0,0,0,0.12)', 'rgba(255,255,255,0.4)'), f'computer: the menu of your name has the light veil ({bg})')
    await ctx.close()
    # the ✕ of the add forms
    for desk in (True, False):
      ctx, pg = await page(br, '2026-10-07T15:00:00Z', desk)
      await pg.goto(B + '/?x=1#accounts'); await pg.wait_for_timeout(2500)
      await pg.locator('#main [data-act=acct-add]').last.click(); await pg.wait_for_timeout(600)
      res = await pg.evaluate("[...document.querySelectorAll('#main .nav-cancel')].filter(b=>b.offsetParent).map(b=>{const s=getComputedStyle(b,'::before'); const r=b.getBoundingClientRect(); return Math.abs(parseFloat(s.left)+parseFloat(s.marginLeft)+parseFloat(s.width)/2-r.width/2)+Math.abs(parseFloat(s.top)+parseFloat(s.marginTop)+parseFloat(s.height)/2-r.height/2)})")
      await pg.goto(B + '/?x=2#payouts'); await pg.wait_for_timeout(2500)
      for k in ['addP', 'addE']:   # « My money »: the add forms open from « + Add »
        await pg.evaluate(f"(document.querySelector('#main [data-mny={k}]')||{{click(){{}}}}).click()"); await pg.wait_for_timeout(500)
      res += await pg.evaluate("[...document.querySelectorAll('#main .nav-cancel')].filter(b=>b.offsetParent).map(b=>{const s=getComputedStyle(b,'::before'); const r=b.getBoundingClientRect(); return Math.abs(parseFloat(s.left)+parseFloat(s.marginLeft)+parseFloat(s.width)/2-r.width/2)+Math.abs(parseFloat(s.top)+parseFloat(s.marginTop)+parseFloat(s.height)/2-r.height/2)})")
      ok(len(res) >= 3 and all(x < 0.6 for x in res), f'[{"ordinateur" if desk else "téléphone"}] ✕ centered in its circle (account, payout, expense): offsets {res}')
      await ctx.close()
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
