from core import *

# Lot C landing pages: the free trading journal (more to come in C-2). Facts come from the pricing page, never invented.

def _faq_ld(t, faqs):
    return jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in faqs]})

FREE_MORE = T("""<h2>Who it’s for</h2><p>Sweep is built for futures traders, on markets like NQ, ES, CL, GC and their micros:</p><ul>
<li><b>Prop firm traders,</b> with evaluations and funded accounts, who want each firm’s rules checked on every trade.</li>
<li><b>Traders with a personal account</b> at a broker, side by side with their prop accounts.</li>
<li><b>Traders starting a journal,</b> who want a daily habit without building a spreadsheet.</li></ul>
<p>Sweep is for futures only: no stocks, options or forex.</p>
<h2>What Pro adds, and when you need it</h2><p>Every new account gets Pro for its first 60 days, so you can try everything. After that, you move to Free automatically: nothing is charged and nothing is lost. Pro, at $19 a month or $159 a year, adds more prop accounts, a bigger Sweep AI quota, the complete path and three weekly missions. Elite, at $39 a month or $329 a year, has the most accounts and the most AI. See every difference on the <a href="@pricing.html">pricing page</a>.</p>
<h2>A free journal or a spreadsheet?</h2><p>A spreadsheet is free too, but you type every number, compute every P&L and recheck your firm’s rules yourself. Sweep fills in the tick values and the P&L, checks each trade against your account’s rules, and keeps the chart, the screenshot and your notes with every trade. Prefer paper to start? Our <a href="@trading-templates.html">free templates</a> are a good first step.</p>
<h2>Compared with other journals</h2><p>See Sweep side by side with <a href="@sweep-vs-tradezella.html">TradeZella</a>, <a href="@sweep-vs-tradervue.html">Tradervue</a>, <a href="@sweep-vs-tradersync.html">TraderSync</a> and <a href="@sweep-vs-edgewonk.html">Edgewonk</a>: price, prop firm rules and features. Or read our comparison of the <a href="@best-trading-journal-for-prop-firms.html">best trading journals for prop firm traders</a>.</p>
<h2>Free doesn’t mean paid with your data</h2><p>Sweep has no ads, and your data is never sold. Your trades are private by default, and you can export everything or delete your account yourself, at any time. More on <a href="@security.html">security and data</a>.</p>""",
"""<h2>Pour qui</h2><p>Sweep est fait pour les traders de futures, sur des marchés comme NQ, ES, CL, GC et leurs micros :</p><ul>
<li><b>Les traders de prop firms,</b> avec des évaluations et des comptes financés, qui veulent que les règles de chaque firme soient vérifiées à chaque trade.</li>
<li><b>Les traders qui ont un compte personnel</b> chez un courtier, à côté de leurs comptes prop.</li>
<li><b>Ceux qui commencent un journal</b> et veulent une habitude quotidienne sans monter un tableur.</li></ul>
<p>Sweep est fait pour les futures seulement : pas d’actions, d’options ni de forex.</p>
<h2>Ce que Pro ajoute, et quand tu en as besoin</h2><p>Chaque nouveau compte a Pro pendant ses 60 premiers jours, pour tout essayer. Ensuite, tu passes automatiquement à Free : rien n’est facturé et rien n’est perdu. Pro, à 19 $ par mois ou 159 $ par an, ajoute plus de comptes prop, un quota Sweep AI plus grand, le parcours complet et trois missions par semaine. Elite, à 39 $ par mois ou 329 $ par an, offre le plus de comptes et le plus d’IA. Toutes les différences sont sur la <a href="@pricing.html">page des tarifs</a>.</p>
<h2>Un journal gratuit ou un tableur ?</h2><p>Un tableur est gratuit lui aussi, mais tu tapes chaque chiffre, tu calcules chaque P&L et tu revérifies toi-même les règles de ta firme. Sweep remplit les valeurs de tick et le P&L, vérifie chaque trade contre les règles de ton compte, et garde le graphique, la capture et tes notes avec chaque trade. Tu préfères commencer sur papier ? Nos <a href="@trading-templates.html">modèles gratuits</a> sont un bon premier pas.</p>
<h2>Comparé aux autres journaux</h2><p>Vois Sweep côte à côte avec <a href="@sweep-vs-tradezella.html">TradeZella</a>, <a href="@sweep-vs-tradervue.html">Tradervue</a>, <a href="@sweep-vs-tradersync.html">TraderSync</a> et <a href="@sweep-vs-edgewonk.html">Edgewonk</a> : prix, règles des prop firms et fonctions. Ou lis notre comparatif des <a href="@best-trading-journal-for-prop-firms.html">meilleurs journaux de trading pour les prop firms</a>.</p>
<h2>Gratuit ne veut pas dire payé avec tes données</h2><p>Sweep n’a pas de publicité, et tes données ne sont jamais vendues. Tes trades sont privés par défaut, et tu peux tout exporter ou supprimer ton compte toi-même, en tout temps. Plus de détails sur la page <a href="@security.html">sécurité et données</a>.</p>""",
"""<h2>Para quién</h2><p>Sweep está hecho para traders de futuros, en mercados como NQ, ES, CL, GC y sus micros:</p><ul>
<li><b>Traders de prop firms,</b> con evaluaciones y cuentas fondeadas, que quieren que las reglas de cada firma se revisen en cada operación.</li>
<li><b>Traders con una cuenta personal</b> en un bróker, junto a sus cuentas prop.</li>
<li><b>Quienes empiezan un diario</b> y quieren un hábito diario sin montar una hoja de cálculo.</li></ul>
<p>Sweep es solo para futuros: sin acciones, opciones ni forex.</p>
<h2>Qué añade Pro y cuándo lo necesitas</h2><p>Cada cuenta nueva tiene Pro durante sus primeros 60 días, para probarlo todo. Después pasas a Free automáticamente: no se cobra nada y no se pierde nada. Pro, a 19 $ al mes o 159 $ al año, añade más cuentas prop, una cuota mayor de Sweep AI, el recorrido completo y tres misiones semanales. Elite, a 39 $ al mes o 329 $ al año, tiene las cuentas y la IA al máximo. Todas las diferencias están en la <a href="@pricing.html">página de precios</a>.</p>
<h2>¿Un diario gratis o una hoja de cálculo?</h2><p>Una hoja de cálculo también es gratis, pero escribes cada cifra, calculas cada P&L y revisas tú mismo las reglas de tu firma. Sweep rellena los valores del tick y el P&L, comprueba cada operación con las reglas de tu cuenta y guarda el gráfico, la captura y tus notas con cada operación. ¿Prefieres empezar en papel? Nuestras <a href="@trading-templates.html">plantillas gratis</a> son un buen primer paso.</p>
<h2>Comparado con otros diarios</h2><p>Mira Sweep lado a lado con <a href="@sweep-vs-tradezella.html">TradeZella</a>, <a href="@sweep-vs-tradervue.html">Tradervue</a>, <a href="@sweep-vs-tradersync.html">TraderSync</a> y <a href="@sweep-vs-edgewonk.html">Edgewonk</a>: precio, reglas de prop firms y funciones. O lee nuestra comparativa de los <a href="@best-trading-journal-for-prop-firms.html">mejores diarios de trading para prop firms</a>.</p>
<h2>Gratis no significa pagar con tus datos</h2><p>Sweep no tiene publicidad y tus datos nunca se venden. Tus operaciones son privadas por defecto y puedes exportarlo todo o eliminar tu cuenta tú mismo, cuando quieras. Más en <a href="@security.html">seguridad y datos</a>.</p>""")

