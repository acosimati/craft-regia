# Prova a tavolino della guardia: nessuna app avviata. Uso: python -X utf8 prove/prova_guardia.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from guardia import esamina, Rifiuto
from figli import PROGETTI

P = PROGETTI  # dalla radice del repository o da CRAFT_RADICE / CRAFT_PROGETTI
FUORI = os.path.dirname(os.path.dirname(P)).replace("\\", "/").rstrip("/") + "/fuori.xlsx"  # fuori dalla radice
# (app, strumento, argomenti, atteso: True = passa, False = rifiutato)
CASI = [
    ("gridcraft", "save_workbook", {"path": FUORI}, False),
    ("gridcraft", "save_workbook", {"path": P + "/_regia/prova.xlsx"}, True),
    ("gridcraft", "save_workbook", {"path": "_regia/prova.xlsx"}, True),
    ("gridcraft", "save_workbook", {"path": "_regia/../../fuori.xlsx"}, False),
    ("gridcraft", "execute_command", {"command": "file.saveAs", "params": {"path": r"C:\Windows\x.xlsx"}}, False),
    ("gridcraft", "execute_command", {"command": "automate.runScript", "params": {"name": "x"}}, False),
    ("gridcraft", "set_cell", {"cell": "A1", "input": "a / b e 1/2"}, True),
    ("gridcraft", "set_cell", {"cell": "A1", "input": r"vedi D:\Dati\x"}, False),
    ("cadcraft", "command_line", {"text": "saveas /x.dwg"}, False),
    ("cadcraft", "command_line", {"text": "saveas ../x.dwg"}, False),
    ("cadcraft", "command_line", {"text": "line 0,0 10,0 10,5 c"}, True),
    ("cadcraft", "script", {"text": "line 0,0 1,1"}, False),
    ("cadcraft", "execute", {"command": "lisp", "params": {"code": "(+ 1 2)"}}, False),
    ("photocraft", "doc_save", {"path": P + "/_regia/a.png"}, True),
    ("photocraft", "doc_save", {"path": "//server/share/a.png"}, False),
    ("photocraft", "command_batch", {"steps": [{"id": "file.scripts.browse", "params": {"script": "x"}}]}, False),
    ("photocraft", "control_call", {"method": "x"}, False),
    ("deckcraft", "insert_picture", {"data": "/9j/4AAQSkZJRg", "x": 1}, True),
    ("effectcraft", "set_property", {"layer": 1, "path": "transform/position", "value": [1, 2]}, True),
    ("effectcraft", "run_script", {"code": "app"}, False),
    ("pdfcraft", "tool_call", {"name": "doc_save", "arguments": {"doc": 1, "path": "D:/x.pdf"}}, False),
    ("figcraft", "run_command", {"command": "plugin.run", "params": {"id": "x"}}, False),
    ("figcraft", "create_node", {"type": "vector", "path": "M0 0 L10 10"}, True),
    ("lightcraft", "import", {"paths": ["%USERPROFILE%/Pictures/a.jpg"]}, False),
    ("designcraft", "batch", {"script": "file.save {}"}, False),
    ("designcraft", "execute", {"command": "file.saveAs", "params": {"path": "C:/x.indd"}}, False),
    # O2: un caso per ogni buco di O1 (la giunzione 2.19 si prova solo dal vero) e i falsi rifiuti da evitare
    ("gridcraft", "save_workbook", {"path": "/srv/altrove/O1_bersagli_fuori/f21 a.xlsx"}, False),
    ("gridcraft", "save_workbook", {"path": r"\srv\altrove\O1_bersagli_fuori\f22 a.xlsx"}, False),
    ("gridcraft", "save_workbook", {"path": r"C:..\O1_bersagli_fuori\f23 a.xlsx"}, False),
    ("deckcraft", "run_command", {"command": "x", "params": {"title": "C:..\\fuori a.txt"}}, False),
    ("filmcraft", "command_run", {"id": "file.newProject", "params": {"name": "vedi /Users/x/f a.txt per favore"}}, False),
    ("gridcraft", "save_workbook", {"path": "NUL"}, False),
    ("gridcraft", "save_workbook", {"path": "CON"}, False),
    ("gridcraft", "save_workbook", {"path": "_regia/com1.xlsx"}, False),
    ("gridcraft", "save_workbook", {"path": "_regia/O2/f a b.xlsx"}, True),
    ("gridcraft", "execute_command", {"command": "Automate.RunScript", "params": {"name": "x"}}, False),
    ("effectcraft", "command_batch", {"steps": [{"id": "file.scripts.list"}]}, False),
    ("effectcraft", "command_batch", {"steps": [{"id": "FILE.SCRIPTS.LIST"}]}, False),
    ("effectcraft", "command_run", {"id": "window.scriptPanel", "params": {"name": "x.jsx"}}, False),
    ("effectcraft", "command_run", {"id": "window.restoreScriptPanels", "params": {}}, False),
    ("effectcraft", "command_batch", {"steps": [{"id": "script.runTasks"}]}, False),
    ("effectcraft", "command_run", {"id": "storage.clear", "params": {"what": "all"}}, False),
    ("effectcraft", "command_run", {"id": "file.executeFile", "params": {"path": "x.jsx"}}, False),
    ("cadcraft", "command_line", {"text": "script _regia/O1/o1.scr"}, False),
    ("cadcraft", "command_line", {"text": "SCR _regia/O1/o1.scr"}, False),
    ("cadcraft", "command_line", {"text": "_appload _regia/O1/o1.scr"}, False),
    ("cadcraft", "command_line", {"text": "ap"}, False),
    ("cadcraft", "command_line", {"text": "(setq o1 42)"}, False),
    ("cadcraft", "command_line", {"text": "(+ 40 2)"}, False),
    ("cadcraft", "command_line", {"text": "!o1"}, False),
    ("cadcraft", "command_line", {"text": "^C^Cscript x.scr"}, False),
    ("cadcraft", "command_line", {"text": "circle 0,0 1 script x.scr"}, False),
    ("cadcraft", "command_line", {"text": "-vlisp"}, False),
    ("cadcraft", "execute", {"command": "appload", "params": {"path": "_regia/x.lsp"}}, False),
    ("cadcraft", "execute", {"command": "aliasedit", "params": {"set": {"zz": "script"}}}, False),
    ("cadcraft", "command_line", {"text": 'saveas "/srv/altrove/f a.dxf"'}, False),
    ("cadcraft", "command_line", {"text": "line 0,0 10,0 10,5 c"}, True),
    ("cadcraft", "command_line", {"text": "circle 5,2.5 1"}, True),
    ("cadcraft", "command_line", {"text": "rectang 0,0 4,3"}, True),
    ("cadcraft", "command_line", {"text": "zoom e"}, True),
    ("cadcraft", "command_line", {"text": "saveas _regia/O2/x.dxf"}, True),
    ("cadcraft", "command_line", {"text": "line 0,0 @10<45"}, True),
    ("gridcraft", "set_cell", {"cell": "A2", "input": "a / b 1/2"}, True),
    ("gridcraft", "set_cell", {"cell": "A3", "input": "=SUM(A1:A2)"}, True),
    ("gridcraft", "set_cell", {"cell": "A4", "input": "caffè con latte"}, True),
    ("effectcraft", "set_property", {"layer": "#1", "path": "effects/#1/blurriness", "value": 3}, True),
    ("figcraft", "create_node", {"type": "vector", "path": "M0 0 L10 10 Z"}, True),
    ("photocraft", "doc_save", {"path": "_regia/O2/a b.png"}, True),
    ("photocraft", "doc_save", {"path": "_regia/O2/../../../fuori.png"}, False),
]

errori = 0
for app, strum, arg, atteso in CASI:
    try:
        nuovi, ctl = esamina(app, strum, arg)
        esito, nota = True, "→ %s" % nuovi
    except Rifiuto as e:
        esito, nota = False, "· %s" % e
    ok = esito == atteso
    errori += not ok
    print("%s %-8s %s.%s %s" % ("✓" if ok else "✗ SBAGLIATO", "passa" if esito else "RIFIUTO", app, strum, nota[:150]))
print("\n%d casi, %d sbagliati" % (len(CASI), errori))
sys.exit(1 if errori else 0)
