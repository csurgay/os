"""Generate the SVG figures for the Fetch-Execute Cycle lecture (Hungarian)."""

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


def path(d, mid, start=False, end=True, dash=None, width=1.25):
    a = f' marker-end="url(#{mid})"' if end else ""
    b = f' marker-start="url(#{mid})"' if start else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" class="edge" stroke-width="{width}"{a}{b}{da}/>'


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
    title = "A CPU minden utasítás után ellenőrzi a megszakításokat"
    p = [marker(m), text(24, 30, title, 15, 600)]
    p += [
        path(f"M{c1+W/2} {rowA}H{c2-W/2}", m),
        path(f"M{c2+W/2} {rowA}H{c3-W/2}", m),
        path(f"M{c3+W/2} {rowA}H{cd-64}", m),
        path(f"M{cd} {rowA-40}V64H{c1}V{rowA-H/2}", m),
        path(f"M{cd} {rowA+40}V{rowB-28}", m),
        path(f"M{cd-hw/2} {rowB}H{c1}V{rowA+H/2}", m),
    ]
    for cx, name, sub in [(c1, "Lehívás", "utasítás lehívása"),
                          (c2, "Dekódolás", "a CIR dekódolása"),
                          (c3, "Végrehajtás", "művelet vagy ugrás")]:
        p.append(rect(cx - W/2, rowA - H/2, W, H))
        p.append(text(cx, rowA - 4, name, 13, 600, anchor="middle"))
        p.append(text(cx, rowA + 14, sub, 11.5, cls="quiet", anchor="middle"))
    pts = f"{cd-64},{rowA} {cd},{rowA-40} {cd+64},{rowA} {cd},{rowA+40}"
    p.append(f'<polygon points="{pts}" class="accf"/><polygon points="{pts}" fill="none" class="acc" stroke-width="2"/>')
    p.append(text(cd, rowA - 2, "Van függő", 13, 600, anchor="middle"))
    p.append(text(cd, rowA + 14, "megszakítás?", 13, 600, anchor="middle"))
    p.append(rect(cd - hw/2, rowB - 28, hw, 56))
    p.append(text(cd, rowB - 4, "Megszakításkezelés", 13, 600, anchor="middle"))
    p.append(text(cd, rowB + 14, "PC, SR mentése; PC ← kezelő címe", 11.5, cls="quiet", anchor="middle"))
    p.append(text((c1 + cd) / 2, 56, "nem: következő utasítás", 11.5, cls="quiet", anchor="middle"))
    p.append(text(cd + 10, rowB - 48, "igen", 11.5, cls="quiet"))
    p.append(text((c1 + cd - hw/2) / 2, rowB - 8, "a kezelő utasításai is lehívódnak", 11.5, cls="quiet", anchor="middle"))
    return svg(760, 292, title, "\n".join(p))


