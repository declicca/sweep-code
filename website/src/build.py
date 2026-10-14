import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from pages1 import page_features
from pages6 import page_home, page_how, page_pricing as page_pricing6
from pages2 import page_faq, page_tradovate, page_install, page_security, page_about, page_contact, page_changelog, page_404
from pages3 import page_ai, page_econ
from pages4 import page_pricing
from pages5 import page_100
from pages7 import page_tools, page_position, page_drawdown, page_consistency
from pages8 import FIRMS, JOURNAL_MOVED
# pages merged into another one (audit n° 3, 1.1): their address redirects there, in the 3 languages
PAGES_MOVED = {"prop-traders": "prop-firm-tracker", "how-to-choose-a-trading-journal": "best-trading-journal-for-prop-firms"}
from pages11 import page_import
from pages7 import page_expectancy, page_roi, page_payoutcalc
import pages12, pages13, pages14, pages17, pages18
import pages9, re as _re
from pages2 import page_changelog as _old_changelog
def page_changelog_new(lang, t):
    body = _old_changelog(lang, t)[2]
    m = _re.search(r'<div class="log">.*?</div>(?=</div></section>)', body, _re.S)
    return pages9.page_changelog(lang, t, older=m.group(0) if m else "")
from legal import page_privacy, page_terms, page_risk
DIST = os.path.join(HERE, "..", "dist")
PAGES = {"index.html":page_home,"features.html":page_features,"ai.html":page_ai,"how-it-works.html":page_how,"economic-calendar.html":page_econ,
 "import.html":page_import,"install.html":page_install,"security.html":page_security,"pricing.html":page_pricing6,"faq.html":page_faq,
 "about.html":page_about,"contact.html":page_contact,"changelog.html":page_changelog_new,"privacy.html":page_privacy,"terms.html":page_terms,"risk.html":page_risk,"404.html":page_404,"100":page_100,"tools.html":page_tools,"position-size-calculator.html":page_position,"trailing-drawdown-calculator.html":page_drawdown,"consistency-rule-calculator.html":page_consistency}
PAGES.update({"expectancy-calculator.html":page_expectancy,"prop-firm-roi-calculator.html":page_roi,"payout-calculator.html":page_payoutcalc,
              "futures-contracts.html":pages12.page_contracts,"release-dates.html":pages13.page_release_hub,"glossary.html":pages13.page_glossary,
              "futures-market-hours.html":pages13.page_hours,"press-kit.html":pages13.page_press,
              "trading-templates.html":pages14.page_templates,"trading-journal-routine.html":pages14.page_routine,
              "best-trading-journal-for-prop-firms.html":pages17.page_best_journal})
for _c in pages12.C: PAGES[pages12.slug(_c[0])] = pages12.make_contract(_c[0])
PAGES["prop-firms/index.html"] = pages18.page_hub
for _s,_n in FIRMS:   # a firm without preloaded rules: its page says which rules to enter
    if _n not in pages18.presets.PRESET_FIRMS: PAGES[_s] = pages18.make_manual_page(_s, _n)
