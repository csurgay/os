#!/usr/bin/env python3
"""heap.py MB [HOLD] - allocate MB MiB that looks like an app's heap: every 4 KiB page
holds 1 KiB of random bytes and 3 KiB of zeros, so it compresses about 3-4x.
Prints its progress every 50 MiB, reads the data back to check it, then
keeps it for HOLD seconds (default 0)."""
import hashlib, os, sys, time
mb = int(sys.argv[1])
pages, h = [], hashlib.sha256()
for i in range(mb * 256):
    p = os.urandom(1024) + bytes(3072)
    h.update(p)
    pages.append(bytearray(p))
    if (i + 1) % (50 * 256) == 0:
        print(f"heap.py: {(i + 1) // 256} MiB allocated", flush=True)
check = hashlib.sha256()
for p in pages:
    check.update(p)
print("heap.py: all data read back intact:", check.digest() == h.digest(), flush=True)
time.sleep(float(sys.argv[2]) if len(sys.argv) > 2 else 0)
