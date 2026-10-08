/* hello3.c: one system call, three ways (x86-64 Linux).
 * 1. the libc wrapper write(), 2. the generic syscall() function,
 * 3. the bare `syscall` instruction with the registers set by hand.
 * Then the same call with a bad file descriptor: the kernel returns -EBADF,
 * the wrapper turns it into -1 and errno = EBADF.
 * Build: gcc -O2 -o hello3 hello3.c */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

static long raw_syscall3(long nr, long a1, long a2, long a3)
{
    long ret;
    /* number in rax, arguments in rdi, rsi, rdx; result comes back in rax.
       The instruction itself overwrites rcx (return address) and r11 (rflags). */
    __asm__ volatile ("syscall"
                      : "=a"(ret)
                      : "a"(nr), "D"(a1), "S"(a2), "d"(a3)
                      : "rcx", "r11", "memory");
    return ret;
}

int main(void)
{
    if (write(1, "1: libc wrapper write()\n", 24) < 0)
        return 1;
    syscall(SYS_write, 1, "2: syscall(SYS_write, ...)\n", 27);
    raw_syscall3(1 /* __NR_write on x86-64 */, 1, (long)"3: bare syscall instruction\n", 28);

    printf("SYS_write = %d, SYS_getpid = %d, SYS_exit_group = %d\n",
           SYS_write, SYS_getpid, SYS_exit_group);

    long r = write(42, "x", 1);
    printf("write(42, ...) via libc: returns %ld, errno = %d (%s)\n", r, errno, strerror(errno));
    r = raw_syscall3(1, 42, (long)"x", 1);
    printf("write(42, ...) raw:      returns %ld (the kernel's -EBADF; EBADF = %d)\n", r, EBADF);
    return 0;
}
