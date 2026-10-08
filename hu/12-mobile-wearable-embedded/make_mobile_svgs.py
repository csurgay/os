"""Generate the SVG figures for the Mobile, Wearable and Embedded Operating Systems lecture.

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
The energy and scheduling figures import energy.py and rtsim.py, so they show exactly what those programs compute.
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



def boxt(x, y, w, h, lines, kind="tint", size=12, weight=400, rx=6, cls="ink"):
    """A box with one or more centred lines of text."""
    out = [rect(x, y, w, h, kind, rx=rx)]
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * (size + 3) / 2 + size * 0.36
    for i, s in enumerate(lines):
        out.append(text(x + w / 2, y0 + i * (size + 3), s, size, weight if i == 0 else 400,
                        cls if i == 0 else "quiet", anchor="middle"))
    return out



def bar(x, y, w, h, cls="acct", op=1.0):
    """A solid filled rectangle (bars of charts, segments of time lines)."""
    o = f' fill-opacity="{op}"' if op < 1 else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" class="{cls}"{o}/>'


def line(x1, y1, x2, y2, cls="edge", width=1.25, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" stroke-width="{width}"{da}/>'


# ---------------- 1. Design goals of five device classes ----------------
def design_goals():
    title = "A szerverteremtől a szenzorig: ugyanazok az OS-ötletek, más prioritások"
    p = [text(24, 30, title, 15, 600)]
    cols = [("Szerver", "acc"), ("Asztali gép, laptop", "plain"), ("Telefon", "c2"), ("Óra", "c2"), ("Mikrovezérlő", "plain")]
    rows = [
        ("Teljesítménykeret", ["több száz W", "10–100 W", "1–5 W tartósan", "tíz–száz mW", "alva µW, ébren mW"]),
        ("Memória", ["száz GiB-tól TiB-ig", "8–64 GiB", "4–16 GiB", "0,5–2 GiB", "KiB-tól pár MiB-ig"]),
        ("Energiaforrás", ["hálózat, redundáns", "hálózat vagy órák", "akkumulátor, egy nap", "akkumulátor, 1–3 nap", "akkumulátor, évekig"]),
        ("Fő cél", ["throughput, uptime", "válaszkészség", "feladatonkénti energia", "mindig ébren, olcsón", "határidők, µW alvás"]),
        ("Ki vár?", ["sok távoli felhasználó", "egy felhasználó", "egy felhasználó, úton", "egy pillantás az órára", "egy fizikai folyamat"]),
        ("Jellemző OS", ["Linux, Windows Server", "Windows, macOS, Linux", "Android, iOS", "Wear OS, watchOS, RTOS", "FreeRTOS, Zephyr"]),
    ]
    x0, lw, cw, ch = 24, 112, 158, 38
    y0 = 56
    for j, (name, kind) in enumerate(cols):
        x = x0 + lw + j * cw
        p += boxt(x + 3, y0, cw - 6, 34, [name], kind, 12.5, 600)
    for i, (label, vals) in enumerate(rows):
        y = y0 + 44 + i * ch
        p.append(text(x0, y + 23, label, 12, 600))
        for j, v in enumerate(vals):
            x = x0 + lw + j * cw
            p.append(rect(x + 3, y + 3, cw - 6, ch - 6, "tint", rx=4))
            p.append(text(x + cw / 2, y + 23, v, 11.5, anchor="middle"))
    ya = y0 + 44 + len(rows) * ch + 22
    m = "dg"
    p.insert(0, f"<defs>{marker(m, 'acct')}</defs>")
    p.append(path(f"M{x0 + lw + 10} {ya}H{x0 + lw + 5 * cw - 10}", m, cls="acc", width=2))
    p.append(text(x0 + lw + 10, ya + 20, "kevesebb energia és memória, több határidő; az OS-nek energiát, hőt, rádiókat és szenzorokat is kezelnie kell", 11.5, cls="quiet"))
    p.append(text(x0, ya + 44, "Tipikus 2026-os eszközök nagyságrendjei, nem határok: minden osztályban vannak sokkal kisebb és sokkal nagyobb eszközök is.", 11.5, cls="quiet"))
    return svg(x0 + lw + 5 * cw + 20, ya + 62, title, "\n".join(p))


# ---------------- 2. The Android stack ----------------
def android_stack():
    m, ma = "as", "asa"
    title = "Az Android rétegei: sandboxolt alkalmazások egy Linux-kernel fölött, köztük a Binder"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    L, W = 24, 560
    # apps
    p.append(text(L, 60, "Alkalmazások: mindegyiknek egy folyamat és egy Linux-UID, SELinux-domain: untrusted_app", 12, 600))
    apps = [("Maps", "u0_a123"), ("Kamera", "u0_a87"), ("Launcher", "u0_a64"), ("A te appod", "u0_a250")]
    for i, (n, u) in enumerate(apps):
        p += boxt(L + i * 142, 70, 132, 46, [n, u], "c2", 12, 600)
    # framework
    p += boxt(L, 130, W, 46, ["Java/Kotlin API-keretrendszer", "ActivityManager, PackageManager, WindowManager … a system_server folyamatban"], "acc", 12.5, 600)
    # runtime + native
    p += boxt(L, 190, 272, 52, ["Android Runtime (ART)", "DEX-bájtkód, AOT/JIT, szemétgyűjtő"], "tint", 12.5, 600)
    p += boxt(L + 288, 190, 272, 52, ["Natív könyvtárak és daemonok", "Bionic libc, média, SQLite; lmkd, surfaceflinger"], "tint", 12.5, 600)
    # treble line
    p.append(line(L - 6, 258, L + W + 6, 258, "acc", 1.5, "6 4"))
    p.append(text(L + W + 50, 254, "fölötte: system partíció", 11, 600, cls="acct"))
    p.append(text(L + W + 50, 270, "HAL-ok: vendor partíció", 11, 600, cls="acct"))
    p.append(text(L + W + 50, 286, "kernel: boot partíció", 11, 600, cls="acct"))
    p.append(text(L + W + 50, 302, "(a szaggatott vonal: Treble)", 11, cls="quiet"))
    p += boxt(L, 268, W, 46, ["Hardverabsztrakciós réteg (HAL)", "kamera, hang, szenzorok, rádió … külön folyamatokként, stabil AIDL-interfészekkel"], "tint", 12.5, 600)
    # kernel
    p.append(rect(L, 328, W, 76, "acc", rx=8))
    p.append(text(L + 12, 348, "Linux-kernel: Generic Kernel Image (GKI) + vendor modulok", 12.5, 600))
    ks = ["vendor driverek", "f2fs, dm-verity", "PSI, cgroupok", "SELinux, seccomp", "Binder-driver"]
    for i, k in enumerate(ks):
        p += boxt(L + 10 + i * 109, 358, 101, 36, [k], "acc" if i == 4 else "plain", 10.5, 600 if i == 4 else 400)
    p += boxt(L, 414, W, 30, ["hardver: SoC big és little magokkal, GPU, NPU, modem, szenzorok"], "plain", 12)
    # Binder path in a corridor right of the stack: app -> driver -> system_server
    bx = L + 10 + 4 * 109 + 101
    p.append(path(f"M{L + 4 * 142 - 10} 100H{L + W + 14}V368H{bx + 4}", ma, cls="acc", width=1.75))
    p.append(path(f"M{bx} 384H{L + W + 26}V153H{L + W + 4}", ma, cls="acc", width=1.75))
    # zygote on the right
    zx = L + W + 50
    p += boxt(zx, 130, 170, 52, ["Zygote", "ART és osztályok előtöltve"], "c2", 12.5, 600)
    p.append(path(f"M{zx + 85} 130V86H{L + 4 * 142 - 6}", m))
    p.append(text(zx + 85, 76, "fork() minden új alkalmazáshoz", 11, cls="quiet", anchor="middle"))
    p.append(text(zx, 330, "Binder-hívás: az alkalmazás", 11, cls="acct"))
    p.append(text(zx, 346, "kérése a kernel driverén", 11, cls="acct"))
    p.append(text(zx, 362, "keresztül jut el a", 11, cls="acct"))
    p.append(text(zx, 378, "system_server folyamathoz,", 11, cls="acct"))
    p.append(text(zx, 394, "és a válasz ugyanezen", 11, cls="acct"))
    p.append(text(zx, 410, "az úton tér vissza", 11, cls="acct"))
    return svg(zx + 190, 460, title, "\n".join(p))


# ---------------- 3. Process importance and oom_score_adj ----------------
def oom_ladder():
    m = "ol"
    title = "Az Android fontosság szerint rangsorolja a folyamatokat; a low memory killer alulról kezdi"
    p = [f"<defs>{marker(m, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    levels = [
        (-1000, "natív daemonok (init, lmkd …)", "sosem áll le", "plain"),
        (-900, "system_server", "", "plain"),
        (-800, "perzisztens alkalm. (telefon, SystemUI)", "", "plain"),
        (0, "előtér: a képernyőn lévő alkalmazás", "", "acc"),
        (100, "látható (pl. egy párbeszédablak mögött)", "", "acc"),
        (200, "érzékelhető (zene szól)", "", "acc"),
        (500, "szolgáltatás (háttérmunka)", "", "tint"),
        (600, "kezdőképernyő (a launcher)", "", "tint"),
        (700, "előző alkalmazás", "", "tint"),
        (800, "régebbi szolgáltatások", "", "tint"),
        (900, "cached alkalmazások: 900 … 999", "a legutóbbi 900-on", "c2"),
    ]
    x, w, h = 140, 370, 30
    for i, (adj, name, note, kind) in enumerate(levels):
        y = 52 + i * (h + 4)
        p.append(text(x - 14, y + 20, str(adj), 12.5, 600, anchor="end"))
        p.append(rect(x, y, w, h, kind, rx=4))
        p.append(text(x + 10, y + 20, name, 12))
        if note:
            p.append(text(x + w - 8, y + 20, note, 11, cls="quiet", anchor="end"))
    p.append(text(x - 14, 46, "oom_score_adj", 11, 600, cls="quiet", anchor="end"))
    ytop = 52 + 10 * (h + 4) + h
    ybot = 52 + 3 * (h + 4)
    ax = x + w + 30
    p.append(path(f"M{ax} {ytop}V{ybot + 6}", m, cls="bads", width=2))
    p.append(text(ax + 12, ytop - 4, "elsőként leállítva", 12, 600, cls="bad"))
    p.append(text(ax + 12, ytop - 40, "nagyobb nyomásnál:", 11, cls="quiet"))
    p.append(text(ax + 12, ytop - 24, "feljebb is leállít", 11, cls="quiet"))
    p.append(text(ax + 12, ybot + 18, "utolsóként leállítva", 12, 600, cls="bad"))
    p.append(text(ax + 12, ybot + 34, "(csak kritikus", 11, cls="quiet"))
    p.append(text(ax + 12, ybot + 50, "nyomásnál)", 11, cls="quiet"))
    yb = 52 + 11 * (h + 4) + 18
    p.append(text(24, yb, "A system_server ActivityManagere minden alkalmazás értékét a /proc/PID/oom_score_adj fájlba írja, valahányszor az állapota változik.", 11.5, cls="quiet"))
    p.append(text(24, yb + 18, "Az lmkd figyeli a memórianyomást (PSI), és alulról kezdve állít le; a kernel OOM killere végső esetben ugyanezeket az értékeket használja.", 11.5, cls="quiet"))
    return svg(800, yb + 34, title, "\n".join(p))


# ---------------- 4. DVFS: race to idle or slow and steady (from energy.py) ----------------
def dvfs_energy():
    import energy
    title = "Race to idle vagy lassan, de egyenletesen? Attól függ, mi marad még ébren (modell)"
    p = [text(24, 30, title, 15, 600)]
    # left panel: power over time for three operating points, P_rest = 0.3 W
    name = energy.SCENARIOS[1][0]
    rows = energy.table()[name]
    pick = [rows[4], rows[2], rows[0]]          # 2.2, 1.4, 0.6 GHz
    X0, Y0, PW, PH = 70, 70, 300, 70            # one strip per strategy
    sx = PW / energy.D
    pmax = 2.2
    p.append(text(24, 58, "Teljesítmény a 2 s-os periódus alatt (P_rest = 0,3 W)", 12.5, 600))
    for k, (f, V, e) in enumerate(pick):
        t, ed, es, ei = e
        prun = (ed + es) / t
        yb = Y0 + k * (PH + 30) + PH
        p.append(line(X0, yb, X0 + PW, yb, "edge"))
        p.append(line(X0, yb - PH, X0, yb, "edge"))
        h = prun / pmax * (PH - 6)
        p.append(bar(X0, yb - h, t * sx, h, "acct", 0.55))
        hi = energy.P_IDLE / pmax * (PH - 6)
        p.append(bar(X0 + t * sx, yb - max(hi, 1.2), (energy.D - t) * sx, max(hi, 1.2), "c2"))
        p.append(text(X0 - 8, yb - PH / 2 + 4, f"{f / 1e9:.1f} GHz".replace(".", ","), 11.5, 600, anchor="end"))
        if t * sx < PW * 0.6:
            p.append(text(X0 + t * sx + 6, yb - h + 12, f"{prun:.2f} W, {t:.2f} s-ig".replace(".", ","), 11, cls="quiet"))
        else:
            p.append(text(X0 + 4, yb - h - 6, f"{prun:.2f} W, {t:.2f} s-ig".replace(".", ","), 11, cls="quiet"))
        p.append(text(X0 + PW, yb - PH + 10, f"E = {ed + es + ei:.2f} J".replace(".", ","), 11.5, 600, anchor="end"))
    yax = Y0 + 3 * (PH + 30) - 14
    p.append(text(X0, yax, "0 s", 10.5, cls="quiet", anchor="middle"))
    p.append(text(X0 + PW, yax, "2 s", 10.5, cls="quiet", anchor="middle"))
    p.append(text(X0 + PW / 2, yax, "magasság: teljesítmény; kék: fut, narancs: mély idle", 10.5, cls="quiet", anchor="middle"))
    # right panel: total energy per operating point for three scenarios
    RX, RY, RW, RH = 440, 70, 300, 250
    p.append(text(RX - 20, 58, "A feladat energiája az egyes működési pontokon [J]", 12.5, 600))
    scen = energy.SCENARIOS[:3]
    emax = 2.2
    p.append(line(RX, RY + RH, RX + RW, RY + RH, "edge"))
    p.append(line(RX, RY, RX, RY + RH, "edge"))
    for v in (0.5, 1.0, 1.5, 2.0):
        yy = RY + RH - v / emax * RH
        p.append(line(RX, yy, RX + RW, yy, "grid", 1))
        p.append(text(RX - 6, yy + 4, f"{v:.1f}".replace(".", ","), 10.5, cls="quiet", anchor="end"))
    cls = ["quiet", "acct", "c2"]
    gw = RW / len(energy.OPPS)
    bw = (gw - 14) / 3
    for j, (f, V) in enumerate(energy.OPPS):
        gx = RX + j * gw + 7
        for s, (sn, prest, stall) in enumerate(scen):
            e = energy.energy(f, V, prest, stall)
            tot = sum(e[1:])
            hh = tot / emax * RH
            p.append(bar(gx + s * bw, RY + RH - hh, bw - 2, hh, cls[s], 0.85))
            best = min(energy.OPPS, key=lambda o: sum(energy.energy(o[0], o[1], prest, stall)[1:]))
            if (f, V) == best:
                p.append(text(gx + s * bw + bw / 2 - 1, RY + RH - hh - 5, "▼", 10, cls="ink", anchor="middle"))
        p.append(text(RX + j * gw + gw / 2, RY + RH + 16, f"{f / 1e9:.1f}".replace(".", ","), 11, anchor="middle"))
    p.append(text(RX + RW / 2, RY + RH + 32, "frekvencia [GHz]", 11, cls="quiet", anchor="middle"))
    leg = ["P_rest = 0 (csak a mag)", "P_rest = 0,3 W (memória ébren)", "P_rest = 1 W (kijelző, rádió)"]
    for s, lab in enumerate(leg):
        ly = RY + RH + 52 + s * 17
        p.append(bar(RX, ly - 9, 10, 10, cls[s], 0.85))
        p.append(text(RX + 16, ly, lab, 11))
    p.append(text(RX + 210, RY + RH + 52, "▼ legkevesebb energia", 11, cls="quiet"))
    yb = RY + RH + 52 + 3 * 17 + 14
    p.append(text(24, yb, "Az energy.py modellje: E = C·V²·f·t + (I_leak·V + P_rest)·t + P_idle·(2 s − t), W = 10⁹ ciklus. Ha semmi más nincs ébren, a leglassabb", 11.5, cls="quiet"))
    p.append(text(24, yb + 18, "pont nyer; minél több marad ébren a rendszerből, amíg a mag dolgozik, annál gyorsabb a legjobb pont (race to idle).", 11.5, cls="quiet"))
    return svg(780, yb + 34, title, "\n".join(p))


# ---------------- 5. Radio tail energy and batching ----------------
def radio_tail():
    title = "A mobilrádió minden átvitel után másodpercekig nagy fogyasztással ébren marad: kötegelj!"
    p = [text(24, 30, title, 15, 600)]
    X0, PW = 120, 600
    T = 60.0
    sx = PW / T
    tail, promo, act = 10.0, 0.5, 1.0
    pw = {"idle": 0.04, "promo": 0.6, "act": 1.0, "tail": 0.55}
    H = 70

    def strip(y, starts, label, sub):
        p.append(text(24, y - H / 2, label, 12.5, 600))
        p.append(text(24, y - H / 2 + 16, sub, 11, cls="quiet"))
        p.append(line(X0, y, X0 + PW, y, "edge"))
        cur = 0.0
        busy_until = -1
        segs = []
        for s in starts:
            segs.append((s, s + promo, "promo"))
            segs.append((s + promo, s + promo + act, "act"))
            segs.append((s + promo + act, s + promo + act + tail, "tail"))
        for a, b, k in segs:
            hh = pw[k] * (H - 8)
            c = {"promo": "c2", "act": "acct", "tail": "bad"}[k]
            p.append(bar(X0 + a * sx, y - hh, (b - a) * sx, hh, c, 0.75 if k != "tail" else 0.45))
        p.append(bar(X0, y - 2, PW, 2, "quiet", 0.6))
        return segs

    s1 = strip(110, [2, 22, 42], "Kötegelés nélkül", "3 átvitel, 3 tail")
    s2 = strip(220, [42], "Kötegelve", "1 átvitel, 1 tail")
    for x, lab in [(2, "küldés"), (22, "küldés"), (42, "küldés")]:
        p.append(text(X0 + x * sx, 124, lab, 10.5, cls="quiet"))
    p.append(text(X0 + 42 * sx, 234, "mindhárom elküldése", 10.5, cls="quiet"))
    for t in (0, 20, 40, 60):
        p.append(text(X0 + t * sx, 252, f"{t} s", 10.5, cls="quiet", anchor="middle"))
    ly = 280
    for i, (c, op, lab) in enumerate([("c2", 0.75, "promotion: kapcsolódás a hálózathoz"), ("acct", 0.75, "átvitel"),
                                      ("bad", 0.45, "tail: várakozás nagy fogyasztással további adatra"),
                                      ("quiet", 0.6, "tétlen")]):
        x = 24 + [0, 250, 340, 660][i]
        p.append(bar(x, ly - 9, 12, 10, c, op))
        p.append(text(x + 18, ly, lab, 11))
    p.append(text(24, ly + 26, "Csak az alak vázlata (a magasságok nem arányosak). Az adat ugyanaz; az energia a színezett terület, nagyobb része a tailekben.", 11.5, cls="quiet"))
    p.append(text(24, ly + 44, "Az OS kötegelhet: a háttér-szinkronizálásokat közös pillanatra halasztja (Doze karbantartási ablakai, JobScheduler, push üzenetek).", 11.5, cls="quiet"))
    return svg(X0 + PW + 30, ly + 62, title, "\n".join(p))


# ---------------- 6. A/B and virtual A/B updates ----------------
def ab_update():
    m, ma = "ab", "aba"
    title = "Seamless update: telepítés a futó rendszer mellé, váltás újraindításkor, visszaállás hiba esetén"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # left: A/B
    p.append(text(24, 62, "Hagyományos A/B: minden partícióból két példány", 12.5, 600))
    for i, (slot, kind, state) in enumerate([("slot A", "acc", "fut (régi változat)"), ("slot B", "c2", "ide íródik a frissítés a háttérben")]):
        x = 24 + i * 190
        p.append(rect(x, 74, 176, 150, kind, rx=8))
        p.append(text(x + 88, 94, slot, 13, 600, anchor="middle"))
        for k, part in enumerate(["boot_" + slot[-1].lower(), "system_" + slot[-1].lower(), "vendor_" + slot[-1].lower()]):
            p += boxt(x + 14, 104 + k * 34, 148, 28, [part], "plain", 11.5)
        p.append(text(x + 88, 242, state, 11, cls="quiet", anchor="middle"))
    p.append(path("M200 160H214", ma, cls="acc", width=1.75))
    p.append(text(24, 270, "Újraindítás: a bootloader B-re vált.", 11.5))
    p.append(text(24, 288, "B többször nem indul el: vissza A-ra.", 11.5))
    p.append(text(24, 306, "Ár: kétszeres hely a rendszernek.", 11.5))
    # right: virtual A/B
    RX = 430
    p.append(text(RX, 62, "Virtual A/B (Android 11+): egy példány plusz egy snapshot", 12.5, 600))
    p.append(rect(RX, 74, 176, 150, "acc", rx=8))
    p.append(text(RX + 88, 94, "alappartíciók", 13, 600, anchor="middle"))
    for k, part in enumerate(["system", "vendor", "product"]):
        p += boxt(RX + 14, 104 + k * 34, 148, 28, [part], "plain", 11.5)
    p.append(text(RX + 88, 242, "fut (régi változat)", 11, cls="quiet", anchor="middle"))
    p.append(rect(RX + 196, 104, 150, 96, "c2", rx=8))
    p.append(text(RX + 271, 126, "copy-on-write", 12.5, 600, anchor="middle"))
    p.append(text(RX + 271, 144, "snapshot a /data-ban:", 11, cls="quiet", anchor="middle"))
    p.append(text(RX + 271, 160, "csak a megváltozott", 11, cls="quiet", anchor="middle"))
    p.append(text(RX + 271, 176, "blokkok, tömörítve", 11, cls="quiet", anchor="middle"))
    p.append(path(f"M{RX + 196} 152H{RX + 180}", ma, cls="acc", width=1.75))
    p.append(text(RX, 270, "Újraindítás: a kernel az alap + snapshotot mutatja új változatként.", 11.5))
    p.append(text(RX, 288, "Sikeres indulás: a snapshotot merge-eli az alapba.", 11.5))
    p.append(text(RX, 306, "Sikertelen indulás: a snapshot elvész, a régi változat marad.", 11.5))
    p.append(text(24, 340, "Mindkettő érintetlenül hagyja a futó rendszert a telepítés alatt, így az egyetlen kiesés egy újraindítás. A verified boot ellenőrzi", 11.5, cls="quiet"))
    p.append(text(24, 358, "a boot image-et futtatás előtt és minden rendszerblokkot olvasáskor (dm-verity); a rollback protection elutasítja a régebbi változatokat.", 11.5, cls="quiet"))
    return svg(800, 376, title, "\n".join(p))


# ---------------- 7. RM vs EDF on task set B (from rtsim.py) ----------------
def rm_edf():
    import rtsim
    tasks = rtsim.TASK_SETS["B"]
    title = "A B feladathalmaz (U = 0,97): a rate-monotonic elmulaszt egy határidőt, az EDF mindet betartja"
    p = [text(24, 30, title, 15, 600)]
    X0, u = 90, 18
    H = len(tasks)
    TT = 35
    cls = ["acct", "c2"]
    for r, pol in enumerate(("RM", "EDF")):
        tl, misses = rtsim.simulate(tasks, pol)
        ybase = 72 + r * 150
        p.append(text(24, ybase + 4, pol, 14, 600))
        for i, (C, T) in enumerate(tasks):
            y = ybase + 14 + i * 40
            p.append(text(X0 - 10, y + 20, f"T{i + 1}", 12, 600, anchor="end"))
            p.append(line(X0, y + 30, X0 + TT * u, y + 30, "edge"))
            for t, who in enumerate(tl):
                if who == i:
                    p.append(bar(X0 + t * u + 0.5, y + 12, u - 1, 18, cls[i], 0.8))
            for k in range(0, TT + 1, T):
                p.append(line(X0 + k * u, y + 2, X0 + k * u, y + 30, "edge", 1.25))
                p.append(f'<path d="M{X0 + k * u - 3:.1f} {y + 6}L{X0 + k * u:.1f} {y}L{X0 + k * u + 3:.1f} {y + 6}" fill="none" class="edge" stroke-width="1.25"/>')
            for (ti, tm) in misses:
                if ti == i:
                    xm = X0 + tm * u
                    p.append(f'<circle cx="{xm:.1f}" cy="{y + 21}" r="8" fill="none" class="bads" stroke-width="2"/>')
                    p.append(text(xm + 12, y + 2, "elmulasztott határidő", 11, 600, cls="bad"))
        ya = ybase + 14 + H * 40 + 2
        for t in range(0, TT + 1, 5):
            p.append(text(X0 + t * u, ya + 10, str(t), 10.5, cls="quiet", anchor="middle"))
    yb = 72 + 2 * 150 + 4
    p.append(text(24, yb, "T1: C = 2, T = 5;  T2: C = 4, T = 7;  határidő = a következő indítás (a jelek). RM alatt mindig T1 nyer, így T2 csak 4 egységéből", 11.5, cls="quiet"))
    p.append(text(24, yb + 18, "3-at kap meg t = 7 előtt. Az EDF a közelebbi határidejű jobot futtatja, és minden jobot időben befejez (U = 0,97 ≤ 1).", 11.5, cls="quiet"))
    return svg(X0 + TT * u + 40, yb + 34, title, "\n".join(p))


# ---------------- 8. A smartwatch: two processors and a phone ----------------
def wearable():
    m = "wr"
    title = "Az okosóra megosztja a munkát: a mikrovezérlő ébren marad, az alkalmazásprocesszor többnyire alszik"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # sensors
    p += boxt(24, 70, 150, 150, [], "plain")
    p.append(text(99, 90, "Szenzorok", 12.5, 600, anchor="middle"))
    for k, s in enumerate(["gyorsulásmérő", "pulzus (PPG)", "giroszkóp", "barométer", "érintés, gombok"]):
        p.append(text(99, 112 + k * 20, s, 11, cls="quiet", anchor="middle"))
    # MCU
    p += boxt(214, 60, 220, 170, [], "c2")
    p.append(text(324, 82, "Kis fogyasztású mikrovezérlő", 12.5, 600, anchor="middle"))
    p.append(text(324, 98, "RTOS, mindig ébren, milliwattok", 11, cls="quiet", anchor="middle"))
    for k, s in enumerate(["szenzorokat olvas és kötegel", "lépést számol, esést észlel", "ambient számlapot rajzol",
                           "egyszerű értesítéseket mutat", "szükség esetén ébreszti az AP-t"]):
        p.append(text(232, 124 + k * 20, "· " + s, 11.5))
    # AP
    p += boxt(474, 60, 240, 170, [], "acc")
    p.append(text(594, 82, "Alkalmazásprocesszor", 12.5, 600, anchor="middle"))
    p.append(text(594, 98, "Wear OS vagy watchOS, többnyire alszik", 11, cls="quiet", anchor="middle"))
    for k, s in enumerate(["alkalmazásokat és UI-t futtat", "térkép, fizetés, hang", "feldolgozza a kötegelt adatokat",
                           "a teljes kijelzőt frissíti", "a telefonnal és a felhővel beszél"]):
        p.append(text(492, 124 + k * 20, "· " + s, 11.5))
    p.append(path("M174 145H210", m))
    p.append(path("M434 130H470", m))
    p.append(path("M474 160H438", m))
    p.append(text(452, 252, "ébresztés / átadás", 11, cls="quiet", anchor="middle"))
    # phone
    p += boxt(754, 80, 150, 130, ["Telefon", "Bluetooth LE-n át:", "internet, nehéz munka,", "értesítések,", "alkalmazástelepítés"], "tint", 12.5, 600)
    p.append(path("M714 135H750", m))
    p.append(path("M754 160H718", m))
    p.append(text(24, 272, "Az egészségügyi adatok titkosítva maradnak az órán és a telefonon; az alkalmazások csak a felhasználó engedélyével kapják meg (Health Connect, HealthKit).", 11.5, cls="quiet"))
    p.append(text(24, 290, "A Wear OS ezt a megosztást hibrid interfésznek hívja; más eszközökben ugyanez szenzorhubként vagy mindig ébren lévő társprocesszorként jelenik meg.", 11.5, cls="quiet"))
    return svg(930, 308, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("design-goals", design_goals), ("android-stack", android_stack), ("oom-adj", oom_ladder),
                    ("dvfs-energy", dvfs_energy), ("radio-tail", radio_tail), ("ab-update", ab_update),
                    ("rm-edf", rm_edf), ("wearable", wearable)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
