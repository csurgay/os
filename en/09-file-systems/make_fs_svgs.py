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
    title = "A hard disk: rotating platters, moving heads, and three components of every access"
    p = [text(24, 30, title, 15, 600), marker("a1")]
    # side view
    cx = 170
    p.append(text(cx, 62, "side view", 12, 600, cls="quiet", anchor="middle"))
    p.append(f'<rect x="{cx - 6}" y="74" width="12" height="190" class="edgef"/>')
    for i, y in enumerate((100, 150, 200, 250)):
        p.append(f'<rect x="{cx - 110}" y="{y - 5}" width="220" height="10" rx="2" class="accf"/>')
        p.append(f'<rect x="{cx - 110}" y="{y - 5}" width="220" height="10" rx="2" fill="none" class="acc" stroke-width="1.5"/>')
        for dy in (-11, 11):
            p.append(path(f"M330 {y + dy}H{cx + 60}", cls="c2s", width=2))
            p.append(f'<circle cx="{cx + 60}" cy="{y + dy}" r="3" class="c2"/>')
    p.append(f'<rect x="326" y="80" width="10" height="190" class="c2"/>')
    p.append(text(cx, 290, "platters on one spindle (5,400–15,000 rpm)", 11.5, cls="quiet", anchor="middle"))
    p.append(text(340, 290, "arm with a head", 11.5, cls="quiet", anchor="start"))
    p.append(text(340, 306, "for each surface", 11.5, cls="quiet", anchor="start"))
    # top view
    ox, oy = 600, 175
    p.append(text(ox, 62, "top view of one surface", 12, 600, cls="quiet", anchor="middle"))
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
    p.append(text(ox + 112, oy - 64, "track", 12, 600, cls="acct"))
    p.append(path(f"M{ox + 108} {oy - 68}L{ox + 62} {oy - 52}", "a1"))
    p.append(text(ox + 112, oy + 2, "sector", 12, 600))
    p.append(path(f"M{ox + 108} {oy - 2}L{ox + 76} {oy - 14}", "a1"))
    p.append(text(ox, oy + 124, "a cylinder = the same track on every surface", 11.5, cls="quiet", anchor="middle"))
    # access time
    y = 340
    p.append(text(24, y, "time of one random 4 KiB read (7,200 rpm desktop disk, typical values)", 12.5, 600))
    parts = [("seek: move the arm", 8.5, "c2"), ("rotation: wait for the sector, ½ turn on average", 4.17, "acc"), ("transfer", 0.02, "bad")]
    x, scale = 40, 52
    for name, ms, k in parts:
        w = max(ms * scale, 4)
        p.append(rect(x, y + 14, w, 26, k, rx=3))
        x += w
    p.append(text(40, y + 60, "≈ 8.5 ms seek", 11.5, cls="quiet"))
    p.append(text(40 + 8.5 * scale, y + 60, "+ 4.17 ms rotation", 11.5, cls="quiet"))
    p.append(text(40 + 12.67 * scale + 8, y + 32, "+ 0.02 ms transfer  ≈ 12.7 ms", 11.5, 600))
    p.append(text(24, y + 86, "≈ 80 random reads per second, while a sequential read streams 200–280 MB/s from the same disk.", 11.5, cls="quiet"))
    return svg(880, y + 100, title, "\n".join(p))


