#!/usr/bin/env python3
"""cachesim.py - a small cache simulator for the two-level memory lecture.

Usage:
  python3 cachesim.py split ADDR            split a 32-bit address for the toy direct-mapped
                                            cache (1024 lines of 16 KiB: 8-bit tag, 10-bit index,
                                            14-bit offset), in the usual tag|index|offset order
  python3 cachesim.py small ADDR...        split 32-bit addresses for a small direct-mapped cache
                                            (1024 lines of 4 bytes = 4 KiB: 20-bit tag, 10-bit
                                            index, 2-bit offset), in binary and hexadecimal
  python3 cachesim.py traverse [N]          row-by-row vs column-by-column sum of an N x N int
                                            matrix through a 32 KiB, 8-way, 64-byte-line cache
  python3 cachesim.py blocksize             miss rate against line size, cache size fixed
  python3 cachesim.py assoc                 direct-mapped vs set-associative vs fully associative
  python3 cachesim.py replace               replacement policies on a fully associative cache
  python3 cachesim.py order                 tag|index|offset vs index|tag|offset on a repeated scan
"""
import random, sys
from collections import OrderedDict

class Cache:
    """size and line in bytes; ways = 0 means fully associative."""
    def __init__(self, size, line, ways=1, policy="lru", index_high=False):
        self.line, self.lines = line, size // line
        self.ways = self.lines if ways == 0 else ways
        self.sets = self.lines // self.ways
        self.policy, self.index_high = policy, index_high
        self.set = [OrderedDict() for _ in range(self.sets)]   # tag -> age (per set)
        self.hits = self.misses = 0
        self.clock = 0
        self.future = None                                     # for OPT

    def split(self, addr, bits=32):
        off_bits = self.line.bit_length() - 1
        idx_bits = self.sets.bit_length() - 1
        block = addr >> off_bits
        if self.index_high:                                    # index in the top bits
            tag_bits = bits - off_bits - idx_bits
            return block >> tag_bits, block & ((1 << tag_bits) - 1)
        return block % self.sets, block // self.sets           # (index, tag)

    def access(self, addr, pos=None):
        idx, tag = self.split(addr)
        s = self.set[idx]
        self.clock += 1
        if self.policy == "aging":                             # counter aging: everyone ages +1
            for t in s: s[t] += 1
        if tag in s:
            self.hits += 1
            if self.policy == "lru": s.move_to_end(tag)
            elif self.policy == "aging": s[tag] //= 2          # a hit halves the age
            return True
        self.misses += 1
        if len(s) >= self.ways:                                # set full: choose a victim
            if self.policy in ("lru", "fifo"): s.popitem(last=False)
            elif self.policy == "random": s.pop(random.choice(list(s)))
            elif self.policy == "aging": s.pop(max(s, key=s.get))
            elif self.policy == "opt":                         # Belady: used farthest in future
                s.pop(max(s, key=lambda t: self.next_use(idx, t, pos)))
        s[tag] = 0
        return False

    def next_use(self, idx, tag, pos):
        for p in self.future.get((idx, tag), []):
            if p > pos: return p
        return float("inf")

    def run(self, trace):
        if self.policy == "opt":
            self.future = {}
            for p, a in enumerate(trace):
                self.future.setdefault(self.split(a), []).append(p)
        for p, a in enumerate(trace):
            self.access(a, p)
        return self.misses / (self.hits + self.misses)

def matrix_trace(n, by_rows, base=0x10000):
    return [base + 4 * (i * n + j) if by_rows else base + 4 * (j * n + i)
            for i in range(n) for j in range(n)]

def mixed_trace(seed=1, hot=32, scan=512, reps=60):
    """Both kinds of locality: 32 "hot" variables scattered over 1 MiB, used
    again and again (temporal locality only), and sequential scans of 2 KiB
    pieces of a large array (spatial locality only)."""
    r, t = random.Random(seed), []
    hot_addr = [0x400000 + 64 * r.randrange(1 << 14) for _ in range(hot)]
    for rep in range(reps):
        for _ in range(3):
            t.extend(hot_addr)
        start = 0x100000 + r.randrange(1 << 12) * 64
        t.extend(start + 4 * k for k in range(scan))
    return t

