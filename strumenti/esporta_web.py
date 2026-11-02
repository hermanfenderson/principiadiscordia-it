#!/usr/bin/env python3
"""Esporta immagini e dati delle pagine per il sito (sito/).

Legge l'ordine del libro, gli indirizzi (libro/pagine-web.yaml), i testi accessibili e, dove ci
sono, le trascrizioni inglesi di Wikisource (testo/en/pagine/), e produce:

  sito/src/data/pagine.json          pagine, sezioni e indice per Astro
  sito/public/tavole/<tavola>-<L>.{avif,jpg}   le tavole in più larghezze (+ -piena.jpg)
  sito/public/originale/<tavola>-<L>.{avif,jpg} le pagine della scansione Loompanics
  sito/public/copertina/…            la prima di copertina e l'immagine per i social
  sito/public/scarica/…              PDF per lo schermo ed EPUB (al massimo 25 MiB ciascuno)

Prima servono tavole, copertina, PDF ed EPUB (vedi CLAUDE.md). Le immagini già esportate e più
recenti della sorgente non si rifanno.

Uso:
    python3 strumenti/esporta_web.py
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml
from PIL import Image

RADICE = Path(__file__).resolve().parent.parent
SITO = RADICE / "sito"
PUBBLICO = SITO / "public"
DATI = SITO / "src" / "data"
LARGHEZZE = (300, 600, 1000, 1400)      # le tavole sono larghe circa 1830 px: -piena.jpg è l'originale
LIMITE = 25 * 1024 * 1024           # limite per file degli asset statici di Cloudflare
WIKISOURCE = "https://en.wikisource.org/wiki/Page:Principia_Discordia_(Loompanics_Unlimited_edition).pdf/{n}"
COMMONS = "https://commons.wikimedia.org/w/index.php?title=File:Principia_Discordia_(Loompanics_Unlimited_edition).pdf&page={n}"
OCRA = (208, 146, 12)


def leggi_yaml(percorso: Path):
    return yaml.safe_load(percorso.read_text(encoding="utf-8"))


def leggi_md(percorso: Path) -> tuple[dict, str]:
    s = percorso.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", s, re.S)
    return yaml.safe_load(m.group(1)), m.group(2)


def md_html(t: str, livello: int = 3) -> str:
    """Markdown -> HTML, con i titoli portati almeno al livello voluto."""
    h = markdown.markdown(t, extensions=["tables", "sane_lists"])
    return re.sub(r"<(/?)h(\d)>", lambda m: f"<{m.group(1)}h{min(6, max(livello, int(m.group(2))))}>", h)


def aggiornato(dest: Path, sorgente: Path) -> bool:
    return dest.exists() and dest.stat().st_mtime >= sorgente.stat().st_mtime


def esporta_immagine(sorgente: Path, cartella: Path, nome: str, misura: tuple[int, int] | None = None) -> dict:
    """Più larghezze in AVIF e JPEG, più la piena risoluzione in JPEG. Ritorna srcset e misure."""
    cartella.mkdir(parents=True, exist_ok=True)
    img = None

    def apri():
        nonlocal img
        if img is None:
            img = Image.open(sorgente)
            img = img.convert("L") if img.mode in ("L", "LA", "1", "P") else img.convert("RGB")
            if misura and img.size != misura:
                img = img.resize(misura, Image.LANCZOS)
        return img

    with Image.open(sorgente) as prova:
        w, h = misura or prova.size
    piena = cartella / f"{nome}-piena.jpg"
    if not aggiornato(piena, sorgente):
        apri().save(piena, quality=82, optimize=True, progressive=True)
    avif, jpg = [], []
    for L in LARGHEZZE:
        if L >= w:
            continue
        A = round(h * L / w)
        for ext, lista in (("avif", avif), ("jpg", jpg)):
            dest = cartella / f"{nome}-{L}.{ext}"
            if not aggiornato(dest, sorgente):
                r = apri().resize((L, A), Image.LANCZOS)
                if ext == "avif":
                    # AVIF monocromatiche (4:0:0): alcuni browser non le decodificano, meglio RGB
                    r.convert("RGB").save(dest, quality=55, speed=6)
                else:
                    r.save(dest, quality=78, optimize=True, progressive=True)
            lista.append(f"{dest.relative_to(PUBBLICO).as_posix()} {L}w")
    base = "/" + cartella.relative_to(PUBBLICO).as_posix()
    return {
        "larghezza": w, "altezza": h,
        "avif": ", ".join("/" + s for s in avif),
        "jpg": ", ".join("/" + s for s in jpg),
        "src": f"{base}/{nome}-1000.jpg" if 1000 < w else f"{base}/{nome}-piena.jpg",
        "piena": f"{base}/{nome}-piena.jpg",
    }


def indice_originale(testo: str) -> list[tuple[int, str]]:
    """Le voci dell'indice di pagina 00002: «17 Il mito della Mela della Discordia»."""
    voci = []
    for riga in testo.splitlines():
        m = re.match(r"(\d+) (.+?)\s*$", riga.strip())
        if m and not re.fullmatch(r"0+\d+", riga.strip()):
            voci.append((int(m.group(1)), m.group(2)))
    return voci


