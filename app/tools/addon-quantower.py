"""Sweep — the Quantower add-on's file: sync/addon/quantower/ (the Sweep Sync panel) and sync/addon/quantower-plan/ (the Sweep Plan
indicator, Plan Sync, with sync/addon/plan/PlanCore.cs) → compiled → sync/addon/SweepSync-Quantower.zip
   python3 -I tools/addon-quantower.py <folder with Quantower's TradingPlatform.BusinessLayer.dll and TradingPlatform.PresentationLayer.Plugins.dll>
The two libraries come from an installed Quantower (<Quantower>\\TradingPlatform\\v1.x\\bin); they are referenced, never shipped,
never put in the repository. Needs the .NET 10 SDK, as Quantower 1.147 (dotnet; on the Mac: brew install dotnet), and NuGet once
(System.Drawing.Common, compile only, for the indicator's drawing). The build runs in a temporary copy (no bin/ or obj/ in the repository).
The zip holds the two compiled files only, in Quantower's folders: plug-ins/SweepSync/SweepSync.dll (the panel) and
Indicators/SweepPlan/SweepPlan.dll (the plan on the chart); the trader unzips it into <Quantower>\\Settings\\Scripts and restarts
Quantower. Fixed date in the zip: the same build gives the same zip."""
import os, shutil, subprocess, sys, tempfile, zipfile
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(APP, 'sync', 'addon'); OUT = os.path.join(ADDON, 'SweepSync-Quantower.zip')
LIBS = ['TradingPlatform.BusinessLayer.dll', 'TradingPlatform.PresentationLayer.Plugins.dll']
# (source folder, project, built file, place in the zip)
PARTS = [('quantower', 'SweepSync.csproj', 'SweepSync.dll', 'plug-ins/SweepSync/SweepSync.dll'),
         ('quantower-plan', 'SweepPlan.csproj', 'SweepPlan.dll', 'Indicators/SweepPlan/SweepPlan.dll')]

def dotnet():
  for d in [shutil.which('dotnet'), '/opt/homebrew/bin/dotnet', os.path.expanduser('~/.dotnet/dotnet'), '/usr/local/share/dotnet/dotnet']:
    if d and os.path.isfile(d) and os.access(d, os.X_OK): return d
  return None

if len(sys.argv) != 2: sys.exit(__doc__)
BIN = os.path.abspath(os.path.expanduser(sys.argv[1]))
missing = [n for n in LIBS if not os.path.isfile(os.path.join(BIN, n))]
if missing: sys.exit('Missing in %s: %s' % (BIN, ', '.join(missing)))
DN = dotnet()
if not DN: sys.exit('The .NET 10 SDK (dotnet) is not installed.')
tmp = tempfile.mkdtemp(prefix='sweep-qt-')
try:
  for d in ['quantower', 'quantower-plan', 'plan']: shutil.copytree(os.path.join(ADDON, d), os.path.join(tmp, 'src', d), ignore=shutil.ignore_patterns('tests', 'bin', 'obj'))
  env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
  if os.path.realpath(DN).startswith('/opt/homebrew/') and 'DOTNET_ROOT' not in env: env['DOTNET_ROOT'] = '/opt/homebrew/opt/dotnet/libexec'   # Homebrew's .NET
  built = []
  for folder, proj, dll, entry in PARTS:
    out = os.path.join(tmp, 'out-' + folder)
    r = subprocess.run([DN, 'build', os.path.join(tmp, 'src', folder, proj), '-c', 'Release', '-nologo', '-p:QuantowerBin=' + BIN, '-o', out], env=env)
    if r.returncode: sys.exit('Build of %s failed (see above).' % proj)
    if not os.path.isfile(os.path.join(out, dll)): sys.exit('Build gave no %s.' % dll)
    built.append((os.path.join(out, dll), entry))
  part = OUT + '.tmp'
  with zipfile.ZipFile(part, 'w', zipfile.ZIP_DEFLATED) as z:
    for path, entry in built:
      zi = zipfile.ZipInfo(entry, date_time=(2026, 10, 12, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
      z.writestr(zi, open(path, 'rb').read())
  os.replace(part, OUT)
  print('%s (%d bytes): %s' % (os.path.relpath(OUT, APP), os.path.getsize(OUT), ', '.join(e for _, e in built)))
finally:
  shutil.rmtree(tmp, ignore_errors=True)
