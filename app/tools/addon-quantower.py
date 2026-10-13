"""Sweep — the Quantower add-on's file: sync/addon/quantower/ (C# source, project, panel page) → compiled → sync/addon/SweepSync-Quantower.zip
   python3 -I tools/addon-quantower.py <folder with Quantower's TradingPlatform.BusinessLayer.dll and TradingPlatform.PresentationLayer.Plugins.dll>
The two libraries come from an installed Quantower (<Quantower>\\TradingPlatform\\v1.x\\bin); they are referenced, never shipped,
never put in the repository. Needs the .NET 10 SDK, as Quantower 1.147 (dotnet; on the Mac: brew install dotnet). The build runs in a temporary copy (no bin/ or obj/ in the repository).
The zip holds SweepSync/SweepSync.dll only: the trader unzips it into <Quantower>\\Settings\\Scripts\\plug-ins and restarts
Quantower. Fixed date in the zip: the same build gives the same zip."""
import os, shutil, subprocess, sys, tempfile, zipfile
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, 'sync', 'addon', 'quantower'); OUT = os.path.join(APP, 'sync', 'addon', 'SweepSync-Quantower.zip')
LIBS = ['TradingPlatform.BusinessLayer.dll', 'TradingPlatform.PresentationLayer.Plugins.dll']

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
  work = os.path.join(tmp, 'src'); shutil.copytree(SRC, work)
  env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
  if os.path.realpath(DN).startswith('/opt/homebrew/') and 'DOTNET_ROOT' not in env: env['DOTNET_ROOT'] = '/opt/homebrew/opt/dotnet/libexec'   # Homebrew's .NET
  r = subprocess.run([DN, 'build', os.path.join(work, 'SweepSync.csproj'), '-c', 'Release', '-nologo', '-p:QuantowerBin=' + BIN, '-o', os.path.join(tmp, 'out')], env=env)
  if r.returncode: sys.exit('Build failed (see above).')
  dll = os.path.join(tmp, 'out', 'SweepSync.dll')
  if not os.path.isfile(dll): sys.exit('Build gave no SweepSync.dll.')
  part = OUT + '.tmp'
  with zipfile.ZipFile(part, 'w', zipfile.ZIP_DEFLATED) as z:
    zi = zipfile.ZipInfo('SweepSync/SweepSync.dll', date_time=(2026, 10, 12, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
    z.writestr(zi, open(dll, 'rb').read())
  os.replace(part, OUT)
  print('%s (%d bytes)' % (os.path.relpath(OUT, APP), os.path.getsize(OUT)))
finally:
  shutil.rmtree(tmp, ignore_errors=True)
