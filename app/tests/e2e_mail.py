"""
Sweep — Admin › Emails (our own campaigns, 3 Nov.), dev environment with Playwright:
  python3 tests/e2e_mail.py http://127.0.0.1:8095 /tmp/show_state.json      (SWEEP_TEST_DB: the dev server's SQLite file)
Three traders of its own (FR, EN, an address that refuses). As the administrator (fr-CA, computer 1300×850 and phone 390×844,
light and dark):
 - the menu has « Courriels »; #mail: the 30-day numbers, the list, the sending pace, the campaigns; a trader gets 403;
 - a draft: name, FR / EN tabs, the toolbar (« Prénom » adds {first}), the preview drawn in its own shadow root, the audience
   count; saved on its own; « M'envoyer un test » goes to the administrator's address;
 - « Envoyer maintenant » asks in the app's own window, then mail/send-cron.php sends: each trader in their language, with the
   one-click unsubscribe headers; the refusing address is set aside;
 - the open image, a signed tracked link (a tampered one goes home), the one-click unsubscribe (no CSRF header), a bounce
   report piped to mail/bounce.php (silent, exit 0);
 - the campaign's numbers page: delivered, opened, clicked, the 48 hours, the links; no horizontal scroll, no page error;
 - the automations (step 5): the 18 in the list with what sends each; one opened: its text, switched off and on, edited and
   saved on its own, a test; never sent by hand nor deleted.
"""
import json, os, random, re, sqlite3, subprocess, sys, time, base64
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').rstrip('/')
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
DEST = os.path.dirname(os.path.dirname(DB)); SENT = os.path.join(DEST, 'data', 'mail-sent.jsonl')
SHOTS = os.environ.get('TMPDIR', '/tmp').rstrip('/')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def sql(q, a=()):
  d = sqlite3.connect(DB); r = d.execute(q, a).fetchall(); d.commit(); d.close(); return r
def unthrottle():
  try: sql('DELETE FROM attempts')
  except Exception: pass
def sent_lines():
  try: return [json.loads(l) for l in open(SENT, encoding='utf-8') if l.strip()]
  except OSError: return []
def cron():
  env = dict(os.environ, SWEEP_TEST_DB=DB)
  return subprocess.run(['php', os.path.join(DEST, 'mail', 'send-cron.php')], capture_output=True, text=True, env=env, cwd=DEST)
tag = '%06d' % random.randint(0, 999999)

