"""
Sweep — the routine of the day, browser against server, through a session (brief 02, part 5), Playwright:
  python3 tests/e2e_routine_parity.py http://127.0.0.1:8095 /tmp/show_state.json
A new trader, one market day D (after today, with D+1 a market day too). For each moment, a second copy of the server runs
next to the first one (port + 1, same database) with its clock set to that moment (SWEEP_GAME_NOW), and the browser's date
is set to the same instant:
 - morning, D 08:30 ET: nothing done → next step: the plan, made from the routine card (max loss from the account's limit);
 - session, D 11:00 ET: a trade → next step: still « add a trade », unless the day's last announcement is past (then the
   review); checked both ways with an announcement at 10:00 and at 15:00;
 - close, D 16:30 ET: next step: the review, made from the routine card → day swept, nothing highlighted;
 - evening, D 19:30 ET: the session of D+1 has started (18:00 ET) → plan first; a trade at 19:35 counts on D+1, D stays swept;
   the plan of D+1 (the pre-market questionnaire) starts from D's levels, max loss $1,500 → the account's $1,000 limit, saved
   only with its sheet.
The review: three one-tap questions (plan followed, discipline, grade) and one optional sentence, saved in the day's
journal; not saved without the three answers.
Each time: the day the browser computes (todayStr), the day of the card and the server's day are the same; the card shows
the server's rings (step done / to do, « n of 3 done », « c of n trades in your plan »); one primary button in the card
(the « Get started » rows inside it are quiet). The plan and review sheets are not covered by anything of the page (the
first-ring tip covered the review's buttons on computer: a « [class*=tip] » rule put it above the sheets).
"""
import asyncio, datetime as dt, os, signal, subprocess, sys, time, urllib.request
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
from pm_helper import apremarket
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
APPDIR = '/tmp/g'   # the served copy (each shard has its own)
P1 = int(B.rsplit(':', 1)[1]) + 1; B1 = f'http://127.0.0.1:{P1}'
NY = ZoneInfo('America/New_York')
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1

def server_at(moment):
    """a copy of the server whose game clock is pinned to `moment` (New York time, « YYYY-MM-DD HH:MM »)"""
    env = dict(os.environ, SWEEP_GAME_NOW=moment, PHP_CLI_SERVER_WORKERS='4')
    p = subprocess.Popen(['php', '-S', f'127.0.0.1:{P1}', 'router.php'], cwd=APPDIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=2); return p
        except Exception: time.sleep(0.2)
    raise RuntimeError('pinned server did not start')
def stop(p):
    try: os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    p.wait()
def epoch(day, hm): return int(dt.datetime.strptime(f'{day} {hm}', '%Y-%m-%d %H:%M').replace(tzinfo=NY).timestamp())

