/* cswitch.c - cost of a context switch: two processes on the same core pass a
 * byte back and forth through two pipes. Each round trip = 2 switches
 * (plus 2 write and 2 read system calls).                                     */
#include <stdio.h>
#include <time.h>
#include <unistd.h>

#define ROUNDS 200000
int main(void) {
    int ab[2], ba[2]; char c = 'x';
    if (pipe(ab) || pipe(ba)) return 1;
    if (fork() == 0) {                       /* child: echo every byte back */
        for (int i = 0; i < ROUNDS; i++) { (void)!read(ab[0], &c, 1); (void)!write(ba[1], &c, 1); }
        return 0;
    }
    struct timespec a, b;
    clock_gettime(CLOCK_MONOTONIC, &a);
    for (int i = 0; i < ROUNDS; i++) { (void)!write(ab[1], &c, 1); (void)!read(ba[0], &c, 1); }
    clock_gettime(CLOCK_MONOTONIC, &b);
    double ns = ((b.tv_sec - a.tv_sec) * 1e9 + (b.tv_nsec - a.tv_nsec)) / (2.0 * ROUNDS);
    printf("%d round trips: %.2f us per switch (including the pipe system calls)\n",
           ROUNDS, ns / 1000);
    return 0;
}
