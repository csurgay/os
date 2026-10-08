#!/bin/sh
# inode-exhaust.sh - a file system can be "full" with free space left (root)
# a 16 MiB ext4 that has only 256 inodes
./mkimg.sh 16M -N 256 >/dev/null
cd /mnt/lab
df -h . | tail -1
df -i . | tail -1
i=0
while touch tiny$i 2>/tmp/err; do i=$((i+1)); done
echo "created $i empty files, then: $(cat /tmp/err)"
df -h . | tail -1
df -i . | tail -1
