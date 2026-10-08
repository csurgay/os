/* falseshare.c - two threads, each with its OWN counter, nothing shared in
 * the program. If the two counters lie in the same 64-byte cache line, the
 * two cores keep taking the line away from each other ("false sharing").
 * Each increment is atomic (lock add), as for statistics counters that other
 * threads may read.
 * Usage: ./falseshare near|far [one]   (one: a single thread, for comparison) */
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#define N 100000000L
struct { long a; long b; } near __attribute__((aligned(64)));        /* 8 bytes apart, one line */
struct { long a; char pad[56]; long b; } far __attribute__((aligned(64))); /* 64 apart */

static void *inc(void *p) {
    long *c = p;
    for (long i = 0; i < N; i++) __atomic_fetch_add(c, 1, __ATOMIC_RELAXED);
    return NULL;
}

int main(int argc, char **argv) {
    int f = argc > 1 && strcmp(argv[1], "far") == 0, one = argc > 2;
    long *ca = f ? &far.a : &near.a, *cb = f ? &far.b : &near.b;
    struct timespec t0, t1; pthread_t x, y;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    pthread_create(&x, NULL, inc, ca);
    if (!one) pthread_create(&y, NULL, inc, cb);
    pthread_join(x, NULL);
    if (!one) pthread_join(y, NULL);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    printf("%-10s counters %2ld bytes apart: %.2f s\n", one ? "1 thread," : "2 threads,",
           (long)((char *)cb - (char *)ca), (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9);
    return 0;
}
