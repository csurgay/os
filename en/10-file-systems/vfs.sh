#!/bin/sh
# vfs.sh - one interface, many file systems
df -T / /dev/shm /proc /sys
echo "--- the same system calls read a file on ext4 and a file made up by the kernel:"
echo "hello" > /tmp/hello.txt
for f in /tmp/hello.txt /proc/version; do
  strace -o /tmp/trace.txt -e trace=openat,read,close cat "$f" >/dev/null
  grep -A3 "\"$f\"" /tmp/trace.txt | cut -c1-80
done
