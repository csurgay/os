# Processes, Threads and System Calls

*Operating Systems lecture: what a process is made of, how a program asks the kernel for service through system calls, how processes are created, replaced and collected (fork, exec, exit, wait, and their alternatives), how a shell uses them, what threads share and how they are mapped onto kernel threads, how processes communicate (pipes, signals, shared memory, message queues, sockets), and how to watch all of this on a running Linux system, with measurements*

## Learning objectives

The [interrupts lecture](../05-interrupts/) showed the hardware side of the story: the CPU runs ordinary programs in user mode and the kernel in kernel mode, and the only ways into the kernel are interrupts, exceptions and the system-call instruction ([User mode and kernel mode](../05-interrupts/#user-mode-and-kernel-mode)). The [next lecture](../07-concurrency-deadlocks-scheduling/) treats processes and threads as the units that share the CPU: their states, how they synchronise, and how the scheduler chooses between them. This lecture sits in between. It explains what a process actually consists of, how a program uses system calls to get work done by the kernel, how processes are born, change program, end and are collected, what a thread is, how processes exchange data, and how to look inside a running system.

<details>
<summary><b>Explained simply:</b> program, process, thread, system call, kernel</summary>

- **Program:** a file with instructions, like a recipe in a book. It does nothing by itself.
- **Process:** a program that is running, with its own memory and its own place in the computer's to-do list, like a cook actually following the recipe in a kitchen. One recipe can be cooked by several cooks at once.
- **Thread:** one line of work inside a process. Several threads of one process are like several cooks in the same kitchen, sharing the ingredients and the tools.
- **Kernel:** the central part of the operating system, which has full control of the hardware.
- **System call:** a request from a program to the kernel ("open this file", "start a new program"), like a customer handing an order to the staff behind the counter.

</details>

By the end, students will be able to:

- distinguish a program from a process, draw the address space of a process (text, data, BSS, heap, memory-mapped area, stack) and list what the kernel keeps about a process outside it;
- distinguish the library API from the system-call interface, explain how a libc wrapper, the x86-64 `syscall` instruction, the system-call number and table, the return value and `errno` work together, and explain what the vDSO is for;
- measure the cost of a system call and explain why it is far more expensive than a function call;
- use `fork`, the `exec` family, `exit` and `wait`/`waitpid`, decode an exit status, and explain copy-on-write, orphans, reparenting and subreapers;
- write a minimal shell with `fork`, `exec`, `wait`, `pipe` and `dup2`, and explain how redirection and pipelines work at the level of file descriptors;
- compare `fork`, `vfork`, `posix_spawn` and `clone`, and explain the criticism of `fork`;
- explain what the threads of a process share and what each owns, compare user-level and kernel-level threads (N:1, 1:1, M:N), and relate them to Linux tasks and `clone` flags, POSIX threads, thread-local storage, goroutines and Java virtual threads;
- describe pipes and FIFOs, signals (handlers, async-signal safety, interrupted system calls), shared memory, message queues and sockets, choose between them, and interpret measured latency and throughput;
- observe processes with `/proc`, `/sys`, `strace`, `gdb` and `ptree`-style tools, and explain what `ltrace`, `perf` and eBPF (`bpftrace`) add.

## Programs and processes

A **program** is a passive file: machine code and initial data in an executable format (ELF on Linux), stored on disk. A **process** is a program in execution: an active entity with its own memory, its own registers and its own entry in the kernel's tables (Silberschatz et al., 2018; Arpaci-Dusseau & Arpaci-Dusseau, 2023). The difference matters in both directions. One program can run as many processes at the same time (ten users running `bash`, a web server with many worker processes), each with its own memory and state. And one process can run several programs one after the other: a shell's child process starts as a copy of the shell and then replaces its program with `ls`.

Unix made the process the central abstraction from the start: "a process is the execution of an image", where the image is "the current state of a pseudo computer" (Ritchie & Thompson, 1974). The operating system gives each process the illusion of a machine of its own: a private memory, a CPU that seems to run only its instructions, and files and devices reached by name.

### What a process consists of

![A process: on the left its virtual address space from address 0 upwards: unmapped page 0, text, data, BSS, heap growing up, the memory-mapped area with libraries and large allocations, the stack growing down, and the kernel's part at the top; on the right the kernel's record of the process: identity, state, saved registers, memory map, open files, credentials, signals and environment](address-space.svg)

**The address space.** Each process sees its own virtual address space (how virtual addresses are mapped to physical memory is the subject of the [virtual memory lecture](../09-virtual-memory/)). On Linux it is laid out in regions:

- **Text:** the machine code of the program, mapped from the executable file, readable and executable but not writable, so that a bug cannot overwrite the code and several processes running the same program can share it.
- **Data:** global and static variables that have an initial value (`int initialised = 42;`), copied from the executable.
- **BSS:** global and static variables without an initial value, which C defines to start as zero. The executable only records their total size; the kernel provides zero-filled pages. (The name is historical, from an assembler directive "block started by symbol".)
- **Heap:** memory allocated at run time with `malloc` or `new`. It grows upwards; the C library extends it with the `brk` system call.
- **Memory-mapped area:** shared libraries (the C library, the dynamic loader), files mapped with `mmap`, large `malloc` blocks (glibc serves blocks of 128 KiB and more with a separate `mmap`), the stacks of additional threads, and the vDSO (below).
- **Stack:** local variables, function arguments and return addresses of the main thread. It grows downwards, by default up to 8 MiB.
- **The kernel's part:** the upper half of the 64-bit address space belongs to the kernel. It is mapped in every process, but protected: user-mode code cannot touch it. (On processors vulnerable to the Meltdown attack, Linux maps only a small entry area while user code runs.)

The [Linux section](#the-address-space-of-a-running-program) prints the address of one variable in each region and finds it in `/proc/self/maps`.

**Everything else.** A process is more than memory. The kernel keeps, in its own memory where the process cannot change it, a record of everything else it needs: the [next lecture](../07-concurrency-deadlocks-scheduling/#the-process-state-space) calls it the **process control block** (PCB); in Linux it is a `struct task_struct` (Love, 2010). It holds the process ID (PID) and the parent's PID; the state and scheduling information; the saved registers (program counter, stack pointer, flags) while the process is not running; the description of the address space (the list of regions and the page tables); the table of open files; the credentials (user and group IDs, capabilities, see the [access control lecture](../11-access-control/#users-groups-and-the-identity-of-a-process)); the signal handlers and the pending and blocked signals; and the environment: current directory, root directory, resource limits and namespaces. Each process also has its own **kernel stack**, used while the kernel works on its behalf.

**Open files.** A process refers to open files, pipes, sockets and devices by small integers, the **file descriptors**. Each descriptor is an index into the process's descriptor table, whose entry points to an **open file description** in the kernel (with the current offset and the access mode), which points to the object itself (an inode, a pipe, a socket) ([File systems: files and the storage stack](../10-file-systems/#files-and-the-storage-stack)). By convention, descriptor 0 is standard input, 1 standard output and 2 standard error. This three-level structure is what makes shell redirection and pipes possible, as the [life-cycle section](#how-a-shell-uses-them) shows.

<details>
<summary><b>Explained simply:</b> executable, ELF, image, address space, text, data, BSS, heap, stack, memory-mapped area, shared library, Meltdown, PCB, task_struct, PID, page table, credentials, capabilities, kernel stack, file descriptor, open file description, inode</summary>

- **Executable, ELF:** a file that contains a program ready to run. ELF (Executable and Linkable Format) is the format of such files on Linux.
- **Image:** the picture of a running program's memory and registers at one moment.
- **Address space:** the range of memory addresses a process can use, like the numbered pages of its own notebook. Each process has its own notebook.
- **Text:** the part of the notebook that holds the program's instructions; it is read-only.
- **Data, BSS:** global variables. Data holds those with a starting value; BSS holds those that start at zero, so the file only needs to say how many there are.
- **Heap:** memory a program asks for while it runs, for things whose size it does not know in advance.
- **Stack:** memory for the local variables of the functions currently running; it grows when a function is called and shrinks when it returns, like a stack of plates.
- **Memory-mapped area, shared library:** a part of the address space where files are made to look like memory. A shared library is a file of ready-made functions (such as `printf`) that many programs use, kept in memory only once.
- **Meltdown:** a flaw found in 2018 in many processors that let user programs read kernel memory through the side effects of the CPU's guesswork; the fix hides most of the kernel while user code runs.
- **PCB, task_struct:** the kernel's record card about one process. Linux calls it `task_struct`.
- **PID:** process identifier, the number of a process.
- **Page table:** the kernel's translation table for one process, which says where each page of the process's memory really lies in the computer's RAM.
- **Credentials, capabilities:** the user and group a process acts for, like the name on an ID card, which decides what it may do; capabilities are single administrator rights that can be given to a process one by one.
- **Kernel stack:** a small stack that the kernel uses when it works for a process, separate from the process's own stack.
- **File descriptor:** a small number a program uses for an open file, like a cloakroom ticket. **Open file description:** the kernel's note behind the ticket: which file, how it was opened, and how far it has been read.
- **Inode:** the file system's record card about one file (its size, owner, permissions and where its data lie), separate from its name.

</details>

## System calls: the doors into the kernel

A process in user mode can compute, but it cannot do anything that involves the outside world or other processes: it cannot read a disk block, send a network packet, create a process or even end itself. All of these need the kernel. A **system call** is a controlled request to the kernel: the process executes a special instruction that switches the CPU into kernel mode and jumps to an entry point that the kernel has registered, exactly like the trap mechanism of the [interrupts lecture](../05-interrupts/#user-mode-and-kernel-mode). The kernel checks the request, does the work and returns the result, and the CPU goes back to user mode.

### The API and the system-call interface

Programmers rarely issue system calls directly. They call functions of an **application programming interface** (API), such as the POSIX API or the C standard library, and the library makes the system calls. The two interfaces are different things:

- Many library functions are thin **wrappers**: `write()`, `read()`, `open()`, `fork()` and `getpid()` in glibc each put their arguments into the right registers and execute one system call.
- Some library functions make **no** system call at all (`strlen`, `memcpy`, `sqrt`), or only sometimes: `printf` and `fwrite` collect output in a buffer in user memory and call `write()` only when the buffer is full, at a newline on a terminal, or when the program exits; `malloc` calls `brk` or `mmap` only when its pool is exhausted.
- Some library functions make **several**: `fopen` makes an `openat` and may check the file with `fstat`; starting a dynamically linked program makes dozens of calls before `main` even begins (measured in the [strace section](#tracing-with-strace)).
- Conversely, a few system calls have no ordinary wrapper and are reached through the generic `syscall()` function, which takes the system-call number as its first argument.

Keeping the API separate from the system-call interface lets the library stay stable while the kernel interface evolves (glibc's `fork()` today makes a `clone` system call, not the old `fork` system call), and lets the same API be implemented on very different kernels: the POSIX API exists on Linux, the BSDs and macOS, and (through a compatibility layer) on Windows. The Linux system-call interface itself is very stable: Linux has the rule that a change in the kernel must never break existing user programs.

### The `syscall` instruction on x86-64

Each system call has a number. On x86-64 Linux, `read` is 0, `write` is 1, `getpid` is 39, `clone` is 56, `fork` is 57, `execve` is 59, `exit` 60, `wait4` 61 and `exit_group` 231; the C headers of the machine used here define 373 numbers, from 0 to 461 (the numbers 335 to 423 are unused, so that every system call added since then has the same number on all architectures). The calling convention is fixed by the kernel (Linux man-pages project, n.d.-f):

![The path of a system call: the program calls write(); the libc wrapper puts the number 1 into rax and executes syscall; the CPU switches to kernel mode and jumps to entry_SYSCALL_64, which saves the user registers; sys_call_table[rax] dispatches to ksys_write, then VFS and the driver; sysret returns with the result in rax; clock_gettime goes to the vDSO instead and never enters the kernel](syscall-path.svg)

1. The wrapper puts the **system-call number** into register `rax` and up to six **arguments** into `rdi`, `rsi`, `rdx`, `r10`, `r8` and `r9` (not `rcx`, which the instruction itself overwrites).
2. It executes `syscall`. The CPU saves the return address in `rcx` and the flags in `r11`, switches to kernel mode and jumps to the address the kernel stored at boot in a model-specific register (MSR). This is Linux's `entry_SYSCALL_64`.
3. The entry code switches to the process's kernel stack, saves the user registers, and uses `rax` as an index into the **system-call table**, an array of function pointers: entry 1 is the kernel's `write` implementation.
4. The kernel function does the work: it checks the descriptor and the buffer, goes through the VFS to the pipe, the file system or the terminal driver, and may block (the process then waits, and other processes run).
5. The result goes into `rax`, and `sysret` returns to user mode, just after the `syscall` instruction.
6. The kernel reports errors as small negative numbers: `-EBADF` (−9) for a bad file descriptor, `-ENOENT` (−2) for a missing file. The wrapper checks for a value between −4095 and −1, stores its negation in the thread's **`errno`** variable and returns −1, which is the convention C programs expect. The [Linux section](#one-system-call-three-ways) shows the same call made three ways, and the wrapper's machine code.

<details>
<summary><b>Explained simply:</b> API, POSIX, wrapper, buffer, system-call number, system-call table, register, MSR, VFS, errno</summary>

- **API** (application programming interface): the list of functions a library offers to programmers, with their names and rules.
- **POSIX:** a standard that says which functions a Unix-like system must offer and how they behave, so that programs can move between such systems.
- **Wrapper:** a small function whose only job is to call something else in the right way, like an envelope around a letter.
- **Buffer:** a waiting area in memory where data is collected before it is sent on in one go, like filling a whole basket before carrying it upstairs.
- **System-call number, system-call table:** each kind of request has a number; the kernel looks the number up in a table to find the code that handles it, like a menu where you order dish 39.
- **Register:** a tiny, very fast storage place inside the CPU; `rax`, `rdi` and so on are register names on x86-64.
- **MSR** (model-specific register): a special CPU register for settings, here the address where system calls enter the kernel.
- **VFS** (virtual file system): the layer of the kernel that offers the same file operations for every kind of file system and device.
- **errno:** a variable in which the C library leaves the number of the last error, such as 2 ("no such file") or 9 ("bad file descriptor").

</details>

### The vDSO: system calls that do not enter the kernel

Some requests only read information that the kernel already knows, and are made very often: above all the current time, which a busy server may ask for millions of times per second. For these, the kernel maps a small shared library into every process, the **vDSO** (virtual dynamic shared object), together with a read-only data page that the kernel keeps up to date (the `[vdso]` and `[vvar]` lines of `/proc/PID/maps` in the [virtual memory lecture](../09-virtual-memory/#the-address-space-of-a-process)). The C library's `clock_gettime()`, `gettimeofday()`, `time()` and `getcpu()` call the vDSO's functions, which compute the answer from the data page and the CPU's time-stamp counter, entirely in user mode (Linux man-pages project, n.d.-h). The kernel tells each new program where the vDSO is through the auxiliary vector (`AT_SYSINFO_EHDR`). Only reading can be done this way; anything that changes the system's state or needs a permission check must enter the kernel.

### What a system call costs

A system call costs much more than a function call, even when the kernel does almost nothing: the mode switch, saving and restoring registers, switching stacks, the checks of the entry code, and on many processors extra work to defend against speculative-execution attacks, which empties or partitions internal buffers at each crossing. The measurement in the [Linux section](#the-price-of-entering-the-kernel) gives about 2 ns for a function call, 120 to 135 ns for `getpid()`, and 30 to 39 ns for `clock_gettime()` through the vDSO, against 190 ns for the same call forced into the kernel. The lessons are the ones of performance work everywhere: do not make a system call per byte (buffer, as `printf` does), batch requests (`readv`/`writev`, `sendmmsg`, `io_uring`), and keep the data in user space where possible. The cost of switching from one process to another, which is much larger, is measured in the [next lecture](../07-concurrency-deadlocks-scheduling/#the-cost-of-a-switch).

<details>
<summary><b>Explained simply:</b> vDSO, time-stamp counter, auxiliary vector, speculative execution, batching</summary>

- **vDSO:** a tiny library that the kernel puts into every program, so that a program can read some kernel information (mostly the time) without asking the kernel.
- **Time-stamp counter:** a counter in the CPU that increases at a fixed rate; the time can be computed from it.
- **Auxiliary vector:** a short list of facts the kernel hands a new program at start-up, such as the page size and where the vDSO is.
- **Speculative execution:** the CPU guesses what comes next and starts working on it early; some attacks abuse traces of these guesses, and the defences make crossings into the kernel slower.
- **Batching:** doing many small requests in one go, like posting all your letters in one trip instead of one trip per letter.

</details>

## The process life cycle

Unix creates processes with an unusual pair of calls: **`fork()`** makes a copy of the calling process, and **`exec()`** replaces the program running in a process with a new one. A third, **`exit()`**, ends a process, and **`wait()`** lets a parent collect the result. Every process except the first is created this way, so the processes of a system form a **tree**: on a typical Linux system, PID 1 (`systemd`, or another init program) is the ancestor of all user processes, and PID 2 (`kthreadd`) of the kernel's own threads.

![A shell runs a command: the parent (PID 100) calls fork; the child (PID 101) starts as a copy of the shell, calls execve("/usr/bin/ls") and runs ls with the same PID, then exit(0) and becomes a zombie; the parent waits in waitpid(101) in state S, gets SIGCHLD and the status 0, and the zombie is removed](fork-exec-wait.svg)

### fork: a copy of the caller

`fork()` creates a new process, the **child**, that is an almost exact copy of the calling process, the **parent**: same program, same memory contents, same open files (the child gets a copy of the descriptor table, whose entries point to the same open file descriptions, so parent and child share file offsets), same current directory, credentials and signal handlers. The differences are few: the child has a new PID, its parent is the caller, its CPU-time counters start at zero, pending signals and locks are not inherited, and, most importantly, `fork()` **returns twice**: in the parent it returns the child's PID, in the child it returns 0. That is how the two copies tell themselves apart:

```c
pid_t pid = fork();
if (pid < 0)        perror("fork");          /* no child was created  */
else if (pid == 0)  child_work();            /* in the child          */
else                parent_work(pid);        /* in the parent         */
```

Copying a whole address space would make `fork()` slow, and is usually wasted, because most children call `exec()` at once. Linux therefore copies only the page tables and marks all private pages read-only in both processes: **copy-on-write**. A page is copied only when one of them writes to it ([Virtual memory: copy-on-write](../09-virtual-memory/#copy-on-write)). Even so, the page tables of a large process must be copied, and the [Linux section](#creating-processes-and-threads-what-it-costs) measures 20 ms for a `fork()` of a process with 1 GiB of memory.

One trap: a `printf` before `fork()` whose output is still in the C library's buffer is copied with the memory and printed twice, once by each process. A program should flush its output (`fflush(stdout)`) before forking, and a child that does not `exec` should end with `_exit()`, which does not flush the buffers again.

### exec: a new program in the same process

`execve(path, argv, envp)` loads a new program into the calling process: the kernel opens the executable, checks permissions, discards the old address space, maps the new program's text and data, sets up a new stack with the arguments and environment, and starts the new program at its entry point (for a dynamically linked program, first the dynamic loader `ld.so`, which maps the shared libraries). On success `execve()` never returns, because the code that called it no longer exists.

What survives is the process itself: the PID and parent, the open file descriptors (except those marked **close-on-exec**, `O_CLOEXEC`), the current directory, the resource limits, the signal mask, and ignored signals (handled signals are reset to their default action, because the handler code is gone). The credentials stay too, unless the new program file is setuid or setgid ([Access control: setuid](../11-access-control/#setuid-borrowing-the-owners-identity)).

`execve` is the only system call; the C library offers a family of front ends whose names say how the arguments are given: `execl`, `execlp`, `execle` take a **l**ist of arguments, `execv`, `execvp`, `execvpe` a **v**ector (array); the **p** versions search the directories of `PATH` for the program, the **e** versions take an explicit **e**nvironment.

### exit and wait

A process ends by calling `exit(status)` (the library function runs `atexit` handlers and flushes the standard I/O buffers, then makes the `exit_group` system call), by returning from `main`, or by being killed by a signal. The kernel then closes its files, frees its memory and its other resources, and keeps only a small record with the **exit status**, until the parent collects it. A process in this state is a **zombie**; how zombies arise, why every ending process passes through this state and what happens to them is covered in the [next lecture's process states](../07-concurrency-deadlocks-scheduling/#the-process-state-space). The parent is notified by the signal `SIGCHLD`.

The parent collects a child with `wait(&status)` (any child) or `waitpid(pid, &status, options)` (a given child, or with `WNOHANG` without blocking). The status word packs several facts, which macros decode: `WIFEXITED(status)` is true if the child called `exit`, and `WEXITSTATUS(status)` then gives the low 8 bits of its exit code (0 means success by convention); `WIFSIGNALED(status)` is true if a signal killed it, and `WTERMSIG(status)` gives the signal's number. A shell shows the same information as `$?`: the exit code, or 128 plus the signal's number.

### Orphans and reparenting

If a parent ends before its child, the child becomes an **orphan**. It keeps running, but someone must collect its exit status, so the kernel gives it a new parent: normally PID 1, whose init program reaps every orphan that ends. A process can also declare itself a **child subreaper** (`prctl(PR_SET_CHILD_SUBREAPER)`): orphans among its descendants are then reparented to it instead of to PID 1. Service managers (`systemd --user`) and container runtimes use this to keep track of all processes they started, even after an intermediate process has exited. The [Linux section](#orphans-and-subreapers) shows both cases.

<details>
<summary><b>Explained simply:</b> parent, child, fork, copy-on-write, exec, dynamic loader, close-on-exec, PATH, exit status, zombie, SIGCHLD, wait, orphan, reparenting, subreaper</summary>

- **Parent, child:** the process that created another one, and the new process.
- **fork():** the call that makes a copy of the running process. Afterwards there are two processes running the same program; the copy is the child.
- **Copy-on-write:** after a fork, parent and child share memory until one of them changes something; only then is a private copy made, like two people sharing a printed text and photocopying a page only when one wants to write on it.
- **exec():** the call that throws away the current program of a process and starts another one in its place, keeping the same process number.
- **Dynamic loader (`ld.so`):** the small program that starts first and connects a program to the shared libraries it needs.
- **Close-on-exec:** a mark on a file descriptor that says "close me automatically when a new program is started".
- **PATH:** a setting that lists the folders in which the system looks for a program when you type only its name.
- **Exit status:** a number a program leaves behind when it ends; 0 means "everything went well".
- **Zombie:** a finished process whose exit status has not yet been collected by its parent.
- **SIGCHLD:** the signal a parent gets when one of its children ends.
- **wait():** the call with which a parent waits for a child to end and collects its exit status.
- **Orphan, reparenting:** a process whose parent has ended; it gets a new parent (reparenting), so that its exit status can still be collected.
- **Subreaper:** a process that has asked to adopt the orphans among its descendants, like a grandparent who takes over.

</details>

### How a shell uses them

A shell is a loop: read a command line, split it into words, `fork()` a child, let the child `exec()` the program, and `wait()` for the child unless the command ends with `&`. The separation of `fork` and `exec` is what makes the Unix shell so simple: between the two calls, the child is still running the shell's own code and can prepare its environment for the new program with ordinary system calls, without any special support in `exec` (Ritchie & Thompson, 1974):

- **Redirection** `cmd > out.txt`: the child opens `out.txt` (getting, say, descriptor 3), calls `dup2(3, 1)`, which makes descriptor 1 refer to the same open file description as descriptor 3, closes 3, and calls `exec`. The new program writes to descriptor 1 as always, and never learns that it is a file and not the terminal. `cmd < in.txt` does the same with descriptor 0.
- **Pipelines** `cmd1 | cmd2`: the shell creates a **pipe** with `pipe(fd)`, a kernel buffer with a write end `fd[1]` and a read end `fd[0]`. It forks two children; the first makes the write end its descriptor 1, the second makes the read end its descriptor 0; every process closes the descriptors it does not need, and the children `exec` their programs.
- **Built-in commands** such as `cd` and `exit` cannot be separate programs: `cd` must change the current directory of the shell itself, and a child's `chdir()` would only change the child's.

![File descriptors for ls /etc | grep ^host >hosts.txt: the ls child has descriptor 1 pointing to the pipe's write end and 0 and 2 to the terminal; the grep child has 0 pointing to the pipe's read end, 1 to hosts.txt and 2 to the terminal; both pipe ends point to one pipe buffer in kernel memory](fd-tables.svg)

`minish.c` in this folder is such a shell in about 100 lines, with `<`, `>`, `>>`, pipelines and the built-ins `cd` and `exit`; the [Linux section](#a-shell-in-a-hundred-lines) runs it and traces its system calls. One detail is easy to get wrong: the parent must close its copies of the pipe's ends. A reader sees end-of-file only when *every* descriptor for the write end is closed; if the shell kept one, `grep` would wait for more input for ever.

### Alternatives to fork

`fork()` followed at once by `exec()` copies page tables only to throw them away, and the bigger the parent, the more it costs. Several alternatives exist:

- **`vfork()`** (from BSD Unix) creates a child that borrows the parent's address space, while the parent is suspended until the child calls `exec` or `_exit`. It is fast, but dangerous: the child must not return from the function or change any variable, because it would change them in the parent.
- **`posix_spawn()`** creates a new process running a new program in one call, with a list of file actions (open, close, `dup2`) and attributes (signal mask, process group) to apply in between, which covers what shells usually do between `fork` and `exec`. glibc implements it with `clone()` in the `vfork` style, on a small separate stack, so its cost does not depend on the parent's size. Windows has always worked this way: `CreateProcess` starts a new program in a new process, and has no `fork`.
- **`clone()`** (and the newer `clone3()`) is Linux's general call behind all of these: its flags say which resources the new task shares with its creator (address space, file table, signal handlers, and so on) and which namespaces it gets (the basis of containers, see [Virtualization and containerization: namespaces](../13-virtualization-containerization/#namespaces)). With no sharing flags it makes a process (glibc's `fork()` is `clone()` with `SIGCHLD` and two flags for thread IDs); with the right flags it makes a thread (next section) (Linux man-pages project, n.d.-a).

Baumann et al. (2019) argue that `fork` was a convenient shortcut for the PDP-7 and PDP-11 era that has outlived its usefulness: it is slow for large processes, it copies all of the parent's state and so is insecure by default (secrets, open descriptors), it does not mix with threads (only the calling thread is copied, so locks held by other threads stay locked for ever in the child, and POSIX allows only async-signal-safe functions in the child of a multithreaded process before `exec`), and it forces the kernel to support copy-on-write and overcommitting memory. They recommend `posix_spawn` for starting programs and keeping `fork` for the cases that really need a copy, such as Android's Zygote ([Mobile operating systems: Android](../14-mobile-wearable-embedded/#android)), which forks every app from a process with the runtime already loaded.

<details>
<summary><b>Explained simply:</b> shell, redirection, dup2, pipe, pipeline, end-of-file, built-in command, vfork, posix_spawn, clone, namespace, PDP-7, overcommitting memory, Zygote</summary>

- **Shell:** the program that reads the commands you type and runs them, such as `bash`.
- **Redirection:** sending a program's output into a file (`>`) or feeding it from a file (`<`) instead of the terminal.
- **dup2(a, b):** "make ticket number b refer to the same thing as ticket number a".
- **Pipe, pipeline:** a pipe is a one-way channel in the kernel: what one process writes into one end, the other reads from the other end. A pipeline (`a | b`) connects programs with pipes, like an assembly line.
- **End-of-file:** the signal to a reader that no more data will come.
- **Built-in command:** a command the shell carries out itself instead of starting a program, because it must change the shell itself (`cd`).
- **vfork:** a faster fork in which the child borrows the parent's memory until it starts a new program; the parent waits meanwhile.
- **posix_spawn:** a single call that means "start this program in a new process", without making a copy first.
- **clone:** Linux's general call for creating processes and threads; its options say what the new one shares with its creator.
- **Namespace:** a Linux feature that gives a group of processes its own view of something (process numbers, network, files); containers are built from them.
- **PDP-7, PDP-11:** small computers of the late 1960s and 1970s on which Unix was first written.
- **Overcommitting memory:** promising programs more memory than the machine has, betting that they will not all use it.
- **Zygote:** a process on Android that starts once with everything an app needs already loaded; every new app is made as a copy of it, which is much faster than starting from nothing.

</details>

## Threads

A process has one address space and, in the classic model, one flow of control. Many programs need several flows of control that share data: a web server that serves many clients at once, a word processor that checks spelling while the user types, a numerical program that uses all cores of the CPU. Several processes could do this, but they would have to share data through explicit IPC (next section), and creating and switching processes is expensive. A **thread** is a flow of control inside a process: it has its own program counter, registers and stack, but shares everything else with the other threads of the process (Arpaci-Dusseau & Arpaci-Dusseau, 2023). The benefits:

- **Responsiveness:** one thread can wait for the disk or the network while another keeps the user interface alive.
- **Sharing:** threads share memory directly, with no copying and no system calls; a pointer means the same in every thread.
- **Economy:** creating a thread and switching between threads of the same process is cheaper than doing the same with processes, because no new address space is needed and no page-table switch (with its TLB flush) happens between them.
- **Parallelism:** the threads of one process can run on several cores at the same time.

The price is that every shared variable can now be the subject of a race condition: synchronisation, the subject of the [next lecture](../07-concurrency-deadlocks-scheduling/#the-critical-section-problem), becomes the programmer's everyday problem.

### What threads share and what they own

![One process with four threads: shared by all are the code, the global data and BSS, the heap, the memory map and page tables, the open files, the signal handlers, the PID and the user and group IDs, the current directory and limits; each thread owns its TID, registers, stack, thread-local storage, signal mask and scheduling state](threads-share.svg)

Each thread has its own **stack**, because each is in the middle of its own chain of function calls, and its own **registers**, saved in the kernel while it does not run. It may also have **thread-local storage** (TLS): variables declared `__thread` in GNU C (`_Thread_local` in C11, `thread_local` in C++11 and C23) exist once per thread, at the same name but at a different address in each thread. The C library uses TLS for `errno`, so that an error in one thread does not overwrite the error code that another thread is about to read. On x86-64 the `fs` segment register points to the current thread's TLS block, and the kernel switches it with the thread.

Sharing has consequences for library design. A function is **thread-safe** if several threads can call it at the same time; functions that keep hidden static state, such as `strtok` or the classic `localtime`, are not, which is why POSIX added re-entrant versions (`strtok_r`, `localtime_r`). And some process-wide operations act on all threads: if any thread calls `exit()`, the whole process ends; a signal sent to the process is delivered to one thread that does not block it.

### User-level and kernel-level threads

Threads can be implemented in two places, and the possible mappings between them have names (Silberschatz et al., 2018):

![Three threading models. N:1: four user threads are scheduled by a thread library onto one kernel thread. 1:1: each of four user threads is its own kernel thread. M:N: four user threads are scheduled by a runtime onto two kernel threads; the kernel schedules the kernel threads on two CPUs](thread-models.svg)

- **N:1, user-level threads.** A library in the process implements threads entirely in user space: it keeps a stack and saved registers for each thread and switches between them in user mode, for example when a thread waits for a lock. The kernel sees one process. Switching is very fast (a function call's worth of work), and it works on any kernel. But if one thread makes a blocking system call, the kernel blocks the whole process, and all threads stop; and the threads cannot run on several cores. Early Java "green threads" and the GNU Portable Threads library worked this way.
- **1:1, kernel-level threads.** Every thread is a separate entity scheduled by the kernel. Blocking calls block only one thread, threads run in parallel on several cores, and the kernel's scheduler treats them fairly; creating a thread and switching between threads needs the kernel. Linux, Windows and macOS use this model for their native threads.
- **M:N, hybrid.** A run-time system schedules many user-level threads onto a smaller number of kernel threads. It combines cheap threads with parallelism, but is complicated: the runtime must know when a kernel thread blocks, so that it can run another user thread on another kernel thread. *Scheduler activations* proposed kernel upcalls for exactly this (Anderson et al., 1992), and Solaris and NetBSD used M:N for a while.

Linux tried M:N designs too, but its developers concluded that a 1:1 model with a fast kernel was simpler and fast enough. The **Native POSIX Thread Library** (NPTL), part of glibc since 2003, is 1:1; its authors reported that starting and stopping 100,000 threads, which had formerly taken 15 minutes, took 2 seconds with NPTL and the kernel changes made for it (Drepper & Molnar, 2003). M:N has returned at the language level, where the runtime controls all blocking operations:

- **Goroutines** in Go are functions running concurrently in the same address space, with small stacks that grow as needed; the Go runtime multiplexes them onto a few OS threads (by default one per core), so that "if one should block, such as while waiting for I/O, others continue to run" (The Go Authors, n.d.). A Go program can run hundreds of thousands of goroutines.
- **Virtual threads** in Java 21 (Pressler & Bateman, 2023) are `Thread` objects that are not tied to an OS thread: the JVM mounts a virtual thread on a *carrier* thread while it runs and, in most cases, unmounts it when it blocks, for example in I/O, so millions of them can exist.
- **async/await** in Python, JavaScript, C# and Rust go further: tasks give up the CPU only at explicit `await` points, and an event loop in one or a few threads runs them (cooperative scheduling).

### Threads in Linux: tasks and clone flags

The Linux kernel has no separate thread object. Its unit of scheduling is the **task** (a `task_struct`), and a thread is simply a task that shares resources with others. `pthread_create()` calls `clone3()` with flags that request sharing: `CLONE_VM` (the address space), `CLONE_FS` (current and root directory, umask), `CLONE_FILES` (the descriptor table), `CLONE_SIGHAND` (signal handlers), `CLONE_THREAD` (the same thread group, so the same PID), `CLONE_SYSVSEM`, and `CLONE_SETTLS` (a new TLS block); it also passes a stack, which glibc allocates with `mmap` (8 MiB by default, plus a guard page). `fork()` uses none of the sharing flags. Between the two lie the many combinations the flags allow, for example a process that shares only its file table.

Linux therefore uses two kinds of IDs. Each task has its own ID, the **TID**, returned by `gettid()`. The tasks of one process form a **thread group**, whose ID, the TGID, is the TID of the first thread; `getpid()` returns the TGID, so that all threads of a process report the same PID, as POSIX requires. `/proc/PID/task/` has one directory per thread, and `ps -L` lists them (the [Linux section](#threads-are-tasks) shows both). The scheduler of the [next lecture](../07-concurrency-deadlocks-scheduling/#linux-scheduling) schedules tasks, not processes.

### POSIX threads

The portable C interface to threads is **pthreads** (POSIX threads; Kerrisk, 2010, ch. 29–33):

```c
#include <pthread.h>

void *worker(void *arg) { /* ... */ return NULL; }

pthread_t t;
pthread_create(&t, NULL, worker, arg);   /* start worker(arg) in a new thread  */
pthread_join(t, &result);                /* wait for it and get its return value */
```

A thread ends when its start function returns or when it calls `pthread_exit()`. Like a process, a finished thread keeps its result until another thread joins it; a thread that nobody will join should be **detached** (`pthread_detach`), so that its resources are freed at once. Shared data is protected with `pthread_mutex_t` and `pthread_cond_t`, the mutexes and condition variables of the [next lecture](../07-concurrency-deadlocks-scheduling/#semaphores-more-than-a-lock).

<details>
<summary><b>Explained simply:</b> thread, responsiveness, parallelism, TLB, thread-local storage, thread-safe, re-entrant, user-level thread, kernel-level thread, N:1, 1:1, M:N, NPTL, goroutine, virtual thread, carrier thread, async/await, event loop, task, umask, TID, TGID, pthreads, join, detach, race condition, mutex, condition variable</summary>

- **Thread:** one line of work inside a process; all threads of a process see the same memory.
- **Responsiveness:** the program keeps reacting to the user while it works on something else.
- **Parallelism:** really doing several things at the same moment, on several CPU cores.
- **TLB:** a small cache of recent address translations in the CPU; it has to be refilled after switching to another process's memory.
- **Thread-local storage:** variables of which each thread has its own copy, like each cook's own notebook in a shared kitchen.
- **Thread-safe, re-entrant:** a function is thread-safe if several threads can use it at the same time without mixing up their data; a re-entrant version keeps all its working data in variables that the caller provides.
- **User-level thread:** a thread that only a library inside the program knows about; the kernel sees one process. **Kernel-level thread:** a thread the kernel knows about and schedules itself.
- **N:1, 1:1, M:N:** how many program threads are mapped onto how many kernel threads: many onto one, one onto one, or many onto a few.
- **NPTL:** the thread library of Linux, part of the C library.
- **Goroutine:** Go's lightweight thread; the Go runtime shares a few real threads among very many goroutines.
- **Virtual thread, carrier thread:** Java's lightweight thread; while it runs it sits on a real (carrier) thread, and when it has to wait it gets off, so the carrier can run another one.
- **async/await, event loop:** a style in which tasks say explicitly where they are willing to wait (`await`); one loop runs whichever task is ready.
- **Task:** Linux's name for anything it schedules: a single-threaded process or one thread of a process.
- **umask:** a per-process setting that removes permissions from newly created files.
- **TID, TGID:** thread ID, the number of one task; thread group ID, the number shared by all threads of a process (which is what `getpid()` returns).
- **pthreads:** the standard thread library of Unix-like systems.
- **Join, detach:** joining a thread means waiting for it to finish and taking its result; a detached thread cleans up after itself and cannot be joined.
- **Race condition:** a bug where the result depends on which of two threads happens to be faster, like two people editing the same shopping list at once and one crossing out what the other just wrote.
- **Mutex, condition variable:** a mutex is a lock that only one thread can hold at a time, like the key to a single bathroom; a condition variable lets a thread sleep until another thread tells it that something has changed.

</details>

## Inter-process communication

Processes are isolated from each other on purpose: each has its own address space, and one cannot read another's memory. When they must cooperate, they use **inter-process communication** (IPC) mechanisms that the kernel provides. They fall into two families: mechanisms that **pass data through the kernel** (pipes, message queues, sockets), and **shared memory**, which lets processes access the same physical pages directly. Signals are a third, special kind: they carry almost no data, only the fact that something happened (Stevens & Rago, 2013; Kerrisk, 2010).

![Two ways to move data between processes. Through the kernel: process A's write() copies its buffer into a kernel buffer, and process B's read() copies it out again: two system calls and two copies per message, and the kernel synchronises the two. Shared memory: processes A and B map the same page frames into their address spaces; A's stores are seen by B without system calls or copies, but they must synchronise themselves](ipc-copies.svg)

### Pipes and FIFOs

A **pipe** is a one-way byte stream through a kernel buffer, created with `pipe(fd)`. What is written into `fd[1]` can be read from `fd[0]`, in order and without message boundaries. The kernel synchronises the two sides: a reader blocks while the pipe is empty, a writer blocks while it is full (the default capacity on Linux is 64 KiB, and can be changed with `fcntl(F_SETPIPE_SZ)`); writes of up to `PIPE_BUF` bytes (4096 on Linux) are atomic, so they are not interleaved with other writers' data (Linux man-pages project, n.d.-b). A reader gets end-of-file when all write ends are closed; a writer whose readers are all gone receives the signal `SIGPIPE` (or the error `EPIPE`). Because a pipe has no name, only related processes can use it: the creator and the children that inherit the descriptors, as in a shell pipeline.

A **FIFO** or *named pipe* (`mkfifo name`) is a pipe with a name in the file system, so unrelated processes can open it like a file; the data still never touches the disk ([File systems: file types](../10-file-systems/#file-types)).

### Signals

A **signal** is a small asynchronous notification sent to a process by the kernel or by another process: "you divided by zero", "your child has ended", "the user pressed Ctrl-C", "please terminate". The [interrupts lecture](../05-interrupts/#program-interrupts-become-signals) showed how the CPU's program interrupts become signals; signals are, in a sense, the interrupts of user processes. Each signal has a number and a default action:

| Signal | Number (x86-64) | Typical cause | Default action |
| --- | --- | --- | --- |
| `SIGINT` | 2 | Ctrl-C on the terminal | terminate |
| `SIGKILL` | 9 | `kill -9`; cannot be caught or ignored | terminate |
| `SIGSEGV` | 11 | invalid memory access | terminate with core dump |
| `SIGPIPE` | 13 | writing to a pipe without readers | terminate |
| `SIGALRM` | 14 | a timer set with `alarm()` expired | terminate |
| `SIGTERM` | 15 | polite request to end (`kill` default) | terminate |
| `SIGCHLD` | 17 | a child ended or stopped | ignore |
| `SIGCONT` | 18 | continue a stopped process (`fg`, `bg`) | continue |
| `SIGSTOP` | 19 | stop; cannot be caught or ignored | stop |

A process can replace the default action with a **handler**, a function installed with `sigaction()`. When the signal arrives, the kernel interrupts the process wherever it is (between two instructions, or in a blocking system call), arranges for the handler to run on its stack, and resumes the interrupted code when the handler returns. Signals that are blocked by the process's signal mask stay pending until they are unblocked. Ordinary signals do not queue: two `SIGUSR1`s that arrive while one is pending are delivered once.

Because a handler can interrupt the program anywhere, even in the middle of `malloc` or `printf` while they are changing their internal data structures, a handler may only call **async-signal-safe** functions: a short list in POSIX that includes `write`, `_exit`, `kill` and `sigaction`, but not `printf`, `malloc` or anything that takes a lock (Linux man-pages project, n.d.-e). The safest handler sets a flag of type `volatile sig_atomic_t` and returns; the main program checks the flag. This is the same problem as the shared data of interrupt handlers in the [interrupts lecture](../05-interrupts/#interrupts-and-concurrency).

A signal can also interrupt a **blocking system call** such as `read()` on an empty pipe. The call then either fails with `EINTR` ("interrupted system call"), and the program must repeat it, or, if the handler was installed with the flag `SA_RESTART`, the kernel restarts it automatically after the handler. The [Linux section](#a-signal-interrupts-a-system-call) shows both. (Waits that a signal may interrupt are the interruptible `S` sleeps of the [next lecture](../07-concurrency-deadlocks-scheduling/#the-process-state-space).)

### Shared memory

**Shared memory** maps the same physical page frames into the address spaces of several processes. After setting it up, the processes read and write it with ordinary instructions: no system call, no copy, which makes it the fastest IPC mechanism. With the POSIX interface, one process creates a named object with `shm_open("/name", O_CREAT | O_RDWR, 0600)` (on Linux, a file in the memory file system `/dev/shm`), sets its size with `ftruncate()`, and every process that opens the same name maps it with `mmap(..., MAP_SHARED, fd, 0)` (Linux man-pages project, n.d.-d). Related processes can also simply create an anonymous `MAP_SHARED` mapping before `fork()`. The older System V interface (`shmget`, `shmat`) does the same with numeric keys.

The kernel does not synchronise the users of shared memory. The processes must do it themselves, with the tools of the [next lecture](../07-concurrency-deadlocks-scheduling/#three-layers-of-mutual-exclusion): a semaphore created with `sem_init(&s, 1, value)` inside the shared region (the 1 means "shared between processes"), a mutex with the `PTHREAD_PROCESS_SHARED` attribute, or atomic variables. Shared memory also needs care with pointers: the region may be mapped at different addresses in different processes, so data structures inside it should use offsets rather than pointers.

### Message queues

A **message queue** keeps messages, not bytes: each `mq_send()` adds one message, each `mq_receive()` takes one whole message, so the boundaries are preserved. POSIX message queues (`mq_open`, `mq_send`, `mq_receive`) have names and priorities (the highest-priority message is received first) and limits: by default at most 10 messages of at most 8 KiB in a queue on Linux. System V message queues (`msgget`, `msgsnd`, `msgrcv`) let the receiver select messages by a type field. Like pipes, both copy the data into the kernel and out again.

### Sockets

A **socket** is an endpoint for communication that can be used across a network, and the only mechanism in this list that can connect processes on different machines. With the address family `AF_INET` or `AF_INET6` it speaks TCP (`SOCK_STREAM`, a reliable byte stream) or UDP (`SOCK_DGRAM`, individual datagrams) over the network. **Unix domain sockets** (`AF_UNIX`) use the same interface on one machine, with a path in the file system as the address (or an unnamed pair from `socketpair()`); they are two-way, support streams, datagrams and sequenced packets, and can do two things no other mechanism can: pass **file descriptors** from one process to another (`SCM_RIGHTS`) and tell the receiver the sender's PID and user ID (`SO_PEERCRED`) (Linux man-pages project, n.d.-g). Most local services are reached through them: systemd and D-Bus, the X and Wayland display servers, the Docker daemon (`/var/run/docker.sock`), databases.

### Choosing a mechanism

| Mechanism | Direction | Boundaries | Unrelated processes | Across machines | Copies per message | Synchronisation |
| --- | --- | --- | --- | --- | --- | --- |
| pipe | one-way | byte stream | no (inherited) | no | 2 | by the kernel |
| FIFO | one-way | byte stream | yes (path name) | no | 2 | by the kernel |
| message queue | one-way per queue | messages, priorities | yes (name) | no | 2 | by the kernel |
| Unix domain socket | two-way | stream or datagrams | yes (path name) | no | 2 | by the kernel |
| TCP/UDP socket | two-way | stream / datagrams | yes (address) | yes | 2 or more | by the kernel |
| shared memory | any | none: just memory | yes (name) | no | 0 | by the processes |
| signal | one-way | a number only | yes (PID, permission) | no | none | by the kernel |

As a rule of thumb: a pipe for a stream between a parent and its children, a Unix domain socket for a local client–server protocol (and anything that must pass descriptors or check the client's identity), a TCP socket when the peer may be on another machine, shared memory for large volumes of data or very low latency, with explicit synchronisation, and signals only for notifications. The [Linux section](#ipc-latency-and-throughput) measures four of them.

<details>
<summary><b>Explained simply:</b> IPC, FIFO, PIPE_BUF, atomic, SIGPIPE, signal, default action, handler, core dump, signal mask, pending, async-signal-safe, sig_atomic_t, EINTR, SA_RESTART, shared memory, /dev/shm, semaphore, process-shared semaphore, message queue, socket, TCP, UDP, Unix domain socket, SCM_RIGHTS, D-Bus</summary>

- **IPC** (inter-process communication): any way for separate processes to exchange data or messages.
- **FIFO** (first in, first out), named pipe: a pipe that has a name in the file system, so any process can find it.
- **PIPE_BUF, atomic:** a write of at most `PIPE_BUF` bytes goes into the pipe in one piece (atomically), never mixed with another writer's data.
- **SIGPIPE:** the signal a process gets when it writes into a pipe that nobody reads any more.
- **Signal:** a short notice from the kernel or another process, like a tap on the shoulder; it says only which kind of event happened.
- **Default action, handler:** what happens to a process when a signal arrives if it has not said otherwise (often: it ends), and a function the program provides to react itself.
- **Core dump:** a file with a copy of the program's memory at the moment it crashed, for later examination with a debugger.
- **Signal mask, pending:** the set of signals a process has asked to hold back for now; a held-back signal waits (is pending) until it is let through.
- **Async-signal-safe:** a function that may be called from a signal handler, because it cannot be harmed by interrupting itself.
- **sig_atomic_t:** an integer type that can be read and written in one step, safe for a flag between a handler and the main program.
- **EINTR, SA_RESTART:** EINTR is the error "interrupted by a signal, try again"; with SA_RESTART the kernel tries again by itself.
- **Shared memory, /dev/shm:** memory that two or more processes can all see; on Linux the named pieces appear as files in `/dev/shm`, which lives in RAM.
- **Semaphore:** a counter used for waiting: taking from it when it is zero makes you sleep until someone adds to it, like waiting for a free parking space.
- **Process-shared semaphore:** a semaphore placed in shared memory, so that several processes can use it.
- **Message queue:** a mailbox in the kernel where processes post and collect whole messages.
- **Socket:** an endpoint of a communication channel, like a telephone socket; the other end can be on the same or another computer.
- **TCP, UDP:** the Internet's two main ways of sending data: TCP like a phone call (reliable, in order), UDP like postcards (separate, may get lost).
- **Unix domain socket:** a socket that only connects programs on the same computer, with a file name as its address.
- **SCM_RIGHTS:** a way to hand an open file descriptor to another process through a Unix domain socket, like passing on a cloakroom ticket.
- **D-Bus:** a message system that desktop and system programs on Linux use to talk to each other.

</details>

## Watching the OS at work

Processes, system calls and IPC are invisible while they work. Linux offers several ways to observe them, each looking at a different layer (Gregg, 2019):

![Observability tools by layer: gdb and valgrind look at application code, ltrace at calls into shared libraries, strace at the system-call interface, /proc and /sys at the kernel's state, perf stat at hardware counters; perf record and eBPF/bpftrace see all layers](observability.svg)

- **`/proc` and `/sys`.** Two virtual file systems through which the kernel shows its data structures as files (Linux man-pages project, n.d.-c). `/proc/PID/` has a directory per process: `status` (name, state, IDs, memory, context switches), `maps` (the address space), `fd/` (the open descriptors, as symbolic links), `cmdline`, `environ`, `cwd`, `exe`, `limits`, `wchan` and `syscall` (where a sleeping process waits), `task/` (its threads). `/proc` also holds system-wide information (`/proc/meminfo`, `/proc/interrupts`), and `/sys` the device model and tunable kernel parameters. Tools such as `ps`, `top`, `pstree` and `lsof` simply read these files; `ptree.py` in this folder is a 50-line `pstree`.
- **`strace`** traces the system calls of a process (and with `-f` of its children and threads): each call with its decoded arguments, its result and the error name, plus signals. `-e trace=…` selects calls, `-c` counts calls and time per call, `-T` shows the time spent in each call, `-p PID` attaches to a running process. It uses the `ptrace` system call, through which the kernel stops the traced process at every system-call entry and exit and lets the tracer inspect it. This is exact but slow: the [Linux section](#tracing-with-strace) measures a factor of about 70 for a cheap system call.
- **`ltrace`** does the same one level higher, for calls into shared libraries (`malloc`, `printf`, `strlen`), by placing breakpoints on the program's calls to library functions.
- **`gdb`** can attach to a running process, stop it, and show its threads, its call stack (`bt`) and any variable; it also uses `ptrace`. **Valgrind** runs a program on a simulated CPU and checks every memory access, finding uses of uninitialised or freed memory and leaks, at a slowdown of 10 to 50 times.
- **`perf`** uses the kernel's `perf_events` subsystem: `perf stat` counts events such as CPU cycles, instructions, cache misses, context switches and page faults with the CPU's hardware counters; `perf record` samples the call stack of the running code many times per second, in user and kernel mode, and `perf report` shows where the time went; `perf trace` is a faster `strace`.
- **eBPF** lets small programs run inside the kernel, attached to almost any event: a kernel function (kprobe), a user function (uprobe), a static tracepoint (`sched:sched_process_fork`, `syscalls:sys_enter_execve`), a timer. The kernel verifies each program before loading it (it must terminate and may only read memory it is allowed to), and the programs aggregate data in the kernel, so only summaries are copied to user space. **bpftrace** is a high-level language for one-line eBPF programs (Gregg, 2019). Because they do not stop the observed processes, perf and eBPF are safe to use on busy production systems, where `strace` would slow everything down.

`strace`, `gdb` and `valgrind` are installed on the machine used for this lecture; `ltrace`, `perf` and `bpftrace` are not, and the eBPF tools need root rights and a kernel built with BPF support. Their use is therefore shown as a lab exercise, without outputs.

<details>
<summary><b>Explained simply:</b> observability, /proc, /sys, strace, ptrace, ltrace, gdb, backtrace, valgrind, perf, hardware counter, sampling, eBPF, kprobe, uprobe, tracepoint, verifier, bpftrace</summary>

- **Observability:** being able to see what a running system is doing, from the outside, without changing it.
- **/proc, /sys:** folders whose files are not on any disk; reading them asks the kernel for live information.
- **strace:** a tool that prints every request (system call) a program makes to the kernel.
- **ptrace:** the system call that lets one process (a debugger or tracer) stop, examine and control another.
- **ltrace:** like strace, but for calls into libraries.
- **gdb, backtrace:** the GNU debugger; a backtrace is the list of functions that are currently in progress, the innermost first.
- **valgrind:** a tool that runs a program slowly on a simulated processor and reports memory mistakes.
- **perf, hardware counter, sampling:** perf is Linux's performance tool; hardware counters are counters in the CPU (cycles, cache misses); sampling means looking at what the program is doing many times a second and counting where it was.
- **eBPF:** small, checked programs that run inside the kernel when chosen events happen, to count or record them.
- **kprobe, uprobe, tracepoint:** places where an eBPF program can be attached: any kernel function, any function of a program, or a fixed, named event in the kernel.
- **Verifier:** the part of the kernel that checks an eBPF program before it may run, so that it cannot crash or hang the kernel.
- **bpftrace:** a short language for writing eBPF programs in one line.

</details>

## The same ideas on Linux (x86-64)

The demos run as root on the Ubuntu 24.04 cloud virtual machine of the previous lectures: a KVM guest with 2 virtual CPUs (Intel Xeon at 2.1 GHz), 8 GiB of RAM and no swap, Linux 6.18, gcc 13.3, glibc 2.39, Python 3.13, strace 6.8 and gdb 15.1. Every program and script is in this folder; C programs are compiled as shown, scripts are run with `sh`. Timings vary from run to run, and more on a virtual machine than on real hardware; the proportions are what matter.

<details>
<summary><b>Explained simply:</b> console, root, gcc, -O2, script, KVM guest</summary>

- **Console** (terminal): a window where you type commands as text. Lines starting with `$` are what you type; the other lines are the computer's answer.
- **Root:** the administrator account.
- **gcc, -O2:** the C compiler, asked to optimise the code.
- **Script** (`.sh` file): a list of commands saved in a file and run one after the other.
- **KVM guest:** a virtual machine running under Linux's built-in hypervisor, KVM.

</details>

### The address space of a running program

`layout.c` prints the address of something in each region (a function, an initialised and an uninitialised global, a small and a large `malloc` block, a library function and a local variable) and then the lines of its own `/proc/self/maps` that contain them:

```console
$ gcc -O0 -o layout layout.c
$ ./layout
text  (main)           0x562f5a6022b9
data  (initialised)    0x562f5a605010
bss   (uninitialised)  0x562f5a605018
heap  (malloc 100 B)   0x562f7f5f22a0
mmap  (malloc 1 MiB)   0x7f5fde0ff010
libc  (printf)         0x7f5fde260100
stack (local)          0x7ffc6e857e88

matching lines of /proc/self/maps:
562f5a602000-562f5a603000 r-xp layout       <- text
562f5a605000-562f5a606000 rw-p layout       <- data, bss
562f7f5f2000-562f7f613000 rw-p [heap]       <- heap
7f5fde0ff000-7f5fde200000 rw-p (anonymous)  <- mmap
7f5fde228000-7f5fde3b1000 r-xp libc.so.6    <- libc
7ffc6e83a000-7ffc6e860000 rw-p [stack]      <- stack
$ size layout
   text	   data	    bss	    dec	    hex	filename
   4485	    700	     12	   5197	   144d	layout
```

The order matches the figure: text, then data and BSS, then the heap at low addresses; libraries, mappings and the stack near the top of the user half. The code is readable and executable (`r-xp`), the data writable but not executable (`rw-p`). The data and the BSS share a single page here, because together they are only 712 bytes: the BSS variable lies 8 bytes after the initialised one. The 100-byte block came from the heap, but the 1 MiB block got an anonymous mapping of its own, 1 MiB plus one page (`0x101000` bytes) for glibc's bookkeeping, because it is above glibc's threshold for using `mmap`. The heap starts at a random distance above the program (address space layout randomisation): run the program twice and all addresses change. The full map, with the vDSO, is shown in the [virtual memory lecture](../09-virtual-memory/#the-address-space-of-a-process).

### One system call, three ways

`hello3.c` makes the same `write` system call through the libc wrapper, through the generic `syscall()` function, and with the bare instruction, then repeats the call with a bad descriptor:

```c
static long raw_syscall3(long nr, long a1, long a2, long a3)
{
    long ret;
    __asm__ volatile ("syscall"
                      : "=a"(ret)                                   /* result in rax          */
                      : "a"(nr), "D"(a1), "S"(a2), "d"(a3)          /* rax, rdi, rsi, rdx     */
                      : "rcx", "r11", "memory");                    /* overwritten by syscall */
    return ret;
}
```

```console
$ gcc -O2 -o hello3 hello3.c
$ ./hello3
1: libc wrapper write()
2: syscall(SYS_write, ...)
3: bare syscall instruction
SYS_write = 1, SYS_getpid = 39, SYS_exit_group = 231
write(42, ...) via libc: returns -1, errno = 9 (Bad file descriptor)
write(42, ...) raw:      returns -9 (the kernel's -EBADF; EBADF = 9)
$ strace -e trace=write ./hello3 > /dev/null
write(1, "1: libc wrapper write()\n", 24) = 24
write(1, "2: syscall(SYS_write, ...)\n", 27) = 27
write(1, "3: bare syscall instruction\n", 28) = 28
write(42, "x", 1)                       = -1 EBADF (Bad file descriptor)
write(42, "x", 1)                       = -1 EBADF (Bad file descriptor)
write(1, "SYS_write = 1, SYS_getpid = 39, "..., 191) = 191
+++ exited with 0 +++
```

For the kernel the three ways are identical: three `write` calls. The bare instruction returns the kernel's raw answer, −9; the wrapper turns it into −1 and `errno` = 9. The `strace` run also shows the C library's buffering: with the output going to a file rather than a terminal, the three `printf` lines were not written when `printf` was called, but collected and written with a single 191-byte `write` when the program exited, after the two failing calls that came later in the program. The wrapper itself is a few instructions in the C library:

```console
$ gdb -q -batch -ex 'disassemble write' /lib/x86_64-linux-gnu/libc.so.6 | head -10
Dump of assembler code for function __GI___libc_write:
   0x000000000011c830 <+0>:	endbr64
   0x000000000011c834 <+4>:	cmpb   $0x0,0xef805(%rip)        # 0x20c040 <__libc_single_threaded>
   0x000000000011c83b <+11>:	je     0x11c850 <__GI___libc_write+32>
   0x000000000011c83d <+13>:	mov    $0x1,%eax
   0x000000000011c842 <+18>:	syscall
   0x000000000011c844 <+20>:	cmp    $0xfffffffffffff000,%rax
   0x000000000011c84a <+26>:	ja     0x11c8a0 <__GI___libc_write+112>
   0x000000000011c84c <+28>:	ret
   0x000000000011c84d <+29>:	nopl   (%rax)
```

The arguments are already in `rdi`, `rsi` and `rdx`, because the C calling convention passes the first three arguments in the same registers, so the wrapper only loads the number 1 into `eax` and executes `syscall`. The unsigned comparison with `0xfffffffffffff000` (−4096) catches exactly the results from −4095 to −1, and jumps to the code that sets `errno`. (The test of `__libc_single_threaded` selects a slower path in multithreaded programs, which also handles thread cancellation.) The kernel tells every new program where its vDSO is:

```console
$ LD_SHOW_AUXV=1 /bin/true | grep -E "SYSINFO|AT_PAGESZ|AT_EXECFN"
AT_SYSINFO_EHDR:      0x7fd8f39a8000
AT_PAGESZ:            4096
AT_EXECFN:            /bin/true
```

### The price of entering the kernel

`sccost.c` times two million calls of each: an ordinary function, `getpid()` through the wrapper and through `syscall()`, and `clock_gettime()` through the vDSO and forced into the kernel with `syscall()`:

```console
$ gcc -O2 -o sccost sccost.c
$ ./sccost
function call:                             3.6 ns
getpid() (libc wrapper):                 170.2 ns
syscall(SYS_getpid):                     123.3 ns
clock_gettime() (vDSO, no kernel):        30.0 ns
syscall(SYS_clock_gettime) (kernel):     190.2 ns
$ ./sccost
function call:                             1.5 ns
getpid() (libc wrapper):                 122.5 ns
syscall(SYS_getpid):                     135.7 ns
clock_gettime() (vDSO, no kernel):        38.8 ns
syscall(SYS_clock_gettime) (kernel):     193.0 ns
```

`getpid()`, which only reads a number from the `task_struct`, costs about 120 to 135 ns (one run measured 170 ns, a disturbance on the virtual machine), some 60 times a function call and about 260 clock cycles at 2.1 GHz; the [virtualization lecture](../13-virtualization-containerization/#the-price-of-a-vm-exit) measured 126 ns for `getppid()` on the same machine. Nearly all of it is the crossing itself. The vDSO's `clock_gettime()` costs 30 to 39 ns: about five times less than the same function in the kernel, because it never leaves user mode. `strace -c` confirms that the vDSO calls are invisible to the kernel:

```console
$ strace -c ./sccost 100000
function call:                             2.0 ns
getpid() (libc wrapper):                9311.7 ns
syscall(SYS_getpid):                    8232.7 ns
clock_gettime() (vDSO, no kernel):        29.4 ns
syscall(SYS_clock_gettime) (kernel):    9090.0 ns
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 66.21    0.193838           0    200000           getpid
 33.79    0.098911           0    100000           clock_gettime
```

The program called `clock_gettime()` 200,000 times, but the kernel saw only the 100,000 forced calls. The measurement also shows the price of tracing: under `strace` every system call took 8 to 9 µs, some 70 times longer, because the kernel stops the process twice per call and wakes up the tracer, while the vDSO calls ran at full speed.

### fork, exec, exit and wait

`lifecycle.c` starts three children. Each adds its number to a copy of the parent's variable `x`; child 0 exits with status 3, child 1 runs `/bin/sh` with `execv()`, child 2 writes through a null pointer. The parent collects all three:

```console
$ gcc -O2 -o lifecycle lifecycle.c
$ ./lifecycle
parent: pid 9348, x = 100
child 1: pid 9350, parent 9348, x = 102
child 1: now I am /bin/sh, pid 9350, parent 9348
child 2: pid 9351, parent 9348, x = 103
child 0: pid 9349, parent 9348, x = 101
parent: child 9349 exited, status 3
parent: child 9350 exited, status 0
parent: child 9351 killed by signal 11 (Segmentation fault)
parent: x is still 100
```

Each child changed only its own copy of `x`. Child 1 is still PID 9350 after `exec`, but now runs a different program, the shell, which prints its own PID (`$$`) and parent PID. The children ran in a different order from the one in which they were created: after `fork()`, parent and children are independent, and the scheduler decides. `waitpid()` decoded a normal exit with status 3 and a death by `SIGSEGV`. `strace` shows the system calls behind the library functions:

```console
$ strace -f -qq -e signal=none -e trace=clone,execve,wait4,exit_group ./lifecycle > /dev/null
execve("./lifecycle", ["./lifecycle"], 0x7ffd3a1c99a0 /* 200 vars */) = 0
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7f370bc08a10) = 9472
[pid  9471] clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7f370bc08a10) = 9473
[pid  9471] clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD <unfinished ...>
[pid  9472] exit_group(3 <unfinished ...>
[pid  9471] <... clone resumed>, child_tidptr=0x7f370bc08a10) = 9474
[pid  9471] wait4(9472,  <unfinished ...>
[pid  9472] <... exit_group resumed>)   = ?
[pid  9471] <... wait4 resumed>[{WIFEXITED(s) && WEXITSTATUS(s) == 3}], 0, NULL) = 9472
[pid  9471] wait4(9473, 0x7ffe8a023c40, 0, NULL) = ? ERESTARTSYS (To be restarted if SA_RESTART is set)
wait4(9473,  <unfinished ...>
[pid  9473] execve("/bin/sh", ["sh", "-c", "echo \"child 1: now I am /bin/sh,"...], 0x7ffe8a023dd8 /* 200 vars */) = 0
[pid  9473] exit_group(0)               = ?
<... wait4 resumed>[{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 9473
wait4(9474, [{WIFSIGNALED(s) && WTERMSIG(s) == SIGSEGV}], 0, NULL) = 9474
exit_group(0)                           = ?
```

glibc's `fork()` is a `clone()` without any sharing flag; `SIGCHLD` is the signal the parent wants when the child ends, and the two `CLONE_CHILD_*` flags let the library record the child's thread ID. `exit()` becomes `exit_group()`, which ends all threads of the process, and `waitpid()` becomes `wait4()`. The line with `ERESTARTSYS` is a side effect of the tracing, and appears only in some runs: the `SIGCHLD` of another child that had ended stopped the traced parent inside `wait4()` so that `strace` could see the signal; the kernel then restarted the call by itself (`ERESTARTSYS` is a kernel-internal code that a program never sees). Without a tracer, a `SIGCHLD` whose default action is to be ignored does not interrupt anything.

### Orphans and subreapers

`orphan.c` makes three generations: a grandparent forks a parent, which forks a child and exits after a second. The child prints its parent's PID before and after:

```console
$ gcc -O2 -o orphan orphan.c
$ ./orphan
grandparent 9512
child 9514: my parent is 9513
parent 9513: exiting without waiting
child 9514: my parent is 1
grandparent: waitpid(-1) returned -1
$ ./orphan subreaper
grandparent 9515
child 9517: my parent is 9516
parent 9516: exiting without waiting
child 9517: my parent is 9515
grandparent: waitpid(-1) returned 9517
```

The orphan was adopted by PID 1, and the grandparent could not wait for it (`waitpid(-1)` found no child: −1, with `errno` = `ECHILD`). With `prctl(PR_SET_CHILD_SUBREAPER, 1)`, the grandparent itself adopted its orphaned grandchild and collected its status.

### A shell in a hundred lines

`minish.c` reads `minish-demo.txt`, which contains a few commands (when its input is not a terminal, it echoes each command after the prompt):

```console
$ gcc -O2 -o minish minish.c
$ ./minish < minish-demo.txt
minish$ echo hello from a child process
hello from a child process
minish$ ls /etc >etc.txt
minish$ wc -l <etc.txt
165
minish$ ls /etc | grep ^host | sort -r
hosts
hostname
host.conf
minish$ echo appended >>etc.txt
minish$ tail -1 etc.txt
appended
minish$ nosuchprogram
minish: nosuchprogram: No such file or directory
[exit status 127]
minish$ ls /nonexistent
ls: cannot access '/nonexistent': No such file or directory
[exit status 2]
minish$ cd /proc/self
minish$ pwd
/proc/5287
minish$ grep ^Name status
Name:	minish
minish$ exit
```

Redirections, a three-stage pipeline and exit statuses work. A command that cannot be found makes `execvp()` fail in the child, which reports the error and exits with 127, the status shells use for "command not found". The last lines show why `cd` must be built in: `/proc/self` is a symbolic link to the directory of whichever process looks it up, and since `minish` itself ran `chdir()`, its current directory became its own `/proc` directory, as `pwd` and `grep ^Name status` in the children confirm. The heart of the program is the loop that builds a pipeline:

```c
int in = 0;                                 /* read end for the next command */
for (int c = 0; c < nc; c++) {
    int fd[2] = { -1, -1 };
    if (c < nc - 1 && pipe(fd) < 0) { perror("pipe"); break; }
    pids[c] = fork();
    if (pids[c] == 0) {                     /* child */
        if (in != 0) { dup2(in, 0); close(in); }
        if (fd[1] >= 0) { dup2(fd[1], 1); close(fd[1]); close(fd[0]); }
        run(cmd[c]);                        /* < > >> with open() + dup2(), then execvp() */
    }
    if (in != 0) close(in);                 /* parent: close what the child inherited */
    if (fd[1] >= 0) close(fd[1]);
    in = fd[0];
}
```

`trace-minish.sh` runs `ls /etc | grep ^host >hosts.txt` under `strace -ff`, which writes one trace file per process, and prints what the shell and its two children did before the new programs started:

```console
$ sh trace-minish.sh
== process 10190
pipe2([3, 4], 0)                        = 0
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7fe60336ca10) = 10191
close(4)                                = 0
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7fe60336ca10) = 10192
close(3)                                = 0
wait4(10191, [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 10191
wait4(10192, [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 10192
== process 10191
dup2(4, 1)                              = 1
close(4)                                = 0
close(3)                                = 0
execve("/usr/bin/ls", ["ls", "/etc"], 0x7ffff24f8c58 /* 200 vars */) = 0
== process 10192
dup2(3, 0)                              = 0
close(3)                                = 0
openat(AT_FDCWD, "hosts.txt", O_WRONLY|O_CREAT|O_TRUNC, 0644) = 3
dup2(3, 1)                              = 1
close(3)                                = 0
execve("/usr/bin/grep", ["grep", "^host"], 0x7ffff24f8c58 /* 200 vars */) = 0
```

This is the figure of the life-cycle section, step by step. The pipe got descriptors 3 (read end) and 4 (write end). The first child made 4 its standard output and closed both originals; the second made 3 its standard input, then opened `hosts.txt`, which got the lowest free number, 3 again, and made it its standard output. The shell closed its copy of the write end after the first fork and its copy of the read end after the second, then waited for both children. Without the `close(4)` in the shell, `grep` would never see end-of-file.

### The process tree from /proc

`ptree.py` reads `/proc/*/stat` (name, state, parent PID and number of threads of every process) and draws the tree. `tree-demo.sh` starts a small family (a `sleep`, a Python process with three extra threads, and a subshell with a child of its own) and then draws the tree below its own shell:

```console
$ sh tree-demo.sh
sh(11138) S
├─ sleep(11139) S
├─ python3(11140) S [4 threads]
├─ sh(11141) S
│  └─ sleep(11144) S
└─ python3(11153) R
$ python3 ptree.py | grep -v "^[ │├└]"        # only the roots
process_api(1) S [6 threads]
kthreadd(2) S
```

The last child, `python3(11153)` in state `R`, is `ptree.py` itself, reading `/proc` while it runs. The whole tree has two roots, PIDs 1 and 2, whose parent is 0. On this machine PID 1 is not `systemd` but the cloud sandbox's own small init program (`process_api`); `kthreadd` is the parent of all kernel threads.

### Threads are tasks

`threads.c` starts three threads. Each increments a global counter under a mutex, a thread-local counter (`__thread int mine`) and a local variable on its stack, a thousand times, and prints its IDs and addresses:

```console
$ gcc -O2 -pthread -o threads threads.c
$ ./threads
thread 0: pid 24450 tid 24451  &shared 0x5617f2382068  &mine 0x7f77441ff6bc  &local 0x7f77441fee94  mine = 1000
thread 1: pid 24450 tid 24452  &shared 0x5617f2382068  &mine 0x7f77439fe6bc  &local 0x7f77439fde94  mine = 1000
thread 2: pid 24450 tid 24453  &shared 0x5617f2382068  &mine 0x7f77431fd6bc  &local 0x7f77431fce94  mine = 1000
main    : pid 24450 tid 24450  shared = 3000, main's own mine = 0
```

All four report the same PID but different TIDs; the main thread's TID equals the PID. `shared` has one address and reached 3000. `mine` has a different address in every thread, each copy counted to 1000, and the main thread's copy is still 0. The stacks (and with them the TLS blocks, which glibc places at the top of each thread's stack) are `0x801000` bytes apart: 8 MiB of stack plus a 4 KiB guard page. The thread creation itself:

```console
$ strace -f -qq -e trace=clone3 ./threads 2>&1 > /dev/null | head -1
clone3({flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID, child_tid=0x7f8da69ff990, parent_tid=0x7f8da69ff990, exit_signal=0, stack=0x7f8da61ff000, stack_size=0x7fff80, tls=0x7f8da69ff6c0} => {parent_tid=[5496]}, 88) = 5496
```

Compare with the `clone()` of `fork()` above: a thread shares the address space, the file system information, the descriptor table and the signal handlers, joins the thread group, gets its own stack (`stack_size` is just under 8 MiB) and TLS block, and sends no signal when it ends (`exit_signal=0`). From outside, `tasks.sh` looks at a Python process with four threads:

```console
$ sh tasks.sh
$ ps -L -o pid,lwp,nlwp,stat,comm -p 24470
  PID   LWP NLWP STAT COMMAND
24470 24470    4 Sl   python3
24470 24472    4 Sl   python3
24470 24473    4 Sl   python3
24470 24474    4 Sl   python3
$ ls /proc/24470/task
24470
24472
24473
24474
$ grep -E '^(Tgid|Pid|Threads)' /proc/24470/status
Tgid:	24470
Pid:	24470
Threads:	4
$ grep -E '^(Tgid|Pid)' /proc/24470/task/24474/status
Tgid:	24470
Pid:	24474
```

`ps` calls the threads "light-weight processes" (`LWP` is the TID, `NLWP` the number of threads; the `l` in `Sl` means multithreaded). Inside the kernel, the `Pid` field of each task is its TID, and `Tgid` is what user space calls the PID.

### Creating processes and threads: what it costs

`spawncost.c` measures, per creation: a thread (`pthread_create` and `pthread_join`), a process that exits at once (`fork` or `vfork`, `_exit`, `waitpid`), and a process that runs `/bin/true` (with `fork` and `exec`, `vfork` and `exec`, or `posix_spawn`). With an argument it first allocates and touches that many MiB, to make the parent big:

```console
$ gcc -O2 -pthread -o spawncost spawncost.c
$ ./spawncost
pthread_create + join                   36.8 us
fork + _exit + wait                    131.5 us
vfork + _exit + wait                    37.2 us
fork + exec /bin/true + wait          1111.2 us
vfork + exec /bin/true + wait         1018.0 us
posix_spawn /bin/true + wait           966.0 us
$ ./spawncost 1024
parent has touched 1024 MiB
pthread_create + join                   38.3 us
fork + _exit + wait                  20135.3 us
vfork + _exit + wait                    44.0 us
fork + exec /bin/true + wait         21334.7 us
vfork + exec /bin/true + wait         1061.1 us
posix_spawn /bin/true + wait          1026.4 us
```

For a small parent, a thread costs about 37 µs, a process about 3.6 times as much (132 µs). Running a new program costs about 1 ms whichever way it is started: `execve`, the dynamic loader mapping the C library, and the start-up of `/bin/true` dominate. With 1 GiB of memory in the parent, everything that copies the address space becomes expensive: `fork` now takes 20 ms, 150 times as long, because the kernel must copy the page-table entries of 262,144 pages, write-protect them for copy-on-write, and tear them down again when the child exits, about 76 ns per page. `vfork` and `posix_spawn` do not copy anything and stay at their old cost; the thread is unaffected too. This is the measurement behind the criticism of `fork` (Baumann et al., 2019, report about 0.5 ms for `posix_spawn` on their machine, regardless of the parent's size). glibc's `posix_spawn` uses `clone3()` in the `vfork` style:

```console
$ gcc -O2 -o spawn1 spawn1.c
$ strace -f -qq -e signal=none -e trace=clone3,execve ./spawn1
execve("./spawn1", ["./spawn1"], 0x7ffee709a4c0 /* 200 vars */) = 0
clone3({flags=CLONE_VM|CLONE_VFORK|CLONE_CLEAR_SIGHAND, exit_signal=SIGCHLD, stack=0x7f38f1882000, stack_size=0x9000}, 88 <unfinished ...>
[pid  5469] execve("/bin/true", ["true"], 0x7ffc249a95a8 /* 200 vars */ <unfinished ...>
[pid  5468] <... clone3 resumed>)       = 5469
[pid  5469] <... execve resumed>)       = 0
```

The child shares the parent's memory (`CLONE_VM`) but runs on its own 36 KiB stack, with all signal handlers reset (`CLONE_CLEAR_SIGHAND`), so that a handler of the parent cannot run in the borrowed address space. `CLONE_VFORK` suspends the parent: its `clone3` returns only after the child's `execve` has replaced the borrowed address space with a new one.

### A signal interrupts a system call

`sigdemo.c` blocks in `read()` on an empty pipe. A child will write into the pipe after 2 seconds, but an alarm signal arrives after 1 second. The handler only sets a flag and calls `write()`, both async-signal-safe:

```console
$ gcc -O2 -o sigdemo sigdemo.c
$ ./sigdemo
no SA_RESTART: read() from an empty pipe, alarm in 1 s, data in 2 s
  handler: SIGALRM arrived
  read() returned -1 after 1.0 s, errno = Interrupted system call, got_alarm = 1
$ ./sigdemo restart
SA_RESTART: read() from an empty pipe, alarm in 1 s, data in 2 s
  handler: SIGALRM arrived
  read() returned 4 after 2.0 s, got_alarm = 1
```

In both cases the signal woke the process from its interruptible sleep, and the handler ran in the middle of `read()`. Without `SA_RESTART`, `read()` then failed with `EINTR` after 1 second, and a careful program would have to call it again; with `SA_RESTART`, the kernel restarted it after the handler, and it returned the 4 bytes when they arrived after 2 seconds.

### IPC: latency and throughput

`ipcbench.c` compares a pipe, a Unix domain socket (`socketpair`), a POSIX message queue and POSIX shared memory between a parent and a child. *Latency*: 100,000 round trips of one byte; for shared memory, the two sides wait for each other either with process-shared semaphores, which sleep, or by spinning on an atomic flag. *Throughput*: 1 GiB in 64 KiB pieces, which the receiver copies into its own buffer (8 KiB pieces for the message queue, the default maximum message size; for shared memory a ring of four 64 KiB slots with semaphores). The argument pins both processes to one CPU, or to two different CPUs:

```console
$ gcc -O2 -pthread -o ipcbench ipcbench.c
$ ./ipcbench same
parent on CPU 0, child on CPU 0
latency (1 byte there and back, 100000 times):
pipe                             2.91 us per round trip
Unix domain socket               6.16 us per round trip
message queue                    2.97 us per round trip
shared memory + semaphores       2.81 us per round trip
shared memory, spinning      (skipped: both on one CPU)
throughput (1 GiB, 64 KiB per write):
pipe (64 KiB buffer)             3.60 GB/s
pipe (1 MiB buffer)              5.28 GB/s
Unix domain socket               8.53 GB/s
message queue                    4.30 GB/s (8 KiB messages)
shared memory + semaphores      14.23 GB/s
$ ./ipcbench split
parent on CPU 0, child on CPU 1
latency (1 byte there and back, 100000 times):
pipe                            33.33 us per round trip
Unix domain socket              31.87 us per round trip
message queue                   26.53 us per round trip
shared memory + semaphores      28.36 us per round trip
shared memory, spinning          0.20 us per round trip
throughput (1 GiB, 64 KiB per write):
pipe (64 KiB buffer)             2.09 GB/s
pipe (1 MiB buffer)              3.50 GB/s
Unix domain socket               4.18 GB/s
message queue                    3.59 GB/s (8 KiB messages)
shared memory + semaphores      12.95 GB/s
```

**Latency.** On one CPU, a round trip costs about 3 µs with any mechanism that sleeps (6 µs with the socket, whose code path is longer): each way, a `write`, a `read` and a context switch to the other process, so two switches per round trip (the [next lecture](../07-concurrency-deadlocks-scheduling/#the-cost-of-a-switch) measures 1.4 to 1.7 µs per switch, including the two system calls, on the same machine). On two CPUs, the same round trip costs 26 to 33 µs, ten times more, and the mechanism hardly matters. The time goes into waking a process on the other CPU: the waker must send an inter-processor interrupt, and on this virtual machine the idle virtual CPU has halted, so the hypervisor must first schedule it again, which is far slower than on real hardware. Spinning avoids sleeping altogether: 0.2 µs per round trip, the time for a cache line to travel between two cores and back, but at the price of keeping both CPUs 100% busy while they wait. Low-latency systems (trading, packet processing) do exactly this, on dedicated cores.

**Throughput.** Shared memory is the clear winner at 13 to 14 GB/s, even though the test copies the data twice in user space, because most slot hand-overs need no system call at all (a semaphore enters the kernel only when it must sleep or wake someone). Every other mechanism makes two system calls and two copies through the kernel per piece, and must sleep and wake the other side whenever the kernel buffer is full or empty. That is why buffer size matters: the default pipe holds only 64 KiB, exactly one piece, so the two sides alternate; with a 1 MiB pipe, or a Unix socket (whose default send buffer here is 208 KiB), more data are in flight and fewer wake-ups are needed. The message queue is limited by its 8 KiB messages: eight times as many system calls. In the run shown, every mechanism was faster on one CPU, where the data stay in that core's caches and no wake-up crosses CPUs; this is a tendency, not a rule. Results vary from run to run by up to a factor of two, depending on where the scheduler happens to place the processes.

### A process seen through /proc

`procfs.sh` starts `sleep 100` with its input from `/dev/null` and its output and errors redirected into a file, and reads its `/proc` directory:

```console
$ sh procfs.sh
$ grep -E '^(Name|State|PPid|Uid|Threads|VmRSS|voluntary)' /proc/26308/status
Name:	sleep
State:	S (sleeping)
PPid:	26307
Uid:	0	0	0	0
VmRSS:	    1764 kB
Threads:	1
voluntary_ctxt_switches:	1
$ ls -l /proc/26308/fd | awk 'NR > 1 {print $9, $10, $11}'
0 -> /dev/null
1 -> /tmp/sleep-out.txt
2 -> /tmp/sleep-out.txt
$ readlink /proc/26308/exe /proc/26308/cwd; tr '\0' ' ' < /proc/26308/cmdline; echo
/usr/bin/sleep
/tmp
sleep 100
$ cat /proc/26308/wchan; echo
hrtimer_nanosleep
$ grep -E 'Max (open files|processes|stack)' /proc/26308/limits
Max stack size            8388608              unlimited            bytes
Max processes             32045                32045                processes
Max open files            20000                20000                files
```

Every part of the kernel's record from the first figure appears as a file: the identity and the state (`S`, sleeping, after one voluntary context switch), the credentials (real, effective, saved and file-system UID, all 0 for root), the memory in use (1.7 MiB resident), the descriptor table with the redirections the shell made, the program, the current directory and the arguments, the kernel function in which the process sleeps (a high-resolution timer) and the resource limits.

### Tracing with strace

`strace -c` gives a profile of the system calls of a whole program. `find` walking a directory tree:

```console
$ strace -c -S calls find /usr/share -name "*.txt" > /dev/null
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 28.35    0.069456           2     32892           fcntl
 24.15    0.059170           2     26197           close
 18.86    0.046205           3     13485           getdents64
 14.38    0.035225           2     13476           newfstatat
  5.97    0.014625           2      6779           fstat
  7.85    0.019234           2      6779           openat
  0.13    0.000317           9        34           brk
  0.08    0.000193          11        17           mmap
  0.07    0.000164          23         7           read
  0.03    0.000063          12         5           mprotect
  0.00    0.000008           2         4           write
  0.01    0.000027           9         3         3 ioctl
```

`find` opens each directory (6,779 `openat` calls), reads its entries in batches with `getdents64` (about two calls per directory: one that returns entries, one that returns nothing), and looks at entries with `newfstatat`; the many `fcntl` and `close` calls come from how it manages the directory descriptors. `-T` shows the time spent in each call:

```console
$ strace -T -e trace=openat,read,write,close cat /etc/hostname > /dev/null
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3 <0.000025>
close(3)                                = 0 <0.000053>
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC) = 3 <0.000031>
read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0\220\243\2\0\0\0\0\0"..., 832) = 832 <0.000030>
close(3)                                = 0 <0.000021>
openat(AT_FDCWD, "/etc/hostname", O_RDONLY) = 3 <0.000030>
read(3, "vm\n", 131072)                 = 3 <0.000023>
write(1, "vm\n", 3)                     = 3 <0.000020>
read(3, "", 131072)                     = 0 <0.000036>
close(3)                                = 0 <0.000021>
close(1)                                = 0 <0.000018>
close(2)                                = 0 <0.000029>
+++ exited with 0 +++
```

`cat` itself makes only seven of these calls: open, read the 3 bytes, write them, read again to find end-of-file, close. The first five belong to the dynamic loader, which finds the C library through the cache file `/etc/ld.so.cache` and reads its ELF header. (Under tracing, each call appears to take 20 to 50 µs; most of that is the tracing itself.) Even a tiny program makes many calls before `main`:

```console
$ strace ./hello3 2>&1 > /dev/null | head -12
execve("./hello3", ["./hello3"], 0x7ffe71939800 /* 200 vars */) = 0
brk(NULL)                               = 0x558a4416c000
mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7f7122505000
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
fstat(3, {st_mode=S_IFREG|0644, st_size=54375, ...}) = 0
mmap(NULL, 54375, PROT_READ, MAP_PRIVATE, 3, 0) = 0x7f71224f7000
close(3)                                = 0
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0\220\243\2\0\0\0\0\0"..., 832) = 832
pread64(3, "\6\0\0\0\4\0\0\0@\0\0\0\0\0\0\0@\0\0\0\0\0\0\0@\0\0\0\0\0\0\0"..., 784, 64) = 784
fstat(3, {st_mode=S_IFREG|0755, st_size=2129424, ...}) = 0
$ strace ./hello3 2>&1 > /dev/null | wc -l
42
```

Of the 42 lines (41 system calls and the exit line), the program's own requests are the six `write` calls, the few calls with which `printf` set up its buffer (`fstat` and `ioctl` to find out that the output is not a terminal; `getrandom` and `brk` when `malloc` first prepared the heap for the buffer's memory), and the final `exit_group`. The rest is `execve`, the loader mapping the C library with `mmap` and protecting it with `mprotect`, and the C library setting up TLS (`arch_prctl`), the thread ID address and its other per-thread data.

### Where is a process waiting?

`waiting.sh` starts `sleep 30` and asks where it waits, first through `/proc`, then with `gdb`, then through `/proc` again:

```console
$ sh waiting.sh
$ cat /proc/26610/wchan; echo; cut -d' ' -f1-3 /proc/26610/syscall
hrtimer_nanosleep
230 0x0 0x0
$ gdb -q -p 26610 -batch -ex bt 2>/dev/null | grep '^#' | cut -d'(' -f1
#0  0x00007f70e28ecb7a in __GI___clock_nanosleep
#1  0x00007f70e28f9b27 in __GI___nanosleep
#2  0x000055e8f4d64a7f in ??
#3  0x00007f70e282a1ca in __libc_start_call_main
#4  0x00007f70e282a28b in __libc_start_main_impl
#5  0x000055e8f4d64ba5 in ??
$ cat /proc/26610/wchan; echo; cut -d' ' -f1-3 /proc/26610/syscall
__do_sys_restart_syscall
219 0x0 0x0
```

The kernel's view: the process sleeps in the kernel function `hrtimer_nanosleep`, inside system call 230 (`clock_nanosleep`). The user-space view from `gdb`: the C library's `nanosleep` wrapper, called from `sleep`'s `main` (shown as `??`, because the installed `sleep` has no symbol table), called from the C library's start-up code. Afterwards the process waits in system call 219, `restart_syscall`: attaching the debugger interrupted the sleep, like a signal, and the kernel resumed it with a special system call that sleeps only for the *remaining* time. Observing a process changed it, which is worth remembering whenever a tracer or debugger is attached to a production process.

### perf and bpftrace

`perf` and `bpftrace` are not installed on this machine, so no output is shown; [lab exercise 9](#lab-exercises) uses them on a machine where they are available. Typical uses:

```console
$ perf stat -e task-clock,context-switches,cpu-migrations,page-faults ./spawncost 256
$ perf record -g ./ipcbench split; perf report
$ perf trace -s ./minish < minish-demo.txt
# bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'
# bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf("%d %s -> %s\n", pid, comm, str(args->filename)); }'
# bpftrace -e 'tracepoint:sched:sched_process_fork { printf("%s (%d) forked %d\n", args->parent_comm, args->parent_pid, args->child_pid); }'
```

The first counts the events of the cost measurement; the second records where `ipcbench` spends its time, in user code and in the kernel; the third is `perf`'s faster equivalent of `strace -c`. The `bpftrace` lines (run as root; `#` is root's prompt) count system calls per program name across the whole system until Ctrl-C, print every program started anywhere on the system (like the `execsnoop` tool), and print every fork.

<details>
<summary><b>Explained simply:</b> ASLR, C calling convention, cancellation, ECHILD, LWP, guard page, context switch, inter-processor interrupt, spinning, profile, wchan, symbol table</summary>

- **ASLR** (address space layout randomisation): putting the parts of a program at random addresses at every start, to make attacks harder.
- **C calling convention:** the agreed way in which a function receives its arguments, here in registers `rdi`, `rsi`, `rdx` and so on.
- **Cancellation:** a way for one thread to ask another to stop; some system calls are places where this request is checked.
- **ECHILD:** the error "you have no child to wait for".
- **LWP** (light-weight process): an old name for a kernel-level thread; in `ps` it is the thread's ID.
- **Guard page:** an unmapped page below each thread stack, so that a stack that grows too far causes a fault instead of silently overwriting other memory.
- **Context switch:** the CPU stops running one process or thread and starts running another, after saving the first one's registers so that it can continue later.
- **Inter-processor interrupt:** an interrupt one CPU core sends to another, for example "wake up, there is work for you".
- **Spinning:** waiting by checking a value again and again in a loop, without going to sleep.
- **Profile:** a summary of where a program spends its time or how often it does something.
- **wchan** ("wait channel"): the kernel function in which a sleeping process is waiting.
- **Symbol table:** the list of function names stored in a program file; without it a debugger shows only addresses (`??`).

</details>

## Lab exercises

1. **Address space.** Run `layout` several times, then with address randomisation switched off for one run (`setarch -R ./layout`): which addresses stay the same? Change the large `malloc` to 64 KiB, 127 KiB, 128 KiB and 256 KiB: where does the switch from the heap to a separate mapping happen? Add a `static int` inside `main`, a string literal and a `const` global, and find their regions. Why is the string literal not in the data region?
2. **System calls by hand.** Extend `hello3.c` with a function `raw_getpid()` (number 39, no arguments) and end the program with a bare `exit_group(7)` (number 231) instead of `return`. Check with `echo $?` and with `strace`. Then run `strace -c` on `ls -l /usr/bin > /dev/null` and on `python3 -c pass`: how many system calls does each make, which are the three most frequent, and which of them are made before `main`?
3. **The price of a system call.** Run `sccost` five times, and once under `taskset -c 0`. Add `getppid()` and `sched_yield()` to the program. On a laptop or a physical Linux machine, compare the results with this lecture's; then look at `/sys/devices/system/cpu/vulnerabilities/` on both machines. Which mitigations could explain a difference?
4. **Extend minish.** Add (a) `2>` redirection, (b) background commands with `&`: do not wait for them, but reap finished ones with `waitpid(-1, &st, WNOHANG)` before each prompt, and (c) Ctrl-C handling: the shell ignores `SIGINT`, the children restore the default action before `exec`. Start `sleep 5 &` and check with `ps -o pid,stat,cmd` that no zombie is left after it ends. Without step (b)'s reaping, what do you see?
5. **The cost of fork.** Run `spawncost` with 0, 256, 512, 1024 and 2048 MiB and plot the `fork` time against the size. Is it linear? Compute the cost per page. Then add `madvise(p, size, MADV_HUGEPAGE)` after the `malloc` (transparent huge pages are in `madvise` mode on many systems) and repeat. What changes, and why?
6. **Threads.** (a) Remove the mutex from `threads.c`, raise the loop count to ten million and run it several times: what happens to `shared`, and why not to `mine`? (b) Print `&errno` in each thread. (c) Let thread 0 call `fork()` and let the child print the number of entries in `/proc/self/task`: how many threads does the child have? What would happen if another thread held a mutex at the moment of the fork?
7. **IPC.** Run `ipcbench` without an argument several times, and with `same` and `split`. Then add two variants: a FIFO created with `mkfifo()` (open it in both processes), and a "zero-copy" shared-memory variant in which the producer writes directly into the slot (`memset`) and the consumer only reads one byte per cache line. Explain the differences. Why does the spinning version need two CPUs?
8. **Signals.** Write a program that counts `SIGUSR1` signals in a handler and sleeps, and send it 10,000 signals as fast as possible from another program (`kill()` in a loop). How many arrive? Repeat with the real-time signal `SIGRTMIN`, installed with `sigaction`. Explain the difference. Then install a handler that calls `printf` and send signals while the main loop also calls `printf`: can you make it misbehave?
9. **Observability with ltrace, perf and bpftrace** (on a Linux machine where you are root and can install packages, e.g. `sudo apt install ltrace linux-tools-common linux-tools-$(uname -r) bpftrace`; no outputs are given here, since the lecture's machine does not have these tools). Run `ltrace -c ./hello3` and `ltrace -e malloc+free ./layout`: which library calls appear, and why do `write` and `printf` appear here although `strace` shows `write` only? Run the `perf` and `bpftrace` commands of the [perf and bpftrace demo](#perf-and-bpftrace). While the `execve` one-liner runs, open a new terminal: which programs does your shell start before the first prompt? Compare the overhead of `strace -c` and `perf trace -s` on `./sccost 100000`.

## Review questions

1. What is the difference between a program and a process? Give an example of one program running as several processes, and one process running several programs one after the other.
2. Name the regions of a process's address space and say what each contains. Why does the BSS take no space in the executable file? In the `layout` demo, why did the 100-byte block come from the heap but the 1 MiB block from a mapping of its own?
3. What does the kernel keep about a process outside its address space? Why must this record be in kernel memory?
4. Explain the difference between the API and the system-call interface. Give an example of a library function that makes no system call, one that makes one, and one that sometimes makes one and sometimes none.
5. Describe what happens on x86-64 Linux, step by step, when a program calls `write(1, buf, 3)`: registers, instruction, kernel entry, dispatch, return, and how an error reaches `errno`.
6. A function call cost about 2 ns and `getpid()` about 125 ns. Where does the difference come from? What is the vDSO, why was `clock_gettime()` five times cheaper through it, and why can `write()` not use it?
7. Under `strace`, `getpid()` took about 8.5 µs. Why? What does this mean for performance measurements made with `strace`?
8. `fork()` "returns twice". Explain. A program prints a line with `printf` (without a newline at the end), then calls `fork()`, and its output goes to a file. What appears in the file, and how is it avoided?
9. What does a process keep across `execve()`, and what is replaced? Why are `fork` and `exec` separate calls in Unix, and what is the main criticism of this design?
10. What happens to a child whose parent ends first? In the `orphan` demo, why did `waitpid(-1)` return −1 in the first run and the child's PID in the second? Who uses subreapers, and why?
11. List the system calls `minish` makes, in the parent and in the child, for `sort <in.txt >out.txt`. Why must `cd` be a built-in command?
12. In the pipeline `ls /etc | grep ^host`, what goes wrong if the shell forgets to close its copy of the pipe's write end? And if the first child forgets to close the read end?
13. With a 1 GiB parent, `fork` with `exec` took 21 ms, but `vfork` with `exec` and `posix_spawn` about 1 ms. Explain the difference. Why is `vfork` dangerous, and how does `posix_spawn` avoid the danger?
14. What do the threads of a process share, and what does each thread own? Why must `errno` be thread-local? What did the `threads` demo show about `__thread` variables?
15. Compare the N:1, 1:1 and M:N threading models: what happens when a thread blocks in a system call, and can the threads use several cores? Which model do Linux's pthreads use, and how do Go and Java 21 run hundreds of thousands of concurrent tasks?
16. Which `clone()` flags turn a new task into a thread rather than a process? What is a thread group, and what do `getpid()` and `gettid()` return in the main thread and in another thread?
17. Why may a signal handler not call `printf` or `malloc`? What should a handler do instead? In `sigdemo`, what was the difference between the runs with and without `SA_RESTART`?
18. Compare a pipe, a Unix domain socket, a message queue and shared memory: direction, message boundaries, use by unrelated processes, number of copies, and who synchronises. In the measurement, why did the latency of all sleeping mechanisms jump from about 3 µs to about 30 µs when the processes were on different CPUs, and why was shared memory the fastest for throughput?
19. Which tool would you use to find out (a) which configuration files a program tries to open, (b) where a busy production server spends its CPU time, (c) which process on a server starts thousands of short-lived programs per minute? Why is `strace` a poor choice for (b) and (c)?

<details>
<summary><strong>Answer key (for instructors)</strong></summary>

1. A program is a passive file of code and data; a process is a program in execution with its own address space, registers, open files and kernel record. Several processes: ten users running `bash`, or a web server's worker processes. Several programs in one process: a shell's child starts as a copy of the shell and then `exec`s `ls`; `exec` keeps the PID.
2. Text (machine code, read-only and executable), data (initialised globals), BSS (zero-initialised globals), heap (`malloc`, grows up with `brk`), memory-mapped area (shared libraries, mapped files, large `malloc` blocks, thread stacks, vDSO), stack (locals, return addresses, grows down), and the protected kernel half. The BSS is all zeros, so the file records only its size; the kernel provides zero-filled pages. glibc serves small requests from the heap and requests above its `mmap` threshold (128 KiB by default) with a separate anonymous mapping, which can be returned to the kernel as a whole when freed.
3. PID and parent, state and scheduling data, saved registers, the memory map and page tables, the descriptor table, credentials, signal handlers and masks, current and root directory, limits, namespaces, accounting, and a kernel stack. If the process could change it, it could raise its own privileges (credentials), escape its memory limits (page tables), or take the CPU (scheduling data); the kernel can trust only what the process cannot write.
4. The API is the set of library functions programmers call (C library, POSIX); the system-call interface is the set of numbered kernel entry points. No system call: `strlen`, `memcpy`. One: `write()`, `getpid()`. Sometimes: `printf` (only when the buffer is flushed), `malloc` (only when its pool must grow), `clock_gettime` (through the vDSO normally none).
5. The arguments are in `rdi` (1), `rsi` (buf), `rdx` (3); the wrapper loads 1 into `rax` and executes `syscall`, which saves the return address in `rcx` and the flags in `r11`, switches to kernel mode and jumps to the entry point from the MSR. `entry_SYSCALL_64` switches to the kernel stack, saves the registers, and calls `sys_call_table[1]`, the write implementation, which goes through the VFS to the terminal, pipe or file. The result (bytes written, or −errno) goes into `rax`; `sysret` returns to user mode. The wrapper checks whether `rax` is in −4095…−1; if so it stores −rax in `errno` and returns −1.
6. The system call needs the mode switch, saving and restoring registers, a stack switch, the entry checks and speculative-execution mitigations; a function call is a jump and a return. The vDSO is code the kernel maps into every process, with a data page the kernel updates; `clock_gettime` computes the time from that page and the time-stamp counter without entering the kernel. `write()` changes state outside the process (a file, a pipe) and needs permission checks and device access, which only the kernel may do.
7. `strace` uses `ptrace`: at every system-call entry and exit the kernel stops the process, wakes the tracer, which reads the registers and memory, prints, and lets the process continue: four context switches and several system calls of the tracer per traced call. Measurements under `strace` are distorted (system-call-heavy code looks far slower than it is); use it to find *what* a program does, not *how fast*, and use `perf` or eBPF for timing.
8. The call creates a child; from then on two processes execute the same code after the call, and the kernel arranges a different return value in each: the child's PID in the parent, 0 in the child. Output to a file is fully buffered, so the line is still in the buffer at the fork; the buffer is copied, and both processes flush it at exit: the line appears twice. Avoid it with `fflush(stdout)` before `fork()`, and by ending children that do not `exec` with `_exit()`.
9. Kept: PID, parent, open descriptors without `O_CLOEXEC`, current and root directory, umask, limits, signal mask and ignored signals, credentials (unless setuid/setgid). Replaced: text, data, heap, stack and mappings; handled signals are reset to their default action. Separate calls let the child adjust its environment (redirections, closing descriptors, changing directory or credentials) with ordinary system calls between them. Criticism (Baumann et al., 2019): `fork` copies the whole process (slow for large processes, insecure by default), does not mix with threads, and complicates the kernel; `posix_spawn` should be the normal way to start programs.
10. It becomes an orphan and is reparented to PID 1 (or to the nearest subreaper ancestor), which reaps it when it ends. In the first run the grandchild belonged to PID 1, so the grandparent had no child left (`ECHILD`); in the second the grandparent was a subreaper and adopted it. Service managers (`systemd --user`) and container runtimes use subreapers to keep track of, and reap, every process they started, even after intermediate processes exit.
11. Parent: `clone` (fork), then `wait4`. Child: `openat("in.txt", O_RDONLY)` = 3, `dup2(3, 0)`, `close(3)`, `openat("out.txt", O_WRONLY|O_CREAT|O_TRUNC)` = 3, `dup2(3, 1)`, `close(3)`, `execve("/usr/bin/sort", …)` (after unsuccessful `execve`s for earlier `PATH` directories). `cd` must change the shell's own current directory; a child's `chdir` would change only the child's, which ends at once.
12. If the shell keeps the write end open, `grep` never sees end-of-file after `ls` finishes, because a writer still exists; `grep` waits for ever and the shell waits for `grep`. If the first child keeps the read end open, nothing visibly breaks while `grep` reads; but if `grep` exited early, `ls` would not get `SIGPIPE`/`EPIPE` and could block on a full pipe for ever, since a reader (itself) still exists.
13. `fork` must copy the page tables of all 262,144 pages, write-protect them for copy-on-write, and tear them down at the child's exit (about 76 ns per page here); `exec` then throws them away. `vfork` and `posix_spawn` share the parent's address space until `exec`, so nothing is copied. `vfork` is dangerous because the child runs in the parent's memory: any change to variables, or returning from the function, corrupts the parent. glibc's `posix_spawn` runs the child on a separate small stack, resets all signal handlers, and executes only its own controlled code before `exec`.
14. Shared: code, globals, heap, memory map, open files, signal handlers, PID and credentials, current directory, limits. Own: TID, registers (PC, SP, flags), stack, TLS, signal mask, scheduling state. `errno` is set by one thread's failing call and read right after; a shared `errno` could be overwritten by another thread in between. The demo showed one address for `shared` but a different address of `mine` in every thread, each counting to 1000 independently, and the main thread's copy still 0.
15. N:1: a blocking call blocks all threads; only one core is used; switching is very cheap. 1:1: only the calling thread blocks; threads run in parallel; creation and switching go through the kernel. M:N: blocking is handled by the runtime, which runs other user threads on other kernel threads; parallel; cheap threads, complex runtime. Linux NPTL is 1:1. Go multiplexes goroutines (small growable stacks) onto a few OS threads; Java 21's virtual threads are mounted on carrier threads and unmounted when they block. Both are M:N at the language level, with the runtime controlling blocking operations.
16. `CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, `CLONE_SIGHAND` and `CLONE_THREAD` (plus `CLONE_SYSVSEM` and `CLONE_SETTLS`, and a separate stack). A thread group is the set of tasks of one process; its ID (TGID) is the TID of the first thread. In the main thread `getpid()` = `gettid()` = TGID; in another thread `getpid()` returns the TGID and `gettid()` its own TID (24450 and 24451 in the demo).
17. The handler may interrupt `printf` or `malloc` in the middle of changing their internal state, or while they hold a lock; calling them again can corrupt the state or deadlock. A handler should only set a `volatile sig_atomic_t` flag (or write a byte into a pipe) and return, leaving the work to the main program. Without `SA_RESTART`, `read()` failed with `EINTR` after 1 s; with it, the kernel restarted the call after the handler, and it returned the data after 2 s.
18. Pipe: one-way stream, related processes, 2 copies, kernel-synchronised. Unix socket: two-way stream or datagrams, unrelated processes by path, 2 copies, kernel-synchronised, can pass descriptors and credentials. Message queue: messages with priorities, unrelated by name, 2 copies, kernel-synchronised. Shared memory: no structure, unrelated by name, 0 copies, synchronised by the processes. On two CPUs each round trip includes two cross-CPU wake-ups (an inter-processor interrupt, and on this VM rescheduling a halted virtual CPU by the hypervisor), which dominate the cost whatever the mechanism; on one CPU only ordinary context switches are needed. Shared memory avoided the system calls and kernel copies and needed a semaphore wake-up only occasionally, so it reached 13–14 GB/s.
19. (a) `strace -e trace=openat,open,stat ./program` (or `-f` for children). (b) `perf record -g` (sampling) or a bpftrace/eBPF profiler. (c) A bpftrace one-liner on `syscalls:sys_enter_execve` or `sched:sched_process_fork`/`exec`, or `execsnoop`. `strace` stops the traced process at every system call (a slowdown of about 70 times was measured for cheap calls), which would cripple a busy server, and it can only follow processes it is attached to, not the whole system.

**Lab answers.** Lab 1: with `setarch -R`, all addresses repeat between runs; on this glibc, requests of 128 KiB and more (the default `M_MMAP_THRESHOLD`) get their own mapping (the threshold also adapts upwards after large blocks are freed); string literals and `const` globals are in the read-only data section (`.rodata`), mapped read-only next to the text, not in the writable data region; a `static` local is in data or BSS. Lab 2: `$?` is 7; `python3 -c pass` makes several hundred system calls, mostly `newfstatat`, `openat`, `read` and `mmap` while it imports its start-up modules; the loader's calls (`openat` of `ld.so.cache` and `libc.so.6`, `mmap`, `mprotect`) come before `main`. Lab 3: `getppid` costs the same as `getpid`; `sched_yield` costs more, as it enters the scheduler; on bare metal without a hypervisor the cost is often lower, and mitigations such as page-table isolation (on CPUs affected by Meltdown) or retpolines raise it. Lab 4: without reaping, each finished background job stays in state `Z` until the shell exits; the shell must ignore `SIGINT` so that Ctrl-C ends only the foreground child. Lab 5: roughly linear, about 70–80 ns per 4 KiB page on this machine; with huge pages the page tables have one entry per 2 MiB, 512 times fewer, so `fork` becomes much faster (if the kernel could actually allocate huge pages). Lab 6: (a) `shared` ends below the expected total (lost updates, the race condition of the next lecture's critical-section problem); `mine` is per thread, so there is nothing to race on; (b) each thread prints a different address; (c) the child has exactly one thread, the one that called `fork`; a mutex held by another thread would stay locked in the child for ever, so the child must only call async-signal-safe functions until `exec`. Lab 7: the FIFO behaves like the pipe; the zero-copy variant is faster still, because it saves both copies; spinning on one CPU wastes whole time slices, because the other side can only run after the spinner is preempted. Lab 8: standard signals do not queue, so many `SIGUSR1`s are merged and far fewer than 10,000 are counted; real-time signals queue (up to a limit, `RLIMIT_SIGPENDING`) and all arrive; `printf` in the handler can garble output or deadlock on the stdio lock, rarely but reproducibly with enough signals. Lab 9: `ltrace` shows calls into shared libraries, so it sees `printf` and the `write` wrapper (which are library functions), while `strace` sees only the kernel's `write`; the shell's start-up runs programs such as `lesspipe`, `dircolors` and the `command-not-found` helpers, depending on the distribution's profile scripts; `perf trace` adds far less overhead than `strace`, because it reads kernel tracepoints instead of stopping the process.

</details>

## References

Anderson, T. E., Bershad, B. N., Lazowska, E. D., & Levy, H. M. (1992). Scheduler activations: Effective kernel support for the user-level management of parallelism. *ACM Transactions on Computer Systems, 10*(1), 53–79. https://doi.org/10.1145/146941.146944

Arpaci-Dusseau, R. H., & Arpaci-Dusseau, A. C. (2023). *Operating systems: Three easy pieces* (Version 1.10). Arpaci-Dusseau Books. https://pages.cs.wisc.edu/~remzi/OSTEP/

Baumann, A., Appavoo, J., Krieger, O., & Roscoe, T. (2019). A fork() in the road. In *Proceedings of the Workshop on Hot Topics in Operating Systems (HotOS '19)* (pp. 14–22). ACM. https://doi.org/10.1145/3317550.3321435

Drepper, U., & Molnar, I. (2003). *The native POSIX thread library for Linux* [White paper]. Red Hat.

Gregg, B. (2019). *BPF performance tools: Linux system and application observability*. Addison-Wesley.

Kerrisk, M. (2010). *The Linux programming interface: A Linux and UNIX system programming handbook*. No Starch Press.

Linux man-pages project. (n.d.-a). *clone(2): Create a child process*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man2/clone.2.html

Linux man-pages project. (n.d.-b). *pipe(7): Overview of pipes and FIFOs*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man7/pipe.7.html

Linux man-pages project. (n.d.-c). *proc(5): Process information, system information, and sysctl pseudo-filesystem*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man5/proc.5.html

Linux man-pages project. (n.d.-d). *shm_overview(7): Overview of POSIX shared memory*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man7/shm_overview.7.html

Linux man-pages project. (n.d.-e). *signal-safety(7): Async-signal-safe functions*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man7/signal-safety.7.html

Linux man-pages project. (n.d.-f). *syscall(2): Indirect system call*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man2/syscall.2.html

Linux man-pages project. (n.d.-g). *unix(7): Sockets for local interprocess communication*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man7/unix.7.html

Linux man-pages project. (n.d.-h). *vdso(7): Overview of the virtual ELF dynamic shared object*. Retrieved October 8, 2026, from https://man7.org/linux/man-pages/man7/vdso.7.html

Love, R. (2010). *Linux kernel development* (3rd ed.). Addison-Wesley.

Pressler, R., & Bateman, A. (2023). *JEP 444: Virtual threads*. OpenJDK. https://openjdk.org/jeps/444

Ritchie, D. M., & Thompson, K. (1974). The UNIX time-sharing system. *Communications of the ACM, 17*(7), 365–375. https://doi.org/10.1145/361011.361061

Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating system concepts* (10th ed.). Wiley.

Stevens, W. R., & Rago, S. A. (2013). *Advanced programming in the UNIX environment* (3rd ed.). Addison-Wesley.

The Go Authors. (n.d.). *Effective Go*. The Go Programming Language. Retrieved October 8, 2026, from https://go.dev/doc/effective_go

## Further reading

Bovet, D. P., & Cesati, M. (2005). *Understanding the Linux kernel* (3rd ed.). O'Reilly.

Gregg, B. (2020). *Systems performance: Enterprise and the cloud* (2nd ed.). Addison-Wesley.

Tanenbaum, A. S., & Bos, H. (2015). *Modern operating systems* (4th ed.). Pearson.
