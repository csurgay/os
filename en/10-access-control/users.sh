#!/bin/sh
# users.sh - create the users and groups of the demos (needs root; safe to run twice)
# john, user1, user2: ordinary users, each with a private group of the same name
# cons1, cons2, cons3: consultants, each in its own private group and in the shared group "cons"
groupadd -f cons
for u in john user1 user2; do
    id "$u" >/dev/null 2>&1 || useradd -m -s /bin/bash "$u"
done
for u in cons1 cons2 cons3; do
    id "$u" >/dev/null 2>&1 || useradd -m -s /bin/bash -G cons "$u"
done
mkdir -p /srv/lab10
for u in john user1 user2 cons1 cons2 cons3; do id "$u"; done
