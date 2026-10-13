from core import *

COUNT_URL = "https://app.makeitsweep.com/api/cohort-count.php"

CRUMBS["100"] = T("The first 100", "Les 100 premiers", "Los primeros 100")

def page_100(lang, t):
    taken_tpl = t(T("{n} of {total} spots taken", "{n} places prises sur {total}", "{n} de {total} plazas ocupadas"))
    full_txt = t(T("The first 100 is full. Join the waitlist.", "Les 100 premières places sont prises. Inscris-toi sur la liste d’attente.", "Los primeros 100 están completos. Únete a la lista de espera."))
    join = t(T("Join the first 100", "Rejoindre les 100 premiers", "Unirme a los primeros 100"))
    hero = f'''<div class="hero c100"><div class="wrap"><div class="hero-copy">
<span class="pill rise"><span class="tag">14 {t(T("days","jours","días"))}</span><b>{t(T("A founding group of futures traders","Un groupe fondateur de traders de futures","Un grupo fundador de traders de futuros"))}</b></span>
<h1 class="wu">{words(t(T("Looking for 100 futures traders.","On cherche 100 traders de futures.","Buscamos 100 traders de futuros.")),0.1)}</h1>
<p class="lead rise d3">{t(T("Not to look at Sweep. To journal with it for 14 days.","Pas pour regarder Sweep. Pour tenir ton journal avec lui pendant 14 jours.","No para mirar Sweep. Para llevar tu diario con él durante 14 días."))}</p>
<div class="cta-row rise d4"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{join}</a></div>
<div class="spots rise d5" id="spots-box" hidden><div class="grid100" aria-hidden="true">{"<i></i>"*100}</div><p id="spots" class="num"></p></div>
</div></div></div>'''
    statement = f'''<section class="rule center"><div class="wrap"><p class="big-quote reveal">{t(T("Your P&L tells you what happened.","Ton P&L te dit ce qui s’est passé.","Tu P&L te dice lo que pasó."))} <span class="gain">{t(T("Sweep shows you why.","Sweep te montre pourquoi.","Sweep te muestra por qué."))}</span></p></div></section>'''
    cards = [
     ("check", T("The deal","Le deal","El trato"), T("Add your account, log every trading day for 14 days, and tell us honestly what helped and what didn’t.","Ajoute ton compte, note chaque journée de trading pendant 14 jours, et dis-nous honnêtement ce qui t’a aidé et ce qui ne t’a pas aidé.","Añade tu cuenta, registra cada día de trading durante 14 días y dinos con honestidad qué te ayudó y qué no.")),
     ("spark", T("You get","Tu reçois","Recibes"), T("Sweep free, a direct line to the founder, and a say in what we build next.","Sweep gratuit, une ligne directe avec le fondateur, et ton mot à dire sur ce qu’on construit ensuite.","Sweep gratis, línea directa con el fundador y voz en lo que construimos después.")),
     ("layers", T("Who it’s for","Pour qui","Para quién"), T("NQ, ES or micros (or other futures) · prop or personal accounts · trading at least 3 days a week.","NQ, ES ou micros (ou autres futures) · comptes prop ou personnels · tu trades au moins 3 jours par semaine.","NQ, ES o micros (u otros futuros) · cuentas prop o personales · operas al menos 3 días por semana.")),
    ]
    deal = f'<section class="rule"><div class="wrap">{grid(t, cards)}<div class="cta-row" style="justify-content:center;margin-top:40px"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{join}</a></div><p class="spots-line num" id="spots2" hidden></p></div></section>'
    shots = f'''<section class="rule center"><div class="wrap"><div class="head center"><h2>{t(T("What your 14 days look like.","À quoi ressemblent tes 14 jours.","Cómo son tus 14 días."))}</h2>
<p class="lead">{t(T("Log each day in about a minute, review it, and watch the patterns show up.","Note chaque journée en environ une minute, révise-la, et regarde les tendances apparaître.","Registra cada día en un minuto, revísalo y mira cómo aparecen los patrones."))}</p></div>
<div class="phones rail reveal">{phone("new-trade",lang,t(T("Logging a trade","Saisie d’un trade","Registrar una operación")))}{phone("calendar",lang,t(T("P&L calendar","Calendrier P&L","Calendario de P&L")))}{phone("insights",lang,t(T("Insights","Analyses","Análisis")))}</div>
<p class="cap" style="margin-top:24px">{t(SAMPLE)}</p></div></section>'''
    faq_items = [
     (T("Is it free?","C’est gratuit?","¿Es gratis?"), T("Yes. Joining costs nothing and no card is needed.","Oui. Rejoindre ne coûte rien et aucune carte n’est requise.","Sí. Unirte no cuesta nada y no hace falta tarjeta.")),
     (T("Is my data private?","Mes données sont-elles privées?","¿Mis datos son privados?"), T("Yes. Only you see your trades; we never sell data, and you can export or delete it anytime.","Oui. Toi seul vois tes trades; on ne vend jamais de données, et tu peux les exporter ou les supprimer en tout temps.","Sí. Solo tú ves tus operaciones; nunca vendemos datos y puedes exportarlos o eliminarlos cuando quieras.")),
     (T("Does it work with my prop firm?","Est-ce que ça marche avec ma prop firm?","¿Funciona con mi prop firm?"), T(f"Yes. Any futures account, prop or personal: log by hand, from a screenshot or with AI, or <a href=\"{href(lang, 'import.html')}\">import your trades</a> from Tradovate, TopstepX, Rithmic, NinjaTrader 8 or Quantower.",f"Oui. Tout compte de futures, prop ou personnel : saisie manuelle, à partir d’une capture ou avec l’IA, ou <a href=\"{href(lang, 'import.html')}\">import de tes trades</a> depuis Tradovate, TopstepX, Rithmic, NinjaTrader 8 ou Quantower.",f"Sí. Cualquier cuenta de futuros, prop o personal: registro manual, desde una captura o con IA, o <a href=\"{href(lang, 'import.html')}\">importando tus operaciones</a> desde Tradovate, TopstepX, Rithmic, NinjaTrader 8 o Quantower.")),
     (T("Does it work on mobile?","Est-ce que ça marche sur mobile?","¿Funciona en el móvil?"), T(f"Yes. It runs in your browser and <a href=\"{href(lang, 'install.html')}\">installs on your home screen</a> like an app.",f"Oui. Ça fonctionne dans ton navigateur et <a href=\"{href(lang, 'install.html')}\">s’installe sur ton écran d’accueil</a> comme une app.",f"Sí. Funciona en el navegador y <a href=\"{href(lang, 'install.html')}\">se instala en tu pantalla de inicio</a> como una app.")),
    ]
    faq_items += [
     (T("How much time does it take each day?","Combien de temps ça prend par jour?","¿Cuánto tiempo lleva cada día?"), T("About a minute to log a trading day, from a screenshot, an import or by hand, and a few more if you review your trades with the checklist.","Environ une minute pour noter une journée de trading, à partir d’une capture, d’un import ou à la main, et quelques minutes de plus si tu révises tes trades avec la checklist.","Más o menos un minuto para registrar un día de trading, desde una captura, una importación o a mano, y unos minutos más si revisas tus operaciones con el checklist.")),
     (T("Do I need a prop firm account?","Ai-je besoin d’un compte prop?","¿Necesito una cuenta prop?"), T("No. Prop or personal futures accounts both work, as long as you trade at least 3 days a week.","Non. Les comptes de futures prop ou personnels conviennent tous les deux, tant que tu trades au moins 3 jours par semaine.","No. Valen cuentas de futuros prop o personales, siempre que operes al menos 3 días por semana.")),
     (T("How do I give feedback?","Comment je donne mes retours?","¿Cómo doy mi opinión?"), T(f"From the app, where every idea and bug report keeps its status, or by writing to {EMAIL}. Short and honest is perfect.",f"Depuis l’app, où chaque idée et chaque bug garde son statut, ou en écrivant à {EMAIL}. Court et honnête, c’est parfait.",f"Desde la app, donde cada idea y cada error conserva su estado, o escribiendo a {EMAIL}. Breve y sincero es perfecto.")),
     (T("What happens afterwards?","Qu’est-ce qui se passe après?","¿Qué pasa después?"), T("You keep your account and your whole history. The free plan stays free forever, and you can export or delete your data anytime.","Tu gardes ton compte et tout ton historique. Le forfait gratuit reste gratuit pour toujours, et tu peux exporter ou supprimer tes données en tout temps.","Conservas tu cuenta y todo tu historial. El plan gratuito sigue siendo gratis para siempre, y puedes exportar o eliminar tus datos cuando quieras.")),
     (T("Who is behind Sweep?","Qui est derrière Sweep?","¿Quién está detrás de Sweep?"), T(f"Sweep Inc., in Laval, Quebec. Sweep was born in a Discord community of futures traders and tested for months by trader friends before it launched. <a href=\"{href(lang, 'about.html')}\">Our story</a>.",f"Sweep Inc., à Laval, au Québec. Sweep est né dans une communauté Discord de traders de futures et a été testé pendant des mois par des amis traders avant son lancement. <a href=\"{href(lang, 'about.html')}\">Notre histoire</a>.",f"Sweep Inc., en Laval, Quebec. Sweep nació en una comunidad de Discord de traders de futuros y lo probaron durante meses amigos traders antes de su lanzamiento. <a href=\"{href(lang, 'about.html')}\">Nuestra historia</a>.")),
    ]
    faq = f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Quick answers","Réponses rapides","Respuestas rápidas"))}</h2></div>{"".join(faq_item(t,q,a) for q,a in faq_items)}</div></section>'
    ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":re.sub(r"<[^>]+>", "", t(a))}} for q, a in faq_items]})
    script = f'''<script>
(function(){{
  var tpl = {json.dumps(taken_tpl)}, full = {json.dumps(full_txt)};
  fetch('https://app.makeitsweep.com/sweep-count.php', {{credentials:'omit'}})
    .then(function(r){{ return r.ok ? r.json() : Promise.reject(); }})
    .catch(function(){{ return fetch({json.dumps(COUNT_URL)}, {{credentials:'omit'}}).then(function(r){{ return r.ok ? r.json() : Promise.reject(); }}); }})
    .then(function(d){{
      var taken = Math.max(parseInt(d.taken,10) || 0, {COHORT_FLOOR}), total = parseInt(d.total,10);
      if(!(total > 0) || !(taken >= 1)) return;
      var txt = taken >= total ? full : tpl.replace('{{n}}', taken).replace('{{total}}', total);
      ['spots','spots2'].forEach(function(id){{ var el = document.getElementById(id); if(el){{ el.textContent = txt; el.hidden = false; }} }});
      var box = document.getElementById('spots-box'); if(box) box.hidden = false;
      var dots = document.querySelectorAll('.grid100 i'), n = Math.min(taken, dots.length);
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      for(var i = 0; i < n; i++){{ (function(k){{ if(reduce) dots[k].classList.add('on'); else setTimeout(function(){{ dots[k].classList.add('on'); }}, 400 + k*14); }})(i); }}
    }})
    .catch(function(){{}});
}})();
</script>'''
    return (t(T("Looking for 100 Futures Traders — Sweep","On cherche 100 traders de futures — Sweep","Buscamos 100 traders de futuros — Sweep")),
            t(T("Sweep is looking for 100 futures and prop traders to journal for 14 days, tell us the truth and shape what we build next. Free, no card.","Sweep cherche 100 traders de futures et de prop firms pour tenir leur journal 14 jours, nous dire la vérité et orienter la suite. Gratuit, sans carte.","Sweep busca 100 traders de futuros y prop para llevar su diario 14 días, contarnos la verdad y decidir qué construimos. Gratis, sin tarjeta.")),
            hero + statement + deal + shots + faq + final_cta(lang, t, T("Join the first 100.","Rejoins les 100 premiers.","Únete a los primeros 100."), T("14 days of journaling, honest feedback, and a say in what we build next.","14 jours de journal, des retours honnêtes, et ton mot à dire sur la suite.","14 días de diario, opiniones honestas y voz en lo que construimos después."), own=True) + script, ld)
