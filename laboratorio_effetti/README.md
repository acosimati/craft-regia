# Laboratorio effetti della suite Craft

Pagine web statiche che disegnano un effetto al tempo `t` e uno script che le apre in un browser **senza finestra e senza rete**, salvando PNG, sequenze o video in `progetti/<progetto>/effetti/`. Le app Craft non vengono toccate (sono «Rust only»): ricevono soltanto file. Dal gateway si usa con lo strumento `effetto` di `regia/server.py`.

## Gli effetti
| effetto | libreria | parametri (`--param k=v`) |
|---|---|---|
| `gradiente` | ShaderGradient (MIT), costruito con esbuild in `effetti/gradiente/dist/` | `colore1` `colore2` `colore3` (#rrggbb), `velocita`, `tipo` (plane, sphere, waterPlane), `forza`, `densita`, `luminosita` |
| `vetro` | liquid-glass-js (MIT, `librerie/liquid-glass-js`, commit fissato) + html2canvas locale | `sfondo` (file in progetti), `x` `y` `larghezza` `altezza` del pannello in px, `raggio`, `tinta` 0-1, `forma` (rounded, pill, circle), `deriva` (px di oscillazione), `periodo` (s), `testo` |
| `metallo` | shader GLSL nostro (WebGL2, nessuna dipendenza) | `maschera` (PNG con alfa in progetti), `tinta` (#rrggbb), `rugosita` 0-1, `velocita`, `scala` 0.1-1, `fondo` (#rrggbb), `trasparente=1` |

Ogni pagina legge dall'indirizzo `w`, `h`, `t` e i suoi parametri, segnala `window.__pronto` quando è pronta ed espone `window.rendi(t)`: il tempo non scorre da solo, lo decide `rendi.py` fotogramma per fotogramma.

## Uso
```
python -X utf8 rendi.py gradiente --out _regia/effetti/prova --w 1280 --h 720 --frames 30 --fps 30 --formato mp4 --param colore1=#ff3d7f
```
`--out` è relativo a `progetti/` (o assoluto, ma dentro `progetti/`); anche `sfondo` e `maschera` devono stare lì. Con `--formato mp4|webm` i PNG passano da `fotogrammi/` e poi si cancellano (restano con `--tieni-fotogrammi`); resta sempre `anteprima.png`. La WebM conserva l'alfa con `trasparente=1`. Esce con 0 e stampa un JSON: file, byte, tempo totale, tempo d'avvio, tempo per fotogramma, renderer WebGL, richieste di rete bloccate.

## Come lavora
- Playwright per Python con il Chromium headless in cache (`chromium_headless_shell-1243`), GPU Intel via ANGLE/D3D11, `--hide-scrollbars`, viewport esatto, un browser alla volta, chiuso a fine resa.
- **Senza rete**: contesto `offline=True` e ogni richiesta che non sia `file:`/`data:`/`blob:` viene interrotta e annotata in `richieste_bloccate`.
- ffmpeg (provato con 9.0.1) per MP4 (x264) e WebM (VP9): quello indicato dalla variabile `FFMPEG`, altrimenti quello nel `PATH`.
- `progetti/` è quella del gateway: `CRAFT_PROGETTI`, oppure `CRAFT_RADICE/progetti`, oppure `progetti/` nella radice del repository.

## Installare e ricostruire
```
npm ci                       # solo in questa cartella; versioni fissate in package-lock.json
npm run build                # ricostruisce effetti/gradiente/dist/
# liquid-glass-js è già inclusa in librerie/; per riscaricarla:
git clone https://github.com/dashersw/liquid-glass-js.git librerie/liquid-glass-js && git -C librerie/liquid-glass-js checkout 78cb6ccb0b9987bb60a88b14ccbd13a9e6e8ab2a
```
Licenze in `../THIRD_PARTY.md`. Dal gateway: strumento `effetto` di `regia/server.py`.
