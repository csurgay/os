#!/bin/bash
# latency.sh - wake-up lateness of a 1 ms periodic task on CPU 0,
# idle and next to two CPU hogs, as SCHED_OTHER and as SCHED_FIFO (priority 80).
run() { echo "\$ $*"; eval "$@" 2>&1; }
gcc -O2 -o latency latency.c && gcc -O2 -o hog hog.c || exit 1
echo "# CPU 0 idle"
run "taskset -c 0 ./latency 5000"
run "chrt -f 80 taskset -c 0 ./latency 5000"
echo "# two CPU hogs on CPU 0"
taskset -c 0 ./hog 60 & H1=$!; taskset -c 0 ./hog 60 & H2=$!; sleep 1
run "taskset -c 0 ./latency 5000"
run "chrt -f 80 taskset -c 0 ./latency 5000"
kill $H1 $H2; wait 2>/dev/null
