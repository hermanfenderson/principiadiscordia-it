#!/usr/bin/env python3
"""Scarica da Wikisource le trascrizioni inglesi della scansione Loompanics.

Pagine «Page:Principia_Discordia_(Loompanics_Unlimited_edition).pdf/N», per le tavole pNNN.
Con calma: una richiesta alla volta (20 pagine per richiesta), pause tra le richieste,
User-Agent che identifica il progetto, maxlag, e rispetto di Retry-After se Wikimedia rallenta.

Salva il wikitesto in testo/en/wikisource/<tavola>.wiki (senza toccare i file già presenti e
identici) e revisione, data e livello di rilettura in testo/en/wikisource/revisioni.yaml.
Poi strumenti/converti_wikisource.py produce testo/en/pagine/<tavola>.md.

Uso:
    python3 strumenti/scarica_wikisource.py            # tutte le tavole pNNN mancanti
    python3 strumenti/scarica_wikisource.py --tutte    # anche quelle già scaricate
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
CARTELLA = RADICE / "testo" / "en" / "wikisource"
REVISIONI = CARTELLA / "revisioni.yaml"
API = "https://en.wikisource.org/w/api.php"
TITOLO = "Page:Principia Discordia (Loompanics Unlimited edition).pdf/{n}"
USER_AGENT = ("PrincipiaDiscordiaIT/1.0 (https://github.com/hermanfenderson/principiadiscordia-it; "
              "edizione italiana dei Principia Discordia, testo a fronte) python-urllib")
PER_RICHIESTA = 20
PAUSA = 6


def richiesta(parametri: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(parametri)
    for tentativo in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dati = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                attesa = int(e.headers.get("Retry-After", "30"))
                print(f"  Wikimedia chiede di aspettare {attesa} s")
                time.sleep(attesa)
                continue
            raise
        if dati.get("error", {}).get("code") == "maxlag":
            print("  server carico (maxlag): aspetto")
            time.sleep(10 * (tentativo + 1))
            continue
        return dati
    raise SystemExit("Wikimedia non risponde: riprova più tardi")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tutte", action="store_true")
    args = ap.parse_args()
    tavole = sorted(p.name for p in (RADICE / "tavole").iterdir() if p.name.startswith("p") and p.name[1:].isdigit())
    tavole = [t for t in tavole if t != "p001"]          # la copertina non è nel libro
    revisioni = yaml.safe_load(REVISIONI.read_text(encoding="utf-8")) if REVISIONI.exists() else {}
    da_fare = [t for t in tavole if args.tutte or t not in revisioni]
    print(f"{len(da_fare)} pagine da chiedere a Wikisource")

    for i in range(0, len(da_fare), PER_RICHIESTA):
        gruppo = da_fare[i:i + PER_RICHIESTA]
        titoli = {TITOLO.format(n=int(t[1:])): t for t in gruppo}
        dati = richiesta({
            "action": "query", "format": "json", "formatversion": "2", "maxlag": "5",
            "prop": "revisions", "rvprop": "ids|timestamp|content", "rvslots": "main",
            "titles": "|".join(titoli),
        })
        for pagina in dati["query"]["pages"]:
            tavola = titoli[pagina["title"]]
            if pagina.get("missing"):
                print(f"  {tavola}: nessuna trascrizione su Wikisource")
                revisioni[tavola] = {"trascrizione": False}
                continue
            rev = pagina["revisions"][0]
            testo = rev["slots"]["main"]["content"]
            qualita = None
            if 'pagequality level="' in testo:
                qualita = int(testo.split('pagequality level="', 1)[1][0])
            dest = CARTELLA / f"{tavola}.wiki"
            if not (dest.exists() and dest.read_text(encoding="utf-8") == testo):
                if dest.exists():
                    dest.chmod(0o644)
                    print(f"  {tavola}: aggiornato rispetto alla copia nel repository")
                dest.write_text(testo, encoding="utf-8")
            revisioni[tavola] = {
                "trascrizione": True,
                "titolo": pagina["title"],
                "url": "https://en.wikisource.org/wiki/" + urllib.parse.quote(pagina["title"].replace(" ", "_")),
                "revisione": rev["revid"],
                "data": rev["timestamp"],
                "qualita": qualita,   # 0 senza testo, 1 non riletta, 2 problematica, 3 riletta, 4 convalidata
            }
            print(f"  {tavola}: revisione {rev['revid']}, qualità {qualita}")
        REVISIONI.write_text("# Revisioni delle pagine di Wikisource scaricate (strumenti/scarica_wikisource.py)\n"
                             + yaml.safe_dump(dict(sorted(revisioni.items())), allow_unicode=True, sort_keys=False),
                             encoding="utf-8")
        if i + PER_RICHIESTA < len(da_fare):
            time.sleep(PAUSA)


if __name__ == "__main__":
    main()
