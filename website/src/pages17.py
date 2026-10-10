from core import *
import re

# Comparison pages (Sweep vs …). Competitor facts come from their public pages; update CHECKED when you re-verify them.
CHECKED = T("October 10, 2026","10 octobre 2026","10 de octubre de 2026")

def _cmp_table(t, rows, other):
    head = (f'<thead><tr><th scope="col"><span class="sr">{t(T("Feature","Fonctionnalité","Función"))}</span></th>'
            f'<th scope="col">Sweep</th><th scope="col">{other}</th></tr></thead>')
    body = "".join(f'<tr><th scope="row">{t(a)}</th><td>{t(b)}</td><td>{t(c)}</td></tr>' for a, b, c in rows)
    return f'<div class="cmp-wrap"><table class="cmp two">{head}<tbody>{body}</tbody></table></div>'

def _pick(t, h, items):
    return f'<div><h3>{t(h)}</h3>{ul(t, items)}</div>'

# ---------------------------------------------------------------- Sweep's side, the same on every comparison
L = {"free": T("Free plan","Forfait gratuit","Plan gratis"), "trial": T("Trial of a paid plan","Essai d’un forfait payant","Prueba de un plan de pago"),
     "month": T("Monthly price","Prix mensuel","Precio mensual"), "year": T("Yearly price","Prix annuel","Precio anual"),
     "add": T("Adding trades","Ajouter des trades","Añadir operaciones"), "sync": T("Automatic broker sync","Synchro automatique avec le courtier","Sincronización automática con el bróker"),
     "rules": T("Prop firm rules","Règles des prop firms","Reglas de las prop firms"), "money": T("Expense and payout tracking","Suivi des dépenses et des payouts","Seguimiento de gastos y payouts"),
     "replay": T("Trade replay","Replay de trades","Replay de operaciones"), "mreplay": T("Market replay","Replay de marché","Replay de mercado"),
     "backtest": T("Backtesting","Backtesting","Backtesting"), "strategy": T("Strategy testing","Test de stratégies","Prueba de estrategias"),
     "charts": T("Charts of your trades","Graphiques de tes trades","Gráficos de tus operaciones"), "mentor": T("Mentoring","Mentorat","Mentoría"),
     "ai": T("AI assistant","Assistant IA","Asistente de IA"), "mobile": T("On your phone","Sur ton téléphone","En tu teléfono"),
     "psych": T("Psychology and discipline","Psychologie et discipline","Psicología y disciplina"), "markets": T("Markets","Marchés","Mercados")}
SW = {"free": T("Yes, no time limit, no card","Oui, sans limite de temps, sans carte","Sí, sin límite de tiempo, sin tarjeta"), "trial": T("60 days of Pro","60 jours de Pro","60 días de Pro"),
      "month": T("Pro $19 · Elite $39","Pro 19 $ · Elite 39 $","Pro 19 $ · Elite 39 $"),
      "year": T("Pro $159 · Elite $329","Pro 159 $ · Elite 329 $","Pro 159 $ · Elite 329 $"),
      "add": T("File import, screenshot read by AI, or by hand","Import de fichier, capture lue par l’IA, ou à la main","Importación de archivo, captura leída por la IA o a mano"),
      "sync": T("In development","En développement","En desarrollo"),
      "rules": T("Preloaded for 5 futures firms, per account type, checked every week","Préremplies pour 5 firmes de futures, par type de compte, vérifiées chaque semaine","Precargadas para 5 firmas de futuros, por tipo de cuenta, revisadas cada semana"),
      "money": T("Pro and Elite","Pro et Elite","Pro y Elite"), "no": T("No","Non","No"),
      "charts": T("Real CME charts, the day after the session","Vrais graphiques CME, le lendemain de la séance","Gráficos reales de CME, al día siguiente de la sesión"),
      "ai": T("Sweep AI on every plan","Sweep AI sur tous les forfaits","Sweep AI en todos los planes"),
      "mobile": T("In the browser, add it to your home screen","Dans le navigateur, à ajouter à ton écran d’accueil","En el navegador, añádelo a tu pantalla de inicio"),
      "psych": T("Daily routine: plan, rules, review","Routine quotidienne : plan, règles, revue","Rutina diaria: plan, reglas, revisión"),
      "markets": T("Futures","Futures","Futuros")}
def row(k, them, sweep=None): return (L[k], sweep or SW.get(k, SW["no"]), them)
NONE_LISTED = T("None listed on its pricing page","Rien sur sa page de tarifs","Nada en su página de precios")

SWEEP_IF = [
 T("You trade futures evaluations and funded accounts, and want each firm’s rules on every account.","Tu trades des évaluations et des comptes financés en futures, et tu veux les règles de chaque firme sur chaque compte.","Operas evaluaciones y cuentas fondeadas de futuros y quieres las reglas de cada firma en cada cuenta."),
 T("You want a free plan with no time limit, or Pro for $19 a month.","Tu veux un forfait gratuit sans limite de temps, ou Pro à 19 $ par mois.","Quieres un plan gratis sin límite de tiempo, o Pro por 19 $ al mes."),
 T("You want a daily routine that rewards following your plan, not just your P&L.","Tu veux une routine quotidienne qui récompense le respect de ton plan, pas seulement ton P&L.","Quieres una rutina diaria que premie seguir tu plan, no solo tu P&L."),
 T("You journal in English, French or Spanish.","Tu tiens ton journal en anglais, en français ou en espagnol.","Llevas tu diario en inglés, francés o español.")]
SWEEP_DIFF = [
 T("Sweep starts from your prop accounts. Pick your firm and account type, and the drawdown, consistency and payout conditions are already there. They’re checked against each firm’s official pages every week; when a firm changes a rule, you’re notified and choose whether to apply it.",
   "Sweep part de tes comptes prop. Choisis ta firme et ton type de compte : le drawdown, la consistance et les conditions de payout sont déjà là. Elles sont vérifiées chaque semaine sur les pages officielles de chaque firme ; quand une firme change une règle, tu es averti et tu choisis de l’appliquer ou non.",
   "Sweep parte de tus cuentas prop. Elige tu firma y tu tipo de cuenta: el drawdown, la consistencia y las condiciones de payout ya están ahí. Se revisan cada semana en las páginas oficiales de cada firma; cuando una firma cambia una regla, recibes un aviso y eliges si aplicarla."),
 T("Your money stays in separate layers: evaluations, funded and live accounts are never mixed, and copy trading counts once in your statistics, not once per account.",
   "Ton argent reste en couches séparées : évaluations, comptes financés et live ne sont jamais mélangés, et le copy trading compte une seule fois dans tes statistiques, pas une fois par compte.",
   "Tu dinero se mantiene en capas separadas: evaluaciones, cuentas fondeadas y live nunca se mezclan, y el copy trading cuenta una sola vez en tus estadísticas, no una vez por cuenta."),
 T("Each session has a routine: a plan before the open, your rules during it, and a short review after the close. Sweep measures those habits, so a red day where you followed your plan still counts.",
   "Chaque séance a sa routine : un plan avant l’ouverture, tes règles pendant, et une courte revue après la clôture. Sweep mesure ces habitudes : une journée dans le rouge où tu as suivi ton plan compte quand même.",
   "Cada sesión tiene su rutina: un plan antes de la apertura, tus reglas durante y una breve revisión tras el cierre. Sweep mide esos hábitos, así que un día en rojo en el que seguiste tu plan también cuenta.")]
SYNC_NOTE = T("At Sweep, automatic sync with Rithmic and Tradovate is in development; we’ll announce it on our changelog as soon as it’s live.",
              "Chez Sweep, la synchronisation automatique avec Rithmic et Tradovate est en développement ; on l’annoncera dans les nouveautés dès qu’elle sera disponible.",
              "En Sweep, la sincronización automática con Rithmic y Tradovate está en desarrollo; la anunciaremos en las novedades en cuanto esté disponible.")
