#!/bin/sh
# firstmatch.sh - only the FIRST matching class (owner, group, others) counts
cd /srv/lab10
rm -rf fm; mkdir fm
echo "anyone but john may read this" > fm/note.txt
chown john:john fm/note.txt
chmod 0007 fm/note.txt                       # -------rwx : nothing for owner and group
ls -l fm/note.txt
echo "--- as john (the owner):"
su john -c 'cat /srv/lab10/fm/note.txt'
echo "--- as user1 (falls into 'others'):"
su user1 -c 'cat /srv/lab10/fm/note.txt'
echo "--- the same for a directory, d------rwx:"
mkdir fm/dir; touch fm/dir/a fm/dir/b
chown john:john fm/dir; chmod 0007 fm/dir
ls -ld fm/dir
su john  -c 'ls /srv/lab10/fm/dir'
su user1 -c 'ls /srv/lab10/fm/dir'
