import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from pages1 import page_features
from pages6 import page_home, page_how, page_pricing as page_pricing6
from pages2 import page_faq, page_install, page_security, page_about, page_contact, page_changelog, page_404
from pages3 import page_ai, page_econ
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
              "trading-templates.html":pages14.page_templates,"trading-journal-routine.html":pages14.page_routine,"trading-journal-guide.html":pages14.page_journal_guide,
              "best-trading-journal-for-prop-firms.html":pages17.page_best_journal})
for _c in pages12.C: PAGES[pages12.slug(_c[0])] = pages12.make_contract(_c[0])
PAGES["prop-firms/index.html"] = pages18.page_hub
for _s,_n in FIRMS:   # a firm without preloaded rules: its page says which rules to enter
    if _n not in pages18.presets.PRESET_FIRMS: PAGES[_s] = pages18.make_manual_page(_s, _n)
import pages20
PAGES["free-trading-journal.html"] = pages20.page_free
import pages11
PAGES.update(pages11.EXPORT_PAGES)   # export guides: Tradovate, TopstepX, Rithmic
PAGES["prop-firm-tracker.html"] = pages20.page_tracker
PAGES["payout-tracker.html"] = pages20.page_payout_tracker
PAGES[pages18.RULE_CHANGES] = pages18.page_rule_changes
PAGES[pages18.METHOD] = pages18.page_method
PAGES["ninjatrader.html"] = pages20.page_ninjatrader
PAGES["quantower.html"] = pages20.page_quantower
import pages21   # the 90-day gameplan: a pillar page and one page per month
PAGES[pages21.GP_HUB] = pages21.page_gp_hub
PAGES[pages21.GP_MONTHS[0]] = pages21.page_gp_month1
PAGES[pages21.GP_MONTHS[1]] = pages21.page_gp_month2
PAGES[pages21.GP_MONTHS[2]] = pages21.page_gp_month3
import pages19
PAGES.update({pages19.HUB: pages19.page_hub, pages19.GUIDE_CONS: pages19.page_consistency, pages19.GUIDE_DD: pages19.page_drawdown_guide, pages19.GUIDE_PAYOUT: pages19.page_payout_guide, pages19.GUIDE_SIZES: pages19.page_sizes_guide, pages19.GUIDE_DAYS: pages19.page_days_guide})
if pages19.COSTS_LIVE: PAGES[pages19.GUIDE_COSTS] = pages19.page_costs_guide
for _c in pages17.VS: PAGES[_c["slug"]] = pages17.make_vs(_c)
for _f in pages18.presets.FIRMS: PAGES[pages18.page_of(_f)] = pages18.make_rules_page(_f)
PAGES.update(pages19.VS_PAGES)   # firm vs firm
for _r in pages13.REL: PAGES[_r[1]] = pages13.make_release(_r[0])
PRIO = {"100":"0.8","tools.html":"0.8","position-size-calculator.html":"0.8","trailing-drawdown-calculator.html":"0.8","consistency-rule-calculator.html":"0.8","index.html":"1.0","features.html":"0.9","ai.html":"0.9","how-it-works.html":"0.8","economic-calendar.html":"0.8","pricing.html":"0.8","faq.html":"0.7","sweep-vs-tradezella.html":"0.8","best-trading-journal-for-prop-firms.html":"0.9","free-trading-journal.html":"0.9","prop-firm-tracker.html":"0.9","payout-tracker.html":"0.9","ninjatrader.html":"0.8","quantower.html":"0.8","how-to-start-prop-firm-trading.html":"0.9","prop-firm-gameplan-month-1.html":"0.8","prop-firm-gameplan-month-2.html":"0.8","prop-firm-gameplan-month-3.html":"0.8"}
if os.path.exists(DIST): shutil.rmtree(DIST)
os.makedirs(os.path.join(DIST,"assets","fonts"))
import hashlib, core
import re as _r
def css_min(s_):   # light minification: comments, whitespace
    s_ = _r.sub(r"/\*.*?\*/", "", s_, flags=_r.S); s_ = _r.sub(r"\s+", " ", s_)
    return _r.sub(r"\s*([{};,>])\s*", r"\1", s_).replace(";}", "}").strip()