FAQ_ADD = (T("How do I add trades to Sweep?","Comment ajouter des trades dans Sweep ?","¿Cómo añado operaciones en Sweep?"),
  T("Import your platform’s export (Tradovate, Rithmic, ProjectX or TradingView), paste a screenshot that Sweep AI reads, or type the trade by hand. Automatic sync with Rithmic and Tradovate is in development.",
    "Importe l’export de ta plateforme (Tradovate, Rithmic, ProjectX ou TradingView), colle une capture que Sweep AI lit, ou saisis le trade à la main. La synchronisation automatique avec Rithmic et Tradovate est en développement.",
    "Importa la exportación de tu plataforma (Tradovate, Rithmic, ProjectX o TradingView), pega una captura que Sweep AI lee o escribe la operación a mano. La sincronización automática con Rithmic y Tradovate está en desarrollo."))
def _free_alt(name, them_en, them_fr, them_es):
    return (T(f"Is there a free alternative to {name}?", f"Existe-t-il une alternative gratuite à {name} ?", f"¿Hay una alternativa gratis a {name}?"),
            T("Yes. Sweep has a Free plan with no time limit and no credit card, and every new account gets 60 days of Pro. " + them_en,
              "Oui. Sweep a un forfait Free sans limite de temps et sans carte de crédit, et chaque nouveau compte reçoit 60 jours de Pro. " + them_fr,
              "Sí. Sweep tiene un plan Free sin límite de tiempo y sin tarjeta, y cada cuenta nueva recibe 60 días de Pro. " + them_es))
def _cheaper(them_en, them_fr, them_es, first=T("Sweep. ","Sweep. ","Sweep. ")):
    return (T("Which one is cheaper?","Lequel coûte le moins cher ?","¿Cuál es más barato?"),
            T(first["en"] + "Pro is $19 a month or $159 a year, and Elite is $39 a month or $329 a year. " + them_en + " Prices in USD, before tax.",
              first["fr"] + "Pro coûte 19 $ par mois ou 159 $ par année, et Elite 39 $ par mois ou 329 $ par année. " + them_fr + " Prix en USD, avant taxes.",
              first["es"] + "Pro cuesta 19 $ al mes o 159 $ al año, y Elite 39 $ al mes o 329 $ al año. " + them_es + " Precios en USD, antes de impuestos."))

