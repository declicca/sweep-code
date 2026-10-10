"""
Sweep — one session-date rule, browser and server (brief 01, step 3): the two sides are written in two languages, this
test locks them together on a grid of cases. Dev environment with Playwright and PHP:
  python3 tests/e2e_rule_parity.py http://127.0.0.1:8095 /tmp/show_state.json        (run from the app folder)
 1. the session of « now » (New York + 6 h): browser todayStr() = server GameEngine::today(), at 00:00, 09:30, 16:59,
    17:00, 17:59, 18:00, 18:01, 23:36 and 23:59 New York time, on a Monday, a Friday, a Sunday and both 2026 clock changes;
 2. the session of a trade from its entry time: browser sessionOfTs() (used when a trade is saved) = server
    GameEngine::tradeDay() of the same trade dated by the calendar (before 18:00 → that day, from 18:00 → the next day);
 3. « is the date already the session? »: browser hasSessionDate() = server GameEngine::hasSessionDate() on typical trades
    (marked, before / after 18:00, already moved by the app, no entry time);
 4. amounts in whole dollars, EN / FR / ES: server SweepMoneyServer::dollars() (« La réalité du mois ») = the app's moneyU()
    without its « $ » (same grouping: 1,688 · 1 688 · 1.688; same minus sign).
"""
import asyncio, datetime, json, subprocess, sys
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
NY = ZoneInfo('America/New_York')
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1

DAYS = ['2026-10-05', '2026-10-09', '2026-10-11', '2026-03-07', '2026-03-08', '2026-03-09', '2026-10-31', '2026-11-01', '2026-11-02', '2026-12-31']
TIMES = ['00:00', '09:30', '16:59', '17:00', '17:59', '18:00', '18:01', '23:36', '23:59']
instants = []
for d in DAYS:
    for t in TIMES:
        local = datetime.datetime.fromisoformat(f'{d} {t}').replace(tzinfo=NY)
        instants.append((f'{d} {t}', int(local.timestamp())))
walls = [f'{d} {t}' for d in DAYS for t in TIMES]
TRADES = [
    {'date': '2026-10-08', 'entry_time': '23:36:00', 'session_date': True},
    {'date': '2026-10-08', 'entry_time': '09:45:00'},
    {'date': '2026-10-07', 'entry_time': '23:36:00'},
    {'date': '2026-10-08', 'entry_time': '18:00:00'},
    {'date': '2026-10-08', 'entry_time': '17:59:00'},
    {'date': '2026-10-08', 'entry_time': '23:36:00', 'executions': [{'t': '2026-10-07 23:36:10'}]},
    {'date': '2026-10-08', 'entry_time': '23:36:00', 'executions': [{'t': '2026-10-08 23:36:10'}]},
    {'date': '2026-10-08', 'entry_time': ''},
    {'date': '2026-10-08'},
]

PHP = r'''
require 'game/game.php';
$in = json_decode(stream_get_contents(STDIN), true); $out = ['today' => [], 'day' => [], 'has' => []];
foreach ($in['instants'] as [$label, $ts]) { putenv('SWEEP_GAME_NOW=@' . $ts); $out['today'][] = GameEngine::today(); }
putenv('SWEEP_GAME_NOW');
foreach ($in['walls'] as $w) $out['day'][] = GameEngine::tradeDay(['date' => substr($w, 0, 10), 'entry_time' => substr($w, 11) . ':00']);
foreach ($in['trades'] as $t) $out['has'][] = GameEngine::hasSessionDate($t);
require 'money/money.php';
foreach (['en', 'fr', 'es'] as $l) foreach ($in['cents'] as $c) $out['money'][$l][] = SweepMoneyServer::dollars($c, $l);
echo json_encode($out, JSON_UNESCAPED_UNICODE);
'''

CENTS = [0, 500, 99900, 100000, 168800, 168850, 1234500, 123456700, -168800, -5000]

async def main():
    srv = json.loads(subprocess.run(['php', '-r', PHP], input=json.dumps({'instants': instants, 'walls': walls, 'trades': TRADES, 'cents': CENTS}),
                                    capture_output=True, text=True, check=True).stdout)
    async with async_playwright() as p:
        br = await p.chromium.launch(); ctx = await br.new_context(storage_state=STATE, locale='fr-CA')
        await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
        pg = await ctx.new_page(); await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
        web = await pg.evaluate("""([instants, walls, trades]) => {
          const real = Date.now, out = { today: [], day: [], has: [] };
          try { for (const [, ts] of instants) { Date.now = () => ts * 1000; out.today.push(todayStr()); } } finally { Date.now = real; }
          for (const w of walls) out.day.push(sessionOfTs(w));
          for (const t of trades) out.has.push(hasSessionDate(t));
          return out; }""", [instants, walls, TRADES])
        web['money'] = {}
        for L in ('en', 'fr', 'es'):
            c2 = await br.new_context(storage_state=STATE); await c2.add_init_script("sessionStorage.setItem('sw.modal','1');localStorage.setItem('tj.lang',JSON.stringify('%s'))" % L)
            p2 = await c2.new_page(); await p2.goto(B + '/#dashboard'); await p2.wait_for_timeout(2000)
            web['money'][L] = await p2.evaluate("(C) => C.map(c => String(moneyU(Math.round(c / 100) * 100)).replace(/<[^>]+>/g, '').replace(/[\\u00a0 ]?\\$/, '').replace('$', ''))", CENTS)
            await c2.close()
        await br.close()
    bad = [f"{lab}: navigateur {w} / serveur {s}" for (lab, _), w, s in zip(instants, web['today'], srv['today']) if w != s]
    ok(not bad, f"1. séance du moment : {len(instants)} instants identiques" + (f" — écarts : {bad[:4]}" if bad else ''))
    eve = [srv['today'][i] for i, (lab, _) in enumerate(instants) if lab == '2026-10-09 18:00']
    ok(eve == ['2026-10-10'], f"1. vendredi 18:00 ET → séance du lendemain des deux côtés ({eve})")
    bad = [f"{w}: navigateur {a} / serveur {b}" for w, a, b in zip(walls, web['day'], srv['day']) if a != b]
    ok(not bad, f"2. séance d'un trade selon son heure d'entrée : {len(walls)} cas identiques" + (f" — écarts : {bad[:4]}" if bad else ''))
    ok(web['day'][walls.index('2026-10-05 23:36')] == '2026-10-06' and web['day'][walls.index('2026-10-05 17:59')] == '2026-10-05',
       '2. 23:36 → séance du lendemain, 17:59 → même jour')
    bad = [f"{t}: navigateur {a} / serveur {b}" for t, a, b in zip(TRADES, web['has'], srv['has']) if bool(a) != bool(b)]
    ok(not bad, f"3. « la date est déjà la séance » : {len(TRADES)} trades identiques" + (f" — écarts : {bad[:3]}" if bad else ''))
    for L in ('en', 'fr', 'es'):
        bad = [f"{c}: app {a!r} / serveur {b!r}" for c, a, b in zip(CENTS, web['money'][L], srv['money'][L]) if a != b]
        ok(not bad, f"4. montants en dollars ({L}) : {len(CENTS)} identiques" + (f" — écarts : {bad[:3]}" if bad else ''))
    print(f"{'all passed' if not fails else str(fails) + ' failed'}"); sys.exit(1 if fails else 0)
asyncio.run(main())
