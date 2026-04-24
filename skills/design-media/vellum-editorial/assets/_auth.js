(function() {
  var KEY = 'vellum_auth';
  var HASH = '90eb3833';
  function h(s) {
    for (var i = 0, v = 0x811c9dc5; i < s.length; i++)
      v = (v ^ s.charCodeAt(i)) * 0x01000193 >>> 0;
    return (v >>> 0).toString(16).slice(0, 8);
  }
  if (sessionStorage.getItem(KEY) === HASH) return;
  var overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:oklch(0.96 0.008 80);display:flex;align-items:center;justify-content:center;font-family:Inconsolata,monospace';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-label', 'Authentication required');
  overlay.innerHTML = '<div style="text-align:center"><h2 style="font-family:Bodoni Moda,serif;font-style:italic;color:oklch(0.22 0.04 270);margin-bottom:1rem">Authentication Required</h2><input id="pw" type="password" aria-label="Password" placeholder="Password" style="font-family:Inconsolata,monospace;padding:0.6rem 1rem;border:1px solid oklch(0.82 0.015 75);border-radius:6px;font-size:1rem;width:220px;text-align:center"><br><button id="go" style="margin-top:0.75rem;padding:0.5rem 1.5rem;font-family:Inconsolata,monospace;font-size:0.85rem;background:oklch(0.38 0.12 160);color:#fff;border:none;border-radius:6px;cursor:pointer">Enter</button><p id="err" style="color:oklch(0.50 0.16 25);font-size:0.8rem;margin-top:0.5rem;display:none">Incorrect password</p></div>';
  document.body.appendChild(overlay);
  function check() {
    if (h(document.getElementById('pw').value) === HASH) {
      sessionStorage.setItem(KEY, HASH);
      overlay.remove();
    } else {
      document.getElementById('err').style.display = 'block';
    }
  }
  document.getElementById('go').onclick = check;
  document.getElementById('pw').onkeydown = function(e) { if (e.key === 'Enter') check(); };
  document.getElementById('pw').focus();
})();
