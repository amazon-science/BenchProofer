#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-10844.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real numeric carrier. The impl returns TWO
              observables and both are shadowed:
                (1) the VALUE, the SQUARED similarity coefficient computed
                    divide-first:
                        v = 0                                   if agree == 0
                        v = (agree/spreadA) * (agree/spreadB)    otherwise
                (2) the returned PLAN, evaluated by the transliterated
                    fixed-width semantics of Solution.lean's pure region at
                    width 64 (the dtype the gold patch's aggregates carry): a
                    materialised integer product has a value only while it fits
                    the word.
              (No axiom is involved; the whole impl is R/I.) The shadow consumes
              the three integer aggregates `(tk, pk, qk)` that the real
              `fowlkes_mallows_score` builds from a pair of label arrays.

              Shadowing the plan is what ties the spec's discriminating clause
              to real machine arithmetic: the returned plan must have a value at
              width 64 on every input the oracle accepts, and that value must be
              the oracle's squared score. The product-first plan is evaluated
              alongside, and the inputs where IT has no value are counted — on
              the F2P-scale witness it has none, which is the same input where
              the real pre-patch expression is `nan`.

                (3) the TIE between the two: the number returned must BE the
                    number the returned plan yields, at this call's own width and
                    aggregates. Compared as exact rationals with no tolerance,
                    because that is how the spec states it.

              The admissible domain INCLUDES a vanishing spread. The requires ask
              only `0 <= spread` and `agree <= spread`, and a partition that puts
              every element in a group of its own reaches this routine with a
              vanishing spread — which forces a vanishing agreement count. There
              the oracle returns 0 while the combine step run unconditionally has
              no value at all, so the returned plan's `zeroThen` step is the only
              reason a number comes out; those inputs are counted rather than
              skipped, and a run that never reaches one FAILS as carrying no
              evidence for the obligation.
  * ORACLE  — `patch.diff`'s behaviour: the patched `fowlkes_mallows_score`
              applied at base_commit (the real correctness oracle, G-RESOLVE).
              Its score is the ROOT of the coefficient, so we compare against
              `oracle_score ** 2` (mapping.md §3: the model carries the square,
              the unchanged np.sqrt is peeled).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with the gold patch
applied). stdlib + numpy + the repo's sklearn only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import sys
import random
from fractions import Fraction

import numpy as np

SEED = 10844
N_FUZZ = 100_000
RTOL = 1e-9
WIDTH = 64                 # the machine word the real aggregates carry

from sklearn.metrics.cluster.supervised import (
    fowlkes_mallows_score, contingency_matrix,
)


# ---------------------------------------------------------------------------
# Transliteration of Solution.lean's pure region (plans + their fixed-width
# partial semantics) and of the plan the impl region returns.
# ---------------------------------------------------------------------------
# The COMBINE step of the returned plan (pair the agreement count with each
# spread, then multiply the two exact ratios)...
COMBINE_PLAN = ("rmul",
                ("ratio", ("read", "agree"), ("read", "spreadA")),
                ("ratio", ("read", "agree"), ("read", "spreadB")))
# ...and the plan the impl region actually RETURNS: answer zero outright when the
# agreement count vanishes, and only otherwise run the combine.
RETURNED_PLAN = ("zeroThen", ("read", "agree"), COMBINE_PLAN)
PRODUCT_FIRST_PLAN = ("ratio",
                      ("imul", ("read", "agree"), ("read", "agree")),
                      ("imul", ("read", "spreadA"), ("read", "spreadB")))


def trunc_w(width, x):
    """Transliteration of the pure region's `truncW`: the silent wraparound a
    `width`-bit two's-complement register performs."""
    return (x + 2 ** (width - 1)) % (2 ** width) - 2 ** (width - 1)


def word_mul(width, x, y):
    """Transliteration of `instMulWord` -- the register carrier's own (wrapping)
    multiplication, which is what an UNPROMOTED aggregate is subject to."""
    return trunc_w(width, x * y)


def in_word(width, x):
    return -(2 ** (width - 1)) <= x <= 2 ** (width - 1) - 1


def int_plan_value(width, agg, plan):
    if plan[0] == "read":
        return agg[plan[1]]
    x = int_plan_value(width, agg, plan[1])
    y = int_plan_value(width, agg, plan[2])
    if x is None or y is None:
        return None
    prod = x * y
    return prod if in_word(width, prod) else None


def rat_plan_value(width, agg, plan):
    if plan[0] == "ratio":
        x = int_plan_value(width, agg, plan[1])
        y = int_plan_value(width, agg, plan[2])
        if x is None or y is None or y == 0:
            return None
        return Fraction(x, y)
    if plan[0] == "zeroThen":
        g = int_plan_value(width, agg, plan[1])
        if g is None:
            return None
        if g == 0:
            return Fraction(0)          # answered; the rest is NOT evaluated
        return rat_plan_value(width, agg, plan[2])
    x = rat_plan_value(width, agg, plan[1])
    y = rat_plan_value(width, agg, plan[2])
    if x is None or y is None:
        return None
    return x * y


