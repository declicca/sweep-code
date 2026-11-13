"""
Sweep — Admin dashboard (brief 01 step 4), dev environment with Playwright:
  python3 tests/e2e_admin_metrics.py http://127.0.0.1:8095 /tmp/show_state.json        (the test trader is the admin)
 - a JS error sent by a trader's browser (api/client-error) is listed, grouped by message, with the traders affected,
   the page, the browser and the version;
 - the four indicators of the brief (activation on the sign-up day, retention D7 and D30, swept days), then the journey's
   baseline (SWEEP.md, step 0): closed days, Friday recaps opened; the brief activation's step C: back on the next trading
   day, risk allowed seen on the sign-up session, when they sign up (4 moments of the New York day);
 - the sign-up week and source filters reload the numbers (« N of M traders »);
 - « Exporter »: the 30-day list as a Markdown file (api/admin/errors-export), with the error and where it happened;
 - « Exporter pour Claude » (27 Oct.): everything Admin shows as one Markdown file (api/admin/report), and the app
   sends the pages it opened, its device and language when it is hidden (api/usage);
 - (7 Nov., brief « premier plan », step 1) a new trader opens his first plan and closes it without saving: the app sends the
   screen and « closed » (api/usage); « Le premier plan, écran par écran » lists it (reached, left here, median time), by start
   and device (the device list redraws the table);
 - FR words, phone and computer, no horizontal scroll, no page error.
"""
import asyncio, json, os, random, sqlite3, sys, time
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    msg = 'Test error %06d' % random.randint(0, 999999)
    # a new trader's first plan, closed without saving (the cross), on a computer
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    nc = await br.new_context(locale='fr-CA', viewport={'width': 1300, 'height': 850})
    await nc.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    r = await nc.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'fp%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.status == 201, f'a new trader signs up ({r.status})')
    np_ = await nc.new_page(); await np_.goto(B + '/'); await np_.wait_for_function("() => !!(window.SweepGame && SweepGame.openPlan)", timeout=20000); await np_.wait_for_timeout(800)
    await np_.evaluate("SweepGame.openPlan((window.SweepNextSession && SweepNextSession()) || new Date().toISOString().slice(0, 10), { then: () => {} })")
    await np_.wait_for_selector('#gSheet.g-plan.open', timeout=8000); await np_.wait_for_timeout(1200)
    async with np_.expect_request(lambda x: x.url.endswith('/api/usage') and '"fp"' in (x.post_data or ''), timeout=8000) as rq:
      await np_.locator('#gSheet [data-g=close]').click()
    fp = ((await rq.value).post_data_json or {}).get('fp') or {}
    ok(fp.get('end') == 'closed' and [x[0] for x in fp.get('s', [])] == ['form'], f'the first plan closed without saving is sent: the short form, « closed » ({fp})')
    await np_.wait_for_timeout(500); await nc.close()
    for w, h, mob in ((1440, 900, False), (390, 844, True)):
      tag = f'{w}px'
      ctx = await br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(1500)
      if not mob:   # what the app does when a script fails on a trader's device
        r = await pg.evaluate(f"fetch('api/client-error',{{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json','X-Requested-With':'fetch'}},body:JSON.stringify({{msg:'{msg}',src:'app.js',line:7,page:'#trades',ver:'app.test'}})}}).then(r=>r.status)")
        ok(r == 200, f'a JS error is received by the server ({r})')
      await pg.evaluate("location.hash='#admin'"); await pg.wait_for_selector('#main .ux-brief', timeout=15000); await pg.wait_for_timeout(800)
      cards = await pg.evaluate("[...document.querySelectorAll('#main .ux-brief .ux-m small')].map(s=>s.textContent)")
      want = ['Activation : un trade le jour de l’inscription', 'Rétention J7', 'Rétention J30', 'Journées balayées', 'Journées fermées', 'Bilans de la semaine ouverts', 'De retour le jour de trading suivant', 'Risque permis vu le jour de l’inscription']
      ok(all(any(c.startswith(x) for c in cards) for x in want), f'{tag} the four indicators, closed days and Friday recaps opened (SWEEP.md, step 0) ({cards})')
      # (brief « pertes oubliées », step 1) the complete journal: 3 figures, over 7 and 30 days
      jr = await pg.evaluate("[...document.querySelectorAll('#main .ux-journal tbody tr')].map((r) => [r.dataset.jr, r.children.length, r.getClientRects().length > 0])")
      # (step 2) and the days closed on the platform's balance: with a gap, the gaps' total, the share detailed in trades
      ok([x[0] for x in jr] == ['high_win_20', 'losing_trades', 'days_without_loss', 'gap_days', 'gap_total_c', 'gap_detailed'] and all(x[1] == 3 and x[2] for x in jr) and 'Journal complet' in (await pg.evaluate("document.getElementById('main').innerText")),
         f'{tag} « Journal complet »: 6 figures, 7 and 30 days ({jr})')
      # (brief activation, step C) when they sign up: the 4 moments of the New York day, each with its sign-ups and the share with a first plan or trade
      sl = await pg.evaluate("[...document.querySelectorAll('#main .ux-slots tbody tr')].map((r) => [r.dataset.slot, r.children.length, r.getClientRects().length > 0])")
      ok([x[0] for x in sl] == ['before', 'session', 'evening', 'weekend'] and all(x[1] == 3 and x[2] for x in sl), f'{tag} « Quand ils s’inscrivent »: 4 moments, sign-ups and first plan or trade ({sl})')
      # (brief « premier plan », step 1) the first plan, screen by screen; on a computer, the device list redraws it
      fpt = await pg.evaluate("(() => { const b = document.querySelector('#main .ux-fp'); if (!b) return null; const r = b.querySelector('tr[data-fps=form]'); const x = b.querySelector('.scroll-x'); return [b.querySelector('h4').textContent, [...b.querySelectorAll('thead th')].map((t) => t.textContent), r ? [...r.children].map((c) => c.textContent.trim()) : null, b.querySelectorAll('select').length, x.scrollWidth <= x.clientWidth] })()")
      ok(fpt and fpt[0] == 'Le premier plan, écran par écran' and fpt[1] == ['Écran', 'Atteignent', 'Partent ici', 'Temps médian'] and fpt[2] and fpt[2][0] == 'Plan court (un écran)' and int(fpt[2][1]) >= 1 and int(fpt[2][2]) >= 1 and fpt[3] == 2 and fpt[4],
         f'{tag} « Le premier plan, écran par écran »: the short form reached and left, the start and device lists, the 4 columns in the width ({fpt})')
      await pg.select_option('#main [data-ux-fp=d]', 'desktop'); await pg.wait_for_timeout(300)
      fpd = await pg.evaluate("(() => { const r = document.querySelector('#main .ux-fp tr[data-fps=form]'); return [document.querySelector('#main [data-ux-fp=d]').value, r ? +r.children[2].textContent : 0, (document.querySelector('#main .ux-fp-end') || {}).textContent || ''] })()")
      ok(fpd[0] == 'desktop' and fpd[1] >= 1 and fpd[2].startswith('Plans mesurés'), f'{tag} « Ordinateur »: the table redrawn, the new trader\'s plan in it ({fpd})')
      await pg.evaluate("document.querySelector('#main .ux-fp').scrollIntoView({block: 'center'})"); await pg.wait_for_timeout(300); await pg.screenshot(path=f'/tmp/admin_first_plan_{w}.png')
      await pg.select_option('#main [data-ux-fp=d]', 'all'); await pg.wait_for_timeout(200)
      row = await pg.evaluate(f"(()=>{{const r=[...document.querySelectorAll('#main .ux-errs tbody tr')].find(t=>t.textContent.includes('{msg}')); return r?[...r.children].map(c=>c.textContent.trim()):null}})()")
      ok(row is not None and row[1] == '1' and row[2] == '1' and row[4] == '#trades' and 'Chrome' in row[5] and row[6] == 'app.test', f'{tag} the error: 1 trader, 1 time, page, browser, version ({row})')
      # « Exporter » (13 Oct.): the 30-day list as a Markdown file, to give to Claude
      exp = await pg.evaluate("(() => { const a = document.querySelector('#main .ux-err-h a[download]'); return a ? [a.textContent.trim(), a.getAttribute('href')] : null; })()")
      ok(exp == ['Exporter', 'api/admin/errors-export'], f'{tag} « Exporter » next to the errors ({exp})')
      if not mob:
        r = await pg.evaluate("fetch('api/admin/errors-export', { credentials: 'same-origin' }).then(async (r) => [r.status, r.headers.get('content-type'), r.headers.get('content-disposition'), await r.text()])")
        ok(r[0] == 200 and r[1].startswith('text/markdown') and 'attachment; filename="sweep-erreurs-' in (r[2] or '') and f'## ' in r[3] and msg in r[3] and '`app.js:7`' in r[3], f'the export: a Markdown file with the error, where it happened ({r[:3]})')
      # « Exporter pour Claude » (27 Oct.): everything Admin shows, one Markdown file (api/admin/report)
      rep = await pg.evaluate("(() => { const a = document.querySelector('#main .ux-rep-bar a[data-ux-rep]'); if (!a) return null; const r = a.getBoundingClientRect(); const h = document.querySelector('#main .ux-health-admin'); return [a.textContent.trim(), a.getAttribute('href'), r.width > 0 && r.right <= innerWidth + 1, !h || !!(a.compareDocumentPosition(h) & 4)]; })()")
      ok(rep == ['Exporter pour Claude', 'api/admin/report', True, True], f'{tag} « Exporter pour Claude » at the top of Admin, before Health, visible ({rep})')
      if not mob:
        r = await pg.evaluate("fetch('api/admin/report', { credentials: 'same-origin' }).then(async (r) => [r.status, r.headers.get('content-type'), r.headers.get('content-disposition'), await r.text()])")
        secs = [n for n in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13) if f'\n## {n}. ' not in r[3]]
        ok(r[0] == 200 and r[1].startswith('text/markdown') and 'attachment; filename="sweep-admin-' in (r[2] or '') and not secs and msg in r[3], f'the report: one Markdown file, every section, the error ({r[:3]}, missing {secs})')
        # the app tells how it is used: the page opened, the « + » sheet, sent when the app is hidden
        await pg.evaluate("location.hash = '#trades'"); await pg.wait_for_timeout(1200)
        async with pg.expect_response(lambda x: x.url.endswith('/api/usage'), timeout=8000) as rs:
          await pg.evaluate("Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange'))")
        res = await rs.value; sent = res.request.post_data_json or {}
        ok(res.status == 200 and 'p:trades' in sent.get('p', {}) and 'p:admin' in sent.get('p', {}) and sent.get('lang') == 'fr' and sent.get('dev') == 'desktop',
           f'the app sends the pages opened, the device and the language ({res.status} {sorted(sent.get("p", {}))} {sent.get("dev")})')
        await pg.evaluate("delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); location.hash = '#admin'"); await pg.wait_for_selector('#main .ux-brief', timeout=15000); await pg.wait_for_timeout(800)
        md = await pg.evaluate("fetch('api/admin/report', { credentials: 'same-origin' }).then((r) => r.text())")
        ok('\n| p:trades | ' in md and '\n| p:admin | ' in md and 'desktop' in md, 'the report lists the pages opened (section 4)')
      before = await pg.evaluate("document.querySelector('#main .ux-bf small').textContent")
      opts = await pg.evaluate("[...document.querySelectorAll('#main [data-ux-mf=source] option')].map(o=>o.value)")
      ok(len(opts) >= 2 and opts[0] == '', f'{tag} the source filter lists « Toutes » and the sources ({opts})')
      await pg.select_option('#main [data-ux-mf=source]', opts[1]); await pg.wait_for_timeout(1500)
      after = await pg.evaluate("document.querySelector('#main .ux-bf small').textContent")
      sel = await pg.evaluate("document.querySelector('#main [data-ux-mf=source]').value")
      ok(sel == opts[1] and after != '' and after.startswith('Traders : '), f'{tag} choosing a source reloads the numbers (« {before} » → « {after} »)')
      await pg.select_option('#main [data-ux-mf=source]', ''); await pg.wait_for_timeout(1200)
      wk = await pg.evaluate("[...document.querySelectorAll('#main [data-ux-mf=cohort] option')].map(o=>o.textContent).slice(1,2)")
      ok(bool(wk) and wk[0].startswith('sem. du'), f'{tag} the sign-up weeks « sem. du … » ({wk})')
      # (13 Nov., brief « comptes par firme ») the accounts by firm, under the start: a row per firm of the catalogue, « other », « personal », the total
      fm = await pg.evaluate("""(() => { const t = document.querySelector('#main table.ux-firms'); if (!t) return null; const st = document.querySelector('#main table.ux-start:not(.ux-slots):not(.ux-cases):not(.ux-journal):not(.ux-first-plan)');
        const w = t.closest('.scroll-x'), h = t.closest('.scroll-x').previousElementSibling;
        return { h: h.textContent, heads: [...t.tHead.rows[0].cells].map((c) => c.textContent), rows: [...t.tBodies[0].rows].map((r) => r.cells[0].textContent), cells: t.tBodies[0].rows[0].cells.length,
          after: !!st && !!(st.compareDocumentPosition(t) & 4), stacked: t.classList.contains('ux-stack'), over: Math.round(t.getBoundingClientRect().right - w.getBoundingClientRect().right), sub: (document.querySelector('#main .ux-firms-s') || {}).textContent || '',
          total: [...t.querySelector('tr.ux-firms-t').cells].map((c) => c.textContent) }; })()""")
      ok(bool(fm) and fm['h'] == 'Comptes par firme' and fm['heads'] == ['Firme', 'Comptes', 'Traders', 'Évaluation', 'Financé', 'Live', 'Trades (30 j)', 'À la main', 'Import CSV', 'Synchro'] and fm['after'], f'{tag} « Comptes par firme » under the start, its 10 columns ({fm and fm["heads"]})')
      ok(bool(fm) and len(fm['rows']) >= 5 and fm['rows'][-3:] == ['Autre firme', 'Compte personnel ou simulation', 'Total'] and 'Topstep' in fm['rows'] and fm['cells'] == 10, f'{tag} a row per firm, then « Autre firme », « Compte personnel ou simulation » and the total ({fm and fm["rows"]})')
      ok(bool(fm) and fm['over'] <= 0 and fm['stacked'] == mob and 'import CSV' in fm['sub'] and int(fm['total'][1]) >= 0, f'{tag} it fits its card ({"stacked rows" if mob else "a table"}), with what each column means under it ({fm and [fm["over"], fm["stacked"], fm["total"]]})')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
