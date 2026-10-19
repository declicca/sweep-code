#!/usr/bin/env python3
"""Checks of makeitsweep.com on the local build (website/dist). Development tool only: nothing here runs on the server.

  qa.py quick [pages…]  the pages changed since the last deploy (or the pages given), phone 390 and computer 1300,
                        light and dark, then the SEO of every page: for a small change (about a minute)
  qa.py full            every page at 360, 390, 768, 1024, 1440 and 1920 px, light and dark
  qa.py seo             titles, descriptions, canonicals, hreflang, sitemap, structured data, links, utm
  qa.py func            menus, phone menu, size switch, tour, language and consent banners, calculators
  qa.py kbd             keyboard: skip link, menus, focus rings, phone menu
  qa.py all             full + seo + func + kbd: before a big delivery
  qa.py mark-deployed   remember the build just deployed (deploy.sh runs it after a real deploy): quick compares with it

It builds first (offline catalogue) unless --no-build. Every layout issue is checked again, alone and slowly, before it is
reported: the fast pass flags blocks still animating. Exit code 1 when an issue remains.

Setup, once:  python3.13 -m venv website/tools/qa/.venv && website/tools/qa/.venv/bin/pip install playwright
              (it drives the installed Google Chrome: no browser to download)
Run:          website/tools/qa/.venv/bin/python website/tools/qa/qa.py quick"""
import asyncio, datetime, functools, hashlib, html, http.server, json, os, re, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.normpath(os.path.join(HERE, "..", ".."))
DIST, SRC = os.path.join(WEB, "dist"), os.path.join(WEB, "src")
MANIFEST = os.path.join(HERE, ".deployed.json")
DOM = "https://makeitsweep.com"
QUICK = ((390, "phone"), (1300, "computer"))
FULL = ((360, ""), (390, ""), (768, ""), (1024, ""), (1440, ""), (1920, ""))
SCHEMES = (("light", "clair"), ("dark", "sombre"))
# when the shared CSS or JS changed, or too many pages to test one by one: one page of each kind, in the 3 languages
SAMPLE = ["/", "/features", "/how-it-works", "/ai", "/pricing", "/import", "/import-tradovate", "/prop-firms/", "/prop-firms/topstep",
          "/prop-firms/topstep-vs-apex", "/prop-firms/tradeify", "/sweep-vs-tradezella", "/best-trading-journal-for-prop-firms",
          "/free-trading-journal", "/prop-firm-tracker", "/guides", "/prop-firm-drawdown-rules", "/tools", "/trailing-drawdown-calculator",
          "/futures-contracts", "/contracts/nq-futures", "/release-dates", "/cpi-release-dates", "/economic-calendar", "/futures-market-hours",
          "/glossary", "/faq", "/about", "/contact", "/press-kit", "/privacy", "/changelog", "/ninjatrader", "/trading-journal-guide",
          "/trading-templates", "/100/"]
MAX_ONE_BY_ONE = 60

# ---------------------------------------------------------------- the build, its pages, what changed since the last deploy
def build():
    t0 = time.time()
    r = subprocess.run([sys.executable, "build.py"], cwd=SRC, env={**os.environ, "SWEEP_PRESETS_OFFLINE": "1"}, capture_output=True, text=True)
    warn = [l for l in (r.stdout + r.stderr).splitlines() if re.search(r"warning|error|traceback", l, re.I)]
    if r.returncode:
        print("Build en échec :\n" + "\n".join((r.stdout + r.stderr).splitlines()[-15:])); sys.exit(2)
    print(f"Build : {time.time() - t0:.0f} s" + ("".join(f"\n  {w}" for w in warn) if warn else ""))

def url_of(rel):
    u = "/" + rel[:-5]
    return u[:-5] if u.endswith("/index") else u   # fr/index.html → /fr/, index.html → /

def pages():
    return sorted(url_of(os.path.relpath(os.path.join(r, f), DIST)) for r, _, fs in os.walk(DIST) for f in fs if f.endswith(".html") and f != "404.html")

