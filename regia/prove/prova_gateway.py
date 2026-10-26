# Prova dal vero: avvia craft-regia su stdio come farebbe Claude e fa le chiamate che discriminano.
# Uso: python -X utf8 prove/prova_gateway.py
import json, os, subprocess, sys, time

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, QUI)
from figli import RADICE, PROGETTI  # dalla radice del repository o da CRAFT_RADICE / CRAFT_PROGETTI
PROGETTI = os.path.normpath(PROGETTI)
FUORI = os.path.normpath(os.path.join(RADICE, "FUORI_regia_prova.xlsx"))  # nella radice, non in progetti/
FUORI_CAD = os.path.normpath(os.path.join(os.path.dirname(RADICE), "FUORI_regia.dxf"))  # fuori dalla radice
DENTRO_REL = "_regia/prova_gateway.xlsx"
DENTRO = os.path.join(PROGETTI, DENTRO_REL)
for f in (FUORI, DENTRO):
    if os.path.exists(f):
        os.remove(f)

p = subprocess.Popen([sys.executable, "-X", "utf8", os.path.join(QUI, "server.py")], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
nid = 0
# O10: lo stderr del gateway (log di FastMCP, uno per richiesta) va svuotato mentre la prova corre: se la pipe si
# riempie, il gateway resta bloccato in scrittura e la prova si appende (misurato il 25/10 con 15 chiamate).
import threading
_righe_err = []
threading.Thread(target=lambda: [_righe_err.append(r) for r in p.stderr], daemon=True).start()


def rpc(method, params=None, notify=False):
    global nid
    m = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        nid += 1
        m["id"] = nid
    p.stdin.write(json.dumps(m) + "\n")
    p.stdin.flush()
    if notify:
        return
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("gateway chiuso: " + "".join(_righe_err[-20:]))
        j = json.loads(line)
        if j.get("id") == nid:
            return j


def tool(nome, **arg):
    t0 = time.time()
    r = rpc("tools/call", {"name": nome, "arguments": arg})
    testo = "".join(c.get("text", "") for c in r.get("result", {}).get("content", []))
    print("\n### %s %s  (%.1f s)\n%s" % (nome, json.dumps(arg, ensure_ascii=False)[:120], time.time() - t0, testo[:1200]))
    return testo


r = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "prova", "version": "0"}})
print("initialize:", r["result"]["serverInfo"])
rpc("notifications/initialized", notify=True)
tools = rpc("tools/list")["result"]["tools"]
print("strumenti del gateway:", [t["name"] for t in tools])

esiti = {}
tool("suite_catalogo")
tool("suite_cerca", testo="sfocatura gaussiana", limite=3)
tool("suite_cerca", testo="tabella pivot", limite=3)
tool("app_strumenti", app="gridcraft", filtro="save")
tool("app_usa", app="gridcraft", strumento="set_cell", argomenti={"cell": "A1", "input": "regia"})
t = tool("app_usa", app="gridcraft", strumento="save_workbook", argomenti={"path": FUORI.replace("\\", "/")})
esiti["fuori_rifiutato"] = t.startswith("RIFIUTATO") and not os.path.exists(FUORI)
t = tool("app_usa", app="gridcraft", strumento="execute_command",
         argomenti={"command": "file.saveAs", "params": {"path": "../FUORI_regia_prova2.xlsx"}})
