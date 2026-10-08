#!/bin/sh
# acl-project.sh - a shared project directory for the group "cons": setgid, umask, then ACLs
# ACL="setfacl/getfacl"; this machine has only libacl, so acl.py (same library calls) stands in:
#   acl.py get F          =  getfacl F
#   acl.py modify F E     =  setfacl -m E F
#   acl.py modify -d D E  =  setfacl -d -m E D
ACL="python3 $(cd "$(dirname "$0")" && pwd)/acl.py"
P=/srv/lab10/project/consult
rm -rf /srv/lab10/project; mkdir -p $P; chmod 755 /srv/lab10/project
chown cons1:cons $P; chmod 0770 $P
cd $P
echo "--- 1. a group directory without setgid: new files get the creator's own group"
ls -ld $P
su cons1 -c "umask 022; echo 'draft 1' > $P/report.txt"
ls -l report.txt
su cons2 -c "echo 'cons2 agrees' >> $P/report.txt"
echo "--- 2. chmod g+s: new files inherit the directory's group; umask 002 lets the group write"
chmod g+s $P; ls -ld $P
su cons1 -c "umask 022; echo 'draft 2' > $P/plan-022.txt"
su cons1 -c "umask 002; echo 'draft 2' > $P/plan.txt"
su cons1 -c "mkdir $P/notes"
ls -l
su cons2 -c "echo 'cons2 agrees' >> $P/plan-022.txt"
su cons2 -c "echo 'cons2 agrees' >> $P/plan.txt && echo 'cons2: appended to plan.txt'"
su cons3 -c "cat $P/plan.txt"
echo "--- 3. the group minus one person: setfacl -m u:cons3:--- plan.txt"
$ACL modify plan.txt u:cons3:---
ls -l plan.txt
$ACL get plan.txt
su cons3 -c "cat $P/plan.txt"
su cons2 -c "cat $P/plan.txt"
echo "--- 4. the mask limits every named entry and the group: chmod g-w plan.txt"
chmod g-w plan.txt; ls -l plan.txt
$ACL get plan.txt
su cons2 -c "echo more >> $P/plan.txt"
chmod g+w plan.txt
echo "--- 5. a default ACL on the directory: setfacl -d -m u:cons3:---,g::rwx consult"
$ACL modify -d $P u:cons3:---,g::rwx
$ACL get $P
su cons1 -c "umask 077; echo 'budget' > $P/budget.txt"
ls -l budget.txt
$ACL get budget.txt
su cons3 -c "cat $P/budget.txt"
su cons2 -c "cat $P/budget.txt"
echo "--- 6. where the ACL is stored: extended attributes of the inode"
python3 -c "import os,sys
for f in sys.argv[1:]:
    print(f, {a: len(os.getxattr(f, a)) for a in os.listxattr(f)})" plan.txt budget.txt notes $P
