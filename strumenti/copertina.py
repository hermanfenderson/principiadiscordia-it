#!/usr/bin/env python3
"""Compone la copertina stesa (quarta + dorso + prima) per il cartaceo KDP.

Formato predefinito A5 (148 x 210 mm): le pagine Loompanics misurano 132 x 203 mm e ci
stanno quasi al 100%, con qualche millimetro in più ai lati. A5 esiste sia su StreetLib
sia su KDP (5,83 x 8,27 pollici).
Il dorso dipende dal numero di pagine e dalla carta (valori KDP indicativi:
bianca 0,002252 pollici per pagina, crema 0,0025): da ricontrollare col calcolatore KDP.

Uso:
  python3 strumenti/copertina.py --pagine 130 --carta crema --variante ocra
  python3 strumenti/copertina.py --pagine 114 --piattaforma streetlib --dorso-mm 9
Con --piattaforma streetlib: abbondanza 0,20", testi a 0,6" dai bordi (la tavola della prima
viene ridotta perché l'inchiostro stia nell'area sicura), nessun riquadro per il codice a barre
(lo stampa StreetLib: resta libera la zona in basso a destra della quarta, 8 x 5 cm),
e in più un PDF CMYK senza profilo incorporato (build/copertina/copertina-<variante>-streetlib.pdf).
Il dorso si prende dal calcolatore StreetLib (--dorso-mm).
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
VARIANTI = {"bianca": (255, 255, 255), "ocra": (208, 146, 12)}  # ocra = il giallo della copertina Loompanics (mediana della scansione)
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


def etichetta(righe: list[str]) -> Image.Image:
    """Etichetta di carta incollata sulla copertina, timbrata a mano (RGBA, già ruotata)."""
    from componi import timbro as effetto_timbro
    f = font("Oswald-VF.ttf", 46)
    f.set_variation_by_axes([500])
    larga = max(round(f.getlength(r)) for r in righe) + 90
    alta = 60 * len(righe) + 56
    strato = Image.new("L", (larga, alta), 255)
    d = ImageDraw.Draw(strato)
    for i, r in enumerate(righe):
        d.text((larga // 2, 28 + 48 + i * 60), r, font=f, fill=0, anchor="ms")
    strato = effetto_timbro(strato)
    e = Image.new("RGBA", (larga, alta), (250, 247, 236, 255))
    e.paste(INCHIOSTRO + (255,), (0, 0), strato.point(lambda v: 255 - v))
    ImageDraw.Draw(e).rectangle([10, 10, larga - 11, alta - 11], outline=INCHIOSTRO + (255,), width=4)
    return e.rotate(8, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))


def frontespizio(prima: dict) -> Image.Image:
    """La tavola p013 ricomposta per la copertina.

    Da libro/copertina.yaml (sezione "prima"): "togli" elenca le righe di p013 da non riportare,
    "cancella" altre zone della scansione da sbiancare, "aggiungi" gli elementi di testo nuovi,
    "immagini" le immagini da incollare (per esempio un disegno spostato).
    """
    from componi import componi
    spec = yaml.safe_load((RADICE / "tavole" / "p013" / "tavola.yaml").read_text(encoding="utf-8"))
    togli = set(prima.get("togli", []))
    spec["testi"] = [el for el in spec["testi"] if not set(el.get("righe", [])) & togli]
    spec["cancella"] += prima.get("cancella", [])
    spec["testi"] += prima.get("aggiungi", [])
    spec["immagini"] = spec.get("immagini", []) + prima.get("immagini", [])
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
    ap.add_argument("--piattaforma", choices=["kdp", "streetlib"], default="kdp")
    ap.add_argument("--dorso-mm", type=float, help="larghezza del dorso dal calcolatore della piattaforma")
    ap.add_argument("--prima", choices=["disegno", "spirale"], default="disegno",
                    help="disegno: il frontespizio di Hill (p013) col timbro; spirale: la copertina Loompanics (p001) con l'etichetta")
    args = ap.parse_args()
    global LARGHEZZA, ALTEZZA, ABBONDANZA
    LARGHEZZA, ALTEZZA = FORMATI[args.formato]
    streetlib = args.piattaforma == "streetlib"
    if streetlib:
        ABBONDANZA = 0.20

    testi = yaml.safe_load((RADICE / "libro" / "copertina.yaml").read_text(encoding="utf-8"))
    carta = VARIANTI[args.variante]
    dorso = px(args.dorso_mm / 25.4) if args.dorso_mm else px(args.pagine * SPESSORE_CARTA[args.carta])
    W = px(ABBONDANZA) * 2 + px(LARGHEZZA) * 2 + dorso
    H = px(ALTEZZA + 2 * ABBONDANZA)
    tela = Image.new("RGB", (W, H), carta)
    d = ImageDraw.Draw(tela)
    x_quarta = px(ABBONDANZA)
    x_dorso = x_quarta + px(LARGHEZZA)
    x_prima = x_dorso + dorso
    y0 = px(ABBONDANZA)
    margine = px(0.6 if streetlib else 0.375)

    # ---- prima
    alt = px(ALTEZZA - 0.25)  # tutta la pagina dentro l'area sicura (0,125 pollici dal taglio), centrata
    if args.prima == "disegno":
        # il frontespizio italiano di Hill (tavola p013), ricomposto secondo libro/copertina.yaml
        front = frontespizio(testi["prima"])
        if streetlib:
            # l'inchiostro (non la tavola intera) deve stare a 0,6" dai bordi: si riduce e si centra
            import numpy as np
            a = np.asarray(front.convert("L")) < 128
            righe, colonne = np.where(a.sum(1) > 2)[0], np.where(a.sum(0) > 2)[0]
            bx0_, by0_, bx1_, by1_ = colonne[0], righe[0], colonne[-1], righe[-1]
            k = min((px(LARGHEZZA) - 2 * margine) / (bx1_ - bx0_), (px(ALTEZZA) - 2 * margine) / (by1_ - by0_))
            front = front.resize((round(front.width * k), round(front.height * k)), Image.LANCZOS)
            cx_ink, cy_ink = (bx0_ + bx1_) / 2 * k, (by0_ + by1_) / 2 * k
            tela.paste(tinta(front, carta), (round(x_prima + px(LARGHEZZA) / 2 - cx_ink),
                                             round(y0 + px(ALTEZZA) / 2 - cy_ink)))
            print(f"prima: tavola p013 al {k * 360 / DPI * 100:.0f}% della grandezza originale")
        else:
            front = front.resize((round(front.width * alt / front.height), alt), Image.LANCZOS)
            tela.paste(tinta(front, carta), (x_prima + (px(LARGHEZZA) - front.width) // 2, y0 + px(0.125)))
        # timbro del traduttore in diagonale, nello stile di "NON E' POSTA SPAZZATURA" (se previsto)
        if testi["prima"].get("timbro"):
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
    else:
        # la copertina gialla Loompanics in italiano (tavola p001), con l'etichetta dell'edizione italiana
        from componi import componi
        front = Image.open(componi(RADICE / "tavole" / "p001"))
        k = alt / front.height
        front = front.resize((round(front.width * k), alt), Image.LANCZOS)
        fx, fy = x_prima + (px(LARGHEZZA) - front.width) // 2, y0 + px(0.125)
        tela.paste(tinta(front, carta), (fx, fy))
        e = etichetta(testi["prima"]["etichetta"])
        # sull'angolo in basso a destra della spirale (in p001: x 328-1468, y 1185-2370)
        cx, cy = fx + round(1330 * k), fy + round(2215 * k)
        tela.paste(e, (cx - e.width // 2, cy - e.height // 2), e)

    # ---- dorso
    if dorso >= px(0.25):
        s = Image.new("RGB", (px(ALTEZZA), dorso), carta)
        ds = ImageDraw.Draw(s)
        # titolo centrato sull'inchiostro (non sul corpo), con almeno 1,6 mm di margine per lato (KDP)
        fg = font(testi["dorso"].get("font", "MysteryQuest-Regular.ttf"), round(dorso * 0.46))
        t = testi["dorso"]["titolo"]
        bb = fg.getbbox(t, anchor="ls", stroke_width=1)
        yb = round(dorso / 2 - (bb[1] + bb[3]) / 2)
        ds.text((px(0.6), yb), t, font=fg, fill=INCHIOSTRO, anchor="ls",
                stroke_width=1, stroke_fill=INCHIOSTRO)  # un filo di grassetto, come sulla prima
        fa = font("Jost-Medium.ttf", round(dorso * 0.40))  # circa 8 pt con 114 pagine
        testo(ds, (px(ALTEZZA) - px(0.6), dorso // 2), testi["dorso"]["autore"], fa, "rm")
        tela.paste(s.rotate(-90, expand=True), (x_dorso, y0))

    # ---- quarta
    x = x_quarta + margine
    larghezza = px(LARGHEZZA) - 2 * margine
    y = y0 + margine + 40
    q = testi["quarta"]
    k = 0.9 if streetlib else 1.0   # StreetLib: margini più larghi e zona del codice a barre più grande
    fd = font("CourierPrime-Bold.ttf", round(46 * k))
    for battuta in q["citazione"]:
        y = blocco(d, x, y, battuta, fd, larghezza, round(56 * k)) - 10
    testo(d, (x + larghezza, y + 10), q["fonte_citazione"], font("CourierPrime-Italic.ttf", round(38 * k)), "rs")
    y += round(110 * k)
    d.rectangle([x, y - 40, x + larghezza, y - 36], fill=INCHIOSTRO)
    y = blocco(d, x, y + 20, q["presentazione"], font("OldStandard-Regular.ttf", round(44 * k)), larghezza, round(56 * k))
    yb = y0 + px(ALTEZZA) - margine
    fp = font("Jost-Regular.ttf", 34)
    ff = font("Kalam-Bold.ttf", 38)  # circa 9 pt: è scritta a mano, più piccola si legge a fatica
    struzzo = Image.open(RADICE / "tavole" / "apparato" / "struzzo-00010.png")
    if streetlib:
        # La guida italiana di StreetLib chiede almeno 8 x 5 cm liberi in fondo alla quarta, senza
        # riquadri. In basso: lo struzzo con la didascalia a sinistra, la zona libera a destra;
        # sopra, a tutta larghezza, la nota sul traduttore e la licenza.
        bx0, by0 = x + larghezza - px(80 / 25.4), yb - px(50 / 25.4)
        colonna = bx0 - x - px(2 / 25.4)
        ff = font("Kalam-Bold.ttf", 37)
        didascalia = a_capo(" ".join(q["didascalia"].split()), ff, colonna)
        alt_didascalia = len(didascalia) * 44
        # via il bordo bianco della scansione, che sull'ocra non si vede ma ruba spazio
        import numpy as np
        a = np.asarray(struzzo.convert("L")) < 128
        rr, cc = np.where(a.sum(1) > 2)[0], np.where(a.sum(0) > 2)[0]
        struzzo = struzzo.crop((cc[0], rr[0], cc[-1] + 1, rr[-1] + 1))
        ls = colonna
        struzzo = struzzo.resize((ls, round(struzzo.height * ls / struzzo.width)), Image.LANCZOS)
        y_struzzo = yb - alt_didascalia - 20 - struzzo.height
        tela.paste(tinta(struzzo, carta), (x, y_struzzo))
        yd = y_struzzo + struzzo.height + 20 + 30
        for r in didascalia:
            testo(d, (x, yd), r, ff, "ls")
            yd += 44
        y += 20
        fine_bio = blocco(d, x, y, q["traduttore"], font("OldStandard-Italic.ttf", round(41 * k)), larghezza, round(51 * k))
        righe_piede = [a_capo(r, fp, larghezza) for r in q["piede"]]
        altezza = sum(len(g) for g in righe_piede) * 43 + (len(righe_piede) - 1) * 10 - 43
        yp = min(by0, y_struzzo) - 40 - altezza
        libero = (yp - 34) - fine_bio
        print(f"quarta: {libero / DPI * 25.4:.1f} mm liberi tra la nota sul traduttore e la licenza")
        if libero < px(0.08):
            sys.exit("la quarta non ci sta: ridurre i testi o i corpi")
    else:
        # traduttore: struzzo a sinistra, nota a destra
        y += 30
        ls = round(larghezza * 0.42)
        struzzo = struzzo.resize((ls, round(struzzo.height * ls / struzzo.width)), Image.LANCZOS)
        tela.paste(tinta(struzzo, carta), (x, y))
        blocco(d, x, y + struzzo.height + 50, q["didascalia"], ff, ls, 46)
        blocco(d, x + ls + 40, y + 30, q["traduttore"], font("OldStandard-Italic.ttf", 41), larghezza - ls - 40, 51)
        # piede: licenza a sinistra, spazio per il codice a barre KDP a destra (2 x 1,2 pollici)
        bx0, by0 = x + larghezza - px(2.0), yb - px(1.2)
        # piede allineato in basso: l'ultima riga sulla stessa linea del fondo del riquadro
        righe_piede = [a_capo(r, fp, bx0 - x - 40) for r in q["piede"]]
        altezza = sum(len(g) for g in righe_piede) * 43 + (len(righe_piede) - 1) * 10 - 43
        yp = yb - 8 - altezza
    for gruppo in righe_piede:
        for rr in gruppo:
            testo(d, (x, yp), rr, fp, "ls")
            yp += 43
        yp += 10

    # versione per lo schermo (sito, PDF da sfogliare, EPUB): senza il riquadro del codice a barre,
    # tutta ocra; quella per la stampa tiene il riquadro bianco dove KDP/StreetLib mettono l'ISBN
    schermo = tela.copy()
    if not streetlib:  # StreetLib stampa da sé il codice a barre: niente riquadro
      d.rectangle([bx0, by0, x + larghezza, yb], fill=(255, 255, 255), outline=(170, 170, 170), width=2)
      testo(d, ((bx0 + x + larghezza) // 2, (by0 + yb) // 2), "codice a barre", font("Jost-Regular.ttf", 28), "mm", (150, 150, 150))

    uscita = RADICE / "build" / "copertina"
    uscita.mkdir(parents=True, exist_ok=True)
    nome = f"copertina-{args.variante}" + ("" if args.prima == "disegno" else f"-{args.prima}") + ("-streetlib" if streetlib else "")
    tela.save(uscita / f"{nome}.png", dpi=(DPI, DPI))
    schermo.save(uscita / f"{nome}-schermo.png", dpi=(DPI, DPI))
    anteprima = tela.copy()
    da = ImageDraw.Draw(anteprima)
    for xx in (x_dorso, x_prima):  # linee di piega, solo nell'anteprima
        da.line([(xx, 0), (xx, H)], fill=(200, 60, 60), width=3)
    da.rectangle([px(ABBONDANZA), px(ABBONDANZA), W - px(ABBONDANZA), H - px(ABBONDANZA)], outline=(60, 120, 200), width=3)
    anteprima.resize((W // 2, H // 2), Image.LANCZOS).save(uscita / f"{nome}-anteprima.png")

    # prima di copertina per l'ebook: solo la prima, senza abbondanza, JPG RGB di almeno 1875 x 2500 px
    pe = schermo.crop((x_prima, y0, x_prima + px(LARGHEZZA), y0 + px(ALTEZZA)))
    pe = pe.resize((1875, round(1875 * pe.height / pe.width)), Image.LANCZOS)
    pe.save(uscita / f"{nome}-prima-ebook.jpg", quality=92, dpi=(DPI, DPI))

    if streetlib:
        pdf_cmyk(tela, uscita / f"{nome}.pdf")
    print(uscita / f"{nome}.png", f"{W}x{H}px, dorso {dorso}px")


def pdf_cmyk(tela: Image.Image, pdf: Path):
    """PDF a una pagina in CMYK, senza profilo incorporato (come chiede StreetLib).
    Conversione colorimetrica sRGB -> FOGRA39 (carta patinata) se il profilo c'è, altrimenti
    il CMYK predefinito di Ghostscript."""
    import img2pdf
    from PIL import ImageCms
    candidati = [Path(p) for p in (
        "/usr/share/texlive/texmf-dist/tex/generic/colorprofiles/FOGRA39L_coated.icc",
        "/Library/ColorSync/Profiles/CoatedFOGRA39.icc",
        "/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc",
        "/usr/share/color/icc/ghostscript/default_cmyk.icc",
    )]
    profilo = next((p for p in candidati if p.exists()), None)
    if profilo is None:
        sys.exit("nessun profilo CMYK trovato per la conversione")
    cmyk = ImageCms.profileToProfile(tela, ImageCms.createProfile("sRGB"), str(profilo),
                                     renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                     outputMode="CMYK", flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
    jpg = pdf.with_suffix(".cmyk.jpg")
    cmyk.save(jpg, quality=95, dpi=(DPI, DPI))   # senza icc_profile
    pdf.write_bytes(img2pdf.convert(str(jpg), layout_fun=img2pdf.get_fixed_dpi_layout_fun((DPI, DPI))))
    print(pdf, "profilo di conversione:", profilo.name)


if __name__ == "__main__":
    main()
