"""
Sweep — data isolation test: trader B must never read or change trader A's data, through any route.
Run in a dev environment: python3 tests/e2e_isolation.py http://127.0.0.1:8095
"""
import asyncio, random, sys, json
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')
async def user(p, name):
  ctx = await p.request.new_context(base_url=B)
  r = await ctx.post('/api/auth/register', data=json.dumps({'username': name, 'password': 'Testpass123!', 'email': name + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
  assert r.status == 201, await r.text()
  return ctx
async def main():
  async with async_playwright() as p:
    n = random.randint(1000, 9999); A = await user(p, f'iso_a{n}'); Bc = await user(p, f'iso_b{n}')
    fails = 0
    def check(name, ok):
      nonlocal fails; print(('ok   ' if ok else 'FAIL ') + name); fails += 0 if ok else 1
    await A.put('/api/docs/trades/secret-1', data=json.dumps({'id': 'secret-1', 'account_id': 'x', 'instrument': 'NQ', 'date': '2026-10-01', 'pnl_c': 123400, 'notes': 'A only'}), headers=H)
    up = await (await A.post('/api/uploads', data=PNG, headers={'X-Requested-With': 'fetch', 'Content-Type': 'image/png'})).json()
    data_b = await (await Bc.get('/api/data')).text()
    check('B cannot see A’s trades in its data', 'secret-1' not in data_b and 'A only' not in data_b)
    check('B cannot open A’s screenshot', (await Bc.get('/uploads/' + up['id'])).status in (401, 403, 404))
    await Bc.post('/api/uploads/' + up['id'] + '?_method=DELETE', headers=H)   # answered as a no-op: it is not B's file
    check('B cannot delete A’s screenshot', (await A.get('/uploads/' + up['id'])).status == 200)
    r = await Bc.get('/api/chart/bars?trade_id=secret-1')
    check('B cannot load the chart of A’s trade', r.status in (401, 403, 404) or 'bars' not in (await r.text()))
    await Bc.put('/api/docs/trades/secret-1', data=json.dumps({'id': 'secret-1', 'notes': 'overwritten by B'}), headers=H)
    data_a = await (await A.get('/api/data')).text()
    check('B writing the same id never touches A’s trade', 'A only' in data_a and 'overwritten by B' not in data_a)
    exp = await Bc.get('/api/export/full')
    check('B’s export contains nothing of A', b'A only' not in await exp.body())
    anon = await p.request.new_context(base_url=B)
    check('signed out: no data', (await anon.get('/api/data')).status in (401, 403))
    print(f'{7 - fails}/7 passed'); sys.exit(1 if fails else 0)
asyncio.run(main())
