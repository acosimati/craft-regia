# craft-regia: un solo server MCP davanti alle 13 app della suite Craft.
# Avvio: python -X utf8 server.py   (stdio). Dipende dal pacchetto «mcp» (FastMCP).
import base64, datetime, json, os, re, subprocess, sys, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

import catalogo, diario
import guardia
from figli import Figli, ErroreFiglio, app_installate, PROGETTI, CONFINATE
from guardia import esamina, Rifiuto, STRUMENTI_BLOCCATI

ISTRUZIONI = """craft-regia è la regia della suite Craft (13 cloni open source di Adobe, Office, AutoCAD, Pro Tools, Figma).
Flusso: suite_catalogo → suite_cerca «che cosa fa X e dove» → app_verbo (apri/salva/esporta/ispeziona/anteprima/inserisci/nuovo,
uguali per tutte le app) oppure app_usa (strumento nativo dell'app, elenco con app_strumenti) → diario_scrivi.
Tutti i file stanno in progetti/: i percorsi si danno relativi a quella cartella (es. «logo/bozza.svg»); un percorso fuori viene rifiutato.
Le app si avviano da sole alla prima chiamata e restano aperte (lo stato del documento è lì) finché non chiami app_chiudi.
Effetti grafici (laboratorio effetti, collegato e non dentro le app): `effetto` rende gradiente (ShaderGradient), vetro
(liquid-glass-js) o metallo (shader nostro) in PNG/MP4/WebM dentro progetti/<progetto>/effetti/; i file poi entrano nelle
app con app_verbo (inserisci/apri)."""

mcp = FastMCP("craft-regia", instructions=ISTRUZIONI)
FIGLI = Figli()


AVVERTENZE = """## Avvertenze note
- PdfCraft e LightCraft, attraverso la regia, espongono tutti i loro strumenti (175 e 388), non la modalità compatta:
  si chiamano per nome con app_usa; `tool_search`/`tool_call` di PdfCraft non servono (e non ci sono).
- VectorCraft: `draw_path` vuole `opacity` in percento 0-100 (doc_inspect la riporta 0-1); il `detail` di `distort.roughen` è per pollice.
- DesignCraft: `render_page` conta le pagine da 0, `file.exportPdf` da 1.
- Le anteprime (app_verbo anteprima, render_*/screenshot con app_usa) arrivano come immagine vera, accanto al testo della regia."""


def _immagini(risultato):
    """I blocchi immagine del risultato MCP di un'app, pronti da inoltrare così come sono."""
    return [ImageContent(type="image", data=c["data"], mimeType=c.get("mimeType") or "image/png")
            for c in risultato.get("content", []) if c.get("type") == "image" and c.get("data")]


def _testo(risultato, immagini_inoltrate=False):
    """Riduce il risultato MCP di un'app a testo (o JSON) leggibile; le immagini, se inoltrate a parte, sono solo annunciate."""
    if risultato.get("structuredContent") is not None:
        t = json.dumps(risultato["structuredContent"], ensure_ascii=False)
    else:
        parti = []
        for c in risultato.get("content", []):
            if c.get("type") == "text":
                parti.append(c["text"])
            elif c.get("type") == "image":
                parti.append("[immagine %s, %d byte base64%s]" % (c.get("mimeType"), len(c.get("data", "")),
                                                                  ": inoltrata qui sotto" if immagini_inoltrate else ""))
            else:
                parti.append(json.dumps(c, ensure_ascii=False)[:500])
        t = "\n".join(parti)
    return ("ERRORE DELL'APP: " + t) if risultato.get("isError") else t


def _inoltra(app, strumento, argomenti):
    """Guardia, poi chiamata all'app. Restituisce (testo, immagini)."""
    nuovi, controllati = esamina(app, strumento, argomenti)
    f = FIGLI.prendi(app)
    if strumento not in {t["name"] for t in f.strumenti}:
        raise ErroreFiglio("%s non ha lo strumento %r: vedi app_strumenti" % (app, strumento))
    r = f.chiama(strumento, nuovi)
    immagini = _immagini(r)
    testo = _testo(r, bool(immagini))
    if app == "pdfcraft" and not r.get("isError"):  # O15: il «doc» aperto diventa il default dei verbi
        if strumento == "doc_open":
            testo += "\n[regia: documento %s ricordato per salva/esporta/ispeziona/anteprima]" % catalogo.ricorda_doc(app, testo)
        elif strumento == "doc_close" and nuovi.get("doc") == catalogo.ULTIMO_DOC.get(app):
            catalogo.dimentica_doc(app)
    if controllati:
        testo += "\n[regia: percorsi controllati: %s]" % ", ".join(controllati)
    return testo, immagini


