#!/usr/bin/env python3
"""Impagina un testo nuovo come pagine dattiloscritte, nello stile delle tavole.

Legge un file di testo/it/apparato/, divide il testo in pagine di macchina da
scrivere e scrive una tavola.yaml per pagina (tavole/<prefisso>-1, -2, ...).

Uso:
  python3 strumenti/impagina.py testo/it/apparato/prefazione-alla-prefazione.md pre \\
      --firma "Herman Fenderson"

Il titolo è la prima riga; le ultime due righe, se c'è --firma, diventano la firma
a mano e la data dattiloscritta.
"""
import argparse
import re
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent

# misure della macchina da scrivere delle tavole (passo 12, 6 righe per pollice a 360 dpi)
FONT = "IBMPlexMono-Medium.ttf"
CORPO = 52
INTERLINEA = 60
COLONNE = 50
X = 227
PRIMA_RIGA = 420          # linea di base della prima riga di testo, pagina 1 (sotto il titolo)
PRIMA_RIGA_SEGUENTI = 330  # pagine successive (sotto il numero di pagina)
ULTIMA_RIGA = 2700        # oltre non si scrive
RIENTRO = "     "          # rientro di capoverso, cinque battute come negli originali


def dattilo(t: str) -> str:
    """Il testo come lo batterebbe una macchina da scrivere del 1970."""
    sost = {"’": "'", "‘": "'", "“": '"', "”": '"', "«": '"', "»": '"', "—": "--", "–": "-",
            "…": "...", "Ⓚ": "(K)"}
    for a, b in sost.items():
        t = t.replace(a, b)
    return t


def a_capo(testo: str, colonne: int) -> list[str]:
    righe, riga = [], ""
    for parola in testo.split():
        prova = f"{riga} {parola}" if riga else parola
        if len(prova) <= colonne:
            riga = prova
        else:
            righe.append(riga)
            riga = parola
    if riga:
        righe.append(riga)
    return righe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sorgente", type=Path)
    ap.add_argument("prefisso")
    ap.add_argument("--firma", help="nome della firma a mano (penultima riga del testo)")
    args = ap.parse_args()

    testo = args.sorgente.read_text(encoding="utf-8")
    testo = re.sub(r"^---\n.*?\n---\n", "", testo, flags=re.S)
    paragrafi = [dattilo(p.strip()) for p in re.split(r"\n\s*\n", testo) if p.strip()]
    titolo = paragrafi.pop(0)
    firma = data = None
    if args.firma:
        ultimo = paragrafi.pop().split("\n")
        firma, data = ultimo[0].strip(), [r.strip() for r in ultimo[1:] if r.strip()]

    # righe con il loro tipo: testo o vuota
    righe = []
    for par in paragrafi:
        par = " ".join(par.split("\n"))
        segnaposto = "\x01" * len(RIENTRO)  # il rientro non deve contare come spazio
        for r in a_capo(segnaposto + par, COLONNE):
            righe.append(r.replace("\x01", " "))
        righe.append("")
    while righe and righe[-1] == "":
        righe.pop()

    # distribuisce le righe sulle pagine
    pagine, corrente, y0 = [], [], PRIMA_RIGA
    capienza = lambda y: (ULTIMA_RIGA - y) // INTERLINEA + 1
    for r in righe:
        if len(corrente) >= capienza(y0):
            while corrente and corrente[-1] == "":
                corrente.pop()
            pagine.append(corrente)
            corrente, y0 = [], PRIMA_RIGA_SEGUENTI
            if r == "":
                continue
        corrente.append(r)
    pagine.append(corrente)

    # la firma deve stare sull'ultima pagina: altrimenti una pagina in più
    spazio_firma = 6 * INTERLINEA
    ultima_y = (PRIMA_RIGA if len(pagine) == 1 else PRIMA_RIGA_SEGUENTI) + (len(pagine[-1]) - 1) * INTERLINEA
    if firma and ultima_y + spazio_firma > ULTIMA_RIGA + 120:
        pagine.append([])

    for n, contenuto in enumerate(pagine, 1):
        cartella = RADICE / "tavole" / f"{args.prefisso}-{n}"
        cartella.mkdir(parents=True, exist_ok=True)
        testi = []
        if n == 1:
            testi.append({"font": FONT, "corpo": CORPO, "x": 913, "y": 260, "allinea": "centro",
                          "righe": [titolo], "sottolineato": True,
                          "distanza_sottolineatura": 9, "spessore_sottolineatura": 6})
            y = PRIMA_RIGA
        else:
            testi.append({"font": FONT, "corpo": CORPO, "x": 913, "y": 200, "allinea": "centro",
                          "righe": [f"-{n}-"]})
            y = PRIMA_RIGA_SEGUENTI
        if contenuto:
            testi.append({"font": FONT, "corpo": CORPO, "interlinea": INTERLINEA, "x": X, "y": y,
                          "righe": contenuto})
        if n == len(pagine) and firma:
            yf = y + max(len(contenuto), 0) * INTERLINEA + 110
            testi.append({"font": "Kalam-Bold.ttf", "corpo": 92, "x": 1700, "y": yf, "rotazione": 4,
                          "allinea": "destra", "righe": [firma]})
            if data:
                testi.append({"font": FONT, "corpo": CORPO, "interlinea": INTERLINEA, "x": 1797, "y": yf + 120,
                              "allinea": "destra", "righe": data})
        spec = {"pagina_pdf": None, "testi": testi}
        intestazione = (f"# Tavola nuova: {titolo.title()}, pagina {n} di {len(pagine)}\n"
                        f"# Generata da strumenti/impagina.py a partire da {args.sorgente.resolve().relative_to(RADICE)}:\n"
                        f"# per cambiare il testo si corregge la sorgente e si rilancia.\n"
                        f"# STATO: completa\n\n")
        (cartella / "tavola.yaml").write_text(
            intestazione + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
        print(cartella.relative_to(RADICE), f"{len(contenuto)} righe")


if __name__ == "__main__":
    main()
