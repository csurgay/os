"""Generate the SVG figures for the Two-Level Memories and Caches lecture (Hungarian version).

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
Needs cachesim.py and depth-sample.csv in the same folder.
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


# ---------------- 1. The memory hierarchy ----------------
def hierarchy():
    m = "hi"
    title = "A memóriahierarchia: minden szint nagyobb, lassabb és bájtonként olcsóbb"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    rows = [("regiszterek", "< 1 ns", "kb. 1 KiB", "a CPU-magban", "acc"),
            ("gyorsítótár (L1, L2, L3)", "1,6 / 4,4 / ~25 ns", "32 KiB … több tíz MiB", "a CPU-lapkán (SRAM)", "acc"),
            ("központi memória (RAM)", "~100–180 ns", "GiB", "DRAM-modulok", "acc"),
            ("SSD / merevlemez", "~0,1 ms / ~5–10 ms", "TB", "tartós", "c2"),
            ("optikai lemez (CD, Blu-ray)", "~100 ms", "0,7–100 GB lemezenként", "cserélhető", "c2"),
            ("mágnesszalag", "másodpercek – percek", "korlátlan (több szalag)", "archívum", "c2")]
    p.append(text(240, 62, "elérési idő", 11.5, 600, cls="quiet")); p.append(text(420, 62, "kapacitás", 11.5, 600, cls="quiet"))
    p.append(text(600, 62, "hol", 11.5, 600, cls="quiet"))
    for i, (a, b, c, d, k) in enumerate(rows):
        y = 72 + i * 46
        p.append(rect(24, y, 740, 36, k, rx=6))
        p.append(text(36, y + 23, a, 12.5, 600)); p.append(text(240, y + 23, b, 12)); p.append(text(420, y + 23, c, 12))
        p.append(text(600, y + 23, d, 11.5, cls="quiet"))
    # Stallings csoportosítása: belső (0-2. sor), külső (3-4. sor), offline (5. sor)
    for r0, r1, name in ((0, 2, "belső"), (3, 4, "külső"), (5, 5, "offline")):
        ya, yb = 72 + r0 * 46 + 2, 72 + r1 * 46 + 34
        p.append(path(f"M774 {ya}H780V{yb}H774", width=1.5))
        p.append(text(788, (ya + yb) / 2 + 4, name, 12, 600))
        p.append(text(788, (ya + yb) / 2 + 19, "tár", 11, cls="quiet"))
    p.append(path("M890 340V84", m, width=2)); p.append(text(902, 210, "bájtonkénti ár", 11.5, cls="quiet"))
    p.append(text(902, 226, "és sebesség", 11.5, cls="quiet"))
    p.append(text(24, 368, "Kék: az előadás gyorsítótár–RAM párosa (felejtő, a hardver kezeli). Narancs: az alatta lévő tárak, ahol a RAM a lemez", 11.5, cls="quiet"))
    p.append(text(24, 386, "gyorsítótáraként működik (page cache, virtuális memória). A gyorsítótár-idők az előadás gépén mérve (latency.c).", 11.5, cls="quiet"))
    p.append(text(24, 404, "A belső tárat a CPU utasításai érik el, a külső tárat I/O-n keresztül; az offline tárnál előbb be kell helyezni az adathordozót.", 11.5, cls="quiet"))
    return svg(1000, 420, title, "\n".join(p))


# ---------------- 2. The triangle and the magic ----------------
def triangle():
    m = "tr"
    title = "Kapacitás, sebesség, olcsóság: kettőt választhatsz – vagy két memóriát kombinálsz"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    A, B, C = (190, 60), (60, 290), (320, 290)
    p.append(f'<path d="M{A[0]} {A[1]}L{B[0]} {B[1]}L{C[0]} {C[1]}Z" class="accf"/>')
    p.append(f'<path d="M{A[0]} {A[1]}L{B[0]} {B[1]}L{C[0]} {C[1]}Z" fill="none" class="acc" stroke-width="2"/>')
    p.append(label(190, 52, "kapacitás", 13, "ink", weight=600)); p.append(label(60, 312, "sebesség", 13, "ink", weight=600))
    p.append(label(320, 312, "olcsóság", 13, "ink", weight=600))
    p.append('<circle cx="190" cy="215" r="6" class="c2"/>')
    p.append(label(190, 240, "bármely memória:", 11)); p.append(label(190, 254, "egy kompromisszum", 11))
    x0 = 400
    p.append(text(x0, 84, "A kétszintű memória „varázsa”", 13.5, 600))
    for i, (a, b, c, k) in enumerate((("nagy", "kicsi", "nagy", None), ("lassú", "gyors", "gyors", "acc"), ("olcsó", "drága", "olcsó", None))):
        y = 128 + i * 36
        p.append(text(x0 + 50, y, a, 14, 600, anchor="middle")); p.append(text(x0 + 180, y, b, 14, 600, anchor="middle"))
        p.append(text(x0 + 330, y, c, 14, 600, cls="acct" if k else "ink", anchor="middle"))
    p.append(text(x0 + 110, 164, "+", 22, 600, anchor="middle")); p.append(text(x0 + 255, 164, "=", 22, 600, anchor="middle"))
    p.append(text(x0 + 50, 228, "RAM", 12, 600, cls="quiet", anchor="middle")); p.append(text(x0 + 180, 228, "gyorsítótár", 12, 600, cls="quiet", anchor="middle"))
    p.append(text(x0 + 330, 228, "amit a program lát", 12, 600, cls="quiet", anchor="middle"))
    p.append(text(x0, 270, "… ha az elérések többsége a kicsi, gyors memóriában talál:", 11.5, cls="quiet"))
    p.append(text(x0, 290, "T = H · T(gyorsítótár) + (1 − H) · T(RAM), ahol H ≈ 1.", 11.5, cls="quiet"))
    return svg(820, 330, title, "\n".join(p))


# ---------------- 3. Latency ladder (measured) ----------------
def ladder():
    title = "Egy memóriaelérés ideje a használt memória függvényében (mérés, latency.c)"
    data = [(4, 1.8), (8, 1.5), (16, 1.6), (32, 2.0), (64, 4.3), (128, 4.3), (256, 4.4), (512, 5.4), (1024, 10.3),
            (2048, 24.3), (4096, 24.7), (8192, 109.6), (16384, 139.2), (32768, 140.3), (65536, 141.0),
            (131072, 146.8), (262144, 161.0), (524288, 182.3)]
    x0, x1, y0, y1 = 90, 760, 330, 60
    lx = lambda kb: x0 + (x1 - x0) * (math.log2(kb) - 2) / (math.log2(524288) - 2)
    ly = lambda ns: y0 - (y0 - y1) * (math.log10(ns) - 0) / (math.log10(300) - 0)
    p = [text(24, 30, title, 15, 600)]
    for ns in (1, 2, 5, 10, 20, 50, 100, 200):
        p.append(f'<line x1="{x0}" y1="{ly(ns):.1f}" x2="{x1}" y2="{ly(ns):.1f}" class="grid"/>')
        p.append(text(x0 - 8, ly(ns) + 4, f"{ns} ns", 10.5, cls="quiet", anchor="end"))
    for kb, lab in ((4, "4 KiB"), (32, "32 KiB"), (1024, "1 MiB"), (32768, "32 MiB"), (524288, "512 MiB")):
        p.append(text(lx(kb), y0 + 18, lab, 10.5, cls="quiet", anchor="middle"))
    for lo, hi, lab, k in ((4, 32, "L1: 32 KiB", "acc"), (64, 1024, "L2: 1 MiB", "acc"), (2048, 4096, "L3 (közös)", "c2"), (8192, 524288, "RAM", "bad")):
        x = lx(lo) - 8; w = lx(hi) - lx(lo) + 16
        cls = {"acc": "accf", "c2": "c2f", "bad": "badf"}[k]
        p.append(f'<rect x="{x:.1f}" y="{y1 - 6}" width="{w:.1f}" height="{y0 - y1 + 6}" class="{cls}"/>')
        p.append(text(x + w / 2, y1 + 10, lab, 11.5, 600, anchor="middle"))
    pts = " ".join(f"{lx(kb):.1f},{ly(ns):.1f}" for kb, ns in data)
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    for kb, ns in data:
        p.append(f'<circle cx="{lx(kb):.1f}" cy="{ly(ns):.1f}" r="3.5" class="acct"/>')
    p.append(text(24, 372, "Véletlenszerű pointer chasing egy 2,8 GHz-es Xeonon (felhőbeli VM): kb. 1,6 ns (4–5 ciklus) az L1-ben, 4,4 ns az L2-ben,", 11.5, cls="quiet"))
    p.append(text(24, 390, "25 ns a más bérlőkkel közös L3-ban, 110–180 ns a RAM-ból. Logaritmikus skálák; minden lépcső egy hierarchiaszint.", 11.5, cls="quiet"))
    return svg(800, 406, title, "\n".join(p))


# ---------------- 4. Call depth over time (measured) ----------------
def calldepth():
    title = "Egy valódi program hívási mélysége: lassan, egyszerre egy szinttel változik"
    t = [int(v) for v in open(os.path.join(HERE, "depth-sample.csv")).read().split()]
    x0, x1, y0, y1 = 70, 780, 280, 60
    lo, hi = 0, 28
    X = lambda i: x0 + (x1 - x0) * i / (len(t) - 1)
    Y = lambda d: y0 - (y0 - y1) * (d - lo) / (hi - lo)
    p = [text(24, 30, title, 15, 600)]
    for d in range(0, 29, 4):
        p.append(f'<line x1="{x0}" y1="{Y(d):.1f}" x2="{x1}" y2="{Y(d):.1f}" class="grid"/>')
        p.append(text(x0 - 8, Y(d) + 4, str(d), 10.5, cls="quiet", anchor="end"))
    d = "M" + " L".join(f"{X(i):.1f} {Y(v):.1f}" for i, v in enumerate(t))
    p.append(f'<path d="{d}" fill="none" class="acc" stroke-width="1.2"/>')
    p.append(text(x0, y0 + 20, "2500 egymást követő hívás és visszatérés (calldepth.py: a json, az ast és a difflib munka közben)", 11, cls="quiet"))
    p.append(f'<g transform="translate(30 {(y0 + y1) / 2}) rotate(-90)">{text(0, 0, "hívási mélység", 12, 600, anchor="middle")}</g>')
    p.append(text(24, 326, "Ha 8 szintet gyors tárban tartunk, a teljes futás hívásainak és visszatéréseinek csak 2,5%-a esik ezen az ablakon kívül.", 11.5, cls="quiet"))
    return svg(800, 342, title, "\n".join(p))


# ---------------- 5. Direct-mapped cache ----------------
def dmcache():
    m = "dm"
    title = "Direkt leképezésű gyorsítótár: az index kiválaszt egy sort, a tag megmondja, kié"
    p = [f"<defs>{marker(m)}{marker('dmb', 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # address
    p.append(text(60, 62, "32 bites cím", 12, 600, cls="quiet"))
    fields = [("tag", 8, "c2"), ("index", 10, "acc"), ("eltolás", 14, "plain")]
    x = 60
    for name, bits, k in fields:
        w = bits * 16
        p.append(rect(x, 70, w, 32, k if k != "plain" else "tint", rx=3))
        p.append(text(x + w / 2, 91, f"{name} ({bits} bit)", 12, 600, anchor="middle"))
        x += w
    # table
    tx, ty = 60, 160
    p.append(text(tx, ty - 10, "1024 sor", 11.5, cls="quiet"))
    cols = [("V", 28), ("D", 28), ("tag", 70), ("sor: 4096 darab 32 bites szó (16 KiB)", 400)]
    cx = tx
    for name, w in cols:
        p.append(rect(cx, ty, w, 28, "tint", rx=0)); p.append(text(cx + w / 2, ty + 19, name, 11.5, 600, anchor="middle"))
        cx += w
    rows = [("0", "", "", ""), ("209", "1", "0", "0x12"), ("⋮", "", "", ""), ("1023", "", "", "")]
    for i, (n, v, dd, tg) in enumerate(rows):
        y = ty + 28 + i * 30
        cx = tx
        for j, (name, w) in enumerate(cols):
            kind = "acc" if i == 1 else "plain"
            p.append(rect(cx, y, w, 30, kind, rx=0))
            cx += w
        p.append(text(tx - 8, y + 20, n, 11, cls="quiet", anchor="end"))
        if v:
            p.append(text(tx + 14, y + 20, v, 12, 600, anchor="middle")); p.append(text(tx + 42, y + 20, dd, 12, 600, anchor="middle"))
            p.append(text(tx + 91, y + 20, tg, 12, 600, anchor="middle"))
            p.append(f'<rect x="{tx + 126 + 230}" y="{y + 4}" width="40" height="22" class="c2f"/>')
            p.append(text(tx + 126 + 250, y + 20, "szó", 10.5, anchor="middle"))
    # arrows
    p.append(path("M300 102C300 130 40 150 36 200C34 222 44 232 56 233", m, width=1.5)); p.append(text(312, 124, "az index kiválasztja a sort", 11, cls="quiet"))
    p.append(path("M124 102C124 180 151 190 151 226", m, width=1.5))
    p.append(text(118, 128, "összehasonlítás", 11, cls="quiet", anchor="end"))
    p.append(path("M500 102C520 160 420 190 410 226", m, width=1.5)); p.append(text(510, 150, "az eltolás kiválasztja a szót", 11, cls="quiet"))
    # outcome boxes
    p.append(rect(620, 160, 230, 64, "acc", rx=8)); p.append(text(632, 182, "TALÁLAT: V = 1, a tag egyezik", 12, 600))
    p.append(text(632, 202, "a szó a gyorsítótárból jön", 11, cls="quiet"))
    p.append(rect(620, 236, 230, 92, "c2", rx=8)); p.append(text(632, 258, "HIÁNY: az egész sor betöltése", 12, 600))
    p.append(text(632, 278, "a RAM-ból; ha D = 1, előbb a régi", 11, cls="quiet")); p.append(text(632, 294, "sort visszaírjuk (write-back),", 11, cls="quiet"))
    p.append(text(632, 312, "majd V = 1, D = 0, új tag", 11, cls="quiet"))
    p.append(text(24, 360, "Tanpélda: 4 GiB RAM (32 bites címek) és 16 MiB-os gyorsítótár 1024 darab 16 KiB-os sorral. A valódi gyorsítótárak 64 bájtos", 11.5, cls="quiet"))
    p.append(text(24, 378, "és sokkal több sort használnak; a mechanizmus ugyanaz. V (valid): a sor valódi adatot tart; D (dirty): írtak bele, eltér a RAM-tól.", 11.5, cls="quiet"))
    return svg(880, 394, title, "\n".join(p))


# ---------------- 6. Fully associative cache ----------------
def facache():
    m = "fa"
    title = "Teljesen asszociatív gyorsítótár: minden taget egyszerre hasonlítunk össze"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(rect(60, 56, 200, 32, "c2", rx=3)); p.append(text(160, 77, "tag (blokkszám)", 12, 600, anchor="middle"))
    p.append(rect(260, 56, 120, 32, "tint", rx=3)); p.append(text(320, 77, "eltolás", 12, 600, anchor="middle"))
    tags = ["0x3a1", "0x0f2", "0x7c0", "0x12d", "0x544", "0x2b8"]
    for i, tg in enumerate(tags):
        y = 120 + i * 34
        hit = i == 3
        p.append(rect(60, y, 120, 28, "acc" if hit else "tint", rx=3)); p.append(text(120, y + 19, tg, 12, 600, anchor="middle"))
        p.append(f'<circle cx="214" cy="{y + 14}" r="12" class="{"c2f" if hit else "tint"}"/><circle cx="214" cy="{y + 14}" r="12" fill="none" class="edge" stroke-width="1.25"/>')
        p.append(text(214, y + 18, "=", 13, 600, anchor="middle"))
        p.append(text(244, y + 19, "1" if hit else "0", 12, 600, cls="ink" if hit else "quiet"))
        p.append(rect(270, y, 300, 28, "acc" if hit else "tint", rx=3)); p.append(text(420, y + 19, "a sor adatai", 11, cls="quiet", anchor="middle"))
        p.append(path(f"M160 88C170 100 200 {y - 6} 210 {y + 2}", None, width=1, dash="3 3"))
    p.append(path("M572 236H640", m, width=1.6)); p.append(rect(640, 218, 180, 36, "acc", rx=6)); p.append(text(730, 241, "TALÁLAT: a szót", 12, 600, anchor="middle"))
    p.append(text(730, 276, "az eltolás választja ki", 11, cls="quiet", anchor="middle"))
    p.append(text(24, 352, "Tartalom szerint címezhető: a tárolt tag alapján keresünk benne, soronként egy, párhuzamosan működő komparátorral.", 11.5, cls="quiet"))
    p.append(text(24, 370, "Bármely blokk bármelyik sorba kerülhet, így nincs ütközés, de a komparátorok drágák: csak kis gyorsítótárak (pl. sok TLB) épülnek így.", 11.5, cls="quiet"))
    p.append(text(24, 388, "Ha a gyorsítótár megtelt, egy csereálgoritmus választ áldozatot: ideális esetben azt a sort, amelyet a legrégebben nem használtak.", 11.5, cls="quiet"))
    return svg(860, 404, title, "\n".join(p))


# ---------------- 7. Where can a block go? ----------------
def placement():
    title = "Hová kerülhet a memória 12-es blokkja egy 8 soros gyorsítótárban?"
    p = [text(24, 30, title, 15, 600)]
    cases = [("direkt leképezésű", "csak a 12 mod 8 = 4. sor", [4], 1),
             ("2 utas csoportasszociatív", "a 12 mod 4 = 0. csoport bármelyik sora", [0, 1], 2),
             ("teljesen asszociatív", "bármelyik sor", list(range(8)), 8)]
    for c, (name, note, allowed, ways) in enumerate(cases):
        x = 24 + c * 280
        p.append(text(x, 66, name, 13, 600)); p.append(text(x, 84, note, 11, cls="quiet"))
        for i in range(8):
            cx = x + i * 30
            p.append(rect(cx, 98, 26, 40, "c2" if i in allowed else "tint", rx=3))
            p.append(text(cx + 13, 154, str(i), 10.5, cls="quiet", anchor="middle"))
        if ways == 2:
            for s in range(4):
                p.append(f'<rect x="{x + s * 60 - 2}" y="94" width="58" height="48" rx="5" fill="none" class="acc" stroke-width="1.5" stroke-dasharray="4 3"/>')
                p.append(text(x + s * 60 + 27, 172, f"{s}. csoport", 10.5, cls="acct", anchor="middle"))
    p.append(text(24, 206, "Több szabadság (asszociativitás) kevesebb ütközési hiányt, de elérésenként több tag-összehasonlítást jelent. A valódi L1 jellemzően", 11.5, cls="quiet"))
    p.append(text(24, 224, "4–12 utas, az L2 és az L3 8–16 utas: ezen a gépen az L1 8, az L2 16, az L3 11 utas, mindegyik 64 bájtos sorokkal.", 11.5, cls="quiet"))
    return svg(860, 240, title, "\n".join(p))


# ---------------- 8. Miss rate against line size (simulated) ----------------
def blocksize():
    spec = importlib.util.spec_from_file_location("cachesim", os.path.join(HERE, "cachesim.py"))
    cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
    t = cs.mixed_trace()
    lines = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    rates = [100 * cs.Cache(4096, L, 4 if 4096 // L >= 4 else 0).run(t) for L in lines]
    title = "Hiányarány a sorméret függvényében, 4 KiB-os gyorsítótár (szimuláció, cachesim.py)"
    x0, x1, y0, y1 = 80, 760, 300, 60
    X = lambda i: x0 + (x1 - x0) * i / (len(lines) - 1)
    Y = lambda r: y0 - (y0 - y1) * r / 100
    p = [text(24, 30, title, 15, 600)]
    for r in (0, 20, 40, 60, 80, 100):
        p.append(f'<line x1="{x0}" y1="{Y(r):.1f}" x2="{x1}" y2="{Y(r):.1f}" class="grid"/>')
        p.append(text(x0 - 8, Y(r) + 4, f"{r}%", 10.5, cls="quiet", anchor="end"))
    for i, L in enumerate(lines):
        p.append(text(X(i), y0 + 18, f"{L}", 10.5, cls="quiet", anchor="middle"))
    p.append(text((x0 + x1) / 2, y0 + 38, "sorméret (blokkméret) bájtban; ahogy a sorok nőnek, a számuk csökken", 11.5, cls="quiet", anchor="middle"))
    pts = " ".join(f"{X(i):.1f},{Y(r):.1f}" for i, r in enumerate(rates))
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    for i, r in enumerate(rates):
        p.append(f'<circle cx="{X(i):.1f}" cy="{Y(r):.1f}" r="4" class="{"c2" if lines[i] == 64 else "acct"}"/>')
        p.append(text(X(i), Y(r) - 10, f"{r:.1f}".replace(".", ","), 10.5, cls="quiet", anchor="middle"))
    k = lines.index(64)
    p.append(text(X(k), Y(rates[k]) + 24, "optimum", 12, 600, anchor="middle"))
    p.append(text(24, 368, "A kis sorok elpazarolják a térbeli lokalitást (egy hiány keveset hoz); a túl nagyok miatt kevés a sor, így az újra meg újra", 11.5, cls="quiet"))
    p.append(text(24, 386, "használt adatot kiszorítja, amit csak a szomszédság miatt hoztunk be. 4 utas (2 és 1 sornál teljesen asszociatív); 32 forró változó + bejárások.", 11.5, cls="quiet"))
    return svg(800, 402, title, "\n".join(p))


# ---------------- 9. Row versus column traversal ----------------
def traversal():
    m = "tv"
    title = "Ugyanaz az összeg, két ciklussorrend: a memóriát 64 bájtos sorokban olvassuk"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    for c, (name, ok) in enumerate((("soronként: for i … for j … a[i][j]", True), ("oszloponként: for j … for i … a[i][j]", False))):
        x = 24 + c * 410
        p.append(text(x, 62, name, 12.5, 600))
        for i in range(4):
            for j in range(8):
                p.append(rect(x + j * 34, 76 + i * 30, 32, 26, "tint", rx=2))
        if ok:
            for i in range(4):
                p.append(path(f"M{x + 6} {89 + i * 30}H{x + 266}", m, cls="acc", width=2))
        else:
            for j in range(8):
                p.append(path(f"M{x + 16 + j * 34} 80V{190}", m, cls="bads", width=2))
        p.append(text(x, 222, "16 szomszédos int egy soron osztozik: 1 hiány, 15 találat" if ok else "minden lépés N × 4 bájtot ugrik: mindig új sor", 11.5, cls="quiet"))
    rows = [("1024 × 1024 (4 MiB)", 0.6, 3.7, 5.7), ("2048 × 2048 (16 MiB)", 2.8, 19.0, 6.8), ("4096 × 4096 (64 MiB)", 10.3, 160.9, 15.6), ("8192 × 8192 (256 MiB)", 39.7, 760.9, 19.2)]
    p.append(text(24, 260, "Mérés (traverse.c, gcc -O2):", 12.5, 600))
    for i, (n, a, b, ratio) in enumerate(rows):
        y = 284 + i * 22
        p.append(text(24, y, n, 11.5)); p.append(text(240, y, f"sorok {a:.1f} ms".replace(".", ","), 11.5, cls="acct")); p.append(text(380, y, f"oszlopok {b:.1f} ms".replace(".", ","), 11.5, cls="bad"))
        p.append(text(540, y, f"× {ratio:.1f}".replace(".", ","), 11.5, 600))
    return svg(840, 380, title, "\n".join(p))


# ---------------- 10. SRAM- és DRAM-cella ----------------
def cells():
    title = "Miért drága a gyors memória: egy SRAM-cellában hat tranzisztor van, egy DRAM-cellában egy tranzisztor és egy kondenzátor"
    p = [text(24, 30, "Miért drága a gyors memória: egy SRAM-bit és egy DRAM-bit", 15, 600)]

    def tr(x, y, name):                      # tranzisztor kis kapcsolódobozként, a vezérlőelektróda felül
        return rect(x, y, 44, 26, "c2", rx=3) + text(x + 22, y + 17, name, 11, 600, anchor="middle")

    def inv(x, y, right=True):              # inverter: háromszög, a kimenetén kis körrel
        d = 1 if right else -1
        tri = f"M{x} {y - 14}L{x + d * 34} {y}L{x} {y + 14}Z"
        return (f'<path d="{tri}" class="accf"/><path d="{tri}" fill="none" class="acc" stroke-width="1.5"/>'
                f'<circle cx="{x + d * 38}" cy="{y}" r="4" fill="none" class="acc" stroke-width="1.5"/>')

    # ---- SRAM, bal oldali panel ----
    p.append(text(24, 64, "SRAM-cella (gyorsítótárak): 6 tranzisztor", 13, 600))
    p.append(path("M40 92H400", width=2)); p.append(text(404, 96, "szóvezeték", 11, cls="quiet"))
    p.append(path("M60 80V290", width=2)); p.append(text(60, 308, "bitvezeték", 11, cls="quiet", anchor="middle"))
    p.append(path("M380 80V290", width=2)); p.append(text(380, 308, "negált bitvezeték", 11, cls="quiet", anchor="middle"))
    p.append(tr(98, 170, "T5")); p.append(tr(298, 170, "T6"))
    p.append(path("M120 92V170")); p.append(path("M320 92V170"))
    p.append(path("M60 183H98")); p.append(path("M342 183H380"))
    # a Q csomópont (x=170) a felső invertert, a nem-Q (x=270) az alsót táplálja; a kimenetek keresztbe kötve
    p.append(path("M142 183H170V150H186")); p.append(path("M224 150H270V183"))
    p.append(path("M298 183H270V216H254")); p.append(path("M216 216H170V183"))
    p.append(inv(186, 150, True)); p.append(inv(254, 216, False))
    p.append('<circle cx="170" cy="183" r="3" class="edgef"/><circle cx="270" cy="183" r="3" class="edgef"/>')
    p.append(text(164, 200, "Q", 11, 600, anchor="end")); p.append(text(276, 212, "nem Q", 11, 600))
    p.append(text(220, 252, "két inverter (egyenként 2 tranzisztor) táplálja egymást:", 11, cls="quiet", anchor="middle"))
    p.append(text(220, 266, "a bit addig marad meg, amíg van tápfeszültség", 11, cls="quiet", anchor="middle"))
    # ---- DRAM, jobb oldali panel ----
    x0 = 500
    p.append(text(x0, 64, "DRAM-cella (központi memória): 1 tranzisztor + 1 kondenzátor", 13, 600))
    p.append(path(f"M{x0 + 10} 92H{x0 + 300}", width=2)); p.append(text(x0 + 304, 96, "szóvezeték", 11, cls="quiet"))
    p.append(path(f"M{x0 + 40} 80V290", width=2)); p.append(text(x0 + 40, 308, "bitvezeték", 11, cls="quiet", anchor="middle"))
    p.append(tr(x0 + 120, 170, "T"))
    p.append(path(f"M{x0 + 142} 92V170")); p.append(path(f"M{x0 + 40} 183H{x0 + 120}"))
    p.append(path(f"M{x0 + 164} 183H{x0 + 220}V206"))
    p.append(f'<path d="M{x0 + 196} 206H{x0 + 244}M{x0 + 196} 216H{x0 + 244}" fill="none" class="acc" stroke-width="3"/>')
    p.append(path(f"M{x0 + 220} 216V236")); p.append(path(f"M{x0 + 204} 236H{x0 + 236}M{x0 + 210} 242H{x0 + 230}M{x0 + 216} 248H{x0 + 224}", width=1.5))
    p.append(text(x0 + 254, 208, "kondenzátor: a bit", 11, cls="quiet")); p.append(text(x0 + 254, 222, "egy parányi töltés", 11, cls="quiet"))
    p.append(text(x0 + 205, 272, "a töltés elszivárog: minden sort frissíteni kell", 11, cls="quiet", anchor="middle"))
    p.append(text(x0 + 205, 286, "(DDR-memóriában 32–64 ms-on belül), és az olvasás kiüríti", 11, cls="quiet", anchor="middle"))
    # ---- összehasonlítás ----
    rows = [("SRAM", "kb. 6 tranzisztor bitenként, nincs frissítés, ~1 ns a CPU-lapkán: gyors, nagy terület, drága → gyorsítótárak", "acct"),
            ("DRAM", "1 tranzisztor + 1 kondenzátor bitenként, frissíteni kell, ~100 ns a memóriavezérlőn át: sűrű, olcsó → RAM", "c2"),
            ("CAM", "SRAM-cella plusz összehasonlító logika, kb. 9–10 tranzisztor bitenként → csak kis teljesen asszociatív gyorsítótárak, TLB-k", "bad")]
    for i, (a, b, c) in enumerate(rows):
        y = 342 + i * 22
        p.append(text(24, y, a, 12, 600, cls=c)); p.append(text(76, y, b, 11.5, cls="quiet"))
    return svg(900, 410, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("memory-hierarchy", hierarchy), ("two-level-magic", triangle), ("latency-ladder", ladder),
                     ("call-depth", calldepth), ("direct-mapped-cache", dmcache), ("fully-associative-cache", facache),
                     ("block-placement", placement), ("miss-rate-vs-line-size", blocksize), ("traversal", traversal),
                     ("memory-cells", cells)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
