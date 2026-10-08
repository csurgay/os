"""Generate the SVG figures for the Virtual Memory lecture.

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
Needs pagesim.py in the same folder.
"""
import math

STYLE = """<style>
  .ink{fill:#1f1f1f}.quiet{fill:#6b6b66}.edge{stroke:#b5b4a8}.edgef{fill:#b5b4a8}
  .grid{stroke:#e3e2da}.acc{stroke:#2f6fd6}.accf{fill:#2f6fd6;fill-opacity:.12}.acct{fill:#2f6fd6}
  .c2{fill:#d9822b}.c2s{stroke:#d9822b}.c2f{fill:#d9822b;fill-opacity:.14}.tint{fill:#f4f3ee}
  .bad{fill:#c8372d}.bads{stroke:#c8372d}.badf{fill:#c8372d;fill-opacity:.14}
  text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
  @media (prefers-color-scheme: dark){
    .ink{fill:#e8e8e3}.quiet{fill:#a3a39c}.edge{stroke:#6f6e66}.edgef{fill:#6f6e66}
    .grid{stroke:#3a3a35}.acc{stroke:#5b93ef}.accf{fill:#5b93ef;fill-opacity:.18}.acct{fill:#7aa9f5}
    .c2{fill:#eb9a4b}.c2s{stroke:#eb9a4b}.c2f{fill:#eb9a4b;fill-opacity:.2}.tint{fill:#22221f}
    .bad{fill:#ff7b70}.bads{stroke:#ff7b70}.badf{fill:#ff7b70;fill-opacity:.2}
  }
</style>"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, weight=400, cls="ink", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'class="{cls}" text-anchor="{anchor}">{esc(s)}</text>')


def marker(mid, cls="edgef"):
    return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="{cls}"/></marker>')


def path(d, mid=None, cls="edge", width=1.25, dash=None):
    a = f' marker-end="url(#{mid})"' if mid else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" class="{cls}" stroke-width="{width}"{a}{da}/>'


def rect(x, y, w, h, kind="plain", rx=8):
    fills = {"acc": ("accf", "acc", 2), "c2": ("c2f", "c2s", 1.5), "bad": ("badf", "bads", 1.5)}
    if kind in fills:
        f, s, sw = fills[kind]
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{f}"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" class="{s}" stroke-width="{sw}"/>')
    t = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="tint"/>' if kind == "tint" else ""
    return t + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" class="edge" stroke-width="1.25"/>'


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}">\n<title>{esc(title)}</title>\n{STYLE}\n{body}\n</svg>\n')



import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))


def label(x, y, s, size=11.5, cls="quiet", anchor="middle", weight=400):
    return text(x, y, s, size, weight, cls=cls, anchor=anchor)


# ---------------- 1. Processes side by side in RAM ----------------
def separation():
    title = "Több program egy RAM-ban: ki kit véd, és mi lesz, ha még egy érkezik?"
    p = [text(24, 30, title, 15, 600)]
    x, y0 = 60, 52
    parts = [("OS", 40, "plain"), ("1. folyamat", 56, "acc"), ("2. folyamat", 50, "c2"), ("3. folyamat", 40, "acc"),
             ("szabad", 24, "plain"), ("4. folyamat", 60, "c2"), ("szabad", 30, "plain")]
    y = y0
    for name, h, k in parts:
        p.append(rect(x, y, 160, h, k if k != "plain" else "tint", rx=0))
        p.append(text(x + 80, y + h / 2 + 4, name, 12, 600 if name != "szabad" else 400, cls="ink" if name != "szabad" else "quiet", anchor="middle"))
        y += h
    p.append(text(x + 80, y + 20, "fizikai RAM", 11.5, cls="quiet", anchor="middle"))
    p.append(rect(260, 120, 120, 70, "bad", rx=6)); p.append(text(320, 150, "5. folyamat", 12, 600, anchor="middle"))
    p.append(text(320, 168, "70 egység kell", 11, cls="quiet", anchor="middle"))
    qs = [("Védelem", "az 1. folyamat nem olvashatja és nem írhatja felül a 2. folyamatot vagy az OS-t"),
          ("Áthelyezés", "a program nem tudhatja előre, melyik címre töltik be"),
          ("Fragmentáció", "54 egység szabad, de két lyukban: az 5. folyamat nem fér el"),
          ("Méret", "a folyamatoknak együtt több memória kellhet, mint amennyi RAM van")]
    for i, (a, b) in enumerate(qs):
        yy = 72 + i * 56
        p.append(text(420, yy, a, 13, 600)); p.append(text(420, yy + 18, b, 11.5, cls="quiet"))
    p.append(text(420, 310, "A virtuális memória mind a négyre választ ad: minden folyamat saját, privát,", 11.5, cls="acct"))
    p.append(text(420, 328, "összefüggő címtartományt kap 0-tól a maximumig, a RAM-ra és a lemezre leképezve.", 11.5, cls="acct"))
    return svg(900, 400, title, "\n".join(p))


# ---------------- 2. Fragmentation ----------------
def fragmentation():
    title = "Belső és külső fragmentáció"
    p = [text(24, 30, title, 15, 600)]
    # internal
    p.append(text(24, 62, "Egyenlő méretű blokkok: belső fragmentáció", 13, 600))
    for i, used in enumerate((1.0, 0.35, 0.9, 0.5)):
        y = 76 + i * 46
        p.append(rect(24, y, 200, 40, "tint", rx=2))
        p.append(f'<rect x="24" y="{y}" width="{200 * used:.0f}" height="40" class="accf"/>')
        p.append(text(234, y + 25, f"{int(used * 100)}% foglalt", 11.5, cls="quiet"))
    p.append(text(24, 310, "minden blokk kihasználatlan maradéka a blokkon belül vész el", 11.5, cls="quiet"))
    p.append(text(24, 328, "(mint a félig üres szállítókonténerek)", 11.5, cls="quiet"))
    # external
    x = 460
    p.append(text(x, 62, "Változó méretű blokkok: külső fragmentáció", 13, 600))
    blocks = [("1. foglalás", 30, "acc"), ("2. foglalás", 44, "acc"), ("szabad", 34, "plain"), ("5. foglalás", 50, "c2"), ("szabad", 28, "plain"), ("6. foglalás", 26, "acc")]
    y = 76
    for name, h, k in blocks:
        p.append(rect(x, y, 180, h, k if k != "plain" else "tint", rx=0))
        p.append(text(x + 90, y + h / 2 + 4, name, 11.5, 600 if name != "szabad" else 400, cls="ink" if name != "szabad" else "quiet", anchor="middle"))
        y += h
    p.append(rect(x + 210, 120, 120, 50, "bad", rx=4)); p.append(text(x + 270, 141, "új kérés", 11.5, 600, anchor="middle"))
    p.append(text(x + 270, 158, "50 egység kell", 11, cls="quiet", anchor="middle"))
    p.append(text(x, 310, "összesen 62 egység szabad, de egyik lyuk sem elég nagy;", 11.5, cls="quiet"))
    p.append(text(x, 328, "a tömörítés (töredezettségmentesítés) egymás mellé tolná a blokkokat", 11.5, cls="quiet"))
    # zebra / horse
    p.append(text(24, 372, "A fragmentált memória olyan, mint a zebra, a tömörített pedig mint egy ló, amelynek minden sötét csíkja egy foltba gyűlt.", 11.5, cls="quiet"))
    for i in range(12):
        p.append(f'<rect x="{24 + i * 20}" y="386" width="10" height="20" class="{"acct" if i % 2 == 0 else "tint"}"/>')
    p.append(f'<rect x="300" y="386" width="120" height="20" class="acct"/><rect x="420" y="386" width="120" height="20" class="tint"/>')
    p.append(f'<rect x="300" y="386" width="240" height="20" fill="none" class="edge"/><rect x="24" y="386" width="240" height="20" fill="none" class="edge"/>')
    p.append(text(144, 424, "fragmentált (zebra)", 11, cls="quiet", anchor="middle")); p.append(text(420, 424, "tömörített (ló)", 11, cls="quiet", anchor="middle"))
    return svg(860, 440, title, "\n".join(p))


# ---------------- 3. Paging: contiguous pages, scattered frames ----------------
def paging():
    m = "pg"
    title = "Lapozás: a folyamat számára összefüggő, a RAM-ban szétszórt"
    p = [f"<defs>{marker(m, 'acct')}{marker('pg2', 'c2')}</defs>", text(24, 30, title, 15, 600)]
    def pages(x, y, name, ids, kind):
        p.append(text(x, y - 8, name, 12.5, 600))
        for i, n in enumerate(ids):
            p.append(rect(x, y + i * 34, 90, 30, kind, rx=2)); p.append(text(x + 45, y + i * 34 + 20, f"{n}. lap", 11.5, 600, anchor="middle"))
    pages(40, 70, "1. folyamat", (11, 12, 13), "acc")
    pages(40, 230, "2. folyamat", (21, 22, 23), "c2")
    rx = 420
    p.append(text(rx, 52, "RAM: 4 KiB-os lapkeretek", 12.5, 600))
    content = {1: ("11", "acc"), 3: ("22", "c2"), 4: ("13", "acc"), 6: ("12", "acc"), 7: ("21", "c2"), 9: ("23", "c2")}
    for f in range(11):
        y = 62 + f * 28
        c = content.get(f)
        p.append(rect(rx, y, 140, 26, c[1] if c else "tint", rx=0))
        p.append(text(rx - 8, y + 18, str(f), 10.5, cls="quiet", anchor="end"))
        if c: p.append(text(rx + 70, y + 18, f"{c[0]}. lap", 11, 600, anchor="middle"))
    for (pi, f) in ((0, 1), (1, 6), (2, 4)):
        y1 = 85 + pi * 34; y2 = 75 + f * 28
        p.append(path(f"M132 {y1}C260 {y1} 300 {y2} {rx - 4} {y2}", m, cls="acc", width=1.5))
    for (pi, f) in ((0, 7), (1, 3), (2, 9)):
        y1 = 245 + pi * 34; y2 = 75 + f * 28
        p.append(path(f"M132 {y1}C260 {y1} 300 {y2} {rx - 4} {y2}", "pg2", cls="c2s", width=1.5))
    p.append(rect(640, 120, 200, 60, "tint", rx=6)); p.append(text(740, 145, "lemez (swap)", 12, 600, anchor="middle"))
    p.append(text(740, 164, "a RAM-ban nem lévő lapok", 11, cls="quiet", anchor="middle"))
    p.append(text(24, 390, "Bármely lap bármely szabad keretbe kerülhet: nincs külső fragmentáció, csak egy kevés belső az utolsó lapokban.", 11.5, cls="quiet"))
    return svg(870, 406, title, "\n".join(p))


# ---------------- 4. Address translation with one page table ----------------
def translation():
    m = "tr"
    title = "Címfordítás laptáblával (32 bites címek, 4 KiB-os lapok)"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(60, 58, "virtuális cím", 12, 600, cls="quiet"))
    p.append(rect(60, 66, 320, 34, "acc", rx=3)); p.append(text(220, 88, "lapszám (20 bit)", 12, 600, anchor="middle"))
    p.append(rect(380, 66, 192, 34, "tint", rx=3)); p.append(text(476, 88, "eltolás (12 bit)", 12, 600, anchor="middle"))
    # page-table base register
    p.append(rect(40, 170, 150, 34, "c2", rx=4)); p.append(text(115, 192, "laptábla-bázis", 12, 600, anchor="middle"))
    p.append(text(115, 222, "(x86-on CR3; minden", 10.5, cls="quiet", anchor="middle")); p.append(text(115, 236, "folyamat környezetének része)", 10.5, cls="quiet", anchor="middle"))
    # page table
    tx, ty = 250, 150
    p.append(text(tx, ty - 8, "ennek a folyamatnak a laptáblája", 12, 600))
    cols = [("V", 26), ("R/W/X", 60), ("keretszám", 120)]
    cx = tx
    for name, w in cols:
        p.append(rect(cx, ty, w, 24, "tint", rx=0)); p.append(text(cx + w / 2, ty + 16, name, 10.5, 600, anchor="middle")); cx += w
    for r in range(5):
        y = ty + 24 + r * 26; cx = tx
        for j, (name, w) in enumerate(cols):
            p.append(rect(cx, y, w, 26, "acc" if r == 2 else "plain", rx=0)); cx += w
        if r == 2:
            p.append(text(tx + 13, y + 18, "1", 11, 600, anchor="middle")); p.append(text(tx + 56, y + 18, "R W -", 11, 600, anchor="middle"))
            p.append(text(tx + 146, y + 18, "0x12dc6", 11, 600, anchor="middle"))
    p.append(path("M220 100C220 160 236 236 246 239", m, width=1.5)); p.append(text(150, 128, "index", 11, cls="quiet"))
    p.append(path("M190 187C220 187 230 180 246 180", m, width=1.5)); p.append(text(196, 176, "kezdet", 10.5, cls="quiet"))
    # physical address
    p.append(text(560, 214, "fizikai cím", 12, 600, cls="quiet"))
    p.append(rect(560, 222, 200, 34, "acc", rx=3)); p.append(text(660, 244, "keretszám", 12, 600, anchor="middle"))
    p.append(rect(760, 222, 100, 34, "tint", rx=3)); p.append(text(810, 244, "eltolás", 12, 600, anchor="middle"))
    p.append(path("M458 239H556", m, width=1.5))
    p.append(path("M476 100C476 130 810 130 810 218", m, width=1.5)); p.append(text(640, 124, "változatlanul átmásolva", 11, cls="quiet"))
    p.append(text(24, 320, "V = 0: a lap nincs a RAM-ban; a CPU laphibát (megszakítást) vált ki, az OS betölti a lapot a lemezről, vagy leállítja a programot.", 11.5, cls="quiet"))
    p.append(text(24, 338, "Jogok (olvasás, írás, futtatás, felhasználó/kernel): a tiltott hozzáférés is laphiba. Folyamatonként egy tábla, folyamatváltáskor a bázisregiszter is vált.", 11.5, cls="quiet"))
    return svg(880, 354, title, "\n".join(p))


# ---------------- 5. Four-level page table of x86-64 ----------------
def multilevel():
    m = "ml"
    title = "x86-64: egy 48 bites virtuális cím bejárja a négyszintű laptáblát"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    fields = [("PML4", 9), ("PDPT", 9), ("PD", 9), ("PT", 9), ("eltolás", 12)]
    x = 60
    for i, (n, b) in enumerate(fields):
        w = b * 13
        p.append(rect(x, 54, w, 32, "tint" if n == "eltolás" else "acc", rx=2)); p.append(text(x + w / 2, 75, f"{n} ({b})", 11.5, 600, anchor="middle"))
        x += w
    p.append(text(x + 10, 75, "= 48 bit", 11.5, cls="quiet"))
    for i, n in enumerate(("4. szint", "3. szint", "2. szint", "1. szint")):
        tx = 60 + i * 160; ty = 140
        p.append(rect(tx, ty, 110, 140, "tint", rx=4)); p.append(text(tx + 55, ty - 8, n, 11.5, 600, anchor="middle"))
        p.append(rect(tx, ty + 50 + i * 12, 110, 18, "acc", rx=0))
        p.append(text(tx + 55, ty + 128, "512 bejegyzés", 10.5, cls="quiet", anchor="middle"))
        p.append(path(f"M{60 + i * 117 + 58} 86C{60 + i * 117 + 58} 110 {tx + 55} 110 {tx + 55} {ty - 22}", m, width=1.2))
        if i < 3:
            p.append(path(f"M{tx + 110} {ty + 59 + i * 12}C{tx + 135} {ty + 59 + i * 12} {tx + 135} {ty + 20} {tx + 158} {ty + 20}", m, width=1.5))
    p.append(rect(60, 300, 80, 28, "c2", rx=4)); p.append(text(100, 319, "CR3", 12, 600, anchor="middle"))
    p.append(path("M100 300V284", m, width=1.5))
    p.append(path("M650 235C670 235 660 205 676 205", m, width=1.5)); p.append(rect(680, 185, 150, 40, "acc", rx=4)); p.append(text(755, 210, "keret + eltolás", 12, 600, anchor="middle"))
    p.append(text(24, 362, "Minden tábla pontosan egy 4 KiB-os lapot tölt ki (512 darab 8 bájtos bejegyzés). Táblák csak a címtartomány használt részeihez", 11.5, cls="quiet"))
    p.append(text(24, 380, "léteznek, így egy kis folyamatnak egy óriási lapos tábla helyett néhány lapnyi tábla elég. Az ár: fordításonként akár négy", 11.5, cls="quiet"))
    p.append(text(24, 398, "további memóriaolvasás, ezért fontos a TLB. Az újabb CPU-k ötödik szintet is kínálnak (57 bites címek).", 11.5, cls="quiet"))
    return svg(860, 414, title, "\n".join(p))


# ---------------- 6. TLB, page table and cache on one access ----------------
def tlbpath():
    m = "tp"
    title = "Egy memória-hozzáférés: TLB, laptábla-bejárás, majd a gyorsítótár"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(rect(40, 60, 170, 34, "acc", rx=3)); p.append(text(125, 82, "virtuális cím", 12, 600, anchor="middle"))
    p.append(rect(270, 50, 160, 54, "c2", rx=6)); p.append(text(350, 74, "TLB", 13, 600, anchor="middle")); p.append(text(350, 92, "friss fordítások", 10.5, cls="quiet", anchor="middle"))
    p.append(path("M210 77H266", m, width=1.5))
    p.append(rect(270, 160, 160, 54, "tint", rx=6)); p.append(text(350, 184, "laptábla-bejárás", 12, 600, anchor="middle")); p.append(text(350, 202, "a memóriában (lassú)", 10.5, cls="quiet", anchor="middle"))
    p.append(path("M350 104V156", m, width=1.5)); p.append(text(358, 134, "TLB-hiány", 11, cls="quiet"))
    p.append(rect(500, 100, 160, 40, "acc", rx=4)); p.append(text(580, 125, "fizikai cím", 12, 600, anchor="middle"))
    p.append(path("M430 77C470 77 480 110 496 116", m, width=1.5)); p.append(text(470, 72, "TLB-találat", 11, cls="quiet"))
    p.append(path("M430 187C470 187 480 134 496 128", m, width=1.5))
    p.append(rect(500, 200, 160, 54, "c2", rx=6)); p.append(text(580, 224, "gyorsítótár", 13, 600, anchor="middle")); p.append(text(580, 242, "(előző előadás)", 10.5, cls="quiet", anchor="middle"))
    p.append(path("M580 140V196", m, width=1.5))
    p.append(rect(720, 200, 120, 54, "tint", rx=6)); p.append(text(780, 230, "RAM", 13, 600, anchor="middle"))
    p.append(path("M660 227H716", m, width=1.5)); p.append(text(688, 220, "hiány", 11, cls="quiet", anchor="middle"))
    p.append(path("M350 214C350 300 700 300 760 258", m, width=1.2, dash="4 4")); p.append(text(520, 300, "maga a bejárás is a gyorsítótáron át olvassa a laptábla-bejegyzéseket", 11, cls="quiet", anchor="middle"))
    p.append(text(24, 336, "Ha a laptáblában az érvényességi bit 0: laphiba, amelyet az operációs rendszer kezel; lehet, hogy a lemezről kell beolvasnia a lapot (ms).", 11.5, cls="quiet"))
    return svg(870, 352, title, "\n".join(p))


# ---------------- 7. Belady's anomaly (from the simulator) ----------------
def belady():
    spec = importlib.util.spec_from_file_location("pagesim", os.path.join(HERE, "pagesim.py"))
    ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
    title = "Bélády-anomália: a FIFO 3 kerettel 9, 4 kerettel 10 laphibát okoz"
    p = [text(24, 30, title, 15, 600)]
    y0 = 60
    for n in (3, 4):
        faults, hist = ps.simulate(ps.EXAMPLE, n, "fifo")
        p.append(text(24, y0 + 18, f"{n} keret", 12.5, 600))
        for j, (page, fault, mem) in enumerate(hist):
            x = 120 + j * 52
            if fault:
                p.append(f'<circle cx="{x + 20}" cy="{y0 + 12}" r="13" class="c2f"/><circle cx="{x + 20}" cy="{y0 + 12}" r="13" fill="none" class="c2s" stroke-width="1.5"/>')
            p.append(text(x + 20, y0 + 17, str(page), 13, 600, anchor="middle"))
            order = list(reversed(mem))
            for r in range(n):
                y = y0 + 32 + r * 24
                p.append(rect(x, y, 40, 22, "tint", rx=0))
                if r < len(order): p.append(text(x + 20, y + 16, str(order[r]), 12, anchor="middle"))
        p.append(text(120 + 12 * 52 + 10, y0 + 70, f"{faults} laphiba", 13, 600, cls="bad" if n == 4 else "ink"))
        y0 += 50 + n * 24 + 20
    p.append(text(24, y0 + 6, "Bekarikázva: laphiba. Minden oszlop a kereteket mutatja a hivatkozás után, a legújabb lap felül; a FIFO az alsót teszi ki.", 11.5, cls="quiet"))
    p.append(text(24, y0 + 24, "Az LRU és az OPT sosem viselkedik így: több kerettel mindig bővebb halmazt tartanak, mint kevesebbel (veremalgoritmusok).", 11.5, cls="quiet"))
    return svg(860, y0 + 40, title, "\n".join(p))


# ---------------- 8. TLB measurement ----------------
def tlbchart():
    title = "Ugyanaz a gyorsítótárazott adat, több lap: a címfordítás ára (mérés, tlb.c)"
    pages = [16, 64, 256, 1024, 4096, 16384, 65536, 262144]
    small = [1.5, 1.6, 3.8, 6.5, 14.9, 27.7, 159.5, 221.4]
    huge = [1.5, 1.5, 1.5, 4.3, 4.3, 5.6, 27.3, 104.4]
    x0, x1, y0, y1 = 90, 760, 320, 60
    X = lambda i: x0 + (x1 - x0) * i / (len(pages) - 1)
    Y = lambda v: y0 - (y0 - y1) * math.log10(v) / math.log10(300)
    p = [text(24, 30, title, 15, 600)]
    for v in (1, 2, 5, 10, 20, 50, 100, 200):
        p.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" class="grid"/>')
        p.append(text(x0 - 8, Y(v) + 4, f"{v} ns", 10.5, cls="quiet", anchor="end"))
    for i, n in enumerate(pages):
        p.append(text(X(i), y0 + 18, f"{n:,}".replace(",", " "), 10.5, cls="quiet", anchor="middle"))
    p.append(text((x0 + x1) / 2, y0 + 38, "az érintett különböző lapok száma (mindegyikben egy 64 bájtos sor)", 11.5, cls="quiet", anchor="middle"))
    for data, cls, lab in ((small, "c2", "4 KiB-os lapok"), (huge, "acct", "2 MiB-os huge page-ek")):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(data))
        stroke = "c2s" if cls == "c2" else "acc"
        p.append(f'<polyline points="{pts}" fill="none" class="{stroke}" stroke-width="2.5"/>')
        for i, v in enumerate(data):
            p.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" class="{cls}"/>')
    p.append(f'<rect x="100" y="70" width="14" height="4" class="c2"/>'); p.append(text(120, 76, "4 KiB-os lapok", 11.5))
    p.append(f'<rect x="100" y="90" width="14" height="4" class="acct"/>'); p.append(text(120, 96, "2 MiB-os huge page-ek", 11.5))
    p.append(text(24, 386, "4096 lapig az érintett sorok (256 KiB) még elférnek az L2 gyorsítótárban; a görbék közti különbség a címfordítás:", 11.5, cls="quiet"))
    p.append(text(24, 404, "a 4 KiB-os lapok túlcsordítják a TLB-t, míg 1 GiB 2 MiB-os lapokkal csak 512 fordítást igényel.", 11.5, cls="quiet"))
    return svg(800, 420, title, "\n".join(p))


# ---------------- 9. Thrashing ----------------
def thrash():
    spec = importlib.util.spec_from_file_location("pagesim", os.path.join(HERE, "pagesim.py"))
    ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
    import random
    r, refs = random.Random(7), []
    for phase in range(3):
        ws = list(range(phase * 12, phase * 12 + 12))
        for _ in range(2000):
            refs.append(r.choice(ws) if r.random() < 0.97 else 100 + r.randrange(30))
    frames = list(range(2, 25))
    rates = [100 * ps.simulate(refs, n, "lru")[0] / len(refs) for n in frames]
    title = "Laphiba-arány a keretek számának függvényében (szimuláció, pagesim.py thrash)"
    x0, x1, y0, y1 = 80, 760, 290, 60
    X = lambda n: x0 + (x1 - x0) * (n - 2) / 22
    Y = lambda v: y0 - (y0 - y1) * v / 100
    p = [text(24, 30, title, 15, 600)]
    for v in (0, 20, 40, 60, 80, 100):
        p.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" class="grid"/>')
        p.append(text(x0 - 8, Y(v) + 4, f"{v}%", 10.5, cls="quiet", anchor="end"))
    for n in (2, 4, 8, 12, 16, 20, 24):
        p.append(text(X(n), y0 + 18, str(n), 10.5, cls="quiet", anchor="middle"))
    p.append(f'<rect x="{X(2):.1f}" y="{y1}" width="{X(11) - X(2):.1f}" height="{y0 - y1}" class="badf"/>')
    p.append(text(X(6.5), y1 + 18, "vergődés: kevesebb keret, mint a munkahalmaz", 11.5, 600, anchor="middle"))
    pts = " ".join(f"{X(n):.1f},{Y(v):.1f}" for n, v in zip(frames, rates))
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    p.append(f'<line x1="{X(12):.1f}" y1="{y1}" x2="{X(12):.1f}" y2="{y0}" class="c2s" stroke-width="1.5" stroke-dasharray="5 4"/>')
    p.append(text(X(12) + 6, y1 + 40, "munkahalmaz: 12 lap", 11.5, 600))
    p.append(text((x0 + x1) / 2, y0 + 38, "a folyamatnak adott keretek száma", 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, 360, "Ha kevesebb kerete van, mint a munkahalmaza, a folyamat hivatkozásainak nagy része laphibát okoz, és a lemezre várakozik.", 11.5, cls="quiet"))
    return svg(800, 376, title, "\n".join(p))


# ---------------- 10. A lapozás előtt: overlay és tárcsere ----------------
def overlays():
    m = "ov"
    title = "A lapozás előtt: overlay (egy program fázisokban) és tárcsere (teljes jobok)"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(24, 62, "Overlay: a rezidens rész fázisonként tölti be a programot az overlay-területre", 13, 600))
    phases = [("1. szövegszerkesztő", "acc"), ("2. fordító", "c2"), ("3. linker", "bad")]
    for i, (name, k) in enumerate(phases):
        x = 40 + i * 170
        # memóriaoszlop, felül a magas címek: szabad, overlay-terület, rezidens rész, OS
        p.append(rect(x, 80, 120, 50, "tint", rx=0)); p.append(text(x + 60, 110, "szabad", 11, cls="quiet", anchor="middle"))
        p.append(rect(x, 130, 120, 80, k, rx=0)); p.append(text(x + 60, 174, name, 10.5 if len(name) > 12 else 12, 600, anchor="middle"))
        p.append(rect(x, 210, 120, 30, "plain", rx=0)); p.append(text(x + 60, 230, "rezidens rész", 11, anchor="middle"))
        p.append(rect(x, 240, 120, 34, "tint", rx=0)); p.append(text(x + 60, 262, "OS", 12, 600, anchor="middle"))
        # a programfájl a lemezen, három overlay-szegmensével
        for j, (_, kk) in enumerate(phases):
            xx = x + j * 40
            p.append(rect(xx, 310, 40, 30, kk if j == i else "plain", rx=0))
            p.append(text(xx + 20, 330, str(j + 1), 12, 600 if j == i else 400, cls="ink" if j == i else "quiet", anchor="middle"))
        p.append(text(x + 60, 358, "programfájl a lemezen", 10.5, cls="quiet", anchor="middle"))
        xs = x + i * 40 + 20
        p.append(path(f"M{xs} 308C{xs} 292 {x + 146} 300 {x + 146} 220S{x + 140} 170 {x + 124} 170", m, width=1.5))
    p.append(text(24, 388, "Maga a program (a rezidens része) dönti el, mikor tölti be a következő fázist az előző helyére;", 11.5, cls="quiet"))
    p.append(text(24, 404, "a programozónak úgy kell felosztania a programot, hogy két fázisra soha ne legyen egyszerre szükség.", 11.5, cls="quiet"))
    # tárcsere
    x0 = 580
    p.append(text(x0, 62, "Tárcsere: az OS teljes jobokat mozgat", 13, 600))
    for i, (who, k) in enumerate((("1. job", "acc"), ("2. job", "c2"))):
        x = x0 + i * 160
        p.append(rect(x, 80, 120, 70, "tint", rx=0)); p.append(text(x + 60, 120, "szabad", 11, cls="quiet", anchor="middle"))
        p.append(rect(x, 150, 120, 90, k, rx=0)); p.append(text(x + 60, 200, who, 12, 600, anchor="middle"))
        p.append(rect(x, 240, 120, 34, "tint", rx=0)); p.append(text(x + 60, 262, "OS", 12, 600, anchor="middle"))
        p.append(text(x + 60, 290, "előtte" if i == 0 else "utána", 11, cls="quiet", anchor="middle"))
    p.append(rect(x0 + 100, 310, 100, 34, "plain", rx=4))
    p.append(f'<rect x="{x0 + 104}" y="314" width="44" height="26" class="accf"/><rect x="{x0 + 152}" y="314" width="44" height="26" class="c2f"/>')
    p.append(text(x0 + 126, 332, "1. job", 10.5, anchor="middle")); p.append(text(x0 + 174, 332, "2. job", 10.5, anchor="middle"))
    p.append(text(x0 + 150, 362, "swap-terület a lemezen", 10.5, cls="quiet", anchor="middle"))
    p.append(path(f"M{x0 + 60} 300C{x0 + 60} 318 {x0 + 80} 326 {x0 + 96} 326", m, width=1.5))
    p.append(text(x0 + 54, 328, "kiírás (swap out)", 10.5, cls="quiet", anchor="end"))
    p.append(path(f"M{x0 + 204} 326C{x0 + 240} 326 {x0 + 250} 310 {x0 + 250} 300", m, width=1.5))
    p.append(text(x0 + 258, 328, "beolvasás", 10.5, cls="quiet"))
    p.append(text(x0 + 258, 342, "(swap in)", 10.5, cls="quiet"))
    return svg(900, 420, title, "\n".join(p))


# ---------------- 11. Laphibakezelés: hardver és operációs rendszer ----------------
def faultflow():
    m = "ff"
    title = "Egy laphibát okozó memória-hozzáférés: mit tesz a hardver, és mit tesz az operációs rendszer"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, "Egy laphibát okozó memória-hozzáférés: hardver és operációs rendszer", 15, 600)]
    X, W = 70, 240

    def box(y, s, k="tint", x=X, w=W, h=36, lines=None):
        out = rect(x, y, w, h, k, rx=6)
        ls = lines or [s]
        for i, l in enumerate(ls):
            out += text(x + w / 2, y + h / 2 + 4 + (i - (len(ls) - 1) / 2) * 15, l, 11.5, 600 if k != "tint" else 400, anchor="middle")
        return out

    def arrow(d, lab=None, lx=0, ly=0, anchor="start"):
        out = path(d, m, width=1.4)
        if lab:
            out += text(lx, ly, lab, 10.5, cls="quiet", anchor=anchor)
        return out

    p.append(text(X, 60, "hardver (CPU és MMU)", 12.5, 600, cls="quiet"))
    p.append(box(90, "a CPU kiad egy virtuális címet", "acc"))
    p.append(box(150, "megvan a fordítás a TLB-ben?", "c2"))
    p.append(box(210, "laptábla-bejárás"))
    p.append(box(270, "érvényes a lap, szabad az elérés?", "c2"))
    p.append(box(330, "a fordítás eltárolása a TLB-ben"))
    p.append(box(390, "fizikai cím → gyorsítótár, RAM", "acc"))
    p.append(arrow("M190 126V146")); p.append(arrow("M190 186V206", "nem (TLB-hiány)", 198, 200))
    p.append(arrow("M190 246V266")); p.append(arrow("M190 306V326", "igen", 198, 320)); p.append(arrow("M190 366V386"))
    p.append(arrow("M70 168H50V408H66", "találat", 44, 290, "end"))
    p.append(arrow("M310 288H426", "nem: laphiba", 354, 280, "middle"))
    p.append(text(354, 304, "(kivétel)", 10.5, cls="quiet", anchor="middle"))
    # az operációs rendszer sávja
    p.append('<rect x="400" y="236" width="490" height="452" rx="10" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="6 4"/>')
    p.append(text(416, 256, "operációs rendszer: a laphibakezelő", 12.5, 600, cls="quiet"))
    OX, OW = 430, 270
    p.append(box(270, "a cím egy VMA-ban van, szabad az elérés?", "c2", OX, OW))
    p.append(box(270, "SIGSEGV: programhiba", "bad", 730, 140))
    p.append(arrow("M700 288H726", "nem", 713, 282, "middle"))
    p.append(box(330, "van szabad keret?", "c2", OX, OW))
    p.append(box(318, "", "tint", 730, 140, 60, ["áldozat kitétele; ha", "módosított, előbb", "kiírjuk a lemezre"]))
    p.append(arrow("M700 348H726", "nem", 713, 342, "middle"))
    p.append(arrow("M800 378V408H704"))
    p.append(box(390, "a lap beolvasásának indítása (DMA)", "tint", OX, OW))
    p.append(box(450, "a folyamat blokkol, egy másik fut", "tint", OX, OW))
    p.append(box(510, "lemezmegszakítás: kész az olvasás", "acc", OX, OW))
    p.append(box(570, "laptábla-bejegyzés: keret, érvényes = 1", "tint", OX, OW))
    p.append(box(630, "", "tint", OX, OW, 36, ["a folyamat futásra kész;", "újraindítja az utasítást"]))
    p.append(arrow("M565 306V326", "igen", 573, 320)); p.append(arrow("M565 366V386", "igen", 573, 380))
    p.append(arrow("M565 426V446")); p.append(arrow("M565 486V506")); p.append(arrow("M565 546V566")); p.append(arrow("M565 606V626"))
    p.append(arrow("M700 648H900V78H190V86"))
    p.append(text(560, 70, "ugyanaz az elérés újra: most már érvényes a lap", 10.5, cls="quiet", anchor="middle"))
    # a minor laphibákról szóló megjegyzés a szabad területen
    for i, l in enumerate(["A minor laphibákhoz (egy lap első érintése, copy-on-write,",
                           "a page cache-ben már bent lévő lap) nem kell lemez: a kernel",
                           "kinullázza, átmásolja vagy csak leképezi a keretet, és kihagyja",
                           "a lemezolvasást, a várakozást és a megszakítást."]):
        p.append(text(420, 130 + i * 18, l, 11.5, cls="quiet"))
    p.append(text(24, 712, "A laphiba a hibát okozó utasítás által kiváltott kivétel; csak a lemezolvasás vége megszakításkérés (IRQ).", 11.5, cls="quiet"))
    return svg(920, 728, title, "\n".join(p))


# ---------------- 12. The buddy allocator: split and merge ----------------
def buddy():
    m = "bd"
    title = "A buddy allocator: egy blokk kettévágása egy kéréshez, a buddyk összeolvasztása felszabadításkor"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    X, W = 40, 30                      # 16 frames, 30 px each
    def bar(y, blocks, label1, label2=None):
        # blocks: list of (first frame, number of frames, kind, text)
        for f0, n, k, s in blocks:
            p.append(rect(X + f0 * W, y, n * W, 34, k, rx=0))
            if s:
                p.append(text(X + (f0 + n / 2) * W, y + 22, s, 11.5, 600 if k == "c2" else 400,
                              cls="ink" if k != "tint" else "quiet", anchor="middle"))
        p.append(text(X + 16 * W + 24, y + 15, label1, 12, 600))
        if label2:
            p.append(text(X + 16 * W + 24, y + 31, label2, 11.5, cls="quiet"))
    for f in range(16):
        p.append(text(X + f * W + W / 2, 70, str(f), 10, cls="quiet", anchor="middle"))
    p.append(text(X, 54, "keretszám", 10.5, cls="quiet"))
    bar(78, [(0, 16, "acc", "4. rendű szabad blokk: 16 keret (64 KiB)")],
        "1. egyetlen 4. rendű szabad blokk", "érkezik egy kérés 2 keretre (1. rend)")
    bar(130, [(0, 8, "acc", "3. rend"), (8, 8, "acc", "3. rend")],
        "2. a 16 kettévágása két 8-as buddyra", "a jobb fél a 3. rend szabadlistájára kerül")
    bar(182, [(0, 4, "acc", "2. rend"), (4, 4, "acc", "2. rend"), (8, 8, "tint", "a 3. szabadlistán")],
        "3. a 8 kettévágása két 4-es buddyra", "a jobb fél a 2. rend szabadlistájára kerül")
    bar(234, [(0, 2, "c2", "foglalt"), (2, 2, "acc", "1. r."), (4, 4, "tint", "a 2. listán"), (8, 8, "tint", "a 3. szabadlistán")],
        "4. a 4 kettévágása: 2 + 2, a 0-1. keret kiadva", "szabadlisták: 1. rend {2}, 2. rend {4}, 3. rend {8}")
    # merging
    p.append(text(24, 306, "A 0-1. keret felszabadítása visszafelé járja be a lépéseket: minden szabad buddy összeolvad, a legnagyobb szabad blokkig.", 12.5, 600))
    bar(320, [(0, 2, "acc", "0-1"), (2, 2, "acc", "2-3"), (4, 4, "tint", ""), (8, 8, "tint", "")],
        "5. a 0-1. keret felszabadul; a 2-3 buddy szabad", "összeolvasztás: egy 2. rendű blokk a 0. keretnél")
    bar(372, [(0, 4, "acc", "0-3"), (4, 4, "acc", "4-7"), (8, 8, "tint", "")],
        "6. a 4-7 buddy is szabad", "összeolvasztás: egy 3. rendű blokk a 0. keretnél")
    bar(424, [(0, 8, "acc", "0-7"), (8, 8, "acc", "8-15")],
        "7. a 8-15 buddy is szabad", "összeolvasztás: újra egyetlen 4. rendű blokk")
    p.append(text(24, 490, "A p keretnél kezdődő, 2^k keretes blokk buddyja a p XOR 2^k keretnél kezdődik: a 0-1 és a 2-3 buddyk, a 2-3 és a 4-5 nem.", 11.5, cls="quiet"))
    p.append(text(24, 508, "A Linux rendenként egy szabadlistát tart, a 0. rendtől (4 KiB) a 10. rendig (4 MiB); a /proc/buddyinfo megszámolja az egyes listák blokkjait.", 11.5, cls="quiet"))
    return svg(920, 524, title, "\n".join(p))


# ---------------- 13. A slab cache ----------------
def slab():
    m = "sl"
    title = "Egy slab cache: a buddy allocatortól kapott lapok, egyetlen méretű objektumokra vágva"
    p = [f"<defs>{marker(m)}{marker('sl2', 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # callers
    p.append(rect(24, 56, 210, 40, "tint", rx=6)); p.append(text(129, 81, "d_alloc(): egy új dentry", 12, 600, anchor="middle"))
    p.append(path("M234 76H262", m))
    # the dentry cache
    p.append(rect(266, 48, 630, 316, "plain", rx=8))
    p.append(text(282, 72, "„dentry” cache: 192 bájtos objektumok, slabenként 21, egy slab = egy 4 KiB-os lap (0. rend)", 12.5, 600))
    CW = 22
    X0 = 400
    def slabrow(y, used, label):
        p.append(text(282, y + 17, label, 11.5, 600))
        for i in range(21):
            p.append(rect(X0 + i * CW, y, CW - 3, 24, "c2" if i in used else "acc", rx=2))
    slabrow(90, {0, 1, 2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19}, "CPU 0 slabje")
    for a, b in ((4, 7), (7, 16), (16, 20)):
        xa = X0 + a * CW + 9; xb = X0 + b * CW + 9
        p.append(path(f"M{xa} 116C{xa} 132 {xb} 132 {xb} 118", "sl2", cls="acc", width=1.25))
    slabrow(146, {0, 2, 3, 4, 7, 8, 9, 10, 12, 13, 15, 16, 17, 18, 19, 20}, "CPU 1 slabje")
    slabrow(196, {1, 4, 5, 9, 12, 17}, "részleges slab")
    slabrow(228, {0, 3, 6, 7, 8, 11, 14, 15, 20}, "részleges slab")
    slabrow(274, set(range(21)), "teli slab")
    p.append(text(282, 322, "Minden CPU a saját slabjéből vesz objektumokat, zár nélkül, és a részleges slabekből tölti fel.", 11.5, cls="quiet"))
    p.append(text(282, 340, "Egy slab szabad objektumait a bennük tárolt mutató fűzi láncba (nyilak a CPU 0 slabjében).", 11.5, cls="quiet"))
    # legend
    p.append(rect(24, 150, 16, 14, "c2", rx=2)); p.append(text(48, 162, "használt objektum", 11.5))
    p.append(rect(24, 174, 16, 14, "acc", rx=2)); p.append(text(48, 186, "szabad objektum", 11.5))
    for i, l in enumerate(["A kmalloc(100) kérést", "ugyanígy szolgálja ki", "a kmalloc-128 cache", "(128 bájtos objektumok)."]):
        p.append(text(24, 230 + i * 17, l, 11.5, cls="quiet"))
    # buddy allocator
    p.append(rect(266, 412, 630, 52, "tint", rx=8))
    p.append(text(282, 436, "buddy allocator: 2^k lapos szabad blokkok", 12.5, 600))
    p.append(text(282, 454, "nagyobb objektumokhoz nagyobb slabek (ext4_inode_cache: 1,1 KiB-os objektumok, 14 egy 16 KiB-os slabben)", 11.5, cls="quiet"))
    p.append(path("M420 410V368", m)); p.append(text(430, 394, "új slab, ha nem maradt szabad objektum", 11.5, cls="quiet"))
    p.append(path("M870 368V410", m)); p.append(text(860, 394, "az üres slab visszakerül", 11.5, cls="quiet", anchor="end"))
    p.append(text(24, 494, "Nincs keresés, a slabon belül nincs külső fragmentáció, és a felszabadított objektum hamar újra használatba kerül, gyakran még a CPU gyorsítótárában.", 11.5, cls="quiet"))
    return svg(920, 510, title, "\n".join(p))


# ---------------- 14. Where malloc gets memory ----------------
def malloc_fig():
    m = "ma"
    title = "Honnan kap memóriát a malloc: kis blokkokhoz a heapből (brk), nagyokhoz saját leképezésből (mmap)"
    p = [f"<defs>{marker(m)}{marker('ma2', 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # address space strip
    X, Wd = 40, 220
    p.append(text(X, 56, "egy folyamat virtuális címtartománya", 12, 600))
    segs = [(66, 40, "tint", "verem (fő szál)", None),
            (106, 26, "plain", "", None),
            (132, 30, "tint", "megosztott könyvtárak (libc)", None),
            (162, 40, "c2", "1 MiB-os blokk: saját mmap", "munmap szabadítja fel"),
            (202, 48, "acc", "a 2. szál arenája", "64 MiB lefoglalva, ezen belül nő"),
            (250, 46, "plain", "", None),
            (296, 70, "acc", "heap (fő arena)", None),
            (366, 30, "tint", "programkód és adatok", None)]
    for y, h, k, s, s2 in segs:
        p.append(rect(X, y, Wd, h, k, rx=0))
        if s:
            p.append(text(X + Wd / 2, y + (h / 2 + 4 if not s2 else h / 2 - 3), s, 11.5, 600, anchor="middle"))
        if s2:
            p.append(text(X + Wd / 2, y + h / 2 + 12, s2, 10.5, cls="quiet", anchor="middle"))
    p.append(text(X + Wd / 2, 268, "nem használt", 11, cls="quiet", anchor="middle"))
    p.append(text(X + Wd / 2, 122, "nem használt", 11, cls="quiet", anchor="middle"))
    p.append(text(X + Wd / 2, 289, "↑ program break, a brk() mozgatja", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(X, 414, "fent a magas címek; a heap felfelé nő, a leképezések a verem alá kerülnek", 10.5, cls="quiet"))
    # the heap in detail
    HX = 420
    p.append(text(HX, 56, "a heap belseje: chunkok, mindegyik méretfejléccel", 12, 600))
    chunks = [(60, "c2", "foglalt"), (54, "acc", "szabad"), (76, "c2", "foglalt"), (30, "c2", ""), (60, "acc", "szabad"), (70, "c2", "foglalt"), (70, "tint", "top")]
    x = HX
    for w, k, s in chunks:
        p.append(rect(x, 70, w, 36, k, rx=0))
        p.append(f'<rect x="{x}" y="70" width="6" height="36" class="edgef"/>')
        if s:
            p.append(text(x + w / 2 + 3, 93, s, 11, 600 if k == "c2" else 400, anchor="middle", cls="ink" if k != "tint" else "quiet"))
        x += w
    p.append(text(HX, 124, "szürke szél = fejléc (méret, jelzőbitek); „top” = a szabad maradék a program breakig", 10.5, cls="quiet"))
    # bins
    bins = [("tcache", "szálanként, méretenként 7 chunk, 1 KiB-ig: semmilyen zár"),
            ("fast bins", "kis méretek (alapból 128 B-ig), összeolvasztás nélkül"),
            ("small bins", "binenként egyetlen pontos méret, 1 KiB alatt"),
            ("unsorted bin", "friss szabad chunkok; a következő malloc rendezi el"),
            ("large bins", "mérettartományok, méret szerint rendezve, best fit")]
    y = 152
    p.append(text(HX, y - 6, "a szabad chunkok binekben várnak; a malloc nagyjából ebben a sorrendben nézi:", 11.5, 600))
    for name, desc in bins:
        p.append(rect(HX, y, 110, 28, "acc", rx=4)); p.append(text(HX + 55, y + 18, name, 11.5, 600, anchor="middle"))
        p.append(text(HX + 120, y + 18, desc, 11, cls="quiet"))
        y += 36
    p.append(text(HX, y + 14, "ha egyik bin sem jó: a chunkot a top chunkból vágja le;", 11.5))
    p.append(text(HX, y + 32, "ha a top túl kicsi: a brk() megnöveli a heapet, de az mmap-küszöböt", 11.5, cls="c2"))
    p.append(text(HX, y + 50, "(kezdetben 128 KiB) elérő kérés saját leképezést kap", 11.5, cls="c2"))
    return svg(920, 430, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("malloc-heap", malloc_fig), ("buddy-allocator", buddy), ("slab-cache", slab), ("separation", separation), ("fragmentation", fragmentation), ("paging", paging),
                     ("address-translation", translation), ("x86-64-page-walk", multilevel), ("tlb-path", tlbpath),
                     ("belady-anomaly", belady), ("tlb-measured", tlbchart), ("thrashing", thrash),
                     ("overlays-swapping", overlays), ("page-fault-flow", faultflow)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
