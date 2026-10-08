#!/usr/bin/env python3
"""eat.py - allocate memory 10 MiB at a time (and really touch it)."""
b = []
for i in range(1, 11):
    b.append(bytearray(10 * 2**20))
    print(i * 10, "MiB", flush=True)
