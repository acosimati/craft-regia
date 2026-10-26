# Catalogo della suite: che cosa fa ogni app, i verbi comuni tradotti per ciascuna,
# la ricerca delle funzioni su tutti i comandi (con i nomi italiani di craft-i18n).
import csv, json, os, re, unicodedata

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(QUI, "dati")

APP = {
    "photocraft": ("Photoshop", "fotoritocco e grafica raster a livelli", "png jpg tif psd webp pcraft"),
    "lightcraft": ("Lightroom", "archivio fotografico e sviluppo dei raw, modifiche non distruttive", "jpg tif dng raw"),
    "filmcraft": ("Premiere Pro", "montaggio video su timeline", "mp4 mov wav edl xml"),
    "effectcraft": ("After Effects", "grafica animata e compositing", "mp4 mov png gif lottie ecproj"),
    "designcraft": ("InDesign", "impaginazione di pagine e libri", "pdf idml epub html pptx designcraft"),
    "vectorcraft": ("Illustrator", "illustrazione vettoriale, loghi, tracciati", "svg pdf ai eps png dxf vectorcraft"),
    "pdfcraft": ("Acrobat", "lettura, modifica, unione e divisione di PDF", "pdf"),
    "wordcraft": ("Word", "videoscrittura", "docx odt rtf pdf png txt"),
    "deckcraft": ("PowerPoint", "presentazioni", "pptx pdf png gif deckcraft"),
    "gridcraft": ("Excel", "fogli di calcolo e grafici", "xlsx csv tsv json html pdf"),
    "cadcraft": ("AutoCAD", "disegno tecnico 2D/3D", "dwg dxf svg png pdf"),
    "soundcraft": ("Pro Tools", "registrazione e missaggio audio multitraccia", "wav aiff flac mid"),
    "figcraft": ("Figma", "progettazione di interfacce, componenti, prototipi", "figcraft fig png jpg svg pdf webp"),
}


# ---------- verbi comuni ----------
# Ogni verbo diventa (strumento, argomenti). «P» è il segnaposto del percorso.
def T(strumento, chiave=None, lista=False, **fisso):
    def f(percorso, opz):
        a = dict(fisso)
        if chiave and percorso is not None:
            a[chiave] = [percorso] if lista else percorso
        a.update(opz)
        return strumento, a
    return f


def C(strumento, campo_id, comando, chiave=None, lista=False):
    def f(percorso, opz):
        p = dict(opz)
        if chiave and percorso is not None:
            p[chiave] = [percorso] if lista else percorso
        return strumento, {campo_id: comando, "params": p}
    return f


def PER_ESTENSIONE(tabella, altrimenti):
    """Sceglie il costruttore dall'estensione del percorso."""
    def f(percorso, opz):
        est = os.path.splitext(percorso or "")[1].lower().lstrip(".")
        return tabella.get(est, altrimenti)(percorso, opz)
    f.tabella, f.altrimenti = tabella, altrimenti  # O15: suite_verbi elenca tutti i casi, non solo il primo
    return f


# O15: PdfCraft vuole «doc» (id del documento aperto) in doc_save, doc_inspect, render_preview. La regia ricorda
# l'ultimo id restituito da doc_open (per app) e lo usa come default se le opzioni non lo danno.
ULTIMO_DOC = {}


def ricorda_doc(app, testo):
    """Dopo un doc_open riuscito: prende l'id dal JSON di risposta ({"doc": N, ...})."""
    m = re.search(r'"doc"\s*:\s*(\d+)', testo or "")
    if m:
        ULTIMO_DOC[app] = int(m.group(1))
    return ULTIMO_DOC.get(app)


def dimentica_doc(app=None):
    if app:
        ULTIMO_DOC.pop(app, None)
    else:
        ULTIMO_DOC.clear()


def DOC(app, strumento, chiave=None, obbligatorio=True):
    """Come T(...), più «doc» = ultimo documento aperto con «apri», se le opzioni non lo danno."""
    def f(percorso, opz):
        a = {}
        if chiave and percorso is not None:
            a[chiave] = percorso
        a.update(opz)
        if "doc" not in a:
            if app in ULTIMO_DOC:
                a["doc"] = ULTIMO_DOC[app]
            elif obbligatorio:
                raise ValueError("apri prima un PDF (app_verbo %s apri <percorso>) oppure passa opzioni {\"doc\": N}" % app)
        return strumento, a
    f.strumento = strumento
    return f


def NON_C_E(motivo):
    def f(percorso, opz):
        raise ValueError(motivo)
    return f


