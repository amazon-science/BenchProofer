#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21596.

The bundle consumes NO axiom's `ensures`: the changed set-algebra restriction is
modeled DEEPLY in Solution.lean's `pure` region by `vanishingSet` / `anyVanishes`
(which indices a factor list picks out) and by `IndexReport` / `reported` (HOW an
index set is assembled, and how to read that assembly back as indices). What G-AX
establishes are the **A-reference** facts that make those deep models faithful to
the real, UNCHANGED repo callees they denote (mapping.md §3, refinement.md §B):

  1. ZERO-SET FIDELITY (imaginary part). For a factored integer-valued
     expression, the symbolic set the UNCHANGED callees build —
     `_solution_union(Mul.make_args(numer(im)), n)` via `solve_linear`/`numer`/
     `FiniteSet`/`ConditionSet`/`Union` — denotes exactly the indices at which
     the imaginary part vanishes:  k ∈ that set  ⇔  im.subs(n,k) == 0  (for every
     integer k where im is defined). This is `anyVanishes gs` for the factor list
     `ImaginaryPart.factors gs` carries, built out of
     the per-factor `vanishingSet`.

  2. ZERO-SET FIDELITY (denominators). The set `_solution_union(denoms(f), n)`
     denotes exactly the indices at which some denominator of f vanishes:
     k ∈ that set ⇔ ∃ d ∈ denoms(f), d.subs(n,k) == 0. This is
     `anyVanishes denominators`.

  3. MEMBERSHIP OF AN ASSEMBLY. The set operations realize `∩` / `\\` on
     membership: k ∈ (B & Z) ⇔ k ∈ B ∧ k ∈ Z, and k ∈ (B - S) ⇔ k ∈ B ∧ k ∉ S —
     so `reported (.apart (.meet (.given B) Z) S)` denotes what the branch's
     `&=` / `-=` produce.

  4. THE ASSEMBLY IS OBSERVABLE, i.e. `IndexReport` records a real distinction.
     `_solution_union` loops over the factors it is GIVEN (one node per element),
     and `solve_linear` NAMES an index only for a factor it can solve. So the
     object built from a factor list is NOT a function of the index set that list
     picks out: for a multi-factor imaginary part, the list of its factors and the
     one-element list holding their product have the SAME membership at every
     integer and are DIFFERENT objects by `srepr` (a `Union` of `FiniteSet`s that
     names the indices, versus one `ConditionSet` that does not). This is the fact
     that makes `zerosOfAny [g₁, g₂] ≠ zerosOfAny [g₁ * g₂]` a faithful model
     rather than an artificial distinction — and it is why an index-set-only
     post-image is too weak here.

  5. THE TWO ROLES ARE NOT INTERCHANGEABLE. Keeping the imaginary part's zeros
     and removing the denominators' zeros is a different object from the swap, so
     `meet`/`apart` taking their operands from specific lists is a real
     constraint.

  6. THE ASSEMBLY IS DETERMINISTIC. Rebuilding the same assembly yields
     `srepr`-identical objects, so pinning one assembly in the spec pins the
     callees' behaviour and not an accident of a particular run.

  7. EACH LISTED FACTOR'S IDENTITY IS OBSERVABLE, i.e. `Factor` being a handle
     with `valueOf` a separate reading records a real distinction. Fact 4 pins the
     list's LENGTH and GROUPING; it says nothing about a member. But
     `_solution_union` does not depend only on the indices a member picks out: for
     a factor `solve_linear` cannot solve it emits `ConditionSet(sym, Eq(i, 0))`,
     embedding the factor ITSELF. So two expressions that take the same value at
     EVERY index and are different objects by `srepr` build DIFFERENT objects from
     the same one-element list — with identical membership at every integer.
     Checked on BOTH legs, since the one helper resolves both. This is the fact
     that makes a factor's identity, and not the function giving its values, the
     faithful carrier: were a factor modeled by its values, an implementation
     handing a leg a value-preserving re-presentation of each member would be
     indistinguishable from the desired one in the model while answering a
     different object in the repo.

  8. A KEEP NODE IS OBSERVABLE EVEN WHERE IT EXCLUDES NOTHING, which is what
     makes the two-shape keep leg (`keptToReal .zeroThroughout = given`, with no
     node over the atom) a faithful model rather than a stylistic choice. Where
     the imaginary part is settled to be zero the branch performs NO keep step
     (`if im.is_zero: … pass`, lines 309-313); a counterpart that keeps anyway
     would hand the callees `Mul.make_args(numer(0))`, whose node is
     `S.UniversalSet` — it excludes no index. Checked here: that node really does
     contain every probed index, `B` and `B & UniversalSet` really do have the
     same membership at every probed index, and they are nonetheless DIFFERENT
     objects by `srepr` when `B` is not already canonical (an unevaluated
     `Intersection`, which is exactly what the leg's own comment is protecting —
     "allow re-evaluation of self in this case to make the result canonical").
     So `IndexReport` distinguishing `given` from `meet given (zerosOfAny gs)` on
     the settled-zero shape records a real distinction in the callees. (On an
     already-canonical `B` the two coincide; that direction is recorded, not
     asserted.)

