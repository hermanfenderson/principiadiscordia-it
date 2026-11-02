// Sito statico dell'edizione italiana dei Principia Discordia (vedi docs/sito.md).
// Immagini e dati si producono prima con  npm run esporta  (strumenti/esporta_web.py).
import { defineConfig } from 'astro/config';

export default defineConfig({
  // indirizzo pubblico (dal 2 novembre 2026). Con un indirizzo *.workers.dev il sito non si fa indicizzare.
  site: process.env.SITO_URL || 'https://principiadiscordia.hermanfenderson.com',
  trailingSlash: 'always',
  // la compressione dell'HTML toglieva lo spazio tra il testo e un link a capo («licenzaCreative»)
  compressHTML: false,
  build: { format: 'directory' },
  devToolbar: { enabled: false },
});
