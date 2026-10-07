/* peterson.c - Peterson's mutual exclusion algorithm (1981), with and without
 * a memory fence. Two threads each enter the critical section N times; inside,
 * each writes its id into `owner` and checks that it is still there (if not,
 * the other thread was inside at the same time: a violation).
 * Usage: ./peterson [fence]                                                    */
#include <pthread.h>
#include <stdio.h>
#include <string.h>

#ifndef N
#define N 10000000
#endif
volatile int flag[2] = {0, 0};   /* flag[i] = 1: thread i wants to enter */
volatile int turn = 0;           /* whose turn it is to wait             */
volatile int owner = -1;         /* who is in the critical section       */
long violations = 0, entries[2];
int use_fence = 0;

static void lock(int i) {
    int j = 1 - i;
    flag[i] = 1;                 /* I want to enter ...                   */
    turn = j;                    /* ... but you go first if you want too  */
    if (use_fence)
        __atomic_thread_fence(__ATOMIC_SEQ_CST);   /* gcc: lock or $0,(%rsp) */
    while (flag[j] && turn == j)
        ;                        /* busy-wait                             */
}
static void unlock(int i) { flag[i] = 0; }

static void *worker(void *arg) {
    int i = *(int *)arg;
    for (long k = 0; k < N; k++) {
        lock(i);
        owner = i;               /* critical section: I am in here ...    */
        entries[i]++;
        if (owner != i)          /* ... unless the other one came in too  */
            __atomic_fetch_add(&violations, 1, __ATOMIC_RELAXED);
        unlock(i);
    }
    return NULL;
}

int main(int argc, char **argv) {
    use_fence = (argc > 1 && strcmp(argv[1], "fence") == 0);
    pthread_t t[2]; int id[2] = {0, 1};
    for (int i = 0; i < 2; i++) pthread_create(&t[i], NULL, worker, &id[i]);
    for (int i = 0; i < 2; i++) pthread_join(t[i], NULL);
    printf("%s: %ld entries, %ld times both threads were inside\n",
           use_fence ? "with fence   " : "without fence", entries[0] + entries[1], violations);
    return 0;
}
