"""
Sweep — the errors reported in Admin › Errors (list of 13 Oct.) do not come back, Playwright:
  python3 tests/e2e_reported_errors.py http://127.0.0.1:8095 /tmp/show_state.json
 A new trader with one account (the sample trader stays untouched); the day off comes last.
 1. « Cannot read properties of null (reading 'hidden') » (nav.js, 12 Oct., #dashboard): the « ? » of the routine card on a
    day off (or markets closed) looked for a help text those cards did not have. Now it opens the same help.
 2. « Trade page jump: tapped control moved -12px … surface » (phones, #trade): after a tap on a chip, the page is redrawn
    and the discipline box got its style one frame late (12 px shorter for a frame). Now it is styled in the page itself:
    same height in every frame, no jump report.
 3. « Object is disposed » (lightweight-charts, 3 Oct.): the add-trade chart was removed (another session, no data) but its
    series was kept; a price typed afterwards drew on the removed chart. Market data are simulated in the page.
 (« Toggle did not stick », 5 Oct.: chips stay selected since then; e2e_rows_open / the trade page tests cover it.)
"""
import asyncio, os, sys, tempfile, time
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    # a new trader with one account, for the three parts (the sample trader's day, XP and celebrations stay untouched)
    c0 = await br.new_context(locale='fr-CA'); u = 're' + str(int(time.time() * 1000))[-8:]
    await c0.request.post(B + '/api/auth/register', data={'username': u, 'password': 'Testpass123!', 'email': u + '@t.dev', 'consent': True, 'elapsed': 6000}, headers={'X-Requested-With': 'fetch'})
    await c0.request.post(B + '/api/me/profile', data={'first_name': 'Errors', 'last_name': 'Test', 'username': u}, headers={'X-Requested-With': 'fetch'})
    p0 = await c0.new_page(); await p0.add_init_script("sessionStorage.setItem('sw.modal','1')"); await p0.goto(B + '/#dashboard'); await p0.wait_for_timeout(2500)
    await p0.evaluate("() => { put('firms', { id: 're-f', name: 'Topstep' }); put('accounts', { id: 're-a', firm_id: 're-f', name: 'Topstep 50K', starting_balance_c: 5000000, status: 'active', phase: 'eval', rules: { dd_c: 200000, dd_type: 'eod', dd_lock: true, target_c: 300000 } }); }")
    await p0.wait_for_timeout(1500)
    fd, ST = tempfile.mkstemp(suffix='.json'); os.close(fd); await c0.storage_state(path=ST); await c0.close()
    # 2. a chip on the trade page (phone): the discipline box keeps its height in every frame, no jump report
    ctx = await br.new_context(storage_state=ST, locale='fr-CA', viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; reports = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.on('request', lambda r: 'client-error' in r.url and reports.append(r.post_data))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
    tid = await pg.evaluate("""(() => { const id = 're-' + Date.now(); put('trades', { id, account_id: 're-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 21000, exit: 21010, pnl_c: 20000, pnl_manual: true, fees_c: 0, date: todayStr(), entry_time: '10:00', exit_time: '10:05', session_date: true }); return id; })()""")
    await pg.wait_for_timeout(1200); await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(2500)
    ok(await pg.locator('#main .nav-tdisc[data-disc-why=trade]').count() == 1, '2. the discipline box is in the page from the first frame')
    hs = set()
    # (the full review is folded under « Answer your coach » since brief 03 step 5: opened, its emotions tapped)
    await pg.evaluate("(() => { const d = document.querySelector('#main details.co-full'); if (d) d.open = true; })()"); await pg.wait_for_timeout(400)
    for v in ('Calm', 'Patient'):
      loc = pg.locator(f'#rs-psy [data-act=toggle][data-path="emo.before"][data-v="{v}"]').first
      await loc.scroll_into_view_if_needed(); await pg.wait_for_timeout(1000)
      await pg.evaluate("""() => { window.__h = []; const t0 = performance.now(); const f = () => { const b = document.querySelector('#main .nav-tdisc'); window.__h.push(b ? Math.round(b.getBoundingClientRect().height) : 0); if (performance.now() - t0 < 700) requestAnimationFrame(f); };
        addEventListener('pointerdown', () => requestAnimationFrame(f), { once: true, capture: true }); }""")
      await loc.tap(); await pg.wait_for_timeout(1200)
      hs |= set(await pg.evaluate("window.__h"))
    jumps = [r for r in reports if 'jump' in (r or '')]
    ok(len(hs) == 1 and not jumps, f'2. tapping emotions: the discipline box stays {sorted(hs)} px in every frame, no jump report ({jumps[:1]})')
    await pg.evaluate(f"remove('trades', '{tid}')"); await pg.wait_for_timeout(500)
    ok(not errs, '2. no page error' + ('' if not errs else ': ' + errs[0])); await ctx.close()
    # 3. the add-trade chart removed, then a price typed by hand
    ctx = await br.new_context(storage_state=ST, locale='fr-CA', viewport={'width': 1300, 'height': 900})
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("""() => { const f = window.fetch; let n = 0; window.fetch = (u, o) => { if (/api\\/chart\\/bars/.test(String(u))) { n++;   // one session of bars, then the provider is down
        if (n > 1) return Promise.resolve(new Response(JSON.stringify({ status: 'unavailable' }), { headers: { 'Content-Type': 'application/json' } }));
        const q = new URLSearchParams(String(u).split('?')[1]), from = +q.get('from'), bars = [];
        for (let i = 0; i < 300; i++) { const o = 21000 + Math.sin(i / 9) * 20; bars.push([from + i * 60, o, o + 3, o - 3, o + 1]); }
        return Promise.resolve(new Response(JSON.stringify({ status: 'ok', tf: '1m', bars, tick_size: 0.25, decimals: 2, source: 'test' }), { headers: { 'Content-Type': 'application/json' } })); }
      return f(u, o); }; }""")
    await pg.evaluate("S.settings.add_mode_pref = 'manual'; S.settings.add_mode = 'manual'; openTicket(null, { date: '2026-10-07' })"); await pg.wait_for_timeout(2000)
    async def setv(k, v, ev='change'):
      await pg.evaluate(f"(() => {{ const i = document.querySelector('#tkSlide [data-tk=\"{k}\"]'); if (!i) return; i.value = '{v}'; i.dispatchEvent(new Event('input', {{ bubbles: true }})); i.dispatchEvent(new Event('{ev}', {{ bubbles: true }})); }})()")
    await setv('inst', 'NQ'); await setv('date', '2026-10-07'); await setv('entryTime', '10:00'); await pg.wait_for_timeout(3000)
    await setv('date', '2026-10-08'); await pg.wait_for_timeout(2000)   # another session, no data: the chart goes
    await setv('exit', '21010.25', 'input'); await setv('entry', '21000.5', 'input'); await pg.wait_for_timeout(800)
    ok(await pg.locator('#tkSlide.open').count() == 1 and not any('disposed' in e for e in errs), f'3. a price typed after the chart went: no « Object is disposed » ({errs[:1]})')
    await ctx.close()
    # 1. the « ? » of a day-off routine card
    ctx = await br.new_context(storage_state=ST, locale='fr-CA', viewport={'width': 1300, 'height': 900})
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_selector('#main .nav-rt:not(.ph)', timeout=20000)
    day = await pg.evaluate("SweepGame.state().today.day")
    await pg.evaluate("""(d) => { const j = structuredClone(getDoc('journals', d) || { id: d }); j.id = d; 
      j.pre = Object.assign({}, j.pre || {}, { bias: 'no_trade', day_off: true }); j.post = Object.assign({}, j.post || {}, { reviewed_at: new Date().toISOString() }); put('journals', j); }""", day)
    await pg.wait_for_timeout(1500); await pg.evaluate("SweepGame.refresh && SweepGame.refresh()"); await pg.wait_for_timeout(1500)
    off = await pg.locator('#main .nav-rt.off, #main .nav-rt.closed').count()
    if off:
      await pg.evaluate("document.querySelector('#main .nav-rt [data-rt=help]').click()"); await pg.wait_for_timeout(300)   # (the « Day swept » celebration may cover the page: the handler is what failed)
      shown = await pg.evaluate("(() => { const h = document.querySelector('#main .nav-rt .nav-rt-help-t'); return !!h && !h.hidden && h.textContent.length > 20; })()")
      ok(shown and not errs, f"1. day off: « ? » opens the help, no error ({errs[:1]})")
    else: ok(False, '1. the routine card shows the day off')
    await ctx.close()
    os.unlink(ST); await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
