"""
Sweep — a trade typed in the evening (brief 00, phase 1.2-a; Q2, recommendation A), Playwright, phone and computer:
  python3 tests/e2e_evening_entry.py http://127.0.0.1:8095 [storage_state, unused: it signs up its own trader]
The clock is set in the browser (New York time). From 17:00 to 9:30 ET the new trade form proposes the session that just
ended (Saturday → Friday), its times empty; « Now » puts today's session and the time, for who trades at night. In the day
nothing changes (today, now). The exit time never fills itself (typing the exit price used to put « now »); a time not
typed is saved empty, never invented; the direction is the Buy / Sell button's, never the order of the times.
Before 16 Oct.: at 21:00 on Tuesday a 10:15 trade went to Wednesday's session, at « 21:00 », and an exit time before the
made-up entry time turned a Buy into a Short.
"""
import datetime as dt, json, os, random, sqlite3, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
NOW = {'fr': 'Maintenant', 'en': 'Now', 'es': 'Ahora'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

SAVE = """async (o) => { Object.assign(TK, o); tkRefresh(); const ids = new Set(S.trades.map((t) => t.id)); tkSave(); await new Promise((r) => setTimeout(r, 1500));
  const t = S.trades.find((x) => !ids.has(x.id)); return t ? [t.date, t.entry_time || '', t.exit_time || '', t.direction, t.pnl_c] : (document.querySelector('#tkErr') || {}).innerText }"""
def utc(y, m, d, h, mi=0): return dt.datetime(y, m, d, h, mi, tzinfo=dt.timezone(dt.timedelta(hours=-4))).astimezone(dt.timezone.utc)   # New York, summer time

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False), ('es', 390, True)):
    tag = f'{w} {lang}'
    def page(at):
      try: d = sqlite3.connect(os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')); d.execute('DELETE FROM attempts'); d.commit(); d.close()   # the sign-up limiter, on the dev database
      except Exception: pass
      c = br.new_context(viewport={'width': w, 'height': 844}, is_mobile=phone, has_touch=phone, timezone_id='America/New_York')
      c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
      r = c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ee%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
      pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.clock.install(time=at); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
      pg.evaluate("put('accounts',{id:'ee-a',name:'A',status:'active',phase:'eval',starting_balance_c:5000000,rules:{}})"); pg.wait_for_timeout(800)
      pg.evaluate("openTicket(null,{manual:true})"); pg.wait_for_timeout(900)
      return c, pg, errs
    form = "[TK.date, TK.entryTime || '', TK.exitTime || '']"
    # Tuesday 13 Oct, 21:00 ET
    c, pg, errs = page(utc(2026, 10, 13, 21))
    f = pg.evaluate(form)
    ok(f == ['2026-10-13', '', ''], f'{tag} 21:00 Tue: the session that just ended (Tue 13), times empty ({f})')
    pg.locator('[data-tk="exit"]').first.fill('21010'); pg.wait_for_timeout(300)
    ok(pg.evaluate("TK.exitTime || ''") == '', f'{tag} typing the exit price leaves the exit time empty ({pg.evaluate("TK.exitTime")!r})')
    r = pg.evaluate(SAVE, {'account': 'ee-a', 'inst': 'NQ', 'dir': 'long', 'qty': 1, 'entry': 21000, 'exit': 21010})
    ok(r == ['2026-10-13', '', '', 'long', 20000], f'{tag} saved without times: Tue 13, no time made up, Long, +$200 ({r})')
    pg.wait_for_timeout(1500); pg.evaluate("typeof closeTicket === 'function' && closeTicket()"); pg.wait_for_timeout(600)   # the saved trade's « How did it go? » step first
    pg.evaluate("openTicket(null,{manual:true})"); pg.wait_for_timeout(900)
    r = pg.evaluate(SAVE, {'account': 'ee-a', 'inst': 'NQ', 'dir': 'long', 'qty': 1, 'entry': 21000, 'exit': 21010, 'entryTime': '10:15:00', 'exitTime': '10:05:00'})
    ok(r and r[0] == '2026-10-13' and r[1] == '10:15' and r[3] == 'long', f'{tag} a 10:15 Buy typed at 21:00: Tue 13, Long even with an exit time before it ({r})')
    pg.wait_for_timeout(1500); pg.evaluate("typeof closeTicket === 'function' && closeTicket()"); pg.wait_for_timeout(600)   # the saved trade's « How did it go? » step first
    pg.evaluate("openTicket(null,{manual:true})"); pg.wait_for_timeout(900)
    b = pg.locator('#tkSlide [data-act="tk-now"]')
    ok(b.count() == 1 and b.inner_text().strip() == NOW[lang], f'{tag} « {NOW[lang]} » next to the date ({b.inner_text().strip() if b.count() else None!r})')
    if b.count():
      b.click(); pg.wait_for_timeout(400)
      f = pg.evaluate(form)
      ok(f[0] == '2026-10-14' and f[1].startswith('21:0'), f'{tag} « {NOW[lang]} »: the session now open (Wed 14) and the time ({f})')
      ok(pg.evaluate("(document.querySelector('[data-tk=date]')||{}).value") == '2026-10-14' and pg.evaluate("(document.querySelector('[data-tk=entryTime]')||{}).value").startswith('21:0'), f'{tag} the fields show it')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    allerr += errs; c.close()
    if lang != 'fr': continue
    # Wednesday 14 Oct, 8:00 ET (before the open) → Tue 13 ; Saturday 17 Oct, 10:00 → Fri 16 ; Tuesday 13 Oct, 11:00 (day) → today, now
    for at, want, what in ((utc(2026, 10, 14, 8), ['2026-10-13', '', ''], '8:00 Wed, before the open: Tue 13'), (utc(2026, 10, 17, 10), ['2026-10-16', '', ''], '10:00 Sat: Fri 16')):
      c, pg, errs = page(at); f = pg.evaluate(form)
      ok(f == want, f'{tag} {what}, times empty ({f})'); allerr += errs; c.close()
    c, pg, errs = page(utc(2026, 10, 13, 11)); f = pg.evaluate(form)
    ok(f[0] == '2026-10-13' and f[1].startswith('11:0'), f'{tag} 11:00 Tue, in the day: unchanged, today and now ({f})'); allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
