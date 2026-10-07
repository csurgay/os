/* counter.c - four ways to let two threads increment one shared counter.
 * Usage: ./counter none|atomic|spin|mutex  [threads]                        */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define N 10000000L
volatile long x = 0;
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;   /* OS-assisted lock (futex) */
volatile char spin = 0;                          /* our own test-and-set lock */
const char *mode;

static void *worker(void *arg) {
    (void)arg;
    for (long i = 0; i < N; i++) {
        if (!strcmp(mode, "none")) {
            x++;                                             /* racy           */
        } else if (!strcmp(mode, "atomic")) {
            __atomic_fetch_add(&x, 1, __ATOMIC_SEQ_CST);     /* lock add        */
        } else if (!strcmp(mode, "spin")) {
            while (__atomic_test_and_set(&spin, __ATOMIC_ACQUIRE))
                ;                                            /* xchg, busy-wait */
            x++;
            __atomic_clear(&spin, __ATOMIC_RELEASE);
        } else {
            pthread_mutex_lock(&m);                          /* may sleep       */
            x++;
            pthread_mutex_unlock(&m);
        }
    }
    return NULL;
}

int main(int argc, char **argv) {
    mode = argc > 1 ? argv[1] : "none";
    int nt = argc > 2 ? atoi(argv[2]) : 2;
    if (nt < 1 || nt > 16) { fprintf(stderr, "threads: 1..16\n"); return 1; }
    pthread_t t[16];
    struct timespec a, b;
    clock_gettime(CLOCK_MONOTONIC, &a);
    for (int i = 0; i < nt; i++) pthread_create(&t[i], NULL, worker, NULL);
    for (int i = 0; i < nt; i++) pthread_join(t[i], NULL);
    clock_gettime(CLOCK_MONOTONIC, &b);
    double s = (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
    printf("%-6s %d threads: x = %9ld (expected %9ld)  %5.2f s  %5.1f ns per increment\n",
           mode, nt, x, nt * N, s, s * 1e9 / (nt * N));
    return 0;
}
