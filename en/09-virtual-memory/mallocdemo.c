/* mallocdemo.c: where does malloc get its memory from?
 * Run under strace to see the system calls behind each step:
 *   strace -e trace=brk,mmap,munmap,write ./mallocdemo
 * Each step prints a marker line first, so the system calls that follow
 * belong to that step.
 */
#include <malloc.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void *volatile sink;                 /* keeps the compiler from removing malloc/free pairs */

/* a write() marks the step in the strace output */
static void step(const char *s)
{
    if (write(1, s, strlen(s)) < 0)
        exit(1);
}

static long rss_kib(void)
{
    FILE *f = fopen("/proc/self/statm", "r");
    long size, res;
    if (fscanf(f, "%ld %ld", &size, &res) != 2)
        res = 0;
    fclose(f);
    return res * (sysconf(_SC_PAGESIZE) / 1024);
}

static void *worker(void *arg)
{
    (void)arg;
    sink = malloc(100);              /* first malloc in a new thread: a new arena */
    free(sink);
    return NULL;
}

int main(void)
{
    enum { N = 100000 };
    static void *small[N];

    step("--- 1. 1000 small blocks of 100 bytes\n");
    for (int i = 0; i < 1000; i++)
        small[i] = malloc(100);

    step("--- 2. one large block of 1 MiB\n");
    void *big = malloc(1 << 20);
    memset(big, 1, 1 << 20);

    step("--- 3. free the large block\n");
    free(big);

    step("--- 4. the same 1 MiB again\n");
    sink = malloc(1 << 20);
    free(sink);

    step("--- 5. a second thread calls malloc\n");
    pthread_t t;
    pthread_create(&t, NULL, worker, NULL);
    pthread_join(t, NULL);

    step("--- 6. 100000 small blocks, then free all but the last one\n");
    for (int i = 1000; i < N; i++)
        small[i] = malloc(100);
    for (int i = 0; i < N; i++)
        memset(small[i], 1, 100);
    long before = rss_kib();
    for (int i = 0; i < N - 1; i++)
        free(small[i]);
    long after = rss_kib();
    malloc_trim(0);
    long trimmed = rss_kib();
    char buf[200];
    snprintf(buf, sizeof buf,
             "resident: %ld KiB with all blocks, %ld KiB after free, %ld KiB after malloc_trim\n",
             before, after, trimmed);
    step(buf);
    free(small[N - 1]);
    return 0;
}
