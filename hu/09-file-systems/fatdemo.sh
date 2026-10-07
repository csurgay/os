#!/bin/sh
# fatdemo.sh - a FAT16 file system built and taken apart by hand (no root needed)
rm -f fat.img; truncate -s 32M fat.img
mkfs.fat -F 16 -s 4 -n LAB9 fat.img >/dev/null
python3 fat16.py info fat.img
printf 'Hello, FAT!\n' > hello.txt
head -c 5000 /dev/urandom > a.dat; head -c 3000 /dev/urandom > b.dat; head -c 9000 /dev/urandom > c.dat
echo "--- adding three files:"
python3 fat16.py add fat.img hello.txt HELLO.TXT
python3 fat16.py add fat.img a.dat A.DAT
python3 fat16.py add fat.img b.dat B.DAT
python3 fat16.py ls fat.img
python3 fat16.py fat fat.img 12
echo "--- deleting A.DAT, then adding a larger C.DAT:"
python3 fat16.py rm fat.img A.DAT
python3 fat16.py ls fat.img
python3 fat16.py add fat.img c.dat C.DAT
python3 fat16.py ls fat.img
python3 fat16.py fat fat.img 12
python3 fat16.py cat fat.img C.DAT | cmp - c.dat && echo "C.DAT reads back correctly"
echo "--- the root directory, raw (32 bytes per entry):"
python3 fat16.py raw fat.img 5
echo "--- an independent check with fsck.fat:"
fsck.fat -n -l fat.img
