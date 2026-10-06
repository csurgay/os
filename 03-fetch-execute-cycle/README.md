# The Fetch-Execute Cycle

*Operating Systems lecture: the von Neumann machine, the instruction cycle and interrupts, with Linux (x86-64) examples*

Previous: [Quality, Commercial Aspects and the Enterprise Linux Ecosystem](../02-quality-and-enterprise-linux/). Next: [Interrupts](../04-interrupts/).

> **How to read this lecture.** Wherever a new abbreviation or concept appears, a box marked **Explained simply** follows. Click it to open a plain-language explanation. You can skip these boxes if you already know the terms.

## Learning objectives

The processor repeats a single cycle: it fetches an instruction, decodes it, executes it, then checks whether an interrupt has arrived. This lesson follows that cycle at register level on a simple teaching CPU, then shows the same mechanisms on a real x86-64 Linux system.

<details>
<summary><b>Explained simply:</b> processor (CPU), instruction, register, interrupt, x86-64, Linux</summary>

- **Processor, CPU** (Central Processing Unit): the chip that runs programs. It does one small step after another, billions of times per second.
- **Instruction:** one elementary step in the CPU's own language, for example "add 2 to this number" or "jump to address 900". A program is a long list of instructions.
- **Register:** a tiny, very fast storage cell inside the CPU that holds one number. A CPU has only a few dozen of them.
- **Interrupt:** a signal that makes the CPU pause its program for a moment to deal with something urgent, like a doorbell while you are reading. The next lecture is all about it.
- **Teaching CPU:** an imaginary, very simple processor invented for learning. Real processors work on the same principles, with many more details.
- **x86-64:** the processor family in most PCs and laptops (Intel and AMD), in its 64-bit version.
- **Linux:** a free operating system used on most servers, in Android phones and on many desktops. An **operating system** is the program that manages the computer and lets other programs run (others: Windows, macOS).

</details>

By the end, students will be able to:

- state the von Neumann principle and explain why it is efficient and why it is not secure;
- name the main CPU registers (PC, MAR, MBR, CIR, ACC, SR) and their roles;
- describe the fetch phase in register transfer notation;
- trace the execution of a short machine-code program step by step, on paper and in `gdb`;
- explain how jumps and interrupts change the order of execution, and why the operating system needs the timer interrupt;
- find these mechanisms on a running Linux system (`/proc/<pid>/maps`, `/proc/interrupts`, `vmstat`).

## The von Neumann principle

In the von Neumann architecture (Stallings, 2018), the program (code) and the data live in the same memory and reach the CPU over the same bus system. The machine has three main units, the CPU, the memory and I/O, connected by a shared bus.

A memory cell alone does not tell whether it holds an instruction or data. The same bit pattern is an instruction if the CPU reads it during the fetch phase, and data if it is read as an instruction's operand.

**Why is it efficient?**

- One memory and one bus are enough, so the hardware is simple.
- A program can be handled as data: it can be loaded, copied and compiled. Loaders, compilers, JIT engines and the operating system itself all rely on this.

<details>
<summary><b>Explained simply:</b> memory, bit, bit pattern, operand, bus, I/O, loader, compiler, JIT</summary>

- **Memory** (RAM): the computer's working storage, a very long row of numbered cells. Each cell's number is its **address**, like house numbers on a street.
- **Bit:** the smallest piece of information, a 0 or a 1. A **bit pattern** is a row of bits, for example 00010011.
- **Operand:** the thing an instruction works on. In "add 2", the operand is 2.
- **Bus:** a shared set of wires that connects the CPU, the memory and the devices, like a road all traffic must use.
- **I/O** (Input/Output): everything the computer exchanges with the outside world: keyboard, disk, network, screen.
- **Loader:** the part of the operating system that copies a program from the disk into memory so it can run.
- **Compiler:** a program that translates code written by people (for example in C) into instructions the CPU understands.
- **JIT** (Just-In-Time) compiler: a compiler that translates code while the program is already running. Web browsers use one to run JavaScript fast.

</details>

**Why is it not secure?**

- If an attacker can write data into memory and redirect control there, the CPU executes it as instructions (for example, in a buffer overflow).
- A faulty program can overwrite its own code or the code of another program.

**The defence: permission bits.** The operating system assigns permissions to regions (pages) of memory, and the CPU's memory management unit (MMU) checks them on every access:

| Bit | Meaning | Typical use | Shown by Linux as |
| --- | --- | --- | --- |
| RD | readable | code and data | `r` |
| WR | writable | data only | `w` |
| NE | not executable (No Execute, NX) | data, heap, stack | missing `x` |

Rule of thumb: a region is either writable or executable, never both at once. This policy is called **W^X** ("write xor execute"). A violation does not just get blocked: the CPU raises an exception (a page fault), and Linux delivers `SIGSEGV` to the process, the familiar "Segmentation fault".

<details>
<summary><b>Explained simply:</b> attacker, buffer overflow, page, permission, MMU, NX, heap, stack, exception, page fault, process, SIGSEGV, XOR</summary>

