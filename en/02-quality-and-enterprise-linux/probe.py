#!/usr/bin/env python3
"""probe.py - measure an availability SLI the way a monitoring system does.

Asks a web server for a page every 0.5 s and counts the answers.
  python3 probe.py http://127.0.0.1:8000/ 60     probe for 60 seconds
"""
import sys
import time
import urllib.request

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/"
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 60
ok = total = 0
end = time.time() + duration
while time.time() < end:
    total += 1
    try:
        with urllib.request.urlopen(url, timeout=1) as r:
            ok += (r.status == 200)
    except Exception:
        pass                                   # no answer = a failed probe
    time.sleep(0.5)
print(f"{ok} of {total} probes succeeded: availability SLI = {100 * ok / total:.2f}%")
