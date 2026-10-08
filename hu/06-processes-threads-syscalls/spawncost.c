/* spawncost.c: how long does it take to create a thread, a process,
 * a process running a new program?
 * Usage: ./spawncost [MiB]   -- first allocate and touch MiB of memory,
 * to see how the parent's size changes the cost of fork().
 * Build: gcc -O2 -pthread -o spawncost spawncost.c */
#define _GNU_SOURCE
#include <pthread.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern char **environ;
static char *true_argv[] = { "true", NULL };

static double now_us(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e6 + t.tv_nsec / 1e3;
}

static void *nothing(void *arg) { return arg; }

static void report(const char *what, double t0, int n)
{
    printf("%-34s %9.1f us\n", what, (now_us() - t0) / n);
}

int main(int argc, char **argv)
{
    long mib = argc > 1 ? atol(argv[1]) : 0;
    if (mib) {
        char *p = malloc(mib << 20);
        memset(p, 1, mib << 20);        /* touch every page: real, mapped memory */
        printf("parent has touched %ld MiB\n", mib);
    }
    int n = 2000;
    double t0;

    t0 = now_us();
    for (int i = 0; i < n; i++) {
        pthread_t t;
        pthread_create(&t, NULL, nothing, NULL);
        pthread_join(t, NULL);
    }
    report("pthread_create + join", t0, n);

    t0 = now_us();
    for (int i = 0; i < n; i++) {
        pid_t p = fork();
        if (p == 0) _exit(0);
        waitpid(p, NULL, 0);
    }
    report("fork + _exit + wait", t0, n);

    t0 = now_us();
    for (int i = 0; i < n; i++) {
        pid_t p = vfork();
        if (p == 0) _exit(0);
        waitpid(p, NULL, 0);
    }
    report("vfork + _exit + wait", t0, n);

    n = 500;
    t0 = now_us();
    for (int i = 0; i < n; i++) {
        pid_t p = fork();
        if (p == 0) { execve("/bin/true", true_argv, environ); _exit(127); }
        waitpid(p, NULL, 0);
    }
    report("fork + exec /bin/true + wait", t0, n);

    t0 = now_us();
    for (int i = 0; i < n; i++) {
        pid_t p = vfork();
        if (p == 0) { execve("/bin/true", true_argv, environ); _exit(127); }
        waitpid(p, NULL, 0);
    }
    report("vfork + exec /bin/true + wait", t0, n);

    t0 = now_us();
    for (int i = 0; i < n; i++) {
        pid_t p;
        posix_spawn(&p, "/bin/true", NULL, NULL, true_argv, environ);
        waitpid(p, NULL, 0);
    }
    report("posix_spawn /bin/true + wait", t0, n);
    return 0;
}
