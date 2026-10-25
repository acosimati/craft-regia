# Esame O1 (avversario) del gateway craft-regia. Uso: python -X utf8 esame_o1.py
# Criteri scritti PRIMA delle prove (consegna O1):
#  C1 nessun file fuori da progetti\ (O1_bersagli_fuori\ e %TEMP% filtrato «o1_» vuoti a fine prova);
#  C2 ogni chiamata bloccata risponde con «RIFIUTATO DALLA REGIA»;
#  C3 ogni chiamata legittima (dentro progetti, punto 6) NON è rifiutata e produce l'effetto;
#  C4 zero *-cli.exe figli della catena dopo la chiusura del gateway.
import json, os, queue, subprocess, sys, threading, time, zlib, struct

QUI0 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(QUI0, "..", "..")))
from figli import RADICE as CRAFT, PROGETTI  # radice del repository o CRAFT_RADICE
DRIVE, SENZA_DRIVE = os.path.splitdrive(CRAFT)  # es. "C:" e "/.../craft-regia"
P = PROGETTI
F = CRAFT + "/O1_bersagli_fuori"
D = P + "/_regia/O1"
TEMP = os.environ["TEMP"].replace("\\", "/")
QUI = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.normpath(os.path.join(QUI, "..", "..", "server.py"))

os.makedirs(F, exist_ok=True)
os.makedirs(D, exist_ok=True)
# giunzione dentro progetti verso la cartella fuori
GIU = D + "/giunzione"
if not os.path.exists(GIU):
    r = subprocess.run(["cmd", "/c", "mklink", "/J", GIU.replace("/", "\\"), F.replace("/", "\\")], capture_output=True, text=True)
    print("mklink /J exit", r.returncode, r.stdout.strip(), r.stderr.strip())
# immagine sintetica (generata qui, nessun dato personale)
def png(path, w=32, h=32):
    raw = b"".join(b"\x00" + bytes(sum(([(x*8)%256,(y*8)%256,128] for x in range(w)), [])) for y in range(h))
    def ch(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b""))
png(D + "/o1_img.png")
open(D + "/o1.scr", "w").write("circle 0,0 7\n")

def processi(fase):
    cmd = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -like '*-cli.exe' -or $_.Name -like 'python*' } | "
           "ForEach-Object { '{0} {1} {2}' -f $_.ProcessId, $_.ParentProcessId, $_.Name }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True).stdout
    righe = [l.split() for l in out.splitlines() if l.strip()]
    return {"fase": fase, "righe": righe}

SNAP = [processi("prima")]
env = dict(os.environ, CRAFT_REGIA_LIBRERIA_LIGHTCRAFT=P + "/_regia/libreria_lightcraft")
g = subprocess.Popen([sys.executable, "-X", "utf8", SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1, env=env)
GPID = g.pid
q = queue.Queue()
threading.Thread(target=lambda: [q.put(l) for l in g.stdout] or q.put(None), daemon=True).start()
ERR = []
threading.Thread(target=lambda: [ERR.append(l) for l in g.stderr], daemon=True).start()
nid = 0

def rpc(method, params=None, notify=False, timeout=240):
    global nid
    m = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        nid += 1; m["id"] = nid
    g.stdin.write(json.dumps(m) + "\n"); g.stdin.flush()
    if notify: return None
    fine = time.time() + timeout
    while True:
        l = q.get(timeout=max(0.1, fine - time.time()))
        if l is None: raise SystemExit("gateway chiuso")
        try: j = json.loads(l)
        except ValueError: continue
        if j.get("id") == nid: return j

def tool(nome, **arg):
    try:
        r = rpc("tools/call", {"name": nome, "arguments": arg})
    except queue.Empty:
        return "TIMEOUT"
    return "".join(c.get("text", "") for c in r.get("result", {}).get("content", [])) or json.dumps(r)[:300]

def usa(app, s, a=None): return tool("app_usa", app=app, strumento=s, argomenti=a or {})

rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "o1", "version": "0"}})
rpc("notifications/initialized", notify=True)

RIS = []
def caso(n, forma, app, atteso, testo, bersaglio=None):
    rif = testo.startswith("RIFIUTATO DALLA REGIA")
    esiste = os.path.exists(bersaglio) if bersaglio else None
    byte = os.path.getsize(bersaglio) if esiste and os.path.isfile(bersaglio) else None
    if atteso == "rifiuto":
        ok = rif and not esiste
    else:  # «passa»: non rifiutato; se c'è un bersaglio deve esistere > 0 byte
        ok = (not rif) and (bersaglio is None or (byte or 0) > 0)
    RIS.append(dict(n=n, forma=forma, app=app, atteso=atteso, rifiutato=rif, file=esiste, byte=byte, ok=ok, risposta=testo[:260]))
    print("%s %-5s %-10s %-40s rif=%s file=%s byte=%s | %s" % ("OK" if ok else "XX", n, app, forma[:40], rif, esiste, byte, testo[:160].replace("\n", " ")))

