from core import *
import ui
import re
import presets
from pages18 import (slug, page_of, payout_page_of, an, has_payouts, usd, pc, kk, day, rep, fr_de, colon, checked_of, official, src_name, verified_of, _ph, _po,
                     groups_of, table, payout_sentence, real_changes, no_change, change_label, change_value, RULE_CHANGES, RSS_LINK)
from pages19 import _day_conds, _fr_nbsp, ABBR, SHORT, GUIDE_PAYOUT

# Payout rules of one firm (Search Console, Nov. 10, 2026: « apex trader funding payout rules », « minimum payout », « maximum payout »,
# « payout rules 50k account », « topstep payout policy »… reach the firm pages on page 3 to 6). One page per firm of the catalogue,
# about payouts only: the answer, the tables by size, an example worked out from the rules, and the questions as they are searched.
# Every number comes from the app's catalogue (presets.py), like the firm pages: nothing is retyped here.

def _funded_pos(f):
    """(program, size, payout rules of the funded account) for every size that has payout rules."""
    return [(p, s, _po(_ph(s, "funded"))) for p in f["programs"] for s in p["sizes"] if _po(_ph(s, "funded"))]
PAYOUT_FIRMS = [f for f in presets.FIRMS if has_payouts(f)]

def _first_cap(po):
    """The most the first payout can be: the first step of a ladder, else the cap per payout. None: no cap in the catalogue."""
    lad = po.get("ladder")
    return lad[0] if lad else po.get("max")
def _span(vals, fmt, lang):
    v = sorted(set(vals))
    if not v: return ""
    return fmt(v[0]) if len(v) == 1 else fmt(v[0]) + {"en": " to ", "fr": " à ", "es": " a "}[lang] + fmt(v[-1])
def _between(vals, fmt, lang):
    """In a sentence: « $200 », or « between $200 and $1,000 »."""
    v = sorted(set(vals))
    if len(v) < 2: return _span(v, fmt, lang)
    return {"en": f"between {fmt(v[0])} and {fmt(v[-1])}", "fr": f"entre {fmt(v[0])} et {fmt(v[-1])}", "es": f"entre {fmt(v[0])} y {fmt(v[-1])}"}[lang]
def _sep(lang): return " ; " if lang == "fr" else "; "
def _tl(l): return lambda d: d[l]

def _answer(f, l):
    """Two sentences with the real ranges: where a payout starts, what caps the first one, what the trader keeps."""
    name = f["name"]; pos = [po for _, _, po in _funded_pos(f)]; U = lambda v: usd(v, l)
    mins, caps, splits = [po["min"] for po in pos if po.get("min")], [c for po in pos if (c := _first_cap(po))], [po["split_pct"] for po in pos if po.get("split_pct")]
    a = {"en": f"At {name}, a payout starts " + ("" if len(set(mins)) > 1 else "at ") + _between(mins, U, l), "fr": f"Chez {name}, un payout commence " + ("" if len(set(mins)) > 1 else "à ") + _between(mins, U, l),
         "es": f"En {name}, un payout empieza " + ("" if len(set(mins)) > 1 else "en ") + _between(mins, U, l)}[l] if mins else ""
    b = {"en": "the first one is capped " + ("" if len(set(caps)) > 1 else "at ") + _between(caps, U, l), "fr": "le premier est plafonné " + ("" if len(set(caps)) > 1 else "à ") + _between(caps, U, l),
         "es": "el primero tiene un tope de " + _between(caps, U, l)}[l] if caps else ""
    if a and b: x = a + {"en": " and ", "fr": " et ", "es": " y "}[l] + b
    elif a: x = a
    elif b: x = {"en": f"At {name}, ", "fr": f"Chez {name}, ", "es": f"En {name}, "}[l] + b.replace("the first one", "the first payout").replace("le premier", "le premier payout").replace("el primero", "el primer payout")
    else: x = ""
    if x and len(set(mins)) < 2 and len(set(caps)) < 2: x += "."
    elif x: x += {"en": ", depending on the account type and size.", "fr": ", selon le type et la taille du compte.", "es": ", según el tipo y el tamaño de la cuenta."}[l]
    if splits: x += " " + {"en": f"You keep {_span(splits, lambda v: pc(v, l), l)} of what you request.", "fr": f"Tu gardes {_span(splits, lambda v: pc(v, l), l)} de ce que tu demandes.",
                           "es": f"Te quedas con el {_span(splits, lambda v: pc(v, l), l)} de lo que pides."}[l]
    return x.strip()

def _po_groups(lang, t, sizes, variant=None):
    """The payout blocks of the firm page's table, alone."""
    return [g for g in groups_of(lang, t, sizes, variant) if g[0]["en"].startswith("Payouts")]

