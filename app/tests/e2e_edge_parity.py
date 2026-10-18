"""
Sweep — « Your edge » (brief edge T2): one profile, browser and server. The two sides are written in two languages, this
test locks them together (like e2e_rule_parity). Dev environment with Playwright and PHP:
  python3 tests/e2e_edge_parity.py http://127.0.0.1:8095 /tmp/show_state.json        (run from the app folder)
8 sets of trades made up from a fixed seed (0 to 260 trades over 10 weeks: setups written with other capitals or spaces,
evening trades, no entry time, copies, example trades, risk known or not, plans of every kind): SweepEdge.profile() in the
browser = GameEdge::profile() on the server, field by field (amounts to the cent).
"""
import asyncio, datetime, json, random, subprocess, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1

DAY = '2026-10-16'
SETUPS = ['ORB', 'orb ', 'VWAP reclaim', 'Liquidity sweep', 'Break & retest', '', '', 'Fair value gap']
SESS = ['ny', 'london', 'asia', '', 'ny']
EMO = [[], ['Calm'], ['FOMO'], ['Confident', 'Calm'], [], ['Frustrated']]
def make(seed, n, risk_share):
    rnd = random.Random(seed); base = datetime.date.fromisoformat(DAY); trades, journals = [], []
    for d in range(0, 70):
        day = (base - datetime.timedelta(days=d)).isoformat()
        if rnd.random() < .5: journals.append({'id': day, 'pre': {'bias': rnd.choice(['bullish', 'bearish', 'neutral', 'no_trade', None]), 'max_loss': rnd.choice(['500', '', '1,000', '0']), 'setups': rnd.choice([[], ['ORB'], ['vwap reclaim', 'Break & retest']])}})
    for i in range(n):
        day = (base - datetime.timedelta(days=rnd.randint(-2, 69))).isoformat()
        h = rnd.choice([None, 9, 9, 10, 11, 13, 15, 18, 19, 23]); tm = '' if h is None else '%02d:%02d:00' % (h, rnd.randint(0, 59))
        t = {'id': 't%03d_%d' % (i, seed), 'date': day, 'entry_time': tm, 'session_date': rnd.random() < .8, 'direction': rnd.choice(['long', 'short']), 'contracts': rnd.choice([1, 1, 2, 3, 0]),
             'instrument': rnd.choice(['NQ', 'MNQ', 'es']), 'pnl_c': rnd.randint(-40000, 50000), 'fees_c': rnd.choice([0, 0, 412, None]), 'risk_c': rnd.choice([10000, 20000, 5000]) if rnd.random() < risk_share else rnd.choice([0, None]),
             'setup': rnd.choice(SETUPS), 'session': rnd.choice(SESS), 'emo': {'before': rnd.choice(EMO)}, 'created_at': day + 'T%02d:%02d:%02d.000Z' % (rnd.randint(0, 23), rnd.randint(0, 59), rnd.randint(0, 59))}
        if rnd.random() < .05: t['demo'] = True
        trades.append(t)
        if rnd.random() < .08:   # a copy on another account, saved a little later (or earlier)
            g = 'g%d_%d' % (i, seed); t['copy_group'] = g
            c = dict(t, id=t['id'] + 'c', copy_group=g, contracts=1, pnl_c=t['pnl_c'] // 2, created_at=t['created_at'][:-5] + rnd.choice(['500Z', '000Z']))
            trades.append(c)
    return trades, journals
SETS = [make(1, 0, 1), make(2, 3, 1), make(3, 30, 1), make(4, 80, .9), make(5, 150, .5), make(6, 260, 0), make(7, 120, .85), make(8, 200, 1)]

PHP = r'''
require 'game/game.php';
$in = json_decode(stream_get_contents(STDIN), true); $out = [];
foreach ($in['sets'] as [$t, $j]) $out[] = GameEdge::profile($t, $j, $in['day']);
echo json_encode($out, JSON_UNESCAPED_UNICODE);
'''
def same(a, b, path=''):
    if isinstance(a, float) or isinstance(b, float):
        return (isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < .006) or [path, a, b]
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b): return [path + ' keys', sorted(a), sorted(b)]
        for k in a:
            r = same(a[k], b[k], path + '.' + k)
            if r is not True: return r
        return True
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): return [path + ' length', len(a), len(b)]
        for i, (x, y) in enumerate(zip(a, b)):
            r = same(x, y, path + '[%d]' % i)
            if r is not True: return r
        return True
    return a == b or [path, a, b]

async def main():
    srv = json.loads(subprocess.run(['php', '-r', PHP], input=json.dumps({'sets': SETS, 'day': DAY}), capture_output=True, text=True, check=True).stdout)
    async with async_playwright() as p:
        br = await p.chromium.launch(); ctx = await br.new_context(storage_state=STATE, locale='fr-CA')
        await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
        await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
        web = await pg.evaluate("([sets, day]) => sets.map(([t, j]) => JSON.parse(JSON.stringify(SweepEdge.profile(t, j, day))))", [SETS, DAY])
        for i, (a, b) in enumerate(zip(web, srv)):
            r = same(a, b)
            ok(r is True, f'set {i + 1} ({len(SETS[i][0])} trades): browser = server — n {a.get("n")}, {a.get("unit")}, {len(a.get("wins") or [])} winning conditions, leak {"yes" if a.get("leak") else "no"}' + ('' if r is True else f' — differs at {r}'))
        ok(sum(len(x.get('wins') or []) for x in srv) >= 4 and any(x.get('leak') for x in srv), 'the sets do find conditions (the comparison is not on empty profiles)')
        ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
        await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
