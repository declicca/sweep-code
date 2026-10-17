"""qa.py kbd: keyboard on computer (skip link, the three menus, language menu, focus rings) and on phone (the menu sheet).
The local files are served under https://makeitsweep.com, intercepted: nothing leaves the machine."""
import mimetypes, os, re

A = "(()=>{const a=document.activeElement;const s=getComputedStyle(a);const r=a.getBoundingClientRect();return {tag:a.tagName,cls:(a.className||'').toString().slice(0,30),txt:(a.textContent||'').trim().slice(0,30),outline:s.outlineStyle+' '+s.outlineWidth,shadow:s.boxShadow!=='none',vis:r.width>0&&r.height>0&&r.top>-5&&r.bottom<innerHeight+5}})()"

async def run(dist):
    from playwright.async_api import async_playwright
    res = []
    def check(name, ok, info=""):
        res.append(ok)
        if not ok: print(f"   ÉCHEC {name}" + (f" {info}" if info else ""), flush=True)
    async def as_site(route):
        path = route.request.url.split("makeitsweep.com", 1)[1].split("?")[0].split("#")[0].lstrip("/")
        for c in (os.path.join(dist, path), os.path.join(dist, path, "index.html"), os.path.join(dist, path + ".html")):
            if os.path.isfile(c):
                if c.endswith(".html"):   # Chrome's prefetch would bypass the interception and fetch the live site
                    return await route.fulfill(body=re.sub(r'<script type="speculationrules">.*?</script>', "", open(c, encoding="utf-8").read(), flags=re.S), content_type="text/html")
                return await route.fulfill(path=c, content_type=mimetypes.guess_type(c)[0] or "text/html")
        await route.fulfill(status=404, body="")
    async def tab_to(pg, sel, n=40):
        for _ in range(n):
            await pg.keyboard.press("Tab")
            if await pg.evaluate(f"document.activeElement.matches({sel!r})"): return True
        return False
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel="chrome")
        for loc, path in (("en-US", "/"), ("fr-CA", "/fr/pricing"), ("es-ES", "/es/prop-firms/")):
            ctx = await b.new_context(viewport={"width": 1300, "height": 850}, locale=loc)
            await ctx.route("https://makeitsweep.com/**", as_site); await ctx.route("https://app.makeitsweep.com/**", lambda r: r.fulfill(status=204, body=""))
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto("https://makeitsweep.com" + path, wait_until="load"); await pg.wait_for_timeout(600)
            await pg.keyboard.press("Tab"); a = await pg.evaluate(A)
            check(f"{path} lien d'évitement en premier et visible", "skip" in a["cls"] and a["vis"], str(a))
            await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
            check(f"{path} lien d'évitement mène au contenu", await pg.evaluate("location.hash.length>1 && !!document.querySelector(location.hash)"))
            await pg.goto("https://makeitsweep.com" + path, wait_until="load"); await pg.wait_for_timeout(500)
            for dd in ("product", "firms", "res"):
                ok = await tab_to(pg, f'.navdd[data-dd="{dd}"] .ddbtn'); a = await pg.evaluate(A)
                check(f"{path} {dd} : bouton atteint, anneau de focus", ok and a["outline"].split()[0] != "none", str(a))
                await pg.keyboard.press("Enter"); await pg.wait_for_timeout(350)
                st = await pg.evaluate(f"(()=>{{const d=document.querySelector('.navdd[data-dd=\"{dd}\"]');const m=d.querySelector('.ddmenu');const r=m.getBoundingClientRect();return {{open:d.classList.contains('open'),exp:d.querySelector('.ddbtn').getAttribute('aria-expanded'),h:r.height,op:getComputedStyle(m).opacity,vis:getComputedStyle(m).visibility}}}})()")
                check(f"{path} {dd} : Entrée ouvre", st["open"] and st["exp"] == "true" and st["h"] > 0 and float(st["op"]) > .9 and st["vis"] == "visible", str(st))
                await pg.keyboard.press("Tab"); a = await pg.evaluate(A)
                check(f"{path} {dd} : Tab entre dans le menu", await pg.evaluate(f"!!document.activeElement.closest('.navdd[data-dd=\"{dd}\"] .ddmenu')") and a["vis"], str(a))
                await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
                st = await pg.evaluate(f"(()=>{{const d=document.querySelector('.navdd[data-dd=\"{dd}\"]');return {{open:d.classList.contains('open'),focus:document.activeElement===d.querySelector('.ddbtn')}}}})()")
                check(f"{path} {dd} : Échap ferme, focus revenu", (not st["open"]) and st["focus"], str(st))
            if await tab_to(pg, ".langsel button, .langsel .lsbtn, [data-lang-btn]"):
                await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
                await pg.keyboard.press("ArrowDown"); a2 = await pg.evaluate(A)
                check(f"{path} langue : Entrée ouvre, flèche bas avance", a2["tag"] == "A", str(a2))
                await pg.keyboard.press("Escape"); await pg.wait_for_timeout(250)
                check(f"{path} langue : Échap ferme, focus revenu", await pg.evaluate("document.activeElement.tagName==='BUTTON'"))
            else: check(f"{path} bouton de langue atteint", False)
            await pg.evaluate("document.activeElement.blur(); const m=document.querySelector('main'); m.setAttribute('tabindex','-1'); m.focus(); m.removeAttribute('tabindex')")
            bad = []
            for _ in range(25):
                await pg.keyboard.press("Tab"); a = await pg.evaluate(A)
                if a["outline"].split()[0] == "none" and not a["shadow"]: bad.append(a)
            check(f"{path} les 25 éléments suivants montrent un anneau de focus", not bad, str(bad[:3]))
            check(f"{path} aucune erreur de script", not errs, str(errs[:2]))
            await ctx.close()
        for loc, path in (("en-US", "/"), ("fr-CA", "/fr/features")):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale=loc)
            await ctx.route("https://makeitsweep.com/**", as_site)
            pg = await ctx.new_page(); await pg.goto("https://makeitsweep.com" + path, wait_until="load"); await pg.wait_for_timeout(600)
            check(f"{path} téléphone : bouton du menu atteint", await tab_to(pg, ".menu-btn", 10))
            await pg.keyboard.press("Enter"); await pg.wait_for_timeout(450)
            check(f"{path} téléphone : le menu s'ouvre", await pg.evaluate("document.getElementById('sheet').getAttribute('data-open')==='true' && document.querySelector('.menu-btn').getAttribute('aria-expanded')==='true'"))
            await pg.keyboard.press("Tab"); a = await pg.evaluate(A)
            check(f"{path} téléphone : Tab entre dans le menu", await pg.evaluate("!!document.activeElement.closest('#sheet')") and a["vis"], str(a))
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(400)
            check(f"{path} téléphone : Échap ferme, focus sur le bouton", await pg.evaluate("document.getElementById('sheet').getAttribute('data-open')!=='true' && document.activeElement.matches('.menu-btn')"))
            await pg.keyboard.press("Tab")
            check(f"{path} téléphone : le menu fermé sort de l'ordre de tabulation", not await pg.evaluate("!!document.activeElement.closest('#sheet')"))
            await ctx.close()
        await b.close()
    print(f"== Clavier : {sum(res)} / {len(res)} vérifications réussies", flush=True)
    return len(res) - sum(res)
