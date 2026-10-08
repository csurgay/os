#!/bin/bash
# shares.sh - two CPU-bound processes on the same core: nice 0 against nice N
N=${1:-5}
taskset -c 0 bash -c 'while :; do :; done' &            A=$!
taskset -c 0 nice -n $N bash -c 'while :; do :; done' & B=$!
sleep 10
ticks() { awk '{print $14 + $15}' /proc/$1/stat; }      # utime + stime, in clock ticks
a=$(ticks $A); b=$(ticks $B)
kill $A $B
echo "nice 0 : $a ticks ($(( 100 * a / (a + b) ))%)"
echo "nice $N : $b ticks ($(( 100 * b / (a + b) ))%)"
