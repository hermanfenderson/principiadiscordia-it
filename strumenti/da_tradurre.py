#!/usr/bin/env python3
"""Prepara docs/da-tradurre.md: i testi dell'edizione Loompanics che mancano
nella traduzione italiana, paragrafo per paragrafo, con lo spazio per l'italiano.

Fonte: le trascrizioni riviste di Wikisource in testo/en/wikisource/pNNN.wiki;
per le pagine che Wikisource non ha ancora reso disponibili, testo/en/ocr/pNNN.txt.

Uso:  python3 strumenti/da_tradurre.py
"""
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
WIKI = RADICE / "testo" / "en" / "wikisource"
OCR = RADICE / "testo" / "en" / "ocr"


def da_wiki(testo: str) -> str:
    t = re.sub(r"<noinclude>.*?</noinclude>", "", testo, flags=re.S)
    t = re.sub(r"<ref>(.*?)</ref>", r" [nota: \1]", t, flags=re.S)
    t = t.replace("<nowiki>--</nowiki>", "--").replace("<nowiki>-</nowiki>", "-")
    t = re.sub(r"\{\{(?:c/s|c/e|nop)\}\}", "", t)
    t = re.sub(r"\{\{rule[^}]*\}\}", "---", t)
    t = re.sub(r"\{\{rh\|[^}]*\}\}", "", t)
    t = re.sub(r"\{\{SIC\|([^|}]*)(?:\|[^}]*)?\}\}", r"\1", t)
    for _ in range(3):  # modelli annidati: {{c|{{larger|...}}}}
        t = re.sub(r"\{\{(?:c|larger|x-larger|smaller)\|([^{}]*)\}\}", r"\1", t)
    t = re.sub(r"'''''(.*?)'''''", r"***\1***", t)
    t = re.sub(r"'''(.*?)'''", r"**\1**", t)
    t = re.sub(r"''(.*?)''", r"*\1*", t)
    t = re.sub(r"<u>(.*?)</u>", r"_\1_", t)
    t = t.replace("<sup>2</sup>", "²")
    t = re.sub(r"_ _", " ", t)  # parole sottolineate una per una: un'unica sottolineatura
    t = re.sub(r"<br\s*/?>", "  \n", t)
    t = re.sub(r"[ \t]+\n", lambda m: "  \n" if m.group(0).startswith("  ") else "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def paragrafi(testo: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", testo) if p.strip()]


def sezione(titolo: str, pagine: list[int], nota: str = "") -> list[str]:
    out = [f"## {titolo}", ""]
    if nota:
        out += [nota, ""]
    for p in pagine:
        wiki, ocr = WIKI / f"p{p:03d}.wiki", OCR / f"p{p:03d}.txt"
        if wiki.exists() and "noinclude" in wiki.read_text(encoding="utf-8"):
            testo, fonte = da_wiki(wiki.read_text(encoding="utf-8")), "Wikisource"
        else:
            testo, fonte = ocr.read_text(encoding="utf-8").strip(), "OCR corretto a mano"
        out += [f"### Pagina PDF {p} ({fonte})", ""]
        for par in paragrafi(testo):
            if par == "---":
                out += ["---", ""]
                continue
            out += ["> " + par.replace("\n", "\n> "), "", "**IT:** ", ""]
    return out


def main():
    L = [
        "# Testi da tradurre",
        "",
        "Testi dell'edizione Loompanics (1980) che non compaiono nella traduzione italiana.",
        "Ogni paragrafo inglese è seguito da una riga **IT:** da riempire. Le pagine PDF sono quelle di `sorgenti/loompanics.pdf` (vedi `docs/mappa-pagine.md`).",
        "",
        "Restano fuori: le citazioni di stampa sul retro (PDF 2, testi di terzi), il telegramma della Quinta edizione (PDF 104: è un modulo Western Union riempito di M, "un aum infinito" secondo Hill, senza testo da tradurre) e le pubblicità Loompanics (PDF 106-108).",
        "",
    ]
    L += sezione("1. Prefazione alla nuova edizione Loompanics", [5],
                 "Testo dell'editore. Va tradotto solo se si vuole riprodurre l'apparato dell'edizione Loompanics; per l'edizione italiana si può sostituire con una prefazione propria.")
    L += sezione("2. Indice di questa edizione", [7],
                 "Come sopra: è l'indice dell'edizione Loompanics, da adattare all'edizione italiana.")
    L += sezione("3. Postfazione speciale: intervista della Norton Cabal", list(range(93, 103)),
                 "Di Greg Hill (firmata Gypsie Skripto), San Francisco 1979. È il testo più lungo mancante: dieci pagine dattiloscritte.")
    L += sezione("4. Quinta edizione: frontespizio", [103])
    L += [
        "## 5. Frammenti rimasti in inglese nella traduzione esistente",
        "",
        "Righe che nel vecchio sito erano rimaste in inglese. Gli agenti che compongono le tavole ne hanno proposto una traduzione: è indicata sotto, da confermare.",
        "",
    ]
    L += (RADICE / "docs" / "frammenti.md").read_text(encoding="utf-8").strip().split("\n")
    (RADICE / "docs" / "da-tradurre.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("docs/da-tradurre.md")


if __name__ == "__main__":
    main()
