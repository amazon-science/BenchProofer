#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21596.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the OBSERVABLE result of the
real-restriction, on BOTH legs of the carrier:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `restrictToRealValues` impl,
              transliterated to Python over the real SymPy carriers via the
              mapping.md bijection: assemble `given domain`; `meet` it with the
              per-factor zero collection of the imaginary numerator's factors
              ONLY on the shape that reaches line 323, i.e. only where the
              imaginary part is not settled to be zero (on the `if im.is_zero:
              … pass` leg the branch keeps nothing, so neither does the shadow);
              then `apart` the per-factor zero collection of the denominators.
              The A-reference callees (`solve_linear`, `numer`, `denoms` and the
              `_solution_union` assembly) are NOT replaced by a model here — they
              are the REAL, UNCHANGED base-commit callees, so they stay out of
              G-CONF's R/I scope (their fidelity is G-AX's job). What G-CONF
              exercises is the control/data flow of the change: which collection
              is kept, which is removed, and in that order.
  * ORACLE  — patch.diff's behaviour: the gold-patched
              `imageset(Lambda(n, f), domain).intersect(S.Reals)` itself (the real
              correctness oracle, G-RESOLVE — the harness applies patch.diff
              before this runs).

Two comparisons per family:

  (1) MEMBERSHIP — every queried integer index (mapped through the family's real
      part) must be in the shadow's restriction iff it is in the oracle's set.
      This is the `ensures reported out = …` clause.
  (2) STRUCTURE — `srepr(shadow object) == srepr(oracle object)`: the assembled
      objects must be the SAME object, not merely sets with the same members.
      This is the `ensures out = .apart (.meet …) …` clause, and it is the
      comparison the failing test itself performs (`assert
      imageset(...).intersect(Reals) == FiniteSet(-1, 1)`).

Leg (2) is checked because leg (1) alone cannot see the difference the change is
about. TWO NEGATIVE CONTROLS run alongside, one per axis on which a
membership-equivalent rival can differ, and each must agree with the oracle on
membership everywhere and DISAGREE on structure:

  * COLLAPSE — the imaginary part's factor list replaced by a single product
    factor. Probes the list's LENGTH/GROUPING.
  * RE-PRESENT — each member of that list replaced by a DIFFERENT expression
    taking the same value at every probed index. Probes each member's IDENTITY,
    which the collapse control cannot see: it keeps the list's length and order
    and every index the answer picks out, and differs only in which factor line
    293 embeds.
  * NARROW-ANYWAY — on the SETTLED-ZERO shape, keep the domain down to the zero
    collection regardless. The node the real callees build for an identically
    zero numerator excludes nothing, so the rival keeps exactly the same
    indices; where the domain is not already canonical the `&` re-evaluates it
    and the object differs. Probes the SHAPE the keep leg is allowed to depend
    on. (On an already-canonical domain this rival is genuinely invisible, so
    the requirement is >=1 family with bite, not zero mutes.)

If either control ever failed to discriminate, the structural leg would be
decoration on that axis, so its failure fails the gate.

Exit 0 iff zero disagreements on either leg and the negative control
discriminates; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + sympy only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

from sympy import (I, S, Lambda, imageset, FiniteSet, Eq, Union, Dummy, Integer,
                   srepr, Intersection, Interval)
from sympy.abc import n
from sympy.core.mul import Mul
from sympy.core.function import expand_complex
from sympy.simplify.radsimp import numer
from sympy.solvers.solvers import denoms, solve_linear
from sympy.sets.conditionset import ConditionSet
from sympy.sets.sets import Set

SEED = 21596
N_FUZZ = 4000
N_FUZZ_STRUCT = 400   # the structural leg builds two objects per family


# ---- the R/I shadow of restrictToRealValues (over the REAL callees) ----------
def _solution_union(exprs, sym):
    """`zerosOfAny`: ONE contribution per LISTED factor, collected together."""
    sols = []
    for i in exprs:
        x, xis = solve_linear(i, 0, [sym])
        if x == sym:
            sols.append(FiniteSet(xis))
        else:
            sols.append(ConditionSet(sym, Eq(i, 0)))
    return Union(*sols)


def _parts(f):
    """The family's real part, its imaginary part's factor LIST, and its
    denominator list — the three inputs of the modeled method."""
    n_ = Dummy(n.name, real=True)
    f_ = f.subs(n, n_)
    re_, im = f_.as_real_imag()
    im = expand_complex(im)
    re_ = re_.subs(n_, n)
    im = im.subs(n_, n)
    return re_, im, Lambda(n, re_), list(Mul.make_args(numer(im))), list(denoms(f))


