#!/bin/sh
# sticky.sh - a shared directory like /tmp, without and with the sticky bit
cd /srv/lab10
ls -ld /tmp
for mode in 0777 1777; do
    rm -rf shared; mkdir shared; chmod $mode shared
    echo "--- shared is $(stat -c %A shared) ($mode)"
    su user1 -c 'echo "user1 was here" > /srv/lab10/shared/file.txt'
    ls -l shared/file.txt
    su user2 -c 'cd /srv/lab10/shared && mv file.txt mine.txt && echo "user2: renamed it to mine.txt" && mv mine.txt file.txt'
    su user2 -c 'cd /srv/lab10/shared && rm -f file.txt && echo "user2: deleted the file of user1"'
done
echo "--- the owner may still delete it:"
su user1 -c 'rm /srv/lab10/shared/file.txt && echo "user1: deleted own file"'
