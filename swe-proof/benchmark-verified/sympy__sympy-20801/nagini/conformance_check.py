#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20801 (nagini).

SHADOW -- the `# impl-start` / `# impl-end` region of `model.py`, copied
VERBATIM. On nagini the model IS Python, so nothing is transliterated: the body
of `float_equals` below is byte-for-byte model.py:105-119 with the contract
calls (`Requires`, `Ensures`, `MustTerminate`) deleted and nothing else touched
-- no reordering, no collapsing of the six single-`return` conditionals into a
membership test (a paraphrase would test the paraphrase, and here the whole
soundness content of the patch is the ORDER of those conditionals). The model's
`@Pure` helpers (`is_truth_value` / `is_irrational_const` / `is_numeric_kind` /
`is_other_kind`, model.py:46-70) are copied verbatim too; the impl region does
not call them, so they are used only to audit each real observation against the
model's Ensures clauses (an extra refutation channel, section (c) below).
model.py has an EMPTY axioms region (mapping.md §3: no `@ContractOnly` callee,
no consumed axiom), so there is no axiomatized callee to bridge, and no Nagini
carrier (`PSeq`/`ToSeq`) appears in the region -- the carrier is bool/int, so no
shim is needed. The region is directly executable: `conf_skip` stays false and
this gate carries full weight.

ORACLE -- the REAL patched repo function, CALLED, never reimplemented:
`sympy.core.numbers.Float.__eq__` (sympy/core/numbers.py:1383 at base_commit,
mapping.md §1). Every verdict compared below is the value of
`self.__eq__(other)` on real `Float` / real sympy operands. The gate applies the
gold patch to /testbed and sets PYTHONPATH before this runs; `_assert_patched()`
inspects the loaded source and REFUSES to report a verdict unless `if not self:`
really sits AFTER the `isinstance(other, Boolean)` test, so a green run cannot
come from unpatched code (at base_commit this script instead exits 1 on the
`S(0.0) == S.false` disagreement -- it is built to be able to fail). Contrast
the two siblings, which do transliterate: velvet's oracle is the real function
too, but lean's ORACLE is an in-process replica of the post-patch dispatch
(lean/conformance_check.py:46-61) because its shadow lives over 12 free boolean
observables. Nothing here is transliterated.

TYPE BRIDGE (mapping.md §2, inverted). The model works over four facets; the
real function wants `(Float, sympy object)`. Bridge DOWN is generation: real
operands are built first, then classified into the model's carrier by exactly
the facets the real dispatch reads --
  self:  Float             -> self_is_zero = (not self)
  other: sympy object      -> kind = 0 isinstance(other, Boolean);
                                     1 other.is_NumberSymbol and is_irrational;
                                     2 other.is_NumberSymbol, not irrational;
                                     3 other.is_Float; 4 other.is_Rational;
                                     5 other.is_Number; 6 otherwise
                              other_truthy = bool(other)
  the kind-proper numeric sub-decision -> numeric_eq, obtained by CALLING the
                              repo's own unchanged sub-decisions (kinds 2/4:
                              `other.__eq__(self)`; kind 3: `self._mpf_ ==
                              other._mpf_`; kind 5: `mlib.mpf_eq(self._mpf_,
                              other._as_mpf_val(self._prec))`) -- not by
                              recomputing equality independently.
Bridge UP is the identity (`bool` verdict -> `bool` verdict). Because `kind` is
produced by the classifier it is always in 0..6, so every generated input
satisfies `Requires(0 <= kind and kind <= 6)` by construction; `MustTerminate`
is discharged by the straight-line region itself. The `NotImplemented` path is
outside the modeled domain (mapping.md §2, last row) and is excluded by feeding
only already-sympified `Basic` operands -- a non-bool return is reported as an
out-of-domain error, never silently swallowed.

