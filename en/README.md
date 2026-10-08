# Operating Systems

Lecture notes for a university Operating Systems course, with Linux (x86-64) examples and lab exercises. Each lecture lives in its own folder: the notes are in the folder's `README.md`, next to its figures (SVG) and the source files used in the labs.

The lectures are written for university students, but every abbreviation and technical term comes with a collapsible **Explained simply** box, so readers with only basic computer knowledge can follow too.

Magyar változat: [../hu/](../hu/)

| # | Lecture | Topics |
| --- | --- | --- |
| 1 | [Operating Systems Historic Evolution](01-historic-evolution/) | why operating systems exist: batch processing, the resident monitor, multiprogramming, virtual memory, time sharing, Multics and Unix, MS-DOS, networks and mobile devices; the roles and layers of an OS |
| 2 | [Quality, Commercial Aspects and the Enterprise Linux Ecosystem](02-quality-and-enterprise-linux/) | quality criteria and ISO/IEC 25010, MTTF/MTTR/MTBF and availability, SLI/SLO/SLA, the commercial model of open source, branch/fork/upstream/backport, Fedora, CentOS Stream, RHEL, AlmaLinux, Rocky Linux; risk matrix, capex vs opex and the cloud; the family's container images (UBI, RHEL images) and image mode |
| 3 | [Cognitive Ergonomics and Operating Systems UI](03-cognitive-ergonomics/) | cognitive ergonomics; OS interfaces from the command line to phones, watches, voice and headsets; colour (lightness vs hue, contrast, colour blindness), short-term memory and chunking, affordances and signifiers, Fitts and Hick–Hyman laws, recognition vs recall, expertise, affective computing, mutual gaze, the uncanny valley, ethorobotics |
| 4 | [The Fetch-Execute Cycle](04-fetch-execute-cycle/) | von Neumann architecture, CPU registers and buses, the instruction cycle, addressing modes, flags and jumps, memory permissions (NX), x86-64 and `gdb` |
| 5 | [Interrupts](05-interrupts/) | interrupt classes, user and kernel mode, interrupt processing, nested interrupts, the interrupt controller, interrupt latency, programmed I/O vs interrupts vs DMA, race conditions, test-and-set and semaphores, `/proc/interrupts` |
| 6 | [Concurrency, Deadlocks, Process States and Linux Scheduling](06-concurrency-deadlocks-scheduling/) | the critical-section problem, Peterson's algorithm and memory fences, atomics, spinlocks, mutexes and futexes, semaphores and producer–consumer, monitors, deadlock (Coffman conditions, prevention, banker's algorithm, detection), livelock and priority inversion, process states and the three schedulers, zombies, FIFO/SJF/SRTF/Round Robin, Linux scheduling classes, nice and EEVDF |
| 7 | [Two-Level Memories and Caches](07-two-level-memory-and-cache/) | the memory hierarchy, the two-level memory and its average access time, locality of reference, direct-mapped, fully associative and set-associative caches, valid and dirty bits, write-through and write-back, replacement (LRU, FIFO, aging, Bélády's OPT), line size, prefetching, coherence and false sharing, the page cache, cache-friendly loops |
| 8 | [Virtual Memory](08-virtual-memory/) | separation and relocation, internal and external fragmentation, paging, page tables and the page-table base register, valid and access-rights bits, x86-64 multi-level page tables, the TLB and huge pages, page faults, demand paging and copy-on-write, page replacement (FIFO, OPT, LRU, clock), Bélády's anomaly, working sets and thrashing, caches vs virtual memory |
| 9 | [File Systems](09-file-systems/) | hard disks and SSDs (geometry, access time, NAND flash, FTL, garbage collection, write amplification, TRIM), the storage stack and the VFS, inodes, block pointers and extents, directories (lists, htree, B+ trees), hard and symbolic links, allocation and fragmentation, journaling and copy-on-write, FAT16, ext4, XFS and NTFS taken apart |
| 10 | [Access Control: Permissions, ACLs and SELinux](10-access-control/) | subjects, objects and the reference monitor, defence in depth, Unix owner/group/others permissions and the first-match rule, r/w/x on directories, chmod, umask, setuid/setgid/sticky, root and capabilities, POSIX ACLs (mask, default ACLs), DAC vs MAC, SELinux contexts, type enforcement, booleans and labelling, AppArmor |
| 11 | [Virtualization and Containerization](11-virtualization-containerization/) | why virtualize, VM/370 to KVM, Popek–Goldberg requirements, sensitive and privileged instructions, trap-and-emulate, binary translation, paravirtualization, VT-x/AMD-V and VM exits, shadow page tables vs EPT/NPT, emulated, virtio and passthrough I/O, type 1 and type 2 hypervisors, KVM/QEMU/libvirt, live and nested virtualization; containers vs VMs, images, layers, registries and OCI, Containerfiles, volumes, Docker, Podman, Buildah, Skopeo; namespaces, cgroups, capabilities and seccomp, OverlayFS, runc/crun, rootless containers |

## Running the labs

The lab programs need a Linux machine (or WSL) with `gcc`, `binutils` (`as`, `ld`, `objdump`) and `gdb`. On Debian or Ubuntu:

```console
$ sudo apt install build-essential gdb
```

Lecture 6 also uses `strace`, Python 3 and (optionally) a Java JDK, and lecture 7 `valgrind` (`sudo apt install strace default-jdk valgrind`). Lecture 9 uses `e2fsprogs` (`debugfs`, `dumpe2fs`, `filefrag`), `dosfstools`, `xfsprogs` and `ntfs-3g` (`sudo apt install e2fsprogs dosfstools xfsprogs ntfs-3g`); its ext4 demos need root to mount image files. Lecture 10 needs root (it creates demo users) and the `libcap2-bin` and `acl` packages (`sudo apt install libcap2-bin acl`); its SELinux lab needs a Fedora, RHEL or AlmaLinux virtual machine. Lecture 11 needs root for its namespace, cgroup and overlay demos, and Podman (or Docker) for its container labs, ideally on Fedora, CentOS Stream, AlmaLinux or Rocky Linux (`sudo dnf install podman skopeo buildah`); its KVM lab needs a physical machine with Intel VT-x or AMD-V and QEMU (`sudo dnf install qemu-kvm libvirt virt-install`).

## Figures

The figures are plain SVG files and switch to dark colours automatically when GitHub is in dark mode. Each folder also holds the Python script (`make_*.py`) that generates its figures, so they can be edited and regenerated.

## License

See [LICENSE](../LICENSE).
