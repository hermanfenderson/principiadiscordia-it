// Dove comprare il libro (distribuzione StreetLib): quando un negozio lo ha in vendita,
// basta mettere l'indirizzo in `href`. Senza `href` la voce compare come «in arrivo».
export interface Negozio { nome: string; formati: string; href?: string }

export const CARTACEO: Negozio[] = [
  { nome: 'Totem', formati: 'cartaceo, brossura A5', href: 'https://totembooks.io/products/9791224748458-principia-discordia' },
  { nome: 'Amazon', formati: 'cartaceo, brossura A5', href: 'https://www.amazon.it/dp/B0HR4N2ND9' },
  { nome: 'IBS', formati: 'cartaceo' },
  { nome: 'laFeltrinelli', formati: 'cartaceo' },
  { nome: 'Mondadori Store', formati: 'cartaceo' },
];

export const EBOOK: Negozio[] = [
  { nome: 'Amazon Kindle', formati: 'ebook', href: 'https://www.amazon.it/dp/B0HR4D38YY' },
  { nome: 'Kobo', formati: 'ebook EPUB' },
  { nome: 'IBS e laFeltrinelli', formati: 'ebook EPUB' },
  { nome: 'Apple Books', formati: 'ebook EPUB' },
];
