"""Generate the SVG figures for the Concurrency, Deadlocks and Linux Scheduling lecture (Hungarian version).

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
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



import sched_sim


def ell(cx, cy, rx, ry, kind="plain"):
    cls = {"acc": ("accf", "acc"), "c2": ("c2f", "c2s"), "bad": ("badf", "bads")}.get(kind)
    if cls:
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" class="{cls[0]}"/>'
                f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" class="{cls[1]}" stroke-width="1.75"/>')
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" class="tint"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" class="edge" stroke-width="1.5"/>')


def label(x, y, s, size=11.5, cls="quiet", anchor="middle", weight=400):
    return text(x, y, s, size, weight, cls=cls, anchor=anchor)


# ---------------- 1. Process state space with three scheduling horizons ----------------
def states():
    m = "st"
    title = "Folyamatállapotok és a három ütemező"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # regions (do not overlap)
    p.append('<rect x="560" y="48" width="290" height="96" rx="30" fill="none" class="edge" stroke-width="1.5" stroke-dasharray="7 6"/>')
    p.append(label(576, 136, "hosszú távú ütemező", 11.5, "quiet", "start", 600))
    p.append('<rect x="190" y="170" width="520" height="220" rx="36" fill="none" class="acc" stroke-width="1.5" stroke-dasharray="7 6"/>')
    p.append(label(696, 380, "rövid távú ütemező", 11.5, "acct", "end", 600))
    p.append('<rect x="40" y="420" width="520" height="116" rx="36" fill="none" class="c2s" stroke-width="1.5" stroke-dasharray="7 6"/>')
    p.append(label(546, 528, "középtávú ütemező", 11.5, "c2", "end", 600))
    # nodes
    p.append(ell(700, 96, 74, 28)); p.append(label(700, 92, "program", 12.5, "ink", weight=600)); p.append(label(700, 108, "(új / befejezett)", 10.5))
    p.append(ell(300, 240, 72, 30, "acc")); p.append(label(300, 238, "futásra kész", 13, "ink", weight=600)); p.append(label(300, 254, "sok (N)", 10.5))
    p.append(ell(590, 240, 72, 30, "acc")); p.append(label(590, 238, "futó", 13, "ink", weight=600)); p.append(label(590, 254, "CPU-nként egy", 10.5))
    p.append(ell(445, 340, 70, 28, "acc")); p.append(label(445, 345, "várakozó", 13, "ink", weight=600))
    p.append(ell(790, 300, 60, 26)); p.append(label(790, 305, "zombi", 13, "ink", weight=600))
    p.append(ell(150, 478, 74, 30, "c2")); p.append(label(150, 474, "felfüggesztett", 12, "ink", weight=600)); p.append(label(150, 490, "futásra kész", 12, "ink", weight=600))
    p.append(ell(420, 478, 74, 30, "c2")); p.append(label(420, 474, "felfüggesztett", 12, "ink", weight=600)); p.append(label(420, 490, "várakozó", 12, "ink", weight=600))
    # admission and exit
    p.append(path("M626 96C460 96 330 130 306 206", m, width=1.4)); p.append(label(440, 92, "befogadás: fork() + exec()", 11.5))
    p.append(path("M650 256C700 270 720 280 732 290", m, width=1.4)); p.append(label(668, 236, "exit()", 11.5, anchor="start")); p.append(label(668, 251, "vagy leállítják", 11.5, anchor="start"))
    p.append(path("M790 274V126", m, width=1.4)); p.append(label(800, 196, "a szülő", 11.5, anchor="start")); p.append(label(800, 211, "wait()-je", 11.5, anchor="start")); p.append(label(800, 226, "begyűjti", 11.5, anchor="start"))
    # short-term
    p.append(path("M372 232H516", m, width=1.4)); p.append(label(444, 224, "kiosztás", 11.5))
    p.append(path("M532 262C500 282 400 282 352 264", m, width=1.4)); p.append(label(444, 296, "lejárt időszelet / yield", 11.5))
    p.append(path("M612 268C612 310 560 336 516 340", m, width=1.4)); p.append(label(624, 312, "várakozás:", 11.5, anchor="start")); p.append(label(624, 327, "I/O, zár,", 11.5, anchor="start")); p.append(label(624, 342, "szemafor", 11.5, anchor="start"))
    p.append(path("M376 342C320 340 290 310 294 272", m, width=1.4)); p.append(label(318, 316, "esemény", 11.5, anchor="start"))
    # medium-term
    p.append(path("M250 260C210 320 170 390 152 446", m, width=1.4)); p.append(label(176, 370, "kivitel", 11.5, anchor="end"))
    p.append(path("M180 450C210 380 250 320 272 268", m, width=1.4, dash="4 4")); p.append(label(222, 400, "behozás", 11.5, anchor="start"))
    p.append(path("M440 368C436 400 430 420 425 446", m, width=1.4)); p.append(label(446, 412, "kivitel", 11.5, anchor="start"))
    p.append(path("M346 478H226", m, width=1.4)); p.append(label(286, 470, "esemény", 11.5))
    p.append(text(24, 566, "Stallingsnál: Ready/Suspend és Blocked/Suspend. Linuxban a futásra kész és a futó egyaránt „R”, a várakozó S vagy D,", 11.5, cls="quiet"))
    p.append(text(24, 584, "a felfüggesztett állapotok szerepét pedig a leállított folyamatok (T) és a swapre kivitt memória tölti be.", 11.5, cls="quiet"))
    return svg(870, 600, title, "\n".join(p))


# ---------------- 2. Layers of synchronisation ----------------
def layers():
    m = "ly"
    title = "Kölcsönös kizárás három rétegben"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    rows = [("Alkalmazás", "Java: synchronized (monitorenter)   C++: std::mutex, std::lock_guard", "plain"),
            ("Operációs rendszer", "mutex, szemafor, feltételváltozó; futex: altatás és ébresztés csak versengés esetén", "acc"),
            ("Hardver", "atomi utasítások: xchg (test-and-set), lock cmpxchg (compare-and-swap); memóriakorlátok", "c2")]
    for i, (a, b, k) in enumerate(rows):
        y = 52 + i * 74
        p.append(rect(24, y, 700, 58, "tint" if k == "plain" else k, rx=8))
        p.append(text(40, y + 25, a, 13.5, 600)); p.append(text(40, y + 45, b, 11.5, cls="quiet"))
    p.append(path("M742 82C770 100 770 116 742 134", m, width=1.4)); p.append(path("M742 156C770 174 770 190 742 208", m, width=1.4))
    p.append(text(782, 112, "erre épül", 11.5, cls="quiet")); p.append(text(782, 186, "erre épül", 11.5, cls="quiet"))
    p.append(text(24, 290, "A gyors út sosem hagyja el a felhasználói teret: egy versengés nélküli pthread_mutex_lock() egyetlen lock cmpxchg.", 11.5, cls="quiet"))
    p.append(text(24, 308, "Csak a várakozni kényszerülő szál hív futex() rendszerhívást, hogy a kernel elaltassa, és később felébressze.", 11.5, cls="quiet"))
    return svg(860, 324, title, "\n".join(p))


# ---------------- 3. Store buffer breaks Peterson ----------------
def reorder():
    m = "ro"
    title = "Miért hibázik Peterson algoritmusa egy modern processzoron?"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    for i, x in enumerate((40, 470)):
        p.append(rect(x, 52, 340, 150, "tint", rx=8))
        p.append(text(x + 14, 74, f"{i}. mag  ({i}. szál)", 13, 600))
        p.append(text(x + 14, 98, f"1. flag[{i}] = 1", 12)); p.append(text(x + 14, 118, f"2. turn = {1 - i}", 12))
        p.append(text(x + 14, 138, f"3. flag[{1 - i}] olvasása → 0 (régi!)", 12, 600))
        p.append(text(x + 14, 158, "4. belép a kritikus szakaszba", 12, cls="bad"))
        p.append(rect(x + 196, 82, 130, 64, "c2", rx=6))
        p.append(text(x + 261, 102, "store buffer", 11.5, 600, anchor="middle"))
        p.append(text(x + 261, 120, f"flag[{i}] = 1", 11, anchor="middle")); p.append(text(x + 261, 136, f"turn = {1 - i}", 11, anchor="middle"))
        p.append(path(f"M{x + 261} 146V246", m, width=1.4, dash="5 4"))
        p.append(text(x + 268, 226, "később íródik ki", 11, cls="quiet"))
    p.append(rect(40, 250, 770, 40, "acc", rx=8))
    p.append(text(425, 275, "közös memória:  flag[0] = 0,  flag[1] = 0  (még mindig)", 12.5, 600, anchor="middle"))
    p.append(text(24, 318, "Az írások a store bufferben várnak, az olvasások egyenesen a memóriához mennek: mindkét mag 0-nak látja a másik jelzőjét.", 11.5, cls="quiet"))
    p.append(text(24, 336, "A 2. és 3. lépés közötti teljes memóriakorlát (mfence vagy lock előtagú utasítás) kiüríti a puffert: a kizárás helyreáll.", 11.5, cls="quiet"))
    return svg(850, 352, title, "\n".join(p))


# ---------------- 4. The one-lane bridge ----------------
def bridge():
    m = "br"
    title = "Holtpont egy egysávos hídon és az erőforrásgráfja"
    p = [f"<defs>{marker(m)}{marker('brb', 'bad')}</defs>", text(24, 30, title, 15, 600)]
    # bridge
    p.append(rect(60, 100, 160, 40, "acc", rx=2)); p.append(rect(220, 100, 160, 40, "acc", rx=2))
    p.append(text(140, 125, "nyugati fél", 12, 600, anchor="middle")); p.append(text(300, 125, "keleti fél", 12, 600, anchor="middle"))
    p.append(f'<path d="M20 140H60M380 140H420" class="edge" stroke-width="3"/>')
    # cars
    p.append(rect(110, 70, 60, 24, "c2", rx=10)); p.append(text(140, 87, "A autó →", 11, 600, anchor="middle"))
    p.append(rect(270, 146, 60, 24, "c2", rx=10)); p.append(text(300, 163, "← B autó", 11, 600, anchor="middle"))
    p.append(text(220, 206, "A a nyugati felet birtokolja, és a keletire van szüksége;", 11.5, cls="quiet", anchor="middle"))
    p.append(text(220, 224, "B a keleti felet birtokolja, és a nyugatira van szüksége.", 11.5, cls="quiet", anchor="middle"))
    # graph
    gx = 500
    p.append(text(gx, 64, "Erőforrás-foglalási gráf", 13, 600))
    P = {"A": (gx + 30, 110), "B": (gx + 230, 190), "W": (gx + 230, 110), "E": (gx + 30, 190)}
    for k in "AB":
        x, y = P[k]; p.append(ell(x, y, 26, 20, "c2")); p.append(label(x, y + 4, k + " autó", 11, "ink", weight=600))
    for k, n in (("W", "nyugat"), ("E", "kelet")):
        x, y = P[k]; p.append(rect(x - 30, y - 18, 60, 36, "acc", rx=4)); p.append(label(x, y + 4, n, 11, "ink", weight=600))
    p.append(path(f"M{gx + 200} 110H{gx + 58}", m, width=1.5)); p.append(label(gx + 130, 102, "birtokolja", 10.5))
    p.append(path(f"M{gx + 30} 132V{gx * 0 + 170}", "brb", cls="bads", width=1.5)); p.append(label(gx + 38, 155, "akarja", 10.5, anchor="start"))
    p.append(path(f"M{gx + 60} 190H{gx + 202}", m, width=1.5)); p.append(label(gx + 130, 182, "birtokolja", 10.5))
    p.append(path(f"M{gx + 230} 168V130", "brb", cls="bads", width=1.5)); p.append(label(gx + 222, 155, "akarja", 10.5, anchor="end"))
    p.append(text(gx, 240, "Kör: A → kelet → B → nyugat → A", 11.5, cls="bad"))
    p.append(text(24, 268, "Javítás: globális sorrendben foglalni a feleket (előbb a nyugatit: nem alakulhat ki kör), vagy az egész hidat", 11.5, cls="quiet"))
    p.append(text(24, 286, "egy szemaforral (közlekedési lámpával) védett erőforrásnak tekinteni: így egy autó sem vár úgy, hogy közben egy felet birtokol.", 11.5, cls="quiet"))
    return svg(800, 302, title, "\n".join(p))


# ---------------- 5. Gantt charts ----------------
def gantt():
    jobs = [("A", 0, 6), ("B", 1, 3), ("C", 2, 8), ("D", 3, 5), ("E", 4, 2)]
    title = "Öt feladat, négy ütemező"
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Feladatok (érkezés, hossz): A (0, 6), B (1, 3), C (2, 8), D (3, 5), E (4, 2). Jobb oldalt az átlagos várakozási idő.", 11.5, cls="quiet")]
    x0, unit = 110, 24
    colours = {"A": "#2f6fd6", "B": "#d9822b", "C": "#2e9e5b", "D": "#b04ad0", "E": "#c8372d"}
    for i, (lab, pol, q) in enumerate([("FIFO", "FIFO", None), ("SJF", "SJF", None), ("SRTF", "SRTF", None), ("RR, q = 2", "RR", 2)]):
        y = 74 + i * 46
        tl, (w, ta, r, end) = sched_sim.simulate(jobs, pol, q)
        merged = []
        for seg in tl:                              # join back-to-back runs of the same job
            if merged and merged[-1][0] == seg[0] and abs(merged[-1][2] - seg[1]) < 1e-9:
                merged[-1] = (seg[0], merged[-1][1], seg[2])
            else:
                merged.append(seg)
        tl = merged
        p.append(text(24, y + 21, lab, 12.5, 600))
        for name, a, b in tl:
            p.append(f'<rect x="{x0 + a * unit:.1f}" y="{y}" width="{(b - a) * unit:.1f}" height="30" fill="{colours[name]}" fill-opacity=".85" stroke="#fff" stroke-width="1"/>')
            if (b - a) * unit >= 16:
                p.append(f'<text x="{x0 + (a + b) / 2 * unit:.1f}" y="{y + 20}" font-size="12" font-weight="600" fill="#fff" text-anchor="middle">{name}</text>')
        p.append(text(x0 + 24 * unit + 14, y + 21, f"{w:.1f}".replace(".", ","), 12.5, 600))
    yb = 74 + 4 * 46
    for t in range(0, 25, 2):
        p.append(f'<line x1="{x0 + t * unit}" y1="{yb - 6}" x2="{x0 + t * unit}" y2="{yb}" class="edge" stroke-width="1.25"/>')
        p.append(text(x0 + t * unit, yb + 14, str(t), 10.5, cls="quiet", anchor="middle"))
    p.append(text(x0 + 24 * unit + 14, 66, "várakozás", 11.5, cls="quiet"))
    p.append(text(24, yb + 40, "Az SJF és az SRTF adja a legkisebb átlagos várakozást, de előre ismernie kell a hosszakat, és kiéheztetheti a hosszúakat;", 11.5, cls="quiet"))
    p.append(text(24, yb + 58, "a Round Robinnál átlagosan többet várnak, de mindenki hamar sorra kerül (válaszidő): ezt érzi az interaktív felhasználó.", 11.5, cls="quiet"))
    return svg(820, yb + 74, title, "\n".join(p))


# ---------------- 6. Linux scheduling classes ----------------
def classes():
    title = "A Linux ütemezési osztályai a legmagasabb prioritástól a legalacsonyabbig"
    p = [text(24, 30, title, 15, 600)]
    rows = [("stop", "kernelen belüli: CPU-k menet közbeni be- és kikapcsolása, feladatok átköltöztetése", "plain"),
            ("deadline", "SCHED_DEADLINE: futásidő / határidő / periódus, a legkorábbi határidő először", "bad"),
            ("valós idejű", "SCHED_FIFO, SCHED_RR: statikus prioritás 1–99, mindig a magasabb fut először", "c2"),
            ("méltányos (EEVDF)", "SCHED_NORMAL (= SCHED_OTHER), SCHED_BATCH, SCHED_IDLE: súly szerinti részesedés (nice −20 … 19)", "acc"),
            ("ext", "sched_ext: BPF-programként betöltött ütemező (opcionális, Linux 6.12+)", "plain"),
            ("idle", "az idle (tétlen) feladat: csak akkor fut, ha semmi más nem tud", "plain")]
    for i, (a, b, k) in enumerate(rows):
        y = 48 + i * 44
        p.append(rect(24, y, 760, 36, k if k != "plain" else "tint", rx=6))
        p.append(text(40, y + 23, a, 12.5, 600)); p.append(text(184, y + 23, b, 11.5, cls="quiet"))
    y = 48 + 6 * 44 + 10
    p.append(text(24, y + 8, "A méltányos osztályon belül: két processzorigényes feladat egy magon, mérve (shares.sh)", 13, 600))
    for j, (lab, share, w) in enumerate([("nice 0 vs. nice 5", 75.3, (748, 244)), ("nice 0 vs. nice 10", 90.3, (897, 96))]):
        yy = y + 24 + j * 40
        tot = sum(w); a = 560 * w[0] / tot
        p.append(text(24, yy + 19, lab, 12, 600))
        p.append(f'<rect x="170" y="{yy}" width="{a:.1f}" height="28" class="accf"/><rect x="170" y="{yy}" width="{a:.1f}" height="28" fill="none" class="acc" stroke-width="1.5"/>')
        p.append(f'<rect x="{170 + a:.1f}" y="{yy}" width="{560 - a:.1f}" height="28" class="c2f"/><rect x="{170 + a:.1f}" y="{yy}" width="{560 - a:.1f}" height="28" fill="none" class="c2s" stroke-width="1.5"/>')
        p.append(text(180, yy + 19, f"{100 * w[0] / tot:.0f}% mért", 11.5, 600))
        p.append(text(740, yy + 19, "a súlyok alapján " + f"{share:.1f}".replace(".", ",") + "%", 11.5, cls="quiet"))
    return svg(900, y + 112, title, "\n".join(p))


# ---------------- 7. The railway semaphore ----------------
def signal(x, y, state, side=1, h=56):
    """A railway semaphore signal: post from (x, y) up by h; arm horizontal (stop) or raised (go).
    side=+1: arm points right, -1: left."""
    top = y - h
    p = [f'<path d="M{x} {y}V{top}" class="edge" stroke-width="3" fill="none"/>',
         f'<path d="M{x - 7} {y}H{x + 7}" class="edge" stroke-width="3" fill="none"/>']
    if state == "stop":
        p.append(f'<path d="M{x} {top + 4}H{x + side * 34}" class="bads" stroke-width="7" fill="none" stroke-linecap="round"/>')
    else:
        p.append(f'<path d="M{x} {top + 4}L{x + side * 24} {top - 20}" class="acc" stroke-width="7" fill="none" stroke-linecap="round"/>')
    p.append(f'<circle cx="{x}" cy="{top + 4}" r="4" class="ink"/>')
    return "".join(p)


def railway():
    title = "A vasúti szemafor: az egyvágányú szakaszon egyszerre egy vonat"
    p = [text(24, 30, title, 15, 600)]
    # critical section band
    p.append(f'<rect x="250" y="122" width="350" height="36" rx="6" class="accf"/>')
    # tracks
    tr = 'class="edge" stroke-width="3" fill="none"'
    p.append(f'<path d="M30 110H200L250 140H600L650 110H820" {tr}/>')
    p.append(f'<path d="M30 170H200L250 140M600 140L650 170H820" {tr}/>')
    # trains
    p.append(rect(360, 128, 96, 24, "c2", rx=10)); p.append(text(408, 145, "A vonat →", 11.5, 600, anchor="middle"))
    p.append(rect(680, 96, 96, 24, "c2", rx=10)); p.append(text(728, 113, "← B vonat", 11.5, 600, anchor="middle"))
    # signals guarding both ends; both at stop because A is inside (S = 0)
    p.append(signal(240, 114, "stop", 1)); p.append(signal(610, 114, "stop", -1))
    p.append(text(425, 186, "egyvágányú szakasz = kritikus szakasz;  S = 0 (foglalt)", 12, 600, cls="acct", anchor="middle"))
    p.append(text(425, 204, "A a P(S) művelettel lépett be, és foglalja a pályát; B a keleti jelzőnél vár, amíg A V(S)-sel ki nem lép", 11.5, cls="quiet", anchor="middle"))
    p.append(text(228, 66, "nyugati jelző", 11, cls="quiet", anchor="end"))
    p.append(text(622, 66, "keleti jelző", 11, cls="quiet", anchor="start"))
    # legend: the two arm positions
    y0 = 300
    p.append(rect(24, 228, 800, 108, "tint", rx=8))
    p.append(signal(80, y0 + 20, "stop", 1)); p.append(signal(470, y0 + 20, "go", 1))
    p.append(text(140, 262, "vízszintes kar: MEGÁLLJ", 12.5, 600)); p.append(text(140, 282, "S = 0: a P(S)-t végrehajtó vonatnak várnia kell", 11.5, cls="quiet"))
    p.append(text(140, 300, "(a szakasz foglalt)", 11.5, cls="quiet"))
    p.append(text(530, 262, "felemelt kar: SZABAD", 12.5, 600)); p.append(text(530, 282, "S = 1: a P(S) átenged, és S = 0 lesz,", 11.5, cls="quiet"))
    p.append(text(530, 300, "a jelzők a vonat mögött megállj állásba", 11.5, cls="quiet"))
    p.append(text(530, 318, "váltanak", 11.5, cls="quiet"))
    p.append(text(24, 362, "A szakasz elhagyása a V(S): S ismét 1 lesz, és egy várakozó vonat beléphet. Az n kezdőértékű szemafor egyszerre n vonatot enged be.", 11.5, cls="quiet"))
    return svg(844, 378, title, "\n".join(p))


# ---------------- 8. Classic Unix sleep priorities ----------------
def unix_prio():
    m = "up"
    title = "A klasszikus Unix folyamatprioritásai (System V, Bach, 1986 nyomán)"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    rows = ["swapper", "lemez-I/O-ra vár", "pufferre vár", "inode-ra vár",
            ("bads", "bad", "PZERO: szignálküszöb"),
            "tty-bemenetre vár", "tty-kimenetre vár", "gyermek kilépésére vár",
            ("edge", "quiet", "PUSER: felhasználói alap"),
            "0. felhasználói szint", "1. felhasználói szint", "⋮", "n. felhasználói szint"]
    beads = [1, 3, 1, 2, None, 2, 0, 1, None, 2, 3, 0, 1]
    x0, w, rh, y0 = 250, 300, 30, 56
    y = y0
    ys = []
    for r, b in zip(rows, beads):
        if isinstance(r, tuple):
            p.append(f'<path d="M{x0 - 120} {y + 7}H{x0 + w + 80}" class="{r[0]}" stroke-width="2.5" fill="none"/>')
            p.append(text(x0 + w + 86, y + 11, r[2], 11, 600, cls=r[1]))
            ys.append(y); y += 14; continue
        n = len(ys)
        kind = "c2" if n < 4 else ("acc" if n < 8 else "tint")
        p.append(rect(x0, y, w, rh - 4, kind, rx=4))
        p.append(text(x0 + 12, y + 18, r, 12, 600 if n < 8 else 400))
        for i in range(b):
            cx = x0 + w + 22 + i * 22
            if i: p.append(f'<path d="M{cx - 15} {y + 13}H{cx - 7}" class="edge" stroke-width="1.5" fill="none"/>')
            p.append(f'<circle cx="{cx}" cy="{y + 13}" r="7" class="tint"/><circle cx="{cx}" cy="{y + 13}" r="7" fill="none" class="edge" stroke-width="1.5"/>')
        ys.append(y); y += rh
    yend = y
    # brackets
    def bracket(xb, ya, yb, lab1, lab2, cls):
        p.append(f'<path d="M{xb + 8} {ya}H{xb}V{yb}H{xb + 8}" fill="none" class="{cls}" stroke-width="1.5"/>')
        p.append(text(xb - 8, (ya + yb) / 2 - 2, lab1, 11.5, 600, anchor="end"))
        if lab2: p.append(text(xb - 8, (ya + yb) / 2 + 14, lab2, 11, cls="quiet", anchor="end"))
    bracket(x0 - 14, ys[0], ys[3] + rh - 4, "nem megszakítható", "szignállal", "c2s")
    bracket(x0 - 14, ys[5], ys[7] + rh - 4, "megszakítható", "szignállal", "acc")
    bracket(x0 - 14, ys[9], yend - 4, "felhasználói módú", "prioritások", "edge")
    p.append(f'<path d="M{x0 - 150} {ys[0]}V{ys[7] + rh - 4}" fill="none" class="edge" stroke-width="1.25"/>')
    p.append(text(x0 - 158, (ys[0] + ys[7]) / 2 + 2, "kernelmódú", 11.5, 600, anchor="end"))
    p.append(text(x0 - 158, (ys[0] + ys[7]) / 2 + 18, "alvási", 11.5, 600, anchor="end"))
    p.append(text(x0 - 158, (ys[0] + ys[7]) / 2 + 34, "prioritások", 11.5, 600, anchor="end"))
    p.append(path(f"M{x0 + w + 260} {yend - 10}V{y0 + 4}", m, width=1.4))
    p.append(text(x0 + w + 252, y0 + 60, "magasabb", 11, cls="quiet", anchor="end"))
    p.append(text(x0 + w + 252, y0 + 74, "prioritás", 11, cls="quiet", anchor="end"))
    p.append(text(x0 + w + 22, y0 - 6, "alvó folyamatok sora", 10.5, cls="quiet"))
    p.append(text(24, yend + 24, "A kernelben elalvó folyamat a várt eseménytől kapja a prioritását, így ébredés után minden felhasználói módú folyamat", 11.5, cls="quiet"))
    p.append(text(24, yend + 42, "előtt fut, és hamar felszabadítja a nála lévő puffereket és inode-okat. PZERO fölött szignál nem ébresztheti fel (Linux: D állapot);", 11.5, cls="quiet"))
    p.append(text(24, yend + 60, "PZERO és PUSER között igen (Linux: S állapot). A létrán lejjebb numerikusan nagyobb prioritásérték tartozik.", 11.5, cls="quiet"))
    return svg(840, yend + 76, title, "\n".join(p))


# ---------------- 9. Gridlock at a crossroads and its resource-allocation graph ----------------
def gridlock():
    m, mb = "gl", "glb"
    title = "Bedugult kereszteződés: négy autó, négy negyed, egy kör"
    hu = {"NW": "ÉNy", "NE": "ÉK", "SE": "DK", "SW": "DNy"}
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    # roads
    cx, cy, half = 190, 200, 56
    p.append(f'<rect x="{cx - half}" y="50" width="{2 * half}" height="300" class="tint"/>')
    p.append(f'<rect x="40" y="{cy - half}" width="300" height="{2 * half}" class="tint"/>')
    p.append(f'<path d="M{cx - half} 50V{cy - half}H40M{cx + half} 50V{cy - half}H340M{cx - half} 350V{cy + half}H40M{cx + half} 350V{cy + half}H340" fill="none" class="edge" stroke-width="1.5"/>')
    p.append(f'<path d="M{cx} 50V{cy - half}M{cx} {cy + half}V350M40 {cy}H{cx - half}M{cx + half} {cy}H340" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="8 6"/>')
    p.append(f'<rect x="{cx - half}" y="{cy - half}" width="{2 * half}" height="{2 * half}" class="accf"/>')
    p.append(f'<path d="M{cx} {cy - half}V{cy + half}M{cx - half} {cy}H{cx + half}" fill="none" class="acc" stroke-width="1" stroke-dasharray="3 3"/>')
    q = {"NW": (cx - 28, cy - 28), "NE": (cx + 28, cy - 28), "SE": (cx + 28, cy + 28), "SW": (cx - 28, cy + 28)}
    for k, (x, y) in q.items():
        p.append(text(x + (-20 if "W" in k else 20), y + (-20 if "N" in k else 26), hu[k], 10, 600, cls="acct", anchor="middle"))
    # cars (right-hand traffic, all going straight): (label, quarter held, size, arrow direction)
    cars = [("1", "SE", "up"), ("2", "NE", "left"), ("3", "NW", "down"), ("4", "SW", "right")]
    for lab, k, d in cars:
        x, y = q[k]
        vw, vh = (20, 34) if d in ("up", "down") else (34, 20)
        p.append(rect(x - vw / 2, y - vh / 2, vw, vh, "c2", rx=4))
        p.append(text(x, y + 4, lab, 11, 700, anchor="middle"))
    # queues behind each car
    for (x, y, vw, vh) in [(cx + 28, cy + 92, 20, 30), (cx + 28, cy + 130, 20, 30), (cx + 92, cy - 28, 30, 20), (cx + 130, cy - 28, 30, 20),
                           (cx - 28, cy - 92, 20, 30), (cx - 28, cy - 130, 20, 30), (cx - 92, cy + 28, 30, 20), (cx - 130, cy + 28, 30, 20)]:
        p.append(rect(x - vw / 2, y - vh / 2, vw, vh, "plain", rx=4))
    # wants-arrows inside the crossroads
    p.append(path(f"M{cx + 28} {cy + 8}V{cy - 8}", mb, cls="bads", width=1.5))
    p.append(path(f"M{cx + 8} {cy - 28}H{cx - 8}", mb, cls="bads", width=1.5))
    p.append(path(f"M{cx - 28} {cy - 8}V{cy + 8}", mb, cls="bads", width=1.5))
    p.append(path(f"M{cx - 8} {cy + 28}H{cx + 8}", mb, cls="bads", width=1.5))
    p.append(text(cx, 372, "minden autó foglal egy negyedet, és a következőre vár", 11.5, cls="quiet", anchor="middle"))
    # resource-allocation graph
    gx = 420
    p.append(text(gx, 64, "Erőforrás-foglalási gráf", 13, 600))
    R = {"SE": (gx + 220, 290), "NE": (gx + 220, 110), "NW": (gx + 40, 110), "SW": (gx + 40, 290)}
    P = {"1": (gx + 220, 200), "2": (gx + 130, 110), "3": (gx + 40, 200), "4": (gx + 130, 290)}
    for k, (x, y) in R.items():
        p.append(rect(x - 30, y - 20, 60, 40, "acc", rx=3))
        p.append(text(x, y - 4, hu[k], 10.5, 600, anchor="middle"))
        p.append(f'<circle cx="{x}" cy="{y + 8}" r="4" class="ink"/>')
    for k, (x, y) in P.items():
        p.append(f'<circle cx="{x}" cy="{y}" r="20" class="c2f"/><circle cx="{x}" cy="{y}" r="20" fill="none" class="c2s" stroke-width="1.75"/>')
        p.append(text(x, y - 1, k + ".", 10.5, 600, anchor="middle"))
        p.append(text(x, y + 10, "autó", 9.5, 600, anchor="middle"))
    # holds: from the instance dot to the process; wants: from the process to the resource box
    p.append(path(f"M{gx + 224} 282V222", m, width=1.5))          # SE dot -> car 1
    p.append(path(f"M{gx + 220} 180V132", mb, cls="bads", width=1.5))  # car 1 -> NE
    p.append(path(f"M{gx + 214} 118H{gx + 152}", m, width=1.5))      # NE dot -> car 2
    p.append(path(f"M{gx + 110} 110H{gx + 72}", mb, cls="bads", width=1.5))  # car 2 -> NW
    p.append(path(f"M{gx + 36} 118V178", m, width=1.5))              # NW dot -> car 3
    p.append(path(f"M{gx + 40} 220V268", mb, cls="bads", width=1.5))  # car 3 -> SW
    p.append(path(f"M{gx + 46} 298H{gx + 108}", m, width=1.5))        # SW dot -> car 4
    p.append(path(f"M{gx + 150} 290H{gx + 188}", mb, cls="bads", width=1.5))  # car 4 -> SE
    # legend
    lx = gx + 290
    p.append(f'<circle cx="{lx + 14}" cy="104" r="12" class="c2f"/><circle cx="{lx + 14}" cy="104" r="12" fill="none" class="c2s" stroke-width="1.5"/>')
    p.append(text(lx + 34, 108, "folyamat", 11.5))
    p.append(rect(lx, 128, 30, 24, "acc", rx=3)); p.append(f'<circle cx="{lx + 9}" cy="140" r="3" class="ink"/><circle cx="{lx + 21}" cy="140" r="3" class="ink"/>')
    p.append(text(lx + 40, 138, "erőforrás; minden", 11.5)); p.append(text(lx + 40, 153, "példány egy pont", 11.5))
    p.append(path(f"M{lx} 184H{lx + 30}", mb, cls="bads", width=1.5)); p.append(text(lx + 40, 188, "kérés (vár rá)", 11.5))
    p.append(path(f"M{lx} 212H{lx + 30}", m, width=1.5)); p.append(text(lx + 40, 216, "hozzárendelés", 11.5)); p.append(text(lx + 40, 231, "(birtokolja)", 11.5))
    p.append(text(lx, 262, "Egy-egy példány:", 11.5, 600)); p.append(text(lx, 278, "kör = holtpont.", 11.5, cls="quiet"))
    p.append(text(lx, 302, "Több példány:", 11.5, 600)); p.append(text(lx, 318, "a kör szükséges,", 11.5, cls="quiet"))
    p.append(text(lx, 334, "de nem elégséges.", 11.5, cls="quiet"))
    p.append(text(gx, 344, "1 → ÉK → 2 → ÉNy → 3 → DNy → 4 → DK → 1", 11.5, 600, cls="bad"))
    return svg(880, 390, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("process-states", states), ("sync-layers", layers), ("store-buffer", reorder),
                     ("bridge-deadlock", bridge), ("gantt", gantt), ("linux-sched-classes", classes),
                     ("railway-semaphore", railway), ("unix-sleep-priorities", unix_prio), ("gridlock", gridlock)]:
        with open(f"{name}.svg", "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