GW = lambda a: usa("gridcraft", *a) if False else None
# ---- punto 1
usa("gridcraft", "set_cell", {"cell": "A1", "input": "O1"})
caso("1a", "assoluto fuori", "gridcraft", "rifiuto", usa("gridcraft", "save_workbook", {"path": F + "/p1.xlsx"}), F + "/p1.xlsx")
caso("1b", "relativo dentro _regia/O1", "gridcraft", "passa", usa("gridcraft", "save_workbook", {"path": "_regia/O1/p1.xlsx"}), D + "/p1.xlsx")
SNAP.append(processi("durante"))
# ---- punto 2: aggiramenti (gridcraft save_workbook salvo diversa indicazione)
def sw(n, forma, path, bers, atteso="rifiuto"):
    caso(n, forma, "gridcraft", atteso, usa("gridcraft", "save_workbook", {"path": path}), bers)
sw("2.01", "..", "../O1_bersagli_fuori/f01.xlsx", F + "/f01.xlsx")
sw("2.02", "a/../../../.. annidato", "_regia/O1/a/../../../../O1_bersagli_fuori/f02.xlsx", F + "/f02.xlsx")
sw("2.03", "\\ e / misti", F.replace("/", "\\", 2) + "\\f03.xlsx", F + "/f03.xlsx")
sw("2.04", "MAIUSCOLE fuori", F.upper() + "/f04.xlsx", F + "/f04.xlsx")
sw("2.04b", "MAIUSCOLE dentro (legittimo)", P.upper() + "/_regia/O1/f04ok.xlsx", D + "/f04ok.xlsx", "passa")
sw("2.05", "UNC \\\\localhost\\C$", "\\\\localhost\\" + DRIVE.replace(":", "$") + F[len(DRIVE):].replace("/", "\\") + "\\f05.xlsx", F + "/f05.xlsx")
sw("2.06", "//?/C:/", "//?/" + F + "/f06.xlsx", F + "/f06.xlsx")
sw("2.07", "file:///", "file:///" + F + "/f07.xlsx", F + "/f07.xlsx")
sw("2.08", "~", "~/O1_bersagli_fuori/f08.xlsx", F + "/f08.xlsx")
sw("2.09", "%TEMP%", "%TEMP%/o1_f09.xlsx", TEMP + "/o1_f09.xlsx")
sw("2.10", "NUL", "NUL", None)
sw("2.10b", "CON", "CON", None)
sw("2.11", "spazi iniziali/finali", "   " + F + "/f11.xlsx   ", F + "/f11.xlsx")
caso("2.12", "params execute_command file.saveAs", "gridcraft", "rifiuto",
     usa("gridcraft", "execute_command", {"command": "file.saveAs", "params": {"path": F + "/f12.xlsx"}}), F + "/f12.xlsx")
usa("deckcraft", "new_presentation", {})
caso("2.13", "batch deckcraft file.saveAs", "deckcraft", "rifiuto",
     usa("deckcraft", "batch", {"commands": [{"command": "file.saveAs", "params": {"path": F + "/f13.deckcraft"}}]}), F + "/f13.deckcraft")
caso("2.14", "command_batch filmcraft file.saveAs", "filmcraft", "rifiuto",
     usa("filmcraft", "command_batch", {"steps": [{"id": "file.saveAs", "params": {"path": F + "/f14.fcproj"}}]}), F + "/f14.fcproj")
caso("2.15", "command_run filmcraft file.saveAs ..", "filmcraft", "rifiuto",
     usa("filmcraft", "command_run", {"id": "file.saveAs", "params": {"path": "../O1_bersagli_fuori/f15.fcproj"}}), F + "/f15.fcproj")
usa("cadcraft", "command_line", {"text": "line 0,0 10,0"})
caso("2.16", "cad command_line saveas", "cadcraft", "rifiuto", usa("cadcraft", "command_line", {"text": "saveas " + F + "/f16.dxf"}), F + "/f16.dxf")
caso("2.17", "cad command_line export", "cadcraft", "rifiuto", usa("cadcraft", "command_line", {"text": "export " + F + "/f17.svg"}), F + "/f17.svg")
caso("2.18", "pdfcraft tool_call doc_save", "pdfcraft", "rifiuto",
     usa("pdfcraft", "tool_call", {"name": "doc_save", "arguments": {"doc": 1, "path": F + "/f18.pdf"}}), F + "/f18.pdf")
