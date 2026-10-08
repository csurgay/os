/* overflow.c - a function that copies its argument into a 16-byte buffer
 * without checking the length: the classic stack buffer overflow bug.
 * The demo only shows how the bug is DETECTED; it does not exploit it.
 *   gcc -O0 -g -fno-stack-protector  -o overflow-plain  overflow.c
 *   gcc -O0 -g -fstack-protector-strong -o overflow-canary overflow.c
 */
#include <stdio.h>
#include <string.h>

static void greet(const char *name) {
    char buf[16];
    strcpy(buf, name);                  /* BUG: no check that name fits in buf */
    printf("hello, %s\n", buf);
}

int main(int argc, char **argv) {
    greet(argc > 1 ? argv[1] : "world");
    puts("greet() returned normally");
    return 0;
}
