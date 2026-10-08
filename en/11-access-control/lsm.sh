#!/bin/sh
# lsm.sh - which Linux Security Modules does this kernel have, and is a MAC policy loaded?
echo "--- compiled-in security modules (kernel configuration):"
zcat /proc/config.gz | grep -E '^CONFIG_LSM=|CONFIG_SECURITY_(SELINUX|APPARMOR)[ =]'
echo "--- the modules actually active, in the order the kernel calls them (securityfs):"
d=$(mktemp -d); mount -t securityfs securityfs "$d" && cat "$d/lsm"; echo; umount "$d"; rmdir "$d"
echo "--- labels as the tools see them:"
ls -Z /etc/passwd
ps -eZ | head -3
id -Z
echo "--- the SELinux kernel interface (selinuxfs):"
mounted=0
grep -q selinuxfs /proc/mounts || { mount -t selinuxfs selinuxfs /sys/fs/selinux && mounted=1; }
printf 'enforce = %s\n' "$(cat /sys/fs/selinux/enforce)"
printf 'policy loaded: '; [ -e /sys/fs/selinux/policy ] && head -c 4 /sys/fs/selinux/policy >/dev/null 2>&1 && echo yes || echo no
printf 'booleans defined: %s\n' "$(ls /sys/fs/selinux/booleans | wc -l)"
if [ $mounted = 1 ]; then umount /sys/fs/selinux; fi
