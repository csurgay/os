#!/bin/bash
# zram.sh - compressed swap in RAM, as Android uses it instead of a swap partition.
# Part 1: a 200 MiB "app" in a 128 MiB memory cgroup without swap is OOM-killed.
# Part 2: the same with a zram swap device: pages are compressed into RAM instead.
run() { echo "\$ $*"; eval "$@" 2>&1; }
CG=/sys/fs/cgroup/memory/lab12z; mkdir -p $CG; echo 128M > $CG/memory.limit_in_bytes
run "cat /proc/pressure/memory"
echo "# Part 1: no swap"
run "swapon --show; sh -c 'echo \$\$ > $CG/cgroup.procs; exec python3 heap.py 200'"
echo "# Part 2: zram swap"
run "cat /sys/block/zram0/comp_algorithm"
run "echo lz4 > /sys/block/zram0/comp_algorithm; echo 512M > /sys/block/zram0/disksize"
run "mkswap /dev/zram0 >/dev/null; swapon -p 100 /dev/zram0; swapon --show"
sh -c "echo \$\$ > $CG/cgroup.procs; exec python3 heap.py 200 3" & P=$!
echo "\$ sh -c 'echo \$\$ > $CG/cgroup.procs; exec python3 heap.py 200 3' &"; sleep 2.5
run "grep -E '^(rss|swap) ' $CG/memory.stat"
run "cat /sys/block/zram0/mm_stat"
read orig compr used rest < /sys/block/zram0/mm_stat
echo "# stored $((orig >> 20)) MiB of pages in $((used >> 20)) MiB of RAM: ratio $(awk "BEGIN{printf \"%.1f\", $orig/$used}")"
wait $P
run "cat /proc/pressure/memory"
swapoff /dev/zram0; echo 1 > /sys/block/zram0/reset; rmdir $CG
