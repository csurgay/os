#!/bin/bash
# stopcont.sh - stop and continue a CPU-bound process with SIGSTOP / SIGCONT
# and watch its state letter and its CPU time (utime, field 14 of /proc/PID/stat)
show() {   # state (field 3) and utime in clock ticks (field 14); comm has no spaces here
    read -r pid comm state rest < /proc/$P/stat
    utime=$(cut -d' ' -f14 /proc/$P/stat)
    printf '%-22s state %s  utime %4s ticks   ps: %s\n' "$1" "$state" "$utime" \
        "$(ps -o stat=,wchan:16= -p $P)"
}
taskset -c 0 bash -c 'while :; do :; done' &  P=$!
sleep 1;  show "running for 1 s:"
kill -STOP $P; sleep 0.1; show "after SIGSTOP:"
sleep 2;  show "2 s later, stopped:"
kill -CONT $P; sleep 1; show "1 s after SIGCONT:"
kill -l STOP CONT
kill -9 $P
