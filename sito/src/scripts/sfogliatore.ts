// Miglioramenti dello sfogliatore: tastiera, swipe, doppia pagina, precaricamento.
// Senza questo script la pagina funziona lo stesso (link «Precedente» / «Successiva»).

const radice = document.querySelector<HTMLElement>('.sfogliatore');

function campoAttivo(t: EventTarget | null): boolean {
  const el = t as HTMLElement | null;
  if (!el) return false;
  return el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName);
}

function leggi(chiave: string): string | null {
  try { return localStorage.getItem(chiave); } catch { return null; }
}
function scrivi(chiave: string, valore: string) {
  try { localStorage.setItem(chiave, valore); } catch { /* storage non disponibile: pazienza */ }
}

if (radice) {
  const d = radice.dataset;
  const largo = window.matchMedia('(min-width: 60rem)');
  const prec = radice.querySelector<HTMLAnchorElement>('a.prec');
  const succ = radice.querySelector<HTMLAnchorElement>('a.succ');

  const doppia = () => document.documentElement.classList.contains('doppia') && largo.matches;
  const destinazione = (verso: 'prec' | 'succ') =>
    doppia() ? (verso === 'prec' ? d.precDoppia : d.succDoppia) : (verso === 'prec' ? d.prec : d.succ);

  function aggiornaLink() {
    if (prec && destinazione('prec')) prec.href = destinazione('prec')!;
    if (succ && destinazione('succ')) succ.href = destinazione('succ')!;
  }

  // ---- doppia pagina
  const bottone = document.getElementById('doppia') as HTMLButtonElement | null;
  if (bottone) {
    bottone.hidden = false;
    const segna = () => bottone.setAttribute('aria-pressed', String(document.documentElement.classList.contains('doppia')));
    segna();
    bottone.addEventListener('click', () => {
      const attiva = document.documentElement.classList.toggle('doppia');
      scrivi('pd-doppia', attiva ? '1' : '0');
      segna();
      aggiornaLink();
    });
  }
  aggiornaLink();
  largo.addEventListener('change', aggiornaLink);

  // ---- tastiera: frecce, Pagina su/giù con modificatori esclusi, Inizio/Fine
  const vai = (href?: string) => { if (href) window.location.href = href; };
  document.addEventListener('keydown', (e) => {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || campoAttivo(e.target)) return;
    switch (e.key) {
      case 'ArrowLeft': vai(destinazione('prec')); break;
      case 'ArrowRight': vai(destinazione('succ')); break;
      case 'Home': vai(d.prima); break;
      case 'End': vai(d.ultima); break;
      case 'd': case 'D': if (bottone && largo.matches) bottone.click(); else return; break;
      default: return;
    }
    e.preventDefault();
  });

  // ---- swipe orizzontale (non quando la pagina è ingrandita con le dita)
  let x0 = 0, y0 = 0, t0 = 0, uno = false;
  const palco = radice.querySelector<HTMLElement>('.palco');
  palco?.addEventListener('touchstart', (e) => {
    uno = e.touches.length === 1;
    if (!uno) return;
    x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now();
  }, { passive: true });
  palco?.addEventListener('touchend', (e) => {
    if (!uno || (window.visualViewport && window.visualViewport.scale > 1.05)) return;
    const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    if (Math.abs(dx) > 60 && Math.abs(dx) > 2 * Math.abs(dy) && Date.now() - t0 < 800) {
      vai(destinazione(dx < 0 ? 'succ' : 'prec'));
    }
  }, { passive: true });

  // ---- precarica l'immagine della pagina successiva
  const precarica = () => {
    if (!d.succAvif) return;
    const img = new Image();
    img.sizes = d.sizes || '100vw';
    img.srcset = d.succAvif;
  };
  if ('requestIdleCallback' in window) (window as any).requestIdleCallback(precarica);
  else setTimeout(precarica, 800);
}
