/* faults.c - demand paging: memory is promised at once but given page by
 * page, at the first touch, through a page fault.
 * Usage: ./faults [huge]      (huge: ask for 2 MiB transparent huge pages)   */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

#define SIZE (1L << 30)                                 /* 1 GiB */

static void report(const char *when) {
    struct rusage u; getrusage(RUSAGE_SELF, &u);
    long pages; FILE *f = fopen("/proc/self/statm", "r");
    if (fscanf(f, "%*s %ld", &pages) != 1) pages = 0;  /* resident pages */
    fclose(f);
    printf("%-28s resident %5ld MiB, minor faults %7ld, major faults %ld\n",
           when, pages * sysconf(_SC_PAGESIZE) >> 20, u.ru_minflt, u.ru_majflt);
}

int main(int argc, char **argv) {
    int huge = argc > 1 && strcmp(argv[1], "huge") == 0;
    report("at start:");
    char *p = mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (huge) madvise(p, SIZE, MADV_HUGEPAGE);
    report("after mmap of 1 GiB:");
    struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
    for (long i = 0; i < SIZE; i += 4096) p[i] = 1;     /* touch every 4 KiB page once */
    clock_gettime(CLOCK_MONOTONIC, &b);
    report("after touching every page:");
    printf("touching took %.0f ms\n", ((b.tv_sec - a.tv_sec) * 1e9 + (b.tv_nsec - a.tv_nsec)) / 1e6);
    FILE *f = fopen("/proc/self/status", "r"); char line[128];       /* size of the page tables */
    while (fgets(line, sizeof line, f))
        if (!strncmp(line, "VmPTE:", 6)) printf("page tables of this process: %s", line + 6);
    fclose(f);
    return 0;
}
