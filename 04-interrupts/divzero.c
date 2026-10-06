#include <stdio.h>

int main(void) {
    volatile int a = 1, b = 0;     /* volatile: stop the compiler from folding 1/0 */
    printf("about to divide...\n");
    fflush(stdout);
    printf("result = %d\n", a / b); /* the CPU raises a divide-error exception */
    return 0;
}
