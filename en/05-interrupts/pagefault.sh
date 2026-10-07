#!/bin/sh
# pagefault.sh: run pagefault twice on a 16 MiB file, first with an empty page
# cache (every page must come from the disk), then again (all pages in memory),
# and count the disk's interrupts during each run. Needs root (drop_caches).
# usage: sudo ./pagefault.sh [readahead]
# Set DISK to the disk's name in /proc/interrupts (default: virtio1-req.0).
DISK=${DISK:-virtio1-req.0}
irqs() { grep "$DISK" /proc/interrupts | awk '{ s = 0; for (i = 2; i <= NF; i++) if ($i ~ /^[0-9]+$/) s += $i; print s }'; }

[ -f data.bin ] || head -c 16M /dev/urandom > data.bin
sync
for run in cold warm; do
    [ $run = cold ] && echo 3 > /proc/sys/vm/drop_caches     # empty the page cache
    before=$(irqs)
    ./pagefault data.bin $1
    after=$(irqs)
    echo "$run run: disk interrupts ($DISK): $((after - before))"
    echo
done