# ---------------- CPU architecture ----------------
def arch():
    BW, BH = 117, 72
    L1, L2, L3 = 40, 185, 330
    R1, R2, R3 = 100, 204, 308
    M0, MW = 600, 136
    c1, c2 = L1 + BW/2, L2 + BW/2
    m = "arch"
    title = "A CPU a címsínen kér, és az adatsínen kap"
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
    for row, name, sub in [(R1, "címsín", "MAR → memória"),
                           (R2, "vezérlősín", "CS, R/W, CLK"),
                           (R3, "adatsín", "kétirányú")]:
        p.append(text(524, row + BH/2 - 8, name, 11.5, 600, anchor="middle"))
        p.append(text(524, row + BH/2 + 18, sub, 11.5, cls="quiet", anchor="middle"))
    boxes = [
        (L1, R1, False, "ACC", "akkumulátor,", "ALU-eredmény"),
        (L2, R1, True, "PC", "utasításszámláló,", "következő cím"),
        (L3, R1, True, "MAR", "memóriacím-", "regiszter"),
        (L1, R2, False, "ALU", "aritmetikai-", "logikai egység"),
        (L2, R2, False, "Dekóder", "műveleti kód →", "vezérlőjelek"),
        (L3, R2, False, "CU", "vezérlőegység:", "sorrendvezérlés"),
        (L1, R3, False, "SR", "állapotbitek:", "S, Z, O (és mások)"),
        (L2, R3, True, "CIR", "utasítás-", "regiszter"),
        (L3, R3, True, "MBR", "memória-", "pufferregiszter"),
    ]
    for x, y, main, name, a, b in boxes:
        p.append(rect(x, y, BW, BH, main))
        p.append(text(x + 12, y + 24, name, 13, 600))
        p.append(text(x + 12, y + 44, a, 11.5, cls="quiet"))
        p.append(text(x + 12, y + 60, b, 11.5, cls="quiet"))
    p.append(text(c1 + 8, R2 + BH + 21, "jelzőbitek", 11.5, cls="quiet"))
    p.append(text(c1 + 8, 414, "IRQ", 11.5, 600))
    # timer
    p.append(rect(L1, 428, BW, 56))
    p.append(text(L1 + 12, 452, "Időzítő", 13, 600))
    p.append(text(L1 + 12, 470, "periodikus IRQ", 11.5, cls="quiet"))
    # memory
    p.append(rect(M0, 56, MW, 340))
    p.append(f'<line x1="{M0+36}" y1="96" x2="{M0+36}" y2="316" class="grid"/>')
    for y in (96, 140, 184, 228, 272, 316):
        p.append(f'<line x1="{M0}" y1="{y}" x2="{M0+MW}" y2="{y}" class="grid"/>')
    p.append(text(M0 + 16, 84, "Memória", 13, 600))
    for i, (a, d, cls) in enumerate([("0", "LD 3", "ink"), ("1", "ADD 2", "ink"), ("2", "–", "quiet"),
                                     ("3", "7 (adat)", "ink"), ("…", "…", "quiet")]):
        y = 122 + 44 * i
        p.append(text(M0 + 18, y, a, 11.5, cls="quiet", anchor="middle"))
        p.append(text(M0 + 48, y, d, 13, cls=cls))
    p.append(text(M0 + 16, 346, "kód és adat", 11.5, cls="quiet"))
    p.append(text(M0 + 16, 362, "együtt", 11.5, cls="quiet"))
    p.append(text(200, 460, "Kiemelve: a lehívási fázis regiszterei (PC, MAR, MBR, CIR)", 11.5, cls="quiet"))
    return svg(760, 508, title, "\n".join(p))


