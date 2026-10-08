# Operating System Security: Attacks and Defences

*Operating Systems lecture: threat models, attack surfaces and the trusted computing base; memory-safety bugs (stack and heap overflows, use after free, integer overflows, format strings) and the defences against them (stack canaries, NX, ASLR and PIE, RELRO, FORTIFY_SOURCE, control-flow integrity, sanitizers, memory-safe languages, kernel hardening, seccomp); cache side channels, Meltdown and Spectre and their mitigations; the boot chain with Secure Boot, measured boot and the TPM; trusted execution environments and confidential VMs; CVEs, CVSS and patching, with the defences measured on Linux*

## Learning objectives

[Lecture 11](../11-access-control/) built the rules: who may do what with which object, enforced by a reference monitor in the kernel. Rules help only if the machinery that enforces them works. This lecture is about the attacks that go *around* the rules instead of through them: a bug that lets an attacker's data become a program's control flow, or a boot process that starts a manipulated kernel before any rule exists. For each class of attack it explains the idea, and then the defences that the hardware, the compiler and the operating system put in its way, measured on the lecture's Linux machine. It builds on the kernel/user boundary of [lecture 5](../05-interrupts/#user-mode-and-kernel-mode), the NX bit of [lecture 4](../04-fetch-execute-cycle/#memory-permissions-in-a-real-process) and the address spaces and page tables of [lecture 9](../09-virtual-memory/). The lecture describes attacks only at the level needed to understand the defences; it contains no working exploits.

By the end, students will be able to:

- describe a threat model: the attacker's goals (confidentiality, integrity, availability), the attack surface, the trusted computing base, privilege escalation and defence in depth;
- explain stack and heap buffer overflows, use after free, double free, integer overflows and format-string bugs, why C and C++ are prone to them, and how large their share of vulnerabilities is;
- explain how stack canaries, NX/W^X, ASLR with PIE, RELRO, FORTIFY_SOURCE and hardware control-flow integrity (Intel CET, Arm PAC and BTI) each break a step of an attack, and what each one does not stop;
- describe how sanitizers, fuzzing and memory-safe languages remove bugs before they ship, and how the kernel protects itself (KASLR, SMEP/SMAP, lockdown) and lets programs give up rights (seccomp);
- explain how cache timing side channels and transient execution (Meltdown, Spectre) leak data across protection boundaries, and how KPTI, retpolines, predictor controls and microcode updates mitigate them;
- trace the boot chain from the firmware to `init`, and distinguish Secure Boot, measured boot with TPM PCRs, remote attestation and TPM-bound disk encryption;
- compare trusted execution environments: Arm TrustZone, Intel SGX, AMD SEV-SNP and Intel TDX confidential VMs, Apple's Secure Enclave;
- explain CVE identifiers, CVSS scores, coordinated disclosure and patch cadence;
- inspect all of this on Linux with `/proc/PID/maps`, `setarch -R`, `gcc` hardening flags, `readelf`, `gdb`, AddressSanitizer, seccomp, `/proc/kallsyms`, `/sys/kernel/security/lockdown`, `/sys/devices/system/cpu/vulnerabilities` and the kernel log.

<details>
<summary><b>Explained simply:</b> security, attacker, vulnerability, exploit, threat model, mitigation</summary>

- **Security:** keeping a system doing what its owner wants, even when someone is actively trying to make it do something else.
- **Attacker:** the person (or program) trying to break in, read secrets or cause damage.
- **Vulnerability:** a weakness, usually a bug, that an attacker can use. A window that does not lock properly.
- **Exploit:** the method or program that uses a vulnerability. The trick of lifting that window from outside.
- **Threat model:** a clear statement of who might attack, what they can do and what they want, so that you know what you are defending against. You lock a bicycle differently from a bank vault.
- **Mitigation:** a defence that does not remove the bug, but makes it much harder or impossible to use.

</details>

## Threat models and attack surfaces

### What attackers want

Security goals are usually stated as three properties, the **CIA triad**:

- **Confidentiality:** information is read only by those allowed to read it. Breaking it means reading another user's files, a server's private key or a password in another process's memory.
- **Integrity:** information and programs are changed only by those allowed to change them. Breaking it means altering data, installing a backdoor or replacing the kernel.
- **Availability:** the system serves its legitimate users. Breaking it means crashing it or exhausting a resource (a denial-of-service attack). [Lecture 2](../02-quality-and-enterprise-linux/) measured availability; an attacker is one more cause of downtime.

A **threat model** states which attackers a system must resist and what they can do: a remote attacker who can only send network packets, a local user who can run any program, a malicious app on a phone, a cloud tenant who shares the physical machine, a thief who holds the laptop, a malicious device on the PCIe bus. A defence is only meaningful relative to a threat model: file permissions do nothing against the thief who boots the stolen disk in another computer, and full-disk encryption does nothing against a remote attacker on the running machine.

### Boundaries and the trusted computing base

![Four kinds of attackers at the top (remote, local user or app, malicious device, physical access); below them user-space processes, the system-call boundary, and the trusted computing base made of the kernel and of the firmware, boot loader, CPU and TPM; arrows show remote and local attacks entering processes and then the kernel, DMA attacks reaching the kernel, and physical attacks reaching the firmware](attack-surface.svg)

The **attack surface** is the set of all places where an attacker can supply input: for a remote attacker, every open network port and every parser behind it; for a local user, additionally every system call (Linux has more than 350), every device file, every setuid program and every file that a privileged service reads. Reducing the attack surface (closing ports, removing setuid programs, filtering system calls) is the cheapest defence, because code that cannot be reached cannot be attacked.

