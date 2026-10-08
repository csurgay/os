"""Generate the SVG figures for the Operating System Security lecture.

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
    title = "Threat model: attackers, boundaries and the trusted computing base"
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    # attackers
    att = [(24, "remote attacker", "network requests"), (204, "local user or app", "runs its own code"),
           (384, "malicious device", "DMA, firmware"), (564, "physical access", "stolen laptop, evil maid")]
    for x, a, b in att:
        p += boxt(x, 50, 172, 42, [a, b], "bad", 12, 600)
    # user space
    W = 480
    p.append(text(24, 124, "user space (user mode)", 12, 600, cls="quiet"))
    p.append(rect(24, 132, W, 62, "plain", rx=8))
    procs = [(36, "web server", "UID www-data"), (190, "sandboxed app", "seccomp, MAC"), (344, "your shell", "UID 1000")]
    for x, a, b in procs:
        p += boxt(x, 142, 148, 42, [a, b], "c2", 12, 600)
    # boundary
    p.append(f'<line x1="24" y1="212" x2="{24 + W}" y2="212" class="bads" stroke-width="1.5" stroke-dasharray="6 4"/>')
    p.append(text(24, 206, "system-call boundary: the only door into the kernel (lecture 5)", 11, 600, cls="bad"))
    # TCB
    p.append(rect(24, 222, W, 52, "acc", rx=8))
    p.append(text(24 + W / 2, 244, "kernel: reference monitor, drivers, file systems", 12.5, 600, anchor="middle"))
    p.append(text(24 + W / 2, 262, "kernel mode; one bug here can defeat every check above", 11, cls="quiet", anchor="middle"))
    p.append(rect(24, 282, W, 46, "acc", rx=8))
    p.append(text(24 + W / 2, 302, "firmware, boot loader, CPU and its microcode, TPM", 12.5, 600, anchor="middle"))
    p.append(text(24 + W / 2, 318, "trusted before the kernel even starts", 11, cls="quiet", anchor="middle"))
    # TCB bracket
    p.append(path("M516 222L526 222L526 328L516 328", cls="acc", width=1.5))
    p.append(text(536, 262, "trusted computing base", 12, 600, cls="acct"))
    p.append(text(536, 280, "everything that must work", 11, cls="quiet"))
    p.append(text(536, 296, "for the policy to hold", 11, cls="quiet"))
    # attack arrows
    p.append(arrow(110, 92, 110, 140, mb, cls="bads"))
    p.append(arrow(280, 92, 270, 140, mb, cls="bads"))
    p.append(path("M154 184C170 200 180 210 190 224", mb, cls="bads", width=1.4))
    p.append(path("M480 92C480 160 560 200 508 238", mb, cls="bads", width=1.4, dash="4 3"))
    p.append(path("M720 92L720 314L508 314", mb, cls="bads", width=1.4, dash="4 3"))
    # legend of steps
    p.append(text(24, 356, "Typical attack: (1) exploit a bug in a network service and run code as its user; (2) exploit a kernel or setuid bug", 11.5, cls="quiet"))
    p.append(text(24, 374, "to become root (privilege escalation); (3) persist, e.g. in the boot chain. Devices attack memory directly (IOMMU),", 11.5, cls="quiet"))
    p.append(text(24, 392, "physical attackers the disk (encryption) and the boot process (Secure Boot, measured boot).", 11.5, cls="quiet"))
    p.append(text(24, 418, "Goals: confidentiality (read secrets), integrity (change code or data), availability (crash or exhaust the system).", 11.5, 600))
    return svg(760, 436, title, "\n".join(p))


# ---------------- 2. A stack frame before and after an overflow ----------------
def stack_frame():
    m, mb = "sf", "sfb"
    title = "A stack buffer overflow overwrites what lies above the buffer"
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    panels = [
        (24, "gcc -fno-stack-protector (overflow-plain)",
         [("main's frame (lowest bytes)", "bad", "AAAAAAAA 00", "8 more bytes and the 0"),
          ("return address", "bad", "0x4141414141414141", "was main+50"),
          ("saved rbp", "bad", "0x4141414141414141", ""),
          ("buf[8..15]", "bad", "AAAAAAAA", ""),
          ("buf[0..7]", "bad", "AAAAAAAA", "")],
         ["ret pops 0x4141414141414141:", "not a valid address, SIGSEGV"], "bad"),
        (400, "gcc -fstack-protector-strong (overflow-canary)",
         [("return address", "bad", "0x0000555555555200", "low byte zeroed"),
          ("saved rbp", "bad", "0x4141414141414141", ""),
          ("canary (random, low byte 00)", "bad", "0x4141414141414141", ""),
          ("padding", "bad", "AAAAAAAA", ""),
          ("buf[8..15]", "bad", "AAAAAAAA", ""),
          ("buf[0..7]", "bad", "AAAAAAAA", "")],
         ["checked before leave/ret: canary changed", "→ __stack_chk_fail → abort; ret never runs"], "acc"),
    ]
    for x0, head, cells, verdict, vk in panels:
        p.append(text(x0, 62, head, 12, 600))
        p.append(text(x0, 80, "higher addresses", 10.5, cls="quiet"))
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
        p.append(text(x0, yb + 12, "lower addresses (the stack grows down)", 10.5, cls="quiet"))
        # write direction arrow
        p.append(arrow(x0 - 8 + 0, yb - 6, x0 - 8 + 0, top + (0 if len(cells) == 5 else 2) * ch + 6, mb, cls="bads", width=1.6))
        p += boxt(x0, yb + 26, 332, 46, verdict, vk, 11.5, 600)
    p.append(text(24, 392, "strcpy copies 40 'A' bytes and a terminating 0 into a 16-byte buffer, from low to high addresses (measured layout, gcc 13 -O0).", 11.5, cls="quiet"))
    p.append(text(24, 410, "The canary sits between the local buffers and the saved registers, so a linear overflow must change it before it reaches them.", 11.5, cls="quiet"))
    return svg(760, 428, title, "\n".join(p))


# ---------------- 3. Control-flow integrity in hardware ----------------
def cfi():
    m, mb, ma = "cf", "cfb", "cfa"
    title = "Control-flow integrity in hardware: shadow stack and landing pads"
    p = [f"<defs>{marker(m)}{marker(mb, 'bad')}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # left: shadow stack
    p.append(text(24, 62, "Backward edges: the shadow stack (Intel CET SS)", 12.5, 600))
    p.append(text(24, 98, "data stack (writable)", 11, 600, cls="quiet"))
    p.append(text(214, 98, "shadow stack (no ordinary writes)", 11, 600, cls="quiet"))
    rows = [("local variables", "plain", None), ("saved rbp", "plain", None), ("return addr", "bad", "overwritten")]
    for i, (s, k, note) in enumerate(rows):
        y = 106 + i * 34
        p += boxt(24, y, 150, 28, [s], k, 11.5)
    p += boxt(214, 106 + 2 * 34, 150, 28, ["return addr (copy)"], "acc", 11.5)
    p.append(text(24, 224, "CALL pushes the return address on both stacks.", 11.5, cls="quiet"))
    p.append(text(24, 242, "RET pops both and compares them:", 11.5, cls="quiet"))
    p += boxt(24, 254, 340, 40, ["different → control-protection fault (#CP)", "the process is killed before it jumps"], "bad", 11.5, 600)
    p.append(arrow(176, 189, 210, 189, ma, cls="acc"))
    p.append(text(193, 182, "=?", 11, 600, cls="acct", anchor="middle"))
    p.append(text(24, 318, "Arm: PAC signs the return address with a secret", 11.5, cls="quiet"))
    p.append(text(24, 336, "key into its unused top bits; AUT checks it before RET.", 11.5, cls="quiet"))
    # right: IBT
    x = 400
    p.append(text(x, 62, "Forward edges: landing pads (Intel IBT, Arm BTI)", 12.5, 600))
    p += boxt(x, 82, 130, 36, ["call *%rax", "function pointer"], "c2", 11.5, 600)
    p.append(text(x + 186, 98, "valid target f():", 11, 600))
    p.append(rect(x + 186, 104, 150, 60, "plain", rx=4))
    p.append(mono(x + 196, 122, "endbr64", 11.5, cls="acct"))
    p.append(mono(x + 196, 140, "push %rbp", 11.5))
    p.append(mono(x + 196, 158, "...", 11.5))
    p.append(path(f"M{x + 130} 100C{x + 160} 104 {x + 168} 116 {x + 192} 118", ma, cls="acc", width=1.5))
    p.append(text(x + 186, 196, "corrupted pointer: middle of g():", 11, 600))
    p.append(rect(x + 186, 202, 150, 44, "plain", rx=4))
    p.append(mono(x + 196, 220, "mov %rdi,%rax", 11.5))
    p.append(mono(x + 196, 238, "...", 11.5))
    p.append(path(f"M{x + 64} 118C{x + 70} 180 {x + 140} 218 {x + 192} 220", mb, cls="bads", width=1.5))
    p += boxt(x, 262, 336, 40, ["no endbr64 at the target → #CP", "the jump is refused"], "bad", 11.5, 600)
    p.append(text(x, 318, "The compiler puts endbr64 (Arm: BTI) at every place", 11.5, cls="quiet"))
    p.append(text(x, 336, "an indirect call or jump may legitimately land.", 11.5, cls="quiet"))
    p.append(text(24, 372, "Both defences stop code-reuse attacks (ROP, JOP) that chain existing instructions by corrupting return addresses or pointers.", 11.5, cls="quiet"))
    p.append(text(24, 390, "They need support in the CPU, the compiler (-fcf-protection, -mbranch-protection), the kernel and every loaded library.", 11.5, cls="quiet"))
    return svg(760, 408, title, "\n".join(p))


# ---------------- 7. The boot chain: verify and measure ----------------
def boot_chain():
    m, ma, mb = "bc", "bca", "bcb"
    title = "The chain of trust: each stage verifies (Secure Boot) and measures (TPM) the next"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}{marker(mb, 'bad')}</defs>", text(24, 30, title, 15, 600)]
    stages = [("UEFI firmware", "in flash; root of", "trust, holds keys"), ("shim", "signed by the", "Microsoft UEFI CA"),
              ("GRUB or", "systemd-boot", "signed by distro"), ("kernel +", "initramfs", "signed kernel"),
              ("init", "(systemd)", "user space")]
    w, gap, y = 128, 18, 92
    for i, (a, b, c) in enumerate(stages):
        x = 24 + i * (w + gap)
        p += boxt(x, y, w, 62, [a, b, c], "acc" if i == 0 else "tint", 12, 600)
        if i < 4:
            p.append(arrow(x + w + 1, y + 31, x + w + gap - 1, y + 31, m, width=1.5))
    p.append(text(24, 64, "Secure Boot: verify the signature of the next stage before running it; refuse to boot if it does not match", 11.5, 600, cls="acct"))
    for i in range(4):
        x = 24 + i * (w + gap) + w / 2
        p.append(path(f"M{x} 72L{x} 88", ma, cls="acc"))
    # TPM
    ty = 214
    p.append(text(24, 176, "Measured boot: hash the next stage into a TPM register (PCR) before running it", 11.5, 600, cls="c2"))
    pcr = ["PCR 0, 2", "PCR 4, 7", "PCR 4, 8", "PCR 9 or 11"]
    for i, s in enumerate(pcr):
        x = 24 + i * (w + gap) + w / 2
        p.append(path(f"M{x} {y + 64}L{x} {y + 70}", None, cls="c2s", width=1.3))
        p.append(path(f"M{x} 184L{x} {ty + 8}", m, cls="c2s", width=1.3, dash="4 3"))
        p.append(text(x + 6, ty - 6, s, 10.5, 600, cls="quiet"))
    p.append(rect(24, ty + 10, 566, 64, "c2", rx=8))
    p.append(text(36, ty + 32, "TPM: PCR[n] ← SHA-256(PCR[n] ‖ hash of the new component)", 12, 600))
    p.append(text(36, ty + 50, "A PCR can only be extended, never set. Its final value is a fingerprint", 11, cls="quiet"))
    p.append(text(36, ty + 66, "of everything that ran, in order. An event log records each step.", 11, cls="quiet"))
    # uses
    p += boxt(24, ty + 92, 270, 58, ["sealing", "disk key released only if the", "PCRs match (TPM-bound encryption)"], "plain", 11.5, 600)
    p += boxt(320, ty + 92, 270, 58, ["remote attestation", "TPM signs a quote of the PCRs;", "a verifier compares them"], "plain", 11.5, 600)
    p.append(arrow(160, ty + 76, 160, ty + 90, m))
    p.append(arrow(455, ty + 76, 455, ty + 90, m))
    p.append(text(612, ty + 30, "Secure Boot stops", 11.5, 600))
    p.append(text(612, ty + 48, "unsigned code;", 11.5, 600))
    p.append(text(612, ty + 70, "measured boot only", 11.5, 600))
    p.append(text(612, ty + 88, "records, so that", 11.5, 600))
    p.append(text(612, ty + 106, "others can decide.", 11.5, 600))
    p.append(text(24, 394, "PCR numbers follow the TCG PC Client profile and the Linux TPM PCR registry: 0 firmware code, 2 option ROMs, 4 boot loader,", 11.5, cls="quiet"))
    p.append(text(24, 412, "7 Secure Boot state and keys, 8 GRUB commands, 9 files GRUB loads (the kernel), 11 unified kernel images.", 11.5, cls="quiet"))
    return svg(760, 430, title, "\n".join(p))


# ---------------- 8. Trusted execution environments ----------------
def tee():
    title = "Trusted execution environments: who still has to be trusted?"
    p = [text(24, 30, title, 15, 600)]
    cols = [
        ("Arm TrustZone", [("normal world: apps", "c2"), ("rich OS (Android, Linux)", "c2"),
                           ("secure world: trusted apps", "acc"), ("trusted OS (e.g. OP-TEE)", "acc"),
                           ("secure monitor (EL3)", "acc")],
         ["the CPU switches worlds; secure", "memory and devices are invisible", "to the normal world, even its kernel"]),
        ("Intel SGX enclave", [("application", "c2"), ("enclave (encrypted pages)", "acc"),
                               ("operating system", "bad"), ("hypervisor", "bad"), ("CPU package", "acc")],
         ["only the CPU and the enclave's", "code are trusted; deprecated", "on client CPUs since 2021"]),
        ("Confidential VM (SEV-SNP, TDX)", [("guest apps", "acc"), ("guest kernel", "acc"),
                                            ("hypervisor, host OS", "bad"), ("cloud operator", "bad"),
                                            ("CPU + its secure processor", "acc")],
         ["the whole VM is encrypted and", "integrity-protected against the", "host; attested at start"]),
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
    p.append(text(48, 356, "trusted (part of the TCB)", 11.5))
    p.append(rect(234, 344, 18, 14, "bad", rx=3))
    p.append(text(258, 356, "not trusted: may be malicious", 11.5))
    p.append(rect(474, 344, 18, 14, "c2", rx=3))
    p.append(text(498, 356, "ordinary, isolated as usual", 11.5))
    p.append(text(24, 386, "Apple's Secure Enclave goes one step further: a separate processor core with its own boot ROM and OS on the same chip.", 11.5, cls="quiet"))
    return svg(760, 404, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("attack-surface", attack_surface), ("stack-frame", stack_frame), ("cfi", cfi),
                    ("boot-chain", boot_chain), ("tee", tee)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
