#!/bin/sh
# requests.sh: how the block layer turns reads and writes into device requests.
# Run as root, in a directory on the disk vda. Writes a 64 MiB file, reads it
# back in several ways, and counts the requests in /sys/block/vda/stat:
# field 1 = read requests completed, 2 = read requests merged, 3 = sectors read,
# fields 5, 6, 7 = the same for writes.
DISK=vda
snap() { cat /sys/block/$DISK/stat; }
report() {   # $1 = label, $2 = stat before, $3 = stat after
    echo "$2 $3" | awk -v l="$1" '{ n = NF / 2
        r = $(n+1) - $1; rm = $(n+2) - $2; rs = $(n+3) - $3
        w = $(n+5) - $5; wm = $(n+6) - $6; ws = $(n+7) - $7
        if (r > 0)  printf "%-34s %6d read requests,  %6d merged, %6.0f KiB per request\n",  l, r, rm, rs / 2 / r
        if (w > 0)  printf "%-34s %6d write requests, %6d merged, %6.0f KiB per request\n", l, w, wm, ws / 2 / w }'
}
run() {      # $1 = label, rest = command
    l=$1; shift
    sync; echo 3 > /proc/sys/vm/drop_caches
    dd --version > /dev/null; ls -l "$F" > /dev/null 2>&1    # reload dd and the file's inode first
    a=$(snap); "$@" 2>/dev/null; b=$(snap)
    report "$l" "$a" "$b"
}
F=requests.tmp
echo "scheduler: $(cat /sys/block/$DISK/queue/scheduler), read-ahead $(cat /sys/block/$DISK/queue/read_ahead_kb) KiB, largest request $(cat /sys/block/$DISK/queue/max_sectors_kb) KiB"
run "4 KiB writes, then fsync"      dd if=/dev/zero of=$F bs=4k count=16384 conv=fsync
run "4 KiB reads, O_DIRECT"         dd if=$F of=/dev/null bs=4k iflag=direct
run "4 KiB reads through the cache" dd if=$F of=/dev/null bs=4k
run "1 MiB reads, O_DIRECT"         dd if=$F of=/dev/null bs=1M iflag=direct
rm -f $F
