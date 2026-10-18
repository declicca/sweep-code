from core import *
import ui

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

def _fmt(v, lang="en"):
    """Money as the rest of the site writes it: $12.50, 12,50 $ (FR), 12,50 $ (ES); thousands 1,000 / 1 000 / 1.000."""
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"
    if lang == "en": return "$" + s
    return s.replace(",", "\0").replace(".", ",").replace("\0", "\u202f" if lang == "fr" else ".") + "\u00a0$"

def _tick(ts, lang="en"):
    """A price step without scientific notation (0.00005, not 5e-05), with a decimal comma in FR and ES."""
    x = ("%.5f" % ts).rstrip("0").rstrip(".")
    return x if lang == "en" else x.replace(".", ",")

NOTE = T("Specifications for guidance only. Always check the official CME Group contract page before trading.",
         "Spécifications à titre indicatif. Vérifie toujours la fiche officielle du CME Group avant de trader.",
         "Especificaciones a título indicativo. Verifica siempre la ficha oficial de CME Group antes de operar.")
HOURS = T("CME Globex: Sunday to Friday, 6:00 p.m. to 5:00 p.m. New York time, with a daily one-hour break from 5:00 to 6:00 p.m.",
          "CME Globex : du dimanche au vendredi, de 18 h à 17 h heure de New York, avec une pause quotidienne d’une heure de 17 h à 18 h.",
          "CME Globex: de domingo a viernes, de 18:00 a 17:00 hora de Nueva York, con una pausa diaria de una hora de 17:00 a 18:00.")

