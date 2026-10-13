#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-17318 (nagini).

SHADOW: the impl region of model.py (`match_additive`), copied verbatim below
with the contract calls (Requires/Ensures/Exsures) stripped. The @Pure fold
helpers (`code_fast_facet`, `code_is_surd`, `code_has_depth`, `all_fast_facet`,
`num_surds`, `any_has_depth`) copy over as plain functions; `PSeq` is realized
as an immutable tuple shim exposing the operations the folds use (len, index,
drop) and `ToSeq` lifts a plain list into it. The single @ContractOnly callee
`split_by_radicand_gcd` calls the REAL repo helper it models
(`sympy.simplify.radsimp.split_surds`, per mapping.md section 4.1) on the
expression currently under check, and wraps the helper's output so the shadow's
fast-path result is grounded in the modeled computation.

ORACLE: the REAL repo function the model models per mapping.md —
`sympy.simplify.sqrtdenest._sqrt_match`, the additive-expression branch. The
gate applies patch.diff to /testbed before this script runs; PYTHONPATH makes
the module importable. This script does NOT apply any patch itself.

Type bridge (mapping.md sections 2-3): each addend of a genuine multi-term
additive expression maps to an integer category code over two facets —
whether the addend's square is a positive rational (facet E, fast-path
eligible) and whether the addend carries a nested square root (facet N,
sqrt-depth at least one):

    0  facet E, no N      1  facet E, with N (a square-root term)
    2  not E, no N        3  not E, with N

The result abstraction (mapping.md section 2): the model's outcome
distinguishes (a) the SPLIT match — the fast path, whose value is pinned equal
to the splitting helper's own output, (b) the DEPTH match — marker 1, triple
contents deliberately unpinned, and (c) the empty match — the NoMatch
exception, standing in for the empty list the real matcher returns. The diff
therefore compares, per input:
    shadow NoMatch          <->  real matcher returns []
    shadow SPLIT outcome    <->  real matcher returns a non-empty match EQUAL
                                 to the real splitting helper's (a, b, r)
                                 output on the same expression (grounding)
    shadow DEPTH marker 1   <->  real matcher returns a non-empty match
                                 (contents not pinned by the spec)
Any exception escaping the real matcher on a Requires-satisfying input is a
disagreement.