def page_free(lang, t):
    import ui
    hero = page_hero(t, T("A free trading journal for futures traders.", "Un journal de trading gratuit pour les traders de futures.", "Un diario de trading gratis para traders de futuros."),
        T("Free forever, not a trial: journal, calendar, analytics, real CME charts and a full export. Every new account also gets 60 days of Pro. No card.",
          "Gratuit pour toujours, pas un essai : journal, calendrier, analyses, vrais graphiques CME et export complet. Chaque nouveau compte a aussi 60 jours de Pro. Sans carte.",
          "Gratis para siempre, no una prueba: diario, calendario, análisis, gráficos reales de CME y exportación completa. Cada cuenta nueva tiene además 60 días de Pro. Sin tarjeta."),
        T("Free trading journal", "Journal de trading gratuit", "Diario de trading gratis"),
        f'<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_free">{t(CREATE)}</a>', visual=ui.frame_d("v6-11-calendar-d.webp", t(T("P&L calendar and daily journal in Sweep, sample data", "Calendrier P&L et journal quotidien dans Sweep, données d’exemple", "Calendario de P&L y diario en Sweep, datos de ejemplo")), m="v6-11-calendar-m.webp", t=t, sizes="(max-width: 1067px) 92vw, 1320px", cls="reveal zoom"))
    free = [T("<b>Journal, P&L calendar and analytics,</b> with the economic calendar", "<b>Journal, calendrier P&L et analyses,</b> avec le calendrier économique", "<b>Diario, calendario de P&L y análisis,</b> con el calendario económico"),
            T("<b>Real CME charts</b> for every trade", "<b>Vrais graphiques CME</b> pour chaque trade", "<b>Gráficos reales de CME</b> para cada operación"),
            T("<b>Log with AI,</b> from your own words or a screenshot", "<b>Saisie avec l’IA,</b> en mots simples ou à partir d’une capture", "<b>Registro con IA,</b> con tus palabras o desde una captura"),
            T("<b>Prop accounts</b> with their firm’s rules prefilled for guidance", "<b>Comptes prop</b> avec les règles de leur firme préremplies à titre indicatif", "<b>Cuentas prop</b> con las reglas de su firma precargadas a título indicativo"),
            T("<b>Rings, streak, badges and ranks,</b> leagues and crews", "<b>Anneaux, série, badges et rangs,</b> ligues et équipes", "<b>Anillos, racha, insignias y rangos,</b> ligas y equipos"),
            T("<b>Full export</b> of your data, anytime", "<b>Export complet</b> de tes données, en tout temps", "<b>Exportación completa</b> de tus datos, cuando quieras")]
    b = ui.split(t, T("Free plan", "Forfait Free", "Plan Free"), T("What stays free, forever.", "Ce qui reste gratuit, pour toujours.", "Lo que sigue siendo gratis, para siempre."), T("The whole daily loop is in the Free plan: log a trade, see it on a real chart, check your rules, review your day.",
                "Toute la boucle quotidienne est dans le forfait Free : ajoute un trade, vois-le sur un vrai graphique, vérifie tes règles, révise ta journée.",
                "Todo el ciclo diario está en el plan Free: registra una operación, mírala en un gráfico real, revisa tus reglas y tu día."), free, ui.frame_d("v6-01-today-d.webp", t(T("P&L calendar and daily journal in Sweep, sample data", "Calendrier P&L et journal quotidien dans Sweep, données d’exemple", "Calendario de P&L y diario en Sweep, datos de ejemplo")), m="v6-01-today-m.webp", t=t), id_="free")
    b += ui.sec(f'<article class="article">{localize(lang, t(FREE_MORE))}</article>', "n", width="read")
    faqs = [(T("Is Sweep really free?", "Sweep est-il vraiment gratuit ?", "¿Sweep es realmente gratis?"),
             T("Yes. The Free plan is free forever, and every new account also gets Pro for its first 60 days.", "Oui. Le forfait Free est gratuit pour toujours, et chaque nouveau compte a aussi Pro pendant ses 60 premiers jours.", "Sí. El plan Free es gratis para siempre, y cada cuenta nueva tiene además Pro durante sus primeros 60 días.")),
            (T("Do I need a credit card?", "Faut-il une carte de crédit ?", "¿Necesito una tarjeta?"),
             T("No. A card is only needed if you choose a paid plan.", "Non. Une carte n’est nécessaire que si tu choisis un forfait payant.", "No. Solo hace falta una tarjeta si eliges un plan de pago.")),
            (T("What happens after the 60 days of Pro?", "Que se passe-t-il après les 60 jours de Pro ?", "¿Qué pasa después de los 60 días de Pro?"),
             T("You move to the Free plan automatically. Nothing is charged and nothing is lost.", "Tu passes automatiquement au forfait Free. Rien n’est facturé et rien n’est perdu.", "Pasas al plan Free automáticamente. No se cobra nada y no se pierde nada.")),
            (T("Can I use the Free plan with a prop firm?", "Puis-je utiliser le forfait Free avec une prop firm ?", "¿Puedo usar el plan Free con una prop firm?"),
             T("Yes. Free includes prop accounts with their firm’s rules prefilled for guidance, with a limited number of accounts. Pro and Elite add more.", "Oui. Free comprend des comptes prop avec les règles de leur firme préremplies à titre indicatif, en nombre limité. Pro et Elite en ajoutent.", "Sí. Free incluye cuentas prop con las reglas de su firma precargadas a título indicativo, en número limitado. Pro y Elite añaden más."))]
    b += ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs), "n", "faq", width="read")
    return (t(T("Free Trading Journal for Futures & Prop Traders · Sweep", "Journal de trading gratuit pour futures · Sweep", "Diario de trading gratis para futuros · Sweep")),
            t(T("A free trading journal for futures and prop firm traders: journal, calendar, analytics, real CME charts and prop firm rules. Free forever, no card.",
                "Un journal de trading gratuit pour les traders de futures et de prop firms : journal, calendrier, analyses, graphiques CME et règles. Gratuit, sans carte.",
                "Un diario de trading gratis para traders de futuros y prop firms: diario, calendario, análisis, gráficos de CME y reglas. Gratis para siempre, sin tarjeta.")),
            hero + b + ui.final(lang, t), _faq_ld(t, faqs))