# when each family trades most, and the scheduled releases that move it (links: @page.html, localized per language)
ACTIVE = {
 "idx": T("{s} trades nearly 24 hours a day on CME Globex, but most of its volume comes during the New York cash session, from 9:30 a.m. to 4:00 p.m. New York time. The first hour after the 9:30 open is usually the most active, and activity picks up again into the close. Overnight, the market stays open with lower volume.",
          "{s} se négocie presque 24 h sur 24 sur CME Globex, mais l’essentiel de son volume se fait pendant la séance au comptant de New York, de 9 h 30 à 16 h, heure de New York. La première heure après l’ouverture de 9 h 30 est généralement la plus active, et l’activité reprend à l’approche de la clôture. La nuit, le marché reste ouvert avec moins de volume.",
          "{s} cotiza casi las 24 horas en CME Globex, pero la mayor parte de su volumen llega durante la sesión de contado de Nueva York, de 9:30 a 16:00 hora de Nueva York. La primera hora tras la apertura de las 9:30 suele ser la más activa, y la actividad vuelve a subir hacia el cierre. Por la noche, el mercado sigue abierto con menos volumen."),
 "energy": T("{s} trades nearly 24 hours a day on CME Globex, but volume is highest during the New York day session, from 9:00 a.m. to the 2:30 p.m. settlement, New York time. Outside those hours, moves can come from headlines with fewer contracts behind them.",
             "{s} se négocie presque 24 h sur 24 sur CME Globex, mais le volume est le plus fort pendant la séance de jour de New York, de 9 h au règlement de 14 h 30, heure de New York. En dehors de ces heures, les mouvements peuvent venir de nouvelles, avec moins de contrats derrière.",
             "{s} cotiza casi las 24 horas en CME Globex, pero el volumen es mayor durante la sesión diurna de Nueva York, de 9:00 a la liquidación de las 14:30, hora de Nueva York. Fuera de ese horario, los movimientos pueden venir de noticias, con menos contratos detrás."),
 "metal": T("{s} trades nearly 24 hours a day. Volume builds with London in the early morning and peaks when London and New York overlap, roughly 8:00 a.m. to noon New York time, before the COMEX settlement in the early afternoon.",
            "{s} se négocie presque 24 h sur 24. Le volume monte avec Londres tôt le matin et culmine quand Londres et New York se chevauchent, environ de 8 h à midi, heure de New York, avant le règlement du COMEX en début d’après-midi.",
            "{s} cotiza casi las 24 horas. El volumen crece con Londres a primera hora y llega a su máximo cuando Londres y Nueva York coinciden, más o menos de 8:00 a mediodía hora de Nueva York, antes de la liquidación del COMEX a primera hora de la tarde."),
 "fx": T("{s} follows the euro against the dollar. It is most active during the London session and above all when London and New York overlap, roughly 8:00 a.m. to noon New York time.",
         "{s} suit l’euro contre le dollar. Il est le plus actif pendant la séance de Londres, et surtout quand Londres et New York se chevauchent, environ de 8 h à midi, heure de New York.",
         "{s} sigue al euro frente al dólar. Tiene más actividad durante la sesión de Londres y, sobre todo, cuando Londres y Nueva York coinciden, más o menos de 8:00 a mediodía hora de Nueva York."),
}
MOVERS = {
 "idx": T("U.S. data released at 8:30 a.m. New York time, before the open, often sets the tone: <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a>, <a href=\"@pce-release-dates.html\">PCE</a>, PPI, GDP and retail sales. <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions at 2:00 p.m. move the whole index complex, and ISM at 10:00 a.m. lands in the middle of the morning session.",
          "Les données américaines publiées à 8 h 30, heure de New York, avant l’ouverture, donnent souvent le ton : <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">emploi (NFP)</a>, <a href=\"@pce-release-dates.html\">PCE</a>, PPI, PIB et ventes au détail. Les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a> à 14 h font bouger tous les indices, et l’ISM de 10 h tombe en pleine séance du matin.",
          "Los datos de EE. UU. publicados a las 8:30 hora de Nueva York, antes de la apertura, suelen marcar el tono: <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">empleo (NFP)</a>, <a href=\"@pce-release-dates.html\">PCE</a>, PPI, PIB y ventas minoristas. Las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a> a las 14:00 mueven todos los índices, y el ISM de las 10:00 llega en plena sesión de la mañana."),
 "energy": T("The EIA weekly petroleum status report, on Wednesdays at 10:30 a.m. New York time (a day later in holiday weeks), is the main scheduled release for crude; the API’s private estimate comes out the day before, on Tuesdays at 4:30 p.m. OPEC+ meetings and U.S. data such as <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a> and <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions matter too.",
             "Le rapport hebdomadaire de l’EIA sur les stocks de pétrole, le mercredi à 10 h 30, heure de New York (un jour plus tard les semaines de congé), est la principale publication prévue pour le brut ; l’estimation privée de l’API sort la veille, le mardi à 16 h 30. Les réunions de l’OPEP+ et les données américaines comme le <a href=\"@cpi-release-dates.html\">CPI</a>, l’<a href=\"@nfp-release-dates.html\">emploi (NFP)</a> et les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a> comptent aussi.",
             "El informe semanal de la EIA sobre inventarios de petróleo, los miércoles a las 10:30 hora de Nueva York (un día después en semanas festivas), es la principal publicación prevista para el crudo; la estimación privada del API sale el día anterior, los martes a las 16:30. Las reuniones de la OPEP+ y los datos de EE. UU. como el <a href=\"@cpi-release-dates.html\">CPI</a>, el <a href=\"@nfp-release-dates.html\">empleo (NFP)</a> y las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a> también cuentan."),
 "metal": T("Precious metals react to anything that moves interest rates and the dollar: <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a>, <a href=\"@pce-release-dates.html\">PCE</a> and <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions above all. The 8:30 a.m. releases land in the middle of the busiest hours.",
            "Les métaux précieux réagissent à tout ce qui fait bouger les taux d’intérêt et le dollar : le <a href=\"@cpi-release-dates.html\">CPI</a>, l’<a href=\"@nfp-release-dates.html\">emploi (NFP)</a>, le <a href=\"@pce-release-dates.html\">PCE</a> et surtout les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a>. Les publications de 8 h 30 tombent en pleine période la plus active.",
            "Los metales preciosos reaccionan a todo lo que mueve los tipos de interés y el dólar: el <a href=\"@cpi-release-dates.html\">CPI</a>, el <a href=\"@nfp-release-dates.html\">empleo (NFP)</a>, el <a href=\"@pce-release-dates.html\">PCE</a> y, sobre todo, las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a>. Los datos de las 8:30 llegan en plenas horas de más actividad."),
 "fx": T("Both sides of the pair matter: U.S. data such as <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a> and <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions, and on the euro side, European Central Bank rate decisions and eurozone inflation.",
         "Les deux côtés de la paire comptent : les données américaines comme le <a href=\"@cpi-release-dates.html\">CPI</a>, l’<a href=\"@nfp-release-dates.html\">emploi (NFP)</a> et les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a>, et du côté de l’euro, les décisions de taux de la Banque centrale européenne et l’inflation de la zone euro.",
         "Cuentan los dos lados del par: los datos de EE. UU. como el <a href=\"@cpi-release-dates.html\">CPI</a>, el <a href=\"@nfp-release-dates.html\">empleo (NFP)</a> y las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a>, y del lado del euro, las decisiones de tipos del Banco Central Europeo y la inflación de la eurozona."),
}
STOP_PTS = {"NQ": 20, "MNQ": 20, "ES": 5, "MES": 5, "YM": 40, "MYM": 40, "RTY": 5, "M2K": 5, "CL": 0.2, "MCL": 0.2, "GC": 5, "MGC": 5, "SI": 0.1, "6E": 0.002}   # example stop, in points
SIZE = {"SI": T("One SI contract is 5,000 troy ounces of silver: each {ts} tick is worth {tv}, and a full {one} move is worth {pv} per contract. With $500 of risk per trade, a stop can’t be wider than 20 ticks (0.10). CME also lists a smaller Micro Silver contract (SIL, 1,000 ounces, one fifth of SI).",
                "Un contrat SI, c’est 5 000 onces troy d’argent : chaque tick de {ts} vaut {tv}, et un mouvement complet de {one} vaut {pv} par contrat. Avec 500 $ de risque par trade, un stop ne peut pas dépasser 20 ticks (0,10). Le CME propose aussi un contrat plus petit, le Micro Silver (SIL, 1 000 onces, un cinquième de SI).",
                "Un contrato SI son 5.000 onzas troy de plata: cada tick de {ts} vale {tv}, y un movimiento completo de {one} vale {pv} por contrato. Con 500 $ de riesgo por operación, un stop no puede superar los 20 ticks (0,10). CME también ofrece un contrato más pequeño, el Micro Silver (SIL, 1.000 onzas, una quinta parte de SI)."),
        "6E": T("One 6E contract is €125,000: each {ts} tick is worth {tv}, and a one-cent move (0.0100) is worth $1,250 per contract. With $500 of risk per trade, a stop can’t be wider than 80 ticks (0.0040). CME also lists a smaller E-micro EUR/USD contract (M6E, €12,500, one tenth of 6E).",
                "Un contrat 6E, c’est 125 000 € : chaque tick de {ts} vaut {tv}, et un mouvement d’un cent (0,0100) vaut 1 250 $ par contrat. Avec 500 $ de risque par trade, un stop ne peut pas dépasser 80 ticks (0,0040). Le CME propose aussi un contrat plus petit, l’E-micro EUR/USD (M6E, 12 500 €, un dixième de 6E).",
                "Un contrato 6E son 125.000 €: cada tick de {ts} vale {tv}, y un movimiento de un centavo (0,0100) vale 1.250 $ por contrato. Con 500 $ de riesgo por operación, un stop no puede superar los 80 ticks (0,0040). CME también ofrece un contrato más pequeño, el E-micro EUR/USD (M6E, 12.500 €, una décima parte de 6E).")}
