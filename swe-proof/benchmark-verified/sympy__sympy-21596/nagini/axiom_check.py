#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21596.

This bundle has NO consumed @ContractOnly axiom. The changed operation -- how
the per-index keep/drop collections are applied to the base domain (a per-index
intersect-with-keep then subtract-drop) -- is modelled DEEPLY by model.py's
`survives` / `kept_seq` (the pure region). The two index collections fed to the
model are produced by UNCHANGED callees and taken as model input.

This script validates the deep model as an A-reference against the REAL fixed
`imageset(Lambda(n, f), base).intersect(S.Reals)` behaviour, in-container (so it
exercises the gold-patched code). The check is made HONESTLY at the INDEX level:

  (A-reference)  for each in-scope issue/F2P case and each base index k in a
      finite window, the model's per-index decision
          survives(k, keep, drop)  ==  contains(keep,k) and not contains(drop,k)
      AGREES with whether the real fixed result retains index k, i.e. with
          gold_keeps(k) := f(k) is finite and real and f(k) in real_result.
      The equivalence is asserted as a full biconditional on every window index
      (both directions), with NO value-realness mask applied to only one side
      -- so a model that over-keeps an index whose image is non-real (e.g. a
      pole f(k)=zoo) is caught, not hidden.

  keep   = the per-factor LINEAR roots of numer(im)        (the modeled regime)
  drop   = EVERY window index k where some denominator of f vanishes (f(k) is
           non-finite); this faithfully models the gold's denominator
           subtraction for ALL denominator factors, linear or not.

REGIME / SCOPE (in-scope vs out-of-scope, reported loudly):
  The model covers the regime where the imaginary-part numerator is a product
  of factors each LINEAR in the index (every factor solvable to a scalar root).
  When a factor is NON-linear (the real callee yields a non-scalar / ConditionSet
  solution), the real result is itself a ConditionSet-image rather than a finite
  index list -- this is OUTSIDE the modeled regime. Such an F2P case is reported
  as SKIPPED-OUT-OF-SCOPE and is NOT silently passed: the script records it and
  asserts (a) the in-scope cases still fully discriminate, and (b) the only
  skipped F2P case is the documented out-of-scope one (the quadratic
  imaginary-part case). If any OTHER F2P case were skipped, the gate fails.

