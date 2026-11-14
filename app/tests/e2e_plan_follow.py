"""Sweep — Plan Sync step 5: was the plan followed? A whole test day, its own trader:
  python3 tests/e2e_plan_follow.py [BASE]
 1  the plan (zones and a sweep rule, journals/{day}.chart), events POSTed by a test Quantower key (api/plan-sync/events),
    two trades of the day (one in a zone in the zone's direction, one between the zones)
 2  api/sync/plan-day: the events in order, 1 trade of 2 in the plan
 3  phone 390 (touch) and computer 1300, FR / EN / ES, light and dark: the journal day's recap and the end-of-day review show
    « 1 of 2 trades in your plan's zones » and the time line (approach, touch, the trade in the plan, the sweep with its
    plan reminder, the trade off plan) in New York order, the words explained (sweep, long / short); in the review, above
    « Did you follow your plan? »; nothing cut or overlapping, the page never wider than the screen, no page error
4  (14 Nov.) a trader on his sign-up session, no plan: the journal's recap says « No plan » and the coach never « all in your plan »
Screenshots: /tmp/sweep-plan-follow-<w>-<lang>-<review|journal|noplan>.png"""
import json, sys, time, uuid, urllib.parse, urllib.request, urllib.error, http.cookiejar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').rstrip('/')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
NY = ZoneInfo('America/New_York')
jar = http.cookiejar.CookieJar(); web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)); bare = urllib.request.build_opener()
fails = 0

def ok(c, what):
    global fails
    if not c: fails += 1
    print(('ok   ' if c else 'FAIL ') + what)

def call(op, method, path, body=None, headers=None):
    req = urllib.request.Request(B + '/' + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=headers or {})
    try:
        with op.open(req, timeout=30) as r:
            raw = r.read(); return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, (json.loads(raw) if raw else {})
        except Exception: return e.code, {}

# the New York trading day of now (Fiche::dayOf: 18:00 starts the next one, a weekend belongs to Monday); the events are real
# moments (the API takes the last 7 days only), a few minutes back, so they never straddle 18:00
ny = datetime.now(NY)
if ny.hour == 18 and ny.minute < 6: time.sleep((6 - ny.minute) * 60); ny = datetime.now(NY)
d = ny.date() + timedelta(days=1) if ny.hour >= 18 else ny.date()
while d.weekday() >= 5: d += timedelta(days=1)
day = d.isoformat()
at = lambda m: (ny - timedelta(minutes=m)).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
hm = lambda m: (ny - timedelta(minutes=m)).strftime('%H:%M')

