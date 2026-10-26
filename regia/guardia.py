# La guardia: ogni chiamata passa di qui prima di arrivare a un'app.
# 1) strumenti e comandi rischiosi bloccati (script, plugin, scaricamenti, RPC grezzo, LISP);
# 2) ogni valore che ha l'aspetto di un percorso, e OGNI valore di una chiave di percorso, deve restare
#    dentro progetti (risolto con realpath: giunzioni e collegamenti vengono seguiti);
# 3) i percorsi dentro progetti vengono riscritti nella forma che l'app accetta, secondo FORMA (misurata in O18a,
#    26/10/2026, app per app: tutte e 13 accettano l'assoluto con «/»; EffectCraft rifiuta il relativo). Si passa
#    sempre l'assoluto con «/» (non dipende dalla cwd); per EffectCraft anche un relativo con l'aspetto di un file
#    viene riscritto assoluto (vedi _vale_come_file).
# Correzioni O2 (25/10/2026) dopo l'esame O1: vedi O2_RAPPORTO.md.
import os, re
from figli import PROGETTI, CONFINATE

RADICE = os.path.normcase(os.path.realpath(PROGETTI))

# Strumenti MCP mai inoltrati: eseguono codice o parlano col programma senza passare dai comandi.
STRUMENTI_BLOCCATI = {
    "cadcraft": {"script": "esegue script .scr senza controllo dei percorsi"},
    "deckcraft": {"call_app": "RPC grezzo verso l'app"},
    "effectcraft": {"run_script": "esegue JavaScript", "script_ui": "finestre di script"},
    "photocraft": {"control_call": "RPC grezzo verso l'app"},
    "filmcraft": {"ui_control": "RPC grezzo verso l'app"},
}
# Parametri vietati in strumenti altrimenti ammessi.
PARAMETRI_BLOCCATI = {("designcraft", "batch", "script"): "script di testo non ispezionabile"}

# Comandi del catalogo (anche dentro batch, command_run, execute, tool_call…). Confronto senza maiuscole.
_BLOCCO_COMUNE = [
    r"(^|\.)scripts?(\.|$)", r"runScript", r"executeFile", r"installScript", r"scriptui\.",
    r"scriptEventsManager", r"runDroplet", r"(^|\.)lisp$",
    r"plugins?\.(install|import|run|reload|load|directory)", r"plugins\.runLast",
    r"download", r"models?\.install", r"(^|\.)install$",
    r"automate\.(runScript|trustScripts)", r"tools\.macros", r"tools\.recordMacro",
    r"js_console", r"document_js", r"svgInteractivity\.addFile",
    # O2: EffectCraft apre o esegue script per altre vie; storage.clear cancella progetti e salvataggi automatici.
    r"^window\.scriptPanel$", r"^window\.restoreScriptPanels$", r"^script\.runTasks$", r"^storage\.clear$",
]
COMANDI_BLOCCATI = re.compile("|".join(_BLOCCO_COMUNE), re.I)
# Eccezioni lecite che la regola comune prenderebbe.
COMANDI_AMMESSI = {"script.check"}

# CADCraft: comandi che eseguono codice o file, o che ridefiniscono gli alias (vie per aggirare questo elenco),
# con gli alias che la riga di comando accetta (sonda O2 su 1-3 lettere: vedi O2_RAPPORTO.md).
CAD_VIETATI = {"script", "scr", "lisp", "appload", "vlide", "vlisp", "netload", "arx", "sh", "shell", "start",
               "startapp", "load", "cuiload", "menuload", "acadlspasdoc", "aliasedit", "reinit", "ap"}

# Chiavi che contengono dati e non percorsi (base64 di immagini comincia spesso con «/9j/»).
CHIAVI_DATI = {"data", "base64", "dataBase64", "bytes", "image", "png", "content", "d", "svg",
               "wasm", "state", "code", "expression", "expr", "formula", "formulas"}
# Chiavi di percorso: questo elenco più ogni chiave il cui nome contiene path/dir/folder/file.
CHIAVI_PERCORSO = {"path", "paths", "dir", "out", "out_dir", "folder", "folders", "destination", "output",
                   "file", "files", "source", "sources", "input", "template", "droplet", "library"}
# Eccezioni: chiavi di percorso che in quello strumento sono testo (sempre controllate, mai riscritte;
# in GridCraft «input» è il contenuto di una cella, che passa dal ramo «testo libero»).
CHIAVI_TESTO = {("gridcraft", "input")}
# Strumenti il cui testo è una riga di comando dell'app: lo esaminiamo parola per parola.
TESTI_COMANDO = {("cadcraft", "command_line", "text")}

_ASSOLUTO = re.compile(r"^(?:[A-Za-z]:|[\\/]|~|file:|%[A-Za-z_]+%|\$[A-Za-z_{])", re.I)
_RISALITA = re.compile(r"(^|[\\/])\.\.([\\/]|$)")
# Nel testo libero: «a / b» resta testo (una barra da sola non è un percorso), «/Users/…» no.
_IN_TESTO = re.compile(r"^(?:[A-Za-z]:|[\\/]+[^\\/\s]|\\\\|//|file:|%[A-Za-z_]+%|~)", re.I)
_DISPOSITIVI = re.compile(r"^(con|prn|aux|nul|com[0-9¹²³]|lpt[0-9¹²³]|conin\$|conout\$)$", re.I)


