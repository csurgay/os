/* latency.c - how late does a periodic task wake up?
 * Every PERIOD_US microseconds the task sleeps until an absolute deadline
 * (clock_nanosleep with TIMER_ABSTIME) and records how late it woke up.
 * Usage: ./latency [iterations] [period_us]
 * Run it as SCHED_OTHER (default) or as SCHED_FIFO with: chrt -f 80 ./latency
 */
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static long long ns(const struct timespec *t) { return t->tv_sec * 1000000000LL + t->tv_nsec; }
static int cmp(const void *a, const void *b) {
    long long x = *(const long long *)a, y = *(const long long *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    int n = argc > 1 ? atoi(argv[1]) : 5000;
    long period = (argc > 2 ? atol(argv[2]) : 1000) * 1000L;      /* ns */
    long long *late = malloc(n * sizeof *late);
    struct timespec next, now;
    clock_gettime(CLOCK_MONOTONIC, &next);
    for (int i = 0; i < n; i++) {
        next.tv_nsec += period;
        while (next.tv_nsec >= 1000000000L) { next.tv_nsec -= 1000000000L; next.tv_sec++; }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL);
        clock_gettime(CLOCK_MONOTONIC, &now);
        late[i] = ns(&now) - ns(&next);
    }
    int pol = sched_getscheduler(0);
    double sum = 0; int over = 0;
    for (int i = 0; i < n; i++) { sum += late[i]; if (late[i] > period) over++; }
    qsort(late, n, sizeof *late, cmp);
    printf("%-10s n=%d period=%ld us  lateness [us]: min %.1f  median %.1f  avg %.1f  p99 %.1f  max %.1f  missed periods %d\n",
           pol == SCHED_FIFO ? "SCHED_FIFO" : pol == SCHED_RR ? "SCHED_RR" : "SCHED_OTHER",
           n, period / 1000, late[0] / 1e3, late[n / 2] / 1e3, sum / n / 1e3,
           late[(int)(n * 0.99)] / 1e3, late[n - 1] / 1e3, over);
    return 0;
}
