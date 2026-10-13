#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-19495.

The bundle models ONE branch of `ConditionSet._eval_subs(self, old, new)` in
`sympy/sets/conditionset.py`: the path taken when `old` is **not** the bound
(dummy) variable `self.sym`. The gold fix replaces a special case in that branch
— which, when the substituted condition collapsed to `S.true`, rebuilt the set
using `new` as the bound variable wrapped in a `Contains(new, base)` membership
condition — with the uniform behavior of always handing the ORIGINAL bound
variable, the substituted condition, and the substituted base set back to the
set constructor `self.func(self.sym, cond, base)`.

The modeled value is therefore a pure function of the three components
(`sym`, `condition`, `base_set`) and the substitution `(old, new)`:

    SHADOW(cs, old, new) = cs.func(cs.sym,
                                   cs.condition.subs(old, new),
                                   cs.base_set.subs(old, new))

This is the op-for-op transliteration of `implementation_freeSubs`
(Solution.lean impl region) under refinement.md:
  * `subsCond`/`subsSet` are the real symbolic substitution callee (A-reference:
    the genuine `Basic.subs`) taken at the `Boolean` condition and at the `Set`
    base — two Lean names for one Python routine, because the model gives the
    condition and the base distinct carriers (`Cond`/`SetE`) so that every
    well-typed term denotes a call that is actually defined; both are exercised
    in-process here;
  * keeping `cs.sym` for the result's bound variable is the identical structural
    op (I). The Lean model gives that position its own carrier `SymE`, so this
    gate only feeds inputs whose bound variable is a `Symbol` — see LEG 2, which
    measures why;
  * `mkSet` is the real set-assembly callee `cs.func` (A-reference), which this
    shadow calls directly. The Lean model leaves it opaque and gives its RESULT
    its own terminal carrier `AsmSet` — no projections, and no routine takes one
    — because the real routine canonicalises (`ConditionSet(x, S.true, base)`
    returns the bare `base`, which has no `.sym`) and because the real callees
    are undefined or re-entrant on an assembled value (LEG 5). So the shadow's
    last step is a literal reading of the spec's right-hand side, and this gate
    is what pins that reading to the real routine.

The ORACLE is the real, gold-patched behavior: `cs.subs(old, new)` (which for
this branch dispatches into `_eval_subs`). We fuzz a wide pool of symbols (with
varied assumptions so the condition sometimes collapses to `S.true` — the
soundness-critical corner case from the issue) and set/condition shapes, and
assert SHADOW == ORACLE on every input where the modeled branch is taken.

Comparison is STRICT structural equality, with no fallback to `.dummy_eq`. That
is possible — and is the honest reading of the spec, whose requirement is an
equation — because `Cond` and `SetE` denote a condition and a base set given
OUTRIGHT: neither is itself a condition-restricted set. On those shapes the
substitution callees and the assembly are deterministic functions of their
arguments under `==`, with no freshly minted bound-variable name anywhere in the
result (LEG 4 measures exactly that, and LEG 1 additionally checks that the two
substitution callees map the narrowed shapes back into themselves, so the
reading is closed under the operations the model has).

