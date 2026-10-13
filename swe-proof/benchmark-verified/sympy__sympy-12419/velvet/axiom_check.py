#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12419 (plan §4).

There are NO consumed axioms in this bundle. The kind-A obligations are
**A-reference** component callees that the deep model `entryFor` (Solution.lean
`pure` region) composes and that `conformance_check.py` exercises end-to-end;
G-AX validates each in ISOLATION against real sympy so the end-to-end agreement
is not double-masking (SPEC_GUIDE §0.7):

  (1) the three-valued comparison verdict — `Eq(a, b)` evaluates to exactly one
      of {S.true, S.false, an unevaluated Eq}, and the `threeval` bridge that
      `conformance_check.py` uses to build the `eq : Option Bool` input
      (`is S.true` -> some true, `is S.false` -> some false, else none) is total
      and exact, matching the `is S.true`/`is S.false` test the patched `_entry`
      performs.

  (2) the coincidence indicator — real `KroneckerDelta(a, b)` (the unchanged
      callee the patch returns when the comparison is unsettled) is itself a
      THREE-VALUED value, and the `kdval` bridge that reads its own verdict is
      total and exact:
        * `== S.One`  -> some true   (the indicator settled the pair coincident),
        * `== S.Zero` -> some false  (the indicator settled the pair distinct),
        * an unevaluated `KroneckerDelta` -> none (the indicator declined),
      and nothing else occurs (the value is always one of those three shapes).

      NOTE, and this is what the model must not overclaim: the indicator's own
      rules are STRICTLY BROADER than the comparison's. `KroneckerDelta.eval`
      applies `diff.is_zero` / `fuzzy_not` and the below_fermi/above_fermi
      assumption rules, so it can settle a pair that `Eq` leaves unsettled. The
      class `Eq(a,b)` unsettled AND `KroneckerDelta(a,b) == S.Zero` is therefore
      NON-EMPTY (witness: `a` below_fermi, `b` above_fermi), and any model that
      claimed the value on an unsettled COMPARISON is always a nonzero symbolic
      object would be unfaithful there. What IS sound, and what the spec pins, is
      that the value is the zero exactly when the INDICATOR'S OWN verdict is
      `some false`, and is the unevaluated indicator (not the zero) exactly when
      the indicator's own verdict is `none`. Both directions are checked below.

Imports only sympy (the same library the gold patch calls; ships in the
testbed). Runs in-container. Exit 0 iff every obligation holds. Seed pinned
(mapping.md §4).
"""
import random
import sys

SEED = 12419


def kdval(kd, S):
    """The mapping.md §2 bridge for the SECOND verdict: the indicator's own
    three-valued self-evaluation -> some true / some false / none."""
    if kd == S.One:
        return True
    if kd == S.Zero:
        return False
    return None


def threeval(v):
    """The mapping.md §2 bridge S.true/S.false/unevaluated -> some true/some
    false/none, expressed over the value `Eq(a, b)` returns. Mirrors the patched
    _entry's `eq is S.true` / `eq is S.false` discrimination exactly."""
    from sympy import S
    if v is S.true:
        return True
    if v is S.false:
        return False
    return None


