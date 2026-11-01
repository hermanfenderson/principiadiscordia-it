# Principia Discordia — edizione italiana

Traduzione italiana dei *Principia Discordia* di Malaclypse il Giovane (Greg Hill) e Lord Omar Khayyam Ravenhurst (Kerry Thornley), tradotti da Herman Fenderson, apprendista patafisico.

La traduzione è nata anni fa sul sito [principiadiscordia.hermanfenderson.com](http://principiadiscordia.hermanfenderson.com). Questo repository la porta a un'edizione completa in **facsimile**: ogni pagina ricomposta in italiano come il collage originale, per la stampa, per l'ebook e per un nuovo sito.

## Decisioni prese

- **Firma della traduzione:** Herman Fenderson. Nel libro nessuno firma col proprio nome, e il traduttore non fa eccezione.
- **Formato:** facsimile. Ogni pagina dell'originale diventa una tavola ricomposta in italiano.
- **Edizione di riferimento:** Loompanics Unlimited (IV e V edizione riunite, 1980), dalla scansione su Wikisource/Wikimedia Commons.
- **Introduzione di Robert Anton Wilson:** inclusa.
- **Copertina:** frontespizio italiano su fondo ocra (il colore del vecchio sito), con il timbro "TRADOTTO DA HERMAN FENDERSON"; testi in `libro/copertina.yaml`, composizione con `strumenti/copertina.py`.
- **Tavole:** si ricostruiscono le scritte, non le immagini. Il testo inglese viene cancellato dalla scansione e ricomposto in italiano con font il più vicini possibile agli originali. Nessuna rigenerazione delle illustrazioni.

## Struttura

```
storico/            la traduzione com'era sul vecchio sito: non si modifica
  sito/html/        le 86 pagine HTML originali
  immagini-it/      le tavole già tradotte a mano a suo tempo
testo/it/           il testo italiano, una pagina per file (NN.md = pagina NN del vecchio sito)
docs/               note di lavoro, inventari, rapporti di confronto
sorgenti/           le scansioni dell'edizione Loompanics (il PDF non è nel repository)
strumenti/          script di conversione e composizione delle tavole
```

Arriveranno poi:

```
tavole/<nome>/      base pulita + descrizione dei testi italiani + resa finale
sito/               il nuovo sito
libro/              impaginazione per stampa ed ebook
```

## Come si lavora

- `testo/it/` è la fonte del testo: le correzioni si fanno lì, non in `storico/`.
- Per rigenerare `testo/it/` dal vecchio sito: `python3 strumenti/importa_sito.py`. Serve solo una volta: dopo il primo import il testo si corregge a mano.
- Per scaricare la scansione Loompanics: `sh sorgenti/scarica.sh`.

## Diritti e licenza

La traduzione italiana di Herman Fenderson è distribuita con licenza [Creative Commons Attribuzione – Condividi allo stesso modo 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.it) (testo completo in `LICENSE`). I font in `strumenti/font/` hanno le proprie licenze (SIL Open Font License e Apache), incluse accanto ai file.

Il testo originale porta la nota "Ⓚ All Rites Reversed – reprint what you like". L'edizione Loompanics è considerata di pubblico dominio negli Stati Uniti perché pubblicata senza nota di copyright e mai registrata.