n = 'pfollow' + uuid.uuid4().hex[:8]
s, _ = call(web, 'POST', 'api/auth/register', {'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000, 'lang': 'fr'}, H)
ok(s in (200, 201), 'sign-up of a test trader')
# 1. the plan, the add-on's events, the trades
chart = {'zones': [
    {'id': 'pdh', 'instrument': 'NQ', 'type': 'level', 'price': 21290.25, 'label': 'PDH', 'role': 'resistance', 'bias': 'short', 'proximity_ticks': 40},
    {'id': 'buy', 'instrument': 'NQ', 'type': 'zone', 'high': 21200, 'low': 21180, 'label': 'Buy zone', 'role': 'support', 'bias': 'long', 'proximity_ticks': 40}],
    'rules': [{'id': 'r1', 'trigger': 'sweep', 'zone': 'pdh', 'tf': '5m', 'action': 'plan', 'message': 'Wait for the reclaim'}]}
s, _ = call(web, 'PUT', 'api/docs/journals/' + day, {'chart': chart, 'pre': {'bias': 'bullish', 'max_loss': '400'}}, H)
ok(s == 200, f'the plan of {day} saved (2 zones, a sweep rule)')
s, k = call(web, 'POST', 'api/sync/key', {'platform': 'quantower'}, H)
AK = {'X-Sweep-Key': k.get('key', ''), 'X-Sweep-Client': 'Sweep Quantower 1.4', 'Content-Type': 'application/json'}
evs = [{'id': 'pf-a-' + uuid.uuid4().hex[:10], 'type': 'zone_approached', 'at': at(5), 'instrument': 'MNQZ6', 'price': 21208.5, 'zone': 'buy'},
       {'id': 'pf-e-' + uuid.uuid4().hex[:10], 'type': 'zone_entered', 'at': at(4), 'instrument': 'MNQZ6', 'price': 21199.75, 'zone': 'buy'},
       {'id': 'pf-s-' + uuid.uuid4().hex[:10], 'type': 'rule_triggered', 'at': at(2), 'instrument': 'NQZ6', 'price': 21292, 'zone': 'pdh', 'rule': 'r1'}]
s, r = call(bare, 'POST', 'api/plan-sync/events', {'events': evs}, AK)
ok(s == 200 and r.get('accepted') == 3, f'3 events sent by the test add-on key ({s} {r})')
for tid, m, dirn, px, inst in (('pf_t1', 3, 'long', 21190, 'MNQ'), ('pf_t2', 1, 'long', 21240, 'NQ')):
    s, _ = call(web, 'PUT', 'api/docs/trades/' + tid, {'date': day, 'session_date': True, 'entry_time': hm(m), 'exit_time': hm(m), 'direction': dirn, 'entry': px, 'exit': px + 5,
                                                      'instrument': inst, 'contracts': 1, 'pnl': 100, 'net': 100}, H)
    ok(s == 200, f'trade {tid} ({dirn} {inst} {px} at {hm(m)} New York)')
# 2. the server's read
s, pdy = call(web, 'GET', 'api/sync/plan-day?day=' + day, None, H)
f = pdy.get('follow') or {}
ok(s == 200 and [e['type'] for e in pdy.get('events', [])] == ['zone_approached', 'zone_entered', 'rule_triggered'], 'api/sync/plan-day: the 3 events, oldest first')
ok(f.get('n') == 2 and f.get('in') == 1 and (f.get('trades') or {}).get('pf_t1') == {'in': True, 'zone': 'buy'} and not f['trades']['pf_t2']['in'], f'1 of 2 trades in the plan (the buy zone; the other between the zones): {f}')
ok(call(bare, 'GET', 'api/sync/plan-day?day=' + day, None, {'X-Sweep-Key': AK['X-Sweep-Key']})[0] == 401, 'the day\'s read needs the signed-in trader (the key alone: 401)')

# 3. the journal day and the end-of-day review, in the browser
X = {'fr': {'line': '1 trade sur 2 dans les zones de ton plan', 'sweep': 'PDH sweepé (5m), rappel du plan affiché', 'near': 'Prix proche de Buy zone, alerte affichée',
            'touch': 'Le prix touche Buy zone, alerte affichée', 'tin': 'Trade long MNQ · dans le plan (Buy zone)', 'tout': 'Trade long NQ · hors plan', 'tip': 'long = achat', 'stip': 'Sweep :',
            'q': 'suivi', 'np': 'Pas de plan', 'all': 'tous dans ton plan', 'locale': 'fr-CA', 'title': 'Sur le chart'},
     'en': {'line': '1 of 2 trades in your plan’s zones', 'sweep': 'Sweep of PDH (5m), plan reminder shown', 'near': 'Price close to Buy zone, alert shown',
            'touch': 'Price touches Buy zone, alert shown', 'tin': 'Trade long MNQ · in the plan (Buy zone)', 'tout': 'Trade long NQ · off plan', 'tip': 'long = buy', 'stip': 'Sweep:',
            'q': 'follow', 'np': 'No plan', 'all': 'all in your plan', 'locale': 'en-US', 'title': 'On the chart'},
     'es': {'line': '1 de 2 operaciones en las zonas de tu plan', 'sweep': 'Sweep de PDH (5m), recordatorio del plan mostrado', 'near': 'Precio cerca de Buy zone, alerta mostrada',
            'touch': 'El precio toca Buy zone, alerta mostrada', 'tin': 'Operación long MNQ · en el plan (Buy zone)', 'tout': 'Operación long NQ · fuera del plan', 'tip': 'long = compra', 'stip': 'Sweep:',
            'q': 'segui', 'np': 'Sin plan', 'all': 'todas dentro de tu plan', 'locale': 'es-ES', 'title': 'En el gráfico'}}
ORDER = ['near', 'touch', 'tin', 'sweep', 'tout']
RUNS = [(390, True, 'fr', 'dark'), (1300, False, 'fr', 'light'), (390, True, 'en', 'light'), (1300, False, 'en', 'dark'), (390, True, 'es', 'light'), (1300, False, 'es', 'dark')]
FIT = """(sel) => { const box = document.querySelector(sel); if (!box) return 'missing'; const r = box.getBoundingClientRect(), bad = [];
  box.querySelectorAll('li, p, h4, summary').forEach((x) => { const q = x.getBoundingClientRect(); if (q.width && (q.left < r.left - 1 || q.right > r.right + 1)) bad.push('out: ' + x.textContent.slice(0, 40)); });
  box.querySelectorAll('li').forEach((li) => { const t = li.querySelector('time').getBoundingClientRect(), s = li.querySelector('span').getBoundingClientRect(); if (t.right > s.left + 0.5) bad.push('overlap: ' + li.textContent.slice(0, 40)); if (li.querySelector('time').scrollWidth > li.querySelector('time').clientWidth + 1) bad.push('cut: ' + li.textContent.slice(0, 20)); });
  if (document.documentElement.scrollWidth > innerWidth + 1) bad.push('page ' + document.documentElement.scrollWidth); return bad.join(' | '); }"""
from playwright.sync_api import sync_playwright
host = urllib.parse.urlparse(B).hostname
cookies = [{'name': c.name, 'value': c.value, 'domain': host, 'path': c.path or '/'} for c in jar]
with sync_playwright() as pw:
    br = pw.chromium.launch(); errs = []
    for w, phone, lang, scheme in RUNS:
        x = X[lang]; tag = f'{w}-{lang}-{scheme}'
        cx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale=x['locale'], color_scheme=scheme)
        cx.add_cookies(cookies); cx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
        pg = cx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
        # the journal day: its recap
        pg.goto(B + '/#journal/' + day)
        for _ in range(120):
            if pg.evaluate("!!(window.SweepPlanChart && window.SweepGame && document.querySelector('.nav-recap .pc-day'))"): break
            pg.wait_for_timeout(150)
        pg.wait_for_timeout(600)
        jt = pg.locator('.nav-recap .pc-day').inner_text() if pg.locator('.nav-recap .pc-day').count() else ''
        ok(x['title'] in jt and x['line'] in jt and x['sweep'] in jt and x['tin'] in jt and x['tout'] in jt, f'{tag} journal: the recap says « {x["line"]} » and shows the time line ({jt[:90]!r})')
        bad = pg.evaluate(FIT, '.nav-recap .pc-day'); ok(bad == '', f'{tag} journal: nothing cut, overlapping or wider than the screen ({bad})')
        pg.locator('.nav-recap .pc-day').scroll_into_view_if_needed(); pg.wait_for_timeout(300)
        pg.screenshot(path=f'/tmp/sweep-plan-follow-{w}-{lang}-journal.png')
        # the end-of-day review
        pg.evaluate('(d) => SweepGame.openReview(d)', day)
        for _ in range(80):
            if pg.evaluate("!!document.querySelector('#gSheet.g-rv .pc-day')"): break
            pg.wait_for_timeout(150)
        pg.wait_for_timeout(700)
        sh = pg.locator('#gSheet.g-rv .pc-day')
        rt = sh.inner_text() if sh.count() else ''
        ok(x['line'] in rt, f'{tag} review: « {x["line"]} »')
        items = pg.evaluate("[...document.querySelectorAll('#gSheet.g-rv .pc-day .pc-tl li span')].map((s) => s.textContent)")
        want = [x[k] for k in ORDER]
        ok(items == want, f'{tag} review: the time line in New York order: approach, touch, the trade in the plan, the sweep and its reminder, the trade off plan ({items})')
        ok(x['tip'] in rt and x['stip'] in rt, f'{tag} review: the words explained where they show (long / short, sweep)')
        above = pg.evaluate("(() => { const a = document.querySelector('#gSheet.g-rv .pc-day'), b = document.querySelector('#gSheet.g-rv .g-seg3'); return !!(a && b && (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING)); })()")
        ok(above, f'{tag} review: above « Did you follow your plan? »')
        dots = pg.evaluate("[...document.querySelectorAll('#gSheet.g-rv .pc-tl-t')].map((li) => getComputedStyle(li.querySelector('span'), '::before').backgroundColor)")
        ok(len(dots) == 2 and dots[0] != dots[1], f'{tag} review: the trade in the plan marked in blue, the other in neutral grey ({dots})')
        bad = pg.evaluate(FIT, '#gSheet.g-rv .pc-day'); ok(bad == '', f'{tag} review: nothing cut, overlapping or wider than the screen ({bad})')
        pg.screenshot(path=f'/tmp/sweep-plan-follow-{w}-{lang}-review.png')
        cx.close()
    # 4. (14 Nov.) the journal's recap and the coach say the same: a trader on his sign-up session, no plan, 2 trades without a
    # mistake — the recap says « No plan » (as Today: « 2 trades · no plan »), never « 0 / 2 », and the coach's lesson never
    # « all in your plan » (no reproach either, R2). The server's own day (its game clock), so the day is in game_days
    jar2 = http.cookiejar.CookieJar(); web2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar2))
    s, _ = call(web2, 'POST', 'api/auth/register', {'password': 'Testpass123!', 'email': 'pfnp' + uuid.uuid4().hex[:8] + '@t.dev', 'consent': True, 'elapsed': 6000, 'lang': 'fr'}, H)
    sday = call(web2, 'GET', 'api/game/history?from=2026-01-01&to=2026-01-01', None, H)[1].get('today') or day
    for tid, hh in (('np_t1', '09:40'), ('np_t2', '10:10')):
        call(web2, 'PUT', 'api/docs/trades/' + tid, {'date': sday, 'entry_time': hh, 'exit_time': hh, 'direction': 'long', 'entry': 21000, 'exit': 21005, 'stop': 20990,
                                                     'instrument': 'NQ', 'contracts': 1, 'pnl': 100, 'net': 100}, H)
    cookies2 = [{'name': c.name, 'value': c.value, 'domain': host, 'path': c.path or '/'} for c in jar2]
    for w, phone, lang, scheme in RUNS:
        x = X[lang]; tag = f'{w}-{lang}-{scheme} no plan'
        cx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale=x['locale'], color_scheme=scheme)
        cx.add_cookies(cookies2); cx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
        pg = cx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
        pg.goto(B + '/#journal/' + sday)
        ex = ''
        for _ in range(120):
            ex = pg.evaluate("(() => { const b = [...document.querySelectorAll('.nav-recap .nav-recap-g > div')][1]; const t = b ? b.querySelector('b').textContent.trim() : ''; return t === '…' ? '' : t; })()")
            if ex and pg.evaluate("!!window.SweepCoach"): break
            pg.wait_for_timeout(150)
        ls = pg.evaluate("(() => { const l = window.SweepCoach && SweepCoach.lesson('%s'); return l ? l.text : ''; })()" % sday)
        ok(ex == x['np'] and ls != '' and x['all'] not in ls, f'{tag}: the recap says « {ex} », the coach agrees ({ls[:70]!r})')
        bad = pg.evaluate(FIT, '.nav-recap'); ok(bad == '', f'{tag}: the recap, nothing cut or overlapping ({bad})')
        pg.screenshot(path=f'/tmp/sweep-plan-follow-{w}-{lang}-noplan.png')
        cx.close()
    br.close()
ok(not errs, 'no page error (%s)' % errs[:2])
call(web, 'DELETE', 'api/sync/key?platform=quantower', None, H)

print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
