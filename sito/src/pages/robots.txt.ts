// robots.txt: sull'indirizzo provvisorio (workers.dev) niente scansione; sul dominio vero tutto, con la sitemap.
import type { APIRoute } from 'astro';
import { PROVVISORIO } from '../config/sito';

export const GET: APIRoute = ({ site }) => {
  const righe = PROVVISORIO(site)
    ? ['# Indirizzo provvisorio: il sito si indicizza solo sul suo dominio.', 'User-agent: *', 'Disallow: /']
    : ['User-agent: *', 'Allow: /', '', `Sitemap: ${new URL('/sitemap.xml', site)}`];
  return new Response(righe.join('\n') + '\n', { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
