"""Generate the SVG figures (Hungarian) for the Cognitive Ergonomics and Operating Systems UI lecture.

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




def box(x, y, w, h, fill, rx=4, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{extra}/>'


# ---------------- 1. Colour channels: shades order, hues group ----------------
def colours():
    title = "A világosság sorrendet, a színezet csoportot jelez"
    p = [text(24, 30, title, 15, 600)]
    # panel A: shades of one hue for an ordered quantity
    p.append(text(24, 64, "A. Rendezett adat: árnyalatok", 13, 600))
    p.append(text(24, 82, "Öt folyamat CPU-terhelése: sötétebb = több", 11.5, cls="quiet"))
    shades = ["#dbe7fb", "#a9c6f3", "#6f9fe8", "#3a74d6", "#1d4c9c"]
    loads = ["5%", "18%", "41%", "67%", "93%"]
    for i, (c, l) in enumerate(zip(shades, loads)):
        p.append(box(24 + i * 50, 96, 44, 44, c))
        p.append(text(46 + i * 50, 158, l, 11.5, cls="quiet", anchor="middle"))
    p.append(text(24, 186, "Jelmagyarázat nélkül is sorba rendezhetők.", 11.5, cls="quiet"))
    # panel B: hues for categories
    bx = 300
    p.append(text(bx, 64, "B. Kategóriák: eltérő színezetek", 13, 600))
    p.append(text(bx, 82, "Fájltípusok, ahogy az ls színezi őket", 11.5, cls="quiet"))
    cats = [("#3a74d6", "könyvtár"), ("#2e9e5b", "program"), ("#d23c3c", "archívum"),
            ("#b04ad0", "kép"), ("#1aa6b7", "link")]
    for i, (c, l) in enumerate(cats):
        p.append(box(bx + i * 50, 96, 44, 44, c))
        p.append(text(bx + 22 + i * 50, 158, l, 10.5, cls="quiet", anchor="middle"))
    p.append(text(bx, 186, "Nincs sorrend, csak „azonos vagy eltérő”.", 11.5, cls="quiet"))
    # panel C: rainbow for order - fails
    cx = 576
    p.append(text(cx, 64, "C. Rendezett adat: szivárványskála", 13, 600))
    p.append(text(cx, 82, "Ugyanaz az öt érték, kéktől pirosig", 11.5, cls="quiet"))
    rain = ["#2b4bd6", "#19b5d1", "#2fb34a", "#f2e21b", "#d8322b"]
    for i, c in enumerate(rain):
        p.append(box(cx + i * 36, 96, 30, 44, c))
    p.append(text(cx, 158, "A sorrendet jelmagyarázatból kell tanulni;", 11.5, cls="quiet"))
    p.append(text(cx, 176, "a sárga a legvilágosabb, a lépcsők egyenetlenek,", 11.5, cls="quiet"))
    p.append(text(cx, 194, "és a színtévesztők számára elvész.", 11.5, cls="quiet"))
    return svg(900, 214, title, "\n".join(p))


# ---------------- 2. Simultaneous contrast ----------------
def illusion():
    title = "Az A és a B négyzet pontosan ugyanolyan szürke (#808080)"
    p = [f'<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="0">'
         f'<stop offset="0" stop-color="#111"/><stop offset="1" stop-color="#f2f2f2"/></linearGradient></defs>',
         text(24, 30, title, 15, 600),
         box(24, 50, 560, 150, "url(#g)", rx=6),
         box(104, 95, 60, 60, "#808080", rx=2), box(444, 95, 60, 60, "#808080", rx=2),
         text(134, 132, "A", 16, 700, cls="ink", anchor="middle").replace('class="ink"', 'fill="#000"'),
         text(474, 132, "B", 16, 700, cls="ink", anchor="middle").replace('class="ink"', 'fill="#111"'),
         box(24, 214, 560, 22, "#808080", rx=2),
         text(304, 229, "ugyanez a szürke egyenletes sávon", 11.5, anchor="middle").replace('class="ink"', 'fill="#000"'),
         text(24, 260, "Az érzékelt világosságot a környezethez viszonyítjuk, ezért A világosabbnak látszik B-nél.", 11.5, cls="quiet"),
         text(24, 278, "Módszer: ne bízzunk a szemünkben, hanem mérjük a színeket (contrast.py),", 11.5, cls="quiet"),
         text(24, 296, "és az eredményt valódi felhasználókkal teszteljük.", 11.5, cls="quiet")]
    return svg(608, 314, title, "\n".join(p))


# ---------------- 3. Chunking: numbers and menus ----------------
def chunking():
    title = "Tömbösítés: ugyanaz az információ kevesebb egységben"
    p = [text(24, 30, title, 15, 600)]
    p.append(text(24, 64, "Egy telefonszám", 13, 600))
    p.append(rect(24, 76, 300, 40, "tint", rx=6)); p.append(text(174, 102, "441632960018", 16, 600, anchor="middle"))
    p.append(text(24, 134, "12 számjegy = 12 megjegyzendő egység", 11.5, cls="quiet"))
    p.append(rect(24, 148, 300, 40, "acc", rx=6)); p.append(text(174, 174, "+44  1632  960018", 16, 600, anchor="middle"))
    p.append(text(24, 206, "3 ismerős tömb: ország, körzet, előfizető", 11.5, cls="quiet"))
    mx = 380
    p.append(text(mx, 64, "16 parancsból álló menü", 13, 600))
    cmds = ["Új", "Megnyitás", "Mentés", "Nyomtatás", "Visszavonás", "Kivágás", "Másolás", "Beillesztés", "Nagyítás", "Vonalzó", "Rács", "Teljes képernyő",
            "Súgó", "Keresés", "Frissítések", "Névjegy"]
    for i, c in enumerate(cmds[:8]):
        p.append(text(mx + (i % 2) * 80, 90 + (i // 2) * 18, c, 11.5, cls="quiet"))
    for i, c in enumerate(cmds[8:]):
        p.append(text(mx + (i % 2) * 80, 90 + (4 + i // 2) * 18, c, 11.5, cls="quiet"))
    p.append(text(mx, 248, "lapos: 16 átnézendő elem", 11.5, cls="quiet"))
    gx = mx + 190
    groups = [("Fájl", cmds[0:4]), ("Szerkesztés", cmds[4:8]), ("Nézet", cmds[8:12]), ("Súgó", cmds[12:16])]
    for i, (g, items) in enumerate(groups):
        x = gx + (i % 2) * 110; y = 76 + (i // 2) * 86
        p.append(rect(x, y, 104, 78, "c2" if i == 0 else "tint", rx=6))
        p.append(text(x + 8, y + 18, g, 12.5, 600))
        for j, it in enumerate(items):
            p.append(text(x + 8, y + 34 + j * 12, it, 10.5, cls="quiet"))
    p.append(text(gx, 260, "csoportosítva: 4 címszó, majd 4 elem", 11.5, cls="quiet"))
    return svg(800, 278, title, "\n".join(p))


# ---------------- 4. Grip textures in a GUI ----------------
def grips():
    title = "Recézés a képernyőn: textúrák, amelyek azt mondják: „itt fogd meg”"
    p = [text(24, 30, title, 15, 600)]
    cw = 170
    labels = [("recézett gomb", "forgasd el"), ("átméretező fogó", "húzd a sarkot"), ("húzófogantyú", "helyezd át az elemet"),
              ("görgetőcsúszka", "húzd a görgetéshez")]
    for i, (n, a) in enumerate(labels):
        x = 24 + i * (cw + 14)
        p.append(rect(x, 46, cw, 150, "tint", rx=8))
        p.append(text(x + cw / 2, 180, n, 12.5, 600, anchor="middle"))
        p.append(text(x + cw / 2, 214, "→ " + a, 11.5, cls="quiet", anchor="middle"))
    # knob with crosshatch
    cx, cy = 24 + cw / 2, 108
    p.append(f'<clipPath id="kc"><circle cx="{cx}" cy="{cy}" r="44"/></clipPath>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="44" fill="none" class="edge" stroke-width="2"/>')
    hatch = []
    for k in range(-10, 11):
        o = k * 9
        hatch.append(f"M{cx + o - 60} {cy - 60}L{cx + o + 60} {cy + 60}M{cx + o + 60} {cy - 60}L{cx + o - 60} {cy + 60}")
    p.append(f'<path d="{"".join(hatch)}" class="edge" stroke-width="1" clip-path="url(#kc)"/>')
    # resize grip: window corner with diagonal lines
    x = 24 + (cw + 14)
    p.append(rect(x + 30, 62, 110, 90, "plain", rx=4))
    for k in range(3):
        d = 8 + k * 9
        p.append(f'<path d="M{x + 138 - d} 150L{x + 138} {150 - d}" class="acc" stroke-width="2"/>')
    # drag handle dots
    x = 24 + 2 * (cw + 14)
    p.append(rect(x + 20, 88, 130, 40, "plain", rx=6))
    for r in range(3):
        for c in range(2):
            p.append(f'<circle cx="{x + 34 + c * 8}" cy="{98 + r * 10}" r="2" class="acct"/>')
    p.append(text(x + 56, 113, "listaelem", 12, cls="quiet"))
    # scrollbar with ridges
    x = 24 + 3 * (cw + 14)
    p.append(rect(x + 76, 58, 18, 104, "plain", rx=9))
    p.append(rect(x + 77, 82, 16, 44, "acc", rx=8))
    for k in range(3):
        p.append(f'<path d="M{x + 81} {98 + k * 6}H{x + 89}" class="acc" stroke-width="1.5"/>')
    p.append(text(24, 242, "A textúra jelölő: megmutatja, hol lehetséges a cselekvés, akkor is, ha az egész felület laposnak látszik.", 11.5, cls="quiet"))
    return svg(760, 258, title, "\n".join(p))


# ---------------- 5. One operation, several paths ----------------
def paths():
    m = "pa"
    title = "Egy művelet, több út: a kezdőtől a szakértőig"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    rows = [("Menü: Szerkesztés → Másolás", "látható, semmit sem kell megjegyezni", "leglassabb: 2 célpontra kell mutatni", "plain"),
            ("Helyi menü (jobb kattintás)", "az objektum mellett látható", "közepes", "plain"),
            ("Húzás egérrel (Ctrl+húzás)", "közvetlen manipuláció", "gyors közeli célpontoknál", "plain"),
            ("Billentyűparancs: Ctrl+C", "fel kell idézni", "leggyorsabb, a kéz a billentyűkön marad", "acc")]
    for i, (a, b, c, k) in enumerate(rows):
        y = 52 + i * 52
        p.append(rect(24, y, 250, 40, "tint" if k == "plain" else "acc", rx=6))
        p.append(text(36, y + 25, a, 12.5, 600))
        p.append(text(292, y + 18, b, 11.5, cls="quiet")); p.append(text(292, y + 34, c, 11.5, cls="quiet"))
    p.append(path("M560 60V250", m, width=1.5))
    p.append(text(574, 70, "kezdő", 12, 600)); p.append(text(574, 88, "felismerés,", 11.5, cls="quiet"))
    p.append(text(574, 104, "a menü kiírja a gyorsbillentyűt", 11.5, cls="quiet"))
    p.append(text(574, 232, "szakértő", 12, 600)); p.append(text(574, 250, "felidézés, gyorsaság", 11.5, cls="quiet"))
    p.append(text(24, 278, "A menü a parancs mellé írja a billentyűparancsot, és ezzel meg is tanítja: a szakértővé válás útja be van építve.", 11.5, cls="quiet"))
    return svg(780, 296, title, "\n".join(p))


# ---------------- 6. Affective computing loop ----------------
def affect():
    m = "af"
    title = "Az affektív számítástechnika mint hurok: érzékelés, előrejelzés, módosítás"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    nodes = [(280, 56, "felhasználó érzelmi állapota", "c2"), (520, 150, "érzékelés", "acc"), (280, 244, "előrejelzés", "acc"),
             (40, 150, "módosítás (mit mutasson)", "acc")]
    subs = {"felhasználó érzelmi állapota": "hat a figyelemre, észlelésre, döntésre",
            "érzékelés": "kattintás, időzés, gépelés, arc, hang",
            "előrejelzés": "modell: mi köti le ezt a felhasználót?",
            "módosítás (mit mutasson)": "hírfolyam, értesítés, a válasz hangneme"}
    for x, y, t, k in nodes:
        p.append(rect(x, y, 220, 56, k, rx=8))
        p.append(text(x + 110, y + 24, t, 12.5, 600, anchor="middle"))
        p.append(text(x + 110, y + 42, subs[t], 10.5, cls="quiet", anchor="middle"))
    p.append(path("M500 84C560 90 600 110 620 146", m))
    p.append(path("M620 206C610 240 560 262 504 268", m))
    p.append(path("M278 270C200 266 160 240 150 210", m))
    p.append(path("M150 148C160 110 210 90 276 84", m))
    p.append(text(24, 330, "Ugyanaz a hurok szolgálhatja a felhasználót (az oktatóprogram lelassít, ha a diák frusztrált), vagy kihasználhatja", 11.5, cls="quiet"))
    p.append(text(24, 348, "(a hírfolyam megtanulja, hogy az irigység vagy a FOMO görgetésre készteti). A célfüggvény dönt.", 11.5, cls="quiet"))
    return svg(780, 364, title, "\n".join(p))


# ---------------- 7. Uncanny valley ----------------
def smooth(pts):
    """Catmull-Rom spline through the points, as SVG cubic Beziers."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def uncanny():
    title = "A hátborzongató völgy (Mori, 1970): hipotézis, nem mért törvény"
    p = [text(24, 30, title, 15, 600)]
    X0, W = 90, 560
    zero, A = 230, 130                        # neutral affinity line, amplitude
    p.append(path(f"M{X0} {zero + 120}V{zero - A - 30}", None, width=1.5))
    p.append(path(f"M{X0} {zero}H{X0 + W + 30}", None, width=1.5))
    p.append(f'<g transform="translate(50 {zero - 60}) rotate(-90)">{text(0, 0, "rokonszenv", 12, 600, anchor="middle")}</g>')
    p.append(text(X0 + W + 110, zero + 4, "emberhez való", 12, 600, anchor="end"))
    p.append(text(X0 + W + 110, zero + 20, "hasonlóság →", 12, 600, anchor="end"))
    p.append(text(X0 - 8, zero + 4, "0", 11, cls="quiet", anchor="end"))
    pts = [(0, 0.02), (0.2, 0.22), (0.4, 0.45), (0.55, 0.6), (0.62, 0.62), (0.68, 0.45),
           (0.73, -0.25), (0.8, -0.85), (0.87, -0.2), (0.9, 0.3), (0.93, 0.7), (1.0, 1.0)]
    S = lambda x, y: (X0 + x * W, zero - y * A)
    p.append(f'<path d="{smooth([S(x, y) for x, y in pts])}" fill="none" class="acc" stroke-width="2.5"/>')
    a, b = S(0, 0.02), S(1.0, 1.0)
    p.append(path(f"M{a[0]} {a[1]}L{b[0]} {b[1]}", None, width=1.2, dash="5 5"))
    p.append(text(S(0.36, 0.62)[0], S(0.36, 0.62)[1], "várt: emberibb = rokonszenvesebb", 11, cls="quiet", anchor="end"))
    for (x, y), lab, anc, dy in [((0.05, 0.06), "ipari robot", "start", 22), ((0.62, 0.62), "játék- / kedvencrobot", "end", -12),
                                  ((0.8, -0.85), "\u201emajdnem emberi\u201d", "start", 4), ((1.0, 1.0), "valódi ember", "end", -12)]:
        cx, cy = S(x, y)
        p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" class="c2"/>')
        p.append(text(cx + (12 if anc == "start" else -8), cy + dy, lab, 12, 600, anchor=anc))
    vx, vy = S(0.8, -0.85)
    p.append(text(vx + 12, vy + 20, "a hátborzongató völgy", 11.5, cls="quiet"))
    p.append(text(24, 384, "Mori intuícióból rajzolta a görbét; szerinte a mozgás mélyíti. A későbbi kísérletek bizonyos ingereknél", 11.5, cls="quiet"))
    p.append(text(24, 402, "alátámasztják a mélyedést, de alakja és okai vitatottak. Tanácsa: az első csúcsot célozzuk, ne a teljes hasonlóságot.", 11.5, cls="quiet"))
    return svg(780, 418, title, "\n".join(p))