# ---------------- System bus with separate memory and I/O control lines ----------------
def system_bus():
    m = "sb"
    title = "Egy egyszerű rendszersín cím-, adat- és vezérlővonalai"
    p = [marker(m), text(24, 30, title, 15, 600)]
    top, bot = 190, 254
    boxes = [(40, 160, "CPU", "hajtja a címsínt"),
             (300, 160, "Memória", "válaszol: MR, MW"),
             (560, 160, "I/O-eszköz", "válaszol: IOR, IOW")]
    # control lines (dashed), nested so that they never cross
    ctrl = [  # x on CPU, x on target, height, label, from CPU?
        (140, 340, 166, "MR  memóriaolvasás", True),
        (120, 380, 142, "MW  memóriaírás", True),
        (100, 590, 118, "IOR  I/O-olvasás", True),
        (80, 630, 94, "IOW  I/O-írás", True),
        (60, 670, 70, "IRQ  megszakításkérés", False),
    ]
    for xc, xt, y, label, out in ctrl:
        if out:
            p.append(path(f"M{xc} {top}V{y}H{xt}V{top}", m, dash="5 4"))
        else:
            p.append(path(f"M{xt} {top}V{y}H{xc}V{top}", m, dash="5 4"))
        p.append(text(232, y - 5, label, 11.5, 600 if not out else 400))
    p.append(text(684, 110, "vezérlő-", 11.5, cls="quiet"))
    p.append(text(684, 126, "vonalak", 11.5, cls="quiet"))
    for x, w, name, sub in boxes:
        p.append(rect(x, top, w, bot - top, main=(name == "CPU")))
        p.append(text(x + w / 2, top + 26, name, 13, 600, anchor="middle"))
        p.append(text(x + w / 2, top + 46, sub, 11.5, cls="quiet", anchor="middle"))
    # address bus: CPU -> memory, I/O
    ya, yd = 292, 326
    p.append(path(f"M90 {bot}V{ya}H630", m, end=False, width=2.5))
    p.append(path(f"M350 {ya}V{bot}", m))
    p.append(path(f"M610 {ya}V{bot}", m))
    # data bus: both directions
    p.append(path(f"M150 {yd}H680", m, end=False, width=2.5))
    for x in (150, 410, 670):
        p.append(path(f"M{x} {yd}V{bot}", m, start=True, end=True))
    p.append(text(36, ya + 4, "cím", 11.5, 600))
    p.append(text(36, yd + 4, "adat", 11.5, 600))
    p.append(text(638, ya + 4, "CPU → memória, I/O", 11.5, cls="quiet"))
    p.append(text(688, yd + 4, "kétirányú", 11.5, cls="quiet"))
    p.append(text(24, 370, "Portleképezett I/O: az IOR/IOW jelzi az eszköznek, hogy a cím portszám, nem memóriarekesz.", 11.5, cls="quiet"))
    p.append(text(24, 388, "Memórialeképezett I/O: az eszköz a saját címtartományában válaszol az MR/MW jelre, mint a memória.", 11.5, cls="quiet"))
    return svg(760, 404, title, "\n".join(p))


