#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13615.

Runs the REAL repository callee in-container (the unchanged membership test
`Set.contains`, collapsed to the three verdicts the partition consumes) and the
end-to-end gold-patched `Set._complement` on the FiniteSet branch, and asserts
that every observation matches the model in model.py.

The single consumed axiom is `verdict` (model.py axioms region): the unchanged
membership oracle `self.contains(el)`, collapsed to {DEFINITELY_OUT=0,
DEFINITELY_IN=1, UNDECIDED=2}.  The ONLY thing the proof relies on is totality
plus the three-value range:

  (A-consumed: verdict)  for every (self, el), the ternary collapse of
      `self.contains(el)` -- `True -> in (1)`, `False -> out (0)`, anything
      else (an unevaluated `Contains`) -> undecided (2) -- is always in
      {0, 1, 2}.  The proof never claims a particular verdict for any element,
      only that each element receives exactly one of the three.

This script ALSO validates the end-to-end model fidelity (model.py's
`complement_finite` partition against the REAL gold-patched `_complement`):
for a FiniteSet of elements, the survivors collection is exactly the
DEFINITELY-OUT elements and the pending collection is exactly the UNDECIDED
elements, in input order; the DEFINITELY-IN elements appear in neither.  The
instance FAIL_TO_PASS witness is asserted directly, and the pre-patch behaviour
(undecided elements forced into the concrete survivors collection) is confirmed
DETECTABLY wrong, so the spec discriminates.

Imports only `sympy` (the package whose `_complement` the patch fixes) and the
standard library.  Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import (FiniteSet, Interval, Complement, Union, EmptySet, S,
                   Symbol, Rational, Integer, oo, pi, sqrt)
from sympy.abc import x, y, z


# --- model.py reference encodings (kept in lock-step with the axioms) --------

DEFINITELY_OUT = 0
DEFINITELY_IN = 1
UNDECIDED = 2


def real_verdict(self_set, el):
    """The ternary collapse of the REAL `self.contains(el)`, exactly the
    `ternary_sift` of the gold patch (`contains if contains in [True, False]
    else None`), mapped to the model's verdict codes:
        True  -> DEFINITELY_IN (1)
        False -> DEFINITELY_OUT (0)
        else  -> UNDECIDED (2)
    """
    contains = self_set.contains(el)
    # `self.contains` may return sympy's `S.true`/`S.false` (BooleanTrue/False),
    # which compare equal to Python True/False but are not the singletons; the
    # gold patch's `ternary_sift` keys exactly on `contains in [True, False]`,
    # then the result Union reads the `False` and `None` buckets (the `True`
    # bucket is dropped).  Mirror that bucketing precisely.
    if contains in [True, False]:
        return DEFINITELY_IN if contains == True else DEFINITELY_OUT  # noqa: E712
    return UNDECIDED


def model_partition(self_set, elements):
    """model.py's complement_finite, computed via the verdict oracle: returns
    (out, undecided) preserving input order."""
    out, undecided = [], []
    for el in elements:
        v = real_verdict(self_set, el)
        assert v in (DEFINITELY_OUT, DEFINITELY_IN, UNDECIDED), (
            "verdict axiom unsound: %r contains %r gave out-of-range verdict %r"
            % (self_set, el, v))
        if v == DEFINITELY_OUT:
            out.append(el)
        elif v == UNDECIDED:
            undecided.append(el)
    return out, undecided


# --- the checks --------------------------------------------------------------

def check_verdict_axiom(self_set, elements):
    """(A-consumed) every element's collapsed membership verdict is in {0,1,2}."""
    for el in elements:
        v = real_verdict(self_set, el)
        assert v in (DEFINITELY_OUT, DEFINITELY_IN, UNDECIDED), (
            "verdict axiom unsound on (%r, %r): collapsed verdict %r not in "
            "{0,1,2}" % (self_set, el, v))


def expected_complement(self_set, elements):
    """The behaviour model.py pins, expressed with real sympy constructors:
    Union(FiniteSet(out), Complement(FiniteSet(undecided), self))."""
    out, undecided = model_partition(self_set, elements)
    if undecided:
        return Union(FiniteSet(*out),
                     Complement(FiniteSet(*undecided), self_set,
                                evaluate=False))
    return Union(FiniteSet(*out), S.EmptySet)


def check_end_to_end(self_set, elements):
    """The REAL gold-patched Complement(FiniteSet(elements), self) equals the
    Union(FiniteSet(out), Complement(FiniteSet(undecided), self)) the model
    pins -- i.e. survivors == DEFINITELY-OUT, pending == UNDECIDED, in order."""
    fs = FiniteSet(*elements)
    real = Complement(fs, self_set)
    expected = expected_complement(self_set, elements)
    assert real == expected, (
        "model fidelity broken: Complement(%r, %r) gave %r; model pins %r"
        % (fs, self_set, real, expected))


