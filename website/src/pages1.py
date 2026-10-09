from core import *
from pages3 import ai_band, AI_FEATURES
from pages4 import share_band, plans_band, plan_tag, share_img
from pages6 import sec_charts, sec_trust, sec_prop, sec_sweep_day, PROP_NOTE

CHECK_SVG = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3 3 7-7"/></svg>'
def fm(m):
    return lambda *a, **k: frame(*a, mobile=m, **k)
CONTRACTS = "NQ MNQ ES MES YM MYM RTY M2K CL MCL GC MGC SI 6E".split()
def chips(): return '<div class="chips">' + "".join(f"<span>{c}</span>" for c in CONTRACTS) + "</div>"

VIP_PILL = T("Share cards are here","Les cartes à partager sont là","Llegan las tarjetas para compartir")
VIP_TAG = T("Share your payouts","Partage tes payouts","Comparte tus payouts")

# ============================ HOME ============================
def page_home(lang, t):
    hero = f'''<div class="hero"><div class="wrap">
<div class="hero-copy">
<a class="pill rise" href="{href(lang,'features.html')}#share-cards"><span class="tag">{t(T("New","Nouveau","Nuevo"))}</span><b>{t(VIP_PILL)}</b><span>{t(VIP_TAG)}</span></a>
<h1 class="wu">{words(t(T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar.")),0.12)}</h1>
<p class="lead rise d2">{t(T("Sweep is the trading journal and performance system for futures traders, now with AI. Log every trade, keep your rules, track every prop account and payout, and see exactly where your edge is.",
 "Sweep est le journal de trading et système de performance des traders de futures, maintenant avec l’IA. Note chaque trade, garde tes règles, suis chaque compte prop et chaque payout, et vois exactement où se trouve ton edge.",
 "Sweep es el diario de trading y sistema de rendimiento para traders de futuros, ahora con IA. Registra cada operación, cumple tus reglas, sigue cada cuenta prop y cada payout, y descubre exactamente dónde está tu ventaja."))}</p>
<div class="cta-row rise d3"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(CREATE_FREE)}</a><a class="btn btn-line btn-lg" href="#tour">{t(T("Take the tour","Faire la visite","Ver el recorrido"))}</a></div>
<ul class="trust rise d4"><li><span class="ck">{CHECK_SVG}</span>{t(T("Free plan available","Forfait Free offert","Plan Free disponible"))}</li><li><span class="ck">{CHECK_SVG}</span>{t(T("Pro free for 14 days","Pro gratuit pendant 14 jours","Pro gratis durante 14 días"))}</li><li><span class="ck">{CHECK_SVG}</span>{t(T("No card needed","Sans carte de crédit","Sin tarjeta"))}</li></ul>
</div>
<div class="stage">
<div class="frame">{picture("desktop","overview-ask-bubble",lang,t(T("Sweep overview: today’s P&L, discipline score, today’s trades, economic events and prop account cards","Aperçu de Sweep : P&L du jour, score de discipline, trades du jour, événements économiques et cartes de comptes prop","Resumen de Sweep: P&L del día, puntuación de disciplina, operaciones del día, eventos económicos y cuentas prop")),eager=True)}</div>
<div class="phone">{picture("mobile","overview-ask-bubble",lang,t(T("Sweep on a phone","Sweep sur téléphone","Sweep en el teléfono")),eager=True,sizes="(max-width: 860px) 60vw, 200px")}</div>
<div class="phone back" aria-hidden="true">{picture("mobile","new-trade",lang,"",sizes="(max-width: 860px) 50vw, 1px")}</div>
<div class="stage-fade"></div>
</div></div></div>'''

    facts = [(12, T("futures contracts with exact tick values","contrats à terme avec les bonnes valeurs de tick","contratos de futuros con el valor de tick exacto")),
             (13, T("discipline questions per trade, all editable","questions de discipline par trade, toutes modifiables","preguntas de disciplina por operación, todas editables")),
             (6, T("measures in one performance score","mesures dans un seul score de performance","medidas en una sola puntuación de rendimiento")),
             (19, T("economic indicators explained","indicateurs économiques expliqués","indicadores económicos explicados"))]
    fx = "".join(f'<div><span class="num" data-count="{n}">{n}</span><span>{t(l)}</span></div>' for n, l in facts)
    facts_html = f'<section style="padding:64px 0 0"><div class="wrap"><div class="facts stagger">{fx}</div></div></section>'

    tour_items = [
     ("journal-day", T("Plan the day","Planifie ta journée","Planifica el día"),
      T("Write your bias, key levels, scenarios and max loss before the open. After the close, grade the day against the plan.",
        "Note ton biais, tes niveaux clés, tes scénarios et ta perte max avant l’ouverture. Après la clôture, note ta journée par rapport au plan.",
        "Escribe tu sesgo, niveles clave, escenarios y pérdida máxima antes de la apertura. Tras el cierre, califica el día frente al plan.")),
     ("new-trade", T("Log the trade in seconds","Ajoute le trade en quelques secondes","Registra la operación en segundos"),
      T("Entry, stop and target with live risk, R:R and your daily risk budget. Sweep warns you before you break a rule.",
        "Entrée, stop et cible avec le risque en direct, le R:R et ton budget de risque quotidien. Sweep t’avertit avant que tu brises une règle.",
        "Entrada, stop y objetivo con riesgo en vivo, R:R y tu presupuesto de riesgo diario. Sweep te avisa antes de romper una regla.")),
     ("trade-review", T("Review it while it’s fresh","Révise-le pendant que c’est frais","Revísala mientras está fresca"),
      T("A chart of your levels and executions, a 4-step guided review, and the news that hit during the trade.",
        "Un graphique de tes niveaux et exécutions, une révision guidée en 4 étapes, et les nouvelles tombées pendant le trade.",
        "Un gráfico con tus niveles y ejecuciones, una revisión guiada en 4 pasos y las noticias que salieron durante la operación.")),
     ("insights", T("See what actually works","Vois ce qui fonctionne vraiment","Mira lo que realmente funciona"),
      T("A performance score, your P&L by session, setup and day, and plain-language patterns you’d never spot alone.",
        "Un score de performance, ton P&L par session, setup et jour, et des tendances en mots simples que tu ne verrais pas seul.",
        "Una puntuación de rendimiento, tu P&L por sesión, setup y día, y patrones en lenguaje claro que no verías solo.")),
     ("payouts", T("Know what you take home","Sache ce que tu ramènes","Sabe lo que te llevas"),
      T("Payouts minus evaluations, resets and fees. The real number, across every firm and account.",
        "Les payouts moins les évaluations, resets et frais. Le vrai chiffre, toutes firmes et tous comptes confondus.",
        "Payouts menos evaluaciones, reinicios y cuotas. El número real, en todas las firmas y cuentas.")),
    ]
    steps = "".join(f'''<div class="tour-step{" on" if i==0 else ""}" data-i="{i}"><span class="n">0{i+1}</span><h3>{t(h)}</h3><p>{t(p)}</p>
<div class="tour-inline">{frame(s,lang,t(h),t,cap=False,mobile={"journal-day":"calendar"}.get(s))}</div></div>''' for i,(s,h,p) in enumerate(tour_items))
    imgs = "".join(picture("desktop", s, lang, t(h), sizes="(max-width: 860px) 92vw, 760px").replace("<img ", f'<img class="{"on" if i==0 else ""}" ', 1) for i,(s,h,p) in enumerate(tour_items))
    tour = f'''<section id="tour"><div class="wrap">
<div class="head"><span class="kick">{t(T("A trading day in Sweep","Une journée de trading dans Sweep","Un día de trading en Sweep"))}</span><h2>{t(T("From the plan to the payout.","Du plan jusqu’au payout.","Del plan al payout."))}</h2></div>
<div class="tour"><div class="tour-steps" tabindex="0" aria-label="{t(T("Tour","Visite","Recorrido"))}">{steps}</div><div class="dots" aria-hidden="true">{"".join("<i></i>" for _ in tour_items)}</div><div class="tour-media"><div class="frame">{imgs}</div><p class="cap">{t(SAMPLE)}</p></div></div>
</div></section>'''

    MOB = {"insights-discipline":"insights","calendar":"calendar","payouts":"payouts"}
    pill = lambda s, h, p, alt: f'''<article class="pillar"><div class="txt"><h3>{t(h)}</h3><p>{t(p)}</p></div><div class="shot">{picture_dm(s,MOB[s],lang,t(alt))}</div></article>'''
    pillars = f'''<section class="rule"><div class="wrap">
<div class="head"><span class="kick">{t(T("Why Sweep","Pourquoi Sweep","Por qué Sweep"))}</span><h2>{t(T("Build the habits. Find the edge. Get paid.","Bâtis les habitudes. Trouve ton edge. Fais-toi payer.","Crea los hábitos. Encuentra tu ventaja. Cobra."))}</h2>
<p class="lead">{t(T("Most traders don’t lack a strategy. They lack a record honest enough to show what to keep and what to cut.","La plupart des traders ne manquent pas de stratégie. Il leur manque un historique assez honnête pour montrer quoi garder et quoi couper.","A la mayoría de los traders no les falta estrategia. Les falta un historial lo bastante honesto para mostrar qué conservar y qué eliminar."))}</p></div>
<div class="pillars stagger">
{pill("insights-discipline", T("Build the habits","Bâtis les habitudes","Crea los hábitos"), T("A discipline checklist on every trade and automatic rule checks. See process versus outcome, and which broken rules cost you the most.","Une checklist de discipline sur chaque trade et des vérifications automatiques. Vois le processus contre le résultat, et les règles brisées qui te coûtent le plus.","Un checklist de disciplina en cada operación y revisión automática de reglas. Ve proceso frente a resultado, y qué reglas rotas te cuestan más."), T("Discipline deep dive","Analyse de discipline","Análisis de disciplina"))}
{pill("calendar", T("Find the edge","Trouve ton edge","Encuentra tu ventaja"), T("Your month as a heat map, with weekly totals and the high-impact news of each day. Then break it down by session, setup and hour.","Ton mois en carte thermique, avec les totaux par semaine et les nouvelles importantes de chaque jour. Puis découpe par session, setup et heure.","Tu mes como mapa de calor, con totales semanales y las noticias de alto impacto de cada día. Luego desglósalo por sesión, setup y hora."), T("P&L calendar","Calendrier P&L","Calendario de P&L"))}
{pill("payouts", T("Get paid","Fais-toi payer","Cobra"), T("Every prop account with its rules, drawdown room and target. Payouts and expenses side by side, so you know your real net.","Chaque compte prop avec ses règles, sa marge de drawdown et sa cible. Payouts et dépenses côte à côte, pour connaître ton vrai net.","Cada cuenta prop con sus reglas, margen de drawdown y objetivo. Payouts y gastos lado a lado, para conocer tu neto real."), T("Payouts and expenses","Payouts et dépenses","Payouts y gastos"))}
</div></div></section>'''

    prop = split(t, T("For prop traders","Pour traders prop","Para traders prop"),
        T("Every prop account. Every rule. One record.","Chaque compte prop. Chaque règle. Un seul historique.","Cada cuenta prop. Cada regla. Un solo historial."),
        T("Add each account with its firm’s rules and Sweep tracks where you stand, trade by trade. When an account ends, its history stays.","Ajoute chaque compte avec les règles de sa firme et Sweep suit où tu en es, trade après trade. Quand un compte se termine, son historique reste.","Añade cada cuenta con las reglas de su firma y Sweep sigue dónde estás, operación a operación. Cuando una cuenta termina, su historial se queda."),
        [T("<b>Drawdown your way:</b> trailing end of day, trailing intraday or static","<b>Ton type de drawdown :</b> trailing fin de journée, trailing intrajournalier ou statique","<b>Tu tipo de drawdown:</b> trailing al cierre, trailing intradía o estático"),
         T("<b>Live status:</b> in good standing, close to a limit, target reached","<b>Statut en direct :</b> en règle, proche d’une limite, cible atteinte","<b>Estado en vivo:</b> en regla, cerca de un límite, objetivo alcanzado"),
         T("<b>Trade copier:</b> log one decision on several accounts at once","<b>Copieur de trades :</b> note une décision sur plusieurs comptes d’un coup","<b>Copiador de operaciones:</b> registra una decisión en varias cuentas a la vez"),
         T("<b>Closed accounts kept</b> as failed, passed or closed","<b>Comptes fermés conservés</b> comme échoués, réussis ou fermés","<b>Cuentas cerradas conservadas</b> como fallidas, aprobadas o cerradas")],
        frame("accounts", lang, t(T("Prop account cards with drawdown room, profit target and daily limit bars","Cartes de comptes prop avec marge de drawdown, cible de profit et limite quotidienne","Tarjetas de cuentas prop con margen de drawdown, objetivo y límite diario")), t),
        more=f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"prop-traders.html")}">{t(T("Sweep for prop traders","Sweep pour les traders prop","Sweep para traders prop"))}</a></div>')

    news = split(t, T("Economic calendar","Calendrier économique","Calendario económico"),
        T("Every U.S. release, recapped in a minute.","Chaque annonce américaine, résumée en une minute.","Cada dato de EE. UU., resumido en un minuto."),
        T("The numbers fill themselves in, a flash recap lands about a minute after the release, and a full market reaction report follows at about 30 minutes. Every trade is linked to the news around it.","Les chiffres se remplissent seuls, un récap éclair arrive environ une minute après la publication, puis un rapport complet sur la réaction du marché vers 30 minutes. Chaque trade est lié aux nouvelles autour.","Las cifras se completan solas, un resumen flash llega aproximadamente un minuto después y un informe completo de la reacción del mercado a los 30 minutos. Cada operación se vincula a las noticias cercanas."),
        [T("Reaction on NQ, ES, the 10-year yield and the dollar, with sources","Réaction sur NQ, ES, le taux 10 ans et le dollar, avec les sources","Reacción en NQ, ES, el rendimiento a 10 años y el dólar, con fuentes"),
         T("Warnings in the trade ticket when news is close","Avertissement dans le ticket quand une nouvelle approche","Aviso en el ticket cuando se acerca una noticia"),
         T("Your results within 5 and 15 minutes of a release","Tes résultats à 5 et 15 minutes d’une publication","Tus resultados a 5 y 15 minutos de una publicación")],
        frame("news-impact-report", lang, t(T("Market impact report after a U.S. release","Rapport d’impact après une annonce américaine","Informe de impacto tras un dato de EE. UU.")), t, cap=EXAMPLE),
        flip=True, more=f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"economic-calendar.html")}">{t(T("About the calendar","À propos du calendrier","Sobre el calendario"))}</a></div>')

    phones = f'''<section class="rule center"><div class="wrap">
<div class="head center"><span class="kick">{t(T("Phone first","Mobile d’abord","Primero el móvil"))}</span><h2>{t(T("Made for the phone in your hand.","Pensé pour le téléphone dans ta main.","Hecho para el teléfono en tu mano."))}</h2>
<p class="lead">{t(T("Log a trade between sessions with one thumb. Swipe sheets away, scroll filters on one line, and add Sweep to your home screen like an app.","Ajoute un trade entre deux sessions avec un pouce. Ferme les fenêtres d’un glissement, filtre sur une seule ligne, et mets Sweep sur ton écran d’accueil comme une app.","Registra una operación entre sesiones con un pulgar. Cierra paneles deslizando, filtra en una sola línea y añade Sweep a tu pantalla de inicio como una app."))}</p></div>
<div class="phones rail reveal">{phone("new-trade",lang,t(T("New trade on a phone","Nouveau trade sur téléphone","Nueva operación en el teléfono")))}{phone("trades",lang,t(T("Trades list on a phone","Liste des trades sur téléphone","Lista de operaciones en el teléfono")))}{phone("ask-sweep",lang,t(T("Ask Sweep on a phone","Ask Sweep sur téléphone","Ask Sweep en el teléfono")))}</div>
<p class="cap" style="margin-top:28px">{t(SAMPLE)}</p>
<div class="cta-row"><a class="btn btn-line" href="{href(lang,'install.html')}">{t(T("Install on your phone","Installer sur ton téléphone","Instalar en tu teléfono"))}</a></div>
</div></section>'''

    data = f'''<section class="rule"><div class="wrap">
<div class="head"><span class="kick">{t(T("Your data","Tes données","Tus datos"))}</span><h2>{t(T("Your record belongs to you.","Ton historique t’appartient.","Tu historial es tuyo."))}</h2></div>
{grid(t,[("eye",T("Private by default","Privé par défaut","Privado por defecto"),T("Only you see your trades, notes and screenshots.","Toi seul vois tes trades, notes et captures.","Solo tú ves tus operaciones, notas y capturas.")),
("download",T("Export anytime","Exporte en tout temps","Exporta cuando quieras"),T("Every account, trade, journal and payout in one JSON file.","Chaque compte, trade, journal et payout dans un fichier JSON.","Cada cuenta, operación, diario y payout en un archivo JSON.")),
("trash",T("Delete instantly","Supprime instantanément","Elimina al instante"),T("One click in Settings removes your account and all its data.","Un clic dans les réglages supprime ton compte et toutes ses données.","Un clic en Ajustes elimina tu cuenta y todos sus datos.")),
("shield",T("No ads, no trackers","Ni pubs ni traqueurs","Sin anuncios ni rastreadores"),T("No analytics, no advertising, and your data is never sold.","Aucune analytique, aucune pub, et tes données ne sont jamais vendues.","Sin analítica, sin publicidad y tus datos nunca se venden."))],"g4")}
<div class="cta-row"><a class="btn btn-line" href="{href(lang,'security.html')}">{t(T("Security and privacy","Sécurité et confidentialité","Seguridad y privacidad"))}</a></div>
</div></section>'''

    from pages2 import FAQ
    picks = [FAQ[0][1][0], FAQ[3][1][0], FAQ[0][1][3], FAQ[1][1][0], FAQ[4][1][0]]
    faq = f'''<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>{"".join(faq_item(t,q,a) for q,a in picks)}
<div class="cta-row"><a class="btn btn-line" href="{href(lang,'faq.html')}">{t(T("All questions","Toutes les questions","Todas las preguntas"))}</a></div></div></section>'''

    ld = jsonld({"@context":"https://schema.org","@graph":[
        {"@type":"Organization","name":"Sweep Inc.","url":f"https://{DOMAIN}/","logo":f"https://{DOMAIN}/icons/icon-512.png","email":EMAIL,
         "sameAs":[u for _,u,_ in SOCIAL],"address":{"@type":"PostalAddress","streetAddress":"3980 Blvd St-Elzear O","addressLocality":"Laval","addressRegion":"QC","postalCode":"H7P 0M2","addressCountry":"CA"}},
        {"@type":"SoftwareApplication","name":"Sweep","applicationCategory":"FinanceApplication","operatingSystem":"Web, iOS, Android",
         "url":APP,"description":t(T("Trading journal and performance system for futures traders.","Journal de trading et système de performance pour traders de futures.","Diario de trading y sistema de rendimiento para traders de futuros.")),
         "offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"inLanguage":["en","fr","es"]},
        {"@type":"WebSite","name":"Sweep","url":f"https://{DOMAIN}/","inLanguage":lang}]})
    from core import _pick
    dk = f"desktop-{_pick('desktop',lang,'overview-ask-bubble')}-dark-overview-ask-bubble"; mk = f"mobile-{_pick('mobile',lang,'overview-ask-bubble')}-dark-overview-ask-bubble"
    ld = (f'<link rel="preload" as="image" href="/img/{dk}-1200.webp" imagesrcset="/img/{dk}-1200.webp 1200w, /img/{dk}-2400.webp 2400w" imagesizes="1120px" media="(min-width: 861px) and (prefers-color-scheme: dark)" fetchpriority="high">'
          f'<link rel="preload" as="image" href="/img/{mk}-400.webp" imagesrcset="/img/{mk}-400.webp 400w, /img/{mk}-786.webp 786w" imagesizes="60vw" media="(max-width: 860px) and (prefers-color-scheme: dark)" fetchpriority="high">') + ld
    return (t(T("Sweep · Trading journal for futures and prop traders","Sweep · Journal de trading pour traders de futures et prop","Sweep · Diario de trading para traders de futuros y prop")),
            t(T("Sweep is the trading journal and performance system for futures traders. Log trades, keep your rules, track prop accounts, payouts and expenses, and find your edge. Free plan available, Pro free for 14 days.",
                "Sweep est le journal de trading et système de performance des traders de futures. Note tes trades, garde tes règles, suis tes comptes prop, payouts et dépenses, et trouve ton edge. Forfait Free offert, Pro gratuit 14 jours.",
                "Sweep es el diario de trading y sistema de rendimiento para traders de futuros. Registra operaciones, cumple tus reglas, sigue cuentas prop, payouts y gastos, y encuentra tu ventaja. Plan Free disponible, Pro gratis 14 días.")),
            hero + facts_html + tour + pillars + ai_band(lang, t) + prop + share_band(lang, t) + phones + data + plans_band(lang, t) + faq + final_cta(lang, t), ld)

# ============================ FEATURES ============================
def page_features(lang, t):
    anchors = [("logging",T("Logging","Saisie","Registro")),("numbers",T("Your numbers","Tes chiffres","Tus números")),("charts",T("Real charts","Graphiques","Gráficos")),("rules",T("Rules","Règles","Reglas")),("review",T("Review","Révision","Revisión")),("insights",T("Insights","Analyses","Análisis")),
               ("journal",T("Calendar & journal","Calendrier & journal","Calendario y diario")),("economic-reports",T("News","Nouvelles","Noticias")),("ai",T("Sweep AI","Sweep AI","Sweep AI")),("ask-sweep",T("Ask Sweep","Ask Sweep","Ask Sweep")),("accounts",T("Accounts","Comptes","Cuentas")),
               ("payouts",T("Payouts","Payouts","Payouts")),("share-cards",T("Share cards","Cartes à partager","Tarjetas")),("sync",T("Sync","Synchro","Sincronización")),("data",T("Your data","Tes données","Tus datos")),("mobile",T("Phone & desktop","Téléphone & ordi","Móvil y escritorio"))]
    sub = '<nav class="subnav" aria-label="Features"><div class="wrap">' + "".join(f'<a href="#{a}">{t(l)}</a>' for a,l in anchors) + "</div></nav>"
    hero = page_hero(t, T("Everything you track, in one place.","Tout ce que tu suis, au même endroit.","Todo lo que sigues, en un solo lugar."),
        T("Logging, charts, prop firm rules, payouts, discipline and AI. One app, one record.","Saisie, graphiques, règles des prop firms, payouts, discipline et IA. Une app, un historique.","Registro, gráficos, reglas de prop firms, payouts, disciplina e IA. Una app, un historial."),
        T("Features","Fonctionnalités","Funciones"))
    S = []
    S.append(split(t, T("Logging","Saisie","Registro"), T("A trade ticket that does the math.","Un ticket de trade qui fait les calculs.","Un ticket que hace las cuentas."),
      T("Symbol, side, time to the second in New York time, contracts, entry, stop, target and exit. Sweep handles the tick values, the P&L and the session.",
        "Symbole, direction, heure à la seconde (heure de New York), contrats, entrée, stop, cible et sortie. Sweep s’occupe des valeurs de tick, du P&L et de la session.",
        "Símbolo, dirección, hora al segundo en hora de Nueva York, contratos, entrada, stop, objetivo y salida. Sweep se encarga del valor del tick, el P&L y la sesión."),
      [T("<b>Live risk:</b> $ and points at risk, reward, R:R, and a warning if the stop or target is on the wrong side","<b>Risque en direct :</b> risque et gain en $ et en points, R:R, et alerte si le stop ou la cible est du mauvais côté","<b>Riesgo en vivo:</b> riesgo y beneficio en $ y puntos, R:R, y aviso si el stop o el objetivo están del lado equivocado"),
       T("<b>Daily risk budget:</b> what’s left of your daily loss limit before and after this trade","<b>Budget de risque quotidien :</b> ce qui reste de ta perte max avant et après ce trade","<b>Presupuesto de riesgo diario:</b> lo que queda de tu pérdida máxima antes y después de esta operación"),
       T("<b>Scale in and out:</b> multiple executions, weighted average entry, FIFO P&L","<b>Entrées et sorties partielles :</b> plusieurs exécutions, entrée moyenne pondérée, P&L FIFO","<b>Entradas y salidas parciales:</b> varias ejecuciones, entrada media ponderada, P&L FIFO"),
       T("<b>One tap exits:</b> “Exit at target” or “Exit at stop” fills the price and time","<b>Sortie en un toucher :</b> « Sortie à la cible » ou « Sortie au stop » remplit le prix et l’heure","<b>Salida en un toque:</b> «Salir en objetivo» o «Salir en stop» completa precio y hora"),
       T("<b>Session detected</b> from the entry time: Asia, London, New York AM, New York PM","<b>Session détectée</b> selon l’heure d’entrée : Asie, Londres, New York AM, New York PM","<b>Sesión detectada</b> por la hora de entrada: Asia, Londres, Nueva York AM, Nueva York PM"),
       T("<b>Multiple entries and partial exits</b> with the average price recalculated","<b>Entrées multiples et sorties partielles</b> avec prix moyen recalculé","<b>Entradas múltiples y salidas parciales</b> con precio medio recalculado")],
      frame("new-trade", lang, t(T("New trade ticket with live risk and daily risk budget","Ticket de nouveau trade avec risque en direct et budget de risque","Ticket de nueva operación con riesgo en vivo y presupuesto de riesgo")), t), id_="logging", rule=False))
    from pages9 import sec_numbers
    S.append(sec_numbers(lang, t))
    S.append(sec_charts(lang, t, id_="charts"))
    S.append(split(t, T("Rules","Règles","Reglas"), T("Rules that check themselves.","Des règles qui se vérifient seules.","Reglas que se revisan solas."),
      T("Sweep compares every trade to your plan and records what broke. A warning never blocks the trade: your history stays honest.",
        "Sweep compare chaque trade à ton plan et note ce qui a été brisé. Un avertissement ne bloque jamais le trade : ton historique reste honnête.",
        "Sweep compara cada operación con tu plan y registra lo que se rompió. Un aviso nunca bloquea la operación: tu historial sigue siendo honesto."),
      [T("<b>Automatic checks:</b> added to a loser, oversized position, stop not respected, risk limit exceeded","<b>Vérifications automatiques :</b> ajout à une perte, position trop grosse, stop non respecté, limite de risque dépassée","<b>Revisión automática:</b> añadir a una perdedora, posición sobredimensionada, stop no respetado, límite de riesgo superado"),
       T("<b>Discipline checklist:</b> 13 questions by default, yours to edit, answered Yes, No or N/A","<b>Checklist de discipline :</b> 13 questions par défaut, modifiables, réponse Oui, Non ou S.O.","<b>Checklist de disciplina:</b> 13 preguntas por defecto, editables, con Sí, No o N/A"),
       T("<b>Your threshold</b> for a good process, 90% by default","<b>Ton seuil</b> de bon processus, 90 % par défaut","<b>Tu umbral</b> de buen proceso, 90 % por defecto"),
       T("<b>Process vs outcome:</b> good trades that lost, bad trades that won, and violations ranked by cost","<b>Processus vs résultat :</b> bons trades perdants, mauvais trades gagnants, et infractions classées par coût","<b>Proceso vs resultado:</b> buenas operaciones perdedoras, malas ganadoras, e infracciones ordenadas por costo")],
      fm("insights")("insights-discipline", lang, t(T("Discipline deep dive: process versus outcome and violations ranked by cost","Analyse de discipline : processus vs résultat et infractions classées par coût","Análisis de disciplina: proceso vs resultado e infracciones por costo")), t), flip=True, id_="rules"))
    S.append(split(t, T("Review","Révision","Revisión"), T("Review every trade in four steps.","Révise chaque trade en quatre étapes.","Revisa cada operación en cuatro pasos."),
      T("A chart of the trade with entry, stop, target and exit, risk and reward zones, your executions and the U.S. news on the time axis. Then a guided review.",
        "Un graphique du trade avec entrée, stop, cible et sortie, zones de risque et de gain, tes exécutions et les nouvelles américaines sur l’axe du temps. Puis une révision guidée.",
        "Un gráfico de la operación con entrada, stop, objetivo y salida, zonas de riesgo y beneficio, tus ejecuciones y las noticias de EE. UU. en el eje del tiempo. Luego una revisión guiada."),
      [T("<b>1. Checklist</b> of your discipline questions","<b>1. Checklist</b> de tes questions de discipline","<b>1. Checklist</b> de tus preguntas de disciplina"),
       T("<b>2. Psychology:</b> 15 emotional states, plus confidence and execution ratings","<b>2. Psychologie :</b> 15 états émotionnels, plus notes de confiance et d’exécution","<b>2. Psicología:</b> 15 estados emocionales, más valoración de confianza y ejecución"),
       T("<b>3. Notes:</b> why you entered, what went well or wrong, the lesson, a grade from A to F","<b>3. Notes :</b> pourquoi tu es entré, ce qui a marché ou non, la leçon, une note de A à F","<b>3. Notas:</b> por qué entraste, qué salió bien o mal, la lección, una nota de A a F"),
       T("<b>4. Screenshots</b> from TradingView or anywhere, stored privately","<b>4. Captures</b> de TradingView ou d’ailleurs, conservées en privé","<b>4. Capturas</b> de TradingView o cualquier sitio, guardadas en privado")],
      frame("trade-review", lang, t(T("Trade review with chart, executions, R multiple and discipline","Révision de trade avec graphique, exécutions, multiple R et discipline","Revisión de operación con gráfico, ejecuciones, múltiplo R y disciplina")), t), id_="review"))
    S.append(split(t, T("Insights","Analyses","Análisis"), T("Find the edge in your own numbers.","Trouve l’edge dans tes propres chiffres.","Encuentra la ventaja en tus propios números."),
      T("Win rate, profit factor and P&L by setup, session and hour, plus a performance score from 0 to 100 once you have 10 trades. Your edge, in your own numbers.",
        "Taux de réussite, profit factor et P&L par setup, session et heure, plus un score de performance de 0 à 100 dès 10 trades. Ton edge, dans tes propres chiffres.",
        "Tasa de acierto, profit factor y P&L por setup, sesión y hora, más una puntuación de 0 a 100 a partir de 10 operaciones. Tu ventaja, en tus propios números."),
      [T("<b>Curves:</b> cumulative or daily P&L, drawdown, and duration analysis","<b>Courbes :</b> P&L cumulatif ou quotidien, drawdown et analyse de durée","<b>Curvas:</b> P&L acumulado o diario, drawdown y análisis de duración"),
       T("<b>Breakdowns</b> by side, session, setup, weekday, tag and account","<b>Répartitions</b> par direction, session, setup, jour, tag et compte","<b>Desgloses</b> por dirección, sesión, setup, día, etiqueta y cuenta"),
       T("<b>Patterns to watch:</b> plain-language findings, each based on at least 5 trades","<b>Tendances à surveiller :</b> constats en mots simples, chacun basé sur au moins 5 trades","<b>Patrones a vigilar:</b> hallazgos en lenguaje claro, cada uno con al menos 5 operaciones"),
       T("<b>Deep dives:</b> discipline, behavior after a loss, recovery, sessions, time, weekday, setups, long vs short, news","<b>Analyses poussées :</b> discipline, comportement après une perte, récupération, sessions, heure, jour, setups, long vs short, nouvelles","<b>Análisis a fondo:</b> disciplina, comportamiento tras una pérdida, recuperación, sesiones, hora, día, setups, largo vs corto, noticias"),
       T("<b>Filters everywhere:</b> period, firm, account (closed ones too), session, side, instrument","<b>Filtres partout :</b> période, firme, compte (fermés inclus), session, direction, instrument","<b>Filtros en todas partes:</b> periodo, firma, cuenta (también cerradas), sesión, dirección, instrumento")],
      slot("ecran-analyses-ordi.webp","desktop",t(T("Insights with KPIs, performance score and P&L curve","Analyses avec indicateurs, score de performance et courbe de P&L","Análisis con KPI, puntuación de rendimiento y curva de P&L")),t,fallback="insights"), flip=True, id_="insights"))
    S.append(split(t, T("Calendar & journal","Calendrier & journal","Calendario y diario"), T("Plan before the open. Grade after the close.","Planifie avant l’ouverture. Évalue après la clôture.","Planifica antes de la apertura. Califica tras el cierre."),
      T("Your month as a heat map with weekly totals and each day’s high-impact news. Open any day for its stats, its trades, and your plan and review.",
        "Ton mois en carte thermique avec les totaux par semaine et les nouvelles importantes du jour. Ouvre n’importe quel jour pour ses stats, ses trades, ton plan et ta révision.",
        "Tu mes como mapa de calor con totales semanales y las noticias de alto impacto de cada día. Abre cualquier día para ver sus datos, operaciones, plan y revisión."),
      [T("<b>Pre-market:</b> bias, key levels, scenarios, plan, max loss, max trades, focus","<b>Pré-marché :</b> biais, niveaux clés, scénarios, plan, perte max, trades max, focus","<b>Pre-mercado:</b> sesgo, niveles clave, escenarios, plan, pérdida máxima, operaciones máximas, enfoque"),
       T("<b>Post-market:</b> did you follow the plan, triggers, lesson, tomorrow, daily grade","<b>Post-marché :</b> as-tu suivi le plan, déclencheurs, leçon, demain, note du jour","<b>Post-mercado:</b> si seguiste el plan, detonantes, lección, mañana, nota del día"),
       T("<b>Weekly review</b> page to step back","<b>Révision hebdomadaire</b> pour prendre du recul","<b>Revisión semanal</b> para tomar distancia")],
      slot("ecran-calendrier-ordi.webp","desktop",t(T("Daily journal with day stats, trades, pre-market plan and post-market review","Journal quotidien avec stats, trades, plan pré-marché et révision post-marché","Diario con datos del día, operaciones, plan pre-mercado y revisión post-mercado")),t,fallback="journal-day"), id_="journal"))
    S.append(split(t, T("News","Nouvelles","Noticias"), T("Every U.S. release, recapped in a minute.","Chaque annonce américaine, résumée en une minute.","Cada dato de EE. UU., resumido en un minuto."),
      T("High and medium impact U.S. events in Eastern Time. Sweep AI fills in the numbers from official sources, writes a flash recap about a minute after the release and a full market reaction report at about 30 minutes.",
        "Les événements américains d’impact élevé et moyen en heure de l’Est. Sweep AI remplit les chiffres à partir de sources officielles, rédige un récap éclair environ une minute après la publication et un rapport complet sur la réaction du marché vers 30 minutes.",
        "Eventos de EE. UU. de impacto alto y medio en hora del Este. Sweep AI completa las cifras desde fuentes oficiales, redacta un resumen flash aproximadamente un minuto después y un informe completo de la reacción del mercado hacia los 30 minutos."),
      [T("<b>Values filled in:</b> actual, consensus, previous and revision, labeled and sourced","<b>Valeurs remplies :</b> réel, consensus, précédent et révision, identifiés et sourcés","<b>Valores completados:</b> real, consenso, anterior y revisión, identificados y con fuentes"),
       T("<b>Full report:</b> NQ, ES, the 10-year yield and the dollar, why it moved, the Fed read, what to watch","<b>Rapport complet :</b> NQ, ES, le taux 10 ans et le dollar, pourquoi ça a bougé, la lecture de la Fed, quoi surveiller","<b>Informe completo:</b> NQ, ES, el rendimiento a 10 años y el dólar, por qué se movió, la lectura de la Fed, qué vigilar"),
       T("<b>Linked to your trades</b> from 30 minutes before entry to 30 after exit","<b>Lié à tes trades</b> de 30 minutes avant l’entrée à 30 minutes après la sortie","<b>Vinculado a tus operaciones</b> de 30 minutos antes de la entrada a 30 después de la salida"),
       T("<b>Explainers</b> for 19 major indicators","<b>Explications</b> pour 19 indicateurs majeurs","<b>Explicaciones</b> de 19 indicadores principales")],
      frame("news-impact-report", lang, t(T("Market impact report after Nonfarm Payrolls","Rapport d’impact après le Nonfarm Payrolls","Informe de impacto tras el Nonfarm Payrolls")), t, cap=EXAMPLE), flip=True, id_="economic-reports",
      more=f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"economic-calendar.html")}">{t(T("Economic calendar","Calendrier économique","Calendario económico"))}</a></div>'))
    S.append(split(t, T("Sweep AI","Sweep AI","Sweep AI"), T("Less typing. More reviewing.","Moins de saisie. Plus de révision.","Menos escribir. Más revisar."),
      T("Optional AI actions, marked ✦, turn plain words, screenshots and receipts into drafts you check, and review your trades, days and weeks. Included on every plan.",
        "Des actions IA optionnelles, marquées ✦, transforment mots simples, captures et reçus en brouillons à vérifier, et révisent tes trades, tes journées et tes semaines. Incluses dans tous les forfaits.",
        "Acciones de IA opcionales, marcadas con ✦, convierten palabras, capturas y recibos en borradores que revisas, y revisan tus operaciones, días y semanas. Incluidas en todos los planes."),
      [x[1] for x in AI_FEATURES],
      frame("ai-log-trades", lang, t(T("Sweep AI logging trades from a sentence","Sweep AI note des trades à partir d’une phrase","Sweep AI registra operaciones a partir de una frase")), t, mobile="ask-sweep"), id_="ai",
      more=f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"ai.html")}">{t(T("Discover Sweep AI","Découvrir Sweep AI","Descubrir Sweep AI"))}</a></div>'))
    S.append(split(t, T("Ask Sweep","Ask Sweep","Ask Sweep"), T("Ask Sweep anything about your trading.","Demande tout à Sweep sur ton trading.","Pregúntale a Sweep lo que quieras sobre tu trading."),
      T("Your trading assistant, in the corner of every page. It answers questions about your own trades with numbers Sweep calculates, covers today’s U.S. news, and shows you around the app.",
        "Ton assistant de trading, dans le coin de chaque page. Il répond à tes questions sur tes trades avec des chiffres calculés par Sweep, couvre les nouvelles américaines du jour et te guide dans l’app.",
        "Tu asistente de trading, en la esquina de cada página. Responde preguntas sobre tus operaciones con cifras que calcula Sweep, cubre las noticias de EE. UU. de hoy y te guía por la app."),
      [T("Starter questions and 2 or 3 follow-ups after each answer","Questions de départ et 2 ou 3 suivis après chaque réponse","Preguntas iniciales y 2 o 3 de seguimiento tras cada respuesta"),
       T("One-tap actions like “Open Insights”","Actions en un toucher comme « Ouvrir les analyses »","Acciones en un toque como «Abrir análisis»"),
       T("A bottom sheet on phones that closes with a swipe","Une fenêtre en bas sur téléphone, qui se ferme d’un glissement","Un panel inferior en el móvil que se cierra deslizando"),
       T("No predictions, no signals, no financial advice","Ni prédictions, ni signaux, ni conseils financiers","Sin predicciones, señales ni asesoramiento financiero")],
      frame("ask-sweep", lang, t(T("Ask Sweep chat","Discussion Ask Sweep","Chat de Ask Sweep")), t), flip=True, id_="ask-sweep"))
    S.append(split(t, T("Accounts","Comptes","Cuentas"), T("Every account, with its firm’s rules.","Chaque compte, avec les règles de sa firme.","Cada cuenta, con las reglas de su firma."),
      T("Prop and personal accounts side by side, each with its own rules. Balances and P&L for today, the week, the month and all time.",
        "Comptes prop et personnels côte à côte, chacun avec ses propres règles. Soldes et P&L du jour, de la semaine, du mois et depuis le début.",
        "Cuentas prop y personales lado a lado, cada una con sus reglas. Saldos y P&L del día, la semana, el mes y desde siempre."),
      [T("<b>Rules per account:</b> profit target, max drawdown, daily loss limit, consistency %, minimum trading days","<b>Règles par compte :</b> cible de profit, drawdown max, perte quotidienne max, consistance %, jours de trading minimum","<b>Reglas por cuenta:</b> objetivo, drawdown máximo, pérdida diaria máxima, consistencia %, días mínimos"),
       T("<b>Status:</b> good standing, target reached, close to a limit, drawdown breached, daily limit hit","<b>Statut :</b> en règle, cible atteinte, proche d’une limite, drawdown dépassé, limite quotidienne atteinte","<b>Estado:</b> en regla, objetivo alcanzado, cerca de un límite, drawdown superado, límite diario alcanzado"),
       T("<b>Trade copier</b> for several accounts at once","<b>Copieur de trades</b> pour plusieurs comptes à la fois","<b>Copiador de operaciones</b> para varias cuentas a la vez"),
       T("<b>Closed accounts keep their history</b> and stay in your filters","<b>Les comptes fermés gardent leur historique</b> et restent dans tes filtres","<b>Las cuentas cerradas conservan su historial</b> y siguen en tus filtros"),
       T("<b>Number of accounts</b> depends on your plan","<b>Nombre de comptes</b> selon ton forfait","<b>Número de cuentas</b> según tu plan")],
      frame("accounts", lang, t(T("Accounts with balances and P&L by period","Comptes avec soldes et P&L par période","Cuentas con saldos y P&L por periodo")), t), id_="accounts"))
    S.append(split(t, T("Payouts","Payouts","Payouts"), T("The number that matters: what you keep.","Le chiffre qui compte : ce que tu gardes.","El número que importa: lo que te quedas."),
      T("Track payouts from request to payment, and every cost of trading. Sweep shows your trading P&L, payouts received, expenses and net realized income.",
        "Suis tes payouts de la demande au paiement, et chaque coût du trading. Sweep montre ton P&L de trading, les payouts reçus, les dépenses et ton revenu net réalisé.",
        "Sigue tus payouts de la solicitud al pago, y cada costo del trading. Sweep muestra tu P&L de trading, payouts recibidos, gastos e ingreso neto realizado."),
      [T("<b>Payout status:</b> planned, requested, approved, paid or rejected, with dates","<b>Statut des payouts :</b> prévu, demandé, approuvé, payé ou refusé, avec les dates","<b>Estado de payouts:</b> planificado, solicitado, aprobado, pagado o rechazado, con fechas"),
       T("<b>Expenses:</b> evaluations, activations, resets, data and platform fees","<b>Dépenses :</b> évaluations, activations, resets, frais de données et de plateforme","<b>Gastos:</b> evaluaciones, activaciones, reinicios, cuotas de datos y plataforma"),
       T("<b>Net realized income</b> = payouts − expenses","<b>Revenu net réalisé</b> = payouts − dépenses","<b>Ingreso neto realizado</b> = payouts − gastos")],
      frame("payouts", lang, t(T("Payouts and expenses with net realized income","Payouts et dépenses avec revenu net réalisé","Payouts y gastos con ingreso neto realizado")), t), flip=True, id_="payouts"))
    S.append(f'''<section id="share-cards" class="rule"><div class="wrap split">
<div class="copy"><span class="kick">{t(T("Share cards","Cartes à partager","Tarjetas para compartir"))}</span><h2>{t(T("Your payouts, beautifully shared.","Tes payouts, partagés avec style.","Tus payouts, compartidos con estilo."))}</h2>
<p class="lead">{t(T("Branded cards for a payout, a green week, your net after fees, a day or a single trade, ready for Instagram, X, Discord or Messages.","Des cartes à ton image pour un payout, une semaine verte, ton net après frais, une journée ou un trade, prêtes pour Instagram, X, Discord ou Messages.","Tarjetas con marca para un payout, una semana en verde, tu neto tras comisiones, un día o una operación, listas para Instagram, X, Discord o Mensajes."))}</p>
{ul(t,[T("<b>Formats:</b> Post, Story and Wide","<b>Formats :</b> publication, story et large","<b>Formatos:</b> publicación, historia y panorámico"),
 T("<b>Amounts optional:</b> hide dollars and show win rate, R or return on fees instead","<b>Montants optionnels :</b> masque les dollars et montre plutôt le taux de réussite, le R ou le rendement sur frais","<b>Importes opcionales:</b> oculta los dólares y muestra la tasa de acierto, la R o el retorno sobre comisiones"),
 T("<b>Hide the prop firm</b> with one switch","<b>Masque la prop firm</b> d’un seul bouton","<b>Oculta la prop firm</b> con un interruptor"),
 T("<b>Payout moment:</b> mark a payout as paid and the card opens on its own","<b>Moment payout :</b> marque un payout comme payé et la carte s’ouvre toute seule","<b>Momento payout:</b> marca un payout como pagado y la tarjeta se abre sola"),
 T("<b>Private:</b> images are made on your phone; nothing is uploaded","<b>Privé :</b> les images sont créées sur ton téléphone; rien n’est téléversé","<b>Privado:</b> las imágenes se crean en tu teléfono; no se sube nada")])}</div>
<div class="reveal share-duo"><figure class="scard">{share_img("share-weekly-hidden",t(T("Weekly recap card with amounts hidden","Carte récap hebdo avec montants masqués","Tarjeta semanal con importes ocultos")),1080,1350,"(max-width: 860px) 44vw, 280px")}</figure><figure class="scard">{share_img("share-payout",t(T("Payout received card","Carte payout reçu","Tarjeta de payout recibido")),1080,1350,"(max-width: 860px) 44vw, 280px")}</figure>
<figure class="scard wide">{share_img("share-trade",t(T("Trade card, wide format","Carte de trade, format large","Tarjeta de operación, formato panorámico")),1200,675,"(max-width: 860px) 90vw, 580px")}</figure>
<div class="cards3">{slot("carte-journee-balayee.webp","card",t(T("Swept day share card","Carte à partager « journée balayée »","Tarjeta para compartir «día barrido»")),t,cap=False)}{slot("carte-payout.webp","card",t(T("Ready-for-payout share card","Carte à partager « prêt pour le payout »","Tarjeta para compartir «listo para el payout»")),t,cap=False)}{slot("carte-wrapped.webp","card",t(T("Wrapped share card, no amounts","Carte à partager Wrapped, sans montant","Tarjeta para compartir Wrapped, sin importes")),t,cap=False)}</div>
<p class="cap" style="grid-column:1/-1">{t(T("Examples made from sample data.","Exemples créés avec des données d’exemple.","Ejemplos creados con datos de ejemplo."))}</p></div></div></section>''')
    S.append(split(t, T("Sync","Synchro","Sincronización"), T("Log on your phone. Review on your desktop.","Note sur ton téléphone. Révise sur ton ordi.","Registra en el móvil. Revisa en el ordenador."),
      T("Your data refreshes when you come back to the app, every minute while it’s open, and with pull to refresh on phones.","Tes données se rafraîchissent quand tu reviens dans l’app, chaque minute pendant qu’elle est ouverte, et en tirant vers le bas sur téléphone.","Tus datos se actualizan al volver a la app, cada minuto mientras está abierta y al deslizar hacia abajo en el móvil."),
      [T("Same account on every device","Le même compte sur tous tes appareils","La misma cuenta en todos tus dispositivos"),
       T("Pull to refresh on phones","Tirer pour actualiser sur téléphone","Deslizar para actualizar en el móvil"),
       T("Works in any modern browser, installable on your home screen","Fonctionne dans tout navigateur récent, installable sur ton écran d’accueil","Funciona en cualquier navegador moderno, instalable en tu pantalla de inicio")],
      frame("trades", lang, t(T("Trades list","Liste des trades","Lista de operaciones")), t), flip=True, id_="sync"))
    S.append(sec_trust(lang, t, id_="data"))
    mob = f'''<section id="mobile" class="rule"><div class="wrap">
<div class="head"><span class="kick">{t(T("Phone & desktop","Téléphone & ordi","Móvil y escritorio"))}</span><h2>{t(T("Fast on the phone. Faster on the desktop.","Rapide sur téléphone. Encore plus sur ordi.","Rápido en el móvil. Más rápido en el escritorio."))}</h2>
<p class="lead">{t(T("The app is cached on your device, so after the first visit it opens almost instantly.","L’app est gardée en cache sur ton appareil : après la première visite, elle s’ouvre presque instantanément.","La app se guarda en caché en tu dispositivo: tras la primera visita, se abre casi al instante."))}</p></div>
<div class="phones rail reveal" style="margin-bottom:64px">{capphone("ecran-plan-du-jour.webp",t(T("Daily plan","Plan du jour","Plan del día")))}{capphone("ecran-revue-60s.webp",t(T("60-second review","Revue en 60 secondes","Revisión en 60 segundos")))}{capphone("ecran-analyses-tel.webp",t(T("Analytics on a phone","Analyses sur téléphone","Análisis en el teléfono")))}</div>
{grid(t,[("phone",T("Phone first","Mobile d’abord","Primero el móvil"),T("A 2-step trade entry, iOS-style filters with removable chips, accounts, payouts and expenses as cards, a swipeable journal day strip and calendar, sheets that swipe away.","Une saisie en 2 étapes, des filtres style iOS avec puces amovibles, comptes, payouts et dépenses en cartes, une bande de jours et un calendrier à balayer, des fenêtres qui se ferment d’un glissement.","Registro en 2 pasos, filtros estilo iOS con chips quitables, cuentas, payouts y gastos en tarjetas, franja de días y calendario deslizables, paneles que se cierran deslizando.")),
("command",T("Keyboard first","Clavier d’abord","Primero el teclado"),T("⌘K or Ctrl+K command palette. N new trade, J and K to move, / to search, ⌘ or Ctrl+Enter to save.","Palette de commandes ⌘K ou Ctrl+K. N nouveau trade, J et K pour naviguer, / pour chercher, ⌘ ou Ctrl+Entrée pour enregistrer.","Paleta de comandos ⌘K o Ctrl+K. N nueva operación, J y K para moverte, / para buscar, ⌘ o Ctrl+Enter para guardar.")),
("globe",T("Your language, your theme","Ta langue, ton thème","Tu idioma, tu tema"),T("English, French or Spanish from your browser. Dark or light from your device.","Anglais, français ou espagnol selon ton navigateur. Foncé ou clair selon ton appareil.","Inglés, francés o español según tu navegador. Oscuro o claro según tu dispositivo."))])}
<div style="margin-top:48px">{chips()}</div>
</div></section>'''
    S.append(mob)
    return (t(T("Features · Sweep trading journal","Fonctionnalités · Journal de trading Sweep","Funciones · Diario de trading Sweep")),
            t(T("Trade ticket with live risk, automatic rule checks, guided trade review, insights and performance score, P&L calendar, economic calendar, prop accounts, payouts and expenses.",
                "Ticket de trade avec risque en direct, vérification automatique des règles, révision guidée, analyses et score de performance, calendrier P&L, calendrier économique, comptes prop, payouts et dépenses.",
                "Ticket con riesgo en vivo, revisión automática de reglas, revisión guiada, análisis y puntuación de rendimiento, calendario de P&L, calendario económico, cuentas prop, payouts y gastos.")),
            hero + sub + "".join(S) + final_cta(lang, t), "")

# ============================ PROP TRADERS ============================
def page_prop(lang, t):
    hero = page_hero(t, T("Every account. Every payout. One record.","Chaque compte. Chaque payout. Un seul historique.","Cada cuenta. Cada payout. Un solo historial."),
        T("Evaluations, funded and live accounts across every firm, with the rules already loaded.","Évaluations, comptes financés et live, toutes firmes confondues, avec les règles déjà chargées.","Evaluaciones, cuentas fondeadas y live de todas las firmas, con las reglas ya cargadas."),
        T("For prop traders","Pour traders prop","Para traders prop"), f'<a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(CREATE_FREE)}</a>')
    pains = grid(t, [
      ("archive", T("Lose the account, keep the data","Perds le compte, garde les données","Pierde la cuenta, conserva los datos"), T("Firm dashboards usually vanish with the account. In Sweep, closed accounts keep their full history, marked as failed, passed or closed.","Les tableaux de bord des firmes disparaissent souvent avec le compte. Dans Sweep, les comptes fermés gardent tout leur historique, marqués échoués, réussis ou fermés.","Los paneles de las firmas suelen desaparecer con la cuenta. En Sweep, las cuentas cerradas conservan todo su historial, marcadas como fallidas, aprobadas o cerradas.")),
      ("shield", T("Know your room before you trade","Connais ta marge avant de trader","Conoce tu margen antes de operar"), T("Drawdown room, target progress and daily limit bars on every account, and your daily risk budget inside the trade ticket.","Barres de marge de drawdown, de progression vers la cible et de limite quotidienne sur chaque compte, et ton budget de risque dans le ticket.","Barras de margen de drawdown, progreso al objetivo y límite diario en cada cuenta, y tu presupuesto de riesgo dentro del ticket.")),
      ("copy", T("Copy one decision to many accounts","Copie une décision sur plusieurs comptes","Copia una decisión a varias cuentas"), T("The trade copier logs the same trade on several accounts. Notes, checklist and screenshots stay in sync; size and P&L stay per account.","Le copieur note le même trade sur plusieurs comptes. Notes, checklist et captures restent synchronisées; taille et P&L restent par compte.","El copiador registra la misma operación en varias cuentas. Notas, checklist y capturas se sincronizan; tamaño y P&L quedan por cuenta.")),
      ("net", T("See if prop trading pays","Vois si le trading prop paie","Mira si el trading prop paga"), T("Payouts against evaluations, activations, resets and data fees. Net realized income across every firm.","Payouts face aux évaluations, activations, resets et frais de données. Revenu net réalisé, toutes firmes confondues.","Payouts frente a evaluaciones, activaciones, reinicios y cuotas de datos. Ingreso neto realizado en todas las firmas.")),
    ], "g2")
    from pages9 import sec_rules
    body = sec_rules(lang, t, id_="presets", link=False)
    from pages8 import firm_row, rule_change
    body += firm_row(lang, t) + rule_change(lang, t) + f'<section class="rule"><div class="wrap">{pains}</div></section>'
    rules_tbl = [(T("Profit target","Cible de profit","Objetivo de ganancia"),T("Progress bar toward the target","Barre de progression vers la cible","Barra de progreso hacia el objetivo")),
                 (T("Max drawdown","Drawdown max","Drawdown máximo"),T("Trailing end of day, trailing trade by trade, or static","Trailing fin de journée, trailing trade par trade, ou statique","Trailing al cierre, trailing por operación o estático")),
                 (T("Daily loss limit","Perte quotidienne max","Pérdida diaria máxima"),T("Live budget in the ticket, warning when exceeded","Budget en direct dans le ticket, alerte si dépassé","Presupuesto en vivo en el ticket, aviso si se supera")),
                 (T("Consistency","Consistance","Consistencia"),T("Percentage rule per account","Règle en pourcentage par compte","Regla en porcentaje por cuenta")),
                 (T("Minimum trading days","Jours de trading minimum","Días mínimos de trading"),T("Tracked per account","Suivis par compte","Seguimiento por cuenta"))]
    tbl = '<table class="tbl"><tbody>' + "".join(f"<tr><th>{t(a)}</th><td>{t(b)}</td></tr>" for a,b in rules_tbl) + "</tbody></table>"
    body += split(t, T("Firm rules","Règles des firmes","Reglas de las firmas"), T("Set the rules once. See where you stand all day.","Entre les règles une fois. Vois où tu en es toute la journée.","Configura las reglas una vez. Ve dónde estás todo el día."),
      T("Each account carries its own rules, so an evaluation and a funded account can live side by side.","Chaque compte a ses propres règles : une évaluation et un compte financé peuvent cohabiter.","Cada cuenta tiene sus propias reglas: una evaluación y una cuenta fondeada pueden convivir."),
      [], frame("overview", lang, t(T("Account cards with drawdown, target and daily limit","Cartes de comptes avec drawdown, cible et limite quotidienne","Tarjetas de cuentas con drawdown, objetivo y límite diario")), t), more=f'<div style="margin-top:28px">{tbl}</div>')
    body += split(t, T("Payouts and expenses","Payouts et dépenses","Payouts y gastos"), T("Payouts on one side. Costs on the other.","Les payouts d’un côté. Les coûts de l’autre.","Payouts por un lado. Costos por el otro."),
      T("Every payout from request to payment, every evaluation, reset and fee. The bottom line tells you whether your prop trading is a business.","Chaque payout de la demande au paiement, chaque évaluation, reset et frais. La ligne du bas te dit si ton trading prop est une entreprise.","Cada payout de la solicitud al pago, cada evaluación, reinicio y cuota. La última línea te dice si tu trading prop es un negocio."),
      [T("Planned, requested, approved, paid or rejected","Prévu, demandé, approuvé, payé ou refusé","Planificado, solicitado, aprobado, pagado o rechazado"),
       T("Evaluation, activation, reset, data and platform fees","Évaluation, activation, reset, frais de données et de plateforme","Evaluación, activación, reinicio, cuotas de datos y plataforma"),
       T("Net realized income = payouts − expenses","Revenu net réalisé = payouts − dépenses","Ingreso neto realizado = payouts − gastos")],
      frame("payouts", lang, t(T("Payouts and expenses summary","Résumé des payouts et dépenses","Resumen de payouts y gastos")), t), flip=True)
    body += split(t, T("Evaluations","Évaluations","Evaluaciones"), T("Keep your rules, especially on the hard days.","Respecte tes règles, surtout les jours difficiles.","Cumple tus reglas, sobre todo en los días difíciles."),
      T("Evaluations are rarely lost on the setup. They’re lost on the one trade that breaks the plan. Sweep makes that trade impossible to miss.","Les évaluations se perdent rarement sur le setup. Elles se perdent sur le trade qui brise le plan. Sweep rend ce trade impossible à manquer.","Las evaluaciones rara vez se pierden por el setup. Se pierden por la operación que rompe el plan. Sweep hace que esa operación sea imposible de ignorar."),
      [T("Rule checks on every trade, counted in your discipline","Vérification des règles sur chaque trade, comptée dans ta discipline","Revisión de reglas en cada operación, contada en tu disciplina"),
       T("What changes after a loss: size, frequency, results","Ce qui change après une perte : taille, fréquence, résultats","Qué cambia tras una pérdida: tamaño, frecuencia, resultados"),
       T("Violations ranked by what they cost you","Infractions classées selon ce qu’elles t’ont coûté","Infracciones ordenadas por lo que te costaron")],
      fm("insights")("insights-discipline", lang, t(T("Discipline insights","Analyses de discipline","Análisis de disciplina")), t))
    body += f'''<section class="rule"><div class="wrap split flip"><div class="copy"><span class="kick">{t(T("Share cards","Cartes à partager","Tarjetas para compartir"))}</span><h2>{t(T("Celebrate the payout. Show the real net.","Célèbre le payout. Montre le vrai net.","Celebra el payout. Muestra el neto real."))}</h2>
<p class="lead">{t(T("Mark a payout as paid and a branded card opens on its own. Or share your net after fees, with your return on fees, and keep the amounts hidden if you prefer.","Marque un payout comme payé et une carte à ton image s’ouvre toute seule. Ou partage ton net après frais, avec ton rendement sur frais, en gardant les montants masqués si tu préfères.","Marca un payout como pagado y se abre sola una tarjeta con marca. O comparte tu neto tras comisiones, con tu retorno sobre comisiones, ocultando los importes si prefieres."))}</p>
<p class="meta">{t(T("The number of prop accounts depends on your plan.","Le nombre de comptes prop dépend de ton forfait.","El número de cuentas prop depende de tu plan."))}</p></div>
<div class="reveal share-duo"><figure class="scard">{share_img("share-payout",t(T("Payout received card, sample data","Carte payout reçu, données d’exemple","Tarjeta de payout recibido, datos de ejemplo")),1080,1350,"(max-width: 860px) 44vw, 280px")}</figure><figure class="scard">{share_img("share-net",t(T("Net after fees card, sample data","Carte net après frais, données d’exemple","Tarjeta de neto tras comisiones, datos de ejemplo")),1080,1920,"(max-width: 860px) 44vw, 280px")}</figure></div></div></section>'''
    note = f'<div class="wrap"><div class="notice">{ico(I["shield"])}<span>{t(T("Sweep is independent and is not affiliated with, endorsed by or connected to any proprietary trading firm. Firm names belong to their owners. Rules prefilled for guidance only: always check your firm’s current rules.","Sweep est indépendant et n’est affilié à aucune firme de trading pour compte propre, ni approuvé par elle. Les noms des firmes appartiennent à leurs propriétaires. Règles préremplies à titre indicatif : vérifie toujours les règles actuelles de ta firme.","Sweep es independiente y no está afiliado, respaldado ni vinculado a ninguna prop firm. Los nombres de las firmas pertenecen a sus propietarios. Reglas precargadas a título indicativo: verifica siempre las reglas actuales de tu firma."))}</span></div></div>'
    k = body.rfind('</section>'); body = body[:k] + note + body[k:]
    return (t(T("Prop firm trading journal · Track accounts, rules and payouts · Sweep","Journal de trading prop firm · Comptes, règles et payouts · Sweep","Diario de trading para prop firms · Cuentas, reglas y payouts · Sweep")),
            t(T("Track every prop firm account with its drawdown, daily limit and target rules, copy trades across accounts, and see payouts minus evaluation fees. History kept after an account fails.",
                "Suis chaque compte prop avec ses règles de drawdown, limite quotidienne et cible, copie tes trades sur plusieurs comptes, et vois tes payouts moins les frais d’évaluation. Historique conservé après un échec.",
                "Sigue cada cuenta prop con sus reglas de drawdown, límite diario y objetivo, copia operaciones entre cuentas y ve tus payouts menos las cuotas de evaluación. Historial conservado tras una cuenta fallida.")),
            hero + body + final_cta(lang, t, T("Keep every account on record.","Garde chaque compte dans ton historique.","Guarda cada cuenta en tu historial.")), "")

# ============================ HOW IT WORKS ============================
def page_how(lang, t):
    hero = page_hero(t, T("From sign-up to your first insights.","De l’inscription à tes premières analyses.","Del registro a tus primeros análisis."),
        T("Five steps, a few minutes of setup, and about 30 seconds per trade after that.","Cinq étapes, quelques minutes de configuration, puis environ 30 secondes par trade.","Cinco pasos, unos minutos de configuración y unos 30 segundos por operación después."),
        T("How it works","Comment ça marche","Cómo funciona"))
    st = [("signup-split", T("Create your account","Crée ton compte","Crea tu cuenta"), T("A username, an email and a password. Start on the Free plan with Pro free for 14 days, no card needed. Then a short welcome sets up your first account with one-tap prop firm suggestions and balance presets, or lets you explore with sample data first.","Un nom d’utilisateur, un courriel et un mot de passe. Commence avec le forfait Free et Pro gratuit 14 jours, sans carte. Un court accueil configure ensuite ton premier compte avec des suggestions de prop firms et des soldes prédéfinis, ou te laisse explorer avec des données d’exemple.","Un usuario, un correo y una contraseña. Empieza con el plan Free y Pro gratis 14 días, sin tarjeta. Luego una breve bienvenida configura tu primera cuenta con sugerencias de prop firms y saldos predefinidos, o te deja explorar con datos de ejemplo."), "desktop"),
          ("welcome", T("Add your accounts and their rules","Ajoute tes comptes et leurs règles","Añade tus cuentas y sus reglas"), T("Each prop or personal account with its target, drawdown type, daily loss limit and other firm rules.","Chaque compte prop ou personnel avec sa cible, son type de drawdown, sa perte quotidienne max et les autres règles de la firme.","Cada cuenta prop o personal con su objetivo, tipo de drawdown, pérdida diaria máxima y demás reglas."), "desktop"),
          ("new-trade", T("Log a trade","Ajoute un trade","Registra una operación"), T("About 30 seconds in the ticket, or import your history from a Tradovate CSV. Then answer your discipline checklist.","Environ 30 secondes dans le ticket, ou importe ton historique depuis un CSV Tradovate. Puis réponds à ta checklist de discipline.","Unos 30 segundos en el ticket, o importa tu historial desde un CSV de Tradovate. Luego responde tu checklist."), "desktop"),
          ("trade-review", T("Review it in four steps","Révise-le en quatre étapes","Revísala en cuatro pasos"), T("Checklist, psychology, notes and screenshots, with the chart of your levels and the news around the trade.","Checklist, psychologie, notes et captures, avec le graphique de tes niveaux et les nouvelles autour du trade.","Checklist, psicología, notas y capturas, con el gráfico de tus niveles y las noticias alrededor."), "desktop"),
          ("insights", T("Read your insights","Lis tes analyses","Lee tus análisis"), T("After 10 trades your performance score appears. Patterns to watch show up as soon as a group has 5 trades.","Après 10 trades, ton score de performance apparaît. Les tendances à surveiller arrivent dès qu’un groupe compte 5 trades.","Tras 10 operaciones aparece tu puntuación. Los patrones a vigilar aparecen cuando un grupo tiene 5 operaciones."), "desktop")]
    items = "".join(f'<li><div><span class="n"></span><h2 style="font-size:clamp(22px,2.2vw,30px)">{t(h)}</h2><p>{t(p)}</p></div><div class="reveal">{frame(s,lang,t(h),t,mobile={"signup-split":"signup"}.get(s))}</div></li>' for s,h,p,k in st)
    body = f'<section style="padding-top:24px"><div class="wrap"><ol class="steps">{items}</ol></div></section>'
    ld = jsonld({"@context":"https://schema.org","@type":"HowTo","name":t(T("How to start with Sweep","Comment commencer avec Sweep","Cómo empezar con Sweep")),
        "step":[{"@type":"HowToStep","position":i+1,"name":t(h),"text":t(p)} for i,(s,h,p,k) in enumerate(st)]})
    return (t(T("How Sweep works · Start your trading journal in minutes","Comment fonctionne Sweep · Ton journal de trading en quelques minutes","Cómo funciona Sweep · Empieza tu diario de trading en minutos")),
            t(T("Create an account, add your prop accounts and rules, log a trade in 30 seconds, review it in four steps and read your insights after 10 trades.",
                "Crée un compte, ajoute tes comptes prop et leurs règles, note un trade en 30 secondes, révise-le en quatre étapes et lis tes analyses après 10 trades.",
                "Crea una cuenta, añade tus cuentas prop y reglas, registra una operación en 30 segundos, revísala en cuatro pasos y lee tus análisis tras 10 operaciones.")),
            hero + body + final_cta(lang, t), ld)
