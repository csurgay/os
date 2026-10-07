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
        return f"{minutes / 1440:.1f} days"
    if minutes >= 60:
        return f"{minutes / 60:.1f} hours"
    return f"{minutes:.1f} min"


# ---------------- 1. The nines ----------------
def nines():
    title = "Each extra nine cuts the allowed downtime tenfold"
    year = 365.25 * 24 * 60
    rows = [("99%", 0.99), ("99.9%", 0.999), ("99.99%", 0.9999), ("99.999%", 0.99999)]
    x0, x1 = 150, 600
    lo, hi = math.log10(1), math.log10(10000)       # 1 minute .. 10,000 minutes
    X = lambda m: x0 + (x1 - x0) * (math.log10(m) - lo) / (hi - lo)
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Allowed downtime per year at each availability level (logarithmic scale)", 11.5, cls="quiet")]
    top, step = 92, 44
    for t, lab in [(1, "1 min"), (10, "10 min"), (60, "1 hour"), (1440, "1 day"), (10000, "1 week")]:
        x = X(t)
        p.append(f'<line x1="{x:.1f}" y1="{top - 20}" x2="{x:.1f}" y2="{top + 4 * step - 10}" class="grid"/>')
        p.append(text(x, top + 4 * step + 8, lab, 11.5, cls="quiet", anchor="middle"))
    for i, (lab, a) in enumerate(rows):
        y = top + i * step
        m = (1 - a) * year
        p.append(text(24, y + 5, lab, 13, 600))
        kind = "acc" if lab == "99.99%" else "tint"
        p.append(rect(x0, y - 11, X(m) - x0, 22, kind, rx=4))
        p.append(text(X(m) + 10, y + 5, fmt(m), 12.5, 600))
    p.append(text(24, top + 4 * step + 38, "Highlighted: 99.99%, a common target for business-critical services: under an hour of downtime a year.", 11.5, cls="quiet"))
    return svg(760, top + 4 * step + 58, title, "\n".join(p))


# ---------------- 2. MTTF, MTTR, MTBF ----------------
def mtbf():
    m = "mt"
    title = "A system alternates between working and being repaired"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    y, h = 96, 34
    segs = [(40, 250, "up"), (250, 300, "down"), (300, 560, "up"), (560, 600, "down"), (600, 720, "up")]
    for a, b, k in segs:
        kind = "tint" if k == "up" else "bad"
        p.append(rect(a, y, b - a, h, kind, rx=0))
    p.append(text(145, y + 22, "working", 12.5, anchor="middle"))
    p.append(text(430, y + 22, "working", 12.5, anchor="middle"))
    p.append(text(275, y + 54, "failure,", 11.5, cls="bad", anchor="middle"))
    p.append(text(275, y + 70, "repair", 11.5, cls="bad", anchor="middle"))
    p.append(text(580, y + 54, "repair", 11.5, cls="bad", anchor="middle"))
    # annotations
    def span(a, b, yy, lab, cls="acc"):
        out = [f'<path d="M{a} {yy}H{b}" fill="none" class="{cls}" stroke-width="1.5" marker-start="url(#{m})" marker-end="url(#{m})"/>',
               text((a + b) / 2, yy - 8, lab, 12, 600, cls="acct" if cls == "acc" else "ink", anchor="middle")]
        return out
    p += span(300, 560, y - 22, "MTTF: time to failure")
    p += span(560, 600, y + 96, "MTTR", "edge")
    p += span(250, 560, y + 128, "MTBF: from one failure to the next = MTTR + MTTF", "edge")
    p.append(text(24, y + 170, "Averaged over many failures: availability = MTTF / (MTTF + MTTR), the share of time the system is working.", 11.5, cls="quiet"))
    p.append(text(24, y + 188, "When repairs are short, MTBF ≈ MTTF, so availability ≈ MTBF / (MTBF + MTTR).", 11.5, cls="quiet"))
    return svg(760, y + 206, title, "\n".join(p))