The most important boundary is the one between user mode and kernel mode ([lecture 5](../05-interrupts/#user-mode-and-kernel-mode)): a process can enter the kernel only through system calls, interrupts and exceptions, and the kernel checks every request at that door. Everything that enforces the security policy forms the **trusted computing base** (TCB): the kernel, the firmware and boot loader that started it, the CPU with its microcode, and the privileged services that make security decisions (`login`, `sshd`, `sudo`). A bug anywhere in the TCB can defeat every rule of [lecture 11](../11-access-control/), so the TCB should be as small as possible; Saltzer and Schroeder (1975) called this *economy of mechanism*. A monolithic kernel of tens of millions of lines is a large TCB, which is one reason why microkernels and hypervisors, with much smaller trusted cores, are attractive for high-assurance systems.

### Privilege escalation

Real attacks proceed in steps. A typical chain against a server: (1) an attacker sends a request that exploits a bug in a network service and makes it run code chosen by the attacker, with the service's user ID (*remote code execution*); (2) from there the attacker exploits a second bug, in a setuid program or in the kernel, to gain root (*local privilege escalation*); (3) the attacker makes the access permanent, for example by installing a kernel module or modifying the boot chain (*persistence*). **Privilege escalation** is the generic name for gaining rights one was not given: *vertical* escalation from an ordinary user to root or from user mode to kernel mode, *horizontal* escalation from one user's account to another's. Every step needs its own vulnerability, so every step is a place where a defence can stop the chain.

### Defence in depth

[Lecture 11](../11-access-control/#defence-in-depth) introduced **defence in depth** for access control: firewall, service configuration, DAC and MAC, one after the other. The same principle shapes this lecture. No single defence is perfect, so each step of an attack meets several independent ones: a memory bug in the service is made hard to exploit by canaries, NX, ASLR and CFI; if it is exploited anyway, the service's own user, its capabilities, its seccomp filter and its SELinux domain limit what the attacker gains; a kernel bug is made harder to exploit by kernel hardening; and a manipulated boot chain is detected by Secure Boot and measured boot. Anderson (2020) describes security engineering as exactly this: understanding the attacker's options and putting enough independent obstacles in their path that the cheapest attack costs more than it is worth.

<details>
<summary><b>Explained simply:</b> CIA triad, confidentiality, integrity, availability, denial of service, attack surface, trusted computing base, economy of mechanism, remote code execution, privilege escalation, persistence, defence in depth</summary>

- **CIA triad:** the three things security protects: **confidentiality** (secrets stay secret), **integrity** (nothing is changed without permission) and **availability** (the system keeps working for the people who need it).
- **Denial of service:** an attack that does not steal anything, but stops the system from working, like blocking a shop's door so that no customer can enter.
- **Attack surface:** all the doors, windows and letterboxes through which someone could try to get into a house. Fewer openings, fewer chances.
- **Trusted computing base (TCB):** all the parts that must work correctly for the protection to hold: the kernel, the firmware, the processor. If any of them is broken, the locks above it do not help.
- **Economy of mechanism:** keep the guard simple and small, so that you can check that it has no holes.
- **Remote code execution:** an attacker on the network makes your computer run the attacker's instructions.
- **Privilege escalation:** an attacker who got in with few rights obtains more rights, for example becomes the administrator. Climbing from the shop floor into the manager's office.
- **Persistence:** the attacker makes sure to stay in, even after a restart, like hiding a spare key.
- **Defence in depth:** several independent locks one after the other, so that breaking one is not enough.

</details>

## Memory-safety bugs

### Why C and C++

The kernel, the C library, most system services, browsers and language runtimes are written in C or C++. These languages give the programmer direct access to memory: a pointer is just an address, an array index is not checked against the array's size, memory is freed by hand, and nothing stops a program from using a pointer after the memory behind it has been freed or reused. This is what makes them fast and suitable for operating systems, and it is also why a single mistake can let input data overwrite unrelated memory. A program is **memory-safe** if every access stays within the object it was meant for (*spatial* safety) and happens only while the object exists (*temporal* safety). C and C++ guarantee neither; checking is the programmer's job (Szekeres et al., 2013).

The consequences have been measured by the largest vendors. Microsoft reported in 2019 that about 70% of the vulnerabilities to which it assigns a CVE each year are memory-safety issues (Thomas, 2019). The Chromium project found the same share, around 70%, among 912 high and critical security bugs of its browser since 2015, and half of these memory-safety bugs were use-after-free bugs (The Chromium Projects, n.d.). In Android, memory-safety bugs were 76% of the vulnerabilities in 2019 (Vander Stoep & Rebert, 2024). The first Internet worm, in 1988, already spread through a buffer overflow in the `fingerd` daemon, which read a line into a fixed-size buffer with `gets` (Spafford, 1989).

### The stack and the return address

Each function call pushes a **stack frame**: the return address (where to continue in the caller), the caller's saved frame pointer, and the function's local variables, among them arrays such as a buffer for an input line. On x86-64 the stack grows towards lower addresses, but an array is filled from its lower end upwards. So if a function copies more bytes into a local buffer than it holds, the extra bytes overwrite what lies *above* the buffer in the frame: other local variables, the saved frame pointer, and the return address.

![Two stack frames side by side. Left, compiled without a canary: a 16-byte buffer, the saved rbp, the return address and the lowest bytes of main's frame, all overwritten with 0x41 bytes; ret pops 0x4141414141414141 and the program gets SIGSEGV. Right, compiled with -fstack-protector-strong: buffer, padding, canary, saved rbp and return address; the overflow changes the canary, and the check before ret aborts the program](stack-frame.svg)

The figure shows the measured layout of the [demo program](#a-stack-overflow-detected) `overflow.c`, whose function `greet` copies its argument into `char buf[16]` with `strcpy`, which copies until the terminating zero byte and knows nothing about the size of `buf`. With a 40-byte argument the copy runs over the saved frame pointer and the return address. When `greet` executes `ret`, the processor pops the overwritten value and jumps there. Here it is `0x4141414141414141` ("AAAAAAAA"), not a valid address, so the program crashes. But the bytes come from the input: whoever controls the input chooses where the program continues. This is the **stack buffer overflow**, described for a broad audience by Aleph One (1996), and for two decades the most important way into a system.

### Heap bugs: use after free and double free

Memory from `malloc` lives on the **heap** until `free` returns it. The allocator keeps its own bookkeeping (sizes, free lists) next to or inside the blocks, and it reuses freed blocks quickly. That makes two temporal bugs dangerous:

- **Use after free (UAF):** the program keeps a pointer to a block after freeing it and uses it later. Meanwhile the allocator may have handed the same memory to another object, so the stale pointer now reads or writes someone else's data. If that object contains a function pointer (a C++ object's pointer to its virtual-function table, for example), the attacker who controls the new object's contents controls the next indirect call. The [demo](#heap-bugs-glibc-and-addresssanitizer) shows a freed block handed out again for the very next `malloc` of the same size.
- **Double free:** freeing the same block twice corrupts the allocator's free list, so that two later allocations can return the same memory.

A **heap buffer overflow** is the spatial counterpart: writing past the end of a heap block overwrites the next block or the allocator's metadata. Heap bugs are harder to exploit than the classic stack overflow, but they dominate today's statistics: Chromium's figures above count use after free as the largest single class.

### Integer overflows and format strings

Two further bug classes often lead to memory corruption:

- **Integer overflow:** fixed-width integers wrap around. A program that computes `count * size` for a `malloc` call can get a small number if the product exceeds $2^{32}$ or $2^{64}$, allocate a small block, and then copy `count` elements into it: a heap overflow caused by arithmetic. Signedness errors are similar: a negative length that passes a check `len < max` becomes a huge unsigned number in `memcpy`.
- **Format-string bug:** `printf(user_input)` instead of `printf("%s", user_input)`. The format string is interpreted, so input containing `%x` makes `printf` print values from the stack it was never given, and the conversion `%n`, which *writes* the number of characters printed so far into a pointer argument, lets input write to memory. Compilers warn about non-constant format strings (`-Wformat-security`), and FORTIFY_SOURCE rejects `%n` in writable format strings.

### From a bug to an attack

Early exploits used **code injection**: the input contained machine code, and the overwritten return address pointed into the buffer, on the stack, where that code lay. NX (below) ended this, because the stack is no longer executable. Attackers moved to **code reuse**: instead of bringing their own code, they redirect control to code that is already in the program or its libraries. The simplest form returns into a library function (*return-to-libc*); its generalisation, **return-oriented programming** (ROP), chains many short instruction sequences that each end in `ret`, found in the existing code, so that the sequence of overwritten return addresses on the stack becomes a program in its own right. Shacham (2007) showed that the C library alone contains enough such sequences for arbitrary computation. Code reuse needs no executable data, but it does need to know *where* the code is, and it needs to corrupt return addresses or function pointers. These two needs are exactly what ASLR and control-flow integrity attack.

<details>
<summary><b>Explained simply:</b> memory safety, spatial and temporal safety, pointer, stack frame, return address, frame pointer, strcpy, buffer overflow, heap, malloc and free, use after free, double free, integer overflow, format string, code injection, code reuse, return-to-libc, ROP</summary>

- **Memory safety:** a guarantee that a program only touches memory that belongs to what it is working on (**spatial**: not past the end of an array) and only while it still exists (**temporal**: not after it was given back).
- **Pointer:** a variable that holds a memory address, like a slip of paper with a house number on it.
- **Stack frame:** the area a function gets on the stack when it is called, holding its local variables and the information needed to go back to its caller.
- **Return address:** the place in the calling function where the program continues when the called function finishes. **Frame pointer** (`rbp`): a register that marks where the current function's frame is.
- **strcpy:** a C function that copies a text until its end mark (a zero byte), without asking how much room there is at the destination.
- **Buffer overflow:** writing more into a storage area than it holds, so that the rest spills over into the neighbouring memory, like pouring a litre into a half-litre glass.
- **Heap; malloc and free:** the heap is the memory a program asks for while running; `malloc` borrows a piece, `free` gives it back.
- **Use after free:** using a piece of memory after giving it back, when someone else may already be using it. Like going back into a hotel room after check-out, when the next guest has moved in.
- **Double free:** giving back the same piece twice, which confuses the bookkeeping of who has what.
- **Integer overflow:** a number grows too large for its fixed number of digits and wraps around to a small one, like a car's odometer rolling over from 999999 to 000000.
- **Format string:** the template given to `printf`, such as `"%d apples"`. If a user's text is used as the template, its `%` codes are obeyed.
- **Code injection:** smuggling new instructions into a program as data and making it run them.
- **Code reuse, return-to-libc, ROP:** instead of bringing new instructions, the attacker strings together pieces of instructions the program already contains, like writing a ransom note from letters cut out of a newspaper. **ROP** (return-oriented programming) is the general form of this; **return-to-libc** is the simplest case, jumping to one existing library function.

</details>

## Defences against memory corruption

Every defence below breaks one step of the attack chain: overwriting the return address, executing data, knowing addresses, or redirecting control. None of them removes the bug; together they make exploitation hard and expensive. Szekeres et al. (2013) organise them along the same chain.

### Stack canaries

A **stack canary** (named after the birds that warned miners of gas) is a random value that the compiler's prologue puts between the local variables and the saved registers of a frame, and that the epilogue checks before `ret`. A linear overflow from a buffer towards the return address must overwrite the canary first; if the value has changed, the program calls `__stack_chk_fail`, which prints `*** stack smashing detected ***` and aborts, before the corrupted return address is ever used. The idea was introduced by StackGuard (Cowan et al., 1998). GCC's `-fstack-protector` protects functions with character arrays, `-fstack-protector-strong` (the default on Ubuntu and Fedora) every function with any local array or address-taken variable, `-fstack-protector-all` every function. On x86-64 Linux the canary is chosen at process start and stored in thread-local storage (`%fs:0x28`); its lowest byte is always zero, so that string functions, which stop at a zero byte, cannot copy or print it.

Canaries detect only overwrites that change the canary. They do not detect an overflow that stays below it (overwriting other local variables, or padding, as the [demo](#a-stack-overflow-detected) shows), an overflow on the heap, or a write that jumps over the canary through a corrupted index or pointer. And an attacker who can read the canary, for example through a format-string bug, can write it back unchanged.

### Non-executable memory: NX and W^X

[Lecture 4](../04-fetch-execute-cycle/#memory-permissions-in-a-real-process) introduced the **NX** bit (Intel calls it XD, Arm XN): a page-table bit that forbids fetching instructions from a page, and the policy **W^X**, which makes every page either writable or executable, never both. The stack, the heap and data are writable, so they are not executable, and injected code cannot run. AMD added the bit to x86 with AMD64 in 2003, and operating systems adopted it around 2004 (Windows calls it DEP). A program asks for a non-executable stack with the `GNU_STACK` program header (`RW`, not `RWE`), which the [demo](#which-protections-does-a-program-have) inspects. NX ended code injection, and it is why attackers turned to code reuse. Programs that generate code at run time, such as JIT compilers, must switch pages between writable and executable explicitly (`mprotect`), which the kernel and SELinux can restrict further.

### ASLR and position-independent executables

Code reuse needs addresses: the address of a library function, of useful instruction sequences, of the buffer. **Address space layout randomisation** (ASLR), introduced by the PaX project for Linux in 2001 and in mainline Linux since 2005, places the stack, the heap, the shared libraries and memory mappings at random addresses at every program start ([lecture 9](../09-virtual-memory/#the-address-space-of-a-process) showed the effect). The program's own code moves only if it is a **position-independent executable** (PIE), compiled to run at any address; a classic non-PIE executable is always loaded at the fixed address 0x400000, which gives attackers a known block of code. Modern distributions build all programs as PIE.

The strength of ASLR is its **entropy**, the number of random bits in an address. With $n$ bits an attacker who must guess blindly succeeds with probability $2^{-n}$ per attempt. If the target is re-randomised after every failed attempt (a crashed program is restarted with a new layout), this takes $2^n$ attempts on average; if the layout stays the same (a forking server whose children inherit it), each wrong guess can be crossed off, and about $2^{n-1}$ attempts are needed on average. The [demo](#where-everything-lands-aslr-measured) measured 28 bits for the program, the heap and anonymous mappings, 30 bits for the stack, and 19 bits for the C library, whose start is aligned to 2 MiB so that it can be backed by huge pages. Two limits matter more than the number of bits. First, only the *base* of each region is random; the offsets inside it are fixed, so a single leaked pointer into a library reveals the whole library. Second, a server that forks children without re-executing gives every child the parent's layout, so a crash-and-retry attack can probe it. ASLR therefore forces attackers to find an information leak first, which turns one bug into a two-bug attack.

### RELRO and FORTIFY_SOURCE

A dynamically linked program calls library functions through the **global offset table** (GOT), a table of function pointers that the dynamic linker fills in. A writable table of function pointers at a known offset from the code is an ideal target: overwrite the entry for `printf`, and the next call to `printf` goes where the attacker wants. **RELRO** (relocation read-only) makes the dynamic linker mark these tables read-only once it has filled them: *partial* RELRO protects only some sections, *full* RELRO (linking with `-z relro -z now`, `BIND_NOW`) resolves all functions at start-up and then makes the whole GOT read-only.

**FORTIFY_SOURCE** (`-D_FORTIFY_SOURCE=1`, `2` or `3`, with optimisation) replaces calls such as `strcpy`, `memcpy`, `sprintf` and `read` with checking variants (`__strcpy_chk`) whenever the compiler knows the size of the destination. The check happens *before* the copy, so the overflow never takes place: the program aborts with `*** buffer overflow detected ***`. Level 3, the default of Ubuntu 24.04's GCC, also uses sizes that are known only at run time. It catches only cases where the size is known; a copy into memory reached through a pointer of unknown provenance is not checked.

### Control-flow integrity

**Control-flow integrity** (CFI) attacks the last step: whatever an attacker has corrupted, the program may only transfer control along the edges of its legitimate control-flow graph (Abadi et al., 2005). Compilers implement software CFI by checking the target of every indirect call against the set of functions with a matching type (Clang's `-fsanitize=cfi`, Microsoft's Control Flow Guard). Processors now provide it in hardware, for the two kinds of edges:

![Left: the shadow stack. CALL writes the return address both to the ordinary stack and to a protected shadow stack; RET compares them and raises a control-protection fault if they differ. Right: indirect branch tracking. An indirect call may only land on an endbr64 instruction; landing in the middle of a function raises a fault](cfi.svg)

- **Backward edges (returns).** Intel's Control-flow Enforcement Technology (CET, in processors since 2020) adds a **shadow stack**: `CALL` pushes the return address both on the ordinary stack and on a second stack in pages that ordinary store instructions cannot write, and `RET` compares the two copies. An overwritten return address no longer matches, and the processor raises a control-protection fault (Shanbhogue et al., 2019). Arm's **pointer authentication** (PAC, Armv8.3) instead signs the return address with a secret key and the stack pointer, storing the signature in the unused upper bits of the pointer; an `AUT` instruction verifies it before the return, and a forged address fails the check.
- **Forward edges (indirect calls and jumps).** Intel's **indirect branch tracking** (IBT) requires every indirect call or jump to land on an `endbr64` instruction, which the compiler puts at the start of every function whose address can be taken; Arm's **branch target identification** (BTI, Armv8.5) does the same with `BTI` landing pads. ROP and its relatives depend on jumping into the middle of existing code, which these checks forbid.

Hardware CFI needs every layer: the compiler must emit it (`-fcf-protection` on x86, `-mbranch-protection` on Arm; Ubuntu's GCC does so by default, as the [demo](#which-protections-does-a-program-have) shows), every library loaded into the process must be marked compatible, and the kernel must enable it: Linux supports IBT for the kernel itself since 5.18 and user-space shadow stacks since 6.6. Apple has used PAC in its own processors since the A12 chip of 2018.

### Finding bugs first: sanitizers and fuzzing

The mitigations above make bugs harder to exploit at run time; the better place to catch a bug is before it ships. **AddressSanitizer** (ASan, `-fsanitize=address`) instruments every memory access of a program and surrounds every object with poisoned *red zones*; a shadow memory, one byte per 8 bytes of application memory, records which bytes may be accessed. Freed memory is poisoned and kept in quarantine for a while, so use after free is detected, too. ASan reports the exact access, with the stacks of the allocation and of the free, at a cost of about 73% slowdown on average (Serebryany et al., 2012), which is fine for testing but not for production. Related sanitizers find uninitialised reads (MSan), undefined behaviour such as signed overflow (UBSan) and data races (TSan); the kernel has its own (KASAN, KCSAN). **Fuzzing** feeds a program millions of automatically mutated inputs and watches for crashes; combined with sanitizers, which turn silent corruption into crashes, it finds memory bugs at scale. Google's syzkaller fuzzes the Linux kernel's system calls continuously and has found thousands of kernel bugs.

### Memory-safe languages

The structural answer is to write new code in a language that is memory-safe by construction: bounds-checked arrays, no manual `free`, no dangling pointers. Garbage-collected languages (Java, Go, C#) achieve this at the cost of a runtime; **Rust** achieves it at compile time through its ownership and borrowing rules, with performance comparable to C, which makes it usable for system software. Android's experience shows the effect: as new code was written mostly in Rust and Kotlin, the share of memory-safety bugs among Android's vulnerabilities fell from 76% in 2019 to 24% in 2024, although most of the existing C and C++ code remained, because vulnerabilities are concentrated in new code (Vander Stoep & Rebert, 2024). Linux accepts drivers written in Rust since version 6.1 ([lecture 14](../14-mobile-wearable-embedded/#rust-in-kernels)). Rust code that must do unchecked things marks them `unsafe`, which confines the remaining risk to small, reviewable places.

### Hardening the kernel itself

A kernel bug is the most valuable target: it gives full control of the machine, past every access-control rule. The kernel therefore applies the same ideas to itself, plus a few that only hardware can give:

- **KASLR** (kernel ASLR, Linux 3.14, on by default since 4.12) loads the kernel image at a random address at each boot, and randomises the base of its direct mapping of physical memory (`CONFIG_RANDOMIZE_MEMORY`). To keep the addresses secret, the kernel hides them: `/proc/kallsyms` shows zeros to processes without `CAP_SYSLOG`, controlled by `kernel.kptr_restrict`, and `kernel.dmesg_restrict` keeps the kernel log, which often contains addresses, from ordinary users ([demo](#the-kernel-hides-its-addresses)).
- **SMEP and SMAP** (supervisor mode execution and access prevention, Intel 2012 and 2014; Arm calls them PXN and PAN) stop the kernel from executing user-space pages and from reading or writing user-space memory except inside the explicit copy routines (`copy_from_user`, which temporarily lifts SMAP). Without SMEP, a kernel bug that corrupted a function pointer could simply point it to code the attacker had placed in user memory.
- **W^X for the kernel** (`CONFIG_STRICT_KERNEL_RWX`): the kernel's code is read-only and its data non-executable, and read-only data are write-protected after boot ("Write protecting the kernel read-only data" in the [boot log](#how-did-this-machine-boot)). The kernel is compiled with its own stack protector, FORTIFY_SOURCE and, where enabled, IBT; *hardened usercopy* checks the size of every copy between user and kernel memory against the kernel object involved.
- **Lockdown** (Linux 5.4) protects the running kernel from root. In `integrity` mode it refuses everything that would let root modify the kernel: unsigned modules, `kexec` of an unsigned kernel, writes to `/dev/mem` and to model-specific registers, direct I/O port access, and debugfs files; `confidentiality` mode also blocks reading kernel memory (`/proc/kcore`, kprobes, BPF reads). Lockdown can only be raised, never lowered, until the next boot (Linux man-pages project, n.d.). It closes the gap between "root" and "kernel" that Secure Boot needs (below): without it, root could load any code into a kernel that was verified at boot.

### Sandboxing: giving up rights

Least privilege ([lecture 11](../11-access-control/#the-reference-monitor)) applies to system calls, too. A process that parses untrusted input, such as a browser's renderer, a PDF viewer or a media decoder, needs only a few system calls; every other call is attack surface on the kernel. **Seccomp** lets a process restrict itself irrevocably. In *strict* mode (Linux 2.6.12) only `read`, `write`, `_exit` and `sigreturn` remain; any other system call kills the process. In *filter* mode (seccomp-bpf, Linux 3.5) the process installs a small BPF program that the kernel runs on every system call, with the call number and the arguments as input, and that returns allow, an error code, a signal or kill (The kernel development community, n.d.-c). Filters are inherited by children and can only be made stricter. An unprivileged process must first set `no_new_privs`, which promises that it will never gain rights through `execve` of a setuid program, so that a filter cannot be used to confuse a privileged program. Chrome, Firefox, OpenSSH's pre-authentication process, systemd services (`SystemCallFilter=`), [container engines](../13-virtualization-containerization/#capabilities-seccomp-and-mandatory-access-control) and [every Android app](../14-mobile-wearable-embedded/#the-application-sandbox) use seccomp. Combined with namespaces, dropped capabilities, Landlock and a MAC domain, it builds a **sandbox**: a process that is assumed to be compromised sooner or later, and is confined so that it gains the attacker nothing.

<details>
<summary><b>Explained simply:</b> stack canary, __stack_chk_fail, NX, W^X, DEP, JIT, ASLR, PIE, entropy, information leak, GOT, RELRO, FORTIFY_SOURCE, control-flow integrity, shadow stack, CET, PAC, IBT, BTI, endbr64, sanitizer, ASan, red zone, fuzzing, Rust, unsafe, KASLR, kptr_restrict, SMEP, SMAP, lockdown, seccomp, BPF, no_new_privs, sandbox</summary>

- **Stack canary:** a secret random number placed just below the return address. If it has changed when the function ends, something has been written over it, and the program stops at once (in `__stack_chk_fail`), like a seal on a box that shows it has been opened.
- **NX, W^X, DEP:** memory is either for writing data or for running instructions, never both; DEP is Windows' name for it.
- **JIT** (just-in-time compiler): a program that turns code into machine instructions while running, such as a browser's JavaScript engine; it must switch memory from "write" to "run" on purpose.
- **ASLR:** placing the parts of a program at random addresses at every start, so that an attacker does not know where anything is. Like moving the furniture every night so that a burglar cannot find his way in the dark.
- **PIE** (position-independent executable): a program built so that it can run at any address, so that ASLR can move it too.
- **Entropy:** how many random bits there are: with 28 bits there are about 268 million possible positions.
- **Information leak:** a bug that lets the attacker read something, such as an address, that should stay hidden.
- **GOT** (global offset table): a program's list of addresses of the library functions it calls. **RELRO:** making that list read-only after start-up, so it cannot be redirected.
- **FORTIFY_SOURCE:** the compiler swaps risky copy functions for versions that check the size of the destination first.
- **Control-flow integrity:** the program may only jump to places where it is meant to jump.
- **Shadow stack, CET, PAC:** a second, protected copy of the return addresses (Intel's CET), or a cryptographic signature on each return address (Arm's PAC), so that a changed return address is noticed.
- **IBT, BTI, endbr64:** jumps through pointers may only land on special marker instructions (`endbr64` on Intel, `BTI` on Arm), which the compiler puts at the legal entry points.
- **Sanitizer, ASan, red zone:** a testing tool that checks every memory access while the program runs. ASan puts forbidden **red zones** around every piece of memory and reports any touch.
- **Fuzzing:** throwing millions of random, slightly broken inputs at a program to see what makes it crash.
- **Rust, unsafe:** a programming language whose compiler refuses programs that could use memory wrongly; the few places that need to break the rules must be marked `unsafe`.
- **KASLR:** ASLR for the kernel itself. **kptr_restrict:** the setting that hides the kernel's addresses from ordinary users.
- **SMEP, SMAP:** processor features that stop the kernel from running, or touching, the memory of ordinary programs by accident or by trickery.
- **Lockdown:** a mode in which even the administrator cannot change the running kernel.
- **Seccomp, BPF:** a process tells the kernel "from now on, refuse these system calls to me"; the rules are written as a tiny **BPF** program that the kernel runs at every call.
- **no_new_privs:** a promise of a process that it, and its children, will never gain more rights, not even by starting a setuid program.
- **Sandbox:** a closed play area for a program that you do not fully trust.

</details>

## Side channels and transient execution

Every defence so far assumes that the hardware does exactly what the instruction set promises: a page marked as kernel-only cannot be read from user mode, and a bounds check that fails stops the access. In January 2018 two classes of hardware flaws, **Meltdown** and **Spectre**, showed that this assumption is too strong. They do not break any rule of the architecture; they read secrets through a **side channel**, a physical effect of computation that the architecture never meant to carry information.

### Leaking through timing

The best-known side channel is the cache of [lecture 8](../08-two-level-memory-and-cache/). Whether a memory line is in the cache is invisible to the program's logic, but it changes how long an access takes: a hit costs a few nanoseconds, a miss to RAM around a hundred. If two programs share a cache and some memory, one of them can learn which lines the other has touched by timing its own accesses to the same lines. In the FLUSH+RELOAD technique the attacker evicts a line of a shared library from all caches with the `clflush` instruction, waits, and then times one read of it: a fast read means that the victim used the line in between. Because the last-level cache is shared by all cores, this works even between processes on different cores (Yarom & Falkner, 2014). This alone leaks only *access patterns*, but access patterns can depend on secrets: which table entry a cryptographic routine looked up, which branch it took.

### Meltdown and Spectre

Modern processors execute instructions **speculatively** and **out of order**: they guess the outcome of branches and run ahead before earlier instructions have finished, and if a guess was wrong or an earlier instruction faults, they throw the results away. Architecturally these **transient** instructions never happened, since no register or memory value they produced survives. Their effect on the cache, however, does survive.

- **Meltdown** (Lipp et al., 2018) affected processors that, during transient execution, let a user-mode load read kernel memory before the permission check of the page table entry took effect. The fault arrived and the result was discarded, but the value had already influenced which cache line was loaded, and a timing measurement could recover it. Because Linux mapped the whole kernel into every process's address space (to make system calls cheap), and the kernel's address space includes a direct mapping of all physical memory, every user process could in principle read all of the machine's memory, including other processes' data.
- **Spectre** (Kocher et al., 2019) uses branch prediction. The attacker trains the predictor so that the *victim's own code* transiently runs down a path it would never take architecturally, for example past a bounds check, and touches memory depending on a secret. Spectre does not need a broken permission check, so it works across processes, against the kernel and inside sandboxes such as a browser's JavaScript engine, and it cannot be fixed by one change.

Later research found a long family of related flaws (Foreshadow/L1TF, MDS, Retbleed, Downfall and others), each leaking through a different internal structure of the processor: the L1 data cache, the fill and store buffers, the return-address predictor, the vector registers.

### Mitigations and their cost

Because the root cause is in silicon, the operating system works around it in cooperation with microcode updates and the compiler:

- **Kernel page-table isolation (KPTI).** Following the KAISER design (Gruss et al., 2017), the kernel keeps two sets of page tables per process: in user mode almost none of the kernel is mapped, so there is nothing for Meltdown to read. Every system call and interrupt now switches page tables, which costs time; the PCID tags of [lecture 9](../09-virtual-memory/#the-tlb-a-cache-for-translations) keep the TLB from being flushed at each switch and make the cost bearable. AMD's processors were never affected by Meltdown, and Intel fixed it in hardware in the generations released from late 2018 on; on these KPTI is switched off.
- **Against Spectre:** barriers and pointer masking at the kernel's bounds checks on user-supplied indices; **retpolines** (compiler-generated indirect jumps that the predictor cannot be trained on) or hardware controls such as enhanced IBRS for indirect branches; flushing the branch predictor state (IBPB) when switching to a different process or VM; and **process isolation** in browsers, which put each web site in its own process.
- **Avoiding sharing** where nothing else helps: two hyperthreads of one core (simultaneous multithreading, SMT) share almost all of the core's internal buffers, so the large cloud providers do not put two different customers' virtual CPUs on the same core, Linux can switch SMT off (`nosmt`) or let only mutually trusting tasks share a core (*core scheduling*), and OpenBSD disables SMT by default.

The kernel reports, for every flaw it knows, whether this CPU is affected and which mitigation is active, in `/sys/devices/system/cpu/vulnerabilities/` (The kernel development community, n.d.-b). The cost of the mitigations varies from a few percent to tens of percent for system-call-heavy workloads, which is why they can be switched off (`mitigations=off`) on machines that run only trusted code.

<details>
<summary><b>Explained simply:</b> side channel, cache timing, FLUSH+RELOAD, clflush, speculative execution, out-of-order execution, branch prediction, transient execution, direct mapping, Meltdown, Spectre, KPTI, KAISER, PCID, retpoline, IBRS, IBPB, microcode, SMT, hyperthread, core scheduling</summary>

- **Side channel:** learning a secret not by reading it, but from a side effect: how long something took, how much power it used. Like guessing which keys of a keypad are used from the worn-off paint.
- **Cache timing:** measuring whether a piece of memory was fast (it was in the cache, so someone used it recently) or slow to read.
- **FLUSH+RELOAD, clflush:** the attacker throws a shared piece of memory out of the cache (with the `clflush` instruction), waits, and reads it again. If the read is fast, the victim must have used it in the meantime.
- **Speculative execution:** the processor guesses what comes next and starts working on it early, to save time. If the guess was wrong, it throws the work away.
- **Out-of-order execution:** the processor does not wait for a slow instruction, but already runs later instructions that do not depend on it, and puts the results in the right order at the end.
- **Branch prediction:** the part of the processor that guesses which way an `if` will go, based on what happened the previous times.
- **Transient execution:** the thrown-away work. Officially it never happened, but it can leave traces in the cache.
- **Meltdown, Spectre:** two families of processor flaws found in 2018. Meltdown let ordinary programs read kernel memory through such traces; Spectre tricks a program into speculatively touching its own secrets.
- **Direct mapping:** a part of the kernel's address space through which the kernel can reach every byte of the computer's RAM.
- **KPTI** (kernel page-table isolation), **KAISER:** while an ordinary program runs, the kernel's memory is simply left out of its page tables, so there is nothing to read. KAISER is the research design that KPTI was built on.
- **PCID:** a label on each TLB entry saying which address space it belongs to, so that switching page tables does not have to throw all entries away.
- **Retpoline:** a compiler trick that turns risky indirect jumps into a form the processor's guessing machinery cannot be misled on.
- **IBRS, IBPB:** processor controls that limit or reset the branch predictor's memory, so one program cannot train it to mislead another.
- **Microcode:** the processor's internal firmware, which can be updated to change how some instructions behave.
- **SMT, hyperthread, core scheduling:** with SMT (Intel calls it Hyper-Threading) one processor core runs two programs at once as two **hyperthreads**, sharing most of its parts. **Core scheduling** lets only programs that trust each other share a core.

</details>

## The boot process and the chain of trust

Every defence so far is enforced by the kernel. An attacker who can change the kernel, or the code that loads it, before it starts has defeated them all, and such a modification (a *bootkit*) survives reinstalling every program. The boot process must therefore establish trust step by step, starting from something the attacker cannot change.

### From power-on to init

On a PC, power-on starts the **firmware** from flash memory on the mainboard: historically the BIOS, today **UEFI**. It initialises the processor, memory and devices, and then loads a boot loader from the EFI system partition, a small FAT file system on the disk. On Linux the first stage is usually **shim**, a tiny loader signed by Microsoft (see below), which loads **GRUB** or **systemd-boot**. The boot loader reads its configuration, loads the **kernel** and the **initramfs** (a small compressed file system with the drivers and tools needed to find and unlock the real root file system) and jumps into the kernel. The kernel initialises itself, unpacks the initramfs, runs its `init`, which mounts the real root file system, and finally hands over to the real **init**, usually systemd, process 1, which starts all services. Each stage runs code that the previous stage loaded from disk, so the integrity of each stage depends on the one before it: a **chain of trust**. The anchor at its start, which must be trusted without being checked, is the **root of trust**: on a PC the firmware in flash, ideally itself verified by a boot ROM in the CPU or chipset (Intel Boot Guard, AMD Platform Secure Boot).

### Secure Boot: verify before running

**UEFI Secure Boot** (UEFI 2.3.1, 2011) makes each stage check a digital signature on the next one before running it (UEFI Forum, 2024). The firmware holds a database of trusted certificates (`db`), a database of revoked signatures and hashes (`dbx`), and the keys that may change them (the platform key PK and key-exchange keys KEK). It runs a boot loader only if the loader is signed by a certificate in `db` and not revoked in `dbx`. Practically all PCs ship with Microsoft's certificates in `db`, so Linux distributions have their first-stage loader, shim, signed by Microsoft; shim contains the distribution's own certificate and checks GRUB and the kernel against it. A user who builds a kernel can enrol a key of their own as a **Machine Owner Key** (MOK) with `mokutil`. A kernel booted this way continues the chain: it accepts only signed modules and, through lockdown, refuses to let even root load unsigned code into it; several distributions switch lockdown on automatically when the machine was booted with Secure Boot.

Secure Boot is *enforcement*: an unsigned or revoked component does not run. Its weakness is that it trusts everything properly signed: a signed but vulnerable boot loader remains a door until its hash is added to `dbx`, which is why revocation updates are a regular part of firmware maintenance.

### Measured boot and the TPM

**Measured boot** does not stop anything; it *records*. Before each stage runs the next, it computes a cryptographic hash of it and sends the hash to the **Trusted Platform Module** (TPM), a small security chip (or a protected function of the processor's firmware) with its own keys and a set of **platform configuration registers** (PCRs). A PCR cannot be written, only **extended**:

$$\mathrm{PCR}_{\mathrm{new}} = \mathrm{SHA256}(\mathrm{PCR}_{\mathrm{old}} \mathbin{\Vert} h)$$

where $h$ is the hash of the new component and $\Vert$ is concatenation. The PCRs start at zero at reset, and because the hash function cannot be reversed, the final value of a PCR depends on every component measured into it and on their order: no later software can bring a PCR to a chosen value (Trusted Computing Group, n.d.). An *event log* in memory lists every measurement, so that a verifier can recompute the PCRs and see what each one contains. Which component is measured into which PCR is fixed by convention: the TCG PC Client profile defines PCRs 0–7 for the firmware, option ROMs, the boot loader and the Secure Boot state (Trusted Computing Group, 2023), and the Linux TPM PCR registry assigns the higher ones to GRUB, the kernel command line and systemd's components (UAPI Group, n.d.).

![Five stages in a row: UEFI firmware, shim, GRUB or systemd-boot, kernel and initramfs, init. Above, Secure Boot verifies each next stage's signature. Below, each stage is measured into TPM PCRs (0 and 2, 4 and 7, 4 and 8, 9 or 11); the TPM extends PCRs and its values are used for sealing a disk key and for remote attestation](boot-chain.svg)

Measurements are useful in two ways:

- **Sealing.** The TPM can encrypt a secret so that it will decrypt it again only if selected PCRs have the same values as when the secret was sealed. **TPM-bound disk encryption** uses this: BitLocker on Windows, and on Linux `systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7` for a LUKS volume, store the disk key sealed to the PCRs. On an unmodified machine the disk unlocks without a password; if someone boots a different loader or kernel, or takes the disk to another machine, the PCRs differ and the TPM refuses. A PIN can be added, so that a stolen machine that boots normally is still not enough.
- **Remote attestation.** The TPM signs the current PCR values together with a fresh random number from the verifier (a *quote*) with a key that never leaves the TPM and is certified by its manufacturer. A remote verifier checks the signature and replays the event log against a list of known-good measurements, and only then grants access, for example to a corporate network or to the secrets of a cloud workload.

Secure Boot and measured boot complement each other: one prevents unknown code from running, the other lets the machine prove afterwards exactly what ran. Phones use the same ideas in a stricter form, with the root of trust in the chip's boot ROM and the system partitions verified block by block; see [verified boot in lecture 14](../14-mobile-wearable-embedded/#verified-boot).

<details>
<summary><b>Explained simply:</b> bootkit, firmware, BIOS, UEFI, EFI system partition, shim, GRUB, systemd-boot, initramfs, chain of trust, root of trust, digital signature, Secure Boot, db, dbx, MOK, measured boot, hash, TPM, PCR, extend, event log, sealing, LUKS, remote attestation, quote</summary>

- **Bootkit:** malware that hides in the start-up process, so it runs before the operating system and its defences.
- **Firmware, BIOS, UEFI:** the program stored on the mainboard that starts the computer; BIOS is the old kind, UEFI the modern one. The **EFI system partition** is a small area of the disk where UEFI looks for the next program to start.
- **shim, GRUB, systemd-boot:** small programs that load the operating system: shim is a signed first step, GRUB and systemd-boot let you choose and load the kernel.
- **initramfs:** a tiny temporary file system packed with the kernel, holding just enough to find and open the real disk.
- **Chain of trust, root of trust:** each step checks the next, like a relay where each runner checks the identity of the next runner. The first runner, who is trusted without being checked, is the root of trust.
- **Digital signature:** a mathematical seal that only the holder of a secret key can produce, but anyone can check with the matching public key.
- **Secure Boot, db, dbx, MOK:** the firmware runs only programs carrying a signature from its list of trusted signers (**db**) and not on its list of banned ones (**dbx**). A **MOK** (machine owner key) is a signer the owner of the computer added.
- **Measured boot, hash:** each step writes down a fingerprint (**hash**) of the next one before starting it. A hash is a short number calculated from a file; changing a single bit of the file gives a completely different hash.
- **TPM, PCR, extend:** the TPM is a small security chip. Its **PCRs** are registers you cannot set, only **extend**: the new value is mixed from the old value and the new fingerprint. Like a diary in ink where every new line depends on all lines before it.
- **Event log:** the list of what was measured, so that someone can check the diary line by line.
- **Sealing, LUKS:** locking a secret inside the TPM so it is given out only if the fingerprints are the same as before. LUKS is Linux's standard format for an encrypted disk.
- **Remote attestation, quote:** the TPM signs its current fingerprints (a **quote**) so that another computer can check what software this machine started.

</details>

## Trusted execution environments

Secure Boot and measured boot protect the operating system from what came before it. A **trusted execution environment** (TEE) goes further: it protects some code and data *from the operating system itself*, and sometimes from the hypervisor and the machine's owner, by enforcing the isolation in the processor. The question each design answers is who remains in the trusted computing base.

![Three columns. Arm TrustZone: normal-world apps and rich OS as ordinary, secure-world trusted apps, trusted OS and secure monitor as trusted. Intel SGX: application ordinary, enclave and CPU package trusted, operating system and hypervisor untrusted. Confidential VM: guest apps and guest kernel and CPU with its secure processor trusted, hypervisor and cloud operator untrusted](tee.svg)

- **Arm TrustZone** divides the processor into a *normal world*, where the ordinary operating system (Android, Linux) runs, and a *secure world* with its own small trusted OS (such as OP-TEE) and trusted applications. Memory and devices can be assigned to the secure world, and the normal world, even its kernel, cannot access them; a secure monitor at the highest exception level switches between the worlds (Pinto & Santos, 2019). Phones use the secure world for keys, fingerprint matching and DRM.
- **Intel SGX** (Software Guard Extensions, 2015) lets an ordinary process create an **enclave**: a region of its address space whose pages the processor encrypts in memory and refuses to let any other software, including the kernel and the hypervisor, read or write. The enclave's code is measured when it is created and can prove its identity by attestation; the OS still manages the enclave's pages, but sees only ciphertext (Costan & Devadas, 2016). The trusted computing base is very small, only the CPU and the enclave's code, but the untrusted OS controls everything around the enclave, including scheduling and page faults, which researchers used in a long series of attacks on enclaves. Intel deprecated SGX on its client processors with the 11th and 12th Core generations (Intel Corporation, n.d.); it continues on Xeon server processors.
- **Confidential virtual machines** apply the same idea to a whole VM. With **AMD SEV-SNP** (Secure Encrypted Virtualization with Secure Nested Paging, EPYC processors since 2021) and **Intel TDX** (Trust Domain Extensions, Xeon processors since 2023), the processor encrypts each VM's memory with its own key and protects its integrity, so that the hypervisor, the host OS and the cloud operator can no longer read or silently change the guest's memory or registers (Advanced Micro Devices, 2020; Intel Corporation, 2020). The hypervisor still schedules the VM and can refuse to run it, so availability is not protected. At start the processor's security firmware measures the initial guest image, and the guest can obtain a signed attestation report to prove to its owner that it runs unmodified on genuine hardware. Compared with [lecture 13's](../13-virtualization-containerization/#memory-two-translations) ordinary VMs, the trust relation is reversed: the guest no longer trusts the host.
- **Apple's Secure Enclave** is a separate processor core on the same chip, with its own boot ROM, encrypted memory and operating system; the main processor can ask it to use a key, but never obtains the key ([lecture 14](../14-mobile-wearable-embedded/#the-secure-enclave); Apple Inc., 2026).

<details>
<summary><b>Explained simply:</b> trusted execution environment, TrustZone, normal and secure world, OP-TEE, SGX, enclave, confidential VM, SEV-SNP, TDX, attestation report, Secure Enclave</summary>

- **Trusted execution environment (TEE):** a protected room inside the processor where some code runs and keeps secrets, sealed off even from the main operating system.
- **TrustZone, normal and secure world:** Arm's way of splitting one processor into two worlds; the everyday operating system lives in the normal world and cannot look into the secure one. **OP-TEE** is a small open-source operating system for the secure world.
- **SGX, enclave:** Intel's protected rooms inside an ordinary program; the memory of an **enclave** is encrypted, and even the kernel sees only scrambled bytes.
- **Confidential VM, SEV-SNP, TDX:** a whole virtual machine whose memory is encrypted by the processor, so that the cloud company that runs the hardware cannot read it. SEV-SNP is AMD's version, TDX Intel's.
- **Attestation report:** a signed certificate from the processor saying "this exact software is running inside me, and I am genuine".
- **Secure Enclave:** Apple's separate little security processor that keeps the keys and only uses them on request.

</details>

## Vulnerability management and updates

Bugs will be found in every large system; what matters is how quickly they are fixed and the fixes installed.

### CVE and CVSS

A publicly known vulnerability receives a **CVE** identifier (Common Vulnerabilities and Exposures), such as CVE-2022-0847 for the Dirty Pipe flaw of [lecture 2](../02-quality-and-enterprise-linux/#why-the-version-number-lies-backporting-in-practice), so that vendors, scanners and advisories can refer to the same problem. Identifiers are assigned by CVE Numbering Authorities (CNAs): vendors such as Red Hat or Microsoft, and since February 2024 the Linux kernel project itself, which assigns a CVE to every fix that could have security consequences and therefore publishes many hundreds per year (Jones, 2024; The kernel development community, n.d.-a). The **CVSS** (Common Vulnerability Scoring System) rates a vulnerability's severity from 0 to 10, from attributes such as the attack vector (network, adjacent, local, physical), the complexity, the privileges and user interaction required, and the impact on confidentiality, integrity and availability; version 4.0 was published in 2023 (FIRST, 2023). A base score describes the vulnerability in general; how urgent it is for a given organisation depends on whether the affected component is used and reachable there, which only an analysis of the actual systems can tell.

### Coordinated disclosure

A researcher who finds a vulnerability normally reports it privately to the vendor, and the details are published only when a fix is available or after a deadline, commonly 90 days: **coordinated disclosure**. It gives users a fix before attackers learn the details, while the deadline keeps vendors from ignoring reports. For problems that affect many vendors at once, such as flaws in widely used libraries or in processors, the coordination involves dozens of companies and a common embargo date. A vulnerability that attackers exploit before a fix exists is a **zero-day**.

### Patch cadence

Vendors publish fixes on a rhythm: Microsoft on the second Tuesday of each month (*Patch Tuesday*), Android in monthly security bulletins, Linux distributions as advisories (RHSA, USN) whenever a fix is ready, with the stable kernel series of kernel.org updated about weekly. Enterprise distributions **backport** fixes into the version they ship ([lecture 2](../02-quality-and-enterprise-linux/#why-the-version-number-lies-backporting-in-practice)), so the version number alone does not tell whether a system is fixed; their advisories do. Installing updates promptly is the single most effective security measure, and also an availability trade-off: a kernel update requires a reboot (or live patching), a library update a restart of every process that uses the library. Immutable, image-based systems and A/B updates ([lecture 2](../02-quality-and-enterprise-linux/#image-mode-the-whole-operating-system-as-an-image), [lecture 14](../14-mobile-wearable-embedded/#ab-and-virtual-ab-updates)) make updates atomic and easy to roll back, which removes much of the fear of updating.

<details>
<summary><b>Explained simply:</b> CVE, CNA, CVSS, attack vector, coordinated disclosure, embargo, zero-day, Patch Tuesday, security advisory, backport, live patching</summary>

- **CVE:** a catalogue number for a security hole, such as CVE-2022-0847, so that everyone talks about the same problem. A **CNA** is an organisation allowed to hand out these numbers.
- **CVSS, attack vector:** a score from 0 to 10 for how bad a hole is; the **attack vector** says from where it can be used: over the network, from the same network, only by someone logged in, or only by someone holding the device.
- **Coordinated disclosure, embargo:** the finder tells the maker first and keeps quiet until a fix is ready or a deadline passes; the **embargo** is the agreed day of publication.
- **Zero-day:** a hole that attackers use before the maker has a fix: the maker has had "zero days" to react.
- **Patch Tuesday:** Microsoft's monthly update day.
- **Security advisory:** a notice from a vendor saying which problem is fixed in which package version.
- **Backport:** copying a fix from a new version into an older one that is still supported.
- **Live patching:** fixing the running kernel without restarting the computer.

</details>

## The same ideas on Linux (x86-64)

The demos run as root on the Ubuntu 24.04 virtual machine of the previous lectures (Linux 6.18, gcc 13.3, glibc 2.39, GDB 15.1, Python 3.13). The lecture's folder may be mounted without execute permission, so every program was compiled and run in a copy of the folder, `/root/lab12`, which is the path that appears in some outputs. The programs only show the defences at work: each one contains a deliberate bug and is fed a harmless string of `A` characters; nothing is exploited. Every console listing is the real output; terminal sessions were recorded in an interactive shell, so the shell's own messages, such as `Segmentation fault`, appear as a user sees them.

<details>
<summary><b>Explained simply:</b> console, root, gcc, gdb, script</summary>

- **Console** (terminal): a window where you type commands. Lines starting with `$` are what you type; the other lines are the computer's answer.
- **Root:** the administrator account, needed for some of the kernel settings shown here.
- **gcc:** the C compiler; its options (such as `-fstack-protector-strong`) switch protections on or off.
- **gdb:** the debugger: it runs a program step by step and shows its memory.
- **Script** (`.sh` file): a list of commands saved in a file and run one after the other with `bash`.

</details>

### Where everything lands: ASLR measured

`aslr.c` prints the address of its `main` function, a global variable, a small `malloc` block, an anonymous `mmap` page, the C library's `puts` and a local variable. Two normal runs, two runs with ASLR switched off for one command by `setarch -R`, and two runs of the same program built without PIE:

```console
$ gcc -O2 -o aslr aslr.c
$ ./aslr
main   (code)  0x55575d88e0c0
global (data)  0x55575d891010
heap           0x5557790832a0
mmap           0x7f198f6de000
libc   (puts)  0x7f198f487cc0
stack  (local) 0x7fffcb0195e4
$ ./aslr
main   (code)  0x5621e5c530c0
global (data)  0x5621e5c56010
heap           0x5622198872a0
mmap           0x7f8be293e000
libc   (puts)  0x7f8be2687cc0
stack  (local) 0x7ffff502c054
$ setarch -R ./aslr
main   (code)  0x5555555550c0
global (data)  0x555555558010
heap           0x5555555592a0
mmap           0x7ffff7fba000
libc   (puts)  0x7ffff7c87cc0
stack  (local) 0x7fffffff8864
$ setarch -R ./aslr
main   (code)  0x5555555550c0
global (data)  0x555555558010
heap           0x5555555592a0
mmap           0x7ffff7fba000
libc   (puts)  0x7ffff7c87cc0
stack  (local) 0x7fffffff8864
$ gcc -O2 -no-pie -o aslr-nopie aslr.c
$ ./aslr-nopie
main   (code)  0x4010b0
global (data)  0x404030
heap           0x39c342a0
mmap           0x7fd246d76000
libc   (puts)  0x7fd246a87cc0
stack  (local) 0x7ffee3e41394
$ ./aslr-nopie
main   (code)  0x4010b0
global (data)  0x404030
heap           0x365422a0
mmap           0x7f87d810e000
libc   (puts)  0x7f87d7e87cc0
stack  (local) 0x7fff912d8a34
```

Every region moves between the two normal runs, but the last three hex digits of each address stay the same (`0c0`, `010`, `2a0`, `cc0`): only the base of a region is random, at page granularity, and the offset of `puts` inside the C library is fixed. With `setarch -R` the program sees the same layout every time, the one a debugger shows by default (`0x555555554000` for the program). The non-PIE build loads its code and data at the fixed addresses 0x401000 and 0x404000 in every run; only the regions the kernel and the dynamic linker place (heap, mappings, libraries, stack) still move.

The system-wide switch is `kernel.randomize_va_space`: 2 randomises everything, 1 everything except the heap's start (`brk`), 0 nothing. With 1 the heap follows directly after the program's data, at a fixed distance from `main`:

```console
$ sysctl kernel.randomize_va_space vm.mmap_rnd_bits
kernel.randomize_va_space = 2
vm.mmap_rnd_bits = 28
$ sysctl -w kernel.randomize_va_space=1
kernel.randomize_va_space = 1
$ ./aslr | grep -E "main|heap"
main   (code)  0x55ac83a3c0c0
heap           0x55ac83a402a0
$ ./aslr | grep -E "main|heap"
main   (code)  0x5571770820c0
heap           0x5571770862a0
$ sysctl -w kernel.randomize_va_space=2
kernel.randomize_va_space = 2
```

How random are the addresses? `aslr_entropy.py` runs the program 2000 times and estimates, for each region, the number of random bits from the range of addresses seen and their alignment:

```console
$ python3 aslr_entropy.py ./aslr 2000
region          distinct  alignment  entropy   lowest .. highest
main   (code)       2000     0x1000  28.0 bits   0x55556cab50c0 .. 0x56554c09d0c0
global (data)       2000     0x1000  28.0 bits   0x55556cab8010 .. 0x56554c0a0010
heap                2000     0x1000  28.0 bits   0x55558922f2a0 .. 0x56557c2902a0
mmap                2000     0x1000  28.0 bits   0x7efc06728000 .. 0x7ffbea824000
libc   (puts)       1999   0x200000  19.0 bits   0x7efc06487cc0 .. 0x7ffbea687cc0
stack  (local)      2000       0x10  30.0 bits   0x7ffc0372d964 .. 0x7ffffffd8a94
$ python3 aslr_entropy.py ./aslr-nopie 2000
region          distinct  alignment  entropy   lowest .. highest
main   (code)          1          -   0 bits   0x4010b0
global (data)          1          -   0 bits   0x404030
heap                1994     0x1000  18.0 bits   0x41d2a0 .. 0x403f12a0
mmap                2000     0x1000  28.0 bits   0x7efc0b146000 .. 0x7ffb97ef0000
libc   (puts)       1997   0x200000  19.0 bits   0x7efc0ae87cc0 .. 0x7ffb97c87cc0
stack  (local)      2000       0x10  30.0 bits   0x7ffc006916b4 .. 0x7fffffc5dc14
```

The program, its data and heap and the anonymous mapping get the full 28 bits set by `vm.mmap_rnd_bits`: page-aligned addresses spread over $2^{28}$ pages, 1 TiB of address space. The stack is randomised at 16-byte granularity and gets 30 bits. The C library gets only 19 bits: its mapping is just over 2 MiB, and the kernel places such mappings on 2 MiB boundaries so that they can use huge pages ([lecture 9](../09-virtual-memory/#the-tlb-a-cache-for-translations)), which costs 9 of the 28 bits: a real trade-off between speed and security. Without PIE the program's code and data have no entropy at all, and even the heap gets only 18 bits.

### A stack overflow, detected

`overflow.c` contains the bug of the [stack figure](#the-stack-and-the-return-address): `greet` copies its argument into `char buf[16]` with `strcpy`. It is compiled twice, without and with the stack protector, and run with a short name, with 24 and with 40 characters:

```console
$ gcc -O0 -g -fno-stack-protector -o overflow-plain overflow.c
$ gcc -O0 -g -fstack-protector-strong -o overflow-canary overflow.c
$ ./overflow-plain Alice
hello, Alice
greet() returned normally
$ ./overflow-plain AAAAAAAAAAAAAAAAAAAAAAAA
hello, AAAAAAAAAAAAAAAAAAAAAAAA
Segmentation fault
$ ./overflow-plain AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
hello, AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Segmentation fault
$ ./overflow-canary Alice
hello, Alice
greet() returned normally
$ ./overflow-canary AAAAAAAAAAAAAAAAAAAAAAAA
hello, AAAAAAAAAAAAAAAAAAAAAAAA
greet() returned normally
$ ./overflow-canary AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
hello, AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
*** stack smashing detected ***: terminated
Aborted
$ echo $?
134
```

Without the protector, both long names crash the program, but only *after* `greet` has printed: the damage happens silently, and the crash comes when the corrupted values are used. With the protector, the 40-character name is caught at the end of `greet`: `__stack_chk_fail` prints the message and aborts the process with `SIGABRT` (exit status 128 + 6 = 134), before `ret` uses the corrupted return address. The 24-character name, however, passes unnoticed: in the protected build there are 8 bytes of padding between `buf` and the canary, and 24 characters plus the terminating zero reach exactly the canary's lowest byte, which is zero anyway. The overflow happened, but it did not change the canary. A canary detects corruption of the canary, nothing else.

### Inside the frame with gdb

`overflow.gdb` stops the unprotected program before and after the `strcpy` and prints the two 8-byte words at the frame pointer: the saved `rbp` and the return address.

```console
$ gdb -q -batch -x overflow.gdb --args ./overflow-plain AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA 2>&1 | grep -v -i thread
Breakpoint 1 at 0x1199: file overflow.c, line 12.
Breakpoint 2 at 0x11ac: file overflow.c, line 13.

Breakpoint 1, greet (name=0x7fffffff915a 'A' <repeats 40 times>) at overflow.c:12
12          strcpy(buf, name);                  /* BUG: no check that name fits in buf */
before strcpy: buf at 0x7fffffff87e0
0x7fffffff87f0: 0x00007fffffff8810      0x00005555555551fc
main + 50 in section .text of /root/lab12/overflow-plain

Breakpoint 2, greet (name=0x7fffffff915a 'A' <repeats 40 times>) at overflow.c:13
13          printf("hello, %s\n", buf);
after strcpy:
0x7fffffff87f0: 0x4141414141414141      0x4141414141414141

Program received signal SIGSEGV, Segmentation fault.
0x00005555555551c9 in greet (name=0x7fffffff915a 'A' <repeats 40 times>) at overflow.c:14
14      }
=> 0x5555555551c9 <greet+64>:   ret
```

The buffer starts 16 bytes below the frame pointer. Before the copy, the return address points back into `main`; after it, both words are `0x41` bytes, the letter A. The fault happens *at* the `ret` instruction: `0x4141414141414141` is not a canonical x86-64 address (the upper 16 bits must repeat bit 47), so the processor refuses to jump there and raises a general protection fault, which Linux delivers as `SIGSEGV`. The same view of the protected build shows the canary, 8 bytes below the frame pointer:

```console
$ gdb -q -batch -ex 'break 12' -ex 'break 13' -ex run -ex 'x/6gx $rbp-0x20' -ex continue -ex 'x/6gx $rbp-0x20' --args ./overflow-canary AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA 2>&1 | grep -v -i thread
Breakpoint 1 at 0x11c8: file overflow.c, line 12.
Breakpoint 2 at 0x11db: file overflow.c, line 13.

Breakpoint 1, greet (name=0x7fffffff9159 'A' <repeats 40 times>) at overflow.c:12
12          strcpy(buf, name);                  /* BUG: no check that name fits in buf */
0x7fffffff87d0: 0x0000000000000000      0x0000000000000000
0x7fffffff87e0: 0x0000000000000000      0xfd3472a03d281d00
0x7fffffff87f0: 0x00007fffffff8810      0x000055555555523f

Breakpoint 2, greet (name=0x7fffffff9159 'A' <repeats 40 times>) at overflow.c:13
13          printf("hello, %s\n", buf);
0x7fffffff87d0: 0x4141414141414141      0x4141414141414141
0x7fffffff87e0: 0x4141414141414141      0x4141414141414141
0x7fffffff87f0: 0x4141414141414141      0x0000555555555200
```

Before the copy the six words are: `buf` (two words), padding, the canary `0xfd3472a03d281d00` (random, with a zero lowest byte), the saved `rbp` and the return address. After the copy the canary, the saved `rbp` and the lowest byte of the return address (now `...5200`, the terminating zero of the string) are all overwritten, exactly as in the figure. The check before `leave` and `ret` notices the changed canary, so neither corrupted value is ever used.

### FORTIFY_SOURCE stops the copy

`fortify.c` has the same unchecked `strcpy`, directly in `main`. Ubuntu's GCC defines `_FORTIFY_SOURCE` by default when optimising; `-U_FORTIFY_SOURCE` switches it off:

```console
$ gcc -O2 -o fortify fortify.c
$ gcc -O2 -U_FORTIFY_SOURCE -o fortify-off fortify.c
$ objdump -d fortify | grep -E "call.*(strcpy|_chk)"
    10d6:       e8 a5 ff ff ff          call   1080 <__strcpy_chk@plt>
    10ec:       e8 9f ff ff ff          call   1090 <__printf_chk@plt>
    1108:       e8 63 ff ff ff          call   1070 <__stack_chk_fail@plt>
$ objdump -d fortify-off | grep -E "call.*(strcpy|_chk)"
    10d1:       e8 9a ff ff ff          call   1070 <strcpy@plt>
    10fe:       e8 7d ff ff ff          call   1080 <__stack_chk_fail@plt>
$ ./fortify Alice
copied: Alice
$ ./fortify AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
*** buffer overflow detected ***: terminated
Aborted
$ ./fortify-off AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
copied: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
*** stack smashing detected ***: terminated
Aborted
```

The compiler knew that `buf` has 16 bytes and replaced `strcpy` with `__strcpy_chk(buf, src, 16)` (and `printf` with its checking variant). The fortified program stops *before* copying anything: no byte of the frame is changed, and `copied:` is never printed. Without fortification the copy happens, the program goes on to print the overlong string from its corrupted frame, and only the canary check at the end of `main` stops it. The two defences complement each other: FORTIFY_SOURCE catches the overflow at the copy when the size is known; the canary catches it at the return when it is not.

### Heap bugs: glibc and AddressSanitizer

`uaf.c` frees a 32-byte block and then either reads it after a new `malloc` of the same size, or frees it a second time:

```console
$ gcc -O0 -g -o uaf uaf.c
$ gcc -O0 -g -fsanitize=address -o uaf-asan uaf.c
$ ./uaf use
p = 0x558262ea92a0, q = 0x558262ea92a0, p[0] = 'o'
$ ./uaf double
free(): double free detected in tcache 2
Aborted
$ ASAN_OPTIONS=color=never ./uaf-asan use 2>&1 | head -20
=================================================================
==2676==ERROR: AddressSanitizer: heap-use-after-free on address 0x503000000040 at pc 0x562f901b239d bp 0x7ffd8c968850 sp 0x7ffd8c968840
READ of size 1 at 0x503000000040 thread T0
    #0 0x562f901b239c in main /root/lab12/uaf.c:18
    #1 0x7f9e65c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x7f9e65c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x562f901b21e4 in _start (/root/lab12/uaf-asan+0x11e4) (BuildId: 820fe91794ad4ac3bd2e336beb4e73624bac101a)

0x503000000040 is located 0 bytes inside of 32-byte region [0x503000000040,0x503000000060)
freed by thread T0 here:
    #0 0x7f9e660fc4d8 in free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52
    #1 0x562f901b22f0 in main /root/lab12/uaf.c:14
    #2 0x7f9e65c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7f9e65c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x562f901b21e4 in _start (/root/lab12/uaf-asan+0x11e4) (BuildId: 820fe91794ad4ac3bd2e336beb4e73624bac101a)

previously allocated by thread T0 here:
    #0 0x7f9e660fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x562f901b22c5 in main /root/lab12/uaf.c:12
    #2 0x7f9e65c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
$ ASAN_OPTIONS=color=never ./uaf-asan double 2>&1 | grep -E "ERROR|SUMMARY"
==2678==ERROR: AddressSanitizer: attempting double-free on 0x503000000040 in thread T0:
SUMMARY: AddressSanitizer: double-free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52 in free
```

The plain build shows why use after free is dangerous: the new block `q` *is* the freed block `p`, and reading through the stale pointer `p` returns the first letter of the new owner's data, "other data". The program runs on without any error. glibc's allocator does catch the simple double free with a consistency check of its per-thread cache (*tcache*) and aborts, but such checks cover only some patterns. The ASan build reports the use after free at the very read (line 18), and says where the block was allocated (line 12) and freed (line 14): this is why testing with sanitizers, and fuzzing under them, finds memory bugs that would otherwise surface, if ever, as rare and puzzling corruption.

### Which protections does a program have?

`hardening.sh` is a small version of the well-known `checksec` tool: it reads each ELF file with `readelf` and reports PIE (an executable of type `DYN` with the `PIE` flag), NX (no `E` in `GNU_STACK`), RELRO (a `GNU_RELRO` segment, full with `BIND_NOW`), the canary (an import of `__stack_chk_fail`), the number of fortified functions (imports named `__*_chk`) and the CET marks in the GNU property note. First the defaults of this compiler, then two system programs, the demo programs, and a program built with every protection switched off:

```console
$ echo | gcc -O2 -dM -E - | grep FORTIFY
#define _FORTIFY_SOURCE 3
$ gcc -Q -O2 --help=common | grep -E "^  -f(PIE|stack-protector-strong|stack-clash-protection|cf-protection) "
  -fPIE                                 [enabled]
  -fcf-protection                       -fcf-protection=full
  -fstack-clash-protection              [enabled]
  -fstack-protector-strong              [enabled]
$ gcc -O2 -no-pie -fno-stack-protector -U_FORTIFY_SOURCE -fcf-protection=none -z execstack -z norelro -o weak fortify.c
$ bash hardening.sh /usr/bin/ls /usr/bin/passwd fortify fortify-off overflow-plain weak
ls                     PIE=yes NX=yes RELRO=full    canary=yes fortified=9  CET=IBT, SHSTK
passwd                 PIE=yes NX=yes RELRO=full    canary=yes fortified=6  CET=IBT, SHSTK
fortify                PIE=yes NX=yes RELRO=full    canary=yes fortified=2  CET=IBT, SHSTK
fortify-off            PIE=yes NX=yes RELRO=full    canary=yes fortified=0  CET=IBT, SHSTK
overflow-plain         PIE=yes NX=yes RELRO=full    canary=no  fortified=0  CET=IBT, SHSTK
weak                   PIE=no  NX=no  RELRO=no      canary=no  fortified=0  CET=none
$ readelf -lW weak fortify | grep -E "^File|GNU_STACK|GNU_RELRO"
File: weak
  GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RWE 0x10
File: fortify
  GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RW  0x10
  GNU_RELRO      0x002da8 0x0000000000003da8 0x0000000000003da8 0x000258 0x000258 R   0x1
$ readelf -dW fortify | grep FLAGS
 0x000000000000001e (FLAGS)              BIND_NOW
 0x000000006ffffffb (FLAGS_1)            Flags: NOW PIE
$ readelf -nW fortify | grep feature
  GNU                  0x00000020       NT_GNU_PROPERTY_TYPE_0        Properties: x86 feature: IBT, SHSTK, x86 ISA needed: x86-64-baseline
```

Ubuntu's GCC turns on PIE, the strong stack protector, FORTIFY_SOURCE level 3, stack-clash protection and CET marks without being asked, and its linker defaults to full RELRO, so an ordinary `gcc -O2` already produces a hardened program, like the distribution's own `ls` and `passwd`. `overflow-plain` lacks only the canary that was switched off on purpose. The `weak` program shows what each flag removes: it loads at a fixed address, asks for an executable stack (`RWE`), and keeps its GOT writable. The CET marks state that the program is *compatible* with IBT and shadow stacks; whether they are enforced depends on the processor and the kernel. This virtual machine's processor reports neither feature to the guest and the kernel was built without them, so here the marks have no effect.

### Seccomp: giving up system calls

`seccomp.c` demonstrates both modes. In strict mode it may still `write`, but its next system call, the harmless `getpid`, kills it. In filter mode it installs a BPF filter that answers `mkdir` with `EPERM`, allows `getpid`, and kills the process at `socket`:

```console
$ gcc -O2 -o seccomp seccomp.c
$ ./seccomp strict
entering strict mode
write() still works
now calling getpid() ...
Killed
$ echo $?
137
$ ./seccomp filter
before the filter:
  Seccomp:      0
after the filter:
  Seccomp:      2
mkdir:  Operation not permitted
getpid: 2883 (allowed)
socket: ...
Bad system call
$ echo $?
159
$ dmesg | tail -2
[ 1532.740367] audit: type=1326 audit(1791460901.490:4): auid=4294967295 uid=0 gid=0 ses=4294967295 subj=kernel pid=2882 comm="seccomp" exe="/root/lab12/seccomp" sig=9 arch=c000003e syscall=39 compat=0 ip=0x7fd87992752d code=0x0
[ 1532.746154] audit: type=1326 audit(1791460901.494:5): auid=4294967295 uid=0 gid=0 ses=4294967295 subj=kernel pid=2883 comm="seccomp" exe="/root/lab12/seccomp" sig=31 arch=c000003e syscall=41 compat=0 ip=0x7fb42e92c57b code=0x80000000
```

Strict mode killed the process with `SIGKILL` (exit status 128 + 9 = 137). In filter mode `/proc/self/status` shows the mode change from 0 to 2 (filter); the forbidden `mkdir` simply failed, as if the kernel had refused it, and the program continued; `socket` killed it with `SIGSYS`, "Bad system call" (128 + 31 = 159). The kernel's audit log records both kills with the system-call numbers, 39 (`getpid`) and 41 (`socket`) on x86-64, and the action codes `0x0` (kill thread) and `0x80000000` (kill process). The process ran as root, yet it lost these system calls for good: seccomp restricts the process, not the user.

### The kernel hides its addresses

`kernel-hiding.sh` looks up two kernel symbols in `/proc/kallsyms`, as root, as the user `nobody`, as root without the capability `CAP_SYSLOG` (with `capsh`, [lecture 11](../11-access-control/#root-and-capabilities)), and with `kernel.kptr_restrict` raised to 2:

```console
$ bash kernel-hiding.sh
== where is the kernel? (root, with CAP_SYSLOG)
ffffffff81000000 T _text
ffffffff813a22e0 T commit_creds
== the same as the user nobody
0000000000000000 T _text
0000000000000000 T commit_creds
== root without CAP_SYSLOG
0000000000000000 T _text
0000000000000000 T commit_creds
== kernel.kptr_restrict = 2: hidden even from root
kernel.kptr_restrict = 2
0000000000000000 T _text
0000000000000000 T commit_creds
== the settings
kernel.kptr_restrict = 0
kernel.dmesg_restrict = 1
kernel.perf_event_paranoid = 2
kernel.randomize_va_space = 2
== dmesg as nobody
dmesg: read kernel buffer failed: Operation not permitted
```

The symbol names are public (they come from the kernel's source), but their addresses are shown only to a process with `CAP_SYSLOG`; it is the capability that counts, not the UID 0, as the root shell without it shows. `kptr_restrict = 2` hides them from everyone. The kernel log, which also contains addresses, is closed to ordinary users by `dmesg_restrict`.

One detail is honest evidence of a limit: the kernel's text starts at `0xffffffff81000000`, which is the default link address of an x86-64 kernel, not a randomised one. The kernel is built with KASLR (`CONFIG_RANDOMIZE_BASE=y`), but on x86 the random placement is chosen by the kernel's decompression stub at boot, and this virtual machine's hypervisor (Firecracker, see [below](#how-did-this-machine-boot)) loads the uncompressed kernel directly, so that step never runs. Hiding the address of a kernel that is not randomised protects nothing; KASLR is only as good as the boot path that applies it.

### Lockdown: protecting the kernel from root

`lockdown.sh` shows the lockdown mode, tries to read a scheduler file in debugfs as root, and tries to switch lockdown off:

```console
$ bash lockdown.sh
== lockdown mode (the one in brackets is active)
none [integrity] confidentiality
== a debugging interface of the scheduler, read by root
cat: /sys/kernel/debug/sched/features: Operation not permitted
[ 1539.700429] Lockdown: cat: debugfs access is restricted; see man kernel_lockdown.7
== can root switch it off?
lockdown.sh: line 13: echo: write error: Operation not permitted
none [integrity] confidentiality
```

This kernel was configured to start in `integrity` mode (the boot log said "Kernel is locked down from Kernel configuration"). Root may mount debugfs, but reading a file through which the scheduler can be reconfigured is refused, and the kernel logs why. Root cannot lower the mode either; only a reboot with another configuration can. The other restricted operations of `integrity` mode, such as loading unsigned modules or writing `/dev/mem`, are not even available here: this kernel has no module support (`nomodule`) and no `/dev/mem`.

### Which CPU flaws does the kernel know about?

Every file in `/sys/devices/system/cpu/vulnerabilities/` names one transient-execution flaw, and its content says whether this CPU is affected and how the kernel handles it:

```console
$ cd /sys/devices/system/cpu/vulnerabilities && grep . *
gather_data_sampling:Not affected
ghostwrite:Not affected
indirect_target_selection:Not affected
itlb_multihit:Not affected
l1tf:Not affected
mds:Not affected
meltdown:Not affected
mmio_stale_data:Not affected
old_microcode:Not affected
reg_file_data_sampling:Not affected
retbleed:Not affected
spec_rstack_overflow:Not affected
spec_store_bypass:Mitigation: Speculative Store Bypass disabled via prctl
spectre_v1:Mitigation: usercopy/swapgs barriers and __user pointer sanitization
spectre_v2:Mitigation: Enhanced / Automatic IBRS; IBPB: conditional; PBRSB-eIBRS: SW sequence; BHI: Vulnerable
srbds:Not affected
tsa:Not affected
tsx_async_abort:Not affected
vmscape:Not affected
$ grep -o -w -E 'ibrs|ibpb|stibp|ssbd|md_clear|arch_capabilities' /proc/cpuinfo | sort | uniq -c
      2 arch_capabilities
      2 ibpb
      2 ibrs
      2 md_clear
      2 ssbd
      2 stibp
```

This virtual CPU belongs to a recent processor generation: Meltdown and most of the buffer-sampling flaws are reported as "Not affected", so KPTI is not needed. Spectre cannot be designed away completely, so its variants show active mitigations: speculation barriers in the kernel's user-copy routines and at kernel entry (`swapgs`), and sanitization (masking) of pointers that come from user space (variant 1); the hardware's enhanced IBRS for indirect branches, a predictor flush (IBPB) on a switch to a process that asked for it (`conditional`), and a short software sequence for a leftover return-prediction issue (`PBRSB-eIBRS`) (variant 2); and speculative store bypass disabled only for programs that ask for it with `prctl`. The `spectre_v2` line also admits one open issue, branch history injection (BHI), for which this kernel enables no mitigation. The flags in `/proc/cpuinfo` list the controls the virtual CPU offers (`md_clear` is the microcode's buffer-clearing support against MDS, `arch_capabilities` the register through which the CPU tells the kernel which flaws it does not have); each appears twice because the machine has two virtual CPUs.

### How did this machine boot?

`boot.sh` collects what the machine can tell about its own boot:

```console
$ bash boot.sh
== firmware interfaces
acpi  memmap
no /sys/firmware/efi: not booted by UEFI
== Secure Boot and TPM
mokutil not installed
ls: cannot access '/dev/tpm*': No such file or directory
ls: cannot access '/sys/class/tpm': No such file or directory
== the first steps of the kernel
[    0.000000] Linux version 6.18.44-fc-v80 (builder@sandboxing) (gcc (GCC) 15.3.0, GNU ld (GNU Binutils) 2.46) #1 SMP PREEMPT_DYNAMIC @0
[    0.000000] NX (Execute Disable) protection: active
[    0.001542] RAMDISK: [mem 0xbf20e000-0xbfffffff]
[    0.001704] ACPI: RSDP 0x00000000000E0000 000024 (v02 FIRECK)
[    0.137791] Kernel is locked down from Kernel configuration; see man kernel_lockdown.7
[    0.452649] LSM: initializing lsm=lockdown,capability,landlock,selinux,bpf
[    0.803630] Unpacking initramfs...
[    1.060837] Write protecting the kernel read-only data: 28672k
[    1.073816] Run /process_api as init process
== process 1
  PID COMMAND
    1 process_api
System has not been booted with systemd as init system (PID 1). Can't operate.
```

This machine has almost none of the chain of trust described above, and the output says so. It is a Firecracker microVM (the ACPI tables come from `FIRECK`): there is no UEFI firmware (`/sys/firmware/efi` is missing), no boot loader, no Secure Boot and no TPM. The hypervisor loads the kernel and an initramfs (`RAMDISK`) straight into memory and jumps into the kernel, which starts the hosting service's own program `/process_api` as process 1 instead of systemd, so `systemd-analyze` cannot work. The kernel does apply its own protections early: NX is active from the first microsecond, lockdown and the security modules (Landlock, SELinux, BPF) start before any process, and the read-only data are write-protected before `init` runs. The trust in this boot rests entirely on the hypervisor and the cloud operator: precisely the situation that confidential VMs are designed to change. A real PC is examined in [lab exercise 7](#lab-exercises).

<details>
<summary><b>Explained simply:</b> setarch, sysctl, objdump, readelf, ELF program header, GOT, tcache, SIGABRT, SIGSYS, exit status, audit log, kallsyms, CAP_SYSLOG, capsh, debugfs, securityfs, speculative store bypass, prctl, enhanced IBRS, BHI, /proc/cpuinfo flags, Firecracker, microVM, ACPI</summary>

- **setarch -R:** runs one program with address randomisation switched off. **sysctl:** reads and changes kernel settings.
- **objdump, readelf:** tools that show the inside of a program file: its machine code, and its headers and tables.
- **ELF program header:** a line in a program file that tells the kernel how to load one part, with its permissions (R, W, E).
- **tcache:** glibc's small per-thread cache of recently freed memory blocks, which it hands out again first.
- **SIGABRT, SIGSYS, exit status:** signals that stop a program: SIGABRT when the program aborts itself, SIGSYS for a forbidden system call. A shell reports a program killed by signal $s$ with the exit status $128 + s$.
- **Audit log:** the kernel's security diary, here part of the kernel log.
- **kallsyms:** the kernel's list of its own functions and variables with their addresses. **CAP_SYSLOG:** the special right needed to see those addresses and the kernel log. **capsh:** a tool to start a shell with fewer capabilities.
- **debugfs, securityfs:** special file systems through which the kernel offers debugging switches and security settings as files.
- **Speculative store bypass, prctl:** a Spectre variant in which the processor reads memory before it knows that an earlier write changes it. **prctl** is the system call with which a program asks the kernel for special treatment, here "switch this speculation off for me".
- **Enhanced IBRS, BHI:** enhanced IBRS is a processor mode, switched on once, that keeps less privileged code from steering the kernel's branch guesses. **BHI** (branch history injection) is a later trick that gets around it through the history of recent branches.
- **/proc/cpuinfo flags:** short words listing the features a processor offers, such as `ibrs` or `md_clear`.
- **Firecracker, microVM:** a very small, fast-starting virtual machine program used by cloud services; a microVM has only the few devices it really needs.
- **ACPI:** the standard tables through which firmware (or a hypervisor) describes the machine to the operating system.

</details>

## Lab exercises

1. **ASLR in your process.** Run `aslr` on your own Linux machine and compare with this lecture. Then run `cat /proc/self/maps` twice and find the C library's start address: is it a multiple of 2 MiB (`0x200000`) on your kernel? Run `aslr_entropy.py` with 32-bit builds (`gcc -m32`, if `gcc-multilib` is installed) and compare the entropy.
2. **Canaries.** Compile `overflow.c` with `-fstack-protector-strong` and find the shortest argument that triggers `*** stack smashing detected ***`. Explain the number from the frame layout that gdb shows. Then compile with `-O2` and repeat: what changes in the layout, and why?
3. **FORTIFY_SOURCE.** Change `fortify.c` so that the buffer is allocated with `malloc(16)` and copied with `strcpy`. Compile with `-O2` and `-D_FORTIFY_SOURCE=2`, then with `=3` (and check with `objdump` whether `__strcpy_chk` is called). Explain the difference between levels 2 and 3.
4. **Sanitizers.** Write a program with a one-byte heap overflow (`char *p = malloc(10); p[10] = 0;`) and one with a stack overflow of an array index. Run them with and without `-fsanitize=address`. Then try `-fsanitize=undefined` on a signed integer overflow. Which bugs went unnoticed without the sanitizers?
5. **Hardening of your system.** Run `hardening.sh` on all programs in `/usr/bin` (`bash hardening.sh /usr/bin/* 2>/dev/null | grep -v "canary=yes"`). Which programs lack a canary, and why might that be harmless (hint: look at their size and language)? If your distribution packages `checksec`, compare its output.
6. **Seccomp for a real service.** Look at a systemd service on your machine with `systemctl show -p SystemCallFilter,NoNewPrivileges,CapabilityBoundingSet systemd-resolved` (or another service), and at its `Seccomp:` line in `/proc/PID/status`. Then extend `seccomp.c` to return `EPERM` for `openat` of anything except one allowed file (hint: seccomp cannot compare strings; why not, and what would you use instead? Look up Landlock).
7. **The boot chain of a real PC** (no outputs are given here, since the lecture's virtual machine has no firmware, Secure Boot or TPM). On a Linux PC or laptop booted with UEFI, run `mokutil --sb-state`, `ls /sys/firmware/efi`, `bootctl status` (systemd-boot) or `efibootmgr -v`, and `sudo dmesg | grep -i -E "secure ?boot|lockdown|tpm"`. If a TPM is present (`ls /dev/tpm*`), install `tpm2-tools` and run `sudo tpm2_pcrread sha256:0,2,4,7,8,9,11`. Reboot, read the PCRs again, and explain which values stayed the same and why. Then change one GRUB menu entry's kernel command line once at the boot menu (press `e`), boot, and read PCR 8 again.
8. **TPM-bound encryption** (on a test VM with a virtual TPM, for example QEMU with `swtpm` or a VirtualBox/Hyper-V VM with a TPM enabled; no outputs are given). Create a LUKS volume on a spare virtual disk, enrol the TPM with `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/vdb`, and unlock it with `sudo /usr/lib/systemd/systemd-cryptsetup attach test /dev/vdb - tpm2-device=auto`. Then disable Secure Boot in the VM's firmware settings and try again. What happens, and how would you recover the data?

## Review questions

1. Name the three security goals of the CIA triad and give one attack on an operating system against each.
2. What is the trusted computing base of a Linux server? Why should it be small, and which component of it is largest?
3. Describe a typical attack chain from a remote request to persistent root access. Which defences of this lecture act at each step?
4. Explain, with a drawing of a stack frame, how a stack buffer overflow can change a program's control flow. Why does the overflow reach the return address rather than other frames' variables below the buffer?
5. Distinguish spatial and temporal memory safety, and classify stack overflow, heap overflow, use after free and double free.
6. Why is use after free especially dangerous in programs written in C++? What did the `uaf` demo show about the reuse of freed memory?
7. How can an integer overflow lead to a heap overflow? Give a short code example.
8. What does a format-string bug allow an attacker to do, and how do compilers and FORTIFY_SOURCE react to it?
9. How does a stack canary work? Why is its lowest byte zero? In the demo, why did a 24-character argument not trigger the canary, although it overflowed the buffer?
10. Why did NX not end memory-corruption attacks? Explain code reuse and return-oriented programming in two or three sentences.
11. What is ASLR's entropy? Using the measured values, how many attempts would blind guessing of the C library's base need on average? Why is an information leak often the real obstacle?
12. Why does ASLR need PIE? What did the demo show for a non-PIE program?
13. What do partial and full RELRO protect, and what does `BIND_NOW` have to do with it?
14. Compare FORTIFY_SOURCE and the stack canary with the `fortify` demo: when does each one act, and what can each one not detect?
15. Explain the shadow stack and indirect branch tracking of Intel CET, and Arm's PAC and BTI. Which attacks do they stop, and what must the compiler, the libraries and the kernel do for them to work?
16. Name four measures by which the Linux kernel protects itself (from attackers in user space and from root), and explain one of them in detail. Why did the demo machine's kernel sit at its default address despite `CONFIG_RANDOMIZE_BASE=y`?
17. What is seccomp? Explain strict and filter mode with the demo's results, and why `no_new_privs` is required for unprivileged processes.
18. Describe the boot chain of a Linux PC with UEFI. What do Secure Boot and measured boot each do, and why are both useful?
19. How does a TPM PCR work? Why can malware that runs after the kernel not "repair" a PCR value, and how is this used to bind disk encryption to the boot chain?
20. Compare Arm TrustZone, Intel SGX and confidential VMs (SEV-SNP, TDX): what is protected from whom, and what remains in the trusted computing base?
21. What are CVE and CVSS? Why does a high CVSS base score not necessarily mean that a particular server must be patched first? Why should the version number of an enterprise kernel not be used to decide whether it is vulnerable?
22. What is a side channel? Explain, without code, how a difference between a cache hit and a cache miss can reveal which memory another program touched.
23. Why did Meltdown make the kernel readable from user mode on affected processors, and how does KPTI prevent it? What does KPTI cost, and why does PCID reduce that cost? What did `/sys/devices/system/cpu/vulnerabilities` report about the lecture's machine?

<details>
<summary><strong>Answer key (for instructors)</strong></summary>

1. Confidentiality: reading another user's files through a bug, or a server's private key from a process's memory. Integrity: replacing a system binary or the kernel (rootkit, bootkit), modifying a database. Availability: crashing the kernel with a malformed packet, a fork bomb or exhausting disk or memory.
2. The kernel, the firmware and boot loader that started it, the CPU and its microcode, and the privileged processes that make security decisions (login, sshd, sudo, setuid programs, systemd). Every bug in it can defeat the policy, and a small TCB is easier to verify (economy of mechanism). The largest part is the kernel with its drivers.
3. (1) Remote code execution through a bug in a network service: made hard by canaries, NX, ASLR/PIE, RELRO, FORTIFY_SOURCE, CFI; its damage is limited by running the service as its own user with few capabilities, seccomp and a MAC domain. (2) Privilege escalation through a kernel or setuid bug: kernel hardening (KASLR, SMEP/SMAP, hardened usercopy), seccomp reducing reachable kernel code, fewer setuid programs. (3) Persistence: lockdown (no unsigned modules), Secure Boot and measured boot, read-only or image-based systems. Updates close the bugs at every step.
4. The frame holds, from higher to lower addresses, the return address, the saved frame pointer and the local variables including the buffer. Copying fills the buffer from low to high addresses, so excess bytes overwrite the saved registers and the return address above it; `ret` then jumps to the address taken from the input. Lower addresses belong to frames of functions called later, which are not live at that point, so the copy runs away from them.
5. Spatial: accesses stay within the object's bounds (stack and heap overflows violate it). Temporal: accesses happen only during the object's lifetime (use after free and double free violate it).
6. Freed memory is quickly reused for another object; a stale pointer then reads or writes the new object. C++ objects contain pointers to virtual-function tables, so an attacker who controls the data of the new object controls the target of the next virtual call through the stale pointer. In the demo the next `malloc(32)` returned exactly the freed block, and the stale pointer read the new owner's data without any error.
7. `p = malloc(n * sizeof(struct item)); for (i = 0; i < n; i++) p[i] = ...;` If `n * sizeof` exceeds the integer's range, the product wraps to a small value, a small block is allocated, and the loop writes `n` elements past its end.
8. With the input as the format string, `%x`/`%p` read values from the stack (information leak, for example of the canary or of addresses that defeat ASLR) and `%n` writes to memory. Compilers warn with `-Wformat -Wformat-security`; fortified `printf` refuses `%n` in a format string located in writable memory.
9. A random value is placed between the local buffers and the saved registers at function entry and compared with the reference copy before return; a mismatch aborts the process. The zero byte stops string functions from reading or copying the canary and makes a string overflow write a zero there. In the demo there were 8 bytes of padding between `buf` and the canary; 24 characters plus the terminating zero reached exactly the canary's lowest byte, which is zero already, so the canary was unchanged.
10. NX prevents executing injected code, but not redirecting control to code that already exists. Code reuse jumps to library functions (return-to-libc) or chains short existing instruction sequences ending in `ret` ("gadgets"), each started by an overwritten return address on the stack, so that the stack contents form a program (ROP); Shacham (2007) showed that this is Turing-complete with the C library's code alone.
11. The number of random bits in a region's address; with $n$ bits a blind guess succeeds with probability $2^{-n}$. For the C library's 19 bits that is on average about $2^{18}$, roughly 262,000 attempts if the layout stays the same between attempts (a forking server, wrong guesses crossed off), and $2^{19}$, roughly 524,000, if the target is re-randomised after every crash; each failed attempt usually crashes the target, which is noticeable. Because only region bases are random, one leaked pointer reveals the whole region; so attackers look for a leak instead of guessing, and ASLR turns one bug into a requirement for two.
12. A non-PIE executable is linked for a fixed address and cannot be moved, so its code and data provide known addresses for code reuse. In the demo the non-PIE program's `main` and global variable were at 0x4010b0 and 0x404030 in every run (0 bits), while the PIE build had 28 bits.
13. They protect the dynamic linker's tables, above all the GOT, a table of function pointers, from being overwritten. Partial RELRO makes some sections read-only; full RELRO also makes the GOT entries for functions read-only, which requires resolving all symbols at start-up (`BIND_NOW`, `-z now`) instead of lazily at the first call.
14. FORTIFY_SOURCE checks the copy against the destination's size before it happens, so no byte is overwritten (`fortify` aborted with "buffer overflow detected" without printing); it works only when the compiler knows the size. The canary detects the overwrite after it happened, at function return (`fortify-off` printed the corrupted string first); it misses overflows that do not reach or change the canary, heap overflows and non-linear writes.
15. Shadow stack: `CALL` also stores the return address on a protected stack, `RET` compares and faults on mismatch, stopping overwritten return addresses (ROP). IBT: indirect calls/jumps must land on `endbr64`, stopping jumps into the middle of functions (JOP, call-oriented gadgets). PAC signs pointers (return addresses) with a secret key and context and verifies them before use; BTI is Arm's equivalent of IBT. The compiler must emit the instructions and mark the binary, every library loaded into the process must be compatible (otherwise enforcement is disabled for the process), and the kernel must enable the feature and manage shadow-stack memory.
16. KASLR with hidden addresses (`kptr_restrict`, `dmesg_restrict`), SMEP/SMAP, read-only kernel code and data (STRICT_KERNEL_RWX), stack protector and hardened usercopy, lockdown, signed modules, seccomp to reduce reachable code. Example SMAP: the kernel cannot access user memory except within explicit copy routines, so a corrupted kernel pointer cannot be made to point at attacker-prepared user data. On x86, KASLR is applied by the decompression stub of the compressed kernel; the Firecracker hypervisor loads the uncompressed kernel directly, so the randomisation never ran.
17. A mechanism by which a process irrevocably restricts its own system calls. Strict mode allows only read, write, exit and sigreturn: the demo's `getpid` was killed with SIGKILL (status 137). Filter mode runs a BPF program on every call: `mkdir` returned EPERM, `getpid` was allowed, `socket` killed the process with SIGSYS (159), logged by audit with the system-call numbers. Without `no_new_privs`, an unprivileged process could install a filter and then execute a setuid program that would run with root's rights under a filter it does not expect, for example one that makes a security-relevant call fail silently.
18. Firmware (UEFI) initialises the hardware and loads shim from the EFI system partition; shim loads GRUB or systemd-boot; the boot loader loads the kernel and initramfs; the kernel starts its init from the initramfs, which mounts the root file system and starts systemd as PID 1. Secure Boot verifies the signature of each next stage and refuses unsigned or revoked code (prevention). Measured boot hashes each stage into TPM PCRs and records an event log (evidence), which allows sealing secrets to a known state and proving the state to others (attestation), and also catches signed but unexpected components.
19. A PCR can only be extended: new value = hash(old value ‖ measurement); it starts at zero at reset. Because the hash cannot be inverted, no software can produce a chosen value later, and the final value reflects all measurements in order. Software running after the kernel can extend, but not reset or set, the PCRs. Disk encryption seals the disk key to selected PCRs (for example PCR 7, the Secure Boot state); the TPM releases it only if the PCRs match, so a modified boot chain or another machine gets nothing.
20. TrustZone: the secure world (trusted OS and apps, secure monitor) is protected from the normal world including its kernel; the TCB is the CPU, the secure-world software and the boot chain. SGX: an enclave is protected from the OS, the hypervisor and other processes; TCB only the CPU and the enclave code, but the untrusted OS controls its environment (paging, scheduling), and SGX is deprecated on client CPUs. Confidential VMs: a whole VM is protected (encryption and integrity) from the hypervisor, the host and the operator; TCB the CPU with its security processor/firmware and the guest itself; availability is not protected; attestation proves the initial state.
21. CVE: a unique identifier for a publicly known vulnerability, assigned by a CNA. CVSS: a 0–10 severity score from exploitability and impact attributes. The base score ignores the environment: whether the component is installed, reachable (for example network-exposed), configured in an affected way, or protected by other layers; a lower-scored flaw in an exposed service may be more urgent. Enterprise kernels keep their base version and receive backported fixes (and sometimes are affected by bugs that "newer" versions are said to have), so only the vendor's advisories show whether a given build is fixed.
22. A side channel leaks information through a physical effect of computation (time, power, cache state) rather than through the program's outputs. A cached line is read in a few nanoseconds, an uncached one in about a hundred; if the attacker first evicts (or flushes) shared lines and later times its own accesses to them, the fast ones are those the victim has used in between, revealing the victim's access pattern, which can depend on a secret.
23. On affected processors, a load from a kernel address in user mode was executed transiently before the permission check took effect; the fault came, but the loaded value had already changed cache state, which could be measured. Since Linux mapped the whole kernel into every address space, all of kernel memory was exposed. KPTI uses separate page tables in user mode that map (almost) nothing of the kernel, so there is nothing to load. Every system call, interrupt and exception then switches page tables; without PCID that would flush the TLB each time, with PCID the entries of both address spaces stay tagged in the TLB. The lecture's machine reported Meltdown as "Not affected" (no KPTI needed) and active mitigations for the Spectre variants, with one admitted gap (BHI).

**Lab answers.** Lab 1: on recent kernels like the lecture's, libc's base is 2 MiB-aligned (about 19 bits); older kernels place it at any page boundary; 32-bit processes get far less entropy (the default `mmap_rnd_compat_bits` is 8). Lab 2: in the `-O0` build the canary is reached from 25 characters on (24 plus the zero byte only rewrite its zero byte); at `-O2` the compiler may drop the frame pointer and lay out the frame differently, so the threshold changes. Lab 3: level 2 checks only sizes known at compile time (`__builtin_object_size`), level 3 also sizes known at run time (`__builtin_dynamic_object_size`), such as a `malloc` with a variable size; with a constant 16 both catch it. Lab 4: without sanitizers the one-byte heap overflow usually goes unnoticed (malloc rounds sizes up), and signed overflow silently wraps or is optimised in surprising ways; ASan and UBSan report each at the faulting line. Lab 5: programs without arrays on the stack need no canary even with `-fstack-protector-strong`; programs written in Go or Rust do not use the C canary at all. Lab 6: many systemd services use `SystemCallFilter=@system-service` and `NoNewPrivileges=yes`; their status shows `Seccomp: 2`. Seccomp sees only the pointer to the path, which user space could change after the check (time-of-check to time-of-use), so it cannot safely filter path names; Landlock restricts file access by path in the kernel. Lab 7: PCR 0, 2, 4 and 7 stay the same across reboots of an unchanged system; PCR 8 changes when the command line is edited, because GRUB measures the commands it executes. Lab 8: with Secure Boot disabled PCR 7 changes, the TPM refuses to unseal and the volume asks for the passphrase or recovery key, which must therefore always be enrolled as well.

</details>

## References

Abadi, M., Budiu, M., Erlingsson, Ú., & Ligatti, J. (2005). Control-flow integrity. In *Proceedings of the 12th ACM Conference on Computer and Communications Security (CCS '05)* (pp. 340–353). ACM. https://doi.org/10.1145/1102120.1102165

Advanced Micro Devices. (2020). *AMD SEV-SNP: Strengthening VM isolation with integrity protection and more* [White paper]. https://docs.amd.com/v/u/en-US/SEV-SNP-strengthening-vm-isolation-with-integrity-protection-and-more

Aleph One. (1996). Smashing the stack for fun and profit. *Phrack, 7*(49), Article 14. https://archives.phrack.org/issues/49/14.txt

Anderson, R. (2020). *Security engineering: A guide to building dependable distributed systems* (3rd ed.). Wiley.

Apple Inc. (2026). *Apple platform security*. Retrieved October 8, 2026, from https://support.apple.com/guide/security/welcome/web

Costan, V., & Devadas, S. (2016). *Intel SGX explained* (Cryptology ePrint Archive, Paper 2016/086). https://eprint.iacr.org/2016/086

Cowan, C., Pu, C., Maier, D., Walpole, J., Bakke, P., Beattie, S., Grier, A., Wagle, P., Zhang, Q., & Hinton, H. (1998). StackGuard: Automatic adaptive detection and prevention of buffer-overflow attacks. In *Proceedings of the 7th USENIX Security Symposium* (pp. 63–78). USENIX Association.

FIRST. (2023). *Common Vulnerability Scoring System version 4.0: Specification document*. Forum of Incident Response and Security Teams. https://www.first.org/cvss/v4.0/specification-document

Gruss, D., Lipp, M., Schwarz, M., Fellner, R., Maurice, C., & Mangard, S. (2017). KASLR is dead: Long live KASLR. In *Engineering Secure Software and Systems (ESSoS 2017)* (Lecture Notes in Computer Science, Vol. 10379, pp. 161–176). Springer. https://doi.org/10.1007/978-3-319-62105-0_11

Intel Corporation. (n.d.). *12th Generation Intel Core processors datasheet, volume 1 of 2* (Document 655258). Retrieved October 8, 2026, from https://cdrdv2-public.intel.com/655258/655258-011.pdf

Intel Corporation. (2020). *Intel Trust Domain Extensions* [White paper, document 343961-002US]. https://www.intel.com/content/dam/develop/external/us/en/documents/tdx-whitepaper-final9-17.pdf

Jones, L. (2024, June 19). How kernel CVE numbers are assigned. *LWN.net*. https://lwn.net/Articles/978711/

Kocher, P., Horn, J., Fogh, A., Genkin, D., Gruss, D., Haas, W., Hamburg, M., Lipp, M., Mangard, S., Prescher, T., Schwarz, M., & Yarom, Y. (2019). Spectre attacks: Exploiting speculative execution. In *2019 IEEE Symposium on Security and Privacy (SP)* (pp. 1–19). IEEE. https://doi.org/10.1109/SP.2019.00002

Linux man-pages project. (n.d.). *kernel_lockdown(7): Kernel image access prevention feature*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man7/kernel_lockdown.7.html

Lipp, M., Schwarz, M., Gruss, D., Prescher, T., Haas, W., Fogh, A., Horn, J., Mangard, S., Kocher, P., Genkin, D., Yarom, Y., & Hamburg, M. (2018). Meltdown: Reading kernel memory from user space. In *Proceedings of the 27th USENIX Security Symposium* (pp. 973–990). USENIX Association. https://www.usenix.org/conference/usenixsecurity18/presentation/lipp

Pinto, S., & Santos, N. (2019). Demystifying Arm TrustZone: A comprehensive survey. *ACM Computing Surveys, 51*(6), Article 130. https://doi.org/10.1145/3291047

Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proceedings of the IEEE, 63*(9), 1278–1308. https://doi.org/10.1109/PROC.1975.9939

Serebryany, K., Bruening, D., Potapenko, A., & Vyukov, D. (2012). AddressSanitizer: A fast address sanity checker. In *Proceedings of the 2012 USENIX Annual Technical Conference (USENIX ATC '12)* (pp. 309–318). USENIX Association.

Shacham, H. (2007). The geometry of innocent flesh on the bone: Return-into-libc without function calls (on the x86). In *Proceedings of the 14th ACM Conference on Computer and Communications Security (CCS '07)* (pp. 552–561). ACM. https://doi.org/10.1145/1315245.1315313

Shanbhogue, V., Gupta, D., & Sahita, R. (2019). Security analysis of processor instruction set architecture for enforcing control-flow integrity. In *Proceedings of the 8th International Workshop on Hardware and Architectural Support for Security and Privacy (HASP '19)*. ACM. https://doi.org/10.1145/3337167.3337175

Spafford, E. H. (1989). The Internet worm program: An analysis. *ACM SIGCOMM Computer Communication Review, 19*(1), 17–57. https://doi.org/10.1145/66093.66095

Szekeres, L., Payer, M., Wei, T., & Song, D. (2013). SoK: Eternal war in memory. In *2013 IEEE Symposium on Security and Privacy* (pp. 48–62). IEEE. https://doi.org/10.1109/SP.2013.13

The Chromium Projects. (n.d.). *Memory safety*. Retrieved October 8, 2026, from https://www.chromium.org/Home/chromium-security/memory-safety/

The kernel development community. (n.d.-a). *CVEs*. The Linux Kernel documentation. Retrieved October 8, 2026, from https://docs.kernel.org/process/cve.html

The kernel development community. (n.d.-b). *Hardware vulnerabilities*. The Linux Kernel documentation. Retrieved October 8, 2026, from https://docs.kernel.org/admin-guide/hw-vuln/index.html

The kernel development community. (n.d.-c). *Seccomp BPF (SECure COMPuting with filters)*. The Linux Kernel documentation. Retrieved October 8, 2026, from https://docs.kernel.org/userspace-api/seccomp_filter.html

Thomas, G. (2019, July 16). *A proactive approach to more secure code*. Microsoft Security Response Center. https://www.microsoft.com/en-us/msrc/blog/2019/07/a-proactive-approach-to-more-secure-code

Trusted Computing Group. (n.d.). *TPM 2.0 Library*. Retrieved October 8, 2026, from https://trustedcomputinggroup.org/resource/tpm-library-specification/

Trusted Computing Group. (2023). *TCG PC Client Platform Firmware Profile specification* (Version 1.06, Revision 52). https://trustedcomputinggroup.org/wp-content/uploads/PC-Client-Platform-Firmware-Profile-Version-1.06-Revision-52_pub.pdf

UAPI Group. (n.d.). *Linux TPM PCR registry*. Retrieved October 8, 2026, from https://uapi-group.org/specifications/specs/linux_tpm_pcr_registry/

UEFI Forum. (2024). *Unified Extensible Firmware Interface (UEFI) specification* (Version 2.11). https://uefi.org/specs/UEFI/2.11/

Vander Stoep, J., & Rebert, A. (2024, September 25). *Eliminating memory safety vulnerabilities at the source*. Google Security Blog. https://security.googleblog.com/2024/09/eliminating-memory-safety-vulnerabilities-Android.html

Yarom, Y., & Falkner, K. (2014). FLUSH+RELOAD: A high resolution, low noise, L3 cache side-channel attack. In *Proceedings of the 23rd USENIX Security Symposium* (pp. 719–732). USENIX Association. https://www.usenix.org/conference/usenixsecurity14/technical-sessions/presentation/yarom

## Further reading

Kerrisk, M. (2010). *The Linux programming interface*. No Starch Press. (Chapters on process credentials, capabilities and secure privileged programs.)

The kernel development community. (n.d.). *Kernel self-protection*. The Linux Kernel documentation. https://docs.kernel.org/security/self-protection.html

