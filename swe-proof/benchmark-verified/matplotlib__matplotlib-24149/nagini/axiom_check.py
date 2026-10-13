#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24149.

Executes the REAL callees the gold patch invokes — `matplotlib.cbook.
_safe_first_finite` and `matplotlib.cbook.safe_first_element` — on coordinate
sequences (lists of finite floats and non-finite NaNs; boundary cases over the
finiteness pattern plus randomized fuzz) and asserts that every observation
matches the two axioms encoded in model.py.

The two kind-A axioms (model.py axioms region), over the flag carrier
(`flags[k] != 0` <-> the k-th coordinate is finite):

  (A-consumed) `first_finite(s)` models `cbook._safe_first_finite(obj)`:
      under its precondition `any_finite(s)` (some element is finite) it returns
      THE FIRST FINITE element of the input — its value/identity, not merely the
      fact that it is finite (Ensures `Result() == first_finite_value(s)`, which
      in particular implies the element is finite). Soundness has three halves:
        * NO-RAISE under the precondition: when at least one element is finite,
          the real callee returns normally (does not raise StopIteration);
        * IDENTITY under the precondition: the returned value equals the element
          at the leftmost finite index (the value `first_finite_value` selects),
          observable because finite flags materialize as DISTINCT finite floats —
          so a constant-echo impl that returns some other finite value violates
          it (this pins the directive-8 ungrounded-marker hole the prior bare
          `Result() != 0` left open);
        * the precondition is EXACTLY the no-raise domain: when NO element is
          finite, the real callee raises StopIteration — which is precisely the
          regression the patch repairs, and precisely the negation of
          `any_finite`. So the axiom's Requires is the weakest sound guard.

  (A-consumed) `first_unconditional(s)` models `cbook.safe_first_element(obj)`:
      on a non-empty sequence it returns the FIRST element unconditionally
      (Ensures `Result() == s[0]`), regardless of finiteness. This is the
      fallback the patch reaches for an all-non-finite sequence.