- **Buffer overflow:** a program writes more data into a storage area than fits, and the extra spills over into whatever lies next to it. An **attacker** (someone trying to break in) can use this to place their own instructions in memory.
- **Page:** memory is managed in fixed-size chunks called pages, usually 4096 bytes. Permissions are set per page.
- **Permission:** what may be done with a page: read it (r), write it (w), run it as instructions (x, execute).
- **MMU** (Memory Management Unit): the part of the CPU that translates the addresses a program uses into real memory addresses, and checks every access against the permissions, like a receptionist who knows which room everyone is really in and who may enter it.
- **NX** (No eXecute): the permission bit that says "this page holds data, never run it as instructions".
- **Heap and stack:** two memory areas every running program has. The **heap** holds data the program creates while running; the **stack** works like a stack of plates (last put on, first taken off) and holds temporary values.
- **Exception:** an interrupt caused by the current instruction itself, for example when it breaks a rule. A **page fault** is the exception raised when an instruction touches a page it may not use, or one that is not in memory right now.
- **Process:** a running program, together with its memory and its state.
- **SIGSEGV, "Segmentation fault":** the message Linux sends a program that broke a memory rule. Usually it ends the program.
- **XOR** (exclusive or): "one or the other, but not both". W^X means a page may be writable or executable, never both.

</details>

The shared bus also limits performance, because an instruction and data cannot travel at the same time (the von Neumann bottleneck). Modern CPUs soften this with separate instruction and data caches close to the core (a "modified Harvard" design), while main memory stays shared.

<details>
<summary><b>Explained simply:</b> bottleneck, cache, core, Harvard architecture</summary>

- **Bottleneck:** the narrowest point that slows everything down, like the neck of a bottle.
- **Cache:** a small, very fast memory close to the CPU that keeps copies of recently used data, so the CPU does not have to wait for the slower main memory. Like keeping the books you use most on your desk instead of in the library.
- **Core:** a modern processor chip contains several complete CPUs, called cores.
- **Harvard architecture:** a design with separate memories (and separate buses) for instructions and for data, named after the Harvard Mark I computer. "Modified Harvard" means separate only in the caches.

</details>

## Inside the CPU

The CPU is a set of registers, an arithmetic logic unit (ALU) and a control unit (CU). It touches memory through only two registers: it sends addresses through the MAR, and receives or sends data through the MBR.

![CPU registers, buses and memory](cpu-architecture.svg)

One input of the ALU is the ACC; the other is the instruction's operand (the low bits of the CIR) or a general-purpose register (REG). The result goes into the ACC, and its properties (sign, zero, overflow) go into the SR.

Not all of these registers are visible to the programmer. PC, ACC/REG and SR can be read and changed by instructions. MAR, MBR and CIR are internal: they exist so the hardware can carry out the cycle, and no instruction names them.

<details>
<summary><b>Explained simply:</b> ALU, CU, PC, MAR, MBR, CIR, ACC, SR, REG</summary>

- **ALU** (Arithmetic Logic Unit): the CPU's calculator. It adds, subtracts, compares and does logical operations.
- **CU** (Control Unit): the CPU's conductor. It sends the signals that make every other part do the right thing at the right time.
- **PC** (Program Counter): holds the address of the next instruction, the CPU's bookmark.
- **MAR** (Memory Address Register): holds the address the CPU wants to read or write, the "which house?" register.
- **MBR** (Memory Buffer Register): holds the data just read from memory or about to be written, the "what's in the parcel?" register.
- **CIR** (Current Instruction Register): holds the instruction being carried out right now.
- **ACC** (Accumulator): the register where results of calculations are collected.
- **SR** (Status Register): a set of yes/no bits (flags) describing the last result, for example "it was zero".
- **REG** (general-purpose registers): extra registers the program can use for anything.

</details>

## The bus system

The CPU and memory communicate over three buses and a clock line. A memory read uses all three: the address goes out on the address bus, the control bus signals that this is a read, and the data comes back on the data bus.

| Bus | Direction | Carries | Example during fetch |
| --- | --- | --- | --- |
| Address bus (ADDR) | CPU → memory | the contents of the MAR, i.e. the cell address | 0, then 1 |
| Data bus (DATA) | bidirectional | the cell contents towards the MBR (the other way when writing) | 19, then 34 |
| Control bus (CTRL) | CPU → memory | CS (chip select: which device responds), R/W (read or write) | CS active, R/W = read |
| Clock (CLK) | everywhere | the timing every step follows | each register transfer on a clock tick |

I/O devices connect to the same bus system. The CS signal decides whether the memory or an I/O device responds to a given address. When a device answers to ordinary memory addresses, this is called **memory-mapped I/O**; on Linux, `/proc/iomem` lists which physical address ranges belong to RAM and which to devices.

<details>
<summary><b>Explained simply:</b> address bus, data bus, control bus, chip select, read/write, clock, RAM, memory-mapped I/O</summary>

