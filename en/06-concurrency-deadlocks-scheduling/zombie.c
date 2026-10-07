/* zombie.c - a parent that does not collect its child's exit status (yet).
 * The child exits at once and stays a zombie until the parent calls wait().  */
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    pid_t child = fork();                 /* duplicate this process            */
    if (child == 0)
        exit(42);                         /* child: finish at once, status 42  */
    printf("parent %d: child %d has exited; sleeping 10 s without wait()\n",
           getpid(), child);
    fflush(stdout);
    sleep(10);                            /* the child is a zombie meanwhile   */
    int status;
    waitpid(child, &status, 0);           /* reap: collect the exit status     */
    printf("parent: reaped child %d, exit status %d\n", child, WEXITSTATUS(status));
    fflush(stdout);
    sleep(5);                             /* now the zombie is gone            */
    return 0;
}
