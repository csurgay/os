#!/bin/bash
# states.sh - put processes into different states and look at them with ps
sleep 100 &                         S=$!   # waiting for a timer: S (sleeping)
bash -c 'while :; do :; done' &     R=$!   # always wants the CPU: R (running)
bash -c 'while :; do :; done' &     T=$!
sleep 0.5; kill -STOP $T                   # stopped by a signal: T
./zombie &                          Z=$!   # its child exits at once: Z (zombie)
sleep 1
ps -o pid,ppid,stat,wchan:14,cmd -p $S,$R,$T,$Z,$(pgrep -P $Z)
CHILD=$(pgrep -P $Z)
sleep 11                                   # meanwhile the parent calls waitpid()
echo "--- child $CHILD after waitpid():"
ps -o pid,ppid,stat,cmd -p $CHILD || echo "(no such process any more)"
kill -9 $S $R $T $Z 2>/dev/null
