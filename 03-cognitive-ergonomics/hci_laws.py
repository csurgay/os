#!/usr/bin/env python3
"""hci_laws.py - the two classic laws of pointing and choosing, as numbers.

Usage:
  python3 hci_laws.py fitts D W [D W ...]   Fitts' law: index of difficulty of reaching a target
                                            of width W at distance D (same units, e.g. pixels)
  python3 hci_laws.py hick N [N ...]        Hick-Hyman law: predicted decision cost, in bits,
                                            of choosing 1 of N equally likely items
  python3 hci_laws.py menu                  one flat menu of 64 items versus 8 x 8 and 4 x 4 x 4
"""
import sys
from math import log2

def fitts_id(d, w):
    return log2(d / w + 1)          # Shannon formulation (MacKenzie, 1992), in bits

def hick_bits(n):
    return log2(n + 1)              # +1: Hick (1952) counted the possibility that no stimulus occurs

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "fitts" and len(a) >= 3 and len(a) % 2 == 1:
        for d, w in zip(map(float, a[1::2]), map(float, a[2::2])):
            print(f"distance {d:6.0f}, width {w:5.0f}: ID = {fitts_id(d, w):4.2f} bits")
    elif a and a[0] == "hick" and len(a) >= 2:
        for n in map(int, a[1:]):
            print(f"{n:3d} choices: {hick_bits(n):4.2f} bits")
    elif a == ["menu"]:
        for name, levels in [("1 level of 64", [64]), ("2 levels of 8", [8, 8]),
                             ("3 levels of 4", [4, 4, 4])]:
            bits = sum(hick_bits(n) for n in levels)
            print(f"{name:14}: {len(levels)} decisions, predicted cost {bits:4.2f} bits, "
                  f"at most {max(levels)} items in view at once")
    else:
        print(__doc__)
