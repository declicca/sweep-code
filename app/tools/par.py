"""Full suite split over several copies of the app, run at the same time (~3× faster than tests/run-all.sh alone).
   python3 tools/par.py [shards=3]        (from the app folder; needs tools/ like run.sh)

Shard 1 is the usual copy (/tmp/g, port 8095, /tmp/show_state.json). Shard N is /tmp/g_N on port 8N95 with its own
database and session (/tmp/show_state_N.json). Many tests have 127.0.0.1:8095, /tmp/show_state.json or /tmp/g/ written
in them: these are rewritten in the shard's own copy only (the tests of the repository never change).
Each shard: fresh database, profile + sample data (prof.py), then tests/run-all.sh on its share of the tests.
Shares are balanced on the durations of the previous run (tools/test-times.json, written at the end)."""
import json, os, re, subprocess, sys, time
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); TOOLS = os.path.join(APP, 'tools')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
TIMES = os.path.join(TOOLS, 'test-times.json')
ENV = dict(os.environ, PATH=':'.join([os.path.expanduser('~/.venvs/sweep/bin'), '/opt/homebrew/bin', '/opt/homebrew/opt/coreutils/libexec/gnubin',
                                      '/opt/homebrew/opt/gnu-sed/libexec/gnubin', os.environ.get('PATH', '')]))
# market weekend: the game runs on Friday 15:00 ET (tools/game-now.py), the tests need an open session
GAME_NOW = subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'game-now.py')], capture_output=True, text=True).stdout.strip()
if GAME_NOW: ENV['SWEEP_GAME_NOW'] = GAME_NOW
core = re.search(r'CORE="([^"]*)"', open(os.path.join(APP, 'tests/run-all.sh')).read()).group(1).split()
php_tests = ['presets_test.php', 'shot_trades_test.php']
# durations of the last run (seconds); unknown tests count as 60 s
known = {'e2e_acceptance': 300, 'e2e_realnet': 120, 'e2e_lot_a': 120}
try: known.update(json.load(open(TIMES)))
except (OSError, ValueError): pass
order = sorted(core, key=lambda t: -known.get(t, 60))
shares = [[] for _ in range(N)]; load = [0] * N
for t in order:   # longest first, to the least loaded shard
    i = load.index(min(load)); shares[i].append(t); load[i] += known.get(t, 60)

def shard(i):
    k = i + 1
    dest = '/tmp/g' if k == 1 else '/tmp/g_%d' % k
    port = 8095 if k == 1 else 8000 + k * 100 + 95
    state = '/tmp/show_state.json' if k == 1 else '/tmp/show_state_%d.json' % k
    return dest, port, state

def prepare(i):
    dest, port, state = shard(i)
    subprocess.run(['sh', os.path.join(TOOLS, 'sync.sh'), dest], check=True, env=ENV)
    subprocess.run(['sh', os.path.join(TOOLS, 'fresh.sh')], check=True, env=dict(ENV, DEST=dest))
    tests = os.path.join(dest, 'tests')
    run_all = open(os.path.join(tests, 'run-all.sh')).read()
    run_all = re.sub(r'CORE="[^"]*"', 'CORE="%s"' % ' '.join(shares[i]), run_all)
    if i > 0: run_all = re.sub(r'^php tests/.*$', '', run_all, flags=re.M)   # the PHP tests run once, in shard 1
    # each test timed (copy only): « name seconds » lines next to run-all's log
    a = 'reset_attempts; timeout 900 python3 "tests/$t.py" "$BASE" "$STATE" > "$out" 2>&1; check "$t" $? "$out"'
    assert a in run_all, 'run-all.sh changed: update tools/par.py'
    run_all = run_all.replace(a, 'st=$(date +%s); ' + a + '; echo "$t $(( $(date +%s) - st ))" >> "$log.times"')
    open(os.path.join(tests, 'run-all.sh'), 'w').write(run_all)
    if i > 0:
        for f in os.listdir(tests):
            if not f.endswith('.py'): continue
            p = os.path.join(tests, f); s = open(p, encoding='utf-8').read()
            s2 = s.replace('127.0.0.1:8095', '127.0.0.1:%d' % port).replace('/tmp/show_state.json', state)
            s2 = re.sub(r"/tmp/g(?=[/'\"])", dest, s2)
            if s2 != s: open(p, 'w', encoding='utf-8').write(s2)

