#!/bin/sh
# buddy.sh: the free blocks of the buddy allocator, before, while and after
# a program holds 2 GiB of memory. For each zone: the number of free blocks
# of order 0 (4 KiB) to 10 (4 MiB), and the free memory they add up to.
# Run as root (for /proc/pagetypeinfo), with hold.c compiled: gcc -O2 -o hold hold.c
show() {
    awk '{ free = 0
           for (o = 0; o <= 10; o++) free += $(5 + o) * 4 * 2 ^ o
           printf "%-9s", $4
           for (o = 0; o <= 10; o++) printf " %5d", $(5 + o)
           printf "  = %5d MiB free\n", free / 1024 }' /proc/buddyinfo
}
echo "order:      0     1     2     3     4     5     6     7     8     9    10"
echo "--- before"; show
./hold 2048 & pid=$!
sleep 3
echo "--- while 2 GiB are held"; show
echo "--- the same Normal zone, split by the kind of page each free block is kept for:"
awk '/zone +Normal, type +(Unmovable|Movable) / {
         printf "%-9s", $6; for (o = 7; o <= 17; o++) printf " %5d", $o; print "" }' /proc/pagetypeinfo
kill $pid; wait $pid 2>/dev/null
sleep 1
echo "--- after the program has ended"; show
