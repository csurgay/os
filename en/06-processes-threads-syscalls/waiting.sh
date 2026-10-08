#!/bin/sh
# waiting.sh: where is a sleeping process waiting? (/proc, gdb, /proc again)
sleep 30 &
P=$!
sleep 0.2
show() {
    echo "\$ cat /proc/$P/wchan; echo; cut -d' ' -f1-3 /proc/$P/syscall"
    cat /proc/$P/wchan; echo; cut -d' ' -f1-3 /proc/$P/syscall
}
show
echo "\$ gdb -q -p $P -batch -ex bt 2>/dev/null | grep '^#' | cut -d'(' -f1"
gdb -q -p $P -batch -ex bt 2>/dev/null | grep '^#' | cut -d'(' -f1
show
kill $P
