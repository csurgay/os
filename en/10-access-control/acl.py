#!/usr/bin/env python3
"""acl.py - a minimal stand-in for getfacl/setfacl, for machines that have libacl but not the acl package.

It calls the same library functions as getfacl and setfacl (libacl.so.1, POSIX.1e draft):
acl_get_file, acl_to_any_text, acl_from_text, acl_calc_mask, acl_valid, acl_set_file.

  acl.py get    [-d] FILE...          like  getfacl FILE...   (-d: only the default ACL)
  acl.py set    [-d] FILE ACL         like  setfacl [-d] --set ACL FILE
  acl.py modify [-d] FILE ENTRIES     like  setfacl [-d] -m ENTRIES FILE
  acl.py remove      FILE             like  setfacl -b FILE

ACL and ENTRIES use the setfacl syntax, e.g.  u::rwx,g::rwx,o::---  or  u:cons3:---,g:audit:r-x
As setfacl does, "modify" recomputes the mask and, for a default ACL that does not exist yet,
starts from a copy of the access ACL.
"""
import ctypes
import os
import pwd
import grp
import stat
import sys

ACL_TYPE_ACCESS, ACL_TYPE_DEFAULT = 0x8000, 0x4000
TEXT_SOME_EFFECTIVE, TEXT_SMART_INDENT = 0x01, 0x04     # from <acl/libacl.h>, as getfacl uses them

lib = ctypes.CDLL("libacl.so.1", use_errno=True)
lib.acl_get_file.restype = ctypes.c_void_p
lib.acl_get_file.argtypes = [ctypes.c_char_p, ctypes.c_uint]
lib.acl_from_text.restype = ctypes.c_void_p
lib.acl_from_text.argtypes = [ctypes.c_char_p]
lib.acl_to_any_text.restype = ctypes.c_void_p
lib.acl_to_any_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char, ctypes.c_int]
lib.acl_calc_mask.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
lib.acl_valid.argtypes = [ctypes.c_void_p]
lib.acl_set_file.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_void_p]
lib.acl_delete_def_file.argtypes = [ctypes.c_char_p]
lib.acl_free.argtypes = [ctypes.c_void_p]
lib.acl_entries.argtypes = [ctypes.c_void_p]


def fail(what, path):
    e = ctypes.get_errno()
    sys.exit(f"acl.py: {path}: {what}: {os.strerror(e)}")


def get_text(path, kind, options=0):
    """The ACL of PATH as text, one entry per line ('' for an empty default ACL)."""
    acl = lib.acl_get_file(path.encode(), kind)
    if not acl:
        fail("cannot read ACL", path)
    try:
        if lib.acl_entries(acl) == 0:
            return ""
        t = lib.acl_to_any_text(acl, None, b"\n", options)
        s = ctypes.string_at(t).decode()
        lib.acl_free(t)
        return s if s.endswith("\n") else s + "\n"
    finally:
        lib.acl_free(acl)


def set_text(path, kind, text, recalc=True):
    acl = ctypes.c_void_p(lib.acl_from_text(text.encode()))
    if not acl.value:
        sys.exit(f"acl.py: invalid ACL text: {text}")
    if recalc and lib.acl_calc_mask(ctypes.byref(acl)) != 0:
        fail("cannot compute mask", path)
    if lib.acl_valid(acl) != 0:
        sys.exit(f"acl.py: {path}: invalid ACL: {text}")
    if lib.acl_set_file(path.encode(), kind, acl) != 0:
        fail("cannot set ACL", path)
    lib.acl_free(acl)


LONG = {"u": "user", "g": "group", "o": "other", "m": "mask"}


def parse(text):
    """'u:cons3:---,g::rwx' -> {('user','cons3'): '---', ('group',''): 'rwx'}"""
    out = {}
    for e in text.replace("\n", ",").split(","):
        e = e.split("#")[0].strip()
        if not e:
            continue
        tag, qual, perm = (e.split(":") + ["", ""])[:3]
        if tag in ("o", "other", "m", "mask") and perm == "" and qual:   # "o:r-x" short form
            qual, perm = "", qual
        tag = LONG.get(tag, tag)
        perm = "".join(c if c in perm else "-" for c in "rwx")
        out[(tag, qual)] = perm
    return out


def unparse(d):
    order = {"user": 0, "group": 2, "mask": 4, "other": 5}
    key = lambda item: (order[item[0][0]] + (1 if item[0][1] else 0), item[0][1])
    return ",".join(f"{t}:{q}:{p}" for (t, q), p in sorted(d.items(), key=key))


def cmd_get(paths, default):
    for p in paths:
        st = os.lstat(p)
        flags = "".join(c if st.st_mode & b else "-" for c, b in
                        (("s", stat.S_ISUID), ("s", stat.S_ISGID), ("t", stat.S_ISVTX)))
        print(f"# file: {p.lstrip('/')}")
        print(f"# owner: {pwd.getpwuid(st.st_uid).pw_name}")
        print(f"# group: {grp.getgrgid(st.st_gid).gr_name}")
        if flags != "---":
            print(f"# flags: {flags}")
        opts = TEXT_SOME_EFFECTIVE | TEXT_SMART_INDENT
        if not default:
            print(get_text(p, ACL_TYPE_ACCESS, opts), end="")
        if stat.S_ISDIR(st.st_mode):
            d = get_text(p, ACL_TYPE_DEFAULT, opts)
            print("".join("default:" + line + "\n" for line in d.splitlines()), end="")
        print()


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, args = argv[1], argv[2:]
    default = "-d" in args
    args = [a for a in args if a != "-d"]
    kind = ACL_TYPE_DEFAULT if default else ACL_TYPE_ACCESS
    if cmd == "get":
        cmd_get(args, default)
    elif cmd == "set":
        set_text(args[0], kind, unparse(parse(args[1])))
    elif cmd == "modify":
        cur = parse(get_text(args[0], kind))
        if default and not cur:
            cur = parse(get_text(args[0], ACL_TYPE_ACCESS))
        cur.pop(("mask", ""), None)
        cur.update(parse(args[1]))
        set_text(args[0], kind, unparse(cur))
    elif cmd == "remove":              # keep only the base entries: owner, owning group, others
        base = {k: v for k, v in parse(get_text(args[0], ACL_TYPE_ACCESS)).items()
                if not k[1] and k[0] != "mask"}
        set_text(args[0], ACL_TYPE_ACCESS, unparse(base), recalc=False)
        if stat.S_ISDIR(os.stat(args[0]).st_mode) and lib.acl_delete_def_file(args[0].encode()) != 0:
            fail("cannot remove default ACL", args[0])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
