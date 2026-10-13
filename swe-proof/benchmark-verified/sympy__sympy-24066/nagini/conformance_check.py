#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24066 (nagini).

SHADOW  — the impl region of model.py copied VERBATIM with the contract
          statement lines (Requires/Ensures/Invariant/Assert) stripped; the
          model IS Python, so no transliteration.  The @Pure helpers
          (CANON_ONE / all_resolvable / canon_dim / canon_seq) copy over as
          plain functions; PSeq becomes a small tuple-backed shim.  The two
          @ContractOnly axioms call the REAL repo callee through the bridge:
          `is_dimensionless(code)` invokes the genuine dimension system's
          dimensionless test on the dimension the code denotes, and
          `resolvable(code)` is its real domain (the test returns a verdict
          rather than raising).

BRIDGE  — mapping.md §2's type abstraction: a dimension is abstracted by an
          integer code, injectively (distinct dimension values <-> distinct
          ints; structural dimension equality <-> int equality), with the
          canonical dimensionless dimension (name == 1) <-> the distinguished
          code CANON_ONE() == 1.  The script builds a concrete code table:
          for each code, an argument EXPRESSION whose collected dimension is
          that code's dimension (quantities, products, powers, plain numbers
          — never an applied function, so producing the table never exercises
          the behaviour under test), and the dimension itself as collected
          once from that expression.  Injectivity of the table is asserted
          (pairwise structural inequality).  The table spans the three
          regimes the model distinguishes: the canonical dimensionless
          dimension, non-canonical dimensionless dimensions (net powers
          cancel but the form is not the canonical one), and genuine
          dimensions — all inside the modeled `resolvable` domain, which is
          re-checked against the real callee per code.

ORACLE  — the REAL patched repo behaviour (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs): the applied-function
          branch of `UnitSystem._collect_factor_and_dimension` (mapping.md
          §1), driven end-to-end by collecting `g(arg_1, ..., arg_n)` for an
          undefined function symbol g, where arg_k is the table expression
          for the k-th input code.  The observable is the tail of the
          returned tuple — the per-argument dimensions.  The shadow runs the
          model's loop over the code list and maps the resulting codes back
          to dimensions through the same table; any argument for which the
          patched branch reports a different dimension than the model
          resolves is a disagreement.  The shadow's loop is additionally
          cross-checked against the pure-region fold (canon_seq) on every
          input, pinning the impl region and the deep model to each other.

Exit 0 iff zero disagreements over the boundary cases + >=1e5 fuzzed
Requires-satisfying inputs (every code resolvable — the modeled domain).
Pinned seed: 24066.  stdlib + sympy (the repo under test) only.
"""
import random
import sys

SEED = 24066
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# PSeq shim: the model's persistent-sequence carrier as a plain tuple wrapper.
# ---------------------------------------------------------------------------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *elems):
        self._t = tuple(elems)

    @classmethod
    def _of(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def take(self, n):
        return PSeq._of(self._t[:n])

    def drop(self, n):
        return PSeq._of(self._t[n:])

    def __add__(self, other):
        return PSeq._of(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(xs):
    return PSeq._of(xs)


# ---------------------------------------------------------------------------
# Bridged axioms (@Pure @ContractOnly in the model): call the REAL repo
# callee on the dimension the code denotes.  Bound in main() once the code
# table exists.
# ---------------------------------------------------------------------------

_CODE2DIM = {}
_REAL_IS_DIMENSIONLESS = None


def resolvable(code):
    """Real meaning of the model's opaque domain predicate: the dimensionless
    test returns a verdict on this code's dimension (does not raise)."""
    try:
        _REAL_IS_DIMENSIONLESS(_CODE2DIM[code])
        return True
    except Exception:
        return False


def is_dimensionless(code):
    """The REAL dimension system's dimensionless test, through the bridge."""
    return _REAL_IS_DIMENSIONLESS(_CODE2DIM[code])


# ---------------------------------------------------------------------------
# model.py pure region, copied as plain functions (@Pure/Requires stripped).
# ---------------------------------------------------------------------------

def CANON_ONE():
    return 1


def all_resolvable(s):
    if len(s) == 0:
        return True
    return resolvable(s[0]) and all_resolvable(s.drop(1))


def canon_dim(code):
    if is_dimensionless(code):
        return CANON_ONE()
    return code