Input domain (the model's Requires): len(codes) >= 2, every code in 0..3, and
the frame fact all_fast_facet(codes) => num_surds(codes) >= 1. Codes are
derived from REAL additive expressions by the same per-addend probes the guard
performs, so the first two hold by construction; the frame fact is asserted on
every generated expression (mapping.md section 3 states it holds for every
genuine multi-term sum, and axiom_check.py validates it) and inputs are
counted, never silently dropped.

>= 1e5 Requires-satisfying inputs: structured boundary expressions (every
branch: all-eligible sums with 1..5 square-root terms, shallow non-eligible
sums, nested sums, mixed sums) plus 100000 fuzz expressions built from pooled
addend kinds. Pinned fuzz seed: 173180.

Exit 0 iff zero disagreements; on disagreement prints the input expression,
its codes, and both outcomes, then exits 1. stdlib only (plain random).
"""
import random
import sys

SEED = 173180
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence with the operations the folds use ----------

class PSeqShim(object):
    __slots__ = ("_t",)

    def __init__(self, items):
        self._t = tuple(items)

    def drop(self, n):
        return PSeqShim(self._t[n:])

    def __getitem__(self, k):
        return self._t[k]

    def __len__(self):
        return len(self._t)


def ToSeq(xs):
    return PSeqShim(xs)


# --- pure helpers from model.py, verbatim, decorators/contracts stripped ------

def code_fast_facet(c):
    return c == 0 or c == 1


def code_is_surd(c):
    return c == 1


def code_has_depth(c):
    return c == 1 or c == 3


def all_fast_facet(s):
    if len(s) == 0:
        return True
    return code_fast_facet(s[0]) and all_fast_facet(s.drop(1))


def num_surds(s):
    if len(s) == 0:
        return 0
    return (1 if code_is_surd(s[0]) else 0) + num_surds(s.drop(1))


def any_has_depth(s):
    if len(s) == 0:
        return False
    return code_has_depth(s[0]) or any_has_depth(s.drop(1))


class NoMatch(Exception):
    """Model-side signal for the empty match (stands in for the empty list
    the real matcher returns)."""


class SplitOutcome(object):
    """The opaque SPLIT outcome the @ContractOnly callee produces: carries the
    real splitting helper's (a, b, r) output so the fast-path result is
    grounded in the modeled computation. Distinct from the depth marker 1."""

    def __init__(self, triple):
        self.triple = triple


# The expression the shadow is currently checking; the @ContractOnly callee
# reads it to invoke the real helper (the model passes only the abstract
# codes, so the concrete expression travels alongside).
_CURRENT_EXPR = [None]


def split_by_radicand_gcd(codes, k):
    """@ContractOnly callee: calls the REAL repo helper it models
    (split_surds) on the expression under check. Its modeled preconditions
    (all_fast_facet, k == num_surds, k >= 1) are asserted at the call site."""
    from sympy.simplify.radsimp import split_surds
    assert all_fast_facet(codes) and k == num_surds(codes) and k >= 1, (
        "shadow invoked the callee outside its modeled precondition")
    r, b, a = split_surds(_CURRENT_EXPR[0])
    return SplitOutcome([a, b, r])


# --- the impl region of model.py, verbatim (contract calls stripped) ----------

def match_additive(codes):
    if all_fast_facet(ToSeq(codes)):
        k = num_surds(ToSeq(codes))
        return split_by_radicand_gcd(ToSeq(codes), k)
    if not any_has_depth(ToSeq(codes)):
        raise NoMatch()
    return 1
    # impl-end (verbatim copy ends here)


# --- bridge: real addends <-> model category codes -----------------------------

def make_probes():
    """Per-addend facet probes, mirroring the guard's own tests (the same
    classification axiom_check.py uses)."""
    from sympy.simplify.sqrtdenest import sqrt_depth

    def addend_code(x):
        sq = x ** 2
        pos_rat = bool(sq.is_Rational) and bool(sq.is_positive)
        depth = sqrt_depth(x) >= 1
        if pos_rat:
            return 1 if depth else 0
        return 3 if depth else 2

    return addend_code


def shadow_outcome(p, codes):
    """Run the contract-stripped impl on the codes; canonicalize the result:
    ('EMPTY',) / ('MATCH', grounded triple) / ('MATCH', None) for the depth
    marker whose triple contents the spec does not pin."""
    _CURRENT_EXPR[0] = p
    try:
        r = match_additive(list(codes))
    except NoMatch:
        return ("EMPTY", None)
    if isinstance(r, SplitOutcome):
        return ("MATCH", r.triple)
    assert r == 1, "impl produced an unexpected marker: %r" % (r,)
    return ("MATCH", None)


def real_outcome(sqrt_match, p):
    """Run the REAL matcher; canonicalize. Any exception is reported as a
    disagreement by the caller."""
    try:
        m = sqrt_match(p)
    except Exception as e:
        return ("RAISED", "%s: %s" % (type(e).__name__, e))
    if m == []:
        return ("EMPTY", None)
    if not (isinstance(m, list) and len(m) == 3):
        return ("ODD-SHAPE", m)
    return ("MATCH", m)


def outcomes_agree(shadow, real):
    if shadow[0] != real[0]:
        return False
    if shadow[0] == "MATCH" and shadow[1] is not None:
        # fast path: the result is pinned equal to the helper's own output
        return list(real[1]) == list(shadow[1])
    return True


def check_one(sqrt_match, addend_code, p):
    """Diff shadow vs real on one prepared additive expression. Returns an
    error string on disagreement, None on agreement, and the string 'SKIP'
    when the expression falls outside the modeled shape."""
    codes = [addend_code(x) for x in p.args]
    if len(codes) < 2:
        return "SKIP"
    # the model's frame fact: an all-eligible genuine multi-term sum always
    # contains at least one square-root term (mapping.md section 3)
    if all(c in (0, 1) for c in codes) and sum(1 for c in codes if c == 1) == 0:
        return ("FRAME-FACT VIOLATION (input outside Requires)\n  p=%r codes=%r"
                % (p, codes))
    shadow = shadow_outcome(p, codes)
    real = real_outcome(sqrt_match, p)
    if not outcomes_agree(shadow, real):
        return ("DISAGREEMENT\n  p=%r\n  codes=%r\n  shadow=%r\n  real=%r"
                % (p, codes, shadow, real))
    return None


# --- input generation ----------------------------------------------------------

def build_pools():
    from sympy import sqrt, I, Rational, pi

    rationals = [1, 2, 3, 4, 7, Rational(1, 2), Rational(5, 3),
                 Rational(-3, 4), -2, -5]
    surds = [sqrt(2), sqrt(3), sqrt(5), 2 * sqrt(2), 3 * sqrt(5),
             sqrt(6), sqrt(7), sqrt(10), sqrt(15), -sqrt(2), -2 * sqrt(3),
             sqrt(5) / 7, Rational(2, 3) * sqrt(7)]
    imag = [I, 2 * I, -I, Rational(1, 3) * I, 3 * I]
    imag_surds = [I * sqrt(2), -I * sqrt(3), 2 * I * sqrt(5)]
    other_shallow = [pi, 2 * pi, -pi, 2 ** Rational(1, 3)]
    nested = [sqrt(1 + sqrt(2)), sqrt(5 + 2 * sqrt(6)),
              2 * sqrt(1 + sqrt(5)), -sqrt(3 + sqrt(7))]
    return {
        "rat": rationals, "surd": surds, "imag": imag,
        "imag_surd": imag_surds, "other": other_shallow, "nested": nested,
    }


def boundary_exprs():
    from sympy import sqrt, I, Rational
    from sympy.core.function import _mexpand

    exprs = [
        # shallow sums with a non-eligible addend -> the empty match
        4 + I, 3 + 2 * I, I + Rational(5, 3), 7 + I,
        I + 2 * I * 3 + 5,  # collapses; filtered if not a multi-term sum
        # all-eligible sums with 1..5 square-root terms -> the SPLIT match
        3 + sqrt(2),
        1 + sqrt(2) + sqrt(3),
        2 + 3 * sqrt(5),
        sqrt(2) + sqrt(3) + sqrt(6),
        3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15),
        Rational(1, 2) + sqrt(7),
        4 + sqrt(2) + sqrt(8) + sqrt(18),
        1 + sqrt(2) + sqrt(2) * sqrt(3),
        -3 + sqrt(2),
        Rational(-1, 2) - sqrt(3) + sqrt(5),
        # mixed sums with a nested / non-eligible deep addend -> DEPTH match
        sqrt(2) + I,
        sqrt(3) + I * sqrt(2),
        3 + I * sqrt(2),
        sqrt(2) + sqrt(3) + I,
        5 * sqrt(2) + 2 * I * sqrt(2),
        I * sqrt(2) + I * sqrt(3),
        sqrt(1 + sqrt(2)) + I,
        sqrt(1 + sqrt(2)) + sqrt(3) + I,
        1 + sqrt(2) + 2 * sqrt(1 + sqrt(5)),
        sqrt(5 + 2 * sqrt(6)) + 4,
        sqrt(5 + 2 * sqrt(6)) + sqrt(2) + 1,
    ]
    out = []
    for p in exprs:
        p = _mexpand(p)
        if getattr(p, "is_Add", False) and len(p.args) >= 2:
            out.append(p)
    return out


def fuzz_exprs(rng, pools, n):
    """Yield up to n prepared multi-term additive expressions. Kind weights
    keep every branch populated (all-eligible, shallow non-eligible, nested)."""
    from sympy import Add
    from sympy.core.function import _mexpand

    kinds_all = ("rat", "surd", "imag", "imag_surd", "other", "nested")
    produced = 0
    while produced < n:
        regime = rng.random()
        nterms = rng.randint(2, 5)
        if regime < 0.4:
            # all-eligible regime: rationals + real surds only
            terms = [rng.choice(pools[rng.choice(("rat", "surd", "surd"))])
                     for _ in range(nterms)]
        elif regime < 0.7:
            # shallow regime: rationals + imaginary/other shallow addends
            terms = [rng.choice(pools[rng.choice(("rat", "imag", "other"))])
                     for _ in range(nterms)]
        else:
            # mixed regime: anything
            terms = [rng.choice(pools[rng.choice(kinds_all)])
                     for _ in range(nterms)]
        p = _mexpand(Add(*terms))
        if not (getattr(p, "is_Add", False) and len(p.args) >= 2):
            continue
        produced += 1
        yield p


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    from sympy.simplify.sqrtdenest import _sqrt_match

    addend_code = make_probes()
    checked = 0
    n_boundary = 0

    for p in boundary_exprs():
        err = check_one(_sqrt_match, addend_code, p)
        if err == "SKIP":
            continue
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    pools = build_pools()
    for p in fuzz_exprs(rng, pools, N_FUZZ):
        err = check_one(_sqrt_match, addend_code, p)
        if err == "SKIP":
            continue
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real additive matcher on %d inputs "
          "(%d boundary + %d fuzz, seed %d); fast-path results grounded in "
          "the real splitting helper's output."
          % (checked, n_boundary, checked - n_boundary, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
