/* protect.c - the access-rights bits of a page table entry at work.
 * Writes to a read-only page, reads an unmapped page, and executes data;
 * each time the CPU raises a page fault, the kernel finds the access illegal
 * and sends SIGSEGV, which we catch to print what happened.                */
#define _GNU_SOURCE
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static sigjmp_buf back;
static volatile unsigned long nowhere = 0x10;           /* an address with no mapping */
static void handler(int sig, siginfo_t *si, void *ctx) {
    (void)sig; (void)ctx;
    printf("  -> SIGSEGV at %p, code %s\n", si->si_addr,
           si->si_code == SEGV_ACCERR ? "SEGV_ACCERR (address is mapped, but this access is not allowed)"
         : si->si_code == SEGV_MAPERR ? "SEGV_MAPERR (no mapping at this address)" : "other");
    siglongjmp(back, 1);
}

int main(void) {
    struct sigaction sa; memset(&sa, 0, sizeof sa);
    sa.sa_sigaction = handler; sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, NULL);
    long ps = sysconf(_SC_PAGESIZE);
    char *ro = mmap(NULL, ps, PROT_READ, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    char *data = mmap(NULL, ps, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    data[0] = (char)0xc3;                                   /* x86 'ret' instruction */

    puts("1. write to a read-only page:");
    if (!sigsetjmp(back, 1)) { ro[0] = 1; puts("  -> allowed?!"); }
    puts("2. read address 0x10 (nothing mapped there):");
    if (!sigsetjmp(back, 1)) { volatile char c = *(volatile char *)nowhere; (void)c; puts("  -> allowed?!"); }
    puts("3. execute code stored in a read-write data page (NX bit):");
    if (!sigsetjmp(back, 1)) { ((void (*)(void))data)(); puts("  -> allowed?!"); }
    puts("4. the same after mprotect(PROT_READ | PROT_EXEC):");
    mprotect(data, ps, PROT_READ | PROT_EXEC);
    if (!sigsetjmp(back, 1)) { ((void (*)(void))data)(); puts("  -> executed and returned normally"); }
    return 0;
}
