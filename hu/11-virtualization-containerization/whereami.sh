#!/bin/bash
# whereami.sh - is this Linux running on real hardware, in a virtual machine, or in a container?
run() { echo "\$ $*"; eval "$@" 2>&1; }
# 1. What the CPU says (CPUID): the "hypervisor" bit and the hypervisor's name
run 'grep -o -w -m1 hypervisor /proc/cpuinfo'
run 'lscpu | grep -E "^(Model name|Hypervisor vendor|Virtualization type)"'
# 2. What the kernel noticed while booting
run 'dmesg | grep -m3 -E "Hypervisor detected|kvm-clock: Using|kvm-guest"'
# 3. Which devices it sees: virtio devices, made for virtual machines
run 'for d in /sys/bus/virtio/devices/*; do basename "$(readlink "$d/driver")"; done | sort | uniq -c'
# 4. Can this machine run virtual machines itself? (vmx = Intel VT-x, svm = AMD-V)
run 'grep -c -w -E "vmx|svm" /proc/cpuinfo'
run 'ls /dev/kvm'
# 5. systemd's verdict
run 'systemd-detect-virt --vm'
run 'systemd-detect-virt --container'
run 'cat /run/systemd/container'
