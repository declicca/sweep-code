from core import *

FIRMS = [("topstep-trading-journal.html","Topstep"),("apex-trader-funding-journal.html","Apex Trader Funding"),
         ("take-profit-trader-journal.html","Take Profit Trader"),("lucid-trading-journal.html","Lucid Trading"),
         ("myfundedfutures-journal.html","MyFundedFutures"),
         ("tradeify-trading-journal.html","Tradeify"),("alpha-futures-trading-journal.html","Alpha Futures")]

def _f(d, firm):
    return {k: v.replace("{F}", firm) for k, v in d.items()}

EXAMPLES = {
 "Topstep": T("<b>Payout conditions</b> counted for you, for example 5 winning days of $150 or more (for guidance)","<b>Conditions de payout</b> comptées pour toi, par exemple 5 jours gagnants de 150 $ et plus (à titre indicatif)","<b>Condiciones de payout</b> contadas por ti, por ejemplo 5 días ganadores de 150 $ o más (a título indicativo)"),
 "Apex Trader Funding": T("<b>Payout conditions</b> counted for you, including the cushion to keep (the safety net), for guidance","<b>Conditions de payout</b> comptées pour toi, dont le coussin à garder (le « safety net »), à titre indicatif","<b>Condiciones de payout</b> contadas por ti, incluido el colchón a mantener (el «safety net»), a título indicativo"),
}
GENERIC_PAYOUT = T("<b>Payout conditions</b> counted since your last request: winning days, cushion, minimum and maximum","<b>Conditions de payout</b> comptées depuis ta dernière demande : jours gagnants, coussin, minimum et maximum","<b>Condiciones de payout</b> contadas desde tu última solicitud: días ganadores, colchón, mínimo y máximo")

def size_range(rp, lang):
    """« 25K to 300K »: the sizes in the app's catalogue for this firm."""
    sz = sorted({x["size"] for p in rp["programs"] for x in p["sizes"]}) if rp else []
    k = lambda v: f"{v / 1000:g}K"
    if not sz: return ""
    return k(sz[0]) if len(sz) == 1 else k(sz[0]) + {"en": " to ", "fr": " à ", "es": " a "}[lang] + k(sz[-1])