# ---------------- 2. The SSD ----------------
def ssd():
    title = "An SSD: a controller in front of many NAND flash chips working in parallel"
    p = [text(24, 30, title, 15, 600), marker("a2")]
    p.append(rect(24, 60, 120, 210, "tint"))
    p.append(text(84, 90, "host", 13, 600, anchor="middle"))
    p.append(text(84, 112, "SATA, SAS", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 128, "or NVMe", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 144, "over PCIe", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 180, "sees logical", 11.5, cls="quiet", anchor="middle"))
    p.append(text(84, 196, "blocks (LBAs)", 11.5, cls="quiet", anchor="middle"))
    p.append(path("M144 165H184", "a2"))
    p.append(rect(184, 60, 230, 210, "acc"))
    p.append(text(299, 86, "controller (firmware)", 13, 600, anchor="middle"))
    for i, s in enumerate(["flash translation layer:", "logical page → physical page", "garbage collection", "wear leveling", "error correction (ECC)", "bad block management"]):
        p.append(text(200, 112 + 22 * i, ("• " if i != 1 else "   ") + s, 11.5, 600 if i == 0 else 400))
    p.append(rect(200, 234, 198, 26, "c2", rx=4))
    p.append(text(299, 252, "DRAM: mapping table, cache", 11, anchor="middle"))
    # channels and dies
    for ch in range(4):
        y = 70 + ch * 50
        p.append(path(f"M414 {y + 15}H452", "a2"))
        p.append(text(433, y + 8, f"ch {ch}", 10, cls="quiet", anchor="middle"))
        for d in range(3):
            x = 456 + d * 74
            p.append(rect(x, y, 66, 30, "plain", rx=4))
            p.append(text(x + 33, y + 19, "NAND die", 10.5, anchor="middle"))
    p.append(text(567, 288, "channels × dies: requests run in parallel", 11.5, cls="quiet", anchor="middle"))
    # inside a die
    y0 = 320
    p.append(text(24, y0, "inside a die", 12.5, 600))
    for b in range(4):
        x = 40 + b * 150
        p.append(rect(x, y0 + 14, 132, 96, "plain", rx=4))
        p.append(text(x + 66, y0 + 30, f"block {b}" if b < 3 else "block …", 11, 600, anchor="middle"))
        for r in range(4):
            cls = ["accf", "badf", "accf", "tint"][(r + b) % 4] if b < 3 else "tint"
            p.append(f'<rect x="{x + 8}" y="{y0 + 40 + r * 16}" width="116" height="13" class="{cls}"/>')
    p.append(rect(660, y0 + 14, 14, 13, "acc", rx=0)); p.append(text(680, y0 + 25, "valid page", 11))
    p.append(f'<rect x="660" y="{y0 + 36}" width="14" height="13" class="badf"/>'); p.append(text(680, y0 + 47, "invalid (stale) page", 11))
    p.append(f'<rect x="660" y="{y0 + 58}" width="14" height="13" class="tint"/>'); p.append(text(680, y0 + 69, "erased page", 11))
    p.append(text(24, y0 + 136, "read and program (write): one page, 4–16 KiB, tens of µs to 1 ms   ·   erase: a whole block of hundreds of pages, several ms", 11.5, cls="quiet"))
    p.append(text(24, y0 + 154, "A page cannot be overwritten in place: a new version goes to an erased page, and the old one becomes invalid.", 11.5, cls="quiet"))
    return svg(880, y0 + 168, title, "\n".join(p))


# ---------------- 3. Write amplification (simulated) ----------------
def write_amp():
    title = "Write amplification against spare flash (simulated, ftlsim.py, random 4 KiB writes)"
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
    p.append(text((x0 + x1) / 2, y0 + 38, "share of the raw flash hidden from the host (over-provisioning)", 11.5, cls="quiet", anchor="middle"))
    pts = " ".join(f"{X(s):.1f},{Y(v):.1f}" for s, v in zip(spare, wa))
    p.append(f'<polyline points="{pts}" fill="none" class="acc" stroke-width="2.5"/>')
    for s, v in zip(spare, wa):
        p.append(f'<circle cx="{X(s):.1f}" cy="{Y(v):.1f}" r="4" class="acct"/>')
        p.append(text(X(s) + 8, Y(v) - 8, f"{v:.2f}", 11, 600))
    p.append(text(24, 370, "For every 4 KiB the host writes, a nearly full SSD may write 6–7 times as much flash, because garbage collection copies valid pages.", 11.5, cls="quiet"))
    p.append(text(24, 388, "More spare flash (or TRIM, which tells the SSD which pages are free) lowers it; sequential writes keep it near 1.", 11.5, cls="quiet"))
    return svg(800, 402, title, "\n".join(p))


