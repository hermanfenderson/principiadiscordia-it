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
# margini di sicurezza: interno 16 mm (StreetLib chiede almeno 0,63" sotto le 500 pagine;
# KDP 9,6 mm sotto le 150), esterno, alto e basso 7 mm (KDP: almeno 6,4 mm senza abbondanza)
INTERNO, ESTERNO, ALTO, BASSO = 16 * MM, 7 * MM, 7 * MM, 7 * MM


def contenuto(tavola: Image.Image):
    """Riquadro dell'inchiostro sulla tavola (ignora i granelli isolati)."""
    a = np.asarray(tavola.convert("L")) < 128
    righe = np.where(a.sum(1) > 2)[0]
    colonne = np.where(a.sum(0) > 2)[0]
    if not len(righe):
        return None
    return colonne[0], righe[0], colonne[-1], righe[-1]


RIDOTTE: list = []


def pagina(tavola: Image.Image | None, numero: int, nome: str) -> Image.Image:
    foglio = Image.new("L", PAGINA, 255)
    destra = numero % 2 == 1  # pagina dispari = a destra, rilegatura a sinistra
    area = (INTERNO if destra else ESTERNO, ALTO,
            PAGINA[0] - (ESTERNO if destra else INTERNO), PAGINA[1] - BASSO)
    if nome == "bianca":
        return foglio
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
    if scala < 0.995:
        RIDOTTE.append((nome, round(scala, 3)))
    if scala < 1.0:
        tavola = tavola.resize((round(tavola.width * scala), round(tavola.height * scala)), Image.LANCZOS)
    foglio.paste(tavola.convert("L"), (round(cx - tavola.width / 2), round(cy - tavola.height / 2)))
    return foglio


def anteprima_con_copertina(pagine: list[str], uscita: Path):
    """Sfogliabile con la prima di copertina in apertura e la quarta in chiusura."""
    cop = Image.open(RADICE / "build" / "copertina" / "copertina-ocra.png").convert("RGB")
    dpi = 300
    ab, pw, ph = round(0.125 * dpi), round(148 / 25.4 * dpi), round(210 / 25.4 * dpi)
    dorso = cop.width - 2 * ab - 2 * pw
    tmp = uscita / "pagine"
    cop.crop((ab + pw + dorso, ab, ab + 2 * pw + dorso, ab + ph)).save(tmp / "000-prima.jpg", quality=85, dpi=(dpi, dpi))
    cop.crop((ab, ab, ab + pw, ab + ph)).save(tmp / "999-quarta.jpg", quality=85, dpi=(dpi, dpi))
    Image.new("RGB", (pw, ph), (255, 255, 255)).save(tmp / "000-bianca.jpg", quality=85, dpi=(dpi, dpi))
    b = str(tmp / "000-bianca.jpg")
    seq = [str(tmp / "000-prima.jpg"), b] + pagine + ([b] if len(pagine) % 2 else []) + [b, str(tmp / "999-quarta.jpg")]
    a5 = (img2pdf.mm_to_pt(148), img2pdf.mm_to_pt(210))
    pdf = uscita / "principia-discordia-con-copertina.pdf"
    pdf.write_bytes(img2pdf.convert(seq, layout_fun=img2pdf.get_layout_fun(a5, fit=img2pdf.FitMode.into)))
    print(pdf, len(seq), "pagine")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ricomponi", action="store_true")
    ap.add_argument("--anteprima", action="store_true", help="PDF leggero da sfogliare (150 dpi, JPEG)")
    ap.add_argument("--copertina", action="store_true",
                    help="con --anteprima: aggiunge prima e quarta di copertina (da build/copertina/copertina-ocra.png)")
    args = ap.parse_args()
    ordine = yaml.safe_load((RADICE / "libro" / "ordine.yaml").read_text(encoding="utf-8"))["pagine"]
    uscita = RADICE / "build" / "libro"
    import shutil
    shutil.rmtree(uscita / "pagine", ignore_errors=True)  # niente pagine vecchie con numerazione diversa
    (uscita / "pagine").mkdir(parents=True, exist_ok=True)
    file_pagine, mancanti, ridotte = [], [], []
    for i, nome in enumerate(ordine, 1):
        png = RADICE / "build" / "tavole" / f"{nome}.png"
        cartella = RADICE / "tavole" / nome
        if (cartella / "tavola.yaml").exists() and (args.ricomponi or not png.exists()):
            subprocess.run([sys.executable, str(RADICE / "strumenti/componi.py"), str(cartella)],
                           check=True, capture_output=True)
        tavola = Image.open(png) if png.exists() and nome != "bianca" else None
        if tavola is None and nome != "bianca":
            mancanti.append(nome)
        foglio = pagina(tavola, i, nome)
        if tavola is not None and contenuto(tavola) and foglio is not None:
            pass
        destinazione = uscita / "pagine" / f"{i:03d}-{nome}.png"
        foglio.save(destinazione, dpi=(DPI, DPI))
        file_pagine.append(str(destinazione))
    if len(file_pagine) % 2:
        print("ATTENZIONE: numero di pagine dispari", len(file_pagine))
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
        if args.copertina:
            anteprima_con_copertina(leggere, uscita)
    print(f"{pdf}: {len(file_pagine)} pagine")
    if mancanti:
        print("tavole in lavorazione:", " ".join(mancanti))
    if RIDOTTE:
        print("tavole ridotte per stare nei margini di sicurezza:", RIDOTTE)


if __name__ == "__main__":
    main()
