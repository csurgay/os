#!/bin/bash
# kernel-hiding.sh - how much does the kernel reveal about itself? (run as root)
echo "== where is the kernel? (root, with CAP_SYSLOG)"
grep -E ' (_text|commit_creds)$' /proc/kallsyms
echo "== the same as the user nobody"
su nobody -s /bin/sh -c "grep -E ' (_text|commit_creds)$' /proc/kallsyms"
echo "== root without CAP_SYSLOG"
capsh --drop=cap_syslog -- -c "grep -E ' (_text|commit_creds)$' /proc/kallsyms"
echo "== kernel.kptr_restrict = 2: hidden even from root"
old=$(cat /proc/sys/kernel/kptr_restrict)
sysctl -w kernel.kptr_restrict=2
grep -E ' (_text|commit_creds)$' /proc/kallsyms
sysctl -q -w kernel.kptr_restrict="$old"
echo "== the settings"
sysctl kernel.kptr_restrict kernel.dmesg_restrict kernel.perf_event_paranoid kernel.randomize_va_space
echo "== dmesg as nobody"
su nobody -s /bin/sh -c "dmesg | head -1"