def prepatch_complement(self_set, elements):
    """The PRE-PATCH behaviour: keep every element whose membership is not
    definitely True in a single concrete FiniteSet (undecided elements wrongly
    forced into the survivors collection)."""
    kept = [el for el in elements if self_set.contains(el) != True]
    return FiniteSet(*kept)


def main():
    syms = [x, y, z]
    nums = [Integer(2), Integer(-3), Integer(0), Integer(11),
            Rational(1, 2), Integer(-20), Integer(20)]
    mixed_pool = syms + nums + [pi, sqrt(2), x + 1, 2 * y]

    # The removal sets exercised for the verdict-axiom RANGE check (totality is
    # the only contract, so every kind of removal set is fair game): intervals
    # (numbers decidable, symbols not), finite sets, and unbounded sets.
    removal_sets = [
        Interval(-10, 10),
        Interval(0, oo),
        Interval(-oo, oo),
        FiniteSet(2, 3, 4),
        FiniteSet(x, 2),
        S.Naturals,
        S.Integers,
        S.Reals,
    ]

    # The removal sets exercised for the END-TO-END partition-fidelity check.
    # The model abstracts `self` as an opaque three-valued membership oracle and
    # pins the partition (survivors / pending / removed).  We validate that
    # partition against the gold `_complement` on removal sets for which the
    # partition is the WHOLE observable result -- intervals and unbounded sets.
    # FiniteSet-vs-FiniteSet removal additionally triggers an UNCHANGED,
    # downstream `Complement(FiniteSet, FiniteSet)` reduction (the subtrahend is
    # pruned of literals that cannot equal a free symbol) that is orthogonal to
    # the modeled partition and not part of this fix; it is therefore excluded
    # from the structural end-to-end comparison (its membership verdicts are
    # still range-checked above).
    e2e_sets = [
        Interval(-10, 10),
        Interval(0, oo),
        Interval(-oo, oo),
        S.Naturals,
        S.Integers,
        S.Reals,
    ]

    # --- (A-consumed) verdict axiom: range soundness over a broad grid -------
    n_verdict = 0
    for self_set in removal_sets:
        check_verdict_axiom(self_set, mixed_pool)
        n_verdict += len(mixed_pool)

    # --- end-to-end model fidelity: boundary collections ---------------------
    boundary_collections = [
        [x, y, Integer(2)],                 # the issue's own example
        [x, y],                             # all undecided
        [Integer(2), Integer(3)],           # all decidable
        [Integer(2), Integer(11)],          # one in, one out (Interval(-10,10))
        [x, Integer(2), y, Integer(11)],    # interleaved
        [],                                 # empty
        [x],                                # single undecided
        [Integer(11)],                      # single definitely-out
        [Integer(2)],                       # single definitely-in
    ]
    n_e2e = 0
    for self_set in e2e_sets:
        for coll in boundary_collections:
            check_end_to_end(self_set, coll)
            n_e2e += 1

    # --- the instance FAIL_TO_PASS witness, asserted directly ----------------
    assert (Complement(FiniteSet(x, y, 2), Interval(-10, 10)) ==
            Complement(FiniteSet(x, y), Interval(-10, 10))), \
        "the issue's FAIL_TO_PASS witness does not hold under the gold patch"

    # --- pre-patch behaviour is DETECTABLY wrong (spec discriminates) --------
    self_set = Interval(-10, 10)
    coll = [x, y, Integer(2)]
    pre = prepatch_complement(self_set, coll)        # {x, y}
    post = Complement(FiniteSet(*coll), self_set)    # {x, y} \ [-10, 10]
    assert pre != post, (
        "pre-patch and gold behaviour coincide on the witness -- the spec "
        "would not discriminate the bug")

    # --- randomized fuzz over the verdict range + end-to-end fidelity --------
    rng = random.Random(13615)
    n_fuzz = 0
    for _ in range(400):
        # verdict range over every removal set; end-to-end over the e2e sets.
        self_any = rng.choice(removal_sets)
        self_e2e = rng.choice(e2e_sets)
        k = rng.randint(0, 5)
        coll = [rng.choice(mixed_pool) for _ in range(k)]
        check_verdict_axiom(self_any, coll)
        check_end_to_end(self_e2e, coll)
        n_fuzz += 1

    print("G-AX OK: verdict axiom range-sound over %d (set, element) pairs; "
          "end-to-end model fidelity == gold _complement over %d boundary + "
          "%d fuzz cases; FAIL_TO_PASS witness holds; pre-patch detectably "
          "wrong." % (n_verdict, n_e2e, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
