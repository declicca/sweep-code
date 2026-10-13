from core import *

# One page per firm (audit of Oct 13): its rules and how to track it in Sweep, at /prop-firms/<firm>.
# The old journal pages (/<firm>-trading-journal) redirect there (JOURNAL_MOVED, .htaccess).
FIRMS = [("prop-firms/topstep.html","Topstep"),("prop-firms/apex.html","Apex Trader Funding"),
         ("prop-firms/take-profit-trader.html","Take Profit Trader"),("prop-firms/lucid.html","Lucid Trading"),
         ("prop-firms/myfundedfutures.html","MyFundedFutures"),
         ("prop-firms/tradeify.html","Tradeify"),("prop-firms/alpha-futures.html","Alpha Futures")]
JOURNAL_MOVED = {"topstep-trading-journal": "prop-firms/topstep", "apex-trader-funding-journal": "prop-firms/apex", "take-profit-trader-journal": "prop-firms/take-profit-trader",
                 "lucid-trading-journal": "prop-firms/lucid", "myfundedfutures-journal": "prop-firms/myfundedfutures", "tradeify-trading-journal": "prop-firms/tradeify",
                 "alpha-futures-trading-journal": "prop-firms/alpha-futures"}

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
