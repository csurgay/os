/* hold.c: take N MiB of anonymous memory, touch every page, and keep it
 * until the program receives a signal (Ctrl-C, or kill). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    size_t mib = argc > 1 ? strtoul(argv[1], NULL, 10) : 1024;
    size_t len = mib << 20;
    char *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    memset(p, 1, len);               /* every page now needs a physical frame */
    printf("holding %zu MiB\n", mib);
    fflush(stdout);
    pause();
    return 0;
}
