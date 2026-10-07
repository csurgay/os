# Operációs rendszerek

Egyetemi operációsrendszer-kurzus előadásanyaga, linuxos (x86-64) példákkal és laborfeladatokkal. Minden előadás saját mappában van: a szöveg a mappa `README.md` fájljában, mellette az ábrák (SVG) és a laborokban használt forrásfájlok.

Az előadások egyetemi hallgatóknak készültek, de minden rövidítéshez és szakkifejezéshez tartozik egy lenyitható **Egyszerűen elmagyarázva** doboz, így alapszintű számítógépes ismeretekkel is követhetők.

English version: [../en/](../en/)

| # | Előadás | Témák |
| --- | --- | --- |
| 1 | [Az operációs rendszerek történeti fejlődése](01-historic-evolution/) | miért vannak operációs rendszerek: kötegelt feldolgozás, rezidens monitor, multiprogramozás, virtuális memória, időosztás, Multics és Unix, MS-DOS, hálózatok és mobileszközök; az operációs rendszer szerepei és rétegei |
| 2 | [Minőség, üzleti szempontok és az Enterprise Linux ökoszisztéma](02-quality-and-enterprise-linux/) | minőségi szempontok és az ISO/IEC 25010, MTTF/MTTR/MTBF és rendelkezésre állás, SLI/SLO/SLA, a nyílt forráskód üzleti modellje, branch/fork/upstream/backport, Fedora, CentOS Stream, RHEL, AlmaLinux, Rocky Linux; konténerképek, UBI, registryk, Podman és image mode |
| 3 | [Kognitív ergonómia és az operációs rendszerek felhasználói felülete](03-cognitive-ergonomics/) | kognitív ergonómia; OS-felületek a parancssortól a telefonokig, órákig, hangvezérlésig és headsetekig; szín (világosság és színezet, kontraszt, színtévesztés), rövid távú memória és tömbösítés, affordanciák és jelölők, Fitts- és Hick–Hyman-törvény, felismerés és felidézés, szakértelem, affektív számítástechnika, kölcsönös tekintet, a hátborzongató völgy, etorobotika |
| 4 | [Az utasítás-végrehajtási ciklus](04-fetch-execute-cycle/) | Neumann-architektúra, CPU-regiszterek és sínek, az utasításciklus, címzési módok, jelzőbitek és ugrások, memóriajogosultságok (NX), x86-64 és `gdb` |
| 5 | [Megszakítások](05-interrupts/) | megszakítási osztályok, felhasználói és kernelmód, a megszakítás feldolgozása, egymásba ágyazott megszakítások, a megszakításvezérlő, megszakítási késleltetés, programozott I/O, megszakítások és DMA, versenyhelyzetek, test-and-set és szemaforok, `/proc/interrupts` |
| 6 | [Párhuzamosság, holtpontok, folyamatállapotok és a Linux ütemezése](06-concurrency-deadlocks-scheduling/) | a kritikus szakasz problémája, Peterson algoritmusa és a memóriakorlátok, atomi műveletek, spinlockok, mutexek és futexek, szemaforok és a termelő–fogyasztó probléma, monitorok, holtpont (Coffman-feltételek, megelőzés, bankár-algoritmus, felismerés), livelock és prioritásinverzió, folyamatállapotok és a három ütemező, zombik, FIFO/SJF/SRTF/Round Robin, a Linux ütemezési osztályai, nice és EEVDF |
| 7 | [Kétszintű memóriák és gyorsítótárak](07-two-level-memory-and-cache/) | a memóriahierarchia, a kétszintű memória és átlagos elérési ideje, a hivatkozási lokalitás, direkt leképezésű, teljesen asszociatív és csoportasszociatív gyorsítótárak, érvényességi és dirty bit, write-through és write-back, csere (LRU, FIFO, öregítés, Bélády OPT algoritmusa), sorméret, előbetöltés, koherencia és hamis megosztás, a lap-gyorsítótár (page cache), gyorsítótár-barát ciklusok |
| 8 | [Virtuális memória](08-virtual-memory/) | elválasztás és áthelyezés, belső és külső fragmentáció, lapozás, laptáblák és a laptábla-bázisregiszter, érvényességi és jogosultsági bitek, az x86-64 többszintű laptáblái, a TLB és az óriáslapok, laphibák, igény szerinti lapozás és írásra másolás, lapcsere (FIFO, OPT, LRU, óra), Bélády-anomália, munkahalmaz és vergődés, gyorsítótárak és virtuális memória összevetése |

## A laborok futtatása

A laborprogramokhoz Linux (vagy WSL) kell `gcc`, `binutils` (`as`, `ld`, `objdump`) és `gdb` csomaggal. Debianon vagy Ubuntun:

```console
$ sudo apt install build-essential gdb
```

A 6. előadás ezen felül `strace`-t, Python 3-at és (opcionálisan) Java JDK-t használ, a 7. előadás `valgrind`-ot (`sudo apt install strace default-jdk valgrind`). A 2. előadás konténeres laborjaihoz Podman (vagy Docker) kell, lehetőleg Fedorán, CentOS Streamen, AlmaLinuxon vagy Rocky Linuxon (`sudo dnf install podman skopeo`).

A programok kimenetei és a bennük lévő megjegyzések angolul vannak; az előadásokban szereplő konzolkimenetek valódi, mért eredmények, ezért változatlanok.

## Ábrák

Az ábrák egyszerű SVG-fájlok, és a GitHub sötét módjában automatikusan sötét színekre váltanak. Minden mappában megtalálható az ábrákat előállító Python-szkript (`make_*.py`) is, így az ábrák szerkeszthetők és újragenerálhatók.

## Licenc

Lásd: [LICENSE](../LICENSE).
