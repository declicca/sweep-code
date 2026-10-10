from core import *

# Comparison pages. Competitor facts come from their public pages; update CHECKED when you re-verify them.
CHECKED = T("October 9, 2026","9 octobre 2026","9 de octubre de 2026")

def _cmp_table(t, rows, other):
    head = (f'<thead><tr><th scope="col"><span class="sr">{t(T("Feature","Fonctionnalité","Función"))}</span></th>'
            f'<th scope="col">Sweep</th><th scope="col">{other}</th></tr></thead>')
    body = "".join(f'<tr><th scope="row">{t(a)}</th><td>{t(b)}</td><td>{t(c)}</td></tr>' for a, b, c in rows)
    return f'<div class="cmp-wrap"><table class="cmp two">{head}<tbody>{body}</tbody></table></div>'

def _pick(t, h, items):
    return f'<div><h3>{t(h)}</h3>{ul(t, items)}</div>'

TZ_FAQ = [
 (T("Is there a free alternative to TradeZella?","Existe-t-il une alternative gratuite à TradeZella ?","¿Hay una alternativa gratis a TradeZella?"),
  T("Yes. Sweep has a Free plan with no time limit and no credit card, and every new account gets 60 days of Pro. TradeZella shows no free plan on its pricing page; its plans start at $35 a month, or $26 a month billed yearly.",
    "Oui. Sweep a un forfait Free sans limite de temps et sans carte de crédit, et chaque nouveau compte reçoit 60 jours de Pro. TradeZella n’affiche aucun forfait gratuit sur sa page de tarifs ; ses forfaits commencent à 35 $ par mois, ou 26 $ par mois en facturation annuelle.",
    "Sí. Sweep tiene un plan Free sin límite de tiempo y sin tarjeta, y cada cuenta nueva recibe 60 días de Pro. TradeZella no muestra ningún plan gratis en su página de precios; sus planes empiezan en 35 $ al mes, o 26 $ al mes con facturación anual.")),
 (T("Which one is cheaper?","Lequel coûte le moins cher ?","¿Cuál es más barato?"),
  T("Sweep. Pro is $19 a month or $159 a year, and Elite is $39 a month or $329 a year. TradeZella’s plans are $35, $59 and $99 a month, or $315, $531 and $891 a year. Prices in USD, before tax.",
    "Sweep. Pro coûte 19 $ par mois ou 159 $ par année, et Elite 39 $ par mois ou 329 $ par année. Les forfaits de TradeZella coûtent 35 $, 59 $ et 99 $ par mois, ou 315 $, 531 $ et 891 $ par année. Prix en USD, avant taxes.",
    "Sweep. Pro cuesta 19 $ al mes o 159 $ al año, y Elite 39 $ al mes o 329 $ al año. Los planes de TradeZella cuestan 35 $, 59 $ y 99 $ al mes, o 315 $, 531 $ y 891 $ al año. Precios en USD, antes de impuestos.")),
 (T("Does TradeZella track prop firm rules?","TradeZella suit-il les règles des prop firms ?","¿TradeZella sigue las reglas de las prop firms?"),
  T("Yes. Its Prop Firm Sync dashboard, free for TradeZella users, tracks drawdown, daily loss limits, profit targets, trading days and consistency, along with expenses and payouts. In Sweep, rules come preloaded for 7 futures prop firms and each account type, and are checked against the firms’ official pages every week.",
    "Oui. Son tableau de bord Prop Firm Sync, gratuit pour les utilisateurs de TradeZella, suit le drawdown, les limites de perte quotidienne, les cibles de profit, les jours de trading et la consistance, ainsi que les dépenses et les payouts. Dans Sweep, les règles sont préremplies pour 7 prop firms de futures et chaque type de compte, et vérifiées chaque semaine sur les pages officielles des firmes.",
    "Sí. Su panel Prop Firm Sync, gratis para los usuarios de TradeZella, sigue el drawdown, los límites de pérdida diaria, los objetivos de ganancia, los días de trading y la consistencia, además de los gastos y los payouts. En Sweep, las reglas vienen precargadas para 7 prop firms de futuros y cada tipo de cuenta, y se revisan cada semana en las páginas oficiales de las firmas.")),
 (T("How do I add trades to Sweep?","Comment ajouter des trades dans Sweep ?","¿Cómo añado operaciones en Sweep?"),
  T("Import your platform’s export (Tradovate, Rithmic, ProjectX or TradingView), paste a screenshot that Sweep AI reads, or type the trade by hand. Automatic sync with Rithmic and Tradovate is in development.",
    "Importe l’export de ta plateforme (Tradovate, Rithmic, ProjectX ou TradingView), colle une capture que Sweep AI lit, ou saisis le trade à la main. La synchronisation automatique avec Rithmic et Tradovate est en développement.",
    "Importa la exportación de tu plataforma (Tradovate, Rithmic, ProjectX o TradingView), pega una captura que Sweep AI lee o escribe la operación a mano. La sincronización automática con Rithmic y Tradovate está en desarrollo.")),
 (T("Does Sweep have trade replay or backtesting?","Sweep offre-t-il le replay de trades ou le backtesting ?","¿Sweep tiene replay de operaciones o backtesting?"),
  T("No. Sweep focuses on journaling, prop firm rules and your daily routine. If replay or backtesting is part of how you work, TradeZella is the better fit today.",
    "Non. Sweep se concentre sur le journal, les règles des prop firms et ta routine quotidienne. Si le replay ou le backtesting fait partie de ta façon de travailler, TradeZella te conviendra mieux aujourd’hui.",
    "No. Sweep se centra en el diario, las reglas de las prop firms y tu rutina diaria. Si el replay o el backtesting forman parte de tu forma de trabajar, hoy TradeZella te encajará mejor.")),
]