These are the equivalences and distinctions the refinement's R/A-reference legs
rely on. They hold of the BASE-COMMIT callees (the change only re-arranges how
they are combined), so no gold patch is needed here; G-CONF separately checks the
assembled behaviour against the gold-patched function, on membership and on
`srepr`. stdlib + sympy (the repo under test) only. Exit 0 iff every obligation
holds.
"""
import random
import sys

from sympy import (I, S, Eq, Union, FiniteSet, Dummy, Integer, srepr,
                   Intersection, Interval)
from sympy.abc import n
from sympy.core.mul import Mul
from sympy.core.function import expand_complex
from sympy.simplify.radsimp import numer
from sympy.solvers.solvers import denoms, solve_linear
from sympy.sets.conditionset import ConditionSet
from sympy.sets.sets import Set


# --- the UNCHANGED callees, assembled exactly as the branch does --------------
def solution_union(exprs, sym):
    """`zerosOfAny`: the union, over each LISTED factor, of its zero set —
    FiniteSet(sol) if the factor is linearly solvable in `sym`, else
    ConditionSet(sym, Eq(i,0)). (The helper the branch uses; built from the
    unchanged solve_linear.)"""
    sols = []
    for i in exprs:
        x, xis = solve_linear(i, 0, [sym])
        if x == sym:
            sols.append(FiniteSet(xis))
        else:
            sols.append(ConditionSet(sym, Eq(i, 0)))
    return Union(*sols)


def real_im(f, sym):
    """The imaginary part of f as a function of a REAL index, as the branch
    computes it (real Dummy, expand_complex)."""
    n_ = Dummy(sym.name, real=True)
    f_ = f.subs(sym, n_)
    re_, im = f_.as_real_imag()
    im = expand_complex(im)
    return re_.subs(n_, sym), im.subs(n_, sym)


def in_set(S_, k):
    """Decide membership of integer k in symbolic set S_, robust to unevaluated
    Contains (returns None on genuinely-undecidable, handled by caller)."""
    c = S_.contains(Integer(k))
    if c in (S.true, True):
        return True
    if c in (S.false, False):
        return False
    return None  # undecidable (should not happen for our linear factors)


def check_imaginary_zero_set(f, ints):
    """Fact 1: anyVanishes fidelity for the imaginary part's factor list."""
    re_, im = real_im(f, n)
    Z = solution_union(Mul.make_args(numer(im)), n)
    assert isinstance(Z, Set), f"zero set not a Set for {f}"
    checked = 0
    for k in ints:
        val = im.subs(n, k)
        # skip indices where im is undefined (denominator zero -> nan/zoo);
        # those are governed by the denominator leg, not the imaginary leg.
        if val.is_finite is False or val.has(S.NaN) or val.has(S.ComplexInfinity):
            continue
        mem = in_set(Z, k)
        if mem is None:
            continue
        assert mem == (val == 0), (
            f"imaginary zero-set INFIDELITY for {f} at n={k}: "
            f"k in Z={mem} but im.subs={val} (== 0 is {val == 0})")
        checked += 1
    return checked


