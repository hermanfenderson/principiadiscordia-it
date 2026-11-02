// Miglioramenti dello sfogliatore: tastiera, swipe, doppia pagina, originale a fronte,
// tutto schermo, precaricamento. Senza questo script la pagina funziona lo stesso
// (link «Precedente» / «Successiva», link «Vedi l'originale inglese»).
//
// Di norma si sfoglia caricando la pagina successiva (ogni pagina è un documento vero).
// Solo nel tutto schermo si sfoglia senza ricaricare, perché il browser uscirebbe dal tutto
// schermo: si sostituisce la pagina corrente, si aggiornano indirizzo e titolo e si annuncia
// la pagina nuova con l'area aria-live.

const h = document.documentElement;
const sfogliatore = document.getElementById('sfogliatore');
const largo = window.matchMedia('(min-width: 60rem)');

function leggi(area: Storage | undefined, chiave: string): string | null {
  try { return area ? area.getItem(chiave) : null; } catch { return null; }
}
function scrivi(area: Storage | undefined, chiave: string, valore: string) {
  try { area?.setItem(chiave, valore); } catch { /* storage non disponibile: pazienza */ }
}
const locale = (() => { try { return window.localStorage; } catch { return undefined; } })();
const sessione = (() => { try { return window.sessionStorage; } catch { return undefined; } })();

function campoAttivo(t: EventTarget | null): boolean {
  const el = t as HTMLElement | null;
  if (!el) return false;
  return el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName);
}

const corrente = () => sfogliatore?.querySelector<HTMLElement>('.pagina-corrente') ?? null;
const doppia = () => h.classList.contains('doppia') && largo.matches;
const aFronte = () => h.classList.contains('a-fronte');
const schermo = () => h.classList.contains('schermo');

/** Indirizzo con ?a-fronte se l'originale a fronte è acceso, così il link si può condividere. */
function conStato(href?: string): string | undefined {
  if (!href) return href;
  const u = new URL(href, location.href);
  if (aFronte()) u.searchParams.set('a-fronte', ''); else u.searchParams.delete('a-fronte');
  return u.pathname + u.search.replace('a-fronte=', 'a-fronte');
}

function destinazione(verso: 'prec' | 'succ'): string | undefined {
  const d = corrente()?.dataset;
  if (!d) return undefined;
  const fronteAttivo = aFronte() && d.originale === 'si';
  const s = doppia() && !fronteAttivo ? (verso === 'prec' ? d.precDoppia : d.succDoppia) : (verso === 'prec' ? d.prec : d.succ);
  return conStato(s);
}

/** Allinea link, pulsanti e indirizzo allo stato corrente. */
function sincronizza() {
  const c = corrente();
  if (!c) return;
  const prec = c.querySelector<HTMLAnchorElement>('a.prec');
  const succ = c.querySelector<HTMLAnchorElement>('a.succ');
  if (prec && destinazione('prec')) prec.href = destinazione('prec')!;
  if (succ && destinazione('succ')) succ.href = destinazione('succ')!;
  c.querySelector('[data-azione="doppia"]')?.setAttribute('aria-pressed', String(h.classList.contains('doppia')));
  c.querySelector('[data-azione="a-fronte"]')?.setAttribute('aria-pressed', String(aFronte() && c.dataset.originale === 'si'));
  const barra = sfogliatore?.querySelector<HTMLElement>('.barra-schermo');
  if (barra) {
    barra.hidden = !schermo();
    (barra.querySelector('[data-azione="prec"]') as HTMLButtonElement).disabled = !destinazione('prec');
    (barra.querySelector('[data-azione="succ"]') as HTMLButtonElement).disabled = !destinazione('succ');
  }
  // nel tutto schermo il foglio è più grande: sizes più larghi (e immagini a risoluzione più alta)
  const sizes = schermo() ? c.dataset.sizesSchermo : c.dataset.sizes;
  if (sizes) c.querySelectorAll<HTMLImageElement | HTMLSourceElement>('.palco img, .palco source').forEach((el) => {
    if (el.getAttribute('sizes') !== sizes) el.setAttribute('sizes', sizes);
  });
  const qui = conStato(location.pathname);
  if (qui && qui !== location.pathname + location.search) history.replaceState(history.state, '', qui);
}

// ---- tutto schermo

async function entraSchermo() {
  h.classList.add('schermo');
  scrivi(sessione, 'pd-schermo', '1');
  if (sfogliatore && document.fullscreenEnabled && !document.fullscreenElement) {
    try { await sfogliatore.requestFullscreen(); } catch { /* resta la vista a finestra piena */ }
  }
  sincronizza();
  (sfogliatore?.querySelector('[data-azione="succ"]:not(:disabled)') as HTMLElement | null)?.focus();
}
function esciSchermo() {
  h.classList.remove('schermo');
  scrivi(sessione, 'pd-schermo', '0');
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  sincronizza();
  (corrente()?.querySelector('[data-azione="schermo"]') as HTMLElement | null)?.focus();
}
document.addEventListener('fullscreenchange', () => {
  if (!document.fullscreenElement && schermo()) esciSchermo();
});

// ---- sfogliare

