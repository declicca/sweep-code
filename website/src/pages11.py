from core import *

# Platforms whose CSV file the app imports directly. Every other platform: screenshot (Sweep AI).
IMPORT_CSV = {"tradovate", "rithmic", "projectx", "tradingview"}

PLATFORMS = [
 ("tradovate", "Tradovate", T("Also used by many prop firms through Tradovate and TradingView.","Utilisé aussi par beaucoup de prop firms via Tradovate et TradingView.","También usado por muchas prop firms a través de Tradovate y TradingView."), [
   T("Set your Tradovate time zone to <b>New York</b>, so times match Sweep.","Règle le fuseau horaire de Tradovate sur <b>New York</b>, pour que les heures concordent avec Sweep.","Pon la zona horaria de Tradovate en <b>Nueva York</b> para que las horas coincidan con Sweep."),
   T("Open <b>Account Reports</b>, then the <b>Performance</b> tab.","Ouvre <b>Account Reports</b>, puis l’onglet <b>Performance</b>.","Abre <b>Account Reports</b> y luego la pestaña <b>Performance</b>."),
   T("Choose the account and the dates, then click <b>Go</b>.","Choisis le compte et les dates, puis clique sur <b>Go</b>.","Elige la cuenta y las fechas y haz clic en <b>Go</b>."),
   T("Click <b>Download CSV</b>.","Clique sur <b>Download CSV</b>.","Haz clic en <b>Download CSV</b>.")]),
 ("projectx", "TopstepX / ProjectX", T("The platform used by Topstep and other firms built on ProjectX.","La plateforme de Topstep et des autres firmes construites sur ProjectX.","La plataforma de Topstep y otras firmas basadas en ProjectX."), [
   T("Open the <b>Trades</b> tab.","Ouvre l’onglet <b>Trades</b>.","Abre la pestaña <b>Trades</b>."),
   T("Click <b>Export</b>, bottom right.","Clique sur <b>Export</b>, en bas à droite.","Haz clic en <b>Export</b>, abajo a la derecha."),
   T("Save the file as <b>CSV</b>.","Enregistre le fichier en <b>CSV</b>.","Guarda el archivo en <b>CSV</b>.")]),
 ("rithmic", "Rithmic · R | Trader Pro", T("Used by many futures prop firms.","Utilisé par beaucoup de prop firms de futures.","Usado por muchas prop firms de futuros."), [
   T("Open <b>Recent Orders</b>, or <b>Order History</b> for older trades.","Ouvre <b>Recent Orders</b>, ou <b>Order History</b> pour les trades plus anciens.","Abre <b>Recent Orders</b>, u <b>Order History</b> para operaciones antiguas."),
   T("Select the account and the date. One day per export.","Choisis le compte et la date. Un jour par export.","Elige la cuenta y la fecha. Un día por exportación."),
   T("In <b>Completed Orders</b>, right-click a column heading → <b>Add/Remove columns</b> → add <b>Qty Filled</b>.","Dans <b>Completed Orders</b>, clic droit sur un titre de colonne → <b>Add/Remove columns</b> → ajoute <b>Qty Filled</b>.","En <b>Completed Orders</b>, clic derecho en un título de columna → <b>Add/Remove columns</b> → añade <b>Qty Filled</b>."),
   T("Click <b>Export as CSV</b>.","Clique sur <b>Export as CSV</b>.","Haz clic en <b>Export as CSV</b>.")]),
 ("tradingview", "TradingView", T("Trading from TradingView with a connected broker.","Si tu trades depuis TradingView avec un courtier connecté.","Si operas desde TradingView con un bróker conectado."), [
   T("Open the <b>Trading Panel</b> at the bottom of the chart.","Ouvre le <b>Trading Panel</b> en bas du graphique.","Abre el <b>Trading Panel</b> en la parte inferior del gráfico."),
   T("Go to the <b>Order History</b> tab.","Va dans l’onglet <b>Order History</b>.","Ve a la pestaña <b>Order History</b>."),
   T("Use the panel’s export option to save the history as <b>CSV</b>.","Utilise l’option d’export du panneau pour enregistrer l’historique en <b>CSV</b>.","Usa la opción de exportar del panel para guardar el historial en <b>CSV</b>."),
   T("In Sweep, pick the time zone of the file when you import it.","Dans Sweep, choisis le fuseau horaire du fichier à l’import.","En Sweep, elige la zona horaria del archivo al importarlo.")]),
 ("ninjatrader", "NinjaTrader 8", T("Desktop platform, with Rithmic or Tradovate connections. Simplest: <a href=\"@ninjatrader.html\">connect it once in Sweep</a> (Settings › Data › Connections) and your trades arrive on their own. For trades from before, export them as below.","Plateforme de bureau, avec connexion Rithmic ou Tradovate. Le plus simple : <a href=\"@ninjatrader.html\">connecte-la une fois dans Sweep</a> (Réglages › Données › Connexions) et tes trades arrivent seuls. Pour tes trades d’avant, exporte-les comme ci-dessous.","Plataforma de escritorio, con conexión Rithmic o Tradovate. Lo más simple: <a href=\"@ninjatrader.html\">conéctala una vez en Sweep</a> (Ajustes › Datos › Conexiones) y tus operaciones llegan solas. Para tus operaciones anteriores, expórtalas como se indica abajo."), [
   T("In the Control Center, open <b>New → Trade Performance</b>.","Dans le Control Center, ouvre <b>New → Trade Performance</b>.","En el Control Center, abre <b>New → Trade Performance</b>."),
   T("Set <b>Display</b> to <b>Executions</b> and choose the dates and the account.","Règle <b>Display</b> sur <b>Executions</b> et choisis les dates et le compte.","Pon <b>Display</b> en <b>Executions</b> y elige las fechas y la cuenta."),
   T("Click <b>Generate</b>.","Clique sur <b>Generate</b>.","Haz clic en <b>Generate</b>."),
   T("Right-click the list → <b>Export</b>, and save as <b>CSV</b>.","Clic droit sur la liste → <b>Export</b>, et enregistre en <b>CSV</b>.","Clic derecho en la lista → <b>Export</b> y guarda en <b>CSV</b>.")]),
]