# ---------------------------------------------------------------- prop firm tracker (also the page for prop traders: /prop-traders redirects here)
CRUMBS["prop-firm-tracker.html"] = T("Prop firm tracker", "Suivi des comptes prop", "Seguimiento de cuentas prop")
TRACKER_MORE = T("""<h2>How it works</h2><ol>
<li><b>Add an account:</b> pick the firm, the account type and the size. For {FIRMS}, the rules fill in from Sweep’s preset, for guidance; for any other firm, you enter them once.</li>
<li><b>Add your trades:</b> from a screenshot, by importing your platform’s export, or automatically from NinjaTrader 8. The trade copier logs one trade on several accounts at once.</li>
<li><b>Watch each account update:</b> when an evaluation is passed, its funded account is created with the firm’s funded rules, and a funded account moves to live in one tap.</li>
<li><b>When an account ends,</b> it keeps its whole history, marked failed, passed or closed.</li></ol>
<h2>When a firm changes a rule</h2><p>Sweep checks every firm’s official pages each week. When a rule changes, you see what it means for your account and choose to apply it or keep yours. The current rules of each firm are on our <a href="@prop-firms/index.html">prop firm rules pages</a>.</p>
<h2>A tracker or a spreadsheet?</h2><p>A spreadsheet can list your accounts, but it won’t recompute a trailing drawdown after every trade, count winning days since your last payout, or warn you in the trade ticket when today’s limit is close. Sweep does, for every account at once.</p>""",
"""<h2>Comment ça marche</h2><ol>
<li><b>Ajoute un compte :</b> choisis la firme, le type de compte et la taille. Pour {FIRMS}, les règles se remplissent à partir du préréglage de Sweep, à titre indicatif ; pour toute autre firme, tu les saisis une fois.</li>
<li><b>Ajoute tes trades :</b> à partir d’une capture, en important l’export de ta plateforme, ou automatiquement depuis NinjaTrader 8. Le copieur de trades note un trade sur plusieurs comptes en une fois.</li>
<li><b>Regarde chaque compte se mettre à jour :</b> quand une évaluation est réussie, son compte financé est créé avec les règles financées de la firme, et un compte financé passe en live d’un toucher.</li>
<li><b>Quand un compte se termine,</b> il garde tout son historique, marqué échoué, réussi ou fermé.</li></ol>
<h2>Quand une firme change une règle</h2><p>Sweep vérifie chaque semaine les pages officielles de chaque firme. Quand une règle change, tu vois ce que ça veut dire pour ton compte et tu choisis de l’appliquer ou de garder la tienne. Les règles actuelles de chaque firme sont sur nos <a href="@prop-firms/index.html">pages de règles des prop firms</a>.</p>
<h2>Un suivi ou un tableur ?</h2><p>Un tableur peut lister tes comptes, mais il ne recalcule pas un drawdown suiveur après chaque trade, ne compte pas les jours gagnants depuis ton dernier payout et ne t’avertit pas dans le ticket quand la limite du jour approche. Sweep le fait, pour tous tes comptes à la fois.</p>""",
"""<h2>Cómo funciona</h2><ol>
<li><b>Añade una cuenta:</b> elige la firma, el tipo de cuenta y el tamaño. Para {FIRMS}, las reglas se rellenan desde el preajuste de Sweep, a título indicativo; para cualquier otra firma, las introduces una vez.</li>
<li><b>Añade tus operaciones:</b> desde una captura, importando la exportación de tu plataforma o automáticamente desde NinjaTrader 8. El copiador registra una operación en varias cuentas a la vez.</li>
<li><b>Mira cómo se actualiza cada cuenta:</b> al superar una evaluación, se crea su cuenta fondeada con las reglas fondeadas de la firma, y una cuenta fondeada pasa a live con un toque.</li>
<li><b>Cuando una cuenta termina,</b> conserva todo su historial, marcada como fallida, superada o cerrada.</li></ol>
<h2>Cuando una firma cambia una regla</h2><p>Sweep revisa cada semana las páginas oficiales de cada firma. Cuando una regla cambia, ves lo que significa para tu cuenta y eliges aplicarla o mantener la tuya. Las reglas actuales de cada firma están en nuestras <a href="@prop-firms/index.html">páginas de reglas de las prop firms</a>.</p>
<h2>¿Un seguimiento o una hoja de cálculo?</h2><p>Una hoja de cálculo puede listar tus cuentas, pero no recalcula un drawdown dinámico tras cada operación, no cuenta los días ganadores desde tu último payout ni te avisa en el ticket cuando se acerca el límite del día. Sweep lo hace, para todas tus cuentas a la vez.</p>""")

