/* vm.c - two processes, the same virtual address, two different values */
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>

int x = 1;

int main(void) {
    pid_t pid = fork();                 /* make a copy of this process */
    if (pid == 0) {                     /* the copy (child) */
        x = 2;
        printf("child  (pid %d): &x = %p, x = %d\n", getpid(), (void *)&x, x);
        return 0;
    }
    wait(NULL);                         /* the original (parent) waits for the child */
    printf("parent (pid %d): &x = %p, x = %d\n", getpid(), (void *)&x, x);
    return 0;
}
