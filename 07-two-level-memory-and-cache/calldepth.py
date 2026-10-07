#!/usr/bin/env python3
"""calldepth.py - how deep do function calls nest while a real program runs?

Runs a real workload (Python's own json, difflib and ast modules on real
input), records the call depth at every function call and return, and then
asks: if the CPU kept the W most recent call levels in fast storage (like
the register windows of RISC processors or a stack cache), how often would a
call or a return fall outside that window and force a slow "spill"?
Usage: python3 calldepth.py [--trace depth.csv]
"""
import ast, difflib, inspect, json, sys

depth, trace = 0, []
def prof(frame, event, arg):
    global depth
    if event in ("call", "c_call"):
        depth += 1; trace.append(depth)
    elif event in ("return", "c_return", "c_exception"):
        depth -= 1; trace.append(depth)

def workload():
    src = inspect.getsource(difflib)                           # ~2000 lines of real code
    tree = ast.parse(src)                                       # parse it
    data = json.loads(json.dumps(ast.dump(tree)[:200000]))     # serialise, parse back
    a, b = src.splitlines(), src.replace("self", "this").splitlines()
    return len(list(difflib.unified_diff(a, b))) + len(data)   # compare two versions

def spills(trace, w):
    """Window of w levels: [top-w+1, top]. A call above or a return below it spills."""
    lo, hi, n = trace[0] - w + 1, trace[0], 0
    for d in trace:
        if d > hi: hi, lo, n = d, d - w + 1, n + 1      # overflow: save the oldest level
        elif d < lo: lo, hi, n = d, d + w - 1, n + 1    # underflow: reload a level
    return n

if __name__ == "__main__":
    sys.setprofile(prof); workload(); sys.setprofile(None)
    base = min(trace); t = [d - base for d in trace]
    print(f"{len(t):,} calls and returns recorded; depth from {min(t)} to {max(t)} "
          f"(relative to the start)")
    print(f"{'window W':>9} {'spills':>10} {'% of calls/returns':>20}")
    for w in (1, 2, 3, 4, 5, 6, 7, 8, 12, 16):
        n = spills(t, w)
        print(f"{w:9d} {n:10,d} {100 * n / len(t):19.2f}%")
    if "--trace" in sys.argv:
        with open(sys.argv[sys.argv.index("--trace") + 1], "w") as f:
            f.write("\n".join(map(str, t)))
