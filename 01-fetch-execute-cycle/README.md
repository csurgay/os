# The Fetch-Execute Cycle

*Operating Systems lecture: the von Neumann machine, the instruction cycle and interrupts, with Linux (x86-64) examples*

Next: [Interrupts](../02-interrupts/).

## Learning objectives

The processor repeats a single cycle: it fetches an instruction, decodes it, executes it, then checks whether an interrupt has arrived. This lesson follows that cycle at register level on a simple teaching CPU, then shows the same mechanisms on a real x86-64 Linux system.

By the end, students will be able to:

- state the von Neumann principle and explain why it is efficient and why it is not secure;
- name the main CPU registers (PC, MAR, MBR, CIR, ACC, SR) and their roles;
- describe the fetch phase in register transfer notation;
- trace the execution of a short machine-code program step by step, on paper and in `gdb`;
- explain how jumps and interrupts change the order of execution, and why the operating system needs the timer interrupt;
- find these mechanisms on a running Linux system (`/proc/<pid>/maps`, `/proc/interrupts`, `vmstat`).

## The von Neumann principle

In the von Neumann architecture, the program (code) and the data live in the same memory and reach the CPU over the same bus system. The machine has three main units, the CPU, the memory and I/O, connected by a shared bus.

A memory cell alone does not tell whether it holds an instruction or data. The same bit pattern is an instruction if the CPU reads it during the fetch phase, and data if it is read as an instruction's operand.

**Why is it efficient?**

- One memory and one bus are enough, so the hardware is simple.
- A program can be handled as data: it can be loaded, copied and compiled. Loaders, compilers, JIT engines and the operating system itself all rely on this.

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

The shared bus also limits performance, because an instruction and data cannot travel at the same time (the von Neumann bottleneck). Modern CPUs soften this with separate instruction and data caches close to the core (a "modified Harvard" design), while main memory stays shared.

## Inside the CPU

The CPU is a set of registers, an arithmetic logic unit (ALU) and a control unit (CU). It touches memory through only two registers: it sends addresses through the MAR, and receives or sends data through the MBR.

![CPU registers, buses and memory](cpu-architecture.svg)

One input of the ALU is the ACC; the other is the instruction's operand (the low bits of the CIR) or a general-purpose register (REG). The result goes into the ACC, and its properties (sign, zero, overflow) go into the SR.

Not all of these registers are visible to the programmer. PC, ACC/REG and SR can be read and changed by instructions. MAR, MBR and CIR are internal: they exist so the hardware can carry out the cycle, and no instruction names them.

## The bus system

The CPU and memory communicate over three buses and a clock line. A memory read uses all three: the address goes out on the address bus, the control bus signals that this is a read, and the data comes back on the data bus.

| Bus | Direction | Carries | Example during fetch |
| --- | --- | --- | --- |
| Address bus (ADDR) | CPU → memory | the contents of the MAR, i.e. the cell address | 0, then 1 |
| Data bus (DATA) | bidirectional | the cell contents towards the MBR (the other way when writing) | 19, then 34 |
| Control bus (CTRL) | CPU → memory | CS (chip select: which device responds), R/W (read or write) | CS active, R/W = read |
| Clock (CLK) | everywhere | the timing every step follows | each register transfer on a clock tick |

I/O devices connect to the same bus system. The CS signal decides whether the memory or an I/O device responds to a given address. When a device answers to ordinary memory addresses, this is called **memory-mapped I/O**; on Linux, `/proc/iomem` lists which physical address ranges belong to RAM and which to devices.

## The instruction cycle

The CPU repeats a single cycle: Fetch, Decode, Execute, then Check Interrupt.

![Instruction cycle: Fetch, Decode, Execute, Check Interrupt](instruction-cycle.svg)

- **Fetch:** the instruction the PC points to is loaded into the CIR, and the PC is advanced.
- **Decode:** the decoder splits the opcode from the operand and sets the control signals.
- **Execute:** the ALU performs the operation, or for a jump the PC gets a new value.
- **Check Interrupt:** if no interrupt is pending, the next fetch follows; if one is, control passes to the interrupt handler.

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

## Interrupts

An interrupt signals an external event, and the CPU only takes it into account at the end of the cycle, in the Check Interrupt step. This way an instruction is never interrupted halfway through. Real x86-64 CPUs follow the same rule: hardware interrupts are recognised at instruction boundaries.

The sequence:

1. A device, for example the hardware **timer**, activates the interrupt request line (**IR**).
2. The request is recorded as pending (in our teaching CPU, as a bit in the SR).
3. The CPU finishes the current instruction.
4. In the Check Interrupt step it detects the pending request. It saves the PC and SR, switches to privileged (kernel) mode, and loads the address of the interrupt handler into the PC.
5. The handler runs (this is operating system code), then restores the saved PC and SR, and the program continues where it left off.

If no request is pending, the cycle simply restarts with the next fetch.

**Masking.** The CPU can be told to ignore interrupts for a short time. On x86-64 this is the IF (interrupt enable) flag in RFLAGS; the kernel clears it while it must not be disturbed. In the `gdb` trace later in this lesson, `[ IF ]` shows that interrupts are enabled in a normal user program.

**Interrupts, exceptions and system calls use the same mechanism.** An *interrupt* comes from outside (timer, disk, network card). An *exception* is caused by the current instruction itself, for example a page fault when it touches memory it may not use. A *system call* is a deliberate jump into the kernel (the `syscall` instruction on x86-64). In all three cases the CPU saves its state and the PC is set to a kernel handler.

**Why does this matter to the operating system?** The timer interrupt guarantees that the OS regularly regains control, even if a program gets stuck in an infinite loop. Time sharing and preemptive scheduling are built on this: in the interrupt handler, the OS decides which process runs next.

## The same ideas on Linux (x86-64)

Everything above is a simplified model. This section shows where each idea appears on a real x86-64 Linux machine. All outputs below come from a real system (kernel 6.18); addresses and counts will differ on yours.

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
6. This makes every instruction atomic: an interrupt never leaves a half-finished register state, and the saved PC unambiguously points to the next instruction.
7. A program that never gives up control voluntarily (for example, one in an infinite loop) would never let the OS run.
8. It prevents the CPU from executing code written into a data region (for example, the stack). It does not prevent an attacker from chaining together existing executable code fragments (for example, return-oriented programming).
9. 0x401008. x86-64 instructions have variable length (1 to 15 bytes), so the CPU must decode at least the start of the instruction to know how far to advance.
10. With `$`, 3 is an immediate value placed in the register. Without it, 3 is a memory address; address 3 is not mapped in the process, so the access causes a page fault and the kernel sends SIGSEGV.
11. The heap has no `x` permission, so the instruction fetch from it causes a page fault (an NX violation). The kernel turns it into a SIGSEGV signal, which by default terminates the program ("Segmentation fault").
12. In all three the CPU saves its state, switches to kernel mode and continues at a kernel handler. They differ in their source: the timer interrupt comes from outside and is asynchronous, the page fault is an exception caused by the current instruction, and `syscall` is a deliberate request made by the program.

</details>
