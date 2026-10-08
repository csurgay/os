/* spawn1.c: start /bin/true with posix_spawn() and wait for it.
 * Run it under strace to see which clone flags glibc uses.
 * Build: gcc -O2 -o spawn1 spawn1.c */
#include <spawn.h>
#include <stdio.h>
#include <sys/wait.h>

extern char **environ;

int main(void)
{
    pid_t pid;
    char *argv[] = { "true", NULL };
    if (posix_spawn(&pid, "/bin/true", NULL, NULL, argv, environ) != 0) {
        perror("posix_spawn");
        return 1;
    }
    waitpid(pid, NULL, 0);
    return 0;
}
