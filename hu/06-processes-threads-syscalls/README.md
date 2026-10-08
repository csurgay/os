# Folyamatok, szálak és rendszerhívások

*Operációs rendszerek előadás: miből áll egy folyamat, hogyan kér szolgáltatást egy program a kerneltől rendszerhívásokkal, hogyan jönnek létre, cserélnek programot és fejeződnek be a folyamatok (fork, exec, exit, wait és alternatíváik), hogyan használja mindezt egy shell, mi közös a szálakban, és hogyan képződnek le kernelszálakra, hogyan kommunikálnak a folyamatok (pipe-ok, szignálok, osztott memória, üzenetsorok, socketek), és hogyan figyelhetjük meg mindezt egy futó Linux rendszeren, mérésekkel*

## Tanulási célok

A [megszakításokról szóló előadás](../05-interrupts/) a történet hardveres oldalát mutatta be: a processzor a közönséges programokat felhasználói módban, a kernelt kernelmódban futtatja, és a kernelbe csak megszakítással, kivétellel vagy a rendszerhívás-utasítással lehet bejutni ([Felhasználói mód és kernelmód](../05-interrupts/#felhasználói-mód-és-kernelmód)). A [következő előadás](../07-concurrency-deadlocks-scheduling/) a folyamatokat és a szálakat mint a processzoron osztozó egységeket tárgyalja: állapotaikat, szinkronizációjukat, és azt, hogyan választ közülük az ütemező. Ez az előadás a kettő között helyezkedik el. Elmagyarázza, miből áll valójában egy folyamat, hogyan végezteti el egy program a munkát a kernellel rendszerhívások segítségével, hogyan születnek a folyamatok, hogyan cserélnek programot, hogyan érnek véget és hogyan gyűjti be őket a szülőjük, mi a szál, hogyan cserélnek adatot a folyamatok, és hogyan nézhetünk bele egy futó rendszerbe.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> program, folyamat, szál, rendszerhívás, kernel</summary>

- **Program:** utasításokat tartalmazó fájl, mint egy recept a szakácskönyvben. Magától semmit sem csinál.
- **Folyamat:** futó program, saját memóriával és saját hellyel a számítógép teendőlistáján, mint egy szakács, aki egy konyhában éppen a receptet követi. Ugyanazt a receptet egyszerre több szakács is főzheti.
- **Szál:** egy munkavonal egy folyamaton belül. Egy folyamat több szála olyan, mint több szakács ugyanabban a konyhában: közösen használják a hozzávalókat és az eszközöket.
- **Kernel:** az operációs rendszer központi része, amely teljes irányítással rendelkezik a hardver fölött.
- **Rendszerhívás:** egy program kérése a kernelhez („nyisd meg ezt a fájlt”, „indíts el egy új programot”), mint amikor a vendég leadja a rendelést a pult mögötti személyzetnek.

</details>

Az előadás végére a hallgatók képesek lesznek:

- megkülönböztetni a programot a folyamattól, felrajzolni egy folyamat címtartományát (text, data, BSS, heap, memórialeképezett terület, verem), és felsorolni, mit tárol a kernel egy folyamatról ezen kívül;
- megkülönböztetni a könyvtári API-t a rendszerhívás-interfésztől, elmagyarázni, hogyan működik együtt a libc wrapper, az x86-64 `syscall` utasítása, a rendszerhívás száma és táblája, a visszatérési érték és az `errno`, és elmagyarázni, mire való a vDSO;
- megmérni egy rendszerhívás költségét, és megmagyarázni, miért sokkal drágább egy függvényhívásnál;
- használni a `fork`-ot, az `exec` családot, az `exit`-et és a `wait`/`waitpid` hívást, dekódolni egy kilépési állapotot, és elmagyarázni a copy-on-write-ot, az árva folyamatokat, az új szülőhöz kerülést és a subreapereket;
- megírni egy minimális shellt a `fork`, `exec`, `wait`, `pipe` és `dup2` hívásokkal, és a fájlleírók szintjén elmagyarázni, hogyan működik az átirányítás és a pipeline;
- összehasonlítani a `fork`, `vfork`, `posix_spawn` és `clone` hívást, és ismertetni a `fork` kritikáját;
- elmagyarázni, mi közös egy folyamat szálaiban és mi az egyes szálak sajátja, összehasonlítani a felhasználói és a kernelszintű szálakat (N:1, 1:1, M:N), és kapcsolatba hozni őket a Linux taskjaival és `clone`-flagjeivel, a POSIX-szálakkal, a TLS-sel (thread-local storage), a goroutine-okkal és a Java virtuális szálaival;
- leírni a pipe-okat és a FIFO-kat, a szignálokat (szignálkezelők, async-signal safety, megszakított rendszerhívások), az osztott memóriát, az üzenetsorokat és a socketeket, választani közülük, és értelmezni a mért késleltetést és áteresztőképességet;
- megfigyelni a folyamatokat a `/proc`, a `/sys`, az `strace`, a `gdb` és `ptree`-szerű eszközök segítségével, és elmagyarázni, mit tesz ehhez hozzá az `ltrace`, a `perf` és az eBPF (`bpftrace`).

## Programok és folyamatok

A **program** passzív fájl: gépi kód és kezdeti adatok egy futtatható formátumban (Linuxon ELF), a lemezen tárolva. A **folyamat** végrehajtás alatt álló program: aktív entitás saját memóriával, saját regiszterekkel és saját bejegyzéssel a kernel tábláiban (Silberschatz et al., 2018; Arpaci-Dusseau & Arpaci-Dusseau, 2023). A különbség mindkét irányban számít. Egy program egyszerre sok folyamatként futhat (tíz felhasználó futtatja a `bash`-t, egy webszerver sok munkafolyamattal), mindegyik saját memóriával és állapottal. Egy folyamat pedig egymás után több programot is futtathat: a shell gyerekfolyamata a shell másolataként indul, majd a programját az `ls`-re cseréli.

A Unix kezdettől fogva a folyamatot tette a központi absztrakcióvá: „a folyamat egy image végrehajtása”, ahol az image „egy pszeudoszámítógép pillanatnyi állapota” (Ritchie & Thompson, 1974). Az operációs rendszer minden folyamatnak azt az illúziót adja, hogy saját gépe van: saját memóriája, egy processzor, amely látszólag csak az ő utasításait futtatja, és név szerint elérhető fájlok és eszközök.

### Miből áll egy folyamat

![Egy folyamat: bal oldalon a virtuális címtartománya a 0-s címtől felfelé: a leképezetlen 0. lap, a text, a data, a BSS, a felfelé növekvő heap, a memórialeképezett terület a könyvtárakkal és a nagy foglalásokkal, a lefelé növekvő verem, legfelül pedig a kernel része; jobb oldalon a kernel nyilvántartása a folyamatról: azonosítók, állapot, mentett regiszterek, memóriatérkép, megnyitott fájlok, jogosultsági adatok, szignálok és környezet](address-space.svg)

**A címtartomány.** Minden folyamat a saját virtuális címtartományát látja (azt, hogyan képződnek le a virtuális címek a fizikai memóriára, a [virtuális memóriáról szóló előadás](../09-virtual-memory/) tárgyalja). Linuxon ez régiókra tagolódik:

- **Text:** a program gépi kódja, a futtatható fájlból leképezve; olvasható és végrehajtható, de nem írható, így egy hiba nem írhatja felül a kódot, és az ugyanazt a programot futtató folyamatok közösen használhatják.
- **Data:** a kezdőértékkel rendelkező globális és statikus változók (`int initialised = 42;`), a futtatható fájlból átmásolva.
- **BSS:** a kezdőérték nélküli globális és statikus változók, amelyek a C szabály szerint nulláról indulnak. A futtatható fájl csak az összméretüket tárolja; a kernel nullákkal feltöltött lapokat ad. (A név történeti eredetű, egy assembler-direktívából származik: „block started by symbol”.)
- **Heap** (kupac): futás közben `malloc`-kal vagy `new`-val foglalt memória. Felfelé növekszik; a C könyvtár a `brk` rendszerhívással bővíti.
- **Memórialeképezett terület:** a megosztott könyvtárak (a C könyvtár, a dinamikus betöltő), az `mmap`-pel leképezett fájlok, a nagy `malloc`-blokkok (a glibc a 128 KiB-os és annál nagyobb blokkokat külön `mmap`-pel szolgálja ki), a további szálak vermei és a vDSO (lásd lent).
- **Verem** (stack): a fő szál lokális változói, függvényargumentumai és visszatérési címei. Lefelé növekszik, alapértelmezés szerint legfeljebb 8 MiB-ig.
- **A kernel része:** a 64 bites címtartomány felső fele a kernelé. Minden folyamatban le van képezve, de védett: felhasználói módú kód nem nyúlhat hozzá. (A Meltdown támadásra sérülékeny processzorokon a Linux csak egy kis belépési területet képez le, amíg felhasználói kód fut.)

A [linuxos rész](#egy-futó-program-címtartománya) minden régióból kiírja egy változó címét, és megkeresi a `/proc/self/maps` fájlban.

**Minden más.** Egy folyamat több, mint memória. A kernel a saját memóriájában, ahol a folyamat nem módosíthatja, nyilvántartást vezet mindarról, amire még szüksége van: a [következő előadás](../07-concurrency-deadlocks-scheduling/#a-folyamatok-állapottere) ezt **folyamatleírónak** (process control block, PCB) nevezi; Linuxon ez egy `struct task_struct` (Love, 2010). Ebben van a folyamatazonosító (PID) és a szülő PID-je; az állapot és az ütemezési információk; a mentett regiszterek (utasításszámláló, veremmutató, jelzőbitek), amíg a folyamat nem fut; a címtartomány leírása (a régiók listája és a laptáblák); a megnyitott fájlok táblája; a jogosultsági adatok (credentials: felhasználói és csoportazonosítók, capabilityk, lásd a [hozzáférés-szabályozásról szóló előadást](../11-access-control/#felhasználók-csoportok-és-a-folyamat-identitása)); a szignálkezelők, valamint a függőben lévő és a blokkolt szignálok; és a környezet: aktuális könyvtár, gyökérkönyvtár, erőforráskorlátok és namespace-ek. Minden folyamatnak saját **kernelverme** is van, amelyet a kernel akkor használ, amikor a folyamat nevében dolgozik.

**Megnyitott fájlok.** A folyamat a megnyitott fájlokra, pipe-okra, socketekre és eszközökre kis egész számokkal, a **fájlleírókkal** hivatkozik. Minden fájlleíró egy index a folyamat leírótáblájába, amelynek bejegyzése a kernelben egy **megnyitott fájl leírására** (open file description) mutat (benne az aktuális pozícióval és a hozzáférési móddal), az pedig magára az objektumra (egy inode-ra, egy pipe-ra, egy socketre) ([Fájlrendszerek: fájlok és a tárolási verem](../10-file-systems/#fájlok-és-a-tárolási-verem)). Megállapodás szerint a 0-s leíró a standard bemenet, az 1-es a standard kimenet, a 2-es a standard hibakimenet. Ez a háromszintű szerkezet teszi lehetővé a shell átirányításait és a pipe-okat, ahogy az [életciklusról szóló rész](#hogyan-használja-őket-a-shell) bemutatja.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> futtatható fájl, ELF, image, címtartomány, text, data, BSS, heap, verem, memórialeképezett terület, megosztott könyvtár, Meltdown, PCB, task_struct, PID, laptábla, credentials, capabilityk, kernelverem, fájlleíró, megnyitott fájl leírása, inode</summary>

- **Futtatható fájl, ELF:** futásra kész programot tartalmazó fájl. Az ELF (Executable and Linkable Format) az ilyen fájlok formátuma Linuxon.
- **Image:** egy futó program memóriájának és regisztereinek pillanatképe.
- **Címtartomány:** azoknak a memóriacímeknek a köre, amelyeket egy folyamat használhat, mint egy saját füzet számozott oldalai. Minden folyamatnak saját füzete van.
- **Text:** a füzetnek az a része, amely a program utasításait tartalmazza; csak olvasható.
- **Data, BSS:** globális változók. A data a kezdőértékkel rendelkezőket tartalmazza; a BSS a nulláról indulókat, ezért a fájlnak csak azt kell megmondania, hány ilyen van.
- **Heap:** memória, amelyet a program futás közben kér olyan dolgokhoz, amelyek méretét előre nem ismeri.
- **Verem:** memória az éppen futó függvények lokális változóinak; függvényhíváskor nő, visszatéréskor csökken, mint egy tányérhalom.
- **Memórialeképezett terület, megosztott könyvtár:** a címtartomány olyan része, ahol a fájlok memóriának látszanak. A megosztott könyvtár kész függvényeket (például a `printf`-et) tartalmazó fájl, amelyet sok program használ, de a memóriában csak egyszer van meg.
- **Meltdown:** 2018-ban sok processzorban talált hiba, amelyen keresztül felhasználói programok a processzor találgatásainak mellékhatásain át kiolvashatták a kernel memóriáját; a javítás a kernel nagy részét elrejti, amíg felhasználói kód fut.
- **PCB, task_struct:** a kernel nyilvántartó kartonja egy folyamatról. A Linux neve erre `task_struct`.
- **PID:** folyamatazonosító, a folyamat sorszáma.
- **Laptábla:** a kernel fordítótáblája egy folyamathoz, amely megmondja, hogy a folyamat memóriájának egyes lapjai valójában hol vannak a számítógép RAM-jában.
- **Credentials, capabilityk:** az a felhasználó és csoport, akinek a nevében a folyamat dolgozik, mint a név a személyi igazolványon, és ez dönti el, mit tehet; a capabilityk egyes rendszergazdai jogok, amelyek egyenként adhatók meg egy folyamatnak.
- **Kernelverem:** kis verem, amelyet a kernel akkor használ, amikor egy folyamatnak dolgozik; elkülönül a folyamat saját vermétől.
- **Fájlleíró:** kis szám, amellyel a program egy megnyitott fájlra hivatkozik, mint egy ruhatári jegy. **Megnyitott fájl leírása:** a kernel jegyzete a jegy mögött: melyik fájl, hogyan nyitották meg, és meddig olvasták már.
- **Inode:** a fájlrendszer nyilvántartó kartonja egy fájlról (mérete, tulajdonosa, jogosultságai és az, hogy hol vannak az adatai), a nevétől elkülönítve.

</details>

## Rendszerhívások: a kernel kapui

Egy felhasználói módban futó folyamat tud számolni, de semmit sem tehet, ami a külvilágot vagy más folyamatokat érinti: nem olvashat lemezblokkot, nem küldhet hálózati csomagot, nem hozhat létre folyamatot, sőt még befejezni sem tudja önmagát. Mindehhez a kernel kell. A **rendszerhívás** ellenőrzött kérés a kernelhez: a folyamat végrehajt egy speciális utasítást, amely a processzort kernelmódba kapcsolja, és a kernel által regisztrált belépési pontra ugrik, pontosan úgy, mint a [megszakításokról szóló előadás](../05-interrupts/#felhasználói-mód-és-kernelmód) trap-mechanizmusa. A kernel ellenőrzi a kérést, elvégzi a munkát és visszaadja az eredményt, a processzor pedig visszatér felhasználói módba.

### Az API és a rendszerhívás-interfész

A programozók ritkán adnak ki közvetlenül rendszerhívást. Egy **alkalmazásprogramozási interfész** (application programming interface, API), például a POSIX API vagy a C standard könyvtár függvényeit hívják, és a rendszerhívásokat a könyvtár végzi. A két interfész különböző dolog:

- Sok könyvtári függvény vékony **wrapper**: a glibc `write()`, `read()`, `open()`, `fork()` és `getpid()` függvénye egyaránt a megfelelő regiszterekbe teszi az argumentumait, és végrehajt egyetlen rendszerhívást.
- Egyes könyvtári függvények egyáltalán **nem** hajtanak végre rendszerhívást (`strlen`, `memcpy`, `sqrt`), vagy csak néha: a `printf` és az `fwrite` a felhasználói memóriában lévő pufferbe gyűjti a kimenetet, és csak akkor hívja a `write()`-ot, ha a puffer megtelt, terminálon sorvégnél, vagy amikor a program kilép; a `malloc` csak akkor hívja a `brk`-ot vagy az `mmap`-et, ha a készlete kifogyott.
- Egyes könyvtári függvények **többet** is végrehajtanak: az `fopen` egy `openat`-et, és az `fstat`-tal ellenőrizheti is a fájlt; egy dinamikusan linkelt program indítása több tucat hívással jár, mielőtt a `main` egyáltalán elkezdődne (ezt az [strace-ről szóló rész](#nyomkövetés-strace-szel) méri meg).
- Fordítva: néhány rendszerhívásnak nincs szokásos wrappere, ezeket az általános `syscall()` függvényen keresztül érjük el, amely első argumentumként a rendszerhívás számát kapja.

Az API és a rendszerhívás-interfész szétválasztása lehetővé teszi, hogy a könyvtár stabil maradjon, miközben a kernel interfésze fejlődik (a glibc `fork()` függvénye ma egy `clone` rendszerhívást hajt végre, nem a régi `fork` rendszerhívást), és hogy ugyanaz az API nagyon különböző kerneleken legyen megvalósítva: a POSIX API létezik Linuxon, a BSD-ken és macOS-en, és (egy kompatibilitási rétegen keresztül) Windowson is. Maga a Linux rendszerhívás-interfésze nagyon stabil: a Linux szabálya, hogy a kernel egyetlen változtatása sem teheti működésképtelenné a meglévő felhasználói programokat.

### A `syscall` utasítás x86-64-en

Minden rendszerhívásnak van száma. x86-64-es Linuxon a `read` a 0, a `write` az 1, a `getpid` a 39, a `clone` az 56, a `fork` az 57, az `execve` az 59, az `exit` a 60, a `wait4` a 61, az `exit_group` a 231; az itt használt gép C fejlécfájljai 373 számot definiálnak, 0-tól 461-ig (a 335–423 számok kihasználatlanok, hogy minden azóta felvett rendszerhívás minden architektúrán ugyanazt a számot kapja). A hívási konvenciót a kernel rögzíti (Linux man-pages project, n.d.-f):

![Egy rendszerhívás útja: a program meghívja a write()-ot; a libc wrapper az 1-es számot az rax regiszterbe teszi, és végrehajtja a syscall utasítást; a processzor kernelmódba vált, és az entry_SYSCALL_64 címre ugrik, amely elmenti a felhasználói regisztereket; a sys_call_table[rax] a ksys_write függvényre irányít, majd a VFS és a meghajtó következik; a sysret az rax-ban lévő eredménnyel tér vissza; a clock_gettime ehelyett a vDSO-ba megy, és be sem lép a kernelbe](syscall-path.svg)

1. A wrapper a **rendszerhívás számát** az `rax` regiszterbe, a legfeljebb hat **argumentumot** pedig az `rdi`, `rsi`, `rdx`, `r10`, `r8` és `r9` regiszterbe teszi (nem az `rcx`-be, mert azt maga az utasítás felülírja).
2. Végrehajtja a `syscall` utasítást. A processzor a visszatérési címet az `rcx`-be, a jelzőbiteket az `r11`-be menti, kernelmódba vált, és arra a címre ugrik, amelyet a kernel indításkor egy modellspecifikus regiszterben (MSR) tárolt el. Ez a Linux `entry_SYSCALL_64` belépési pontja.
3. A belépési kód átvált a folyamat kernelvermére, elmenti a felhasználói regisztereket, és az `rax` értékét indexként használja a **rendszerhívás-táblában**, amely függvénymutatók tömbje: az 1-es bejegyzés a kernel `write`-megvalósítása.
4. A kernelfüggvény elvégzi a munkát: ellenőrzi a fájlleírót és a puffert, a VFS-en keresztül eljut a pipe-hoz, a fájlrendszerhez vagy a terminál meghajtójához, és blokkolhat is (a folyamat ekkor várakozik, és más folyamatok futnak).
5. Az eredmény az `rax`-ba kerül, és a `sysret` közvetlenül a `syscall` utasítás utánra tér vissza felhasználói módba.
6. A kernel a hibákat kis negatív számokkal jelzi: `-EBADF` (−9) érvénytelen fájlleíró, `-ENOENT` (−2) nem létező fájl esetén. A wrapper ellenőrzi, hogy az érték −4095 és −1 közé esik-e; ha igen, az ellentettjét a szál **`errno`** változójába írja, és −1-et ad vissza, ahogy a C programok várják. A [linuxos rész](#egy-rendszerhívás-háromféleképpen) ugyanazt a hívást háromféleképpen hajtja végre, és megmutatja a wrapper gépi kódját is.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> API, POSIX, wrapper, puffer, rendszerhívásszám, rendszerhívás-tábla, regiszter, MSR, VFS, errno</summary>

- **API** (application programming interface, alkalmazásprogramozási interfész): azoknak a függvényeknek a listája, amelyeket egy könyvtár a programozóknak kínál, a nevükkel és a szabályaikkal együtt.
- **POSIX:** szabvány, amely előírja, milyen függvényeket kell egy Unix-szerű rendszernek kínálnia, és hogyan viselkednek ezek, hogy a programok átvihetők legyenek az ilyen rendszerek között.
- **Wrapper:** kis függvény, amelynek egyetlen feladata, hogy valami mást a megfelelő módon meghívjon, mint egy boríték a levél körül.
- **Puffer:** várakozóhely a memóriában, ahol az adatok összegyűlnek, mielőtt egyszerre továbbmennének, mint amikor tele kosarat viszünk fel a lépcsőn, nem darabonként.
- **Rendszerhívásszám, rendszerhívás-tábla:** minden kéréstípusnak száma van; a kernel ezt a számot egy táblázatban keresi ki, hogy megtalálja a kezelő kódot, mint egy étlapon, ahol a 39-es ételt rendeljük.
- **Regiszter:** apró, nagyon gyors tárolóhely a processzoron belül; az `rax`, `rdi` és a többi x86-64-es regiszternév.
- **MSR** (model-specific register, modellspecifikus regiszter): beállításokat tároló speciális processzorregiszter, itt annak a címnek a tárolására, ahol a rendszerhívások belépnek a kernelbe.
- **VFS** (virtual file system, virtuális fájlrendszer): a kernelnek az a rétege, amely minden fájlrendszer- és eszköztípushoz ugyanazokat a fájlműveleteket kínálja.
- **errno:** változó, amelyben a C könyvtár az utolsó hiba számát hagyja, például 2 („nincs ilyen fájl”) vagy 9 („érvénytelen fájlleíró”).

</details>

### A vDSO: rendszerhívások, amelyek nem lépnek be a kernelbe

Egyes kérések csak olyan információt olvasnak ki, amelyet a kernel már ismer, és nagyon gyakran fordulnak elő: mindenekelőtt az aktuális idő, amelyet egy forgalmas szerver másodpercenként milliószor is lekérdezhet. Ezekhez a kernel minden folyamatba leképez egy kis megosztott könyvtárat, a **vDSO**-t (virtual dynamic shared object), egy csak olvasható adatlappal együtt, amelyet a kernel naprakészen tart (ezek a `/proc/PID/maps` `[vdso]` és `[vvar]` sorai a [virtuális memóriáról szóló előadásban](../09-virtual-memory/#egy-folyamat-címtartománya)). A C könyvtár `clock_gettime()`, `gettimeofday()`, `time()` és `getcpu()` függvénye a vDSO függvényeit hívja, amelyek az adatlapból és a processzor időbélyeg-számlálójából teljes egészében felhasználói módban számítják ki a választ (Linux man-pages project, n.d.-h). A kernel minden új programnak az auxiliary vectoron (`AT_SYSINFO_EHDR`) keresztül adja meg, hol van a vDSO. Így csak olvasni lehet; ami a rendszer állapotát megváltoztatja, vagy jogosultság-ellenőrzést igényel, annak be kell lépnie a kernelbe.

### Mibe kerül egy rendszerhívás

Egy rendszerhívás sokkal többe kerül egy függvényhívásnál, még akkor is, ha a kernel szinte semmit sem csinál: ott a módváltás, a regiszterek mentése és visszaállítása, a veremváltás, a belépési kód ellenőrzései, és sok processzoron a spekulatív végrehajtást kihasználó támadások elleni többletmunka, amely minden átlépéskor kiüríti vagy szétválasztja a belső puffereket. A [linuxos rész](#a-kernelbe-lépés-ára) mérése szerint egy függvényhívás körülbelül 2 ns, a `getpid()` 120–135 ns, a `clock_gettime()` a vDSO-n keresztül 30–39 ns, szemben a kernelbe kényszerített ugyanazon hívás 190 ns-ával. A tanulságok ugyanazok, mint a teljesítményoptimalizálásban mindenütt: ne hajtsunk végre bájtonként egy rendszerhívást (pufferelés, ahogy a `printf` is teszi), kötegeljük a kéréseket (`readv`/`writev`, `sendmmsg`, `io_uring`), és ahol lehet, tartsuk az adatokat a felhasználói térben. Az egyik folyamatról a másikra való váltás ennél jóval nagyobb költségét a [következő előadás](../07-concurrency-deadlocks-scheduling/#egy-környezetváltás-ára) méri meg.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> vDSO, időbélyeg-számláló, auxiliary vector, spekulatív végrehajtás, kötegelés</summary>

- **vDSO:** apró könyvtár, amelyet a kernel minden programba betesz, hogy a program bizonyos kernelinformációkat (főleg az időt) a kernel megkérdezése nélkül olvashasson ki.
- **Időbélyeg-számláló:** a processzor egy számlálója, amely állandó ütemben nő; ebből kiszámítható az idő.
- **Auxiliary vector** (kiegészítő vektor): rövid adatlista, amelyet a kernel induláskor átad egy új programnak, például a lapméretet és a vDSO helyét.
- **Spekulatív végrehajtás:** a processzor kitalálja, mi következik, és előre nekikezd; egyes támadások ezeknek a találgatásoknak a nyomait használják ki, az ellenük való védekezés pedig lassabbá teszi a kernelbe való átlépést.
- **Kötegelés:** sok kis kérés elintézése egyszerre, mint amikor minden levelünket egy úttal adjuk postára, nem levelenként külön úttal.

</details>

## A folyamatok életciklusa

A Unix szokatlan hívás-párral hozza létre a folyamatokat: a **`fork()`** lemásolja a hívó folyamatot, az **`exec()`** pedig egy folyamatban futó programot egy újra cserél. A harmadik, az **`exit()`** befejezi a folyamatot, a **`wait()`** pedig lehetővé teszi, hogy a szülő begyűjtse az eredményt. Az első kivételével minden folyamat így jön létre, ezért a rendszer folyamatai **fát** alkotnak (folyamatfa): egy tipikus Linux rendszeren az 1-es PID (`systemd` vagy más init program) minden felhasználói folyamat őse, a 2-es PID (`kthreadd`) pedig a kernel saját szálaié.

![Egy shell futtat egy parancsot: a szülő (PID 100) meghívja a fork-ot; a gyerek (PID 101) a shell másolataként indul, meghívja az execve("/usr/bin/ls") hívást, és ugyanazzal a PID-del futtatja az ls-t, majd exit(0), és zombivá válik; a szülő S állapotban várakozik a waitpid(101) hívásban, megkapja a SIGCHLD szignált és a 0 állapotot, a zombi pedig eltűnik](fork-exec-wait.svg)

### fork: a hívó másolata

A `fork()` új folyamatot hoz létre, a **gyereket**, amely a hívó folyamatnak, a **szülőnek** szinte pontos másolata: ugyanaz a program, ugyanaz a memóriatartalom, ugyanazok a megnyitott fájlok (a gyerek a leírótábla másolatát kapja, amelynek bejegyzései ugyanazokra a megnyitott fájl leírásokra mutatnak, így a szülő és a gyerek közösen használja a fájlpozíciókat), ugyanaz az aktuális könyvtár, ugyanazok a jogosultsági adatok és szignálkezelők. Kevés a különbség: a gyereknek új PID-je van, a szülője a hívó, a processzoridő-számlálói nulláról indulnak, a függőben lévő szignálokat és a zárakat nem örökli, és ami a legfontosabb: a `fork()` **kétszer tér vissza**: a szülőben a gyerek PID-jét adja vissza, a gyerekben 0-t. Így különbözteti meg magát a két másolat:

```c
pid_t pid = fork();
if (pid < 0)        perror("fork");          /* no child was created  */
else if (pid == 0)  child_work();            /* in the child          */
else                parent_work(pid);        /* in the parent         */
```

Egy teljes címtartomány lemásolása lassúvá tenné a `fork()`-ot, és többnyire fölösleges is volna, mert a legtöbb gyerek azonnal meghívja az `exec()`-et. A Linux ezért csak a laptáblákat másolja le, és mindkét folyamatban csak olvashatónak jelöli az összes privát lapot: ez a **copy-on-write**. Egy lapot csak akkor másol le, amikor valamelyikük ír bele ([Virtuális memória: copy-on-write](../09-virtual-memory/#copy-on-write)). A laptáblákat azonban így is le kell másolni, és a [linuxos rész](#folyamatok-és-szálak-létrehozása-mibe-kerül) 20 ms-ot mér egy 1 GiB memóriát használó folyamat `fork()`-jára.

Egy csapda: ha egy `fork()` előtti `printf` kimenete még a C könyvtár pufferében van, az a memóriával együtt lemásolódik, és kétszer jelenik meg, mindkét folyamat kiírja. A programnak ezért a forkolás előtt ki kell ürítenie a kimenetét (`fflush(stdout)`), az `exec`-et nem hívó gyereknek pedig `_exit()`-tel kell befejeződnie, amely nem üríti ki újra a puffereket.

### exec: új program ugyanabban a folyamatban

Az `execve(path, argv, envp)` új programot tölt be a hívó folyamatba: a kernel megnyitja a futtatható fájlt, ellenőrzi a jogosultságokat, eldobja a régi címtartományt, leképezi az új program text és data részét, új vermet állít össze az argumentumokkal és a környezeti változókkal, és az új programot a belépési pontján indítja el (dinamikusan linkelt programnál először az `ld.so` dinamikus betöltőt, amely leképezi a megosztott könyvtárakat). Sikeres végrehajtás esetén az `execve()` soha nem tér vissza, mert az őt hívó kód már nem létezik.

Ami megmarad, az maga a folyamat: a PID és a szülő, a megnyitott fájlleírók (kivéve a **close-on-exec** jelzésűeket, `O_CLOEXEC`), az aktuális könyvtár, az erőforráskorlátok, a szignálmaszk és a figyelmen kívül hagyott szignálok (a kezelt szignálok visszaállnak az alapértelmezett műveletükre, mert a kezelő kódja eltűnt). A jogosultsági adatok is megmaradnak, hacsak az új programfájl nem setuid vagy setgid ([Hozzáférés-szabályozás: setuid](../11-access-control/#setuid-a-tulajdonos-identitásának-kölcsönvétele)).

Csak az `execve` rendszerhívás; a C könyvtár előtétfüggvények egész családját kínálja, amelyek neve elárulja, hogyan adjuk meg az argumentumokat: az `execl`, `execlp`, `execle` **l**istát (list), az `execv`, `execvp`, `execvpe` **v**ektort (tömböt) vár; a **p** változatok a `PATH` könyvtáraiban keresik a programot, az **e** változatok pedig kifejezetten megadott környezetet (**e**nvironment) kapnak.

### exit és wait

Egy folyamat úgy fejeződik be, hogy meghívja az `exit(status)` függvényt (ez a könyvtári függvény lefuttatja az `atexit` kezelőket, kiüríti a standard I/O puffereket, majd végrehajtja az `exit_group` rendszerhívást), visszatér a `main`-ből, vagy egy szignál megöli. A kernel ekkor lezárja a fájljait, felszabadítja a memóriáját és többi erőforrását, és csak egy kis bejegyzést tart meg a **kilépési állapottal** (exit status), amíg a szülő be nem gyűjti. Az ilyen állapotú folyamat a **zombi**; azt, hogyan keletkeznek a zombik, miért megy át ezen az állapoton minden befejeződő folyamat, és mi lesz velük, a [következő előadás folyamatállapotokról szóló része](../07-concurrency-deadlocks-scheduling/#a-folyamatok-állapottere) tárgyalja. A szülő a `SIGCHLD` szignált kapja értesítésként.

A szülő a `wait(&status)` (bármelyik gyerek) vagy a `waitpid(pid, &status, options)` hívással (egy adott gyerek, vagy `WNOHANG` esetén blokkolás nélkül) gyűjti be a gyereket. Az állapotszó több tényt tartalmaz, ezeket makrók dekódolják: a `WIFEXITED(status)` igaz, ha a gyerek meghívta az `exit`-et, és ekkor a `WEXITSTATUS(status)` a kilépési kód alsó 8 bitjét adja (megállapodás szerint a 0 a sikert jelenti); a `WIFSIGNALED(status)` igaz, ha egy szignál ölte meg, és a `WTERMSIG(status)` a szignál számát adja. A shell ugyanezt az információt a `$?` változóban mutatja: a kilépési kódot, vagy 128 plusz a szignál számát.

### Árva folyamatok és új szülő

Ha a szülő a gyereke előtt fejeződik be, a gyerek **árva folyamattá** válik. Tovább fut, de valakinek be kell gyűjtenie a kilépési állapotát, ezért a kernel új szülőt ad neki (reparenting): rendszerint az 1-es PID-et, amelynek init programja minden befejeződő árvát begyűjt. Egy folyamat **child subreaperré** is nyilváníthatja magát (`prctl(PR_SET_CHILD_SUBREAPER)`): ekkor a leszármazottai közül az árvák hozzá kerülnek, nem az 1-es PID-hez. A szolgáltatáskezelők (`systemd --user`) és a konténer-futtatókörnyezetek ezzel tartják nyilván az összes általuk indított folyamatot, akkor is, ha egy köztes folyamat már kilépett. A [linuxos rész](#árva-folyamatok-és-subreaperek) mindkét esetet bemutatja.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> szülő, gyerek, fork, copy-on-write, exec, dinamikus betöltő, close-on-exec, PATH, kilépési állapot, zombi, SIGCHLD, wait, árva folyamat, új szülő, subreaper</summary>

- **Szülő, gyerek:** az a folyamat, amely egy másikat létrehozott, illetve az új folyamat.
- **fork():** az a hívás, amely lemásolja a futó folyamatot. Utána két folyamat futtatja ugyanazt a programot; a másolat a gyerek.
- **Copy-on-write:** fork után a szülő és a gyerek közösen használja a memóriát, amíg egyikük meg nem változtat valamit; csak ekkor készül saját másolat, mint amikor két ember egy kinyomtatott szövegen osztozik, és csak akkor fénymásolnak le egy oldalt, amikor valamelyikük írni akar rá.
- **exec():** az a hívás, amely eldobja egy folyamat jelenlegi programját, és helyette egy másikat indít el, ugyanazzal a folyamatazonosítóval.
- **Dinamikus betöltő (`ld.so`):** az a kis program, amely elsőként indul, és összekapcsolja a programot a szükséges megosztott könyvtárakkal.
- **Close-on-exec:** jelzés egy fájlleírón, amely azt mondja: „zárj be automatikusan, ha új program indul”.
- **PATH:** beállítás, amely felsorolja azokat a mappákat, amelyekben a rendszer egy programot keres, ha csak a nevét írjuk be.
- **Kilépési állapot:** szám, amelyet egy program befejeződésekor hátrahagy; a 0 azt jelenti: „minden rendben ment”.
- **Zombi:** befejeződött folyamat, amelynek kilépési állapotát a szülője még nem gyűjtötte be.
- **SIGCHLD:** az a szignál, amelyet a szülő kap, amikor valamelyik gyereke befejeződik.
- **wait():** az a hívás, amellyel a szülő megvárja, hogy egy gyereke befejeződjön, és begyűjti a kilépési állapotát.
- **Árva folyamat, új szülő:** olyan folyamat, amelynek a szülője már befejeződött; új szülőt kap (reparenting), hogy a kilépési állapotát továbbra is be lehessen gyűjteni.
- **Subreaper:** olyan folyamat, amely kérte, hogy örökbe fogadhassa a leszármazottai közül az árvákat, mint egy nagyszülő, aki átveszi a gondoskodást.

</details>

### Hogyan használja őket a shell

A shell egy ciklus: beolvas egy parancssort, szavakra bontja, `fork()`-kal létrehoz egy gyereket, a gyerekkel `exec()`-kel lefuttatja a programot, és a `wait()`-tel megvárja a gyereket, hacsak a parancs nem `&`-re végződik. A `fork` és az `exec` szétválasztása teszi a Unix shellt ilyen egyszerűvé: a két hívás között a gyerek még a shell saját kódját futtatja, és közönséges rendszerhívásokkal előkészítheti a környezetét az új programnak, anélkül hogy az `exec`-nek ehhez bármilyen különleges támogatást kellene nyújtania (Ritchie & Thompson, 1974):

- **Átirányítás**, `cmd > out.txt`: a gyerek megnyitja az `out.txt`-t (mondjuk a 3-as leírót kapja), meghívja a `dup2(3, 1)`-et, amely az 1-es leírót ugyanarra a megnyitott fájl leírásra irányítja, amelyre a 3-as mutat, bezárja a 3-ast, és meghívja az `exec`-et. Az új program a szokásos módon az 1-es leíróra ír, és sosem tudja meg, hogy az fájl, nem pedig a terminál. A `cmd < in.txt` ugyanezt teszi a 0-s leíróval.
- **Pipeline**, `cmd1 | cmd2`: a shell a `pipe(fd)` hívással **pipe**-ot hoz létre: egy kernelpuffert az `fd[1]` író és az `fd[0]` olvasó véggel. Két gyereket forkol; az első az író véget teszi meg 1-es leírójának, a második az olvasó véget 0-s leírójának; minden folyamat bezárja azokat a leírókat, amelyekre nincs szüksége, és a gyerekek `exec`-kel elindítják a programjukat.
- **Beépített parancsok**, például a `cd` és az `exit`, nem lehetnek külön programok: a `cd`-nek magának a shellnek az aktuális könyvtárát kell megváltoztatnia, egy gyerek `chdir()` hívása pedig csak a gyerekét változtatná meg.

![Fájlleírók az ls /etc | grep ^host >hosts.txt parancsnál: az ls gyerek 1-es leírója a pipe író végére, a 0-s és a 2-es a terminálra mutat; a grep gyerek 0-s leírója a pipe olvasó végére, az 1-es a hosts.txt-re, a 2-es a terminálra mutat; a pipe mindkét vége ugyanarra a kernelmemóriában lévő pipe-pufferre mutat](fd-tables.svg)

A mappában lévő `minish.c` egy ilyen shell nagyjából 100 sorban, `<`, `>`, `>>` átirányítással, pipeline-okkal és a `cd` és `exit` beépített parancsokkal; a [linuxos rész](#shell-száz-sorban) lefuttatja, és nyomon követi a rendszerhívásait. Egy részletet könnyű elrontani: a szülőnek be kell zárnia a pipe végeinek saját másolatait. Az olvasó csak akkor észleli a fájl végét, ha az író vég *minden* leírója be van zárva; ha a shell megtartana egyet, a `grep` örökké további bemenetre várna.

### A fork alternatívái

Az azonnal `exec()`-kel folytatott `fork()` csak azért másolja le a laptáblákat, hogy aztán eldobja őket, és minél nagyobb a szülő, annál drágább. Több alternatíva is létezik:

- A **`vfork()`** (a BSD Unixból) olyan gyereket hoz létre, amely kölcsönveszi a szülő címtartományát, a szülő pedig fel van függesztve, amíg a gyerek meg nem hívja az `exec`-et vagy az `_exit`-et. Gyors, de veszélyes: a gyerek nem térhet vissza a függvényből, és nem változtathat meg egyetlen változót sem, mert azzal a szülőben változtatná meg.
- A **`posix_spawn()`** egyetlen hívással hoz létre egy új programot futtató új folyamatot, a közben végrehajtandó fájlműveletek (open, close, `dup2`) és attribútumok (szignálmaszk, folyamatcsoport) listájával, amely lefedi azt, amit a shellek a `fork` és az `exec` között általában csinálnak. A glibc `vfork` stílusú `clone()`-nal valósítja meg, egy kis külön vermen, így a költsége nem függ a szülő méretétől. A Windows mindig is így működött: a `CreateProcess` új programot indít egy új folyamatban, `fork` pedig nincs.
- A **`clone()`** (és az újabb `clone3()`) a Linux általános hívása mindezek mögött: a flagjei megmondják, mely erőforrásokon osztozik az új task a létrehozójával (címtartomány, fájltábla, szignálkezelők stb.), és milyen namespace-eket kap (ez a konténerek alapja, lásd [Virtualizáció és konténerizáció: namespace-ek](../13-virtualization-containerization/#namespace-ek)). Megosztási flagek nélkül folyamatot hoz létre (a glibc `fork()`-ja egy `clone()` a `SIGCHLD`-dal és két, a szálazonosítókra vonatkozó flaggel); a megfelelő flagekkel szálat (lásd a következő részt) (Linux man-pages project, n.d.-a).

Baumann et al. (2019) amellett érvelnek, hogy a `fork` a PDP-7 és PDP-11 korszakának kényelmes rövidítése volt, amely túlélte a hasznosságát: nagy folyamatoknál lassú; a szülő teljes állapotát lemásolja, ezért alapértelmezésben nem biztonságos (titkok, megnyitott leírók); nem fér össze a szálakkal (csak a hívó szál másolódik le, így a más szálak által tartott zárak a gyerekben örökre zárva maradnak, és a POSIX egy többszálú folyamat gyerekében az `exec` előtt csak async-signal-safe függvényeket enged meg); és arra kényszeríti a kernelt, hogy támogassa a copy-on-write-ot és a memória túlvállalását (overcommit). Azt javasolják, hogy programok indítására a `posix_spawn`-t használjuk, a `fork`-ot pedig tartsuk meg azokra az esetekre, amelyekhez valóban másolat kell, mint az Android Zygote-ja ([Mobil operációs rendszerek: Android](../14-mobile-wearable-embedded/#android)), amely minden alkalmazást egy olyan folyamatból forkol, amelybe a futtatókörnyezet már be van töltve.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> shell, átirányítás, dup2, pipe, pipeline, fájl vége, beépített parancs, vfork, posix_spawn, clone, namespace, PDP-7, overcommit, Zygote</summary>

- **Shell:** az a program, amely beolvassa és lefuttatja a begépelt parancsokat, például a `bash`.
- **Átirányítás:** egy program kimenetének fájlba küldése (`>`), vagy bemenetének fájlból való táplálása (`<`) a terminál helyett.
- **dup2(a, b):** „a b számú jegy ugyanarra mutasson, mint az a számú jegy”.
- **Pipe, pipeline:** a pipe egyirányú csatorna a kernelben: amit az egyik folyamat az egyik végébe ír, azt a másik a másik végén olvassa ki. A pipeline (`a | b`) pipe-okkal köti össze a programokat, mint egy futószalag.
- **Fájl vége** (end-of-file): jelzés az olvasónak, hogy több adat nem jön.
- **Beépített parancs:** olyan parancs, amelyet a shell maga hajt végre ahelyett, hogy programot indítana, mert magát a shellt kell megváltoztatnia (`cd`).
- **vfork:** gyorsabb fork, amelyben a gyerek kölcsönveszi a szülő memóriáját, amíg új programot nem indít; a szülő addig vár.
- **posix_spawn:** egyetlen hívás, amely azt jelenti: „indítsd el ezt a programot egy új folyamatban”, előzetes másolás nélkül.
- **clone:** a Linux általános hívása folyamatok és szálak létrehozására; a beállításai mondják meg, min osztozik az új a létrehozójával.
- **Namespace:** Linux-funkció, amely egy folyamatcsoportnak saját nézetet ad valamiről (folyamatszámok, hálózat, fájlok); a konténerek ezekből épülnek.
- **PDP-7, PDP-11:** az 1960-as évek végének és az 1970-es éveknek kis számítógépei, amelyeken a Unixot először megírták.
- **Overcommit** (a memória túlvállalása): több memória ígérése a programoknak, mint amennyi a gépben van, abban bízva, hogy nem használják ki egyszerre mindet.
- **Zygote:** egy folyamat Androidon, amely egyszer indul el, és már minden be van töltve benne, ami egy alkalmazásnak kell; minden új alkalmazás ennek másolataként jön létre, ami sokkal gyorsabb, mint a semmiből indulni.

</details>

## Szálak

Egy folyamatnak egy címtartománya és a klasszikus modellben egyetlen vezérlési szála van. Sok programnak azonban több, közös adatokon dolgozó vezérlési szálra van szüksége: egy webszervernek, amely egyszerre sok klienst szolgál ki, egy szövegszerkesztőnek, amely gépelés közben ellenőrzi a helyesírást, egy numerikus programnak, amely a processzor összes magját kihasználja. Ezt több folyamat is megoldhatná, de akkor explicit IPC-n (lásd a következő részt) keresztül kellene megosztaniuk az adatokat, a folyamatok létrehozása és a köztük való váltás pedig drága. A **szál** vezérlési szál egy folyamaton belül: saját utasításszámlálója, regiszterei és verme van, minden máson viszont a folyamat többi szálával osztozik (Arpaci-Dusseau & Arpaci-Dusseau, 2023). Az előnyök:

- **Reszponzivitás:** az egyik szál várhat a lemezre vagy a hálózatra, miközben egy másik életben tartja a felhasználói felületet.
- **Megosztás:** a szálak közvetlenül osztoznak a memórián, másolás és rendszerhívások nélkül; egy mutató minden szálban ugyanazt jelenti.
- **Takarékosság:** egy szál létrehozása és az ugyanazon folyamat szálai közötti váltás olcsóbb, mint ugyanez folyamatokkal, mert nem kell új címtartomány, és köztük nincs laptáblaváltás (a vele járó TLB-ürítéssel).
- **Párhuzamosság:** egy folyamat szálai egyszerre több magon futhatnak.

Az ár az, hogy minden közös változó versenyhelyzet tárgya lehet: a szinkronizáció, a [következő előadás](../07-concurrency-deadlocks-scheduling/#a-kritikus-szakasz-problémája) témája, a programozó mindennapi problémájává válik.

### Mi közös a szálakban, és mi a sajátjuk

![Egy folyamat négy szállal: mind közösen használják a kódot, a globális adatokat és a BSS-t, a heapet, a memóriatérképet és a laptáblákat, a megnyitott fájlokat, a szignálkezelőket, a PID-et és a felhasználói és csoportazonosítókat, az aktuális könyvtárat és a korlátokat; minden szálnak saját TID-je, regiszterei, verme, TLS-e, szignálmaszkja és ütemezési állapota van](threads-share.svg)

Minden szálnak saját **verme** van, mert mindegyik a saját függvényhívás-láncának közepén tart, és saját **regiszterei**, amelyeket a kernel ment el, amíg a szál nem fut. Lehet **TLS**-e (thread-local storage, szálankénti tároló) is: a GNU C-ben `__thread` kulcsszóval deklarált változók (C11-ben `_Thread_local`, C++11-ben és C23-ban `thread_local`) szálanként egyszer léteznek, ugyanazon a néven, de minden szálban más címen. A C könyvtár az `errno`-hoz használ TLS-t, hogy az egyik szál hibája ne írja felül azt a hibakódot, amelyet egy másik szál éppen kiolvasni készül. x86-64-en az `fs` szegmensregiszter az aktuális szál TLS-blokkjára mutat, és a kernel a szállal együtt váltja.

A megosztásnak következményei vannak a könyvtárak tervezésére. Egy függvény **szálbiztos** (thread-safe), ha több szál egyszerre hívhatja; a rejtett statikus állapotot tartó függvények, például a `strtok` vagy a klasszikus `localtime`, nem azok, ezért vezetett be a POSIX újrahívható (re-entrant) változatokat (`strtok_r`, `localtime_r`). Egyes, az egész folyamatra vonatkozó műveletek pedig minden szálra hatnak: ha bármelyik szál meghívja az `exit()`-et, az egész folyamat véget ér; a folyamatnak küldött szignált egy olyan szál kapja meg, amely nem blokkolja.

### Felhasználói szintű és kernelszintű szálak

A szálak két helyen valósíthatók meg, és a köztük lehetséges leképezéseknek nevük van (Silberschatz et al., 2018):

![Három szálmodell. N:1: négy felhasználói szálat egy szálkönyvtár ütemez egyetlen kernelszálra. 1:1: a négy felhasználói szál mindegyike saját kernelszál. M:N: négy felhasználói szálat egy futtatókörnyezet ütemez két kernelszálra; a kernelszálakat a kernel ütemezi két processzorra](thread-models.svg)

- **N:1, felhasználói szintű szálak.** Egy, a folyamaton belüli könyvtár teljes egészében a felhasználói térben valósítja meg a szálakat: minden szálhoz tart egy vermet és mentett regisztereket, és felhasználói módban vált közöttük, például amikor egy szál egy zárra vár. A kernel egyetlen folyamatot lát. A váltás nagyon gyors (egy függvényhívásnyi munka), és bármilyen kernelen működik. Ha azonban egy szál blokkoló rendszerhívást hajt végre, a kernel az egész folyamatot blokkolja, és minden szál megáll; a szálak ráadásul nem futhatnak több magon. A korai Java „green threads” és a GNU Portable Threads könyvtár így működött.
- **1:1, kernelszintű szálak.** Minden szál a kernel által ütemezett külön entitás. A blokkoló hívások csak egy szálat blokkolnak, a szálak párhuzamosan futnak több magon, és a kernel ütemezője igazságosan bánik velük; a szál létrehozásához és a szálak közötti váltáshoz viszont a kernel kell. A Linux, a Windows és a macOS ezt a modellt használja a natív szálaihoz.
- **M:N, hibrid.** Egy futtatókörnyezet sok felhasználói szintű szálat ütemez kevesebb kernelszálra. Egyesíti az olcsó szálakat a párhuzamossággal, de bonyolult: a futtatókörnyezetnek tudnia kell, mikor blokkol egy kernelszál, hogy egy másik felhasználói szálat egy másik kernelszálon futtathasson. A *scheduler activations* pontosan erre javasolt kernelből érkező visszahívásokat (upcall) (Anderson et al., 1992), és a Solaris és a NetBSD egy ideig M:N modellt használt.

A Linux is kipróbált M:N terveket, de a fejlesztői arra jutottak, hogy egy gyors kernellel működő 1:1 modell egyszerűbb és elég gyors. A **Native POSIX Thread Library** (NPTL), amely 2003 óta a glibc része, 1:1 modellű; a szerzői arról számoltak be, hogy 100 000 szál elindítása és leállítása, amely korábban 15 percig tartott, az NPTL-lel és az érdekében végrehajtott kernelmódosításokkal 2 másodperc alatt lefutott (Drepper & Molnar, 2003). Az M:N nyelvi szinten tért vissza, ahol a futtatókörnyezet ellenőrzi az összes blokkoló műveletet:

- A Go **goroutine**-jai ugyanabban a címtartományban párhuzamosan futó függvények, kis, szükség szerint növekvő vermekkel; a Go futtatókörnyezete néhány OS-szálra (alapértelmezés szerint magonként egyre) multiplexeli őket, így „ha az egyik blokkolna, például I/O-ra várva, a többi tovább fut” (The Go Authors, n.d.). Egy Go program több százezer goroutine-t is futtathat.
- A Java 21 **virtuális szálai** (Pressler & Bateman, 2023) olyan `Thread` objektumok, amelyek nincsenek egy OS-szálhoz kötve: a JVM a futás idejére egy *carrier* (hordozó) szálra helyezi (mount) a virtuális szálat, és a legtöbb esetben leveszi róla (unmount), amikor blokkol, például I/O-ban, így milliószámra létezhetnek.
- Az **async/await** a Pythonban, a JavaScriptben, a C#-ban és a Rustban még tovább megy: a taskok csak explicit `await` pontokon adják át a processzort, és egy vagy néhány szálban futó eseményhurok (event loop) futtatja őket (kooperatív ütemezés).

### Szálak Linuxon: taskok és clone-flagek

A Linux kernelnek nincs külön szálobjektuma. Az ütemezés egysége a **task** (egy `task_struct`), a szál pedig egyszerűen olyan task, amely erőforrásokon osztozik másokkal. A `pthread_create()` a `clone3()`-at hívja, olyan flagekkel, amelyek megosztást kérnek: `CLONE_VM` (a címtartomány), `CLONE_FS` (aktuális és gyökérkönyvtár, umask), `CLONE_FILES` (a leírótábla), `CLONE_SIGHAND` (szignálkezelők), `CLONE_THREAD` (ugyanaz a szálcsoport, így ugyanaz a PID), `CLONE_SYSVSEM` és `CLONE_SETTLS` (új TLS-blokk); egy vermet is átad, amelyet a glibc `mmap`-pel foglal le (alapértelmezés szerint 8 MiB, plusz egy védőlap). A `fork()` egyetlen megosztási flaget sem használ. A kettő között a flagek által megengedett sokféle kombináció áll, például egy olyan folyamat, amely csak a fájltábláján osztozik.

A Linux ezért kétféle azonosítót használ. Minden tasknak saját azonosítója, **TID**-je van, ezt a `gettid()` adja vissza. Egy folyamat taskjai **szálcsoportot** (thread group) alkotnak, amelynek azonosítója, a TGID, az első szál TID-je; a `getpid()` a TGID-et adja vissza, így egy folyamat minden szála ugyanazt a PID-et jelenti, ahogy a POSIX megköveteli. A `/proc/PID/task/` alatt szálanként egy könyvtár van, és a `ps -L` kilistázza őket (a [linuxos rész](#a-szálak-taskok) mindkettőt bemutatja). A [következő előadás](../07-concurrency-deadlocks-scheduling/#a-linux-ütemezése) ütemezője taskokat ütemez, nem folyamatokat.

### POSIX-szálak

A szálak hordozható C-interfésze a **pthreads** (POSIX threads; Kerrisk, 2010, 29–33. fejezet):

```c
#include <pthread.h>

void *worker(void *arg) { /* ... */ return NULL; }

pthread_t t;
pthread_create(&t, NULL, worker, arg);   /* start worker(arg) in a new thread  */
pthread_join(t, &result);                /* wait for it and get its return value */
```

Egy szál akkor ér véget, amikor az indítófüggvénye visszatér, vagy amikor meghívja a `pthread_exit()`-et. A folyamathoz hasonlóan a befejeződött szál is megőrzi az eredményét, amíg egy másik szál be nem várja (join); azt a szálat, amelyet senki sem fog bevárni, **le kell választani** (detach, `pthread_detach`), hogy az erőforrásai azonnal felszabaduljanak. A közös adatokat `pthread_mutex_t` és `pthread_cond_t` védi, a [következő előadás](../07-concurrency-deadlocks-scheduling/#szemaforok-több-mint-egy-zár) mutexei és feltételváltozói.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> szál, reszponzivitás, párhuzamosság, TLB, TLS, szálbiztos, újrahívható, felhasználói szintű szál, kernelszintű szál, N:1, 1:1, M:N, NPTL, goroutine, virtuális szál, carrier szál, async/await, eseményhurok, task, umask, TID, TGID, pthreads, join, detach, versenyhelyzet, mutex, feltételváltozó</summary>

- **Szál:** egy munkavonal egy folyamaton belül; egy folyamat minden szála ugyanazt a memóriát látja.
- **Reszponzivitás:** a program akkor is reagál a felhasználóra, amikor közben valami máson dolgozik.
- **Párhuzamosság:** valóban több dolog egyidejű végzése, több processzormagon.
- **TLB:** a legutóbbi címfordítások kis gyorsítótára a processzorban; ha egy másik folyamat memóriájára váltunk, újra fel kell tölteni.
- **TLS** (thread-local storage, szálankénti tároló): olyan változók, amelyekből minden szálnak saját példánya van, mint minden szakácsnak a saját jegyzetfüzete a közös konyhában.
- **Szálbiztos, újrahívható:** egy függvény szálbiztos, ha több szál egyszerre használhatja anélkül, hogy összekeverné az adataikat; az újrahívható (re-entrant) változat minden munkaadatát a hívó által megadott változókban tartja.
- **Felhasználói szintű szál:** olyan szál, amelyről csak a programon belüli könyvtár tud; a kernel egyetlen folyamatot lát. **Kernelszintű szál:** olyan szál, amelyről a kernel tud, és amelyet maga ütemez.
- **N:1, 1:1, M:N:** hány programszál képződik le hány kernelszálra: sok egyre, egy egyre, vagy sok néhányra.
- **NPTL:** a Linux szálkönyvtára, a C könyvtár része.
- **Goroutine:** a Go könnyűsúlyú szála; a Go futtatókörnyezete néhány valódi szálat oszt meg nagyon sok goroutine között.
- **Virtuális szál, carrier szál:** a Java könnyűsúlyú szála; futás közben egy valódi (carrier, hordozó) szálon ül, és amikor várnia kell, leszáll róla, így a hordozó egy másikat futtathat.
- **async/await, eseményhurok:** olyan programozási stílus, amelyben a taskok kifejezetten megmondják, hol hajlandók várni (`await`); egyetlen hurok azt a taskot futtatja, amelyik éppen kész a folytatásra.
- **Task:** a Linux neve mindarra, amit ütemez: egy egyszálú folyamatra vagy egy folyamat egyik szálára.
- **umask:** folyamatonkénti beállítás, amely jogosultságokat vesz el az újonnan létrehozott fájloktól.
- **TID, TGID:** a szálazonosító (thread ID), egy task száma; a szálcsoport-azonosító (thread group ID), a folyamat összes szála által közösen használt szám (ezt adja vissza a `getpid()`).
- **pthreads:** a Unix-szerű rendszerek szabványos szálkönyvtára.
- **Join, detach:** egy szál bevárása (join) azt jelenti, hogy megvárjuk a befejeződését, és átvesszük az eredményét; a leválasztott (detached) szál maga takarít el maga után, és nem lehet bevárni.
- **Versenyhelyzet:** olyan hiba, amelyben az eredmény attól függ, hogy két szál közül melyik a gyorsabb, mint amikor két ember egyszerre szerkeszti ugyanazt a bevásárlólistát, és az egyik kihúzza, amit a másik éppen beírt.
- **Mutex, feltételváltozó:** a mutex olyan zár, amelyet egyszerre csak egy szál birtokolhat, mint egyetlen fürdőszoba kulcsa; a feltételváltozó lehetővé teszi, hogy egy szál aludjon, amíg egy másik szál nem szól neki, hogy valami megváltozott.

</details>

## Folyamatok közötti kommunikáció

A folyamatok szándékosan el vannak szigetelve egymástól: mindegyiknek saját címtartománya van, és egyik sem olvashatja a másik memóriáját. Ha együtt kell működniük, a kernel által nyújtott **folyamatok közötti kommunikációs** (inter-process communication, IPC) mechanizmusokat használják. Ezek két családba tartoznak: azok a mechanizmusok, amelyek **a kernelen keresztül adják át az adatokat** (pipe-ok, üzenetsorok, socketek), és az **osztott memória**, amellyel a folyamatok közvetlenül ugyanazokat a fizikai lapokat érik el. A szignálok egy harmadik, különleges fajtát alkotnak: szinte semmilyen adatot nem visznek, csak azt a tényt, hogy valami történt (Stevens & Rago, 2013; Kerrisk, 2010).

![Két módja az adatok folyamatok közötti mozgatásának. A kernelen keresztül: az A folyamat write() hívása a pufferét egy kernelpufferbe másolja, a B folyamat read() hívása pedig onnan ismét kimásolja: üzenetenként két rendszerhívás és két másolás, a szinkronizációt a kernel végzi. Osztott memória: az A és a B folyamat ugyanazokat a lapkereteket képezi le a címtartományába; A írásait B rendszerhívások és másolások nélkül látja, de a szinkronizációról maguknak kell gondoskodniuk](ipc-copies.svg)

### Pipe-ok és FIFO-k

A **pipe** egyirányú bájtfolyam egy kernelpufferen keresztül, a `pipe(fd)` hívással hozzuk létre. Amit az `fd[1]`-be írunk, az az `fd[0]`-ból olvasható ki, sorrendben és üzenethatárok nélkül. A két oldalt a kernel szinkronizálja: az olvasó blokkol, amíg a pipe üres, az író blokkol, amíg tele van (az alapértelmezett kapacitás Linuxon 64 KiB, és az `fcntl(F_SETPIPE_SZ)` hívással módosítható); a legfeljebb `PIPE_BUF` bájtos (Linuxon 4096) írások atomiak, így nem keverednek más írók adataival (Linux man-pages project, n.d.-b). Az olvasó akkor kap fájlvéget, ha minden író vég be van zárva; az az író, amelynek minden olvasója eltűnt, `SIGPIPE` szignált (vagy `EPIPE` hibát) kap. Mivel a pipe-nak nincs neve, csak rokon folyamatok használhatják: a létrehozója és a leírókat öröklő gyerekei, ahogy egy shell pipeline-ban.

A **FIFO** vagy *named pipe* (`mkfifo name`) olyan pipe, amelynek neve van a fájlrendszerben, így nem rokon folyamatok is megnyithatják, mint egy fájlt; az adatok ekkor sem érintik a lemezt ([Fájlrendszerek: fájltípusok](../10-file-systems/#fájltípusok)).

### Szignálok

A **szignál** kis, aszinkron értesítés, amelyet a kernel vagy egy másik folyamat küld egy folyamatnak: „nullával osztottál”, „a gyereked befejeződött”, „a felhasználó lenyomta a Ctrl-C-t”, „kérlek, fejeződj be”. A [megszakításokról szóló előadás](../05-interrupts/#a-programmegszakításokból-szignálok-lesznek) bemutatta, hogyan lesznek a processzor programmegszakításaiból szignálok; a szignálok bizonyos értelemben a felhasználói folyamatok megszakításai. Minden szignálnak száma és alapértelmezett művelete van:

| Szignál | Szám (x86-64) | Tipikus ok | Alapértelmezett művelet |
| --- | --- | --- | --- |
| `SIGINT` | 2 | Ctrl-C a terminálon | befejezés |
| `SIGKILL` | 9 | `kill -9`; nem kapható el és nem hagyható figyelmen kívül | befejezés |
| `SIGSEGV` | 11 | érvénytelen memória-hozzáférés | befejezés core dumppal |
| `SIGPIPE` | 13 | írás olvasó nélküli pipe-ba | befejezés |
| `SIGALRM` | 14 | lejárt az `alarm()`-mal beállított időzítő | befejezés |
| `SIGTERM` | 15 | udvarias kérés a befejezésre (a `kill` alapértelmezése) | befejezés |
| `SIGCHLD` | 17 | egy gyerek befejeződött vagy leállt | figyelmen kívül hagyás |
| `SIGCONT` | 18 | egy leállított folyamat folytatása (`fg`, `bg`) | folytatás |
| `SIGSTOP` | 19 | leállítás; nem kapható el és nem hagyható figyelmen kívül | leállítás |

Egy folyamat az alapértelmezett műveletet **szignálkezelővel** (handler) helyettesítheti, a `sigaction()` hívással telepített függvénnyel. Amikor a szignál megérkezik, a kernel ott szakítja meg a folyamatot, ahol éppen tart (két utasítás között, vagy egy blokkoló rendszerhívásban), előkészíti a kezelő futtatását a folyamat vermén, és a kezelő visszatérése után folytatja a megszakított kódot. A folyamat szignálmaszkja által blokkolt szignálok függőben maradnak, amíg a blokkolást fel nem oldják. A közönséges szignálok nem állnak sorba: két `SIGUSR1`, amely akkor érkezik, amikor egy már függőben van, csak egyszer kézbesítődik.

Mivel a kezelő bárhol megszakíthatja a programot, akár a `malloc` vagy a `printf` közepén is, miközben azok a belső adatszerkezeteiket módosítják, a kezelő csak **async-signal-safe** függvényeket hívhat: ez a POSIX egy rövid listája, amelyen rajta van a `write`, az `_exit`, a `kill` és a `sigaction`, de nincs rajta a `printf`, a `malloc`, sem semmi, ami zárat vesz fel (Linux man-pages project, n.d.-e). A legbiztonságosabb kezelő beállít egy `volatile sig_atomic_t` típusú jelzőt, és visszatér; a főprogram ellenőrzi a jelzőt. Ez ugyanaz a probléma, mint a megszakításkezelők közös adatai a [megszakításokról szóló előadásban](../05-interrupts/#megszakítások-és-párhuzamosság).

Egy szignál egy **blokkoló rendszerhívást** is megszakíthat, például egy üres pipe-on végrehajtott `read()`-et. A hívás ekkor vagy `EINTR` („interrupted system call”) hibával tér vissza, és a programnak meg kell ismételnie, vagy, ha a kezelőt `SA_RESTART` flaggel telepítették, a kernel a kezelő után automatikusan újraindítja. A [linuxos rész](#egy-szignál-megszakít-egy-rendszerhívást) mindkettőt bemutatja. (A szignállal megszakítható várakozások a [következő előadás](../07-concurrency-deadlocks-scheduling/#a-folyamatok-állapottere) megszakítható `S` alvásai.)

### Osztott memória

Az **osztott memória** ugyanazokat a fizikai lapkereteket képezi le több folyamat címtartományába. Beállítás után a folyamatok közönséges utasításokkal olvassák és írják: se rendszerhívás, se másolás, ettől ez a leggyorsabb IPC-mechanizmus. A POSIX-interfésszel az egyik folyamat a `shm_open("/name", O_CREAT | O_RDWR, 0600)` hívással névvel ellátott objektumot hoz létre (Linuxon egy fájlt a `/dev/shm` memóriabeli fájlrendszerben), az `ftruncate()`-tel beállítja a méretét, és minden folyamat, amely ugyanezt a nevet megnyitja, az `mmap(..., MAP_SHARED, fd, 0)` hívással képezi le (Linux man-pages project, n.d.-d). Rokon folyamatok egyszerűen a `fork()` előtt létrehozott névtelen `MAP_SHARED` leképezést is használhatnak. A régebbi System V interfész (`shmget`, `shmat`) ugyanezt numerikus kulcsokkal végzi.

Az osztott memória használóit a kernel nem szinkronizálja. Ezt a folyamatoknak maguknak kell megtenniük, a [következő előadás](../07-concurrency-deadlocks-scheduling/#a-kölcsönös-kizárás-három-rétege) eszközeivel: az osztott területen belül `sem_init(&s, 1, value)` hívással létrehozott szemaforral (az 1 azt jelenti: „folyamatok között megosztott”), `PTHREAD_PROCESS_SHARED` attribútumú mutexszel vagy atomi változókkal. Az osztott memória a mutatókkal is óvatosságot kíván: a terület különböző folyamatokban különböző címekre lehet leképezve, ezért a benne lévő adatszerkezeteknek mutatók helyett eltolásokat (offseteket) kell használniuk.

### Üzenetsorok

Az **üzenetsor** üzeneteket tárol, nem bájtokat: minden `mq_send()` egy üzenetet tesz hozzá, minden `mq_receive()` egy teljes üzenetet vesz ki, így a határok megmaradnak. A POSIX üzenetsoroknak (`mq_open`, `mq_send`, `mq_receive`) nevük és prioritásaik vannak (a legmagasabb prioritású üzenet érkezik meg elsőként), valamint korlátaik: Linuxon alapértelmezés szerint legfeljebb 10, egyenként legfeljebb 8 KiB-os üzenet lehet egy sorban. A System V üzenetsorok (`msgget`, `msgsnd`, `msgrcv`) lehetővé teszik, hogy a fogadó egy típusmező alapján válogasson az üzenetek között. A pipe-okhoz hasonlóan mindkettő bemásolja az adatokat a kernelbe, majd ki is onnan.

### Socketek

A **socket** kommunikációs végpont, amely hálózaton keresztül is használható, és ez az egyetlen mechanizmus a listában, amely különböző gépeken futó folyamatokat is összeköthet. Az `AF_INET` vagy `AF_INET6` címcsaláddal TCP-t (`SOCK_STREAM`, megbízható bájtfolyam) vagy UDP-t (`SOCK_DGRAM`, különálló datagramok) beszél a hálózaton. A **Unix domain socketek** (`AF_UNIX`) ugyanezt az interfészt használják egy gépen belül, címként egy fájlrendszerbeli útvonallal (vagy a `socketpair()` által létrehozott névtelen párral); kétirányúak, támogatják a folyamokat, a datagramokat és a sorrendezett csomagokat, és két olyan dologra képesek, amire más mechanizmus nem: **fájlleírókat** adhatnak át egyik folyamatból a másikba (`SCM_RIGHTS`), és közölhetik a fogadóval a küldő PID-jét és felhasználói azonosítóját (`SO_PEERCRED`) (Linux man-pages project, n.d.-g). A legtöbb helyi szolgáltatást ezeken keresztül érjük el: a systemd-t és a D-Bust, az X és a Wayland display szervert, a Docker daemont (`/var/run/docker.sock`), az adatbázisokat.

### Melyik mechanizmust válasszuk?

| Mechanizmus | Irány | Határok | Nem rokon folyamatok | Gépek között | Másolások üzenetenként | Szinkronizáció |
| --- | --- | --- | --- | --- | --- | --- |
| pipe | egyirányú | bájtfolyam | nem (öröklés) | nem | 2 | a kernel végzi |
| FIFO | egyirányú | bájtfolyam | igen (útvonal) | nem | 2 | a kernel végzi |
| üzenetsor | soronként egyirányú | üzenetek, prioritások | igen (név) | nem | 2 | a kernel végzi |
| Unix domain socket | kétirányú | folyam vagy datagramok | igen (útvonal) | nem | 2 | a kernel végzi |
| TCP/UDP socket | kétirányú | folyam / datagramok | igen (cím) | igen | 2 vagy több | a kernel végzi |
| osztott memória | tetszőleges | nincs: csak memória | igen (név) | nem | 0 | a folyamatok végzik |
| szignál | egyirányú | csak egy szám | igen (PID, jogosultság) | nem | nincs | a kernel végzi |

Ökölszabályként: pipe egy szülő és gyerekei közötti adatfolyamhoz, Unix domain socket helyi kliens–szerver protokollhoz (és mindenhez, aminek leírókat kell átadnia vagy ellenőriznie kell a kliens identitását), TCP socket, ha a partner másik gépen is lehet, osztott memória nagy adatmennyiséghez vagy nagyon kis késleltetéshez, explicit szinkronizációval, szignálok pedig csak értesítésekhez. A [linuxos rész](#ipc-késleltetés-és-áteresztőképesség) négyet megmér közülük.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> IPC, FIFO, PIPE_BUF, atomi, SIGPIPE, szignál, alapértelmezett művelet, szignálkezelő, core dump, szignálmaszk, függőben lévő szignál, async-signal-safe, sig_atomic_t, EINTR, SA_RESTART, osztott memória, /dev/shm, szemafor, folyamatok között megosztott szemafor, üzenetsor, socket, TCP, UDP, Unix domain socket, SCM_RIGHTS, D-Bus</summary>

- **IPC** (inter-process communication, folyamatok közötti kommunikáció): bármilyen mód, amellyel különálló folyamatok adatokat vagy üzeneteket cserélnek.
- **FIFO** (first in, first out), named pipe: olyan pipe, amelynek neve van a fájlrendszerben, így bármelyik folyamat megtalálhatja.
- **PIPE_BUF, atomi:** a legfeljebb `PIPE_BUF` bájtos írás egy darabban (atomian) kerül a pipe-ba, sosem keveredik egy másik író adataival.
- **SIGPIPE:** az a szignál, amelyet egy folyamat akkor kap, ha olyan pipe-ba ír, amelyből már senki sem olvas.
- **Szignál:** rövid értesítés a kerneltől vagy egy másik folyamattól, mint egy vállveregetés; csak azt mondja meg, milyen fajta esemény történt.
- **Alapértelmezett művelet, szignálkezelő:** az, ami egy folyamattal szignál érkezésekor történik, ha nem rendelkezett másképp (gyakran: befejeződik); illetve egy függvény, amelyet a program azért ad meg, hogy maga reagáljon.
- **Core dump:** a program memóriájának másolatát tartalmazó fájl az összeomlás pillanatából, későbbi vizsgálatra egy debuggerrel.
- **Szignálmaszk, függőben lévő szignál:** azoknak a szignáloknak a halmaza, amelyeket a folyamat egyelőre visszatartatni kért; a visszatartott szignál várakozik (függőben van), amíg át nem engedik.
- **Async-signal-safe:** olyan függvény, amely szignálkezelőből is hívható, mert nem okozhat neki kárt, ha önmagát szakítja meg.
- **sig_atomic_t:** egész típus, amely egy lépésben olvasható és írható, így biztonságos jelzőként szolgálhat a kezelő és a főprogram között.
- **EINTR, SA_RESTART:** az EINTR a „szignál szakította meg, próbáld újra” hiba; az SA_RESTART beállítással a kernel magától próbálkozik újra.
- **Osztott memória, /dev/shm:** olyan memória, amelyet két vagy több folyamat is lát; Linuxon a névvel ellátott darabok fájlokként jelennek meg a `/dev/shm` alatt, amely a RAM-ban van.
- **Szemafor:** várakozásra használt számláló: ha nulla, és el akarunk venni belőle, elalszunk, amíg valaki hozzá nem ad, mint amikor szabad parkolóhelyre várunk.
- **Folyamatok között megosztott szemafor:** osztott memóriában elhelyezett szemafor, így több folyamat is használhatja.
- **Üzenetsor:** postafiók a kernelben, ahová a folyamatok teljes üzeneteket adnak fel, és ahonnan teljes üzeneteket vesznek ki.
- **Socket:** egy kommunikációs csatorna végpontja, mint egy telefonaljzat; a másik vége ugyanazon vagy egy másik számítógépen is lehet.
- **TCP, UDP:** az internet két fő adatküldési módja: a TCP olyan, mint egy telefonhívás (megbízható, sorrendben érkezik), az UDP olyan, mint a képeslapok (különállók, elveszhetnek).
- **Unix domain socket:** olyan socket, amely csak ugyanazon a számítógépen futó programokat köt össze, címként egy fájlnévvel.
- **SCM_RIGHTS:** mód arra, hogy egy megnyitott fájlleírót Unix domain socketen keresztül átadjunk egy másik folyamatnak, mint egy ruhatári jegy továbbadását.
- **D-Bus:** üzenetküldő rendszer, amelyen keresztül a Linux asztali és rendszerprogramjai egymással beszélnek.

</details>

## Az operációs rendszer munka közben

A folyamatok, a rendszerhívások és az IPC munka közben láthatatlanok. A Linux többféle módot kínál a megfigyelésükre, mindegyik más réteget lát (Gregg, 2019):

![Megfigyelőeszközök rétegenként: a gdb és a valgrind az alkalmazás kódját, az ltrace a megosztott könyvtárak hívásait, az strace a rendszerhívás-interfészt, a /proc és a /sys a kernel állapotát, a perf stat a hardveres számlálókat nézi; a perf record és az eBPF/bpftrace minden réteget lát](observability.svg)

- **`/proc` és `/sys`.** Két virtuális fájlrendszer, amelyeken keresztül a kernel fájlokként mutatja meg az adatszerkezeteit (Linux man-pages project, n.d.-c). A `/proc/PID/` alatt folyamatonként egy könyvtár van: `status` (név, állapot, azonosítók, memória, környezetváltások), `maps` (a címtartomány), `fd/` (a megnyitott leírók, szimbolikus linkekként), `cmdline`, `environ`, `cwd`, `exe`, `limits`, `wchan` és `syscall` (hol várakozik egy alvó folyamat), `task/` (a szálai). A `/proc` rendszerszintű információkat is tartalmaz (`/proc/meminfo`, `/proc/interrupts`), a `/sys` pedig az eszközmodellt és a hangolható kernelparamétereket. Az olyan eszközök, mint a `ps`, a `top`, a `pstree` és az `lsof`, egyszerűen ezeket a fájlokat olvassák; a mappában lévő `ptree.py` egy 50 soros `pstree`.
- Az **`strace`** egy folyamat (`-f`-fel a gyerekei és szálai) rendszerhívásait követi nyomon: minden hívást dekódolt argumentumokkal, eredménnyel és a hiba nevével, valamint a szignálokat. Az `-e trace=…` kiválasztja a hívásokat, a `-c` hívásonként megszámolja a hívásokat és az időt, a `-T` megmutatja az egyes hívásokban töltött időt, a `-p PID` egy futó folyamathoz csatlakozik. A `ptrace` rendszerhívást használja, amelyen keresztül a kernel minden rendszerhívásba való belépéskor és kilépéskor megállítja a nyomon követett folyamatot, és megengedi a nyomkövetőnek, hogy megvizsgálja. Ez pontos, de lassú: a [linuxos rész](#nyomkövetés-strace-szel) egy olcsó rendszerhívásnál nagyjából 70-szeres lassulást mér.
- Az **`ltrace`** ugyanezt teszi egy szinttel feljebb, a megosztott könyvtárak hívásaira (`malloc`, `printf`, `strlen`), úgy, hogy töréspontokat helyez el a program könyvtári függvényhívásain.
- A **`gdb`** csatlakozhat egy futó folyamathoz, megállíthatja, és megmutathatja a szálait, a hívási vermét (`bt`) és bármelyik változóját; ez is a `ptrace`-t használja. A **Valgrind** egy szimulált processzoron futtatja a programot, és minden memória-hozzáférést ellenőriz, így megtalálja az inicializálatlan vagy felszabadított memória használatát és a memóriaszivárgásokat, 10–50-szeres lassulás árán.
- A **`perf`** a kernel `perf_events` alrendszerét használja: a `perf stat` a processzor hardveres számlálóival olyan eseményeket számol, mint a processzorciklusok, az utasítások, a gyorsítótár-hiányok, a környezetváltások és a laphibák; a `perf record` másodpercenként sokszor mintát vesz a futó kód hívási verméből, felhasználói és kernelmódban is, a `perf report` pedig megmutatja, hová ment az idő; a `perf trace` egy gyorsabb `strace`.
- Az **eBPF** lehetővé teszi, hogy kis programok fussanak a kernelen belül, szinte bármilyen eseményhez csatolva: kernelfüggvényhez (kprobe), felhasználói függvényhez (uprobe), statikus tracepointhoz (`sched:sched_process_fork`, `syscalls:sys_enter_execve`), időzítőhöz. A kernel minden programot ellenőriz a betöltés előtt (be kell fejeződnie, és csak olyan memóriát olvashat, amelyet szabad neki), a programok pedig a kernelen belül összesítik az adatokat, így csak összefoglalók másolódnak a felhasználói térbe. A **bpftrace** magas szintű nyelv egysoros eBPF-programokhoz (Gregg, 2019). Mivel nem állítják meg a megfigyelt folyamatokat, a perf és az eBPF forgalmas éles rendszereken is biztonságosan használható, ahol az `strace` mindent lelassítana.

Az előadáshoz használt gépen az `strace`, a `gdb` és a `valgrind` telepítve van; az `ltrace`, a `perf` és a `bpftrace` nincs, az eBPF-eszközökhöz pedig root jog és BPF-támogatással fordított kernel kell. Használatukat ezért laborfeladat mutatja be, kimenetek nélkül.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> megfigyelhetőség, /proc, /sys, strace, ptrace, ltrace, gdb, backtrace, valgrind, perf, hardveres számláló, mintavételezés, eBPF, kprobe, uprobe, tracepoint, verifier, bpftrace</summary>

- **Megfigyelhetőség** (observability): az, hogy kívülről, a működése megváltoztatása nélkül láthatjuk, mit csinál egy futó rendszer.
- **/proc, /sys:** olyan mappák, amelyeknek a fájljai egyetlen lemezen sincsenek rajta; olvasásukkal élő információt kérünk a kerneltől.
- **strace:** eszköz, amely kiírja egy program minden kérését (rendszerhívását) a kernelhez.
- **ptrace:** az a rendszerhívás, amellyel egy folyamat (debugger vagy nyomkövető) megállíthat, megvizsgálhat és irányíthat egy másikat.
- **ltrace:** olyan, mint az strace, de a könyvtári hívásokra.
- **gdb, backtrace:** a GNU debugger; a backtrace az éppen folyamatban lévő függvények listája, a legbelsővel kezdve.
- **valgrind:** eszköz, amely egy szimulált processzoron lassan futtatja a programot, és jelzi a memóriahibákat.
- **perf, hardveres számláló, mintavételezés:** a perf a Linux teljesítménymérő eszköze; a hardveres számlálók a processzor számlálói (ciklusok, gyorsítótár-hiányok); a mintavételezés azt jelenti, hogy másodpercenként sokszor megnézzük, mit csinál a program, és megszámoljuk, hol tartott.
- **eBPF:** kis, ellenőrzött programok, amelyek a kernelen belül futnak, amikor kiválasztott események történnek, hogy megszámolják vagy rögzítsék őket.
- **kprobe, uprobe, tracepoint:** helyek, ahová egy eBPF-program csatolható: bármelyik kernelfüggvény, egy program bármelyik függvénye, vagy a kernel egy rögzített, névvel ellátott eseménye.
- **Verifier** (ellenőrző): a kernelnek az a része, amely egy eBPF-programot a futtatása előtt ellenőriz, hogy ne tudja összeomlasztani vagy megakasztani a kernelt.
- **bpftrace:** rövid nyelv eBPF-programok egy sorban való megírásához.

</details>

## Ugyanezek az elvek Linuxon (x86-64)

A bemutatók rootként futnak az előző előadások Ubuntu 24.04-es felhőbeli virtuális gépén: KVM-vendég 2 virtuális processzorral (2,1 GHz-es Intel Xeon), 8 GiB RAM-mal és swap nélkül, Linux 6.18, gcc 13.3, glibc 2.39, Python 3.13, strace 6.8 és gdb 15.1 szoftverrel. Minden program és szkript ebben a mappában van; a C programokat a bemutatott módon fordítjuk, a szkripteket `sh`-val futtatjuk. Az időértékek futásról futásra változnak, virtuális gépen jobban, mint valódi hardveren; az arányok számítanak.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> konzol, root, gcc, -O2, szkript, KVM-vendég</summary>

- **Konzol** (terminál): ablak, ahová szövegesen gépeljük be a parancsokat. A `$` jellel kezdődő sorokat mi írjuk be; a többi sor a számítógép válasza.
- **Root:** a rendszergazdai fiók.
- **gcc, -O2:** a C fordító, amelyet arra kérünk, hogy optimalizálja a kódot.
- **Szkript** (`.sh` fájl): fájlba mentett parancsok listája, amelyek egymás után futnak le.
- **KVM-vendég:** a Linux beépített hypervisora, a KVM alatt futó virtuális gép.

</details>

### Egy futó program címtartománya

A `layout.c` minden régióból kiírja valaminek a címét (egy függvényét, egy inicializált és egy inicializálatlan globális változóét, egy kis és egy nagy `malloc`-blokkét, egy könyvtári függvényét és egy lokális változóét), majd a saját `/proc/self/maps` fájljának azokat a sorait, amelyek ezeket tartalmazzák:

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

A sorrend megegyezik az ábráéval: alacsony címeken a text, majd a data és a BSS, aztán a heap; a felhasználói fél teteje közelében a könyvtárak, a leképezések és a verem. A kód olvasható és végrehajtható (`r-xp`), az adatok írhatók, de nem végrehajthatók (`rw-p`). A data és a BSS itt egyetlen lapon osztozik, mert együtt csak 712 bájtosak: a BSS-beli változó 8 bájttal az inicializált után van. A 100 bájtos blokk a heapből jött, az 1 MiB-os blokk viszont saját névtelen leképezést kapott, 1 MiB plusz egy lapnyi méretben (`0x101000` bájt) a glibc nyilvántartása miatt, mert meghaladja a glibc küszöbét, amely fölött az `mmap`-et használja. A heap véletlenszerű távolságra kezdődik a program fölött (address space layout randomisation, ASLR): ha kétszer futtatjuk a programot, minden cím megváltozik. A teljes térképet, a vDSO-val együtt, a [virtuális memóriáról szóló előadás](../09-virtual-memory/#egy-folyamat-címtartománya) mutatja be.

### Egy rendszerhívás, háromféleképpen

A `hello3.c` ugyanazt a `write` rendszerhívást hajtja végre a libc wrapperen, az általános `syscall()` függvényen és a puszta utasításon keresztül, majd érvénytelen fájlleíróval megismétli a hívást:

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

A kernel számára a három mód azonos: három `write` hívás. A puszta utasítás a kernel nyers válaszát adja vissza, a −9-et; a wrapper ezt −1-gyé és `errno` = 9-cé alakítja. Az `strace` futás a C könyvtár pufferelését is megmutatja: mivel a kimenet nem terminálra, hanem fájlba megy, a három `printf` sor nem a `printf` hívásakor íródott ki, hanem összegyűlt, és egyetlen 191 bájtos `write`-tal íródott ki a program kilépésekor, a két sikertelen hívás után, amelyek a programban később következtek. Maga a wrapper néhány utasítás a C könyvtárban:

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

Az argumentumok már az `rdi`, `rsi` és `rdx` regiszterben vannak, mert a C hívási konvenció az első három argumentumot ugyanezekben a regiszterekben adja át, így a wrapper csak az 1-es számot tölti az `eax`-be, és végrehajtja a `syscall` utasítást. Az előjel nélküli összehasonlítás a `0xfffffffffffff000` (−4096) értékkel pontosan a −4095 és −1 közötti eredményeket fogja meg, és az `errno`-t beállító kódra ugrik. (A `__libc_single_threaded` vizsgálata többszálú programokban egy lassabb utat választ, amely a szálak megszakítását, a cancellationt is kezeli.) A kernel minden új programnak megmondja, hol van a vDSO-ja:

```console
$ LD_SHOW_AUXV=1 /bin/true | grep -E "SYSINFO|AT_PAGESZ|AT_EXECFN"
AT_SYSINFO_EHDR:      0x7fd8f39a8000
AT_PAGESZ:            4096
AT_EXECFN:            /bin/true
```

### A kernelbe lépés ára

A `sccost.c` kétmillió hívást mér meg mindegyikből: egy közönséges függvényét, a `getpid()`-ét a wrapperen és a `syscall()`-on keresztül, valamint a `clock_gettime()`-ét a vDSO-n keresztül és `syscall()`-lal a kernelbe kényszerítve:

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

A `getpid()`, amely csak kiolvas egy számot a `task_struct`-ból, nagyjából 120–135 ns-ba kerül (az egyik futás 170 ns-ot mért, ez a virtuális gép zavara), ami egy függvényhívás mintegy 60-szorosa, és 2,1 GHz-en körülbelül 260 órajelciklus; a [virtualizációról szóló előadás](../13-virtualization-containerization/#egy-vm-exit-ára) ugyanezen a gépen 126 ns-ot mért a `getppid()`-re. Ennek szinte egésze maga az átlépés. A vDSO-s `clock_gettime()` 30–39 ns-ba kerül: nagyjából ötödannyiba, mint ugyanez a függvény a kernelben, mert sosem hagyja el a felhasználói módot. Az `strace -c` megerősíti, hogy a vDSO-hívások a kernel számára láthatatlanok:

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

A program 200 000-szer hívta meg a `clock_gettime()`-ot, a kernel azonban csak a 100 000 kényszerített hívást látta. A mérés a nyomkövetés árát is megmutatja: `strace` alatt minden rendszerhívás 8–9 µs-ig tartott, mintegy 70-szer tovább, mert a kernel hívásonként kétszer megállítja a folyamatot, és felébreszti a nyomkövetőt, a vDSO-hívások viszont teljes sebességgel futottak.

### fork, exec, exit és wait

A `lifecycle.c` három gyereket indít. Mindegyik hozzáadja a saját sorszámát a szülő `x` változójának egy másolatához; a 0. gyerek 3-as állapottal lép ki, az 1. gyerek `execv()`-vel lefuttatja a `/bin/sh`-t, a 2. gyerek nullmutatón keresztül ír. A szülő mindhármat begyűjti:

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

Minden gyerek csak a saját `x`-másolatát változtatta meg. Az 1. gyerek az `exec` után is a 9350-es PID, de most egy másik programot, a shellt futtatja, amely kiírja a saját PID-jét (`$$`) és a szülője PID-jét. A gyerekek más sorrendben futottak, mint amelyben létrejöttek: a `fork()` után a szülő és a gyerekek függetlenek, és az ütemező dönt. A `waitpid()` dekódolt egy 3-as állapotú normál kilépést és egy `SIGSEGV` miatti halált. Az `strace` megmutatja a könyvtári függvények mögötti rendszerhívásokat:

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

A glibc `fork()`-ja egy megosztási flag nélküli `clone()`; a `SIGCHLD` az a szignál, amelyet a szülő a gyerek befejeződésekor kérni szeretne, a két `CLONE_CHILD_*` flag pedig lehetővé teszi, hogy a könyvtár feljegyezze a gyerek szálazonosítóját. Az `exit()`-ből `exit_group()` lesz, amely a folyamat összes szálát befejezi, a `waitpid()`-ből pedig `wait4()`. Az `ERESTARTSYS`-t tartalmazó sor a nyomkövetés mellékhatása, és csak egyes futásokban jelenik meg: egy másik, már befejeződött gyerek `SIGCHLD` szignálja megállította a nyomon követett szülőt a `wait4()`-en belül, hogy az `strace` láthassa a szignált; a kernel ezután magától újraindította a hívást (az `ERESTARTSYS` kernelen belüli kód, amelyet egy program sosem lát). Nyomkövető nélkül egy olyan `SIGCHLD`, amelynek alapértelmezett művelete a figyelmen kívül hagyás, semmit sem szakít meg.

### Árva folyamatok és subreaperek

Az `orphan.c` három generációt hoz létre: a nagyszülő forkol egy szülőt, amely forkol egy gyereket, és egy másodperc múlva kilép. A gyerek előtte és utána is kiírja a szülője PID-jét:

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

Az árva folyamatot az 1-es PID fogadta örökbe, a nagyszülő pedig nem tudott rá várni (a `waitpid(-1)` nem talált gyereket: −1, `errno` = `ECHILD`). A `prctl(PR_SET_CHILD_SUBREAPER, 1)` hívás után maga a nagyszülő fogadta örökbe árvává vált unokáját, és begyűjtötte az állapotát.

### Shell száz sorban

A `minish.c` a `minish-demo.txt` fájlt olvassa, amely néhány parancsot tartalmaz (ha a bemenete nem terminál, minden parancsot kiír a prompt után):

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

Az átirányítások, egy háromtagú pipeline és a kilépési állapotok működnek. Egy nem található parancs miatt az `execvp()` a gyerekben sikertelen lesz, a gyerek jelzi a hibát, és 127-es állapottal lép ki, ezt használják a shellek a „parancs nem található” esetre. Az utolsó sorok megmutatják, miért kell a `cd`-nek beépítettnek lennie: a `/proc/self` szimbolikus link annak a folyamatnak a könyvtárára, amelyik éppen feloldja, és mivel a `chdir()`-t maga a `minish` futtatta, az aktuális könyvtára a saját `/proc` könyvtára lett, ahogy a gyerekekben futó `pwd` és `grep ^Name status` megerősíti. A program szíve a pipeline-t felépítő ciklus:

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

A `trace-minish.sh` az `ls /etc | grep ^host >hosts.txt` parancsot `strace -ff` alatt futtatja, amely folyamatonként egy nyomkövetési fájlt ír, és kiírja, mit csinált a shell és a két gyereke, mielőtt az új programok elindultak:

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

Ez az életciklusról szóló rész ábrája, lépésről lépésre. A pipe a 3-as (olvasó vég) és a 4-es (író vég) leírót kapta. Az első gyerek a 4-est tette meg standard kimenetének, és mindkét eredetit bezárta; a második a 3-ast tette meg standard bemenetének, majd megnyitotta a `hosts.txt`-t, amely a legkisebb szabad számot, ismét a 3-ast kapta, és ezt tette meg standard kimenetének. A shell az első fork után bezárta az író vég saját másolatát, a második után az olvasó végét, majd megvárta mindkét gyereket. A shellben lévő `close(4)` nélkül a `grep` sosem észlelné a fájl végét.

### A folyamatfa a /proc-ból

A `ptree.py` a `/proc/*/stat` fájlokat olvassa (minden folyamat nevét, állapotát, szülőjének PID-jét és szálainak számát), és megrajzolja a fát. A `tree-demo.sh` elindít egy kis családot (egy `sleep`-et, egy három további szállal rendelkező Python-folyamatot és egy alshellt saját gyerekkel), majd megrajzolja a fát a saját shellje alatt:

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

Az utolsó gyerek, az `R` állapotú `python3(11153)`, maga a `ptree.py`, amely futás közben olvassa a `/proc`-ot. Az egész fának két gyökere van, az 1-es és a 2-es PID, amelyek szülője a 0. Ezen a gépen az 1-es PID nem a `systemd`, hanem a felhős sandbox saját kis init programja (`process_api`); a `kthreadd` minden kernelszál szülője.

### A szálak taskok

A `threads.c` három szálat indít. Mindegyik ezerszer növel egy mutex által védett globális számlálót, egy szálankénti számlálót (`__thread int mine`) és egy, a vermén lévő lokális változót, majd kiírja az azonosítóit és a címeket:

```console
$ gcc -O2 -pthread -o threads threads.c
$ ./threads
thread 0: pid 24450 tid 24451  &shared 0x5617f2382068  &mine 0x7f77441ff6bc  &local 0x7f77441fee94  mine = 1000
thread 1: pid 24450 tid 24452  &shared 0x5617f2382068  &mine 0x7f77439fe6bc  &local 0x7f77439fde94  mine = 1000
thread 2: pid 24450 tid 24453  &shared 0x5617f2382068  &mine 0x7f77431fd6bc  &local 0x7f77431fce94  mine = 1000
main    : pid 24450 tid 24450  shared = 3000, main's own mine = 0
```

Mind a négy ugyanazt a PID-et, de különböző TID-et jelent; a fő szál TID-je megegyezik a PID-del. A `shared` változónak egyetlen címe van, és elérte a 3000-et. A `mine` minden szálban más címen van, minden példány 1000-ig számolt, a fő szál példánya pedig még mindig 0. A vermek (és velük a TLS-blokkok, amelyeket a glibc minden szál vermének tetejére tesz) egymástól `0x801000` bájtra vannak: 8 MiB verem plusz egy 4 KiB-os védőlap. Maga a szál létrehozása:

```console
$ strace -f -qq -e trace=clone3 ./threads 2>&1 > /dev/null | head -1
clone3({flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID, child_tid=0x7f8da69ff990, parent_tid=0x7f8da69ff990, exit_signal=0, stack=0x7f8da61ff000, stack_size=0x7fff80, tls=0x7f8da69ff6c0} => {parent_tid=[5496]}, 88) = 5496
```

Vessük össze a `fork()` fenti `clone()` hívásával: a szál osztozik a címtartományon, a fájlrendszer-információkon, a leírótáblán és a szignálkezelőkön, belép a szálcsoportba, saját vermet (a `stack_size` alig kevesebb 8 MiB-nál) és TLS-blokkot kap, és befejeződésekor nem küld szignált (`exit_signal=0`). Kívülről a `tasks.sh` egy négyszálú Python-folyamatot vizsgál:

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

A `ps` a szálakat „light-weight process”-nek (könnyűsúlyú folyamatnak) nevezi (az `LWP` a TID, az `NLWP` a szálak száma; az `Sl`-ben az `l` azt jelenti, hogy többszálú). A kernelen belül minden task `Pid` mezője a TID-je, a `Tgid` pedig az, amit a felhasználói tér PID-nek hív.

### Folyamatok és szálak létrehozása: mibe kerül

A `spawncost.c` létrehozásonként méri: egy szál (`pthread_create` és `pthread_join`), egy azonnal kilépő folyamat (`fork` vagy `vfork`, `_exit`, `waitpid`), és egy `/bin/true`-t futtató folyamat (`fork` és `exec`, `vfork` és `exec`, vagy `posix_spawn`) költségét. Argumentummal először ennyi MiB-ot foglal le és érint meg, hogy nagy legyen a szülő:

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

Kis szülőnél egy szál nagyjából 37 µs-ba kerül, egy folyamat ennek körülbelül 3,6-szeresébe (132 µs). Egy új program futtatása körülbelül 1 ms, akárhogyan indítjuk: az `execve`, a C könyvtárat leképező dinamikus betöltő és a `/bin/true` indulása dominál. Ha a szülőben 1 GiB memória van, minden, ami a címtartományt másolja, drágává válik: a `fork` most 20 ms, 150-szer annyi, mert a kernelnek 262 144 lap laptábla-bejegyzéseit kell lemásolnia, írásvédetté tennie a copy-on-write miatt, majd a gyerek kilépésekor ismét lebontania, laponként nagyjából 76 ns alatt. A `vfork` és a `posix_spawn` semmit sem másol, és a régi költségén marad; a szálat sem érinti. Ez a mérés áll a `fork` kritikája mögött (Baumann et al., 2019, a saját gépükön a szülő méretétől függetlenül körülbelül 0,5 ms-ot mértek a `posix_spawn`-ra). A glibc `posix_spawn`-ja `vfork` stílusú `clone3()`-at használ:

```console
$ gcc -O2 -o spawn1 spawn1.c
$ strace -f -qq -e signal=none -e trace=clone3,execve ./spawn1
execve("./spawn1", ["./spawn1"], 0x7ffee709a4c0 /* 200 vars */) = 0
clone3({flags=CLONE_VM|CLONE_VFORK|CLONE_CLEAR_SIGHAND, exit_signal=SIGCHLD, stack=0x7f38f1882000, stack_size=0x9000}, 88 <unfinished ...>
[pid  5469] execve("/bin/true", ["true"], 0x7ffc249a95a8 /* 200 vars */ <unfinished ...>
[pid  5468] <... clone3 resumed>)       = 5469
[pid  5469] <... execve resumed>)       = 0
```

A gyerek osztozik a szülő memóriáján (`CLONE_VM`), de saját, 36 KiB-os vermen fut, minden szignálkezelő visszaállításával (`CLONE_CLEAR_SIGHAND`), hogy a szülő egyik kezelője se futhasson a kölcsönvett címtartományban. A `CLONE_VFORK` felfüggeszti a szülőt: a `clone3` hívása csak akkor tér vissza, amikor a gyerek `execve`-je a kölcsönvett címtartományt már egy újra cserélte.

### Egy szignál megszakít egy rendszerhívást

A `sigdemo.c` egy üres pipe-on blokkol a `read()`-ben. Egy gyerek 2 másodperc múlva ír a pipe-ba, egy riasztási szignál azonban már 1 másodperc múlva megérkezik. A kezelő csak beállít egy jelzőt, és meghívja a `write()`-ot, mindkettő async-signal-safe:

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

A szignál mindkét esetben felébresztette a folyamatot a megszakítható alvásából, és a kezelő a `read()` közepén futott le. `SA_RESTART` nélkül a `read()` ezután 1 másodperc után `EINTR` hibával tért vissza, és egy gondos programnak újra meg kellene hívnia; `SA_RESTART` mellett a kernel a kezelő után újraindította, és a hívás visszaadta a 4 bájtot, amikor azok 2 másodperc múlva megérkeztek.

### IPC: késleltetés és áteresztőképesség

Az `ipcbench.c` egy pipe-ot, egy Unix domain socketet (`socketpair`), egy POSIX üzenetsort és POSIX osztott memóriát hasonlít össze egy szülő és egy gyerek között. *Késleltetés*: 100 000 oda-vissza út egy bájttal; osztott memóriánál a két oldal vagy folyamatok között megosztott, alvó szemaforokkal, vagy egy atomi jelzőn pörögve (spinning) vár egymásra. *Áteresztőképesség*: 1 GiB 64 KiB-os darabokban, amelyeket a fogadó a saját pufferébe másol (az üzenetsornál 8 KiB-os darabokban, ez az alapértelmezett maximális üzenetméret; osztott memóriánál négy 64 KiB-os rekeszből álló gyűrűvel és szemaforokkal). Az argumentum mindkét folyamatot ugyanarra a processzorra, vagy két különbözőre rögzíti:

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

**Késleltetés.** Egy processzoron egy oda-vissza út nagyjából 3 µs bármelyik alvó mechanizmussal (a sockettel 6 µs, mert hosszabb a kódútja): mindkét irányban egy `write`, egy `read` és egy környezetváltás a másik folyamatra, vagyis oda-vissza utanként két váltás (a [következő előadás](../07-concurrency-deadlocks-scheduling/#egy-környezetváltás-ára) ugyanezen a gépen váltásonként 1,4–1,7 µs-ot mér, a két rendszerhívással együtt). Két processzoron ugyanez az oda-vissza út 26–33 µs, tízszer annyi, és a mechanizmus alig számít. Az idő egy másik processzoron lévő folyamat felébresztésére megy el: a felébresztőnek processzorok közötti megszakítást kell küldenie, és ezen a virtuális gépen a tétlen virtuális processzor leállt, így a hypervisornak először újra ütemeznie kell, ami sokkal lassabb, mint valódi hardveren. A pörgés (spinning) teljesen elkerüli az alvást: 0,2 µs oda-vissza utanként, ennyi idő kell egy gyorsítótár-sornak, hogy két mag között oda-vissza utazzon, de annak az árán, hogy várakozás közben mindkét processzor 100%-ban foglalt. Az alacsony késleltetésű rendszerek (tőzsdei kereskedés, csomagfeldolgozás) pontosan ezt teszik, dedikált magokon.

**Áteresztőképesség.** Az osztott memória az egyértelmű győztes 13–14 GB/s-mal, pedig a teszt kétszer másolja az adatokat a felhasználói térben, mert a legtöbb rekeszátadáshoz egyáltalán nem kell rendszerhívás (a szemafor csak akkor lép be a kernelbe, ha aludnia kell, vagy fel kell ébresztenie valakit). Minden más mechanizmus darabonként két rendszerhívást és két, a kernelen át vezető másolást végez, és alszik, illetve felébreszti a másik oldalt, valahányszor a kernelpuffer megtelik vagy kiürül. Ezért számít a pufferméret: az alapértelmezett pipe csak 64 KiB-ot tárol, pontosan egy darabot, így a két oldal felváltva dolgozik; 1 MiB-os pipe-pal vagy Unix sockettel (amelynek alapértelmezett küldőpuffere itt 208 KiB) több adat van úton, és kevesebb ébresztés kell. Az üzenetsort a 8 KiB-os üzenetei korlátozzák: nyolcszor annyi rendszerhívás. A bemutatott futásban minden mechanizmus gyorsabb volt egy processzoron, ahol az adatok az adott mag gyorsítótáraiban maradnak, és egyetlen ébresztés sem lépi át a processzorok határát; ez tendencia, nem szabály. Az eredmények futásról futásra akár kétszeres eltérést is mutatnak, attól függően, hová helyezi éppen az ütemező a folyamatokat.

### Egy folyamat a /proc-on keresztül

A `procfs.sh` elindít egy `sleep 100`-at, amelynek a bemenete a `/dev/null`, a kimenete és a hibakimenete egy fájlba van átirányítva, és kiolvassa a `/proc` könyvtárát:

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

Az első ábrán látható kernelnyilvántartás minden része megjelenik fájlként: az azonosítók és az állapot (`S`, alszik, egy önkéntes környezetváltás után), a jogosultsági adatok (valós, effektív, mentett és fájlrendszer-UID, rootként mind 0), a használt memória (1,7 MiB rezidens), a leírótábla a shell által végzett átirányításokkal, a program, az aktuális könyvtár és az argumentumok, az a kernelfüggvény, amelyben a folyamat alszik (egy nagy felbontású időzítő), és az erőforráskorlátok.

### Nyomkövetés strace-szel

Az `strace -c` egy teljes program rendszerhívásainak profilját adja. A `find` egy könyvtárfát jár be:

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

A `find` megnyit minden könyvtárat (6779 `openat` hívás), kötegekben olvassa be a bejegyzéseiket a `getdents64` hívással (könyvtáranként nagyjából két hívás: az egyik bejegyzéseket ad vissza, a másik semmit), és a `newfstatat` hívással vizsgálja a bejegyzéseket; a sok `fcntl` és `close` hívás abból adódik, ahogyan a könyvtárleírókat kezeli. A `-T` megmutatja az egyes hívásokban töltött időt:

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

Maga a `cat` ezek közül csak hét hívást végez: megnyitás, a 3 bájt beolvasása, kiírásuk, újabb olvasás a fájl végének észlelésére, bezárás. Az első öt a dinamikus betöltőé, amely az `/etc/ld.so.cache` gyorsítótárfájlon keresztül megtalálja a C könyvtárat, és beolvassa az ELF-fejlécét. (Nyomkövetés alatt minden hívás 20–50 µs-nak tűnik; ennek nagy része maga a nyomkövetés.) Még egy apró program is sok hívást végez a `main` előtt:

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

A 42 sorból (41 rendszerhívás és a kilépési sor) a program saját kérései a hat `write` hívás, az a néhány hívás, amellyel a `printf` beállította a pufferét (`fstat` és `ioctl` annak kiderítésére, hogy a kimenet nem terminál; `getrandom` és `brk`, amikor a `malloc` először előkészítette a heapet a puffer memóriájához), valamint a záró `exit_group`. A többi az `execve`, a C könyvtárat `mmap`-pel leképező és `mprotect`-tel védő betöltő, valamint a C könyvtár, amely beállítja a TLS-t (`arch_prctl`), a szálazonosító címét és a többi szálankénti adatát.

### Hol várakozik egy folyamat?

A `waiting.sh` elindít egy `sleep 30`-at, és megkérdezi, hol várakozik: először a `/proc`-on keresztül, majd a `gdb`-vel, majd ismét a `/proc`-on keresztül:

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

A kernel nézete: a folyamat a `hrtimer_nanosleep` kernelfüggvényben alszik, a 230-as rendszerhíváson (`clock_nanosleep`) belül. A `gdb` felhasználói térbeli nézete: a C könyvtár `nanosleep` wrappere, amelyet a `sleep` `main` függvénye hívott (`??`-ként jelenik meg, mert a telepített `sleep`-nek nincs szimbólumtáblája), azt pedig a C könyvtár indítókódja. Utána a folyamat a 219-es rendszerhívásban, a `restart_syscall`-ban várakozik: a debugger csatlakozása egy szignálhoz hasonlóan megszakította az alvást, a kernel pedig egy speciális rendszerhívással folytatta, amely csak a *hátralévő* ideig alszik. A folyamat megfigyelése megváltoztatta a folyamatot, és ezt érdemes észben tartani, valahányszor nyomkövetőt vagy debuggert csatlakoztatunk egy éles folyamathoz.

### perf és bpftrace

A `perf` és a `bpftrace` nincs telepítve ezen a gépen, ezért kimenet nem szerepel; a [9. laborfeladat](#laborfeladatok) olyan gépen használja őket, ahol elérhetők. Tipikus használat:

```console
$ perf stat -e task-clock,context-switches,cpu-migrations,page-faults ./spawncost 256
$ perf record -g ./ipcbench split; perf report
$ perf trace -s ./minish < minish-demo.txt
# bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'
# bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf("%d %s -> %s\n", pid, comm, str(args->filename)); }'
# bpftrace -e 'tracepoint:sched:sched_process_fork { printf("%s (%d) forked %d\n", args->parent_comm, args->parent_pid, args->child_pid); }'
```

Az első a költségmérés eseményeit számolja; a második rögzíti, hol tölti az idejét az `ipcbench`, a felhasználói kódban és a kernelben; a harmadik a `perf` gyorsabb megfelelője az `strace -c`-nek. A `bpftrace` sorok (rootként futtatva; a `#` a root promptja) a Ctrl-C lenyomásáig programnevenként megszámolják a rendszerhívásokat az egész rendszeren, kiírnak minden, a rendszeren bárhol elindított programot (mint az `execsnoop` eszköz), illetve minden forkot.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> ASLR, C hívási konvenció, cancellation, ECHILD, LWP, védőlap, környezetváltás, processzorok közötti megszakítás, pörgés, profil, wchan, szimbólumtábla</summary>

- **ASLR** (address space layout randomisation, a címtartomány elrendezésének véletlenszerűsítése): a program részeinek minden indításkor véletlenszerű címekre helyezése, hogy nehezebb legyen a támadás.
- **C hívási konvenció:** az a megállapodás, ahogyan egy függvény megkapja az argumentumait, itt az `rdi`, `rsi`, `rdx` stb. regiszterekben.
- **Cancellation** (szál megszakítása): mód arra, hogy egy szál megkérjen egy másikat a leállásra; egyes rendszerhívások olyan pontok, ahol ezt a kérést ellenőrzik.
- **ECHILD:** a „nincs gyereked, amelyre várhatnál” hiba.
- **LWP** (light-weight process, könnyűsúlyú folyamat): a kernelszintű szál régi neve; a `ps`-ben a szál azonosítója.
- **Védőlap** (guard page): leképezetlen lap minden szálverem alatt, hogy a túlságosan megnőtt verem hibát okozzon, ne pedig csendben felülírjon más memóriát.
- **Környezetváltás:** a processzor abbahagyja az egyik folyamat vagy szál futtatását, és egy másikat kezd futtatni, miután elmentette az első regisztereit, hogy az később folytathassa.
- **Processzorok közötti megszakítás** (inter-processor interrupt): megszakítás, amelyet az egyik processzormag küld egy másiknak, például: „ébredj, munka van”.
- **Pörgés** (spinning): várakozás úgy, hogy egy ciklusban újra és újra megnézünk egy értéket, elalvás nélkül.
- **Profil:** összefoglaló arról, hol tölti az idejét egy program, vagy milyen gyakran csinál valamit.
- **wchan** („wait channel”, várakozási csatorna): az a kernelfüggvény, amelyben egy alvó folyamat várakozik.
- **Szimbólumtábla:** a programfájlban tárolt függvénynevek listája; nélküle a debugger csak címeket mutat (`??`).

</details>

## Laborfeladatok

1. **Címtartomány.** Futtasd többször a `layout` programot, majd egyszer kikapcsolt címvéletlenítéssel (`setarch -R ./layout`): mely címek maradnak ugyanazok? Változtasd a nagy `malloc` méretét 64 KiB-ra, 127 KiB-ra, 128 KiB-ra és 256 KiB-ra: hol vált a heapről külön leképezésre? Adj hozzá egy `static int` változót a `main`-en belül, egy sztringliterált és egy `const` globális változót, és keresd meg a régióikat. Miért nincs a sztringliterál a data régióban?
2. **Rendszerhívások kézzel.** Egészítsd ki a `hello3.c`-t egy `raw_getpid()` függvénnyel (39-es szám, argumentumok nélkül), és a programot `return` helyett egy puszta `exit_group(7)` hívással (231-es szám) fejezd be. Ellenőrizd az `echo $?` paranccsal és az `strace`-szel. Ezután futtasd az `strace -c` parancsot az `ls -l /usr/bin > /dev/null` és a `python3 -c pass` parancsra: hány rendszerhívást végez mindkettő, melyik a három leggyakoribb, és melyek történnek a `main` előtt?
3. **Egy rendszerhívás ára.** Futtasd ötször a `sccost` programot, és egyszer `taskset -c 0` alatt. Add hozzá a programhoz a `getppid()` és a `sched_yield()` hívást. Laptopon vagy fizikai Linux gépen hasonlítsd össze az eredményeket az előadás eredményeivel; aztán nézd meg mindkét gépen a `/sys/devices/system/cpu/vulnerabilities/` könyvtárat. Mely védekezések (mitigációk) magyarázhatnak egy eltérést?
4. **A minish bővítése.** Valósítsd meg (a) a `2>` átirányítást, (b) a háttérparancsokat `&`-del: ne várj rájuk, de minden prompt előtt gyűjtsd be a befejeződötteket a `waitpid(-1, &st, WNOHANG)` hívással, és (c) a Ctrl-C kezelését: a shell figyelmen kívül hagyja a `SIGINT`-et, a gyerekek az `exec` előtt visszaállítják az alapértelmezett műveletet. Indíts egy `sleep 5 &` parancsot, és a `ps -o pid,stat,cmd` paranccsal ellenőrizd, hogy a befejeződése után nem marad zombi. Mit látsz a (b) lépés begyűjtése nélkül?
5. **A fork ára.** Futtasd a `spawncost` programot 0, 256, 512, 1024 és 2048 MiB-tal, és ábrázold a `fork` idejét a méret függvényében. Lineáris? Számítsd ki a laponkénti költséget. Ezután a `malloc` után add hozzá a `madvise(p, size, MADV_HUGEPAGE)` hívást (sok rendszeren a transparent huge page-ek `madvise` módban vannak), és ismételd meg. Mi változik, és miért?
6. **Szálak.** (a) Vedd ki a mutexet a `threads.c`-ből, növeld a ciklusszámot tízmillióra, és futtasd többször: mi történik a `shared` változóval, és miért nem a `mine`-nal? (b) Írasd ki az `&errno` értékét minden szálban. (c) A 0. szál hívja meg a `fork()`-ot, a gyerek pedig írja ki a `/proc/self/task` bejegyzéseinek számát: hány szála van a gyereknek? Mi történne, ha a fork pillanatában egy másik szál egy mutexet tartana?
7. **IPC.** Futtasd többször az `ipcbench` programot argumentum nélkül, valamint `same` és `split` argumentummal. Ezután adj hozzá két változatot: egy `mkfifo()`-val létrehozott FIFO-t (nyisd meg mindkét folyamatban), és egy „zero-copy” osztottmemória-változatot, amelyben a termelő közvetlenül a rekeszbe ír (`memset`), a fogyasztó pedig gyorsítótár-soronként csak egy bájtot olvas. Magyarázd meg a különbségeket. Miért kell a pörgő változatnak két processzor?
8. **Szignálok.** Írj egy programot, amely egy szignálkezelőben számolja a `SIGUSR1` szignálokat, és közben alszik, és egy másik programból (`kill()` egy ciklusban) küldj neki a lehető leggyorsabban 10 000 szignált. Hány érkezik meg? Ismételd meg a `sigaction`-nel telepített `SIGRTMIN` valós idejű szignállal. Magyarázd meg a különbséget. Ezután telepíts egy `printf`-et hívó kezelőt, és küldj szignálokat, miközben a főciklus is `printf`-et hív: el tudod érni, hogy hibásan viselkedjen?
9. **Megfigyelés ltrace-szel, perf-fel és bpftrace-szel** (olyan Linux gépen, ahol root vagy, és telepíthetsz csomagokat, pl. `sudo apt install ltrace linux-tools-common linux-tools-$(uname -r) bpftrace`; kimenetek itt nem szerepelnek, mert az előadás gépén nincsenek meg ezek az eszközök). Futtasd az `ltrace -c ./hello3` és az `ltrace -e malloc+free ./layout` parancsot: milyen könyvtári hívások jelennek meg, és miért jelenik meg itt a `write` és a `printf` is, holott az `strace` csak a `write`-ot mutatja? Futtasd a [perf és bpftrace bemutató](#perf-és-bpftrace) `perf` és `bpftrace` parancsait. Amíg az `execve`-s egysoros fut, nyiss egy új terminált: milyen programokat indít el a shelled az első prompt előtt? Hasonlítsd össze az `strace -c` és a `perf trace -s` többletterhelését a `./sccost 100000` parancson.

## Ellenőrző kérdések

1. Mi a különbség a program és a folyamat között? Adj példát arra, amikor egy program több folyamatként fut, és arra, amikor egy folyamat egymás után több programot futtat.
2. Nevezd meg egy folyamat címtartományának régióit, és mondd meg, mit tartalmaz mindegyik. Miért nem foglal helyet a BSS a futtatható fájlban? A `layout` bemutatóban miért a heapből jött a 100 bájtos blokk, és miért saját leképezésből az 1 MiB-os?
3. Mit tart nyilván a kernel egy folyamatról a címtartományán kívül? Miért kell ennek a nyilvántartásnak a kernel memóriájában lennie?
4. Magyarázd el a különbséget az API és a rendszerhívás-interfész között. Adj példát olyan könyvtári függvényre, amely nem hajt végre rendszerhívást, olyanra, amely egyet hajt végre, és olyanra, amely néha egyet, néha egyet sem.
5. Írd le lépésről lépésre, mi történik x86-64-es Linuxon, amikor egy program meghívja a `write(1, buf, 3)` függvényt: regiszterek, utasítás, belépés a kernelbe, a hívás továbbítása, visszatérés, és hogyan jut el egy hiba az `errno`-ig.
6. Egy függvényhívás nagyjából 2 ns-ba, a `getpid()` nagyjából 125 ns-ba került. Honnan ered a különbség? Mi a vDSO, miért volt rajta keresztül ötször olcsóbb a `clock_gettime()`, és miért nem használhatja a `write()`?
7. `strace` alatt a `getpid()` nagyjából 8,5 µs-ig tartott. Miért? Mit jelent ez az `strace`-szel végzett teljesítménymérésekre nézve?
8. A `fork()` „kétszer tér vissza”. Magyarázd el. Egy program kiír egy sort `printf`-fel (a végén sorvége nélkül), majd meghívja a `fork()`-ot, és a kimenete egy fájlba megy. Mi jelenik meg a fájlban, és hogyan kerülhető el?
9. Mit őriz meg egy folyamat az `execve()` során, és mi cserélődik le? Miért külön hívás a Unixban a `fork` és az `exec`, és mi ennek a tervezésnek a fő kritikája?
10. Mi történik azzal a gyerekkel, amelynek a szülője előbb fejeződik be? Az `orphan` bemutatóban miért adott vissza −1-et a `waitpid(-1)` az első futásban, és miért a gyerek PID-jét a másodikban? Kik használnak subreapereket, és miért?
11. Sorold fel, milyen rendszerhívásokat végez a `minish` a szülőben és a gyerekben a `sort <in.txt >out.txt` parancsra. Miért kell a `cd`-nek beépített parancsnak lennie?
12. Az `ls /etc | grep ^host` pipeline-ban mi romlik el, ha a shell elfelejti bezárni a pipe író végének saját másolatát? És ha az első gyerek felejti el bezárni az olvasó véget?
13. 1 GiB-os szülővel az `exec`-kel kombinált `fork` 21 ms-ig tartott, az `exec`-kel kombinált `vfork` és a `posix_spawn` viszont nagyjából 1 ms-ig. Magyarázd meg a különbséget. Miért veszélyes a `vfork`, és hogyan kerüli el a veszélyt a `posix_spawn`?
14. Min osztoznak egy folyamat szálai, és mi az egyes szálak sajátja? Miért kell az `errno`-nak szálankéntinek lennie? Mit mutatott a `threads` bemutató a `__thread` változókról?
15. Hasonlítsd össze az N:1, az 1:1 és az M:N szálmodellt: mi történik, ha egy szál blokkol egy rendszerhívásban, és használhatnak-e a szálak több magot? Melyik modellt használják a Linux pthreads szálai, és hogyan futtat a Go és a Java 21 több százezer párhuzamos taskot?
16. Mely `clone()` flagek teszik az új taskot szállá folyamat helyett? Mi a szálcsoport, és mit ad vissza a `getpid()` és a `gettid()` a fő szálban és egy másik szálban?
17. Miért nem hívhat egy szignálkezelő `printf`-et vagy `malloc`-ot? Mit tegyen helyette a kezelő? A `sigdemo`-ban mi volt a különbség az `SA_RESTART`-tal és az anélkül végzett futás között?
18. Hasonlítsd össze a pipe-ot, a Unix domain socketet, az üzenetsort és az osztott memóriát: irány, üzenethatárok, nem rokon folyamatok általi használat, a másolások száma, és ki szinkronizál. A mérésben miért ugrott meg minden alvó mechanizmus késleltetése nagyjából 3 µs-ról nagyjából 30 µs-ra, amikor a folyamatok különböző processzorokon voltak, és miért az osztott memória volt a leggyorsabb áteresztőképességben?
19. Melyik eszközt használnád annak kiderítésére, (a) hogy egy program mely konfigurációs fájlokat próbál megnyitni, (b) hogy egy forgalmas éles szerver mire tölti a processzoridejét, (c) hogy egy szerveren melyik folyamat indít percenként több ezer rövid életű programot? Miért rossz választás az `strace` a (b) és a (c) esetre?

<details>
<summary><strong>Megoldókulcs (oktatóknak)</strong></summary>

1. A program kódból és adatokból álló passzív fájl; a folyamat végrehajtás alatt álló program saját címtartománnyal, regiszterekkel, megnyitott fájlokkal és kernelbeli nyilvántartással. Több folyamat: tíz felhasználó futtatja a `bash`-t, vagy egy webszerver munkafolyamatai. Több program egy folyamatban: a shell gyereke a shell másolataként indul, majd `exec`-kel lefuttatja az `ls`-t; az `exec` megtartja a PID-et.
2. Text (gépi kód, csak olvasható és végrehajtható), data (inicializált globális változók), BSS (nullára inicializált globális változók), heap (`malloc`, a `brk`-kal felfelé nő), memórialeképezett terület (megosztott könyvtárak, leképezett fájlok, nagy `malloc`-blokkok, szálvermek, vDSO), verem (lokális változók, visszatérési címek, lefelé nő), és a védett kernelfél. A BSS csupa nulla, ezért a fájl csak a méretét tárolja; a kernel nullákkal feltöltött lapokat ad. A glibc a kis kéréseket a heapből szolgálja ki, az `mmap` küszöbe (alapértelmezés szerint 128 KiB) fölöttieket pedig külön névtelen leképezéssel, amely felszabadításkor egészében visszaadható a kernelnek.
3. A PID és a szülő, az állapot és az ütemezési adatok, a mentett regiszterek, a memóriatérkép és a laptáblák, a leírótábla, a jogosultsági adatok, a szignálkezelők és -maszkok, az aktuális és a gyökérkönyvtár, a korlátok, a namespace-ek, az elszámolási adatok és egy kernelverem. Ha a folyamat módosíthatná, megnövelhetné a saját jogosultságait (credentials), kijátszhatná a memóriakorlátait (laptáblák), vagy kisajátíthatná a processzort (ütemezési adatok); a kernel csak abban bízhat meg, amit a folyamat nem írhat.
4. Az API a programozók által hívott könyvtári függvények halmaza (C könyvtár, POSIX); a rendszerhívás-interfész a kernel számozott belépési pontjainak halmaza. Rendszerhívás nélkül: `strlen`, `memcpy`. Egy rendszerhívással: `write()`, `getpid()`. Néha: `printf` (csak a puffer ürítésekor), `malloc` (csak ha a készletének növekednie kell), `clock_gettime` (a vDSO-n keresztül rendesen egy sem).
5. Az argumentumok az `rdi` (1), `rsi` (buf), `rdx` (3) regiszterben vannak; a wrapper az 1-et az `rax`-be tölti, és végrehajtja a `syscall` utasítást, amely a visszatérési címet az `rcx`-be, a jelzőbiteket az `r11`-be menti, kernelmódba vált, és az MSR-ben tárolt belépési pontra ugrik. Az `entry_SYSCALL_64` átvált a kernelveremre, elmenti a regisztereket, és meghívja a `sys_call_table[1]` bejegyzést, a write megvalósítását, amely a VFS-en keresztül eljut a terminálhoz, a pipe-hoz vagy a fájlhoz. Az eredmény (a kiírt bájtok száma vagy −errno) az `rax`-ba kerül; a `sysret` visszatér felhasználói módba. A wrapper ellenőrzi, hogy az `rax` a −4095…−1 tartományban van-e; ha igen, a −rax értéket az `errno`-ba írja, és −1-et ad vissza.
6. A rendszerhíváshoz kell a módváltás, a regiszterek mentése és visszaállítása, a veremváltás, a belépési ellenőrzések és a spekulatív végrehajtás elleni védekezések; egy függvényhívás csak egy ugrás és egy visszatérés. A vDSO olyan kód, amelyet a kernel minden folyamatba leképez, egy általa frissített adatlappal együtt; a `clock_gettime` ebből a lapból és az időbélyeg-számlálóból számítja ki az időt, a kernelbe való belépés nélkül. A `write()` a folyamaton kívüli állapotot (egy fájlt, egy pipe-ot) változtat meg, és jogosultság-ellenőrzés és eszköz-hozzáférés kell hozzá, amit csak a kernel végezhet.
7. Az `strace` a `ptrace`-t használja: minden rendszerhívásba való belépéskor és kilépéskor a kernel megállítja a folyamatot, felébreszti a nyomkövetőt, amely kiolvassa a regisztereket és a memóriát, kiír, majd továbbengedi a folyamatot: nyomon követett hívásonként négy környezetváltás és a nyomkövető több rendszerhívása. Az `strace` alatt végzett mérések torzak (a rendszerhívás-igényes kód sokkal lassabbnak látszik, mint amilyen); arra használjuk, hogy kiderítsük, *mit* csinál egy program, nem azt, hogy *milyen gyorsan*, időzítéshez pedig a `perf`-et vagy az eBPF-et.
8. A hívás létrehoz egy gyereket; ettől kezdve két folyamat hajtja végre ugyanazt a kódot a hívás után, és a kernel mindkettőben más visszatérési értéket állít be: a szülőben a gyerek PID-jét, a gyerekben 0-t. A fájlba menő kimenet teljesen pufferelt, így a sor a forkoláskor még a pufferben van; a puffer lemásolódik, és mindkét folyamat kiüríti kilépéskor: a sor kétszer jelenik meg. Elkerülhető a `fork()` előtti `fflush(stdout)` hívással, és azzal, hogy az `exec`-et nem hívó gyerekek `_exit()`-tel fejeződnek be.
9. Megmarad: a PID, a szülő, az `O_CLOEXEC` nélküli megnyitott leírók, az aktuális és a gyökérkönyvtár, az umask, a korlátok, a szignálmaszk és a figyelmen kívül hagyott szignálok, a jogosultsági adatok (hacsak nem setuid/setgid). Lecserélődik: a text, a data, a heap, a verem és a leképezések; a kezelt szignálok visszaállnak az alapértelmezett műveletükre. A külön hívások lehetővé teszik, hogy a gyerek a kettő között közönséges rendszerhívásokkal igazítsa a környezetét (átirányítások, leírók bezárása, könyvtár- vagy jogosultságváltás). A kritika (Baumann et al., 2019): a `fork` lemásolja az egész folyamatot (nagy folyamatoknál lassú, alapértelmezésben nem biztonságos), nem fér össze a szálakkal, és bonyolítja a kernelt; programok indításának a `posix_spawn`-nak kellene a szokásos módjának lennie.
10. Árva folyamattá válik, és az 1-es PID-hez (vagy a legközelebbi subreaper őséhez) kerül, amely a befejeződésekor begyűjti. Az első futásban az unoka az 1-es PID-hez tartozott, így a nagyszülőnek nem maradt gyereke (`ECHILD`); a másodikban a nagyszülő subreaper volt, és örökbe fogadta. A szolgáltatáskezelők (`systemd --user`) és a konténer-futtatókörnyezetek subreaperekkel tartják nyilván és gyűjtik be az összes általuk indított folyamatot, akkor is, ha a köztes folyamatok kilépnek.
11. Szülő: `clone` (fork), majd `wait4`. Gyerek: `openat("in.txt", O_RDONLY)` = 3, `dup2(3, 0)`, `close(3)`, `openat("out.txt", O_WRONLY|O_CREAT|O_TRUNC)` = 3, `dup2(3, 1)`, `close(3)`, `execve("/usr/bin/sort", …)` (a korábbi `PATH`-könyvtárakra tett sikertelen `execve`-k után). A `cd`-nek a shell saját aktuális könyvtárát kell megváltoztatnia; egy gyerek `chdir`-je csak a gyerekét változtatná meg, amely azonnal befejeződik.
12. Ha a shell nyitva tartja az író véget, a `grep` az `ls` befejeződése után sem észleli a fájl végét, mert még létezik író; a `grep` örökké vár, a shell pedig a `grep`-re vár. Ha az első gyerek tartja nyitva az olvasó véget, látható hiba nem történik, amíg a `grep` olvas; ha azonban a `grep` korán kilépne, az `ls` nem kapna `SIGPIPE`/`EPIPE` jelzést, és örökre blokkolhatna a megtelt pipe-on, mert még létezik olvasó (önmaga).
13. A `fork`-nak mind a 262 144 lap laptábláit le kell másolnia, írásvédetté kell tennie a copy-on-write miatt, és a gyerek kilépésekor le kell bontania (itt laponként körülbelül 76 ns); az `exec` aztán eldobja őket. A `vfork` és a `posix_spawn` az `exec`-ig osztozik a szülő címtartományán, így semmit sem kell másolni. A `vfork` veszélyes, mert a gyerek a szülő memóriájában fut: a változók bármilyen módosítása, vagy a függvényből való visszatérés, elrontja a szülőt. A glibc `posix_spawn`-ja a gyereket egy külön kis vermen futtatja, minden szignálkezelőt visszaállít, és az `exec` előtt csak a saját, ellenőrzött kódját hajtja végre.
14. Közös: a kód, a globális változók, a heap, a memóriatérkép, a megnyitott fájlok, a szignálkezelők, a PID és a jogosultsági adatok, az aktuális könyvtár, a korlátok. Saját: a TID, a regiszterek (PC, SP, jelzőbitek), a verem, a TLS, a szignálmaszk, az ütemezési állapot. Az `errno`-t az egyik szál sikertelen hívása állítja be, és közvetlenül utána olvassák ki; egy közös `errno`-t egy másik szál közben felülírhatna. A bemutató a `shared` változónak egyetlen címet mutatott, a `mine` címe viszont minden szálban más volt, mindegyik egymástól függetlenül 1000-ig számolt, a fő szál példánya pedig még mindig 0 volt.
15. N:1: egy blokkoló hívás minden szálat blokkol; csak egy mag használható; a váltás nagyon olcsó. 1:1: csak a hívó szál blokkol; a szálak párhuzamosan futnak; a létrehozás és a váltás a kernelen keresztül történik. M:N: a blokkolást a futtatókörnyezet kezeli, amely más felhasználói szálakat futtat más kernelszálakon; párhuzamos; olcsó szálak, bonyolult futtatókörnyezet. A Linux NPTL 1:1 modellű. A Go a goroutine-okat (kis, növekedni képes vermekkel) néhány OS-szálra multiplexeli; a Java 21 virtuális szálai carrier szálakra kerülnek, és blokkoláskor lekerülnek róluk. Mindkettő nyelvi szintű M:N, ahol a blokkoló műveleteket a futtatókörnyezet ellenőrzi.
16. `CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, `CLONE_SIGHAND` és `CLONE_THREAD` (valamint `CLONE_SYSVSEM` és `CLONE_SETTLS`, és egy külön verem). A szálcsoport egy folyamat taskjainak halmaza; azonosítója (TGID) az első szál TID-je. A fő szálban `getpid()` = `gettid()` = TGID; egy másik szálban a `getpid()` a TGID-et, a `gettid()` a saját TID-jét adja vissza (a bemutatóban 24450 és 24451).
17. A kezelő a `printf`-et vagy a `malloc`-ot a belső állapotuk módosításának közepén, vagy egy zár birtoklása közben is megszakíthatja; ha újra meghívja őket, elronthatja az állapotot, vagy holtpontba juthat. A kezelő csak állítson be egy `volatile sig_atomic_t` jelzőt (vagy írjon egy bájtot egy pipe-ba), és térjen vissza, a munkát pedig hagyja a főprogramra. `SA_RESTART` nélkül a `read()` 1 s után `EINTR` hibával tért vissza; vele a kernel a kezelő után újraindította a hívást, és az 2 s után visszaadta az adatokat.
18. Pipe: egyirányú folyam, rokon folyamatok, 2 másolás, a kernel szinkronizál. Unix socket: kétirányú folyam vagy datagramok, nem rokon folyamatok útvonal alapján, 2 másolás, a kernel szinkronizál, leírókat és jogosultsági adatokat is átadhat. Üzenetsor: üzenetek prioritásokkal, nem rokon folyamatok név alapján, 2 másolás, a kernel szinkronizál. Osztott memória: nincs szerkezete, nem rokon folyamatok név alapján, 0 másolás, a folyamatok szinkronizálnak. Két processzoron minden oda-vissza út két, processzorok közötti ébresztést tartalmaz (egy processzorok közötti megszakítást, és ezen a virtuális gépen egy leállt virtuális processzor újraütemezését a hypervisor által), ezek uralják a költséget, bármilyen mechanizmusról legyen is szó; egy processzoron csak közönséges környezetváltások kellenek. Az osztott memória elkerülte a rendszerhívásokat és a kernelen át vezető másolásokat, és csak időnként volt szükség szemaforos ébresztésre, így elérte a 13–14 GB/s-ot.
19. (a) `strace -e trace=openat,open,stat ./program` (vagy `-f` a gyerekekhez). (b) `perf record -g` (mintavételezés) vagy egy bpftrace/eBPF profilozó. (c) Egy bpftrace egysoros a `syscalls:sys_enter_execve` vagy a `sched:sched_process_fork`/`exec` tracepointra, vagy az `execsnoop`. Az `strace` minden rendszerhívásnál megállítja a nyomon követett folyamatot (olcsó hívásoknál nagyjából 70-szeres lassulást mértünk), ami megbénítana egy forgalmas szervert, és csak azokat a folyamatokat tudja követni, amelyekhez csatlakozott, nem az egész rendszert.

**Válaszok a laborfeladatokhoz.** 1. labor: `setarch -R` mellett minden cím ismétlődik a futások között; ezen a glibc-n a 128 KiB-os és nagyobb kérések (az alapértelmezett `M_MMAP_THRESHOLD`) saját leképezést kapnak (a küszöb nagy blokkok felszabadítása után felfelé is alkalmazkodik); a sztringliterálok és a `const` globális változók a csak olvasható adatszakaszban (`.rodata`) vannak, amely a text mellé csak olvashatóan van leképezve, nem az írható data régióban; egy `static` lokális változó a data-ban vagy a BSS-ben van. 2. labor: a `$?` értéke 7; a `python3 -c pass` több száz rendszerhívást végez, többnyire `newfstatat`, `openat`, `read` és `mmap` hívást, miközben importálja az indulási moduljait; a betöltő hívásai (az `ld.so.cache` és a `libc.so.6` `openat`-je, `mmap`, `mprotect`) a `main` előtt történnek. 3. labor: a `getppid` ugyanannyiba kerül, mint a `getpid`; a `sched_yield` többe, mert belép az ütemezőbe; hypervisor nélküli fizikai gépen a költség gyakran kisebb, az olyan védekezések pedig, mint a laptábla-izoláció (a Meltdown által érintett processzorokon) vagy a retpoline-ok, növelik. 4. labor: begyűjtés nélkül minden befejeződött háttérfeladat `Z` állapotban marad, amíg a shell ki nem lép; a shellnek figyelmen kívül kell hagynia a `SIGINT`-et, hogy a Ctrl-C csak az előtérben futó gyereket fejezze be. 5. labor: nagyjából lineáris, ezen a gépen 4 KiB-os laponként körülbelül 70–80 ns; huge page-ekkel a laptábláknak 2 MiB-onként van egy bejegyzésük, 512-szer kevesebb, így a `fork` sokkal gyorsabb lesz (ha a kernel ténylegesen tudott huge page-eket foglalni). 6. labor: (a) a `shared` a vártnál kisebb értékkel végez (elveszett frissítések, a következő előadás kritikusszakasz-problémájának versenyhelyzete); a `mine` szálankénti, így nincs min versenyezni; (b) minden szál más címet ír ki; (c) a gyereknek pontosan egy szála van, az, amelyik a `fork`-ot hívta; egy másik szál által tartott mutex a gyerekben örökre zárva maradna, ezért a gyerek az `exec`-ig csak async-signal-safe függvényeket hívhat. 7. labor: a FIFO úgy viselkedik, mint a pipe; a zero-copy változat még gyorsabb, mert mindkét másolást megspórolja; egy processzoron a pörgés teljes időszeleteket pazarol el, mert a másik oldal csak azután futhat, hogy a pörgő folyamatot az ütemező kiszorította. 8. labor: a szabványos szignálok nem állnak sorba, így sok `SIGUSR1` összeolvad, és jóval kevesebbet számolunk 10 000-nél; a valós idejű szignálok sorba állnak (egy korlátig, `RLIMIT_SIGPENDING`), és mind megérkezik; a kezelőben hívott `printf` összezavarhatja a kimenetet, vagy holtpontba juthat a stdio zárán, ritkán, de elég szignállal reprodukálhatóan. 9. labor: az `ltrace` a megosztott könyvtárak hívásait mutatja, így látja a `printf`-et és a `write` wrappert (amelyek könyvtári függvények), míg az `strace` csak a kernel `write`-ját látja; a shell indulásakor olyan programok futnak, mint a `lesspipe`, a `dircolors` és a `command-not-found` segédprogramjai, a disztribúció profilszkriptjeitől függően; a `perf trace` sokkal kisebb többletterhelést okoz, mint az `strace`, mert a kernel tracepointjait olvassa ahelyett, hogy megállítaná a folyamatot.

</details>

## Irodalom

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

## További olvasnivaló

Bovet, D. P., & Cesati, M. (2005). *Understanding the Linux kernel* (3rd ed.). O'Reilly.

Gregg, B. (2020). *Systems performance: Enterprise and the cloud* (2nd ed.). Addison-Wesley.

Tanenbaum, A. S., & Bos, H. (2015). *Modern operating systems* (4th ed.). Pearson.
