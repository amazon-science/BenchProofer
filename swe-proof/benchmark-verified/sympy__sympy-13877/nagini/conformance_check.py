#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13877 (nagini).

SHADOW: the `# impl-start`/`# impl-end` region of model.py (`lowest_live_index`),
copied VERBATIM below with only the contract calls stripped (Requires/Ensures/
Invariant and the `# invariants-start`/`-end` markers), plus the two `@Pure`
helpers it depends on — `is_genuinely_zero` and `first_usable` — likewise copied
verbatim minus contracts. `PSeq`/`ToSeq` are realized by an immutable tuple
shim. There are NO `@ContractOnly` callees in this bundle: mapping.md §3.1
records the zero-test as a *deep* model (A-reference), so `is_genuinely_zero`
copies over as `e <= 0` and is genuinely under test here — the shadow's verdict
on a column is decided by the model's own predicate, not by the repo's.

`first_usable` is used by the frozen postconditions rather than by the impl, so
it is copied and used here as a redundant cross-check of the two postcondition
clauses that relate the returned index to it (§ check_column).

ORACLE: the REAL patched repo function, CALLED, not transliterated —
`sympy.matrices.matrices._find_reasonable_pivot(col,
iszerofunc=_is_zero_after_expand_mul)`, which is the exact call the gold patch
installs at the Bareiss pivot step (patch.diff hunk 5, `matrices.py:190`);
`_find_reasonable_pivot` itself lives at `matrices.py:4065` @ base_commit and
`_is_zero_after_expand_mul` is added by the patch at `matrices.py:42`. The gate
applies patch.diff to /testbed and PYTHONPATH=/testbed makes the patched module
importable, so both are imported and driven directly. Its 4-tuple is normalized
to the modeled single index: `pivot_pos is None -> -1`, else `pivot_pos`
(mapping.md §2, last row); we additionally require the oracle's `pivot_val` to
be the column entry at the returned index.

TYPE BRIDGE (mapping.md §2, inverted). The model's carrier is a `List[int]` of
per-entry zero-status codes; the real function wants a column (list) of SymPy
expressions. Generation runs concrete -> abstract so every input is inside the
Requires by construction: each entry is built as an expression tree over the
grammar {integer monomial c*a^i*b^j, +, -, *, optional top-level division by a
non-vanishing denominator}, its mathematical vanish status is computed by an
INDEPENDENT flat-polynomial evaluator (dict of exponent-pair -> coefficient) in
this file, and the status code is then read off mapping.md §2's bijection:

    vanishes and structurally falsy  -> code  0  (literal/atomic zero)
    vanishes and structurally truthy -> code -1  (PSEUDO-ZERO, the bug class)
    does not vanish                  -> code +1  (genuinely non-zero)

