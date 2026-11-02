# Il sito: principiadiscordia.hermanfenderson.com

Progetto del nuovo sito dell'edizione italiana. Da costruire in una sessione di Claude Code su questo repository. Decisioni prese con Mauro (Herman Fenderson) il 1°-2 novembre 2026.

## Obiettivi

1. **Sfogliatore** del libro, una tavola per pagina, bello e **accessibile** (WCAG 2.2 AA).
2. **Scarica**: PDF ed EPUB gratuiti (copyleft, CC BY-SA 4.0).
3. **Compra**: invito a comprare il cartaceo o l'ebook sulle principali piattaforme.
4. **Storico**: un clone statico del vecchio sito PHP (la traduzione storica), come omaggio.
5. **Originale a fronte**: con un interruttore, accanto alla pagina italiana la pagina originale inglese.

## Architettura

- **Sito statico** generato in fase di build, servito da un **Cloudflare Worker con Static Assets** (wrangler). Niente server, niente database.
- **Deploy** (deciso il 2 novembre 2026): Worker di nome **`principiadiscordia-it`** sull'account Cloudflare di Mauro, pubblicato per ora sul sottodominio `workers.dev`. Il collegamento a un dominio vero si fa più avanti, su sua indicazione: fino ad allora il vecchio sito su principiadiscordia.hermanfenderson.com resta com'è.
- **Autonomia**: Mauro preferisce non essere coinvolto a ogni passo. Si procede da soli, scegliendo in modo ragionevole e annotando le scelte; si chiede solo per ciò che non si può annullare o che tocca il dominio e il vecchio sito.
- **Niente bucket R2.** Le immagini stanno negli asset statici: 109 tavole in due o tre misure sono qualche centinaio di file, ben sotto i limiti (20.000 file per versione sul piano Free, **25 MiB per file**).
- Conseguenza del limite dei 25 MiB: il PDF da scaricare è la versione per lo schermo (circa 19 MB, 150 dpi, come `build/libro/principia-discordia-con-copertina.pdf`), **non** il PDF di stampa a 360 dpi (circa 68 MB). Anche l'EPUB deve stare sotto i 25 MiB. Se un giorno servissero file più grandi: GitHub Releases o, solo allora, R2.
- Generatore: **Astro** in output statico (deciso; è lo strumento che Mauro usa anche per gli altri suoi siti). Il sito vive in una cartella `sito/` di questo repository. Cloudflare non esegue PHP: tutto, compreso il clone del vecchio sito, è HTML statico (più JavaScript dove serve).
- Le immagini e i dati delle pagine si producono dal libro con uno script (da scrivere, es. `strumenti/esporta_web.py`), così quando cambia una tavola si rigenerano insieme libro e sito.

## Le fonti (già pronte nel repository)

- `libro/ordine.yaml`: l'ordine delle pagine del libro (114, con le pagine `bianca`). Le pagine bianche nello sfogliatore si saltano, ma il numero di pagina del libro e il lato (dispari = destra) servono per la vista a doppia pagina.
- `build/tavole/<tavola>.png`: le tavole composte, **senza i margini di stampa** (circa 1827 × 2962 px a 360 dpi, in scala di grigi). Si rigenerano con `python3 strumenti/libro.py --ricomponi` (vedi CLAUDE.md). Sono queste le immagini da pubblicare, centrate, senza margini interni.
- `testo/accessibile/<tavola>.md`: per ogni tavola (109 file):
  - intestazione YAML: `tavola`, `pagina_originale` (numerazione di Hill 000NN, solo dove esiste: p013 = "-00002", p014 = "-00001", p015 = "00000", p016…p090 = "00001"…"00075"), `alt` (una o due frasi);
  - `## Descrizione`: descrizione dell'immagine;
  - `## Testo`: il testo della pagina in ordine di lettura, in Markdown, con corsivi, titoli `###`, a capo forzati (due spazi) per i versi e le lingue marcate con `<span lang="en|la|grc|de|pl">`.
  - `python3 strumenti/verifica_accessibili.py` controlla che siano completi e coerenti con le tavole.
- `build/copertina/copertina-ocra.png`: la copertina stesa (quarta, dorso, prima) a 300 dpi; la prima si ritaglia per la home e per le anteprime social.
- `libro/metadati.yaml`, `libro/copertina.yaml`: titolo, sottotitolo, autori, testi della quarta (presentazione e bio, utili per la home).
- `storico/sito/html/*.html` (86 pagine del vecchio sito, già scaricate e convertite dal PHP) e `storico/immagini-it/` (le tavole italiane del vecchio sito), `storico/sito/bookstyle.css`.

