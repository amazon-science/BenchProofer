#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-7757.

The bundle models ONE behavior: how the default-value expressions of a parsed
function signature are aligned onto its positional parameters
(`signature_from_str` in `sphinx/util/inspect.py`). Its Lean implementation
(`implementation_positionalDefaults`) computes, for each positional parameter —
positional-only first (count `nPosonly`), then positional-or-keyword (count
`nArgs`) — the default it carries: `some text` or `none`. The supplied defaults
(`defaults`, in order) fill the RIGHTMOST positions across the whole positional
run:

    padded = [none]*(nPosonly + nArgs - len(defaults)) + [some d for d in defaults]

This script transliterates that R/I impl into Python (`shadow`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH alignment block of `signature_from_str` (the per-group loops that
left-pad `defaults` to the positional count and read `defaults[i]` /
`defaults[i + posonlyargs]`). A model-level default is represented by its
already-rendered text (what `ast_unparse` returns); `Parameter.empty` ↔ None.

We do NOT stand up the `ast` parser / `Parameter` objects (the modeled value is
the pure alignment over the group counts and the default-expression list). Both
legs are total functions over the modeled abstraction. The edge set EXHAUSTIVELY
enumerates small group-count combinations × every default-list length ≤ the
positional count × representative default contents; the fuzz loop additionally
samples random points. The discriminating case — a default belonging to a
positional-only parameter — is covered (oracle keeps it; the pre-patch code
would drop it).

stdlib-only. Pinned seed: 7757 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 7757
N = 200_000

EMPTY = object()  # sentinel ↔ Parameter.empty ↔ Lean `none`


# --- ORACLE: the post-patch alignment block, faithful in-process replica -------
def oracle(n_posonly, n_args, defaults):
    """Replicates signature_from_str's post-patch positional-default wiring.
    `defaults` is the list of rendered default texts (newest-rightmost), as
    `args.defaults` would unparse. Returns the per-positional-parameter default
    (text or None), posonly params first then regular params."""
    defaults = list(defaults)
    positionals = n_posonly + n_args
    # left-pad with EMPTY up to the positional count
    for _ in range(len(defaults), positionals):
        defaults.insert(0, EMPTY)

    out = []
    for i in range(n_posonly):
        d = defaults[i]
        out.append(None if d is EMPTY else d)
    for i in range(n_args):
        d = defaults[i + n_posonly]
        out.append(None if d is EMPTY else d)
    return out


# --- shadow of implementation_positionalDefaults (the R/I leg) -----------------
# Mirrors Solution.lean op-for-op: start from the defaults as `some`, left-pad
# with `none` up to the positional count.
def shadow(n_posonly, n_args, defaults):
    positionals = n_posonly + n_args
    padded = list(defaults)  # each is `some text`
    while len(padded) < positionals:
        padded.insert(0, None)
    return padded


def disagree(np_, na, defs):
    got = oracle(np_, na, defs)
    want = shadow(np_, na, defs)
    if got != want:
        return (np_, na, list(defs), got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# representative rendered default texts
DEF_POOL = ("0", "1", "5", "None", "'x'", "()", "-1")


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over small group-count combos and every legal
    # default-list length, with representative contents.
    for np_ in range(0, 5):
        for na in range(0, 5):
            positionals = np_ + na
            for k in range(0, positionals + 1):  # len(defaults) ≤ positionals
                # a few content patterns for a length-k default list
                patterns = [tuple(DEF_POOL[j % len(DEF_POOL)] for j in range(k))]
                if k >= 1:
                    patterns.append(tuple("d%d" % j for j in range(k)))
                for defs in patterns:
                    d = disagree(np_, na, defs)
                    if d:
                        print(f"DISAGREE exhaustive np={d[0]} na={d[1]} "
                              f"defs={d[2]}: oracle={d[3]} shadow={d[4]}")
                        print("status=fail")
                        return 1
                    checked += 1

    # Random fuzz over wider counts and default contents (respecting the
    # well-formedness precondition len(defaults) ≤ positionals).
    rnd = _lcg(SEED)
    for _ in range(N):
        np_ = next(rnd) % 8
        na = next(rnd) % 8
        positionals = np_ + na
        k = 0 if positionals == 0 else next(rnd) % (positionals + 1)
        defs = tuple(DEF_POOL[next(rnd) % len(DEF_POOL)] for _ in range(k))
        d = disagree(np_, na, defs)
        if d:
            print(f"DISAGREE fuzz np={d[0]} na={d[1]} "
                  f"defs={d[2]}: oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
