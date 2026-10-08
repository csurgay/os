#!/bin/sh
# sparse.sh - holes, extents and delayed allocation (root, after mkimg.sh)
cd /mnt/lab
truncate -s 1G huge.bin                           # 1 GiB long, nothing written
printf 'X' | dd of=huge.bin bs=1 seek=500M conv=notrunc 2>/dev/null
sync
ls -lh huge.bin; du -h huge.bin; df -h . | tail -1
filefrag -v huge.bin | sed -n '3,5p'
echo "--- two files growing at the same time, 16 x 64 KiB each:"
i=0
while [ $i -lt 16 ]; do
  head -c 64K /dev/zero >> a.dat; head -c 64K /dev/zero >> b.dat; i=$((i+1))
done
sync
filefrag a.dat b.dat
echo "--- the same, but with a sync after every 64 KiB:"
i=0
while [ $i -lt 16 ]; do
  head -c 64K /dev/zero >> c.dat; head -c 64K /dev/zero >> d.dat; sync; i=$((i+1))
done
filefrag c.dat d.dat
filefrag -v c.dat | sed -n '3,6p'
