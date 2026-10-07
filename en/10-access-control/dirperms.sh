#!/bin/sh
# dirperms.sh - what r, w and x mean on a DIRECTORY, tried by user1 ("others")
# The directory d belongs to john; the file d/f inside it is rw-rw-rw- (everyone may read and
# write its CONTENT), so every "denied" below comes from the directory's bits alone.
cd /srv/lab10
try() {   # try LABEL COMMAND: run COMMAND as user1, print ok or denied
    if su user1 -c "$2" >/dev/null 2>&1; then r=ok; else r=denied; fi
    printf '%-9s' "$r"
}
printf '%-12s%-9s%-9s%-9s%-9s%-9s\n' "others" "ls d" "cd d" "cat d/f" "touch" "rm d/f"
for o in "" r x rx w wx rwx; do
    rm -rf d; mkdir d; echo data > d/f; chmod 0666 d/f; chown -R john:john d
    chmod "u=rwx,g=rx,o=$o" d
    printf '%-12s' "$(stat -c %A d)"
    try ls    'ls /srv/lab10/d'
    try cd    'cd /srv/lab10/d'
    try cat   'cat /srv/lab10/d/f'
    try touch 'touch /srv/lab10/d/new'
    try rm    'rm -f /srv/lab10/d/f'
    echo
done
echo "--- a file with no permissions at all, in a directory where user1 has w and x:"
rm -rf d; mkdir d; chmod 0733 d; chown john:john d
touch d/locked; chmod 0000 d/locked; chown john:john d/locked
ls -l d/locked
su user1 -c 'cat /srv/lab10/d/locked; rm -f /srv/lab10/d/locked && echo "rm worked: deleting is a change of the directory"'