# ---------------------------------------------------------------- one entry per competitor
VS = [
 {"slug": "sweep-vs-tradezella.html", "name": "TradeZella",
  "sources": T("its public pricing and Prop Firm Sync pages", "ses pages publiques de tarifs et de Prop Firm Sync", "sus páginas públicas de precios y de Prop Firm Sync"),
  "them_if": [T("You want trades to sync from your broker automatically, today.","Tu veux que tes trades arrivent automatiquement de ton courtier, dès aujourd’hui.","Quieres que tus operaciones lleguen solas desde tu bróker, ya hoy."),
              T("You use trade replay or backtesting.","Tu utilises le replay de trades ou le backtesting.","Usas el replay de operaciones o el backtesting."),
              T("You also trade stocks, forex or crypto.","Tu trades aussi des actions, du forex ou des cryptos.","También operas acciones, forex o cripto."),
              T("You work with a mentor who reviews your journal.","Tu travailles avec un mentor qui consulte ton journal.","Trabajas con un mentor que revisa tu diario.")],
  "rows": [row("free", T("None on its pricing page","Aucun sur sa page de tarifs","Ninguno en su página de precios")),
           row("trial", T("None on its pricing page","Aucun sur sa page de tarifs","Ninguno en su página de precios")),
           row("month", T("Essential $35 · Pro $59 · Ultra $99","Essential 35 $ · Pro 59 $ · Ultra 99 $","Essential 35 $ · Pro 59 $ · Ultra 99 $")),
           row("year", T("Essential $315 · Pro $531 · Ultra $891","Essential 315 $ · Pro 531 $ · Ultra 891 $","Essential 315 $ · Pro 531 $ · Ultra 891 $")),
           row("add", T("Auto-sync, file upload or by hand","Synchro automatique, import de fichier ou à la main","Sincronización automática, subida de archivo o a mano")),
           row("sync", T("Yes","Oui","Sí")),
           row("rules", T("Prop Firm Sync: drawdown, daily loss, target, trading days, consistency","Prop Firm Sync : drawdown, perte quotidienne, cible, jours de trading, consistance","Prop Firm Sync: drawdown, pérdida diaria, objetivo, días de trading, consistencia")),
           row("money", T("Every plan","Tous les forfaits","Todos los planes")),
           row("replay", T("Pro and Ultra","Pro et Ultra","Pro y Ultra")),
           row("backtest", T("Every plan (AI runs on Pro and Ultra)","Tous les forfaits (exécutions IA sur Pro et Ultra)","Todos los planes (ejecuciones con IA en Pro y Ultra)")),
           row("markets", T("Futures, stocks, forex, crypto","Futures, actions, forex, cryptos","Futuros, acciones, forex, cripto"))],
  "ahead": T("TradeZella is a larger, all-round journal. It syncs trades automatically from many brokers, replays your trades second by second, and includes backtesting on historical data. It covers stocks, forex and crypto as well as futures, and offers a mentor mode. If you rely on any of these today, it’s the better fit.",
             "TradeZella est un journal plus vaste et plus généraliste. Il synchronise automatiquement les trades de nombreux courtiers, rejoue tes trades seconde par seconde et inclut du backtesting sur données historiques. Il couvre aussi les actions, le forex et les cryptos, et offre un mode mentor. Si tu comptes sur l’une de ces fonctions aujourd’hui, c’est le meilleur choix.",
             "TradeZella es un diario más amplio y generalista. Sincroniza automáticamente las operaciones de muchos brókers, reproduce tus operaciones segundo a segundo e incluye backtesting con datos históricos. También cubre acciones, forex y cripto, y ofrece un modo mentor. Si hoy dependes de alguna de estas funciones, es la mejor opción."),
  "faq": [_free_alt("TradeZella", "TradeZella shows no free plan on its pricing page; its plans start at $35 a month, or $26 a month billed yearly.", "TradeZella n’affiche aucun forfait gratuit sur sa page de tarifs ; ses forfaits commencent à 35 $ par mois, ou 26 $ par mois en facturation annuelle.", "TradeZella no muestra ningún plan gratis en su página de precios; sus planes empiezan en 35 $ al mes, o 26 $ al mes con facturación anual."),
          _cheaper("TradeZella’s plans are $35, $59 and $99 a month, or $315, $531 and $891 a year.", "Les forfaits de TradeZella coûtent 35 $, 59 $ et 99 $ par mois, ou 315 $, 531 $ et 891 $ par année.", "Los planes de TradeZella cuestan 35 $, 59 $ y 99 $ al mes, o 315 $, 531 $ y 891 $ al año."),
          (T("Does TradeZella track prop firm rules?","TradeZella suit-il les règles des prop firms ?","¿TradeZella sigue las reglas de las prop firms?"),
           T("Yes. Its Prop Firm Sync dashboard, free for TradeZella users, tracks drawdown, daily loss limits, profit targets, trading days and consistency, along with expenses and payouts. In Sweep, rules come preloaded for 5 futures prop firms (Apex, Topstep, Lucid, Take Profit Trader and MyFundedFutures) and each account type, and are checked against the firms’ official pages every week.",
             "Oui. Son tableau de bord Prop Firm Sync, gratuit pour les utilisateurs de TradeZella, suit le drawdown, les limites de perte quotidienne, les cibles de profit, les jours de trading et la consistance, ainsi que les dépenses et les payouts. Dans Sweep, les règles sont préremplies pour 5 prop firms de futures (Apex, Topstep, Lucid, Take Profit Trader et MyFundedFutures) et chaque type de compte, et vérifiées chaque semaine sur les pages officielles des firmes.",
             "Sí. Su panel Prop Firm Sync, gratis para los usuarios de TradeZella, sigue el drawdown, los límites de pérdida diaria, los objetivos de ganancia, los días de trading y la consistencia, además de los gastos y los payouts. En Sweep, las reglas vienen precargadas para 5 prop firms de futuros (Apex, Topstep, Lucid, Take Profit Trader y MyFundedFutures) y cada tipo de cuenta, y se revisan cada semana en las páginas oficiales de las firmas.")),
          FAQ_ADD,
          (T("Does Sweep have trade replay or backtesting?","Sweep offre-t-il le replay de trades ou le backtesting ?","¿Sweep tiene replay de operaciones o backtesting?"),
           T("No. Sweep focuses on journaling, prop firm rules and your daily routine. If replay or backtesting is part of how you work, TradeZella is the better fit today.",
             "Non. Sweep se concentre sur le journal, les règles des prop firms et ta routine quotidienne. Si le replay ou le backtesting fait partie de ta façon de travailler, TradeZella te conviendra mieux aujourd’hui.",
             "No. Sweep se centra en el diario, las reglas de las prop firms y tu rutina diaria. Si el replay o el backtesting forman parte de tu forma de trabajar, hoy TradeZella te encajará mejor."))],
  "desc": T("Sweep vs TradeZella for futures prop firm traders: free plan, prices, trade import, firm rules, replay and backtesting, compared side by side.",
            "Sweep vs TradeZella pour les traders de prop firms en futures : forfait gratuit, prix, import, règles des firmes, replay et backtesting, côte à côte.",
            "Sweep vs TradeZella para traders de prop firms de futuros: plan gratis, precios, importación, reglas de las firmas, replay y backtesting, lado a lado.")},

 {"slug": "sweep-vs-tradervue.html", "name": "Tradervue",
  "sources": T("its public pricing page and help center", "sa page publique de tarifs et son centre d’aide", "su página pública de precios y su centro de ayuda"),
  "them_if": [T("You mostly trade stocks or options.","Tu trades surtout des actions ou des options.","Operas sobre todo acciones u opciones."),
              T("You want deep reports: MFE and MAE, exit analysis, liquidity.","Tu veux des rapports poussés : MFE et MAE, analyse des sorties, liquidité.","Quieres informes a fondo: MFE y MAE, análisis de salidas, liquidez."),
              T("You want trades to sync from your broker automatically, today.","Tu veux que tes trades arrivent automatiquement de ton courtier, dès aujourd’hui.","Quieres que tus operaciones lleguen solas desde tu bróker, ya hoy."),
              T("You work with a mentor who reviews your trades.","Tu travailles avec un mentor qui consulte tes trades.","Trabajas con un mentor que revisa tus operaciones.")],
  "rows": [row("free", T("Yes, 30 trades a month","Oui, 30 trades par mois","Sí, 30 operaciones al mes")),
           row("trial", T("Yes, on Silver and Gold","Oui, sur Silver et Gold","Sí, en Silver y Gold")),
           row("month", T("Silver $29.95 · Gold $49.95","Silver 29,95 $ · Gold 49,95 $","Silver 29,95 $ · Gold 49,95 $")),
           row("year", T("Not listed on its pricing page","Pas indiqué sur sa page de tarifs","No figura en su página de precios")),
           row("add", T("Broker imports","Imports depuis le courtier","Importación desde el bróker")),
           row("sync", T("Silver and Gold","Silver et Gold","Silver y Gold")),
           row("rules", NONE_LISTED),
           row("money", NONE_LISTED),
           row("charts", T("Price charts with your entries and exits","Graphiques de prix avec tes entrées et sorties","Gráficos de precio con tus entradas y salidas")),
           row("mentor", T("Silver and Gold","Silver et Gold","Silver y Gold")),
           row("markets", T("Stocks, options, futures, forex","Actions, options, futures, forex","Acciones, opciones, futuros, forex"))],
  "ahead": T("Tradervue focuses on detailed reporting: MFE and MAE statistics, exit analysis, liquidity and risk reports, with mentoring and trade sharing. It covers stocks, options and forex as well as futures, syncs with brokers on its paid plans, and has a free plan for up to 30 trades a month. If you mostly trade stocks or want deep reports, it’s the better fit.",
             "Tradervue mise sur des rapports détaillés : statistiques MFE et MAE, analyse des sorties, rapports de liquidité et de risque, avec mentorat et partage de trades. Il couvre les actions, les options et le forex en plus des futures, se synchronise avec les courtiers sur ses forfaits payants, et a un forfait gratuit jusqu’à 30 trades par mois. Si tu trades surtout des actions ou veux des rapports poussés, c’est le meilleur choix.",
             "Tradervue se centra en informes detallados: estadísticas MFE y MAE, análisis de salidas, informes de liquidez y de riesgo, con mentoría y operaciones compartidas. Cubre acciones, opciones y forex además de futuros, se sincroniza con brókers en sus planes de pago y tiene un plan gratis de hasta 30 operaciones al mes. Si operas sobre todo acciones o quieres informes a fondo, es la mejor opción."),
  "faq": [(T("Is Tradervue free?","Tradervue est-il gratuit ?","¿Tradervue es gratis?"),
           T("Tradervue has a free plan limited to 30 trades a month; Silver ($29.95 a month) and Gold ($49.95 a month) remove that limit. Sweep’s Free plan has no time limit and no credit card, and every new account gets 60 days of Pro.",
             "Tradervue a un forfait gratuit limité à 30 trades par mois ; Silver (29,95 $ par mois) et Gold (49,95 $ par mois) lèvent cette limite. Le forfait Free de Sweep n’a pas de limite de temps ni de carte de crédit, et chaque nouveau compte reçoit 60 jours de Pro.",
             "Tradervue tiene un plan gratis limitado a 30 operaciones al mes; Silver (29,95 $ al mes) y Gold (49,95 $ al mes) quitan ese límite. El plan Free de Sweep no tiene límite de tiempo ni tarjeta, y cada cuenta nueva recibe 60 días de Pro.")),
          _cheaper("Tradervue’s paid plans are $29.95 (Silver) and $49.95 (Gold) a month; its pricing page lists no yearly price.", "Les forfaits payants de Tradervue coûtent 29,95 $ (Silver) et 49,95 $ (Gold) par mois ; sa page de tarifs n’affiche pas de prix annuel.", "Los planes de pago de Tradervue cuestan 29,95 $ (Silver) y 49,95 $ (Gold) al mes; su página de precios no muestra precio anual.",
                   first=T("Among paid plans, Sweep. ","Parmi les forfaits payants, Sweep. ","Entre los planes de pago, Sweep. ")),
          (T("Does Tradervue track prop firm rules?","Tradervue suit-il les règles des prop firms ?","¿Tradervue sigue las reglas de las prop firms?"),
           T("Its pricing page lists no prop firm features: no drawdown, consistency or payout rules. In Sweep, rules come preloaded for 5 futures prop firms (Apex, Topstep, Lucid, Take Profit Trader and MyFundedFutures) and each account type, and are checked against the firms’ official pages every week.",
             "Sa page de tarifs n’affiche aucune fonction pour les prop firms : ni drawdown, ni consistance, ni règles de payout. Dans Sweep, les règles sont préremplies pour 5 prop firms de futures (Apex, Topstep, Lucid, Take Profit Trader et MyFundedFutures) et chaque type de compte, et vérifiées chaque semaine sur les pages officielles des firmes.",
             "Su página de precios no muestra funciones para prop firms: ni drawdown, ni consistencia, ni reglas de payout. En Sweep, las reglas vienen precargadas para 5 prop firms de futuros (Apex, Topstep, Lucid, Take Profit Trader y MyFundedFutures) y cada tipo de cuenta, y se revisan cada semana en las páginas oficiales de las firmas.")),
          FAQ_ADD,
          (T("Is Tradervue better for stock traders?","Tradervue est-il meilleur pour les traders d’actions ?","¿Tradervue es mejor para traders de acciones?"),
           T("Often, yes. Tradervue covers stocks, options, futures and forex with detailed reports. Sweep is built for futures only, and for prop firm accounts first.",
             "Souvent, oui. Tradervue couvre les actions, les options, les futures et le forex avec des rapports détaillés. Sweep est conçu pour les futures seulement, et d’abord pour les comptes de prop firms.",
             "A menudo, sí. Tradervue cubre acciones, opciones, futuros y forex con informes detallados. Sweep está hecho solo para futuros, y primero para cuentas de prop firms."))],
  "desc": T("Sweep vs Tradervue for futures prop firm traders: free plans, prices, broker sync, prop firm rules, reports and markets, compared side by side.",
            "Sweep vs Tradervue pour les traders de prop firms en futures : forfaits gratuits, prix, synchro, règles des firmes, rapports et marchés, côte à côte.",
            "Sweep vs Tradervue para traders de prop firms de futuros: planes gratis, precios, sincronización, reglas de las firmas, informes y mercados, lado a lado.")},

 {"slug": "sweep-vs-tradersync.html", "name": "TraderSync",
  "sources": T("its public pricing page", "sa page publique de tarifs", "su página pública de precios"),
  "them_if": [T("You want automatic broker sync and a native mobile app today.","Tu veux une synchro automatique avec ton courtier et une app mobile native dès aujourd’hui.","Quieres sincronización automática con tu bróker y una app móvil nativa ya hoy."),
              T("You use trade replay, market replay or backtesting.","Tu utilises le replay de trades, le replay de marché ou le backtesting.","Usas el replay de operaciones, el replay de mercado o el backtesting."),
              T("You want an AI coach on your trades.","Tu veux un coach IA sur tes trades.","Quieres un coach de IA sobre tus operaciones."),
              T("You also trade stocks, forex, crypto or options.","Tu trades aussi des actions, du forex, des cryptos ou des options.","También operas acciones, forex, cripto u opciones.")],
  "rows": [row("free", T("None on its pricing page","Aucun sur sa page de tarifs","Ninguno en su página de precios")),
           row("trial", T("7 days, every plan","7 jours, tous les forfaits","7 días, todos los planes")),
           row("month", T("Pro $29.95 · Premium $49.95 · Elite $79.95","Pro 29,95 $ · Premium 49,95 $ · Elite 79,95 $","Pro 29,95 $ · Premium 49,95 $ · Elite 79,95 $")),
           row("year", T("Pro $269.52 · Premium $449.52 · Elite $719.52","Pro 269,52 $ · Premium 449,52 $ · Elite 719,52 $","Pro 269,52 $ · Premium 449,52 $ · Elite 719,52 $")),
           row("add", T("Auto-sync or imports, 700+ brokers and platforms","Synchro automatique ou imports, 700+ courtiers et plateformes","Sincronización automática o importación, más de 700 brókers y plataformas")),
           row("sync", T("Every plan","Tous les forfaits","Todos los planes")),
           row("rules", NONE_LISTED),
           row("replay", T("Premium and Elite","Premium et Elite","Premium y Elite")),
           row("mreplay", T("Every plan","Tous les forfaits","Todos los planes")),
           row("backtest", T("Automated, on Elite","Automatisé, sur Elite","Automatizado, en Elite")),
           row("ai", T("Cypher, 5 to 60 messages a day","Cypher, 5 à 60 messages par jour","Cypher, de 5 a 60 mensajes al día"), SW["ai"]),
           row("mobile", T("Mobile app, every plan","App mobile, tous les forfaits","App móvil, todos los planes"), SW["mobile"]),
           row("markets", T("Stocks, futures, forex, crypto; options on Elite","Actions, futures, forex, cryptos ; options sur Elite","Acciones, futuros, forex, cripto; opciones en Elite"))],
  "ahead": T("TraderSync is a broad journal with a market simulator built in. It syncs with more than 700 brokers and platforms, has a mobile app, replays your trades (Premium and Elite) and whole sessions (every plan), and adds automated backtesting and an AI coach on Elite. It covers stocks, forex and crypto as well as futures. If you rely on any of these today, it’s the better fit.",
             "TraderSync est un journal vaste avec un simulateur de marché intégré. Il se synchronise avec plus de 700 courtiers et plateformes, a une app mobile, rejoue tes trades (Premium et Elite) et des séances entières (tous les forfaits), et ajoute du backtesting automatisé et un coach IA sur Elite. Il couvre aussi les actions, le forex et les cryptos. Si tu comptes sur l’une de ces fonctions aujourd’hui, c’est le meilleur choix.",
             "TraderSync es un diario amplio con un simulador de mercado integrado. Se sincroniza con más de 700 brókers y plataformas, tiene app móvil, reproduce tus operaciones (Premium y Elite) y sesiones enteras (todos los planes), y añade backtesting automatizado y un coach de IA en Elite. También cubre acciones, forex y cripto. Si hoy dependes de alguna de estas funciones, es la mejor opción."),
  "faq": [_free_alt("TraderSync", "TraderSync offers a 7-day free trial; its plans start at $29.95 a month, or $22.46 a month billed yearly.", "TraderSync offre un essai gratuit de 7 jours ; ses forfaits commencent à 29,95 $ par mois, ou 22,46 $ par mois en facturation annuelle.", "TraderSync ofrece una prueba gratis de 7 días; sus planes empiezan en 29,95 $ al mes, o 22,46 $ al mes con facturación anual."),
          _cheaper("TraderSync’s plans are $29.95, $49.95 and $79.95 a month, or $269.52, $449.52 and $719.52 a year.", "Les forfaits de TraderSync coûtent 29,95 $, 49,95 $ et 79,95 $ par mois, ou 269,52 $, 449,52 $ et 719,52 $ par année.", "Los planes de TraderSync cuestan 29,95 $, 49,95 $ y 79,95 $ al mes, o 269,52 $, 449,52 $ y 719,52 $ al año."),
          (T("Does TraderSync have trade replay?","TraderSync a-t-il le replay de trades ?","¿TraderSync tiene replay de operaciones?"),
           T("Yes, on Premium and Elite; every plan also has market replay. Sweep has neither: it focuses on journaling, prop firm rules and your daily routine.",
             "Oui, sur Premium et Elite ; tous les forfaits ont aussi le replay de marché. Sweep n’a ni l’un ni l’autre : il se concentre sur le journal, les règles des prop firms et ta routine quotidienne.",
             "Sí, en Premium y Elite; todos los planes tienen además replay de mercado. Sweep no tiene ninguno de los dos: se centra en el diario, las reglas de las prop firms y tu rutina diaria.")),
          FAQ_ADD,
          (T("Does TraderSync have a mobile app?","TraderSync a-t-il une app mobile ?","¿TraderSync tiene app móvil?"),
           T("Yes, on every plan. Sweep is designed mobile-first and works in your phone’s browser; you can add it to your home screen. Native iOS and Android apps are on the roadmap.",
             "Oui, sur tous les forfaits. Sweep est conçu d’abord pour le mobile et fonctionne dans le navigateur de ton téléphone ; tu peux l’ajouter à ton écran d’accueil. Des apps iOS et Android natives sont prévues.",
             "Sí, en todos los planes. Sweep está pensado primero para el móvil y funciona en el navegador de tu teléfono; puedes añadirlo a tu pantalla de inicio. Las apps nativas para iOS y Android están previstas."))],
  "desc": T("Sweep vs TraderSync for futures prop firm traders: prices, free plan and trial, broker sync, prop firm rules, replay, AI and mobile, side by side.",
            "Sweep vs TraderSync pour les traders de prop firms en futures : prix, forfait gratuit et essai, synchro, règles des firmes, replay, IA et mobile.",
            "Sweep vs TraderSync para traders de prop firms de futuros: precios, plan gratis y prueba, sincronización, reglas de las firmas, replay, IA y móvil.")},

 {"slug": "sweep-vs-edgewonk.html", "name": "Edgewonk",
  "sources": T("its public pricing and home pages", "ses pages publiques de tarifs et d’accueil", "sus páginas públicas de precios y de inicio"),
  "them_if": [T("You want one yearly price with every feature included.","Tu veux un seul prix annuel avec toutes les fonctions incluses.","Quieres un solo precio anual con todas las funciones incluidas."),
              T("You focus on psychology: tilt, mistakes and missed trades.","Tu mises sur la psychologie : tilt, erreurs et trades manqués.","Te centras en la psicología: tilt, errores y operaciones perdidas."),
              T("You also trade forex, stocks or crypto.","Tu trades aussi du forex, des actions ou des cryptos.","También operas forex, acciones o cripto."),
              T("You want automatic imports from your platform today.","Tu veux des imports automatiques depuis ta plateforme dès aujourd’hui.","Quieres importaciones automáticas desde tu plataforma ya hoy.")],
  "rows": [row("free", T("None on its pricing page","Aucun sur sa page de tarifs","Ninguno en su página de precios")),
           row("trial", T("No; 14-day money-back guarantee","Non ; satisfait ou remboursé 14 jours","No; garantía de reembolso de 14 días")),
           row("month", T("No monthly plan","Pas de forfait mensuel","Sin plan mensual")),
           row("year", T("$197 (one plan)","197 $ (un seul forfait)","197 $ (un solo plan)")),
           row("add", T("Automated imports, 200+ brokers","Imports automatiques, 200+ courtiers","Importación automática, más de 200 brókers")),
           row("sync", T("Automated imports","Imports automatiques","Importación automática")),
           row("rules", T("Tracks unlimited prop firm accounts; no rules listed","Suit un nombre illimité de comptes prop ; aucune règle indiquée","Sigue cuentas prop ilimitadas; sin reglas indicadas")),
           row("money", NONE_LISTED),
           row("psych", T("Tiltmeter and a weekly edge finder","Tiltmeter et un edge finder chaque semaine","Tiltmeter y un edge finder semanal"), SW["psych"]),
           row("strategy", T("Strategy testing and performance simulator","Test de stratégies et simulateur de performance","Prueba de estrategias y simulador de rendimiento")),
           row("markets", T("Forex, stocks, futures, crypto, indices, commodities, options","Forex, actions, futures, cryptos, indices, matières premières, options","Forex, acciones, futuros, cripto, índices, materias primas, opciones"))],
  "ahead": T("Edgewonk focuses on finding your edge and fixing your mistakes: a Tiltmeter that shows how often you break your rules, an automatic edge finder every Sunday, missed-trade tracking, strategy testing and a performance simulator. It imports trades automatically from more than 200 brokers, covers forex, stocks and crypto as well as futures, and costs one yearly price. If that’s how you work, it’s the better fit.",
             "Edgewonk mise sur la recherche de ton edge et la correction de tes erreurs : un Tiltmeter qui montre à quelle fréquence tu enfreins tes règles, un edge finder automatique chaque dimanche, le suivi des trades manqués, le test de stratégies et un simulateur de performance. Il importe les trades automatiquement depuis plus de 200 courtiers, couvre aussi le forex, les actions et les cryptos, et coûte un seul prix annuel. Si c’est ta façon de travailler, c’est le meilleur choix.",
             "Edgewonk se centra en encontrar tu ventaja y corregir tus errores: un Tiltmeter que muestra con qué frecuencia rompes tus reglas, un edge finder automático cada domingo, seguimiento de operaciones perdidas, prueba de estrategias y un simulador de rendimiento. Importa operaciones automáticamente desde más de 200 brókers, cubre también forex, acciones y cripto, y cuesta un solo precio anual. Si es tu forma de trabajar, es la mejor opción."),
  "faq": [_free_alt("Edgewonk", "Edgewonk has no free plan or trial: it costs $197 a year, with a 14-day money-back guarantee.", "Edgewonk n’a ni forfait gratuit ni essai : il coûte 197 $ par année, avec une garantie satisfait ou remboursé de 14 jours.", "Edgewonk no tiene plan gratis ni prueba: cuesta 197 $ al año, con una garantía de reembolso de 14 días."),
          _cheaper("Edgewonk has one plan at $197 a year, with no monthly option.", "Edgewonk a un seul forfait à 197 $ par année, sans option mensuelle.", "Edgewonk tiene un solo plan de 197 $ al año, sin opción mensual."),
          (T("Does Edgewonk track prop firm accounts?","Edgewonk suit-il les comptes de prop firms ?","¿Edgewonk sigue las cuentas de prop firms?"),
           T("Yes: it tracks unlimited prop firm accounts. Its pricing page doesn’t list prop firm rules. In Sweep, rules come preloaded for 5 futures prop firms (Apex, Topstep, Lucid, Take Profit Trader and MyFundedFutures) and each account type, and are checked against the firms’ official pages every week.",
             "Oui : il suit un nombre illimité de comptes de prop firms. Sa page de tarifs n’indique pas de règles de prop firms. Dans Sweep, les règles sont préremplies pour 5 prop firms de futures (Apex, Topstep, Lucid, Take Profit Trader et MyFundedFutures) et chaque type de compte, et vérifiées chaque semaine sur les pages officielles des firmes.",
             "Sí: sigue cuentas de prop firms ilimitadas. Su página de precios no indica reglas de prop firms. En Sweep, las reglas vienen precargadas para 5 prop firms de futuros (Apex, Topstep, Lucid, Take Profit Trader y MyFundedFutures) y cada tipo de cuenta, y se revisan cada semana en las páginas oficiales de las firmas.")),
          FAQ_ADD,
          (T("Is Edgewonk better for trading psychology?","Edgewonk est-il meilleur pour la psychologie du trading ?","¿Edgewonk es mejor para la psicología del trading?"),
           T("It goes deep on it: a Tiltmeter, mistake tracking and a weekly edge finder. Sweep works on discipline through a daily routine (plan, rules, review) and rewards following your plan, not just your P&L.",
             "Il va loin sur ce terrain : Tiltmeter, suivi des erreurs et edge finder chaque semaine. Sweep travaille la discipline par une routine quotidienne (plan, règles, revue) et récompense le respect de ton plan, pas seulement ton P&L.",
             "Profundiza mucho en ello: Tiltmeter, seguimiento de errores y un edge finder semanal. Sweep trabaja la disciplina con una rutina diaria (plan, reglas, revisión) y premia seguir tu plan, no solo tu P&L."))],
  "desc": T("Sweep vs Edgewonk for futures prop firm traders: free plan, yearly price, imports, prop firm rules, psychology tools and markets, side by side.",
            "Sweep vs Edgewonk pour les traders de prop firms en futures : forfait gratuit, prix annuel, imports, règles des firmes, psychologie et marchés.",
            "Sweep vs Edgewonk para traders de prop firms de futuros: plan gratis, precio anual, importación, reglas de las firmas, psicología y mercados.")},
]

