/* Sweep — Admin › Emails (brief « Courriels maison », 3 Nov. 2026): our own campaigns, sent from our server.
   Loaded on demand (window.SWEEP_LAZY.mail, vMail in app.js) for an administrator who opens #mail:
   #mail            the last 30 days, the list, the sending pace, the campaigns
   #mail/<id>       a draft: content in EN / FR / ES, audience, preview, test, send · a campaign that went out: its numbers
   Server: mail/mail-admin.php (api/admin/mail…). */
(function () {
  'use strict';
  const T = {
    en: { h: 'Emails', sub: 'Campaigns sent from Sweep’s own server. Only administrators see this page.', nw: 'New campaign', back: 'Emails',
      k: { sent: 'Sent (30 days)', open: 'Open rate', click: 'Click rate', unsub: 'Unsubscribed', bounce: 'Bounces' },
      kSub: { open: '{a} % counting machine opens', click: '{a} % of people who opened', unsub: '{n} people', bounce: '{n} addresses', unsub1: '1 person', bounce1: '1 address' },
      note: 'Opens: Apple Mail and some antivirus software open every email on their own. Those opens are counted apart; clicks are the sure number.',
      camps: 'Campaigns', none: 'No campaign yet. Start with « New campaign ».',
      st: { draft: 'Draft', scheduled: 'Scheduled', sending: 'Sending', paused: 'Paused', sent: 'Sent' },
      row: { sent: '{n} sent', opens: '{a} % opened', clicks: '{a} % clicked', at: 'for {d}', edited: 'edited {d}' },
      list: 'The list', reach: '{n} traders can receive campaigns', off: '{n} unsubscribed', sup: '{n} set aside (bounce or complaint)',
      pace: 'Sending pace', paceL: '{a} of {b} this hour · {q} waiting', paceW: 'The hourly cap doubles each week from the first email, up to {m}: a new sending address earns its reputation slowly.', paceN: 'Cap at the start: {b} an hour, doubled each week up to {m}.',
      noSmtp: 'No mailbox (SMTP) in config.php: nothing can go out.', addr: 'Postal address at the bottom of every email', addrHelp: 'Required by anti-spam laws (CASL, CAN-SPAM). Your full address.', save: 'Save', saved: 'Saved',
      name: 'Name (only you see it)', namePh: 'November news', content: 'Content', subject: 'Subject', pre: 'Preview text (grey, after the subject)', body: 'Message',
      tools: { h: 'Title', b: 'Bold', l: 'Link', btn: 'Button', first: 'First name' }, linkTxt: 'text', btnTxt: 'Open Sweep',
      help: 'A blank line starts a new paragraph. {first} becomes the trader’s first name. An empty language gets the English version.',
      prev: 'Preview', prevNone: 'Write a subject and a message to see the email.', aud: 'Audience',
      aLang: 'Language', aPlan: 'Plan', aAct: 'Activity', all: 'All', act: { a0: 'All', j30: 'Joined < 30 days', a7: 'Active 7 days', a30: 'Active 30 days', i14: 'Inactive 14 days', i30: 'Inactive 30 days', i60: 'Inactive 60 days' },
      count: 'Reaches {n} traders', countL: 'EN {en} · FR {fr} · ES {es}', send: 'Sending', test: 'Send me a test', testOk: 'Test sent to {e}', now: 'Send now', at: 'Schedule', del: 'Delete',
      schedFor: 'Scheduled for {d}. It leaves on its own at that time.', unsched: 'Cancel the schedule',
      askSend: 'Send « {n} » to {c} traders?', askSendS: 'It starts within a minute, at the pace of the hourly cap. An email that went out cannot be taken back.', askGo: 'Send',
      askDel: 'Delete « {n} »?', askDelS: 'The draft is removed.', askDelGo: 'Delete',
      err: { name: 'Give the campaign a name.', content: 'Write at least a subject and a message (English, or the language of the audience).', no_email: 'Your account has no email address.', send: 'The mailbox refused: {d}', at: 'Choose a time within 90 days.', sent: 'This campaign already went out.' },
      pause: 'Pause', resume: 'Resume', dup: 'Duplicate', paused: { bounces: 'Paused on its own: more than 3 % of addresses bounced. Check the list before resuming.', complaints: 'Paused on its own: too many people marked it as spam.', manual: 'Paused.' },
      prog: '{a} of {b} sent', rk: { delivered: 'Delivered', opens: 'Opened', clicks: 'Clicked', cto: 'Clicked after opening', unsub: 'Unsubscribed', bounce: 'Bounced', compl: 'Marked as spam' },
      auto: '+ {n} machine opens (Apple Mail, antivirus) not counted', auto1: '+ 1 machine open (Apple Mail, antivirus) not counted', h48: 'The first 48 hours', leg: ['Opened', 'Clicked'], hrs: '{h} h',
      byLang: 'By language', links: 'Most clicked links', noLinks: 'No click yet.', lg: { en: 'English', fr: 'French', es: 'Spanish' }, sent2: 'Sent', shown: 'What was sent',
      saving: 'Saving…', savedAt: 'Saved', untitled: 'New campaign' },
    fr: { h: 'Courriels', sub: 'Campagnes envoyées par le serveur de Sweep. Seuls les administrateurs voient cette page.', nw: 'Nouvelle campagne', back: 'Courriels',
      k: { sent: 'Envoyés (30 jours)', open: 'Taux d’ouverture', click: 'Taux de clic', unsub: 'Désinscriptions', bounce: 'Rebonds' },
      kSub: { open: '{a} % avec les ouvertures automatiques', click: '{a} % de ceux qui ont ouvert', unsub: '{n} personnes', bounce: '{n} adresses', unsub1: '1 personne', bounce1: '1 adresse' },
      note: 'Ouvertures : Apple Mail et certains antivirus ouvrent chaque courriel tout seuls. Ces ouvertures sont comptées à part ; les clics sont le chiffre sûr.',
      camps: 'Campagnes', none: 'Aucune campagne pour l’instant. Commence par « Nouvelle campagne ».',
      st: { draft: 'Brouillon', scheduled: 'Planifiée', sending: 'En cours', paused: 'En pause', sent: 'Envoyée' },
      row: { sent: '{n} envoyés', opens: '{a} % ouverts', clicks: '{a} % de clics', at: 'pour le {d}', edited: 'modifiée le {d}' },
      list: 'La liste', reach: '{n} traders peuvent recevoir les campagnes', off: '{n} désinscrits', sup: '{n} mis de côté (rebond ou plainte)',
      pace: 'Rythme d’envoi', paceL: '{a} sur {b} cette heure · {q} en attente', paceW: 'Le plafond par heure double chaque semaine à partir du premier courriel, jusqu’à {m} : une nouvelle adresse d’envoi gagne sa réputation lentement.', paceN: 'Plafond au départ : {b} par heure, doublé chaque semaine jusqu’à {m}.',
      noSmtp: 'Aucune boîte (SMTP) dans config.php : rien ne peut partir.', addr: 'Adresse postale au bas de chaque courriel', addrHelp: 'Exigée par les lois anti-pourriel (LCAP, CAN-SPAM). Ton adresse complète.', save: 'Enregistrer', saved: 'Enregistré',
      name: 'Nom (toi seul le vois)', namePh: 'Nouvelles de novembre', content: 'Contenu', subject: 'Objet', pre: 'Texte d’aperçu (gris, après l’objet)', body: 'Message',
      tools: { h: 'Titre', b: 'Gras', l: 'Lien', btn: 'Bouton', first: 'Prénom' }, linkTxt: 'texte', btnTxt: 'Ouvrir Sweep',
      help: 'Une ligne vide commence un nouveau paragraphe. {first} devient le prénom du trader. Une langue vide reçoit la version anglaise.',
      prev: 'Aperçu', prevNone: 'Écris un objet et un message pour voir le courriel.', aud: 'Audience',
      aLang: 'Langue', aPlan: 'Forfait', aAct: 'Activité', all: 'Toutes', act: { a0: 'Tous', j30: 'Inscrits < 30 jours', a7: 'Actifs 7 jours', a30: 'Actifs 30 jours', i14: 'Inactifs 14 jours', i30: 'Inactifs 30 jours', i60: 'Inactifs 60 jours' },
      count: 'Rejoint {n} traders', countL: 'EN {en} · FR {fr} · ES {es}', send: 'Envoi', test: 'M’envoyer un test', testOk: 'Test envoyé à {e}', now: 'Envoyer maintenant', at: 'Planifier', del: 'Supprimer',
      schedFor: 'Planifiée pour le {d}. Elle part toute seule à cette heure.', unsched: 'Annuler la planification',
      askSend: 'Envoyer « {n} » à {c} traders ?', askSendS: 'L’envoi commence dans la minute, au rythme du plafond par heure. Un courriel parti ne se reprend pas.', askGo: 'Envoyer',
      askDel: 'Supprimer « {n} » ?', askDelS: 'Le brouillon est effacé.', askDelGo: 'Supprimer',
      err: { name: 'Donne un nom à la campagne.', content: 'Écris au moins un objet et un message (en anglais, ou dans la langue de l’audience).', no_email: 'Ton compte n’a pas d’adresse courriel.', send: 'La boîte a refusé : {d}', at: 'Choisis une heure dans les 90 prochains jours.', sent: 'Cette campagne est déjà partie.' },
      pause: 'Mettre en pause', resume: 'Reprendre', dup: 'Dupliquer', paused: { bounces: 'Mise en pause toute seule : plus de 3 % des adresses ont rebondi. Vérifie la liste avant de reprendre.', complaints: 'Mise en pause toute seule : trop de personnes l’ont signalée comme indésirable.', manual: 'En pause.' },
      prog: '{a} sur {b} envoyés', rk: { delivered: 'Livrés', opens: 'Ouverts', clicks: 'Cliqués', cto: 'Clics après ouverture', unsub: 'Désinscrits', bounce: 'Rebonds', compl: 'Signalés indésirables' },
      auto: '+ {n} ouvertures automatiques (Apple Mail, antivirus) non comptées', auto1: '+ 1 ouverture automatique (Apple Mail, antivirus) non comptée', h48: 'Les 48 premières heures', leg: ['Ouverts', 'Cliqués'], hrs: '{h} h',
      byLang: 'Par langue', links: 'Liens les plus cliqués', noLinks: 'Aucun clic pour l’instant.', lg: { en: 'Anglais', fr: 'Français', es: 'Espagnol' }, sent2: 'Envoyés', shown: 'Ce qui a été envoyé',
      saving: 'Enregistrement…', savedAt: 'Enregistré', untitled: 'Nouvelle campagne' },
    es: { h: 'Correos', sub: 'Campañas enviadas desde el servidor de Sweep. Solo los administradores ven esta página.', nw: 'Nueva campaña', back: 'Correos',
      k: { sent: 'Enviados (30 días)', open: 'Tasa de apertura', click: 'Tasa de clics', unsub: 'Bajas', bounce: 'Rebotes' },
      kSub: { open: '{a} % con las aperturas automáticas', click: '{a} % de quienes abrieron', unsub: '{n} personas', bounce: '{n} direcciones', unsub1: '1 persona', bounce1: '1 dirección' },
      note: 'Aperturas: Apple Mail y algunos antivirus abren cada correo por sí solos. Esas aperturas se cuentan aparte; los clics son la cifra segura.',
      camps: 'Campañas', none: 'Ninguna campaña por ahora. Empieza con « Nueva campaña ».',
      st: { draft: 'Borrador', scheduled: 'Programada', sending: 'Enviando', paused: 'En pausa', sent: 'Enviada' },
      row: { sent: '{n} enviados', opens: '{a} % abiertos', clicks: '{a} % de clics', at: 'para el {d}', edited: 'editada el {d}' },
      list: 'La lista', reach: '{n} traders pueden recibir las campañas', off: '{n} dados de baja', sup: '{n} apartados (rebote o queja)',
      pace: 'Ritmo de envío', paceL: '{a} de {b} esta hora · {q} en espera', paceW: 'El límite por hora se duplica cada semana desde el primer correo, hasta {m}: una nueva dirección de envío gana su reputación poco a poco.', paceN: 'Límite al inicio: {b} por hora, duplicado cada semana hasta {m}.',
      noSmtp: 'Ningún buzón (SMTP) en config.php: nada puede salir.', addr: 'Dirección postal al pie de cada correo', addrHelp: 'Exigida por las leyes antispam (CASL, CAN-SPAM). Tu dirección completa.', save: 'Guardar', saved: 'Guardado',
      name: 'Nombre (solo tú lo ves)', namePh: 'Novedades de noviembre', content: 'Contenido', subject: 'Asunto', pre: 'Texto de vista previa (gris, después del asunto)', body: 'Mensaje',
      tools: { h: 'Título', b: 'Negrita', l: 'Enlace', btn: 'Botón', first: 'Nombre' }, linkTxt: 'texto', btnTxt: 'Abrir Sweep',
      help: 'Una línea vacía empieza un párrafo nuevo. {first} se convierte en el nombre del trader. Un idioma vacío recibe la versión en inglés.',
      prev: 'Vista previa', prevNone: 'Escribe un asunto y un mensaje para ver el correo.', aud: 'Audiencia',
      aLang: 'Idioma', aPlan: 'Plan', aAct: 'Actividad', all: 'Todos', act: { a0: 'Todos', j30: 'Inscritos < 30 días', a7: 'Activos 7 días', a30: 'Activos 30 días', i14: 'Inactivos 14 días', i30: 'Inactivos 30 días', i60: 'Inactivos 60 días' },
      count: 'Llega a {n} traders', countL: 'EN {en} · FR {fr} · ES {es}', send: 'Envío', test: 'Enviarme una prueba', testOk: 'Prueba enviada a {e}', now: 'Enviar ahora', at: 'Programar', del: 'Eliminar',
      schedFor: 'Programada para el {d}. Sale sola a esa hora.', unsched: 'Cancelar la programación',
      askSend: '¿Enviar « {n} » a {c} traders?', askSendS: 'El envío empieza en un minuto, al ritmo del límite por hora. Un correo enviado no se puede recuperar.', askGo: 'Enviar',
      askDel: '¿Eliminar « {n} »?', askDelS: 'El borrador se borra.', askDelGo: 'Eliminar',
      err: { name: 'Ponle un nombre a la campaña.', content: 'Escribe al menos un asunto y un mensaje (en inglés, o en el idioma de la audiencia).', no_email: 'Tu cuenta no tiene dirección de correo.', send: 'El buzón rechazó: {d}', at: 'Elige una hora dentro de los próximos 90 días.', sent: 'Esta campaña ya salió.' },
      pause: 'Pausar', resume: 'Reanudar', dup: 'Duplicar', paused: { bounces: 'Pausada sola: más del 3 % de las direcciones rebotaron. Revisa la lista antes de reanudar.', complaints: 'Pausada sola: demasiadas personas la marcaron como spam.', manual: 'En pausa.' },
      prog: '{a} de {b} enviados', rk: { delivered: 'Entregados', opens: 'Abiertos', clicks: 'Con clic', cto: 'Clics tras abrir', unsub: 'Bajas', bounce: 'Rebotes', compl: 'Marcados como spam' },
      auto: '+ {n} aperturas automáticas (Apple Mail, antivirus) no contadas', auto1: '+ 1 apertura automática (Apple Mail, antivirus) no contada', h48: 'Las primeras 48 horas', leg: ['Abiertos', 'Con clic'], hrs: '{h} h',
      byLang: 'Por idioma', links: 'Enlaces más pulsados', noLinks: 'Ningún clic por ahora.', lg: { en: 'Inglés', fr: 'Francés', es: 'Español' }, sent2: 'Enviados', shown: 'Lo que se envió',
      saving: 'Guardando…', savedAt: 'Guardado', untitled: 'Nueva campaña' },
  };
  const x = () => T[LANG] || T.en;
  const f = (s, p) => String(s).replace(/\{(\w+)\}/g, (m, k) => (p && p[k] != null ? p[k] : m));
  const h = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const loc = () => (typeof LOC === 'function' ? LOC() : 'en-US');
  const num = (n) => Number(n || 0).toLocaleString(loc());
  const pct = (v) => (v == null ? '—' : Number(v).toLocaleString(loc(), { maximumFractionDigits: 1 }));
  const when = (ts) => new Date(ts * 1000).toLocaleString(loc(), { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  const LANGS = ['en', 'fr', 'es'];
  const ACT = { a0: {}, j30: { joined: 30 }, a7: { active: 7 }, a30: { active: 30 }, i14: { inactive: 14 }, i30: { inactive: 30 }, i60: { inactive: 60 } };
  const actOf = (a) => Object.keys(ACT).find((k) => ['joined', 'active', 'inactive'].every((n) => (ACT[k][n] || 0) === (a[n] || 0))) || 'a0';
  const M = { ov: null, ovAt: 0, rep: {}, repAt: {}, edit: null, editId: 0, tab: 'en', aud: null, prev: null, msg: '', msgBad: false, saveT: 0, prevT: 0, saving: 0 };
  const api = (path, body, method) => apiJSON(path, body !== undefined ? { method: method || 'POST', body } : method ? { method } : {});
  const errText = (e) => { const c = e && e.data && e.data.error; return (c && x().err[c]) ? f(x().err[c], { d: (e.data.detail || '').slice(0, 120) }) : (e && e.message) || 'Error'; };
  const here = () => route().v === 'mail';
  const repaint = () => { if (here() && typeof render === 'function') render(); };

  /* ───── #mail: overview ───── */
  function loadOv(force) {
    if (M.ovBusy || (!force && M.ov && Date.now() - M.ovAt < 30000)) return;
    M.ovBusy = true;
    api('api/admin/mail').then((d) => { M.ov = d; M.ovAt = Date.now(); M.ovBusy = false; repaint(); }).catch((e) => { M.ovBusy = false; M.ovErr = errText(e); repaint(); });
  }
  const kpi = (label, value, sub) => `<div class="ux-m"><small>${h(label)}</small><b>${value}</b>${sub ? `<span>${h(sub)}</span>` : ''}</div>`;
  const chip = (st) => `<span class="ml-st ml-st-${h(st)}">${h(x().st[st] || st)}</span>`;
  function vList() {
    loadOv();
    const X = x(), d = M.ov;
    if (!d) return `<section class="sec ml" data-noi18n>${M.ovErr ? `<div class="empty">${h(M.ovErr)}</div>` : SKELETON}</section>`;
    const m = d.month, L = d.list, P = d.sending;
    const rows = d.campaigns.map((c) => {
      const info = c.status === 'draft' ? f(X.row.edited, { d: when(c.updated_at) }) : c.status === 'scheduled' ? f(X.row.at, { d: when(c.scheduled_at) })
        : [f(X.row.sent, { n: num(c.sent) }), c.open_rate != null ? f(X.row.opens, { a: pct(c.open_rate) }) : '', c.click_rate != null ? f(X.row.clicks, { a: pct(c.click_rate) }) : '', c.started_at ? when(c.started_at) : ''].filter(Boolean).join(' · ');
      return `<li><a class="ml-row" href="#mail/${c.id}"><div><b>${h(c.name || X.untitled)}</b>${chip(c.status)}</div><small>${h(info)}</small></a></li>`;
    }).join('');
    return `<section class="sec ml" data-noi18n>
      <div class="sec-h ml-head"><p class="muted ml-sub">${h(X.sub)}</p><button type="button" class="btn primary ml-new" data-ml="new">${h(X.nw)}</button></div>
      ${d.smtp ? '' : `<div class="ml-alert" role="alert">${h(X.noSmtp)}</div>`}
      <div class="ux-mgrid ml-kpis">${kpi(X.k.sent, num(m.sent))}${kpi(X.k.open, m.open_rate != null ? pct(m.open_rate) + ' %' : '—', m.open_rate_all != null ? f(X.kSub.open, { a: pct(m.open_rate_all) }) : '')}
        ${kpi(X.k.click, m.click_rate != null ? pct(m.click_rate) + ' %' : '—', m.click_to_open != null ? f(X.kSub.click, { a: pct(m.click_to_open) }) : '')}
        ${kpi(X.k.unsub, m.unsub_rate != null ? pct(m.unsub_rate) + ' %' : '—', m.unsubs === 1 ? X.kSub.unsub1 : f(X.kSub.unsub, { n: num(m.unsubs) }))}${kpi(X.k.bounce, m.bounce_rate != null ? pct(m.bounce_rate) + ' %' : '—', m.bounces === 1 ? X.kSub.bounce1 : f(X.kSub.bounce, { n: num(m.bounces) }))}</div>
      <p class="muted ml-note">${h(X.note)}</p>
      <h3 class="ml-h3">${h(X.camps)}</h3>
      ${rows ? `<ul class="ml-list">${rows}</ul>` : `<p class="muted ml-empty">${h(X.none)}</p>`}
      <div class="ml-two">
        <div class="ml-box"><h4>${h(X.list)}</h4><p><b>${h(f(X.reach, { n: num(L.reachable) }))}</b></p><p class="muted">${h(f(X.off, { n: num(L.unsubscribed) }))} · ${h(f(X.sup, { n: num(L.suppressed) }))}</p></div>
        <div class="ml-box"><h4>${h(X.pace)}</h4><p><b>${h(f(X.paceL, { a: num(P.last_hour), b: num(P.cap), q: num(P.left) }))}</b></p><p class="muted">${h(f(P.warm_start ? X.paceW : X.paceN, { b: num(P.cap), m: num(P.max) }))}</p></div>
      </div>
      <details class="ml-set"><summary>${h(X.addr)}</summary><p class="muted">${h(X.addrHelp)}</p>
        <div class="ml-inline"><input type="text" data-ml-addr maxlength="200" value="${h(d.address)}" aria-label="${h(X.addr)}"><button type="button" class="btn" data-ml="addr">${h(X.save)}</button></div></details>
    </section>`;
  }

  /* ───── #mail/<id> ───── */
  function loadRep(id, force) {
    if (M['rb' + id] || (!force && M.rep[id] && Date.now() - (M.repAt[id] || 0) < 30000)) return;
    M['rb' + id] = true;
    api('api/admin/mail/campaigns/' + id).then((d) => {
      M['rb' + id] = false; M.rep[id] = d; M.repAt[id] = Date.now();
      const c = d.campaign;
      if (['draft', 'scheduled'].includes(c.status) && M.editId !== id) { M.edit = { name: c.name, content: c.content, audience: c.audience }; M.editId = id; M.aud = d.audience_count != null ? { count: d.audience_count } : null; M.prev = null; M.msg = ''; countAud(); }
      repaint(); if (M.editId === id) refreshPrev();
    }).catch((e) => { M['rb' + id] = false; M.repErr = errText(e); repaint(); });
  }
  function vCampaign(id) {
    const d = M.rep[id]; loadRep(id);
    const X = x(), back = '';
    if (d && ['draft', 'scheduled'].includes(d.campaign.status) && M.editId !== id) { delete M.rep[id]; loadRep(id, true); }   // another draft was open: its latest saved version
    if (!M.rep[id]) return `<section class="sec ml" data-noi18n>${back}${M.repErr ? `<div class="empty">${h(M.repErr)}</div>` : SKELETON}</section>`;
    return ['draft', 'scheduled'].includes(d.campaign.status) && M.editId === id ? vEditor(id, d) : vReport(id, d);
  }
  const filled = (v) => v && v.subject.trim() && v.body.trim();
  function vEditor(id, d) {
    const X = x(), E = M.edit, v = E.content[M.tab], c = d.campaign, sched = c.status === 'scheduled';
    const tabs = LANGS.map((l) => `<button type="button" class="chip ${M.tab === l ? 'on' : ''}" data-ml="tab" data-v="${l}" aria-pressed="${M.tab === l}">${l.toUpperCase()}${filled(E.content[l]) ? ' ✓' : ''}</button>`).join('');
    const row = (label, k, opts) => `<div class="ml-arow"><span>${h(label)}</span><div class="ml-chips">${opts.map(([val, lab]) => `<button type="button" class="chip ${String(E.audience[k] || '') === String(val) ? 'on' : ''}" data-ml="aud" data-k="${k}" data-v="${val}">${h(lab)}</button>`).join('')}</div></div>`;
    const act = actOf(E.audience);
    const A = M.aud;
    const soon = new Date(Date.now() + 3600e3); soon.setMinutes(0, 0, 0);
    const lv = (t) => { const z = new Date(t - new Date(t).getTimezoneOffset() * 60e3); return z.toISOString().slice(0, 16); };
    return `<section class="sec ml ml-ed" data-noi18n>
      <div class="sec-h"><h2>${h(E.name || X.untitled)}</h2>${chip(c.status)}<small class="muted ml-saved" data-ml-saved>${M.saving ? h(X.saving) : ''}</small></div>
      <label class="ml-f"><span>${h(X.name)}</span><input type="text" data-mlf="name" maxlength="120" value="${h(E.name)}" placeholder="${h(X.namePh)}"></label>
      <h3 class="ml-h3">${h(X.content)}</h3>
      <div class="ml-chips ml-tabs" role="group" aria-label="${h(X.content)}">${tabs}</div>
      <label class="ml-f"><span>${h(X.subject)}</span><input type="text" data-mlf="subject" maxlength="200" value="${h(v.subject)}"></label>
      <label class="ml-f"><span>${h(X.pre)}</span><input type="text" data-mlf="preheader" maxlength="200" value="${h(v.preheader)}"></label>
      <div class="ml-f"><span id="ml-body-l">${h(X.body)}</span>
        <div class="ml-chips ml-tools">${Object.entries(X.tools).map(([k, lab]) => `<button type="button" class="chip" data-ml="tool" data-v="${k}">${h(lab)}</button>`).join('')}</div>
        <textarea data-mlf="body" rows="12" aria-labelledby="ml-body-l">${h(v.body)}</textarea><small class="muted">${h(X.help)}</small></div>
      <h3 class="ml-h3">${h(X.prev)}</h3>
      <div class="ml-prev" data-ml-prev aria-label="${h(X.prev)}"></div>
      <h3 class="ml-h3">${h(X.aud)}</h3>
      ${row(X.aLang, 'lang', [['', X.all], ['en', 'EN'], ['fr', 'FR'], ['es', 'ES']])}
      ${row(X.aPlan, 'plan', [['', X.all], ['free', 'Free'], ['pro', 'Pro'], ['elite', 'Elite']])}
      <div class="ml-arow"><span>${h(X.aAct)}</span><div class="ml-chips">${Object.keys(ACT).map((k) => `<button type="button" class="chip ${act === k ? 'on' : ''}" data-ml="act" data-v="${k}">${h(X.act[k])}</button>`).join('')}</div></div>
      <p class="ml-count" data-ml-count>${A ? `<b>${h(f(X.count, { n: num(A.count) }))}</b>${A.langs ? ` <span class="muted">${h(f(X.countL, A.langs))}</span>` : ''}` : '…'}</p>
      <h3 class="ml-h3">${h(X.send)}</h3>
      ${sched ? `<p class="ml-sched">${h(f(X.schedFor, { d: when(c.scheduled_at) }))}</p><div class="ml-acts"><button type="button" class="btn" data-ml="unsched">${h(X.unsched)}</button></div>`
        : `<div class="ml-acts"><button type="button" class="btn" data-ml="test">${h(X.test)}</button><button type="button" class="btn primary" data-ml="now">${h(X.now)}</button></div>
           <div class="ml-inline ml-at"><input type="datetime-local" data-ml-at value="${lv(soon.getTime())}" min="${lv(Date.now())}" aria-label="${h(X.at)}"><button type="button" class="btn" data-ml="at">${h(X.at)}</button></div>`}
      <p class="ml-msg ${M.msgBad ? 'bad' : ''}" role="status" data-ml-msg>${h(M.msg)}</p>
      <div class="ml-acts ml-del"><button type="button" class="btn danger" data-ml="del">${h(X.del)}</button></div>
    </section>`;
  }
  function bars(hours) {
    const max = Math.max(1, ...hours.map((r) => r[0])), W = 480, H = 110, bw = W / 48;
    const b = hours.map((r, i) => `<rect x="${(i * bw + 1).toFixed(1)}" y="${(H - (r[0] / max) * H).toFixed(1)}" width="${(bw - 2).toFixed(1)}" height="${((r[0] / max) * H).toFixed(1)}" rx="2" class="ml-bo"><title>${i} h: ${r[0]} / ${r[1]}</title></rect>`
      + (r[1] ? `<rect x="${(i * bw + 1).toFixed(1)}" y="${(H - (r[1] / max) * H).toFixed(1)}" width="${(bw - 2).toFixed(1)}" height="${((r[1] / max) * H).toFixed(1)}" rx="2" class="ml-bc"/>` : '')).join('');
    const X = x();
    return `<svg class="ml-bars" viewBox="0 0 ${W} ${H + 18}" role="img" aria-label="${h(X.h48)}">${b}<line x1="0" x2="${W}" y1="${H + .5}" y2="${H + .5}" class="ml-ax"/>
      ${[0, 12, 24, 36, 47].map((t) => `<text x="${(t * bw + bw / 2).toFixed(1)}" y="${H + 14}" text-anchor="${t === 0 ? 'start' : t === 47 ? 'end' : 'middle'}">${h(f(X.hrs, { h: t === 47 ? 48 : t }))}</text>`).join('')}</svg>
      <p class="ml-leg"><i class="ml-bo"></i>${h(X.leg[0])}<i class="ml-bc"></i>${h(X.leg[1])}</p>`;
  }
  function vReport(id, d) {
    const X = x(), c = d.campaign, s = d.stats, live = c.status === 'sending' || c.status === 'paused';
    if (live && Date.now() - (M.repAt[id] || 0) > 30000) loadRep(id, true);
    const r = (v) => (v == null ? '—' : pct(v) + ' %');
    const langs = d.langs.map((l) => `<tr><td>${h(X.lg[l.lang])}</td><td class="ml-n">${num(l.sent)}</td><td class="ml-n">${r(l.open_rate)}</td><td class="ml-n">${r(l.click_rate)}</td></tr>`).join('');
    const links = d.links.map((l) => `<li><span>${h(l.url.replace(/^https?:\/\//, ''))}</span><b>${num(l.clicks)}</b></li>`).join('');
    const done = s.recipients ? Math.round(((s.sent + s.failed + s.skipped) / s.recipients) * 100) : 100;
    return `<section class="sec ml ml-rep" data-noi18n>
      <div class="sec-h"><h2>${h(c.name)}</h2>${chip(c.status)}<div class="ml-acts ml-top">${c.status === 'sending' ? `<button type="button" class="btn sm" data-ml="pause">${h(X.pause)}</button>` : c.status === 'paused' ? `<button type="button" class="btn sm primary" data-ml="resume">${h(X.resume)}</button>` : ''}<button type="button" class="btn sm" data-ml="dup">${h(X.dup)}</button></div></div>
      ${c.status === 'paused' ? `<div class="ml-alert" role="alert">${h(X.paused[c.paused_reason] || X.paused.manual)}</div>` : ''}
      <div class="ml-progress" role="progressbar" aria-valuenow="${done}" aria-valuemin="0" aria-valuemax="100"><i style="width:${done}%"></i></div>
      <p class="muted ml-pl">${h(f(X.prog, { a: num(s.sent), b: num(s.recipients) }))}${c.started_at ? ' · ' + h(when(c.started_at)) : ''}</p>
      <div class="ux-mgrid ml-kpis">${kpi(X.rk.delivered, num(s.delivered))}${kpi(X.rk.opens, r(s.open_rate), num(s.opens))}${kpi(X.rk.clicks, r(s.click_rate), num(s.clicks))}${kpi(X.rk.cto, r(s.click_to_open))}
        ${kpi(X.rk.unsub, r(s.unsub_rate), num(s.unsubs))}${kpi(X.rk.bounce, r(s.bounce_rate), num(s.bounces))}${kpi(X.rk.compl, num(s.complaints))}</div>
      ${s.opens_auto ? `<p class="muted ml-note">${h(s.opens_auto === 1 ? X.auto1 : f(X.auto, { n: num(s.opens_auto) }))}</p>` : ''}
      <h3 class="ml-h3">${h(X.h48)}</h3>${bars(d.hours)}
      <div class="ml-two">
        <div class="ml-box"><h4>${h(X.byLang)}</h4>${langs ? `<table class="ml-tbl"><thead><tr><th></th><th class="ml-n">${h(X.sent2)}</th><th class="ml-n">${h(X.rk.opens)}</th><th class="ml-n">${h(X.rk.clicks)}</th></tr></thead><tbody>${langs}</tbody></table>` : '<p class="muted">—</p>'}</div>
        <div class="ml-box"><h4>${h(X.links)}</h4>${links ? `<ul class="ml-links">${links}</ul>` : `<p class="muted">${h(X.noLinks)}</p>`}</div>
      </div>
      <details class="ml-set ml-shown"><summary>${h(X.shown)}</summary><div class="ml-chips ml-tabs">${LANGS.map((l) => `<button type="button" class="chip ${M.tab === l ? 'on' : ''}" data-ml="rtab" data-v="${l}">${l.toUpperCase()}</button>`).join('')}</div><div class="ml-prev" data-ml-prev></div></details>
    </section>`;
  }

  /* ───── the preview: the email's own HTML in a shadow root (its styles never touch the app's) ───── */
  function paintPrev() {
    const box = document.querySelector('#main [data-ml-prev]'); if (!box) return;
    const root = box.shadowRoot || box.attachShadow({ mode: 'open' });
    const p = M.prev;
    if (!p) { root.innerHTML = `<p style="margin:0;padding:24px;font:14px/1.5 -apple-system,system-ui,sans-serif;color:#8a8a94">${h(x().prevNone)}</p>`; return; }
    const style = (p.html.match(/<body[^>]*style="([^"]*)"/) || [])[1] || '';
    const inner = p.html.replace(/^[\s\S]*?<body[^>]*>/, '').replace(/<\/body>[\s\S]*$/, '').replace(/<img [^>]*api\/m\/o\/[^>]*>/g, '');
    root.innerHTML = `<div style="${style};border-radius:20px;overflow:hidden"><div style="max-width:520px;margin:0 auto 14px;font-size:13px;color:#9a9aa2"><b style="color:#f2f2f3">${h(p.subject)}</b></div>${inner}</div>`;
  }
  function refreshPrev(now) {
    clearTimeout(M.prevT);
    M.prevT = setTimeout(() => {
      const id = route().arg | 0, d = M.rep[id]; if (!d) return;
      const content = M.editId === id ? M.edit.content : d.campaign.content;
      api('api/admin/mail/preview', { content, lang: M.tab }).then((p) => { M.prev = p; paintPrev(); }).catch(() => { M.prev = null; paintPrev(); });
    }, now ? 0 : 400);
  }
  function countAud() {
    clearTimeout(M.audT);
    M.audT = setTimeout(() => {
      if (!M.edit) return;
      api('api/admin/mail/audience', { audience: M.edit.audience }).then((a) => {
        M.aud = a; const el = document.querySelector('#main [data-ml-count]');
        if (el) el.innerHTML = `<b>${h(f(x().count, { n: num(a.count) }))}</b> <span class="muted">${h(f(x().countL, a.langs))}</span>`;
      }).catch(() => {});
    }, 250);
  }
  function save(now) {
    clearTimeout(M.saveT);
    const id = M.editId; if (!id) return Promise.resolve();
    const go = () => { M.saving++; paintSaved(); return api('api/admin/mail/campaigns/' + id, { name: M.edit.name, content: M.edit.content, audience: M.edit.audience }).catch((e) => setMsg(errText(e), true)).finally(() => { M.saving--; paintSaved(true); }); };
    if (now) return go();
    M.saveT = setTimeout(go, 700); return Promise.resolve();
  }
  function paintSaved(done) { const el = document.querySelector('#main [data-ml-saved]'); if (el) el.textContent = M.saving ? x().saving : done ? x().savedAt : ''; }
  function setMsg(t, bad) { M.msg = t; M.msgBad = !!bad; const el = document.querySelector('#main [data-ml-msg]'); if (el) { el.textContent = t; el.classList.toggle('bad', !!bad); } }

  /* ───── events ───── */
  document.addEventListener('input', (e) => {
    const el = e.target; if (!here() || !el.closest || !el.closest('.ml-ed')) return;
    const k = el.dataset && el.dataset.mlf; if (!k || !M.edit) return;
    if (k === 'name') M.edit.name = el.value; else M.edit.content[M.tab][k] = el.value;
    if (k === 'subject' || k === 'body') { const t = document.querySelector(`#main .ml-tabs [data-v="${M.tab}"]`); if (t) t.textContent = M.tab.toUpperCase() + (filled(M.edit.content[M.tab]) ? ' ✓' : ''); }
    save(); if (k !== 'name') refreshPrev();
  });
  function insert(kind) {
    const ta = document.querySelector('#main textarea[data-mlf="body"]'); if (!ta) return;
    const X = x(), a = ta.selectionStart, b = ta.selectionEnd, v = ta.value, sel = v.slice(a, b);
    let add, caret;
    if (kind === 'h') { const ls = v.lastIndexOf('\n', a - 1) + 1; ta.value = v.slice(0, ls) + '# ' + v.slice(ls); caret = b + 2; }
    else {
      add = kind === 'b' ? `**${sel || X.tools.b}**` : kind === 'l' ? `[${sel || X.linkTxt}](https://)` : kind === 'btn' ? `\n\n[[${sel || X.btnTxt}|https://app.makeitsweep.com/]]\n\n` : '{first}';
      ta.value = v.slice(0, a) + add + v.slice(b); caret = a + add.length - (kind === 'l' ? 1 : 0);
    }
    ta.focus(); ta.setSelectionRange(caret, caret); ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('[data-ml]'); if (!b || !here()) return;
    e.preventDefault();
    const X = x(), k = b.dataset.ml, id = route().arg | 0;
    try {
      if (k === 'new') { b.disabled = true; const r = await api('api/admin/mail/campaigns', { name: '', content: {}, audience: {} }); M.ov = null; location.hash = '#mail/' + r.id; return; }
      if (k === 'addr') { const v = document.querySelector('#main [data-ml-addr]').value; await api('api/admin/mail/settings', { address: v }); b.textContent = X.saved; M.ovAt = 0; return; }
      if (k === 'tab' || k === 'rtab') { M.tab = b.dataset.v; M.prev = null; repaint(); refreshPrev(true); return; }
      if (k === 'tool') { insert(b.dataset.v); return; }
      if (k === 'aud') { M.edit.audience[b.dataset.k] = b.dataset.v; save(); countAud(); repaint(); return; }
      if (k === 'act') { const a = ACT[b.dataset.v]; Object.assign(M.edit.audience, { joined: a.joined || 0, active: a.active || 0, inactive: a.inactive || 0 }); save(); countAud(); repaint(); return; }
      if (k === 'test') { await save(true); setMsg('…'); const r = await api('api/admin/mail/test', { content: M.edit.content, lang: M.tab }); setMsg(f(X.testOk, { e: r.to })); return; }
      if (k === 'now' || k === 'at') {
        let at;
        if (k === 'at') { const v = document.querySelector('#main [data-ml-at]').value; at = v ? Math.floor(new Date(v).getTime() / 1000) : 0; if (!at) return; }
        await save(true);
        const n = M.aud ? M.aud.count : 0;
        if (k === 'now' && !(await (window.SweepAsk ? SweepAsk(f(X.askSend, { n: M.edit.name || X.untitled, c: num(n) }), X.askSendS, X.askGo) : Promise.resolve(false)))) return;
        await api('api/admin/mail/campaigns/' + id + '/send', at ? { at } : {});
        M.editId = 0; M.edit = null; M.ov = null; await reload(id); return;
      }
      if (k === 'unsched') { await api('api/admin/mail/campaigns/' + id + '/unschedule', {}); M.editId = 0; await reload(id); return; }
      if (k === 'del') {
        if (!(await (window.SweepAsk ? SweepAsk(f(X.askDel, { n: (M.edit && M.edit.name) || X.untitled }), X.askDelS, X.askDelGo) : Promise.resolve(false)))) return;
        await api('api/admin/mail/campaigns/' + id, undefined, 'DELETE'); M.editId = 0; M.edit = null; M.ov = null; delete M.rep[id]; location.hash = '#mail'; return;
      }
      if (k === 'pause' || k === 'resume') { await api('api/admin/mail/campaigns/' + id + '/pause', { pause: k === 'pause' }); await reload(id); return; }
      if (k === 'dup') { const r = await api('api/admin/mail/campaigns/' + id + '/duplicate', { lang: LANG }); M.ov = null; location.hash = '#mail/' + r.id; return; }
    } catch (err) { setMsg(errText(err), true); if (k !== 'test' && typeof toast === 'function') toast(errText(err)); }
  });
  async function reload(id) { M.repAt[id] = 0; delete M.rep[id]; loadRep(id, true); repaint(); }

  // after each render of the page: the preview into its shadow root
  const mo = new MutationObserver(() => { if (here() && document.querySelector('#main [data-ml-prev]') && !document.querySelector('#main [data-ml-prev]').shadowRoot) { paintPrev(); if (!M.prev) refreshPrev(true); } });
  const main = document.getElementById('main'); if (main) mo.observe(main, { childList: true });

  // the page title in the trader's language (the app's own title list has no « Emails »); a campaign gets « ‹ Emails » as its way back
  window.SweepMail = { view: (arg) => {
    const X = x(), id = parseInt(arg, 10), t = document.getElementById('title');
    if (t) t.textContent = X.h; document.title = X.h + ' · Sweep';
    return id > 0 ? `<a class="nav-back" href="#mail" data-noi18n><span>${h(X.back)}</span></a>` + vCampaign(id) : vList();
  } };
})();
