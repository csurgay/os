/* ipcbench.c: latency and throughput of four IPC mechanisms between a parent
 * and a child process: a pipe, a Unix domain socket, a POSIX message queue
 * and POSIX shared memory (synchronised with process-shared semaphores, or,
 * for latency only, by spinning on an atomic flag). For throughput the pipe is
 * also tried with a 1 MiB buffer, and shared memory is a ring of 4 x 64 KiB.
 * Usage: ./ipcbench [same|split]  -- pin parent and child to the same CPU
 * (0) or to different CPUs (0 and 1); without an argument the scheduler decides.
 * Latency: 100,000 round trips of 1 byte. Throughput: 1 GiB in 64 KiB pieces;
 * the receiver copies every piece into its own buffer.
 * Build: gcc -O2 -pthread -o ipcbench ipcbench.c */
#define _GNU_SOURCE
#include <fcntl.h>
#include <mqueue.h>
#include <sched.h>
#include <semaphore.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define ROUNDS 100000
#define CHUNK  (64 * 1024)
#define TOTAL  (1L << 30)
#define NSLOT  4              /* shared-memory ring: 4 x 64 KiB */

static int child_cpu = -1;          /* set by the "same" and "split" arguments */

static void pin(int cpu)
{
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    sched_setaffinity(0, sizeof set, &set);
}

/* fork() that also pins the child, if asked */
static pid_t xfork(void)
{
    pid_t p = fork();
    if (p == 0 && child_cpu >= 0) pin(child_cpu);
    return p;
}

static double now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static void xread(int fd, char *b, size_t n)        /* read exactly n bytes */
{
    while (n) { ssize_t r = read(fd, b, n); if (r <= 0) exit(1); b += r; n -= r; }
}
static void xwrite(int fd, const char *b, size_t n)
{
    while (n) { ssize_t r = write(fd, b, n); if (r <= 0) exit(1); b += r; n -= r; }
}

/* ---------- byte streams: pipe and Unix socket ---------- */
static void stream_latency(const char *name, int pw, int pr, int cr, int cw)
{
    /* the parent writes pw and reads pr; the child reads cr and writes cw */
    char c = 'x';
    if (xfork() == 0) {
        for (int i = 0; i < ROUNDS; i++) { xread(cr, &c, 1); xwrite(cw, &c, 1); }
        _exit(0);
    }
    double t0 = now();
    for (int i = 0; i < ROUNDS; i++) { xwrite(pw, &c, 1); xread(pr, &c, 1); }
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f us per round trip\n", name, t / ROUNDS * 1e6);
}

static void stream_throughput(const char *name, int wfd, int rfd)
{
    char *buf = malloc(CHUNK), *rbuf = malloc(CHUNK);
    memset(buf, 7, CHUNK);
    if (xfork() == 0) {
        for (long s = 0; s < TOTAL; s += CHUNK) xwrite(wfd, buf, CHUNK);
        _exit(0);
    }
    double t0 = now();
    for (long s = 0; s < TOTAL; s += CHUNK) xread(rfd, rbuf, CHUNK);
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f GB/s\n", name, TOTAL / t / 1e9);
    free(buf); free(rbuf);
}

/* ---------- POSIX message queue ---------- */
static mqd_t mq_new(const char *nm, long msgsize)
{
    struct mq_attr at = { .mq_maxmsg = 8, .mq_msgsize = msgsize };
    mq_unlink(nm);
    mqd_t q = mq_open(nm, O_CREAT | O_RDWR, 0600, &at);
    if (q == (mqd_t)-1) { perror("mq_open"); exit(1); }
    return q;
}

static void mq_latency(void)
{
    mqd_t q1 = mq_new("/ipcb1", 8), q2 = mq_new("/ipcb2", 8);
    char c[8] = "x";
    if (xfork() == 0) {
        for (int i = 0; i < ROUNDS; i++) { mq_receive(q1, c, 8, NULL); mq_send(q2, c, 1, 0); }
        _exit(0);
    }
    double t0 = now();
    for (int i = 0; i < ROUNDS; i++) { mq_send(q1, c, 1, 0); mq_receive(q2, c, 8, NULL); }
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f us per round trip\n", "message queue", t / ROUNDS * 1e6);
    mq_unlink("/ipcb1"); mq_unlink("/ipcb2");
}

static void mq_throughput(void)
{
    long sz = 8192;                 /* the default maximum message size (msgsize_max) */
    mqd_t q = mq_new("/ipcb3", sz);
    char *buf = malloc(sz), *rbuf = malloc(sz);
    memset(buf, 7, sz);
    if (xfork() == 0) {
        for (long s = 0; s < TOTAL; s += sz) mq_send(q, buf, sz, 0);
        _exit(0);
    }
    double t0 = now();
    for (long s = 0; s < TOTAL; s += sz) mq_receive(q, rbuf, sz, NULL);
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f GB/s (8 KiB messages)\n", "message queue", TOTAL / t / 1e9);
    mq_unlink("/ipcb3");
}