def _fr_nbsp(lang, title, desc, body, ld):
    """French: no « : », « ; » or « ? » alone at the start of a line."""
    if lang == "fr":
        title, desc, body = (re.sub(r" ([:;?!])(?=\s|<|$)", "\u00a0\\1", x) for x in (title, desc, body))
    return (title, desc, body, ld)

def make_vs(c):
    name = c["name"]
    def page(lang, t):
        hero = page_hero(t, T(f"Sweep vs {name}.", f"Sweep vs {name}.", f"Sweep vs {name}."),
            T(f"Two trading journals built for different traders. What each one does, what it costs, and when {name} is the better pick.",
              f"Deux journaux de trading pensés pour des traders différents. Ce que fait chacun, ce qu’il coûte, et quand {name} est le meilleur choix.",
              f"Dos diarios de trading pensados para traders distintos. Qué hace cada uno, cuánto cuesta y cuándo {name} es la mejor opción."),
            T("Compare","Comparer","Comparar"))
        picks = _pick(t, T("Choose Sweep if","Choisis Sweep si","Elige Sweep si"), SWEEP_IF) + _pick(t, T(f"Choose {name} if", f"Choisis {name} si", f"Elige {name} si"), c["them_if"])
        S = c["sources"]
        note = T(f"{name} details come from {S['en']}, checked on {CHECKED['en']}. Prices in USD, before tax. Something out of date? Write to {EMAIL}. {name} is a trademark of its owner; Sweep is not affiliated with {name}.",
                 f"Les infos sur {name} viennent de {S['fr']}, vérifiées le {CHECKED['fr']}. Prix en USD, avant taxes. Une info n’est plus à jour ? Écris à {EMAIL}. {name} est une marque de son propriétaire ; Sweep n’est pas affilié à {name}.",
                 f"La información de {name} proviene de {S['es']}, revisadas el {CHECKED['es']}. Precios en USD, antes de impuestos. ¿Algo ya no está al día? Escribe a {EMAIL}. {name} es una marca de su propietario; Sweep no está afiliado a {name}.")
        diff = [(T("Where Sweep is different","Ce qui distingue Sweep","Lo que distingue a Sweep"), SWEEP_DIFF),
                (T(f"Where {name} is ahead", f"Là où {name} est en avance", f"Donde {name} va por delante"), [c["ahead"], SYNC_NOTE])]
        article = "".join(f'<h2>{t(h)}</h2>' + "".join(f"<p>{t(p)}</p>" for p in ps) for h, ps in diff)
        faq = "".join(faq_item(t, q, a) for q, a in c["faq"])
        others = [(o["slug"], T(f"Sweep vs {o['name']}", f"Sweep vs {o['name']}", f"Sweep vs {o['name']}")) for o in VS if o is not c]
        rel = [("best-trading-journal-for-prop-firms.html",T("Best trading journal for prop firms","Meilleur journal pour prop firms","Mejor diario para prop firms")),("how-to-choose-a-trading-journal.html",T("How to choose a trading journal","Bien choisir son journal de trading","Cómo elegir un diario de trading")),
               ("prop-traders.html",T("For prop traders","Pour traders prop","Para traders prop")),("import.html",T("Import your trades","Importer tes trades","Importar operaciones")),("pricing.html",T("Sweep pricing","Tarifs de Sweep","Precios de Sweep"))]
        chips = lambda label, items, top="": (f'<p class="firm-others"{top}><span>{t(label)}</span>' + "".join(f'<a href="{href(lang,s)}">{t(n)}</a>' for s, n in items) + '</p>')
        b = (f'<section style="padding-top:8px"><div class="wrap narrow"><div class="head"><h2>{t(T("The short answer.","La réponse courte.","La respuesta corta."))}</h2></div>'
             f'<div class="grid g2 vs-picks">{picks}</div></div></section>'
             f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Side by side.","Côte à côte.","Lado a lado."))}</h2></div>'
             f'{_cmp_table(t, c["rows"], name)}<p class="fine vs-note">{t(note)}</p></div></section>'
             f'<section class="rule"><div class="wrap narrow"><article class="article">{article}</article></div></section>'
             f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>{faq}'
             + chips(T("Compare too","Compare aussi","Compara también"), others, ' style="margin-top:36px"')
             + chips(T("Related","Voir aussi","Ver también"), rel, ' style="margin-top:12px"') + '</div></section>')
        ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","inLanguage":lang,
                     "mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q, a in c["faq"]]})
        title = t(T(f"Sweep vs {name} (2026): free {name} alternative · Sweep", f"Sweep vs {name} (2026) : alternative gratuite · Sweep", f"Sweep vs {name} (2026): alternativa gratuita · Sweep"))
        return _fr_nbsp(lang, title, t(c["desc"]), hero + b + final_cta(lang, t), ld)
    return page

