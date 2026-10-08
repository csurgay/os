#!/usr/bin/env python3
"""app.py NAME ADJ MB [STEP_MB MAX_MB] - a pretend app for the low-memory-killer demo.

Joins the cgroup given in the CG environment variable, sets its own
oom_score_adj (as Android's ActivityManager does for each app process),
then holds MB MiB of touched memory. With STEP_MB it keeps growing by
STEP_MB every 0.3 s up to MAX_MB, like a game loading levels."""
import os, sys, time
name, adj, mb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
step = int(sys.argv[4]) if len(sys.argv) > 4 else 0
max_mb = int(sys.argv[5]) if len(sys.argv) > 5 else mb
if os.environ.get("CG"):
    with open(os.environ["CG"] + "/cgroup.procs", "w") as f:
        f.write(str(os.getpid()))
with open("/proc/self/oom_score_adj", "w") as f:
    f.write(str(adj))
held = [bytearray(mb * 2**20)]
print(f"{name:<12} pid {os.getpid():>5}  oom_score_adj {adj:>4}  holds {mb} MiB", flush=True)
while step and mb + step <= max_mb:
    time.sleep(0.3)
    held.append(bytearray(step * 2**20))
    mb += step
    print(f"{name:<12} grows to {mb} MiB", flush=True)
time.sleep(600)