def page_css(css):
    """The sections of system.css headed /* ---- [pages: a.html b.html] … */ leave the shared sheet:
    each page listed gets them inline (core.PAGE_CSS), in the same cascade layer."""
    parts = _r.split(r"(/\* -{4} .*?\*/|/\* =+ .*?\*/)", css, flags=_r.S)
    out, per, layer = [parts[0]], {}, None
    for h, body in [(parts[0], "")] + list(zip(parts[1::2], parts[2::2])):
        m = _r.match(r"/\* -{4} \[pages: ([^\]]+)\]", h)
        if m:
            depth, cut = 0, len(body)
            for i, ch in enumerate(body):   # the section ends before its layer's closing brace
                depth += (ch == "{") - (ch == "}")
                if depth < 0: cut = i; break
            for pg in m.group(1).split():
                if pg not in PAGES or pg not in SYSTEM_PAGES: raise SystemExit(f"system.css: [pages: {pg}] is not a page on the design system")
                per.setdefault(pg, {}).setdefault(layer, []).append(body[:cut])
            out.append(body[cut:])
        elif body: out += [h, body]
        for l in _r.findall(r"@layer (\w+)\{", h + body): layer = l
    return "".join(out), {pg: css_min("".join(f"@layer {l}{{{''.join(b)}}}" for l, b in ls.items())) for pg, ls in per.items()}
missing = [p for p in PAGES if p not in SYSTEM_PAGES]   # every page is built with ui.py and loads system.css (styles.css is gone, October 2026)
if missing: raise SystemExit(f"not on the design system: {missing}")
for key, src, ext in (("js","site.js","js"),("system","system.css","css")):
    data = open(os.path.join(HERE,src),"rb").read()
    if key == "system":
        s_, core.PAGE_CSS = page_css(data.decode("utf-8")); data = s_.encode("utf-8")
    if ext == "css": data = css_min(data.decode("utf-8")).encode("utf-8")
    h = hashlib.md5(data).hexdigest()[:10]
    name = f"{src.split('.')[0]}.{h}.{ext}"; open(os.path.join(DIST,"assets",name),"wb").write(data); core.ASSETS[key] = name
