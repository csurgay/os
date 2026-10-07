"""Generate the SVG figures for the Quality, Commercial Aspects and Enterprise Linux lecture.

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
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


def fmt(minutes):
    if minutes >= 24 * 60:
        return f"{minutes / 1440:.1f} nap".replace(".", ",")
    if minutes >= 60:
        return f"{minutes / 60:.1f} óra".replace(".", ",")
    return f"{minutes:.1f} perc".replace(".", ",")


# ---------------- 1. The nines ----------------
def nines():
    title = "Minden újabb kilences tizedére csökkenti a megengedett leállási időt"
    year = 365.25 * 24 * 60
    rows = [("99%", 0.99), ("99,9%", 0.999), ("99,99%", 0.9999), ("99,999%", 0.99999)]
    x0, x1 = 150, 600
    lo, hi = math.log10(1), math.log10(10000)       # 1 minute .. 10,000 minutes
    X = lambda m: x0 + (x1 - x0) * (math.log10(m) - lo) / (hi - lo)
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Megengedett éves leállási idő az egyes rendelkezésre állási szinteken (logaritmikus skála)", 11.5, cls="quiet")]
    top, step = 92, 44
    for t, lab in [(1, "1 perc"), (10, "10 perc"), (60, "1 óra"), (1440, "1 nap"), (10000, "1 hét")]:
        x = X(t)
        p.append(f'<line x1="{x:.1f}" y1="{top - 20}" x2="{x:.1f}" y2="{top + 4 * step - 10}" class="grid"/>')
        p.append(text(x, top + 4 * step + 8, lab, 11.5, cls="quiet", anchor="middle"))
    for i, (lab, a) in enumerate(rows):
        y = top + i * step
        m = (1 - a) * year
        p.append(text(24, y + 5, lab, 13, 600))
        kind = "acc" if lab == "99,99%" else "tint"
        p.append(rect(x0, y - 11, X(m) - x0, 22, kind, rx=4))
        p.append(text(X(m) + 10, y + 5, fmt(m), 12.5, 600))
    p.append(text(24, top + 4 * step + 38, "Kiemelve: 99,99%, az üzletkritikus szolgáltatások gyakori célja: évente kevesebb mint egy óra leállás.", 11.5, cls="quiet"))
    return svg(760, top + 4 * step + 58, title, "\n".join(p))


# ---------------- 2. MTTF, MTTR, MTBF ----------------
def mtbf():
    m = "mt"
    title = "A rendszer felváltva működik és javítás alatt áll"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    y, h = 96, 34
    segs = [(40, 250, "up"), (250, 300, "down"), (300, 560, "up"), (560, 600, "down"), (600, 720, "up")]
    for a, b, k in segs:
        kind = "tint" if k == "up" else "bad"
        p.append(rect(a, y, b - a, h, kind, rx=0))
    p.append(text(145, y + 22, "működik", 12.5, anchor="middle"))
    p.append(text(430, y + 22, "működik", 12.5, anchor="middle"))
    p.append(text(275, y + 54, "meghibásodás,", 11.5, cls="bad", anchor="middle"))
    p.append(text(275, y + 70, "javítás", 11.5, cls="bad", anchor="middle"))
    p.append(text(580, y + 54, "javítás", 11.5, cls="bad", anchor="middle"))
    # annotations
    def span(a, b, yy, lab, cls="acc"):
        out = [f'<path d="M{a} {yy}H{b}" fill="none" class="{cls}" stroke-width="1.5" marker-start="url(#{m})" marker-end="url(#{m})"/>',
               text((a + b) / 2, yy - 8, lab, 12, 600, cls="acct" if cls == "acc" else "ink", anchor="middle")]
        return out
    p += span(300, 560, y - 22, "MTTF: idő a meghibásodásig")
    p += span(560, 600, y + 96, "MTTR", "edge")
    p += span(250, 560, y + 128, "MTBF: egyik meghibásodástól a következőig = MTTR + MTTF", "edge")
    p.append(text(24, y + 170, "Sok meghibásodás átlagában: rendelkezésre állás = MTTF / (MTTF + MTTR), vagyis a működéssel töltött időarány.", 11.5, cls="quiet"))
    p.append(text(24, y + 188, "Ha a javítások rövidek, MTBF ≈ MTTF, így a rendelkezésre állás ≈ MTBF / (MTBF + MTTR).", 11.5, cls="quiet"))
    return svg(760, y + 206, title, "\n".join(p))


# ---------------- 3. Branching vocabulary ----------------
def vocab():
    m, ma = "vb", "vba"
    title = "Ág, összefésülés, fork, upstream, downstream, visszaportolás"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    r = 17
    up = [(110, 150), (250, 150), (390, 150), (530, 150)]
    br = (320, 82)
    dn = [(180, 270), (460, 270)]
    old = (300, 350)

    def node(x, y, kind="plain", lab=None):
        cls = {"plain": ("tint", "edge"), "acc": ("accf", "acc"), "c2": ("c2f", "c2s")}[kind]
        out = [f'<circle cx="{x}" cy="{y}" r="{r}" class="{cls[0]}"/>',
               f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" class="{cls[1]}" stroke-width="1.5"/>']
        if lab:
            out.append(text(x, y + 4, lab, 11, 600, anchor="middle"))
        return out

    # upstream line
    p.append(text(24, 154, "Upstream", 13, 600))
    p.append(text(24, 170, "projekt", 11.5, cls="quiet"))
    for (x1, y1), (x2, y2) in zip(up, up[1:]):
        p.append(path(f"M{x1 + r} {y1}H{x2 - r}", m))
    p.append(path(f"M{up[-1][0] + r} 150H{640}", m, dash="4 3"))
    # branch and merge
    p.append(path(f"M{up[1][0] + 12} {150 - 12}L{br[0] - 14} {br[1] + 8}", m))
    p.append(path(f"M{br[0] + 14} {br[1] + 8}L{up[2][0] - 12} {150 - 12}", m, dash="4 3"))
    p.append(text(262, 98, "ág (branch)", 11.5, 600, cls="quiet", anchor="end"))
    p.append(text(372, 92, "összefésülés (merge)", 11.5, 600, cls="quiet"))
    for x, y in up:
        p += node(x, y)
    p += node(*br)
    # downstream product (fork)
    p.append(text(24, 274, "Downstream", 13, 600))
    p.append(text(24, 290, "termék", 11.5, cls="quiet"))
    p.append(path(f"M{up[0][0] + 8} {150 + r}L{dn[0][0] - 8} {270 - r}", m))
    p.append(text(124, 220, "fork", 11.5, 600, cls="quiet", anchor="end"))
    p.append(path(f"M{dn[0][0] + r} 270H{dn[1][0] - r}", m))
    p.append(path(f"M{dn[1][0] + r} 270H{560}", m, dash="4 3"))
    # downstream from upstream node 3 into product release 2
    p.append(path(f"M{up[2][0] + 6} {150 + r}L{dn[1][0] - 8} {270 - r}", m))
    p.append(text(432, 214, "downstream", 11.5, 600, cls="quiet"))
    # upstream contribution from product to upstream
    p.append(path(f"M{dn[0][0] + 10} {270 - r}L{up[1][0] - 6} {150 + r}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(222, 210, "upstream", 11.5, 600, cls="acct"))
    p.append(text(222, 225, "(javítás visszaküldése)", 11, cls="quiet"))
    p += node(*dn[0], "acc", "v1")
    p += node(*dn[1], "acc", "v2")
    # old release line + backport
    p.append(path(f"M{dn[0][0]} {270 + r}L{old[0] - 12} {old[1] - 12}", m))
    p += node(*old, "c2", "v1.1")
    p.append(path(f"M{dn[1][0] - 10} {270 + r - 2}C{430} {330} {380} {350} {old[0] + r + 2} {old[1]}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(430, 342, "visszaportolás: az új verzió", 11.5, 600, cls="acct"))
    p.append(text(430, 358, "javítása a régihez igazítva", 11.5, cls="quiet"))
    p.append(text(dn[1][0] + 22, 262, "patch", 11.5, 600, cls="quiet"))
    # servers: install + update
    sx = 640
    for i, yy in enumerate((236, 300)):
        p.append(rect(sx, yy, 80, 40, "tint", rx=4))
        p.append(text(sx + 40, yy + 25, f"{i + 1}. szerver", 11.5, anchor="middle"))
    p.append(path(f"M{560} 266L{sx - 4} 256", m))
    p.append(text(572, 240, "telepítés", 11.5, 600, cls="quiet"))
    p.append(path(f"M{old[0] + r} {old[1] + 6}C{480} 392 {600} 392 {sx + 40} {344}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(540, 404, "frissítés: a javítások alkalmazása a használt szervereken", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(24, 432, "Folytonos nyilak: egy kódvonal története. Kék szaggatott: egyik vonalról a másikra átvitt változtatás.", 11.5, cls="quiet"))
    return svg(760, 452, title, "\n".join(p))


# ---------------- 4. The Enterprise Linux family, then and now ----------------
def ecosystem():
    m, ma = "ec", "eca"
    title = "2020-ban a CentOS a RHEL mögül elé került"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]

    def box(x, y, w, name, sub, kind="tint"):
        return [rect(x, y, w, 52, kind), text(x + w / 2, y + 22, name, 13, 600, anchor="middle"),
                text(x + w / 2, y + 39, sub, 11, cls="quiet", anchor="middle")]

    # panel A
    p.append(text(24, 66, "2020-ig", 13, 600))
    ya = 80
    p += box(24, ya, 170, "Fedora", "közösségi, gyors ütemű")
    p += box(290, ya, 170, "RHEL", "Red Hat, előfizetéses", "acc")
    p += box(556, ya, 180, "CentOS Linux", "a RHEL ingyenes rebuildje")
    p.append(path(f"M194 {ya + 26}H290", m))
    p.append(text(242, ya + 18, "ág (branch)", 11, 600, cls="quiet", anchor="middle"))
    p.append(text(242, ya + 44, "néhány évente", 10.5, cls="quiet", anchor="middle"))
    p.append(path(f"M460 {ya + 26}H556", m))
    p.append(text(508, ya + 18, "rebuild", 11, 600, cls="quiet", anchor="middle"))
    p.append(text(508, ya + 44, "forrásokból", 10.5, cls="quiet", anchor="middle"))
    # panel B
    yb = 196
    p.append(f'<line x1="24" y1="{yb - 26}" x2="736" y2="{yb - 26}" class="grid"/>')
    p.append(text(24, yb - 2, "2021 óta", 13, 600))
    yb += 12
    p += box(24, yb, 150, "Fedora", "közösségi")
    p += box(214, yb, 160, "CentOS Stream", "a jövő RHEL-je, nyíltan")
    p += box(414, yb, 130, "RHEL", "Red Hat", "acc")
    p.append(path(f"M174 {yb + 26}H214", m))
    p.append(text(194, yb - 8, "ág", 11, 600, cls="quiet", anchor="middle"))
    p.append(path(f"M374 {yb + 26}H414", m))
    p.append(text(384, yb - 12, "kiadás", 11, 600, cls="quiet", anchor="middle"))
    # rebuilds
    rb = [("AlmaLinux", "ABI-kompatibilis (2021)"), ("Rocky Linux", "1:1 rebuild (2021)"), ("Oracle Linux", "rebuild (2006)")]
    for i, (n, sub) in enumerate(rb):
        y = yb - 30 + i * 62
        p += box(600, y, 136, n, sub, "c2")
        if n == "AlmaLinux":   # builds mainly from CentOS Stream since 2023
            p.append(path(f"M374 {yb + 12}C470 {yb - 40} 540 {y + 26} 600 {y + 26}", m, dash="4 3"))
        else:
            p.append(path(f"M544 {yb + 26}C572 {yb + 26} 572 {y + 26} 600 {y + 26}", m))
    # upstream-first
    p.append(path(f"M{479} {yb + 52}C479 {yb + 96} 99 {yb + 96} 99 {yb + 56}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(290, yb + 112, "a javítások először upstreambe mennek: Fedora, CentOS Stream, eredeti projektek", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(24, yb + 164, "2023 júniusa óta a RHEL-hez kapcsolódó kód egyetlen nyilvános forrása a CentOS Stream; a RHEL saját forráscsomagjait", 11.5, cls="quiet"))
    p.append(text(24, yb + 182, "az ügyfelek és partnerek kapják. Szaggatott: az AlmaLinux főként CentOS Streamből épül (ABI-kompatibilitás).", 11.5, cls="quiet"))
    return svg(760, yb + 202, title, "\n".join(p))


# ---------------- 5. Life cycles ----------------
def lifecycle():
    title = "A RHEL főverziónként tíz évet ígér, a Fedora nagyjából tizenhárom hónapot"
    y0, x0, x1 = 2014, 150, 724
    X = lambda t: x0 + (x1 - x0) * (t - y0) / (2036 - y0)
    rows = [  # name, GA, end of full support, end of maintenance, kind
        ("RHEL 7", 2014.45, 2019.6, 2024.5, "rhel"),
        ("RHEL 8", 2019.37, 2024.37, 2029.37, "rhel"),
        ("RHEL 9", 2022.37, 2027.37, 2032.37, "rhel"),
        ("RHEL 10", 2025.37, 2030.37, 2035.37, "rhel"),
        ("CentOS Linux 8", 2019.7, None, 2022.0, "cut"),
        ("Fedora (mindegyik)", 2024.8, None, 2025.9, "fed"),
    ]
    top, step = 92, 38
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Támogatási időszakok évenként (közelítőleg; a Red Hat jövőbeli dátumai változhatnak)", 11.5, cls="quiet")]
    ya = top + len(rows) * step
    for yr in range(2014, 2037, 2):
        x = X(yr)
        p.append(f'<line x1="{x:.1f}" y1="{top - 20}" x2="{x:.1f}" y2="{ya - 8}" class="grid"/>')
        p.append(text(x, ya + 8, str(yr), 11.5, cls="quiet", anchor="middle"))
    for i, (n, ga, full, end, k) in enumerate(rows):
        y = top + i * step
        p.append(text(24, y + 5, n, 12.5, 600))
        if k == "rhel":
            p.append(rect(X(ga), y - 10, X(full) - X(ga), 20, "acc", rx=3))
            p.append(rect(X(full), y - 10, X(end) - X(full), 20, "tint", rx=3))
        elif k == "cut":
            p.append(rect(X(ga), y - 10, X(end) - X(ga), 20, "bad", rx=3))
            p.append(f'<rect x="{X(end):.1f}" y="{y - 10}" width="{X(2029.4) - X(end):.1f}" height="20" rx="3" fill="none" class="bads" stroke-width="1.25" stroke-dasharray="4 3"/>')
            p.append(text(X(2029.4) + 8, y + 5, "eredetileg 2029-ig tervezve", 11, cls="quiet"))
        else:
            p.append(rect(X(ga), y - 10, X(end) - X(ga), 20, "c2", rx=3))
            p.append(text(X(end) + 8, y + 5, "≈ 13 hónap", 11, cls="quiet"))
    ly = ya + 40
    p.append(rect(24, ly - 11, 14, 14, "acc", rx=2)); p.append(text(44, ly + 1, "teljes támogatás", 11.5))
    p.append(rect(164, ly - 11, 14, 14, "tint", rx=2)); p.append(text(184, ly + 1, "karbantartási támogatás (csak javítások)", 11.5))
    p.append(rect(440, ly - 11, 14, 14, "bad", rx=2)); p.append(text(460, ly + 1, "CentOS Linux 8: korán megszűnt (2021. dec.)", 11.5))
    return svg(760, ly + 20, title, "\n".join(p))


# ---------------- 6. Containers: images share layers, containers share the kernel ----------------
def containers():
    m = "ct"
    title = "A kép saját felhasználói teret hoz; a kernel minden konténernél a gazdagépé"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # left: two images sharing the base layer
    p.append(text(24, 66, "Két kép ugyanarra az alapra építve", 13, 600))
    bw, bh = 150, 34
    lx = [24, 190]
    labels = [("webalkalmazás", "számlázó alkalmazás"), ("Python-csomagok", "Java-futtatókörnyezet")]
    for i, x in enumerate(lx):
        p.append(rect(x, 80, bw, bh, "c2", rx=4)); p.append(text(x + bw / 2, 102, labels[0][i], 12, anchor="middle"))
        p.append(rect(x, 80 + bh + 4, bw, bh, "tint", rx=4)); p.append(text(x + bw / 2, 102 + bh + 4, labels[1][i], 12, anchor="middle"))
        p.append(text(x + bw / 2, 216, f"{i + 1}. kép", 11.5, 600, cls="quiet", anchor="middle"))
    p.append(rect(24, 80 + 2 * (bh + 4), 316, bh + 8, "acc", rx=4))
    p.append(text(182, 106 + 2 * (bh + 4), "alapréteg: UBI 9 (egy példány a lemezen)", 12, 600, anchor="middle"))
    p.append(text(24, 262, "A rétegek csak olvashatók, és hash azonosítja őket,", 11.5, cls="quiet"))
    p.append(text(24, 278, "így a közös alapot egyszer kell tárolni és letölteni.", 11.5, cls="quiet"))
    # right: host with containers
    hx, hy, hw = 400, 66, 336
    p.append(text(hx, hy, "Egy gazdagép három konténerrel", 13, 600))
    cw = 100
    names = [("UBI 9", "felhasználói tér"), ("AlmaLinux 9", "felhasználói tér"), ("Fedora", "felhasználói tér")]
    for i, (n, sub) in enumerate(names):
        x = hx + i * (cw + 18)
        p.append(rect(x, 80, cw, 86, "c2" if i == 0 else "tint", rx=6))
        p.append(text(x + cw / 2, 104, "alkalmazás", 11.5, cls="quiet", anchor="middle"))
        p.append(text(x + cw / 2, 128, n, 12, 600, anchor="middle"))
        p.append(text(x + cw / 2, 146, sub, 11, cls="quiet", anchor="middle"))
        p.append(path(f"M{x + cw / 2} 166V{196}", m))
    p.append(rect(hx, 198, hw, 40, "acc", rx=6))
    p.append(text(hx + hw / 2, 223, "egy Linux-kernel: a gazdagépé (pl. RHEL 9)", 12.5, 600, anchor="middle"))
    p.append(rect(hx, 244, hw, 30, "tint", rx=6))
    p.append(text(hx + hw / 2, 264, "hardver", 12, anchor="middle"))
    p.append(text(24, 314, "Nyilak: rendszerhívások. Minden konténer ugyanazzal a kernellel beszél, ezért a Red Hat a RHEL/UBI-képeket", 11.5, cls="quiet"))
    p.append(text(24, 332, "csak azonos főverziójú gazdagépen támogatja teljesen; más párosítást csak közönséges, nem privilegizált", 11.5, cls="quiet"))
    p.append(text(24, 350, "munkaterheléseknél (a Red Hat kompatibilitási mátrixa szerint).", 11.5, cls="quiet"))
    return svg(760, 370, title, "\n".join(p))


# ---------------- 7. Owning or renting capacity: capex steps vs pay-as-you-go ----------------
def cloud_costs():
    m = "cc"
    title = "Saját szerver: lépcsőkben, az igény előtt; felhő: a költség a használatot követi"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # ---- panel A: capacity over time ----
    ax, ay, aw, ah = 60, 104, 290, 206          # plot area: x0, y_top, width, height
    X = lambda t: ax + aw * t
    Y = lambda v: ay + ah * (1 - v)
    p.append(text(24, 66, "A. Kapacitás és igény az idő függvényében", 13, 600))
    d = lambda t: 0.15 + 0.6 * t + 0.06 * math.sin(12 * t)
    steps = [(0.0, 0.36), (0.30, 0.54), (0.82, 0.92)]   # (purchase time, capacity after it)
    def cap(t):
        c = 0
        for t0, v in steps:
            if t >= t0:
                c = v
        return c
    ts = [i / 400 for i in range(401)]
    # idle area (capacity above demand) and shortage area (demand above capacity)
    top = [(X(t), Y(cap(t))) for t in ts]
    low = [(X(t), Y(min(d(t), cap(t)))) for t in ts]
    poly = top + low[::-1]
    p.append('<path d="M' + "L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + 'Z" class="accf"/>')
    hi = [(X(t), Y(max(d(t), cap(t)))) for t in ts]
    lo2 = [(X(t), Y(cap(t))) for t in ts]
    poly = hi + lo2[::-1]
    p.append('<path d="M' + "L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + 'Z" class="badf"/>')
    # axes
    p.append(path(f"M{ax} {ay + ah}H{ax + aw + 14}", m))
    p.append(path(f"M{ax} {ay + ah}V{ay - 14}", m))
    p.append(text(ax + aw + 14, ay + ah + 18, "idő", 11.5, cls="quiet", anchor="end"))
    p.append(text(ax + 6, ay - 18, "kapacitás", 11.5, cls="quiet"))
    # staircase of owned capacity
    sd = f"M{X(0):.1f} {Y(steps[0][1]):.1f}"
    for (t0, v), (t1, _) in zip(steps, steps[1:] + [(1.0, 0)]):
        sd += f"H{X(t1):.1f}"
        if t1 < 1.0:
            sd += f"V{Y(cap(t1)):.1f}"
    p.append(path(sd, cls="acc", width=2))
    # demand
    p.append('<path d="M' + "L".join(f"{X(t):.1f} {Y(d(t)):.1f}" for t in ts) + '" fill="none" class="c2s" stroke-width="2"/>')
    p.append(text(X(0.06), Y(0.36) - 8, "saját gépek", 11.5, 600, cls="acct"))
    p.append(text(X(0.36), Y(0.28) + 4, "igény", 11.5, 600, cls="c2"))
    p.append(text(X(0.04), Y(0.80), "tétlen: kifizetve, kihasználatlan", 11, 600, cls="acct"))
    p.append(path(f"M{X(0.25):.1f} {Y(0.78):.1f}L{X(0.40):.1f} {Y(0.52):.1f}", cls="acc", width=1))
    p.append(text(X(0.38), Y(0.94), "hiány: késik a szerver", 11, 600, cls="bad"))
    p.append(path(f"M{X(0.62):.1f} {Y(0.91):.1f}L{X(0.72):.1f} {Y(0.61):.1f}", cls="bads", width=1))
    for t0, _ in steps[1:]:
        p.append(text(X(t0), ay + ah + 18, "vétel", 11, cls="quiet", anchor="middle"))
    # ---- panel B: monthly cost vs load ----
    bx, by, bw, bh = 450, 104, 270, 206
    XB = lambda u: bx + bw * u
    YB = lambda c: by + bh * (1 - c / 0.9)
    p.append(text(410, 66, "B. Havi költség a terhelés függvényében", 13, 600))
    blocks = [(0.0, 0.20), (1 / 3, 0.30), (2 / 3, 0.40)]   # load where a block is needed, capex per month
    def capex(u):
        c = 0
        for u0, v in blocks:
            if u >= u0:
                c = v
        return c
    opex = lambda u: 0.10 + 0.08 * u
    cloud = lambda u: 0.04 + 0.80 * u
    us = [i / 300 for i in range(301)]
    # opex band on top of capex
    topb = [(XB(u), YB(capex(u) + opex(u))) for u in us]
    lowb = [(XB(u), YB(capex(u))) for u in us]
    p.append('<path d="M' + "L".join(f"{x:.1f} {y:.1f}" for x, y in topb + lowb[::-1]) + 'Z" class="tint"/>')
    p.append(path(f"M{bx} {by + bh}H{bx + bw + 14}", m))
    p.append(path(f"M{bx} {by + bh}V{by - 14}", m))
    p.append(text(bx + bw + 14, by + bh + 18, "terhelés (forgalom)", 11.5, cls="quiet", anchor="end"))
    p.append(text(bx + 6, by - 18, "havi költség", 11.5, cls="quiet"))
    def stair(f):
        out, prev = "", None
        for u in us:
            v = f(u)
            if prev is None:
                out = f"M{XB(u):.1f} {YB(v):.1f}"
            elif abs(v - prev) > 0.02:
                out += f"V{YB(v):.1f}"
            out += f"L{XB(u):.1f} {YB(v):.1f}"
            prev = v
        return out
    p.append(path(stair(capex), cls="acc", width=1.5, dash="5 3"))
    p.append(path(stair(lambda u: capex(u) + opex(u)), cls="acc", width=2))
    p.append(f'<path d="M{XB(0):.1f} {YB(cloud(0)):.1f}L{XB(1):.1f} {YB(cloud(1)):.1f}" fill="none" class="c2s" stroke-width="2"/>')
    # crossover at u = 0.5
    xc, yc = XB(0.5), YB(cloud(0.5))
    p.append(f'<circle cx="{xc:.1f}" cy="{yc:.1f}" r="4" class="ink"/>')
    p.append(text(xc - 6, yc - 10, "megtérülési pont", 11, 600, anchor="end"))
    p.append(text(XB(0.80) - 4, YB(cloud(0.80)) - 8, "felhő (opex)", 11.5, 600, cls="c2", anchor="end"))
    p.append(text(XB(0.80), YB(0.40 + opex(0.8)) - 8, "saját: összesen", 11.5, 600, cls="acct"))
    p.append(text(XB(0.70), YB(0.40) + 16, "capex", 11, cls="quiet"))
    p.append(text(XB(0.02), YB(0.20) + 16, "capex", 11, cls="quiet"))
    p.append(text(XB(0.80), YB(0.40) - 7, "opex", 11, cls="quiet"))
    p.append(text(24, 352, "A: a hardver blokkokban érkezik, és a terhelés előtt kell megvenni, így mindig van tétlen kapacitás vagy hiány.", 11.5, cls="quiet"))
    p.append(text(24, 370, "B: a megtérülési pont alatt vagy hullámzó terhelésnél a bérlés olcsóbb, tartósan nagy terhelésnél többnyire a birtoklás.", 11.5, cls="quiet"))
    p.append(text(24, 388, "Saját: capex (szaggatott: a hardver havi része) + opex (árnyékolt: személyzet, áram, hely). Szemléltető alakok, nem árak.", 11.5, cls="quiet"))
    return svg(760, 406, title, "\n".join(p))


# ---------------- 8. Risk matrix ----------------
def risk_matrix():
    m = "rm"
    title = "A kockázat (valószínűség × hatás) dönti el, mire költsünk a rendelkezésre állásból"
    p = [f"<defs>{marker(m, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    impacts = ["elhanyagolható", "kisebb", "súlyos", "katasztrofális"]
    likes = ["gyakori", "lehetséges", "valószínűtlen", "ritka"]          # top to bottom
    x0, y0, cw, ch = 150, 70, 146, 64
    for r, lk in enumerate(likes):
        for c, im in enumerate(impacts):
            score = (4 - r) * (c + 1)            # 1..16
            kind = "bad" if score >= 8 else ("c2" if score >= 4 else "tint")
            p.append(rect(x0 + c * cw, y0 + r * ch, cw, ch, kind, rx=0))
        p.append(text(x0 - 10, y0 + r * ch + ch / 2 + 4, lk, 12, 600, anchor="end"))
    for c, im in enumerate(impacts):
        p.append(text(x0 + c * cw + cw / 2, y0 + 4 * ch + 18, im, 12, 600, anchor="middle"))
    p.append(text(x0 + 2 * cw, y0 + 4 * ch + 40, "hatás (kár eseményenként) →", 12, cls="quiet", anchor="middle"))
    p.append(f'<text x="34" y="{y0 + 2 * ch}" font-size="12" class="quiet" text-anchor="middle" transform="rotate(-90 34 {y0 + 2 * ch})">valószínűség →</text>')

    def item(r, c, lines, dy=0, cls="ink"):
        out = []
        for i, s in enumerate(lines):
            out.append(text(x0 + c * cw + cw / 2, y0 + r * ch + 26 + dy + i * 15, s, 11, 600 if i == 0 else 400,
                            cls=cls if i == 0 else "quiet", anchor="middle"))
        return out
    p += item(0, 0, ["összeomló folyamat", "magától újraindul"])
    p += item(1, 2, ["lemezhiba", "(egyetlen lemez)"])
    p += item(1, 1, ["lemezhiba", "RAID 1-gyel"], cls="acct")
    p += item(1, 3, ["konfigurációs hiba", "minden szerveren"])
    p += item(2, 2, ["áramszünet", "a szerverteremben"])
    p += item(2, 3, ["zsarolóvírus", "mindent titkosít"])
    p += item(3, 3, ["tűz vagy árvíz", "az adatközpontban"])
    p += item(3, 0, ["kiesik egy ventilátor", "a másik tovább hűt"])
    # mitigation arrow: RAID moves the disk risk left
    ya = y0 + ch + 56
    p.append(f'<path d="M{x0 + 2 * cw + 30} {ya}H{x0 + cw + cw - 8}" fill="none" class="acc" stroke-width="1.5" marker-end="url(#{m})"/>')
    p.append(text(x0 + 2 * cw + 34, ya + 4, "csökkentés", 10.5, 600, cls="acct"))
    ly = y0 + 4 * ch + 68
    p.append(rect(24, ly - 11, 14, 14, "tint", rx=2)); p.append(text(44, ly + 1, "alacsony: elfogadni, figyelni", 11.5))
    p.append(rect(230, ly - 11, 14, 14, "c2", rx=2)); p.append(text(250, ly + 1, "közepes: csökkenteni, ahol olcsó", 11.5))
    p.append(rect(460, ly - 11, 14, 14, "bad", rx=2)); p.append(text(480, ly + 1, "magas: csökkenteni, áthárítani, elkerülni", 11.5))
    p.append(text(24, ly + 30, "A csökkentés elmozdítja a kockázatot: RAID 1 tükörrel a lemezhiba ugyanolyan valószínű, de kisebb a hatása.", 11.5, cls="quiet"))
    return svg(760, ly + 50, title, "\n".join(p))


# ---------------- 9. Image, container, volume ----------------
def mono(x, y, s, size=12, cls="ink", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" text-anchor="{anchor}" '
            f'style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{esc(s)}</text>')


def image_container():
    m, ma = "ic", "ica"
    title = "A kép a csak olvasható tervrajz; minden konténer egy vékony írható réteget ad hozzá"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # Containerfile
    p.append(text(24, 66, "Containerfile", 13, 600))
    lines = ["FROM scratch", "COPY tool /bin/tool", "RUN tool mkdir /data", "COPY app.conf /etc/",
             "EXPOSE 8080", "USER 1000", "WORKDIR /data", "CMD tool serve"]
    ly0, lstep = 96, 26
    p.append(rect(18, 76, 190, len(lines) * lstep + 10, "tint", rx=6))
    for i, s in enumerate(lines):
        p.append(mono(28, ly0 + i * lstep, s, 12))
    # image stack (bottom-up)
    sx, sw = 270, 200
    p.append(text(sx, 66, "Kép (csak olvasható, közös)", 13, 600))
    cfg_y, cfg_h = 80, 76
    p.append(f'<rect x="{sx}" y="{cfg_y}" width="{sw}" height="{cfg_h}" rx="4" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="4 3"/>')
    p.append(text(sx + sw / 2, cfg_y + 20, "konfiguráció (nincs fájl):", 11.5, 600, anchor="middle"))
    p.append(text(sx + sw / 2, cfg_y + 38, "port 8080, felhasználó 1000,", 11, cls="quiet", anchor="middle"))
    p.append(text(sx + sw / 2, cfg_y + 54, "munkakönyvtár /data,", 11, cls="quiet", anchor="middle"))
    p.append(text(sx + sw / 2, cfg_y + 70, "parancs: tool serve", 11, cls="quiet", anchor="middle"))
    layers = [("/etc/app.conf", "3. réteg"), ("/data, UID 1000", "2. réteg"), ("/bin/tool", "1. réteg")]
    lh = 36
    ly = cfg_y + cfg_h + 10
    for i, (n, tag) in enumerate(layers):
        y = ly + i * (lh + 4)
        p.append(rect(sx, y, sw, lh, "acc", rx=4))
        p.append(text(sx + 12, y + 23, n, 12, 600))
        p.append(text(sx + sw - 10, y + 23, tag, 11, cls="quiet", anchor="end"))
    base_y = ly + 3 * (lh + 4)
    p.append(text(sx + sw / 2, base_y + 16, "üres alap (FROM scratch)", 11, cls="quiet", anchor="middle"))
    # arrows from Containerfile lines to layers / config
    def arrow_to(line_i, ty):
        yy = ly0 + line_i * lstep - 4
        return path(f"M210 {yy}C240 {yy} 240 {ty} {sx - 4} {ty}", m)
    p.append(arrow_to(1, ly + 2 * (lh + 4) + lh / 2))
    p.append(arrow_to(2, ly + 1 * (lh + 4) + lh / 2))
    p.append(arrow_to(3, ly + lh / 2))
    for i in (4, 5, 6, 7):
        yy = ly0 + i * lstep - 4
        p.append(path(f"M210 {yy}C236 {yy} 236 {cfg_y + cfg_h / 2} {sx - 4} {cfg_y + cfg_h / 2}", m, dash="3 3"))
    # containers
    cx, cw = 540, 196
    p.append(text(cx, 66, "Konténerek (példányok)", 13, 600))
    for j, (name, wl, yy) in enumerate([("c1 konténer", "írható réteg: notes.txt", 80),
                                        ("c2 konténer", "írható réteg: (üres)", 186)]):
        p.append(f'<rect x="{cx}" y="{yy}" width="{cw}" height="84" rx="6" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="5 3"/>')
        p.append(text(cx + 10, yy + 20, name, 12, 600))
        p.append(rect(cx + 10, yy + 30, cw - 20, 24, "c2", rx=3))
        p.append(text(cx + cw / 2, yy + 47, wl, 11, anchor="middle"))
        p.append(text(cx + cw / 2, yy + 72, "+ alatta a kép rétegei", 11, cls="quiet", anchor="middle"))
        p.append(path(f"M{sx + sw + 4} {ly + 40 + j * 30}C{505} {ly + 40 + j * 30} {505} {yy + 64} {cx - 4} {yy + 64}", m))
    p.append(text(506, ly + 14, "futtatás", 11, 600, cls="quiet", anchor="middle"))
    # volume
    vy = 300
    p.append(rect(cx, vy, cw, 46, "tint", rx=6))
    p.append(text(cx + cw / 2, vy + 19, "appdata kötet", 12, 600, anchor="middle"))
    p.append(text(cx + cw / 2, vy + 36, "minden konténert túlél", 11, cls="quiet", anchor="middle"))
    p.append(path(f"M{cx + cw / 2} {vy - 2}V{186 + 86}", ma, cls="acc", width=1.5))
    p.append(text(cx + cw / 2 + 8, vy - 12, "csatolva: /data", 11, 600, cls="acct"))
    p.append(text(24, 386, "A konténerben írt adat a saját írható rétegébe kerül, és elvész, amikor a konténert eltávolítják;", 11.5, cls="quiet"))
    p.append(text(24, 404, "a megmaradó adatok (adatbázis, feltöltések) kötetre valók. Folytonos nyilak: fájlokat hozzáadó építési lépések.", 11.5, cls="quiet"))
    return svg(760, 424, title, "\n".join(p))



if __name__ == "__main__":
    for name, f in [("nines", nines), ("mtbf-mttr", mtbf), ("branching-vocabulary", vocab),
                    ("enterprise-linux-family", ecosystem), ("support-lifecycles", lifecycle),
                    ("container-images", containers), ("cloud-vs-own", cloud_costs),
                    ("risk-matrix", risk_matrix), ("image-container-volume", image_container)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