def _example(f, p, s, l):
    """The payout rules of one account, worked out: what it takes to qualify, how much can be requested, what is received.
    Each line is arithmetic on the catalogue's values, nothing else."""
    F = _ph(s, "funded"); po = _po(F); U = lambda v: usd(v, l); size = kk(s["size"]); out = []
    if po.get("win_days"):
        n, m = po["win_days"], po.get("win_min")
        out.append({"en": f"<b>To qualify:</b> {n:g} winning days" + (f" of {U(m)} or more each, so at least {U(n * m)} of profit made on those days." if m else ", whatever the profit of each."),
                    "fr": f"<b>Pour y avoir droit :</b> {n:g} jours gagnants" + (f" de {U(m)} ou plus chacun, donc au moins {U(n * m)} de profit sur ces jours." if m else ", quel que soit le profit de chacun."),
                    "es": f"<b>Para tener derecho:</b> {n:g} días ganadores" + (f" de {U(m)} o más cada uno, es decir, al menos {U(n * m)} de beneficio en esos días." if m else ", sea cual sea el beneficio de cada uno.")}[l])
    if po.get("trade_days"):
        out.append({"en": f"<b>Traded days:</b> {po['trade_days']:g} days with at least one trade before you request.", "fr": f"<b>Jours tradés :</b> {po['trade_days']:g} jours avec au moins un trade avant de demander.",
                    "es": f"<b>Días operados:</b> {po['trade_days']:g} días con al menos una operación antes de pedir."}[l])
    if po.get("cycle_days"):
        out.append({"en": f"<b>Between two payouts:</b> {po['cycle_days']:g} days.", "fr": f"<b>Entre deux payouts :</b> {po['cycle_days']:g} jours.", "es": f"<b>Entre dos payouts:</b> {po['cycle_days']:g} días."}[l])
    if po.get("first_min") or po.get("cycle_min"):
        a, b = po.get("first_min"), po.get("cycle_min")
        out.append({"en": "<b>Profit to reach:</b> " + (f"{U(a)} before the first payout" + (f", then {U(b)} before each next one." if b else ".") if a else f"{U(b)} since your last payout."),
                    "fr": "<b>Profit à atteindre :</b> " + (f"{U(a)} avant le premier payout" + (f", puis {U(b)} avant chaque suivant." if b else ".") if a else f"{U(b)} depuis ton dernier payout."),
                    "es": "<b>Beneficio que alcanzar:</b> " + (f"{U(a)} antes del primer payout" + (f", luego {U(b)} antes de cada siguiente." if b else ".") if a else f"{U(b)} desde tu último payout.")}[l])
    elif po.get("cycle_pos"):
        out.append({"en": "<b>Since your last payout:</b> the account must be in profit.", "fr": "<b>Depuis ton dernier payout :</b> le compte doit être en profit.", "es": "<b>Desde tu último payout:</b> la cuenta debe estar en beneficio."}[l])
    if po.get("min_bal"):
        over = po["min_bal"] - s["size"]
        out.append({"en": f"<b>Balance to keep:</b> above {U(po['min_bal'])}" + (f", that is {U(over)} over the {size} you start with." if over > 0 else "."),
                    "fr": f"<b>Solde à garder :</b> au-dessus de {U(po['min_bal'])}" + (f", soit {U(over)} de plus que les {size} de départ." if over > 0 else "."),
                    "es": f"<b>Saldo a mantener:</b> por encima de {U(po['min_bal'])}" + (f", es decir, {U(over)} más que los {size} iniciales." if over > 0 else ".")}[l])
    if F.get("consistency"):
        c = F["consistency"]
        out.append({"en": f"<b>Consistency:</b> your best day can be at most {pc(c, l)} of the profit made since your last payout.",
                    "fr": f"<b>Consistance :</b> ton meilleur jour peut représenter au plus {pc(c, l)} du profit fait depuis ton dernier payout.",
                    "es": f"<b>Consistencia:</b> tu mejor día puede ser como máximo el {pc(c, l)} del beneficio hecho desde tu último payout."}[l])
    lad, cap = po.get("ladder"), _first_cap(po)
    if po.get("min"):
        out.append({"en": f"<b>Smallest request:</b> {U(po['min'])}.", "fr": f"<b>Plus petite demande :</b> {U(po['min'])}.", "es": f"<b>Solicitud más pequeña:</b> {U(po['min'])}."}[l])
    if lad:
        caps = " / ".join(U(x) if x is not None else {"en": "no cap", "fr": "sans plafond", "es": "sin tope"}[l] for x in lad)
        out.append({"en": f"<b>Largest request:</b> the cap changes with each payout. For payouts 1 to {len(lad)}: {caps}.",
                    "fr": f"<b>Plus grande demande :</b> le plafond change à chaque payout. Pour les payouts 1 à {len(lad)} : {caps}.",
                    "es": f"<b>Solicitud más grande:</b> el tope cambia en cada payout. Para los payouts 1 a {len(lad)}: {caps}."}[l])
    elif cap:
        x = {"en": f"<b>Largest request:</b> {U(cap)} per payout", "fr": f"<b>Plus grande demande :</b> {U(cap)} par payout", "es": f"<b>Solicitud más grande:</b> {U(cap)} por payout"}[l]
        if po.get("max_dll"): x += {"en": f", or {U(po['max_dll'])} with the daily loss limit option", "fr": f", ou {U(po['max_dll'])} avec l’option limite de perte du jour", "es": f", o {U(po['max_dll'])} con la opción de límite de pérdida diaria"}[l]
        out.append(x + ".")
    if po.get("max_pct"):
        pct = po["max_pct"]; need = cap * 100 / pct if cap else None
        out.append({"en": f"<b>Share of your profit:</b> a payout is at most {pc(pct, l)} of the profit in the account" + (f", so requesting the full {U(cap)} takes {U(need)} of profit." if need else "."),
                    "fr": f"<b>Part de ton profit :</b> un payout vaut au plus {pc(pct, l)} du profit du compte" + (f", donc pour demander les {U(cap)} en entier, il faut {U(need)} de profit." if need else "."),
                    "es": f"<b>Parte de tu beneficio:</b> un payout es como máximo el {pc(pct, l)} del beneficio de la cuenta" + (f", así que para pedir los {U(cap)} completos hacen falta {U(need)} de beneficio." if need else ".")}[l])
    if po.get("max_payouts") and not lad:
        out.append({"en": f"<b>Number of payouts:</b> up to {po['max_payouts']:g} on this account.", "fr": f"<b>Nombre de payouts :</b> jusqu’à {po['max_payouts']:g} sur ce compte.", "es": f"<b>Número de payouts:</b> hasta {po['max_payouts']:g} en esta cuenta."}[l])
    if po.get("split_pct"):
        sp = po["split_pct"]; req = cap or po.get("min")
        out.append({"en": f"<b>What you receive:</b> {pc(sp, l)}, the profit split (your share of each payout)" + (f". A {U(req)} request pays you {U(req * sp / 100)}." if req and sp < 100 else "."),
                    "fr": f"<b>Ce que tu reçois :</b> {pc(sp, l)}, le partage des profits (ta part de chaque payout)" + (f". Une demande de {U(req)} te verse {U(req * sp / 100)}." if req and sp < 100 else "."),
                    "es": f"<b>Lo que recibes:</b> el {pc(sp, l)}, el reparto de beneficios (tu parte de cada payout)" + (f". Una solicitud de {U(req)} te paga {U(req * sp / 100)}." if req and sp < 100 else ".")}[l])
    return out

