"""
Sweep — sharing (brief 02 part 12), Playwright, phone (fr, es: Android Chrome) and computer (en):
  python3 tests/e2e_share.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
 - the Discipline card first, everywhere: from Stats, from Mon argent (« net »), from a payout; the card asked for one tap
   away (« Mon argent », « Payout »); streak, discipline, days swept (« Journées balayées »), the FIRST name, no dollar until
   « Afficher les montants »; « Afficher mon nom » off: no name;
 - the image itself: a PNG of the format's size (1080 × 1350, 1080 × 1920, 1200 × 675), handed to the system share sheet as a
   file (navigator.share with files, as Android Chrome and iPhone Safari do);
 - « Créer un lien »: the page's preview tags (og:image = the wide preview 1200 × 675, its size, og:url, twitter:card and
   title), noindex; the preview image served;
 - the public discipline profile: off by default in Settings › Profile; on: a personal link, the page (first name, 4 weeks,
   no amount, noindex), « Vérifié » once every trade comes from a sync (sync_trades), off again: « not public » (404).
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, re, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
X = {
  'fr': {'disc': 'Discipline', 'swept': 'Journées balayées', 'streak': 'Série', 'card': 'Ma discipline', 'net': 'Mon argent', 'pay': 'Payout', 'amounts': 'Afficher les montants',
         'pub': 'Profil public de discipline', 'sub': 'Discipline · 4 dernières semaines', 'ver': 'Vérifié', 'gone': 'Ce profil n’est pas public.', 'al': 'fr-CA,fr;q=0.9'},
  'en': {'disc': 'Discipline', 'swept': 'Days swept', 'streak': 'Streak', 'card': 'My discipline', 'net': 'My money', 'pay': 'Payout', 'amounts': 'Show amounts',
         'pub': 'Public discipline profile', 'sub': 'Discipline · last 4 weeks', 'ver': 'Verified', 'gone': 'This profile is not public.', 'al': 'en-US,en;q=0.9'},
  'es': {'disc': 'Disciplina', 'swept': 'Días barridos', 'streak': 'Racha', 'card': 'Mi disciplina', 'net': 'Mi dinero', 'pay': 'Payout', 'amounts': 'Mostrar importes',
         'pub': 'Perfil público de disciplina', 'sub': 'Disciplina · últimas 4 semanas', 'ver': 'Verificado', 'gone': 'Este perfil no es público.', 'al': 'es-ES,es;q=0.9'},
}
# canvas text recorder and the system share sheet stand-in
INIT = """(() => {
  const T = []; window.__txt = T; const f = CanvasRenderingContext2D.prototype.fillText;
  CanvasRenderingContext2D.prototype.fillText = function (s, ...a) { T.push(String(s)); return f.call(this, s, ...a); };
  window.__shared = null;
  navigator.canShare = () => true;
  navigator.share = async (d) => { window.__shared = { files: (d.files || []).map((x) => [x.name, x.type, x.size]), text: d.text || '', url: d.url || '' }; };
})();"""
SEED = """() => {
  const ago = (k) => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - k); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  put('accounts', { id: 'a', name: 'Main 50K', status: 'active', starting_balance_c: 5000000, rules: {} });
  [[1, { plan: 'y', stop: 'y' }], [2, { plan: 'y', stop: 'n' }], [3, { plan: 'y', stop: 'y' }]].forEach(([k, dsc], i) => put('trades', { id: 'x' + i, account_id: 'a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 125000, date: ago(k), session_date: true, entry_time: '09:45:00', exit_time: '10:00:00', discipline: dsc }));
  put('payouts', { id: 'p1', account_id: 'a', status: 'paid', amount_c: 150000, net_c: 150000, request_date: ago(5), payment_date: ago(3), paid_on: ago(3) });
  render(); }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"
DRAWN = "() => window.__txt.join(' | ')"

def card(pg):   # the card drawn and its texts
  pg.wait_for_function("() => SH && SH.blob && document.querySelector('#shPanel .sh-prev img')", timeout=15000); pg.wait_for_timeout(250)
  return pg.evaluate(DRAWN)
def redraw(pg, f):
  pg.evaluate("window.__txt.length = 0; SH.blob = null"); f(); return card(pg)

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  ctx.add_init_script(INIT)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'share%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Noa', 'last_name': 'Tremblay', 'experience': 'gt1'}), headers=H)
  ctx.request.post(B + '/api/me/name', data=json.dumps({'full_name': 'Noa Tremblay'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(1000)
  uid = pg.evaluate("S.me && S.me.id")
  # 1. from Mon argent (« net »): the Discipline card first, « Mon argent » one tap away
  t = redraw(pg, lambda: pg.evaluate("openShare('net', 'all')"))
  seg = pg.evaluate(TXT, '#shPanel .nav-dk button'); on = pg.evaluate(TXT, '#shPanel .nav-dk button.on')
  ok(pg.evaluate("SH.kind") == 'discipline' and seg == [x['disc'], x['net']] and on == [x['disc']], f"{tag} from Mon argent: the Discipline card first, « {x['net']} » next to it ({seg})")
  ok(x['card'] in t and x['streak'] in t and x['swept'] in t and 'Noa' in t and 'Tremblay' not in t and '$' not in t, f"{tag} the card: « {x['card']} », streak, « {x['swept']} », the first name only, no dollar ({t[:180]})")
  ok(pg.evaluate("SH.amounts") is False and not pg.evaluate("!!document.querySelector('#shPanel [data-sh]')"), f"{tag} amounts off by default; no amount or firm switch on the Discipline card (nothing to hide)")
  if SHOTS: pg.locator('#shPanel').screenshot(path=os.path.join(SHOTS, f'p12-disc-{tag}.png'))
  ok(pg.evaluate(WIDE) <= 1, f'{tag} nothing wider than the window')
  # the image, each format: the right size, handed to the share sheet as a PNG file
  sizes = {}
  for fmt, wh in (('post', [1080, 1350]), ('story', [1080, 1920]), ('wide', [1200, 675])):
    redraw(pg, lambda: pg.click(f'#shPanel [data-sh-fmt="{fmt}"]'))
    sizes[fmt] = pg.evaluate("createImageBitmap(SH.blob).then((b) => [b.width, b.height])")
  ok(sizes == {'post': [1080, 1350], 'story': [1080, 1920], 'wide': [1200, 675]}, f"{tag} the image: 1080 × 1350, 1080 × 1920, 1200 × 675 ({sizes})")
  redraw(pg, lambda: pg.click('#shPanel [data-sh-fmt="post"]'))
  pg.click('#shPanel [data-sh-act="share"]'); pg.wait_for_function("window.__shared", timeout=5000)
  sh = pg.evaluate("window.__shared")
  ok(len(sh['files']) == 1 and re.match(r'^sweep-discipline-\d{4}-\d{2}-\d{2}\.png$', sh['files'][0][0]) and sh['files'][0][1] == 'image/png' and sh['files'][0][2] > 20000 and 'makeitsweep.com' in sh['text'],
     f"{tag} « Partager »: the system share sheet gets the PNG file and the caption ({sh['files']})")
  # the card asked for, one tap away; amounts only when turned on
  t = redraw(pg, lambda: pg.click('#shPanel .nav-dk button:nth-child(2)'))
  ok(pg.evaluate("SH.kind") == 'net' and '$' not in t and pg.evaluate("document.querySelector('#shPanel [data-sh=\"amounts\"]').checked") is False, f"{tag} « {x['net']} »: the money card, « {x['amounts']} » off, no dollar")
  t = redraw(pg, lambda: pg.click('#shPanel .sh-tg label:has([data-sh="amounts"]) .sw'))
  ok('$' in t, f"{tag} « {x['amounts']} » on: the amounts")
  pg.evaluate("SH.amounts = false; closeShare()"); pg.wait_for_timeout(400)
  # from a payout: Discipline first too
  redraw(pg, lambda: pg.evaluate("openShare('payout', 'p1')"))
  ok(pg.evaluate("SH.kind") == 'discipline' and pg.evaluate(TXT, '#shPanel .nav-dk button') == [x['disc'], x['pay']], f"{tag} from a payout: Discipline first, « {x['pay']} » next to it")
  # « Show my name » off: no name on the Discipline card
  t = redraw(pg, lambda: pg.click('#shPanel .sh-tg label:has([data-shname]) .sw'))
  ok('Noa' not in t, f'{tag} « Afficher mon nom » off: no name on the card')
  t = redraw(pg, lambda: pg.click('#shPanel .sh-tg label:has([data-shname]) .sw'))
  # 2. « Créer un lien »: the preview tags, the wide preview
  pg.click('#shPanel [data-shl="create"]'); pg.wait_for_selector('#shPanel .nav-shl-row input', timeout=15000)
  url = pg.input_value('#shPanel .nav-shl-row input'); sid = url.rsplit('/', 1)[-1]
  r = ctx.request.get(B + '/s/' + sid); html = r.text()
  meta = dict(re.findall(r'<meta (?:property|name)="([^"]+)" content="([^"]*)"', html))
  ok(r.status == 200 and r.headers.get('x-robots-tag') == 'noindex' and meta.get('og:image', '').endswith('/s/%s-og.png' % sid) and meta.get('og:image:width') == '1200' and meta.get('og:image:height') == '675'
     and meta.get('twitter:card') == 'summary_large_image' and meta.get('twitter:title') == meta.get('og:title') and meta.get('og:url', '').endswith('/s/' + sid) and '$' not in meta.get('og:description', '$'),
     f"{tag} the link's page: og:image the wide preview 1200 × 675, og:url, twitter:card and title, noindex, no dollar ({meta.get('og:title')})")
  im = ctx.request.get(B + '/s/%s-og.png' % sid)
  ok(im.status == 200 and im.headers.get('content-type') in ('image/jpeg', 'image/png') and len(im.body()) > 10000, f"{tag} the preview image served ({im.status}, {im.headers.get('content-type')})")
  pg.evaluate("closeShare()"); pg.wait_for_timeout(300)
  # 3. the public discipline profile
  pg.goto(B + '/#settings'); pg.wait_for_selector('#main .nav-set-prof [data-pub]:not([disabled])', timeout=20000); pg.wait_for_timeout(300)
  ok(pg.evaluate(TXT, '#main .nav-pub-row b') == [x['pub']] and not pg.evaluate("document.querySelector('#main [data-pub]').checked") and not pg.evaluate("!!document.querySelector('#main .nav-pub-link')"),
     f"{tag} Settings › Profile: « {x['pub']} », off by default")
  pg.click('#main .nav-pub-row .sw'); pg.wait_for_selector('#main .nav-pub-link input', timeout=10000); pg.wait_for_timeout(300)
  purl = pg.input_value('#main .nav-pub-link input'); slug = purl.rsplit('/', 1)[-1]
  ok(re.match(r'^https?://[^/]+/p/[A-Za-z0-9]{14}$', purl) is not None, f"{tag} on: a personal link ({purl})")
  if SHOTS: pg.locator('#main .nav-set-prof').screenshot(path=os.path.join(SHOTS, f'p12-settings-{tag}.png'))
  ok(pg.evaluate(WIDE) <= 1, f'{tag} Settings: nothing wider than the window')
  r = ctx.request.get(B + '/p/' + slug, headers={'Accept-Language': x['al']}); page = r.text().replace(slug, '')
  ok(r.status == 200 and r.headers.get('x-robots-tag') == 'noindex' and '<h1>Noa</h1>' in page and x['sub'] in page and '$' not in page and 'Tremblay' not in page and x['ver'] not in page,
     f"{tag} the profile page: the first name, « {x['sub']} », no dollar, no last name, not verified, noindex")
  pp = br.new_page(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}); pp.goto(B + '/p/' + slug); pp.wait_for_timeout(400)
  ok(pp.evaluate(WIDE) <= 1, f'{tag} the profile page: nothing wider than the window')
  if SHOTS: pp.screenshot(path=os.path.join(SHOTS, f'p12-profile-{tag}.png'), full_page=True)
  pp.close()
  d = sqlite3.connect(DB)
  d.execute('CREATE TABLE IF NOT EXISTS sync_trades (user_id TEXT NOT NULL, trade_id TEXT NOT NULL, doc_id TEXT NOT NULL, sync_account_id TEXT NOT NULL, sig TEXT NOT NULL, fills TEXT NOT NULL, entry_at TEXT NOT NULL, inst TEXT NOT NULL, dir TEXT NOT NULL, copy_group TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, PRIMARY KEY (user_id, trade_id))')   # (sync/sync-store.php, if no sync ran yet)
  for i, tid in enumerate(['x0', 'x1', 'x2']):
    d.execute("INSERT OR REPLACE INTO sync_trades (user_id, trade_id, doc_id, sync_account_id, sig, fills, entry_at, inst, dir, created_at, updated_at) VALUES (?, ?, ?, 'sa', 'x', '[]', '2026-10-01 09:30:00', 'NQ', 'long', 0, 0)", (uid, 'e2e%d' % i, tid))
  d.commit(); d.close()
  page = ctx.request.get(B + '/p/' + slug, headers={'Accept-Language': x['al']}).text()
  ok('✓ ' + x['ver'] in page, f"{tag} every trade from a sync: « ✓ {x['ver']} »")
  pg.click('#main .nav-pub-row .sw'); pg.wait_for_function("!document.querySelector('#main .nav-pub-link')", timeout=10000)
  r = ctx.request.get(B + '/p/' + slug, headers={'Accept-Language': x['al']})
  ok(r.status == 404 and x['gone'] in r.text() and 'Noa' not in r.text(), f"{tag} off again: « {x['gone']} » (404), nothing of the trader")
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True)
  run(p, 'en', False)
  run(p, 'es', True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
