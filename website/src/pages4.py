from core import *

PRICES = {"pro": {"m": 19, "y": 159}, "elite": {"m": 39, "y": 329}}
TAX = T("+ applicable taxes","Taxes applicables en sus","Impuestos aplicables no incluidos")
TRIAL = T("Pro free for 14 days, no card needed","Pro gratuit 14 jours, sans carte","Pro gratis 14 días, sin tarjeta")
START = T("Start free","Commencer gratuitement","Empezar gratis")
TRIAL_BTN = T("Start 14-day Pro trial","Essai Pro de 14 jours","Prueba Pro de 14 días")
ELITE_BTN = T("Choose Elite","Choisir Elite","Elegir Elite")

def share_img(name, alt, w, h, sizes="(max-width: 860px) 64vw, 340px"):
    return (f'<img src="/img/{name}-540.webp" srcset="/img/{name}-540.webp 540w, /img/{name}-1080.webp 1080w" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{html.escape(alt)}" loading="lazy" decoding="async">')

def plan_tag(p):  # small label for plan-gated features
    return f' <span class="plan-tag {p.lower()}">{p}</span>'

PLAN_FAQ = [
 (T("Is Sweep free?","Sweep est-il gratuit?","¿Sweep es gratis?"),
  T("Yes, there’s a Free plan: 1 trading account, unlimited trades, the last 30 days of analytics, and 5 Sweep AI messages a day. New accounts also get Pro free for 14 days, no card needed.",
    "Oui, il y a un forfait Free : 1 compte de trading, trades illimités, les 30 derniers jours d’analyses et 5 messages Sweep AI par jour. Les nouveaux comptes ont aussi Pro gratuit pendant 14 jours, sans carte.",
    "Sí, hay un plan Free: 1 cuenta de trading, operaciones ilimitadas, los últimos 30 días de análisis y 5 mensajes de Sweep AI al día. Las cuentas nuevas también tienen Pro gratis durante 14 días, sin tarjeta.")),
 (T("What’s the difference between Pro and Elite?","Quelle est la différence entre Pro et Elite?","¿Qué diferencia hay entre Pro y Elite?"),
  T("Pro unlocks unlimited accounts, your full history, payouts and expenses, and AI import. Elite adds full economic market reports, a weekly AI review of your trading, unlimited AI trade reviews (fair use) and priority support.",
    "Pro débloque les comptes illimités, tout ton historique, les payouts et dépenses, et l’import IA. Elite ajoute les rapports de marché économiques complets, un bilan hebdo IA de ton trading, les avis IA illimités sur tes trades (usage raisonnable) et le soutien prioritaire.",
    "Pro desbloquea cuentas ilimitadas, todo tu historial, payouts y gastos, e importación con IA. Elite añade los informes de mercado completos, una revisión semanal con IA, opiniones de IA ilimitadas sobre tus operaciones (uso razonable) y soporte prioritario.")),
 (T("What happens if I cancel or downgrade?","Qu’arrive-t-il si j’annule ou change de forfait?","¿Qué pasa si cancelo o bajo de plan?"),
  T("You keep access until the end of your paid period. Then nothing is deleted: extra accounts are paused (read-only), older analytics stay saved, and you choose which account stays active.",
    "Tu gardes l’accès jusqu’à la fin de ta période payée. Ensuite, rien n’est supprimé : les comptes en trop sont mis en pause (lecture seule), les anciennes analyses restent sauvegardées, et tu choisis le compte qui reste actif.",
    "Conservas el acceso hasta el final del periodo pagado. Después no se elimina nada: las cuentas adicionales quedan en pausa (solo lectura), los análisis antiguos se guardan y tú eliges qué cuenta queda activa.")),
 (T("Do you offer refunds?","Offrez-vous des remboursements?","¿Ofrecen reembolsos?"),
  T("No. Payments are non-refundable, but you can cancel anytime and keep access until the end of the period you paid for.",
    "Non. Les paiements ne sont pas remboursables, mais tu peux annuler en tout temps et garder l’accès jusqu’à la fin de la période payée.",
    "No. Los pagos no son reembolsables, pero puedes cancelar cuando quieras y mantener el acceso hasta el final del periodo pagado.")),
 (T("Are taxes included?","Les taxes sont-elles incluses?","¿Los impuestos están incluidos?"),
  T("No. Prices are shown in USD before tax; applicable taxes are added at checkout based on your billing address.",
    "Non. Les prix sont affichés en dollars américains avant taxes; les taxes applicables sont ajoutées au paiement selon ton adresse de facturation.",
    "No. Los precios se muestran en USD antes de impuestos; los impuestos aplicables se añaden al pagar según tu dirección de facturación.")),
 (T("Can I switch between monthly and yearly, or between Pro and Elite?","Puis-je passer du mensuel à l’annuel, ou de Pro à Elite?","¿Puedo cambiar entre mensual y anual, o entre Pro y Elite?"),
  T("Yes, anytime from Settings → Plan → Manage billing.","Oui, en tout temps dans Réglages → Forfait → Gérer la facturation.","Sí, cuando quieras desde Ajustes → Plan → Gestionar facturación.")),
 (T("How do payments work?","Comment fonctionnent les paiements?","¿Cómo funcionan los pagos?"),
  T("Securely through Stripe, by card. Sweep never sees or stores your card number. Upgrades happen inside the app after you sign up.",
    "De façon sécurisée avec Stripe, par carte. Sweep ne voit ni ne conserve jamais ton numéro de carte. Les mises à niveau se font dans l’app après l’inscription.",
    "De forma segura con Stripe, con tarjeta. Sweep nunca ve ni guarda tu número de tarjeta. Las mejoras de plan se hacen dentro de la app tras registrarte.")),
 (T("What is the founding price?","Qu’est-ce que le prix fondateur?","¿Qué es el precio fundador?"),
  T("Members who joined during early access (before October 2, 2026) can lock in 50% off for life, until December 1, 2026. “For life” means for as long as that subscription stays active.",
    "Les membres inscrits pendant l’accès anticipé (avant le 2 octobre 2026) peuvent obtenir 50 % de rabais à vie, jusqu’au 1er décembre 2026. « À vie » veut dire tant que cet abonnement reste actif.",
    "Quienes se unieron durante el acceso anticipado (antes del 2 de octubre de 2026) pueden asegurar un 50 % de descuento de por vida, hasta el 1 de diciembre de 2026. «De por vida» significa mientras esa suscripción siga activa.")),
]
SHARE_FAQ = (T("Can I share my payouts?","Puis-je partager mes payouts?","¿Puedo compartir mis payouts?"),
  T("Yes. Sweep makes branded share cards for payouts, weekly recaps, net after fees, days and trades, and you can hide amounts or the prop firm. Images are made on your device.",
    "Oui. Sweep crée des cartes à partager à son image pour les payouts, les récaps de la semaine, le net après frais, les journées et les trades, et tu peux masquer les montants ou la prop firm. Les images sont créées sur ton appareil.",
    "Sí. Sweep crea tarjetas con su marca para payouts, resúmenes semanales, neto tras comisiones, días y operaciones, y puedes ocultar los importes o la prop firm. Las imágenes se crean en tu dispositivo."))
