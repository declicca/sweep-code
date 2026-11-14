"""Sweep — Plan Sync step 2 over HTTP: the add-ons' API (api/plan-sync/today, api/plan-sync/events) with the sync key alone.
Valid / wrong / revoked key, the other platform's add-on, the day's plan for MNQ, ETag and 304, a plan changed → 200 again,
events kept once, the rate limit, « Synced with Quantower » in api/sync. Its own trader, no browser.
  python3 tests/e2e_plan_sync.py [BASE]"""
import json, sys, uuid, urllib.parse, urllib.request, urllib.error, http.cookiejar
from datetime import datetime, timezone

B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').rstrip('/')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
jar = http.cookiejar.CookieJar(); web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
bare = urllib.request.build_opener()   # the add-on: no cookie, no session
fails = 0

def ok(c, what):
    global fails
    if not c: fails += 1
    print(('ok   ' if c else 'FAIL ') + what)

def call(op, method, path, body=None, headers=None):
    """status, json body (or {}), response headers"""
    req = urllib.request.Request(B + '/' + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=headers or {})
    try:
        with op.open(req, timeout=30) as r:
            raw = r.read(); return r.status, (json.loads(raw) if raw else {}), r.headers
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, (json.loads(raw) if raw else {}), e.headers
        except Exception: return e.code, {}, e.headers

