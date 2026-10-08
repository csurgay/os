#!/bin/sh
# trace-minish.sh: what does minish do for "ls /etc | grep ^host >hosts.txt"?
# strace -ff writes one trace file per process (tr.PID); for the children,
# only the lines up to their execve() are printed: the shell's own work;
# for the shell, the lines from pipe2() on (before it, the loader opens libc).
cd "$(dirname "$0")" || exit 1
rm -f tr.*
echo 'ls /etc | grep ^host >hosts.txt' |
    PATH=/usr/bin:/bin strace -ff -o tr -qq -e signal=none \
        -e trace=pipe2,clone,dup2,close,openat,execve,wait4 ./minish > /dev/null
first=yes
for f in $(ls tr.* | sort -t. -k2 -n); do
    echo "== process ${f#tr.}"
    if [ $first = yes ]; then
        sed -n '/^pipe2/,$p' "$f"; first=no      # from the pipe on
    else
        sed '/^execve/q' "$f"
    fi
done
rm -f tr.*
