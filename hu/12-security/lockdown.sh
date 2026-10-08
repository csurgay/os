#!/bin/bash
# lockdown.sh - the kernel protects itself from root (run as root)
# securityfs and debugfs are not always mounted; mount them for the demo.
mountpoint -q /sys/kernel/security || mount -t securityfs securityfs /sys/kernel/security
echo "== lockdown mode (the one in brackets is active)"
cat /sys/kernel/security/lockdown
echo "== a debugging interface of the scheduler, read by root"
mount -t debugfs none /sys/kernel/debug
cat /sys/kernel/debug/sched/features
dmesg | tail -1
umount /sys/kernel/debug
echo "== can root switch it off?"
echo none > /sys/kernel/security/lockdown
cat /sys/kernel/security/lockdown
