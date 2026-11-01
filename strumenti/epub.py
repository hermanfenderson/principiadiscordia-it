#!/usr/bin/env python3
"""Costruisce l'EPUB 3 a impaginazione fissa, accessibile: una tavola per pagina.

Ogni pagina è un documento XHTML con l'immagine della tavola (alt breve) e, collegati con
aria-describedby, la descrizione e il testo della pagina presi da testo/accessibile/<tavola>.md,
nascosti alla vista ma letti dagli screen reader. Ci sono l'indice (con le voci dell'indice
originale di pagina 00002), la lista delle pagine del libro stampato, i punti di riferimento
e i metadati di accessibilità (schema.org). Si verifica con EPUBCheck e DAISY Ace.

Prima di lanciarlo servono le tavole e la copertina:
    python3 strumenti/libro.py --ricomponi
    python3 strumenti/copertina.py --pagine 114
Uso:
    python3 strumenti/epub.py            # -> build/epub/principia-discordia.epub
"""
import datetime as dt
import html
import io
import re
import uuid
import zipfile
from pathlib import Path

import markdown
import yaml
from PIL import Image

RADICE = Path(__file__).resolve().parent.parent
USCITA = RADICE / "build" / "epub"
LARGO, ALTO = 1160, 1874            # tela comune delle pagine (le tavole sono tutte circa 0,62)
QUALITA = 72
# identificatore stabile dell'edizione (non cambia a ogni build)
IDENTIFICATORE = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "principiadiscordia.hermanfenderson.com/epub"))

SEZIONI = {  # voci principali dell'indice: tavola -> titolo
    "frontespizio": "Frontespizio",
    "colophon-1": "Colophon",
    "pre-1": "Prefazione alla prefazione",
    "p005": "Prefazione alla nuova edizione Loompanics",
    "p007": "Contenuto di questa edizione",
    "p009": "Introduzione di Robert Anton Wilson",
    "p013": "Principia Discordia, Quarta Edizione",
    "p093": "Postfazione e intervista della Cabala Norton a Greg Hill",
    "p103": "Quinta Edizione",
    "p105": "Collage di Greg Hill",
    "ndt-1": "Note del traduttore",
    "fine-herman": "Chi (non) è Herman Fenderson",
}

CSS = """@charset "utf-8";
html, body { margin: 0; padding: 0; background: #fff; }
body { width: %dpx; height: %dpx; overflow: hidden; }
img.tavola { display: block; width: %dpx; height: %dpx; }
/* testo per gli screen reader: fuori dalla vista, ma presente nel documento */
.solo-lettori { position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%%); white-space: nowrap; }
""" % (LARGO, ALTO, LARGO, ALTO)


def leggi_accessibile(tavola: str) -> tuple[dict, str, str]:
    s = (RADICE / "testo" / "accessibile" / f"{tavola}.md").read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", s, re.S)
    testa, corpo = yaml.safe_load(m.group(1)), m.group(2)
    descr = corpo.split("## Descrizione", 1)[1].split("## Testo", 1)[0].strip()
    testo = corpo.split("## Testo", 1)[1].strip()
    return testa, descr, testo


def md_xhtml(t: str, livello: int = 3) -> str:
    """Markdown -> XHTML, con i titoli portati al livello voluto e xml:lang accanto a lang."""
    h = markdown.markdown(t, extensions=["tables", "sane_lists"], output_format="xhtml")
    h = re.sub(r"<(/?)h(\d)>", lambda m: f"<{m.group(1)}h{min(6, max(livello, int(m.group(2))))}>", h)
    h = re.sub(r'(<[^>]*?)\blang="([\w-]+)"', r'\1lang="\2" xml:lang="\2"', h)
    h = h.replace("&nbsp;", "&#160;")
    return h