- **Address bus:** the wires that carry *where* (which memory cell). **Data bus:** the wires that carry *what* (the number itself). **Control bus:** the wires that carry *how* (read or write, which chip should answer).
- **CS** (Chip Select): a signal that wakes up one specific chip and tells the others to ignore the bus.
- **R/W** (Read/Write): a signal that says whether the CPU wants to read or to write.
- **Clock** (CLK): a signal that ticks at a steady rate, billions of times per second. Every step happens on a tick, like rowers following the drum.
- **Bidirectional:** works in both directions.
- **RAM** (Random Access Memory): the main memory.
- **I/O** (Input/Output): everything the computer exchanges with the outside world: keyboard, disk, network, screen.
- **Memory-mapped I/O:** a device pretends to be a piece of memory. Writing to "its" address sends data to the device instead of to RAM.
- **Physical address:** the real address of a cell in the memory chips (programs normally see different, translated addresses).

</details>

## The instruction cycle

The CPU repeats a single cycle: Fetch, Decode, Execute, then Check Interrupt.

![Instruction cycle: Fetch, Decode, Execute, Check Interrupt](instruction-cycle.svg)

- **Fetch:** the instruction the PC points to is loaded into the CIR, and the PC is advanced.
- **Decode:** the decoder splits the opcode from the operand and sets the control signals.
- **Execute:** the ALU performs the operation, or for a jump the PC gets a new value.
- **Check Interrupt:** if no interrupt is pending, the next fetch follows; if one is, control passes to the interrupt handler.

<details>
<summary><b>Explained simply:</b> fetch, decode, execute, opcode, decoder, control signals, pending, interrupt handler</summary>

- **Fetch:** bring the next instruction from memory into the CPU. **Decode:** work out what it means. **Execute:** do it.
- **Opcode** (operation code): the part of an instruction that says *what* to do (add, load, jump). The rest is the operand: *with what*.
- **Decoder:** the circuit that reads the opcode and turns it into control signals.
- **Control signals:** the CPU's internal "switch on now" commands, for example "ALU, add!" or "memory, read!".
- **Pending:** waiting to be dealt with.
- **Interrupt handler:** the piece of operating system code that runs when an interrupt arrives.

</details>

## The fetch phase step by step

The fetch consists of four register transfer steps. `X ← Y` means X takes the value Y, `[R]` denotes the contents of register R, and `Mem[A]` denotes the contents of the memory cell at address A.

```
MAR ← [PC]
PC  ← [PC] + 1
MBR ← Mem[MAR]
CIR ← [MBR]
```

1. **MAR ← [PC]**: the address of the next instruction goes into the memory address register, and from there onto the address bus.
2. **PC ← [PC] + 1**: the program counter already points to the next instruction. In our teaching CPU every instruction is one memory word, hence +1. On a real CPU the PC advances by the instruction's length, which on x86-64 varies from 1 to 15 bytes.
3. **MBR ← Mem[MAR]**: the memory sends the requested cell over the data bus into the memory buffer register.
4. **CIR ← [MBR]**: the instruction goes into the current instruction register, where the decoder reads it.

The PC is advanced during the fetch, not after execution. This way a jump instruction has nothing to undo: during execute it simply overwrites the PC, and the next fetch reads from the new address.

<details>
<summary><b>Explained simply:</b> register transfer notation, memory word, byte, bracket notation</summary>

- **Register transfer notation:** a short way of writing what moves where inside the CPU. `MAR ← [PC]` reads: "copy the contents of PC into MAR".
- **`[PC]`:** the square brackets mean "the value stored in". `Mem[MAR]` means "the memory cell whose address is in MAR".
- **Memory word:** one memory cell of the machine's natural size. In our teaching CPU a word is 8 bits.
- **Byte:** 8 bits, enough to store one letter of text.

</details>

## Worked example: LD 3, ADD 2

At the end of this two-instruction program the accumulator holds 5: LD 3 loads 3, ADD 2 adds 2.

**Instruction format.** An instruction is 8 bits wide: the upper 4 bits are the opcode (what to do), the lower 4 bits are the operand.

| Opcode | Mnemonic | Effect |
| --- | --- | --- |
| 0001 | LD n | ACC ← n |
| 0010 | ADD n | ACC ← [ACC] + n |

**Memory contents before the run:**

| Address | Contents | Binary | Decimal |
| --- | --- | --- | --- |
| 0 | LD 3 | 0001 0011 | 19 |
| 1 | ADD 2 | 0010 0010 | 34 |
| 2 | (empty) | | |
| 3 | 7 (data) | 0000 0111 | 7 |

Memory stores only numbers. The 19 at address 0 is LD 3 because the CPU fetches it as an instruction. The 7 at address 3 is data, but if the PC pointed there, the CPU would try to interpret it as an instruction too. This is the von Neumann principle in practice.

**Tracing the run** (each row shows the state after the step):

| Step | PC | MAR | MBR | CIR (opcode / operand) | ACC |
| --- | --- | --- | --- | --- | --- |
| Start | 0 | – | – | – | – |
| 1st fetch | 1 | 0 | 19 | 0001 / 0011 | – |
| 1st decode | 1 | 0 | 19 | LD, 3 | – |
| 1st execute | 1 | 0 | 19 | LD, 3 | 3 |
| 2nd fetch | 2 | 1 | 34 | 0010 / 0010 | 3 |
| 2nd decode | 2 | 1 | 34 | ADD, 2 | 3 |
| 2nd execute | 2 | 1 | 34 | ADD, 2 | 5 |

