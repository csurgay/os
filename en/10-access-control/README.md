# Access Control: Permissions, ACLs and SELinux

*Operating Systems lecture: who may do what with a file, a device or a port, and how the kernel enforces it: subjects, objects and the reference monitor, Unix owner/group/others permissions, the setuid, setgid and sticky bits, root and capabilities, POSIX access control lists, and mandatory access control with SELinux, all tried out on Linux*

Previous: [File Systems](../09-file-systems/).

> **How to read this lecture.** Wherever a new abbreviation or concept appears, a box marked **Explained simply** follows. Click it to open a plain-language explanation. You can skip these boxes if you already know the terms.

## Learning objectives

The [previous lecture](../09-file-systems/#inodes) showed that every inode stores an owner, a group and a few permission bits. This lecture explains what the kernel does with them, what it adds when they are not enough, and how a modern Linux server confines even programs that run as root.

By the end, students will be able to:

- describe access control in terms of subjects, objects, actions and a reference monitor, distinguish policy from mechanism, and apply the principles of least privilege, fail-safe defaults and complete mediation;
- explain the layers a request passes on a server (firewall, service, DAC, MAC) and why defence in depth needs all of them;
- predict the result of a Unix permission check, including the "first matching class decides" rule and the different meaning of `r`, `w` and `x` on files and directories;
- set permissions with `chmod` in octal and symbolic form, with capital `X`, and choose a `umask`;
- explain the setuid, setgid and sticky bits, convert four-digit octal modes to and from the `ls -l` notation (`s`/`S`, `t`/`T`), and assess the risks of setuid programs;
- explain why root bypasses permissions, and how Linux capabilities split root's power;
- design a shared directory with setgid, `umask` and POSIX ACLs, and explain the ACL mask and default ACLs;
- contrast discretionary and mandatory access control, read an SELinux security context, explain type enforcement, and fix the common labelling problems with `restorecon` and `semanage`;
- inspect all of this on Linux with `ls -l`, `stat`, `id`, `chmod`, `su`, `capsh`, `getcap`/`setcap`, `getfacl`/`setfacl` and the SELinux tools.

<details>
<summary><b>Explained simply:</b> access control, permission, DAC, MAC, ACL, SELinux</summary>

- **Access control:** deciding who may do what with which thing, and enforcing that decision. Like a doorman who checks every guest against a list.
- **Permission:** one "yes" on that list: for example "Anna may read this file".
- **DAC** (discretionary access control): the owner of a file decides who may use it, at their own discretion. Like lending your bicycle to whomever you like.
- **MAC** (mandatory access control): a rule set fixed by the system administrator decides, and even owners cannot override it. Like the rules of a hospital: a doctor may not take patient files home, even ones she wrote herself.
- **ACL** (access control list): a list attached to a file: "Anna: read; Béla: read and write; the group: nothing".
- **SELinux** (Security-Enhanced Linux): the MAC system of Red Hat-family Linux distributions.

</details>

## Why access control?

A multi-user, multi-program computer holds data of many owners and runs programs of varying trustworthiness side by side. The [history lecture](../01-historic-evolution/#vii-programs-share-the-memory-protection-and-virtual-memory) showed that protection was needed as soon as several programs shared one machine; the [virtual memory lecture](../08-virtual-memory/#protection) showed how the hardware keeps processes out of each other's memory. Files, devices and network ports live longer than any process and are shared on purpose, so they need finer rules: not "nobody else", but "these people, for these actions".

Every access-control decision has the same three parts:

- the **subject**: the active party, in an OS always a process, acting on behalf of a user;
- the **object**: the passive party: a file, directory, device, network port, another process, a message queue;
- the **action** (access mode): read, write, execute, delete, bind a port, send a signal.

Lampson (1974) described all decisions of a system as an **access matrix**: one row per subject, one column per object, and in each cell the allowed actions. The matrix is far too large and sparse to store, so systems store it in slices. Storing each **column** with its object gives an **access control list** (ACL): "file X: Anna may read, Béla may read and write". Storing each **row** with its subject gives a **capability list**: "Anna holds: read X, write Y". Unix permissions and ACLs are column slices; an open file descriptor, which a process may use without any further check, behaves like a capability.

<details>
<summary><b>Explained simply:</b> subject, object, action, access matrix, capability list</summary>

- **Subject:** who wants to do something: a running program, acting for a person.
- **Object:** what it wants to do it to: a file, a folder, a printer, a network port.
- **Action:** what exactly it wants: read, change, run, delete.
- **Access matrix:** a giant table with people down the side, things across the top, and in each box what that person may do with that thing.
- **Capability list:** the same information kept per person, like a key ring: each key opens one door for one purpose.

</details>

### The reference monitor

The component that makes the decision is the **reference monitor** (Anderson, 1972). Whatever its form, it must have three properties to be trusted: it is **always invoked** (no access path goes around it; Saltzer and Schroeder, 1975, call this *complete mediation*), it is **tamper-proof** (the programs it controls cannot change it), and it is **small enough to be verified**. In Linux the reference monitor is part of the kernel: a process cannot touch a file except through a system call such as `open`, the system call runs in kernel mode where user code cannot interfere ([lecture 5](../05-interrupts/#user-mode-and-kernel-mode)), and the kernel checks the permissions there. A refused request returns the error `EACCES` ("Permission denied") or `EPERM` ("Operation not permitted").

It helps to separate **policy**, *what* is allowed (this file is readable by the group `cons`), from **mechanism**, *how* it is enforced (the kernel compares the process's group IDs with the file's group at `open` time). One mechanism can enforce many policies, and the policy can change without changing the kernel.

Saltzer and Schroeder (1975) listed eight design principles that are still the checklist of secure system design. Four of them recur throughout this lecture:

- **Least privilege:** every program and every user should have only the rights needed for the job, and only for as long as needed. Setuid programs and capabilities are tools for it, and root is its opposite.
- **Fail-safe defaults:** the default is "no"; access is granted explicitly. SELinux denies everything that no rule allows.
- **Complete mediation:** every access is checked, not only the first one.
- **Psychological acceptability:** a mechanism that users find too complicated will be switched off or worked around; the [cognitive ergonomics lecture](../03-cognitive-ergonomics/) applies to security, too. SELinux is the textbook case: the most common "fix" for its error messages is to disable it.

### Defence in depth

On a server no single check is trusted alone. A request from the network to a web server passes a series of independent layers, and it is refused at the first one that says no:

![Left: a stack of five layers from the firewall at the bottom through the service, DAC and MAC to execution at the top. Right: a subject (the httpd process) asks the reference monitor in the kernel for an action on an object (index.html or port 80); the monitor consults the policy, allows or refuses with EACCES/EPERM, and logs denials](access-path.svg)

1. The **firewall** decides which hosts may reach which ports at all.
2. The **service** itself (the daemon, such as the Apache web server or the MariaDB database server) applies its own configuration: which URLs it serves, which database users exist and what they may query.
3. **DAC**: the kernel checks the Unix permissions and ACLs of the files and directories the service touches, using the user ID the service runs as (for example `apache`).
4. **MAC**: the kernel checks a system-wide policy such as SELinux, which can refuse even what DAC allows.
5. Only then is the operation **executed**.

Each layer protects against the failure of the others. If an attacker finds a bug in the web server (layer 2) and makes it run arbitrary code, DAC still keeps the hijacked process away from files of other users, and MAC keeps it away from everything that is not web content, such as the database files, even if those are world-readable by mistake. In Linux, layer 3 is checked before layer 4: a request that DAC refuses never reaches SELinux (Wright et al., 2002).

<details>
<summary><b>Explained simply:</b> reference monitor, EACCES, EPERM, policy, mechanism, least privilege, complete mediation, tamper-proof, fail-safe default, psychological acceptability, defence in depth, firewall, daemon</summary>

- **Reference monitor:** the guard that checks every single access. It must check everything, be impossible to bribe, and be simple enough to inspect.
- **EACCES, EPERM:** the two error codes the kernel returns when it refuses: "Permission denied" (the permission bits say no) and "Operation not permitted" (the operation itself is reserved, for example for the owner or for root).
- **Policy:** the rules: who may do what. **Mechanism:** the machinery that enforces the rules. The house rules versus the lock on the door.
- **Least privilege:** give everyone only the keys they really need. A cleaner gets the key to the offices, not to the safe.
- **Complete mediation, tamper-proof:** the guard checks every visit, not only the first one, and nobody can bribe or replace the guard.
- **Fail-safe default:** if the list says nothing, the answer is "no".
- **Psychological acceptability:** security that is too annoying gets switched off, so it must be easy enough to live with.
- **Defence in depth:** several independent locks one after the other, so that breaking one is not enough. Like a castle with a moat, a wall and a keep.
- **Firewall:** a filter on the network connection that lets only certain kinds of traffic through.
- **Daemon:** a program that runs in the background and provides a service, such as a web server (`httpd`) or a database server (`mysqld`).

</details>

## Users, groups and the identity of a process

The kernel does not know names, only numbers. Every user has a **user ID** (UID) and belongs to a **primary group** (GID) and any number of **supplementary groups**. The mapping between names and numbers is kept in `/etc/passwd` and `/etc/group` (or in a directory service such as LDAP); `id` shows it:

```console
$ id cons1
uid=30036(cons1) gid=30036(cons1) groups=30036(cons1),30002(cons)
```

UID 0 is **root**, the administrator. Most distributions give every user a **private group** of the same name as the primary group (here `cons1`), and the shared groups (here `cons`) as supplementary groups.

A **process** carries the identity of the user who started it, copied from its parent at `fork` and set at login. In fact it carries several IDs (Kerrisk, 2010, ch. 9):

- the **real UID and GID**: who started the process;
- the **effective UID and GID**, together with the supplementary groups: whose rights the process uses in permission checks;
- the **saved set-user-ID**: a copy of the effective UID that lets a setuid program drop its privileges temporarily and take them back.

Normally the real and the effective IDs are the same. The setuid and setgid bits, explained below, make them differ. Every **file** in turn has one owner (a UID) and one group (a GID) in its inode, and the permission bits, which are checked against the effective IDs of the process.

<details>
<summary><b>Explained simply:</b> UID, GID, primary group, supplementary group, private group, root, real and effective ID, saved set-user-ID</summary>

- **UID** (user ID) and **GID** (group ID): the numbers the computer uses for a user and a group. The names are only for people.
- **Primary group:** the group a user's new files belong to by default. **Supplementary groups:** further groups the user is a member of, like extra club memberships.
- **Private group:** a group with exactly one member, named after the user. It keeps a user's files private by default.
- **Root:** the administrator account, number 0, which may do (almost) anything.
- **Real ID, effective ID:** who started a program, and whose rights the program is using right now. Usually the same person; a "setuid" program borrows the rights of its owner.
- **Saved set-user-ID:** a spare copy of the borrowed identity, so that a program can put the borrowed rights aside for a while and pick them up again later.

</details>

## Unix permissions: discretionary access control

### Owner, group, others: the first match decides

The nine permission bits of a file form three triplets of `r` (read), `w` (write) and `x` (execute): one for the **owner** (user, `u`), one for the **group** (`g`) and one for all **others** (`o`). They are a very compact ACL with exactly three entries. The kernel does not combine them: it picks **one** triplet and uses only that one (Kerrisk, 2010, ch. 15):

![A flowchart of five questions: does the process have CAP_DAC_OVERRIDE, is it the owner, is there a named ACL entry for it, is it in a matching group, otherwise others; each yes leads to a decision box, and an example shows that the owner of -------rwx is denied while everybody else may read](dac-check.svg)

1. A process with the capability `CAP_DAC_OVERRIDE`, normally root, skips the check (more below).
2. If the effective UID of the process is the file's owner, the **owner** bits decide, and nothing else is looked at.
3. Otherwise, if the effective GID or one of the supplementary groups is the file's group, the **group** bits decide.
4. Otherwise the **others** bits decide.

The figure has one more step (3) and a wider step 4; both belong to ACLs and are explained [later](#posix-access-control-lists). The consequence of "first match, then stop" surprises many users: rights do **not** add up. A file with mode `-------rwx` owned by `john` can be read by everybody except `john` (and except the members of its group): `john` matches step 2, and the owner bits are empty. The [Linux section](#the-first-match-decides) shows it. The owner is not locked out for good, though: only the owner (or root) may change the mode, so `john` can give himself the rights back with `chmod`. Ownership is the right to decide, which is exactly what *discretionary* means.

### What r, w and x mean for files and directories

For a regular file the meaning is obvious: read the content, change the content, run it as a program. A directory is a file that maps names to inode numbers ([lecture 9](../09-file-systems/#directories)), and its bits apply to that list of names:

| bit | on a file | on a directory |
| --- | --- | --- |
| `r` | read the content | list the names in it (`ls`), but without `x` not their inodes (`ls -l` shows `?`) |
| `w` | change the content (also truncate it) | create, delete and rename entries in it, **only together with `x`** |
| `x` | execute it as a program or script | pass through it: use it in a path, `cd` into it, reach the inodes of the names in it |

Three rules follow, all measured in the [Linux section](#directories-r-w-and-x):

- **`x` is the key to a directory.** Without it nothing inside can be reached, even if the name is known; with `x` alone (`--x`) a file can be opened if its name is known, but the directory cannot be listed: a "secret" directory.
- **`w` on a directory is useless without `x`.**
- **Deleting a file is a change of the directory, not of the file.** `rm` needs `w` and `x` on the directory and no permission at all on the file: a user may delete a file he cannot even read (`rm` asks for confirmation if the file is write-protected, but the kernel does not care). The sticky bit, below, closes this hole for shared directories.

To reach a file, a process needs `x` on **every** directory along the path, then the right bit on the file itself. This is why a home directory with mode `700` protects all files in it, whatever their own modes are.

<details>
<summary><b>Explained simply:</b> owner, group, others, rwx, first match</summary>

- **Owner, group, others:** three kinds of people for every file: the one person who owns it, the members of the file's group, and everyone else.
- **r, w, x:** read, write, execute (run). For a folder: see the list of names, change the list (add, remove, rename), and go into the folder.
- **First match:** the computer finds which kind of person you are, looks only at that kind's rights, and stops. If you are the owner, the rights of "everyone else" do not help you.

</details>

### chmod, chown, chgrp

`chmod` sets the mode, in two notations (Linux man-pages project, n.d.-c):

- **Octal**, one digit per triplet, with the weights $r = 4$, $w = 2$, $x = 1$: `chmod 640 f` sets `rw-r-----` ($6 = 4 + 2$, $4$, $0$). Every digit sets a whole triplet, so the result does not depend on the old mode.
- **Symbolic**, per class (`u`, `g`, `o`, `a` for all) and per bit, with `+` (add), `-` (remove) or `=` (set exactly): `chmod u+x,g-r,o+r f`. Only the named bits change.

A useful symbolic letter is the capital **`X`**: it sets `x` only on directories and on files that are already executable for someone. `chmod -R go+rX dir` makes a whole tree readable and traversable without making every data file executable, which `go+rx` would do.

Only the owner of a file (or root) may change its mode. `chown user:group f` changes the owner and the group; on Linux only root may give a file away (otherwise users could dodge disk quotas or plant files on others), while the owner may change the group with `chgrp` to any group he is a member of.

### The umask

When a program creates a file, it asks for a mode in `open` or `mkdir`: by convention `666` (`rw-rw-rw-`) for data files and `777` for directories and executables. The process's **umask** (user file-creation mask) removes bits from that request: the new mode is the requested mode AND NOT umask. With the common umask `022` the group and others lose `w`: files get `644`, directories `755`. With `002` the group keeps `w` (`664`, `775`), which suits private groups and shared project directories; with `077` nothing is left for anyone but the owner (`600`, `700`). The umask is inherited by child processes and set with the shell built-in `umask`, or for logins in `/etc/login.defs` and by `pam_umask`. Ubuntu, for example, uses `022` in general but `002` for users whose primary group is their private group.

<details>
<summary><b>Explained simply:</b> chmod, octal, symbolic mode, capital X, chown, chgrp, umask</summary>

- **chmod** ("change mode"): the command that sets the permissions of a file.
- **Octal notation:** writing each group of three yes/no switches as one digit from 0 to 7: read counts 4, write 2, execute 1, and you add them up. `7` = all three, `6` = read and write, `4` = read only.
- **Symbolic notation:** saying it in letters: `u+x` = "give the owner execute", `go-w` = "take write away from group and others".
- **Capital X:** "execute, but only where it makes sense": for folders and for programs, not for documents.
- **chown, chgrp:** change the owner, change the group of a file.
- **umask:** a filter that takes away some permissions from every new file automatically. `022` means "never give write permission to group and others unless asked for later".

</details>

### Root and capabilities

The superuser, UID 0, is not checked against the permission bits at all: it may read and write every file and enter every directory. Only execution keeps a small condition: root may execute a file only if at least one of its three `x` bits is set, so that it does not start data files as programs by mistake.

Since Linux 2.2 this power is not a single switch but a set of **capabilities**, each covering one class of privileged operations (Linux man-pages project, n.d.-b). The ones relevant here:

| capability | allows |
| --- | --- |
| `CAP_DAC_OVERRIDE` | ignore read, write and execute bits (execute: if any `x` bit is set) |
| `CAP_DAC_READ_SEARCH` | ignore read bits of files and read and search bits of directories |
| `CAP_FOWNER` | act as the owner of any file (`chmod`, set ACLs, ignore the sticky bit) |
| `CAP_CHOWN` | change the owner and group of any file |
| `CAP_SETUID`, `CAP_SETGID` | change the process's UIDs and GIDs (used by `login`, `su`, `sudo`) |
| `CAP_NET_BIND_SERVICE` | bind TCP/UDP ports below 1024 |
| `CAP_KILL` | send signals to any process |
| `CAP_SYS_ADMIN` | a large mixed bag: mount, swapon, sethostname and much more |

A process running as root normally holds all of them; the kernel checks the capability, not the UID. This makes least privilege possible for system services: a web server may keep only `CAP_NET_BIND_SERVICE` to open port 80, and a backup program only `CAP_DAC_READ_SEARCH` to read everything without being able to change anything. Capabilities can be dropped by a process (`capsh --drop=…`, or `CapabilityBoundingSet=` in a systemd unit), and they can be attached to a program file (`setcap`), which then gives them to whoever runs it, as a finer-grained replacement for setuid root. The [Linux section](#root-is-root-because-of-capabilities) shows a root shell that cannot read a file because it gave up two capabilities, and an ordinary user who can read root's file with one.

<details>
<summary><b>Explained simply:</b> superuser, capability, CAP_DAC_OVERRIDE, bounding set, file capability</summary>

- **Superuser:** another name for root.
- **Capability:** one single piece of root's power, such as "may ignore file permissions" or "may use the network ports below 1024". Instead of a master key, a set of special keys that can be handed out one by one.
- **CAP_DAC_OVERRIDE:** the special key that opens every file regardless of its permissions.
- **Bounding set:** the list of capabilities a program and all its children can ever get. Shrinking it is like taking keys off the ring for good.
- **File capability:** a special key glued to one program file: whoever runs that program gets that one key while it runs, and nothing else.

</details>

## Special bits: setuid, setgid and sticky

The mode of a file has twelve permission bits, not nine. In front of the three triplets stand three special bits, and the whole 16-bit mode word of the inode also holds the file type in its top four bits:

![The 16-bit mode word: four bits of file type, then setuid, setgid and sticky with weights 4, 2, 1, then rwx for owner, group and others with weights 4, 2, 1 each; the example bits give octal 7743, which ls -l shows as -rwsr-S-wt; below, a table of how ls shows a special bit in the x position: -, x, S or s, T or t](mode-bits.svg)

| bit | octal | on an executable file | on a directory |
| --- | --- | --- | --- |
| **setuid** (SUID) | `4000` | runs with the **owner's** effective UID, for example `/usr/bin/passwd` | no effect on Linux |
| **setgid** (SGID) | `2000` | runs with the **group's** effective GID | new files and subdirectories **inherit the directory's group** (and subdirectories the setgid bit) |
| **sticky** | `1000` | no effect on Linux (historically: keep the program text in swap) | in a shared directory only the **owner of a file** (or of the directory, or root) may delete or rename it, for example `/tmp` |

### Reading and writing them

`ls -l` has no separate columns for the special bits. Each one shares the position of an `x`: setuid the owner's, setgid the group's, sticky the others'. Lowercase means that both bits are set, uppercase that only the special bit is:

| | `x` not set | `x` set |
| --- | --- | --- |
| special bit not set | `-` | `x` |
| setuid or setgid set | `S` | `s` |
| sticky set | `T` | `t` |

An uppercase `S` or `T` is usually a mistake: a setuid bit on a file nobody may execute does nothing.

In octal the special bits form a fourth digit in front of the other three, with the same weights: setuid $4$, setgid $2$, sticky $1$. To convert a mode string, read each triplet with the weights $4 2 1$, and collect the special bits into the leading digit. Two examples:

- `rwsr-S-wt`: the owner has `rws` = $4 + 2 + 1 = 7$ with setuid; the group `r-S` = $4$ with setgid; others `-wt` = $2 + 1 = 3$ with sticky. The special digit is $4 + 2 + 1 = 7$, so the mode is `7743`.
- `-wxrwsr-T`: owner `-wx` = $3$, group `rws` = $7$ with setgid, others `r-T` = $4$ with sticky; the special digit is $2 + 1 = 3$: `3374`.

Conversely, `chmod 1777 dir` gives `drwxrwxrwt`, the mode of `/tmp`, and `chmod 7640 f` gives `-rwSr-S--T`: all three special bits, none of them effective. The [Linux section](#chmod-umask-and-the-special-bits) checks these with `stat`.

### setuid: borrowing the owner's identity

Users change their own password with `passwd`, but the password hashes are in `/etc/shadow`, which only root may write. The solution is the setuid bit: `/usr/bin/passwd` is owned by root and has mode `4755` (`-rwsr-xr-x`). When any user executes it, the kernel sets the effective UID of the new process to the file's owner, root, while the real UID stays the user's. The program uses the real UID to find out *whose* password to change, and the effective UID to be *able* to change it. `su`, `sudo`, `mount` and `ping` (on older systems) work the same way.

A setuid-root program is therefore a hole in the wall between users and root, and it must be written with great care. It runs in an environment chosen by the attacker: its arguments, environment variables, open file descriptors, current directory and resource limits all come from the caller. The kernel and the C library help: for setuid programs the dynamic linker ignores `LD_LIBRARY_PATH` and restricts `LD_PRELOAD`, which would otherwise let the caller inject code (Kerrisk, 2010, ch. 38). Good practice is to keep setuid programs few and small, to drop the privilege as soon as it is not needed (`seteuid(getuid())`), and to replace setuid root with a single file capability wherever possible. `find / -perm -4000 -type f` lists all setuid programs of a system, a standard step of a security audit.

Two more safeguards are measured in the Linux section:

- The kernel **ignores the setuid and setgid bits on scripts** (files starting with `#!`). Between the kernel reading the `#!` line and the interpreter opening the script, an attacker could replace the script, for example by renaming a symbolic link: the classic race condition of [lecture 5](../05-interrupts/#interrupts-and-concurrency) in another setting.
- A file system mounted with the **`nosuid`** option ignores both bits. Removable media, network shares and `/tmp` are often mounted this way, so that a user cannot bring a setuid-root shell from home on a USB stick.

A third safeguard: writing to a setuid file or changing its owner clears the setuid bit, so that a modified program, or one handed to a new owner, does not keep the old privilege.

### setgid on a directory: one group for a team

On a file, setgid works like setuid with the group. On a directory it means something different and very practical: files and subdirectories created inside get the **directory's group** instead of the creator's primary group, and new subdirectories inherit the setgid bit too. A team directory owned by the group `cons` with mode `2770` (`drwxrws---`) keeps all its content in the group `cons`, whoever creates it. Setgid fixes only the group, not the bits: the group can *write* the new files only if the creator's umask leaves the group's `w`, so team members need `umask 002`, or a default ACL (below).

### sticky on a directory: shared, but not common

`/tmp` must be writable by everyone, so its mode would be `777`. But `w` on a directory allows deleting and renaming any entry in it: `user2` could delete or replace the temporary files of `user1`, a classic attack on programs that write to predictable names in `/tmp`. With the sticky bit (`1777`, `drwxrwxrwt`) everyone may still create files, but only a file's owner, the directory's owner or root may delete or rename it. `/tmp` and `/var/tmp` have mode `1777` on every Unix system.

<details>
<summary><b>Explained simply:</b> setuid, setgid, sticky bit, s/S, t/T, passwd, /etc/shadow, nosuid, race condition</summary>

- **setuid** ("set user ID"): a mark on a program that says "whoever starts this, it runs with my owner's rights". Like a bank teller who may open the vault for you, but only to do exactly what the teller's job allows.
- **setgid** ("set group ID"): the same for the group; on a folder: "everything created in here belongs to my group".
- **Sticky bit:** a mark on a shared folder: "anyone may put things in, but only the owner may take them out". Like a shared fridge where everyone may add food but may take only their own.
- **s/S, t/T:** how `ls -l` shows these marks: lowercase if the "execute" switch is also on, uppercase if not.
- **passwd:** the program that changes your password. **/etc/shadow:** the file that stores the scrambled passwords, readable only by root.
- **nosuid:** a mount option that tells the system to ignore setuid marks on a disk, for example on a USB stick.
- **Race condition:** a bug where the result depends on who is faster, here: replacing a file in the tiny moment between two steps of the system.

</details>

## POSIX access control lists

### What the nine bits cannot say

Three consultants, `cons1`, `cons2` and `cons3`, work on a project and share the group `cons`. Their directory `/srv/lab10/project/consult` belongs to `cons1:cons` with mode `2770`, and they use `umask 002`, so every file is readable and writable by the group. Now a document arrives that `cons3` must not see. With mode bits alone there is no way to say "the group `cons` except `cons3`": the options are a new group for `cons1` and `cons2` (which the administrator must create, for every such exception), or taking the group's rights away from everyone. Equally impossible: "`cons` may write, and the auditor `audit1` may read".

**Access control lists** solve this by allowing more than three entries per file. Linux implements the ACLs of the POSIX.1e draft standard: the standard itself was withdrawn in 1998, but its ACL part was implemented almost identically in Linux, the BSDs and Solaris (Grünbacher, 2003). They are supported by ext4, XFS, Btrfs, tmpfs and others, and stored in an **extended attribute** of the inode, `system.posix_acl_access`.

### Entries and the mask

An ACL is a list of entries of the form `type:qualifier:permissions` (Linux man-pages project, n.d.-a):

| entry | meaning | corresponds to |
| --- | --- | --- |
| `user::rw-` | the owner | owner bits |
| `user:cons3:---` | a **named user** | (new) |
| `group::rw-` | the owning group | group bits (without ACL) |
| `group:audit:r--` | a **named group** | (new) |
| `mask::rw-` | the **upper limit** for all named entries and the owning group | group bits (with ACL) |
| `other::r--` | everyone else | others bits |

An ACL with only the three entries `user::`, `group::` and `other::` (a *minimal* ACL) is exactly the classic mode; an ACL with more entries is an **extended ACL**, marked with a `+` after the mode in `ls -l`. The check follows the same "first match" idea, extended by two steps (see the flowchart above): owner → named user → owning group and named groups → others. A named user entry and all group entries are combined with the mask by AND; if the process matches several groups, it gets access if any matching group entry (after the mask) grants it.

The **mask** is what keeps ACLs compatible with programs that know only the nine bits. In an extended ACL, the group triplet of the mode *is* the mask: `ls -l` shows it, and `chmod g-w` changes it. So `chmod go-rwx file`, the classic "make it private", still works: it sets the mask to `---` and switches off every named user and group at once, without deleting them.

![The ACL of plan.txt as five rows: user::rw- in the owner class; user:cons3:---, group::rw- and mask::r-- in the group class, where group::rw- is effectively r-- because of the mask; other::r-- in the other class. The owner, mask and other entries appear as the three triplets of ls -l, followed by a +. Below: notes on the mask and on default ACLs](acl-mask.svg)

### Default ACLs

A directory can also carry a **default ACL** (`system.posix_acl_default`). It is never checked; it is a template: every file or subdirectory created inside gets it as its access ACL, and subdirectories also get it as their own default ACL, so the rule spreads down the tree. When a default ACL exists, the umask is not applied; the mode requested by the program still limits the result (a file created with `0666` gets no `x`, so its mask becomes `rw-`). This is the clean answer to the umask problem of shared directories: `setfacl -d -m g::rwx,u:cons3:--- consult` makes every future file writable by the group and closed to `cons3`, whatever umask the creator uses.

### The tools

`getfacl` shows an ACL and `setfacl` changes it (Linux man-pages project, n.d.-d):

```console
$ getfacl plan.txt                         # show the ACL
$ setfacl -m u:cons3:--- plan.txt          # modify: add or change entries
$ setfacl -m g:audit:r-x -R consult        # recursively
$ setfacl -d -m g::rwx consult             # change the default ACL of a directory
$ setfacl -x u:cons3 plan.txt              # remove one entry
$ setfacl -b plan.txt                      # remove all extended entries
$ getfacl -R consult > acl.txt; setfacl --restore=acl.txt   # back up and restore
```

ACLs travel with the file within a file system (`mv`), but copies keep them only when asked (`cp -p`, `cp -a`, `rsync -A`, `tar --acls`). Backup programs that do not know about extended attributes silently drop them.

### ACLs in other systems

Windows NT and its successors have used ACLs for everything from the start. Every NTFS file ([lecture 9](../09-file-systems/#ntfs)), registry key, process and service has a **security descriptor** with an owner, a **discretionary ACL** (DACL) of allow and deny entries for users and groups, and a **system ACL** (SACL) that says which accesses to audit. Entries are inherited from the parent folder by default, and the entries are checked in order until the requested rights are granted or one of them is denied; since the standard (canonical) order puts the explicit deny entries first, an explicit deny beats an allow (Microsoft, n.d.-a). NFS version 4 uses a similar, richer ACL model, which is why `nfs4_setfacl` exists next to `setfacl`.

<details>
<summary><b>Explained simply:</b> named user, named group, mask, extended ACL, default ACL, extended attribute, POSIX.1e, security descriptor, DACL, SACL, NFSv4</summary>

- **Named user, named group:** an extra line in the list for one particular person or group: "cons3: nothing".
- **Mask:** a ceiling for everyone in the middle of the list (named people and groups). Even if a line says "read and write", if the ceiling says "read only", only reading is allowed.
- **Extended ACL:** a list with more than the basic three lines; `ls -l` shows a `+` for it.
- **Default ACL:** a template on a folder: every new file in it gets a copy of these rules automatically.
- **Extended attribute:** a small labelled note attached to a file, next to its content and its basic information. ACLs and SELinux labels are stored as such notes.
- **POSIX.1e:** a planned common standard for security features of Unix-like systems. It was never finished, but its ACL part is what Linux uses.
- **Security descriptor:** the security information sheet of a Windows object: its owner and its two lists.
- **DACL, SACL:** the two lists of a Windows file: who may do what (DACL), and which actions should be recorded in the security log (SACL).
- **NFSv4** (Network File System, version 4): a way of using files stored on another computer over the network as if they were local.

</details>

## Mandatory access control

### Why DAC is not enough

Under DAC the owner of a file decides who may use it, and **every program the owner runs may decide in his name**. That is the weakness: a program is not the user. If a user runs a malicious program (a Trojan horse), or a program with a bug that an attacker exploits, it has all the rights of the user: it can read his files and give them away, for example by copying them to `/tmp` with mode `666` or sending them over the network. DAC cannot prevent this, because from the kernel's point of view the program *is* the owner exercising his discretion. For services running as root, DAC offers no protection at all.

**Mandatory access control** adds a second set of rules that is set by the system's security policy, applies to every process including root's, and cannot be changed by users or by the owners of files. A short mnemonic: DAC answers *who* (which user) may access an object; MAC answers *what* (which kind of program) may do *what* with *which kind* of object. The two are combined: an access must be allowed by both.

The oldest MAC model comes from the military: **multi-level security** (MLS), in which subjects and objects have clearance and classification levels (unclassified, confidential, secret, top secret), and information may flow only upwards: a subject may not read objects above its level ("no read up") and may not write objects below it ("no write down"), so that a secret process cannot leak into an unclassified file (Bell & LaPadula, 1976). Such rules are too rigid for general servers. Modern Linux MAC systems are built on the kernel's **Linux Security Modules** (LSM) framework: a set of hooks at every security-relevant point in the kernel (opening a file, binding a socket, sending a signal) that a security module can use to refuse the operation after the DAC check has passed (Wright et al., 2002). The two most widely used modules are SELinux and AppArmor.

<details>
<summary><b>Explained simply:</b> Trojan horse, MAC, MLS, clearance, LSM, hook</summary>

- **Trojan horse:** a program that does something harmful in secret while it seems to do something useful, using the rights of the person who started it.
- **MAC** (mandatory access control): rules from the top that nobody below can switch off, not even the owner of a file or the administrator's programs.
- **MLS** (multi-level security): the "secret / top secret" system: you may read only what your clearance allows, and you may not write secrets into a less secret place.
- **Clearance:** the highest secrecy level a person or program is trusted with.
- **LSM** (Linux Security Modules): the slots in the Linux kernel where an extra security guard can be plugged in. **Hook:** one such slot, a point where the kernel asks the guard "may this happen?".

</details>

### SELinux: labels and type enforcement

SELinux was developed by the US National Security Agency on the basis of the Flask research architecture, released as open source in 2000, and merged into Linux 2.6 through the LSM framework (Loscocco & Smalley, 2001; Smalley et al., 2001). It is enabled and enforcing by default on Fedora, Red Hat Enterprise Linux and its rebuilds (AlmaLinux, Rocky Linux; see [lecture 2](../02-quality-and-enterprise-linux/)), and on Android.

SELinux gives **every** subject and object a **security context** (label), a string of four fields `user:role:type:level`:

![Top: the context system_u:system_r:httpd_t:s0 split into user, role, type and level, with a file and a port context beside it. Below: the domains httpd_t (Apache httpd) and mysqld_t (MariaDB mysqld) on the left, the types http_port_t, httpd_sys_content_t, user_home_t, mysqld_db_t and mysqld_port_t on the right; solid arrows show allowed access (httpd_t may bind http_port_t and read httpd_sys_content_t, mysqld_t may read and write mysqld_db_t and bind mysqld_port_t), dashed red arrows show denied access (httpd_t to user_home_t and mysqld_db_t, mysqld_t to httpd_sys_content_t)](selinux-te.svg)

- **user** (`system_u`, `unconfined_u`, `staff_u`, …): the SELinux user, mapped from the Linux user at login; it limits which roles are possible.
- **role** (`system_r`, `object_r` for files, …): the roles a user may enter, and the domains a role may run in (role-based access control).
- **type**: the field that matters most. The type of a process is called its **domain** (`httpd_t`, `mysqld_t`); the type of a file or port says what kind of object it is (`httpd_sys_content_t` for web pages, `mysqld_db_t` for database files, `user_home_t` for the contents of home directories, `http_port_t` for TCP ports 80, 443 and a few others).
- **level** (`s0`, `s0-s0:c0.c1023`): the MLS sensitivity and the categories of multi-category security (MCS), used for example to separate virtual machines and containers from each other.

Files keep their context in the extended attribute `security.selinux`; processes get theirs from the context of the program they execute and the domain of their parent, according to **transition rules** (when `systemd`, in domain `init_t`, executes `/usr/sbin/httpd`, labelled `httpd_exec_t`, the new process enters `httpd_t`). `ls -Z`, `ps -Z` and `id -Z` show the contexts.

The policy is a large set of **type enforcement** rules that say which domain may perform which actions on which types, per object class:

```
allow httpd_t httpd_sys_content_t:file { read open getattr };
allow httpd_t http_port_t:tcp_socket name_bind;
```

Everything that no rule allows is **denied**, and logged. The effect is that each confined service lives in its own small sandbox: the web server may read web content and bind the web ports, but not read the database files, the users' home directories or `/etc/shadow`, even when it runs as root and even if those files had mode `777`. A hijacked Apache still cannot read MariaDB's data, and a hijacked MariaDB cannot change the web pages.

Writing such a policy for a whole system is an enormous task (the reference policy has tens of thousands of rules), so distributions ship ready-made policies:

- **targeted** (the default): network services and other selected daemons run in confined domains; users and everything else run in the `unconfined_t` domain, which is constrained only by DAC;
- **minimum**: like targeted, but only a few selected processes are confined, for small or special systems;
- **mls**: full multi-level security for government and military requirements.

Behaviour that varies between sites is switched by **booleans**, named on/off switches over groups of rules: `httpd_can_network_connect` (may the web server open outgoing connections, for example to an application server), `httpd_enable_homedirs` (may it serve `~/public_html`), `httpd_can_network_connect_db`. `getsebool -a` lists them, `setsebool -P name on` sets one permanently.

SELinux runs in one of three **modes**:

- **enforcing**: denies and logs;
- **permissive**: only logs what it would deny; useful for diagnosing and for developing policy;
- **disabled**: no labels are maintained at all. Files created meanwhile are unlabelled, so returning to enforcing requires relabelling the whole file system.

`getenforce` shows the mode and `setenforce 0|1` switches between enforcing and permissive until the next boot; the boot-time mode is set in `/etc/selinux/config` (on RHEL 9 and later, the documented way to disable it completely is the kernel parameter `selinux=0`). The Red Hat documentation's advice is unambiguous: permissive mode, or a permissive domain for a single service, is for diagnosis; disabling SELinux removes a layer of defence (Red Hat, n.d.).

<details>
<summary><b>Explained simply:</b> security context, label, domain, type, type enforcement, role, MCS, transition, targeted policy, boolean, enforcing, permissive</summary>

- **Security context, label:** a name tag on every program and every file, such as "web server" or "web page".
- **Type, domain:** the most important part of the name tag: what kind of thing it is. For a running program it is called its domain.
- **Type enforcement:** the rule book: "programs tagged *web server* may read files tagged *web page*". Whatever is not in the book is forbidden.
- **Role:** a job title that decides which kinds of programs a user may run.
- **MCS** (multi-category security): extra tags that keep, for example, two virtual machines of the same kind apart.
- **Transition:** the rule that gives a newly started program its tag, for example "when the system starts the web server program, it gets the *web server* tag".
- **Targeted policy:** the standard rule book: it locks down the risky network services and leaves ordinary users alone.
- **Boolean:** an on/off switch for a group of rules, for example "may the web server connect to other computers?".
- **Enforcing, permissive:** really forbidding, or only writing down what would have been forbidden.

</details>

### Working with labels

Most SELinux problems on a real server are **wrong labels**, not missing rules. The policy contains a database of default file contexts for paths (`/var/www(/.*)?` → `httpd_sys_content_t`); a file gets its label at creation from the policy (usually the label of the directory it is created in) and keeps it afterwards. Hence the classic trap:

- `cp ~/index.html /var/www/html/` creates a **new** file in `/var/www/html`, which gets `httpd_sys_content_t`: the page works.
- `mv ~/index.html /var/www/html/` only renames the existing inode, which **keeps** its old label `user_home_t`. DAC allows the access (mode `644`), but the web server's domain may not read `user_home_t`: the browser shows **403 Forbidden**, and the audit log shows a denial.

The tools:

- `restorecon -Rv /var/www/html` resets labels to the policy's defaults for those paths: the fix for the `mv` case.
- `chcon -t httpd_sys_content_t file` sets a label by hand, but only **temporarily**: the next `restorecon` or full relabel (`touch /.autorelabel` and reboot) reverts it, because the policy's database still says otherwise.
- `semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'` adds a rule to the database (here: a web root outside `/var/www`), and `restorecon -Rv /web` then applies it. This is the **persistent** way.
- `semanage port -a -t http_port_t -p tcp 3131` labels a non-standard port, so that the web server may listen on it.

When something is denied, the kernel writes an **AVC denial** (access vector cache, the kernel's cache of policy decisions) to the audit log, `/var/log/audit/audit.log`. It names the action (for example `{ read }`), the process (`comm="httpd"`), the object (`name="index.html"`), the source context (`scontext=…:httpd_t:s0`), the target context (`tcontext=…:user_home_t:s0`) and the object class (`tclass=file`). `ausearch -m AVC -ts recent` finds them; `audit2why` explains them; with the `setroubleshoot` package, `sealert -a /var/log/audit/audit.log` (or `sealert -l ID`, whose ID is announced in the system log) gives a readable analysis with suggested commands. The suggestion is usually one of three: fix a label (`restorecon`, `semanage fcontext`), switch a boolean, or, rarely, extend the policy with a local module (`audit2allow -M`), which should be the last resort, since it can allow exactly what an attacker attempted.

### AppArmor and other security modules

**AppArmor**, the default MAC system of Ubuntu and Debian (and of SUSE until SUSE Linux Enterprise 16 and openSUSE Leap 16 switched to SELinux in 2025), takes the opposite approach to labels: it confines programs by **path names**. A profile in `/etc/apparmor.d/` lists, for one program, the files and directories it may access (with permissions such as `r`, `w`, `ix`), the capabilities and the network access it may use; everything else is denied. Programs without a profile are unconfined. Profiles are easier to read and write than SELinux policy, and need no file labels, but a path-based rule follows the name, not the object: a hard link or a bind mount gives the same file another name that the profile may not cover. `aa-status` lists the loaded profiles; `aa-complain` and `aa-enforce` correspond to SELinux's permissive and enforcing modes, per profile. The kernel also offers smaller modules that can be stacked with these: Yama (restricts `ptrace`), Landlock (lets an unprivileged program sandbox itself) and lockdown (protects the running kernel from root).

Windows has a mandatory element too: **Mandatory Integrity Control** gives every process and object an integrity level (low, medium, high, system), and a process may not write to objects of a higher level whatever the DACL says ("no write up"). Web browsers run their sandboxed content processes at low (or even lower, "untrusted") integrity for this reason (Microsoft, n.d.-b).

<details>
<summary><b>Explained simply:</b> AVC, audit log, restorecon, chcon, semanage, sealert, AppArmor, profile, Yama, Landlock, lockdown, Mandatory Integrity Control</summary>

- **AVC denial:** the message SELinux writes when it forbids something: who tried what on which thing.
- **Audit log:** the system's security diary, `/var/log/audit/audit.log`.
- **restorecon:** "put the correct name tags back" according to the official list.
- **chcon:** change a name tag by hand, for now. The next clean-up undoes it.
- **semanage:** change the official list itself, so that the change lasts.
- **sealert:** a helper that turns the cryptic denial messages into explanations and suggestions.
- **AppArmor:** another lock-down system, which describes what a program may touch by file names instead of name tags. **Profile:** the list of allowed things for one program.
- **Yama, Landlock, lockdown:** small extra guards in the Linux kernel: Yama stops programs from spying on each other, Landlock lets a program lock itself into a smaller room, lockdown stops even the administrator from tampering with the running kernel.
- **Mandatory Integrity Control, integrity level:** Windows' trust levels (low, medium, high, system): a less trusted program may not change things that belong to a more trusted level.

</details>

## The same ideas on Linux (x86-64)

The demos run as root on the Ubuntu 24.04 cloud virtual machine of the previous lectures (Linux 6.18, GNU coreutils 9.4, gcc 13, libacl 2.3.2, libcap 2.66). Root is needed to create users and to change owners; each experiment then switches to an ordinary user with `su USER -c 'command'`. All experiments work in `/srv/lab10`. To repeat them, make the scripts executable (`chmod +x *.sh`), run `./users.sh` first, and compile the setuid demo (`gcc -O2 -o showid showid.c`). `userdel -r USER` and `rm -r /srv/lab10` clean up at the end.

This machine has the ACL library (`libacl.so.1`) but not the `acl` package with `getfacl` and `setfacl`. The ACL demo therefore uses `acl.py`, a minimal stand-in of about 150 lines that calls the same library functions as `getfacl` and `setfacl` (`acl_get_file`, `acl_to_any_text`, `acl_from_text`, `acl_calc_mask`, `acl_set_file`) and prints in the same format; on a normal installation, use `getfacl` and `setfacl` (`sudo apt install acl`, `sudo dnf install acl`). This kernel is built with SELinux, but no policy is loaded (see the [last demo](#is-there-a-mac-policy-on-this-machine)), so the SELinux part is a [lab for a virtual machine](#selinux-on-a-fedora-rhel-or-almalinux-virtual-machine) with commands only.

<details>
<summary><b>Explained simply:</b> console, root, su, useradd, script</summary>

- **Console** (terminal): a window where you type commands. Lines starting with `$` (or `#` when typed as the administrator) are what you type; the other lines are the computer's answer.
- **su USER -c '…'**: "run this one command as that user". Root may do so without a password.
- **useradd:** create a new user account.
- **Script** (`.sh` file): a list of commands saved in a file and run one after the other.

</details>

### Users for the demos

```console
# ./users.sh
uid=30033(john) gid=30033(john) groups=30033(john)
uid=30034(user1) gid=30034(user1) groups=30034(user1)
uid=30035(user2) gid=30035(user2) groups=30035(user2)
uid=30036(cons1) gid=30036(cons1) groups=30036(cons1),30002(cons)
uid=30037(cons2) gid=30037(cons2) groups=30037(cons2),30002(cons)
uid=30038(cons3) gid=30038(cons3) groups=30038(cons3),30002(cons)
```

Every user got a private group with the same number; the three consultants are also in the supplementary group `cons` (GID 30002). The numbers are large because this machine starts its user IDs at 30000.

### The first match decides

```console
# ./firstmatch.sh
-------rwx 1 john john 30 Oct  7 18:42 fm/note.txt
--- as john (the owner):
cat: /srv/lab10/fm/note.txt: Permission denied
--- as user1 (falls into 'others'):
anyone but john may read this
--- the same for a directory, d------rwx:
d------rwx 2 john john 4096 Oct  7 18:42 fm/dir
ls: cannot open directory '/srv/lab10/fm/dir': Permission denied
a
b
```

The owner is refused, and a stranger is admitted. The kernel found that `john` is the owner, took the owner triplet `---`, and stopped; `user1` is neither owner nor group member and gets the others triplet `rwx`. The same holds for the directory.

### Directories: r, w and x

`dirperms.sh` lets `user1` (an "other") try five operations on a directory `d` of `john`, for seven settings of the others' bits. The file `d/f` inside has mode `666`, so every refusal comes from the directory:

```console
# ./dirperms.sh
others      ls d     cd d     cat d/f  touch    rm d/f   
drwxr-x---  denied   denied   denied   denied   denied   
drwxr-xr--  ok       denied   denied   denied   denied   
drwxr-x--x  denied   ok       ok       denied   denied   
drwxr-xr-x  ok       ok       ok       denied   denied   
drwxr-x-w-  denied   denied   denied   denied   denied   
drwxr-x-wx  denied   ok       ok       ok       ok       
drwxr-xrwx  ok       ok       ok       ok       ok       
--- a file with no permissions at all, in a directory where user1 has w and x:
---------- 1 john john 0 Oct  7 18:42 d/locked
cat: /srv/lab10/d/locked: Permission denied
rm worked: deleting is a change of the directory
```

Read the table row by row: `r` alone lists the names but opens nothing; `x` alone opens a file whose name is known but cannot list; `w` alone (`-w-`) achieves nothing; `wx` allows creating and deleting without listing. The last lines are the surprise of the section: `user1` cannot read `locked`, but may delete it.

### chmod, umask and the special bits

```console
# ./modes.sh
--- octal: every digit sets one class completely
640  -rw-r-----  f
--- symbolic: change single bits, leave the others alone
704  -rwx---r--  f
644  -rw-r--r--  f
--- capital X: x only for directories and files that are already executable by someone
700  drwx------  d
600  -rw-------  plain
700  -rwx------  script
755  drwxr-xr-x  d
644  -rw-r--r--  plain
755  -rwxr-xr-x  script
--- umask: bits removed from new files (base 666) and directories (base 777)
umask 022 -> file 644 -rw-r--r--, dir 755 drwxr-xr-x
umask 002 -> file 664 -rw-rw-r--, dir 775 drwxrwxr-x
umask 077 -> file 600 -rw-------, dir 700 drwx------
umask 027 -> file 640 -rw-r-----, dir 750 drwxr-x---
--- the special bits: 4 = setuid, 2 = setgid, 1 = sticky
4755  -rwsr-xr-x  f
2755  -rwxr-sr-x  f
1777  -rwxrwxrwt  f
4644  -rwSr--r--  f
2644  -rw-r-Sr--  f
1666  -rw-rw-rwT  f
7743  -rwsr-S-wt  f
3374  --wxrwsr-T  f
7640  -rwSr-S--T  f
```

`stat -c '%a %A'` prints the mode in octal and as a string. `chmod u+x,g-r,o+r` on `640` gives `704`: only the named bits changed. `chmod -R go+rX` gave `x` to the directory and to `script` (executable by its owner) but not to `plain`. The umask lines show that a umask never adds bits, it only removes them from `666` or `777`. The last block confirms the display rule and both worked examples: `7743` is `rwsr-S-wt` and `3374` is `-wxrwsr-T` (after the leading `-` for a regular file).

### The sticky bit on a shared directory

`user1` creates a file in a world-writable directory, and `user2` tries to rename and delete it, first with mode `777`, then with `1777`:

```console
# ./sticky.sh
drwxrwxrwt 12 root root 4096 Oct  7 18:42 /tmp
--- shared is drwxrwxrwx (0777)
-rw-rw-r-- 1 user1 user1 15 Oct  7 18:42 shared/file.txt
user2: renamed it to mine.txt
user2: deleted the file of user1
--- shared is drwxrwxrwt (1777)
-rw-rw-r-- 1 user1 user1 15 Oct  7 18:42 shared/file.txt
mv: cannot move 'file.txt' to 'mine.txt': Operation not permitted
rm: cannot remove 'file.txt': Operation not permitted
--- the owner may still delete it:
user1: deleted own file
```

Without the sticky bit, `user2` could rename and delete a file that is not his (and that he could not even write: it is `rw-rw-r--`). With it, the kernel refuses with `EPERM` ("Operation not permitted"), not `EACCES`: the bits would allow it, the operation itself is reserved for the owner. The new file is `rw-rw-r--` because `su` gave `user1` the umask `002` of users with a private group.

### A setuid program

`showid.c` prints the real and effective IDs of its process and then tries to read the file named on its command line. `setuid.sh` installs it owned by `john`, next to `john`'s private diary, and runs it as `user1`:

```console
# gcc -O2 -o showid showid.c
# ./setuid.sh
-rw------- 1 john john    13 Oct  7 18:42 diary.txt
-rwxr-xr-x 1 john john 16576 Oct  7 18:42 showid
--- an ordinary program runs with the IDs of the user who starts it:
real UID 30034 (user1), effective UID 30034 (user1); real GID 30034 (user1), effective GID 30034 (user1)
/srv/lab10/suid/diary.txt: Permission denied
--- chmod u+s (4755): it runs with the effective UID of its owner, john:
-rwsr-xr-x 1 john john 16576 Oct  7 18:42 showid
real UID 30034 (user1), effective UID 30033 (john); real GID 30034 (user1), effective GID 30034 (user1)
read /srv/lab10/suid/diary.txt: john's diary
--- chmod g+s (2755) instead: the effective GID becomes the file's group:
-rwxr-sr-x 1 john john 16576 Oct  7 18:42 showid
real UID 30034 (user1), effective UID 30034 (user1); real GID 30034 (user1), effective GID 30033 (john)
--- a real setuid-root program of the system:
-rwsr-xr-x 1 root root 64152 May 30  2024 /usr/bin/passwd
--- the setuid bit on a script is ignored by the kernel:
-rwsr-xr-x 1 john john 68 Oct  7 18:42 who.sh
script: real UID 30034, effective UID 30034
--- and on a file system mounted with nosuid:
tmpfs /mnt/l10nosuid tmpfs rw,nosuid,relatime,size=4096k 0 0
real UID 30034 (user1), effective UID 30034 (user1); real GID 30034 (user1), effective GID 30034 (user1)
```

With the setuid bit, the same binary started by the same user reads `john`'s diary: the effective UID is `john`'s, the real UID still says who is at the keyboard. This is exactly why setuid programs are dangerous: whatever `showid` can be tricked into reading, `user1` can read. The script with the same bits runs with `user1`'s IDs, and so does the setuid binary copied to a `nosuid` file system.

### Root is root because of capabilities

```console
# ./caps.sh
---------- 1 root root 21 Oct  7 18:42 locked.txt
--- root reads it anyway:
nobody may read this
--- some capabilities of this root shell (effective set, decoded, filtered):
cap_chown cap_dac_override cap_dac_read_search cap_fowner cap_kill cap_setuid cap_net_bind_service 
--- root without CAP_DAC_OVERRIDE and CAP_DAC_READ_SEARCH:
0
cat: locked.txt: Permission denied
--- the opposite: an ordinary user with one capability on one program
/srv/lab10/caps/rcat: /srv/lab10/caps/rootonly.txt: Permission denied
./rcat cap_dac_read_search=ep
root's note
```

A file with mode `000` is no obstacle for root. `capsh --drop=…` starts a shell that is still UID 0 (`id -u` prints `0`) but has given up the two DAC capabilities, and it is refused like anybody else: the kernel checks capabilities, not the number 0. Conversely, a copy of `cat` with the file capability `cap_dac_read_search` (`e` = effective, `p` = permitted) lets `user1` read a file of root, but grants nothing else: it cannot write or delete anything. That is least privilege, and also a warning: `getcap -r /` belongs in a security audit next to `find / -perm -4000`.

### A project directory with setgid and ACLs

`acl-project.sh` plays the consultants' story from the ACL section step by step; `acl.py get` prints exactly what `getfacl` would, and the comments in the output name the `setfacl` command that `acl.py modify` replaces:

```console
# ./acl-project.sh
--- 1. a group directory without setgid: new files get the creator's own group
drwxrwx--- 2 cons1 cons 4096 Oct  7 18:42 /srv/lab10/project/consult
-rw-r--r-- 1 cons1 cons1 8 Oct  7 18:42 report.txt
bash: line 1: /srv/lab10/project/consult/report.txt: Permission denied
--- 2. chmod g+s: new files inherit the directory's group; umask 002 lets the group write
drwxrws--- 2 cons1 cons 4096 Oct  7 18:42 /srv/lab10/project/consult
total 16
drwxrwsr-x 2 cons1 cons  4096 Oct  7 18:42 notes
-rw-r--r-- 1 cons1 cons     8 Oct  7 18:42 plan-022.txt
-rw-rw-r-- 1 cons1 cons     8 Oct  7 18:42 plan.txt
-rw-r--r-- 1 cons1 cons1    8 Oct  7 18:42 report.txt
bash: line 1: /srv/lab10/project/consult/plan-022.txt: Permission denied
cons2: appended to plan.txt
draft 2
cons2 agrees
--- 3. the group minus one person: setfacl -m u:cons3:--- plan.txt
-rw-rw-r--+ 1 cons1 cons 21 Oct  7 18:42 plan.txt
# file: plan.txt
# owner: cons1
# group: cons
user::rw-
user:cons3:---
group::rw-
mask::rw-
other::r--

cat: /srv/lab10/project/consult/plan.txt: Permission denied
draft 2
cons2 agrees
```

Step 1: without setgid, `report.txt` belongs to `cons1`'s private group, and `cons2` cannot append to it. Step 2: after `chmod g+s` the new files and the new directory `notes` belong to `cons` (and `notes` inherited the setgid bit, `rws`), but only `plan.txt`, created with umask `002`, is group-writable; `plan-022.txt` is not. `cons3`, a member of `cons`, can still read `plan.txt`. Step 3: one ACL entry excludes `cons3`, although `cons3` is in the group that may read and write: the named user entry matches before the groups. `ls -l` shows the `+`. The output continues:

```console
--- 4. the mask limits every named entry and the group: chmod g-w plan.txt
-rw-r--r--+ 1 cons1 cons 21 Oct  7 18:42 plan.txt
# file: plan.txt
# owner: cons1
# group: cons
user::rw-
user:cons3:---
group::rw-			#effective:r--
mask::r--
other::r--

bash: line 1: /srv/lab10/project/consult/plan.txt: Permission denied
--- 5. a default ACL on the directory: setfacl -d -m u:cons3:---,g::rwx consult
# file: srv/lab10/project/consult
# owner: cons1
# group: cons
# flags: -s-
user::rwx
group::rwx
other::---
default:user::rwx
default:user:cons3:---
default:group::rwx
default:mask::rwx
default:other::---

-rw-rw----+ 1 cons1 cons 7 Oct  7 18:42 budget.txt
# file: budget.txt
# owner: cons1
# group: cons
user::rw-
user:cons3:---
group::rwx			#effective:rw-
mask::rw-
other::---

cat: /srv/lab10/project/consult/budget.txt: Permission denied
budget
--- 6. where the ACL is stored: extended attributes of the inode
plan.txt {'system.posix_acl_access': 44}
budget.txt {'system.posix_acl_access': 44}
notes {}
/srv/lab10/project/consult {'system.posix_acl_default': 44}
```

Step 4: `chmod g-w` did not touch `group::rw-`; it lowered the mask to `r--`, and the effective right of the group became `r--`, so `cons2` can no longer append. Step 5: with a default ACL on the directory, `cons1` created `budget.txt` with the strict umask `077`, yet the file is `rw-rw----` for the group and closed to `cons3`: the default ACL replaced the umask, and the requested mode `0666` limited the mask to `rw-`. (`# flags: -s-` is `getfacl`'s way of showing the setgid bit.) Step 6: the ACLs are 44-byte extended attributes, a 4-byte header and 8 bytes for each of the five entries; `notes`, created before the default ACL, has none.

### Is there a MAC policy on this machine?

```console
# ./lsm.sh
--- compiled-in security modules (kernel configuration):
CONFIG_SECURITY_SELINUX=y
# CONFIG_SECURITY_APPARMOR is not set
CONFIG_LSM="landlock,lockdown,yama,loadpin,safesetid,integrity,selinux,smack,tomoyo,apparmor,bpf"
--- the modules actually active, in the order the kernel calls them (securityfs):
lockdown,capability,landlock,selinux,bpf
--- labels as the tools see them:
? /etc/passwd
LABEL                             PID TTY          TIME CMD
kernel                              1 ?        00:00:01 process_api
kernel                              2 ?        00:00:00 kthreadd
id: --context (-Z) works only on an SELinux-enabled kernel
--- the SELinux kernel interface (selinuxfs):
enforce = 0
policy loaded: no
booleans defined: 0
```

The kernel of this virtual machine contains SELinux and has it among the active LSMs, but no policy was ever loaded: every process carries the initial label `kernel`, files have no label (`?`), there are no booleans, and nothing is enforced. Capabilities are an LSM too (`capability` in the list). The commodity Ubuntu installation would show AppArmor instead; a Fedora or RHEL installation shows a full SELinux setup, which the next part explores.

### SELinux on a Fedora, RHEL or AlmaLinux virtual machine

The following lab needs a virtual machine with Fedora, Red Hat Enterprise Linux, AlmaLinux or Rocky Linux (SELinux enforcing by default). The commands are given **without output**: run them and interpret what you see, following the explanations of the [SELinux section](#selinux-labels-and-type-enforcement).

```console
$ getenforce; sestatus                       # mode and policy (expect: Enforcing, targeted)
$ id -Z; ps -eZ | head; ls -Z /etc/shadow    # your context, process domains, a file label
$ sudo dnf install -y httpd policycoreutils-python-utils setroubleshoot-server
$ sudo systemctl enable --now httpd
$ ps -eZ | grep httpd                        # the domain of the web server
$ ls -Zd /var/www/html; sudo semanage fcontext -l | grep '/var/www'

# 1. the mv trap
$ echo 'hello from home' > ~/index.html
$ sudo mv ~/index.html /var/www/html/
$ ls -Z /var/www/html/index.html             # which type did it keep?
$ curl -i http://localhost/index.html        # status code?
$ sudo ausearch -m AVC -ts recent            # the denial: scontext, tcontext, tclass
$ sudo sealert -a /var/log/audit/audit.log   # the explanation and the suggested fix
$ sudo restorecon -v /var/www/html/index.html
$ curl -i http://localhost/index.html

# 2. a web root outside /var/www: temporary and persistent labels
$ sudo mkdir /web; echo 'web root' | sudo tee /web/index.html
$ sudo chcon -R -t httpd_sys_content_t /web; ls -Z /web
$ sudo restorecon -Rv /web; ls -Z /web       # chcon is undone
$ sudo semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'
$ sudo restorecon -Rv /web; ls -Z /web       # now the policy agrees

# 3. ports are labelled too
$ sudo semanage port -l | grep -w http_port_t
$ echo 'Listen 3131' | sudo tee /etc/httpd/conf.d/port3131.conf
$ sudo systemctl restart httpd               # fails: why? (journalctl -xeu httpd, ausearch)
$ sudo semanage port -a -t http_port_t -p tcp 3131
$ sudo systemctl restart httpd; curl -s http://localhost:3131/ | head -3

# 4. booleans and modes
$ getsebool -a | grep httpd | head -20
$ sudo setsebool -P httpd_enable_homedirs on; getsebool httpd_enable_homedirs
$ sudo setenforce 0; getenforce; sudo setenforce 1; getenforce
```

Clean up with `sudo rm /etc/httpd/conf.d/port3131.conf`, `sudo semanage port -d -t http_port_t -p tcp 3131`, `sudo semanage fcontext -d '/web(/.*)?'` and `sudo setsebool -P httpd_enable_homedirs off`. On an Ubuntu virtual machine the AppArmor counterparts are `sudo aa-status`, the profiles in `/etc/apparmor.d/`, and `aa-complain`/`aa-enforce` (package `apparmor-utils`).

## Lab exercises

1. **Predict, then test.** For each of the modes `d--x--x--x`, `dr--r--r--`, `d-wx-wx-wx` and `drwx-wx-wx` of a directory owned by root, predict whether `user1` can `ls`, `ls -l`, `cd`, read a known file, create and delete a file in it. Check your predictions by extending `dirperms.sh` with an `ls -l` column. What does `ls -l` print for `dr--r--r--`, and why?
2. **Octal drill.** Convert to octal: `rwxr-sr-x`, `rw-r--r-T`, `r-sr-x--x`, `rwSrwSrwT`; and to strings: `4711`, `2770`, `1755`, `6555`. Verify each answer with `chmod` and `stat -c '%a %A'`. Which of the eight modes contain a special bit that has no effect?
3. **A team directory.** Build `/srv/team` for a group `dev` (two users) and an auditor `audit1` who may read everything but change nothing, so that it works whatever umask the developers use. Use setgid and default ACLs. Then test what happens to the ACLs when a developer copies a file in with `cp`, with `cp -p`, and moves one in with `mv` from his home directory.
4. **Dropping privileges.** Change `showid.c` so that it opens the file with the effective UID, then calls `seteuid(getuid())`, and then tries to open the file again. What does the second attempt print, and why is this the recommended pattern? List the setuid and setgid programs of your system (`find / -perm /6000 -type f 2>/dev/null`) and explain for three of them why they need the bit.
5. **A capability instead of setuid root.** Copy `python3` to `./py`, try `./py -m http.server 80` as an ordinary user, then give the copy only `cap_net_bind_service` with `setcap` and try again. Can the same program now read `/etc/shadow`? Why is this better than making the copy setuid root?
6. **SELinux.** Do the four parts of the SELinux lab in a Fedora, RHEL or AlmaLinux virtual machine. For each denial, write down the source context, the target context, the object class and the permission from the AVC message, and which of the three kinds of fix (label, boolean, policy module) `sealert` suggested.
7. **AppArmor.** On an Ubuntu virtual machine, run `aa-status`, pick one confined program and read its profile in `/etc/apparmor.d/`. Write a profile for a small script of your own with `aa-genprof`, and show that a file it is not allowed to read is refused, also when the script runs as root.

## Review questions

1. What are the subject, the object and the action in an access decision? What is the access matrix, and how do ACLs and capability lists store it?
2. What three properties must a reference monitor have? Where is the reference monitor for files in Linux, and why can user programs not bypass it?
3. A request reaches a web server. Name the layers it passes before a file is read, and explain why each layer is useful even though the others exist.
4. A directory has mode `d---rwxrwx` and belongs to `john`. Can `john` list it? Can another user? Can `john` get access back, and how?
5. Which permissions does a user need to delete a file? Why can a user delete a file he cannot read, and what prevents this in `/tmp`?
6. A user has umask `027`. What modes do a new file created by an editor and a new directory get? Why does a umask never add permissions?
7. Convert `rwsr-S-wt` and `-wxrwsr-T` to octal, and `7640` to the `ls -l` notation. What does a capital `S` or `T` tell you?
8. Explain how `passwd` can change `/etc/shadow`. What are the real and the effective UID of the process? Why does the kernel ignore the setuid bit on scripts and on `nosuid` file systems?
9. What does the setgid bit do on a directory, and why is it often combined with umask `002` or a default ACL?
10. Why can root read a file with mode `000`? How do capabilities make it possible to give a program only part of root's power? Give two examples.
11. Why can mode bits not express "the group `cons` except `cons3`"? Show the ACL that does, and explain the order in which the kernel checks its entries.
12. What is the ACL mask? What happens to a file's ACL when you run `chmod g-w` or `chmod 600` on it?
13. Contrast DAC and MAC. Why can DAC not stop a Trojan horse, and how does MAC limit the damage of a hijacked web server running as root?
14. Read the context `system_u:object_r:httpd_sys_content_t:s0` field by field. What does the rule `allow httpd_t httpd_sys_content_t:file { read open getattr };` permit, and what happens to accesses that no rule mentions?
15. A web page moved from a home directory to `/var/www/html` gives "403 Forbidden", although its mode is `644`. Explain the cause, how to confirm it, and the right fix. Why is `chcon` not a permanent fix, and what is?
16. What is the difference between permissive and disabled mode? Why is switching SELinux off a poor answer to a denial?

<details>
<summary><strong>Answer key (for instructors)</strong></summary>

1. Subject: the process (acting for a user); object: file, directory, device, port, process; action: read, write, execute, delete, bind, signal. The access matrix has subjects as rows, objects as columns, allowed actions in the cells. ACLs store it by column (with the object), capability lists by row (with the subject).
2. Always invoked (complete mediation), tamper-proof, small enough to verify. In the kernel, in the system calls (`open`, `unlink`, …); user code runs in user mode and can reach files only through system calls, which the kernel executes in kernel mode.
3. Firewall (reachability), service configuration and authentication, DAC (files of the service's user), MAC (system policy), execution. Each layer covers the failure of the others: a bug in the service is contained by DAC and MAC; a permission mistake by MAC; a wrong MAC label by DAC; the firewall keeps unneeded services unreachable.
4. `john` cannot (the owner triplet `---` decides, others' `rwx` does not help). Users outside the group can (others `rwx`); members of the group too (group `rwx`). `john` is the owner and may `chmod u+rwx` it.
5. `w` and `x` on the directory; nothing on the file. Deletion removes a directory entry, a change of the directory. The sticky bit (`1777`) allows deletion and renaming only to the file's owner, the directory's owner and root.
6. Files: 666 AND NOT 027 = `640` (`rw-r-----`); directories: 777 AND NOT 027 = `750`. The umask is subtracted (AND NOT) from the mode the program requests.
7. `7743` and `3374`; `7640` is `-rwSr-S--T`. A capital letter means the special bit is set but the corresponding `x` is not, so it usually has no effect.
8. `passwd` is owned by root and setuid (`4755`); the process runs with effective UID 0 and real UID of the user, who can change only his own entry. For scripts there is a race between the kernel reading `#!` and the interpreter opening the file, which could be swapped; `nosuid` mounts prevent bringing setuid programs on removable or untrusted media.
9. New files and subdirectories get the directory's group (subdirectories also the setgid bit). Setgid fixes the group, not the bits: the group can write only if the creator's umask keeps `g+w` (`002`) or a default ACL grants it.
10. Root has `CAP_DAC_OVERRIDE` (and `CAP_DAC_READ_SEARCH`), which skip the permission bits. Capabilities split root's powers; a program can keep or get only some: `cap_net_bind_service` for a web server on port 80, `cap_dac_read_search` for a backup reader, `cap_chown` for a file service. Dropping both DAC capabilities makes root obey the bits (measured).
11. There are only three classes; `cons3` is in the group class like `cons1` and `cons2`. ACL: `user::rw-, user:cons3:---, group::rw-, mask::rw-, other::---`. Order: owner → named users → owning group and named groups (any match grants, after the mask) → others; the first matching step decides.
12. The upper limit for named users, named groups and the owning group; with an ACL, the group triplet of the mode is the mask. `chmod g-w` removes `w` from the mask (entries stay, effective rights shrink); `chmod 600` sets the mask to `---`, disabling all named entries and the owning group.
13. DAC: the owner (and every program he runs) decides; MAC: a system policy decides, and binds root too. A Trojan horse runs with the user's rights, so DAC considers its actions legitimate. MAC confines the web server's domain to web content and web ports; a hijacked server cannot read database files, home directories or `/etc/shadow`, even as root.
14. SELinux user `system_u`, role `object_r` (files), type `httpd_sys_content_t`, level `s0`. Processes in domain `httpd_t` may read, open and stat files of that type. Anything not allowed by a rule is denied and logged as an AVC denial.
15. `mv` keeps the inode's old label `user_home_t`, which `httpd_t` may not read. Confirm with `ls -Z` and `ausearch -m AVC` (tcontext `user_home_t`) or `sealert`. Fix: `restorecon -v` (or copy with `cp` instead of `mv`). `chcon` changes only the file's label, which the next relabel or `restorecon` reverts; persistent: `semanage fcontext -a -t … 'path(/.*)?'` then `restorecon -Rv`.
16. Permissive: the policy is loaded and labels are maintained, denials are only logged; disabled: no labels, no checks, and returning requires a full relabel. Disabling removes the MAC layer for every service; the real cause is usually a label or a boolean, and fixing it keeps the protection.

**Lab answers.** Lab 1: `--x` everywhere: no `ls`, `cd` and reading known names work, no create/delete; `r--`: names listed, `ls -l` prints `?` for all fields (and "Permission denied" for each entry) because the inodes cannot be reached without `x`; `-wx`: create/delete/open by name, no listing; `rwx-wx-wx` for others is `-wx`. Lab 2: `2755`, `1644`, `4551`, `7666`; `-rws--x--x`, `-rwxrws---`, `-rwxr-xr-t`, `-r-sr-sr-x`. Without effect: every capital letter (`T` in `1644`, all three in `7666`, which shows as `rwSrwSrwT`) and, on a regular file, the sticky bit in general (`1755`), which Linux ignores for files. Lab 3: `chmod 2770`, `setfacl -m g:dev:rwx,u:audit1:r-x` and `setfacl -d -m g:dev:rwx,u:audit1:r-x`; `cp` creates a new file and applies the default ACL; `cp -p` copies the source's mode and ACL instead; `mv` keeps the inode with its old ACL and group. Lab 4: the second open fails with "Permission denied": after `seteuid(getuid())` the process uses `user1`'s rights; dropping privileges as early as possible limits what a bug in the rest of the program can do. Lab 5: binding port 80 fails without, succeeds with `cap_net_bind_service`; `/etc/shadow` remains unreadable, because the copy has no DAC capability; a setuid-root copy would let any user run arbitrary Python code as root (for example `os.setuid(0)` followed by any command).

</details>

## References

Anderson, J. P. (1972). *Computer security technology planning study* (ESD-TR-73-51, Vol. II). Electronic Systems Division, Air Force Systems Command.

Bell, D. E., & LaPadula, L. J. (1976). *Secure computer system: Unified exposition and Multics interpretation* (MTR-2997 Rev. 1, ESD-TR-75-306). The MITRE Corporation.

Grünbacher, A. (2003). POSIX access control lists on Linux. In *Proceedings of the FREENIX Track: 2003 USENIX Annual Technical Conference*. USENIX Association. https://www.usenix.org/legacy/events/usenix03/tech/freenix03/full_papers/gruenbacher/gruenbacher_html/index.html

Kerrisk, M. (2010). *The Linux programming interface: A Linux and UNIX system programming handbook*. No Starch Press.

Lampson, B. W. (1974). Protection. *ACM SIGOPS Operating Systems Review, 8*(1), 18–24. https://doi.org/10.1145/775265.775268

Linux man-pages project. (n.d.-a). *acl(5): Access control lists*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man5/acl.5.html

Linux man-pages project. (n.d.-b). *capabilities(7): Overview of Linux capabilities*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man7/capabilities.7.html

Linux man-pages project. (n.d.-c). *chmod(1): Change file mode bits*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man1/chmod.1.html

Linux man-pages project. (n.d.-d). *setfacl(1): Set file access control lists*. Retrieved October 7, 2026, from https://man7.org/linux/man-pages/man1/setfacl.1.html

Loscocco, P., & Smalley, S. (2001). Integrating flexible support for security policies into the Linux operating system. In *Proceedings of the FREENIX Track: 2001 USENIX Annual Technical Conference*. USENIX Association. https://www.usenix.org/legacy/events/usenix01/freenix01/loscocco.html

Microsoft. (n.d.-a). *Access control lists*. Retrieved October 7, 2026, from https://learn.microsoft.com/en-us/windows/win32/secauthz/access-control-lists

Microsoft. (n.d.-b). *Mandatory integrity control*. Retrieved October 7, 2026, from https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control

Red Hat. (n.d.). *Using SELinux: Red Hat Enterprise Linux 9*. Retrieved October 7, 2026, from https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/index

Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proceedings of the IEEE, 63*(9), 1278–1308. https://doi.org/10.1109/PROC.1975.9939

Smalley, S., Vance, C., & Salamon, W. (2001). *Implementing SELinux as a Linux security module* (NAI Labs Report #01-043). NAI Labs.

Wright, C., Cowan, C., Smalley, S., Morris, J., & Kroah-Hartman, G. (2002). Linux security modules: General security support for the Linux kernel. In *Proceedings of the 11th USENIX Security Symposium* (pp. 17–31). USENIX Association.

## Further reading

Arpaci-Dusseau, R. H., & Arpaci-Dusseau, A. C. (2023). *Operating systems: Three easy pieces* (Version 1.10). Arpaci-Dusseau Books. https://pages.cs.wisc.edu/~remzi/OSTEP/ (chapter 39 on files and directories, including permissions)

Mayer, F., MacMillan, K., & Caplan, D. (2006). *SELinux by example: Using security enhanced Linux*. Prentice Hall.

The kernel development community. (n.d.). *Linux Security Module development*. The Linux Kernel documentation. https://docs.kernel.org/security/lsm-development.html