# ---------------- 4. The layers ----------------
def layers():
    title = "From a system call to the device: the layers of the storage stack in Linux"
    p = [text(24, 30, title, 15, 600), marker("a4")]
    rows = [("application", "open() read() write() close() rename() fsync() …", "tint"),
            ("virtual file system (VFS)", "one interface for every file system; dentry and inode caches", "acc"),
            ("page cache", "file data in RAM; writes are delayed (write-back)", "c2"),
            ("file system", "ext4 · XFS · Btrfs · vfat · ntfs3 · tmpfs · proc · NFS …", "acc"),
            ("block layer", "requests to numbered blocks; merging and I/O scheduling", "tint"),
            ("device driver", "NVMe · SATA (AHCI) · SCSI · virtio-blk · USB storage", "tint"),
            ("storage device", "SSD (flash + FTL) or hard disk (platters + firmware)", "c2")]
    y = 54
    for i, (name, desc, k) in enumerate(rows):
        p.append(rect(60, y, 760, 42, k, rx=6))
        p.append(text(76, y + 26, name, 13, 600))
        p.append(text(300, y + 26, desc, 12, cls="quiet" if k == "tint" else "ink"))
        if i < len(rows) - 1:
            p.append(path(f"M440 {y + 42}V{y + 54}", "a4"))
        y += 54
    p.append(text(830, 86, "user space", 11, cls="quiet", anchor="start"))
    p.append(path("M40 102H850", cls="edge", width=1, dash="5 4"))
    p.append(text(830, 120, "kernel", 11, cls="quiet", anchor="start"))
    p.append(text(24, y + 8, "Pseudo file systems (proc, sysfs, tmpfs) stop at the VFS or the page cache: they have no device below them.", 11.5, cls="quiet"))
    return svg(900, y + 22, title, "\n".join(p))


# ---------------- 5. The inode ----------------
def inode():
    title = "A directory entry gives a name to an inode; the inode describes the file and finds its data"
    p = [text(24, 30, title, 15, 600), marker("a5")]
    p.append(rect(24, 60, 170, 96, "tint"))
    p.append(text(36, 82, "directory entry", 12.5, 600))
    p.append(text(36, 106, "name: photo.jpg", 12))
    p.append(text(36, 126, "inode number: 19", 12, 600, cls="acct"))
    p.append(path("M194 120H236", "a5"))
    p.append(rect(236, 60, 250, 286, "acc"))
    p.append(text(250, 82, "inode 19 (256 bytes in ext4)", 12.5, 600))
    fields = ["type and permissions (rw-r--r--)", "owner (uid) and group (gid)", "size: 307,200 bytes", "link count: 1",
              "times: access, modify, change, birth", "flags (extents, …)", "", "where the data is:",
              "ext2/ext3: block pointers  ↗", "ext4: extents  ↘"]
    for i, f in enumerate(fields):
        if f:
            p.append(text(250, 106 + 20 * i, f, 11.5, 600 if f.startswith("where") else 400))
    p.append(text(250, 330, "no name: names live in directories", 11.5, cls="quiet"))
    # classic block map
    p.append(text(520, 70, "classic Unix / ext2: block pointers", 12.5, 600))
    labels = ["12 direct pointers", "single indirect", "double indirect", "triple indirect"]
    for i, l in enumerate(labels):
        y = 84 + i * 30
        p.append(rect(520, y, 150, 24, "plain", rx=3))
        p.append(text(530, y + 16, l, 11))
        p.append(path(f"M670 {y + 12}H{700 + 20 * i}", "a5"))
        for j in range(i + 1):
            p.append(rect(702 + 20 * i + j * 6, y + 2 - j * 2, 18, 20, "c2" if j == i else "plain", rx=2))
    p.append(text(520, 216, "4 KiB blocks: 48 KiB direct, then 1,024 more", 11, cls="quiet"))
    p.append(text(520, 232, "pointers per indirect block, and so on", 11, cls="quiet"))
    # ext4 extents
    p.append(text(520, 268, "ext4: extents", 12.5, 600))
    p.append(rect(520, 280, 330, 46, "c2", rx=4))
    p.append(text(532, 300, "file blocks 0–74  →  disk blocks 2581–2655", 12, 600))
    p.append(text(532, 318, "one extent: start, length (up to 32,768 blocks = 128 MiB)", 11, cls="quiet"))
    p.append(path("M486 300H520", "a5"))
    p.append(text(24, 372, "Up to 4 extents fit in the inode itself; larger or fragmented files get a small tree of extent blocks.", 11.5, cls="quiet"))
    return svg(880, 388, title, "\n".join(p))