def _risposta(testo, immagini):
    """Solo testo se non ci sono immagini (come prima); altrimenti il testo della regia più le immagini intere."""
    return [TextContent(type="text", text=testo)] + immagini if immagini else testo


@mcp.tool()
def suite_catalogo() -> str:
    """Le 13 app della suite: che cosa fa ciascuna, di che cosa è il clone, versione installata, formati, se è avviata.
    In fondo le «Avvertenze note»: PdfCraft e LightCraft via regia espongono tutti gli strumenti (175 e 388), non la
    modalità compatta (tool_search/tool_call di PdfCraft non servono: si chiama lo strumento per nome); VectorCraft
    draw_path vuole opacity 0-100 e il dettaglio di distort.roughen è per pollice; DesignCraft render_page conta da 0,
    exportPdf da 1."""
    inst = app_installate()
    righe = []
    for app, (clone, cosa, formati) in catalogo.APP.items():
        ver = inst.get(app, ("non installata",))[0]
        stato = "avviata" if app in FIGLI.attivi and FIGLI.attivi[app].vivo() else "ferma"
        righe.append("- **%s** %s (come %s): %s. Formati: %s. Confinata dall'app: %s. [%s]" % (
            app, ver, clone, cosa, formati, "sì" if app in CONFINATE else "no, ci pensa la regia", stato))
    righe.append("- **laboratorio_effetti** (collegato, non un'app: pagine web rese senza finestra; licenze MIT: "
                 "ShaderGradient, liquid-glass-js, html2canvas, three, React, R3F): effetti gradiente, vetro, metallo → "
                 "PNG/MP4/WebM in progetti/<progetto>/effetti/. Si usa con lo strumento `effetto`. [%s]"
                 % ("pronto" if os.path.isfile(RENDI) else "non installato"))
    righe.append("\nVerbi comuni: " + ", ".join(catalogo.NOMI_VERBI) + ". Radice dei file: " + PROGETTI)
    righe.append("\n" + AVVERTENZE)
    return "\n".join(righe)


@mcp.tool()
def suite_cerca(testo: str, app: str = "", limite: int = 12) -> str:
    """Dove si trova una funzione nella suite: cerca in tutti i comandi delle 13 app (≈7.300), anche con i nomi italiani.
    Restituisce app, id del comando (da usare in app_usa con lo strumento di esecuzione dell'app), etichetta, menu, parametri."""
    ris = catalogo.cerca(testo, app or None, limite)
    if not ris:
        return "Niente trovato per %r." % testo
    out = []
    for r in ris:
        et = r["etichetta"] + (" («%s»)" % r["etichetta_it"] if r["etichetta_it"] else "")
        menu = (" · menu: " + (r["menu_it"] or r["menu"])) if r["menu"] else ""
        out.append("- %s · %s `%s` — %s%s\n    parametri: %s" % (r["app"], r["tipo"], r["id"], et, menu, r["params"][:200] or "—"))
    return "\n".join(out)


def _tipo(s):
    """Tipo compatto di uno schema JSON: number, string, array<number>, string|array<number>|object, ..."""
    if not isinstance(s, dict):
        return "?"
    if "anyOf" in s or "oneOf" in s:
        return "|".join(_tipo(x) for x in s.get("anyOf") or s.get("oneOf"))
    t = s.get("type")
    if isinstance(t, list):
        return "|".join(t)
    if t == "array" and isinstance(s.get("items"), dict):
        return "array<%s>" % _tipo(s["items"])
    return t or ("enum" if "enum" in s else "any")


