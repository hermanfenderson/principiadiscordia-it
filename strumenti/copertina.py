#!/usr/bin/env python3
"""Compone la copertina stesa (quarta + dorso + prima) per il cartaceo KDP.

Formato predefinito A5 (148 x 210 mm): le pagine Loompanics misurano 132 x 203 mm e ci
stanno quasi al 100%, con qualche millimetro in più ai lati. A5 esiste sia su StreetLib
sia su KDP (5,83 x 8,27 pollici).
Il dorso dipende dal numero di pagine e dalla carta (valori KDP indicativi:
bianca 0,002252 pollici per pagina, crema 0,0025): da ricontrollare col calcolatore KDP.

Uso:
  python3 strumenti/copertina.py --pagine 130 --carta crema --variante ocra
Uscita: build/copertina/copertina-<variante>.png (300 dpi) e un'anteprima ridotta.
"""
import argparse
from pathlib import Path

import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "strumenti"))
FONT = RADICE / "strumenti" / "font"
DPI = 300
FORMATI = {  # larghezza, altezza in pollici
    "a5": (148 / 25.4, 210 / 25.4),
    "tascabile": (115 / 25.4, 190 / 25.4),
    "152x228": (152 / 25.4, 228 / 25.4),
    "kdp-5.25x8": (5.25, 8.0),
}
LARGHEZZA, ALTEZZA = FORMATI["a5"]
ABBONDANZA = 0.125
SPESSORE_CARTA = {"bianca": 0.002252, "crema": 0.0025}
VARIANTI = {"bianca": (255, 255, 255), "ocra": (241, 225, 141)}  # ocra = il fondo del vecchio sito
INCHIOSTRO = (20, 18, 16)


def px(pollici: float) -> int:
    return round(pollici * DPI)


def font(nome: str, corpo: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT / nome), corpo)


def tinta(img: Image.Image, carta) -> Image.Image:
    """Porta una tavola in scala di grigi su carta colorata: il bianco diventa carta, il nero inchiostro."""
    g = img.convert("L")
    return Image.merge("RGB", [g.point(lambda v, c=c, k=k: round(k + (c - k) * v / 255))
                               for c, k in zip(carta, INCHIOSTRO)])


def testo(d, xy, t, f, ancora="la", colore=INCHIOSTRO):
    d.text(xy, t, font=f, fill=colore, anchor=ancora)


def a_capo(t: str, f, larghezza: int) -> list[str]:
    righe, riga = [], ""
    for parola in t.split():
        prova = f"{riga} {parola}" if riga else parola
        if f.getlength(prova) <= larghezza:
            riga = prova
        else:
            righe.append(riga)
            riga = parola
    return righe + [riga]


def blocco(d, x, y, t, f, larghezza, interlinea, colore=INCHIOSTRO) -> int:
    for paragrafo in t.split("\n\n"):
        for r in a_capo(" ".join(paragrafo.split()), f, larghezza):
            testo(d, (x, y), r, f, "ls", colore)
            y += interlinea
        y += interlinea // 2
    return y