# ---------------------------------------------------------------- pillar: best trading journal for prop firm traders
# TraderSync blocks automated reads of its site: its figures are the ones consistent across independent public listings.
def _journal(t, n, name, best, text, price, watch, extra=""):
    return (f'<h2 id="{name.lower()}">{n}. {name}{t(T(": ", " : ", ": "))}{t(best)}</h2><p>{t(text)}</p>'
            f'<ul class="list"><li><b>{t(T("Price","Prix","Precio"))}</b> · {t(price)}</li><li><b>{t(T("Watch out","À savoir","A tener en cuenta"))}</b> · {t(watch)}</li></ul>{extra}')

PILLAR_FAQ = [
 (T("What is the best trading journal for prop firm traders?","Quel est le meilleur journal de trading pour les traders de prop firms ?","¿Cuál es el mejor diario de trading para traders de prop firms?"),
  T("It depends on how you trade. For futures evaluations and funded accounts with each firm’s rules on every account, Sweep is built for that and free to start. If you need automatic broker sync, trade replay or backtesting today, TradeZella is the stronger all-round pick.",
    "Ça dépend de ta façon de trader. Pour des évaluations et des comptes financés en futures, avec les règles de chaque firme sur chaque compte, Sweep est conçu pour ça et gratuit pour commencer. Si tu as besoin aujourd’hui d’une synchro automatique avec ton courtier, du replay de trades ou du backtesting, TradeZella est le choix le plus complet.",
    "Depende de cómo operes. Para evaluaciones y cuentas fondeadas de futuros, con las reglas de cada firma en cada cuenta, Sweep está hecho para eso y es gratis para empezar. Si hoy necesitas sincronización automática con tu bróker, replay de operaciones o backtesting, TradeZella es la opción más completa.")),
 (T("Is there a free trading journal for prop firms?","Existe-t-il un journal de trading gratuit pour les prop firms ?","¿Hay un diario de trading gratis para prop firms?"),
  T("Yes. Sweep has a Free plan with no time limit and no credit card, with prop firm rules included. Tradervue also has a free plan, limited to 30 trades a month.",
    "Oui. Sweep a un forfait Free sans limite de temps et sans carte de crédit, avec les règles des prop firms incluses. Tradervue a aussi un forfait gratuit, limité à 30 trades par mois.",
    "Sí. Sweep tiene un plan Free sin límite de tiempo y sin tarjeta, con las reglas de las prop firms incluidas. Tradervue también tiene un plan gratis, limitado a 30 operaciones al mes.")),
 (T("Which trading journals track prop firm rules?","Quels journaux de trading suivent les règles des prop firms ?","¿Qué diarios de trading siguen las reglas de las prop firms?"),
  T("Sweep preloads the rules of 5 futures prop firms (Apex, Topstep, Lucid, Take Profit Trader and MyFundedFutures) for each account type and checks them against the firms’ official pages every week. TradeZella’s Prop Firm Sync dashboard tracks drawdown, daily loss, profit targets, trading days and consistency. Edgewonk lets you track several prop firm accounts.",
    "Sweep préremplit les règles de 5 prop firms de futures (Apex, Topstep, Lucid, Take Profit Trader et MyFundedFutures) pour chaque type de compte et les vérifie chaque semaine sur les pages officielles des firmes. Le tableau de bord Prop Firm Sync de TradeZella suit le drawdown, la perte quotidienne, les cibles de profit, les jours de trading et la consistance. Edgewonk permet de suivre plusieurs comptes de prop firms.",
    "Sweep precarga las reglas de 5 prop firms de futuros (Apex, Topstep, Lucid, Take Profit Trader y MyFundedFutures) para cada tipo de cuenta y las revisa cada semana en las páginas oficiales de las firmas. El panel Prop Firm Sync de TradeZella sigue el drawdown, la pérdida diaria, los objetivos de ganancia, los días de trading y la consistencia. Edgewonk permite seguir varias cuentas de prop firms.")),
 (T("Do I need automatic broker sync?","Ai-je besoin d’une synchro automatique avec mon courtier ?","¿Necesito sincronización automática con el bróker?"),
  T("It saves a few minutes a day, but it isn’t required. In Sweep you import your platform’s export, paste a screenshot that Sweep AI reads, or type a trade by hand; automatic sync with Rithmic and Tradovate is in development. If you trade many accounts and don’t want any manual step, pick a journal with sync today.",
    "Elle fait gagner quelques minutes par jour, mais elle n’est pas obligatoire. Dans Sweep, tu importes l’export de ta plateforme, tu colles une capture que Sweep AI lit, ou tu saisis un trade à la main ; la synchro automatique avec Rithmic et Tradovate est en développement. Si tu trades beaucoup de comptes et ne veux aucune étape manuelle, choisis un journal qui synchronise dès aujourd’hui.",
    "Ahorra unos minutos al día, pero no es imprescindible. En Sweep importas la exportación de tu plataforma, pegas una captura que Sweep AI lee o escribes una operación a mano; la sincronización automática con Rithmic y Tradovate está en desarrollo. Si operas muchas cuentas y no quieres ningún paso manual, elige hoy un diario con sincronización.")),
]

