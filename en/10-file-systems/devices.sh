#!/bin/sh
# devices.sh: block devices, their queues and drivers, as sysfs shows them.
echo "--- the block devices: I/O scheduler, request slots, hardware queues"
for d in vda loop0 zram0; do
    q=/sys/block/$d/queue
    if [ ! -e $q/scheduler ]; then
        printf "%-6s no scheduler, no request slots, hw queues: 0 (the driver takes bios directly)\n" $d
        continue
    fi
    printf "%-6s scheduler: %-28s nr_requests: %-4s hw queues: %s\n" $d \
        "$(cat $q/scheduler)" "$(cat $q/nr_requests)" "$(ls /sys/block/$d/mq 2>/dev/null | wc -l)"
done
echo "CPUs served by hardware queue 0 of vda: $(cat /sys/block/vda/mq/0/cpu_list)"
echo "--- where vda sits in the device tree"
readlink -f /sys/block/vda
echo "--- the driver bound to each level"
for dev in /sys/block/vda/device /sys/block/vda/device/..; do
    d=$(readlink -f $dev)
    echo "$(basename $d) on bus $(basename $(readlink $d/subsystem)) -> driver $(basename $(readlink $d/driver))"
done
p=/sys/bus/pci/devices/0000:00:02.0
echo "PCI vendor $(cat $p/vendor), device $(cat $p/device), class $(cat $p/class)"
echo "--- what the kernel tells udev about vda"
cat /sys/block/vda/uevent
ls -l /dev/vda
echo "--- the buses of this machine"
ls /sys/bus | tr '\n' ' '; echo
echo "--- major numbers: the first character drivers, and all block drivers"
sed -n '1,6p' /proc/devices; echo "  ..."
sed -n '/^Block devices:/,$p' /proc/devices
echo "--- loadable modules"
if [ -e /proc/modules ]; then lsmod | head; else
    echo "no /proc/modules: $(zcat /proc/config.gz | grep CONFIG_MODULES[^_])"; fi