def aggregates(labels_true, labels_pred):
    """Recompute the three integer aggregates exactly as the patched function
    does, so the shadow consumes the same (tk, pk, qk) the oracle does."""
    n_samples, = np.asarray(labels_true).shape
    c = contingency_matrix(labels_true, labels_pred, sparse=True).astype(np.int64)
    tk = np.dot(c.data, c.data) - n_samples
    pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples
    qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples
    return int(tk), int(pk), int(qk)


def admissible(tk, pk, qk):
    """The spec's `require` list at width WIDTH, as a predicate on the three
    aggregates. A spread of ZERO satisfies it: the requires demand only
    `0 <= spread` and `agree <= spread`, so a partition that puts every element in
    a group of its own -- whose aggregate vanishes, forcing the agreement count to
    vanish with it -- is an ADMISSIBLE input and not a skipped one. That domain is
    where the returned plan's short-circuit is load-bearing, so excluding it would
    leave the one obligation this leg exists to ground untested."""
    return (0 <= tk <= pk and tk <= qk
            and all(in_word(WIDTH, x) for x in (tk, pk, qk)))


def shadow_squared(tk, pk, qk):
    """fowlkesCoeffSquared's VALUE transliterated: the divide-first squared
    coefficient (the R/I ops of the impl region). Returns the squared score (a
    float)."""
    if not admissible(tk, pk, qk):
        return None            # outside Requires; skip (handled by caller)
    if tk == 0:
        return 0.0
    return (tk / pk) * (tk / qk)


def shadow_value_exact(tk, pk, qk):
    """The same VALUE as an exact rational, for the tie leg (the returned number
    must BE the number the returned plan yields, so the comparison has to be
    exact and not float-tolerant)."""
    if tk == 0:
        return Fraction(0)
    return Fraction(int(tk), int(pk)) * Fraction(int(tk), int(qk))


def shadow_plan_squared(tk, pk, qk):
    """fowlkesCoeffSquared's PLAN transliterated: evaluate the plan the impl
    region returns under a WIDTH-bit machine word, exactly as the pure region
    does. `None` means the plan materialises an integer the word cannot hold —
    for the returned plan that must never happen on an in-Requires input, which
    is the fidelity claim this leg refutes."""
    agg = {"agree": int(tk), "spreadA": int(pk), "spreadB": int(qk)}
    val = rat_plan_value(WIDTH, agg, RETURNED_PLAN)
    return None if val is None else float(val)


def shadow_register_route_squared(tk, pk, qk):
    """The value a routine gets if it combines through the REGISTER product of
    the two spreads instead of dividing first (or promoting).

    This is not the shipped impl -- it is the route the strengthened value clause
    rejects -- and it is shadowed so the run carries evidence that the register
    carrier's distinction is REACHABLE on real label data rather than only in
    principle. Where the product fits the register this equals the coefficient;
    where it wraps it does not, and on the F2P-scale witness it goes negative.
    """
    if pk <= 0 or qk <= 0 or tk == 0:
        return None
    reg = word_mul(WIDTH, pk, qk)
    if reg == 0:
        return None
    return Fraction(int(tk) * int(tk), reg)


def oracle_squared(labels_true, labels_pred):
    """patch.diff's behaviour: the patched fowlkes_mallows_score, squared
    (the score is the root of the modeled coefficient)."""
    score = float(fowlkes_mallows_score(labels_true, labels_pred))
    return score * score


def random_labels(rng, n, k_true, k_pred):
    lt = np.array([rng.randrange(k_true) for _ in range(n)])
    lp = np.array([rng.randrange(k_pred) for _ in range(n)])
    return lt, lp


