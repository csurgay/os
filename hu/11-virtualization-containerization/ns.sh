#!/bin/bash
# ns.sh - namespaces by hand: a process tree, a host name and a mount table of its own.
run() { echo "\$ $*"; eval "$@" 2>&1; }
run 'ls -l /proc/self/ns | awk "NR>1 {print \$9, \$10, \$11}"'
run 'hostname'
# New PID, UTS and mount namespaces; --fork makes the shell PID 1 of the new
# PID namespace, --mount-proc mounts a fresh /proc that shows only its processes.
run "unshare --pid --uts --mount --fork --mount-proc bash -c 'hostname box; echo \"hostname: \$(hostname)\"; echo \"my PID: \$\$\"; ps -e -o pid,ppid,comm; readlink /proc/self/ns/pid /proc/self/ns/uts /proc/self/ns/net'"
run 'hostname'
# The same kind of process seen from the outside: a PID namespace only renumbers.
unshare --pid --fork --mount-proc sleep 60 &
sleep 1
P=$(pgrep -n -x sleep)
run "ps -o pid,ppid,comm -p $P"
run "grep NSpid /proc/$P/status"
run "readlink /proc/$P/ns/pid"
kill %1 2>/dev/null; wait 2>/dev/null
