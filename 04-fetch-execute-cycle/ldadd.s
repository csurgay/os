    .globl _start
    .text
_start:
    mov  $3, %eax        # LD 3   (immediate)
    add  $2, %eax        # ADD 2
    jz   done            # JZ: jump if ZF = 1
    mov  %eax, %edi      # exit code = result
done:
    mov  $60, %eax       # syscall number: exit
    syscall
