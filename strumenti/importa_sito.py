#!/usr/bin/env python3
"""Converte le pagine HTML storiche del sito (storico/sito/html/N.html)
in file Markdown, uno per pagina, in testo/it/NN.md.

Uso:  python3 strumenti/importa_sito.py
"""
import re
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "storico" / "sito" / "html"
DESTINAZIONE = RADICE / "testo" / "it"


def contenuto(html: str) -> BeautifulSoup:
    pagina = BeautifulSoup(html, "lxml")
    for nav in pagina.select("div.cssnav"):
        nav.decompose()
    for img in pagina.find_all("img"):
        src = img.get("src", "")
        if "book-eris" in src or "downbtn" in src:
            img.decompose()
            continue
        nome = src.split("/")[-1]
        if "immagini/" in src:
            img["src"] = f"../../storico/immagini-it/{nome}"
        else:
            img["src"] = f"originale:{nome}"
    # le tabelle di impaginazione del vecchio sito diventano semplici blocchi
    for tag in pagina.find_all(["table", "tbody", "tr", "td", "center"]):
        tag.name = "div"
    return pagina


def pulisci(md: str) -> str:
    md = re.sub(r"all rights revers\w*.*?PrincipiaDiscordia\.com\)?", "", md, flags=re.I | re.S)
    md = md.replace("\xa0", " ")
    md = re.sub(r"[ \t]+\n", "\n", md)
    # i rientri fatti con &nbsp; diventerebbero blocchi di codice in Markdown
    md = re.sub(r"(?m)^[ \t]+", "", md)
    # righe vuote rimaste con il solo a-capo forzato
    md = re.sub(r"(?m)^\\$", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def main() -> None:
    DESTINAZIONE.mkdir(parents=True, exist_ok=True)
    pagine = sorted(SORGENTE.glob("*.html"), key=lambda p: int(p.stem))
    for p in pagine:
        n = int(p.stem)
        corpo = contenuto(p.read_text(encoding="utf-8", errors="replace"))
        titolo = corpo.find(class_="subheader")
        titolo = titolo.get_text(" ", strip=True) if titolo else ""
        md = markdownify(
            str(corpo.body or corpo),
            heading_style="ATX",
            newline_style="BACKSLASH",
            strip=["a"],
        )
        intestazione = (
            "---\n"
            f"pagina_sito: {n}\n"
            f"titolo: \"{titolo.replace(chr(34), chr(39))}\"\n"
            f"originale: http://www.principiadiscordia.com/book/{n}.php\n"
            "---\n\n"
        )
        (DESTINAZIONE / f"{n:02d}.md").write_text(intestazione + pulisci(md), encoding="utf-8")
    print(f"{len(pagine)} pagine convertite in {DESTINAZIONE}")


if __name__ == "__main__":
    main()