# ---------------- 6. Hard and symbolic links ----------------
def links():
    title = "Hard link: a second name for the same inode.  Symbolic link: a small file that contains a path"
    p = [text(24, 30, title, 15, 600), marker("a6")]
    p.append(rect(24, 60, 210, 150, "tint"))
    p.append(text(36, 82, "directory /mnt/lab", 12.5, 600))
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
    p.append(text(342, 112, "inode 12  regular file", 12, 600))
    p.append(text(342, 132, "link count: 2", 12))
    p.append(text(342, 150, "size 19", 11.5, cls="quiet"))
    p.append(path("M530 125H586", "a6"))
    p.append(rect(586, 104, 190, 42, "plain", rx=4))
    p.append(text(600, 130, "\"hello, file system\"", 12))
    p.append(rect(330, 196, 200, 64, "c2"))
    p.append(text(342, 218, "inode 13  symbolic link", 12, 600))
    p.append(text(342, 240, "contents: \"notes.txt\"", 12))
    p.append(text(550, 216, "the path is looked up again at every use:", 11.5, cls="quiet"))
    p.append(text(550, 232, "after rm notes.txt the link dangles", 11.5, cls="quiet"))
    rows2 = [("", "hard link", "symbolic link"), ("points to", "an inode (by number)", "a path (by name)"),
             ("own inode", "no: same inode, link count + 1", "yes, type \"symlink\""),
             ("target deleted", "data stays until the last link goes", "link dangles"),
             ("other file system", "impossible (inode numbers are local)", "possible"),
             ("directories", "not allowed (would create cycles)", "allowed")]
    y = 296
    for i, (a, b, c) in enumerate(rows2):
        w = 600 if i == 0 else 400
        p.append(text(36, y + 20 * i, a, 11.5, 600))
        p.append(text(200, y + 20 * i, b, 11.5, w))
        p.append(text(520, y + 20 * i, c, 11.5, w))
    return svg(880, y + 20 * len(rows2) + 8, title, "\n".join(p))


# ---------------- 7. Directories ----------------
def directory():
    title = "A directory is a file of (name, inode) entries: a list for small directories, a hashed tree for large ones"
    p = [text(24, 30, title, 15, 600), marker("a7")]
    p.append(text(24, 62, "linear list (ext2, FAT, ext4 for small directories): search from the start", 12.5, 600))
    entries = [("2", "12", "."), ("2", "12", ".."), ("11", "20", "lost+found"), ("14", "20", "host-link"), ("12", "16", "hard.txt"),
               ("13", "16", "soft.txt"), ("15", "12", "dir"), ("19", "3976", "photo.jpg")]
    x = 24
    for ino, rl, name in entries:
        w = 52 + 6 * len(name)
        p.append(rect(x, 74, w, 50, "plain", rx=3))
        p.append(text(x + 6, 92, f"inode {ino}", 10.5, cls="quiet"))
        p.append(text(x + 6, 108, f"len {rl}", 10.5, cls="quiet"))
        p.append(text(x + 6, 120, name, 11, 600))
        x += w + 4
    p.append(text(24, 144, "Each entry stores its length; a deleted entry is absorbed by the one before it, and its space can be reused. Finding a name: O(n).", 11.5, cls="quiet"))
    y0 = 180
    p.append(text(24, y0, "hashed tree (ext4 htree; XFS and NTFS use B+ trees): hash the name, follow the tree", 12.5, 600))
    p.append(rect(320, y0 + 16, 240, 76, "acc"))
    p.append(text(440, y0 + 36, "root block", 12, 600, anchor="middle"))
    p.append(text(440, y0 + 56, "hash 0x00000000 → block 1", 11, anchor="middle"))
    p.append(text(440, y0 + 72, "hash 0x2092d826 → block 6  …", 11, anchor="middle"))
    for i, (lab, x) in enumerate([("leaf block 1", 60), ("leaf block 6", 260), ("leaf block 4", 460), ("… 10 leaves", 660)]):
        p.append(rect(x, y0 + 130, 160, 50, "plain" if i < 3 else "tint", rx=4))
        p.append(text(x + 80, y0 + 152, lab, 11.5, 600, anchor="middle"))
        p.append(text(x + 80, y0 + 170, "entries in that hash range" if i < 3 else "", 10.5, cls="quiet", anchor="middle"))
        p.append(path(f"M440 {y0 + 92}L{x + 80} {y0 + 128}", "a7"))
    p.append(text(24, y0 + 208, "2,000 files measured: one root block and 10 leaf blocks. A lookup reads the root and one leaf: O(log n) instead of O(n).", 11.5, cls="quiet"))
    return svg(880, y0 + 222, title, "\n".join(p))


