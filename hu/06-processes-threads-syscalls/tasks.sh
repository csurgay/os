#!/bin/sh
# tasks.sh: a process with four threads, seen by ps and /proc
python3 -c 'import threading, time
for _ in range(3):
    threading.Thread(target=time.sleep, args=(5,)).start()
time.sleep(5)' &
P=$!
sleep 0.5
echo "\$ ps -L -o pid,lwp,nlwp,stat,comm -p $P"
ps -L -o pid,lwp,nlwp,stat,comm -p $P
echo "\$ ls /proc/$P/task"
ls /proc/$P/task
echo "\$ grep -E '^(Tgid|Pid|Threads)' /proc/$P/status"
grep -E '^(Tgid|Pid|Threads)' /proc/$P/status
T=$(ls /proc/$P/task | tail -1)
echo "\$ grep -E '^(Tgid|Pid)' /proc/$P/task/$T/status"
grep -E '^(Tgid|Pid)' /proc/$P/task/$T/status
kill $P
