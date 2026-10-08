#!/bin/bash
# inspect.sh - a running container seen from the host: namespaces, cgroups,
# capabilities, seccomp and the overlay mount. Needs root and the image course/app:1.0
# (see demo.sh); run "D=podman bash inspect.sh" for Podman (cgroup paths differ).
D=${D:-docker}
run() { echo "\$ $*"; eval "$@" 2>&1; }
$D rm -f fg lim >/dev/null 2>&1
$D run -d --name fg course/app:1.0 >/dev/null
P=$($D inspect -f '{{.State.Pid}}' fg)
run "$D inspect -f '{{.State.Pid}}' fg"
run "ps -o pid,ppid,user,comm -p $P"
run "ps -o comm= -p \$(ps -o ppid= -p $P)"
run "grep -E 'NSpid|^Uid|CapEff|Seccomp:' /proc/$P/status"
run "for n in pid mnt net uts ipc user; do echo \"\$n: \$(readlink /proc/$P/ns/\$n)  host: \$(readlink /proc/self/ns/\$n)\"; done"
# The container's root file system is an overlay mount (paths shortened to ...)
run "findmnt -N $P -n -o FSTYPE,OPTIONS / | sed 's#/var/lib/docker/[^:,]*/snapshots/#...#g' | tr ',' '\n' | grep -E 'overlay|dir='"
# Resource limits are cgroup settings written by the engine
$D run -d --name lim --memory 64m --cpus 0.2 course/app:1.0 >/dev/null
ID=$($D inspect -f '{{.Id}}' lim)
if [ -d /sys/fs/cgroup/memory/docker ]; then
  run "cat /sys/fs/cgroup/memory/docker/${ID:0:12}*/memory.limit_in_bytes /sys/fs/cgroup/cpu/docker/${ID:0:12}*/cpu.cfs_quota_us"
else
  run "cat /sys/fs/cgroup/system.slice/docker-${ID:0:12}*.scope/memory.max /sys/fs/cgroup/system.slice/docker-${ID:0:12}*.scope/cpu.max"
fi
run "$D run --rm --user 0 course/app:1.0 tool cat /proc/self/status | grep CapEff"
run "capsh --decode=\$($D run --rm --user 0 course/app:1.0 tool cat /proc/self/status | awk '/CapEff/ {print \$2}')"
run "$D info -f '{{.DefaultRuntime}}'"
$D rm -f lim >/dev/null