SYNC_FAQ = (T("Does Sweep sync between my phone and computer?","Sweep se synchronise-t-il entre mon téléphone et mon ordi?","¿Sweep se sincroniza entre mi teléfono y mi ordenador?"),
  T("Yes. Changes appear when you come back to the app on the other device, every minute while it’s open, or when you pull down to refresh on your phone.",
    "Oui. Les changements apparaissent quand tu reviens dans l’app sur l’autre appareil, chaque minute pendant qu’elle est ouverte, ou quand tu tires vers le bas pour actualiser sur ton téléphone.",
    "Sí. Los cambios aparecen al volver a la app en el otro dispositivo, cada minuto mientras está abierta, o al deslizar hacia abajo para actualizar en el teléfono."))

TRUST = T("Prices in USD, before applicable taxes. Cancel anytime. No refunds for periods already paid. Your data is never deleted. Secure payments by Stripe.",
          "Prix en dollars américains, avant les taxes applicables. Annule en tout temps. Aucun remboursement pour les périodes déjà payées. Tes données ne sont jamais supprimées. Paiements sécurisés par Stripe.",
          "Precios en USD, antes de los impuestos aplicables. Cancela cuando quieras. Sin reembolsos por periodos ya pagados. Tus datos nunca se eliminan. Pagos seguros con Stripe.")

def money(t, v):
    L = t(T("en","fr","es"))
    txt = f"{v:.2f}" if isinstance(v, float) and v != int(v) else f"{int(v)}"
    return f"${txt}" if L == "en" else txt.replace(".", ",") + " $"