import pages20
PAGES["free-trading-journal.html"] = pages20.page_free
PAGES["prop-firm-tracker.html"] = pages20.page_tracker
PAGES["payout-tracker.html"] = pages20.page_payout_tracker
PAGES[pages18.RULE_CHANGES] = pages18.page_rule_changes
PAGES[pages18.METHOD] = pages18.page_method
PAGES["ninjatrader.html"] = pages20.page_ninjatrader
import pages19
PAGES.update({pages19.HUB: pages19.page_hub, pages19.GUIDE_CONS: pages19.page_consistency, pages19.GUIDE_DD: pages19.page_drawdown_guide, pages19.GUIDE_PAYOUT: pages19.page_payout_guide, pages19.GUIDE_SIZES: pages19.page_sizes_guide, pages19.GUIDE_DAYS: pages19.page_days_guide})
if pages19.COSTS_LIVE: PAGES[pages19.GUIDE_COSTS] = pages19.page_costs_guide
for _c in pages17.VS: PAGES[_c["slug"]] = pages17.make_vs(_c)
for _f in pages18.presets.FIRMS: PAGES[pages18.page_of(_f)] = pages18.make_rules_page(_f)
for _r in pages13.REL: PAGES[_r[1]] = pages13.make_release(_r[0])
PRIO = {"100":"0.8","tools.html":"0.8","position-size-calculator.html":"0.8","trailing-drawdown-calculator.html":"0.8","consistency-rule-calculator.html":"0.8","index.html":"1.0","features.html":"0.9","ai.html":"0.9","how-it-works.html":"0.8","economic-calendar.html":"0.8","pricing.html":"0.8","faq.html":"0.7","sweep-vs-tradezella.html":"0.8","best-trading-journal-for-prop-firms.html":"0.9","free-trading-journal.html":"0.9","prop-firm-tracker.html":"0.9","payout-tracker.html":"0.9","ninjatrader.html":"0.8"}
if os.path.exists(DIST): shutil.rmtree(DIST)
os.makedirs(os.path.join(DIST,"assets","fonts"))
import hashlib, core
for key, src, ext in (("css","styles.css","css"),("js","site.js","js")):
    data = open(os.path.join(HERE,src),"rb").read()
    if ext == "css":   # light minification: comments, whitespace
        import re as _r
        s_ = data.decode("utf-8"); s_ = _r.sub(r"/\*.*?\*/", "", s_, flags=_r.S); s_ = _r.sub(r"\s+", " ", s_)
        s_ = _r.sub(r"\s*([{};,>])\s*", r"\1", s_); s_ = s_.replace(";}", "}"); data = s_.strip().encode("utf-8")
    h = hashlib.md5(data).hexdigest()[:10]
    name = f"{src.split('.')[0]}.{h}.{ext}"; open(os.path.join(DIST,"assets",name),"wb").write(data); core.ASSETS[key] = name
# safety net: old un-versioned files for any stale cached HTML from the first version
for f in ("styles.css","site.js"): shutil.copy(os.path.join(HERE,"..","legacy",f), os.path.join(DIST,"assets",f))
for f in os.listdir(os.path.join(STATIC,"fonts")): shutil.copy(os.path.join(STATIC,"fonts",f), os.path.join(DIST,"assets","fonts",f))
shutil.copytree(os.path.join(STATIC,"img"), os.path.join(DIST,"img"))
for d in ("icons","social","video","press","templates"): shutil.copytree(os.path.join(STATIC,d), os.path.join(DIST,d))
shutil.copy(os.path.join(STATIC,"site.webmanifest"), os.path.join(DIST,"site.webmanifest"))
MAIN = {p: hashlib.sha256() for p in PAGES}   # each page's main content, in the 3 languages: its sitemap date changes only when this does
for lang in LANGS:
    t = lambda d, L=lang: d[L]
    out = DIST if lang == "en" else os.path.join(DIST, lang); os.makedirs(out, exist_ok=True)
    for page, fn in PAGES.items():
        title, desc, body, ld = fn(lang, t)
        dest = os.path.join(out, "100", "index.html") if page == "100" else os.path.join(out, page)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        body = add_related(lang, t, page, body)
        body = add_xlinks(lang, t, page, body)
        body = add_links(lang, page, body)
        body = nbsp(lang, body)
        MAIN[page].update(body.encode("utf-8"))
        open(dest, "w").write(shell(lang, page, title, desc, body, t, ld))
import datetime
BUILD_DATE = datetime.date.today().isoformat()
# sitemap dates: a page's date is the day its main content last changed (fingerprint kept in data/lastmod.json, to commit
# when it changes); a prop firm's rules page keeps the date its rules were last verified
LM_FILE = os.path.join(HERE, "data", "lastmod.json")
try: _lm = json.load(open(LM_FILE, encoding="utf-8"))
except (OSError, ValueError): _lm = {}
LM = {}
for _p, _h in MAIN.items():
    _d = _h.hexdigest()[:16]
    LM[_p] = _lm[_p] if _lm.get(_p, {}).get("hash") == _d else {"hash": _d, "date": BUILD_DATE}