def fuzz_inputs(n, rng):
    # boundary cases first
    yield np.array([0, 0, 1, 1]), np.array([0, 0, 1, 1])      # perfect
    yield np.array([0, 0, 1, 1]), np.array([1, 1, 0, 0])      # perfect (relabel)
    yield np.array([0, 0, 0, 0]), np.array([0, 1, 2, 3])      # fully split (agree=0)
    yield np.array([0, 1, 2, 3]), np.array([0, 0, 0, 0])
    yield np.array([0, 0, 1, 1, 2, 2]), np.array([0, 1, 1, 2, 2, 0])
    # the F2P-scale overflow witness (pk*qk overflows int64 in the pre-patch)
    x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 + 204)
                 + [4] * (814 + 39) + [5] * (316 + 20))
    y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793
                 + [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39
                 + [0] * 316 + [1] * 20)
    yield x, y
    # randomized fuzz
    for _ in range(n):
        size = rng.randint(2, 60)
        k_true = rng.randint(1, max(2, size // 2))
        k_pred = rng.randint(1, max(2, size // 2))
        yield random_labels(rng, size, k_true, k_pred)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    prod_first_valueless = 0
    register_diverges = 0
    unguarded_valueless = 0
    for lt, lp in fuzz_inputs(N_FUZZ, rng):
        tk, pk, qk = aggregates(lt, lp)
        sh = shadow_squared(tk, pk, qk)
        if sh is None:                 # pk<=0 or qk<=0: outside Requires
            skipped += 1
            continue
        count += 1
        orc = oracle_squared(lt, lp)
        denom = max(1.0, abs(orc))
        if abs(sh - orc) > RTOL * denom:
            disagreements.append(("value", tk, pk, qk, sh, orc))
        # SECOND observable: the returned PLAN, evaluated in fixed-width machine
        # arithmetic, must have a value here and must denote the oracle's score.
        pl = shadow_plan_squared(tk, pk, qk)
        if pl is None:
            disagreements.append(("plan-has-no-value", tk, pk, qk, None, orc))
        elif abs(pl - orc) > RTOL * denom:
            disagreements.append(("plan-value", tk, pk, qk, pl, orc))
        agg = {"agree": int(tk), "spreadA": int(pk), "spreadB": int(qk)}
        # THE TIE. The spec requires the returned NUMBER to be the number the
        # returned PLAN yields, at this call's own width and aggregates. Compared
        # exactly (rationals, no tolerance): a tie that held only to within a
        # tolerance would not be the obligation the spec states.
        tie_plan = rat_plan_value(WIDTH, agg, RETURNED_PLAN)
        if tie_plan != shadow_value_exact(tk, pk, qk):
            disagreements.append(("tie", tk, pk, qk, tie_plan,
                                  shadow_value_exact(tk, pk, qk)))
        if rat_plan_value(WIDTH, agg, PRODUCT_FIRST_PLAN) is None:
            prod_first_valueless += 1
        # The reach of the SHORT-CIRCUIT on real label data: inputs where the
        # combine step run unconditionally has NO value (a spread vanishes) while
        # the oracle does return a number. There the `zeroThen` step is the only
        # reason the routine answers at all, so a refinement that drops it
        # answers nothing where the oracle answers 0.
        if rat_plan_value(WIDTH, agg, COMBINE_PLAN) is None:
            unguarded_valueless += 1
        # THIRD observable: the register carrier. Count the inputs where
        # combining through the register product of the two spreads gives a
        # DIFFERENT number from the exact coefficient -- i.e. where the value
        # clause's carrier distinction actually bites on real data.
        reg_route = shadow_register_route_squared(tk, pk, qk)
        if reg_route is not None:
            if reg_route != Fraction(int(tk) * int(tk), int(pk) * int(qk)):
                register_diverges += 1
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for leg, tk, pk, qk, sh, orc in disagreements:
            print("  [%s] (tk=%d,pk=%d,qk=%d) shadow=%r oracle=%r"
                  % (leg, tk, pk, qk, sh, orc))
        return 1
    if not prod_first_valueless:
        # Not a fidelity failure of the shipped routine, but the run would carry
        # no evidence that the plan observable discriminates anything on real
        # data, which is the one thing this leg exists to show.
        print("G-CONF FAIL: the product-first plan kept a value at width %d on "
              "every one of the %d inputs, so this fuzz never reached the "
              "regime the plan clause separates (expected the F2P-scale witness "
              "to be one)." % (WIDTH, count))
        return 1
    if not register_diverges:
        # As above: not a fidelity failure of the shipped routine, but without a
        # single input where the register route parts company from the exact
        # coefficient, this run carries no evidence that the carrier distinction
        # the value clause rests on is reachable on real data.
        print("G-CONF FAIL: combining through the register product never "
              "diverged from the exact coefficient at width %d over the %d "
              "inputs, so this fuzz never reached the regime the value clause's "
              "carrier distinction separates (expected the F2P-scale witness to "
              "be one)." % (WIDTH, count))
        return 1
    if not unguarded_valueless:
        # As above: the shipped routine is fine, but without one input on which
        # the unconditional combine has no value, this run carries no evidence
        # that the returned plan's short-circuit is reachable on real label data.
        print("G-CONF FAIL: the combine step never lost its value at width %d "
              "over the %d admissible inputs, so this fuzz never reached a "
              "vanishing spread and carries no evidence that the returned plan's "
              "short-circuit is load-bearing (expected the fully-split label "
              "arrays to be such an input)." % (WIDTH, count))
        return 1
    print("G-CONF OK: R/I shadow of fowlkesCoeffSquared agrees with patch.diff "
          "behaviour (squared) on %d inputs (seed=%d, %d skipped outside "
          "Requires), 0 disagreements; the returned PLAN also has a value at "
          "width %d on all %d and denotes the same score, while the "
          "product-first plan is valueless on %d of them. The TIE holds "
          "exactly (rational equality, no tolerance) on all %d: the returned "
          "number IS the returned plan's number. On %d of the inputs a spread "
          "vanishes, so the combine step run unconditionally has no value while "
          "the oracle still returns a number -- the returned plan's "
          "short-circuit is what answers there."
          % (count, SEED, skipped, WIDTH, count, prod_first_valueless, count,
             unguarded_valueless))
    return 0


if __name__ == "__main__":
    sys.exit(main())
