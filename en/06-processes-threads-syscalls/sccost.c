/* sccost.c: what does crossing into the kernel cost?
 * Times, per call: an ordinary function call, getpid() through the libc
 * wrapper, getpid() through syscall(), clock_gettime() through the vDSO
 * (no kernel entry), and clock_gettime() forced into the kernel with syscall().
 * Usage: ./sccost [calls per test]
 * Build: gcc -O2 -o sccost sccost.c */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static long N = 2000000;            /* or the first argument */

static double now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + t.tv_nsec;
}

__attribute__((noinline)) static long plain(long x) { __asm__ volatile(""); return x + 1; }

int main(int argc, char **argv)
{
    if (argc > 1) N = atol(argv[1]);
    struct timespec ts;
    volatile long sink = 0;
    double t0, t;

    t0 = now();
    for (long i = 0; i < N; i++) sink += plain(i);
    t = (now() - t0) / N;
    printf("function call:                         %7.1f ns\n", t);

    t0 = now();
    for (long i = 0; i < N; i++) sink += getpid();
    t = (now() - t0) / N;
    printf("getpid() (libc wrapper):               %7.1f ns\n", t);

    t0 = now();
    for (long i = 0; i < N; i++) sink += syscall(SYS_getpid);
    t = (now() - t0) / N;
    printf("syscall(SYS_getpid):                   %7.1f ns\n", t);

    t0 = now();
    for (long i = 0; i < N; i++) { clock_gettime(CLOCK_MONOTONIC, &ts); sink += ts.tv_nsec; }
    t = (now() - t0) / N;
    printf("clock_gettime() (vDSO, no kernel):     %7.1f ns\n", t);

    t0 = now();
    for (long i = 0; i < N; i++) { syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &ts); sink += ts.tv_nsec; }
    t = (now() - t0) / N;
    printf("syscall(SYS_clock_gettime) (kernel):   %7.1f ns\n", t);
    return 0;
}