VERBI = {
    "photocraft": {"nuovo": T("doc_new"), "apri": T("doc_open", "path"), "salva": T("doc_save", "path"),
                   "esporta": T("doc_export", "path"), "ispeziona": T("doc_inspect"),
                   "anteprima": T("render_preview"), "inserisci": T("doc_place", "path")},
    "lightcraft": {"nuovo": NON_C_E("LightCraft lavora su una libreria: si importa, non si crea un documento"),
                   "apri": T("import", "paths", lista=True), "inserisci": T("import", "paths", lista=True),
                   "salva": NON_C_E("LightCraft salva da sola nella libreria; per un file usa «esporta»"),
                   "esporta": T("export", "path"), "ispeziona": T("doc_inspect"), "anteprima": T("render_preview")},
    "filmcraft": {"nuovo": C("command_run", "id", "file.newProject"), "apri": C("command_run", "id", "file.open", "path"),
                  "salva": C("command_run", "id", "file.save", "path"),
                  "esporta": C("command_run", "id", "file.exportMedia", "path"),
                  "ispeziona": T("doc_inspect"), "anteprima": T("render_preview"),
                  "inserisci": T("media_import", "paths", lista=True)},
    "effectcraft": {"nuovo": T("open_project", new=True), "apri": T("open_project", "path"),
                    "salva": T("save_project", "path"),
                    "esporta": PER_ESTENSIONE({"png": T("render_frame", "path"), "jpg": T("render_frame", "path")},
                                              lambda p, o: ("command_batch", {"steps": [
                                                  {"id": "renderQueue.add", "params": dict({"output": p}, **o)},
                                                  {"id": "renderQueue.render", "params": {"wait": True}}]})),
                    "ispeziona": T("doc_inspect"), "anteprima": T("render_preview"),
                    "inserisci": C("command_run", "id", "file.import", "paths", lista=True)},
    "designcraft": {"nuovo": T("new_document"), "apri": T("open_document", "path"), "salva": T("save_document", "path"),
                    "esporta": PER_ESTENSIONE({
                        "png": T("export_png", "path"),
                        "pdf": C("execute", "command", "file.exportPdf", "path"),
                        "idml": C("execute", "command", "file.exportIdml", "path"),
                        "epub": C("execute", "command", "file.exportEpub", "path"),
                        "html": C("execute", "command", "file.exportHtml", "path"),
                        "pptx": C("execute", "command", "file.exportPptx", "path"),
                        "txt": C("execute", "command", "file.exportText", "path"),
                        "rtf": C("execute", "command", "file.exportText", "path"),
                        "xml": C("execute", "command", "file.exportXml", "path")}, T("save_document", "path")),
                    "ispeziona": T("inspect_document"), "anteprima": T("render_page"),
                    "inserisci": T("place_image", "path")},
    "vectorcraft": {"nuovo": C("command_run", "id", "file.new"), "apri": T("open_file", "path"),
                    "salva": T("save_file", "path"), "esporta": T("export", "path"), "ispeziona": T("doc_inspect"),
                    "anteprima": T("render_preview"), "inserisci": C("command_run", "id", "file.place", "path")},
    "pdfcraft": {"nuovo": NON_C_E("PdfCraft non crea PDF vuoti: esporta in PDF da un'altra app, poi aprilo"),
                 "apri": T("doc_open", "path"), "salva": DOC("pdfcraft", "doc_save", "path"),
                 "esporta": DOC("pdfcraft", "doc_save", "path"),
                 "ispeziona": DOC("pdfcraft", "doc_inspect", obbligatorio=False),  # senza doc: tutti gli aperti
                 "anteprima": DOC("pdfcraft", "render_preview"),
                 "inserisci": NON_C_E("per unire PDF usa app_usa pdfcraft doc_combine {paths, out}")},
    "wordcraft": {"nuovo": T("new_document"), "apri": T("open_document", "path"), "salva": T("save_document", "path"),
                  "esporta": PER_ESTENSIONE({"pdf": C("execute", "command", "file.exportPdf", "path"),
                                             "png": C("execute", "command", "file.exportPng", "path")},
                                            T("save_document", "path")),
                  "ispeziona": T("inspect_document"), "anteprima": T("render_page"),
                  "inserisci": C("execute", "command", "insert.picture", "path")},
    "deckcraft": {"nuovo": T("new_presentation"), "apri": T("open_presentation", "path"),
                  "salva": T("save_presentation", "path"), "esporta": T("export", "path"),
                  "ispeziona": T("inspect_document"), "anteprima": T("render_slide"),
                  "inserisci": T("insert_picture", "path")},
    "gridcraft": {"nuovo": T("new_workbook"), "apri": T("open_workbook", "path"), "salva": T("save_workbook", "path"),
                  "esporta": PER_ESTENSIONE({"pdf": C("execute_command", "command", "file.exportPdf", "path"),
                                             "csv": C("execute_command", "command", "file.exportCsv", "path"),
                                             "html": C("execute_command", "command", "file.exportHtml", "path")},
                                            T("save_workbook", "path")),
                  "ispeziona": T("inspect_workbook"),
                  "anteprima": lambda p, o: ("screenshot", dict({"path": p or "_regia/anteprime/gridcraft.png"}, **o)),
                  "inserisci": C("execute_command", "command", "insert.picture", "path")},
    "cadcraft": {"nuovo": T("new_drawing"), "apri": T("open", "path"), "salva": T("save", "path"),
                 "esporta": C("execute", "command", "export", "path"), "ispeziona": T("inspect_drawing"),
                 "anteprima": T("render"),
                 "inserisci": NON_C_E("CADCraft non sa ancora inserire immagini («attach: not available yet»)")},
    "soundcraft": {"nuovo": T("new_session"), "apri": T("open_session", "path"), "salva": T("save_session", "path"),
                   "esporta": T("bounce_mix", "path"), "ispeziona": T("inspect_session"),
                   "anteprima": NON_C_E("SoundCraft senza finestra non produce un'immagine: usa «ispeziona»"),
                   "inserisci": T("import_audio", "path")},
    "figcraft": {"nuovo": C("run_command", "command", "file.new"), "apri": T("open_file", "path"),
                 "salva": T("save_file", "path"), "esporta": T("export", "path"), "ispeziona": T("inspect_document"),
                 "anteprima": T("screenshot"), "inserisci": C("run_command", "command", "image.place", "path")},
}
NOMI_VERBI = ["nuovo", "apri", "salva", "esporta", "ispeziona", "anteprima", "inserisci"]


