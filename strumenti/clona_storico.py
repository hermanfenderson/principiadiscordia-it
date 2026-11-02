#!/usr/bin/env python3
"""Clone statico del vecchio sito sotto /storico/, con i redirect dei vecchi indirizzi .php.

Legge storico/ (che non si modifica): le 86 pagine HTML convertite dal PHP, bookstyle.css e le
tavole italiane (storico/immagini-it/). Le risorse che nel repository mancavano (pulsanti,
book-eris.gif, le immagini inglesi in images/) si scaricano una volta dal vecchio sito, con calma,
in sorgenti/vecchio-sito/, che sta in git: così il clone si rifà anche quando il vecchio sito
non ci sarà più.

Produce:
  sito/public/storico/              libro/<N>/index.html, immagini, CSS (/storico/ porta a libro/0/)
  sito/public/_redirects            /libro/<N>.php e /index.php -> pagine del clone (301)

Uso:
    python3 strumenti/clona_storico.py              # scarica solo ciò che manca, poi genera
    python3 strumenti/clona_storico.py --non-scaricare
"""
import argparse
import re
import shutil
import time
import urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
STORICO = RADICE / "storico"
CACHE = RADICE / "sorgenti" / "vecchio-sito"
USCITA = RADICE / "sito" / "public" / "storico"
REDIRECTS = RADICE / "sito" / "public" / "_redirects"
VECCHIO = "http://principiadiscordia.hermanfenderson.com/libro/"
USER_AGENT = ("PrincipiaDiscordiaIT/1.0 (https://github.com/hermanfenderson/principiadiscordia-it; "
              "clone statico del vecchio sito)")
PAUSA = 1.5

AVVISO = """<div lang="it" style="font-family: Verdana, Helvetica, Arial, sans-serif; font-size: 13px; line-height: 1.5; background: #141210; color: #fbf7ec; padding: 8px 12px; margin: 0 0 10px;">
Questo è il <strong>vecchio sito</strong> della traduzione, conservato com'era.
La traduzione completa, pagina per pagina in facsimile, è nella
<a href="/" style="color: #f1e18d; text-decoration: underline;">nuova edizione italiana dei Principia Discordia</a>{nuova}.
</div>
"""


def risorse(pagine: list[str]) -> set[str]:
    usate = set()
    for h in pagine:
        usate |= {m for m in re.findall(r'(?i)src="([^"]+)"', h) if not m.startswith("http")}
    usate.add("overbtn.jpg")       # sfondo dei pulsanti, citato in bookstyle.css
    return usate


def scarica(nomi: list[str]) -> None:
    for i, nome in enumerate(nomi):
        dest = CACHE / nome
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(VECCHIO + nome, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            print(f"  scaricato {nome}")
        except urllib.error.HTTPError as e:
            print(f"  MANCA sul vecchio sito: {nome} ({e.code})")
        if i + 1 < len(nomi):
            time.sleep(PAUSA)


def corrispondenze() -> dict[int, str]:
    """Pagina N del vecchio sito -> indirizzo della pagina corrispondente nella nuova edizione.

    Dai commenti «Pagina del vecchio sito: N» nelle tavole (la prima tavola che la cita)."""
    import yaml
    web = yaml.safe_load((RADICE / "libro" / "pagine-web.yaml").read_text(encoding="utf-8"))["indirizzi"]
    mappa = {}
    for t in sorted((RADICE / "tavole").glob("*/tavola.yaml")):
        tavola = t.parent.name
        m = re.search(r"Pagina del vecchio sito:\s*([\d ,e+-]+)", t.read_text(encoding="utf-8"))
        if not m:
            continue
        acc = RADICE / "testo" / "accessibile" / f"{tavola}.md"
        if not acc.exists():
            continue
        hill = re.search(r'^pagina_originale:\s*"([^"]+)"', acc.read_text(encoding="utf-8"), re.M)
        indirizzo = hill.group(1) if hill else web.get(tavola)
        if not indirizzo:
            continue
        for n in re.findall(r"\d+", m.group(1)):
            mappa.setdefault(int(n), indirizzo)
    return mappa


def riscrivi(h: str, n: int, nuova: str | None) -> str:
    h = re.sub(r'href="(\d+)\.php"', r'href="/storico/libro/\1/"', h)
    h = h.replace('href="../index.php"', 'href="/"')   # «Chiudi il libro»: alla home del sito nuovo
    h = re.sub(r'(?i)(src=")(?!http)([^"]+)"', r'\1/storico/libro/\2"', h)
    h = re.sub(r'(?i)HREF="bookstyle\.css"', 'HREF="/storico/libro/bookstyle.css"', h)
    h = re.sub(r"window\.location\.href = \"(\d+)\.php\"", r'window.location.href = "/storico/libro/\1/"', h)
    # lingua del documento e titolo che dica che è il vecchio sito
    h = h.replace("<html>", '<html lang="it">', 1)
    h = re.sub(r"<title>(.*?)</title>", r"<title>\1 (vecchio sito)</title>", h, count=1)
    link = f' (questa pagina: <a href="/libro/{nuova}/" style="color: #f1e18d; text-decoration: underline;">pagina {nuova}</a>)' \
        if nuova and re.fullmatch(r"-?\d{5}", nuova) else \
        (f' (<a href="/libro/{nuova}/" style="color: #f1e18d; text-decoration: underline;">questa pagina nella nuova edizione</a>)' if nuova else "")
    h = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + AVVISO.format(nuova=link), h, count=1)
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--non-scaricare", action="store_true")
    args = ap.parse_args()

    pagine = {int(p.stem): p.read_text(encoding="utf-8") for p in (STORICO / "sito" / "html").glob("*.html")}
    usate = risorse(list(pagine.values()))
    da_scaricare = sorted(r for r in usate
                          if not r.startswith("immagini/") and not (CACHE / r).exists())
    if da_scaricare and not args.non_scaricare:
        print(f"{len(da_scaricare)} risorse da scaricare dal vecchio sito")
        scarica(da_scaricare)

    shutil.rmtree(USCITA, ignore_errors=True)
    libro = USCITA / "libro"
    (libro / "immagini").mkdir(parents=True)
    shutil.copy2(STORICO / "sito" / "bookstyle.css", libro / "bookstyle.css")
    mancanti = []
    for r in sorted(usate):
        if r.startswith("immagini/"):
            src = STORICO / "immagini-it" / r.split("/", 1)[1]
        else:
            src = CACHE / r
        if not src.exists():
            mancanti.append(r)
            continue
        (libro / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, libro / r)

    nuove = corrispondenze()
    for n, h in sorted(pagine.items()):
        dest = libro / str(n) / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(riscrivi(h, n, nuove.get(n)), encoding="utf-8")

    righe = ["# Vecchi indirizzi del sito PHP (generato da strumenti/clona_storico.py): verso il clone storico",
             "/index.php /storico/libro/0/ 301",
             "/storico /storico/libro/0/ 301",
             "/storico/ /storico/libro/0/ 301"]
    righe += [f"/libro/{n}.php /storico/libro/{n}/ 301" for n in sorted(pagine)]
    REDIRECTS.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print(f"{len(pagine)} pagine -> {USCITA.relative_to(RADICE)}, {len(righe) - 1} redirect")
    if mancanti:
        print("Risorse che mancano ancora:", ", ".join(mancanti))


if __name__ == "__main__":
    main()
