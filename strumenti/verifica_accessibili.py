#!/usr/bin/env python3
"""Controlla i testi accessibili di testo/accessibile/.

Per ogni tavola del libro (libro/ordine.yaml, pagine bianche escluse) verifica che:
- il file esista, con intestazione (tavola, alt) e le sezioni "## Descrizione" e "## Testo";
- l'alt non sia troppo lungo e cominci con il numero originale, se la pagina ne ha uno;
- pagina_originale sia giusto (pNNN con NNN 13-90: numerazione 000NN di Hill);
- il testo contenga le parole composte sulla tavola (copertura, in percentuale);
- i tag <span lang="..."> siano bilanciati.

Uso:  python3 strumenti/verifica_accessibili.py
"""
import re
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
CARTELLA = RADICE / "testo" / "accessibile"


def numero_originale(tavola: str) -> str | None:
    m = re.fullmatch(r"p(\d{3})", tavola)
    if not m:
        return None
    n = int(m.group(1)) - 15
    if -2 <= n <= 75 and int(m.group(1)) >= 13:
        return f"-{abs(n):05d}" if n < 0 else f"{n:05d}"
    return None


def parole(t: str) -> list[str]:
    t = re.sub(r"<[^>]+>", " ", t)
    return [w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ']{4,}", t)]


def parole_tavola(tavola: str) -> list[str]:
    spec = yaml.safe_load((RADICE / "tavole" / tavola / "tavola.yaml").read_text(encoding="utf-8"))
    righe = []
    for el in spec.get("testi", []):
        righe += el.get("righe", [])
        if el.get("testo"):  # blocchi di testo a capo automatico (chiave "testo" con "colonne")
            righe.append(el["testo"])
    t = " ".join(re.sub(r"[  ​]", "", r) for r in righe)
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)  # a capo col trattino
    return parole(t)


def main():
    ordine = [p for p in yaml.safe_load((RADICE / "libro/ordine.yaml").read_text(encoding="utf-8"))["pagine"]
              if p != "bianca"]
    problemi, coperture = [], []
    for t in ordine:
        f = CARTELLA / f"{t}.md"
        if not f.exists():
            problemi.append((t, "manca il file"))
            continue
        s = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", s, re.S)
        if not m:
            problemi.append((t, "intestazione mancante"))
            continue
        testa, corpo = yaml.safe_load(m.group(1)), m.group(2)
        if testa.get("tavola") != t:
            problemi.append((t, f"tavola nell'intestazione: {testa.get('tavola')}"))
        alt = testa.get("alt", "")
        if not alt:
            problemi.append((t, "alt vuoto"))
        elif len(alt) > 260:
            problemi.append((t, f"alt lungo ({len(alt)} caratteri)"))
        num = numero_originale(t)
        if str(testa.get("pagina_originale") or "") != (num or ""):
            problemi.append((t, f"pagina_originale {testa.get('pagina_originale')!r}, atteso {num!r}"))
        if num and not alt.startswith(f"Pagina {num}"):
            problemi.append((t, "l'alt non comincia con il numero di pagina"))
        for sez in ("## Descrizione", "## Testo"):
            if sez not in corpo:
                problemi.append((t, f"manca {sez}"))
        if corpo.count("<span") != corpo.count("</span>"):
            problemi.append((t, "tag <span> non bilanciati"))
        testo = corpo.split("## Testo", 1)[-1]
        nel_md = set(parole(testo.replace("*", "")))
        attese = parole_tavola(t)
        if attese:
            presenti = sum(w in nel_md for w in attese)
            c = presenti / len(attese)
            coperture.append((c, t, sorted({w for w in attese if w not in nel_md})[:12]))
    print(f"{len(ordine)} pagine, {len(problemi)} problemi")
    for p in problemi:
        print("  ", *p)
    print("pagine con copertura delle parole della tavola sotto il 97%:")
    for c, t, mancanti in sorted(coperture):
        if c < 0.97:
            print(f"   {t}: {c:.0%}  mancano: {' '.join(mancanti)}")


if __name__ == "__main__":
    main()