def price_block(t, plan):
    if plan == "free":
        return '<div class="price"><span class="num">' + money(t,0) + '</span></div><p class="per muted">' + t(T("forever, with limits","pour toujours, avec limites","para siempre, con límites")) + '</p>'
    m, y = PRICES[plan]["m"], PRICES[plan]["y"]
    ym = money(t, round(y/12, 2)); mm = money(t, m)
    return (f'<div class="price"><span class="num" data-m="{mm}" data-y="{ym}">{ym}</span><span class="muted">/{t(T("mo","mois","mes"))}</span></div>'
            f'<p class="per muted" data-m="{t(T("billed monthly","facturé chaque mois","facturado mensualmente"))}" data-y="{t(T(f"billed ${y} yearly",f"facturé {y} $ par année",f"facturado {y} $ al año"))}">{t(T(f"billed ${y} yearly",f"facturé {y} $ par année",f"facturado {y} $ al año"))}</p>')

def plan_cards(lang, t):
    free = [T("1 trading account","1 compte de trading","1 cuenta de trading"),T("Unlimited trades and journal","Trades et journal illimités","Operaciones y diario ilimitados"),
            T("Last 30 days of analytics","30 derniers jours d’analyses","Últimos 30 días de análisis"),T("5 Sweep AI messages a day","5 messages Sweep AI par jour","5 mensajes de Sweep AI al día"),
            T("1 AI trade review a month","1 avis IA sur un trade par mois","1 opinión de IA al mes"),T("Economic calendar, share cards, rule checks","Calendrier économique, cartes à partager, vérification des règles","Calendario económico, tarjetas para compartir, revisión de reglas")]
    pro = [T("Everything in Free, plus:","Tout Free, plus :","Todo lo de Free, más:"),T("Unlimited trading accounts","Comptes de trading illimités","Cuentas de trading ilimitadas"),T("Your full analytics history","Tout ton historique d’analyses","Todo tu historial de análisis"),
           T("Payouts and expenses tracking","Suivi des payouts et dépenses","Seguimiento de payouts y gastos"),T("AI import: screenshots, statements, receipts","Import IA : captures, relevés, reçus","Importación con IA: capturas, extractos, recibos"),
           T("40 Sweep AI messages a day","40 messages Sweep AI par jour","40 mensajes de Sweep AI al día"),T("3 AI trade reviews a month","3 avis IA sur des trades par mois","3 opiniones de IA al mes")]
    elite = [T("Everything in Pro, plus:","Tout Pro, plus :","Todo lo de Pro, más:"),T("Full economic market reports","Rapports de marché économiques complets","Informes de mercado económicos completos"),
             T("Weekly AI review of your trading","Bilan hebdo IA de ton trading","Revisión semanal con IA de tu trading"),T("Unlimited AI trade reviews (fair use)","Avis IA illimités sur tes trades (usage raisonnable)","Opiniones de IA ilimitadas (uso razonable)"),
             T("150 Sweep AI messages a day","150 messages Sweep AI par jour","150 mensajes de Sweep AI al día"),T("Priority support","Soutien prioritaire","Soporte prioritario")]
    def card(name, tag, tagline, block, feats, btn, cls, badge=""):
        link = f"{SIGNUP}&plan={tag}" + ("" if tag == "free" else "&interval=year")
        return f'''<div class="plan {cls} reveal">{badge}<h2>{name}</h2><p class="tagline">{t(tagline)}</p>{block}{ul(t,feats)}<a class="btn {"btn-primary" if cls=="main" else "btn-line"} btn-lg" href="{link}" data-plan="{tag}">{t(btn)}</a></div>'''
    return f'''<div class="billing" data-k="y" role="group" aria-label="{t(T("Billing period","Période de facturation","Periodo de facturación"))}">
<button type="button" data-bill="m" aria-pressed="false">{t(T("Monthly","Mensuel","Mensual"))}</button><button type="button" data-bill="y" aria-pressed="true">{t(T("Yearly","Annuel","Anual"))} <span class="save">{t(T("Save ~30%","Économise ~30 %","Ahorra ~30 %"))}</span></button></div>
<div class="plans three" id="plans">
{card("Free","free",T("Journal and core dashboard.","Journal et tableau de bord de base.","Diario y panel principal."),price_block(t,"free"),free,START,"")}
{card("Pro","pro",T("Every account, your full history, payouts and AI import.","Tous tes comptes, tout ton historique, les payouts et l’import IA.","Todas tus cuentas, todo tu historial, payouts e importación con IA."),price_block(t,"pro"),pro,TRIAL_BTN,"main",f'<span class="badge">{t(T("Most popular","Le plus populaire","El más popular"))}</span>')}
{card("Elite","elite",T("Full market reports, weekly AI review, unlimited AI trade reviews.","Rapports de marché complets, bilan hebdo IA, avis IA illimités sur tes trades.","Informes de mercado completos, revisión semanal con IA, opiniones de IA ilimitadas."),price_block(t,"elite"),elite,ELITE_BTN,"")}
</div>
<div class="dots plan-dots" aria-hidden="true"><i></i><i></i><i></i></div>
<p class="trustline">{t(TRUST)}</p>'''

