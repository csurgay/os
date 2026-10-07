#!/usr/bin/env python3
"""availability.py - the arithmetic of availability.

  python3 availability.py nines            downtime allowed by 99%, 99.9%, ... availability
  python3 availability.py mttf 2000 4      availability from MTTF and MTTR (in hours)
  python3 availability.py combine 0.99 0.99   two components in series and in parallel
"""
import sys

YEAR_MIN = 365.25 * 24 * 60          # minutes in an average year
MONTH_MIN = YEAR_MIN / 12


def fmt(minutes):
    if minutes >= 24 * 60:
        return f"{minutes / (24 * 60):.1f} days"
    if minutes >= 60:
        return f"{minutes / 60:.1f} hours"
    if minutes >= 1:
        return f"{minutes:.1f} minutes"
    return f"{minutes * 60:.1f} seconds"


def nines():
    print(f"{'availability':>13}  {'downtime per year':>18}  {'per month':>14}")
    for a in (0.99, 0.999, 0.9999, 0.99999):
        down = 1 - a
        print(f"{a * 100:12.3f}%  {fmt(down * YEAR_MIN):>18}  {fmt(down * MONTH_MIN):>14}")


def mttf(mttf_h, mttr_h):
    a = mttf_h / (mttf_h + mttr_h)
    print(f"MTTF {mttf_h} h, MTTR {mttr_h} h  ->  availability {a * 100:.3f}%, "
          f"downtime {fmt((1 - a) * YEAR_MIN)} per year")


def combine(a1, a2):
    series = a1 * a2                      # both must work
    parallel = 1 - (1 - a1) * (1 - a2)    # at least one must work
    print(f"A1 = {a1 * 100:.2f}%, A2 = {a2 * 100:.2f}%")
    print(f"in series   (both needed):   {series * 100:.4f}%  downtime {fmt((1 - series) * YEAR_MIN)} per year")
    print(f"in parallel (either enough): {parallel * 100:.4f}%  downtime {fmt((1 - parallel) * YEAR_MIN)} per year")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "nines"
    if cmd == "nines":
        nines()
    elif cmd == "mttf":
        mttf(float(sys.argv[2]), float(sys.argv[3]))
    elif cmd == "combine":
        combine(float(sys.argv[2]), float(sys.argv[3]))
