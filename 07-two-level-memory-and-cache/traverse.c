/* traverse.c - the same sum, two loop orders (Scott Meyers' example).
 * C stores a 2-D array row by row: a[i][0], a[i][1], ... are neighbours in
 * memory, a[i][j] and a[i+1][j] are N*4 bytes apart.
 * Usage: ./traverse N        an N x N array of int                           */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

int main(int argc, char **argv) {
    int n = argc > 1 ? atoi(argv[1]) : 4096;
    int (*a)[n] = malloc(sizeof(int[n][n]));          /* one block, row-major */
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) a[i][j] = i + j;
    long sum = 0; double t0, t1, t2;

    t0 = now();
    for (int i = 0; i < n; i++)                       /* row by row: along memory */
        for (int j = 0; j < n; j++) sum += a[i][j];
    t1 = now();
    for (int j = 0; j < n; j++)                       /* column by column: jumps of n*4 bytes */
        for (int i = 0; i < n; i++) sum += a[i][j];
    t2 = now();

    printf("%5d x %-5d (%4zu MiB)  row by row %7.1f ms   column by column %7.1f ms   ratio %4.1f  (sum %ld)\n",
           n, n, sizeof(int[n][n]) >> 20, (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t2 - t1) / (t1 - t0), sum);
    free(a);
    return 0;
}
