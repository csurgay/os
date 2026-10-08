/* minish.c: a minimal Unix shell in about 100 lines.
 * Shows the process API at work: fork() a child per command, exec() the
 * program, wait() for it; open() + dup2() for < > >> redirections;
 * pipe() + dup2() for pipelines (cmd1 | cmd2 | ...). Built-ins: cd, exit.
 * No quoting, variables or job control: words are separated by blanks.
 * Build: gcc -O2 -o minish minish.c */
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAXW 64
#define MAXC 16

/* Run one command in the current (child) process: redirections, then exec. */
static void run(char **w)
{
    char *argv[MAXW];
    int n = 0;
    for (int i = 0; w[i]; i++) {
        int fd = -1, target = -1;
        if (w[i][0] == '<') {
            fd = open(w[i] + 1, O_RDONLY); target = 0;
        } else if (strncmp(w[i], ">>", 2) == 0) {
            fd = open(w[i] + 2, O_WRONLY | O_CREAT | O_APPEND, 0644); target = 1;
        } else if (w[i][0] == '>') {
            fd = open(w[i] + 1, O_WRONLY | O_CREAT | O_TRUNC, 0644); target = 1;
        } else {
            argv[n++] = w[i];
            continue;
        }
        if (fd < 0) { perror(w[i]); _exit(1); }
        dup2(fd, target);           /* make fd 0 or 1 refer to the file ... */
        close(fd);                  /* ... and drop the extra descriptor   */
    }
    argv[n] = NULL;
    if (n == 0) _exit(0);
    execvp(argv[0], argv);          /* searches PATH; returns only on error */
    fprintf(stderr, "minish: %s: %s\n", argv[0], strerror(errno));
    _exit(127);
}

int main(void)
{
    char line[1024];
    int tty = isatty(0);
    for (;;) {
        fputs("minish$ ", stdout);
        fflush(stdout);
        if (!fgets(line, sizeof line, stdin)) break;
        if (!tty) { fputs(line, stdout); fflush(stdout); }  /* echo commands read from a file */

        /* split into commands at '|', and each command into words */
        char *cmd[MAXC][MAXW];
        int nc = 0, nw = 0;
        for (char *t = strtok(line, " \t\n"); t; t = strtok(NULL, " \t\n")) {
            if (strcmp(t, "|") == 0 && nc < MAXC - 1) { cmd[nc][nw] = NULL; nc++; nw = 0; continue; }
            if (nw < MAXW - 1) cmd[nc][nw++] = t;
        }
        cmd[nc][nw] = NULL;
        nc++;
        if (cmd[0][0] == NULL) continue;

        if (strcmp(cmd[0][0], "exit") == 0) break;  /* built-ins run in the shell itself */
        if (strcmp(cmd[0][0], "cd") == 0) {
            if (chdir(cmd[0][1] ? cmd[0][1] : getenv("HOME")) < 0) perror("cd");
            continue;
        }

        pid_t pids[MAXC];
        int in = 0;                                 /* read end for the next command */
        for (int c = 0; c < nc; c++) {
            int fd[2] = { -1, -1 };
            if (c < nc - 1 && pipe(fd) < 0) { perror("pipe"); break; }
            pids[c] = fork();
            if (pids[c] == 0) {                     /* child */
                if (in != 0) { dup2(in, 0); close(in); }
                if (fd[1] >= 0) { dup2(fd[1], 1); close(fd[1]); close(fd[0]); }
                run(cmd[c]);
            }
            if (in != 0) close(in);                 /* parent: close what the child inherited */
            if (fd[1] >= 0) close(fd[1]);
            in = fd[0];
        }
        for (int c = 0; c < nc; c++) {
            int st;
            waitpid(pids[c], &st, 0);
            if (c == nc - 1 && WIFEXITED(st) && WEXITSTATUS(st) != 0)
                printf("[exit status %d]\n", WEXITSTATUS(st));
            else if (c == nc - 1 && WIFSIGNALED(st))
                printf("[killed by signal %d]\n", WTERMSIG(st));
        }
    }
    return 0;
}
