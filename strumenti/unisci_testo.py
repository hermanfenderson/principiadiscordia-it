#!/usr/bin/env python3
"""Riunisce testo/it/*.md in un unico file, nell'ordine del libro.

Uso:  python3 strumenti/unisci_testo.py   ->  docs/testo-italiano.md
"""
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
TESTO = RADICE / "testo" / "it"

# file del vecchio sito -> (pagina PDF Loompanics, numerazione originale)
ORDINE = [(1, 9, "Introduzione di R.A. Wilson, 1"), (2, 10, "Introduzione di R.A. Wilson, 2"),
          (3, 11, "Introduzione di R.A. Wilson, 3"), (5, 13, "Frontespizio"),
          (6, 14, "Intervista a Malaclypse il Giovane"), (7, 15, "Frontespizio della IV edizione")]
ORDINE += [(n, n + 8, f"000{n - 7:02d}") for n in range(8, 83)]
ORDINE += [(83, 91, "Società Discordiana"), (84, 92, "Le parole degli Illuminati")]


def corpo(file: Path) -> tuple[str, str]:
    testo = file.read_text(encoding="utf-8")
    titolo = re.search(r'^titolo: "(.*)"$', testo, re.M)
    testo = testo.split("---", 2)[2]
    testo = re.sub(r"!\[[^\]]*\]\(([^)]*)\)", lambda m: f"[immagine: {m.group(1).split('/')[-1].split(':')[-1]}]", testo)
    testo = re.sub(r"\\\n", "  \n", testo)
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return (titolo.group(1).strip(" -") if titolo else ""), testo.strip()


def main():
    L = ["# Principia Discordia — testo italiano", "",
         "La traduzione di Herman Fenderson com'è oggi in `testo/it/`, riunita in un unico file nell'ordine del libro (edizione Loompanics).",
         "Ogni sezione indica la pagina originale, la pagina del PDF e il file da cui viene. Le immagini sono indicate col nome del file.",
         "Questo file si rigenera con `python3 strumenti/unisci_testo.py`: le correzioni vanno fatte nei file di `testo/it/`.", ""]
    for n, pdf, etichetta in ORDINE:
        titolo, testo = corpo(TESTO / f"{n:02d}.md")
        intestazione = f"## {etichetta}" + (f" — {titolo}" if titolo and not etichetta.startswith(("Intro", "Front")) else "")
        L += ["---", "", intestazione, "", f"*PDF {pdf} · `testo/it/{n:02d}.md`*", "", testo or "*(solo illustrazione)*", ""]
    (RADICE / "docs" / "testo-italiano.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("docs/testo-italiano.md")


if __name__ == "__main__":
    main()