# safety net: old un-versioned files for any stale cached HTML from the first version
for f in ("styles.css","site.js"): shutil.copy(os.path.join(HERE,"..","legacy",f), os.path.join(DIST,"assets",f))
for f in os.listdir(os.path.join(STATIC,"fonts")): shutil.copy(os.path.join(STATIC,"fonts",f), os.path.join(DIST,"assets","fonts",f))
shutil.copytree(os.path.join(STATIC,"img"), os.path.join(DIST,"img"))
for d in ("icons","social","video","press","templates"): shutil.copytree(os.path.join(STATIC,d), os.path.join(DIST,d))
shutil.copy(os.path.join(STATIC,"site.webmanifest"), os.path.join(DIST,"site.webmanifest"))
def _text(body):
    """A page's visible text, without tags, scripts or styles: what its sitemap date follows."""
    return _re.sub(r"\s+", " ", _re.sub(r"<[^>]+>", " ", _re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", body, flags=_re.S))).strip()
MAIN = {p: hashlib.sha256() for p in PAGES}
EN_META = {}   # each page's English title and description, for llms.txt   # each page's main content, in the 3 languages: its sitemap date changes only when this does
import html as _html_b
def heading_levels(body):
    """No jump from the h1 to an h3: cards placed before the page's first h2 get h2 titles that keep the h3 look."""
    i = body.find("<h2")
    head, tail = (body, "") if i < 0 else (body[:i], body[i:])
    def h2(m):
        a = m.group(1) or ""
        a = a.replace('class="', 'class="h3 ', 1) if 'class="' in a else ' class="h3"' + a
        return f"<h2{a}>{m.group(2)}</h2>"
    return _re.sub(r"<h3(\s[^>]*)?>(.*?)</h3>", h2, head, flags=_re.S) + tail
def table_names(body):
    """A table is named after the heading before it, and the row headers of key/value tables say they are."""
    out, last = [], 0
    for m in _re.finditer(r"<table\b[^>]*>", body):
        tag = m.group(0)
        if "aria-label" not in tag and "<caption" not in body[m.end():m.end() + 120]:
            hs = list(_re.finditer(r"<h([1-4])\b[^>]*>(.*?)</h\1>", body[:m.start()], _re.S))
            name = _re.sub(r"\s+", " ", _re.sub(r"<[^>]+>", " ", hs[-1].group(2))).strip() if hs else ""
            if name: tag = tag[:-1] + f' aria-label="{_html_b.escape(name)}">'
        out.append(body[last:m.start()] + tag); last = m.end()
    body = "".join(out) + body[last:]
    return _re.sub(r"<tbody\b[^>]*>.*?</tbody>", lambda m: _re.sub(r"<tr([^>]*)><th>", r'<tr\1><th scope="row">', m.group(0)), body, flags=_re.S)

for lang in LANGS:
    t = lambda d, L=lang: d[L]
    out = DIST if lang == "en" else os.path.join(DIST, lang); os.makedirs(out, exist_ok=True)
    for page, fn in PAGES.items():
        title, desc, body, ld = fn(lang, t)
        if lang == "en": EN_META[page] = (title, desc)
        dest = os.path.join(out, "100", "index.html") if page == "100" else os.path.join(out, page)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        body = add_related(lang, t, page, body)
        body = add_xlinks(lang, t, page, body)
        body = add_links(lang, page, body)
        body = table_names(heading_levels(body))
        body = nbsp(lang, body)
        MAIN[page].update(_text(body).encode("utf-8"))   # the visible text: a markup or style change keeps the page's date
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
_llms = _llms.replace("{PRESET_FIRMS}", core.FIRMS_TXT["en"]).replace("{OTHER_FIRMS}", f" (for example {core.and_list(_oth, 'en').replace(' and ', ' or ')})" if _oth else "")
# every English page is listed: the hand-written sections first, then the ones they don't name; dated, with the French and Spanish entry points
_named = set(_re.findall(r"\(https://makeitsweep\.com(/[^)\s]*)\)", _llms))
_more = [p for p in PAGES if p not in ("404.html",) and href("en", p) not in _named and p in EN_META]
_line = lambda p: f"- [{_re.sub(r'\s*[·—|]\s*Sweep$', '', EN_META[p][0])}](https://{DOMAIN}{href('en', p)}): {EN_META[p][1]}"
_llms = _llms.replace("\n## Company", ("\n## More pages\n" + "\n".join(_line(p) for p in sorted(_more, key=lambda p: href("en", p))) + "\n" if _more else "")
                      + "\n## Languages\n- [Français](https://makeitsweep.com/fr/)\n- [Español](https://makeitsweep.com/es/)\n\n## Company", 1)
_llms = _llms.replace("\n\nSweep is made by", f"\n\nLast updated: {max(LASTMOD.values())}\n\nSweep is made by", 1)
open(os.path.join(DIST,"llms.txt"), "w", encoding="utf-8").write(_llms)
# an Article's structured data gets the page's sitemap date, its share image and the organization as author
for _l in LANGS:
    for _p in PAGES:
        _f = os.path.join(DIST if _l == "en" else os.path.join(DIST, _l), "100", "index.html") if _p == "100" else os.path.join(DIST if _l == "en" else os.path.join(DIST, _l), _p)
        _s = open(_f, encoding="utf-8").read()
        if '"Article"' not in _s: continue
        _og = _re.search(r'<meta property="og:image" content="([^"]+)"', _s)
        def _fix(m):
            try: _d = json.loads(m.group(2).replace("<\\/", "</"))
            except ValueError: return m.group(0)
            _nodes = _d.get("@graph", [_d]) if isinstance(_d, dict) else []
            _hit = False
            for _n in _nodes:
                if isinstance(_n, dict) and _n.get("@type") == "Article":
                    _n["dateModified"] = LASTMOD.get(_p, _n.get("dateModified")); _n["author"] = {"@id": f"https://{DOMAIN}/#org"}
                    if _og and "image" not in _n: _n["image"] = _og.group(1)
                    _hit = True
            return m.group(1) + json.dumps(_d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + m.group(3) if _hit else m.group(0)
        _s2 = _re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', _fix, _s, flags=_re.S)
        if _s2 != _s: open(_f, "w", encoding="utf-8").write(_s2)
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
AddCharset utf-8 .txt .xml .webmanifest
<IfModule mod_rewrite.c>
RewriteEngine On
# http and www go to https://makeitsweep.com in one hop
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} ^www\\. [NC]
RewriteCond %{HTTP_HOST} ^(?:www\\.)?(.+)$ [NC]
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
# a page has one address: /pricing/ -> /pricing (folders keep their slash, which NGINX adds)
RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{DOCUMENT_ROOT}/$1.html -f
RewriteRule ^(.+?)/$ /$1 [R=301,L]
# /404 is not a page: it falls through to the real 404
RewriteCond $1 !(^|/)404$
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
# pages only load from the site itself (and call the app); inline scripts and styles stay allowed (the site uses them). Not on files like the PDFs
<FilesMatch "\\.html$">
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://app.makeitsweep.com; media-src 'self'; manifest-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
</FilesMatch>
<FilesMatch "\\.woff2$">
Header set Cache-Control "public, max-age=2592000, immutable"
</FilesMatch>
# images and videos keep their name when they are redone: fresh for a day, then checked again in the background
<FilesMatch "\\.(webp|png|svg|ico|mp4|webm)$">
Header set Cache-Control "public, max-age=86400, stale-while-revalidate=2592000"
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
AddOutputFilterByType DEFLATE text/html text/css application/javascript text/javascript application/json image/svg+xml application/xml text/xml application/rss+xml text/plain application/manifest+json
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
_odd = _prices_named("free-trading-journal.html") - _SWEEP_PRICES - set().union(*(_amounts(pages17.COMP[n]) for n, *_ in pages20.FREE_CMP if n != "Sweep"))
if _odd: print(f"warning: free-trading-journal.html names prices that aren't in src/data/competitors.json: {sorted(_odd)}")