def page_tracker(lang, t):
    import ui
    hero = page_hero(t, T("Track every prop firm account in one place.", "Suis tous tes comptes de prop firm au même endroit.", "Sigue todas tus cuentas de prop firm en un solo lugar."),
        T("Evaluations, funded and live accounts across every firm, each with its own rules. Sweep shows where each one stands after every trade.",
          "Évaluations, comptes financés et live de toutes tes firmes, chacun avec ses propres règles. Sweep montre où en est chacun après chaque trade.",
          "Evaluaciones, cuentas fondeadas y live de todas tus firmas, cada una con sus propias reglas. Sweep muestra cómo va cada una tras cada operación."),
        T("Prop firm tracker", "Suivi des comptes prop", "Seguimiento de cuentas prop"),
        f'<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_tracker">{t(CREATE)}</a>', visual=ui.frame_d("v6-13-accounts-d.webp", t(T("Prop accounts side by side, sample data", "Comptes prop côte à côte, données d’exemple", "Cuentas prop lado a lado, datos de ejemplo")), m="v6-13-accounts-m.webp", t=t, sizes="(max-width: 1067px) 92vw, 1320px", cls="reveal zoom"))
    items = [T("<b>Target progress,</b> with the amount still to make", "<b>Progression vers l’objectif,</b> avec le montant qu’il reste à faire", "<b>Progreso hacia el objetivo,</b> con lo que falta por hacer"),
             T("<b>Room above the max loss,</b> trailing or static, and today’s loss limit", "<b>Marge au-dessus de la perte max,</b> suiveuse ou fixe, et la limite du jour", "<b>Margen sobre la pérdida máx.,</b> dinámica o fija, y el límite del día"),
             T("<b>Consistency and minimum days,</b> counted for you", "<b>Consistance et jours minimum,</b> comptés pour toi", "<b>Consistencia y días mínimos,</b> contados por ti"),
             T("<b>Ready for payout</b> in %, on funded accounts", "<b>Prêt pour le payout</b> en %, sur les comptes financés", "<b>Listo para el payout</b> en %, en las cuentas fondeadas"),
             T("<b>Status:</b> good standing, target reached, close to a limit, drawdown breached, daily limit hit", "<b>Statut :</b> en règle, objectif atteint, proche d’une limite, drawdown dépassé, limite du jour atteinte", "<b>Estado:</b> en regla, objetivo alcanzado, cerca de un límite, drawdown superado, límite diario alcanzado")]
    b = ui.split(t, T("On one screen", "Sur un seul écran", "En una sola pantalla"), T("Every account, where it stands.", "Chaque compte, là où il en est.", "Cada cuenta, cómo va."), T("Each account carries its firm, its type, its size and its rules, so an evaluation and a funded account can sit side by side.",
                "Chaque compte porte sa firme, son type, sa taille et ses règles : une évaluation et un compte financé peuvent vivre côte à côte.",
                "Cada cuenta lleva su firma, su tipo, su tamaño y sus reglas, así que una evaluación y una cuenta fondeada conviven sin problema."), items, ui.frame_d("v6-08-payout-conditions-d.webp", t(T("Prop accounts with the ready-for-payout meter, sample data", "Comptes prop avec le compteur prêt pour le payout, données d’exemple", "Cuentas prop con el indicador listo para el payout, datos de ejemplo")), m="v6-08-payout-conditions-m.webp", t=t), id_="accounts")
    from pages1 import prop_blocks, prop_notice
    b += prop_blocks(lang, t)   # what /prop-traders had (merged here, audit n° 3)
    b += ui.sec(f'<article class="article">{localize(lang, t(TRACKER_MORE)).replace("{FIRMS}", FIRMS_TXT[lang])}</article>' + prop_notice(lang, t), "n", "how", width="read")
    faqs = [(T("Which firms have preloaded rules?", "Quelles firmes ont des règles préremplies ?", "¿Qué firmas tienen reglas precargadas?"),
             T(f"{FIRMS_TXT['en']}. Any other firm can be added with its rules entered once.", f"{FIRMS_TXT['fr']}. Toute autre firme peut être ajoutée en saisissant ses règles une fois.", f"{FIRMS_TXT['es']}. Cualquier otra firma se puede añadir introduciendo sus reglas una vez.")),
            (T("How many accounts can I track?", "Combien de comptes puis-je suivre ?", "¿Cuántas cuentas puedo seguir?"),
             T("It depends on your plan: Free includes a limited number of prop accounts, Pro more and Elite the most.", "Ça dépend de ton forfait : Free comprend un nombre limité de comptes prop, Pro davantage et Elite le plus.", "Depende de tu plan: Free incluye un número limitado de cuentas prop, Pro más y Elite el máximo.")),
            (T("Does Sweep connect to my firm’s dashboard?", "Sweep se connecte-t-il au tableau de bord de ma firme ?", "¿Sweep se conecta al panel de mi firma?"),
             T("No. Your trades come from your platform, by import or NinjaTrader 8 sync, or from a screenshot, and Sweep applies your account’s rules to them.", "Non. Tes trades viennent de ta plateforme, par import ou synchro NinjaTrader 8, ou d’une capture, et Sweep leur applique les règles de ton compte.", "No. Tus operaciones vienen de tu plataforma, por importación o sincronización con NinjaTrader 8, o de una captura, y Sweep les aplica las reglas de tu cuenta.")),
            (T("Can I keep a failed account?", "Puis-je garder un compte échoué ?", "¿Puedo conservar una cuenta fallida?"),
             T("Yes. Closed and failed accounts keep their full history and stay in your filters.", "Oui. Les comptes fermés et échoués gardent tout leur historique et restent dans tes filtres.", "Sí. Las cuentas cerradas y fallidas conservan todo su historial y siguen en tus filtros."))]
    b += ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs), "n", "faq", width="read")
    return (t(T("Prop Firm Tracker & Trading Journal · Sweep", "Suivi des comptes prop et journal de trading · Sweep", "Seguimiento de cuentas prop y diario de trading · Sweep")),
            t(T("Track every prop firm account in one place: evaluations, funded and live, with each firm’s rules, drawdown room, consistency and payout readiness.",
                "Suis tous tes comptes de prop firm au même endroit : évaluations, financés et live, avec les règles, la marge de drawdown, la consistance et le payout.",
                "Sigue todas tus cuentas de prop firm en un solo lugar: evaluaciones, fondeadas y live, con las reglas, el margen de drawdown, la consistencia y el payout.")),
            hero + b + ui.final(lang, t), _faq_ld(t, faqs))

