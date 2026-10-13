#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23950 (nagini).

Refutes (never proves) the refinement leg no other gate covers: does the MODEL
in model.py agree with the REAL gold-patched repository function it claims to
model?

SHADOW
  The `# impl-start` / `# impl-end` region of model.py, copied VERBATIM below
  (`return self.region`) together with the carrier classes it selects from
  (`Region`, `MembershipAssertion`), each minus its contract calls (`Requires`,
  `Ensures`, `Acc`, `MustTerminate`). Nothing is renamed, inlined or
  "simplified": `solution_region` still takes the assertion object and performs
  the same single stored-component selection, so what is diffed is the model's
  own operation and not a paraphrase of it.

  There are no `@Pure` helpers and no `@ContractOnly` axioms in this bundle
  (model.py `# pure-start`/`# axioms-start` regions are both empty, mapping.md
  §2 last paragraph), so nothing has to be shimmed or axiomatized: the whole
  impl region is directly executable, which is why this bundle is NOT a
  `conf_skip`. No `PSeq`/`ToSeq` carrier appears in the region either.

ORACLE
  The REAL patched repo function, CALLED (not transliterated):
  `sympy.sets.contains.Contains.as_set(self)` — `sympy/sets/contains.py:47` at
  base_commit 88664e6e0b781d0a8b5347896af74b555e92891e (mapping.md §1). The gate
  applies patch.diff (gold: `raise NotImplementedError()` -> `return
  self.args[1]`) and sets PYTHONPATH=/testbed, so `from sympy import Contains`
  resolves the patched in-tree sympy. Nothing is transliterated: a real
  `Contains` object is cheap to build in-container, so the oracle is the live
  method.

  Two false-green guards, because "the oracle silently did something else" is
  the failure mode that certifies nothing:
    * `inspect.getsource(Contains.as_set)` must contain `return self.args[1]`
      and must NOT contain `NotImplementedError` — otherwise a patch-apply
      failure or a stale module would be reported as agreement (exit 2).
    * `Contains.as_set` must not be overridden anywhere below `Contains` in the
      MRO of any object under test (checked per input: `type(c).as_set` must be
      the `Contains.as_set` function object), so the single binding in
      mapping.md §1 really is the whole oracle.

TYPE BRIDGE (mapping.md §2, inverted)
  Model side: `MembershipAssertion` with two opaque object-reference fields
  `element`, `region`; `Region` is identity-only (the model observes nothing but
  which component object comes back). Repo side: a `Contains` instance whose two
  STORED operands are `self.args[0]` (the asserted element) and `self.args[1]`
  (the region/set whose membership is asserted).

  Inversion direction: build the REAL object first (`Contains(x, s)`), then read
  its STORED operands back and wrap them, `MembershipAssertion(c.args[0],
  c.args[1])`. Generating in this direction is what keeps the bridge exact —
  sympy may canonicalize the constructor operand `s` into an equal-but-distinct
  object (confirmed in-container: `Contains(x, FiniteSet(y)).args[1] is
  FiniteSet(y)` is False while `== ` is True, mapping.md §1), so seeding the
  model carrier from `s` instead of from `c.args[1]` would be testing the
  bridge's own bug. Every wrapped pair satisfies the model's `Requires`, which
  is only field permission (`Acc(self.element, 1/2)`, `Acc(self.region, 1/2)`)
  plus `MustTerminate(2)`: any two references qualify, and each call's return
  witnesses termination.

COMPARISON
  The model's postcondition is `Result() is self.region` — object IDENTITY — so
  the differential is on identity: `solution_region(assertion) is c.as_set()`.
  Three further observations are pinned on every input, so that a shadow which
  returned the wrong component, or a real method that rebuilt a fresh equal
  object, cannot pass unnoticed:
    * `real == s_in` — the F2P observation (`Contains(x, FiniteSet(y)).as_set()
      == FiniteSet(y)`), by `==` because of the canonicalization above;
    * `real is c.args[1]` — the real method returns the STORED operand, not a
      copy (mapping.md §2 row 3);
    * whenever the two stored operands are distinct objects, `real is not
      c.args[0]` — the element component is never what comes back (the
      discriminator refinement.md relies on).

