# Laboratorio effetti: rende un effetto in PNG, sequenza o video, senza finestra e senza rete.
# Uso: python -X utf8 rendi.py <gradiente|vetro|metallo> --out <cartella dentro progetti> [--w 1280 --h 720]
#        [--frames 30 --fps 30 --t0 0] [--formato png|mp4|webm] [--param k=v ...] [--tieni-fotogrammi]
# Stampa un JSON (file prodotti, byte, tempi) ed esce con 0; con un errore stampa {"errore": ...} ed esce con 1.
import argparse, json, os, shutil, subprocess, sys, time, urllib.parse
from pathlib import Path

QUI = Path(__file__).resolve().parent
# Stessa regola del gateway (regia/figli.py): CRAFT_PROGETTI, poi CRAFT_RADICE/progetti, poi <repository>/progetti.
PROGETTI = Path(os.environ.get("CRAFT_PROGETTI")
                or os.path.join(os.environ.get("CRAFT_RADICE") or str(QUI.parent), "progetti")).resolve()
PAGINE = {"gradiente": QUI / "effetti/gradiente/dist/index.html",
          "vetro": QUI / "effetti/vetro/index.html",
          "metallo": QUI / "effetti/metallo/index.html"}
PARAMETRI_PERCORSO = {"sfondo", "maschera"}
# ffmpeg: variabile FFMPEG (percorso dell'eseguibile), altrimenti quello nel PATH.
FFMPEG_ENV = os.environ.get("FFMPEG", "")


class Errore(Exception):
    pass


def dentro_progetti(s, deve_esistere=False):
    """Percorso risolto (realpath) che deve stare dentro progetti; i relativi sono relativi a progetti."""
    p = Path(s)
    p = (p if p.is_absolute() else PROGETTI / p)
    r = Path(os.path.realpath(p))
    if r != PROGETTI and PROGETTI not in r.parents:
        raise Errore("percorso fuori da progetti: %r" % s)
    if deve_esistere and not r.is_file():
        raise Errore("file inesistente: %r" % s)
    return r


def leggi_argomenti(argv):
    a = argparse.ArgumentParser(description="Rende un effetto del laboratorio senza finestra.")
    a.add_argument("effetto", choices=sorted(PAGINE))
    a.add_argument("--out", required=True)
    a.add_argument("--w", type=int, default=1280)
    a.add_argument("--h", type=int, default=720)
    a.add_argument("--frames", type=int, default=1)
    a.add_argument("--fps", type=float, default=30)
    a.add_argument("--t0", type=float, default=0.0)
    a.add_argument("--formato", choices=["png", "mp4", "webm"], default="png")
    a.add_argument("--param", action="append", default=[], metavar="k=v")
    a.add_argument("--tieni-fotogrammi", action="store_true")
    g = a.parse_args(argv)
    if not (16 <= g.w <= 3840 and 16 <= g.h <= 2160):
        raise Errore("dimensioni fuori misura (16-3840 × 16-2160)")
    if not (1 <= g.frames <= 900 and 1 <= g.fps <= 120):
        raise Errore("fotogrammi 1-900, fps 1-120")
    return g


def url_pagina(g):
    q = {"w": g.w, "h": g.h, "t": g.t0}
    for kv in g.param:
        if "=" not in kv:
            raise Errore("parametro senza «=»: %r" % kv)
        k, v = kv.split("=", 1)
        k = k.strip()
        if k in PARAMETRI_PERCORSO:
            v = dentro_progetti(v, deve_esistere=True).as_uri()
        q[k] = v
    pagina = PAGINE[g.effetto]
    if not pagina.is_file():
        raise Errore("pagina mancante: %s (per il gradiente: npm run build)" % pagina)
    return pagina.as_uri() + "?" + urllib.parse.urlencode(q)


def ffmpeg():
    return (FFMPEG_ENV if os.path.isfile(FFMPEG_ENV) else None) or shutil.which("ffmpeg")


