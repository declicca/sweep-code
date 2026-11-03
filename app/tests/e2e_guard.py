"""
Sweep — the account guardian on Today (brief « Gardien de compte », 3 Nov., SWEEP.md section 8), Playwright:
  python3 tests/e2e_guard.py http://127.0.0.1:8095
A trader of his own each time: phone 390 (fr, touch, dark), phone 390 (es, light), computer 1300 (en, light), computer 1300 (fr, dark).
 1  an account without firm rules: no guardian card
 2  one account: the card is the first of Today, « Risk left today » with its number (Geist Mono), the room's bar blue, the calm
    sentence, no pills
 3  three accounts: the most at risk first (gold bar, the « danger » sentence), a pill per account; a tap on a pill shows that
    account; « Estimate » on a typed account trailing trade by trade
 4  the sheet (a tap on the card): the floors, the room, the target, what the firm's rules do not say (« Not set in this firm's
    rules »); it closes by sliding down (phone) or with its ×
 5  an account on its floor: the « breached » sentence, $0 left
 6  Free (a server with billing): one account with its numbers, the other pills locked and linked to the plans
 8  the stop rule (two losing trades in a row): the card at « stopped », one calm sheet — full screen on a phone — with the
    day in two numbers and « Close my day » (the review in one tap); not again after a reload; the + still opens the trade form
 7  « Update » (an account without sync): one field, the balance now; saved, the card shows the new risk left in under 5 s,
    and « Close my day » proposes that balance as the platform's; a synced account has no « Update »
No page error, nothing wider than the window, no English in French or Spanish, nothing cut or overlapping in the card.
"""
import json, os, random, sqlite3, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APPDIR = os.path.dirname(os.path.dirname(DB))
P1 = int(B.rsplit(':', 1)[1]) + 2; B1 = f'http://127.0.0.1:{P1}'
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def sql(q, args=()):
  d = sqlite3.connect(DB, timeout=10); c = d.execute(q, args); r = c.fetchall(); d.commit(); d.close(); return r
def unthrottle():
  try: sql('DELETE FROM attempts')
  except Exception: pass