def file_of(u):
    return os.path.join(DIST, (u.lstrip("/") + "index.html") if u.endswith("/") else u.lstrip("/") + ".html")

def signatures():
    """{page: hash} (asset names without their content hash, so a CSS change alone doesn't flag every page), {asset: hash}."""
    norm = lambda s: re.sub(r"(/assets/[\w-]+)\.[0-9a-f]{6,}(\.\w+)", r"\1\2", s)
    ps = {u: hashlib.sha256(norm(open(file_of(u), encoding="utf-8").read()).encode()).hexdigest()[:16] for u in pages()}
    ad = os.path.join(DIST, "assets")
    assets = {re.sub(r"\.[0-9a-f]{6,}(?=\.\w+$)", "", f): hashlib.sha256(open(os.path.join(ad, f), "rb").read()).hexdigest()[:16]
              for f in sorted(os.listdir(ad)) if f.endswith((".css", ".js"))} if os.path.isdir(ad) else {}
    return ps, assets

def mark_deployed():
    ps, assets = signatures()
    json.dump({"at": datetime.datetime.now().isoformat(timespec="seconds"), "pages": ps, "assets": assets}, open(MANIFEST, "w"), indent=0, sort_keys=True)
    print(f"qa : build déployé mémorisé ({len(ps)} pages)")

def quick_targets(given):
    have = set(pages())
    if given:
        norm = lambda p: "/" + p.strip("/") + ("/" if p.endswith("/") and p.strip("/") else "") if p.strip("/") else "/"
        out = [norm(p) for p in given]
        miss = [p for p in out if p not in have]
        if miss: print("Pages inconnues :", ", ".join(miss)); sys.exit(2)
        return out, f"{len(out)} page(s) demandée(s)"
    sample = sorted({x for p in SAMPLE for x in (p, "/fr" + p, "/es" + p) if x in have})
    if not os.path.exists(MANIFEST):
        return sample, "pas de déploiement mémorisé : une page de chaque sorte, en 3 langues"
    old = json.load(open(MANIFEST)); ps, assets = signatures()
    changed = sorted(u for u in ps if old["pages"].get(u) != ps[u])
    shared = [a for a in assets if old.get("assets", {}).get(a) != assets[a]]
    if not changed and not shared:
        return [], f"rien n'a changé depuis le déploiement du {old['at'][:16].replace('T', ' à ')}"
    if len(changed) > MAX_ONE_BY_ONE:
        return sample, f"{len(changed)} pages changées : une page de chaque sorte, en 3 langues"
    why = f"{len(changed)} page(s) changée(s)" + (f", plus une page de chaque sorte (CSS ou JS commun changé : {', '.join(shared)})" if shared else "")
    return sorted(set(changed) | (set(sample) if shared else set())), why

# ---------------------------------------------------------------- a local server for dist
def serve():
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def handle(self):
            try: super().handle()
            except (BrokenPipeError, ConnectionResetError): pass
        def send_head(self):
            p = self.path.split("?")[0].split("#")[0]; f = self.translate_path(p)
            if not os.path.exists(f) and os.path.exists(f + ".html"): self.path = p + ".html"
            return super().send_head()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=DIST))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"

