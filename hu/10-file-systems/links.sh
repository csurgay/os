#!/bin/sh
# links.sh - hard links and symbolic links on the ext4 file system mounted at /mnt/lab
cd /mnt/lab
echo "hello, file system" > notes.txt
ln notes.txt hard.txt            # a second name for the same inode
ln -s notes.txt soft.txt         # a new inode that stores the path "notes.txt"
ls -li notes.txt hard.txt soft.txt
echo "--- after rm notes.txt:"
rm notes.txt
ls -li hard.txt soft.txt
cat hard.txt
cat soft.txt
echo "--- a hard link to another file system:"
ln hard.txt /tmp/hard-elsewhere.txt
echo "--- a symbolic link to another file system:"
ln -s /etc/hostname host-link && ls -l host-link
echo "--- a hard link to a directory:"
mkdir dir
ln dir dir2
echo "--- link counts of directories:"
mkdir -p dir/a dir/b dir/c
stat -c '%n: inode %i, %h links' dir dir/a .
