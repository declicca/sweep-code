"""qa.py func: menus by mouse and keyboard, phone menu, account size switch, one-minute tour, language and consent banners,
the 6 calculators. Prints a line per failed check and the count."""
import mimetypes, os

VIS = "e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.visibility !== 'hidden' && parseFloat(s.opacity) > .9 && r.width > 0 && r.height > 0; }"
CALCS = ("position-size-calculator", "trailing-drawdown-calculator", "consistency-rule-calculator", "payout-calculator", "expectancy-calculator", "prop-firm-roi-calculator")

async def run(B, dist):
    from playwright.async_api import async_playwright
    res = []
    def check(name, ok, info=""):
        res.append(ok)
        if not ok: print(f"   ÉCHEC {name}" + (f" ({info})" if info else ""), flush=True)
    async with async_playwright() as p:
        br = await p.chromium.launch(channel="chrome")
        # desktop menus, mouse and keyboard
        for lang in ("", "/fr", "/es"):
            ctx = await br.new_context(viewport={"width": 1300, "height": 850}, locale="en-US" if not lang else "fr-CA"); pg = await ctx.new_page()
            await pg.goto(B + lang + "/pricing", wait_until="load")
            for key in ("product", "firms", "res"):
                dd = pg.locator(f'.navdd[data-dd="{key}"]'); btn, menu = dd.locator(".ddbtn"), dd.locator(".ddmenu")
                await btn.hover(); await pg.wait_for_timeout(450)
                check(f"{lang or '/'} menu {key} : s'ouvre au survol", await menu.evaluate(VIS))
                await pg.mouse.move(650, 600); await pg.wait_for_timeout(450)
                await btn.click(); await pg.wait_for_timeout(350)
                check(f"{lang or '/'} menu {key} : s'ouvre au clic", await btn.get_attribute("aria-expanded") == "true" and await menu.evaluate(VIS))
                await pg.mouse.click(650, 700); await pg.wait_for_timeout(350)
                check(f"{lang or '/'} menu {key} : se ferme au clic à côté", await btn.get_attribute("aria-expanded") == "false")
                await btn.focus(); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(350)
                opened = await btn.get_attribute("aria-expanded") == "true"
                await pg.keyboard.press("Tab"); inmenu = await pg.evaluate("document.activeElement.closest('.ddmenu') !== null")
                await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
                back = await pg.evaluate("document.activeElement.classList.contains('ddbtn')")
                check(f"{lang or '/'} menu {key} : Entrée / Tab / Échap", opened and inmenu and back and await btn.get_attribute("aria-expanded") == "false", f"open={opened} tab-in={inmenu} focus-back={back}")
            await ctx.close()
        # phone menu, size switch, tour, banners
        ctx = await br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="fr-CA"); pg = await ctx.new_page()
        await pg.goto(B + "/fr/pricing", wait_until="load")
        await pg.locator(".menu-btn").click(); await pg.wait_for_timeout(500)
        check("menu téléphone : s'ouvre", await pg.locator("#sheet").get_attribute("data-open") == "true" and await pg.locator("#sheet a").first.evaluate(VIS))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(500)
        check("menu téléphone : se ferme avec Échap", await pg.locator("#sheet").get_attribute("data-open") == "false")
        await pg.locator(".menu-btn").click(); await pg.wait_for_timeout(500); await pg.locator(".menu-btn").click(); await pg.wait_for_timeout(500)
        check("menu téléphone : se ferme avec le bouton", await pg.locator("#sheet").get_attribute("data-open") == "false")
        await pg.goto(B + "/fr/prop-firms/topstep", wait_until="load")
        seg = pg.locator(".seg.sizes").first
        check("tailles de compte : visibles sur téléphone", await seg.is_visible())
        await seg.locator("button").nth(1).click(); await pg.wait_for_timeout(300)
        col = await pg.locator(".rules-tbl").first.get_attribute("data-col")
        vis = await pg.evaluate("[...document.querySelectorAll('.rules-tbl')].every(t => [...t.querySelectorAll('.cc.c1')].every(c => getComputedStyle(c).display !== 'none') && [...t.querySelectorAll('.cc.c0')].every(c => getComputedStyle(c).display === 'none'))")
        check("tailles de compte : la 2e taille dans chaque tableau", col == "1" and vis, f"data-col={col}")
        await pg.reload(wait_until="load")
        check("tailles de compte : gardée après rechargement", await pg.locator(".rules-tbl").first.get_attribute("data-col") == "1")
        for w, mob in ((390, True), (1300, False)):
            c2 = await br.new_context(viewport={"width": w, "height": 844}, is_mobile=mob, has_touch=mob, locale="fr-CA"); q = await c2.new_page()
            await q.goto(B + "/fr/", wait_until="load"); await q.locator("[data-tour]").first.click(); await q.wait_for_timeout(700)
            opened = await q.evaluate("document.getElementById('tour').open"); src = await q.evaluate("document.querySelectorAll('#tour video source').length")
            await q.keyboard.press("Escape"); await q.wait_for_timeout(600)
            check(f"visite {w} px : s'ouvre avec sa vidéo, se ferme avec Échap", opened and src > 0 and not await q.evaluate("document.getElementById('tour').open"), f"open={opened} sources={src}")
            await c2.close()
        # language suggestion: a French browser on an English page, offered once
        await pg.goto(B + "/pricing", wait_until="load"); await pg.wait_for_timeout(1400)
        shown = await pg.locator("#langsug").evaluate(VIS); href = await pg.locator("#langsug-go").get_attribute("href")
        await pg.locator("#langsug-x").click(); await pg.wait_for_timeout(500)
        await pg.reload(wait_until="load"); await pg.wait_for_timeout(1400)
        check("suggestion de langue : proposée, mène à /fr, plus proposée une fois fermée", shown and href == "/fr/pricing" and await pg.locator("#langsug").is_hidden(), f"href={href}")
        # consent (Loi 25): shown only with utm, nothing written before a choice
        await pg.goto(B + "/fr/?utm_source=qc&utm_medium=test&utm_campaign=audit", wait_until="load"); await pg.wait_for_timeout(600)
        c_shown = await pg.locator("#consent").evaluate(VIS); before = "sweep_utm=" in await pg.evaluate("document.cookie")
        await pg.locator('#consent [data-consent="no"]').click(); await pg.wait_for_timeout(500)
        hidden = await pg.locator("#consent").is_hidden(); stored = await pg.evaluate("localStorage.getItem('sweep-consent')")
        after = "sweep_utm=" in await pg.evaluate("document.cookie")
        check("consentement : affiché avec utm, rien avant un choix, Refuser n'écrit rien", c_shown and not before and hidden and stored == "no" and not after, f"stored={stored}")
        # the cookie is for .makeitsweep.com over HTTPS: the local files served under that address, intercepted (nothing leaves the machine)
        async def as_site(route):
            path = route.request.url.split("makeitsweep.com", 1)[1].split("?")[0].split("#")[0]; f = os.path.join(dist, path.lstrip("/"))
            for c in (f, f + ".html", os.path.join(f, "index.html")):
                if os.path.isfile(c): return await route.fulfill(path=c, content_type=mimetypes.guess_type(c)[0] or "text/html")
            await route.fulfill(status=404, body="")
        c3 = await br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="fr-CA")
        await c3.route("https://makeitsweep.com/**", as_site); await c3.route("https://app.makeitsweep.com/**", lambda r: r.fulfill(status=204, body=""))
        q = await c3.new_page(); B2 = "https://makeitsweep.com"
        await q.goto(B2 + "/fr/?utm_source=qc&utm_medium=test&utm_campaign=audit", wait_until="load"); await q.wait_for_timeout(600)
        await q.locator('#consent [data-consent="yes"]').click(); await q.wait_for_timeout(400)
        check("consentement : Accepter écrit le témoin d'attribution", "sweep_utm=" in await q.evaluate("document.cookie"))
        await q.goto(B2 + "/fr/pricing?utm_source=qc2", wait_until="load"); await q.wait_for_timeout(500)
        check("consentement : plus affiché ensuite", await q.locator("#consent").is_hidden())
        await c3.close()
        # calculators: every number field changes the result
        for slug in CALCS:
            for path in (f"/{slug}", f"/fr/{slug}"):
                await pg.goto(B + path, wait_until="load"); await pg.wait_for_timeout(300)
                errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
                n = await pg.locator(".calc-form input[type=number]").count(); changed = 0
                for i in range(n):
                    inp = pg.locator(".calc-form input[type=number]").nth(i)
                    if not await inp.is_visible(): continue
                    before = await pg.locator(".calc-out").inner_text(); v = await inp.input_value()
                    await inp.fill(str(round(float(v or 0) * 1.5 + 7, 2))); await inp.dispatch_event("input"); await inp.dispatch_event("change"); await pg.wait_for_timeout(150)
                    changed += before != await pg.locator(".calc-out").inner_text()
                    await inp.fill(v); await inp.dispatch_event("input"); await inp.dispatch_event("change")
                out = await pg.locator(".calc-out").inner_text()
                check(f"calculateur {path} : {changed} champ(s) sur {n} changent le résultat", changed > 0 and not errs and "NaN" not in out and "undefined" not in out, f"errors={errs[:1]}")
        await ctx.close(); await br.close()
    print(f"== Fonctionnel : {sum(res)} / {len(res)} vérifications réussies", flush=True)
    return len(res) - sum(res)