# ---------------------------------------------------------------- payout tracker
PAYOUT_MORE = T("""<h2>Expenses and your real net</h2><p>Next to the payouts, Sweep keeps every cost of prop trading: evaluations, activations, resets, data and platform fees. A monthly evaluation stops counting when its account ends. Your real net is the payouts you received plus your live and personal P&L, minus your expenses; simulated profits on evaluation and funded accounts are never added in.</p>
<h2>Start with your past payouts</h2><p>When you start, Sweep asks since when you want to track your money: this month, since January or a date of your choice. It prefills what you bought from each firm with catalogue prices you can edit, then asks for the payouts you received, so your real net is right from day one.</p>
<h2>Included in Pro and Elite</h2><p>Payouts, expenses and your real net live in My money, which is part of Pro and Elite, and every new account starts with Pro. The <a href="@payout-calculator.html">payout calculator</a> and the <a href="@prop-firm-roi-calculator.html">prop firm ROI calculator</a> stay free for everyone, and each firm’s conditions are compared in the <a href="@prop-firm-payout-rules.html">payout rules guide</a>.</p>""",
"""<h2>Les dépenses et ton vrai net</h2><p>À côté des payouts, Sweep garde chaque coût du trading prop : évaluations, activations, resets, frais de données et de plateforme. Une évaluation mensuelle arrête de compter quand son compte se termine. Ton vrai net, ce sont les payouts reçus plus ton P&L live et perso, moins tes dépenses ; les profits simulés des évaluations et des comptes financés n’y sont jamais ajoutés.</p>
<h2>Commence avec tes payouts passés</h2><p>Au départ, Sweep te demande depuis quand tu veux suivre ton argent : ce mois-ci, depuis janvier ou une date de ton choix. Il préremplit ce que tu as acheté chez chaque firme avec les prix du catalogue, modifiables, puis te demande les payouts reçus : ton vrai net est juste dès le premier jour.</p>
<h2>Inclus dans Pro et Elite</h2><p>Les payouts, les dépenses et ton vrai net sont dans Mon argent, qui fait partie de Pro et d’Elite, et chaque nouveau compte commence avec Pro. Le <a href="@payout-calculator.html">calculateur de payout</a> et le <a href="@prop-firm-roi-calculator.html">calculateur de rentabilité prop</a> restent gratuits pour tous, et les conditions de chaque firme sont comparées dans le <a href="@prop-firm-payout-rules.html">guide des règles de payout</a>.</p>""",
"""<h2>Los gastos y tu neto real</h2><p>Junto a los payouts, Sweep guarda cada coste del trading prop: evaluaciones, activaciones, reinicios, cuotas de datos y de plataforma. Una evaluación mensual deja de contar cuando su cuenta termina. Tu neto real son los payouts recibidos más tu P&L live y personal, menos tus gastos; los beneficios simulados de las evaluaciones y cuentas fondeadas nunca se suman.</p>
<h2>Empieza con tus payouts pasados</h2><p>Al empezar, Sweep te pregunta desde cuándo quieres seguir tu dinero: este mes, desde enero o una fecha que elijas. Precarga lo que compraste a cada firma con los precios del catálogo, editables, y luego te pide los payouts recibidos, así tu neto real es correcto desde el primer día.</p>
<h2>Incluido en Pro y Elite</h2><p>Los payouts, los gastos y tu neto real están en Mi dinero, que forma parte de Pro y Elite, y cada cuenta nueva empieza con Pro. La <a href="@payout-calculator.html">calculadora de payout</a> y la <a href="@prop-firm-roi-calculator.html">calculadora de rentabilidad prop</a> siguen siendo gratis para todos, y las condiciones de cada firma se comparan en la <a href="@prop-firm-payout-rules.html">guía de reglas de payout</a>.</p>""")