def _parametro(nome, s, obbligatorio, taglio=None):
    """Una riga per parametro: `- opacity: number 0..100 — Opacity in % (...)`, con enum e default se dichiarati."""
    s = s if isinstance(s, dict) else {}
    parti = [_tipo(s)]
    mn, mx = s.get("minimum", s.get("exclusiveMinimum")), s.get("maximum", s.get("exclusiveMaximum"))
    if mn is not None or mx is not None:
        parti.append("%s..%s" % ("" if mn is None else mn, "" if mx is None else mx))
    if "enum" in s:
        parti.append("{%s}" % "|".join(str(v) for v in s["enum"]))
    if "default" in s:
        parti.append("= %s" % json.dumps(s["default"], ensure_ascii=False))
    desc = (s.get("description") or "").replace("\n", " ")
    if taglio and len(desc) > taglio:
        desc = desc[:taglio] + "…"
    return "    - %s%s: %s%s" % (nome, "*" if obbligatorio else "", " ".join(parti), (" — " + desc) if desc else "")


@mcp.tool()
def app_strumenti(app: str, filtro: str = "", strumento: str = "") -> str:
    """Gli strumenti MCP nativi di un'app; per ogni parametro: tipo, minimo..massimo, enum, default e descrizione dichiarati
    dall'app (es. «- opacity: number 0..100 — Opacity in %»; * = obbligatorio). Avvia l'app se è ferma.
    `filtro` restringe l'elenco (nome o descrizione); `strumento` mostra UN solo strumento per intero (descrizione completa,
    nessun taglio). Gli strumenti bloccati dalla regia sono segnati."""
    f = FIGLI.prendi(app)
    bloccati = STRUMENTI_BLOCCATI.get(app, {})
    if strumento and strumento not in {t["name"] for t in f.strumenti}:
        return "RIFIUTATO DALLA REGIA: %s non ha lo strumento %r (elenco con app_strumenti senza `strumento`)" % (app, strumento)
    out = []
    for t in f.strumenti:
        if strumento and t["name"] != strumento:
            continue
        if filtro and filtro.lower() not in (t["name"] + " " + t.get("description", "")).lower():
            continue
        sch = t.get("inputSchema") or {}
        req = sch.get("required") or []
        props = sch.get("properties") or {}
        marca = "  ⛔ BLOCCATO: " + bloccati[t["name"]] if t["name"] in bloccati else ""
        desc = t.get("description") or ""
        if not strumento and len(desc) > 220:
            desc = desc[:220] + "…"
        righe = ["- `%s`%s\n    %s" % (t["name"], marca, desc)]
        righe += [_parametro(k, v, k in req, None if strumento else 160) for k, v in props.items()] or ["    (nessun parametro)"]
        out.append("\n".join(righe))
    return "%s %s · %d strumenti\n" % (app, f.info.get("serverInfo", {}).get("version", "?"), len(f.strumenti)) + "\n".join(out)


# structured_output=False: così il tool può restituire testo oppure [testo, immagini] (FastMCP 1.30,
# func_metadata._convert_to_content inoltra TextContent/ImageContent così come sono).
@mcp.tool(structured_output=False)
def app_usa(app: str, strumento: str, argomenti: dict = None) -> str | list:
    """Usa l'app X con il suo strumento nativo Y (nomi da app_strumenti; per i comandi del catalogo usa lo strumento di
    esecuzione dell'app: command_run/execute/run_command/execute_command con {id|command, params}).
    PdfCraft e LightCraft, attraverso la regia, espongono tutti gli strumenti (175 e 388), non la modalità compatta:
    si chiamano per nome (tool_search/tool_call di PdfCraft non servono). Le immagini dell'app arrivano intere.
    La regia controlla ogni percorso (deve stare in progetti/) e blocca script, plug-in e scaricamenti."""
    try:
        return _risposta(*_inoltra(app, strumento, argomenti or {}))
    except (Rifiuto, ErroreFiglio, ValueError) as e:
        return "RIFIUTATO DALLA REGIA: %s" % e


