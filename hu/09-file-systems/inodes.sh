#!/bin/sh
# inodes.sh - look inside ext4 with debugfs (run after mkimg.sh and links.sh, as root)
cd /mnt/lab
DEV=$(findmnt -n -o SOURCE /mnt/lab)
head -c 300K /dev/urandom > photo.jpg
sync
echo "--- the inode of photo.jpg:"
debugfs -R "stat /photo.jpg" $DEV 2>/dev/null | sed -n '1,4p;/EXTENTS/,$p'
echo "--- the same through filefrag:"
filefrag -v photo.jpg | sed -n '1,5p'
echo "--- the directory / as stored on disk (inode, name, entry length):"
debugfs -R "ls /" $DEV 2>/dev/null
echo "--- the symbolic link: the path is stored inside the inode itself:"
debugfs -R "stat /soft.txt" $DEV 2>/dev/null | grep -E 'Type|Fast link'