def page_payout_tracker(lang, t):
    import ui
    hero = page_hero(t, T("Track every payout, and what it really cost.", "Suis chaque payout, et ce qu’il t’a vraiment coûté.", "Sigue cada payout y lo que te costó de verdad."),
        T("From the first condition met to the money received: Sweep tracks your payouts, the fees behind them and your real net, firm by firm.",
          "De la première condition remplie à l’argent reçu : Sweep suit tes payouts, les frais derrière eux et ton vrai net, firme par firme.",
          "De la primera condición cumplida al dinero recibido: Sweep sigue tus payouts, los costes que hay detrás y tu neto real, firma por firma."),
        T("Payout tracker", "Suivi des payouts", "Seguimiento de payouts"),
        f'<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_payouts">{t(CREATE)}</a>', visual=ui.frame_d("v6-17b-share-one-payout-d.webp", t(T("A payout received, ready to share, sample data", "Un payout reçu, prêt à partager, données d’exemple", "Un payout recibido, listo para compartir, datos de ejemplo")), m="v6-17b-share-one-payout-m.webp", t=t, sizes="(max-width: 1067px) 92vw, 1320px", cls="reveal zoom"))
    items = [T("<b>Status:</b> planned, requested, approved, paid or rejected, with dates", "<b>Statut :</b> prévu, demandé, approuvé, payé ou refusé, avec les dates", "<b>Estado:</b> planificado, solicitado, aprobado, pagado o rechazado, con fechas"),
             T("<b>Ready for payout</b> in % on each funded account: winning days, cushion, minimum and maximum, counted since your last request", "<b>Prêt pour le payout</b> en % sur chaque compte financé : jours gagnants, coussin, minimum et maximum, comptés depuis ta dernière demande", "<b>Listo para el payout</b> en % en cada cuenta fondeada: días ganadores, colchón, mínimo y máximo, contados desde tu última solicitud"),
             T("<b>How much you can request,</b> after the cushion and within the limits", "<b>Combien tu peux demander,</b> après le coussin et dans les limites", "<b>Cuánto puedes pedir,</b> tras el colchón y dentro de los límites"),
             T("<b>A share card</b> when a payout is marked paid, amounts optional", "<b>Une carte à partager</b> quand un payout est marqué payé, montants optionnels", "<b>Una tarjeta para compartir</b> cuando un payout se marca como pagado, importes opcionales")]
    b = ui.split(t, T("Payouts", "Payouts", "Payouts"), T("From request to paid.", "De la demande au paiement.", "De la solicitud al pago."), T("Each payout has a status and its dates, so you always know what’s on the way.", "Chaque payout a un statut et ses dates : tu sais toujours ce qui s’en vient.", "Cada payout tiene un estado y sus fechas, así siempre sabes lo que está en camino."), items, ui.frame_d("v6-12-payouts-d.webp", t(T("Payouts and expenses with net realized income, sample data", "Payouts et dépenses avec le revenu net réalisé, données d’exemple", "Payouts y gastos con el ingreso neto realizado, datos de ejemplo")), m="v6-12-payouts-m.webp", t=t), id_="payouts")
    b += ui.sec(f'<article class="article">{localize(lang, t(PAYOUT_MORE))}</article>', "n", width="read")
    faqs = [(T("Does Sweep request the payout for me?", "Sweep demande-t-il le payout pour moi ?", "¿Sweep pide el payout por mí?"),
             T("No. You request it on your firm’s site; Sweep tells you when you can and tracks it until it’s paid.", "Non. Tu le demandes sur le site de ta firme ; Sweep te dit quand tu peux et le suit jusqu’au paiement.", "No. Lo pides en el sitio de tu firma; Sweep te dice cuándo puedes y lo sigue hasta el pago.")),
            (T("Is my net simulated or real?", "Mon net est-il simulé ou réel ?", "¿Mi neto es simulado o real?"),
             T("Real. Evaluation and funded profits are labeled simulated; only payouts received and live or personal P&L count in your real net.", "Réel. Les profits des évaluations et des comptes financés sont marqués simulés ; seuls les payouts reçus et le P&L live ou perso comptent dans ton vrai net.", "Real. Los beneficios de evaluaciones y cuentas fondeadas se marcan como simulados; solo los payouts recibidos y el P&L live o personal cuentan en tu neto real.")),
            (T("Can I export my payouts and expenses?", "Puis-je exporter mes payouts et mes dépenses ?", "¿Puedo exportar mis payouts y gastos?"),
             T("Yes. The full export includes CSV spreadsheets of your payouts and expenses, handy for your accountant.", "Oui. L’export complet comprend des tableurs CSV de tes payouts et de tes dépenses, pratiques pour ton comptable.", "Sí. La exportación completa incluye hojas CSV de tus payouts y gastos, útiles para tu contable.")),
            (T("Can I hide the amounts when I share?", "Puis-je masquer les montants quand je partage ?", "¿Puedo ocultar los importes al compartir?"),
             T("Yes. Share cards can hide the dollars and show your win rate, R or return on fees instead.", "Oui. Les cartes à partager peuvent masquer les dollars et montrer plutôt ton taux de réussite, ton R ou ton rendement sur frais.", "Sí. Las tarjetas pueden ocultar los dólares y mostrar en su lugar tu tasa de acierto, tu R o tu rendimiento sobre cuotas."))]
    b += ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs), "n", "faq", width="read")
    return (t(T("Prop Firm Payout Tracker: Payouts, Fees and Net · Sweep", "Suivi des payouts prop : payouts, frais et net · Sweep", "Seguimiento de payouts prop: payouts, gastos y neto · Sweep")),
            t(T("Track prop firm payouts from request to paid, with evaluations, resets and fees, your real net and when you can request your next payout.",
                "Suis tes payouts de prop firm de la demande au paiement, avec évaluations, resets et frais, ton vrai net et quand demander ton prochain payout.",
                "Sigue tus payouts de prop firm de la solicitud al pago, con evaluaciones, reinicios y cuotas, tu neto real y cuándo pedir tu próximo payout.")),
            hero + b + ui.final(lang, t), _faq_ld(t, faqs))

