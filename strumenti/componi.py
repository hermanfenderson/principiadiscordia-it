#!/usr/bin/env python3
"""Compone una tavola italiana a partire dalla scansione Loompanics.

Ogni tavola vive in tavole/<numero>/tavola.yaml e descrive:
  - quale pagina del PDF usare come base,
  - quali zone cancellare (il testo inglese),
  - quali testi italiani comporre, dove e con quale font.

Uso:
  python3 strumenti/componi.py tavole/00033          # una tavola
  python3 strumenti/componi.py tavole/*              # tutte
  python3 strumenti/componi.py tavole/00033 --prova  # sovrappone in rosso le zone cancellate

Il risultato va in build/tavole/<numero>.png (360 dpi, scala di grigi).
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RADICE = Path(__file__).resolve().parent.parent
PDF = RADICE / "sorgenti" / "loompanics.pdf"
FONT = RADICE / "strumenti" / "font"
USCITA = RADICE / "build" / "tavole"
DPI = 360


# ---------------------------------------------------------------- base

def pagina_base(numero_pdf: int) -> Image.Image:
    """Estrae la pagina dal PDF e la porta a inchiostro nero su carta bianca."""
    cache = RADICE / "build" / "base" / f"{numero_pdf:03d}.png"
    if cache.exists():
        return Image.open(cache).convert("L")
    img = livelli(scansione(numero_pdf))
    cache.parent.mkdir(parents=True, exist_ok=True)
    img.save(cache)
    return img


def scansione(numero_pdf: int) -> Image.Image:
    """La pagina del PDF così com'è, in scala di grigi a 360 dpi."""
    if not PDF.exists():
        sys.exit("Manca sorgenti/loompanics.pdf: lancia prima  sh sorgenti/scarica.sh")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pdftoppm", "-r", str(DPI), "-gray", "-png",
             "-f", str(numero_pdf), "-l", str(numero_pdf), str(PDF), f"{tmp}/p"],
            check=True,
        )
        img = Image.open(next(Path(tmp).glob("p-*.png"))).convert("L")
        img.load()
    return img


def livelli(img: Image.Image, nero: int = 70, bianco: int = 165) -> Image.Image:
    """Toglie il grigio della carta ingiallita conservando i bordi morbidi dell'inchiostro."""
    a = np.asarray(img, dtype=np.float32)
    a = np.clip((a - nero) / (bianco - nero), 0, 1) * 255
    return Image.fromarray(a.astype(np.uint8), "L")


# ---------------------------------------------------------------- testo

def carica_font(nome: str, corpo: float, peso: int | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT / nome), size=round(corpo))
    if peso is not None:  # solo per i font variabili (es. Oswald)
        font.set_variation_by_axes([peso])
    return font


def a_capo(testo: str, colonne: int) -> list[str]:
    """Va a capo come una macchina da scrivere: al massimo `colonne` caratteri per riga."""
    righe = []
    for paragrafo in testo.split("\n"):
        riga = ""
        for parola in paragrafo.split():
            prova = f"{riga} {parola}" if riga else parola
            if len(prova) <= colonne:
                riga = prova
            else:
                righe.append(riga)
                riga = parola
        righe.append(riga)
    return righe


def strato_testo(el: dict, dimensioni):
    """Disegna un elemento di testo su uno strato trasparente (bianco = vuoto)."""
    font = carica_font(el["font"], el["corpo"], el.get("peso"))
    righe = el["righe"] if "righe" in el else a_capo(el["testo"], el.get("colonne", 999))
    interlinea = el.get("interlinea", el["corpo"] * 1.2)

    # adatta: riduce il corpo finché la riga più lunga entra nella larghezza data
    if "adatta" in el:
        corpo = el["corpo"]
        while corpo > 8 and max(font.getlength(r) for r in righe) > el["adatta"]:
            corpo -= 1
            font = carica_font(el["font"], corpo, el.get("peso"))
        interlinea = interlinea * corpo / el["corpo"]

    massima = max(font.getlength(r) for r in righe)
    larghezza = int(massima) + 40
    altezza = int(interlinea * (len(righe) - 1) + el["corpo"] * 1.6) + 40
    strato = Image.new("L", (larghezza, altezza), 255)
    d = ImageDraw.Draw(strato)
    sx = el.get("scala_x", 1.0)
    allinea = el.get("allinea", "sinistra")
    for i, riga in enumerate(righe):
        y = 20 + el["corpo"] + i * interlinea
        lunghezza = font.getlength(riga)
        x = 20 + {"sinistra": 0, "centro": (massima - lunghezza) / 2, "destra": massima - lunghezza}[allinea]
        d.text((x, y), riga, font=font, fill=0, anchor="ls",
               stroke_width=el.get("grassetto", 0), stroke_fill=0)
        if el.get("sottolineato"):
            spessore = el.get("spessore_sottolineatura", 8)
            yy = y + el.get("distanza_sottolineatura", 12)
            d.rectangle([x, yy, x + lunghezza, yy + spessore], fill=0)
    # punto di aggancio: inizio della linea di base della prima riga
    # (con allinea centro/destra: il centro / la fine della riga più lunga)
    ancora_x = 20 + {"sinistra": 0, "centro": massima / 2, "destra": massima}[allinea]
    ancora = (ancora_x * sx, 20 + el["corpo"])
    if sx != 1.0:
        strato = strato.resize((int(strato.width * sx), strato.height), Image.LANCZOS)
    if el.get("effetto") == "timbro":
        strato = timbro(strato)
    elif el.get("inchiostro", True):
        strato = inchiostro(strato)
    if el.get("rotazione"):
        import math
        w, h = strato.size
        strato = strato.rotate(el["rotazione"], expand=True, fillcolor=255, resample=Image.BICUBIC)
        # dove finisce il punto di aggancio dopo la rotazione attorno al centro
        a = math.radians(el["rotazione"])
        cx, cy = w / 2, h / 2
        dx, dy = ancora[0] - cx, ancora[1] - cy
        rx = dx * math.cos(a) + dy * math.sin(a)
        ry = -dx * math.sin(a) + dy * math.cos(a)
        ancora = (rx + strato.width / 2, ry + strato.height / 2)
    return strato, ancora


