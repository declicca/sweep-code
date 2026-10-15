from core import *
import json as _json
import ui

# numbers in the page's language, as everywhere on the site (never the browser's): $1,700.50 · 1 700,50 $ · 1.700,50 $ ; 52% · 52 %
NUM_JS = ("var LG=(document.documentElement.lang||'en').slice(0,2),"
          "fx=function(v,a,b){var s=Math.abs(v).toLocaleString('en-US',{minimumFractionDigits:a,maximumFractionDigits:b});return LG==='en'?s:s.replace(/,/g,'~').replace('.',',').replace(/~/g,LG==='fr'?'\\u202f':'.')},"
          "sg=function(v){return v<0?'\\u2212':''},"
          "cur=function(v,a){return sg(v)+(LG==='en'?'$'+fx(v,a,2):fx(v,a,2)+'\\u00a0$')},"
          "pc=function(v,d){return sg(v)+fx(v,d,d)+(LG==='en'?'%':'\\u202f%')},"
          "dec=function(v,d){return sg(v)+fx(v,d,d)};")

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

def note(lang, t):
    """The guidance note, its last sentence linked to the risk disclosure."""
    s = t(NOTE); k = s.rfind(". ") + 2
    return s[:k] + f'<a href="{href(lang, "risk.html")}">{s[k:-1]}</a>.'

ACT = {
 "position-size-calculator.html": T("Sweep checks every trade against your daily risk budget, right in the trade ticket.", "Sweep vérifie chaque trade contre ton budget de risque du jour, directement dans le ticket.", "Sweep comprueba cada operación con tu presupuesto de riesgo del día, en el propio ticket."),
 "trailing-drawdown-calculator.html": T("Sweep tracks the room left above your max loss on every prop account, trade by trade.", "Sweep suit la marge restante au-dessus de ta perte max sur chaque compte prop, trade après trade.", "Sweep sigue el margen que te queda sobre tu pérdida máx. en cada cuenta prop, operación a operación."),
 "consistency-rule-calculator.html": T("Sweep checks your best day against your firm’s consistency rule after every trade.", "Sweep vérifie ton meilleur jour contre la règle de consistance de ta firme après chaque trade.", "Sweep comprueba tu mejor día con la regla de consistencia de tu firma tras cada operación."),
 "payout-calculator.html": T("Sweep counts your payout conditions on every trade and tells you when you can request.", "Sweep compte tes conditions de payout à chaque trade et te dit quand tu peux demander.", "Sweep cuenta tus condiciones de payout en cada operación y te dice cuándo puedes pedirlo."),
 "expectancy-calculator.html": T("Sweep computes your expectancy, win rate and profit factor from your real trades.", "Sweep calcule ton espérance, ton taux de réussite et ton profit factor à partir de tes vrais trades.", "Sweep calcula tu esperanza, tu tasa de acierto y tu profit factor con tus operaciones reales."),
 "prop-firm-roi-calculator.html": T("Sweep keeps every evaluation, reset and payout in one place: your real net, firm by firm (Pro and Elite, included for your first 60 days).", "Sweep garde chaque évaluation, reset et payout au même endroit : ton vrai net, firme par firme (Pro et Elite, offerts tes 60 premiers jours).", "Sweep guarda cada evaluación, reinicio y payout en un solo lugar: tu neto real, firma por firma (Pro y Elite, incluidos tus primeros 60 días)."),
}

