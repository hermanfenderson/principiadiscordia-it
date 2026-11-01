#!/usr/bin/env python3
"""Elenca le righe di testo di una pagina della scansione, con le coordinate.

Serve a preparare tavola.yaml: dice dove sta ogni riga inglese (da cancellare)
e dove cade la sua linea di base (dove comporre l'italiano).

Uso:  python3 strumenti/righe.py 48
Colonne: x0 y0 x1 y1 della riga, base stimata, passo per carattere, testo OCR.
Coordinate in pixel sulla scansione a 360 dpi.
"""
import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from componi import RADICE, pagina_base  # noqa: E402

DISCENDENTI = set("gjpqy,;")


def ocr(numero_pdf: int) -> Path:
    cartella = RADICE / "build" / "ocr"
    cartella.mkdir(parents=True, exist_ok=True)
    tsv = cartella / f"{numero_pdf:03d}.tsv"
    if not tsv.exists():
        immagine = cartella / f"{numero_pdf:03d}.png"
        pagina_base(numero_pdf).save(immagine)
        subprocess.run(["tesseract", str(immagine), str(tsv.with_suffix("")), "-l", "eng", "--psm", "3", "tsv"],
                       check=True, capture_output=True)
        immagine.unlink()
    return tsv


def righe(numero_pdf: int):
    gruppi = defaultdict(list)
    with open(ocr(numero_pdf), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["level"] != "5" or not r["text"].strip() or float(r["conf"]) < 10:
                continue
            chiave = (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))
            gruppi[chiave].append(r)
    out = []
    for parole in gruppi.values():
        x0 = min(int(p["left"]) for p in parole)
        y0 = min(int(p["top"]) for p in parole)
        x1 = max(int(p["left"]) + int(p["width"]) for p in parole)
        y1 = max(int(p["top"]) + int(p["height"]) for p in parole)
        testo = " ".join(p["text"] for p in parole)
        # base: il fondo delle parole senza discendenti
        senza = [int(p["top"]) + int(p["height"]) for p in parole if not (set(p["text"]) & DISCENDENTI)]
        base = max(senza) if senza else y1 - round((y1 - y0) * 0.2)
        passo = (x1 - x0) / max(len(testo), 1)
        out.append((y0, x0, y1, x1, base, passo, testo))
    return sorted(out)


def main():
    n = int(sys.argv[1])
    for y0, x0, y1, x1, base, passo, testo in righe(n):
        print(f"[{x0:4d},{y0:4d},{x1:4d},{y1:4d}] base {base:4d} passo {passo:4.1f} | {testo}")


if __name__ == "__main__":
    main()
