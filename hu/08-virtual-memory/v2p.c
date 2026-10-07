/* v2p.c - where do my pages really live? Allocates 6 virtual pages that are
 * contiguous in the process's address space, touches 4 of them, and asks the
 * kernel (/proc/self/pagemap) which physical frame holds each one.
 * Needs root (CAP_SYS_ADMIN) to see frame numbers; others see frame 0.      */
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/mman.h>
#include <unistd.h>

/* physical frame of the page containing va, or -1 if not present */
long frame_of(void *va) {
    long ps = sysconf(_SC_PAGESIZE);
    uint64_t e = 0;
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0 || pread(fd, &e, 8, ((uintptr_t)va / ps) * 8) != 8) e = 0;  /* 8 bytes per page */
    if (fd >= 0) close(fd);
    if (!((e >> 63) & 1)) return -1;                   /* bit 63: page present in RAM */
    return (long)(e & ((1ULL << 55) - 1));             /* bits 0-54: frame number     */
}

#ifndef NO_MAIN
int main(void) {
    long ps = sysconf(_SC_PAGESIZE);
    char *p = mmap(NULL, 6 * ps, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    for (int i = 0; i < 4; i++) p[i * ps] = 1;         /* touch pages 0..3 only */
    printf("page size %ld bytes\n", ps);
    for (int i = 0; i < 6; i++) {
        long f = frame_of(p + i * ps);
        if (f >= 0)
            printf("virtual page %#lx -> physical frame %#lx\n", (unsigned long)((uintptr_t)(p + i * ps) / ps), f);
        else
            printf("virtual page %#lx -> not in RAM (never touched)\n", (unsigned long)((uintptr_t)(p + i * ps) / ps));
    }
    return 0;
}
#endif