## Aspetto

La grafica deve venire dal mondo dei *Principia*: un collage fotocopiato di dattiloscritti, timbri, ritagli, scritte a mano e disegni rubacchiati. Non un sito "editoriale" pulito e anonimo.

- **Colori**: l'ocra della copertina Loompanics (RGB 208,146,12) come colore di casa; carta (bianco caldo o crema) per le pagine; inchiostro quasi nero (20,18,16), come nel libro. Il nero sull'ocra contrasta circa 7:1; il bianco sull'ocra **non** basta per il testo.
- **Caratteri**, gli stessi del libro, tutti OFL e già in `strumenti/font/` (da servire in WOFF2, con `font-display: swap`):
  - **MysteryQuest**, il carattere a riccioli del titolo in copertina, per i titoli grandi;
  - **Jost**, il grottesco geometrico del frontespizio, per l'interfaccia (menu, pulsanti, didascalie);
  - un carattere da macchina da scrivere (**IBM Plex Mono** o **Courier Prime**, quelli delle pagine dattiloscritte) per i testi lunghi del sito e i numeri di pagina 000NN;
  - **Kalam**, la scrittura a mano delle didascalie (come sotto lo struzzo), per note e commenti a margine;
  - **Oswald** con l'effetto timbro, per etichette tipo «SCARICA GRATIS», «COMPRA», «ORIGINALE A FRONTE», nello stile di «NON È POSTA SPAZZATURA».
- **Elementi**: timbri leggermente storti, ritagli con il bordo irregolare, la numerazione 000NN, le illustrazioni del libro (disegni di Hill, pubblico dominio) come decorazioni: il Sacro Cao come logo e favicon, la mela con kallisti, lo struzzo per la pagina su Herman Fenderson. Qualche scherzo discordiano discreto, ad esempio un «fnord» che compare solo selezionando il testo, a patto che non dia fastidio agli screen reader.
- **Limiti**: storture, rotazioni e grana fotocopia sono **solo decorazione**: i testi da leggere restano dritti, con contrasto AA e dimensioni regolabili. Niente animazioni con `prefers-reduced-motion`. Le decorazioni hanno `alt=""` o `aria-hidden`. Lo sfogliatore resta sobrio: la pagina del libro è già abbastanza discordiana da sola.

## Sfogliatore

