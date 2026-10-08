#!/usr/bin/env python3
"""spin.py - stay busy for 2 seconds of wall-clock time, then report the CPU time used."""
import time
t = time.time()
while time.time() - t < 2:
    pass
print(f"wall {time.time() - t:.2f} s, CPU {time.process_time():.2f} s")
