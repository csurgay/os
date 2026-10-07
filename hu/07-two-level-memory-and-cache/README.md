# Kétszintű memóriák és gyorsítótárak

*Operációs rendszerek előadás: miért látszik az egész rendszer nagynak és gyorsnak, ha egy nagy, lassú memória elé egy kicsi, gyorsat teszünk; hogyan találja meg a gyorsítótár az adatait (direkt leképezésű, teljesen asszociatív, csoportasszociatív szervezés); melyik sort kell kidobni; és hogyan írjunk olyan programot, amelyet a gyorsítótár „szeret”*

Előző: [Párhuzamosság, holtpontok, folyamatállapotok és a Linux ütemezése](../06-concurrency-deadlocks-scheduling/). Következő: [Virtuális memória](../08-virtual-memory/).

> **Hogyan olvasd ezt az előadást?** Ahol új rövidítés vagy fogalom jelenik meg, utána egy **Egyszerűen elmagyarázva** feliratú doboz következik. Kattints rá, és kinyílik egy köznapi nyelvű magyarázat. Ha már ismered a fogalmakat, nyugodtan átugorhatod ezeket a dobozokat.

## Tanulási célok

Az [utasítás-végrehajtási ciklusról szóló előadás](../04-fetch-execute-cycle/) feltételezte, hogy a CPU minden lépésben ki tud olvasni a memóriából egy utasítást vagy egy adatszót. A valóságban a központi memória százszor lassabb a CPU-nál. Ez az előadás azt mutatja meg, hogyan rejtik el a számítógépek ezt a különbséget egy **kétszintű memóriával**: egy nagy, lassú memória (a RAM) elé egy kicsi, gyors memóriát (a gyorsítótárat, angolul cache) tesznek. Megmutatja azt is, miért tér vissza ugyanez az ötlet a RAM és a lemez között, amire a virtuális memóriáról szóló későbbi előadások épülnek.

Az előadás végére a hallgatók képesek lesznek:

- leírni a memóriahierarchiát (regiszterek, gyorsítótár, RAM, lemezek, szalag) elérési idő, kapacitás és ár szerint, és megmagyarázni, miért nem lehet egyetlen memória egyszerre nagy, gyors és olcsó;
- kiszámítani egy kétszintű memória átlagos elérési idejét a találati arányból, és megmagyarázni, miért kell a találati aránynak nagyon közel lennie 1-hez;
- kimondani a lokalitás elvét, megkülönböztetni az időbeli és a térbeli lokalitást, és megmagyarázni, miért rendelkeznek a programok ezekkel;
- felbontani egy címet tag, index és eltolás (offset) mezőkre, és végigkövetni egy találatot és egy hiányt egy direkt leképezésű gyorsítótárban, az érvényességi és a módosítási (dirty) bittel, valamint a visszaíró (write-back) és az átíró (write-through) stratégiával együtt;
- elmagyarázni a teljesen asszociatív és a csoportasszociatív gyorsítótárat, a hiányok három fajtáját és a csereálgoritmusokat (LRU, FIFO, véletlen, öregítés, Bélády optimuma);
- megmagyarázni, miért létezik optimális sorméret, és hogyan befolyásolja a teljesítményt az előbetöltés és a többmagos koherencia (hamis megosztás);
- gyorsítótár-barát ciklusokat és adatszerkezeteket írni, és mérni a gyorsítótár hatásait Linuxon.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> memória, RAM, gyorsítótár (cache), regiszter, találat, hiány, késleltetés</summary>

- **Memória:** itt tartja a számítógép azokat a programokat és adatokat, amelyekkel éppen dolgozik. A **RAM** (random-access memory, tetszőleges elérésű memória) a központi memória: nagy, de a CPU-hoz képest lassú, és kikapcsoláskor mindent elfelejt.
- **Gyorsítótár (cache):** kicsi, nagyon gyors memória, amely a legutóbb használt adatok másolatát tartja, hogy a CPU-nak ne kelljen minden alkalommal a RAM-ra várnia. Olyan, mint egy íróasztal a könyvtár mellett: a könyvek, amelyeket éppen használsz, ott maradnak az asztalon.
- **Regiszter:** az a néhány apró tárolóhely magában a CPU-ban, ami a leggyorsabb mind közül.
- **Találat, hiány:** találat, ha az adat megvan a gyorsítótárban; hiány, ha nincs meg, és a lassabb memóriából kell elhozni.
- **Késleltetés:** az a várakozási idő, ami az adat kérése és megérkezése között eltelik.

</details>

## A memóriahierarchia

Nincs olyan memóriatechnológia, amely egyszerre nagy, gyors és olcsó. A leggyorsabb memóriák a processzorlapkába vannak beépítve, ahol kevés a hely; a legnagyobbak mechanikusak vagy mágnesesek, és lassúak. A számítógépek ezért memóriák **hierarchiáját** használják:

![Regiszterek, gyorsítótár, RAM, SSD és merevlemez, optikai lemez és szalag, elérési idővel és kapacitással; a bájtonkénti ár felfelé nő](memory-hierarchy.svg)

