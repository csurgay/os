/* fortify.c - the same unchecked strcpy as overflow.c, in main().
 * With optimisation and _FORTIFY_SOURCE the compiler knows that buf has
 * 16 bytes and calls a checking version of strcpy instead.
 *   gcc -O2 -o fortify fortify.c                       (Ubuntu: fortify on by default)
 *   gcc -O2 -U_FORTIFY_SOURCE -o fortify-off fortify.c
 */
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    char buf[16];
    strcpy(buf, argc > 1 ? argv[1] : "short");     /* BUG: unchecked length */
    printf("copied: %s\n", buf);
    return 0;
}
