"""Generate the SVG figures for the Two-Level Memories and Caches lecture.

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
    title = "The memory hierarchy: each level is bigger, slower and cheaper per byte"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    rows = [("registers", "< 1 ns", "about 1 KiB", "inside the CPU core", "acc"),
            ("cache (L1, L2, L3)", "1.6 / 4.4 / ~25 ns", "32 KiB … tens of MiB", "on the CPU chip (SRAM)", "acc"),
            ("main memory (RAM)", "~100–180 ns", "GiB", "DRAM modules", "acc"),
            ("SSD / hard disk", "~0.1 ms / ~5–10 ms", "TB", "persistent", "c2"),
            ("optical disc (CD, Blu-ray)", "~100 ms", "0.7–100 GB per disc", "removable", "c2"),
            ("magnetic tape", "seconds – minutes", "unlimited (more tapes)", "archive", "c2")]
    p.append(text(240, 62, "access time", 11.5, 600, cls="quiet")); p.append(text(420, 62, "capacity", 11.5, 600, cls="quiet"))
    p.append(text(600, 62, "where", 11.5, 600, cls="quiet"))
    for i, (a, b, c, d, k) in enumerate(rows):
        y = 72 + i * 46
        p.append(rect(24, y, 740, 36, k, rx=6))
        p.append(text(36, y + 23, a, 12.5, 600)); p.append(text(240, y + 23, b, 12)); p.append(text(420, y + 23, c, 12))
        p.append(text(600, y + 23, d, 11.5, cls="quiet"))
    p.append(path("M790 340V84", m, width=2)); p.append(text(804, 210, "price per byte", 11.5, cls="quiet"))
    p.append(text(804, 226, "and speed", 11.5, cls="quiet"))
    p.append(text(24, 368, "Blue: the cache–RAM pair of this lecture (volatile, managed by hardware). Orange: storage below, where RAM acts as the", 11.5, cls="quiet"))
    p.append(text(24, 386, "cache of the disk (page cache, virtual memory). Cache times: measured on this lecture's machine (latency.c).", 11.5, cls="quiet"))
    return svg(900, 402, title, "\n".join(p))


# ---------------- 2. The triangle and the magic ----------------
def triangle():
    m = "tr"
    title = "Capacity, speed, cheapness: pick two — or combine two memories"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    A, B, C = (190, 60), (60, 290), (320, 290)
    p.append(f'<path d="M{A[0]} {A[1]}L{B[0]} {B[1]}L{C[0]} {C[1]}Z" class="accf"/>')
    p.append(f'<path d="M{A[0]} {A[1]}L{B[0]} {B[1]}L{C[0]} {C[1]}Z" fill="none" class="acc" stroke-width="2"/>')
    p.append(label(190, 52, "capacity", 13, "ink", weight=600)); p.append(label(60, 312, "speed", 13, "ink", weight=600))
    p.append(label(320, 312, "cheapness", 13, "ink", weight=600))
    p.append('<circle cx="190" cy="215" r="6" class="c2"/>')
    p.append(label(190, 240, "any one memory:", 11)); p.append(label(190, 254, "a compromise", 11))
    x0 = 400
    p.append(text(x0, 84, "The “magic” of a two-level memory", 13.5, 600))
    for i, (a, b, c, k) in enumerate((("big", "small", "big", None), ("slow", "fast", "fast", "acc"), ("cheap", "expensive", "cheap", None))):
        y = 128 + i * 36
        p.append(text(x0 + 50, y, a, 14, 600, anchor="middle")); p.append(text(x0 + 180, y, b, 14, 600, anchor="middle"))
        p.append(text(x0 + 330, y, c, 14, 600, cls="acct" if k else "ink", anchor="middle"))
    p.append(text(x0 + 110, 164, "+", 22, 600, anchor="middle")); p.append(text(x0 + 255, 164, "=", 22, 600, anchor="middle"))
    p.append(text(x0 + 50, 228, "RAM", 12, 600, cls="quiet", anchor="middle")); p.append(text(x0 + 180, 228, "cache", 12, 600, cls="quiet", anchor="middle"))
    p.append(text(x0 + 330, 228, "what the program sees", 12, 600, cls="quiet", anchor="middle"))
    p.append(text(x0, 270, "… as long as most accesses hit the small, fast memory:", 11.5, cls="quiet"))
    p.append(text(x0, 290, "T = H · T(cache) + (1 − H) · T(RAM), with hit rate H close to 1.", 11.5, cls="quiet"))
    return svg(820, 330, title, "\n".join(p))


# ---------------- 3. Latency ladder (measured) ----------------
def ladder():
    title = "Time per memory access against the amount of memory used (measured, latency.c)"
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
    for lo, hi, lab, k in ((4, 32, "L1: 32 KiB", "acc"), (64, 1024, "L2: 1 MiB", "acc"), (2048, 4096, "L3 (shared)", "c2"), (8192, 524288, "RAM", "bad")):
        x = lx(lo) - 8; w = lx(hi) - lx(lo) + 16
        cls = {"acc": "accf", "c2": "c2f", "bad": "badf"}[k]
        p.append(f'<rect x="{x:.1f}" y="{y1 - 6}" width="{w:.1f}" height="{y0 - y1 + 6}" class="{cls}"/>')
        p.append(text(x + w / 2, y1 + 10, lab, 11.5, 600, anchor="middle"))
    pts = " ".join(f"{lx(kb):.1f},{ly(ns):.1f}" for kb, ns in data)
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    for kb, ns in data:
        p.append(f'<circle cx="{lx(kb):.1f}" cy="{ly(ns):.1f}" r="3.5" class="acct"/>')
    p.append(text(24, 372, "Random pointer chasing on a 2.8 GHz Xeon (cloud VM): about 1.6 ns (4–5 cycles) in L1, 4.4 ns in L2, 25 ns in the L3 that this", 11.5, cls="quiet"))
    p.append(text(24, 390, "virtual machine shares with others, and 110–180 ns from RAM. Logarithmic scales; each step is a level of the hierarchy.", 11.5, cls="quiet"))
    return svg(800, 406, title, "\n".join(p))


# ---------------- 4. Call depth over time (measured) ----------------
def calldepth():
    title = "Call depth while a real program runs: it changes slowly, one level at a time"
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
    p.append(text(x0, y0 + 20, "2,500 consecutive calls and returns (calldepth.py: json, ast and difflib at work)", 11, cls="quiet"))
    p.append(f'<g transform="translate(30 {(y0 + y1) / 2}) rotate(-90)">{text(0, 0, "call depth", 12, 600, anchor="middle")}</g>')
    p.append(text(24, 326, "With a window of 8 levels kept in fast storage, only 2.5% of the calls and returns of the whole run fall outside it.", 11.5, cls="quiet"))
    return svg(800, 342, title, "\n".join(p))


# ---------------- 5. Direct-mapped cache ----------------
def dmcache():
    m = "dm"
    title = "A direct-mapped cache: the index picks one line, the tag says whose it is"
    p = [f"<defs>{marker(m)}{marker('dmb', 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # address
    p.append(text(60, 62, "32-bit address", 12, 600, cls="quiet"))
    fields = [("tag", 8, "c2"), ("index", 10, "acc"), ("offset", 14, "plain")]
    x = 60
    for name, bits, k in fields:
        w = bits * 16
        p.append(rect(x, 70, w, 32, k if k != "plain" else "tint", rx=3))
        p.append(text(x + w / 2, 91, f"{name} ({bits} bits)", 12, 600, anchor="middle"))
        x += w
    # table
    tx, ty = 60, 160
    p.append(text(tx, ty - 10, "1024 lines", 11.5, cls="quiet"))
    cols = [("V", 28), ("D", 28), ("tag", 70), ("line: 4096 words of 32 bits (16 KiB)", 400)]
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
            p.append(text(tx + 126 + 250, y + 20, "word", 10.5, anchor="middle"))
    # arrows
    p.append(path("M300 102C300 130 40 150 36 200C34 222 44 232 56 233", m, width=1.5)); p.append(text(170, 140, "index selects the line", 11, cls="quiet"))
    p.append(path("M124 102C124 180 151 190 151 226", m, width=1.5))
    p.append(text(118, 128, "compare", 11, cls="quiet", anchor="end"))
    p.append(path("M500 102C520 160 420 190 410 226", m, width=1.5)); p.append(text(510, 150, "offset selects the word", 11, cls="quiet"))
    # outcome boxes
    p.append(rect(620, 160, 230, 64, "acc", rx=8)); p.append(text(632, 182, "HIT: V = 1 and stored tag = tag", 12, 600))
    p.append(text(632, 202, "the word comes from the cache", 11, cls="quiet"))
    p.append(rect(620, 236, 230, 92, "c2", rx=8)); p.append(text(632, 258, "MISS: load the whole line", 12, 600))
    p.append(text(632, 278, "from RAM; if D = 1, first write", 11, cls="quiet")); p.append(text(632, 294, "the old line back (write-back)", 11, cls="quiet"))
    p.append(text(632, 312, "then set V = 1, D = 0, new tag", 11, cls="quiet"))
    p.append(text(24, 360, "The lecture notes' toy example: 4 GiB of RAM (32-bit addresses) and a 16 MiB cache of 1024 lines of 16 KiB. Real caches use 64-byte lines", 11.5, cls="quiet"))
    p.append(text(24, 378, "and far more lines; the mechanism is the same. V (valid): the line holds real data; D (dirty): it was written and differs from RAM.", 11.5, cls="quiet"))
    return svg(880, 394, title, "\n".join(p))


# ---------------- 6. Fully associative cache ----------------
def facache():
    m = "fa"
    title = "A fully associative cache: every tag is compared at the same time"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(rect(60, 56, 200, 32, "c2", rx=3)); p.append(text(160, 77, "tag (block number)", 12, 600, anchor="middle"))
    p.append(rect(260, 56, 120, 32, "tint", rx=3)); p.append(text(320, 77, "offset", 12, 600, anchor="middle"))
    tags = ["0x3a1", "0x0f2", "0x7c0", "0x12d", "0x544", "0x2b8"]
    for i, tg in enumerate(tags):
        y = 120 + i * 34
        hit = i == 3
        p.append(rect(60, y, 120, 28, "acc" if hit else "tint", rx=3)); p.append(text(120, y + 19, tg, 12, 600, anchor="middle"))
        p.append(f'<circle cx="214" cy="{y + 14}" r="12" class="{"c2f" if hit else "tint"}"/><circle cx="214" cy="{y + 14}" r="12" fill="none" class="edge" stroke-width="1.25"/>')
        p.append(text(214, y + 18, "=", 13, 600, anchor="middle"))
        p.append(text(244, y + 19, "1" if hit else "0", 12, 600, cls="ink" if hit else "quiet"))
        p.append(rect(270, y, 300, 28, "acc" if hit else "tint", rx=3)); p.append(text(420, y + 19, "line data", 11, cls="quiet", anchor="middle"))
        p.append(path(f"M160 88C170 100 200 {y - 6} 210 {y + 2}", None, width=1, dash="3 3"))
    p.append(path("M572 236H640", m, width=1.6)); p.append(rect(640, 218, 180, 36, "acc", rx=6)); p.append(text(730, 241, "HIT: word selected", 12, 600, anchor="middle"))
    p.append(text(730, 276, "by the offset", 11, cls="quiet", anchor="middle"))
    p.append(text(24, 352, "Content-addressable: the cache is searched by what it holds (the tag), with one comparator per line, all working in parallel.", 11.5, cls="quiet"))
    p.append(text(24, 370, "Any block can go into any line, so there are no conflicts, but the comparators are costly: only small caches (such as many TLBs) are built this way.", 11.5, cls="quiet"))
    p.append(text(24, 388, "When the cache is full, a replacement algorithm must choose a victim: ideally the line that nobody has used for the longest time.", 11.5, cls="quiet"))
    return svg(860, 404, title, "\n".join(p))


# ---------------- 7. Where can a block go? ----------------
def placement():
    title = "Where can memory block 12 go in an 8-line cache?"
    p = [text(24, 30, title, 15, 600)]
    cases = [("direct-mapped", "line 12 mod 8 = 4 only", [4], 1),
             ("2-way set-associative", "set 12 mod 4 = 0: either line of it", [0, 1], 2),
             ("fully associative", "any line", list(range(8)), 8)]
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
                p.append(text(x + s * 60 + 27, 172, f"set {s}", 10.5, cls="acct", anchor="middle"))
    p.append(text(24, 206, "More freedom (associativity) means fewer conflict misses but more tags to compare per access. Real L1 caches are typically 4- to 12-way,", 11.5, cls="quiet"))
    p.append(text(24, 224, "L2 and L3 caches 8- to 16-way: on this machine L1 is 8-way, L2 16-way and L3 11-way, all with 64-byte lines.", 11.5, cls="quiet"))
    return svg(860, 240, title, "\n".join(p))


# ---------------- 8. Miss rate against line size (simulated) ----------------
def blocksize():
    spec = importlib.util.spec_from_file_location("cachesim", os.path.join(HERE, "cachesim.py"))
    cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
    t = cs.mixed_trace()
    lines = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    rates = [100 * cs.Cache(4096, L, 4 if 4096 // L >= 4 else 0).run(t) for L in lines]
    title = "Miss rate against line size, for a fixed 4 KiB cache (simulated, cachesim.py)"
    x0, x1, y0, y1 = 80, 760, 300, 60
    X = lambda i: x0 + (x1 - x0) * i / (len(lines) - 1)
    Y = lambda r: y0 - (y0 - y1) * r / 100
    p = [text(24, 30, title, 15, 600)]
    for r in (0, 20, 40, 60, 80, 100):
        p.append(f'<line x1="{x0}" y1="{Y(r):.1f}" x2="{x1}" y2="{Y(r):.1f}" class="grid"/>')
        p.append(text(x0 - 8, Y(r) + 4, f"{r}%", 10.5, cls="quiet", anchor="end"))
    for i, L in enumerate(lines):
        p.append(text(X(i), y0 + 18, f"{L}", 10.5, cls="quiet", anchor="middle"))
    p.append(text((x0 + x1) / 2, y0 + 38, "line (block) size in bytes; the number of lines falls as the lines grow", 11.5, cls="quiet", anchor="middle"))
    pts = " ".join(f"{X(i):.1f},{Y(r):.1f}" for i, r in enumerate(rates))
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    for i, r in enumerate(rates):
        p.append(f'<circle cx="{X(i):.1f}" cy="{Y(r):.1f}" r="4" class="{"c2" if lines[i] == 64 else "acct"}"/>')
        p.append(text(X(i), Y(r) - 10, f"{r:.1f}", 10.5, cls="quiet", anchor="middle"))
    k = lines.index(64)
    p.append(text(X(k), Y(rates[k]) + 24, "sweet spot", 12, 600, anchor="middle"))
    p.append(text(24, 368, "Small lines waste spatial locality (each miss brings in little); huge lines leave too few lines, so data used again and again", 11.5, cls="quiet"))
    p.append(text(24, 386, "is thrown out by data brought in only because it was next door. 4-way (2 and 1 lines: fully associative); 32 hot variables plus scans.", 11.5, cls="quiet"))
    return svg(800, 402, title, "\n".join(p))


# ---------------- 9. Row versus column traversal ----------------
def traversal():
    m = "tv"
    title = "Same sum, two loop orders: memory is read in 64-byte lines"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    for c, (name, ok) in enumerate((("row by row: for i … for j … a[i][j]", True), ("column by column: for j … for i … a[i][j]", False))):
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
        p.append(text(x, 222, "16 neighbouring ints share one line: 1 miss, 15 hits" if ok else "every step jumps N × 4 bytes: a new line each time", 11.5, cls="quiet"))
    rows = [("1024 × 1024 (4 MiB)", 0.6, 3.7, 5.7), ("2048 × 2048 (16 MiB)", 2.8, 19.0, 6.8), ("4096 × 4096 (64 MiB)", 10.3, 160.9, 15.6), ("8192 × 8192 (256 MiB)", 39.7, 760.9, 19.2)]
    p.append(text(24, 260, "Measured (traverse.c, gcc -O2):", 12.5, 600))
    for i, (n, a, b, ratio) in enumerate(rows):
        y = 284 + i * 22
        p.append(text(24, y, n, 11.5)); p.append(text(240, y, f"rows {a:.1f} ms", 11.5, cls="acct")); p.append(text(380, y, f"columns {b:.1f} ms", 11.5, cls="bad"))
        p.append(text(540, y, f"× {ratio:.1f}", 11.5, 600))
    return svg(840, 380, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("memory-hierarchy", hierarchy), ("two-level-magic", triangle), ("latency-ladder", ladder),
                     ("call-depth", calldepth), ("direct-mapped-cache", dmcache), ("fully-associative-cache", facache),
                     ("block-placement", placement), ("miss-rate-vs-line-size", blocksize), ("traversal", traversal)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