def _by_size_table(lang, t, f, cell, note):
    """One row per account size, one column per account type: `cell(payout rules)` → text or « — »."""
    progs = [p for p in f["programs"] if any(cell(_po(_ph(s, "funded"))) != "—" for s in p["sizes"])]
    if not progs: return ""
    sizes = sorted({s["size"] for p in progs for s in p["sizes"]})
    head = f'<tr><th scope="col">{t(T("Size","Taille","Tamaño"))}</th>' + "".join(f'<th scope="col">{p["name"]}</th>' for p in progs) + "</tr>"
    rows = "".join(f'<tr><th scope="row">{kk(z)}</th>' + "".join(f'<td class="num" data-label="{html.escape(p["name"])}">{cell(_po(_ph(s, "funded"))) if (s := next((x for x in p["sizes"] if x["size"] == z), None)) else "—"}</td>' for p in progs) + "</tr>" for z in sizes)
    return f'<p>{t(note)}</p><div class="cmp-wrap"><table class="cmp guide"><thead>{head}</thead><tbody>{rows}</tbody></table></div>'

def _faqs(f):
    name, progs = f["name"], [p for p in f["programs"] if any(_po(_ph(s, "funded")) for s in p["sizes"])]
    def by_prog(l, fn):
        parts = [(p["name"], x) for p in progs if (x := fn(p, l))]
        if len(progs) == 1: return parts[0][1] if parts else ""
        if len(parts) == len(progs) and len({x for _, x in parts}) == 1:
            return parts[0][1] + {"en": " on every account type", "fr": " sur chaque type de compte", "es": " en cada tipo de cuenta"}[l]
        return _sep(l).join(n + colon(l) + x for n, x in parts)
    pos_of = lambda p: [(s, _po(_ph(s, "funded"))) for s in p["sizes"] if _po(_ph(s, "funded"))]
    out = []
    # minimum
    mn = lambda p, l: _span([po["min"] for _, po in pos_of(p) if po.get("min")], lambda v: usd(v, l), l)
    if any(mn(p, "en") for p in progs):
        out.append((T(f"What is the minimum payout at {name}?", f"Quel est le payout minimum chez {name} ?", f"¿Cuál es el payout mínimo en {name}?"),
                    {l: {"en": "The smallest amount you can request: ", "fr": "Le plus petit montant que tu peux demander : ", "es": "El importe más pequeño que puedes pedir: "}[l] + by_prog(l, mn) + "." for l in LANGS}))
    # maximum
    def mx(p, l):
        xs = [(s["size"], _first_cap(po)) for s, po in pos_of(p) if _first_cap(po)]
        if not xs: return {"en": "no cap in the rules Sweep tracks", "fr": "aucun plafond dans les règles suivies par Sweep", "es": "sin tope en las reglas que sigue Sweep"}[l]
        txt = ", ".join(f"{usd(c, l)} ({kk(z)})" for z, c in xs)
        if any(po.get("ladder") for _, po in pos_of(p)): txt += {"en": " for the first payout", "fr": " pour le premier payout", "es": " para el primer payout"}[l]
        return txt
    if any(_first_cap(po) for p in progs for _, po in pos_of(p)):
        pct = sorted({po["max_pct"] for p in progs for _, po in pos_of(p) if po.get("max_pct")})
        more = {l: ({"en": f" A payout is also limited to {_span(pct, lambda v: pc(v, l), l)} of the profit in the account.", "fr": f" Un payout est aussi limité à {_span(pct, lambda v: pc(v, l), l)} du profit du compte.",
                     "es": f" Un payout también está limitado al {_span(pct, lambda v: pc(v, l), l)} del beneficio de la cuenta."}[l] if pct else "") for l in LANGS}
        out.append((T(f"What is the maximum payout at {name}?", f"Quel est le payout maximum chez {name} ?", f"¿Cuál es el payout máximo en {name}?"),
                    {l: {"en": "Per payout, before the profit split. ", "fr": "Par payout, avant le partage des profits. ", "es": "Por payout, antes del reparto de beneficios. "}[l] + by_prog(l, mx) + "." + more[l] for l in LANGS}))
    # days
    def dz(p, l):
        po = _po(_ph(rep(p), "funded")); c = _day_conds(po, l, _tl(l))
        return ", ".join(c) if c else {"en": "no number of days in the rules Sweep tracks", "fr": "aucun nombre de jours dans les règles suivies par Sweep", "es": "ningún número de días en las reglas que sigue Sweep"}[l]
    if any(_day_conds(_po(_ph(rep(p), "funded")), "en", _tl("en")) for p in progs):
        out.append((T(f"How many days do I need before a payout at {name}?", f"Combien de jours faut-il avant un payout chez {name} ?", f"¿Cuántos días hacen falta antes de un payout en {name}?"),
                    {l: by_prog(l, dz) + ". " + {"en": "A winning day is a day that ends with at least the profit shown.", "fr": "Un jour gagnant est une journée qui finit avec au moins le profit indiqué.",
                                                  "es": "Un día ganador es un día que termina con al menos el beneficio indicado."}[l] for l in LANGS}))
    # split
    sp = lambda p, l: _span([po["split_pct"] for _, po in pos_of(p) if po.get("split_pct")], lambda v: pc(v, l), l)
    if any(sp(p, "en") for p in progs):
        out.append((T(f"What is the {name} profit split?", f"Quel est le partage des profits chez {name} ?", f"¿Cuál es el reparto de beneficios en {name}?"),
                    {l: {"en": "The share of each payout that you keep: ", "fr": "La part de chaque payout que tu gardes : ", "es": "La parte de cada payout que te quedas: "}[l] + by_prog(l, sp) + "." for l in LANGS}))
    # the 50K account, as it is searched
    fifty = [(p, s) for p in progs for s in p["sizes"] if s["size"] == 50000 and _po(_ph(s, "funded"))]
    sents = [x for p, s in fifty if (x := payout_sentence(f, p, s, {"en": an(f"{p['name']} 50K"), "fr": f"un {p['name']} 50K", "es": f"una cuenta {p['name']} de 50K"}))]
    if sents:
        out.append((T(f"What are the {name} payout rules for a 50K account?", f"Quelles sont les règles de payout d’un compte {name} 50K ?", f"¿Cuáles son las reglas de payout de una cuenta de 50K en {name}?"),
                    {l: " ".join(x[l] for x in sents) for l in LANGS}))
    out.append((T(f"Is Sweep affiliated with {name}?", f"Sweep est-il affilié à {name} ?", f"¿Sweep está afiliado a {name}?"),
                T(f"No. Sweep is independent and isn’t affiliated with, endorsed by or connected to {name}. The rules on this page come from Sweep’s weekly check of {poss(name)} official pages; always confirm on {poss(name)} site before you request a payout.",
                  f"Non. Sweep est indépendant et n’est ni affilié à {name}, ni approuvé par {name}. Les règles de cette page viennent de la vérification hebdomadaire des pages officielles {fr_de(name)} par Sweep ; confirme toujours sur le site {fr_de(name)} avant de demander un payout.",
                  f"No. Sweep es independiente y no está afiliado, respaldado ni vinculado a {name}. Las reglas de esta página vienen de la revisión semanal de las páginas oficiales de {name} por Sweep; confirma siempre en el sitio de {name} antes de pedir un payout.")))
    return out

