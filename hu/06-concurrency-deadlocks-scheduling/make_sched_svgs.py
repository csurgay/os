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
    p.append(text(24, 584, "a felfüggesztett állapotok szerepét pedig a leállított folyamatok (T) és a lapozóterületre kivitt memória tölti be.", 11.5, cls="quiet"))
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
        p.append(text(x + 261, 102, "tárolópuffer", 11.5, 600, anchor="middle"))
        p.append(text(x + 261, 120, f"flag[{i}] = 1", 11, anchor="middle")); p.append(text(x + 261, 136, f"turn = {1 - i}", 11, anchor="middle"))
        p.append(path(f"M{x + 261} 146V246", m, width=1.4, dash="5 4"))
        p.append(text(x + 268, 226, "később íródik ki", 11, cls="quiet"))
    p.append(rect(40, 250, 770, 40, "acc", rx=8))
    p.append(text(425, 275, "közös memória:  flag[0] = 0,  flag[1] = 0  (még mindig)", 12.5, 600, anchor="middle"))
    p.append(text(24, 318, "Az írások a tárolópufferben várnak, az olvasások egyenesen a memóriához mennek: mindkét mag 0-nak látja a másik jelzőjét.", 11.5, cls="quiet"))
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


if __name__ == "__main__":
    for name, fn in [("process-states", states), ("sync-layers", layers), ("store-buffer", reorder),
                     ("bridge-deadlock", bridge), ("gantt", gantt), ("linux-sched-classes", classes)]:
        with open(f"{name}.svg", "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
