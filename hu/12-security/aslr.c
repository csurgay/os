/* aslr.c - print where the parts of this process were placed in memory.
 * Run it several times: with ASLR the addresses change at every start.
 *   gcc -O2 -o aslr aslr.c            (PIE, the default on Ubuntu)
 *   gcc -O2 -no-pie -o aslr-nopie aslr.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

int global = 1;                                   /* data segment of the program */

int main(void) {
    int local = 2;                                /* on the stack */
    void *heap = malloc(16);                      /* small block: from the heap (brk) */
    void *map = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    printf("main   (code)  %p\n", (void *)main);
    printf("global (data)  %p\n", (void *)&global);
    printf("heap           %p\n", heap);
    printf("mmap           %p\n", map);
    printf("libc   (puts)  %p\n", (void *)puts);
    printf("stack  (local) %p\n", (void *)&local);
    return 0;
}