def check_denominator_zero_set(f, ints):
    """Fact 2: anyVanishes fidelity for the denominator list."""
    ds = [d for d in denoms(f) if d.has(n)]
    D = solution_union(ds, n) if ds else S.EmptySet
    assert isinstance(D, Set), f"denominator zero set not a Set for {f}"
    checked = 0
    for k in ints:
        any_zero = any((d.subs(n, k) == 0) for d in ds)
        mem = in_set(D, k)
        if mem is None:
            continue
        assert mem == any_zero, (
            f"denominator zero-set INFIDELITY for {f} at n={k}: "
            f"k in D={mem} but exists-denominator-zero={any_zero}")
        checked += 1
    return checked


def check_membership_ops(f, domain, ints):
    """Fact 3: & / - realize membership intersection / difference, so `reported`
    of the assembly keeps exactly the real, defined indices."""
    re_, im = real_im(f, n)
    Z = solution_union(Mul.make_args(numer(im)), n)
    ds = [d for d in denoms(f) if d.has(n)]
    D = solution_union(ds, n) if ds else S.EmptySet
    base = domain & Z
    base = base - D
    checked = 0
    for k in ints:
        in_dom = in_set(domain, k)
        in_z = in_set(Z, k)
        in_d = in_set(D, k) if ds else False
        mem = in_set(base, k)
        if None in (in_dom, in_z, mem) or in_d is None:
            continue
        expected = in_dom and in_z and (not in_d)
        assert mem == expected, (
            f"membership-op INFIDELITY for {f} at n={k}: base says {mem}, "
            f"expected (dom={in_dom} & zero={in_z} & notdenomzero={not in_d})="
            f"{expected}")
        checked += 1
    return checked


def check_per_factor_structure(f, ints):
    """Fact 4: the object `_solution_union` builds is a function of the FACTOR
    LIST, not of the index set that list picks out. Returns 1 if this family
    exhibited the distinction, 0 if it has nothing to exhibit (a single factor).
    Raises if a multi-factor family FAILS to exhibit it — that would mean the
    per-factor structure in `IndexReport` models nothing real."""
    re_, im = real_im(f, n)
    factors = list(Mul.make_args(numer(im)))
    # The demonstration needs a list whose collapse actually loses names: at
    # least TWO factors that `solve_linear` can solve, so that resolving them one
    # at a time names two indices while their (then non-linear) product names
    # none. A list of one factor, or one padded with constants (`-1`, `2`: their
    # `ConditionSet(n, Eq(c, 0))` is empty and their product with a linear factor
    # is still linear), has nothing to exhibit — not a failure, just silent.
    solvable = [g for g in factors if solve_linear(g, 0, [n])[0] == n]
    if len(solvable) < 2:
        return 0
    per_factor = solution_union(factors, n)                 # zerosOfAny [g1, g2, …]
    collapsed = solution_union([Mul(*factors)], n)          # zerosOfAny [g1*g2*…]
    same = 0
    for k in ints:
        a, b = in_set(per_factor, k), in_set(collapsed, k)
        if a is None or b is None:
            continue
        assert a == b, (
            f"per-factor vs collapsed MEMBERSHIP differs for {f} at n={k} "
            f"({a} vs {b}) — the two are supposed to pick out the same indices, "
            f"so the distinction Fact 4 records would not be purely structural")
        same += 1
    assert srepr(per_factor) != srepr(collapsed), (
        f"per-factor and collapsed assemblies are the SAME object for {f}: "
        f"{srepr(per_factor)} — the factor list would then be unobservable and "
        f"`zerosOfAny` would not need to carry it")
    # and the discriminating detail: resolving factor by factor NAMES indices
    assert per_factor.has(FiniteSet) or isinstance(per_factor, FiniteSet), (
        f"per-factor assembly names no index for {f}: {srepr(per_factor)}")
    assert same > 0, f"no decidable membership compare for {f}"
    return 1