if LM != _lm: json.dump(LM, open(LM_FILE, "w", encoding="utf-8"), indent=1, sort_keys=True); open(LM_FILE, "a").write("\n")
LASTMOD = {p: v["date"] for p, v in LM.items()}
for f in pages18.presets.FIRMS: LASTMOD[pages18.page_of(f)] = pages18.checked_of(f); PRIO.setdefault(pages18.page_of(f), "0.8")
PRIO.setdefault("prop-firms/index.html", "0.8"); PRIO.setdefault(pages18.RULE_CHANGES, "0.8")
for _c in pages17.VS: PRIO.setdefault(_c["slug"], "0.8")
for _g in pages19.RULE_GUIDES: PRIO.setdefault(_g, "0.8")
PRIO.setdefault(pages19.HUB, "0.7")
urls = []
for p in PAGES:
    if p == "404.html": continue
    for l in LANGS:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{a}" href="https://{DOMAIN}{href(a,p)}"/>' for a in LANGS) + f'<xhtml:link rel="alternate" hreflang="x-default" href="https://{DOMAIN}{href("en",p)}"/>'
        urls.append(f'<url><loc>https://{DOMAIN}{href(l,p)}</loc><lastmod>{LASTMOD[p]}</lastmod><priority>{PRIO.get(p,"0.5")}</priority>{alts}</url>')