def loop_trace(hot, loop, reps=100, seed=1):
    """A loop over `loop` cache lines, with references to `hot` other lines
    mixed in at random (half of the loop steps)."""
    r, t = random.Random(seed), []
    hot_addr = [0x400000 + 64 * 37 * k for k in range(hot)]
    for rep in range(reps):
        for k in range(loop):
            t.append(0x100000 + 64 * k)
            if r.random() < 0.5:
                t.append(r.choice(hot_addr))
    return t

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "split":
        a = int(sys.argv[2], 0)
        c = Cache(1024 * 16384, 16384)
        idx, tag = c.split(a)
        print(f"address {a:#010x} = tag {tag:#04x} | index {idx} | offset {a & 0x3FFF:#06x} "
              f"(word {(a & 0x3FFF) // 4} of the 4096 in the line)")
    elif cmd == "small":
        c = Cache(1024 * 4, 4)
        print("cache: 1024 lines x 4 bytes = 4 KiB, direct-mapped; tag 20 | index 10 | offset 2 bits")
        for arg in sys.argv[2:]:
            a = int(arg, 0)
            idx, tag = c.split(a)
            b = f"{a:032b}"
            print(f"{a:#010x} = {b[:20]} | {b[20:30]} | {b[30:]}  -> tag {tag:#07x}, line {idx}, byte {a & 3}")
    elif cmd == "traverse":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 256
        for rows in (True, False):
            c = Cache(32 * 1024, 64, 8)
            m = c.run(matrix_trace(n, rows))
            print(f"{'row by row      ' if rows else 'column by column'}: {c.misses:7d} misses of {n*n} accesses, miss rate {100*m:5.1f}%")
    elif cmd == "blocksize":
        t = mixed_trace()
        print(f"{len(t)} accesses, cache 4 KiB, 4-way set-associative")
        for line in (4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096):
            c = Cache(4096, line, 4 if 4096 // line >= 4 else 0)
            print(f"line {line:5d} B ({4096 // line:4d} lines): miss rate {100 * c.run(t):5.1f}%")
    elif cmd == "assoc":
        # two arrays exactly one cache size (8 KiB) apart, used alternately: a[i] += b[i]
        t = [x for i in range(2048) for x in (0x10000 + 4 * i, 0x10000 + 8192 + 4 * i)] * 4
        for ways, name in ((1, "direct-mapped"), (2, "2-way"), (4, "4-way"), (0, "fully associative")):
            c = Cache(8192, 64, ways)
            print(f"{name:18}: miss rate {100 * c.run(t):5.1f}%")
    elif cmd == "replace":
        print("fully associative, 64 lines of 64 B; miss rates:")
        print(f"{'workload':34}" + "".join(f"{p:>8}" for p in ("lru", "fifo", "random", "aging", "opt")))
        for hot, loop in ((16, 56), (32, 40)):
            t, row = loop_trace(hot, loop), ""
            for pol in ("lru", "fifo", "random", "aging", "opt"):
                random.seed(3)
                row += f"{100 * Cache(4096, 64, 0, pol).run(t):7.1f}%"
            print(f"loop of {loop} lines + {hot} hot lines   " + row)
    elif cmd == "order":
        t = list(range(0x100000, 0x100000 + 128 * 1024, 4)) * 2     # a 128 KiB array, twice
        print("a 128 KiB array read twice through a 256 KiB direct-mapped cache (64 B lines):")
        for high, name in ((False, "tag | index | offset"), (True, "index | tag | offset")):
            c = Cache(256 * 1024, 64, 1, index_high=high)
            m = c.run(t)
            print(f"  {name}: {c.misses:6d} misses, miss rate {100 * m:4.1f}%")
    else:
        print(__doc__)
