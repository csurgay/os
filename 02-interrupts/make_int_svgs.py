"""Generate the SVG figures for the Interrupts lecture (English labels).

Same look as the Fetch-Execute Cycle figures: light/dark aware, system font, quiet strokes, one accent.
"""

STYLE = """<style>
  .ink{fill:#1f1f1f}.quiet{fill:#6b6b66}.edge{stroke:#b5b4a8}.edgef{fill:#b5b4a8}
  .grid{stroke:#e3e2da}.acc{stroke:#2f6fd6}.accf{fill:#2f6fd6;fill-opacity:.12}.acct{fill:#2f6fd6}
  .bad{fill:#c8372d}.bads{stroke:#c8372d}.tint{fill:#f4f3ee}
  text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
  .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
  @media (prefers-color-scheme: dark){
    .ink{fill:#e8e8e3}.quiet{fill:#a3a39c}.edge{stroke:#6f6e66}.edgef{fill:#6f6e66}
    .grid{stroke:#3a3a35}.acc{stroke:#5b93ef}.accf{fill:#5b93ef;fill-opacity:.18}.acct{fill:#7aa9f5}
    .bad{fill:#ff7b70}.bads{stroke:#ff7b70}.tint{fill:#22221f}
  }
</style>"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, weight=400, cls="ink", anchor="start", mono=False):
    c = f"{cls} mono" if mono else cls
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'class="{c}" text-anchor="{anchor}">{esc(s)}</text>')


def marker(mid):
    return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="edgef"/></marker>')


def marker_acc(mid):
    return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="acct"/></marker>')


def path(d, mid, start=False, end=True, cls="edge", width=1.25, dash=None):
    a = f' marker-end="url(#{mid})"' if end else ""
    b = f' marker-start="url(#{mid})"' if start else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" class="{cls}" stroke-width="{width}"{a}{b}{da}/>'


def rect(x, y, w, h, main=False, tint=False):
    if main:
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="accf"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" class="acc" stroke-width="2"/>')
    t = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="tint"/>' if tint else ""
    return t + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" class="edge" stroke-width="1.25"/>'


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}">\n<title>{esc(title)}</title>\n{STYLE}\n{body}\n</svg>\n')


# ---------------- 1. The cycle, with the atomic part marked ----------------
def cycle():
    W, H, rowA, rowB = 136, 56, 150, 268
    c1, c2, c3, cd, hw = 96, 256, 416, 600, 240
    m = "ic"
    title = "An interrupt is only taken between two instructions"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # atomic brace over Fetch..Execute
    bx0, bx1, by = c1 - W / 2, c3 + W / 2, 98
    p.append(path(f"M{bx0} {by + 10}V{by}H{bx1}V{by + 10}", m, end=False, cls="acc", width=2))
    p.append(text((bx0 + bx1) / 2, by - 10, "atomic: one instruction, never interrupted halfway", 11.5, 600, cls="acct", anchor="middle"))
    p += [
        path(f"M{c1 + W / 2} {rowA}H{c2 - W / 2}", m),
        path(f"M{c2 + W / 2} {rowA}H{c3 - W / 2}", m),
        path(f"M{c3 + W / 2} {rowA}H{cd - 64}", m),
        path(f"M{cd - hw / 2} {rowB}H{c1}V{rowA + H / 2}", m),
        path(f"M{cd} {rowA + 40}V{rowB - 28}", m),
        path(f"M{cd + 64} {rowA}H{736}V{rowB + 52}H{14}V{rowA}H{c1 - W / 2}", m),
    ]
    for cx, name, sub in [(c1, "Fetch", "fetch instruction"),
                          (c2, "Decode", "decode CIR"),
                          (c3, "Execute", "operate or jump")]:
        p.append(rect(cx - W / 2, rowA - H / 2, W, H))
        p.append(text(cx, rowA - 4, name, 13, 600, anchor="middle"))
        p.append(text(cx, rowA + 14, sub, 11.5, cls="quiet", anchor="middle"))
    pts = f"{cd - 64},{rowA} {cd},{rowA - 40} {cd + 64},{rowA} {cd},{rowA + 40}"
    p.append(f'<polygon points="{pts}" class="accf"/><polygon points="{pts}" fill="none" class="acc" stroke-width="2"/>')
    p.append(text(cd, rowA - 2, "Interrupt", 13, 600, anchor="middle"))
    p.append(text(cd, rowA + 14, "pending?", 13, 600, anchor="middle"))
    p.append(rect(cd - hw / 2, rowB - 28, hw, 56))
    p.append(text(cd, rowB - 4, "Interrupt handler", 13, 600, anchor="middle"))
    p.append(text(cd, rowB + 14, "PC already points to the next instruction", 11.5, cls="quiet", anchor="middle"))
    p.append(text(cd + 10, rowA + 64, "yes", 11.5, cls="quiet"))
    p.append(text(728, rowA - 8, "no", 11.5, cls="quiet", anchor="end"))
    p.append(text((c1 + cd - hw / 2) / 2, rowB - 8, "the handler is fetched like any other code", 11.5, cls="quiet", anchor="middle"))
    p.append(text(400, rowB + 70, "no interrupt: straight on to the next instruction", 11.5, cls="quiet", anchor="middle"))
    return svg(760, 360, title, "\n".join(p))


# ---------------- 2. Interrupt processing: hardware then software ----------------
def processing():
    m = "ip"
    title = "The hardware saves the minimum, the handler saves the rest"
    xL, xR, w, h, y0, step = 40, 420, 300, 56, 104, 76
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(xL, 76, "Hardware (automatic, every interrupt)", 13, 600))
    p.append(text(xR, 76, "Software (interrupt handler, in the OS)", 13, 600))
    hw = [
        ("1  Device raises interrupt request", "e.g. transfer finished, timer expired", False),
        ("2  CPU finishes current instruction", "the instruction cycle is atomic", False),
        ("3  CPU acknowledges, device clears IR", "the request will not be taken twice", False),
        ("4  CPU saves PC and PSW", "pushed on the stack (LIFO)", True),
        ("5  CPU loads new PC from vector", "interrupt vector table → handler address", False),
    ]
    sw = [
        ("6  Save the other registers", "the rest of the process state", False),
        ("7  Run the handler routine", "service the device, keep it short", False),
        ("8  Restore the other registers", "in reverse order (LIFO)", False),
        ("9  Restore PC and PSW", "return instruction: the program resumes", True),
    ]
    for i, (a, b, acc) in enumerate(hw):
        y = y0 + i * step
        p.append(rect(xL, y, w, h, acc, tint=not acc))
        p.append(text(xL + 12, y + 24, a, 13, 600))
        p.append(text(xL + 30, y + 42, b, 11.5, cls="quiet"))
        if i < len(hw) - 1:
            p.append(path(f"M{xL + w / 2} {y + h}V{y + step}", m))
    for i, (a, b, acc) in enumerate(sw):
        y = y0 + i * step
        p.append(rect(xR, y, w, h, acc))
        p.append(text(xR + 12, y + 24, a, 13, 600))
        p.append(text(xR + 30, y + 42, b, 11.5, cls="quiet"))
        if i < len(sw) - 1:
            p.append(path(f"M{xR + w / 2} {y + h}V{y + step}", m))
    # hand-over from hardware (5) to software (6)
    y5 = y0 + 4 * step + h / 2
    p.append(path(f"M{xL + w} {y5}H{380}V{y0 + h / 2}H{xR}", m))
    # return
    y9 = y0 + 3 * step + h
    p.append(path(f"M{xR + w / 2} {y9}V{y9 + 40}", m))
    p.append(text(xR + w / 2, y9 + 58, "back to the interrupted program,", 11.5, cls="quiet", anchor="middle"))
    p.append(text(xR + w / 2, y9 + 74, "at the saved PC", 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, 504, "Highlighted: the one pair the hardware itself saves and the return instruction restores", 11.5, cls="quiet"))
    return svg(760, 524, title, "\n".join(p))


# ---------------- 3. Nested interrupts ----------------
def nested():
    m, ma = "ni", "nia"
    title = "Nested interrupts return in reverse order, like a stack"
    cols = [(24, "User program"), (304, "Interrupt handler"), (584, "High-priority handler")]
    cw, top, n, dy = 152, 104, 11, 20
    ly = lambda i: top + 16 + i * dy
    p = [f"<defs>{marker(m)}{marker_acc(ma)}</defs>", text(24, 30, title, 15, 600)]
    for x, name in cols:
        p.append(text(x + cw / 2, 84, name, 13, 600, anchor="middle"))
        p.append(rect(x, top, cw, n * dy + 12))
        for i in range(n):
            p.append(f'<line x1="{x + 20}" y1="{ly(i)}" x2="{x + cw - 20}" y2="{ly(i)}" class="grid" stroke-width="2"/>')
    # addresses in the user program
    for i, lab in enumerate(["0", "1", "2", "3"]):
        p.append(text(36, ly(i) + 4, lab, 11.5, cls="quiet"))
    # interrupt points (accent dots)
    p.append(f'<circle cx="{24 + cw - 20}" cy="{ly(2)}" r="4" class="acct"/>')
    p.append(f'<circle cx="{304 + cw - 20}" cy="{ly(5)}" r="4" class="acct"/>')
    # handler notes
    p.append(text(304 + 26, ly(0) - 4, "save registers", 11.5, cls="acct"))
    p.append(text(304 + 26, ly(10) + 16, "restore, return", 11.5, cls="acct"))
    # arrows
    p.append(path(f"M{24 + cw} {ly(2)}C{230} {ly(2)} {250} {ly(0)} {304} {ly(0)}", ma, cls="acc", width=1.5))
    p.append(path(f"M{304} {ly(10)}C{240} {ly(10)} {230} {ly(3)} {24 + cw} {ly(3)}", m))
    p.append(path(f"M{304 + cw} {ly(5)}C{510} {ly(5)} {530} {ly(0)} {584} {ly(0)}", ma, cls="acc", width=1.5))
    p.append(path(f"M{584} {ly(9)}C{520} {ly(9)} {510} {ly(6)} {304 + cw} {ly(6)}", m))
    p.append(text(240, ly(0) - 14, "interrupt", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(240, top + n * dy + 30, "return to address 3", 11.5, cls="quiet", anchor="middle"))
    p.append(text(520, ly(0) - 14, "higher-priority interrupt", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(520, top + n * dy + 30, "back to handler", 11.5, cls="quiet", anchor="middle"))
    # stack panel
    sy = top + n * dy + 72
    p.append(text(24, sy, "The stack while the high-priority handler runs", 13, 600))
    sx, sw_, sh = 24, 260, 30
    p.append(rect(sx, sy + 14, sw_, sh, main=True))
    p.append(text(sx + 12, sy + 34, "PC + PSW of the first handler", 12.5))
    p.append(rect(sx, sy + 14 + sh + 6, sw_, sh))
    p.append(text(sx + 12, sy + 34 + sh + 6, "PC = 3 + PSW of the user program", 12.5))
    p.append(text(sx + sw_ + 16, sy + 34, "← top: popped first", 11.5, cls="quiet"))
    p.append(text(sx + sw_ + 16, sy + 34 + sh + 6, "← popped last", 11.5, cls="quiet"))
    p.append(text(330, sy + 112, "A lower-priority request that arrives meanwhile waits until the higher one is done.", 11.5, cls="quiet", anchor="middle"))
    return svg(760, sy + 134, title, "\n".join(p))


# ---------------- 4. Race condition, two panels ----------------
def race():
    m, ma = "rc", "rca"
    title = "A badly timed interrupt lets two processes into the critical section"
    xs = [214, 344, 474, 604]
    bw, bh = 116, 30
    p = [f"<defs>{marker(m)}{marker_acc(ma)}</defs>", text(24, 30, title, 15, 600)]

    def panel(y0, heading, steps, var, values, bad_from, note):
        out = [text(24, y0, heading, 13, 600)]
        lanes = {"P1": y0 + 34, "P2": y0 + 78}
        vy = y0 + 118
        for lane, ly in lanes.items():
            out.append(text(24, ly + 5, lane, 13, 600))
            out.append(f'<line x1="70" y1="{ly}" x2="{xs[len(steps) - 1] + bw / 2 + 20}" y2="{ly}" class="grid"/>')
        out.append(text(24, vy + 4, var, 13, 600, mono=True))
        prev = None
        for i, (lane, code) in enumerate(steps):
            x, ly = xs[i], lanes[lane]
            out.append(f'<rect x="{x - bw / 2}" y="{ly - bh / 2}" width="{bw}" height="{bh}" rx="6" class="tint"/>')
            out.append(f'<rect x="{x - bw / 2}" y="{ly - bh / 2}" width="{bw}" height="{bh}" rx="6" fill="none" class="edge" stroke-width="1.25"/>')
            out.append(text(x - bw / 2 + 8, ly + 5, f"{i + 1}", 11.5, 600, cls="acct"))
            out.append(text(x + 6, ly + 5, code, 12.5, mono=True, anchor="middle"))
            if prev is not None:
                px, ply, plane = prev
                if plane != lane:
                    out.append(path(f"M{px + bw / 2} {ply}L{x - bw / 2} {ly}", ma, cls="acc", width=1.5, dash="4 3"))
                else:
                    out.append(path(f"M{px + bw / 2} {ply}H{x - bw / 2}", m))
            prev = (x, ly, lane)
            cls = "bad" if i >= bad_from else "ink"
            out.append(text(x, vy + 4, f"{var} = {values[i]}", 12.5, 600 if i >= bad_from else 400, cls=cls, mono=True, anchor="middle"))
        out.append(text(24, vy + 30, note, 11.5, cls="quiet"))
        return out

    p += panel(70, "A. The lock itself: test and take are two separate steps (S = 1 means free)",
               [("P1", "S == 0 ?"), ("P2", "S == 0 ?"), ("P1", "S = 0"), ("P2", "S--")],
               "S", ["1", "1", "0", "-1"], 3,
               "Both saw S = 1, so both entered. Dashed arrows: a timer interrupt switched to the other process.")
    p += panel(260, "B. Inside the critical section: another process changes X in between",
               [("P1", "X := 0"), ("P2", "X := 1"), ("P1", "X++")],
               "X", ["0", "1", "2"], 2,
               "P1 expected X = 1 after its own two steps, but P2 changed X in between.")
    return svg(760, 440, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("interrupt-cycle", cycle), ("interrupt-processing", processing),
                    ("nested-interrupts", nested), ("race-condition", race)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
