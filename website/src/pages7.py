from core import *
import json as _json

# CME contract specs used by the calculators: (symbol, name, tick size, tick value $)
SPECS = [("NQ","E-mini Nasdaq-100",0.25,5.0),("MNQ","Micro E-mini Nasdaq-100",0.25,0.5),("ES","E-mini S&P 500",0.25,12.5),("MES","Micro E-mini S&P 500",0.25,1.25),
         ("YM","E-mini Dow",1.0,5.0),("MYM","Micro E-mini Dow",1.0,0.5),("RTY","E-mini Russell 2000",0.1,5.0),("M2K","Micro E-mini Russell 2000",0.1,0.5),
         ("CL","Crude Oil",0.01,10.0),("MCL","Micro Crude Oil",0.01,1.0),("GC","Gold",0.1,10.0),("MGC","Micro Gold",0.1,1.0),
         ("SI","Silver",0.005,25.0),("6E","Euro FX",0.00005,6.25)]

TOOLS = [
 ("position-size-calculator.html","calc",T("Position size calculator","Calculateur de taille de position","Calculadora de tamaño de posición"),
  T("How many contracts can you trade for the risk you accept? Pick the instrument, enter your stop.","Combien de contrats pour le risque que tu acceptes ? Choisis l’instrument, entre ton stop.","¿Cuántos contratos para el riesgo que aceptas? Elige el instrumento e introduce tu stop.")),
 ("trailing-drawdown-calculator.html","shield",T("Trailing drawdown calculator","Calculateur de drawdown suiveur","Calculadora de drawdown dinámico"),
  T("Where is your liquidation level today, and how much room is left before it?","Où est ton seuil de liquidation aujourd’hui, et combien de marge te reste-t-il ?","¿Dónde está hoy tu nivel de liquidación y cuánto margen te queda?")),
 ("consistency-rule-calculator.html","layers",T("Consistency rule calculator","Calculateur de règle de consistance","Calculadora de regla de consistencia"),
  T("Is your best day too big a share of your profit? See how much more you need.","Ta meilleure journée pèse-t-elle trop dans ton profit ? Vois combien il te manque.","¿Tu mejor día pesa demasiado en tu beneficio? Mira cuánto te falta.")),
]
NOTE = T("For guidance only. Every prop firm has its own rules, and they change: always check your firm’s current rules. Not financial advice.",
         "À titre indicatif seulement. Chaque prop firm a ses propres règles, et elles changent : vérifie toujours les règles actuelles de ta firme. Ce n’est pas un conseil financier.",
         "Solo a título indicativo. Cada prop firm tiene sus propias reglas y cambian: verifica siempre las reglas actuales de tu firma. No es asesoramiento financiero.")