@mcp.tool(structured_output=False)
def app_verbo(app: str, verbo: str, percorso: str = "", opzioni: dict = None) -> str | list:
    """Verbo comune tradotto per l'app: nuovo, apri, salva, esporta, ispeziona, anteprima, inserisci.
    `percorso` è relativo a progetti/ (es. «volantino/bozza.pdf»); «esporta» sceglie il formato dall'estensione.
    `opzioni` sono i parametri piatti dello strumento o del comando sottostante (es. per `nuovo` di VectorCraft:
    `{"width": 841.89, "height": 1190.55}`); se arrivano annidati in {"params": {...}} la regia li spiana.
    «anteprima» restituisce l'immagine vera, accanto al testo della regia.
    PdfCraft e LightCraft via regia espongono tutti gli strumenti (175 e 388), non la modalità compatta: con app_usa
    si chiamano per nome. Avvertenze sulle singole app (opacità di VectorCraft, pagine di DesignCraft) in suite_catalogo."""
    try:
        strumento, argomenti = catalogo.traduci_verbo(app, verbo, percorso or None, opzioni)
        testo, immagini = _inoltra(app, strumento, argomenti)
        testo = "[regia: %s.%s → %s %s]\n%s" % (app, verbo, strumento, json.dumps(argomenti, ensure_ascii=False)[:200], testo)
        return _risposta(testo, immagini)
    except (Rifiuto, ErroreFiglio, ValueError) as e:
        return "RIFIUTATO DALLA REGIA: %s" % e


@mcp.tool()
def suite_verbi() -> str:
    """Tabella: per ogni app, quale strumento nativo sta dietro a ogni verbo comune (mostra le incoerenze della suite)."""
    tab = catalogo.tabella_verbi()
    righe = ["| app | " + " | ".join(catalogo.NOMI_VERBI) + " |", "|---" * (len(catalogo.NOMI_VERBI) + 1) + "|"]
    for app, r in tab.items():
        righe.append("| %s | %s |" % (app, " | ".join(r[v] for v in catalogo.NOMI_VERBI)))
    return "\n".join(righe)


@mcp.tool()
def app_chiudi(app: str = "") -> str:
    """Chiude un'app avviata (o tutte, senza argomento) in modo pulito. Salva prima: lo stato in memoria va perso."""
    esiti = FIGLI.chiudi(app or None)
    catalogo.dimentica_doc(app or None)
    return "Chiuse: %s" % (json.dumps(esiti, ensure_ascii=False) if esiti else "nessuna app era avviata")


@mcp.tool()
def diario_scrivi(progetto: str, testo: str, fase: str = "nota", app: str = "") -> str:
    """Aggiunge una voce al diario progetti/<progetto>/DIARIO.md. Fasi: idea, piano, produzione, revisione, consegna, nota."""
    try:
        p = diario.scrivi(progetto, testo, fase, app or None)
        return "Scritto in " + p.replace("\\", "/")
    except ValueError as e:
        return "RIFIUTATO DALLA REGIA: %s" % e


LAB = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "laboratorio_effetti"))
RENDI = os.path.join(LAB, "rendi.py")
EFFETTI = ("gradiente", "vetro", "metallo")
PARAMETRI_PERCORSO_EFFETTI = {"sfondo", "maschera"}
_UN_BROWSER = threading.Lock()  # un browser headless alla volta (regola del PC HP)


def _chiudi_albero(proc):
    """Chiude il sottoprocesso e i suoi figli (browser compresi) per PID, mai per nome."""
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)


