/* seccomp.c - a process that gives up system calls it does not need.
 *   gcc -O2 -o seccomp seccomp.c
 *   ./seccomp strict   strict mode: only read, write, _exit and sigreturn remain
 *   ./seccomp filter   a BPF filter: mkdir fails with EPERM, socket kills the process
 */
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

static void say(const char *s) { (void)!write(1, s, strlen(s)); }   /* write(2) only */

static void show_status(void) {                 /* the Seccomp line of /proc/self/status */
    char line[256];
    FILE *f = fopen("/proc/self/status", "r");
    while (fgets(line, sizeof line, f))
        if (strncmp(line, "Seccomp:", 8) == 0) printf("  %s", line);
    fclose(f);
}

static int strict(void) {
    say("entering strict mode\n");
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT);
    say("write() still works\n");
    say("now calling getpid() ...\n");
    syscall(SYS_getpid);                        /* not on the list: SIGKILL */
    say("never printed\n");
    syscall(SYS_exit, 0);                       /* exit, not exit_group */
    return 0;
}

static int filter(void) {
    struct sock_filter prog[] = {
        /* refuse to run if this is not an x86-64 system call */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* load the system call number and compare it */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mkdir, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_socket, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),   /* everything else */
    };
    struct sock_fprog fprog = { .len = sizeof prog / sizeof prog[0], .filter = prog };

    printf("before the filter:\n"); show_status();
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);     /* required without CAP_SYS_ADMIN */
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fprog) != 0) { perror("seccomp"); return 1; }
    printf("after the filter:\n"); show_status();

    if (syscall(SYS_mkdir, "/tmp/seccomp-test", 0755) != 0)
        printf("mkdir:  %s\n", strerror(errno));
    printf("getpid: %ld (allowed)\n", (long)getpid());
    printf("socket: ...\n");
    fflush(stdout);
    socket(AF_UNIX, SOCK_STREAM, 0);            /* kills the process with SIGSYS */
    printf("never printed\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "strict") == 0) return strict();
    if (argc > 1 && strcmp(argv[1], "filter") == 0) return filter();
    fprintf(stderr, "usage: %s strict|filter\n", argv[0]);
    return 2;
}
