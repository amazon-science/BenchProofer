#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-7982.

The bundle consumes NO `axiom <callee>_prop`: the directory walk is the function
under spec (modeled deeply as the recursive `collectTree` / `implementation_visit`)
and `recurse` is an opaque caller-supplied predicate (a universally-quantified
function parameter). There is therefore no callee contract to validate and G-AX
is a SKIP.

For defensiveness we additionally confirm the ONE OS fact the R-tag in
refinement.md row 4 depends on — that `os.DirEntry.is_dir()` (default
follow_symlinks=True) follows a symlink to a directory while
`is_dir(follow_symlinks=False)` does not — using REAL filesystem symlinks. This
is not a consumed axiom; failure here would only indicate the type bijection is
mis-stated. stdlib-only. exit 0 on skip/sound.
"""
import json
import os
import sys
import tempfile


def check_is_dir_symlink_semantics() -> bool:
    with tempfile.TemporaryDirectory() as root:
        # a real directory
        realdir = os.path.join(root, "realdir")
        os.mkdir(realdir)
        # a regular file
        regfile = os.path.join(root, "regfile")
        with open(regfile, "w") as fh:
            fh.write("x")
        # a symlink pointing at the directory
        symdir = os.path.join(root, "symdir")
        os.symlink(realdir, symdir)
        # a symlink pointing at the file
        symfile = os.path.join(root, "symfile")
        os.symlink(regfile, symfile)

        by_name = {e.name: e for e in os.scandir(root)}
        ok = True
        # plain dir: is_dir true under both flags
        d = by_name["realdir"]
        ok &= d.is_dir() is True and d.is_dir(follow_symlinks=False) is True
        # regular file: false under both
        f = by_name["regfile"]
        ok &= f.is_dir() is False and f.is_dir(follow_symlinks=False) is False
        # symlinked dir: THE DISCRIMINATOR — follows under default, not under False
        sd = by_name["symdir"]
        ok &= sd.is_symlink() is True
        ok &= sd.is_dir() is True                          # post-patch: descends
        ok &= sd.is_dir(follow_symlinks=False) is False    # prepatch: skipped
        # symlinked file: never a dir
        sf = by_name["symfile"]
        ok &= sf.is_dir() is False and sf.is_dir(follow_symlinks=False) is False
        return ok


def main() -> int:
    result = {"gate": "G-AX", "instance": "pytest-dev__pytest-7982",
              "consumed_axioms": []}
    try:
        sound = check_is_dir_symlink_semantics()
    except OSError as exc:
        # No symlink support (rare in container) — still a valid SKIP since no
        # axiom is consumed.
        result["status"] = "skip"
        result["note"] = f"no consumed axiom; symlink probe unavailable ({exc})"
        print(json.dumps(result))
        return 0
    if not sound:
        result["status"] = "fail"
        result["note"] = "is_dir() follow_symlinks bijection (mapping.md) violated"
        print(json.dumps(result))
        return 1
    result["status"] = "skip"
    result["note"] = ("no consumed axiom; deep models only. is_dir() "
                      "follow-symlinks bijection confirmed on real symlinks.")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
