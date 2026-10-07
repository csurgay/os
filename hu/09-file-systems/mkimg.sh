#!/bin/sh
# mkimg.sh - create a small ext4 file system in an image file and mount it (needs root)
# usage: sudo ./mkimg.sh [SIZE] [extra mkfs.ext4 options]
set -e
SIZE=${1:-64M}; [ $# -gt 0 ] && shift
umount /mnt/lab 2>/dev/null || true   # a previous experiment may still be mounted
rm -f lab.img
truncate -s "$SIZE" lab.img
mkfs.ext4 -q -F "$@" lab.img
mkdir -p /mnt/lab
mount -o loop lab.img /mnt/lab
df -hT /mnt/lab
