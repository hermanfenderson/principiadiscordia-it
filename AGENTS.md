# Principia Discordia — edizione italiana

Traduzione italiana di Herman Fenderson (pseudonimo di Mauro Minenna) dei *Principia Discordia*, in facsimile dell'edizione Loompanics 1980: ogni pagina della scansione originale è ricomposta con le scritte in italiano, illustrazioni originali. Licenza della traduzione CC BY-SA 4.0. Leggi README.md per le decisioni editoriali.

Si lavora in italiano: messaggi di commit, commenti, documentazione.

## Struttura

- `tavole/<tavola>/tavola.yaml` — una tavola per pagina: zone da cancellare sulla scansione e testi da comporre. Regole in `docs/guida-tavole.md`. Nomi: `pNNN` = pagina NNN del PDF Loompanics; tavole nuove: `occhiello`, `frontespizio`, `colophon-1`, `pre-1..4` (prefazione alla prefazione), `ndt-1..3` (note del traduttore), `fine-herman`.
- `libro/ordine.yaml` — ordine delle pagine del libro (114, con le `bianca`); `libro/copertina.yaml` — testi e impaginazione della copertina; `libro/metadati.yaml`.
- `testo/accessibile/<tavola>.md` — alt, descrizione e testo di ogni pagina (per il sito e l'EPUB).
- `testo/it/` — testo italiano storico (vecchio sito) e `apparato/` (prefazione, note, bio, colophon: le tavole relative si generano da qui).
- `strumenti/` — gli script; `strumenti/font/` — i caratteri (tutti a licenza libera, licenze accanto).
- `storico/` — il vecchio sito (HTML e immagini italiane).
- `docs/` — guida delle tavole, mappa delle pagine, **`docs/sito.md` (progetto del sito)**.
- `sorgenti/loompanics.pdf` — la scansione (non in git: `sh sorgenti/scarica.sh`). `build/` — tutto ciò che si rigenera (non in git).

## Comandi

Requisiti: Python 3 con `pip install -r requirements.txt`, e `pdftoppm` (poppler: `brew install poppler`).

```sh
python3 strumenti/componi.py tavole/p032          # una tavola -> build/tavole/p032.png (+ build/confronti/)
python3 strumenti/copertina.py --pagine 114       # copertina stesa -> build/copertina/copertina-ocra.png (stampa) e -schermo.png (senza riquadro del codice a barre)
python3 strumenti/libro.py --ricomponi            # tutte le tavole + PDF di stampa A5 (build/libro/)
python3 strumenti/libro.py --anteprima --copertina  # + PDF leggero da sfogliare con copertina
python3 strumenti/verifica_accessibili.py         # controllo dei testi accessibili
python3 strumenti/epub.py                         # EPUB accessibile -> build/epub/ (prima: libro.py e copertina.py)
python3 strumenti/impagina.py testo/it/apparato/note-del-traduttore.md ndt   # rigenera le tavole dattiloscritte
python3 strumenti/pagina_herman.py                # rigenera la pagina "Chi (non) è Herman Fenderson"
python3 strumenti/pagine_apertura.py              # rigenera occhiello e frontespizio
```

## Regole

- Quando cambia il testo di una tavola, aggiorna anche `testo/accessibile/<tavola>.md` (e `testo/it/` se c'è lo stesso testo) e lancia `verifica_accessibili.py`.
- Il libro deve restare di un numero pari di pagine, con ogni pagina Loompanics sul suo lato originale (PDF dispari = destra).
- Non modificare `storico/` (è l'archivio del vecchio sito): il clone per il web si genera altrove.
- Grafie fissate: "Malaclypse", "Cao" (Chao), "Facciagrigia", "Guazza/Buglio"; i refusi voluti dell'originale restano (spiegati nelle note del traduttore).
