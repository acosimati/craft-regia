# Third-party components and data

Everything listed here keeps its own licence. Licences were read from the packages' `package.json`/`package-lock.json` and LICENSE files and from the source repositories on 25 Oct 2026.

## Vendored in this repository

| component | version | licence | where | source |
|---|---|---|---|---|
| liquid-glass-js (dashersw) | commit `78cb6ccb0b9987bb60a88b14ccbd13a9e6e8ab2a` (12 Jun 2025), unmodified, without `.git` | MIT (`LICENSE`, Copyright (c) 2025 Armagan Amcalar) | `laboratorio_effetti/librerie/liquid-glass-js/` | https://github.com/dashersw/liquid-glass-js |
| craft-i18n, Italian catalogues (`it` column only, 7 TSV files) | commit `ed5cc5e` (24 Oct 2026) | MIT OR Apache-2.0 (`regia/dati/i18n_it/LICENSE-MIT`, `LICENSE-APACHE`, copied from the repository); translator credits in the upstream `ATTRIBUTION.md` | `regia/dati/i18n_it/` | https://github.com/storytold/craft-i18n |

liquid-glass-js is not published on npm (the npm package with that name is a different project), so it is vendored at a pinned commit.

## Generated data

`regia/dati/schemi.json`, `regia/dati/cataloghi_grezzi.json` and `regia/dati/comandi.json` were generated from the MCP servers and command catalogues of the Craft apps (https://github.com/storytold), portable Windows x64 releases: PhotoCraft 0.15.1, LightCraft 0.13.0, FilmCraft 0.12.0, DesignCraft 0.12.0, VectorCraft 0.16.0, PdfCraft 0.13.0, EffectCraft 0.16.0, WordCraft 0.10.0, DeckCraft 0.10.0, GridCraft 0.11.1, CADCraft 0.12.0, SoundCraft 0.12.1, FigCraft 0.10.0. They contain the apps' own tool names, descriptions and schemas, kept as published; the only change is that a local sandbox path in FigCraft's server instructions was replaced by `<CRAFT_RADICE>\progetti`. The apps themselves are not included: `strumenti/installa_suite.sh` downloads them from their official releases.

## npm packages (effects lab, not committed: installed with `npm ci`)

Pinned in `laboratorio_effetti/package-lock.json`. All permissive: MIT except `ieee754` (BSD-3-Clause).

| package | version | licence | source |
|---|---|---|---|
| `@shadergradient/react` | 2.4.20 | MIT (field `license`; the package ships no LICENSE file); bundles camera-controls (MIT) | https://github.com/ruucm/shadergradient |
| `@react-three/fiber` | 9.8.2 | MIT | https://github.com/pmndrs/react-three-fiber |
| `three` | 0.186.1 | MIT | https://github.com/mrdoob/three.js |
| `react`, `react-dom` | 19.3.1 | MIT | https://github.com/react/react |
| `scheduler` | 0.28.0 | MIT | https://github.com/react/react |
| `use-sync-external-store` | 1.7.0 | MIT | https://github.com/react/react |
| `html2canvas` | 1.4.1 | MIT | https://github.com/niklasvh/html2canvas |
| `base64-arraybuffer` | 1.0.2 | MIT | https://github.com/niklasvh/base64-arraybuffer |
| `css-line-break` | 2.1.0 | MIT | https://github.com/niklasvh/css-line-break |
| `text-segmentation` | 1.0.3 | MIT | https://github.com/niklasvh/text-segmentation |
| `utrie` | 1.0.2 | MIT | https://github.com/niklasvh/utrie |
| `@babel/runtime` | 7.29.10 | MIT | https://github.com/babel/babel |
| `its-fine` | 2.1.1 | MIT | https://github.com/pmndrs/its-fine |
| `react-use-measure` | 2.1.7 | MIT | https://github.com/pmndrs/react-use-measure |
| `suspend-react` | 0.1.3 | MIT | https://github.com/pmndrs/suspend-react |
| `zustand` | 5.0.16 | MIT | https://github.com/pmndrs/zustand |
| `buffer` | 6.0.3 | MIT | https://github.com/feross/buffer |
| `base64-js` | 1.5.1 | MIT | https://github.com/beatgammit/base64-js |
| `ieee754` | 1.2.1 | BSD-3-Clause | https://github.com/feross/ieee754 |
| `csstype` | 3.2.3 | MIT | https://github.com/frenic/csstype |
| `@types/react` | 19.3.0 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| `@types/react-reconciler` | 0.28.9 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| `@types/webxr` | 0.5.24 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| `esbuild`, `@esbuild/<platform>` (build only) | 0.28.2 | MIT | https://github.com/evanw/esbuild |

The gradient page is built by `npm run build` into `laboratorio_effetti/effetti/gradiente/dist/` (not committed); the bundle keeps the packages' licence comments at the end of `app.js`.

## Python packages (not vendored)

| package | licence | use |
|---|---|---|
| `mcp` (tested 1.30.0) | MIT | the gateway (FastMCP) |
| `playwright` | Apache-2.0 | effects lab rendering, optional |

ffmpeg is used, if present on the `PATH`, to encode MP4/WebM; it is not distributed here.
