/* cow.c - copy-on-write after fork(): parent and child see the SAME virtual
 * address; until one of them writes, it is even the same physical frame.   */
#define NO_MAIN
#include "v2p.c"
#include <stdlib.h>
#include <sys/wait.h>

int main(void) {
    long ps = sysconf(_SC_PAGESIZE);
    int *x = mmap(NULL, ps, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    *x = 1;
    printf("parent: x at %p = %d, frame %#lx\n", (void *)x, *x, frame_of(x));
    fflush(stdout);
    if (fork() == 0) {
        printf("child : x at %p = %d, frame %#lx (shared, read-only for now)\n", (void *)x, *x, frame_of(x));
        *x = 2;                                         /* write -> page fault -> private copy */
        printf("child : x at %p = %d, frame %#lx (after writing: its own copy)\n", (void *)x, *x, frame_of(x));
        exit(0);
    }
    wait(NULL);
    printf("parent: x at %p = %d, frame %#lx (unchanged)\n", (void *)x, *x, frame_of(x));
    return 0;
}
