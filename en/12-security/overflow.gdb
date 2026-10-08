# gcc -O0 -g -fno-stack-protector -o overflow-plain overflow.c
# gdb -q -batch -x overflow.gdb --args ./overflow-plain AAAA...
# Stops in greet() before and after strcpy and shows the two words just
# above the frame: the saved frame pointer (at rbp) and the return address
# (at rbp+8).
set pagination off
break 12
break 13
run
printf "before strcpy: buf at %p\n", buf
x/2gx $rbp
info symbol *(long *)($rbp + 8)
continue
printf "after strcpy:\n"
x/2gx $rbp
continue
x/i $pc
