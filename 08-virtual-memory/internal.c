/* internal.c - internal fragmentation: malloc hands out blocks in a few fixed
 * size classes, so a request usually gets more than it asked for.         */
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t req[] = {1, 8, 24, 25, 40, 100, 1000, 4000, 5000};
    printf("%8s %10s %8s\n", "asked", "got", "wasted");
    for (unsigned i = 0; i < sizeof req / sizeof req[0]; i++) {
        void *p = malloc(req[i]);
        size_t got = malloc_usable_size(p);
        printf("%8zu %10zu %7.0f%%\n", req[i], got, 100.0 * (got - req[i]) / got);
        free(p);
    }
    return 0;
}
