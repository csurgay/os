"""Generate the SVG figures for the Access Control lecture (Hungarian version).

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
The examples in the figures are the ones measured in the lecture's demo scripts.
"""
import math
import os

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





HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------- 1. Defence in depth and the reference monitor ----------------
def access_path():
    title = "Minden hozzáférést ellenőrizni kell: a kérés rétegei és a referenciamonitor minden ellenőrzésnél"
    p = [text(24, 30, title, 15, 600), marker("a1"), marker("a1b", "bad")]
    # left: the layers, bottom to top
    p.append(text(24, 62, "egy hálózati kérés egy webszerverhez", 12.5, 600, cls="quiet"))
    layers = [("5. végrehajtás", "a művelet végrehajtódik", "tint"),
              ("4. MAC: SELinux, AppArmor", "rendszerszintű policy; a rootot is köti", "acc"),
              ("3. DAC: módbitek, ACL-ek", "a fájl tulajdonosa dönt", "c2"),
              ("2. a szolgáltatás (démon)", "saját konfiguráció és hitelesítés", "plain"),
              ("1. tűzfal", "mely gépek mely portokat érhetik el", "plain")]
    y = 76
    for i, (name, desc, k) in enumerate(layers):
        p.append(rect(40, y, 300, 50, k, rx=6))
        p.append(text(54, y + 21, name, 12.5, 600))
        p.append(text(54, y + 39, desc, 11, cls="quiet" if k in ("plain", "tint") else "ink"))
        if i:
            p.append(path(f"M190 {y + 10}V{y - 2}", "a1"))
        y += 60
    p.append(path(f"M190 {y + 22}V{y - 8}", "a1", width=1.5))
    p.append(text(190, y + 36, "kérés (pl. GET /index.html)", 11.5, cls="quiet", anchor="middle"))
    p.append(text(40, y + 58, "A kérést az első réteg elutasítja, amelyik nemet mond;", 11, cls="quiet"))
    p.append(text(40, y + 74, "a támadónak minden rétegen át kell jutnia a sikerhez.", 11, cls="quiet"))
    # right: the reference monitor
    x0 = 400
    p.append(text(x0, 62, "a referenciamonitor (egy ellenőrzés, pl. a 3. vagy a 4. réteg)", 12.5, 600, cls="quiet"))
    p.append(rect(x0, 84, 132, 80, "tint"))
    p.append(text(x0 + 66, 106, "alany", 12.5, 600, anchor="middle"))
    p.append(text(x0 + 66, 126, "folyamat: httpd", 11, anchor="middle"))
    p.append(text(x0 + 66, 142, "UID apache", 11, cls="quiet", anchor="middle"))
    p.append(text(x0 + 66, 156, "context: httpd_t", 11, cls="quiet", anchor="middle"))
    p.append(rect(x0 + 172, 84, 132, 80, "acc"))
    p.append(text(x0 + 238, 108, "referencia-", 12.5, 600, anchor="middle"))
    p.append(text(x0 + 238, 126, "monitor", 12.5, 600, anchor="middle"))
    p.append(text(x0 + 238, 148, "(a kernelben)", 11, cls="quiet", anchor="middle"))
    p.append(rect(x0 + 344, 84, 112, 80, "tint"))
    p.append(text(x0 + 400, 106, "objektum", 12.5, 600, anchor="middle"))
    p.append(text(x0 + 400, 126, "index.html", 11, anchor="middle"))
    p.append(text(x0 + 400, 142, "vagy a 80-as port", 11, cls="quiet", anchor="middle"))
    p.append(path(f"M{x0 + 132} 124H{x0 + 170}", "a1", width=1.5))
    p.append(text(x0 + 151, 184, "művelet:", 11, 600, anchor="middle"))
    p.append(text(x0 + 151, 200, "megnyitás, olvasás,", 10.5, cls="quiet", anchor="middle"))
    p.append(text(x0 + 151, 214, "írás, bind …", 10.5, cls="quiet", anchor="middle"))
    p.append(path(f"M{x0 + 304} 116H{x0 + 342}", "a1", width=1.5))
    p.append(text(x0 + 323, 108, "igen", 11, 600, cls="acct", anchor="middle"))
    p.append(path(f"M{x0 + 304} 146C{x0 + 322} 150 {x0 + 330} 170 {x0 + 336} 184", "a1b", cls="bads", width=1.5))
    p.append(text(x0 + 342, 198, "nem: EACCES / EPERM", 11, 600, cls="bad"))
    # policy and log
    p.append(rect(x0 + 172, 226, 132, 50, "c2"))
    p.append(text(x0 + 238, 247, "policy", 12.5, 600, anchor="middle"))
    p.append(text(x0 + 238, 264, "bitek, ACL, szabályok", 10.5, anchor="middle"))
    p.append(path(f"M{x0 + 238} 226V166", "a1"))
    p.append(rect(x0 + 344, 226, 112, 50, "plain"))
    p.append(text(x0 + 400, 247, "auditnapló", 12.5, 600, anchor="middle"))
    p.append(text(x0 + 400, 264, "rögzített tiltások", 10.5, cls="quiet", anchor="middle"))
    p.append(path(f"M{x0 + 400} 204V224", "a1", dash="4 3"))
    # properties
    y = 312
    p.append(text(x0, y, "A referenciamonitor tulajdonságai:", 12, 600))
    props = [("mindig meghívódik", "nem lehet megkerülni (teljes közvetítés)"),
             ("sérthetetlen", "a felhasználói kód nem módosíthatja (kernelmódban fut)"),
             ("ellenőrizhető", "elég kicsi és egyszerű az ellenőrzéshez")]
    for i, (a, b) in enumerate(props):
        p.append(text(x0 + 6, y + 24 + 20 * i, "• " + a + ": ", 11.5, 600))
        p.append(text(x0 + 148, y + 24 + 20 * i, b, 11.5, cls="quiet"))
    return svg(880, 468, title, "\n".join(p))


