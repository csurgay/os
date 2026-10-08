# Operációs rendszerek

Egyetemi operációsrendszer-kurzus előadásanyaga, linuxos (x86-64) példákkal és laborfeladatokkal. Minden előadás saját mappában van: a szöveg a mappa `README.md` fájljában, mellette az ábrák (SVG) és a laborokban használt forrásfájlok.

Az előadások egyetemi hallgatóknak készültek, de minden rövidítéshez és szakkifejezéshez tartozik egy lenyitható **Egyszerűen elmagyarázva** doboz, így alapszintű számítógépes ismeretekkel is követhetők.

English version: [../en/](../en/)

| # | Előadás | Témák |
| --- | --- | --- |
| 1 | [Az operációs rendszerek történeti fejlődése](01-historic-evolution/) | miért vannak operációs rendszerek: kötegelt feldolgozás, rezidens monitor, multiprogramozás, virtuális memória, időosztás, Multics és Unix, MS-DOS, hálózatok és mobileszközök; az operációs rendszer szerepei és rétegei |
| 2 | [Minőség, üzleti szempontok és az Enterprise Linux ökoszisztéma](02-quality-and-enterprise-linux/) | minőségi szempontok és az ISO/IEC 25010, MTTF/MTTR/MTBF és rendelkezésre állás, SLI/SLO/SLA, a nyílt forráskód üzleti modellje, branch/fork/upstream/backport, Fedora, CentOS Stream, RHEL, AlmaLinux, Rocky Linux; kockázati mátrix, capex és opex, felhő; a család konténer image-ei (UBI, RHEL image-ek) és az image mode |
| 3 | [Kognitív ergonómia és az operációs rendszerek felhasználói felülete](03-cognitive-ergonomics/) | kognitív ergonómia; OS-felületek a parancssortól a telefonokig, órákig, hangvezérlésig és headsetekig; szín (világosság és színezet, kontraszt, színtévesztés), rövid távú memória és tömbösítés, affordanciák és jelölők, Fitts- és Hick–Hyman-törvény, felismerés és felidézés, szakértelem, affektív számítástechnika, kölcsönös tekintet, a hátborzongató völgy, etorobotika |
| 4 | [Az utasítás-végrehajtási ciklus](04-fetch-execute-cycle/) | Neumann-architektúra, CPU-regiszterek és sínek, az utasításciklus, címzési módok, jelzőbitek és ugrások, memóriajogosultságok (NX), x86-64 és `gdb` |
| 5 | [Megszakítások](05-interrupts/) | megszakítási osztályok, felhasználói és kernelmód, a megszakítás feldolgozása, egymásba ágyazott megszakítások, a megszakításvezérlő, megszakítási késleltetés, programozott I/O, megszakítások és DMA, versenyhelyzetek, test-and-set és szemaforok, `/proc/interrupts` |
| 6 | [Párhuzamosság, holtpontok, folyamatállapotok és a Linux ütemezése](06-concurrency-deadlocks-scheduling/) | a kritikus szakasz problémája, Peterson algoritmusa és a memóriakorlátok, atomi műveletek, spinlockok, mutexek és futexek, szemaforok és a termelő–fogyasztó probléma, monitorok, holtpont (Coffman-feltételek, megelőzés, bankár-algoritmus, felismerés), livelock és prioritásinverzió, folyamatállapotok és a három ütemező, zombik, FIFO/SJF/SRTF/Round Robin, a Linux ütemezési osztályai, nice és EEVDF |
| 7 | [Kétszintű memóriák és gyorsítótárak](07-two-level-memory-and-cache/) | a memóriahierarchia, a kétszintű memória és átlagos elérési ideje, a hivatkozási lokalitás, direkt leképezésű, teljesen asszociatív és csoportasszociatív gyorsítótárak, érvényességi és dirty bit, write-through és write-back, csere (LRU, FIFO, öregítés, Bélády OPT algoritmusa), sorméret, előbetöltés, koherencia és hamis megosztás, a page cache, gyorsítótár-barát ciklusok |
| 8 | [Virtuális memória](08-virtual-memory/) | elválasztás és áthelyezés, belső és külső fragmentáció, lapozás, laptáblák és a laptábla-bázisregiszter, érvényességi és jogosultsági bitek, az x86-64 többszintű laptáblái, a TLB és a huge page-ek, laphibák, igény szerinti lapozás és copy-on-write, lapcsere (FIFO, OPT, LRU, óra), Bélády-anomália, munkahalmaz és vergődés, gyorsítótárak és virtuális memória összevetése |
| 9 | [Fájlrendszerek](09-file-systems/) | merevlemezek és SSD-k (felépítés, elérési idő, NAND flash, FTL, szemétgyűjtés, írásamplifikáció, TRIM), a tárolási verem és a VFS, inode-ok, blokkmutatók és extentek, könyvtárak (lista, htree, B+ fa), hard és szimbolikus linkek, foglalás és fragmentáció, naplózás és copy-on-write, a FAT16, az ext4, az XFS és az NTFS szétszedve |
| 10 | [Hozzáférés-szabályozás: jogosultságok, ACL-ek és SELinux](10-access-control/) | alanyok, objektumok és a referenciamonitor, mélységi védelem, a Unix tulajdonos/csoport/mindenki más jogosultságai és az első egyezés szabálya, r/w/x könyvtárakon, chmod, umask, setuid/setgid/sticky, a root és a capabilityk, POSIX ACL-ek (maszk, alapértelmezett ACL-ek), DAC és MAC, SELinux contextek, type enforcement, booleanok és címkézés, AppArmor |
| 11 | [Virtualizáció – Konténerizáció](11-virtualization-containerization/) | miért virtualizálunk, a VM/370-től a KVM-ig, a Popek–Goldberg-feltételek, érzékeny és privilegizált utasítások, trap-and-emulate, binary translation, paravirtualizáció, VT-x/AMD-V és VM exitek, shadow laptáblák és EPT/NPT, emulált, virtio- és passthrough I/O, 1-es és 2-es típusú hypervisorok, KVM/QEMU/libvirt, live migration és beágyazott virtualizáció; konténerek és virtuális gépek, image-ek, rétegek, registryk és OCI, Containerfile, volume-ok, Docker, Podman, Buildah, Skopeo; namespace-ek, cgroupok, capabilityk és seccomp, OverlayFS, runc/crun, rootless konténerek |
| 12 | [Mobil, viselhető és beágyazott operációs rendszerek](12-mobile-wearable-embedded/) | tervezési célok a szerverektől a mikrovezérlőkig; Android (GKI, Binder, HAL-ok és Treble, ART és Zygote, az alkalmazások sandboxa, a folyamatok fontossága és az `oom_score_adj`, lmkd PSI-vel, zram, Doze és App Standby); iOS (XNU, kódaláírás, sandbox és entitlementek, jetsam, Secure Enclave); energia (DVFS, idle állapotok, race to idle, big.LITTLE és energiatudatos ütemezés, wakelockok, radio tail, thermal throttling); f2fs, fájlalapú titkosítás, verified boot, A/B és virtual A/B update, Mainline; viselhető eszközök; mikrovezérlők és MPU-k, rate-monotonic és EDF ütemezés, prioritásöröklés, RTOS-ek, TinyOS és Contiki, beágyazott Linux és PREEMPT_RT, autók és XR; NPU-k, Rust, seL4, Fuchsia és HarmonyOS |

