/* whoami-os.c - which OS am I running on?
 * Prints the kernel (asked from the running kernel) and the distribution
 * (read from /etc/os-release, a file in the filesystem the program sees). */
#include <stdio.h>
#include <string.h>
#include <sys/utsname.h>

int main(void) {
    struct utsname u;
    uname(&u);                                   /* system call: ask the kernel */
    printf("kernel (from the running kernel): %s %s\n", u.sysname, u.release);

    FILE *f = fopen("/etc/os-release", "r");     /* a file in this filesystem */
    char line[256];
    while (f && fgets(line, sizeof line, f))
        if (strncmp(line, "PRETTY_NAME=", 12) == 0)
            printf("distribution (from /etc/os-release): %s", line + 12);
    if (f) fclose(f);
    return 0;
}
