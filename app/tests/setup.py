"""Sweep — test setup: everything the tests need, created on the test server (never a real one).
   python3 tests/setup.py [base_url] [state_file]          (run by tests/run-all.sh before the tests)
 - the test trader « mateo » (admin, created by the server from the local config at the first request) signs in;
 - his profile is filled (otherwise the « Complete your profile » window covers every page);
 - the sample data are added once (accounts, trades, payouts, journals), through the app's own « Add sample data »;
 - the signed-in session is saved to state_file (default /tmp/show_state.json), used by the tests.
The password is the local test one (tools/config.local.php, or SWEEP_TEST_PASSWORD). Tests that need other traders
create them themselves (POST /api/auth/register then /api/me/profile)."""
import asyncio, os, re, sys
from playwright.async_api import async_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'config.local.php')
PASS = os.environ.get('SWEEP_TEST_PASSWORD') or re.search(r"'password'\s*=>\s*'([^']+)'", open(LOCAL).read()).group(1)
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        # bypass_csp: Playwright's waits evaluate their condition, which the app's Content Security Policy forbids (setup only)
        ctx = await br.new_context(viewport={'width': 1300, 'height': 850}, locale='fr-CA', bypass_csp=True)
        await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
        pg = await ctx.new_page()
        await pg.goto(BASE + '/')   # the first request creates the admin account from the local config
        r = await ctx.request.post(BASE + '/api/auth/login', headers=H, data={'username': 'mateo', 'password': PASS})
        assert r.ok, 'login: %s %s' % (r.status, await r.text())
        r = await ctx.request.post(BASE + '/api/me/profile', headers=H, data={'first_name': 'Mateo', 'last_name': 'De Cristofaro', 'experience': 'gt1'})
        assert r.ok, 'profile: %s %s' % (r.status, await r.text())
        # the app is ready when loadDemo exists (not « network idle »: one slow request is enough to miss it)
        await pg.goto(BASE + '/'); await pg.wait_for_function("typeof loadDemo === 'function' && typeof S !== 'undefined' && Array.isArray(S.trades)", timeout=60000)
        if not await pg.evaluate("S.trades.some(t => t.demo)"):
            await pg.evaluate('void loadDemo()')
            await pg.wait_for_selector('aside.nav-ask.open [data-ask="1"]', timeout=15000)
            await pg.click('aside.nav-ask.open [data-ask="1"]')
            await pg.wait_for_function("S.trades.some(t => t.demo) && S.accounts.length > 0", timeout=60000)
            await pg.wait_for_timeout(3000)   # the sample data are saved in batches
        n = await pg.evaluate("[S.accounts.length, S.trades.length]")
        assert n[0] > 0 and n[1] > 0, 'sample data missing: %s' % n
        await ctx.storage_state(path=STATE); await br.close()
        print('setup ok: mateo signed in, %d accounts, %d trades, session in %s' % (n[0], n[1], STATE))
asyncio.run(main())