# How to use each calculator, a worked example (the calculator's default numbers), common mistakes and more questions.
# Links are written href="@page.html" and localized by _tool_page.
HELP = {
 "position-size-calculator.html": {
  "steps": [T("Pick the instrument: its tick size and tick value fill in.", "Choisis l’instrument : sa taille et sa valeur de tick se remplissent.", "Elige el instrumento: su tamaño y valor del tick se rellenan."),
            T("Enter your risk per trade, in dollars or as a percentage of the balance.", "Entre ton risque par trade, en dollars ou en pourcentage du solde.", "Introduce tu riesgo por operación, en dólares o en porcentaje del saldo."),
            T("Enter your stop distance in points or in ticks. The result is the number of contracts, rounded down.", "Entre la distance de ton stop en points ou en ticks. Le résultat est le nombre de contrats, arrondi vers le bas.", "Introduce la distancia del stop en puntos o en ticks. El resultado es el número de contratos, redondeado hacia abajo.")],
  "example": T("<p>On a $50,000 account, you risk 0.5% ($250) with a 12-point stop on ES. Twelve points are 48 ticks × $12.50 = $600 per contract: 0 ES contracts. On MES, the same stop costs $60 per contract, so 4 contracts for $240 at risk.</p>",
               "<p>Sur un compte de 50 000 $, tu risques 0,5 % (250 $) avec un stop de 12 points sur ES. Douze points, c’est 48 ticks × 12,50 $ = 600 $ par contrat : 0 contrat ES. Sur MES, le même stop coûte 60 $ par contrat, donc 4 contrats pour 240 $ de risque.</p>",
               "<p>En una cuenta de 50.000 $, arriesgas el 0,5 % (250 $) con un stop de 12 puntos en ES. Doce puntos son 48 ticks × 12,50 $ = 600 $ por contrato: 0 contratos de ES. En MES, el mismo stop cuesta 60 $ por contrato, así que 4 contratos con 240 $ en riesgo.</p>"),
  "mistakes": [(T("Mixing up points and ticks.", "Confondre points et ticks.", "Confundir puntos y ticks."),
                T("A 10-point stop on NQ is 40 ticks, not 10. Check the switch above the stop field.", "Un stop de 10 points sur NQ, c’est 40 ticks, pas 10. Vérifie le sélecteur au-dessus du champ du stop.", "Un stop de 10 puntos en NQ son 40 ticks, no 10. Revisa el selector encima del campo del stop.")),
               (T("Treating the stop as the most you can lose.", "Prendre le stop pour la perte maximale.", "Tomar el stop como la pérdida máxima."),
                T("Commissions and slippage come on top. Keep a little room under the risk you accept.", "Les commissions et le glissement s’ajoutent. Garde un peu de marge sous le risque accepté.", "Las comisiones y el deslizamiento se suman. Deja algo de margen bajo el riesgo que aceptas.")),
               (T("Sizing from the balance on a prop account.", "Calculer la taille sur le solde d’un compte prop.", "Calcular el tamaño sobre el saldo de una cuenta prop."),
                T("What matters is the room left before your max loss. Check it with the <a href=\"@trailing-drawdown-calculator.html\">trailing drawdown calculator</a>.", "Ce qui compte, c’est la marge restante avant ta perte max. Vérifie-la avec le <a href=\"@trailing-drawdown-calculator.html\">calculateur de drawdown suiveur</a>.", "Lo que cuenta es el margen que te queda antes de tu pérdida máx. Compruébalo con la <a href=\"@trailing-drawdown-calculator.html\">calculadora de drawdown dinámico</a>."))],
  "faq": [(T("Should I trade micros or minis?", "Micros ou minis : lesquels trader ?", "¿Micros o minis?"),
           T("Micros (MNQ, MES, MYM, M2K, MCL, MGC) are one tenth of the mini, so they let you size in smaller steps. When the result is 0 or 1 mini, the same risk often fits several micros.", "Les micros (MNQ, MES, MYM, M2K, MCL, MGC) valent un dixième du mini : ils permettent d’ajuster la taille par petits pas. Quand le résultat est 0 ou 1 mini, le même risque permet souvent plusieurs micros.", "Los micros (MNQ, MES, MYM, M2K, MCL, MGC) valen una décima parte del mini, así que permiten ajustar el tamaño en pasos pequeños. Cuando el resultado es 0 o 1 mini, el mismo riesgo suele permitir varios micros."))]},
 "trailing-drawdown-calculator.html": {
  "steps": [T("Enter the starting balance and the maximum drawdown of your account.", "Entre le solde de départ et le drawdown maximum de ton compte.", "Introduce el saldo inicial y el drawdown máximo de tu cuenta."),
            T("Enter the highest balance reached, measured the way your firm does, and your current balance.", "Entre le plus haut solde atteint, mesuré comme le fait ta firme, et ton solde actuel.", "Introduce el saldo más alto alcanzado, medido como lo hace tu firma, y tu saldo actual."),
            T("Tick the box if your firm stops trailing at the starting balance. You get your liquidation level and the room left.", "Coche la case si ta firme arrête le suivi au solde de départ. Tu obtiens ton seuil de liquidation et la marge restante.", "Marca la casilla si tu firma deja de seguir en el saldo inicial. Obtienes tu nivel de liquidación y el margen restante.")],
  "example": T("<p>A $50,000 account with a $2,000 trailing drawdown peaks at $51,200: the level is $49,200. At $50,800, you have $1,600 of room left and 20% of the drawdown is used. Once the peak reaches $52,000, a level that locks at the start stays at $50,000.</p>",
               "<p>Un compte de 50 000 $ avec un drawdown suiveur de 2 000 $ monte jusqu’à 51 200 $ : le seuil est à 49 200 $. À 50 800 $, il te reste 1 600 $ de marge et 20 % du drawdown est utilisé. Quand le sommet atteint 52 000 $, un seuil bloqué au départ reste à 50 000 $.</p>",
               "<p>Una cuenta de 50.000 $ con un drawdown dinámico de 2.000 $ llega a 51.200 $: el nivel está en 49.200 $. A 50.800 $, te quedan 1.600 $ de margen y has usado el 20 % del drawdown. Cuando el máximo llega a 52.000 $, un nivel bloqueado en el inicio se queda en 50.000 $.</p>"),
  "mistakes": [(T("Entering the current balance as the peak.", "Entrer le solde actuel comme sommet.", "Introducir el saldo actual como máximo."),
                T("The level follows the highest balance reached, even if you gave the profit back since.", "Le seuil suit le plus haut solde atteint, même si tu as rendu le profit depuis.", "El nivel sigue el saldo más alto alcanzado, aunque hayas devuelto el beneficio después.")),
               (T("Mixing up intraday and end of day.", "Confondre intraday et fin de journée.", "Confundir intradía y fin de día."),
                T("With intraday trailing, the high of an open trade counts, even if you close lower.", "Avec un suivi intraday, le plus haut d’un trade ouvert compte, même si tu fermes plus bas.", "Con seguimiento intradía, el máximo de una operación abierta cuenta, aunque cierres más abajo.")),
               (T("Confusing it with the daily loss limit.", "Le confondre avec la limite de perte quotidienne.", "Confundirlo con el límite de pérdida diaria."),
                T("The daily limit resets every session. The trailing level never moves down, so a losing day doesn’t give room back.", "La limite quotidienne repart à zéro chaque séance. Le seuil suiveur ne redescend jamais : une journée perdante ne rend pas de marge.", "El límite diario se reinicia cada sesión. El nivel dinámico nunca baja: un día perdedor no devuelve margen."))],
  "faq": [(T("When does a trailing drawdown stop trailing?", "Quand un drawdown suiveur arrête-t-il de suivre ?", "¿Cuándo deja de seguir un drawdown dinámico?"),
           T("At many firms, once the level reaches the starting balance (sometimes plus a small amount), it stays there. The rule varies by firm and account type: see each firm’s rules page.", "Chez beaucoup de firmes, une fois que le seuil atteint le solde de départ (parfois un peu plus), il ne bouge plus. La règle varie selon la firme et le type de compte : vois la page de règles de chaque firme.", "En muchas firmas, cuando el nivel alcanza el saldo inicial (a veces algo más), se queda ahí. La regla varía según la firma y el tipo de cuenta: mira la página de reglas de cada firma."))]},
 "consistency-rule-calculator.html": {
  "steps": [T("Enter your firm’s consistency limit, as a percentage of total profit.", "Entre la limite de consistance de ta firme, en pourcentage du profit total.", "Introduce el límite de consistencia de tu firma, en porcentaje del beneficio total."),
            T("Enter your best day’s profit and your total profit for the period your firm counts.", "Entre le profit de ta meilleure journée et ton profit total sur la période que compte ta firme.", "Introduce el beneficio de tu mejor día y tu beneficio total en el periodo que cuenta tu firma."),
            T("Read your best day’s share and how much more total profit you need to be within the limit.", "Lis la part de ta meilleure journée et le profit total qu’il te manque pour être dans la limite.", "Lee el peso de tu mejor día y cuánto beneficio total te falta para estar dentro del límite.")],
  "example": T("<p>With a 30% limit, a $1,500 best day and $3,800 of total profit, the best day is 39.5% of the profit. The total must reach $5,000: $1,200 more, made on other days.</p>",
               "<p>Avec une limite de 30 %, une meilleure journée de 1 500 $ et 3 800 $ de profit total, la meilleure journée pèse 39,5 % du profit. Le total doit atteindre 5 000 $ : encore 1 200 $, faits sur d’autres journées.</p>",
               "<p>Con un límite del 30 %, un mejor día de 1.500 $ y 3.800 $ de beneficio total, el mejor día pesa el 39,5 % del beneficio. El total debe llegar a 5.000 $: 1.200 $ más, hechos en otros días.</p>"),
  "mistakes": [(T("Counting the wrong period.", "Compter la mauvaise période.", "Contar el periodo equivocado."),
                T("Some firms count the whole evaluation, others only the profit since your last payout.", "Certaines firmes comptent toute l’évaluation, d’autres seulement le profit depuis ton dernier payout.", "Algunas firmas cuentan toda la evaluación y otras solo el beneficio desde tu último payout.")),
               (T("Fixing it with one big day.", "Corriger avec une grosse journée.", "Arreglarlo con un día grande."),
                T("A day bigger than your best day becomes the new best day, and you need even more total profit.", "Une journée plus grosse que ta meilleure devient la nouvelle meilleure, et il te faut encore plus de profit total.", "Un día mayor que tu mejor día se convierte en el nuevo mejor día, y necesitas aún más beneficio total.")),
               (T("Forgetting losing days.", "Oublier les journées perdantes.", "Olvidar los días perdedores."),
                T("Total profit is net: a losing day lowers it and raises your best day’s share.", "Le profit total est net : une journée perdante le fait baisser et augmente la part de ta meilleure journée.", "El beneficio total es neto: un día perdedor lo reduce y aumenta el peso de tu mejor día."))],
  "faq": [(T("What happens if I’m above the limit?", "Que se passe-t-il si je dépasse la limite ?", "¿Qué pasa si estoy por encima del límite?"),
           T("Under most rules you don’t fail: you need more total profit before you can pass or request a payout. The exact effect depends on the firm.", "Avec la plupart des règles, tu n’échoues pas : il te faut plus de profit total avant de réussir ou de demander un payout. L’effet exact dépend de la firme.", "Con la mayoría de las reglas no suspendes: necesitas más beneficio total antes de aprobar o pedir un payout. El efecto exacto depende de la firma."))]},
 "payout-calculator.html": {
  "steps": [T("Enter your current balance and your starting balance.", "Entre ton solde actuel et ton solde de départ.", "Introduce tu saldo actual y tu saldo inicial."),
            T("Enter the cushion your firm asks you to keep above the start, and its minimum and maximum per request.", "Entre le coussin que ta firme te demande de garder au-dessus du départ, et son minimum et son maximum par demande.", "Introduce el colchón que tu firma te pide mantener sobre el inicio, y su mínimo y máximo por solicitud."),
            T("Read what you can request now, what’s missing for the minimum and your balance after the payout.", "Lis ce que tu peux demander maintenant, ce qu’il manque pour le minimum et ton solde après le payout.", "Lee lo que puedes pedir ahora, lo que falta para el mínimo y tu saldo tras el payout.")],
  "example": T("<p>A $50,000 account at $53,800 with a $2,100 cushion has $1,700 above the cushion. That’s between the $500 minimum and the $2,000 maximum, so you can request $1,700 and you’re back at $52,100.</p>",
               "<p>Un compte de 50 000 $ à 53 800 $, avec un coussin de 2 100 $, a 1 700 $ au-dessus du coussin. C’est entre le minimum de 500 $ et le maximum de 2 000 $ : tu peux demander 1 700 $ et tu reviens à 52 100 $.</p>",
               "<p>Una cuenta de 50.000 $ en 53.800 $, con un colchón de 2.100 $, tiene 1.700 $ por encima del colchón. Está entre el mínimo de 500 $ y el máximo de 2.000 $: puedes pedir 1.700 $ y vuelves a 52.100 $.</p>"),
  "mistakes": [(T("Counting the whole profit.", "Compter tout le profit.", "Contar todo el beneficio."),
                T("Only what sits above the starting balance plus the cushion can be requested.", "Seul ce qui dépasse le solde de départ plus le coussin peut être demandé.", "Solo se puede pedir lo que supera el saldo inicial más el colchón.")),
               (T("Forgetting the other conditions.", "Oublier les autres conditions.", "Olvidar las demás condiciones."),
                T("Winning days, trading days and consistency must be met too. This calculator checks the amounts only.", "Les jours gagnants, les jours tradés et la consistance doivent aussi être respectés. Ce calculateur ne vérifie que les montants.", "Los días ganadores, los días operados y la consistencia también deben cumplirse. Esta calculadora solo revisa los importes.")),
               (T("Forgetting the profit split.", "Oublier le partage des profits.", "Olvidar el reparto de beneficios."),
                T("Depending on the firm, you receive a share of the amount you request, for example 90%.", "Selon la firme, tu reçois une part du montant demandé, par exemple 90 %.", "Según la firma, recibes una parte del importe que pides, por ejemplo el 90 %."))],
  "faq": [(T("What is the payout cushion?", "Qu’est-ce que le coussin de payout ?", "¿Qué es el colchón de payout?"),
           T("An amount some firms ask you to keep above the starting balance, so the account isn’t at its max loss right after a payout. Not every firm has one.", "Un montant que certaines firmes te demandent de garder au-dessus du solde de départ, pour que le compte ne soit pas à sa perte max juste après un payout. Toutes les firmes n’en ont pas.", "Un importe que algunas firmas te piden mantener sobre el saldo inicial, para que la cuenta no quede en su pérdida máx. justo después de un payout. No todas las firmas lo tienen.")),
          (T("How often can I request a payout?", "À quelle fréquence puis-je demander un payout ?", "¿Cada cuánto puedo pedir un payout?"),
           T("It depends on the firm: some count winning days or trading days since the last payout, others use a fixed cycle. Sweep tracks your firm’s conditions on each account.", "Ça dépend de la firme : certaines comptent les jours gagnants ou tradés depuis le dernier payout, d’autres suivent un cycle fixe. Sweep suit les conditions de ta firme sur chaque compte.", "Depende de la firma: algunas cuentan los días ganadores u operados desde el último payout y otras usan un ciclo fijo. Sweep sigue las condiciones de tu firma en cada cuenta."))]},
 "expectancy-calculator.html": {
  "steps": [T("Enter your win rate over a meaningful sample, for example your last 50 or 100 trades.", "Entre ton taux de réussite sur un échantillon parlant, par exemple tes 50 ou 100 derniers trades.", "Introduce tu tasa de acierto en una muestra representativa, por ejemplo tus últimas 50 o 100 operaciones."),
            T("Enter your average win and average loss in dollars, after commissions.", "Entre ton gain moyen et ta perte moyenne en dollars, après commissions.", "Introduce tu ganancia media y tu pérdida media en dólares, después de comisiones."),
            T("Read your expectancy per trade, per 100 trades and in R, with the break-even win rate and the profit factor.", "Lis ton espérance par trade, pour 100 trades et en R, avec le taux de réussite d’équilibre et le profit factor.", "Lee tu esperanza por operación, por 100 operaciones y en R, con la tasa de acierto de equilibrio y el profit factor.")],
  "example": T("<p>The $42.50 per trade above is $42.50 ÷ $250 = 0.17 R. The break-even win rate is 250 ÷ (400 + 250) = 38.5%: below it, the same average win and loss lose money. The profit factor is (0.45 × 400) ÷ (0.55 × 250) = 1.31.</p>",
               "<p>Les 42,50 $ par trade ci-dessus, c’est 42,50 $ ÷ 250 $ = 0,17 R. Le taux de réussite d’équilibre est de 250 ÷ (400 + 250) = 38,5 % : en dessous, le même gain moyen et la même perte moyenne perdent de l’argent. Le profit factor est de (0,45 × 400) ÷ (0,55 × 250) = 1,31.</p>",
               "<p>Los 42,50 $ por operación de arriba son 42,50 $ ÷ 250 $ = 0,17 R. La tasa de acierto de equilibrio es 250 ÷ (400 + 250) = 38,5 %: por debajo, la misma ganancia y pérdida medias pierden dinero. El profit factor es (0,45 × 400) ÷ (0,55 × 250) = 1,31.</p>"),
  "mistakes": [(T("Judging on too few trades.", "Juger sur trop peu de trades.", "Juzgar con muy pocas operaciones."),
                T("Ten trades say little. Wait for dozens before trusting the number.", "Dix trades ne disent pas grand-chose. Attends quelques dizaines de trades avant de te fier au chiffre.", "Diez operaciones dicen poco. Espera a tener decenas antes de fiarte del número.")),
               (T("Mixing setups.", "Mélanger les setups.", "Mezclar setups."),
                T("One average over several strategies hides which one earns. Measure each setup on its own.", "Une moyenne sur plusieurs stratégies cache celle qui rapporte. Mesure chaque setup séparément.", "Una media de varias estrategias oculta cuál gana. Mide cada setup por separado.")),
               (T("Leaving out costs.", "Oublier les frais.", "Olvidar los costes."),
                T("Commissions and fees lower every trade. Use your net results.", "Les commissions et les frais réduisent chaque trade. Utilise tes résultats nets.", "Las comisiones y los costes reducen cada operación. Usa tus resultados netos."))],
  "faq": [(T("What is a good expectancy?", "Qu’est-ce qu’une bonne espérance ?", "¿Qué es una buena esperanza?"),
           T("Any positive expectancy over a large sample means the process made money. Compare it in R rather than in dollars to judge across account sizes.", "Toute espérance positive sur un grand échantillon veut dire que le processus a rapporté. Compare-la en R plutôt qu’en dollars pour juger d’une taille de compte à l’autre.", "Cualquier esperanza positiva en una muestra grande significa que el proceso ganó dinero. Compárala en R y no en dólares para juzgar entre tamaños de cuenta.")),
          (T("What’s the difference between expectancy and profit factor?", "Quelle différence entre espérance et profit factor ?", "¿Qué diferencia hay entre esperanza y profit factor?"),
           T("Expectancy is the average result per trade. Profit factor is total gains ÷ total losses. A profit factor above 1 means a positive expectancy.", "L’espérance est le résultat moyen par trade. Le profit factor est le total des gains ÷ le total des pertes. Un profit factor supérieur à 1 veut dire une espérance positive.", "La esperanza es el resultado medio por operación. El profit factor es el total de ganancias ÷ el total de pérdidas. Un profit factor mayor que 1 significa una esperanza positiva."))]},
 "prop-firm-roi-calculator.html": {
  "steps": [T("Enter the evaluations you bought and their price, then your resets and their price.", "Entre les évaluations achetées et leur prix, puis tes resets et leur prix.", "Introduce las evaluaciones compradas y su precio, y luego tus reinicios y su precio."),
            T("Add activation and data fees.", "Ajoute les frais d’activation et de données.", "Añade las cuotas de activación y de datos."),
            T("Enter the payouts you actually received. You get your net, your return on fees and your ROI.", "Entre les payouts réellement reçus. Tu obtiens ton net, ton rendement sur frais et ton ROI.", "Introduce los payouts que recibiste de verdad. Obtienes tu neto, tu rendimiento sobre cuotas y tu ROI.")],
  "example": T("<p>Three evaluations at $150, two resets at $100 and $150 of activation fees add up to $800. With $2,000 of payouts received, the net is $1,200: a 2.5× return on fees, or an ROI of 150%.</p>",
               "<p>Trois évaluations à 150 $, deux resets à 100 $ et 150 $ de frais d’activation font 800 $. Avec 2 000 $ de payouts reçus, le net est de 1 200 $ : un rendement de 2,5× sur les frais, soit un ROI de 150 %.</p>",
               "<p>Tres evaluaciones a 150 $, dos reinicios a 100 $ y 150 $ de activación suman 800 $. Con 2.000 $ de payouts recibidos, el neto es de 1.200 $: un rendimiento de 2,5× sobre las cuotas, o un ROI del 150 %.</p>"),
  "mistakes": [(T("Counting account profit instead of payouts.", "Compter le profit du compte au lieu des payouts.", "Contar el beneficio de la cuenta en lugar de los payouts."),
                T("Only money actually paid out is real. Profit still on the account can be lost.", "Seul l’argent vraiment versé est réel. Le profit encore sur le compte peut être perdu.", "Solo el dinero pagado de verdad es real. El beneficio que sigue en la cuenta se puede perder.")),
               (T("Forgetting small fees.", "Oublier les petits frais.", "Olvidar las cuotas pequeñas."),
                T("Activations, data fees and monthly renewals add up over a year.", "Les activations, les frais de données et les renouvellements mensuels s’additionnent sur un an.", "Las activaciones, los datos y las renovaciones mensuales suman mucho en un año.")),
               (T("Leaving out failed evaluations.", "Exclure les évaluations ratées.", "Dejar fuera las evaluaciones fallidas."),
                T("Every evaluation and reset you paid for is part of the cost of your payouts.", "Chaque évaluation et chaque reset payés font partie du coût de tes payouts.", "Cada evaluación y cada reinicio pagados forman parte del coste de tus payouts."))],
  "faq": [(T("What’s the difference between ROI and return on fees?", "Quelle différence entre ROI et rendement sur frais ?", "¿Qué diferencia hay entre ROI y rendimiento sobre cuotas?"),
           T("Return on fees is payouts ÷ total spent: 2.5× means $2.50 back for every $1 spent. ROI is net ÷ total spent: 150% means you earned one and a half times what you spent, on top of getting it back.", "Le rendement sur frais, c’est payouts ÷ total dépensé : 2,5× veut dire 2,50 $ reçus pour chaque dollar dépensé. Le ROI, c’est net ÷ total dépensé : 150 % veut dire que tu as gagné une fois et demie ta dépense, en plus de la récupérer.", "El rendimiento sobre cuotas es payouts ÷ total gastado: 2,5× significa 2,50 $ por cada dólar gastado. El ROI es neto ÷ total gastado: 150 % significa que ganaste una vez y media lo gastado, además de recuperarlo.")),
          (T("Which period should I use?", "Quelle période utiliser ?", "¿Qué periodo debo usar?"),
           T("The same one for costs and payouts: a month, a quarter or a year. Mixing periods makes the return look better or worse than it is.", "La même pour les frais et les payouts : un mois, un trimestre ou un an. Mélanger les périodes rend le rendement meilleur ou pire qu’il ne l’est.", "El mismo para costes y payouts: un mes, un trimestre o un año. Mezclar periodos hace que el rendimiento parezca mejor o peor de lo que es."))]},
}

