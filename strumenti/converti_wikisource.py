#!/usr/bin/env python3
"""Converte le trascrizioni di Wikisource (testo/en/wikisource/<tavola>.wiki) in Markdown.

Produce testo/en/pagine/<tavola>.md con nell'intestazione la pagina di Wikisource da cui viene
il testo, la revisione e la licenza (CC BY-SA 4.0, volontari di Wikisource). Il testo resta
quello della trascrizione: si traducono solo i template di impaginazione in Markdown/HTML.
I refusi segnati con {{SIC}} restano come nell'originale.

Uso:
    python3 strumenti/converti_wikisource.py
"""
import re
import urllib.parse
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
SORGENTI = RADICE / "testo" / "en" / "wikisource"
USCITA = RADICE / "testo" / "en" / "pagine"


def template(nome: str, argomenti: list[str]) -> str:
    """Il testo che resta di un template, senza parentesi graffe dentro."""
    nome = nome.strip().lower()
    posizionali = [a for a in argomenti if not re.match(r"^\s*[\w-]+\s*=", a)]
    if nome in ("c", "center", "larger", "smaller", "x-larger", "x-smaller", "big", "small", "sc"):
        return posizionali[0] if posizionali else ""
    if nome == "left margin":
        return posizionali[1] if len(posizionali) > 1 else ""
    if nome == "sic":
        return posizionali[0] if posizionali else ""        # la grafia dell'originale
    if nome == "fqm":
        return posizionali[0] if posizionali else "“"
    if nome == "rh":                                        # testatina: sinistra, centro, destra
        return "\n\n" + " · ".join(a.strip() for a in posizionali if a.strip()) + "\n\n"
    if nome == "rule":
        return "\n\n---\n\n"
    if nome in ("nop", "c/s", "c/e", "dhr", "gap"):
        return "\n\n" if nome != "gap" else " "
    raise SystemExit(f"Template sconosciuto: {{{{{nome}|...}}}}: aggiungilo a converti_wikisource.py")


def converti(w: str) -> tuple[str, list[str]]:
    w = re.sub(r"<noinclude>.*?</noinclude>", "", w, flags=re.S)
    w = w.replace("<nowiki>--</nowiki>", "--")
    w = re.sub(r"<nowiki>(.*?)</nowiki>", r"\1", w, flags=re.S)
    note = []

    def nota(m):
        note.append(m.group(1).strip())
        return f"<sup>[{len(note)}]</sup>"
    w = re.sub(r"<ref>(.*?)</ref>", nota, w, flags=re.S)
    # template, dal più interno
    interno = re.compile(r"\{\{([^{}|]+)((?:\|[^{}]*)?)\}\}")
    while interno.search(w):
        w = interno.sub(lambda m: template(m.group(1), m.group(2).split("|")[1:] if m.group(2) else []), w)
    # grassetti e corsivi
    w = re.sub(r"'''''(.+?)'''''", r"***\1***", w)
    w = re.sub(r"'''(.+?)'''", r"**\1**", w)
    w = re.sub(r"''(.+?)''", r"*\1*", w)
    w = w.replace("****", "")                               # due grassetti attaccati
    w = re.sub(r"\s*<br\s*/?>\s*\n?", "  \n", w)
    # righe vuote (anche fatte di soli spazi): al massimo una
    w = re.sub(r"\n[ \t]+\n", "\n\n", w)
    w = re.sub(r"[ \t]+\n\n", "\n\n", w)
    w = re.sub(r"\n{3,}", "\n\n", w).strip()
    return w, note


def main():
    revisioni = yaml.safe_load((SORGENTI / "revisioni.yaml").read_text(encoding="utf-8"))
    USCITA.mkdir(parents=True, exist_ok=True)
    fatti = 0
    for tavola, rev in revisioni.items():
        if not rev.get("trascrizione"):
            continue
        testo, note = converti((SORGENTI / f"{tavola}.wiki").read_text(encoding="utf-8"))
        if note:
            testo += "\n\n" + "\n\n".join(f"<sup>[{i}]</sup> {n}" for i, n in enumerate(note, 1))
        storia = ("https://en.wikisource.org/w/index.php?title="
                  + urllib.parse.quote(rev["titolo"].replace(" ", "_")) + "&action=history")
        testa = {
            "tavola": tavola,
            "fonte": rev["url"],
            "titolo_wikisource": rev["titolo"],
            "revisione": rev["revisione"],
            "data": rev["data"],
            "qualita": rev["qualita"],
            "cronologia": storia,
            "licenza": "CC BY-SA 4.0 (trascrizione dei volontari di Wikisource)",
        }
        (USCITA / f"{tavola}.md").write_text(
            "---\n" + yaml.safe_dump(testa, allow_unicode=True, sort_keys=False) + "---\n\n" + testo + "\n",
            encoding="utf-8")
        fatti += 1
    print(f"{fatti} pagine -> {USCITA.relative_to(RADICE)}")


if __name__ == "__main__":
    main()
