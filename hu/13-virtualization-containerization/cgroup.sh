#!/bin/bash
# cgroup.sh - limit the memory and CPU time of a group of processes, by hand.
# Uses cgroup v2 if its memory controller is available, otherwise the v1 controllers.
run() { echo "\$ $*"; eval "$@" 2>&1; }
G=lab11
if grep -qw memory /sys/fs/cgroup/cgroup.controllers 2>/dev/null; then      # cgroup v2
    M=/sys/fs/cgroup/$G; C=$M
    run "mkdir -p $M; echo +memory +cpu > /sys/fs/cgroup/cgroup.subtree_control"
    run "echo 64M > $M/memory.max; echo 0 > $M/memory.swap.max"
    run "echo '20000 100000' > $C/cpu.max"
else                                                                         # cgroup v1
    M=/sys/fs/cgroup/memory/$G; C=/sys/fs/cgroup/cpu/$G
    run "mkdir -p $M $C"
    run "echo 64M > $M/memory.limit_in_bytes; cat $M/memory.limit_in_bytes"
    run "echo 100000 > $C/cpu.cfs_period_us; echo 20000 > $C/cpu.cfs_quota_us"
fi
run "python3 spin.py"
run "sh -c 'echo \$\$ > $C/cgroup.procs; exec python3 spin.py'"
run "sh -c 'echo \$\$ > $M/cgroup.procs; exec python3 eat.py'"
if [ "$M" = "$C" ]; then run "grep oom_kill $M/memory.events"
else run "cat $M/memory.max_usage_in_bytes; grep oom_kill $M/memory.oom_control"; fi
rmdir $M $C 2>/dev/null
