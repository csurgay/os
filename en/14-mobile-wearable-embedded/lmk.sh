#!/bin/bash
# lmk.sh - who is killed first when memory runs out?
# Five "apps" with Android-like oom_score_adj values share a 256 MiB memory cgroup
# while a "game" in the foreground keeps growing. Part 1: the kernel's OOM killer
# decides. Part 2: the toy user-space killer mini_lmkd.py acts first.
run() { echo "\$ $*"; eval "$@" 2>&1; }
G=lab12
if grep -qw memory /sys/fs/cgroup/cgroup.controllers 2>/dev/null; then      # cgroup v2
    CG=/sys/fs/cgroup/$G; mkdir -p $CG; echo +memory > /sys/fs/cgroup/cgroup.subtree_control
    echo 256M > $CG/memory.max; echo 0 > $CG/memory.swap.max
else                                                                         # cgroup v1
    CG=/sys/fs/cgroup/memory/$G; mkdir -p $CG
    echo 256M > $CG/memory.limit_in_bytes
fi
export CG
start_apps() {
    for a in "launcher 0" "music 200" "sync 500" "browser 900" "gallery 950"; do
        python3 app.py $a 30 & disown; sleep 0.5
    done
}
scores() { for p in $(cat $CG/cgroup.procs); do
    printf "%-10s adj %4s  oom_score %4s\n" "$(tr '\0' ' ' < /proc/$p/cmdline | cut -d' ' -f3)" \
        "$(cat /proc/$p/oom_score_adj)" "$(cat /proc/$p/oom_score)"; done; }
survivors() { echo "# still running:"; for p in $(cat $CG/cgroup.procs); do
    tr '\0' ' ' < /proc/$p/cmdline | cut -d' ' -f3; done | sort | tr '\n' ' '; echo; }

run "cat /proc/pressure/memory"
echo "# Part 1: the kernel's OOM killer"
dmesg -C
start_apps
scores
python3 app.py game 0 20 20 180 & disown; sleep 5
run "dmesg | grep 'Killed process' | sed -E 's/.*(Killed process [0-9]+).*(anon-rss:[0-9]+kB).*(oom_score_adj:-?[0-9]+)/\\1 \\2 \\3/'"
survivors
kill -9 $(cat $CG/cgroup.procs) 2>/dev/null; sleep 1

echo "# Part 2: a user-space killer acts first"
dmesg -C
LMKD_SECONDS=7 python3 mini_lmkd.py $CG & L=$!
sleep 0.5
start_apps
python3 app.py game 0 20 20 180 & disown; sleep 5
wait $L
run "dmesg | grep -c 'Killed process'"
survivors
kill -9 $(cat $CG/cgroup.procs) 2>/dev/null; sleep 1
run "cat /proc/pressure/memory"
rmdir $CG