When ADD executes, one ALU input is the ACC and the other is the operand field of the CIR. The result goes back into the ACC, while the decoder tells the ALU to add.

**Addressing modes.** Here the operand of LD 3 is the value itself (an *immediate* operand), so ACC ← 3. If LD used direct (absolute) addressing, 3 would be a memory address, and ACC ← Mem[3] = 7. The same bit pattern therefore means different things depending on the addressing mode, and the opcode determines the addressing mode.

<details>
<summary><b>Explained simply:</b> mnemonic, binary, decimal, accumulator, trace, immediate operand, direct addressing, addressing mode</summary>

- **Mnemonic:** a short, memorable name for an opcode, such as LD (load) or ADD. People write mnemonics; the machine stores numbers.
- **Binary:** writing numbers with only 0 and 1 (base 2). 0001 0011 in binary is 19 in **decimal**, our everyday base-10 numbers.
- **Trace:** following a program step by step and writing down every register's value after each step.
- **Immediate operand:** the number in the instruction is the value itself. "LD 3" means "load the number 3".
- **Direct addressing:** the number in the instruction is an address. "LD 3" would then mean "load whatever is stored in memory cell 3".
- **Addressing mode:** the rule that says how to interpret the operand: as a value, as an address, or in some other way.

</details>

## Control transfer and flags

A jump instruction changes the order of execution by overwriting the PC. A conditional jump decides based on the ALU's flags.

**Flags.** After every ALU operation, the properties of the result are stored in the status register (SR):

| Flag | Set to 1 when | x86-64 equivalent |
| --- | --- | --- |
| SN (sign) | the result is negative | SF |
| Z (zero) | the result is zero | ZF |
| NZ (not zero) | the result is not zero | no separate bit: "ZF = 0" |
| OF (overflow) | the signed result does not fit in the register | OF |

Real processors store only Z; "not zero" is simply the condition Z = 0, tested by a different jump instruction (on x86-64: `jz` and `jnz`). They also keep further flags, such as carry (CF), which is the unsigned counterpart of OF.

**Unconditional jump: JMP 1000.** During execute, PC ← 1000. The next fetch takes the instruction from address 1000.

**Conditional jump: JMZ 900** (jump if zero). The execute phase checks the Z flag:

- **yes** (Z = 1, the previous result was zero): PC ← 900, and the program continues at address 900;
- **no** (Z = 0): the PC does not change. Since the fetch already advanced it, the program continues with the instruction after JMZ.

Loops and branches (`if`, `while`, `for`) are all implemented with conditional jumps like this at machine level.

<details>
<summary><b>Explained simply:</b> flag, signed, unsigned, overflow, carry, jump, conditional jump, loop, branch</summary>

- **Flag:** a single yes/no bit in the status register, set by the last calculation (was it zero? negative? too big?).
- **Signed / unsigned numbers:** signed numbers can be negative (−128 … 127 in 8 bits); unsigned ones cannot (0 … 255 in 8 bits).
- **Overflow (OF):** a signed result does not fit, so it comes out with the wrong sign: in 8 bits, 127 + 1 gives −128.
- **Carry (CF):** an unsigned result does not fit, and a digit "falls off" the end, like a car odometer rolling over from 999999 to 000000.
- **Jump:** an instruction that changes the PC, so the program continues somewhere else instead of with the next instruction.
- **Conditional jump:** jump only if a condition holds (for example "if the result was zero"). This is how computers make decisions.
- **Loop, branch:** a loop repeats steps (`while`, `for`); a branch chooses between two paths (`if`). In C and most languages, these keywords become conditional jumps.

</details>

## Interrupts

An interrupt signals an external event, and the CPU only takes it into account at the end of the cycle, in the Check Interrupt step. This way an instruction is never interrupted halfway through. Real x86-64 CPUs follow the same rule: hardware interrupts are recognised at instruction boundaries. (Exceptions caused by the instruction itself, such as page faults, arise while the instruction is being fetched or executed; the [Interrupts](../04-interrupts/) lecture explains how they are handled.)

The sequence:

1. A device, for example the hardware **timer**, activates the interrupt request line (**IR**).
2. The request is recorded as pending (in our teaching CPU, as a bit in the SR).
3. The CPU finishes the current instruction.
4. In the Check Interrupt step it detects the pending request. It saves the PC and SR, switches to privileged (kernel) mode, and loads the address of the interrupt handler into the PC.
5. The handler runs (this is operating system code), then restores the saved PC and SR, and the program continues where it left off.

If no request is pending, the cycle simply restarts with the next fetch.

**Masking.** The CPU can be told to ignore interrupts for a short time. On x86-64 this is the IF (interrupt enable) flag in RFLAGS; the kernel clears it while it must not be disturbed. In the `gdb` trace later in this lesson, `[ IF ]` shows that interrupts are enabled in a normal user program.

