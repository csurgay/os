#!/bin/sh
# procfs.sh: a process seen through /proc
cd /tmp
sleep 100 < /dev/null > /tmp/sleep-out.txt 2>&1 &
P=$!
sleep 0.2
echo "\$ grep -E '^(Name|State|PPid|Uid|Threads|VmRSS|voluntary)' /proc/$P/status"
grep -E '^(Name|State|PPid|Uid|Threads|VmRSS|voluntary)' /proc/$P/status
echo "\$ ls -l /proc/$P/fd | awk 'NR > 1 {print \$9, \$10, \$11}'"
ls -l /proc/$P/fd | awk 'NR > 1 {print $9, $10, $11}'
echo "\$ readlink /proc/$P/exe /proc/$P/cwd; tr '\\\\0' ' ' < /proc/$P/cmdline; echo"
readlink /proc/$P/exe /proc/$P/cwd; tr '\0' ' ' < /proc/$P/cmdline; echo
echo "\$ cat /proc/$P/wchan; echo"
cat /proc/$P/wchan; echo
echo "\$ grep -E 'Max (open files|processes|stack)' /proc/$P/limits"
grep -E 'Max (open files|processes|stack)' /proc/$P/limits
kill $P
rm -f /tmp/sleep-out.txt
