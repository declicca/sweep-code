"""Signs mateo in, fills the profile, adds the sample data and saves the session to /tmp/show_state.json.
   python3 tools/prof.py [base_url] [state_file]"""
import asyncio, re, sys
from playwright.async_api import async_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
PASS = re.search(r"'password'\s*=>\s*'([^']+)'", open(__file__.rsplit('/', 1)[0] + '/config.local.php').read()).group(1)
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        ctx = await br.new_context(viewport={'width': 1300, 'height': 850}, locale='fr-CA')
        await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
        pg = await ctx.new_page()
        await pg.goto(BASE + '/')   # first request creates the admin account from config.php
        r = await ctx.request.post(BASE + '/api/auth/login', headers=H, data={'username': 'mateo', 'password': PASS})
        assert r.ok, 'login: %s %s' % (r.status, await r.text())
        r = await ctx.request.post(BASE + '/api/me/profile', headers=H, data={'first_name': 'Mateo', 'last_name': 'De Cristofaro', 'experience': 'gt1'})
        assert r.ok, 'profile: %s %s' % (r.status, await r.text())
        # the app is ready when loadDemo exists (not « network idle »: one slow request is enough to miss it)
        await pg.goto(BASE + '/'); await pg.wait_for_function("typeof loadDemo === 'function'", timeout=60000)
        await pg.evaluate('void loadDemo()')
        await pg.wait_for_selector('aside.nav-ask.open [data-ask="1"]', timeout=15000)
        await pg.click('aside.nav-ask.open [data-ask="1"]')
        await pg.wait_for_timeout(8000)
        try: await pg.wait_for_load_state('networkidle', timeout=10000)
        except Exception: pass   # the sample data are saved by then; a slow side request must not fail the setup
        print('sample data added')
        await ctx.storage_state(path=STATE); await br.close()
asyncio.run(main())