def copertina() -> tuple[dict, dict]:
    """Prima e quarta di copertina ritagliate dalla stesa (come in epub.py) e immagine per i social."""
    sorgente = RADICE / "build" / "copertina" / "copertina-ocra-schermo.png"
    cartella = PUBBLICO / "copertina"
    prima, quarta = cartella / "prima.png", cartella / "quarta.png"
    if not (aggiornato(prima, sorgente) and aggiornato(quarta, sorgente)):
        cartella.mkdir(parents=True, exist_ok=True)
        stesa = Image.open(sorgente).convert("RGB")
        ab, pw, ph = round(0.125 * 300), round(148 / 25.4 * 300), round(210 / 25.4 * 300)
        dorso = stesa.width - 2 * ab - 2 * pw
        x0 = ab + pw + dorso
        c = stesa.crop((x0, ab, x0 + pw, ab + ph))
        c.save(prima)
        stesa.crop((ab, ab, ab + pw, ab + ph)).save(quarta)
        # Open Graph 1200 x 630: la prima su fondo ocra
        og = Image.new("RGB", (1200, 630), OCRA)
        k = 600 / c.height
        r = c.resize((round(c.width * k), 600), Image.LANCZOS)
        og.paste(r, ((1200 - r.width) // 2, 15))
        og.save(cartella / "social.jpg", quality=85, optimize=True)
    return esporta_immagine(prima, cartella, "prima"), esporta_immagine(quarta, cartella, "quarta")


def pagine_copertina(cop: dict, img_prima: dict, img_quarta: dict) -> tuple[dict, dict]:
    """Copertina e quarta come pagine dello sfogliatore, con i testi accessibili di libro/copertina.yaml."""
    q = cop["quarta"]
    paragrafi = lambda t: [" ".join(x.split()) for x in t.split("\n\n") if x.strip()]
    comune = {"hill": None, "voce": None, "originale": None,
              "avviso": "la copertina dell'edizione italiana è nuova"}
    prima = dict(comune, slug="copertina", tavola="copertina", numero=0, lato="destra",
                 sezione="Copertina", titolo="Copertina", posizione="prima di copertina",
                 alt="Copertina: Principia Discordia, ovvero Come trovai la Dea e Cosa le feci Quando la trovai. "
                     "Edizione italiana, traduzione di Herman Fenderson.",
                 descrizione=md_html(
                     "Copertina color ocra. In alto «Sua Grande Narcoticità Malaclypse il Giovane», poi il titolo "
                     "«Principia Discordia» in grandi lettere a riccioli, «ovvero» e il sottotitolo «Come trovai la Dea "
                     "e Cosa le feci Quando la trovai»; sotto, «In cui è Spiegata Assolutamente Qualsiasi Cosa che Valga "
                     "la Pena di Sapere A proposito Assolutamente di Tutto». In basso a sinistra una croce nera "
                     "attraversata da due mezzelune; accanto «Edizione italiana, traduzione, prefazione alla prefazione "
                     "e note di Herman Fenderson» e, sotto, una statua di donna distesa.", 4),
                 testo=md_html("SUA GRANDE NARCOTICITÀ MALACLYPSE IL GIOVANE\n\n### <span lang=\"la\">Principia Discordia</span>\n\n"
                               "OVVERO\n\nCome trovai la Dea e Cosa le feci Quando la trovai\n\n"
                               "In cui è Spiegata Assolutamente Qualsiasi Cosa che Valga la Pena di Sapere "
                               "A proposito Assolutamente di Tutto\n\nEDIZIONE ITALIANA\n\n"
                               "traduzione, prefazione alla prefazione e note di HERMAN FENDERSON", 4),
                 immagine=img_prima)
    testo_quarta = ("\n\n".join(r.replace("--", "—") for r in q["citazione"]) + f"\n\n({q['fonte_citazione']})\n\n"
                    + "\n\n".join(paragrafi(q["presentazione"]))
                    + f"\n\nSotto il disegno dello struzzo: «{q['didascalia']}»\n\n"
                    + "\n\n".join(paragrafi(q["traduttore"])) + "\n\n"
                    + "\n\n".join(r.replace("--", "—") for r in q["piede"]))
    quarta = dict(comune, slug="quarta", tavola="quarta", numero=None, lato="sinistra",
                  sezione="Quarta di copertina", titolo="Quarta di copertina", posizione="quarta di copertina",
                  alt="Quarta di copertina: citazione di Malaclypse, presentazione del libro e nota sul traduttore "
                      "con il disegno di uno struzzo.",
                  descrizione=md_html(
                      "Quarta di copertina color ocra. In alto la citazione, un breve dialogo; sotto, la presentazione "
                      "del libro in tre capoversi; poi il disegno di uno struzzo con la testa nella sabbia, con la "
                      "didascalia scritta a mano, e accanto la nota su Herman Fenderson. In fondo la nota «All Rites "
                      "Reversed» e la licenza della traduzione.", 4),
                  testo=md_html(testo_quarta, 4), immagine=img_quarta)
    return prima, quarta


def scaricabili() -> list[dict]:
    file = [
        ("pdf", RADICE / "build" / "libro" / "principia-discordia-con-copertina.pdf",
         "principia-discordia-edizione-italiana.pdf"),
        ("epub", RADICE / "build" / "epub" / "principia-discordia.epub",
         "principia-discordia-edizione-italiana.epub"),
    ]
    uscita = []
    for tipo, sorgente, nome in file:
        if not sorgente.exists():
            print(f"ATTENZIONE: manca {sorgente.relative_to(RADICE)}", file=sys.stderr)
            continue
        peso = sorgente.stat().st_size
        if peso > LIMITE:
            sys.exit(f"{sorgente.name}: {peso / 2**20:.1f} MiB, oltre il limite di 25 MiB degli asset")
        dest = PUBBLICO / "scarica" / nome
        if not aggiornato(dest, sorgente):
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sorgente, dest)
        uscita.append({"tipo": tipo, "href": f"/scarica/{nome}", "byte": peso})
    return uscita


FONT_WEB = {  # file in strumenti/font/ -> nome del WOFF2 servito dal sito
    "MysteryQuest-Regular.ttf": "mysteryquest.woff2",
    "Jost-Regular.ttf": "jost-400.woff2",
    "Jost-Medium.ttf": "jost-500.woff2",
    "Jost-Bold.ttf": "jost-700.woff2",
    "Jost-Italic-VF.ttf": "jost-italic.woff2",
    "IBMPlexMono-Regular.ttf": "plexmono-400.woff2",
    "IBMPlexMono-Italic.ttf": "plexmono-italic.woff2",
    "IBMPlexMono-Medium.ttf": "plexmono-500.woff2",
    "Kalam-Regular.ttf": "kalam.woff2",
    "Oswald-VF.ttf": "oswald.woff2",
}
# caratteri con un Reserved Font Name ("Mystery Quest", "Plex"): per la OFL un sottoinsieme sarebbe una
# versione modificata, che non può portare quel nome; per questi si fa solo la conversione in WOFF2
SENZA_RIDUZIONE = {"MysteryQuest-Regular.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Italic.ttf", "IBMPlexMono-Medium.ttf"}
UNICODE_WEB = "U+0000-024F,U+02C6-02DD,U+1E00-1EFF,U+2000-206F,U+20AC,U+2116,U+2122,U+2190-2193,U+2212,U+25CF,U+FB01-FB02"


def font_web() -> None:
    """I caratteri del libro in WOFF2, ridotti all'alfabeto latino (tutti OFL: licenze accanto)."""
    from fontTools import subset
    cartella = PUBBLICO / "font"
    cartella.mkdir(parents=True, exist_ok=True)
    for sorgente, nome in FONT_WEB.items():
        src, dest = RADICE / "strumenti" / "font" / sorgente, cartella / nome
        if aggiornato(dest, src):
            continue
        if sorgente in SENZA_RIDUZIONE:
            from fontTools.ttLib import TTFont
            f = TTFont(src)
            f.flavor = "woff2"
            f.save(dest)
            continue
        subset.main([str(src), f"--unicodes={UNICODE_WEB}", "--flavor=woff2", "--layout-features=*",
                     f"--output-file={dest}"])
    for lic in ("OFL-mysteryquest.txt", "OFL-jost.txt", "OFL-ibmplexmono.txt", "OFL-kalam.txt", "OFL-oswald.txt"):
        shutil.copy2(RADICE / "strumenti" / "font" / lic, cartella / lic)


def sacro_cao() -> None:
    """Logo e favicon: il Sacro Cao di pagina 00003 (scansione, PDF 18), ritagliato nel suo cerchio."""
    import numpy as np
    sorgente = RADICE / "build" / "base" / "018.png"
    cartella = PUBBLICO / "cao"
    if aggiornato(cartella / "cao.png", sorgente):
        return
    cartella.mkdir(parents=True, exist_ok=True)
    cx, cy, r = 971.1, 1503.2, 496.7          # centro e raggio del cerchio sulla scansione a 360 dpi
    s = int(r + 3)
    pag = Image.open(sorgente).convert("L").crop((round(cx) - s, round(cy) - s, round(cx) + s, round(cy) + s))
    yy, xx = np.mgrid[:2 * s, :2 * s]
    dentro = (xx - s) ** 2 + (yy - s) ** 2 <= (r + 1) ** 2
    inchiostro = Image.fromarray(np.where(dentro, 255 - np.asarray(pag), 0).astype(np.uint8))
    disco = Image.fromarray((dentro * 255).astype(np.uint8))
    # inchiostro quasi nero su carta bianca dentro il cerchio, trasparente fuori
    cao = Image.new("RGBA", pag.size, (255, 255, 255, 0))
    cao.paste((255, 255, 255, 255), mask=disco)
    cao.paste((20, 18, 16, 255), mask=inchiostro)
    cao.resize((256, 256), Image.LANCZOS).save(cartella / "cao.png", optimize=True)
    for lato, nome in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (512, "icona-512.png")):
        cao.resize((lato, lato), Image.LANCZOS).save(cartella / nome, optimize=True)


