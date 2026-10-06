# Operating Systems

Lecture notes for a university Operating Systems course, with Linux (x86-64) examples and lab exercises. Each lecture lives in its own folder: the notes are in the folder's `README.md`, next to its figures (SVG) and the source files used in the labs.

| # | Lecture | Topics |
| --- | --- | --- |
| 1 | [The Fetch-Execute Cycle](01-fetch-execute-cycle/) | von Neumann architecture, CPU registers and buses, the instruction cycle, addressing modes, flags and jumps, memory permissions (NX), x86-64 and `gdb` |
| 2 | [Interrupts](02-interrupts/) | interrupt classes, interrupt processing, nested interrupts, programmed I/O vs interrupts vs DMA, race conditions, test-and-set and semaphores, `/proc/interrupts` |

## Running the labs

The lab programs need a Linux machine (or WSL) with `gcc`, `binutils` (`as`, `ld`, `objdump`) and `gdb`. On Debian or Ubuntu:

```console
$ sudo apt install build-essential gdb
```

## Figures

The figures are plain SVG files and switch to dark colours automatically when GitHub is in dark mode. Each folder also holds the Python script (`make_*.py`) that generates its figures, so they can be edited and regenerated.

## License

See [LICENSE](LICENSE).