# ---------------------------------------------------------------- NinjaTrader 8 add-on (facts from app/CONTEXTE-APP.md, sync section)
NT8_MORE = T("""<h2>Install it once</h2><ol>
<li><b>In Sweep,</b> open Settings › Data › Connections, then NinjaTrader 8 › Connect. Download the add-on and copy your personal key: it’s shown only once.</li>
<li><b>In NinjaTrader 8,</b> go to Tools › Import › NinjaScript Add-On and choose the file you downloaded.</li>
<li><b>Open Control Center › New › Sweep Sync,</b> paste your key and save. The window shows that it’s connected.</li>
<li><b>Back in Sweep,</b> the accounts the add-on found appear: link each one to a Sweep account, or create it on the spot. Your trades start arriving.</li></ol>
<h2>What it sends, and what it never touches</h2><p>The add-on reads your executions: the account, the contract, the side, the quantity, the price, the time and the fees. It never places, changes or cancels an order, and it never sends your password or your balance. Sweep keeps only a fingerprint of your key; you can stop the sync or make a new key at any time, and the old one stops working.</p>
<h2>When NinjaTrader is closed or offline</h2><p>Executions wait on your computer and leave as soon as the connection is back. When NinjaTrader starts, the add-on sends the session’s executions again, and Sweep never counts the same one twice.</p>
<h2>Your trades from before</h2><p>The add-on sends what you trade from now on. For your history, export it from NinjaTrader’s Trade Performance window and <a href="@import.html#ninjatrader">import the CSV</a>: trades already synced are recognized and never imported twice.</p>""",
"""<h2>Installe-le une fois</h2><ol>
<li><b>Dans Sweep,</b> ouvre Réglages › Données › Connexions, puis NinjaTrader 8 › Connecter. Télécharge le module et copie ta clé personnelle : elle n’est montrée qu’une fois.</li>
<li><b>Dans NinjaTrader 8,</b> va dans Tools › Import › NinjaScript Add-On et choisis le fichier téléchargé.</li>
<li><b>Ouvre Control Center › New › Sweep Sync,</b> colle ta clé et enregistre. La fenêtre indique que c’est connecté.</li>
<li><b>De retour dans Sweep,</b> les comptes trouvés par le module s’affichent : relie chacun à un compte Sweep, ou crée-le sur place. Tes trades commencent à arriver.</li></ol>
<h2>Ce qu’il envoie, et ce qu’il ne touche jamais</h2><p>Le module lit tes exécutions : le compte, le contrat, le sens, la quantité, le prix, l’heure et les frais. Il ne passe, ne modifie et n’annule jamais d’ordre, et il n’envoie jamais ton mot de passe ni ton solde. Sweep ne garde qu’une empreinte de ta clé ; tu peux arrêter la synchro ou créer une nouvelle clé en tout temps, et l’ancienne cesse de fonctionner.</p>
<h2>Quand NinjaTrader est fermé ou hors ligne</h2><p>Les exécutions attendent sur ton ordinateur et partent dès que la connexion revient. Au démarrage de NinjaTrader, le module renvoie les exécutions de la séance, et Sweep ne compte jamais deux fois la même.</p>
<h2>Tes trades d’avant</h2><p>Le module envoie ce que tu trades à partir de maintenant. Pour ton historique, exporte-le depuis la fenêtre Trade Performance de NinjaTrader et <a href="@import.html#ninjatrader">importe le CSV</a> : les trades déjà synchronisés sont reconnus et jamais importés en double.</p>""",
"""<h2>Instálalo una vez</h2><ol>
<li><b>En Sweep,</b> abre Ajustes › Datos › Conexiones y luego NinjaTrader 8 › Conectar. Descarga el complemento y copia tu clave personal: solo se muestra una vez.</li>
<li><b>En NinjaTrader 8,</b> ve a Tools › Import › NinjaScript Add-On y elige el archivo descargado.</li>
<li><b>Abre Control Center › New › Sweep Sync,</b> pega tu clave y guarda. La ventana indica que está conectado.</li>
<li><b>De vuelta en Sweep,</b> aparecen las cuentas que encontró el complemento: vincula cada una a una cuenta de Sweep o créala ahí mismo. Tus operaciones empiezan a llegar.</li></ol>
<h2>Qué envía, y qué no toca nunca</h2><p>El complemento lee tus ejecuciones: la cuenta, el contrato, el sentido, la cantidad, el precio, la hora y las comisiones. Nunca envía, modifica ni cancela una orden, y nunca envía tu contraseña ni tu saldo. Sweep solo guarda una huella de tu clave; puedes detener la sincronización o crear una clave nueva cuando quieras, y la anterior deja de funcionar.</p>
<h2>Cuando NinjaTrader está cerrado o sin conexión</h2><p>Las ejecuciones esperan en tu ordenador y salen en cuanto vuelve la conexión. Al iniciar NinjaTrader, el complemento vuelve a enviar las ejecuciones de la sesión, y Sweep nunca cuenta dos veces la misma.</p>
<h2>Tus operaciones anteriores</h2><p>El complemento envía lo que operas a partir de ahora. Para tu historial, expórtalo desde la ventana Trade Performance de NinjaTrader e <a href="@import.html#ninjatrader">importa el CSV</a>: las operaciones ya sincronizadas se reconocen y nunca se importan dos veces.</p>""")