def traduci_verbo(app, verbo, percorso=None, opzioni=None):
    if app not in VERBI:
        raise ValueError("app sconosciuta: %s" % app)
    if verbo not in VERBI[app]:
        raise ValueError("verbo sconosciuto: %s (validi: %s)" % (verbo, ", ".join(NOMI_VERBI)))
    opz = dict(opzioni or {})
    # le opzioni sono piatte: chi le annida in {"params": {...}} o {"arguments": {...}} (unica chiave) viene spianato,
    # perché i costruttori C(...) le mettono già dentro «params» (O4: params.params → «unknown parameter»).
    if len(opz) == 1:
        (k, v), = opz.items()
        if k in ("params", "arguments") and isinstance(v, dict):
            opz = dict(v)
    return VERBI[app][verbo](percorso, opz)


def _nome_verbo(fn, percorso="x/esempio.png"):
    """strumento(comando) dietro a un costruttore; per PER_ESTENSIONE tutti i casi: «pdf→execute(file.exportPdf), …»."""
    if hasattr(fn, "tabella"):
        casi = ["%s→%s" % (est, _nome_verbo(c, "x/esempio." + est)) for est, c in fn.tabella.items()]
        return ", ".join(casi) + ", altrimenti " + _nome_verbo(fn.altrimenti, "x/esempio")
    if hasattr(fn, "strumento"):
        return fn.strumento
    s, a = fn(percorso, {})
    cmd = a.get("id") or a.get("command")
    return s + ("(%s)" % cmd if isinstance(cmd, str) else "")


def tabella_verbi():
    """Per ogni app e verbo, lo strumento vero (mostra le incoerenze dei nomi)."""
    out = {}
    for app, vv in VERBI.items():
        riga = {}
        for v in NOMI_VERBI:
            try:
                riga[v] = _nome_verbo(vv[v])
            except ValueError as e:
                riga[v] = "— " + str(e)
        out[app] = riga
    return out


