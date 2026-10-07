"""Generate the SVG figures for the Interrupts lecture.

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
    c1, c2, c3, cd, hw = 96, 256, 416, 600, 250
    m = "ic"
    title = "A megszakítást a processzor csak két utasítás között fogadja el"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # atomic brace over Fetch..Execute
    bx0, bx1, by = c1 - W / 2, c3 + W / 2, 98
    p.append(path(f"M{bx0} {by + 10}V{by}H{bx1}V{by + 10}", m, end=False, cls="acc", width=2))
    p.append(text((bx0 + bx1) / 2, by - 10, "atomi: egy utasítás, sosem szakad meg félúton", 11.5, 600, cls="acct", anchor="middle"))
    p += [
        path(f"M{c1 + W / 2} {rowA}H{c2 - W / 2}", m),
        path(f"M{c2 + W / 2} {rowA}H{c3 - W / 2}", m),
        path(f"M{c3 + W / 2} {rowA}H{cd - 64}", m),
        path(f"M{cd - hw / 2} {rowB}H{c1}V{rowA + H / 2}", m),
        path(f"M{cd} {rowA + 40}V{rowB - 28}", m),
        path(f"M{cd + 64} {rowA}H{736}V{rowB + 52}H{14}V{rowA}H{c1 - W / 2}", m),
    ]
    for cx, name, sub in [(c1, "Lehívás", "utasítás lehívása"),
                          (c2, "Dekódolás", "a CIR dekódolása"),
                          (c3, "Végrehajtás", "művelet vagy ugrás")]:
        p.append(rect(cx - W / 2, rowA - H / 2, W, H))
        p.append(text(cx, rowA - 4, name, 13, 600, anchor="middle"))
        p.append(text(cx, rowA + 14, sub, 11.5, cls="quiet", anchor="middle"))
    pts = f"{cd - 64},{rowA} {cd},{rowA - 40} {cd + 64},{rowA} {cd},{rowA + 40}"
    p.append(f'<polygon points="{pts}" class="accf"/><polygon points="{pts}" fill="none" class="acc" stroke-width="2"/>')
    p.append(text(cd, rowA - 2, "Van függő", 13, 600, anchor="middle"))
    p.append(text(cd, rowA + 14, "megszakítás?", 13, 600, anchor="middle"))
    p.append(rect(cd - hw / 2, rowB - 28, hw, 56))
    p.append(text(cd, rowB - 4, "Megszakításkezelő", 13, 600, anchor="middle"))
    p.append(text(cd, rowB + 14, "a PC már a következő utasításra mutat", 11.5, cls="quiet", anchor="middle"))
    p.append(text(cd + 10, rowA + 64, "igen", 11.5, cls="quiet"))
    p.append(text(728, rowA - 8, "nem", 11.5, cls="quiet", anchor="end"))
    p.append(text((c1 + cd - hw / 2) / 2, rowB - 8, "a kezelő ugyanúgy lehívódik, mint bármely más kód", 11.5, cls="quiet", anchor="middle"))
    p.append(text(400, rowB + 70, "nincs megszakítás: azonnal jön a következő utasítás", 11.5, cls="quiet", anchor="middle"))
    return svg(760, 360, title, "\n".join(p))


# ---------------- 2. Interrupt processing: hardware then software ----------------
def processing():
    m = "ip"
    title = "A hardver a minimumot menti, a többit a kezelő"
    xL, xR, w, h, y0, step = 40, 420, 300, 56, 104, 76
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(xL, 76, "Hardver (automatikus, minden megszakításnál)", 13, 600))
    p.append(text(xR, 76, "Szoftver (megszakításkezelő, az OS-ben)", 13, 600))
    hw = [
        ("1  Az eszköz megszakítást kér", "pl. kész az átvitel, lejárt az időzítő", False),
        ("2  A CPU befejezi az utasítást", "az utasításciklus atomi", False),
        ("3  A CPU nyugtázza a kérést", "később a kezelő törli (EOI)", False),
        ("4  A CPU menti a PC-t és a PSW-t", "a verembe kerülnek (LIFO)", True),
        ("5  A CPU betölti az új PC-t", "vektortábla → a kezelő címe", False),
    ]
    sw = [
        ("6  A többi regiszter mentése", "a folyamatállapot többi része", False),
        ("7  A kezelőrutin futtatása", "kiszolgálja az eszközt, röviden", False),
        ("8  A többi regiszter visszaállítása", "fordított sorrendben (LIFO)", False),
        ("9  A PC és a PSW visszaállítása", "visszatérés: a program folytatódik", True),
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
    p.append(text(xR + w / 2, y9 + 58, "vissza a megszakított programba,", 11.5, cls="quiet", anchor="middle"))
    p.append(text(xR + w / 2, y9 + 74, "a mentett PC-nél", 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, 504, "Kiemelve: az az egy pár, amelyet maga a hardver ment, és a visszatérő utasítás visszaállít", 11.5, cls="quiet"))
    return svg(760, 524, title, "\n".join(p))


# ---------------- 3. Nested interrupts ----------------
def nested():
    m, ma = "ni", "nia"
    title = "Az egymásba ágyazott megszakítások veremként, fordított sorrendben térnek vissza"
    cols = [(24, "Felhasználói program"), (304, "Megszakításkezelő"), (584, "Nagy prioritású kezelő")]
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
    p.append(text(304 + 26, ly(0) - 4, "regiszterek mentése", 11.5, cls="acct"))
    p.append(text(304 + 26, ly(10) + 16, "visszaállít, visszatér", 11.5, cls="acct"))
    # arrows
    p.append(path(f"M{24 + cw} {ly(2)}C{230} {ly(2)} {250} {ly(0)} {304} {ly(0)}", ma, cls="acc", width=1.5))
    p.append(path(f"M{304} {ly(10)}C{240} {ly(10)} {230} {ly(3)} {24 + cw} {ly(3)}", m))
    p.append(path(f"M{304 + cw} {ly(5)}C{510} {ly(5)} {530} {ly(0)} {584} {ly(0)}", ma, cls="acc", width=1.5))
    p.append(path(f"M{584} {ly(9)}C{520} {ly(9)} {510} {ly(6)} {304 + cw} {ly(6)}", m))
    p.append(text(240, ly(0) - 14, "megszakítás", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(240, top + n * dy + 30, "vissza a 3-as címre", 11.5, cls="quiet", anchor="middle"))
    p.append(text(520, ly(0) - 28, "nagyobb prioritású", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(520, ly(0) - 14, "megszakítás", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(520, top + n * dy + 30, "vissza a kezelőbe", 11.5, cls="quiet", anchor="middle"))
    # stack panel
    sy = top + n * dy + 72
    p.append(text(24, sy, "A verem, miközben a nagy prioritású kezelő fut", 13, 600))
    sx, sw_, sh = 24, 290, 30
    p.append(rect(sx, sy + 14, sw_, sh, main=True))
    p.append(text(sx + 12, sy + 34, "az első kezelő PC-je + PSW-je", 12.5))
    p.append(rect(sx, sy + 14 + sh + 6, sw_, sh))
    p.append(text(sx + 12, sy + 34 + sh + 6, "PC = 3 + a felhasználói program PSW-je", 12.5))
    p.append(text(sx + sw_ + 16, sy + 34, "← teteje: elsőként kerül le", 11.5, cls="quiet"))
    p.append(text(sx + sw_ + 16, sy + 34 + sh + 6, "← utolsóként kerül le", 11.5, cls="quiet"))
    p.append(text(330, sy + 112, "Egy közben érkező kisebb prioritású kérés megvárja, amíg a nagyobb prioritású végez.", 11.5, cls="quiet", anchor="middle"))
    return svg(760, sy + 134, title, "\n".join(p))


# ---------------- 4. Race condition, two panels ----------------
def race():
    m, ma = "rc", "rca"
    title = "Egy rosszkor érkező megszakítás két folyamatot enged be a kritikus szakaszba"
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

    p += panel(70, "A. Maga a zár: a tesztelés és a megszerzés két külön lépés (S = 1: szabad)",
               [("P1", "S == 0 ?"), ("P2", "S == 0 ?"), ("P1", "S = 0"), ("P2", "S = 0")],
               "S", ["1", "1", "0", "0"], 3,
               "Mindkettő S = 1-et látott, így mindkettő belépett. Szaggatott nyíl: időzítő-megszakítás, váltás a másikra.")
    p += panel(260, "B. A kritikus szakaszon belül: egy másik folyamat közben megváltoztatja X-et",
               [("P1", "X := 0"), ("P2", "X := 1"), ("P1", "X++")],
               "X", ["0", "1", "2"], 2,
               "P1 a saját két lépése után X = 1-et várt, de P2 közben megváltoztatta X-et.")
    return svg(760, 440, title, "\n".join(p))


# ---------------- 5. CPU time spent on one block transfer ----------------
def io_timeline():
    title = "Ugyanaz a 4 KiB-os átvitel a CPU idejének 100%-át, 20%-át, 0,14%-át vagy 0,007%-át köti le"
    x0, x1 = 236, 640                       # time axis, 0 .. 40.96 ms
    total = 40960.0
    X = lambda us: x0 + (x1 - x0) * us / total
    rows = [
        ("Programozott I/O", "az állapotregiszter lekérdezése", "100%"),
        ("Bájtonkénti megszakítás", "4096 megszakítás × 2 µs", "20%"),
        ("Pufferenkénti megszakítás", "8 × (2 µs + 512 B másolása)", "0,14%"),
        ("DMA", "beállítás + 1 megszakítás", "0,007%"),
    ]
    y0, step, bh = 92, 60, 22
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Az átvitelre fordított CPU-idő (kék) az eszköznek szükséges 41 ms alatt. Feltételezett értékek, lásd a táblázatot.", 11.5, cls="quiet")]
    for i, (name, sub, pct) in enumerate(rows):
        y = y0 + i * step
        p.append(text(24, y + 8, name, 13, 600))
        p.append(text(24, y + 24, sub, 11.5, cls="quiet"))
        p.append(f'<rect x="{x0}" y="{y - 4}" width="{x1 - x0}" height="{bh}" rx="3" class="tint"/>')
        p.append(f'<rect x="{x0}" y="{y - 4}" width="{x1 - x0}" height="{bh}" rx="3" fill="none" class="edge" stroke-width="1"/>')
        if i == 0:
            p.append(f'<rect x="{x0}" y="{y - 4}" width="{x1 - x0}" height="{bh}" rx="3" class="acct"/>')
        elif i == 1:
            # 20% duty: one 2 µs slice in every 10 µs; drawn as an even stripe pattern
            for k in range(0, 110):
                xs = X(k * total / 110)
                p.append(f'<rect x="{xs:.2f}" y="{y - 4}" width="{(x1 - x0) / 110 * 0.2:.2f}" height="{bh}" class="acct"/>')
        elif i == 2:
            for k in range(1, 9):
                xs = X(k * 512 * 10.0) - 1.2
                p.append(f'<rect x="{xs:.2f}" y="{y - 4}" width="1.6" height="{bh}" class="acct"/>')
        else:
            p.append(f'<rect x="{x0:.2f}" y="{y - 4}" width="1.6" height="{bh}" class="acct"/>')
            p.append(f'<rect x="{x1 - 1.6:.2f}" y="{y - 4}" width="1.6" height="{bh}" class="acct"/>')
        p.append(text(x1 + 16, y + 12, pct, 13, 600))
    ya = y0 + 4 * step - 18
    p.append(f'<line x1="{x0}" y1="{ya}" x2="{x1}" y2="{ya}" class="edge" stroke-width="1.25"/>')
    for ms in range(0, 41, 10):
        xs = X(ms * 1000)
        p.append(f'<line x1="{xs:.1f}" y1="{ya}" x2="{xs:.1f}" y2="{ya + 5}" class="edge" stroke-width="1.25"/>')
        p.append(text(xs, ya + 19, f"{ms} ms", 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, ya + 46, "A pufferes megszakítások és a DMA vékony vonalai a méretarányosnál szélesebbek, különben nem látszanának.", 11.5, cls="quiet"))
    return svg(760, ya + 66, title, "\n".join(p))


# ---------------- 6. Interrupt latency ----------------
def latency():
    m = "lat"
    title = "A megszakítási késleltetés több várakozásból adódik össze"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    segs = [
        ("az utasítás", "befejezése", 120, False),
        ("a megszakítások", "letiltva (maszkolva)", 172, True),
        ("hardveres belépés:", "PC, PSW mentése", 128, False),
        ("a kezelő menti", "a regisztereket", 112, False),
        ("sürgős munka", "(felső fél)", 112, False),
    ]
    x, y, h = 40, 96, 52
    xs = []
    for a, b, w, acc in segs:
        p.append(rect(x, y, w, h, main=acc, tint=not acc))
        p.append(text(x + 10, y + 22, a, 11.5, 600))
        p.append(text(x + 10, y + 38, b, 11.5, cls="quiet"))
        xs.append((x, w))
        x += w + 12
    # device signal arrow
    p.append(path(f"M40 72V{y - 4}", m))
    p.append(text(48, 72, "az eszköz IRQ-t küld", 11.5, 600))
    # brace for latency (first four)
    lx0 = 40
    lx1 = xs[3][0] + xs[3][1]
    yb = y + h + 18
    p.append(f'<path d="M{lx0} {yb - 8}V{yb}H{lx1}V{yb - 8}" fill="none" class="acc" stroke-width="2"/>')
    p.append(text((lx0 + lx1) / 2, yb + 20, "megszakítási késleltetés: a kéréstől a kezelő első hasznos utasításáig", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(24, yb + 50, "Kiemelve: általában ez a leghosszabb és legkevésbé kiszámítható rész.", 11.5, cls="quiet"))
    p.append(text(24, yb + 66, "A késleltetést az tartja alacsonyan, ha a megszakítások csak rövid időre vannak letiltva.", 11.5, cls="quiet"))
    return svg(760, yb + 86, title, "\n".join(p))


# ---------------- 7. Interrupt controller ----------------
def controller():
    m = "ctl"
    title = "Az eszközök a megszakításvezérlőnek jeleznek, a vezérlő megszakít egy CPU-magot"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    devs = [("Lemez", 80), ("Hálózati kártya", 150), ("Billentyűzet", 220), ("Időzítőchip", 290)]
    for name, y in devs:
        p.append(rect(24, y - 22, 150, 44, tint=True))
        p.append(text(40, y + 5, name, 13, 600))
        p.append(path(f"M174 {y}H{300}", m))
    p.append(text(237, 66, "IRQ-vonalak", 11.5, cls="quiet", anchor="middle"))
    # controller
    p.append(rect(300, 56, 190, 256, main=True))
    p.append(text(316, 84, "Megszakításvezérlő", 13, 600))
    p.append(text(316, 104, "(PIC, PC-ken I/O APIC)", 11.5, cls="quiet"))
    for i, t in enumerate(["• bemenet eszközönként", "• prioritás, maszkolás", "• megadja a vektorszámot", "• kiválasztja a magot", "• megvárja a kezelő", "   EOI-üzenetét"]):
        p.append(text(316, 136 + i * 22, t, 12.5))
    # cores
    for i, y in enumerate([110, 250]):
        p.append(rect(600, y - 40, 136, 80))
        p.append(text(616, y - 12, f"{i}. CPU-mag", 13, 600))
        p.append(text(616, y + 8, "helyi APIC,", 11.5, cls="quiet"))
        p.append(text(616, y + 24, "saját időzítő", 11.5, cls="quiet"))
        p.append(path(f"M490 {y}H600", m))
    p.append(text(545, 86, "megszakítás +", 11.5, cls="quiet", anchor="middle"))
    p.append(text(545, 102, "vektorszám", 11.5, cls="quiet", anchor="middle"))
    p.append(path(f"M668 150V210", m, start=True))
    p.append(text(676, 184, "IPI", 11.5, cls="quiet"))
    p.append(text(24, 346, "A modern PCI Express eszközök megkerülhetik a vezetékeket: MSI esetén ehelyett egy rövid üzenetet írnak", 11.5, cls="quiet"))
    p.append(text(24, 362, "egy speciális memóriacímre. Ezek a /proc/interrupts PCI-MSIX sorai.", 11.5, cls="quiet"))
    return svg(760, 384, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("interrupt-cycle", cycle), ("interrupt-processing", processing),
                    ("nested-interrupts", nested), ("race-condition", race),
                    ("io-cpu-time", io_timeline), ("interrupt-latency", latency),
                    ("interrupt-controller", controller)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