n = 'psync' + uuid.uuid4().hex[:8]
s, _, _ = call(web, 'POST', 'api/auth/register', {'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000, 'lang': 'es'}, H)
ok(s in (200, 201), 'sign-up of a test trader (Spanish)')
s, k, _ = call(web, 'POST', 'api/sync/key', {'platform': 'quantower'}, H)
key = k.get('key', '')
ok(s == 200 and key.startswith('swk_'), 'a Quantower key (the same key as the trade sync)')
AK = {'X-Sweep-Key': key, 'X-Sweep-Client': 'Sweep Quantower 1.4'}

# the key decides, never a session
s, b, _ = call(web, 'GET', 'api/plan-sync/today?instrument=NQ', None, H)
ok(s == 401 and b.get('code') == 'key' and set((b.get('messages') or {}).keys()) == {'en', 'fr', 'es'}, 'a session without the key → 401, the way back in EN, FR and ES')
ok(call(bare, 'GET', 'api/plan-sync/today', None, {'X-Sweep-Key': 'swk_' + '0' * 40})[0] == 401, 'a wrong key → 401')
s, b, _ = call(bare, 'GET', 'api/plan-sync/today', None, {'X-Sweep-Key': key, 'X-Sweep-Client': 'Sweep NT8 1.4'})
ok(s == 401 and b.get('code') == 'platform', 'the Quantower key in the NinjaTrader add-on → 401 « platform »')
ok(call(bare, 'POST', 'api/plan-sync/today', {}, AK)[0] == 405 and call(bare, 'GET', 'api/plan-sync/events', None, AK)[0] == 405, 'wrong methods → 405')

# no plan yet
s, p0, h0 = call(bare, 'GET', 'api/plan-sync/today?instrument=MNQZ6', None, AK)
day = p0.get('day', '')
ok(s == 200 and p0.get('empty') is True and p0.get('zones') == [] and p0.get('instrument') == 'NQ' and p0.get('lang') == 'es' and len(day) == 10, 'no plan today: 200, empty, MNQZ6 read as NQ, the trader\'s language (' + day + ')')
ok(isinstance(p0.get('limits'), dict) and 'max_loss_c' in p0['limits'] and 'accounts' in p0['limits'], 'the limits Sweep knows are there (read from the guardian and the routine)')
ok(h0.get('ETag') == '"%s"' % p0.get('version') and 'no-store' not in (h0.get('Cache-Control') or ''), 'ETag = the version')

# the editor saves zones and rules (journals/{day}.chart, step 1)
chart = {'zones': [
    {'id': 'pdh', 'instrument': 'NQ', 'type': 'level', 'price': 21290.25, 'label': 'PDH', 'role': 'resistance', 'bias': 'short', 'note': 'Sweep then back under', 'proximity_ticks': 40},
    {'id': 'gc1', 'instrument': 'GC', 'type': 'zone', 'high': 2650.5, 'low': 2648, 'label': 'Gold zone', 'role': 'support', 'proximity_ticks': 20}],
    'rules': [{'id': 'r1', 'trigger': 'sweep', 'zone': 'pdh', 'tf': '5m', 'action': 'plan', 'message': 'Esperar el retorno'}]}
s, _, _ = call(web, 'PUT', 'api/docs/journals/' + day, {'chart': chart, 'pre': {'bias': 'bearish', 'max_loss': '400', 'max_trades': 3}}, H)
ok(s == 200, 'the day\'s plan saved in the app')
s, p1, h1 = call(bare, 'GET', 'api/plan-sync/today?instrument=MNQ', None, AK)
ok(s == 200 and p1.get('empty') is False and [z['id'] for z in p1.get('zones', [])] == ['pdh'] and [r['id'] for r in p1.get('rules', [])] == ['r1'] and p1.get('version') != p0.get('version'), 'MNQ gets the NQ level and its rule (not the gold zone), a new version')
ok((p1.get('plan') or {}).get('bias') == 'bearish' and p1['limits'].get('max_loss_c') == 40000 and p1['limits'].get('max_trades') == 3, 'the plan\'s bias, its max loss and max trades read from the day\'s plan')
etag = h1.get('ETag')
s, b, h = call(bare, 'GET', 'api/plan-sync/today?instrument=MNQ', None, dict(AK, **{'If-None-Match': etag}))
ok(s == 304 and b == {} and h.get('ETag') == etag, 'If-None-Match with the same version → 304, no body')
ok(call(bare, 'GET', 'api/plan-sync/today?instrument=MNQ', None, dict(AK, **{'If-None-Match': 'W/' + etag[:-1] + '-gzip"'}))[0] == 304, 'a weak or « -gzip » ETag is the same version → 304')
chart['zones'][0]['price'] = 21300
call(web, 'PUT', 'api/docs/journals/' + day, {'chart': chart}, H)
s, p2, _ = call(bare, 'GET', 'api/plan-sync/today?instrument=MNQ', None, dict(AK, **{'If-None-Match': etag}))
ok(s == 200 and p2['zones'][0]['price'] == 21300 and p2['version'] != p1['version'], 'the level moved in the app: the old ETag gets the new plan (200)')
ok(call(bare, 'GET', 'api/plan-sync/today?instrument=CL', None, AK)[1].get('zones') == [], 'CL, no zone: nothing to draw')

# « Synced with Quantower · … ago » in the editor
s, st, _ = call(web, 'GET', 'api/sync', None, H)
ok(s == 200 and st.get('plan_read_by') == 'quantower' and isinstance(st.get('plan_read_at'), int) and st['plan_read_at'] > 0, 'api/sync: the plan was read by Quantower just now')

# events
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
evs = [{'id': 'qt-' + uuid.uuid4().hex[:12], 'type': t, 'at': now, 'instrument': 'MNQZ6', 'price': 21300.5, 'zone': 'pdh', **({'rule': 'r1'} if t == 'rule_triggered' else {})} for t in ('zone_approached', 'zone_entered', 'rule_triggered', 'addon_heartbeat')]
s, r, _ = call(bare, 'POST', 'api/plan-sync/events', {'events': evs}, dict(AK, **{'Content-Type': 'application/json'}))
ok(s == 200 and r == {'ok': True, 'accepted': 4, 'duplicates': 0, 'rejected': 0}, 'a batch of 4 events (one heartbeat) accepted')
s, r, _ = call(bare, 'POST', 'api/plan-sync/events', {'events': evs}, dict(AK, **{'Content-Type': 'application/json'}))
ok(s == 200 and r.get('duplicates') == 3 and r.get('accepted') == 1, 'the same batch again: the 3 events ignored (their ids), the heartbeat counted')
s, r, _ = call(bare, 'POST', 'api/plan-sync/events', {'events': [{'id': 'qt-order-0001', 'type': 'order_sent', 'at': now}]}, dict(AK, **{'Content-Type': 'application/json'}))
ok(s == 200 and r.get('rejected') == 1 and r.get('accepted') == 0, 'an unknown type is refused (no order, ever)')
ok(call(bare, 'POST', 'api/plan-sync/events', {'events': {'a': 1}}, dict(AK, **{'Content-Type': 'application/json'}))[0] == 400, 'events must be a list → 400')
ok(call(bare, 'POST', 'api/plan-sync/events', {'events': [{}] * 101}, dict(AK, **{'Content-Type': 'application/json'}))[0] == 413, 'more than 100 events in one request → 413')

# the rate limit: 20 batches a minute per trader (the add-on sends one every 30 s)
codes = [call(bare, 'POST', 'api/plan-sync/events', {'events': []}, dict(AK, **{'Content-Type': 'application/json'}))[0] for _ in range(25)]
ok(429 in codes and all(c == 200 for c in codes[:codes.index(429)]), 'event batches past 20 a minute → 429')

# the editor in the browser: « Synced with Quantower · … ago » (phone 390 touch dark, computer 1300 light; FR, ES)
from playwright.sync_api import sync_playwright
ON = {'fr': 'Synchronisé avec Quantower · il y a', 'es': 'Sincronizado con Quantower · hace'}
host = urllib.parse.urlparse(B).hostname
cookies = [{'name': c.name, 'value': c.value, 'domain': host, 'path': c.path or '/'} for c in jar]
with sync_playwright() as pw:
    br = pw.chromium.launch(); errs = []
    for w, phone, lang, scheme in ((390, True, 'fr', 'dark'), (1300, False, 'es', 'light')):
        tag = f'{w}-{lang}-{scheme}'
        cx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'es-ES', color_scheme=scheme)
        cx.add_cookies(cookies); cx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
        pg = cx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
        pg.goto(B + '/#dashboard')
        for _ in range(100):
            if pg.evaluate('!!(window.SweepPlanChart && window.S && S.journals)'): break
            pg.wait_for_timeout(150)
        pg.wait_for_timeout(800)
        pg.evaluate('(d) => SweepPlanChart.open(d)', day)
        line = pg.locator('#pcSheet .pc-sync.on')
        try: line.wait_for(state='visible', timeout=8000)
        except Exception: pass
        txt = line.inner_text() if line.count() else ''
        ok(ON[lang] in txt, f'{tag}: the editor says the plan was read: {txt!r}')
        wd = pg.evaluate('document.documentElement.scrollWidth')
        ok(wd <= w + 1, f'{tag}: nothing overflows ({wd})')
        if w == 390: pg.screenshot(path='/tmp/sweep-plan-sync-390.png')
        cx.close()
    br.close()
    ok(not errs, 'no page error (%s)' % errs[:2])

# a revoked key
call(web, 'DELETE', 'api/sync/key?platform=quantower', None, H)
s, b, _ = call(bare, 'GET', 'api/plan-sync/today?instrument=NQ', None, AK)
ok(s == 401 and b.get('code') == 'key', 'stop the sync: the key no longer reads the plan (401, the way back)')
ok(call(web, 'GET', 'sync/plan-sync.php', None, H)[0] in (403, 404), 'the code is never served directly')

print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