INPUTS. The modeled input space is FINITE: (self_is_zero, kind, other_truthy,
numeric_eq) = 2*7*2*2 = 56 abstract points, so this check enumerates the
ABSTRACT domain exhaustively -- every one of the 56 points is driven through the
shadow. That is strictly stronger than sampling the abstract domain. Only 24 of
the 56 are REALIZABLE by a real (Float, operand) pair, however, because the
facets are not independent: the classifier's kinds 0/1/6 always come with
numeric_eq False (numeric_decision returns False for them by construction), and
kind 1 can never have numeric_eq True anyway since pi/E/GoldenRatio never
satisfy the mpf compare. The differential leg cannot constrain the shadow at an
unrealizable point, so at all 56 points the shadow is additionally audited
against model.py's five Ensures clauses -- otherwise a shadow that returned
`numeric_eq` instead of False in the kind-0 branch would pass the differential
leg vacuously (verified: that mutation is caught only by this audit). On top of
the abstract sweep, and to reach the >= 1e5 count over REAL objects:
  (a) an exhaustive concrete matrix over the boundary corpus (every self Float x
      every operand, both kinds of truth value, both signs of zero, Float(.1,3)
      vs Float(.1,33), oo/-oo/nan, falsy non-numbers) -- includes the exact F2P
      shape `S(0.0) == S.false` and its three companions from the issue;
  (b) seeded fuzz drawing random Floats (mixed magnitude and precision, biased
      onto zero) against randomly generated operands of every kind, with a
      deliberate bias toward operands numerically EQUAL to self so the numeric
      branches are exercised with numeric_eq True as well as False;
  (c) for every observation, an audit that the real verdict also satisfies each
      of model.py's five Ensures clauses (via the verbatim `@Pure` helpers).
The run FAILS if any of the seven impl branches was never taken, if any of the
seven kinds was never observed, or if the discriminating witnesses are missing
(kind 0 with self_is_zero and a falsy operand -- the branch the gold patch
creates; kind 6 with self_is_zero and a falsy operand -- the relocated block's
only surviving effect, real witness `Float(0.0) == Tuple()` is True; and
numeric_eq both True and False on kinds 3 and 4). A generator that dodged the
relocated branch must not be able to report a green verdict.

Pinned seed: 20801 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + sympy only (container Python 3.9).
"""
import itertools
import json
import random
import sys

SEED = 20801
N_TARGET = 100000       # minimum Requires-satisfying observations
MAX_REPORT = 8


# ---------------------------------------------------------------------------
# SHADOW: model.py's pure helpers + impl region, verbatim, contracts stripped.
# ---------------------------------------------------------------------------

# model.py:46-70 (`# pure-start` .. `# pure-end`), verbatim minus @Pure.
def is_truth_value(kind: int) -> bool:
    """The operand is a symbolic logical truth value (kind 0)."""
    return kind == 0


def is_irrational_const(kind: int) -> bool:
    """The operand is an irrational named constant (kind 1)."""
    return kind == 1


def is_numeric_kind(kind: int) -> bool:
    """The operand is one of the numeric kinds whose verdict is the
    numeric-equality decision: a rational named constant, another floating
    value, a rational number, or any other number (kinds 2..5)."""
    return kind == 2 or kind == 3 or kind == 4 or kind == 5


def is_other_kind(kind: int) -> bool:
    """The operand is none of the above: neither a number nor a logical truth
    value (kind 6)."""
    return kind == 6


def float_equals(self_is_zero, kind, other_truthy, numeric_eq):
    # impl-start (model.py:105-119, verbatim; Requires/Ensures stripped)
    if kind == 0:
        return False
    if kind == 1:
        return False
    if kind == 2:
        return numeric_eq
    if kind == 3:
        return numeric_eq
    if kind == 4:
        return numeric_eq
    if kind == 5:
        return numeric_eq
    if self_is_zero:
        return not other_truthy
    return False
    # impl-end


# Nothing above was added to, removed from, or reordered within the copied
# region. Branch coverage is therefore observed from OUTSIDE, by tracing which
# line of the region executed (never by editing the region).
#
# The eight reachable returns of the region, by their offset from the `if
# kind == 0:` line (kept as offsets so no copied line is annotated).
_BRANCH_BY_OFFSET = {
    1: "kind0_boolean",         # return False        (kind == 0)
    3: "kind1_irrational",      # return False        (kind == 1)
    5: "kind2_numsym",          # return numeric_eq   (kind == 2)
    7: "kind3_float",           # return numeric_eq   (kind == 3)
    9: "kind4_rational",        # return numeric_eq   (kind == 4)
    11: "kind5_number",         # return numeric_eq   (kind == 5)
    13: "zero_fallthrough",     # return not other_truthy
    14: "tail_false",           # return False
}
_IMPL_FIRST_LINE = float_equals.__code__.co_firstlineno + 2   # `if kind == 0:`
_COVERED = set()


def _tracer(frame, event, arg):
    if event == "line" and frame.f_code is float_equals.__code__:
        _COVERED.add(frame.f_lineno - _IMPL_FIRST_LINE)
    return _tracer


def branch_coverage():
    hit = set(_BRANCH_BY_OFFSET[o] for o in _COVERED if o in _BRANCH_BY_OFFSET)
    return dict((b, (b in hit)) for b in _BRANCH_BY_OFFSET.values())


def shadow(self_is_zero, kind, other_truthy, numeric_eq, trace=False):
    """Run the verbatim region. `trace` records which branch it took."""
    if not trace:
        return float_equals(self_is_zero, kind, other_truthy, numeric_eq)
    sys.settrace(_tracer)
    try:
        return float_equals(self_is_zero, kind, other_truthy, numeric_eq)
    finally:
        sys.settrace(None)


# ---------------------------------------------------------------------------
# TYPE BRIDGE (mapping.md §2, inverted): real objects -> the model's carrier
# ---------------------------------------------------------------------------

def classify(other):
    """kind: read exactly the facets the real dispatch tests, in its order."""
    from sympy.logic.boolalg import Boolean
    if isinstance(other, Boolean):
        return 0
    if getattr(other, "is_NumberSymbol", False):
        if getattr(other, "is_irrational", False):
            return 1
        return 2
    if getattr(other, "is_Float", False):
        return 3
    if getattr(other, "is_Rational", False):
        return 4
    if getattr(other, "is_Number", False):
        return 5
    return 6


def numeric_decision(self_f, other, kind):
    """The kind-proper numeric sub-decision, obtained by CALLING the repo's own
    unchanged sub-decisions (mapping.md §2, row 4). Not an independent
    reimplementation of equality: kinds 2/4 delegate to the operand's own
    `__eq__`, kind 3 compares the repo's mpf tuples, kind 5 calls the repo's
    `_as_mpf_val` and mpmath's `mpf_eq` -- exactly the expressions the patched
    method evaluates."""
    import mpmath.libmp as mlib
    if kind == 2 or kind == 4:
        return bool(other.__eq__(self_f))
    if kind == 3:
        return self_f._mpf_ == other._mpf_
    if kind == 5:
        return bool(mlib.mpf_eq(self_f._mpf_, other._as_mpf_val(self_f._prec)))
    return False


def facets(self_f, other):
    """Bridge down: (Float, sympy object) -> the model's four facets."""
    kind = classify(other)
    return ((not self_f), kind, bool(other), numeric_decision(self_f, other, kind))