# ---------------------------------------------------------------- layout: errors, 404s, overflow, text out of its box, hidden blocks, broken images
KNOWN = ("sweep-count.php", "cohort-count", "hero-loop", "Failed to load resource: net::ERR_FAILED")
isknown = lambda x: any(k in x for k in KNOWN) or (x.startswith("failed ") and x.endswith(".mp4"))   # local server: no CORS from the app; a video cut by the next page
CHECK = """async (wait) => {
 const sleep = ms => new Promise(r => setTimeout(r, ms));
 for (let y = 0; y < document.documentElement.scrollHeight; y += Math.round(innerHeight * .6)) { scrollTo(0, y); await sleep(45); }
 scrollTo(0, document.documentElement.scrollHeight); await sleep(wait);
 // a phone widens its layout to fit what overflows (innerWidth grows with it): measure against the screen, not the layout
 const o = {overflow: Math.max(document.documentElement.scrollWidth, innerWidth) - screen.width, text: [], hidden: [], broken: [], deformed: []};
 const name = e => e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\\s+/).slice(0, 2).join('.') : '') + ' «' + (e.textContent || '').trim().slice(0, 30) + '»';
 const shown = e => { if (!e.offsetParent && getComputedStyle(e).position !== 'fixed') return false; if (e.closest('[hidden],dialog:not([open]),details:not([open]) > :not(summary),.sheet:not(.open)')) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
 const R = document.createRange();
 for (const e of document.querySelectorAll('.btn, button, .plan, .plat, .chip, .tag, .seg button, .ddmenu a, .subnav a, .cmp td, .cmp th, .card')) {
   if (!shown(e)) continue; const b = e.getBoundingClientRect(); let worst = 0;
   const tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
   for (let n = tw.nextNode(); n; n = tw.nextNode()) {
     if (!n.textContent.trim()) continue; let p = n.parentElement, skip = false;
     for (; p && p !== e; p = p.parentElement) { const ps = getComputedStyle(p); if (/(auto|scroll)/.test(ps.overflowX) || ps.position === 'absolute' || ps.position === 'fixed') { skip = true; break; } }
     if (skip) continue; R.selectNodeContents(n);
     for (const r of R.getClientRects()) worst = Math.max(worst, r.right - b.right, b.left - r.left);
   }
   if (worst > 1.5) o.text.push(name(e) + ' +' + Math.round(worst) + 'px');
 }
 for (const e of document.querySelectorAll('.reveal, .stagger > *, .rise, .io .head, .wu')) { if (shown(e) && parseFloat(getComputedStyle(e).opacity) < .1) o.hidden.push(name(e)); }
 for (const i of document.querySelectorAll('img')) {
   if (!shown(i)) continue;
   if (i.complete && i.naturalWidth === 0) { o.broken.push(i.currentSrc || i.src); continue; }
   const fit = getComputedStyle(i).objectFit; if (!i.naturalWidth || fit === 'cover' || fit === 'contain') continue;
   const r = i.getBoundingClientRect(), a = r.width / r.height, n = i.naturalWidth / i.naturalHeight;
   if (r.width > 8 && Math.abs(a - n) / n > .03) o.deformed.push((i.currentSrc || i.src).split('/').slice(-2).join('/') + ` ${a.toFixed(2)} vs ${n.toFixed(2)}`);
 }
 o.text = [...new Set(o.text)].slice(0, 6); o.hidden = [...new Set(o.hidden)].slice(0, 6);
 return o; }"""

async def layout_pass(br, base, urls, width, scheme, slow=False):
    """[(url, message)] for these pages at this width and colour scheme; and how many pages showed only the known local noise."""
    mob = width < 1024
    ctx = await br.new_context(viewport={"width": width, "height": 844 if width < 768 else 850}, has_touch=mob, is_mobile=width < 768,
                               locale="fr-CA", color_scheme=scheme)
    issues, known = [], 0; sem = asyncio.Semaphore(2 if slow else 6)
    async def one(u):
        nonlocal known
        async with sem:
            pg = await ctx.new_page(); errs, bad = [], []
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:140]))
            pg.on("pageerror", lambda e: errs.append("JS " + str(e)[:140]))
            pg.on("response", lambda r: r.status >= 400 and r.url.startswith(base) and bad.append(f"{r.status} {r.url[len(base):]}"))
            pg.on("requestfailed", lambda r: r.url.startswith(base) and bad.append(f"failed {r.url[len(base):]}"))
            try:
                await pg.goto(base + u, wait_until="load", timeout=45000); await pg.wait_for_timeout(250)
                c = await pg.evaluate(CHECK, 4500 if slow else 2200)
            except Exception as e:
                issues.append((u, f"chargement : {str(e)[:160]}")); await pg.close(); return
            known += bool([x for x in errs + bad if isknown(x)])
            errs = [x for x in errs if not isknown(x)]; bad = [x for x in bad if not isknown(x)]
            for cond, msg in ((errs, f"erreur de script {errs[:3]}"), (bad, f"ressource brisée {bad[:3]}"), (c["overflow"] > 1, f"débordement de {c['overflow']} px"),
                              (c["text"], f"texte qui dépasse {c['text']}"), (c["hidden"], f"bloc pas affiché {c['hidden']}"),
                              (c["broken"], f"image brisée {c['broken'][:3]}"), (c["deformed"], f"image déformée {c['deformed'][:3]}")):
                if cond: issues.append((u, msg))
            await pg.close()
    await asyncio.gather(*(one(u) for u in urls)); await ctx.close()
    return issues, known

