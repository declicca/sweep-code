from core import *

# Platforms whose CSV file the app imports directly. Every other platform: screenshot (Sweep AI).
IMPORT_CSV = {"tradovate", "rithmic", "projectx", "tradingview"}
SYNCED = {"ninjatrader", "quantower"}   # an add-on sends their trades on its own (Settings › Data › Connections)
GUIDE_OF = {"tradovate": "import-tradovate.html", "projectx": "import-topstepx.html", "rithmic": "import-rithmic.html"}   # export guides, end of file

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
   T("Open <b>Orders History</b> (File → Orders History), or <b>Recent Orders</b> for today.","Ouvre <b>Orders History</b> (File → Orders History), ou <b>Recent Orders</b> pour aujourd’hui.","Abre <b>Orders History</b> (File → Orders History), o <b>Recent Orders</b> para hoy."),
   T("Pick the account and the day. One day per export.","Choisis le compte et la journée. Une journée par export.","Elige la cuenta y el día. Un día por exportación."),
   T("In <b>Completed Orders</b>, right-click a column heading → <b>Add/Remove columns</b>, and show <b>Account, Status, Buy/Sell, Symbol, Qty Filled, Avg Fill Price, Update Time</b> and <b>Commission</b>.",
     "Dans <b>Completed Orders</b>, clic droit sur un titre de colonne → <b>Add/Remove columns</b>, et affiche <b>Account, Status, Buy/Sell, Symbol, Qty Filled, Avg Fill Price, Update Time</b> et <b>Commission</b>.",
     "En <b>Completed Orders</b>, clic derecho en un título de columna → <b>Add/Remove columns</b>, y muestra <b>Account, Status, Buy/Sell, Symbol, Qty Filled, Avg Fill Price, Update Time</b> y <b>Commission</b>."),
   T("Click <b>Export as CSV</b>.","Clique sur <b>Export as CSV</b>.","Haz clic en <b>Export as CSV</b>.")]),
 ("tradingview", "TradingView", T("Trading from TradingView with a connected broker.","Si tu trades depuis TradingView avec un courtier connecté.","Si operas desde TradingView con un bróker conectado."), [
   T("Open the <b>Trading Panel</b> at the bottom of the chart.","Ouvre le <b>Trading Panel</b> en bas du graphique.","Abre el <b>Trading Panel</b> en la parte inferior del gráfico."),
   T("Go to the <b>Order History</b> tab.","Va dans l’onglet <b>Order History</b>.","Ve a la pestaña <b>Order History</b>."),
   T("Use the panel’s export option to save the history as <b>CSV</b>.","Utilise l’option d’export du panneau pour enregistrer l’historique en <b>CSV</b>.","Usa la opción de exportar del panel para guardar el historial en <b>CSV</b>."),
   T("In Sweep, pick the time zone of the file when you import it.","Dans Sweep, choisis le fuseau horaire du fichier à l’import.","En Sweep, elige la zona horaria del archivo al importarlo.")]),
 ("ninjatrader", "NinjaTrader 8", T("Desktop platform, with Rithmic or Tradovate connections. Simplest: <a href=\"@ninjatrader.html\">connect it once in Sweep</a> (Settings › Data › Connections) and your trades arrive on their own. For trades from before, NinjaTrader’s own export isn’t read: use one of these.","Plateforme de bureau, avec connexion Rithmic ou Tradovate. Le plus simple : <a href=\"@ninjatrader.html\">connecte-la une fois dans Sweep</a> (Réglages › Données › Connexions) et tes trades arrivent seuls. Pour tes trades d’avant, l’export de NinjaTrader n’est pas lu : utilise une de ces façons.","Plataforma de escritorio, con conexión Rithmic o Tradovate. Lo más simple: <a href=\"@ninjatrader.html\">conéctala una vez en Sweep</a> (Ajustes › Datos › Conexiones) y tus operaciones llegan solas. Para tus operaciones anteriores, la exportación de NinjaTrader no se lee: usa una de estas formas."), [
   T("<b>A screenshot:</b> in the Control Center, open <b>New → Trade Performance</b>, show the trades, take a screenshot and add it in Sweep: Sweep AI creates every trade at once.","<b>Une capture :</b> dans le Control Center, ouvre <b>New → Trade Performance</b>, affiche les trades, fais une capture et ajoute-la dans Sweep : Sweep AI crée tous les trades d’un coup.","<b>Una captura:</b> en el Control Center, abre <b>New → Trade Performance</b>, muestra las operaciones, haz una captura y añádela en Sweep: Sweep AI crea todas las operaciones de una vez."),
   T("<b>Your broker’s export:</b> on a Rithmic connection, export from R | Trader Pro; on a Tradovate connection, from Tradovate (their steps are above).","<b>L’export de ton courtier :</b> avec une connexion Rithmic, exporte depuis R | Trader Pro ; avec une connexion Tradovate, depuis Tradovate (leurs étapes sont plus haut).","<b>La exportación de tu bróker:</b> con una conexión Rithmic, exporta desde R | Trader Pro; con una conexión Tradovate, desde Tradovate (sus pasos están arriba).")]),
 ("quantower", "Quantower", T("Desktop platform, free version included. <a href=\"@quantower.html\">Connect it once</a> and your trades arrive on their own, from every account, with your last 7 days. Read only: the add-on never places an order. For older trades, add a screenshot of its history.","Plateforme de bureau, version gratuite comprise. <a href=\"@quantower.html\">Connecte-la une fois</a> et tes trades arrivent seuls, de tous tes comptes, avec tes 7 derniers jours. Lecture seule : le module ne passe jamais d’ordre. Pour tes trades plus anciens, ajoute une capture de son historique.","Plataforma de escritorio, versión gratuita incluida. <a href=\"@quantower.html\">Conéctala una vez</a> y tus operaciones llegan solas, de todas tus cuentas, con tus últimos 7 días. Solo lectura: el complemento nunca envía una orden. Para operaciones más antiguas, añade una captura de su historial."), [
   T("In Sweep, open <b>Settings › Data › Connections</b>, then <b>Quantower › Connect</b>. Download the add-on and copy your key: it’s shown only once.","Dans Sweep, ouvre <b>Réglages › Données › Connexions</b>, puis <b>Quantower › Connecter</b>. Télécharge le module et copie ta clé : elle n’est montrée qu’une fois.","En Sweep, abre <b>Ajustes › Datos › Conexiones</b> y luego <b>Quantower › Conectar</b>. Descarga el complemento y copia tu clave: solo se muestra una vez."),
   T("Unzip it into Quantower’s folder: <b>Settings › Scripts › plug-ins</b>, then restart Quantower.","Décompresse-le dans le dossier de Quantower : <b>Settings › Scripts › plug-ins</b>, puis redémarre Quantower.","Descomprímelo en la carpeta de Quantower: <b>Settings › Scripts › plug-ins</b> y reinicia Quantower."),
   T("In Quantower, open the <b>Sweep Sync</b> panel and paste your key.","Dans Quantower, ouvre le panneau <b>Sweep Sync</b> et colle ta clé.","En Quantower, abre el panel <b>Sweep Sync</b> y pega tu clave."),
   T("Back in Sweep, the accounts it finds show up: link them all at once.","De retour dans Sweep, les comptes trouvés s’affichent : relie-les tous d’un coup.","De vuelta en Sweep, aparecen las cuentas encontradas: vincúlalas todas de una vez.")]),
]