def make_firm_page(slug, firm):
    def page(lang, t):
        F = lambda d: t(_f(d, firm))
        has = firm in PRESET_FIRMS   # rules preloaded in the app for this firm?
        import pages18
        rp = next((x for x in pages18.presets.FIRMS if x["name"] == firm), None)   # its rules page, if any
        lead_manual = T("Add your {F} account as “Other firm”, enter its rules once, and Sweep checks every trade against them, so you see when you’re ready for the payout. {F}’s rules aren’t preloaded in Sweep yet.",
                        "Ajoute ton compte {F} comme « Autre firme », saisis ses règles une fois, et Sweep vérifie chaque trade contre elles : tu vois quand tu es prêt pour le payout. Les règles de {F} ne sont pas encore préremplies dans Sweep.",
                        "Añade tu cuenta de {F} como «Otra firma», introduce sus reglas una vez y Sweep comprueba cada operación con ellas: ves cuándo estás listo para el payout. Las reglas de {F} aún no están precargadas en Sweep.")
        hero = page_hero(t, _f(T("A trading journal for {F} traders.","Un journal de trading pour les traders {F}.","Un diario de trading para traders de {F}."), firm),
            _f(lead_manual, firm) if not has else _f(T("Add your {F} account in one click and Sweep prefills its rules from the {F} preset, for guidance only. Then every trade is checked against them, and you see when you’re ready for the payout.",
                 "Ajoute ton compte {F} en un clic : Sweep préremplit ses règles à partir du préréglage {F}, à titre indicatif. Ensuite, chaque trade est vérifié contre elles, et tu vois quand tu es prêt pour le payout.",
                 "Añade tu cuenta de {F} en un clic: Sweep precarga sus reglas desde el preajuste de {F}, a título indicativo. Después, cada operación se comprueba con ellas y ves cuándo estás listo para el payout."), firm),
            T("Prop firms","Prop firms","Prop firms"), f'<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_firm">{t(T("Start for free","Commencer gratuitement","Empieza gratis"))}</a>')
        rules = [T("<b>Profit target</b> with a progress bar","<b>Objectif de profit</b> avec barre de progression","<b>Objetivo de beneficio</b> con barra de progreso"),
                 T("<b>Maximum drawdown,</b> trailing or static","<b>Drawdown maximum,</b> suiveur ou statique","<b>Drawdown máximo,</b> dinámico o estático"),
                 T("<b>Daily loss limit</b> with a warning in the trade ticket","<b>Perte quotidienne max</b> avec alerte dans le ticket","<b>Pérdida diaria máxima</b> con aviso en el ticket"),
                 T("<b>Consistency</b> rule in %","Règle de <b>consistance</b> en %","Regla de <b>consistencia</b> en %"),
                 T("<b>Minimum trading days</b> counted for you","<b>Jours de trading minimum</b> comptés pour toi","<b>Días mínimos de trading</b> contados por ti"),
                 EXAMPLES.get(firm, GENERIC_PAYOUT),
                 T("<b>Evaluation passed → funded</b> automatically, then funded → live","<b>Évaluation réussie → financé</b> automatiquement, puis financé → live","<b>Evaluación superada → fondeada</b> automáticamente, luego fondeada → live")]
        b = split(t, T("Rules","Règles","Reglas"), _f(T("Every {F} rule, on every trade.","Chaque règle {F}, à chaque trade.","Cada regla de {F}, en cada operación."), firm),
            _f(T("Enter your account’s rules once: every value below is then tracked on every trade. Firms update their rules, so always check the current ones on {F}’s site.",
                 "Saisis les règles de ton compte une fois : chaque valeur ci-dessous est ensuite suivie à chaque trade. Les firmes mettent leurs règles à jour : vérifie toujours les règles actuelles sur le site de {F}.",
                 "Introduce las reglas de tu cuenta una vez: cada valor de abajo se sigue en cada operación. Las firmas actualizan sus reglas: verifica siempre las actuales en el sitio de {F}."), firm) if not has else
            {l: v.replace("{R}", size_range(rp, l)) for l, v in _f(T("Pick the account size ({R}) and the preset fills in the rules below. Every value stays editable, because firms update their rules: always check the current ones on {F}’s site.",
                 "Choisis la taille du compte ({R}) et le préréglage remplit les règles ci-dessous. Chaque valeur reste modifiable, parce que les firmes mettent leurs règles à jour : vérifie toujours les règles actuelles sur le site de {F}.",
                 "Elige el tamaño de la cuenta ({R}) y el preajuste completa las reglas de abajo. Cada valor sigue siendo editable, porque las firmas actualizan sus reglas: verifica siempre las actuales en el sitio de {F}."), firm).items()},
            rules, frame("accounts", lang, F(T("{F} accounts in Sweep, sample data","Comptes {F} dans Sweep, données d’exemple","Cuentas de {F} en Sweep, datos de ejemplo")), t), id_="rules",
            more=(f'<p><a class="tlink" href="{href(lang, pages18.page_of(rp))}">{F(T("{F} rules, explained","Les règles de {F}, expliquées","Las reglas de {F}, explicadas"))} <span aria-hidden="true">→</span></a></p>' if rp else ""))
        b += split(t, T("Payouts and costs","Payouts et coûts","Payouts y costes"), _f(T("Know what {F} really pays you.","Sache ce que {F} te rapporte vraiment.","Conoce lo que {F} te paga realmente."), firm),
            T("Track evaluations, activations and resets next to every payout, from requested to paid. Your net result is always one line: payouts minus what you spent.",
              "Suis évaluations, activations et resets à côté de chaque payout, de la demande au paiement. Ton résultat net tient toujours en une ligne : payouts moins ce que tu as dépensé.",
              "Sigue evaluaciones, activaciones y reinicios junto a cada payout, de la solicitud al pago. Tu resultado neto siempre cabe en una línea: payouts menos lo que gastaste."),
            [T("Copy a trade to several accounts at once","Copie un trade sur plusieurs comptes en même temps","Copia una operación en varias cuentas a la vez"),
             T("Closed or failed accounts keep their history","Les comptes fermés ou échoués gardent leur historique","Las cuentas cerradas o fallidas conservan su historial"),
             T("Share a payout card, amounts optional","Partage une carte de payout, montants optionnels","Comparte una tarjeta de payout, importes opcionales")],
            frame("payouts", lang, F(T("Payouts and expenses for {F} accounts, sample data","Payouts et dépenses des comptes {F}, données d’exemple","Payouts y gastos de cuentas de {F}, datos de ejemplo")), t), flip=True, id_="payouts")
        from pages7 import TOOLS
        tools = "".join(f'<a class="tool-mini" href="{href(lang,s)}">{ico(I[ic])}<span>{t(n)}</span></a>' for s,ic,n,_ in TOOLS)
        b += f'<section class="rule"><div class="wrap"><div class="head"><span class="kick">{t(T("Free tools","Outils gratuits","Herramientas gratuitas"))}</span><h2>{t(T("Check a number before the open.","Vérifie un chiffre avant l’ouverture.","Comprueba una cifra antes de la apertura."))}</h2></div><div class="tool-row">{tools}</div></div></section>'
        faqs = [(_f(T("Is Sweep affiliated with {F}?","Sweep est-il affilié à {F} ?","¿Sweep está afiliado a {F}?"),firm),
                 _f(T("No. Sweep is independent and isn’t affiliated with, endorsed by or connected to {F}. The {F} name belongs to its owner.","Non. Sweep est indépendant et n’est ni affilié à {F}, ni approuvé par {F}. Le nom {F} appartient à son propriétaire.","No. Sweep es independiente y no está afiliado, respaldado ni vinculado a {F}. El nombre {F} pertenece a su propietario."),firm)),
                (_f(T("Are the {F} rules in Sweep always up to date?","Les règles {F} dans Sweep sont-elles toujours à jour ?","¿Las reglas de {F} en Sweep están siempre actualizadas?"),firm),
                 _f(T("{F}’s rules aren’t preloaded in Sweep yet: you enter them yourself and can edit them anytime. Firms change their rules, so always check the current ones on {F}’s site.",
                      "Les règles de {F} ne sont pas encore préremplies dans Sweep : tu les saisis toi-même et tu peux les modifier à tout moment. Les firmes changent leurs règles : vérifie toujours les règles actuelles sur le site de {F}.",
                      "Las reglas de {F} aún no están precargadas en Sweep: las introduces tú y puedes editarlas cuando quieras. Las firmas cambian sus reglas: verifica siempre las actuales en el sitio de {F}."),firm) if not has else
                 _f(T("The preset is prefilled for guidance and every value can be edited. Firms change their rules, so always check the current rules on {F}’s site.","Le préréglage est prérempli à titre indicatif et chaque valeur est modifiable. Les firmes changent leurs règles : vérifie toujours les règles actuelles sur le site de {F}.","El preajuste está precargado a título indicativo y cada valor es editable. Las firmas cambian sus reglas: verifica siempre las reglas actuales en el sitio de {F}."),firm)),
                (_f(T("Can I track several {F} accounts?","Puis-je suivre plusieurs comptes {F} ?","¿Puedo seguir varias cuentas de {F}?"),firm),
                 T("Yes, as many as your plan allows, each with its own rules, and you can copy one trade to several accounts at once.","Oui, autant que ton forfait le permet, chacun avec ses propres règles, et tu peux copier un trade sur plusieurs comptes en une fois.","Sí, tantas como permita tu plan, cada una con sus propias reglas, y puedes copiar una operación en varias cuentas a la vez.")),
                (T("Is it free?","C’est gratuit ?","¿Es gratis?"), T("Yes. Sweep is free forever, with Pro included for your first 60 days. No credit card.","Oui. Sweep est gratuit pour toujours, avec Pro offert pendant tes 60 premiers jours. Sans carte de crédit.","Sí. Sweep es gratis para siempre, con Pro incluido tus primeros 60 días. Sin tarjeta."))]
        b += f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>{"".join(faq_item(t,q,a) for q,a in faqs)}</div></section>'
        others = "".join(f'<a href="{href(lang,s)}">{n}</a>' for s,n in FIRMS if s != slug)
        b += f'<section class="rule"><div class="wrap"><p class="firm-others"><span>{t(T("Also for","Aussi pour","También para"))}</span>{others}<a href="{href(lang,"prop-traders.html")}">{t(T("All prop traders","Tous les traders prop","Todos los traders prop"))} →</a></p></div></section>'
        ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in faqs]})
        return (F(T("{F} trading journal: rules and payouts · Sweep","Journal de trading {F} : règles et payouts · Sweep","Diario de trading para {F} · Sweep")) if len(firm) < 14 else F(T("{F} trading journal · Sweep","Journal de trading {F} · Sweep","Diario de trading para {F} · Sweep")),
                F(T("Track your {F} accounts in one place: profit target, drawdown, daily loss, consistency and payouts. Enter your rules once. Free forever.",
                    "Suis tes comptes {F} au même endroit : objectif, drawdown, perte quotidienne, consistance et payouts. Saisis tes règles une fois. Gratuit pour toujours.",
                    "Sigue tus cuentas de {F} en un solo lugar: objetivo, drawdown, pérdida diaria, consistencia y payouts. Introduce tus reglas una vez. Gratis para siempre.")) if not has else
                F(T("Track your {F} accounts in one place: profit target, drawdown, daily loss, consistency and payouts. Rules prefilled for guidance. Free forever.",
                    "Suis tes comptes {F} au même endroit : objectif, drawdown, perte quotidienne, consistance et payouts. Règles préremplies à titre indicatif. Gratuit pour toujours.",
                    "Sigue tus cuentas de {F} en un solo lugar: objetivo, drawdown, pérdida diaria, consistencia y payouts. Reglas precargadas a título indicativo. Gratis para siempre.")),
                hero + b + final_cta(lang, t), ld)
    return page

