#!/bin/bash
# switches.sh - voluntary and involuntary context switches of three processes on one core
taskset -c 0 bash -c 'while :; do :; done' &                 A=$!   # CPU-bound
taskset -c 0 bash -c 'while :; do :; done' &                 B=$!   # CPU-bound
taskset -c 0 bash -c 'while :; do sleep 0.01; done' &        C=$!   # mostly waits
sleep 5
for p in $A $B $C; do
  printf "%-6s %-38s" $p "$(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-38)"
  grep ctxt /proc/$p/status | tr '\n' ' ' | sed 's/_ctxt_switches://g'; echo
done
kill $A $B $C