# ---------------- 2. The DAC check ----------------
def dac_check():
    title = "Így dönt a Linux egy olvasási, írási vagy végrehajtási kérésről: az első egyezés dönt"
    p = [text(24, 30, title, 15, 600), marker("a2")]
    steps = [("1", "Van-e a folyamatnak CAP_DAC_OVERRIDE-ja?", "(a rootnak van)",
              "engedélyezve, a bitek megnézése nélkül", "(végrehajtás: csak ha van beállított x bit)", "acc"),
             ("2", "Effektív UID = a fájl tulajdonosa?", "",
              "a tulajdonos bitjei (user::) döntenek, vége", "akkor is, ha a csoport vagy mások többet kapnának", "c2"),
             ("3", "Van-e névvel megadott user-bejegyzés?", "(csak ACL esetén: user:cons3:…)",
              "az a bejegyzés ÉS a maszk dönt, vége", "", "c2"),
             ("4", "A folyamat a tulajdonos csoportban van,", "vagy az ACL egy névvel megadott csoportjában?",
              "engedélyezve, ha egy illeszkedő csoportbejegyzés", "megadja (ÉS a maszk), különben elutasítva", "c2"),
             ("5", "Különben: mindenki más", "",
              "a mindenki más bitjei (other::) döntenek", "", "c2")]
    y = 56
    for i, (n, q1, q2, a1, a2, k) in enumerate(steps):
        last = i == len(steps) - 1
        p.append(rect(40, y, 340, 56, "tint" if not last else "plain"))
        p.append(text(56, y + 23, f"{n}.  {q1}", 12.5, 600))
        if q2:
            p.append(text(76, y + 42, q2, 11, cls="quiet"))
        p.append(rect(456, y, 384, 56, k))
        p.append(text(470, y + 23, a1, 12.5, 600))
        if a2:
            p.append(text(470, y + 42, a2, 11))
        p.append(path(f"M380 {y + 28}H454", "a2", width=1.5))
        if not last:
            p.append(text(417, y + 22, "igen", 11, 600, cls="acct", anchor="middle"))
            p.append(path(f"M210 {y + 56}V{y + 74}", "a2"))
            p.append(text(220, y + 69, "nem", 11, 600, cls="quiet"))
        y += 76
    y += 6
    p.append(rect(40, y, 800, 74, "plain"))
    p.append(text(56, y + 22, "Példa: -------rwx  john  john  note.txt", 12.5, 600))
    p.append(text(56, y + 42, "john a tulajdonos: a 2. lépés illeszkedik, a tulajdonos bitjei ---, így john nem fér hozzá.", 11.5))
    p.append(text(56, y + 60, "user1 az 5. lépésig semmivel sem illeszkedik: a mindenki más bitjei rwx, így olvashat. A jogok nem adódnak össze.", 11.5))
    p.append(text(40, y + 96, "ACL nélkül nincs 3. lépés, nincsenek névvel megadott csoportok, és maszk sincs; a bitek önmagukban döntenek.", 11.5, cls="quiet"))
    return svg(880, y + 110, title, "\n".join(p))


