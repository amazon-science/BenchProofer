#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-19495.

Validates the A-reference callees and the deep model in Solution.lean against the
REAL repository code. Runs against the UNPATCHED (pre-patch) source — the gate
mounts the bundle read-only and does NOT apply the gold patch — which is exactly
right here, because every A-reference callee is UNCHANGED by the gold patch:

  (A-reference) `substCond` / `substSet` == `Basic.subs`   (sympy/core/basic.py)
  (A-reference) `mkSet` / `mkSetOnValue` == the two invocation shapes of the
                `ConditionSet` constructor `self.func`
                (sympy/sets/conditionset.py:117)

The deep model `evalSubsSpec boundSym cond base old new`
  == `cs.func(cs.sym, cs.condition.subs(old,new), cs.base_set.subs(old,new))`
is built entirely from these unchanged callees. There is NO consumed axiom; the
operation under change (`ConditionSet._eval_subs`) is NEVER axiomatized.

BOTH callees are PARTIAL: on arguments outside their domain they raise instead of
returning a value. Modelling a partial callee as a total function of unsorted
handles would make an ADDITIONAL, RESULT-DISCARDED invocation of it
unobservable — the weakest-precondition calculus cannot see a discarded
application of a total function — so the model does three things instead.

  * It SORTS the argument slots. The constructor's three slots are `Binder`,
    `Cond`, `SetObj`; the substitution callee's two argument slots are `Old` and
    `New`; the set the operation BUILDS is `BuiltSet`, a sort distinct from the
    component sort `SetObj` it substitutes into. One axiom per real INVOCATION
    SHAPE completes it (`mkSet` binder-keyed, `mkSetOnValue` value-keyed).
    Together these keep the set of invocations the model can NAME down to
    invocations the real callees accept, so an invocation they would refuse is a
    Lean type error — unwritable, not merely unproven, and unwritable even when
    its result is discarded.
  * It carries the substitution callee's non-sortal partiality (a replacement the
    component cannot be compared against) as the two PRECONDITIONS
    `CondSubDefined` / `BaseSubDefined`, because on those inputs the real
    operation has no result either: it propagates the error instead of returning
    a set, so a total-semantics contract must not promise one.
  * It carries the CONSTRUCTOR's non-sortal partiality the same way, as the third
    precondition `BuildsDefined`. Sorting the three slots is NOT the whole domain:
    `ConditionSet.__new__` tests the condition against the elements of a finite
    base (`sifted = sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))`,
    conditionset.py:151-152), so an element the condition cannot be compared
    against makes it raise with every slot holding exactly the kind of object it
    asks for — e.g. `ConditionSet(x, x > 0, FiniteSet(I))`. On this instance that
    is reachable with BOTH component substitutions defined and `old != sym`
    (obligation 16's exhibit), so without this precondition the contract would
    promise a result where the real operation raises. `BuildsDefined` ranges over
    every set-building invocation the model can NAME at the operation's arguments,
    not only the one the contract returns, which is what licenses treating the two
    building axioms as total functions of their sorts (obligations 17-18).

Obligations 6-18 are what make all of that an executable claim about the real
callees rather than a stipulation: 7/8/15 measure that every invocation the model
CAN express is accepted, 9/10/11/16 exhibit, for each excluded shape and for each
non-sortal domain fact, a real invocation that IS refused, and 12/13/14/17/18
measure that the three preconditions are non-vacuous, sufficient, complete for the
invocations the model can name, and closed under the re-application the model can
still express.

The check asserts:

  1. (purity)  the unchanged callees are deterministic pure functions: the model
     composition recomputed twice is structurally equal.

  2. (unchanged-path fidelity)  on every input where the substituted condition
     does NOT collapse to `S.true`, the real PRE-PATCH `_eval_subs` already
     returns the model `cs.func(cs.sym, subs(cond), subs(base))` — pre- and
     post-patch agree on this path, so the model faithfully transliterates the
     unchanged composition. (Runnable on pre-patch source.)

  3. (collapse-path bug characterization)  on every input with `old != sym` on
     which the substituted condition collapses to `S.true`, the real PRE-PATCH
     `_eval_subs` returns exactly the substituted-value rebuild
     `cs.func(new, Contains(new, base.subs(old,new)), base.subs(old,new))` — i.e.
     it binds with `new`, the conflation the gold patch removes. This pins the
     exact bug the spec's `mkSet boundSym ...` (vs the prepatch twin's
     `mkSetOnValue new ...`) discriminates against.

  4. (load-bearing witness)  among the collapse inputs there exist DISCRIMINATING
     ones on which the original-binder rebuild (the model) is NOT `dummy_eq` to
     the substituted-value rebuild — so the binder choice the spec pins is
     genuinely observable and the spec is not vacuous. (We require >= 2; the
     issue's ImageSet example and the Interval(-oo,0) case are two such.)

  5. (excluded-arm identity)  on the legacy compound (Tuple) binder form the real
     `_eval_subs` returns `self` untouched (an UNCHANGED early return,
     `conditionset.py:209-212`, identical pre- and post-patch), so leaving that
     form out of the model's domain is sound.

  6. (sort fidelity of the substitution callee)  `Basic.subs` maps a condition to
     a condition and a set to a set, in BOTH substitution directions — so
     `substCond : Cond -> Old -> New -> Cond` and
     `substSet : SetObj -> Old -> New -> SetObj` are the right RESULT sorts, and a
     substituted component is always still legal in the slot it came from. (The
     measurement runs both directions even though the `Old`/`New` sorts let the
     model name only one, so the result sorts do not depend on that restriction.)

  7. (`mkSet` is TOTAL on its sorts, INSIDE `BuildsDefined`)  over the whole
     argument grid — a Symbol binder, every condition, every base set — the real
     constructor accepts every binder-keyed invocation: 0 refusals. The claim is
     explicitly NOT that the sorts alone are the domain: 7b exhibits a
     well-sorted triple the constructor REFUSES (a relational condition over a
     base holding an element it cannot be compared against), which is what forces
     the third precondition rather than leaving it decorative. Inside that
     precondition no writable `mkSet` application — including one whose result is
     discarded — denotes an invocation the real constructor would refuse.

  8. (`mkSetOnValue` is TOTAL on its sorts, INSIDE `BuildsDefined`)  an arbitrary
     object bound over the membership test of that same object in the SAME set is
     accepted over the whole grid; 8b exhibits the non-sortal refusal for this
     shape too — the membership test can ABSORB the object it tests (it gets
     solved against the set's own description), and the constructor then refuses
     because the condition no longer mentions the object it must bind — so the
     same precondition is what licenses this axiom's totality as well.

  9. (the partiality is REAL, on this instance's own witness)  on the F2P input
     from the problem statement, the three shapes the sorts exclude are each
     REFUSED by the real constructor: an object the condition does not bind in
     the binder slot (this is exactly the extra discarded call a total-function
     model would hide), a set in the condition slot, and a condition in the base
     slot.

 10. (the domain restrictions are FORCED, not stylistic)  there exists an
     Expr-but-not-Symbol binder pairing the constructor refuses (so `Binder`
     cannot be widened to every symbolic expression), and there exists a
     membership binding over a base set DIFFERENT from the set tested that the
     constructor refuses (so `mkSetOnValue` must take one shared set, not two).

 11. (the SUBSTITUTION callee is PARTIAL too, in two distinct ways)  `Basic.subs`
     is not a total function of (component, old, new): handed a replacement the
     component cannot be compared against it raises, and applied to a
     membership-style set AT THAT SET'S OWN BINDER with a mismatched replacement
     it raises as well. Both refusals are exhibited on real objects. The first is
     what `CondSubDefined` / `BaseSubDefined` exclude; the second is what the
     `Old` sort and the `SetObj`/`BuiltSet` split make unnameable (a receiver the
     model can name is the stored base set or a substituted form of it, and the
     object it substitutes is never the set's own binder).

 12. (the preconditions are NON-VACUOUS and cover this instance's own case)  on
     the F2P input from the problem statement both component substitutions return
     normally AND every set-building invocation the model can name is accepted,
     and over the fuzz pool the share of inputs on which that holds is measured
     and reported — so the modeled domain is not a corner of the input space and
     in particular contains the case the tests exercise.

 13. (the preconditions are SUFFICIENT for the modeled branch to be TOTAL)  over
     the whole pool, whenever the binder is a plain Symbol, `old != sym`, both
     component substitutions return normally AND `BuildsDefined` holds, the real
     `_eval_subs` returns normally: 0 refusals. This is what licenses a
     total-correctness contract on the modeled branch. The two substitution
     preconditions alone do NOT suffice — the same loop counts the inputs they
     admit on which the real operation still raises (a condition constraining the
     BINDER ALONE, so that substituting into it is trivially defined, over a base
     whose substituted form holds an element that condition cannot be compared
     against), and every one of them is an input `BuildsDefined` excludes.

 14. (the modeled domain is CLOSED under re-application)  whenever a component
     substitution is defined, applying the SAME substitution again to its result
     is defined too (and is measured to be idempotent). This is the only extra
     substitution invocation the sorts still let an impl name — a discarded double
     substitution — so its acceptance has to be measured rather than assumed.

 15. (every extra invocation the model can still NAME is accepted)  the complete
     list of well-sorted invocation shapes an impl can write beyond the operation's
     own three is enumerated (double condition substitution, double base
     substitution, the raw-component rebuild, and the value-keyed rebuild on each
     of the three objects the model can name, over both the raw and the
     substituted base) and every one of them is accepted by the real callees on
     every boundary case and on every pool input the three preconditions admit. So
     inside the modeled domain no writable discarded call denotes a refusal.

 16. (the CONSTRUCTOR's non-sortal partiality is REAL, and the third precondition
     is FORCED)  there is a fully well-sorted input — a Symbol binder, a genuine
     condition, a genuine base set, `old != sym`, and both component substitutions
     defined — on which the constructor REFUSES the operation's own rebuild and the
     real `_eval_subs` propagates that refusal instead of returning a set
     (`ConditionSet(x, x > 0, FiniteSet(z))` with `z -> I`: the condition survives
     the substitution untouched, the base becomes `FiniteSet(I)`, and the rebuild
     raises `TypeError('Invalid comparison of non-real I')` inside `__new__`'s own
     sift). Measured on the PRE-PATCH source, so it is a property of the unchanged
     callee and not of the patch delta. Over the pool, EVERY input whose own
     rebuild the constructor refuses is one where the real operation raises too, so
     the precondition is not stricter than the operation's own domain at that
     clause.

 17. (`BuildsDefined` is NON-VACUOUS)  it holds on this instance's F2P witness and
     on the second example the problem statement displays, and its density over the
     pool (among inputs the two substitution preconditions already admit) is
     measured and reported.

 18. (`BuildsDefined`'s coverage is COMPLETE for what an impl can write, and the
     price is measured)  the nameable set-building invocations are enumerated at
     every component the sorts allow — the stored condition and base, their
     substituted forms, and their twice-substituted forms — over both shapes and
     all three nameable objects; re-application is measured IDEMPOTENT on every
     admitted pool input, so deeper nesting denotes objects already covered. The
     inputs this precondition excludes only because a writable EXTRA shape is
     refused (the operation itself returning normally there) are counted and
     reported: that is the sliver of the operation's domain the model gives up in
     exchange for building axioms that are total on their sorts, and giving it up
     is conservative — the contract is silent there rather than wrong.

Imports only `sympy` (the package the patch lives in). Exit 0 iff every
obligation holds.
"""
import random
import sys

from sympy import (Symbol, S, Interval, Contains, Lambda, asin, sin, cos, pi,
                   imageset, Rational, oo, Eq, Mod, Abs, FiniteSet, Tuple,
                   Function, I, zoo, nan)
from sympy.core.expr import Expr
from sympy.logic.boolalg import as_Boolean
from sympy.sets import ConditionSet
from sympy.sets.sets import Set


def model(cs, old, new):
    """Deep model evalSubsSpec, built from the UNCHANGED callees: rebuild with
    the ORIGINAL bound symbol and the substitution pushed through cond/base."""
    sym, cond, base = cs.args
    return cs.func(sym, cond.subs(old, new), base.subs(old, new))


def wrong_rebuild(cs, old, new):
    """The pre-patch collapse-path rebuild: bind with the SUBSTITUTED value `new`
    instead of the original symbol (the conflation the gold patch removes)."""
    sym, cond, base = cs.args
    base2 = base.subs(old, new)
    return cs.func(new, Contains(new, base2), base2)


def cond_collapses(cs, old, new):
    sym, cond, base = cs.args
    return cond.subs(old, new) is S.true


def build_cases():
    x = Symbol('x'); y = Symbol('y'); z = Symbol('z'); w = Symbol('w')
    n = Symbol('n'); k = Symbol('k')
    neg = Symbol('n', negative=True); pos = Symbol('p', positive=True)
    cases = []
    # --- collapse witnesses (the discriminating path) ---
    # ImageSet base, Contains(y,[-1,1]) -> True at y=1/3  (the issue's example)
    img = imageset(Lambda(k, 2 * k * pi + asin(y)), S.Integers)
    cases.append(("imageset/collapse",
                  ConditionSet(x, Contains(y, Interval(-1, 1)), img), y, Rational(1, 3)))
    # Interval base, n<x with n negative, x->p positive => n<p True
    cases.append(("interval/collapse",
                  ConditionSet(neg, neg < x, Interval(-oo, 0)), x, pos))
    cases.append(("interval/collapse2",
                  ConditionSet(neg, neg < x, Interval(0, oo)), x, pos))
    # FiniteSet base, condition true after subs
    cases.append(("finiteset/collapse",
                  ConditionSet(n, Contains(y, Interval(0, 5)), FiniteSet(z, w)),
                  y, Rational(1, 2)))
    # --- non-collapse cases (cond stays symbolic) ---
    cases.append(("noncollapse/imageset",
                  ConditionSet(x, x < y, img), y, w))
    cases.append(("noncollapse/finiteset",
                  ConditionSet(x, x < y, FiniteSet(z, w)), y, z))
    cases.append(("noncollapse/eq",
                  ConditionSet(x, Eq(sin(x), 0), Interval(0, 2 * pi)), y, z))
    cases.append(("noncollapse/mod",
                  ConditionSet(n, Eq(Mod(n, 2), 0), S.Integers), y, w))
    return cases


# ---------------------------------------------------------------------------
# The sort pools: the argument grids obligations 6-10 quantify over.
# ---------------------------------------------------------------------------
_x = Symbol('x'); _y = Symbol('y'); _z = Symbol('z'); _w = Symbol('w')
_k = Symbol('k'); _n = Symbol('n'); _r = Symbol('r')
_neg = Symbol('nn', negative=True); _pos = Symbol('pp', positive=True)
_f = Function('f')
_IMG = imageset(Lambda(_k, 2 * _k * pi + asin(_y)), S.Integers)
_IMG2 = imageset(Lambda(_k, 2 * _k * pi + asin(Rational(1, 3))), S.Integers)

# `Binder`: a plain single symbol.
BINDERS = [_x, _z, _w, _k, _n, _neg, _pos]
# Expr-but-not-Symbol candidates for the binder slot: EXCLUDED by the sort.
NON_SYMBOL_BINDERS = [_f(_x), _x + 1, sin(_x), Abs(_x), cos(_x) ** 2]
# `Obj`: plain objects — a binder once it has left the binder slot, a
# substitution target, or a replacement.
OBJS = [Rational(1, 3), S.Zero, S.One, _y, _z, _x, Rational(-2, 5)]
# `SetObj`.
SETS = [Interval(-oo, 0), Interval(0, oo), Interval(-1, 1), S.Integers, S.Reals,
        FiniteSet(_z, _w), FiniteSet(_z), _IMG, _IMG2, S.Naturals, S.EmptySet,
        S.UniversalSet]
# Finite bases holding an element a relational condition cannot be compared
# against. Every slot is still the right KIND of object, so these are the
# witnesses that the constructor's domain is not exhausted by the sorts
# (obligations 7b / 8b / 16). They are not in `SETS`: they are what the third
# precondition excludes, not part of the modeled domain.
NON_COMPARABLE_SETS = [FiniteSet(I), FiniteSet(2 * I), FiniteSet(nan),
                       FiniteSet(zoo), FiniteSet(I, 1), FiniteSet(_z, nan)]


def conds(sym, fv):
    """`Cond`: filtering conditions over a binder `sym` and a free value `fv`.

    The last group constrains the BINDER ALONE — it does not mention `fv` at all —
    so substituting `fv` into it is trivially defined and the input reaches the
    constructor's own test of the condition against the base's elements. That is
    the family in which the constructor's non-sortal partiality is observable
    (obligations 13, 16), so the pool has to contain it.
    """
    return [sym < fv, Contains(fv, Interval(-1, 1)), Contains(fv, Interval(0, 5)),
            Eq(Mod(sym, 2), 0) & Contains(fv, Interval(-1, 1)), Eq(sym, fv),
            (sym < fv) | Contains(fv, Interval(0, oo)), S.true, S.false,
            Contains(sym, FiniteSet(_z, _w)),
            sym > 0, sym < 0, sym >= 1, Eq(sym, 0),
            Contains(sym, Interval(0, oo)),
            (sym > 0) & Contains(fv, Interval(-1, 1))]


def nameable_builds(cs, old, new):
    """Every set-building invocation the model can NAME at these arguments, as
    (label, thunk) pairs. This is what the precondition `BuildsDefined` ranges
    over, and it is complete because:

      * the only binder the model can name is the set's own (`Binder` is inhabited
        by nothing else here), and the only objects it can name are that binder,
        the replaced object and the replacement (`binderObj` / `oldObj` /
        `newObj`);
      * the only components it can name are the stored condition / base set and
        their images under the ONE substitution the `Old` / `New` sorts admit,
        applied any number of times — enumerated here to depth 2, with obligation
        14 measuring that a further application changes nothing;
      * the only two invocation shapes are the binder-keyed and the value-keyed
        one (`mkSet` / `mkSetOnValue`), and the value-keyed shape takes ONE set,
        used both as the set tested and the set bound over.
    """
    sym, c0, s0 = cs.args
    c1, s1 = c0.subs(old, new), s0.subs(old, new)
    c2, s2 = c1.subs(old, new), s1.subs(old, new)
    conds_terms = [("raw", c0), ("substituted", c1), ("twice-substituted", c2)]
    sets_terms = [("raw", s0), ("substituted", s1), ("twice-substituted", s2)]
    out = []
    for cn, cc in conds_terms:
        for sn, ss in sets_terms:
            out.append(("binder-keyed(%s cond, %s base)" % (cn, sn),
                        lambda cc=cc, ss=ss: cs.func(sym, cc, ss)))
    for on, ob in (("binder", sym), ("replaced object", old),
                   ("replacement", new)):
        for sn, ss in sets_terms:
            out.append(("value-keyed(%s over %s base)" % (on, sn),
                        lambda ob=ob, ss=ss: ConditionSet(ob, Contains(ob, ss), ss)))
    return out


# the invocation the contract itself returns: `mkSet boundSym (substCond …) (substSet …)`
OWN_REBUILD = "binder-keyed(substituted cond, substituted base)"


def builds_refused(cs, old, new):
    """The labels of the nameable set-building invocations the REAL constructor
    refuses at these arguments. `BuildsDefined` holds iff this is empty."""
    return [label for label, thunk in nameable_builds(cs, old, new)
            if refuses(thunk) is not None]


def refuses(thunk):
    """Return the exception the real constructor raises, or None if accepted."""
    try:
        thunk()
        return None
    except Exception as exc:                                    # noqa: BLE001
        return exc


def main():
    random.seed(19495)
    cases = build_cases()

    def dummy_same(a, b):
        try:
            return a.dummy_eq(b)
        except AttributeError:
            return a == b

    n_purity = 0
    n_noncollapse = 0
    n_collapse = 0
    n_witness = 0

    for name, cs, old, new in cases:
        sym = cs.args[0]
        assert old != sym, "test case %r violates old != sym" % name

        # (1) purity of the unchanged callees: recompute the model, must match.
        m1 = model(cs, old, new)
        m2 = model(cs, old, new)
        assert m1 == m2, "model non-deterministic on %r: %r vs %r" % (name, m1, m2)
        n_purity += 1

        if cond_collapses(cs, old, new):
            # (3) collapse-path bug characterization: real PRE-PATCH _eval_subs
            # is exactly the substituted-value rebuild (binds with `new`).
            wr = wrong_rebuild(cs, old, new)
            real = cs._eval_subs(old, new)
            assert dummy_same(real, wr), (
                "collapse case %r: real pre-patch _eval_subs %r is not the "
                "substituted-value rebuild %r — bug characterization wrong"
                % (name, real, wr))
            # (4) discriminating witness: model (original binder) != wrong rebuild.
            if not dummy_same(m1, wr):
                n_witness += 1
            n_collapse += 1
        else:
            # (2) unchanged-path fidelity: pre-patch _eval_subs already == model.
            real = cs._eval_subs(old, new)
            assert real == m1, (
                "real pre-patch _eval_subs diverges from the model on non-collapse "
                "case %r: real=%r model=%r" % (name, real, m1))
            n_noncollapse += 1

    assert n_witness >= 2, (
        "need >= 2 discriminating collapse witnesses (binder choice observable); "
        "found %d" % n_witness)

    # randomized fuzz: random ConditionSets over a symbol pool, random subs.
    syms = [Symbol(c) for c in "abcdijkmstuv"]
    free = [Symbol('y'), Symbol('z'), Symbol('w'), Symbol('q')]
    repls = [Rational(1, 3), Rational(-2, 5), S.One, S.Zero, Symbol('r'),
             Symbol('rp', positive=True), Symbol('rn', negative=True)]
    bases = [Interval(-oo, 0), Interval(0, oo), Interval(-1, 1), S.Integers,
             S.Reals, FiniteSet(Symbol('z'), Symbol('w'))]
    n_fuzz = 0
    n_fuzz_collapse = 0
    for _ in range(4000):
        sym = random.choice(syms)
        fv = random.choice(free)
        base = random.choice(bases)
        which = random.randint(0, 2)
        if which == 0:
            cond = sym < fv
        elif which == 1:
            cond = Contains(fv, Interval(-1, 1))
        else:
            cond = Eq(Mod(sym, 2), 0) & Contains(fv, Interval(0, 5))
        try:
            cs = ConditionSet(sym, cond, base)
        except Exception:
            continue
        if not isinstance(cs, ConditionSet):
            continue  # constructor already simplified it away
        old = fv
        new = random.choice(repls)
        if old == cs.args[0]:
            continue
        m1 = model(cs, old, new)
        m2 = model(cs, old, new)
        assert m1 == m2, "fuzz: model non-deterministic"
        if cond_collapses(cs, old, new):
            # real pre-patch == substituted-value rebuild (the bug); model is a
            # well-formed set (the post-patch answer).
            wr = wrong_rebuild(cs, old, new)
            real = cs._eval_subs(old, new)
            assert dummy_same(real, wr), (
                "fuzz collapse: real pre-patch _eval_subs %r != substituted-value "
                "rebuild %r" % (real, wr))
            assert m1 is not None
            n_fuzz_collapse += 1
        else:
            real = cs._eval_subs(old, new)
            assert real == m1, (
                "fuzz: pre-patch _eval_subs != model on non-collapse: real=%r model=%r"
                % (real, m1))
        n_fuzz += 1

    # (5) excluded-arm identity: the legacy compound (Tuple) binder form =>
    # _eval_subs returns self untouched. This arm is UNCHANGED by the gold patch;
    # the model's `Binder` sort leaves it outside the spec's domain.
    x = Symbol('x'); y = Symbol('y'); z = Symbol('z'); w = Symbol('w')
    tuple_cases = [
        (ConditionSet(Tuple(x, y), Contains(y, Interval(-1, 1)), S.Reals), y, S.Zero),
        (ConditionSet(Tuple(x, y), Eq(x, z), S.Complexes), z, w),
        (ConditionSet(Tuple(x, y), Contains(y, Interval(0, 5)), S.Integers),
         y, Rational(1, 2)),
    ]
    n_excluded = 0
    for cs, old, new in tuple_cases:
        assert not isinstance(cs.sym, Expr), (
            "excluded-arm case has an Expr binder: %r" % (cs.sym,))
        real = cs._eval_subs(old, new)
        assert real is cs, (
            "non-Expr-binder arm must return self untouched; got %r for %r"
            % (real, cs))
        n_excluded += 1
    assert n_excluded >= 3

    # ---------------------------------------------------------------------
    # (6) sort fidelity of the substitution callee, in BOTH directions.
    # ---------------------------------------------------------------------
    n_sort_cond = 0
    n_sort_set = 0
    for b in BINDERS:
        for fv in (y, z, Rational(1, 3)):
            for c in conds(b, fv):
                for old, new in ((fv, Rational(1, 3)), (Rational(1, 3), fv),
                                 (fv, z), (z, fv)):
                    c2 = c.subs(old, new)
                    # a substituted condition is still legal in the condition slot
                    as_Boolean(c2)
                    n_sort_cond += 1
    for s in SETS:
        for old, new in ((y, Rational(1, 3)), (Rational(1, 3), y), (z, w), (w, z),
                         (y, z), (z, y)):
            s2 = s.subs(old, new)
            assert isinstance(s2, Set), (
                "substSet sort violated: %r.subs(%r, %r) = %r is not a Set"
                % (s, old, new, s2))
            n_sort_set += 1

    # ---------------------------------------------------------------------
    # (7) `mkSet : Binder -> Cond -> SetObj -> BuiltSet` is TOTAL on its sorts
    #     over the modeled domain (7a) — and NOT total on the sorts alone (7b),
    #     which is what forces the third precondition.
    # ---------------------------------------------------------------------
    n_mkset = 0
    for b in BINDERS:
        for fv in (y, z, Rational(1, 3)):
            for c in conds(b, fv):
                for s in SETS:
                    exc = refuses(lambda b=b, c=c, s=s: ConditionSet(b, c, s))
                    assert exc is None, (
                        "mkSet must be total on (Binder, Cond, SetObj) inside the "
                        "modeled domain but ConditionSet(%r, %r, %r) raised %s: %s"
                        % (b, c, s, type(exc).__name__, exc))
                    n_mkset += 1
    assert n_mkset >= 2000, n_mkset

    # (7b) the sorts alone are NOT the constructor's domain: a Symbol binder, a
    #      genuine Boolean condition and a genuine Set base that it still REFUSES,
    #      because it tests the condition against the base's elements.
    n_nonsortal_refused = 0
    nonsortal_witness = None
    for b in BINDERS:
        for c in (b > 0, b < 0, b >= 1, Eq(Mod(b, 2), 0)):
            for s in NON_COMPARABLE_SETS:
                exc = refuses(lambda b=b, c=c, s=s: ConditionSet(b, c, s))
                if exc is not None:
                    n_nonsortal_refused += 1
                    if nonsortal_witness is None:
                        nonsortal_witness = (b, c, s, exc)
    assert n_nonsortal_refused >= 1, (
        "no well-sorted (Symbol binder, Boolean condition, Set base) triple was "
        "refused, so the third precondition BuildsDefined would be a restriction "
        "the real constructor does not justify")

    # ---------------------------------------------------------------------
    # (8) `mkSetOnValue : Obj -> SetObj -> BuiltSet` is TOTAL on its sorts over
    #     the modeled domain: the object is bound over a membership test of that
    #     SAME object in the SAME set it is bound over. (8b) the same non-sortal
    #     refusal exists for this shape too.
    # ---------------------------------------------------------------------
    n_onvalue = 0
    for o in OBJS:
        for s in SETS:
            exc = refuses(lambda o=o, s=s: ConditionSet(o, Contains(o, s), s))
            assert exc is None, (
                "mkSetOnValue must be total on (Obj, SetObj) inside the modeled "
                "domain but ConditionSet(%r, Contains(%r, %r), %r) raised %s: %s"
                % (o, o, s, s, type(exc).__name__, exc))
            n_onvalue += 1
    assert n_onvalue >= 60, n_onvalue

    # (8b) the value-keyed shape is not total on its sorts either, and again the
    #      refusal is not sortal: the membership test `Contains(v, s)` can ABSORB
    #      the object it is testing (the test gets solved against the set's own
    #      description), and the constructor then refuses because the condition no
    #      longer mentions the object it is asked to bind. The nameable shape that
    #      reaches it is "the replacement bound over the SUBSTITUTED base", so the
    #      grid is exactly that: pool bases with a non-comparable replacement
    #      pushed into them.
    n_onvalue_refused = 0
    onvalue_witness = None
    for o in (I, 2 * I, zoo, nan):
        for base in SETS:
            for old in (_z, _w, _y):
                try:
                    s = base.subs(old, o)
                except Exception:                                # noqa: BLE001
                    continue
                exc = refuses(lambda o=o, s=s: ConditionSet(o, Contains(o, s), s))
                if exc is not None:
                    n_onvalue_refused += 1
                    if onvalue_witness is None:
                        onvalue_witness = (o, s, exc)
    assert n_onvalue_refused >= 1, (
        "no value-keyed invocation was refused for a non-comparable replacement "
        "over a substituted base, so the third precondition would not be forced "
        "for `mkSetOnValue`")

    # ---------------------------------------------------------------------
    # (9) the partiality is REAL on this instance's own F2P witness.
    # ---------------------------------------------------------------------
    k = Symbol('k')
    img = imageset(Lambda(k, 2 * k * pi + asin(y)), S.Integers)
    f2p = ConditionSet(x, Contains(y, Interval(-1, 1)), img)
    old_f2p, new_f2p = y, Rational(1, 3)
    assert isinstance(f2p, ConditionSet)
    sym, cond, base = f2p.args
    arms = []
    # (9a) an object the condition does not bind, in the binder slot. This is
    # EXACTLY the extra invocation an attack impl can make and discard when the
    # constructor is modelled as a total function of unsorted handles.
    arms.append(("object-not-bound-by-condition in the binder slot",
                 refuses(lambda: f2p.func(new_f2p, cond, base))))
    # (9b) a set in the condition slot.
    arms.append(("set in the condition slot",
                 refuses(lambda: f2p.func(sym, base, base))))
    # (9c) a condition in the base slot.
    arms.append(("condition in the base slot",
                 refuses(lambda: f2p.func(sym, cond, cond))))
    for label, exc in arms:
        assert exc is not None, (
            "the constructor was expected to REFUSE %s on the F2P witness, but it "
            "returned a set — the sorted model would then be stricter than the "
            "real callee" % label)
    # the model's own image on this witness IS accepted (the gold invocation).
    assert refuses(lambda: f2p.func(sym, cond.subs(old_f2p, new_f2p),
                                    base.subs(old_f2p, new_f2p))) is None

    # ---------------------------------------------------------------------
    # (10) the two domain restrictions are FORCED by the real callee.
    # ---------------------------------------------------------------------
    n_nonsym_refused = 0
    nonsym_witness = None
    for b in NON_SYMBOL_BINDERS:
        for fv in (y, z, Rational(1, 3)):
            for c in conds(b, fv):
                for s in SETS:
                    exc = refuses(lambda b=b, c=c, s=s: ConditionSet(b, c, s))
                    if exc is not None:
                        n_nonsym_refused += 1
                        if nonsym_witness is None:
                            nonsym_witness = (b, c, s, exc)
    assert n_nonsym_refused >= 1, (
        "no Expr-but-not-Symbol binder pairing was refused, so the Binder=Symbol "
        "restriction would not be forced by the real callee")

    n_cross_refused = 0
    cross_witness = None
    for o in OBJS:
        for s in SETS:
            for s2 in SETS:
                if s is s2:
                    continue
                exc = refuses(
                    lambda o=o, s=s, s2=s2: ConditionSet(o, Contains(o, s), s2))
                if exc is not None:
                    n_cross_refused += 1
                    if cross_witness is None:
                        cross_witness = (o, s, s2, exc)
    assert n_cross_refused >= 1, (
        "no cross-base membership binding was refused, so mkSetOnValue's single "
        "shared set argument would not be forced by the real callee")

    # ---------------------------------------------------------------------
    # (11) the SUBSTITUTION callee is PARTIAL too, in two distinct ways: a
    #      replacement the component cannot be compared against, and a
    #      membership-style set substituted at its own binder. The first is what
    #      the two preconditions exclude; the second is what the `Old` sort and
    #      the `SetObj`/`BuiltSet` split make unnameable.
    # ---------------------------------------------------------------------
    _own_binder_set = ConditionSet(_neg, _neg < _x, Interval(0, oo))
    sub_refusals = []
    for label, thunk in (
        ("incomparable replacement in a relational condition",
         lambda: (y > 0).subs(y, I)),
        ("unbounded replacement in a relational condition",
         lambda: (y > 0).subs(y, zoo)),
        ("undefined replacement in a relational condition",
         lambda: (y > 0).subs(y, nan)),
        ("membership-style set substituted AT ITS OWN BINDER, mismatched "
         "assumptions on the replacement",
         lambda: _own_binder_set.func(_own_binder_set.sym,
                                      _own_binder_set.condition,
                                      _own_binder_set.base_set).subs(
                                          _own_binder_set.sym, _pos)),
    ):
        exc = refuses(thunk)
        if exc is not None:
            sub_refusals.append((label, exc))
    assert len(sub_refusals) >= 2, (
        "the substitution callee was expected to REFUSE at least two shapes "
        "(otherwise the two definedness preconditions and the Old sort would be "
        "restrictions the real callee does not justify); refused %d"
        % len(sub_refusals))
    # and the shape the sorts make unnameable is among them: substituting a
    # membership-style set at its own binder.
    assert any("own binder" in lbl.lower() for lbl, _ in sub_refusals), (
        "the own-binder substitution refusal is the one the sorts exclude; it "
        "must be exhibited on real objects")

    # ---------------------------------------------------------------------
    # (12) the preconditions are NON-VACUOUS: they hold on this instance's own
    #      F2P input, and their density over the pool is measured.
    # (13) they are SUFFICIENT: on the modeled branch, both substitutions
    #      returning normally implies the real operation returns normally.
    # (14) the domain is CLOSED under re-application of the same substitution.
    # ---------------------------------------------------------------------
    assert refuses(lambda: cond.subs(old_f2p, new_f2p)) is None, (
        "CondSubDefined must hold on the F2P witness")
    assert refuses(lambda: base.subs(old_f2p, new_f2p)) is None, (
        "BaseSubDefined must hold on the F2P witness")
    assert refuses(lambda: f2p._eval_subs(old_f2p, new_f2p)) is None, (
        "the real operation must return normally on the F2P witness")

    assert not builds_refused(f2p, old_f2p, new_f2p), (
        "BuildsDefined must hold on the F2P witness, but the constructor refuses "
        "%r there" % builds_refused(f2p, old_f2p, new_f2p))
    # the second example the problem statement displays.
    _ps2 = ConditionSet(x, x > 0, Interval(-oo, oo))
    if isinstance(_ps2, ConditionSet):
        assert not builds_refused(_ps2, y, Rational(1, 3)), (
            "BuildsDefined must hold on the problem statement's second example")

    # A grid that deliberately MIXES in replacements the callee cannot handle, so
    # the definedness filter is doing work rather than passing everything.
    risky = [I, zoo, nan, 2 * I]
    repl_pool = list(OBJS) + risky
    n_dom = 0                 # ALL THREE preconditions hold
    n_dom_excluded = 0        # a component substitution refused
    n_excluded_real_refuses = 0
    n_build_excluded = 0      # substitutions fine, but a nameable build refused
    n_build_excluded_own = 0  # ... including the operation's OWN rebuild
    n_build_excluded_own_raises = 0   # ... and the real operation raises there
    n_build_excluded_extra = 0        # ... only a writable EXTRA shape refused
    n_build_excluded_extra_op_ok = 0  # ... where the operation returns normally
    n_builds_checked = 0      # nameable builds measured on admitted inputs
    build_witness = None
    n_suff = 0               # preconditions hold AND the real operation is total
    n_closed = 0             # re-application defined
    n_idem = 0               # ... and idempotent
    random.seed(19495)
    for _ in range(4000):
        b = random.choice(BINDERS)
        fv = random.choice([y, z, _r])
        c = random.choice(conds(b, fv))
        s = random.choice(SETS)
        o = fv
        nw = random.choice(repl_pool)
        if o == b:
            continue
        try:
            cs = ConditionSet(b, c, s)
        except Exception:                                        # noqa: BLE001
            continue
        if not isinstance(cs, ConditionSet) or not isinstance(cs.sym, Symbol):
            continue
        if o == cs.sym:
            continue
        c0, s0 = cs.condition, cs.base_set
        e_c = refuses(lambda c0=c0, o=o, nw=nw: c0.subs(o, nw))
        e_s = refuses(lambda s0=s0, o=o, nw=nw: s0.subs(o, nw))
        if e_c is not None or e_s is not None:
            n_dom_excluded += 1
            if refuses(lambda cs=cs, o=o, nw=nw: cs._eval_subs(o, nw)) is not None:
                n_excluded_real_refuses += 1
            continue
        # (16) the third precondition: every set-building invocation the model can
        #      NAME here is one the real constructor accepts. Where it fails the
        #      input is outside the modeled domain — but the failure must be
        #      justified by the real callee, so it is classified and counted.
        bad = builds_refused(cs, o, nw)
        if bad:
            n_build_excluded += 1
            op_raises = refuses(
                lambda cs=cs, o=o, nw=nw: cs._eval_subs(o, nw)) is not None
            if OWN_REBUILD in bad:
                n_build_excluded_own += 1
                if op_raises:
                    n_build_excluded_own_raises += 1
                if build_witness is None:
                    build_witness = (cs, o, nw,
                                     [OWN_REBUILD]
                                     + [b for b in bad if b != OWN_REBUILD][:1])
            else:
                n_build_excluded_extra += 1
                if not op_raises:
                    n_build_excluded_extra_op_ok += 1
            continue
        n_dom += 1
        n_builds_checked += len(nameable_builds(cs, o, nw))
        # (13) sufficiency of the THREE preconditions on the modeled branch.
        exc = refuses(lambda cs=cs, o=o, nw=nw: cs._eval_subs(o, nw))
        assert exc is None, (
            "the three preconditions hold for (%r, %r, %r) yet the real "
            "_eval_subs raised %s: %s — they would then be insufficient for a "
            "total-correctness contract"
            % (cs, o, nw, type(exc).__name__, exc))
        n_suff += 1
        # (14) closure under re-application of the SAME substitution.
        c1, s1 = c0.subs(o, nw), s0.subs(o, nw)
        e_c2 = refuses(lambda c1=c1, o=o, nw=nw: c1.subs(o, nw))
        e_s2 = refuses(lambda s1=s1, o=o, nw=nw: s1.subs(o, nw))
        assert e_c2 is None and e_s2 is None, (
            "the modeled domain is not closed under re-application: a second "
            "application of (%r -> %r) to %r / %r raised %r / %r — a discarded "
            "double substitution is writable, so it must be accepted"
            % (o, nw, c1, s1, e_c2, e_s2))
        n_closed += 1
        if c1.subs(o, nw) == c1 and s1.subs(o, nw) == s1:
            n_idem += 1
    assert n_dom >= 500, n_dom
    assert n_dom_excluded >= 1, (
        "no pool input was excluded by the definedness preconditions, so their "
        "density measurement would attest nothing")
    assert n_excluded_real_refuses == n_dom_excluded, (
        "on %d of %d inputs outside the preconditions the real operation still "
        "returned normally, so the preconditions would be STRICTER than the real "
        "operation's domain"
        % (n_dom_excluded - n_excluded_real_refuses, n_dom_excluded))
    # (16) the third precondition does real work, and its main clause — the
    #      operation's OWN rebuild — is exactly as strict as the operation itself.
    assert n_build_excluded_own >= 1, (
        "the two substitution preconditions admitted every pool input, so the "
        "third one's necessity would rest on the single exhibit alone; the pool "
        "must contain binder-only conditions over finite bases")
    assert n_build_excluded_own_raises == n_build_excluded_own, (
        "on %d of %d inputs where the constructor refuses the operation's own "
        "rebuild the real _eval_subs still returned normally, so that clause of "
        "BuildsDefined would be stricter than the operation's own domain"
        % (n_build_excluded_own - n_build_excluded_own_raises,
           n_build_excluded_own))
    assert n_builds_checked >= 5000, n_builds_checked

    # ---------------------------------------------------------------------
    # (16) THE EXHIBIT: a fully well-sorted input, inside both substitution
    #      preconditions, on which the CONSTRUCTOR itself refuses and the real
    #      operation propagates that refusal. Measured on the PRE-PATCH source, so
    #      it is a property of the unchanged callee.
    # ---------------------------------------------------------------------
    exhibit = ConditionSet(x, x > 0, FiniteSet(z))
    assert isinstance(exhibit, ConditionSet) and isinstance(exhibit.sym, Symbol)
    assert z != exhibit.sym
    # both substitution preconditions HOLD here: the condition does not mention
    # the replaced symbol at all, and the base substitution is a plain rewrite.
    assert refuses(lambda: exhibit.condition.subs(z, I)) is None
    assert refuses(lambda: exhibit.base_set.subs(z, I)) is None
    assert exhibit.base_set.subs(z, I) == FiniteSet(I)
    # ... and the operation's own rebuild is REFUSED, inside `__new__`'s sift.
    exhibit_build = refuses(lambda: exhibit.func(exhibit.sym,
                                                 exhibit.condition.subs(z, I),
                                                 exhibit.base_set.subs(z, I)))
    assert isinstance(exhibit_build, TypeError), (
        "the exhibit no longer refuses the operation's own rebuild (%r) — the "
        "third precondition's justification must be re-measured" % exhibit_build)
    exhibit_op = refuses(lambda: exhibit._eval_subs(z, I))
    assert exhibit_op is not None and type(exhibit_op) is type(exhibit_build), (
        "the real operation must propagate the constructor's refusal on the "
        "exhibit; got %r" % exhibit_op)
    # the RAW rebuild is accepted on the same input, so the refusal is about WHICH
    # arguments reach the constructor, not about the constructor being unusable.
    assert refuses(lambda: exhibit.func(exhibit.sym, exhibit.condition,
                                        exhibit.base_set)) is None

    # ---------------------------------------------------------------------
    # (15) every extra invocation shape the model can still NAME is accepted on
    #      every boundary case. This is the complete list: the sorts admit no
    #      others, and on the pool the same enumeration was measured above for
    #      every input the three preconditions admit (n_builds_checked).
    # ---------------------------------------------------------------------
    n_writable = 0
    for name, cs, old, new in cases:
        sym, c0, s0 = cs.args
        if not isinstance(sym, Symbol):
            continue
        c1, s1 = c0.subs(old, new), s0.subs(old, new)
        shapes = [
            ("double condition substitution", lambda c1=c1, old=old, new=new: c1.subs(old, new)),
            ("double base substitution", lambda s1=s1, old=old, new=new: s1.subs(old, new)),
            ("raw-component rebuild", lambda cs=cs, sym=sym, c0=c0, s0=s0: cs.func(sym, c0, s0)),
        ]
        for oname, ob in (("binder", sym), ("replaced object", old),
                          ("replacement", new)):
            for sname, ss in (("raw base", s0), ("substituted base", s1)):
                shapes.append(
                    ("value-keyed rebuild on the %s over the %s" % (oname, sname),
                     lambda ob=ob, ss=ss: ConditionSet(ob, Contains(ob, ss), ss)))
        for label, thunk in shapes:
            exc = refuses(thunk)
            assert exc is None, (
                "the writable extra invocation %r on case %r raised %s: %s — a "
                "discarded call of that shape would verify while the code it "
                "denotes signals an error"
                % (label, name, type(exc).__name__, exc))
            n_writable += 1
    assert n_writable >= 70, n_writable

    print("G-AX OK: unchanged A-reference callees Basic.subs / ConditionSet ctor "
          "are pure; the deep model cs.func(cs.sym, subs(cond), subs(base)) equals "
          "the real pre-patch _eval_subs on every non-collapse input (%d boundary + "
          "%d fuzz); on every collapse input (%d boundary + %d fuzz) the real "
          "pre-patch _eval_subs equals the substituted-value rebuild (binds `new`, "
          "the bug); %d boundary collapse witnesses are DISCRIMINATING "
          "(original-binder rebuild not dummy_eq to substituted-value rebuild), so "
          "the spec's binder choice is observable; %d compound (Tuple) binder "
          "inputs confirm the excluded arm returns self untouched.\n"
          "G-AX PARTIALITY: Basic.subs is sort-preserving (%d condition x %d set "
          "substitutions, both directions); the constructor is TOTAL on the modeled "
          "sorts inside the modeled domain — %d (Symbol binder, condition, set) "
          "invocations and %d (object, same set) membership invocations all "
          "accepted, 0 refused — and PARTIAL outside them: on the problem "
          "statement's own F2P witness it refuses all %d excluded shapes (%s), and "
          "the two domain restrictions are forced, %d Expr-non-Symbol binder "
          "pairings refused (e.g. %s: %s) and %d cross-base membership bindings "
          "refused (e.g. %s: %s). Its domain is NOT exhausted by the sorts, and the "
          "third precondition is forced by that: %d well-sorted (Symbol binder, "
          "Boolean condition, Set base) triples are refused because the "
          "constructor tests the condition against the base's elements (e.g. "
          "ConditionSet(%s, %s, %s) -> %s: %s), and %d value-keyed invocations are "
          "refused for a non-comparable replacement over a substituted base (e.g. %s "
          "over %s -> %s). So every "
          "invocation the model can express INSIDE its preconditions is accepted by "
          "the real callee, and the shapes it refuses are unwritable rather than "
          "merely unproven.\n"
          "G-AX SUBSTITUTION PARTIALITY: Basic.subs is partial too — %d refusal "
          "shapes exhibited (%s) — so the two definedness preconditions and the "
          "Old/New and SetObj/BuiltSet sort splits are forced by the real callee. "
          "The three preconditions hold on the problem statement's own F2P input "
          "and on %d of %d pool inputs; on all %d inputs a component substitution "
          "excludes, the real operation itself signals an error (so they are not "
          "stricter than its domain); on all %d inputs they admit, the real "
          "operation returns normally (so they are sufficient for a "
          "total-correctness contract); the domain is closed under re-application "
          "of the same substitution (%d of %d, idempotent on %d), and all %d extra "
          "invocation shapes the sorts still let an impl name are accepted on the "
          "boundary cases plus %d nameable set-building invocations on the admitted "
          "pool inputs.\n"
          "G-AX CONSTRUCTOR DEFINEDNESS (BuildsDefined): the exhibit "
          "ConditionSet(x, x > 0, FiniteSet(z)) with z -> I has both component "
          "substitutions defined, old != sym, and every slot well-sorted, yet the "
          "operation's own rebuild raises %s: %s inside __new__'s sift and the real "
          "pre-patch _eval_subs propagates it (%s) while the RAW rebuild is "
          "accepted — so the precondition is necessary for a total-semantics "
          "contract and is about WHICH arguments reach the constructor. Over the "
          "pool it excludes %d of the %d inputs the two substitution preconditions "
          "admit: %d because the operation's own rebuild is refused — the real "
          "operation raises on all %d of those, so that clause is exactly as strict "
          "as the operation itself (e.g. %r with %r -> %r, refused: %s) — and %d "
          "because only a writable EXTRA shape is refused, on %d of which the "
          "operation itself returns normally: that sliver is the price of building "
          "axioms that are total on their sorts, and the contract is silent there "
          "rather than over-strong."
          % (n_noncollapse, n_fuzz - n_fuzz_collapse, n_collapse, n_fuzz_collapse,
             n_witness, n_excluded,
             n_sort_cond, n_sort_set, n_mkset, n_onvalue,
             len(arms), "; ".join("%s -> %s" % (lbl, type(e).__name__)
                                  for lbl, e in arms),
             n_nonsym_refused,
             type(nonsym_witness[3]).__name__, nonsym_witness[3],
             n_cross_refused,
             type(cross_witness[3]).__name__, cross_witness[3],
             n_nonsortal_refused,
             nonsortal_witness[0], nonsortal_witness[1], nonsortal_witness[2],
             type(nonsortal_witness[3]).__name__, nonsortal_witness[3],
             n_onvalue_refused, onvalue_witness[0], onvalue_witness[1],
             type(onvalue_witness[2]).__name__,
             len(sub_refusals),
             "; ".join("%s -> %s" % (lbl, type(e).__name__)
                       for lbl, e in sub_refusals),
             n_dom, n_dom + n_dom_excluded + n_build_excluded, n_dom_excluded,
             n_suff, n_closed, n_dom, n_idem, n_writable, n_builds_checked,
             type(exhibit_build).__name__, exhibit_build,
             type(exhibit_op).__name__,
             n_build_excluded, n_dom + n_build_excluded,
             n_build_excluded_own, n_build_excluded_own_raises,
             build_witness[0], build_witness[1], build_witness[2],
             ", ".join(build_witness[3]),
             n_build_excluded_extra, n_build_excluded_extra_op_ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