def value_identical(a, b, ints):
    """Whether two expressions take the same value at every probed index —
    including agreeing on WHERE they take no rational value at all."""
    for k in ints:
        va, vb = a.subs(n, k), b.subs(n, k)
        oka = va.is_Rational
        okb = vb.is_Rational
        if oka != okb:
            return False
        if oka and va != vb:
            return False
    return True


def check_member_identity(f, ints):
    """Fact 7: the object `_solution_union` builds depends on each listed
    factor's own IDENTITY, not only on the values that factor takes.

    For every factor of BOTH legs that `solve_linear` cannot solve (the branch
    that embeds the factor), find a re-presentation of it — a DIFFERENT
    expression taking the same value at every probed index — and assert the two
    one-element lists have the same membership everywhere and build different
    objects. Returns the number of demonstrations; 0 if this family has no
    unsolvable factor to exhibit one with (not a failure, just silent).

    Raises if a re-presentation IS value-identical, IS a different object, and
    yet builds the SAME node — that would mean member identity is unobservable
    and `Factor` would be modeling nothing real.
    """
    from sympy import factor as sym_factor
    from sympy.polys.rationaltools import together

    re_, im = real_im(f, n)
    members = list(Mul.make_args(numer(im))) + [d for d in denoms(f) if d.has(n)]
    shown = 0
    for g in members:
        if not g.has(n):
            continue
        if solve_linear(g, 0, [n])[0] == n:
            # the FiniteSet branch: the emitted node is the naked index and
            # carries no syntax, so there is nothing for identity to be
            # observable IN. Recorded in mapping.md §2.3 as the conservative
            # direction, not checked here.
            continue
        for alt in (sym_factor(together(g)), g.expand(), g + S.Zero):
            if srepr(alt) == srepr(g):
                continue
            if not value_identical(g, alt, ints):
                continue
            node_g = solution_union([g], n)
            node_alt = solution_union([alt], n)
            for k in ints:
                a, b = in_set(node_g, k), in_set(node_alt, k)
                if a is None or b is None:
                    continue
                assert a == b, (
                    f"a value-identical re-presentation of {g} as {alt} picks out "
                    f"DIFFERENT indices at n={k} ({a} vs {b}) — then Fact 7's "
                    f"distinction would not be purely a matter of identity")
            assert srepr(node_g) != srepr(node_alt), (
                f"the value-identical, srepr-different factors {g} and {alt} "
                f"build the SAME object {srepr(node_g)} — a listed factor's "
                f"identity would then be unobservable and `Factor` would not "
                f"need to be a handle")
            shown += 1
            break
    return shown


def check_role_asymmetry(f, domain, ints):
    """Fact 5: keep-the-imaginary-zeros / remove-the-denominator-zeros is a
    different object from the swap. Returns 1 if exhibited, 0 if the family has
    no n-dependent denominator (nothing to swap)."""
    re_, im = real_im(f, n)
    Z = solution_union(Mul.make_args(numer(im)), n)
    ds = [d for d in denoms(f) if d.has(n)]
    if not ds:
        return 0
    D = solution_union(ds, n)
    straight = (domain & Z) - D
    swapped = (domain & D) - Z
    assert srepr(straight) != srepr(swapped), (
        f"swapping the two roles builds the SAME object for {f}: "
        f"{srepr(straight)} — the spec's naming of which list fills which role "
        f"would then be unobservable")
    return 1


def check_determinism(f, domain, reps=3):
    """Fact 6: the assembly is deterministic (srepr-stable across rebuilds), so
    pinning one assembly pins the callees rather than a run accident."""
    reprs = set()
    for _ in range(reps):
        re_, im = real_im(f, n)
        Z = solution_union(Mul.make_args(numer(im)), n)
        ds = [d for d in denoms(f) if d.has(n)]
        D = solution_union(ds, n) if ds else S.EmptySet
        reprs.add(srepr((domain & Z) - D))
    assert len(reprs) == 1, (
        f"assembly NOT deterministic for {f}: {len(reprs)} distinct srepr")
    return 1


