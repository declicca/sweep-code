"""Plan Sync on NinjaTrader 8 (step 4): the Sweep Plan indicator (sync/addon/ninjatrader-plan/SweepPlan.cs).
1. It compiles in C# 5, the language NinjaTrader 8 compiles, with the shared logic (sync/addon/plan/PlanCore.cs), against WPF,
   SharpDX and stubs of NinjaTrader's API (check/). NinjaTrader compiles the real thing itself from the source it imports.
2. With a server (BASE): its network, files and logic run for real (check/run/, NinjaTrader and WPF stubbed) against a test
   trader: the plan read with Sweep Sync's key, MNQ and NQ charts → one alert each, the events in Sweep, another platform's key
   refused, no key → where to paste it.
Without a .NET 10 SDK (the CI), it says so and passes: like plan_core_test.py, it runs where .NET exists (Mateo's Mac).
Its files go to a temporary folder (SWEEP_PLAN_TEST_DIR), never to Documents.
   python3 tests/ninjatrader_plan_test.py [BASE]"""
import fcntl, json, os, shutil, sqlite3, subprocess, sys, tempfile, urllib.request, urllib.error, http.cookiejar, uuid
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(APP, 'sync', 'addon')
B = (sys.argv[1] if len(sys.argv) > 1 else '').rstrip('/')
fails = 0

def ok(c, what):
  global fails
  if not c: fails += 1
  print(('ok   ' if c else 'FAIL ') + what)

def dotnet():
  for d in [shutil.which('dotnet'), '/opt/homebrew/bin/dotnet', os.path.expanduser('~/.dotnet/dotnet'), '/usr/local/share/dotnet/dotnet']:
    if d and os.path.isfile(d) and os.access(d, os.X_OK): return d
  return None

DN = dotnet()
ENV = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
if DN and os.path.realpath(DN).startswith('/opt/homebrew/') and 'DOTNET_ROOT' not in ENV: ENV['DOTNET_ROOT'] = '/opt/homebrew/opt/dotnet/libexec'
sdks = subprocess.run([DN, '--list-sdks'], env=ENV, capture_output=True, text=True).stdout if DN else ''
if not any(l.split('.')[0].isdigit() and int(l.split('.')[0]) >= 10 for l in sdks.splitlines()):
  print('--   no .NET 10 SDK here: the NinjaTrader 8 Plan Sync checks are skipped'); sys.exit(0)