def page_vs_tradezella(lang, t):
    hero = page_hero(t, T("Sweep vs TradeZella.","Sweep vs TradeZella.","Sweep vs TradeZella."),
        T("Two trading journals built for different traders. What each one does, what it costs, and when TradeZella is the better pick.",
          "Deux journaux de trading pensés pour des traders différents. Ce que fait chacun, ce qu’il coûte, et quand TradeZella est le meilleur choix.",
          "Dos diarios de trading pensados para traders distintos. Qué hace cada uno, cuánto cuesta y cuándo TradeZella es la mejor opción."),
        T("Compare","Comparer","Comparar"))
    picks = (_pick(t, T("Choose Sweep if","Choisis Sweep si","Elige Sweep si"), [
        T("You trade futures evaluations and funded accounts, and want each firm’s rules on every account.","Tu trades des évaluations et des comptes financés en futures, et tu veux les règles de chaque firme sur chaque compte.","Operas evaluaciones y cuentas fondeadas de futuros y quieres las reglas de cada firma en cada cuenta."),
        T("You want a free plan with no time limit, or Pro for $19 a month.","Tu veux un forfait gratuit sans limite de temps, ou Pro à 19 $ par mois.","Quieres un plan gratis sin límite de tiempo, o Pro por 19 $ al mes."),
        T("You want a daily routine that rewards following your plan, not just your P&L.","Tu veux une routine quotidienne qui récompense le respect de ton plan, pas seulement ton P&L.","Quieres una rutina diaria que premie seguir tu plan, no solo tu P&L."),
        T("You journal in English, French or Spanish.","Tu tiens ton journal en anglais, en français ou en espagnol.","Llevas tu diario en inglés, francés o español.")])
      + _pick(t, T("Choose TradeZella if","Choisis TradeZella si","Elige TradeZella si"), [
        T("You want trades to sync from your broker automatically, today.","Tu veux que tes trades arrivent automatiquement de ton courtier, dès aujourd’hui.","Quieres que tus operaciones lleguen solas desde tu bróker, ya hoy."),
        T("You use trade replay or backtesting.","Tu utilises le replay de trades ou le backtesting.","Usas el replay de operaciones o el backtesting."),
        T("You also trade stocks, forex or crypto.","Tu trades aussi des actions, du forex ou des cryptos.","También operas acciones, forex o cripto."),
        T("You work with a mentor who reviews your journal.","Tu travailles avec un mentor qui consulte ton journal.","Trabajas con un mentor que revisa tu diario.")]))
    rows = [
     (T("Free plan","Forfait gratuit","Plan gratis"), T("Yes, no time limit, no card","Oui, sans limite de temps, sans carte","Sí, sin límite de tiempo, sin tarjeta"), T("None on its pricing page","Aucun sur sa page de tarifs","Ninguno en su página de precios")),
     (T("Trial of a paid plan","Essai d’un forfait payant","Prueba de un plan de pago"), T("60 days of Pro","60 jours de Pro","60 días de Pro"), T("None on its pricing page","Aucun sur sa page de tarifs","Ninguno en su página de precios")),
     (T("Monthly price","Prix mensuel","Precio mensual"), T("Pro\u00a0$19 · Elite\u00a0$39","Pro\u00a019\u00a0$ · Elite\u00a039\u00a0$","Pro\u00a019\u00a0$ · Elite\u00a039\u00a0$"), T("Essential\u00a0$35 · Pro\u00a0$59 · Ultra\u00a0$99","Essential\u00a035\u00a0$ · Pro\u00a059\u00a0$ · Ultra\u00a099\u00a0$","Essential\u00a035\u00a0$ · Pro\u00a059\u00a0$ · Ultra\u00a099\u00a0$")),
     (T("Yearly price","Prix annuel","Precio anual"), T("Pro\u00a0$159 · Elite\u00a0$329","Pro\u00a0159\u00a0$ · Elite\u00a0329\u00a0$","Pro\u00a0159\u00a0$ · Elite\u00a0329\u00a0$"), T("Essential\u00a0$315 · Pro\u00a0$531 · Ultra\u00a0$891","Essential\u00a0315\u00a0$ · Pro\u00a0531\u00a0$ · Ultra\u00a0891\u00a0$","Essential\u00a0315\u00a0$ · Pro\u00a0531\u00a0$ · Ultra\u00a0891\u00a0$")),
     (T("Adding trades","Ajouter des trades","Añadir operaciones"), T("File import, screenshot read by AI, or by hand","Import de fichier, capture lue par l’IA, ou à la main","Importación de archivo, captura leída por la IA o a mano"), T("Auto-sync, file upload or by hand","Synchro automatique, import de fichier ou à la main","Sincronización automática, subida de archivo o a mano")),
     (T("Automatic broker sync","Synchro automatique avec le courtier","Sincronización automática con el bróker"), T("In development","En développement","En desarrollo"), T("Yes","Oui","Sí")),
     (T("Prop firm rules","Règles des prop firms","Reglas de las prop firms"), T("Preloaded for 7 futures firms, per account type, checked every week","Préremplies pour 7 firmes de futures, par type de compte, vérifiées chaque semaine","Precargadas para 7 firmas de futuros, por tipo de cuenta, revisadas cada semana"), T("Prop Firm Sync: drawdown, daily loss, target, trading days, consistency","Prop Firm Sync : drawdown, perte quotidienne, cible, jours de trading, consistance","Prop Firm Sync: drawdown, pérdida diaria, objetivo, días de trading, consistencia")),
     (T("Expense and payout tracking","Suivi des dépenses et des payouts","Seguimiento de gastos y payouts"), T("Pro and Elite","Pro et Elite","Pro y Elite"), T("Every plan","Tous les forfaits","Todos los planes")),
     (T("Trade replay","Replay de trades","Replay de operaciones"), T("No","Non","No"), T("Pro and Ultra","Pro et Ultra","Pro y Ultra")),
     (T("Backtesting","Backtesting","Backtesting"), T("No","Non","No"), T("Every plan (AI runs on Pro and Ultra)","Tous les forfaits (exécutions IA sur Pro et Ultra)","Todos los planes (ejecuciones con IA en Pro y Ultra)")),
     (T("Markets","Marchés","Mercados"), T("Futures","Futures","Futuros"), T("Futures, stocks, forex, crypto","Futures, actions, forex, cryptos","Futuros, acciones, forex, cripto")),
    ]
    note = T(f"TradeZella details come from its public pricing and Prop Firm Sync pages, checked on {CHECKED['en']}. Prices in USD, before tax. Something out of date? Write to {EMAIL}. TradeZella is a trademark of its owner; Sweep is not affiliated with TradeZella.",
             f"Les infos sur TradeZella viennent de ses pages publiques de tarifs et de Prop Firm Sync, vérifiées le {CHECKED['fr']}. Prix en USD, avant taxes. Une info n’est plus à jour ? Écris à {EMAIL}. TradeZella est une marque de son propriétaire ; Sweep n’est pas affilié à TradeZella.",
             f"La información de TradeZella proviene de sus páginas públicas de precios y de Prop Firm Sync, revisadas el {CHECKED['es']}. Precios en USD, antes de impuestos. ¿Algo ya no está al día? Escribe a {EMAIL}. TradeZella es una marca de su propietario; Sweep no está afiliado a TradeZella.")
    diff = [
     (T("Where Sweep is different","Ce qui distingue Sweep","Lo que distingue a Sweep"), [
      T("Sweep starts from your prop accounts. Pick your firm and account type, and the drawdown, consistency and payout conditions are already there. They’re checked against each firm’s official pages every week; when a firm changes a rule, you’re notified and choose whether to apply it.",
        "Sweep part de tes comptes prop. Choisis ta firme et ton type de compte : le drawdown, la consistance et les conditions de payout sont déjà là. Elles sont vérifiées chaque semaine sur les pages officielles de chaque firme ; quand une firme change une règle, tu es averti et tu choisis de l’appliquer ou non.",
        "Sweep parte de tus cuentas prop. Elige tu firma y tu tipo de cuenta: el drawdown, la consistencia y las condiciones de payout ya están ahí. Se revisan cada semana en las páginas oficiales de cada firma; cuando una firma cambia una regla, recibes un aviso y eliges si aplicarla."),
      T("Your money stays in separate layers: evaluations, funded and live accounts are never mixed, and copy trading counts once in your statistics, not once per account.",
        "Ton argent reste en couches séparées : évaluations, comptes financés et live ne sont jamais mélangés, et le copy trading compte une seule fois dans tes statistiques, pas une fois par compte.",
        "Tu dinero se mantiene en capas separadas: evaluaciones, cuentas fondeadas y live nunca se mezclan, y el copy trading cuenta una sola vez en tus estadísticas, no una vez por cuenta."),
      T("Each session has a routine: a plan before the open, your rules during it, and a short review after the close. Sweep measures those habits, so a red day where you followed your plan still counts.",
        "Chaque séance a sa routine : un plan avant l’ouverture, tes règles pendant, et une courte revue après la clôture. Sweep mesure ces habitudes : une journée dans le rouge où tu as suivi ton plan compte quand même.",
        "Cada sesión tiene su rutina: un plan antes de la apertura, tus reglas durante y una breve revisión tras el cierre. Sweep mide esos hábitos, así que un día en rojo en el que seguiste tu plan también cuenta.")]),
     (T("Where TradeZella is ahead","Là où TradeZella est en avance","Donde TradeZella va por delante"), [
      T("TradeZella is a larger, all-round journal. It syncs trades automatically from many brokers, replays your trades second by second, and includes backtesting on historical data. It covers stocks, forex and crypto as well as futures, and offers a mentor mode. If you rely on any of these today, it’s the better fit.",
        "TradeZella est un journal plus vaste et plus généraliste. Il synchronise automatiquement les trades de nombreux courtiers, rejoue tes trades seconde par seconde et inclut du backtesting sur données historiques. Il couvre aussi les actions, le forex et les cryptos, et offre un mode mentor. Si tu comptes sur l’une de ces fonctions aujourd’hui, c’est le meilleur choix.",
        "TradeZella es un diario más amplio y generalista. Sincroniza automáticamente las operaciones de muchos brókers, reproduce tus operaciones segundo a segundo e incluye backtesting con datos históricos. También cubre acciones, forex y cripto, y ofrece un modo mentor. Si hoy dependes de alguna de estas funciones, es la mejor opción."),
      T("At Sweep, automatic sync with Rithmic and Tradovate is in development; we’ll announce it on our changelog as soon as it’s live.",
        "Chez Sweep, la synchronisation automatique avec Rithmic et Tradovate est en développement ; on l’annoncera dans les nouveautés dès qu’elle sera disponible.",
        "En Sweep, la sincronización automática con Rithmic y Tradovate está en desarrollo; la anunciaremos en las novedades en cuanto esté disponible.")]),
    ]
    article = "".join(f'<h2>{t(h)}</h2>' + "".join(f"<p>{t(p)}</p>" for p in ps) for h, ps in diff)
    faq = "".join(faq_item(t, q, a) for q, a in TZ_FAQ)
    rel = [("how-to-choose-a-trading-journal.html",T("How to choose a trading journal","Bien choisir son journal de trading","Cómo elegir un diario de trading")),
           ("prop-traders.html",T("For prop traders","Pour traders prop","Para traders prop")),("import.html",T("Import your trades","Importer tes trades","Importar operaciones")),("pricing.html",T("Sweep pricing","Tarifs de Sweep","Precios de Sweep"))]
    b = (f'<section style="padding-top:8px"><div class="wrap narrow"><div class="head"><h2>{t(T("The short answer.","La réponse courte.","La respuesta corta."))}</h2></div>'
         f'<div class="grid g2 vs-picks">{picks}</div></div></section>'
         f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Side by side.","Côte à côte.","Lado a lado."))}</h2></div>'
         f'{_cmp_table(t, rows, "TradeZella")}<p class="fine vs-note">{t(note)}</p></div></section>'
         f'<section class="rule"><div class="wrap narrow"><article class="article">{article}</article></div></section>'
         f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>{faq}'
         f'<p class="firm-others" style="margin-top:36px"><span>{t(T("Related","Voir aussi","Ver también"))}</span>'
         + "".join(f'<a href="{href(lang,s)}">{t(n)}</a>' for s, n in rel) + '</p></div></section>')
    ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","inLanguage":lang,
                 "mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q, a in TZ_FAQ]})
    return (t(T("Sweep vs TradeZella (2026): free TradeZella alternative · Sweep","Sweep vs TradeZella (2026) : alternative gratuite · Sweep","Sweep vs TradeZella (2026): alternativa gratuita · Sweep")),
            t(T("Sweep vs TradeZella for futures prop firm traders: free plan, prices, trade import, firm rules, replay and backtesting, compared side by side.",
                "Sweep vs TradeZella pour les traders de prop firms en futures : forfait gratuit, prix, import, règles des firmes, replay et backtesting, côte à côte.",
                "Sweep vs TradeZella para traders de prop firms de futuros: plan gratis, precios, importación, reglas de las firmas, replay y backtesting, lado a lado.")),
            hero + b + final_cta(lang, t), ld)
