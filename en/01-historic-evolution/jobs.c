/* jobs.c - a CPU-bound job, an I/O-bound job, and a counting job.
 *
 *   ./jobs cpu     uses 2 seconds of CPU time without ever waiting
 *   ./jobs io      40 rounds of: 10 ms of computing, then 40 ms of waiting
 *                  (the wait stands in for a slow I/O device; like a real
 *                  device wait, the process blocks and gives up the CPU)
 *   ./jobs count   counts as fast as it can for 3 seconds of wall-clock time
 *
 * At the end each job reports its wall-clock time, CPU time and context switches.
 */
#include <stdio.h>
#include <string.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

static double now(clockid_t c) {
    struct timespec t;
    clock_gettime(c, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static void compute(double seconds) {            /* burn this much CPU time */
    double end = now(CLOCK_PROCESS_CPUTIME_ID) + seconds;
    volatile unsigned long x = 0;
    while (now(CLOCK_PROCESS_CPUTIME_ID) < end)
        for (int i = 0; i < 1000; i++) x++;
}

int main(int argc, char **argv) {
    const char *mode = (argc > 1) ? argv[1] : "cpu";
    double start = now(CLOCK_MONOTONIC);
    unsigned long count = 0;

    if (strcmp(mode, "cpu") == 0) {
        compute(2.0);
    } else if (strcmp(mode, "io") == 0) {
        for (int i = 0; i < 40; i++) {
            compute(0.010);                      /* prepare the next request  */
            usleep(40000);                       /* wait for the "device"     */
        }
    } else {                                     /* count */
        while (now(CLOCK_MONOTONIC) - start < 3.0)
            for (int i = 0; i < 1000; i++) count++;
    }

    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
    double cpu = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6
               + ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6;
    printf("%-5s wall %5.2f s  cpu %5.2f s  switches: voluntary %4ld, involuntary %4ld",
           mode, now(CLOCK_MONOTONIC) - start, cpu, ru.ru_nvcsw, ru.ru_nivcsw);
    if (count) printf("  count %lu million", count / 1000000);
    printf("\n");
    return 0;
}