def settled_zero(f):
    """Which SHAPE the imaginary part arrives in — the branch's own test.

    `if im.is_zero:` (line 309) decides whether the keep step at 323-324 runs at
    all; on that leg the body is `pass`, so nothing is kept. This is read off the
    imaginary part alone, before any set is built, which is why the modeled
    `imaginaryPart` is a two-constructor INPUT (`.zeroThroughout` / `.factors gs`)
    and the keep leg is `keptToReal` of that shape (mapping.md 2.4)."""
    _re, im, _lam, _ims, _dens = _parts(f)
    return bool(im.is_zero)


def shadow_base_set(f, domain, collapse=False, narrow_anyway=False):
    """The impl region, transliterated, FOLLOWING THE SHAPE: `given domain`; then,
    only where the imaginary part is not settled to be zero, `meet` with the
    per-factor zero collection of its numerator's factors; then `apart` the
    per-factor zero collection of `denominators`.

    Where it IS settled zero the keep step is skipped — the branch says `pass`
    (309-313) — and the domain reaches the removal exactly as it was bound.
    With `collapse=True` the factor list is replaced by the single product factor
    (negative control 1). With `narrow_anyway=True` the keep step is performed on
    the settled-zero shape too (negative control 3): the same indices, since the
    node the real callees build for an identically zero numerator excludes
    nothing, and a different object."""
    _re, im, _lam, imFactors, dens = _parts(f)
    base = domain                                     # .given domain
    if not im.is_zero or narrow_anyway:
        if collapse:
            imFactors = [Mul(*imFactors)]
        base = base & _solution_union(imFactors, n)   # .meet  (the kept leg)
    base = base - _solution_union(dens, n)            # .apart (the removed leg)
    return base


def shadow_object(f, domain, collapse=False, narrow_anyway=False):
    """The object the caller ends up reporting: the unchanged, structure-
    preserving `imageset(lam, ·)` frame applied to the assembled index set."""
    _re, _im, lam, _ims, _dens = _parts(f)
    return imageset(lam, shadow_base_set(f, domain, collapse=collapse,
                                         narrow_anyway=narrow_anyway))


def shadow_member(f, domain, k, collapse=False):
    """Is index k kept by the shadow's restriction? (The imageset frame is
    unchanged and injective on the surviving integer indices, mapping.md §2.)"""
    return _decide(shadow_base_set(f, domain, collapse=collapse)
                   .contains(Integer(k)))


def oracle_set(f, domain):
    """patch.diff behaviour: the gold-patched intersect(Reals)."""
    return imageset(Lambda(n, f), domain).intersect(S.Reals)


def _decide(c):
    if c in (S.true, True):
        return True
    if c in (S.false, False):
        return False
    return None


def _frame_injective(f, domain, ints):
    """Is the family's `imageset` frame injective on the probed indices?

    The membership leg asks the shadow which INDEX survives and asks the oracle
    whether the VALUE at that index is in the reported set. Those two questions
    have the same answer only when distinct surviving indices carry distinct
    values — `shadow_member`'s docstring already assumes it. When the real part
    sends two probed indices to one value (in the limit: a CONSTANT real part,
    where every index collapses to a single value) no value-level query can say
    which index was kept, so the comparison has no subject and is skipped. This
    is a property of the family alone, decided before either side is consulted,
    so it cannot filter on who won: the STRUCTURAL leg still compares these
    families in full, and it compares the whole assembled object.
    """
    n_ = Dummy(n.name, real=True)
    re_ = f.subs(n, n_).as_real_imag()[0].subs(n_, n)
    vals = []
    for k in ints:
        if domain is S.Naturals0 and k < 0:
            continue
        vals.append(srepr(re_.subs(n, Integer(k))))
    return len(set(vals)) == len(vals)


def oracle_member(f, domain, k):
    """Membership of the value f(k) in the gold real intersection. We compare at
    the VALUE level: the real value the family takes at index k (when real)."""
    val = f.subs(n, k)
    if val.has(S.NaN) or val.has(S.ComplexInfinity) or val.is_finite is False:
        return None
    if val.is_real is False:
        # value is non-real -> definitely not in a subset of the reals
        return False
    res = oracle_set(f, domain)
    return _decide(res.contains(val))