RISK = 500   # risk per trade used in the worked example
MAX_LOSS = 2000   # the max loss of a 50K evaluation, a common size, in the prop firm paragraph

def make_contract(sym):
    s, name, exch, ts, tv, pv, months, sib, fam = next(c for c in C if c[0] == sym)
    CRUMBS[slug(s)] = T(f"{s} futures", f"Futures {s}", f"Futuros {s}")
    SYSTEM_PAGES.add(slug(s))
    def page(lang, t):
        F = lambda v: _fmt(v, lang); K = lambda v: _tick(v, lang)
        loc = lambda x: re.sub(r'href="@([^"]+)"', lambda m: f'href="{href(lang, m.group(1))}"', x)
        h1 = T(f"{s} futures: tick size, tick value and specs.", f"Contrat à terme {s} : taille et valeur du tick.", f"Futuros {s}: tamaño y valor del tick.")
        lead = T(f"{name} ({s}) on {exch}: one tick is {K(ts)} points and is worth {F(tv)} per contract; one full point is worth {F(pv)}.",
                 f"{name} ({s}) sur {exch} : un tick vaut {K(ts)} point et rapporte {F(tv)} par contrat ; un point complet vaut {F(pv)}.",
                 f"{name} ({s}) en {exch}: un tick son {K(ts)} puntos y vale {F(tv)} por contrato; un punto completo vale {F(pv)}.")
        hero = ui.hero(t, T("Contract specs","Fiche contrat","Ficha del contrato"), h1, lead)
        key = ui.stats([(t(T("Tick size","Taille du tick","Tamaño del tick")), K(ts), ""), (t(T("Tick value","Valeur du tick","Valor del tick")), F(tv), ""), (t(T("Point value","Valeur du point","Valor del punto")), F(pv), "")])   # the three numbers first; the rest of the sheet under them
        rows = [(T("Symbol","Symbole","Símbolo"), s), (T("Name","Nom","Nombre"), name), (T("Exchange","Bourse","Mercado"), exch),
                (T("Contract months","Mois de contrat","Meses de contrato"), f'<span class="num">{months}</span>'), (T("Trading hours","Heures de marché","Horario"), t(HOURS))]
        tbl = '<table class="tbl specs"><tbody>' + "".join(f"<tr><th>{t(a)}</th><td>{b}</td></tr>" for a, b in rows) + "</tbody></table>"
        stops = [5, 10, 20, 40] if fam == "idx" and pv >= 5 else ([10, 20, 40, 80] if fam=="idx" else None)
        if fam == "energy": stops_t = [10, 20, 30, 50]
        elif fam == "metal": stops_t = [20, 50, 100, 200]
        elif fam == "fx": stops_t = [10, 20, 40, 80]
        else: stops_t = [int(x/ts) for x in stops]
        risk = "".join(f"<tr><th scope=\"row\">{n} ticks <small>({K(round(n*ts, 6))} pts)</small></th><td>{F(n*tv)}</td><td>{F(n*tv*5)}</td></tr>" for n in stops_t)
        rtbl = (f'<div class="cmp-wrap"><table class="cmp risk"><thead><tr><th>{t(T("Stop","Stop","Stop"))}</th><th>{t(T("1 contract","1 contrat","1 contrato"))}</th><th>{t(T("5 contracts","5 contrats","5 contratos"))}</th></tr></thead><tbody>{risk}</tbody></table></div>')
        calc = f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"position-size-calculator.html")}?sym={s}">{t(T(f"Position size calculator for {s}",f"Calculateur de taille de position pour {s}",f"Calculadora de tamaño de posición para {s}"))}</a></div>'
        # trading it: when it moves, mini or micro, what moves it, a worked stop
        big, mic = (s, sib) if sib and len(sib) > len(s) else (sib, s)
        if sib:
            cb, cm = next(c for c in C if c[0] == big), next(c for c in C if c[0] == mic)
            size_h = T(f"{big} or {mic}", f"{big} ou {mic}", f"{big} o {mic}")
            if s == mic:   # each twin tells its own side: the micro page why the micro, the mini page why the mini
                size_p = T(f"{mic} is the micro version of {big}: one {big} equals 10 {mic}, and every tick is worth ten times less ({F(cm[4])} instead of {F(cb[4])}). The price and the chart are the same; only the size changes. When one {big} is too much risk for your stop, 2 to 9 {mic} fill the gap. Micros also let you exit in steps, one contract at a time, where a single {big} can’t be split.",
                           f"{mic} est la version micro de {big} : un {big} équivaut à 10 {mic}, et chaque tick vaut dix fois moins ({F(cm[4])} au lieu de {F(cb[4])}). Le prix et le graphique sont les mêmes ; seule la taille change. Quand un {big} représente trop de risque pour ton stop, 2 à 9 {mic} comblent l’écart. Les micros permettent aussi de sortir par étapes, un contrat à la fois, là où un seul {big} ne se divise pas.",
                           f"{mic} es la versión micro de {big}: un {big} equivale a 10 {mic}, y cada tick vale diez veces menos ({F(cm[4])} en lugar de {F(cb[4])}). El precio y el gráfico son los mismos; solo cambia el tamaño. Cuando un {big} es demasiado riesgo para tu stop, de 2 a 9 {mic} cubren la diferencia. Los micros también permiten salir por partes, un contrato cada vez, donde un solo {big} no se puede dividir.")
            else:
                size_p = T(f"{big} is the full-size contract; {mic} is its micro, one tenth of it: one {big} equals 10 {mic}, and a tick is worth {F(cb[4])} on {big} against {F(cm[4])} on {mic}. The price and the chart are the same. Once your stop fits one {big}, a single order replaces ten micros: one fill and one commission instead of ten.",
                           f"{big} est le contrat de taille normale ; {mic} est sa version micro, dix fois plus petite : un {big} équivaut à 10 {mic}, et un tick vaut {F(cb[4])} sur {big} contre {F(cm[4])} sur {mic}. Le prix et le graphique sont les mêmes. Quand ton stop tient sur un {big}, un seul ordre remplace dix micros : une exécution et une commission au lieu de dix.",
                           f"{big} es el contrato de tamaño normal; {mic} es su versión micro, diez veces más pequeña: un {big} equivale a 10 {mic}, y un tick vale {F(cb[4])} en {big} frente a {F(cm[4])} en {mic}. El precio y el gráfico son los mismos. Cuando tu stop cabe en un {big}, una sola orden sustituye a diez micros: una ejecución y una comisión en lugar de diez.")
            size_p = {l: size_p[l] + f' <a href="{href(l, slug(sib))}">{sib} →</a>' for l in LANGS}
        else:
            size_h = T("Contract size", "Taille du contrat", "Tamaño del contrato")
            size_p = {l: SIZE[s][l].format(ts=_tick(ts, l), tv=_fmt(tv, l), pv=_fmt(pv, l), one=_fmt(1, l)) for l in LANGS}
        pts = STOP_PTS[s]; ticks = round(pts / ts); cost = ticks * tv; n = int(RISK // cost + 1e-9)
        ct = lambda k: t(T("contract" if k == 1 else "contracts", "contrat" if k == 1 else "contrats", "contrato" if k == 1 else "contratos"))
        ex = T(f"A {K(pts)}-point stop on {s} is {ticks} ticks × {F(tv)} = {F(cost)} per contract. With {F(RISK)} of risk per trade, that’s {n} {ct(n)}, {F(n * cost)} at risk.",
               f"Un stop de {K(pts)} point{'s' if pts >= 2 else ''} sur {s}, c’est {ticks} ticks × {F(tv)} = {F(cost)} par contrat. Avec {F(RISK)} de risque par trade, ça fait {n} {ct(n)}, soit {F(n * cost)} de risque.",
               f"Un stop de {K(pts)} puntos en {s} son {ticks} ticks × {F(tv)} = {F(cost)} por contrato. Con {F(RISK)} de riesgo por operación, {"es" if n == 1 else "son"} {n} {ct(n)}, con {F(n * cost)} en riesgo.")
        if sib:
            c2 = next(c for c in C if c[0] == sib); cost2 = ticks * c2[4]; n2 = int(RISK // cost2 + 1e-9)
            ex = {l: ex[l] + " " + {"en": f"On {sib}, the same stop costs {_fmt(cost2, l)} per contract: {n2} {('contract' if n2 == 1 else 'contracts')}, {_fmt(n2 * cost2, l)} at risk.",
                                    "fr": f"Sur {sib}, le même stop coûte {_fmt(cost2, l)} par contrat : {n2} {('contrat' if n2 == 1 else 'contrats')}, soit {_fmt(n2 * cost2, l)} de risque.",
                                    "es": f"En {sib}, el mismo stop cuesta {_fmt(cost2, l)} por contrato: {n2} {('contrato' if n2 == 1 else 'contratos')}, con {_fmt(n2 * cost2, l)} en riesgo."}[l] for l in LANGS}
        # on a 50K evaluation: how much of the max loss that stop uses, and how many contracts keep a loss under a tenth of it
        pct = round(cost / MAX_LOSS * 100, 1); pcs = lambda l: (f"{pct:g}" if l == "en" else f"{pct:g}".replace(".", ",")); k = int(MAX_LOSS / 10 // cost + 1e-9)
        smaller = mic if sib and s == big else ""
        prop_p = T(f"On a 50K evaluation with a {F(MAX_LOSS)} max loss, a common size, that {K(pts)}-point stop costs {F(cost)} per contract: {pcs('en')}% of the whole allowance on one trade. "
                   + (f"To keep each loss under a tenth of it ({F(MAX_LOSS / 10)}), trade at most {k} {'contract' if k == 1 else 'contracts'}." if k else f"Even one contract risks more than a tenth of it ({F(MAX_LOSS / 10)}): tighten the stop{' or trade ' + smaller if smaller else ''}."),
                   f"Sur une évaluation de 50K avec une perte max de {F(MAX_LOSS)}, une taille courante, ce stop de {K(pts)} point{'s' if pts >= 2 else ''} coûte {F(cost)} par contrat : {pcs('fr')} % de toute la marge sur un seul trade. "
                   + (f"Pour garder chaque perte sous le dixième de cette marge ({F(MAX_LOSS / 10)}), trade au plus {k} {'contrat' if k == 1 else 'contrats'}." if k else f"Même un seul contrat risque plus du dixième de cette marge ({F(MAX_LOSS / 10)}) : resserre le stop{' ou passe à ' + smaller if smaller else ''}."),
                   f"En una evaluación de 50K con una pérdida máxima de {F(MAX_LOSS)}, un tamaño habitual, ese stop de {K(pts)} puntos cuesta {F(cost)} por contrato: el {pcs('es')} % de todo el margen en una sola operación. "
                   + (f"Para mantener cada pérdida por debajo de la décima parte de ese margen ({F(MAX_LOSS / 10)}), opera como máximo {k} {'contrato' if k == 1 else 'contratos'}." if k else f"Incluso un solo contrato arriesga más de la décima parte de ese margen ({F(MAX_LOSS / 10)}): ajusta el stop{' o pasa a ' + smaller if smaller else ''}."))
        art = (f'<h2>{t(T(f"When {s} is most active", f"Quand {s} est le plus actif", f"Cuándo tiene {s} más actividad"))}</h2><p>{t(ACTIVE[fam]).replace("{s}", s)}</p>'
               f'<h2>{t(size_h)}</h2><p>{t(size_p)}</p>'
               f'<h2>{t(T(f"What moves {s}", f"Ce qui fait bouger {s}", f"Qué mueve {s}"))}</h2><p>{loc(t(MOVERS[fam]))} '
               + t(T(f'Check the <a href="{href("en", "release-dates.html")}">release dates</a> before you plan the day.', f'Vérifie les <a href="{href("fr", "release-dates.html")}">dates des annonces</a> avant de planifier ta journée.', f'Revisa las <a href="{href("es", "release-dates.html")}">fechas de publicación</a> antes de planificar el día.')) + '</p>'
               f'<h2>{t(T("Example","Exemple","Ejemplo"))}</h2><p>{t(ex)}</p>'
               f'<h2>{t(T(f"{s} on a prop firm account", f"{s} sur un compte de prop firm", f"{s} en una cuenta de prop firm"))}</h2><p>{t(prop_p)}</p>')
        band = ui.band(t(T(f"Journal your {s} trades.",f"Journalise tes trades {s}.",f"Registra tus operaciones de {s}.")),
                       t(T(f"Sweep knows the {s} tick value: your net P&L and R are exact, and every trade shows on real CME candles.",f"Sweep connaît la valeur du tick {s} : ton P&L net et ton R sont exacts, et chaque trade s’affiche sur de vraies bougies CME.",f"Sweep conoce el valor del tick de {s}: tu P&L neto y tu R son exactos, y cada operación se ve sobre velas reales de CME.")),
                       ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_contract"'))
        others = (f'<div class="chiprow" style="margin-top:40px"><span class="eyebrow">{t(T("Other contracts","Autres contrats","Otros contratos"))}</span>'
                  + "".join(f'<a class="chip" href="{href(lang,slug(c[0]))}">{c[0]}</a>' for c in C if c[0] != s) + "</div>")
        faqs = [(T(f"What is the tick value of {s}?",f"Quelle est la valeur du tick de {s} ?",f"¿Cuál es el valor del tick de {s}?"),
                 T(f"One {s} tick ({_tick(ts)}) is worth {_fmt(tv)} per contract.",f"Un tick {s} ({_tick(ts, 'fr')}) vaut {_fmt(tv, 'fr')} par contrat.",f"Un tick de {s} ({_tick(ts, 'es')}) vale {_fmt(tv, 'es')} por contrato.")),
                (T(f"How much is one point of {s} worth?",f"Combien vaut un point de {s} ?",f"¿Cuánto vale un punto de {s}?"),
                 T(f"One full point is worth {_fmt(pv)} per contract.",f"Un point complet vaut {_fmt(pv, 'fr')} par contrat.",f"Un punto completo vale {_fmt(pv, 'es')} por contrato."))]
        b = (ui.sec(key + tbl + f'<p class="fine" style="margin-top:16px">{t(NOTE)}</p>', "t", "specs", width="read")
             + ui.sec(ui.head(t, None, T(f"What a stop costs on {s}",f"Ce que coûte un stop sur {s}",f"Lo que cuesta un stop en {s}")) + rtbl + calc, "n", "stops", width="read")
             + ui.sec(f'<article class="article">{art}</article>' + ui.head(t, None, T("Questions","Questions","Preguntas")) + ui.qa(t, faqs), "n", "trading", width="read")
             + ui.sec(band + others, "t", "journal"))
        ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in faqs]})
        return (t(T(f"{s} futures tick value, tick size and contract specs · Sweep",f"{s} : valeur du tick, taille et spécifications · Sweep",f"{s}: valor del tick, tamaño y especificaciones · Sweep")),
                t(T(f"{name} ({s}) futures: tick size {_tick(ts)}, tick value {_fmt(tv)}, point value {_fmt(pv)}, trading hours and what a stop costs, for prop traders.",
                    f"Contrat {name} ({s}) : tick de {_tick(ts, 'fr')}, valeur du tick {_fmt(tv, 'fr')}, valeur du point {_fmt(pv, 'fr')}, heures de marché et coût d’un stop, pour les traders prop.",
                    f"Futuros {name} ({s}): tick de {_tick(ts, 'es')}, valor del tick {_fmt(tv, 'es')}, valor del punto {_fmt(pv, 'es')}, horario y coste de un stop, para traders prop.")),
                hero + b + ui.final(lang, t), ld)
    return page

def page_contracts(lang, t):
    hero = ui.hero(t, T("Contract specs","Fiches contrats","Fichas"), T("CME futures contract specs.","Fiches des contrats à terme CME.","Fichas de los contratos de futuros de CME."),
        T("Tick size, tick value and point value for the 14 contracts Sweep charts.","Taille du tick, valeur du tick et valeur du point pour les 14 contrats que Sweep affiche en graphique.","Tamaño del tick, valor del tick y valor del punto para los 14 contratos que Sweep muestra en gráfico."))
    L = [t(T("Name","Nom","Nombre")), t(T("Tick","Tick","Tick")), t(T("Tick value","Valeur du tick","Valor del tick")), t(T("Point value","Valeur du point","Valor del punto"))]
    rows = "".join(f'<tr><th scope="row"><a href="{href(lang,slug(s))}">{s}</a></th><td data-label="{L[0]}">{n}</td><td class="num" data-label="{L[1]}">{_tick(ts, lang)}</td><td class="num" data-label="{L[2]}">{_fmt(tv, lang)}</td><td class="num" data-label="{L[3]}">{_fmt(pv, lang)}</td></tr>' for s,n,_,ts,tv,pv,_,_,_ in C)
    tbl = (f'<div class="cmp-wrap"><table class="cmp guide specs-all"><thead><tr><th scope="col">{t(T("Symbol","Symbole","Símbolo"))}</th>' + "".join(f'<th scope="col">{x}</th>' for x in L) + f'</tr></thead><tbody>{rows}</tbody></table></div>')
    guide = T("""<h2>How to read a contract spec</h2><ul>
<li><b>Tick size.</b> The smallest price step: 0.25 points on NQ and ES, 1 point on YM, 0.01 on crude oil.</li>
<li><b>Tick value.</b> What one tick is worth per contract. Your P&L is ticks × tick value × contracts.</li>
<li><b>Point value.</b> What a full one-point move is worth: tick value ÷ tick size, so $5 ÷ 0.25 = $20 on NQ.</li>
<li><b>Micro contracts.</b> MNQ, MES, MYM, M2K, MCL and MGC are one tenth of their mini: same price, same chart, ticks worth ten times less.</li></ul>
<h2>Contract months and rollover</h2><p>Each letter is a delivery month: F January, G February, H March, J April, K May, M June, N July, Q August, U September, V October, X November, Z December. The year follows: NQZ6 is the December 2026 Nasdaq-100 contract.</p>
<p>Equity index futures expire every quarter, on the third Friday of March, June, September and December. Volume moves to the next contract about a week before, which is when most traders roll. Crude oil has a contract for every month, and gold trades mostly in its even months.</p>
<h2>Why it matters on a prop account</h2><p>Your firm’s max loss is in dollars, but your stop is in points. The point value turns one into the other: a $2,000 max loss is 100 points on one NQ, 40 points on one ES and 1,000 points on one MNQ. It tells you how many losing trades your account can take before the limit, and the <a href="@position-size-calculator.html">position size calculator</a> does the math for any stop.</p>""",
"""<h2>Comment lire une fiche contrat</h2><ul>
<li><b>Taille du tick.</b> Le plus petit pas de prix : 0,25 point sur NQ et ES, 1 point sur YM, 0,01 sur le pétrole brut.</li>
<li><b>Valeur du tick.</b> Ce que vaut un tick par contrat. Ton P&L, c’est ticks × valeur du tick × contrats.</li>
<li><b>Valeur du point.</b> Ce que vaut un mouvement complet d’un point : valeur du tick ÷ taille du tick, donc 5 $ ÷ 0,25 = 20 $ sur NQ.</li>
<li><b>Contrats micro.</b> MNQ, MES, MYM, M2K, MCL et MGC valent un dixième de leur mini : même prix, même graphique, des ticks dix fois plus petits.</li></ul>
<h2>Mois de contrat et rollover</h2><p>Chaque lettre est un mois de livraison : F janvier, G février, H mars, J avril, K mai, M juin, N juillet, Q août, U septembre, V octobre, X novembre, Z décembre. L’année suit : NQZ6 est le contrat Nasdaq-100 de décembre 2026.</p>
<p>Les contrats sur indices boursiers expirent chaque trimestre, le troisième vendredi de mars, juin, septembre et décembre. Le volume passe au contrat suivant environ une semaine avant : c’est là que la plupart des traders font leur rollover. Le pétrole brut a un contrat chaque mois, et l’or se négocie surtout sur ses mois pairs.</p>
<h2>Pourquoi ça compte sur un compte prop</h2><p>La perte max de ta firme est en dollars, mais ton stop est en points. La valeur du point fait le lien : une perte max de 2 000 $, c’est 100 points sur un NQ, 40 points sur un ES et 1 000 points sur un MNQ. Elle te dit combien de trades perdants ton compte peut encaisser avant la limite, et le <a href="@position-size-calculator.html">calculateur de taille de position</a> fait le calcul pour n’importe quel stop.</p>""",
"""<h2>Cómo leer una ficha de contrato</h2><ul>
<li><b>Tamaño del tick.</b> El paso de precio más pequeño: 0,25 puntos en NQ y ES, 1 punto en YM, 0,01 en el crudo.</li>
<li><b>Valor del tick.</b> Lo que vale un tick por contrato. Tu P&L son ticks × valor del tick × contratos.</li>
<li><b>Valor del punto.</b> Lo que vale un movimiento completo de un punto: valor del tick ÷ tamaño del tick, así que 5 $ ÷ 0,25 = 20 $ en NQ.</li>
<li><b>Contratos micro.</b> MNQ, MES, MYM, M2K, MCL y MGC valen una décima parte de su mini: mismo precio, mismo gráfico, ticks diez veces menores.</li></ul>
<h2>Meses de contrato y rollover</h2><p>Cada letra es un mes de entrega: F enero, G febrero, H marzo, J abril, K mayo, M junio, N julio, Q agosto, U septiembre, V octubre, X noviembre, Z diciembre. Después va el año: NQZ6 es el contrato del Nasdaq-100 de diciembre de 2026.</p>
<p>Los futuros sobre índices bursátiles vencen cada trimestre, el tercer viernes de marzo, junio, septiembre y diciembre. El volumen pasa al contrato siguiente más o menos una semana antes, y es cuando la mayoría de los traders hacen el rollover. El crudo tiene un contrato cada mes, y el oro se negocia sobre todo en sus meses pares.</p>
<h2>Por qué importa en una cuenta prop</h2><p>La pérdida máx. de tu firma está en dólares, pero tu stop está en puntos. El valor del punto une las dos cosas: una pérdida máx. de 2.000 $ son 100 puntos en un NQ, 40 puntos en un ES y 1.000 puntos en un MNQ. Te dice cuántas operaciones perdedoras aguanta tu cuenta antes del límite, y la <a href="@position-size-calculator.html">calculadora de tamaño de posición</a> hace el cálculo para cualquier stop.</p>""")
    b = (ui.sec(tbl + f'<p class="fine" style="margin-top:16px">{t(NOTE)}</p>', "t", "contracts")
         + ui.sec(f'<article class="article">{re.sub(r'href="@([^"]+)"', lambda m: f'href="{href(lang, m.group(1))}"', t(guide))}</article>', "n", "read", width="read"))
    return (t(T("Futures tick values: NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep","Valeur du tick : NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep","Valor del tick: NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep")),
            t(T("Tick size, tick value and point value for NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI and 6E futures, with what a stop costs.","Taille, valeur du tick et valeur du point pour NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI et 6E, avec le coût d’un stop.","Tamaño, valor del tick y valor del punto para NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI y 6E, con el coste de un stop.")),
            hero + b + ui.final(lang, t), "")
SYSTEM_PAGES.add("futures-contracts.html")