# phones: while you type, the result stays in a bar at the bottom of the screen (in place of the signup bar)
BAR_JS = """<script>(function(){var c=document.querySelector('[data-calc]'),bar=document.querySelector('.calc-bar');if(!c||!bar||!('IntersectionObserver' in window))return;
var big=c.querySelector('.big'),x=big.querySelector('.num'),y=x.nextElementSibling,n=bar.querySelector('.num'),l=bar.querySelector('.lbl'),inForm=false,seen=false,used=false;
function sync(){n.textContent=x.textContent;n.className=x.className;l.textContent=y?y.textContent:'';}
function show(){var on=used&&inForm&&!seen;bar.classList.toggle('on',on);}
c.addEventListener('focusin',function(){used=true;show();});
var last=x._mine=x.textContent;   // a new result rolls from the one on screen (site.js, sweepRoll); its own steps are only copied to the bar
new MutationObserver(function(){var now=x.textContent;if(now!==x._mine&&now!==last&&window.sweepRoll){var from=x._mine;last=now;window.sweepRoll(x,now,from);}sync();}).observe(big,{subtree:true,childList:true,characterData:true,attributes:true});sync();
new IntersectionObserver(function(es){es.forEach(function(e){inForm=e.isIntersecting;show();});}).observe(c.querySelector('.calc-form'));
new IntersectionObserver(function(es){es.forEach(function(e){seen=e.isIntersecting;show();});},{threshold:.6}).observe(big);})();</script>"""

