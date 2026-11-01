#!/usr/bin/env python3
"""Prepara le bozze dei testi accessibili: per ogni tavola del libro, le righe di testo
composte (dal tavola.yaml), ordinate dall'alto in basso e da sinistra a destra, ripulite
degli spazi sottili di giustificazione e con gli a capo col trattino ricuciti.

Le bozze (build/accessibile-bozze/<tavola>.txt) servono solo come punto di partenza per
scrivere a mano testo/accessibile/<tavola>.md, guardando la tavola: l'ordine di lettura
delle pagine a collage e le scritte rimaste dalla scansione vanno sistemati a occhio.

Uso:  python3 strumenti/bozze_accessibili.py [tavola ...]
"""
import re
import sys
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
USCITA = RADICE / "build" / "accessibile-bozze"


def pulisci(riga: str) -> str:
    return re.sub(r"[  ​]", "", riga).replace("\x01", " ")


def bozza(nome: str) -> str:
    spec = yaml.safe_load((RADICE / "tavole" / nome / "tavola.yaml").read_text(encoding="utf-8"))
    corsivi = ("Italic", "Oblique", "Corsivo")
    elementi = []
    for el in spec.get("testi", []):
        righe = [pulisci(r) for r in el.get("righe", [])]
        if el.get("testo"):  # blocchi a capo automatico: un capoverso per riga vuota
            righe += [pulisci(c) for c in str(el["testo"]).split("\n")]
        if any(c in el.get("font", "") for c in corsivi) and len(righe) == 1 and righe[0].strip():
            righe = [f"*{righe[0].strip()}*"]
        elementi.append((el.get("y", 0), el.get("x", 0), el.get("rotazione", 0), righe, el.get("allinea", "sinistra")))
    elementi.sort(key=lambda e: (round(e[0] / 25), e[1]))  # stessa riga di base: da sinistra a destra
    # margine sinistro più frequente: una riga che parte più a destra apre un capoverso
    from collections import Counter
    xs = Counter(round(e[1] / 10) * 10 for e in elementi if not e[2] and e[4] == "sinistra")
    sinistra = xs.most_common(1)[0][0] if xs else 0
    out, testo = [], ""
    ultimo_y = None
    for y, x, rot, righe, allinea in elementi:
        nuova_riga = ultimo_y is None or abs(y - ultimo_y) > 12
        if ultimo_y is not None and (y - ultimo_y > 100 or (nuova_riga and allinea == "sinistra" and sinistra + 30 < x < sinistra + 150)):
            out.append(testo)
            testo = ""
        for r in righe:
            r = r.strip()
            if not r:
                out.append(testo)
                testo = ""
                continue
            if testo.endswith("-") and not testo.endswith(" -") and not testo.endswith("--"):
                testo = testo[:-1] + r
            elif r[:1] in ",.;:!?)" and not nuova_riga:
                testo += r
            else:
                testo = f"{testo} {r}".strip()
        if rot:
            testo += f"   [ruotato {rot}°]"
        ultimo_y = y
    out.append(testo)
    return "\n\n".join(t for t in out if t)


def main():
    import yaml as _y
    ordine = [p for p in _y.safe_load((RADICE / "libro/ordine.yaml").read_text(encoding="utf-8"))["pagine"] if p != "bianca"]
    nomi = sys.argv[1:] or ordine
    USCITA.mkdir(parents=True, exist_ok=True)
    for n in nomi:
        (USCITA / f"{n}.txt").write_text(bozza(n), encoding="utf-8")
    print(USCITA, len(nomi), "bozze")


if __name__ == "__main__":
    main()
