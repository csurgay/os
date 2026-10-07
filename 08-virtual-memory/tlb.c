/* tlb.c - the cost of address translation. A random pointer chase through
 * ONE 64-byte line per page, over N pages. The lines themselves (N x 64 B)
 * fit in the caches; what grows with N is the number of different pages,
 * and so of address translations the TLB must hold.
 * Usage: ./tlb [huge]   (huge: 2 MiB pages, so 512 times fewer translations) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

int main(int argc, char **argv) {
    int huge = argc > 1 && strcmp(argv[1], "huge") == 0;
    size_t span = 1UL << 30;                                   /* 1 GiB of address space */
    char *mem = mmap(NULL, span + (2 << 20), PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    char *base = (char *)(((unsigned long)mem + (2 << 20) - 1) & ~((2UL << 20) - 1));
    madvise(base, span, huge ? MADV_HUGEPAGE : MADV_NOHUGEPAGE);
    printf("%8s %10s %12s\n", "pages", "lines (KiB)", "ns/access");
    for (size_t n = 16; n <= 65536 * 4; n *= 4) {
        size_t *perm = malloc(n * sizeof(size_t));
        for (size_t i = 0; i < n; i++) perm[i] = i;
        srand(1);
        for (size_t i = n - 1; i > 0; i--) { size_t j = rand() % (i + 1), t = perm[i]; perm[i] = perm[j]; perm[j] = t; }
        /* one line in page k, at a line offset chosen so that the lines spread
           evenly over the cache sets even when the pages are physically contiguous */
        #define LINE(k) ((void **)(base + (k) * 4096 + (((k) + (k) / 64) % 64) * 64))
        for (size_t i = 0; i < n; i++) *LINE(perm[i]) = LINE(perm[(i + 1) % n]);
        void **p = LINE(perm[0]);
        for (size_t i = 0; i < n; i++) p = *p;                 /* warm up */
        long steps = 20000000;
        struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
        for (long i = 0; i < steps; i++) p = *p;
        clock_gettime(CLOCK_MONOTONIC, &b);
        printf("%8zu %10zu %12.1f\n", n, n * 64 / 1024,
               ((b.tv_sec - a.tv_sec) * 1e9 + (b.tv_nsec - a.tv_nsec)) / steps);
        if (p == NULL) puts("");
        free(perm);
    }
    FILE *f = fopen("/proc/self/smaps_rollup", "r"); char line[256];
    while (f && fgets(line, sizeof line, f))
        if (!strncmp(line, "AnonHugePages:", 14)) printf("huge pages in use by this process:%s", line + 14);
    if (f) fclose(f);
    return 0;
}
