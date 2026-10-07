/* seqrand.c - sequential versus random reads from a storage device, bypassing the
 * page cache with O_DIRECT.  usage: ./seqrand FILE   (FILE should be 1 GiB or more) */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/stat.h>

static double now(void)
{
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

int main(int argc, char **argv)
{
    if (argc < 2) { fprintf(stderr, "usage: %s FILE\n", argv[0]); return 1; }
    int fd = open(argv[1], O_RDONLY | O_DIRECT);
    if (fd < 0) { perror(argv[1]); return 1; }
    struct stat st; fstat(fd, &st);
    long long size = st.st_size & ~((1LL << 20) - 1);
    void *buf;
    if (posix_memalign(&buf, 4096, 1 << 20)) return 1;

    /* sequential: the whole file in 1 MiB requests */
    double t = now();
    for (long long off = 0; off < size; off += 1 << 20)
        if (pread(fd, buf, 1 << 20, off) != 1 << 20) { perror("pread"); return 1; }
    t = now() - t;
    printf("sequential 1 MiB reads: %6.0f MB/s\n", size / t / 1e6);

    /* random: 4 KiB requests at random 4 KiB-aligned offsets, for 10 seconds */
    srandom(1);
    long n = 0; double t0 = now(), el;
    do {
        long long off = (random() % (size / 4096)) * 4096;
        if (pread(fd, buf, 4096, off) != 4096) { perror("pread"); return 1; }
        n++;
    } while ((el = now() - t0) < 10);
    printf("random 4 KiB reads:     %6.1f MB/s, %6.0f reads/s, %7.1f us per read\n",
           n * 4096.0 / el / 1e6, n / el, el / n * 1e6);
    return 0;
}