def rendi(g):
    from playwright.sync_api import sync_playwright
    t_inizio = time.perf_counter()
    out = dentro_progetti(g.out)
    out.mkdir(parents=True, exist_ok=True)
    video = g.formato in ("mp4", "webm")
    cart_fot = out / "fotogrammi" if video else out
    cart_fot.mkdir(exist_ok=True)
    url = url_pagina(g)
    trasparente = any(kv.split("=", 1)[0] == "trasparente" and kv.split("=", 1)[1] in ("1", "si", "true")
                      for kv in g.param if "=" in kv)
    bloccate, errori_pagina, prodotti = [], [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True,
                                     args=["--hide-scrollbars", "--allow-file-access-from-files",
                                           "--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=d3d11"])
        try:
            ctx = browser.new_context(viewport={"width": g.w, "height": g.h}, device_scale_factor=1, offline=True)

            def filtro(route):
                if route.request.url.startswith(("file:", "data:", "blob:")):
                    route.continue_()
                else:
                    bloccate.append(route.request.url[:200])
                    route.abort()
            ctx.route("**/*", filtro)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errori_pagina.append(str(e)[:300]))
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_function("window.__pronto === true || !!window.__errore", timeout=60000)
            err = page.evaluate("window.__errore || null")
            if err:
                raise Errore("la pagina segnala: %s" % err)
            renderer = page.evaluate("""() => { try { const c = document.createElement('canvas').getContext('webgl2');
                const e = c.getExtension('WEBGL_debug_renderer_info');
                return e ? c.getParameter(e.UNMASKED_RENDERER_WEBGL) : c.getParameter(c.RENDERER); } catch (x) { return String(x); } }""")
            t_pronto = time.perf_counter()
            for i in range(g.frames):
                t = g.t0 + i / g.fps
                page.evaluate("t => window.rendi(t)", t)
                f = cart_fot / ("fotogramma_%04d.png" % i)
                page.screenshot(path=str(f), omit_background=trasparente)
            t_fotogrammi = time.perf_counter()
            err = page.evaluate("window.__errore || null")
            if err:
                raise Errore("la pagina segnala: %s" % err)
        finally:
            browser.close()
    t_video = 0.0
    if video:
        ff = ffmpeg()
        if not ff:
            raise Errore("ffmpeg non trovato")
        dest = out / ("%s.%s" % (g.effetto, g.formato))
        if g.formato == "mp4":
            cod = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        else:
            cod = ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32", "-deadline", "realtime", "-cpu-used", "8",
                   "-pix_fmt", "yuva420p" if trasparente else "yuv420p"]
        t0v = time.perf_counter()
        r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(g.fps),
                            "-i", str(cart_fot / "fotogramma_%04d.png")] + cod + [str(dest)],
                           capture_output=True, text=True)
        t_video = time.perf_counter() - t0v
        if r.returncode != 0 or not dest.is_file():
            raise Errore("ffmpeg exit %d: %s" % (r.returncode, r.stderr[-400:]))
        prodotti.append(dest)
        shutil.copyfile(cart_fot / "fotogramma_0000.png", out / "anteprima.png")
        prodotti.insert(0, out / "anteprima.png")
        if g.tieni_fotogrammi:
            prodotti += sorted(cart_fot.glob("fotogramma_*.png"))
        else:
            shutil.rmtree(cart_fot)
    else:
        prodotti += sorted(cart_fot.glob("fotogramma_*.png"))
    totale = time.perf_counter() - t_inizio
    return {
        "effetto": g.effetto, "formato": g.formato, "larghezza": g.w, "altezza": g.h,
        "fotogrammi": g.frames, "fps": g.fps, "cartella": str(out).replace("\\", "/"),
        "file": [{"percorso": str(p).replace("\\", "/"), "byte": p.stat().st_size} for p in prodotti],
        "byte_totali": sum(p.stat().st_size for p in prodotti),
        "tempo_totale_s": round(totale, 3),
        "tempo_avvio_s": round(t_pronto - t_inizio, 3),
        "tempo_per_fotogramma_s": round((t_fotogrammi - t_pronto) / g.frames, 4),
        "tempo_video_s": round(t_video, 3),
        "renderer_webgl": renderer, "senza_rete": True,
        "richieste_bloccate": bloccate, "errori_pagina": errori_pagina,
    }


def main(argv):
    try:
        g = leggi_argomenti(argv)
        print(json.dumps(rendi(g), ensure_ascii=False))
        return 0
    except SystemExit as e:
        return int(e.code or 0) if e.code not in (None, 0) else 0
    except Exception as e:  # noqa: BLE001 — il chiamante vuole sempre un JSON
        print(json.dumps({"errore": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
