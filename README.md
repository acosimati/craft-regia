# craft-regia

A single MCP gateway that sits in front of the 13 [Craft apps](https://github.com/storytold) (open-source Rust clones of Photoshop, Lightroom, Premiere, InDesign, Illustrator, Acrobat, After Effects, Word, PowerPoint, Excel, AutoCAD, Pro Tools and Figma) and gives an AI agent one coherent way to drive all of them, from an idea to a finished result.

**Status:** prototype, 25 Oct 2026. Built to accompany a proposal to the Craft project: an agent that accompanies a production across the whole suite. It is not part of the Craft project and is not endorsed by it.

## What it does

The gateway (`regia/server.py`, Python, FastMCP) exposes **10 tools** instead of the ~270 native tools of the 13 apps:

| tool | what it does |
|---|---|
| `suite_catalogo` | the 13 apps: what they clone, version, formats, whether the app is sandboxed, whether it is running; plus known caveats |
| `suite_cerca` | "where is X": search over ~7,300 commands of all apps, also by their Italian names from [craft-i18n](https://github.com/storytold/craft-i18n) |
| `suite_verbi` | table of common verbs → native tool for every app |
| `app_strumenti` | the native MCP tools of one app (starts it if needed), with blocked tools marked and every parameter's type, range, enum, default and description |
| `app_usa` | call a native tool of an app, through the gateway's checks; images returned by the app are passed through intact |
| `app_verbo` | common verbs, identical for every app: new, open, save, export, inspect, preview, insert |
| `app_chiudi` | clean shutdown of one or all child apps (stdin closed → wait → terminate by PID) |
| `effetto` | renders an effect from the effects lab (gradient, liquid glass, liquid metal) to PNG/MP4/WebM inside `progetti/<project>/effetti/` |
| `diario_scrivi` / `diario_leggi` | a per-project diary, `progetti/<project>/DIARIO.md`, with phases idea / plan / production / review / delivery |

Key pieces:

- **Path guard** (`regia/guardia.py`): every string that looks like a path (absolute, `..`, `~`, `%VAR%`, `file:`, UNC, device paths), including inside generic command `params`, batches and the CADCraft command line, is resolved with `realpath` and must lie inside `progetti/`. Four of the apps (CADCraft, FilmCraft, GridCraft, LightCraft) have no sandbox of their own; the other nine, DeckCraft included, are launched with `--automation-read-root`/`--automation-write-root` set to `progetti/`: the guard is what keeps them inside `progetti/`. Paths inside `progetti/` are rewritten into the form each app accepts (`FORMA` in `guardia.py`, measured app by app: all 13 accept an absolute path with `/`, EffectCraft rejects relative ones), so every app receives an absolute path with `/`; for EffectCraft a relative value that looks like a file is made absolute too, while property paths such as `transform/position` pass unchanged.
- **Blocked tools and commands**: CADCraft `script`, EffectCraft `run_script`/`script_ui`, PhotoCraft `control_call`, DeckCraft `call_app`, FilmCraft `ui_control`, the `script` parameter of DesignCraft `batch`; and, at any nesting depth, commands that run scripts, plug-ins, macros, installers, model downloads, the JavaScript console or LISP.
- **Common verbs** (`regia/catalogo.py`): one vocabulary over the apps' different native names (`doc_save`, `save`, `save_workbook`, `save_presentation`, ...).
- **Search with i18n**: command catalogues of the 13 apps normalised into one index (`regia/normalizza.py`, `regia/dati/`), with Italian labels from craft-i18n for 6 apps plus the common catalogue. A word naming an app (its name or a short alias such as pdf, word, excel, cad, video, audio) becomes the app filter when none is given: "metadati pdf" searches "metadati" inside PdfCraft.
- **Effects lab** (`laboratorio_effetti/`): static web pages rendered headless and offline by Playwright (`rendi.py`); the apps only receive the resulting files. See `laboratorio_effetti/README.md`.

## Layout

```
craft-regia/
  regia/               gateway: server.py, figli.py (child servers), guardia.py, catalogo.py, diario.py, normalizza.py
    dati/              tool schemas and command catalogues of the 13 apps (generated), Italian TSVs from craft-i18n
    prove/             tests: prova_guardia.py, prova_gateway.py, O1/esame_o1.py (adversarial exam)
  laboratorio_effetti/ effects lab: effetti/, rendi.py, package.json, librerie/liquid-glass-js (vendored, MIT)
  strumenti/           install and maintenance scripts
  esempio.mcp.json     example MCP client entry
  app/                 (not in git) the portable Craft apps, one folder <app>-<version>
  progetti/            (not in git) the only folder the apps may read and write
```

The gateway finds `app/` and `progetti/` under the repository root. Override with environment variables: `CRAFT_RADICE` (root containing both), or `CRAFT_APP` and `CRAFT_PROGETTI` separately; `CRAFT_REGIA_LIBRERIA_LIGHTCRAFT` moves the LightCraft library (default `progetti/_regia/libreria_lightcraft`).

## Install (Windows x64)

1. Python 3.12 or newer, then `pip install mcp` (tested with `mcp` 1.30.0 on Python 3.14).
2. The portable apps, downloaded from their GitHub releases and checked against `SHA256SUMS.txt` (Git Bash):
   ```
   bash strumenti/installa_suite.sh "$PWD"
   mkdir -p progetti
   ```
   This fills `app/` (versions pinned inside the script) and keeps the zips in `scaricati/`.
3. Register the gateway with your MCP client: copy the entry in `esempio.mcp.json` into your `.mcp.json` and replace the placeholder paths. `python strumenti/genera_mcp_json.py <root>` writes instead a `.mcp.json` with the 13 native app servers, useful for comparison and for `strumenti/scarica_schemi.py`.
4. Optional, for the effects lab: `pip install playwright`, `python -m playwright install chromium`, ffmpeg on the `PATH` (or `FFMPEG=<path to ffmpeg.exe>`), then in `laboratorio_effetti/`: `npm ci` and `npm run build`.

## Tests

```
python -X utf8 regia/prove/prova_guardia.py      # 69 path-guard cases + 9 path-form cases, no app started
python -X utf8 regia/prove/prova_gateway.py      # 14 live checks over stdio (starts 4 apps, closes them)
python -X utf8 regia/prove/O1/esame_o1.py        # adversarial exam: escape attempts must leave no file outside progetti/
```

All three start the gateway themselves as a child process and close it at the end. The adversarial exam creates a junction inside `progetti/` pointing outside and a folder `O1_bersagli_fuori/` next to it; both are test fixtures.

## Updating after a new app release

```
python -I -X utf8 strumenti/scarica_schemi.py .mcp.json regia/dati/schemi.json
```
then collect the command catalogues again and run `python -X utf8 normalizza.py` from `regia/`.

## Known limits

- Tested on Windows 10 only, on one PC. The apps are started from `app/<app>-<version>/<app>-cli.exe`.
- PdfCraft and LightCraft are exposed with all their tools (not their compact mode); PdfCraft `tool_search`/`tool_call` are therefore absent.
- The gateway reads schemas from `regia/dati/`, not from the apps at start-up; versions are read from the folder names in `app/`.
- LightCraft uses its own library because a library can be opened by one process only.
- Italian labels exist only for CADCraft, FilmCraft, PdfCraft, PhotoCraft, VectorCraft, WordCraft and the common catalogue.
- Blocked tools are listed above; the block list is conservative and may refuse legitimate calls.
- CADCraft evaluates LISP anywhere on its command line (measured once on 0.12.0: `circle 0,0 !r`, `circle 10,0 (+ 1 4)`), while at the TEXT «Enter text» prompt the same line stays text. The gateway does not know the prompt, so it refuses a line that starts with `(`, `!` or `'(`, a `(` followed by a known LISP form (`setq`, `command`, `load`, `defun`, `getpoint`, `strcat`, `+ - * /` followed by a space, `vl-`/`vla-`, … see `_LISP_FORME` in `regia/guardia.py`), and a word starting with `!` followed by a name. Text such as `PLAN (holes D6 through)` passes. A LISP function outside the list, placed after the first character, can pass: the defence remains the block on `script`/`appload`/`lisp` and path confinement.
- `regia/dati/schemi.json` keeps the apps' own server instructions; where an app printed its local sandbox folder, it has been replaced by `<CRAFT_RADICE>\progetti`.

## License

MIT, see `LICENSE`. Third-party components and data: see `THIRD_PARTY.md`.

---

## In italiano

**craft-regia** è un unico server MCP che sta davanti alle 13 app Craft e le rende guidabili da un agente con 10 strumenti: catalogo della suite, ricerca delle funzioni (anche coi nomi italiani di craft-i18n), verbi comuni uguali per tutte le app, uso degli strumenti nativi sotto controllo, diario di progetto e laboratorio effetti. La **guardia dei percorsi** tiene ogni file dentro `progetti/`, anche per le cinque app che non hanno confini propri, e blocca script, plug-in e macro.

Installazione: Python 3.12+, `pip install mcp`, le app con `strumenti/installa_suite.sh`, la voce di `esempio.mcp.json` nel proprio `.mcp.json`. La radice si trova da sola (la cartella del repository) oppure si indica con `CRAFT_RADICE`; `app/` e `progetti/` non sono nel repository.

Prove: `regia/prove/prova_guardia.py` (69 casi), `regia/prove/prova_gateway.py` (14 esiti dal vero), `regia/prove/O1/esame_o1.py` (esame avversario).

Stato: prototipo del 25 ottobre 2026, provato solo su Windows, scritto per accompagnare una proposta al progetto Craft.
