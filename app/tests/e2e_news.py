"""
Sweep — « What's new » (16 Oct., step 1 of the announcements), Playwright:
  python3 tests/e2e_news.py http://127.0.0.1:8095
A trader of its own. Phone 390 (fr) and computer 1300 (en):
 1  the day of sign-up: no window;
 2  from the next day: one window « What's new » with each new feature and the button that does it (the reminders on the phone
    only when this device can have them and they are not on yet);
 3  a feature's button closes the window and goes there (« See my accounts » → Accounts; « Turn on » where the phone cannot:
    Settings, which says why); every feature shown is seen once, on every device: after a reload, no window;
 4  one automatic window per session: none when another one already opened;
 5  (step 3) the bell keeps them (« What's new », already read when seen in the window): a tap opens that one; the avatar
    menu › « What's new » opens the last 60 days' features, seen ones too.
No page error, nothing wider than the window.
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'h': 'Quoi de neuf', 'acc': 'Voir mes comptes', 'push': 'Des rappels sur ton téléphone', 'on': 'Activer', 'debrief': 'Débriefe ta journée, même sans trade'},
     'en': {'h': 'What’s new', 'acc': 'See my accounts', 'push': 'Reminders on your phone', 'on': 'Turn on', 'debrief': 'Debrief your day, even without trades'}}
OLD = "() => { S.me.created_at = Math.floor(Date.now() / 1000) - 3 * 86400; sessionStorage.removeItem('sw.modal'); }"
SHOWN = "() => { const s = document.querySelector('#gSheet.g-wnsheet'); return s ? { h: s.querySelector('h2').textContent, items: [...s.querySelectorAll('.g-wn-it b')].map((b) => b.textContent), btns: [...s.querySelectorAll('.g-wn-go')].map((b) => b.textContent) } : null }"
with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'nw%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Noa', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'nw-a', name: 'Apex 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, rules: { dd_c: 250000 } })"); pg.wait_for_timeout(800)
    # 1. the day of sign-up
    pg.evaluate("sessionStorage.removeItem('sw.modal'); SweepNews.show()"); pg.wait_for_timeout(900)
    ok(pg.evaluate(SHOWN) is None, f'{tag} the day of sign-up: no « {x["h"]} » window')
    # 4. another automatic window already this session
    pg.evaluate("() => { S.me.created_at = Math.floor(Date.now() / 1000) - 3 * 86400; sessionStorage.setItem('sw.modal', '1'); SweepNews.show() }"); pg.wait_for_timeout(900)
    ok(pg.evaluate(SHOWN) is None, f'{tag} one automatic window per session: none after another one')
    # 2. the next days
    pg.evaluate(OLD); pg.evaluate("SweepNews.show()"); pg.wait_for_timeout(1200)
    s = pg.evaluate(SHOWN)
    ok(s and s['h'] == x['h'] and len(s['items']) >= 2 and x['acc'] in s['btns'], f'{tag} from the next day: « {x["h"]} », each feature with its button ({s})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    if phone: pg.screenshot(path='/tmp/news_390.png')
    else: pg.screenshot(path='/tmp/news_1300.png')
    # 3. its button goes there; seen once, on every device
    pg.locator('#gSheet .g-wn-go', has_text=x['acc']).click(); pg.wait_for_timeout(1200)
    ok(pg.evaluate("location.hash") == '#accounts' and pg.evaluate(SHOWN) is None, f'{tag} « {x["acc"]} »: the window closes, Accounts opens ({pg.evaluate("location.hash")})')
    seen = pg.evaluate("(S.settings.news_seen || []).slice().sort()")
    ok(len(seen) >= 2, f'{tag} the features shown are seen ({seen})')
    pg.wait_for_timeout(1500); pg.reload(); pg.wait_for_timeout(2500)
    pg.evaluate(OLD); pg.evaluate("SweepNews.show()"); pg.wait_for_timeout(1200)
    ok(pg.evaluate(SHOWN) is None and len(pg.evaluate("S.settings.news_seen || []")) >= 2, f'{tag} after a reload (the server kept it): no window again')
    # 5. the bell and the avatar menu
    inbox = pg.evaluate("fetch('api/notifications',{headers:{'X-Requested-With':'fetch'},credentials:'same-origin'}).then(r=>r.json()).then(j=>j.items.filter(n=>n.type==='news').map(n=>[n.params.id,n.read]).sort())")
    ok(len(inbox) >= 2 and all(r for _, r in inbox), f'{tag} the bell keeps them, read (seen in the window): {inbox}')
    pg.evaluate("SweepNotify.open()"); pg.wait_for_timeout(1500)
    it = pg.locator('#ntSheet .nt-item', has_text=x['debrief'])
    ok(it.count() == 1, f'{tag} the bell: « {x["debrief"]} », in the trader\'s language')
    if it.count():
      it.click(); pg.wait_for_timeout(1400)
      s2 = pg.evaluate(SHOWN)
      ok(s2 and s2['items'] == [x['debrief']], f'{tag} a tap in the bell opens that one ({s2 and s2["items"]})')
      pg.evaluate("(document.querySelector('#gSheet [data-g=wn-ok]')||{click(){}}).click()"); pg.wait_for_timeout(500)
    pg.locator('[data-nav="menu"]').first.click(); pg.wait_for_timeout(600)
    pg.locator('#navMenu [data-navm="news"]').click(); pg.wait_for_timeout(1400)
    s3 = pg.evaluate(SHOWN)
    ok(s3 and len(s3['items']) >= 2, f'{tag} avatar menu › « {x["h"]} »: the last features, seen ones too ({s3 and s3["items"]})')
    pg.evaluate("(document.querySelector('#gSheet [data-g=wn-ok]')||{click(){}}).click()"); pg.wait_for_timeout(500)
    # the reminders: offered only when this device can have them and they are off; « Turn on » where the phone cannot → Settings
    pg.evaluate("() => { S.settings.news_seen = []; SweepNotify.push.state = async () => ({ available: true, can: false, on: false }); SweepNotify.push.on = async () => ({ available: true, can: false, on: false }); }")
    pg.evaluate(OLD); pg.evaluate("SweepNews.show()"); pg.wait_for_timeout(1200)
    s = pg.evaluate(SHOWN)
    ok(s and x['push'] in s['items'], f'{tag} the reminders off on this device: offered ({s and s["items"]})')
    pg.locator('#gSheet .g-wn-go', has_text=x['on']).click(); pg.wait_for_timeout(1200)
    ok(pg.evaluate("location.hash").startswith('#settings'), f'{tag} « {x["on"]} » where this phone cannot: Settings, which says why ({pg.evaluate("location.hash")})')
    pg.evaluate("() => { S.settings.news_seen = []; SweepNotify.push.state = async () => ({ available: true, can: true, on: true }); }")
    pg.evaluate(OLD); pg.evaluate("SweepNews.show()"); pg.wait_for_timeout(1200)
    s = pg.evaluate(SHOWN)
    ok(s and x['push'] not in s['items'], f'{tag} the reminders already on: not offered ({s and s["items"]})')
    allerr += errs; ctx.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