## A laborok futtatása

A laborprogramokhoz Linux (vagy WSL) kell `gcc`, `binutils` (`as`, `ld`, `objdump`) és `gdb` csomaggal. Debianon vagy Ubuntun:

```console
$ sudo apt install build-essential gdb
```

A 6. előadás ezen felül `strace`-t, Python 3-at és (opcionálisan) Java JDK-t használ, a 7. előadás `valgrind`-ot (`sudo apt install strace default-jdk valgrind`). A 9. előadáshoz `e2fsprogs` (`debugfs`, `dumpe2fs`, `filefrag`), `dosfstools`, `xfsprogs` és `ntfs-3g` kell (`sudo apt install e2fsprogs dosfstools xfsprogs ntfs-3g`); az ext4-es bemutatók képfájlok csatolásához root jogot igényelnek. A 10. előadáshoz root jog kell (bemutató felhasználókat hoz létre), valamint a `libcap2-bin` és az `acl` csomag (`sudo apt install libcap2-bin acl`); a SELinux-laborhoz Fedora, RHEL vagy AlmaLinux virtuális gép kell. A 11. előadás namespace-, cgroup- és overlay-bemutatóihoz root jog kell, a konténeres laborokhoz Podman (vagy Docker), lehetőleg Fedorán, CentOS Streamen, AlmaLinuxon vagy Rocky Linuxon (`sudo dnf install podman skopeo buildah`); a KVM-laborhoz Intel VT-x-et vagy AMD-V-t támogató fizikai gép és QEMU kell (`sudo dnf install qemu-kvm libvirt virt-install`). A 12. előadás cgroup-, zram- és valós idejű bemutatóihoz root jog kell (a `chrt`, a `taskset` és a `swapon` a `util-linux` csomag része; a zram-bemutatóhoz zramot tartalmazó kernel kell), az androidos laborokhoz pedig `adb` (`sudo apt install adb`) és az Android Studio Android-emulátora vagy egy bekapcsolt USB-hibakereséssel rendelkező telefon.

A programok kimenetei és a bennük lévő megjegyzések angolul vannak; az előadásokban szereplő konzolkimenetek valódi, mért eredmények, ezért változatlanok.

## Ábrák

Az ábrák egyszerű SVG-fájlok, és a GitHub sötét módjában automatikusan sötét színekre váltanak. Minden mappában megtalálható az ábrákat előállító Python-szkript (`make_*.py`) is, így az ábrák szerkeszthetők és újragenerálhatók.

## Licenc

Lásd: [LICENSE](../LICENSE).
