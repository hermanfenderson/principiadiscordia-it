// Sitemap: tutte le pagine del sito, con le immagini delle pagine del libro, e il clone del vecchio sito.
import type { APIRoute } from 'astro';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import dati from '../data/pagine.json';

const xml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export const GET: APIRoute = ({ site }) => {
  const assoluto = (p: string) => new URL(p, site).href;
  const voci: { loc: string; immagini?: string[] }[] = [
    { loc: '/', immagini: [dati.copertina.piena] },
    { loc: '/libro/' },
    { loc: '/scarica/' },
    { loc: '/compra/' },
    { loc: '/crediti/' },
    { loc: '/accessibilita/' },
  ];
  for (const p of dati.pagine) {
    voci.push({ loc: `/libro/${p.slug}/`, immagini: [p.immagine.piena] });
    if (p.originale) voci.push({ loc: `/libro/${p.slug}/originale/`, immagini: [p.originale.immagine.piena] });
  }
  // il vecchio sito (generato da strumenti/clona_storico.py in public/storico/)
  try {
    const numeri = readdirSync(join(process.cwd(), 'public', 'storico', 'libro'), { withFileTypes: true })
      .filter((d) => d.isDirectory() && /^\d+$/.test(d.name)).map((d) => Number(d.name)).sort((a, b) => a - b);
    for (const n of numeri) voci.push({ loc: `/storico/libro/${n}/` });
  } catch { /* clone non ancora generato */ }

  const corpo = voci.map((v) => [
    '  <url>',
    `    <loc>${xml(assoluto(v.loc))}</loc>`,
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
