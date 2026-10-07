#!/usr/bin/env python3
"""ftlsim.py - a small simulator of the flash translation layer (FTL) inside an SSD.

Flash memory can only be written a page at a time into an erased page, and only
erased a whole block (many pages) at a time.  The FTL therefore writes every new
version of a logical page into a fresh physical page, remembers the new location in
a mapping table, and marks the old copy invalid.  When it runs out of erased blocks,
garbage collection picks a victim block, copies its still-valid pages elsewhere and
erases it.  Those copies are extra writes: write amplification.

usage:
  python3 ftlsim.py op          write amplification against over-provisioning (random writes)
  python3 ftlsim.py workload    random vs sequential writes, and the effect of TRIM
"""
import random
import sys

PAGES_PER_BLOCK = 64
BLOCKS = 1024                          # 65 536 physical pages (a "256 MiB" SSD with 4 KiB pages)


class SSD:
    def __init__(self, op):
        self.npages = BLOCKS * PAGES_PER_BLOCK
        self.logical = int(self.npages * (1 - op))     # pages the host can address
        self.map = [-1] * self.logical                 # logical page -> physical page
        self.owner = [-1] * self.npages                # physical page -> logical page (or -1)
        self.valid = [0] * BLOCKS                      # valid pages per block
        self.erases = [0] * BLOCKS
        self.free = list(range(BLOCKS))                # erased blocks
        self.cur, self.ptr = self.free.pop(), 0        # block being filled, next page in it
        self.host_writes = self.flash_writes = 0

    def _program(self, lpage):
        if self.ptr == PAGES_PER_BLOCK:                # current block full: take an erased one
            self.cur, self.ptr = self.free.pop(), 0
        p = self.cur * PAGES_PER_BLOCK + self.ptr
        self.ptr += 1
        self.owner[p] = lpage
        self.map[lpage] = p
        self.valid[self.cur] += 1
        self.flash_writes += 1

    def _invalidate(self, lpage):
        old = self.map[lpage]
        if old >= 0:
            self.owner[old] = -1
            self.valid[old // PAGES_PER_BLOCK] -= 1
            self.map[lpage] = -1

    def _gc(self):
        while len(self.free) < 2:                      # keep two erased blocks in reserve
            busy = {self.cur}
            victim = min((b for b in range(BLOCKS) if b not in busy and b not in self.free),
                         key=lambda b: self.valid[b])  # greedy: the block with fewest valid pages
            for p in range(victim * PAGES_PER_BLOCK, (victim + 1) * PAGES_PER_BLOCK):
                lp = self.owner[p]
                if lp >= 0:                            # still valid: copy it (extra write)
                    self._invalidate(lp)
                    self._program(lp)
            self.erases[victim] += 1
            self.free.insert(0, victim)

    def write(self, lpage):
        self._invalidate(lpage)
        self._gc()
        self._program(lpage)
        self.host_writes += 1

    def trim(self, lpage):                             # the host says: this page is no longer used
        self._invalidate(lpage)


def run(op, pattern="random", trim_fraction=0.0, rounds=6, seed=1):
    random.seed(seed)
    ssd = SSD(op)
    n = ssd.logical
    for lp in range(n):                                # fill the drive once
        ssd.write(lp)
    if trim_fraction:                                  # delete files, and tell the drive
        for lp in range(int(n * (1 - trim_fraction)), n):
            ssd.trim(lp)
    used = int(n * (1 - trim_fraction))
    h0, f0 = ssd.host_writes, ssd.flash_writes
    for i in range(rounds * n):
        lp = random.randrange(used) if pattern == "random" else i % used
        ssd.write(lp)
    wa = (ssd.flash_writes - f0) / (ssd.host_writes - h0)
    return wa, min(ssd.erases), max(ssd.erases)


def main(a):
    mode = a[0] if a else "op"
    if mode == "op":
        print(f"{BLOCKS} blocks of {PAGES_PER_BLOCK} pages, random 4 KiB writes, greedy garbage collection")
        print("spare flash  write amplification   erases per block (min..max)")
        for op in (0.07, 0.12, 0.20, 0.28, 0.40, 0.50):
            wa, lo, hi = run(op)
            print(f"   {op:4.0%}           {wa:5.2f}               {lo} .. {hi}")
    elif mode == "workload":
        print("spare flash 7%")
        for name, pattern, trim in (("random writes, drive full        ", "random", 0.0),
                                    ("random writes, 25% trimmed       ", "random", 0.25),
                                    ("sequential writes, drive full    ", "seq", 0.0)):
            wa, lo, hi = run(0.07, pattern, trim)
            print(f"{name} write amplification {wa:5.2f}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
