#!/bin/sh
# slab.sh: the kernel's slab caches. Run as root.
echo "--- the largest caches (slabtop, sorted by cache size):"
slabtop -o -s c | sed -n '7,14p'
echo "--- one cache in detail: dentry"
cd /sys/kernel/slab/dentry
echo "object size $(cat object_size) B, $(cat objs_per_slab) objects per slab, slab = 2^$(cat order) page(s)"
cd - > /dev/null
count() {   # active objects of the dentry and ext4 inode caches
    awk '$1 == "dentry" || $1 == "ext4_inode_cache" { printf "%s %d  ", $1, $2 }
         END { printf "| " }' /proc/slabinfo
    grep '^Slab:' /proc/meminfo
}
echo "--- active objects before, after creating 100000 files, after deleting them:"
count
mkdir -p /tmp/slabdemo && cd /tmp/slabdemo
seq 100000 | xargs touch
count
cd / && rm -rf /tmp/slabdemo
count
echo "--- the general-purpose caches behind kmalloc():"
for s in 8 16 32 64 96 128 192 256 512 1k 2k 4k 8k; do
    [ -d /sys/kernel/slab/kmalloc-$s ] && printf 'kmalloc-%s ' $s
done; echo
echo "--- caches merged with another cache of the same size (SLUB aliases):"
ls -l /sys/kernel/slab | grep -c -- '->'
grep -E '^(Slab|SReclaimable|SUnreclaim|VmallocUsed)' /proc/meminfo