# ---------------- 3. The 12 permission bits ----------------
def mode_bits():
    title = "Egy fájl módja: 4 típusbit, 3 speciális bit és 9 jogosultságbit"
    p = [text(24, 30, title, 15, 600), marker("a3")]
    cw, x0, y0 = 44, 88, 96
    groups = [("fájltípus", 4, "tint"), ("speciális", 3, "acc"), ("tulajdonos (u)", 3, "c2"), ("csoport (g)", 3, "c2"), ("mindenki más (o)", 3, "c2")]
    labels = ["", "", "", "", "setuid", "setgid", "sticky", "r", "w", "x", "r", "w", "x", "r", "w", "x"]
    weights = ["", "", "", "", "4", "2", "1", "4", "2", "1", "4", "2", "1", "4", "2", "1"]
    example = ["1", "0", "0", "0", "1", "1", "1", "1", "1", "1", "1", "0", "0", "0", "1", "1"]
    x = x0
    i = 0
    for name, n, k in groups:
        p.append(text(x + n * cw / 2, y0 - 22, name, 12, 600, anchor="middle"))
        p.append(path(f"M{x + 2} {y0 - 12}V{y0 - 6}H{x + n * cw - 2}V{y0 - 12}", width=1))
        for j in range(n):
            p.append(rect(x + j * cw, y0, cw, 34, k, rx=0))
            if labels[i]:
                p.append(text(x + j * cw + cw / 2, y0 + 21, labels[i], 10 if len(labels[i]) > 1 else 13, 600, anchor="middle"))
            if weights[i]:
                p.append(text(x + j * cw + cw / 2, y0 + 52, weights[i], 11.5, cls="quiet", anchor="middle"))
            p.append(text(x + j * cw + cw / 2, y0 + 82, example[i], 13, 600, cls="acct" if example[i] == "1" else "quiet", anchor="middle"))
            i += 1
        x += n * cw
    p.append(text(x0 - 12, y0 + 52, "súly", 11, cls="quiet", anchor="end"))
    p.append(text(x0 - 12, y0 + 82, "bitek", 11, cls="quiet", anchor="end"))
    # octal digits for the example
    y1 = y0 + 112
    p.append(text(x0 - 12, y1, "oktális", 11, cls="quiet", anchor="end"))
    p.append(text(x0 + 2 * cw, y1, "közönséges fájl", 12, cls="quiet", anchor="middle"))
    for gi, d in enumerate(["7", "7", "4", "3"]):
        p.append(text(x0 + 4 * cw + gi * 3 * cw + 1.5 * cw, y1, d, 15, 600, anchor="middle"))
    p.append(text(x0 + 4 * cw + 6 * cw, y1 + 26, "chmod 7743 f   →   az ls -l kiírása:   -rwsr-S-wt", 13, 600, anchor="middle"))
    # display rule
    y2 = y1 + 64
    p.append(text(24, y2, "Így mutatja az ls a speciális bitet: egy x helyén osztozik vele", 12.5, 600))
    hdr = ["", "nincs x", "van x"]
    rows = [("nincs speciális bit", "-", "x"), ("setuid / setgid beállítva", "S", "s"), ("sticky beállítva", "T", "t")]
    cx = [40, 260, 380]
    for j, h in enumerate(hdr):
        p.append(text(cx[j] + (0 if j == 0 else 40), y2 + 26, h, 11.5, 600, cls="quiet", anchor="start" if j == 0 else "middle"))
    for r, (a, b, c) in enumerate(rows):
        yy = y2 + 50 + r * 26
        p.append(text(cx[0], yy, a, 12))
        p.append(text(cx[1] + 40, yy, b, 14, 600, cls="bad" if b in "ST" else "ink", anchor="middle"))
        p.append(text(cx[2] + 40, yy, c, 14, 600, cls="acct" if c in "st" else "ink", anchor="middle"))
    p.append(text(500, y2 + 26, "A nagy S vagy T figyelmeztető jel:", 11.5, 600))
    p.append(text(500, y2 + 46, "a speciális bit be van állítva, de a hozzá tartozó", 11.5, cls="quiet"))
    p.append(text(500, y2 + 64, "x nincs, így általában nincs hatása.", 11.5, cls="quiet"))
    p.append(text(500, y2 + 90, "Típusmező: 1000 közönséges, 0100 könyvtár,", 11.5, cls="quiet"))
    p.append(text(500, y2 + 108, "1010 szimbolikus link, 0001 FIFO, 1100 socket,", 11.5, cls="quiet"))
    p.append(text(500, y2 + 126, "0110 blokkeszköz, 0010 karakteres eszköz", 11.5, cls="quiet"))
    return svg(880, y2 + 142, title, "\n".join(p))


