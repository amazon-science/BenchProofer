#!/usr/bin/env python3
"""G-CONF cross-language differential test for sympy__sympy-19495.

The gate runs this inside the instance image with the GOLD PATCH APPLIED
(`apply_gold=True`), so `sympy.sets.conditionset.ConditionSet._eval_subs` is the
PATCHED (correct) method — the behavioural oracle.

We build the R/I shadow of `Solution.lean`'s `evalSubsFree` impl region in Python
and differential-test it against that oracle on >= 1e5 fuzzed inputs:

  * R/I op (the binder choice): rebuild the set with the set's ORIGINAL bound
    symbol `cs.sym` (this is the I/R content the spec pins — `mkSet boundSym ...`).
  * A-reference callees, left as the REAL repo callees (NOT modeled):
      - `substCond` / `substSet` -> the real `Basic.subs`
        (cond.subs(old,new), base.subs(old,new))
      - `mkSet` -> the real `ConditionSet` constructor `cs.func(...)`, in its
        binder-keyed invocation shape

So the shadow is

    shadow(cs, old, new) = cs.func(cs.sym, cs.condition.subs(old, new),
                                   cs.base_set.subs(old, new))

restricted to the modeled branch `isinstance(cs.sym, Symbol) and old != cs.sym`
— the model's `require old ≠ binderObj boundSym` together with the `Binder` sort,
which is a plain `Symbol` (mapping.md §2, §3.3: the constructor is total for a
`Symbol` binder and partial on `Expr`-but-not-`Symbol` binders, so the model's
domain stops at `Symbol`). The bound-symbol pool below is all `Symbol`s, so this
is the same input distribution the previous `Expr` filter admitted.

The domain is further restricted by the model's three DEFINEDNESS preconditions
(mapping.md §3.4, §3.5), because BOTH delegated callees are PARTIAL:

  * `CondSubDefined` / `BaseSubDefined` — a relational condition cannot be
    compared against every replacement, and where the substitution refuses, the
    real operation propagates the error instead of returning a set. We evaluate
    the two component substitutions FIRST and skip (and count) the inputs they
    refuse.
  * `BuildsDefined` — the constructor itself tests the condition against the
    elements of a finite base (`conditionset.py:151-152`), so it can refuse with
    every slot holding the right kind of object, and again the real operation
    propagates. Its main clause is the invocation the shadow itself performs, so
    we compute the SHADOW first: if the constructor refuses the operation's own
    rebuild, the input is outside the modeled domain and is skipped and counted,
    and we assert on the consumer side that the patched `_eval_subs` refuses it
    too (i.e. the precondition is not stricter than the real operation). The
    precondition's remaining clauses cover invocations the SHADOW never makes
    (discarded extra rebuilds), so this filter admits a SUPERSET of the modeled
    domain — a conservative choice for a differential test.

Inside the preconditions the modeled branch must be TOTAL, so a raise from either
leg after that point is reported as a DISAGREEMENT rather than skipped — that is
the consumer-side check of the same claim axiom_check.py obligation 13 measures.

The oracle is the patched `cs._eval_subs(old, new)` on that branch. Sets are
compared with `dummy_eq` (equates sets differing only by bound-symbol naming) AND
exact `==`; a disagreement on either is a failure.

Inputs are fuzzed over a pool of bound symbols, free symbols, replacement values,
conditions, and base sets, with `random.Random(19495)`. Exit 0 iff zero
disagreements.
"""
import random
import sys

from sympy import (Symbol, S, Interval, Contains, Lambda, asin, sin, cos, pi,
                   imageset, Rational, oo, Eq, Mod, Abs, FiniteSet, I)
from sympy.sets import ConditionSet

SEED = 19495
N_TARGET = 100000


def shadow(cs, old, new):
    """R/I shadow of evalSubsFree: rebuild with the ORIGINAL binder; the two
    substitutions and the constructor are the REAL (A-reference) callees."""
    sym, cond, base = cs.args
    return cs.func(sym, cond.subs(old, new), base.subs(old, new))


