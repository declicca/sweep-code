from core import *

# symbol, name, exchange, tick size, tick value, point value, months, sibling, family
C = [
 ("NQ","E-mini Nasdaq-100","CME",0.25,5.0,20.0,"H M U Z","MNQ","idx"),
 ("MNQ","Micro E-mini Nasdaq-100","CME",0.25,0.5,2.0,"H M U Z","NQ","idx"),
 ("ES","E-mini S&P 500","CME",0.25,12.5,50.0,"H M U Z","MES","idx"),
 ("MES","Micro E-mini S&P 500","CME",0.25,1.25,5.0,"H M U Z","ES","idx"),
 ("YM","E-mini Dow ($5)","CBOT",1.0,5.0,5.0,"H M U Z","MYM","idx"),
 ("MYM","Micro E-mini Dow","CBOT",1.0,0.5,0.5,"H M U Z","YM","idx"),
 ("RTY","E-mini Russell 2000","CME",0.1,5.0,50.0,"H M U Z","M2K","idx"),
 ("M2K","Micro E-mini Russell 2000","CME",0.1,0.5,5.0,"H M U Z","RTY","idx"),
 ("CL","Crude Oil (WTI)","NYMEX",0.01,10.0,1000.0,"F G H J K M N Q U V X Z","MCL","energy"),
 ("MCL","Micro WTI Crude Oil","NYMEX",0.01,1.0,100.0,"F G H J K M N Q U V X Z","CL","energy"),
 ("GC","Gold","COMEX",0.1,10.0,100.0,"G J M Q V Z","MGC","metal"),
 ("MGC","Micro Gold","COMEX",0.1,1.0,10.0,"G J M Q V Z","GC","metal"),
 ("SI","Silver","COMEX",0.005,25.0,5000.0,"H K N U Z",None,"metal"),
 ("6E","Euro FX","CME",0.00005,6.25,125000.0,"H M U Z",None,"fx"),
]
def slug(s): return f"contracts/{s.lower()}-futures.html"

def _fmt(v):
    if v >= 1000: return f"${v:,.0f}"
    return f"${v:,.2f}".rstrip("0").rstrip(".") if v % 1 else f"${v:,.0f}"

def _tick(ts):
    return f"{ts:g}"

NOTE = T("Specifications for guidance only. Always check the official CME Group contract page before trading.",
         "Spécifications à titre indicatif. Vérifie toujours la fiche officielle du CME Group avant de trader.",
         "Especificaciones a título indicativo. Verifica siempre la ficha oficial de CME Group antes de operar.")
HOURS = T("CME Globex: Sunday to Friday, 6:00 p.m. to 5:00 p.m. New York time, with a daily one-hour break from 5:00 to 6:00 p.m.",
          "CME Globex : du dimanche au vendredi, de 18 h à 17 h heure de New York, avec une pause quotidienne d’une heure de 17 h à 18 h.",
          "CME Globex: de domingo a viernes, de 18:00 a 17:00 hora de Nueva York, con una pausa diaria de una hora de 17:00 a 18:00.")

