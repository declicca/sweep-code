"""
Sweep — « The reality of the month »: the server (money/money.php) and the app (moneyOf in src/ux.js) give the same
numbers, and the notification is sent once, on the 1st. Dev environment:
  python3 tests/e2e_money_parity.py http://127.0.0.1:8095 [path/to/journal.db] [app folder]
"""
import asyncio, sys, random, subprocess, json, datetime
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith('.db') else '/tmp/g/data/journal.db'
APP = sys.argv[3] if len(sys.argv) > 3 else '/tmp/g'
H = {'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
PHP = r'''
$pdo = new PDO('sqlite:%s'); $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); function db() { global $pdo; return $pdo; } $cfg = ['notifications' => ['daily_limit' => 50]];
require '%s/notify/notify.php'; require_once '%s/notify/listeners.php'; require '%s/money/money.php';
$uid = $argv[1]; $mode = $argv[2];
if ($mode === 'period') echo json_encode(SweepMoneyServer::period($pdo, $uid, $argv[3], $argv[4]));
else { $r = []; foreach (['2026-11-01 09:00', '2026-11-01 10:00', '2026-11-02 09:00'] as $t) $r[] = SweepMoneyServer::monthly($pdo, $uid, new DateTimeImmutable($t, new DateTimeZone('America/New_York')));
  $n = $pdo->query("SELECT COUNT(*) FROM notifications WHERE user_id = " . $pdo->quote($uid) . " AND type = 'money_month'")->fetchColumn(); echo json_encode(['sent' => $r, 'count' => (int) $n]); }
'''
def php(*a):
  code = PHP % (DB, APP, APP, APP)
  return json.loads(subprocess.run(['php', '-r', code, '--', *a], capture_output=True, text=True).stdout or 'null')
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); u = 'par%d' % random.randint(10000, 99999)
    rq = await p.request.new_context(base_url=B)
    r = await rq.post('/api/auth/register', data={'username': u, 'password': 'Testpass123!', 'email': u + '@t.dev', 'consent': True, 'elapsed': 6000}, headers=H); assert r.status == 201, await r.text()
    await rq.post('/api/me/profile', data={'first_name': 'T', 'last_name': 'P', 'username': u}, headers=H)
    me = (await (await rq.get('/api/data', headers=H)).json())['user']; uid = me.get('id') or me.get('uid')
    ctx = await br.new_context(storage_state=await rq.storage_state()); await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg = await ctx.new_page(); await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("""(async()=>{ put('firms',{id:'f1',name:'Apex'}); const A=(id,mt,x)=>put('accounts',Object.assign({id,firm_id:'f1',name:id,starting_balance_c:5000000,status:'active',money_type:mt},x||{}));
      A('ev','eval',{rules:{target_c:300000}}); A('fu','funded'); A('li','live'); A('c2','eval');
      const T=(id,a,p,d,x)=>put('trades',Object.assign({id,account_id:a,instrument:'NQ',direction:'long',contracts:1,entry:1,exit:2,pnl_c:p,fees_c:500,pnl_manual:true,date:d,entry_time:'10:00',exit_time:'10:05',session_date:true},x||{}));
      T('a','ev',120000,'2026-10-03'); T('b','fu',230000,'2026-10-10'); T('c','li',45000,'2026-10-15'); T('d','li',-5000,'2026-10-20');
      T('e','ev',30000,'2026-10-21',{copy_group:'g',created_at:'2026-10-21T10:00:00Z'}); T('f','c2',30000,'2026-10-21',{copy_group:'g',created_at:'2026-10-21T10:00:05Z'});
      T('z','fu',999900,'2026-09-30');
      put('payouts',{id:'p1',account_id:'fu',firm_id:'f1',gross_c:100000,split_pct:90,fees_c:2500,net_c:87500,amount_c:100000,status:'paid',paid_on:'2026-10-25'});
      put('payouts',{id:'p2',account_id:'fu',firm_id:'f1',gross_c:50000,net_c:50000,amount_c:50000,status:'rejected',request_date:'2026-10-26'});
      put('expenses',{id:'x1',firm_id:'f1',account_id:'ev',category:'evaluation',amount_c:9900,date:'2026-10-02'}); put('expenses',{id:'x2',firm_id:'f1',category:'evaluation',amount_c:-2000,date:'2026-10-28'});
      await new Promise(r=>setTimeout(r,2500)); })()""")
    js = await pg.evaluate("(()=>{const m=SweepMoney.moneyOf({from:'2026-10-01',to:'2026-10-31',realOnly:true}); return {sim:m.perf.byType.eval+m.perf.byType.funded, received:m.real.payouts, expenses:m.real.expenses, live:m.real.live, net:m.real.net}})()")
    sv = php(uid, 'period', '2026-10-01', '2026-10-31')
    print('app', js, 'server', sv)
    ok(sv is not None and all(js[k] == sv[k] for k in ['sim', 'received', 'expenses', 'live', 'net']), 'the server and the app give the same numbers for the month')
    ok(js['sim'] == 120000 - 500 + 230000 - 500 + 30000 - 500 and js['received'] == 87500 and js['expenses'] == 7900 and js['net'] == 87500 + 45000 - 500 - 5000 - 500 - 7900, f'the expected numbers ({js})')
    n = php(uid, 'monthly')
    ok(n and n['sent'] == [True, False, False] and n['count'] == 1, f'« The reality of the month » is sent once, on the 1st ({n})')
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