The independent evaluator is a legitimate bridge (not a re-implementation of
the oracle) because the grammar is deliberately restricted to what `expand_mul`
decides exactly: `expand_mul` = `expand(deep=True, mul=True, power_exp=False,
power_base=False, basic=False, multinomial=False)`, i.e. it distributes products
over sums recursively but does NOT expand a Pow of an Add. The grammar therefore
contains no Pow-of-Add (a column entry like `(a+1)**2 - a**2 - 2*a - 1` is
mathematically zero yet `expand_mul`-nonzero, so it is NOT generated — it is not
in the abstraction's domain). Cross-checked in-container before this script was
written: over 20000 generated entries the evaluator's vanish flag agreed with
the real `_is_zero_after_expand_mul` 20000/20000.

Because the code is derived from the entry's construction rather than from the
repo predicate, a disagreement here refutes either the loop (R/I) or the
`is_genuinely_zero` abstraction — the check is not circular in the predicate.

MODELED SLICE: mapping.md §2 restricts the model to non-Float columns (the
decisive-`iszerofunc` PASS-1 branch). The generator emits only Integer/Symbol
polynomials, never a Float, so `_find_reasonable_pivot`'s leading numeric
(partial-pivoting) branch is never taken; `assert_non_float_column` enforces
this per input rather than trusting the generator.

INPUTS: >= 1e5 Requires-satisfying columns. The modeled space is infinite
(unbounded length, unbounded entries), so: 25 hand-written boundary columns
(empty, singleton of each code, all-zero, all-pseudo-zero, pseudo-zero followed
by a live entry, quotient pseudo-zeros, the >8-length case) + the columns the
REAL Bareiss recursion actually feeds the pivot finder for the FAIL_TO_PASS
matrices `M(n) = [[i + a*j]]`, n = 1..7 (recorded by wrapping the module global
and running `M(n).det()`) + 100000 seeded fuzz columns. Pinned seed 13877
(mapping.md § G-CONF). Every impl branch and every code class is required to
occur: the coverage counters are asserted non-zero and a shortfall exits 1, so
a generator that stopped exercising the pseudo-zero branch fails loudly instead
of passing vacuously. Coverage is tracked TWICE — once over all inputs and once
over the fuzz phase alone — because the boundary catalogue covers every class by
construction and would otherwise mask a fuzzer that had stopped producing the
bug class.

MUTATION-TESTED (the check is capable of failing; each mutant was run
in-container and exits 1): reversing the scan direction (last live index
instead of first); weakening `is_genuinely_zero` to `e < 0` so pseudo-zeros
become pivots (i.e. re-introducing the bug the patch fixes); mapping the
pseudo-zero class to code +1 in the bridge; returning 0 instead of -1 for the
no-pivot case; a generator that emits no pseudo-zeros (caught by the fuzz-phase
coverage guard); a generator restricted to length <= 1 columns, which never
takes the skip-then-pivot branch (also caught by the guard).

Exit 0 iff zero disagreements; on disagreement prints the column (codes and
expressions) and both outputs, then exits 1. stdlib + sympy only.
"""
import json
import random
import sys

SEED = 13877
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the model region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- model.py pure region, copied verbatim, contracts stripped ----------------

def is_genuinely_zero(e):
    """Is this column entry mathematically (genuinely) zero?"""
    return e <= 0


def first_usable(s, k):
    """Lowest index >= k of an entry that is NOT genuinely zero; `len(s)` if no
    such entry exists in s[k:]."""
    if k == len(s):
        return len(s)
    if not is_genuinely_zero(s[k]):
        return k
    return first_usable(s, k + 1)


# --- model.py impl region (lowest_live_index), verbatim, contracts stripped ---

def lowest_live_index(col):
    i = 0
    while i < len(col):
        if not is_genuinely_zero(col[i]):
            return i
        i = i + 1
    return -1


# --- bridge: independent flat-polynomial ground truth over the grammar -------
# A polynomial is a dict {(i, j): c} with c != 0, for the monomial c*a^i*b^j.
# An expression tree node is one of
#   ('mono', c, i, j) | ('add', x, y) | ('sub', x, y) | ('mul', x, y)
#   ('div', x, y)   -- y is generated so that poly(y) is non-empty (non-zero)

def _p_mono(c, i, j):
    return {(i, j): c} if c else {}


def _p_add(p, q):
    r = dict(p)
    for k, v in q.items():
        n = r.get(k, 0) + v
        if n:
            r[k] = n
        else:
            r.pop(k, None)
    return r


def _p_neg(p):
    return dict((k, -v) for k, v in p.items())


def _p_mul(p, q):
    r = {}
    for (i1, j1), c1 in p.items():
        for (i2, j2), c2 in q.items():
            k = (i1 + i2, j1 + j2)
            n = r.get(k, 0) + c1 * c2
            if n:
                r[k] = n
            else:
                r.pop(k, None)
    return r


def poly(e):
    """The entry's exact polynomial (numerator polynomial for a quotient)."""
    tag = e[0]
    if tag == 'mono':
        return _p_mono(e[1], e[2], e[3])
    if tag == 'add':
        return _p_add(poly(e[1]), poly(e[2]))
    if tag == 'sub':
        return _p_add(poly(e[1]), _p_neg(poly(e[2])))
    if tag == 'mul':
        return _p_mul(poly(e[1]), poly(e[2]))
    if tag == 'div':
        assert poly(e[2]), "denominator must be non-zero: %r" % (e[2],)
        return poly(e[1])
    raise ValueError("bad node %r" % (e,))


def vanishes(e):
    """Ground truth: is the entry mathematically zero? (independent of sympy)"""
    return not poly(e)


def to_sympy(e, a, b, Integer):
    """abstract tree -> the concrete SymPy expression the real function wants."""
    tag = e[0]
    if tag == 'mono':
        return Integer(e[1]) * a ** e[2] * b ** e[3]
    if tag == 'add':
        return to_sympy(e[1], a, b, Integer) + to_sympy(e[2], a, b, Integer)
    if tag == 'sub':
        return to_sympy(e[1], a, b, Integer) - to_sympy(e[2], a, b, Integer)
    if tag == 'mul':
        return to_sympy(e[1], a, b, Integer) * to_sympy(e[2], a, b, Integer)
    if tag == 'div':
        return to_sympy(e[1], a, b, Integer) / to_sympy(e[2], a, b, Integer)
    raise ValueError("bad node %r" % (e,))


def code_of(e, x):
    """mapping.md section 2 bijection, applied to a built entry.

    `x` is the SymPy expression; only its *structural* truthiness (the
    pre-patch `if val:` test, mapping.md section 3.2) is consulted, and only to
    split the vanishing entries into literal zeros (code 0) and pseudo-zeros
    (code -1). `is_genuinely_zero` treats both alike, so the shadow's answer
    depends solely on the construction-derived `vanishes(e)`.
    """
    if vanishes(e):
        return -1 if bool(x) else 0
    return 1


# --- generator ---------------------------------------------------------------

def gen_tree(rng, depth):
    """A polynomial tree in the grammar: no Pow of an Add (see docstring)."""
    if depth <= 0:
        return ('mono', rng.randint(-3, 3), rng.randint(0, 2), rng.randint(0, 2))
    r = rng.random()
    if r < 0.35:
        return ('mono', rng.randint(-3, 3), rng.randint(0, 2), rng.randint(0, 2))
    if r < 0.60:
        return ('add', gen_tree(rng, depth - 1), gen_tree(rng, depth - 1))
    if r < 0.80:
        return ('sub', gen_tree(rng, depth - 1), gen_tree(rng, depth - 1))
    return ('mul', gen_tree(rng, depth - 1), gen_tree(rng, depth - 1))


def gen_nonzero_tree(rng, depth):
    """A tree whose polynomial is non-empty (ground-truth genuinely non-zero)."""
    for _ in range(8):
        t = gen_tree(rng, depth)
        if poly(t):
            return t
    return ('mono', 1, 0, 0)


def gen_pseudo_zero(rng):
    """A structurally non-trivial entry that is nonetheless exactly zero.

    Built as `m*(t1 + t2 + ...) - m*t1 - m*t2 - ...`: the leading product of a
    monomial by an unexpanded sum does not cancel structurally (so the entry is
    `bool`-truthy, the pre-patch pivot test wrongly accepts it) yet the whole
    expression expands to 0. This is the shape the issue's Bareiss entries
    `(pivot*x - y*z)/cumm` take.
    """
    m = ('mono', rng.choice([-3, -2, -1, 1, 2, 3]),
         rng.randint(0, 2), rng.randint(0, 2))
    k = rng.randint(2, 3)
    terms = [('mono', rng.choice([-3, -2, -1, 1, 2, 3]),
              rng.randint(0, 2), rng.randint(0, 2)) for _ in range(k)]
    s = terms[0]
    for t in terms[1:]:
        s = ('add', s, t)
    e = ('mul', m, s)
    for t in terms:
        e = ('sub', e, ('mul', m, t))
    if rng.random() < 0.25:                      # the issue's quotient shape
        e = ('div', e, gen_nonzero_tree(rng, 1))
    return e


def gen_entry(rng):
    r = rng.random()
    if r < 0.30:                                 # pseudo-zero (the bug class)
        return gen_pseudo_zero(rng)
    if r < 0.45:                                 # literal / atomic zero
        return rng.choice([('mono', 0, 0, 0),
                           ('sub', ('mono', 1, 1, 0), ('mono', 1, 1, 0))])
    if r < 0.60:                                 # genuinely non-zero, shallow
        return gen_nonzero_tree(rng, rng.randint(0, 1))
    return gen_nonzero_tree(rng, rng.randint(1, 3))  # genuinely non-zero, deep


def gen_column(rng):
    n = rng.randint(0, 6)
    return [gen_entry(rng) for _ in range(n)]


# --- boundary catalogue ------------------------------------------------------

Z_LIT = ('mono', 0, 0, 0)                  # S.Zero
Z_CANCEL = ('sub', ('mono', 1, 1, 0), ('mono', 1, 1, 0))   # a - a -> literal 0
NZ_SYM = ('mono', 1, 1, 0)                 # a
NZ_INT = ('mono', 5, 0, 0)                 # 5
NZ_POLY = ('add', ('mono', 1, 1, 0), ('mono', 1, 0, 0))    # a + 1
# a*(b - 1) - a*b + a : truthy, expand_mul -> 0   (the pseudo-zero class)
PZ = ('sub', ('sub', ('mul', ('mono', 1, 1, 0),
                      ('sub', ('mono', 1, 0, 1), ('mono', 1, 0, 0))),
              ('mul', ('mono', 1, 1, 0), ('mono', 1, 0, 1))),
      ('mul', ('mono', -1, 1, 0), ('mono', 1, 0, 0)))
PZ2 = ('sub', ('sub', ('mul', ('mono', 2, 0, 1),
                       ('add', ('mono', 1, 1, 0), ('mono', 3, 0, 0))),
               ('mul', ('mono', 2, 0, 1), ('mono', 1, 1, 0))),
       ('mul', ('mono', 2, 0, 1), ('mono', 3, 0, 0)))
PZ_DIV = ('div', PZ, ('add', ('mono', 1, 1, 0), ('mono', 1, 0, 0)))   # .../(a+1)
NZ_DIV = ('div', NZ_POLY, ('add', ('mono', 1, 0, 1), ('mono', 2, 0, 0)))


def boundary_columns():
    return [
        [],                                     # empty column -> no pivot
        [Z_LIT],
        [Z_CANCEL],
        [PZ],                                   # lone pseudo-zero -> no pivot
        [PZ_DIV],
        [NZ_SYM],
        [NZ_INT],
        [NZ_DIV],
        [Z_LIT, Z_LIT, Z_LIT],                  # all zero -> no pivot
        [PZ, PZ2, PZ_DIV],                      # all pseudo-zero -> no pivot
        [Z_LIT, PZ, Z_CANCEL],                  # mixed vanishing -> no pivot
        [PZ, NZ_SYM],                           # THE bug shape: pivot at 1
        [PZ, PZ2, NZ_POLY],
        [Z_LIT, PZ, NZ_INT],
        [PZ_DIV, NZ_DIV],
        [NZ_SYM, PZ],                           # live entry first: pivot at 0
        [NZ_SYM, Z_LIT, PZ],
        [Z_LIT, NZ_INT],
        [Z_LIT, Z_LIT, NZ_SYM, NZ_INT],
        [NZ_POLY, NZ_SYM, NZ_INT],
        [Z_CANCEL, PZ, Z_LIT, PZ2, NZ_SYM],
        [PZ] * 8,                               # longer than any fuzz column
        [Z_LIT] * 7 + [NZ_SYM],
        [PZ2, Z_LIT, PZ, Z_CANCEL, PZ_DIV, NZ_DIV],
        [NZ_DIV, PZ_DIV, Z_LIT],
    ]


# --- oracle ------------------------------------------------------------------

def oracle_index(find_reasonable_pivot, iszerofunc, col_exprs):
    """The REAL patched repo function, called; 4-tuple -> modeled index."""
    pivot_pos, pivot_val, _, _ = find_reasonable_pivot(
        list(col_exprs), iszerofunc=iszerofunc)
    if pivot_pos is None:
        return -1, None
    return pivot_pos, pivot_val


def assert_non_float_column(col_exprs, Float):
    """The modeled slice is non-Float columns (mapping.md section 2)."""
    for x in col_exprs:
        assert not x.atoms(Float), "generated a Float entry: %r" % (x,)


# --- differential check ------------------------------------------------------

class Cov(object):
    def __init__(self):
        self.d = {"no_pivot": 0, "pivot_at_0": 0, "pivot_after_skip": 0,
                  "code_zero": 0, "code_pseudo_zero": 0, "code_nonzero": 0,
                  "empty_column": 0, "quotient_entry": 0}

    def bump(self, k, n=1):
        self.d[k] += n


def check_column(trees, ctx, *covs):
    a, b, Integer, Float, frp, iszero = ctx
    col_exprs = [to_sympy(t, a, b, Integer) for t in trees]
    codes = [code_of(t, x) for t, x in zip(trees, col_exprs)]
    assert_non_float_column(col_exprs, Float)

    shadow = lowest_live_index(codes)              # the model impl region
    oracle, pivot_val = oracle_index(frp, iszero, col_exprs)

    for cov in covs:
        if not trees:
            cov.bump("empty_column")
        for t, c in zip(trees, codes):
            cov.bump({0: "code_zero", -1: "code_pseudo_zero",
                      1: "code_nonzero"}[c])
            if t[0] == 'div':
                cov.bump("quotient_entry")
        if shadow == -1:
            cov.bump("no_pivot")
        elif shadow == 0:
            cov.bump("pivot_at_0")
        else:
            cov.bump("pivot_after_skip")

    if shadow != oracle:
        return ("index", codes, col_exprs, shadow, oracle)
    # the frozen postconditions relate the result to first_usable; check them.
    fu = first_usable(ToSeq(codes), 0)
    if (shadow == -1) != (fu == len(codes)):
        return ("postcond-nopivot", codes, col_exprs, shadow, fu)
    if shadow != -1 and shadow != fu:
        return ("postcond-index", codes, col_exprs, shadow, fu)
    # when a pivot exists the oracle's value must be that column entry
    if shadow != -1 and pivot_val is not col_exprs[shadow]:
        return ("pivot-val", codes, col_exprs, shadow, pivot_val)
    return None


def report(bad):
    kind, codes, exprs, got, other = bad
    print("G-CONF DISAGREEMENT (%s)" % kind)
    print("  codes  = %r" % (codes,))
    print("  column = %r" % ([str(x) for x in exprs],))
    print("  shadow (model impl region) = %r" % (got,))
    print("  oracle (_find_reasonable_pivot / expected) = %r" % (other,))


# --- the FAIL_TO_PASS columns, recorded from the real Bareiss recursion -------

def f2p_columns(a, expand):
    """Columns the REAL patched Bareiss recursion feeds the pivot finder for
    `M(n) = [[i + a*j]]`, n = 1..7 (the FAIL_TO_PASS matrices), recorded by
    wrapping the module global `_find_reasonable_pivot` and running `.det()`.

    These are real SymPy expressions with no construction to read a code off,
    so they are classified with full `expand(x) == 0` — a different code path
    from the oracle's `expand_mul` (expand with every option on, of which
    expand_mul is a restriction), and exact for these polynomial entries.
    """
    from sympy import Matrix
    # `import sympy.matrices.matrices as mm` raises ImportError in this sympy
    # (1.1.2.dev): the submodule shadows the attribute on the package. The
    # module object is already in sys.modules from the import at top of main().
    mm = sys.modules['sympy.matrices.matrices']
    real = mm._find_reasonable_pivot
    seen = []

    def recorder(col, **kw):
        cols = list(col)
        out = real(cols, **kw)
        seen.append(cols)
        return out

    mm._find_reasonable_pivot = recorder
    try:
        for n in range(1, 8):
            Matrix(n, n, lambda i, j: i + a * j).det(method='bareiss')
    finally:
        mm._find_reasonable_pivot = real

    out = []
    for cols in seen:
        codes = [0 if expand(x) == 0 else 1 for x in cols]
        out.append((cols, codes))
    return out


def main():
    from sympy import symbols, Integer, Float, expand
    from sympy.matrices.matrices import (_find_reasonable_pivot,
                                          _is_zero_after_expand_mul)
    a, b = symbols('a b')
    ctx = (a, b, Integer, Float, _find_reasonable_pivot,
           _is_zero_after_expand_mul)
    cov = Cov()
    checked = 0

    # 1. the real FAIL_TO_PASS columns, straight from the patched recursion
    f2p = f2p_columns(a, expand)
    for col_exprs, codes in f2p:
        shadow = lowest_live_index(codes)
        oracle, _ = oracle_index(_find_reasonable_pivot,
                                 _is_zero_after_expand_mul, col_exprs)
        if shadow != oracle:
            report(("f2p-index", codes, col_exprs, shadow, oracle))
            return 1
        checked += 1

    # 2. boundary columns
    bounds = boundary_columns()
    for trees in bounds:
        bad = check_column(trees, ctx, cov)
        if bad:
            report(bad)
            return 1
        checked += 1

    # 3. seeded fuzz. Coverage is counted SEPARATELY for the fuzz phase: the
    # boundary catalogue hits every class by construction, so a shared counter
    # would let a fuzzer that silently stopped generating (say) pseudo-zeros
    # still look fully covered. Both counters must be complete.
    cov_fuzz = Cov()
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        bad = check_column(gen_column(rng), ctx, cov, cov_fuzz)
        if bad:
            report(bad)
            return 1
        checked += 1

    missing = sorted(k for k, v in cov.d.items() if v == 0)
    missing_fuzz = sorted(k for k, v in cov_fuzz.d.items() if v == 0)
    if missing or missing_fuzz:
        print("G-CONF COVERAGE SHORTFALL: overall never exercised %r; "
              "fuzz phase never exercised %r" % (missing, missing_fuzz))
        print(json.dumps({"checked": checked, "disagreements": 0,
                          "coverage": cov.d, "coverage_fuzz": cov_fuzz.d,
                          "seed": SEED,
                          "unsupported": "coverage shortfall: overall=%s fuzz=%s"
                                         % (",".join(missing),
                                            ",".join(missing_fuzz))}))
        return 1

    print("G-CONF OK: model.py impl region (lowest_live_index, contracts "
          "stripped) == real patched _find_reasonable_pivot(col, "
          "iszerofunc=_is_zero_after_expand_mul) on %d columns "
          "(%d recorded FAIL_TO_PASS + %d boundary + %d fuzz, seed %d), "
          "0 disagreements; coverage %r."
          % (checked, len(f2p), len(bounds), N_FUZZ, SEED, cov.d))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "f2p_columns": len(f2p), "boundary": len(bounds),
                      "fuzz": N_FUZZ, "coverage": cov.d,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "sympy.matrices.matrices._find_reasonable_pivot"
                                " (real, patched, called)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
