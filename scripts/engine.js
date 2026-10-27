// Every frame is a pure function of t. Helpers for timing and easing.
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const S = (t, a, b) => clamp((t - a) / (b - a));          // 0..1 progress between a and b
const out3 = x => 1 - Math.pow(1 - x, 3);
const inout = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const back = x => { const c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
// a scene's visibility: in over 0.15s after a, out over 0.1s before b (a short dip, so cuts don't read as pauses)
const vis = (t, a, b, fin = .15, fout = .1) => (a <= 0 ? 1 : out3(S(t, a, a + fin))) * (1 - S(t, b - fout, b));
function words(el) {  // wrap headline words once so they can stagger in
  if (el.dataset.split) return; el.dataset.split = 1;
  const walk = n => { [...n.childNodes].forEach(c => {
    if (c.nodeType === 3) { const f = document.createDocumentFragment();
      c.textContent.split(/(\s+)/).forEach(p => { if (!p) return;
        if (/^\s+$/.test(p)) f.appendChild(document.createTextNode(p));
        else { const s = document.createElement('span'); s.className = 'w'; s.textContent = p; f.appendChild(s); } });
      c.replaceWith(f); } else walk(c); }); };
  walk(el);
}
function stagger(el, t, a, step = .045, dur = .32) {   // words rise in from time a
  $$('#' + el.id + ' .w').forEach((w, i) => { const p = out3(S(t, a + i * step, a + i * step + dur));
    w.style.opacity = p; w.style.transform = `translateY(${(1 - p) * 26}px)`; });
}
const imgReady = () => Promise.all($$('img').map(i => i.complete ? (i.decode ? i.decode().catch(() => {}) : 0) :
  new Promise(r => { i.onload = i.onerror = () => r(); })));
