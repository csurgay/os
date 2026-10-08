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
    title = "From the server room to the sensor: the same OS ideas, different priorities"
    p = [text(24, 30, title, 15, 600)]
    cols = [("Server", "acc"), ("Desktop, laptop", "plain"), ("Phone", "c2"), ("Watch", "c2"), ("Microcontroller", "plain")]
    rows = [
        ("Power budget", ["100s of W", "10-100 W", "1-5 W sustained", "10s-100s of mW", "µW asleep, mW awake"]),
        ("Memory", ["100s of GiB-TiB", "8-64 GiB", "4-16 GiB", "0.5-2 GiB", "KiB to a few MiB"]),
        ("Energy source", ["mains, redundant", "mains or hours", "battery, a day", "battery, 1-3 days", "battery for years"]),
        ("Main goal", ["throughput, uptime", "responsiveness", "energy per task", "always on, cheaply", "deadlines, µW sleep"]),
        ("Who is waiting", ["many remote users", "one user", "one user, on the move", "a glance at the wrist", "a physical process"]),
        ("Typical OS", ["Linux, Windows Server", "Windows, macOS, Linux", "Android, iOS", "Wear OS, watchOS, RTOS", "FreeRTOS, Zephyr"]),
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
    p.append(text(x0 + lw + 10, ya + 20, "less energy, less memory, more deadlines; the OS must also manage energy, heat, radios and sensors", 11.5, cls="quiet"))
    p.append(text(x0, ya + 44, "Orders of magnitude for typical devices of 2026, not limits: each class contains much smaller and much larger devices.", 11.5, cls="quiet"))
    return svg(x0 + lw + 5 * cw + 20, ya + 62, title, "\n".join(p))


# ---------------- 2. The Android stack ----------------
def android_stack():
    m, ma = "as", "asa"
    title = "The Android stack: apps in sandboxes above a Linux kernel, Binder in between"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    L, W = 24, 560
    # apps
    p.append(text(L, 60, "Apps: one process and one Linux UID each, SELinux domain untrusted_app", 12, 600))
    apps = [("Maps", "u0_a123"), ("Camera", "u0_a87"), ("Launcher", "u0_a64"), ("Your app", "u0_a250")]
    for i, (n, u) in enumerate(apps):
        p += boxt(L + i * 142, 70, 132, 46, [n, u], "c2", 12, 600)
    # framework
    p += boxt(L, 130, W, 46, ["Java/Kotlin API framework", "ActivityManager, PackageManager, WindowManager … in the system_server process"], "acc", 12.5, 600)
    # runtime + native
    p += boxt(L, 190, 272, 52, ["Android Runtime (ART)", "DEX bytecode, AOT/JIT, garbage collector"], "tint", 12.5, 600)
    p += boxt(L + 288, 190, 272, 52, ["Native libraries and daemons", "Bionic libc, media, SQLite; lmkd, surfaceflinger"], "tint", 12.5, 600)
    # treble line
    p.append(line(L - 6, 258, L + W + 6, 258, "acc", 1.5, "6 4"))
    p.append(text(L + W + 50, 254, "above: system partition", 11, 600, cls="acct"))
    p.append(text(L + W + 50, 270, "HALs: vendor partition", 11, 600, cls="acct"))
    p.append(text(L + W + 50, 286, "kernel: boot partition", 11, 600, cls="acct"))
    p.append(text(L + W + 50, 302, "(the dashed line: Treble)", 11, cls="quiet"))
    p += boxt(L, 268, W, 46, ["Hardware abstraction layer (HAL)", "camera, audio, sensors, radio … as separate processes with stable AIDL interfaces"], "tint", 12.5, 600)
    # kernel
    p.append(rect(L, 328, W, 76, "acc", rx=8))
    p.append(text(L + 12, 348, "Linux kernel: Generic Kernel Image (GKI) + vendor modules", 12.5, 600))
    ks = ["vendor drivers", "f2fs, dm-verity", "PSI, cgroups", "SELinux, seccomp", "Binder driver"]
    for i, k in enumerate(ks):
        p += boxt(L + 10 + i * 109, 358, 101, 36, [k], "acc" if i == 4 else "plain", 10.5, 600 if i == 4 else 400)
    p += boxt(L, 414, W, 30, ["hardware: SoC with big and little cores, GPU, NPU, modem, sensors"], "plain", 12)
    # Binder path in a corridor right of the stack: app -> driver -> system_server
    bx = L + 10 + 4 * 109 + 101
    p.append(path(f"M{L + 4 * 142 - 10} 100H{L + W + 14}V368H{bx + 4}", ma, cls="acc", width=1.75))
    p.append(path(f"M{bx} 384H{L + W + 26}V153H{L + W + 4}", ma, cls="acc", width=1.75))
    # zygote on the right
    zx = L + W + 50
    p += boxt(zx, 130, 170, 52, ["Zygote", "ART and classes preloaded"], "c2", 12.5, 600)
    p.append(path(f"M{zx + 85} 130V86H{L + 4 * 142 - 6}", m))
    p.append(text(zx + 85, 76, "fork() for every new app", 11, cls="quiet", anchor="middle"))
    p.append(text(zx, 330, "Binder call: the app's", 11, cls="acct"))
    p.append(text(zx, 346, "request goes through the", 11, cls="acct"))
    p.append(text(zx, 362, "kernel driver to the", 11, cls="acct"))
    p.append(text(zx, 378, "system_server process,", 11, cls="acct"))
    p.append(text(zx, 394, "and the reply comes back", 11, cls="acct"))
    p.append(text(zx, 410, "the same way", 11, cls="acct"))
    return svg(zx + 190, 460, title, "\n".join(p))


# ---------------- 3. Process importance and oom_score_adj ----------------
def oom_ladder():
    m = "ol"
    title = "Android ranks processes by importance; the low-memory killer starts at the bottom"
    p = [f"<defs>{marker(m, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    levels = [
        (-1000, "native daemons (init, lmkd …)", "never killed", "plain"),
        (-900, "system_server", "", "plain"),
        (-800, "persistent apps (phone, SystemUI)", "", "plain"),
        (0, "foreground: the app on screen", "", "acc"),
        (100, "visible (e.g. behind a dialog)", "", "acc"),
        (200, "perceptible (music playing)", "", "acc"),
        (500, "service (background work)", "", "tint"),
        (600, "home (the launcher)", "", "tint"),
        (700, "previous app", "", "tint"),
        (800, "older services", "", "tint"),
        (900, "cached apps: 900 … 999", "most recent at 900", "c2"),
    ]
    x, w, h = 140, 300, 30
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
    p.append(text(ax + 12, ytop - 4, "killed first", 12, 600, cls="bad"))
    p.append(text(ax + 12, ytop - 40, "more pressure:", 11, cls="quiet"))
    p.append(text(ax + 12, ytop - 24, "kill further up", 11, cls="quiet"))
    p.append(text(ax + 12, ybot + 18, "killed last", 12, 600, cls="bad"))
    p.append(text(ax + 12, ybot + 34, "(only under critical", 11, cls="quiet"))
    p.append(text(ax + 12, ybot + 50, "pressure)", 11, cls="quiet"))
    yb = 52 + 11 * (h + 4) + 18
    p.append(text(24, yb, "ActivityManager in system_server writes each app's value to /proc/PID/oom_score_adj whenever the app's state changes.", 11.5, cls="quiet"))
    p.append(text(24, yb + 18, "lmkd watches memory pressure (PSI) and kills from the bottom; the kernel's OOM killer uses the same values as a last resort.", 11.5, cls="quiet"))
    return svg(720, yb + 34, title, "\n".join(p))


# ---------------- 4. DVFS: race to idle or slow and steady (from energy.py) ----------------
def dvfs_energy():
    import energy
    title = "Race to idle or slow and steady? It depends on what else stays awake (a model)"
    p = [text(24, 30, title, 15, 600)]
    # left panel: power over time for three operating points, P_rest = 0.3 W
    name = energy.SCENARIOS[1][0]
    rows = energy.table()[name]
    pick = [rows[4], rows[2], rows[0]]          # 2.2, 1.4, 0.6 GHz
    X0, Y0, PW, PH = 70, 70, 300, 70            # one strip per strategy
    sx = PW / energy.D
    pmax = 2.2
    p.append(text(24, 58, "Power over the 2 s period (P_rest = 0.3 W)", 12.5, 600))
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
        p.append(text(X0 - 8, yb - PH / 2 + 4, f"{f / 1e9:.1f} GHz", 11.5, 600, anchor="end"))
        if t * sx < PW * 0.6:
            p.append(text(X0 + t * sx + 6, yb - h + 12, f"{prun:.2f} W for {t:.2f} s", 11, cls="quiet"))
        else:
            p.append(text(X0 + 4, yb - h - 6, f"{prun:.2f} W for {t:.2f} s", 11, cls="quiet"))
        p.append(text(X0 + PW, yb - PH + 10, f"E = {ed + es + ei:.2f} J", 11.5, 600, anchor="end"))
    yax = Y0 + 3 * (PH + 30) - 14
    p.append(text(X0, yax, "0 s", 10.5, cls="quiet", anchor="middle"))
    p.append(text(X0 + PW, yax, "2 s", 10.5, cls="quiet", anchor="middle"))
    p.append(text(X0 + PW / 2, yax, "height: power; blue: running, orange: deep idle", 10.5, cls="quiet", anchor="middle"))
    # right panel: total energy per operating point for three scenarios
    RX, RY, RW, RH = 440, 70, 300, 250
    p.append(text(RX - 20, 58, "Energy of the task at each operating point [J]", 12.5, 600))
    scen = energy.SCENARIOS[:3]
    emax = 2.2
    p.append(line(RX, RY + RH, RX + RW, RY + RH, "edge"))
    p.append(line(RX, RY, RX, RY + RH, "edge"))
    for v in (0.5, 1.0, 1.5, 2.0):
        yy = RY + RH - v / emax * RH
        p.append(line(RX, yy, RX + RW, yy, "grid", 1))
        p.append(text(RX - 6, yy + 4, f"{v:.1f}", 10.5, cls="quiet", anchor="end"))
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
        p.append(text(RX + j * gw + gw / 2, RY + RH + 16, f"{f / 1e9:.1f}", 11, anchor="middle"))
    p.append(text(RX + RW / 2, RY + RH + 32, "frequency [GHz]", 11, cls="quiet", anchor="middle"))
    leg = ["P_rest = 0 (only the core)", "P_rest = 0.3 W (memory awake)", "P_rest = 1 W (screen, radio)"]
    for s, lab in enumerate(leg):
        ly = RY + RH + 52 + s * 17
        p.append(bar(RX, ly - 9, 10, 10, cls[s], 0.85))
        p.append(text(RX + 16, ly, lab, 11))
    p.append(text(RX + 210, RY + RH + 52, "▼ least energy", 11, cls="quiet"))
    yb = RY + RH + 52 + 3 * 17 + 14
    p.append(text(24, yb, "Model of energy.py: E = C·V²·f·t + (I_leak·V + P_rest)·t + P_idle·(2 s − t), W = 10⁹ cycles. When nothing else is awake, the slowest", 11.5, cls="quiet"))
    p.append(text(24, yb + 18, "point wins; the more of the system must stay awake while the core works, the faster the best point (race to idle).", 11.5, cls="quiet"))
    return svg(780, yb + 34, title, "\n".join(p))


# ---------------- 5. Radio tail energy and batching ----------------
def radio_tail():
    title = "A cellular radio stays in a high-power state for seconds after each transfer: batch the transfers"
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

    s1 = strip(110, [2, 22, 42], "Unbatched", "3 transfers, 3 tails")
    s2 = strip(220, [42], "Batched", "1 transfer, 1 tail")
    for x, lab in [(2, "send"), (22, "send"), (42, "send")]:
        p.append(text(X0 + x * sx, 124, lab, 10.5, cls="quiet"))
    p.append(text(X0 + 42 * sx, 234, "send all three", 10.5, cls="quiet"))
    for t in (0, 20, 40, 60):
        p.append(text(X0 + t * sx, 252, f"{t} s", 10.5, cls="quiet", anchor="middle"))
    ly = 280
    for i, (c, op, lab) in enumerate([("c2", 0.75, "promotion: connecting to the network"), ("acct", 0.75, "transfer"),
                                      ("bad", 0.45, "tail: waiting in a high-power state for more data"),
                                      ("quiet", 0.6, "idle")]):
        x = 24 + [0, 250, 340, 660][i]
        p.append(bar(x, ly - 9, 12, 10, c, op))
        p.append(text(x + 18, ly, lab, 11))
    p.append(text(24, ly + 26, "Sketch of the shape only (heights not to scale). The data sent is the same; the energy is the shaded area, and most of it is in the tails.", 11.5, cls="quiet"))
    p.append(text(24, ly + 44, "The OS can batch: defer background syncs to a common moment (Doze maintenance windows, JobScheduler, push messages).", 11.5, cls="quiet"))
    return svg(X0 + PW + 30, ly + 62, title, "\n".join(p))


# ---------------- 6. A/B and virtual A/B updates ----------------
def ab_update():
    m, ma = "ab", "aba"
    title = "Seamless updates: install beside the running system, switch at reboot, fall back on failure"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # left: A/B
    p.append(text(24, 62, "Legacy A/B: two copies of every partition", 12.5, 600))
    for i, (slot, kind, state) in enumerate([("slot A", "acc", "running (old version)"), ("slot B", "c2", "update written here in the background")]):
        x = 24 + i * 190
        p.append(rect(x, 74, 176, 150, kind, rx=8))
        p.append(text(x + 88, 94, slot, 13, 600, anchor="middle"))
        for k, part in enumerate(["boot_" + slot[-1].lower(), "system_" + slot[-1].lower(), "vendor_" + slot[-1].lower()]):
            p += boxt(x + 14, 104 + k * 34, 148, 28, [part], "plain", 11.5)
        p.append(text(x + 88, 242, state, 11, cls="quiet", anchor="middle"))
    p.append(path("M200 160H214", ma, cls="acc", width=1.75))
    p.append(text(24, 270, "Reboot: the bootloader switches to B.", 11.5))
    p.append(text(24, 288, "B fails to boot a few times: back to A.", 11.5))
    p.append(text(24, 306, "Cost: twice the space for the system.", 11.5))
    # right: virtual A/B
    RX = 430
    p.append(text(RX, 62, "Virtual A/B (Android 11+): one copy plus a snapshot", 12.5, 600))
    p.append(rect(RX, 74, 176, 150, "acc", rx=8))
    p.append(text(RX + 88, 94, "base partitions", 13, 600, anchor="middle"))
    for k, part in enumerate(["system", "vendor", "product"]):
        p += boxt(RX + 14, 104 + k * 34, 148, 28, [part], "plain", 11.5)
    p.append(text(RX + 88, 242, "running (old version)", 11, cls="quiet", anchor="middle"))
    p.append(rect(RX + 196, 104, 150, 96, "c2", rx=8))
    p.append(text(RX + 271, 126, "copy-on-write", 12.5, 600, anchor="middle"))
    p.append(text(RX + 271, 144, "snapshot in /data:", 11, cls="quiet", anchor="middle"))
    p.append(text(RX + 271, 160, "only the changed", 11, cls="quiet", anchor="middle"))
    p.append(text(RX + 271, 176, "blocks, compressed", 11, cls="quiet", anchor="middle"))
    p.append(path(f"M{RX + 196} 152H{RX + 180}", ma, cls="acc", width=1.75))
    p.append(text(RX, 270, "Reboot: the kernel shows base + snapshot as the new version.", 11.5))
    p.append(text(RX, 288, "Boot confirmed: the snapshot is merged into the base.", 11.5))
    p.append(text(RX, 306, "Boot fails: the snapshot is dropped, the old version stays.", 11.5))
    p.append(text(24, 340, "Both keep the running system untouched while the update installs, so the only downtime is one reboot. Verified boot checks", 11.5, cls="quiet"))
    p.append(text(24, 358, "the boot image before running it and every system block as it is read (dm-verity); rollback protection refuses older versions.", 11.5, cls="quiet"))
    return svg(800, 376, title, "\n".join(p))


# ---------------- 7. RM vs EDF on task set B (from rtsim.py) ----------------
def rm_edf():
    import rtsim
    tasks = rtsim.TASK_SETS["B"]
    title = "Task set B (U = 0.97): rate-monotonic misses a deadline, EDF meets them all"
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
                    p.append(text(xm + 12, y + 2, "deadline missed", 11, 600, cls="bad"))
        ya = ybase + 14 + H * 40 + 2
        for t in range(0, TT + 1, 5):
            p.append(text(X0 + t * u, ya + 10, str(t), 10.5, cls="quiet", anchor="middle"))
    yb = 72 + 2 * 150 + 4
    p.append(text(24, yb, "T1: C = 2, T = 5;  T2: C = 4, T = 7;  deadline = next release (the ticks). Under RM, T1 always wins, so T2 gets only", 11.5, cls="quiet"))
    p.append(text(24, yb + 18, "3 of its 4 units before t = 7. EDF runs whichever job's deadline is nearer and finishes every job in time (U = 0.97 ≤ 1).", 11.5, cls="quiet"))
    return svg(X0 + TT * u + 40, yb + 34, title, "\n".join(p))


# ---------------- 8. A smartwatch: two processors and a phone ----------------
def wearable():
    m = "wr"
    title = "A smartwatch splits the work: a microcontroller stays awake, the application processor mostly sleeps"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # sensors
    p += boxt(24, 70, 150, 150, [], "plain")
    p.append(text(99, 90, "Sensors", 12.5, 600, anchor="middle"))
    for k, s in enumerate(["accelerometer", "heart rate (PPG)", "gyroscope", "barometer", "touch, buttons"]):
        p.append(text(99, 112 + k * 20, s, 11, cls="quiet", anchor="middle"))
    # MCU
    p += boxt(214, 60, 220, 170, [], "c2")
    p.append(text(324, 82, "Low-power microcontroller", 12.5, 600, anchor="middle"))
    p.append(text(324, 98, "an RTOS, always on, milliwatts", 11, cls="quiet", anchor="middle"))
    for k, s in enumerate(["reads and batches sensors", "counts steps, detects falls", "draws the ambient watch face",
                           "shows simple notifications", "wakes the AP when needed"]):
        p.append(text(232, 124 + k * 20, "· " + s, 11.5))
    # AP
    p += boxt(474, 60, 240, 170, [], "acc")
    p.append(text(594, 82, "Application processor", 12.5, 600, anchor="middle"))
    p.append(text(594, 98, "Wear OS or watchOS, mostly asleep", 11, cls="quiet", anchor="middle"))
    for k, s in enumerate(["runs apps and their UI", "maps, payments, voice", "processes batched sensor data",
                           "updates the full display", "talks to the phone and cloud"]):
        p.append(text(492, 124 + k * 20, "· " + s, 11.5))
    p.append(path("M174 145H210", m))
    p.append(path("M434 130H470", m))
    p.append(path("M474 160H438", m))
    p.append(text(452, 252, "wake / hand over", 11, cls="quiet", anchor="middle"))
    # phone
    p += boxt(754, 80, 150, 130, ["Phone", "over Bluetooth LE:", "internet, heavy work,", "notifications,", "app installs"], "tint", 12.5, 600)
    p.append(path("M714 135H750", m))
    p.append(path("M754 160H718", m))
    p.append(text(24, 272, "Health data stay encrypted on the watch and the phone; apps get them only with the user's permission (Health Connect, HealthKit).", 11.5, cls="quiet"))
    p.append(text(24, 290, "Wear OS calls this split its hybrid interface; the same idea appears in other devices as a sensor hub or always-on co-processor.", 11.5, cls="quiet"))
    return svg(930, 308, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("design-goals", design_goals), ("android-stack", android_stack), ("oom-adj", oom_ladder),
                    ("dvfs-energy", dvfs_energy), ("radio-tail", radio_tail), ("ab-update", ab_update),
                    ("rm-edf", rm_edf), ("wearable", wearable)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
