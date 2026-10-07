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
    title = "Several programs in one RAM: who protects whom, and what if one more arrives?"
    p = [text(24, 30, title, 15, 600)]
    x, y0 = 60, 52
    parts = [("OS", 40, "plain"), ("process 1", 56, "acc"), ("process 2", 50, "c2"), ("process 3", 40, "acc"),
             ("free", 24, "plain"), ("process 4", 60, "c2"), ("free", 30, "plain")]
    y = y0
    for name, h, k in parts:
        p.append(rect(x, y, 160, h, k if k != "plain" else "tint", rx=0))
        p.append(text(x + 80, y + h / 2 + 4, name, 12, 600 if name != "free" else 400, cls="ink" if name != "free" else "quiet", anchor="middle"))
        y += h
    p.append(text(x + 80, y + 20, "physical RAM", 11.5, cls="quiet", anchor="middle"))
    p.append(rect(260, 120, 120, 70, "bad", rx=6)); p.append(text(320, 150, "process 5", 12, 600, anchor="middle"))
    p.append(text(320, 168, "needs 70", 11, cls="quiet", anchor="middle"))
    qs = [("Protection", "process 1 must not read or overwrite process 2 or the OS"),
          ("Relocation", "a program cannot know in advance at which address it will be loaded"),
          ("Fragmentation", "54 units are free, but in two holes: process 5 does not fit"),
          ("Size", "all processes together may need more memory than there is RAM")]
    for i, (a, b) in enumerate(qs):
        yy = 72 + i * 56
        p.append(text(420, yy, a, 13, 600)); p.append(text(420, yy + 18, b, 11.5, cls="quiet"))
    p.append(text(420, 310, "Virtual memory answers all four: every process gets its own private, contiguous", 11.5, cls="acct"))
    p.append(text(420, 328, "address space from 0 to max, mapped piece by piece onto RAM and the disk.", 11.5, cls="acct"))
    return svg(900, 400, title, "\n".join(p))


# ---------------- 2. Fragmentation ----------------
def fragmentation():
    title = "Internal and external fragmentation"
    p = [text(24, 30, title, 15, 600)]
    # internal
    p.append(text(24, 62, "Equal-sized blocks: internal fragmentation", 13, 600))
    for i, used in enumerate((1.0, 0.35, 0.9, 0.5)):
        y = 76 + i * 46
        p.append(rect(24, y, 200, 40, "tint", rx=2))
        p.append(f'<rect x="24" y="{y}" width="{200 * used:.0f}" height="40" class="accf"/>')
        p.append(text(234, y + 25, f"{int(used * 100)}% used", 11.5, cls="quiet"))
    p.append(text(24, 310, "the unused rest of each block is lost inside it", 11.5, cls="quiet"))
    p.append(text(24, 328, "(like half-empty shipping containers)", 11.5, cls="quiet"))
    # external
    x = 460
    p.append(text(x, 62, "Variable-sized blocks: external fragmentation", 13, 600))
    blocks = [("allocation 1", 30, "acc"), ("allocation 2", 44, "acc"), ("free", 34, "plain"), ("allocation 5", 50, "c2"), ("free", 28, "plain"), ("allocation 6", 26, "acc")]
    y = 76
    for name, h, k in blocks:
        p.append(rect(x, y, 180, h, k if k != "plain" else "tint", rx=0))
        p.append(text(x + 90, y + h / 2 + 4, name, 11.5, 600 if name != "free" else 400, cls="ink" if name != "free" else "quiet", anchor="middle"))
        y += h
    p.append(rect(x + 210, 120, 120, 50, "bad", rx=4)); p.append(text(x + 270, 141, "new request", 11.5, 600, anchor="middle"))
    p.append(text(x + 270, 158, "needs 50", 11, cls="quiet", anchor="middle"))
    p.append(text(x, 310, "62 units free in total, but no hole is big enough;", 11.5, cls="quiet"))
    p.append(text(x, 328, "compaction (defragmentation) would move the blocks together", 11.5, cls="quiet"))
    # zebra / horse
    p.append(text(24, 372, "A fragmented memory is like a zebra, a defragmented one a horse with all its dark stripes in one patch.", 11.5, cls="quiet"))
    for i in range(12):
        p.append(f'<rect x="{24 + i * 20}" y="386" width="10" height="20" class="{"acct" if i % 2 == 0 else "tint"}"/>')
    p.append(f'<rect x="300" y="386" width="120" height="20" class="acct"/><rect x="420" y="386" width="120" height="20" class="tint"/>')
    p.append(f'<rect x="300" y="386" width="240" height="20" fill="none" class="edge"/><rect x="24" y="386" width="240" height="20" fill="none" class="edge"/>')
    p.append(text(144, 424, "fragmented (zebra)", 11, cls="quiet", anchor="middle")); p.append(text(420, 424, "defragmented (horse)", 11, cls="quiet", anchor="middle"))
    return svg(860, 440, title, "\n".join(p))