def until(pg, js, ms=20000):   # (a predicate given as text is evaluated: the app's CSP refuses that)
  for _ in range(ms // 250):
    try:
      if pg.evaluate(js): return True
    except Exception: pass
    pg.wait_for_timeout(250)
  return False
UP = {'fr': 'Mettre à jour', 'es': 'Actualizar', 'en': 'Update'}
X = {
  'fr': {'title': 'Gardien de compte', 'risk': 'Risque restant aujourd’hui', 'calm': 'Tu as de la marge. Suis ton plan.', 'danger': 'Encore une perte pourrait coûter ce compte. Protège-le.',
         'breached': 'Ce compte a dépassé sa limite. Ton historique reste en sécurité dans Sweep.', 'est': 'Estimation', 'miss': 'Non défini dans les règles de cette firme', 'dd': 'Plancher de drawdown', 'day': 'Plancher du jour'},
  'es': {'title': 'Guardián de cuenta', 'risk': 'Riesgo restante hoy', 'calm': 'Tienes margen. Sigue tu plan.', 'danger': 'Una pérdida más podría costarte esta cuenta. Protégela.',
         'breached': 'Esta cuenta superó su límite. Tu historial sigue a salvo en Sweep.', 'est': 'Estimación', 'miss': 'No definido en las reglas de esta firma', 'dd': 'Piso de drawdown', 'day': 'Piso del día'},
  'en': {'title': 'Account guardian', 'risk': 'Risk left today', 'calm': 'You have room. Trade your plan.', 'danger': 'One more loss could cost this account. Protect it.',
         'breached': 'This account crossed its limit. Your history stays safe in Sweep.', 'est': 'Estimate', 'miss': 'Not set in this firm’s rules', 'dd': 'Drawdown floor', 'day': 'Daily floor'},
}
EN = ['Account guardian', 'Risk left today', 'You have room', 'Estimate', 'Not set in', 'Drawdown floor', 'Daily floor', 'Balance now', 'Profit target', 'Trading days', 'Room', 'Planned risk', 'Today']
CARD = """(() => { const c = document.querySelector('#main .nav-guard'); if (!c) return null; const r = c.getBoundingClientRect(), col = c.parentElement, n = c.querySelector('.nav-guard-n'), bar = c.querySelector('.nav-guard-bar > i');
  const kids = [...c.querySelectorAll('.nav-guard-h > *, .nav-guard-v > *, .nav-guard-pill')].filter((e) => e.getClientRects().length);
  const cut = kids.filter((e) => e.scrollWidth > e.clientWidth + 1 && !e.matches('.nav-guard-acc')).map((e) => e.textContent.trim());
  const first = [...col.children].filter((e) => e.getClientRects().length).sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0] === c;
  return { text: c.innerText.replace(/\\s+/g, ' ').trim(), visible: r.height > 40 && r.width > 200, first, top: Math.round(r.top),
    num: n ? n.textContent : '', mono: n ? getComputedStyle(n).fontFamily : '', bar: bar ? getComputedStyle(bar).backgroundColor : '', msg: (c.querySelector('.nav-guard-msg') || {}).textContent || '',
    pills: [...c.querySelectorAll('.nav-guard-pill')].map((p) => [p.textContent.trim(), p.classList.contains('on'), p.classList.contains('is-locked'), p.getAttribute('href') || '']),
    est: !!c.querySelector('.nav-guard-est'), cut, wide: c.scrollWidth - c.clientWidth } })()"""
WIDE = "document.documentElement.scrollWidth - innerWidth"
BLUE, GOLD = ('rgb(76, 141, 255)', ('rgb(212, 162, 76)', 'rgb(132, 92, 14)'))   # (the gold of the light theme is deeper, for contrast)
def acc(i, name, start, rules, phase='eval', extra=None):
  return dict({'id': i, 'name': name, 'status': 'active', 'phase': phase, 'starting_balance_c': start, 'rules': rules}, **(extra or {}))
def trades(pg, rows):
  pg.evaluate("""async (rows) => { const d = todayStr(), y = (n) => { const x = new Date(d + 'T12:00:00'); do x.setDate(x.getDate() - 1); while (--n > 0 || x.getDay() === 0 || x.getDay() === 6); return x.toISOString().slice(0, 10); };
    rows.forEach(([id, a, back, p, tm]) => put('trades', { id, account_id: a, date: back ? y(back) : d, entry_time: tm || '10:00', exit_time: tm || '10:04', instrument: 'NQ', contracts: 1, direction: 'long', pnl_c: p, fees_c: 0 }));
    await Promise.all(Object.values(chains)); }""", rows)
def fresh(pg, wait=True):
  pg.evaluate("SweepGuard.load(true)"); pg.wait_for_timeout(1200)
def signup(ctx, base, pre):
  unthrottle()
  email = '%s%06d@t.dev' % (pre, random.randint(0, 999999))
  r = ctx.request.post(base + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(base + '/api/me/profile', data=json.dumps({'first_name': 'Noa', 'experience': 'gt1'}), headers=H)
  return email
def context(br, lang, w, phone, theme):
  ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'es': 'es-ES', 'en': 'en-US'}[lang], color_scheme=theme,
                       timezone_id='America/New_York', device_scale_factor=2 if phone else 1)
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  return ctx

