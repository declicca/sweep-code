"""Prop firm rules for the website. One source of truth: the app's catalogue (checked every week), never retyped here.

At each build:
  - read https://app.makeitsweep.com/api/presets (the catalogue the app serves);
  - keep a copy in data/presets.json, so a build without network uses the last one;
  - log every rule that changed since that copy in data/presets-changes.json (newest first), for the « changes » history.
Without network and without a copy, the app's shipped catalogue (app/presets/seed.json) is used.
SWEEP_PRESETS_OFFLINE=1 skips the network (tests, offline builds).
"""
import datetime, json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://app.makeitsweep.com/api/presets"
SNAP = os.path.join(HERE, "data", "presets.json")
LOG = os.path.join(HERE, "data", "presets-changes.json")
SEED = os.path.join(HERE, "..", "..", "app", "presets", "seed.json")

def _read(path):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError): return None

def _write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
    os.replace(tmp, path)

def _valid(cat):
    return isinstance(cat, dict) and isinstance(cat.get("firms"), list) and all(isinstance(f, dict) and f.get("id") for f in cat["firms"])

def _fetch():
    if os.environ.get("SWEEP_PRESETS_OFFLINE"): return None
    try:
        req = urllib.request.Request(API, headers={"User-Agent": "SweepSiteBuild/1", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r: cat = json.loads(r.read().decode("utf-8"))
        return cat if _valid(cat) else None
    except Exception as e:
        print("presets: app catalogue not reachable (" + type(e).__name__ + "), using the last copy")
        return None

def _leaves(cat):
    """Every rule value, keyed by (firm, program, size, path): what the change log compares."""
    out = {}
    def walk(node, key, path):
        if isinstance(node, dict):
            for k, v in node.items(): walk(v, key, path + (k,))
        else:
            out[key + (".".join(path),)] = node
    for f in cat.get("firms", []):
        for p in f.get("programs", []):
            for s in p.get("sizes", []):
                walk({k: v for k, v in s.items() if k != "size"}, (f["id"], p.get("id", p.get("name")), s.get("size")), ())
    return out

def _changes(old, new, date):
    a, b = _leaves(old), _leaves(new)
    rows = []
    for k in sorted(set(a) | set(b), key=lambda k: tuple(str(x) for x in k)):
        if a.get(k) != b.get(k):
            rows.append({"date": date, "firm": k[0], "program": k[1], "size": k[2], "rule": k[3], "old": a.get(k), "new": b.get(k)})
    return rows

def _load():
    live, snap = _fetch(), _read(SNAP)
    if live is None:
        cat = snap if _valid(snap) else _read(SEED)
        src = "copy" if _valid(snap) else "app seed"
    else:
        cat, src = live, "app"
        if snap != live:
            if _valid(snap):
                # the date of the check that produced the new rules; today when the catalogue changed without a new check
                new_check = (live.get("checked_at") or "")[:10]
                date = new_check if new_check and new_check != (snap.get("checked_at") or "")[:10] else datetime.date.today().isoformat()
                rows = _changes(snap, live, date)
                if rows: _write(LOG, rows + (_read(LOG) or []))
                print(f"presets: {len(rows)} rule change(s) logged")
            _write(SNAP, live)
    if not _valid(cat): raise SystemExit("presets: no prop firm catalogue (app API, data/presets.json and app/presets/seed.json all unusable)")
    print(f"presets: {src}, version {cat.get('version')}, checked {(cat.get('checked_at') or '')[:10]}, origin {cat.get('origin')}")
    return cat

CATALOGUE = _load()
CHANGES = _read(LOG) or []
CHECKED = (CATALOGUE.get("checked_at") or "")[:10]
FIRMS = [f for f in CATALOGUE["firms"] if f.get("programs")]
PRESET_FIRMS = {f["name"] for f in FIRMS}
