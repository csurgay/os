#!/bin/sh
# modes.sh - chmod in octal and symbolic form, capital X, umask, and the 12-bit mode
cd /srv/lab10
rm -rf m; mkdir m; cd m
show() { stat -c '%a  %A  %n' "$@"; }
touch f; mkdir d
echo "--- octal: every digit sets one class completely"
chmod 640 f; show f
echo "--- symbolic: change single bits, leave the others alone"
chmod u+x,g-r,o+r f; show f
chmod a=r,u+w f; show f
echo "--- capital X: x only for directories and files that are already executable by someone"
touch script plain; chmod 744 script; chmod 644 plain; chmod 755 d
chmod -R go-rwx . ; show d plain script
chmod -R go+rX . ; show d plain script
echo "--- umask: bits removed from new files (base 666) and directories (base 777)"
for u in 022 002 077 027; do
    rm -rf n nd; (umask $u; touch n; mkdir nd); echo "umask $u -> file $(stat -c '%a %A' n), dir $(stat -c '%a %A' nd)"
done
echo "--- the special bits: 4 = setuid, 2 = setgid, 1 = sticky"
for m in 4755 2755 1777 4644 2644 1666 7743 3374 7640; do chmod $m f; show f; done