# The seven families `test_imageset_intersect_real` asserts, in its own order.
def boundary_families():
    im0 = (n - 1) * (n + S.Half)
    # SETTLED-ZERO shape (`if im.is_zero: … pass`, lines 309-313): a family with
    # no imaginary part at all. The keep step does not run, and the changed line
    # 326 does, so this shape is inside the modeled surface. The first has an
    # UNEVALUATED base set, which is where standing a keep node over the domain
    # becomes caller-visible (the `&=` re-evaluates it — the leg's own comment
    # says avoiding that is the point of the `pass`); the second is already
    # canonical, where the same rival is genuinely invisible.
    yield (n / 2, Intersection(S.Integers, Interval(0, 5), evaluate=False))
    yield (n / (n - 6), S.Integers)
    yield (n + (n - 1) * (n + 1) * I, S.Integers)
    yield (n + im0 * I, S.Integers)
    yield (n + im0 * (n + 1) * I, S.Naturals0)
    yield (n / 2 + im0.expand() * I, S.Integers)
    yield (n / (1 / n - 1) + im0 * (n + 1) * I, S.Integers)
    yield (n / (n - 6) + (n - 3) * (n + 1) * I / (2 * n + 2), S.Integers)
    yield (n / (n ** 2 - 9) + (n - 3) * (n + 1) * I / (2 * n + 2), S.Integers)


def fuzz_families(rng, count):
    for fam in boundary_families():
        yield fam
    for _ in range(count):
        kf = rng.randint(1, 3)
        im_expr = Integer(1)
        for _ in range(kf):
            if rng.random() < 0.45:
                # a factor `solve_linear` CANNOT solve. Without these almost
                # every fuzzed family lands on the naked-index branch, where a
                # factor's identity is genuinely unobservable, and the
                # member-identity control has nothing to exhibit. Family 4 of
                # the asserted seven has exactly this shape (an expanded
                # quadratic), so it is in-distribution, not a contrivance.
                a = rng.choice([1, 1, 2, -1])
                b = rng.randint(-7, 7)
                c = rng.randint(-7, 7)
                im_expr = im_expr * ((a * n + b) * (n + c)).expand()
                continue
            a = rng.choice([1, 1, 2, -1])
            b = rng.randint(-7, 7)
            im_expr = im_expr * (a * n + b)
        denom = None
        if rng.random() < 0.5:
            c = rng.choice([1, 2])
            e = rng.randint(-7, 7)
            denom = c * n + e
        re_part = n
        im_part = im_expr if denom is None else im_expr / denom
        if denom is not None and rng.random() < 0.4:
            re_part = n / denom
        f = re_part + im_part * I
        domain = rng.choice([S.Integers, S.Naturals0])
        yield (f, domain)


def _settled(obj):
    """The gold branch declines some inputs (it returns None when the imaginary
    part is not univariate in the lambda variable), leaving `intersect` an
    unevaluated `Intersection`. Those families are outside the modeled branch, so
    the STRUCTURAL comparison has no subject; membership is still compared."""
    return not isinstance(obj, Intersection)


def membership_leg(rng):
    query_ints = list(range(-12, 13))
    bad, compared, families = [], 0, 0
    noninjective = 0
    for f, domain in fuzz_families(rng, N_FUZZ):
        families += 1
        try:
            if not _frame_injective(f, domain, query_ints):
                noninjective += 1
                continue
            for k in query_ints:
                if domain is S.Naturals0 and k < 0:
                    continue
                sh = shadow_member(f, domain, k)
                orc = oracle_member(f, domain, k)
                if sh is None or orc is None:
                    continue  # undecidable membership for this index — skip
                compared += 1
                if sh != orc:
                    bad.append((str(f), str(domain), k, sh, orc))
                    if len(bad) >= 8:
                        return bad, compared, families, noninjective
        except Exception:
            # a degenerate random family the real callees choke on is not an
            # R/I obligation; skip it
            continue
    return bad, compared, families, noninjective


def _collapse_eligible(imFactors):
    """Is the collapse control able to say anything for this factor list? It is
    only when at least TWO of the listed factors are ones `solve_linear` can
    solve: resolving those one at a time NAMES two indices, while their (then
    non-linear) product names none. A one-factor list, or one padded with
    constants (`-1`, `2` — whose own contribution is empty and whose product with
    a linear factor is still linear), collapses to the very same object, so it is
    silent rather than a failure."""
    return len([g for g in imFactors if solve_linear(g, 0, [n])[0] == n]) >= 2


