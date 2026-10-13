#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-10844.

This bundle consumes NO axiom. Its single callee — the positive square root
`np.sqrt` — is handled by squaring (refinement.md, mapping.md §3): the modeled
routine returns the SQUARED similarity coefficient `v = agree^2/(spreadA*spreadB)`
together with the PLAN by which that coefficient is assembled. G-AX therefore
validates the deep-model references the spec's two observables rest on:

  (A-reference, soundness of squaring)  the model's squared coefficient
      `tk^2 / (pk*qk)` equals the SQUARE of the REAL patched formula
      `np.sqrt(tk/pk) * np.sqrt(tk/qk)` — i.e. the deep model agrees with the
      unchanged-callee computation as the (squared) score.

  (P-reference, soundness of the plan semantics)  `RatPlan`/`IntPlan.value` in
      Solution.lean's pure region model fixed-width machine arithmetic: a
      materialised integer product has a value only while it fits the word. Here
      that model is transliterated to Python and executed at width 64 (the
      dtype the gold patch's aggregates carry) on the same aggregates:

        * the plan the routine returns (pair the agreement count with each
          spread, then multiply the two exact ratios) HAS a value on every
          admissible aggregate triple, and that value equals the squared patched
          score;
        * the product-first plan (materialise `agree*agree` and
          `spreadA*spreadB`, then take one ratio) has NO value at the documented
          large-aggregate input — and the REAL numpy pre-patch expression
          `tk / np.sqrt(pk*qk)` is `nan` there while the patched one is finite.
          So the model's partiality is the real machine failure, not an artifact.

  (S-reference, the short-circuit is a real obligation)  the returned plan
      decides the zero-agreement case BEFORE forming a quotient (`zeroThen`), and
      the tie clause makes the returned number that plan's number. Grounded here
      rather than argued: on an admissible triple whose spread vanishes -- a
      partition with every element in a group of its own, aggregates (0, 0, 30) --
      the real patched arithmetic returns a finite 0 with the zero test in place
      and NO number (non-finite) with it dropped, in both refinement shapes
      (divide first, or promote the spreads to an exact product first). The plan
      semantics splits the two the same way: the returned plan yields 0 there and
      the bare combine step has no value. The NEGATIVE CONTROL is run too: the
      model's rational arithmetic is TOTAL and reports the same number for the
      guarded and the unguarded value expression, there and across the admissible
      domain -- so the reading that takes an unguarded value expression for an
      unguarded routine is refuted by the machine, not by preference.

  (width-universality)  the spec quantifies the plan clause over EVERY machine
      word width that holds the aggregates, which is what forbids materialising
      ANY aggregate product rather than one named product. Executed here: at the
      small widths, aggregates the word holds whose product it does not are
      exhibited, the product-first plan is valueless on them, and the returned
      plan still yields the exact coefficient.

Runs the real `numpy` (the same library the gold patch calls). stdlib + numpy
only; nothing repo-specific. Exit 0 iff every obligation holds.
"""
import sys
import random
import warnings
from fractions import Fraction

import numpy as np

# Match the gold patch's wide-integer dtype (the `.astype(np.int64)` hunk).
INT = np.int64
WIDTH = 64                      # the machine word the real aggregates carry


# ---------------------------------------------------------------------------
# Transliteration of Solution.lean's pure region: plans and their fixed-width
# partial semantics. A plan is a nested tuple; ('read', k) reads aggregate k.
# ---------------------------------------------------------------------------
# The COMBINE step of the returned plan: pair the agreement count with each
# spread, then multiply the two exact ratios.
COMBINE_PLAN = ("rmul",
                ("ratio", ("read", "agree"), ("read", "spreadA")),
                ("ratio", ("read", "agree"), ("read", "spreadB")))
# The plan the routine actually RETURNS: answer zero outright when the agreement
# count vanishes, and only otherwise run the combine. `zeroThen` is what makes
# "does this routine answer at all on a degenerate input" observable, and it is
# the step `check_degenerate_short_circuit` grounds against real arithmetic.
RETURNED_PLAN = ("zeroThen", ("read", "agree"), COMBINE_PLAN)
PRODUCT_FIRST_PLAN = ("ratio",
                      ("imul", ("read", "agree"), ("read", "agree")),
                      ("imul", ("read", "spreadA"), ("read", "spreadB")))


def trunc_w(width, x):
    """Transliteration of the pure region's `truncW`: writing an exact integer
    into a `width`-bit two's-complement register, with the machine's silent
    wraparound."""
    return (x + 2 ** (width - 1)) % (2 ** width) - 2 ** (width - 1)


def word_mul(width, x, y):
    """Transliteration of `instMulWord`: the register carrier's multiplication.
    Total, silent, and wrapping."""
    return trunc_w(width, x * y)


def in_word(width, x):
    """`inWord`: the integers a two's-complement word of `width` bits holds."""
    return -(2 ** (width - 1)) <= x <= 2 ** (width - 1) - 1


def int_plan_value(width, agg, plan):
    """`IntPlan.value`: None (no value) as soon as a materialised product leaves
    the word."""
    if plan[0] == "read":
        return agg[plan[1]]
    x = int_plan_value(width, agg, plan[1])
    y = int_plan_value(width, agg, plan[2])
    if x is None or y is None:
        return None
    prod = x * y
    return prod if in_word(width, prod) else None


def rat_plan_value(width, agg, plan):
    """`RatPlan.value`: an exact Fraction, or None if some integer step has no
    value at this width (or the divisor is zero)."""
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
            return Fraction(0)              # answered, rest NOT evaluated
        return rat_plan_value(width, agg, plan[2])
    x = rat_plan_value(width, agg, plan[1])
    y = rat_plan_value(width, agg, plan[2])
    if x is None or y is None:
        return None
    return x * y


def agg_of(tk, pk, qk):
    return {"agree": int(tk), "spreadA": int(pk), "spreadB": int(qk)}


def squared_model(tk, pk, qk):
    """Reference of Solution.lean's `fowlkesCoeffSquared` VALUE: the SQUARED
    score as an exact rational, computed divide-first (no pk*qk product).
    Returns a Python float for comparison (the magnitudes here are within
    float's exact range for the boundary set; fuzz uses the same divide-first
    association as the model, so no overflow)."""
    if tk == 0:
        return 0.0
    # divide first — exactly the model's `ra * rb`
    return (tk / pk) * (tk / qk)


def patched_score(tk, pk, qk):
    """The REAL patched formula np.sqrt(tk/pk) * np.sqrt(tk/qk) (or 0 if tk==0),
    on int64 operands — the unchanged-callee computation under test."""
    t = INT(tk); p = INT(pk); q = INT(qk)
    if tk == 0:
        return np.float64(0.0)
    return np.sqrt(t / p) * np.sqrt(t / q)


def prepatch_score(tk, pk, qk):
    """The REAL pre-patch formula tk / np.sqrt(pk*qk) on int64 operands. With
    overflow warnings silenced this yields nan when pk*qk overflows int64."""
    t = INT(tk); p = INT(pk); q = INT(qk)
    if tk == 0:
        return np.float64(0.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prod = p * q                      # may wrap negative (overflow)
        return t / np.sqrt(np.float64(prod))


def patched_score_unguarded(tk, pk, qk):
    """The patched ARITHMETIC with the zero test dropped: sqrt(t/p)*sqrt(t/q)
    evaluated unconditionally. On a triple whose spread vanishes this divides by
    zero, which is the whole point of the check below."""
    t = INT(tk); p = INT(pk); q = INT(qk)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.sqrt(t / p) * np.sqrt(t / q)


def promoted_product_unguarded(tk, pk, qk):
    """The other unguarded shape: promote both spreads out of their registers,
    form their exact product, and take one square root of one quotient. The
    promotion is legitimate (it is why this stays finite at large aggregates);
    dropping the zero test is not."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with np.errstate(divide="ignore", invalid="ignore"):
            num = np.float64(int(tk) * int(tk))
            den = np.float64(int(pk) * int(qk))
            return np.sqrt(num / den)


def rat_div(x, y):
    """The model's rational division, transliterated FAITHFULLY: Lean's `Rat`
    division is TOTAL and returns 0 on a zero divisor. That totality is a
    property of the carrier, not of any machine, and it is exactly why the
    returned VALUE cannot be the observable that carries the short-circuit."""
    return Fraction(0) if y == 0 else Fraction(x, y)


def value_slot_unguarded(tk, pk, qk):
    """What the model's value slot reports for an UNGUARDED combination: the
    product of the two total rational quotients, with no zero test."""
    return rat_div(int(tk), int(pk)) * rat_div(int(tk), int(qk))


def value_slot_promoted_unguarded(tk, pk, qk):
    """And for an UNGUARDED combination that promotes both spreads out of their
    registers and divides by their exact product."""
    return rat_div(int(tk) * int(tk), int(pk) * int(qk))


def value_slot_guarded(tk, pk, qk):
    """What the model's value slot reports for the GUARDED combination."""
    if tk == 0:
        return Fraction(0)
    return Fraction(int(tk), int(pk)) * Fraction(int(tk), int(qk))


def check_reference(tk, pk, qk):
    """A-reference: square of the REAL patched formula == the squared model."""
    score = patched_score(tk, pk, qk)
    assert np.isfinite(score), (
        "patched formula not finite on (tk=%d,pk=%d,qk=%d): %r"
        % (tk, pk, qk, score))
    observed = float(score) ** 2                      # real callee, squared
    expected = squared_model(tk, pk, qk)              # deep model
    # relative tolerance: both are float computations of the same rational
    denom = max(1.0, abs(expected))
    assert abs(observed - expected) <= 1e-9 * denom, (
        "squaring reference unsound on (tk=%d,pk=%d,qk=%d): "
        "patched^2=%r, model=%r" % (tk, pk, qk, observed, expected))


def check_plan_reference(tk, pk, qk):
    """P-reference: the plan the routine returns HAS a value at the real machine
    word width on this admissible triple, and that value is the exact squared
    coefficient (so the plan denotes the computation the value clause pins)."""
    agg = agg_of(tk, pk, qk)
    got = rat_plan_value(WIDTH, agg, RETURNED_PLAN)
    assert got is not None, (
        "returned plan has NO value at width %d on (tk=%d,pk=%d,qk=%d): the "
        "plan clause would be false of the real patched routine"
        % (WIDTH, tk, pk, qk))
    want = Fraction(int(tk), int(pk)) * Fraction(int(tk), int(qk))
    assert got == want, (
        "plan value disagrees with the exact coefficient on "
        "(tk=%d,pk=%d,qk=%d): plan=%s exact=%s" % (tk, pk, qk, got, want))


def check_register_reference():
    """R-reference for the register carrier of the three aggregates.

    The pure region models each aggregate as the contents of a `width`-bit
    register whose multiplication WRAPS (`truncW` / `instMulWord`). That is a
    claim about real machine arithmetic, so it is executed against real numpy
    `int64` multiplication rather than asserted in prose: the two must agree on
    every pair, both where the product fits the register and where it does not.

    A model whose wrap did not coincide with the machine's would make the value
    clause a statement about an imaginary machine, so this is the obligation the
    strengthened value clause rests on.
    """
    pairs = [
        (0, 0), (1, 1), (-1, 1), (7, 7), (123456789, 987654321),
        (2 ** 31, 2 ** 31), (2 ** 32, 2 ** 32), (-(2 ** 40), 2 ** 40),
        (5152663196, 3294371982),            # the F2P witness product
        (3003497866, 3003497866),            # the F2P numerator square
        (4000000000, 4000000000),            # a numerator-side wrap
        (2 ** 62, 2), (2 ** 62, 4), (-(2 ** 62), 4),
    ]
    rng = random.Random(108442)
    for _ in range(20000):
        pairs.append((rng.randint(-(2 ** 63), 2 ** 63 - 1),
                      rng.randint(-(2 ** 63), 2 ** 63 - 1)))
    wrapped = 0
    with np.errstate(over="ignore", invalid="ignore"):
        for x, y in pairs:
            machine = int(np.int64(x) * np.int64(y))
            model = word_mul(WIDTH, x, y)
            assert machine == model, (
                "register carrier diverges from real np.int64 multiplication at "
                "(%d, %d): machine %d, model %d" % (x, y, machine, model))
            if model != x * y:
                wrapped += 1
    # NON-VACUITY: the wrap must actually be reachable, or the carrier's
    # distinction between register and promoted arithmetic is decoration.
    assert wrapped > 0, (
        "the register multiplication never wrapped over %d pairs, so the "
        "carrier's wrap is unreachable and the value clause it supports would "
        "be vacuous" % len(pairs))
    # And the register must be FAITHFUL in range: where the exact product fits,
    # the register holds exactly it (so the carrier distorts nothing admissible).
    for x, y in [(1, 1), (7, 7), (3003497866, 3003497866), (123456789, 7)]:
        assert word_mul(WIDTH, x, y) == x * y, (
            "register multiplication must equal the exact product when it fits "
            "the word, failed at (%d, %d)" % (x, y))
    return wrapped, len(pairs)


def check_register_discriminates(tk, pk, qk):
    """At the F2P witness the register product of the two spreads is NEGATIVE,
    so a routine that combines through it divides by a negative quantity and
    cannot return the (nonnegative) coefficient -- which is what the value
    clause now rejects, and what real numpy does at that scale."""
    reg = word_mul(WIDTH, pk, qk)
    assert reg < 0, (
        "expected the register product of the two spreads to wrap negative at "
        "the F2P witness, got %d" % reg)
    exact = int(pk) * int(qk)
    assert reg != exact, "register product unexpectedly equals the exact product"
    # the coefficient the register route computes is not the coefficient:
    assert Fraction(tk * tk, exact) != Fraction(tk * tk, reg), (
        "the register route and the exact route unexpectedly agree")
    return reg


def check_degenerate_short_circuit():
    """The obligation the RETURNED PLAN's `zeroThen` carries, grounded against
    the real callee's arithmetic instead of asserted in prose.

    A partition that puts every element in a group of its own is an ORDINARY
    input to this computation, and it is admissible under every `require`: the
    aggregate of that partition's group sizes VANISHES, and because each spread
    is at least the agreement count, the agreement count vanishes with it. The
    aggregates are then (0, 0, s) for the other partition's spread s.

    Two readings of a routine whose value slot divides unconditionally are on
    offer, and they disagree about what such a routine does here:

      * read the VALUE SLOT as the arithmetic -> the model's rational quotient
        is total and reports 0 at a zero divisor, so the unguarded expression
        reports the required 0 and the routine looks fine;
      * read the returned PLAN as the arithmetic -> the combine step has NO
        value at a zero divisor, so a routine that runs it unconditionally
        produces nothing here, and only `zeroThen` produces the required 0.

    Real arithmetic decides between the two, and it decides for the plan: with
    the zero test in place both refinement shapes return a finite 0, and with it
    dropped BOTH return a non-finite value. So the first reading attributes to a
    routine a number the machine does not produce. The NEGATIVE CONTROL is the
    last assertion: the value slot reports the SAME rational for the guarded
    combination and for BOTH unguarded shapes (divide first, or promote the two
    spreads to an exact product first), at this triple and across the admissible
    domain, so no clause about the returned number could have separated them --
    an identity of the returned pair, re-executed on every run rather than
    argued. Which is
    why the tie clause pins the returned number to the returned PLAN, and why the
    short-circuit is an obligation on a refinement rather than a convenience.
    """
    tk, pk, qk = 0, 0, 30            # every element in its own group, 6 elements
    # ADMISSIBLE: nonnegative, each spread at least the agreement count, in word.
    assert 0 <= tk <= pk and tk <= qk, "degenerate triple must be admissible"
    for x in (tk, pk, qk):
        assert in_word(WIDTH, x), "degenerate triple must fit the machine word"

    # 1. the real arithmetic, with the zero test in place: a finite 0.
    for name, got in (("ratio-first", patched_score(tk, pk, qk)),):
        assert np.isfinite(got) and float(got) == 0.0, (
            "the %s shape WITH the zero test must return a finite 0 on the "
            "degenerate triple, got %r" % (name, got))

    # 2. the same real arithmetic with the zero test dropped: no number at all,
    #    in BOTH refinement shapes (dividing the ratios first, and promoting the
    #    spreads to an exact product first).
    for name, got in (("ratio-first", patched_score_unguarded(tk, pk, qk)),
                      ("promoted-product",
                       promoted_product_unguarded(tk, pk, qk))):
        assert not np.isfinite(got), (
            "the unguarded %s shape was expected to produce no number on the "
            "degenerate triple, got %r" % (name, got))

    # 3. the plan semantics predicts exactly that split: the returned plan has a
    #    value (0) and the bare combine step has none.
    agg = agg_of(tk, pk, qk)
    got = rat_plan_value(WIDTH, agg, RETURNED_PLAN)
    assert got == Fraction(0), (
        "the returned plan must yield 0 on the degenerate triple, got %s" % got)
    assert rat_plan_value(WIDTH, agg, COMBINE_PLAN) is None, (
        "the combine step run unconditionally must have NO value on the "
        "degenerate triple; if it had one the plan clause would not carry the "
        "short-circuit")

    # 4. NEGATIVE CONTROL for the unmodelled reading. The value slot cannot see
    #    the difference the machine makes: guarded and unguarded agree here...
    assert (value_slot_unguarded(tk, pk, qk)
            == value_slot_promoted_unguarded(tk, pk, qk)
            == value_slot_guarded(tk, pk, qk) == Fraction(0)), (
        "expected the model's total rational arithmetic to report 0 for the "
        "guarded value expression AND for both unguarded shapes on the "
        "degenerate triple")
    #    ...and everywhere else on the admissible domain, so the agreement is not
    #    an accident of one input. (A vanishing spread forces a vanishing
    #    agreement count, so these are all the degenerate triples there are.)
    rng = random.Random(1084430)
    degenerate = 0
    for _ in range(4000):
        s_pk = rng.choice([0, rng.randint(0, 2 ** 20)])
        s_qk = rng.choice([0, rng.randint(0, 2 ** 20)])
        s_tk = rng.randint(0, min(s_pk, s_qk)) if min(s_pk, s_qk) > 0 else 0
        shapes = (value_slot_guarded(s_tk, s_pk, s_qk),
                  value_slot_unguarded(s_tk, s_pk, s_qk),
                  value_slot_promoted_unguarded(s_tk, s_pk, s_qk))
        assert shapes[0] == shapes[1] == shapes[2], (
            "the value slot separated the guarded expression from an unguarded "
            "one at (%d,%d,%d): %s; the tie clause would then be unnecessary, "
            "because a clause about the returned NUMBER would already reject the "
            "unguarded shapes" % (s_tk, s_pk, s_qk, shapes))
        if s_pk == 0 or s_qk == 0:
            degenerate += 1
    assert degenerate > 0, (
        "no degenerate triple was drawn, so this sweep does not reach the "
        "regime the short-circuit governs")
    #    Non-vacuity of the OTHER direction: where no spread vanishes, dropping
    #    the zero test costs nothing, so what the check above isolates is the
    #    vanishing spread and not the vanishing agreement count.
    ok = patched_score_unguarded(0, 5, 7)
    assert np.isfinite(ok) and float(ok) == 0.0, (
        "with both spreads positive the unguarded shape must still return a "
        "finite 0 at a vanishing agreement count, got %r" % ok)
    return degenerate


def main():
    # --- the register carrier IS the machine (R-reference, non-vacuous) ----
    reg_wrapped, reg_pairs = check_register_reference()

    # --- the short-circuit is a real obligation, not a convenience ---------
    degenerate_seen = check_degenerate_short_circuit()

    # --- boundary aggregates (small, exact in float) ----------------------
    boundary = [
        (1, 1, 1), (0, 1, 1), (0, 5, 7), (1, 2, 8),
        (3, 4, 9), (10, 100, 100), (2, 3, 3),
        (123, 456, 789), (1, 1000000, 1000000),
    ]
    for tk, pk, qk in boundary:
        check_reference(tk, pk, qk)
        check_plan_reference(tk, pk, qk)

    # --- randomized fuzz over realistic aggregate magnitudes --------------
    rng = random.Random(10844)
    plan_none = 0
    for _ in range(20000):
        # aggregates up to ~ (2^31)^2-scale: ratios stay in float's exact band,
        # products would overflow int64 — exactly the regime of interest.
        pk = rng.randint(1, 2 ** 40)
        qk = rng.randint(1, 2 ** 40)
        tk = rng.randint(0, min(pk, qk))   # tk <= pk,qk (a real coefficient <= 1)
        check_reference(tk, pk, qk)
        check_plan_reference(tk, pk, qk)
        if rat_plan_value(WIDTH, agg_of(tk, pk, qk), PRODUCT_FIRST_PLAN) is None:
            plan_none += 1
    assert plan_none > 0, (
        "the product-first plan never lost its value over the fuzz range, so "
        "this fuzz does not reach the regime the plan clause discriminates")

    # --- faithfulness of the plan discriminator (the actual bug) -----------
    # The F2P-scale aggregates (from the gold test's label arrays):
    f2p = (3003497866, 5152663196, 3294371982)
    tk, pk, qk = f2p
    assert (int(pk) * int(qk)) > np.iinfo(np.int64).max, (
        "expected pk*qk to exceed int64 range for the F2P witness")
    pre = prepatch_score(tk, pk, qk)
    post = patched_score(tk, pk, qk)
    assert not np.isfinite(pre), (
        "pre-patch was expected to overflow to nan at F2P scale, got %r" % pre)
    assert np.isfinite(post), (
        "patched formula must stay finite at F2P scale, got %r" % post)
    # and the model agrees with the patched (squared) value at this scale:
    check_reference(tk, pk, qk)
    # the plan observable separates the two routines at exactly this point, and
    # separates them the same way the real machine does:
    agg = agg_of(tk, pk, qk)
    assert rat_plan_value(WIDTH, agg, PRODUCT_FIRST_PLAN) is None, (
        "the product-first plan was expected to have NO value at width %d on "
        "the F2P witness (its denominator product leaves the word)" % WIDTH)
    check_plan_reference(tk, pk, qk)
    # ...and the register carrier separates them at the same point, the same way:
    reg_prod = check_register_discriminates(tk, pk, qk)

    # --- width-universality: no materialised aggregate product survives ----
    # For each small width, the largest value the word holds is m = 2^(w-1)-1;
    # every product a plan can materialise from three copies of m is at least
    # m^2, which the word does not hold. So the product-first plan is valueless
    # while the returned plan still yields the exact coefficient — the mechanised
    # content of quantifying the plan clause over every width.
    for w in range(3, 17):
        m = 2 ** (w - 1) - 1
        agg = agg_of(m, m, m)
        assert not in_word(w, m * m), "width %d: m^2 unexpectedly fits" % w
        assert rat_plan_value(w, agg, PRODUCT_FIRST_PLAN) is None, (
            "width %d: the product-first plan unexpectedly has a value on "
            "aggregates the word holds" % w)
        got = rat_plan_value(w, agg, RETURNED_PLAN)
        assert got == Fraction(1, 1), (
            "width %d: the returned plan must still yield the exact "
            "coefficient (1), got %s" % (w, got))

    print("G-AX OK: squaring reference sound (patched^2 == squared model) on "
          "%d boundary + 20000 fuzz aggregates; plan reference sound (the "
          "returned plan has a value at width %d there and equals the exact "
          "coefficient, %d fuzz triples where the product-first plan does not); "
          "plan discriminator faithful - at the F2P witness the product-first "
          "plan has no value and real numpy pre-patch is nan, while the "
          "returned plan and the patched formula are both fine; "
          "width-universality checked at widths 3..16; register carrier == real "
          "np.int64 multiplication on %d pairs (%d of them wrapping, so the "
          "wrap is reachable and not decoration), and at the F2P witness the "
          "register product of the two spreads wraps to %d < 0 while the exact "
          "product is %d. Short-circuit reference sound: on the degenerate "
          "admissible triple (0, 0, 30) the real arithmetic returns a finite 0 "
          "with the zero test and no number without it (both refinement shapes), "
          "the returned plan yields 0 there while the bare combine step has no "
          "value, and the negative control holds - the model's total rational "
          "arithmetic reports the same number for the guarded and the unguarded "
          "value expression across the admissible domain (%d degenerate triples "
          "drawn), so the plan and the tie clause are what carry the "
          "short-circuit."
          % (len(boundary), WIDTH, plan_none, reg_pairs, reg_wrapped,
             reg_prod, int(f2p[1]) * int(f2p[2]), degenerate_seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
