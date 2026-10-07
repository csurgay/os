#!/usr/bin/env python3
"""fat16.py - read and write a FAT16 file system image, to see how FAT works.

Only the root directory and 8.3 names are supported; that is enough to see the
boot sector, the file allocation table and the directory entries at work.

usage:
  python3 fat16.py info IMAGE              the boot sector (BIOS parameter block)
  python3 fat16.py ls   IMAGE              the root directory, including deleted entries
  python3 fat16.py fat  IMAGE [N]          the first N entries of the FAT (default 24)
  python3 fat16.py add  IMAGE HOSTFILE NAME.EXT   copy a file in (first-fit allocation)
  python3 fat16.py rm   IMAGE NAME.EXT     delete a file as DOS did
  python3 fat16.py cat  IMAGE NAME.EXT     follow the cluster chain and print the data
  python3 fat16.py raw  IMAGE [N]          hex dump of the first N root directory entries

Make an image first, e.g.:  truncate -s 32M fat.img && mkfs.fat -F 16 -s 4 fat.img
"""
import struct
import sys
import time

FREE, EOC = 0x0000, 0xFFFF


class Fat16:
    def __init__(self, path):
        self.path = path
        self.img = bytearray(open(path, "rb").read())
        b = self.img
        (self.bps, self.spc, self.reserved, self.nfats, self.rootents,
         tot16, self.media, self.fatsz) = struct.unpack_from("<HBHBHHBH", b, 11)
        tot32, = struct.unpack_from("<I", b, 32)
        self.total = tot16 or tot32
        self.label = bytes(b[43:54]).decode("ascii", "replace")
        self.fstype = bytes(b[54:62]).decode("ascii", "replace")
        self.fat_start = self.reserved * self.bps                       # bytes
        self.root_start = self.fat_start + self.nfats * self.fatsz * self.bps
        self.root_bytes = self.rootents * 32
        self.data_start = self.root_start + self.root_bytes
        self.csize = self.spc * self.bps
        self.nclusters = (self.total * self.bps - self.data_start) // self.csize

    # --- the file allocation table --------------------------------------------
    def fat(self, n):
        return struct.unpack_from("<H", self.img, self.fat_start + 2 * n)[0]

    def set_fat(self, n, value):
        for i in range(self.nfats):                 # every copy of the FAT is updated
            struct.pack_into("<H", self.img, self.fat_start + i * self.fatsz * self.bps + 2 * n, value)

    def chain(self, first):
        out = []
        while 2 <= first < 0xFFF8:
            out.append(first)
            first = self.fat(first)
        return out

    def cluster_offset(self, n):
        return self.data_start + (n - 2) * self.csize

    # --- the root directory ---------------------------------------------------
    def entries(self):
        for i in range(self.rootents):
            off = self.root_start + 32 * i
            e = self.img[off:off + 32]
            if e[0] == 0x00:                          # end of the directory
                return
            yield off, e

    @staticmethod
    def name83(e):
        base = bytes(e[0:8]).decode("ascii", "replace").rstrip()
        ext = bytes(e[8:11]).decode("ascii", "replace").rstrip()
        return base + ("." + ext if ext else "")

    def find(self, name):
        for off, e in self.entries():
            if e[0] != 0xE5 and not e[11] & 0x08 and self.name83(e) == name.upper():
                return off, e
        sys.exit(f"{name}: not found")

    def save(self):
        open(self.path, "r+b").write(self.img)

    # --- commands -------------------------------------------------------------
    def info(self):
        print(f"file system type field : {self.fstype!r}")
        print(f"volume label           : {self.label!r}")
        print(f"bytes per sector       : {self.bps}")
        print(f"sectors per cluster    : {self.spc}  (cluster = {self.csize} bytes)")
        print(f"reserved sectors       : {self.reserved}  (the boot sector is the first)")
        print(f"number of FATs         : {self.nfats}")
        print(f"sectors per FAT        : {self.fatsz}")
        print(f"root directory entries : {self.rootents}  ({self.root_bytes // self.bps} sectors)")
        print(f"total sectors          : {self.total}  ({self.total * self.bps // 2**20} MiB)")
        print(f"data clusters          : {self.nclusters}  (numbered 2 .. {self.nclusters + 1})")
        print("layout (sector numbers):")
        s = lambda byte: byte // self.bps
        print(f"  boot sector + reserved  0 .. {self.reserved - 1}")
        for i in range(self.nfats):
            a = self.reserved + i * self.fatsz
            print(f"  FAT #{i + 1}                {a} .. {a + self.fatsz - 1}")
        print(f"  root directory          {s(self.root_start)} .. {s(self.data_start) - 1}")
        print(f"  data area (cluster 2 ..) {s(self.data_start)} .. {self.total - 1}")

    def ls(self):
        print(f"{'entry':>5}  {'name':<12} {'attr':<5} {'size':>7}  first  cluster chain")
        for off, e in self.entries():
            idx = (off - self.root_start) // 32
            attr = e[11]
            first, size = struct.unpack_from("<HI", e, 26)
            if attr == 0x0F:
                print(f"{idx:>5}  (long-name part)")
                continue
            if attr & 0x08:
                print(f"{idx:>5}  {self.name83(e):<12} label")
                continue
            if e[0] == 0xE5:
                name = "?" + self.name83(e)[1:]
                print(f"{idx:>5}  {name:<12} {'del':<5} {size:>7}  {first:>5}  (deleted: 0xE5 in byte 0)")
                continue
            flags = ("D" if attr & 0x10 else "-") + ("A" if attr & 0x20 else "-")
            ch = self.chain(first)
            text = " -> ".join(map(str, ch[:12])) + (" ..." if len(ch) > 12 else "") + " -> EOC"
            print(f"{idx:>5}  {self.name83(e):<12} {flags:<5} {size:>7}  {first:>5}  {text}")

    def show_fat(self, n=24):
        words = []
        for i in range(n):
            v = self.fat(i)
            if i < 2:
                t = f"{v:#06x}"
            elif v == FREE:
                t = "free"
            elif v >= 0xFFF8:
                t = "EOC"
            elif v == 0xFFF7:
                t = "bad"
            else:
                t = str(v)
            words.append(f"[{i:>2}] {t:<6}")
        for i in range(0, n, 6):
            print("  ".join(words[i:i + 6]))

    def raw(self, n=4):
        for i in range(n):
            off = self.root_start + 32 * i
            for half in (0, 16):
                chunk = self.img[off + half:off + half + 16]
                hexpart = " ".join(f"{c:02x}" for c in chunk)
                text = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
                print(f"{off + half:08x}: {hexpart}  {text}")

    def add(self, hostfile, name):
        data = open(hostfile, "rb").read()
        base, _, ext = name.upper().partition(".")
        if len(base) > 8 or len(ext) > 3:
            sys.exit("only 8.3 names are supported")
        need = max(1, -(-len(data) // self.csize))
        clusters = [n for n in range(2, self.nclusters + 2) if self.fat(n) == FREE][:need]  # first fit
        if len(clusters) < need:
            sys.exit("disk full")
        for i, n in enumerate(clusters):
            chunk = data[i * self.csize:(i + 1) * self.csize]
            off = self.cluster_offset(n)
            self.img[off:off + self.csize] = chunk.ljust(self.csize, b"\0")
            self.set_fat(n, clusters[i + 1] if i + 1 < need else EOC)
        slot = None
        for i in range(self.rootents):                        # first free directory slot
            off = self.root_start + 32 * i
            if self.img[off] in (0x00, 0xE5):
                slot = off
                break
        if slot is None:
            sys.exit("root directory full")
        t = time.localtime()
        dos_time = (t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)
        dos_date = ((t.tm_year - 1980) << 9) | (t.tm_mon << 5) | t.tm_mday
        e = bytearray(32)
        e[0:11] = (base.ljust(8) + ext.ljust(3)).encode("ascii")
        e[11] = 0x20                                          # archive bit
        struct.pack_into("<HHHH", e, 14, dos_time, dos_date, dos_date, 0)  # created, accessed
        struct.pack_into("<HHHI", e, 22, dos_time, dos_date, clusters[0], len(data))
        self.img[slot:slot + 32] = e
        self.save()
        print(f"{name.upper()}: {len(data)} bytes in {need} cluster(s): {clusters}")

    def rm(self, name):
        off, e = self.find(name)
        first = struct.unpack_from("<H", e, 26)[0]
        ch = self.chain(first)
        for n in ch:
            self.set_fat(n, FREE)                             # the chain is forgotten ...
        self.img[off] = 0xE5                                  # ... and the name loses its first byte
        self.save()
        print(f"{name.upper()}: entry marked 0xE5, clusters {ch} marked free; the data is still there")

    def cat(self, name):
        off, e = self.find(name)
        first, size = struct.unpack_from("<HI", e, 26)
        out = b"".join(self.img[self.cluster_offset(n):self.cluster_offset(n) + self.csize]
                       for n in self.chain(first))
        sys.stdout.buffer.write(out[:size])


def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    fs = Fat16(a[1])
    cmd = a[0]
    if cmd == "info":
        fs.info()
    elif cmd == "ls":
        fs.ls()
    elif cmd == "fat":
        fs.show_fat(int(a[2]) if len(a) > 2 else 24)
    elif cmd == "add":
        fs.add(a[2], a[3])
    elif cmd == "rm":
        fs.rm(a[2])
    elif cmd == "raw":
        fs.raw(int(a[2]) if len(a) > 2 else 4)
    elif cmd == "cat":
        fs.cat(a[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
