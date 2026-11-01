#!/usr/bin/env python3
"""Genera le tavole di apertura del libro.

  tavole/occhiello      pagina 1: solo autore e titolo (lettering della copertina Loompanics), a un terzo dell'altezza
  tavole/frontespizio   pagina 3: autore, titolo e sottotitolo nel carattere a riccioli di p013,
                        più "edizione italiana" e il traduttore (testi in libro/copertina.yaml)

Uso:  python3 strumenti/pagine_apertura.py   (poi componi.py sulle cartelle, o libro.py --ricomponi)
"""
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
LARGO = 1827  # pagina nuova, come in componi.py
CENTRO = LARGO // 2


def scrivi(nome: str, testa: str, spec: dict):
    cartella = RADICE / "tavole" / nome
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "tavola.yaml").write_text(
        testa + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")


def main():
    testi = yaml.safe_load((RADICE / "libro" / "copertina.yaml").read_text(encoding="utf-8"))
    f = testi["frontespizio"]

    # ---- pagina 1: frontespizio italiano
    scrivi("frontespizio",
           "# Tavola nuova: frontespizio dell'edizione italiana (pagina 3 del libro)\n"
           "# Generata da strumenti/pagine_apertura.py: titolo e sottotitolo nel carattere a riccioli di p013,\n"
           "# testi da libro/copertina.yaml.\n"
           "# STATO: proposta\n\n",
           {
               "pagina_pdf": None,
               "testi": [
                   {"font": "Jost-Bold.ttf", "corpo": 60, "allinea": "centro", "x": CENTRO, "y": 500,
                    "righe": [f["autore"]]},
                   # titolo nel carattere a riccioli del sottotitolo (MysteryQuest, come in p013)
                   {"font": "MysteryQuest-Regular.ttf", "corpo": 190, "grassetto": 1, "interlinea": 185,
                    "allinea": "centro", "x": CENTRO, "y": 780, "righe": ["Principia", "Discordia"]},
                   {"font": "Jost-Bold.ttf", "corpo": 46, "allinea": "centro", "x": CENTRO, "y": 1110,
                    "righe": ["OVVERO"]},
                   {"font": "MysteryQuest-Regular.ttf", "corpo": 112, "grassetto": 1, "interlinea": 120,
                    "allinea": "centro", "x": CENTRO, "y": 1260,
                    "righe": ["Come trovai la Dea", "e Cosa le feci", "Quando la trovai"]},
                   {"font": "Jost-Bold.ttf", "corpo": 64, "allinea": "centro", "x": CENTRO, "y": 1750,
                    "righe": [f["edizione"]]},
                   {"font": "Jost-Regular.ttf", "corpo": 46, "allinea": "centro", "x": CENTRO, "y": 2180,
                    "righe": [f["traduzione"]]},
                   {"font": "Jost-Bold.ttf", "corpo": 60, "allinea": "centro", "x": CENTRO, "y": 2260,
                    "righe": [f["traduttore"]]},
               ],
               "linee": [[CENTRO - 160, 1610, CENTRO + 160, 1616]],
           })

    # ---- pagina 1: occhiello, solo autore e titolo a un terzo dell'altezza
    scrivi("occhiello",
           "# Tavola nuova: occhiello (pagina 1 del libro), autore e titolo a un terzo dell'altezza\n"
           "# Generata da strumenti/pagine_apertura.py: non modificarla a mano.\n"
           "# STATO: proposta\n\n",
           {
               "pagina_pdf": None,
               "testi": [{"font": "Jost-Bold.ttf", "corpo": 52, "allinea": "centro", "x": CENTRO, "y": 860,
                          "righe": [f["autore"]]}],
               # il titolo disegnato a mano della copertina Loompanics (ritagliato da p001)
               "immagini": [{"file": "tavole/apparato/titolo-loompanics.png", "x": CENTRO - 500, "y": 930,
                             "larghezza": 1000}],
           })

if __name__ == "__main__":
    main()
