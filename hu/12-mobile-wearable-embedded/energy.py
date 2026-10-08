#!/usr/bin/env python3
"""energy.py - a MODEL (not a measurement) of the energy of one task under DVFS.

One CPU core with five operating points (frequency, voltage) runs a task of
W = 1e9 clock cycles that must finish within D = 2 s, and then idles until D.
Power while running at an operating point:
    P_run = C_eff * V^2 * f  (dynamic, switching)
          + I_leak * V       (static, leakage of the powered core)
          + P_rest           (the rest of the system that stays awake while the core works:
                              memory, interconnect, voltage regulators)
Power while idle: P_idle (the core in a deep, power-gated idle state, the rest asleep too).
For a memory-bound task, a fraction of the run time is spent waiting for memory and does
not shrink with the frequency (and the core burns only static and rest power while it waits).
All parameters are invented but of a realistic order of magnitude for one phone core.
"""

OPPS = [(0.6e9, 0.60), (1.0e9, 0.70), (1.4e9, 0.80), (1.8e9, 0.95), (2.2e9, 1.10)]  # (f in Hz, V in volts)
C_EFF = 0.6e-9      # F, effective switched capacitance per cycle
I_LEAK = 0.15       # A, leakage current of the powered core
P_IDLE = 0.005      # W, deep idle
W = 1e9             # cycles of work
D = 2.0             # s, deadline (the period of the task)

SCENARIOS = [
    # name, P_rest in W, memory-stall time in s (does not scale with f)
    ("CPU-bound, nothing else awake (P_rest = 0)", 0.0, 0.0),
    ("CPU-bound, memory and interconnect awake (P_rest = 0.3 W)", 0.3, 0.0),
    ("CPU-bound, screen and radio awake (P_rest = 1.0 W)", 1.0, 0.0),
    ("memory-bound: 0.4 s of stalls (P_rest = 0.3 W)", 0.3, 0.4),
]


def energy(f, V, p_rest, stall):
    t_cpu = W / f                                  # time spent executing cycles
    t_run = t_cpu + stall
    if t_run > D:
        return None
    e_dyn = C_EFF * V * V * W                      # = C V^2 f * t_cpu, independent of f for fixed V
    e_static = (I_LEAK * V + p_rest) * t_run
    e_idle = P_IDLE * (D - t_run)
    return t_run, e_dyn, e_static, e_idle


def table():
    rows = {}
    for name, p_rest, stall in SCENARIOS:
        rows[name] = [(f, V, energy(f, V, p_rest, stall)) for f, V in OPPS]
    return rows


def main():
    print("MODEL: W = 1e9 cycles, deadline 2 s, C_eff = 0.6 nF, I_leak = 0.15 A, P_idle = 5 mW")
    for name, rows in table().items():
        print(f"\n{name}")
        print("  f [GHz]  V [V]  P_run [W]  busy [s]  E_dyn [J]  E_static+rest [J]  E_idle [J]  E_total [J]")
        best = min((r for r in rows if r[2]), key=lambda r: sum(r[2][1:]))
        for f, V, e in rows:
            if e is None:
                print(f"  {f / 1e9:6.1f}  {V:5.2f}   misses the deadline")
                continue
            t, ed, es, ei = e
            p_run = (ed + es) / t
            mark = "  <- least energy" if (f, V) == best[:2] else ""
            print(f"  {f / 1e9:6.1f}  {V:5.2f}  {p_run:8.3f}  {t:8.3f}  {ed:9.3f}  {es:17.3f}  {ei:9.3f}  {ed + es + ei:10.3f}{mark}")


if __name__ == "__main__":
    main()