def page_import(lang, t):
    """Import, on the design system: how trades come in (CSV or screenshot) said once, then one card per platform."""
    import ui
    H = (T("Bring your trades from any platform.","Ramène tes trades de n’importe quelle plateforme.","Trae tus operaciones de cualquier plataforma."),
        T("On NinjaTrader 8, Sweep’s free add-on sends your trades on its own. Otherwise, import a CSV from Tradovate, Rithmic, TopstepX or TradingView, or drop a history screenshot from any platform: Sweep AI creates every trade on it at once.",
          "Sur NinjaTrader 8, le module gratuit de Sweep envoie tes trades tout seul. Sinon, importe un CSV de Tradovate, Rithmic, TopstepX ou TradingView, ou dépose une capture d’historique de n’importe quelle plateforme : Sweep AI crée tous ses trades d’un coup.",
          "En NinjaTrader 8, el complemento gratuito de Sweep envía tus operaciones solo. Si no, importa un CSV de Tradovate, Rithmic, TopstepX o TradingView, o sube una captura del historial de cualquier plataforma: Sweep AI crea todas sus operaciones de una vez."),
        T("Import","Importer","Importar"))
    INTO = {True: T("In Sweep: <b>Trades → Import CSV</b>, choose the file. Fees come from the file, or from your account’s commission. A Rithmic file with several accounts goes to each matching account.","Dans Sweep : <b>Trades → Importer un CSV</b>, choisis le fichier. Les frais viennent du fichier, sinon de la commission de ton compte. Un fichier Rithmic à plusieurs comptes va vers chaque compte correspondant.","En Sweep: <b>Operaciones → Importar CSV</b>, elige el archivo. Las comisiones vienen del archivo o de la comisión de tu cuenta. Un archivo de Rithmic con varias cuentas va a cada cuenta correspondiente."),
            False: T("In Sweep: add a <b>screenshot of your trade history</b>; Sweep AI creates every trade on it at once. Keep the CSV as your backup.","Dans Sweep : ajoute une <b>capture de ton historique de trades</b> ; Sweep AI crée tous les trades d’un coup. Garde le CSV comme sauvegarde.","En Sweep: añade una <b>captura de tu historial</b>; Sweep AI crea todas las operaciones de una vez. Guarda el CSV como copia.")}
    CSV, SHOT = T("CSV import","Import CSV","Importación CSV"), T("By screenshot","Par capture","Por captura")
    def badge(csv, key=""):
        if key == "ninjatrader": return f'<span class="chip tint">{t(T("Auto sync","Synchro auto","Sincro automática"))}</span>'   # its trades arrive on their own
        return f'<span class="chip{" tint" if csv else ""}">{t(CSV if csv else SHOT)}</span>'
    how = ui.cards([ui.card(t, CSV, INTO[True], "download"), ui.card(t, SHOT, INTO[False], "image")], 2)
    plats = [ui.Card("text", f'<article class="card plat" id="{key}"><div class="plat-h"><h3>{name.replace(" | ", "\u00a0|\u00a0")}</h3>{badge(key in IMPORT_CSV, key)}</div><p>{localize(lang, t(note))}</p>'
                     f'<h4>{t(T("Export your trades","Exporter tes trades","Exportar tus operaciones"))}</h4><ol class="psteps">' + "".join(f"<li>{t(x)}</li>" for x in steps) + "</ol></article>")
             for key, name, note, steps in PLATFORMS]
    anyp = ui.Card("text", f'<article class="card plat" id="any"><div class="plat-h"><h3>{t(T("Any other platform","Toute autre plateforme","Cualquier otra plataforma"))}</h3>{badge(False)}</div>'
            f'<p>{t(T("Take a screenshot of the trade on your platform (or of its fills list) and paste it with Ctrl+V when you add a trade. Sweep AI reads the symbol, side, contracts, times, prices and fees, and shows your net P&L and R. You check and save.","Fais une capture du trade sur ta plateforme (ou de la liste des exécutions) et colle-la avec Ctrl+V à l’ajout d’un trade. Sweep AI lit le symbole, le sens, les contrats, les heures, les prix et les frais, et affiche ton P&L net et ton R. Tu vérifies et tu enregistres.","Haz una captura de la operación en tu plataforma (o de su lista de ejecuciones) y pégala con Ctrl+V al añadir una operación. Sweep AI lee el símbolo, el sentido, los contratos, las horas, los precios y las comisiones, y muestra tu P&L neto y tu R. Revisas y guardas."))}</p>'
            f'<p class="fine">{t(T("Copy trading? Choose “Also on” and the trade is saved on every account at once.","Copy trading ? Choisis « Aussi sur » et le trade est enregistré sur chaque compte d’un coup.","¿Copy trading? Elige «También en» y la operación se guarda en cada cuenta a la vez."))}</p></article>')
    tips = [T("Automatic sync for Rithmic and Tradovate is in development. Until then, use the CSV import or a screenshot.","La synchro automatique Rithmic et Tradovate est en développement. D’ici là, utilise l’import CSV ou une capture.","La sincronización automática con Rithmic y Tradovate está en desarrollo. Mientras tanto, usa la importación CSV o una captura."),
            T("Export one account at a time, so each trade lands on the right account.","Exporte un compte à la fois, pour que chaque trade arrive sur le bon compte.","Exporta una cuenta cada vez para que cada operación vaya a la cuenta correcta."),
            T("Most platforms limit the date range of an export: export week by week or month by month if needed.","La plupart des plateformes limitent la période d’un export : exporte semaine par semaine ou mois par mois si besoin.","La mayoría de plataformas limitan el periodo de exportación: exporta por semanas o por meses si hace falta."),
            T("Your P&L differs from your platform? Enter the real P&L (platform) on the trade, or your commission per contract on the account.","Ton P&L diffère de ta plateforme ? Entre le P&L réel (plateforme) sur le trade, ou ta commission par contrat sur le compte.","¿Tu P&L no coincide con tu plataforma? Introduce el P&L real (plataforma) en la operación, o tu comisión por contrato en la cuenta.")]
    nav = ui.subnav(t, T("Platforms","Plateformes","Plataformas"), [(k, {"en": n, "fr": n, "es": n}) for k, n, _, _ in PLATFORMS] + [("any", T("Other platforms","Autres plateformes","Otras plataformas"))])
    hero = ui.hero(t, H[2], H[0], H[1], cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True),
                   visual=ui.frame_d("v6-18-add-trade-choice-d.webp", t(T("Adding a trade: from a screenshot, in your words or from a file","Ajouter un trade : par capture, avec tes mots ou par fichier","Añadir una operación: por captura, con tus palabras o por archivo")), m="v6-18-add-trade-choice-m.webp", t=t, sizes="(max-width: 1067px) 92vw, 1320px", cls="reveal zoom"))
    b = (nav + ui.sec(how, "t", "how") + ui.sec(ui.cards(plats + [anyp], 3), "t", "platforms")
         + ui.sec(ui.head(t, None, T("Good to know","Bon à savoir","Conviene saber")) + ui.bullets(t, tips)
                  + f'<p class="fine" style="margin-top:24px">{t(T("Platform menus can change between versions. Platform names belong to their owners; Sweep isn’t affiliated with them.","Les menus des plateformes peuvent changer d’une version à l’autre. Les noms des plateformes appartiennent à leurs propriétaires ; Sweep n’y est pas affilié.","Los menús de las plataformas pueden cambiar entre versiones. Los nombres pertenecen a sus propietarios; Sweep no está afiliado a ellas."))}</p>', "n", "tips", width="read")
         + ui.final(lang, t))
    ld = jsonld({"@context":"https://schema.org","@type":"HowTo","name":t(T("How to export your trades from Tradovate, TopstepX, Rithmic, TradingView and NinjaTrader","Comment exporter tes trades de Tradovate, TopstepX, Rithmic, TradingView et NinjaTrader","Cómo exportar tus operaciones de Tradovate, TopstepX, Rithmic, TradingView y NinjaTrader")),
        "step":[{"@type":"HowToSection","name":name,"itemListElement":[{"@type":"HowToStep","position":i+1,"text":re_strip(t(s))} for i,s in enumerate(steps)]} for _,name,_,steps in PLATFORMS]})
    return (t(T("Import trades: Tradovate, TopstepX, Rithmic… · Sweep","Importer tes trades : Tradovate, TopstepX, Rithmic… · Sweep","Importar operaciones: Tradovate, TopstepX, Rithmic… · Sweep")),
            t(T("How to export your trade history from Tradovate, TopstepX, Rithmic R|Trader Pro, TradingView and NinjaTrader 8, and bring it into Sweep.","Comment exporter ton historique de Tradovate, TopstepX, Rithmic R|Trader Pro, TradingView et NinjaTrader 8, et le ramener dans Sweep.","Cómo exportar tu historial de Tradovate, TopstepX, Rithmic R|Trader Pro, TradingView y NinjaTrader 8, y llevarlo a Sweep en unos clics.")),
            hero + b, ld)

SYSTEM_PAGES.add("import.html")

def re_strip(s):
    import re
    return re.sub("<[^>]+>", "", s)
