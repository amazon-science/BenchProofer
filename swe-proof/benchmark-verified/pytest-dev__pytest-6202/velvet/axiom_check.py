#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-6202.

Executes the REAL stdlib string callees (`str.join`, `str.replace`) on boundary
cases and randomized fuzz, asserting that every observation matches the deep
models encoded in Solution.lean. There is NO consumed axiom in this bundle; both
checks are A-reference validations of deep models against the real callees.

  (A-reference) `joinDot` (Solution.lean pure region) == the real
      ".".join(parts): the separator-join with a single '.' between consecutive
      parts; the empty list joins to "", a singleton to itself.

  (A-reference) `replaceWindow` (Solution.lean pure region, referenced only by
      Solution_prepatch.lean) == the real s.replace(".[", "["): left-to-right
      non-overlapping replacement of the two-char pattern ".[" by "[".

Imports nothing repo-specific: `str.join`/`str.replace` are builtins — the same
operations the gold patch (and its pre-image) call. Exit 0 iff every obligation
holds.
"""
import random
import sys

SEP = "."          # Solution.lean `sep`
PATTERN = ".["     # the prepatch substitution pattern
REPL = "["


# --- Solution.lean deep-model reference encodings (kept in lock-step) --------

def join_dot(parts):
    """Reference for Solution.lean `joinDot`: front-recursive separator-join.
    parts is a list of str (each str a name part)."""
    if len(parts) == 0:
        return ""
    if len(parts) == 1:
        return parts[0]
    return parts[0] + SEP + join_dot(parts[1:])


def replace_window(s):
    """Reference for Solution.lean `replaceWindow`: greedy left-to-right,
    non-overlapping replacement of the 2-char window '.[' by '['."""
    out = []
    i, n = 0, len(s)
    while i < n:
        if i + 1 < n and s[i] == "." and s[i + 1] == "[":
            out.append("[")
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


# --- the checks --------------------------------------------------------------

def check_join_reference(parts):
    """Assert the deep model join_dot(parts) == the REAL ".".join(parts)."""
    observed = SEP.join(parts)            # real builtin callee
    expected = join_dot(parts)            # deep model
    assert observed == expected, (
        "joinDot deep model unsound on %r: '.'.join gave %r, "
        "deep model gives %r" % (parts, observed, expected))


def check_replace_reference(s):
    """Assert the deep model replace_window(s) == the REAL s.replace('.[','[')."""
    observed = s.replace(PATTERN, REPL)   # real builtin callee
    expected = replace_window(s)          # deep model
    assert observed == expected, (
        "replaceWindow deep model unsound on %r: str.replace gave %r, "
        "deep model gives %r" % (s, observed, expected))


def main():
    # --- joinDot deep model (A-reference): boundary part-lists --------------
    join_boundary = [
        [],
        [""],
        ["a"],
        ["TestX", "testmethod_one"],
        ["TestY", "testmethod_one"],
        ["testone"],
        # the F2P witness: a part that itself contains '.[' must survive the
        # plain join verbatim (the gold behaviour).
        ["TestY", "testmethod_two[.[]"],
        ["a", "b", "c"],
        [".", "[", "]"],
        ["x.", "[y"],          # '.[' straddles two parts -> join inserts another '.'
        ["", "", ""],
        ["p.[q", "r.[s"],
        ["test_boo[..[]"],
        ["a..[b"],
    ]
    for parts in join_boundary:
        check_join_reference(parts)

    # --- replaceWindow deep model (A-reference): boundary strings -----------
    replace_boundary = [
        "",
        ".",
        "[",
        ".[",
        "..[",
        ".[.[",
        "[.[",
        "...[[[",
        "TestY.testmethod_two[.[]",
        "TestY.testmethod_two[[]",
        "test_boo[..[]",
        "test_boo[.[]",
        "a.b.c",
        "no pattern here",
        ".[.[.[",
        "][.",
    ]
    for s in replace_boundary:
        check_replace_reference(s)

    # --- randomized fuzz over a small alphabet rich in '.' '[' ']' ----------
    rng = random.Random(6202)
    alphabet = list(".[]abT0")
    for _ in range(30000):
        # fuzz join: random list of random parts
        nparts = rng.randint(1, 5)
        parts = []
        for _ in range(nparts):
            k = rng.randint(0, 8)
            parts.append("".join(rng.choice(alphabet) for _ in range(k)))
        check_join_reference(parts)
        # the join itself is a good replace-fuzz input, plus fresh strings
        check_replace_reference(SEP.join(parts))
        m = rng.randint(0, 16)
        check_replace_reference("".join(rng.choice(alphabet) for _ in range(m)))

    print("G-AX OK: joinDot deep model (== '.'.join) and replaceWindow deep "
          "model (== str.replace('.[','[')) sound on %d join + %d replace "
          "boundary inputs and 30000 fuzz rounds (seed=6202)."
          % (len(join_boundary), len(replace_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
