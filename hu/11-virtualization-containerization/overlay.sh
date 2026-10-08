#!/bin/bash
# overlay.sh - OverlayFS by hand: two read-only lower layers, one writable upper layer.
run() { echo "\$ $*"; eval "$@" 2>&1; }
D=/srv/lab11/ovl
rm -rf $D; mkdir -p $D/{base,app,upper,work,merged}
echo "base v1"      > $D/base/os-release      # layer 1: "the base image"
echo "config, base" > $D/base/app.conf
echo "print('hi')"  > $D/app/app.py           # layer 2: "the application"
cd $D
run "mount -t overlay overlay -o lowerdir=app:base,upperdir=upper,workdir=work merged"
run "ls merged"
run "echo 'config, changed' >> merged/app.conf; echo 'scratch' > merged/new.txt; rm merged/os-release"
run "ls merged"
run "cat base/app.conf; ls base"
run "ls -l upper | tail -n +2"
run "cat upper/app.conf"
run "umount merged; ls merged"