class Rifiuto(Exception):
    pass


def chiave_di_percorso(k):
    if not isinstance(k, str):
        return False
    kl = k.lower()
    return kl in CHIAVI_PERCORSO or any(x in kl for x in ("path", "dir", "folder", "file"))


def sembra_percorso(s):
    return bool(_ASSOLUTO.match(s.strip()) or _RISALITA.search(s))


def _dispositivo(s):
    for parte in re.split(r"[\\/]", s):
        nome = parte.strip().rstrip(" .").split(".")[0].strip()
        if nome and _DISPOSITIVI.match(nome):
            raise Rifiuto("nome di dispositivo Windows non ammesso: %r" % s)


def risolvi(s):
    """Percorso assoluto normalizzato; i relativi sono relativi a progetti."""
    s = s.strip()
    if s.lower().startswith("file:"):
        raise Rifiuto("URL file: non ammessi: %r" % s)
    if re.match(r"^(%[A-Za-z_]+%|\$|~)", s):
        raise Rifiuto("variabili d'ambiente e ~ non ammesse: %r" % s)
    if re.match(r"^[A-Za-z]:(?![\\/])", s):
        raise Rifiuto("percorso relativo a un'unità (%r): usa un percorso completo" % s)
    if s.startswith(("\\\\", "//")):
        raise Rifiuto("percorsi di rete e di dispositivo non ammessi: %r" % s)
    if re.match(r"^[\\/]", s):
        raise Rifiuto("percorso dalla radice dell'unità non ammesso: %r" % s)
    _dispositivo(s)
    base = s if os.path.isabs(s) else os.path.join(PROGETTI, s)
    try:
        return os.path.realpath(base)
    except (OSError, ValueError) as e:
        raise Rifiuto("percorso non risolvibile: %r (%s)" % (s, e))


def dentro(assoluto):
    p = os.path.normcase(assoluto)
    return p == RADICE or p.startswith(RADICE + os.sep)


# Forma dei percorsi per app, misurata in O18a (26/10/2026): ogni app lanciata da sola, «nuovo» + «salva» con
# relativo, assoluto con «/» e assoluto con «\» (PdfCraft: doc_open + doc_save; LightCraft: import + export).
# «assoluto» = accetta SOLO l'assoluto (misurato: EffectCraft, «give an absolute path»);
# «entrambe» = accetta relativo e assoluto (le altre 12): si passa l'assoluto con «/», più robusto rispetto alla cwd.
# Un campione per app (il salvataggio); per EffectCraft O17 ha visto lo stesso rifiuto anche in lettura.
FORMA = {"cadcraft": "entrambe", "deckcraft": "entrambe", "designcraft": "entrambe", "effectcraft": "assoluto",
         "figcraft": "entrambe", "filmcraft": "entrambe", "gridcraft": "entrambe", "lightcraft": "entrambe",
         "pdfcraft": "entrambe", "photocraft": "entrambe", "soundcraft": "entrambe", "vectorcraft": "entrambe",
         "wordcraft": "entrambe"}


def forma_per_app(app, s):
    """Controlla il percorso e lo restituisce nella forma attesa dall'app (FORMA): assoluto con «/» per tutte.
    Un'app fuori da FORMA riceve anch'essa l'assoluto, accettato da tutte e 13 nella misura O18a."""
    ass = risolvi(s)
    if not dentro(ass):
        raise Rifiuto("percorso fuori da progetti: %r → %s" % (s, ass.replace("\\", "/")))
    return ass.replace("\\", "/")


def _vale_come_file(app, v):
    """Per le app che accettano SOLO l'assoluto: un relativo in una chiave di percorso va riscritto se ha l'aspetto
    di un file (estensione finale) o se la sua prima cartella esiste in progetti. «transform/position» o
    «effects/#1/blurriness» (percorsi di proprietà di EffectCraft) non lo hanno e restano invariati."""
    if FORMA.get(app) != "assoluto" or sembra_percorso(v):
        return False
    t = v.strip().replace("\\", "/")
    if re.search(r"\.[A-Za-z0-9]{1,8}$", t):
        return True
    primo = t.split("/")[0]
    return bool(primo) and "/" in t and os.path.isdir(os.path.join(PROGETTI, primo))


def _parola_cad(t):
    """Una parola della riga di comando ridotta al nome del comando: senza ^C, virgolette, - _ . ' iniziali."""
    t = re.sub(r"^(\^c)+", "", t.strip().strip('"'), flags=re.I)
    return t.lstrip("-_.'").lower()


def _comando_bloccato(app, cid):
    if not isinstance(cid, str) or cid.lower() in COMANDI_AMMESSI:
        return False
    if app == "cadcraft" and _parola_cad(cid) in CAD_VIETATI:
        return True
    return bool(COMANDI_BLOCCATI.search(cid))