def oracle(self_f, other):
    """CALL the real patched Float.__eq__. -> bool, or ('OUT-OF-DOMAIN', v)."""
    v = self_f.__eq__(other)
    if v is True or v is False:
        return bool(v)
    return ("OUT-OF-DOMAIN", repr(v))


def _assert_patched():
    """Refuse to certify anything unless the loaded repo really is patched:
    `if not self:` must sit AFTER the Boolean test (that relocation IS the
    patch). Without this an unpatched container would look green wherever the
    fuzz missed the zero/boolean corner."""
    import inspect
    from sympy import Float
    src = inspect.getsource(Float.__eq__)
    for needle in ("if not self:", "isinstance(other, Boolean)", "other.is_Number:"):
        if needle not in src:
            raise SystemExit("G-CONF ERROR: Float.__eq__ source lacks %r; the "
                             "oracle would not be the modeled function" % needle)
    if src.index("if not self:") < src.index("isinstance(other, Boolean)"):
        raise SystemExit("G-CONF ERROR: Float.__eq__ is the PRE-patch source "
                         "(zero short circuit precedes the Boolean test); the "
                         "oracle must be the patched function")


# ---------------------------------------------------------------------------
# corpora
# ---------------------------------------------------------------------------

def operand_corpus():
    """Real, already-sympified operands spanning all seven kinds, with both
    truth values wherever the kind admits them."""
    from sympy import (S, Float, Integer, Rational, pi, E, GoldenRatio, Catalan,
                       EulerGamma, sqrt, Symbol, I, Tuple, oo, zoo, nan, Eq, Ne,
                       Lt, FiniteSet, Interval)
    from sympy.logic.boolalg import And, Or
    x, y = Symbol("x"), Symbol("y")
    return [
        # kind 0 -- symbolic truth values (Symbol is a Boolean subclass here):
        S.true, S.false, Eq(1, 1), Eq(1, 2), Ne(1, 1), Lt(2, 1),
        And(S.true, S.false), Or(S.false, S.false), x, y, And(x, y),
        # kind 1 -- irrational named constants:
        pi, E, GoldenRatio,
        # kind 2 -- NumberSymbols whose irrationality is unproven (delegate):
        Catalan, EulerGamma,
        # kind 3 -- other floating values (incl. both zeros, precision pairs):
        Float(0.0), Float(-0.0), Float(1.0), Float(2.0), Float(-3.5),
        Float("0.1", 3), Float("0.1", 33), Float(1e10), Float("1e-300"),
        # kind 4 -- rationals (Integer(0) is the falsy one):
        Integer(0), Integer(1), Integer(-3), Integer(10000000000),
        Rational(1, 2), Rational(-7, 3), Rational(4, 2),
        # kind 5 -- other numbers:
        oo, -oo, nan,
        # kind 6 -- neither number nor truth value (Tuple()/EmptySet are falsy):
        sqrt(2), I, zoo, Tuple(), Tuple(1, 2), S.EmptySet, FiniteSet(1),
        Interval(0, 1), x + 1, 2 * x,
    ]