# ---------------- 4. ACL entries and the mask ----------------
def acl_mask():
    title = "Egy POSIX ACL: tulajdonosi, csoport- és egyéb osztály, és a csoportosztályt korlátozó maszk"
    p = [text(24, 30, title, 15, 600), marker("a4")]
    p.append(text(90, 62, "a plan.txt a setfacl -m u:cons3:--- és a chmod g-w után", 12.5, 600, cls="quiet"))
    rows = [("user::rw-", "rw-", "az ls -l tulajdonosi hármasa"),
            ("user:cons3:---", "---", None),
            ("group::rw-", "r--", None),
            ("mask::r--", None, "az ls -l csoporthármasa"),
            ("other::r--", "r--", "az ls -l mindenki más hármasa")]
    y = 78
    for i, (e, eff, tag) in enumerate(rows):
        k = "acc" if 1 <= i <= 3 else "tint"
        p.append(rect(90, y, 200, 34, k, rx=4))
        p.append(text(104, y + 22, e, 13, 600))
        if eff is not None:
            p.append(text(306, y + 22, "tényleges:", 11, cls="quiet"))
            p.append(text(380, y + 22, eff, 13, 600, cls="bad" if eff != e.split(":")[-1] else "ink"))
        else:
            p.append(text(306, y + 16, "korlátozza a", 11, cls="quiet"))
            p.append(text(306, y + 30, "fenti három sort", 11, cls="quiet"))
        if tag:
            p.append(path(f"M410 {y + 17}H436", "a4", cls="acc" if i == 3 else "edge"))
            p.append(text(444, y + 22, tag, 11.5, 600 if i == 3 else 400, cls="acct" if i == 3 else "ink"))
        y += 42
    # class brackets
    for (y1, y2, lab) in ((80, 110, "tulajdonosi"), (122, 236, "csoport-"), (248, 278, "egyéb")):
        p.append(path(f"M82 {y1}H76V{y2}H82", width=1))
        p.append(text(70, (y1 + y2) / 2 + 4, lab, 11, cls="quiet", anchor="end"))
        p.append(text(70, (y1 + y2) / 2 + 18, "osztály", 11, cls="quiet", anchor="end"))
    # ls -l string
    lx, ly = 640, 124
    p.append(text(lx, ly - 10, "ls -l plan.txt", 12, 600, cls="quiet"))
    x = lx
    for s_, k in [("-", "tint"), ("rw-", "tint"), ("r--", "acc"), ("r--", "tint"), ("+", "tint")]:
        w = 18 if len(s_) == 1 else 46
        p.append(rect(x, ly, w, 30, k, rx=3))
        p.append(text(x + w / 2, ly + 21, s_, 13.5, 600, anchor="middle"))
        x += w + 4
    p.append(text(lx, 184, "tényleges = bejegyzés ÉS maszk:", 12, 600, cls="acct"))
    p.append(text(lx, 202, "group::rw- ÉS mask::r-- = r--", 11.5))
    # explanations
    y = 300
    p.append(rect(40, y, 800, 74, "plain"))
    p.append(text(56, y + 24, "Ha van ACL, a csoporthármas maga a maszk", 12.5, 600))
    p.append(text(56, y + 44, "Az ls -l és a chmod g=… a maszkot mutatja és állítja, nem a tulajdonos csoport bejegyzését, így egy csak a kilenc bitet", 11.5))
    p.append(text(56, y + 62, "ismerő program (chmod go-rwx) is egyszerre korlátoz minden névvel megadott bejegyzést. A bitek utáni „+”: van ACL.", 11.5))
    y += 88
    p.append(rect(40, y, 800, 92, "plain"))
    p.append(text(56, y + 24, "Alapértelmezett ACL (csak könyvtárakon): sablon, nem ellenőrzés", 12.5, 600))
    p.append(text(56, y + 46, "A default:user:cons3:---, default:group::rwx, … bejegyzések minden új fájl vagy alkönyvtár hozzáférési", 11.5))
    p.append(text(56, y + 64, "ACL-jébe bemásolódnak (az alkönyvtárak magát az alapértelmezett ACL-t is öröklik). Az umask ilyenkor nem számít;", 11.5))
    p.append(text(56, y + 82, "a program által kért mód (fájloknál 0666) viszont korlátozza az eredményt: az új fájl mask::rw- maszkot kap.", 11.5))
    return svg(880, y + 106, title, "\n".join(p))