def make_contract(sym):
    s, name, exch, ts, tv, pv, months, sib, fam = next(c for c in C if c[0] == sym)
    def page(lang, t):
        h1 = T(f"{s} futures: tick size, tick value and specs.", f"Contrat à terme {s} : taille et valeur du tick.", f"Futuros {s}: tamaño y valor del tick.")
        lead = T(f"{name} ({s}) on {exch}: one tick is {_tick(ts)} points and is worth {_fmt(tv)} per contract; one full point is worth {_fmt(pv)}.",
                 f"{name} ({s}) sur {exch} : un tick vaut {_tick(ts)} point et rapporte {_fmt(tv)} par contrat ; un point complet vaut {_fmt(pv)}.",
                 f"{name} ({s}) en {exch}: un tick son {_tick(ts)} puntos y vale {_fmt(tv)} por contrato; un punto completo vale {_fmt(pv)}.")
        hero = page_hero(t, h1, lead, T("Contract specs","Fiche contrat","Ficha del contrato"))
        rows = [(T("Symbol","Symbole","Símbolo"), s), (T("Name","Nom","Nombre"), name), (T("Exchange","Bourse","Mercado"), exch),
                (T("Tick size","Taille du tick","Tamaño del tick"), f"{_tick(ts)}"), (T("Tick value","Valeur du tick","Valor del tick"), _fmt(tv)),
                (T("Point value","Valeur du point","Valor del punto"), _fmt(pv)), (T("Contract months","Mois de contrat","Meses de contrato"), months),
                (T("Trading hours","Heures de marché","Horario"), t(HOURS))]
        tbl = '<table class="tbl specs"><tbody>' + "".join(f"<tr><th>{t(a)}</th><td{' class=\"num\"' if i in (3,4,5,6) else ''}>{b}</td></tr>" for i,(a,b) in enumerate(rows)) + "</tbody></table>"
        stops = [5, 10, 20, 40] if fam == "idx" and pv >= 5 else ([10, 20, 40, 80] if fam=="idx" else None)
        if fam == "energy": stops_t = [10, 20, 30, 50]
        elif fam == "metal": stops_t = [20, 50, 100, 200]
        elif fam == "fx": stops_t = [10, 20, 40, 80]
        else: stops_t = [int(x/ts) for x in stops]
        risk = "".join(f"<tr><td class=\"num\">{n} ticks ({n*ts:g} pts)</td><td class=\"num\">{_fmt(n*tv)}</td><td class=\"num\">{_fmt(n*tv*5)}</td></tr>" for n in stops_t)
        rtbl = (f'<table class="tbl risk"><thead><tr><th>{t(T("Stop","Stop","Stop"))}</th><th>{t(T("1 contract","1 contrat","1 contrato"))}</th><th>{t(T("5 contracts","5 contrats","5 contratos"))}</th></tr></thead><tbody>{risk}</tbody></table>')
        sibl = ""
        if sib:
            ratio = T(f"{sib} is the {'micro' if len(sib) > len(s) else 'full-size'} version of {s}: one {s} = {('10 ' + sib) if len(sib) > len(s) else ('1/10 ' + sib)}.",
                      f"{sib} est la version {'micro' if len(sib) > len(s) else 'standard'} de {s} : un {s} = {('10 ' + sib) if len(sib) > len(s) else ('1/10 de ' + sib)}.",
                      f"{sib} es la versión {'micro' if len(sib) > len(s) else 'estándar'} de {s}: un {s} = {('10 ' + sib) if len(sib) > len(s) else ('1/10 de ' + sib)}.")
            sibl = f'<p class="lead" style="margin-top:20px">{t(ratio)} <a href="{href(lang, slug(sib))}">{sib} →</a></p>'
        calc = f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"position-size-calculator.html")}?sym={s}">{t(T(f"Position size calculator for {s}",f"Calculateur de taille de position pour {s}",f"Calculadora de tamaño de posición para {s}"))}</a></div>'
        b = (f'<section style="padding-top:8px"><div class="wrap narrow">{tbl}<p class="fine">{t(NOTE)}</p>{sibl}</div></section>'
             f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T(f"What a stop costs on {s}",f"Ce que coûte un stop sur {s}",f"Lo que cuesta un stop en {s}"))}</h2></div>{rtbl}{calc}</div></section>'
             f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T(f"Journal your {s} trades.",f"Journalise tes trades {s}.",f"Registra tus operaciones de {s}."))}</h2>'
             f'<p class="lead">{t(T(f"Sweep knows the {s} tick value: your net P&L and R are exact, and every trade shows on real CME candles.",f"Sweep connaît la valeur du tick {s} : ton P&L net et ton R sont exacts, et chaque trade s’affiche sur de vraies bougies CME.",f"Sweep conoce el valor del tick de {s}: tu P&L neto y tu R son exactos, y cada operación se ve sobre velas reales de CME."))}</p></div>'
             f'<p class="firm-others"><span>{t(T("Other contracts","Autres contrats","Otros contratos"))}</span>' + "".join(f'<a href="{href(lang,slug(c[0]))}">{c[0]}</a>' for c in C if c[0] != s) + '</p></div></section>')
        faqs = [(T(f"What is the tick value of {s}?",f"Quelle est la valeur du tick de {s} ?",f"¿Cuál es el valor del tick de {s}?"),
                 T(f"One {s} tick ({_tick(ts)}) is worth {_fmt(tv)} per contract.",f"Un tick {s} ({_tick(ts)}) vaut {_fmt(tv)} par contrat.",f"Un tick de {s} ({_tick(ts)}) vale {_fmt(tv)} por contrato.")),
                (T(f"How much is one point of {s} worth?",f"Combien vaut un point de {s} ?",f"¿Cuánto vale un punto de {s}?"),
                 T(f"One full point is worth {_fmt(pv)} per contract.",f"Un point complet vaut {_fmt(pv)} par contrat.",f"Un punto completo vale {_fmt(pv)} por contrato."))]
        b += f'<section class="rule"><div class="wrap narrow">{"".join(faq_item(t,q,a) for q,a in faqs)}</div></section>'
        ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in faqs]})
        return (t(T(f"{s} futures tick value, tick size and contract specs · Sweep",f"{s} : valeur du tick, taille et spécifications · Sweep",f"{s}: valor del tick, tamaño y especificaciones · Sweep")),
                t(T(f"{name} ({s}) futures: tick size {_tick(ts)}, tick value {_fmt(tv)}, point value {_fmt(pv)}, trading hours and what a stop costs.",
                    f"Contrat {name} ({s}) : tick de {_tick(ts)}, valeur du tick {_fmt(tv)}, valeur du point {_fmt(pv)}, heures de marché et coût d’un stop.",
                    f"Futuros {name} ({s}): tick de {_tick(ts)}, valor del tick {_fmt(tv)}, valor del punto {_fmt(pv)}, horario y coste de un stop.")),
                hero + b + final_cta(lang, t), ld)
    return page

