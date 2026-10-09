// Sweep site: mobile menu + language preference
(function(){
  var btn=document.querySelector('.menu-btn'),sheet=document.getElementById('sheet');
  if(btn&&sheet){
    btn.addEventListener('click',function(){var o=sheet.getAttribute('data-open')==='true';sheet.setAttribute('data-open',o?'false':'true');btn.setAttribute('aria-expanded',o?'false':'true');document.body.style.overflow=o?'':'hidden';});
    sheet.addEventListener('click',function(e){if(e.target.tagName==='A'){sheet.setAttribute('data-open','false');btn.setAttribute('aria-expanded','false');document.body.style.overflow='';}});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&sheet.getAttribute('data-open')==='true'){sheet.setAttribute('data-open','false');btn.setAttribute('aria-expanded','false');document.body.style.overflow='';btn.focus();}});
  }
  document.querySelectorAll('[data-setlang]').forEach(function(a){a.addEventListener('click',function(){try{localStorage.setItem('sweep-lang',a.getAttribute('data-setlang'));}catch(e){}});});
})();