Minden szint nagyobb és lassabb a fölötte lévőnél: regiszterek (jóval egy nanoszekundum alatt, kevesebb mint egy kilobájt), gyorsítótárak (nanoszekundumok, kilobájtoktól megabájtokig), RAM (nagyjából száz nanoszekundum, gigabájtok), lemezek (SSD-nél mikroszekundumok, merevlemeznél milliszekundumok, terabájtok) és szalagos archívumok (másodpercektől percekig, gyakorlatilag korlátlan kapacitás). A szintek közötti nagyságrendi különbség a lényeg, és az előadás gépén végzett mérések ([Linux-szakasz](#a-hierarchia-mérése)) ezt világosan mutatják: körülbelül 1,6 ns az első szintű gyorsítótárra, 4,4 ns a másodikra, nagyjából 25 ns a harmadikra és 110–180 ns a RAM-ra. Az évtizedek során a processzorok sokkal gyorsabban lettek gyorsabbak, mint ahogy a DRAM válaszideje csökkent: egy 2,8 GHz-es CPU több száz utasítást hajt végre annyi idő alatt, amennyi egyetlen véletlenszerű RAM-elérés. Wulf és McKee (1995) ezt **memóriafalnak** (memory wall) nevezte, és arra figyelmeztettek, hogy mivel a különbség exponenciálisan nő, idővel még a nagyon magas találati arányú gyorsítótárak mellett is ideje nagy részében a memóriára fog várni a processzor. (Maga a DRAM-lapka egy nyitott sorból körülbelül 10–15 ns alatt szolgáltat egy oszlopnyi adatot; az itt mért 100 ns feletti érték egy olyan betöltés teljes útja, amely az összes gyorsítótárban hiányt okoz: a gyorsítótár-keresések, a memóriavezérlő és egy DRAM-sor megnyitása.)

A felső szintek (regiszterek, gyorsítótár, RAM) **felejtők** (volatile), és a CPU utasításai közvetlenül címezhetik őket; az alsók **tartósak** (persistent), és az operációs rendszer I/O-műveletein keresztül érhetők el. A bájtonkénti ár fentről lefelé meredeken esik, a kapacitás pedig nő.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> hierarchia, ns, KiB/MiB/GiB, SRAM, DRAM, felejtő, tartós, SSD, memóriafal</summary>

- **Hierarchia:** szintekbe rendezés, fentről lefelé.
- **ns** (nanoszekundum): a másodperc egymilliárdod része. A fény egy nanoszekundum alatt körülbelül 30 cm-t tesz meg.
- **KiB, MiB, GiB:** nagyjából ezer, egymillió, egymilliárd bájt (pontosan 1024, 1024², 1024³).
- **SRAM, DRAM:** kétféle memórialapka. Az SRAM (statikus) gyors és drága, ebből készülnek a gyorsítótárak; a DRAM (dinamikus) lassabb, olcsóbb és sűrűbb, ebből készül a központi memória.
- **Felejtő / tartós:** a felejtő memória áram nélkül elveszíti a tartalmát; a tartós tár (lemezek, SSD-k, szalag) megőrzi.
- **SSD** (solid-state drive, félvezetős meghajtó): flashmemória-lapkákból épített „lemez”, sokkal gyorsabb a forgó merevlemeznél.
- **Memóriafal:** az egyre nagyobb szakadék aközött, hogy a processzorok milyen gyorsan számolnak, és hogy a memória milyen gyorsan tudja szállítani az adatot.

</details>

## A kétszintű memória varázsa

A dilemma egy háromszöggel ábrázolható: **kapacitás**, **sebesség** és **olcsóság**. Minden egyes memória egy pont a háromszögön belül, egy kompromisszum. A trükk az, hogy két memóriát kombinálunk:

![A kapacitás–sebesség–olcsóság háromszög, valamint: nagy-lassú-olcsó plusz kicsi-gyors-drága egyenlő nagy-gyors-olcsó](two-level-magic.svg)

Egy nagy, lassú, olcsó memória (a RAM) és egy kicsi, gyors, drága memória (a gyorsítótár) együtt a program szemszögéből úgy viselkedik, mint egy nagy, gyors, olcsó memória, **feltéve, hogy szinte minden elérést a kicsi szolgál ki**. Ha az elérések $H$ hányada (a **találati arány**) megtalálható a $T_C$ idő alatt válaszoló gyorsítótárban, a többinek pedig a $T_{RAM}$ idő alatt válaszoló RAM-hoz kell fordulnia, akkor az átlagos elérési idő

$$T = H \cdot T_C + (1 - H) \cdot T_{RAM}$$

A **hiányarány** $M = 1 - H$. Ha a gyorsítótár csak háromszor gyorsabb a RAM-nál ($T_C = 3$ ns, $T_{RAM} = 10$ ns), és a találati arány 95%, akkor $T = 3{,}35$ ns: majdnem olyan gyors, mint a gyorsítótár. Egy valódi gépen mért aránnyal a kép kevésbé kedvező ([Linux-szakasz](#mennyit-számít-a-találati-arány)): ha a gyorsítótár 4,4 ns, a RAM 140 ns alatt válaszol, akkor 95%-os találati arány mellett 11,2 ns adódik, két és félszer lassabb a gyorsítótárnál, és még 99% mellett is körülbelül 30%-kal lassabb marad. A valódi gyorsítótárak a tipikus programoknál valóban 95–99%-os vagy még nagyobb találati arányt érnek el (Hennessy & Patterson, 2019).

(Egyes tankönyvek a képletet $T = T_C + M \cdot T_{penalty}$ alakban írják, mert hiány esetén a gyorsítótárat már megvizsgáltuk, mielőtt a RAM-hoz fordulnánk; a két alak csak abban különbözik, hogy mit számítunk a hiány idejébe.)

És mekkora a gyorsítótár? Jellemzően a RAM **0,1%**-ának nagyságrendjébe esik: $Cap_C \cdot 1000 \approx Cap_{RAM}$. Az alább használt gépnek 33 MiB utolsó szintű gyorsítótára és 8 GiB RAM-ja van, ez 0,4%-os arány; egy 32 MiB gyorsítótárral és 32 GiB RAM-mal rendelkező szerver pontosan 0,1%-on áll. Az az igazi varázslat, hogy egy ezerszer kisebb memória az összes elérés 95–99%-át ki tudja szolgálni – és ez magyarázatra szorul.

Több gyorsítótárszint esetén a képletet szintenként alkalmazzuk: az L1-beli hiány az L2-höz megy, az L2-beli hiány az L3-hoz, és így tovább. Minden szintnek csak a fölötte lévő szint hiányainak nagy részét kell elkapnia. Az „előbb megnézzük” alakban, minden szint **lokális** $m_i$ hiányarányával (az adott szintig *eljutó* elérések közül ott hiányt okozók hányada):

$$T = T_{L1} + m_{L1} \cdot \bigl(T_{L2} + m_{L2} \cdot (T_{L3} + m_{L3} \cdot T_{RAM})\bigr)$$

Az alább mért késleltetésekkel (1,6, 4,4, 25 és 140 ns) és 95%, 80% és 50% lokális találati aránnyal $T = 1{,}6 + 0{,}05 \cdot (4{,}4 + 0{,}2 \cdot (25 + 0{,}5 \cdot 140)) \approx 2{,}8$ ns, pedig az L3 csak a hozzá eljutó elérések felét fogja el: a $0{,}05 \cdot 0{,}2 \cdot 0{,}5 = 0{,}005$ szorzat (0,5%) a **globális** hiányarány, az összes elérésnek az a hányada, amely a RAM-ig jut.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> találati arány, hiányarány, átlagos elérési idő, hiánybüntetés, gyorsítótárszint (L1, L2, L3)</summary>

- **Találati arány (H):** az elérések azon része, amelyet a gyorsítótárban megtalálunk, például 0,95 = 95%. **Hiányarány (M):** a maradék, 1 − H.
- **Átlagos elérési idő:** mennyibe kerül átlagosan egy memóriaelérés, a gyors találatokat és a lassú hiányokat együtt számolva.
- **Hiánybüntetés:** az a többletidő, amibe egy hiány kerül.
- **L1, L2, L3:** a gyorsítótár szintjei. Az L1 a legkisebb és leggyorsabb, a legközelebb van a CPU-maghoz; az L3 a legnagyobb és leglassabb, és általában a lapka összes magja közösen használja.

</details>

## Miért működik: a hivatkozási lokalitás

A programok nem véletlenszerűen érik el a memóriát. **Lokalitással** (hivatkozási lokalitással) rendelkeznek: bármely rövid időszakban a memóriájuknak csak egy kis részét használják, és ez a rész lassan változik (Denning, 2005). Ennek négy fő oka van (Stallings, 2016):

1. **A Neumann-elv: a kód szekvenciális.** Az utasításszámláló a legtöbb utasítás után egyszerűen eggyel nő (`PC++`), így a következő utasítás szinte mindig közvetlenül az aktuális után következik. Az ugrások a kivételek, és a legtöbbjük rövid.
2. **Az egymásba ágyazott hívások szűk sávban maradnak.** A programok függvényeket hívnak, azok további függvényeket, de a hívási mélység lassan, egyszerre egy szinttel változik, és hosszú ideig néhány szinten belül vándorol fel-le. A Berkeley RISC processzorokhoz végzett programvizsgálatok ezt tapasztalták, és erre építették a **regiszterablakokat**: a CPU az utolsó néhány hívási szint regisztereit a lapkán tartja, és csak az ablakon kívülre eső hívás vagy visszatérés igényel lassú átvitelt a memóriába; 8 ablakkal erre a hívások és visszatérések csak körülbelül 1%-ánál volt szükség (Stallings, 2016, a csökkentett utasításkészletű számítógépekről szóló fejezet; a fenti négy ok Stallings kétszintű memóriák teljesítményéről szóló függelékét követi). Az alábbi mérés hasonló képet talál egy mai Python-programban: 8 szintes ablaknál a hívások és visszatérések 2,5%-a esik kívülre ([Linux-szakasz](#a-hívási-mélység-mérése)).
3. **A hosszú ciklusok ritkák.** Az idő nagy része rövid ciklusokban telik, amelyek ugyanazt a néhány utasítást hajtják végre újra meg újra.
4. **A legtöbb adatszerkezet szekvenciális.** A tömbök, karakterláncok, rekordok és a verem folytonosan helyezkednek el, és gyakran elemről elemre dolgozzuk fel őket.

Ezek az okok kétféle lokalitást eredményeznek:

- **Időbeli lokalitás:** amit nemrég használtunk, azt valószínűleg hamarosan újra használni fogjuk (a ciklus utasításai, a ciklusszámlálók, a verem teteje). A gyorsítótár ezt úgy használja ki, hogy **megtartja** a nemrég használt adatokat.
- **Térbeli lokalitás:** ami egy éppen használt dolog mellett van, azt valószínűleg hamarosan használni fogjuk (a következő utasítás, a következő tömbelem). A gyorsítótár ezt úgy használja ki, hogy minden hiánykor a szomszédos bájtok egész **sorát** (blokkját) tölti be, nem csak a kért szót.

![Egy valódi program hívási mélysége 2500 egymást követő hívás és visszatérés során: egyszerre egy szinttel változik, és egy sávon belül mozog](call-depth.svg)

A lokalitás a programok tulajdonsága, nem a hardveré, ezért a programozó le is ronthatja, ahogy a [Meyers-példa](#gyorsítótár-barát-kód-írása) mutatja, vagy javíthatja is.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> lokalitás, Neumann-elv, utasításszámláló, hívási mélység, regiszterablak, ciklus, időbeli lokalitás, térbeli lokalitás, sor/blokk</summary>

- **Hivatkozási lokalitás:** a programok hajlamosak ugyanazt a néhány dolgot újra és újra használni (mint az asztalos azt a néhány szerszámot, amelyet a munkapadon tart), és az egymás mellett lévő dolgokat.
- **Neumann-elv:** az utasításokat ugyanúgy a memóriában tároljuk, mint az adatokat, és egymás után hajtjuk végre őket.
- **Utasításszámláló (PC, program counter):** az a CPU-regiszter, amely a következő utasítás címét tartalmazza; a `PC++` azt jelenti: „menj tovább a következőre”.
- **Hívási mélység:** hány függvényhívás van éppen nyitva, egymásba ágyazva.
- **Regiszterablak:** egyes processzorokban a legutóbbi függvényhívások számára fenntartott regiszterkészlet, hogy a híváshoz és a visszatéréshez ne kelljen a memóriához fordulni.
- **Ciklus:** a programnak az a része, amely sokszor ismétlődik.
- **Időbeli lokalitás:** most használtuk → valószínűleg hamarosan újra használjuk. **Térbeli lokalitás:** most használtuk → valószínűleg hamarosan a szomszédait is használjuk.
- **Sor (blokk):** az az egység, amelyben a gyorsítótár a RAM-ból adatot tölt be, például egyszerre 64 bájtot.

</details>

## Hogyan találja meg a gyorsítótár az adatait

A gyorsítótár a memória **sorainak** (blokkjainak) másolatát tárolja, azzal a feljegyzéssel együtt, hogy az egyes másolatok a memória melyik részéből származnak. A tervezése három kérdésre felel: hová kerülhet egy blokk, hogyan találjuk meg, és melyik blokkot dobjuk ki, ha hely kell.

### A direkt leképezésű gyorsítótár

A legegyszerűbb szervezés a **direkt leképezésű** gyorsítótár. Kerek számokkal dolgozó tanpéldaként legyen 4 GiB RAM, így egy bájtcím 32 bites, és legyen a gyorsítótárban 1024 sor, mindegyikben 4096 darab 32 bites szó (16 KiB), összesen 16 MiB. A címet három mezőre vágjuk:

- az **eltolás** (offset; 14 bit, mert egy sor $2^{14}$ = 16 KiB) a soron belüli bájtot választja ki;
- az **index** (10 bit, mert $2^{10}$ = 1024 sor van) azt az egyetlen sort választja ki, ahol ez a blokk lehet;
- a **tag** (címke; a maradék 8 bit) megmondja, hogy az ezen a soron osztozó $2^8 = 256$ blokk közül melyik van ott valójában.

![A cím felbontása tagre, indexre és eltolásra; az index kiválaszt egy sort, a tárolt taget összehasonlítjuk, az eltolás kiválasztja a szót](direct-mapped-cache.svg)

Minden sorhoz két állapotbit is tartozik:

- **V (valid, érvényességi bit):** 0 azt jelenti, hogy a sor még nincs betöltve (szemetet tartalmaz, például közvetlenül bekapcsolás után); 1 azt, hogy valódi másolatot tartalmaz.
- **D (dirty, módosítási bit):** 1 azt jelenti, hogy a CPU írt a másolatba, és az eltér a RAM tartalmától.

**Olvasás**: az index kiválasztja a sort; ha V = 1, és a tárolt tag megegyezik a cím tagjével, akkor **találat** van, és az eltolás kiválasztja a szót a sorból. Különben **hiány** van: ha a sor módosított (dirty), a régi tartalmát először visszaírjuk a RAM-ba; aztán a teljes új sort betöltjük a RAM-ból, eltároljuk a taget, V-t 1-re, D-t 0-ra állítjuk, és kiadjuk a szót. Egy kidolgozott példa a `cachesim.py` segítségével: a `0x12345678` cím tagje `0x12`, indexe 209, eltolása `0x1678`, ez a sor 1438. szava ([Linux-szakasz](#gyorsítótár-szimulátor)).

Az **írásokhoz** stratégia kell:

- **Átíró (write-through):** minden írás a gyorsítótárba és a RAM-ba is eljut. Egyszerű, a RAM mindig naprakész, de minden írás egy RAM-elérésbe kerül (ezt általában egy írási puffer tompítja).
- **Visszaíró (write-back):** az írás csak a gyorsítótárba kerül, és D = 1 lesz; a RAM csak akkor frissül, amikor a módosított sort kiszorítjuk. Kevesebb RAM-írás, ezért használja a legtöbb mai gyorsítótár, cserébe a hiány kezelése bonyolultabb, és a RAM átmenetileg elavult (ami a DMA és a többi mag szempontjából számít, lásd alább a koherenciát).

És mi történik, ha egy írás **hiányt** okoz? Az **írásra foglaló** (write-allocate) gyorsítótár előbb betölti a sort, majd beleír (ez a visszaíró stratégia szokásos párja: az ugyanarra a sorra eső későbbi írások találatot adnak); a **nem foglaló** (no-write-allocate) gyorsítótár az írást egyenesen a RAM-nak küldi, és a gyorsítótárat nem bántja (ez az átíró stratégia szokásos párja). Ezért jelent az alább bemutatott cachegrind írásokra is hiányokat.

**Miért van középen az index?** A gyorsítótárak a címet *tag | index | eltolás* sorrendben bontják fel, az index tehát középen van, nem a legfelső biteken. Ez a sorrend nem mellékes részlet. Ha az indexet az eltolás fölötti bitekből vesszük, a memória egymást követő blokkjai egymást követő sorokba kerülnek, így egy program, amely egy a gyorsítótárnál kisebb tömbön halad végig, az egészet bent tarthatja. Ha az index a legfelső biteken volna, az összes szomszédos blokk ugyanazon a néhány soron osztozna, és kiszorítanák egymást; a szimulátor megmutatja ennek árát ([Linux-szakasz](#gyorsítótár-szimulátor)). A valódi sorok ráadásul sokkal rövidebbek a tanpélda 16 KiB-jánál: minden mai x86 és a legtöbb ARM processzoron 64 bájtosak, [a sorméretről szóló szakaszban](#a-sorméret-megválasztása) kifejtett okokból.

A direkt leképezésű gyorsítótár egyszerű és gyors: elérésenként egyetlen összehasonlítás. Gyengesége az **ütközés**: két blokk, amelyek címe a gyorsítótár méretének többszörösével tér el, ugyanarra a sorra képeződik le, és kiszorítják egymást, még akkor is, ha a gyorsítótár többi része üres.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> direkt leképezés, cím, bit, mező, eltolás, index, tag, érvényességi bit, módosítási bit, átíró, visszaíró, írási puffer, ütközés</summary>

- **Direkt leképezés:** a memória minden blokkjának pontosan egy helye van a gyorsítótárban, ahová kerülhet, mint a ruhatárban, ahol a számod dönti el, melyik fogasra kerül a kabátod.
- **Cím:** egy bájt sorszáma a memóriában. **Bit:** egy 0 vagy 1; egy 32 bites cím 32 bitből áll. A **mező** bitek olyan csoportja, amelynek saját jelentése van.
- **Eltolás (offset):** a soron belül melyik bájt. **Index:** a gyorsítótár melyik sora. **Tag (címke):** a cím többi része, amelyet a sorral együtt tárolunk, és amely megmondja, a memória melyik blokkját tartalmazza éppen a sor.
- **Érvényességi bit:** „ebben a sorban valódi adat van”. **Módosítási (dirty) bit:** „ezt a sort megváltoztatták, és a RAM még nincs frissítve”.
- **Átíró (write-through):** írjunk egyszerre a gyorsítótárba és a RAM-ba. **Visszaíró (write-back):** most csak a gyorsítótárba írjunk, a RAM-ba pedig később, amikor a sor elhagyja a gyorsítótárat.
- **Írási puffer:** kis várakozási sor, amelynek révén a CPU folytathatja a munkát, amíg az írások a RAM felé tartanak.
- **Ütközés:** két blokk ugyanarra a gyorsítótársorra tart igényt, és folyton kiszorítják egymást.

</details>

### A teljesen asszociatív gyorsítótár

Az ellenkező végletben bármely blokk **bármelyik** sorba kerülhet. Ekkor a gyorsítótárnak nincs indexe: a cím csak tagből és eltolásból áll, és egy blokk megtalálásához a gyorsítótár a taget egyszerre hasonlítja össze **az összes** sor tagjével, soronként egy komparátorral (minden komparátor a két tag bitenkénti XOR-ja, majd az eredmények ÉS-kapcsolata). Ez **tartalom szerint címezhető memória** (content-addressable memory): a tartalma alapján keresünk benne, nem a hely alapján.

![Az összes tárolt taget párhuzamosan hasonlítjuk össze a cím tagjével; az egyező sor adja ki az eltolás által kiválasztott szót](fully-associative-cache.svg)

Ütközések nincsenek, de a komparátorok miatt nagy és sok energiát fogyaszt, ezért így csak kis gyorsítótárakat építenek, például sok olyan TLB-t (translation lookaside buffer, címfordítási gyorsítótár), amely a virtuális memória címfordításait tárolja (a nagyobb TLB-k viszont, a többi gyorsítótárhoz hasonlóan, csoportasszociatívak).

### Csoportasszociatív gyorsítótárak: a kompromisszum

A valódi gyorsítótárak **csoportasszociatívak** (set-associative): a sorok *n* elemű csoportokba (n utas, n-way) rendeződnek, az index egy csoportot választ ki, és a blokk a csoport *n* sorának bármelyikében lehet, így csak *n* taget kell összehasonlítani. Az 1 utas gyorsítótár direkt leképezésű; az egyetlen csoportból álló gyorsítótár teljesen asszociatív.

![Hová kerülhet a 12-es blokk egy 8 soros gyorsítótárban: direkt leképezésnél egyetlen sorba, 2 utasnál a 0. csoport bármelyik sorába, teljesen asszociatívnál bármelyik sorba](block-placement.svg)

Az alább használt gépnek 8 utas, 32 KiB-os L1 adatgyorsítótára (64 csoport, csoportonként 8 sor), 16 utas, 1 MiB-os L2-je és 11 utas, 33 MiB-os L3-a van, mind 64 bájtos sorokkal ([Linux-szakasz](#a-mért-gép-gyorsítótárai)).

**A hiányok három fajtája** (Hill & Smith, 1989) megmagyarázza, melyik tervezési döntés mi ellen segít:

- **kötelező** (hideg, compulsory) hiányok: egy blokk első elérése mindig hiány; a nagyobb sorok csökkentik a számukat, mert egy hiány több szomszédot is behoz;
- **kapacitás**hiányok: a program több adatot használ, mint amennyi a gyorsítótárba belefér; csak a nagyobb gyorsítótár segít;
- **ütközési** (conflict) hiányok: az adat elférne, de túl sok blokk képeződik ugyanarra a csoportra; a nagyobb asszociativitás segít.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> teljesen asszociatív, komparátor, tartalom szerint címezhető memória, TLB, csoport, n utas, kötelező, kapacitás- és ütközési hiány</summary>

- **Teljesen asszociatív:** bármely blokk bárhová kerülhet, mint egy parkolóban számozott helyek nélkül; hogy megtaláld az autódat, az összeset végig kell nézned.
- **Komparátor:** kis áramkör, amely megvizsgálja, hogy két szám egyenlő-e.
- **Tartalom szerint címezhető memória:** olyan memória, amelytől azt kérdezed: „hol van ez az érték?”, nem pedig azt, hogy „mi van ezen a helyen?”.
- **TLB** (translation lookaside buffer, címfordítási gyorsítótár): kis gyorsítótár a CPU-ban a virtuális memória címfordításai számára (egy későbbi előadás témája).
- **Csoport, n utas:** a gyorsítótár n sorból álló kis csoportokra oszlik; egy blokk a saját csoportjának bármelyik sorába kerülhet. Középút az „egyetlen fix hely” és a „bárhol” között.
- **Kötelező hiány:** amikor valamit először használunk, az még nem lehet a gyorsítótárban. **Kapacitáshiány:** a gyorsítótár egyszerűen túl kicsi. **Ütközési hiány:** lenne hely, csak nem a megfelelő csoportban.

</details>

### Melyik sort dobjuk ki?

Ha egy hiánynak sor kell, és a csoport (teljesen asszociatív gyorsítótárban az egész gyorsítótár) tele van, egy **csereálgoritmus** választja ki az áldozatot. Az ideális áldozat az a sor, amelyet már régóta senki sem keresett. Egy egyszerű, számlálókon alapuló **öregítési** (aging) eljárás ezt közelíti: minden eléréskor minden sor kora eggyel nő, egy találat pedig megfelezi a megtalált sor korát, így a gyakran használt sorok fiatalok maradnak; a legöregebb sort szorítjuk ki. A szokásos stratégiák:

- **LRU** (least recently used, legrégebben használt): azt a sort szorítjuk ki, amelyet a legrégebben nem használtak. Az időbeli lokalitást követi, de a pontos LRU-hoz az összes sor sorrendjét nyilván kell tartani, ezért a hardver olcsó közelítéseket használ, például fa alapú pszeudo-LRU-t. A fenti öregítéshez hasonló számlálók az operációs rendszerek lapcseréjének klasszikus közelítései, ez a virtuális memóriáról szóló előadás témája. (Ennek az *öregítésnek* semmi köze az ütemezésről szóló előadás prioritás-öregítéséhez.)
- **FIFO** (first in, first out, először be, először ki): azt a sort szorítjuk ki, amelyik a legrégebben van a gyorsítótárban, függetlenül a használattól. Egyszerű, de kidobhat egy állandóan használt sort is.
- **Véletlen**: meglepően versenyképes, és elkerüli az LRU legrosszabb esetét, amikor egy szabályos minta miatt az LRU éppen azt a sort szorítja ki, amelyre legközelebb szükség lesz.
- **OPT** (Bélády algoritmusa): azt a sort szorítjuk ki, amelynek következő használata a legtávolabbi jövőben van. Bizonyíthatóan optimális, de a jövő ismeretét igényli, ezért mércéként szolgál. Bélády László, aki 1928-ban született Budapesten, 1966-ban publikálta, amikor az IBM Researchnél dolgozott (Bélády, 1966). 1969-ben munkatársaival megmutatta, hogy egyes stratégiáknál, például a FIFO-nál, a nagyobb memória *több* hiányt eredményezhet; ezt ma Bélády-anomáliának nevezzük (Bélády et al., 1969).

Nincs olyan stratégia, amely minden terhelésen győzne. A szimulátor ([Linux-szakasz](#gyorsítótár-szimulátor)) mutat egy ciklust, amely kicsit nagyobb a gyorsítótárnál, és ahol az LRU éppen azt a sort dobja ki, amelyre legközelebb szükség lesz (72,7% hiány), a véletlen csere pedig sokkal jobban teljesít (18,2%), és egy másik terhelést, ahol az LRU a legjobb; Bélády optimuma mindkettőn mindegyiket megveri.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> csereálgoritmus, áldozat, LRU, FIFO, öregítés, Bélády algoritmusa, Bélády-anomália</summary>

- **Csereálgoritmus, áldozat:** az a szabály, amely eldönti, melyik sornak kell elhagynia a megtelt gyorsítótárat; a kiválasztott sor az áldozat.
- **LRU:** azt dobjuk ki, amit a legrégebben nem használtunk, mint amikor leszedjük az asztalunkról azokat a könyveket, amelyeket hetek óta ki sem nyitottunk.
- **FIFO** (first in, first out): azt dobjuk ki, ami elsőként érkezett, mint a legrégebbi tejet a hűtőből – akkor is, ha minden nap iszunk belőle.
- **Öregítés:** minden sornak van egy számlálója, amely nő, amíg a sort nem használjuk, és csökken, amikor igen; a legöregebb megy.
- **Bélády algoritmusa (OPT):** azt dobjuk ki, amire a legkésőbb lesz újra szükség. Tökéletes, de ehhez ismerni kellene a jövőt.
- **Bélády-anomália:** FIFO esetén, furcsa módon, ha több helyet adunk a gyorsítótárnak, az több hiányt okozhat.

</details>

## A sorméret megválasztása

Rögzített kapacitású gyorsítótárnál a hiányarány a sor (blokk) méretétől függ. A kis sorok elpazarolják a térbeli lokalitást: minden hiány csak néhány bájtot hoz be. A nagyon nagy sorok az időbeli lokalitást pazarolják el: a rögzített méretű gyorsítótárban ekkor kevés sor van, és az újra meg újra használt adatokat kiszorítják azok a nagy blokkok, amelyeket csak azért töltöttünk be, mert valami mellett voltak. A kettő között van egy **optimum**:

![Szimulált hiányarány a sorméret függvényében egy 4 KiB-os gyorsítótárra: 4 bájtnál 87%, a minimum 9,1% 64 bájtnál, nagy soroknál körülbelül 16%-ra nő](miss-rate-vs-line-size.svg)

A szimulált terhelés a kétféle lokalitást keveri: 32 gyakran használt változó egy megabájton szétszórva (csak időbeli lokalitás) és egy tömb szekvenciális bejárásai (csak térbeli lokalitás). A hiányarány az egyszavas sorok 87%-áról 64 bájtnál 9,1%-ra esik, aztán újra emelkedik. A nagyobb sorok ráadásul minden hiányt lassabbá is tesznek, mert több bájtot kell átvinni. A sok programon végzett mérések a processzortervezőket ugyanide vezették: ma a 64 bájtos sor a szabvány (Hennessy & Patterson, 2019).

## Gyorsítótárak egy valódi gépben

- **Több szint.** Minden magnak saját L1 gyorsítótárai vannak, utasítás- és adatgyorsítótárra osztva (hogy egy utasításlehívás és egy adatelérés ugyanabban az órajelciklusban történhessen), valamint saját L2-je; a lapka magjai közösen használják az L3-at.
- **Előbetöltés (prefetching).** A hardver figyeli az elérési mintát, és a sorokat **még a kérés előtt** betölti, ha meg tudja jósolni őket: egy szekvenciális bejárás következő sorait, az állandó lépésközöket, Intel processzorokon pedig a „pár” sort is, amely egy 128 bájtos blokkot tesz teljessé (Intel, 2024). Az előbetöltés elrejti a szabályos elérési minták késleltetését, de a véletlenszerűeken nem tud segíteni; ezért látja az alábbi mutatókövetés a RAM teljes késleltetését, míg egy szekvenciális bejárás nem.
- **Koherencia.** Ha két mag ugyanazt a sort tartja a gyorsítótárában, és az egyik ír bele, a másik másolata elavul. Egy **gyorsítótár-koherencia protokoll** (például a MESI, amely a sorokat Modified, Exclusive, Shared vagy Invalid, azaz módosított, kizárólagos, megosztott vagy érvénytelen állapotúnak jelöli) az író magot a sor kizárólagos tulajdonosává teszi, a többi másolatot pedig érvényteleníti. A koherencia egész sorokon működik, ebből fakad a **hamis megosztás**: két szál, amely *különböző* változókat ír *ugyanabban* a sorban, folyton elveszi egymástól a sort, holott a programban semmin sem osztoznak ([Linux-szakasz](#hamis-megosztás)). Egy sornak ugyanez a magok közötti pattogása, egyetlen változó *valódi* megosztásával, áll a [párhuzamosságról szóló előadás](../06-concurrency-deadlocks-scheduling/#atomi-műveletek-spinlockok-és-mutexek) lassú, versengő számlálója mögött is.
- **Ugyanez az ötlet egy szinttel lejjebb.** A RAM maga is a gyors szint a lemez számára: az operációs rendszer a nemrég olvasott fájladatokat az egyébként kihasználatlan RAM-ban, a **lapgyorsítótárban** (page cache) tartja, így ugyanannak a fájlnak a második olvasása a memóriából jön ([Linux-szakasz](#a-ram-mint-a-lemez-gyorsítótára)); a virtuális memória, egy későbbi előadás témája, a lemezt használja a RAM lassú szintjeként. A képlet, a lokalitás jelentősége és a csereprobléma ugyanaz; csak a számok változnak, nanoszekundumokról milliszekundumokra.

**Történet.** Maurice Wilkes 1965-ben egy kétoldalas cikkben vetette fel az ötletet **szolgamemória** (slave memory) néven: egy kicsi, gyors memória, amely automatikusan a nagy központi memória legutóbb használt szavainak másolatát tartja (Wilkes, 1965). Az első gyorsítótárral rendelkező kereskedelmi számítógép az IBM System/360 Model 85 volt, amelyet 1968 januárjában jelentettek be 16–32 KiB-os, a mai sorokhoz hasonlóan 64 bájtos blokkokba szervezett gyorsítótárral (Liptay, 1968); a *cache* szó (franciául rejtekhely) hamarosan általános elnevezéssé vált (Smith, 1982, a következő évek terveit tekinti át).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> utasítás- és adatgyorsítótár, megosztott gyorsítótár, előbetöltés, koherencia, MESI, hamis megosztás, lapgyorsítótár, virtuális memória</summary>

- **Utasításgyorsítótár / adatgyorsítótár:** külön gyorsítótár a program utasításainak és azoknak az adatoknak, amelyeken a program dolgozik.
- **Megosztott gyorsítótár:** egyetlen gyorsítótár, amelyet a lapka minden magja használ.
- **Előbetöltés:** az adat elhozása még azelőtt, hogy kérnék, mert a mintából megjósolható – mint a pincér, aki már hozza a következő fogást, mielőtt intenél.
- **Koherencia:** ugyanannak az adatnak a különböző gyorsítótárakban lévő másolatait összhangban tartjuk, hogy egyetlen mag se olvasson elavult értéket. **MESI:** a szokásos protokollban az a négy állapot, amelyben egy sor lehet (Modified, Exclusive, Shared, Invalid: módosított, kizárólagos, megosztott, érvénytelen).
- **Hamis megosztás:** két szál különböző változókat használ, amelyek véletlenül ugyanabban a gyorsítótársorban vannak, és úgy lassítják egymást, mintha ugyanazért a változóért harcolnának.
- **Lapgyorsítótár (page cache):** a RAM-nak az a része, ahol az operációs rendszer a nemrég használt fájladatok másolatát tartja.
- **Virtuális memória:** olyan technika, amely lehetővé teszi, hogy a programok több memóriát használjanak, mint amennyi RAM van, a lemezt használva lassú szintként (egy későbbi előadás témája).

</details>

## Miért fontos ez az operációs rendszernek

A gyorsítótárak hardverek, de az operációs rendszer döntései megváltoztatják a találati arányukat, és egyes feladatai csak miattuk léteznek:

- **A környezetváltások szennyezik a gyorsítótárakat.** Amikor egy folyamat visszakapja a CPU-t, a sorait addigra kiszorította az, aki közben futott. Ez a közvetett költség – nem pedig maga a váltás 1,5 µs-a, amelyet az [ütemezésről szóló előadásban](../06-concurrency-deadlocks-scheduling/#egy-környezetváltás-ára) mértünk – a fő oka annak, hogy az időszeletek milliszekundumos hosszúságúak.
- **Gyorsítótár-affinitást figyelembe vevő ütemezés.** A felébredő feladat azon a magon fut a leggyorsabban, amelynek gyorsítótárai még tartalmazzák az adatait, ezért az ütemező szívesen hagyja a feladatokat ott, ahol legutóbb futottak, és a [terheléskiegyenlítője](../06-concurrency-deadlocks-scheduling/#a-linux-ütemezése) vonakodva mozgatja őket, elsősorban olyan magok között, amelyek közös gyorsítótáron osztoznak.
- **A TLB és a címtartományok.** Egy másik folyamatra váltva megváltoznak a címfordítások, így a régi folyamat TLB-bejegyzései használhatatlanok. A régebbi processzorok minden váltáskor kiürítették a teljes TLB-t; a modernek a bejegyzéseket címtartomány-azonosítóval címkézik (x86-on PCID, process-context identifier; ARM-on ASID, address space identifier), így mindkét folyamat bejegyzései bent maradhatnak.
- **DMA és koherencia.** Amikor egy eszköz DMA-val (közvetlen memória-hozzáféréssel) a memóriába ír, a gyorsítótárakban lévő másolatok elavulnak. x86-on a hardver tartja őket koherensen; sok beágyazott processzoron a meghajtóprogramnak magának kell kiírnia vagy érvénytelenítenie az érintett sorokat, a kernel DMA-interfészén keresztül.
- **Az utolsó szintű gyorsítótár megosztása.** A különböző magokon futó folyamatok versenyeznek a közös L3-ért. Az operációs rendszerek ezt csökkenthetik, ha olyan fizikai lapokat választanak, amelyek a gyorsítótár különböző részeire képeződnek le (*lapszínezés*, page colouring), a modern Intel és AMD processzorok pedig lehetővé teszik, hogy az operációs rendszer az L3-at folyamatcsoportok között felossza (az Intel Cache Allocation Technology, amelyet Linuxon a `resctrl` fájlrendszer kezel). A felhőszolgáltatók ilyen mechanizmusokra támaszkodnak; ez az egyik oka annak, hogy egy virtuális gép kisebb L3-at láthat, mint amekkora a lapkán van, ahogy az alábbi mérésben is.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> gyorsítótár-szennyezés, affinitás, PCID/ASID, lapszínezés, gyorsítótár-particionálás</summary>

- **Gyorsítótár-szennyezés:** egy másik program adatai kiszorították a tieidet a gyorsítótárból, így hiányokkal kezdesz.
- **Affinitás:** egy feladat „ragaszkodása” ahhoz a maghoz, amelyen korábban futott, és ahol az adatai még a gyorsítótárban vannak.
- **PCID, ASID:** kis szám, amely jelzi, melyik folyamathoz tartozik egy TLB-bejegyzés, így a bejegyzéseket nem kell minden váltáskor eldobni.
- **Lapszínezés:** a memórialapokat úgy választjuk, hogy a különböző programok a gyorsítótár különböző részeit használják.
- **Gyorsítótár-particionálás:** minden programcsoport rögzített részt kap a közös gyorsítótárból, így egyik sem tudja az összes többit kiszorítani.

</details>

## Gyorsítótár-barát kód írása

Egy klasszikus példa Scott Meyers *CPU Caches and Why You Care* című előadásából származik (Meyers, 2014). A C és a C++ a kétdimenziós tömböt **soronként** tárolja: `a[i][0]`, `a[i][1]`, … a memóriában szomszédok, míg `a[i][j]` és `a[i+1][j]` között egy teljes sor van. Ha a tömböt soronként összegezzük, szekvenciálisan haladunk végig a memórián, és minden betöltött sor minden bájtját felhasználjuk; ha oszloponként, akkor minden lépésben egy sornyit ugrunk, és minden 64 bájtos sorból egyetlen `int`-et használunk fel, mielőtt továbblépnénk:

![A soronkénti bejárás a memóriát követi, és egy sor mind a 16 int-jét felhasználja; az oszloponkénti minden lépésben egy sornyit ugrik; mért idők négy méretre](traversal.svg)

A gyorsítótárba beférő kis tömböknél a különbség szerény lehet; az előadás gépén az oszloponkénti ciklus 5,7–19-szer volt lassabb, és a különbség nő, ahogy a tömb kinövi a gyorsítótárakat ([Linux-szakasz](#soronként-vagy-oszloponként)). A pontos szorzó a processzortól, a fordítótól és a tömb méretétől függ, de az irány soha nem változik. Az általános szabályok a lokalitásból következnek:

- **Az adatokat a tárolás sorrendjében járjuk be.** Az egymásba ágyazott ciklusok legbelső ciklusa C/C++-ban az utolsó indexen fusson végig (Fortranban az elsőn, mert ott a tömböket oszloponként tárolják).
- **Részesítsük előnyben a folytonos adatszerkezeteket.** Egy értékeket tartalmazó tömb (`std::vector`) sokkal gyorsabban bejárható, mint a külön-külön lefoglalt csomópontokból álló láncolt lista, amelynél minden lépés potenciális hiány.
- **Ami együtt használatos, legyen együtt**, és válasszuk szét, amit különböző szálak írnak: a szálankénti adatokat töltsük ki 64 bájtra (erre a C++17 a `std::hardware_destructive_interference_size` konstanst kínálja).
- **Dolgozzunk a gyorsítótárba beférő blokkokban.** A nagy mátrixokon dolgozó algoritmusok (szorzás, transzponálás) olyan csempéket dolgoznak fel, amelyek beférnek az L1-be vagy az L2-be (blokkosítás, csempézés).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> kétdimenziós tömb, soronkénti (row-major) tárolás, láncolt lista, kitöltés, csempézés</summary>

- **Kétdimenziós tömb:** számok táblázata sorokkal és oszlopokkal, `a[sor][oszlop]`.
- **Soronkénti tárolás (row-major order):** a táblázatot sorról sorra tároljuk a memóriában, mint egy könyv sorait.
- **Láncolt lista:** különálló adatdarabok lánca, ahol mindegyik a következőre mutat; a darabok bárhol lehetnek a memóriában.
- **Kitöltés (padding):** szándékosan hozzáadott üres bájtok, hogy két adat különböző gyorsítótársorokba kerüljön.
- **Csempézés (tiling, blokkosítás):** egy nagy táblázatot kis négyzetekre bontunk, és egy négyzetet befejezünk, mielőtt a következőt elkezdenénk, így a négyzet a gyorsítótárban marad.

</details>

## Ugyanezek az elvek Linuxon (x86-64)

Az alábbi kimenetek egy valódi rendszerről származnak: egy felhőalapú adatközpontban futó Ubuntu 24.04 virtuális gépről, 2 virtuális CPU-val (Intel Xeon, Cascade Lake család, 2,8 GHz), 8 GiB RAM-mal, Linux 6.18-cal és gcc 13-mal. Egy virtuális gépen más bérlők is osztozhatnak az L3 gyorsítótáron és a memóriasínen, így az abszolút számok futásról futásra változnak; a lépcsők és az arányok a lényegesek.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> konzol, lscpu, sysfs, gcc, -O2, taskset, valgrind/cachegrind, munkahalmaz, mutatókövetés, lépésköz, lap, óriáslap, vektorutasítások, memóriaszintű párhuzamosság, atomi növelés</summary>

- **Konzol** (terminál): ablak, amelybe szövegként gépeljük a parancsokat. A `$` jellel kezdődő sorokat mi gépeljük; a többi sor a számítógép válasza.
- **lscpu:** a processzort leíró parancs. **sysfs** (`/sys`): virtuális fájlok halmaza, amelyekben a Linux-kernel a hardverről közöl információkat.
- **gcc, -O2:** a C-fordító, amelyet a program optimalizálására kérünk.
- **taskset -c 0:** a programot csak a 0. CPU-n futtatjuk, hogy a mérés közben ne kerüljön át egy másik magra.
- **valgrind / cachegrind:** eszköz, amely a programot egy szimulált processzoron futtatja, és megszámolja a gyorsítótár-találatait és -hiányait.
- **Munkahalmaz:** az a memória, amelyet egy program egy adott időszakban használ.
- **Mutatókövetés (pointer chase):** egy lánc követése, amelyben minden elem megmondja, hol van a következő, így minden lépésnek meg kell várnia az előzőt.
- **Lépésköz (stride):** két egymást követő elérés távolsága; az 1-es lépésköz minden elemet jelent, a 16-os minden 16.-at.
- **Lap, óriáslap:** a memóriát lapokban kezeljük, ezek általában 4 KiB-osak; az óriáslap (huge page) 2 MiB-os. Kevesebb, nagyobb laphoz kevesebb címfordítás kell.
- **Vektorutasítások (SIMD):** olyan utasítások, amelyek egyszerre több szomszédos számon végzik el ugyanazt a műveletet.
- **Memóriaszintű párhuzamosság:** a processzor egyszerre több, egymástól független memóriaelérésre vár, így a várakozási idők átfedik egymást.
- **Atomi növelés:** egy változó eggyel növelése egyetlen oszthatatlan lépésként, hogy két mag ne keverhesse össze a frissítéseit.

</details>

### A mért gép gyorsítótárai

A kernel minden gyorsítótárszintet leír a sysfs-ben:

```console
$ for d in /sys/devices/system/cpu/cpu0/cache/index*; do echo "L$(cat $d/level) $(cat $d/type) size=$(cat $d/size) ways=$(cat $d/ways_of_associativity) line=$(cat $d/coherency_line_size) sets=$(cat $d/number_of_sets) shared=$(cat $d/shared_cpu_list)"; done
L1 Data size=32K ways=8 line=64 sets=64 shared=0
L1 Instruction size=32K ways=8 line=64 sets=64 shared=0
L2 Unified size=1024K ways=16 line=64 sets=1024 shared=0
L3 Unified size=33792K ways=11 line=64 sets=49152 shared=0-1
$ getconf LEVEL1_DCACHE_LINESIZE
64
```

Méret = csoportok száma × utak száma × sorméret: az L1-re 64 × 8 × 64 B = 32 KiB; az L3-ra 49 152 × 11 × 64 B = 33 MiB. Az L1 és az L2 gyorsítótár egyetlen maghoz tartozik (`shared=0`), az L3-on mindkét mag osztozik (`0-1`). Ebből adódik a cím felbontása: 64 bájtos soroknál az eltolás 6 bit, és 64 csoportnál az L1 indexe a következő 6 bit. Együtt éppen egy 4 KiB-os lapon belüli eltolás 12 bitjét adják, és ez nem véletlen: az L1 már azelőtt elkezdheti a csoport kikeresését, hogy a virtuális címet fizikai címre fordították volna (*virtuálisan indexelt, fizikailag címkézett* gyorsítótár, virtually indexed, physically tagged). Ezért is nőnek az L1 gyorsítótárak az utak számának, nem pedig a csoportok számának növelésével.

### A hierarchia mérése

A `latency.c` egyetlen memóriaelérés idejét méri annak függvényében, hogy a program mennyi memóriát használ. Egy puffer minden 64 bájtos sorát véletlenszerű sorrendben egy másikhoz láncolja, és végigköveti a láncot: minden elérés az előzőtől függ, így a CPU nem tudja sem átfedni, sem előre betölteni őket, és annak a szintnek a teljes késleltetése látszik, amelyik az adatot tartja:

```console
$ gcc -O2 -o latency latency.c
$ taskset -c 0 ./latency
working set  ns/access
      4 KiB       1.8
      8 KiB       1.5
     16 KiB       1.6
     32 KiB       2.0
     64 KiB       4.3
    128 KiB       4.3
    256 KiB       4.4
    512 KiB       5.4
      1 MiB      10.3
      2 MiB      24.3
      4 MiB      24.7
      8 MiB     109.6
     16 MiB     139.2
     32 MiB     140.3
     64 MiB     141.0
    128 MiB     146.8
    256 MiB     161.0
    512 MiB     182.3
```

![Mért elérési idő a munkahalmaz méretének függvényében, logaritmikus tengelyeken, lépcsőkkel az L1, L2, L3 és RAM szinteknél](latency-ladder.svg)

A lépcsők maguk a hierarchia: 32 KiB-ig az adat befér az L1-be (körülbelül 1,6 ns, 2,8 GHz-en 4–5 órajelciklus); 1 MiB-ig az L2-be (4,4 ns); aztán jön az L3 (körülbelül 25 ns); néhány MiB fölött a RAM (110–180 ns). Az L3-lépcső jóval a hardver által jelentett 33 MiB alatt véget ér, valószínűleg azért, mert egy felhőbeli virtuális gépen az L3-on ugyanazon a fizikai processzoron futó más bérlők is osztoznak. 8 MiB fölött egy második hatás is hozzáadódik a RAM késleltetéséhez: a szokásos 4 KiB-os lapokkal maguk a címfordítások sem férnek már bele a TLB-be. 2 MiB-os „óriáslapokat” kérve (`./latency huge`) ebben a futásban a legnagyobb munkahalmazok 10–26%-kal gyorsabbak lettek (például 512 MiB-nál 182 helyett 134 ns); erre a virtuális memóriáról szóló előadás visszatér.

### Mennyit számít a találati arány

Az `amat.py` kiértékeli a $T = H \cdot T_C + (1-H) \cdot T_{RAM}$ képletet, először kerek értékekkel egy a RAM-nál háromszor gyorsabb gyorsítótárra, aztán a fent mért L2- és RAM-késleltetéssel:

```console
$ python3 amat.py 3 10
cache 3 ns, main memory 10 ns
  H =  50.0%:  T =    6.50 ns  (  1.5x faster than memory alone,  2.2x slower than the cache)
  H =  80.0%:  T =    4.40 ns  (  2.3x faster than memory alone,  1.5x slower than the cache)
  H =  90.0%:  T =    3.70 ns  (  2.7x faster than memory alone,  1.2x slower than the cache)
  H =  95.0%:  T =    3.35 ns  (  3.0x faster than memory alone,  1.1x slower than the cache)
  H =  98.0%:  T =    3.14 ns  (  3.2x faster than memory alone,  1.0x slower than the cache)
  H =  99.0%:  T =    3.07 ns  (  3.3x faster than memory alone,  1.0x slower than the cache)
  H =  99.9%:  T =    3.01 ns  (  3.3x faster than memory alone,  1.0x slower than the cache)
$ python3 amat.py 4.4 140
cache 4.4 ns, main memory 140 ns
  H =  50.0%:  T =   72.20 ns  (  1.9x faster than memory alone, 16.4x slower than the cache)
  H =  80.0%:  T =   31.52 ns  (  4.4x faster than memory alone,  7.2x slower than the cache)
  H =  90.0%:  T =   17.96 ns  (  7.8x faster than memory alone,  4.1x slower than the cache)
  H =  95.0%:  T =   11.18 ns  ( 12.5x faster than memory alone,  2.5x slower than the cache)
  H =  98.0%:  T =    7.11 ns  ( 19.7x faster than memory alone,  1.6x slower than the cache)
  H =  99.0%:  T =    5.76 ns  ( 24.3x faster than memory alone,  1.3x slower than the cache)
  H =  99.9%:  T =    4.54 ns  ( 30.9x faster than memory alone,  1.0x slower than the cache)
```

3-as sebességarány mellett már a 90%-os találati arány is jó. 32-es aránynál, mint a valódi gépen, minden százaléknyi hiány sokba kerül: ha 95%-ról 99%-ra lépünk, az átlagos elérési idő a felére csökken. Ezért van a gyorsítótáraknak több szintjük, és ezért lehetnek a jó lokalitású programok sokszor gyorsabbak a rossz lokalitásúaknál.

### Soronként vagy oszloponként

A `traverse.c` egy N × N méretű `int` tömböt kétszer összegez, először soronként, aztán oszloponként:

```console
$ gcc -O2 -o traverse traverse.c
$ for n in 1024 2048 4096 8192; do taskset -c 0 ./traverse $n; done
 1024 x 1024  (   4 MiB)  row by row     0.6 ms   column by column     3.7 ms   ratio  5.7  (sum 2145386496)
 2048 x 2048  (  16 MiB)  row by row     2.8 ms   column by column    19.0 ms   ratio  6.8  (sum 17171480576)
 4096 x 4096  (  64 MiB)  row by row    10.3 ms   column by column   160.9 ms   ratio 15.6  (sum 137405399040)
 8192 x 8192  ( 256 MiB)  row by row    39.7 ms   column by column   760.9 ms   ratio 19.2  (sum 1099377410048)
```

Optimalizálás nélkül (`-O0`) minden változót minden lépésben betöltünk a memóriából és visszaírunk oda, ami mindkét ciklushoz ugyanazt az állandó költséget adja hozzá, és felhígítja az arányt; `-O2`-nél a változók regiszterekben maradnak, és a tömb memóriaelérései dominálnak. (`-O3`-nál a gcc a soronkénti ciklust vektorutasításokká is alakítja, amelyek egyszerre több szomszédos `int`-et adnak össze – ez csak azért működik, mert szomszédok.) Optimalizálás nélkül a különbség kisebb, de még mindig nagy:

```console
$ gcc -O0 -o traverse_O0 traverse.c
$ for n in 1024 4096; do taskset -c 0 ./traverse_O0 $n; done
 1024 x 1024  (   4 MiB)  row by row     2.1 ms   column by column     4.2 ms   ratio  1.9  (sum 2145386496)
 4096 x 4096  (  64 MiB)  row by row    35.1 ms   column by column   177.2 ms   ratio  5.0  (sum 137405399040)
```

A `cachegrind` közvetlenül megszámolja a hiányokat: mindkét bejárási sorrendet külön futtatja egy szimulált, a gép geometriájával megegyező L1 adatgyorsítótáron (a cachegrind csak az első és az utolsó gyorsítótárszintet szimulálja; `traverse_one.c`, N = 1024; részletek az összesítésből):

```console
$ gcc -O1 -o traverse_one traverse_one.c
$ valgrind --tool=cachegrind --cache-sim=yes ./traverse_one row 1024
==282== D refs:         2,163,441  (1,102,477 rd   + 1,060,964 wr)
==282== D1  misses:       132,923  (   66,981 rd   +    65,942 wr)
==282== D1  miss rate:        6.1% (      6.1%     +       6.2%  )
$ valgrind --tool=cachegrind --cache-sim=yes ./traverse_one col 1024
==284== D refs:         2,163,441  (1,102,477 rd   + 1,060,964 wr)
==284== D1  misses:     1,115,962  (1,050,020 rd   +    65,942 wr)
==284== D1  miss rate:       51.6% (     95.2%     +       6.2%  )
```

Az írások (a tömb feltöltése, ami mindkét programban azonos) 16 `int`-enként egyszer okoznak hiányt: 6,2%. Az összegző olvasások soronkénti bejárásnál gyorsítótársoronként egyszer okoznak hiányt (6,1%), oszloponkéntinél gyakorlatilag minden alkalommal (1 050 020 olvasási hiány 1 048 576 összegző olvasásra; a 95,2%-ot a program többi olvasása hígítja): egy oszlop gyorsítótársorai nem maradnak bent addig, amíg a következő oszlopnak szüksége lenne a szomszédaikra. Egy oszlop 1024 gyorsítótársort (64 KiB-ot) érint, többet, mint az egész 32 KiB-os L1, és ami még rosszabb, a tömbsorok egymástól 4096 bájtra vannak, így mind az 1024 gyorsítótársor ugyanarra az L1-csoportra képeződik le, amely közülük csak 8-at tud tárolni.

### Sorok és előbetöltés

A `stride.c` egy 64 MiB-os tömb minden *k*-adik `int`-jét érinti. Az elérések száma *k*-val csökken, de amíg minden gyorsítótársort még érintünk, az idő alig csökken, mert a memória egész sorokat szállít:

```console
$ gcc -O1 -o stride stride.c
$ taskset -c 0 ./stride
stride   accesses    time (ms)    ns/access
     1   16777216         11.7         0.70
     2    8388608          8.9         1.06
     4    4194304          7.9         1.89
     8    2097152          7.4         3.53
    16    1048576          6.9         6.58
    32     524288          6.0        11.38
    64     262144          3.1        11.73
   128     131072          1.4        10.71
   256      65536          0.7        11.04
   512      32768          0.4        11.09
  1024      16384          0.2        10.74
```

Az 1-es lépésköztől a 16-osig (64 bájtos soronként egy `int`) a tizenhatszor kevesebb elérés az időnek kevesebb mint a felét takarítja meg. Az idő csak a 32-es lépésközről a 64-esre feleződik, nem a 16-osról a 32-esre: 32-es lépésköznél (128 bájt) a program minden második sort érinti, de a processzor térbeli előbetöltője minden sor párját is betölti, amely a 128 bájtos blokkot teljessé teszi, így ugyanannyi adat halad át a memóriasínen. Figyeljük meg azt is, hogy egy elérés itt körülbelül 11 ns-ba kerül, tízszer kevesebbe, mint a véletlenszerű mutatókövetés 110–180 ns-a. Néhány száz bájtig terjedő lépésközöknél a hardveres előbetöltők felismerik a mintát, és előre betöltenek; az előbetöltők azonban nem lépik át a 4 KiB-os laphatárokat, és 1024-es lépésköznél (4 KiB) minden elérés új lapra esik, mégis csak 11 ns-ba kerül. Ennek oka a **memóriaszintű párhuzamosság**: ezek az elérések nem függenek egymástól, így a soron kívüli végrehajtású (out-of-order) mag egyszerre körülbelül tíz hiányt tart folyamatban, és 140 ns tíz átfedő hiány között elosztva körülbelül 14 ns hiányonként. A mutatókövetésnél minden elérésnek szüksége van az előző eredményére, így a hiányok nem fedhetik át egymást.

### Hamis megosztás

A `falseshare.c` két szálat futtat, amelyek két **különálló** számlálót növelnek egyenként 100 milliószor (atomi növeléssel, ahogy a statisztikai számlálókat általában szokás). A futások között az egyetlen különbség az, hogy a számlálók 8 vagy 64 bájtra vannak-e egymástól:

```console
$ gcc -O2 -pthread -o falseshare falseshare.c
$ ./falseshare near one
1 thread,  counters  8 bytes apart: 0.66 s
$ ./falseshare near
2 threads, counters  8 bytes apart: 2.93 s
$ ./falseshare far
2 threads, counters 64 bytes apart: 0.72 s
```

Két magon futó két szálnak ugyanannyi idő alatt kellene végeznie, mint egyetlen szálnak. Amikor a számlálók ugyanabban a 64 bájtos sorban voltak, a futás több mint négyszer annyi ideig tartott, mert minden növeléskor a sort kizárólagos tulajdonjoggal át kell vinni az egyik mag gyorsítótárából a másikéba. Ha a számlálókat egy sornyi távolságra helyezzük, visszatér a teljes sebesség.

### A RAM mint a lemez gyorsítótára

A lapgyorsítótár a RAM-ot a fájlok gyors szintjévé teszi. Egy 512 MiB-os fájlt olvasunk be közvetlenül a lapgyorsítótár kiürítése után, majd újra:

```console
$ head -c 512M /dev/urandom > big.bin
$ sync; echo 1 > /proc/sys/vm/drop_caches          # as root: empty the page cache
$ grep ^Cached /proc/meminfo
Cached:           189264 kB
$ dd if=big.bin of=/dev/null bs=1M
536870912 bytes (537 MB, 512 MiB) copied, 0.246671 s, 2.2 GB/s
$ grep ^Cached /proc/meminfo
Cached:           713816 kB
$ dd if=big.bin of=/dev/null bs=1M
536870912 bytes (537 MB, 512 MiB) copied, 0.0828352 s, 6.5 GB/s
```

Az első olvasás után a lapgyorsítótár a fájl 512 MiB-jával nőtt, és a második olvasás a RAM-ból jön, háromszor gyorsabban. Egy fizikai merevlemezen, amely 100–200 MB/s sebességgel olvas, az első olvasás néhány másodpercig tartana, ez 30–60-szoros különbség (szétszórt kis olvasásoknál akár százszoros vagy még nagyobb); egy felhőbeli gép virtuális lemezét maga a gazdagép is gyorsítótárazza. Rendszergazdai jogok nélkül a `dd if=big.bin iflag=nocache count=0` arra kéri a kernelt, hogy csak ezt a fájlt dobja ki a lapgyorsítótárból.

### A hívási mélység mérése

A `calldepth.py` minden függvényhíváskor és visszatéréskor feljegyzi a hívási mélységet, miközben a Python saját `json`, `ast` és `difflib` moduljai valódi munkát végeznek, majd szimulál egy ablakot, amely a *W* legutóbbi szintet gyors tárban tartja, mint egy regiszterablak: az ablak fölé eső hívás vagy alá eső visszatérés „kiírást” (spill) kényszerít ki:

```console
$ python3 calldepth.py
195,383 calls and returns recorded; depth from 0 to 76 (relative to the start)
 window W     spills   % of calls/returns
        1    195,382              100.00%
        2     30,134               15.42%
        3     19,033                9.74%
        4     13,638                6.98%
        5      9,887                5.06%
        6      7,794                3.99%
        7      6,193                3.17%
        8      4,862                2.49%
       12      2,190                1.12%
       16      1,124                0.58%
```

Bár a mélység a futás során 76 szinten belül mozog, egy 5 szintes ablak a hívások és visszatérések 95%-át lefedi, 8 szint pedig 97,5%-át: az egymásba ágyazás lassan változik. (A `python3 calldepth.py --trace depth.csv` elmenti a teljes nyomvonalat; a fenti ábra ebből 2500 egymást követő eseményt mutat.)

### Gyorsítótár-szimulátor

A `cachesim.py` tetszőleges méretű, sorméretű, asszociativitású és cserestratégiájú gyorsítótárat szimulál. Felbont egy címet a fenti direkt leképezésű példagyorsítótárra:

```console
$ python3 cachesim.py split 0x12345678
address 0x12345678 = tag 0x12 | index 209 | offset 0x1678 (word 1438 of the 4096 in the line)
```

Megerősíti a cachegrind eredményét a két bejárási sorrendre egy 32 KiB-os, 8 utas gyorsítótáron:

```console
$ python3 cachesim.py traverse 256
row by row      :    4096 misses of 65536 accesses, miss rate   6.2%
column by column:   65536 misses of 65536 accesses, miss rate 100.0%
```

Megmutatja, mi történne, ha az indexet a cím felső bitjeiből vennénk, egy olyan tömbre, amely befér a gyorsítótárba, és kétszer olvassuk végig:

```console
$ python3 cachesim.py order
a 128 KiB array read twice through a 256 KiB direct-mapped cache (64 B lines):
  tag | index | offset:   2048 misses, miss rate  3.1%
  index | tag | offset:   4096 misses, miss rate  6.2%
```

A szokásos sorrendnél a második menet minden alkalommal találatot ad; ha az index felül van, a tömb összes sora ugyanazért a gyorsítótársorért versenyez, és a második menet ugyanannyi hiányt okoz, mint az első.

Az asszociativitás megszünteti az ütközési hiányokat. Két tömb, amelyek pontosan egy gyorsítótárméretnyire vannak egymástól, és felváltva használjuk őket (`a[i] += b[i]`), egy direkt leképezésű gyorsítótárban minden eléréskor kiszorítja egymást:

```console
$ python3 cachesim.py assoc
direct-mapped     : miss rate 100.0%
2-way             : miss rate   6.2%
4-way             : miss rate   6.2%
fully associative : miss rate   6.2%
```

Az ábra sorméret-görbéje:

```console
$ python3 cachesim.py blocksize
36480 accesses, cache 4 KiB, 4-way set-associative
line     4 B (1024 lines): miss rate  87.3%
line     8 B ( 512 lines): miss rate  45.6%
line    16 B ( 256 lines): miss rate  24.7%
line    32 B ( 128 lines): miss rate  14.3%
line    64 B (  64 lines): miss rate   9.1%
line   128 B (  32 lines): miss rate  13.4%
line   256 B (  16 lines): miss rate  16.2%
line   512 B (   8 lines): miss rate  16.6%
line  1024 B (   4 lines): miss rate  16.3%
line  2048 B (   2 lines): miss rate  16.1%
line  4096 B (   1 lines): miss rate  16.0%
```

Végül a cserestratégiák, a számlálókon alapuló öregítéssel és Bélády optimumával együtt, két terhelésen:

```console
$ python3 cachesim.py replace
fully associative, 64 lines of 64 B; miss rates:
workload                               lru    fifo  random   aging     opt
loop of 56 lines + 16 hot lines      72.7%   41.7%   18.2%   44.7%    8.0%
loop of 40 lines + 32 hot lines       9.1%   19.9%   14.6%    9.3%    3.9%
```

Mindkét terhelés 72 különböző sort használ; a különbség az *újrafelhasználási távolság* (reuse distance). Az elsőben egy ciklusbeli sor két használata között körülbelül 68 különböző sort érintünk, többet, mint a gyorsítótár 64 sora, így az LRU mindig éppen azt a sort szorítja ki, amelyre legközelebb szükség lesz, és ez teljesít a legrosszabbul. A másodikban csak körülbelül 54-et, így az LRU bent tartja az egész ciklust, és az LRU, valamint az azt közelítő öregítés teljesít a legjobban. Az OPT megmutatja, milyen messze van minden gyakorlati stratégia az optimumtól.

## Laborfeladatok

1. **A saját géped hierarchiája.** Futtasd az `lscpu` parancsot és a sysfs-ciklust a saját számítógépeden, és számítsd ki minden szintre a csoportok száma × utak száma × sorméret szorzatot. Futtasd a `latency` (és a `latency huge`) programot, és jelöld be a lépcsőket. Hogyan viszonyulnak az L1-, L2-, L3- és RAM-késleltetéseid az előadás méréseihez? Váltsd át őket órajelciklusokra.
2. **A szükséges találati arány.** Az `amat.py` és a mért L1- és RAM-késleltetéseid segítségével keresd meg azt a találati arányt, amelynél egyetlen gyorsítótárszint mellett a memória csak 10%-kal tűnik lassabbnak a gyorsítótárnál. Ezután bővítsd az `amat.py`-t három szintre (L1, L2, L3, RAM) az előadás többszintű képlete szerint, és számítsd ki az átlagos elérési időt a három szinten 95%, 80% és 50% *lokális* találati arány mellett. Mekkora a globális hiányarány?
3. **Ciklussorrend.** Futtasd a `traverse` programot N = 512 … 8192 értékekre `-O0`, `-O2` és `-O3` mellett. Ábrázold az arányt a tömbméret függvényében, és jelöld be, hol nő túl a tömb az L2-n és az L3-on. Ezután írj mátrixszorzást (`C = A × B`) N = 1024-re i-j-k és i-k-j sorrendben, és mérd meg mindkettőt. Melyik belső ciklus halad végig a memórián?
4. **Cachegrind.** Használd a `valgrind --tool=cachegrind --cache-sim=yes` parancsot a mátrixszorzásod két sorrendjére. Magyarázd meg a D1-hiányok számát a sorméret segítségével. Próbáld ki a `--D1=32768,1,64` (direkt leképezésű L1) és a `--D1=32768,8,64` beállítást: mi változik, és miért?
5. **A direkt leképezésű példagyorsítótár.** Az előadás példagyorsítótárának geometriájára (32 bites címek, 1024 darab 16 KiB-os sor) add meg a `0x00000000`, `0x00004000`, `0x01000000` és `0xFFFFFFFC` címek tagjét, indexét és eltolását. Melyikek versenyeznek ugyanazért a sorért? Ellenőrizd a `cachesim.py split` paranccsal. Ezután számítsd ki, hány bit tagre és állapotbitre van szüksége összesen a gyorsítótárnak, az adatkapacitásának százalékában.
6. **Szimuláció.** A `cachesim.py` segítségével ismételd meg az `assoc` kísérletet úgy, hogy a két tömb 8 KiB + 64 bájtra legyen egymástól: mi történik a direkt leképezésű gyorsítótárral, és miért? Adj gyorsítótárméret-paramétert a `blocksize` kísérlethez, és ábrázold a görbét 2, 4 és 8 KiB-os gyorsítótárra. Hogyan mozdul el az optimum?
7. **Csere.** Valósítsd meg a `cachesim.py`-ban a klasszikus öregítési algoritmust (soronként egy 8 bites számláló, amelyet minden eléréskor jobbra léptetünk, találatkor pedig beállítjuk a legmagasabb helyiértékű bitjét), és hasonlítsd össze a „+1 / felezés” eljárással és az LRU-val. Ezután mutasd meg a Bélády-anomáliát: keress olyan elérési sorozatot, amelyre a FIFO 4 sorral több hiányt okoz, mint 3-mal.
8. **Hamis megosztás és lapgyorsítótár.** Módosítsd a `falseshare.c`-t úgy, hogy a két számláló 16, 32, 64 és 128 bájtra legyen egymástól. Hol tűnik el a lassulás? Ezután mérd meg egy nagy fájl hideg és meleg olvasását a saját lemezeden (`dd`, a kiszorításhoz `iflag=nocache`), és hasonlítsd össze a szorzót az előadásban látottal.

## Ellenőrző kérdések

1. Miért nem lehet egyetlen memória egyszerre nagy, gyors és olcsó? Rendezd a regisztereket, a gyorsítótárat, a RAM-ot, a lemezt és a szalagot sebesség, kapacitás és bájtonkénti ár szerint.
2. Írd fel egy kétszintű memória átlagos elérési idejének képletét, és számítsd ki $T_C$ = 3 ns, $T_{RAM}$ = 10 ns, H = 95%, valamint $T_C$ = 4 ns, $T_{RAM}$ = 120 ns, H = 95% esetén. Mit mutat az összehasonlítás?
3. Hogyan tudja egy a RAM kapacitásának 0,1%-át kitevő gyorsítótár az elérések 95%-át kiszolgálni? Nevezd meg a lokalitás négy okát, és definiáld az időbeli és a térbeli lokalitást.
4. A gyorsítótár melyik része használja ki az időbeli, és melyik a térbeli lokalitást?
5. Az előadás direkt leképezésű példagyorsítótárára (32 bites címek, 1024 sor, soronként 4096 darab 32 bites szó) vezesd le a tag-, az index- és az eltolásmező szélességét, valamint a gyorsítótár és a RAM méretét.
6. Írd le lépésről lépésre, mi történik olvasási találatkor, tiszta sorral járó olvasási hiánykor és módosított (dirty) sorral járó olvasási hiánykor. Mire való a V és a D bit?
7. Hasonlítsd össze az átíró (write-through) és a visszaíró (write-back) stratégiát. Melyiknek van szüksége a módosítási bitre, és miért használja a legtöbb mai gyorsítótár a visszaíró stratégiát?
8. Miért az eltolás feletti bitekből veszik a valódi gyorsítótárak az indexet, és nem a cím legfelső bitjeiből?
9. Magyarázd el a teljesen asszociatív gyorsítótárat. Miért nem használják nagy gyorsítótárakhoz? Hogyan egyesíti a csoportasszociatív gyorsítótár a két tervet?
10. Nevezd meg és magyarázd el a gyorsítótár-hiányok három fajtáját, és mondd meg, melyik tervezési változtatás csökkenti az egyes fajtákat.
11. Írd le az LRU-t, a FIFO-t, a véletlen cserét, a számlálókon alapuló öregítést és Bélády OPT algoritmusát. Miért nem használják az OPT-t a gyakorlatban, és miért hasznos mégis? Mi a Bélády-anomália?
12. Rögzített gyorsítótárméret mellett miért csökken először, majd nő a hiányarány, ahogy a sorméret nő? Miért szabványosak a 64 bájtos sorok?
13. Magyarázd el Scott Meyers soronkénti és oszloponkénti példáját. Miért lassabb az oszloponkénti ciklus, és miért nő a különbség a tömb méretével?
14. Mi a hamis megosztás, és hogyan kerülhető el? Hogyan kapcsolódik a gyorsítótár-koherenciához?
15. Milyen értelemben gyorsítótára a RAM a lemeznek? Mi a lapgyorsítótár (page cache), és mi ott a „találati arány” és a „hiánybüntetés”?

<details>
<summary><strong>Megoldókulcs (oktatóknak)</strong></summary>

1. A gyors memóriának (a CPU-lapkán lévő SRAM-nak) bitenként sok tranzisztor kell, és közel kell lennie a maghoz, ezért drága és kicsi; a sűrű, olcsó memória (DRAM, mágneses, optikai) lassabb. Sebesség és bájtonkénti ár: regiszterek > gyorsítótár > RAM > SSD/lemez > optikai lemez > szalag; a kapacitás fordított sorrendben.
2. 0,95 × 3 + 0,05 × 10 = 3,35 ns (közel a gyorsítótárhoz). 0,95 × 4 + 0,05 × 120 = 9,8 ns (a gyorsítótár 2,5-szerese). Minél nagyobb a szintek közötti sebességarány, annál közelebb kell lennie a találati aránynak 1-hez.
3. A programok a memóriájuknak egy kis, lassan változó részét használják. Okok: szekvenciális kód (PC++), szűk sávban maradó hívási mélység, rövid ciklusok, szekvenciális adatszerkezetek. Időbeli: a nemrég használt elemeket hamarosan újra használjuk. Térbeli: a nemrég használt elemek közelében lévőket hamarosan használjuk.
4. A nemrég használt sorok megtartása (és a cserestratégia) az időbeli lokalitást használja ki; az egész sorok betöltése (és az előbetöltés) a térbeli lokalitást.
5. Sor = 4096 × 4 B = 16 KiB → eltolás 14 bit; 1024 sor → index 10 bit; tag = 32 − 14 − 10 = 8 bit. Gyorsítótár = 1024 × 16 KiB = 16 MiB (4 Mi szó); RAM = 2³² B = 4 GiB.
6. Találat: az index kiválasztja a sort, V = 1 és a tag egyezik, az eltolás kiválasztja a szót. Hiány, tiszta sor: a sor betöltése a RAM-ból, a tag eltárolása, V = 1, D = 0, a szó kiadása. Hiány, módosított sor: előbb a régi sor visszaírása a RAM-ba, aztán mint az előbb. V a valódi adatot tartalmazó sorokat jelöli (bekapcsolás után mind érvénytelen); D a betöltés óta megváltozott sorokat jelöli, amelyeket csere előtt vissza kell írni.
7. Az átíró stratégia minden alkalommal a gyorsítótárba és a RAM-ba is ír (a RAM mindig naprakész, sok RAM-írás); a visszaíró csak a gyorsítótárba ír, a RAM-ot kiszorításkor frissíti (kell hozzá D, kevesebb RAM-írás). A visszaíró stratégia memória-sávszélességet takarít meg, és ez a szűkös erőforrás.
8. Azért, hogy az egymást követő blokkok egymást követő sorokra képeződjenek le: egy legfeljebb gyorsítótárméretű folytonos tartomány teljes egészében gyorsítótárazható. Ha az index felül van, a szomszédos blokkok egy soron osztoznak, és kiszorítják egymást (a szimulátorban: a szokásos sorrendnél a második menetben minden elérés találat, míg felül lévő indexnél a második menet ugyanannyi hiányt okoz, mint az első; a két menetre együtt 6,2% a 3,1%-kal szemben).
9. Bármely blokk bármelyik sorba kerülhet; a taget párhuzamosan hasonlítjuk össze az összes tárolt taggel. Soronként egy komparátor kell: drága területben és energiában, ezért csak kis gyorsítótárakhoz (TLB-khez) használják. Csoportasszociatív: az index kiválaszt egy csoportot, a taget a csoport n során belül hasonlítjuk össze: kevés komparátor, kevés ütközés.
10. Kötelező (első elérés; nagyobb sorok, előbetöltés), kapacitás (túl kicsi gyorsítótár; nagyobb gyorsítótár), ütközési (túl sok blokk egy csoportban; nagyobb asszociativitás).
11. LRU: a legrégebben használtat szorítja ki; FIFO: a legrégebben betöltöttet; véletlen; öregítés: számlálók közelítik az LRU-t (itt: minden eléréskor mind +1, a találat megfelezi a kort, a legöregebb megy); OPT: azt a sort szorítja ki, amelyet a legtávolabbi jövőben használunk. Az OPT-hez ismerni kellene a jövőt, de alsó korlátot ad, amelyhez a valódi stratégiákat mérjük. Bélády-anomália: FIFO esetén több sor több hiányt adhat.
12. A kis sorok hiányonként keveset hoznak (elpazarolt térbeli lokalitás, sok kötelező hiány); a nagy sorok miatt kevés sor van, így az újra használt adat kiszorul (elpazarolt időbeli lokalitás), és minden hiány tovább tart. A 64 B a tipikus programoknál egyensúlyban tartja a kettőt, és illeszkedik a DRAM sorozatos (burst) átviteleihez.
13. A C soronként tárolja a tömböket. A soronkénti bejárás minden 64 bájtos sor mind a 16 int-jét felhasználja (és `-O3`-nál lehetővé teszi a vektorutasításokat); az oszloponkénti soronként egy int-et használ, és minden eléréshez új sor kell. A kis tömbök az oszlopok között még bent maradnak a gyorsítótárban; ha a tömb nagyobb az L2-nél/L3-nál, minden oszloponkénti elérés a RAM-ig megy.
14. Két szál különböző változókat ír ugyanabban a gyorsítótársorban; a koherenciaprotokoll a sort kizárólagosan az író magnak adja, így a sor minden íráskor átpattog a magok között. Elkerülhető, ha a szálankénti adatokat kitöltéssel vagy a sorméretre (64 B) való igazítással külön-külön gyorsítótársorba tesszük.
15. Az operációs rendszer a nemrég olvasott fájladatokat a kihasználatlan RAM-ban tartja; az olyan olvasások, amelyek ott megtalálják az adatukat, találatok (nincs lemezelérés), a hiányok a lemezhez fordulnak. A hiánybüntetés egy lemezelérés, nanoszekundumok helyett milliszekundumok, ezért a lapgyorsítótár találati aránya még fontosabb.

**Megoldások a laborfeladatokhoz.** 1. labor: tipikus asztali értékek: L1 1–1,5 ns (4–5 ciklus), L2 3–5 ns, L3 10–20 ns, RAM 70–120 ns. 2. labor: 1,5 és 100 ns mellett H-nak körülbelül 99,85%-nak kell lennie; ezért van három szint. Az előadás késleltetéseivel és 95/80/50%-os lokális találati arányokkal T ≈ 2,8 ns (2,5 ns az egyszerűbb $T = H \cdot T_C + (1-H) \cdot T_{RAM}$ alakban, amely egy hiányért csak az alsó szint idejét számítja fel); a globális hiányarány 0,5%. 3. labor: az i-k-j, amelynek belső ciklusa B és C utolsó indexén fut végig. 4. labor: az oszloponkénti sorrend hiányai elérésenként egy közelében maradnak; a direkt leképezésű L1 ütközési hiányokat ad hozzá. 5. labor: a tagek 0x00, 0x00, 0x01 és 0xFF; az indexek 0, 1, 0 és 1023; tehát a `0x00000000` és a `0x01000000` versenyez a 0. sorért. Többletköltség: 1024 × (8 + 2) bit = 10 Kibit = 1,25 KiB 16 MiB adatra, 0,01% alatt. 6. labor: a plusz 64 bájttal a két tömb szomszédos sorokra képeződik le, és az ütközések eltűnnek: a direkt leképezésű gyorsítótár ekkor 6,25% hiányt ad, mint a 2 utas; ezek a megmaradó hiányok kapacitáshiányok, mert 16 KiB adatot járatunk körbe egy 8 KiB-os gyorsítótáron. 7. labor: a klasszikus példa az 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5 sorozat: FIFO-val 3 sorral 9, 4 sorral 10 hiány. 8. labor: a lassulás 64 bájtnál nagyrészt eltűnik; Intel processzorokon némi interferencia 128 bájtig megmaradhat, mert a térbeli előbetöltő sorpárokon dolgozik, ezért egyes könyvtárak 128 bájtra töltenek ki.

</details>

## Irodalom

Bélády, L. A. (1966). A study of replacement algorithms for a virtual-storage computer. *IBM Systems Journal, 5*(2), 78–101. https://doi.org/10.1147/sj.52.0078

Bélády, L. A., Nelson, R. A., & Shedler, G. S. (1969). An anomaly in space-time characteristics of certain programs running in a paging machine. *Communications of the ACM, 12*(6), 349–353. https://doi.org/10.1145/363011.363155

Denning, P. J. (2005). The locality principle. *Communications of the ACM, 48*(7), 19–24. https://doi.org/10.1145/1070838.1070856

Hennessy, J. L., & Patterson, D. A. (2019). *Computer architecture: A quantitative approach* (6th ed.). Morgan Kaufmann.

Hill, M. D., & Smith, A. J. (1989). Evaluating associativity in CPU caches. *IEEE Transactions on Computers, 38*(12), 1612–1630. https://doi.org/10.1109/12.40842

Intel Corporation. (2024). *Intel 64 and IA-32 architectures optimization reference manual*. https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html

Liptay, J. S. (1968). Structural aspects of the System/360 Model 85, II: The cache. *IBM Systems Journal, 7*(1), 15–21. https://doi.org/10.1147/sj.71.0015

Meyers, S. (2014, June). *CPU caches and why you care* [Conference presentation]. NDC Oslo 2014. https://vimeo.com/97337258

Smith, A. J. (1982). Cache memories. *ACM Computing Surveys, 14*(3), 473–530. https://doi.org/10.1145/356887.356892

Stallings, W. (2016). *Computer organization and architecture: Designing for performance* (10th ed.). Pearson.

Wilkes, M. V. (1965). Slave memories and dynamic storage allocation. *IEEE Transactions on Electronic Computers, EC-14*(2), 270–271. https://doi.org/10.1109/PGEC.1965.264263

Wulf, W. A., & McKee, S. A. (1995). Hitting the memory wall: Implications of the obvious. *ACM SIGARCH Computer Architecture News, 23*(1), 20–24. https://doi.org/10.1145/216585.216588

## További olvasnivaló

Drepper, U. (2007). *What every programmer should know about memory*. Red Hat. https://people.freebsd.org/~lstewart/articles/cpumemory.pdf

Ostrovsky, I. (2010, February). *Gallery of processor cache effects*. http://igoro.com/archive/gallery-of-processor-cache-effects/

Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating system concepts* (10th ed.). Wiley.