def page_import(lang, t):
    """Import, on the design system: how trades come in (CSV or screenshot) said once, then one card per platform."""
    import ui
    H = (T("Bring your trades from any platform.","Ramène tes trades de n’importe quelle plateforme.","Trae tus operaciones de cualquier plataforma."),
        T("On NinjaTrader 8 or Quantower, Sweep’s free add-on sends your trades on its own. Otherwise, import a CSV from Tradovate, Rithmic, TopstepX or TradingView, or drop a history screenshot from any platform: Sweep AI creates every trade on it at once.",
          "Sur NinjaTrader 8 ou Quantower, le module gratuit de Sweep envoie tes trades tout seul. Sinon, importe un CSV de Tradovate, Rithmic, TopstepX ou TradingView, ou dépose une capture d’historique de n’importe quelle plateforme : Sweep AI crée tous ses trades d’un coup.",
          "En NinjaTrader 8 o Quantower, el complemento gratuito de Sweep envía tus operaciones solo. Si no, importa un CSV de Tradovate, Rithmic, TopstepX o TradingView, o sube una captura del historial de cualquier plataforma: Sweep AI crea todas sus operaciones de una vez."),
        T("Import","Importer","Importar"))
    INTO = {True: T("In Sweep: <b>Trades → Import CSV</b>, choose the file. Fees come from the file, or from your account’s commission. A Rithmic file with several accounts goes to each matching account.","Dans Sweep : <b>Trades → Importer un CSV</b>, choisis le fichier. Les frais viennent du fichier, sinon de la commission de ton compte. Un fichier Rithmic à plusieurs comptes va vers chaque compte correspondant.","En Sweep: <b>Operaciones → Importar CSV</b>, elige el archivo. Las comisiones vienen del archivo o de la comisión de tu cuenta. Un archivo de Rithmic con varias cuentas va a cada cuenta correspondiente."),
            False: T("In Sweep: add a <b>screenshot of your trade history</b>; Sweep AI creates every trade on it at once. Keep the CSV as your backup.","Dans Sweep : ajoute une <b>capture de ton historique de trades</b> ; Sweep AI crée tous les trades d’un coup. Garde le CSV comme sauvegarde.","En Sweep: añade una <b>captura de tu historial</b>; Sweep AI crea todas las operaciones de una vez. Guarda el CSV como copia.")}
    CSV, SHOT = T("CSV import","Import CSV","Importación CSV"), T("By screenshot","Par capture","Por captura")
    def badge(csv, key=""):
        if key in SYNCED: return f'<span class="chip tint">{t(T("Auto sync","Synchro auto","Sincro automática"))}</span>'   # its trades arrive on their own
        return f'<span class="chip{" tint" if csv else ""}">{t(CSV if csv else SHOT)}</span>'
    how = ui.cards([ui.card(t, CSV, INTO[True], "download"), ui.card(t, SHOT, INTO[False], "image")], 2)
    plats = [ui.Card("text", f'<article class="card plat" id="{key}"><div class="plat-h"><h3>{name.replace(" | ", "\u00a0|\u00a0")}</h3>{badge(key in IMPORT_CSV, key)}</div><p>{localize(lang, t(note))}</p>'
                     f'<h4>{t(T("Connect it once","Connecte-la une fois","Conéctala una vez") if key == "quantower" else T("Export your trades","Exporter tes trades","Exportar tus operaciones"))}</h4><ol class="psteps">' + "".join(f"<li>{t(x)}</li>" for x in steps) + "</ol>"
                     + (f'<p class="plat-more"><a href="{href(lang, GUIDE_OF[key])}">{t(T("Step-by-step guide","Le guide pas à pas","La guía paso a paso"))}<span class="sr">, {name}</span> <span aria-hidden="true">→</span></a></p>' if key in GUIDE_OF else "") + "</article>")
             for key, name, note, steps in PLATFORMS]
    anyp = ui.Card("text", f'<article class="card plat" id="any"><div class="plat-h"><h3>{t(T("Any other platform","Toute autre plateforme","Cualquier otra plataforma"))}</h3>{badge(False)}</div>'
            f'<p>{t(T("Take a screenshot of the trade on your platform (or of its fills list) and paste it with Ctrl+V when you add a trade. Sweep AI reads the symbol, side, contracts, times, prices and fees, and shows your net P&L and R. You check and save.","Fais une capture du trade sur ta plateforme (ou de la liste des exécutions) et colle-la avec Ctrl+V à l’ajout d’un trade. Sweep AI lit le symbole, le sens, les contrats, les heures, les prix et les frais, et affiche ton P&L net et ton R. Tu vérifies et tu enregistres.","Haz una captura de la operación en tu plataforma (o de su lista de ejecuciones) y pégala con Ctrl+V al añadir una operación. Sweep AI lee el símbolo, el sentido, los contratos, las horas, los precios y las comisiones, y muestra tu P&L neto y tu R. Revisas y guardas."))}</p>'
            f'<p class="fine">{t(T("Copy trading? Choose “Also on” and the trade is saved on every account at once.","Copy trading ? Choisis « Aussi sur » et le trade est enregistré sur chaque compte d’un coup.","¿Copy trading? Elige «También en» y la operación se guarda en cada cuenta a la vez."))}</p></article>')
    tips = [T("Automatic sync for Rithmic and Tradovate is planned for later. Until then, use the CSV import or a screenshot.","La synchro automatique Rithmic et Tradovate est prévue plus tard. D’ici là, utilise l’import CSV ou une capture.","La sincronización automática con Rithmic y Tradovate está prevista para más adelante. Mientras tanto, usa la importación CSV o una captura."),
            T("Export one account at a time, so each trade lands on the right account (a Rithmic file with several accounts is split on its own).","Exporte un compte à la fois, pour que chaque trade arrive sur le bon compte (un fichier Rithmic à plusieurs comptes est réparti tout seul).","Exporta una cuenta cada vez para que cada operación vaya a la cuenta correcta (un archivo de Rithmic con varias cuentas se reparte solo)."),
            T("Most platforms limit the date range of an export: export week by week or month by month if needed.","La plupart des plateformes limitent la période d’un export : exporte semaine par semaine ou mois par mois si besoin.","La mayoría de plataformas limitan el periodo de exportación: exporta por semanas o por meses si hace falta."),
            T("Your P&L differs from your platform? Enter the real P&L (platform) on the trade, or your commission per contract on the account.","Ton P&L diffère de ta plateforme ? Entre le P&L réel (plateforme) sur le trade, ou ta commission par contrat sur le compte.","¿Tu P&L no coincide con tu plataforma? Introduce el P&L real (plataforma) en la operación, o tu comisión por contrato en la cuenta.")]
    nav = ui.subnav(t, T("Platforms","Plateformes","Plataformas"), [(k, {"en": n, "fr": n, "es": n}) for k, n, _, _ in PLATFORMS] + [("any", T("Other platforms","Autres plateformes","Otras plataformas"))])
    hero = ui.hero(t, H[2], H[0], H[1], cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True),
                   visual=ui.frame_d("v6-18-add-trade-choice-d.webp", t(T("Adding a trade: from a screenshot, by hand or from a CSV file","Ajouter un trade : par capture, à la main ou par fichier CSV","Añadir una operación: por captura, a mano o con un archivo CSV")), m="v6-18-add-trade-choice-m.webp", t=t, sizes="(max-width: 1067px) 92vw, 1200px", cls="reveal zoom"))
    b = (nav + ui.sec(how, "t", "how") + ui.sec(ui.cards(plats, 3) + ui.cards([anyp], 1), "t", "platforms")
         + ui.sec(ui.head(t, None, T("Good to know","Bon à savoir","Conviene saber")) + ui.bullets(t, tips)
                  + f'<p class="fine" style="margin-top:24px">{t(T("Platform menus can change between versions. Platform names belong to their owners; Sweep isn’t affiliated with them.","Les menus des plateformes peuvent changer d’une version à l’autre. Les noms des plateformes appartiennent à leurs propriétaires ; Sweep n’y est pas affilié.","Los menús de las plataformas pueden cambiar entre versiones. Los nombres pertenecen a sus propietarios; Sweep no está afiliado a ellas."))}</p>', "n", "tips", width="read")
         + ui.final(lang, t))
    ld = jsonld({"@context":"https://schema.org","@type":"HowTo","name":t(T("How to bring your trades from Tradovate, TopstepX, Rithmic, TradingView, NinjaTrader and Quantower into Sweep","Comment ramener tes trades de Tradovate, TopstepX, Rithmic, TradingView, NinjaTrader et Quantower dans Sweep","Cómo llevar tus operaciones de Tradovate, TopstepX, Rithmic, TradingView, NinjaTrader y Quantower a Sweep")),
        "step":[{"@type":"HowToSection","name":name,"itemListElement":[{"@type":"HowToStep","position":i+1,"text":re_strip(t(s))} for i,s in enumerate(steps)]} for _,name,_,steps in PLATFORMS]})
    return (t(T("Import trades: Tradovate, TopstepX, Rithmic… · Sweep","Importer tes trades : Tradovate, TopstepX, Rithmic… · Sweep","Importar operaciones: Tradovate, TopstepX, Rithmic… · Sweep")),
            t(T("How to export your trade history from Tradovate, TopstepX, Rithmic R|Trader Pro and TradingView, or sync NinjaTrader 8 and Quantower, and bring it into Sweep.","Comment exporter ton historique de Tradovate, TopstepX, Rithmic R|Trader Pro et TradingView, ou synchroniser NinjaTrader 8 et Quantower, et le ramener dans Sweep.","Cómo exportar tu historial de Tradovate, TopstepX, Rithmic R|Trader Pro y TradingView, o sincronizar NinjaTrader 8 y Quantower, y llevarlo a Sweep.")),
            hero + b, ld)

