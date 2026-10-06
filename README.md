# Operating Systems

Lecture notes for a university Operating Systems course, with Linux (x86-64) examples and lab exercises. Each lecture lives in its own folder: the notes are in the folder's `README.md`, next to its figures (SVG) and the source files used in the labs.

The lectures are written for university students, but every abbreviation and technical term comes with a collapsible **Explained simply** box, so readers with only basic computer knowledge can follow too.

| # | Lecture | Topics |
| --- | --- | --- |
| 1 | [Operating Systems Historic Evolution](01-historic-evolution/) | why operating systems exist: batch processing, the resident monitor, multiprogramming, virtual memory, time sharing, Multics and Unix, MS-DOS, networks and mobile devices; the roles and layers of an OS |
| 2 | [The Fetch-Execute Cycle](02-fetch-execute-cycle/) | von Neumann architecture, CPU registers and buses, the instruction cycle, addressing modes, flags and jumps, memory permissions (NX), x86-64 and `gdb` |
| 3 | [Interrupts](03-interrupts/) | interrupt classes, user and kernel mode, interrupt processing, nested interrupts, the interrupt controller, interrupt latency, programmed I/O vs interrupts vs DMA, race conditions, test-and-set and semaphores, `/proc/interrupts` |
| 4 | [Quality, Commercial Aspects and the Enterprise Linux Family](04-quality-and-enterprise-linux/) | quality criteria and ISO/IEC 25010, MTTF/MTTR/MTBF and availability, SLI/SLO/SLA, the commercial model of open source, branch/fork/upstream/backport, Fedora, CentOS Stream, RHEL, AlmaLinux, Rocky Linux |

## Running the labs

The lab programs need a Linux machine (or WSL) with `gcc`, `binutils` (`as`, `ld`, `objdump`) and `gdb`. On Debian or Ubuntu:

```console
$ sudo apt install build-essential gdb
```

## Figures

The figures are plain SVG files and switch to dark colours automatically when GitHub is in dark mode. Each folder also holds the Python script (`make_*.py`) that generates its figures, so they can be edited and regenerated.

## License

See [LICENSE](LICENSE).
