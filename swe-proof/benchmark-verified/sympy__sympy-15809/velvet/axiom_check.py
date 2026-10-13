#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-15809.

G-AX runs against the UNPATCHED base repo (the gates apply NO patch here): its
job is to validate that the axioms/deep-model references about the UNCHANGED
callees match those callees' real behaviour. So every assertion below must be
true on the base image — we never invoke the post-patch whole-constructor
behaviour here (that empty-input result is the MODELED function's own behaviour,
validated by G-RESOLVE — official test_Min/test_Max — and by G-CONF, which
applies the gold patch and asserts the empty case returns cls.identity).

Runs the REAL, UNCHANGED argument-normalisation pipeline of the lattice-extremum
constructor in-container and asserts the model's only consumed axiom holds, plus
that the non-empty count-dispatch legs (unchanged by the patch) are real.

Modeled callee (mapping.md §3.1):
    processArgs  ==  the unchanged chain run inside MinMaxBase.__new__:
        frozenset(cls._new_args_filter(args))   # standard filter / flatten
        cls._collapse_arguments(args, ...)       # drop dominated members
        cls._find_localzeros(args, ...)          # remove locally-dominated

The ONE consumed axiom (A-consumed):
    processArgs_nil :  processArgs [] = []
i.e. normalising NO raw arguments yields NO surviving members. We assert this on
the REAL pipeline for BOTH Max and Min (the two concrete lattices). This is the
unchanged-callee fact the empty-input model leg rests on; it holds on the base
repo (the deleted guard sits in __new__ ABOVE this pipeline, so the pipeline
itself is reached and behaves identically pre- and post-patch).

The non-empty count-dispatch legs (A-reference; unchanged by the patch, hence
base-valid):
    1 survivor   -> that member verbatim    (Max(x) == x,   Min(x) == x)
    >=2 survivors-> a built Max/Min object  (Max(x, y) is a Max with .args = {x,y})
The 0-survivor leg (Max() == -oo, Min() == oo) is the PATCHED constructor
behaviour and is therefore NOT checked here (unreachable on base — guarded);
G-RESOLVE and G-CONF cover it.

Imports only sympy (the base repo under test; NO patch applied for G-AX).
Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import Max, Min, Symbol
from sympy.core.operations import ShortCircuit


def normalised_args(cls, raw):
    """Re-run the UNCHANGED normalisation chain of MinMaxBase.__new__ on `raw`
    (a sequence of sympy args) and return the surviving-member set — i.e. the
    real `processArgs(raw)`. Mirrors miscellaneous.py:347-360 exactly."""
    args = (a for a in raw)
    try:
        args = frozenset(cls._new_args_filter(args))
    except ShortCircuit:
        # absorbing element present: constructor short-circuits to cls.zero;
        # not an empty-normalisation observation, signalled to caller.
        return None
    args = cls._collapse_arguments(args, **{})
    args = cls._find_localzeros(args, **{})
    return args


def check_processArgs_nil():
    """A-consumed: processArgs [] = [] on the REAL pipeline, both lattices."""
    for cls in (Max, Min):
        surv = normalised_args(cls, [])
        assert surv is not None, (
            "processArgs_nil unsound: empty input short-circuited for %s" % cls)
        assert len(surv) == 0, (
            "processArgs_nil unsound for %s: normalising [] gave %r, "
            "axiom requires []" % (cls, surv))


def check_single_leg(syms):
    """1 survivor -> that member verbatim."""
    for s in syms:
        assert Max(s) == s, "Max(%r) must be %r, got %r" % (s, s, Max(s))
        assert Min(s) == s, "Min(%r) must be %r, got %r" % (s, s, Min(s))


def check_combined_leg(pairs):
    """>=2 survivors -> a built Max/Min object over the survivors."""
    for a, b in pairs:
        mx, mn = Max(a, b), Min(a, b)
        assert isinstance(mx, Max), "Max(%r,%r) not a Max object: %r" % (a, b, mx)
        assert isinstance(mn, Min), "Min(%r,%r) not a Min object: %r" % (a, b, mn)
        # the survivors are exactly {a, b} (distinct, incomparable symbols)
        assert set(mx.args) == {a, b}, "Max(%r,%r).args = %r" % (a, b, mx.args)
        assert set(mn.args) == {a, b}, "Min(%r,%r).args = %r" % (a, b, mn.args)


def main():
    # --- A-consumed: the empty-normalisation axiom (base-valid) -----------
    # processArgs [] = []: the unchanged pipeline introduces no members from
    # nothing. This is the only fact the empty-input MODEL leg consumes; the
    # 0-survivor -> cls.identity result is the patched constructor's behaviour
    # (G-RESOLVE / G-CONF cover it), unreachable on the base repo here.
    check_processArgs_nil()

    # --- A-reference: the non-empty count-dispatch legs (unchanged by patch)
    # distinct, pairwise-incomparable real symbols => each survives alone /
    # two of them survive together (no collapse, no local-zero domination).
    syms = [Symbol("a%d" % i, real=True) for i in range(8)]
    check_single_leg(syms)

    rng = random.Random(15809)
    pairs = []
    for _ in range(2000):
        i, j = rng.randrange(len(syms)), rng.randrange(len(syms))
        if i == j:
            j = (j + 1) % len(syms)
        pairs.append((syms[i], syms[j]))
    check_combined_leg(pairs)

    print("G-AX OK: processArgs_nil sound on the real (unchanged) normalisation "
          "pipeline (Max and Min) on the base repo; single/combined legs real "
          "over %d symbols + %d combined pairs. (The empty->identity leg is the "
          "patched-constructor behaviour, validated by G-RESOLVE / G-CONF.)"
          % (len(syms), len(pairs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