def trader(p, first, lang, email=None):
  unthrottle()
  ctx = p.request.new_context(base_url=B)
  email = email or 'ml%s%s@t.dev' % (first.lower(), tag)
  r = ctx.post('/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000, 'lang': lang}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  ctx.post('/api/me/profile', data=json.dumps({'first_name': first, 'last_name': 'Mail', 'experience': 'gt1'}), headers=H)
  return ctx, email

with sync_playwright() as p:
  a, ea = trader(p, 'Amelie', 'fr'); b, eb = trader(p, 'Bob', 'en'); c, ec = trader(p, 'Carl', 'en', 'bounce-hard%s@t.dev' % tag)
  ok(a.get('/api/admin/mail', headers=H).status == 403, 'api/admin/mail: administrators only (403 for a trader)')
  adm = p.request.new_context(base_url=B, storage_state=STATE)
  had = sql("SELECT email FROM users WHERE username = 'mateo'")[0][0]
  if not had: sql("UPDATE users SET email = ?, email_lc = ? WHERE username = 'mateo'", ('mateo-ml%s@t.dev' % tag, 'mateo-ml%s@t.dev' % tag))
  try:
    content = {'en': {'subject': 'News for {first} ' + tag, 'preheader': 'Two minutes', 'body': "# What is new\n\nHello {first}, read the [guide](https://makeitsweep.com/guide).\n\n[[Open Sweep|https://app.makeitsweep.com/#dashboard]]"},
               'fr': {'subject': 'Du nouveau, {first} ' + tag, 'preheader': '', 'body': 'Qu\'est-ce qui te manque le plus ?\n\n[[?choix|Les stats|La synchro]]\n\nSalut {first}, voici le [guide](https://makeitsweep.com/guide).'}, 'es': {'subject': '', 'preheader': '', 'body': ''}}
    cid = adm.post('/api/admin/mail/campaigns', data=json.dumps({'name': 'Test ' + tag, 'content': content, 'audience': {'joined': 1}}), headers=H).json()['id']
    pv = adm.post('/api/admin/mail/preview', data=json.dumps({'content': content, 'lang': 'fr'}), headers=H).json()
    ok(pv['subject'].startswith('Du nouveau, ') and 'api/m/' not in pv['html'] and 'Me désinscrire' in pv['html'], 'preview: the French version, nothing tracked (%s)' % pv['subject'][:40])
    n0 = len(sent_lines())
    tr = adm.post('/api/admin/mail/test', data=json.dumps({'content': content, 'lang': 'en'}), headers=H)
    last = sent_lines()[-1] if len(sent_lines()) > n0 else {}
    me = sql("SELECT email FROM users WHERE username = 'mateo'")[0][0]
    ok(tr.status == 200 and last.get('subject', '').startswith('[Test] News for') and last.get('to') == me, 'test: to the administrator, at once (%s)' % last.get('to'))

    br = p.chromium.launch()
    shots = []
    for w, hgt, mob, scheme in ((1300, 850, False, 'dark'), (390, 844, True, 'light'), (390, 844, True, 'dark'), (1300, 850, False, 'light')):
      t = f'{w}px {scheme}'
      ctx = br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': hgt}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, color_scheme=scheme)
      ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      pg.goto(B + '/#dashboard'); pg.wait_for_timeout(800)
      pg.click('.who'); pg.wait_for_selector('#navMenu [data-navm="mail"]', timeout=8000)
      ok(pg.inner_text('#navMenu [data-navm="mail"]').strip() == 'Courriels', f'{t} the menu: « Courriels » under Traders')
      pg.click('#navMenu [data-navm="mail"]'); pg.wait_for_selector('#main .ml-kpis', timeout=15000); pg.wait_for_timeout(500)
      ok(pg.inner_text('#title').strip() == 'Courriels' and pg.locator('#main .ml h2').count() == 0 and pg.locator('#main .ml-kpis .ux-m').count() == 5, f'{t} #mail: the title « Courriels » once, the 5 numbers of the last 30 days')
      row = pg.locator(f'#main .ml-list a[href="#mail/{cid}"]')
      ok(row.count() == 1 and 'Brouillon' in row.inner_text(), f'{t} the draft in the list, « Brouillon »')
      ok('peuvent recevoir les campagnes' in pg.inner_text('#main .ml-two') and 'cette heure' in pg.inner_text('#main .ml-two'), f'{t} the list and the sending pace')
      ov = pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
      ok(ov <= 0, f'{t} #mail: no horizontal scroll ({ov})')
      pg.screenshot(path=f'{SHOTS}/e2e_mail_list_{w}_{scheme}.png', full_page=True); shots.append(f'list {w} {scheme}')
      row.click(); pg.wait_for_selector('#main .ml-ed textarea', timeout=15000); pg.wait_for_timeout(700)
      ok(pg.inner_text('.top-back').strip() == 'Courriels' and pg.get_attribute('.top-back', 'href') == '#mail', f'{t} a campaign: « ‹ Courriels » as the way back')
      ok(pg.input_value('#main [data-mlf="name"]') == 'Test ' + tag and pg.locator('#main .ml-tabs .chip').count() == 3, f'{t} the editor: name, 3 language tabs')
      pg.click('#main .ml-tabs [data-v="fr"]'); pg.wait_for_timeout(500)
      ok(pg.input_value('#main [data-mlf="subject"]').startswith('Du nouveau'), f'{t} FR tab: the French subject')
      if w == 1300 and scheme == 'dark':   # once: type, the toolbar, saved on its own
        pg.fill('#main [data-mlf="subject"]', 'Du nouveau, {first} ? ' + tag)
        pg.click('#main textarea[data-mlf="body"]'); pg.keyboard.press('End'); pg.keyboard.type(' ')
        pg.click('#main .ml-tools [data-v="first"]'); pg.wait_for_timeout(1400)
        ok(pg.input_value('#main textarea[data-mlf="body"]').endswith('{first}'), f'{t} toolbar « Prénom »: {{first}} at the cursor')
        saved = adm.get(f'/api/admin/mail/campaigns/{cid}', headers=H).json()['campaign']['content']['fr']
        ok(saved['body'].endswith('{first}') and saved['subject'].startswith('Du nouveau, {first} ?'), f'{t} saved on its own')
      pg.wait_for_function("(()=>{const r=document.querySelector('#main [data-ml-prev]'); return r && r.shadowRoot && r.shadowRoot.textContent.includes('Du nouveau')})()", timeout=10000)
      ok(True, f'{t} the preview: the email in its own shadow root')
      cnt = pg.inner_text('#main [data-ml-count]')
      ok(re.search(r'Rejoint \d+ traders', cnt) is not None, f'{t} the audience count ({cnt.strip()[:60]})')
      ov = pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
      ok(ov <= 0, f'{t} editor: no horizontal scroll ({ov})')
      pg.screenshot(path=f'{SHOTS}/e2e_mail_editor_{w}_{scheme}.png', full_page=True)
      ok(not errs, f'{t} no page error {errs[:2]}')
      ctx.close()

    # send now, from the page (phone): the app's own window asks first
    ctx = br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + f'/#mail/{cid}'); pg.wait_for_selector('#main .ml-ed [data-ml="now"]', timeout=15000); pg.wait_for_timeout(600)
    pg.click('#main [data-ml="now"]'); pg.wait_for_selector('.nav-dlg [data-ask="1"]', timeout=8000)
    ok('Envoyer « Test ' + tag in pg.inner_text('.nav-dlg'), 'send now: the app asks first (« Envoyer « … » à N traders ? »)')
    pg.click('.nav-dlg [data-ask="1"]'); pg.wait_for_timeout(1500)
    st = adm.get(f'/api/admin/mail/campaigns/{cid}', headers=H).json()['campaign']['status']
    ok(st == 'scheduled', f'confirmed: scheduled for now ({st})')

    # the sender: only this campaign's three lines are sent here (the dev database has many test traders)
    n0 = len(sent_lines())
    r = cron()
    mine = (ea, eb, ec)
    sql("UPDATE mail_queue SET state = 'skipped' WHERE campaign_id = ? AND state = 'queued' AND email NOT IN (?, ?, ?)", (cid, *mine))
    for _ in range(4):
      if not sql("SELECT COUNT(*) FROM mail_queue WHERE campaign_id = ? AND state = 'queued'", (cid,))[0][0]: break
      cron()
    got = {m['to']: m for m in sent_lines()[n0:]}
    ok(r.returncode == 0 and ea in got and eb in got, f'mail/send-cron.php: sent ({r.stderr[:120]})')
    ok(got.get(ea, {}).get('subject', '') == 'Du nouveau, Amelie ? ' + tag and got.get(eb, {}).get('subject', '') == 'News for Bob ' + tag, 'each trader in their language, with their first name')
    hd = got.get(eb, {}).get('headers', {})
    ok(hd.get('List-Unsubscribe-Post') == 'List-Unsubscribe=One-Click' and '/api/m/u/' in hd.get('List-Unsubscribe', ''), 'one-click unsubscribe headers')
    cst = sql("SELECT state FROM mail_queue WHERE campaign_id = ? AND email = ?", (cid, ec))[0][0]   # skipped when its welcome email (an automation, sent first) already bounced
    ok(cst in ('failed', 'skipped') and sql('SELECT reason FROM mail_suppress WHERE email_lc = ?', (ec,))[0][0] == 'hard', f'the refusing address: set aside ({cst})')
    ok(sql('SELECT status FROM mail_campaigns WHERE id = ?', (cid,))[0][0] == 'sent', 'nothing left: the campaign is « sent »')
    ok(any(t[0] == 'mail' for t in sql('SELECT task FROM cron_runs')), 'Admin › Health: the « mail » task recorded its run')

    # opens, clicks, unsubscribe, bounce
    tka, tkb = got[ea]['token'], got[eb]['token']
    pub = p.request.new_context(base_url=B)
    time.sleep(1)
    o1 = pub.get(f'/api/m/o/{tka}', headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15'})
    o2 = pub.get(f'/api/m/o/{tkb}', headers={'User-Agent': 'Mozilla/5.0'})
    ok(o1.status == 200 and o1.headers.get('content-type') == 'image/gif', 'the open image (a gif, never an error)')
    link = re.search(r'href="([^"]*/api/m/c/' + tka + r'[^"]*)"', got[ea]['html']).group(1).replace('&amp;', '&')
    path = urlparse(link).path + '?' + urlparse(link).query
    c1 = pub.get(path, max_redirects=0)
    ok(c1.status == 302 and c1.headers.get('location') == 'https://makeitsweep.com/guide', 'a tracked link: counted, then the real page')
    c2 = pub.get(path.replace('&s=', '&s=0'), max_redirects=0)
    ok(c2.status == 302 and 'makeitsweep.com/guide' not in c2.headers.get('location', '') and '127.0.0.1' in c2.headers.get('location', ''), 'a tampered link: home, not an open redirect')
    u = pub.post(f'/api/m/u/{tkb}', form={'List-Unsubscribe': 'One-Click'})
    ok(u.status == 200 and 'Subscribe again' in u.text(), 'one-click unsubscribe from the mail app: no session, no CSRF header (English page)')
    ok(sql("SELECT marketing FROM email_prefs WHERE user_id = (SELECT id FROM users WHERE email_lc = ?)", (eb,))[0][0] == 0, 'unsubscribed: off the list')
    rep = "Subject: Undelivered Mail Returned to Sender\nAction: failed\nStatus: 4.2.2\nDiagnostic-Code: smtp; 452 mailbox full\n\nX-Sweep-Id: " + tka + "\n"
    bp = subprocess.run(['php', os.path.join(DEST, 'mail', 'bounce.php')], input=rep, capture_output=True, text=True, env=dict(os.environ, SWEEP_TEST_DB=DB), cwd=DEST)
    ok(bp.returncode == 0 and bp.stdout == '' and sql("SELECT COUNT(*) FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE q.token = ? AND e.type = 'soft_bounce'", (tka,))[0][0] == 1, 'mail/bounce.php: the report recorded, silent, exit 0')
    rp = adm.get(f'/api/admin/mail/campaigns/{cid}', headers=H).json(); s = rp['stats']
    # a one-click answer (feedback brief, step 1): the page records it by its script, a comment is added; a scanner (no script) answers nothing
    al = [x.replace('&amp;', '&') for x in re.findall(r'href="([^"]*/api/m/r/' + tka + r'[^"]*)"', got[ea]['html'])]
    ok(len(al) == 2 and 'a=La%20synchro' in al[1], f'the email: one signed answer link per option ({len(al)})')
    apath = urlparse(al[1]).path + '?' + urlparse(al[1]).query
    pub.get(apath)
    try: n_fb = sql('SELECT COUNT(*) FROM feedback WHERE src_queue = (SELECT id FROM mail_queue WHERE token = ?)', (tka,))[0][0]
    except sqlite3.OperationalError: n_fb = 0   # (a fresh copy: no feedback table before the first one)
    ok(n_fb == 0, 'a link scanner (no script) opening the answer: nothing recorded')
    ok(pub.get(apath.replace('&s=', '&s=0')).status == 404, 'an answer link changed by hand: refused (404)')
    for w, hgt, mob, scheme in ((390, 844, True, 'light'), (1300, 850, False, 'dark')):
      cx = br.new_context(locale='fr-CA', viewport={'width': w, 'height': hgt}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, color_scheme=scheme)
      q = cx.new_page(); er = []; q.on('pageerror', lambda e: er.append(str(e)[:150])); q.on('console', lambda m: er.append(m.text[:150]) if m.type == 'error' else None)
      q.goto(B + apath); q.wait_for_selector('textarea#more'); q.wait_for_timeout(900)
      txt = q.inner_text('main'); bg = q.evaluate('getComputedStyle(document.body).backgroundColor')
      ok('Merci' in txt and 'La synchro' in txt and 'Tu veux en dire plus' in txt and (bg == 'rgb(8, 8, 10)') == (scheme == 'dark'), f'{w}px {scheme} the answer page: « Merci », the answer, the comment box, the device\'s theme ({bg})')
      r = sql('SELECT answer, answer_i, type, question FROM feedback WHERE src_queue = (SELECT id FROM mail_queue WHERE token = ?)', (tka,))
      ok(len(r) == 1 and r[0][0] == 'La synchro' and r[0][1] == 1 and r[0][2] == 'answer' and r[0][3].startswith('Qu'), f'{w}px {scheme} recorded on its own by the page: one line ({r})')
      ov = q.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
      ok(ov <= 0 and not er, f'{w}px {scheme} the answer page: no horizontal scroll ({ov}), no error {er[:2]}')
      if w == 390:
        q.fill('textarea#more', 'Tradovate ' + tag); q.click('button[type=submit]'); q.wait_for_selector('h1')
        ok('C’est noté' in q.inner_text('main') and sql('SELECT message FROM feedback WHERE src_queue = (SELECT id FROM mail_queue WHERE token = ?)', (tka,))[0][0] == 'Tradovate ' + tag, f'{w}px the comment: « C’est noté », kept with the answer')
      q.screenshot(path=f'{SHOTS}/e2e_mail_answer_{w}_{scheme}.png', full_page=True)
      cx.close()
    ok(sql('SELECT message FROM feedback WHERE src_queue = (SELECT id FROM mail_queue WHERE token = ?)', (tka,))[0][0] == 'Tradovate ' + tag, 'the page opened again: the comment stays')
    ra = adm.get(f'/api/admin/mail/campaigns/{cid}', headers=H).json()
    ok(ra['stats']['answers'] == 1 and ra['questions'][0]['counts'].get('1') == 1 and ra['comments'][0]['message'] == 'Tradovate ' + tag, 'the campaign\'s numbers: 1 answered, « La synchro » 1, the comment')
    ok(s['opens'] == 1 and s['opens_auto'] == 1 and s['clicks'] == 1 and s['unsubs'] == 1 and s['bounces'] == (cst == 'failed'), 'numbers: 1 real open (+1 machine), 1 click, 1 unsubscribed, 1 bounce (%s)' % json.dumps({k: s[k] for k in ('sent', 'opens', 'opens_auto', 'clicks', 'unsubs', 'bounces')}))

    # the numbers page
    for w, hgt, mob, scheme in ((390, 844, True, 'dark'), (1300, 850, False, 'light')):
      t = f'{w}px {scheme}'
      cx = br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': hgt}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, color_scheme=scheme)
      cx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      q = cx.new_page(); er = []; q.on('pageerror', lambda e: er.append(str(e)[:150]))
      q.goto(B + f'/#mail/{cid}'); q.wait_for_selector('#main .ml-rep .ml-kpis', timeout=15000); q.wait_for_timeout(600)
      txt = q.inner_text('#main .ml-rep')
      ok('Envoyée' in txt and 'Livrés' in txt and 'Ouverts' in txt and 'Cliqués' in txt and 'Désinscrits' in txt, f'{t} the numbers page: delivered, opened, clicked, unsubscribed')
      ok('Ont répondu' in txt and 'Réponses' in txt and 'La synchro' in txt and 'Tradovate ' + tag in txt, f'{t} the answers: answered, each option, the last comment')
      ok('ouverture' in txt and 'automatique' in txt and q.locator('#main .ml-bars rect').count() >= 48 and 'makeitsweep.com/guide' in txt, f'{t} machine opens apart, the 48 hours, the most clicked link')
      ov = q.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
      ok(ov <= 0 and not er, f'{t} no horizontal scroll ({ov}), no page error {er[:2]}')
      q.screenshot(path=f'{SHOTS}/e2e_mail_report_{w}_{scheme}.png', full_page=True)
      cx.close()
    ok(not errs, f'send page: no page error {errs[:2]}')
    # Admin › Feedback « Depuis un courriel »: the answer with its email and question
    for w, hgt, mob, scheme in ((390, 844, True, 'dark'), (1300, 850, False, 'light')):
      cx = br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': hgt}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, color_scheme=scheme)
      cx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      q = cx.new_page(); er = []; q.on('pageerror', lambda e: er.append(str(e)[:150]))
      q.goto(B + '/#admin'); q.wait_for_selector('[data-act="gadm-f"][data-v="mail"]', timeout=20000); q.click('[data-act="gadm-f"][data-v="mail"]'); q.wait_for_timeout(1500)
      it = q.locator('.fb-item.adm', has_text='Tradovate ' + tag)
      ok(q.inner_text('[data-act="gadm-f"][data-v="mail"]').strip() == 'Depuis un courriel' and it.count() == 1 and 'La synchro' in it.inner_text() and 'Test ' + tag in it.inner_text() and 'manque' in it.inner_text(), f'{w}px {scheme} Admin › Feedback « Depuis un courriel »: the email, the question, the answer, the comment')
      ov = q.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
      ok(ov <= 0 and not er, f'{w}px {scheme} Admin › Feedback: no horizontal scroll ({ov}), no page error {er[:2]}')
      it.scroll_into_view_if_needed(); it.screenshot(path=f'{SHOTS}/e2e_mail_fb_{w}_{scheme}.png')
      cx.close()

    # the automations (step 5): in the list, an automation's page (its text, on or off, a test, its numbers; no audience, no delete)
    autos = adm.get('/api/admin/mail', headers=H).json()['autos']
    wel = next(x for x in autos if x['auto'] == 'signedUp')
    ok(len(autos) == 18 and wel['kind'] == 'marketing' and next(x for x in autos if x['auto'] == 'paymentFailed')['kind'] == 'transactional', f'api: the 18 automations, their kind ({len(autos)})')
    ok(adm.post(f"/api/admin/mail/campaigns/{wel['id']}/send", data='{}', headers=H).status == 409 and adm.delete(f"/api/admin/mail/campaigns/{wel['id']}", headers=H).status == 409, 'an automation is never sent by hand nor deleted (409)')
    orig = adm.get(f"/api/admin/mail/campaigns/{wel['id']}", headers=H).json()['campaign']
    try:
      for w, hgt, mob, scheme in ((1300, 850, False, 'dark'), (390, 844, True, 'light'), (390, 844, True, 'dark'), (1300, 850, False, 'light')):
        t = f'{w}px {scheme}'
        cx = br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': hgt}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, color_scheme=scheme)
        cx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
        q = cx.new_page(); er = []; q.on('pageerror', lambda e: er.append(str(e)[:150]))
        q.goto(B + '/#mail'); q.wait_for_selector('#main .ml-autos .ml-row', timeout=15000); q.wait_for_timeout(500)
        row = q.locator(f"#main .ml-autos a[href=\"#mail/{wel['id']}\"]")
        ok(q.locator('#main .ml-autos .ml-row').count() == 18 and 'Automatisations' in q.inner_text('#main .ml') and 'Bienvenue' in row.inner_text() and 'Allumé' in row.inner_text() and 'Juste après l’inscription' in row.inner_text(), f'{t} #mail: « Automatisations », 18 rows, « Bienvenue » allumé, what sends it')
        q.screenshot(path=f'{SHOTS}/e2e_mail_autos_{w}_{scheme}.png', full_page=True)
        row.click(); q.wait_for_selector('#main .ml-auto textarea', timeout=15000); q.wait_for_timeout(600)
        q.click('#main .ml-tabs [data-v="fr"]'); q.wait_for_timeout(400)
        txt = q.inner_text('#main .ml-auto')
        ok(q.input_value('#main [data-mlf="subject"]') == orig['content']['fr']['subject'] and 'Respecte les désinscriptions' in txt and '{first} le prénom' in txt, f'{t} the automation: its French text, its kind, the values it fills in')
        ok(q.locator('#main .ml-auto [data-ml="del"], #main .ml-auto [data-ml-count], #main .ml-auto [data-mlf="name"], #main .ml-auto [data-ml="now"]').count() == 0 and q.locator('#main .ml-auto .ml-kpis .ux-m').count() == 5, f'{t} no audience, no name, no send, no delete; its 5 numbers')
        q.wait_for_function("(()=>{const r=document.querySelector('#main [data-ml-prev]'); return r && r.shadowRoot && r.shadowRoot.textContent.includes('Bienvenue dans Sweep')})()", timeout=10000)
        ok(True, f'{t} the preview of the automation')
        if w == 1300 and scheme == 'dark':   # once: switched off and on, the text edited and saved on its own, a test
          q.click('#main [data-ml="auto"]'); q.wait_for_timeout(900)
          st = adm.get(f"/api/admin/mail/campaigns/{wel['id']}", headers=H).json()['campaign']['status']
          ok(st == 'off' and 'Éteint' in q.inner_text('#main .ml-auto .sec-h') and q.inner_text('#main [data-ml="auto"]').strip() == 'Allumer', f'{t} « Éteindre »: off ({st})')
          q.click('#main [data-ml="auto"]'); q.wait_for_timeout(900)
          ok(adm.get(f"/api/admin/mail/campaigns/{wel['id']}", headers=H).json()['campaign']['status'] == 'active', f'{t} « Allumer »: on again')
          q.fill('#main [data-mlf="subject"]', 'Bienvenue, {first} ' + tag); q.wait_for_timeout(1400)
          c2 = adm.get(f"/api/admin/mail/campaigns/{wel['id']}", headers=H).json()['campaign']
          ok(c2['content']['fr']['subject'] == 'Bienvenue, {first} ' + tag and c2['status'] == 'active' and c2['name'] == orig['name'], f'{t} the text saved on its own (status and name untouched)')
          n0 = len(sent_lines()); q.click('#main [data-ml="test"]'); q.wait_for_timeout(1500)
          last = sent_lines()[-1] if len(sent_lines()) > n0 else {}
          ok(last.get('subject', '').startswith('[Test] Bienvenue, ') and 'Test envoyé' in q.inner_text('#main [data-ml-msg]'), f"{t} « M'envoyer un test »: the edited French text ({last.get('subject', '')[:40]})")
          adm.post(f"/api/admin/mail/campaigns/{wel['id']}", data=json.dumps({'content': orig['content']}), headers=H)   # its own text again for the next sizes
        ov = q.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
        ok(ov <= 0 and not er, f'{t} automation: no horizontal scroll ({ov}), no page error {er[:2]}')
        q.screenshot(path=f'{SHOTS}/e2e_mail_auto_{w}_{scheme}.png', full_page=True)
        cx.close()
    finally:
      adm.post(f"/api/admin/mail/campaigns/{wel['id']}", data=json.dumps({'content': orig['content']}), headers=H)
      adm.post(f"/api/admin/mail/campaigns/{wel['id']}/auto", data=json.dumps({'on': orig['status'] == 'active'}), headers=H)
    br.close()
  finally:
    if not had: sql("UPDATE users SET email = NULL, email_lc = NULL WHERE username = 'mateo'")
print('screenshots: ' + SHOTS + '/e2e_mail_*.png')
sys.exit(1 if fails else 0)
