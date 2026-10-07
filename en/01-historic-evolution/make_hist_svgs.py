"""Generate the SVG figures for the Operating Systems Historic Evolution lecture.

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
"""

STYLE = """<style>
  .ink{fill:#1f1f1f}.quiet{fill:#6b6b66}.edge{stroke:#b5b4a8}.edgef{fill:#b5b4a8}
  .grid{stroke:#e3e2da}.acc{stroke:#2f6fd6}.accf{fill:#2f6fd6;fill-opacity:.12}.acct{fill:#2f6fd6}
  .c2{fill:#d9822b}.c2s{stroke:#d9822b}.c2f{fill:#d9822b;fill-opacity:.14}.tint{fill:#f4f3ee}
  text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
  @media (prefers-color-scheme: dark){
    .ink{fill:#e8e8e3}.quiet{fill:#a3a39c}.edge{stroke:#6f6e66}.edgef{fill:#6f6e66}
    .grid{stroke:#3a3a35}.acc{stroke:#5b93ef}.accf{fill:#5b93ef;fill-opacity:.18}.acct{fill:#7aa9f5}
    .c2{fill:#eb9a4b}.c2s{stroke:#eb9a4b}.c2f{fill:#eb9a4b;fill-opacity:.2}.tint{fill:#22221f}
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


def path(d, mid=None, cls="edge", width=1.25, dash=None, start=False):
    a = f' marker-end="url(#{mid})"' if mid else ""
    b = f' marker-start="url(#{mid})"' if (mid and start) else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" class="{cls}" stroke-width="{width}"{a}{b}{da}/>'


def rect(x, y, w, h, kind="plain", rx=8):
    if kind == "acc":
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="accf"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" class="acc" stroke-width="2"/>')
    if kind == "c2":
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="c2f"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" class="c2s" stroke-width="1.5"/>')
    t = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="tint"/>' if kind == "tint" else ""
    return t + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" class="edge" stroke-width="1.25"/>'


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}">\n<title>{esc(title)}</title>\n{STYLE}\n{body}\n</svg>\n')


# ---------------- 1. Timeline ----------------
def timeline():
    title = "Each era added a new OS idea; the ideas outlived the machines"
    y0, x0, x1 = 1940, 200, 724
    X = lambda yr: x0 + (x1 - x0) * (yr - y0) / (2025 - y0)
    lanes = [  # name, start, note
        ("Raw hardware, one user", 1945, 1956, "switches, lamps, plugboards"),
        ("Batch processing", 1956, None, "GM-NAA I/O (1956)"),
        ("Multiprogramming", 1962, None, "Atlas Supervisor (1962)"),
        ("Time sharing", 1961, None, "CTSS (1961), Multics, Unix (1969)"),
        ("Minicomputers", 1965, 1990, "PDP-8, PDP-11, VAX"),
        ("Personal computers", 1974, None, "CP/M (1974), IBM PC + DOS (1981), Mac (1984)"),
        ("Networked systems", 1983, None, "ARPANET moves to TCP/IP (1983)"),
        ("Battery-powered, portable", 1992, None, "laptops, then phones"),
    ]
    top, step = 96, 40
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Approximate start of each approach (bars run on to today where the idea is still in use)", 11.5, cls="quiet")]
    # axis
    ya = top + len(lanes) * step + 4
    for yr in range(1940, 2030, 10):
        x = X(yr)
        p.append(f'<line x1="{x:.1f}" y1="{top - 16}" x2="{x:.1f}" y2="{ya}" class="grid"/>')
        p.append(text(x, ya + 18, str(yr), 11.5, cls="quiet", anchor="middle"))
    for i, (name, a, b, note) in enumerate(lanes):
        y = top + i * step
        p.append(text(24, y + 5, name, 12.5, 600))
        end = X(b) if b else X(2025)
        kind = "acc" if i in (1, 2, 3) else "tint"
        p.append(rect(X(a), y - 9, end - X(a), 18, kind, rx=4))
        nx = X(a) + 8 if (end - X(a)) > 200 else X(a) - 8
        anchor = "start" if (end - X(a)) > 200 else "end"
        if b:  # finished era: note after the bar
            p.append(text(end + 8, y + 4, note, 11.5, cls="quiet"))
        elif anchor == "start":
            p.append(text(nx, y + 4, note, 11.5))
        else:
            p.append(text(nx, y + 4, note, 11.5, cls="quiet", anchor="end"))
    p.append(text(24, ya + 44, "Before 1945: abacus (memory + fast addition), Hollerith's punched-card tabulator (1890 US census), wartime machines.", 11.5, cls="quiet"))
    p.append(text(24, ya + 62, "Highlighted: the three ideas that made the operating system necessary.", 11.5, cls="quiet"))
    return svg(760, ya + 80, title, "\n".join(p))


# ---------------- 2. Batch job deck + resident monitor ----------------
def batch():
    m = "bt"
    title = "A batch job is a deck of cards; the monitor stays resident in memory"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # card deck, drawn as offset cards, first card read = bottom
    cards = ["DAT2  data for program 2", "PR2   program 2", "DAT1  data for program 1",
             "PR1   program 1 (source code)", "compiler", "loader (loads the compiler)"]
    x, y, w, h, dx, dy = 40, 84, 300, 30, 14, 34
    p.append(text(40, 70, "The job deck (read from the bottom up)", 13, 600))
    for i, c in enumerate(cards):
        cx, cy = x + i * 0, y + i * dy
        p.append(f'<path d="M{cx} {cy}H{cx + w - 18}L{cx + w} {cy + 12}V{cy + h}H{cx}Z" class="tint"/>')
        p.append(f'<path d="M{cx} {cy}H{cx + w - 18}L{cx + w} {cy + 12}V{cy + h}H{cx}Z" fill="none" class="edge" stroke-width="1.25"/>')
        p.append(text(cx + 14, cy + 20, c, 12.5))
    yb = y + len(cards) * dy
    p.append(path(f"M{x + w / 2} {yb + 4}V{yb + 36}", m))
    p.append(text(x + w / 2 + 10, yb + 26, "card reader", 11.5, cls="quiet"))
    # memory map
    mx, my, mw = 470, 84, 220
    p.append(text(mx, 70, "Main memory", 13, 600))
    p.append(rect(mx, my, mw, 92, "acc", rx=6))
    p.append(text(mx + 14, my + 24, "Resident monitor", 13, 600))
    for i, t in enumerate(["• device routines: card reader,", "   printer, tape", "• job sequencing"]):
        p.append(text(mx + 14, my + 46 + i * 16, t, 11.5))
    p.append(rect(mx, my + 92, mw, 172, "plain", rx=0))
    p.append(text(mx + 14, my + 120, "User program area", 13, 600))
    p.append(text(mx + 14, my + 140, "one job at a time:", 11.5, cls="quiet"))
    p.append(text(mx + 14, my + 156, "compiler, then PR1, then PR2", 11.5, cls="quiet"))
    p.append(text(mx + mw + 8, my + 10, "MAX", 11.5, cls="quiet"))
    p.append(text(mx + mw + 8, my + 264, "0", 11.5, cls="quiet"))
    p.append(path(f"M{x + w + 14} {y + 3 * dy}C{410} {y + 3 * dy} {420} {my + 180} {mx} {my + 180}", m))
    p.append(text(372, y + 3 * dy - 10, "loaded", 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, my + 300, "The programs call the monitor's device routines instead of containing their own: the first step towards an OS.", 11.5, cls="quiet"))
    return svg(760, my + 320, title, "\n".join(p))


# ---------------- 3. Multiprogramming (measured) ----------------
def multiprog():
    title = "Two jobs on one CPU core: 4.03 s one after the other, 2.44 s together"
    x0, x1 = 170, 640
    T = 4.2
    X = lambda t: x0 + (x1 - x0) * t / T
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Measured on Linux with jobs.c: the CPU job computes for 2 s; the I/O job computes 10 ms, then waits 40 ms, 40 times.", 11.5, cls="quiet")]

    def row(y, label, sub, segs, total, util):
        out = [text(24, y + 4, label, 13, 600), text(24, y + 20, sub, 11.5, cls="quiet")]
        out.append(f'<rect x="{x0}" y="{y - 12}" width="{X(total) - x0:.1f}" height="28" class="tint"/>')
        for a, b, kind in segs:
            cls = "acct" if kind == "cpu" else "c2"
            out.append(f'<rect x="{X(a):.2f}" y="{y - 12}" width="{max(X(b) - X(a), 0.8):.2f}" height="28" class="{cls}"/>')
        out.append(f'<rect x="{x0}" y="{y - 12}" width="{X(total) - x0:.1f}" height="28" fill="none" class="edge" stroke-width="1"/>')
        out.append(text(X(total) + 8, y + 2, f"{total:.2f} s", 12.5, 600))
        out.append(text(X(total) + 8, y + 18, f"CPU busy {util}", 11.5, cls="quiet"))
        return out

    seq = [(0, 2.02, "cpu")] + [(2.02 + k * 0.0502, 2.02 + k * 0.0502 + 0.010, "io") for k in range(40)]
    tog = []
    for k in range(40):
        a = k * 0.0600
        tog.append((a, a + 0.010, "io"))
        tog.append((a + 0.010, a + 0.060, "cpu"))
    tog.append((2.40, 2.44, "cpu"))
    p += row(110, "One after the other", "sequential, like early batch", seq, 4.03, "60%")
    p += row(190, "Together", "multiprogramming", tog, 2.44, "99%")
    ya = 230
    for t in range(0, 5):
        p.append(f'<line x1="{X(t):.1f}" y1="{ya}" x2="{X(t):.1f}" y2="{ya + 5}" class="edge" stroke-width="1.25"/>')
        p.append(text(X(t), ya + 19, f"{t} s", 11.5, cls="quiet", anchor="middle"))
    p.append(f'<line x1="{x0}" y1="{ya}" x2="{x1}" y2="{ya}" class="edge" stroke-width="1.25"/>')
    ly = 278
    p.append(f'<rect x="24" y="{ly - 10}" width="14" height="14" class="acct"/>')
    p.append(text(44, ly + 2, "CPU-bound job computing", 11.5))
    p.append(f'<rect x="224" y="{ly - 10}" width="14" height="14" class="c2"/>')
    p.append(text(244, ly + 2, "I/O-bound job computing", 11.5))
    p.append(f'<rect x="424" y="{ly - 10}" width="14" height="14" class="tint"/><rect x="424" y="{ly - 10}" width="14" height="14" fill="none" class="edge"/>')
    p.append(text(444, ly + 2, "CPU idle: the only job is waiting for I/O", 11.5))
    p.append(text(24, ly + 30, "Schematic: the real run had about 650 context switches, too many to draw. The I/O job's bursts are drawn wider than to scale.", 11.5, cls="quiet"))
    return svg(760, ly + 50, title, "\n".join(p))


# ---------------- 4. Virtual memory ----------------
def vmem():
    m, mo = "vm", "vmo"
    title = "Each program sees its own memory from 0 to MAX; the OS maps its pages to frames"
    p = [f"<defs>{marker(m)}{marker(mo, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # virtual spaces
    def vspace(x, y, name, kind):
        out = [rect(x - 96, y + 36, 80, 40, kind), text(x - 56, y + 61, name, 13, 600, anchor="middle"),
               text(x, y + 10, "0", 11.5, cls="quiet"), text(x, y + 120, "MAX", 11.5, cls="quiet")]
        for i in range(5):
            out.append(rect(x + 34, y + i * 22, 70, 20, "tint", rx=2))
            out.append(text(x + 69, y + i * 22 + 14, f"page {i}", 11, cls="quiet", anchor="middle"))
        return out
    p += vspace(150, 90, "PR 1", "acc")
    p += vspace(150, 250, "PR 2", "c2")
    p.append(text(220, 76, "virtual memory", 12.5, 600, anchor="middle"))
    p.append(text(150 + 112, 90 + 4 * 22 + 14, "not used yet", 11, cls="quiet"))
    # RAM
    rx, ry, rw = 450, 90, 110
    p.append(text(rx + rw / 2, 76, "physical memory (RAM, 8 GB)", 12.5, 600, anchor="middle"))
    owners = ["p1", "", "p2", "p1", "", "p2", "p1", "p2", "", "p2"]
    for i, o in enumerate(owners):
        kind = "acc" if o == "p1" else ("c2" if o == "p2" else "plain")
        p.append(rect(rx, ry + i * 24, rw, 22, kind, rx=2))
        p.append(text(rx + rw + 8, ry + i * 24 + 15, f"frame {i}", 11, cls="quiet"))
    # disk
    dx, dy = 640, 300
    p.append(rect(dx - 20, dy, 110, 70, "plain"))
    p.append(text(dx + 35, dy + 28, "disk (swap)", 12.5, 600, anchor="middle"))
    p.append(text(dx + 35, dy + 48, "16 GB", 11.5, cls="quiet", anchor="middle"))
    # mappings: (proc_y, page, frame) ; None frame -> disk
    v1, v2 = 90, 250
    vx = 150 + 104
    maps = [(v1, 0, 0), (v1, 1, 3), (v1, 2, 6), (v1, 3, None),
            (v2, 0, 2), (v2, 1, 5), (v2, 2, 7), (v2, 3, 9), (v2, 4, None)]
    for vy, pg, fr in maps:
        sy = vy + pg * 22 + 10
        if fr is None:
            p.append(path(f"M{vx} {sy}C{380} {sy} {380} {dy + 60} {dx - 20} {dy + 50}", None, dash="4 3"))
        else:
            ty = ry + fr * 24 + 11
            p.append(path(f"M{vx} {sy}C{360} {sy} {360} {ty} {rx} {ty}", m))
    p.append(path(f"M{rx + rw + 52} {ry + 4 * 24 + 11}C{650} {ry + 4 * 24 + 11} {670} {dy - 40} {dx + 30} {dy}", m, dash="4 3", start=True))
    p.append(text(650, 208, "pages moved out", 11.5, cls="quiet"))
    p.append(text(650, 224, "and back in", 11.5, cls="quiet"))
    p.append(text(24, 404, "Solid arrows: page in RAM. Dashed: page currently on disk; touching it causes a page fault, and the OS loads it back.", 11.5, cls="quiet"))
    p.append(text(24, 422, "Neither program can reach a frame the OS has not mapped for it: this is the memory protection.", 11.5, cls="quiet"))
    return svg(760, 442, title, "\n".join(p))


# ---------------- 5. Layers ----------------
def layers():
    title = "The operating system sits between the hardware and the programs"
    rows = [("Application programs", "web browser, game, banking system"),
            ("System programs", "shell, compilers, editors, utilities"),
            ("Kernel", "process, memory, device and file management"),
            ("Machine language", "the CPU's instruction set (ISA)"),
            ("Microarchitecture", "how the CPU carries out instructions"),
            ("Physical devices", "chips, wires, disks")]
    x, y0, w, h = 150, 72, 340, 48
    p = [text(24, 30, title, 15, 600)]
    for i, (a, b) in enumerate(rows):
        y = y0 + i * h
        kind = "acc" if i == 2 else ("c2" if i == 1 else "tint")
        p.append(rect(x, y, w, h - 6, kind, rx=6))
        p.append(text(x + 16, y + 19, a, 13, 600))
        p.append(text(x + 16, y + 35, b, 11.5, cls="quiet"))
    # OS brackets
    bx = x + w + 16
    p.append(f'<path d="M{bx} {y0 + 2 * h}h10V{y0 + 3 * h - 6}h-10" fill="none" class="acc" stroke-width="2"/>')
    p.append(text(bx + 18, y0 + 2 * h + 18, "the OS in the", 11.5, 600, cls="acct"))
    p.append(text(bx + 18, y0 + 2 * h + 34, "narrow sense", 11.5, 600, cls="acct"))
    p.append(f'<path d="M{bx + 120} {y0 + 1 * h}h10V{y0 + 3 * h - 6}h-10" fill="none" class="c2s" stroke-width="2"/>')
    p.append(text(bx + 138, y0 + 1 * h + 42, "the OS in the", 11.5, 600))
    p.append(text(bx + 138, y0 + 1 * h + 58, "broad sense", 11.5, 600))
    p.append(f'<line x1="{x - 8}" y1="{y0 + 2 * h - 3}" x2="{x + w + 8}" y2="{y0 + 2 * h - 3}" class="acc" stroke-width="1.5" stroke-dasharray="5 4"/>')
    p.append(text(x - 12, y0 + 2 * h - 20, "user mode", 11.5, cls="quiet", anchor="end"))
    p.append(text(x - 12, y0 + 2 * h + 1, "system calls", 11.5, 600, cls="acct", anchor="end"))
    p.append(text(x - 12, y0 + 2 * h + 22, "kernel mode", 11.5, cls="quiet", anchor="end"))
    p.append(text(x - 12, y0 + 3 * h + 22, "hardware", 11.5, cls="quiet", anchor="end"))
    p.append(text(24, y0 + 6 * h + 22, "Adapted from Tanenbaum (2001). Where the OS ends is a matter of definition: firmware and microcode are borderline.", 11.5, cls="quiet"))
    return svg(760, y0 + 6 * h + 42, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("os-timeline", timeline), ("batch-monitor", batch), ("multiprogramming", multiprog),
                    ("virtual-memory", vmem), ("os-layers", layers)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
