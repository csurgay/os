#!/bin/sh
# setuid.sh - setuid and setgid programs: the effective ID decides, not the real one
# needs the compiled showid (gcc -O2 -o showid showid.c) in the current directory
L=/srv/lab10/suid
rm -rf $L; mkdir -p $L; cp showid $L/; cd $L
echo "john's diary" > diary.txt; chown john:john diary.txt; chmod 600 diary.txt
chown john:john showid
ls -l diary.txt showid
echo "--- an ordinary program runs with the IDs of the user who starts it:"
su user1 -c "$L/showid $L/diary.txt"
echo "--- chmod u+s (4755): it runs with the effective UID of its owner, john:"
chmod 4755 showid; ls -l showid
su user1 -c "$L/showid $L/diary.txt"
echo "--- chmod g+s (2755) instead: the effective GID becomes the file's group:"
chmod 2755 showid; ls -l showid
su user1 -c "$L/showid"
echo "--- a real setuid-root program of the system:"
ls -l /usr/bin/passwd
echo "--- the setuid bit on a script is ignored by the kernel:"
printf '#!/bin/sh\necho "script: real UID $(id -ru), effective UID $(id -u)"\n' > who.sh
chown john:john who.sh; chmod 4755 who.sh; ls -l who.sh
su user1 -c "$L/who.sh"
echo "--- and on a file system mounted with nosuid:"
mkdir -p /mnt/l10nosuid; mount -t tmpfs -o nosuid,size=4m tmpfs /mnt/l10nosuid
cp -p showid /mnt/l10nosuid/; chmod 4755 /mnt/l10nosuid/showid
grep l10nosuid /proc/mounts
su user1 -c "/mnt/l10nosuid/showid"
umount /mnt/l10nosuid; rmdir /mnt/l10nosuid
