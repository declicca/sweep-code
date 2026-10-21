"""
Sweep — the site's captures: Alex's platforms connected (Settings › Data › Connections), through the app's own API on the
capture server: NinjaTrader 8 and Quantower each with its key, their add-ons' first push (3 accounts found, no fills),
2 of them linked to their Sweep account, the third still to link.
  python3 tools/site-shots/connect.py <base_url> <state_file>
"""
import json, sys
from playwright.sync_api import sync_playwright
B, STATE = sys.argv[1], sys.argv[2]
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
PUSH = {'ninjatrader': ('Sweep NT8 1.4', [{'name': 'PA-APEX-224455-03', 'connection': 'Apex', 'provider': 'Rithmic'}, {'name': 'LFE-50K-118204', 'connection': 'Lucid', 'provider': 'Rithmic'}]),
        'quantower': ('Sweep Quantower 1.2', [{'name': 'XFA-50K-771204', 'connection': 'Topstep', 'provider': 'ProjectX'}])}
LINK = {'PA-APEX-224455-03': 'a4', 'XFA-50K-771204': 'a2'}   # the Lucid one stays « to link »
with sync_playwright() as p:
  br = p.chromium.launch(); ctx = br.new_context(storage_state=STATE); rq = ctx.request
  for plat, (client, accs) in PUSH.items():
    k = rq.post(B + '/api/sync/key', data=json.dumps({'platform': plat}), headers=H).json()
    key = k.get('key') or k.get('token') or ''
    r = rq.post(B + '/api/sync/push', data=json.dumps({'client': client, 'accounts': accs, 'fills': []}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
    assert r.ok, (plat, r.status, r.text()[:200])
  st = rq.get(B + '/api/sync', headers=H).json()
  for a in st.get('accounts', []):
    name = a.get('name') or (a.get('info') or {}).get('name') or a.get('ext_id')
    if name in LINK:
      r = rq.post(B + '/api/sync/accounts/' + a['id'], data=json.dumps({'action': 'link', 'account_id': LINK[name]}), headers=H)
      print('link', name, r.status)
  print(json.dumps(rq.get(B + '/api/sync', headers=H).json())[:900])
  br.close()