/* ---------- POSIX shared memory ---------- */
struct shm {
    sem_t full[NSLOT], empty[NSLOT];  /* process-shared semaphores, one pair per slot */
    atomic_int turn;                /* for the spinning ping-pong */
    char slot[NSLOT][CHUNK];        /* a ring of buffers */
};

static struct shm *shm_new(void)
{
    int fd = shm_open("/ipcbench", O_CREAT | O_RDWR, 0600);
    if (fd < 0 || ftruncate(fd, sizeof(struct shm)) < 0) { perror("shm"); exit(1); }
    struct shm *s = mmap(NULL, sizeof *s, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    shm_unlink("/ipcbench");        /* the name goes, the mapping stays */
    for (int i = 0; i < NSLOT; i++) { sem_init(&s->full[i], 1, 0); sem_init(&s->empty[i], 1, 1); }
    atomic_store(&s->turn, 0);
    return s;
}

static void shm_latency_sem(struct shm *s)
{
    /* full[0]: parent -> child, full[1]: child -> parent */
    if (xfork() == 0) {
        for (int i = 0; i < ROUNDS; i++) { sem_wait(&s->full[0]); s->slot[1][0] = s->slot[0][0]; sem_post(&s->full[1]); }
        _exit(0);
    }
    double t0 = now();
    for (int i = 0; i < ROUNDS; i++) { s->slot[0][0] = 'x'; sem_post(&s->full[0]); sem_wait(&s->full[1]); }
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f us per round trip\n", "shared memory + semaphores", t / ROUNDS * 1e6);
}

static void shm_latency_spin(struct shm *s)
{
    if (xfork() == 0) {
        for (int i = 0; i < ROUNDS; i++) {
            while (atomic_load(&s->turn) != 1) ;     /* busy-wait for the parent */
            atomic_store(&s->turn, 0);
        }
        _exit(0);
    }
    double t0 = now();
    for (int i = 0; i < ROUNDS; i++) {
        atomic_store(&s->turn, 1);
        while (atomic_load(&s->turn) != 0) ;         /* busy-wait for the child */
    }
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f us per round trip\n", "shared memory, spinning", t / ROUNDS * 1e6);
}

static void shm_throughput(struct shm *s)
{
    for (int i = 0; i < NSLOT; i++) { sem_init(&s->full[i], 1, 0); sem_init(&s->empty[i], 1, 1); }
    char *buf = malloc(CHUNK), *rbuf = malloc(CHUNK);
    memset(buf, 7, CHUNK);
    if (xfork() == 0) {
        int k = 0;
        for (long n = 0; n < TOTAL; n += CHUNK, k = (k + 1) % NSLOT) {
            sem_wait(&s->empty[k]); memcpy(s->slot[k], buf, CHUNK); sem_post(&s->full[k]);
        }
        _exit(0);
    }
    double t0 = now();
    int k = 0;
    for (long n = 0; n < TOTAL; n += CHUNK, k = (k + 1) % NSLOT) {
        sem_wait(&s->full[k]); memcpy(rbuf, s->slot[k], CHUNK); sem_post(&s->empty[k]);
    }
    double t = now() - t0;
    wait(NULL);
    printf("%-28s %8.2f GB/s\n", "shared memory + semaphores", TOTAL / t / 1e9);
}

int main(int argc, char **argv)
{
    int a[2], b[2];
    if (argc > 1) {                     /* parent on CPU 0, child on CPU 0 or CPU 1 */
        pin(0);
        child_cpu = strcmp(argv[1], "split") == 0 ? 1 : 0;
        printf("parent on CPU 0, child on CPU %d\n", child_cpu);
    }
    printf("latency (1 byte there and back, %d times):\n", ROUNDS);
    if (pipe(a) < 0 || pipe(b) < 0) return 1;
    stream_latency("pipe", a[1], b[0], a[0], b[1]);     /* two pipes, one per direction */
    close(a[0]); close(a[1]); close(b[0]); close(b[1]);
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, a) < 0) return 1;
    stream_latency("Unix domain socket", a[0], a[0], a[1], a[1]);   /* one two-way pair */
    close(a[0]); close(a[1]);
    mq_latency();
    struct shm *s = shm_new();
    shm_latency_sem(s);
    cpu_set_t cpus;
    sched_getaffinity(0, sizeof cpus, &cpus);
    if (child_cpu == 1 || (child_cpu < 0 && CPU_COUNT(&cpus) > 1))  /* not on one core */
        shm_latency_spin(s);
    else
        printf("%-28s (skipped: both on one CPU)\n", "shared memory, spinning");

    printf("throughput (1 GiB, 64 KiB per write):\n");
    if (pipe(a) < 0) return 1;
    stream_throughput("pipe (64 KiB buffer)", a[1], a[0]);
    fcntl(a[1], F_SETPIPE_SZ, 1 << 20);
    stream_throughput("pipe (1 MiB buffer)", a[1], a[0]);
    close(a[0]); close(a[1]);
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, a) < 0) return 1;
    stream_throughput("Unix domain socket", a[1], a[0]);
    close(a[0]); close(a[1]);
    mq_throughput();
    shm_throughput(s);
    return 0;
}