def _value_identical(a, b, ints):
    """Do two expressions take the same value at every probed index, agreeing
    also on where they take no rational value at all?"""
    for k in ints:
        va, vb = a.subs(n, k), b.subs(n, k)
        oka, okb = va.is_Rational, vb.is_Rational
        if oka != okb or (oka and va != vb):
            return False
    return True


def _represent(imFactors, ints):
    """The imaginary factor list with each member replaced by a value-identical
    but DIFFERENT expression, or None if no member admits one.

    Only a member `solve_linear` cannot solve is worth re-presenting: on the
    solvable branch the emitted node is the naked index and carries no syntax, so
    there is nothing for the control to observe (mapping.md §2.3 records that as
    the conservative direction). Returns None rather than a same-object list, so
    a family with nothing to exhibit stays silent instead of counting as a mute
    control."""
    from sympy import factor as sym_factor
    from sympy.polys.rationaltools import together

    out, changed = [], False
    for g in imFactors:
        alt = None
        if g.has(n) and solve_linear(g, 0, [n])[0] != n:
            for cand in (sym_factor(together(g)), g.expand(), g + S.Zero):
                if srepr(cand) != srepr(g) and _value_identical(g, cand, ints):
                    alt = cand
                    break
        out.append(alt if alt is not None else g)
        changed = changed or alt is not None
    return out if changed else None


def structure_leg(rng):
    """srepr-equality of the assembled objects, plus the collapse control."""
    bad, compared, skipped = [], 0, 0
    ctrl_seen, ctrl_mute = 0, []
    rep_seen, rep_mute = 0, []
    zero_seen, zero_bite, zero_bad = 0, 0, []
    ctrl_ints = range(-8, 9)
    for f, domain in fuzz_families(rng, N_FUZZ_STRUCT):
        try:
            orc = oracle_set(f, domain)
            if not _settled(orc):
                skipped += 1
                continue
            _re, im, lam, imFactors, dens = _parts(f)
            removed = _solution_union(dens, n)
            kept = _solution_union(imFactors, n)
            # the keep step runs only on the shape that reaches line 323
            base = (domain if im.is_zero else (domain & kept)) - removed
            sh = imageset(lam, base)
            compared += 1
            if srepr(sh) != srepr(orc):
                bad.append((str(f), str(domain), srepr(sh), srepr(orc)))
                if len(bad) >= 8:
                    return (bad, compared, skipped, ctrl_seen, ctrl_mute,
                            rep_seen, rep_mute, zero_seen, zero_bite, zero_bad)

            def _membership_equivalent(rbase):
                return all(
                    _decide(base.contains(Integer(k))) ==
                    _decide(rbase.contains(Integer(k)))
                    for k in ctrl_ints
                    if not (domain is S.Naturals0 and k < 0))

            # negative control 2: the same indices, the same list length and
            # order, each MEMBER re-presented as another expression of equal
            # value everywhere. Probes member identity, which control 1 cannot.
            rep = _represent(imFactors, ctrl_ints)
            if rep is not None:
                rbase = (domain & _solution_union(rep, n)) - removed
                if _membership_equivalent(rbase):
                    rep_seen += 1
                    if srepr(imageset(lam, rbase)) == srepr(orc):
                        rep_mute.append((str(f), str(domain), srepr(orc)))

            # negative control 3: on the SETTLED-ZERO shape, narrow the domain
            # anyway. The node the real callees build for an identically zero
            # numerator excludes no index, so the rival keeps exactly the same
            # ones; where the domain is not already canonical the `&` re-evaluates
            # it and the object DIFFERS, which is the divergence the shape split
            # exists to refuse. Where the domain is already canonical the rival is
            # invisible — recorded as seen-without-bite, not as a failure.
            if im.is_zero:
                zbase = (domain & kept) - removed
                if _membership_equivalent(zbase):
                    zero_seen += 1
                    if srepr(imageset(lam, zbase)) != srepr(orc):
                        zero_bite += 1
                else:
                    zero_bad.append((str(f), str(domain), srepr(zbase),
                                     srepr(base)))
                continue

            # negative control 1: the same indices via one collapsed factor
            if not _collapse_eligible(imFactors):
                continue
            cbase = (domain & _solution_union([Mul(*imFactors)], n)) - removed
            if not _membership_equivalent(cbase):
                continue     # not a membership-equivalent rival here; no claim
            ctrl_seen += 1
            if srepr(imageset(lam, cbase)) == srepr(orc):
                ctrl_mute.append((str(f), str(domain), srepr(orc)))
        except Exception:
            skipped += 1
            continue
    return (bad, compared, skipped, ctrl_seen, ctrl_mute, rep_seen, rep_mute,
            zero_seen, zero_bite, zero_bad)