def build(proj, out):
  """dotnet build, one at a time on this machine: the copies of tools/par.py run at once, and their first restores of the same
  NuGet packages (a fresh CI machine) collide in the shared cache"""
  with open(os.path.join(tempfile.gettempdir(), 'sweep-dotnet-build.lock'), 'w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    r = subprocess.run([DN, 'build', proj, '-c', 'Release', '-nologo', '-v', 'q', '-o', out], env=ENV, capture_output=True, text=True)
  if r.returncode:
    errs = [l.strip() for l in (r.stdout + r.stderr).splitlines() if ' error ' in l or 'error NU' in l or 'error NETSDK' in l or 'error MSB' in l]
    print('\n'.join(sorted(set(errs))[:20]) or (r.stdout[-3000:] + r.stderr[-1500:]))
  return r.returncode

tmp = tempfile.mkdtemp(prefix='sweep-ntplan-')
try:
  # a copy without bin/ or obj/ (nothing lands in the repository)
  work = os.path.join(tmp, 'addon')
  for d in ('plan', 'ninjatrader-plan'): shutil.copytree(os.path.join(ADDON, d), os.path.join(work, d), ignore=shutil.ignore_patterns('bin', 'obj'))
  src = open(os.path.join(ADDON, 'ninjatrader-plan', 'SweepPlan.cs'), encoding='utf-8').read()

  # what NinjaTrader needs, read in the source
  ok('public class SweepPlan : Indicator' in src and 'namespace NinjaTrader.NinjaScript.Indicators' in src and '#region NinjaScript generated code. Neither change nor remove.' in src, 'an indicator of NinjaTrader 8 (namespace, base class, the generated code NinjaTrader expects)')
  ok('SetZOrder(-1)' in src and 'IsAutoScale = false' in src and 'IsOverlay = true' in src, 'drawn behind the bars, on the price panel, never changing the price scale')
  ok('NinjaTrader.NinjaScript.Alert.AlertCallback(' in src and '"sounds", "Alert2.wav"' in src, 'alerts in NinjaTrader\'s Alerts window, with a sound')
  ok('SweepSyncEngine.Key' in src and '"Sweep NT8 Plan "' in src and '/api/plan-sync/today?instrument=' in src and '/api/plan-sync/events' in src, 'Sweep Sync\'s key, named « Sweep NT8 … » (a NinjaTrader 8 key only), the two Plan Sync addresses')
  ok(all(s not in src for s in ('Submit', 'CreateOrder', 'EnterLong', 'EnterShort', 'ExitLong', 'ExitShort', 'Flatten', 'Cancel(', 'Account.')), 'reminders only: no order function anywhere')
  ok('AddOns/SweepPlanCore.cs' in open(os.path.join(APP, 'tools', 'addon-zip.py'), encoding='utf-8').read(), 'the shared logic travels in the zip as AddOns/SweepPlanCore.cs')

  # 1. compiles in C# 5 against WPF, SharpDX and NinjaTrader's stubs
  ok(build(os.path.join(work, 'ninjatrader-plan', 'check', 'SweepPlanCheck.csproj'), os.path.join(tmp, 'check')) == 0, 'the indicator and the shared logic compile in C# 5 (NinjaTrader 8\'s language), 0 warning')

  # 2. live, against a test trader
  if B:
    H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
    jar = http.cookiejar.CookieJar(); web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def call(method, path, body=None):
      req = urllib.request.Request(B + '/' + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=H)
      try:
        with web.open(req, timeout=30) as r: raw = r.read(); return r.status, (json.loads(raw) if raw else {})
      except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, (json.loads(raw) if raw else {})
        except Exception: return e.code, {}
    n = 'ntplan' + uuid.uuid4().hex[:8]
    s, _ = call('POST', 'api/auth/register', {'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000, 'lang': 'fr'})
    ok(s in (200, 201), 'sign-up of a test trader (French)')
    nt = call('POST', 'api/sync/key', {'platform': 'ninjatrader'})[1].get('key', '')
    qt = call('POST', 'api/sync/key', {'platform': 'quantower'})[1].get('key', '')
    ok(nt.startswith('swk_') and qt.startswith('swk_'), 'a NinjaTrader 8 key, and a Quantower key')
    req = urllib.request.Request(B + '/api/plan-sync/today?instrument=NQ', headers={'X-Sweep-Key': nt, 'X-Sweep-Client': 'Sweep NT8 Plan test'})
    with urllib.request.urlopen(req, timeout=30) as r: day = json.loads(r.read()).get('day', '')
    zid = 'nt' + uuid.uuid4().hex[:8]
    s, _ = call('PUT', 'api/docs/journals/' + day, {'chart': {'zones': [{'id': zid, 'instrument': 'NQ', 'type': 'level', 'price': 21300, 'label': 'PDH', 'role': 'resistance', 'proximity_ticks': 40}], 'rules': []}})
    ok(s == 200 and len(day) == 10, 'the day\'s plan saved in the app: PDH 21300 on NQ (' + day + ')')
    rc = build(os.path.join(work, 'ninjatrader-plan', 'check', 'run', 'SweepPlanRun.csproj'), os.path.join(tmp, 'run'))
    ok(rc == 0, 'the live run builds')
    if rc == 0:
      home = os.path.join(tmp, 'files')
      x = subprocess.run([DN, os.path.join(tmp, 'run', 'SweepPlanRun.dll'), B, nt, qt], env=dict(ENV, SWEEP_PLAN_TEST_DIR=home), capture_output=True, text=True, timeout=120)
      out = x.stdout
      print(''.join('     ' + l + '\n' for l in out.splitlines() if not l.startswith('folder ')), end='')
      if x.stderr.strip(): print(x.stderr[-2000:])
      folder = next((l[7:] for l in out.splitlines() if l.startswith('folder ')), '')
      ok(x.returncode == 0 and 'all passed' in out, 'the indicator\'s own code against Sweep: plan, alerts once, events, keys')
      ok(folder.startswith(home), 'its files went to the temporary folder only (' + folder + ')')
      st = call('GET', 'api/sync')[1]
      ok(st.get('plan_read_by') == 'ninjatrader', 'Sweep knows the plan was read by NinjaTrader 8 (« Synchronisé avec NinjaTrader 8 » in the editor)')
      db = os.environ.get('SWEEP_TEST_DB', '')
      if db and os.path.isfile(db):
        c = sqlite3.connect(db)
        rows = sorted(t for (t,) in c.execute('SELECT type FROM plan_sync_events WHERE id LIKE ?', ('ps.%.z' + zid + '.%',)))
        c.close()
        ok(rows == ['zone_approached', 'zone_entered'], 'the events in Sweep: approached, entered, once each (re-arming does not send the same event twice: same id) (%s)' % rows)
finally:
  shutil.rmtree(tmp, ignore_errors=True)

print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
