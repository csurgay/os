/* bridge.c - a one-lane bridge, seen as two halves (west and east).
 * A car going east needs the west half, then the east half; a car going west
 * needs them in the opposite order. Each half is a mutex.
 * Usage: ./bridge naive|stuck|ordered|semaphore [cars-per-direction]
 *   naive      take your near half, then the far half      -> can deadlock;
 *              a car that waits 2 s for the far half backs off (recovery)
 *   stuck      the same without the time-out: a real, permanent deadlock
 *   ordered    always take the west half first               (breaks circular wait)
 *   semaphore  a signal lets one car onto the bridge at a time (the bridge is
 *              one resource)                                                   */
#include <errno.h>
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

pthread_mutex_t half[2] = {PTHREAD_MUTEX_INITIALIZER, PTHREAD_MUTEX_INITIALIZER};
enum { WEST = 0, EAST = 1 };
sem_t signal_light;                     /* semaphore mode: 1 car on the bridge */
const char *mode;
int crossings = 0, deadlocks = 0;
pthread_mutex_t stats = PTHREAD_MUTEX_INITIALIZER;

static int take(int h) {               /* lock one half, give up after 2 s     */
    struct timespec t;
    clock_gettime(CLOCK_REALTIME, &t);
    t.tv_sec += 2;
    return pthread_mutex_timedlock(&half[h], &t);
}

static void *car(void *arg) {
    int dir = *(int *)arg;              /* WEST: going east (enters at west) */
    int first = dir, second = 1 - dir;
    if (!strcmp(mode, "ordered")) { first = WEST; second = EAST; }
    if (!strcmp(mode, "semaphore")) sem_wait(&signal_light);   /* P(): wait for green */
    pthread_mutex_lock(&half[first]);   /* enter the near half                 */
    usleep(1000);                       /* drive onto the bridge: 1 ms         */
    int r = !strcmp(mode, "stuck") ? pthread_mutex_lock(&half[second])  /* wait forever */
                                   : take(second);                      /* wait 2 s     */
    if (r == ETIMEDOUT) {               /* the far half never became free      */
        pthread_mutex_lock(&stats); deadlocks++; pthread_mutex_unlock(&stats);
        pthread_mutex_unlock(&half[first]);   /* back off (a recovery!)        */
    } else if (r == 0) {
        pthread_mutex_lock(&stats); crossings++; pthread_mutex_unlock(&stats);
        pthread_mutex_unlock(&half[second]);
        pthread_mutex_unlock(&half[first]);
    }
    if (!strcmp(mode, "semaphore")) sem_post(&signal_light);   /* V(): green again */
    return NULL;
}

int main(int argc, char **argv) {
    mode = argc > 1 ? argv[1] : "naive";
    int n = argc > 2 ? atoi(argv[2]) : 1;
    sem_init(&signal_light, 0, 1);
    pthread_t t[2 * n]; int dir[2] = {WEST, EAST};
    for (int i = 0; i < n; i++) {
        pthread_create(&t[2 * i], NULL, car, &dir[0]);
        pthread_create(&t[2 * i + 1], NULL, car, &dir[1]);
    }
    for (int i = 0; i < 2 * n; i++) pthread_join(t[i], NULL);
    printf("%-9s %3d cars: %3d crossed, %3d stuck in a deadlock (gave up after 2 s)\n",
           mode, 2 * n, crossings, deadlocks);
    return 0;
}
