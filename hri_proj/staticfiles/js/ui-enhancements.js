(() => {
  const click = new Audio('/static/audio/click.mp3');
  const success = new Audio('/static/audio/success.mp3');
  const fail = new Audio('/static/audio/fail.mp3');
  document.addEventListener('click', (e) => {
    const el = e.target.closest('button, .btn, a[href], [data-snd="click"], input[type="submit"]');
    if (!el || el.dataset.snd === 'off') return;
    try { click.currentTime = 0; } catch {}
    click.play().catch(()=>{});
  });
  document.addEventListener('puzzle:match',   () => { try{success.currentTime=0}catch{} success.play().catch(()=>{}) });
  document.addEventListener('puzzle:nomatch', () => { try{fail.currentTime=0}catch{}    fail.play().catch(()=>{}) });
})();
