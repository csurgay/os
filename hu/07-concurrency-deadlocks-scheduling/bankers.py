#!/usr/bin/env python3
"""bankers.py - Dijkstra's banker's algorithm: is this state safe?

A state is safe if there is an order in which every process can obtain its
maximum claim and finish. The example has 5 processes and 3 resource types
(think: 10 tape drives, 5 printers, 7 scanners), as in Silberschatz et al.
Usage: python3 bankers.py            check the example state
       python3 bankers.py P1 1 0 2   ...and then a request of P1 for (1, 0, 2)
"""
import sys

total      = [10, 5, 7]
allocation = {"P0": [0, 1, 0], "P1": [2, 0, 0], "P2": [3, 0, 2], "P3": [2, 1, 1], "P4": [0, 0, 2]}
maximum    = {"P0": [7, 5, 3], "P1": [3, 2, 2], "P2": [9, 0, 2], "P3": [2, 2, 2], "P4": [4, 3, 3]}

def available(alloc):
    return [t - sum(a[r] for a in alloc.values()) for r, t in enumerate(total)]

def safe_sequence(alloc):
    work = available(alloc)
    need = {p: [m - a for m, a in zip(maximum[p], alloc[p])] for p in alloc}
    finished, order = set(), []
    while len(finished) < len(alloc):
        for p in alloc:                                   # find one that can finish now
            if p not in finished and all(n <= w for n, w in zip(need[p], work)):
                work = [w + a for w, a in zip(work, alloc[p])]   # it returns everything
                finished.add(p); order.append(p)
                break
        else:
            return None                                   # nobody can finish: unsafe
    return order

if __name__ == "__main__":
    print("available:", available(allocation))
    seq = safe_sequence(allocation)
    print("state is", "SAFE, e.g. order " + " -> ".join(seq) if seq else "UNSAFE")
    if len(sys.argv) == 5:
        p, req = sys.argv[1], [int(v) for v in sys.argv[2:]]
        need = [m - a for m, a in zip(maximum[p], allocation[p])]
        if any(r > n for r, n in zip(req, need)):
            sys.exit(f"request {p} {req}: error, more than its declared maximum (need {need})")
        trial = {q: list(a) for q, a in allocation.items()}
        trial[p] = [a + r for a, r in zip(trial[p], req)]
        if any(v < 0 for v in available(trial)):
            print(f"request {p} {req}: not enough free resources now, {p} must wait")
        else:
            seq = safe_sequence(trial)
            print(f"request {p} {req}:", f"granted (safe order {' -> '.join(seq)})" if seq
                  else "refused: granting it would make the state unsafe, " + p + " must wait")
