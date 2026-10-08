/* uaf.c - two heap bugs: use after free and double free.
 *   gcc -O0 -g -o uaf uaf.c                          (plain build)
 *   gcc -O0 -g -fsanitize=address -o uaf-asan uaf.c  (AddressSanitizer)
 *   ./uaf use     reads a block after free()
 *   ./uaf double  frees the same block twice
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    char *p = malloc(32);
    strcpy(p, "secret");
    free(p);
    if (argc > 1 && strcmp(argv[1], "use") == 0) {
        char *q = malloc(32);                  /* likely gets the same block */
        strcpy(q, "other data");
        printf("p = %p, q = %p, p[0] = '%c'\n", (void *)p, (void *)q, p[0]);  /* BUG */
    } else if (argc > 1 && strcmp(argv[1], "double") == 0) {
        free(p);                               /* BUG: second free */
        puts("double free went unnoticed");
    }
    return 0;
}