async def layout(urls, widths):
    """Every width × light and dark; then each page with an issue again, alone and slowly: only what remains is reported."""
    from playwright.async_api import async_playwright
    base = serve(); left = 0
    async with async_playwright() as p:
        br = await p.chromium.launch(channel="chrome")
        for scheme, label in SCHEMES:
            for w, kind in widths:
                issues, known = await layout_pass(br, base, urls, w, scheme)
                flagged = sorted({u for u, _ in issues}); again = []
                if flagged: again, _ = await layout_pass(br, base, flagged, w, scheme, slow=True)
                left += len(again)
                note = f" ({len(flagged)} signalée(s) au premier passage, revérifiée(s) lentement)" if flagged else ""
                print(f"== {w} px{' ' + kind if kind else ''}, {label} : {len(urls)} pages, {len(again)} problème(s){note}", flush=True)
                for u, m in sorted(again): print(f"   {u} : {m}", flush=True)
        await br.close()
    return left

# ---------------------------------------------------------------- SEO, read from the files
def seo():
    D = DIST; files = sorted(os.path.relpath(os.path.join(r, f), D) for r, _, fs in os.walk(D) for f in fs if f.endswith(".html") and f != "404.html")
    sm = set(re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(D, "sitemap.xml")).read()))
    ht = open(os.path.join(D, ".htaccess")).read()
    olds = [re.compile(m) for m in re.findall(r"RewriteRule \^\(fr/\|es/\)\?([^\s]+?)\s", ht) + re.findall(r"RedirectMatch 301 \^/\(fr/\|es/\)\?([^\s]+?)\s", ht)]
    txt = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()
    bad = []
    for rel in files:
        s = open(os.path.join(D, rel), encoding="utf-8").read(); u = url_of(rel); head = s[:s.find("</head>")]
        err = lambda m: bad.append((u, m))
        t = re.search(r"<title>(.*?)</title>", s, re.S); d = re.search(r'<meta name="description" content="([^"]*)"', s)
        if not t or len(html.unescape(t.group(1))) > 60: err(f"title {len(html.unescape(t.group(1))) if t else 'absent'} car.")
        if not d or not 120 <= len(html.unescape(d.group(1))) <= 158: err(f"description {len(html.unescape(d.group(1))) if d else 'absente'} car.")
        if len(re.findall(r"<h1[\s>]", s)) != 1: err(f"{len(re.findall(r'<h1[\\s>]', s))} H1")
        can = re.findall(r'<link rel="canonical" href="([^"]+)"', head)
        if len(can) != 1: err(f"{len(can)} canonique(s)")
        alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', head)
        if sorted(h for h, _ in alts) != ["en", "es", "fr", "x-default"]: err(f"hreflang {sorted(h for h, _ in alts)}")
        elif can and can[0] not in [h for _, h in alts]: err("canonique absente des hreflang")
        if len(re.findall(r'<meta property="og:locale:alternate"', head)) != 2: err("og:locale:alternate ≠ 2")
        if can and can[0] not in sm: err(f"canonique absente du sitemap {can[0]}")
        vis_q = [txt(q) for q in re.findall(r'<summary>(.*?)<span class="plus"', s, re.S)]
        crumbs = re.search(r'<nav class="crumbs".*?</nav>', s, re.S)
        vis_c = [txt(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", crumbs.group(0), re.S)] if crumbs else []
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try: j = json.loads(blk)
            except Exception as e: err(f"JSON-LD invalide : {e}"); continue
            for n in (j.get("@graph", [j]) if isinstance(j, dict) else j):
                ty = n.get("@type")
                if ty == "FAQPage":
                    ld_q = [txt(q["name"]) for q in n.get("mainEntity", [])]
                    if ld_q != vis_q[:len(ld_q)] and sorted(ld_q) != sorted(vis_q): err(f"FAQPage ≠ questions visibles ({len(ld_q)} / {len(vis_q)})")
                elif ty == "VideoObject":
                    miss = [k for k in ("name", "description", "thumbnailUrl", "uploadDate", "duration", "contentUrl") if not n.get(k)]
                    if miss: err(f"VideoObject sans {miss}")
                elif ty == "ItemList":
                    if not n.get("itemListElement") or any(not i.get("position") or not (i.get("name") or i.get("url") or i.get("item")) for i in n["itemListElement"]): err("ItemList incomplète")
                elif ty == "BreadcrumbList":
                    ld_c = [txt(i["name"]) for i in n.get("itemListElement", [])]
                    if ld_c != vis_c: err(f"BreadcrumbList {ld_c} ≠ fil visible {vis_c}")
        if crumbs and "BreadcrumbList" not in s: err("fil d'Ariane sans BreadcrumbList")
        for h in re.findall(r'href="(/[^"#?]*)', s):
            p = re.sub(r"^(fr|es)/", "", h.lstrip("/"))
            if p.endswith(".html") or any(o.fullmatch(p) or o.fullmatch(p + "/") for o in olds): err(f"lien vers une adresse qui redirige {h}")
        for h in re.findall(r'href="(https://app\.makeitsweep\.com/\?signup[^"]*)"', s):
            if not all(k in html.unescape(h) for k in ("utm_source=", "utm_medium=", "utm_campaign=")): err("lien d'inscription sans utm")
    for loc in sm:
        p = re.sub(r"^https://makeitsweep\.com/(fr/|es/)?", "", loc)
        if any(o.fullmatch(p) or o.fullmatch(p + "/") for o in olds): bad.append((loc, "adresse qui redirige dans le sitemap"))
    missing = [url_of(r) for r in files if DOM + url_of(r) not in sm]
    for m in missing: bad.append((m, "absente du sitemap"))
    print(f"== SEO : {len(files)} pages, sitemap de {len(sm)} adresses, {len(bad)} problème(s)")
    for u, m in sorted(set(bad))[:60]: print(f"   {u} : {m}")
    return len(bad)

# ---------------------------------------------------------------- main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in ("quick", "full", "seo", "func", "kbd", "all", "mark-deployed"): print(__doc__); sys.exit(2)
    cmd, rest = args[0], args[1:]
    if cmd == "mark-deployed": return mark_deployed()
    t0 = time.time()
    if "--no-build" not in sys.argv: build()
    left = 0
    if cmd == "quick":
        urls, why = quick_targets(rest); print(f"Pages testées : {why}")
        if urls:
            if len(urls) <= 12: print("  " + " ".join(urls))
            left += asyncio.run(layout(urls, QUICK))
        left += seo()
    if cmd in ("full", "all"): left += asyncio.run(layout(pages(), FULL))
    if cmd in ("seo", "all"): left += seo()
    if cmd in ("func", "all"):
        import checks_func; left += asyncio.run(checks_func.run(serve(), DIST))
    if cmd in ("kbd", "all"):
        import checks_kbd; left += asyncio.run(checks_kbd.run(DIST))
    print(f"\n{'Tout est bon' if not left else f'{left} problème(s) à voir'} · {time.time() - t0:.0f} s")
    sys.exit(1 if left else 0)

if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
