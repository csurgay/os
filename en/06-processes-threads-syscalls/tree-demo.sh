#!/bin/sh
# tree-demo.sh: start a small family of processes, then draw it with ptree.py.
sleep 30 &                                        # a child that waits
python3 -c 'import threading, time
for _ in range(3):
    threading.Thread(target=time.sleep, args=(30,)).start()' &   # 1 process, 4 threads
(sleep 30; true) &                                # a subshell with its own child
sleep 0.5
python3 "$(dirname "$0")/ptree.py" $$
kill $(jobs -p) 2>/dev/null
pkill -P $$ 2>/dev/null; wait 2>/dev/null