SYSTEM_PAGES.add("import.html")

def re_strip(s):
    import re
    return re.sub("<[^>]+>", "", s)

# ---------------------------------------------------------------- export guides, one page per platform (SEO brief, Oct 15, step 3)
# What Sweep reads in each file comes from the app's import (src/ux.js, section 17, and parseTradovate in src/app.js).
_STEPS = {k: steps for k, _, _, steps in PLATFORMS}
INTO_SWEEP = [T("In Sweep, open <b>Trades → Import CSV</b>.","Dans Sweep, ouvre <b>Trades → Importer un CSV</b>.","En Sweep, abre <b>Operaciones → Importar CSV</b>."),
              T("Pick the account the trades belong to, then choose the file. Sweep recognizes the format on its own.","Choisis le compte des trades, puis le fichier. Sweep reconnaît le format tout seul.","Elige la cuenta de las operaciones y luego el archivo. Sweep reconoce el formato solo."),
              T("Check the preview, then import. Trades already imported on that account are left out.","Vérifie l’aperçu, puis importe. Les trades déjà importés sur ce compte sont laissés de côté.","Revisa la vista previa e importa. Las operaciones ya importadas en esa cuenta se dejan fuera.")]
SESSION_DAY = T("<b>The session day:</b> a trade opened at 6 p.m. New York time or later counts for the next day, as at the firms (daily limit, winning days, calendar).",
                "<b>Le jour de séance :</b> un trade ouvert à 18 h (heure de New York) ou plus tard compte pour le lendemain, comme chez les firmes (limite du jour, jours gagnants, calendrier).",
                "<b>El día de sesión:</b> una operación abierta a las 18:00 (hora de Nueva York) o más tarde cuenta para el día siguiente, como en las firmas (límite diario, días ganadores, calendario).")
