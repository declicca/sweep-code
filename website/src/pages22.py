from core import *
import ui, json, random

# Sweep Wrapped (/wrapped, brief « avance concurrentielle », step 7): a trading month from a CSV export, as a 6-card story and a
# 1080 × 1920 card to share. Everything runs in the browser: the file is read with FileReader, nothing is sent or stored.
# A tool of the site, not an import into the app (no CSV import in the app stays the rule).
WRAPPED = "wrapped.html"

def _demo_csv():
    """A month of sample trades (October 2026, trading days only), always the same: the « Try the demo » file."""
    r = random.Random(20261031)
    rows = ["Date,Time,Symbol,P&L"]
    import datetime
    for d in range(1, 32):
        if datetime.date(2026, 10, d).weekday() >= 5: continue   # trading days only
        for _ in range(r.choice((1, 2, 2, 3))):
            h, m = r.choice((9, 10, 10, 10, 11, 13, 14)), r.randrange(0, 60, 5)
            if h == 9: m = max(m, 35)
            sym = r.choice(("NQZ6", "NQZ6", "MNQZ6", "ESZ6"))
            v = r.choice((420, 310, 255, 180, 640, 120, -150, -210, -95, -320, 505, -260, 380, 95, -410, -185, -240, -130, -75))
            if sym == "MNQZ6": v = round(v / 6)
            rows.append(f"2026-10-{d:02d},{h:02d}:{m:02d},{sym},{v:.2f}")
    return "\n".join(rows)