async function sostituisci(href: string, nuovaVoce = true): Promise<boolean> {
  try {
    const r = await fetch(href, { headers: { Accept: 'text/html' } });
    if (!r.ok) return false;
    const doc = new DOMParser().parseFromString(await r.text(), 'text/html');
    const nuova = doc.querySelector('.pagina-corrente');
    const vecchia = corrente();
    if (!nuova || !vecchia) return false;
    vecchia.replaceWith(document.importNode(nuova, true));
    document.title = doc.title;
    if (nuovaVoce) history.pushState({ pd: true }, '', href);
    const annuncio = document.getElementById('annuncio');
    if (annuncio) annuncio.textContent = corrente()?.dataset.titolo ?? '';
    sincronizza();
    precarica();
    return true;
  } catch {
    return false;
  }
}

async function vai(href?: string) {
  if (!href) return;
  if (schermo() && (await sostituisci(href))) return;
  window.location.href = href;
}
window.addEventListener('popstate', (e) => {
  // solo le voci create sfogliando nel tutto schermo (non, per esempio, il link «Salta al contenuto»)
  if (!e.state?.pd && !history.state?.pd) return;
  if (schermo()) sostituisci(location.pathname + location.search, false);
  else location.reload();
});

// ---- pulsanti (delega: la pagina corrente può essere sostituita)

document.addEventListener('click', (e) => {
  const b = (e.target as HTMLElement).closest<HTMLElement>('[data-azione]');
  if (!b) return;
  switch (b.dataset.azione) {
    case 'doppia': {
      const attiva = h.classList.toggle('doppia');
      scrivi(locale, 'pd-doppia', attiva ? '1' : '0');
      break;
    }
    case 'a-fronte': {
      if (b.getAttribute('aria-disabled') === 'true') return;
      const attiva = h.classList.toggle('a-fronte');
      scrivi(locale, 'pd-a-fronte', attiva ? '1' : '0');
      break;
    }
    case 'schermo': entraSchermo(); return;
    case 'esci-schermo': esciSchermo(); return;
    case 'prec': vai(destinazione('prec')); return;
    case 'succ': vai(destinazione('succ')); return;
    default: return;
  }
  sincronizza();
});

// ---- menu della pagina (<details>): si chiude con Esc, cliccando fuori o scegliendo «Tutto schermo»

const menu = () => corrente()?.querySelector<HTMLDetailsElement>('.menu-pagina') ?? null;
function chiudiMenu(fuoco = false) {
  const m = menu();
  if (!m?.open) return false;
  m.open = false;
  if (fuoco) m.querySelector('summary')?.focus();
  return true;
}
document.addEventListener('click', (e) => {
  const t = e.target as HTMLElement;
  if (!t.closest('.menu-pagina') || t.closest('[data-azione="schermo"]')) chiudiMenu();
});

// ---- tastiera


document.addEventListener('keydown', (e) => {
  if (!sfogliatore || e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || campoAttivo(e.target)) return;
  if (e.key === 'Escape' && chiudiMenu(true)) { e.preventDefault(); return; }
  const c = corrente();
  const premi = (azione: string) => (c?.querySelector(`[data-azione="${azione}"]`) as HTMLElement | null)?.click();
  switch (e.key) {
    case 'ArrowLeft': vai(destinazione('prec')); break;
    case 'ArrowRight': vai(destinazione('succ')); break;
    case 'Home': vai(conStato(c?.dataset.prima)); break;
    case 'End': vai(conStato(c?.dataset.ultima)); break;
    case 'd': case 'D': if (!largo.matches) return; premi('doppia'); break;
    case 'o': case 'O': premi('a-fronte'); break;
    case 'f': case 'F': if (schermo()) esciSchermo(); else entraSchermo(); break;
    case 'Escape': if (!schermo()) return; esciSchermo(); break;
    default: return;
  }
  e.preventDefault();
});

// ---- swipe orizzontale (non quando la pagina è ingrandita con le dita)

let x0 = 0, y0 = 0, t0 = 0, uno = false;
sfogliatore?.addEventListener('touchstart', (e) => {
  uno = e.touches.length === 1 && !!(e.target as HTMLElement).closest('.palco');
  if (!uno) return;
  x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now();
}, { passive: true });
sfogliatore?.addEventListener('touchend', (e) => {
  if (!uno || (window.visualViewport && window.visualViewport.scale > 1.05)) return;
  const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
  if (Math.abs(dx) > 60 && Math.abs(dx) > 2 * Math.abs(dy) && Date.now() - t0 < 800) {
    vai(destinazione(dx < 0 ? 'succ' : 'prec'));
  }
}, { passive: true });

// ---- precarica l'immagine della pagina successiva

function precarica() {
  const d = corrente()?.dataset;
  if (!d?.succAvif) return;
  const img = new Image();
  img.sizes = d.sizes || '100vw';
  img.srcset = d.succAvif;
}

if (sfogliatore) {
  largo.addEventListener('change', sincronizza);
  // ricaricando dentro il tutto schermo si resta nella vista a finestra piena:
  // il tutto schermo vero del browser richiede un gesto (pulsante o tasto F)
  sincronizza();
  if ('requestIdleCallback' in window) (window as any).requestIdleCallback(precarica);
  else setTimeout(precarica, 800);
}