def _tool_page(lang, t, slug, h1, lead, form, results, script, howto, faqs):
    """A calculator: the form and the result side by side in one card, the action under the result, then how it works."""
    NO_DOCK.add(slug)
    hero = ui.hero(t, T("Free tools","Outils gratuits","Herramientas gratuitas"), h1, lead, cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_tool_hero"'))
    h = HELP[slug]; faqs = faqs + h["faq"]
    loc = lambda x: re.sub(r'href="@([^"]+)"', lambda m: f'href="{href(lang, m.group(1))}"', x)
    act = (f'<div class="calc-act"><b>{t(T("Track this automatically in Sweep","Suis ça automatiquement dans Sweep","Síguelo automáticamente en Sweep"))}</b>'
           f'<p data-nolinks>{t(ACT[slug])}</p>{ui.btn(t(CREATE_FREE), SIGNUP, attrs='data-track="signup_tool"')}</div>')
    calc = (f'<div class="calc" data-calc="{slug}"><div class="calc-form">{form}</div><div class="calc-out" aria-live="polite">{results}{act}</div></div>'
            f'<p class="fine calc-note">{note(lang, t)}</p><div class="calc-bar" aria-hidden="true"><span class="num"></span><span class="lbl"></span></div>')
    article = (f'<h2>{t(T("How to use it","Comment l’utiliser","Cómo usarla"))}</h2><ol>{"".join(f"<li>{t(x)}</li>" for x in h["steps"])}</ol>'
               f'<h2>{t(T("How it works","Comment ça marche","Cómo funciona"))}</h2>{t(howto)}'
               f'<h2>{t(T("Example","Exemple","Ejemplo"))}</h2>{t(h["example"])}'
               f'<h2>{t(T("Common mistakes","Erreurs fréquentes","Errores frecuentes"))}</h2><ul>{"".join(f"<li><b>{t(a)}</b> {loc(t(b))}</li>" for a, b in h["mistakes"])}</ul>')
    others = ('<div class="chiprow" style="margin-top:40px"><span class="eyebrow">' + t(T("More free tools","Autres outils gratuits","Más herramientas gratuitas")) + "</span>"
              + "".join(f'<a class="chip" href="{href(lang,s)}">{t(n)}</a>' for s,_,n,_ in TOOLS if s != slug) + "</div>")
    b = (ui.sec(calc, "t", "calculator")
         + ui.sec(f'<article class="article">{article}</article>', "n", "how", width="read")
         + ui.sec(ui.head(t, None, T("Questions","Questions","Preguntas")) + ui.qa(t, faqs) + others, "n", "faq", width="read"))
    ld = jsonld({"@context":"https://schema.org","@graph":[
        {"@type":"WebApplication","name":t(h1),"url":f"https://{DOMAIN}{href(lang,slug)}","applicationCategory":"FinanceApplication","operatingSystem":"Web","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"publisher":{"@id":f"https://{DOMAIN}/#org"}},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in faqs]}]})
    return hero + b + ui.final(lang, t) + script + BAR_JS, ld

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
{NUM_JS}var money=function(v){{return cur(v,v%1?2:0)}};
function run(){{var s=S[$('ps-sym').value],ts=s[0],tv=s[1],r=parseFloat($('ps-risk').value)||0,b=parseFloat($('ps-bal').value)||0,d=parseFloat($('ps-stop').value)||0;
var risk=mode==='pct'?b*r/100:r,ticks=stop==='pts'?d/ts:d,rpc=ticks*tv,n=rpc>0?Math.floor(risk/rpc+1e-9):0;
$('ps-out').textContent=n;$('ps-rpc').textContent=rpc>0?money(rpc):'—';$('ps-act').textContent=money(n*rpc);$('ps-tv').textContent=money(tv)+' / '+fx(ts,0,6);
$('ps-msg').textContent=(rpc>0&&n===0)?M.zero:'';}}
document.querySelectorAll('[data-calc] input,[data-calc] select').forEach(function(e){{e.addEventListener('input',run)}});
document.querySelectorAll('[data-mode]').forEach(function(b){{b.addEventListener('click',function(){{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});document.querySelector('[data-pct-only]').closest('.fld').hidden=mode!=='pct';document.querySelector('#ps-risk+em').textContent=mode==='pct'?'%':'$';run()}})}});
document.querySelectorAll('[data-stop]').forEach(function(b){{b.addEventListener('click',function(){{stop=b.dataset.stop;document.querySelectorAll('[data-stop]').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});run()}})}});
document.querySelector('[data-pct-only]').closest('.fld').hidden=true;try{{var q=new URLSearchParams(location.search).get('sym');if(q&&S[q.toUpperCase()])$('ps-sym').value=q.toUpperCase();}}catch(e){{}}run();}})();</script>'''
    howto = T("<p>Contracts = risk you accept ÷ risk per contract. The risk per contract is your stop distance in ticks × the instrument’s tick value. For example, a 10-point stop on NQ is 40 ticks × $5 = $200 per contract.</p><p>The result is rounded down, so you never risk more than you planned. If it shows 0, the same stop on the micro contract (MNQ, MES…) is ten times smaller.</p>",
              "<p>Contrats = risque accepté ÷ risque par contrat. Le risque par contrat est la distance du stop en ticks × la valeur du tick de l’instrument. Par exemple, un stop de 10 points sur NQ, c’est 40 ticks × 5 $ = 200 $ par contrat.</p><p>Le résultat est arrondi vers le bas, pour ne jamais risquer plus que prévu. S’il affiche 0, le même stop sur le contrat micro (MNQ, MES…) est dix fois plus petit.</p>",
              "<p>Contratos = riesgo aceptado ÷ riesgo por contrato. El riesgo por contrato es la distancia del stop en ticks × el valor del tick. Por ejemplo, un stop de 10 puntos en NQ son 40 ticks × 5 $ = 200 $ por contrato.</p><p>El resultado se redondea hacia abajo para no arriesgar nunca más de lo previsto. Si muestra 0, el mismo stop en el contrato micro (MNQ, MES…) es diez veces menor.</p>")
    howto = {l: howto[l] + guide_note("prop-firm-profit-targets.html", T("prop firm account sizes, profit targets and max loss","les tailles de compte, objectifs et perte max des prop firms","los tamaños de cuenta, objetivos y pérdida máx. de las prop firms"))[l] for l in LANGS}
    faqs = [(T("What is the tick value of NQ and MNQ?","Quelle est la valeur du tick de NQ et MNQ ?","¿Cuál es el valor del tick de NQ y MNQ?"),
             T("NQ moves in 0.25-point ticks worth $5 each ($20 per point). MNQ is one tenth: $0.50 per tick, $2 per point.","NQ bouge par ticks de 0,25 point valant 5 $ chacun (20 $ par point). MNQ vaut un dixième : 0,50 $ par tick, 2 $ par point.","NQ se mueve en ticks de 0,25 puntos de 5 $ cada uno (20 $ por punto). MNQ es una décima parte: 0,50 $ por tick, 2 $ por punto.")),
            (T("How much should I risk per trade?","Combien devrais-je risquer par trade ?","¿Cuánto debería arriesgar por operación?"),
             T("That’s your decision and depends on your account and its rules. Many traders define it as a fixed dollar amount or a small percentage of the balance, and keep it the same on every trade.","C’est ta décision, selon ton compte et ses règles. Beaucoup de traders la fixent en montant fixe ou en petit pourcentage du solde, et la gardent identique à chaque trade.","Es tu decisión y depende de tu cuenta y sus reglas. Muchos traders la fijan como un importe fijo o un pequeño porcentaje del saldo, y la mantienen igual en cada operación."))]
    body, ld = _tool_page(lang, t, "position-size-calculator.html", TOOLS[0][2], TOOLS[0][3], form, results, script, howto, faqs)
    return (t(T("Futures position size calculator (NQ, ES, CL, GC…) · Sweep","Calculateur de taille de position futures (NQ, ES, CL, GC…) · Sweep","Calculadora de tamaño de posición en futuros (NQ, ES, CL, GC…) · Sweep")),
            t(T("Free calculator: how many NQ, MNQ, ES, MES, CL or GC contracts to trade for your risk and stop, with official CME tick values.","Calculateur gratuit : combien de contrats NQ, MNQ, ES, MES, CL ou GC trader selon ton risque et ton stop, avec les valeurs de tick CME.","Calculadora gratuita: cuántos contratos de NQ, MNQ, ES, MES, CL o GC operar según tu riesgo y tu stop, con los valores de tick de CME.")),
            body, ld)

def guide_note(page, label):
    """« Compare every firm’s … » with a link to a guide (calculators’ explanations)."""
    return {l: {"en": "<p>Compare every firm: <a href=\"{u}\">{n}</a>.</p>", "fr": "<p>Compare toutes les firmes : <a href=\"{u}\">{n}</a>.</p>", "es": "<p>Compara todas las firmas: <a href=\"{u}\">{n}</a>.</p>"}[l].replace("{u}", href(l, page)).replace("{n}", label[l]) for l in LANGS}

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
{NUM_JS}var money=function(v){{return cur(v,0)}};
function run(){{var s=parseFloat($('dd-start').value)||0,m=parseFloat($('dd-max').value)||0,p=Math.max(parseFloat($('dd-peak').value)||0,s),c=parseFloat($('dd-cur').value)||0,lock=$('dd-lock').checked;
var thr=p-m,locked=false;if(lock&&thr>=s){{thr=s;locked=true;}}var room=c-thr,used=m>0?Math.min(100,Math.max(0,(1-room/m)*100)):0;
$('dd-thr').textContent=money(thr);var sb=$('dd-sub');sb.textContent=sb.getAttribute('data-base')+(locked?' · '+L.locked:'');$('dd-room').textContent=money(room);$('dd-used').textContent=pc(Math.round(used),0);
var k=room<=0?'out':(used>=75?'near':'ok');$('dd-st').textContent=L[k];$('dd-st').className='st-'+k;$('dd-bar').style.setProperty('--p',used);$('dd-bar').className='bar-'+k;}}
document.querySelectorAll('[data-calc] input').forEach(function(e){{e.addEventListener('input',run)}});run();}})();</script>'''
    howto = T("<p>With a trailing drawdown, your liquidation level follows your highest balance: it sits at that peak minus the maximum drawdown. It never moves down. Depending on the firm, the peak is measured during the day (intraday) or at the close (end of day), and the level often stops trailing once it reaches the starting balance.</p><p>Enter your peak according to your firm’s method: the intraday high for intraday trailing, the best closing balance for end-of-day.</p>",
              "<p>Avec un drawdown suiveur, ton seuil de liquidation suit ton plus haut solde : il se situe à ce sommet moins le drawdown maximum, et il ne redescend jamais. Selon la firme, le sommet est mesuré pendant la journée (intraday) ou à la clôture (fin de journée), et le seuil arrête souvent de suivre une fois arrivé au solde de départ.</p><p>Entre ton sommet selon la méthode de ta firme : le plus haut intraday pour un suivi intraday, le meilleur solde de clôture pour un suivi en fin de journée.</p>",
              "<p>Con un drawdown dinámico, tu nivel de liquidación sigue tu saldo más alto: está en ese máximo menos el drawdown máximo y nunca baja. Según la firma, el máximo se mide durante el día (intradía) o al cierre (fin de día), y el nivel suele dejar de seguir al alcanzar el saldo inicial.</p><p>Introduce tu máximo según el método de tu firma: el máximo intradía para el seguimiento intradía, el mejor saldo de cierre para el de fin de día.</p>")
    howto = {l: howto[l] + hub_note()[l] + guide_note("prop-firm-drawdown-rules.html", T("prop firm drawdown rules, compared","les règles de drawdown des prop firms, comparées","las reglas de drawdown de las prop firms, comparadas"))[l] for l in LANGS}
    faqs = [(T("What’s the difference between intraday and end-of-day trailing?","Quelle différence entre suivi intraday et fin de journée ?","¿Qué diferencia hay entre seguimiento intradía y de fin de día?"),
             T("Intraday trailing moves with your open profit during the session, so a winning trade you give back can still raise your level. End-of-day trailing only moves with your closing balance.","Le suivi intraday bouge avec ton profit latent pendant la séance : un gain rendu en cours de trade peut quand même monter ton seuil. Le suivi en fin de journée ne bouge qu’avec ton solde de clôture.","El seguimiento intradía se mueve con tu beneficio abierto durante la sesión: una ganancia devuelta puede subir igualmente tu nivel. El de fin de día solo se mueve con tu saldo de cierre.")),
            (T("Does Sweep track my drawdown automatically?","Sweep suit-il mon drawdown automatiquement ?","¿Sweep sigue mi drawdown automáticamente?"),
             T("Yes. Each prop account in Sweep has its own drawdown rule, prefilled for guidance from your firm’s preset, and its status updates with every trade.","Oui. Chaque compte prop dans Sweep a sa propre règle de drawdown, préremplie à titre indicatif à partir du préréglage de ta firme, et son statut se met à jour à chaque trade.","Sí. Cada cuenta prop en Sweep tiene su propia regla de drawdown, precargada a título indicativo desde el preajuste de tu firma, y su estado se actualiza con cada operación."))]
    body, ld = _tool_page(lang, t, "trailing-drawdown-calculator.html", TOOLS[1][2], TOOLS[1][3], form, results, script, howto, faqs)
    return (t(T("Trailing drawdown calculator for prop firm accounts · Sweep","Calculateur de drawdown suiveur pour comptes prop · Sweep","Calculadora de drawdown dinámico para prop firms · Sweep")),
            t(T("Free calculator: find your liquidation level and the room left on a trailing drawdown prop firm account, end of day or intraday.","Calculateur gratuit : trouve ton seuil de liquidation et la marge restante sur un compte prop à drawdown suiveur, fin de journée ou intraday.","Calculadora gratuita: tu nivel de liquidación y el margen restante en una cuenta de fondeo con drawdown dinámico, al cierre o intradía.")),
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
{NUM_JS}var money=function(v){{return cur(Math.max(0,v),0)}};
function run(){{var p=parseFloat($('cr-pct').value)||0,b=parseFloat($('cr-best').value)||0,tt=parseFloat($('cr-total').value)||0;
var share=tt>0?b/tt*100:0,need=p>0?b/(p/100):0,ok=tt>0&&share<=p+1e-9;
$('cr-share').textContent=tt>0?pc(share,1):'—';$('cr-st').textContent=tt>0?(ok?L.ok:L.out):'—';$('cr-st').className=ok?'st-ok':'st-out';
$('cr-need').textContent=money(need);$('cr-left').textContent=money(need-tt);$('cr-bar').style.setProperty('--p',Math.min(100,share));$('cr-bar').className=ok?'bar-ok':'bar-out';$('cr-lim').style.left=Math.min(100,p)+'%';}}
document.querySelectorAll('[data-calc] input').forEach(function(e){{e.addEventListener('input',run)}});run();}})();</script>'''
    howto = T("<p>A consistency rule limits how much of your total profit can come from a single day. With a 30% rule and a $1,500 best day, your total profit must reach at least $1,500 ÷ 0.30 = $5,000 before you qualify.</p><p>The fix is never a bigger day: it’s more ordinary days. Some firms apply the rule to evaluations, others to payouts, with different percentages.</p>",
              "<p>Une règle de consistance limite la part de ton profit total qui peut venir d’une seule journée. Avec une règle de 30 % et une meilleure journée de 1 500 $, ton profit total doit atteindre au moins 1 500 $ ÷ 0,30 = 5 000 $ pour être admissible.</p><p>La solution n’est jamais une plus grosse journée : ce sont plus de journées ordinaires. Certaines firmes appliquent la règle aux évaluations, d’autres aux payouts, avec des pourcentages différents.</p>",
              "<p>Una regla de consistencia limita qué parte de tu beneficio total puede venir de un solo día. Con una regla del 30 % y un mejor día de 1.500 $, tu beneficio total debe llegar al menos a 1.500 $ ÷ 0,30 = 5.000 $ para calificar.</p><p>La solución nunca es un día más grande: son más días normales. Algunas firmas aplican la regla a las evaluaciones y otras a los payouts, con porcentajes distintos.</p>")
    howto = {l: howto[l] + guide_note("prop-firm-consistency-rules.html", T("prop firm consistency rules, compared","les règles de consistance des prop firms, comparées","las reglas de consistencia de las prop firms, comparadas"))[l] for l in LANGS}
    faqs = [(T("Why do prop firms use a consistency rule?","Pourquoi les prop firms ont-elles une règle de consistance ?","¿Por qué las prop firms usan una regla de consistencia?"),
             T("To make sure results come from a repeatable process rather than one outsized day.","Pour s’assurer que les résultats viennent d’un processus répétable plutôt que d’une seule journée hors norme.","Para asegurarse de que los resultados vienen de un proceso repetible y no de un único día excepcional.")),
            (T("Does Sweep check consistency for me?","Sweep vérifie-t-il la consistance pour moi ?","¿Sweep revisa la consistencia por mí?"),
             T("Yes. Consistency is one of the rules Sweep tracks on each prop account, with the percentage prefilled for guidance from your firm’s preset.","Oui. La consistance fait partie des règles que Sweep suit sur chaque compte prop, avec le pourcentage prérempli à titre indicatif à partir du préréglage de ta firme.","Sí. La consistencia es una de las reglas que Sweep sigue en cada cuenta prop, con el porcentaje precargado a título indicativo desde el preajuste de tu firma."))]
    body, ld = _tool_page(lang, t, "consistency-rule-calculator.html", TOOLS[2][2], TOOLS[2][3], form, results, script, howto, faqs)
    return (t(T("Consistency rule calculator for prop firm payouts · Sweep","Calculateur de règle de consistance pour prop firms · Sweep","Calculadora de regla de consistencia para prop firms · Sweep")),
            t(T("Free calculator: check your best day against your prop firm’s consistency rule and see how much more profit you need before a payout.","Calculateur gratuit : compare ta meilleure journée à la règle de consistance de ta prop firm et vois le profit qu’il te manque avant un payout.","Calculadora gratuita: compara tu mejor día con la regla de consistencia de tu prop firm y mira cuánto beneficio te falta antes de un payout.")),
            body, ld)

def page_tools(lang, t):
    hero = ui.hero(t, T("Free tools","Outils gratuits","Herramientas gratuitas"), T("Free tools for futures and prop traders.","Outils gratuits pour traders de futures et de prop firms.","Herramientas gratuitas para traders de futuros y de fondeo."),
        T("Quick answers before you take the trade. No account needed.","Des réponses rapides avant de prendre le trade. Sans compte.","Respuestas rápidas antes de entrar en la operación. Sin cuenta."),
        cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_tools_hero"'))
    cards = ui.cards([ui.card(t, n, d, icon=ic, more=T("Open","Ouvrir","Abrir"), url=href(lang, s)) for s, ic, n, d in TOOLS], cols=3)
    b = ui.sec(cards + f'<div class="links">{ui.go(lang, t, "prop-firms/index.html", T("Each firm’s rules, explained","Les règles de chaque firme, expliquées","Las reglas de cada firma, explicadas"))}</div>'
               + f'<p class="fine" style="margin-top:20px">{note(lang, t)}</p>', "t", "tools")
    when = [(T("Before the session.","Avant la séance.","Antes de la sesión."),
             T("Size each setup with the {ps}, and check the room left above your max loss with the {dd}.","Calcule la taille de chaque setup avec le {ps}, et vérifie la marge restante au-dessus de ta perte max avec le {dd}.","Calcula el tamaño de cada setup con la {ps} y revisa el margen que te queda sobre tu pérdida máx. con la {dd}.")),
            (T("During an evaluation.","Pendant une évaluation.","Durante una evaluación."),
             T("After a big day, the {cr} tells you how much more profit you need to stay within the limit.","Après une grosse journée, le {cr} te dit combien de profit il te manque pour rester dans la limite.","Tras un día grande, la {cr} te dice cuánto beneficio te falta para seguir dentro del límite.")),
            (T("Before a payout.","Avant un payout.","Antes de un payout."),
             T("The {po} shows what you can request after your firm’s cushion, between its minimum and maximum.","Le {po} montre ce que tu peux demander après le coussin de ta firme, entre son minimum et son maximum.","La {po} muestra lo que puedes pedir tras el colchón de tu firma, entre su mínimo y su máximo.")),
            (T("Once a month.","Une fois par mois.","Una vez al mes."),
             T("Review your expectancy on your recent trades with the {ex}, and your real net after evaluations and resets with the {ro}.","Revois ton espérance sur tes trades récents avec le {ex}, et ton vrai net après évaluations et resets avec le {ro}.","Revisa tu esperanza en tus operaciones recientes con la {ex}, y tu neto real tras evaluaciones y reinicios con la {ro}."))]
    names = {k: f'<a href="{href(lang, p_)}">{t(n)[0].lower() + t(n)[1:]}</a>' for k, (p_, _, n, _) in zip(("ps", "dd", "cr", "ex", "ro", "po"), TOOLS)}   # « the position size calculator »
    guide = (f'<h2>{t(T("When to use them","Quand les utiliser","Cuándo usarlas"))}</h2><ul>'
             + "".join(f"<li><b>{t(h)}</b> {t(d).format(**names)}</li>" for h, d in when) + "</ul>"
             + f'<h2>{t(T("Where the numbers come from","D’où viennent les chiffres","De dónde salen las cifras"))}</h2>'
             + t(T(f"<p>Tick sizes and tick values come from the CME contract specifications: see the <a href=\"{href('en', 'futures-contracts.html')}\">contract specs</a>. Prop firm rules differ from one firm to the next and change: enter your own firm’s numbers, or check the <a href=\"{href('en', 'prop-firms/index.html')}\">rules of each firm</a>, which Sweep checks against their official pages every week.</p><p>The calculators run in your browser: what you type isn’t sent or saved, and you don’t need an account.</p>",
                   f"<p>Les tailles et valeurs de tick viennent des spécifications des contrats du CME : vois les <a href=\"{href('fr', 'futures-contracts.html')}\">fiches contrats</a>. Les règles des prop firms diffèrent d’une firme à l’autre et changent : entre les chiffres de ta propre firme, ou consulte les <a href=\"{href('fr', 'prop-firms/index.html')}\">règles de chaque firme</a>, que Sweep vérifie chaque semaine sur leurs pages officielles.</p><p>Les calculateurs fonctionnent dans ton navigateur : ce que tu entres n’est ni envoyé ni enregistré, et tu n’as pas besoin de compte.</p>",
                   f"<p>Los tamaños y valores del tick vienen de las especificaciones de los contratos de CME: mira las <a href=\"{href('es', 'futures-contracts.html')}\">fichas de contratos</a>. Las reglas de las prop firms cambian de una firma a otra y con el tiempo: introduce las cifras de tu propia firma o consulta las <a href=\"{href('es', 'prop-firms/index.html')}\">reglas de cada firma</a>, que Sweep revisa cada semana en sus páginas oficiales.</p><p>Las calculadoras funcionan en tu navegador: lo que escribes no se envía ni se guarda, y no necesitas cuenta.</p>")))
    faqs = [(T("Are these calculators free?","Ces calculateurs sont-ils gratuits ?","¿Estas calculadoras son gratuitas?"),
             T("Yes, all of them, with no account and no limit.","Oui, tous, sans compte et sans limite.","Sí, todas, sin cuenta y sin límite.")),
            (T("Can Sweep do these calculations for me?","Sweep peut-il faire ces calculs pour moi ?","¿Sweep puede hacer estos cálculos por mí?"),
             T("Yes. In Sweep, your trades fill in the numbers: risk per trade, room left above the max loss, consistency and payout conditions update with every trade.","Oui. Dans Sweep, tes trades remplissent les chiffres : risque par trade, marge restante au-dessus de la perte max, consistance et conditions de payout se mettent à jour à chaque trade.","Sí. En Sweep, tus operaciones rellenan las cifras: el riesgo por operación, el margen sobre la pérdida máx., la consistencia y las condiciones de payout se actualizan con cada operación."))]
    b += ui.sec(f'<article class="article">{guide}</article>' + ui.head(t, None, T("Questions","Questions","Preguntas")) + ui.qa(t, faqs), "n", "when", width="read")   # two questions: under the text, not a section of their own
    ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(x)}} for q, x in faqs]})
    return (t(T("Free futures and prop firm calculators · Sweep","Calculateurs gratuits pour futures et prop firms · Sweep","Calculadoras gratuitas para futuros y prop firms · Sweep")),
            t(T("Free position size, trailing drawdown, consistency, payout, expectancy and prop firm ROI calculators for futures and prop firm traders.","Calculateurs gratuits : taille de position, drawdown suiveur, consistance, payout, espérance et rentabilité prop, pour traders de futures.","Calculadoras gratuitas: tamaño de posición, drawdown dinámico, consistencia, payout, esperanza y rentabilidad prop, para traders de futuros.")),
            hero + b + ui.final(lang, t), ld)
SYSTEM_PAGES.add("tools.html")

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
    body, ld = _tool_page(lang, t, s, n, d, form, results, f"<script>(function(){{var $=function(i){{return document.getElementById(i)}},money=function(v){{return cur(v,Math.abs(v)%1?2:0)}};{NUM_JS}{js}document.querySelectorAll('[data-calc] input').forEach(function(e){{e.addEventListener('input',run)}});run();}})();</script>", howto, faqs)
    return (t(title), t(desc), body, ld)

def page_expectancy(lang, t):
    form = _num("ex-wr", t(T("Win rate","Taux de réussite","Tasa de acierto")), 45, "any", "%") + _num("ex-w", t(T("Average win","Gain moyen","Ganancia media")), 400, "any", "$") + _num("ex-l", t(T("Average loss","Perte moyenne","Pérdida media")), 250, "any", "$")
    res = (f'<div class="big"><span class="num" id="ex-e">—</span><span>{t(T("per trade, on average","par trade, en moyenne","por operación, de media"))}</span></div>'
           f'<dl><div><dt>{t(T("Per 100 trades","Pour 100 trades","Por 100 operaciones"))}</dt><dd class="num" id="ex-100">—</dd></div><div><dt>{t(T("In R (risk = average loss)","En R (risque = perte moyenne)","En R (riesgo = pérdida media)"))}</dt><dd class="num" id="ex-r">—</dd></div><div><dt>{t(T("Break-even win rate","Taux de réussite d’équilibre","Tasa de acierto de equilibrio"))}</dt><dd class="num" id="ex-be">—</dd></div><div><dt>Profit factor</dt><dd class="num" id="ex-pf">—</dd></div></dl>')
    js = "function run(){var w=(parseFloat($('ex-wr').value)||0)/100,aw=parseFloat($('ex-w').value)||0,al=parseFloat($('ex-l').value)||0;var e=w*aw-(1-w)*al;$('ex-e').textContent=money(e);$('ex-e').className='num '+(e>=0?'st-ok':'st-out');$('ex-100').textContent=money(e*100);$('ex-r').textContent=al>0?dec(e/al,2)+' R':'—';$('ex-be').textContent=(aw+al)>0?pc(al/(aw+al)*100,1):'—';$('ex-pf').textContent=(1-w)*al>0?dec(w*aw/((1-w)*al),2):'—';}"
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
    js = "function run(){var v=function(i){return parseFloat($(i).value)||0};var sp=v('ro-ev')*v('ro-evp')+v('ro-rs')*v('ro-rsp')+v('ro-act'),p=v('ro-pay'),n=p-sp;$('ro-net').textContent=money(n);$('ro-net').className='num '+(n>=0?'st-ok':'st-out');$('ro-sp').textContent=money(sp);$('ro-x').textContent=sp>0?dec(p/sp,1)+'×':'—';$('ro-roi').textContent=sp>0?pc(Math.round(n/sp*100),0):'—';}"
    howto = T("<p>Net = payouts received − everything you paid: evaluations, resets, activations and data fees. Return on fees = payouts ÷ total spent: 3.0× means every dollar spent came back three times.</p>",
              "<p>Net = payouts reçus − tout ce que tu as payé : évaluations, resets, activations et frais de données. Rendement sur frais = payouts ÷ total dépensé : 3,0× veut dire que chaque dollar dépensé est revenu trois fois.</p>",
              "<p>Neto = payouts recibidos − todo lo pagado: evaluaciones, reinicios, activaciones y datos. Rendimiento sobre cuotas = payouts ÷ total gastado: 3,0× significa que cada dólar gastado volvió tres veces.</p>")
    faqs = [(T("Does Sweep track this automatically?","Sweep calcule-t-il ça automatiquement ?","¿Sweep lo calcula automáticamente?"),
             T("Yes. Log your expenses and payouts in Sweep and your net after fees is always one line, by firm and by account.","Oui. Note tes dépenses et tes payouts dans Sweep et ton net après frais tient toujours en une ligne, par firme et par compte.","Sí. Registra tus gastos y payouts en Sweep y tu neto tras cuotas siempre cabe en una línea, por firma y por cuenta."))]
    return _simple_tool(lang, t, 4, form, res, js, howto, faqs,
        T("Prop firm ROI calculator: net after evaluations and resets · Sweep","Calculateur de rentabilité prop : net après frais · Sweep","Calculadora de rentabilidad prop: neto tras cuotas · Sweep"),
        T("Free calculator: what prop trading really pays you after evaluations, resets, activation and data fees, with your return on fees.","Calculateur gratuit : ce que le trading prop te rapporte vraiment après évaluations, resets, activation et frais de données.","Calculadora gratuita: lo que el trading prop te deja realmente tras evaluaciones, reinicios, activación y datos, con tu retorno sobre los costes."))

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
    howto = {l: howto[l] + hub_note()[l] + guide_note("prop-firm-payout-rules.html", T("prop firm payout rules, compared","les règles de payout des prop firms, comparées","las reglas de payout de las prop firms, comparadas"))[l] for l in LANGS}
    faqs = [(T("Why can’t I withdraw my whole profit?","Pourquoi je ne peux pas retirer tout mon profit ?","¿Por qué no puedo retirar todo mi beneficio?"),
             T("Firms often require a cushion above the starting balance and cap each payout. Always check your firm’s current rules.","Les firmes exigent souvent un coussin au-dessus du solde de départ et plafonnent chaque payout. Vérifie toujours les règles actuelles de ta firme.","Las firmas suelen exigir un colchón sobre el saldo inicial y limitan cada payout. Verifica siempre las reglas actuales de tu firma."))]
    return _simple_tool(lang, t, 5, form, res, js, howto, faqs,
        T("Prop firm payout calculator: what can you request? · Sweep","Calculateur de payout prop : combien retirer ? · Sweep","Calculadora de payout prop: ¿cuánto puedes pedir? · Sweep"),
        T("Free calculator: the payout you can request after your firm’s cushion, within the minimum and maximum per request, for any prop firm.","Calculateur gratuit : le payout que tu peux demander après le coussin de ta firme, entre le minimum et le maximum, pour toute prop firm.","Calculadora gratuita: el payout que puedes pedir tras el colchón de tu firma, entre el mínimo y el máximo, para cualquier prop firm."))

SYSTEM_PAGES.update(s for s, _, _, _ in TOOLS)
