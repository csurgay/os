/* latency.c - how late does a sleeping program wake up?
 *
 * The program asks to be woken every 1 ms, at exact absolute times.
 * Waking it up takes a timer interrupt, the kernel's interrupt handling
 * and the scheduler. The difference between the requested and the actual
 * wake-up time is the latency of that whole chain.
 *
 * Usage:  ./latency            ordinary task (the kernel may add up to 50 us of "timer slack")
 *         ./latency noslack    ask the kernel for (almost) no timer slack
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <time.h>

#define PERIOD_NS 1000000L          /* 1 ms */
#define LOOPS     5000

static long ns_between(struct timespec a, struct timespec b) {
    return (b.tv_sec - a.tv_sec) * 1000000000L + (b.tv_nsec - a.tv_nsec);
}

static int cmp(const void *a, const void *b) {
    long x = *(const long *)a, y = *(const long *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    static long lat[LOOPS];
    struct timespec next, now;

    if (argc > 1 && strcmp(argv[1], "noslack") == 0)
        prctl(PR_SET_TIMERSLACK, 1UL, 0, 0, 0);     /* slack = 1 ns instead of 50 us */

    clock_gettime(CLOCK_MONOTONIC, &next);
    for (int i = 0; i < LOOPS; i++) {
        next.tv_nsec += PERIOD_NS;                  /* next wake-up time */
        if (next.tv_nsec >= 1000000000L) { next.tv_nsec -= 1000000000L; next.tv_sec++; }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL);
        clock_gettime(CLOCK_MONOTONIC, &now);
        lat[i] = ns_between(next, now);             /* how late we woke up */
    }
    qsort(lat, LOOPS, sizeof(long), cmp);
    printf("%d wake-ups, latency in microseconds:\n", LOOPS);
    printf("  min %6.1f   median %6.1f   99%% %6.1f   max %6.1f\n",
           lat[0] / 1e3, lat[LOOPS / 2] / 1e3, lat[LOOPS * 99 / 100] / 1e3, lat[LOOPS - 1] / 1e3);
    return 0;
}
