#!/usr/bin/env bash
# Scarica, verifica (SHA-256) ed estrae il portabile Windows x64 di ogni app Craft, una alla volta.
# Uso: installa_suite.sh <cartella_base>   (es. la radice del repository craft-regia)
set -u
BASE="$1"
APP_DIR="$BASE/app"
ZIP_DIR="$BASE/scaricati"
mkdir -p "$APP_DIR" "$ZIP_DIR"
LOG="$BASE/installazione.log"
: > "$LOG"

APPS="photocraft:v0.15.1 lightcraft:v0.13.0 filmcraft:v0.12.0 designcraft:v0.12.0 vectorcraft:v0.16.0 pdfcraft:v0.13.0 effectcraft:v0.16.0 wordcraft:v0.10.0 deckcraft:v0.10.0 gridcraft:v0.11.1 cadcraft:v0.12.0 soundcraft:v0.12.1 figcraft:v0.10.0"

for item in $APPS; do
  app=${item%%:*}; tag=${item##*:}; ver=${tag#v}
  zip="$app-$ver-windows-x64-portable.zip"
  url="https://github.com/storytold/$app/releases/download/$tag"
  d="$ZIP_DIR/$app"; mkdir -p "$d"
  t0=$(date +%s)
  if ! curl -sSfL -A Photocraft-dev -o "$d/SHA256SUMS.txt" "$url/SHA256SUMS.txt" || ! curl -sSfL -A Photocraft-dev -o "$d/$zip" "$url/$zip"; then
    echo "$app	$ver	ERRORE_DOWNLOAD" | tee -a "$LOG"; continue
  fi
  atteso=$(grep -F " $zip" "$d/SHA256SUMS.txt" | grep -v '\.sig' | head -1 | cut -d' ' -f1)
  reale=$(sha256sum "$d/$zip" | cut -d' ' -f1)
  if [ -z "$atteso" ] || [ "$atteso" != "$reale" ]; then
    echo "$app	$ver	SHA_NON_CORRISPONDE atteso=$atteso reale=$reale" | tee -a "$LOG"; continue
  fi
  dest="$APP_DIR/$app-$ver"
  rm -rf "$dest.tmp"; mkdir -p "$dest.tmp"
  unzip -q "$d/$zip" -d "$dest.tmp"
  # il contenuto sta in una sottocartella: la porto al livello di $dest
  inner=$(find "$dest.tmp" -mindepth 1 -maxdepth 1 -type d | head -1)
  if [ -n "$inner" ] && [ "$(find "$dest.tmp" -mindepth 1 -maxdepth 1 | wc -l)" = "1" ]; then
    mv "$inner" "$dest"; rmdir "$dest.tmp"
  else
    mv "$dest.tmp" "$dest"
  fi
  cli="$dest/$app-cli.exe"
  if [ -f "$cli" ]; then
    mcp=$("$cli" --help 2>&1 | grep -c -E '^\s+[a-z-]+-cli mcp|  .*cli mcp')
    ncmd=$("$cli" commands 2>/dev/null | wc -l)
  else
    mcp="-"; ncmd="-"
  fi
  mb=$(( $(stat -c %s "$d/$zip") / 1048576 ))
  echo "$app	$ver	OK	${mb}MB	$(( $(date +%s) - t0 ))s	cli=$( [ -f "$cli" ] && echo si || echo NO )	mcp_in_help=$mcp	comandi=$ncmd" | tee -a "$LOG"
done
echo FINE | tee -a "$LOG"
