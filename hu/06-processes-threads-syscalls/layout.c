/* layout.c: where do the parts of a process live in its address space?
 * Prints the address of a function (text), an initialised global (data),
 * an uninitialised global (BSS), a small and a large malloc (heap and mmap),
 * a local variable (stack) and a library function, then the lines of
 * /proc/self/maps that contain them.
 * Build: gcc -O0 -o layout layout.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int initialised = 42;          /* .data */
int uninitialised;             /* .bss  */

struct item { const char *name; unsigned long addr; };

int main(void)
{
    int local = 7;                                  /* stack */
    char *small = malloc(100);                      /* heap (brk)          */
    char *large = malloc(1 << 20);                  /* 1 MiB: its own mmap */
    struct item it[] = {
        { "text  (main)",          (unsigned long)main },
        { "data  (initialised)",   (unsigned long)&initialised },
        { "bss   (uninitialised)", (unsigned long)&uninitialised },
        { "heap  (malloc 100 B)",  (unsigned long)small },
        { "mmap  (malloc 1 MiB)",  (unsigned long)large },
        { "libc  (printf)",        (unsigned long)printf },
        { "stack (local)",         (unsigned long)&local },
    };
    int n = sizeof it / sizeof it[0];

    for (int i = 0; i < n; i++)
        printf("%-22s %#14lx\n", it[i].name, it[i].addr);

    printf("\nmatching lines of /proc/self/maps:\n");
    FILE *f = fopen("/proc/self/maps", "r");
    char line[512];
    while (fgets(line, sizeof line, f)) {
        unsigned long lo, hi;
        if (sscanf(line, "%lx-%lx", &lo, &hi) != 2)
            continue;
        char names[256] = "";
        for (int i = 0; i < n; i++)
            if (it[i].addr >= lo && it[i].addr < hi) {
                if (names[0]) strcat(names, ", ");
                strncat(names, it[i].name, strcspn(it[i].name, " "));  /* first word */
            }
        if (!names[0])
            continue;
        /* drop the offset, device and inode columns to keep the line short */
        char perm[8], path[256] = "";
        sscanf(line, "%*s %7s %*s %*s %*s %255s", perm, path);
        printf("%012lx-%012lx %s %-12s <- %s\n", lo, hi, perm,
               path[0] ? (strrchr(path, '/') ? strrchr(path, '/') + 1 : path)
                       : "(anonymous)", names);
    }
    fclose(f);
    free(small);
    free(large);
    return 0;
}
