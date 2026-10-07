"""Generate the SVG figures for the Fetch-Execute Cycle lecture."""

STYLE = """<style>
  .ink{fill:#1f1f1f}.quiet{fill:#6b6b66}.edge{stroke:#b5b4a8}.edgef{fill:#b5b4a8}
  .grid{stroke:#e3e2da}.acc{stroke:#2f6fd6}.accf{fill:#2f6fd6;fill-opacity:.12}
  text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
  @media (prefers-color-scheme: dark){
    .ink{fill:#e8e8e3}.quiet{fill:#a3a39c}.edge{stroke:#6f6e66}.edgef{fill:#6f6e66}
    .grid{stroke:#3a3a35}.acc{stroke:#5b93ef}.accf{fill:#5b93ef;fill-opacity:.18}
  }
</style>"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, weight=400, cls="ink", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'class="{cls}" text-anchor="{anchor}">{esc(s)}</text>')


def marker(mid):
    return (f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="edgef"/>'
            f'</marker></defs>')


def path(d, mid, start=False, end=True):
    a = f' marker-end="url(#{mid})"' if end else ""
    b = f' marker-start="url(#{mid})"' if start else ""
    return f'<path d="{d}" fill="none" class="edge" stroke-width="1.25"{a}{b}/>'


def rect(x, y, w, h, main=False):
    if main:
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="accf"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" class="acc" stroke-width="2"/>')
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" class="edge" stroke-width="1.25"/>'


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}">\n<title>{esc(title)}</title>\n{STYLE}\n{body}\n</svg>\n')


# ---------------- Instruction cycle ----------------
def cycle():
    W, H, rowA, rowB = 136, 56, 120, 240
    c1, c2, c3, cd, hw = 96, 256, 416, 600, 240
    m = "cyc"
    title = "After every instruction, the CPU checks for interrupts"
    p = [marker(m), text(24, 30, title, 15, 600)]
    p += [
        path(f"M{c1+W/2} {rowA}H{c2-W/2}", m),
        path(f"M{c2+W/2} {rowA}H{c3-W/2}", m),
        path(f"M{c3+W/2} {rowA}H{cd-64}", m),
        path(f"M{cd} {rowA-40}V64H{c1}V{rowA-H/2}", m),
        path(f"M{cd} {rowA+40}V{rowB-28}", m),
        path(f"M{cd-hw/2} {rowB}H{c1}V{rowA+H/2}", m),
    ]
    for cx, name, sub in [(c1, "Fetch", "fetch instruction"),
                          (c2, "Decode", "decode CIR"),
                          (c3, "Execute", "operate or jump")]:
        p.append(rect(cx - W/2, rowA - H/2, W, H))
        p.append(text(cx, rowA - 4, name, 13, 600, anchor="middle"))
        p.append(text(cx, rowA + 14, sub, 11.5, cls="quiet", anchor="middle"))
    pts = f"{cd-64},{rowA} {cd},{rowA-40} {cd+64},{rowA} {cd},{rowA+40}"
    p.append(f'<polygon points="{pts}" class="accf"/><polygon points="{pts}" fill="none" class="acc" stroke-width="2"/>')
    p.append(text(cd, rowA - 2, "Interrupt", 13, 600, anchor="middle"))
    p.append(text(cd, rowA + 14, "pending?", 13, 600, anchor="middle"))
    p.append(rect(cd - hw/2, rowB - 28, hw, 56))
    p.append(text(cd, rowB - 4, "Interrupt handling", 13, 600, anchor="middle"))
    p.append(text(cd, rowB + 14, "save PC, SR; PC ← handler address", 11.5, cls="quiet", anchor="middle"))
    p.append(text((c1 + cd) / 2, 56, "no: next instruction", 11.5, cls="quiet", anchor="middle"))
    p.append(text(cd + 10, rowB - 48, "yes", 11.5, cls="quiet"))
    p.append(text((c1 + cd - hw/2) / 2, rowB - 8, "the handler's instructions are fetched too", 11.5, cls="quiet", anchor="middle"))
    return svg(760, 292, title, "\n".join(p))


# ---------------- CPU architecture ----------------
def arch():
    BW, BH = 117, 72
    L1, L2, L3 = 40, 185, 330
    R1, R2, R3 = 100, 204, 308
    M0, MW = 600, 136
    c1, c2 = L1 + BW/2, L2 + BW/2
    m = "arch"
    title = "The CPU requests on the address bus and receives on the data bus"
    p = [marker(m), text(24, 30, title, 15, 600)]
    # CPU container
    p.append(rect(24, 56, 440, 340))
    p.append(text(40, 84, "CPU", 13, 600))
    # internal connectors
    p += [
        path(f"M{L2+BW} {R1+BH/2}H{L3}", m),            # PC -> MAR
        path(f"M{L3} {R3+BH/2}H{L2+BW}", m),            # MBR -> CIR
        path(f"M{c2} {R3}V{R2+BH}", m),                 # CIR -> Decoder
        path(f"M{L2} {R2+BH/2}H{L1+BW}", m),            # Decoder -> ALU
        path(f"M{L2+BW} {R2+BH/2}H{L3}", m),            # Decoder -> CU
        path(f"M{c1} {R1+BH}V{R2}", m, start=True),     # ACC <-> ALU
        path(f"M{c1} {R2+BH}V{R3}", m),                 # ALU -> SR
        path(f"M{c1} 428V{R3+BH}", m),                  # timer -> SR
    ]
    # buses
    p += [
        path(f"M{L3+BW} {R1+BH/2}H{M0}", m),
        path(f"M{L3+BW} {R2+BH/2}H{M0}", m),
        path(f"M{L3+BW} {R3+BH/2}H{M0}", m, start=True),
    ]
    for row, name, sub in [(R1, "address bus", "MAR → memory"),
                           (R2, "control bus", "CS, R/W, CLK"),
                           (R3, "data bus", "bidirectional")]:
        p.append(text(524, row + BH/2 - 8, name, 11.5, 600, anchor="middle"))
        p.append(text(524, row + BH/2 + 18, sub, 11.5, cls="quiet", anchor="middle"))
    boxes = [
        (L1, R1, False, "ACC", "accumulator,", "ALU result"),
        (L2, R1, True, "PC", "program counter,", "next address"),
        (L3, R1, True, "MAR", "memory address", "register"),
        (L1, R2, False, "ALU", "arithmetic and", "logic unit"),
        (L2, R2, False, "Decoder", "opcode →", "control signals"),
        (L3, R2, False, "CU", "control unit:", "sequencing"),
        (L1, R3, False, "SR", "status bits:", "S, Z, O (and more)"),
        (L2, R3, True, "CIR", "current", "instruction"),
        (L3, R3, True, "MBR", "memory buffer", "register"),
    ]
    for x, y, main, name, a, b in boxes:
        p.append(rect(x, y, BW, BH, main))
        p.append(text(x + 12, y + 24, name, 13, 600))
        p.append(text(x + 12, y + 44, a, 11.5, cls="quiet"))
        p.append(text(x + 12, y + 60, b, 11.5, cls="quiet"))
    p.append(text(c1 + 8, R2 + BH + 21, "flags", 11.5, cls="quiet"))
    p.append(text(c1 + 8, 414, "IRQ", 11.5, 600))
    # timer
    p.append(rect(L1, 428, BW, 56))
    p.append(text(L1 + 12, 452, "Timer", 13, 600))
    p.append(text(L1 + 12, 470, "periodic IRQ", 11.5, cls="quiet"))
    # memory
    p.append(rect(M0, 56, MW, 340))
    p.append(f'<line x1="{M0+36}" y1="96" x2="{M0+36}" y2="316" class="grid"/>')
    for y in (96, 140, 184, 228, 272, 316):
        p.append(f'<line x1="{M0}" y1="{y}" x2="{M0+MW}" y2="{y}" class="grid"/>')
    p.append(text(M0 + 16, 84, "Memory", 13, 600))
    for i, (a, d, cls) in enumerate([("0", "LD 3", "ink"), ("1", "ADD 2", "ink"), ("2", "–", "quiet"),
                                     ("3", "7 (data)", "ink"), ("…", "…", "quiet")]):
        y = 122 + 44 * i
        p.append(text(M0 + 18, y, a, 11.5, cls="quiet", anchor="middle"))
        p.append(text(M0 + 48, y, d, 13, cls=cls))
    p.append(text(M0 + 16, 346, "code and data", 11.5, cls="quiet"))
    p.append(text(M0 + 16, 362, "together", 11.5, cls="quiet"))
    p.append(text(200, 460, "Highlighted: fetch-phase registers (PC, MAR, MBR, CIR)", 11.5, cls="quiet"))
    return svg(760, 508, title, "\n".join(p))


if __name__ == "__main__":
    open("instruction-cycle.svg", "w", encoding="utf-8").write(cycle())
    open("cpu-architecture.svg", "w", encoding="utf-8").write(arch())
    print("ok")
