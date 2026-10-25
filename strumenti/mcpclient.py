# Client MCP minimo su stdio per provare photocraft-cli mcp.
# Uso: python -I mcpclient.py <exe> <script.json> [args extra per mcp...]
# script.json: lista di {"tool": nome, "args": {...}} oppure {"method": ..., "params": ...}
import json, subprocess, sys, time

exe, script_path = sys.argv[1], sys.argv[2]
extra = sys.argv[3:]
p = subprocess.Popen([exe, "mcp", *extra], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
nid = 0

def call(method, params=None, notify=False):
    global nid
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        nid += 1
        msg["id"] = nid
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()
    if notify:
        return None
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("server chiuso; stderr: " + p.stderr.read())
        r = json.loads(line)
        if r.get("id") == nid:
            return r

t0 = time.perf_counter()
r = call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "prova", "version": "0"}})
print("## initialize %.0f ms" % ((time.perf_counter() - t0) * 1000))
print(json.dumps(r.get("result", r), ensure_ascii=False)[:3000])
call("notifications/initialized", notify=True)

with open(script_path, encoding="utf-8") as f:
    steps = json.load(f)
for s in steps:
    t0 = time.perf_counter()
    if "tool" in s:
        r = call("tools/call", {"name": s["tool"], "arguments": s.get("args", {})})
        label = s["tool"]
    else:
        r = call(s["method"], s.get("params", {}))
        label = s["method"]
    ms = (time.perf_counter() - t0) * 1000
    out = json.dumps(r.get("result", r.get("error")), ensure_ascii=False)
    lim = s.get("limit", 1500)
    print("\n## %s %.0f ms%s" % (label, ms, "  [ERRORE]" if ("error" in r or (r.get("result") or {}).get("isError")) else ""))
    print(json.dumps(s.get("args", s.get("params", {})), ensure_ascii=False)[:400])
    print(out if len(out) <= lim else out[:lim] + " …(%d car.)" % len(out))
    if s.get("save"):
        with open(s["save"], "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
p.stdin.close()
p.wait(timeout=30)
err = p.stderr.read()
if err.strip():
    print("\n## stderr\n" + err[:3000])
