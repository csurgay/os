"""Generate the SVG figures for the Operating System Security lecture (Hungarian texts).

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



def arrow(x1, y1, x2, y2, mid, cls="edge", width=1.4, dash=None):
    return path(f"M{x1} {y1}L{x2} {y2}", mid, cls=cls, width=width, dash=dash)


# ---------------- 1. Threat model and attack surface ----------------
def attack_surface():
    m, mb = "as", "asb"
    title = "Fenyegetésmodell: támadók, határok és a megbízható számítási bázis"
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    # attackers
    att = [(24, "távoli támadó", "hálózati kérések"), (204, "helyi felhasználó, app", "saját kódot futtat"),
           (384, "rosszindulatú eszköz", "DMA, firmware"), (564, "fizikai hozzáférés", "lopott laptop, evil maid")]
    for x, a, b in att:
        p += boxt(x, 50, 172, 42, [a, b], "bad", 12, 600)
    # user space
    W = 480
    p.append(text(24, 124, "felhasználói tér (felhasználói mód)", 12, 600, cls="quiet"))
    p.append(rect(24, 132, W, 62, "plain", rx=8))
    procs = [(36, "webszerver", "UID www-data"), (190, "sandboxolt app", "seccomp, MAC"), (344, "a te shelled", "UID 1000")]
    for x, a, b in procs:
        p += boxt(x, 142, 148, 42, [a, b], "c2", 12, 600)
    # boundary
    p.append(f'<line x1="24" y1="212" x2="{24 + W}" y2="212" class="bads" stroke-width="1.5" stroke-dasharray="6 4"/>')
    p.append(text(24, 206, "rendszerhívási határ:", 11, 600, cls="bad"))
    p.append(text(194, 206, "az egyetlen ajtó a kernelbe (5. előadás)", 11, 600, cls="bad"))
    # TCB
    p.append(rect(24, 222, W, 52, "acc", rx=8))
    p.append(text(24 + W / 2, 244, "kernel: referenciamonitor, driverek, fájlrendszerek", 12.5, 600, anchor="middle"))
    p.append(text(24 + W / 2, 262, "kernelmód; egyetlen hiba itt minden fenti ellenőrzést semmissé tehet", 11, cls="quiet", anchor="middle"))
    p.append(rect(24, 282, W, 46, "acc", rx=8))
    p.append(text(24 + W / 2, 302, "firmware, boot loader, CPU és mikrokódja, TPM", 12.5, 600, anchor="middle"))
    p.append(text(24 + W / 2, 318, "megbízunk benne, még mielőtt a kernel elindulna", 11, cls="quiet", anchor="middle"))
    # TCB bracket
    p.append(path("M516 222L526 222L526 328L516 328", cls="acc", width=1.5))
    p.append(text(536, 262, "megbízható számítási bázis", 12, 600, cls="acct"))
    p.append(text(536, 280, "minden, aminek működnie kell", 11, cls="quiet"))
    p.append(text(536, 296, "a szabályok érvényesüléséhez", 11, cls="quiet"))
    # attack arrows
    p.append(arrow(110, 92, 110, 140, mb, cls="bads"))
    p.append(arrow(280, 92, 270, 140, mb, cls="bads"))
    p.append(path("M154 184C170 200 180 210 190 224", mb, cls="bads", width=1.4))
    p.append(path("M480 92C480 160 560 200 508 238", mb, cls="bads", width=1.4, dash="4 3"))
    p.append(path("M720 92L720 314L508 314", mb, cls="bads", width=1.4, dash="4 3"))
    # legend of steps
    p.append(text(24, 356, "Tipikus támadás: (1) egy hálózati szolgáltatás hibájának kihasználása, kódfuttatás a felhasználójaként; (2) egy kernel- vagy", 11.5, cls="quiet"))
    p.append(text(24, 374, "setuid-hiba kihasználása, hogy root legyen (jogosultság-kiterjesztés); (3) megtelepedés, pl. a rendszerindítási láncban.", 11.5, cls="quiet"))
    p.append(text(24, 392, "Az eszközök közvetlenül a memóriát támadják (IOMMU), a fizikai támadók a lemezt (titkosítás) és a rendszerindítást (Secure Boot).", 11.5, cls="quiet"))
    p.append(text(24, 418, "Célok: bizalmasság (titkok olvasása), sértetlenség (kód vagy adat módosítása), rendelkezésre állás (összeomlasztás, kimerítés).", 11.5, 600))
    return svg(760, 436, title, "\n".join(p))


# ---------------- 2. A stack frame before and after an overflow ----------------
def stack_frame():
    m, mb = "sf", "sfb"
    title = "A verembeli buffer overflow azt írja felül, ami a puffer fölött van"
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    panels = [
        (24, "gcc -fno-stack-protector (overflow-plain)",
         [("a main kerete (alsó bájtok)", "bad", "AAAAAAAA 00", "még 8 bájt és a 0"),
          ("visszatérési cím", "bad", "0x4141414141414141", "korábban main+50"),
          ("elmentett rbp", "bad", "0x4141414141414141", ""),
          ("buf[8..15]", "bad", "AAAAAAAA", ""),
          ("buf[0..7]", "bad", "AAAAAAAA", "")],
         ["a ret a 0x4141414141414141 címet veszi ki:", "nem érvényes cím, SIGSEGV"], "bad"),
        (400, "gcc -fstack-protector-strong (overflow-canary)",
         [("visszatérési cím", "bad", "0x0000555555555200", "alsó bájtja nullázva"),
          ("elmentett rbp", "bad", "0x4141414141414141", ""),
          ("canary (véletlen, alsó bájt 00)", "bad", "0x4141414141414141", ""),
          ("kitöltés (padding)", "bad", "AAAAAAAA", ""),
          ("buf[8..15]", "bad", "AAAAAAAA", ""),
          ("buf[0..7]", "bad", "AAAAAAAA", "")],
         ["ellenőrzés a leave/ret előtt: a canary változott", "→ __stack_chk_fail → abort; a ret nem fut le"], "acc"),
    ]
    for x0, head, cells, verdict, vk in panels:
        p.append(text(x0, 62, head, 12, 600))
        p.append(text(x0, 80, "magasabb címek", 10.5, cls="quiet"))
        ch = 34
        top = 88 if len(cells) == 6 else 88 + ch
        for i, (name, kind, val, note) in enumerate(cells):
            y = top + i * ch
            p.append(rect(x0, y, 200, ch - 4, kind, rx=4))
            p.append(text(x0 + 8, y + 19, name, 11.5, 600))
            if val:
                p.append(mono(x0 + 208, y + 13, val, 10.5, cls="bad" if kind == "bad" else "ink"))
            if note:
                p.append(text(x0 + 208, y + 26, note, 10.5, cls="quiet"))
        yb = top + len(cells) * ch
        p.append(text(x0, yb + 12, "alacsonyabb címek (a verem lefelé nő)", 10.5, cls="quiet"))
        # write direction arrow
        p.append(arrow(x0 - 8 + 0, yb - 6, x0 - 8 + 0, top + (0 if len(cells) == 5 else 2) * ch + 6, mb, cls="bads", width=1.6))
        p += boxt(x0, yb + 26, 332, 46, verdict, vk, 11.5, 600)
    p.append(text(24, 392, "A strcpy 40 'A' bájtot és egy lezáró 0-t másol egy 16 bájtos pufferbe, alacsony címtől a magas felé (mért elrendezés, gcc 13 -O0).", 11.5, cls="quiet"))
    p.append(text(24, 410, "A canary a lokális pufferek és az elmentett regiszterek között ül, így egy lineáris túlcsordulás előbb őt változtatja meg.", 11.5, cls="quiet"))
    return svg(760, 428, title, "\n".join(p))


# ---------------- 3. Control-flow integrity in hardware ----------------
def cfi():
    m, mb, ma = "cf", "cfb", "cfa"
    title = "Hardveres control-flow integrity: shadow stack és landing padek"
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # left: shadow stack
    p.append(text(24, 62, "Visszafelé mutató élek: a shadow stack (Intel CET SS)", 12.5, 600))
    p.append(text(24, 98, "adatverem (írható)", 11, 600, cls="quiet"))
    p.append(text(214, 98, "shadow stack (védett lapokon)", 11, 600, cls="quiet"))
    rows = [("lokális változók", "plain", None), ("elmentett rbp", "plain", None), ("visszatérési cím", "bad", "overwritten")]
    for i, (s, k, note) in enumerate(rows):
        y = 106 + i * 34
        p += boxt(24, y, 150, 28, [s], k, 11.5)
    p += boxt(214, 106 + 2 * 34, 150, 28, ["visszatérési cím (másolat)"], "acc", 11.5)
    p.append(text(24, 224, "A CALL mindkét verembe beírja a visszatérési címet.", 11.5, cls="quiet"))
    p.append(text(24, 242, "A RET mindkettőt kiveszi és összeveti:", 11.5, cls="quiet"))
    p += boxt(24, 254, 340, 40, ["eltérnek → control-protection kivétel (#CP)", "a folyamat leáll, mielőtt ugrana"], "bad", 11.5, 600)
    p.append(arrow(176, 189, 210, 189, ma, cls="acc"))
    p.append(text(193, 182, "=?", 11, 600, cls="acct", anchor="middle"))
    p.append(text(24, 318, "Arm: a PAC titkos kulccsal aláírja a visszatérési", 11.5, cls="quiet"))
    p.append(text(24, 336, "címet a fel nem használt felső bitjeibe; az AUT a RET előtt ellenőrzi.", 11.5, cls="quiet"))
    # right: IBT
    x = 400
    p.append(text(x, 62, "Előre mutató élek: landing padek (Intel IBT, Arm BTI)", 12.5, 600))
    p += boxt(x, 82, 130, 36, ["call *%rax", "függvénymutató"], "c2", 11.5, 600)
    p.append(text(x + 186, 98, "érvényes cél, f():", 11, 600))
    p.append(rect(x + 186, 104, 150, 60, "plain", rx=4))
    p.append(mono(x + 196, 122, "endbr64", 11.5, cls="acct"))
    p.append(mono(x + 196, 140, "push %rbp", 11.5))
    p.append(mono(x + 196, 158, "...", 11.5))
    p.append(path(f"M{x + 130} 100C{x + 160} 104 {x + 168} 116 {x + 192} 118", ma, cls="acc", width=1.5))
    p.append(text(x + 186, 196, "sérült mutató: a g() közepe:", 11, 600))
    p.append(rect(x + 186, 202, 150, 44, "plain", rx=4))
    p.append(mono(x + 196, 220, "mov %rdi,%rax", 11.5))
    p.append(mono(x + 196, 238, "...", 11.5))
    p.append(path(f"M{x + 64} 118C{x + 70} 180 {x + 140} 218 {x + 192} 220", mb, cls="bads", width=1.5))
    p += boxt(x, 262, 336, 40, ["a célon nincs endbr64 → #CP", "az ugrást a CPU megtagadja"], "bad", 11.5, 600)
    p.append(text(x, 318, "A fordító minden olyan helyre endbr64-et (Arm: BTI) tesz,", 11.5, cls="quiet"))
    p.append(text(x, 336, "ahová egy indirekt hívás vagy ugrás jogosan érkezhet.", 11.5, cls="quiet"))
    p.append(text(24, 372, "Mindkettő megállítja a kód-újrafelhasználást (ROP, JOP), amely visszatérési címek vagy mutatók elrontásával fűz össze", 11.5, cls="quiet"))
    p.append(text(24, 390, "meglévő utasításokat. Kell hozzá CPU, fordító (-fcf-protection, -mbranch-protection), kernel és minden könyvtár támogatása.", 11.5, cls="quiet"))
    return svg(760, 408, title, "\n".join(p))


# ---------------- 7. The boot chain: verify and measure ----------------
def boot_chain():
    m, ma, mb = "bc", "bca", "bcb"
    title = "A bizalmi lánc: minden lépcső ellenőrzi (Secure Boot) és megméri (TPM) a következőt"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    stages = [("UEFI firmware", "flashben; bizalmi", "gyökér, kulcsokkal"), ("shim", "aláírója a", "Microsoft UEFI CA"),
              ("GRUB vagy", "systemd-boot", "distro aláírásával"), ("kernel +", "initramfs", "aláírt kernel"),
              ("init", "(systemd)", "felhasználói tér")]
    w, gap, y = 128, 18, 92
    for i, (a, b, c) in enumerate(stages):
        x = 24 + i * (w + gap)
        p += boxt(x, y, w, 62, [a, b, c], "acc" if i == 0 else "tint", 12, 600)
        if i < 4:
            p.append(arrow(x + w + 1, y + 31, x + w + gap - 1, y + 31, m, width=1.5))
    p.append(text(24, 64, "Secure Boot: a következő lépcső aláírásának ellenőrzése indítás előtt; ha nem egyezik, nincs rendszerindítás", 11.5, 600, cls="acct"))
    for i in range(4):
        x = 24 + i * (w + gap) + w / 2
        p.append(path(f"M{x} 72L{x} 88", ma, cls="acc"))
    # TPM
    ty = 214
    p.append(text(24, 176, "Measured boot: a következő lépcső hash-ének bemérése egy TPM-regiszterbe (PCR) indítás előtt", 11.5, 600, cls="c2"))
    pcr = ["PCR 0, 2", "PCR 4, 7", "PCR 4, 8", "PCR 9 vagy 11"]
    for i, s in enumerate(pcr):
        x = 24 + i * (w + gap) + w / 2
        p.append(path(f"M{x} {y + 64}L{x} {y + 70}", None, cls="c2s", width=1.3))
        p.append(path(f"M{x} 184L{x} {ty + 8}", m, cls="c2s", width=1.3, dash="4 3"))
        p.append(text(x + 6, ty - 6, s, 10.5, 600, cls="quiet"))
    p.append(rect(24, ty + 10, 566, 64, "c2", rx=8))
    p.append(text(36, ty + 32, "TPM: PCR[n] ← SHA-256(PCR[n] ‖ az új komponens hash-e)", 12, 600))
    p.append(text(36, ty + 50, "Egy PCR-t csak kiterjeszteni lehet, beállítani soha. Végső értéke a lefutott", 11, cls="quiet"))
    p.append(text(36, ty + 66, "összes komponens ujjlenyomata, sorrendben. Az event log minden lépést rögzít.", 11, cls="quiet"))
    # uses
    p += boxt(24, ty + 92, 270, 58, ["sealing", "a lemezkulcsot csak egyező PCR-eknél", "adja ki (TPM-hez kötött titkosítás)"], "plain", 11.5, 600)
    p += boxt(320, ty + 92, 270, 58, ["távoli attestation", "a TPM aláír egy quote-ot a PCR-ekről;", "az ellenőrző összeveti őket"], "plain", 11.5, 600)
    p.append(arrow(160, ty + 76, 160, ty + 90, m))
    p.append(arrow(455, ty + 76, 455, ty + 90, m))
    p.append(text(612, ty + 30, "A Secure Boot", 11.5, 600))
    p.append(text(612, ty + 48, "megállítja az", 11.5, 600))
    p.append(text(612, ty + 70, "aláíratlan kódot; a", 11.5, 600))
    p.append(text(612, ty + 88, "measured boot csak", 11.5, 600))
    p.append(text(612, ty + 106, "rögzít, mások döntenek.", 11.5, 600))
    p.append(text(24, 394, "A PCR-számozás a TCG PC Client profilt és a Linux TPM PCR registryt követi: 0 firmware-kód, 2 option ROM-ok, 4 boot loader,", 11.5, cls="quiet"))
    p.append(text(24, 412, "7 a Secure Boot állapota és kulcsai, 8 GRUB-parancsok, 9 a GRUB által betöltött fájlok (a kernel), 11 unified kernel image-ek.", 11.5, cls="quiet"))
    return svg(760, 430, title, "\n".join(p))


# ---------------- 8. Trusted execution environments ----------------
def tee():
    title = "Trusted execution environmentek: kiben kell még megbízni?"
    p = [text(24, 30, title, 15, 600)]
    cols = [
        ("Arm TrustZone", [("normal world: alkalmazások", "c2"), ("rich OS (Android, Linux)", "c2"),
                           ("secure world: trusted appok", "acc"), ("trusted OS (pl. OP-TEE)", "acc"),
                           ("secure monitor (EL3)", "acc")],
         ["a CPU váltja a világokat; a secure", "memória és eszközök láthatatlanok", "a normal world, még kernele számára is"]),
        ("Intel SGX enclave", [("alkalmazás", "c2"), ("enclave (titkosított lapok)", "acc"),
                               ("operációs rendszer", "bad"), ("hypervisor", "bad"), ("CPU-tok", "acc")],
         ["csak a CPU és az enclave kódja", "megbízható; kliens-CPU-kon", "2021 óta elavult"]),
        ("Confidential VM (SEV-SNP, TDX)", [("vendég alkalmazásai", "acc"), ("vendégkernel", "acc"),
                                            ("hypervisor, gazda OS", "bad"), ("felhőüzemeltető", "bad"),
                                            ("CPU + biztonsági processzora", "acc")],
         ["az egész VM titkosított és sértetlen-", "ségvédett a gazdával szemben;", "induláskor attestation"]),
    ]
    for i, (head, layers, notes) in enumerate(cols):
        x = 24 + i * 246
        p.append(text(x, 62, head, 12.5, 600))
        for j, (s, k) in enumerate(layers):
            p += boxt(x, 74 + j * 38, 226, 32, [s], k, 11.5, 600 if k != "bad" else 400)
        for j, s in enumerate(notes):
            p.append(text(x, 280 + j * 17, s, 11, cls="quiet"))
    # legend
    p.append(rect(24, 344, 18, 14, "acc", rx=3))
    p.append(text(48, 356, "megbízható (a TCB része)", 11.5))
    p.append(rect(234, 344, 18, 14, "bad", rx=3))
    p.append(text(258, 356, "nem megbízható: lehet rosszindulatú", 11.5))
    p.append(rect(474, 344, 18, 14, "c2", rx=3))
    p.append(text(498, 356, "közönséges, a szokásos elkülönítéssel", 11.5))
    p.append(text(24, 386, "Az Apple Secure Enclave még tovább megy: külön processzormag saját boot ROM-mal és OS-sel, ugyanazon a chipen.", 11.5, cls="quiet"))
    return svg(760, 404, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("attack-surface", attack_surface), ("stack-frame", stack_frame), ("cfi", cfi),
                    ("boot-chain", boot_chain), ("tee", tee)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