**Interrupts, exceptions and system calls use the same mechanism.** An *interrupt* comes from outside (timer, disk, network card). An *exception* is caused by the current instruction itself, for example a page fault when it touches memory it may not use. A *system call* is a deliberate jump into the kernel (the `syscall` instruction on x86-64). In all three cases the CPU saves its state and the PC is set to a kernel handler.

**Why does this matter to the operating system?** The timer interrupt guarantees that the OS regularly regains control, even if a program gets stuck in an infinite loop. Time sharing and preemptive scheduling are built on this: in the interrupt handler, the OS decides which process runs next (Silberschatz et al., 2018).

<details>
<summary><b>Explained simply:</b> timer, IR, kernel mode, masking, RFLAGS, IF, system call, time sharing, preemptive scheduling, infinite loop</summary>

- **Timer:** a hardware clock that can send an interrupt at regular intervals.
- **IR** (Interrupt Request): the signal a device sends to ask for an interrupt, like raising your hand.
- **Kernel mode** (privileged mode): the CPU mode in which everything is allowed. Only the operating system's core, the **kernel**, runs in it; ordinary programs run in the restricted user mode.
- **Masking:** telling the CPU to ignore interrupts for a while, like "do not disturb" on a phone. The requests wait; they are not lost.
- **RFLAGS, IF:** RFLAGS is the x86-64 status register; IF (Interrupt enable Flag) is the bit in it that switches ordinary interrupts on or off.
- **System call:** a program's request to the operating system to do something it may not do itself, for example "read this file".
- **Time sharing:** giving each program short turns on the CPU in rotation, so they all seem to run at once.
- **Preemptive scheduling:** the OS may take the CPU away from a program at any moment to give another program a turn. Without it, a program would have to give the CPU back voluntarily.
- **Infinite loop:** a program that repeats the same steps forever and never finishes.

</details>

## The same ideas on Linux (x86-64)

Everything above is a simplified model. This section shows where each idea appears on a real x86-64 Linux machine. All outputs below come from a real system (kernel 6.18); addresses and counts will differ on yours.

<details>
<summary><b>Explained simply:</b> kernel, kernel version, real system</summary>

- **Kernel:** the core of the operating system, the part with full control over the hardware. "Kernel 6.18" is the version number of Linux's kernel.
- In the examples, lines starting with `$` are commands you type into a terminal; the other lines are the computer's answer.

</details>

### From the teaching CPU to x86-64

| Teaching CPU | x86-64 | Visible to programs? |
| --- | --- | --- |
| PC | RIP (instruction pointer) | yes, indirectly (jumps, calls) |
| ACC, REG | 16 general-purpose registers (RAX, RBX, …, R15) | yes |
| SR | RFLAGS (SF, ZF, OF, CF, IF, …) | yes |
| MAR, MBR, CIR | internal parts of the CPU's front end and memory pipeline | no |
| 8-bit instruction, 4-bit opcode | 1 to 15 bytes per instruction | yes (`objdump`) |
| LD n, ADD n | `mov $n, %eax`, `add $n, %eax` | yes |
| JMP, JMZ | `jmp`, `jz` (also written `je`) | yes |
| RD / WR / NE bits | page table bits, NX supported by the CPU (`nx` in `/proc/cpuinfo`) | via `/proc/<pid>/maps` |
| Timer → IR | local APIC timer → "Local timer interrupts" | via `/proc/interrupts` |

<details>
<summary><b>Explained simply:</b> RIP, RAX, RFLAGS, pipeline, page table, PID, /proc, local APIC</summary>

- **RIP, RAX, RFLAGS:** the x86-64 names for the program counter (Instruction Pointer), the first general-purpose register, and the status register.
- **Front end, pipeline:** a real CPU works on several instructions at once, like an assembly line where each station does one step. The front end is the part that fetches and decodes.
- **Page table:** the list the operating system keeps for each program, saying which pages of memory it may use, where they really are in memory, and with what permissions.
- **PID** (process ID): the number Linux gives each running program. `/proc/<pid>/maps` means "the maps file of the program with that number".
- **`/proc`:** a folder in Linux that does not exist on any disk. Its "files" are windows into the kernel, showing live information. `/proc/cpuinfo` describes the processor.
- **Local APIC** (Advanced Programmable Interrupt Controller): a small interrupt controller built into each CPU core; it also contains the core's timer.

</details>

### The example program in x86-64 assembly

The same program, LD 3 then ADD 2, with a conditional jump added. The result becomes the process exit code, so the shell can show it. (AT&T syntax, as used by the GNU tools.)

```asm
    .globl _start
    .text
_start:
    mov  $3, %eax        # LD 3   (immediate operand)
    add  $2, %eax        # ADD 2
    jz   done            # JMZ: jump if ZF = 1
    mov  %eax, %edi      # exit code = result
done:
    mov  $60, %eax       # system call number 60 = exit
    syscall              # enter the kernel
```

```console
$ as ldadd.s -o ldadd.o && ld ldadd.o -o ldadd
$ ./ldadd; echo $?
5
```