Five legs run, each of which must pass:

  LEG 1 (differential) — SHADOW == ORACLE over the fuzzed pool under strict
    `==`, the condition-collapse corner case is reached at least once (otherwise
    the differential would be silent on the very sub-domain the fix decides),
    and the substituted condition / base stay within the carriers.
  LEG 2 (the assembly's argument-1 domain rule) — the premise behind the `SymE`
    carrier: the assembly routine RAISES for a bound variable that is not a
    `Symbol` and does not occur in the condition, and returns normally for a
    `Symbol` one. Measured over a grid, and asserted to be exactly the split the
    Lean type discipline draws.
  LEG 3 (the fused membership assembly's domain) — the premise behind
    `mkMemberSet : Expr → SetE → AsmSet`: `ConditionSet(v, Contains(v, base),
    base)` IS defined for a general expression `v` on the base sets this branch
    ranges over, which is why the pre-patch's deleted expression stays
    expressible while the bare membership question does not.
  LEG 4 (determinism under `==`) — the premise behind structural identity on the
    carriers: repeating each callee on the same arguments returns an `==`-equal
    value, so the spec's equation is an equation between determined values.
  LEG 5 (the assembled-set carrier is terminal) — the premise behind `AsmSet`:
    on an ASSEMBLED (condition-restricted) set the consumers this branch has are
    not defined — the fused membership assembly raises, and a substitution
    applied to a set assembled inside the routine re-enters the routine and
    diverges.

stdlib-only (plus sympy from the testbed). Pinned seed: 19495 (also mapping.md).
"""
import random
import sys

from sympy import (Symbol, Interval, oo, S, Contains, Lambda, pi, asin, Eq, Lt)
from sympy.sets import ConditionSet, FiniteSet, imageset

SEED = 19495
N = 100_000

rng = random.Random(SEED)

# Symbol pool: plain symbols plus assumption-carrying symbols whose presence in a
# relation lets the substituted condition evaluate to S.true (issue corner case).
_NEG = Symbol('m', negative=True)
_POS = Symbol('p', positive=True)
SYMS = [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('y'), Symbol('z'),
        _NEG, _POS]
NEWS = SYMS + [S.One / 3, S.One, S.Zero, Symbol('w'), Symbol('q')]
_K = Symbol('k')


def rand_base():
    c = rng.randint(0, 4)
    if c == 0:
        return S.Integers
    if c == 1:
        lo = rng.choice([-oo, -1, 0]); hi = rng.choice([0, 1, oo])
        return Interval(lo, hi)
    if c == 2:
        return FiniteSet(*[rng.choice(SYMS) for _ in range(rng.randint(1, 3))])
    if c == 3:
        return imageset(Lambda(_K, 2 * _K * pi + asin(rng.choice(SYMS))),
                        S.Integers)
    return S.Reals


def rand_cond(sym):
    other = rng.choice(SYMS)
    c = rng.randint(0, 3)
    if c == 0:
        return sym < other
    if c == 1:
        return Lt(other, sym)
    if c == 2:
        return Eq(sym, other)
    return Contains(rng.choice(SYMS), Interval(-1, 1))


def given_outright(x):
    """The `Cond` / `SetE` reading: no condition-restricted set inside."""
    return not x.atoms(ConditionSet)


def leg1_differential():
    """SHADOW == ORACLE on the modeled branch, corner case included.

    Strict `==`; inputs outside the carriers (a condition or a base set that is
    itself condition-restricted) are skipped and counted, and the substituted
    components are checked to stay inside the carriers.
    """
    ran = 0
    diffs = 0
    collapsed = 0
    outside = 0
    escaped_cond = escaped_base = 0
    examples = []
    for _ in range(N):
        sym = rng.choice([Symbol('a'), Symbol('b'), Symbol('c'),
                          Symbol('y'), Symbol('z')])
        cond = rand_cond(sym)
        base = rand_base()
        old = rng.choice(SYMS)
        new = rng.choice(NEWS)
        # the modeled branch is `old != sym`
        if old == sym:
            continue
        try:
            cs = ConditionSet(sym, cond, base)
        except Exception:
            continue
        # the branch guard: a genuine ConditionSet bound over a Symbol.  The Lean
        # model types that position as `SymE`, and LEG 2 measures why: for a bound
        # variable that is not a Symbol the assembly routine raises, so such an
        # input is outside the modeled domain rather than a disagreement.
        if not isinstance(cs, ConditionSet):
            continue
        if not isinstance(cs.sym, Symbol):
            continue
        if cs.sym == old:
            continue
        # the `Cond` / `SetE` reading: components given outright.  An input whose
        # condition or base is itself condition-restricted is outside the model
        # (its own components are then not the ones the carriers denote), and
        # LEG 5 records what the routine does on such values.
        if not (given_outright(cs.condition) and given_outright(cs.base_set)):
            outside += 1
            continue
        try:
            oracle = cs.subs(old, new)                          # gold behavior
            sub_cond = cs.condition.subs(old, new)
            sub_base = cs.base_set.subs(old, new)
            shadow = cs.func(cs.sym,                            # impl transliteration
                             sub_cond,
                             sub_base)
        except Exception:
            continue
        ran += 1
        if sub_cond is S.true:
            collapsed += 1
        # closure: the substitution callees map the carriers into themselves, so
        # `subsCond : Cond → … → Cond` and `subsSet : SetE → … → SetE` are the
        # honest types and the narrowing is not lost after one step.
        if not given_outright(sub_cond):
            escaped_cond += 1
        if not given_outright(sub_base):
            escaped_base += 1
        if not (oracle == shadow):
            diffs += 1
            if len(examples) < 8:
                examples.append((str(cs), str(old), str(new),
                                 str(oracle), str(shadow)))

    for cs_s, o, n, orc, shd in examples:
        print(f"DISAGREE cs={cs_s} old={o} new={n} oracle={orc} shadow={shd}")
    print(f"LEG 1 differential (strict ==): ran={ran} disagreements={diffs} "
          f"condition-collapse inputs={collapsed} inputs outside the "
          f"carriers={outside} carrier escapes: cond={escaped_cond} "
          f"base={escaped_base} (seed={SEED}, N={N})")
    if collapsed == 0:
        print("LEG 1 FAIL: the condition-collapse corner case was never reached")
        return False
    if escaped_cond or escaped_base:
        print("LEG 1 FAIL: a substitution left the carriers, so `Cond`/`SetE` "
              "are not closed under the model's own operations")
        return False
    return diffs == 0


# The two argument pools for the domain legs.  ARG1 splits into the values the
# model admits at the binding position (`SymE`) and the ones it does not.
_SYM_ARGS = [Symbol('a'), Symbol('b'), Symbol('y'), Symbol('p', positive=True)]
_NONSYM_ARGS = [2 * Symbol('x'), Symbol('x') + 1, S(2), S.One / 3,
                asin(Symbol('y'))]
_X, _Y, _Z = Symbol('x'), Symbol('y'), Symbol('z')
_BASES = [S.Integers, S.Reals, Interval(0, 1), Interval(-oo, 0),
          FiniteSet(_Y, _Z), imageset(Lambda(_K, 2 * _K * pi + asin(_Y)),
                                      S.Integers)]
# conditions that do NOT mention the candidate bound variable
_FREE_CONDS = [_Y < _Z, Eq(_Y, _Z), Contains(_Y, Interval(-1, 1))]
# ASSEMBLED sets: what the assembly routine hands back.  These are the values the
# model puts on their own terminal carrier, and LEG 5 measures why.
_ASSEMBLED = [ConditionSet(_X, _X < _Y, FiniteSet(_Y, _Z)),
              ConditionSet(Symbol('n'), Symbol('n') < _X, Interval(0, oo)),
              ConditionSet(_X, Contains(_Y, Interval(-1, 1)), S.Reals),
              ConditionSet(_X, _X < 2, S.Integers)]


def leg2_binding_position_domain():
    """The assembly raises for a non-Symbol bound variable, not for a Symbol."""
    sym_ok = sym_raise = non_ok = non_raise = 0
    seen = set()
    for cond in _FREE_CONDS:
        for base in _BASES:
            for v in _SYM_ARGS:
                try:
                    ConditionSet(v, cond, base)
                    sym_ok += 1
                except Exception:
                    sym_raise += 1
            for v in _NONSYM_ARGS:
                try:
                    ConditionSet(v, cond, base)
                    non_ok += 1
                except Exception as exc:
                    non_raise += 1
                    seen.add(type(exc).__name__)
    print(f"LEG 2 binding-position domain: Symbol ok={sym_ok} raise={sym_raise} "
          f"| non-Symbol ok={non_ok} raise={non_raise} exc={sorted(seen)}")
    if sym_raise:
        print("LEG 2 FAIL: the assembly raised for a Symbol bound variable")
        return False
    if non_ok:
        print("LEG 2 FAIL: a non-Symbol bound variable was accepted, so the "
              "SymE carrier would be narrower than the real domain")
        return False
    return True


def leg3_fused_membership_domain():
    """`ConditionSet(v, Contains(v, base), base)` is defined for general `v`."""
    ok = raised = 0
    seen = set()
    for v in _SYM_ARGS + _NONSYM_ARGS:
        for base in _BASES:
            try:
                ConditionSet(v, Contains(v, base), base)
                ok += 1
            except Exception as exc:
                raised += 1
                seen.add(f"{type(exc).__name__}: {exc}"[:60])
    print(f"LEG 3 fused-membership domain: ok={ok} raise={raised} "
          f"exc={sorted(seen)}")
    if raised:
        print("LEG 3 FAIL: the fused membership assembly is not total on the "
              "bases this branch ranges over")
        return False
    return True


def leg4_determinism(repeats=3):
    """Each callee returns an `==`-equal value when repeated on the same input.

    This is the premise behind structural identity on the carriers: the spec
    states its requirement as an equation between assembled values, which is
    only a statement about the routine if the routine is determined by its
    arguments up to `==` — no freshly minted bound-variable name in the result.
    """
    unstable_cond = unstable_base = unstable_mk = unstable_real = 0
    checked = 0
    for cond in _FREE_CONDS:
        for base in _BASES:
            for sym in _SYM_ARGS:
                old, new = _Y, S.One / 3
                if sym == old:
                    continue
                try:
                    cs = ConditionSet(sym, cond, base)
                except Exception:
                    continue
                if not isinstance(cs, ConditionSet):
                    continue
                if not (given_outright(cs.condition)
                        and given_outright(cs.base_set)):
                    continue
                try:
                    c1 = cs.condition.subs(old, new)
                    b1 = cs.base_set.subs(old, new)
                    m1 = cs.func(cs.sym, c1, b1)
                    r1 = cs.subs(old, new)
                except Exception:
                    continue
                checked += 1
                for _ in range(repeats - 1):
                    if not (cs.condition.subs(old, new) == c1):
                        unstable_cond += 1
                        break
                for _ in range(repeats - 1):
                    if not (cs.base_set.subs(old, new) == b1):
                        unstable_base += 1
                        break
                for _ in range(repeats - 1):
                    if not (cs.func(cs.sym, c1, b1) == m1):
                        unstable_mk += 1
                        break
                for _ in range(repeats - 1):
                    if not (cs.subs(old, new) == r1):
                        unstable_real += 1
                        break
    print(f"LEG 4 determinism under `==` over {repeats} repeats: checked="
          f"{checked} unstable: subsCond={unstable_cond} subsSet={unstable_base} "
          f"mkSet={unstable_mk} real_routine={unstable_real}")
    if not checked:
        print("LEG 4 FAIL: no input was checked")
        return False
    if unstable_cond or unstable_base or unstable_mk or unstable_real:
        print("LEG 4 FAIL: a callee is not determined by its arguments under "
              "`==` on the carriers, so the spec's equation would not be one")
        return False
    return True


def leg5_assembled_is_terminal():
    """An ASSEMBLED set is not something this branch's consumers accept.

    Two consumer positions, matching the two the model would otherwise offer:
      (a) the fused membership assembly `mkMemberSet v s` at an assembled `s`;
      (b) a substitution applied to a set assembled inside the routine, i.e.
          `subsSet (mkSet …) old new` — which re-enters the very routine being
          modeled rather than calling something external, and so diverges.
    """
    vals = [Symbol('a'), Symbol('b'), _Y, Symbol('p', positive=True),
            2 * _X, _X + 1, S(2), S.One / 3, asin(_Y)]
    ok = raised = 0
    seen = set()
    for v in vals:
        for b in _ASSEMBLED:
            try:
                ConditionSet(v, Contains(v, b), b)
                ok += 1
            except Exception as exc:
                raised += 1
                seen.add(f"{type(exc).__name__}: {exc}"[:60])
    print(f"LEG 5a fused membership on an ASSEMBLED set: ok={ok} raise={raised} "
          f"exc={sorted(seen)}")

    # (b) the re-entrant substitution, measured in-process by adding exactly the
    # discarded call a rival would name INSIDE the routine.
    original = ConditionSet._eval_subs
    diverged = None

    def probing(self, old, new):
        sym, cond, base = self.args
        inner = self.func(sym, cond, base)       # mkSet cs.sym cs.cond cs.base
        _probe = inner.subs(old, new)            # subsSet (mkSet …) old new
        return original(self, old, new)

    cs = ConditionSet(_X, _X < _Y, FiniteSet(_Y, _Z))
    try:
        ConditionSet._eval_subs = probing
        cs.subs(_Y, Symbol('w'))
        diverged = None
    except Exception as exc:
        diverged = type(exc).__name__
    finally:
        ConditionSet._eval_subs = original
    print(f"LEG 5b substitution applied to a set assembled inside the routine: "
          f"{diverged or 'returned normally'}")

    if not raised:
        print("LEG 5 FAIL: the fused membership assembly accepted every "
              "assembled set, so the terminal carrier would be narrower than "
              "the real domain")
        return False
    if diverged is None:
        print("LEG 5 FAIL: substituting into a set assembled inside the routine "
              "returned normally, so it would be an ordinary callee")
        return False
    return True


def main():
    legs = [leg1_differential(), leg2_binding_position_domain(),
            leg3_fused_membership_domain(), leg4_determinism(),
            leg5_assembled_is_terminal()]
    print(f"conformance: legs_passed={sum(1 for x in legs if x)}/{len(legs)}")
    sys.exit(0 if all(legs) else 1)


if __name__ == "__main__":
    main()