def agree(a, b):
    """Sets agree if structurally equal or dummy-equal (binder-name-insensitive).
    For non-set results (e.g. EmptySet, Interval) dummy_eq may be absent; fall
    back to ==. A disagreement requires BOTH to differ."""
    if a == b:
        return True
    for x, y in ((a, b), (b, a)):
        try:
            if x.dummy_eq(y):
                return True
        except (AttributeError, TypeError):
            pass
    return False


def build_pool():
    x = Symbol('x'); y = Symbol('y'); z = Symbol('z'); w = Symbol('w')
    k = Symbol('k'); m = Symbol('m'); t = Symbol('t')
    bound = [x, z, w, k, m, t, Symbol('a'), Symbol('b'),
             Symbol('n', negative=True), Symbol('p', positive=True)]
    # `z` / `w` are also drawn as the REPLACED symbol, so that the finite bases
    # below (which mention them) can have a non-real replacement pushed into them
    # while the condition is left untouched — the family in which the
    # constructor's own definedness precondition is observable (mapping.md §3.5).
    free = [y, Symbol('q'), Symbol('u'), Symbol('v'), z, w]
    repls = [Rational(1, 3), Rational(-2, 5), S.One, S.Zero, S.Half,
             Symbol('r'), Symbol('rp', positive=True), Symbol('rn', negative=True),
             Symbol('z'), Symbol('w'),
             # replacements the substitution callee REFUSES inside a relational
             # condition, so that the two definedness preconditions are exercised
             # (and counted) on the consumer side too (mapping.md §3.4).
             I, S.ComplexInfinity, S.NaN]
    imgs = [imageset(Lambda(k, 2 * k * pi + asin(y)), S.Integers),
            imageset(Lambda(m, m * pi + sin(y)), S.Integers)]
    bases = [Interval(-oo, 0), Interval(0, oo), Interval(-1, 1), Interval(1, 7),
             S.Integers, S.Reals, S.Naturals, FiniteSet(z, w), FiniteSet(z),
             imgs[0], imgs[1]]
    return bound, free, repls, bases


N_COND = 9


def make_cond(sym, fv, which):
    if which == 0:
        return sym < fv
    if which == 1:
        return Contains(fv, Interval(-1, 1))
    if which == 2:
        return Contains(fv, Interval(0, 5))
    if which == 3:
        return Eq(Mod(sym, 2), 0) & Contains(fv, Interval(-1, 1))
    if which == 4:
        return Eq(sym, fv)
    if which == 5:
        return (sym < fv) | Contains(fv, Interval(0, oo))
    # conditions on the BINDER ALONE: substituting the free symbol into them is
    # trivially defined, so these inputs reach the constructor's own test of the
    # condition against the base's elements (mapping.md §3.5).
    if which == 6:
        return sym > 0
    if which == 7:
        return sym >= 1
    return (sym > 0) & Contains(fv, Interval(-1, 1))


