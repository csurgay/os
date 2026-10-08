/* stride.c - touch every k-th int of a 64 MiB array. The work done falls as
 * 1/k, but the time stays almost the same until k reaches the cache line
 * (64 bytes = 16 ints): memory is read in whole lines, not in ints.
 * Usage: ./stride                                                            */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N (16 * 1024 * 1024)                 /* 16 Mi ints = 64 MiB */
int main(void) {
    int *a = malloc(N * sizeof(int));
    for (long i = 0; i < N; i++) a[i] = 1;
    printf("%6s %10s %12s %12s\n", "stride", "accesses", "time (ms)", "ns/access");
    for (int k = 1; k <= 1024; k *= 2) {
        struct timespec t0, t1;
        clock_gettime(CLOCK_MONOTONIC, &t0);
        for (long i = 0; i < N; i += k) a[i] *= 3;
        clock_gettime(CLOCK_MONOTONIC, &t1);
        double ms = (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
        long acc = N / k;
        printf("%6d %10ld %12.1f %12.2f\n", k, acc, ms, ms * 1e6 / acc);
    }
    return a[7] == 0;
}