open(os.path.join(DIST,"sitemap.xml"),"w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(urls) + "</urlset>")
shutil.copy(os.path.join(HERE,"data","robots.txt"), os.path.join(DIST,"robots.txt"))
open(os.path.join(DIST, pages18.RSS.lstrip("/")), "w", encoding="utf-8").write(pages18.rss(DOMAIN))   # rule changes feed
_llms = open(os.path.join(HERE,"data","llms.txt"), encoding="utf-8").read()
_oth = core.other_firms()
open(os.path.join(DIST,"llms.txt"), "w", encoding="utf-8").write(_llms.replace("{PRESET_FIRMS}", core.FIRMS_TXT["en"]).replace("{OTHER_FIRMS}", f" (for example {core.and_list(_oth, 'en').replace(' and ', ' or ')})" if _oth else ""))
open(os.path.join(DIST,".htaccess"),"w").write("""# makeitsweep.com (Apache / cPanel)
Options -Indexes
# Never serve this site from LiteSpeed's server-side page cache (stale pages break the design)
<IfModule LiteSpeed>
CacheLookup off
</IfModule>
DirectoryIndex index.html
ErrorDocument 404 /404.html
AddType font/woff2 .woff2
AddType image/webp .webp
AddType application/manifest+json .webmanifest
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=Cache-Control:no-cache]
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]
RewriteRule ^ https://%1%{REQUEST_URI} [L,R=301]
# folders (/100, /prop-firms): NGINX answers before Apache and adds the trailing slash itself (301, query string kept),
# so these pages are linked as /100/ and /prop-firms/ everywhere (core.href)
# Alpha Futures' rules page was first published at /prop-firms/alpha (the old file stays on the server: deploy.sh never deletes)
RewriteRule ^(fr/|es/)?prop-firms/alpha/?$ /$1prop-firms/alpha-futures [R=301,L]
{JOURNAL_REDIRECTS}
# clean URLs: /pricing.html -> /pricing (301), and /pricing serves pricing.html
RewriteCond %{THE_REQUEST} \\s/+([^?\\s]+?)\\.html[\\s?] [NC]
RewriteCond %1 !(^|/)index$
RewriteRule ^ /%1 [R=301,L,NE]
RewriteCond %{DOCUMENT_ROOT}/$1.html -f
RewriteRule ^(.+?)/?$ /$1.html [L]
# pages renamed with the clean URLs
RedirectMatch 301 ^/(fr/|es/)?contracts/?$ /$1futures-contracts
RedirectMatch 301 ^/(fr/|es/)?templates/?$ /$1trading-templates
RedirectMatch 301 ^/(fr/|es/)?press/?$ /$1press-kit
# old import page moved
RedirectMatch 301 ^/(fr/|es/)?tradovate-import(\\.html)?$ /$1import
# index.html is never a second URL for the same page (avoids duplicate content)
RewriteCond %{THE_REQUEST} \\s/+(.*/)?index\\.html[\\s?] [NC]
RewriteRule ^(.*/)?index\\.html$ /$1 [R=301,L]
</IfModule>
<IfModule mod_headers.c>
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set X-Frame-Options "DENY"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
Header always set Strict-Transport-Security "max-age=31536000"
<FilesMatch "\\.(webp|png|svg|ico|woff2|mp4|webm)$">
Header set Cache-Control "public, max-age=2592000, immutable"
</FilesMatch>
<FilesMatch "\\.[0-9a-f]{10}\\.(css|js)$">
Header set Cache-Control "public, max-age=31536000, immutable"
</FilesMatch>
<FilesMatch "\\.(html|xml|txt|webmanifest)$">
Header set Cache-Control "no-cache, must-revalidate"
</FilesMatch>
<FilesMatch "^$">
Header set Cache-Control "no-cache, must-revalidate"
</FilesMatch>
</IfModule>
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css application/javascript image/svg+xml application/xml text/plain application/manifest+json
</IfModule>
""".replace("{JOURNAL_REDIRECTS}", "\n".join(f"RewriteRule ^(fr/|es/)?{old}(\\.html)?/?$ /$1{new} [R=301,L]" for old, new in {**JOURNAL_MOVED, **PAGES_MOVED}.items())))   # old journal pages → one page per firm; merged pages
n = sum(len(f) for _,_,f in os.walk(DIST)); print("built", n, "files")

# per-language 404 pages, served with a real 404 status
for l in ("fr","es"):
    open(os.path.join(DIST,l,".htaccess"),"w").write(f"ErrorDocument 404 /{l}/404.html\n")
# IndexNow key (Bing, Yandex, Seznam, Naver): proves ownership for instant URL submission
open(os.path.join(DIST,"a7c3e9f14b2d4e6f8a0b1c2d3e4f5a6b.txt"),"w").write("a7c3e9f14b2d4e6f8a0b1c2d3e4f5a6b")

# ---- prune assets no page references (keeps the upload small)
import re as _re2
_refs = set()
for _root, _d, _fs in os.walk(DIST):
    for _f in _fs:
        if _f.endswith((".html", ".css", ".js", ".webmanifest", ".xml")):
            _s = open(os.path.join(_root, _f), encoding="utf-8", errors="ignore").read()
            for _m in _re2.findall(r"/(?:img|video)/[A-Za-z0-9_./@-]+\.(?:webp|png|jpg|mp4|webm|svg)", _s): _refs.add(_m.split("?")[0])
_removed = 0; _bytes = 0
for _sub in ("img", "video"):
    for _root, _d, _fs in os.walk(os.path.join(DIST, _sub)):
        for _f in _fs:
            _p = os.path.join(_root, _f); _rel = "/" + os.path.relpath(_p, DIST).replace(os.sep, "/")
            if _rel not in _refs and not _f.endswith(".txt"):
                _bytes += os.path.getsize(_p); os.remove(_p); _removed += 1
print(f"pruned {_removed} unused files ({_bytes//1024//1024} MB)")
_stale = [pg for pg, d in (list((pages18.page_of(f), pages18.checked_of(f)) for f in pages18.presets.FIRMS)
                           + [(g, pages18.presets.CHECKED) for g in pages19.RULE_GUIDES])
          if (core.OG.get(pg) or {}).get("en", {}).get("date") not in (None, d)]
if _stale: print("share images show an older verification date, run tools/og_images.py:", ", ".join(_stale))
# competitors (audit n° 3, 3.3): details re-checked every month, and no price on a page that data/competitors.json doesn't have
_today = datetime.date.today()
for _n, _c in pages17.COMP.items():
    _age = (_today - datetime.date.fromisoformat(_c["checked"])).days
    if _age > 35: print(f"warning: {_n} details were checked {_age} days ago ({_c['checked']}): read its pages again, then update src/data/competitors.json (prices: with Mateo)")
_SWEEP_PRICES = {0, 19, 39, 159, 329}
_amounts = lambda c: {float(v) for p in c["plans"] for k, v in p.items() if k in ("month", "year", "year_per_month")}
def _prices_named(page):
    s = open(os.path.join(DIST, page), encoding="utf-8").read(); s = s[s.find("<main"):s.find("</main>")]
    return {float(x.replace(",", "")) for x in re.findall(r"\$(\d[\d,]*(?:\.\d+)?)", re.sub(r"<[^>]+>", " ", s))}
import re
for _vs in pages17.VS:
    _odd = _prices_named(_vs["slug"]) - _SWEEP_PRICES - _amounts(pages17.COMP[_vs["name"]])
    if _odd: print(f"warning: {_vs['slug']} names prices that aren't in src/data/competitors.json: {sorted(_odd)}")
_odd = _prices_named("best-trading-journal-for-prop-firms.html") - _SWEEP_PRICES - set().union(*(_amounts(c) for c in pages17.COMP.values()))
if _odd: print(f"warning: best-trading-journal-for-prop-firms.html names prices that aren't in src/data/competitors.json: {sorted(_odd)}")