INPUT DOMAIN — >= 1e5 satisfying the Requires
  The domain (arbitrary sympy element x arbitrary region) is infinite, so:
  boundary catalogue first (the exact F2P triples; every kind of region —
  Reals/Integers/Naturals/Rationals/Complexes/EmptySet/UniversalSet/FiniteSet/
  Interval/Union/Intersection/ProductSet/ImageSet/ConditionSet/Range; degenerate
  shapes: the two operands the same object, a region used as the element, a
  nested `Contains` as the element, a non-`Set` region), then seeded fuzz to
  fill the count. The impl region is straight-line — one path, no branch — so
  branch coverage is "the selection executed"; what the catalogue varies instead
  is the input CLASS, since that is the only thing that could make the real
  method diverge.

  Both construction paths of the real object are exercised, and neither is
  routed around: `Contains(x, s)` with default evaluation (kept only when
  `Contains.eval` did not collapse it to a Boolean/Set — a collapsed value is a
  different repo function, not this one) and `Contains(x, s, evaluate=False)`,
  which keeps decidable pairings such as `Contains(2, S.Integers)` as genuine
  `Contains` objects so that the region under specification is reached for them
  too rather than discarded.

ANTI-VACUITY CONTROL
  A deliberately WRONG shadow (`return self.element`, the mutant G-PBT rejects
  as `wrong-component-return-element`) is run over the same boundary catalogue
  and MUST disagree with the real method at least once. If it agreed
  everywhere, the comparison would not be discriminating and a green verdict
  here would mean nothing; that case exits 1.

