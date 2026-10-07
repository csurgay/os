#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    printf("user mode: trying a privileged instruction...\n");
    fflush(stdout);
    if (argc > 1 && strcmp(argv[1], "hlt") == 0)
        __asm__ volatile ("hlt");   /* stop the CPU until the next interrupt */
    else
        __asm__ volatile ("cli");   /* switch off interrupts */
    printf("this line is never printed\n");
    return 0;
}