def inchiostro(strato: Image.Image) -> Image.Image:
    """Ammorbidisce appena i bordi: il digitale troppo netto stona accanto alla scansione."""
    return strato.filter(ImageFilter.GaussianBlur(0.9))


def timbro(strato: Image.Image, seme: int = 5) -> Image.Image:
    """Inchiostro irregolare da timbro di gomma: buchi, bordi sgranati."""
    rng = np.random.default_rng(seme)
    a = np.asarray(strato, dtype=np.float32) / 255
    rumore = rng.random(a.shape)
    rumore = np.asarray(Image.fromarray((rumore * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), dtype=np.float32) / 255
    a = np.where((a < 0.5) & (rumore > 0.53), 1.0, a)
    img = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.1))
    return img


def incolla(base: Image.Image, strato: Image.Image, x: int, y: int, ancora: str = "alto-sinistra"):
    """Incolla moltiplicando: il nero del testo si somma alla pagina senza coprire nulla."""
    if ancora == "basso-sinistra":
        y = y - strato.height
    regione = base.crop((x, y, x + strato.width, y + strato.height))
    unito = Image.fromarray(np.minimum(np.asarray(regione), np.asarray(strato)), "L")
    base.paste(unito, (x, y))


# ---------------------------------------------------------------- tavola

def componi(cartella: Path, prova: bool = False) -> Path:
    spec = yaml.safe_load((cartella / "tavola.yaml").read_text(encoding="utf-8"))
    base = pagina_base(spec["pagina_pdf"])
    d = ImageDraw.Draw(base)
    for zona in spec.get("cancella", []):
        d.rectangle(zona, fill=255)
    for el in spec.get("testi", []):
        strato, (ax, ay) = strato_testo(el, base.size)
        # (x, y) = dove cade l'inizio della linea di base della prima riga,
        # anche per il testo ruotato
        incolla(base, strato, round(el["x"] - ax), round(el["y"] - ay))
    for linea in spec.get("linee", []):
        d.rectangle(linea, fill=0)
    USCITA.mkdir(parents=True, exist_ok=True)
    destinazione = USCITA / f"{cartella.name}.png"
    if prova:
        rgb = base.convert("RGB")
        dr = ImageDraw.Draw(rgb)
        for zona in spec.get("cancella", []):
            dr.rectangle(zona, outline=(220, 0, 0), width=4)
        destinazione = USCITA / f"{cartella.name}-prova.png"
        rgb.save(destinazione, dpi=(DPI, DPI))
    else:
        base.save(destinazione, dpi=(DPI, DPI))
        confronto(spec["pagina_pdf"], base, cartella.name)
    return destinazione


def confronto(numero_pdf: int, tavola: Image.Image, nome: str):
    """Affianca originale e tavola a mezza risoluzione, per la revisione."""
    originale = pagina_base(numero_pdf)
    w, h = tavola.width // 2, tavola.height // 2
    foglio = Image.new("L", (w * 2 + 30, h), 255)
    foglio.paste(originale.resize((w, h)), (0, 0))
    foglio.paste(tavola.resize((w, h)), (w + 30, 0))
    cartella = RADICE / "build" / "confronti"
    cartella.mkdir(parents=True, exist_ok=True)
    foglio.save(cartella / f"{nome}.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tavole", nargs="+", type=Path)
    ap.add_argument("--prova", action="store_true", help="evidenzia le zone cancellate")
    args = ap.parse_args()
    for t in args.tavole:
        if (t / "tavola.yaml").exists():
            print(componi(t, args.prova))


if __name__ == "__main__":
    main()