def main():
    argparse.ArgumentParser(description=__doc__.split("\n")[0]).parse_args()

    ordine = leggi_yaml(RADICE / "libro" / "ordine.yaml")["pagine"]
    web = leggi_yaml(RADICE / "libro" / "pagine-web.yaml")
    sezioni_cfg = {s["tavola"]: s for s in web["sezioni"]}

    font_web()
    sacro_cao()

    pagine, sezione = [], None
    for numero, tavola in enumerate(ordine, start=1):
        if tavola == "bianca":
            continue
        testa, corpo = leggi_md(RADICE / "testo" / "accessibile" / f"{tavola}.md")
        descr = corpo.split("## Descrizione", 1)[1].split("## Testo", 1)[0].strip()
        testo = corpo.split("## Testo", 1)[1].strip()
        hill = testa.get("pagina_originale")
        slug = hill or web["indirizzi"].get(tavola)
        if not slug:
            sys.exit(f"{tavola}: manca l'indirizzo in libro/pagine-web.yaml")
        if tavola in sezioni_cfg:
            sezione = sezioni_cfg[tavola]["titolo"]
        png = RADICE / "build" / "tavole" / f"{tavola}.png"
        if not png.exists():
            sys.exit(f"Manca {png.relative_to(RADICE)}: lancia prima  python3 strumenti/libro.py --ricomponi")
        p = {
            "slug": slug, "tavola": tavola, "numero": numero,
            "lato": "destra" if numero % 2 else "sinistra",
            "hill": hill, "sezione": sezione,
            "alt": testa["alt"].strip(),
            "descrizione": md_html(descr, 4), "testo": md_html(testo, 4),
            "immagine": esporta_immagine(png, PUBBLICO / "tavole", tavola),
            "originale": None,
        }
        # la pagina corrispondente della scansione Loompanics (solo per le tavole pNNN)
        m = re.fullmatch(r"p(\d{3})", tavola)
        if m:
            n = int(m.group(1))
            base = RADICE / "build" / "base" / f"{n:03d}.png"
            if not base.exists():
                sys.path.insert(0, str(RADICE / "strumenti"))
                from componi import pagina_base
                pagina_base(n)
            orig = {"pdf": n, "wikisource": WIKISOURCE.format(n=n), "commons": COMMONS.format(n=n),
                    "testo": None, "revisione": None}
            en = RADICE / "testo" / "en" / "pagine" / f"{tavola}.md"
            if en.exists():
                testa_en, corpo_en = leggi_md(en)
                orig["testo"] = md_html(corpo_en.strip(), 3)
                orig["revisione"] = testa_en.get("revisione")
                orig["wikisource"] = testa_en.get("fonte", orig["wikisource"])
                orig["cronologia"] = testa_en.get("cronologia")
            misura = (p["immagine"]["larghezza"], p["immagine"]["altezza"])
            orig["immagine"] = esporta_immagine(base, PUBBLICO / "originale", tavola, misura)
            p["originale"] = orig
        pagine.append(p)

    cop = leggi_yaml(RADICE / "libro" / "copertina.yaml")
    img_prima, img_quarta = copertina()
    pag_prima, pag_quarta = pagine_copertina(cop, img_prima, img_quarta)
    pag_quarta["numero"] = len(ordine) + 1

    # posizione nella sezione, per i titoli delle pagine senza numero di Hill
    for p in pagine:
        p["posizione"] = f"pagina {p['numero']} di {len(ordine)} dell'edizione italiana"
        p["avviso"] = None if p["originale"] else "questa pagina non esiste nell'originale"
        stessa = [q for q in pagine if q["sezione"] == p["sezione"]]
        i = stessa.index(p) + 1
        p["titolo"] = (f"Pagina {p['hill']}" if p["hill"]
                       else web.get("titoli", {}).get(p["tavola"])
                       or p["sezione"] + (f", pagina {i} di {len(stessa)}" if len(stessa) > 1 else ""))
    pagine = [pag_prima] + pagine + [pag_quarta]
    for i, p in enumerate(pagine):
        p["prec"] = pagine[i - 1]["slug"] if i else None
        p["succ"] = pagine[i + 1]["slug"] if i + 1 < len(pagine) else None
    # doppia pagina, come nel libro stampato: pari a sinistra, dispari a destra
    per_numero = {p["numero"]: p for p in pagine}
    for p in pagine[1:-1]:
        sinistra = p["numero"] - (p["numero"] % 2)          # 0 per la prima pagina (sola a destra)
        destra = sinistra + 1
        altra = per_numero.get(destra if p["numero"] == sinistra else sinistra)
        p["compagna"] = altra["slug"] if altra else None
        dopo = [q for q in pagine if q["numero"] > destra]
        prima = [q for q in pagine if q["numero"] < sinistra]
        p["succ_doppia"] = dopo[0]["slug"] if dopo else None
        p["prec_doppia"] = prima[-1]["slug"] if prima else None
    # copertina e quarta stanno da sole, come nel libro chiuso
    pag_prima.update(compagna=None, prec_doppia=None, succ_doppia=pagine[1]["slug"])
    pag_quarta.update(compagna=None, succ_doppia=None, prec_doppia=pagine[-2]["slug"])
    for p in pagine[1:-1]:
        if p["prec_doppia"] in (None, ):
            p["prec_doppia"] = "copertina"

    # indice: sezioni con le loro pagine; sotto la Quarta Edizione le voci dell'indice originale
    per_hill = {int(p["hill"]): p for p in pagine if p["hill"]}
    p017 = next(p for p in pagine if p["tavola"] == "p017")
    _, corpo017 = leggi_md(RADICE / "testo" / "accessibile" / "p017.md")
    voci = indice_originale(corpo017.split("## Testo", 1)[1])
    sezioni = [{"titolo": "Copertina", "pagine": ["copertina"], "voci": []}]
    for s in web["sezioni"]:
        sp = [p["slug"] for p in pagine if p["sezione"] == s["titolo"]]
        voce = {"titolo": s["titolo"], "pagine": sp, "voci": []}
        if s.get("indice_originale"):
            voce["voci"] = [{"titolo": t, "hill": f"{n:05d}", "slug": per_hill[n]["slug"]}
                            for n, t in voci if n in per_hill]
        sezioni.append(voce)
    sezioni.append({"titolo": "Quarta di copertina", "pagine": ["quarta"], "voci": []})
    for p in pagine:   # voce dell'indice originale in cui cade la pagina (per il sottotitolo)
        if p["hill"] and int(p["hill"]) > 0:
            prima = [v for v in voci if v[0] <= int(p["hill"])]
            p["voce"] = prima[-1][1] if prima else None
        else:
            p["voce"] = None
    assert p017["slug"] == "00002"

    meta = leggi_yaml(RADICE / "libro" / "metadati.yaml")
    dati = {
        "libro": {"titolo": meta["titolo"], "sottotitolo": meta["sottotitolo"], "autore": meta["autore"],
                  "pagine": len(ordine), "presentazione": cop["quarta"].get("presentazione", ""),
                  "citazione": cop["quarta"].get("citazione", []),
                  "fonte_citazione": cop["quarta"].get("fonte_citazione", "")},
        "copertina": img_prima,
        "scarica": scaricabili(),
        "sezioni": sezioni,
        "pagine": pagine,
    }
    DATI.mkdir(parents=True, exist_ok=True)
    (DATI / "pagine.json").write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8")

    grossi = [f for f in PUBBLICO.rglob("*") if f.is_file() and f.stat().st_size > LIMITE]
    if grossi:
        sys.exit("File oltre i 25 MiB: " + ", ".join(str(f.relative_to(RADICE)) for f in grossi))
    print(f"{len(pagine)} pagine, {sum(1 for p in pagine if p['originale'])} con originale -> {DATI / 'pagine.json'}")


if __name__ == "__main__":
    main()