- **Ogni pagina ha il suo indirizzo** e funziona **anche senza JavaScript**: HTML statico con l'immagine e i link "precedente" / "successiva" / "indice". Il JavaScript migliora l'esperienza (precaricamento, transizioni, tastiera, swipe) senza essere necessario.
- **Indirizzi** stabili e citabili: per le pagine con numero originale il numero di Hill (es. `/libro/00017/`; per le negative `/libro/-00002/`); per le altre un nome parlante ricavato dalla tavola (es. `/libro/prefazione-1/`, `/libro/introduzione-2/`, `/libro/intervista-5/`, `/libro/note-1/`, `/libro/herman-fenderson/`). La tabella tavola → indirizzo va scritta una volta sola (es. `libro/pagine-web.yaml`) e non cambiata più.
- **Immagine**: `<img>` con `alt` dal file accessibile, `width`/`height` espliciti (niente salti di layout), `srcset` in due-tre larghezze (es. 800, 1400, 2200 px; WebP o AVIF più JPEG di riserva), caricamento pigro tranne la pagina corrente. Le tavole sono in scala di grigi: si comprimono molto. Link "apri a piena risoluzione" per chi ingrandisce.
- **Testo accessibile**: la sezione con descrizione e testo della pagina è nel DOM della pagina, collegata all'immagine con `aria-describedby`. Per la consultazione normale si vede solo la tavola; il blocco è nascosto alla vista ma non agli screen reader (classe tipo `visually-hidden`). Deciso: **solo per gli screen reader**, nessun pulsante per mostrarlo. Il Markdown si converte in HTML vero (titoli, paragrafi, `lang`).
- **Tastiera**: frecce sinistra/destra per sfogliare (senza intercettarle quando il fuoco è in un campo), `Home`/`End` per inizio e fine, focus sempre visibile, link "salta al contenuto". Se la navigazione avviene lato client, il titolo del documento si aggiorna e un'area `aria-live="polite"` annuncia "Pagina 00017".
- **Mobile**: una pagina alla volta, swipe, pinch-zoom non bloccato. **Desktop**: opzione doppia pagina (pari a sinistra, dispari a destra, come nel libro stampato).
- **Indice**: griglia di miniature con i titoli delle sezioni (dall'indice originale, pagina 00002, e dai titoli nei testi accessibili), navigabile da tastiera.
- **Dichiararlo**: va detto in modo visibile che lo sfogliatore è accessibile, perché chi usa uno screen reader lo sappia prima di rinunciare. Una riga breve nello sfogliatore e in home (es. «Ogni pagina ha descrizione e testo completo per chi usa uno screen reader») con link a una pagina **Accessibilità** (raggiungibile anche dal piè di pagina) che spiega cosa c'è: alt, descrizione, testo in ordine di lettura, navigazione da tastiera, EPUB accessibile, e un contatto per segnalare problemi.
- `prefers-reduced-motion`: niente animazioni di sfoglio. Contrasto AA in tutta l'interfaccia. `lang="it"` sul documento.

## Originale a fronte

Un interruttore nello sfogliatore («Originale a fronte») mostra accanto alla tavola italiana la pagina inglese corrispondente, come nelle edizioni con testo a fronte: originale a sinistra, traduzione a destra.

- **Quali pagine**: tutte quelle che vengono dall'edizione Loompanics (tavole `p005`…`p105`). Per le pagine nuove dell'edizione italiana (occhiello, frontespizio, colophon, prefazione alla prefazione, note del traduttore, Herman Fenderson) l'interruttore è disattivato, con un breve avviso («questa pagina non esiste nell'originale»).
- **Cosa si vede**: la pagina della scansione Loompanics (`sorgenti/loompanics.pdf`, pagina N per la tavola pNNN), esportata come le tavole italiane e con le stesse misure, così le due pagine stanno affiancate alla stessa scala. Su schermi stretti non c'è spazio per due pagine: l'interruttore scambia la tavola italiana con l'originale, con un'etichetta chiara («Originale inglese»).
- **Testo inglese**: per gli screen reader (e per chi vuole copiarlo) la pagina originale ha il suo testo inglese, marcato `lang="en"`, preso dalle **trascrizioni di Wikisource** della scansione (indice «Principia Discordia (Loompanics Unlimited edition).pdf», pagine `Page:Principia_Discordia_(Loompanics_Unlimited_edition).pdf/N`). Nel repository ci sono già, in wikitesto, le pagine 5, 7 e 93–101 (`testo/en/wikisource/`); le altre vanno scaricate (dal Mac: le API di Wikimedia limitano le richieste, quindi con calma e con un User-Agent che identifichi il progetto) e convertite in Markdown in `testo/en/pagine/<tavola>.md`, con nell'intestazione l'indirizzo della pagina Wikisource e la revisione. Dove Wikisource non ha la trascrizione, si mostra solo la scansione, con alt e descrizione brevi in italiano, e nessun testo inventato (`testo/en/ocr/` è solo un OCR di lavoro, non da pubblicare).
- **Citare e linkare la fonte**: sotto la pagina originale, una riga con il link alla pagina di Wikisource da cui viene il testo e al file della scansione su Wikimedia Commons; nella pagina dei crediti, la nota completa: scansione dell'edizione Loompanics 1980 su Wikimedia Commons (pubblico dominio), trascrizioni dei volontari di Wikisource (CC BY-SA 4.0), testo originale «(K) All Rites Reversed». È anche un omaggio al vecchio sito, che a ogni pagina aveva il bottone «In inglese!».
- **Interruttore accessibile**: un `<button aria-pressed>` con etichetta visibile, raggiungibile da tastiera (anche con una scorciatoia, es. `O`), che resta attivo mentre si sfoglia (stato in `localStorage` e nell'indirizzo, es. `?a-fronte`, così si può condividere il link). Senza JavaScript: un semplice link «Vedi l'originale» a una pagina statica con la scansione e il testo inglese. Quando è attivo, per gli screen reader la pagina originale viene prima, annunciata come «Originale inglese», poi la traduzione.

## Scarica e compra

- **Scarica**: PDF per lo schermo con copertina (< 25 MiB) ed EPUB. L'EPUB si genera con `python3 strumenti/epub.py` (→ `build/epub/principia-discordia.epub`, circa 24 MiB): impaginazione fissa, una tavola per pagina, con gli stessi alt e testi di `testo/accessibile/` collegati alle immagini, indice (con le voci dell'indice originale), lista delle pagine stampate, punti di riferimento e metadati di accessibilità. Passa EPUBCheck 5.3 e DAISY Ace senza errori. Sta appena sotto il limite dei 25 MiB per file: se cresce, lo script avvisa e si abbassa la qualità JPEG.
- **Compra**: cartaceo e Kindle su Amazon; ebook e cartaceo nelle librerie online italiane (IBS, Feltrinelli, Mondadori Store, Kobo…). La piattaforma (KDP o StreetLib) **non è ancora decisa**: i link sono segnaposto in un file di configurazione, facili da riempire dopo.
- Testo d'invito breve, nello spirito del libro: il libro è libero, ma comprarlo è un buon modo di disordinare. Licenza CC BY-SA 4.0 e "(K) All Rites Reversed — Ristampa quel che ti pare" ben visibili.