def _tool_page(lang, t, slug, h1, lead, form, results, script, howto, faqs):
    hero = page_hero(t, h1, lead, T("Free tools","Outils gratuits","Herramientas gratuitas"))
    others = "".join(f'<a class="tool-mini" href="{href(lang,s)}">{ico(I[ic])}<span>{t(n)}</span></a>' for s,ic,n,_ in TOOLS if s != slug)
    b = f'''<section style="padding-top:8px"><div class="wrap"><div class="calc" data-calc="{slug}">
<div class="calc-form">{form}</div><div class="calc-out" aria-live="polite">{results}</div></div>
<p class="fine" style="margin:18px auto 0;text-align:center;max-width:70ch">{t(NOTE)}</p></div></section>
<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("How it works","Comment ça marche","Cómo funciona"))}</h2></div><div class="prose">{t(howto)}</div>
{"".join(faq_item(t,q,a) for q,a in faqs)}</div></section>
<section class="rule"><div class="wrap"><div class="tool-cta"><div><h2>{t(T("Let Sweep track this for you.","Laisse Sweep suivre ça pour toi.","Deja que Sweep lo siga por ti."))}</h2>
<p class="lead">{t(T("Sweep checks your risk on every trade, tracks your drawdown and consistency on every prop account, and tells you when you’re ready for the payout.","Sweep vérifie ton risque à chaque trade, suit ton drawdown et ta consistance sur chaque compte prop, et te dit quand tu es prêt pour le payout.","Sweep revisa tu riesgo en cada operación, sigue tu drawdown y tu consistencia en cada cuenta prop y te dice cuándo estás listo para el payout."))}</p></div>
<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_tool">{t(T("Start for free","Commencer gratuitement","Empieza gratis"))}</a></div>
<div class="tool-others"><span class="kick">{t(T("More free tools","Autres outils gratuits","Más herramientas gratuitas"))}</span><div>{others}</div></div></div></section>'''
    ld = jsonld({"@context":"https://schema.org","@graph":[
        {"@type":"WebApplication","name":t(h1),"url":f"https://{DOMAIN}{href(lang,slug)}","applicationCategory":"FinanceApplication","operatingSystem":"Web","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"publisher":{"@id":f"https://{DOMAIN}/#org"}},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in faqs]}]})
    return hero + b + script, ld

def _num(id_, label, val, step="any", suffix="", attrs=""):
    return f'<label class="fld"><span>{label}</span><span class="inp"><input id="{id_}" type="number" inputmode="decimal" step="{step}" value="{val}" {attrs}>{f"<em>{suffix}</em>" if suffix else ""}</span></label>'

def _sel(id_, label, opts):
    return f'<label class="fld"><span>{label}</span><span class="inp"><select id="{id_}">{opts}</select></span></label>'

def page_position(lang, t):
    opts = "".join(f'<option value="{s}"{" selected" if s=="NQ" else ""}>{s} · {n}</option>' for s,n,_,_ in SPECS)
    form = (_sel("ps-sym", t(T("Instrument","Instrument","Instrumento")), opts)
        + f'<div class="seg" role="radiogroup" aria-label="{t(T("Risk as","Risque en","Riesgo en"))}"><button type="button" data-mode="usd" aria-pressed="true">$</button><button type="button" data-mode="pct" aria-pressed="false">% {t(T("of balance","du solde","del saldo"))}</button></div>'
        + _num("ps-risk", t(T("Risk per trade","Risque par trade","Riesgo por operación")), 200, "any", "$")
        + _num("ps-bal", t(T("Account balance","Solde du compte","Saldo de la cuenta")), 50000, "any", "$", 'data-pct-only')
        + f'<div class="seg" role="radiogroup" aria-label="Stop"><button type="button" data-stop="pts" aria-pressed="true">{t(T("Points","Points","Puntos"))}</button><button type="button" data-stop="ticks" aria-pressed="false">Ticks</button></div>'
        + _num("ps-stop", t(T("Stop distance","Distance du stop","Distancia del stop")), 10, "any"))
    results = (f'<div class="big"><span class="num" id="ps-out">0</span><span>{t(T("contracts","contrats","contratos"))}</span></div>'
        + f'<dl><div><dt>{t(T("Risk per contract","Risque par contrat","Riesgo por contrato"))}</dt><dd class="num" id="ps-rpc">—</dd></div><div><dt>{t(T("Actual risk","Risque réel","Riesgo real"))}</dt><dd class="num" id="ps-act">—</dd></div><div><dt>{t(T("Tick value","Valeur du tick","Valor del tick"))}</dt><dd class="num" id="ps-tv">—</dd></div></dl>'
        + f'<p class="calc-msg" id="ps-msg"></p>')
    msg = {"zero":t(T("Your stop is too wide for this risk: trade a micro, tighten the stop or accept less size.","Ton stop est trop large pour ce risque : passe à un micro, resserre le stop ou réduis la taille.","Tu stop es demasiado amplio para este riesgo: usa un micro, ajusta el stop o reduce el tamaño."))}
    script = f'''<script>(function(){{var S={_json.dumps({s:[ts,tv] for s,_,ts,tv in SPECS})},M={_json.dumps(msg)},mode='usd',stop='pts',$=function(i){{return document.getElementById(i)}};
var money=function(v){{return '$'+v.toLocaleString(undefined,{{maximumFractionDigits:2,minimumFractionDigits:v%1?2:0}})}};
function run(){{var s=S[$('ps-sym').value],ts=s[0],tv=s[1],r=parseFloat($('ps-risk').value)||0,b=parseFloat($('ps-bal').value)||0,d=parseFloat($('ps-stop').value)||0;
var risk=mode==='pct'?b*r/100:r,ticks=stop==='pts'?d/ts:d,rpc=ticks*tv,n=rpc>0?Math.floor(risk/rpc+1e-9):0;
$('ps-out').textContent=n;$('ps-rpc').textContent=rpc>0?money(rpc):'—';$('ps-act').textContent=money(n*rpc);$('ps-tv').textContent=money(tv)+' / '+ts;
$('ps-msg').textContent=(rpc>0&&n===0)?M.zero:'';}}
document.querySelectorAll('[data-calc] input,[data-calc] select').forEach(function(e){{e.addEventListener('input',run)}});
document.querySelectorAll('[data-mode]').forEach(function(b){{b.addEventListener('click',function(){{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});document.querySelector('[data-pct-only]').closest('.fld').hidden=mode!=='pct';document.querySelector('#ps-risk+em').textContent=mode==='pct'?'%':'$';run()}})}});
document.querySelectorAll('[data-stop]').forEach(function(b){{b.addEventListener('click',function(){{stop=b.dataset.stop;document.querySelectorAll('[data-stop]').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});run()}})}});
document.querySelector('[data-pct-only]').closest('.fld').hidden=true;try{{var q=new URLSearchParams(location.search).get('sym');if(q&&S[q.toUpperCase()])$('ps-sym').value=q.toUpperCase();}}catch(e){{}}run();}})();</script>'''
    howto = T("<p>Contracts = risk you accept ÷ risk per contract. The risk per contract is your stop distance in ticks × the instrument’s tick value. For example, a 10-point stop on NQ is 40 ticks × $5 = $200 per contract.</p><p>The result is rounded down, so you never risk more than you planned. If it shows 0, the same stop on the micro contract (MNQ, MES…) is ten times smaller.</p>",
              "<p>Contrats = risque accepté ÷ risque par contrat. Le risque par contrat est la distance du stop en ticks × la valeur du tick de l’instrument. Par exemple, un stop de 10 points sur NQ, c’est 40 ticks × 5 $ = 200 $ par contrat.</p><p>Le résultat est arrondi vers le bas, pour ne jamais risquer plus que prévu. S’il affiche 0, le même stop sur le contrat micro (MNQ, MES…) est dix fois plus petit.</p>",
              "<p>Contratos = riesgo aceptado ÷ riesgo por contrato. El riesgo por contrato es la distancia del stop en ticks × el valor del tick. Por ejemplo, un stop de 10 puntos en NQ son 40 ticks × 5 $ = 200 $ por contrato.</p><p>El resultado se redondea hacia abajo para no arriesgar nunca más de lo previsto. Si muestra 0, el mismo stop en el contrato micro (MNQ, MES…) es diez veces menor.</p>")
    faqs = [(T("What is the tick value of NQ and MNQ?","Quelle est la valeur du tick de NQ et MNQ ?","¿Cuál es el valor del tick de NQ y MNQ?"),
             T("NQ moves in 0.25-point ticks worth $5 each ($20 per point). MNQ is one tenth: $0.50 per tick, $2 per point.","NQ bouge par ticks de 0,25 point valant 5 $ chacun (20 $ par point). MNQ vaut un dixième : 0,50 $ par tick, 2 $ par point.","NQ se mueve en ticks de 0,25 puntos de 5 $ cada uno (20 $ por punto). MNQ es una décima parte: 0,50 $ por tick, 2 $ por punto.")),
            (T("How much should I risk per trade?","Combien devrais-je risquer par trade ?","¿Cuánto debería arriesgar por operación?"),
             T("That’s your decision and depends on your account and its rules. Many traders define it as a fixed dollar amount or a small percentage of the balance, and keep it the same on every trade.","C’est ta décision, selon ton compte et ses règles. Beaucoup de traders la fixent en montant fixe ou en petit pourcentage du solde, et la gardent identique à chaque trade.","Es tu decisión y depende de tu cuenta y sus reglas. Muchos traders la fijan como un importe fijo o un pequeño porcentaje del saldo, y la mantienen igual en cada operación."))]
    body, ld = _tool_page(lang, t, "position-size-calculator.html", TOOLS[0][2], TOOLS[0][3], form, results, script, howto, faqs)
    return (t(T("Futures position size calculator (NQ, ES, CL, GC…) · Sweep","Calculateur de taille de position futures (NQ, ES, CL, GC…) · Sweep","Calculadora de tamaño de posición en futuros (NQ, ES, CL, GC…) · Sweep")),
            t(T("Free calculator: how many NQ, MNQ, ES, MES, CL or GC contracts to trade for your risk and stop, with CME tick values.","Calculateur gratuit : combien de contrats NQ, MNQ, ES, MES, CL ou GC trader selon ton risque et ton stop, avec les valeurs de tick CME.","Calculadora gratuita: cuántos contratos de NQ, MNQ, ES, MES, CL o GC operar según tu riesgo y tu stop, con los valores de tick de CME.")),
            body, ld)

def hub_note():
    """« Each firm’s exact numbers … » with a link to the prop firm rules (calculators’ explanations)."""
    return {l: {"en": "<p>Each firm’s exact numbers (max loss, consistency, payout conditions) are on our <a href=\"{u}\">prop firm rules pages</a>.</p>",
                 "fr": "<p>Les chiffres exacts de chaque firme (perte max, consistance, conditions de payout) sont sur nos <a href=\"{u}\">pages de règles des prop firms</a>.</p>",
                 "es": "<p>Las cifras exactas de cada firma (pérdida máx., consistencia, condiciones de payout) están en nuestras <a href=\"{u}\">páginas de reglas de las prop firms</a>.</p>"}[l].replace("{u}", href(l, "prop-firms/index.html")) for l in LANGS}

def page_drawdown(lang, t):
    form = (_num("dd-start", t(T("Starting balance","Solde de départ","Saldo inicial")), 50000, "any", "$")
        + _num("dd-max", t(T("Maximum drawdown","Drawdown maximum","Drawdown máximo")), 2000, "any", "$")
        + _num("dd-peak", t(T("Highest balance reached","Plus haut solde atteint","Saldo más alto alcanzado")), 51200, "any", "$")
        + _num("dd-cur", t(T("Current balance","Solde actuel","Saldo actual")), 50800, "any", "$")
        + f'<label class="chk"><input id="dd-lock" type="checkbox" checked><span>{t(T("The threshold stops trailing once it reaches the starting balance","Le seuil arrête de suivre une fois arrivé au solde de départ","El umbral deja de seguir al alcanzar el saldo inicial"))}</span></label>')
    results = (f'<div class="big"><span class="num" id="dd-thr">—</span><span id="dd-sub" data-base="{t(T("liquidation level","seuil de liquidation","nivel de liquidación"))}">{t(T("liquidation level","seuil de liquidation","nivel de liquidación"))}</span></div>'
        + f'<div class="meter"><i id="dd-bar"></i></div>'
        + f'<dl><div><dt>{t(T("Room left","Marge restante","Margen restante"))}</dt><dd class="num" id="dd-room">—</dd></div><div><dt>{t(T("Room used","Marge utilisée","Margen usado"))}</dt><dd class="num" id="dd-used">—</dd></div><div><dt>{t(T("Status","Statut","Estado"))}</dt><dd id="dd-st">—</dd></div></dl>')
    st = {"ok":t(T("Safe","Correct","Correcto")),"near":t(T("Close to the limit","Proche de la limite","Cerca del límite")),"out":t(T("Limit reached","Limite atteinte","Límite alcanzado")),"locked":t(T("locked","bloqué","bloqueado"))}
    script = f'''<script>(function(){{var L={_json.dumps(st)},$=function(i){{return document.getElementById(i)}};
var money=function(v){{return (v<0?'−$':'$')+Math.abs(v).toLocaleString(undefined,{{maximumFractionDigits:2}})}};
function run(){{var s=parseFloat($('dd-start').value)||0,m=parseFloat($('dd-max').value)||0,p=Math.max(parseFloat($('dd-peak').value)||0,s),c=parseFloat($('dd-cur').value)||0,lock=$('dd-lock').checked;
var thr=p-m,locked=false;if(lock&&thr>=s){{thr=s;locked=true;}}var room=c-thr,used=m>0?Math.min(100,Math.max(0,(1-room/m)*100)):0;
$('dd-thr').textContent=money(thr);var sb=$('dd-sub');sb.textContent=sb.getAttribute('data-base')+(locked?' · '+L.locked:'');$('dd-room').textContent=money(room);$('dd-used').textContent=Math.round(used)+' %';
var k=room<=0?'out':(used>=75?'near':'ok');$('dd-st').textContent=L[k];$('dd-st').className='st-'+k;$('dd-bar').style.width=used+'%';$('dd-bar').className='bar-'+k;}}
document.querySelectorAll('[data-calc] input').forEach(function(e){{e.addEventListener('input',run)}});run();}})();</script>'''
    howto = T("<p>With a trailing drawdown, your liquidation level follows your highest balance: it sits at that peak minus the maximum drawdown. It never moves down. Depending on the firm, the peak is measured during the day (intraday) or at the close (end of day), and the level often stops trailing once it reaches the starting balance.</p><p>Enter your peak according to your firm’s method: the intraday high for intraday trailing, the best closing balance for end-of-day.</p>",
              "<p>Avec un drawdown suiveur, ton seuil de liquidation suit ton plus haut solde : il se situe à ce sommet moins le drawdown maximum, et il ne redescend jamais. Selon la firme, le sommet est mesuré pendant la journée (intraday) ou à la clôture (fin de journée), et le seuil arrête souvent de suivre une fois arrivé au solde de départ.</p><p>Entre ton sommet selon la méthode de ta firme : le plus haut intraday pour un suivi intraday, le meilleur solde de clôture pour un suivi en fin de journée.</p>",
              "<p>Con un drawdown dinámico, tu nivel de liquidación sigue tu saldo más alto: está en ese máximo menos el drawdown máximo y nunca baja. Según la firma, el máximo se mide durante el día (intradía) o al cierre (fin de día), y el nivel suele dejar de seguir al alcanzar el saldo inicial.</p><p>Introduce tu máximo según el método de tu firma: el máximo intradía para el seguimiento intradía, el mejor saldo de cierre para el de fin de día.</p>")
    howto = {l: howto[l] + hub_note()[l] for l in LANGS}
    faqs = [(T("What’s the difference between intraday and end-of-day trailing?","Quelle différence entre suivi intraday et fin de journée ?","¿Qué diferencia hay entre seguimiento intradía y de fin de día?"),
             T("Intraday trailing moves with your open profit during the session, so a winning trade you give back can still raise your level. End-of-day trailing only moves with your closing balance.","Le suivi intraday bouge avec ton profit latent pendant la séance : un gain rendu en cours de trade peut quand même monter ton seuil. Le suivi en fin de journée ne bouge qu’avec ton solde de clôture.","El seguimiento intradía se mueve con tu beneficio abierto durante la sesión: una ganancia devuelta puede subir igualmente tu nivel. El de fin de día solo se mueve con tu saldo de cierre.")),
            (T("Does Sweep track my drawdown automatically?","Sweep suit-il mon drawdown automatiquement ?","¿Sweep sigue mi drawdown automáticamente?"),
             T("Yes. Each prop account in Sweep has its own drawdown rule, prefilled for guidance from your firm’s preset, and its status updates with every trade.","Oui. Chaque compte prop dans Sweep a sa propre règle de drawdown, préremplie à titre indicatif à partir du préréglage de ta firme, et son statut se met à jour à chaque trade.","Sí. Cada cuenta prop en Sweep tiene su propia regla de drawdown, precargada a título indicativo desde el preajuste de tu firma, y su estado se actualiza con cada operación."))]
    body, ld = _tool_page(lang, t, "trailing-drawdown-calculator.html", TOOLS[1][2], TOOLS[1][3], form, results, script, howto, faqs)
    return (t(T("Trailing drawdown calculator for prop firm accounts · Sweep","Calculateur de drawdown suiveur pour comptes prop · Sweep","Calculadora de drawdown dinámico para cuentas de fondeo · Sweep")),
            t(T("Free calculator: find your liquidation level and the room left on a trailing drawdown prop firm account.","Calculateur gratuit : trouve ton seuil de liquidation et la marge restante sur un compte prop à drawdown suiveur.","Calculadora gratuita: encuentra tu nivel de liquidación y el margen restante en una cuenta de fondeo con drawdown dinámico.")),
            body, ld)

def page_consistency(lang, t):
    form = (_num("cr-pct", t(T("Consistency limit (best day ≤ % of total profit)","Limite de consistance (meilleure journée ≤ % du profit total)","Límite de consistencia (mejor día ≤ % del beneficio total)")), 30, "any", "%")
        + _num("cr-best", t(T("Best day profit","Profit de la meilleure journée","Beneficio del mejor día")), 1500, "any", "$")
        + _num("cr-total", t(T("Total profit","Profit total","Beneficio total")), 3800, "any", "$"))
    results = (f'<div class="big"><span class="num" id="cr-share">—</span><span>{t(T("of your profit comes from your best day","de ton profit vient de ta meilleure journée","de tu beneficio viene de tu mejor día"))}</span></div>'
        + f'<div class="meter"><i id="cr-bar"></i><b id="cr-lim"></b></div>'
        + f'<dl><div><dt>{t(T("Status","Statut","Estado"))}</dt><dd id="cr-st">—</dd></div><div><dt>{t(T("Total profit needed","Profit total nécessaire","Beneficio total necesario"))}</dt><dd class="num" id="cr-need">—</dd></div><div><dt>{t(T("Still to make","Reste à faire","Falta por hacer"))}</dt><dd class="num" id="cr-left">—</dd></div></dl>')
    st = {"ok":t(T("Within the limit","Dans la limite","Dentro del límite")),"out":t(T("Above the limit","Au-dessus de la limite","Por encima del límite"))}
    script = f'''<script>(function(){{var L={_json.dumps(st)},$=function(i){{return document.getElementById(i)}};
var money=function(v){{return '$'+Math.max(0,v).toLocaleString(undefined,{{maximumFractionDigits:2}})}};
function run(){{var p=parseFloat($('cr-pct').value)||0,b=parseFloat($('cr-best').value)||0,tt=parseFloat($('cr-total').value)||0;
var share=tt>0?b/tt*100:0,need=p>0?b/(p/100):0,ok=tt>0&&share<=p+1e-9;
$('cr-share').textContent=tt>0?share.toFixed(1)+' %':'—';$('cr-st').textContent=tt>0?(ok?L.ok:L.out):'—';$('cr-st').className=ok?'st-ok':'st-out';
$('cr-need').textContent=money(need);$('cr-left').textContent=money(need-tt);$('cr-bar').style.width=Math.min(100,share)+'%';$('cr-bar').className=ok?'bar-ok':'bar-out';$('cr-lim').style.left=Math.min(100,p)+'%';}}
document.querySelectorAll('[data-calc] input').forEach(function(e){{e.addEventListener('input',run)}});run();}})();</script>'''
    howto = T("<p>A consistency rule limits how much of your total profit can come from a single day. With a 30% rule and a $1,500 best day, your total profit must reach at least $1,500 ÷ 0.30 = $5,000 before you qualify.</p><p>The fix is never a bigger day: it’s more ordinary days. Some firms apply the rule to evaluations, others to payouts, with different percentages.</p>",
              "<p>Une règle de consistance limite la part de ton profit total qui peut venir d’une seule journée. Avec une règle de 30 % et une meilleure journée de 1 500 $, ton profit total doit atteindre au moins 1 500 $ ÷ 0,30 = 5 000 $ pour être admissible.</p><p>La solution n’est jamais une plus grosse journée : ce sont plus de journées ordinaires. Certaines firmes appliquent la règle aux évaluations, d’autres aux payouts, avec des pourcentages différents.</p>",
              "<p>Una regla de consistencia limita qué parte de tu beneficio total puede venir de un solo día. Con una regla del 30 % y un mejor día de 1.500 $, tu beneficio total debe llegar al menos a 1.500 $ ÷ 0,30 = 5.000 $ para calificar.</p><p>La solución nunca es un día más grande: son más días normales. Algunas firmas aplican la regla a las evaluaciones y otras a los payouts, con porcentajes distintos.</p>")
    faqs = [(T("Why do prop firms use a consistency rule?","Pourquoi les prop firms ont-elles une règle de consistance ?","¿Por qué las prop firms usan una regla de consistencia?"),
             T("To make sure results come from a repeatable process rather than one outsized day.","Pour s’assurer que les résultats viennent d’un processus répétable plutôt que d’une seule journée hors norme.","Para asegurarse de que los resultados vienen de un proceso repetible y no de un único día excepcional.")),
            (T("Does Sweep check consistency for me?","Sweep vérifie-t-il la consistance pour moi ?","¿Sweep revisa la consistencia por mí?"),
             T("Yes. Consistency is one of the rules Sweep tracks on each prop account, with the percentage prefilled for guidance from your firm’s preset.","Oui. La consistance fait partie des règles que Sweep suit sur chaque compte prop, avec le pourcentage prérempli à titre indicatif à partir du préréglage de ta firme.","Sí. La consistencia es una de las reglas que Sweep sigue en cada cuenta prop, con el porcentaje precargado a título indicativo desde el preajuste de tu firma."))]
    body, ld = _tool_page(lang, t, "consistency-rule-calculator.html", TOOLS[2][2], TOOLS[2][3], form, results, script, howto, faqs)
    return (t(T("Consistency rule calculator for prop firm payouts · Sweep","Calculateur de règle de consistance pour prop firms · Sweep","Calculadora de regla de consistencia para prop firms · Sweep")),
            t(T("Free calculator: check your best day against your prop firm’s consistency rule and see how much more profit you need.","Calculateur gratuit : compare ta meilleure journée à la règle de consistance de ta prop firm et vois combien de profit il te manque.","Calculadora gratuita: compara tu mejor día con la regla de consistencia de tu prop firm y mira cuánto beneficio te falta.")),
            body, ld)

def page_tools(lang, t):
    hero = page_hero(t, T("Free tools for futures and prop traders.","Outils gratuits pour traders de futures et de prop firms.","Herramientas gratuitas para traders de futuros y de fondeo."),
        T("Quick answers before you take the trade. No account needed.","Des réponses rapides avant de prendre le trade. Sans compte.","Respuestas rápidas antes de entrar en la operación. Sin cuenta."), T("Free tools","Outils gratuits","Herramientas gratuitas"))
    cards = "".join(f'<a class="tool-card reveal" href="{href(lang,s)}">{ico(I[ic])}<h2>{t(n)}</h2><p>{t(d)}</p><span class="go">{t(T("Open","Ouvrir","Abrir"))} →</span></a>' for s,ic,n,d in TOOLS)
    b = f'<section style="padding-top:8px"><div class="wrap"><div class="tool-grid">{cards}</div><p class="center-note"><a class="tlink" href="{href(lang,"prop-firms/index.html")}">{t(T("Each firm’s rules, explained","Les règles de chaque firme, expliquées","Las reglas de cada firma, explicadas"))} <span aria-hidden="true">→</span></a></p><p class="fine" style="text-align:center;margin:22px auto 0;max-width:70ch">{t(NOTE)}</p></div></section>'
    return (t(T("Free futures and prop firm calculators · Sweep","Calculateurs gratuits pour futures et prop firms · Sweep","Calculadoras gratuitas para futuros y prop firms · Sweep")),
            t(T("Free position size, trailing drawdown and consistency rule calculators for futures and prop firm traders.","Calculateurs gratuits de taille de position, de drawdown suiveur et de règle de consistance pour traders de futures et de prop firms.","Calculadoras gratuitas de tamaño de posición, drawdown dinámico y regla de consistencia para traders de futuros y de fondeo.")),
            hero + b + final_cta(lang, t), "")

TOOLS += [
 ("expectancy-calculator.html","target2",T("Expectancy calculator","Calculateur d’espérance","Calculadora de esperanza"),
  T("What does one trade earn you on average, given your win rate and average win and loss?","Que te rapporte un trade en moyenne, selon ton taux de réussite et tes gains et pertes moyens ?","¿Cuánto te deja una operación de media, según tu tasa de acierto y tus ganancias y pérdidas medias?")),
 ("prop-firm-roi-calculator.html","receipt",T("Prop firm ROI calculator","Calculateur de rentabilité prop","Calculadora de rentabilidad prop"),
  T("Evaluations, resets and fees against payouts: your real net, and your return.","Évaluations, resets et frais contre payouts : ton vrai net, et ton rendement.","Evaluaciones, reinicios y cuotas frente a payouts: tu neto real y tu rendimiento.")),
 ("payout-calculator.html","download",T("Payout calculator","Calculateur de payout","Calculadora de payout"),
  T("How much can you request, after the cushion and within the minimum and maximum?","Combien peux-tu demander, après le coussin et entre le minimum et le maximum ?","¿Cuánto puedes pedir, tras el colchón y entre el mínimo y el máximo?")),
]

def _simple_tool(lang, t, idx, form, results, js, howto, faqs, title, desc):
    s, ic, n, d = TOOLS[idx]
    body, ld = _tool_page(lang, t, s, n, d, form, results, f"<script>(function(){{var $=function(i){{return document.getElementById(i)}},money=function(v){{var a=Math.abs(v);return (v<0?'−$':'$')+a.toLocaleString(undefined,{{maximumFractionDigits:2,minimumFractionDigits:a%1?2:0}})}};{js}document.querySelectorAll('[data-calc] input').forEach(function(e){{e.addEventListener('input',run)}});run();}})();</script>", howto, faqs)
    return (t(title), t(desc), body, ld)

def page_expectancy(lang, t):
    form = _num("ex-wr", t(T("Win rate","Taux de réussite","Tasa de acierto")), 45, "any", "%") + _num("ex-w", t(T("Average win","Gain moyen","Ganancia media")), 400, "any", "$") + _num("ex-l", t(T("Average loss","Perte moyenne","Pérdida media")), 250, "any", "$")
    res = (f'<div class="big"><span class="num" id="ex-e">—</span><span>{t(T("per trade, on average","par trade, en moyenne","por operación, de media"))}</span></div>'
           f'<dl><div><dt>{t(T("Per 100 trades","Pour 100 trades","Por 100 operaciones"))}</dt><dd class="num" id="ex-100">—</dd></div><div><dt>{t(T("In R (risk = average loss)","En R (risque = perte moyenne)","En R (riesgo = pérdida media)"))}</dt><dd class="num" id="ex-r">—</dd></div><div><dt>{t(T("Break-even win rate","Taux de réussite d’équilibre","Tasa de acierto de equilibrio"))}</dt><dd class="num" id="ex-be">—</dd></div><div><dt>Profit factor</dt><dd class="num" id="ex-pf">—</dd></div></dl>')
    js = "function run(){var w=(parseFloat($('ex-wr').value)||0)/100,aw=parseFloat($('ex-w').value)||0,al=parseFloat($('ex-l').value)||0;var e=w*aw-(1-w)*al;$('ex-e').textContent=money(e);$('ex-e').className='num '+(e>=0?'st-ok':'st-out');$('ex-100').textContent=money(e*100);$('ex-r').textContent=al>0?(e/al).toFixed(2)+' R':'—';$('ex-be').textContent=(aw+al)>0?(al/(aw+al)*100).toFixed(1)+' %':'—';$('ex-pf').textContent=(1-w)*al>0?(w*aw/((1-w)*al)).toFixed(2):'—';}"
    howto = T("<p>Expectancy = win rate × average win − loss rate × average loss. With a 45% win rate, a $400 average win and a $250 average loss: 0.45 × 400 − 0.55 × 250 = $42.50 per trade.</p><p>It describes your past results, not the future. The more trades behind the numbers, the more meaningful it is.</p>",
              "<p>Espérance = taux de réussite × gain moyen − taux de perte × perte moyenne. Avec 45 % de réussite, 400 $ de gain moyen et 250 $ de perte moyenne : 0,45 × 400 − 0,55 × 250 = 42,50 $ par trade.</p><p>Elle décrit tes résultats passés, pas l’avenir. Plus il y a de trades derrière les chiffres, plus elle a du sens.</p>",
              "<p>Esperanza = tasa de acierto × ganancia media − tasa de pérdida × pérdida media. Con un 45 % de acierto, 400 $ de ganancia media y 250 $ de pérdida media: 0,45 × 400 − 0,55 × 250 = 42,50 $ por operación.</p><p>Describe tus resultados pasados, no el futuro. Cuantas más operaciones haya detrás, más sentido tiene.</p>")
    faqs = [(T("Can a strategy win less than half the time and still make money?","Une stratégie peut-elle gagner moins d’une fois sur deux et rester rentable ?","¿Puede una estrategia ganar menos de la mitad de las veces y ser rentable?"),
             T("Yes, if the average win is large enough compared with the average loss. The break-even win rate shows where that line is.","Oui, si le gain moyen est assez grand par rapport à la perte moyenne. Le taux de réussite d’équilibre montre où se trouve cette limite.","Sí, si la ganancia media es suficientemente grande frente a la pérdida media. La tasa de acierto de equilibrio muestra dónde está ese límite."))]
    return _simple_tool(lang, t, 3, form, res, js, howto, faqs,
        T("Trading expectancy calculator (win rate, R, profit factor) · Sweep","Calculateur d’espérance de trading (R, profit factor) · Sweep","Calculadora de esperanza de trading (R, profit factor) · Sweep"),
        T("Free calculator: expectancy per trade from your win rate, average win and average loss, in dollars and in R, with break-even win rate and profit factor.","Calculateur gratuit : espérance par trade selon ton taux de réussite, ton gain moyen et ta perte moyenne, en dollars et en R.","Calculadora gratuita: esperanza por operación según tu tasa de acierto, ganancia media y pérdida media, en dólares y en R."))

def page_roi(lang, t):
    form = (_num("ro-ev", t(T("Evaluations bought","Évaluations achetées","Evaluaciones compradas")), 3, "1") + _num("ro-evp", t(T("Price per evaluation","Prix par évaluation","Precio por evaluación")), 150, "any", "$")
            + _num("ro-rs", t(T("Resets","Resets","Reinicios")), 2, "1") + _num("ro-rsp", t(T("Price per reset","Prix par reset","Precio por reinicio")), 100, "any", "$")
            + _num("ro-act", t(T("Activation and data fees","Frais d’activation et de données","Cuotas de activación y datos")), 150, "any", "$") + _num("ro-pay", t(T("Payouts received","Payouts reçus","Payouts recibidos")), 2000, "any", "$"))
    res = (f'<div class="big"><span class="num" id="ro-net">—</span><span>{t(T("net after fees","net après frais","neto tras cuotas"))}</span></div>'
           f'<dl><div><dt>{t(T("Total spent","Total dépensé","Total gastado"))}</dt><dd class="num" id="ro-sp">—</dd></div><div><dt>{t(T("Return on fees","Rendement sur frais","Rendimiento sobre cuotas"))}</dt><dd class="num" id="ro-x">—</dd></div><div><dt>ROI</dt><dd class="num" id="ro-roi">—</dd></div></dl>')
    js = "function run(){var v=function(i){return parseFloat($(i).value)||0};var sp=v('ro-ev')*v('ro-evp')+v('ro-rs')*v('ro-rsp')+v('ro-act'),p=v('ro-pay'),n=p-sp;$('ro-net').textContent=money(n);$('ro-net').className='num '+(n>=0?'st-ok':'st-out');$('ro-sp').textContent=money(sp);$('ro-x').textContent=sp>0?(p/sp).toFixed(1)+'×':'—';$('ro-roi').textContent=sp>0?Math.round(n/sp*100)+' %':'—';}"
    howto = T("<p>Net = payouts received − everything you paid: evaluations, resets, activations and data fees. Return on fees = payouts ÷ total spent: 3.0× means every dollar spent came back three times.</p>",
              "<p>Net = payouts reçus − tout ce que tu as payé : évaluations, resets, activations et frais de données. Rendement sur frais = payouts ÷ total dépensé : 3,0× veut dire que chaque dollar dépensé est revenu trois fois.</p>",
              "<p>Neto = payouts recibidos − todo lo pagado: evaluaciones, reinicios, activaciones y datos. Rendimiento sobre cuotas = payouts ÷ total gastado: 3,0× significa que cada dólar gastado volvió tres veces.</p>")
    faqs = [(T("Does Sweep track this automatically?","Sweep calcule-t-il ça automatiquement ?","¿Sweep lo calcula automáticamente?"),
             T("Yes. Log your expenses and payouts in Sweep and your net after fees is always one line, by firm and by account.","Oui. Note tes dépenses et tes payouts dans Sweep et ton net après frais tient toujours en une ligne, par firme et par compte.","Sí. Registra tus gastos y payouts en Sweep y tu neto tras cuotas siempre cabe en una línea, por firma y por cuenta."))]
    return _simple_tool(lang, t, 4, form, res, js, howto, faqs,
        T("Prop firm ROI calculator: net after evaluations and resets · Sweep","Calculateur de rentabilité prop : ton net après frais · Sweep","Calculadora de rentabilidad prop: neto tras cuotas · Sweep"),
        T("Free calculator: what prop trading really pays you after evaluations, resets, activation and data fees, with your return on fees.","Calculateur gratuit : ce que le trading prop te rapporte vraiment après évaluations, resets, activation et frais de données.","Calculadora gratuita: lo que el trading prop te deja realmente tras evaluaciones, reinicios, activación y datos."))

def page_payoutcalc(lang, t):
    form = (_num("po-bal", t(T("Current balance","Solde actuel","Saldo actual")), 53800, "any", "$") + _num("po-st", t(T("Starting balance","Solde de départ","Saldo inicial")), 50000, "any", "$")
            + _num("po-cu", t(T("Cushion to keep above the start","Coussin à garder au-dessus du départ","Colchón a mantener sobre el inicio")), 2100, "any", "$")
            + _num("po-min", t(T("Minimum payout","Payout minimum","Payout mínimo")), 500, "any", "$") + _num("po-max", t(T("Maximum payout","Payout maximum","Payout máximo")), 2000, "any", "$"))
    res = (f'<div class="big"><span class="num" id="po-out">—</span><span id="po-sub">{t(T("you can request","tu peux demander","puedes pedir"))}</span></div>'
           f'<dl><div><dt>{t(T("Above the cushion","Au-dessus du coussin","Por encima del colchón"))}</dt><dd class="num" id="po-av">—</dd></div><div><dt>{t(T("Still needed for the minimum","Manque pour le minimum","Falta para el mínimo"))}</dt><dd class="num" id="po-need">—</dd></div><div><dt>{t(T("Balance after the payout","Solde après le payout","Saldo tras el payout"))}</dt><dd class="num" id="po-after">—</dd></div></dl>')
    js = "function run(){var v=function(i){return parseFloat($(i).value)||0};var av=v('po-bal')-(v('po-st')+v('po-cu')),mx=v('po-max')>0?v('po-max'):Infinity,ok=av>=v('po-min'),req=ok?Math.min(av,mx):0;$('po-out').textContent=money(req);$('po-out').className='num '+(ok?'st-ok':'st-out');$('po-av').textContent=money(Math.max(0,av));$('po-need').textContent=money(Math.max(0,v('po-min')-av));$('po-after').textContent=money(v('po-bal')-req);}"
    howto = T("<p>Many firms only pay what sits above the starting balance plus a cushion, between a minimum and a maximum per request. Requestable = the smaller of (balance − start − cushion) and the maximum, if it reaches the minimum.</p><p>Firms also count winning days and consistency before a payout: Sweep tracks those on each account.</p>",
              "<p>Beaucoup de firmes ne paient que ce qui dépasse le solde de départ plus un coussin, entre un minimum et un maximum par demande. Montant demandable = le plus petit entre (solde − départ − coussin) et le maximum, s’il atteint le minimum.</p><p>Les firmes comptent aussi les jours gagnants et la consistance avant un payout : Sweep les suit sur chaque compte.</p>",
              "<p>Muchas firmas solo pagan lo que supera el saldo inicial más un colchón, entre un mínimo y un máximo por solicitud. Importe solicitable = el menor entre (saldo − inicio − colchón) y el máximo, si alcanza el mínimo.</p><p>Las firmas también cuentan los días ganadores y la consistencia antes de un payout: Sweep los sigue en cada cuenta.</p>")
    howto = {l: howto[l] + hub_note()[l] for l in LANGS}
    faqs = [(T("Why can’t I withdraw my whole profit?","Pourquoi je ne peux pas retirer tout mon profit ?","¿Por qué no puedo retirar todo mi beneficio?"),
             T("Firms often require a cushion above the starting balance and cap each payout. Always check your firm’s current rules.","Les firmes exigent souvent un coussin au-dessus du solde de départ et plafonnent chaque payout. Vérifie toujours les règles actuelles de ta firme.","Las firmas suelen exigir un colchón sobre el saldo inicial y limitan cada payout. Verifica siempre las reglas actuales de tu firma."))]
    return _simple_tool(lang, t, 5, form, res, js, howto, faqs,
        T("Prop firm payout calculator: how much can you request? · Sweep","Calculateur de payout prop : combien peux-tu demander ? · Sweep","Calculadora de payout prop: ¿cuánto puedes pedir? · Sweep"),
        T("Free calculator: the payout you can request after your firm’s cushion, within the minimum and maximum per request.","Calculateur gratuit : le payout que tu peux demander après le coussin de ta firme, entre le minimum et le maximum.","Calculadora gratuita: el payout que puedes pedir tras el colchón de tu firma, entre el mínimo y el máximo."))
