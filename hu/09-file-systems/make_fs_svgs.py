"""Generate the SVG figures for the File Systems lecture.

Same look as the other lectures' figures: light/dark aware, system font, quiet strokes, one accent.
The numbers in the figures come from the measurements in the lecture (ftlsim.py, the demo scripts).
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



# ---------------- 1. The hard disk ----------------
def hdd():
    title = "A merevlemez: forgó lemezek, mozgó fejek és minden elérés három összetevője"
    p = [text(24, 30, title, 15, 600), marker("a1")]
    # side view
    cx = 170
    p.append(text(cx, 62, "oldalnézet", 12, 600, cls="quiet", anchor="middle"))
    p.append(f'<rect x="{cx - 6}" y="74" width="12" height="190" class="edgef"/>')
    for i, y in enumerate((100, 150, 200, 250)):
        p.append(f'<rect x="{cx - 110}" y="{y - 5}" width="220" height="10" rx="2" class="accf"/>')
        p.append(f'<rect x="{cx - 110}" y="{y - 5}" width="220" height="10" rx="2" fill="none" class="acc" stroke-width="1.5"/>')
        for dy in (-11, 11):
            p.append(path(f"M330 {y + dy}H{cx + 60}", cls="c2s", width=2))
            p.append(f'<circle cx="{cx + 60}" cy="{y + dy}" r="3" class="c2"/>')
    p.append(f'<rect x="326" y="80" width="10" height="190" class="c2"/>')
    p.append(text(cx, 290, "lemezek egy tengelyen (5400–15 000 rpm)", 11.5, cls="quiet", anchor="middle"))
    p.append(text(340, 290, "kar, rajta minden", 11.5, cls="quiet", anchor="start"))
    p.append(text(340, 306, "felülethez egy fej", 11.5, cls="quiet", anchor="start"))
    # top view
    ox, oy = 600, 175
    p.append(text(ox, 62, "egy felület felülnézetben", 12, 600, cls="quiet", anchor="middle"))
    for r in (100, 80, 60, 40):
        p.append(f'<circle cx="{ox}" cy="{oy}" r="{r}" fill="none" class="edge" stroke-width="1.25"/>')
    p.append(f'<circle cx="{ox}" cy="{oy}" r="80" fill="none" class="acc" stroke-width="3"/>')
    p.append(f'<circle cx="{ox}" cy="{oy}" r="8" class="edgef"/>')
    for k in range(16):
        a = k * math.pi / 8
        p.append(path(f"M{ox + 40 * math.cos(a):.1f} {oy + 40 * math.sin(a):.1f}L{ox + 100 * math.cos(a):.1f} {oy + 100 * math.sin(a):.1f}", width=0.8))
    a0, a1 = -math.pi / 8, 0
    p.append(f'<path d="M{ox + 60 * math.cos(a0):.1f} {oy + 60 * math.sin(a0):.1f} A60 60 0 0 1 {ox + 60:.1f} {oy} '
             f'L{ox + 80} {oy} A80 80 0 0 0 {ox + 80 * math.cos(a0):.1f} {oy + 80 * math.sin(a0):.1f}Z" class="c2"/>')
    p.append(text(ox + 112, oy - 64, "sáv", 12, 600, cls="acct"))
    p.append(path(f"M{ox + 108} {oy - 68}L{ox + 62} {oy - 52}", "a1"))
    p.append(text(ox + 112, oy + 2, "szektor", 12, 600))
    p.append(path(f"M{ox + 108} {oy - 2}L{ox + 76} {oy - 14}", "a1"))
    p.append(text(ox, oy + 124, "cilinder = ugyanaz a sáv minden felületen", 11.5, cls="quiet", anchor="middle"))
    # access time
    y = 340
    p.append(text(24, y, "egy véletlen 4 KiB-os olvasás ideje (7200 rpm-es asztali lemez, jellemző értékek)", 12.5, 600))
    parts = [("fejmozgatás: a kar mozgatása", 8.5, "c2"), ("forgás: várakozás a szektorra, átlagosan ½ fordulat", 4.17, "acc"), ("adatátvitel", 0.02, "bad")]
    x, scale = 40, 52
    for name, ms, k in parts:
        w = max(ms * scale, 4)
        p.append(rect(x, y + 14, w, 26, k, rx=3))
        x += w
    p.append(text(40, y + 60, "≈ 8,5 ms fejmozgatás", 11.5, cls="quiet"))
    p.append(text(40 + 8.5 * scale, y + 60, "+ 4,17 ms forgás", 11.5, cls="quiet"))
    p.append(text(40 + 12.67 * scale + 8, y + 32, "+ 0,02 ms adatátvitel  ≈ 12,7 ms", 11.5, 600))
    p.append(text(24, y + 86, "≈ 80 véletlen olvasás másodpercenként, miközben ugyanez a lemez szekvenciálisan 200–280 MB/s-ot ad.", 11.5, cls="quiet"))
    return svg(880, y + 100, title, "\n".join(p))


# ---------------- 2. The SSD ----------------
def ssd():
    title = "Az SSD: egy vezérlő sok, párhuzamosan dolgozó NAND flash chip előtt"
    p = [text(24, 30, title, 15, 600), marker("a2")]
    p.append(rect(24, 60, 120, 210, "tint"))
    p.append(text(84, 90, "gazdagép", 13, 600, anchor="middle"))
    p.append(text(84, 112, "SATA, SAS", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 128, "vagy NVMe", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 144, "PCIe-n", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 180, "logikai blokkokat", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 196, "(LBA-kat) lát", 11.5, cls="quiet", anchor="middle"))
    p.append(path("M144 165H184", "a2"))
    p.append(rect(184, 60, 230, 210, "acc"))
    p.append(text(299, 86, "vezérlő (firmware)", 13, 600, anchor="middle"))
    for i, s in enumerate(["flash-fordítóréteg (FTL):", "logikai lap → fizikai lap", "szemétgyűjtés", "kopáskiegyenlítés", "hibajavítás (ECC)", "hibásblokk-kezelés"]):
        p.append(text(200, 112 + 22 * i, ("• " if i != 1 else "   ") + s, 11.5, 600 if i == 0 else 400))
    p.append(rect(200, 234, 198, 26, "c2", rx=4))
    p.append(text(299, 252, "DRAM: leképezési tábla, cache", 11, anchor="middle"))
    # channels and dies
    for ch in range(4):
        y = 70 + ch * 50
        p.append(path(f"M414 {y + 15}H452", "a2"))
        p.append(text(433, y + 8, f"cs. {ch}", 10, cls="quiet", anchor="middle"))
        for d in range(3):
            x = 456 + d * 74
            p.append(rect(x, y, 66, 30, "plain", rx=4))
            p.append(text(x + 33, y + 19, "NAND-lapka", 10.5, anchor="middle"))
    p.append(text(567, 288, "csatornák × lapkák: a kérések párhuzamosan futnak", 11.5, cls="quiet", anchor="middle"))
    # inside a die
    y0 = 320
    p.append(text(24, y0, "egy lapka belseje", 12.5, 600))
    for b in range(4):
        x = 40 + b * 150
        p.append(rect(x, y0 + 14, 132, 96, "plain", rx=4))
        p.append(text(x + 66, y0 + 30, f"{b}. blokk" if b < 3 else "… blokk", 11, 600, anchor="middle"))
        for r in range(4):
            cls = ["accf", "badf", "accf", "tint"][(r + b) % 4] if b < 3 else "tint"
            p.append(f'<rect x="{x + 8}" y="{y0 + 40 + r * 16}" width="116" height="13" class="{cls}"/>')
    p.append(rect(660, y0 + 14, 14, 13, "acc", rx=0)); p.append(text(680, y0 + 25, "érvényes lap", 11))
    p.append(f'<rect x="660" y="{y0 + 36}" width="14" height="13" class="badf"/>'); p.append(text(680, y0 + 47, "érvénytelen (elavult) lap", 11))
    p.append(f'<rect x="660" y="{y0 + 58}" width="14" height="13" class="tint"/>'); p.append(text(680, y0 + 69, "törölt lap", 11))
    p.append(text(24, y0 + 136, "olvasás és programozás (írás): egy lap, 4–16 KiB, néhányszor 10 µs-tól 1 ms-ig   ·   törlés: egy egész, több száz lapos blokk, több ms", 11.5, cls="quiet"))
    p.append(text(24, y0 + 154, "Egy lapot nem lehet a helyén felülírni: az új változat egy törölt lapra kerül, a régi pedig érvénytelenné válik.", 11.5, cls="quiet"))
    return svg(880, y0 + 168, title, "\n".join(p))


# ---------------- 3. Write amplification (simulated) ----------------
def write_amp():
    title = "Írásamplifikáció a tartalék flash függvényében (szimuláció, ftlsim.py, véletlen 4 KiB-os írások)"
    spare = [7, 12, 20, 28, 40, 50]
    wa = [6.71, 4.09, 2.56, 1.90, 1.42, 1.21]
    x0, x1, y0, y1 = 80, 760, 300, 60
    X = lambda v: x0 + (x1 - x0) * (v - 5) / 47
    Y = lambda v: y0 - (y0 - y1) * (v - 1) / 6.5
    p = [text(24, 30, title, 15, 600)]
    for v in (1, 2, 3, 4, 5, 6, 7):
        p.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" class="grid"/>')
        p.append(text(x0 - 8, Y(v) + 4, f"{v}×", 10.5, cls="quiet", anchor="end"))
    for s in spare:
        p.append(text(X(s), y0 + 18, f"{s}%", 10.5, cls="quiet", anchor="middle"))
    p.append(text((x0 + x1) / 2, y0 + 38, "a nyers flash gazdagép elől elrejtett hányada (tartalékterület, over-provisioning)", 11.5, cls="quiet", anchor="middle"))
    pts = " ".join(f"{X(s):.1f},{Y(v):.1f}" for s, v in zip(spare, wa))
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    for s, v in zip(spare, wa):
        p.append(f'<circle cx="{X(s):.1f}" cy="{Y(v):.1f}" r="4" class="acct"/>')
        p.append(text(X(s) + 8, Y(v) - 8, f"{v:.2f}".replace(".", ","), 11, 600))
    p.append(text(24, 370, "A gazdagép minden 4 KiB-jára egy majdnem tele SSD 6–7-szer annyi flasht írhat, mert a szemétgyűjtés átmásolja az érvényes lapokat.", 11.5, cls="quiet"))
    p.append(text(24, 388, "Több tartalék flash (vagy TRIM, amely közli az SSD-vel, mely lapok szabadok) csökkenti; szekvenciális írásnál 1 közelében marad.", 11.5, cls="quiet"))
    return svg(800, 402, title, "\n".join(p))


# ---------------- 4. The layers ----------------
def layers():
    title = "A rendszerhívástól az eszközig: a tárolási verem rétegei Linuxon"
    p = [text(24, 30, title, 15, 600), marker("a4")]
    rows = [("alkalmazás", "open() read() write() close() rename() fsync() …", "tint"),
            ("virtuális fájlrendszer (VFS)", "egy felület minden fájlrendszerhez; dentry- és inode-gyorsítótár", "acc"),
            ("lap-gyorsítótár", "fájladatok a RAM-ban; az írás késleltetett (visszaírás)", "c2"),
            ("fájlrendszer", "ext4 · XFS · Btrfs · vfat · ntfs3 · tmpfs · proc · NFS …", "acc"),
            ("blokkréteg", "számozott blokkokra vonatkozó kérések; összevonás és I/O-ütemezés", "tint"),
            ("eszközmeghajtó", "NVMe · SATA (AHCI) · SCSI · virtio-blk · USB-háttértár", "tint"),
            ("háttértár", "SSD (flash + FTL) vagy merevlemez (lemezek + firmware)", "c2")]
    y = 54
    for i, (name, desc, k) in enumerate(rows):
        p.append(rect(60, y, 760, 42, k, rx=6))
        p.append(text(76, y + 26, name, 13, 600))
        p.append(text(300, y + 26, desc, 12, cls="quiet" if k == "tint" else "ink"))
        if i < len(rows) - 1:
            p.append(path(f"M440 {y + 42}V{y + 54}", "a4"))
        y += 54
    p.append(text(826, 80, "felhasználói", 11, cls="quiet", anchor="start"))
    p.append(text(826, 93, "tér", 11, cls="quiet", anchor="start"))
    p.append(path("M40 102H850", cls="edge", width=1, dash="5 4"))
    p.append(text(826, 120, "kernel", 11, cls="quiet", anchor="start"))
    p.append(text(24, y + 8, "A pszeudo-fájlrendszerek (proc, sysfs, tmpfs) a VFS-nél vagy a lap-gyorsítótárnál megállnak: nincs alattuk eszköz.", 11.5, cls="quiet"))
    return svg(900, y + 22, title, "\n".join(p))


# ---------------- 5. The inode ----------------
def inode():
    title = "A könyvtárbejegyzés nevet ad egy inode-nak; az inode leírja a fájlt, és megtalálja az adatait"
    p = [text(24, 30, title, 15, 600), marker("a5")]
    p.append(rect(24, 60, 170, 96, "tint"))
    p.append(text(36, 82, "könyvtárbejegyzés", 12.5, 600))
    p.append(text(36, 106, "név: photo.jpg", 12))
    p.append(text(36, 126, "inode-sorszám: 19", 12, 600, cls="acct"))
    p.append(path("M194 120H236", "a5"))
    p.append(rect(236, 60, 250, 286, "acc"))
    p.append(text(250, 82, "19-es inode (ext4-ben 256 bájt)", 12.5, 600))
    fields = ["típus és jogosultságok (rw-r--r--)", "tulajdonos (uid) és csoport (gid)", "méret: 307 200 bájt", "linkszám: 1",
              "idők: access, modify, change, birth", "jelzőbitek (extentek, …)", "", "hol vannak az adatok:",
              "ext2/ext3: blokkmutatók  ↗", "ext4: extentek  ↘"]
    for i, f in enumerate(fields):
        if f:
            p.append(text(250, 106 + 20 * i, f, 11.5, 600 if f.startswith("hol") else 400))
    p.append(text(250, 330, "név nincs: a nevek a könyvtárakban élnek", 11.5, cls="quiet"))
    # classic block map
    p.append(text(520, 70, "klasszikus Unix / ext2: blokkmutatók", 12.5, 600))
    labels = ["12 közvetlen mutató", "egyszeresen indirekt", "kétszeresen indirekt", "háromszorosan indirekt"]
    for i, l in enumerate(labels):
        y = 84 + i * 30
        p.append(rect(520, y, 150, 24, "plain", rx=3))
        p.append(text(530, y + 16, l, 11))
        p.append(path(f"M670 {y + 12}H{700 + 20 * i}", "a5"))
        for j in range(i + 1):
            p.append(rect(702 + 20 * i + j * 6, y + 2 - j * 2, 18, 20, "c2" if j == i else "plain", rx=2))
    p.append(text(520, 216, "4 KiB-os blokkok: 48 KiB közvetlenül, aztán indirekt", 11, cls="quiet"))
    p.append(text(520, 232, "blokkonként további 1024 mutató, és így tovább", 11, cls="quiet"))
    # ext4 extents
    p.append(text(520, 268, "ext4: extentek", 12.5, 600))
    p.append(rect(520, 280, 330, 46, "c2", rx=4))
    p.append(text(532, 300, "fájlblokkok 0–74  →  lemezblokkok 2581–2655", 12, 600))
    p.append(text(532, 318, "egy extent: kezdet, hossz (max. 32 768 blokk = 128 MiB)", 11, cls="quiet"))
    p.append(path("M486 300H520", "a5"))
    p.append(text(24, 372, "Legfeljebb 4 extent fér el magában az inode-ban; a nagyobb vagy fragmentált fájlok extentblokkokból álló kis fát kapnak.", 11.5, cls="quiet"))
    return svg(880, 388, title, "\n".join(p))


# ---------------- 6. Hard and symbolic links ----------------
def links():
    title = "Hard link: második név ugyanahhoz az inode-hoz.  Szimbolikus link: elérési utat tartalmazó kis fájl"
    p = [text(24, 30, title, 15, 600), marker("a6")]
    p.append(rect(24, 60, 210, 150, "tint"))
    p.append(text(36, 82, "a /mnt/lab könyvtár", 12.5, 600))
    rows = [("notes.txt", "12"), ("hard.txt", "12"), ("soft.txt", "13")]
    for i, (n, ino) in enumerate(rows):
        y = 104 + 34 * i
        p.append(rect(36, y - 16, 186, 26, "plain", rx=3))
        p.append(text(46, y + 2, n, 12))
        p.append(text(210, y + 2, ino, 12, 600, cls="acct", anchor="end"))
    p.append(path("M222 101C280 101 300 112 330 118", "a6", cls="acc", width=1.8))
    p.append(path("M222 135C280 135 300 128 330 124", "a6", cls="acc", width=1.8))
    p.append(path("M222 169C280 169 300 210 330 226", "a6", cls="c2s", width=1.8))
    p.append(rect(330, 90, 200, 70, "acc"))
    p.append(text(342, 112, "12-es inode, közönséges fájl", 12, 600))
    p.append(text(342, 132, "linkszám: 2", 12))
    p.append(text(342, 150, "méret: 19", 11.5, cls="quiet"))
    p.append(path("M530 125H586", "a6"))
    p.append(rect(586, 104, 190, 42, "plain", rx=4))
    p.append(text(600, 130, "\"hello, file system\"", 12))
    p.append(rect(330, 196, 200, 64, "c2"))
    p.append(text(342, 218, "13-as inode, szimb. link", 12, 600))
    p.append(text(342, 240, "tartalma: \"notes.txt\"", 12))
    p.append(text(550, 216, "az elérési utat minden használatkor újra feloldja:", 11.5, cls="quiet"))
    p.append(text(550, 232, "az rm notes.txt után a link lóg", 11.5, cls="quiet"))
    # the symlink's content leads back into name lookup, to the NAME notes.txt (not to inode 12)
    p.append(path("M400 260V276H12V101H34", "a6", cls="c2s", width=1.4, dash="5 4"))
    p.append(text(412, 280, "a tárolt elérési utat újra feloldja, a névtől kezdve", 11, cls="c2"))
    rows2 = [("", "hard link", "szimbolikus link"), ("mire mutat", "egy inode-ra (sorszám szerint)", "egy elérési útra (név szerint)"),
             ("saját inode", "nincs: ugyanaz az inode, linkszám + 1", "van, „symlink” típusú"),
             ("a cél törlése", "az adat marad, amíg az utolsó link is el nem tűnik", "a link lóg"),
             ("másik fájlrendszer", "lehetetlen (az inode-sorszámok helyiek)", "lehetséges"),
             ("könyvtárak", "nem megengedett (ciklusokat hozna létre)", "megengedett")]
    y = 316
    for i, (a, b, c) in enumerate(rows2):
        w = 600 if i == 0 else 400
        p.append(text(36, y + 20 * i, a, 11.5, 600))
        p.append(text(200, y + 20 * i, b, 11.5, w))
        p.append(text(560, y + 20 * i, c, 11.5, w))
    return svg(880, y + 20 * len(rows2) + 8, title, "\n".join(p))


# ---------------- 7. Directories ----------------
def directory():
    title = "A könyvtár (név, inode) bejegyzésekből álló fájl: kicsiben lista, nagyban hasítófa"
    p = [text(24, 30, title, 15, 600), marker("a7")]
    p.append(text(24, 62, "lineáris lista (ext2, FAT, ext4 kis könyvtárakhoz): keresés az elejétől", 12.5, 600))
    entries = [("2", "12", "."), ("2", "12", ".."), ("11", "20", "lost+found"), ("14", "20", "host-link"), ("12", "16", "hard.txt"),
               ("13", "16", "soft.txt"), ("15", "12", "dir"), ("19", "3976", "photo.jpg")]
    x = 24
    for ino, rl, name in entries:
        w = 52 + 6 * len(name)
        p.append(rect(x, 74, w, 50, "plain", rx=3))
        p.append(text(x + 6, 92, f"inode {ino}", 10.5, cls="quiet"))
        p.append(text(x + 6, 108, f"hossz {rl}", 10.5, cls="quiet"))
        p.append(text(x + 6, 120, name, 11, 600))
        x += w + 4
    p.append(text(24, 144, "Minden bejegyzés tárolja a hosszát; a törölt bejegyzést elnyeli az előző, a helye újra felhasználható. Keresés: O(n).", 11.5, cls="quiet"))
    y0 = 180
    p.append(text(24, y0, "hasítófa (ext4 htree; az XFS és az NTFS B+ fát használ): a név hasítása, majd a fa követése", 12.5, 600))
    p.append(rect(320, y0 + 16, 240, 76, "acc"))
    p.append(text(440, y0 + 36, "gyökérblokk", 12, 600, anchor="middle"))
    p.append(text(440, y0 + 56, "hash 0x00000000 → 1. blokk", 11, anchor="middle"))
    p.append(text(440, y0 + 72, "hash 0x2092d826 → 6. blokk  …", 11, anchor="middle"))
    for i, (lab, x) in enumerate([("1. levélblokk", 60), ("6. levélblokk", 260), ("4. levélblokk", 460), ("… 10 levél", 660)]):
        p.append(rect(x, y0 + 130, 160, 50, "plain" if i < 3 else "tint", rx=4))
        p.append(text(x + 80, y0 + 152, lab, 11.5, 600, anchor="middle"))
        p.append(text(x + 80, y0 + 170, "az adott hash-tartomány" if i < 3 else "", 10.5, cls="quiet", anchor="middle"))
        p.append(path(f"M440 {y0 + 92}L{x + 80} {y0 + 128}", "a7"))
    p.append(text(24, y0 + 208, "Mérés 2000 fájllal: egy gyökérblokk és 10 levélblokk. Egy keresés a gyökeret és egy levelet olvassa: O(n) helyett O(log n).", 11.5, cls="quiet"))
    return svg(880, y0 + 222, title, "\n".join(p))


# ---------------- 8. FAT16 ----------------
def fat16():
    title = "FAT16: a megmért 32 MiB-os kötet elrendezése, és a C.DAT fájl mint klaszterlánc"
    p = [text(24, 30, title, 15, 600), marker("a8")]
    parts = [("boot", 0, 4, "c2"), ("1. FAT", 4, 64, "acc"), ("2. FAT", 68, 64, "acc"), ("gyökérkvt.", 132, 32, "c2"), ("adatterület: 2., 3., 4., … klaszter", 164, 300, "tint")]
    x = 24
    for name, start, n, k in parts:
        w = {4: 50, 64: 110, 32: 90, 300: 470}[n]
        p.append(rect(x, 54, w, 40, k, rx=3))
        p.append(text(x + w / 2, 79, name, 12, 600, anchor="middle"))
        p.append(text(x, 110, str(start), 10.5, cls="quiet"))
        x += w
    p.append(text(x, 110, "65535", 10.5, cls="quiet", anchor="end"))
    p.append(text(24, 128, "szektorszámok (egyenként 512 bájt); egy klaszter = 4 szektor = 2 KiB", 11.5, cls="quiet"))
    # directory entry
    y = 160
    p.append(rect(24, y, 230, 64, "c2"))
    p.append(text(36, y + 22, "a gyökérkönyvtár 2. bejegyzése", 12, 600))
    p.append(text(36, y + 42, "C.DAT  méret 9000  első 3", 12))
    p.append(path(f"M254 {y + 38}H300", "a8"))
    # FAT table
    p.append(text(300, y - 6, "FAT-bejegyzések (index: érték)", 11.5, 600))
    vals = ["0xfff8", "0xffff", "EOC", "4", "5", "8", "7", "EOC", "9", "EOC", "szabad", "szabad"]
    chain = {3, 4, 5, 8, 9}
    for i, v in enumerate(vals):
        cx = 300 + i * 46
        k = "acc" if i in chain else ("tint" if v == "szabad" else "plain")
        p.append(rect(cx, y + 18, 44, 40, k, rx=3))
        p.append(text(cx + 22, y + 32, str(i), 10, cls="quiet", anchor="middle"))
        p.append(text(cx + 22, y + 50, v, 10.5 if v == "szabad" else 11.5, 600 if i in chain else 400, anchor="middle"))
    for a, b in ((3, 4), (4, 5), (5, 8), (8, 9)):
        xa, xb = 300 + a * 46 + 22, 300 + b * 46 + 22
        p.append(path(f"M{xa} {y + 60}C{xa} {y + 80} {xb} {y + 80} {xb} {y + 62}", "a8", cls="acc", width=1.5))
    p.append(text(300, y + 104, "C.DAT = 3 → 4 → 5 → 8 → 9 → a lánc vége (egy törölt fájl klasztereit használta újra: fragmentált)", 11.5, cls="quiet"))
    p.append(text(300, y + 122, "B.DAT = 6 → 7. klaszter;  HELLO.TXT = 2. klaszter", 11.5, cls="quiet"))
    p.append(text(24, y + 160, "Egy fájl n. bájtjához n / 2048 lépésben kell követni a láncot a FAT-ban: a FAT a RAM-ban van, így ez gyors, de a pozicionálás O(n).", 11.5, cls="quiet"))
    p.append(text(24, y + 178, "A törlés csak szabadnak jelöli a klasztereket, és 0xE5-re írja át a név első bájtját: az adat megmarad, amíg újra fel nem használják.", 11.5, cls="quiet"))
    return svg(880, y + 192, title, "\n".join(p))


# ---------------- 9. ext4 layout ----------------
def ext4_layout():
    title = "Az ext4 a lemezen: a megmért 512 MiB-os fájlrendszer négy 128 MiB-os blokkcsoport"
    p = [text(24, 30, title, 15, 600), marker("a9")]
    for g in range(4):
        x = 24 + g * 212
        p.append(rect(x, 54, 204, 40, "acc" if g == 0 else ("c2" if g == 2 else "tint"), rx=3))
        p.append(text(x + 102, 72, f"{g}. blokkcsoport", 12, 600, anchor="middle"))
        sub = f"blokkok: {g * 32768}–{g * 32768 + 32767}"
        p.append(text(x + 102, 88, sub, 10.5, cls="quiet", anchor="middle"))
    p.append(text(448 + 102, 112, "a 16 MiB-os napló: 65536–69631. blokk", 11, 600, anchor="middle"))
    p.append(path("M24 94L24 140", cls="edge", width=1, dash="4 3"))
    p.append(path("M228 94L856 140", cls="edge", width=1, dash="4 3"))
    parts = [("szuper-\nblokk", 0, "c2"), ("csoport-\nleírók", 1, "c2"), ("tartalék\nGDT", 2, "tint"), ("blokk-\nbittérk.", 65, "acc"),
             ("inode-\nbittérk.", 69, "acc"), ("a 0–3. csoport\ninode-táblái", 73, "acc"), ("adatblokkok", 2121, "plain")]
    widths = [62, 62, 72, 64, 64, 150, 358]
    x = 24
    for (name, start, k), w in zip(parts, widths):
        p.append(rect(x, 140, w, 54, k, rx=3))
        for j, line in enumerate(name.split("\n")):
            p.append(text(x + w / 2, 162 + 15 * j, line, 11, 600, anchor="middle"))
        p.append(text(x, 210, str(start), 10, cls="quiet"))
        x += w
    p.append(text(24, 236, "A flex_bg miatt 16 csoport bittérképei és inode-táblái egymás mellé kerülnek, így a 0. csoport tárolja mind a négyét:", 11.5, cls="quiet"))
    p.append(text(24, 254, "bittérképek: 65–68 és 69–72, inode-táblák: 73–2120 (egyenként 512 blokk). Az 1. és 3. csoport tart szuperblokk-másolatot (sparse_super).", 11.5, cls="quiet"))
    p.append(text(24, 272, "Az inode-ok száma mkfs-kor rögzül (itt csoportonként 8192): ha elfogynak, a lemez „tele van”, pedig maradt szabad hely.", 11.5, cls="quiet"))
    return svg(880, 286, title, "\n".join(p))


# ---------------- 10. NTFS MFT ----------------
def mft():
    title = "NTFS: minden fájl, és minden fájl egy 1 KiB-os rekord a Master File Table-ben"
    p = [text(24, 30, title, 15, 600), marker("a10")]
    p.append(text(24, 62, "az MFT (maga is fájl: $MFT)", 12.5, 600))
    recs = [("0", "$MFT"), ("1", "$MFTMirr"), ("2", "$LogFile"), ("3", "$Volume"), ("5", "gyökérkönyvtár"), ("6", "$Bitmap"), ("…", ""), ("64", "hello.txt"), ("65", "big.bin")]
    for i, (n, name) in enumerate(recs):
        y = 74 + i * 28
        k = "acc" if n == "64" else ("c2" if n == "65" else "tint")
        p.append(rect(24, y, 160, 24, k, rx=3))
        p.append(text(34, y + 16, n, 11, 600))
        p.append(text(64, y + 16, name, 11))
    p.append(path("M184 284H250", "a10"))
    p.append(path("M184 312C220 312 220 360 250 360", "a10"))
    p.append(rect(250, 222, 600, 100, "acc"))
    p.append(text(262, 242, "64. rekord: hello.txt (12 bájt) — az adat rezidens", 12, 600))
    attrs = [("$STANDARD_INFORMATION", "idők, jelzőbitek"), ("$FILE_NAME", "név, szülőkönyvtár"), ("$SECURITY_DESCRIPTOR", "hozzáférési jogok"), ("$DATA", "maga a \"hello, NTFS\"")]
    for i, (a, d) in enumerate(attrs):
        x = 262 + i * 146
        p.append(rect(x, 254, 140, 56, "plain", rx=3))
        p.append(text(x + 6, 272, a, 9.5 if len(a) > 16 else 10.5, 600))
        p.append(text(x + 6, 290, d, 10.5, cls="quiet"))
    p.append(rect(250, 336, 600, 70, "c2"))
    p.append(text(262, 356, "65. rekord: big.bin (3 MiB) — az adat nem rezidens", 12, 600))
    p.append(text(262, 378, "a $DATA futáslistát tárol: VCN 0, LCN 0x206a, hossz 0x300 klaszter", 11.5))
    p.append(text(262, 396, "(a fájl 0. klasztere a lemez 8298. klaszterén kezdődik, és 768 klaszteren át tart)", 11, cls="quiet"))
    p.append(text(24, 432, "A kis fájlok (nagyjából 700 bájtig) teljes egészében az MFT-rekordjukban élnek; a könyvtárak $FILE_NAME bejegyzések B+ fái.", 11.5, cls="quiet"))
    return svg(880, 446, title, "\n".join(p))


# ---------------- 11. Flying height ----------------
def head_gap():
    title = "A fej 1–2 nm-rel a lemez fölött repül: minden részecske szikla az útjában"
    p = [text(24, 30, title, 15, 600), marker("a11"), marker("a11b", "bad")]
    # left: schematic side view, not to scale
    p.append(text(24, 62, "oldalnézet (vázlatos, nem méretarányos)", 12, 600, cls="quiet"))
    p.append('<rect x="24" y="200" width="400" height="16" class="accf"/>')
    p.append(path("M24 200H424", cls="acc", width=2))
    p.append(text(24, 236, "a lemez felülete, amely a fej alatt halad", 11.5, cls="quiet"))
    p.append(path("M300 232H340", "a11", cls="acc", width=1.6))
    # arm and slider
    p.append(path("M200 96L290 150", cls="c2s", width=4))
    p.append('<rect x="250" y="150" width="120" height="44" rx="4" class="c2f"/>')
    p.append('<rect x="250" y="150" width="120" height="44" rx="4" fill="none" class="c2s" stroke-width="1.5"/>')
    p.append(text(310, 176, "csúszka + fej", 11.5, 600, anchor="middle"))
    p.append(path("M380 194H396", cls="edge", width=1))
    p.append(path("M380 200H396", cls="edge", width=1))
    p.append(text(400, 172, "1–2 nm", 11.5, 600))
    p.append(text(400, 188, "rés", 11, cls="quiet"))
    # a particle in front of the slider
    p.append('<circle cx="150" cy="184" r="16" class="badf"/><circle cx="150" cy="184" r="16" fill="none" class="bads" stroke-width="1.5"/>')
    p.append(text(150, 146, "porszem", 11.5, 600, cls="bad", anchor="middle"))
    p.append(text(150, 160, "vagy ujjlenyomatréteg", 11, cls="bad", anchor="middle"))
    p.append(path("M246 178H172", "a11b", cls="bads", width=1.4, dash="4 3"))
    p.append(text(24, 266, "Ha nekiütközik, megkarcolja a felületet és a fejet: fejütközés.", 11.5, cls="quiet"))
    p.append(text(24, 284, "Ezért van zárt ház, szűrő és parkolórámpa.", 11.5, cls="quiet"))
    # right: logarithmic scale
    x0, x1, yb = 480, 860, 170
    p.append(text(x0, 62, "ugyanezek a méretek logaritmikus skálán", 12, 600, cls="quiet"))
    p.append(path(f"M{x0} {yb}H{x1}", cls="edge", width=1.5))
    span = (x1 - x0 - 30) / 5
    for lab, e in [("1 nm", 0), ("10 nm", 1), ("100 nm", 2), ("1 µm", 3), ("10 µm", 4), ("100 µm", 5)]:
        x = x0 + 15 + e * span
        p.append(path(f"M{x:.1f} {yb - 5}V{yb + 5}", cls="edge", width=1.2))
        p.append(text(x, yb + 22, lab, 10.5, cls="quiet", anchor="middle"))
    items = [("repülési magasság 1–2 nm", math.log10(1.5), "acct"), ("finom porszem ≤ 2,5 µm", math.log10(2500), "bad"),
             ("emberi hajszál ≈ 70 µm", math.log10(70000), "c2")]
    for i, (lab, e, cls) in enumerate(items):
        x = x0 + 15 + e * span
        y = yb - 30 - 24 * i
        p.append(f'<circle cx="{x:.1f}" cy="{yb}" r="5" class="{cls}"/>')
        p.append(path(f"M{x:.1f} {yb - 6}V{y + 5}", cls="edge", width=1))
        anchor = "start" if e < 2 else "end"
        p.append(text(x + (4 if anchor == "start" else -4), y, lab, 11.5, 600, cls=cls, anchor=anchor))
    p.append(text(x0, yb + 56, "Egy 2,5 µm-es részecske több mint ezerszer", 11.5, cls="quiet"))
    p.append(text(x0, yb + 74, "magasabb a résnél, egy hajszál több tízezerszer.", 11.5, cls="quiet"))
    return svg(880, 300, title, "\n".join(p))


# ---------------- 12. The Linux directory tree ----------------
def fhs():
    title = "A linuxos könyvtárfa teteje (Filesystem Hierarchy Standard)"
    p = [text(24, 30, title, 15, 600)]
    p.append(rect(400, 48, 80, 30, "plain", rx=4))
    p.append(text(440, 68, "/", 14, 600, anchor="middle"))
    rows = [
        [("/boot", ["kernel (vmlinuz),", "initramfs, GRUB;", "/boot/efi (ESP)"], "acc"),
         ("/etc", ["a gépre jellemző", "konfiguráció:", "fstab, passwd …"], "acc"),
         ("/usr", ["telepített szoftver,", "csak olvasható,", "megosztható"], "acc"),
         ("/opt", ["kiegészítő csomagok,", "mindegyik a saját", "/opt/<package> alatt"], "acc"),
         ("/home, /root", ["a felhasználók saját", "könyvtárai; a rooté", "a /root"], "c2")],
        [("/var", ["változó adatok, amelyek", "túlélik az újraindítást:", "log spool lib www"], "c2"),
         ("/srv", ["a gép által kiszolgált", "adatok (web, FTP)", ""], "c2"),
         ("/tmp", ["ideiglenes fájlok,", "törlődhetnek,", "gyakran tmpfs"], "tint"),
         ("/run", ["futásidejű adatok az", "indítás óta (PID-ek,", "socketek), tmpfs"], "tint"),
         ("/mnt, /media", ["csatolási pontok", "ideiglenes és", "cserélhető tárolóknak"], "tint")],
        [("/dev", ["eszközfájlok:", "sda nvme0n1 tty", "null zero random"], "virt"),
         ("/proc", ["folyamatok, csatolások,", "partíciók, memória", "(generált)"], "virt"),
         ("/sys", ["eszközök, meghajtók,", "kernelbeállítások", "(generált)"], "virt")],
    ]
    bw, bh, gap = 158, 86, 12
    y = 108
    p.append(path("M440 78V94", cls="edge", width=1))
    p.append(path(f"M{24 + bw / 2} 94H{24 + 4 * (bw + gap) + bw / 2}", cls="edge", width=1))
    for r, row in enumerate(rows):
        x = 24
        for name, lines, k in row:
            if k == "virt":
                p.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="6" fill="none" class="edge" stroke-width="1.4" stroke-dasharray="5 4"/>')
            else:
                p.append(rect(x, y, bw, bh, k, rx=6))
            p.append(text(x + 10, y + 20, name, 13, 600))
            for i, l in enumerate(lines):
                if l:
                    p.append(text(x + 10, y + 40 + 16 * i, l, 11, cls="ink" if k != "virt" else "quiet"))
            if r == 0:
                p.append(path(f"M{x + bw / 2} 94V{y}", cls="edge", width=1))
            x += bw + gap
        y += bh + gap
    lx = 24 + 3 * (bw + gap) + 4
    ly = 108 + 2 * (bh + gap) + 18
    leg = [("acc", "statikus: szoftvertelepítéskor változik"), ("c2", "változó: a rendszer futása közben nő"),
           ("tint", "ideiglenes vagy illékony"), ("virt", "virtuális: a kernel állítja elő")]
    for i, (k, lab) in enumerate(leg):
        yy = ly + 18 * i
        if k == "virt":
            p.append(f'<rect x="{lx}" y="{yy - 10}" width="18" height="12" rx="2" fill="none" class="edge" stroke-width="1.2" stroke-dasharray="3 2"/>')
        else:
            p.append(rect(lx, yy - 10, 18, 12, k, rx=2))
        p.append(text(lx + 26, yy, lab, 11, cls="quiet"))
    p.append(text(24, y + 14, "A mai disztribúciókon a /bin, /sbin, /lib szimbolikus link a /usr/bin, /usr/sbin, /usr/lib könyvtárra (usr-merge).", 11.5, cls="quiet"))
    return svg(880, y + 28, title, "\n".join(p))


# ---------------- 13. LVM ----------------
def lvm():
    title = "LVM: a blokkeszközökből fizikai kötetek lesznek, extentjeik egy kötetcsoportba kerülnek"
    p = [text(24, 30, title, 15, 600), marker("a13"), marker("a13r", "c2")]
    for x, lab in [(24, "blokkeszközök"), (190, "fizikai kötetek (PV)"), (400, "kötetcsoport (VG)"), (580, "logikai kötetek (LV)"), (760, "fájlrendszerek")]:
        p.append(text(x, 62, lab, 12, 600, cls="quiet"))
    p.append(text(190, 78, "4 MiB-os extentekre vágva", 10.5, cls="quiet"))
    devs = [("/dev/sda2", "egy partíció", 5), ("/dev/md0", "egy RAID-tömb", 4), ("/dev/sdb", "egy SAN-lemez (LUN)", 6), ("/dev/sdc", "később hozzáadva", 5)]
    ys = [90, 160, 230, 310]
    vg_in = [130, 180, 230, 300]
    for i, ((d, s, n), y) in enumerate(zip(devs, ys)):
        new = i == 3
        p.append(rect(24, y, 140, 50, "c2" if new else "tint", rx=10))
        p.append(text(36, y + 22, d, 12, 600))
        p.append(text(36, y + 40, s, 11, cls="c2" if new else "quiet"))
        p.append(path(f"M164 {y + 25}H186", "a13r" if new else "a13", cls="c2s" if new else "edge"))
        for j in range(n):
            p.append(rect(190 + j * 26, y + 12, 22, 26, "c2" if new else "acc", rx=2))
        sx = 190 + n * 26
        p.append(path(f"M{sx} {y + 25}L396 {vg_in[i]}", "a13r" if new else "a13", cls="c2s" if new else "edge"))
    # VG pool
    p.append(rect(400, 90, 150, 270, "plain", rx=8))
    p.append(text(475, 110, "vg1", 13, 600, anchor="middle"))
    for r in range(8):
        for c in range(4):
            p.append(rect(414 + c * 32, 122 + r * 28, 26, 22, "c2" if r >= 6 else "acc", rx=2))
    p.append(text(475, 378, "egy közös extentkészlet", 11, cls="quiet", anchor="middle"))
    # LVs
    p.append(rect(580, 96, 150, 56, "acc", rx=6))
    p.append(text(592, 118, "lv_home", 12, 600))
    p.append(text(592, 138, "lineáris", 11, cls="quiet"))
    p.append(path("M552 124H578", "a13"))
    p.append(rect(580, 190, 150, 56, "acc", rx=6))
    p.append(text(592, 212, "lv_db", 12, 600))
    p.append(text(592, 232, "raid1: két példány", 11, cls="quiet"))
    p.append(path("M552 218H578", "a13"))
    p.append(rect(580, 246, 150, 30, "c2", rx=6))
    p.append(text(592, 266, "+ extentek (bővítve)", 11, 600, cls="c2"))
    p.append(path("M552 300C566 300 566 262 578 262", "a13r", cls="c2s"))
    for lab, mnt, y in [("XFS", "/home", 104), ("XFS", "/var/lib/db", 210)]:
        p.append(path(f"M730 {y + 20}H758", "a13"))
        p.append(rect(760, y, 100, 40, "tint", rx=6))
        p.append(text(770, y + 17, lab, 12, 600))
        p.append(text(770, y + 33, mnt, 11, cls="quiet"))
    p.append(text(580, 300, "az lvextend -r csatolt állapotban", 11, cls="c2"))
    p.append(text(580, 316, "bővíti az LV-t és a fájlrendszerét", 11, cls="c2"))
    cmds = [("létrehozás", "pvcreate", "vgcreate", "lvcreate -L vagy -l", "mkfs.xfs, mount"),
            ("bővítés", "pvcreate (új lemez)", "vgextend", "lvextend -r", "xfs_growfs, resize2fs"),
            ("lemez kivonása", "pvmove, majd pvremove", "vgreduce", "", ""),
            ("vizsgálat", "pvs, pvdisplay", "vgs, vgdisplay", "lvs, lvdisplay", "df, lsblk")]
    y0 = 412
    p.append(path(f"M24 {y0 - 18}H860", cls="grid", width=1))
    xs = [24, 190, 400, 580, 760]
    for i, row in enumerate(cmds):
        for j, c in enumerate(row):
            cls = "c2" if (i == 1 and j > 0) else ("quiet" if j == 0 else "ink")
            p.append(text(xs[j], y0 + 20 * i, c, 11.5, 600 if j == 0 else 400, cls=cls))
    return svg(880, y0 + 20 * len(cmds) + 4, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("hdd", hdd), ("ssd", ssd), ("write-amplification", write_amp), ("storage-stack", layers),
                     ("inode", inode), ("links", links), ("directory", directory), ("fat16", fat16),
                     ("ext4-layout", ext4_layout), ("ntfs-mft", mft), ("head-gap", head_gap), ("fhs", fhs),
                     ("lvm", lvm)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