def frontespizio(togli: list[str]) -> Image.Image:
    """La tavola p013 ricomposta senza le scritte da togliere in copertina."""
    from componi import componi
    spec = yaml.safe_load((RADICE / "tavole" / "p013" / "tavola.yaml").read_text(encoding="utf-8"))
    spec["testi"] = [el for el in spec["testi"] if not set(el.get("righe", [])) & set(togli)]
    cartella = RADICE / "build" / "copertina" / "p013-copertina"
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "tavola.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    return Image.open(componi(cartella))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pagine", type=int, default=130)
    ap.add_argument("--carta", choices=SPESSORE_CARTA, default="crema")
    ap.add_argument("--variante", choices=VARIANTI, default="ocra")
    ap.add_argument("--formato", choices=FORMATI, default="a5")
    args = ap.parse_args()
    global LARGHEZZA, ALTEZZA
    LARGHEZZA, ALTEZZA = FORMATI[args.formato]

    testi = yaml.safe_load((RADICE / "libro" / "copertina.yaml").read_text(encoding="utf-8"))
    carta = VARIANTI[args.variante]
    dorso = px(args.pagine * SPESSORE_CARTA[args.carta])
    W = px(ABBONDANZA) * 2 + px(LARGHEZZA) * 2 + dorso
    H = px(ALTEZZA + 2 * ABBONDANZA)
    tela = Image.new("RGB", (W, H), carta)
    d = ImageDraw.Draw(tela)
    x_quarta = px(ABBONDANZA)
    x_dorso = x_quarta + px(LARGHEZZA)
    x_prima = x_dorso + dorso
    y0 = px(ABBONDANZA)
    margine = px(0.375)

    # ---- prima: il frontespizio italiano (tavola p013), ritagliato al formato
    front = frontespizio(testi["prima"].get("togli", []))
    # tutta la pagina dentro l'area sicura (0,125 pollici dal taglio), centrata
    alt = px(ALTEZZA - 0.25)
    front = front.resize((round(front.width * alt / front.height), alt), Image.LANCZOS)
    tela.paste(tinta(front, carta), (x_prima + (px(LARGHEZZA) - front.width) // 2, y0 + px(0.125)))
    # timbro del traduttore, nello stile di "NON E' POSTA SPAZZATURA"
    t = testi["prima"]["timbro"]
    f = font("Oswald-VF.ttf", 62)
    f.set_variation_by_axes([500])
    strato = Image.new("L", (round(f.getlength(t)) + 40, 110), 255)
    ImageDraw.Draw(strato).text((20, 85), t, font=f, fill=0, anchor="ls")
    from componi import timbro as effetto_timbro
    strato = effetto_timbro(strato)
    strato = strato.rotate(-14, expand=True, fillcolor=255, resample=Image.BICUBIC)
    maschera = strato.point(lambda v: 255 - v)
    tela.paste(INCHIOSTRO, (x_prima + px(LARGHEZZA) - strato.width - px(0.3), y0 + px(ALTEZZA * 0.555)), maschera)

    # ---- dorso
    if dorso >= px(0.25):
        s = Image.new("RGB", (px(ALTEZZA), dorso), carta)
        ds = ImageDraw.Draw(s)
        fg = font("UnifrakturMaguntia-Book.ttf", round(dorso * 0.55))
        testo(ds, (px(0.6), dorso // 2), testi["dorso"]["titolo"], fg, "lm")
        fa = font("Jost-Medium.ttf", round(dorso * 0.32))
        testo(ds, (px(ALTEZZA) - px(0.6), dorso // 2), testi["dorso"]["autore"], fa, "rm")
        tela.paste(s.rotate(-90, expand=True), (x_dorso, y0))

    # ---- quarta
    x = x_quarta + margine
    larghezza = px(LARGHEZZA) - 2 * margine
    y = y0 + margine + 40
    q = testi["quarta"]
    fd = font("CourierPrime-Bold.ttf", 46)
    for battuta in q["citazione"]:
        y = blocco(d, x, y, battuta, fd, larghezza, 56) - 10
    testo(d, (x + larghezza, y + 10), q["fonte_citazione"], font("CourierPrime-Italic.ttf", 36), "rs")
    y += 110
    d.rectangle([x, y - 40, x + larghezza, y - 36], fill=INCHIOSTRO)
    y = blocco(d, x, y + 20, q["presentazione"], font("OldStandard-Regular.ttf", 40), larghezza, 50)
    # traduttore: struzzo a sinistra, nota a destra
    y += 30
    struzzo = Image.open(RADICE / "tavole" / "apparato" / "struzzo-00010.png")
    ls = round(larghezza * 0.42)
    struzzo = struzzo.resize((ls, round(struzzo.height * ls / struzzo.width)), Image.LANCZOS)
    tela.paste(tinta(struzzo, carta), (x, y))
    ff = font("Kalam-Bold.ttf", 30)
    blocco(d, x, y + struzzo.height + 45, q["didascalia"], ff, ls, 36)
    blocco(d, x + ls + 40, y + 30, q["traduttore"], font("OldStandard-Italic.ttf", 36), larghezza - ls - 40, 44)
    # piede: licenza a sinistra, spazio per il codice a barre KDP a destra (2 x 1,2 pollici)
    yb = y0 + px(ALTEZZA) - margine
    bx0, by0 = x + larghezza - px(2.0), yb - px(1.2)
    d.rectangle([bx0, by0, x + larghezza, yb], fill=(255, 255, 255), outline=(170, 170, 170), width=2)
    testo(d, ((bx0 + x + larghezza) // 2, (by0 + yb) // 2), "codice a barre", font("Jost-Regular.ttf", 28), "mm", (150, 150, 150))
    fp = font("Jost-Regular.ttf", 28)
    yp = by0 + 30
    for r in q["piede"]:
        for rr in a_capo(r, fp, bx0 - x - 40):
            testo(d, (x, yp), rr, fp, "ls")
            yp += 36
        yp += 8

    uscita = RADICE / "build" / "copertina"
    uscita.mkdir(parents=True, exist_ok=True)
    nome = f"copertina-{args.variante}"
    tela.save(uscita / f"{nome}.png", dpi=(DPI, DPI))
    anteprima = tela.copy()
    da = ImageDraw.Draw(anteprima)
    for xx in (x_dorso, x_prima):  # linee di piega, solo nell'anteprima
        da.line([(xx, 0), (xx, H)], fill=(200, 60, 60), width=3)
    da.rectangle([px(ABBONDANZA), px(ABBONDANZA), W - px(ABBONDANZA), H - px(ABBONDANZA)], outline=(60, 120, 200), width=3)
    anteprima.resize((W // 2, H // 2), Image.LANCZOS).save(uscita / f"{nome}-anteprima.png")
    print(uscita / f"{nome}.png", f"{W}x{H}px, dorso {dorso}px")


if __name__ == "__main__":
    main()
