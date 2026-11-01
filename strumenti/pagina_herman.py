#!/usr/bin/env python3
"""Compone la pagina "Chi (non) è Herman Fenderson" da testo/it/apparato/chi-non-e-herman-fenderson.md.

Struzzo di pagina 00010 in alto, didascalia a mano, bio dattiloscritta sotto.
Uso:  python3 strumenti/pagina_herman.py   (poi  python3 strumenti/componi.py tavole/fine-herman)
"""
import re
import sys
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "strumenti"))
from impagina import a_capo, dattilo  # noqa: E402


def main():
    t = (RADICE / "testo/it/apparato/chi-non-e-herman-fenderson.md").read_text(encoding="utf-8")
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)
    pars = [dattilo(p.strip()) for p in re.split(r"\n\s*\n", t) if p.strip()]
    titolo = pars[0]
    didascalia = pars[1].split("\n", 1)[1].strip()
    righe = []
    for p in pars[2:]:
        righe += [r.replace("\x01", " ") for r in a_capo("\x01" * 5 + " ".join(p.split()), 62)]
        righe.append("")
    righe.pop()
    spec = {
        "pagina_pdf": None,
        "immagini": [{"file": "tavole/apparato/struzzo-00010.png", "x": 463, "y": 320, "larghezza": 900}],
        "testi": [
            {"font": "IBMPlexMono-Medium.ttf", "corpo": 52, "x": 913, "y": 240, "allinea": "centro",
             "righe": [titolo], "sottolineato": True, "distanza_sottolineatura": 9, "spessore_sottolineatura": 6},
            {"font": "Kalam-Bold.ttf", "corpo": 50, "x": 913, "y": 955, "allinea": "centro", "rotazione": -1.5,
             "adatta": 1450, "righe": [didascalia]},
            {"font": "IBMPlexMono-Medium.ttf", "corpo": 42, "interlinea": 47, "x": 227, "y": 1060, "righe": righe},
        ],
    }
    testa = ("# Tavola nuova: Chi (non) è Herman Fenderson, ultima pagina del libro\n"
             "# Generata da strumenti/pagina_herman.py a partire da testo/it/apparato/chi-non-e-herman-fenderson.md;\n"
             "# struzzo da pagina 00010 (PDF 25). Il \"WOW!\" dello struzzo resta in inglese, come in pagina 00010.\n"
             "# STATO: completa\n\n")
    out = RADICE / "tavole/fine-herman/tavola.yaml"
    out.write_text(testa + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    ultima = 1060 + (len(righe) - 1) * 47
    print(out, f"{len(righe)} righe, ultima linea di base a y={ultima}")


if __name__ == "__main__":
    main()
