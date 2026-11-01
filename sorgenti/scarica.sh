#!/bin/sh
# Scarica la scansione dell'edizione Loompanics (1980) da Wikimedia Commons.
# Il PDF resta fuori dal repository (vedi .gitignore): si rigenera con questo script.
set -e
cd "$(dirname "$0")"
URL="https://upload.wikimedia.org/wikipedia/commons/1/15/Principia_Discordia_(Loompanics_Unlimited_edition).pdf"
curl -fL -A "PrincipiaDiscordiaIT/0.1 (traduzione italiana)" -o loompanics.pdf "$URL"
echo "Scaricato: sorgenti/loompanics.pdf"
