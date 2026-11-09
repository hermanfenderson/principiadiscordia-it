// Sitemap: solo le pagine che vogliamo indicizzate, con le immagini delle pagine del libro.
// Restano fuori (e hanno noindex, vedi docs/sito.md, «SEO»): il clone del vecchio sito in /storico/
// e le pagine dell'originale inglese senza trascrizione di Wikisource, che sono solo una scansione.
// <lastmod> viene dalla data dell'ultimo commit che ha toccato le fonti di ogni pagina.
import type { APIRoute } from 'astro';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import dati from '../data/pagine.json';

const xml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// la build si lancia da sito/: la radice del repository è un livello sopra
const RADICE = join(process.cwd(), '..');

// data (AAAA-MM-GG) dell'ultimo commit che tocca uno dei percorsi; undefined se git non c'è o non trova nulla
function ultimaModifica(...percorsi: string[]): string | undefined {
  try {
    const data = execFileSync('git', ['log', '-1', '--format=%cs', '--', ...percorsi],
      { cwd: RADICE, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    return /^\d{4}-\d{2}-\d{2}$/.test(data) ? data : undefined;
  } catch {
    return undefined;
  }
}

// le fonti di una tavola: la sua composizione e il testo accessibile (prima e quarta: la copertina)
const fontiTavola = (t: string) => t === 'copertina' || t === 'quarta'
  ? ['libro/copertina.yaml', `testo/accessibile/${t}.md`]
  : [`tavole/${t}`, `testo/accessibile/${t}.md`];

export const GET: APIRoute = ({ site }) => {
  const assoluto = (p: string) => new URL(p, site).href;
  const pagina = (nome: string) => `sito/src/pages/${nome}.astro`;
  const voci: { loc: string; lastmod?: string; immagini?: string[] }[] = [
    { loc: '/', lastmod: ultimaModifica(pagina('index'), 'libro/metadati.yaml', 'libro/copertina.yaml'), immagini: [dati.copertina.piena] },
    { loc: '/libro/', lastmod: ultimaModifica(pagina('libro/index'), 'libro/ordine.yaml', 'libro/pagine-web.yaml') },
    { loc: '/scarica/', lastmod: ultimaModifica(pagina('scarica')) },
    { loc: '/compra/', lastmod: ultimaModifica(pagina('compra'), 'sito/src/config') },
    { loc: '/crediti/', lastmod: ultimaModifica(pagina('crediti')) },
    { loc: '/accessibilita/', lastmod: ultimaModifica(pagina('accessibilita')) },
  ];
  for (const p of dati.pagine) {
    voci.push({ loc: `/libro/${p.slug}/`, lastmod: ultimaModifica(...fontiTavola(p.tavola)), immagini: [p.immagine.piena] });
    // l'originale entra solo se ha il testo inglese trascritto: senza, è una scansione e basta
    if (p.originale?.testo) {
      voci.push({
        loc: `/libro/${p.slug}/originale/`,
        lastmod: ultimaModifica(`testo/en/pagine/${p.tavola}.md`),
        immagini: [p.originale.immagine.piena],
      });
    }
  }

  const corpo = voci.map((v) => [
    '  <url>',
    `    <loc>${xml(assoluto(v.loc))}</loc>`,
    ...(v.lastmod ? [`    <lastmod>${v.lastmod}</lastmod>`] : []),
    ...(v.immagini ?? []).map((i) => `    <image:image><image:loc>${xml(assoluto(i))}</image:loc></image:image>`),
    '  </url>',
  ].join('\n')).join('\n');
  return new Response(
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
    corpo + '\n</urlset>\n',
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
  );
};
