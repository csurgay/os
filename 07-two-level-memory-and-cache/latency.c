/* latency.c - how long does one memory access take, as a function of how
 * much memory the program touches?  A "pointer chase": every 64-byte cache
 * line holds the address of the next one, in random order, so the CPU can
 * neither predict nor overlap the accesses; each one waits for the last.
 * Usage: ./latency            sizes from 4 KiB to 512 MiB, normal 4 KiB pages
 *        ./latency huge       the same with 2 MiB (transparent huge) pages    */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

static int huge = 0;                                  /* ./latency huge */

#define LINE 64
typedef struct node { struct node *next; char pad[LINE - sizeof(void *)]; } node;

static double chase(size_t bytes) {
    size_t n = bytes / LINE;
    size_t sz = (n * sizeof(node) + (2 << 20) - 1) & ~(size_t)((2 << 20) - 1);
    node *a = aligned_alloc(2 << 20, sz);            /* 2 MiB aligned        */
    if (huge) madvise(a, sz, MADV_HUGEPAGE);         /* ask for 2 MiB pages  */
    size_t *perm = malloc(n * sizeof(size_t));
    for (size_t i = 0; i < n; i++) perm[i] = i;
    for (size_t i = n - 1; i > 0; i--) {             /* random cyclic order */
        size_t j = (size_t)rand() % (i + 1), t = perm[i]; perm[i] = perm[j]; perm[j] = t;
    }
    for (size_t i = 0; i < n; i++) a[perm[i]].next = &a[perm[(i + 1) % n]];
    long steps = 50000000;
    node *p = &a[perm[0]];
    for (size_t i = 0; i < n; i++) p = p->next;      /* warm up */
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long i = 0; i < steps; i++) p = p->next;    /* the measured chase */
    clock_gettime(CLOCK_MONOTONIC, &t1);
    if (p == NULL) puts("");                         /* keep p alive */
    free(perm); free(a);
    return ((t1.tv_sec - t0.tv_sec) * 1e9 + (t1.tv_nsec - t0.tv_nsec)) / steps;
}

int main(int argc, char **argv) {
    huge = argc > 1 && strcmp(argv[1], "huge") == 0;
    srand(1);
    printf("%10s  %8s\n", "working set", "ns/access");
    for (size_t kb = 4; kb <= 512 * 1024; kb *= 2) {
        double ns = chase(kb * 1024);
        if (kb < 1024) printf("%7zu KiB  %8.1f\n", kb, ns);
        else           printf("%7zu MiB  %8.1f\n", kb / 1024, ns);
    }
    return 0;
}
