// Sweep — makeitsweep.com
(function(){
  // captures not uploaded yet: collapse their empty spaces
  var tidy = function(){
    document.querySelectorAll('.duo,.gwrapped,.cards3').forEach(function(g){ var sl = g.querySelectorAll('.slot'); var all = sl.length && [].every.call(sl, function(x){ return x.classList.contains('missing'); }); g.classList.toggle('empty-media', !!all); });
    document.querySelectorAll('.split').forEach(function(s){ var r = s.querySelector(':scope > .reveal'); if(!r) return; var sl = r.querySelectorAll('.slot'); var all = sl.length && [].every.call(sl, function(x){ return x.classList.contains('missing'); }); s.classList.toggle('nomedia', !!all); });
  };
  var tt; document.addEventListener('error', function(e){ if(e.target && e.target.tagName === 'IMG'){ clearTimeout(tt); tt = setTimeout(tidy, 30); } }, true);
  window.addEventListener('load', tidy);

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var nav = document.querySelector('.nav'), root = document.documentElement, lastY = window.scrollY, menuOpen = false;
  function onScroll(){
    var y = window.scrollY;
    if(nav){
      nav.classList.toggle('scrolled', y > 8);
      var hide = !menuOpen && y > 160 && y > lastY + 2;
      if(y < lastY - 6 || y < 160) hide = false;
      if(hide !== nav.classList.contains('hide') && (Math.abs(y - lastY) > 2)){ nav.classList.toggle('hide', hide); root.classList.toggle('nav-hidden', hide); }
    }
    lastY = y;
  }
  onScroll(); window.addEventListener('scroll', onScroll, {passive:true});

  // mobile menu
  var btn = document.querySelector('.menu-btn'), sheet = document.getElementById('sheet');
  function setMenu(open){ menuOpen = open; root.classList.toggle('menu-open', open); nav.classList.remove('hide'); root.classList.remove('nav-hidden'); sheet.setAttribute('data-open', open?'true':'false'); btn.setAttribute('aria-expanded', open?'true':'false'); document.body.style.overflow = open?'hidden':''; if(open) nav.classList.add('scrolled'); else onScroll(); }
  if(btn && sheet){
    btn.addEventListener('click', function(){ setMenu(sheet.getAttribute('data-open') !== 'true'); });
    // keep the menu in place while the next page loads: the page transition takes over (no flicker)
    sheet.addEventListener('click', function(e){ var a = e.target.closest('a'); if(a && a.getAttribute('href').charAt(0) === '#') setMenu(false); });
    window.addEventListener('pageshow', function(e){ if(e.persisted) setMenu(false); });
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape' && sheet.getAttribute('data-open') === 'true'){ setMenu(false); btn.focus(); } });
  }

  // pricing: monthly / yearly
  var bill = document.querySelectorAll('[data-bill]');
  if(bill.length){
    var bw = document.querySelector('.billing');
    var place = function(){ var a = bw.querySelector('[aria-pressed="true"]'); if(!a) return; bw.style.setProperty('--x', a.offsetLeft + 'px'); bw.style.setProperty('--w', a.offsetWidth + 'px'); };
    var setBill = function(k){
      bill.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.bill===k ? 'true' : 'false'); });
      place();
      document.querySelectorAll('.plan [data-m]').forEach(function(el){ el.textContent = el.getAttribute('data-'+k); if(el.classList.contains('num') && !reduce){ el.classList.remove('swap'); void el.offsetWidth; el.classList.add('swap'); } });
      // send the chosen plan and billing period to the app
      document.querySelectorAll('.plan a[data-plan]').forEach(function(a){ if(a.dataset.plan === 'free') return; a.href = a.href.replace(/interval=(month|year)/, 'interval=' + (k === 'm' ? 'month' : 'year')); });
    };
    bill.forEach(function(b){ b.addEventListener('click', function(){ setBill(b.dataset.bill); }); });
    place(); bw.classList.add('ready'); window.addEventListener('resize', place);
    if(document.fonts && document.fonts.ready) document.fonts.ready.then(place);
    // phones: plans deck opens on Pro, dots follow the swipe
    var deck = document.getElementById('plans'), pd = document.querySelectorAll('.plan-dots i');
    if(deck && window.matchMedia('(max-width: 860px)').matches){
      var cards = deck.querySelectorAll('.plan'), main = deck.querySelector('.plan.main');
      if(main) deck.scrollLeft = main.offsetLeft - (deck.clientWidth - main.offsetWidth) / 2;
      var updd = function(){ var c = deck.scrollLeft + deck.clientWidth/2, best = 0, bd = 1e9; cards.forEach(function(cd,i){ var d = Math.abs(cd.offsetLeft + cd.offsetWidth/2 - c); if(d < bd){ bd = d; best = i; } }); pd.forEach(function(d,i){ d.classList.toggle('on', i===best); }); };
      deck.addEventListener('scroll', function(){ requestAnimationFrame(updd); }, {passive:true}); updd();
    }
  }

  // product tour: full-screen window, video loaded only on open, opens from the button you pressed
  var tour = document.getElementById('tour');
  if(tour && tour.showModal){
    var tv = tour.querySelector('video'), lastBtn = null;
    var load = function(){
      if(tv.dataset.loaded) return;
      var sm = window.matchMedia('(max-width: 900px)').matches || (navigator.connection && navigator.connection.saveData);
      [['webm', sm ? tv.dataset.srcWebmSm : tv.dataset.srcWebm], ['mp4', sm ? tv.dataset.srcMp4Sm : tv.dataset.srcMp4]].forEach(function(s){
        if(!s[1]) return; var e = document.createElement('source'); e.src = s[1]; e.type = 'video/' + s[0]; tv.appendChild(e); });
      tv.preload = 'auto'; tv.load(); tv.dataset.loaded = '1';
    };
    var openTour = function(e){
      lastBtn = e && e.currentTarget;
      if(lastBtn){ var r = lastBtn.getBoundingClientRect(); tour.style.setProperty('--ox', (r.left + r.width/2) + 'px'); tour.style.setProperty('--oy', (r.top + r.height/2) + 'px'); }
      load(); tour.classList.remove('closing'); tour.showModal(); document.documentElement.classList.add('modal-open');
      var hv = document.querySelector('.hero-loop'); if(hv) hv.pause();
      var pr = tv.play(); if(pr && pr.catch) pr.catch(function(){ tv.controls = true; });
      if(window.sweepTrack) sweepTrack('tour_open');
    };
    var closeTour = function(){
      if(!tour.open || tour.classList.contains('closing')) return;
      tour.classList.add('closing'); tv.pause();
      setTimeout(function(){ tour.close(); tour.classList.remove('closing'); }, reduce ? 0 : 260);
    };
    document.querySelectorAll('[data-tour]').forEach(function(b){ b.addEventListener('click', openTour); });
    tour.addEventListener('click', function(e){ if(e.target === tour || e.target.closest('[data-close]')) closeTour(); });
    tour.addEventListener('cancel', function(e){ e.preventDefault(); closeTour(); });
    tour.addEventListener('close', function(){ tv.pause(); try{ tv.currentTime = 0; }catch(err){} document.documentElement.classList.remove('modal-open');
      var hv = document.querySelector('.hero-loop'); if(hv && hv.classList.contains('is-playing')){ var p2 = hv.play(); if(p2 && p2.catch) p2.catch(function(){}); }
      if(lastBtn) lastBtn.focus({preventScroll:true}); });
  } else { document.querySelectorAll('[data-tour]').forEach(function(b){ b.addEventListener('click', function(){ window.open('/video/tour.mp4', '_blank'); }); }); }

  // hero intro video: flattens and grows as the page scrolls (desktop)
  var reel = document.querySelector('.stage.has-reel .reel');
  if(reel && !reduce){
    var rt = false;
    var settle = function(){ var r = reel.getBoundingClientRect(), vh = window.innerHeight;
      var p = Math.min(1, Math.max(0, (vh - r.top) / (vh * 0.85) - 0.35));
      var mx = window.innerWidth < 861 ? 6 : 10; reel.style.setProperty('--rx', (mx * (1 - p)).toFixed(2) + 'deg'); reel.style.setProperty('--rs', (0.94 + 0.06 * p).toFixed(4));
      if(reel.dataset.ready) reel.style.transform = 'perspective(1800px) rotateX(' + (mx * (1 - p)).toFixed(2) + 'deg) scale(' + (0.94 + 0.06 * p).toFixed(4) + ')';
      rt = false; };
    reel.addEventListener('animationend', function(){ reel.dataset.ready = '1'; reel.style.animation = 'none'; settle(); }, {once:true});
    window.addEventListener('scroll', function(){ if(!rt){ rt = true; requestAnimationFrame(settle); } }, {passive:true}); settle();
  }

  // consent (Loi 25): the attribution cookie is written only after "Accept"
  var consentBox = document.getElementById('consent');
  if(consentBox){ var consentVal = null; try{ consentVal = localStorage.getItem('sweep-consent'); }catch(e){}
    var utmPending = false; try{ utmPending = !!sessionStorage.getItem('sweep_utm_pending'); }catch(e){}
    if(!consentVal && utmPending){ consentBox.hidden = false; requestAnimationFrame(function(){ consentBox.classList.add('in'); }); }
    consentBox.querySelectorAll('[data-consent]').forEach(function(b){ b.addEventListener('click', function(){ var v = b.getAttribute('data-consent');
      try{ localStorage.setItem('sweep-consent', v); }catch(e){} if(v === 'yes' && window.sweepWriteUTM) window.sweepWriteUTM();
      consentBox.classList.remove('in'); setTimeout(function(){ consentBox.hidden = true; }, 350); }); }); }

  // language suggestion (no automatic redirect): offered once, remembered
  var langSug = document.getElementById('langsug');
  if(langSug && !/bot|crawl|spider|slurp|lighthouse|preview/i.test(navigator.userAgent)){
    var langPage = document.documentElement.lang.slice(0,2), langWant = (navigator.language||'').slice(0,2).toLowerCase(), langSeen = null;
    try{ langSeen = localStorage.getItem('sweep-lang'); }catch(e){}
    var langAlt = document.querySelector('link[rel="alternate"][hreflang="' + langWant + '"]');
    if(!langSeen && langAlt && langWant !== langPage && ['en','fr','es'].indexOf(langWant) > -1){
      langSug.querySelectorAll('[data-l]').forEach(function(s){ s.hidden = s.getAttribute('data-l') !== langWant; });
      var langGo = document.getElementById('langsug-go'); langGo.textContent = {fr:'Voir en français →', es:'Ver en español →', en:'View in English →'}[langWant];
      langGo.href = langAlt.getAttribute('href').replace(/^https?:\/\/[^/]+/, '');
      langGo.addEventListener('click', function(){ try{ localStorage.setItem('sweep-lang', langWant); }catch(e){} });
      document.getElementById('langsug-x').addEventListener('click', function(){ try{ localStorage.setItem('sweep-lang', langPage); }catch(e){} langSug.classList.remove('in'); setTimeout(function(){ langSug.hidden = true; }, 350); });
      langSug.hidden = false; setTimeout(function(){ langSug.classList.add('in'); }, 900);
    }
  }

  // header dropdowns (Product, Resources)
  var dds = [].slice.call(document.querySelectorAll('.navdd'));
  var closeDD = function(except){ dds.forEach(function(d){ if(d !== except){ d.classList.remove('open'); d.querySelector('.ddbtn').setAttribute('aria-expanded','false'); } }); };
  dds.forEach(function(d){
    var b = d.querySelector('.ddbtn');
    b.addEventListener('click', function(e){ e.stopPropagation(); var o = !d.classList.contains('open'); closeDD(d); d.classList.toggle('open', o); b.setAttribute('aria-expanded', o ? 'true' : 'false'); if(o){ var f = d.querySelector('.ddmenu a'); if(f && e.detail === 0) f.focus(); } });
    d.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ closeDD(); b.focus(); } });
  });
  document.addEventListener('click', function(e){ if(!e.target.closest('.navdd')) closeDD(); });
  // picking a page in a dropdown: close it at once (no hover ghost while the next page loads)
  document.querySelectorAll('.ddmenu a').forEach(function(a){ a.addEventListener('click', function(){ var n = document.querySelector('.nav'); if(n) n.classList.add('dd-off'); closeDD(); if(document.activeElement) document.activeElement.blur(); }); });
  window.addEventListener('pageshow', function(){ var n = document.querySelector('.nav'); if(n) n.classList.remove('dd-off'); });
  document.addEventListener('mousemove', function once(e){ var n = document.querySelector('.nav'); if(n && n.classList.contains('dd-off') && !e.target.closest('.navdd')){ n.classList.remove('dd-off'); } }, {passive:true});

  // language dropdown
  var ls = document.querySelector('.langsel'), lb = ls && ls.querySelector('.langbtn');
  if(ls && lb){
    var setL = function(o){ ls.classList.toggle('open', o); lb.setAttribute('aria-expanded', o?'true':'false'); };
    lb.addEventListener('click', function(e){ e.stopPropagation(); var o = !ls.classList.contains('open'); setL(o); if(o){ var c = ls.querySelector('[aria-current="true"]') || ls.querySelector('a'); c && c.focus(); } });
    document.addEventListener('click', function(e){ if(!ls.contains(e.target)) setL(false); });
    ls.addEventListener('keydown', function(e){
      var items = [].slice.call(ls.querySelectorAll('.langmenu a')), i = items.indexOf(document.activeElement);
      if(e.key === 'Escape'){ setL(false); lb.focus(); }
      else if(e.key === 'ArrowDown'){ e.preventDefault(); if(!ls.classList.contains('open')) setL(true); (items[i+1]||items[0]).focus(); }
      else if(e.key === 'ArrowUp'){ e.preventDefault(); (items[i-1]||items[items.length-1]).focus(); }
    });
  }

  // language preference
  document.querySelectorAll('[data-setlang]').forEach(function(a){
    a.addEventListener('click', function(){ try{ localStorage.setItem('sweep-lang', a.getAttribute('data-setlang')); }catch(e){} });
  });

  // hero: the product frame flattens as you scroll (max 6deg)
  var frame = document.querySelector('.stage .frame');
  if(frame){
    if(reduce){ frame.style.setProperty('--tilt','0deg'); frame.style.transform='none'; }
    else {
      var ticking = false;
      var px = 0, py = 0;
      var upd = function(){ var p = Math.min(1, Math.max(0, window.scrollY / 420)); var tx = 6*(1-p) - py*2; var t = tx.toFixed(2)+'deg';
        frame.style.setProperty('--tilt', (6*(1-p)).toFixed(2)+'deg'); if(frame.dataset.ready) frame.style.transform='rotateX('+t+') rotateY('+(px*2.5).toFixed(2)+'deg)'; ticking=false; };
      if(window.matchMedia('(hover: hover) and (pointer: fine)').matches){
        var stage = document.querySelector('.stage');
        stage.addEventListener('pointermove', function(e){ var r = stage.getBoundingClientRect(); px = (e.clientX - r.left)/r.width - .5; py = (e.clientY - r.top)/r.height - .5; if(!ticking){ ticking=true; requestAnimationFrame(upd); } });
        stage.addEventListener('pointerleave', function(){ px = 0; py = 0; requestAnimationFrame(upd); });
      }
      frame.addEventListener('animationend', function(){ frame.dataset.ready='1'; frame.style.opacity=1; upd(); }, {once:true});
      window.addEventListener('scroll', function(){ if(!ticking){ ticking=true; requestAnimationFrame(upd); } }, {passive:true});
      upd();
    }
  }

  if(!('IntersectionObserver' in window)){ document.querySelectorAll('.reveal,.final .mark').forEach(function(el){ el.classList.add('in'); }); return; }

  // screenshots fade in when loaded
  document.querySelectorAll('.frame img, .phone img, .pillar .shot img').forEach(function(img){
    if(img.complete && img.naturalWidth) img.classList.add('ld');
    else { img.addEventListener('load', function(){ img.classList.add('ld'); }, {once:true}); img.addEventListener('error', function(){ img.classList.add('ld'); }, {once:true}); }
  });

  // reveal once
  document.documentElement.classList.add('io');
  var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } }); }, {rootMargin:'0px 0px -12% 0px'});
  document.querySelectorAll('.stagger').forEach(function(g){ [].forEach.call(g.children, function(ch,i){ ch.style.setProperty('--i', i); }); });
  document.querySelectorAll('.reveal,.final .mark,.stagger,.head').forEach(function(el){ io.observe(el); });
  // failsafe: anything already on screen at the end of the page (or skipped by a fast scroll) is revealed
  var sweepReveal = function(){ var vh = window.innerHeight, end = window.scrollY + vh >= document.documentElement.scrollHeight - 8;
    document.querySelectorAll('.reveal:not(.in),.stagger:not(.in),.head:not(.in),.final .mark:not(.in)').forEach(function(el){
      var r = el.getBoundingClientRect(); if(r.bottom < 0 || (r.top < vh * (end ? 1 : 0.88))){ el.classList.add('in'); io.unobserve(el); } }); };
  var srt = 0; window.addEventListener('scroll', function(){ clearTimeout(srt); srt = setTimeout(sweepReveal, 120); }, {passive:true});
  window.addEventListener('load', function(){ setTimeout(sweepReveal, 400); });

  // videos: load just before they scroll in, play only while visible, fade in once the first frame is ready
  var vids = document.querySelectorAll('video[data-auto]');
  if(vids.length && !reduce){
    vids.forEach(function(v){ v.addEventListener('playing', function(){ v.classList.add('is-playing'); }); });
    var startLoad = function(v){ v.preload = 'auto'; v.load(); };
    var whenIdle = function(fn){ var go = function(){ (window.requestIdleCallback || function(f){ setTimeout(f, 200); })(fn, {timeout:1500}); };
      if(document.readyState === 'complete') go(); else window.addEventListener('load', go, {once:true}); };
    var pre = new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting){ var v = e.target; pre.unobserve(v);
      if(v.classList.contains('hero-loop')) whenIdle(function(){ startLoad(v); }); else startLoad(v); } }); }, {rootMargin:'800px 0px'});
    var vio = new IntersectionObserver(function(es){ es.forEach(function(e){ var v = e.target;
      if(e.isIntersecting){ var go = function(){ var pr = v.play(); if(pr && pr.catch) pr.catch(function(){}); };
        if(v.readyState >= 3) go(); else v.addEventListener('canplay', go, {once:true}); }
      else { v.pause(); } }); }, {threshold:.35});
    vids.forEach(function(v){ pre.observe(v); vio.observe(v); });
  }

  // swipe rails: highlight the card in focus
  if(window.matchMedia('(max-width: 860px)').matches && !reduce){
    document.querySelectorAll('.phones.rail, .tour-steps').forEach(function(r){
      r.classList.add('live');
      var kids = [].slice.call(r.children);
      var rio = new IntersectionObserver(function(es){ es.forEach(function(e){ e.target.classList.toggle('act', e.intersectionRatio > .6); }); }, {root:r, threshold:[0,.6,1]});
      kids.forEach(function(k){ rio.observe(k); });
    });
  }

  // sticky call to action on phones: after the hero buttons scroll away, until the final call to action
  var dock = document.querySelector('.dock'), heroCta = document.querySelector('.hero .cta-row, .page-hero'), endZone = document.querySelector('.final, footer');
  if(dock && heroCta){
    var past = false, atEnd = false;
    var setDock = function(){ var on = past && !atEnd; dock.classList.toggle('on', on); dock.setAttribute('aria-hidden', on?'false':'true'); dock.querySelectorAll('a').forEach(function(a){ a.tabIndex = on?0:-1; }); };
    new IntersectionObserver(function(es){ es.forEach(function(e){ past = !e.isIntersecting && e.boundingClientRect.top < 0; setDock(); }); }).observe(heroCta);
    if(endZone) new IntersectionObserver(function(es){ es.forEach(function(e){ atEnd = e.isIntersecting || e.boundingClientRect.top < 0; setDock(); }); }).observe(endZone);
  }

  // swipe carousel dots (phones)
  var rail = document.querySelector('.tour-steps'), dots = document.querySelectorAll('.dots i');
  if(rail && dots.length){
    var upd = function(){ var w = rail.firstElementChild ? rail.firstElementChild.getBoundingClientRect().width + 12 : 1; var i = Math.round(rail.scrollLeft / w); dots.forEach(function(d,k){ d.classList.toggle('on', k===i); }); };
    rail.addEventListener('scroll', function(){ requestAnimationFrame(upd); }, {passive:true}); upd();
  }

  // hero phone drifts slightly as you scroll (desktop)
  var hp = document.querySelector('.stage .phone:not(.back)');
  if(hp && !reduce && window.matchMedia('(min-width: 861px)').matches){
    hp.addEventListener('animationend', function(){ hp.style.opacity = 1; hp.style.animation = 'none'; }, {once:true});
    window.addEventListener('scroll', function(){ var y = Math.min(window.scrollY, 700); hp.style.transform = 'translate3d(0,' + (-y*0.08).toFixed(1) + 'px,0)'; }, {passive:true});
  }

  // sticky product tour
  var steps = document.querySelectorAll('.tour-step'), imgs = document.querySelectorAll('.tour-media img');
  if(steps.length && imgs.length){
    var tio = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){
        var i = +e.target.dataset.i;
        steps.forEach(function(s,k){ s.classList.toggle('on', k===i); });
        e.target.parentElement.style.setProperty('--p', ((i+1)/steps.length).toFixed(3));
        imgs.forEach(function(m,k){ m.classList.toggle('on', k===i); });
      }});
    }, {rootMargin:'-45% 0px -45% 0px'});
    steps.forEach(function(s){ tio.observe(s); });
  }

  // count-up facts
  var nums = document.querySelectorAll('[data-count]');
  var cio = new IntersectionObserver(function(es){ es.forEach(function(e){
    if(!e.isIntersecting) return; cio.unobserve(e.target);
    var el = e.target, end = +el.dataset.count; if(reduce){ el.textContent = end; return; }
    var t0 = performance.now(), d = 1100;
    (function tick(t){ var p = Math.min(1,(t-t0)/d), k = 1-Math.pow(1-p,3); el.textContent = Math.round(end*k); if(p<1) requestAnimationFrame(tick); })(t0);
  }); }, {threshold:.6});
  nums.forEach(function(n){ cio.observe(n); });

  // sub navigation highlight
  var links = document.querySelectorAll('.subnav a');
  if(links.length){
    var map = {}; links.forEach(function(a){ map[a.getAttribute('href').slice(1)] = a; });
    var sio = new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting){ links.forEach(function(a){ a.classList.remove('on'); }); var a = map[e.target.id]; if(a){ a.classList.add('on'); var c=a.parentElement; c.scrollTo({left:a.offsetLeft-c.clientWidth/2+a.clientWidth/2,behavior:reduce?'auto':'smooth'}); } } }); }, {rootMargin:'-40% 0px -55% 0px'});
    Object.keys(map).forEach(function(id){ var s = document.getElementById(id); if(s) sio.observe(s); });
  }
})();
