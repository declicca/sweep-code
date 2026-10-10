import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from pages1 import page_features, page_prop
from pages6 import page_home, page_how, page_pricing as page_pricing6
from pages2 import page_faq, page_tradovate, page_install, page_security, page_about, page_contact, page_changelog, page_404
from pages3 import page_ai, page_econ
from pages4 import page_pricing
from pages5 import page_100
from pages7 import page_tools, page_position, page_drawdown, page_consistency
from pages8 import FIRMS, make_firm_page
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
PAGES = {"index.html":page_home,"features.html":page_features,"ai.html":page_ai,"how-it-works.html":page_how,"prop-traders.html":page_prop,"economic-calendar.html":page_econ,
 "import.html":page_import,"install.html":page_install,"security.html":page_security,"pricing.html":page_pricing6,"faq.html":page_faq,
 "about.html":page_about,"contact.html":page_contact,"changelog.html":page_changelog_new,"privacy.html":page_privacy,"terms.html":page_terms,"risk.html":page_risk,"404.html":page_404,"100":page_100,"tools.html":page_tools,"position-size-calculator.html":page_position,"trailing-drawdown-calculator.html":page_drawdown,"consistency-rule-calculator.html":page_consistency}
for _s,_n in FIRMS: PAGES[_s] = make_firm_page(_s,_n)
PAGES.update({"expectancy-calculator.html":page_expectancy,"prop-firm-roi-calculator.html":page_roi,"payout-calculator.html":page_payoutcalc,
              "futures-contracts.html":pages12.page_contracts,"release-dates.html":pages13.page_release_hub,"glossary.html":pages13.page_glossary,
              "futures-market-hours.html":pages13.page_hours,"press-kit.html":pages13.page_press,
              "trading-templates.html":pages14.page_templates,"how-to-choose-a-trading-journal.html":pages14.page_choose,"trading-journal-routine.html":pages14.page_routine,
              "sweep-vs-tradezella.html":pages17.page_vs_tradezella,"best-trading-journal-for-prop-firms.html":pages17.page_best_journal})
for _c in pages12.C: PAGES[pages12.slug(_c[0])] = pages12.make_contract(_c[0])
PAGES["prop-firms/index.html"] = pages18.page_hub
for _f in pages18.presets.FIRMS: PAGES[pages18.page_of(_f)] = pages18.make_rules_page(_f)
for _r in pages13.REL: PAGES[_r[1]] = pages13.make_release(_r[0])
PRIO = {"100":"0.8","tools.html":"0.8","position-size-calculator.html":"0.8","trailing-drawdown-calculator.html":"0.8","consistency-rule-calculator.html":"0.8","topstep-trading-journal.html":"0.8","apex-trader-funding-journal.html":"0.8","take-profit-trader-journal.html":"0.8","lucid-trading-journal.html":"0.8","myfundedfutures-journal.html":"0.8","index.html":"1.0","features.html":"0.9","ai.html":"0.9","prop-traders.html":"0.9","how-it-works.html":"0.8","economic-calendar.html":"0.8","pricing.html":"0.8","faq.html":"0.7","sweep-vs-tradezella.html":"0.8","best-trading-journal-for-prop-firms.html":"0.9"}
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
for lang in LANGS:
    t = lambda d, L=lang: d[L]
    out = DIST if lang == "en" else os.path.join(DIST, lang); os.makedirs(out, exist_ok=True)
    for page, fn in PAGES.items():
        title, desc, body, ld = fn(lang, t)
        dest = os.path.join(out, "100", "index.html") if page == "100" else os.path.join(out, page)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w").write(shell(lang, page, title, desc, body, t, ld))
import datetime
BUILD_DATE = datetime.date.today().isoformat()
# prop firm rule pages: lastmod = the date their rules were last verified
LASTMOD = {pages18.page_of(f): pages18.checked_of(f) for f in pages18.presets.FIRMS}
LASTMOD["prop-firms/index.html"] = max(LASTMOD.values())
for _p in LASTMOD: PRIO.setdefault(_p, "0.8")
urls = []
for p in PAGES:
    if p == "404.html": continue
    for l in LANGS:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{a}" href="https://{DOMAIN}{href(a,p)}"/>' for a in LANGS) + f'<xhtml:link rel="alternate" hreflang="x-default" href="https://{DOMAIN}{href("en",p)}"/>'
        urls.append(f'<url><loc>https://{DOMAIN}{href(l,p)}</loc><lastmod>{LASTMOD.get(p, BUILD_DATE)}</lastmod><priority>{PRIO.get(p,"0.5")}</priority>{alts}</url>')
open(os.path.join(DIST,"sitemap.xml"),"w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(urls) + "</urlset>")
shutil.copy(os.path.join(HERE,"data","robots.txt"), os.path.join(DIST,"robots.txt"))
shutil.copy(os.path.join(HERE,"data","llms.txt"), os.path.join(DIST,"llms.txt"))
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
# /100 campaign page without a trailing-slash redirect (keeps UTM query strings intact)
RewriteRule ^100$ /100/index.html [L]
RewriteRule ^(fr|es)/100$ /$1/100/index.html [L]
# prop firm rules hub: /prop-firms serves prop-firms/index.html (the firms' pages live in that folder)
RewriteRule ^prop-firms$ /prop-firms/index.html [L]
RewriteRule ^(fr|es)/prop-firms$ /$1/prop-firms/index.html [L]
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
RewriteCond %{THE_REQUEST} \s/+(.*/)?index\.html[\s?] [NC]
RewriteRule ^(.*/)?index\.html$ /$1 [R=301,L]
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
""")
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
