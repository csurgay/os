#!/bin/sh
# bigdir.sh - a large directory becomes a hashed tree (htree) in ext4 (root, after mkimg.sh)
cd /mnt/lab
DEV=$(findmnt -n -o SOURCE /mnt/lab)
mkdir big
i=0; while [ $i -lt 2000 ]; do : > big/file$i; i=$((i+1)); done
sync
ls -ld big
debugfs -R "stat /big" $DEV 2>/dev/null | grep -E 'Flags|Size'
debugfs -R "htree /big" $DEV 2>/dev/null > /tmp/htree.txt
sed -n '1,12p' /tmp/htree.txt
echo "..."
echo "leaf blocks: $(grep -c '^Reading directory block' /tmp/htree.txt)"