with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone, theme in (('fr', 390, True, 'dark'), ('es', 390, True, 'light'), ('en', 1300, False, 'light'), ('fr', 1300, False, 'dark')):
    tag = f'{w}-{lang}-{theme}'; x = X[lang]
    ctx = context(br, lang, w, phone, theme); signup(ctx, B, 'gd')
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, "typeof put === 'function' && !!window.SweepGuard")
    # 1. an account without rules
    pg.evaluate("put('accounts', { id: 'g0', name: 'Perso', status: 'active', phase: 'eval', starting_balance_c: 1000000, rules: {} }); render()")
    pg.wait_for_timeout(800); fresh(pg)
    ok(pg.evaluate("!document.querySelector('#main .nav-guard')") and pg.evaluate("!!document.querySelector('#main .nav-dash')"), f'{tag} 1 an account without firm rules: no guardian card')
    # 2. one account, calm
    pg.evaluate("put('accounts', %s)" % json.dumps(acc('g1', 'Topstep 50K', 5000000, {'dd_c': 200000, 'dd_type': 'eod', 'target_c': 300000})))
    trades(pg, [['a1', 'g1', 1, 30000], ['a2', 'g1', 0, -20000, '09:40']]); fresh(pg)
    c = pg.evaluate(CARD)
    ok(c and c['visible'] and c['first'] and x['title'] in c['text'] and x['risk'] in c['text'] and 'Geist Mono' in c['mono'] and c['bar'] == BLUE and c['msg'] == x['calm'] and not c['pills'],
       f'{tag} 2 one account: first card, « {x["risk"]} » {c and c["num"]}, Geist Mono, blue bar, calm sentence, no pills ({c and [c["first"], c["bar"], c["msg"], c["pills"]]})')
    ok(c and c['num'].replace(' ', ' ').replace(' ', ' ').strip() in ('$1,800', '1 800 $', '1.800 $'), f'{tag} 2 risk left = the room: $2,000 − $200 = $1,800 ({c and c["num"]!r})')
    if SHOTS and phone and lang == 'fr': pg.screenshot(path=f'{SHOTS}/guard-1-{tag}.png')
    # 3. three accounts, the most at risk first
    pg.evaluate("put('accounts', %s); put('accounts', %s)" % (json.dumps(acc('g2', 'Apex 100K', 10000000, {'dd_c': 300000, 'dd_type': 'trade'}, 'funded')),
                                                             json.dumps(acc('g3', 'Lucid 25K', 2500000, {'dd_c': 100000, 'dd_type': 'static', 'dll_c': 200000}))))
    trades(pg, [['b1', 'g3', 0, -80000, '09:50'], ['b2', 'g2', 0, 15000, '09:55']]); fresh(pg)
    c = pg.evaluate(CARD)
    ok(c and c['bar'] in GOLD and c['msg'] == x['danger'] and [q[0] for q in c['pills']][:1] == ['Lucid 25K'] and c['pills'][0][1] and len(c['pills']) == 3,
       f'{tag} 3 three accounts: Lucid first (danger, gold), three pills ({c and [c["msg"], c["bar"], c["pills"]]})')
    pg.locator('#main .nav-guard [data-guard-pick="g2"]').click(); pg.wait_for_timeout(500)
    c = pg.evaluate(CARD)
    ok(c and 'Apex 100K' in c['text'] and c['est'] and x['est'] in c['text'] and [q[0] for q in c['pills'] if q[1]] == ['Apex 100K'] and pg.locator('#main .nav-guard .nav-guard-est').is_visible(),
       f'{tag} 3 a tap on « Apex 100K »: that account, « {x["est"]} » (trailing trade by trade, typed) ({c and c["text"][:90]})')
    ok(c and not c['cut'] and c['wide'] <= 0 and pg.evaluate(WIDE) <= 0, f'{tag} 3 nothing cut in the card, nothing wider than the window ({c and c["cut"]})')
    if SHOTS: pg.screenshot(path=f'{SHOTS}/guard-3-{tag}.png')
    # 4. the sheet
    pg.locator('#main .nav-guard [data-guard-pick="g3"]').click(); pg.wait_for_timeout(400)
    pg.locator('#main .nav-guard [data-guard-open]').click(); pg.wait_for_timeout(800)
    sh = pg.evaluate("(() => { const s = document.querySelector('#gSheet.nav-guard-sheet.open'); return s ? s.innerText.replace(/\\s+/g, ' ') : '' })()")
    ok(x['dd'] in sh and x['day'] in sh and x['miss'] in sh and pg.locator('#gSheet .nav-guard-rows').first.is_visible(), f'{tag} 4 the sheet: both floors and « {x["miss"]} » ({sh[:120]})')
    if lang != 'en': ok(not [e for e in EN if e in sh or e in (c or {}).get('text', '')] , f'{tag} no English in {lang} ({[e for e in EN if e in sh]})')
    ok(pg.evaluate("(() => { const s = document.querySelector('#gSheet'); return s && s.scrollWidth <= s.clientWidth + 1 })()"), f'{tag} 4 the sheet: nothing wider')
    if SHOTS: pg.screenshot(path=f'{SHOTS}/guard-4-{tag}.png')
    if phone:   # a finger on the sheet's grabber, slid down (touch events, as the phone sends them)
      bx = pg.locator('#gSheet').bounding_box(); y0 = bx['y'] + 12; cdp = ctx.new_cdp_session(pg)
      cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 195, 'y': y0}]})
      for k in range(1, 13): cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 195, 'y': y0 + k * 30}]}); pg.wait_for_timeout(16)
      cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(800)
    else: pg.locator('#gSheet [data-g="close"]').click(); pg.wait_for_timeout(600)
    ok(pg.evaluate("!document.querySelector('#gSheet.open')"), f'{tag} 4 the sheet closes ({"slid down" if phone else "×"})')
    # 5. an account on its floor
    trades(pg, [['c1', 'g3', 0, -60000, '10:30']]); fresh(pg)
    pg.locator('#main .nav-guard [data-guard-pick="g3"]').click(); pg.wait_for_timeout(400)
    c = pg.evaluate(CARD)
    ok(c and c['msg'] == x['breached'] and c['num'].replace(' ', ' ').strip() in ('$0', '0 $'), f'{tag} 5 on its floor: « {x["breached"][:30]}… », $0 left ({c and [c["msg"], c["num"]]})')
    # 7. « Update »: Topstep 50K (typed) — its balance is $50,100; typed $49,700 → today −$600, room $2,000 − 600 = $1,400... from the start of the day
    pg.locator('#main .nav-guard [data-guard-pick="g1"]').click(); pg.wait_for_timeout(400)
    upb = pg.locator('#main .nav-guard [data-guard-up="g1"]')
    ok(upb.is_visible() and upb.inner_text().strip() == UP[lang], f'{tag} 7 « {UP[lang]} » on a typed account')
    t0 = time.time(); upb.click(); pg.wait_for_selector('#gSheet.open [data-guard-bal]', timeout=4000)
    inputs = pg.evaluate("document.querySelectorAll('#gSheet.open input').length")
    pg.fill('#gSheet [data-guard-bal]', {'fr': '49 700,00', 'es': '49.700,00', 'en': '49,700.00'}[lang])
    pg.locator('#gSheet [data-guard-save]').click()
    until(pg, r"""(() => { const n = document.querySelector('#main .nav-guard[data-guard="g1"] .nav-guard-n'); return !!n && /1[\s\u202f\u00a0.,]?400/.test(n.textContent) })()""", 5000)
    dt = time.time() - t0
    c = pg.evaluate(CARD)
    ok(inputs == 1 and dt < 5 and c and 'Topstep 50K' in c['text'], f'{tag} 7 one field, saved: the card shows $1,400 left in {dt:.1f} s ({c and c["num"]!r})')
    pg.wait_for_timeout(1500); st = pg.evaluate("SweepGuard.state()"); g1 = [a for a in st['accounts'] if a['id'] == 'g1'][0]
    ok(g1['balance_c'] == 4970000 and g1['pnl_c'] == -60000 and g1['typed'], f'{tag} 7 the server: balance $49,700, today −$600, a typed balance ({g1["balance_c"]}, {g1["pnl_c"]})')
    if SHOTS and phone: pg.screenshot(path=f'{SHOTS}/guard-7-{tag}.png')
    pg.evaluate("SweepGame.openReview()"); pg.wait_for_timeout(1200)
    bal = pg.evaluate("""(() => { const i = document.querySelector('#gSheet.open [data-bal-in="g1"]'); return i ? i.value : null })()""")
    ok(bal is not None and bal.replace('\u202f', ' ').replace('\u00a0', ' ') in ('49 700,00', '49.700,00', '49,700.00'), f'{tag} 7 « Close my day » proposes the typed balance ({bal!r})')
    pg.evaluate("SweepGame.ui.close(true)"); pg.wait_for_timeout(400)
    # a synced account: no « Update »
    ctx.request.get(B + '/api/sync', headers=H)
    uid = pg.evaluate("S.uid")
    sql("INSERT OR REPLACE INTO sync_accounts (id, user_id, platform, ext_id, info, account_id, state, created_at, updated_at) VALUES (?, ?, 'ninjatrader', ?, '{}', 'g2', 'linked', 1, 1)", ('sa' + uid[:20], uid, 'ext' + uid[:20]))
    fresh(pg); pg.locator('#main .nav-guard [data-guard-pick="g2"]').click(); pg.wait_for_timeout(400)
    ok(pg.locator('#main .nav-guard[data-guard="g2"]').count() == 1 and pg.locator('#main .nav-guard [data-guard-up]').count() == 0 and not pg.evaluate(CARD)['est'],
       f'{tag} 7 a synced account: no « {UP[lang]} », not an estimate')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()

  # 8. the stop rule
  ST = {'fr': ('Séance terminée. C’est ça, la discipline.', 'Fermer ma journée', 'Tu as atteint ta règle d’arrêt.'), 'en': ('Session done. That’s discipline.', 'Close my day', 'You hit your stop rule.'),
        'es': ('Sesión terminada. Eso es disciplina.', 'Cerrar mi día', 'Alcanzaste tu regla de stop.')}
  for lang, w, phone, theme in (('fr', 390, True, 'dark'), ('en', 1300, False, 'light'), ('es', 390, True, 'light')):
    tag = f'stop-{w}-{lang}-{theme}'; s = ST[lang]
    ctx = context(br, lang, w, phone, theme); signup(ctx, B, 'gs')
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, "typeof put === 'function' && !!window.SweepGuard")
    pg.evaluate("editDoc('settings', 'settings', (s) => { s.day_lock = { stop: true }; })")   # his stop rule turned on (2 losses in a row by default)
    pg.evaluate("put('accounts', %s)" % json.dumps(acc('s1', 'Apex 50K', 5000000, {'dd_c': 250000, 'dd_type': 'eod', 'dll_c': 100000})))
    trades(pg, [['s1a', 's1', 0, -12000, '09:40']]); fresh(pg)
    ok(pg.evaluate("!document.querySelector('#gSheet.nav-guard-stop')") and pg.evaluate(CARD)['msg'] != s[0], f'{tag} one loss: no stop')
    trades(pg, [['s1b', 's1', 0, -9000, '09:52']]); pg.wait_for_timeout(1500); fresh(pg); pg.wait_for_timeout(800)
    sh = pg.evaluate(r"""(() => { const e = document.querySelector('#gSheet.open.nav-guard-stop'); if (!e) return null; const r = e.getBoundingClientRect();
      return { text: e.innerText.replace(/\s+/g, ' '), h: Math.round(r.height), top: Math.round(r.top), btn: [...e.querySelectorAll('.btn.primary')].map((b) => b.textContent.trim()), nums: [...e.querySelectorAll('.nav-guard-stopn b')].map((b) => b.textContent) } })()""")
    ok(sh and s[0] in sh['text'] and s[2] in sh['text'] and sh['btn'] == [s[1]] and len(sh['nums']) == 2 and sh['nums'][1] == '2', f'{tag} two losses in a row: the stop sheet, the day in two numbers, « {s[1]} » ({sh and [sh["nums"], sh["btn"]]})')
    ok(sh and (not phone or (sh['h'] >= 840 and sh['top'] <= 2)), f'{tag} full screen on a phone ({sh and [sh["h"], sh["top"]]})')
    ok(sh and not any(k in sh['text'].lower() for k in ('block', 'bloqu')), f'{tag} never says Sweep blocks orders')
    if SHOTS: pg.screenshot(path=f'{SHOTS}/guard-8-{tag}.png')
    pg.locator('#gSheet [data-guard-close]').click(); pg.wait_for_timeout(1200)
    ok(pg.evaluate("!!document.querySelector('#gSheet.open.g-rv')"), f'{tag} « {s[1]} »: the day\'s review opens (one tap)')
    pg.evaluate("SweepGame.ui.close(true)"); pg.wait_for_timeout(300)
    c = pg.evaluate(CARD)
    ok(c and c['msg'] == s[0] and c['bar'] in GOLD, f'{tag} the card at « stopped » ({c and c["msg"]})')
    pg.reload(); until(pg, "!!window.SweepGuard && !!SweepGuard.state()"); pg.wait_for_timeout(2500)
    ok(pg.evaluate("!document.querySelector('#gSheet.nav-guard-stop')"), f'{tag} after a reload: the sheet does not come back (once a day)')
    pg.evaluate("openTicket()"); pg.wait_for_timeout(900)
    ok(pg.evaluate("!!document.querySelector('.ticket.on, #ticket.on, .tk-sheet.open, .nav-am.open, [data-am]')"), f'{tag} the + still opens the trade form (Sweep advises, never blocks)')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()

  # 6. Free: a server with billing (the trial ended)
  env = dict(os.environ, SWEEP_BILLING_CONFIG=APPDIR + '/tools/billing-config.local.php', PHP_CLI_SERVER_WORKERS='4')
  pr = subprocess.Popen(['php', '-S', f'127.0.0.1:{P1}', 'router.php'], cwd=APPDIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
  try:
    for _ in range(50):
      try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=2); break
      except Exception: time.sleep(0.2)
    for lang, w, phone, theme in (('fr', 390, True, 'light'), ('en', 1300, False, 'dark')):
      tag = f'free-{w}-{lang}'
      ctx = context(br, lang, w, phone, theme); email = signup(ctx, B1, 'gf')
      uid = sql('SELECT id FROM users WHERE email_lc = ?', (email.lower(),))[0][0]
      ctx.request.get(B1 + '/api/billing/me', headers=H)
      sql("UPDATE billing_grants SET ends_at = ? WHERE uid = ? AND reason IN ('trial', 'early_access')", (int(time.time()) - 86400, uid))
      pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.goto(B1 + '/#dashboard'); until(pg, "typeof put === 'function' && !!window.SweepGuard")
      pg.evaluate("put('accounts', %s); put('accounts', %s)" % (json.dumps(acc('f1', 'Apex 50K', 5000000, {'dd_c': 250000, 'dd_type': 'eod'})), json.dumps(acc('f2', 'Topstep 50K', 5000000, {'dd_c': 200000, 'dd_type': 'static'}))))
      trades(pg, [['f1t', 'f2', 0, -150000, '09:45']])
      until(pg, "typeof BILL !== 'undefined' && BILL.on && BILL.st && BILL.st.plan === 'free'", 15000)
      for _ in range(3):
        if not pg.locator('.sb-layer').count(): break
        pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
      pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(800); fresh(pg)
      st = pg.evaluate("SweepGuard.state()"); c = pg.evaluate(CARD)
      ok(st and st['all'] is False and 'room_c' in st['accounts'][0] and st['accounts'][1].get('locked') and 'room_c' not in st['accounts'][1], f'{tag} 6 Free: the server sends one account\'s numbers ({st and [a.get("name") for a in st["accounts"]]})')
      ok(c and 'Topstep 50K' in c['text'] and c['pills'] and c['pills'][1][2] and c['pills'][1][3] == '#plan' and pg.locator('#main .nav-guard .nav-guard-pill.is-locked').is_visible(),
         f'{tag} 6 Free: the most at risk shown, the other pill locked and linked to the plans ({c and c["pills"]})')
      if SHOTS: pg.screenshot(path=f'{SHOTS}/guard-6-{tag}.png')
      ok(not errs, f'{tag} no page error ({errs[:2]})')
      ctx.close()
  finally:
    os.killpg(pr.pid, 15)
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
