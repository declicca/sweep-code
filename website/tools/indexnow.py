"""IndexNow (Bing, Yandex, Seznam, Naver): after a real deploy of the site, submit the pages whose sitemap date changed.

deploy.sh saves the live sitemap before uploading, then runs:  python3 -I website/tools/indexnow.py <old sitemap> website/dist/sitemap.xml
Pages that are new or have a new <lastmod> are sent in one request, with the key file the build writes at the site's root
(dates are days: a page changed again on the day of an earlier deploy is not sent twice; the sitemap still has it).
--dry prints them without sending. A failure is only reported: it never stops the deploy. Standard library only."""
import json, os, re, sys, time, urllib.request

HOST = "makeitsweep.com"

def dates(xml):
    """{url: lastmod} from a sitemap."""
    return dict(re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", xml))

def read(path, live):
    """{url: lastmod} of a sitemap, or of every sitemap an index lists: read next to the index for the new build,
    fetched one at a time, gently, for the live site (the site's server blocks bursts)."""
    xml = open(path, encoding="utf-8").read()
    if "<sitemapindex" not in xml: return dates(xml)
    out = {}
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        if live:
            time.sleep(1)
            with urllib.request.urlopen(loc, timeout=20) as r: out.update(dates(r.read().decode("utf-8")))
        else:
            out.update(dates(open(os.path.join(os.path.dirname(os.path.abspath(path)), loc.rsplit("/", 1)[1]), encoding="utf-8").read()))
    return out

def main():
    args = [a for a in sys.argv[1:] if a != "--dry"]
    if len(args) != 2: sys.exit("Usage : indexnow.py <old sitemap> <new sitemap> [--dry]")
    old_path, new_path = args
    try: old = read(old_path, live=True)
    except Exception: old = {}
    new = read(new_path, live=False)
    if not old:
        print("IndexNow : sitemap en ligne illisible, rien n'est envoyé."); return
    urls = [u for u, d in new.items() if old.get(u) != d]
    if not urls:
        print("IndexNow : aucune page nouvelle ou modifiée."); return
    root = os.path.dirname(os.path.abspath(new_path))
    key = next((f[:-4] for f in os.listdir(root) if re.fullmatch(r"[0-9a-f]{32}\.txt", f)), None)
    if not key:
        print("IndexNow : fichier de clé absent du site, rien n'est envoyé."); return
    if "--dry" in sys.argv:
        print(f"IndexNow (simulation) : {len(urls)} page(s) à envoyer."); return
    body = json.dumps({"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: print(f"IndexNow : {len(urls)} page(s) envoyée(s) (HTTP {r.status}).")
    except Exception as e:
        print(f"IndexNow : envoi refusé ou impossible ({e}). Le déploiement, lui, est fait.")

if __name__ == "__main__":
    main()
