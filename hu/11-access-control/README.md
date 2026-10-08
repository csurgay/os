# Hozzáférés-szabályozás: jogosultságok, ACL-ek és SELinux

*Operációs rendszerek előadás: ki mit tehet egy fájllal, egy eszközzel vagy egy porttal, és hogyan kényszeríti ezt ki a kernel: alanyok, objektumok és a referenciamonitor, a Unix tulajdonos/csoport/mindenki más jogosultságai, a setuid, a setgid és a sticky bit, a root és a capabilityk, a POSIX hozzáférés-szabályozási listák, valamint a MAC (mandatory access control) SELinuxszal, mindez kipróbálva Linuxon*

## Tanulási célok

Az [előző előadás](../10-file-systems/#inode-ok) megmutatta, hogy minden inode tárol egy tulajdonost, egy csoportot és néhány jogosultságbitet. Ez az előadás azt magyarázza el, mit kezd ezekkel a kernel, mivel egészíti ki őket, ha nem elegendők, és hogyan zárja korlátok közé egy modern linuxos szerver még a root jogokkal futó programokat is.

Az előadás végére a hallgatók képesek lesznek:

- a hozzáférés-szabályozást alanyok, objektumok, műveletek és egy referenciamonitor fogalmaival leírni, megkülönböztetni a policyt (a szabályrendszert) a mechanizmustól, és alkalmazni a legkisebb jogosultság elvét, a biztonságos alapértelmezés (fail-safe defaults) és a teljes közvetítés (complete mediation) elvét;
- elmagyarázni, milyen rétegeken halad át egy kérés egy szerveren (tűzfal, szolgáltatás, DAC, MAC), és miért van szüksége a mélységi védelemnek mindegyikre;
- megjósolni egy Unix-jogosultságellenőrzés eredményét, beleértve az „első illeszkedő osztály dönt” szabályt, valamint az `r`, a `w` és az `x` eltérő jelentését fájlokon és könyvtárakon;
- jogosultságokat beállítani a `chmod` paranccsal oktális és szimbolikus alakban, a nagy `X`-szel, és megfelelő `umask`-ot választani;
- elmagyarázni a setuid, a setgid és a sticky bitet, a négyjegyű oktális módokat az `ls -l` jelölésére (`s`/`S`, `t`/`T`) és vissza átváltani, valamint felmérni a setuid programok kockázatait;
- elmagyarázni, miért kerüli meg a root a jogosultságokat, és hogyan bontják részekre a root hatalmát a Linux capabilityk;
- közös könyvtárat tervezni setgid, `umask` és POSIX ACL-ek segítségével, és elmagyarázni az ACL-maszkot és az alapértelmezett ACL-eket;
- szembeállítani a DAC-ot és a MAC-ot (discretionary és mandatory access control), értelmezni egy SELinux contextet, elmagyarázni a type enforcementet, és a `restorecon` és `semanage` paranccsal kijavítani a gyakori címkézési hibákat;
- mindezt megvizsgálni Linuxon az `ls -l`, `stat`, `id`, `chmod`, `su`, `capsh`, `getcap`/`setcap`, `getfacl`/`setfacl` parancsokkal és a SELinux eszközeivel.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> hozzáférés-szabályozás, jogosultság, DAC, MAC, ACL, SELinux</summary>

- **Hozzáférés-szabályozás:** annak eldöntése, hogy ki mit tehet mivel, és a döntés betartatása. Olyan, mint egy portás, aki minden vendéget összevet a listával.
- **Jogosultság:** egyetlen „igen” ezen a listán, például „Anna olvashatja ezt a fájlt”.
- **DAC** (discretionary access control, belátás szerinti hozzáférés-szabályozás): a fájl tulajdonosa dönti el, a saját belátása szerint, hogy ki használhatja. Mint amikor a biciklidet annak adod kölcsön, akinek akarod.
- **MAC** (mandatory access control, kötelező hozzáférés-szabályozás): a rendszergazda által rögzített szabálykészlet dönt, és ezt még a tulajdonos sem írhatja felül. Mint egy kórház szabályai: az orvos nem viheti haza a betegek kartonjait, még azokat sem, amelyeket ő maga írt.
- **ACL** (access control list, hozzáférés-szabályozási lista): egy fájlhoz csatolt lista: „Anna: olvasás; Béla: olvasás és írás; a csoport: semmi”.
- **SELinux** (Security-Enhanced Linux, biztonságilag megerősített Linux): a Red Hat-családba tartozó Linux-disztribúciók MAC-rendszere.

</details>

## Miért kell hozzáférés-szabályozás?

Egy többfelhasználós, egyszerre sok programot futtató számítógép sok tulajdonos adatait tárolja, és egymás mellett futtat különböző mértékben megbízható programokat. A [történeti előadás](../01-historic-evolution/#vii-a-programok-osztoznak-a-memórián-védelem-és-virtuális-memória) megmutatta, hogy a védelemre attól a pillanattól szükség volt, hogy több program osztozott egy gépen; a [virtuális memóriáról szóló előadás](../09-virtual-memory/#védelem) bemutatta, hogyan tartja távol a hardver a folyamatokat egymás memóriájától. A fájlok, az eszközök és a hálózati portok viszont minden folyamatnál tovább élnek, és szándékosan közösek, ezért finomabb szabályok kellenek hozzájuk: nem az, hogy „senki más”, hanem az, hogy „ezek az emberek, ezekre a műveletekre”.

Minden hozzáférés-szabályozási döntésnek ugyanaz a három része van:

- az **alany** (subject): a cselekvő fél, egy operációs rendszerben mindig egy folyamat, amely egy felhasználó nevében jár el;
- az **objektum** (object): a passzív fél: fájl, könyvtár, eszköz, hálózati port, egy másik folyamat, egy üzenetsor;
- a **művelet** (action, hozzáférési mód): olvasás, írás, végrehajtás, törlés, port lefoglalása, szignál küldése.

Lampson (1974) egy rendszer összes döntését **hozzáférési mátrixként** (access matrix) írta le: alanyonként egy sor, objektumonként egy oszlop, és minden cellában a megengedett műveletek. A mátrix túlságosan nagy és ritka ahhoz, hogy egészében tárolják, ezért a rendszerek szeletekben tárolják. Ha minden **oszlopot** az objektumával együtt tárolunk, **hozzáférés-szabályozási listát** (ACL) kapunk: „X fájl: Anna olvashatja, Béla olvashatja és írhatja”. Ha minden **sort** az alanyával együtt tárolunk, **capability listát** (C-listát) kapunk: „Anna birtokában van: X olvasása, Y írása”. A Unix-jogosultságok és az ACL-ek oszlopszeletek; egy megnyitott fájlleíró viszont, amelyet a folyamat további ellenőrzés nélkül használhat, capabilityként viselkedik.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> alany, objektum, művelet, hozzáférési mátrix, capability list</summary>

- **Alany:** aki tenni akar valamit: egy futó program, amely egy ember helyett dolgozik.
- **Objektum:** amivel tenni akarja: egy fájl, egy mappa, egy nyomtató, egy hálózati port.
- **Művelet:** hogy pontosan mit akar: olvasni, módosítani, futtatni, törölni.
- **Hozzáférési mátrix:** egy óriási táblázat, a sorokban az emberekkel, az oszlopokban a dolgokkal, és minden mezőben az, hogy az adott ember mit tehet az adott dologgal.
- **Capability list:** ugyanez az információ emberenként tárolva, mint egy kulcscsomó: minden kulcs egy ajtót nyit, egy bizonyos célra.

</details>

### A referenciamonitor

A döntést meghozó komponens a **referenciamonitor** (reference monitor; Anderson, 1972). Bármilyen formát ölt is, három tulajdonsággal kell rendelkeznie ahhoz, hogy megbízhassunk benne: **mindig meghívódik** (egyetlen hozzáférési út sem kerülheti meg; Saltzer és Schroeder, 1975, ezt *teljes közvetítésnek*, complete mediation nevezi), **nem lehet belepiszkálni** (tamper-proof: az általa ellenőrzött programok nem módosíthatják), és **elég kicsi ahhoz, hogy ellenőrizni lehessen**. Linuxban a referenciamonitor a kernel része: egy folyamat csak rendszerhíváson, például az `open` hívásán keresztül férhet hozzá egy fájlhoz, a rendszerhívás kernelmódban fut, ahol a felhasználói kód nem avatkozhat be ([5. előadás](../05-interrupts/#felhasználói-mód-és-kernelmód)), és a kernel ott ellenőrzi a jogosultságokat. Az elutasított kérés az `EACCES` („Permission denied”, hozzáférés megtagadva) vagy az `EPERM` („Operation not permitted”, a művelet nem engedélyezett) hibakóddal tér vissza.

Érdemes külön választani a **policyt**, vagyis azt, *hogy mi* megengedett (ezt a fájlt a `cons` csoport olvashatja), és a **mechanizmust**, vagyis azt, *hogyan* kényszerítjük ki (a kernel az `open` pillanatában összeveti a folyamat csoportazonosítóit a fájl csoportjával). Egy mechanizmus sokféle policyt kikényszeríthet, és a policy a kernel módosítása nélkül változhat.

Saltzer és Schroeder (1975) nyolc tervezési elvet sorolt fel, amelyek ma is a biztonságos rendszertervezés ellenőrzőlistáját adják. Közülük négy végigkíséri ezt az előadást:

- **A legkisebb jogosultság elve** (least privilege): minden program és minden felhasználó csak azokkal a jogokkal rendelkezzen, amelyek a feladatához szükségesek, és csak addig, ameddig szükségesek. A setuid programok és a capabilityk ennek eszközei, a root pedig az ellentéte.
- **Biztonságos alapértelmezés** (fail-safe defaults): az alapértelmezett válasz a „nem”; a hozzáférést kifejezetten meg kell adni. A SELinux mindent megtagad, amit egyetlen szabály sem enged meg.
- **Teljes közvetítés** (complete mediation): minden hozzáférést ellenőrizni kell, nem csak az elsőt.
- **Pszichológiai elfogadhatóság** (psychological acceptability): azt a mechanizmust, amelyet a felhasználók túl bonyolultnak találnak, kikapcsolják vagy megkerülik; a [kognitív ergonómiáról szóló előadás](../03-cognitive-ergonomics/) a biztonságra is érvényes. A SELinux a tankönyvi példa: hibaüzeneteinek leggyakoribb „javítása” a kikapcsolása.

### Mélységi védelem

Egy szerveren egyetlen ellenőrzésben sem bízunk meg önmagában. A hálózatról egy webszerverhez érkező kérés egymástól független rétegek sorozatán halad át, és az első olyan rétegnél elutasítják, amelyik nemet mond:

![Balra: öt réteg egymás fölött, alul a tűzfal, majd a szolgáltatás, a DAC és a MAC, legfelül a végrehajtás. Jobbra: egy alany (a httpd folyamat) egy objektumon (index.html vagy a 80-as port) végzendő műveletet kér a kernelben lévő referenciamonitortól; a monitor a policyhoz fordul, engedélyez vagy EACCES/EPERM hibával elutasít, és naplózza az elutasításokat](access-path.svg)

1. A **tűzfal** (firewall) dönti el, hogy egyáltalán mely gépek mely portokat érhetik el.
2. Maga a **szolgáltatás** (a démon, például az Apache webszerver vagy a MariaDB adatbázis-szerver) a saját konfigurációját alkalmazza: milyen URL-eket szolgál ki, milyen adatbázis-felhasználók léteznek, és mit kérdezhetnek le.
3. **DAC**: a kernel ellenőrzi azoknak a fájloknak és könyvtáraknak a Unix-jogosultságait és ACL-jeit, amelyekhez a szolgáltatás hozzányúl, annak a felhasználói azonosítónak a nevében, amellyel a szolgáltatás fut (például `apache`).
4. **MAC**: a kernel egy rendszerszintű policyt ellenőriz, például a SELinuxét, amely azt is megtagadhatja, amit a DAC megenged.
5. A művelet csak ezután **hajtódik végre**.

Minden réteg a többi meghibásodása ellen véd. Ha egy támadó hibát talál a webszerverben (2. réteg), és tetszőleges kódot futtat vele, a DAC akkor is távol tartja az eltérített folyamatot más felhasználók fájljaitól, a MAC pedig mindentől, ami nem webes tartalom, például az adatbázisfájloktól, még akkor is, ha azok tévedésből mindenki számára olvashatók. Linuxban a 3. réteget a 4. előtt ellenőrzi a kernel: a DAC által elutasított kérés el sem jut a SELinuxig (Wright et al., 2002).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> referenciamonitor, EACCES, EPERM, policy, mechanizmus, legkisebb jogosultság elve, teljes közvetítés, sérthetetlenség, biztonságos alapértelmezés, pszichológiai elfogadhatóság, mélységi védelem, tűzfal, démon</summary>

- **Referenciamonitor:** az őr, aki minden egyes belépést ellenőriz. Mindent ellenőriznie kell, megvesztegethetetlennek kell lennie, és elég egyszerűnek ahhoz, hogy át lehessen vizsgálni.
- **EACCES, EPERM:** az a két hibakód, amelyet a kernel elutasításkor visszaad: „Permission denied” (a jogosultságbitek nemet mondanak) és „Operation not permitted” (maga a művelet foglalt, például a tulajdonosnak vagy a rootnak).
- **Policy:** a szabályok: ki mit tehet. **Mechanizmus:** a gépezet, amely betartatja a szabályokat. A policy olyan, mint egy kollégium házirendje, a mechanizmus olyan, mint a zár az ajtón.
- **A legkisebb jogosultság elve:** mindenki csak azokat a kulcsokat kapja meg, amelyekre tényleg szüksége van. A takarító az irodák kulcsát kapja meg, nem a széfét.
- **Teljes közvetítés, sérthetetlenség:** az őr minden látogatást ellenőriz, nem csak az elsőt, és senki sem vesztegetheti meg vagy cserélheti le.
- **Biztonságos alapértelmezés:** ha a lista nem mond semmit, a válasz „nem”.
- **Pszichológiai elfogadhatóság:** a túl idegesítő biztonsági megoldást kikapcsolják, ezért annyira kényelmesnek kell lennie, hogy együtt lehessen élni vele.
- **Mélységi védelem:** több, egymástól független zár egymás után, hogy egy feltörése ne legyen elég. Mint egy vár vizesárokkal, várfallal és öregtoronnyal.
- **Tűzfal:** egy szűrő a hálózati kapcsolaton, amely csak bizonyos fajta forgalmat enged át.
- **Démon** (daemon): a háttérben futó, szolgáltatást nyújtó program, például egy webszerver (`httpd`) vagy egy adatbázis-szerver (`mysqld`).

</details>

## Felhasználók, csoportok és a folyamat identitása

A kernel nem ismer neveket, csak számokat. Minden felhasználónak van egy **felhasználói azonosítója** (UID, user ID), egy **elsődleges csoportja** (GID, group ID) és tetszőleges számú **kiegészítő csoportja** (supplementary groups). A nevek és a számok közötti megfeleltetést az `/etc/passwd` és az `/etc/group` fájl tárolja (vagy egy címtárszolgáltatás, például LDAP); az `id` parancs megmutatja:

```console
$ id cons1
uid=30036(cons1) gid=30036(cons1) groups=30036(cons1),30002(cons)
```

A 0-s UID a **root**, a rendszergazda. A legtöbb disztribúció minden felhasználónak ad egy vele azonos nevű **saját csoportot** (private group) elsődleges csoportként (itt `cons1`), a közös csoportok (itt `cons`) pedig kiegészítő csoportok.

Egy **folyamat** annak a felhasználónak az identitását hordozza, aki elindította: a `fork`-kor a szülőjétől másolja, bejelentkezéskor pedig beállítják. Valójában több azonosítót is hordoz (Kerrisk, 2010, ch. 9):

- a **valós UID és GID** (real UID/GID): ki indította a folyamatot;
- az **effektív UID és GID**, a kiegészítő csoportokkal együtt: kinek a jogait használja a folyamat a jogosultságellenőrzésekben;
- a **mentett set-user-ID** (saved set-user-ID): az effektív UID másolata, amelynek segítségével egy setuid program ideiglenesen lemondhat a jogairól, majd visszaveheti őket.

Általában a valós és az effektív azonosítók megegyeznek. Az alább ismertetett setuid és setgid bit teszi őket különbözővé. A **fájloknak** pedig egy tulajdonosuk (egy UID) és egy csoportjuk (egy GID) van az inode-jukban, valamint jogosultságbitjeik, amelyeket a kernel a folyamat effektív azonosítóival vet össze.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> UID, GID, elsődleges csoport, kiegészítő csoport, saját csoport, root, valós és effektív azonosító, mentett set-user-ID</summary>

- **UID** (user ID, felhasználói azonosító) és **GID** (group ID, csoportazonosító): azok a számok, amelyekkel a számítógép egy felhasználót, illetve egy csoportot jelöl. A nevek csak az embereknek kellenek.
- **Elsődleges csoport:** az a csoport, amelyhez a felhasználó új fájljai alapértelmezésben tartoznak. **Kiegészítő csoportok:** további csoportok, amelyeknek a felhasználó tagja, mint a további klubtagságok.
- **Saját csoport:** egy pontosan egytagú csoport, a felhasználóról elnevezve. Ettől maradnak a felhasználó fájljai alapértelmezésben a sajátjai.
- **Root:** a rendszergazdai fiók, a 0-s számú, amely (majdnem) bármit megtehet.
- **Valós azonosító, effektív azonosító:** ki indított el egy programot, és kinek a jogait használja a program éppen most. Általában ugyanaz a személy; egy „setuid” program a tulajdonosa jogait kölcsönzi.
- **Mentett set-user-ID:** a kölcsönkapott identitás tartalék példánya: így a program egy időre félreteheti a kölcsönkapott jogokat, és később újra felveheti őket.

</details>

## Unix-jogosultságok: DAC (discretionary access control)

### Tulajdonos, csoport, mindenki más: az első egyezés dönt

Egy fájl kilenc jogosultságbitje három hármast alkot az `r` (read, olvasás), a `w` (write, írás) és az `x` (execute, végrehajtás) bitből: egyet a **tulajdonosnak** (user, `u`), egyet a **csoportnak** (group, `g`) és egyet **mindenki másnak** (others, `o`). Ez egy nagyon tömör, pontosan háromelemű ACL. A kernel nem kombinálja őket: **egyetlen** hármast választ ki, és csak azt használja (Kerrisk, 2010, ch. 15):

![Öt kérdésből álló folyamatábra: rendelkezik-e a folyamat a CAP_DAC_OVERRIDE capabilityvel, ő-e a tulajdonos, van-e rá vonatkozó névvel megadott ACL-bejegyzés, tagja-e egy illeszkedő csoportnak, különben mindenki más; minden igen egy döntési dobozhoz vezet, és egy példa mutatja, hogy a -------rwx módú fájl tulajdonosa nem fér hozzá, mindenki más viszont olvashatja](dac-check.svg)

1. A `CAP_DAC_OVERRIDE` capabilityvel rendelkező folyamat, ami általában a root, kihagyja az ellenőrzést (erről alább bővebben).
2. Ha a folyamat effektív UID-je a fájl tulajdonosa, akkor a **tulajdonos** bitjei döntenek, és semmi mást nem néz meg a kernel.
3. Különben, ha az effektív GID vagy valamelyik kiegészítő csoport a fájl csoportja, akkor a **csoport** bitjei döntenek.
4. Különben a **mindenki más** bitjei döntenek.

Az ábrán van még egy lépés (a 3.), és a 4. lépés is szélesebb; mindkettő az ACL-ekhez tartozik, és [később](#posix-hozzáférés-szabályozási-listák) tárgyaljuk őket. Az „első egyezés, aztán vége” szabály következménye sok felhasználót meglep: a jogok **nem** adódnak össze. Egy `john` tulajdonában lévő, `-------rwx` módú fájlt mindenki olvashat, kivéve `john`-t (és a fájl csoportjának tagjait): `john` a 2. lépésnél illeszkedik, és a tulajdonos bitjei üresek. A [linuxos rész](#az-első-egyezés-dönt) ezt meg is mutatja. A tulajdonos azonban nincs véglegesen kizárva: a módot csak a tulajdonos (vagy a root) változtathatja meg, így `john` a `chmod` paranccsal visszaadhatja magának a jogokat. A tulajdonjog a döntés joga, és pontosan ezt jelenti a DAC nevében a *discretionary* („belátás szerinti”) jelző.

### Mit jelent az r, a w és az x fájlokon és könyvtárakon?

Közönséges fájlnál a jelentés kézenfekvő: a tartalom olvasása, a tartalom módosítása, futtatás programként. A könyvtár olyan fájl, amely neveket képez le inode-számokra ([10. előadás](../10-file-systems/#könyvtárak)), és a bitjei erre a névlistára vonatkoznak:

| bit | fájlon | könyvtáron |
| --- | --- | --- |
| `r` | a tartalom olvasása | a benne lévő nevek listázása (`ls`), de `x` nélkül az inode-jaik nem (az `ls -l` `?`-et mutat) |
| `w` | a tartalom módosítása (csonkolása is) | bejegyzések létrehozása, törlése és átnevezése benne, **csak az `x`-szel együtt** |
| `x` | végrehajtás programként vagy szkriptként | áthaladás rajta: használat egy elérési útban, `cd` bele, a benne lévő nevek inode-jainak elérése |

Ebből három szabály következik, mindhármat megmérjük a [linuxos részben](#könyvtárak-r-w-és-x):

- **Az `x` a könyvtár kulcsa.** Nélküle semmi sem érhető el benne, még akkor sem, ha ismerjük a nevét; csak `x`-szel (`--x`) egy fájl megnyitható, ha tudjuk a nevét, de a könyvtár nem listázható: ez a „titkos” könyvtár.
- **A `w` egy könyvtáron `x` nélkül haszontalan.**
- **Egy fájl törlése a könyvtár módosítása, nem a fájlé.** Az `rm`-hez `w` és `x` kell a könyvtáron, a fájlon viszont semmilyen jogosultság: egy felhasználó olyan fájlt is törölhet, amelyet el sem tud olvasni (az `rm` megerősítést kér, ha a fájl írásvédett, de a kernelt ez nem érdekli). Az alább ismertetett sticky bit közös könyvtárak esetén bezárja ezt a rést.

Egy fájl eléréséhez a folyamatnak az út mentén **minden** könyvtáron `x` jog kell, majd a megfelelő bit magán a fájlon. Ezért véd egy `700` módú saját könyvtár (home directory) minden benne lévő fájlt, akármilyen is a saját módjuk.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> tulajdonos, csoport, mindenki más, rwx, első egyezés</summary>

- **Tulajdonos, csoport, mindenki más:** minden fájlnál háromféle ember van: az egyetlen személy, akié a fájl, a fájl csoportjának tagjai, és mindenki más.
- **r, w, x:** olvasás, írás, végrehajtás (futtatás). Mappánál: a nevek listájának megnézése, a lista módosítása (hozzáadás, eltávolítás, átnevezés), és belépés a mappába.
- **Első egyezés:** a számítógép megállapítja, melyik fajtához tartozol, csak annak a fajtának a jogait nézi meg, és megáll. Ha te vagy a tulajdonos, a „mindenki más” jogai nem segítenek rajtad.

</details>

### chmod, chown, chgrp

A `chmod` kétféle jelöléssel állítja be a módot (Linux man-pages project, n.d.-c):

- **Oktális** jelöléssel, hármasonként egy számjeggyel, $r = 4$, $w = 2$, $x = 1$ súlyokkal: a `chmod 640 f` eredménye `rw-r-----` ($6 = 4 + 2$, $4$, $0$). Minden számjegy egy teljes hármast állít be, így az eredmény nem függ a régi módtól.
- **Szimbolikus** jelöléssel, osztályonként (`u`, `g`, `o`, illetve `a` mindenkire) és bitenként, `+` (hozzáadás), `-` (elvétel) vagy `=` (pontos beállítás) jellel: `chmod u+x,g-r,o+r f`. Csak a megnevezett bitek változnak.

Hasznos szimbolikus betű a nagy **`X`**: csak könyvtárakon és olyan fájlokon állítja be az `x`-et, amelyek valakinek már futtathatók. A `chmod -R go+rX dir` egy egész fát olvashatóvá és bejárhatóvá tesz anélkül, hogy minden adatfájlt futtathatóvá tenne, amit a `go+rx` megtenne.

Egy fájl módját csak a tulajdonosa (vagy a root) változtathatja meg. A `chown user:group f` a tulajdonost és a csoportot módosítja; Linuxon csak a root adhat át egy fájlt másnak (különben a felhasználók kijátszhatnák a lemezkvótákat, vagy fájlokat csempészhetnének másokhoz), a tulajdonos viszont a `chgrp` paranccsal bármely olyan csoportra átállíthatja a fájl csoportját, amelynek ő maga tagja.

### Az umask

Amikor egy program fájlt hoz létre, az `open` vagy az `mkdir` hívásban egy módot kér: megállapodás szerint adatfájloknál `666`-ot (`rw-rw-rw-`), könyvtáraknál és futtatható fájloknál `777`-et. A folyamat **umask**-ja (user file-creation mask, fájllétrehozási maszk) biteket vesz el ebből a kérésből: az új mód a kért mód AND NOT umask. A szokásos `022` umaskkal a csoport és mindenki más elveszíti a `w` jogot: a fájlok `644`, a könyvtárak `755` módot kapnak. `002` mellett a csoport megtartja a `w`-t (`664`, `775`), ami saját csoportok és közös projektkönyvtárak esetén megfelelő; `077` mellett a tulajdonoson kívül senkinek sem marad semmi (`600`, `700`). Az umaskot a gyermekfolyamatok öröklik; a shell beépített `umask` parancsával, bejelentkezéskor pedig az `/etc/login.defs` fájlban és a `pam_umask` modullal lehet beállítani. Az Ubuntu például általában `022`-t használ, de `002`-t azoknak a felhasználóknak, akiknek az elsődleges csoportja a saját csoportjuk.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> chmod, oktális, szimbolikus mód, nagy X, chown, chgrp, umask</summary>

- **chmod** („change mode”, módváltás): a parancs, amely beállítja egy fájl jogosultságait.
- **Oktális jelölés:** három igen/nem kapcsolóból álló csoportonként egyetlen 0 és 7 közötti számjegy: az olvasás 4-et ér, az írás 2-t, a végrehajtás 1-et, és ezeket összeadjuk. `7` = mindhárom, `6` = olvasás és írás, `4` = csak olvasás.
- **Szimbolikus jelölés:** ugyanez betűkkel: `u+x` = „adj végrehajtási jogot a tulajdonosnak”, `go-w` = „vedd el az írási jogot a csoporttól és mindenki mástól”.
- **Nagy X:** „végrehajtás, de csak ahol értelme van”: mappáknál és programoknál, dokumentumoknál nem.
- **chown, chgrp:** egy fájl tulajdonosának, illetve csoportjának megváltoztatása.
- **umask:** egy szűrő, amely minden új fájltól automatikusan elvesz bizonyos jogosultságokat. A `022` azt jelenti: „a csoportnak és mindenki másnak sose adj írási jogot, hacsak később külön nem kérik”.

</details>

### A root és a capabilityk

A szuperfelhasználó (UID 0) jogait a kernel egyáltalán nem veti össze a jogosultságbitekkel: bármely fájlt olvashat és írhat, és bármely könyvtárba beléphet. Csak a végrehajtásnál marad egy kis feltétel: a root csak akkor futtathat egy fájlt, ha annak legalább az egyik `x` bitje be van állítva, nehogy tévedésből adatfájlokat indítson el programként.

A Linux 2.2 óta ez a hatalom nem egyetlen kapcsoló, hanem **capabilityk** halmaza, és mindegyik capability a privilegizált műveletek egy-egy osztályát fedi le (Linux man-pages project, n.d.-b). Az itt fontosak:

| capability | mit enged meg |
| --- | --- |
| `CAP_DAC_OVERRIDE` | az olvasási, írási és végrehajtási bitek figyelmen kívül hagyása (végrehajtás: ha bármelyik `x` bit be van állítva) |
| `CAP_DAC_READ_SEARCH` | a fájlok olvasási bitjeinek, valamint a könyvtárak olvasási és keresési bitjeinek figyelmen kívül hagyása |
| `CAP_FOWNER` | bármely fájl tulajdonosaként való fellépés (`chmod`, ACL-ek beállítása, a sticky bit figyelmen kívül hagyása) |
| `CAP_CHOWN` | bármely fájl tulajdonosának és csoportjának megváltoztatása |
| `CAP_SETUID`, `CAP_SETGID` | a folyamat UID-jeinek és GID-jeinek megváltoztatása (ezt használja a `login`, a `su` és a `sudo`) |
| `CAP_NET_BIND_SERVICE` | 1024 alatti TCP/UDP portok lefoglalása (bind) |
| `CAP_KILL` | szignál küldése bármely folyamatnak |
| `CAP_SYS_ADMIN` | nagy, vegyes gyűjtemény: mount, swapon, sethostname és még sok más |

A rootként futó folyamat általában mindegyikkel rendelkezik; a kernel a capabilityt ellenőrzi, nem az UID-t. Ez teszi lehetővé a legkisebb jogosultság elvének alkalmazását a rendszerszolgáltatásokra: egy webszerver megtarthatja csak a `CAP_NET_BIND_SERVICE` capabilityt, hogy megnyithassa a 80-as portot, egy mentőprogram pedig csak a `CAP_DAC_READ_SEARCH` capabilityt, hogy mindent elolvashasson, de semmit se módosíthasson. Egy folyamat lemondhat capabilitykről (`capsh --drop=…`, vagy a `CapabilityBoundingSet=` beállítás egy systemd unitban), és capabilityket egy programfájlhoz is lehet csatolni (`setcap`, file capability), amely aztán megadja őket annak, aki futtatja: ez a setuid root finomabb szemcsézettségű helyettesítője. A [linuxos rész](#a-root-a-capabilityk-miatt-root) bemutat egy root shellt, amely nem tud elolvasni egy fájlt, mert lemondott két capabilityről, és egy közönséges felhasználót, aki egyetlen capabilityvel elolvassa a root fájlját.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> szuperfelhasználó, capability, CAP_DAC_OVERRIDE, bounding set, file capability</summary>

- **Szuperfelhasználó:** a root másik neve.
- **Capability:** a root hatalmának egyetlen darabja, például „figyelmen kívül hagyhatja a fájljogosultságokat” vagy „használhatja az 1024 alatti hálózati portokat”. Egyetlen mesterkulcs helyett különleges kulcsok készlete, amelyeket egyenként lehet kiosztani.
- **CAP_DAC_OVERRIDE:** az a különleges kulcs, amely a jogosultságaitól függetlenül minden fájlt kinyit.
- **Bounding set:** azoknak a capabilityknek a felső korlátja, amelyeket egy program és minden gyermeke valaha megkaphat. Ha szűkítjük, az olyan, mintha végleg levennénk kulcsokat a karikáról.
- **File capability:** egy programfájlra ragasztott különleges kulcs: aki azt a programot futtatja, a futás idejére megkapja azt az egy kulcsot, és semmi mást.

</details>

## Speciális bitek: setuid, setgid és sticky

Egy fájl módjában nem kilenc, hanem tizenkét jogosultságbit van. A három hármas előtt három speciális bit áll, az inode teljes, 16 bites módszava pedig a felső négy bitjében a fájl típusát is tárolja:

![A 16 bites módszó: négy bit fájltípus, majd a setuid, a setgid és a sticky bit 4, 2, 1 súllyal, aztán a tulajdonos, a csoport és mindenki más rwx bitjei, szintén 4, 2, 1 súllyal; a példa bitjei az oktális 7743-at adják, amelyet az ls -l -rwsr-S-wt alakban mutat; alatta egy táblázat arról, hogyan jeleníti meg az ls egy speciális bitet az x helyén: -, x, S vagy s, T vagy t](mode-bits.svg)

| bit | oktális | futtatható fájlon | könyvtáron |
| --- | --- | --- | --- |
| **setuid** (SUID) | `4000` | a **tulajdonos** effektív UID-jével fut, például `/usr/bin/passwd` | Linuxon nincs hatása |
| **setgid** (SGID) | `2000` | a **csoport** effektív GID-jével fut | az új fájlok és alkönyvtárak **öröklik a könyvtár csoportját** (az alkönyvtárak a setgid bitet is) |
| **sticky** | `1000` | Linuxon nincs hatása (történetileg: a programkód maradjon a swapban) | közös könyvtárban csak a **fájl tulajdonosa** (vagy a könyvtáré, vagy a root) törölheti vagy nevezheti át a fájlt, például `/tmp` |

### Olvasásuk és beállításuk

Az `ls -l` kimenetében nincs külön oszlop a speciális biteknek. Mindegyik egy `x` helyén osztozik: a setuid a tulajdonosén, a setgid a csoportén, a sticky a mindenki másén. A kisbetű azt jelenti, hogy mindkét bit be van állítva, a nagybetű azt, hogy csak a speciális bit:

| | `x` nincs beállítva | `x` be van állítva |
| --- | --- | --- |
| nincs speciális bit | `-` | `x` |
| setuid vagy setgid beállítva | `S` | `s` |
| sticky beállítva | `T` | `t` |

A nagy `S` vagy `T` általában hibára utal: egy olyan fájlon, amelyet senki sem futtathat, a setuid bit semmit sem csinál.

Oktálisan a speciális bitek egy negyedik számjegyet alkotnak a másik három előtt, ugyanazokkal a súlyokkal: setuid $4$, setgid $2$, sticky $1$. Egy módsztring átváltásakor minden hármast a $4 2 1$ súlyokkal olvasunk ki, a speciális biteket pedig a vezető számjegybe gyűjtjük. Két példa:

- `rwsr-S-wt`: a tulajdonosé `rws` = $4 + 2 + 1 = 7$, setuiddal; a csoporté `r-S` = $4$, setgiddel; mindenki másé `-wt` = $2 + 1 = 3$, sticky bittel. A speciális számjegy $4 + 2 + 1 = 7$, így a mód `7743`.
- `-wxrwsr-T`: tulajdonos `-wx` = $3$, csoport `rws` = $7$ setgiddel, mindenki más `r-T` = $4$ sticky bittel; a speciális számjegy $2 + 1 = 3$: `3374`.

Fordítva: a `chmod 1777 dir` eredménye `drwxrwxrwt`, a `/tmp` módja, a `chmod 7640 f` eredménye pedig `-rwSr-S--T`: mindhárom speciális bit be van állítva, de egyik sem hatásos. A [linuxos rész](#chmod-umask-és-a-speciális-bitek) ezeket a `stat` paranccsal ellenőrzi.

### setuid: a tulajdonos identitásának kölcsönvétele

A felhasználók a `passwd` paranccsal maguk változtatják meg a jelszavukat, a jelszó-hasítóértékek (hashek) azonban az `/etc/shadow` fájlban vannak, amelyet csak a root írhat. A megoldás a setuid bit: az `/usr/bin/passwd` a root tulajdonában van, és `4755` (`-rwsr-xr-x`) módú. Amikor bármely felhasználó futtatja, a kernel az új folyamat effektív UID-jét a fájl tulajdonosára, a rootra állítja, a valós UID viszont a felhasználóé marad. A program a valós UID-ből tudja meg, *kinek* a jelszavát kell megváltoztatnia, az effektív UID-nek köszönhetően pedig *képes* megváltoztatni. A `su`, a `sudo`, a `mount` és (régebbi rendszereken) a `ping` ugyanígy működik.

Egy setuid-root program tehát rés a felhasználókat a roottól elválasztó falon, és nagy gonddal kell megírni. A támadó által választott környezetben fut: az argumentumai, a környezeti változói, a nyitott fájlleírói, az aktuális könyvtára és az erőforráskorlátai mind a hívótól származnak. A kernel és a C-könyvtár segít: setuid programok esetén a dinamikus linker figyelmen kívül hagyja az `LD_LIBRARY_PATH` változót, és korlátozza az `LD_PRELOAD` változót, amelyekkel a hívó egyébként kódot csempészhetne a programba (Kerrisk, 2010, ch. 38). A jó gyakorlat: kevés és kicsi setuid program legyen, a jogosultságról azonnal le kell mondani, amint már nincs rá szükség (`seteuid(getuid())`), és ahol csak lehet, a setuid rootot egyetlen file capabilityvel kell helyettesíteni. A `find / -perm -4000 -type f` kilistázza egy rendszer összes setuid programját, ez a biztonsági auditok szokásos lépése.

Két további biztosítékot a linuxos részben meg is mérünk:

- A kernel **figyelmen kívül hagyja a setuid és a setgid bitet a szkripteken** (a `#!` sorral kezdődő fájlokon). Abban az időben, amely a `#!` sor kernel általi beolvasása és a szkript értelmező általi megnyitása között eltelik, egy támadó kicserélhetné a szkriptet, például egy szimbolikus link átnevezésével: ez az [5. előadás](../05-interrupts/#megszakítások-és-párhuzamosság) klasszikus versenyhelyzete, más környezetben.
- A **`nosuid`** opcióval csatolt (mount) fájlrendszer mindkét bitet figyelmen kívül hagyja. A cserélhető adathordozókat, a hálózati megosztásokat és a `/tmp`-t gyakran így csatolják, hogy egy felhasználó ne hozhasson otthonról egy pendrive-on setuid-root shellt.

Egy harmadik biztosíték: ha egy setuid fájlba írnak, vagy megváltoztatják a tulajdonosát, a setuid bit törlődik, hogy egy módosított program, vagy egy új tulajdonoshoz került program ne őrizze meg a régi jogosultságot.

### setgid könyvtáron: egy csoport a csapatnak

Fájlon a setgid ugyanúgy működik, mint a setuid, csak a csoporttal. Könyvtáron viszont mást, és nagyon hasznos dolgot jelent: a benne létrehozott fájlok és alkönyvtárak a létrehozó elsődleges csoportja helyett a **könyvtár csoportját** kapják, az új alkönyvtárak pedig a setgid bitet is öröklik. Egy `cons` csoport tulajdonában lévő, `2770` (`drwxrws---`) módú csapatkönyvtár minden tartalma a `cons` csoportban marad, bárki hozza is létre. A setgid csak a csoportot rögzíti, a biteket nem: a csoport csak akkor *írhatja* az új fájlokat, ha a létrehozó umaskja meghagyja a csoport `w` jogát, ezért a csapattagoknak `umask 002` kell, vagy egy alapértelmezett ACL (lásd alább).

### sticky könyvtáron: közös, de nem mindenkié

A `/tmp`-nek mindenki számára írhatónak kell lennie, így a módja `777` lenne. A könyvtáron lévő `w` azonban bármely bejegyzés törlését és átnevezését megengedi: `user2` törölhetné vagy kicserélhetné `user1` ideiglenes fájljait, ami klasszikus támadás az olyan programok ellen, amelyek kiszámítható nevű fájlokba írnak a `/tmp`-ben. A sticky bittel (`1777`, `drwxrwxrwt`) továbbra is mindenki létrehozhat fájlokat, de egy fájlt csak a tulajdonosa, a könyvtár tulajdonosa vagy a root törölhet és nevezhet át. A `/tmp` és a `/var/tmp` módja minden Unix-rendszeren `1777`.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> setuid, setgid, sticky bit, s/S, t/T, passwd, /etc/shadow, nosuid, versenyhelyzet</summary>

- **setuid** („set user ID”, a felhasználói azonosító beállítása): egy jel egy programon, amely azt mondja: „bárki indít el, a tulajdonosom jogaival futok”. Mint egy banki pénztáros, aki kinyithatja neked a trezort, de csak arra, amit a munkaköre megenged.
- **setgid** („set group ID”, a csoportazonosító beállítása): ugyanez a csoporttal; mappán pedig: „minden, ami itt készül, az én csoportomé”.
- **Sticky bit** (ragadós bit): egy jel egy közös mappán: „bárki betehet ide dolgokat, de mindent csak a tulajdonosa vehet ki”. Mint egy közös hűtő, amelybe mindenki tehet ételt, de mindenki csak a sajátját veheti ki.
- **s/S, t/T:** így mutatja ezeket a jeleket az `ls -l`: kisbetűvel, ha a „végrehajtás” kapcsoló is be van kapcsolva, nagybetűvel, ha nincs.
- **passwd:** a program, amellyel a jelszavadat megváltoztatod. **/etc/shadow:** a fájl, amely az összekevert (hasított) jelszavakat tárolja, és csak a root olvashatja.
- **nosuid:** egy csatolási opció, amely azt mondja a rendszernek, hogy hagyja figyelmen kívül a setuid jeleket egy lemezen, például egy pendrive-on.
- **Versenyhelyzet:** olyan hiba, ahol az eredmény attól függ, ki a gyorsabb; itt: egy fájl kicserélése abban a parányi pillanatban, amely a rendszer két lépése között eltelik.

</details>

## POSIX hozzáférés-szabályozási listák

### Amit a kilenc bit nem tud kifejezni

Három tanácsadó, `cons1`, `cons2` és `cons3` egy projekten dolgozik, és közös a csoportjuk: `cons`. A `/srv/lab10/project/consult` könyvtáruk a `cons1:cons` tulajdonában van, `2770` módú, és `umask 002`-t használnak, így minden fájl olvasható és írható a csoport számára. Ekkor érkezik egy dokumentum, amelyet `cons3` nem láthat. Csupán a módbitekkel nem lehet kifejezni, hogy „a `cons` csoport, kivéve `cons3`-at”: a lehetőségek vagy egy új csoport `cons1` és `cons2` számára (amelyet a rendszergazdának kell létrehoznia, minden egyes ilyen kivételhez), vagy a csoport jogainak elvétele mindenkitől. Ugyanígy lehetetlen ez: „a `cons` írhatja, az `audit1` ellenőr pedig olvashatja”.

A **hozzáférés-szabályozási listák** (access control lists, ACL-ek) úgy oldják meg ezt, hogy fájlonként háromnál több bejegyzést engednek meg. A Linux a POSIX.1e szabványtervezet ACL-jeit valósítja meg: magát a szabványt 1998-ban visszavonták, de az ACL-részét a Linux, a BSD-k és a Solaris szinte azonosan implementálta (Grünbacher, 2003). Az ext4, az XFS, a Btrfs, a tmpfs és mások is támogatják őket, és az inode egy **kiterjesztett attribútumában** (extended attribute) tárolódnak, a `system.posix_acl_access` nevűben.

### Bejegyzések és a maszk

Az ACL `típus:minősítő:jogosultságok` (`type:qualifier:permissions`) alakú bejegyzések listája (Linux man-pages project, n.d.-a):

| bejegyzés | jelentés | megfelelője |
| --- | --- | --- |
| `user::rw-` | a tulajdonos | tulajdonosbitek |
| `user:cons3:---` | egy **névvel megadott felhasználó** (named user) | (új) |
| `group::rw-` | a tulajdonos csoport | csoportbitek (ACL nélkül) |
| `group:audit:r--` | egy **névvel megadott csoport** (named group) | (új) |
| `mask::rw-` | a **felső korlát** minden névvel megadott bejegyzésre és a tulajdonos csoportra | csoportbitek (ACL-lel) |
| `other::r--` | mindenki más | mindenki más bitjei |

Az az ACL, amely csak a `user::`, a `group::` és az `other::` bejegyzésből áll (*minimális* ACL), pontosan a klasszikus mód; a több bejegyzést tartalmazó ACL **kiterjesztett ACL** (extended ACL), és az `ls -l` a mód után egy `+` jellel jelöli. Az ellenőrzés ugyanazt az „első egyezés” elvet követi, két lépéssel kibővítve (lásd a fenti folyamatábrát): tulajdonos → névvel megadott felhasználó → tulajdonos csoport és névvel megadott csoportok → mindenki más. A névvel megadott felhasználói bejegyzést és minden csoportbejegyzést a kernel ÉS-sel (AND) kombinálja a maszkkal; ha a folyamat több csoporttal is illeszkedik, akkor hozzáfér, ha bármelyik illeszkedő csoportbejegyzés (a maszk után) megadja a jogot.

A **maszk** (mask) tartja kompatibilisen az ACL-eket azokkal a programokkal, amelyek csak a kilenc bitet ismerik. Kiterjesztett ACL esetén a mód csoporthármasa maga *a* maszk: az `ls -l` ezt mutatja, és a `chmod g-w` ezt módosítja. Így a klasszikus „tedd priváttá” parancs, a `chmod go-rwx file` továbbra is működik: a maszkot `---`-ra állítja, és egy csapásra kikapcsol minden névvel megadott felhasználót és csoportot, anélkül, hogy törölné őket.

![A plan.txt ACL-je öt sorban: user::rw- a tulajdonosi osztályban; user:cons3:---, group::rw- és mask::r-- a csoportosztályban, ahol a group::rw- a maszk miatt ténylegesen r--; other::r-- a mindenki más osztályában. A tulajdonos-, a maszk- és a mindenki más bejegyzés jelenik meg az ls -l három hármasaként, utánuk egy +. Alul: megjegyzések a maszkról és az alapértelmezett ACL-ekről](acl-mask.svg)

### Alapértelmezett ACL-ek

Egy könyvtárnak **alapértelmezett ACL-je** (default ACL, `system.posix_acl_default`) is lehet. Ezt a kernel sosem ellenőrzi; ez egy sablon: minden benne létrehozott fájl vagy alkönyvtár ezt kapja hozzáférési ACL-ként, az alkönyvtárak pedig saját alapértelmezett ACL-ként is, így a szabály végigterjed a fán. Ha van alapértelmezett ACL, az umask nem érvényesül; a program által kért mód viszont továbbra is korlátozza az eredményt (a `0666` móddal létrehozott fájl nem kap `x`-et, így a maszkja `rw-` lesz). Ez a tiszta megoldás a közös könyvtárak umask-problémájára: a `setfacl -d -m g::rwx,u:cons3:--- consult` minden jövőbeli fájlt írhatóvá tesz a csoport számára és elzár `cons3` elől, akármilyen umaskot használ is a létrehozó.

### Az eszközök

A `getfacl` megmutatja, a `setfacl` módosítja az ACL-t (Linux man-pages project, n.d.-d):

```console
$ getfacl plan.txt                         # show the ACL
$ setfacl -m u:cons3:--- plan.txt          # modify: add or change entries
$ setfacl -m g:audit:r-x -R consult        # recursively
$ setfacl -d -m g::rwx consult             # change the default ACL of a directory
$ setfacl -x u:cons3 plan.txt              # remove one entry
$ setfacl -b plan.txt                      # remove all extended entries
$ getfacl -R consult > acl.txt; setfacl --restore=acl.txt   # back up and restore
```

Az ACL-ek egy fájlrendszeren belül együtt mozognak a fájllal (`mv`), a másolatok viszont csak kérésre őrzik meg őket (`cp -p`, `cp -a`, `rsync -A`, `tar --acls`). A kiterjesztett attribútumokat nem ismerő mentőprogramok szó nélkül elhagyják őket.

### ACL-ek más rendszerekben

A Windows NT és utódai kezdettől fogva mindenre ACL-eket használnak. Minden NTFS-fájlnak ([10. előadás](../10-file-systems/#ntfs)), registry-kulcsnak, folyamatnak és szolgáltatásnak van egy **biztonsági leírója** (security descriptor), amely tartalmaz egy tulajdonost, egy felhasználókra és csoportokra vonatkozó engedélyező és tiltó bejegyzésekből álló **DACL-t** (discretionary ACL), valamint egy **rendszer-ACL-t** (SACL, system ACL), amely megadja, mely hozzáféréseket kell naplózni. A bejegyzéseket alapértelmezésben a szülőmappától örökli az objektum, és a bejegyzéseket sorban ellenőrzi a rendszer, amíg a kért jogokat meg nem kapja a kérelmező, vagy valamelyik bejegyzés meg nem tagadja őket; mivel a szabványos (kanonikus) sorrend a kifejezett tiltó bejegyzéseket teszi előre, egy kifejezett tiltás erősebb az engedélyezésnél (Microsoft, n.d.-a). Az NFS 4-es verziója hasonló, de gazdagabb ACL-modellt használ, ezért létezik a `setfacl` mellett `nfs4_setfacl` is.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> névvel megadott felhasználó, névvel megadott csoport, maszk, kiterjesztett ACL, alapértelmezett ACL, kiterjesztett attribútum, POSIX.1e, biztonsági leíró, DACL, SACL, NFSv4</summary>

- **Névvel megadott felhasználó, névvel megadott csoport:** egy külön sor a listában egy bizonyos személyre vagy csoportra: „cons3: semmi”.
- **Maszk:** plafon mindenkinek, aki a lista közepén van (a név szerint felsorolt embereknek és csoportoknak). Ha egy sor azt mondja, „olvasás és írás”, de a plafon azt, hogy „csak olvasás”, akkor csak az olvasás megengedett.
- **Kiterjesztett ACL:** az alap három sornál hosszabb lista; az `ls -l` egy `+` jellel jelzi.
- **Alapértelmezett ACL:** sablon egy mappán: minden új fájl automatikusan megkapja ezeknek a szabályoknak egy másolatát.
- **Kiterjesztett attribútum:** egy kis, felirattal ellátott cetli a fájlon, a tartalma és az alapadatai mellett. Az ACL-ek és a SELinux-címkék ilyen cetliken tárolódnak.
- **POSIX.1e:** a Unix-szerű rendszerek biztonsági funkcióira tervezett közös szabvány. Sosem készült el, de az ACL-részét használja a Linux.
- **Biztonsági leíró:** egy windowsos objektum biztonsági adatlapja: a tulajdonosa és a két listája.
- **DACL, SACL:** egy windowsos fájl két listája: ki mit tehet (DACL), és mely műveleteket kell feljegyezni a biztonsági naplóba (SACL).
- **NFSv4** (Network File System, version 4, hálózati fájlrendszer, 4-es verzió): egy másik számítógépen tárolt fájlok használata a hálózaton át, mintha helyben lennének.

</details>

## MAC (mandatory access control)

### Miért nem elég a DAC?

DAC esetén a fájl tulajdonosa dönti el, ki használhatja, és **minden program, amelyet a tulajdonos futtat, az ő nevében dönthet**. Ez a gyenge pont: a program nem azonos a felhasználóval. Ha egy felhasználó rosszindulatú programot (trójai falovat) futtat, vagy egy hibás programot, amelynek hibáját egy támadó kihasználja, akkor az a felhasználó összes jogával rendelkezik: elolvashatja a fájljait és kiadhatja őket, például úgy, hogy `666` móddal a `/tmp`-be másolja őket, vagy elküldi őket a hálózaton. A DAC ezt nem akadályozhatja meg, mert a kernel szempontjából a program *maga* a tulajdonos, aki a saját belátása szerint jár el. A rootként futó szolgáltatások számára a DAC semmilyen védelmet nem nyújt.

A **MAC** (mandatory access control, „kötelező” hozzáférés-szabályozás) egy második szabálykészletet ad hozzá, amelyet a rendszer biztonsági policyja határoz meg, amely minden folyamatra vonatkozik, a root folyamataira is, és amelyet sem a felhasználók, sem a fájlok tulajdonosai nem változtathatnak meg. Rövid emlékeztető: a DAC arra felel, *ki* (melyik felhasználó) férhet hozzá egy objektumhoz; a MAC arra, hogy *mi* (milyen fajta program) *mit* tehet *milyen fajta* objektummal. A kettő együtt érvényes: egy hozzáférést mindkettőnek meg kell engednie.

A legrégebbi MAC-modell a katonaságtól származik: ez a **többszintű biztonság** (multi-level security, MLS), amelyben az alanyoknak és az objektumoknak biztonsági szintjük (clearance), illetve minősítési szintjük van (nem minősített, bizalmas, titkos, szigorúan titkos), és az információ csak felfelé áramolhat: egy alany nem olvashat a saját szintje fölötti objektumokat („no read up”), és nem írhat az alatta lévőkbe („no write down”), így egy titkos folyamat nem szivároghat ki egy nem minősített fájlba (Bell & LaPadula, 1976). Az ilyen szabályok túl merevek az általános célú szerverekhez. A modern linuxos MAC-rendszerek a kernel **Linux Security Modules** (LSM, Linux biztonsági modulok) keretrendszerére épülnek: ez hookok (beépített ellenőrzési pontok) halmaza a kernel minden biztonsági szempontból fontos pontján (fájl megnyitása, socket lefoglalása, szignál küldése), amelyeken keresztül egy biztonsági modul a DAC-ellenőrzés sikeres lefutása után is megtagadhatja a műveletet (Wright et al., 2002). A két legelterjedtebb modul a SELinux és az AppArmor.

<details>
<summary><b>Egyszerűen elmagyarázva:</b> trójai faló, MAC, MLS, biztonsági szint (clearance), LSM, hook</summary>

- **Trójai faló:** olyan program, amely látszólag valami hasznosat csinál, közben titokban valami kárt okoz, annak a személynek a jogaival, aki elindította.
- **MAC** (mandatory access control, kötelező hozzáférés-szabályozás): felülről jövő szabályok, amelyeket lent senki sem kapcsolhat ki, sem a fájl tulajdonosa, sem a rendszergazda programjai.
- **MLS** (multi-level security, többszintű biztonság): a „titkos / szigorúan titkos” rendszer: csak azt olvashatod, amit a biztonsági szinted megenged, és titkot nem írhatsz kevésbé titkos helyre.
- **Biztonsági szint (clearance):** a legmagasabb titkossági szint, amellyel egy személyre vagy programra rábíznak valamit.
- **LSM** (Linux Security Modules, Linux biztonsági modulok): a Linux-kernel csatlakozóhelyei, ahová egy további biztonsági őrt lehet bedugni. **Hook:** egy ilyen csatlakozóhely, egy pont, ahol a kernel megkérdezi az őrt: „megtörténhet ez?”.

</details>

### SELinux: címkék és type enforcement

A SELinuxot az amerikai Nemzetbiztonsági Ügynökség (National Security Agency, NSA) fejlesztette ki a Flask kutatási architektúra alapján; 2000-ben nyílt forráskódúként tették közzé, és az LSM-keretrendszeren keresztül került be a Linux 2.6-ba (Loscocco & Smalley, 2001; Smalley et al., 2001). Alapértelmezésben engedélyezve van és kikényszerítő (enforcing) módban működik a Fedorán, a Red Hat Enterprise Linuxon és rebuildjein (AlmaLinux, Rocky Linux; lásd a [2. előadást](../02-quality-and-enterprise-linux/)), valamint az Androidon.

A SELinux **minden** alanynak és objektumnak ad egy **contextet** (security context), más néven **címkét** (label): ez egy négy mezőből álló sztring, `user:role:type:level` alakban:

![Fent: a system_u:system_r:httpd_t:s0 context felbontva felhasználóra, szerepre, típusra és szintre, mellette egy fájl és egy port contextje. Alatta: balra a httpd_t (Apache httpd) és a mysqld_t (MariaDB mysqld) domain, jobbra a http_port_t, a httpd_sys_content_t, a user_home_t, a mysqld_db_t és a mysqld_port_t típus; a folytonos nyilak a megengedett hozzáférést mutatják (a httpd_t lefoglalhatja a http_port_t portot és olvashatja a httpd_sys_content_t típust, a mysqld_t olvashatja és írhatja a mysqld_db_t típust és lefoglalhatja a mysqld_port_t portot), a szaggatott piros nyilak a megtagadott hozzáférést (httpd_t a user_home_t és a mysqld_db_t felé, mysqld_t a httpd_sys_content_t felé)](selinux-te.svg)

- **user** (felhasználó; `system_u`, `unconfined_u`, `staff_u`, …): a SELinux-felhasználó, amelyre a Linux-felhasználót bejelentkezéskor leképezi a rendszer; ez korlátozza, mely szerepek lehetségesek.
- **role** (szerep; `system_r`, fájloknál `object_r`, …): azok a szerepek, amelyekbe egy felhasználó beléphet, és azok a domainek, amelyekben egy szerep futhat (szerepalapú hozzáférés-szabályozás, role-based access control).
- **type** (típus): a legfontosabb mező. Egy folyamat típusát **domainnek** nevezzük (`httpd_t`, `mysqld_t`); egy fájl vagy port típusa azt mondja meg, milyen fajta objektumról van szó (`httpd_sys_content_t` a weboldalaknál, `mysqld_db_t` az adatbázisfájloknál, `user_home_t` a saját könyvtárak tartalmánál, `http_port_t` a 80-as, a 443-as és néhány további TCP-portnál).
- **level** (szint; `s0`, `s0-s0:c0.c1023`): az MLS érzékenységi szint és a többkategóriás biztonság (multi-category security, MCS) kategóriái, amelyekkel például a virtuális gépeket és a konténereket választják el egymástól.

A fájlok a `security.selinux` kiterjesztett attribútumban tárolják a contextjüket; a folyamatok a futtatott program contextjéből és a szülőjük domainjéből kapják a sajátjukat, **átmeneti szabályok** (transition rules) szerint (amikor az `init_t` domainben futó `systemd` végrehajtja a `httpd_exec_t` címkéjű `/usr/sbin/httpd` programot, az új folyamat a `httpd_t` domainbe lép). Az `ls -Z`, a `ps -Z` és az `id -Z` mutatja meg a contexteket.

A policy **type enforcement** (TE) szabályok nagy halmaza, amelyek objektumosztályonként megmondják, melyik domain milyen műveleteket végezhet milyen típusokon:

```
allow httpd_t httpd_sys_content_t:file { read open getattr };
allow httpd_t http_port_t:tcp_socket name_bind;
```

Mindent, amit egyetlen szabály sem enged meg, a rendszer **megtagad** és naplóz. Ennek az a hatása, hogy minden korlátozott szolgáltatás a saját kis homokozójában (sandbox) él: a webszerver olvashatja a webes tartalmat és lefoglalhatja a webes portokat, de nem olvashatja az adatbázisfájlokat, a felhasználók saját könyvtárait vagy az `/etc/shadow` fájlt, még akkor sem, ha rootként fut, és akkor sem, ha ezeknek a fájloknak `777` lenne a módjuk. Egy eltérített Apache sem olvashatja a MariaDB adatait, és egy eltérített MariaDB sem módosíthatja a weboldalakat.

Egy egész rendszerre ilyen policyt írni óriási feladat (a reference policy több tízezer szabályból áll), ezért a disztribúciók kész policyket szállítanak:

- **targeted** (célzott; ez az alapértelmezett): a hálózati szolgáltatások és más kiválasztott démonok korlátozott domainekben futnak; a felhasználók és minden más az `unconfined_t` domainben fut, amelyet csak a DAC korlátoz;
- **minimum**: mint a targeted, de csak néhány kiválasztott folyamat korlátozott, kicsi vagy speciális rendszerekhez;
- **mls**: teljes többszintű biztonság kormányzati és katonai követelményekhez.

A telephelyenként eltérő viselkedést **booleanok** állítják: ezek szabálycsoportok névvel ellátott be/ki kapcsolói: `httpd_can_network_connect` (nyithat-e a webszerver kimenő kapcsolatokat, például egy alkalmazásszerver felé), `httpd_enable_homedirs` (kiszolgálhatja-e a `~/public_html` tartalmát), `httpd_can_network_connect_db`. A `getsebool -a` kilistázza őket, a `setsebool -P name on` tartósan beállít egyet.

A SELinux három **mód** egyikében fut:

- **enforcing** (kikényszerítő): megtagad és naplóz;
- **permissive** (megengedő): csak naplózza, amit megtagadna; hibakereséshez és policyfejlesztéshez hasznos;
- **disabled** (letiltott): egyáltalán nem tart nyilván címkéket. Az ezalatt létrehozott fájlok címke nélküliek, ezért az enforcing módba való visszatéréshez az egész fájlrendszert újra kell címkézni.

A `getenforce` megmutatja a módot, a `setenforce 0|1` pedig a következő rendszerindításig vált az enforcing és a permissive mód között; az induláskori módot az `/etc/selinux/config` fájl adja meg (a RHEL 9-től kezdve a teljes letiltás dokumentált módja a `selinux=0` kernelparaméter). A Red Hat dokumentációjának tanácsa egyértelmű: a permissive mód, vagy egyetlen szolgáltatás permissive domainje, hibakeresésre való; a SELinux letiltása eltávolít egy védelmi réteget (Red Hat, n.d.).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> context, címke, domain, típus, type enforcement, szerep, MCS, átmenet, targeted policy, boolean, enforcing, permissive</summary>

- **Context, címke:** névcédula minden programon és minden fájlon, például „webszerver” vagy „weboldal”.
- **Típus, domain:** a névcédula legfontosabb része: hogy milyen fajta dologról van szó. Egy futó programnál domainnek hívják.
- **Type enforcement:** a szabálykönyv: „a *webszerver* cédulás programok olvashatják a *weboldal* cédulás fájlokat”. Ami nincs benne a könyvben, az tilos.
- **Szerep:** egy beosztás, amely eldönti, milyen fajta programokat futtathat egy felhasználó.
- **MCS** (multi-category security, többkategóriás biztonság): további cédulák, amelyek például két azonos fajta virtuális gépet tartanak távol egymástól.
- **Átmenet:** az a szabály, amely egy újonnan elindított programnak cédulát ad, például: „amikor a rendszer elindítja a webszerverprogramot, az a *webszerver* cédulát kapja”.
- **Targeted policy:** az alapértelmezett szabálykönyv: a kockázatos hálózati szolgáltatásokat bezárja, a hétköznapi felhasználókat békén hagyja.
- **Boolean:** be/ki kapcsoló egy szabálycsoporthoz, például: „csatlakozhat-e a webszerver más számítógépekhez?”.
- **Enforcing, permissive:** valóban tilt, vagy csak felírja, mit tiltott volna.

</details>

### Munka a címkékkel

Egy valódi szerveren a legtöbb SELinux-probléma **rossz címke**, nem hiányzó szabály. A policy tartalmaz egy adatbázist az elérési utak alapértelmezett fájl-contextjeiről (file context, `/var/www(/.*)?` → `httpd_sys_content_t`); egy fájl a létrehozásakor kapja a címkéjét a policytól (általában annak a könyvtárnak a címkéjét, amelyben létrejön), és utána megtartja. Innen ered a klasszikus csapda:

- a `cp ~/index.html /var/www/html/` egy **új** fájlt hoz létre a `/var/www/html`-ben, amely `httpd_sys_content_t` címkét kap: az oldal működik;
- a `mv ~/index.html /var/www/html/` csak átnevezi a meglévő inode-ot, amely **megtartja** régi, `user_home_t` címkéjét. A DAC megengedi a hozzáférést (`644` mód), de a webszerver domainje nem olvashat `user_home_t` típust: a böngésző **403 Forbidden** hibát mutat, az auditnapló pedig egy elutasítást.

Az eszközök:

- a `restorecon -Rv /var/www/html` a policy alapértelmezéseire állítja vissza az adott utak címkéit: ez a javítás az `mv` esetére;
- a `chcon -t httpd_sys_content_t file` kézzel állít be egy címkét, de csak **ideiglenesen**: a következő `restorecon` vagy teljes újracímkézés (`touch /.autorelabel` és újraindítás) visszaállítja, mert a policy adatbázisa továbbra is mást mond;
- a `semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'` egy szabályt vesz fel az adatbázisba (itt: egy `/var/www`-n kívüli webes gyökérkönyvtárat), a `restorecon -Rv /web` pedig érvényesíti. Ez a **tartós** megoldás;
- a `semanage port -a -t http_port_t -p tcp 3131` felcímkéz egy nem szabványos portot, hogy a webszerver figyelhessen rajta.

Ha valamit megtagad, a kernel egy **AVC-elutasítást** (AVC denial; access vector cache, a kernel policydöntéseinek gyorsítótára) ír az auditnaplóba, a `/var/log/audit/audit.log` fájlba. Ez megnevezi a műveletet (például `{ read }`), a folyamatot (`comm="httpd"`), az objektumot (`name="index.html"`), a forrás contextjét (`scontext=…:httpd_t:s0`), a cél contextjét (`tcontext=…:user_home_t:s0`) és az objektumosztályt (`tclass=file`). Az `ausearch -m AVC -ts recent` megkeresi őket; az `audit2why` megmagyarázza őket; a `setroubleshoot` csomaggal a `sealert -a /var/log/audit/audit.log` (vagy a `sealert -l ID`, amelynek azonosítóját a rendszernapló közli) olvasható elemzést ad javasolt parancsokkal. A javaslat általában a három közül az egyik: egy címke javítása (`restorecon`, `semanage fcontext`), egy boolean átállítása, vagy ritkán a policy kibővítése egy helyi modullal (`audit2allow -M`), ami csak a legvégső megoldás lehet, mert pontosan azt engedélyezheti, amivel egy támadó próbálkozott.

### Az AppArmor és más biztonsági modulok

Az **AppArmor**, az Ubuntu és a Debian alapértelmezett MAC-rendszere (és a SUSE-é is volt, amíg a SUSE Linux Enterprise 16 és az openSUSE Leap 16 2025-ben át nem tért a SELinuxra), a címkékkel ellentétes megközelítést követ: **elérési utak** (path names) alapján korlátozza a programokat. Az `/etc/apparmor.d/` könyvtárban lévő profil egy programra felsorolja azokat a fájlokat és könyvtárakat, amelyekhez hozzáférhet (olyan jogosultságokkal, mint `r`, `w`, `ix`), valamint azokat a capabilityket és hálózati hozzáféréseket, amelyeket használhat; minden mást megtagad. A profil nélküli programok korlátozás nélkül futnak. A profilokat könnyebb olvasni és írni, mint a SELinux-policyt, és nem kellenek hozzájuk fájlcímkék, de egy útvonalalapú szabály a nevet követi, nem az objektumot: egy hard link vagy egy bind mount ugyanannak a fájlnak egy másik nevet ad, amelyre a profil talán nem terjed ki. Az `aa-status` kilistázza a betöltött profilokat; az `aa-complain` és az `aa-enforce` a SELinux permissive, illetve enforcing módjának felel meg, profilonként. A kernel kisebb modulokat is kínál, amelyek ezekkel egymásra rétegezhetők: a Yama (korlátozza a `ptrace` hívást), a Landlock (lehetővé teszi, hogy egy privilégium nélküli program saját magát homokozóba zárja) és a lockdown (megvédi a futó kernelt a roottól).

A Windowsban is van kötelező elem: a **Mandatory Integrity Control** (kötelező integritás-szabályozás) minden folyamatnak és objektumnak egy integritási szintet (integrity level) ad (alacsony, közepes, magas, rendszer), és egy folyamat nem írhat magasabb szintű objektumokba, bármit mondjon is a DACL („no write up”). Ezért futtatják a webböngészők a homokozóba zárt tartalomfolyamataikat alacsony (vagy még alacsonyabb, „untrusted”, nem megbízható) integritási szinten (Microsoft, n.d.-b).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> AVC, auditnapló, restorecon, chcon, semanage, sealert, AppArmor, profil, Yama, Landlock, lockdown, Mandatory Integrity Control</summary>

- **AVC-elutasítás:** az az üzenet, amelyet a SELinux ír, amikor megtilt valamit: ki mit próbált meg mivel.
- **Auditnapló:** a rendszer biztonsági naplója, a `/var/log/audit/audit.log`.
- **restorecon:** „tedd vissza a helyes névcédulákat” a hivatalos lista szerint.
- **chcon:** egy névcédula kézi átírása, egyelőre. A következő rendrakás visszacsinálja.
- **semanage:** magának a hivatalos listának a módosítása, hogy a változás tartós legyen.
- **sealert:** segédprogram, amely a rejtélyes elutasító üzeneteket magyarázatokká és javaslatokká alakítja.
- **AppArmor:** egy másik bezáró rendszer, amely névcédulák helyett fájlnevekkel írja le, mihez nyúlhat egy program. **Profil:** az egy programnak megengedett dolgok listája.
- **Yama, Landlock, lockdown:** kis, kiegészítő őrök a Linux-kernelben: a Yama megakadályozza, hogy a programok kémkedjenek egymás után, a Landlock lehetővé teszi, hogy egy program saját magát egy kisebb szobába zárja, a lockdown pedig még a rendszergazdát is megakadályozza abban, hogy belenyúljon a futó kernelbe.
- **Mandatory Integrity Control, integritási szint:** a Windows bizalmi szintjei (alacsony, közepes, magas, rendszer): egy kevésbé megbízható program nem módosíthat olyasmit, ami egy megbízhatóbb szinthez tartozik.

</details>

## Ugyanezek az elvek Linuxon (x86-64)

A bemutatók rootként futnak az előző előadások Ubuntu 24.04-es felhőbeli virtuális gépén (Linux 6.18, GNU coreutils 9.4, gcc 13, libacl 2.3.2, libcap 2.66). Root jog a felhasználók létrehozásához és a tulajdonosok megváltoztatásához kell; minden kísérlet ezután a `su USER -c 'command'` paranccsal vált át egy közönséges felhasználóra. Minden kísérlet a `/srv/lab10` könyvtárban dolgozik. Ha meg akarod ismételni őket, tedd futtathatóvá a szkripteket (`chmod +x *.sh`), először futtasd a `./users.sh` szkriptet, és fordítsd le a setuid bemutatót (`gcc -O2 -o showid showid.c`). A végén a `userdel -r USER` és az `rm -r /srv/lab10` takarít el.

Ezen a gépen megvan az ACL-könyvtár (`libacl.so.1`), de az `acl` csomag a `getfacl` és a `setfacl` paranccsal nincs telepítve. Az ACL-bemutató ezért az `acl.py` szkriptet használja, egy körülbelül 150 soros minimális helyettesítőt, amely ugyanazokat a könyvtári függvényeket hívja, mint a `getfacl` és a `setfacl` (`acl_get_file`, `acl_to_any_text`, `acl_from_text`, `acl_calc_mask`, `acl_set_file`), és ugyanabban a formátumban ír ki; egy szokásos telepítésen használd a `getfacl` és a `setfacl` parancsot (`sudo apt install acl`, `sudo dnf install acl`). Ez a kernel SELinux-támogatással készült, de nincs betöltve policy (lásd az [utolsó bemutatót](#van-e-mac-policy-ezen-a-gépen)), így a SELinux-rész egy csak parancsokat tartalmazó [labor egy virtuális gépre](#selinux-egy-fedora-rhel-vagy-almalinux-virtuális-gépen).

<details>
<summary><b>Egyszerűen elmagyarázva:</b> konzol, root, su, useradd, szkript</summary>

- **Konzol** (terminál): egy ablak, amelybe parancsokat gépelsz. A `$` jellel (rendszergazdaként `#` jellel) kezdődő sorokat te gépeled be; a többi sor a számítógép válasza.
- **su USER -c '…'**: „futtasd ezt az egy parancsot annak a felhasználónak a nevében”. A root ezt jelszó nélkül megteheti.
- **useradd:** új felhasználói fiók létrehozása.
- **Szkript** (`.sh` fájl): egy fájlba mentett parancslista, amelynek parancsai egymás után futnak le.

</details>

### Felhasználók a bemutatókhoz

```console
# ./users.sh
uid=30033(john) gid=30033(john) groups=30033(john)
uid=30034(user1) gid=30034(user1) groups=30034(user1)
uid=30035(user2) gid=30035(user2) groups=30035(user2)
uid=30036(cons1) gid=30036(cons1) groups=30036(cons1),30002(cons)
uid=30037(cons2) gid=30037(cons2) groups=30037(cons2),30002(cons)
uid=30038(cons3) gid=30038(cons3) groups=30038(cons3),30002(cons)
```

Minden felhasználó kapott egy saját csoportot ugyanazzal a számmal; a három tanácsadó a `cons` kiegészítő csoportnak (GID 30002) is tagja. A számok azért nagyok, mert ezen a gépen a felhasználói azonosítók 30000-től kezdődnek.

### Az első egyezés dönt

```console
# ./firstmatch.sh
-------rwx 1 john john 30 Oct  7 18:42 fm/note.txt
--- as john (the owner):
cat: /srv/lab10/fm/note.txt: Permission denied
--- as user1 (falls into 'others'):
anyone but john may read this
--- the same for a directory, d------rwx:
d------rwx 2 john john 4096 Oct  7 18:42 fm/dir
ls: cannot open directory '/srv/lab10/fm/dir': Permission denied
a
b
```

A tulajdonost elutasítja a rendszer, egy idegent pedig beenged. A kernel megállapította, hogy `john` a tulajdonos, vette a `---` tulajdonosi hármast, és megállt; `user1` sem nem tulajdonos, sem nem csoporttag, így a mindenki más `rwx` hármasát kapja. Ugyanez érvényes a könyvtárra is.

### Könyvtárak: r, w és x

A `dirperms.sh` szkript `user1`-gyel (egy „mindenki más” kategóriájú felhasználóval) öt műveletet próbáltat ki `john` egy `d` könyvtárán, a mindenki más bitjeinek hét beállítása mellett. A benne lévő `d/f` fájl módja `666`, így minden elutasítás a könyvtártól ered:

```console
# ./dirperms.sh
others      ls d     cd d     cat d/f  touch    rm d/f   
drwxr-x---  denied   denied   denied   denied   denied   
drwxr-xr--  ok       denied   denied   denied   denied   
drwxr-x--x  denied   ok       ok       denied   denied   
drwxr-xr-x  ok       ok       ok       denied   denied   
drwxr-x-w-  denied   denied   denied   denied   denied   
drwxr-x-wx  denied   ok       ok       ok       ok       
drwxr-xrwx  ok       ok       ok       ok       ok       
--- a file with no permissions at all, in a directory where user1 has w and x:
---------- 1 john john 0 Oct  7 18:42 d/locked
cat: /srv/lab10/d/locked: Permission denied
rm worked: deleting is a change of the directory
```

Olvasd a táblázatot soronként: az `r` önmagában kilistázza a neveket, de semmit sem nyit meg; az `x` önmagában megnyit egy fájlt, ha ismert a neve, de listázni nem tud; a `w` önmagában (`-w-`) semmit sem ér el; a `wx` lehetővé teszi a létrehozást és a törlést listázás nélkül. Az utolsó sorok a szakasz meglepetését mutatják: `user1` nem tudja elolvasni a `locked` fájlt, de törölheti.

### chmod, umask és a speciális bitek

```console
# ./modes.sh
--- octal: every digit sets one class completely
640  -rw-r-----  f
--- symbolic: change single bits, leave the others alone
704  -rwx---r--  f
644  -rw-r--r--  f
--- capital X: x only for directories and files that are already executable by someone
700  drwx------  d
600  -rw-------  plain
700  -rwx------  script
755  drwxr-xr-x  d
644  -rw-r--r--  plain
755  -rwxr-xr-x  script
--- umask: bits removed from new files (base 666) and directories (base 777)
umask 022 -> file 644 -rw-r--r--, dir 755 drwxr-xr-x
umask 002 -> file 664 -rw-rw-r--, dir 775 drwxrwxr-x
umask 077 -> file 600 -rw-------, dir 700 drwx------
umask 027 -> file 640 -rw-r-----, dir 750 drwxr-x---
--- the special bits: 4 = setuid, 2 = setgid, 1 = sticky
4755  -rwsr-xr-x  f
2755  -rwxr-sr-x  f
1777  -rwxrwxrwt  f
4644  -rwSr--r--  f
2644  -rw-r-Sr--  f
1666  -rw-rw-rwT  f
7743  -rwsr-S-wt  f
3374  --wxrwsr-T  f
7640  -rwSr-S--T  f
```

A `stat -c '%a %A'` oktálisan és sztringként is kiírja a módot. A `chmod u+x,g-r,o+r` a `640`-ből `704`-et csinál: csak a megnevezett bitek változtak. A `chmod -R go+rX` `x`-et adott a könyvtárnak és a `script` fájlnak (amely a tulajdonosa számára futtatható), a `plain` fájlnak viszont nem. Az umask-sorok azt mutatják, hogy az umask sosem ad hozzá biteket, csak elveszi őket a `666`-ból vagy a `777`-ből. Az utolsó blokk megerősíti a megjelenítési szabályt és mindkét kidolgozott példát: a `7743` az `rwsr-S-wt`, a `3374` pedig a `-wxrwsr-T` (a közönséges fájlt jelző vezető `-` után).

### A sticky bit egy közös könyvtáron

`user1` létrehoz egy fájlt egy mindenki által írható könyvtárban, `user2` pedig megpróbálja átnevezni és törölni, először `777`, aztán `1777` mód mellett:

```console
# ./sticky.sh
drwxrwxrwt 12 root root 4096 Oct  7 18:42 /tmp
--- shared is drwxrwxrwx (0777)
-rw-rw-r-- 1 user1 user1 15 Oct  7 18:42 shared/file.txt
user2: renamed it to mine.txt
user2: deleted the file of user1
--- shared is drwxrwxrwt (1777)
-rw-rw-r-- 1 user1 user1 15 Oct  7 18:42 shared/file.txt
mv: cannot move 'file.txt' to 'mine.txt': Operation not permitted
rm: cannot remove 'file.txt': Operation not permitted
--- the owner may still delete it:
user1: deleted own file
```

Sticky bit nélkül `user2` átnevezhetett és törölhetett egy olyan fájlt, amely nem az övé (és amelyet írni sem tudott volna: a módja `rw-rw-r--`). A sticky bittel a kernel `EPERM` („Operation not permitted”) hibával utasítja el, nem `EACCES`-szel: a bitek megengednék, de maga a művelet a tulajdonosnak van fenntartva. Az új fájl azért `rw-rw-r--` módú, mert a `su` a saját csoporttal rendelkező felhasználók `002`-es umaskját adta `user1`-nek.

### Egy setuid program

A `showid.c` kiírja a folyamata valós és effektív azonosítóit, majd megpróbálja elolvasni a parancssorában megadott fájlt. A `setuid.sh` `john` tulajdonában telepíti, `john` privát naplója mellé, és `user1`-ként futtatja:

```console
# gcc -O2 -o showid showid.c
# ./setuid.sh
-rw------- 1 john john    13 Oct  7 18:42 diary.txt
-rwxr-xr-x 1 john john 16576 Oct  7 18:42 showid
--- an ordinary program runs with the IDs of the user who starts it:
real UID 30034 (user1), effective UID 30034 (user1); real GID 30034 (user1), effective GID 30034 (user1)
/srv/lab10/suid/diary.txt: Permission denied
--- chmod u+s (4755): it runs with the effective UID of its owner, john:
-rwsr-xr-x 1 john john 16576 Oct  7 18:42 showid
real UID 30034 (user1), effective UID 30033 (john); real GID 30034 (user1), effective GID 30034 (user1)
read /srv/lab10/suid/diary.txt: john's diary
--- chmod g+s (2755) instead: the effective GID becomes the file's group:
-rwxr-sr-x 1 john john 16576 Oct  7 18:42 showid
real UID 30034 (user1), effective UID 30034 (user1); real GID 30034 (user1), effective GID 30033 (john)
--- a real setuid-root program of the system:
-rwsr-xr-x 1 root root 64152 May 30  2024 /usr/bin/passwd
--- the setuid bit on a script is ignored by the kernel:
-rwsr-xr-x 1 john john 68 Oct  7 18:42 who.sh
script: real UID 30034, effective UID 30034
--- and on a file system mounted with nosuid:
tmpfs /mnt/l10nosuid tmpfs rw,nosuid,relatime,size=4096k 0 0
real UID 30034 (user1), effective UID 30034 (user1); real GID 30034 (user1), effective GID 30034 (user1)
```

A setuid bittel ugyanaz a bináris, ugyanattól a felhasználótól indítva, elolvassa `john` naplóját: az effektív UID `john`-é, a valós UID továbbra is azt mutatja, ki ül a billentyűzetnél. Pontosan ezért veszélyesek a setuid programok: amit a `showid` rávehető, hogy elolvasson, azt `user1` is elolvashatja. Az ugyanilyen bitekkel rendelkező szkript `user1` azonosítóival fut, és ugyanígy a `nosuid` fájlrendszerre másolt setuid bináris is.

### A root a capabilityk miatt root

```console
# ./caps.sh
---------- 1 root root 21 Oct  7 18:42 locked.txt
--- root reads it anyway:
nobody may read this
--- some capabilities of this root shell (effective set, decoded, filtered):
cap_chown cap_dac_override cap_dac_read_search cap_fowner cap_kill cap_setuid cap_net_bind_service 
--- root without CAP_DAC_OVERRIDE and CAP_DAC_READ_SEARCH:
0
cat: locked.txt: Permission denied
--- the opposite: an ordinary user with one capability on one program
/srv/lab10/caps/rcat: /srv/lab10/caps/rootonly.txt: Permission denied
./rcat cap_dac_read_search=ep
root's note
```

Egy `000` módú fájl nem akadály a root számára. A `capsh --drop=…` olyan shellt indít, amely még mindig 0-s UID-del fut (az `id -u` `0`-t ír ki), de lemondott a két DAC-capabilityről, és ugyanúgy elutasítják, mint bárki mást: a kernel a capabilityket ellenőrzi, nem a 0-s számot. Fordítva: a `cat` egy olyan másolata, amely a `cap_dac_read_search` file capabilityvel rendelkezik (`e` = effective, effektív; `p` = permitted, megengedett), lehetővé teszi `user1`-nek, hogy elolvassa a root egy fájlját, de semmi mást nem ad: semmit sem írhat vagy törölhet vele. Ez a legkisebb jogosultság elve, és egyben figyelmeztetés is: a `getcap -r /` parancsnak a `find / -perm -4000` mellett helye van minden biztonsági auditban.

### Projektkönyvtár setgid-del és ACL-ekkel

Az `acl-project.sh` lépésről lépésre lejátssza a tanácsadók történetét az ACL-szakaszból; az `acl.py get` pontosan azt írja ki, amit a `getfacl` kiírna, a kimenetben lévő megjegyzések pedig megnevezik azt a `setfacl` parancsot, amelyet az `acl.py modify` helyettesít:

```console
# ./acl-project.sh
--- 1. a group directory without setgid: new files get the creator's own group
drwxrwx--- 2 cons1 cons 4096 Oct  7 18:42 /srv/lab10/project/consult
-rw-r--r-- 1 cons1 cons1 8 Oct  7 18:42 report.txt
bash: line 1: /srv/lab10/project/consult/report.txt: Permission denied
--- 2. chmod g+s: new files inherit the directory's group; umask 002 lets the group write
drwxrws--- 2 cons1 cons 4096 Oct  7 18:42 /srv/lab10/project/consult
total 16
drwxrwsr-x 2 cons1 cons  4096 Oct  7 18:42 notes
-rw-r--r-- 1 cons1 cons     8 Oct  7 18:42 plan-022.txt
-rw-rw-r-- 1 cons1 cons     8 Oct  7 18:42 plan.txt
-rw-r--r-- 1 cons1 cons1    8 Oct  7 18:42 report.txt
bash: line 1: /srv/lab10/project/consult/plan-022.txt: Permission denied
cons2: appended to plan.txt
draft 2
cons2 agrees
--- 3. the group minus one person: setfacl -m u:cons3:--- plan.txt
-rw-rw-r--+ 1 cons1 cons 21 Oct  7 18:42 plan.txt
# file: plan.txt
# owner: cons1
# group: cons
user::rw-
user:cons3:---
group::rw-
mask::rw-
other::r--

cat: /srv/lab10/project/consult/plan.txt: Permission denied
draft 2
cons2 agrees
```

1. lépés: setgid nélkül a `report.txt` `cons1` saját csoportjához tartozik, és `cons2` nem tud hozzáfűzni. 2. lépés: a `chmod g+s` után az új fájlok és a `notes` nevű új könyvtár a `cons` csoporthoz tartoznak (és a `notes` örökölte a setgid bitet, `rws`), de csak a `002`-es umaskkal létrehozott `plan.txt` írható a csoport számára; a `plan-022.txt` nem. `cons3`, aki a `cons` tagja, továbbra is olvashatja a `plan.txt`-t. 3. lépés: egyetlen ACL-bejegyzés kizárja `cons3`-at, pedig `cons3` benne van abban a csoportban, amely olvashat és írhat: a névvel megadott felhasználói bejegyzés a csoportok előtt illeszkedik. Az `ls -l` mutatja a `+` jelet. A kimenet folytatódik:

```console
--- 4. the mask limits every named entry and the group: chmod g-w plan.txt
-rw-r--r--+ 1 cons1 cons 21 Oct  7 18:42 plan.txt
# file: plan.txt
# owner: cons1
# group: cons
user::rw-
user:cons3:---
group::rw-			#effective:r--
mask::r--
other::r--

bash: line 1: /srv/lab10/project/consult/plan.txt: Permission denied
--- 5. a default ACL on the directory: setfacl -d -m u:cons3:---,g::rwx consult
# file: srv/lab10/project/consult
# owner: cons1
# group: cons
# flags: -s-
user::rwx
group::rwx
other::---
default:user::rwx
default:user:cons3:---
default:group::rwx
default:mask::rwx
default:other::---

-rw-rw----+ 1 cons1 cons 7 Oct  7 18:42 budget.txt
# file: budget.txt
# owner: cons1
# group: cons
user::rw-
user:cons3:---
group::rwx			#effective:rw-
mask::rw-
other::---

cat: /srv/lab10/project/consult/budget.txt: Permission denied
budget
--- 6. where the ACL is stored: extended attributes of the inode
plan.txt {'system.posix_acl_access': 44}
budget.txt {'system.posix_acl_access': 44}
notes {}
/srv/lab10/project/consult {'system.posix_acl_default': 44}
```

4. lépés: a `chmod g-w` nem nyúlt a `group::rw-` bejegyzéshez; a maszkot csökkentette `r--`-ra, és a csoport tényleges joga `r--` lett, így `cons2` már nem tud hozzáfűzni. 5. lépés: a könyvtáron lévő alapértelmezett ACL mellett `cons1` a szigorú `077`-es umaskkal hozta létre a `budget.txt`-t, a fájl mégis `rw-rw----` a csoport számára, és el van zárva `cons3` elől: az alapértelmezett ACL helyettesítette az umaskot, a kért `0666` mód pedig `rw-`-ra korlátozta a maszkot. (A `# flags: -s-` a `getfacl` módja a setgid bit megjelenítésére.) 6. lépés: az ACL-ek 44 bájtos kiterjesztett attribútumok: 4 bájt fejléc és az öt bejegyzés mindegyikére 8 bájt; a `notes`, amely az alapértelmezett ACL előtt jött létre, nem rendelkezik ilyennel.

### Van-e MAC-policy ezen a gépen?

```console
# ./lsm.sh
--- compiled-in security modules (kernel configuration):
CONFIG_SECURITY_SELINUX=y
# CONFIG_SECURITY_APPARMOR is not set
CONFIG_LSM="landlock,lockdown,yama,loadpin,safesetid,integrity,selinux,smack,tomoyo,apparmor,bpf"
--- the modules actually active, in the order the kernel calls them (securityfs):
lockdown,capability,landlock,selinux,bpf
--- labels as the tools see them:
? /etc/passwd
LABEL                             PID TTY          TIME CMD
kernel                              1 ?        00:00:01 process_api
kernel                              2 ?        00:00:00 kthreadd
id: --context (-Z) works only on an SELinux-enabled kernel
--- the SELinux kernel interface (selinuxfs):
enforce = 0
policy loaded: no
booleans defined: 0
```

Ennek a virtuális gépnek a kernelje tartalmazza a SELinuxot, és az aktív LSM-ek között is szerepel, de soha nem töltöttek be policyt: minden folyamat a kezdeti `kernel` címkét viseli, a fájloknak nincs címkéjük (`?`), nincsenek booleanok, és semmit sem kényszerít ki a rendszer. A capabilityk is egy LSM (`capability` a listában). A szokásos Ubuntu-telepítés helyette AppArmort mutatna; egy Fedora- vagy RHEL-telepítés teljes SELinux-beállítást mutat, amelyet a következő rész tár fel.

### SELinux egy Fedora, RHEL vagy AlmaLinux virtuális gépen

A következő laborhoz Fedorát, Red Hat Enterprise Linuxot, AlmaLinuxot vagy Rocky Linuxot futtató virtuális gép kell (ezeken a SELinux alapértelmezésben enforcing módban van). A parancsok **kimenet nélkül** szerepelnek: futtasd őket, és értelmezd, amit látsz, a [SELinux-szakasz](#selinux-címkék-és-type-enforcement) magyarázatai alapján.

```console
$ getenforce; sestatus                       # mode and policy (expect: Enforcing, targeted)
$ id -Z; ps -eZ | head; ls -Z /etc/shadow    # your context, process domains, a file label
$ sudo dnf install -y httpd policycoreutils-python-utils setroubleshoot-server
$ sudo systemctl enable --now httpd
$ ps -eZ | grep httpd                        # the domain of the web server
$ ls -Zd /var/www/html; sudo semanage fcontext -l | grep '/var/www'

# 1. the mv trap
$ echo 'hello from home' > ~/index.html
$ sudo mv ~/index.html /var/www/html/
$ ls -Z /var/www/html/index.html             # which type did it keep?
$ curl -i http://localhost/index.html        # status code?
$ sudo ausearch -m AVC -ts recent            # the denial: scontext, tcontext, tclass
$ sudo sealert -a /var/log/audit/audit.log   # the explanation and the suggested fix
$ sudo restorecon -v /var/www/html/index.html
$ curl -i http://localhost/index.html

# 2. a web root outside /var/www: temporary and persistent labels
$ sudo mkdir /web; echo 'web root' | sudo tee /web/index.html
$ sudo chcon -R -t httpd_sys_content_t /web; ls -Z /web
$ sudo restorecon -Rv /web; ls -Z /web       # chcon is undone
$ sudo semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'
$ sudo restorecon -Rv /web; ls -Z /web       # now the policy agrees

# 3. ports are labelled too
$ sudo semanage port -l | grep -w http_port_t
$ echo 'Listen 3131' | sudo tee /etc/httpd/conf.d/port3131.conf
$ sudo systemctl restart httpd               # fails: why? (journalctl -xeu httpd, ausearch)
$ sudo semanage port -a -t http_port_t -p tcp 3131
$ sudo systemctl restart httpd; curl -s http://localhost:3131/ | head -3

# 4. booleans and modes
$ getsebool -a | grep httpd | head -20
$ sudo setsebool -P httpd_enable_homedirs on; getsebool httpd_enable_homedirs
$ sudo setenforce 0; getenforce; sudo setenforce 1; getenforce
```

Takaríts el a `sudo rm /etc/httpd/conf.d/port3131.conf`, a `sudo semanage port -d -t http_port_t -p tcp 3131`, a `sudo semanage fcontext -d '/web(/.*)?'` és a `sudo setsebool -P httpd_enable_homedirs off` paranccsal. Egy Ubuntus virtuális gépen az AppArmor megfelelői a `sudo aa-status`, az `/etc/apparmor.d/` könyvtárban lévő profilok, valamint az `aa-complain`/`aa-enforce` (az `apparmor-utils` csomagból).

## Laborfeladatok

1. **Előbb jósold meg, aztán teszteld.** Egy root tulajdonában lévő könyvtár `d--x--x--x`, `dr--r--r--`, `d-wx-wx-wx` és `drwx-wx-wx` módja mellett jósold meg, hogy `user1` végre tudja-e hajtani rajta az `ls`, az `ls -l` és a `cd` parancsot, el tud-e olvasni benne egy ismert nevű fájlt, létre tud-e hozni és törölni tud-e benne fájlt. Ellenőrizd a jóslataidat úgy, hogy a `dirperms.sh` szkriptet kiegészíted egy `ls -l` oszloppal. Mit ír ki az `ls -l` a `dr--r--r--` esetben, és miért?
2. **Oktális gyakorlat.** Váltsd át oktálisra: `rwxr-sr-x`, `rw-r--r-T`, `r-sr-x--x`, `rwSrwSrwT`; és sztringre: `4711`, `2770`, `1755`, `6555`. Minden válaszodat ellenőrizd a `chmod` és a `stat -c '%a %A'` paranccsal. A nyolc mód közül melyikben van olyan speciális bit, amelynek nincs hatása?
3. **Csapatkönyvtár.** Hozd létre a `/srv/team` könyvtárat egy `dev` csoport (két felhasználó) és egy `audit1` ellenőr számára, aki mindent olvashat, de semmit sem módosíthat, úgy, hogy a fejlesztők bármilyen umaskja mellett működjön. Használj setgidet és alapértelmezett ACL-eket. Ezután vizsgáld meg, mi történik az ACL-ekkel, ha egy fejlesztő a saját könyvtárából `cp`-vel, `cp -p`-vel másol be, illetve `mv`-vel mozgat be egy fájlt.
4. **Lemondás a jogosultságokról.** Módosítsd a `showid.c` programot úgy, hogy az effektív UID-del nyissa meg a fájlt, aztán hívja meg a `seteuid(getuid())` függvényt, majd próbálja meg újra megnyitni a fájlt. Mit ír ki a második kísérlet, és miért ez az ajánlott minta? Listázd ki a rendszered setuid és setgid programjait (`find / -perm /6000 -type f 2>/dev/null`), és háromról magyarázd el, miért van szükségük a bitre.
5. **Capability a setuid root helyett.** Másold a `python3`-at `./py` néven, próbáld ki közönséges felhasználóként a `./py -m http.server 80` parancsot, aztán a `setcap` paranccsal add meg a másolatnak csak a `cap_net_bind_service` capabilityt, és próbáld újra. El tudja-e most olvasni ugyanez a program az `/etc/shadow` fájlt? Miért jobb ez, mint setuid rootként beállítani a másolatot?
6. **SELinux.** Végezd el a SELinux-labor négy részét egy Fedora, RHEL vagy AlmaLinux virtuális gépen. Minden elutasításnál írd fel az AVC-üzenetből a forrás contextjét, a cél contextjét, az objektumosztályt és a jogosultságot, valamint azt, hogy a háromféle javítás (címke, boolean, policymodul) közül melyiket javasolta a `sealert`.
7. **AppArmor.** Egy Ubuntus virtuális gépen futtasd az `aa-status` parancsot, válassz ki egy korlátozott programot, és olvasd el a profilját az `/etc/apparmor.d/` könyvtárban. Írj profilt egy saját kis szkriptedhez az `aa-genprof` segítségével, és mutasd meg, hogy egy olyan fájlhoz, amelyet nem olvashat, megtagadják a hozzáférést, akkor is, ha a szkript rootként fut.

## Ellenőrző kérdések

1. Mi az alany, az objektum és a művelet egy hozzáférési döntésben? Mi a hozzáférési mátrix, és hogyan tárolják az ACL-ek és a capability listák?
2. Milyen három tulajdonsággal kell rendelkeznie egy referenciamonitornak? Hol van Linuxban a fájlok referenciamonitora, és miért nem kerülhetik meg a felhasználói programok?
3. Egy kérés eljut egy webszerverhez. Nevezd meg a rétegeket, amelyeken áthalad, mielőtt a szerver beolvas egy fájlt, és magyarázd el, miért hasznos mindegyik réteg, annak ellenére, hogy a többi is létezik!
4. Egy könyvtár módja `d---rwxrwx`, és `john` tulajdonában van. Ki tudja-e listázni `john`? És egy másik felhasználó? Visszaszerezheti-e `john` a hozzáférést, és ha igen, hogyan?
5. Milyen jogosultságok kellenek egy felhasználónak egy fájl törléséhez? Miért törölhet egy felhasználó olyan fájlt, amelyet nem tud elolvasni, és mi akadályozza ezt meg a `/tmp`-ben?
6. Egy felhasználó umaskja `027`. Milyen módot kap egy szerkesztővel létrehozott új fájl és egy új könyvtár? Miért nem ad hozzá soha jogosultságot az umask?
7. Váltsd át oktálisra az `rwsr-S-wt` és a `-wxrwsr-T` módot, a `7640`-et pedig az `ls -l` jelölésére! Mit árul el egy nagy `S` vagy `T`?
8. Magyarázd el, hogyan tudja a `passwd` módosítani az `/etc/shadow` fájlt! Mi a folyamat valós és effektív UID-je? Miért hagyja figyelmen kívül a kernel a setuid bitet a szkripteken és a `nosuid` fájlrendszereken?
9. Mit csinál a setgid bit egy könyvtáron, és miért kombinálják gyakran `002`-es umaskkal vagy alapértelmezett ACL-lel?
10. Miért tud a root elolvasni egy `000` módú fájlt? Hogyan teszik lehetővé a capabilityk, hogy egy program a root hatalmának csak egy részét kapja meg? Adj két példát!
11. Miért nem tudják a módbitek kifejezni azt, hogy „a `cons` csoport, kivéve `cons3`-at”? Mutasd meg az ACL-t, amelyik ki tudja, és magyarázd el, milyen sorrendben ellenőrzi a kernel a bejegyzéseit!
12. Mi az ACL-maszk? Mi történik egy fájl ACL-jével, ha `chmod g-w` vagy `chmod 600` parancsot futtatsz rajta?
13. Állítsd szembe a DAC-ot és a MAC-ot! Miért nem tudja a DAC megállítani a trójai falovat, és hogyan korlátozza a MAC egy rootként futó, eltérített webszerver okozta kárt?
14. Értelmezd mezőnként a `system_u:object_r:httpd_sys_content_t:s0` contextet! Mit enged meg az `allow httpd_t httpd_sys_content_t:file { read open getattr };` szabály, és mi történik azokkal a hozzáférésekkel, amelyeket egyetlen szabály sem említ?
15. Egy saját könyvtárból a `/var/www/html`-be áthelyezett weboldal „403 Forbidden” hibát ad, pedig a módja `644`. Magyarázd el az okát, azt, hogyan lehet megerősíteni, és a helyes javítást! Miért nem tartós javítás a `chcon`, és mi az?
16. Mi a különbség a permissive és a disabled mód között? Miért rossz válasz egy elutasításra a SELinux kikapcsolása?

<details>
<summary><strong>Megoldókulcs (oktatóknak)</strong></summary>

1. Alany: a folyamat (egy felhasználó nevében); objektum: fájl, könyvtár, eszköz, port, folyamat; művelet: olvasás, írás, végrehajtás, törlés, lefoglalás (bind), szignál. A hozzáférési mátrix sorai az alanyok, oszlopai az objektumok, celláiban a megengedett műveletek állnak. Az ACL-ek oszloponként tárolják (az objektummal együtt), a capability listák soronként (az alannyal együtt).
2. Mindig meghívódik (teljes közvetítés), nem lehet belepiszkálni, elég kicsi az ellenőrzéshez. A kernelben, a rendszerhívásokban (`open`, `unlink`, …); a felhasználói kód felhasználói módban fut, és csak rendszerhívásokon keresztül érheti el a fájlokat, amelyeket a kernel kernelmódban hajt végre.
3. Tűzfal (elérhetőség), a szolgáltatás konfigurációja és hitelesítése, DAC (a szolgáltatás felhasználójának fájljai), MAC (rendszerszintű policy), végrehajtás. Minden réteg a többi meghibásodását fedezi: a szolgáltatás hibáját a DAC és a MAC tartja kordában; egy jogosultsági tévedést a MAC; egy rossz MAC-címkét a DAC; a tűzfal elérhetetlenné teszi a nem szükséges szolgáltatásokat.
4. `john` nem tudja (a `---` tulajdonosi hármas dönt, a mindenki más `rwx` joga nem segít). A csoporton kívüli felhasználók igen (mindenki más: `rwx`); a csoport tagjai is (csoport: `rwx`). `john` a tulajdonos, ezért `chmod u+rwx` paranccsal visszaadhatja magának.
5. `w` és `x` a könyvtáron; a fájlon semmi. A törlés egy könyvtárbejegyzést távolít el, ami a könyvtár módosítása. A sticky bit (`1777`) a törlést és az átnevezést csak a fájl tulajdonosának, a könyvtár tulajdonosának és a rootnak engedi meg.
6. Fájlok: 666 AND NOT 027 = `640` (`rw-r-----`); könyvtárak: 777 AND NOT 027 = `750`. Az umaskot a program által kért módból vonjuk le (AND NOT).
7. `7743` és `3374`; a `7640` az `-rwSr-S--T`. A nagybetű azt jelenti, hogy a speciális bit be van állítva, de a megfelelő `x` nem, így általában nincs hatása.
8. A `passwd` a root tulajdonában van, és setuid (`4755`); a folyamat 0-s effektív UID-del és a felhasználó valós UID-jével fut, aki csak a saját bejegyzését változtathatja meg. Szkripteknél versenyhelyzet áll fenn a `#!` kernel általi beolvasása és a fájl értelmező általi megnyitása között, és közben a fájlt ki lehetne cserélni; a `nosuid` csatolások megakadályozzák, hogy setuid programokat hozzanak be cserélhető vagy nem megbízható adathordozón.
9. Az új fájlok és alkönyvtárak a könyvtár csoportját kapják (az alkönyvtárak a setgid bitet is). A setgid a csoportot rögzíti, a biteket nem: a csoport csak akkor írhat, ha a létrehozó umaskja meghagyja a `g+w`-t (`002`), vagy egy alapértelmezett ACL megadja.
10. A root rendelkezik a `CAP_DAC_OVERRIDE` (és a `CAP_DAC_READ_SEARCH`) capabilityvel, amelyek átugorják a jogosultságbiteket. A capabilityk felosztják a root hatalmát; egy program csak néhányat tarthat meg vagy kaphat meg: `cap_net_bind_service` egy 80-as porton futó webszervernek, `cap_dac_read_search` egy mentési olvasónak, `cap_chown` egy fájlszolgáltatásnak. Ha a root lemond mindkét DAC-capabilityről, engedelmeskedik a biteknek (ezt meg is mértük).
11. Csak három osztály van; `cons3` ugyanúgy a csoportosztályba tartozik, mint `cons1` és `cons2`. ACL: `user::rw-, user:cons3:---, group::rw-, mask::rw-, other::---`. Sorrend: tulajdonos → névvel megadott felhasználók → tulajdonos csoport és névvel megadott csoportok (bármely egyezés megadja a jogot, a maszk után) → mindenki más; az első illeszkedő lépés dönt.
12. A felső korlát a névvel megadott felhasználókra, a névvel megadott csoportokra és a tulajdonos csoportra; ACL esetén a mód csoporthármasa a maszk. A `chmod g-w` elveszi a `w`-t a maszkból (a bejegyzések megmaradnak, a tényleges jogok szűkülnek); a `chmod 600` `---`-ra állítja a maszkot, amivel minden névvel megadott bejegyzést és a tulajdonos csoportot is kikapcsolja.
13. DAC: a tulajdonos (és minden program, amelyet futtat) dönt; MAC: egy rendszerszintű policy dönt, és a rootot is köti. A trójai faló a felhasználó jogaival fut, így a DAC jogosnak tekinti a tevékenységét. A MAC a webszerver domainjét a webes tartalomra és a webes portokra korlátozza; egy eltérített szerver nem olvashat adatbázisfájlokat, saját könyvtárakat vagy az `/etc/shadow` fájlt, még rootként sem.
14. SELinux-felhasználó `system_u`, szerep `object_r` (fájlok), típus `httpd_sys_content_t`, szint `s0`. A `httpd_t` domainben futó folyamatok olvashatják, megnyithatják és lekérdezhetik (stat) az ilyen típusú fájlokat. Amit egyetlen szabály sem enged meg, azt a rendszer megtagadja, és AVC-elutasításként naplózza.
15. Az `mv` megtartja az inode régi, `user_home_t` címkéjét, amelyet a `httpd_t` nem olvashat. Megerősítés: `ls -Z` és `ausearch -m AVC` (tcontext `user_home_t`) vagy `sealert`. Javítás: `restorecon -v` (vagy másolás `cp`-vel `mv` helyett). A `chcon` csak a fájl címkéjét módosítja, amit a következő újracímkézés vagy `restorecon` visszaállít; tartós megoldás: `semanage fcontext -a -t … 'path(/.*)?'`, majd `restorecon -Rv`.
16. Permissive: a policy be van töltve, a címkék nyilvántartása folyik, az elutasításokat csak naplózza a rendszer; disabled: nincsenek címkék, nincsenek ellenőrzések, a visszatéréshez teljes újracímkézés kell. A letiltás minden szolgáltatás elől eltávolítja a MAC-réteget; a valódi ok általában egy címke vagy egy boolean, és ezek javításával a védelem megmarad.

**Laborválaszok.** 1. labor: mindenhol `--x`: nincs `ls`, a `cd` és az ismert nevek olvasása működik, létrehozás/törlés nincs; `r--`: a nevek listázhatók, az `ls -l` minden mezőre `?`-et ír ki (és minden bejegyzésre „Permission denied” hibát), mert `x` nélkül az inode-ok nem érhetők el; `-wx`: létrehozás/törlés/megnyitás név szerint, listázás nincs; az `rwx-wx-wx` a mindenki más számára `-wx`. 2. labor: `2755`, `1644`, `4551`, `7666`; `-rws--x--x`, `-rwxrws---`, `-rwxr-xr-t`, `-r-sr-sr-x`. Hatás nélküli: minden nagybetű (a `T` az `1644`-ben, mindhárom a `7666`-ban, amely `rwSrwSrwT` alakban jelenik meg), valamint közönséges fájlon általában a sticky bit (`1755`), amelyet a Linux fájlokon figyelmen kívül hagy. 3. labor: `chmod 2770`, `setfacl -m g:dev:rwx,u:audit1:r-x` és `setfacl -d -m g:dev:rwx,u:audit1:r-x`; a `cp` új fájlt hoz létre, és alkalmazza az alapértelmezett ACL-t; a `cp -p` ehelyett a forrás módját és ACL-jét másolja; az `mv` megtartja az inode-ot a régi ACL-jével és csoportjával. 4. labor: a második megnyitás „Permission denied” hibával meghiúsul: a `seteuid(getuid())` után a folyamat `user1` jogait használja; a jogosultságokról való minél korábbi lemondás korlátozza, mit tehet a program többi részében lévő hiba. 5. labor: a 80-as port lefoglalása `cap_net_bind_service` nélkül meghiúsul, vele sikerül; az `/etc/shadow` olvashatatlan marad, mert a másolatnak nincs DAC-capabilityje; egy setuid-root másolat bármely felhasználónak lehetővé tenné, hogy tetszőleges Python-kódot futtasson rootként (például `os.setuid(0)`, majd bármilyen parancs).

</details>

## Irodalom

Anderson, J. P. (1972). *Computer security technology planning study* (ESD-TR-73-51, Vol. II). Electronic Systems Division, Air Force Systems Command.

Bell, D. E., & LaPadula, L. J. (1976). *Secure computer system: Unified exposition and Multics interpretation* (MTR-2997 Rev. 1, ESD-TR-75-306). The MITRE Corporation.

Grünbacher, A. (2003). POSIX access control lists on Linux. In *Proceedings of the FREENIX Track: 2003 USENIX Annual Technical Conference*. USENIX Association. https://www.usenix.org/legacy/events/usenix03/tech/freenix03/full_papers/gruenbacher/gruenbacher_html/index.html

Kerrisk, M. (2010). *The Linux programming interface: A Linux and UNIX system programming handbook*. No Starch Press.

Lampson, B. W. (1974). Protection. *ACM SIGOPS Operating Systems Review, 8*(1), 18–24. https://doi.org/10.1145/775265.775268

Linux man-pages project. (n.d.-a). *acl(5): Access control lists*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man5/acl.5.html

Linux man-pages project. (n.d.-b). *capabilities(7): Overview of Linux capabilities*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man7/capabilities.7.html

Linux man-pages project. (n.d.-c). *chmod(1): Change file mode bits*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man1/chmod.1.html

Linux man-pages project. (n.d.-d). *setfacl(1): Set file access control lists*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man1/setfacl.1.html

Loscocco, P., & Smalley, S. (2001). Integrating flexible support for security policies into the Linux operating system. In *Proceedings of the FREENIX Track: 2001 USENIX Annual Technical Conference*. USENIX Association. https://www.usenix.org/legacy/events/usenix01/freenix01/loscocco.html

Microsoft. (n.d.-a). *Access control lists*. Retrieved October 7, 2026, from https://learn.microsoft.com/en-us/windows/win32/secauthz/access-control-lists

Microsoft. (n.d.-b). *Mandatory integrity control*. Retrieved October 7, 2026, from https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control

Red Hat. (n.d.). *Using SELinux: Red Hat Enterprise Linux 9*. Retrieved October 7, 2026, from https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/index

Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proceedings of the IEEE, 63*(9), 1278–1308. https://doi.org/10.1109/PROC.1975.9939

Smalley, S., Vance, C., & Salamon, W. (2001). *Implementing SELinux as a Linux security module* (NAI Labs Report #01-043). NAI Labs.

Wright, C., Cowan, C., Smalley, S., Morris, J., & Kroah-Hartman, G. (2002). Linux security modules: General security support for the Linux kernel. In *Proceedings of the 11th USENIX Security Symposium* (pp. 17–31). USENIX Association.

## További olvasnivaló

Arpaci-Dusseau, R. H., & Arpaci-Dusseau, A. C. (2023). *Operating systems: Three easy pieces* (Version 1.10). Arpaci-Dusseau Books. https://pages.cs.wisc.edu/~remzi/OSTEP/ (a 39. fejezet a fájlokról és könyvtárakról, a jogosultságokkal együtt)

Mayer, F., MacMillan, K., & Caplan, D. (2006). *SELinux by example: Using security enhanced Linux*. Prentice Hall.

The kernel development community. (n.d.). *Linux Security Module development*. The Linux Kernel documentation. https://docs.kernel.org/security/lsm-development.html