def comparison(t):
    Y = '<span class="yes" aria-label="✓">✓</span>'; N = '<span class="no" aria-label="—">—</span>'
    rows = [(T("Trading accounts","Comptes de trading","Cuentas de trading"),"1",t(T("Unlimited","Illimités","Ilimitadas")),t(T("Unlimited","Illimités","Ilimitadas"))),
            (T("Manual trades and journal","Trades manuels et journal","Operaciones manuales y diario"),t(T("Unlimited","Illimités","Ilimitados")),t(T("Unlimited","Illimités","Ilimitados")),t(T("Unlimited","Illimités","Ilimitados"))),
            (T("Analytics history","Historique des analyses","Historial de análisis"),t(T("Last 30 days","30 derniers jours","Últimos 30 días")),t(T("Full history","Complet","Completo")),t(T("Full history","Complet","Completo"))),
            (T("Payouts and expenses","Payouts et dépenses","Payouts y gastos"),N,Y,Y),
            (T("Sweep AI messages (chat, log with AI, debriefs, tags)","Messages Sweep AI (discussion, saisie IA, débriefs, tags)","Mensajes de Sweep AI (chat, registro con IA, resúmenes, etiquetas)"),t(T("5 a day","5 par jour","5 al día")),t(T("40 a day","40 par jour","40 al día")),t(T("150 a day","150 par jour","150 al día"))),
            (T("AI import (screenshots, statements, receipts)","Import IA (captures, relevés, reçus)","Importación con IA (capturas, extractos, recibos)"),N,Y,Y),
            (T("AI trade reviews","Avis IA sur les trades","Opiniones de IA sobre operaciones"),t(T("1 a month","1 par mois","1 al mes")),t(T("3 a month","3 par mois","3 al mes")),t(T("Unlimited (fair use)","Illimités (usage raisonnable)","Ilimitadas (uso razonable)"))),
            (T("Economic market reports","Rapports de marché économiques","Informes de mercado económicos"),t(T("Headline + first sentence","Titre + première phrase","Titular + primera frase")),t(T("Headline + first sentence","Titre + première phrase","Titular + primera frase")),t(T("Full reports","Rapports complets","Informes completos"))),
            (T("Weekly AI review","Bilan hebdo IA","Revisión semanal con IA"),N,N,Y),
            (T("Priority support","Soutien prioritaire","Soporte prioritario"),N,N,Y)]
    every = [T("Economic calendar with auto-filled numbers","Calendrier économique avec chiffres remplis","Calendario económico con cifras completadas"),T("Ask Sweep, within your AI message limit","Ask Sweep, dans ta limite de messages IA","Ask Sweep, dentro de tu límite de mensajes"),
             T("Share cards","Cartes à partager","Tarjetas para compartir"),T("Discipline checklist and automatic rule checks","Checklist de discipline et vérification automatique des règles","Checklist de disciplina y revisión automática de reglas"),
             T("Sync across devices, English, French and Spanish","Synchronisation entre appareils, anglais, français et espagnol","Sincronización entre dispositivos, inglés, francés y español"),T("Export and delete your data","Export et suppression de tes données","Exportar y eliminar tus datos")]
    body = "".join(f"<tr><th scope=\"row\">{t(a)}</th><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a,b,c,d in rows)
    return f'''<div class="cmp-wrap"><table class="cmp"><thead><tr><th scope="col"><span class="sr">{t(T("Feature","Fonctionnalité","Función"))}</span></th><th scope="col">Free</th><th scope="col" class="hl">Pro</th><th scope="col">Elite</th></tr></thead><tbody>{body}</tbody></table></div>
<div class="head" style="margin:48px 0 16px"><h3>{t(T("Included on every plan","Inclus dans tous les forfaits","Incluido en todos los planes"))}</h3></div>{ul(t,every,"list cols")}'''

def page_pricing(lang, t):
    hero = f'<div class="page-hero" style="text-align:center"><div class="wrap"><span class="kick">{t(T("Pricing","Tarifs","Precios"))}</span><h1 class="wu" style="margin:0 auto;max-width:22ch">{words(t(T("Start free. Upgrade when your trading grows.","Commence gratuitement. Passe au niveau supérieur quand ton trading grandit.","Empieza gratis. Mejora cuando tu trading crezca.")))}</h1><p class="lead rise d3" style="margin-left:auto;margin-right:auto">{t(T("A Free plan to journal and review, with Pro free for 14 days, no card needed. Upgrade inside the app whenever you want more.","Un forfait Free pour tenir ton journal et réviser, avec Pro gratuit pendant 14 jours, sans carte. Passe au niveau supérieur dans l’app quand tu veux plus.","Un plan Free para llevar tu diario y revisar, con Pro gratis durante 14 días, sin tarjeta. Mejora dentro de la app cuando quieras más."))}</p></div></div>'
    b = f'<section style="padding-top:8px"><div class="wrap">{plan_cards(lang,t)}</div></section>'
    stat = lambda big, small: f'<div><span class="num">{t(big)}</span><span>{t(small)}</span></div>'
    early = f'''<div class="early reveal"><div class="early-copy"><span class="kick">{t(T("Early-access members","Membres de l’accès anticipé","Miembros del acceso anticipado"))}</span>
<h3>{t(T("Thank you for being early. Here’s your founding price.","Merci d’être arrivé tôt. Voici ton prix fondateur.","Gracias por llegar pronto. Este es tu precio fundador."))}</h3>
<p>{t(T("For accounts created before October 2, 2026. The offer appears in the app under Settings → Plan.","Pour les comptes créés avant le 2 octobre 2026. L’offre apparaît dans l’app sous Réglages → Forfait.","Para cuentas creadas antes del 2 de octubre de 2026. La oferta aparece en la app en Ajustes → Plan."))}</p></div>
<div class="early-stats">{stat(T("30 days","30 jours","30 días"),T("of Pro free from launch","de Pro gratuit dès le lancement","de Pro gratis desde el lanzamiento"))}{stat(T("50% off","−50 %","−50 %"),T("for life, while you stay subscribed","à vie, tant que tu restes abonné","de por vida, mientras sigas suscrito"))}{stat(T("Dec 1","1er déc.","1 dic."),T("last day to lock it in","dernier jour pour en profiter","último día para asegurarlo"))}</div></div>'''

    b += f'<section class="rule"><div class="wrap"><div class="head"><h2>{t(T("Compare plans","Compare les forfaits","Compara los planes"))}</h2></div>{comparison(t)}{early}</div></section>'
    b += f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Pricing questions","Questions sur les tarifs","Preguntas sobre precios"))}</h2></div>{"".join(faq_item(t,q,a) for q,a in PLAN_FAQ)}</div></section>'
    offers = [{"@type":"Offer","name":n,"price":str(p),"priceCurrency":"USD"} for n,p in (("Free",0),("Pro monthly",19),("Pro yearly",159),("Elite monthly",39),("Elite yearly",329))]
    ld = jsonld({"@context":"https://schema.org","@graph":[{"@type":"Product","name":"Sweep","description":t(T("Trading journal and performance system for futures traders.","Journal de trading et système de performance pour traders de futures.","Diario de trading y sistema de rendimiento para traders de futuros.")),"brand":{"@type":"Brand","name":"Sweep"},"offers":offers},
          {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in PLAN_FAQ]}]})
    return (t(T("Pricing · Free, Pro and Elite plans · Sweep","Tarifs · Forfaits Free, Pro et Elite · Sweep","Precios · Planes Free, Pro y Elite · Sweep")),
            t(T("Start free with 1 account and unlimited trades. Pro ($19/mo or $159/yr) adds unlimited accounts, full history, payouts and AI import. Elite ($39/mo) adds full market reports and weekly AI reviews. Pro free for 14 days.",
                "Commence gratuitement avec 1 compte et des trades illimités. Pro (19 $/mois ou 159 $/an) ajoute les comptes illimités, tout l’historique, les payouts et l’import IA. Elite (39 $/mois) ajoute les rapports de marché complets et le bilan hebdo IA. Pro gratuit 14 jours.",
                "Empieza gratis con 1 cuenta y operaciones ilimitadas. Pro (19 $/mes o 159 $/año) añade cuentas ilimitadas, historial completo, payouts e importación con IA. Elite (39 $/mes) añade informes de mercado completos y revisiones semanales con IA. Pro gratis 14 días.")),
            hero + b + final_cta(lang, t), ld)