>= 1e5 Requires-satisfying inputs. Pinned seed: 23950 (recorded in mapping.md
under `## G-CONF`). Exit 0 iff zero disagreements; on a disagreement the input
and both outputs are printed and the exit code is 1. stdlib + sympy (the repo
package under change) only.
"""
import json
import random
import sys

SEED = 23950
N_TOTAL = 100_000  # >= 1e5 differential comparisons


# --- model.py carriers, contracts stripped, otherwise verbatim ---------------

class ViewNotProduced(Exception):
    """model.py's deferral signal. The spec admits no `Exsures`, so a raise is a
    verification failure; kept here only so the copied region is complete."""


class Region:
    """A region of values, abstracted to an opaque object reference."""

    def __init__(self):
        # Ensures(True)  [stripped]
        pass


class MembershipAssertion:
    """The proposition that ``element`` belongs to ``region``, abstracted to its
    two touched components."""

    def __init__(self, element, region):
        # Ensures(Acc(self.element, 1/2) and self.element is element)  [stripped]
        # Ensures(Acc(self.region, 1/2) and self.region is region)     [stripped]
        self.element = element
        self.region = region


# --- the impl region of model.py, VERBATIM, contract calls stripped ----------

def solution_region(self):
    # Requires(Acc(self.element, 1/2))     [stripped]
    # Requires(Acc(self.region, 1/2))      [stripped]
    # Requires(MustTerminate(2))           [stripped]
    # Ensures(Acc(self.element, 1/2))      [stripped]
    # Ensures(Acc(self.region, 1/2))       [stripped]
    # Ensures(Result() is self.region)     [stripped]
    # impl-start
    return self.region
    # impl-end


def wrong_shadow(self):
    """The `wrong-component-return-element` mutant (G-PBT case id). Used ONLY by
    the anti-vacuity control: it must disagree with the real method somewhere."""
    return self.element


# --- type bridge: real Contains -> the model's MembershipAssertion -----------

def to_model(c):
    """mapping.md §2 inverted: wrap the object's STORED operands, `self.args[0]`
    ↔ `self.element` and `self.args[1]` ↔ `self.region`. Read back from `args`,
    never from the constructor arguments, because sympy may canonicalize the
    region operand into an equal but distinct object."""
    return MembershipAssertion(c.args[0], c.args[1])


# --- differential ------------------------------------------------------------

class Disagreement(Exception):
    pass


def check_one(Contains, as_set_fn, elem_in, set_in, evaluate, tag, state):
    """Build the real assertion, diff the shadow against the real patched
    `as_set`. Returns True if the input was in scope and checked."""
    try:
        if evaluate:
            c = Contains(elem_in, set_in)
        else:
            c = Contains(elem_in, set_in, evaluate=False)
    except Exception:
        # the constructor rejected this pairing (e.g. Contains.eval's Set type
        # gate): there is no assertion object, so nothing to compare.
        state["rejected"] += 1
        return False
    if type(c) is not Contains:
        # Contains.eval collapsed the assertion to a Boolean/Set: that value is
        # produced by a DIFFERENT repo function, not by the modeled as_set.
        state["collapsed"] += 1
        return False
    if type(c).as_set is not as_set_fn:
        raise Disagreement(
            "oracle binding incomplete: %s overrides as_set (mapping.md §1 "
            "binds only Contains.as_set)" % type(c).__name__)

    assertion = to_model(c)
    shadow = solution_region(assertion)
    real = as_set_fn(c)

    if shadow is not real:
        raise Disagreement(
            "DISAGREEMENT [%s]\n"
            "  element=%r  region=%r  evaluate=%s\n"
            "  assertion            = %r\n"
            "  shadow solution_region = %r  (id=%d)\n"
            "  real   Contains.as_set = %r  (id=%d)"
            % (tag, elem_in, set_in, evaluate, c, shadow, id(shadow),
               real, id(real)))
    # the real method returns the STORED operand, not a fresh equal object
    if real is not c.args[1]:
        raise Disagreement(
            "DISAGREEMENT [%s] real as_set() is not the stored operand\n"
            "  assertion=%r  real=%r  args[1]=%r" % (tag, c, real, c.args[1]))
    # the F2P observation: the produced region equals the region passed in
    try:
        eq_in = bool(real == set_in)
    except Exception:
        eq_in = False
    if not eq_in:
        raise Disagreement(
            "DISAGREEMENT [%s] produced region != the region asserted\n"
            "  assertion=%r  real=%r  input region=%r"
            % (tag, c, real, set_in))
    # the discriminator: never the element component (when the two differ)
    if c.args[0] is not c.args[1] and real is c.args[0]:
        raise Disagreement(
            "DISAGREEMENT [%s] real as_set() returned the ELEMENT component\n"
            "  assertion=%r  real=%r" % (tag, c, real))
    state["checked"] += 1
    return True


# --- input catalogue ---------------------------------------------------------

def pools(sp):
    """(elements, regions) — the operand pools, spanning every region kind the
    repo ships and every element kind that can be asserted to lie in one."""
    x = sp.Symbol('x')
    y = sp.Symbol('y')
    z = sp.Symbol('z')
    n = sp.Symbol('n', integer=True)
    p = sp.Symbol('p', positive=True)

    elems = [
        x, y, z, n, p,
        sp.Integer(0), sp.Integer(1), sp.Integer(-2), sp.Integer(7),
        sp.Rational(3, 2), sp.Rational(-7, 3),
        sp.Float(1.5), sp.pi, sp.oo, -sp.oo, sp.zoo, sp.nan,
        sp.I, sp.Integer(2) + 3 * sp.I,
        x + y, x * y, x ** 2, sp.sin(x), sp.exp(n),
        sp.S.Reals,                      # a region used as the element
        sp.Tuple(x, y),
    ]
    regions = [
        sp.S.Reals, sp.S.Integers, sp.S.Naturals, sp.S.Naturals0,
        sp.S.Rationals, sp.S.Complexes, sp.S.EmptySet, sp.S.UniversalSet,
        sp.FiniteSet(y), sp.FiniteSet(x, y), sp.FiniteSet(1, 2, 3),
        sp.FiniteSet(0), sp.FiniteSet(),
        sp.Interval(0, 1), sp.Interval(-2, 5),
        sp.Interval.open(0, 5), sp.Interval.Lopen(-1, sp.Rational(7, 2)),
        sp.Interval(-sp.oo, sp.oo),
        sp.Union(sp.FiniteSet(1), sp.Interval(2, 3)),
        sp.Union(sp.Interval(0, 1), sp.Interval(3, 4)),
        sp.Intersection(sp.S.Integers, sp.Interval(0, 10)),
        sp.Complement(sp.S.Reals, sp.FiniteSet(0)),
        sp.ProductSet(sp.S.Integers, sp.S.Reals),
        sp.ImageSet(sp.Lambda(n, 2 * n), sp.S.Integers),
        sp.ConditionSet(x, sp.Eq(x ** 2, 1), sp.S.Reals),
        sp.Range(0, 10, 2), sp.Range(sp.oo),
        sp.SymmetricDifference(sp.Interval(0, 2), sp.Interval(1, 3)),
    ]
    return elems, regions


def boundary_cases(sp):
    """Boundary catalogue: the exact F2P assertions, every region kind, and the
    degenerate operand shapes. Each entry is (element, region, evaluate)."""
    x = sp.Symbol('x')
    y = sp.Symbol('y')
    elems, regions = pools(sp)

    cases = [
        # --- the exact F2P shapes (sympy/sets/tests/test_contains.py::test_as_set)
        (x, sp.FiniteSet(y), True),
        (x, sp.S.Integers, True),
        (x, sp.S.Reals, True),
        # --- empty / singleton regions
        (x, sp.S.EmptySet, False),
        (x, sp.FiniteSet(), False),
        (x, sp.FiniteSet(y), False),
        (x, sp.S.UniversalSet, False),
        # --- decidable pairings, kept as genuine assertions via evaluate=False
        (sp.Integer(2), sp.S.Integers, False),
        (sp.Integer(-2), sp.S.Naturals, False),
        (sp.Rational(3, 2), sp.S.Integers, False),
        (sp.pi, sp.S.Rationals, False),
        # --- degenerate operand shapes
        (sp.S.Reals, sp.S.Reals, False),          # the two operands equal
        (sp.S.Integers, sp.S.Reals, False),       # a region as the element
        (sp.Contains(x, sp.S.Reals), sp.S.Reals, False),   # nested assertion
        (x, y, False),                            # a non-Set region
        (x, sp.Integer(3), False),                # a non-Set, numeric region
        (sp.Tuple(x, y), sp.ProductSet(sp.S.Reals, sp.S.Reals), False),
    ]
    # every region kind against a symbolic and a numeric element, both
    # construction paths
    for s in regions:
        for e in (x, y, sp.Integer(3), sp.Rational(3, 2)):
            cases.append((e, s, True))
            cases.append((e, s, False))
    # every element kind against the F2P regions
    for e in elems:
        for s in (sp.FiniteSet(y), sp.S.Integers, sp.S.Reals):
            cases.append((e, s, False))
    return cases


def main():
    try:
        import inspect
        import sympy as sp
        from sympy.sets.contains import Contains
    except Exception as e:
        print("G-CONF ERROR: cannot import the patched sympy Contains: %r" % e)
        return 2

    # false-green guard: the oracle must be the PATCHED function.
    try:
        src = inspect.getsource(Contains.as_set)
    except Exception as e:
        print("G-CONF ERROR: cannot read Contains.as_set source: %r" % e)
        return 2
    if "return self.args[1]" not in src or "NotImplementedError" in src:
        print("G-CONF ERROR: loaded Contains.as_set is not the patched body "
              "(patch not applied / stale module) - refusing to report "
              "agreement. source:\n%s" % src)
        return 2
    as_set_fn = Contains.as_set

    state = {"checked": 0, "collapsed": 0, "rejected": 0}
    cases = boundary_cases(sp)

    # --- 1) anti-vacuity control: the WRONG shadow must be caught -----------
    caught = 0
    for elem_in, set_in, evaluate in cases:
        try:
            c = Contains(elem_in, set_in) if evaluate else \
                Contains(elem_in, set_in, evaluate=False)
        except Exception:
            continue
        if type(c) is not Contains:
            continue
        if wrong_shadow(to_model(c)) is not as_set_fn(c):
            caught += 1
    if caught == 0:
        print("G-CONF FAIL: anti-vacuity control - the wrong shadow "
              "(return self.element) agreed with the real Contains.as_set on "
              "every one of the %d boundary inputs, so this differential is "
              "not discriminating." % len(cases))
        print(json.dumps({"checked": 0, "disagreements": 1, "seed": SEED,
                          "status": "fail", "reason": "non-discriminating"}))
        return 1

    # --- 2) boundary catalogue ----------------------------------------------
    try:
        for elem_in, set_in, evaluate in cases:
            check_one(Contains, as_set_fn, elem_in, set_in, evaluate,
                      "boundary", state)
        n_boundary = state["checked"]

        # --- 3) seeded fuzz to fill >= 1e5 ---------------------------------
        rng = random.Random(SEED)
        elems, regions = pools(sp)
        guard = 0
        while state["checked"] < N_TOTAL:
            guard += 1
            if guard > 40 * N_TOTAL:
                print("G-CONF ERROR: could not reach %d in-scope inputs "
                      "(checked=%d)" % (N_TOTAL, state["checked"]))
                return 2
            elem_in = rng.choice(elems)
            set_in = rng.choice(regions)
            # 1/5 of draws go through the default-evaluation path (kept only
            # when the assertion stays symbolic); the rest use evaluate=False
            # so decidable pairings are checked too instead of discarded.
            evaluate = (rng.randrange(5) == 0)
            check_one(Contains, as_set_fn, elem_in, set_in, evaluate,
                      "fuzz", state)
    except Disagreement as d:
        print(str(d))
        print(json.dumps({"checked": state["checked"], "disagreements": 1,
                          "seed": SEED, "status": "fail"}))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py "
          "(solution_region: return self.region, over the MembershipAssertion "
          "carrier built from the real object's stored operands) == real "
          "patched Contains.as_set() BY OBJECT IDENTITY on %d assertions "
          "(%d boundary + fuzz, seed=%d); on every one the produced region is "
          "also the stored args[1] object, equals the region asserted, and is "
          "never the element component; the wrong-component shadow was caught "
          "on %d boundary inputs (anti-vacuity control); %d draws collapsed by "
          "Contains.eval and %d constructor-rejected were out of scope; "
          "0 disagreements."
          % (state["checked"], n_boundary, SEED, caught,
             state["collapsed"], state["rejected"]))
    print(json.dumps({
        "checked": state["checked"],
        "boundary": n_boundary,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl region of model.py)",
        "oracle": "sympy.sets.contains.Contains.as_set (called, gold-patched)",
        "comparison": "object identity (Ensures(Result() is self.region))",
        "out_of_scope": {"eval_collapsed": state["collapsed"],
                         "constructor_rejected": state["rejected"]},
        "anti_vacuity_caught": caught,
        "status": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