# ---------------- 5. SELinux type enforcement ----------------
def selinux_te():
    title = "SELinux type enforcement: mindennek címkéje van, és csak a megengedett párok érintkezhetnek"
    p = [text(24, 30, title, 15, 600), marker("a5"), marker("a5b", "bad")]
    # context anatomy
    y = 70
    fields = [("system_u", "felhasználó"), ("system_r", "szerep"), ("httpd_t", "típus (folyamatnál: domain)"), ("s0", "szint (MLS/MCS)")]
    x = 60
    p.append(text(24, 52, "egy SELinux context, ahogy a ps -Z (folyamat) vagy az ls -Z (fájl) mutatja:", 12, 600, cls="quiet"))
    xs = []
    for i, (f, lab) in enumerate(fields):
        w = 12 + len(f) * 9
        k = "acc" if i == 2 else "tint"
        p.append(rect(x, y, w, 30, k, rx=3))
        p.append(text(x + w / 2, y + 20, f, 13.5, 600, anchor="middle"))
        xs.append((x, w, lab))
        x += w
        if i < 3:
            p.append(text(x + 7, y + 20, ":", 14, 600, anchor="middle"))
            x += 14
    for i, (x1, w, lab) in enumerate(xs):
        p.append(path(f"M{x1 + w / 2} {y + 32}V{y + 46}", width=1))
        p.append(text(x1 + (w / 2 if i < 2 else 0), y + 60 + (16 if i == 3 else 0), lab, 11, 600 if i == 2 else 400,
                      cls="acct" if i == 2 else "quiet", anchor="middle" if i < 2 else "start"))
    p.append(text(520, y + 12, "fájl:  system_u:object_r:httpd_sys_content_t:s0", 11.5))
    p.append(text(520, y + 30, "port:  system_u:object_r:http_port_t:s0", 11.5))
    # domains and types
    y0 = 182
    p.append(text(60, y0 - 12, "domainek (folyamatok)", 12, 600, cls="quiet"))
    p.append(text(560, y0 - 12, "típusok (fájlok, portok)", 12, 600, cls="quiet"))
    doms = [("httpd_t", "Apache httpd", y0 + 30), ("mysqld_t", "MariaDB mysqld", y0 + 190)]
    for name, desc, yy in doms:
        p.append(rect(60, yy, 170, 60, "acc"))
        p.append(text(145, yy + 25, name, 13.5, 600, anchor="middle"))
        p.append(text(145, yy + 45, desc, 11, anchor="middle"))
    types = [("http_port_t", "TCP 80, 443, …"), ("httpd_sys_content_t", "/var/www/html"),
             ("user_home_t", "/home/*"), ("mysqld_db_t", "/var/lib/mysql"), ("mysqld_port_t", "TCP 3306")]
    ty = {}
    for i, (name, desc) in enumerate(types):
        yy = y0 + i * 60
        p.append(rect(560, yy, 250, 46, "c2" if "port" in name else "tint"))
        p.append(text(574, yy + 20, name, 12.5, 600))
        p.append(text(574, yy + 37, desc, 11, cls="quiet"))
        ty[name] = yy + 23
    hy, my = doms[0][2] + 30, doms[1][2] + 30
    allow = [(hy - 12, "http_port_t", "name_bind"), (hy + 2, "httpd_sys_content_t", "read"),
             (my - 2, "mysqld_db_t", "read, write"), (my + 12, "mysqld_port_t", "name_bind")]
    for sy, t, lab in allow:
        p.append(path(f"M230 {sy}C390 {sy} 400 {ty[t]} 558 {ty[t]}", "a5", cls="acc", width=1.75))
    for t, lab in (("http_port_t", "name_bind"), ("httpd_sys_content_t", "read"),
                   ("mysqld_db_t", "read, write"), ("mysqld_port_t", "name_bind")):
        p.append(text(548, ty[t] - 7, lab, 10.5, cls="acct", anchor="end"))
    deny = [(hy + 16, "user_home_t"), (hy + 26, "mysqld_db_t"), (my - 16, "httpd_sys_content_t")]
    for sy, t in deny:
        ey = ty[t] + (0 if t == "user_home_t" else 12)
        p.append(path(f"M230 {sy}C380 {sy} 400 {ey} 556 {ey}", "a5b", cls="bads", width=1.25, dash="5 4"))
    yb = y0 + 5 * 60 + 8
    p.append(path(f"M60 {yb}H90", "a5", cls="acc", width=1.75))
    p.append(text(98, yb + 4, "egy allow szabály megengedi", 11.5))
    p.append(path(f"M300 {yb}H330", "a5b", cls="bads", width=1.25, dash="5 4"))
    p.append(text(338, yb + 4, "nincs szabály: tiltva, a root folyamatainak is, és AVC-elutasításként naplózva", 11.5))
    p.append(text(60, yb + 34, "allow httpd_t httpd_sys_content_t:file { read open getattr };", 12.5, 600))
    p.append(text(60, yb + 54, "Ami nincs megengedve, az tilos. Egy eltérített webszerver olvashatja a weboldalakat, de az adatbázisfájlokat nem.", 11.5, cls="quiet"))
    return svg(880, yb + 70, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("access-path", access_path), ("dac-check", dac_check), ("mode-bits", mode_bits),
                     ("acl-mask", acl_mask), ("selinux-te", selinux_te)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