# ---------------- 3. Branching vocabulary ----------------
def vocab():
    m, ma = "vb", "vba"
    title = "Branch, merge, fork, upstream, downstream, backport"
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
    p.append(text(24, 170, "project", 11.5, cls="quiet"))
    for (x1, y1), (x2, y2) in zip(up, up[1:]):
        p.append(path(f"M{x1 + r} {y1}H{x2 - r}", m))
    p.append(path(f"M{up[-1][0] + r} 150H{640}", m, dash="4 3"))
    # branch and merge
    p.append(path(f"M{up[1][0] + 12} {150 - 12}L{br[0] - 14} {br[1] + 8}", m))
    p.append(path(f"M{br[0] + 14} {br[1] + 8}L{up[2][0] - 12} {150 - 12}", m, dash="4 3"))
    p.append(text(262, 98, "branch", 11.5, 600, cls="quiet", anchor="end"))
    p.append(text(372, 92, "merge", 11.5, 600, cls="quiet"))
    for x, y in up:
        p += node(x, y)
    p += node(*br)
    # downstream product (fork)
    p.append(text(24, 274, "Downstream", 13, 600))
    p.append(text(24, 290, "product", 11.5, cls="quiet"))
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
    p.append(text(222, 225, "(send the fix back)", 11, cls="quiet"))
    p += node(*dn[0], "acc", "v1")
    p += node(*dn[1], "acc", "v2")
    # old release line + backport
    p.append(path(f"M{dn[0][0]} {270 + r}L{old[0] - 12} {old[1] - 12}", m))
    p += node(*old, "c2", "v1.1")
    p.append(path(f"M{dn[1][0] - 10} {270 + r - 2}C{430} {330} {380} {350} {old[0] + r + 2} {old[1]}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(430, 342, "backport: a fix from the new", 11.5, 600, cls="acct"))
    p.append(text(430, 358, "version, adapted to the old one", 11.5, cls="quiet"))
    p.append(text(dn[1][0] + 22, 262, "patch", 11.5, 600, cls="quiet"))
    # servers: install + update
    sx = 640
    for i, yy in enumerate((236, 300)):
        p.append(rect(sx, yy, 80, 40, "tint", rx=4))
        p.append(text(sx + 40, yy + 25, f"server {i + 1}", 11.5, anchor="middle"))
    p.append(path(f"M{560} 266L{sx - 4} 256", m))
    p.append(text(578, 240, "install", 11.5, 600, cls="quiet"))
    p.append(path(f"M{old[0] + r} {old[1] + 6}C{480} 392 {600} 392 {sx + 40} {344}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(540, 404, "update: apply the fixes to servers in use", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(24, 432, "Solid arrows: history of a code line. Dashed blue: a change carried from one line to another.", 11.5, cls="quiet"))
    return svg(760, 452, title, "\n".join(p))


# ---------------- 4. The Enterprise Linux family, then and now ----------------
def ecosystem():
    m, ma = "ec", "eca"
    title = "In 2020 CentOS moved from after RHEL to before it"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]

    def box(x, y, w, name, sub, kind="tint"):
        return [rect(x, y, w, 52, kind), text(x + w / 2, y + 22, name, 13, 600, anchor="middle"),
                text(x + w / 2, y + 39, sub, 11, cls="quiet", anchor="middle")]

    # panel A
    p.append(text(24, 66, "Until 2020", 13, 600))
    ya = 80
    p += box(24, ya, 170, "Fedora", "community, fast-moving")
    p += box(290, ya, 170, "RHEL", "Red Hat, subscription", "acc")
    p += box(556, ya, 180, "CentOS Linux", "free rebuild of RHEL")
    p.append(path(f"M194 {ya + 26}H290", m))
    p.append(text(242, ya + 18, "branch", 11, 600, cls="quiet", anchor="middle"))
    p.append(text(242, ya + 44, "every few years", 10.5, cls="quiet", anchor="middle"))
    p.append(path(f"M460 {ya + 26}H556", m))
    p.append(text(508, ya + 18, "rebuild", 11, 600, cls="quiet", anchor="middle"))
    p.append(text(508, ya + 44, "from sources", 10.5, cls="quiet", anchor="middle"))
    # panel B
    yb = 196
    p.append(f'<line x1="24" y1="{yb - 26}" x2="736" y2="{yb - 26}" class="grid"/>')
    p.append(text(24, yb - 2, "Since 2021", 13, 600))
    yb += 12
    p += box(24, yb, 150, "Fedora", "community")
    p += box(214, yb, 160, "CentOS Stream", "the next RHEL, in public")
    p += box(414, yb, 130, "RHEL", "Red Hat", "acc")
    p.append(path(f"M174 {yb + 26}H214", m))
    p.append(text(194, yb - 8, "branch", 11, 600, cls="quiet", anchor="middle"))
    p.append(path(f"M374 {yb + 26}H414", m))
    p.append(text(394, yb - 8, "release", 11, 600, cls="quiet", anchor="middle"))
    # rebuilds
    rb = [("AlmaLinux", "ABI-compatible (2021)"), ("Rocky Linux", "1:1 rebuild (2021)"), ("Oracle Linux", "rebuild (2006)")]
    for i, (n, sub) in enumerate(rb):
        y = yb - 30 + i * 62
        p += box(600, y, 136, n, sub, "c2")
        if n == "AlmaLinux":   # builds mainly from CentOS Stream since 2023
            p.append(path(f"M374 {yb + 12}C470 {yb - 40} 540 {y + 26} 600 {y + 26}", m, dash="4 3"))
        else:
            p.append(path(f"M544 {yb + 26}C572 {yb + 26} 572 {y + 26} 600 {y + 26}", m))
    # upstream-first
    p.append(path(f"M{479} {yb + 52}C479 {yb + 96} 99 {yb + 96} 99 {yb + 56}", ma, cls="acc", width=1.5, dash="5 3"))
    p.append(text(290, yb + 112, "fixes go upstream first: into Fedora, CentOS Stream and the original projects", 11.5, 600, cls="acct", anchor="middle"))
    p.append(text(24, yb + 150, "Since June 2023, CentOS Stream is the only public source of RHEL-related code; RHEL's own source packages go to", 11.5, cls="quiet"))
    p.append(text(24, yb + 168, "customers and partners. Dashed: AlmaLinux now builds mainly from CentOS Stream, aiming for ABI compatibility.", 11.5, cls="quiet"))
    return svg(760, yb + 188, title, "\n".join(p))


# ---------------- 5. Life cycles ----------------
def lifecycle():
    title = "RHEL promises ten years per major version; Fedora about thirteen months"
    y0, x0, x1 = 2014, 150, 724
    X = lambda t: x0 + (x1 - x0) * (t - y0) / (2036 - y0)
    rows = [  # name, GA, end of full support, end of maintenance, kind
        ("RHEL 7", 2014.45, 2019.6, 2024.5, "rhel"),
        ("RHEL 8", 2019.37, 2024.37, 2029.37, "rhel"),
        ("RHEL 9", 2022.37, 2027.37, 2032.37, "rhel"),
        ("RHEL 10", 2025.37, 2030.37, 2035.37, "rhel"),
        ("CentOS Linux 8", 2019.7, None, 2022.0, "cut"),
        ("Fedora (each)", 2024.8, None, 2025.9, "fed"),
    ]
    top, step = 92, 38
    p = [text(24, 30, title, 15, 600),
         text(24, 50, "Support periods by year (approximate; Red Hat's future dates are subject to change)", 11.5, cls="quiet")]
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
            p.append(text(X(2029.4) + 8, y + 5, "originally planned to 2029", 11, cls="quiet"))
        else:
            p.append(rect(X(ga), y - 10, X(end) - X(ga), 20, "c2", rx=3))
            p.append(text(X(end) + 8, y + 5, "≈ 13 months", 11, cls="quiet"))
    ly = ya + 40
    p.append(rect(24, ly - 11, 14, 14, "acc", rx=2)); p.append(text(44, ly + 1, "full support", 11.5))
    p.append(rect(150, ly - 11, 14, 14, "tint", rx=2)); p.append(text(170, ly + 1, "maintenance support (fixes only)", 11.5))
    p.append(rect(400, ly - 11, 14, 14, "bad", rx=2)); p.append(text(420, ly + 1, "CentOS Linux 8, ended early (Dec 2021)", 11.5))
    return svg(760, ly + 20, title, "\n".join(p))


# ---------------- 6. Containers: images share layers, containers share the kernel ----------------
def containers():
    m = "ct"
    title = "Images bring their own user space; every container shares the host's kernel"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    # left: two images sharing the base layer
    p.append(text(24, 66, "Two images built on the same base", 13, 600))
    bw, bh = 150, 34
    lx = [24, 190]
    labels = [("web app", "billing app"), ("Python packages", "Java runtime")]
    for i, x in enumerate(lx):
        p.append(rect(x, 80, bw, bh, "c2", rx=4)); p.append(text(x + bw / 2, 102, labels[0][i], 12, anchor="middle"))
        p.append(rect(x, 80 + bh + 4, bw, bh, "tint", rx=4)); p.append(text(x + bw / 2, 102 + bh + 4, labels[1][i], 12, anchor="middle"))
        p.append(text(x + bw / 2, 216, f"image {i + 1}", 11.5, 600, cls="quiet", anchor="middle"))
    p.append(rect(24, 80 + 2 * (bh + 4), 316, bh + 8, "acc", rx=4))
    p.append(text(182, 106 + 2 * (bh + 4), "base layer: UBI 9 (one copy on disk)", 12, 600, anchor="middle"))
    p.append(text(24, 262, "Layers are read-only and identified by a hash,", 11.5, cls="quiet"))
    p.append(text(24, 278, "so a shared base is stored and downloaded once.", 11.5, cls="quiet"))
    # right: host with containers
    hx, hy, hw = 400, 66, 336
    p.append(text(hx, hy, "One host running three containers", 13, 600))
    cw = 100
    names = [("UBI 9", "user space"), ("AlmaLinux 9", "user space"), ("Fedora", "user space")]
    for i, (n, sub) in enumerate(names):
        x = hx + i * (cw + 18)
        p.append(rect(x, 80, cw, 86, "c2" if i == 0 else "tint", rx=6))
        p.append(text(x + cw / 2, 104, "app", 11.5, cls="quiet", anchor="middle"))
        p.append(text(x + cw / 2, 128, n, 12, 600, anchor="middle"))
        p.append(text(x + cw / 2, 146, sub, 11, cls="quiet", anchor="middle"))
        p.append(path(f"M{x + cw / 2} 166V{196}", m))
    p.append(rect(hx, 198, hw, 40, "acc", rx=6))
    p.append(text(hx + hw / 2, 223, "one Linux kernel: the host's (e.g. RHEL 9)", 12.5, 600, anchor="middle"))
    p.append(rect(hx, 244, hw, 30, "tint", rx=6))
    p.append(text(hx + hw / 2, 264, "hardware", 12, anchor="middle"))
    p.append(text(24, 314, "Arrows: system calls. Every container talks to the same kernel, so for RHEL/UBI images Red Hat fully supports only a host of the", 11.5, cls="quiet"))
    p.append(text(24, 332, "same major version; other pairings are supported only for ordinary, unprivileged workloads (Red Hat's compatibility matrix).", 11.5, cls="quiet"))
    return svg(760, 352, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("nines", nines), ("mtbf-mttr", mtbf), ("branching-vocabulary", vocab),
                    ("enterprise-linux-family", ecosystem), ("support-lifecycles", lifecycle),
                    ("container-images", containers)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
