#!/usr/bin/env python3
"""G-CONF for django__django-13658.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_progName` (the Lean impl, transliterated
op-for-op per refinement.md, with `basename` / `computeProgName` reproducing the
deep-modeled path-basename + module-entry special case) against the REAL patched
program-name computation over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Real target
-----------
The fix makes the utility present a program name that is a function of the
utility's OWN argument vector, not the ambient process argument vector. In the
patched source, `ManagementUtility(argv).prog_name` is exactly the program name
threaded into the option parser (`prog=self.prog_name`). We therefore take the
real observable as `ManagementUtility(argv).prog_name`, evaluated while the
ambient `sys.argv` is mocked to an UNRELATED vector — this simultaneously (a)
validates the deep basename/special-case model against the real computation and
(b) exercises the fixed property that the presented name does not depend on the
ambient vector.

Type bijection (mapping.md):
  argv     : list[str] <-> List String   (one element per argument)
  ambient  : list[str] <-> List String   (the process-global argument vector)
  result   : str       <-> String        (the presented program name)

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib + django only.
"""
import os
import random
import sys
from unittest import mock


# --- shadow: R/I transliteration of implementation_progName -----------------
def basename(s):
    # (s.splitToList (· = '/')).reverse.headI  ==  os.path.basename on POSIX
    return s.split('/')[-1]


def compute_prog_name(arg0):
    b = basename(arg0)
    return 'python -m django' if b == '__main__.py' else b


def shadow_prog_name(argv, _ambient):
    # let mut progName := basename argv.headI
    prog_name = basename(argv[0])
    # if progName = "__main__.py" then progName := "python -m django"
    if prog_name == '__main__.py':
        prog_name = 'python -m django'
    return prog_name


# --- the real patched computation -------------------------------------------
from django.core.management import ManagementUtility


def real_prog_name(argv, ambient):
    # Mock the ambient process argv to an UNRELATED vector; the patched utility
    # must present a name derived from `argv`, not from `ambient`.
    with mock.patch.object(sys, 'argv', list(ambient)):
        return ManagementUtility(list(argv)).prog_name


# --- fuzz corpus -------------------------------------------------------------
NAME_POOL = [
    'django-admin', 'manage.py', 'django-admin.py', '__main__.py',
    'py', 'a', '', 'x.y', 'foo.bar.baz', 'sub command',
]
DIR_POOL = ['', '/', 'usr', 'usr/local/bin', './', '../parent', 'a/b/c', 'trailing/']


def gen_arg0(rng):
    parts = []
    for _ in range(rng.randint(0, 3)):
        parts.append(rng.choice(DIR_POOL).strip('/'))
    parts = [p for p in parts if p != '']
    leading = '/' if rng.random() < 0.4 else ''
    trailing = '/' if rng.random() < 0.15 else ''
    body = '/'.join(parts + [rng.choice(NAME_POOL)])
    return leading + body + trailing


def gen_argv(rng):
    # argv is non-empty (precondition argv ≠ []); extra args are irrelevant to
    # the program name but included to mirror real invocations.
    n = rng.randint(0, 3)
    return [gen_arg0(rng)] + [rng.choice(NAME_POOL) for _ in range(n)]


def main():
    rng = random.Random(13658)
    N = 100_000
    fixed = [
        (['django-admin', 'help', 'shell'], [None, 'help', 'shell']),
        (['django-admin'], ['manage.py']),
        (['/usr/local/bin/django-admin.py'], ['x']),
        (['manage.py', 'migrate'], ['django-admin']),
        (['/a/b/__main__.py'], ['django-admin']),
        (['__main__.py'], ['manage.py']),
        ([''], ['django-admin']),
        (['/'], ['x']),
        (['a/b/'], ['x']),
    ]
    disagreements = 0
    examples = []

    def check(argv, ambient):
        nonlocal disagreements
        want = shadow_prog_name(argv, ambient)
        got = real_prog_name(argv, ambient)
        if want != got:
            disagreements += 1
            if len(examples) < 5:
                examples.append((argv, ambient, want, got))

    for argv, ambient in fixed:
        check(argv, ambient)
    for _ in range(N):
        argv = gen_argv(rng)
        # ambient is deliberately an unrelated vector (may even be [None])
        ambient = [rng.choice([None] + NAME_POOL)] + [rng.choice(NAME_POOL)
                                                      for _ in range(rng.randint(0, 2))]
        check(argv, ambient)

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreement(s)")
        for argv, ambient, want, got in examples:
            print(f"  argv={argv!r} ambient={ambient!r} shadow={want!r} real={got!r}")
        sys.exit(1)
    print(f"G-CONF PASS: {N + len(fixed)} inputs, 0 disagreements (seed 13658)")
    sys.exit(0)


if __name__ == "__main__":
    main()