## Storico (clone del vecchio sito)

- Sotto `/storico/`: le 86 pagine del vecchio sito come HTML statico, con lo stesso aspetto (fondo ocra chiaro #f1e18d, `bookstyle.css`), i link interni riscritti da `N.php` agli indirizzi nuovi, e un piccolo avviso in alto che rimanda alla nuova edizione.
- **Risorse mancanti** nel repository, da scaricare dal vecchio sito, che è ancora online su principiadiscordia.hermanfenderson.com: `downbtn.jpg`, `images/book-eris.gif`, la cartella `images/` con le immagini inglesi originali usate da alcune pagine, la home `index.php`. Controllare ogni pagina dopo il port.
- **Vecchi indirizzi** (`/libro/N.php`, `/index.php`), in giro da anni: niente PHP, redirect 301 statici (file `_redirects` degli asset statici del Worker) verso le pagine corrispondenti del clone storico, cioè il contenuto che quei link indicavano.

## Da non dimenticare

- Metadati: titolo "Principia Discordia — Edizione italiana", descrizione, Open Graph con la prima di copertina, `lang="it"`.
- Nessun tracciamento invasivo; se servono statistiche, Cloudflare Web Analytics.
- Verifiche prima della pubblicazione: navigazione solo da tastiera, VoiceOver (macOS/iOS) e NVDA, Lighthouse/axe senza errori, pagina leggibile senza JavaScript, peso delle immagini.

## Scelte fatte durante la costruzione (novembre 2026)

Annotate man mano, come chiesto, al posto di chiedere a ogni passo.

- **Comandi**: `python3 strumenti/esporta_web.py` (immagini, dati, caratteri, logo; salta ciò che è già aggiornato), poi in `sito/`: `npm run dev`, `npm run build`, `npx wrangler deploy`. Gli script vogliono Python ≥ 3.10 (il `python3` di sistema del Mac è il 3.9): si usa `.venv/` con Python 3.13. Astro 7 vuole Node ≥ 22.23.4.
- **Indirizzo provvisorio**: https://principiadiscordia-it.mauro-be5.workers.dev (impostato come `site` in `sito/astro.config.mjs`; si cambia lì, o con la variabile `SITO_URL`, quando arriva il dominio).
- **Repository pubblico** citato nel piè di pagina di ogni pagina, in home, in «Scarica» (i sorgenti della CC BY-SA, e il PDF di stampa che non sta negli asset) e nei crediti.
- **Contatto** per le segnalazioni di accessibilità: le issue di GitHub, non un indirizzo personale (il traduttore è Herman Fenderson).
- **Indirizzi**: `libro/pagine-web.yaml`; `/libro/` è l'indice, «Sfoglia» porta a `/libro/occhiello/`. Titoli propri solo per occhiello, colophon e frontespizio; le altre pagine senza numero di Hill si chiamano «<parte>, pagina N di M».
- **Immagini**: larghezze 300 (miniature), 600, 1000, 1400 in AVIF e JPEG, più `-piena.jpg` (1827 px, la risoluzione delle tavole). Le AVIF si salvano in RGB: quelle monocromatiche (4:0:0) non si vedevano nel browser. Circa 110 kB per una pagina vista a schermo.
- **Navigazione**: niente router lato client; ogni pagina è un documento vero, con precaricamento della successiva e transizioni tra documenti (`@view-transition`) solo senza `prefers-reduced-motion`. Così lo screen reader annuncia il titolo nuovo da sé, e non serve un'area `aria-live`.
- **Doppia pagina**: la pagina compagna è nel codice HTML ma nascosta (si carica solo quando serve); in doppia pagina è un link alla sua pagina con il suo alt. Le pagine bianche lasciano uno spazio vuoto, così ogni pagina resta sul suo lato. Tasto `D`.
- **Caratteri**: WOFF2 ridotti all'alfabeto latino, tranne MysteryQuest e IBM Plex Mono, che hanno un «Reserved Font Name»: per la OFL un sottoinsieme sarebbe una versione modificata, quindi solo conversione di formato. Licenze servite accanto ai file in `/font/`.
- **Logo e favicon**: il Sacro Cao ritagliato dalla scansione (PDF 18), cerchio ricavato in automatico (`sacro_cao()` in `esporta_web.py`).
- **Timbri e storture**: i riquadri dei pulsanti-timbro sono storti, le scritte restano dritte; la copertina in home è appena ruotata. Il «fnord» del piè di pagina compare solo selezionando il testo ed è `aria-hidden`.
- **Compra**: i negozi sono in `sito/src/config/compra.ts`; senza `href` compaiono come «in arrivo», senza link finti.
- **Wikisource** (scaricato il 2 novembre 2026, 5 richieste da 20 pagine con 6 s di pausa): le pagine trascritte sono solo 14, tutte rilette (livello 3): p005, p007, p009–p011, p093–p101. La Quarta Edizione (p013–p092) e p102–p105 su Wikisource non hanno trascrizione: lì si vede solo la scansione, con un alt in italiano e il rimando a Wikisource per chi volesse trascriverle. I file `p102`–`p105.wiki` che c'erano nel repository erano pagine d'errore di Wikimedia salvate per sbaglio: tolti. Revisioni in `testo/en/wikisource/revisioni.yaml`; `strumenti/converti_wikisource.py` produce `testo/en/pagine/` (i `{{SIC}}` restano con la grafia originale; le note `<ref>` vanno in fondo alla pagina).
- **Originale a fronte**: largo, originale a sinistra e traduzione a destra (vince sulla doppia pagina); stretto, l'originale prende il posto della traduzione. Stato in `localStorage` e in `?a-fronte`, che i link «Precedente/Successiva» si portano dietro. Sulle pagine nuove dell'edizione italiana il pulsante è `aria-disabled` con l'avviso visibile. Senza JavaScript: link a `/libro/<pagina>/originale/`, pagina statica con scansione e testo inglese leggibile e copiabile.
- **Tutto schermo** (chiesto da Mauro il 2 novembre): pulsante «Tutto schermo» e tasto `F`; restano solo la pagina e, sotto, due frecce e «Esci». Il browser esce dal tutto schermo a ogni cambio di documento, quindi lì si sfoglia senza ricaricare (si sostituisce la pagina, si aggiornano indirizzo e titolo, `aria-live` annuncia la pagina). Dove l'API Fullscreen non c'è (Safari su iPhone) la stessa vista copre la finestra.
- **Spazi prima dei link**: `compressHTML: false` in `astro.config.mjs`; la compressione di Astro mangiava l'a capo tra il testo e un link sulla riga dopo.
- **Storico**: `strumenti/clona_storico.py` genera `sito/public/storico/` (home e `libro/<N>/`) e `sito/public/_redirects` (`/index.php` e `/libro/<N>.php` → clone, 301). Le 88 risorse che mancavano nel repository (`downbtn.jpg`, `overbtn.jpg` del CSS, `images/*.gif`) sono scaricate una volta dal vecchio sito (una richiesta alla volta, 1,5 s di pausa) in `sorgenti/vecchio-sito/`, **in git**, così il clone si rifà anche dopo la chiusura del vecchio sito. Ritocchi minimi alle pagine: `lang="it"`, «(vecchio sito)» nel titolo, link interni riscritti, e in cima una striscia che riporta alla nuova edizione e, dove le tavole dicono da quale vecchia pagina vengono, alla stessa pagina nello sfogliatore. Il bottone «In inglese!» porta ancora a principiadiscordia.com, com'era. La vecchia home rimandava subito a `libro/0.php`: nel clone è una paginetta con il link, senza refresh automatico.
- **Copertina e quarta nello sfogliatore** (chiesto da Mauro): `/libro/copertina/` è la prima pagina e `/libro/quarta/` l'ultima, da sole anche in doppia pagina (copertina a destra, quarta a sinistra). Immagini ritagliate dalla copertina stesa; testi accessibili da `libro/copertina.yaml` (come nell'EPUB). «Sfoglia» ora parte dalla copertina.
- **Riquadro del codice a barre**: `strumenti/copertina.py` produce anche `copertina-ocra-schermo.png`, tutta ocra, senza il riquadro bianco; la usano il sito, il PDF da sfogliare e l'EPUB. `copertina-ocra.png`, per la tipografia, tiene il riquadro dove KDP/StreetLib stampano l'ISBN.
- **Tutto schermo, seconda versione** (su indicazione di Mauro): foglio a tutta altezza, frecce piccole tonde ai lati (sul telefono in basso agli angoli), «Esci ✕» nell'angolo in alto. Nel tutto schermo lo script cambia `sizes` di immagini e sorgenti, così il foglio cresce davvero (con `srcset` la larghezza intrinseca è quella di `sizes`) e si carica la risoluzione più alta.