# ---------------- 3. Paging: contiguous pages, scattered frames ----------------
def paging():
    m = "pg"
    title = "Paging: contiguous for the process, scattered in RAM"
    p = [f"<defs>{marker(m, 'acct')}{marker('pg2', 'c2')}</defs>", text(24, 30, title, 15, 600)]
    def pages(x, y, name, ids, kind):
        p.append(text(x, y - 8, name, 12.5, 600))
        for i, n in enumerate(ids):
            p.append(rect(x, y + i * 34, 90, 30, kind, rx=2)); p.append(text(x + 45, y + i * 34 + 20, f"page {n}", 11.5, 600, anchor="middle"))
    pages(40, 70, "process 1", (11, 12, 13), "acc")
    pages(40, 230, "process 2", (21, 22, 23), "c2")
    rx = 420
    p.append(text(rx, 52, "RAM: 4 KiB frames", 12.5, 600))
    content = {1: ("11", "acc"), 3: ("22", "c2"), 4: ("13", "acc"), 6: ("12", "acc"), 7: ("21", "c2"), 9: ("23", "c2")}
    for f in range(11):
        y = 62 + f * 28
        c = content.get(f)
        p.append(rect(rx, y, 140, 26, c[1] if c else "tint", rx=0))
        p.append(text(rx - 8, y + 18, str(f), 10.5, cls="quiet", anchor="end"))
        if c: p.append(text(rx + 70, y + 18, f"page {c[0]}", 11, 600, anchor="middle"))
    for (pi, f) in ((0, 1), (1, 6), (2, 4)):
        y1 = 85 + pi * 34; y2 = 75 + f * 28
        p.append(path(f"M132 {y1}C260 {y1} 300 {y2} {rx - 4} {y2}", m, cls="acc", width=1.5))
    for (pi, f) in ((0, 7), (1, 3), (2, 9)):
        y1 = 245 + pi * 34; y2 = 75 + f * 28
        p.append(path(f"M132 {y1}C260 {y1} 300 {y2} {rx - 4} {y2}", "pg2", cls="c2s", width=1.5))
    p.append(rect(640, 120, 200, 60, "tint", rx=6)); p.append(text(740, 145, "disk (swap)", 12, 600, anchor="middle"))
    p.append(text(740, 164, "pages not in RAM", 11, cls="quiet", anchor="middle"))
    p.append(text(24, 390, "Each page can go into any free frame: no external fragmentation, only a little internal fragmentation in each last page.", 11.5, cls="quiet"))
    return svg(870, 406, title, "\n".join(p))


# ---------------- 4. Address translation with one page table ----------------
def translation():
    m = "tr"
    title = "Address translation with a page table (32-bit addresses, 4 KiB pages)"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(60, 58, "virtual address", 12, 600, cls="quiet"))
    p.append(rect(60, 66, 320, 34, "acc", rx=3)); p.append(text(220, 88, "page number (20 bits)", 12, 600, anchor="middle"))
    p.append(rect(380, 66, 192, 34, "tint", rx=3)); p.append(text(476, 88, "offset (12 bits)", 12, 600, anchor="middle"))
    # page-table base register
    p.append(rect(40, 170, 150, 34, "c2", rx=4)); p.append(text(115, 192, "page-table base", 12, 600, anchor="middle"))
    p.append(text(115, 222, "(CR3 on x86; part of", 10.5, cls="quiet", anchor="middle")); p.append(text(115, 236, "each process's context)", 10.5, cls="quiet", anchor="middle"))
    # page table
    tx, ty = 250, 150
    p.append(text(tx, ty - 8, "page table of this process", 12, 600))
    cols = [("V", 26), ("R/W/X", 60), ("frame number", 120)]
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
    p.append(path("M190 187C220 187 230 180 246 180", m, width=1.5)); p.append(text(196, 176, "start", 10.5, cls="quiet"))
    # physical address
    p.append(text(560, 214, "physical address", 12, 600, cls="quiet"))
    p.append(rect(560, 222, 200, 34, "acc", rx=3)); p.append(text(660, 244, "frame number", 12, 600, anchor="middle"))
    p.append(rect(760, 222, 100, 34, "tint", rx=3)); p.append(text(810, 244, "offset", 12, 600, anchor="middle"))
    p.append(path("M458 239H556", m, width=1.5))
    p.append(path("M476 100C476 130 810 130 810 218", m, width=1.5)); p.append(text(640, 124, "copied unchanged", 11, cls="quiet"))
    p.append(text(24, 320, "V = 0: the page is not in RAM; the CPU raises a page fault (an interrupt), and the OS loads the page from disk or stops the program.", 11.5, cls="quiet"))
    p.append(text(24, 338, "Rights (read, write, execute, user/kernel): a forbidden access also faults. One table per process: switching processes switches the base register.", 11.5, cls="quiet"))
    return svg(880, 354, title, "\n".join(p))