Imports nothing repo-specific beyond `sympy` itself (the library under change).
Exit 0 iff every obligation holds.
"""
import sys
import random

from sympy import (S, I, Lambda, imageset, FiniteSet, Union, Eq, Integer,
                   Rational, oo)
from sympy.abc import n
from sympy.core.mul import Mul
from sympy.solvers.solvers import solve_linear, denoms
from sympy.simplify.radsimp import numer
from sympy.sets.conditionset import ConditionSet


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def contains(seq, v):
    return any(x == v for x in seq)


def survives(v, keep, drop):
    """model.py: survives(v, keep, drop)."""
    return contains(keep, v) and not contains(drop, v)


def kept_seq(base, keep, drop):
    """model.py: kept_seq(base, keep, drop)."""
    return [b for b in base if survives(b, keep, drop)]


def keep_filter(base, keep):
    """model.py: keep_filter(base, keep) -- step 1, intersection with keep
    (the gold's `base_set &= _solution_union(numer(im) factors)` step)."""
    return [b for b in base if contains(keep, b)]


def drop_filter(seq, drop):
    """model.py: drop_filter(seq, drop) -- step 2, difference with drop
    (the gold's `base_set -= _solution_union(denoms(f) factors)` step)."""
    return [s for s in seq if not contains(drop, s)]


# --- the two index collections, produced by the UNCHANGED callees ------------

def linear_roots(exprs, sym):
    """The per-factor LINEAR roots (the scalars a factor contributes). A factor
    that is not linear in sym is not scalar-solvable; we flag it via `conditional`
    so the caller can decide the case is out of the modeled regime."""
    roots = []
    conditional = False
    for i in exprs:
        x, xis = solve_linear(i, 0, [sym])
        if x == sym:
            roots.append(xis)
        else:
            conditional = True
    return roots, conditional


def imag_part(f):
    """Reproduce intersection.py's real/imag split for f over a real symbol."""
    from sympy import Dummy
    from sympy.core.function import expand_complex
    n_ = Dummy(n.name, real=True)
    f_ = f.subs(n, n_)
    re, im = f_.as_real_imag()
    im = expand_complex(im)
    im = im.subs(n_, n)
    return im


def denominator_zero_indices(f, base_idx):
    """EVERY base index k at which some denominator of f vanishes (so f(k) is a
    pole / non-finite). This faithfully models the gold denominator subtraction
    for ALL denominator factors -- including non-linear ones whose roots a
    per-factor linear solve would miss."""
    drop = []
    ds = denoms(f)
    for k in base_idx:
        for d in ds:
            if d.subs(n, k) == 0:
                drop.append(k)
                break
    return drop


# --- the check --------------------------------------------------------------

def gold_keeps(f, k, real_result):
    """Does the real fixed result retain index k? True iff f(k) is a finite,
    real value that lies in the real result. No one-sided masking: this is the
    single ground-truth predicate both directions of the biconditional use."""
    val = f.subs(n, k)
    if val.is_finite is False or val.is_finite is None:
        # a pole / non-finite image is never retained
        if val.is_finite is None:
            # be conservative: treat unknown-finiteness as non-real -> not kept
            return False
        return False
    if val.is_real is not True:
        return False
    return bool(val in real_result)


def _solution_union(exprs, sym):
    """The gold-added helper, reproduced VERBATIM (sympy/sets/handlers/
    intersection.py:283-294 post-patch): a Union of the per-factor linear
    solutions (FiniteSet of the scalar root) or, for a non-scalar factor, a
    ConditionSet of its roots. Used to recompute the gold's two set operations
    (base_set &= _solution_union(...) ; base_set -= _solution_union(...)) so the
    two-step model can be validated against the gold's ACTUAL step ordering."""
    sols = []
    for i in exprs:
        x, xis = solve_linear(i, 0, [sym])
        if x == sym:
            sols.append(FiniteSet(xis))
        else:
            sols.append(ConditionSet(sym, Eq(i, 0)))
    return Union(*sols)


def check_two_step(f, base_set, base_idx, keep, drop, label):
    """Validate the WIDENED model (collect_real_indices_two_step) against the
    gold's two SEPARATE _solution_union call sites, at the index level:

      step 1  base_set &= _solution_union(Mul.make_args(numer(im)), n)
              -> the surviving indices must equal keep_filter(base_idx, keep);
      step 2  (step-1 result) -= _solution_union(denoms(f), n)
              -> the surviving indices must equal
                 drop_filter(keep_filter(base_idx, keep), drop).

    This pins WHERE each collection is applied (keep at the intersection `&=`,
    drop at the difference `-=`) and the ORDER (keep then drop), exactly as the
    gold patch performs them -- not just the aggregate selection."""
    im = imag_part(f)

    # --- gold step 1: base_set &= _solution_union(numer(im) factors) ---------
    keep_solution = _solution_union(Mul.make_args(numer(im)), n)
    after_keep_set = base_set & keep_solution
    gold_after_keep = [k for k in base_idx if k in after_keep_set]
    model_after_keep = keep_filter(base_idx, keep)
    assert model_after_keep == gold_after_keep, (
        "step-1 (&= keep) index list disagrees [%s] f=%s: model keep_filter=%s "
        "gold base_set&keep=%s (keep=%s)"
        % (label, f, model_after_keep, gold_after_keep, keep))

    # --- gold step 2: (after step 1) -= _solution_union(denoms(f) factors) ----
    drop_solution = _solution_union(denoms(f), n)
    after_drop_set = after_keep_set - drop_solution
    gold_after_drop = [k for k in base_idx if k in after_drop_set]
    model_after_drop = drop_filter(keep_filter(base_idx, keep), drop)
    assert model_after_drop == gold_after_drop, (
        "step-2 (-= drop) composition index list disagrees [%s] f=%s: model "
        "drop_filter(keep_filter(.))=%s gold (base_set&keep)-drop=%s "
        "(keep=%s drop=%s)"
        % (label, f, model_after_drop, gold_after_drop, keep, drop))

    # the two-step composition must equal the aggregate per-index selection:
    # drop_filter(keep_filter(.)) and the per-index kept_seq are two descriptions
    # of the same retained subsequence, so they agree index-for-index on every
    # case (a mathematical identity, confirmed here empirically against gold).
    assert model_after_drop == kept_seq(base_idx, keep, drop), (
        "two-step composition != aggregate kept_seq [%s] f=%s: two_step=%s "
        "kept_seq=%s" % (label, f, model_after_drop, kept_seq(base_idx, keep, drop)))


def check_case(f, base_set, base_window, label):
    """Returns 'checked' or 'skipped-out-of-scope'. Asserts the index-level
    biconditional on every window index when in-scope, plus the two-step
    decomposition (keep `&=` then drop `-=`) against the gold step ordering."""
    real_result = imageset(Lambda(n, f), base_set).intersect(S.Reals)

    im = imag_part(f)
    keep, keep_conditional = linear_roots(Mul.make_args(numer(im)), n)

    base_idx = [k for k in base_window if k in base_set]

    if keep_conditional:
        # A non-linear imaginary-part factor -> the real result is a
        # ConditionSet-image, OUTSIDE the modeled (all-linear) regime.
        return "skipped-out-of-scope"

    drop = denominator_zero_indices(f, base_idx)

    # honest index-level biconditional, BOTH directions, no one-sided mask.
    for k in base_idx:
        model_in = survives(k, keep, drop)
        real_in = gold_keeps(f, k, real_result)
        assert model_in == real_in, (
            "deep model disagrees with real intersect(Reals) at the INDEX level "
            "[%s] f=%s n=%d: model_in=%s real_in=%s "
            "(keep=%s drop=%s real_result=%s)"
            % (label, f, k, model_in, real_in, keep, drop, real_result))

    # also pin the kept INDEX list against the gold-kept index list directly.
    model_kept = kept_seq(base_idx, keep, drop)
    gold_kept = [k for k in base_idx if gold_keeps(f, k, real_result)]
    assert model_kept == gold_kept, (
        "kept_seq index list disagrees [%s] f=%s: model=%s gold=%s"
        % (label, f, model_kept, gold_kept))

    # WIDENED-SCOPE check: the two _solution_union call sites individually,
    # validated against the gold's actual `&=`-then-`-=` step ordering.
    check_two_step(f, base_set, base_idx, keep, drop, label)
    return "checked"


def main():
    im = (n - 1)*(n + S.Half)
    # The issue example + the 7 F2P assertions of test_imageset_intersect_real.
    # Each tagged with whether it is in the modeled (all-linear imaginary part)
    # regime; the one out-of-scope F2P case (quadratic imaginary part) is named.
    f2p_cases = [
        ("issue/F2P-1: n + (n-1)(n+1)i",      n + (n - 1)*(n + 1)*I, S.Integers, True),
        ("F2P-2: n + im*i",                   n + im*I, S.Integers, True),
        ("F2P-3: n + im(n+1)i over N0",       n + im*(n + 1)*I, S.Naturals0, True),
        ("F2P-4: n/2 + im.expand()*i (QUAD)", n/2 + im.expand()*I, S.Integers, False),
        ("F2P-5: n/(1/n-1) + im(n+1)i",       n/(1/n - 1) + im*(n + 1)*I, S.Integers, True),
        ("F2P-6: n/(n-6) + ...",              n/(n - 6) + (n - 3)*(n + 1)*I/(2*n + 2), S.Integers, True),
        ("F2P-7: n/(n**2-9) + ... (NONLIN denom)", n/(n**2 - 9) + (n - 3)*(n + 1)*I/(2*n + 2), S.Integers, True),
    ]
    window = list(range(-12, 13))

    checked = []
    skipped = []
    for label, f, base, expect_in_scope in f2p_cases:
        status = check_case(f, base, window, label)
        if status == "checked":
            checked.append(label)
            assert expect_in_scope, (
                "case [%s] was checkable but documented out-of-scope" % label)
        else:
            skipped.append(label)
            # A skipped F2P case MUST be a documented out-of-scope case, never
            # a silent skip of an in-scope discriminator.
            assert not expect_in_scope, (
                "F2P case [%s] was SKIPPED but is documented in-scope -- the "
                "modeled regime fails to cover a discriminating F2P case" % label)

    # Coverage-completeness: exactly the documented out-of-scope F2P case is
    # skipped (the quadratic imaginary-part case); all others are checked.
    assert len(skipped) == 1 and "QUAD" in skipped[0], (
        "unexpected skip set: %s" % skipped)
    assert len(checked) == 6, "expected 6 in-scope F2P cases, got %d" % len(checked)

    # The in-scope subset still fully discriminates the bug: the issue case
    # (F2P-1) alone separates gold (keeps only roots {-1,1}) from the pre-fix
    # collapse (keeps every non-pole index, e.g. index 2). Assert directly.
    f1 = n + (n - 1)*(n + 1)*I
    rr1 = imageset(Lambda(n, f1), S.Integers).intersect(S.Reals)
    base_idx1 = [k for k in window if k in S.Integers]
    keep1, _ = linear_roots(Mul.make_args(numer(imag_part(f1))), n)
    drop1 = denominator_zero_indices(f1, base_idx1)
    gold_kept1 = [k for k in base_idx1 if gold_keeps(f1, k, rr1)]
    prepatch_kept1 = [k for k in base_idx1 if not contains(drop1, k)]  # collapse no-ops keep
    assert gold_kept1 == [-1, 1], "gold F2P-1 index set changed: %s" % gold_kept1
    assert 2 in prepatch_kept1 and 2 not in gold_kept1, (
        "the in-scope discriminator no longer separates prepatch from gold")

    # fuzz: random products of DISTINCT linear factors as the imaginary part
    # (every factor genuinely linear -> fully in the modeled regime, so every
    # case must be checked, never skipped). The index-level biconditional must
    # hold on all of them.
    rng = random.Random(21596)
    nfuzz = 0
    for _ in range(400):
        nfac = rng.randint(1, 3)
        roots = rng.sample(range(-6, 7), nfac)  # distinct -> all-linear factors
        im_expr = Integer(1)
        for r in roots:
            im_expr *= (n - r)
        f = n + im_expr * I
        status = check_case(f, S.Integers, window, "fuzz")
        assert status == "checked", "distinct-linear-factor fuzz unexpectedly skipped"
        nfuzz += 1

    # adversarial regime fuzz: a REPEATED linear root produces a power factor
    # (n-r)**k that is NOT scalar-solvable -> the case is correctly classified
    # OUT-OF-SCOPE (skipped), exactly like the quadratic F2P case. This proves
    # the regime guard fires honestly rather than silently passing such inputs.
    nregime = 0
    for _ in range(120):
        r = rng.randint(-6, 6)
        other = rng.randint(-6, 6)
        f = n + ((n - r) ** 2) * (n - other) * I
        status = check_case(f, S.Integers, window, "regime-fuzz")
        assert status == "skipped-out-of-scope", (
            "a repeated-root (non-linear) imaginary part was NOT flagged "
            "out-of-scope: f=%s" % f)
        nregime += 1

    print("G-AX OK: index-level biconditional survives(k,keep,drop) == "
          "gold_keeps(k) holds on %d in-scope F2P cases + %d distinct-linear-"
          "factor fuzz cases (honest, no value-realness mask); the WIDENED "
          "two-step decomposition is validated against the gold's actual step "
          "ordering -- keep_filter == (base_set &= _solution_union(numer(im))) "
          "at the index level, then drop_filter == (-= _solution_union(denoms"
          "(f))), and their composition == the aggregate kept_seq -- on every "
          "in-scope case; %d repeated-root (non-linear) fuzz cases were "
          "correctly flagged out-of-scope; drop = ALL denominator-zero indices "
          "(covers non-linear denominators, e.g. F2P-7 -> EmptySet); the single "
          "skipped F2P case is the documented out-of-scope quadratic "
          "imaginary-part case (%s); the in-scope subset still discriminates "
          "the bug (index 2 kept by the collapse, excluded by gold)."
          % (len(checked), nfuzz, nregime, skipped[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
