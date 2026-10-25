# Avvia ogni server elencato in un .mcp.json con i suoi argomenti esatti: initialize + tools/list.
import json, subprocess, sys, time

cfg = json.load(open(sys.argv[1], encoding="utf-8"))["mcpServers"]
tot = 0
for name, s in cfg.items():
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "sonda", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    t0 = time.perf_counter()
    p = subprocess.Popen([s["command"], *s["args"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8")
    try:
        out, err = p.communicate("\n".join(json.dumps(m) for m in msgs) + "\n", timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
        print("%-12s TIMEOUT" % name)
        continue
    n = None
    for line in out.splitlines():
        try:
            j = json.loads(line)
        except ValueError:
            continue
        if j.get("id") == 2:
            n = len(j.get("result", {}).get("tools", []))
    tot += n or 0
    print("%-12s strumenti=%-4s %5d ms  %s" % (name, n, (time.perf_counter() - t0) * 1000,
                                              "" if n else err.strip()[:200]))
print("TOTALE strumenti:", tot)