# ---------------- 8. FAT16 ----------------
def fat16():
    title = "FAT16: the layout of the measured 32 MiB volume, and the file C.DAT as a chain of clusters"
    p = [text(24, 30, title, 15, 600), marker("a8")]
    parts = [("boot", 0, 4, "c2"), ("FAT #1", 4, 64, "acc"), ("FAT #2", 68, 64, "acc"), ("root dir", 132, 32, "c2"), ("data area: clusters 2, 3, 4, …", 164, 300, "tint")]
    x = 24
    for name, start, n, k in parts:
        w = {4: 50, 64: 110, 32: 90, 300: 470}[n]
        p.append(rect(x, 54, w, 40, k, rx=3))
        p.append(text(x + w / 2, 79, name, 12, 600, anchor="middle"))
        p.append(text(x, 110, str(start), 10.5, cls="quiet"))
        x += w
    p.append(text(x, 110, "65535", 10.5, cls="quiet", anchor="end"))
    p.append(text(24, 128, "sector numbers (512 bytes each); one cluster = 4 sectors = 2 KiB", 11.5, cls="quiet"))
    # directory entry
    y = 160
    p.append(rect(24, y, 230, 64, "c2"))
    p.append(text(36, y + 22, "root directory entry 2", 12, 600))
    p.append(text(36, y + 42, "C.DAT  size 9000  first 3", 12))
    p.append(path(f"M254 {y + 38}H300", "a8"))
    # FAT table
    p.append(text(300, y - 6, "FAT entries (index: value)", 11.5, 600))
    vals = ["0xfff8", "0xffff", "EOC", "4", "5", "8", "7", "EOC", "9", "EOC", "free", "free"]
    chain = {3, 4, 5, 8, 9}
    for i, v in enumerate(vals):
        cx = 300 + i * 46
        k = "acc" if i in chain else ("tint" if v == "free" else "plain")
        p.append(rect(cx, y + 18, 44, 40, k, rx=3))
        p.append(text(cx + 22, y + 32, str(i), 10, cls="quiet", anchor="middle"))
        p.append(text(cx + 22, y + 50, v, 11.5, 600 if i in chain else 400, anchor="middle"))
    for a, b in ((3, 4), (4, 5), (5, 8), (8, 9)):
        xa, xb = 300 + a * 46 + 22, 300 + b * 46 + 22
        p.append(path(f"M{xa} {y + 60}C{xa} {y + 80} {xb} {y + 80} {xb} {y + 62}", "a8", cls="acc", width=1.5))
    p.append(text(300, y + 104, "C.DAT = clusters 3 → 4 → 5 → 8 → 9 → end of chain (it reused the clusters of a deleted file: fragmented)", 11.5, cls="quiet"))
    p.append(text(300, y + 122, "B.DAT = clusters 6 → 7;  HELLO.TXT = cluster 2", 11.5, cls="quiet"))
    p.append(text(24, y + 160, "To read byte n of a file, follow the chain n / 2048 steps through the FAT: the FAT is kept in RAM, so this is fast, but seeking is O(n).", 11.5, cls="quiet"))
    p.append(text(24, y + 178, "Deleting only marks the clusters free and overwrites the first byte of the name with 0xE5: the data stays until reused.", 11.5, cls="quiet"))
    return svg(880, y + 192, title, "\n".join(p))