# ---------------- Bus hierarchy: then and now ----------------
def hierarchy():
    m = "bh"
    title = "Egy közös síntől a sínek és kapcsolatok hierarchiájáig"
    p = [marker(m), text(24, 30, title, 15, 600)]

    def box(x, y, w, h, name, sub=None, main=False):
        p.append(rect(x, y, w, h, main))
        if sub:
            p.append(text(x + w / 2, y + h / 2 - 3, name, 13, 600, anchor="middle"))
            p.append(text(x + w / 2, y + h / 2 + 14, sub, 11.5, cls="quiet", anchor="middle"))
        else:
            p.append(text(x + w / 2, y + h / 2 + 5, name, 13, 600, anchor="middle"))

    def line(d, w=1.25):
        p.append(path(d, m, end=False, width=w))

    # ---- Panel A: late 1990s ----
    p.append(text(24, 64, "A   Az 1990-es évek vége: hidakkal összekötött sínek", 13, 600, cls="quiet"))
    y1 = 84
    box(40, y1, 110, 44, "L2", "gyorsítótár")
    box(230, y1, 110, 44, "CPU", main=True)
    box(420, y1, 120, 44, "PCI-híd")
    box(620, y1, 110, 44, "Központi", "memória")
    line(f"M150 {y1+22}H230", 2.5)
    line(f"M340 {y1+22}H420", 2.5)
    line(f"M540 {y1+22}H620", 2.5)
    p.append(text(190, y1 + 14, "cache-sín", 11, cls="quiet", anchor="middle"))
    p.append(text(380, y1 + 14, "helyi sín", 11, cls="quiet", anchor="middle"))
    p.append(text(580, y1 + 14, "memóriasín", 11, cls="quiet", anchor="middle"))
    ypci = 170
    line(f"M480 {y1+44}V{ypci}")
    line(f"M40 {ypci}H730", 2.5)
    p.append(text(730, ypci - 8, "PCI sín (33 MHz, közös)", 11.5, 600, anchor="end"))
    yd = 196
    for x, w, name in [(40, 90, "SCSI"), (145, 90, "USB"), (250, 100, "Hálózat"), (365, 100, "Grafika")]:
        line(f"M{x + w/2} {ypci}V{yd}")
        box(x, yd, w, 40, name)
    box(480, yd, 110, 40, "ISA-híd")
    line(f"M535 {ypci}V{yd}")
    box(630, yd, 100, 40, "IDE-lemezek")
    line(f"M590 {yd+20}H630")
    yisa = 284
    line(f"M535 {yd+40}V{yisa}")
    line(f"M40 {yisa}H730", 2.5)
    p.append(text(730, yisa - 8, "ISA sín (8 MHz, közös)", 11.5, 600, anchor="end"))
    for x, w, name in [(40, 100, "Modem"), (155, 110, "Hangkártya"), (280, 100, "Nyomtató")]:
        line(f"M{x + w/2} {yisa}V{yisa+26}")
        box(x, yisa + 26, w, 40, name)
    p.append(text(730, yisa + 44, "gyors a CPU közelében, lassú távolabb", 11.5, cls="quiet", anchor="end"))
    p.append(f'<line x1="24" y1="378" x2="736" y2="378" class="grid"/>')

    # ---- Panel B: today ----
    p.append(text(24, 408, "B   Ma (egyszerűsítve): pont–pont kapcsolatok, vezérlők a CPU-ban", 13, 600, cls="quiet"))
    py0, py1 = 424, 524
    p.append(rect(40, py0, 480, py1 - py0))
    p.append(text(52, py0 + 20, "CPU-tok", 11.5, 600, cls="quiet"))
    iy = 456
    box(56, iy, 140, 52, "PCIe", "root complex")
    box(212, iy, 140, 52, "Magok", "gyorsítótárakkal", main=True)
    box(368, iy, 140, 52, "Memória-", "vezérlő")
    box(600, iy, 130, 52, "DRAM", "DDR-csatornák")
    line(f"M508 {iy+26}H600", 2.5)
    line(f"M196 {iy+26}H212")
    line(f"M352 {iy+26}H368")
    ydev = 572
    line(f"M100 {iy+52}V{ydev}", 2.5)
    box(30, ydev, 140, 44, "Grafikus kártya")
    line(f"M160 {iy+52}V548H260V{ydev}", 2.5)
    box(190, ydev, 140, 44, "NVMe SSD")
    p.append(text(208, 544, "PCIe-sávok", 11, cls="quiet"))
    # chipset
    line(f"M470 {py1}V{ydev}", 2.5)
    p.append(text(480, 552, "DMI-kapcsolat", 11, cls="quiet"))
    box(400, ydev, 140, 44, "Chipset (PCH)", main=False)
    yb = 660
    line(f"M470 {ydev+44}V640")
    devs = [(250, "USB"), (350, "SATA"), (450, "Hálózat"), (550, "Hang"), (650, "PCIe-foglalatok")]
    line(f"M{devs[0][0]+40} 640H{devs[-1][0]+40}")
    for x, name in devs:
        line(f"M{x+40} 640V{yb}")
        if name == "PCIe-foglalatok":
            box(x, yb, 90, 40, "PCIe-", "foglalatok")
        else:
            box(x, yb, 80, 40, name)
    p.append(text(24, 742, "Minden PCIe-kapcsolat pont–pont: az eszközök már nem osztoznak egy sínen, és nem várnak egymásra.", 11.5, cls="quiet"))
    p.append(text(24, 760, "A lassú eszközök a chipset egyetlen CPU-kapcsolatán osztoznak; a gyorsak saját sávokat kapnak.", 11.5, cls="quiet"))
    return svg(760, 776, title, "\n".join(p))


if __name__ == "__main__":
    open("instruction-cycle.svg", "w", encoding="utf-8").write(cycle())
    open("cpu-architecture.svg", "w", encoding="utf-8").write(arch())
    open("system-bus.svg", "w", encoding="utf-8").write(system_bus())
    open("bus-hierarchy.svg", "w", encoding="utf-8").write(hierarchy())
    print("ok")
