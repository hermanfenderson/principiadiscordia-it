#!/usr/bin/env python3
"""Impagina il libro: tutte le tavole, nell'ordine di libro/ordine.yaml, in un PDF A5.

Ogni tavola è stampata al 100% (360 dpi), centrata sulla pagina con il margine
interno (verso la rilegatura) più largo di quello esterno. Se il contenuto di una
tavola uscirebbe dai margini di sicurezza, la tavola viene ridotta quanto basta.
Le tavole non ancora composte diventano una pagina segnaposto.

Uso:
  python3 strumenti/libro.py                 # build/libro/principia-discordia-a5.pdf
  python3 strumenti/libro.py --ricomponi     # ricompone prima tutte le tavole
"""
import argparse
import subprocess
import sys
from pathlib import Path

import img2pdf
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

RADICE = Path(__file__).resolve().parent.parent
DPI = 360
MM = DPI / 25.4
PAGINA = (round(148 * MM), round(210 * MM))   # A5
INTERNO, ESTERNO, ALTO, BASSO = 10 * MM, 7 * MM, 7 * MM, 7 * MM  # margini di sicurezza


def contenuto(tavola: Image.Image):
    """Riquadro dell'inchiostro sulla tavola (ignora i granelli isolati)."""
    a = np.asarray(tavola.convert("L")) < 128
    righe = np.where(a.sum(1) > 2)[0]
    colonne = np.where(a.sum(0) > 2)[0]
    if not len(righe):
        return None
    return colonne[0], righe[0], colonne[-1], righe[-1]


def pagina(tavola: Image.Image | None, numero: int, nome: str) -> Image.Image:
    foglio = Image.new("L", PAGINA, 255)
    destra = numero % 2 == 1  # pagina dispari = a destra, rilegatura a sinistra
    area = (INTERNO if destra else ESTERNO, ALTO,
            PAGINA[0] - (ESTERNO if destra else INTERNO), PAGINA[1] - BASSO)
    if tavola is None:
        d = ImageDraw.Draw(foglio)
        f = ImageFont.truetype(str(RADICE / "strumenti/font/IBMPlexMono-Medium.ttf"), 60)
        d.text((PAGINA[0] / 2, PAGINA[1] / 2), f"[ {nome}: tavola in lavorazione ]", font=f, fill=120, anchor="mm")
        return foglio
    cx, cy = (area[0] + area[2]) / 2, (area[1] + area[3]) / 2
    scala = 1.0
    box = contenuto(tavola)
    if box:
        w, h = tavola.size
        # distanza del contenuto dal centro della tavola, in ogni direzione
        sx = min((cx - area[0]) / max(w / 2 - box[0], 1), (area[2] - cx) / max(box[2] - w / 2, 1))
        sy = min((cy - area[1]) / max(h / 2 - box[1], 1), (area[3] - cy) / max(box[3] - h / 2, 1))
        scala = min(1.0, sx, sy)
    if scala < 1.0:
        tavola = tavola.resize((round(tavola.width * scala), round(tavola.height * scala)), Image.LANCZOS)
    foglio.paste(tavola.convert("L"), (round(cx - tavola.width / 2), round(cy - tavola.height / 2)))
    return foglio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ricomponi", action="store_true")
    ap.add_argument("--anteprima", action="store_true", help="PDF leggero da sfogliare (150 dpi, JPEG)")
    args = ap.parse_args()
    ordine = yaml.safe_load((RADICE / "libro" / "ordine.yaml").read_text(encoding="utf-8"))["pagine"]
    uscita = RADICE / "build" / "libro"
    (uscita / "pagine").mkdir(parents=True, exist_ok=True)
    file_pagine, mancanti, ridotte = [], [], []
    for i, nome in enumerate(ordine, 1):
        png = RADICE / "build" / "tavole" / f"{nome}.png"
        cartella = RADICE / "tavole" / nome
        if (cartella / "tavola.yaml").exists() and (args.ricomponi or not png.exists()):
            subprocess.run([sys.executable, str(RADICE / "strumenti/componi.py"), str(cartella)],
                           check=True, capture_output=True)
        tavola = Image.open(png) if png.exists() else None
        if tavola is None:
            mancanti.append(nome)
        foglio = pagina(tavola, i, nome)
        if tavola is not None and contenuto(tavola) and foglio is not None:
            pass
        destinazione = uscita / "pagine" / f"{i:03d}-{nome}.png"
        foglio.save(destinazione, dpi=(DPI, DPI))
        file_pagine.append(str(destinazione))
    pdf = uscita / "principia-discordia-a5.pdf"
    pdf.write_bytes(img2pdf.convert(file_pagine, layout_fun=img2pdf.get_fixed_dpi_layout_fun((DPI, DPI))))
    if args.anteprima:
        leggere = []
        for f in file_pagine:
            j = Path(f).with_suffix(".jpg")
            im = Image.open(f)
            im.resize((im.width * 150 // DPI, im.height * 150 // DPI), Image.LANCZOS).save(j, quality=82, dpi=(150, 150))
            leggere.append(str(j))
        anteprima = uscita / "principia-discordia-a5-anteprima.pdf"
        anteprima.write_bytes(img2pdf.convert(leggere, layout_fun=img2pdf.get_fixed_dpi_layout_fun((150, 150))))
        print(anteprima)
    print(f"{pdf}: {len(file_pagine)} pagine")
    if mancanti:
        print("tavole in lavorazione:", " ".join(mancanti))


if __name__ == "__main__":
    main()