# ---------------- 9. ext4 layout ----------------
def ext4_layout():
    title = "ext4 on disk: the measured 512 MiB file system is four block groups of 128 MiB"
    p = [text(24, 30, title, 15, 600), marker("a9")]
    for g in range(4):
        x = 24 + g * 212
        p.append(rect(x, 54, 204, 40, "acc" if g == 0 else ("c2" if g == 2 else "tint"), rx=3))
        p.append(text(x + 102, 72, f"block group {g}", 12, 600, anchor="middle"))
        sub = f"blocks {g * 32768}–{g * 32768 + 32767}"
        p.append(text(x + 102, 88, sub, 10.5, cls="quiet", anchor="middle"))
    p.append(text(448 + 102, 112, "the 16 MiB journal: blocks 65536–69631", 11, 600, anchor="middle"))
    p.append(path("M24 94L24 140", cls="edge", width=1, dash="4 3"))
    p.append(path("M228 94L856 140", cls="edge", width=1, dash="4 3"))
    parts = [("super-\nblock", 0, "c2"), ("group\ndescr.", 1, "c2"), ("reserved\nGDT", 2, "tint"), ("block\nbitmaps", 65, "acc"),
             ("inode\nbitmaps", 69, "acc"), ("inode tables of\ngroups 0–3", 73, "acc"), ("data blocks", 2121, "plain")]
    widths = [62, 62, 72, 64, 64, 150, 358]
    x = 24
    for (name, start, k), w in zip(parts, widths):
        p.append(rect(x, 140, w, 54, k, rx=3))
        for j, line in enumerate(name.split("\n")):
            p.append(text(x + w / 2, 162 + 15 * j, line, 11, 600, anchor="middle"))
        p.append(text(x, 210, str(start), 10, cls="quiet"))
        x += w
    p.append(text(24, 236, "With flex_bg, the bitmaps and inode tables of 16 groups are packed together, so group 0 holds those of all four groups:", 11.5, cls="quiet"))
    p.append(text(24, 254, "bitmaps at 65–68 and 69–72, inode tables at 73–2120 (512 blocks each). Groups 1 and 3 keep backup superblocks (sparse_super).", 11.5, cls="quiet"))
    p.append(text(24, 272, "The inode count is fixed at mkfs time (here 8,192 per group): when inodes run out, the disk is \"full\" with free space left.", 11.5, cls="quiet"))
    return svg(880, 286, title, "\n".join(p))


# ---------------- 10. NTFS MFT ----------------
def mft():
    title = "NTFS: everything is a file, and every file is a 1 KiB record in the Master File Table"
    p = [text(24, 30, title, 15, 600), marker("a10")]
    p.append(text(24, 62, "the MFT (itself the file $MFT)", 12.5, 600))
    recs = [("0", "$MFT"), ("1", "$MFTMirr"), ("2", "$LogFile"), ("3", "$Volume"), ("5", "root dir"), ("6", "$Bitmap"), ("…", ""), ("64", "hello.txt"), ("65", "big.bin")]
    for i, (n, name) in enumerate(recs):
        y = 74 + i * 28
        k = "acc" if n == "64" else ("c2" if n == "65" else "tint")
        p.append(rect(24, y, 160, 24, k, rx=3))
        p.append(text(34, y + 16, n, 11, 600))
        p.append(text(64, y + 16, name, 11))
    p.append(path("M184 284H250", "a10"))
    p.append(path("M184 312C220 312 220 360 250 360", "a10"))
    p.append(rect(250, 222, 600, 100, "acc"))
    p.append(text(262, 242, "record 64: hello.txt (12 bytes) — the data is resident", 12, 600))
    attrs = [("$STANDARD_INFORMATION", "times, flags"), ("$FILE_NAME", "name, parent dir"), ("$SECURITY_DESCRIPTOR", "access rights"), ("$DATA", "\"hello, NTFS\" itself")]
    for i, (a, d) in enumerate(attrs):
        x = 262 + i * 146
        p.append(rect(x, 254, 140, 56, "plain", rx=3))
        p.append(text(x + 6, 272, a, 9.5 if len(a) > 16 else 10.5, 600))
        p.append(text(x + 6, 290, d, 10.5, cls="quiet"))
    p.append(rect(250, 336, 600, 70, "c2"))
    p.append(text(262, 356, "record 65: big.bin (3 MiB) — the data is non-resident", 12, 600))
    p.append(text(262, 378, "$DATA holds a run list: VCN 0, LCN 0x206a, length 0x300 clusters", 11.5))
    p.append(text(262, 396, "(file cluster 0 starts at disk cluster 8298 and runs for 768 clusters)", 11, cls="quiet"))
    p.append(text(24, 432, "Small files (up to roughly 700 bytes) live entirely in their MFT record; directories are B+ trees of $FILE_NAME entries.", 11.5, cls="quiet"))
    return svg(880, 446, title, "\n".join(p))


if __name__ == "__main__":
    for name, fn in [("hdd", hdd), ("ssd", ssd), ("write-amplification", write_amp), ("storage-stack", layers),
                     ("inode", inode), ("links", links), ("directory", directory), ("fat16", fat16),
                     ("ext4-layout", ext4_layout), ("ntfs-mft", mft)]:
        with open(os.path.join(HERE, f"{name}.svg"), "w") as f:
            f.write(fn())
        print("wrote", name + ".svg")
