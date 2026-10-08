#!/usr/bin/env python3
"""rtsim.py - rate-monotonic (RM) and earliest-deadline-first (EDF) scheduling, simulated and tested.

Periodic tasks (C = worst-case execution time, T = period, deadline = end of the period)
run on one CPU in whole time units. The simulator runs every task set over its
hyperperiod (the least common multiple of the periods) under preemptive RM (fixed
priorities: shorter period = higher priority) and preemptive EDF (dynamic priorities:
earlier absolute deadline = higher priority; ties go to the lower task number).
A job that has not finished at its deadline counts as a miss and is dropped.

The schedulability tests printed next to the simulation:
  * utilisation U = sum of C/T;
  * the Liu & Layland bound for RM, U <= n(2^(1/n) - 1): sufficient, not necessary;
  * response-time analysis for RM, R = C_i + sum over higher-priority j of ceil(R/T_j) C_j:
    exact for this task model;
  * EDF: U <= 1, exact for this task model.
"""
from math import ceil, gcd
from functools import reduce

TASK_SETS = {
    "A": [(1, 4), (2, 6), (1, 12)],   # (C, T): U = 0.667, below the bound
    "B": [(2, 5), (4, 7)],            # U = 0.971: EDF only
    "C": [(2, 4), (4, 8)],            # U = 1.0, harmonic periods: RM still meets every deadline
}


def lcm(a, b):
    return a * b // gcd(a, b)


def simulate(tasks, policy):
    """Return (timeline, misses): timeline[t] = index of the task running in [t, t+1) or None."""
    H = reduce(lcm, (T for _, T in tasks))
    jobs = []                       # [task index, remaining, absolute deadline]
    timeline, misses = [], []
    for t in range(H):
        for i, (C, T) in enumerate(tasks):
            if t % T == 0:
                jobs.append([i, C, t + T])
        if policy == "RM":
            key = lambda j: (tasks[j[0]][1], j[0])
        else:
            key = lambda j: (j[2], j[0])
        jobs.sort(key=key)
        if jobs:
            jobs[0][1] -= 1
            timeline.append(jobs[0][0])
            if jobs[0][1] == 0:
                jobs.pop(0)
        else:
            timeline.append(None)
        for j in jobs[:]:            # deadlines at the end of this time unit
            if j[2] == t + 1:
                misses.append((j[0], t + 1))
                jobs.remove(j)
    return timeline, misses


def rta(tasks):
    """Worst-case response times under RM (None if a task cannot meet its deadline)."""
    order = sorted(range(len(tasks)), key=lambda i: tasks[i][1])
    result = {}
    for k, i in enumerate(order):
        C, T = tasks[i]
        R = C
        while True:
            Rn = C + sum(ceil(R / tasks[j][1]) * tasks[j][0] for j in order[:k])
            if Rn > T:
                result[i] = None
                break
            if Rn == R:
                result[i] = R
                break
            R = Rn
    return [result[i] for i in range(len(tasks))]


def gantt(timeline):
    return "".join("." if x is None else str(x + 1) for x in timeline)


def main():
    for name, tasks in TASK_SETS.items():
        n = len(tasks)
        U = sum(C / T for C, T in tasks)
        bound = n * (2 ** (1 / n) - 1)
        R = rta(tasks)
        desc = ", ".join(f"T{i + 1}(C={C}, T={T})" for i, (C, T) in enumerate(tasks))
        print(f"Task set {name}: {desc}")
        print(f"  U = {U:.3f}   Liu-Layland bound for n={n}: {bound:.3f} -> "
              f"{'RM guaranteed' if U <= bound else 'bound says nothing'}")
        print("  RM response times: " + ", ".join(
            f"R{i + 1}={'miss' if r is None else r}" for i, r in enumerate(R)) +
              f" -> RM {'schedulable' if all(r is not None for r in R) else 'NOT schedulable'}")
        print(f"  EDF test U <= 1 -> EDF {'schedulable' if U <= 1 else 'NOT schedulable'}")
        for policy in ("RM", "EDF"):
            tl, misses = simulate(tasks, policy)
            m = ", ".join(f"T{i + 1} at t={t}" for i, t in misses) or "none"
            print(f"  {policy:<3} |{gantt(tl)}|  deadline misses: {m}")
        print()


if __name__ == "__main__":
    main()
