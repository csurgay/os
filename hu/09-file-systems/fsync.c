/* fsync.c - the price of durability: write N small files, with and without fsync
 * usage: ./fsync DIR [sync]     (creates DIR/f0 ... DIR/f999, 4 KiB each)      */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

int main(int argc, char **argv)
{
    if (argc < 2) { fprintf(stderr, "usage: %s DIR [sync]\n", argv[0]); return 1; }
    int dosync = argc > 2 && strcmp(argv[2], "sync") == 0;
    char buf[4096], name[4096];
    memset(buf, 'x', sizeof buf);
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < 1000; i++) {
        snprintf(name, sizeof name, "%s/f%d", argv[1], i);
        int fd = open(name, O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd < 0 || write(fd, buf, sizeof buf) != sizeof buf) { perror(name); return 1; }
        if (dosync && fsync(fd) != 0) { perror("fsync"); return 1; }
        close(fd);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms = (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
    printf("1000 files of 4 KiB %s: %.0f ms (%.0f us per file)\n",
           dosync ? "with fsync   " : "without fsync", ms, ms);
    return 0;
}
