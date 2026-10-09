"""
Sweep — the real net from the start (step 1 of the evolution brief), dev environment with Playwright:
  python3 tests/e2e_realnet.py http://127.0.0.1:8095 [storage_state, unused: every case signs up its own trader]
A. New trader, 3 languages × phone and computer: profile → « How long have you been trading? » (kept on the server) →
   Topstep 50K → « Account added » (never the trade window) → « + Add another account » → Apex 50K → catch-up:
   period, purchases per firm (Topstep: months of subscription at $49, activation $149, « already in My money »;
   Apex: no catalogue price, typed), net payouts → the real net screen. Checks: the real net = moneyOf = My money for the
   same period, the estimated entries carry « Estimated », no English in FR/ES, nothing wider than the window, taps ≥ 44 px.
B. « I'll do it later » → Today's My money card offers « Your real net in 1 minute » → hidden with ✕ (stays hidden).
C. An existing trader: « Complete your history in 1 minute » on one day only.
D. My money: an estimate is edited in its small form; an exact purchase in the period shows the reminder; the CSV says « estimé ».
"""
import json, os, sqlite3, sys, time, re
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():   # every case signs up a trader: the sign-up limiter (5 per hour) is cleared on the dev database
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
EXP = {'fr': 'Tu trades depuis combien de temps ?', 'en': 'How long have you been trading?', 'es': '¿Desde cuándo operas?'}
ADDED = {'fr': 'Compte ajouté', 'en': 'Account added', 'es': 'Cuenta añadida'}
MONTHS = {'fr': 'Mois d’abonnement', 'en': 'Months of subscription', 'es': 'Meses de suscripción'}
POS = {'fr': 'Tu es rentable de', 'en': 'You’re up', 'es': 'Eres rentable en'}
NEG = {'fr': 'C’est ton point de départ', 'en': 'This is your starting point', 'es': 'Este es tu punto de partida'}
EN_ONLY = ['Account added', 'Continue', 'Add another account', 'Since when', 'Your purchases', 'Months of subscription', 'Evaluations', 'I’ll do it later', 'See my real net', 'Your real net', 'Spent', 'Received', 'Let’s go', 'Already in My money']
digits = lambda s: re.sub(r'[^0-9−-]', '', s or '').replace('−', '-')

def new_trader(p, lang, phone, profile=False):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1440, 'height': 900}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  n = 'rn%d' % int(time.time() * 1000)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  if profile: ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Lea', 'last_name': 'Test'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  return br, pg, errs

def tap(pg, sel):
  last = None
  for _ in range(6):
    try: pg.locator(sel).first.click(timeout=3000); pg.wait_for_timeout(220); return
    except Exception as e: last = e; pg.wait_for_timeout(300)
  raise last

def add_account(pg, firm, typ, size='50000'):
  tap(pg, 'form[data-form=account] [data-st-ph0=eval]'); tap(pg, f'[data-st-firm={firm}]')
  if typ and pg.locator(f'[data-st-type={typ}]').count(): tap(pg, f'[data-st-type={typ}]')
  tap(pg, f'[data-st-size="{size}"]')
  pg.evaluate("document.querySelector('form[data-form=account]').requestSubmit()")
  pg.wait_for_selector('.rn.open h2', timeout=6000); pg.wait_for_timeout(450)

def fits(pg):   # nothing wider than the window; on a phone, every control of the window is a 44 px target
  return pg.evaluate("""(phone)=>{const e=document.querySelector('.rn'); if(!e) return 'no window';
    if(e.scrollWidth>e.clientWidth+1) return 'too wide '+e.scrollWidth+'>'+e.clientWidth;
    for(const b of e.querySelectorAll('button,input')){ if(b.offsetParent===null) continue; const r=b.getBoundingClientRect(), o=e.getBoundingClientRect();
      if(r.right>o.right+1||r.left<o.left-1) return 'outside: '+(b.textContent||b.outerHTML).slice(0,40);
      if(phone && r.height<44 && !b.classList.contains('link')) return 'small target '+r.height+': '+(b.textContent||b.outerHTML).slice(0,40); }
    return ''}""", pg.viewport_size['width'] < 600)