# ---------- ricerca delle funzioni ----------
def _piano(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _parole(s):
    return re.findall(r"[a-z0-9]+", _piano(s))


def _chiave_it(s):
    return s.strip().rstrip("…").rstrip(".").strip()


def _carica_it():
    """{app|common: {inglese_senza_puntini: italiano}} dai TSV di craft-i18n."""
    res = {}
    cartella = os.path.join(DATI, "i18n_it")
    if not os.path.isdir(cartella):
        return res
    for f in os.listdir(cartella):
        if not f.endswith(".tsv"):
            continue
        d = {}
        with open(os.path.join(cartella, f), encoding="utf-8") as fh:
            for riga in fh:
                if riga.startswith("#") or "\t" not in riga:
                    continue
                parti = riga.rstrip("\n").split("\t")
                if len(parti) >= 3 and not parti[0].startswith("@"):
                    d.setdefault(_chiave_it(parti[1]), _chiave_it(parti[2]))
        res[f[:-4]] = d
    return res


_INDICE = None


def indice():
    global _INDICE
    if _INDICE is not None:
        return _INDICE
    comandi = json.load(open(os.path.join(DATI, "comandi.json"), encoding="utf-8"))
    schemi = json.load(open(os.path.join(DATI, "schemi.json"), encoding="utf-8"))
    it = _carica_it()
    voci = []

    def it_di(app, testo):
        k = _chiave_it(testo)
        return it.get(app, {}).get(k) or it.get("common", {}).get(k) or ""

    for app, cs in comandi.items():
        for c in cs:
            menu_it = " › ".join(filter(None, (it_di(app, m) for m in c["menu"].split(" › ")))) if c["menu"] else ""
            voci.append({"app": app, "tipo": "comando", "id": c["id"], "etichetta": c["label"],
                         "etichetta_it": it_di(app, c["label"]), "menu": c["menu"], "menu_it": menu_it,
                         "params": c["params"][:300]})
    for app, r in schemi.items():
        for t in r.get("tools", []):
            voci.append({"app": app, "tipo": "strumento", "id": t["name"], "etichetta": t.get("title") or "",
                         "etichetta_it": "", "menu": "", "menu_it": "",
                         "params": (t.get("description") or "")[:300]})
    for v in voci:
        v["_t"] = {"forte": set(_parole(v["etichetta"] + " " + v["etichetta_it"] + " " + v["id"].replace(".", " ").replace("_", " ")
                                     + " " + re.sub(r"([a-z])([A-Z])", r"\1 \2", v["id"]))),
                   "medio": set(_parole(v["menu"] + " " + v["menu_it"])),
                   "debole": set(_parole(v["params"]))}
    _INDICE = {"voci": voci, "lingue_it": sorted(k for k in it if k != "common")}
    return _INDICE


def _corrisponde(q, parole):
    if q in parole:
        return 1.0
    radice = q[:max(4, len(q) - 2)] if len(q) >= 5 else None
    if radice and any(w.startswith(radice) for w in parole):
        return 0.7
    return 0.0


# O15: sinonimi italiani → inglesi, applicati alle parole della ricerca prima del confronto (servono dove l'app non
# ha la traduzione di craft-i18n, es. GridCraft, e per gli strumenti MCP, che hanno solo nomi inglesi).
# Ogni parola cerca sé stessa OPPURE uno dei suoi sinonimi: vale il confronto migliore.
SINONIMI = {
    "somma": ["sum", "autosum"], "media": ["average", "mean"], "tabella": ["table"], "grafico": ["chart", "graph"],
    "esporta": ["export"], "salva": ["save"], "apri": ["open"], "unisci": ["combine", "merge"], "dividi": ["split"],
    "pagina": ["page"], "intestazione": ["header"], "immagine": ["image", "picture"], "testo": ["text"],
    "stile": ["style"], "cerca": ["find", "search"], "trova": ["find", "search"], "sostituisci": ["replace"],
    "ruota": ["rotate"], "ritaglia": ["crop"], "colonna": ["column"], "riga": ["row"], "cella": ["cell"],
    "formula": ["formula"], "grassetto": ["bold"], "corsivo": ["italic"], "allinea": ["align"], "margine": ["margin"],
    "numero": ["number"], "barre": ["bar"], "barra": ["bar"], "paragrafo": ["paragraph", "para"],
    "documento": ["document", "doc"], "informazioni": ["info", "information", "properties"], "estrai": ["extract"],
    "metadati": ["metadata"], "titolo": ["title", "heading"], "autore": ["author"], "valuta": ["currency"],
    "inserisci": ["insert"],
}
# frasi che vanno lette insieme (prima delle parole singole): «piè» da solo sarebbe «pie» (grafico a torta)
FRASI = {"pie di pagina": [["footer"]], "salto di pagina": [["break"], ["page", "pagina"]],
         "salto pagina": [["break"], ["page", "pagina"]], "numero di pagina": [["number", "numero"], ["page", "pagina"]]}
VUOTE = {"il", "lo", "la", "di", "da", "in", "un", "una", "the", "of", "a", "to", "con", "per", "e", "come", "dove", "si"}
BONUS_STRUMENTO = 0.3  # O15: a parità, lo strumento MCP (chiamabile per nome) passa davanti al comando di menu


def _concetti(testo):
    """La ricerca diventa una lista di concetti; ogni concetto è l'elenco delle forme accettate (italiano + sinonimi)."""
    t = " ".join(_parole(testo))
    t = re.sub(r"\bdove si trova\b", " ", t)
    concetti = []
    for frase, cc in FRASI.items():
        if re.search(r"\b%s\b" % frase, t):
            concetti += cc
            t = re.sub(r"\b%s\b" % frase, " ", t)
    for q in t.split():
        if len(q) > 1 and q not in VUOTE:
            concetti.append([q] + SINONIMI.get(q, []))
    return concetti


def _esatta(q, parole):
    """Per i sinonimi inglesi: parola esatta o col plurale in -s, senza radici (O15: «currency» non deve valere «current»)."""
    return 1.0 if (q in parole or q + "s" in parole) else 0.0


# O16-bis: una parola che nomina un'app (nome o alias breve) diventa il filtro `app`, se non è già dato
# («metadati pdf» = «metadati» dentro PdfCraft: la parola «pdf» non compare negli strumenti di PdfCraft).
ALIAS_APP = {"pdf": "pdfcraft", "word": "wordcraft", "excel": "gridcraft", "foglio": "gridcraft",
             "powerpoint": "deckcraft", "slide": "deckcraft", "photoshop": "photocraft", "foto": "photocraft",
             "illustrator": "vectorcraft", "vettoriale": "vectorcraft", "indesign": "designcraft",
             "impaginazione": "designcraft", "cad": "cadcraft", "autocad": "cadcraft", "video": "filmcraft",
             "premiere": "filmcraft", "audio": "soundcraft", "protools": "soundcraft", "figma": "figcraft",
             "lightroom": "lightcraft", "aftereffects": "effectcraft"}
# O16-ter: gli alias che sono anche formati di file non filtrano se la ricerca ha un verbo di uscita/ingresso
# («esporta pdf» = esportare in PDF da qualunque app, non «esporta» dentro PdfCraft). «effetti» tolto: parola comune.
ALIAS_FORMATO = {"pdf", "foto", "video", "audio"}
VERBI_IO = {"esporta", "salva", "converti", "stampa", "apri", "importa", "export", "save", "print", "open", "import"}


def _app_dalla_ricerca(testo):
    """(app, testo senza quella parola) se una parola è il nome o l'alias di un'app; altrimenti (None, testo)."""
    parole = _parole(testo)
    io = bool(VERBI_IO & set(parole))
    for i, w in enumerate(parole):
        if io and w in ALIAS_FORMATO:
            continue
        a = w if w in APP else ALIAS_APP.get(w)
        if a:
            return a, " ".join(parole[:i] + parole[i + 1:])
    return None, testo


def cerca(testo, app=None, limite=15):
    idx = indice()
    if not app:
        app, testo = _app_dalla_ricerca(testo)
        if app and not _concetti(testo):  # solo il nome dell'app: i suoi primi strumenti
            return [dict({k: x for k, x in v.items() if not k.startswith("_")}, punti=0.0)
                    for v in idx["voci"] if v["app"] == app and v["tipo"] == "strumento"][:limite]
    qs = _concetti(testo)
    if not qs:
        return []
    ris = []
    for v in idx["voci"]:
        if app and v["app"] != app:
            continue
        punti, coperte = 0.0, 0
        for forme in qs:
            m = max(max(3 * f(q, v["_t"]["forte"]), 1.5 * f(q, v["_t"]["medio"]), 0.5 * f(q, v["_t"]["debole"]))
                    for q, f in zip(forme, [_corrisponde] + [_esatta] * (len(forme) - 1)))
            punti += m
            coperte += m > 0
        if coperte:
            punti *= coperte / len(qs)  # premia chi copre tutte le parole
            if v["tipo"] == "comando" and v["etichetta_it"]:
                punti += 0.1
            if v["tipo"] == "strumento":
                punti += BONUS_STRUMENTO
            ris.append((punti, v))
    ris.sort(key=lambda x: -x[0])
    return [dict({k: x for k, x in v.items() if not k.startswith("_")}, punti=round(p, 2)) for p, v in ris[:limite]]