async def main():
  async with async_playwright() as pw:
    br = await pw.chromium.launch()
    # a new trader (on the usual server), one account with a daily loss limit
    ctx = await br.new_context(locale='fr-CA'); u = 'rp' + str(int(time.time() * 1000))[-8:]
    await ctx.request.post(B + '/api/auth/register', data={'username': u, 'password': 'Testpass123!', 'email': u + '@t.dev', 'consent': True, 'elapsed': 6000}, headers={'X-Requested-With': 'fetch'})
    await ctx.request.post(B + '/api/me/profile', data={'first_name': 'Routine', 'last_name': 'Parity', 'username': u}, headers={'X-Requested-With': 'fetch'})
    pg = await ctx.new_page(); await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("""()=>{ put('firms',{id:'rp-f',name:'Topstep'}); put('accounts',{id:'rp-a',firm_id:'rp-f',name:'Topstep 50K',starting_balance_c:5000000,status:'active',phase:'eval',rules:{dd_c:200000,dd_type:'eod',dd_lock:true,target_c:300000,dll_c:100000}}); }""")
    await pg.wait_for_timeout(1500); await pg.close()
    # D: a market day after today, the next day a market day too (asked to the pinned server)
    d = dt.date.today() + dt.timedelta(days=1)
    while True:
      if d.weekday() < 4:
        srv = server_at(f'{d} 08:30')
        r = await (await ctx.request.get(B1 + '/api/game/today')).json(); stop(srv)
        nxt = d + dt.timedelta(days=1); srv = server_at(f'{nxt} 08:30')
        r2 = await (await ctx.request.get(B1 + '/api/game/today')).json(); stop(srv)
        if r['today']['market'] and r2['today']['market']: break
      d += dt.timedelta(days=1)
    D, D1 = str(d), str(d + dt.timedelta(days=1))
    print(f'D = {D}, D+1 = {D1}')

    async def at(moment, label, act=None, next_before=None, next_after=None):
      """open Today at `moment` (both clocks), check the card against the server, run `act`, check again"""
      srv = server_at(moment)
      try:
        page = await ctx.new_page(); errs = []; page.on('pageerror', lambda e: errs.append(str(e)[:160]))
        await page.clock.set_system_time(dt.datetime.strptime(moment, '%Y-%m-%d %H:%M').replace(tzinfo=NY))   # the date only: timers and animations keep running
        await page.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
        await page.goto(B1 + '/#dashboard'); await page.wait_for_selector('#main .nav-rt:not(.ph) .nav-rt-steps', timeout=20000)
        async def check(when, nxt):
          await page.evaluate("SweepGame.refresh && SweepGame.refresh()"); await page.wait_for_timeout(1500)
          srvst = (await (await ctx.request.get(B1 + '/api/game/today')).json())['today']
          b = await page.evaluate("""() => { const c = document.querySelector('#main .nav-rt'); const s = [...c.querySelectorAll('.nav-rt-s')];
            const st = (el) => ['done', 'late', 'todo', 'wait', 'part'].find((k) => el.classList.contains(k));
            return { today: todayStr(), card: SweepGame.state().today.day, s: s.map(st), pill: (c.querySelector('.nav-rt-pill') || {}).textContent || '',
              exec: (s[1].querySelector('.nav-rt-st') || {}).textContent || '', next: c.querySelector('.nav-rt-steps').dataset.next, prim: c.querySelectorAll('.btn.primary').length }; }""")
          r = srvst['rings']
          want = ['done' if r['plan'] >= 100 else 'todo', 'wait' if not srvst['trades'] else ('done' if r['execution'] >= 100 else 'part'), 'done' if r['review'] >= 100 else 'todo']
          n = sum([want[0] != 'todo', want[1] == 'done', want[2] == 'done'])
          ok(b['today'] == b['card'] == srvst['day'], f"{label} {when}: same day in the browser, on the card and on the server ({b['today']} / {b['card']} / {srvst['day']})")
          ok(b['s'] == want, f"{label} {when}: the card shows the server's rings {r} → {b['s']}")
          pill_ok = ('réussie' in b['pill']) if srvst['swept'] else (f'{n} sur 3' in b['pill'])
          ok(pill_ok, f"{label} {when}: « {b['pill'].strip()} » (server: {n} of 3{', swept' if srvst['swept'] else ''})")
          if srvst['trades'] and srvst['plan_valid']: ok(f"{srvst['compliant']} sur {srvst['trades']}" in b['exec'], f"{label} {when}: « {b['exec']} » (server: {srvst['compliant']} of {srvst['trades']})")
          elif srvst['trades']: ok(srvst['compliant'] == 0 and 'pas de plan' in b['exec'], f"{label} {when}: no plan: « {b['exec']} » (server: {srvst['compliant']} in the plan, audit of 16 Oct.)")
          if nxt is not None:
            ok(b['next'] == str(nxt), f"{label} {when}: next step {b['next']} (expects {nxt})")
            ok(b['prim'] == (1 if nxt else 0), f"{label} {when}: {b['prim']} primary button in the card (expects {1 if nxt else 0})")
          return srvst
        await check('on opening', next_before)
        if act: await act(page); await check('after', next_after)
        ok(not errs, f'{label}: no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
        await page.close()
      finally: stop(srv)

    async def sheet_on_top(page, what):   # nothing of the page covers a button of the sheet (the first-ring tip did, 13 Oct.)
      await page.wait_for_selector('#gSheet.open', timeout=8000); await page.wait_for_timeout(900)   # opened and settled
      hb = await page.locator('#gSheet .g-head').bounding_box(); await page.mouse.move(hb['x'] + 20, hb['y'] + 10)   # the pointer and the focus on the sheet, off the card that opened it
      await page.evaluate("document.activeElement && document.activeElement.blur()"); await page.wait_for_timeout(200)   # (« :hover / :focus-within » on that card hid the bug)
      cov = await page.evaluate("""() => { const sh = document.getElementById('gSheet').getBoundingClientRect();
        return [...document.querySelectorAll('#gSheet button, #gSheet textarea, #gSheet input')].filter((b) => b.getClientRects().length).map((b) => {
        const r = b.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
        if (y < Math.max(0, sh.top) || y > Math.min(innerHeight, sh.bottom)) return null;   // scrolled out of the sheet: not on screen
        const row = b.closest('.g-chips-row'), rr = row && row.getBoundingClientRect(); if (rr && (x < rr.left || x > rr.right)) return null;   // further along a row of chips that scrolls sideways (the instrument, 20 Oct.)
        const at = document.elementFromPoint(x, y);
        return at && !b.contains(at) && !at.closest('#gSheet') ? (b.dataset.v || b.dataset.g || b.tagName) + ' ← ' + String(at.className || at.tagName).slice(0, 30) : null; }).filter(Boolean); }""")
      ok(not cov, f'{what}: nothing of the page covers the sheet' + (f' ({cov[:3]})' if cov else ''))
    async def make_plan(page):
      await page.locator('#main .nav-rt [data-rt=plan]').click(); await sheet_on_top(page, 'plan')
      first = await page.locator('#gSheet [data-pmf="lv.london_high"]').input_value()
      await apremarket(page, stop_at='limits')
      ml = await page.locator('#gSheet [data-pmf=max_loss]').input_value()
      ok(ml == '1000', f'plan: the max loss starts from the account\'s daily limit ({ml})')
      hint = await page.locator('#gSheet .g-dll').text_content()
      ok('Topstep 50K' in hint and '1' in hint, f'plan: « {hint} » under the max loss')
      ok(first == '', f'plan: a first plan starts empty (nothing to take back) ({first!r})')
      await apremarket(page, max_loss=1500)   # the trader goes above the limit (allowed)
    async def trade(page):
      await page.evaluate("""() => put('trades', {id:'rp-t1', account_id:'rp-a', instrument:'NQ', direction:'long', contracts:1, entry:21000, exit:21010, pnl_c:20000, pnl_manual:true, fees_c:0,
        date: todayStr(), entry_time:'10:30', exit_time:'10:40', session_date:true})"""); await page.wait_for_timeout(1500)
      await page.evaluate("SweepGame.refresh && SweepGame.refresh()"); await page.wait_for_timeout(1200)
      # the day's announcements: the review comes once the last one is past (after a trade), not before
      await page.wait_for_function("typeof ECON !== 'undefined' && ECON.days && Array.isArray(ECON.days[todayStr()])", timeout=15000)
      real = await page.evaluate("(() => { const ev = ECON.days[todayStr()]; return ev.length ? ev[ev.length - 1].ts : null; })()")
      for hm, want in (('10:00', 3), ('15:00', 2)):
        await page.evaluate(f"(() => {{ window.__ev = window.__ev || ECON.days[todayStr()]; ECON.days[todayStr()] = [{{ id: 'rp-ev', ts: {epoch(D, hm)}, event: 'Test', impact: 'high' }}]; render(); }})()"); await page.wait_for_timeout(600)
        nx = await page.evaluate("document.querySelector('#main .nav-rt .nav-rt-steps').dataset.next")
        ok(nx == str(want), f"session: a trade, the day's last announcement at {hm} ET → next step {nx} (expects {want}: {'the review' if want == 3 else 'add a trade'})")
      await page.evaluate("ECON.days[todayStr()] = window.__ev; render()"); await page.wait_for_timeout(400)
      return 3 if real and real < epoch(D, '11:00') else 2
    async def sheet_review(page):
      await page.locator('#main .nav-rt [data-rt=review]').click(); await sheet_on_top(page, 'review')
      await review(page)
    async def review(page):   # 60 seconds: three taps and one optional sentence
      qs = await page.evaluate("[...document.querySelectorAll('#gSheet .g-f > span')].map(x => x.textContent.trim())")
      ok(qs == ['As-tu suivi ta fiche ?', 'Quelle règle ?', 'Discipline aujourd’hui', 'Ta note du jour', 'Une note pour demain ? (facultatif, en haut de ton prochain pré-marché)'], f'review: the sheet\'s questions (a day with a pre-market sheet, brief step 7) ({qs})')
      await page.locator('#gSheet [data-g=save-review]').click(); await page.wait_for_timeout(300)
      err = await page.locator('#gSheet #gErr').text_content()
      ok(err == 'Réponds aux 3 questions.' and await page.locator('#gSheet.g-rv').count() == 1, f'review: not saved without the 3 answers (« {err} »)')
      await page.locator('#gSheet [data-g=r-followed][data-v=yes]').click(); await page.wait_for_timeout(100)
      await page.locator('#gSheet [data-g=r-score][data-v="4"]').click(); await page.wait_for_timeout(100)
      await page.locator('#gSheet [data-g=r-grade][data-v=B]').click(); await page.wait_for_timeout(100)
      await page.locator('#gSheet [data-gr=tomorrow]').fill('Attendre la confirmation.')
      await page.locator('#gSheet [data-g=save-review]').click(); await page.wait_for_timeout(1200)
      post = await page.evaluate("(getDoc('journals', todayStr()) || {}).post || {}")
      ok(post.get('followed') == 'yes' and post.get('discipline') == 4 and post.get('grade') == 'B' and post.get('tomorrow') == 'Attendre la confirmation.' and post.get('reviewed_at'),
         f"review: saved in the day's journal (the Post-market fields) {dict((k, post.get(k)) for k in ('followed', 'discipline', 'grade', 'tomorrow'))}")
    async def evening_trade(page):
      await page.evaluate("""() => put('trades', {id:'rp-t2', account_id:'rp-a', instrument:'NQ', direction:'short', contracts:1, entry:21020, exit:21015, pnl_c:10000, pnl_manual:true, fees_c:0,
        date: todayStr(), entry_time:'19:35', exit_time:'19:40', session_date:true})"""); await page.wait_for_timeout(1500)
    async def next_plan(page):   # the plan of D+1 starts from the plan of D: bias, max loss (never above the account's limit)
      await page.locator('#main .nav-rt [data-rt=plan]').click(); await sheet_on_top(page, 'plan of the next session')
      lh = await page.locator('#gSheet [data-pmf="lv.london_high"]').input_value(); ph = await page.locator('#gSheet [data-pmf="lv.london_high"]').get_attribute('placeholder')
      ok(lh == '' and ph == '5820', f"next plan: yesterday's levels in grey, for reference, never kept by mistake ({lh!r}, placeholder {ph!r})")   # (20 Oct.: they change every day)
      await apremarket(page, stop_at='limits')
      ml = await page.locator('#gSheet [data-pmf=max_loss]').input_value()
      ok(ml == '1000', f"next plan: the max loss of yesterday ($1,500) starts at the account's limit ({ml})")
      nothing = await page.evaluate("!((getDoc('journals', todayStr()) || {}).pre || {}).bias")
      ok(nothing, 'next plan: nothing saved before « Enregistrer ma fiche »')
      await apremarket(page)
      pre = await page.evaluate("(getDoc('journals', todayStr()) || {}).pre || {}")
      ok(pre.get('bias') == 'bullish' and pre.get('max_loss') == '1000', f"next plan: confirmed as shown ({pre.get('bias')}, {pre.get('max_loss')})")
    async def evening(page): await evening_trade(page); await next_plan(page)

    await at(f'{D} 08:30', 'morning', make_plan, next_before=1, next_after=2)
    box = {}
    async def trade_kept(page): box['next'] = await trade(page)
    await at(f'{D} 11:00', 'session', trade_kept, next_before=2)
    await at(f'{D} 11:00', 'session, the real announcements of the day', None, next_before=box.get('next'))
    await at(f'{D} 16:30', 'close', sheet_review, next_before=3, next_after=0)
    await at(f'{D} 19:30', 'evening (after 18:00 ET)', evening, next_before=1, next_after=2)
    # the evening trade is on D+1, D keeps its one trade and stays swept
    srv = server_at(f'{D} 19:30')
    try:
      r = await (await ctx.request.get(B1 + '/api/game/today')).json()
      ok(r['today']['day'] == D1 and r['today']['trades'] == 1, f"evening: the trade at 19:35 counts on {D1} ({r['today']['day']}, {r['today']['trades']} trade)")
      y = r.get('yesterday') or {}
      ok(y.get('day') == D and y.get('trades') == 1 and y.get('swept'), f"evening: {D} keeps 1 trade and stays swept ({y.get('day')}, {y.get('trades')}, swept {y.get('swept')})")
    finally: stop(srv)
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