@mcp.tool(structured_output=False)
def effetto(nome: str, progetto: str, parametri: dict = None, larghezza: int = 1280, altezza: int = 720,
            fotogrammi: int = 1, fps: float = 30, formato: str = "png") -> str | list:
    """Rende un effetto del laboratorio effetti senza finestra e senza rete, in progetti/<progetto>/effetti/<nome>_<data-ora>/.
    nome: gradiente (ShaderGradient; parametri colore1/colore2/colore3 #rrggbb, velocita, tipo plane|sphere|waterPlane,
    forza, densita, luminosita), vetro (liquid-glass-js su un'immagine; sfondo=<file in progetti>, x, y, larghezza,
    altezza, raggio, tinta 0-1, forma rounded|pill|circle, deriva px, periodo s, testo), metallo (shader nostro su un PNG
    con alfa; maschera=<file in progetti>, tinta #rrggbb, rugosita 0-1, velocita, scala, fondo #rrggbb, trasparente=1).
    formato: png (un PNG per fotogramma), mp4 o webm (con anteprima.png). I percorsi passano dalla guardia della regia.
    Restituisce il JSON del laboratorio (file, byte, tempi) e il primo fotogramma come immagine; scrive il diario."""
    try:
        if nome not in EFFETTI:
            raise ValueError("effetto sconosciuto: %r (validi: %s)" % (nome, ", ".join(EFFETTI)))
        if formato not in ("png", "mp4", "webm"):
            raise ValueError("formato non valido: %r (png, mp4, webm)" % formato)
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_\-]{0,60}", progetto or ""):
            raise Rifiuto("nome di progetto non valido: %r (lettere, cifre, _ e -; niente percorsi)" % progetto)
        if not (1 <= int(fotogrammi) <= 900):
            raise ValueError("fotogrammi tra 1 e 900")
        ora = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        uscita = guardia.forma_per_app("gridcraft", "%s/effetti/%s_%s" % (progetto, nome, ora))  # assoluto, dentro progetti
        argv = [sys.executable, "-X", "utf8", RENDI, nome, "--out", uscita, "--w", str(int(larghezza)),
                "--h", str(int(altezza)), "--frames", str(int(fotogrammi)), "--fps", str(float(fps)), "--formato", formato]
        controllati = []
        for k, v in (parametri or {}).items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,30}", str(k)):
                raise ValueError("nome di parametro non valido: %r" % k)
            v = str(v)
            if "\n" in v or "\r" in v or len(v) > 500:
                raise ValueError("valore del parametro %s non ammesso" % k)
            if k in PARAMETRI_PERCORSO_EFFETTI or guardia.chiave_di_percorso(k) or guardia.sembra_percorso(v):
                v = guardia.forma_per_app("gridcraft", v)  # solleva Rifiuto se fuori da progetti
                controllati.append(v)
            argv += ["--param", "%s=%s" % (k, v)]
    except (Rifiuto, ValueError) as e:
        return "RIFIUTATO DALLA REGIA: %s" % e
    if not os.path.isfile(RENDI):
        return "ERRORE: laboratorio effetti non trovato in %s" % LAB.replace("\\", "/")
    with _UN_BROWSER:
        # stdin=DEVNULL: il figlio non deve ereditare la pipe MCP del gateway (su Windows il suo avvio si blocca: O8)
        proc = subprocess.Popen(argv, cwd=LAB, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            out, err = proc.communicate(timeout=90 + 3 * int(fotogrammi))
        except subprocess.TimeoutExpired:
            _chiudi_albero(proc)
            proc.communicate()
            return "ERRORE DEL LABORATORIO: tempo scaduto (processo chiuso per PID %d)" % proc.pid
    try:
        esito = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return "ERRORE DEL LABORATORIO (exit %s): %s %s" % (proc.returncode, out[-500:], err[-500:])
    if proc.returncode != 0 or "errore" in esito:
        return "ERRORE DEL LABORATORIO (exit %s): %s" % (proc.returncode, esito.get("errore", out[-500:]))
    rel = os.path.relpath(esito["cartella"], PROGETTI).replace("\\", "/")
    diario.scrivi(progetto, "effetto «%s» %s %d×%d, %d fotogrammi → %s (%s s)" % (
        nome, formato, esito["larghezza"], esito["altezza"], esito["fotogrammi"], rel, esito["tempo_totale_s"]),
        "produzione", "laboratorio_effetti")
    testo = json.dumps(esito, ensure_ascii=False)
    if controllati:
        testo += "\n[regia: percorsi controllati: %s]" % ", ".join(controllati)
    png = next((f["percorso"] for f in esito["file"] if f["percorso"].lower().endswith(".png")), None)
    if not png:
        return testo
    with open(png, "rb") as fh:
        dati = base64.b64encode(fh.read()).decode("ascii")
    return [TextContent(type="text", text=testo + "\n[regia: anteprima = %s]" % os.path.basename(png)),
            ImageContent(type="image", data=dati, mimeType="image/png")]


@mcp.tool()
def diario_leggi(progetto: str) -> str:
    """Il diario del progetto, più l'elenco dei file nella sua cartella (quelli che passano da un'app all'altra)."""
    try:
        files = diario.file_del_progetto(progetto)
    except ValueError as e:
        return "RIFIUTATO DALLA REGIA: %s" % e
    elenco = "\n".join("- %s (%d byte, %s)" % (f["file"], f["byte"], f["modificato"]) for f in files) or "- (nessun file)"
    return diario.leggi(progetto) + "\n\n## File del progetto\n" + elenco


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    finally:
        FIGLI.chiudi()
