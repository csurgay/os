#!/bin/sh
# ntfsdemo.sh - an NTFS file system image, created and inspected with ntfsprogs
# (no root needed: nothing is mounted)
rm -f ntfs.img; truncate -s 256M ntfs.img
mkntfs -q -F -f -L LAB9 ntfs.img 2>/dev/null
printf 'hello, NTFS\n' > hello.txt
head -c 3M /dev/urandom > big.bin
ntfscp -q ntfs.img hello.txt hello.txt
ntfscp -q ntfs.img big.bin big.bin
echo "--- the volume:"
ntfsinfo -m ntfs.img | grep -E 'Volume Name|Cluster Size|Volume Size in Clusters|MFT Record Size'
echo "--- the root directory, including the metadata files:"
ntfsls -a -s -l ntfs.img | grep -v ' \.\.*$'
echo "--- hello.txt: its data is resident, stored inside its own MFT record:"
ntfsinfo -F /hello.txt ntfs.img | grep -E 'Dumping attribute|Resident:|Data size'
echo "--- big.bin: its data is non-resident, described by a run list:"
ntfsinfo -v -F /big.bin ntfs.img | sed -n '/attribute \$DATA/,$p' | grep -E 'Dumping|Resident:|Data size|Runlist|^\s+0x'
