// Sito statico dell'edizione italiana dei Principia Discordia (vedi docs/sito.md).
// Immagini e dati si producono prima con  npm run esporta  (strumenti/esporta_web.py).
import { defineConfig } from 'astro/config';

export default defineConfig({
  // indirizzo pubblico: per ora il sottodominio workers.dev (il dominio vero arriverà più avanti)
  site: process.env.SITO_URL || 'https://principiadiscordia-it.mauro-be5.workers.dev',
  trailingSlash: 'always',
  // la compressione dell'HTML toglieva lo spazio tra il testo e un link a capo («licenzaCreative»)
  compressHTML: false,
  build: { format: 'directory' },
  devToolbar: { enabled: false },
});
