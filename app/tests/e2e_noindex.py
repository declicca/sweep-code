"""
Sweep — the app is never indexed by search engines (brief « app depuis le site », 12 Oct., step 2), dev server, HTTP only:
  python3 tests/e2e_noindex.py http://127.0.0.1:8095
 - every HTML page of the app says « noindex » (X-Robots-Tag), at all the addresses the website links to (/, /?signup=1,
   the plan links, utm_* tags); a public share page and its image too (a trader's stats);
 - robots.txt does not block the app (Google must read the « noindex »);
 - the public JSON the website reads is unchanged: api/presets (rules of the firms) and api/cohort-count.php (/100 counter);
 - the project's .md files are never served.
"""
import base64, http.cookiejar, json, random, struct, sys, urllib.error, urllib.request, zlib
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
def get(path, headers=None, opener=None):
    try: r = (opener or urllib.request.build_opener()).open(urllib.request.Request(B + path, headers=headers or {})); return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e: return e.code, e.headers, e.read()
for u in ('/', '/?signup=1', '/?signup=1&plan=free', '/?signup=1&plan=pro&interval=year', '/?signup=1&plan=elite&interval=year', '/?signup=1&plan=pro&interval=year&utm_source=site&utm_campaign=prices', '/index.html'):
    st, h, _ = get(u)
    ok(st == 200 and (h.get('Content-Type') or '').startswith('text/html') and h.get('X-Robots-Tag') == 'noindex', f'{u}: HTML with « X-Robots-Tag: noindex » ({st}, {h.get("X-Robots-Tag")})')
st, h, body = get('/robots.txt')
ok(st == 404 or b'Disallow: /' not in body, f'robots.txt does not block the app ({st})')
st, h, body = get('/api/presets')
d = json.loads(body)
ok(st == 200 and d.get('origin') in ('seed', 'checked') and d.get('firms') and 'version' in d and 'checked_at' in d, f'api/presets: the JSON the website reads ({d.get("origin")}, {len(d.get("firms") or [])} firms)')
st, h, body = get('/api/cohort-count.php', {'Origin': 'https://makeitsweep.com'})
c = json.loads(body)
ok(st == 200 and set(c) == {'taken', 'total'} and h.get('Access-Control-Allow-Origin') == 'https://makeitsweep.com', f'api/cohort-count.php: the /100 counter, readable from makeitsweep.com ({c})')
for u in ('/INSTALLATION.md', '/README.md', '/CONTEXTE-APP.md', '/NOTES.md'):
    st, _, _ = get(u)
    ok(st in (403, 404), f'{u} is not served ({st})')
# a public share link and its image: a trader's stats
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
post = lambda p, b: json.load(op.open(urllib.request.Request(B + p, data=json.dumps(b).encode(), headers=H, method='POST')))
post('/api/auth/register', {'password': 'Testpass123!', 'email': 'ni%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000})
chunk = lambda t, x: struct.pack('>I', len(x)) + t + x + struct.pack('>I', zlib.crc32(t + x) & 0xffffffff)
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 40, 40, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\x00' + b'\x4c\x8d\xff' * 40 for _ in range(40)))) + chunk(b'IEND', b'')
sid = post('/api/share/create', {'kind': 'week', 'card': {'label': 'Test', 'stats': [['Discipline', '67 %']]}, 'image': 'data:image/png;base64,' + base64.b64encode(png).decode(), 'lang': 'fr'}).get('id', '')
for u in ('/s/' + sid, '/s/' + sid + '.png'):
    st, h, _ = get(u)
    ok(st == 200 and h.get('X-Robots-Tag') == 'noindex', f'share {"image" if u.endswith(".png") else "page"}: « noindex » ({st}, {h.get("X-Robots-Tag")})')
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