Imports `matplotlib.cbook` (the very module the gold patch calls) and `numpy`
(the finiteness layer `np.isfinite` it uses); nothing else repo-specific. Exit 0
iff every obligation holds.
"""
import math
import random
import sys

import numpy as np
from matplotlib import cbook


# --- model.py reference encodings (kept in lock-step with the axioms) --------

def any_finite(flags):
    """Reference of model.py's deep model `any_finite`: some element's flag is
    non-zero (False on the empty sequence)."""
    for f in flags:
        if f != 0:
            return True
    return False


def first_finite_index(flags):
    """Index of the leftmost finite (non-zero) flag; -1 if none. The position
    model.py's `first_finite_value` selects (it skips leading non-finite flags
    and yields the first finite one)."""
    for i, f in enumerate(flags):
        if f != 0:
            return i
    return -1


def to_values(flags):
    """Materialize a flag pattern as a concrete coordinate list: a finite flag
    becomes a DISTINCT finite float (so the selected element's identity is
    observable — the value pins WHICH element was chosen, not just that it is
    finite); a zero flag becomes a non-finite NaN."""
    vals = []
    for i, f in enumerate(flags):
        vals.append(float(i + 1) if f != 0 else float("nan"))
    return vals


def flag_of(value):
    """The model flag of a concrete coordinate value: 1 if finite, else 0."""
    return 1 if (value is not None and np.isscalar(value)
                 and bool(np.isfinite(value))) else (
        1 if value is not None and not np.isscalar(value) else 0)


# --- the checks --------------------------------------------------------------

def first_finite_raises_when_no_finite():
    """Probe the installed `_safe_first_finite`: does it raise StopIteration on
    an all-non-finite list (the base_commit, pre-fix matplotlib 3.6 behaviour
    the eval container pins — the regression this instance repairs), or has it
    been refactored to fall back internally (a LATER matplotlib version)? The
    `first_finite` axiom is only ever invoked under the `any_finite` guard, so
    its SOUNDNESS does not depend on which branch holds; this probe lets the
    explanatory no-raise-domain witness adapt to the installed version."""
    try:
        cbook._safe_first_finite([float("nan")])
        return False
    except StopIteration:
        return True
    except Exception:
        return False


_RAISES_NO_FINITE = first_finite_raises_when_no_finite()


def check_first_finite(flags):
    """A-consumed: validate `first_finite` axiom against the REAL callee.

    The axiom is invoked only under its precondition `any_finite(s)`, so the
    load-bearing obligation — sound in EVERY matplotlib version — is: when some
    element is finite, the real `_safe_first_finite` returns normally with the
    FIRST FINITE element of the sequence. The strengthened axiom pins the
    selected element's IDENTITY (`Result() == first_finite_value(s)`), not
    merely its finiteness, so the check asserts the real callee returns exactly
    the value at the first-finite index (the element `first_finite_value`
    selects) — a constant-echo impl that returns some other finite value would
    violate this. When NO element is finite (outside the precondition), the
    base_commit (pre-fix 3.6) callee raises StopIteration — the regression — and
    that is what the in-container G-AX observes."""
    vals = to_values(flags)
    if any_finite(flags):
        # precondition holds -> real callee must return normally, and must
        # return THE first finite element (its value/identity, not just any
        # finite value): the value at the leftmost non-zero flag.
        idx = first_finite_index(flags)
        expected = vals[idx]
        try:
            observed = cbook._safe_first_finite(vals)
        except StopIteration:
            raise AssertionError(
                "first_finite axiom unsound: _safe_first_finite raised "
                "StopIteration on %r although a finite element exists" % (vals,))
        assert flag_of(observed) != 0, (
            "first_finite axiom unsound on %r: _safe_first_finite returned a "
            "non-finite element %r, axiom requires a finite one" % (vals, observed))
        # IDENTITY: the returned element must be the FIRST finite element, the
        # exact value first_finite_value(s) pins (vals are distinct finite
        # floats so the selected position is observable).
        assert observed == expected, (
            "first_finite axiom unsound on %r: _safe_first_finite returned %r, "
            "but the axiom pins the FIRST finite element %r (index %d)"
            % (vals, observed, expected, idx))
    else:
        # outside the precondition: in the base_commit (pre-fix) callee this is
        # exactly the StopIteration domain — the negation of `any_finite` — so
        # the axiom's Requires is the weakest sound guard. (A later refactor
        # absorbed the fallback into the callee; then no raise occurs, which is
        # equally consistent with the guarded axiom.)
        if len(vals) == 0:
            return  # empty is excluded by the function precondition len(seq) > 0
        if _RAISES_NO_FINITE:
            raised = False
            try:
                cbook._safe_first_finite(vals)
            except StopIteration:
                raised = True
            assert raised, (
                "first_finite axiom's Requires not the weakest sound guard: "
                "_safe_first_finite did NOT raise on the all-non-finite %r, so "
                "the no-finite case is reachable without the guard" % (vals,))


def check_first_unconditional(flags):
    """A-consumed: validate `first_unconditional` axiom against the REAL callee."""
    vals = to_values(flags)
    if len(vals) == 0:
        return  # precondition len(s) > 0
    observed = cbook.safe_first_element(vals)
    first = vals[0]
    # Ensures Result() == s[0]: same element (NaN-aware identity).
    ok = (observed is first) or (observed == first) or (
        isinstance(observed, float) and isinstance(first, float)
        and math.isnan(observed) and math.isnan(first))
    assert ok, (
        "first_unconditional axiom unsound on %r: safe_first_element returned "
        "%r, axiom requires the first element %r" % (vals, observed, first))


def check_case(flags):
    check_first_finite(flags)
    check_first_unconditional(flags)


def main():
    # --- boundary cases over the finiteness pattern ------------------------
    boundary = [
        [1],                 # single finite
        [0],                 # single non-finite  (the all-NaN F2P scenario)
        [0, 0],              # all non-finite
        [0, 0, 0],
        [1, 1],
        [1, 0],              # leading finite
        [0, 1],              # leading non-finite, then finite (skip the NaN)
        [0, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 1, 1, 1],
    ]
    for case in boundary:
        check_case(case)

    # explicit all-non-finite regression witness (the exact ax.bar([nan]) case).
    # In the base_commit (pre-fix matplotlib 3.6) callee that G-AX pins,
    # _safe_first_finite([nan]) raises StopIteration; that propagating out of
    # _convert_dx's inner try (which catches only TypeError/IndexError/KeyError)
    # is the crash being fixed. The patched fallback safe_first_element returns
    # the (NaN) first element unconditionally — sound in every version.
    if _RAISES_NO_FINITE:
        raised = False
        try:
            cbook._safe_first_finite([float("nan")])
        except StopIteration:
            raised = True
        assert raised, "all-NaN input must raise StopIteration in _safe_first_finite"
    assert math.isnan(cbook.safe_first_element([float("nan")])), (
        "all-NaN fallback: safe_first_element must return the (NaN) first element")

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(24149)
    for _ in range(20000):
        n = rng.randint(1, 12)
        case = [1 if rng.random() < 0.5 else 0 for _ in range(n)]
        check_case(case)

    mode = ("base_commit 3.6 (raises StopIteration on all-non-finite)"
            if _RAISES_NO_FINITE else
            "post-refactor (callee falls back internally)")
    print("G-AX OK: first_finite (returns finite under any_finite) and "
          "first_unconditional (returns the first element) axioms sound vs the "
          "real cbook._safe_first_finite / cbook.safe_first_element over %d "
          "boundary + 20000 fuzz coordinate sequences; installed callee mode: %s"
          % (len(boundary), mode))
    return 0


if __name__ == "__main__":
    sys.exit(main())