# ---------------- 5. Four-level page table of x86-64 ----------------
def multilevel():
    m = "ml"
    title = "x86-64: a 48-bit virtual address walks a four-level page table"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    fields = [("PML4", 9), ("PDPT", 9), ("PD", 9), ("PT", 9), ("offset", 12)]
    x = 60
    for i, (n, b) in enumerate(fields):
        w = b * 13
        p.append(rect(x, 54, w, 32, "tint" if n == "offset" else "acc", rx=2)); p.append(text(x + w / 2, 75, f"{n} ({b})", 11.5, 600, anchor="middle"))
        x += w
    p.append(text(x + 10, 75, "= 48 bits", 11.5, cls="quiet"))
    for i, n in enumerate(("level 4", "level 3", "level 2", "level 1")):
        tx = 60 + i * 160; ty = 140
        p.append(rect(tx, ty, 110, 140, "tint", rx=4)); p.append(text(tx + 55, ty - 8, n, 11.5, 600, anchor="middle"))
        p.append(rect(tx, ty + 50 + i * 12, 110, 18, "acc", rx=0))
        p.append(text(tx + 55, ty + 128, "512 entries", 10.5, cls="quiet", anchor="middle"))
        p.append(path(f"M{60 + i * 117 + 58} 86C{60 + i * 117 + 58} 110 {tx + 55} 110 {tx + 55} {ty - 22}", m, width=1.2))
        if i < 3:
            p.append(path(f"M{tx + 110} {ty + 59 + i * 12}C{tx + 135} {ty + 59 + i * 12} {tx + 135} {ty + 20} {tx + 158} {ty + 20}", m, width=1.5))
    p.append(rect(60, 300, 80, 28, "c2", rx=4)); p.append(text(100, 319, "CR3", 12, 600, anchor="middle"))
    p.append(path("M100 300V284", m, width=1.5))
    p.append(path("M650 235C670 235 660 205 676 205", m, width=1.5)); p.append(rect(680, 185, 150, 40, "acc", rx=4)); p.append(text(755, 210, "frame + offset", 12, 600, anchor="middle"))
    p.append(text(24, 362, "Each table fills exactly one 4 KiB page (512 entries of 8 bytes). Tables exist only for the parts of the address space in use,", 11.5, cls="quiet"))
    p.append(text(24, 380, "so a small process needs a few pages of tables instead of one huge flat table. The price: up to four extra memory reads per", 11.5, cls="quiet"))
    p.append(text(24, 398, "translation, which is why the TLB matters. Newer CPUs offer a fifth level (57-bit addresses).", 11.5, cls="quiet"))
    return svg(860, 414, title, "\n".join(p))


# ---------------- 6. TLB, page table and cache on one access ----------------
def tlbpath():
    m = "tp"
    title = "One memory access: TLB, page-table walk, then the cache"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(rect(40, 60, 170, 34, "acc", rx=3)); p.append(text(125, 82, "virtual address", 12, 600, anchor="middle"))
    p.append(rect(270, 50, 160, 54, "c2", rx=6)); p.append(text(350, 74, "TLB", 13, 600, anchor="middle")); p.append(text(350, 92, "recent translations", 10.5, cls="quiet", anchor="middle"))
    p.append(path("M210 77H266", m, width=1.5))
    p.append(rect(270, 160, 160, 54, "tint", rx=6)); p.append(text(350, 184, "page-table walk", 12, 600, anchor="middle")); p.append(text(350, 202, "in memory (slow)", 10.5, cls="quiet", anchor="middle"))
    p.append(path("M350 104V156", m, width=1.5)); p.append(text(358, 134, "TLB miss", 11, cls="quiet"))
    p.append(rect(500, 100, 160, 40, "acc", rx=4)); p.append(text(580, 125, "physical address", 12, 600, anchor="middle"))
    p.append(path("M430 77C470 77 480 110 496 116", m, width=1.5)); p.append(text(470, 72, "TLB hit", 11, cls="quiet"))
    p.append(path("M430 187C470 187 480 134 496 128", m, width=1.5))
    p.append(rect(500, 200, 160, 54, "c2", rx=6)); p.append(text(580, 224, "cache", 13, 600, anchor="middle")); p.append(text(580, 242, "(previous lecture)", 10.5, cls="quiet", anchor="middle"))
    p.append(path("M580 140V196", m, width=1.5))
    p.append(rect(720, 200, 120, 54, "tint", rx=6)); p.append(text(780, 230, "RAM", 13, 600, anchor="middle"))
    p.append(path("M660 227H716", m, width=1.5)); p.append(text(688, 220, "miss", 11, cls="quiet", anchor="middle"))
    p.append(path("M350 214C350 300 700 300 760 258", m, width=1.2, dash="4 4")); p.append(text(520, 300, "the walk itself reads page-table entries through the cache", 11, cls="quiet", anchor="middle"))
    p.append(text(24, 336, "Valid bit 0 in the page table: a page fault, handled by the operating system, which may have to read the page from disk (milliseconds).", 11.5, cls="quiet"))
    return svg(870, 352, title, "\n".join(p))


