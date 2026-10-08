"""Generate the SVG figures for the Processes, Threads and System Calls lecture.

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



def mono(x, y, s, size=12, cls="ink", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" text-anchor="{anchor}" '
            f'style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{esc(s)}</text>')



def boxt(x, y, w, h, lines, kind="tint", size=12, weight=400, rx=6, cls="ink"):
    """A box with one or more centred lines of text."""
    out = [rect(x, y, w, h, kind, rx=rx)]
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * (size + 3) / 2 + size * 0.36
    for i, s in enumerate(lines):
        out.append(text(x + w / 2, y0 + i * (size + 3), s, size, weight if i == 0 else 400,
                        cls if i == 0 else "quiet", anchor="middle"))
    return out



# ---------------- 1. What a process consists of ----------------
def address_space():
    m = "as"
    title = "Egy folyamat: címtartomány, plusz a kernel nyilvántartása minden másról"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(24, 62, "Egy folyamat virtuális címtartománya (x86-64)", 13, 600))
    x, w = 128, 222
    # (y, h, kind, main label, sub label, address label)
    regions = [
        (74, 30, "plain", "kernel", "felhasználói módban nem érhető el", "0xffff8000…"),
        (126, 40, "acc", "verem", "lokális változók, visszatérési címek", "0x7ffc6e85…"),
        (186, 66, "c2", "memórialeképezett terület", "libc, ld.so, vDSO, nagy malloc,", "0x7f5fde26…"),
        (300, 34, "acc", "heap", "malloc, a brk() növeli", "0x562f7f5f…"),
        (338, 22, "tint", "BSS", "", "0x562f5a60…"),
        (362, 22, "tint", "data", "", ""),
        (386, 30, "tint", "text", "gépi kód, csak olvasható", "0x562f5a60…"),
    ]
    for y, h, kind, a, b, addr in regions:
        p.append(rect(x, y, w, h, kind, rx=4))
        if b:
            p.append(text(x + 10, y + h / 2 - 2 if h >= 30 else y + 15, a, 12, 600))
            p.append(text(x + 10, y + h / 2 + 12 if h >= 30 else y + 15, b, 10.5, cls="quiet"))
        else:
            p.append(text(x + 10, y + 15, a, 12, 600))
        if addr:
            p.append(mono(x - 8, y + h / 2 + 4, addr, 10.5, cls="quiet", anchor="end"))
    p.append(text(x + 10, 246, "szálvermek", 10.5, cls="quiet"))
    p.append(text(x + w - 8, 383 - 6, "inicializált globálisok", 10, cls="quiet", anchor="end"))
    p.append(text(x + w - 8, 353, "nullázott globálisok", 10, cls="quiet", anchor="end"))
    # growth arrows in the gaps
    p.append(path(f"M{x + 60} 168V182", m))
    p.append(path(f"M{x + 60} 298V276", m))
    p.append(path(f"M{x + 160} 254V270", m))
    p.append(text(x + 74, 289, "a heap felfelé nő", 10.5, cls="quiet"))
    p.append(text(x + 174, 268, "lefelé", 10.5, cls="quiet"))
    p.append(text(x + 74, 180, "a verem lefelé nő", 10.5, cls="quiet"))
    p.append(text(x + 10, 116, "· · ·", 12, cls="quiet"))
    p.append(mono(x - 8, 430, "0x0", 10.5, cls="quiet", anchor="end"))
    p.append(text(x + 10, 432, "a 0. lap leképezetlen: nullmutató → hiba", 10.5, cls="quiet"))
    # right: the kernel's side
    rx0, rw = 392, 344
    p.append(text(rx0, 62, "A kernel nyilvántartása (Linux: task_struct)", 13, 600))
    items = [("azonosítók", "PID, a szülő PID-je, szálcsoport, munkamenet"),
             ("állapot és ütemezés", "R, S, D, T, Z; prioritás, felhasznált CPU-idő"),
             ("mentett regiszterek", "PC, veremmutató, jelzőbitek, általános regiszterek"),
             ("memóriatérkép", "a régiók (VMA-k) listája és a laptáblák"),
             ("megnyitott fájlok", "leírótábla: 0, 1, 2, …"),
             ("credentials", "felhasználói és csoportazonosítók, capabilityk"),
             ("szignálok", "kezelők, blokkolt és függőben lévő szignálok"),
             ("környezet", "aktuális könyvtár, gyökér, korlátok, namespace-ek")]
    for i, (a, b) in enumerate(items):
        y = 74 + i * 43
        p.append(rect(rx0, y, rw, 37, "tint" if i % 2 == 0 else "plain", rx=4))
        p.append(text(rx0 + 10, y + 16, a, 12, 600))
        p.append(text(rx0 + 10, y + 31, b, 10.5, cls="quiet"))
    p.append(text(24, 462, "Bal oldalon: címek az előadás layout bemutatójából (az ASLR miatt minden futáskor változnak). A címtartomány kernelhez", 11.5, cls="quiet"))
    p.append(text(24, 480, "tartozó fele minden folyamatban le van képezve, de védett; a jobb oldali nyilvántartás sosem hagyja el a kernelt.", 11.5, cls="quiet"))
    return svg(760, 498, title, "\n".join(p))


# ---------------- 2. The path of a system call ----------------
def syscall_path():
    m, ma = "sp", "spa"
    title = "Egy rendszerhívás útja x86-64-es Linuxon, és a vDSO rövidítése"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(24, 60, "felhasználói mód", 12.5, 600, cls="quiet"))
    p.append('<line x1="24" y1="240" x2="736" y2="240" class="grid" stroke-width="1.5" stroke-dasharray="5 4"/>')
    p.append(text(24, 262, "kernelmód", 12.5, 600, cls="quiet"))
    # program
    p.append(rect(24, 74, 176, 144, "tint", rx=6))
    p.append(text(36, 94, "program", 12, 600))
    p.append(mono(36, 120, "n = write(1, buf, 3);", 11))
    p.append(mono(36, 190, "clock_gettime(…);", 11))
    # libc wrapper
    p.append(rect(236, 74, 196, 70, "c2", rx=6))
    p.append(text(248, 92, "libc wrapper write()", 12, 600))
    p.append(mono(248, 112, "mov  $1, %eax", 11))
    p.append(mono(248, 130, "syscall", 11, cls="acct"))
    # vDSO
    p.append(rect(236, 156, 196, 62, "plain", rx=6))
    p.append(text(248, 175, "vDSO: __vdso_clock_gettime", 12, 600))
    p.append(text(248, 192, "a kernel által frissített órát", 10.5, cls="quiet"))
    p.append(text(248, 207, "olvassa: nincs módváltás", 10.5, cls="quiet"))
    p.append(path("M200 116H232", m, width=1.5))
    p.append(path("M200 186H232", m, width=1.5))
    # syscall down
    p.append(path("M432 96H560V280", ma, cls="acc", width=1.8))
    p.append(text(572, 92, "syscall utasítás:", 11.5, 600, cls="acct"))
    p.append(text(572, 108, "kernelmódba vált, és a kernel", 10.5, cls="quiet"))
    p.append(text(572, 123, "belépési pontjára ugrik", 10.5, cls="quiet"))
    p.append(text(572, 138, "(a cím egy MSR-ben van)", 10.5, cls="quiet"))
    # kernel boxes
    p += boxt(480, 284, 256, 44, ["entry_SYSCALL_64", "regiszterek mentése, váltás a kernelveremre"], "acc", 11.5, 600)
    p += boxt(480, 340, 256, 44, ["sys_call_table[rax]  (1 = write)", "ksys_write() → VFS → pipe, fájl vagy tty"], "acc", 11.5, 600)
    p.append(path("M608 328V336", m))
    # return
    p.append(path("M480 362H456V136H436", m, width=1.5))
    p.append(text(444, 300, "sysret:", 11.5, 600, anchor="end"))
    p.append(text(444, 316, "eredmény az rax-ban,", 10.5, cls="quiet", anchor="end"))
    p.append(text(444, 331, "vagy −errno", 10.5, cls="quiet", anchor="end"))
    p.append(text(24, 300, "A kernel a hívó folyamat nevében fut:", 11, cls="quiet"))
    p.append(text(24, 316, "ugyanaz a PID, saját kernelverem;", 11, cls="quiet"))
    p.append(text(24, 332, "az idő rendszeridőnek (sys) számít.", 11, cls="quiet"))
    p.append('<line x1="24" y1="402" x2="736" y2="402" class="grid" stroke-width="1"/>')
    p.append(text(24, 426, "Az x86-64 rendszerhívási konvenciója", 12, 600))
    rows = [("rax", "be: a szám, ki: az eredmény"), ("rdi rsi rdx", "1–3. argumentum"),
            ("r10 r8 r9", "4–6. argumentum"), ("rcx r11", "a syscall felülírja")]
    for i, (a, b) in enumerate(rows):
        x0 = 24 + (i % 2) * 300
        y = 450 + (i // 2) * 20
        p.append(mono(x0, y, a, 11, cls="acct"))
        p.append(text(x0 + 92, y, b, 10.5, cls="quiet"))
    p.append(text(24, 506, "A wrapper a −4095 és −1 közötti eredményt errno-vá alakítja, és −1-et ad vissza; minden más a valódi eredmény.", 11.5, cls="quiet"))
    p.append(text(24, 524, "A vDSO kis könyvtár, amelyet a kernel minden folyamatba leképez a csak kerneladatokat olvasó hívásokhoz.", 11.5, cls="quiet"))
    return svg(760, 542, title, "\n".join(p))


# ---------------- 3. fork, exec, exit, wait ----------------
def fork_exec_wait():
    m, ma = "fw", "fwa"
    title = "Hogyan futtat a shell egy parancsot: fork, exec, exit, wait"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    py, cy = 96, 196
    # parent line
    p.append(text(24, py - 30, "szülő: a shell, PID 100", 12, 600))
    p.append(f'<line x1="24" y1="{py}" x2="150" y2="{py}" class="acc" stroke-width="3"/>')
    p.append(f'<line x1="150" y1="{py}" x2="236" y2="{py}" class="acc" stroke-width="3"/>')
    p.append(f'<line x1="236" y1="{py}" x2="610" y2="{py}" class="edge" stroke-width="2" stroke-dasharray="5 4"/>')
    p.append(f'<line x1="610" y1="{py}" x2="736" y2="{py}" class="acc" stroke-width="3"/>')
    p.append(text(423, py - 8, "várakozik (S állapot), nem használ CPU-t", 11, cls="quiet", anchor="middle"))
    # fork
    p.append(f'<circle cx="150" cy="{py}" r="5" class="acct"/>')
    p.append(text(150, py - 10, "fork()", 12, 600, cls="acct", anchor="middle"))
    p.append(path(f"M150 {py + 4}C150 {cy - 30} 160 {cy} 196 {cy}", m, width=2))
    # wait call
    p.append(f'<circle cx="236" cy="{py}" r="5" class="acct"/>')
    p.append(text(236, py + 22, "waitpid(101)", 11.5, 600, anchor="middle"))
    # child line
    p.append(text(24, cy + 4, "gyerek: PID 101", 12, 600))
    p.append(f'<line x1="200" y1="{cy}" x2="320" y2="{cy}" class="c2s" stroke-width="3"/>')
    p.append(text(260, cy - 10, "shellkód (másolat)", 10.5, cls="quiet", anchor="middle"))
    p.append(f'<circle cx="320" cy="{cy}" r="5" class="c2"/>')
    p.append(text(320, cy + 22, "execve(\"/usr/bin/ls\")", 11.5, 600, anchor="middle"))
    p.append(f'<line x1="320" y1="{cy}" x2="520" y2="{cy}" class="c2s" stroke-width="3"/>')
    p.append(text(420, cy - 10, "az ls fut: ugyanaz a PID, új program", 10.5, cls="quiet", anchor="middle"))
    p.append(f'<circle cx="520" cy="{cy}" r="5" class="c2"/>')
    p.append(text(520, cy + 22, "exit(0)", 11.5, 600, anchor="middle"))
    p.append(f'<line x1="520" y1="{cy}" x2="610" y2="{cy}" class="bads" stroke-width="2" stroke-dasharray="3 3"/>')
    p.append(text(565, cy - 10, "zombi", 11, 600, cls="bad", anchor="middle"))
    # SIGCHLD and reap
    p.append(path(f"M610 {cy - 4}V{py + 8}", ma, cls="acc", width=1.5))
    p.append(text(618, (py + cy) / 2 - 4, "SIGCHLD; wait: 101,", 10.5, cls="quiet"))
    p.append(text(618, (py + cy) / 2 + 11, "állapot 0; begyűjtve", 10.5, cls="quiet"))
    p.append(text(736, py - 8, "következő prompt", 10.5, cls="quiet", anchor="end"))
    # what each call does
    rows = [("fork()", "lemásolja a hívót (ugyanaz a program és a fájlok, copy-on-write memória); a szülőben 101, a gyerekben 0"),
            ("execve()", "lecseréli a hívó folyamat programját: új kód, adatok, heap és verem; a PID és a fájlok maradnak"),
            ("exit()", "befejezi a folyamatot; a kernel felszabadítja a memóriáját, csak a kilépési állapot marad (zombi)"),
            ("waitpid()", "blokkol, amíg egy gyerek be nem fejeződik, visszaadja az állapotát, és eltávolítja a zombit")]
    for i, (a, b) in enumerate(rows):
        y = 268 + i * 22
        p.append(mono(24, y, a, 11.5, cls="acct"))
        p.append(text(110, y, b, 11, cls="quiet"))
    return svg(760, 356, title, "\n".join(p))


# ---------------- 4. File descriptors after redirection ----------------
def fd_tables():
    m = "fd"
    title = "ls /etc | grep ^host >hosts.txt: a minish által az exec előtt felépített leírótáblák"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(24, 60, "folyamatonként: leírótábla", 12, 600))
    p.append(text(300, 60, "kernel: megnyitott fájl leírások", 12, 600))
    p.append(text(560, 60, "kernel: objektumok", 12, 600))
    tx, tw, rh = 24, 150, 24

    def table(y0, name, rows):
        out = [text(tx, y0 - 6, name, 11.5, 600, cls="acct")]
        ys = []
        for i, lab in enumerate(rows):
            y = y0 + i * (rh + 4)
            out.append(rect(tx, y, tw, rh, "tint", rx=3))
            out.append(mono(tx + 10, y + 16, lab, 11))
            ys.append(y + rh / 2)
        return out, ys
    t1, ls_y = table(92, "ls (1. gyerek)", ["0  stdin", "1  stdout", "2  stderr"])
    t2, gr_y = table(232, "grep (2. gyerek)", ["0  stdin", "1  stdout", "2  stderr"])
    p += t1 + t2
    dx, dw, dh = 300, 200, 34
    desc = {"pw": (84, ["pipe, író vég", "csak írás"]),
            "pr": (136, ["pipe, olvasó vég", "csak olvasás"]),
            "tty": (204, ["terminál", "írás/olvasás, mind közös"]),
            "file": (270, ["hosts.txt", "csak írás, pozíció 0"])}
    for k, (y, lines) in desc.items():
        p += boxt(dx, y, dw, dh, lines, "c2" if k in ("pw", "pr") else "plain", 11.5, 600, rx=4)
    ox, ow = 560, 176
    p += boxt(ox, 110, ow, 34, ["pipe-puffer", "64 KiB a kernelmemóriában"], "acc", 11.5, 600, rx=4)
    p += boxt(ox, 204, ow, 34, ["terminál eszköz", "/dev/pts/0"], "plain", 11.5, 600, rx=4)
    p += boxt(ox, 270, ow, 34, ["a hosts.txt inode-ja", "a fájlrendszeren"], "plain", 11.5, 600, rx=4)

    def arrow(y1, key):
        y2 = desc[key][0] + dh / 2
        return path(f"M{tx + tw} {y1}C{tx + tw + 60} {y1} {dx - 60} {y2} {dx - 2} {y2}", m)
    for y, k in zip(ls_y, ["tty", "pw", "tty"]):
        p.append(arrow(y, k))
    for y, k in zip(gr_y, ["pr", "file", "tty"]):
        p.append(arrow(y, k))
    for k, oy in (("pw", 127), ("pr", 127), ("tty", 221), ("file", 287)):
        y1 = desc[k][0] + dh / 2
        p.append(path(f"M{dx + dw} {y1}C{dx + dw + 30} {y1} {ox - 30} {oy} {ox - 2} {oy}", m))
    p.append(text(24, 344, "A pipe() mindkét véget a shellnek adja; fork után az 1. gyerek dup2(író vég, 1), a 2. gyerek dup2(olvasó vég, 0) hívást végez;", 11.5, cls="quiet"))
    p.append(text(24, 362, "a 2. gyerek megnyitja a hosts.txt-t is, és dup2(fd, 1). Minden fölösleges leírót bezárnak, majd mindkét gyerek execve()-t hív:", 11.5, cls="quiet"))
    p.append(text(24, 380, "az ls és a grep egyszerűen a 0-s, 1-es és 2-es leírót használja, és sosem tud a pipe-ról vagy a fájlról.", 11.5, cls="quiet"))
    return svg(760, 398, title, "\n".join(p))


# ---------------- 5. What threads share ----------------
def threads_share():
    title = "Egy folyamat, több szál: min osztoznak, és mi az egyes szálak sajátja"
    p = [text(24, 30, title, 15, 600)]
    p.append(rect(24, 48, 712, 314, "plain", rx=10))
    p.append(text(40, 70, "folyamat, PID 24450 (a threads bemutató)", 12.5, 600))
    p.append(text(40, 92, "minden szál közösen használja", 12, 600, cls="acct"))
    shared = ["kód (text)", "globálisok: data, BSS", "heap", "memóriatérkép, laptáblák",
              "megnyitott fájlok (leírók)", "szignálkezelők", "PID, UID, GID", "aktuális könyvtár, korlátok"]
    bw, bh = 162, 30
    for i, lab in enumerate(shared):
        x = 40 + (i % 4) * (bw + 10)
        y = 102 + (i // 4) * (bh + 8)
        p += boxt(x, y, bw, bh, [lab], "acc", 11.5, 400, rx=4)
    p.append(text(40, 200, "az egyes szálak sajátja", 12, 600, cls="c2"))
    own = ["TID", "regiszterek (PC, SP, …)", "verem", "TLS (szálankénti tároló)", "szignálmaszk", "állapot, prioritás, CPU"]
    tw = 162
    for t in range(4):
        x = 40 + t * (tw + 10)
        name = "fő szál" if t == 0 else f"{t - 1}. szál"
        tid = 24450 + t
        p.append(rect(x, 210, tw, 140, "c2", rx=6))
        p.append(text(x + tw / 2, 228, f"{name}  (TID {tid})", 11.5, 600, anchor="middle"))
        for j, lab in enumerate(own[1:]):
            p.append(text(x + 12, 250 + j * 20, "• " + lab, 11, cls="quiet"))
    p.append(text(24, 386, "A Linux minden szálat tasknak hív; egy folyamat taskjainak közös a szálcsoport-azonosítója (ezt adja a getpid()),", 11.5, cls="quiet"))
    p.append(text(24, 404, "a gettid() a task saját azonosítóját. Új szál: egy verem és egy task_struct; új folyamathoz saját címtartomány is kell.", 11.5, cls="quiet"))
    return svg(760, 422, title, "\n".join(p))


# ---------------- 6. Threading models ----------------
def thread_models():
    m = "tm"
    title = "Felhasználói szálak leképezése kernelszálakra: N:1, 1:1 és M:N"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    pw, gap = 228, 18
    heads = [("N:1 (felhasználói szintű szálak)", "korai Java green threads, GNU Pth"),
             ("1:1 (kernelszintű szálak)", "Linux NPTL, Windows, macOS"),
             ("M:N (hibrid)", "Go goroutine-ok, Java virtuális szálak")]
    uy, ky, cyy = 112, 238, 312
    for k, (h, ex) in enumerate(heads):
        x0 = 24 + k * (pw + gap)
        p.append(text(x0, 60, h, 13, 600))
        p.append(text(x0, 78, ex, 11, cls="quiet"))
        p.append(rect(x0, 90, pw, 120, "plain", rx=8))
        p.append(text(x0 + 8, 106, "felhasználói tér", 10.5, cls="quiet"))
        p.append(f'<line x1="{x0}" y1="222" x2="{x0 + pw}" y2="222" class="grid" stroke-width="1.5" stroke-dasharray="5 4"/>')
        p.append(text(x0 + 8, 290, "kernel", 10.5, cls="quiet"))
        # CPUs
        for c in range(2):
            cx = x0 + 40 + c * 100
            p += boxt(cx, cyy, 64, 26, [f"CPU {c}"], "tint", 11, 600, rx=4)
        n_user = 4 if k != 1 else 4
        xs = [x0 + 30 + i * 56 for i in range(n_user)]
        for x in xs:
            p.append(f'<circle cx="{x}" cy="{uy + 18}" r="11" class="c2f"/>')
            p.append(f'<circle cx="{x}" cy="{uy + 18}" r="11" fill="none" class="c2s" stroke-width="1.5"/>')
        if k == 0:
            p += boxt(x0 + 30, 170, pw - 60, 30, ["a szálkönyvtár ütemezője"], "c2", 11, 600, rx=4)
            for x in xs:
                p.append(path(f"M{x} {uy + 30}V{168}", m))
            kx = [x0 + pw / 2]
        elif k == 1:
            kx = xs
            for x in xs:
                p.append(path(f"M{x} {uy + 30}V{ky - 4}", m))
        else:
            p += boxt(x0 + 30, 170, pw - 60, 30, ["a futtatókörnyezet ütemezője"], "c2", 11, 600, rx=4)
            for x in xs:
                p.append(path(f"M{x} {uy + 30}V{168}", m))
            kx = [x0 + 70, x0 + pw - 70]
        for x in kx:
            p.append(rect(x - 14, ky, 28, 30, "acc", rx=4))
            if k != 1:
                p.append(path(f"M{x} {202 if k != 1 else uy + 30}V{ky - 4}", m))
        p.append(text(x0 + pw - 8, ky + 20, f"{len(kx)} kernelszál", 10.5, cls="quiet", anchor="end") if k == 0 else "")
    p.append(text(24, 368, "N:1: a váltás olcsó, de egy blokkoló rendszerhívás minden szálat megállít, és csak egy CPU-t használ.", 11.5, cls="quiet"))
    p.append(text(24, 386, "1:1: valódi párhuzamosság és független blokkolás; minden szál egy kerneltaskba és kernelbeli váltásba kerül.", 11.5, cls="quiet"))
    p.append(text(24, 404, "M:N: sok olcsó szál néhány kernelszálon; a futtatókörnyezetnek ki kell kerülnie a blokkoló hívásokat.", 11.5, cls="quiet"))
    p.append(text(24, 424, "Narancs körök: a program által létrehozott szálak; kék: a kernel által ütemezett szálak.", 11.5, cls="quiet"))
    return svg(760, 442, title, "\n".join(p))


# ---------------- 7. IPC: through the kernel or shared memory ----------------
def ipc_copies():
    m, ma = "ic", "ica"
    title = "Adatmozgatás folyamatok között, kétféleképpen"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # left panel
    p.append(text(24, 62, "Pipe, socket, üzenetsor: a kernelen keresztül", 13, 600))
    p += boxt(24, 80, 150, 48, ["A folyamat", "felhasználói puffer"], "c2", 11.5, 600)
    p += boxt(214, 80, 150, 48, ["B folyamat", "felhasználói puffer"], "c2", 11.5, 600)
    p.append('<line x1="24" y1="150" x2="364" y2="150" class="grid" stroke-width="1.5" stroke-dasharray="5 4"/>')
    p.append(text(28, 166, "kernel", 10.5, cls="quiet"))
    p += boxt(104, 196, 180, 48, ["kernelpuffer", "pipe- vagy socketpuffer, sor"], "acc", 11.5, 600)
    p.append(path("M80 130C80 180 90 220 100 220", m, width=1.6))
    p.append(text(24, 196, "write():", 11, 600))
    p.append(text(22, 211, "1. másolás", 10, cls="quiet"))
    p.append(path("M288 220C300 220 310 180 300 132", m, width=1.6))
    p.append(text(316, 196, "read():", 11, 600))
    p.append(text(316, 211, "2. másolás", 11, cls="quiet"))
    lines = ["üzenetenként két rendszerhívás és két másolás;",
             "a kernel szinkronizál: a read() alszik, amíg",
             "nem jön adat, a write() alszik, amíg tele a",
             "puffer; gépek között is működik (socketek)"]
    for i, t in enumerate(lines):
        p.append(text(24, 278 + i * 17, t, 11.5, cls="quiet"))
    # right panel
    x0 = 404
    p.append(text(x0, 62, "Osztott memória: ugyanazok a keretek", 13, 600))
    for i, name in enumerate(["A folyamat", "B folyamat"]):
        x = x0 + i * 182
        p.append(rect(x, 80, 150, 92, "plain", rx=6))
        p.append(text(x + 75, 98, name, 11.5, 600, anchor="middle"))
        p.append(text(x + 75, 114, "virtuális címtartomány", 10.5, cls="quiet", anchor="middle"))
        p += boxt(x + 20, 126, 110, 32, ["osztott terület"], "c2", 11, 600, rx=4)
    p.append('<line x1="404" y1="190" x2="736" y2="190" class="grid" stroke-width="1.5" stroke-dasharray="5 4"/>')
    p.append(text(x0 + 4, 206, "fizikai memória", 10.5, cls="quiet"))
    p += boxt(x0 + 96, 218, 140, 36, ["ugyanazok a lapkeretek"], "acc", 11, 600, rx=4)
    p.append(path(f"M{x0 + 75} 160C{x0 + 75} 200 {x0 + 100} 214 {x0 + 120} 216", m, width=1.6))
    p.append(path(f"M{x0 + 257} 160C{x0 + 257} 200 {x0 + 232} 214 {x0 + 212} 216", m, width=1.6))
    lines = ["shm_open() + mmap() után B rendszerhívás és",
             "másolás nélkül látja A írásait; a folyamatoknak",
             "viszont maguknak kell szinkronizálniuk: szemaforral,",
             "futexszel vagy atomi jelzővel a közös területen"]
    for i, t in enumerate(lines):
        p.append(text(x0, 278 + i * 17, t, 11.5, cls="quiet"))
    return svg(760, 360, title, "\n".join(p))


# ---------------- 8. Observability tools and the layers they see ----------------
def observability():
    m = "ob"
    title = "Az operációs rendszer munka közben: melyik eszköz melyik réteget látja"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    p.append(text(24, 60, "egy futó program rétegei", 12, 600))
    p.append(text(356, 60, "eszközök egy réteghez", 12, 600))
    p.append(text(606, 60, "minden réteghez", 12, 600))
    layers = [("alkalmazáskód", "a saját függvényeid", "c2"),
              ("könyvtárak", "libc, libstdc++, …", "c2"),
              ("rendszerhívás-interfész", "write, openat, clone, …", "plain"),
              ("kernel", "ütemező, VFS, hálózat, memória", "acc"),
              ("hardver", "CPU, gyorsítótárak, eszközök", "tint")]
    tools = [["gdb: megállít, memóriát vizsgál", "valgrind: memóriahibákat keres"],
             ["ltrace: megosztott könyvtárak hívásai"],
             ["strace: minden rendszerhívás és", "eredménye; -c számol, -T időt mér"],
             ["/proc, /sys: a folyamatok és a", "kernel állapota és számlálói"],
             ["perf stat: hardveres eseményszámlálók", "(ciklusok, utasítások, cache-hiányok)"]]
    for i, ((a, b, kind), tl) in enumerate(zip(layers, tools)):
        y = 70 + i * 50
        p += boxt(24, y, 280, 42, [a, b], kind, 12, 600, rx=4)
        p.append(rect(356, y, 226, 42, "plain", rx=4))
        for j, t in enumerate(tl):
            p.append(text(366, y + (26 if len(tl) == 1 else 17 + j * 16), t, 10.5, cls="ink" if j == 0 else "quiet"))
        p.append(path(f"M352 {y + 21}H308", m))
    for k, (y, h, lines) in enumerate([(70, 116, ["perf record", "másodpercenként", "sokszor mintát vesz", "a hívási veremből,", "mindkét módban"]),
                                       (194, 116, ["eBPF, bpftrace", "kis, ellenőrzött", "programok bármely", "probe-on; számlálás", "a kernelen belül"])]):
        p.append(rect(606, y, 130, h, "acc", rx=6))
        for j, t in enumerate(lines):
            p.append(text(616, y + 20 + j * 19, t, 11 if j else 12, 600 if j == 0 else 400, cls="ink" if j == 0 else "quiet"))
    p.append(text(24, 340, "A gdb és az strace a ptrace-t használja: a kernel minden eseménynél megállítja a folyamatot, ami pontos, de lassú. A perf és", 11.5, cls="quiet"))
    p.append(text(24, 358, "az eBPF a kernelen belülről, kis többletterheléssel figyel, ezért forgalmas éles rendszereken is használható.", 11.5, cls="quiet"))
    return svg(760, 376, title, "\n".join(p))


FIGS = [("address-space", address_space), ("syscall-path", syscall_path),
        ("fork-exec-wait", fork_exec_wait),
        ("fd-tables", fd_tables),
        ("threads-share", threads_share),
        ("thread-models", thread_models),
        ("ipc-copies", ipc_copies),
        ("observability", observability)]

if __name__ == "__main__":
    for name, f in FIGS:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