UNKNOWN_SYM = T("<b>A contract Sweep doesn’t know</b> keeps its own symbol and is never priced as NQ.","<b>Un contrat que Sweep ne connaît pas</b> garde son symbole et n’est jamais compté comme du NQ.","<b>Un contrato que Sweep no conoce</b> conserva su símbolo y nunca se calcula como NQ.")
NO_DOUBLE = lambda key: (T("Will importing the same file twice double my trades?","Importer deux fois le même fichier double-t-il mes trades ?","¿Importar dos veces el mismo archivo duplica mis operaciones?"),
                         T(f"No. Each trade keeps a key from {key['en']}, and trades already imported on the account are left out.",f"Non. Chaque trade garde une clé tirée de {key['fr']}, et les trades déjà importés sur le compte sont laissés de côté.",f"No. Cada operación guarda una clave sacada de {key['es']}, y las operaciones ya importadas en la cuenta se dejan fuera."))
EXPORT_GUIDES = [
 {"slug": "import-tradovate.html", "key": "tradovate", "name": "Tradovate",
  "title": T("How to Export Trades from Tradovate (CSV) · Sweep","Exporter tes trades de Tradovate en CSV · Sweep","Exportar tus operaciones de Tradovate en CSV · Sweep"),
  "desc": T("Export your Tradovate trades as a CSV from the Performance report, set the time zone, and import them into Sweep, a free trading journal.",
            "Exporte tes trades Tradovate en CSV depuis le rapport Performance, règle le fuseau horaire et importe-les dans Sweep, journal de trading gratuit.",
            "Exporta tus operaciones de Tradovate en CSV desde el informe Performance, ajusta la zona horaria e impórtalas en Sweep, diario de trading gratis."),
  "kick": T("Export trades from Tradovate","Exporter tes trades de Tradovate","Exportar operaciones de Tradovate"),
  "h1": T("Your Tradovate history, in four steps.","Ton historique Tradovate, en quatre étapes.","Tu historial de Tradovate, en cuatro pasos."),
  "lead": T("Tradovate’s Performance report lists your closed trades with their prices, P&L and times. Download it as a CSV, then import it into Sweep: each trade lands on your account, on its New York session day.",
            "Le rapport Performance de Tradovate liste tes trades fermés avec leurs prix, leur P&L et leurs heures. Télécharge-le en CSV, puis importe-le dans Sweep : chaque trade arrive sur ton compte, au jour de sa séance de New York.",
            "El informe Performance de Tradovate lista tus operaciones cerradas con sus precios, su P&L y sus horas. Descárgalo en CSV e impórtalo en Sweep: cada operación llega a tu cuenta, en el día de su sesión de Nueva York."),
  "reads": [T("<b>The columns it needs:</b> symbol, qty, buyPrice, sellPrice, pnl, boughtTimestamp and soldTimestamp, as in the Performance report.","<b>Les colonnes nécessaires :</b> symbol, qty, buyPrice, sellPrice, pnl, boughtTimestamp et soldTimestamp, comme dans le rapport Performance.","<b>Las columnas necesarias:</b> symbol, qty, buyPrice, sellPrice, pnl, boughtTimestamp y soldTimestamp, como en el informe Performance."),
            T("<b>One trade per entry:</b> the lines that share the same entry fill are grouped, with the average entry and exit prices.","<b>Un trade par entrée :</b> les lignes qui partagent la même exécution d’entrée sont regroupées, avec les prix moyens d’entrée et de sortie.","<b>Una operación por entrada:</b> las líneas que comparten la misma ejecución de entrada se agrupan, con los precios medios de entrada y salida."),
            T("<b>The P&L is Tradovate’s,</b> line by line. Sweep doesn’t read fees from this report: it applies the commission per contract set on your account.","<b>Le P&L est celui de Tradovate,</b> ligne par ligne. Sweep ne lit pas de frais dans ce rapport : il applique la commission par contrat réglée sur ton compte.","<b>El P&L es el de Tradovate,</b> línea por línea. Sweep no lee comisiones en este informe: aplica la comisión por contrato configurada en tu cuenta."),
            T("<b>Times as written in the file:</b> that’s why Tradovate’s time zone should be New York before you export.","<b>Les heures telles qu’écrites dans le fichier :</b> c’est pourquoi le fuseau de Tradovate doit être New York avant l’export.","<b>Las horas tal como están en el archivo:</b> por eso la zona horaria de Tradovate debe ser Nueva York antes de exportar."),
            SESSION_DAY, UNKNOWN_SYM],
  "faqs": [(T("Why are my times off by a few hours?","Pourquoi mes heures sont-elles décalées de quelques heures ?","¿Por qué mis horas están desfasadas unas horas?"),
            T("Tradovate writes the times in its own time zone setting, and Sweep reads them as they are. Set Tradovate’s time zone to New York and export again. Delete the trades imported with the wrong times first: a trade already imported is left out.",
              "Tradovate écrit les heures dans le fuseau réglé chez lui, et Sweep les lit telles quelles. Règle le fuseau de Tradovate sur New York et exporte de nouveau. Supprime d’abord les trades importés avec les mauvaises heures : un trade déjà importé est laissé de côté.",
              "Tradovate escribe las horas en la zona horaria que tiene configurada, y Sweep las lee tal cual. Pon la zona horaria de Tradovate en Nueva York y exporta de nuevo. Borra antes las operaciones importadas con las horas mal: una operación ya importada se deja fuera.")),
           (T("Why is my P&L different from Tradovate’s?","Pourquoi mon P&L diffère-t-il de celui de Tradovate ?","¿Por qué mi P&L difiere del de Tradovate?"),
            T("Usually the fees: Sweep subtracts the commission per contract set on your account. Check that commission, or enter the real P&L (platform) on the trade.",
              "En général, les frais : Sweep retire la commission par contrat réglée sur ton compte. Vérifie cette commission, ou entre le P&L réel (plateforme) sur le trade.",
              "Normalmente, las comisiones: Sweep resta la comisión por contrato configurada en tu cuenta. Revisa esa comisión, o introduce el P&L real (plataforma) en la operación.")),
           NO_DOUBLE(T("its fills","ses exécutions","sus ejecuciones"))]},
 {"slug": "import-topstepx.html", "key": "projectx", "name": "TopstepX",
  "title": T("How to Export Trades from TopstepX (CSV) · Sweep","Exporter tes trades de TopstepX en CSV · Sweep","Exportar tus operaciones de TopstepX en CSV · Sweep"),
  "desc": T("Export your TopstepX trades as a CSV from the Trades tab and import them into Sweep: UTC times converted, Topstep’s trading day kept, fees included.",
            "Exporte tes trades TopstepX en CSV depuis l’onglet Trades et importe-les dans Sweep : heures UTC converties, jour de trading gardé, frais inclus.",
            "Exporta tus operaciones de TopstepX en CSV desde la pestaña Trades e impórtalas en Sweep: horas UTC convertidas y comisiones incluidas."),
  "kick": T("Export trades from TopstepX","Exporter tes trades de TopstepX","Exportar operaciones de TopstepX"),
  "h1": T("Your TopstepX trades, in three clicks.","Tes trades TopstepX, en trois clics.","Tus operaciones de TopstepX, en tres clics."),
  "lead": T("TopstepX is Topstep’s platform, also used by other firms built on ProjectX. Its Trades tab exports one line per trade, with the fees and the trading day, and Sweep reads it as is.",
            "TopstepX est la plateforme de Topstep, utilisée aussi par d’autres firmes construites sur ProjectX. Son onglet Trades exporte une ligne par trade, avec les frais et le jour de trading, et Sweep le lit tel quel.",
            "TopstepX es la plataforma de Topstep, usada también por otras firmas basadas en ProjectX. Su pestaña Trades exporta una línea por operación, con las comisiones y el día de trading, y Sweep la lee tal cual."),
  "reads": [T("<b>The columns it needs:</b> ContractName, EnteredAt, ExitedAt, EntryPrice and ExitPrice, with Size, Type, PnL, Fees, Commissions and TradeDay.","<b>Les colonnes nécessaires :</b> ContractName, EnteredAt, ExitedAt, EntryPrice et ExitPrice, avec Size, Type, PnL, Fees, Commissions et TradeDay.","<b>Las columnas necesarias:</b> ContractName, EnteredAt, ExitedAt, EntryPrice y ExitPrice, con Size, Type, PnL, Fees, Commissions y TradeDay."),
            T("<b>One line, one trade:</b> TopstepX writes each trade with its entry and its exit, and Sweep keeps it as one trade.","<b>Une ligne, un trade :</b> TopstepX écrit chaque trade avec son entrée et sa sortie, et Sweep le garde comme un seul trade.","<b>Una línea, una operación:</b> TopstepX escribe cada operación con su entrada y su salida, y Sweep la guarda como una sola operación."),
            T("<b>UTC times, converted:</b> TopstepX writes its times in UTC, and Sweep shows them in New York time.","<b>Heures UTC, converties :</b> TopstepX écrit ses heures en UTC, et Sweep les affiche à l’heure de New York.","<b>Horas UTC, convertidas:</b> TopstepX escribe sus horas en UTC, y Sweep las muestra en hora de Nueva York."),
            T("<b>The trading day TopstepX gives</b> is used as is, so your daily limit, winning days and calendar follow the same day.","<b>Le jour de trading donné par TopstepX</b> est repris tel quel : ta limite du jour, tes jours gagnants et ton calendrier suivent le même jour.","<b>El día de trading que da TopstepX</b> se usa tal cual: tu límite diario, tus días ganadores y tu calendario siguen el mismo día."),
            T("<b>P&L, fees and commissions</b> come from the file.","<b>Le P&L, les frais et les commissions</b> viennent du fichier.","<b>El P&L, las comisiones y los cargos</b> vienen del archivo."),
            UNKNOWN_SYM],
  "faqs": [(T("Why don’t the times look like the ones in TopstepX?","Pourquoi les heures ne ressemblent-elles pas à celles de TopstepX ?","¿Por qué las horas no se parecen a las de TopstepX?"),
            T("The file is in UTC and Sweep shows New York time, the time of the futures session. If TopstepX shows you another time zone, the hours differ but the trades are the same.",
              "Le fichier est en UTC et Sweep affiche l’heure de New York, celle de la séance des futures. Si TopstepX t’affiche un autre fuseau, les heures diffèrent mais les trades sont les mêmes.",
              "El archivo está en UTC y Sweep muestra la hora de Nueva York, la de la sesión de futuros. Si TopstepX te muestra otra zona horaria, las horas difieren pero las operaciones son las mismas.")),
           (T("Does it work for other firms on ProjectX?","Ça marche pour les autres firmes sur ProjectX ?","¿Funciona con otras firmas en ProjectX?"),
            T("Yes, when their platform exports the same Trades file (ContractName, EnteredAt, ExitedAt…): Sweep reads it the same way.",
              "Oui, quand leur plateforme exporte le même fichier Trades (ContractName, EnteredAt, ExitedAt…) : Sweep le lit de la même façon.",
              "Sí, cuando su plataforma exporta el mismo archivo Trades (ContractName, EnteredAt, ExitedAt…): Sweep lo lee igual.")),
           NO_DOUBLE(T("its TopstepX ID","son identifiant TopstepX","su identificador de TopstepX"))]},
 {"slug": "import-rithmic.html", "key": "rithmic", "name": "Rithmic",
  "title": T("How to Export Trades from Rithmic R | Trader Pro · Sweep","Exporter tes trades de Rithmic R | Trader Pro · Sweep","Exportar tus operaciones de Rithmic R | Trader Pro · Sweep"),
  "desc": T("Export your trades from Rithmic R | Trader Pro (Completed Orders, as a CSV) and import them into Sweep: fills paired into trades, several accounts at once.",
            "Exporte tes trades de R | Trader Pro (Completed Orders, en CSV) et importe-les dans Sweep : exécutions regroupées en trades, plusieurs comptes à la fois.",
            "Exporta tus operaciones de R | Trader Pro (Completed Orders, en CSV) e impórtalas en Sweep: ejecuciones agrupadas en operaciones, varias cuentas a la vez."),
  "kick": T("Export trades from Rithmic","Exporter tes trades de Rithmic","Exportar operaciones de Rithmic"),
  "h1": T("Your R | Trader Pro orders, as trades.","Tes ordres R | Trader Pro, en trades.","Tus órdenes de R | Trader Pro, como operaciones."),
  "lead": T("R | Trader Pro exports your filled orders, one day at a time. Sweep pairs them into trades, account by account and contract by contract, with the average prices and the commission.",
            "R | Trader Pro exporte tes ordres exécutés, une journée à la fois. Sweep les regroupe en trades, compte par compte et contrat par contrat, avec les prix moyens et la commission.",
            "R | Trader Pro exporta tus órdenes ejecutadas, un día cada vez. Sweep las agrupa en operaciones, cuenta por cuenta y contrato por contrato, con los precios medios y la comisión."),
  "reads": [T("<b>Filled orders only:</b> cancelled or rejected orders are skipped.","<b>Les ordres exécutés seulement :</b> les ordres annulés ou rejetés sont ignorés.","<b>Solo las órdenes ejecutadas:</b> las órdenes canceladas o rechazadas se ignoran."),
            T("<b>Paired into trades,</b> first in, first out, for each account and each contract: a trade ends when the position is back to zero.","<b>Regroupés en trades,</b> premier entré, premier sorti, pour chaque compte et chaque contrat : un trade se termine quand la position revient à zéro.","<b>Agrupadas en operaciones,</b> primera en entrar, primera en salir, para cada cuenta y cada contrato: una operación termina cuando la posición vuelve a cero."),
            T("<b>Contracts</b> count the largest position held, as in the trade form; entry and exit are the average prices.","<b>Les contrats</b> comptent la plus grosse position tenue, comme dans le formulaire ; l’entrée et la sortie sont les prix moyens.","<b>Los contratos</b> cuentan la posición más grande mantenida, como en el formulario; la entrada y la salida son los precios medios."),
            T("<b>P&L from the prices</b> and the contract’s point value; fees from the Commission column.","<b>Le P&L vient des prix</b> et de la valeur du point du contrat ; les frais, de la colonne Commission.","<b>El P&L sale de los precios</b> y del valor del punto del contrato; las comisiones, de la columna Commission."),
            T("<b>Several accounts in one file:</b> each trade goes to the matching account, and an account that isn’t in Sweep yet is flagged.","<b>Plusieurs comptes dans un fichier :</b> chaque trade va sur le compte correspondant, et un compte qui n’est pas encore dans Sweep est signalé.","<b>Varias cuentas en un archivo:</b> cada operación va a la cuenta correspondiente, y una cuenta que aún no está en Sweep se señala."),
            T("<b>Times as R | Trader Pro writes them.</b>","<b>Les heures telles que R | Trader Pro les écrit.</b>","<b>Las horas tal como las escribe R | Trader Pro.</b>"),
            SESSION_DAY,
            T("<b>A contract Sweep doesn’t know</b> is never priced as NQ: you enter its P&L.","<b>Un contrat que Sweep ne connaît pas</b> n’est jamais compté comme du NQ : tu entres son P&L.","<b>Un contrato que Sweep no conoce</b> nunca se calcula como NQ: introduces tú su P&L.")],
  "faqs": [(T("Why does Sweep find no trade in my file?","Pourquoi Sweep ne trouve-t-il aucun trade dans mon fichier ?","¿Por qué Sweep no encuentra ninguna operación en mi archivo?"),
            T("Some Completed Orders columns are missing. Show Buy/Sell, Symbol, Qty Filled and Avg Fill Price (plus Account, Status, Update Time and Commission), then export again.",
              "Il manque des colonnes de Completed Orders. Affiche Buy/Sell, Symbol, Qty Filled et Avg Fill Price (et Account, Status, Update Time et Commission), puis exporte de nouveau.",
              "Faltan columnas de Completed Orders. Muestra Buy/Sell, Symbol, Qty Filled y Avg Fill Price (y Account, Status, Update Time y Commission) y exporta de nuevo.")),
           (T("Can I export a whole week?","Puis-je exporter une semaine entière ?","¿Puedo exportar una semana entera?"),
            T("R | Trader Pro exports one day per file. Import each day’s file: Sweep adds them up, and a day imported twice isn’t doubled.",
              "R | Trader Pro exporte une journée par fichier. Importe le fichier de chaque journée : Sweep les additionne, et une journée importée deux fois n’est pas doublée.",
              "R | Trader Pro exporta un día por archivo. Importa el archivo de cada día: Sweep los suma, y un día importado dos veces no se duplica.")),
           (T("Why was one of my trades split in two?","Pourquoi un de mes trades a-t-il été coupé en deux ?","¿Por qué una de mis operaciones se dividió en dos?"),
            T("Sweep ends a trade each time the position is back to zero. Adding to the position and taking partial exits without going flat stays one trade.",
              "Sweep termine un trade chaque fois que la position revient à zéro. Ajouter à la position et prendre des sorties partielles sans revenir à zéro reste un seul trade.",
              "Sweep termina una operación cada vez que la posición vuelve a cero. Añadir a la posición y tomar salidas parciales sin cerrar del todo sigue siendo una sola operación."))]},
]