`objdump -d ldadd` shows the machine code. Just as in our memory table, the program is only a sequence of numbers in memory:

```console
0000000000401000 <_start>:
  401000:  b8 03 00 00 00     mov    $0x3,%eax
  401005:  83 c0 02           add    $0x2,%eax
  401008:  74 02              je     40100c <done>
  40100a:  89 c7              mov    %eax,%edi

000000000040100c <done>:
  40100c:  b8 3c 00 00 00     mov    $0x3c,%eax
  401011:  0f 05              syscall
```

Note the different instruction lengths (5, 3, 2 and 2 bytes): the "+1" of our fetch phase becomes "+ length of this instruction".

<details>
<summary><b>Explained simply:</b> assembly language, AT&T syntax, GNU, as, ld, exit code, shell, objdump, hexadecimal, EAX, EDI</summary>

- **Assembly language:** instructions written as readable mnemonics (`mov`, `add`) instead of numbers. Each line becomes one machine instruction.
- **AT&T syntax:** one of two common ways of writing x86 assembly; it puts the source first and the destination second (`mov $3, %eax` = "move 3 into EAX").
- **GNU tools, `as`, `ld`:** GNU is a large free-software project whose tools (compiler, assembler, linker) Linux systems use. `as` (assembler) turns assembly into machine code; `ld` (linker) turns that into a runnable program.
- **Exit code:** a number a program gives back when it ends. `echo $?` prints it. By convention 0 means "everything was fine".
- **Shell:** the program that reads the commands you type in the terminal and runs them.
- **`objdump -d`:** a tool that shows the machine instructions inside a program (disassembly).
- **Hexadecimal** (`0x…`): writing numbers in base 16, with digits 0–9 and a–f. `0x3c` = 60. Programmers like it because one hex digit is exactly 4 bits.
- **EAX, EDI:** the lower 32-bit halves of the 64-bit registers RAX and RDI. For the `exit` system call, RDI carries the exit code.
- **`syscall`:** the x86-64 instruction a program uses to call the operating system. Here it asks the kernel to end the program (system call number 60, "exit").

</details>

### Tracing it in gdb

`gdb` can execute one instruction at a time (`stepi`), so we can repeat the paper trace on the real CPU:

```console
$ gdb -q ./ldadd
(gdb) starti
(gdb) info registers rip rax eflags
(gdb) stepi
...
```

| After | RIP (PC) | RAX (ACC) | EFLAGS |
| --- | --- | --- | --- |
| start | 0x401000 | 0 | `[ IF ]` |
| `mov $3, %eax` | 0x401005 | 3 | `[ IF ]` |
| `add $2, %eax` | 0x401008 | 5 | `[ PF IF ]` |
| `je done` (not taken) | 0x40100a | 5 | `[ PF IF ]` |

The result is 5, not zero, so ZF stays 0 and the jump is not taken: RIP simply moves on to the next instruction, exactly like the "no" branch of JMZ. (PF is the parity flag: the low byte of the result, 5 = 101₂, has an even number of 1 bits.)

<details>
<summary><b>Explained simply:</b> debugger, gdb, starti, stepi, EFLAGS, PF, 101₂</summary>

- **Debugger, `gdb`:** a tool that runs a program under supervision, so you can stop it, look inside, and run it one instruction at a time.
- **`starti`, `stepi`:** gdb commands: start the program and stop before its first instruction; execute exactly one instruction.
- **EFLAGS:** the 32-bit part of RFLAGS, the status register. gdb lists the flags that are 1.
- **PF** (Parity Flag): 1 if the lowest byte of the result has an even number of 1 bits.
- **101₂:** the small ₂ means "in binary": 101 in binary is 5.

</details>

### Addressing modes: one character makes the difference

In AT&T syntax, `$` marks an immediate operand. Without it, the number is a memory address:

| Instruction | Machine code | Meaning |
| --- | --- | --- |
| `mov $3, %eax` | `b8 03 00 00 00` | EAX ← 3 (immediate, like our LD 3) |
| `mov 3, %eax` | `8b 04 25 03 00 00 00` | EAX ← Mem[3] (direct addressing) |

The direct version assembles without complaint, but it crashes:

```console
$ ./direct
Segmentation fault
```

Address 3 is not mapped into the process, so the MMU raises a page fault, and the kernel kills the process with `SIGSEGV`. This is the crossed-out arrow from our worked example, made real: the same "3" means a value in one addressing mode and an address in the other.

<details>
<summary><b>Explained simply:</b> mapped, kernel kills the process</summary>

- **Mapped:** a memory address is mapped if the program has been given a page there. Low addresses such as 3 are deliberately never mapped, so that mistakes like this are caught.
- **The kernel kills the process:** the operating system ends the program. A **process** is a running program.

</details>

### Memory permissions in a real process

Every process can see its own memory map in `/proc/self/maps`. An excerpt for `cat /proc/self/maps`:

