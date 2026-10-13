#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9711.

There are NO consumed axioms in Solution.lean. The single operation under spec —
the component-wise version ordering — is modeled DEEPLY by `verGt` (with
`splitDots`/`parseComp`/`relGt`) in the `pure` region, NOT hidden behind an
axiom about the function under change (SPEC_GUIDE directive 7). This check
validates that deep model as an **A-reference**:

  (A-reference) the deep model `ver_gt(a, b)` (this file mirrors `verGt`) equals
      the REAL numeric version comparator the gold patch uses,
          packaging.version.Version(a) > packaging.version.Version(b),
      on the modeled numeric-version domain `numericVer` (every dotted component
      a non-empty decimal-digit run). The `require reqs.all reqWellFormed`
      precondition in Solution.lean pins exactly this domain; the fuzz here stays
      inside it. Outside the domain the gold patch falls back to the textual
      comparison (`except InvalidVersion`), which the spec does not model and the
      precondition forbids — so it is out of scope by construction.

`packaging` is the genuine callee the gold patch imports (`from
packaging.version import InvalidVersion, Version`); running it IS running the
real comparator. Exit 0 iff every observation matches the deep model.
"""
import random
import sys

from packaging.version import Version, InvalidVersion   # the real callee


# --- model.py reference encodings (kept in lock-step with Solution.lean) ------

def split_dots(s):
    """splitDots: dotted components as lists of chars (always >= 1 component)."""
    if s == "":
        return [[]]
    rest = split_dots(s[1:])
    if s[0] == ".":
        return [[]] + rest
    head = rest[0] if rest else []
    return [[s[0]] + head] + rest[1:]


def parse_comp(cs):
    """parseComp: numeric value of one decimal-digit run, MSB first."""
    acc = 0
    for c in cs:
        acc = acc * 10 + (ord(c) - ord("0"))
    return acc


def rel_gt(xs, ys):
    """relGt: strict numeric ordering of component lists, MSB first, with the
    shorter list zero-extended (so trailing-zero components do not matter)."""
    if not xs and not ys:
        return False
    if not xs:
        y, ys2 = ys[0], ys[1:]
        return False if y > 0 else rel_gt([], ys2)
    if not ys:
        x, xs2 = xs[0], xs[1:]
        return True if x > 0 else rel_gt(xs2, [])
    x, y = xs[0], ys[0]
    if x > y:
        return True
    if x < y:
        return False
    return rel_gt(xs[1:], ys[1:])


def ver_gt(a, b):
    """verGt: component-wise numeric strictly-greater-than on version strings."""
    return rel_gt([parse_comp(c) for c in split_dots(a)],
                  [parse_comp(c) for c in split_dots(b)])


def numeric_ver(s):
    """numericVer: every dotted component a non-empty decimal-digit run."""
    comps = split_dots(s)
    return all(len(c) > 0 and all(ch.isdigit() for ch in c) for c in comps)


# --- the A-reference check ----------------------------------------------------

def check_ver_gt(a, b):
    """Assert the deep model ver_gt(a, b) == REAL packaging Version compare."""
    # domain guard: the spec only claims behaviour where both are numeric
    assert numeric_ver(a) and numeric_ver(b), \
        "fuzzer left the modeled domain: %r %r" % (a, b)
    try:
        real = Version(a) > Version(b)             # the real callee
    except InvalidVersion:                          # must not happen on-domain
        raise AssertionError(
            "Version() raised InvalidVersion inside the modeled numeric domain "
            "on %r/%r — domain model (numericVer) is wrong" % (a, b))
    model = ver_gt(a, b)
    assert model == real, (
        "verGt deep model unsound on (%r, %r): packaging Version compare gave "
        "%r, deep model gives %r" % (a, b, real, model))


def main():
    # --- boundary cases over the discriminating + structural edges -----------
    boundary_pairs = [
        ("3.9", "3.10"),    # the issue's headline: numeric 3.9 < 3.10
        ("3.10", "3.9"),
        ("3.11", "3.10"),
        ("0.6", "0.10"),    # the issue's other example
        ("0.10", "0.6"),
        ("0.6.0", "0.10.0"),
        ("1.0", "1.0.0"),   # trailing-zero equality
        ("1.0.0", "1.0"),
        ("2", "2.0"),
        ("1.0", "1"),
        ("01.2", "1.2"),    # leading zeros absorbed
        ("1.02", "1.2"),
        ("10", "9"),        # multi-digit single component
        ("9", "10"),
        ("1.2.3", "1.2"),
        ("1.2", "1.2.3"),
        ("0", "0.0.0"),
        ("3.9", "3.9"),     # equal
        ("100.200.300", "100.200.299"),
    ]
    for a, b in boundary_pairs:
        check_ver_gt(a, b)

    # --- randomized fuzz on the numeric domain (seed pinned, mapping.md §4) ---
    rng = random.Random(9711)

    def gen_version():
        n = rng.randint(1, 4)                       # 1..4 dotted components
        comps = []
        for _ in range(n):
            # mix of single/multi-digit and occasional leading zeros & zeros
            kind = rng.randint(0, 3)
            if kind == 0:
                comps.append(str(rng.randint(0, 9)))
            elif kind == 1:
                comps.append(str(rng.randint(0, 999)))
            elif kind == 2:
                comps.append("0" + str(rng.randint(0, 99)))   # leading zero
            else:
                comps.append("0")
        return ".".join(comps)

    N = 50000
    for _ in range(N):
        a, b = gen_version(), gen_version()
        check_ver_gt(a, b)
        check_ver_gt(a, a)                          # reflexive: always False

    print("G-AX OK: verGt deep model (== packaging Version comparison) sound on "
          "%d boundary + %d fuzz version pairs over the numeric domain."
          % (len(boundary_pairs), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
