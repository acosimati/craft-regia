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
                 "apri": T("doc_open", "path"), "salva": T("doc_save", "path"), "esporta": T("doc_save", "path"),
                 "ispeziona": T("doc_inspect"), "anteprima": T("render_preview"),
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


def tabella_verbi():
    """Per ogni app e verbo, lo strumento vero (mostra le incoerenze dei nomi)."""
    out = {}
    for app, vv in VERBI.items():
        riga = {}
        for v in NOMI_VERBI:
            try:
                s, a = vv[v]("x/esempio.png", {})
                cmd = a.get("id") or a.get("command")
                riga[v] = s + ("(%s)" % cmd if isinstance(cmd, str) else "")
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


def cerca(testo, app=None, limite=15):
    idx = indice()
    qs = [q for q in _parole(testo) if len(q) > 1 and q not in {"il", "lo", "la", "di", "da", "in", "un", "una", "the", "of", "a", "to", "con", "per", "e", "come", "dove", "si", "trova"}]
    if not qs:
        return []
    ris = []
    for v in idx["voci"]:
        if app and v["app"] != app:
            continue
        punti, coperte = 0.0, 0
        for q in qs:
            m = max(3 * _corrisponde(q, v["_t"]["forte"]), 1.5 * _corrisponde(q, v["_t"]["medio"]),
                    0.5 * _corrisponde(q, v["_t"]["debole"]))
            punti += m
            coperte += m > 0
        if coperte:
            punti *= coperte / len(qs)  # premia chi copre tutte le parole
            if v["tipo"] == "comando" and v["etichetta_it"]:
                punti += 0.1
            ris.append((punti, v))
    ris.sort(key=lambda x: -x[0])
    return [dict({k: x for k, x in v.items() if not k.startswith("_")}, punti=round(p, 2)) for p, v in ris[:limite]]