def page_wrapped(lang, t):
    from pages7 import NUM_JS
    L = {k: t(v) for k, v in {
        "drop": T("Drop your CSV here, or tap to choose it", "Dépose ton CSV ici, ou touche pour le choisir", "Suelta tu CSV aquí, o toca para elegirlo"),
        "demo": T("Try the demo", "Essayer la démo", "Probar la demo"),
        "map_t": T("Which columns are which?", "Quelles colonnes utiliser ?", "¿Qué columnas usar?"),
        "map_p": T("Sweep couldn’t find the date and the P&L in this file on its own. Pick them:", "Sweep n’a pas trouvé seul la date et le P&L dans ce fichier. Choisis-les :", "Sweep no encontró solo la fecha y el P&L en este archivo. Elígelos:"),
        "map_d": T("Date of the trade", "Date du trade", "Fecha de la operación"), "map_v": T("P&L of the trade", "P&L du trade", "P&L de la operación"),
        "map_go": T("Use these columns", "Utiliser ces colonnes", "Usar estas columnas"),
        "err_empty": T("This file has no trades Sweep can read.", "Ce fichier n’a aucun trade que Sweep peut lire.", "Este archivo no tiene operaciones que Sweep pueda leer."),
        "err_cols": T("Those two columns don’t give a date and an amount on most rows.", "Ces deux colonnes ne donnent pas une date et un montant sur la plupart des lignes.", "Esas dos columnas no dan una fecha y un importe en la mayoría de las filas."),
        "read": T("{n} trades read from {f} · {k}", "{n} trades lus dans {f} · {k}", "{n} operaciones leídas de {f} · {k}"),
        "generic": T("CSV", "CSV", "CSV"), "month": T("Month", "Mois", "Mes"),
        "hide": T("Hide amounts", "Masquer les montants", "Ocultar montos"),
        "play": T("Play my story", "Voir mon histoire", "Ver mi historia"), "dl": T("Download my card (PNG)", "Télécharger ma carte (PNG)", "Descargar mi tarjeta (PNG)"),
        "c1": T("Your net result", "Ton résultat net", "Tu resultado neto"),
        "c1s": T("{n} trades over {d} trading days.", "{n} trades sur {d} jours de trading.", "{n} operaciones en {d} días de trading."),
        "c1h": T("of your trades closed in profit.", "de tes trades ont fini en profit.", "de tus operaciones cerraron en beneficio."),
        "c2": T("Winning days · losing days", "Jours gagnants · jours perdants", "Días ganadores · días perdedores"),
        "c2s": T("{f} flat.", "{f} à zéro.", "{f} en cero."), "c2w": T("winning", "gagnants", "ganadores"), "c2l": T("losing", "perdants", "perdedores"),
        "c3": T("Your best trade", "Ton meilleur trade", "Tu mejor operación"),
        "c3h": T("of everything your winning trades made.", "de tout ce qu’ont rapporté tes trades gagnants.", "de todo lo que dejaron tus operaciones ganadoras."),
        "c4": T("Your toughest trade", "Ton trade le plus dur", "Tu operación más dura"),
        "c4s": T("Every month has one. What counts is the next trade.", "Chaque mois en a un. Ce qui compte, c’est le trade suivant.", "Cada mes tiene una. Lo que cuenta es la siguiente."),
        "c4h": T("of this month’s losses.", "des pertes du mois.", "de las pérdidas del mes."),
        "c5": T("What your month says", "Ce que dit ton mois", "Lo que dice tu mes"),
        "c5d": T("Your best day of the week", "Ton meilleur jour de la semaine", "Tu mejor día de la semana"),
        "c5ds": T("{v} over {n} {w}", "{v} sur {n} {w}", "{v} en {n} {w}"), "c5dh": T("{k} of {n} in profit", "{k} sur {n} en profit", "{k} de {n} en beneficio"),
        "c5h": T("Your best hour", "Ta meilleure heure", "Tu mejor hora"), "et": T("ET", "ET", "ET"),
        "c6": T("Imagine this every Friday, automatically.", "Imagine ça chaque vendredi, automatiquement.", "Imagina esto cada viernes, automáticamente."),
        "start": CREATE_FREE, "close": T("Close", "Fermer", "Cerrar"), "next": T("Next", "Suivant", "Siguiente"), "prev": T("Previous", "Précédent", "Anterior"),
        "tap": T("Tap to continue", "Touche pour continuer", "Toca para seguir"),
        "card_t": T("My trading month", "Mon mois de trading", "Mi mes de trading"),
        "k_net": T("Net result", "Résultat net", "Resultado neto"), "k_wr": T("Trades in profit", "Trades en profit", "Operaciones en beneficio"),
        "k_days": T("Winning days", "Jours gagnants", "Días ganadores"), "k_of": T("{a} of {b}", "{a} sur {b}", "{a} de {b}"),
        "k_best": T("Best trade", "Meilleur trade", "Mejor operación"), "k_dow": T("Best day of the week", "Meilleur jour de la semaine", "Mejor día de la semana"),
        "slogan": T("Your edge, finally in one place.", "Ton edge, enfin au même endroit.", "Tu edge, por fin en un solo lugar."),
    }.items()}
    L["loc"] = {"en": "en-US", "fr": "fr-CA", "es": "es"}[lang]
    drop = (f'<div class="wr-drop" id="wr-drop"><input type="file" id="wr-file" accept=".csv,text/csv,text/plain" class="sr">'
            f'<label for="wr-file" class="wr-zone"><span class="ico" aria-hidden="true">{ico(I["download"])}</span><b>{L["drop"]}</b>'
            f'<small>{t(T("Tradovate Performance, TopstepX, or any CSV with a date and a P&L column", "Tradovate Performance, TopstepX, ou tout CSV avec une colonne de date et une de P&L", "Tradovate Performance, TopstepX, o cualquier CSV con una columna de fecha y una de P&L"))}</small></label>'
            f'<button type="button" class="btn btn-line" id="wr-demo">{L["demo"]}</button>'
            f'<p class="wr-err" id="wr-err" role="alert" hidden></p>'
            f'<div class="wr-map" id="wr-map" hidden><h2 class="h3">{L["map_t"]}</h2><p>{L["map_p"]}</p>'
            f'<label class="fld"><span>{L["map_d"]}</span><span class="inp"><select id="wr-cd"></select></span></label>'
            f'<label class="fld"><span>{L["map_v"]}</span><span class="inp"><select id="wr-cv"></select></span></label>'
            f'<button type="button" class="btn btn-primary" id="wr-use">{L["map_go"]}</button></div></div>')
    res = (f'<div class="wr-res" id="wr-res" hidden><p class="wr-read" id="wr-read"></p>'
           f'<div class="wr-row"><label class="fld wr-month" id="wr-mwrap" hidden><span>{L["month"]}</span><span class="inp"><select id="wr-m"></select></span></label>'
           f'<label class="chk"><input type="checkbox" id="wr-hide"> {L["hide"]}</label></div>'
           f'<div class="cta-row"><button type="button" class="btn btn-primary btn-lg" id="wr-play">{L["play"]}</button>'
           f'<button type="button" class="btn btn-line btn-lg" id="wr-dl">{L["dl"]}</button></div></div>')
    story = (f'<dialog class="wr-story" id="wr-story" aria-label="{t(T("Your trading month", "Ton mois de trading", "Tu mes de trading"))}">'
             f'<div class="wr-bars" id="wr-bars"></div><button type="button" class="wr-x" id="wr-x" aria-label="{L["close"]}">'
             '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg></button>'
             f'<div class="wr-card" id="wr-card" aria-live="polite"></div>'
             f'<button type="button" class="wr-tap wr-prev" id="wr-prev" aria-label="{L["prev"]}"></button><button type="button" class="wr-tap wr-next" id="wr-next" aria-label="{L["next"]}"></button></dialog>')
    hero = ui.hero(t, T("Sweep Wrapped", "Sweep Wrapped", "Sweep Wrapped"), T("Your trading month, as a story.", "Ton mois de trading, en histoire.", "Tu mes de trading, como una historia."),
                   T("Free. No account. Your file never leaves your browser.", "Gratuit. Sans compte. Ton fichier ne quitte jamais ton navigateur.", "Gratis. Sin cuenta. Tu archivo nunca sale de tu navegador."), center=True)
    tool = ui.sec(f'<div class="wr-tool">{drop}{res}</div>'
                  + f'<p class="fine wr-fine">{t(T("Read and counted on your device: nothing is uploaded, nothing is stored. Fees are subtracted when your file has them. A recap of your own numbers. Education, not financial advice.", "Lu et compté sur ton appareil : rien n’est envoyé, rien n’est gardé. Les frais sont déduits quand ton fichier les contient. Un récapitulatif de tes propres chiffres. De l’éducation, pas un conseil financier.", "Leído y contado en tu dispositivo: nada se envía, nada se guarda. Las comisiones se restan cuando tu archivo las tiene. Un resumen de tus propios números. Educación, no asesoramiento financiero."))}</p>', "t", "wrapped")
    how = [(T("Which files work?", "Quels fichiers fonctionnent ?", "¿Qué archivos funcionan?"),
            T(f"The Performance report from Tradovate, the trades export from TopstepX, or any CSV with one row per trade, a date and a P&L. If Sweep can’t tell the columns apart, it asks you. To export your trades, see <a href=\"{href('en', 'import.html')}\">import your trades</a>.",
              f"Le rapport Performance de Tradovate, l’export des trades de TopstepX, ou tout CSV avec une ligne par trade, une date et un P&L. Si Sweep ne reconnaît pas les colonnes, il te les demande. Pour exporter tes trades, vois <a href=\"{href('fr', 'import.html')}\">importer tes trades</a>.",
              f"El informe Performance de Tradovate, la exportación de operaciones de TopstepX, o cualquier CSV con una fila por operación, una fecha y un P&L. Si Sweep no distingue las columnas, te las pide. Para exportar tus operaciones, mira <a href=\"{href('es', 'import.html')}\">importar operaciones</a>.")),
           (T("Is my file sent anywhere?", "Mon fichier est-il envoyé quelque part ?", "¿Mi archivo se envía a algún sitio?"),
            T("No. Your browser reads it and counts it on your device. Nothing is uploaded and nothing is kept: close the page and it’s gone.", "Non. Ton navigateur le lit et le compte sur ton appareil. Rien n’est envoyé et rien n’est gardé : ferme la page et tout disparaît.", "No. Tu navegador lo lee y lo cuenta en tu dispositivo. Nada se envía y nada se guarda: cierra la página y desaparece.")),
           (T("Which day does a trade count on?", "Sur quel jour compte un trade ?", "¿En qué día cuenta una operación?"),
            T("On its trading day, in New York time, like in Sweep: a trade after 6 PM ET counts for the next session. Hours are shown in ET when your file gives a time zone.", "Sur sa journée de trading, à l’heure de New York, comme dans Sweep : un trade après 18 h ET compte pour la séance suivante. Les heures sont en ET quand ton fichier donne un fuseau.", "En su día de trading, en hora de Nueva York, como en Sweep: una operación después de las 6 p. m. ET cuenta para la sesión siguiente. Las horas se muestran en ET cuando tu archivo da una zona horaria.")),
           (T("What does « Hide amounts » change?", "Que change « Masquer les montants » ?", "¿Qué cambia «Ocultar montos»?"),
            T("Your story and your card show percentages and days instead of dollars, so you can share your month without your numbers.", "Ton histoire et ta carte montrent des pourcentages et des jours au lieu des dollars : tu partages ton mois sans tes chiffres.", "Tu historia y tu tarjeta muestran porcentajes y días en vez de dólares: compartes tu mes sin tus cifras."))]
    b = tool + ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, how), "n", "faq", width="read")
    script = ("<script>(function(){var L=" + json.dumps(L, ensure_ascii=False) + ",DEMO=" + json.dumps(_demo_csv()) + ",SIGNUP=" + json.dumps(SIGNUP) + ";" + NUM_JS + WRAPPED_JS + "})()</script>")
    ld = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": "Sweep Wrapped", "url": f"https://{DOMAIN}{href(lang, WRAPPED)}", "applicationCategory": "FinanceApplication", "operatingSystem": "Web", "isAccessibleForFree": True,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "publisher": {"@id": f"https://{DOMAIN}/#org"}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in how]}]})
    return (t(T("Sweep Wrapped: your trading month as a story · Sweep", "Sweep Wrapped : ton mois de trading en histoire · Sweep", "Sweep Wrapped: tu mes de trading como una historia · Sweep")),
            t(T("Drop a Tradovate, TopstepX or any CSV export: your net result, winning days, best and toughest trade and best day of the week, as a story and a card to share. Free, no account, your file stays in your browser.",
                "Dépose un export Tradovate, TopstepX ou tout CSV : ton résultat net, tes jours gagnants, ton meilleur et ton pire trade et ton meilleur jour, en histoire et en carte à partager. Gratuit, sans compte, ton fichier reste dans ton navigateur.",
                "Suelta una exportación de Tradovate, TopstepX o cualquier CSV: tu resultado neto, días ganadores, mejor y peor operación y mejor día, como historia y tarjeta para compartir. Gratis, sin cuenta, tu archivo se queda en tu navegador.")),
            hero + b + story + script + ui.final(lang, t), ld)