def firm_row(lang, t):
    links = "".join(f'<a href="{href(lang,s)}">{n}</a>' for s,n in FIRMS)
    return (f'<section class="rule" style="padding:40px 0"><div class="wrap"><p class="firm-others"><span>{t(T("By firm","Par firme","Por firma"))}</span>{links}'
            f'<a href="{href(lang,"prop-firms/index.html")}">{t(T("Rules by firm","Règles par firme","Reglas por firma"))} →</a>'
            f'<a href="{href(lang,"tools.html")}">{t(T("Free calculators","Calculateurs gratuits","Calculadoras gratuitas"))} →</a></p></div></section>')

def rule_change(lang, t):
    return (f'<section class="rule" id="rule-changes"><div class="wrap narrow" style="text-align:center"><div class="head" style="margin:0 auto"><span class="kick">{t(T("Rule changes","Changements de règles","Cambios de reglas"))}</span>'
            f'<h2>{t(T("Rules change. You stay informed.","Les règles changent. Tu restes informé.","Las reglas cambian. Tú sigues informado."))}</h2>'
            f'<p class="lead" style="margin-left:auto;margin-right:auto">{t(T("We check every firm’s official pages weekly. When a rule changes, you see what it means for your account and choose to apply it or keep yours.","On vérifie les pages officielles de chaque firme chaque semaine. Quand une règle change, tu vois ce que ça change pour ton compte et tu choisis de l’appliquer ou de garder la tienne.","Revisamos cada semana las páginas oficiales de cada firma. Cuando una regla cambia, ves qué significa para tu cuenta y eliges aplicarla o mantener la tuya."))}</p></div>'
            f'<p class="fine" style="margin-top:22px">{t(T("Rules are shown for information. Always confirm on your firm’s official site. Firm names belong to their owners; Sweep is independent.","Les règles sont présentées à titre indicatif ; confirme toujours sur le site officiel de ta firme. Les noms appartiennent à leurs propriétaires ; Sweep est indépendant.","Las reglas se muestran a título informativo; confirma siempre en el sitio oficial de tu firma. Los nombres pertenecen a sus propietarios; Sweep es independiente."))}</p></div></section>')
