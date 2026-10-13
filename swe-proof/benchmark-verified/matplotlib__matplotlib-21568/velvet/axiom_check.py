#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-21568.

Executes the REAL string operations the gold patch performs and asserts every
observation matches the model encoded in Solution.lean.

The kind-A checks:

  (A-reference) the deep model `protect_seq` (Solution.lean pure region,
      `protectSeq`/`mathProtect`) == the REAL chained `.replace` the gold patch
      applies inside `_wrap_in_tex`:
          s.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\\;')
      per code point: '-'(45)->'{-}'  ':'(58)->'{:}'  ' '(32)->'\\;'  else id.
      The chain collapses to this per-code-point map because no replacement
      output contains a code point a later replacement targets (validated here
      directly against the real chained replace, no double-masking).

  (A-consumed, vacuous) `re_sub` / `remove_empty` model the two UNCHANGED
      context callees `re.sub(p, …, text)` and `str.replace('$\\mathdefault{}$',
      '')`. The Lean axioms carry NO `ensures` (uninterpreted maps), so the only
      obligation is that each real callee is a deterministic function of its
      input — checked here. (The patch does not touch them, so they hold no
      discriminator.)

Imports only the Python standard library (`re`, `random`) — `str.replace` and
`re.sub` are the very operations the gold patch calls. Exit 0 iff every
obligation holds.
"""
import random
import re
import sys

# --- Solution.lean reference encodings (kept in lock-step with `mathProtect`) -

_PROTECT = {
    ord('-'): list("{-}"),
    ord(':'): list("{:}"),
    ord(' '): list("\\;"),
}


def protect_seq(codepoints):
    """Reference implementation of Solution.lean's deep model `protectSeq`, as a
    list of code points (the per-code-point substitution)."""
    out = []
    for c in codepoints:
        out.extend([ord(ch) for ch in _PROTECT.get(c, [chr(c)])] if c in _PROTECT
                   else [c])
    return out


def real_chained_replace(s):
    """The REAL changed string op from the gold patch (lib/matplotlib/dates.py
    post-patch, the chained .replace)."""
    return s.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')


# --- the checks --------------------------------------------------------------

def check_protect_reference(s):
    """Assert the deep model protect_seq(s) == the REAL chained .replace(s)."""
    observed = [ord(ch) for ch in real_chained_replace(s)]   # real op
    expected = protect_seq([ord(ch) for ch in s])            # deep model
    assert observed == expected, (
        "protect_seq deep model unsound on %r: chained .replace gave %r, "
        "deep model gives %r" % (s, observed, expected))


# --- the two opaque unchanged context callees (vacuous: determinism only) ----

_RE_P = r'([a-zA-Z]+)'


def real_re_sub(s):
    return re.sub(_RE_P, r'}$\1$\\mathdefault{', s)


def real_remove_empty(s):
    return s.replace('$\\mathdefault{}$', '')


def check_callee_deterministic(fn, s):
    assert fn(s) == fn(s), "context callee %s non-deterministic on %r" % (
        fn.__name__, s)


def main():
    significant = ['-', ':', ' ']
    ordinary = list("aZ09;#x{}$\\<>\"'.eé•qutlgmp")

    # --- protect_seq deep model (A-reference): boundary cases -------------
    boundary = [""]
    boundary += significant                       # each significant char alone
    boundary += [c + c for c in significant]      # doubled
    boundary += ["".join(significant)]            # all three together
    boundary += ["".join(reversed(significant))]
    boundary += [
        "a-b:c d",
        "1990-01-01",
        "01-01 20",
        "00:00:00",
        "01 00:10",
        "}$Jan$\\mathdefault{ 01 1990",            # post-re.sub shape
        "{-}", "{:}", "\\;",                       # already-protected fragments
        "- : ", " :-", "::--  ",
        "$\\mathdefault{}$",
        "no specials here",
    ]
    for s in boundary:
        check_protect_reference(s)

    # --- protect_seq deep model (A-reference): randomized fuzz ------------
    rng = random.Random(21568)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_protect_reference(s)

    # --- opaque context callees (A-consumed, vacuous): determinism --------
    for s in boundary:
        check_callee_deterministic(real_re_sub, s)
        check_callee_deterministic(real_remove_empty, s)

    print("G-AX OK: protect_seq deep model (== chained .replace) sound on %d "
          "boundary + 20000 fuzz inputs; re_sub/remove_empty deterministic "
          "(uninterpreted context callees)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