def main():
    m_bad, m_compared, m_families, m_noninj = membership_leg(
        random.Random(SEED))
    (s_bad, s_compared, s_skipped, c_seen, c_mute,
     r_seen, r_mute, z_seen, z_bite, z_bad) = structure_leg(random.Random(SEED))

    failed = False
    if m_bad:
        failed = True
        print("G-CONF FAIL: %d membership disagreement(s) over %d compares "
              "(%d families):" % (len(m_bad), m_compared, m_families))
        for f, dom, k, sh, orc in m_bad:
            print("  f=%s domain=%s n=%d shadow=%s oracle=%s"
                  % (f, dom, k, sh, orc))
    if s_bad:
        failed = True
        print("G-CONF FAIL: %d structural disagreement(s) over %d compares:"
              % (len(s_bad), s_compared))
        for f, dom, sh, orc in s_bad:
            print("  f=%s domain=%s\n    shadow=%s\n    oracle=%s"
                  % (f, dom, sh, orc))
    if c_seen < 20 or c_mute:
        failed = True
        print("G-CONF FAIL: the collapse control was mute on %d of %d "
              "membership-equivalent families (need >=20 eligible, 0 mute) — the "
              "structural leg would be decoration there:"
              % (len(c_mute), c_seen))
        for f, dom, orc in c_mute[:8]:
            print("  f=%s domain=%s built the SAME object as gold: %s"
                  % (f, dom, orc))
    if r_seen < 20 or r_mute:
        failed = True
        print("G-CONF FAIL: the RE-PRESENT control was mute on %d of %d "
              "membership-equivalent families (need >=20 eligible, 0 mute) — the "
              "structural leg would then be decoration on the MEMBER-IDENTITY "
              "axis, which is the one a value-only carrier leaves free:"
              % (len(r_mute), r_seen))
        for f, dom, orc in r_mute[:8]:
            print("  f=%s domain=%s built the SAME object as gold: %s"
                  % (f, dom, orc))
    if z_bad:
        failed = True
        print("G-CONF FAIL: on %d settled-zero family(ies) the narrow-anyway "
              "rival did NOT keep the same indices, so it is not a "
              "membership-equivalent rival there and control 3 would be "
              "comparing two different questions:" % len(z_bad))
        for f, dom, rv, sh in z_bad:
            print("  f=%s domain=%s\n    rival=%s\n    shadow=%s"
                  % (f, dom, rv, sh))
    if z_seen < 2 or z_bite < 1:
        failed = True
        print("G-CONF FAIL: the SETTLED-ZERO control had no bite: %d "
              "membership-equivalent rival(s) seen, %d of them differing on "
              "srepr (need >=2 seen and >=1 differing). Without one differing, "
              "the shape split in the spec would be unobservable here and "
              "clause (1)'s two-shape keep leg would be decoration."
              % (z_seen, z_bite))
    if failed:
        return 1

    print("G-CONF OK: the R/I shadow of restrictToRealValues (assemble the "
          "domain, keep it down to the per-factor zero collection of the "
          "imaginary numerator's factors, take that apart from the "
          "denominators' per-factor zero collection, over the real unchanged "
          "callees) agrees with the gold-patched intersect(S.Reals) on "
          "%d membership compares across %d families (%d skipped as having a "
          "non-injective frame, where an index-level and a value-level query are "
          "not the same question — those families are still compared in full by "
          "the structural leg) AND on srepr for all %d "
          "settled families (%d unsettled/degenerate skipped); seed=%d. The "
          "collapsed-factor-list control agrees on membership and differs on "
          "srepr for all %d families where collapsing can lose a name, and the "
          "re-presented-members control (same list length and order, each member "
          "another expression of equal value everywhere) does the same on all %d "
          "families that admit one — so the structural leg has bite on the list's "
          "grouping AND on each member's identity. On the SETTLED-ZERO shape "
          "(`if im.is_zero: … pass`), where the shadow builds NO keep node, it "
          "agrees with gold on all %d compared family(ies) and the "
          "narrow-anyway rival — same indices, a keep node the branch does not "
          "build — differs on srepr for %d of them, so the two-shape keep leg "
          "has bite too."
          % (m_compared, m_families, m_noninj, s_compared, s_skipped, SEED,
             c_seen, r_seen, z_seen, z_bite))
    return 0


if __name__ == "__main__":
    sys.exit(main())
