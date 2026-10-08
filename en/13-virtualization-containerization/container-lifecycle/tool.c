/* tool.c - a tiny static "userland" for a FROM scratch image.
 *   tool write FILE TEXT     append TEXT as a line to FILE
 *   tool cat FILE            print FILE
 *   tool mkdir DIR UID       create DIR owned by UID (used by RUN at build time)
 *   tool serve [--daemon]    a pretend server: stays in the foreground,
 *                            or forks into the background like a classic daemon */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

static int serve(int daemonize) {
    if (daemonize) {
        pid_t child = fork();
        if (child > 0) {                     /* parent: report and leave */
            printf("server: started in the background as pid %d, parent (pid %d) exits\n",
                   (int)child, (int)getpid());
            return 0;
        }
        setsid();                            /* child: detach and keep running */
    } else {
        printf("server: pid %d, running in the foreground\n", (int)getpid());
    }
    fflush(stdout);
    for (;;) pause();                        /* "serve" forever */
}

int main(int argc, char **argv) {
    if (argc >= 4 && strcmp(argv[1], "write") == 0) {
        FILE *f = fopen(argv[2], "a");
        if (!f) { perror(argv[2]); return 1; }
        fprintf(f, "%s\n", argv[3]);
        return fclose(f) != 0;
    }
    if (argc >= 3 && strcmp(argv[1], "cat") == 0) {
        FILE *f = fopen(argv[2], "r");
        if (!f) { perror(argv[2]); return 1; }
        char line[256];
        while (fgets(line, sizeof line, f)) fputs(line, stdout);
        return fclose(f) != 0;
    }
    if (argc >= 4 && strcmp(argv[1], "mkdir") == 0) {
        if (mkdir(argv[2], 0755) != 0 || chown(argv[2], atoi(argv[3]), atoi(argv[3])) != 0) {
            perror(argv[2]); return 1;
        }
        return 0;
    }
    if (argc >= 2 && strcmp(argv[1], "serve") == 0)
        return serve(argc >= 3 && strcmp(argv[2], "--daemon") == 0);
    fprintf(stderr, "usage: tool write FILE TEXT | cat FILE | mkdir DIR UID | serve [--daemon]\n");
    return 2;
}
