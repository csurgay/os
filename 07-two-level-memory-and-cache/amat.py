#!/usr/bin/env python3
"""amat.py - average memory access time of a two-level memory, T = H*Tc + (1-H)*Tm.

Usage: python3 amat.py TC TM            table for hit rates 50 ... 99.9 %
       python3 amat.py TC TM H          one hit rate (0..1)
Times in any unit (ns). Note: some books charge a miss Tc + Tm (the cache is
checked first); the simpler formula here charges Tm.
"""
import sys

def amat(h, tc, tm):
    return h * tc + (1 - h) * tm

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    tc, tm = float(sys.argv[1]), float(sys.argv[2])
    rates = [float(sys.argv[3])] if len(sys.argv) > 3 else [0.5, 0.8, 0.9, 0.95, 0.98, 0.99, 0.999]
    print(f"cache {tc:g} ns, main memory {tm:g} ns")
    for h in rates:
        t = amat(h, tc, tm)
        print(f"  H = {100 * h:5.1f}%:  T = {t:7.2f} ns  ({tm / t:5.1f}x faster than memory alone, "
              f"{t / tc:4.1f}x slower than the cache)")
