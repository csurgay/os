#!/bin/sh
# filetypes.sh - one file of each of the seven Unix file types, and the type of content (needs root for mknod)
rm -rf /tmp/types && mkdir /tmp/types && cd /tmp/types
echo "hello, file system" > notes.txt                 # -  regular file
mkdir dir                                             # d  directory
ln -s notes.txt link                                  # l  symbolic link
mkfifo pipe                                           # p  named pipe (FIFO)
python3 -c 'import socket; socket.socket(socket.AF_UNIX).bind("sock")'   # s  Unix domain socket
mknod mynull c 1 3                                    # c  character device, numbers 1,3 (= /dev/null)
mknod myloop b 7 0                                    # b  block device, numbers 7,0 (= /dev/loop0)
ls -l
echo "--- the type as stat names it:"
stat -c '%-10n %F' *
echo "--- a FIFO passes bytes in one direction, from a writer to a reader:"
echo "through the pipe" > pipe &
cat pipe
echo "--- a device file is only a name and two numbers; the driver does the rest:"
echo "this disappears" > mynull; cat mynull; ls -l mynull
head -c 8 /dev/zero | od -An -tx1
echo "--- extensions are just part of the name; file(1) looks at the content:"
cp notes.txt photo.jpg
gzip -c notes.txt > report.txt
cp /usr/bin/ls notes.pdf
file photo.jpg report.txt notes.pdf pipe mynull link | cut -c1-80
