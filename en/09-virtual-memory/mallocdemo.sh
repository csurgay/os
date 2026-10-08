#!/bin/sh
# mallocdemo.sh: run mallocdemo under strace and show the memory system calls
# of each step. A run of consecutive brk() calls is shortened to its first and
# last call and a count, and only the calls after the program's first marker
# are shown (before it, the dynamic loader maps the C library).
strace -f -s 100 -e trace=brk,mmap,munmap,mprotect,madvise,write ./mallocdemo 2>&1 >/dev/null |
awk '
/^write\(1, "---/ { started = 1 }
!started { next }
/^brk\(/ { if (n == 0) first = $0; last = $0; n++; next }
{ flush(); print }
function flush() {
    if (n == 1) print first
    else if (n == 2) { print first; print last }
    else if (n > 2) { print first; printf "   ... %d more brk() calls ...\n", n - 2; print last }
    n = 0
}
END { flush() }' |
sed -E 's/^write\(1, "([^"]*)\\n"[^)]*\) += [0-9]+$/\1/; s/^write\(1, "([^"]*)"\.\.\., [0-9]+\) += [0-9]+$/\1.../'