def self_corpus():
    """Real Floats, including both zeros and several precisions."""
    from sympy import Float, S
    return [Float(0.0), Float(-0.0), Float("0.0", 3), S(0.0),
            Float(1.0), Float(2.0), Float(-3.5), Float("0.1", 3),
            Float("0.1", 33), Float(1e10), Float("1e-300"), Float(10000000000)]


def fuzz_self(rng, Float):
    k = rng.randrange(10)
    if k < 3:                                   # bias onto the zero float
        return Float(rng.choice([0.0, -0.0]), rng.choice([15, 3, 33, 53]))
    if k < 6:
        return Float(rng.uniform(-1e3, 1e3))
    if k < 8:
        return Float(rng.randint(-10 ** 6, 10 ** 6))
    return Float(rng.choice(["1e-300", "1e300", "0.1", "-0.5", "3"]),
                 rng.choice([3, 15, 33]))


def fuzz_operand(rng, self_f, mods):
    """A random operand of a random kind; with probability ~1/3 one that is
    numerically EQUAL to self_f, so the numeric branches see numeric_eq True."""
    S, Float, Integer, Rational = mods["S"], mods["Float"], mods["Integer"], mods["Rational"]
    k = rng.randrange(14)
    if k == 0:
        return rng.choice([S.true, S.false, mods["Eq"](1, 1), mods["Eq"](1, 2)])
    if k == 1:
        return rng.choice([mods["pi"], mods["E"], mods["GoldenRatio"]])
    if k == 2:
        return rng.choice([mods["Catalan"], mods["EulerGamma"]])
    if k in (3, 4):                             # equal-by-construction Float
        return Float(self_f, rng.choice([self_f._prec, 15, 33])) if rng.random() < 0.5 else self_f
    if k in (5, 6):
        return Float(rng.uniform(-10, 10), rng.choice([3, 15, 33]))
    if k == 7:                                  # rational equal to self, maybe
        try:
            return Rational(self_f)
        except Exception:
            return Integer(0)
    if k in (8, 9):
        return rng.choice([Integer(rng.randint(-5, 5)),
                           Rational(rng.randint(-9, 9), rng.randint(1, 9))])
    if k == 10:
        return rng.choice([mods["oo"], -mods["oo"], mods["nan"]])
    if k == 11:
        return rng.choice([mods["Tuple"](), S.EmptySet])         # falsy kind 6
    if k == 12:
        return rng.choice([mods["sqrt"](2), mods["I"], mods["zoo"],
                           mods["Tuple"](1, 2)])
    return rng.choice([mods["x"], mods["y"], mods["x"] + 1])     # kind 0 / 6


# ---------------------------------------------------------------------------
# differential driver
# ---------------------------------------------------------------------------

