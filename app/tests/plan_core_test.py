"""Plan Sync — the chart add-ons' shared logic (sync/addon/plan/PlanCore.cs): its tests (sync/addon/plan/tests) run with .NET in a
temporary copy (no bin/ or obj/ in the repository). Without the .NET SDK (the CI), it says so and passes: the logic is then
only checked where .NET exists (Mateo's Mac: brew install dotnet).
   python3 tests/plan_core_test.py"""
import os, shutil, subprocess, sys, tempfile
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, 'sync', 'addon', 'plan')

def dotnet():
  for d in [shutil.which('dotnet'), '/opt/homebrew/bin/dotnet', os.path.expanduser('~/.dotnet/dotnet'), '/usr/local/share/dotnet/dotnet']:
    if d and os.path.isfile(d) and os.access(d, os.X_OK): return d
  return None

DN = dotnet()
ENV0 = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
if DN and os.path.realpath(DN).startswith('/opt/homebrew/') and 'DOTNET_ROOT' not in ENV0: ENV0['DOTNET_ROOT'] = '/opt/homebrew/opt/dotnet/libexec'
sdks = subprocess.run([DN, '--list-sdks'], env=ENV0, capture_output=True, text=True).stdout if DN else ''
if not any(l.split('.')[0].isdigit() and int(l.split('.')[0]) >= 10 for l in sdks.splitlines()):   # net10.0, as Quantower
  print('--   no .NET 10 SDK here: the Plan Sync logic tests are skipped'); sys.exit(0)
tmp = tempfile.mkdtemp(prefix='sweep-plan-')
try:
  work = os.path.join(tmp, 'plan'); shutil.copytree(SRC, work, ignore=shutil.ignore_patterns('bin', 'obj'))
  env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
  if os.path.realpath(DN).startswith('/opt/homebrew/') and 'DOTNET_ROOT' not in env: env['DOTNET_ROOT'] = '/opt/homebrew/opt/dotnet/libexec'
  b = subprocess.run([DN, 'build', os.path.join(work, 'tests', 'PlanCoreTests.csproj'), '-c', 'Release', '-nologo', '-v', 'q', '-o', os.path.join(tmp, 'out'), '-p:TreatWarningsAsErrors=true'], env=env, capture_output=True, text=True)
  if b.returncode:
    print(b.stdout[-4000:], b.stderr[-2000:]); print('FAIL the Plan Sync logic does not compile'); sys.exit(1)
  r = subprocess.run([DN, os.path.join(tmp, 'out', 'PlanCoreTests.dll')], env=env, capture_output=True, text=True)
  print(r.stdout, end=''); print(r.stderr, end='')
  sys.exit(r.returncode)
finally:
  shutil.rmtree(tmp, ignore_errors=True)
