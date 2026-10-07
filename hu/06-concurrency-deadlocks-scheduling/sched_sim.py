#!/usr/bin/env python3
"""sched_sim.py - simulate classic CPU scheduling algorithms on one CPU.

Usage:
  python3 sched_sim.py                   the example job set, all algorithms
  python3 sched_sim.py A:0:8 B:1:4 ...   your own jobs as name:arrival:burst
  python3 sched_sim.py --switch 0.5 ...  add a context-switch cost (time units)

Prints a text Gantt chart and the average waiting, turnaround and response
times for FIFO, SJF, SRTF and Round Robin (quantum 1, 2 and 4).

Conventions: a job that arrives at the moment another is preempted enters the
ready queue before the preempted job; ties in SJF/SRTF go to the job that has
been in the queue longer (stable sort); a newly arrived job in SRTF preempts
only if its remaining time is shorter or equal.
"""
import sys

def simulate(jobs, policy, quantum=None, switch=0.0):
    """jobs: list of (name, arrival, burst). Returns (timeline, stats)."""
    t, done = 0.0, {}
    left = {n: b for n, a, b in jobs}
    first_run = {}
    timeline, queue, last = [], [], None
    pending = sorted(jobs, key=lambda j: j[1])
    def admit(now):
        while pending and pending[0][1] <= now:
            queue.append(pending.pop(0)[0])
    admit(t)
    while queue or pending:
        if not queue:                                   # CPU idle until next arrival
            timeline.append(("-", t, pending[0][1])); t = pending[0][1]; admit(t); continue
        if policy in ("SJF", "SRTF"):                   # pick the shortest (remaining) job: O(n)
            queue.sort(key=lambda n: left[n])
        name = queue.pop(0)
        if last is not None and name != last and switch:
            timeline.append(("s", t, t + switch)); t += switch; admit(t)
        first_run.setdefault(name, t)
        if policy in ("FIFO", "SJF"):
            run = left[name]                            # non-preemptive: to the end
        elif policy == "RR":
            run = min(quantum, left[name])
        else:                                           # SRTF: until done or next arrival
            run = left[name]
            if pending:
                run = min(run, max(pending[0][1] - t, 0) or run)
        timeline.append((name, t, t + run)); t += run; left[name] -= run
        admit(t)
        if left[name] > 1e-9:
            queue.append(name)                          # back to the end of the ready queue
        else:
            done[name] = t
        last = name
    arr = {n: a for n, a, b in jobs}; bur = {n: b for n, a, b in jobs}
    turn = {n: done[n] - arr[n] for n in done}
    wait = {n: turn[n] - bur[n] for n in done}
    resp = {n: first_run[n] - arr[n] for n in done}
    avg = lambda d: sum(d.values()) / len(d)
    return timeline, (avg(wait), avg(turn), avg(resp), t)

def gantt(timeline):
    out = ""
    for name, a, b in timeline:
        width = max(1, round((b - a) * 2))
        out += (name if name != "s" else "|") * width
    return out

if __name__ == "__main__":
    args = sys.argv[1:]
    switch = 0.0
    if args[:1] == ["--switch"]:
        switch = float(args[1]); args = args[2:]
    jobs = [(a.split(":")[0], float(a.split(":")[1]), float(a.split(":")[2])) for a in args] or \
           [("A", 0, 6), ("B", 1, 3), ("C", 2, 8), ("D", 3, 5), ("E", 4, 2)]
    print("jobs:", ", ".join(f"{n}(arrives {a:g}, needs {b:g})" for n, a, b in jobs))
    print(f"{'algorithm':10} {'wait':>6} {'turnaround':>10} {'response':>8} {'end':>6}   timeline (2 chars = 1 unit)")
    for label, pol, q in [("FIFO", "FIFO", None), ("SJF", "SJF", None), ("SRTF", "SRTF", None),
                          ("RR q=1", "RR", 1), ("RR q=2", "RR", 2), ("RR q=4", "RR", 4)]:
        tl, (w, ta, r, end) = simulate(jobs, pol, q, switch)
        print(f"{label:10} {w:6.2f} {ta:10.2f} {r:8.2f} {end:6.1f}   {gantt(tl)}")