def page_ninjatrader(lang, t):
    import ui
    hero = page_hero(t, T("Your NinjaTrader\u00a08 trades, in your journal on their own.", "Tes trades NinjaTrader\u00a08, dans ton journal tout seuls.", "Tus operaciones de NinjaTrader\u00a08, en tu diario solas."),
        T("Sweep’s free add-on sends every execution from NinjaTrader 8 to your journal within seconds. Read only: it never places an order.",
          "Le module gratuit de Sweep envoie chaque exécution de NinjaTrader 8 à ton journal en quelques secondes. Lecture seule : il ne passe jamais d’ordre.",
          "El complemento gratuito de Sweep envía cada ejecución de NinjaTrader 8 a tu diario en segundos. Solo lectura: nunca envía una orden."),
        T("NinjaTrader 8", "NinjaTrader 8", "NinjaTrader 8"),
        f'<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_ninjatrader">{t(CREATE)}</a>')
    items = [T("<b>Every execution, grouped into trades:</b> partial entries and exits, and reversals", "<b>Chaque exécution, regroupée en trades :</b> entrées et sorties partielles, et retournements", "<b>Cada ejecución, agrupada en operaciones:</b> entradas y salidas parciales, y giros"),
             T("<b>P&L and fees</b> from your commissions and the contract’s point value", "<b>P&L et frais</b> à partir de tes commissions et de la valeur du point du contrat", "<b>P&L y comisiones</b> a partir de tus comisiones y del valor del punto del contrato"),
             T("<b>Every account found,</b> Apex accounts recognized; simulation accounts left aside until you link them", "<b>Chaque compte trouvé,</b> les comptes Apex reconnus ; les comptes de simulation mis de côté tant que tu ne les relies pas", "<b>Cada cuenta encontrada,</b> las cuentas Apex reconocidas; las de simulación quedan aparte hasta que las vinculas"),
             T("<b>Copied trades</b> grouped across your accounts", "<b>Trades copiés</b> regroupés entre tes comptes", "<b>Operaciones copiadas</b> agrupadas entre tus cuentas"),
             T("<b>Your notes, screenshots and review</b> are never overwritten, and a trade you logged by hand is completed, not doubled", "<b>Tes notes, captures et révisions</b> ne sont jamais écrasées, et un trade ajouté à la main est complété, pas doublé", "<b>Tus notas, capturas y revisiones</b> nunca se sobrescriben, y una operación registrada a mano se completa, no se duplica")]
    b = (ui.sec(f'<article class="article"><h2>{t(T("What it does", "Ce qu’il fait", "Qué hace"))}</h2>{ul(t, items)}</article>', "t", width="read")
         + ui.sec(f'<article class="article">{localize(lang, t(NT8_MORE))}</article>', "n", width="read"))
    faqs = [(T("Is the NinjaTrader 8 add-on free?", "Le module NinjaTrader 8 est-il gratuit ?", "¿El complemento de NinjaTrader 8 es gratis?"),
             T("Yes, on every plan, Free included.", "Oui, avec tous les forfaits, Free compris.", "Sí, en todos los planes, Free incluido.")),
            (T("Does it work with my prop firm account?", "Est-ce que ça marche avec mon compte de prop firm ?", "¿Funciona con mi cuenta de prop firm?"),
             T("It follows every account connected in your NinjaTrader 8, prop accounts included. You link each one to its Sweep account once, and Sweep checks every trade against that account’s rules.",
               "Il suit chaque compte connecté dans ton NinjaTrader 8, comptes prop compris. Tu relies chacun à son compte Sweep une fois, et Sweep vérifie chaque trade contre les règles de ce compte.",
               "Sigue cada cuenta conectada en tu NinjaTrader 8, cuentas prop incluidas. Vinculas cada una a su cuenta de Sweep una vez, y Sweep revisa cada operación con las reglas de esa cuenta.")),
            (T("Can the add-on place or change orders?", "Le module peut-il passer ou modifier des ordres ?", "¿El complemento puede enviar o modificar órdenes?"),
             T("No. It only reads your executions and never sends your password or your balance.", "Non. Il lit seulement tes exécutions et n’envoie jamais ton mot de passe ni ton solde.", "No. Solo lee tus ejecuciones y nunca envía tu contraseña ni tu saldo.")),
            (T("Can I edit a synced trade?", "Puis-je modifier un trade synchronisé ?", "¿Puedo editar una operación sincronizada?"),
             T("Yes. Notes, review, setup, tags, screenshots and fees are edited as usual, and you can set the stop and the target. Prices and P&L come from NinjaTrader.",
               "Oui. Notes, révision, setup, étiquettes, captures et frais se modifient comme d’habitude, et tu peux fixer le stop et la cible. Les prix et le P&L viennent de NinjaTrader.",
               "Sí. Las notas, la revisión, el setup, las etiquetas, las capturas y las comisiones se editan como siempre, y puedes fijar el stop y el objetivo. Los precios y el P&L vienen de NinjaTrader.")),
            (T("What about other platforms?", "Et les autres plateformes ?", "¿Y las demás plataformas?"),
             T(f'Sync is for NinjaTrader 8 for now; sync for Rithmic and Tradovate is in development. From any other platform, <a href="{href("en", "import.html")}">import a file or a screenshot</a>.',
               f'La synchro est pour NinjaTrader 8 pour l’instant ; celle de Rithmic et Tradovate est en développement. Depuis toute autre plateforme, <a href="{href("fr", "import.html")}">importe un fichier ou une capture</a>.',
               f'La sincronización es para NinjaTrader 8 por ahora; la de Rithmic y Tradovate está en desarrollo. Desde cualquier otra plataforma, <a href="{href("es", "import.html")}">importa un archivo o una captura</a>.'))]
    b += ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs), "n", "faq", width="read")
    return (t(T("NinjaTrader 8 Trading Journal: Free Auto Sync · Sweep", "Journal de trading NinjaTrader 8 : synchro gratuite · Sweep", "Diario de trading para NinjaTrader 8, gratis · Sweep")),
            t(T("Sync your NinjaTrader 8 trades to your trading journal with Sweep’s free add-on: every execution in seconds, read only, prop accounts included.",
                "Synchronise tes trades NinjaTrader 8 avec ton journal grâce au module gratuit de Sweep : chaque exécution en quelques secondes, en lecture seule.",
                "Sincroniza tus operaciones de NinjaTrader 8 con tu diario gracias al complemento gratuito de Sweep: cada ejecución en segundos, solo lectura.")),
            hero + b + ui.final(lang, t), _faq_ld(t, faqs))

SYSTEM_PAGES.update({"free-trading-journal.html", "prop-firm-tracker.html", "payout-tracker.html", "ninjatrader.html"})
