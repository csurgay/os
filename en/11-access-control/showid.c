/* showid.c - print the real and effective user and group IDs, then try to read a file.
 * Compile: gcc -O2 -o showid showid.c
 * As a setuid program (chown john showid; chmod 4755 showid) it runs with john's effective UID
 * whoever starts it, so it can read files that only john may read.
 */
#include <grp.h>
#include <pwd.h>
#include <stdio.h>
#include <unistd.h>

static const char *uname_of(uid_t u) { struct passwd *p = getpwuid(u); return p ? p->pw_name : "?"; }
static const char *gname_of(gid_t g) { struct group *p = getgrgid(g); return p ? p->gr_name : "?"; }

int main(int argc, char **argv)
{
    uid_t ruid = getuid(), euid = geteuid();
    gid_t rgid = getgid(), egid = getegid();
    /* getpwuid/getgrgid return a static buffer, so print each name before looking up the next */
    printf("real UID %d (%s), ", ruid, uname_of(ruid));
    printf("effective UID %d (%s); ", euid, uname_of(euid));
    printf("real GID %d (%s), ", rgid, gname_of(rgid));
    printf("effective GID %d (%s)\n", egid, gname_of(egid));
    fflush(stdout);
    if (argc > 1) {
        FILE *f = fopen(argv[1], "r");
        char line[256];
        if (!f) { perror(argv[1]); return 1; }
        if (fgets(line, sizeof line, f)) printf("read %s: %s", argv[1], line);
        fclose(f);
    }
    return 0;
}