def immagine(png: Path, nome: str, dest: Path) -> None:
    """La tavola centrata sulla tela comune, in scala di grigi, JPEG."""
    t = Image.open(png).convert("L")
    k = min(LARGO / t.width, ALTO / t.height)
    t = t.resize((round(t.width * k), round(t.height * k)), Image.LANCZOS)
    tela = Image.new("L", (LARGO, ALTO), 255)
    tela.paste(t, ((LARGO - t.width) // 2, (ALTO - t.height) // 2))
    tela.save(dest / nome, quality=QUALITA, optimize=True, progressive=False)


def xhtml(titolo: str, corpo: str, tipo: str = "") -> str:
    epub_type = f' epub:type="{tipo}"' if tipo else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="it" xml:lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width={LARGO}, height={ALTO}"/>
<title>{html.escape(titolo)}</title>
<link rel="stylesheet" type="text/css" href="../css/pagina.css"/>
</head>
<body{epub_type}>
{corpo}
</body>
</html>
"""


def main():
    ordine = yaml.safe_load((RADICE / "libro/ordine.yaml").read_text(encoding="utf-8"))["pagine"]
    meta = yaml.safe_load((RADICE / "libro/metadati.yaml").read_text(encoding="utf-8"))
    cop = yaml.safe_load((RADICE / "libro/copertina.yaml").read_text(encoding="utf-8"))
    lavoro = USCITA / "contenuto"
    import shutil
    shutil.rmtree(lavoro, ignore_errors=True)
    for d in ("xhtml", "img", "css"):
        (lavoro / "OEBPS" / d).mkdir(parents=True)
    oebps = lavoro / "OEBPS"
    (oebps / "css" / "pagina.css").write_text(CSS, encoding="utf-8")

    # ---- copertina: prima e quarta ritagliate dalla copertina stesa
    stesa = Image.open(RADICE / "build" / "copertina" / "copertina-ocra.png").convert("RGB")
    ab, pw, ph = round(0.125 * 300), round(148 / 25.4 * 300), round(210 / 25.4 * 300)
    dorso = stesa.width - 2 * ab - 2 * pw
    for nome, x0 in (("copertina.jpg", ab + pw + dorso), ("quarta.jpg", ab)):
        c = stesa.crop((x0, ab, x0 + pw, ab + ph))
        k = min(LARGO / c.width, ALTO / c.height)
        c = c.resize((round(c.width * k), round(c.height * k)), Image.LANCZOS)
        tela = Image.new("RGB", (LARGO, ALTO), (208, 146, 12))
        tela.paste(c, ((LARGO - c.width) // 2, (ALTO - c.height) // 2))
        tela.save(oebps / "img" / nome, quality=85, optimize=True)

    spine, manifest, pagine_lista, toc_voci = [], [], [], []

    def aggiungi(id_, href, mt, props=""):
        p = f' properties="{props}"' if props else ""
        manifest.append(f'<item id="{id_}" href="{href}" media-type="{mt}"{p}/>')

    # prima di copertina
    q = cop["quarta"]
    alt_cop = ("Copertina: Principia Discordia, ovvero Come trovai la Dea e Cosa le feci Quando la trovai. "
               "Edizione italiana, traduzione di Herman Fenderson.")
    corpo = (f'<img class="tavola" src="../img/copertina.jpg" alt="{html.escape(alt_cop)}" '
             f'aria-describedby="descr"/>\n<section id="descr" class="solo-lettori" aria-label="Descrizione della copertina">\n'
             "<p>Copertina color ocra. In alto «Sua Grande Narcoticità Malaclypse il Giovane», poi il titolo "
             "«Principia Discordia» in grandi lettere a riccioli, «ovvero» e il sottotitolo «Come trovai la Dea e Cosa "
             "le feci Quando la trovai»; sotto, «In cui è Spiegata Assolutamente Qualsiasi Cosa che Valga la Pena di "
             "Sapere A proposito Assolutamente di Tutto». In basso a sinistra una croce nera attraversata da due "
             "mezzelune; accanto «Edizione italiana, traduzione, prefazione alla prefazione e note di Herman "
             "Fenderson» e, sotto, una statua di donna distesa.</p>\n</section>")
    (oebps / "xhtml" / "copertina.xhtml").write_text(xhtml("Copertina", corpo, "cover"), encoding="utf-8")
    aggiungi("img-copertina", "img/copertina.jpg", "image/jpeg", "cover-image")
    aggiungi("copertina", "xhtml/copertina.xhtml", "application/xhtml+xml")
    spine.append('<itemref idref="copertina" properties="rendition:page-spread-center"/>')
    toc_voci.append(("copertina", "Copertina", []))

    # pagine del libro
    numero = 0
    indice_originale = {}
    for nome in ordine:
        numero += 1
        lato = "rendition:page-spread-right" if numero % 2 else "rendition:page-spread-left"
        pid = f"pag-{numero:03d}"
        href = f"xhtml/{pid}.xhtml"
        if nome == "bianca":
            corpo = f'<div role="doc-pagebreak" id="pb{numero}" aria-label="{numero}"></div>\n<p class="solo-lettori">Pagina bianca.</p>'
            (oebps / href).write_text(xhtml(f"Pagina {numero}", corpo), encoding="utf-8")
            aggiungi(pid, href, "application/xhtml+xml")
            spine.append(f'<itemref idref="{pid}" properties="{lato}"/>')
            pagine_lista.append((numero, href))
            continue
        testa, descr, testo = leggi_accessibile(nome)
        img = f"{nome}.jpg"
        immagine(RADICE / "build" / "tavole" / f"{nome}.png", img, oebps / "img")
        aggiungi(f"img-{nome}", f"img/{img}", "image/jpeg")
        orig = testa.get("pagina_originale")
        titolo = f"Pagina {orig}" if orig else SEZIONI.get(nome, f"Pagina {numero}")
        corpo = (
            f'<div role="doc-pagebreak" id="pb{numero}" aria-label="{numero}"></div>\n'
            f'<img class="tavola" src="../img/{img}" alt="{html.escape(testa["alt"])}" aria-describedby="testo-{nome}"/>\n'
            f'<section id="testo-{nome}" class="solo-lettori" aria-label="{html.escape(titolo)}">\n'
            f'<h2>Descrizione</h2>\n{md_xhtml(descr)}\n<h2>Testo della pagina</h2>\n{md_xhtml(testo)}\n</section>'
        )
        (oebps / href).write_text(xhtml(titolo, corpo, "frontmatter" if numero < 9 else ""), encoding="utf-8")
        aggiungi(pid, href, "application/xhtml+xml")
        spine.append(f'<itemref idref="{pid}" properties="{lato}"/>')
        pagine_lista.append((numero, href))
        if nome in SEZIONI:
            toc_voci.append((pid, SEZIONI[nome], []))
        if orig and not orig.startswith("-") and orig != "00000":
            indice_originale[int(orig)] = pid
        if nome == "p017":
            voci = re.findall(r"^(\d+) (.+?)\s*$", testo, re.M)
            sotto = [(n, t.replace("  ", "").strip()) for n, t in voci]

    # voci dell'indice originale sotto la Quarta Edizione
    for i, (pid, tit, figli) in enumerate(toc_voci):
        if tit.startswith("Principia Discordia, Quarta"):
            for n, t in sotto:
                if int(n) in indice_originale:
                    figli.append((indice_originale[int(n)], f"{t} ({int(n):05d})"))

    # quarta di copertina
    pres = " ".join(q["presentazione"].split())
    quarta_testo = (
        "<p>«" + html.escape(q["citazione"][0].lstrip("- ")) + "» «" + html.escape(q["citazione"][1].lstrip("- ")) +
        "» (" + html.escape(q["fonte_citazione"]) + ")</p>\n" +
        "".join(f"<p>{html.escape(' '.join(p.split()))}</p>\n" for p in q["presentazione"].split("\n\n")) +
        f"<p>{html.escape(q['didascalia'])}</p>\n" +
        "".join(f"<p>{html.escape(' '.join(p.split()))}</p>\n" for p in q["traduttore"].split("\n\n")) +
        "".join(f"<p>{html.escape(p)}</p>\n" for p in q["piede"]))
    corpo = (f'<img class="tavola" src="../img/quarta.jpg" alt="Quarta di copertina: citazione di Malaclypse, '
             f'presentazione del libro e nota sul traduttore con il disegno di uno struzzo." aria-describedby="testo-quarta"/>\n'
             f'<section id="testo-quarta" class="solo-lettori" aria-label="Quarta di copertina">\n{quarta_testo}</section>')
    (oebps / "xhtml" / "quarta.xhtml").write_text(xhtml("Quarta di copertina", corpo, "backmatter"), encoding="utf-8")
    aggiungi("img-quarta", "img/quarta.jpg", "image/jpeg")
    aggiungi("quarta", "xhtml/quarta.xhtml", "application/xhtml+xml")
    spine.append('<itemref idref="quarta" properties="rendition:page-spread-center"/>')
    toc_voci.append(("quarta", "Quarta di copertina", []))

    # ---- navigazione
    def li(pid, tit, figli):
        h = f'<li><a href="{"xhtml/" + pid + ".xhtml"}">{html.escape(tit)}</a>'
        if figli:
            h += "\n<ol>\n" + "\n".join(f'<li><a href="xhtml/{p}.xhtml">{html.escape(t)}</a></li>' for p, t in figli) + "\n</ol>"
        return h + "</li>"
    pid_bodymatter = next(p for p, t, _ in toc_voci if t.startswith("Principia Discordia, Quarta"))
    pid_front = next(p for p, t, _ in toc_voci if t == "Frontespizio")
    nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="it" xml:lang="it">
<head><meta charset="utf-8"/><title>Indice</title></head>
<body>
<nav epub:type="toc" id="toc" role="doc-toc" aria-labelledby="titolo-indice">
<h1 id="titolo-indice">Indice</h1>
<ol>
{chr(10).join(li(*v) for v in toc_voci)}
</ol>
</nav>
<nav epub:type="page-list" id="pagine" role="doc-pagelist" aria-labelledby="titolo-pagine" hidden="hidden">
<h2 id="titolo-pagine">Pagine</h2>
<ol>
{chr(10).join(f'<li><a href="{h}#pb{n}">{n}</a></li>' for n, h in pagine_lista)}
</ol>
</nav>
<nav epub:type="landmarks" id="riferimenti" aria-labelledby="titolo-riferimenti" hidden="hidden">
<h2 id="titolo-riferimenti">Punti di riferimento</h2>
<ol>
<li><a epub:type="cover" href="xhtml/copertina.xhtml">Copertina</a></li>
<li><a epub:type="titlepage" href="xhtml/{pid_front}.xhtml">Frontespizio</a></li>
<li><a epub:type="bodymatter" href="xhtml/{pid_bodymatter}.xhtml">Inizio del libro</a></li>
</ol>
</nav>
</body>
</html>
"""
    (oebps / "nav.xhtml").write_text(nav, encoding="utf-8")
    aggiungi("nav", "nav.xhtml", "application/xhtml+xml", "nav")
    aggiungi("css", "css/pagina.css", "text/css")

    # ---- metadati
    ora = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sommario = ("Edizione a impaginazione fissa che riproduce in facsimile le pagine del libro stampato. "
                "Ogni pagina ha un testo alternativo breve e, collegati all'immagine, una descrizione "
                "dell'immagine e il testo completo della pagina in ordine di lettura, con titoli, corsivi e "
                "lingue straniere marcate, leggibili con la sintesi vocale. Sono presenti l'indice, la lista "
                "delle pagine dell'edizione stampata e i punti di riferimento. L'aspetto visivo delle pagine "
                "(caratteri, impaginazione) non si può modificare.")
    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id" xml:lang="it"
  prefix="rendition: http://www.idpf.org/vocab/rendition/# a11y: http://www.idpf.org/epub/vocab/package/a11y/#">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="id">{IDENTIFICATORE}</dc:identifier>
<dc:title id="titolo">Principia Discordia</dc:title>
<meta refines="#titolo" property="title-type">main</meta>
<dc:title id="sottotitolo">Edizione italiana. Ovvero Come trovai la Dea e Cosa le feci Quando la trovai</dc:title>
<meta refines="#sottotitolo" property="title-type">subtitle</meta>
<dc:creator id="autore">Malaclypse il Giovane (Gregory Hill)</dc:creator>
<meta refines="#autore" property="role" scheme="marc:relators">aut</meta>
<dc:creator id="autore2">Lord Omar Khayyam Ravenhurst (Kerry Thornley)</dc:creator>
<meta refines="#autore2" property="role" scheme="marc:relators">aut</meta>
<dc:contributor id="traduttore">Herman Fenderson</dc:contributor>
<meta refines="#traduttore" property="role" scheme="marc:relators">trl</meta>
<dc:contributor id="wilson">Robert Anton Wilson</dc:contributor>
<meta refines="#wilson" property="role" scheme="marc:relators">aui</meta>
<dc:language>it</dc:language>
<dc:publisher>Herman Fenderson</dc:publisher>
<dc:date>2026</dc:date>
<dc:rights>Testo originale: (K) All Rites Reversed, Reprint What You Like. Traduzione italiana: Creative Commons Attribuzione - Condividi allo stesso modo 4.0 (CC BY-SA 4.0).</dc:rights>
<dc:source>Principia Discordia, Loompanics Unlimited, Port Townsend, 1980</dc:source>
<dc:description>{html.escape(' '.join(q['presentazione'].split()))}</dc:description>
<dc:subject>Discordianesimo</dc:subject>
<meta property="dcterms:modified">{ora}</meta>
<meta property="rendition:layout">pre-paginated</meta>
<meta property="rendition:orientation">portrait</meta>
<meta property="rendition:spread">landscape</meta>
<meta property="schema:accessMode">visual</meta>
<meta property="schema:accessMode">textual</meta>
<meta property="schema:accessModeSufficient">textual</meta>
<meta property="schema:accessModeSufficient">visual</meta>
<meta property="schema:accessModeSufficient">textual,visual</meta>
<meta property="schema:accessibilityFeature">alternativeText</meta>
<meta property="schema:accessibilityFeature">longDescription</meta>
<meta property="schema:accessibilityFeature">readingOrder</meta>
<meta property="schema:accessibilityFeature">structuralNavigation</meta>
<meta property="schema:accessibilityFeature">tableOfContents</meta>
<meta property="schema:accessibilityFeature">pageNavigation</meta>
<meta property="schema:accessibilityFeature">printPageNumbers</meta>
<meta property="schema:accessibilityHazard">none</meta>
<meta property="schema:accessibilitySummary">{sommario}</meta>
<meta property="pageBreakSource">urn:uuid:principia-discordia-it-a5-2026</meta>
</metadata>
<manifest>
{chr(10).join(manifest)}
</manifest>
<spine page-progression-direction="ltr">
{chr(10).join(spine)}
</spine>
</package>
"""
    (oebps / "content.opf").write_text(opf, encoding="utf-8")
    contenitore = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
"""
    (lavoro / "META-INF").mkdir(exist_ok=True)
    (lavoro / "META-INF" / "container.xml").write_text(contenitore, encoding="utf-8")

    epub = USCITA / "principia-discordia.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for f in sorted(lavoro.rglob("*")):
            if f.is_file():
                tipo = zipfile.ZIP_STORED if f.suffix == ".jpg" else zipfile.ZIP_DEFLATED
                z.write(f, f.relative_to(lavoro).as_posix(), compress_type=tipo)
    print(epub, f"{epub.stat().st_size / 2**20:.1f} MiB, {len(spine)} pagine")
    if epub.stat().st_size > 24 * 2**20:
        print("ATTENZIONE: vicino al limite di 25 MiB per file degli asset statici di Cloudflare: abbassare QUALITA")


if __name__ == "__main__":
    main()