def vs_link(t, lang, slug, name):
    return f'<p class="firm-others"><a href="{href(lang, slug)}">{t(T(f"Sweep vs {name}, in detail", f"Sweep vs {name}, en détail", f"Sweep vs {name}, en detalle"))} →</a></p>'

def page_best_journal(lang, t):
    from pages8 import FIRMS
    hero = page_hero(t, T("The best trading journal for prop firm traders (2026).","Le meilleur journal de trading pour les traders de prop firms (2026).","El mejor diario de trading para traders de prop firms (2026)."),
        T("Five journals compared on what matters when you trade futures evaluations and funded accounts: price, prop firm rules, how trades get in, and what each one does best.",
          "Cinq journaux comparés sur ce qui compte quand tu trades des évaluations et des comptes financés en futures : le prix, les règles des prop firms, la façon d’ajouter tes trades, et ce que chacun fait de mieux.",
          "Cinco diarios comparados en lo que importa cuando operas evaluaciones y cuentas fondeadas de futuros: el precio, las reglas de las prop firms, cómo entran tus operaciones y lo que cada uno hace mejor."),
        T("Guide","Guide","Guía"))
    glance_rows = [
     ("Sweep", T("Yes, no time limit","Oui, sans limite de temps","Sí, sin límite de tiempo"), T("$19/mo","19 $/mois","19 $/mes")),
     ("TradeZella", T("No","Non","No"), T("$35/mo","35 $/mois","35 $/mes")),
     ("Tradervue", T("Yes, 30 trades a month","Oui, 30 trades par mois","Sí, 30 operaciones al mes"), T("$29.95/mo","29,95 $/mois","29,95 $/mes")),
     ("TraderSync", T("7-day trial","Essai de 7 jours","Prueba de 7 días"), T("$29.95/mo","29,95 $/mois","29,95 $/mes")),
     ("Edgewonk", T("No","Non","No"), T("$197/yr","197 $/an","197 $/año")),
    ]
    glance = (f'<div class="cmp-wrap"><table class="cmp glance"><thead><tr><th scope="col">{t(T("Journal","Journal","Diario"))}</th>'
              f'<th scope="col">{t(T("Free plan","Forfait gratuit","Plan gratis"))}</th><th scope="col">{t(T("Paid plans from","Forfaits payants dès","Planes de pago desde"))}</th></tr></thead><tbody>'
              + "".join(f'<tr><th scope="row"><a href="#{n.lower()}">{n}</a></th><td>{t(a)}</td><td>{t(b)}</td></tr>' for n, a, b in glance_rows) + '</tbody></table></div>')
    firms = (f'<p class="firm-others"><span>{t(T("Firm pages","Pages des firmes","Páginas de las firmas"))}</span>'
             + "".join(f'<a href="{href(lang,s)}">{n}</a>' for s, n in FIRMS) + '</p>')
    vs = vs_link(t, lang, "sweep-vs-tradezella.html", "TradeZella")
    journals = (
     _journal(t, 1, "Sweep", T("best for futures prop firm accounts","idéal pour les comptes prop en futures","ideal para cuentas prop de futuros"),
      T("Sweep is built around prop firm accounts. Pick your firm and account type and the rules are already there: drawdown, consistency and payout conditions, checked against each firm’s official pages every week. Evaluations, funded and live accounts stay apart in your P&L, and a daily routine (plan, rules, review) keeps the focus on process.",
        "Sweep est construit autour des comptes prop. Choisis ta firme et ton type de compte, et les règles sont déjà là : drawdown, consistance et conditions de payout, vérifiées chaque semaine sur les pages officielles de chaque firme. Évaluations, comptes financés et live restent séparés dans ton P&L, et une routine quotidienne (plan, règles, revue) garde l’accent sur le processus.",
        "Sweep está construido alrededor de las cuentas prop. Elige tu firma y tu tipo de cuenta y las reglas ya están ahí: drawdown, consistencia y condiciones de payout, revisadas cada semana en las páginas oficiales de cada firma. Evaluaciones, cuentas fondeadas y live se mantienen separadas en tu P&L, y una rutina diaria (plan, reglas, revisión) mantiene el foco en el proceso."),
      T("Free forever; Pro $19/mo or $159/yr; Elite $39/mo or $329/yr; 60 days of Pro for every new account.","Gratuit pour toujours ; Pro 19 $/mois ou 159 $/an ; Elite 39 $/mois ou 329 $/an ; 60 jours de Pro pour chaque nouveau compte.","Gratis para siempre; Pro 19 $/mes o 159 $/año; Elite 39 $/mes o 329 $/año; 60 días de Pro para cada cuenta nueva."),
      T("No automatic broker sync yet (in development), no trade replay or backtesting, futures only. Expense and payout tracking is on Pro and Elite.","Pas encore de synchro automatique avec le courtier (en développement), pas de replay ni de backtesting, futures seulement. Le suivi des dépenses et des payouts est sur Pro et Elite.","Todavía sin sincronización automática con el bróker (en desarrollo), sin replay ni backtesting, solo futuros. El seguimiento de gastos y payouts está en Pro y Elite."),
      firms)
     + _journal(t, 2, "TradeZella", T("best all-round journal with sync, replay and backtesting","le plus complet, avec synchro, replay et backtesting","el más completo, con sincronización, replay y backtesting"),
      T("TradeZella is a large all-round journal. It syncs trades from hundreds of brokers and prop firms, replays trades second by second and includes backtesting. Its free Prop Firm Sync dashboard tracks drawdown, daily loss, profit targets, trading days and consistency, along with expenses and payouts.",
        "TradeZella est un journal vaste et généraliste. Il synchronise les trades de centaines de courtiers et de prop firms, rejoue les trades seconde par seconde et inclut du backtesting. Son tableau de bord gratuit Prop Firm Sync suit le drawdown, la perte quotidienne, les cibles de profit, les jours de trading et la consistance, ainsi que les dépenses et les payouts.",
        "TradeZella es un diario amplio y generalista. Sincroniza operaciones de cientos de brókers y prop firms, reproduce las operaciones segundo a segundo e incluye backtesting. Su panel gratuito Prop Firm Sync sigue el drawdown, la pérdida diaria, los objetivos de ganancia, los días de trading y la consistencia, además de los gastos y los payouts."),
      T("Essential $35/mo, Pro $59/mo, Ultra $99/mo; about 25% less billed yearly.","Essential 35 $/mois, Pro 59 $/mois, Ultra 99 $/mois ; environ 25 % de moins en facturation annuelle.","Essential 35 $/mes, Pro 59 $/mes, Ultra 99 $/mes; un 25 % menos aprox. con facturación anual."),
      T("No free plan; trade replay starts on Pro.","Pas de forfait gratuit ; le replay commence avec Pro.","Sin plan gratis; el replay empieza en Pro."), vs)
     + _journal(t, 3, "Tradervue", T("best for detailed reports, especially in stocks","idéal pour des rapports détaillés, surtout en actions","ideal para informes detallados, sobre todo en acciones"),
      T("Tradervue focuses on reporting: MFE and MAE statistics, exit analysis, risk and liquidity reports, with mentoring and trade sharing. Futures are supported on its paid plans.",
        "Tradervue mise sur les rapports : statistiques MFE et MAE, analyse des sorties, rapports de risque et de liquidité, avec mentorat et partage de trades. Les futures sont pris en charge sur ses forfaits payants.",
        "Tradervue se centra en los informes: estadísticas MFE y MAE, análisis de salidas, informes de riesgo y liquidez, con mentoría y trades compartidos. Los futuros están incluidos en sus planes de pago."),
      T("Free plan limited to 30 trades a month; Silver $29.95/mo, Gold $49.95/mo, with a trial.","Forfait gratuit limité à 30 trades par mois ; Silver 29,95 $/mois, Gold 49,95 $/mois, avec un essai.","Plan gratis limitado a 30 operaciones al mes; Silver 29,95 $/mes, Gold 49,95 $/mes, con prueba."),
      T("No prop firm features listed on its pricing page.","Aucune fonction pour les prop firms sur sa page de tarifs.","Ninguna función para prop firms en su página de precios."), vs_link(t, lang, "sweep-vs-tradervue.html", "Tradervue"))
     + _journal(t, 4, "TraderSync", T("best for replay and AI across many markets","idéal pour le replay et l’IA sur plusieurs marchés","ideal para replay e IA en muchos mercados"),
      T("TraderSync covers stocks, futures, forex and crypto, with broker sync, a mobile app, market replay and an AI assistant on every plan. Trade replay starts on Premium; automated backtesting and an AI coach come with Elite.",
        "TraderSync couvre les actions, les futures, le forex et les cryptos, avec synchro courtier, app mobile, replay de marché et assistant IA sur tous les forfaits. Le replay de trades commence avec Premium ; le backtesting automatisé et un coach IA viennent avec Elite.",
        "TraderSync cubre acciones, futuros, forex y cripto, con sincronización con el bróker, app móvil, replay de mercado y asistente de IA en todos los planes. El replay de operaciones empieza en Premium; el backtesting automatizado y un coach de IA llegan con Elite."),
      T("Pro $29.95/mo, Premium $49.95/mo, Elite $79.95/mo, with a 7-day trial; up to 25% less billed yearly.","Pro 29,95 $/mois, Premium 49,95 $/mois, Elite 79,95 $/mois, avec un essai de 7 jours ; jusqu’à 25 % de moins en facturation annuelle.","Pro 29,95 $/mes, Premium 49,95 $/mes, Elite 79,95 $/mes, con una prueba de 7 días; hasta un 25 % menos con facturación anual."),
      T("Pro is limited to 5 accounts and has no trade replay.","Pro est limité à 5 comptes et n’a pas le replay de trades.","Pro está limitado a 5 cuentas y no tiene replay de operaciones."), vs_link(t, lang, "sweep-vs-tradersync.html", "TraderSync"))
     + _journal(t, 5, "Edgewonk", T("best for psychology and strategy statistics","idéal pour la psychologie et les statistiques de stratégie","ideal para psicología y estadísticas de estrategia"),
      T("Edgewonk focuses on finding your edge: a Tiltmeter for emotional mistakes, an Edge Finder and strategy testing tools. It covers forex, stocks, futures, crypto, indices, commodities and options, and tracks unlimited prop firm accounts.",
        "Edgewonk aide à trouver ton edge : un Tiltmeter pour les erreurs émotionnelles, un Edge Finder et des outils pour tester des stratégies. Il couvre le forex, les actions, les futures, les cryptos, les indices, les matières premières et les options, et suit un nombre illimité de comptes de prop firms.",
        "Edgewonk se centra en encontrar tu ventaja: un Tiltmeter para los errores emocionales, un Edge Finder y herramientas para probar estrategias. Cubre forex, acciones, futuros, cripto, índices, materias primas y opciones, y sigue cuentas de prop firms ilimitadas."),
      T("$197 a year, with a 14-day refund window; no free plan.","197 $ par année, remboursable pendant 14 jours ; pas de forfait gratuit.","197 $ al año, con reembolso durante 14 días; sin plan gratis."),
      T("Automatic import lists NinjaTrader and Tradovate among its platforms: check yours before you buy.","L’import automatique cite NinjaTrader et Tradovate parmi ses plateformes : vérifie la tienne avant d’acheter.","La importación automática incluye NinjaTrader y Tradovate entre sus plataformas: comprueba la tuya antes de comprar."), vs_link(t, lang, "sweep-vs-edgewonk.html", "Edgewonk")))
    pick = [
     T("<b>Futures evaluations and funded accounts, with firm rules on every account:</b> Sweep.","<b>Évaluations et comptes financés en futures, avec les règles de la firme sur chaque compte :</b> Sweep.","<b>Evaluaciones y cuentas fondeadas de futuros, con las reglas de la firma en cada cuenta:</b> Sweep."),
     T("<b>Automatic broker sync, replay and backtesting today:</b> TradeZella.","<b>Synchro automatique, replay et backtesting dès aujourd’hui :</b> TradeZella.","<b>Sincronización automática, replay y backtesting ya hoy:</b> TradeZella."),
     T("<b>Mostly stocks, with deep reports:</b> Tradervue.","<b>Surtout des actions, avec des rapports poussés :</b> Tradervue.","<b>Sobre todo acciones, con informes a fondo:</b> Tradervue."),
     T("<b>Broker sync, a mobile app, replay and AI across many markets:</b> TraderSync.","<b>Synchro courtier, app mobile, replay et IA sur plusieurs marchés :</b> TraderSync.","<b>Sincronización, app móvil, replay e IA en muchos mercados:</b> TraderSync."),
     T("<b>Psychology and strategy statistics, one yearly price:</b> Edgewonk.","<b>Psychologie et statistiques de stratégie, un seul prix annuel :</b> Edgewonk.","<b>Psicología y estadísticas de estrategia, un solo precio anual:</b> Edgewonk."),
    ]
    note = T(f"We make Sweep, so it’s listed first; each section says where another journal is the better fit. Prices in USD, monthly billing unless noted, before tax, from each journal’s public website and help pages, checked on {CHECKED['en']}. Plans change often: confirm on the journal’s site before you buy, and tell us at {EMAIL} if something is out of date. All names are trademarks of their owners.",
             f"On fait Sweep, donc il est en premier ; chaque section dit quand un autre journal convient mieux. Prix en USD, facturation mensuelle sauf mention contraire, avant taxes, tirés du site public et des pages d’aide de chaque journal, vérifiés le {CHECKED['fr']}. Les forfaits changent souvent : confirme sur le site du journal avant d’acheter, et écris-nous à {EMAIL} si une info n’est plus à jour. Tous les noms sont des marques de leurs propriétaires.",
             f"Hacemos Sweep, así que aparece primero; cada sección dice cuándo otro diario encaja mejor. Precios en USD, facturación mensual salvo indicación, antes de impuestos, tomados del sitio público y las páginas de ayuda de cada diario, revisados el {CHECKED['es']}. Los planes cambian a menudo: confírmalo en el sitio del diario antes de comprar y escríbenos a {EMAIL} si algo ya no está al día. Todos los nombres son marcas de sus propietarios.")
    faq = "".join(faq_item(t, q, a) for q, a in PILLAR_FAQ)
    rel = [("sweep-vs-tradezella.html",T("Sweep vs TradeZella","Sweep vs TradeZella","Sweep vs TradeZella")),("how-to-choose-a-trading-journal.html",T("How to choose a trading journal","Bien choisir son journal de trading","Cómo elegir un diario de trading")),
           ("prop-traders.html",T("For prop traders","Pour traders prop","Para traders prop")),("pricing.html",T("Sweep pricing","Tarifs de Sweep","Precios de Sweep"))]
    b = (f'<section style="padding-top:8px"><div class="wrap narrow"><div class="head"><h2>{t(T("At a glance.","En bref.","De un vistazo."))}</h2></div>{glance}<p class="fine vs-note">{t(note)}</p></div></section>'
         f'<section class="rule"><div class="wrap narrow"><article class="article">{journals}</article></div></section>'
         f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Which one should you pick?","Lequel choisir ?","¿Cuál elegir?"))}</h2></div>{ul(t, pick)}</div></section>'
         f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>{faq}'
         f'<p class="firm-others" style="margin-top:36px"><span>{t(T("Related","Voir aussi","Ver también"))}</span>'
         + "".join(f'<a href="{href(lang,s)}">{t(n)}</a>' for s, n in rel) + '</p></div></section>')
    ld = jsonld({"@context":"https://schema.org","@graph":[
        {"@type":"Article","headline":t(T("The best trading journal for prop firm traders (2026)","Le meilleur journal de trading pour les traders de prop firms (2026)","El mejor diario de trading para traders de prop firms (2026)")),
         "inLanguage":lang,"datePublished":"2026-10-09","dateModified":"2026-10-09","publisher":{"@id":f"https://{DOMAIN}/#org"},"author":{"@type":"Organization","name":"Sweep"}},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q, a in PILLAR_FAQ]}]})
    return _fr_nbsp(lang, t(T("Best trading journal for prop firm traders (2026) · Sweep","Meilleur journal de trading pour prop firms (2026) · Sweep","Mejor diario de trading para prop firms (2026) · Sweep")),
            t(T("Sweep, TradeZella, Tradervue, TraderSync and Edgewonk compared for futures prop firm traders: free plans, prices, firm rules and what each does best.",
                "Sweep, TradeZella, Tradervue, TraderSync et Edgewonk comparés pour les traders de prop firms : forfaits gratuits, prix, règles des firmes et points forts.",
                "Sweep, TradeZella, Tradervue, TraderSync y Edgewonk comparados para traders de prop firms: planes gratis, precios, reglas de las firmas y puntos fuertes.")),
            hero + b + final_cta(lang, t), ld)