class Diff(object):
    def __init__(self):
        self.count = 0
        self.bad = []
        self.kinds = set()
        self.abstract = set()          # realized (self_is_zero, kind, truthy, neq)
        self.numeric_eq_seen = {}      # kind -> set of numeric_eq values

    def check(self, self_f, other):
        self_is_zero, kind, other_truthy, numeric_eq = facets(self_f, other)
        if not (0 <= kind <= 6):       # the model's Requires
            self.bad.append("bridge produced out-of-domain kind=%r for %r"
                            % (kind, other))
            return
        point = (bool(self_is_zero), kind, other_truthy, bool(numeric_eq))
        fresh = point not in self.abstract
        self.abstract.add(point)
        self.kinds.add(kind)
        self.numeric_eq_seen.setdefault(kind, set()).add(bool(numeric_eq))
        # trace only the first time each abstract point occurs: full branch
        # coverage, no tracing overhead on the fuzz bulk.
        got_shadow = shadow(self_is_zero, kind, other_truthy, numeric_eq,
                            trace=fresh)
        got_real = oracle(self_f, other)
        self.count += 1
        if got_shadow is not got_real:
            self.bad.append(
                "self=%r (prec=%s, self_is_zero=%s) other=%r (kind=%d, "
                "other_truthy=%s, numeric_eq=%s): shadow=%r real=%r"
                % (self_f, getattr(self_f, "_prec", "?"), self_is_zero, other,
                   kind, other_truthy, numeric_eq, got_shadow, got_real))
            return
        # (c) audit the real verdict against model.py's five Ensures clauses.
        r = got_real
        if is_truth_value(kind) and r is not False:
            self.bad.append("Ensures(truth_value -> False) violated by the real "
                            "function: self=%r other=%r real=%r" % (self_f, other, r))
        if is_irrational_const(kind) and r is not False:
            self.bad.append("Ensures(irrational_const -> False) violated: "
                            "self=%r other=%r real=%r" % (self_f, other, r))
        if is_numeric_kind(kind) and r != bool(numeric_eq):
            self.bad.append("Ensures(numeric -> numeric_eq) violated: self=%r "
                            "other=%r numeric_eq=%s real=%r"
                            % (self_f, other, numeric_eq, r))
        if is_other_kind(kind) and self_is_zero and r != (not other_truthy):
            self.bad.append("Ensures(other & zero -> not truthy) violated: "
                            "self=%r other=%r real=%r" % (self_f, other, r))
        if is_other_kind(kind) and not self_is_zero and r is not False:
            self.bad.append("Ensures(other & nonzero -> False) violated: "
                            "self=%r other=%r real=%r" % (self_f, other, r))


