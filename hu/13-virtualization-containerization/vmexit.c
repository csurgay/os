/* vmexit.c - what does an instruction cost that the hypervisor must handle?
 * Under Intel VT-x and AMD-V, CPUID always causes a VM exit: the CPU leaves
 * the guest, the hypervisor emulates the instruction and resumes the guest.
 * We time it against an ordinary instruction and against a system call. */
#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>

#define N 200000

static double now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + t.tv_nsec;
}

static inline void cpuid(unsigned leaf) {
    unsigned a, b, c, d;
    __asm__ volatile("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(leaf), "c"(0));
}

int main(void) {
    double t0, t1;
    volatile unsigned x = 0;

    t0 = now_ns();
    for (int i = 0; i < N; i++) x += i;                  /* ordinary work, no trap */
    t1 = now_ns();
    printf("ordinary add:                %8.1f ns\n", (t1 - t0) / N);

    t0 = now_ns();
    for (int i = 0; i < N; i++) syscall(SYS_getppid);    /* user -> kernel -> user */
    t1 = now_ns();
    printf("system call (getppid):       %8.1f ns\n", (t1 - t0) / N);

    t0 = now_ns();
    for (int i = 0; i < N; i++) cpuid(0);                /* guest -> hypervisor -> guest */
    t1 = now_ns();
    printf("CPUID (VM exit in a guest):  %8.1f ns\n", (t1 - t0) / N);
    return 0;
}