def free(port):
    pids = subprocess.run(['lsof', '-ti', 'tcp:%d' % port, '-sTCP:LISTEN'], capture_output=True, text=True).stdout.split()
    for pid in pids: subprocess.run(['kill', pid])
    for _ in range(50):
        if not subprocess.run(['lsof', '-ti', 'tcp:%d' % port, '-sTCP:LISTEN'], capture_output=True, text=True).stdout.strip(): return
        time.sleep(0.1)
    raise SystemExit('port %d still in use' % port)

def stop(srv):   # php -S with workers: the whole process group (the workers are children)
    try: os.killpg(srv.pid, 15)
    except ProcessLookupError: pass
    srv.wait()

def main():
    t0 = time.time()
    if GAME_NOW: print('SWEEP_GAME_NOW=%s (market weekend)' % GAME_NOW, flush=True)
    print('shards:', ' | '.join('%d: %d tests ~%d s' % (i + 1, len(s), load[i]) for i, s in enumerate(shares)), flush=True)
    for i in range(N): prepare(i)
    procs = []
    for i in range(N):
        dest, port, state = shard(i)
        env = dict(ENV, SWEEP_PRESETS_MOCK=dest + '/tests/presets_mock.json', SWEEP_TEST_DB=dest + '/data/journal.db',
                   SWEEP_AI_CONFIG=TOOLS + '/ai-config.local.php', SWEEP_AI_MOCK=dest + '/tests/samples/shot-ai-mock.json',
                   TMPDIR='/tmp/sweep-par-%d' % (i + 1), PHP_CLI_SERVER_WORKERS='4')   # php -S answers one request at a time otherwise
        os.makedirs(env['TMPDIR'], exist_ok=True); [os.remove(os.path.join(env['TMPDIR'], f)) for f in os.listdir(env['TMPDIR'])]
        free(port)   # a server left over by an earlier run would answer instead (without this run's settings)
        srv = subprocess.Popen(['php', '-S', '127.0.0.1:%d' % port, 'router.php'], cwd=dest, env=env, stdout=subprocess.DEVNULL, stderr=open(env['TMPDIR'] + '/php.log', 'w'), start_new_session=True)
        base = 'http://127.0.0.1:%d' % port
        script = ('for i in $(seq 1 50); do curl -s -o /dev/null %s/api/auth/config && break; sleep 0.2; done; '
                  'python3 %s/prof.py %s %s && cd %s && sh tests/run-all.sh %s %s') % (base, TOOLS, base, state, dest, base, state)
        log = open(env['TMPDIR'] + '/run.log', 'w')
        procs.append((i, srv, subprocess.Popen(['sh', '-c', script], env=env, stdout=log, stderr=subprocess.STDOUT), log, env['TMPDIR']))
        time.sleep(8)   # the shards start a few seconds apart (cold browsers, fresh databases)
    rc = 0; passed = failed = 0; failed_names = []
    for i, srv, p, log, tmp in procs:
        p.wait(); stop(srv); log.close()
        out = open(tmp + '/run.log').read()
        m = re.search(r'(\d+) passed, (\d+) failed', out)
        if not m: print('shard %d: no result (see %s/run.log)' % (i + 1, tmp)); rc = 1; continue
        passed += int(m.group(1)); failed += int(m.group(2)); failed_names += re.findall(r'^FAIL\s+(\S+)', out, re.M)
        print('shard %d: %s passed, %s failed' % (i + 1, m.group(1), m.group(2)), flush=True)
    # durations, for the next balance
    times = {}
    for i, srv, p, log, tmp in procs:
        stamp = os.path.join(tmp, 'sweep-run-all.log')
        if os.path.exists(stamp + '.times'):
            for line in open(stamp + '.times'):
                n, s = line.split(); times[n] = round(float(s))
    if times: json.dump(dict(known, **times), open(TIMES, 'w'), indent=1, sort_keys=True)
    print('\n%d passed, %d failed%s   (%d min %02d s)' % (passed, failed, (' — failed: ' + ' '.join(failed_names)) if failed_names else '', (time.time() - t0) // 60, (time.time() - t0) % 60))
    sys.exit(1 if failed or rc else 0)

main()
