#!/bin/sh
# caps.sh - root bypasses the permission bits through capabilities, which can be dropped or granted
cd /srv/lab10
rm -rf caps; mkdir caps; cd caps
echo "nobody may read this" > locked.txt; chmod 0000 locked.txt; ls -l locked.txt
echo "--- root reads it anyway:"
cat locked.txt
echo "--- some capabilities of this root shell (effective set, decoded, filtered):"
capsh --decode=$(awk '/^CapEff/ {print $2}' /proc/self/status) | sed 's/.*=//' | tr ',' '\n' | grep -E 'dac|fowner|chown|setuid|kill|net_bind' | tr '\n' ' '; echo
echo "--- root without CAP_DAC_OVERRIDE and CAP_DAC_READ_SEARCH:"
capsh --drop=cap_dac_override,cap_dac_read_search -- -c 'id -u; cat locked.txt'
echo "--- the opposite: an ordinary user with one capability on one program"
echo "root's note" > rootonly.txt; chmod 600 rootonly.txt
cp /usr/bin/cat ./rcat; chmod 755 ./rcat; chmod 755 /srv/lab10/caps
su user1 -c '/srv/lab10/caps/rcat /srv/lab10/caps/rootonly.txt'
setcap cap_dac_read_search=ep ./rcat
getcap ./rcat
su user1 -c '/srv/lab10/caps/rcat /srv/lab10/caps/rootonly.txt'