def canon_seq(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(canon_dim(s[0])) + canon_seq(s.drop(1))


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------

def collect_argument_dimensions(arg_dims):
    result = []  # type: list
    i = len(arg_dims)
    while i > 0:
        c = arg_dims[i - 1]
        if is_dimensionless(c):
            result = [CANON_ONE()] + result
        else:
            result = [c] + result
        i = i - 1
    return result


# ---------------------------------------------------------------------------
# Input generation: Requires-satisfying = every code in the modeled table
# (all resolvable; re-asserted against the real callee at setup).
# ---------------------------------------------------------------------------

def boundary_cases(codes, canon_codes, noncanon_dimless, genuine):
    yield []                                        # no arguments
    for c in codes:
        yield [c]                                   # each regime singly
    yield list(canon_codes)                         # all canonical
    yield list(noncanon_dimless)                    # all non-canonical dimless
    yield list(genuine)                             # all genuine
    yield list(noncanon_dimless) + list(genuine)    # mixed regimes
    yield list(genuine) + list(noncanon_dimless)
    if noncanon_dimless:
        c = noncanon_dimless[0]
        yield [c, c, c]                             # repeats
        yield [c] + list(genuine) + [c]             # interleaved
    yield list(codes)                               # the whole table
    yield list(reversed(codes))


def gen_case(rng, codes):
    n = rng.randint(0, 6)
    return [rng.choice(codes) for _ in range(n)]


def main():
    global _REAL_IS_DIMENSIONLESS
    from sympy import S, Function
    from sympy.physics.units import (
        impedance, capacitance, time, ohm, farad, second,
        length, mass, meter, kilogram, current, ampere)
    from sympy.physics.units.quantities import Quantity
    from sympy.physics.units.dimensions import Dimension
    from sympy.physics.units.systems.si import SI

    dimsys = SI.get_dimension_system()
    _REAL_IS_DIMENSIONLESS = dimsys.is_dimensionless
    collect = SI._collect_factor_and_dimension

    # ---- quantities used to build argument expressions -----------------------
    R = Quantity('R_conf')
    C = Quantity('C_conf')
    T = Quantity('T_conf')
    L = Quantity('L_conf')
    M = Quantity('M_conf')
    I = Quantity('I_conf')
    for q, d, u in ((R, impedance, ohm), (C, capacitance, farad),
                    (T, time, second), (L, length, meter),
                    (M, mass, kilogram), (I, current, ampere)):
        SI.set_quantity_dimension(q, d)
        q.set_global_relative_scale_factor(1, u)

    # ---- code table: code -> (argument expression, its collected dimension) --
    # The expression is what an applied function receives as one argument; its
    # dimension (collected once, outside any function application) is the
    # dimension the code denotes.  code 1 is the canonical dimensionless
    # dimension, matching CANON_ONE() == 1 in the model.
    arg_exprs = {
        1: S(2),                    # a plain number: canonical dimensionless
        2: T / (R * C),             # dimensionless, non-canonical form
        3: (T / (R * C)) ** 2,      # another non-canonical dimensionless form
        4: R * C / T,               # the reciprocal, also dimensionless
        5: L,                       # genuine dimensions from here on
        6: M,
        7: T,
        8: I,
        9: L * M,
        10: L / T,
        11: L ** 2,
        12: M * T / L,
        13: R,
        14: C,
    }
    canon_codes = (1,)
    noncanon_dimless = (2, 3, 4)
    genuine = tuple(c for c in arg_exprs if c not in (1, 2, 3, 4))

    for code, e in arg_exprs.items():
        _CODE2DIM[code] = collect(e)[1]

    # sanity: the bridge is injective (distinct codes <-> structurally
    # distinct dimensions) and lands in the intended regimes, all resolvable.
    codes = sorted(arg_exprs)
    for a_i, a in enumerate(codes):
        for b in codes[a_i + 1:]:
            assert _CODE2DIM[a] != _CODE2DIM[b], (
                "code table not injective: %d and %d share dimension %r"
                % (a, b, _CODE2DIM[a]))
    assert _CODE2DIM[1] == Dimension(1), \
        "code 1 must denote the canonical dimensionless dimension"
    for c in codes:
        assert resolvable(c), "code %d must be in the modeled domain" % c
    for c in canon_codes + noncanon_dimless:
        assert is_dimensionless(c) is True, \
            "code %d must denote a dimensionless dimension" % c
    for c in noncanon_dimless:
        assert _CODE2DIM[c] != Dimension(1), (
            "code %d must denote a NON-canonical dimensionless dimension" % c)
    for c in genuine:
        assert is_dimensionless(c) is False, \
            "code %d must denote a genuine dimension" % c

    g = Function('g_conf')

    def oracle_dims(case):
        """The REAL patched branch: collect an applied function over the
        case's argument expressions; the tuple tail is the per-argument
        dimensions it reports."""
        res = collect(g(*[arg_exprs[c] for c in case]))
        return list(res[1:])

    rng = random.Random(SEED)
    checked = 0
    disagreements = []

    def check(case, tag):
        nonlocal checked
        checked += 1
        shadow_codes = collect_argument_dimensions(list(case))
        # impl region vs pure-region fold (internal cross-check)
        fold = canon_seq(ToSeq(case))
        if ToSeq(shadow_codes) != fold:
            disagreements.append((tag + "/fold", case, shadow_codes,
                                  list(fold._t)))
            return len(disagreements) < 5
        shadow_dims = [_CODE2DIM[c] for c in shadow_codes]
        real_dims = oracle_dims(case)
        if len(shadow_dims) != len(real_dims) or any(
                s != r for s, r in zip(shadow_dims, real_dims)):
            disagreements.append((tag, case, shadow_dims, real_dims))
        return len(disagreements) < 5

    for case in boundary_cases(codes, canon_codes, noncanon_dimless, genuine):
        if not check(case, "boundary"):
            break

    if not disagreements:
        for _ in range(N_FUZZ):
            if not check(gen_case(rng, codes), "fuzz"):
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for tag, case, sh, orc in disagreements:
            print("  [%s] codes=%r args=%r\n    shadow=%r\n    oracle=%r"
                  % (tag, case, [arg_exprs[c] for c in case], sh, orc))
        return 1
    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "per-argument dimension reporting of an applied function on %d "
          "inputs across %d dimension codes (canonical / non-canonical "
          "dimensionless / genuine), seed=%d, 0 disagreements."
          % (checked, len(codes), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