SYSTEM_PAGES.add(WRAPPED)
NO_DOCK.add(WRAPPED)

WRAPPED_JS = r"""
var $=function(i){return document.getElementById(i)},S={rows:null,trades:null,month:null,hide:false,name:'',kind:''},LOC=L.loc;
function csv(text){text=text.replace(/^﻿/,'');var first=text.split(/\r?\n/)[0]||'',sep=[',',';','\t'].sort(function(a,b){return first.split(b).length-first.split(a).length})[0],out=[];S.sep=sep;var _,row=[],f='',q=false;
 for(var i=0;i<text.length;i++){var c=text[i];if(q){if(c=='"'){if(text[i+1]=='"'){f+='"';i++}else q=false}else f+=c}
  else if(c=='"')q=true;else if(c==sep){row.push(f);f=''}else if(c=='\n'||c=='\r'){if(c=='\r'&&text[i+1]=='\n')i++;row.push(f);f='';if(row.join('').trim())out.push(row);row=[]}else f+=c}
 row.push(f);if(row.join('').trim())out.push(row);return out}
function num(s){s=String(s==null?'':s).trim();if(!s)return NaN;var b=s.replace(/[$€£\s]/g,''),neg=/^\(.*\)$/.test(b)||/^[-−]/.test(b);s=s.replace(/[()$€£\s+−-]/g,'');
 if(/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(s))s=s.replace(/\./g,'').replace(',','.');else if(/^\d+,\d{1,2}$/.test(s))s=s.replace(',','.');else s=s.replace(/,/g,'');
 if(!/^\d*\.?\d+$/.test(s))return NaN;var v=parseFloat(s);return neg?-v:v}
var NY=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
function when(s,dmy){s=String(s==null?'':s).trim();if(!s)return null;var m,y,mo,d,h=null,mi=0,se=0,off=null;
 if(m=s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?)?\s*(Z|[+-]\d{2}:?\d{2})?/)){y=+m[1];mo=+m[2];d=+m[3];if(m[4]!=null){h=+m[4];mi=+m[5];se=+(m[6]||0)}off=m[7]||null}
 else if(m=s.match(/^(\d{1,2})[\/.](\d{1,2})[\/.](\d{2,4})(?:,?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?\s*(AM|PM)?)?\s*(Z|[+-]\d{2}:?\d{2})?/i)){mo=+m[1];d=+m[2];y=+m[3];if(y<100)y+=2000;
  if(m[4]!=null){h=+m[4];mi=+m[5];se=+(m[6]||0);if(m[7]){h=h%12+(/pm/i.test(m[7])?12:0)}}off=m[8]||null;if(mo>12&&d<=12||dmy&&d<=12){var x=mo;mo=d;d=x}}
 else return null;
 if(mo<1||mo>12||d<1||d>31)return null;
 if(off&&h!=null){var o=off=='Z'?0:(off[0]=='-'?-1:1)*(+off.slice(1,3)*60+ +off.slice(-2)),ms=Date.UTC(y,mo-1,d,h,mi,se)-o*60000,p={};
  NY.formatToParts(new Date(ms)).forEach(function(x){p[x.type]=x.value});y=+p.year;mo=+p.month;d=+p.day;h=+p.hour;mi=+p.minute}
 return {y:y,mo:mo,d:d,h:h,mi:mi}}
function pad(n){return(n<10?'0':'')+n}
function day(w){var dt=new Date(Date.UTC(w.y,w.mo-1,w.d));if(w.h!=null&&w.h>=18)dt.setUTCDate(dt.getUTCDate()+1);   // after 6 PM ET: the next session, as in Sweep
 if(dt.getUTCDay()==6)dt.setUTCDate(dt.getUTCDate()+2);if(dt.getUTCDay()==0)dt.setUTCDate(dt.getUTCDate()+1);return dt.toISOString().slice(0,10)}
function low(r){return r.map(function(x){return String(x).trim().toLowerCase()})}
function detect(rows){var H=low(rows[0]),ix=function(k){return H.indexOf(k)};
 if(ix('boughttimestamp')>=0&&ix('soldtimestamp')>=0&&ix('pnl')>=0)return{kind:'Tradovate',sym:ix('symbol'),date:function(r){var a=when(r[ix('boughttimestamp')]),b=when(r[ix('soldtimestamp')]);if(!a||!b)return a||b;return(a.y*1e8+a.mo*1e6+a.d*1e4+(a.h||0)*100+a.mi)<=(b.y*1e8+b.mo*1e6+b.d*1e4+(b.h||0)*100+b.mi)?a:b},
  pnl:function(r){return num(r[ix('pnl')])}};
 if(ix('enteredat')>=0&&ix('pnl')>=0)return{kind:'TopstepX',sym:ix('contractname'),date:function(r){return when(r[ix('enteredat')])},
  pnl:function(r){var v=num(r[ix('pnl')]),f=ix('fees')>=0?num(r[ix('fees')]):0,c=ix('commissions')>=0?num(r[ix('commissions')]):0;return v-(isNaN(f)?0:Math.abs(f))-(isNaN(c)?0:Math.abs(c))}};
 var body=rows.slice(1,201),ok=function(i,fn){var n=0,k=0;body.forEach(function(r){if((r[i]||'').trim()){n++;if(fn(r[i]))k++}});return n&&k/n>=.8};
 var dc=-1,vc=-1,fc=-1,tc=-1,sc=-1,dre=/(close|exit|sold|fill|trade).*(date|time)|^date|date$|^time$|datetime|timestamp|^day$|trade ?date/,vre=/net.*(p&?l|profit)|p&?l|pnl|profit|realized|result|gain/;
 H.forEach(function(h,i){if(dc<0&&dre.test(h)&&ok(i,when))dc=i;if(tc<0&&/^time$|hour/.test(h))tc=i;if(sc<0&&/symbol|contract|instrument|ticker/.test(h))sc=i;if(fc<0&&/fee|commission/.test(h))fc=i});
 H.forEach(function(h,i){if(vre.test(h)&&ok(i,function(x){return!isNaN(num(x))})&&(vc<0||/net/.test(h)&&!/net/.test(H[vc])))vc=i});
 if(dc<0||vc<0)return null;return generic(dc,vc,/net/.test(H[vc])?-1:fc,tc==dc?-1:tc,sc)}
function generic(dc,vc,fc,tc,sc){var dmy=S.sep==';'||S.rows.slice(1).some(function(r){var m=String(r[dc]||'').match(/^(\d{1,2})[\/.](\d{1,2})[\/.]/);return m&&+m[1]>12});   // day first: European files
 return{kind:L.generic,sym:sc,date:function(r){var w=when(r[dc],dmy);if(w&&w.h==null&&tc>=0){var m=String(r[tc]||'').match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/i);if(m){w.h=+m[1]%(m[3]?12:24)+(m[3]&&/pm/i.test(m[3])?12:0);w.mi=+m[2]}}return w},
 pnl:function(r){var v=num(r[vc]),f=fc>=0?num(r[fc]):0;return v-(isNaN(f)?0:Math.abs(f))}}}
function load(text,name){err('');$('wr-map').hidden=true;var rows=csv(text);if(rows.length<2)return err(L.err_empty);S.rows=rows;S.name=name;var f=detect(rows);if(!f)return map();run(f)}
function run(f){var tr=[];S.rows.slice(1).forEach(function(r){var w=f.date(r),v=f.pnl(r);if(!w||isNaN(v))return;tr.push({day:day(w),h:w.h,net:Math.round(v*100)/100,sym:f.sym>=0?String(r[f.sym]||'').trim():''})});
 if(tr.length<Math.max(1,(S.rows.length-1)*.5))return f.kind==L.generic&&S.rows.length>1?err(L.err_cols):err(L.err_empty);
 S.trades=tr;S.kind=f.kind;var ms={};tr.forEach(function(x){ms[x.day.slice(0,7)]=1});var keys=Object.keys(ms).sort().reverse();S.month=keys[0];
 $('wr-m').innerHTML=keys.map(function(k){return'<option value="'+k+'">'+mname(k)+'</option>'}).join('');$('wr-mwrap').hidden=keys.length<2;
 $('wr-read').textContent=L.read.replace('{n}',tr.length).replace('{f}',S.name).replace('{k}',S.kind);$('wr-res').hidden=false;open(0)}
function map(){var H=S.rows[0],o=H.map(function(h,i){return'<option value="'+i+'">'+esc(h||('#'+(i+1)))+'</option>'}).join('');$('wr-cd').innerHTML=o;$('wr-cv').innerHTML=o;$('wr-cv').selectedIndex=Math.min(1,H.length-1);$('wr-map').hidden=false;$('wr-res').hidden=true}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function err(m){$('wr-err').textContent=m;$('wr-err').hidden=!m}
function mname(k){return new Date(Date.UTC(+k.slice(0,4),+k.slice(5,7)-1,15)).toLocaleDateString(LOC,{month:'long',year:'numeric',timeZone:'UTC'}).replace(/^./,function(c){return c.toUpperCase()})}
function wd(k,o){return new Date(k+'T12:00:00Z').toLocaleDateString(LOC,Object.assign({timeZone:'UTC'},o))}
function stats(){var tr=S.trades.filter(function(x){return x.day.slice(0,7)==S.month}),days={},dow={},hrs={},hn=0,net=0,wins=0,gain=0,loss=0,best=null,worst=null;
 tr.forEach(function(x){net+=x.net;days[x.day]=(days[x.day]||0)+x.net;if(x.net>0){wins++;gain+=x.net}else if(x.net<0)loss+=x.net;if(!best||x.net>best.net)best=x;if(!worst||x.net<worst.net)worst=x;if(x.h!=null){hn++;hrs[x.h]=(hrs[x.h]||0)+x.net}});
 var dk=Object.keys(days),wd_=dk.filter(function(k){return days[k]>0.004}).length,ld=dk.filter(function(k){return days[k]<-0.004}).length;
 dk.forEach(function(k){var g=new Date(k+'T12:00:00Z').getUTCDay(),o=dow[g]||(dow[g]={v:0,n:0,k:0,day:k});o.v+=days[k];o.n++;if(days[k]>0)o.k++});
 var bd=null;Object.keys(dow).forEach(function(g){if(!bd||dow[g].v>bd.v)bd=dow[g]});var bh=null;if(hn>=tr.length*.5)Object.keys(hrs).forEach(function(h){if(bh==null||hrs[h]>hrs[bh])bh=h});
 return{n:tr.length,days:dk.length,net:net,wr:tr.length?wins/tr.length:0,wd:wd_,ld:ld,fl:dk.length-wd_-ld,best:best,worst:worst,gain:gain,loss:loss,dow:bd,hour:bh==null?null:{h:+bh,v:hrs[bh]}}}
function money(v){return(v>0?'+':'')+cur(v,Math.round(Math.abs(v)*100)%100?2:0)}
function hour(h){return LOC=='en-US'?((h%12)||12)+(h<12?' AM':' PM'):h+' h'}
function cards(s){var H=S.hide,c=[],tone=function(v){return v<0?' neg':''};
 c.push('<small>'+mname(S.month)+'</small><h2>'+L.c1+'</h2>'+(H?'<b class="big">'+pc(100*s.wr,0)+'</b><p>'+L.c1h+'</p>':'<b class="big'+tone(s.net)+'">'+money(s.net)+'</b><p>'+L.c1s.replace('{n}',s.n).replace('{d}',s.days)+'</p>'));
 c.push('<h2>'+L.c2+'</h2><div class="wl"><span><b class="big">'+s.wd+'</b>'+L.c2w+'</span><span><b class="big neg">'+s.ld+'</b>'+L.c2l+'</span></div>'+(s.fl?'<p>'+L.c2s.replace('{f}',s.fl)+'</p>':''));
 var bl=function(x){return esc((x.sym?x.sym+' · ':'')+wd(x.day,{weekday:'long',day:'numeric',month:'long'}))};
 c.push('<h2>'+L.c3+'</h2>'+(H?'<b class="big">'+pc(s.gain>0?100*Math.max(0,s.best.net)/s.gain:0,0)+'</b><p>'+L.c3h+'</p>':'<b class="big'+tone(s.best.net)+'">'+money(s.best.net)+'</b><p>'+bl(s.best)+'</p>'));
 c.push('<h2>'+L.c4+'</h2>'+(H&&s.worst.net<0?'<b class="big">'+pc(s.loss<0?100*s.worst.net/s.loss:0,0)+'</b><p>'+L.c4h+'</p>':H?'<p>'+L.c4s+'</p>':'<b class="big'+tone(s.worst.net)+'">'+money(s.worst.net)+'</b><p>'+bl(s.worst)+'</p>')+(H&&s.worst.net<0||!H?'<p class="soft">'+L.c4s+'</p>':''));
 var dn=s.dow?wd(s.dow.day,{weekday:'long'}):'',dp=s.dow?wd(s.dow.day,{weekday:'long'})+(s.dow.n>1&&LOC!='es'?'s':''):'';
 c.push('<h2>'+L.c5+'</h2><div class="ins"><small>'+L.c5d+'</small><b>'+esc(dn.replace(/^./,function(x){return x.toUpperCase()}))+'</b><p>'+(H?L.c5dh.replace('{k}',s.dow.k).replace('{n}',s.dow.n):L.c5ds.replace('{v}',money(s.dow.v)).replace('{n}',s.dow.n).replace('{w}',esc(dp)))+'</p></div>'
  +(s.hour?'<div class="ins"><small>'+L.c5h+'</small><b>'+hour(s.hour.h)+' '+L.et+'</b>'+(H?'':'<p>'+money(s.hour.v)+'</p>')+'</div>':''));
 c.push('<h2 class="end">'+L.c6+'</h2><div class="cta-row"><a class="btn btn-primary btn-lg" href="'+SIGNUP+'">'+L.start+'</a><button type="button" class="btn btn-line btn-lg" data-dl>'+L.dl+'</button></div>');
 return c}
var dlg=$('wr-story'),cur_=0,C=[];
function open(i){var s=stats();C=cards(s);cur_=i||0;$('wr-bars').innerHTML=C.map(function(){return'<i></i>'}).join('');show();if(!dlg.open)dlg.showModal()}
function show(){$('wr-card').innerHTML=C[cur_]+(cur_<C.length-1?'<p class="hint">'+L.tap+'</p>':'');[].forEach.call($('wr-bars').children,function(b,k){b.className=k<=cur_?'on':''});$('wr-card').classList.remove('in');void $('wr-card').offsetWidth;$('wr-card').classList.add('in');
 var d=$('wr-card').querySelector('[data-dl]');if(d)d.onclick=function(e){e.stopPropagation();png()};$('wr-next').hidden=cur_==C.length-1}
function go(k){var n=cur_+k;if(n<0||n>=C.length)return;cur_=n;show()}
$('wr-next').onclick=function(){go(1)};$('wr-prev').onclick=function(){go(-1)};$('wr-x').onclick=function(){dlg.close()};
dlg.addEventListener('keydown',function(e){if(e.key=='ArrowRight'||e.key==' '&&e.target==dlg){e.preventDefault();go(1)}if(e.key=='ArrowLeft'){e.preventDefault();go(-1)}});
$('wr-file').onchange=function(){var f=this.files&&this.files[0];if(!f)return;var r=new FileReader();r.onload=function(){load(String(r.result),f.name)};r.readAsText(f);this.value=''};
var dz=$('wr-drop');['dragover','dragenter'].forEach(function(e){dz.addEventListener(e,function(v){v.preventDefault();dz.classList.add('over')})});['dragleave','drop'].forEach(function(e){dz.addEventListener(e,function(){dz.classList.remove('over')})});
dz.addEventListener('drop',function(e){e.preventDefault();var f=e.dataTransfer.files&&e.dataTransfer.files[0];if(!f)return;var r=new FileReader();r.onload=function(){load(String(r.result),f.name)};r.readAsText(f)});
$('wr-demo').onclick=function(){load(DEMO,'demo.csv')};
$('wr-use').onclick=function(){var dc=+$('wr-cd').value,vc=+$('wr-cv').value;if(dc==vc)return err(L.err_cols);run(generic(dc,vc,-1,-1,-1))};
$('wr-m').onchange=function(){S.month=this.value};$('wr-hide').onchange=function(){S.hide=this.checked};
$('wr-play').onclick=function(){open(0)};$('wr-dl').onclick=png;
// the card to share: 1080 × 1920, Sweep's art direction (dark glass, Geist, the logo, makeitsweep.com)
function rr(x,a,b,w,h,r){x.beginPath();x.moveTo(a+r,b);x.arcTo(a+w,b,a+w,b+h,r);x.arcTo(a+w,b+h,a,b+h,r);x.arcTo(a,b+h,a,b,r);x.arcTo(a,b,a+w,b,r);x.closePath()}
function png(){var s=stats(),H=S.hide;Promise.all([document.fonts.load('600 80px Geist'),document.fonts.load('500 40px Geist')]).catch(function(){}).then(function(){
 var cv=document.createElement('canvas');cv.width=1080;cv.height=1920;var x=cv.getContext('2d'),F='Geist, -apple-system, system-ui, sans-serif',BLUE='#4C8DFF',GOLD='#D4A24C';
 x.fillStyle='#08080A';x.fillRect(0,0,1080,1920);var g=x.createRadialGradient(540,-200,0,540,-200,1400);g.addColorStop(0,'rgba(76,141,255,.16)');g.addColorStop(1,'rgba(76,141,255,0)');x.fillStyle=g;x.fillRect(0,0,1080,1920);
 x.save();x.translate(96,104);rr(x,0,0,30,38,5);x.fillStyle='#F2F2F3';x.fill();x.strokeStyle=BLUE;x.lineWidth=11;x.lineCap='round';x.beginPath();x.moveTo(15,44);x.lineTo(15,66);x.stroke();x.restore();
 x.fillStyle='#F2F2F3';x.font='600 54px '+F;x.textBaseline='alphabetic';x.fillText('sweep',146,150);
 x.fillStyle='rgba(242,242,243,.6)';x.font='500 40px '+F;x.fillText(L.card_t,96,330);x.fillStyle='#F2F2F3';x.font='600 76px '+F;x.fillText(mname(S.month),96,420);
 var panel=function(y,h){rr(x,72,y,936,h,40);var p=x.createLinearGradient(0,y,0,y+h);p.addColorStop(0,'rgba(255,255,255,.075)');p.addColorStop(1,'rgba(255,255,255,.03)');x.fillStyle=p;x.fill();x.strokeStyle='rgba(255,255,255,.09)';x.lineWidth=2;x.stroke()};
 panel(500,380);x.fillStyle='rgba(242,242,243,.6)';x.font='500 38px '+F;x.fillText(H?L.k_wr:L.k_net,120,590);
 x.font='600 150px '+F;x.fillStyle=H?BLUE:(s.net<0?GOLD:BLUE);x.fillText(H?pc(100*s.wr,0):money(s.net),116,780);
 var rows=[[L.k_days,L.k_of.replace('{a}',s.wd).replace('{b}',s.days)],[L.k_dow,s.dow?wd(s.dow.day,{weekday:'long'}).replace(/^./,function(c){return c.toUpperCase()}):'—']];
 if(!H)rows.splice(1,0,[L.k_best,money(s.best.net)]);
 var y=930;panel(y,rows.length*150+40);rows.forEach(function(r,i){var yy=y+105+i*150;x.fillStyle='rgba(242,242,243,.6)';x.font='500 38px '+F;x.fillText(r[0],120,yy);x.textAlign='right';x.fillStyle='#F2F2F3';x.font='600 46px '+F;x.fillText(r[1],960,yy);x.textAlign='left';
  if(i<rows.length-1){x.fillStyle='rgba(255,255,255,.08)';x.fillRect(120,yy+52,840,2)}});
 x.fillStyle='rgba(242,242,243,.6)';x.font='500 36px '+F;x.fillText(L.slogan,96,1740);x.fillStyle=BLUE;x.font='600 40px '+F;x.fillText('makeitsweep.com',96,1800);
 cv.toBlob(function(b){var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='sweep-wrapped-'+S.month+'.png';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},1500)},'image/png')})}
"""
