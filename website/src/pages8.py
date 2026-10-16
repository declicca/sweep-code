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
    """One line of chips (it scrolls on phones): each firm's rules, then the rules side by side and the calculators."""
    links = "".join(f'<a class="chip" href="{href(lang,s)}">{n}</a>' for s,n in FIRMS)
    return (f'<section class="s-t"><div class="c"><div class="chiprow"><span class="eyebrow">{t(T("By firm","Par firme","Por firma"))}</span>{links}'
            f'<a class="go" href="{href(lang,"prop-firms/index.html")}">{t(T("Rules by firm","Règles par firme","Reglas por firma"))} <span aria-hidden="true">→</span></a>'
            f'<a class="go" href="{href(lang,"tools.html")}">{t(T("Free calculators","Calculateurs gratuits","Calculadoras gratuitas"))} <span aria-hidden="true">→</span></a></div></div></section>')

