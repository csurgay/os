#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(int argc, char **argv) {
    /* x86-64 machine code for:  mov $5, %eax ; ret */
    unsigned char code[] = { 0xb8, 0x05, 0x00, 0x00, 0x00, 0xc3 };

    if (argc > 1) {                       /* "./nx fix": copy to a page we make executable */
        long pg = sysconf(_SC_PAGESIZE);
        unsigned char *p = mmap(NULL, pg, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        memcpy(p, code, sizeof code);
        mprotect(p, pg, PROT_READ | PROT_EXEC);   /* W^X: drop write, add exec */
        printf("result = %d\n", ((int (*)(void))p)());
    } else {                              /* "./nx": run the bytes where they are (stack) */
        printf("result = %d\n", ((int (*)(void))code)());
    }
    return 0;
}
