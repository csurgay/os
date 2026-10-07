#!/usr/bin/env python3
"""pagesim.py - page replacement algorithms on a reference string.

Usage:
  python3 pagesim.py belady                 the lecture notes' example, FIFO with 3 and 4 frames
  python3 pagesim.py table [PAGES...]       faults of FIFO, LRU, OPT, clock and random for 1..7 frames
  python3 pagesim.py trace ALG N PAGES...   step-by-step table for one algorithm and N frames
  python3 pagesim.py thrash                 fault rate against frames for a program with phases
"""
import random, sys

NOTES = [3, 2, 1, 0, 3, 2, 4, 3, 2, 1, 0, 4]          # the reference string in the notes

def simulate(refs, frames, alg, seed=1):
    """Returns (faults, history); history[i] = (page, fault?, frame contents)."""
    rnd = random.Random(seed)
    mem, hist, faults = [], [], 0          # mem: list of pages; order depends on the algorithm
    ref_bit, hand = {}, 0
    for i, p in enumerate(refs):
        fault = p not in mem
        if fault:
            faults += 1
            if len(mem) < frames:
                mem.append(p)
            else:
                if alg == "fifo":                       # oldest loaded = front of the list
                    mem.pop(0); mem.append(p)
                elif alg == "lru":                      # least recently used = front
                    mem.pop(0); mem.append(p)
                elif alg == "opt":                      # used farthest in the future (Belady)
                    def nxt(q):
                        try: return refs.index(q, i + 1)
                        except ValueError: return float("inf")
                    victim = max(mem, key=nxt)
                    mem[mem.index(victim)] = p
                elif alg == "random":
                    mem[rnd.randrange(frames)] = p
                elif alg == "clock":                    # second chance: skip pages used since last pass
                    while ref_bit.get(mem[hand], 0):
                        ref_bit[mem[hand]] = 0
                        hand = (hand + 1) % frames
                    mem[hand] = p
                    hand = (hand + 1) % frames
            ref_bit[p] = 1
        else:
            ref_bit[p] = 1
            if alg == "lru":                            # move to the most recently used end
                mem.remove(p); mem.append(p)
        hist.append((p, fault, list(mem)))
    return faults, hist

def print_trace(refs, frames, alg):
    faults, hist = simulate(refs, frames, alg)
    print(f"{alg.upper()}, {frames} frames (frames listed newest first for FIFO/LRU):")
    print("  reference: " + " ".join(f"{p:>2}" for p, _, _ in hist))
    for row in range(frames):
        cells = []
        for _, _, mem in hist:
            order = list(reversed(mem)) if alg in ("fifo", "lru") else mem
            cells.append(f"{order[row]:>2}" if row < len(order) else "  ")
        print(f"  frame {row + 1}:   " + " ".join(cells))
    print("  fault:     " + " ".join(" *" if f else "  " for _, f, _ in hist) + f"   -> {faults} faults")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["belady"]:
        print_trace(NOTES, 3, "fifo"); print(); print_trace(NOTES, 4, "fifo")
    elif a[:1] == ["table"]:
        refs = [int(x) for x in a[1:]] or NOTES
        print("reference string:", " ".join(map(str, refs)))
        print(f"{'frames':>6}" + "".join(f"{alg:>8}" for alg in ("fifo", "lru", "opt", "clock", "random")))
        for n in range(1, 8):
            print(f"{n:>6}" + "".join(f"{simulate(refs, n, alg)[0]:>8}" for alg in ("fifo", "lru", "opt", "clock", "random")))
    elif a[:1] == ["trace"]:
        print_trace([int(x) for x in a[3:]], int(a[2]), a[1])
    elif a[:1] == ["thrash"]:
        # a program in three phases, each looping over its own 12 pages (its working set),
        # with an occasional reference to 30 rarely used pages
        r, refs = random.Random(7), []
        for phase in range(3):
            ws = list(range(phase * 12, phase * 12 + 12))
            for _ in range(2000):
                refs.append(r.choice(ws) if r.random() < 0.97 else 100 + r.randrange(30))
        print(f"{len(refs)} references, 3 phases with a working set of 12 pages each")
        print(f"{'frames':>6} {'LRU faults':>11} {'fault rate':>11}")
        for n in (4, 6, 8, 10, 11, 12, 13, 14, 16, 20, 24):
            f = simulate(refs, n, "lru")[0]
            print(f"{n:>6} {f:>11} {100 * f / len(refs):>10.1f}%  " + "#" * round(50 * f / len(refs)))
    else:
        print(__doc__)
