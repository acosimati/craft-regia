# Genera .mcp.json (livello progetto) per i 13 server MCP della suite Craft.
# Uso: python -I -X utf8 genera_mcp_json.py <cartella_craft>
import json, os, sys

base = sys.argv[1].replace("\\", "/").rstrip("/")
app_dir = base + "/app"
root = base + "/progetti"
CON_RADICI = {"designcraft", "effectcraft", "figcraft", "pdfcraft", "photocraft",
              "soundcraft", "vectorcraft", "wordcraft"}
EXTRA = {
    "vectorcraft": ["--headless"],
    "pdfcraft": ["--compact"],
    "lightcraft": ["--compact", "--library", root + "/libreria_lightcraft"],
}

servers = {}
for d in sorted(os.listdir(app_dir)):
    app = d.split("-")[0]
    args = ["mcp"] + EXTRA.get(app, [])
    if app in CON_RADICI:
        args += ["--automation-read-root", root, "--automation-write-root", root]
    servers[app] = {"type": "stdio", "command": f"{app_dir}/{d}/{app}-cli.exe", "args": args, "env": {}}

with open(base + "/.mcp.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump({"mcpServers": servers}, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(len(servers), "server scritti in", base + "/.mcp.json")
