#!/bin/bash
# userns.sh - rootless: an ordinary user becomes "root" in a user namespace of its own.
# Run as root; it creates the user lab11 if needed and runs every step as lab11.
id lab11 >/dev/null 2>&1 || useradd -m -s /bin/bash lab11
run() { echo "\$ $*"; su lab11 -c "$*" 2>&1; }
run 'id'
run 'hostname box'
run "unshare --user --map-root-user bash -c 'id; cat /proc/self/uid_map; grep CapEff /proc/self/status'"
run "unshare --user --map-root-user bash -c 'touch /etc/owned-by-me; ls -ln /etc/hostname'"
run "unshare --user --map-root-user --uts bash -c 'hostname box; hostname'"
