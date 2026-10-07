/* pagefault.c: touch every page of a file mapped into memory and count the
   page faults. If the file is not in the page cache, every fault needs a disk
   read: page fault (exception) -> the kernel starts the disk transfer (DMA) ->
   another task may run -> the disk raises an interrupt -> the process resumes.

   usage: ./pagefault FILE [readahead]
   Without "readahead", read-ahead is switched off (MADV_RANDOM), so every
   first touch of a page is a separate fault and a separate disk read.        */
#include <fcntl.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s FILE [readahead]\n", argv[0]); return 1; }
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    struct stat st;
    fstat(fd, &st);
    long pg = sysconf(_SC_PAGESIZE), pages = st.st_size / pg;

    volatile unsigned char *p = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    if (argc < 3)                                  /* no read-ahead: one fault = one page */
        madvise((void *)p, st.st_size, MADV_RANDOM);

    struct rusage r0, r1;
    struct timespec t0, t1;
    getrusage(RUSAGE_SELF, &r0);
    clock_gettime(CLOCK_MONOTONIC, &t0);
    unsigned long sum = 0;
    for (long i = 0; i < pages; i++)
        sum += p[i * pg];                          /* first touch of each page */
    clock_gettime(CLOCK_MONOTONIC, &t1);
    getrusage(RUSAGE_SELF, &r1);

    double ms = (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
    printf("%ld pages touched in %.1f ms (checksum %lu)\n", pages, ms, sum);
    printf("major faults (needed the disk): %ld\n", r1.ru_majflt - r0.ru_majflt);
    printf("minor faults (page already in memory): %ld\n", r1.ru_minflt - r0.ru_minflt);
    return 0;
}
