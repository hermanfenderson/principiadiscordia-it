// Dove comprare il libro. La piattaforma (KDP o StreetLib) non è ancora decisa:
// quando ci sono, basta mettere l'indirizzo in `href`. Senza `href` la voce compare come «in arrivo».
export interface Negozio { nome: string; formati: string; href?: string }

export const CARTACEO: Negozio[] = [
  { nome: 'Amazon', formati: 'cartaceo, brossura A5' },
  { nome: 'IBS', formati: 'cartaceo' },
  { nome: 'laFeltrinelli', formati: 'cartaceo' },
  { nome: 'Mondadori Store', formati: 'cartaceo' },
];

export const EBOOK: Negozio[] = [
  { nome: 'Amazon Kindle', formati: 'ebook' },
  { nome: 'Kobo', formati: 'ebook EPUB' },
  { nome: 'IBS e laFeltrinelli', formati: 'ebook EPUB' },
  { nome: 'Apple Books', formati: 'ebook EPUB' },
];
