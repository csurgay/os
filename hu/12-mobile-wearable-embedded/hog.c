/* hog.c - burn CPU for the given number of seconds (default 30). */
#include <stdlib.h>
#include <time.h>
int main(int argc, char **argv) {
    time_t end = time(NULL) + (argc > 1 ? atoi(argv[1]) : 30);
    volatile unsigned long x = 0;
    while (time(NULL) < end) for (int i = 0; i < 1000000; i++) x += i;
    return 0;
}