def check_settled_zero_node(f, domain, ints):
    """Fact 8: on the settled-zero shape the keep node excludes nothing and is
    still observable. Returns 1 if this (family, domain) exhibits the srepr
    difference, 0 if the domain is already canonical and the node is invisible."""
    re_, im = real_im(f, n)
    assert im.is_zero, f"{f} is not a settled-zero family (im={im})"
    Z0 = solution_union(Mul.make_args(numer(im)), n)
    assert Z0 == S.UniversalSet, (
        f"the node built for an identically zero numerator is {srepr(Z0)}, not "
        f"UniversalSet — Fact 8's premise (a keep node that excludes nothing) "
        f"does not hold, so the settled-zero rival is not membership-equivalent")
    for k in ints:
        assert in_set(Z0, k) is True, (
            f"the settled-zero keep node does not contain index {k}")
    ds = [d for d in denoms(f) if d.has(n)]
    D = solution_union(ds, n) if ds else S.EmptySet
    plain = domain - D                      # the branch: no keep node at all
    narrowed = (domain & Z0) - D            # the rival: keep anyway
    for k in ints:
        a, b = in_set(plain, k), in_set(narrowed, k)
        if a is None or b is None:
            continue
        assert a == b, (
            f"the settled-zero rival differs on membership at {k} for {f} over "
            f"{domain}: {a} vs {b} — then it is not the membership-equivalent "
            f"rival Fact 8 is about")
    return 1 if srepr(plain) != srepr(narrowed) else 0