def case_a(p, lang, phone, per, exp):
  tag = f"{'390' if phone else '1440'}-{lang}"
  br, pg, errs = new_trader(p, lang, phone)
  t0 = time.time(); taps = 0
  pg.goto(B + '/'); pg.wait_for_selector('.nav-prof [data-pf=first_name]', timeout=15000)
  pg.fill('.nav-prof [data-pf=first_name]', 'Léa'); pg.fill('.nav-prof [data-pf=last_name]', 'Test'); tap(pg, '[data-prof-go]'); taps += 1
  try: pg.wait_for_selector('.nav-prof [data-exp]', timeout=6000)
  except Exception:   # seen 2 times in ~25 runs, never by hand: the names typed in the first milliseconds were gone → typed again once, and said
    print('      RETRY profile: the names were empty at « Continue » (%r)' % pg.evaluate("(document.querySelector('.nav-prof-err')||{}).textContent||''"))
    pg.fill('.nav-prof [data-pf=first_name]', 'Léa'); pg.fill('.nav-prof [data-pf=last_name]', 'Test'); tap(pg, '[data-prof-go]')
    pg.wait_for_selector('.nav-prof [data-exp]', timeout=8000)
  ok(EXP[lang] in pg.locator('aside.nav-prof').inner_text(), f'{tag} the question « {EXP[lang]} »')
  tap(pg, f'.nav-prof [data-exp="{exp}"]'); taps += 1; pg.wait_for_timeout(900)
  srv = pg.evaluate("fetch('api/data',{headers:{'X-Requested-With':'fetch'},credentials:'same-origin'}).then(r=>r.json()).then(j=>j.user&&j.user.experience)")
  ok(srv == (exp or None), f'{tag} experience kept on the server ({srv!r})')
  pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=15000); pg.wait_for_timeout(800)
  add_account(pg, 'topstep', None); taps += 4
  ok(pg.evaluate("!document.querySelector('#tkSlide.open, .nav-am.open, .nav-am-shot.open')"), f'{tag} « {ADDED[lang]} », not the trade window')
  ok(ADDED[lang] in pg.locator('.rn').inner_text(), f'{tag} the window says « {ADDED[lang]} »')
  if phone: pg.screenshot(path=f'/tmp/rn_{tag}_1_added.png')
  tap(pg, '[data-rn=another]'); taps += 1; pg.wait_for_timeout(900)
  pg.wait_for_selector('form[data-form=account] [data-st-ph0=eval]', timeout=8000)
  add_account(pg, 'apex', 'apex-eod'); taps += 4
  ok(pg.locator('.rn-accs li').count() == 2 and pg.evaluate("!document.querySelector('#tkSlide.open, .nav-am.open, .nav-am-shot.open')"), f'{tag} second account added from the window, the list shows 2')
  texts = []
  tap(pg, '[data-rn=start]'); taps += 1; texts.append(pg.locator('.rn').inner_text())
  if per != 'year': tap(pg, f'[data-rn-per={per}]'); taps += 1
  if per == 'date':
    d0 = pg.evaluate("(()=>{const d=new Date(todayStr()+'T12:00:00'); d.setMonth(d.getMonth()-3); d.setDate(1); return d.toISOString().slice(0,10)})()")
    pg.fill('[data-rn-from]', d0)
  ok(fits(pg) == '', f'{tag} period screen fits ({fits(pg)})')
  tap(pg, '[data-rn=buys]'); taps += 1; pg.wait_for_selector('.rn [data-rn-q]', timeout=5000)
  ts = pg.evaluate("S.accounts.find(a=>a.preset&&a.preset.startsWith('topstep')).firm_id"); ap = pg.evaluate("S.accounts.find(a=>a.preset&&a.preset.startsWith('apex')).firm_id")
  txt = pg.locator('.rn').inner_text(); texts.append(txt)
  ok(MONTHS[lang] in txt, f'{tag} Topstep asks « {MONTHS[lang]} » (monthly evaluation)')
  pv = pg.evaluate("(k)=>[...k].map(x=>(document.querySelector(`[data-rn-p=\"${x}\"]`)||{}).value)", [ts + '|evaluation', ts + '|activation', ap + '|evaluation'])
  ok(pv == ['49', '149', ''], f'{tag} prices from the catalogue: Topstep 49 / 149, Apex empty ({pv})')
  ok('49' in pg.locator('.rn-firm').first.inner_text(), f'{tag} « already in My money » shows the $49 of the account')
  ok(fits(pg) == '', f'{tag} purchases screen fits, targets ≥ 44 px on a phone ({fits(pg)})')
  if phone: pg.screenshot(path=f'/tmp/rn_{tag}_2_buys.png', full_page=True)
  def plus(k, n):
    for _ in range(n): pg.locator(f'[data-rn-q="{k}"][data-d="1"]').click(); pg.wait_for_timeout(50)
  plus(ts + '|evaluation', 3); plus(ts + '|activation', 1); plus(ap + '|evaluation', 2); plus(ap + '|reset', 1); taps += 7
  pg.fill(f'[data-rn-p="{ap}|evaluation"]', '167'); pg.fill(f'[data-rn-p="{ap}|reset"]', '80'); taps += 2
  tap(pg, '[data-rn=payouts]'); taps += 1; texts.append(pg.locator('.rn').inner_text())
  pay = '1000' if exp != 'new' else '300'
  pg.fill('[data-rn-pay]', pay); taps += 1
  tap(pg, '[data-rn=save]'); taps += 1; pg.wait_for_selector('.rn-net', timeout=5000)
  secs = time.time() - t0; txt = pg.locator('.rn').inner_text(); texts.append(txt)
  if phone: pg.screenshot(path=f'/tmp/rn_{tag}_3_net.png')
  frm = pg.evaluate("(p)=>{const t=todayStr(); return p==='month'?t.slice(0,8)+'01':p==='year'?t.slice(0,4)+'-01-01':null}", per) or d0
  m = pg.evaluate("(f)=>{const r=SweepMoney.moneyOf({from:f,to:todayStr()}).real; return [r.expenses,r.payouts,r.net]}", frm)
  exp_spent = 4900 + 3 * 4900 + 14900 + 2 * 16700 + 8000
  ok(m[0] == exp_spent and m[1] == int(pay) * 100, f'{tag} entries saved: spent {m[0]} (expected {exp_spent}), received {m[1]}')
  shown = digits(pg.locator('.rn-net-t b').inner_text())
  ok(shown == str(m[2] // 100) or shown == '+' + str(m[2] // 100) or shown.lstrip('+') == str(m[2] // 100), f'{tag} the real net shown ({shown}) = moneyOf ({m[2] // 100})')
  ok((POS[lang] if m[2] > 0 else NEG[lang]) in txt, f'{tag} the sentence matches the sign of the net')
  if lang != 'en':
    bad = [w for w in EN_ONLY if any(re.search(r'(?<![\w’])' + re.escape(w) + r'(?![\w’])', t) for t in texts)]
    ok(not bad, f'{tag} no English in the catch-up ({bad})')
  ok(fits(pg) == '', f'{tag} real net screen fits ({fits(pg)})')
  tap(pg, '[data-rn=close]'); pg.wait_for_timeout(900)
  st = pg.evaluate("S.settings.realnet||{}")
  ok(st.get('state') == 'done' and pg.locator('.rn-inv').count() == 0 and pg.locator('.rn.open').count() == 0, f'{tag} done: window closed, no invitation on Today')
  # My money: same period → same net, the « Estimated » tags
  if per == 'date': pg.evaluate("(f)=>{U.mper='custom'; U.mcustom={from:f,to:todayStr()}; saveU()}", d0)
  else: pg.evaluate("(p)=>{U.mper=p; saveU()}", per)
  pg.evaluate("location.hash='#payouts'"); pg.wait_for_selector('.mny-net', timeout=8000); pg.wait_for_timeout(500)
  mn = digits(pg.locator('.mny-net .tot b').inner_text())
  ok(mn.lstrip('+') == shown.lstrip('+'), f'{tag} My money shows the same real net ({mn} / {shown})')
  ok(pg.locator('.mny .rn-est').count() == 5, f'{tag} 5 entries tagged « Estimated » in My money ({pg.locator(".mny .rn-est").count()})')
  print(f'      {tag}: {taps} taps, {secs:.0f} s from the profile to the real net (automated)')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

def case_b(p):
  br, pg, errs = new_trader(p, 'fr', True, profile=True)
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=15000); pg.wait_for_timeout(800)
  add_account(pg, 'topstep', None)
  tap(pg, '[data-rn=start]'); tap(pg, '[data-rn=later]'); pg.wait_for_timeout(900)
  ok(pg.evaluate("(S.settings.realnet||{}).state") == 'later' and pg.locator('.rn.open').count() == 0, 'B « Je le ferai plus tard » closes the window')
  inv = pg.locator('.d-money .rn-inv')
  ok(inv.count() == 1 and 'Ton vrai net en 1 minute' in inv.inner_text(), 'B Today: « Ton vrai net en 1 minute » in My money')
  pg.screenshot(path='/tmp/rn_B_invite.png', full_page=True)
  tap(pg, '.rn-inv [data-rn=open]'); ok(pg.locator('.rn.open [data-rn-per]').count() == 3, 'B the invitation opens the catch-up')
  tap(pg, '[data-rn=later]'); pg.wait_for_timeout(600)
  tap(pg, '.rn-inv [data-rn=hide]'); pg.wait_for_timeout(600)
  pg.reload(); pg.wait_for_timeout(3500)
  ok(pg.locator('.rn-inv').count() == 0 and pg.evaluate("(S.settings.realnet||{}).state") == 'hidden', 'B ✕ hides the invitation for good (after a reload too)')
  ok(not errs, f'B no page error ({errs[:2]})')
  br.close()

def case_c(p):
  br, pg, errs = new_trader(p, 'en', False, profile=True)
  pg.goto(B + '/'); pg.wait_for_timeout(3000)
  pg.evaluate("put('firms',{id:'f-old',name:'Lucid'}); put('accounts',{id:'a-old',firm_id:'f-old',name:'Lucid 50K',starting_balance_c:5000000,status:'active',created_on:'2026-01-05',money_type:'eval',phase:'eval'}); render()")
  pg.wait_for_timeout(1500)
  ok(pg.locator('.rn.open').count() == 0, 'C an account added outside the first visit opens no window')
  inv = pg.locator('.d-money .rn-inv')
  ok(inv.count() == 1 and 'Complete your history in 1 minute' in inv.inner_text(), 'C existing trader: « Complete your history in 1 minute »')
  pg.wait_for_timeout(800)
  ok(pg.evaluate("(S.settings.realnet||{}).shown_on") == pg.evaluate("todayStr()"), 'C the day it was offered is kept')
  pg.evaluate("(()=>{const s=JSON.parse(JSON.stringify(S.settings)); s.realnet={shown_on:'2020-01-01'}; put('settings',s)})()"); pg.wait_for_timeout(1200)
  pg.reload(); pg.wait_for_timeout(3500)
  ok(pg.locator('.rn-inv').count() == 0, 'C the next day: no invitation (offered once)')
  ok(not errs, f'C no page error ({errs[:2]})')
  br.close()

def case_d(p):
  br, pg, errs = new_trader(p, 'fr', False, profile=True)
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=15000); pg.wait_for_timeout(800)
  add_account(pg, 'apex', 'apex-eod')
  ap = pg.evaluate("S.accounts[0].firm_id")
  tap(pg, '[data-rn=start]'); tap(pg, '[data-rn=buys]')
  pg.locator(f'[data-rn-q="{ap}|evaluation"][data-d="1"]').click(); pg.locator(f'[data-rn-q="{ap}|evaluation"][data-d="1"]').click()
  pg.fill(f'[data-rn-p="{ap}|evaluation"]', '100'); tap(pg, '[data-rn=payouts]'); tap(pg, '[data-rn=save]'); tap(pg, '[data-rn=close]')
  pg.evaluate("U.mper='year'; saveU(); location.hash='#payouts'"); pg.wait_for_selector('.mny-net', timeout=8000); pg.wait_for_timeout(600)
  eid = f'est-{ap}-evaluation'
  tap(pg, f'.mny-row[data-id="{eid}"]'); pg.wait_for_selector('form.rn-estf', timeout=4000)
  pg.fill('form.rn-estf [name=amount]', '250'); pg.evaluate("document.querySelector('form.rn-estf').requestSubmit()"); pg.wait_for_timeout(700)
  d = pg.evaluate("(id)=>{const e=getDoc('expenses',id); return e&&[e.amount_c,!!e.estimated]}", eid)
  ok(d == [25000, True], f'D an estimate is edited in its small form, still estimated ({d})')
  # an exact purchase inside the period → the reminder
  tap(pg, '[data-mny=addE]'); pg.wait_for_selector('form.mny-form[data-form=expense]', timeout=4000)
  pg.fill('form[data-form=expense] [name=amount]', '167'); pg.select_option('form[data-form=expense] [name=firm]', ap)
  pg.evaluate("document.querySelector('form[data-form=expense]').requestSubmit()"); pg.wait_for_timeout(600)
  ok(pg.locator('.rn-remind').count() == 1 and 'estimation' in pg.locator('.rn-remind').inner_text(), 'D an exact purchase in the period: « ajuste-la si besoin » reminder')
  n_est = pg.evaluate("S.expenses.filter(e=>e.estimated).length"); n_all = pg.evaluate("S.expenses.length")
  ok(n_est == 1 and n_all == 2, f'D nothing merged automatically ({n_est} estimate, {n_all} expenses)')
  tap(pg, '.rn-remind button'); pg.wait_for_timeout(700)
  ok(pg.locator('form.rn-estf').count() == 1, 'D « Ajuster » opens the estimate')
  csv = pg.evaluate("""async()=>{let b=null; const o=URL.createObjectURL; URL.createObjectURL=(x)=>{b=x; return o.call(URL,x)}; try{SweepMoney.csvYear()}finally{URL.createObjectURL=o} return b?await b.text():''}""")
  ok('estimé' in csv, 'D the yearly CSV marks the estimate « estimé »')
  ok(not errs, f'D no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  combos = [('fr', True, 'year', 'new'), ('en', True, 'month', 'lt1'), ('es', True, 'date', 'gt1'), ('fr', False, 'date', ''), ('en', False, 'year', 'new'), ('es', False, 'month', 'lt1')]
  if os.environ.get('RN_ONLY'): combos = [c for c in combos if f"{c[0]}-{'p' if c[1] else 'c'}" == os.environ['RN_ONLY']] * int(os.environ.get('RN_TIMES', '1'))
  for lang, phone, per, exp in combos:
    print(f"— A. {'phone' if phone else 'computer'} {lang} · {per}")
    case_a(p, lang, phone, per, exp)
  if not os.environ.get('RN_ONLY'):
    print('— B. later, then hidden'); case_b(p)
    print('— C. existing trader'); case_c(p)
    print('— D. estimates in My money'); case_d(p)
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
