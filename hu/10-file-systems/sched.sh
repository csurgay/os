#!/bin/sh
# sched.sh: the same reads under each I/O scheduler of the disk vda. Run as root,
# in a directory on vda. One reader, then four readers at once, each reading a
# 64 MiB file in 4 KiB O_DIRECT requests (no page cache). Restores the scheduler.
DISK=vda
old=$(sed 's/.*\[\(.*\)\].*/\1/' /sys/block/$DISK/queue/scheduler)
for i in 1 2 3 4; do dd if=/dev/urandom of=sched$i.tmp bs=1M count=64 conv=fsync status=none; done
rd() { dd if=sched$1.tmp of=/dev/null bs=4k iflag=direct 2>&1 | awk -F', ' '/copied/ { print $3 }'; }
printf "%-12s %12s %22s\n" scheduler "one reader" "four readers (total)"
for s in none mq-deadline kyber bfq; do
    echo $s > /sys/block/$DISK/queue/scheduler
    t1=$(rd 1 | awk '{ printf "%.2f s", $1 }')
    start=$(date +%s.%N)
    rd 1 > /dev/null & rd 2 > /dev/null & rd 3 > /dev/null & rd 4 > /dev/null & wait
    t4=$(echo "$start $(date +%s.%N)" | awk '{ printf "%.2f s", $2 - $1 }')
    printf "%-12s %12s %22s\n" $s "$t1" "$t4"
done
echo "--- the main settings of each scheduler (in /sys/block/$DISK/queue/iosched):"
for s in mq-deadline kyber bfq; do
    echo $s > /sys/block/$DISK/queue/scheduler
    case $s in
        mq-deadline) f="read_expire write_expire fifo_batch" ;;
        kyber)       f="read_lat_nsec write_lat_nsec" ;;
        bfq)         f="low_latency slice_idle" ;;
    esac
    printf "%-12s" $s
    for x in $f; do printf " %s=%s" $x $(cat /sys/block/$DISK/queue/iosched/$x); done; echo
done
echo $old > /sys/block/$DISK/queue/scheduler
rm -f sched?.tmp
