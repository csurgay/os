#!/usr/bin/env python3
"""ptree.py: a small pstree, built only from /proc.

Every /proc/PID/stat holds the process's name, state, parent PID and number
of threads; linking each PID to its parent gives the process tree.
Usage: python3 ptree.py [PID]   (default: the whole tree; kernel threads,
the children of kthreadd, PID 2, are only counted)."""
import os
import sys


def read_stat(pid):
    with open(f"/proc/{pid}/stat") as f:
        s = f.read()
    # the name is in parentheses and may itself contain spaces or ')'
    name = s[s.index("(") + 1:s.rindex(")")]
    rest = s[s.rindex(")") + 2:].split()
    state, ppid, threads = rest[0], int(rest[1]), int(rest[17])
    return name, state, ppid, threads


procs, children = {}, {}
for d in os.listdir("/proc"):
    if d.isdigit():
        try:
            procs[int(d)] = read_stat(d)
        except (FileNotFoundError, ProcessLookupError):
            pass                        # the process ended while we looked
for pid, (_, _, ppid, _) in procs.items():
    children.setdefault(ppid, []).append(pid)


def show(pid, prefix="", last=True, top=True):
    name, state, _, threads = procs[pid]
    th = f" [{threads} threads]" if threads > 1 else ""
    branch = "" if top else ("└─ " if last else "├─ ")
    print(f"{prefix}{branch}{name}({pid}) {state}{th}")
    if pid == 2:
        print(f"{prefix}   └─ ... {len(children.get(2, []))} kernel threads")
        return
    kids = sorted(children.get(pid, []))
    for i, k in enumerate(kids):
        show(k, prefix + ("" if top else ("   " if last else "│  ")), i == len(kids) - 1, False)


if len(sys.argv) > 1:
    show(int(sys.argv[1]))
else:
    for root in sorted(children.get(0, [])):     # PID 1 and PID 2 have parent 0
        show(root)
