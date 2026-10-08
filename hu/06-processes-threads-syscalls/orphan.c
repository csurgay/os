/* orphan.c: what happens to a child whose parent dies?
 * A "grandparent" forks a parent, which forks a child and exits at once.
 * The child prints its parent PID before and after. Without arguments the
 * orphan is adopted by PID 1; with "subreaper" the grandparent first declares
 * itself a child subreaper (prctl), and adopts its orphaned descendants.
 * Build: gcc -O2 -o orphan orphan.c */
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "subreaper") == 0)
        prctl(PR_SET_CHILD_SUBREAPER, 1);
    printf("grandparent %d\n", getpid());
    fflush(stdout);

    if (fork() == 0) {                       /* parent */
        if (fork() == 0) {                   /* child */
            printf("child %d: my parent is %d\n", getpid(), getppid());
            fflush(stdout);
            sleep(2);                        /* meanwhile the parent exits */
            printf("child %d: my parent is %d\n", getpid(), getppid());
            return 0;
        }
        sleep(1);
        printf("parent %d: exiting without waiting\n", getpid());
        return 0;
    }
    wait(NULL);                              /* reap the parent */
    sleep(2);
    int status;
    pid_t p = waitpid(-1, &status, WNOHANG); /* an adopted child is our child now */
    printf("grandparent: waitpid(-1) returned %d\n", p);
    return 0;
}
