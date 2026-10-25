# Per ogni server di .mcp.json: initialize + tools/list (schemi completi), uno alla volta.
# Uso: python -I -X utf8 scarica_schemi.py <.mcp.json> <uscita.json>
import json, subprocess, sys

cfg = json.load(open(sys.argv[1], encoding="utf-8"))["mcpServers"]
res = {}
for name, s in cfg.items():
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "sonda", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    p = subprocess.Popen([s["command"], *s["args"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8")
    out, err = p.communicate("\n".join(json.dumps(m) for m in msgs) + "\n", timeout=60)
    r = {}
    for line in out.splitlines():
        try:
            j = json.loads(line)
        except ValueError:
            continue
        if j.get("id") == 1:
            r["init"] = j.get("result")
        if j.get("id") == 2:
            r["tools"] = j.get("result", {}).get("tools", [])
    res[name] = r
    print(name, len(r.get("tools", [])))
json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
