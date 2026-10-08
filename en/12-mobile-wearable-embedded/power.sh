#!/bin/bash
# power.sh - what does this machine offer for power management?
run() { echo "\$ $*"; eval "$@" 2>&1; }
run "ls /sys/devices/system/cpu/cpufreq/ | wc -l"
run "ls /sys/devices/system/cpu/cpu0/cpufreq"
run "cat /sys/devices/system/cpu/cpuidle/current_driver /sys/devices/system/cpu/cpuidle/current_governor"
run "cat /sys/devices/system/cpu/cpuidle/available_governors"
run "ls /sys/devices/system/cpu/cpu0/cpuidle"
run "ls -A /sys/class/thermal /sys/class/power_supply"
run "cat /sys/devices/system/cpu/cpu*/cpu_capacity"
run "ls /sys/devices/system/cpu/cpu0/topology/"
run "cat /proc/self/timerslack_ns; chrt -f 80 cat /proc/self/timerslack_ns"
run "uname -v"
