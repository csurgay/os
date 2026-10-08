#!/usr/bin/env python3
"""mini_lmkd.py CGROUP - a toy user-space low-memory killer in the spirit of Android's lmkd.

Watches the memory use of a cgroup (v1 or v2) and, before the kernel's OOM killer
has to act, kills the process with the highest oom_score_adj that the current
pressure level allows: above 70% of the limit only cached apps (adj >= 900),
above 85% also services and perceptible apps (adj >= 200). Never kills adj < 200."""
import os, signal, sys, time
cg = sys.argv[1]
v2 = os.path.exists(cg + "/memory.max")
def rd(f):
    with open(os.path.join(cg, f)) as h:
        return h.read().strip()
limit = int(rd("memory.max" if v2 else "memory.limit_in_bytes"))
def usage():
    return int(rd("memory.current" if v2 else "memory.usage_in_bytes"))
def victims(min_adj):
    out = []
    for pid in rd("cgroup.procs").split():
        try:
            with open(f"/proc/{pid}/oom_score_adj") as h: adj = int(h.read())
            with open(f"/proc/{pid}/statm") as h: rss = int(h.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
            with open(f"/proc/{pid}/cmdline") as h: name = h.read().split("\0")[2]
        except (OSError, IndexError):
            continue
        if adj >= min_adj:
            out.append((adj, rss, int(pid), name))
    return sorted(out, reverse=True)
print(f"mini_lmkd: watching {cg}, limit {limit >> 20} MiB", flush=True)
t0 = time.time()
while time.time() - t0 < float(os.environ.get("LMKD_SECONDS", "20")):
    u = usage() / limit
    level = 900 if u > 0.70 else None
    level = 200 if u > 0.85 else level
    if level is not None:
        v = victims(level)
        if v:
            adj, rss, pid, name = v[0]
            os.kill(pid, signal.SIGKILL)
            print(f"mini_lmkd: usage {u:.0%} of limit -> kill {name} (pid {pid}, adj {adj}, rss {rss >> 20} MiB)", flush=True)
            time.sleep(0.2)          # give the kernel time to free its memory
    time.sleep(0.02)