def make_export_guide(g):
    SYSTEM_PAGES.add(g["slug"])
    CRUMBS[g["slug"]] = {l: g["name"] for l in LANGS}
    def page(lang, t):
        import ui
        from pages17 import chiprow
        hero = ui.hero(t, g["kick"], g["h1"], g["lead"], kick_in_h1=True,
                       cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs=f'data-track="signup_export_{g["key"]}"') + ui.btn(t(T("Every platform","Toutes les plateformes","Todas las plataformas")), href(lang, "import.html"), "line", lg=True))
        steps = g.get("steps") or _STEPS[g["key"]]
        ol = lambda xs: '<ol class="psteps">' + "".join(f"<li>{t(x)}</li>" for x in xs) + "</ol>"
        cards = ui.cards([ui.Card("text", f'<article class="card plat"><div class="plat-h"><h2>{t(T(f"Export from {g["name"]}", f"Exporter de {g["name"]}", f"Exportar de {g["name"]}"))}</h2></div>{ol(steps)}</article>'),
                          ui.Card("text", f'<article class="card plat"><div class="plat-h"><h2>{t(T("Import it into Sweep","L’importer dans Sweep","Importarlo en Sweep"))}</h2></div>{ol(INTO_SWEEP)}</article>')], 2)
        others = [(x["slug"], {l: x["name"] for l in LANGS}) for x in EXPORT_GUIDES if x is not g] + [("ninjatrader.html", {l: "NinjaTrader 8" for l in LANGS}), ("quantower.html", {l: "Quantower" for l in LANGS})]
        reads = (f'<h2>{t(T("What Sweep reads in the file","Ce que Sweep lit dans le fichier","Lo que Sweep lee en el archivo"))}</h2><ul class="list">' + "".join(f"<li>{t(x)}</li>" for x in g["reads"]) + "</ul>"
                 + chiprow(lang, t, T("Other platforms","Autres plateformes","Otras plataformas"), others, 24)
                 + f'<p class="fine" style="margin-top:24px">{t(T("Platform menus can change between versions. Platform names belong to their owners; Sweep isn’t affiliated with them.","Les menus des plateformes peuvent changer d’une version à l’autre. Les noms des plateformes appartiennent à leurs propriétaires ; Sweep n’est affilié à aucune.","Los menús de las plataformas pueden cambiar de una versión a otra. Los nombres de las plataformas pertenecen a sus propietarios; Sweep no está afiliado a ninguna."))}</p>')
        b = (ui.sec(cards, "t", "steps") + ui.sec(f'<article class="article">{reads}</article>', "n", "reads", width="read")
             + ui.sec(ui.head(t, None, T("Questions","Questions","Preguntas")) + ui.qa(t, g["faqs"]), "n", "faq", width="read")
             + ui.read_next(lang, t, ["import.html", "ninjatrader.html", "free-trading-journal.html"]) + ui.final(lang, t))
        ld = jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in g["faqs"]]})
        return t(g["title"]), t(g["desc"]), hero + b, ld
    return page

EXPORT_PAGES = {g["slug"]: make_export_guide(g) for g in EXPORT_GUIDES}