def main():
    try:
        import sympy                                            # noqa: F401
        from sympy import (S, Float, Integer, Rational, pi, E, GoldenRatio,
                           Catalan, EulerGamma, sqrt, Symbol, I, Tuple, oo,
                           zoo, nan, Eq)
    except Exception as e:
        print("G-CONF ERROR: sympy import failed: %r" % (e,))
        return 2
    _assert_patched()

    rng = random.Random(SEED)
    d = Diff()

    # -- (0) EXHAUSTIVE enumeration of the FINITE abstract domain -------------
    # 2 * 7 * 2 * 2 = 56 points, every one driven through the verbatim region.
    # Some abstract points are UNREALIZABLE by any real (Float, operand) pair --
    # e.g. kind 0 with numeric_eq True, since the classifier's kind-0 operands
    # are non-numbers for which numeric_decision returns False by construction.
    # The differential leg (a)/(b) therefore cannot constrain the shadow there,
    # so at every point the shadow is ALSO audited against model.py's five
    # Ensures clauses. Without this, a shadow that returned `numeric_eq` in the
    # kind-0 branch would pass the differential leg vacuously.
    n_abstract = 0
    for z, kind, t, neq in itertools.product([False, True], range(7),
                                             [False, True], [False, True]):
        v = shadow(z, kind, t, neq, trace=True)
        n_abstract += 1
        expected = None
        if is_truth_value(kind) or is_irrational_const(kind):
            expected = False
        elif is_numeric_kind(kind):
            expected = bool(neq)
        elif is_other_kind(kind):
            expected = (not t) if z else False
        if v is not expected:
            d.bad.append(
                "shadow violates model.py's Ensures at abstract point "
                "(self_is_zero=%s, kind=%d, other_truthy=%s, numeric_eq=%s): "
                "shadow=%r spec=%r" % (z, kind, t, neq, v, expected))

    # -- (a) exhaustive concrete matrix over the boundary corpora ------------
    selves = self_corpus()
    operands = operand_corpus()
    for s in selves:
        for o in operands:
            d.check(s, o)
    n_matrix = d.count

    # the four issue witnesses / the exact F2P shape, explicitly
    witnesses = [(S(0.0), S.false), (S(0.0), S.true), (Float(0.0), S.false),
                 (Float(-0.0), S.false), (Float(0.0), Tuple()),
                 (Float(0.0), S.EmptySet), (Float(0.0), Integer(0)),
                 (Float(0.0), Float(0.0))]
    for s, o in witnesses:
        d.check(s, o)
    if not ((S(0.0) == S.false) is False and (S.false == S(0.0)) is False
            and (S(0) == S.false) is False and (S.false == S(0)) is False):
        d.bad.append("the four issue witnesses do not hold on the real "
                     "patched repo (oracle is not the fixed function)")

    # -- (b) seeded fuzz over real objects to >= N_TARGET --------------------
    mods = {"S": S, "Float": Float, "Integer": Integer, "Rational": Rational,
            "pi": pi, "E": E, "GoldenRatio": GoldenRatio, "Catalan": Catalan,
            "EulerGamma": EulerGamma, "sqrt": sqrt, "I": I, "Tuple": Tuple,
            "oo": oo, "zoo": zoo, "nan": nan, "Eq": Eq,
            "x": Symbol("x"), "y": Symbol("y")}
    while d.count < N_TARGET:
        s = fuzz_self(rng, Float)
        try:
            o = fuzz_operand(rng, s, mods)
        except Exception as e:
            d.bad.append("operand generation failed: %r" % (e,))
            break
        d.check(s, o)
        if len(d.bad) >= MAX_REPORT:
            break
    n_fuzz = d.count - n_matrix

    # -- coverage obligations: a green verdict must have exercised the fix ---
    covered = branch_coverage()
    missed = [b for b, ok in sorted(covered.items()) if not ok]
    if missed:
        d.bad.append("impl branch(es) never executed: %s" % ", ".join(missed))
    missing_kinds = [k for k in range(7) if k not in d.kinds]
    if missing_kinds:
        d.bad.append("operand kind(s) never observed on the real function: %s"
                     % missing_kinds)
    required = {
        "kind0_zero_falsy_operand": (True, 0, False),   # S(0.0) == S.false
        "kind0_zero_truthy_operand": (True, 0, True),   # S(0.0) == S.true
        "kind6_zero_falsy_operand": (True, 6, False),   # Float(0.0) == Tuple()
        "kind6_zero_truthy_operand": (True, 6, True),
        "kind6_nonzero": (False, 6, True),
    }
    for label, (z, kind, t) in sorted(required.items()):
        if not any(p[0] == z and p[1] == kind and p[2] == t for p in d.abstract):
            d.bad.append("discriminating witness %s never generated (a green "
                         "verdict would certify nothing about it)" % label)
    for kind in (3, 4):
        if d.numeric_eq_seen.get(kind) != {False, True}:
            d.bad.append("kind %d never observed with both numeric_eq values "
                         "(saw %s)" % (kind, sorted(d.numeric_eq_seen.get(kind, []))))

    report = {
        "checked": d.count,
        "disagreements": len(d.bad),
        "seed": SEED,
        "abstract_domain_enumerated": n_abstract,
        "abstract_points_realized": len(d.abstract),
        "kinds": sorted(d.kinds),
        "branches": covered,
        "numeric_eq_observed": dict((str(k), sorted(v)) for k, v
                                    in sorted(d.numeric_eq_seen.items())),
        "shadow": "direct (contract-stripped impl region of model.py:105-119)",
        "oracle": ("called: sympy.core.numbers.Float.__eq__ "
                   "(sympy/core/numbers.py:1383, gold-patched)"),
    }
    if d.bad:
        print("G-CONF FAIL: %d disagreement(s) over %d Requires-satisfying "
              "inputs" % (len(d.bad), d.count))
        for line in d.bad[:MAX_REPORT]:
            print("  " + line)
        print(json.dumps(report, sort_keys=True))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py (float_equals) "
          "agrees with the REAL gold-patched Float.__eq__ on %d "
          "Requires-satisfying inputs (%d exhaustive boundary matrix + %d "
          "seeded fuzz, seed=%d); the finite abstract domain (%d points) was "
          "enumerated exhaustively, %d of them realized by real operands; "
          "kinds %s, all %d impl branches exercised; every observation also "
          "satisfies all five Ensures clauses; 0 disagreements."
          % (d.count, n_matrix, n_fuzz, SEED, n_abstract, len(d.abstract),
             sorted(d.kinds), len(covered)))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
