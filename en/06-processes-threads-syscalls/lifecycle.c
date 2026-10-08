/* lifecycle.c: fork, exec, exit and wait.
 * The parent starts three children: one exits with status 3, one runs
 * another program with execv(), one dies of a signal (a null-pointer write).
 * The parent collects each one with waitpid() and decodes the status.
 * Build: gcc -O2 -o lifecycle lifecycle.c */
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int x = 100;                    /* each child gets its own copy */
    pid_t kids[3];

    printf("parent: pid %d, x = %d\n", getpid(), x);
    fflush(stdout);                 /* otherwise the buffer would be copied too */

    for (int k = 0; k < 3; k++) {
        pid_t pid = fork();         /* returns twice: 0 in the child, the child's PID in the parent */
        if (pid < 0) { perror("fork"); exit(1); }
        if (pid == 0) {             /* ---- child ---- */
            x += k + 1;
            printf("child %d: pid %d, parent %d, x = %d\n", k, getpid(), getppid(), x);
            fflush(stdout);
            if (k == 0)
                exit(3);                                    /* normal exit with status 3 */
            if (k == 1) {
                char *argv[] = { "sh", "-c",
                    "echo \"child 1: now I am /bin/sh, pid $$, parent $PPID\"", NULL };
                execv("/bin/sh", argv);                     /* returns only on error */
                perror("execv");
                exit(127);
            }
            *(volatile int *)0 = 1;                         /* k == 2: SIGSEGV */
        }
        kids[k] = pid;
    }

    for (int k = 0; k < 3; k++) {
        int status;
        pid_t pid = waitpid(kids[k], &status, 0);
        if (WIFEXITED(status))
            printf("parent: child %d exited, status %d\n", pid, WEXITSTATUS(status));
        else if (WIFSIGNALED(status))
            printf("parent: child %d killed by signal %d (%s)\n", pid,
                   WTERMSIG(status), strsignal(WTERMSIG(status)));
    }
    printf("parent: x is still %d\n", x);
    return 0;
}
