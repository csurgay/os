/* majfault.c - page faults that need the disk: map a file into memory and
 * read one byte of every page. If the file is not in the page cache, each
 * fault must wait for the disk (a major fault); if it is, the page is just
 * mapped (a minor fault).  Usage: ./majfault FILE                            */
#include <fcntl.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

int main(int argc, char **argv) {
    int fd = open(argv[1], O_RDONLY);
    struct stat st; fstat(fd, &st);
    char *p = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    madvise(p, st.st_size, MADV_RANDOM);                /* no read-ahead: one page per fault */
    struct rusage u0, u1; struct timespec a, b;
    getrusage(RUSAGE_SELF, &u0); clock_gettime(CLOCK_MONOTONIC, &a);
    long sum = 0;
    for (off_t i = 0; i < st.st_size; i += 4096) sum += p[i];
    clock_gettime(CLOCK_MONOTONIC, &b); getrusage(RUSAGE_SELF, &u1);
    double ms = ((b.tv_sec - a.tv_sec) * 1e9 + (b.tv_nsec - a.tv_nsec)) / 1e6;
    long maj = u1.ru_majflt - u0.ru_majflt, min = u1.ru_minflt - u0.ru_minflt;
    printf("%ld pages: %ld major + %ld minor faults, %.0f ms (%.1f us per page)\n",
           (long)(st.st_size / 4096), maj, min, ms, ms * 1000 / (st.st_size / 4096));
    return sum == 42;
}
