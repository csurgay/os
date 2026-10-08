"""Generate the SVG figures for the Virtualization and Containerization lecture.

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


# ---------------- 7. Containers: images share layers, containers share the kernel ----------------
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

# ---------------- 8. Image, container, volume ----------------
def mono(x, y, s, size=12, cls="ink", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" text-anchor="{anchor}" '
            f'style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{esc(s)}</text>')


def image_container():
    m, ma = "ic", "ica"
    title = "An image is the read-only blueprint; each container adds a thin writable layer"
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
    p.append(text(sx, 66, "Image (read-only, shared)", 13, 600))
    cfg_y, cfg_h = 80, 76
    p.append(f'<rect x="{sx}" y="{cfg_y}" width="{sw}" height="{cfg_h}" rx="4" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="4 3"/>')
    p.append(text(sx + sw / 2, cfg_y + 20, "configuration (no files):", 11.5, 600, anchor="middle"))
    p.append(text(sx + sw / 2, cfg_y + 38, "port 8080, user 1000,", 11, cls="quiet", anchor="middle"))
    p.append(text(sx + sw / 2, cfg_y + 54, "working dir /data,", 11, cls="quiet", anchor="middle"))
    p.append(text(sx + sw / 2, cfg_y + 70, "command: tool serve", 11, cls="quiet", anchor="middle"))
    layers = [("/etc/app.conf", "layer 3"), ("/data, owner 1000", "layer 2"), ("/bin/tool", "layer 1")]
    lh = 36
    ly = cfg_y + cfg_h + 10
    for i, (n, tag) in enumerate(layers):
        y = ly + i * (lh + 4)
        p.append(rect(sx, y, sw, lh, "acc", rx=4))
        p.append(text(sx + 12, y + 23, n, 12, 600))
        p.append(text(sx + sw - 10, y + 23, tag, 11, cls="quiet", anchor="end"))
    base_y = ly + 3 * (lh + 4)
    p.append(text(sx + sw / 2, base_y + 16, "empty base (FROM scratch)", 11, cls="quiet", anchor="middle"))
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
    p.append(text(cx, 66, "Containers (instances)", 13, 600))
    for j, (name, wl, yy) in enumerate([("container c1", "writable layer: notes.txt", 80),
                                        ("container c2", "writable layer: (empty)", 186)]):
        p.append(f'<rect x="{cx}" y="{yy}" width="{cw}" height="84" rx="6" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="5 3"/>')
        p.append(text(cx + 10, yy + 20, name, 12, 600))
        p.append(rect(cx + 10, yy + 30, cw - 20, 24, "c2", rx=3))
        p.append(text(cx + cw / 2, yy + 47, wl, 11, anchor="middle"))
        p.append(text(cx + cw / 2, yy + 72, "+ the image's layers below", 11, cls="quiet", anchor="middle"))
        p.append(path(f"M{sx + sw + 4} {ly + 40 + j * 30}C{505} {ly + 40 + j * 30} {505} {yy + 64} {cx - 4} {yy + 64}", m))
    p.append(text(506, ly + 14, "run", 11, 600, cls="quiet", anchor="middle"))
    # volume
    vy = 300
    p.append(rect(cx, vy, cw, 46, "tint", rx=6))
    p.append(text(cx + cw / 2, vy + 19, "volume appdata", 12, 600, anchor="middle"))
    p.append(text(cx + cw / 2, vy + 36, "outlives every container", 11, cls="quiet", anchor="middle"))
    p.append(path(f"M{cx + cw / 2} {vy - 2}V{186 + 86}", ma, cls="acc", width=1.5))
    p.append(text(cx + cw / 2 + 8, vy - 12, "mounted at /data", 11, 600, cls="acct"))
    p.append(text(24, 386, "Writes in a container go to its own writable layer and are lost when the container is removed;", 11.5, cls="quiet"))
    p.append(text(24, 404, "data that must survive (a database, uploads) belongs on a volume. Solid arrows: build steps that add files.", 11.5, cls="quiet"))
    return svg(760, 424, title, "\n".join(p))


def boxt(x, y, w, h, lines, kind="tint", size=12, weight=400, rx=6, cls="ink"):
    """A box with one or more centred lines of text."""
    out = [rect(x, y, w, h, kind, rx=rx)]
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * (size + 3) / 2 + size * 0.36
    for i, s in enumerate(lines):
        out.append(text(x + w / 2, y0 + i * (size + 3), s, size, weight if i == 0 else 400,
                        cls if i == 0 else "quiet", anchor="middle"))
    return out


# ---------------- 1. Sensitive and privileged instructions ----------------
def sensitive():
    title = "Popek and Goldberg: every sensitive instruction must trap"
    p = [text(24, 30, title, 15, 600)]
    for k, (x0, head, ok) in enumerate([(24, "Virtualizable (e.g. IBM System/370)", True),
                                        (400, "Not virtualizable (classic 32-bit x86)", False)]):
        p.append(text(x0, 64, head, 13, 600))
        p.append(rect(x0, 76, 336, 236, "plain", rx=10))
        p.append(text(x0 + 12, 96, "all instructions", 11.5, cls="quiet"))
        # privileged set (traps in user mode)
        pcx = x0 + 168 if ok else x0 + 140
        prx = 146 if ok else 124
        p.append(f'<ellipse cx="{pcx}" cy="196" rx="{prx}" ry="96" class="accf"/>')
        p.append(f'<ellipse cx="{pcx}" cy="196" rx="{prx}" ry="96" fill="none" class="acc" stroke-width="1.5"/>')
        p.append(text(pcx, 124, "privileged: trap if run", 12, 600, cls="acct", anchor="middle"))
        p.append(text(pcx, 140, "outside kernel mode", 12, 600, cls="acct", anchor="middle"))
        if ok:
            p.append(f'<ellipse cx="{x0 + 168}" cy="214" rx="96" ry="52" class="c2f"/>')
            p.append(f'<ellipse cx="{x0 + 168}" cy="214" rx="96" ry="52" fill="none" class="c2s" stroke-width="1.5"/>')
            p.append(text(x0 + 168, 208, "sensitive", 12, 600, anchor="middle"))
            p.append(text(x0 + 168, 225, "(read or change machine state)", 10.5, cls="quiet", anchor="middle"))
        else:
            p.append(f'<ellipse cx="{x0 + 222}" cy="222" rx="100" ry="56" class="badf"/>')
            p.append(f'<ellipse cx="{x0 + 222}" cy="222" rx="100" ry="56" fill="none" class="bads" stroke-width="1.5"/>')
            p.append(text(x0 + 196, 210, "sensitive", 12, 600, anchor="middle"))
            p.append(text(x0 + 196, 227, "(e.g. MOV to CR3)", 10.5, cls="quiet", anchor="middle"))
            p.append(text(x0 + 291, 226, "no trap!", 10.5, 600, cls="bad", anchor="middle"))
            p.append(text(x0 + 330, 300, "sensitive, not privileged: POPF, SGDT, SMSW…", 11, 600, cls="bad", anchor="end"))
        p.append(text(x0 + 168, 336, "sensitive ⊆ privileged: trap-and-emulate works" if ok else
                      "some sensitive instructions do not trap", 12, 600,
                      cls="acct" if ok else "bad", anchor="middle"))
    p.append(text(24, 372, "Run de-privileged, a guest kernel's sensitive instructions must cause a trap, so that the VMM can emulate them.", 11.5, cls="quiet"))
    p.append(text(24, 390, "On classic x86, POPF in user mode silently ignores the interrupt flag, and SGDT/SMSW reveal real state without trapping.", 11.5, cls="quiet"))
    return svg(760, 408, title, "\n".join(p))


# ---------------- 2. Hypervisor types ----------------
def hypervisor_types():
    m = "ht"
    title = "Where the hypervisor runs: type 1, type 2, and KVM"
    p = [f"<defs>{marker(m)}</defs>", text(24, 30, title, 15, 600)]
    pw, gap = 228, 18
    heads = [("Type 1 (bare metal)", "Xen, VMware ESXi, Hyper-V"),
             ("Type 2 (hosted)", "VirtualBox, VMware Workstation"),
             ("KVM (Linux as the hypervisor)", "KVM + QEMU, Firecracker")]
    y_hw, h_hw = 318, 32
    for k, (h, ex) in enumerate(heads):
        x = 24 + k * (pw + gap)
        p.append(text(x, 62, h, 13, 600))
        p.append(text(x, 80, ex, 11, cls="quiet"))
        p += boxt(x, y_hw, pw, h_hw, ["hardware (with VT-x / AMD-V)"], "plain", 11.5)
    # type 1
    x = 24
    p += boxt(x, 272, pw, 38, ["hypervisor (VMM)", "runs in the most privileged mode"], "acc", 11.5, 600)
    vw = (pw - 12) / 3
    for i, lab in enumerate(["VM 1", "VM 2", "VM 3"]):
        vx = x + i * (vw + 6)
        p.append(rect(vx, 104, vw, 160, "plain", rx=6))
        p.append(text(vx + vw / 2, 122, lab, 11.5, 600, anchor="middle"))
        p += boxt(vx + 6, 132, vw - 12, 54, ["apps"], "tint", 11)
        p += boxt(vx + 6, 194, vw - 12, 62, ["guest", "kernel"], "c2", 11, 600)
    # type 2
    x = 24 + pw + gap
    p += boxt(x, 272, pw, 38, ["host operating system", "(Windows, macOS, Linux)"], "tint", 11.5, 600)
    p.append(rect(x, 104, 70, 160, "plain", rx=6))
    p += boxt(x + 6, 132, 58, 124, ["other", "apps"], "tint", 11)
    hx = x + 78
    p.append(rect(hx, 104, pw - 78, 160, "acc", rx=6))
    p.append(text(hx + (pw - 78) / 2, 122, "hypervisor: an application", 11, 600, cls="acct", anchor="middle"))
    vw2 = (pw - 78 - 18) / 2
    for i, lab in enumerate(["VM 1", "VM 2"]):
        vx = hx + 6 + i * (vw2 + 6)
        p += boxt(vx, 132, vw2, 58, ["apps"], "tint", 11)
        p += boxt(vx, 196, vw2, 60, ["guest", "kernel"], "c2", 11, 600)
    # KVM
    x = 24 + 2 * (pw + gap)
    p.append(rect(x, 272, pw, 38, "tint", rx=6))
    p.append(text(x + 8, 295, "Linux kernel", 11.5, 600))
    p += boxt(x + 104, 277, pw - 110, 28, ["kvm module"], "acc", 11, 600, rx=4)
    p.append(rect(x, 104, 64, 160, "plain", rx=6))
    p += boxt(x + 6, 132, 52, 124, ["other", "processes"], "tint", 10.5)
    vw3 = (pw - 64 - 18) / 2
    for i, lab in enumerate(["QEMU 1", "QEMU 2"]):
        vx = x + 70 + i * (vw3 + 6)
        p.append(rect(vx, 104, vw3, 160, "plain", rx=6))
        p.append(text(vx + vw3 / 2, 122, lab, 11, 600, anchor="middle"))
        p += boxt(vx + 6, 132, vw3 - 12, 48, ["guest", "apps"], "tint", 10.5)
        p += boxt(vx + 6, 186, vw3 - 12, 44, ["guest", "kernel"], "c2", 10.5, 600)
        p.append(text(vx + vw3 / 2, 250, "device model", 10, cls="quiet", anchor="middle"))
    p.append(text(24, 376, "Type 1: the hypervisor owns the hardware. Type 2: it is a program on an ordinary OS and uses that OS's drivers.", 11.5, cls="quiet"))
    p.append(text(24, 394, "KVM makes the Linux kernel itself the hypervisor; each VM is an ordinary process (QEMU) with one thread per virtual CPU.", 11.5, cls="quiet"))
    return svg(760, 412, title, "\n".join(p))


# ---------------- 3. VM entry and VM exit ----------------
def vm_exit():
    m, ma = "vx", "vxa"
    title = "Hardware-assisted virtualization: the guest runs directly until a VM exit"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    # two lanes
    p.append(text(24, 62, "guest: VMX non-root mode", 12.5, 600))
    p.append(text(24, 222, "hypervisor:", 12.5, 600))
    p.append(text(24, 240, "VMX root mode", 12.5, 600))
    p.append(f'<line x1="24" y1="186" x2="736" y2="186" class="grid" stroke-dasharray="4 4"/>')
    gy, hy = 74, 200
    # guest runs
    segs = [(24, 214), (420, 600)]
    for a, b in segs:
        p += boxt(a, gy, b - a, 40, ["guest code runs at full speed"], "c2", 11.5)
    p += boxt(616, gy, 120, 40, ["… until the next exit"], "c2", 11)
    # exit arrow
    p.append(path(f"M214 {gy + 40}C240 {gy + 80} 250 {hy - 30} 262 {hy - 2}", m, width=1.5))
    p.append(text(160, 142, "VM exit", 12, 600, anchor="middle"))
    p.append(text(160, 158, "guest state → VMCS", 10.5, cls="quiet", anchor="middle"))
    # handler
    p += boxt(262, hy, 150, 52, ["handle the exit", "emulate, inject, schedule"], "acc", 11.5, 600)
    p.append(path(f"M412 {hy + 10}C428 {hy - 30} 410 {gy + 80} 430 {gy + 42}", ma, cls="acc", width=1.5))
    p.append(text(470, 142, "VM entry", 12, 600, cls="acct", anchor="middle"))
    p.append(text(470, 158, "VMRESUME", 10.5, cls="quiet", anchor="middle"))
    # causes
    p.append(text(24, 288, "Typical exit reasons", 12.5, 600))
    causes = [("CPUID, HLT, MOV to CR, RDMSR/WRMSR", "instructions configured to exit"),
              ("I/O port access, MMIO", "an emulated device is touched"),
              ("EPT violation", "guest-physical page not mapped yet"),
              ("external interrupt", "the host needs the CPU back")]
    for i, (a, b) in enumerate(causes):
        y = 312 + i * 22
        p.append(text(36, y, "• " + a, 11.5, 600))
        p.append(text(330, y, b, 11.5, cls="quiet"))
    p.append(text(24, 412, "Each exit costs hundreds to thousands of CPU cycles (more under nested virtualization); hypervisors are tuned to avoid exits.", 11.5, cls="quiet"))
    return svg(760, 430, title, "\n".join(p))


# ---------------- 4. Two-dimensional address translation ----------------
def nested_paging():
    m, ma = "np", "npa"
    title = "Memory virtualization: two translations, done by software or by hardware"
    p = [f"<defs>{marker(m)}{marker(ma, 'acct')}</defs>", text(24, 30, title, 15, 600)]
    xs = [24, 290, 556]
    labels = [("guest virtual", "address (GVA)"), ("guest physical", "address (GPA)"), ("host physical", "address (HPA)")]
    y = 92
    for x, (a, b) in zip(xs, labels):
        p += boxt(x, y, 180, 50, [a, b], "tint", 12, 600)
    p.append(path(f"M204 {y + 25}H{286}", m, width=1.5))
    p.append(text(245, y - 12, "guest page table", 11.5, 600, anchor="middle"))
    p.append(text(245, y - 28, "kept by the guest OS", 10.5, cls="quiet", anchor="middle"))
    p.append(path(f"M470 {y + 25}H{552}", m, width=1.5))
    p.append(text(511, y - 12, "EPT / NPT", 11.5, 600, anchor="middle"))
    p.append(text(511, y - 28, "kept by the hypervisor", 10.5, cls="quiet", anchor="middle"))
    # shadow page table (software): a direct GVA -> HPA table
    p.append(path(f"M114 {y + 52}C114 {y + 119} 180 {y + 119} 246 {y + 119}", None, cls="acc", width=1.5, dash="6 4"))
    p.append(path(f"M514 {y + 119}C610 {y + 119} 646 {y + 110} 646 {y + 56}", ma, cls="acc", width=1.5, dash="6 4"))
    p += boxt(250, y + 98, 260, 42, ["shadow page table: GVA → HPA", "built and kept in sync by the hypervisor"], "acc", 11.5, 600)
    p.append(text(24, 272, "Software (dashed; before about 2008): the hypervisor write-protects the guest's page tables, traps each change and keeps a", 11.5))
    p.append(text(24, 290, "shadow table that the real MMU uses. TLB misses stay cheap, but every guest page-table update costs a VM exit.", 11.5, cls="quiet"))
    p.append(text(24, 320, "Hardware (AMD NPT from 2007, Intel EPT from 2008): the MMU walks both tables itself on a TLB miss and caches GVA → HPA.", 11.5))
    p.append(text(24, 338, "No exits for page-table updates, but with four levels each, one TLB miss can need up to 24 memory references instead of 4.", 11.5, cls="quiet"))
    return svg(760, 358, title, "\n".join(p))


# ---------------- 5. VM vs container stacks ----------------
def vm_vs_container():
    title = "Virtual machines virtualize the hardware; containers virtualize the operating system"
    p = [text(24, 30, title, 15, 600)]
    pw = 344
    for k, (x, head) in enumerate([(24, "Three virtual machines"), (392, "Three containers")]):
        p.append(text(x, 64, head, 13, 600))
        p += boxt(x, 330, pw, 30, ["hardware"], "plain", 12)
        cw = (pw - 2 * 10) / 3
        if k == 0:
            p += boxt(x, 290, pw, 34, ["hypervisor (VMM)"], "acc", 12, 600)
            for i in range(3):
                cx = x + i * (cw + 10)
                p.append(rect(cx, 76, cw, 208, "plain", rx=6))
                p += boxt(cx + 6, 84, cw - 12, 38, ["app"], "tint", 11.5)
                p += boxt(cx + 6, 128, cw - 12, 50, ["libraries,", "user space"], "tint", 11.5)
                p += boxt(cx + 6, 184, cw - 12, 50, ["guest", "kernel"], "c2", 11.5, 600)
                p += boxt(cx + 6, 240, cw - 12, 38, ["virtual hw"], "plain", 11)
        else:
            p.append(rect(x, 240, pw, 84, "acc", rx=6))
            p.append(text(x + pw / 2, 262, "one shared host kernel", 12, 600, cls="acct", anchor="middle"))
            p.append(text(x + pw / 2, 282, "namespaces · cgroups · capabilities · seccomp", 11, cls="quiet", anchor="middle"))
            p.append(text(x + pw / 2, 300, "OverlayFS for image layers", 11, cls="quiet", anchor="middle"))
            for i in range(3):
                cx = x + i * (cw + 10)
                p.append(f'<rect x="{cx}" y="128" width="{cw}" height="106" rx="6" fill="none" class="edge" stroke-width="1.25" stroke-dasharray="5 3"/>')
                p += boxt(cx + 6, 136, cw - 12, 38, ["app"], "tint", 11.5)
                p += boxt(cx + 6, 180, cw - 12, 48, ["libraries,", "user space"], "tint", 11.5)
            p.append(text(x + pw / 2, 110, "(processes of the host, isolated)", 11, cls="quiet", anchor="middle"))
    rows = [("isolation boundary", "hardware interface (VT-x, EPT)", "system-call interface of one kernel"),
            ("start-up, overhead", "seconds; a whole OS per VM", "milliseconds; a process per service"),
            ("may differ from host", "any OS, any kernel version", "only the user space (same kernel)")]
    y = 414
    for a, b, c in rows:
        p.append(text(24, y, a, 11.5, 600))
        p.append(text(170, y, b, 11.5, cls="quiet"))
        p.append(text(470, y, c, 11.5, cls="quiet"))
        y += 20
    p.append(f'<line x1="24" y1="398" x2="736" y2="398" class="grid"/>')
    p.append(text(170, 392, "virtual machine", 11.5, 600))
    p.append(text(470, 392, "container", 11.5, 600))
    return svg(760, y + 6, title, "\n".join(p))


# ---------------- 6. OverlayFS ----------------
def overlay():
    title = "OverlayFS: read-only lower layers, one writable upper layer, one merged view"
    p = [text(24, 30, title, 15, 600)]
    cols = ["os-release", "app.conf", "app.py", "new.txt"]
    cx = [236, 356, 476, 596]
    for x, c in zip(cx, cols):
        p.append(text(x + 56, 62, c, 12, 600, anchor="middle"))
    rows = [("merged", "what the container sees", "plain"), ("upperdir", "writable: the container's layer", "c2"),
            ("lowerdir 1", "app layer (read-only)", "acc"), ("lowerdir 2", "base layer (read-only)", "acc")]
    ys = [80, 150, 220, 290]
    for (n, d, k), y in zip(rows, ys):
        p.append(text(24, y + 22, n, 12.5, 600))
        p.append(text(24, y + 40, d, 11, cls="quiet"))
    cells = {
        (3, 0): ("base v1", "acc"), (3, 1): ("config, base", "acc"),
        (2, 2): ("print('hi')", "acc"),
        (1, 0): ("whiteout (c 0,0)", "bad"), (1, 1): ("copied up + edited", "c2"), (1, 3): ("scratch", "c2"),
        (0, 1): ("from upper", "tint"), (0, 2): ("from lower 1", "tint"), (0, 3): ("from upper", "tint"),
    }
    for (r, c), (s, k) in cells.items():
        p += boxt(cx[c], ys[r] + 6, 112, 40, [s], k, 11)
    p += boxt(cx[0], ys[0] + 6, 112, 40, ["(hidden)"], "plain", 11, cls="quiet")
    p.append(text(24, 372, "A file is looked up from the top down; the first layer that has it wins. Changing a lower file first copies it up;", 11.5, cls="quiet"))
    p.append(text(24, 390, "deleting one leaves a whiteout in the upper layer. The lower layers never change, so many containers can share them.", 11.5, cls="quiet"))
    return svg(760, 408, title, "\n".join(p))


if __name__ == "__main__":
    for name, f in [("sensitive-instructions", sensitive), ("hypervisor-types", hypervisor_types),
                    ("vm-exit", vm_exit), ("nested-paging", nested_paging),
                    ("vm-vs-container", vm_vs_container), ("overlayfs", overlay),
                    ("container-images", containers), ("image-container-volume", image_container)]:
        open(f"{name}.svg", "w", encoding="utf-8").write(f())
    print("ok")