```console
56520cec6000-56520cec8000 r--p 00000000 fe:00 343944   /usr/bin/cat
56520cec8000-56520cecd000 r-xp 00002000 fe:00 343944   /usr/bin/cat
56520cecd000-56520cecf000 r--p 00007000 fe:00 343944   /usr/bin/cat
56520ced0000-56520ced1000 rw-p 00009000 fe:00 343944   /usr/bin/cat
565230d03000-565230d24000 rw-p 00000000 00:00 0        [heap]
...
7fff65453000-7fff65479000 rw-p 00000000 00:00 0        [stack]
```

The code (`r-x`) is readable and executable but not writable. The data, the heap and the stack (`rw-`) are writable but not executable. No region is `rwx`: this is W^X in practice.

The executable file itself asks for a non-executable stack. `readelf -lW /bin/ls` prints, among others:

```console
  GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RW  0x10
```

`RW` with no `E`: the stack may be read and written, but not executed.

<details>
<summary><b>Explained simply:</b> /proc/self/maps, columns, readelf, ELF</summary>

- **`/proc/self/maps`:** a list of all the memory areas of the program that reads it ("self"), one per line: start and end address, permissions, and what is stored there.
- **`r-xp`:** the permission column: r = read, w = write, x = execute, `-` = not allowed; the final `p` means private: if the program writes there, it gets its own copy, and the change is not seen by other programs or written back to the file.
- **`readelf`:** a tool that shows the inside of a Linux program file. **ELF** (Executable and Linkable Format) is the file format of Linux programs, like `.exe` on Windows.

</details>

**Experiment: executing data.** This C program holds six bytes of machine code (`mov $5, %eax; ret`) in an array on the stack and tries to call it:

```c
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(int argc, char **argv) {
    /* x86-64 machine code for:  mov $5, %eax ; ret */
    unsigned char code[] = { 0xb8, 0x05, 0x00, 0x00, 0x00, 0xc3 };

    if (argc > 1) {   /* "./nx fix": copy to a page, then make it executable */
        long pg = sysconf(_SC_PAGESIZE);
        unsigned char *p = mmap(NULL, pg, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        memcpy(p, code, sizeof code);
        mprotect(p, pg, PROT_READ | PROT_EXEC);   /* W^X: drop write, add exec */
        printf("result = %d\n", ((int (*)(void))p)());
    } else {          /* "./nx": run the bytes where they are, on the stack */
        printf("result = %d\n", ((int (*)(void))code)());
    }
    return 0;
}
```

```console
$ gcc -o nx nx.c
$ ./nx
Segmentation fault
$ ./nx fix
result = 5
```

The bytes are identical in both cases. On the stack they are data, and the NX bit stops the CPU from fetching them as instructions. After `mprotect` switches the page from writable to executable, the very same bytes run. This is how JIT compilers (for example in web browsers) legitimately turn generated data into code.

<details>
<summary><b>Explained simply:</b> array, function pointer, mmap, mprotect, page size</summary>

- **Array:** a numbered row of values stored next to each other in memory. Here it holds six bytes of machine code.
- **Calling a function pointer:** in C you can tell the CPU "jump to this address and run what is there". That is how the program tries to run its array.
- **`mmap`:** asks the operating system for a fresh piece of memory (whole pages).
- **`mprotect`:** asks the operating system to change the permissions of some pages, here from "writable" to "executable".
- **Page size:** the size of one page, usually 4096 bytes; `sysconf(_SC_PAGESIZE)` asks the system for it.

</details>

### Interrupts on a running system

`/proc/interrupts` counts interrupts per CPU core since boot:

```console
$ grep -E 'LOC|RES' /proc/interrupts
LOC:      17996      16921   Local timer interrupts
RES:       1567       1431   Rescheduling interrupts
```

- **LOC** is the timer interrupt from our diagram: each core has its own local timer.
- **RES** are interrupts one core sends to another to ask it to reschedule.

How often does the timer fire? The kernel's tick rate is a build option, `CONFIG_HZ`. On this system it is 250 (250 ticks per second, one every 4 ms); common values are 100, 250, 300 and 1000. Modern kernels also stop the tick on idle cores to save power ("tickless" operation), which is why the counters grow more slowly than 250 per second on an idle machine.

`vmstat 1` shows the rates live. The `in` column is interrupts per second, `cs` is context switches per second:

```console
$ vmstat 1
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 0  0      0 7319044  18932 620260    0    0     0     0  239  191  9  0 91  0  1  0
```

Each context switch happens inside the kernel, reached through an interrupt or a system call. When the timer interrupt arrives, the Linux scheduler (EEVDF, the default since kernel 6.6) checks whether the running task has used up its fair share of CPU time, and if so, switches to another one.

<details>
<summary><b>Explained simply:</b> grep, tick, CONFIG_HZ, tickless, vmstat, context switch, scheduler, EEVDF</summary>

- **`grep`:** a command that prints only the lines of a file that match a pattern.
- **Tick:** one regular timer interrupt. **`CONFIG_HZ`** is how many ticks per second the kernel was built for (Hz = per second).
- **Tickless:** an idle core switches off its regular tick to save power, and wakes only when there is something to do.
- **`vmstat 1`:** a command that prints a line of system statistics every second.
- **Context switch:** the CPU stops running one program and starts running another: it saves the first one's registers and loads the second one's. Like bookmarking one book and opening another.
- **Scheduler:** the part of the OS that decides which program gets the CPU next.
- **EEVDF** (Earliest Eligible Virtual Deadline First): the name of the method Linux's scheduler uses since version 6.6 to share CPU time fairly.

