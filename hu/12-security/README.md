# Operációsrendszer-biztonság: támadások és védekezés

*Operációs rendszerek előadás: fenyegetésmodellek, támadási felületek és a megbízható számítási bázis (TCB); memóriabiztonsági hibák (buffer overflow a veremben és a heapen, use after free, egészszám-túlcsordulás, format string hibák) és az ellenük való védekezés (stack canary, NX, ASLR és PIE, RELRO, FORTIFY_SOURCE, control-flow integrity, sanitizerek, memóriabiztos nyelvek, a kernel megerősítése, seccomp); cache-alapú side channel támadások, a Meltdown és a Spectre, valamint az ellenük bevezetett védekezés; a rendszerindítás bizalmi lánca: Secure Boot, measured boot és a TPM; trusted execution environmentek és confidential VM-ek; CVE, CVSS és a frissítések, a védekezési eszközök Linuxon mérve*

## Tanulási célok

A [11. előadás](../11-access-control/) a szabályokat építette fel: ki mit tehet melyik objektummal, és ezt a kernelben egy referenciamonitor kényszeríti ki. A szabályok csak akkor érnek valamit, ha az őket kikényszerítő gépezet hibátlanul működik. Ez az előadás azokról a támadásokról szól, amelyek nem a szabályokon *keresztül*, hanem azokat *megkerülve* jutnak célba: egy hibáról, amelynek révén a támadó adatából a program vezérlési folyamata lesz, vagy egy rendszerindításról, amely egy manipulált kernelt indít el, mielőtt bármilyen szabály létezne. Minden támadási osztálynál először az alapötletet magyarázza el, majd azt a védekezést, amelyet a hardver, a fordítóprogram és az operációs rendszer állít az útjába, az előadás linuxos gépén mérve. Az [5. előadás](../05-interrupts/#felhasználói-mód-és-kernelmód) kernel/felhasználói határára, a [4. előadás](../04-fetch-execute-cycle/#memóriajogosultságok-egy-valódi-folyamatban) NX bitjére, valamint a [9. előadás](../09-virtual-memory/) címtartományaira és laptábláira épít. A támadásokat csak olyan mélységben írja le, amennyi a védekezés megértéséhez szükséges; működő exploitot nem tartalmaz.

Az előadás végére a hallgatók képesek lesznek:

- leírni egy fenyegetésmodellt: a támadó céljait (bizalmasság, sértetlenség, rendelkezésre állás), a támadási felületet, a megbízható számítási bázist, a jogosultság-kiterjesztést és a mélységi védelmet;
- elmagyarázni a verembeli és a heapbeli buffer overflow, a use after free, a double free, az egészszám-túlcsordulás és a format string hibák lényegét, azt, hogy a C és a C++ miért hajlamos rájuk, és hogy mekkora a részesedésük a sérülékenységek között;
- elmagyarázni, hogy a stack canary, az NX/W^X, az ASLR a PIE-vel, a RELRO, a FORTIFY_SOURCE és a hardveres control-flow integrity (Intel CET, Arm PAC és BTI) egy támadás melyik lépését töri meg, és mit nem akadályoz meg;
- leírni, hogyan szűrik ki a sanitizerek, a fuzzing és a memóriabiztos nyelvek a hibákat még a kiadás előtt, hogyan védi magát a kernel (KASLR, SMEP/SMAP, lockdown), és hogyan mondhatnak le a programok a jogaikról (seccomp);
- elmagyarázni, hogyan szivárogtatnak ki adatot a védelmi határokon át a cache időzítésén alapuló side channel támadások és a tranziens végrehajtás (Meltdown, Spectre), és hogyan mérsékli ezt a KPTI, a retpoline, az elágazásbecslő vezérlése és a mikrokód-frissítés;
- végigkövetni a rendszerindítás láncát a firmware-től az `init`-ig, és megkülönböztetni a Secure Bootot, a TPM PCR-eket használó measured bootot, a távoli attestationt és a TPM-hez kötött lemeztitkosítást;
- összehasonlítani a trusted execution environmenteket: az Arm TrustZone-t, az Intel SGX-et, az AMD SEV-SNP és az Intel TDX confidential VM-eket, valamint az Apple Secure Enclave-et;
- elmagyarázni a CVE-azonosítókat, a CVSS-pontszámokat, a koordinált nyilvánosságra hozatalt és a frissítések ütemezését;
- mindezt megvizsgálni Linuxon a `/proc/PID/maps`, a `setarch -R`, a `gcc` hardening kapcsolói, a `readelf`, a `gdb`, az AddressSanitizer, a seccomp, a `/proc/kallsyms`, a `/sys/kernel/security/lockdown`, a `/sys/devices/system/cpu/vulnerabilities` és a kernelnapló segítségével.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> biztonság, támadó, sérülékenység, exploit, fenyegetésmodell, mitigáció</summary>

- **Biztonság:** az, hogy a rendszer azt csinálja, amit a tulajdonosa akar, akkor is, ha valaki szándékosan próbálja rávenni valami másra.
- **Támadó:** az a személy (vagy program), aki be akar törni, titkokat akar megszerezni vagy kárt akar okozni.
- **Sérülékenység:** egy gyenge pont, általában egy programhiba, amelyet a támadó ki tud használni. Olyan, mint egy ablak, amely nem záródik rendesen.
- **Exploit:** az a módszer vagy program, amely kihasznál egy sérülékenységet. Az a trükk, amellyel kívülről fel lehet emelni azt az ablakot.
- **Fenyegetésmodell:** világos leírás arról, hogy ki támadhat, mire képes és mit akar, hogy tudd, mi ellen védekezel. Egy biciklit másképp zárunk le, mint egy banki páncéltermet.
- **Mitigáció (mitigation):** olyan védekezés, amely nem szünteti meg a hibát, de sokkal nehezebbé vagy lehetetlenné teszi a kihasználását.

</details>

## Fenyegetésmodellek és támadási felületek

### Mit akarnak a támadók?

A biztonsági célokat általában három tulajdonsággal fogalmazzák meg, ez a **CIA-hármas** (CIA triad):

- **Bizalmasság (confidentiality):** az információt csak az olvashatja, akinek szabad. Megsértése például egy másik felhasználó fájljainak, egy szerver titkos kulcsának vagy egy másik folyamat memóriájában lévő jelszónak a kiolvasása.
- **Sértetlenség (integrity):** az információt és a programokat csak az módosíthatja, akinek szabad. Megsértése az adatok megváltoztatása, egy hátsó kapu (backdoor) telepítése vagy a kernel lecserélése.
- **Rendelkezésre állás (availability):** a rendszer kiszolgálja a jogosult felhasználóit. Megsértése a rendszer összeomlasztása vagy egy erőforrás kimerítése (szolgáltatásmegtagadásos, azaz denial-of-service támadás). A [2. előadás](../02-quality-and-enterprise-linux/) a rendelkezésre állást mérte; a támadó az üzemszünetek még egy lehetséges oka.

A **fenyegetésmodell** megmondja, milyen támadóknak kell a rendszernek ellenállnia, és azok mire képesek: távoli támadó, aki csak hálózati csomagokat tud küldeni; helyi felhasználó, aki bármilyen programot futtathat; rosszindulatú alkalmazás egy telefonon; felhőbeli bérlő, aki ugyanazon a fizikai gépen osztozik; tolvaj, akinél ott a laptop; rosszindulatú eszköz a PCIe sínen. Egy védekezésnek csak egy fenyegetésmodellhez viszonyítva van értelme: a fájljogosultságok semmit sem érnek a tolvaj ellen, aki az ellopott lemezt egy másik számítógépen indítja el, a teljes lemeztitkosítás pedig semmit sem ér a futó gépen dolgozó távoli támadó ellen.

### Határok és a megbízható számítási bázis

![Felül négyféle támadó (távoli, helyi felhasználó vagy alkalmazás, rosszindulatú eszköz, fizikai hozzáférés); alattuk a felhasználói térben futó folyamatok, a rendszerhívási határ, valamint a kernelből és a firmware-ből, a boot loaderből, a CPU-ból és a TPM-ből álló megbízható számítási bázis; nyilak mutatják, hogy a távoli és a helyi támadás a folyamatokon át a kernelig jut, a DMA-támadás közvetlenül a kernelt, a fizikai támadás a firmware-t éri el](attack-surface.svg)

A **támadási felület** (attack surface) mindazon helyek összessége, ahol a támadó bemenetet adhat: távoli támadónál minden nyitott hálózati port és minden mögötte álló feldolgozó (parser), helyi felhasználónál ezen felül minden rendszerhívás (a Linuxnak több mint 350 van), minden eszközfájl, minden setuid program és minden fájl, amelyet egy privilegizált szolgáltatás beolvas. A támadási felület csökkentése (portok bezárása, setuid programok eltávolítása, rendszerhívások szűrése) a legolcsóbb védekezés, mert az elérhetetlen kódot nem lehet megtámadni.

A legfontosabb határ a felhasználói mód és a kernelmód közötti ([5. előadás](../05-interrupts/#felhasználói-mód-és-kernelmód)): egy folyamat csak rendszerhívásokon, megszakításokon és kivételeken át léphet be a kernelbe, és a kernel ennél az ajtónál minden kérést ellenőriz. Mindaz, ami a biztonsági szabályrendszert kikényszeríti, a **megbízható számítási bázist** (trusted computing base, TCB) alkotja: a kernel, az őt elindító firmware és boot loader, a CPU a mikrokódjával, valamint a biztonsági döntéseket hozó privilegizált szolgáltatások (`login`, `sshd`, `sudo`). A TCB bármely pontján lévő hiba a [11. előadás](../11-access-control/) minden szabályát semmissé teheti, ezért a TCB-nek a lehető legkisebbnek kell lennie; Saltzer és Schroeder (1975) ezt a *mechanizmus egyszerűségének* (economy of mechanism) nevezte. Egy több tízmillió soros monolitikus kernel nagy TCB, és ez az egyik oka annak, hogy a jóval kisebb megbízható maggal rendelkező mikrokernelek és hypervisorok vonzóak a magas biztonsági szintet igénylő rendszerekben.

### Jogosultság-kiterjesztés

A valódi támadások lépésekben haladnak. Egy tipikus lánc egy szerver ellen: (1) a támadó olyan kérést küld, amely egy hálózati szolgáltatás hibáját kihasználva a támadó által választott kódot futtat a szolgáltatás felhasználói azonosítójával (*távoli kódfuttatás*, remote code execution); (2) innen egy második hibát használ ki, egy setuid programban vagy a kernelben, hogy root legyen (*helyi jogosultság-kiterjesztés*, local privilege escalation); (3) tartóssá teszi a hozzáférését, például egy kernelmodul telepítésével vagy a rendszerindítási lánc módosításával (*tartós megtelepedés*, persistence). A **jogosultság-kiterjesztés** (privilege escalation) általános neve annak, ha valaki olyan jogokat szerez, amelyeket nem kapott meg: *vertikális* kiterjesztés egy közönséges felhasználóból rootba vagy felhasználói módból kernelmódba, *horizontális* kiterjesztés egy felhasználó fiókjából egy másikéba. Minden lépéshez külön sérülékenység kell, így minden lépés egy olyan pont, ahol egy védekezés megállíthatja a láncot.

### Mélységi védelem

A [11. előadás](../11-access-control/#mélységi-védelem) a hozzáférés-szabályozásnál vezette be a **mélységi védelmet** (defence in depth): tűzfal, a szolgáltatás konfigurációja, DAC és MAC, egymás után. Ugyanez az elv formálja ezt az előadást is. Egyetlen védekezés sem tökéletes, ezért egy támadás minden lépése több, egymástól független akadályba ütközik: a szolgáltatás memóriahibájának kihasználását a stack canary, az NX, az ASLR és a CFI nehezíti; ha mégis sikerül, a szolgáltatás saját felhasználója, a capabilityjei, a seccomp-szűrője és a SELinux domainje korlátozza, mit nyer a támadó; egy kernelhiba kihasználását a kernel megerősítése nehezíti; egy manipulált rendszerindítási láncot pedig a Secure Boot és a measured boot észlel. Anderson (2020) éppen így írja le a biztonságtechnikát (security engineering): meg kell érteni a támadó lehetőségeit, és annyi független akadályt kell az útjába állítani, hogy a legolcsóbb támadás is többe kerüljön, mint amennyit ér.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> CIA-hármas, bizalmasság, sértetlenség, rendelkezésre állás, szolgáltatásmegtagadás, támadási felület, megbízható számítási bázis, a mechanizmus egyszerűsége, távoli kódfuttatás, jogosultság-kiterjesztés, tartós megtelepedés, mélységi védelem</summary>

- **CIA-hármas:** a három dolog, amit a biztonság véd: a **bizalmasság** (a titok titok marad), a **sértetlenség** (semmi sem változik engedély nélkül) és a **rendelkezésre állás** (a rendszer működik azoknak, akiknek szükségük van rá).
- **Szolgáltatásmegtagadás (denial of service):** olyan támadás, amely nem lop el semmit, hanem megbénítja a rendszert, mint amikor valaki elállja egy bolt ajtaját, hogy egyetlen vevő se tudjon bemenni.
- **Támadási felület:** egy ház összes ajtaja, ablaka és levélnyílása, amelyen át valaki megpróbálhat bejutni. Kevesebb nyílás, kevesebb esély.
- **Megbízható számítási bázis (TCB, trusted computing base):** mindazok a részek, amelyeknek hibátlanul kell működniük ahhoz, hogy a védelem érvényesüljön: a kernel, a firmware, a processzor. Ha ezek közül bármelyik hibás, a ráépülő zárak nem segítenek.
- **A mechanizmus egyszerűsége (economy of mechanism):** az őr legyen egyszerű és kicsi, hogy ellenőrizni lehessen, nincs-e rajta rés.
- **Távoli kódfuttatás (remote code execution):** egy támadó a hálózaton keresztül ráveszi a számítógépedet, hogy az ő utasításait hajtsa végre.
- **Jogosultság-kiterjesztés:** egy támadó, aki kevés joggal jutott be, több jogot szerez, például rendszergazda lesz. Mintha a bolttérből felmászna az igazgatói irodába.
- **Tartós megtelepedés (persistence):** a támadó gondoskodik róla, hogy bent maradjon, egy újraindítás után is, mint aki elrejt egy pótkulcsot.
- **Mélységi védelem:** több, egymástól független zár egymás után, hogy egy feltörése ne legyen elég.

</details>

## Memóriabiztonsági hibák

### Miért éppen a C és a C++?

A kernel, a C könyvtár, a legtöbb rendszerszolgáltatás, a böngészők és a nyelvi futtatókörnyezetek C-ben vagy C++-ban készülnek. Ezek a nyelvek közvetlen hozzáférést adnak a programozónak a memóriához: egy mutató csak egy cím, a tömbindexet senki sem veti össze a tömb méretével, a memóriát kézzel kell felszabadítani, és semmi sem akadályozza meg, hogy a program egy mutatót akkor is használjon, amikor a mögötte lévő memóriát már felszabadították vagy újrahasznosították. Ettől gyorsak és alkalmasak operációs rendszerek írására, és emiatt engedheti meg egyetlen tévedés is, hogy a bemenő adat felülírjon vele semmilyen kapcsolatban nem álló memóriát. Egy program **memóriabiztos** (memory-safe), ha minden memória-hozzáférése azon az objektumon belül marad, amelyre szánták (*térbeli*, spatial biztonság), és csak addig történik, amíg az objektum létezik (*időbeli*, temporal biztonság). A C és a C++ egyiket sem garantálja; az ellenőrzés a programozó dolga (Szekeres et al., 2013).

A következményeket a legnagyobb szoftvergyártók megmérték. A Microsoft 2019-ben arról számolt be, hogy azoknak a sérülékenységeknek, amelyekhez évente CVE-azonosítót rendel, körülbelül 70%-a memóriabiztonsági probléma (Thomas, 2019). A Chromium-projekt ugyanezt az arányt, nagyjából 70%-ot találta a böngésző 2015 óta talált 912 magas és kritikus súlyosságú biztonsági hibája között, és ezeknek a memóriabiztonsági hibáknak a fele use after free hiba volt (The Chromium Projects, n.d.). Az Androidban 2019-ben a sérülékenységek 76%-a volt memóriabiztonsági hiba (Vander Stoep & Rebert, 2024). Már az első internetes féreg is, 1988-ban, egy buffer overflow révén terjedt a `fingerd` démonban, amely egy sort egy rögzített méretű pufferbe olvasott be a `gets` függvénnyel (Spafford, 1989).

### A verem és a visszatérési cím

Minden függvényhívás egy **veremkeretet** (stack frame) helyez a verembe: a visszatérési címet (ahol a hívóban folytatni kell), a hívó elmentett keretmutatóját (frame pointer) és a függvény lokális változóit, köztük tömböket, például egy bemeneti sor pufferét. x86-64-en a verem az alacsonyabb címek felé nő, egy tömb viszont az alsó végétől felfelé töltődik fel. Ha tehát egy függvény több bájtot másol egy lokális pufferbe, mint amennyi belefér, a többletbájtok azt írják felül, ami a keretben a puffer *fölött* van: más lokális változókat, az elmentett keretmutatót és a visszatérési címet.

![Két veremkeret egymás mellett. Balra canary nélkül fordítva: egy 16 bájtos puffer, az elmentett rbp, a visszatérési cím és a main keretének legalsó bájtjai, mind 0x41 bájtokkal felülírva; a ret a 0x4141414141414141 értéket veszi ki, és a program SIGSEGV-t kap. Jobbra -fstack-protector-stronggal fordítva: puffer, kitöltés, canary, elmentett rbp és visszatérési cím; a túlcsordulás megváltoztatja a canaryt, és a ret előtti ellenőrzés leállítja a programot](stack-frame.svg)

Az ábra az `overflow.c` [bemutatóprogram](#buffer-overflow-a-veremben-észlelés) mért elrendezését mutatja. A program `greet` függvénye az argumentumát `strcpy`-vel egy `char buf[16]` pufferbe másolja; a `strcpy` a lezáró nulla bájtig másol, és semmit sem tud a `buf` méretéről. Egy 40 bájtos argumentummal a másolás túlfut az elmentett keretmutatón és a visszatérési címen. Amikor a `greet` végrehajtja a `ret` utasítást, a processzor kiveszi a veremből a felülírt értéket, és oda ugrik. Itt ez `0x4141414141414141` („AAAAAAAA”), ami nem érvényes cím, így a program összeomlik. A bájtok azonban a bemenetből származnak: aki a bemenetet irányítja, az választja ki, hol folytatódjon a program. Ez a **verembeli buffer overflow** (stack buffer overflow), amelyet széles közönség számára Aleph One (1996) írt le, és amely két évtizeden át a legfontosabb behatolási út volt.

### Heaphibák: use after free és double free

A `malloc`-kal kapott memória a **heapen** él, amíg a `free` vissza nem adja. A memóriafoglaló (allocator) a saját nyilvántartását (méreteket, szabadlistákat) a blokkok mellett vagy azokon belül tartja, és a felszabadított blokkokat gyorsan újra kiosztja. Ez két időbeli hibát tesz veszélyessé:

- **Use after free (UAF):** a program a felszabadítás után is megtart egy mutatót a blokkra, és később használja. Közben a foglaló ugyanazt a memóriát már odaadhatta egy másik objektumnak, így az elavult mutató most valaki más adatait olvassa vagy írja. Ha ez az objektum függvénymutatót tartalmaz (például egy C++ objektum mutatóját a virtuálisfüggvény-táblájára), akkor a támadó, aki az új objektum tartalmát irányítja, a következő indirekt hívást is irányítja. A [bemutató](#heaphibák-glibc-és-addresssanitizer) azt mutatja, hogy egy felszabadított blokkot a következő, azonos méretű `malloc` azonnal újra kiad.
- **Double free:** ugyanannak a blokknak a kétszeri felszabadítása összezavarja a foglaló szabadlistáját, így két későbbi foglalás ugyanazt a memóriát kaphatja.

A **heapbeli buffer overflow** (heap buffer overflow) a térbeli megfelelő: egy heapblokk végén túlírva a következő blokk vagy a foglaló metaadatai íródnak felül. A heaphibákat nehezebb kihasználni, mint a klasszikus verembeli túlcsordulást, de ma ezek uralják a statisztikákat: a Chromium fenti adataiban a use after free a legnagyobb egyedi hibaosztály.

### Egészszám-túlcsordulás és format string hibák

Két további hibaosztály vezet gyakran memóriasérüléshez:

- **Egészszám-túlcsordulás (integer overflow):** a rögzített szélességű egész számok körbefordulnak. Ha egy program egy `malloc` hívás méretét `count * size` alakban számolja ki, kis számot kaphat, ha a szorzat meghaladja a $2^{32}$ vagy $2^{64}$ értéket; ekkor kis blokkot foglal, majd `count` elemet másol bele: ez egy aritmetika okozta heap overflow. Az előjelhibák hasonlók: egy negatív hossz, amely átmegy egy `len < max` ellenőrzésen, a `memcpy`-ben óriási előjel nélküli számmá válik.
- **Format string hiba:** `printf("%s", user_input)` helyett `printf(user_input)`. A formátumsztringet a függvény értelmezi, így egy `%x`-et tartalmazó bemenet hatására a `printf` olyan értékeket ír ki a veremből, amelyeket meg sem kapott, a `%n` konverzió pedig, amely az addig kiírt karakterek számát egy mutató argumentumon át *beírja* a memóriába, lehetővé teszi, hogy a bemenet memóriát írjon. A fordítók figyelmeztetnek a nem konstans formátumsztringekre (`-Wformat-security`), a FORTIFY_SOURCE pedig elutasítja a `%n`-t írható memóriában lévő formátumsztringekben.

### A hibától a támadásig

A korai exploitok **kódinjektálást** (code injection) használtak: a bemenet gépi kódot tartalmazott, és a felülírt visszatérési cím a pufferbe mutatott, a verembe, ahol ez a kód volt. Ennek az NX (lásd alább) vetett véget, mert a verem már nem végrehajtható. A támadók áttértek a **kód-újrafelhasználásra** (code reuse): saját kód bejuttatása helyett olyan kódra irányítják a vezérlést, amely már ott van a programban vagy a könyvtáraiban. A legegyszerűbb forma egy könyvtári függvénybe tér vissza (*return-to-libc*); általánosítása, a **return-oriented programming** (ROP) a meglévő kódban talált, `ret`-tel végződő rövid utasítássorozatok sokaságát fűzi össze, így a veremben lévő felülírt visszatérési címek sorozata önálló programmá válik. Shacham (2007) megmutatta, hogy már a C könyvtár egymagában elég ilyen sorozatot tartalmaz tetszőleges számításhoz. A kód-újrafelhasználáshoz nem kell végrehajtható adat, de tudni kell, *hol* van a kód, és felül kell írni visszatérési címeket vagy függvénymutatókat. Pontosan ezt a két feltételt támadja az ASLR és a control-flow integrity.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> memóriabiztonság, térbeli és időbeli biztonság, mutató, veremkeret, visszatérési cím, keretmutató, strcpy, buffer overflow, heap, malloc és free, use after free, double free, egészszám-túlcsordulás, format string, kódinjektálás, kód-újrafelhasználás, return-to-libc, ROP</summary>

- **Memóriabiztonság:** garancia arra, hogy a program csak azt a memóriát érinti, amely ahhoz tartozik, amin éppen dolgozik (**térbeli**: nem lép túl egy tömb végén), és csak addig, amíg az még létezik (**időbeli**: nem azután, hogy visszaadta).
- **Mutató (pointer):** olyan változó, amely egy memóriacímet tárol, mint egy cetli, amelyre egy házszámot írtak.
- **Veremkeret (stack frame):** az a terület, amelyet egy függvény a hívásakor a veremben kap; itt vannak a lokális változói és azok az adatok, amelyekkel vissza lehet térni a hívójához.
- **Visszatérési cím:** az a hely a hívó függvényben, ahol a program folytatódik, amikor a meghívott függvény befejeződik. **Keretmutató** (frame pointer, `rbp`): egy regiszter, amely megjelöli, hol van az aktuális függvény kerete.
- **strcpy:** egy C függvény, amely egy szöveget a végjeléig (egy nulla bájtig) másol, és nem kérdezi meg, mennyi hely van a célterületen.
- **Buffer overflow:** egy tárolóterületre több kerül, mint amennyi belefér, és a többlet átfolyik a szomszédos memóriába, mint amikor egy fél literes pohárba egy litert öntesz.
- **Heap; malloc és free:** a heap az a memória, amelyet a program futás közben kér; a `malloc` kölcsönkér egy darabot, a `free` visszaadja.
- **Use after free:** egy memóriadarab használata azután, hogy visszaadtad, amikor már valaki más használhatja. Mint amikor kijelentkezés után visszamész a szállodai szobába, ahová már beköltözött a következő vendég.
- **Double free:** ugyanannak a darabnak a kétszeri visszaadása, ami összezavarja a nyilvántartást arról, hogy kinél mi van.
- **Egészszám-túlcsordulás:** egy szám túl nagyra nő a rögzített számú számjegyéhez képest, és körbefordulva kicsi lesz, mint az autó kilométer-számlálója, amely 999999-ről 000000-ra ugrik.
- **Format string:** a `printf`-nek átadott minta, például `"%d alma"`. Ha egy felhasználó szövegét használják mintaként, a benne lévő `%` kódokat a függvény végrehajtja.
- **Kódinjektálás:** új utasítások becsempészése egy programba adatként, és a program rávétele, hogy futtassa őket.
- **Kód-újrafelhasználás, return-to-libc, ROP:** új utasítások bejuttatása helyett a támadó a programban már meglévő utasításdarabokat fűzi össze, mint amikor valaki újságból kivágott betűkből ragaszt össze egy zsarolólevelet. A **ROP** (return-oriented programming) ennek általános formája; a **return-to-libc** a legegyszerűbb eset, amikor egyetlen létező könyvtári függvényre ugrik a program.

</details>

## Védekezés a memóriasérülés ellen

Az alábbi védekezési módok mindegyike a támadási lánc egy-egy lépését töri meg: a visszatérési cím felülírását, az adat végrehajtását, a címek ismeretét vagy a vezérlés átirányítását. Egyik sem szünteti meg a hibát; együtt azonban nehézzé és drágává teszik a kihasználást. Szekeres et al. (2013) ugyanennek a láncnak a mentén rendszerezik őket.

### Stack canaryk

A **stack canary** (a kanárimadárról kapta a nevét, amely a bányászokat figyelmeztette a sújtólégre) egy véletlen érték, amelyet a fordító által generált függvényprológus a keret lokális változói és elmentett regiszterei közé helyez, és amelyet az epilógus a `ret` előtt ellenőriz. Egy pufferből a visszatérési cím felé haladó lineáris túlcsordulásnak először a canaryt kell felülírnia; ha az érték megváltozott, a program meghívja a `__stack_chk_fail` függvényt, amely kiírja, hogy `*** stack smashing detected ***`, és leállítja a programot, még mielőtt a sérült visszatérési címet bármi felhasználná. Az ötletet a StackGuard vezette be (Cowan et al., 1998). A GCC `-fstack-protector` kapcsolója a karaktertömböt tartalmazó függvényeket védi, a `-fstack-protector-strong` (az Ubuntu és a Fedora alapértelmezése) minden olyan függvényt, amelynek bármilyen lokális tömbje vagy olyan változója van, amelynek a címét felhasználják, a `-fstack-protector-all` pedig minden függvényt. x86-64-es Linuxon a canaryt a folyamat indulásakor választja ki a rendszer, és a szál lokális tárolójában (thread-local storage, `%fs:0x28`) tárolja; legalsó bájtja mindig nulla, így a nulla bájtnál megálló sztringfüggvények nem tudják sem átmásolni, sem kiírni.

A canary csak azokat a felülírásokat észleli, amelyek megváltoztatják a canaryt. Nem észleli azt a túlcsordulást, amely alatta marad (más lokális változókat vagy a kitöltést írja felül, ahogy a [bemutató](#buffer-overflow-a-veremben-észlelés) mutatja), a heapen történő túlcsordulást, sem azt az írást, amely egy sérült indexen vagy mutatón át átugorja a canaryt. A támadó pedig, aki ki tudja olvasni a canaryt, például egy format string hibán keresztül, változatlanul visszaírhatja.

### Nem végrehajtható memória: NX és W^X

A [4. előadás](../04-fetch-execute-cycle/#memóriajogosultságok-egy-valódi-folyamatban) bevezette az **NX** bitet (no-execute; az Intel XD-nek, az Arm XN-nek hívja): egy laptáblabitet, amely megtiltja, hogy egy lapról utasítást töltsön be a processzor, és a **W^X** szabályt, amely szerint minden lap vagy írható, vagy végrehajtható, de soha nem mindkettő. A verem, a heap és az adatterület írható, tehát nem végrehajtható, így a bejuttatott kód nem futhat. Az AMD 2003-ban, az AMD64-gyel vezette be ezt a bitet az x86-ba, az operációs rendszerek 2004 körül vették át (a Windows DEP-nek hívja). Egy program a `GNU_STACK` programfejléccel (`RW`, nem `RWE`) kér nem végrehajtható vermet, ezt a [bemutató](#milyen-védelmei-vannak-egy-programnak) meg is vizsgálja. Az NX véget vetett a kódinjektálásnak, és emiatt fordultak a támadók a kód-újrafelhasználás felé. A futás közben kódot generáló programoknak, például a JIT-fordítóknak a lapokat kifejezetten át kell kapcsolniuk írhatóról végrehajthatóra (`mprotect`), amit a kernel és a SELinux tovább korlátozhat.

### ASLR és pozíciófüggetlen programok (PIE)

A kód-újrafelhasználáshoz címek kellenek: egy könyvtári függvény címe, a hasznos utasítássorozatok címe, a puffer címe. Az **ASLR** (address space layout randomisation, a címtartomány elrendezésének véletlenítése), amelyet a PaX projekt vezetett be Linuxra 2001-ben, és amely 2005 óta a hivatalos Linux-kernel része, a vermet, a heapet, a megosztott könyvtárakat és a memórialeképezéseket minden programindításkor véletlen címre helyezi (a hatását a [9. előadás](../09-virtual-memory/#egy-folyamat-címtartománya) megmutatta). A program saját kódja csak akkor mozog, ha az **pozíciófüggetlen futtatható állomány** (position-independent executable, PIE), vagyis tetszőleges címen futni képes módon fordították; egy klasszikus, nem PIE program mindig a rögzített 0x400000 címre töltődik be, ami a támadóknak egy ismert kódblokkot ad. A modern disztribúciók minden programot PIE-ként fordítanak.

Az ASLR erőssége az **entrópiája**, vagyis a véletlen bitek száma egy címben. $n$ bit esetén a vakon találgató támadó egy-egy próbálkozással $2^{-n}$ valószínűséggel jár sikerrel. Ha a célpontot minden sikertelen próbálkozás után újra véletlenítik (az összeomlott programot új elrendezéssel indítják újra), ehhez átlagosan $2^n$ próbálkozás kell; ha az elrendezés ugyanaz marad (egy forkoló szerver, amelynek gyermekei öröklik), minden rossz tipp kihúzható, és átlagosan nagyjából $2^{n-1}$ próbálkozás kell. A [bemutató](#hová-kerül-minden-az-aslr-mérése) 28 bitet mért a programra, a heapre és az anonim leképezésekre, 30 bitet a veremre és 19 bitet a C könyvtárra, amelynek kezdete 2 MiB-ra van igazítva, hogy huge page-ekkel lehessen lefedni. A bitek számánál két korlát fontosabb. Először: csak az egyes területek *kezdőcíme* véletlen, a területen belüli eltolások rögzítettek, így egyetlen kiszivárgott, egy könyvtárba mutató pointer felfedi az egész könyvtárat. Másodszor: az a szerver, amely újbóli `exec` nélkül forkolja a gyermekeit, minden gyermeknek a szülő elrendezését adja, így egy összeomlasztó-újrapróbáló támadás kitapogathatja. Az ASLR ezért arra kényszeríti a támadókat, hogy előbb információszivárgást találjanak, és így egy hibából kéthibás támadás lesz.

### RELRO és FORTIFY_SOURCE

Egy dinamikusan linkelt program a könyvtári függvényeket a **global offset table** (GOT) segítségével hívja; ez egy függvénymutatókból álló tábla, amelyet a dinamikus linker tölt ki. Egy írható függvénymutató-tábla, amely a kódtól ismert távolságra van, ideális célpont: ha a támadó felülírja a `printf` bejegyzését, a `printf` következő hívása oda megy, ahová ő akarja. A **RELRO** (relocation read-only) hatására a dinamikus linker csak olvashatóvá teszi ezeket a táblákat, miután kitöltötte őket: a *részleges* (partial) RELRO csak néhány szekciót véd, a *teljes* (full) RELRO (`-z relro -z now` linkelés, `BIND_NOW`) induláskor minden függvényt feloldja, majd az egész GOT-ot csak olvashatóvá teszi.

A **FORTIFY_SOURCE** (`-D_FORTIFY_SOURCE=1`, `2` vagy `3`, optimalizálással együtt) az olyan hívásokat, mint a `strcpy`, a `memcpy`, a `sprintf` és a `read`, ellenőrző változatokra (`__strcpy_chk`) cseréli, valahányszor a fordító ismeri a cél méretét. Az ellenőrzés a másolás *előtt* történik, így a túlcsordulás meg sem történik: a program `*** buffer overflow detected ***` üzenettel leáll. A 3-as szint, az Ubuntu 24.04 GCC-jének alapértelmezése, a csak futásidőben ismert méreteket is felhasználja. Csak azokat az eseteket fogja meg, ahol a méret ismert; egy ismeretlen eredetű mutatón át elért memóriába történő másolást nem ellenőriz.

### Control-flow integrity

A **control-flow integrity** (CFI, a vezérlési folyam sértetlensége) az utolsó lépést támadja: bármit rontott is el a támadó, a program csak a legitim vezérlésifolyam-gráfjának élei mentén adhatja át a vezérlést (Abadi et al., 2005). A fordítók szoftveres CFI-t úgy valósítanak meg, hogy minden indirekt hívás célját összevetik a megfelelő típusú függvények halmazával (a Clang `-fsanitize=cfi` kapcsolója, a Microsoft Control Flow Guardja). A processzorok ma már hardveresen is támogatják, a kétféle élre:

![Balra a shadow stack: a CALL a visszatérési címet a közönséges verembe és egy védett shadow stackbe is beírja; a RET összeveti őket, és control-protection kivételt vált ki, ha eltérnek. Jobbra az indirect branch tracking: egy indirekt hívás csak endbr64 utasításra érkezhet; ha egy függvény közepére érkezik, kivétel keletkezik](cfi.svg)

- **Visszafelé mutató élek (visszatérések).** Az Intel Control-flow Enforcement Technology (CET, 2020 óta a processzorokban) egy **shadow stacket** (árnyékverem) ad hozzá: a `CALL` a visszatérési címet a közönséges verembe és egy második verembe is beírja, olyan lapokra, amelyeket a közönséges tároló utasítások nem írhatnak, a `RET` pedig összeveti a két példányt. Egy felülírt visszatérési cím már nem egyezik, és a processzor control-protection kivételt vált ki (Shanbhogue et al., 2019). Az Arm **pointer authentication** (PAC, Armv8.3) ehelyett egy titkos kulccsal és a veremmutatóval aláírja a visszatérési címet, és az aláírást a mutató fel nem használt felső bitjeiben tárolja; egy `AUT` utasítás a visszatérés előtt ellenőrzi, és a hamisított cím elbukik az ellenőrzésen.
- **Előrefelé mutató élek (indirekt hívások és ugrások).** Az Intel **indirect branch tracking** (IBT) megköveteli, hogy minden indirekt hívás vagy ugrás egy `endbr64` utasításra érkezzen, amelyet a fordító minden olyan függvény elejére elhelyez, amelynek a címe felhasználható; az Arm **branch target identification** (BTI, Armv8.5) ugyanezt teszi `BTI` leszállási pontokkal (landing pad). A ROP és rokonai azon alapulnak, hogy a meglévő kód közepébe ugranak, ezt pedig ezek az ellenőrzések megtiltják.

A hardveres CFI-hez minden rétegre szükség van: a fordítónak elő kell állítania (`-fcf-protection` x86-on, `-mbranch-protection` Armon; az Ubuntu GCC-je alapértelmezésben ezt teszi, ahogy a [bemutató](#milyen-védelmei-vannak-egy-programnak) mutatja), a folyamatba betöltött minden könyvtárat kompatibilisnek kell jelölni, és a kernelnek be kell kapcsolnia: a Linux az 5.18-as verzió óta támogatja az IBT-t magában a kernelben, és a 6.6 óta a felhasználói térbeli shadow stacket. Az Apple 2018 óta, az A12-es chip óta használja a PAC-ot a saját processzoraiban.

### Előbb megtalálni a hibákat: sanitizerek és fuzzing

A fenti mitigációk futásidőben nehezítik a hibák kihasználását; a hibát azonban jobb még a kiadás előtt elkapni. Az **AddressSanitizer** (ASan, `-fsanitize=address`) a program minden memória-hozzáférését instrumentálja, és minden objektumot mérgezett *red zone*-okkal vesz körül; egy shadow memory, amely az alkalmazás memóriájának minden 8 bájtjához 1 bájtot rendel, nyilvántartja, mely bájtok érhetők el. A felszabadított memóriát is megmérgezi, és egy ideig karanténban tartja, így a use after free is kiderül. Az ASan a pontos hozzáférést jelenti, a foglalás és a felszabadítás hívási vermével együtt, átlagosan kb. 73%-os lassulás árán (Serebryany et al., 2012), ami teszteléshez megfelel, éles üzemhez nem. Rokon sanitizerek találják meg az inicializálatlan olvasásokat (MSan), a nem definiált viselkedést, például az előjeles túlcsordulást (UBSan) és az adatversenyeket (TSan); a kernelnek sajátjai vannak (KASAN, KCSAN). A **fuzzing** automatikusan mutált bemenetek millióival bombázza a programot, és figyeli az összeomlásokat; a sanitizerekkel együtt, amelyek a csendes memóriasérülésből összeomlást csinálnak, nagy tömegben találja meg a memóriahibákat. A Google syzkaller nevű eszköze folyamatosan fuzzolja a Linux-kernel rendszerhívásait, és már több ezer kernelhibát talált.

### Memóriabiztos nyelvek

A strukturális válasz az, hogy az új kódot olyan nyelven írjuk, amely felépítéséből adódóan memóriabiztos: ellenőrzött határú tömbök, nincs kézi `free`, nincsenek lógó mutatók. A szemétgyűjtéses nyelvek (Java, Go, C#) ezt egy futtatókörnyezet árán érik el; a **Rust** fordítási időben, a tulajdonlási (ownership) és kölcsönzési (borrowing) szabályai révén, a C-hez hasonló teljesítménnyel, ami rendszerszoftverhez is használhatóvá teszi. Az Android tapasztalata mutatja a hatást: ahogy az új kód nagyrészt Rustban és Kotlinban készült, a memóriabiztonsági hibák aránya az Android sérülékenységei között a 2019-es 76%-ról 2024-re 24%-ra esett, bár a meglévő C és C++ kód nagy része megmaradt, mert a sérülékenységek az új kódban koncentrálódnak (Vander Stoep & Rebert, 2024). A Linux a 6.1-es verzió óta fogad el Rustban írt drivereket ([14. előadás](../14-mobile-wearable-embedded/#rust-a-kernelekben)). Az a Rust-kód, amelynek ellenőrizetlen műveleteket kell végeznie, ezeket `unsafe`-ként jelöli, így a megmaradó kockázat kicsi, átnézhető helyekre korlátozódik.

### A kernel megerősítése

A kernelhiba a legértékesebb célpont: teljes irányítást ad a gép felett, minden hozzáférés-szabályozási szabályon túl. A kernel ezért ugyanezeket az ötleteket alkalmazza önmagára, néhány olyannal kiegészítve, amelyet csak a hardver adhat:

- A **KASLR** (kernel ASLR, Linux 3.14, a 4.12 óta alapértelmezetten bekapcsolva) minden rendszerindításkor véletlen címre tölti a kernel image-et, és véletleníti a fizikai memória direkt leképezésének kezdőcímét is (`CONFIG_RANDOMIZE_MEMORY`). Hogy a címek titokban maradjanak, a kernel elrejti őket: a `/proc/kallsyms` nullákat mutat a `CAP_SYSLOG` nélküli folyamatoknak, ezt a `kernel.kptr_restrict` szabályozza, a `kernel.dmesg_restrict` pedig elzárja a közönséges felhasználók elől a kernelnaplót, amely gyakran tartalmaz címeket ([bemutató](#a-kernel-elrejti-a-címeit)).
- Az **SMEP és SMAP** (supervisor mode execution / access prevention, Intel, 2012 és 2014; az Arm PXN-nek és PAN-nak hívja) megakadályozza, hogy a kernel felhasználói térbeli lapokat hajtson végre, illetve felhasználói memóriát olvasson vagy írjon, kivéve a kifejezett másolórutinokat (`copy_from_user`, amely ideiglenesen feloldja az SMAP-ot). SMEP nélkül egy kernelhiba, amely elrontott egy függvénymutatót, egyszerűen a támadó által a felhasználói memóriában elhelyezett kódra irányíthatná azt.
- **W^X a kernelre** (`CONFIG_STRICT_KERNEL_RWX`): a kernel kódja csak olvasható, az adatai nem végrehajthatók, a csak olvasható adatok pedig a rendszerindítás után írásvédetté válnak („Write protecting the kernel read-only data” a [rendszerindítási naplóban](#hogyan-indult-ez-a-gép)). A kernel saját stack protectorral, FORTIFY_SOURCE-szal és, ahol engedélyezve van, IBT-vel készül; a *hardened usercopy* a felhasználói és a kernelmemória közötti minden másolás méretét összeveti az érintett kernelobjektummal.
- A **lockdown** (Linux 5.4) a futó kernelt a root ellen védi. `integrity` módban megtagad mindent, amivel a root módosíthatná a kernelt: az aláíratlan modulokat, egy aláíratlan kernel `kexec`-jét, a `/dev/mem` és a modellspecifikus regiszterek írását, a közvetlen I/O-port-hozzáférést és a debugfs fájljait; a `confidentiality` mód a kernelmemória olvasását is tiltja (`/proc/kcore`, kprobe-ok, BPF-olvasás). A lockdown szintjét csak emelni lehet, csökkenteni a következő rendszerindításig nem (Linux man-pages project, n.d.). Ez zárja be azt a rést a „root” és a „kernel” között, amelyre a Secure Bootnak (lásd alább) szüksége van: nélküle a root bármilyen kódot betölthetne egy olyan kernelbe, amelyet indításkor ellenőriztek.

### Sandbox: lemondás a jogokról

A legkisebb jogosultság elve ([11. előadás](../11-access-control/#a-referenciamonitor)) a rendszerhívásokra is érvényes. Egy folyamatnak, amely megbízhatatlan bemenetet dolgoz fel, például egy böngésző renderelőjének, egy PDF-nézőnek vagy egy médiadekódernek, csak néhány rendszerhívásra van szüksége; minden más hívás a kernel támadási felülete. A **seccomp** lehetővé teszi, hogy egy folyamat visszavonhatatlanul korlátozza önmagát. *Strict* módban (Linux 2.6.12) csak a `read`, a `write`, az `_exit` és a `sigreturn` marad; minden más rendszerhívás megöli a folyamatot. *Filter* módban (seccomp-bpf, Linux 3.5) a folyamat egy kis BPF-programot telepít, amelyet a kernel minden rendszerhívásnál lefuttat, bemenetként a hívás számával és argumentumaival, és amely engedélyezést, hibakódot, szignált vagy a folyamat megölését adja vissza (The kernel development community, n.d.-c). A szűrőket a gyermekfolyamatok öröklik, és csak szigorítani lehet őket. Egy nem privilegizált folyamatnak előbb be kell állítania a `no_new_privs` jelzőt, amellyel megígéri, hogy soha nem szerez jogokat egy setuid program `execve`-jével, így egy szűrőt nem lehet egy privilegizált program megtévesztésére használni. A seccompot használja a Chrome, a Firefox, az OpenSSH hitelesítés előtti folyamata, a systemd szolgáltatásai (`SystemCallFilter=`), a [konténermotorok](../13-virtualization-containerization/#capabilityk-seccomp-és-mac-mandatory-access-control) és [minden androidos alkalmazás](../14-mobile-wearable-embedded/#az-alkalmazások-sandboxa). Namespace-ekkel, eldobott capabilitykkel, Landlockkal és egy MAC-domainnel kombinálva **sandboxot** épít: egy olyan folyamatot, amelyről feltételezzük, hogy előbb-utóbb a támadó kezébe kerül, és amelyet úgy zárunk be, hogy a támadó semmit se nyerjen vele.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> stack canary, __stack_chk_fail, NX, W^X, DEP, JIT, ASLR, PIE, entrópia, információszivárgás, GOT, RELRO, FORTIFY_SOURCE, control-flow integrity, shadow stack, CET, PAC, IBT, BTI, endbr64, sanitizer, ASan, red zone, fuzzing, Rust, unsafe, KASLR, kptr_restrict, SMEP, SMAP, lockdown, seccomp, BPF, no_new_privs, sandbox</summary>

- **Stack canary:** egy titkos véletlen szám, amely közvetlenül a visszatérési cím alatt áll. Ha a függvény végén megváltozott, akkor valami felülírta, és a program azonnal leáll (a `__stack_chk_fail` függvényben), mint egy dobozon lévő pecsét, amelyből látszik, hogy kinyitották.
- **NX, W^X, DEP:** a memória vagy adatírásra, vagy utasítások futtatására való, de soha nem mindkettőre; a DEP ennek a Windows-beli neve.
- **JIT** (just-in-time compiler, futás közbeni fordító): olyan program, amely futás közben alakítja a kódot gépi utasításokká, például egy böngésző JavaScript-motorja; szándékosan kell átkapcsolnia a memóriát „írás”-ról „futtatás”-ra.
- **ASLR:** a program részeinek véletlen címekre helyezése minden indításkor, hogy a támadó ne tudja, mi hol van. Mintha minden éjjel átrendeznéd a bútorokat, hogy a betörő ne találjon el a sötétben.
- **PIE** (position-independent executable, pozíciófüggetlen program): úgy fordított program, hogy bármilyen címen futni tudjon, így az ASLR azt is el tudja mozgatni.
- **Entrópia:** hány véletlen bit van: 28 bittel körülbelül 268 millió lehetséges hely van.
- **Információszivárgás (information leak):** olyan hiba, amelynek révén a támadó kiolvashat valamit, például egy címet, aminek rejtve kellene maradnia.
- **GOT** (global offset table): a program listája az általa hívott könyvtári függvények címeiről. **RELRO:** ennek a listának a csak olvashatóvá tétele induláskor, hogy ne lehessen átirányítani.
- **FORTIFY_SOURCE:** a fordító a kockázatos másolófüggvényeket olyan változatokra cseréli, amelyek előbb ellenőrzik a cél méretét.
- **Control-flow integrity:** a program csak oda ugorhat, ahová ugrania kell.
- **Shadow stack, CET, PAC:** a visszatérési címek második, védett példánya (az Intel CET-je), vagy minden visszatérési cím kriptográfiai aláírása (az Arm PAC-ja), hogy egy megváltoztatott visszatérési cím kiderüljön.
- **IBT, BTI, endbr64:** a mutatón keresztüli ugrások csak különleges jelölő utasításokra érkezhetnek (Intelen `endbr64`, Armon `BTI`), amelyeket a fordító a legális belépési pontokra tesz.
- **Sanitizer, ASan, red zone:** tesztelőeszköz, amely futás közben ellenőrzi a program minden memória-hozzáférését. Az ASan minden memóriadarab köré tiltott **red zone**-okat tesz, és jelez, ha bármi hozzájuk ér.
- **Fuzzing:** véletlenszerű, kicsit elrontott bemenetek millióinak rázúdítása egy programra, hogy kiderüljön, mitől omlik össze.
- **Rust, unsafe:** olyan programozási nyelv, amelynek fordítója visszautasítja azokat a programokat, amelyek rosszul használhatnák a memóriát; azt a néhány helyet, ahol meg kell szegni a szabályokat, `unsafe`-ként kell jelölni.
- **KASLR:** ASLR magára a kernelre. **kptr_restrict:** az a beállítás, amely elrejti a kernel címeit a közönséges felhasználók elől.
- **SMEP, SMAP:** processzorfunkciók, amelyek megakadályozzák, hogy a kernel véletlenül vagy egy trükk hatására a közönséges programok memóriáját futtassa vagy hozzányúljon.
- **Lockdown:** olyan üzemmód, amelyben még a rendszergazda sem változtathatja meg a futó kernelt.
- **Seccomp, BPF:** egy folyamat azt mondja a kernelnek: „mostantól tagadd meg tőlem ezeket a rendszerhívásokat”; a szabályokat egy apró **BPF**-programként írják meg, amelyet a kernel minden hívásnál lefuttat.
- **no_new_privs:** egy folyamat ígérete, hogy sem ő, sem a gyermekei soha nem kapnak több jogot, egy setuid program elindításával sem.
- **Sandbox:** zárt játszótér egy olyan programnak, amelyben nem bízol meg teljesen.

</details>

## Side channel támadások és tranziens végrehajtás

Az eddigi védekezési módok mind feltételezik, hogy a hardver pontosan azt teszi, amit az utasításkészlet ígér: egy csak a kernel számára jelölt lap felhasználói módból nem olvasható, és egy sikertelen határellenőrzés megállítja a hozzáférést. 2018 januárjában a hardverhibák két osztálya, a **Meltdown** és a **Spectre** megmutatta, hogy ez a feltételezés túl erős. Ezek az architektúra egyetlen szabályát sem szegik meg; a titkokat egy **side channelen** (mellékcsatornán) át olvassák ki, vagyis a számítás egy olyan fizikai hatásán keresztül, amelynek az architektúra szerint nem volna szabad információt hordoznia.

### Szivárgás időméréssel

A legismertebb side channel a [8. előadás](../08-two-level-memory-and-cache/) gyorsítótára. Hogy egy memóriasor a gyorsítótárban van-e, az a program logikája számára láthatatlan, de megváltoztatja, mennyi ideig tart egy hozzáférés: egy találat néhány nanoszekundum, egy RAM-ig menő hiány nagyjából száz. Ha két program közös gyorsítótárat és némi közös memóriát használ, az egyik a saját, ugyanazokra a sorokra irányuló hozzáféréseinek időzítéséből megtudhatja, mely sorokat érintette a másik. A FLUSH+RELOAD technikában a támadó a `clflush` utasítással kidobja egy megosztott könyvtár egy sorát az összes gyorsítótárból, vár, majd megméri egyetlen olvasás idejét: a gyors olvasás azt jelenti, hogy az áldozat közben használta a sort. Mivel az utolsó szintű gyorsítótáron (last-level cache) az összes mag osztozik, ez különböző magokon futó folyamatok között is működik (Yarom & Falkner, 2014). Ez önmagában csak *hozzáférési mintázatokat* szivárogtat ki, de a hozzáférési mintázatok függhetnek titkoktól: attól, hogy egy kriptográfiai rutin melyik táblázatbejegyzést kereste ki, vagy melyik ágon haladt tovább.

### Meltdown és Spectre

A modern processzorok az utasításokat **spekulatívan** és **sorrenden kívül** (out of order) hajtják végre: megtippelik az elágazások kimenetelét, és előrefutnak, mielőtt a korábbi utasítások befejeződnének; ha egy tipp rossz volt, vagy egy korábbi utasítás kivételt okoz, eldobják az eredményeket. Architekturálisan ezek a **tranziens** utasítások meg sem történtek, hiszen egyetlen általuk előállított regiszter- vagy memóriaérték sem marad meg. A gyorsítótárra gyakorolt hatásuk azonban megmarad.

- A **Meltdown** (Lipp et al., 2018) azokat a processzorokat érintette, amelyek a tranziens végrehajtás során megengedték, hogy egy felhasználói módú betöltés kernelmemóriát olvasson, mielőtt a laptábla-bejegyzés jogosultság-ellenőrzése érvénybe lépett volna. A kivétel megérkezett, és az eredményt eldobták, de az érték addigra már befolyásolta, melyik gyorsítótár-sor töltődött be, és egy időméréssel vissza lehetett nyerni. Mivel a Linux a teljes kernelt minden folyamat címtartományába beleképezte (hogy a rendszerhívások olcsók legyenek), a kernel címtartománya pedig a teljes fizikai memória direkt leképezését is tartalmazza, elvben minden felhasználói folyamat kiolvashatta a gép teljes memóriáját, más folyamatok adatait is beleértve.
- A **Spectre** (Kocher et al., 2019) az elágazásbecslést használja. A támadó úgy tanítja be a becslőt, hogy *az áldozat saját kódja* tranziensen egy olyan úton fusson, amelyen architekturálisan soha nem haladna, például túl egy határellenőrzésen, és egy titoktól függő memóriaterülethez nyúljon. A Spectre-nek nincs szüksége hibás jogosultság-ellenőrzésre, így folyamatok között, a kernel ellen és sandboxokon belül, például egy böngésző JavaScript-motorjában is működik, és egyetlen változtatással nem javítható.

A későbbi kutatások a rokon hibák hosszú családját találták meg (Foreshadow/L1TF, MDS, Retbleed, Downfall és mások), amelyek mindegyike a processzor egy-egy másik belső struktúráján át szivárogtat: az L1 adatgyorsítótáron, a fill és store buffereken, a visszatérésicím-becslőn, a vektorregisztereken.

### Védekezés és ára

Mivel a kiváltó ok a szilíciumban van, az operációs rendszer a mikrokód-frissítésekkel és a fordítóval együttműködve kerüli meg:

- **Kernel page-table isolation (KPTI, a kernel laptábláinak elkülönítése).** A KAISER-terv (Gruss et al., 2017) nyomán a kernel folyamatonként két laptáblakészletet tart: felhasználói módban a kernelből szinte semmi sincs leképezve, így a Meltdownnak nincs mit kiolvasnia. Minden rendszerhívás és megszakítás laptáblát vált, ami időbe kerül; a [9. előadás](../09-virtual-memory/#a-tlb-gyorsítótár-a-címfordításokhoz) PCID-címkéi megakadályozzák, hogy minden váltáskor ki kelljen üríteni a TLB-t, és így elviselhetővé teszik a költséget. Az AMD processzorait a Meltdown soha nem érintette, az Intel pedig a 2018 végétől megjelent generációkban hardveresen javította; ezeken a KPTI ki van kapcsolva.
- **A Spectre ellen:** korlátok (barrier) és mutatómaszkolás a kernel határellenőrzéseinél a felhasználótól kapott indexeken; **retpoline**-ok (a fordító által generált indirekt ugrások, amelyekre a becslőt nem lehet betanítani) vagy hardveres vezérlők, például az enhanced IBRS az indirekt elágazásokra; az elágazásbecslő állapotának törlése (IBPB), amikor másik folyamatra vagy VM-re vált a rendszer; valamint a böngészőkben a **folyamatszintű elkülönítés**, amely minden webhelyet külön folyamatba tesz.
- **A megosztás elkerülése** ott, ahol semmi más nem segít: egy mag két hyperthreadje (simultaneous multithreading, SMT) a mag szinte minden belső pufferén osztozik, ezért a nagy felhőszolgáltatók nem tesznek két különböző ügyfél virtuális CPU-it ugyanarra a magra, a Linux ki tudja kapcsolni az SMT-t (`nosmt`), vagy csak egymásban megbízó feladatokat enged egy magon osztozni (*core scheduling*), az OpenBSD pedig alapértelmezésben kikapcsolja az SMT-t.

A kernel minden általa ismert hibáról jelenti a `/sys/devices/system/cpu/vulnerabilities/` könyvtárban, hogy az adott CPU érintett-e, és melyik védekezés aktív (The kernel development community, n.d.-b). A védekezés költsége néhány százaléktól a rendszerhívás-igényes terheléseknél több tíz százalékig terjed, ezért a csak megbízható kódot futtató gépeken ki lehet kapcsolni (`mitigations=off`).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> side channel, cache-időzítés, FLUSH+RELOAD, clflush, spekulatív végrehajtás, sorrenden kívüli végrehajtás, elágazásbecslés, tranziens végrehajtás, direkt leképezés, Meltdown, Spectre, KPTI, KAISER, PCID, retpoline, IBRS, IBPB, mikrokód, SMT, hyperthread, core scheduling</summary>

- **Side channel (mellékcsatorna):** egy titok megszerzése nem kiolvasással, hanem egy mellékhatásból: mennyi ideig tartott valami, mennyi áramot fogyasztott. Mintha egy kódzáras ajtónál a lekopott festékből találnád ki, mely gombokat nyomják.
- **Cache-időzítés:** annak mérése, hogy egy memóriadarabot gyorsan (benne volt a gyorsítótárban, tehát valaki nemrég használta) vagy lassan lehetett-e kiolvasni.
- **FLUSH+RELOAD, clflush:** a támadó kidob egy közös memóriadarabot a gyorsítótárból (a `clflush` utasítással), vár, majd újra kiolvassa. Ha az olvasás gyors, az áldozat közben biztosan használta.
- **Spekulatív végrehajtás:** a processzor megtippeli, mi következik, és időt spórolva előre nekilát. Ha a tipp rossz volt, eldobja a munkát.
- **Sorrenden kívüli (out-of-order) végrehajtás:** a processzor nem vár meg egy lassú utasítást, hanem már futtatja a tőle nem függő későbbi utasításokat, és a végén helyes sorrendbe rakja az eredményeket.
- **Elágazásbecslés (branch prediction):** a processzornak az a része, amely a korábbi esetek alapján megtippeli, merre megy majd egy `if`.
- **Tranziens végrehajtás:** az eldobott munka. Hivatalosan meg sem történt, de nyomokat hagyhat a gyorsítótárban.
- **Meltdown, Spectre:** a processzorhibák két, 2018-ban felfedezett családja. A Meltdown révén közönséges programok ilyen nyomokon át kiolvashatták a kernel memóriáját; a Spectre ráveszi a programot, hogy spekulatívan a saját titkaihoz nyúljon.
- **Direkt leképezés (direct mapping):** a kernel címtartományának az a része, amelyen át a kernel a számítógép RAM-jának minden bájtját eléri.
- **KPTI** (kernel page-table isolation), **KAISER:** amíg egy közönséges program fut, a kernel memóriáját egyszerűen kihagyják a laptábláiból, így nincs mit kiolvasni. A KAISER az a kutatási terv, amelyre a KPTI épült.
- **PCID:** egy címke minden TLB-bejegyzésen, amely megmondja, melyik címtartományhoz tartozik, így laptáblaváltáskor nem kell minden bejegyzést eldobni.
- **Retpoline:** fordítói trükk, amely a kockázatos indirekt ugrásokat olyan formára alakítja, amellyel a processzor tippelő gépezetét nem lehet félrevezetni.
- **IBRS, IBPB:** processzorvezérlők, amelyek korlátozzák vagy törlik az elágazásbecslő emlékezetét, hogy egy program ne taníthassa be egy másik félrevezetésére.
- **Mikrokód:** a processzor belső firmware-e, amelyet frissíteni lehet, hogy egyes utasítások másképp viselkedjenek.
- **SMT, hyperthread, core scheduling:** SMT esetén (az Intel Hyper-Threadingnek hívja) egy processzormag egyszerre két programot futtat két **hyperthreadként**, és a részeinek nagy részén osztoznak. A **core scheduling** csak egymásban megbízó programoknak engedi, hogy egy magon osztozzanak.

</details>

## A rendszerindítás és a bizalmi lánc

Az eddigi védekezési módokat mind a kernel kényszeríti ki. Az a támadó, aki a kernelt vagy az azt betöltő kódot még az indulás előtt meg tudja változtatni, mindegyiket legyőzte, és egy ilyen módosítás (*bootkit*) minden program újratelepítését túléli. A rendszerindításnak ezért lépésről lépésre kell felépítenie a bizalmat, valamiből kiindulva, amit a támadó nem tud megváltoztatni.

### A bekapcsolástól az initig

PC-n a bekapcsolás az alaplapi flash memóriában lévő **firmware**-t indítja el: régen a BIOS-t, ma az **UEFI**-t. Ez inicializálja a processzort, a memóriát és az eszközöket, majd betölt egy boot loadert az EFI rendszerpartícióról (EFI system partition), egy kis FAT fájlrendszerről a lemezen. Linuxon az első lépcső általában a **shim**, egy apró, a Microsoft által aláírt betöltő (lásd alább), amely a **GRUB**-ot vagy a **systemd-boot**-ot tölti be. A boot loader beolvassa a konfigurációját, betölti a **kernelt** és az **initramfs**-t (egy kis tömörített fájlrendszert azokkal a driverekkel és eszközökkel, amelyek a valódi gyökér-fájlrendszer megtalálásához és feloldásához kellenek), majd a kernelre ugrik. A kernel inicializálja magát, kicsomagolja az initramfs-t, lefuttatja annak `init`-jét, amely csatolja a valódi gyökér-fájlrendszert, végül átadja a vezérlést a valódi **init**-nek, általában a systemd-nek, az 1-es folyamatnak, amely elindítja az összes szolgáltatást. Minden lépcső olyan kódot futtat, amelyet az előző töltött be a lemezről, így minden lépcső sértetlensége az előzőétől függ: ez a **bizalmi lánc** (chain of trust). A kezdetén álló horgony, amelyben ellenőrzés nélkül kell megbízni, a **bizalmi gyökér** (root of trust): PC-n a flashben lévő firmware, amelyet ideális esetben a CPU-ban vagy a lapkakészletben lévő boot ROM ellenőriz (Intel Boot Guard, AMD Platform Secure Boot).

### Secure Boot: ellenőrzés futtatás előtt

Az **UEFI Secure Boot** (UEFI 2.3.1, 2011) hatására minden lépcső ellenőrzi a következő digitális aláírását, mielőtt elindítaná (UEFI Forum, 2024). A firmware tárolja a megbízható tanúsítványok adatbázisát (`db`), a visszavont aláírások és hash-ek adatbázisát (`dbx`), valamint azokat a kulcsokat, amelyekkel ezek módosíthatók (a platformkulcsot, PK, és a kulcscserélő kulcsokat, KEK). Egy boot loadert csak akkor futtat, ha azt egy `db`-beli tanúsítvány írta alá, és nincs visszavonva a `dbx`-ben. Gyakorlatilag minden PC a Microsoft tanúsítványaival a `db`-ben kerül forgalomba, ezért a Linux-disztribúciók az első lépcsős betöltőjüket, a shimet, a Microsofttal íratják alá; a shim tartalmazza a disztribúció saját tanúsítványát, és ehhez méri a GRUB-ot és a kernelt. Az a felhasználó, aki saját kernelt fordít, saját kulcsot regisztrálhat **Machine Owner Key**-ként (MOK, a gép tulajdonosának kulcsa) a `mokutil` paranccsal. Az így indított kernel folytatja a láncot: csak aláírt modulokat fogad el, és a lockdown révén még a rootnak sem engedi, hogy aláíratlan kódot töltsön bele; több disztribúció automatikusan bekapcsolja a lockdownt, ha a gép Secure Boottal indult.

A Secure Boot *kikényszerítés*: egy aláíratlan vagy visszavont komponens nem fut le. A gyengesége az, hogy mindenben megbízik, ami szabályosan alá van írva: egy aláírt, de sérülékeny boot loader nyitott ajtó marad, amíg a hash-e be nem kerül a `dbx`-be, ezért a visszavonási frissítések a firmware-karbantartás rendszeres részei.

### Measured boot és a TPM

A **measured boot** (mért rendszerindítás) semmit sem állít meg, hanem *rögzít*. Mielőtt egy lépcső elindítaná a következőt, kiszámítja annak kriptográfiai hash-ét, és elküldi a **Trusted Platform Module**-nak (TPM), egy kis biztonsági chipnek (vagy a processzor firmware-ének egy védett funkciójának), amelynek saját kulcsai és **platform configuration register**-ei (PCR-ek, platformkonfigurációs regiszterek) vannak. Egy PCR-t nem lehet írni, csak **kiterjeszteni** (extend):

$$\mathrm{PCR}_{\mathrm{új}} = \mathrm{SHA256}(\mathrm{PCR}_{\mathrm{régi}} \mathbin{\Vert} h)$$

ahol $h$ az új komponens hash-e, a $\Vert$ pedig az összefűzés. A PCR-ek reset után nulláról indulnak, és mivel a hash-függvény nem fordítható meg, egy PCR végső értéke a belemért összes komponenstől és azok sorrendjétől függ: semmilyen később futó szoftver nem tud egy PCR-t egy általa választott értékre hozni (Trusted Computing Group, n.d.). Egy memóriában tárolt *eseménynapló* (event log) minden mérést felsorol, így egy ellenőrző újraszámolhatja a PCR-eket, és láthatja, mi van mindegyikben. Hogy melyik komponenst melyik PCR-be mérik, azt konvenció rögzíti: a TCG PC Client profil a 0–7. PCR-eket a firmware-nek, az opcionális ROM-oknak (option ROM), a boot loadernek és a Secure Boot állapotának tartja fenn (Trusted Computing Group, 2023), a Linux TPM PCR registry pedig a magasabbakat a GRUB-nak, a kernel parancssorának és a systemd komponenseinek osztja ki (UAPI Group, n.d.).

![Öt lépcső egy sorban: UEFI firmware, shim, GRUB vagy systemd-boot, kernel és initramfs, init. Felül a Secure Boot ellenőrzi minden következő lépcső aláírását. Alul minden lépcsőt TPM PCR-ekbe mérnek (0 és 2, 4 és 7, 4 és 8, 9 vagy 11); a TPM kiterjeszti a PCR-eket, és az értékeiket egy lemezkulcs sealingjéhez és távoli attestationhöz használják](boot-chain.svg)

A mérések kétféleképpen hasznosak:

- **Sealing (lepecsételés).** A TPM úgy tud titkosítani egy titkot, hogy csak akkor fejti vissza, ha a kiválasztott PCR-ek értéke ugyanaz, mint a lepecsételéskor. A **TPM-hez kötött lemeztitkosítás** ezt használja: a Windows BitLockere, Linuxon pedig egy LUKS-kötetnél a `systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7` a PCR-ekhez pecsételve tárolja a lemezkulcsot. Változatlan gépen a lemez jelszó nélkül nyílik meg; ha valaki más betöltőt vagy kernelt indít, vagy egy másik gépbe teszi a lemezt, a PCR-ek eltérnek, és a TPM megtagadja a kiadást. Egy PIN-kód is hozzáadható, így egy ellopott, normálisan induló gép sem elég.
- **Távoli attestation (remote attestation).** A TPM az aktuális PCR-értékeket az ellenőrzőtől kapott friss véletlen számmal együtt aláírja (ez a *quote*), egy olyan kulccsal, amely soha nem hagyja el a TPM-et, és amelyet a gyártója tanúsított. Egy távoli ellenőrző megvizsgálja az aláírást, az eseménynaplót összeveti az ismert jó mérések listájával, és csak ezután ad hozzáférést, például egy vállalati hálózathoz vagy egy felhőbeli munkaterhelés titkaihoz.

A Secure Boot és a measured boot kiegészíti egymást: az egyik megakadályozza, hogy ismeretlen kód fusson, a másik lehetővé teszi, hogy a gép utólag bizonyítsa, pontosan mi futott. A telefonok ugyanezeket az ötleteket szigorúbb formában használják: a bizalmi gyökér a chip boot ROM-jában van, a rendszerpartíciókat pedig blokkról blokkra ellenőrzik; lásd a [14. előadás verified bootját](../14-mobile-wearable-embedded/#verified-boot).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> bootkit, firmware, BIOS, UEFI, EFI rendszerpartíció, shim, GRUB, systemd-boot, initramfs, bizalmi lánc, bizalmi gyökér, digitális aláírás, Secure Boot, db, dbx, MOK, measured boot, hash, TPM, PCR, extend, eseménynapló, sealing, LUKS, távoli attestation, quote</summary>

- **Bootkit:** az indulási folyamatba befészkelő kártevő, amely így az operációs rendszer és annak védelme előtt fut le.
- **Firmware, BIOS, UEFI:** az alaplapon tárolt program, amely elindítja a számítógépet; a BIOS a régi fajta, az UEFI a modern. Az **EFI rendszerpartíció** a lemez egy kis területe, ahol az UEFI a következőként indítandó programot keresi.
- **shim, GRUB, systemd-boot:** kis programok, amelyek betöltik az operációs rendszert: a shim egy aláírt első lépés, a GRUB és a systemd-boot pedig lehetővé teszi a kernel kiválasztását és betöltését.
- **initramfs:** egy apró, ideiglenes fájlrendszer a kernel mellé csomagolva, épp annyival, amennyi a valódi lemez megtalálásához és megnyitásához kell.
- **Bizalmi lánc, bizalmi gyökér:** minden lépés ellenőrzi a következőt, mint egy váltófutásban, ahol minden futó ellenőrzi a következő futó személyazonosságát. Az első futó, akiben ellenőrzés nélkül megbízunk, a bizalmi gyökér.
- **Digitális aláírás:** matematikai pecsét, amelyet csak egy titkos kulcs birtokosa tud előállítani, de bárki ellenőrizheti a hozzá tartozó nyilvános kulccsal.
- **Secure Boot, db, dbx, MOK:** a firmware csak olyan programokat futtat, amelyeken a megbízható aláírók listáján (**db**) szereplő valaki aláírása van, és amelyek nincsenek a tiltólistán (**dbx**). A **MOK** (machine owner key) egy olyan aláíró, akit a számítógép tulajdonosa vett fel.
- **Measured boot, hash:** minden lépés feljegyzi a következő ujjlenyomatát (**hash**), mielőtt elindítaná. A hash egy fájlból kiszámított rövid szám; a fájl egyetlen bitjének megváltoztatása teljesen más hash-t ad.
- **TPM, PCR, extend:** a TPM egy kis biztonsági chip. A **PCR**-jeit nem lehet beállítani, csak **kiterjeszteni** (extend): az új érték a régi értékből és az új ujjlenyomatból keveredik ki. Mint egy tintával írt napló, ahol minden új sor az összes előzőtől függ.
- **Eseménynapló (event log):** a lemért dolgok listája, hogy valaki soronként ellenőrizhesse a naplót.
- **Sealing, LUKS:** egy titok bezárása a TPM-be úgy, hogy csak akkor adja ki, ha az ujjlenyomatok ugyanazok, mint korábban. A LUKS a Linux szabványos formátuma titkosított lemezekhez.
- **Távoli attestation, quote:** a TPM aláírja az aktuális ujjlenyomatait (ez a **quote**), hogy egy másik számítógép ellenőrizhesse, milyen szoftvert indított ez a gép.

</details>

## Megbízható végrehajtási környezetek (TEE)

A Secure Boot és a measured boot az operációs rendszert attól védi, ami előtte jött. Egy **trusted execution environment** (TEE, megbízható végrehajtási környezet) ennél tovább megy: bizonyos kódot és adatot *magától az operációs rendszertől* véd, néha a hypervisortól és a gép tulajdonosától is, úgy, hogy az elkülönítést a processzor kényszeríti ki. A kérdés, amelyre minden megoldás választ ad: ki marad a megbízható számítási bázisban?

![Három oszlop. Arm TrustZone: a normal world alkalmazásai és a rich OS közönséges, a secure world trusted alkalmazásai, a trusted OS és a secure monitor megbízható. Intel SGX: az alkalmazás közönséges, az enclave és a CPU-tok megbízható, az operációs rendszer és a hypervisor nem megbízható. Confidential VM: a vendég alkalmazásai, a vendégkernel és a CPU a biztonsági processzorával megbízható, a hypervisor és a felhőüzemeltető nem megbízható](tee.svg)

- Az **Arm TrustZone** a processzort egy *normal worldre* (normál világ) osztja, ahol a közönséges operációs rendszer (Android, Linux) fut, és egy *secure worldre* (biztonságos világ), amelynek saját kis trusted OS-e (például az OP-TEE) és trusted alkalmazásai vannak. Memória és eszközök rendelhetők a secure worldhöz, és a normal world, még annak kernele sem fér hozzájuk; a világok között a legmagasabb kivételszinten (exception level) futó secure monitor vált (Pinto & Santos, 2019). A telefonok a secure worldöt kulcsokhoz, ujjlenyomat-egyeztetéshez és DRM-hez használják.
- Az **Intel SGX** (Software Guard Extensions, 2015) lehetővé teszi, hogy egy közönséges folyamat **enclave**-et hozzon létre: a címtartományának egy olyan területét, amelynek lapjait a processzor a memóriában titkosítja, és semmilyen más szoftvernek, a kernelt és a hypervisort is beleértve, nem engedi olvasni vagy írni. Az enclave kódját a létrehozásakor megmérik, és attestationnel igazolni tudja az identitását; az operációs rendszer továbbra is kezeli az enclave lapjait, de csak titkosított adatot lát (Costan & Devadas, 2016). A megbízható számítási bázis nagyon kicsi, csak a CPU és az enclave kódja, de a nem megbízható operációs rendszer irányít mindent az enclave körül, az ütemezést és a laphibákat is, amit a kutatók támadások hosszú sorában használtak ki. Az Intel a kliensprocesszorain a 11. és 12. Core generációval elavulttá nyilvánította az SGX-et (Intel Corporation, n.d.); a Xeon szerverprocesszorokon megmaradt.
- A **confidential VM-ek** (bizalmas virtuális gépek) ugyanezt az ötletet egy egész VM-re alkalmazzák. Az **AMD SEV-SNP** (Secure Encrypted Virtualization with Secure Nested Paging, 2021 óta az EPYC processzorokban) és az **Intel TDX** (Trust Domain Extensions, 2023 óta a Xeon processzorokban) esetén a processzor minden VM memóriáját saját kulccsal titkosítja, és védi a sértetlenségét, így a hypervisor, a gazda operációs rendszer és a felhőüzemeltető már nem tudja olvasni vagy észrevétlenül megváltoztatni a vendég memóriáját vagy regisztereit (Advanced Micro Devices, 2020; Intel Corporation, 2020). A hypervisor továbbra is ütemezi a VM-et, és megtagadhatja a futtatását, így a rendelkezésre állás nem védett. Induláskor a processzor biztonsági firmware-e megméri a kezdeti vendég image-et, és a vendég aláírt attestation reportot kérhet, amellyel bizonyíthatja a tulajdonosának, hogy módosítatlanul fut valódi hardveren. A [13. előadás](../13-virtualization-containerization/#memória-két-címfordítás) közönséges VM-jeihez képest a bizalmi viszony megfordul: a vendég már nem bízik a gazdában.
- Az **Apple Secure Enclave** ugyanazon a chipen lévő különálló processzormag saját boot ROM-mal, titkosított memóriával és operációs rendszerrel; a fő processzor megkérheti, hogy használjon egy kulcsot, de magát a kulcsot soha nem kapja meg ([14. előadás](../14-mobile-wearable-embedded/#a-secure-enclave); Apple Inc., 2026).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> trusted execution environment, TrustZone, normal world és secure world, OP-TEE, SGX, enclave, confidential VM, SEV-SNP, TDX, attestation report, Secure Enclave</summary>

- **Trusted execution environment (TEE):** védett szoba a processzoron belül, ahol bizonyos kód fut és titkokat őriz, még a fő operációs rendszertől is elzárva.
- **TrustZone, normal world és secure world:** az Arm módszere egy processzor két világra osztására; a hétköznapi operációs rendszer a normal worldben él, és nem lát be a secure worldbe. Az **OP-TEE** egy kis nyílt forráskódú operációs rendszer a secure world számára.
- **SGX, enclave:** az Intel védett szobái egy közönséges programon belül; egy **enclave** memóriája titkosított, és még a kernel is csak összekevert bájtokat lát.
- **Confidential VM, SEV-SNP, TDX:** egy egész virtuális gép, amelynek memóriáját a processzor titkosítja, így a hardvert üzemeltető felhőcég nem tudja olvasni. A SEV-SNP az AMD változata, a TDX az Intelé.
- **Attestation report:** a processzor aláírt igazolása arról, hogy „pontosan ez a szoftver fut bennem, és én valódi vagyok”.
- **Secure Enclave:** az Apple különálló kis biztonsági processzora, amely őrzi a kulcsokat, és csak kérésre használja őket.

</details>

## Sérülékenységkezelés és frissítések

Minden nagy rendszerben lesznek hibák; az számít, milyen gyorsan javítják ki őket, és milyen gyorsan telepítik a javításokat.

### CVE és CVSS

Egy nyilvánosan ismert sérülékenység **CVE**-azonosítót kap (Common Vulnerabilities and Exposures), például a [2. előadás](../02-quality-and-enterprise-linux/#miért-hazudik-a-verziószám-a-backportolás-a-gyakorlatban) Dirty Pipe hibája a CVE-2022-0847-et, hogy a gyártók, a sérülékenységkeresők (scanner) és a biztonsági közlemények ugyanarra a problémára hivatkozhassanak. Az azonosítókat a CVE Numbering Authority-k (CNA-k) osztják ki: olyan gyártók, mint a Red Hat vagy a Microsoft, és 2024 februárja óta maga a Linux-kernel projekt is, amely minden olyan javításhoz CVE-t rendel, amelynek biztonsági következményei lehetnek, és ezért évente sok százat tesz közzé (Jones, 2024; The kernel development community, n.d.-a). A **CVSS** (Common Vulnerability Scoring System) 0-tól 10-ig pontozza egy sérülékenység súlyosságát olyan jellemzők alapján, mint a támadási vektor (hálózat, szomszédos hálózat, helyi, fizikai), a bonyolultság, a szükséges jogosultságok és felhasználói közreműködés, valamint a bizalmasságra, a sértetlenségre és a rendelkezésre állásra gyakorolt hatás; a 4.0-s verzió 2023-ban jelent meg (FIRST, 2023). Az alappontszám (base score) általánosságban írja le a sérülékenységet; hogy egy adott szervezet számára mennyire sürgős, az attól függ, használják-e ott az érintett komponenst, és elérhető-e, amit csak a tényleges rendszerek elemzése mondhat meg.

### Koordinált nyilvánosságra hozatal

Az a kutató, aki sérülékenységet talál, általában négyszemközt jelenti a gyártónak, és a részleteket csak akkor hozzák nyilvánosságra, amikor már van javítás, vagy egy határidő lejárta után, ami gyakran 90 nap: ez a **koordinált nyilvánosságra hozatal** (coordinated disclosure). A felhasználók így előbb kapnak javítást, mint ahogy a támadók megismernék a részleteket, a határidő pedig megakadályozza, hogy a gyártók figyelmen kívül hagyják a bejelentéseket. Az egyszerre sok gyártót érintő problémáknál, például a széles körben használt könyvtárak vagy a processzorok hibáinál, a koordinációban több tucat cég vesz részt, egy közös embargódátummal. Az a sérülékenység, amelyet a támadók már azelőtt kihasználnak, hogy javítás létezne, a **zero-day**.

### Frissítési ütem

A gyártók ritmusosan adják ki a javításokat: a Microsoft minden hónap második keddjén (*Patch Tuesday*), az Android havi biztonsági közleményekben, a Linux-disztribúciók biztonsági közleményekként (RHSA, USN), amikor egy javítás elkészül, a kernel.org stabil kernelsorozatait pedig nagyjából hetente frissítik. Az enterprise disztribúciók a javításokat **backportolják** az általuk szállított verzióba ([2. előadás](../02-quality-and-enterprise-linux/#miért-hazudik-a-verziószám-a-backportolás-a-gyakorlatban)), így a verziószám önmagában nem árulja el, javítva van-e egy rendszer; a biztonsági közleményeik igen. A frissítések gyors telepítése az egyetlen leghatékonyabb biztonsági intézkedés, és egyben kompromisszum a rendelkezésre állással: egy kernelfrissítés újraindítást (vagy live patchinget) igényel, egy könyvtárfrissítés pedig minden olyan folyamat újraindítását, amely a könyvtárat használja. A megváltoztathatatlan (immutable), image-alapú rendszerek és az A/B update-ek ([2. előadás](../02-quality-and-enterprise-linux/#image-mode-a-teljes-operációs-rendszer-image-ként), [14. előadás](../14-mobile-wearable-embedded/#ab-és-virtual-ab-update-ek)) atomivá és könnyen visszavonhatóvá teszik a frissítéseket, ami a frissítéstől való félelem nagy részét megszünteti.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> CVE, CNA, CVSS, támadási vektor, koordinált nyilvánosságra hozatal, embargó, zero-day, Patch Tuesday, biztonsági közlemény, backport, live patching</summary>

- **CVE:** egy biztonsági rés katalógusszáma, például CVE-2022-0847, hogy mindenki ugyanarról a problémáról beszéljen. A **CNA** olyan szervezet, amely kiadhat ilyen számokat.
- **CVSS, támadási vektor:** egy 0 és 10 közötti pontszám arra, mennyire súlyos egy rés; a **támadási vektor** megmondja, honnan lehet kihasználni: a hálózaton át, ugyanarról a helyi hálózatról, csak bejelentkezett felhasználóként, vagy csak az eszközt kézben tartva.
- **Koordinált nyilvánosságra hozatal, embargó:** a megtaláló először a gyártónak szól, és hallgat, amíg el nem készül a javítás, vagy le nem jár egy határidő; az **embargó** a nyilvánosságra hozatal megállapodott napja.
- **Zero-day:** olyan rés, amelyet a támadók azelőtt használnak ki, hogy a gyártónak javítása lenne: a gyártónak „nulla napja” volt reagálni.
- **Patch Tuesday:** a Microsoft havi frissítési napja.
- **Biztonsági közlemény (security advisory):** egy gyártó értesítése arról, hogy melyik probléma melyik csomagverzióban van javítva.
- **Backport:** egy javítás átmásolása egy új verzióból egy régebbibe, amelyet még támogatnak.
- **Live patching:** a futó kernel javítása a számítógép újraindítása nélkül.

</details>

## Ugyanezek az elvek Linuxon (x86-64)

A bemutatók rootként futnak az előző előadások Ubuntu 24.04-es virtuális gépén (Linux 6.18, gcc 13.3, glibc 2.39, GDB 15.1, Python 3.13). Az előadás mappája végrehajtási jog nélkül is csatolva lehet, ezért minden programot a mappa egy másolatában, a `/root/lab12` könyvtárban fordítottunk és futtattunk; néhány kimenetben ez az útvonal látszik. A programok csak a védekezés működését mutatják: mindegyik tartalmaz egy szándékos hibát, és egy ártalmatlan, `A` karakterekből álló sztringet kap; semmit sem használunk ki. Minden konzollista valódi kimenet; a terminálmeneteket interaktív shellben rögzítettük, így a shell saját üzenetei, például a `Segmentation fault`, úgy jelennek meg, ahogy a felhasználó látja őket.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> konzol, root, gcc, gdb, szkript</summary>

- **Konzol** (terminál): egy ablak, amelybe parancsokat gépelsz. A `$` jellel kezdődő sorokat te írod be; a többi sor a számítógép válasza.
- **Root:** a rendszergazdai fiók, amely az itt bemutatott kernelbeállítások egy részéhez kell.
- **gcc:** a C fordítóprogram; a kapcsolói (például `-fstack-protector-strong`) be- vagy kikapcsolják a védelmeket.
- **gdb:** a hibakereső (debugger): lépésenként futtat egy programot, és megmutatja a memóriáját.
- **Szkript** (`.sh` fájl): egy fájlba mentett parancslista, amelyet a `bash` egymás után lefuttat.

</details>

### Hová kerül minden: az ASLR mérése

Az `aslr.c` kiírja a `main` függvényének, egy globális változónak, egy kis `malloc`-blokknak, egy anonim `mmap`-lapnak, a C könyvtár `puts` függvényének és egy lokális változónak a címét. Két normál futtatás, két futtatás úgy, hogy a `setarch -R` egyetlen parancsra kikapcsolja az ASLR-t, és ugyanannak a programnak két futtatása PIE nélkül fordítva:

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

A két normál futtatás között minden terület elmozdul, de minden cím utolsó három hexadecimális számjegye ugyanaz marad (`0c0`, `010`, `2a0`, `cc0`): csak egy terület kezdőcíme véletlen, lapnyi felbontással, és a `puts` eltolása a C könyvtáron belül rögzített. A `setarch -R` mellett a program minden alkalommal ugyanazt az elrendezést látja, azt, amelyet egy debugger alapértelmezésben mutat (a programnál `0x555555554000`). A nem PIE változat a kódját és az adatait minden futtatáskor a rögzített 0x401000 és 0x404000 címre tölti; csak a kernel és a dinamikus linker által elhelyezett területek (heap, leképezések, könyvtárak, verem) mozognak továbbra is.

A rendszerszintű kapcsoló a `kernel.randomize_va_space`: a 2 mindent véletlenít, az 1 mindent a heap kezdete (`brk`) kivételével, a 0 semmit. 1-es értéknél a heap közvetlenül a program adatai után következik, a `main`-től rögzített távolságra:

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

Mennyire véletlenek a címek? Az `aslr_entropy.py` 2000-szer futtatja a programot, és minden területre megbecsüli a véletlen bitek számát a látott címek tartományából és igazításából:

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

A program, az adatai, a heap és az anonim leképezés megkapja a `vm.mmap_rnd_bits` által beállított teljes 28 bitet: laphatárra igazított címek $2^{28}$ lapon, 1 TiB címtartományon szétszórva. A verem 16 bájtos felbontással véletlenített, és 30 bitet kap. A C könyvtár csak 19 bitet kap: a leképezése alig több 2 MiB-nál, és a kernel az ilyen leképezéseket 2 MiB-os határra teszi, hogy huge page-eket használhassanak ([9. előadás](../09-virtual-memory/#a-tlb-gyorsítótár-a-címfordításokhoz)), ami a 28 bitből 9-be kerül: valódi kompromisszum a sebesség és a biztonság között. PIE nélkül a program kódjának és adatainak egyáltalán nincs entrópiája, és még a heap is csak 18 bitet kap.

### Buffer overflow a veremben: észlelés

Az `overflow.c` a [veremábra](#a-verem-és-a-visszatérési-cím) hibáját tartalmazza: a `greet` az argumentumát `strcpy`-vel egy `char buf[16]` pufferbe másolja. Kétszer fordítjuk le, stack protector nélkül és vele, és egy rövid névvel, valamint 24 és 40 karakterrel futtatjuk:

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

Védelem nélkül mindkét hosszú név összeomlasztja a programot, de csak *azután*, hogy a `greet` kiírta a szöveget: a kár csendben keletkezik, és az összeomlás akkor jön, amikor a sérült értékeket felhasználják. Védelemmel a 40 karakteres nevet a `greet` végén elkapja a rendszer: a `__stack_chk_fail` kiírja az üzenetet, és `SIGABRT` szignállal leállítja a folyamatot (kilépési kód 128 + 6 = 134), még mielőtt a `ret` felhasználná a sérült visszatérési címet. A 24 karakteres név viszont észrevétlenül átjut: a védett változatban 8 bájt kitöltés (padding) van a `buf` és a canary között, és 24 karakter a lezáró nullával együtt pontosan a canary legalsó bájtjáig ér, amely amúgy is nulla. A túlcsordulás megtörtént, de nem változtatta meg a canaryt. A canary a canary sérülését észleli, semmi mást.

### A veremkeret belülről, gdb-vel

Az `overflow.gdb` megállítja a védelem nélküli programot a `strcpy` előtt és után, és kiírja a keretmutatónál lévő két 8 bájtos szót: az elmentett `rbp`-t és a visszatérési címet.

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

A puffer 16 bájttal a keretmutató alatt kezdődik. A másolás előtt a visszatérési cím a `main`-be mutat vissza; utána mindkét szó `0x41` bájtokból, azaz A betűkből áll. A hiba *a* `ret` utasításnál következik be: a `0x4141414141414141` nem kanonikus x86-64-es cím (a felső 16 bitnek a 47. bitet kell ismételnie), ezért a processzor megtagadja az ugrást, és általános védelmi hibát (general protection fault) vált ki, amelyet a Linux `SIGSEGV` szignálként kézbesít. A védett változat ugyanilyen nézete megmutatja a canaryt, 8 bájttal a keretmutató alatt:

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

A másolás előtt a hat szó: a `buf` (két szó), a kitöltés, a canary `0xfd3472a03d281d00` (véletlen, nulla legalsó bájttal), az elmentett `rbp` és a visszatérési cím. A másolás után a canary, az elmentett `rbp` és a visszatérési cím legalsó bájtja (most `...5200`, a sztring lezáró nullája) mind felülíródott, pontosan úgy, ahogy az ábrán. A `leave` és a `ret` előtti ellenőrzés észreveszi a megváltozott canaryt, így egyik sérült értéket sem használja fel semmi.

### A FORTIFY_SOURCE megállítja a másolást

A `fortify.c` ugyanazt az ellenőrizetlen `strcpy`-t tartalmazza, közvetlenül a `main`-ben. Az Ubuntu GCC-je optimalizáláskor alapértelmezésben definiálja a `_FORTIFY_SOURCE` makrót; a `-U_FORTIFY_SOURCE` kikapcsolja:

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

A fordító tudta, hogy a `buf` 16 bájtos, és a `strcpy`-t `__strcpy_chk(buf, src, 16)`-ra cserélte (a `printf`-et pedig az ellenőrző változatára). A megerősített program *még a másolás előtt* leáll: a keret egyetlen bájtja sem változik, és a `copied:` sosem jelenik meg. Megerősítés nélkül a másolás megtörténik, a program a sérült keretéből tovább is kiírja a túl hosszú sztringet, és csak a `main` végén lévő canary-ellenőrzés állítja meg. A két védekezés kiegészíti egymást: a FORTIFY_SOURCE a másolásnál fogja meg a túlcsordulást, ha a méret ismert; a canary a visszatérésnél, ha nem.

### Heaphibák: glibc és AddressSanitizer

Az `uaf.c` felszabadít egy 32 bájtos blokkot, majd vagy kiolvassa egy azonos méretű új `malloc` után, vagy másodszor is felszabadítja:

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

Az egyszerű változat megmutatja, miért veszélyes a use after free: az új `q` blokk *maga* a felszabadított `p` blokk, és az elavult `p` mutatón át olvasva az új tulajdonos adatának („other data”) első betűjét kapjuk. A program hiba nélkül fut tovább. A glibc memóriafoglalója a szálankénti gyorsítótárának (*tcache*) egy konzisztencia-ellenőrzésével elkapja az egyszerű double free-t, és leállítja a programot, de az ilyen ellenőrzések csak bizonyos mintákat fednek le. Az ASan-os változat a use after free-t magánál az olvasásnál (18. sor) jelenti, és megmondja, hol foglalták (12. sor) és hol szabadították fel (14. sor) a blokkot: ezért talál a sanitizerekkel végzett tesztelés és az alattuk futó fuzzing olyan memóriahibákat, amelyek különben, ha egyáltalán, ritka és rejtélyes memóriasérülésként bukkannának fel.

### Milyen védelmei vannak egy programnak?

A `hardening.sh` az ismert `checksec` eszköz kicsinyített változata: minden ELF-fájlt beolvas a `readelf`-fel, és jelenti a PIE-t (`DYN` típusú futtatható állomány `PIE` jelzővel), az NX-et (nincs `E` a `GNU_STACK`-ben), a RELRO-t (`GNU_RELRO` szegmens, teljes `BIND_NOW`-val), a canaryt (a `__stack_chk_fail` importja), a megerősített függvények számát (`__*_chk` nevű importok) és a CET-jelöléseket a GNU property note-ban. Először ennek a fordítónak az alapbeállításai, majd két rendszerprogram, a bemutatóprogramok, végül egy olyan program, amelyben minden védelem ki van kapcsolva:

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

Az Ubuntu GCC-je kérés nélkül bekapcsolja a PIE-t, az erős stack protectort, a FORTIFY_SOURCE 3-as szintjét, a stack clash elleni védelmet és a CET-jelöléseket, a linkere pedig alapértelmezésben teljes RELRO-t használ, így egy közönséges `gcc -O2` már megerősített programot készít, akárcsak a disztribúció saját `ls`-e és `passwd`-je. Az `overflow-plain` programból csak a szándékosan kikapcsolt canary hiányzik. A `weak` program megmutatja, mit vesz el az egyes kapcsolók kikapcsolása: rögzített címre töltődik, végrehajtható vermet kér (`RWE`), és írhatóan hagyja a GOT-ját. A CET-jelölések azt jelentik, hogy a program *kompatibilis* az IBT-vel és a shadow stackkel; hogy ki is kényszeríti-e őket a rendszer, az a processzortól és a kerneltől függ. Ennek a virtuális gépnek a processzora egyik funkciót sem jelenti a vendégnek, és a kernelt is nélkülük fordították, így itt a jelöléseknek nincs hatásuk.

### Seccomp: lemondás rendszerhívásokról

A `seccomp.c` mindkét módot bemutatja. Strict módban még `write`-olhat, de a következő rendszerhívása, az ártalmatlan `getpid`, megöli. Filter módban egy BPF-szűrőt telepít, amely a `mkdir`-re `EPERM`-mel válaszol, a `getpid`-et engedélyezi, a `socket`-nél pedig megöli a folyamatot:

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

Strict módban a folyamatot `SIGKILL` ölte meg (kilépési kód 128 + 9 = 137). Filter módban a `/proc/self/status` mutatja a mód változását 0-ról 2-re (filter); a tiltott `mkdir` egyszerűen sikertelen volt, mintha a kernel utasította volna el, és a program folytatódott; a `socket` `SIGSYS` szignállal, „Bad system call” üzenettel ölte meg (128 + 31 = 159). A kernel audit naplója mindkét leállítást rögzíti a rendszerhívások számával, x86-64-en ez 39 (`getpid`) és 41 (`socket`), valamint a `0x0` (a szál megölése) és `0x80000000` (a folyamat megölése) akciókóddal. A folyamat rootként futott, mégis végleg elvesztette ezeket a rendszerhívásokat: a seccomp a folyamatot korlátozza, nem a felhasználót.

### A kernel elrejti a címeit

A `kernel-hiding.sh` két kernelszimbólumot keres meg a `/proc/kallsyms` fájlban: rootként, a `nobody` felhasználóként, rootként a `CAP_SYSLOG` capability nélkül (a `capsh` segítségével, [11. előadás](../11-access-control/#a-root-és-a-capabilityk)), valamint 2-re emelt `kernel.kptr_restrict` mellett:

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

A szimbólumnevek nyilvánosak (a kernel forráskódjából származnak), de a címüket csak egy `CAP_SYSLOG` capabilityvel rendelkező folyamat látja; a capability számít, nem a 0-s UID, ahogy a nélküle futó root shell mutatja. A `kptr_restrict = 2` mindenki elől elrejti őket. A kernelnaplót, amely szintén tartalmaz címeket, a `dmesg_restrict` zárja el a közönséges felhasználók elől.

Egy részlet őszintén megmutat egy korlátot: a kernel kódja a `0xffffffff81000000` címen kezdődik, ami egy x86-64-es kernel alapértelmezett linkelési címe, nem pedig véletlenített cím. A kernel KASLR-rel készült (`CONFIG_RANDOMIZE_BASE=y`), de x86-on a véletlen elhelyezést a kernel kicsomagoló kódja (decompression stub) választja ki induláskor, ennek a virtuális gépnek a hypervisora (a Firecracker, lásd [alább](#hogyan-indult-ez-a-gép)) viszont közvetlenül a kicsomagolt kernelt tölti be, így ez a lépés sosem fut le. Egy nem véletlenített kernel címének elrejtése semmit sem véd; a KASLR csak annyit ér, amennyit az azt alkalmazó rendszerindítási út.

### Lockdown: a kernel védelme a root ellen

A `lockdown.sh` megmutatja a lockdown módot, rootként megpróbál kiolvasni egy ütemezőfájlt a debugfs-ből, és megpróbálja kikapcsolni a lockdownt:

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

Ezt a kernelt úgy konfigurálták, hogy `integrity` módban induljon (a rendszerindítási napló szerint „Kernel is locked down from Kernel configuration”). A root csatolhatja a debugfs-t, de egy olyan fájl olvasását, amelyen át az ütemező átkonfigurálható, a kernel megtagadja, és naplózza az okát. A root a módot csökkenteni sem tudja; erre csak egy másik konfigurációval végzett újraindítás képes. Az `integrity` mód többi korlátozott művelete, például az aláíratlan modulok betöltése vagy a `/dev/mem` írása, itt elérhető sem lenne: ennek a kernelnek nincs modultámogatása (`nomodule`), és nincs `/dev/mem` eszköze.

### Mely CPU-hibákról tud a kernel?

A `/sys/devices/system/cpu/vulnerabilities/` könyvtár minden fájlja egy-egy tranziens végrehajtási hibát nevez meg, a tartalma pedig azt mondja meg, hogy ez a CPU érintett-e, és hogyan kezeli a kernel:

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

Ez a virtuális CPU egy új processzorgenerációhoz tartozik: a Meltdown és a pufferekből mintavételező (buffer-sampling) hibák többsége „Not affected” (nem érintett), így nincs szükség KPTI-re. A Spectre-t nem lehet teljesen kitervezni a hardverből, ezért a változatainál aktív védekezés látszik: spekulációs korlátok (barrier) a kernel felhasználói másolórutinjaiban és a kernelbe lépésnél (`swapgs`), valamint a felhasználói térből érkező mutatók tisztítása (maszkolása) (1. változat); a hardver enhanced IBRS-e az indirekt elágazásokra, az elágazásbecslő törlése (IBPB), amikor olyan folyamatra vált a rendszer, amely ezt kérte (`conditional`), és egy rövid szoftveres utasítássorozat egy visszamaradt visszatérésbecslési problémára (`PBRSB-eIBRS`) (2. változat); végül a speculative store bypass kikapcsolása, csak azoknál a programoknál, amelyek `prctl`-lel kérik. A `spectre_v2` sor egy nyitott problémát is beismer, a branch history injectiont (BHI), amely ellen ez a kernel nem kapcsol be védekezést. A `/proc/cpuinfo` jelzői a virtuális CPU által kínált vezérlőket sorolják fel (az `md_clear` a mikrokód pufferürítő támogatása az MDS ellen, az `arch_capabilities` az a regiszter, amelyen át a CPU közli a kernellel, mely hibák nincsenek meg benne); mindegyik kétszer szerepel, mert a gépnek két virtuális CPU-ja van.

### Hogyan indult ez a gép?

A `boot.sh` összegyűjti, amit a gép a saját rendszerindításáról el tud mondani:

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

Ebből a gépből a fent leírt bizalmi lánc szinte teljesen hiányzik, és a kimenet ezt meg is mondja. Ez egy Firecracker microVM (az ACPI-táblák a `FIRECK`-től származnak): nincs UEFI firmware (a `/sys/firmware/efi` hiányzik), nincs boot loader, nincs Secure Boot és nincs TPM. A hypervisor a kernelt és egy initramfs-t (`RAMDISK`) közvetlenül a memóriába tölti, és a kernelre ugrik, amely 1-es folyamatként a szolgáltató saját `/process_api` programját indítja el a systemd helyett, így a `systemd-analyze` nem működhet. A kernel viszont korán alkalmazza a saját védelmeit: az NX az első mikroszekundumtól aktív, a lockdown és a biztonsági modulok (Landlock, SELinux, BPF) bármely folyamat előtt elindulnak, és a csak olvasható adatok már az `init` futása előtt írásvédetté válnak. Ennek a rendszerindításnak a bizalma teljes egészében a hypervisoron és a felhőüzemeltetőn nyugszik: pontosan ez az a helyzet, amelyet a confidential VM-ek meg akarnak változtatni. Egy valódi PC-t a [7. laborfeladat](#laborfeladatok) vizsgál meg.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> setarch, sysctl, objdump, readelf, ELF programfejléc, GOT, tcache, SIGABRT, SIGSYS, kilépési kód, audit napló, kallsyms, CAP_SYSLOG, capsh, debugfs, securityfs, speculative store bypass, prctl, enhanced IBRS, BHI, /proc/cpuinfo jelzők, Firecracker, microVM, ACPI</summary>

- **setarch -R:** egyetlen programot a címvéletlenítés kikapcsolásával futtat. **sysctl:** kernelbeállításokat olvas és módosít.
- **objdump, readelf:** olyan eszközök, amelyek egy programfájl belsejét mutatják meg: a gépi kódját, valamint a fejléceit és tábláit.
- **ELF programfejléc (program header):** egy sor a programfájlban, amely megmondja a kernelnek, hogyan töltse be a program egy részét, és milyen jogosultságokkal (R, W, E).
- **tcache:** a glibc kis, szálankénti gyorsítótára a nemrég felszabadított memóriablokkokból, amelyeket elsőként ad ki újra.
- **SIGABRT, SIGSYS, kilépési kód:** programot leállító szignálok: SIGABRT, ha a program önmagát állítja le, SIGSYS egy tiltott rendszerhívásnál. A shell a $s$ szignállal megölt programot $128 + s$ kilépési kóddal jelenti.
- **Audit napló:** a kernel biztonsági naplója, itt a kernelnapló része.
- **kallsyms:** a kernel listája a saját függvényeiről és változóiról, a címükkel együtt. **CAP_SYSLOG:** az a különleges jog, amely ezeknek a címeknek és a kernelnaplónak a megtekintéséhez kell. **capsh:** eszköz, amellyel kevesebb capabilityvel lehet shellt indítani.
- **debugfs, securityfs:** különleges fájlrendszerek, amelyeken át a kernel fájlok formájában kínál hibakereső kapcsolókat és biztonsági beállításokat.
- **Speculative store bypass, prctl:** egy Spectre-változat, amelyben a processzor kiolvas egy memóriaterületet, mielőtt tudná, hogy egy korábbi írás megváltoztatja. A **prctl** az a rendszerhívás, amellyel egy program különleges bánásmódot kér a kerneltől, itt azt, hogy „kapcsold ki nekem ezt a spekulációt”.
- **Enhanced IBRS, BHI:** az enhanced IBRS egy egyszer bekapcsolt processzorüzemmód, amely megakadályozza, hogy a kevésbé privilegizált kód befolyásolja a kernel elágazási tippjeit. A **BHI** (branch history injection) egy későbbi trükk, amely a legutóbbi elágazások történetén keresztül kerüli meg ezt.
- **/proc/cpuinfo jelzők (flags):** rövid szavak, amelyek felsorolják a processzor által kínált funkciókat, például `ibrs` vagy `md_clear`.
- **Firecracker, microVM:** nagyon kicsi, gyorsan induló virtuálisgép-program, amelyet felhőszolgáltatások használnak; a microVM-nek csak az a néhány eszköze van, amelyre valóban szüksége van.
- **ACPI:** szabványos táblák, amelyekkel a firmware (vagy egy hypervisor) leírja a gépet az operációs rendszernek.

</details>

## Laborfeladatok

1. **ASLR a saját folyamatodban.** Futtasd az `aslr` programot a saját linuxos gépeden, és hasonlítsd össze az eredményt ezzel az előadással. Ezután futtasd kétszer a `cat /proc/self/maps` parancsot, és keresd meg a C könyvtár kezdőcímét: 2 MiB (`0x200000`) többszöröse-e a te kerneleden? Futtasd az `aslr_entropy.py` szkriptet 32 bites változatokkal (`gcc -m32`, ha a `gcc-multilib` telepítve van), és hasonlítsd össze az entrópiát.
2. **Stack canaryk.** Fordítsd le az `overflow.c` programot `-fstack-protector-strong` kapcsolóval, és keresd meg a legrövidebb argumentumot, amely kiváltja a `*** stack smashing detected ***` üzenetet. Magyarázd meg a számot a gdb által mutatott keretelrendezésből. Ezután fordítsd `-O2`-vel, és ismételd meg: mi változik az elrendezésben, és miért?
3. **FORTIFY_SOURCE.** Módosítsd a `fortify.c` programot úgy, hogy a puffert `malloc(16)`-tal foglalja, és `strcpy`-vel másoljon bele. Fordítsd `-O2` és `-D_FORTIFY_SOURCE=2` kapcsolóval, majd `=3`-mal (és ellenőrizd az `objdump`-pal, hogy meghívódik-e a `__strcpy_chk`). Magyarázd meg a 2-es és a 3-as szint közötti különbséget.
4. **Sanitizerek.** Írj egy programot egy egybájtos heap overflow-val (`char *p = malloc(10); p[10] = 0;`) és egyet egy tömbindex okozta verembeli túlcsordulással. Futtasd őket `-fsanitize=address` kapcsolóval és anélkül. Ezután próbáld ki a `-fsanitize=undefined` kapcsolót egy előjeles egészszám-túlcsordulásra. Mely hibák maradtak észrevétlenek sanitizerek nélkül?
5. **A saját rendszered megerősítése.** Futtasd a `hardening.sh` szkriptet a `/usr/bin` összes programjára (`bash hardening.sh /usr/bin/* 2>/dev/null | grep -v "canary=yes"`). Mely programokból hiányzik a canary, és miért lehet ez ártalmatlan (tipp: nézd meg a méretüket és a nyelvüket)? Ha a disztribúciód csomagolja a `checksec`-et, hasonlítsd össze a kimenetével.
6. **Seccomp egy valódi szolgáltatásnál.** Nézz meg egy systemd szolgáltatást a gépeden a `systemctl show -p SystemCallFilter,NoNewPrivileges,CapabilityBoundingSet systemd-resolved` paranccsal (vagy egy másik szolgáltatást), és a `Seccomp:` sorát a `/proc/PID/status` fájlban. Ezután bővítsd a `seccomp.c` programot úgy, hogy az `openat` hívásra `EPERM`-et adjon vissza minden fájlnál egy engedélyezett kivételével (tipp: a seccomp nem tud sztringeket összehasonlítani; miért nem, és mit használnál helyette? Nézz utána a Landlocknak).
7. **Egy valódi PC rendszerindítási lánca** (kimeneteket itt nem adunk meg, mert az előadás virtuális gépén nincs firmware, Secure Boot és TPM). Egy UEFI-vel indított linuxos PC-n vagy laptopon futtasd a `mokutil --sb-state`, az `ls /sys/firmware/efi`, a `bootctl status` (systemd-boot) vagy az `efibootmgr -v`, valamint a `sudo dmesg | grep -i -E "secure ?boot|lockdown|tpm"` parancsot. Ha van TPM (`ls /dev/tpm*`), telepítsd a `tpm2-tools` csomagot, és futtasd a `sudo tpm2_pcrread sha256:0,2,4,7,8,9,11` parancsot. Indítsd újra a gépet, olvasd ki újra a PCR-eket, és magyarázd meg, mely értékek maradtak ugyanazok, és miért. Ezután a rendszerindító menüben egyszer módosítsd egy GRUB-menübejegyzés kernel-parancssorát (nyomd meg az `e` billentyűt), indítsd el a gépet, és olvasd ki újra a PCR 8-at.
8. **TPM-hez kötött titkosítás** (virtuális TPM-mel rendelkező teszt-VM-en, például QEMU-ban `swtpm`-mel, vagy bekapcsolt TPM-mel rendelkező VirtualBox/Hyper-V VM-en; kimeneteket nem adunk meg). Hozz létre egy LUKS-kötetet egy tartalék virtuális lemezen, regisztráld a TPM-et a `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/vdb` paranccsal, és nyisd meg a `sudo /usr/lib/systemd/systemd-cryptsetup attach test /dev/vdb - tpm2-device=auto` paranccsal. Ezután kapcsold ki a Secure Bootot a VM firmware-beállításaiban, és próbáld újra. Mi történik, és hogyan állítanád helyre az adatokat?

## Ellenőrző kérdések

1. Nevezd meg a CIA-hármas három biztonsági célját, és mindegyik ellen adj meg egy operációs rendszer elleni támadást.
2. Mi egy linuxos szerver megbízható számítási bázisa? Miért kell kicsinek lennie, és melyik része a legnagyobb?
3. Írj le egy tipikus támadási láncot egy távoli kéréstől a tartós root-hozzáférésig. Ennek az előadásnak mely védekezési módjai hatnak az egyes lépéseknél?
4. Egy veremkeret rajzával magyarázd el, hogyan változtathatja meg egy verembeli buffer overflow egy program vezérlési folyamatát. Miért a visszatérési címet éri el a túlcsordulás, és nem a puffer alatti, más keretekben lévő változókat?
5. Különböztesd meg a térbeli és az időbeli memóriabiztonságot, és sorold be a verembeli túlcsordulást, a heap overflow-t, a use after free-t és a double free-t.
6. Miért különösen veszélyes a use after free a C++-ban írt programokban? Mit mutatott az `uaf` bemutató a felszabadított memória újrafelhasználásáról?
7. Hogyan vezethet egy egészszám-túlcsordulás heap overflow-hoz? Adj egy rövid kódpéldát.
8. Mit tesz lehetővé egy format string hiba a támadónak, és hogyan reagálnak rá a fordítók és a FORTIFY_SOURCE?
9. Hogyan működik a stack canary? Miért nulla a legalsó bájtja? A bemutatóban miért nem váltotta ki a canaryt egy 24 karakteres argumentum, bár túlcsordult a pufferen?
10. Miért nem vetett véget az NX a memóriasérüléses támadásoknak? Két-három mondatban magyarázd el a kód-újrafelhasználást és a return-oriented programminget.
11. Mi az ASLR entrópiája? A mért értékek alapján átlagosan hány próbálkozás kellene a C könyvtár kezdőcímének vak kitalálásához? Miért gyakran az információszivárgás a valódi akadály?
12. Miért van szüksége az ASLR-nek a PIE-re? Mit mutatott a bemutató egy nem PIE programnál?
13. Mit véd a részleges és a teljes RELRO, és mi köze ehhez a `BIND_NOW`-nak?
14. Hasonlítsd össze a FORTIFY_SOURCE-ot és a stack canaryt a `fortify` bemutató alapján: mikor lép működésbe egyik és másik, és mit nem tud észlelni egyik és másik?
15. Magyarázd el az Intel CET shadow stackjét és indirect branch trackingjét, valamint az Arm PAC-ját és BTI-ját. Mely támadásokat állítják meg, és mit kell tennie a fordítónak, a könyvtáraknak és a kernelnek, hogy működjenek?
16. Nevezz meg négy olyan intézkedést, amellyel a Linux-kernel védi magát (a felhasználói térbeli támadóktól és a roottól), és egyet magyarázz el részletesen. Miért volt a bemutatógép kernele az alapértelmezett címén a `CONFIG_RANDOMIZE_BASE=y` ellenére?
17. Mi a seccomp? Magyarázd el a strict és a filter módot a bemutató eredményei alapján, és azt, hogy miért kötelező a `no_new_privs` a nem privilegizált folyamatoknak.
18. Írd le egy UEFI-s linuxos PC rendszerindítási láncát. Mit tesz a Secure Boot és mit a measured boot, és miért hasznos mindkettő?
19. Hogyan működik egy TPM PCR? Miért nem tudja a kernel után futó kártevő „megjavítani” egy PCR értékét, és hogyan használják ezt a lemeztitkosítás rendszerindítási lánchoz kötésére?
20. Hasonlítsd össze az Arm TrustZone-t, az Intel SGX-et és a confidential VM-eket (SEV-SNP, TDX): mit védenek kitől, és mi marad a megbízható számítási bázisban?
21. Mi a CVE és a CVSS? Miért nem jelenti feltétlenül egy magas CVSS-alappontszám, hogy egy adott szervert kell elsőként javítani? Miért nem szabad egy enterprise kernel verziószáma alapján eldönteni, hogy sérülékeny-e?
22. Mi a side channel? Kód nélkül magyarázd el, hogyan árulhatja el a gyorsítótár-találat és -hiány közötti különbség, hogy egy másik program mely memóriaterületekhez nyúlt.
23. Miért tette olvashatóvá a Meltdown a kernelt felhasználói módból az érintett processzorokon, és hogyan akadályozza ezt meg a KPTI? Mibe kerül a KPTI, és miért csökkenti ezt a költséget a PCID? Mit jelentett a `/sys/devices/system/cpu/vulnerabilities` az előadás gépéről?

<details>
<summary><strong>Megoldókulcs (oktatóknak)</strong></summary>

1. Bizalmasság: egy másik felhasználó fájljainak kiolvasása egy hibán keresztül, vagy egy szerver titkos kulcsáé egy folyamat memóriájából. Sértetlenség: egy rendszerprogram vagy a kernel lecserélése (rootkit, bootkit), egy adatbázis módosítása. Rendelkezésre állás: a kernel összeomlasztása egy hibás formátumú csomaggal, egy fork bomba, vagy a lemez vagy a memória kimerítése.
2. A kernel, az őt elindító firmware és boot loader, a CPU és a mikrokódja, valamint a biztonsági döntéseket hozó privilegizált folyamatok (login, sshd, sudo, setuid programok, systemd). Bármely hibája semmissé teheti a szabályrendszert, a kis TCB-t pedig könnyebb ellenőrizni (a mechanizmus egyszerűsége). A legnagyobb része a kernel a drivereivel.
3. (1) Távoli kódfuttatás egy hálózati szolgáltatás hibáján keresztül: ezt a stack canary, az NX, az ASLR/PIE, a RELRO, a FORTIFY_SOURCE és a CFI nehezíti; a kárt az korlátozza, hogy a szolgáltatás saját felhasználóként, kevés capabilityvel, seccomppal és MAC-domainben fut. (2) Jogosultság-kiterjesztés egy kernel- vagy setuid-hibán keresztül: a kernel megerősítése (KASLR, SMEP/SMAP, hardened usercopy), az elérhető kernelkódot csökkentő seccomp, kevesebb setuid program. (3) Tartós megtelepedés: lockdown (nincs aláíratlan modul), Secure Boot és measured boot, csak olvasható vagy image-alapú rendszerek. A frissítések minden lépésnél bezárják a hibákat.
4. A keret a magasabb címektől az alacsonyabbak felé haladva a visszatérési címet, az elmentett keretmutatót és a lokális változókat, köztük a puffert tartalmazza. A másolás az alacsony címektől a magasak felé tölti a puffert, így a többletbájtok a fölötte lévő elmentett regisztereket és a visszatérési címet írják felül; a `ret` ezután a bemenetből vett címre ugrik. Az alacsonyabb címek a később hívott függvények keretéhez tartoznak, amelyek ekkor nem élnek, így a másolás eltávolodik tőlük.
5. Térbeli: a hozzáférések az objektum határain belül maradnak (a verembeli és a heapbeli túlcsordulás ezt sérti). Időbeli: a hozzáférések csak az objektum élettartama alatt történnek (a use after free és a double free ezt sérti).
6. A felszabadított memóriát a foglaló gyorsan újrahasznosítja egy másik objektum számára; az elavult mutató ezután az új objektumot olvassa vagy írja. A C++ objektumok a virtuálisfüggvény-táblájukra mutató pointereket tartalmaznak, így az a támadó, aki az új objektum adatait irányítja, az elavult mutatón át végzett következő virtuális hívás célját is irányítja. A bemutatóban a következő `malloc(32)` pontosan a felszabadított blokkot adta vissza, és az elavult mutató hiba nélkül kiolvasta az új tulajdonos adatát.
7. `p = malloc(n * sizeof(struct item)); for (i = 0; i < n; i++) p[i] = ...;` Ha az `n * sizeof` túllépi az egész típus tartományát, a szorzat kis értékre fordul körbe, kis blokk foglalódik, és a ciklus `n` elemet ír, a blokk végén túl.
8. Ha a bemenet a formátumsztring, a `%x`/`%p` értékeket olvas ki a veremből (információszivárgás, például a canaryé vagy az ASLR-t legyőző címeké), a `%n` pedig memóriát ír. A fordítók a `-Wformat -Wformat-security` kapcsolókkal figyelmeztetnek; a megerősített `printf` elutasítja a `%n`-t az írható memóriában lévő formátumsztringekben.
9. A függvénybe lépéskor egy véletlen érték kerül a lokális pufferek és az elmentett regiszterek közé, és visszatérés előtt összevetik a referenciapéldánnyal; eltérés esetén a folyamat leáll. A nulla bájt megakadályozza, hogy a sztringfüggvények kiolvassák vagy átmásolják a canaryt, és azt eredményezi, hogy egy sztringes túlcsordulás nullát ír oda. A bemutatóban 8 bájt kitöltés volt a `buf` és a canary között; 24 karakter a lezáró nullával pontosan a canary legalsó bájtjáig ért, amely már eleve nulla, így a canary nem változott.
10. Az NX megakadályozza a bejuttatott kód végrehajtását, de azt nem, hogy a vezérlést már létező kódra irányítsák. A kód-újrafelhasználás könyvtári függvényekre ugrik (return-to-libc), vagy rövid, `ret`-tel végződő meglévő utasítássorozatokat („gadgeteket”) fűz össze, amelyeket egy-egy felülírt visszatérési cím indít el a veremben, így a verem tartalma programmá válik (ROP); Shacham (2007) megmutatta, hogy ez már a C könyvtár kódjával is Turing-teljes.
11. Egy terület címében lévő véletlen bitek száma; $n$ bitnél egy vak tipp $2^{-n}$ valószínűséggel sikeres. A C könyvtár 19 bitjénél ez átlagosan nagyjából $2^{18}$, azaz körülbelül 262 000 próbálkozás, ha az elrendezés a próbálkozások között ugyanaz marad (forkoló szerver, a rossz tippek kihúzhatók), és $2^{19}$, azaz körülbelül 524 000, ha a célpontot minden összeomlás után újra véletlenítik; minden sikertelen próbálkozás általában összeomlasztja a célpontot, ami feltűnő. Mivel csak a területek kezdőcíme véletlen, egyetlen kiszivárgott mutató felfedi az egész területet; a támadók ezért találgatás helyett szivárgást keresnek, és az ASLR-rel egy hibából két hiba követelménye lesz.
12. Egy nem PIE program rögzített címre van linkelve, és nem mozgatható, így a kódja és az adatai ismert címeket adnak a kód-újrafelhasználáshoz. A bemutatóban a nem PIE program `main` függvénye és globális változója minden futtatáskor a 0x4010b0 és a 0x404030 címen volt (0 bit), míg a PIE változat 28 bitet kapott.
13. A dinamikus linker tábláit védik a felülírástól, mindenekelőtt a GOT-ot, egy függvénymutató-táblát. A részleges RELRO néhány szekciót tesz csak olvashatóvá; a teljes RELRO a függvények GOT-bejegyzéseit is csak olvashatóvá teszi, ehhez pedig minden szimbólumot induláskor kell feloldani (`BIND_NOW`, `-z now`), nem lustán, az első hívásnál.
14. A FORTIFY_SOURCE a másolást még a végrehajtása előtt veti össze a cél méretével, így egyetlen bájt sem íródik felül (a `fortify` „buffer overflow detected” üzenettel, kiírás nélkül állt le); csak akkor működik, ha a fordító ismeri a méretet. A canary a felülírást utólag, a függvény visszatérésekor észleli (a `fortify-off` előbb kiírta a sérült sztringet); nem veszi észre azokat a túlcsordulásokat, amelyek nem érik el vagy nem változtatják meg a canaryt, a heap overflow-t és a nem lineáris írásokat.
15. Shadow stack: a `CALL` a visszatérési címet egy védett verembe is elmenti, a `RET` összeveti őket, és eltérés esetén kivételt vált ki, így megállítja a felülírt visszatérési címeket (ROP). IBT: az indirekt hívásoknak és ugrásoknak `endbr64` utasításra kell érkezniük, így megállítja a függvények közepébe történő ugrásokat (JOP, hívásorientált gadgetek). A PAC titkos kulccsal és környezettel aláírja a mutatókat (a visszatérési címeket), és használat előtt ellenőrzi őket; a BTI az IBT Arm-megfelelője. A fordítónak elő kell állítania az utasításokat, és meg kell jelölnie a binárist, a folyamatba betöltött minden könyvtárnak kompatibilisnek kell lennie (különben a kikényszerítés kikapcsol a folyamatra), a kernelnek pedig be kell kapcsolnia a funkciót, és kezelnie kell a shadow stack memóriáját.
16. KASLR rejtett címekkel (`kptr_restrict`, `dmesg_restrict`), SMEP/SMAP, csak olvasható kernelkód és -adatok (STRICT_KERNEL_RWX), stack protector és hardened usercopy, lockdown, aláírt modulok, az elérhető kódot csökkentő seccomp. Példa, az SMAP: a kernel a kifejezett másolórutinokon kívül nem fér hozzá a felhasználói memóriához, így egy sérült kernelmutatót nem lehet a támadó által előkészített felhasználói adatra irányítani. x86-on a KASLR-t a tömörített kernel kicsomagoló kódja alkalmazza; a Firecracker hypervisor közvetlenül a kicsomagolt kernelt tölti be, így a véletlenítés sosem futott le.
17. Olyan mechanizmus, amellyel egy folyamat visszavonhatatlanul korlátozza a saját rendszerhívásait. A strict mód csak a read, write, exit és sigreturn hívást engedi: a bemutató `getpid` hívását SIGKILL követte (137-es kód). A filter mód minden hívásnál lefuttat egy BPF-programot: a `mkdir` EPERM-et adott vissza, a `getpid` engedélyezett volt, a `socket` SIGSYS szignállal (159) megölte a folyamatot, és ezt az audit a rendszerhívások számával naplózta. `no_new_privs` nélkül egy nem privilegizált folyamat telepíthetne egy szűrőt, majd elindíthatna egy setuid programot, amely root jogaival, de egy általa nem várt szűrő alatt futna, például olyan alatt, amely egy biztonsági szempontból fontos hívást csendben sikertelenné tesz.
18. A firmware (UEFI) inicializálja a hardvert, és betölti a shimet az EFI rendszerpartícióról; a shim betölti a GRUB-ot vagy a systemd-boot-ot; a boot loader betölti a kernelt és az initramfs-t; a kernel elindítja az initramfs-beli init-et, amely csatolja a gyökér-fájlrendszert, és PID 1-ként elindítja a systemd-t. A Secure Boot minden következő lépcső aláírását ellenőrzi, és megtagadja az aláíratlan vagy visszavont kódot (megelőzés). A measured boot minden lépcső hash-ét TPM PCR-ekbe méri, és eseménynaplót vezet (bizonyíték), ami lehetővé teszi titkok egy ismert állapothoz pecsételését és az állapot bizonyítását mások felé (attestation), és az aláírt, de nem várt komponenseket is kimutatja.
19. Egy PCR-t csak kiterjeszteni lehet: új érték = hash(régi érték ‖ mérés); reset után nulláról indul. Mivel a hash nem fordítható meg, semmilyen szoftver nem tud utólag egy választott értéket előállítani, és a végső érték az összes mérést tükrözi, sorrendben. A kernel után futó szoftver kiterjesztheti a PCR-eket, de nem állíthatja vissza vagy be őket. A lemeztitkosítás a lemezkulcsot kiválasztott PCR-ekhez pecsételi (például a PCR 7-hez, a Secure Boot állapotához); a TPM csak akkor adja ki, ha a PCR-ek egyeznek, így egy módosított rendszerindítási lánc vagy egy másik gép semmit sem kap.
20. TrustZone: a secure world (trusted OS és alkalmazások, secure monitor) védett a normal worldtől, annak kernelét is beleértve; a TCB a CPU, a secure world szoftvere és a rendszerindítási lánc. SGX: az enclave védett az operációs rendszertől, a hypervisortól és más folyamatoktól; a TCB csak a CPU és az enclave kódja, de a nem megbízható operációs rendszer irányítja a környezetét (lapozás, ütemezés), és az SGX a kliens-CPU-kon elavult. Confidential VM-ek: egy egész VM védett (titkosítás és sértetlenség) a hypervisortól, a gazdától és az üzemeltetőtől; a TCB a CPU a biztonsági processzorával/firmware-ével és maga a vendég; a rendelkezésre állás nem védett; az attestation a kezdeti állapotot bizonyítja.
21. CVE: egy nyilvánosan ismert sérülékenység egyedi azonosítója, amelyet egy CNA ad ki. CVSS: 0–10 közötti súlyossági pontszám a kihasználhatósági és hatásjellemzők alapján. Az alappontszám nem veszi figyelembe a környezetet: hogy az érintett komponens telepítve van-e, elérhető-e (például a hálózat felől), érintett módon van-e konfigurálva, vagy védik-e más rétegek; egy kitett szolgáltatás alacsonyabb pontszámú hibája sürgősebb lehet. Az enterprise kernelek megtartják az alapverziójukat, és backportolt javításokat kapnak (és néha olyan hibák is érintik őket, amelyekről azt mondják, hogy csak az „újabb” verziókban vannak meg), így csak a gyártó biztonsági közleményei mutatják meg, hogy egy adott build javítva van-e.
22. A side channel a számítás egy fizikai hatásán (idő, fogyasztás, gyorsítótár-állapot) keresztül szivárogtat információt, nem a program kimenetein át. Egy gyorsítótárban lévő sor néhány nanoszekundum alatt olvasható, egy nem gyorsítótárazott nagyjából száz alatt; ha a támadó előbb kiszorítja (vagy kiüríti) a megosztott sorokat, majd később megméri a saját hozzáféréseit, akkor a gyorsak azok, amelyeket közben az áldozat használt, és ez felfedi az áldozat hozzáférési mintázatát, amely függhet egy titoktól.
23. Az érintett processzorokon egy felhasználói módban végzett, kernelcímről történő betöltés tranziensen végrehajtódott, mielőtt a jogosultság-ellenőrzés érvénybe lépett volna; a kivétel megérkezett, de a betöltött érték addigra már megváltoztatta a gyorsítótár állapotát, ami mérhető volt. Mivel a Linux a teljes kernelt minden címtartományba beleképezte, a teljes kernelmemória ki volt téve. A KPTI felhasználói módban külön laptáblákat használ, amelyek a kernelből (szinte) semmit sem képeznek le, így nincs mit betölteni. Ezután minden rendszerhívás, megszakítás és kivétel laptáblát vált; PCID nélkül ez minden alkalommal kiürítené a TLB-t, PCID-del mindkét címtartomány bejegyzései címkézve a TLB-ben maradnak. Az előadás gépe a Meltdownt „Not affected”-nek jelentette (nincs szükség KPTI-re), a Spectre-változatoknál pedig aktív védekezést, egy beismert hiánnyal (BHI).

**A laborfeladatok megoldásai.** 1. labor: az előadáséhoz hasonló új kerneleken a libc kezdőcíme 2 MiB-ra igazított (kb. 19 bit); a régebbi kernelek bármely laphatárra teszik; a 32 bites folyamatok sokkal kevesebb entrópiát kapnak (az `mmap_rnd_compat_bits` alapértéke 8). 2. labor: az `-O0`-s változatban a canaryt 25 karaktertől érjük el (24 karakter és a nulla bájt csak a nulla bájtját írja felül); `-O2`-nél a fordító elhagyhatja a keretmutatót, és másképp rendezheti el a keretet, így a küszöb megváltozik. 3. labor: a 2-es szint csak a fordítási időben ismert méreteket ellenőrzi (`__builtin_object_size`), a 3-as a futásidőben ismerteket is (`__builtin_dynamic_object_size`), például egy változó méretű `malloc` esetén; konstans 16-nál mindkettő elkapja. 4. labor: sanitizerek nélkül az egybájtos heap overflow általában észrevétlen marad (a malloc felfelé kerekíti a méreteket), az előjeles túlcsordulás pedig csendben körbefordul, vagy meglepő módon optimalizálódik; az ASan és az UBSan mindegyiket a hibát okozó sornál jelenti. 5. labor: a veremben tömböt nem használó programoknak `-fstack-protector-strong` mellett sincs szükségük canaryre; a Go-ban vagy Rustban írt programok egyáltalán nem használják a C canaryjét. 6. labor: sok systemd szolgáltatás használja a `SystemCallFilter=@system-service` és a `NoNewPrivileges=yes` beállítást; a státuszukban `Seccomp: 2` látszik. A seccomp csak az útvonalra mutató pointert látja, amelyet a felhasználói tér az ellenőrzés után megváltoztathat (time-of-check to time-of-use), így nem tud biztonságosan útvonalnevekre szűrni; a Landlock a kernelben, útvonal szerint korlátozza a fájlhozzáférést. 7. labor: változatlan rendszer újraindításai között a PCR 0, 2, 4 és 7 ugyanaz marad; a PCR 8 megváltozik, ha szerkesztjük a parancssort, mert a GRUB megméri az általa végrehajtott parancsokat. 8. labor: kikapcsolt Secure Bootnál a PCR 7 megváltozik, a TPM nem hajlandó feloldani a pecsétet, és a kötet a jelmondatot vagy a helyreállítási kulcsot kéri, amelyet ezért mindig szintén regisztrálni kell.

</details>

## Irodalom

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

## További olvasnivaló

Kerrisk, M. (2010). *The Linux programming interface*. No Starch Press. (Chapters on process credentials, capabilities and secure privileged programs.)

The kernel development community. (n.d.). *Kernel self-protection*. The Linux Kernel documentation. https://docs.kernel.org/security/self-protection.html

