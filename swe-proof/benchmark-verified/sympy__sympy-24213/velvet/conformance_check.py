#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24213.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`combineAddends`,
              `checkAddends`/`checkStep`, `sumFactors`) transliterated to Python
              over the *real* repo types, via the mapping.md bijection. The
              A-tagged callee `equivalent_dims` is NOT replaced by an axiom model
              here; G-CONF isolates the R/I legs, so the dimensional-equivalence
              test is left as the real repo callee (mapping.md §4). The shadow
              returns one of the THREE outcomes of the `Combined` carrier:
              `("ok", reported_dim)`, `("disagree", None)`, `("nosig", None)`.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `UnitSystem._collect_factor_and_dimension` Add branch applied at
              base_commit (the real correctness oracle, G-RESOLVE). We invoke it
              on the same sum expression and observe WHICH of the three outcomes
              it produced — a returned `(factor, dim)`, a dimensional
              disagreement, or an abandoned combination whose comparison never
              happened.

They must agree on every Add expression: the same one of the three outcomes and,
when returning, the same reported dimension. Grading the two non-returning
outcomes SEPARATELY is what makes this check able to see the distinction the
spec pins; a check that merged them into a single "raised" verdict would pass
for a routine that reports a dimensional disagreement about a pair of dimensions
it never compared. Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 24213
N_FUZZ = 100_000


def build_quantity(SI, name, dim, scale_dim_quantity):
    """A Quantity with the given dimension and a scale factor of the matching
    unit expression so _collect_factor_and_dimension can collect it."""
    from sympy.physics.units import Quantity
    q = Quantity(name)
    SI.set_quantity_dimension(q, dim)
    SI.set_quantity_scale_factor(q, scale_dim_quantity)
    return q


def shadow_addbranch(ds, addends):
    """R/I shadow of combineAddends over a list of (factor, dim) sub-results.

    `addends[0]` is `first`; the rest are `rest`. `checkAddends` folds the
    per-addend test using the REAL equivalent_dims (A-tagged callee, left real per
    mapping.md §4). Returns one of THREE outcomes, matching the three-valued
    `Combined` carrier:

      ("ok", first_dim)     — every addend certified;
      ("disagree", None)    — the equivalence test RAN, on signatures it had, and
                              returned "not equivalent";
      ("nosig", None)       — the test could not run at all: a dimension in play
                              admits no signature, so the reduction the test is
                              built on fails before any comparison.

    The last two are DISTINCT outcomes and the shadow must not fold them
    together — that fold is the whole thing this bundle's spec had to be
    strengthened to see. Which one holds is decided by the LEFTMOST addend that is
    not certified, in the manner in which IT failed (`checkStep`), so the loop
    stops at the first non-certified addend rather than scanning ahead."""
    first_factor, first_dim = addends[0]
    outcome = None                                # None == still certified
    factor = first_factor
    for f, d in addends[1:]:
        # A3 (A-reference, left as the real callee in the R/I shadow). The
        # reduction equivalent_dims performs is PARTIAL: when a dimension in play
        # admits no signature it raises instead of returning a verdict, which the
        # `Option`-valued `deps` carrier spells `none` and `checkStep` answers
        # with the signature-less outcome (mapping.md §2 rows 3, 5a, 5b).
        if outcome is None:
            try:
                if not bool(ds.equivalent_dims(first_dim, d)):
                    outcome = ("disagree", None)
            except TypeError:
                outcome = ("nosig", None)
        factor = factor + f                       # A2: sumFactors fold (I)
    if outcome is None:
        return ("ok", first_dim)                  # A4a: Combined.reported
    return outcome                                # A4b / A4c


def oracle_addbranch(SI, expr):
    """patch.diff's behaviour: run the patched _collect_factor_and_dimension on
    the Add expression and report which of the three outcomes it produced.

    The two non-returning outcomes are NOT merged. What a caller is handed when a
    sum's dimensions were compared and found different is a different observation
    from what it is handed when the comparison could not be carried out at all,
    and the repository's own consistency checks grade sums by which of the two
    they get. Collapsing them here would make the shadow blind to exactly the
    distinction the spec now pins, so the graded class is reported."""
    try:
        _factor, dim = SI._collect_factor_and_dimension(expr)
        return ("ok", dim)
    except ValueError:
        # the dimensional-disagreement report: the comparison ran and the
        # dimensions of the sum's addends did not agree.
        return ("disagree", None)
    except TypeError:
        # no verdict was produced at all: the reduction the comparison is built
        # on failed first, on a dimension that admits no signature.
        return ("nosig", None)


