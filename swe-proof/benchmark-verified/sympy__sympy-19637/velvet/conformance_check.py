#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19637 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `markerPresent` impl region,
              transliterated to Python over the *real* repo type (the working
              `str` `s`), via the mapping.md bijection (`List Char` ↔ `str`,
              marker ↔ the space code point). The whole impl region is pure R/I
              (a concrete per-code-point membership branch); there is NO A-tagged
              callee, so the shadow is the membership decision itself, returned
              on the success leg. What G-CONF exercises is the CONTROL FLOW the
              change adds: both paths yield a flag (a value), never a failure.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched flag step of `kernS`,
              replayed standalone on the same working string (the real
              correctness oracle, G-RESOLVE). Returns the flag `hit`; raising is
              recorded as a disagreement (the pre-patch defect).

They must agree on the resulting flag for every working string. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys
from random import choice

SEED = 19637
N_FUZZ = 100_000


# --- the R/I shadow: markerPresent's do block, transliterated ----------------
def shadow_marker(s):
    """The R/I shadow of `markerPresent`: decide the flag from whether the
    substitution marker (the space code point, mapping.md §2) is present in the
    working string `s`, branching so BOTH paths yield a value. Returns the flag
    carried on the success leg (the `Except.ok` leg). `s.contains ' '` ↔
    `' ' in s` (mapping.md §2)."""
    if ' ' in s:
        return True             # Except.ok true
    else:
        return False            # Except.ok false


# --- the oracle: patch.diff's gold flag step of kernS ------------------------
def oracle_marker(s):
    """patch.diff's behaviour for the marker-presence flag step of `kernS`:

        if ' ' in s:
            # get a unique kern
            kern = '_'
            while kern in s:
                kern += choice(string.ascii_letters + string.digits)
            s = s.replace(' ', kern)
            hit = kern in s
        else:
            hit = False

    replayed standalone on the working string `s`; returns the resulting flag
    `hit`. This is the gold patch's exact control flow (instance.json patch /
    patch.diff), the real correctness oracle. The pre-patch read `hit = kern in
    s` sat OUTSIDE the `if ' ' in s` branch and raised UnboundLocalError on the
    else path; here both paths bind a flag, so the step is total."""
    if ' ' in s:
        # get a unique kern
        kern = '_'
        while kern in s:
            kern += choice(string.ascii_letters + string.digits)
        s = s.replace(' ', kern)
        hit = kern in s
    else:
        hit = False
    return hit


def fuzz_inputs(n, rng):
    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    yield ""                              # empty: no marker -> False (else path)
    yield " "                             # single marker
    yield "  "                            # repeated marker
    yield "x"                             # no marker, non-empty (the bug path)
    yield "(2*x)/(x-1)"                   # the F2P input: NO space after transforms
    yield "* *(2*x)/(x-1)"               # a working string WITH a marker
    yield "_"                             # the seed kern char, no space
    yield "_ "                            # seed kern char plus a space
    yield "abc_def"                       # only kern-like chars, no space
    yield "a b c"                         # several markers
    yield " leading"
    yield "trailing "
    yield "no_space_at_all-1+2*3"

    alphabet = list("ab_*()+-/0123456789xyz") + [" ", " ", " "]  # spaces weighted up
    no_space_alphabet = list("ab_*()+-/0123456789xyz")
    for i in range(n):
        # ~1/2 of draws are guaranteed space-free (the else/total path, the bug
        # path), the rest may contain markers — both control-flow paths covered.
        if i % 2 == 0:
            k = rng.randint(0, 20)
            yield "".join(rng.choice(no_space_alphabet) for _ in range(k))
        else:
            k = rng.randint(0, 20)
            yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            shadow = shadow_marker(s)
        except Exception as e:
            disagreements.append((s, "shadow raised %s" % type(e).__name__,
                                  "(oracle not run)"))
            if len(disagreements) >= 5:
                break
            continue
        try:
            oracle = oracle_marker(s)
        except Exception as e:
            disagreements.append((s, repr(shadow),
                                  "oracle raised %s" % type(e).__name__))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((s, repr(shadow), repr(oracle)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  s=%r shadow=%s oracle=%s" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of markerPresent agrees with patch.diff "
          "behaviour on %d working strings (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
