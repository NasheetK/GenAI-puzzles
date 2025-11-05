
(function(){
  const stored = localStorage.getItem('pg_sound_enabled');
  let enabled = stored ? stored === 'true' : true;

  const urls = window.PG_SOUNDS || {};
  const A = {
    click: new Audio(urls.click),
    hover: new Audio(urls.hover),
    toggle: new Audio(urls.toggle),
    success: new Audio(urls.success),
    fail: new Audio(urls.fail),
    complete: new Audio(urls.complete),
  };
  Object.values(A).forEach(a => { a.volume = 0.55; a.preload = 'auto'; });

  function setEnabled(v){
    enabled = v;
    localStorage.setItem('pg_sound_enabled', v ? 'true' : 'false');
    const el = document.querySelector('.pg-sound-toggle');
    if(el){ el.setAttribute('data-state', v ? 'on' : 'off'); }
    try{ A.toggle.currentTime=0; if(v) A.toggle.play(); }catch(e){}
  }

  document.addEventListener('click', (e)=>{
    const t = e.target.closest('.pg-sound-toggle');
    if(!t) return;
    e.preventDefault();
    setEnabled(!enabled);
  });

  document.addEventListener('click', (e)=>{
    const t = e.target.closest('a.btn,button,input[type="submit"],input[type="button"]');
    if(!t || !enabled) return;
    try { A.click.currentTime=0; A.click.play(); } catch(err){}
  });

  let hoverCooldown = 0;
  document.addEventListener('mouseover', (e)=>{
    if(!(window.PG_THEME && PG_THEME.includes('fusion'))) return;
    const t = e.target.closest('a.btn, .btn, button');
    if(!t || !enabled) return;
    const now = performance.now();
    if(now - hoverCooldown < 250) return;
    hoverCooldown = now;
    try { A.hover.currentTime=0; A.hover.play(); } catch(err){}
  });

  window.playSuccess = ()=>{ if(!enabled) return; try{ A.success.currentTime=0; A.success.play(); }catch(e){} };
  window.playFail    = ()=>{ if(!enabled) return; try{ A.fail.currentTime=0; A.fail.play(); }catch(e){} };
  window.playComplete= ()=>{ if(!enabled) return; try{ A.complete.currentTime=0; A.complete.play(); }catch(e){} };

  window.setSoundEnabled = setEnabled;
  window.getSoundEnabled = () => enabled;
})();
