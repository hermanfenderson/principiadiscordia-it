#!/usr/bin/env python3
"""Genera le tavole di apertura del libro.

  tavole/frontespizio   pagina 1: titolo gotico e sottotitolo del frontespizio Loompanics,
                        più "edizione italiana" e il traduttore (testi in libro/copertina.yaml)
  tavole/copertina-bn   pagina 3: la prima di copertina in bianco e nero, cioè la tavola p013
                        senza le scritte tolte in copertina e con il timbro del traduttore

Uso:  python3 strumenti/pagine_apertura.py   (poi componi.py sulle due cartelle, o libro.py --ricomponi)
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
           "# Tavola nuova: frontespizio dell'edizione italiana (pagina 1 del libro)\n"
           "# Generata da strumenti/pagine_apertura.py: titolo gotico ritagliato dalla tavola p013\n"
           "# (tavole/apparato/titolo-gotico.png), sottotitolo nei caratteri di p013, testi da libro/copertina.yaml.\n"
           "# STATO: proposta\n\n",
           {
               "pagina_pdf": None,
               "immagini": [{"file": "tavole/apparato/titolo-gotico.png", "x": CENTRO - 610, "y": 640}],
               "testi": [
                   {"font": "Jost-Bold.ttf", "corpo": 46, "allinea": "centro", "x": CENTRO, "y": 860,
                    "righe": ["OVVERO"]},
                   {"font": "MysteryQuest-Regular.ttf", "corpo": 132, "grassetto": 1, "interlinea": 140,
                    "allinea": "centro", "x": CENTRO, "y": 1040,
                    "righe": ["Come trovai la Dea", "e Cosa le feci", "Quando la trovai"]},
                   {"font": "Jost-Bold.ttf", "corpo": 64, "allinea": "centro", "x": CENTRO, "y": 1600,
                    "righe": [f["edizione"]]},
                   {"font": "Jost-Regular.ttf", "corpo": 46, "allinea": "centro", "x": CENTRO, "y": 2180,
                    "righe": [f["traduzione"]]},
                   {"font": "Jost-Bold.ttf", "corpo": 60, "allinea": "centro", "x": CENTRO, "y": 2260,
                    "righe": [f["traduttore"]]},
               ],
               "linee": [[CENTRO - 160, 1440, CENTRO + 160, 1446]],
           })

    # ---- pagina 3: la prima di copertina, in bianco e nero
    p013 = yaml.safe_load((RADICE / "tavole" / "p013" / "tavola.yaml").read_text(encoding="utf-8"))
    togli = set(testi["prima"].get("togli", []))
    p013["testi"] = [el for el in p013["testi"] if not set(el.get("righe", [])) & togli]
    p013["testi"].append({"font": "Oswald-VF.ttf", "corpo": 74, "peso": 500, "effetto": "timbro",
                          "rotazione": -14, "x": 690, "y": 1700, "righe": [testi["prima"]["timbro"]]})
    scrivi("copertina-bn",
           "# Tavola nuova: la prima di copertina in bianco e nero (pagina 3 del libro)\n"
           "# Generata da strumenti/pagine_apertura.py a partire da tavole/p013: non modificarla a mano.\n"
           "# STATO: completa\n\n", p013)


if __name__ == "__main__":
    main()