def plans_band(lang, t):
    tile = lambda n, price, line: f'<a class="ptile" href="{href(lang,"pricing.html")}"><span class="n">{n}</span><span class="p num">{price}</span><span class="l">{t(line)}</span></a>'
    return f'''<section class="rule"><div class="wrap"><div class="vip reveal"><div class="inner">
<div><span class="kick">{t(T("Plans","Forfaits","Planes"))}</span><h2>{t(T("Free forever. Pro included for 60 days.","Gratuit pour toujours. Pro offert pendant 60 jours.","Gratis para siempre. Pro incluido durante 60 días."))}</h2>
<p class="lead">{t(T("No credit card to start. Cancel anytime. Elite is a paid upgrade.","Sans carte de crédit pour commencer. Annule quand tu veux. Elite reste une montée en gamme payante.","Sin tarjeta para empezar. Cancela cuando quieras. Elite es una mejora de pago."))}</p>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(T("Start for free","Commencer gratuitement","Empieza gratis"))}</a><a class="btn btn-line btn-lg" href="{href(lang,'pricing.html')}">{t(T("Compare plans","Comparer les forfaits","Comparar planes"))}</a></div></div>
<div class="ptiles">{tile("Free",money(t,0),T("forever · journal, real charts, rings","pour toujours · journal, vrais graphiques, anneaux","para siempre · diario, gráficos reales, anillos"))}{tile("Pro",money(t,19),T("/mo or $159/yr (save 30%) · 60 days included","/mois ou 159 $/an (−30 %) · 60 jours offerts","/mes o 159 $/año (−30 %) · 60 días incluidos"))}{tile("Elite",money(t,39),T("/mo or $329/yr (save 30%) · the most accounts and AI","/mois ou 329 $/an (−30 %) · le plus de comptes et d’IA","/mes o 329 $/año (−30 %) · el máximo de cuentas e IA"))}</div>
</div><p class="meta" style="margin-top:20px">{t(T("Prices in USD, before taxes.","Prix en USD, avant taxes.","Precios en USD, antes de impuestos."))}</p></div></div></section>'''