def page_contracts(lang, t):
    hero = page_hero(t, T("CME futures contract specs.","Fiches des contrats à terme CME.","Fichas de los contratos de futuros de CME."),
        T("Tick size, tick value and point value for the 14 contracts Sweep charts.","Taille du tick, valeur du tick et valeur du point pour les 14 contrats que Sweep affiche en graphique.","Tamaño del tick, valor del tick y valor del punto para los 14 contratos que Sweep muestra en gráfico."), T("Contract specs","Fiches contrats","Fichas"))
    rows = "".join(f'<tr><th><a href="{href(lang,slug(s))}">{s}</a></th><td>{n}</td><td class="num">{_tick(ts)}</td><td class="num">{_fmt(tv)}</td><td class="num">{_fmt(pv)}</td></tr>' for s,n,_,ts,tv,pv,_,_,_ in C)
    tbl = (f'<div class="cmp-wrap"><table class="cmp"><thead><tr><th>{t(T("Symbol","Symbole","Símbolo"))}</th><th>{t(T("Name","Nom","Nombre"))}</th><th>{t(T("Tick","Tick","Tick"))}</th><th>{t(T("Tick value","Valeur du tick","Valor del tick"))}</th><th>{t(T("Point value","Valeur du point","Valor del punto"))}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    b = f'<section style="padding-top:8px"><div class="wrap">{tbl}<p class="fine">{t(NOTE)}</p></div></section>'
    return (t(T("CME futures tick values: NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep","Valeurs de tick CME : NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep","Valores de tick de CME: NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep")),
            t(T("Tick size, tick value and point value for NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI and 6E futures.","Taille, valeur du tick et valeur du point pour NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI et 6E.","Tamaño, valor del tick y valor del punto para NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI y 6E.")),
            hero + b + final_cta(lang, t), "")
