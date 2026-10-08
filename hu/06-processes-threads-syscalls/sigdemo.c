/* sigdemo.c: a signal interrupts a blocked system call.
 * The process blocks in read() on an empty pipe; a child writes into the
 * pipe after 2 s; an alarm signal arrives after 1 s. Its handler only does
 * async-signal-safe work (write() and setting a flag).
 * Without SA_RESTART the read() fails with EINTR; with "restart" the kernel
 * restarts it after the handler, and it returns the data.
 * Usage: ./sigdemo [restart]
 * Build: gcc -O2 -o sigdemo sigdemo.c */
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t got_alarm = 0;

static void on_alarm(int sig)
{
    (void)sig;
    got_alarm = 1;                                   /* only async-signal-safe */
    static const char msg[] = "  handler: SIGALRM arrived\n";
    if (write(1, msg, sizeof msg - 1) < 0) {}        /* write() is safe; printf() is not */
}

static double now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

int main(int argc, char **argv)
{
    int restart = argc > 1 && strcmp(argv[1], "restart") == 0;
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_alarm;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = restart ? SA_RESTART : 0;
    sigaction(SIGALRM, &sa, NULL);

    int p[2];
    if (pipe(p) < 0) return 1;
    if (fork() == 0) {                               /* child: data after 2 s */
        sleep(2);
        if (write(p[1], "data", 4) < 0) _exit(1);
        _exit(0);
    }
    printf("%s: read() from an empty pipe, alarm in 1 s, data in 2 s\n",
           restart ? "SA_RESTART" : "no SA_RESTART");
    fflush(stdout);
    alarm(1);
    double t0 = now();
    char buf[16];
    ssize_t n = read(p[0], buf, sizeof buf);
    int e = errno;
    printf("  read() returned %zd after %.1f s%s%s, got_alarm = %d\n", n, now() - t0,
           n < 0 ? ", errno = " : "", n < 0 ? strerror(e) : "", got_alarm);
    wait(NULL);
    return 0;
}
