#!/bin/sh
# layout.sh - the on-disk layout of a fresh 512 MiB ext4 (no root needed)
rm -f layout.img; truncate -s 512M layout.img
mkfs.ext4 -q -F layout.img
dumpe2fs -h layout.img 2>/dev/null | grep -E '^(Filesystem features|Inode count|Block count|Block size|Blocks per group|Inodes per group|Inode size|Total journal size|Flex block group size)'
echo "..."
dumpe2fs layout.img 2>/dev/null | grep -A7 '^Group 0:'
dumpe2fs layout.img 2>/dev/null | grep -A3 '^Group 1:'