# ---------------- 7. Belady's anomaly (from the simulator) ----------------
def belady():
    spec = importlib.util.spec_from_file_location("pagesim", os.path.join(HERE, "pagesim.py"))
    ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
    title = "Bélády's anomaly: FIFO with 3 frames makes 9 faults, with 4 frames 10"
    p = [text(24, 30, title, 15, 600)]
    y0 = 60
    for n in (3, 4):
        faults, hist = ps.simulate(ps.EXAMPLE, n, "fifo")
        p.append(text(24, y0 + 18, f"{n} frames", 12.5, 600))
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
        p.append(text(120 + 12 * 52 + 10, y0 + 70, f"{faults} faults", 13, 600, cls="bad" if n == 4 else "ink"))
        y0 += 50 + n * 24 + 20
    p.append(text(24, y0 + 6, "Circled: page fault. Each column shows the frames after the reference, newest page on top; FIFO evicts the bottom one.", 11.5, cls="quiet"))
    p.append(text(24, y0 + 24, "LRU and OPT never do this: with more frames they always hold a superset of what they would hold with fewer (stack algorithms).", 11.5, cls="quiet"))
    return svg(860, y0 + 40, title, "\n".join(p))


# ---------------- 8. TLB measurement ----------------
def tlbchart():
    title = "Same cached data, more pages: the cost of address translation (measured, tlb.c)"
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
        p.append(text(X(i), y0 + 18, f"{n:,}", 10.5, cls="quiet", anchor="middle"))
    p.append(text((x0 + x1) / 2, y0 + 38, "number of different pages touched (one 64-byte line in each)", 11.5, cls="quiet", anchor="middle"))
    for data, cls, lab in ((small, "c2", "4 KiB pages"), (huge, "acct", "2 MiB huge pages")):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(data))
        stroke = "c2s" if cls == "c2" else "acc"
        p.append(f'<polyline points="{pts}" fill="none" class="{stroke}" stroke-width="2.5"/>')
        for i, v in enumerate(data):
            p.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" class="{cls}"/>')
    p.append(f'<rect x="100" y="70" width="14" height="4" class="c2"/>'); p.append(text(120, 76, "4 KiB pages", 11.5))
    p.append(f'<rect x="100" y="90" width="14" height="4" class="acct"/>'); p.append(text(120, 96, "2 MiB huge pages", 11.5))
    p.append(text(24, 386, "Up to 4,096 pages the touched lines (256 KiB) still fit in the L2 cache; the difference between the curves is translation:", 11.5, cls="quiet"))
    p.append(text(24, 404, "4 KiB pages overflow the TLB, while 1 GiB of 2 MiB pages needs only 512 translations.", 11.5, cls="quiet"))
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
    title = "Fault rate against the number of frames (simulated, pagesim.py thrash)"
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
    p.append(text(X(6.5), y1 + 18, "thrashing: fewer frames than the working set", 11.5, 600, anchor="middle"))
    pts = " ".join(f"{X(n):.1f},{Y(v):.1f}" for n, v in zip(frames, rates))
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    p.append(f'<line x1="{X(12):.1f}" y1="{y1}" x2="{X(12):.1f}" y2="{y0}" class="c2s" stroke-width="1.5" stroke-dasharray="5 4"/>')
    p.append(text(X(12) + 6, y1 + 40, "working set: 12 pages", 11.5, 600))
    p.append(text((x0 + x1) / 2, y0 + 38, "frames given to the process", 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, 360, "Below its working set, a process faults on a large part of its references and spends its time waiting for the disk.", 11.5, cls="quiet"))
    return svg(800, 376, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("separation", separation), ("fragmentation", fragmentation), ("paging", paging),
                     ("address-translation", translation), ("x86-64-page-walk", multilevel), ("tlb-path", tlbpath),
                     ("belady-anomaly", belady), ("tlb-measured", tlbchart), ("thrashing", thrash)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
