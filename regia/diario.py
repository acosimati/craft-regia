# Diario di progetto: progetti/<nome>/DIARIO.md, una riga per voce, con data, fase e app.
import datetime, os, re
from figli import PROGETTI

FASI = ["idea", "piano", "produzione", "revisione", "consegna", "nota"]


def _cartella(progetto):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_\-]{0,60}", progetto or ""):
        raise ValueError("nome di progetto non valido: %r (lettere, cifre, _ e -)" % progetto)
    c = os.path.join(PROGETTI, progetto)
    os.makedirs(c, exist_ok=True)
    return c


def percorso_diario(progetto):
    return os.path.join(_cartella(progetto), "DIARIO.md")


def scrivi(progetto, testo, fase="nota", app=None):
    if fase not in FASI:
        raise ValueError("fase sconosciuta: %s (valide: %s)" % (fase, ", ".join(FASI)))
    p = percorso_diario(progetto)
    nuovo = not os.path.exists(p)
    with open(p, "a", encoding="utf-8") as f:
        if nuovo:
            f.write("# Diario del progetto «%s»\n\nAperto il %s dalla regia della suite Craft.\n\n"
                    % (progetto, datetime.date.today().strftime("%d/%m/%Y")))
        ora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        f.write("- **%s** · *%s*%s: %s\n" % (ora, fase, (" · `%s`" % app) if app else "", testo.strip().replace("\n", " ")))
    return p


def leggi(progetto):
    p = percorso_diario(progetto)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else "(nessun diario ancora per «%s»)" % progetto


def file_del_progetto(progetto):
    """Elenco dei file del progetto con dimensione e ora: è ciò che passa da un'app all'altra."""
    c = _cartella(progetto)
    out = []
    for radice, _, nomi in os.walk(c):
        for n in sorted(nomi):
            pf = os.path.join(radice, n)
            st = os.stat(pf)
            out.append({"file": os.path.relpath(pf, PROGETTI).replace("\\", "/"), "byte": st.st_size,
                        "modificato": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y %H:%M")})
    return out
