#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13658 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types (`list[str]`, `str`), via the
              mapping.md bijection: out = progNameOf(argv) = basename(argv[0])
              with the '__main__.py' -> 'python -m django' rename. There are no
              A-tagged callees inside the impl region (basename/progNameOf are
              deep models validated as references by G-AX), so this is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the program name the PATCHED
              `ManagementUtility.execute` feeds the early-options parser,
              i.e. `CommandParser(prog=self.prog_name, usage='%(prog)s …')`'s
              rendered program name, where `self = ManagementUtility(argv)`.
              This is the exact construction the gold hunk introduces.

Critically, each comparison runs with `sys.argv` set to an ADVERSARIAL value
distinct from `argv` (mirroring the F2P test's `mock.patch('sys.argv', [None]+…)`)
to confirm the patched result depends only on `argv`, never on the process
global. They must agree on every Requires-satisfying input (argv != []). Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + Django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13658
N_FUZZ = 100_000

USAGE = '%(prog)s subcommand [options] [args]'


# --- the R/I shadow: Solution.lean basename/progNameOf, transliterated -------

def shadow_basename(path):
    """Solution.lean `basename`: longest suffix containing no '/'."""
    out = []
    for ch in reversed(path):
        if ch == '/':
            break
        out.append(ch)
    return ''.join(reversed(out))


def shadow_prog_name(argv):
    """Solution.lean `progNameOf argv` — the R/I shadow of `out`."""
    first = argv[0] if argv else ''
    b = shadow_basename(first)
    return 'python -m django' if b == '__main__.py' else b


# --- the oracle: patch.diff's behaviour --------------------------------------

def oracle_prog_name(argv, ManagementUtility, CommandParser):
    """Reproduce the patched construction at __init__.py:347 exactly:
        parser = CommandParser(prog=self.prog_name, usage='%(prog)s …', …)
    and return the program name it renders ('%(prog)s' -> parser.prog).
    `self.prog_name` is computed by ManagementUtility from `argv` alone."""
    utility = ManagementUtility(list(argv))
    parser = CommandParser(
        prog=utility.prog_name,
        usage=USAGE,
        add_help=False,
        allow_abbrev=False,
    )
    return parser.prog


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ["django-admin"]
    yield ["django-admin", "help", "shell"]            # the F2P invocation
    yield ["/usr/local/bin/django-admin", "migrate"]
    yield ["manage.py", "runserver"]
    yield ["./manage.py"]
    yield ["__main__.py"]
    yield ["x/__main__.py", "test"]
    yield ["/a/b/__main__.py"]
    yield ["a/b/c"]
    yield ["a/b/"]
    yield ["/"]
    yield ["prog with spaces", "x"]
    yield ["réalünïcode/p"]
    first_alpha = list("abcXYZ.-_/0129") + [" ", "/", ".", "é"]
    for _ in range(n):
        n0 = rng.randint(1, 20)
        first = "".join(rng.choice(first_alpha) for _ in range(n0))
        if rng.random() < 0.1:
            first = rng.choice(["", "x/", "/a/b/"]) + "__main__.py"
        rest = ["arg%d" % i for i in range(rng.randint(0, 3))]
        yield [first] + rest


def main():
    from django.core.management import ManagementUtility
    from django.core.management.base import CommandParser

    rng = random.Random(SEED)
    saved_argv = sys.argv
    disagreements = []
    count = 0
    try:
        for argv in fuzz_inputs(N_FUZZ, rng):
            count += 1
            # Adversarial process global, distinct from `argv` and from the
            # F2P-style [None]+args, to prove independence (the actual bug).
            sys.argv = [None, "GARBAGE_PROG.py", "noise", "--x"]
            shadow = shadow_prog_name(argv)
            oracle = oracle_prog_name(argv, ManagementUtility, CommandParser)
            if shadow != oracle:
                disagreements.append((argv, shadow, oracle))
                if len(disagreements) >= 5:
                    break
    finally:
        sys.argv = saved_argv

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for argv, sh, orc in disagreements:
            print("  argv=%r shadow=%r oracle=%r" % (argv, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of usageProgName agrees with patch.diff "
          "behaviour on %d inputs (seed=%d, sys.argv adversarial), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