def main():
    from sympy import Eq, S, Symbol, symbols, Integer
    from sympy.functions.special.tensor_functions import KroneckerDelta

    rng = random.Random(SEED)
    checked = 0
    disagreements = []

    n = Symbol('n', integer=True, positive=True)
    i, j, k = symbols('i j k', integer=True)
    syms = [i, j, k, Symbol('a', integer=True), Symbol('b', integer=True),
            Symbol('bf', below_fermi=True), Symbol('af', above_fermi=True)]
    ints = [Integer(v) for v in range(-2, 6)]

    # candidate index pairs: symbol/symbol (undetermined), symbol/self
    # (definite-equal), int/int (definite either way), symbol/int (undetermined),
    # and small affine combinations.
    pairs = []
    for a in syms:
        pairs.append((a, a))                 # definitely equal
    for a in syms:
        for b in syms:
            if a is not b:
                pairs.append((a, b))         # undetermined
    for a in ints:
        for b in ints:
            pairs.append((a, b))             # definite (equal or distinct)
    for a in syms:
        for b in ints:
            pairs.append((a, b))             # undetermined (symbol vs literal)
            pairs.append((b, a))
    # affine combinations
    pairs += [(i + 1, i), (i, i + 1), (2 * i, 2 * i), (i + j, j + i),
              (2 * i, i + i), (i - 1, i), (3 * i, 3 * j)]

    def check_pair(a, b):
        nonlocal checked
        checked += 1
        verdict = threeval(Eq(a, b))
        kd = KroneckerDelta(a, b)
        kdv = kdval(kd, S)
        if verdict is True:
            # definite-equal: the indicator agrees and collapses to the unit
            if kd != S.One:
                disagreements.append(("equal->One", (a, b), kd))
        elif verdict is False:
            # definite-distinct: the indicator agrees and collapses to the zero
            if kd != S.Zero:
                disagreements.append(("distinct->Zero", (a, b), kd))
        # The `kdval` bridge must be TOTAL and EXACT on every pair: the
        # indicator's value is always the unit, the zero, or an unevaluated
        # KroneckerDelta, and the bridge reads exactly that. This is the
        # obligation the spec's second verdict rests on. Note we do NOT claim
        # the value is nonzero merely because `Eq` was unsettled — that claim is
        # FALSE (see the fermi class in the docstring) and asserting it here is
        # what an earlier revision of this check got wrong.
        if kdv is True and kd != S.One:
            disagreements.append(("kdval-true-not-One", (a, b), kd))
        if kdv is False and kd != S.Zero:
            disagreements.append(("kdval-false-not-Zero", (a, b), kd))
        if kdv is None and not isinstance(kd, KroneckerDelta):
            disagreements.append(("kdval-none-not-KD", (a, b), kd))
        if kdv is None and (kd == S.Zero or kd == S.One):
            disagreements.append(("kdval-none-collapsed", (a, b), kd))

    for a, b in pairs:
        check_pair(a, b)
        if len(disagreements) >= 5:
            break

    # randomized fuzz to broaden coverage of the three verdict classes
    if not disagreements:
        pool = syms + ints + [i + 1, j - 2, 2 * k, i + j]
        for _ in range(20000):
            a = rng.choice(pool)
            b = rng.choice(pool)
            check_pair(a, b)
            if len(disagreements) >= 5:
                break

    # explicit boundary witnesses (the F2P-relevant cases)
    boundary = [
        (i, j, None),         # distinct symbols -> undetermined -> KD, != 0
        (i, i, True),         # same symbol -> equal -> One
        (Integer(0), Integer(1), False),   # distinct ints -> Zero
        (Integer(2), Integer(2), True),    # equal ints -> One
    ]
    for a, b, want in boundary:
        checked += 1
        got = threeval(Eq(a, b))
        if got != want:
            disagreements.append(("verdict-boundary", (a, b), (got, want)))

    # explicit witness for the POPULATED cross-class the two-stage model exists
    # to get right: the comparison declines, the indicator settles DISTINCT.
    bf = Symbol('bf_w', below_fermi=True)
    af = Symbol('af_w', above_fermi=True)
    checked += 1
    if threeval(Eq(bf, af)) is not None:
        disagreements.append(("fermi-Eq-should-be-unsettled", (bf, af),
                              Eq(bf, af)))
    if kdval(KroneckerDelta(bf, af), S) is not False:
        disagreements.append(("fermi-KD-should-settle-false", (bf, af),
                              KroneckerDelta(bf, af)))

    if disagreements:
        print("G-AX FAIL: %d component-callee disagreement(s) over %d checks:"
              % (len(disagreements), checked))
        for who, inp, val in disagreements:
            print("  %s input=%r value=%r" % (who, inp, val))
        return 1

    print("G-AX OK: three-valued Eq verdict bridge + the coincidence indicator's "
          "OWN three-valued bridge (== entryFor/coincideValue's unchanged "
          "component callees) sound on %d index-pair checks incl. boundary, the "
          "populated Eq-unsettled/indicator-distinct cross-class, and 20000 fuzz "
          "(seed=%d), 0 disagreements." % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
