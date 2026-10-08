/* traverse_one.c - only one loop order, for cachegrind: ./traverse_one row|col N */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    int col = argc > 1 && strcmp(argv[1], "col") == 0;
    int n = argc > 2 ? atoi(argv[2]) : 1024;
    int (*a)[n] = malloc(sizeof(int[n][n]));
    for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) a[i][j] = i + j;
    long sum = 0;
    if (!col) { for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) sum += a[i][j]; }
    else      { for (int j = 0; j < n; j++) for (int i = 0; i < n; i++) sum += a[i][j]; }
    printf("%ld\n", sum);
    return 0;
}
