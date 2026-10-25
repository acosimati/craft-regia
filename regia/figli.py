# Server MCP figli: avvio su richiesta, chiamate JSON-RPC su stdio, chiusura pulita.
# Nessuna dipendenza esterna: un processo per app, un thread che legge stdout e uno stderr.
import json, os, queue, subprocess, threading, time

# Radice: CRAFT_RADICE se data, altrimenti la cartella del repository (quella che contiene regia/).
# app/ e progetti/ stanno sotto la radice; CRAFT_APP e CRAFT_PROGETTI possono spostarle una per una.
_QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADICE = os.environ.get("CRAFT_RADICE", _QUI).replace("\\", "/").rstrip("/")
APP_DIR = os.environ.get("CRAFT_APP", RADICE + "/app").replace("\\", "/").rstrip("/")
PROGETTI = os.environ.get("CRAFT_PROGETTI", RADICE + "/progetti").replace("\\", "/").rstrip("/")
LIBRERIA_LIGHTCRAFT = os.environ.get("CRAFT_REGIA_LIBRERIA_LIGHTCRAFT", PROGETTI + "/_regia/libreria_lightcraft")

# App che accettano le radici di automazione e vogliono percorsi relativi a progetti (9 su 13).
# DeckCraft dalla 0.10.0 (PR deckcraft #247): prima la regia non gliele passava (O12, O13 del 25/10/2026).
# Senza opzione restano cadcraft, gridcraft, filmcraft, lightcraft: per loro vale solo la guardia.
CONFINATE = {"deckcraft", "designcraft", "effectcraft", "figcraft", "pdfcraft", "photocraft",
             "soundcraft", "vectorcraft", "wordcraft"}


def app_installate():
    """{app: (versione, cartella)} letto da app/, una cartella <app>-<versione> per app."""
    res = {}
    for d in sorted(os.listdir(APP_DIR)):
        nome, _, ver = d.partition("-")
        if os.path.isfile(os.path.join(APP_DIR, d, nome + "-cli.exe")):
            res[nome] = (ver, APP_DIR + "/" + d)
    return res


def argomenti_avvio(app):
    """Riga di comando del server MCP, senza modalità compatte: il gateway vede tutti gli strumenti."""
    ver, cartella = app_installate()[app]
    args = [cartella + "/" + app + "-cli.exe", "mcp"]
    if app == "vectorcraft":
        args.append("--headless")
    if app == "lightcraft":
        args += ["--library", LIBRERIA_LIGHTCRAFT]
    if app in CONFINATE:
        args += ["--automation-read-root", PROGETTI, "--automation-write-root", PROGETTI]
    return args


class ErroreFiglio(Exception):
    pass


class Figlio:
    def __init__(self, app):
        self.app = app
        self.args = argomenti_avvio(app)
        self.lock = threading.Lock()
        self.risposte = queue.Queue()
        self.stderr = []
        self.nid = 0
        self.avviato = time.time()
        # cwd = progetti: per le app senza confini un percorso relativo cade lì dentro.
        self.p = subprocess.Popen(self.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, cwd=PROGETTI, text=True,
                                  encoding="utf-8", errors="replace", bufsize=1,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        threading.Thread(target=self._leggi, daemon=True).start()
        threading.Thread(target=self._leggi_err, daemon=True).start()
        r = self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "craft-regia", "version": "0.1"}}, 60)
        self.info = r
        self._scrivi({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.strumenti = self._rpc("tools/list", {}, 60).get("tools", [])

    def _leggi(self):
        for line in self.p.stdout:
            try:
                j = json.loads(line)
            except ValueError:
                continue
            if "id" in j and ("result" in j or "error" in j):
                self.risposte.put(j)
        self.risposte.put(None)

    def _leggi_err(self):
        for line in self.p.stderr:
            self.stderr.append(line.rstrip())
            del self.stderr[:-50]

    def _scrivi(self, msg):
        try:
            self.p.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
            self.p.stdin.flush()
        except OSError as e:
            raise ErroreFiglio("%s non risponde (%s); stderr: %s" % (self.app, e, " | ".join(self.stderr[-5:])))

    def _rpc(self, method, params, timeout):
        with self.lock:
            self.nid += 1
            mid = self.nid
            self._scrivi({"jsonrpc": "2.0", "id": mid, "method": method, "params": params})
            scadenza = time.time() + timeout
            while True:
                try:
                    j = self.risposte.get(timeout=max(0.1, scadenza - time.time()))
                except queue.Empty:
                    raise ErroreFiglio("%s: nessuna risposta a %s in %d s" % (self.app, method, timeout))
                if j is None:
                    raise ErroreFiglio("%s si è chiuso; stderr: %s" % (self.app, " | ".join(self.stderr[-5:])))
                if j.get("id") != mid:
                    continue  # risposta tardiva di una chiamata scaduta
                if "error" in j:
                    raise ErroreFiglio("%s: %s" % (self.app, j["error"].get("message", j["error"])))
                return j["result"]

    def chiama(self, strumento, argomenti, timeout=180):
        return self._rpc("tools/call", {"name": strumento, "arguments": argomenti or {}}, timeout)

    def vivo(self):
        return self.p.poll() is None

    def chiudi(self):
        """Chiusura pulita: stdin chiuso, attesa; poi terminate sul solo PID del figlio."""
        try:
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=10)
            return "chiuso"
        except subprocess.TimeoutExpired:
            self.p.terminate()
            try:
                self.p.wait(timeout=5)
                return "terminato (PID %d)" % self.p.pid
            except subprocess.TimeoutExpired:
                self.p.kill()
                return "ucciso (PID %d)" % self.p.pid


class Figli:
    def __init__(self):
        self.attivi = {}
        self.lock = threading.Lock()

    def prendi(self, app):
        with self.lock:
            f = self.attivi.get(app)
            if f and f.vivo():
                return f
            if app not in app_installate():
                raise ErroreFiglio("app sconosciuta: %s" % app)
            f = Figlio(app)
            self.attivi[app] = f
            return f

    def chiudi(self, app=None):
        with self.lock:
            nomi = [app] if app else list(self.attivi)
            return {n: self.attivi.pop(n).chiudi() for n in nomi if n in self.attivi}