</details>

## Lab exercises

1. **Your process's memory.** Run `cat /proc/self/maps`. Find the code, the heap and the stack. Which regions are writable, which are executable? Is there any `rwx` region?
2. **Machine code.** Assemble and run `ldadd.s`. Check the exit code with `echo $?`. Change the program so that the result is 0 (for example, `add $-3, %eax`). What is the exit code now, and why? (Hint: which branch does `jz` take, and what is in EDI when the program starts?)
3. **Single stepping.** Trace `ldadd` in `gdb` with `starti`, `stepi` and `info registers rip rax eflags`. Fill in the trace table yourself, then repeat it for the modified version from exercise 2. When does ZF appear in EFLAGS?
4. **Addressing modes.** Remove the `$` from `mov $3, %eax`, assemble and run it. Explain the result using the words *direct addressing*, *page fault* and *SIGSEGV*.
5. **NX.** Compile and run `nx.c` both ways. Then look at `/proc/<pid>/maps` of a running copy (add a `sleep(60)` before the call) and find the stack's permissions.
6. **The timer.** Run `grep LOC /proc/interrupts` twice, 10 seconds apart. Roughly how many timer interrupts arrived per second on each core? Compare this with `CONFIG_HZ` (`grep CONFIG_HZ= /boot/config-$(uname -r)`). Then start a busy loop (`yes > /dev/null`) and measure again.

## Review questions

1. Address 0 in memory holds 19. Is it an instruction or data? What does the answer depend on?
2. Why is the PC advanced during the fetch phase rather than at the end of execution?
3. What would the ACC hold after the first instruction if LD used direct addressing?
4. JMZ 900 is at address 20. What will the PC be after it executes if the previous result was 0, and what if it was 5?
5. Why is the PC not connected directly to the address bus? What is the role of the MAR?
6. Why does the CPU check for interrupts only at the end of the cycle?
7. Why could preemptive scheduling not work without a timer interrupt?
8. What does the NE (NX) bit prevent, and what can it not prevent?
9. On x86-64 the instruction at 0x401005 is 3 bytes long. What will RIP be after it is fetched? Why can a real CPU not simply use "PC + 1"?
10. `mov $3, %eax` and `mov 3, %eax` differ by one character. Why does only the second one crash?
11. In `/proc/self/maps`, the heap is `rw-p`. What would happen if a program jumped into its heap? Which Linux mechanism reports the error to the program?
12. What do a timer interrupt, a page fault and a `syscall` instruction have in common at CPU level, and how do they differ?

<details>
<summary><strong>Answer key (for instructors)</strong></summary>

1. Neither on its own. It is an instruction because the CPU fetches it based on the PC. If it were read as an operand, it would be data.
2. This way a jump can simply overwrite the PC, and after a non-jump instruction the PC already points to the correct next address.
3. 7, because ACC ← Mem[3].
4. If the result was 0, the Z flag is 1, so PC = 900. If it was 5, PC = 21, because the fetch already advanced it.
5. The MAR holds the address steady on the bus for the whole memory operation, while the PC already moves on to the next address. Data accesses also send their address out through the MAR, not the PC.
6. This makes every instruction atomic: an external interrupt never leaves a half-finished register state, and the saved PC unambiguously points to the next instruction. (Exceptions such as page faults are different: the faulting instruction is abandoned and later re-executed.)
7. A program that never gives up control voluntarily (for example, one in an infinite loop) would never let the OS run.
8. It prevents the CPU from executing code written into a data region (for example, the stack). It does not prevent an attacker from chaining together existing executable code fragments (for example, return-oriented programming).
9. 0x401008. x86-64 instructions have variable length (1 to 15 bytes), so the CPU must decode at least the start of the instruction to know how far to advance.
10. With `$`, 3 is an immediate value placed in the register. Without it, 3 is a memory address; address 3 is not mapped in the process, so the access causes a page fault and the kernel sends SIGSEGV.
11. The heap has no `x` permission, so the instruction fetch from it causes a page fault (an NX violation). The kernel turns it into a SIGSEGV signal, which by default terminates the program ("Segmentation fault").
12. In all three the CPU saves its state, switches to kernel mode and continues at a kernel handler. They differ in their source: the timer interrupt comes from outside and is asynchronous, the page fault is an exception caused by the current instruction, and `syscall` is a deliberate request made by the program.

</details>

## References

Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating system concepts* (10th ed.). Wiley.

Stallings, W. (2018). *Operating systems: Internals and design principles* (9th ed.). Pearson.

## Further reading

Kóczy, A., & Kondorosi, K. (Eds.). (2000). *Operációs rendszerek mérnöki megközelítésben* [Operating systems: An engineering approach]. Panem.

Tanenbaum, A. S., & Bos, H. (2015). *Modern operating systems* (4th ed.). Pearson.