def main():
    from sympy import Float, Integer, Rational
    from sympy.core.add import Add
    from sympy.physics.units.systems.si import SI
    from sympy.physics.units import (
        meter, second, kilogram, ampere, Dimension,
        velocity, acceleration, time, length, mass,
    )
    ds = SI.get_dimension_system()

    # Base quantities with coherent SI scale factors. Composite *term*
    # expressions (products of these) are what exercise the surface-distinct
    # dimension carriers (e.g. a1*t1 collects to dimension `acceleration*time`,
    # surface-distinct from `velocity` yet dimensionally equivalent — the bug).
    v1 = build_quantity(SI, "cf_v1", velocity, meter / second)
    a1 = build_quantity(SI, "cf_a1", acceleration, meter / second**2)
    t1 = build_quantity(SI, "cf_t1", time, second)
    l1 = build_quantity(SI, "cf_l1", length, meter)
    m1 = build_quantity(SI, "cf_m1", mass, kilogram)

    # Each term is a SymPy expression whose collected dimension may be a Mul/Pow
    # (surface-distinct) rather than a bare Dimension symbol.
    #
    # The last four terms carry MIXED-NUMERIC-TYPE / MIXED-PRECISION dimension
    # exponents. They matter because SymPy numbers compare equal across type while
    # hashing differently (Integer(2) == Float(2.0); Float('2.0',5) ==
    # Float('2.0',50)), so `l1**2` and `l1**2.0` collect to the surface-distinct
    # dimensions Dimension(length**2) / Dimension(length**2.0) that the real
    # `equivalent_dims` nevertheless ACCEPTS as equivalent. An integer-exponent-only
    # pool never builds such a pair and so cannot exercise the eq/hash split at all
    # (mapping.md §2.1).
    terms = [
        v1,            # velocity (symbol surface)
        a1 * t1,       # acceleration*time  (== velocity, surface-distinct)
        a1,            # acceleration
        t1,            # time
        l1,            # length
        m1 * a1,       # mass*acceleration  (== force)
        v1 + 0,        # velocity again (alias)
        l1 / t1,       # length/time (== velocity)
        a1 * t1 * t1,  # acceleration*time^2 (== length)
        m1 * l1,       # mass*length
        l1**Integer(2),         # Dimension(length**2)
        l1**Float(2.0),         # Dimension(length**2.0)   -- equivalent, distinct
        l1**Rational(4, 2),     # Dimension(length**2)     via a Rational power
        l1**Float('2.0', 50),   # Dimension(length**2.0)   at another precision
        # NO-SIGNATURE dimensions: an Add-named Dimension cannot be reduced to
        # base-dimension powers (dimensions.py:383-395 raises TypeError), so
        # equivalent_dims raises rather than returning a verdict. This class is a
        # genuine patch delta -- pre-patch the guard was a surface test that never
        # reduced anything, so `b1 + b2` returned a value (mapping.md §2.1).
        build_quantity(SI, "cf_b1", Dimension(length + time), meter),
        build_quantity(SI, "cf_b2", Dimension(length + time), 2 * meter),
        build_quantity(SI, "cf_b3", Dimension(mass + time), kilogram),
    ]

    # For the ORDERING class below we need to control which addend the routine
    # meets FIRST, and a sum does not preserve the order its addends were written
    # in — it canonicalises them, here by name. So the two probes are built from
    # two signature-less quantities whose names bracket `cf_l1`/`cf_t1`: `cf_a0`
    # sorts ahead of them (the routine meets the signature-less addend first) and
    # `cf_z9` sorts behind them (it meets the disagreeing pair first). Same
    # dimensions, same multiset of failures, different first failure.
    b_first = build_quantity(SI, "cf_a0", Dimension(length + time), meter)
    b_last = build_quantity(SI, "cf_z9", Dimension(length + time), meter)

    # NOT in this pool: the SAME-PRINTED-FORM, DIFFERENT-ASSUMPTIONS exponent pair
    # (`length**n` against a positive `n`). It is a real class and it IS covered —
    # by axiom_check.py, which reaches the dimension comparison directly — but it
    # cannot be reached through a sum. Measured: a quantity carrying such a
    # dimension fails in the RECURSIVE SUB-COLLECTION of its own addend, before the
    # combination step this check shadows is entered at all, so `trial` discards it
    # as out of the modeled domain and adding it here would claim coverage that
    # never runs.

    rng = random.Random(SEED)
    disagreements = []

    def trial(chosen_terms):
        # oracle: the Add of the chosen terms. Build the real sum expression.
        expr = Add(*chosen_terms)
        # Need a genuine multi-addend Add (terms may combine/cancel).
        if not getattr(expr, "is_Add", False) or len(expr.args) < 2:
            return None
        # Faithful to the real Add branch: first = args[0], rest = args[1:];
        # each addend's (factor, dim) is the REAL recursive sub-collection
        # (the unchanged callee), exactly the bijection mapping.md §1/§2.
        try:
            subs = [SI._collect_factor_and_dimension(a) for a in expr.args]
        except Exception:
            return None       # un-collectable addend: out of the modeled domain
        shadow = shadow_addbranch(ds, subs)
        oracle = oracle_addbranch(SI, expr)
        if shadow[0] != oracle[0]:
            return (chosen_terms, shadow, oracle)
        if shadow[0] == "ok":
            # reported dim must be dimensionally equal (shadow reports first dim)
            if not ds.equivalent_dims(shadow[1], oracle[1]):
                return (chosen_terms, shadow, oracle)
        return None

    # --- boundary trials -----------------------------------------------------
    boundary = [
        [v1, a1 * t1],            # the issue: velocity + acceleration*time (ok)
        [a1 * t1, v1],            # reversed order
        [v1, a1],                 # velocity + acceleration (raise)
        [l1, t1],                 # length + time (raise)
        [v1, l1 / t1],            # velocity + length/time (ok)
        [a1 * t1, l1 / t1, v1],   # 3-term, all velocity-equivalent (ok)
        [v1, a1 * t1, a1],        # 3-term, one inconsistent (raise)
        [m1 * a1, m1 * a1],       # force + force (ok)
        [a1 * t1 * t1, l1],       # acceleration*time^2 + length (ok)
        # G-PANEL-2's witness class: mixed numeric TYPE / PRECISION in the
        # dimension exponent. Surface-distinct, dimensionally equivalent, and
        # ACCEPTED by the patched repo — the region a hash-keyed bridge got wrong.
        [l1**Integer(2), l1**Float(2.0)],
        [l1**Float(2.0), l1**Integer(2)],            # reversed order
        [l1**Float(2.0), l1**Rational(4, 2)],
        [l1**Float('2.0', 5), l1**Float('2.0', 50)],
        [l1**Integer(2), l1**Float(2.0), l1**Rational(4, 2)],   # 3-term, all ok
        [l1**Integer(2), l1**Float(3.0)],            # genuinely different (raise)
        # The NO-SIGNATURE leg. `b1 + b2` is the patch delta: pre-patch returned
        # a value, post-patch reports none.
        [terms[-3], terms[-2]],       # b1 + b2: same unreducible surface
        [terms[-3], terms[-1]],       # b1 + b3: different unreducible surfaces
        [terms[-3], l1],              # unreducible reference, reducible addend
        [l1, terms[-3]],              # reducible reference, unreducible addend
        [l1, l1, terms[-3]],          # unreducible arriving at the 2nd addend
        [t1, terms[-3]],              # inequivalent AND unreducible
        # THE ORDERING CLASS. Both non-returning outcomes are reachable in the
        # SAME sum, and which one comes back depends on which failing addend the
        # routine meets FIRST: it walks the addends in the sum's own order and
        # stops at the first one it cannot carry through, so a later disagreement
        # does not override an earlier missing signature or vice versa. These two
        # sums hold dimensionally identical addends and differ only in where the
        # signature-less one falls, and they must produce DIFFERENT outcomes. A
        # shadow that scanned the whole sum for a disagreement before considering
        # reducibility, or that merged the two outcomes, agrees with the oracle on
        # at most one of them.
        [l1, t1, b_first],            # signature-less addend met first
        [l1, t1, b_last],             # disagreeing pair met first
        [l1, b_first, l1],            # signature-less first, equivalent tail
        [l1, t1, t1],                 # disagreement, no signature-less present
    ]
    count = 0
    for chosen in boundary:
        count += 1
        r = trial(chosen)
        if r:
            disagreements.append(r)

    # --- the ordering class is LIVE: the two probes really do produce DIFFERENT
    # --- outcomes on this repo, so they are not two spellings of one verdict. If
    # --- they agreed, the separation of the two non-returning outcomes would be
    # --- untested and this check would be claiming coverage it does not have.
    o_first = oracle_addbranch(SI, Add(l1, t1, b_first))
    o_last = oracle_addbranch(SI, Add(l1, t1, b_last))
    if o_first[0] == o_last[0]:
        print("G-CONF FAIL: the ordering class is VACUOUS — both probes gave "
              "%r, so the separation of the two non-returning outcomes is "
              "untested here." % (o_first[0],))
        return 1

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_FUZZ):
        k = rng.randint(2, 4)
        chosen = [rng.choice(terms) for _ in range(k)]
        count += 1
        r = trial(chosen)
        if r:
            disagreements.append(r)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d trials:"
              % (len(disagreements), count))
        for chosen, sh, orc in disagreements:
            tags = [str(t) for t in chosen]
            print("  addends=%r shadow=%r oracle=%r" % (tags, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of combineAddends agrees with patch.diff "
          "behaviour on %d trials (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