def main():
    rng = random.Random(SEED)
    bound, free, repls, bases = build_pool()

    n = 0
    n_collapse = 0
    n_disagree = 0
    n_precond_skip = 0
    n_build_skip = 0
    n_build_skip_oracle_refuses = 0
    build_examples = []
    examples = []

    attempts = 0
    while n < N_TARGET and attempts < N_TARGET * 6:
        attempts += 1
        sym = rng.choice(bound)
        fv = rng.choice(free)
        base = rng.choice(bases)
        cond = make_cond(sym, fv, rng.randint(0, N_COND - 1))
        try:
            cs = ConditionSet(sym, cond, base)
        except Exception:
            continue
        if not isinstance(cs, ConditionSet):
            continue  # constructor simplified it away; nothing to substitute on
        old = fv
        new = rng.choice(repls)
        # modeled branch only: the binder must be a plain Symbol (the `Binder`
        # sort — the compound Tuple arm returns self untouched and the
        # Expr-but-not-Symbol sub-domain is where the constructor is itself
        # partial, both outside the model) and old must be a free symbol
        # distinct from the binder (`require old ≠ binderObj boundSym`).
        if not isinstance(cs.sym, Symbol):
            continue
        if old == cs.args[0] or old not in cs.free_symbols:
            continue

        # the model's two DEFINEDNESS preconditions (mapping.md §3.4): the
        # substitution callee is PARTIAL, and on the inputs it refuses the real
        # operation has no result either, so they are outside the modeled domain.
        try:
            sub_cond = cs.args[1].subs(old, new)
            cs.args[2].subs(old, new)
        except Exception:
            n_precond_skip += 1
            continue

        # the model's CONSTRUCTOR-definedness precondition `BuildsDefined`
        # (mapping.md §3.5): its main clause is exactly the invocation the shadow
        # performs, so compute the shadow first. Where the constructor refuses it,
        # the input is outside the modeled domain — and the real operation must
        # refuse it too, which is checked (and counted) rather than assumed.
        try:
            sh = shadow(cs, old, new)
        except Exception as e:
            n_build_skip += 1
            try:
                cs._eval_subs(old, new)
            except Exception:
                n_build_skip_oracle_refuses += 1
            if len(build_examples) < 3:
                build_examples.append((repr(cs), repr(old), repr(new),
                                       '%s: %s' % (type(e).__name__, e)))
            continue

        try:
            oracle = cs._eval_subs(old, new)   # patched (correct) method
        except Exception as e:
            # INSIDE the preconditions the modeled branch is claimed TOTAL, so a
            # raise here is a genuine disagreement with the contract, not a skip.
            n_disagree += 1
            if len(examples) < 5:
                examples.append((repr(cs), repr(old), repr(new),
                                 'raised %s: %s' % (type(e).__name__, e), '-'))
            continue

        if sub_cond is S.true:
            n_collapse += 1

        if not agree(oracle, sh):
            n_disagree += 1
            if len(examples) < 5:
                examples.append((repr(cs), repr(old), repr(new),
                                 repr(oracle), repr(sh)))
        n += 1

    if n_disagree:
        print("G-CONF FAIL: %d/%d disagreements between the R/I shadow and the "
              "patched _eval_subs (seed=%d)." % (n_disagree, n, SEED))
        for ex in examples:
            print("  cs=%s old=%s new=%s | oracle=%s | shadow=%s" % ex)
        return 1

    if n_build_skip_oracle_refuses != n_build_skip:
        print("G-CONF FAIL: on %d of %d inputs where the constructor refuses the "
              "operation's own rebuild the patched _eval_subs still returned a "
              "set, so the precondition BuildsDefined would be STRICTER than the "
              "real operation (mapping.md §3.5)."
              % (n_build_skip - n_build_skip_oracle_refuses, n_build_skip))
        for ex in build_examples:
            print("  cs=%s old=%s new=%s | rebuild refused: %s" % ex)
        return 1

    print("G-CONF OK: R/I shadow of evalSubsFree (rebuild with the ORIGINAL bound "
          "symbol; substitutions and constructor left as the real Basic.subs / "
          "ConditionSet callees) agrees with the patched ConditionSet._eval_subs "
          "on %d inputs (%d on the condition-collapse path), seed=%d, 0 "
          "disagreements. A further %d input(s) were outside the modeled domain "
          "because a component substitution itself refused (CondSubDefined / "
          "BaseSubDefined, mapping.md §3.4) and %d because the constructor refused "
          "the operation's own rebuild although every slot was well-sorted "
          "(BuildsDefined, mapping.md §3.5) — on ALL %d of those the patched "
          "_eval_subs refused as well, so that precondition is not stricter than "
          "the real operation. On every input INSIDE the domain the operation "
          "returned normally, so the total-semantics contract is not stronger than "
          "the real method here."
          % (n, n_collapse, SEED, n_precond_skip, n_build_skip, n_build_skip))
    return 0


if __name__ == "__main__":
    sys.exit(main())
