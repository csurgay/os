#!/usr/bin/env python3
"""reaction.py - measure your own choice reaction time (the Hick-Hyman law).

A number from 1..N appears; type it and press Enter as fast as you can.
Each block uses a different N. At the end you get your median time per N.
Usage: python3 reaction.py [trials-per-block]   (default 10)
"""
import math, random, statistics, sys, time
try:
    import termios                                # to discard keys typed too early
except ImportError:                               # (not available on Windows)
    termios = None

def block(n, trials):
    times, errors = [], 0
    input(f"\n--- {n} possible answers (1..{n}). Press Enter to start. ")
    for _ in range(trials):
        time.sleep(random.uniform(0.8, 2.0))          # unpredictable start
        if termios and sys.stdin.isatty():
            termios.tcflush(sys.stdin, termios.TCIFLUSH)   # anticipations do not count
        target = str(random.randint(1, n))
        t0 = time.perf_counter()
        answer = input(f"  >>> {target}   ").strip()
        dt = time.perf_counter() - t0
        if answer == target:
            times.append(dt)
        else:
            errors += 1
    return times, errors

if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    results = {}
    for n in random.sample([1, 2, 4, 8], 4):          # random order: practice affects all N alike
        results[n] = block(n, trials)
    print("\n N   bits  median time  errors")
    for n in sorted(results):
        times, errors = results[n]
        med = statistics.median(times) if times else float("nan")
        print(f"{n:2d}  {math.log2(n + 1):5.2f}  {med * 1000:8.0f} ms   {errors:3d}")
    print("Fit a line: time = a + b * bits. What are your a and b?")