def _payout_changes(f):
    return [c for c in real_changes(f) if "payout" in c.get("rule", "")]

def make_payout_page(f):
    pg = payout_page_of(f)
    SYSTEM_PAGES.add(pg)
    CRUMBS[pg] = T(f"{f['name']} payout rules", f"Payouts {f['name']}", f"Payouts de {f['name']}")
    def page(lang, t):
        name = f["name"]; U = lambda v: usd(v, lang)
        sn = ABBR.get(f["id"]) or SHORT.get(f["id"], name)   # the button stays on one line on a phone
        progs = [p for p in f["programs"] if any(_po(_ph(s, "funded")) for s in p["sizes"])]
        when = checked_of(f); last = max(when, presets.CHECKED)
        pos = [po for _, _, po in _funded_pos(f)]
        mins, caps, splits = [po["min"] for po in pos if po.get("min")], [c for po in pos if (c := _first_cap(po))], [po["split_pct"] for po in pos if po.get("split_pct")]
        lead = {l: (_answer(f, l) + " " + {"en": f"Below: what it takes to request one, the amounts by account size and an example worked out, from Sweep’s weekly check of {poss(name)} official pages.",
                                           "fr": f"Plus bas : ce qu’il faut pour en demander un, les montants par taille de compte et un exemple chiffré, tirés de la vérification hebdomadaire des pages officielles {fr_de(name)} par Sweep.",
                                           "es": f"Más abajo: lo que hace falta para pedir uno, los importes por tamaño de cuenta y un ejemplo con cifras, tomados de la revisión semanal de las páginas oficiales de {name} por Sweep."}[l]).strip() for l in LANGS}
        jump = ('<div class="jump rise d5">' + "".join(f'<a class="chip" href="#{i}">{t(x)}</a>' for i, x in (
                    [(f"p-{p.get('id', n)}", {l: p["name"] for l in LANGS}) for n, p in enumerate(progs)] if len(progs) > 1 else [])
                    + ([("max-payout", T("Max payout", "Payout max", "Payout máx."))] if caps else []) + ([("min-payout", T("Min payout", "Payout min", "Payout mín."))] if mins else [])
                    + [("changes", T("Rule changes", "Changements", "Cambios")), ("questions", T("Questions", "Questions", "Preguntas"))]) + "</div>")
        hero = ui.hero(t, T(name, name, name), T("Payout rules, by account size.", "Les règles de payout, par taille de compte.", "Las reglas de payout, por tamaño de cuenta."), lead, kick_in_h1=True,
                       cta=ui.btn(t(T(f"Track my {sn} payouts", f"Suivre mes payouts {sn}", f"Seguir mis payouts de {sn}")), SIGNUP, lg=True, attrs='data-track="signup_payoutrules_hero"'),
                       extra=f'<p class="fine rise d4 verified">{t(verified_of(f))}</p>' + jump)
        key = [x for x in [
            (t(T("Minimum payout", "Payout minimum", "Payout mínimo")), _span(mins, U, lang), "") if mins else None,
            (t(T("Maximum, first payout", "Maximum, premier payout", "Máximo, primer payout")), _span(caps, U, lang), t(T("before the split", "avant le partage", "antes del reparto"))) if caps else None,
            (t(T("Profit split", "Partage des profits", "Reparto de beneficios")), _span(splits, lambda v: pc(v, lang), lang), t(T("you keep", "tu gardes", "te quedas"))) if splits else None,
            (t(T("Checked", "Vérifiées le", "Revisadas el")), day(last, lang), t(T("every week", "chaque semaine", "cada semana")))] if x]
        b = ui.sec(ui.stats(key, t(T(f"{name} · every account type and size", f"{name} · tous les types et tailles de compte", f"{name} · todos los tipos y tamaños de cuenta")),
                            t(T("The range across accounts. Each account is in the tables below.", "La fourchette entre les comptes. Chaque compte est dans les tableaux ci-dessous.", "El rango entre cuentas. Cada cuenta está en las tablas de abajo."))), "t", "summary")
        # in short: one sentence per account type
        short = [f"<li><b>{p['name']}</b>{colon(lang)}{x[lang][0].lower() + x[lang][1:]}</li>" for p in progs if (x := payout_sentence(f, p, rep(p), None))]
        if short:
            b += ui.sec(f'<article class="article"><h2 id="in-short">{t(T(f"{name} payout rules in short", f"Les règles de payout {fr_de(name)} en bref", f"Las reglas de payout de {name} en resumen"))}</h2>'
                        f'<ul class="list">{"".join(short)}</ul></article>', "n", "short", width="read")
        # each account type: its payout table by size, its options, an example worked out, its sources
        secs = ""
        for n, p in enumerate(progs):
            sizes = p["sizes"]; G = _po_groups(lang, t, sizes); s = rep(p)
            note = (p.get("note") or {}).get(lang, "")
            h = T(f"{p['name']} payout rules", f"Règles de payout du {p['name']}", f"Reglas de payout de {p['name']}")
            sec = f'<h2 id="p-{p.get("id", n)}">{t(h)}</h2>' + (f"<p>{note}</p>" if note else "") + table(lang, t, sizes, G)
            for o in p.get("options") or []:
                if o.get("phase") != "funded": continue
                for c in o.get("choices") or []:
                    if c["id"] == o.get("default") or not any((((z.get("variants") or {}).get(c["id"]) or {}).get("funded") or {}).get("payout") for z in sizes): continue
                    VG = _po_groups(lang, t, sizes, (c["id"], "funded"))
                    base = [g for g in G if g[0] in [vg[0] for vg in VG]]
                    sub = (c.get("sub") or {}).get(lang, "")
                    tb = table(lang, t, sizes, VG, only_diff_from=base)
                    if tb: sec += (f'<h3>{(o.get("label") or {}).get(lang, "")} : {c["label"][lang]}</h3>'.replace(" : ", ": " if lang != "fr" else " : ")
                                   + f'<p>{sub + ". " if sub else ""}{t(T("Only the payout rules that differ from the default option:", "Seules les règles de payout qui diffèrent de l’option par défaut :", "Solo las reglas de payout que cambian respecto a la opción por defecto:"))}</p>' + tb)
            ex = _example(f, p, s, lang)
            if ex:
                sec += (f'<h3>{t(T(f"Example: {an(p["name"])} {kk(s["size"])} account", f"Exemple : un compte {p["name"]} {kk(s["size"])}", f"Ejemplo: una cuenta {p["name"]} de {kk(s["size"])}"))}</h3>'
                        + '<ul class="list">' + "".join(f"<li>{x}</li>" for x in ex) + "</ul>")
            urls = list(dict.fromkeys([u for u in p.get("payout_sources") or []] + [v["url"] for v in p.get("verified", []) if v.get("url")])) or (f.get("sources") or [])[:1]
            if urls:
                other = t(T("third-party source", "source tierce", "fuente externa"))
                sec += '<p class="fine sources">' + t(T("Sources", "Sources", "Fuentes")) + " · " + " · ".join(
                    f'<a href="{u}" rel="nofollow noopener" target="_blank">{src_name(u)}</a>' + ("" if official(f, u) else f" ({other})") for u in urls[:4]) + "</p>"
            secs += f'<div class="prog-block">{sec}</div>'
        disclaimer = T(f"Sweep is not affiliated with {name}. Payout rules can change at any time; always confirm on {poss(name)} official site before you request. Values are shown for information, from Sweep’s weekly check of {poss(name)} pages.",
                       f"Sweep n’est pas affilié à {name}. Les règles de payout peuvent changer à tout moment ; confirme toujours sur le site officiel {fr_de(name)} avant de demander. Valeurs présentées à titre indicatif, tirées de la vérification hebdomadaire des pages {fr_de(name)} par Sweep.",
                       f"Sweep no está afiliado a {name}. Las reglas de payout pueden cambiar en cualquier momento; confirma siempre en el sitio oficial de {name} antes de pedir. Valores a título informativo, tomados de la revisión semanal de las páginas de {name} por Sweep.")
        b += ui.sec(secs + f'<p class="fine" style="margin-top:40px">{t(disclaimer)}</p>', "n", "rules")
        # maximum and minimum by size, every account type side by side
        def cap_cell(po):
            lad = po.get("ladder")
            if lad:
                cs = [x for x in lad if x is not None]
                if not cs: return t(T("No cap", "Sans plafond", "Sin tope"))
                lo, hi = min(cs), max(cs)
                return (U(lo) if lo == hi else f"{U(lo)} → {U(hi)}") + (" · " + t(T("then no cap", "puis sans plafond", "luego sin tope")) if None in lad else "")
            return U(po["max"]) if po.get("max") else "—"
        mxt = _by_size_table(lang, t, f, cap_cell, T("The most you can request per payout, before the profit split. When the cap changes from one payout to the next, the first and the highest are shown.",
                                                     "Le maximum que tu peux demander par payout, avant le partage des profits. Quand le plafond change d’un payout à l’autre, le premier et le plus haut sont indiqués.",
                                                     "Lo máximo que puedes pedir por payout, antes del reparto de beneficios. Cuando el tope cambia de un payout a otro, se indican el primero y el más alto."))
        mnt = _by_size_table(lang, t, f, lambda po: U(po["min"]) if po.get("min") else "—", T("The smallest payout you can request. Below it, the request isn’t accepted.",
                                                                                              "Le plus petit payout que tu peux demander. En dessous, la demande n’est pas acceptée.",
                                                                                              "El payout más pequeño que puedes pedir. Por debajo, la solicitud no se acepta."))
        go = lambda page, label: f'<p><a class="go" href="{href(lang, page)}">{t(label)} <span aria-hidden="true">→</span></a></p>'
        art = ""
        if mxt: art += (f'<h2 id="max-payout">{t(T(f"{name} maximum payout, by account size", f"Payout maximum chez {name}, par taille de compte", f"Payout máximo en {name}, por tamaño de cuenta"))}</h2>{mxt}'
                        + go("payout-calculator.html", T("Payout calculator: what you can request and what you keep", "Calculateur de payout : ce que tu peux demander et ce que tu gardes", "Calculadora de payout: lo que puedes pedir y lo que te quedas")))
        if mnt: art += f'<h2 id="min-payout">{t(T(f"{name} minimum payout", f"Payout minimum chez {name}", f"Payout mínimo en {name}"))}</h2>{mnt}'
        art += (go(page_of(f), T(f"Every {name} rule: drawdown, daily loss limit, consistency", f"Toutes les règles {fr_de(name)} : drawdown, limite du jour, consistance", f"Todas las reglas de {name}: drawdown, límite diario, consistencia"))
                + go(GUIDE_PAYOUT, T("Payout rules of every firm, compared", "Les règles de payout de chaque firme, comparées", "Las reglas de payout de cada firma, comparadas")))
        b += ui.sec(f'<article class="article">{art}</article>', "t", "amounts", width="read")
        # in Sweep
        b += ui.split(t, T("Track it", "Suis-le", "Síguelo"), T(f"Know when your {name} payout is ready.", f"Sache quand ton payout {name} est prêt.", f"Sabe cuándo tu payout de {name} está listo."),
                   T(f"Pick {name} and your account type: these payout rules fill in, and Sweep counts what’s done and what’s missing after every trade.",
                     f"Choisis {name} et ton type de compte : ces règles de payout se remplissent, et Sweep compte ce qui est fait et ce qui manque après chaque trade.",
                     f"Elige {name} y tu tipo de cuenta: estas reglas de payout se completan y Sweep cuenta lo hecho y lo que falta después de cada operación."),
                   [T("<b>Payout conditions counted</b> on every trade: winning days, balance to keep, amount available", "<b>Conditions de payout comptées</b> à chaque trade : jours gagnants, solde à garder, montant disponible", "<b>Condiciones de payout contadas</b> en cada operación: días ganadores, saldo a mantener, importe disponible"),
                    T("<b>From request to paid:</b> each payout, your fees and your real net in My money", "<b>De la demande au versement :</b> chaque payout, tes frais et ton net réel dans Mon argent", "<b>De la solicitud al cobro:</b> cada payout, tus gastos y tu neto real en Mi dinero"),
                    T("<b>A rule changes?</b> You’re notified and you choose to apply it or keep yours", "<b>Une règle change ?</b> Tu es prévenu et tu choisis de l’appliquer ou de garder la tienne", "<b>¿Cambia una regla?</b> Te avisamos y eliges aplicarla o mantener la tuya")],
                   ui.frame_d("v6-08-payout-conditions-d.webp", t(T("Payout conditions for a prop account, sample data", "Conditions de payout d’un compte prop, données d’exemple", "Condiciones de payout de una cuenta prop, datos de ejemplo")), m="v6-08-payout-conditions-m.webp", t=t),
                   id_="track", more=f'<div class="cta-row"><a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_payoutrules">{t(T(f"Track my {sn} payouts", f"Suivre mes payouts {sn}", f"Seguir mis payouts de {sn}"))}</a></div><p class="fine" style="margin-top:16px">{t(MONEY_PLAN)}</p>')
        # payout rule changes
        ch = _payout_changes(f)[:8]
        if ch:
            prog = {p.get("id", p["name"]): p["name"] for p in f["programs"]}
            changes = '<ul class="list">' + "".join(f'<li><b>{day(c["date"], lang)}</b> · {prog.get(c["program"], c["program"])} {kk(c["size"])} · {change_label(c["rule"], lang, t)}{colon(lang)}{change_value(c["rule"], c["old"], lang, t)} → {change_value(c["rule"], c["new"], lang, t)}</li>' for c in ch) + "</ul>"
        elif real_changes(f):
            changes = ui.state(t(T("No payout rule has changed since we started logging this firm’s changes; its other rule changes are on its rules page.",
                                   "Aucune règle de payout n’a changé depuis le début du suivi de cette firme ; ses autres changements de règles sont sur sa page de règles.",
                                   "Ninguna regla de payout ha cambiado desde que empezamos a registrar los cambios de esta firma; sus otros cambios de reglas están en su página de reglas.")))
        else:
            changes = ui.state(no_change(lang, t, f))
        allc = f'<a class="go" href="{href(lang, RULE_CHANGES)}#{slug(f)}">{t(T("Every firm’s rule changes", "Les changements de règles de toutes les firmes", "Los cambios de reglas de todas las firmas"))} <span aria-hidden="true">→</span></a>'
        b += ui.sec(f'<div class="read"><div class="head"><h2>{t(T("Payout rule changes", "Changements des règles de payout", "Cambios en las reglas de payout"))}</h2></div>{changes}<div class="links">{allc}</div></div>', "t", "changes")
        faqs = _faqs(f)
        from pages17 import chiprow
        others = [(payout_page_of(x), {l: x["name"] for l in LANGS}) for x in PAYOUT_FIRMS if x["id"] != f["id"]]
        b += (ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs)
                     + chiprow(lang, t, T("Payout rules of", "Règles de payout de", "Reglas de payout de"), others, 32), "n", "questions", width="read")
              + ui.read_next(lang, t, ["payout-tracker.html", "funded-account-playbook.html", "prop-firm-benchmark-days.html"]) + ui.final(lang, t))
        short_name = ABBR.get(f["id"], name)
        fit = lambda n, *c: next((x for x in c if len(x) <= n), c[-1])
        title = {"en": fit(60, f"{name} Payout Rules 2026: Minimum, Maximum & Split · Sweep", f"{name} Payout Rules 2026: Min, Max & Split · Sweep", f"{name} Payout Rules 2026: Min, Max & Split", f"{name} Payout Rules 2026 · Sweep", f"{short_name} Payout Rules 2026 · Sweep"),
                 "fr": fit(60, f"Règles de payout {fr_de(name)} 2026 : minimum, maximum · Sweep", f"Règles de payout {fr_de(name)} 2026 : minimum et maximum", f"Règles de payout {fr_de(name)} 2026 · Sweep", f"Règles de payout {short_name} 2026 · Sweep"),
                 "es": fit(60, f"Reglas de payout de {name} 2026: mínimo, máximo · Sweep", f"Reglas de payout de {name} 2026: mínimo y máximo", f"Reglas de payout de {name} 2026 · Sweep", f"Reglas de payout de {short_name} 2026 · Sweep")}[lang]
        desc = {"en": fit(158, f"{name} payout rules 2026, checked every week (last: {day(last, 'en')}): days to qualify, minimum and maximum payout by account size, profit split, with an example.",
                          f"{name} payout rules 2026, checked weekly (last: {day(last, 'en')}): days to qualify, minimum and maximum payout by account size, profit split.",
                          f"{name} payout rules 2026, checked weekly ({day(last, 'en')}): days to qualify, minimum and maximum payout, profit split."),
                "fr": fit(158, f"Règles de payout {fr_de(name)} 2026, vérifiées chaque semaine (dernière : {day(last, 'fr')}) : jours requis, payout minimum et maximum par taille de compte, partage.",
                          f"Règles de payout {fr_de(name)} 2026, vérifiées chaque semaine ({day(last, 'fr')}) : jours requis, payout minimum et maximum par taille, partage.",
                          f"Règles de payout {fr_de(name)} 2026, vérifiées chaque semaine ({day(last, 'fr')}) : jours requis, minimum, maximum, partage."),
                "es": fit(158, f"Reglas de payout de {name} 2026, revisadas cada semana (última: {day(last, 'es')}): días necesarios, payout mínimo y máximo por tamaño de cuenta, reparto.",
                          f"Reglas de payout de {name} 2026, revisadas cada semana ({day(last, 'es')}): días necesarios, payout mínimo y máximo por tamaño, reparto.",
                          f"Reglas de payout de {name} 2026, revisadas cada semana ({day(last, 'es')}): días necesarios, mínimo, máximo, reparto.")}[lang]
        ld = jsonld({"@context": "https://schema.org", "@graph": [
            {"@type": "WebPage", "name": title, "inLanguage": lang, "dateModified": last, "url": f"https://{DOMAIN}{href(lang, pg)}", "about": {"@type": "Organization", "name": name, "url": (f.get("sources") or [None])[0]}},
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in faqs]}]})
        return _fr_nbsp(lang, title, desc, hero + b, ld + RSS_LINK)
    return pg, page

PAYOUT_PAGES = dict(make_payout_page(f) for f in PAYOUT_FIRMS)
