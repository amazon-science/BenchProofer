#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13658.

Both operations the program name is derived by are modeled DEEPLY in
Solution.lean (no consumed axiom); this script validates each deep model against
its REAL, UNCHANGED callee over boundary + fuzz inputs:

  (A-reference)  `basename`   (Solution.lean pure region)  ==  os.path.basename
  (A-reference)  `progNameOf` (Solution.lean pure region)  ==  the program name
                 a ManagementUtility records for a given argument vector
                 (os.path.basename(argv[0]) then '__main__.py' -> 'python -m django').

`basename`/`os.path.basename` is POSIX path-component logic; `progNameOf` adds
the module-entry-point rename. Imports only stdlib `os`/`random` and Django's
`ManagementUtility` (the real callee site, unchanged by the patch). Exit 0 iff
every obligation holds.
"""
import os
import random
import sys


# --- Solution.lean deep-model reference encodings ----------------------------

def basename_model(path):
    """Reference impl of Solution.lean `basename`: longest suffix with no '/'.
    (path.reverse.takeWhile (· ≠ '/')).reverse"""
    out = []
    for ch in reversed(path):
        if ch == '/':
            break
        out.append(ch)
    return ''.join(reversed(out))


def prog_name_model(argv):
    """Reference impl of Solution.lean `progNameOf`: basename of the first
    entry, with the '__main__.py' -> 'python -m django' rename."""
    first = argv[0] if argv else ''
    b = basename_model(first)
    return 'python -m django' if b == '__main__.py' else b


# --- the checks --------------------------------------------------------------

def check_basename(path):
    observed = os.path.basename(path)          # real callee
    expected = basename_model(path)            # deep model
    assert observed == expected, (
        "basename deep model unsound on %r: os.path.basename gave %r, "
        "deep model gives %r" % (path, observed, expected))


def check_prog_name(argv, ManagementUtility):
    # Real callee: the prog_name a ManagementUtility records for this vector.
    # __init__ does `self.argv = argv or sys.argv[:]`, so a NON-EMPTY argv is
    # used verbatim (the precondition `argv != []` in Solution.lean mirrors
    # this; an empty vector falls back to sys.argv and is out of scope).
    real = ManagementUtility(list(argv)).prog_name
    expected = prog_name_model(argv)           # deep model
    assert real == expected, (
        "progNameOf deep model unsound on %r: ManagementUtility.prog_name gave "
        "%r, deep model gives %r" % (argv, real, expected))


def main():
    # --- basename (A-reference): boundary cases ---------------------------
    basename_boundary = [
        "", "/", "//", "a", "a/b", "a/b/c", "a/b/", "/a", "/a/b",
        "django-admin", "/usr/bin/django-admin", "manage.py", "./manage.py",
        "__main__.py", "x/__main__.py", "/path/to/__main__.py",
        "a.b.c", "no_slash_here", "trailing/slash/", " ", "a b/c d",
        "réal/ünïcode", "weird\\path", "C:/win/style",
    ]
    for p in basename_boundary:
        check_basename(p)

    # --- basename (A-reference): randomized fuzz --------------------------
    rng = random.Random(13658)
    alphabet = list("abcXYZ.-_/0129") + [" ", "/", ".", "é", "•"]
    for _ in range(20000):
        n = rng.randint(0, 24)
        p = "".join(rng.choice(alphabet) for _ in range(n))
        check_basename(p)

    # --- progNameOf (A-reference): against real ManagementUtility ---------
    try:
        # Avoid argparse touching settings; ManagementUtility() construction
        # itself does not require configured settings.
        from django.core.management import ManagementUtility
    except Exception as exc:  # pragma: no cover - env guard
        print("G-AX SKIP-ENV: could not import ManagementUtility: %r" % exc)
        # In-container this import succeeds; treat absence as a hard failure
        # only when Django is expected. Re-raise to be safe.
        raise

    # Boundary vectors: the F2P invocation, module entry point, dotted/sliced
    # first entries, multi-arg vectors (only argv[0] matters for prog_name).
    progname_boundary = [
        ["django-admin"],
        ["django-admin", "help", "shell"],
        ["/usr/local/bin/django-admin", "migrate"],
        ["manage.py", "runserver"],
        ["./manage.py"],
        ["__main__.py"],
        ["/some/where/__main__.py", "test"],
        ["a/b/c", "x"],
        ["a/b/", "x"],
        ["/", "x"],
        ["weird name with spaces"],
        ["réalünïcode/prog"],
    ]
    for v in progname_boundary:
        check_prog_name(v, ManagementUtility)

    # randomized fuzz vectors
    first_alpha = list("abcXYZ.-_/0129") + [" ", "/", ".", "é"]
    for _ in range(3000):
        n0 = rng.randint(1, 20)
        first = "".join(rng.choice(first_alpha) for _ in range(n0))
        # occasionally hit the __main__.py rename branch exactly
        if rng.random() < 0.1:
            first = (rng.choice(["", "x/", "/a/b/"])) + "__main__.py"
        rest = ["arg%d" % i for i in range(rng.randint(0, 3))]
        check_prog_name([first] + rest, ManagementUtility)

    print("G-AX OK: basename deep model (== os.path.basename) sound on %d "
          "boundary + 20000 fuzz paths; progNameOf deep model (== "
          "ManagementUtility.prog_name) sound on %d boundary + 3000 fuzz "
          "vectors." % (len(basename_boundary), len(progname_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
