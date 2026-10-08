#!/bin/sh
# xfsdemo.sh - an XFS file system image, populated at creation time and inspected
# with xfs_db (no root needed: nothing is mounted)
rm -f xfs.img; truncate -s 1G xfs.img
printf 'hello, XFS\n' > hello.txt
head -c 3M /dev/urandom > big.bin
cat > proto.txt <<PROTO
/dev/null
0 0
d--755 0 0
hello.txt ---644 0 0 $PWD/hello.txt
big.bin ---644 0 0 $PWD/big.bin
docs d--755 0 0
$
$
PROTO
mkfs.xfs -q -f -p proto.txt xfs.img
echo "--- the superblock of allocation group 0:"
xfs_db -r xfs.img -c "sb 0" -c "print blocksize agcount agblocks inodesize rootino"
echo "--- the root directory: a short-form directory stored inside its inode:"
xfs_db -r xfs.img -c "inode 128" -c "print core.format core.size core.nlinkv2" -c "print u3.sfdir3" | grep -v -E "offset|filetype|namelen"
echo "--- the inode of big.bin and its extents (file offset, disk block, length):"
ino=$(xfs_db -r xfs.img -c "inode 128" -c "print u3.sfdir3.list[1].inumber.i4" | awk '{print $3}')
xfs_db -r xfs.img -c "inode $ino" -c "print core.format core.size core.nextents" -c "bmap"
