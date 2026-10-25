# Riduce i cataloghi dei comandi delle 13 app a un formato unico:
# [{"id", "label", "menu", "params"}], tutti stringhe. Uso: python normalizza.py
import json, re


def normalizza(app, risultato):
    sc = risultato.get("structuredContent")
    txt = "".join(c.get("text", "") for c in risultato.get("content", []) if c.get("type") == "text")
    try:
        dati = sc if sc is not None else json.loads(txt)
    except ValueError:
        dati = None
    if isinstance(dati, dict):
        dati = dati.get("commands") or dati.get("items") or next(
            (v for v in dati.values() if isinstance(v, list)), [])
    out = []
    if isinstance(dati, list):
        for c in dati:
            menu = c.get("menu") or c.get("location") or ""
            if isinstance(menu, list):
                menu = " › ".join(menu)
            p = c.get("params")
            if not isinstance(p, str):
                p = json.dumps(p, ensure_ascii=False) if p else ""
            out.append({"id": c.get("id", ""), "label": c.get("label") or c.get("title") or "",
                        "menu": menu, "params": p})
        return out
    # FigCraft: righe di testo «id* — Etichetta [Menu] (scorciatoia) {params}»
    for riga in txt.splitlines():
        m = re.match(r"^([\w.\-:]+)\*?\s+—\s+(.*)$", riga)
        if not m:
            continue
        resto = m.group(2)
        params = ""
        i = resto.find("{")
        if i >= 0:
            resto, params = resto[:i], resto[i:]
        menu = ""
        mm = re.search(r"\[([^\]]*)\]", resto)
        if mm:
            menu = mm.group(1)
            resto = resto[:mm.start()] + resto[mm.end():]
        resto = re.sub(r"\([^)]*\)\s*$", "", resto.strip())
        out.append({"id": m.group(1), "label": resto.strip(), "menu": menu, "params": params.strip()})
    return out


if __name__ == "__main__":
    grezzi = json.load(open("dati/cataloghi_grezzi.json", encoding="utf-8"))
    res = {}
    for app, v in grezzi.items():
        res[app] = normalizza(app, v["risultato"])
        print("%-12s %4d comandi  es. %s" % (app, len(res[app]), res[app][1] if res[app] else "-"))
    json.dump(res, open("dati/comandi.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