esiti["fuori_via_comando_rifiutato"] = t.startswith("RIFIUTATO") and not os.path.exists(os.path.join(RADICE, "FUORI_regia_prova2.xlsx"))
t = tool("app_usa", app="gridcraft", strumento="execute_command", argomenti={"command": "automate.runScript", "params": {"name": "x"}})
esiti["script_bloccato"] = t.startswith("RIFIUTATO")
t = tool("app_verbo", app="gridcraft", verbo="salva", percorso=DENTRO_REL)
esiti["dentro_riuscito"] = (not t.startswith("RIFIUTATO")) and os.path.exists(DENTRO) and os.path.getsize(DENTRO) > 0
tool("app_verbo", app="gridcraft", verbo="ispeziona")
t = tool("app_usa", app="cadcraft", strumento="script", argomenti={"text": "line 0,0 1,1"})
esiti["cad_script_bloccato"] = t.startswith("RIFIUTATO")
t = tool("app_usa", app="cadcraft", strumento="command_line", argomenti={"text": "line 0,0 10,0 10,5 c"})
esiti["cad_linea_ok"] = "RIFIUTATO" not in t and "ERRORE" not in t
t = tool("app_verbo", app="cadcraft", verbo="salva", percorso="_regia/prova_gateway.dxf")
esiti["cad_salva_dentro"] = os.path.exists(os.path.join(PROGETTI, "_regia/prova_gateway.dxf"))
t = tool("app_verbo", app="cadcraft", verbo="salva", percorso=FUORI_CAD.replace("\\", "/"))
esiti["cad_fuori_rifiutato"] = t.startswith("RIFIUTATO") and not os.path.exists(FUORI_CAD)
# PhotoCraft con assoluto dentro progetti (dal 26/10, O18a, la regia lo passa assoluto con «/»)
tool("app_verbo", app="photocraft", verbo="nuovo", opzioni={"width": 64, "height": 64})
t = tool("app_verbo", app="photocraft", verbo="salva", percorso=PROGETTI.replace("\\", "/") + "/_regia/prova_gateway.png")
esiti["photo_assoluto_riscritto"] = os.path.exists(os.path.join(PROGETTI, "_regia/prova_gateway.png"))
tool("diario_scrivi", progetto="_regia", testo="prova del gateway eseguita", fase="revisione", app="gridcraft")
t = tool("diario_leggi", progetto="_regia")
esiti["diario"] = "prova del gateway" in t and "prova_gateway.xlsx" in t
t = tool("suite_verbi")
riga_word = next((r for r in t.splitlines() if r.startswith("| wordcraft ")), "")
print("O15 suite_verbi, wordcraft elenca exportPdf ed exportPng:", "exportPdf" in riga_word and "exportPng" in riga_word)
# O6: opzioni annidate spianate, e anteprima che arriva come blocco immagine vero
tool("app_verbo", app="vectorcraft", verbo="nuovo", opzioni={"params": {"width": 100, "height": 100}})
t = tool("app_verbo", app="vectorcraft", verbo="ispeziona")
esiti["nuovo_opzioni_annidate"] = '"width": 100.0' in t and '"height": 100.0' in t and "ERRORE" not in t
r = rpc("tools/call", {"name": "app_verbo", "arguments": {"app": "vectorcraft", "verbo": "anteprima"}})
cont = r.get("result", {}).get("content", [])
img = [c for c in cont if c.get("type") == "image"]
import base64
esiti["anteprima_blocco_immagine"] = (len(img) == 1 and img[0].get("mimeType") == "image/png"
                                      and base64.b64decode(img[0]["data"])[:8] == b"\x89PNG\r\n\x1a\n"
                                      and any(c.get("type") == "text" and "[regia:" in c["text"] for c in cont))
print("\n### anteprima: blocchi", [(c["type"], c.get("mimeType"), len(c.get("data", c.get("text", "")))) for c in cont])
# O10: app_strumenti mostra descrizioni, tipi e limiti dei parametri; `strumento` mostra la descrizione intera
t1 = tool("app_strumenti", app="vectorcraft", filtro="draw_path")
t2 = tool("app_strumenti", app="vectorcraft", strumento="draw_path")
riga_op = next((r for r in t1.splitlines() if r.strip().startswith("- opacity")), "")
esiti["strumenti_parametri_descritti"] = ("Opacity in %" in riga_op and "0..100" in riga_op
                                          and "Returns the new object id." in t2)
print("riga opacity:", riga_op)
# O15: PdfCraft, «salva» senza doc → prima del doc_open messaggio chiaro; dopo «apri» la regia usa l'ultimo doc da sola.
# Il PDF di partenza è un PDF minimo di una pagina scritto qui (nessun file esterno).
def pdf_minimo(path):
    oggetti = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 100] >>"]
    out, pos = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(oggetti, 1):
        pos.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(oggetti) + 1) + b"".join(b"%010d 00000 n \n" % x for x in pos)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(oggetti) + 1, xref)
    open(path, "wb").write(bytes(out))


SORGENTE_REL, COPIA_REL = "_regia/O15/origine.pdf", "_regia/O15/copia.pdf"
COPIA = os.path.join(PROGETTI, COPIA_REL)
os.makedirs(os.path.dirname(COPIA), exist_ok=True)
pdf_minimo(os.path.join(PROGETTI, SORGENTE_REL))
if os.path.exists(COPIA):
    os.remove(COPIA)
t0 = tool("app_verbo", app="pdfcraft", verbo="salva", percorso=COPIA_REL)
t1 = tool("app_verbo", app="pdfcraft", verbo="apri", percorso=SORGENTE_REL)
t2 = tool("app_verbo", app="pdfcraft", verbo="ispeziona")
t3 = tool("app_verbo", app="pdfcraft", verbo="salva", percorso=COPIA_REL)
esiti["pdf_salva_senza_doc"] = ("apri prima un PDF" in t0 and "ricordato" in t1 and "ERRORE" not in t2 + t3
                                and os.path.exists(COPIA) and os.path.getsize(COPIA) > 0)
t = tool("app_chiudi")
esiti["chiusura"] = "chiuso" in t

p.stdin.close()
p.wait(timeout=30)
err = "".join(_righe_err)
print("\n### stderr del gateway (ultime righe)\n" + "\n".join(err.splitlines()[-8:]))
print("\n### ESITI")
for k, v in esiti.items():
    print("  %s %s" % ("✓" if v else "✗", k))
sys.exit(0 if all(esiti.values()) else 1)
