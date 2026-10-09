"""
Sweep — A1: one session-date rule everywhere (dev environment with Playwright):
  python3 tests/e2e_session_parity.py http://127.0.0.1:8095 /tmp/show_state.json [path/to/journal.db]
 - a trade typed at 23:36 New York time is saved on the next day's session, with session_date: true;
 - the server (rings, streak, XP, missions: GameEngine::tradeDay) counts it on that SAME session, not one day later;
   the « Execution » ring of that session is done;
 - the calendar shows it on that session;
 - migration: an older trade (no mark) entered at 19:00 and dated by the calendar moves once to the next day;
   a trade already moved by the app (execution the day before its date) keeps its date; both get session_date: true.
Uses today's session of the server (the game only scores days up to today).
"""
import asyncio, sys, json, sqlite3, datetime
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = sys.argv[3] if len(sys.argv) > 3 else '/tmp/g/data/journal.db'
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def add(d, n): return (datetime.date.fromisoformat(d) + datetime.timedelta(days=n)).isoformat()

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); ctx = await br.new_context(viewport={'width': 1280, 'height': 900}, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    rq = ctx.request
    h = await (await rq.get(B + '/api/game/history', headers=H)).json()
    D = h['today']
    # test fixture: the game profile must have started before D (a fresh test trader started today)
    con = sqlite3.connect(DB); con.execute("UPDATE user_game_profile SET started_on = ? WHERE started_on > ?", (add(D, -30), add(D, -30))); con.commit(); con.close()
    # 23:36 New York (EDT, UTC-4) on the evening before D = 03:36 UTC on D
    pg = await ctx.new_page(); await pg.clock.install(time=f'{D}T03:36:00Z')
    await pg.goto(B + '/?x=1#trades'); await pg.wait_for_timeout(2800)
    acc = await pg.evaluate("(S.accounts.find(a=>a.status!=='archived')||{}).id")
    await pg.evaluate("editDoc('settings','settings',d=>{d.add_mode='manual'})")
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(800)
    saved = await pg.evaluate("""(async (a) => { TK.account = a; TK.entry = 21000; TK.exit = 21004; TK.qty = 1; TK.dir = 'long'; const ids = new Set(S.trades.map(t => t.id));
      tkSave(); await new Promise(r => setTimeout(r, 1800)); const t = S.trades.find(x => !ids.has(x.id)); return t ? { id: t.id, date: t.date, time: t.entry_time, flag: t.session_date, ex: (t.executions || []).map(x => x.t) } : null; })""", acc)
    ok(bool(saved) and saved['date'] == D and saved['flag'] is True and saved['time'] == '23:36', f'browser: 23:36 ET → session {D}, session_date: true ({saved})')
    ok(bool(saved) and all(x.startswith(add(D, -1) + ' 23:36') for x in saved['ex']), 'its executions keep the real clock time (the evening before)')
    await pg.wait_for_timeout(1500)
    hist = await (await rq.get(B + f'/api/game/history?from={add(D, -1)}&to={add(D, 1)}', headers=H)).json()
    days = {d['trading_day']: d for d in hist['days']}
    ok(D in days and int(days[D]['ring_execution']) == 100, f'server: the « Execution » ring of {D} is done ({days.get(D)})')
    me = (await (await rq.get(B + '/api/data', headers=H)).json())['user']; uid = me.get('id') or me.get('uid')
    con = sqlite3.connect(DB); cnt = {r[0]: r[1] for r in con.execute("SELECT trading_day, trades_count FROM game_days WHERE user_id = ? AND trading_day IN (?, ?)", (uid, D, add(D, 1)))}; con.close()
    mine = await pg.evaluate(f"S.trades.filter(t=>t.date==='{D}' && !t.demo).length")   # the game leaves sample trades out
    ok(cnt.get(D, 0) == mine and add(D, 1) not in cnt, f'server: {cnt.get(D, 0)} trades counted on {D} (browser: {mine}), none on {add(D, 1)}')
    await pg.evaluate("location.hash='#calendar'"); await pg.wait_for_timeout(1500)
    cal = await pg.evaluate(f"(()=>{{const c=document.querySelector('#main a[href=\"#journal/{D}\"]'); return c?c.innerText.replace(/\\n/g,' '):null}})()")
    ok(bool(cal) and '$' in cal, f'calendar: the session {D} shows the day’s P&L ({cal})')
    # migration of older trades
    old = {'id': 'mig-old', 'account_id': acc, 'instrument': 'NQ', 'direction': 'long', 'contracts': 1, 'entry': 1, 'exit': 2, 'pnl_c': 2000, 'date': '2026-09-29', 'entry_time': '19:00', 'exit_time': '19:10'}
    moved = {'id': 'mig-moved', 'account_id': acc, 'instrument': 'NQ', 'direction': 'long', 'contracts': 1, 'entry': 1, 'exit': 2, 'pnl_c': 2000, 'date': '2026-09-30', 'entry_time': '20:00', 'exit_time': '20:05',
             'executions': [{'id': 'x1', 'side': 'buy', 'qty': 1, 'price': 1, 't': '2026-09-29 20:00:00'}, {'id': 'x2', 'side': 'sell', 'qty': 1, 'price': 2, 't': '2026-09-29 20:05:00'}]}
    for d in (old, moved): await rq.put(B + f"/api/docs/trades/{d['id']}", data=json.dumps(d), headers=H)
    con = sqlite3.connect(DB)
    for i in ('mig-old', 'mig-moved'): con.execute("UPDATE documents SET data = replace(data, '\"session_date\":true', '\"x\":1') WHERE id = ?", (i,))
    con.commit(); con.close()
    data = await (await rq.get(B + '/api/data', headers=H)).json()
    t = {x['id']: x for x in data['trades'] if x['id'] in ('mig-old', 'mig-moved')}
    ok(t['mig-old']['date'] == '2026-09-30' and t['mig-old'].get('session_date') is True, f"older evening trade moved once to its session: {t['mig-old']['date']}")
    ok(t['mig-moved']['date'] == '2026-09-30' and t['mig-moved'].get('session_date') is True, f"trade already moved by the app keeps its date: {t['mig-moved']['date']}")
    data2 = await (await rq.get(B + '/api/data', headers=H)).json()
    ok({x['id']: x['date'] for x in data2['trades'] if x['id'] in ('mig-old', 'mig-moved')} == {'mig-old': '2026-09-30', 'mig-moved': '2026-09-30'}, 'a second load moves nothing (never twice)')
    for i in ('mig-old', 'mig-moved', saved and saved['id']):
      if i: await rq.post(B + f'/api/docs/trades/{i}?_method=DELETE', headers=H)
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