def _controlla_riga_cad(testo):
    """Riga di comando di CADCraft: niente LISP e nessuna parola che avvii un comando vietato
    (gli spazi valgono Invio, quindi ogni parola può essere un comando nuovo)."""
    if "(" in testo or "!" in testo:
        raise Rifiuto("LISP non ammesso nella riga di comando di CADCraft: %r" % testo)
    for parola in re.split(r"[\s;]+", testo):
        if parola and _parola_cad(parola) in CAD_VIETATI:
            raise Rifiuto("comando bloccato dalla regia nella riga di comando di CADCraft: %r" % parola)


def _controlla_comandi(app, v, strumento):
    """Cerca, in profondità, i passi di comando ({command|id|tool} o [id, params]), con o senza params."""
    if isinstance(v, dict):
        for k in ("command", "id", "tool"):
            cid = v.get(k)
            if isinstance(cid, str) and _comando_bloccato(app, cid):
                raise Rifiuto("comando bloccato dalla regia: %s.%s" % (app, cid))
        for x in v.values():
            _controlla_comandi(app, x, strumento)
    elif isinstance(v, list):
        if len(v) >= 1 and isinstance(v[0], str) and (len(v) == 1 or isinstance(v[1], dict)):
            if _comando_bloccato(app, v[0]) and "." in v[0]:
                raise Rifiuto("comando bloccato dalla regia: %s.%s" % (app, v[0]))
        for x in v:
            _controlla_comandi(app, x, strumento)


def _candidati(v):
    """I pezzi di un testo che potrebbero essere un percorso: il testo intero, i tratti tra virgolette, le parole."""
    pezzi = [v.strip()]
    pezzi += re.findall(r'"([^"]*)"', v)
    pezzi += [p.strip('"') for p in re.findall(r'"[^"]*"|\S+', v)]
    return [p for p in pezzi if p]


def _testo_libero(app, v, comando, controlli):
    if comando:
        _controlla_riga_cad(v)
    for pezzo in _candidati(v):
        # nella riga di comando ogni pezzo con una barra è un possibile percorso (anche relativo: giunzioni)
        if (_IN_TESTO.match(pezzo) or _RISALITA.search(pezzo)
                or (comando and (sembra_percorso(pezzo) or re.search(r"[\\/]", pezzo)))):
            forma_per_app(app, pezzo)
            controlli.append(pezzo)


def _riscrivi(app, v, chiave, strumento, controlli):
    if isinstance(v, dict):
        return {k: _riscrivi(app, x, k, strumento, controlli) for k, x in v.items()}
    if isinstance(v, list):
        return [_riscrivi(app, x, chiave, strumento, controlli) for x in v]
    if not isinstance(v, str) or chiave in CHIAVI_DATI:
        return v
    comando = (app, strumento, chiave) in TESTI_COMANDO
    if comando:
        _testo_libero(app, v, True, controlli)
        return v
    if chiave_di_percorso(chiave) and (app, chiave) not in CHIAVI_TESTO:
        # Chiave di percorso: il valore si risolve SEMPRE (anche relativo, anche con spazi). Si riscrive solo
        # se ha forma di percorso assoluto o con «..»; altrimenti si lascia com'è (FigCraft «M0 0 L10 10»,
        # EffectCraft «transform/position»: risolti dentro progetti, quindi passano invariati).
        if not v.strip():
            return v
        nuovo = forma_per_app(app, v)
        controlli.append(v)
        return nuovo if (sembra_percorso(v) or _vale_come_file(app, v)) else v
    if app not in CONFINATE and len(v) < 4000 and (" " in v.strip() or '"' in v):
        _testo_libero(app, v, False, controlli)
        return v
    if sembra_percorso(v):
        nuovo = forma_per_app(app, v)
        controlli.append(v)
        return nuovo
    return v


def esamina(app, strumento, argomenti):
    """Restituisce (argomenti_riscritti, percorsi_controllati) o solleva Rifiuto."""
    if strumento in STRUMENTI_BLOCCATI.get(app, {}):
        raise Rifiuto("strumento bloccato dalla regia: %s.%s (%s)" % (app, strumento, STRUMENTI_BLOCCATI[app][strumento]))
    argomenti = argomenti or {}
    for (a, s, p), motivo in PARAMETRI_BLOCCATI.items():
        if a == app and s == strumento and p in argomenti:
            raise Rifiuto("parametro bloccato: %s.%s.%s (%s)" % (app, strumento, p, motivo))
    # pdfcraft tool_call: lo strumento vero è dentro.
    if strumento == "tool_call" and isinstance(argomenti.get("name"), str):
        interno = argomenti["name"]
        if interno in STRUMENTI_BLOCCATI.get(app, {}) or _comando_bloccato(app, interno):
            raise Rifiuto("strumento bloccato dalla regia: %s.%s" % (app, interno))
    for k in ("command", "id"):
        if isinstance(argomenti.get(k), str) and _comando_bloccato(app, argomenti[k]):
            raise Rifiuto("comando bloccato dalla regia: %s.%s" % (app, argomenti[k]))
    _controlla_comandi(app, argomenti, strumento)
    controlli = []
    nuovi = _riscrivi(app, argomenti, None, strumento, controlli)
    return nuovi, controlli
