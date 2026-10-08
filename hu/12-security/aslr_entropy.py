"""Run ./aslr many times and estimate how random each address is.

usage: python3 aslr_entropy.py ./aslr 2000

For every region it prints how many different addresses appeared, the
alignment (the lowest address bit that ever changed) and an estimate of the
entropy: log2 of (highest - lowest) / alignment, the number of random bits
that an attacker would have to guess.
"""
import math
import subprocess
import sys

prog, runs = sys.argv[1], int(sys.argv[2])
seen = {}
for _ in range(runs):
    out = subprocess.run([prog], capture_output=True, text=True).stdout
    for line in out.splitlines():
        name, addr = line.rsplit(None, 1)
        seen.setdefault(name, set()).add(int(addr, 16))

print(f"{'region':15} {'distinct':>8} {'alignment':>10} {'entropy':>8}   lowest .. highest")
for name, vals in seen.items():
    lo, hi = min(vals), max(vals)
    varying = 0
    for v in vals:
        varying |= v ^ lo                      # every bit that ever differed
    if not varying:
        print(f"{name:15} {len(vals):8} {'-':>10} {'0 bits':>8}   {lo:#x}")
        continue
    align = varying & -varying                 # lowest bit that changed
    bits = math.log2((hi - lo) // align + 1)
    print(f"{name:15} {len(vals):8} {align:>#10x} {bits:5.1f} bits   {lo:#x} .. {hi:#x}")