# ---------------- 8. Timeline of user interfaces ----------------
def timeline():
    title = "Hogyan beszéltek az emberek az operációs rendszerekkel"
    p = [text(24, 30, title, 15, 600)]
    y0, x0, x1 = 300, 40, 900
    yrs = (1960, 2030)
    X = lambda yr: x0 + (x1 - x0) * (yr - yrs[0]) / (yrs[1] - yrs[0])
    p.append(path(f"M{x0} {y0}H{x1}", None, width=1.5))
    for yr in range(1960, 2031, 10):
        p.append(f'<line x1="{X(yr):.1f}" y1="{y0 - 4}" x2="{X(yr):.1f}" y2="{y0 + 4}" class="edge" stroke-width="1.25"/>')
        p.append(text(X(yr), y0 + 20, str(yr), 11, cls="quiet", anchor="middle"))
    lanes = [("Parancssor", 1960, 2030, 60, "plain", ["távgépíró, majd terminál; ma is a rendszergazda eszköze"]),
             ("Asztali GUI", 1973, 2030, 104, "acc", ["Alto 1973, Star 1981, Mac 1984, Windows 95"]),
             ("Toll és PDA", 1993, 2007, 148, "plain", ["Newton 1993, PalmPilot 1996"]),
             ("Érintőképernyős telefon", 2007, 2030, 192, "c2", ["iPhone 2007, Android 2008; lapos dizájn 2013–14"]),
             ("Viselhető, hang, térbeli", 2011, 2030, 236, "plain", ["Siri 2011, Glass 2013, Watch 2015, Vision Pro 2024"])]
    for name, a, b, y, k, notes in lanes:
        p.append(rect(X(a), y, X(b) - X(a), 30, k if k != "plain" else "tint", rx=6))
        p.append(text(X(a) + 8, y + 20, name, 12, 600))
        p.append(text(X(a) - 8, y + 20, notes[0], 11, cls="quiet", anchor="end") if X(a) > 420 else
                 text(X(b) - 8, y + 20, notes[0], 11, cls="quiet", anchor="end"))
    p.append(text(24, 344, "Minden új stílus hozzáadódott, nem helyettesített: a telefon Unix-szerű kernelt rejt, és a parancssor ma is ott van.", 11.5, cls="quiet"))
    return svg(920, 360, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("color-channels", colours), ("simultaneous-contrast", illusion), ("chunking", chunking),
                     ("gui-grips", grips), ("input-paths", paths), ("affective-loop", affect),
                     ("uncanny-valley", uncanny), ("ui-timeline", timeline)]:
        with open(f"{name}.svg", "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