def main():
    ints = list(range(-12, 13))

    # boundary families from the issue / F2P test (and structurally similar ones)
    families = [
        n + (n - 1) * (n + 1) * I,                       # issue example -> {-1,1}
        n + (n - 1) * (n + S.Half) * I,                  # -> {1}
        n + (n - 1) * (n + S.Half) * (n + 1) * I,        # -> {1}
        n / (1 / n - 1) + (n - 1) * (n + S.Half) * (n + 1) * I,
        n / (n - 6) + (n - 3) * (n + 1) * I / (2 * n + 2),
        n / (n ** 2 - 9) + (n - 3) * (n + 1) * I / (2 * n + 2),
    ]

    tot_im = tot_den = tot_ops = 0
    tot_struct = tot_roles = tot_det = tot_ident = 0
    # Fact 8 — the settled-zero shape (`im.is_zero`), where the branch keeps
    # nothing. The first domain is UNEVALUATED (where a keep node is visible),
    # the second already canonical (where it is not).
    tot_zero_seen = tot_zero_bite = 0
    for zf, zdom in ((n / 2, Intersection(S.Integers, Interval(0, 5),
                                          evaluate=False)),
                     (n / (n - 6), S.Integers),
                     (n / 2, S.Integers)):
        tot_zero_seen += 1
        tot_zero_bite += check_settled_zero_node(zf, zdom, ints)
    for f in families:
        tot_im += check_imaginary_zero_set(f, ints)
        tot_den += check_denominator_zero_set(f, ints)
        tot_ops += check_membership_ops(f, S.Integers, ints)
        tot_struct += check_per_factor_structure(f, ints)
        tot_roles += check_role_asymmetry(f, S.Integers, ints)
        tot_det += check_determinism(f, S.Integers)
        tot_ident += check_member_identity(f, ints)

    # --- randomized fuzz over products of integer-linear/affine factors -------
    rng = random.Random(21596)
    n_fuzz_im = n_fuzz_den = n_fuzz_struct = n_fuzz_ident = 0
    for _ in range(3000):
        # build an imaginary part as a product of up to 3 linear factors a*n+b
        kf = rng.randint(1, 3)
        im_expr = Integer(1)
        for _ in range(kf):
            a = rng.choice([1, 1, 1, 2, -1])
            b = rng.randint(-6, 6)
            im_expr = im_expr * (a * n + b)
        # optionally divide by a linear denominator (n-dependent)
        denom = None
        if rng.random() < 0.5:
            c = rng.choice([1, 2])
            e = rng.randint(-6, 6)
            denom = c * n + e
        f = n + (im_expr if denom is None else im_expr / denom) * I
        if denom is not None:
            # also give the family a real-part denominator sometimes
            f = (n if rng.random() < 0.5 else n / (denom)) + \
                (im_expr / denom) * I
        try:
            n_fuzz_im += check_imaginary_zero_set(f, ints)
            n_fuzz_den += check_denominator_zero_set(f, ints)
            check_membership_ops(f, S.Integers, ints)
            n_fuzz_struct += check_per_factor_structure(f, ints)
            n_fuzz_ident += check_member_identity(f, ints)
        except AssertionError:
            raise
        except Exception:
            # malformed random family (e.g. fully-cancelling) — skip, not an
            # obligation
            continue

    assert tot_im > 30 and tot_ops > 30, (
        "too few imaginary/membership checks exercised (%d / %d)"
        % (tot_im, tot_ops))
    assert n_fuzz_im > 500, (
        "fuzz exercised too few imaginary zero-set checks (%d)" % n_fuzz_im)
    assert tot_struct >= 4 and n_fuzz_struct > 200, (
        "too few per-factor structure demonstrations (%d boundary, %d fuzz) — "
        "Fact 4 must be exhibited widely, since it is what justifies the "
        "assembly post-image" % (tot_struct, n_fuzz_struct))
    assert tot_roles >= 3, (
        "too few role-asymmetry demonstrations (%d)" % tot_roles)
    assert tot_zero_seen >= 3 and tot_zero_bite >= 1, (
        "Fact 8 (a keep node is observable even where it excludes nothing) was "
        "never exhibited: %d settled-zero family/domain pairs checked, %d "
        "exhibiting the srepr difference — without one, the spec's two-shape "
        "keep leg would be unobservable in the callees"
        % (tot_zero_seen, tot_zero_bite))
    assert tot_ident >= 1, (
        "Fact 7 (a listed factor's identity is observable) was never exhibited "
        "on the boundary families (%d) — it is what justifies `Factor` being a "
        "handle rather than a value function, so a silent zero here would leave "
        "the member-identity leg of the post-image unvalidated" % tot_ident)

    print("G-AX OK: zero sets built from the UNCHANGED callees (solve_linear/"
          "numer/denoms/FiniteSet/ConditionSet/Union) denote exactly the "
          "imaginary-part vanishing indices (%d boundary +%d fuzz) and the "
          "denominator vanishing indices (%d boundary +%d fuzz); & / - realize "
          "membership intersection/difference (%d boundary checks). The ASSEMBLY "
          "is observable: a multi-factor list and the one-element list of its "
          "product pick out the same indices and build different objects "
          "(%d boundary +%d fuzz demonstrations), swapping the keep/remove roles "
          "builds a different object (%d families), and the assembly is "
          "srepr-deterministic (%d families). Each LISTED FACTOR's identity is "
          "observable too: on both legs, a value-identical but srepr-different "
          "re-presentation of an unsolvable member picks out the same indices "
          "everywhere and builds a different object (%d boundary +%d fuzz "
          "demonstrations). And a keep node is observable even where it excludes "
          "nothing: on %d settled-zero family/domain pairs the node built for an "
          "identically zero numerator is UniversalSet and keeps every probed "
          "index, yet `B` and `B & UniversalSet` are different objects by srepr "
          "on %d of them — so the two-shape keep leg records a real distinction. "
          "A-reference deep models (Factor/valueOf/vanishingSet/"
          "anyVanishes/IndexReport/reported) sound; no consumed axiom."
          % (tot_im, n_fuzz_im, tot_den, n_fuzz_den, tot_ops, tot_struct,
             n_fuzz_struct, tot_roles, tot_det, tot_ident, n_fuzz_ident,
             tot_zero_seen, tot_zero_bite))
    return 0


if __name__ == "__main__":
    sys.exit(main())
