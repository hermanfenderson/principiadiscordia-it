# Guida alla composizione delle tavole

Come si ricompone in italiano una pagina dell'edizione Loompanics. Vale per chiunque lavori alle tavole, umano o Claude.

## Principio

Si rifanno **le scritte, non le immagini**. Il testo inglese viene cancellato dalla scansione e ricomposto in italiano con un font il più vicino possibile all'originale, nella stessa posizione, con lo stesso corpo e la stessa interlinea. Disegni, collage, cornici, timbri decorativi senza testo e numeri di pagina 000NN restano intatti.

## File

- Ogni tavola è una cartella `tavole/pNNN/` (NNN = pagina del PDF, a tre cifre) con un solo file: `tavola.yaml`.
- `docs/mappa-pagine.md` dice quale file di `testo/it/` corrisponde a ogni pagina del PDF.
- `tavole/p048/tavola.yaml` è la tavola di riferimento: guardala prima di cominciare.

## Comandi

```
python3 strumenti/righe.py 48                 # righe OCR con coordinate, linea di base e passo
python3 strumenti/componi.py tavole/p048      # compone la tavola
python3 strumenti/componi.py tavole/p048 --prova   # evidenzia in rosso le zone cancellate
```

`componi.py` scrive la tavola in `build/tavole/pNNN.png` e un confronto affiancato (originale | tavola, a metà risoluzione) in `build/confronti/pNNN.png`. **Ogni tavola va guardata nel confronto prima di considerarla finita.**

Coordinate: pixel sulla scansione a 360 dpi (circa 1830 × 2960). La pagina di base pulita è in `build/base/NNN.png`.

## tavola.yaml

```yaml
pagina_pdf: 48
cancella:                 # rettangoli [x0, y0, x1, y1] riempiti di bianco
  - [200, 180, 1810, 1115]
testi:
  - font: IBMPlexMono-Medium.ttf
    corpo: 52             # dimensione in pixel
    interlinea: 60        # distanza tra le linee di base
    x: 227                # inizio della linea di base della prima riga
    y: 422
    colonne: 49           # a capo automatico a N caratteri (oppure `righe:` esplicite)
    testo: >-
      testo italiano...
linee:                    # rettangoli neri (filetti, sottolineature lunghe)
  - [225, 976, 986, 984]
```

Opzioni di un elemento di testo:

| chiave | effetto |
|---|---|
| `righe: [...]` | righe esplicite, al posto di `testo` + `colonne` |
| `allinea: centro` / `destra` | allora `x` è il centro / la fine della riga più lunga |
| `sottolineato: true` | con `distanza_sottolineatura`, `spessore_sottolineatura` |
| `grassetto: 1` o `2` | ispessisce il tratto (contorno in pixel) |
| `scala_x: 0.8` | stringe o allarga orizzontalmente |
| `rotazione: 90` | gradi in senso antiorario; `x, y` restano l'inizio della prima linea di base |
| `adatta: 1480` | riduce il corpo finché la riga più lunga entra in quei pixel |
| `effetto: timbro` | inchiostro irregolare da timbro di gomma |
| `peso: 300` | solo per i font variabili (Oswald, EB Garamond, Caveat) |
| `inchiostro: false` | niente ammorbidimento dei bordi |

## Font (in `strumenti/font/`, tutti a licenza libera)

| stile nell'originale | font | note |
|---|---|---|
| macchina da scrivere, passo 12 (≈30 px a carattere) | `IBMPlexMono-Medium.ttf`, corpo 52 | il caso più frequente |
| macchina da scrivere, passo 10 (≈36 px) | `IBMPlexMono-Medium.ttf`, corpo = passo / 0,6 | |
| macchina da scrivere stile Courier | `CourierPrime-Regular.ttf` / `-Bold` | Courier Prime ha passo = 0,6 × corpo |
| dattiloscritto corsivo | `CourierPrime-Italic.ttf` + `grassetto: 1` | |
| dattiloscritto consumato, sporco | `SpecialElite-Regular.ttf` | |
| scritta a mano, stampatello tecnico | `ArchitectsDaughter-Regular.ttf` (+ `grassetto`) | |
| scritta a mano con pennarello | `Kalam-Bold.ttf`, `PermanentMarker-Regular.ttf` | |
| scritta a mano corsiva | `Caveat-VF.ttf`, `Kalam-Regular.ttf`, `PatrickHand-Regular.ttf`, `GochiHand-Regular.ttf` | |
| timbro, lettere condensate | `Oswald-VF.ttf` + `effetto: timbro` | |
| titoli a stencil | `StardosStencil-Bold.ttf` | |
| titoli neri condensati | `Anton-Regular.ttf`, `BebasNeue-Regular.ttf` | |
| titoli con grazie pesanti | `AlfaSlabOne-Regular.ttf` | |
| gotico / blackletter | `UnifrakturMaguntia-Book.ttf` | |
| stile western / circo | `Rye-Regular.ttf` | |
| tipografia con grazie (moduli, ritagli, frontespizi) | `OldStandard-*.ttf`, `EBGaramond-VF.ttf` | |

Se nessuno va bene, si usa il più vicino e lo si segnala nelle note.

## Regole

1. **Testo italiano:** quello di `testo/it/` del file indicato nella mappa, parola per parola. Si correggono solo i refusi evidenti (lettere doppie, spazi mancanti), e vanno elencati nelle note.
2. **Tavole già tradotte da Herman Fenderson:** se la pagina del vecchio sito usava un'immagine di `storico/immagini-it/`, quella contiene la sua traduzione delle scritte: si usa quella formulazione.
3. **Scritte dentro le immagini mai tradotte:** si traducono, si compongono, e si elencano nelle note come *traduzione nuova da rivedere*.
4. **Cancellare senza danneggiare:** i rettangoli coprono solo testo. Se una scritta è intrecciata al disegno e un rettangolo lo rovinerebbe, si usano più rettangoli piccoli; se non basta, si lascia l'inglese e si segnala *da ritoccare a mano*.
5. **Stessa impaginazione:** stessi margini, corpo e interlinea dell'originale (`righe.py` dà base e passo). L'italiano è più lungo dell'inglese: prima si usa lo spazio libero, poi si stringe con `scala_x` (non sotto 0,85) o si riduce l'interlinea; non si cambia il corpo del dattiloscritto.
6. **Nomi propri, sigle e giochi di parole:** si seguono le scelte già fatte nella traduzione (POEE, Mal-2, Hung Mung, Facciagrigia, Chao/Cao come nel testo).
7. **Note del traduttore (NdT):** restano fuori dalle tavole; si elencano nelle note.
8. **Numeri di pagina 000NN:** non si toccano.

## Note per tavola

Chi compone una tavola aggiunge in testa a `tavola.yaml` un commento con:

- `# STATO: completa` oppure `# STATO: da ritoccare` (e perché);
- `# NUOVE TRADUZIONI:` testi tradotti ex novo, con l'inglese a fianco;
- `# DIFFERENZE:` testo presente nell'edizione Loompanics ma assente in `testo/it/`, o viceversa;
- `# REFUSI CORRETTI:` correzioni fatte al testo italiano;
- `# NdT ESCLUSE:` note del traduttore lasciate fuori.
