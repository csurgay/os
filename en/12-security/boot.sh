#!/bin/bash
# boot.sh - how did this machine boot, and what can it prove about it?
echo "== firmware interfaces"
ls /sys/firmware
[ -d /sys/firmware/efi ] && echo "booted by UEFI" || echo "no /sys/firmware/efi: not booted by UEFI"
echo "== Secure Boot and TPM"
command -v mokutil >/dev/null && mokutil --sb-state || echo "mokutil not installed"
ls /dev/tpm* /sys/class/tpm 2>&1
echo "== the first steps of the kernel"
dmesg | grep -E "Linux version|ACPI: RSDP|NX \(Execute|RAMDISK|Unpacking initramfs|Write protecting|Kernel is locked down|LSM: initializing|Run .* as init"
echo "== process 1"
ps -o pid,comm -p 1
systemd-analyze 2>&1 | head -1