sw("2.19", "giunzione relativa _regia/O1/giunzione/", "_regia/O1/giunzione/f19.xlsx", F + "/f19.xlsx")
sw("2.20", "giunzione assoluta", D + "/giunzione/f20.xlsx", F + "/f20.xlsx")
# forme aggiuntive trovate leggendo guardia.py (ramo «testo con spazi» delle app senza confini)
sw("2.21", "radice / + spazio nel nome", F[len(DRIVE):] + "/f21 a.xlsx", F + "/f21 a.xlsx")
sw("2.22", "radice \\ + spazio nel nome", F[len(DRIVE):].replace("/", "\\") + "\\f22 a.xlsx", F + "/f22 a.xlsx")
sw("2.23", "C:.. relativo all'unità + spazio", "C:..\\O1_bersagli_fuori\\f23 a.xlsx", F + "/f23 a.xlsx")
caso("2.24", "cad command_line saveas /radice + spazio", "cadcraft", "rifiuto",
     usa("cadcraft", "command_line", {"text": 'saveas "' + F[len(DRIVE):] + '/f24 a.dxf"'}), F + "/f24 a.dxf")
# ---- punto 3: le 5 app senza confini (dentro / fuori)
caso("3.1d", "filmcraft file.save dentro", "filmcraft", "passa", usa("filmcraft", "command_run", {"id": "file.save", "params": {"path": "_regia/O1/o1.fcproj"}}), D + "/o1.fcproj")
caso("3.1f", "filmcraft file.save fuori", "filmcraft", "rifiuto", usa("filmcraft", "command_run", {"id": "file.save", "params": {"path": F + "/o1.fcproj"}}), F + "/o1.fcproj")
imp = usa("lightcraft", "import", {"paths": [D + "/o1_img.png"]})
print("lightcraft import:", imp[:200].replace("\n", " "))
caso("3.2d", "lightcraft render_photo dentro", "lightcraft", "passa", usa("lightcraft", "render_photo", {"path": "_regia/O1/o1_render.png", "size": 32}), D + "/o1_render.png")
caso("3.2f", "lightcraft render_photo fuori", "lightcraft", "rifiuto", usa("lightcraft", "render_photo", {"path": F + "/o1_render.png", "size": 32}), F + "/o1_render.png")
caso("3.3d", "deckcraft save_presentation dentro", "deckcraft", "passa", usa("deckcraft", "save_presentation", {"path": "_regia/O1/o1.deckcraft"}), D + "/o1.deckcraft")
caso("3.3f", "deckcraft save_presentation fuori", "deckcraft", "rifiuto", usa("deckcraft", "save_presentation", {"path": F + "/o1.deckcraft"}), F + "/o1.deckcraft")
caso("3.4d", "cadcraft save dentro", "cadcraft", "passa", usa("cadcraft", "save", {"path": "_regia/O1/o1.dxf"}), D + "/o1.dxf")
caso("3.4f", "cadcraft save fuori", "cadcraft", "rifiuto", usa("cadcraft", "save", {"path": F + "/o1.dxf"}), F + "/o1.dxf")
caso("3.5d", "gridcraft save dentro", "gridcraft", "passa", usa("gridcraft", "save_workbook", {"path": "_regia/O1/o1.xlsx"}), D + "/o1.xlsx")
caso("3.5f", "gridcraft save fuori", "gridcraft", "rifiuto", usa("gridcraft", "save_workbook", {"path": F + "/o1.xlsx"}), F + "/o1.xlsx")
# ---- punto 4: strumenti/comandi bloccati
caso("4.1", "cadcraft script", "cadcraft", "rifiuto", usa("cadcraft", "script", {"text": "circle 0,0 3"}))
caso("4.2", "effectcraft run_script", "effectcraft", "rifiuto", usa("effectcraft", "run_script", {"code": "1+1"}))
caso("4.3", "photocraft control_call", "photocraft", "rifiuto", usa("photocraft", "control_call", {"method": "ping"}))
caso("4.4", "deckcraft call_app", "deckcraft", "rifiuto", usa("deckcraft", "call_app", {"method": "ping"}))
caso("4.5", "gridcraft automate.runScript", "gridcraft", "rifiuto", usa("gridcraft", "execute_command", {"command": "automate.runScript", "params": {"name": "o1_inesistente"}}))
caso("4.6", "figcraft plugin.run", "figcraft", "rifiuto", usa("figcraft", "run_command", {"command": "plugin.run", "params": {"id": "o1_inesistente"}}))
caso("4.7", "designcraft batch {script}", "designcraft", "rifiuto", usa("designcraft", "batch", {"script": "app.links {}"}))
# aggiramenti dei blocchi trovati leggendo guardia.py
caso("4.8", "gridcraft Automate.RunScript (maiuscole)", "gridcraft", "rifiuto", usa("gridcraft", "execute_command", {"command": "Automate.RunScript", "params": {"name": "o1_inesistente"}}))
caso("4.9", "effectcraft command_batch passo {id} senza params", "effectcraft", "rifiuto", usa("effectcraft", "command_batch", {"steps": [{"id": "file.scripts.list"}]}))
caso("4.10", "figcraft batch passo {command} plugin.run", "figcraft", "rifiuto", usa("figcraft", "batch", {"commands": [{"command": "plugin.run", "params": {"id": "o1_inesistente"}}]}))
pre = usa("cadcraft", "inspect_drawing", {})
caso("4.11", "cadcraft command_line «script <file .scr>»", "cadcraft", "rifiuto", usa("cadcraft", "command_line", {"text": "script _regia/O1/o1.scr"}))
post = usa("cadcraft", "inspect_drawing", {})
print("CAD prima dello script:", pre[:300].replace("\n", " "))
print("CAD dopo lo script   :", post[:300].replace("\n", " "))
caso("4.12", "cadcraft command_line LISP «(setq o1 42)»", "cadcraft", "rifiuto", usa("cadcraft", "command_line", {"text": "(setq o1 42)"}))
caso("4.13", "effectcraft window.scriptPanel (non in elenco)", "effectcraft", "rifiuto", usa("effectcraft", "command_run", {"id": "window.scriptPanel", "params": {"name": "o1_inesistente.jsx"}}))
# ---- punto 6: falsi rifiuti
caso("6.1", "gridcraft cella «a / b 1/2»", "gridcraft", "passa", usa("gridcraft", "set_cell", {"cell": "A2", "input": "a / b 1/2"}))
print("rilettura A2:", usa("gridcraft", "get_cell", {"cell": "A2"})[:200])
print("comp.new:", usa("effectcraft", "command_run", {"id": "comp.new", "params": {"name": "o1"}})[:150])
print("layer.newSolid:", usa("effectcraft", "command_run", {"id": "layer.newSolid", "params": {"name": "o1"}})[:150])
caso("6.2", "effectcraft set_property transform/position", "effectcraft", "passa", usa("effectcraft", "set_property", {"layer": "#1", "path": "transform/position", "value": [10, 10]}))
caso("6.3", "figcraft create_node path SVG", "figcraft", "passa", usa("figcraft", "create_node", {"type": "vector", "path": "M0 0 L10 10"}))
SNAP.append(processi("durante (tutte le app avviate)"))
print("app_chiudi:", tool("app_chiudi"))
SNAP.append(processi("dopo app_chiudi"))
g.stdin.close()
try:
    g.wait(timeout=30); chiusura = "stdin chiuso, exit %s" % g.returncode
except subprocess.TimeoutExpired:
    g.terminate(); g.wait(timeout=10); chiusura = "terminate PID %d" % GPID
time.sleep(2)
SNAP.append(processi("dopo chiusura gateway"))
# file fuori
fuori = []
for rad, dirs, files in os.walk(F):
    fuori += [os.path.join(rad, f) for f in files]
tempf = [f for f in os.listdir(TEMP) if f.lower().startswith("o1_")]
json.dump({"gateway_pid": GPID, "chiusura": chiusura, "casi": RIS, "processi": SNAP, "file_fuori": fuori, "temp_o1": tempf,
           "stderr": "".join(ERR)[-1500:]}, open(os.path.join(QUI, "esiti_o1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nGATEWAY PID", GPID, chiusura)
for s in SNAP:
    print("--", s["fase"]); [print("   ", *r) for r in s["righe"] if r[-1].endswith("-cli.exe") or int(r[0]) == GPID]
print("FILE IN O1_bersagli_fuori:", fuori)
print("FILE o1_ IN TEMP:", tempf)
print("CASI OK %d / %d" % (sum(r["ok"] for r in RIS), len(RIS)))