def share_band(lang, t, more=True):
    a = t(T("Share card example, sample data","Exemple de carte à partager, données d’exemple","Ejemplo de tarjeta para compartir, datos de ejemplo"))
    m = f'<div class="cta-row" style="justify-content:center"><a class="btn btn-line" href="{href(lang,"features.html")}#share-cards">{t(T("How sharing works","Comment fonctionne le partage","Cómo funciona compartir"))}</a></div>' if more else ""
    return f'''<section class="rule center share-band"><div class="wrap">
<div class="head center"><span class="kick">{t(T("Share cards","Cartes à partager","Tarjetas para compartir"))}</span><h2>{t(T("Your payouts, beautifully shared.","Tes payouts, partagés avec style.","Tus payouts, compartidos con estilo."))}</h2>
<p class="lead">{t(T("Turn a payout, a green week or your net after fees into a branded card for Instagram, X or Discord. Amounts are optional, and the image is made on your phone.","Transforme un payout, une semaine verte ou ton net après frais en carte à ton image pour Instagram, X ou Discord. Les montants sont optionnels, et l’image est créée sur ton téléphone.","Convierte un payout, una semana en verde o tu neto tras comisiones en una tarjeta con marca para Instagram, X o Discord. Los importes son opcionales y la imagen se crea en tu teléfono."))}</p></div>
<div class="cards-fan rail stagger">
<figure class="scard">{share_img("share-payout",a,1080,1350)}</figure>
<figure class="scard tall">{share_img("share-net",a,1080,1920)}</figure>
<figure class="scard">{share_img("share-weekly",a,1080,1350)}</figure>
</div>
<p class="cap">{t(T("Examples made from sample data, stamped “Sample data” by the app.","Exemples créés avec des données d’exemple, marqués « Sample data » par l’app.","Ejemplos creados con datos de ejemplo, marcados «Sample data» por la app."))}</p>{m}
</div></section>'''
