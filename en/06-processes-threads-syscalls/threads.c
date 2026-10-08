/* threads.c: what do the threads of one process share, and what is their own?
 * Three threads each add to a global counter (shared, protected by a mutex),
 * to a thread-local counter (__thread: one copy per thread) and to a local
 * variable on their own stack, then print their IDs and addresses.
 * Build: gcc -O2 -pthread -o threads threads.c */
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

int shared = 0;                       /* one copy for the whole process */
__thread int mine = 0;                /* one copy per thread (TLS)       */
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;

static void *worker(void *arg)
{
    long id = (long)arg;
    int local = 0;                    /* on this thread's own stack */
    for (int i = 0; i < 1000; i++) {
        pthread_mutex_lock(&m);
        shared++;
        pthread_mutex_unlock(&m);
        mine++;
        local++;
    }
    pthread_mutex_lock(&m);
    printf("thread %ld: pid %d tid %d  &shared %p  &mine %p  &local %p  mine = %d\n",
           id, getpid(), gettid(), (void *)&shared, (void *)&mine, (void *)&local, mine);
    pthread_mutex_unlock(&m);
    return NULL;
}

int main(void)
{
    pthread_t t[3];
    for (long i = 0; i < 3; i++)
        pthread_create(&t[i], NULL, worker, (void *)i);
    for (int i = 0; i < 3; i++)
        pthread_join(t[i], NULL);
    printf("main    : pid %d tid %d  shared = %d, main's own mine = %d\n",
           getpid(), gettid(), shared, mine);
    return 0;
}
