#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12419 (nagini).

Refutes (never proves) the refinement leg no other gate covers: does the MODEL
in model.py agree with the REAL patched repository function it claims to model?

SHADOW
------
The impl region of `model.py` (`diagonal_unit_entry`, lines between
`# impl-start` / `# impl-end`), copied VERBATIM below as `shadow_entry`. The
model IS Python, so nothing is transliterated; the only deletions are the
contract calls, and the region contains none inside the markers (the
`Requires(MustTerminate(2))` / `Ensures(...)` lines live in the
`pre-conditions` / `post-conditions` regions above it and are stripped). The
region is three statements and they are reproduced statement-for-statement,
including the `elif` and the fall-through `return DEFERRED`:

    e = eq_class(i, j)
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED

The `# pure-start` region is empty (no `@Pure` deep-model helper to copy over),
and no Nagini carrier appears in the signature (`i`, `j`, and the result are
plain `int`), so no `PSeq`/`ToSeq` shim is needed here.

`eq_class` is `@ContractOnly` — it has no body to copy, so the shadow calls the
REAL repo callee it axiomatizes (mapping.md §1/§3.1: `Eq(i, j)` read through the
`is S.true` / `is S.false` identity tests, `sympy.core.relational.Equality.eval`,
`sympy/core/relational.py:284`). The axiom is therefore EXERCISED, not assumed:
`real_eq_class` below is the only thing standing where the axiom stood, and a
pair the axiom mis-describes shows up as a disagreement. `struct_eq` (the other
`@ContractOnly` callee) is not called from this impl region — it is consumed only
by the pre-image twin's proof — so it has no shadow obligation here; its
soundness is G-AX's job (axiom_check.py).

ORACLE
------
The REAL patched repo function, CALLED, not transliterated:
`Identity._entry(self, i, j)` — `sympy/matrices/expressions/matexpr.py:478` at
base_commit `479939f8c65c` (mapping.md §1). The gate applies `patch.diff` to
/testbed and sets PYTHONPATH before this script runs, so the `_entry` reached
here is the post-gold three-way branch; this script applies no patch itself and
reimplements nothing. Driving it needs only `Identity(n)` for a symbolic `n`,
which is buildable in-container, so there is no excuse for a replica. Each
boundary pair is additionally cross-checked through the public accessor
`Identity(n)[i, j]` (`MatrixExpr.__getitem__` → `_entry`), the exact path the
sole FAIL_TO_PASS `test_Identity` observes. `__getitem__` runs its own UNCHANGED
bounds validation (matexpr.py:244) upstream of the modeled decision and raises
`IndexError` for indices it cannot place in range (e.g. a negative-assumption
symbol); those are skipped and counted on that secondary leg only — the modeled
function itself was already compared through `_entry` directly for every input,
so nothing is waved through.

Sanity-pinned at startup: the oracle module's `_entry` source must contain the
post-patch `Eq(` / `KroneckerDelta(` tokens. If the gate ever forgets to apply
the gold patch, this check would otherwise silently compare against pre-patch
code and "pass" its own tag inversion; instead it exits 1.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
The model works over opaque `int` identity tags and returns a 3-valued cell
TAG; the real function takes SymPy `Expr` index expressions and returns a SymPy
cell VALUE. Both directions are written out explicitly and both are checked:

  * inputs — index expression `Expr` ↔ opaque `int` tag: the model never does
    arithmetic on `i`/`j`, it only feeds them to the equality callee, so the
    bridge is "generate the concrete `Expr` and pass the SAME object to both
    sides". Generating in the concrete direction is what keeps every input
    inside the model's `Requires` (which is `MustTerminate(2)` only — a
    permission/termination obligation with no data constraint, so EVERY index
    pair satisfies it and none has to be filtered out).
  * eq verdict — `Eq(i,j) is S.true` ↔ `EQ_TRUE`, `is S.false` ↔ `EQ_FALSE`,
    unevaluated `Equality` ↔ `EQ_UNKNOWN` (`real_eq_class`).
  * result, oracle → model (`tag_of_value`, the primary comparison): `S.One` ↔
    `ONE`, `S.Zero` ↔ `ZERO`, a `KroneckerDelta` instance ↔ `DEFERRED`. Any
    other returned object is unmappable and reported as a disagreement rather
    than silently bucketed.
  * result, model → oracle (`value_of_tag`, the redundant second leg): `ONE` ↔
    `S.One`, `ZERO` ↔ `S.Zero`, `DEFERRED` ↔ the REAL `KroneckerDelta(i, j)`,
    compared to the oracle's value under `Basic.__eq__` — the same structural
    equality `test_Identity`'s `In[i, j] != 0` rests on.

Because `KroneckerDelta(i, j)` evaluates to `1`/`0` on DECIDED pairs, the
`DEFERRED` tag is only observably distinct from `ONE`/`ZERO` if it is never
reached on such a pair. That is mapping.md §2's claim ("a value distinct from
both ONE and ZERO"), and it is not assumed: on every `EQ_UNKNOWN` input the
check asserts the real `KroneckerDelta(i, j)` is neither `S.One` nor `S.Zero`
(`degenerate` counter). A collapse there would make the bridge non-injective
and is reported as a failure, not tolerated.

WHY THIS CAN FAIL
-----------------
The discriminating branch is the third one. On an undecided pair the shadow
yields `DEFERRED` while pre-patch `_entry` yields `S.Zero` → tag `ZERO`, so
running this script WITHOUT the gold patch applied makes it exit 1 on the very
first boundary case `(i, j)`. That negative control was run: pre-patch it
reports the `(i, j)` disagreement, post-patch it is clean. The input generator
is built around that branch rather than avoiding it — the undecided class is the
majority of the corpus (see the printed per-class counts), so the behaviour
under specification is exercised, not routed around.

INPUTS
------
The model's `Requires` constrains nothing, so the satisfying domain is every
index pair; the ABSTRACT input space, however, is finite: the modeled decision
reads only the 3-valued verdict, and all three classes are enumerated
exhaustively with concrete witnesses in the boundary block (so every branch of
the impl — `EQ_TRUE`, `EQ_FALSE`, `EQ_UNKNOWN` — is taken, each many times,
and the F2P shape `(i, j)` is pinned first). The CONCRETE space is infinite, so
on top of that: an exhaustive ordered sweep of a hand-built 34-expression
boundary pool (34² = 1156 pairs: bare symbols with assorted assumptions,
integer literals of both signs and zero, and symbol arithmetic `i±1`, `2*i`,
`i+j`, `i*j`, `i**2`, `-i`, `5-i`, `floor(i/2)`, `Abs(i)`), then seeded fuzz
over randomly built integer index expressions to fill the count.

Total inputs: 1156 boundary + 100000 fuzz = 101156 ≥ 1e5, each checked on both
bridge legs. Pinned seed: 12419 (module constant `SEED`, recorded in mapping.md
§G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + sympy (the repo under test) only.
"""
import itertools
import random
import sys

SEED = 12419
N_FUZZ = 100_000
BOUNDARY_POOL_MAX = 34   # boundary sweep is BOUNDARY_POOL_MAX ** 2 ordered pairs
FUZZ_CORPUS = 500        # distinct random index expressions the fuzz draws from
DISAGREE_CAP = 5


# --- model.py constants, verbatim -------------------------------------------
EQ_FALSE = 0    # the two indices are provably unequal
EQ_TRUE = 1     # the two indices are provably equal
EQ_UNKNOWN = 2  # equality of the two indices is undecided

ZERO = 10       # the zero cell value
ONE = 11        # the unit cell value
DEFERRED = 12   # the deferred symbolic cell value

TAG_NAME = {ZERO: "ZERO", ONE: "ONE", DEFERRED: "DEFERRED", None: "UNMAPPABLE"}
CLASS_NAME = {EQ_FALSE: "EQ_FALSE", EQ_TRUE: "EQ_TRUE", EQ_UNKNOWN: "EQ_UNKNOWN"}


# --- the @ContractOnly callee, bound to the REAL repo callee ----------------
def real_eq_class(i, j, Eq, S):
    """model.py's `eq_class` axiom, executed as the REAL unchanged callee it
    axiomatizes: `Eq(i, j)` read through the `is S.true` / `is S.false` identity
    tests (mapping.md §3.1). No model, no replica — this is the library call the
    patched `_entry` itself makes."""
    eq = Eq(i, j)
    if eq is S.true:
        return EQ_TRUE
    if eq is S.false:
        return EQ_FALSE
    return EQ_UNKNOWN


# --- SHADOW: the impl region of model.py, verbatim (contracts stripped) -----
def shadow_entry(i, j, Eq, S):
    # impl-start
    e = real_eq_class(i, j, Eq, S)        # `e = eq_class(i, j)`
    if e == EQ_TRUE:
        return ONE
    elif e == EQ_FALSE:
        return ZERO
    return DEFERRED
    # impl-end


# --- type bridge (mapping.md §2) --------------------------------------------
def tag_of_value(v, S, KroneckerDelta):
    """oracle value -> model cell tag. Returns None for an unmappable value
    (reported as a disagreement, never silently bucketed)."""
    if v is S.One:
        return ONE
    if v is S.Zero:
        return ZERO
    if isinstance(v, KroneckerDelta):
        return DEFERRED
    return None


def value_of_tag(tag, i, j, S, KroneckerDelta):
    """model cell tag -> oracle value (the REAL KroneckerDelta for DEFERRED)."""
    if tag == ONE:
        return S.One
    if tag == ZERO:
        return S.Zero
    return KroneckerDelta(i, j)


# --- input generation -------------------------------------------------------
def boundary_pool(sympy_ns):
    """Hand-built index expressions covering the shapes `_entry` really sees:
    bare symbols under assorted assumptions, integer literals (positive, zero,
    negative), and symbol arithmetic. Every branch of the impl is reached from
    the ordered sweep over this pool."""
    Symbol = sympy_ns["Symbol"]
    symbols = sympy_ns["symbols"]
    Integer = sympy_ns["Integer"]
    S = sympy_ns["S"]
    floor = sympy_ns["floor"]
    Abs = sympy_ns["Abs"]

    i, j, k, l = symbols("i j k l", integer=True)
    p, q = symbols("p q", integer=True, positive=True)
    m = Symbol("m", integer=True, negative=True)
    z = Symbol("zz", integer=True, zero=True)
    n = Symbol("n", integer=True, positive=True)
    return [
        i, j, k, l, p, q, m, z, n,
        i + 1, i - 1, j + 1, 2 * i, i + j, i + k, 3 * k, i + j + k,
        i * j, i ** 2, -i, 5 - i, i + 0,
        Integer(0), Integer(1), Integer(2), Integer(3),
        Integer(-1), Integer(-2), Integer(10),
        S.Zero, S.One, floor(i / 2), Abs(i), Abs(j),
    ][:BOUNDARY_POOL_MAX]


def f2p_pairs(sympy_ns):
    """The exact FAIL_TO_PASS shape first, then one witness per impl branch."""
    symbols = sympy_ns["symbols"]
    Integer = sympy_ns["Integer"]
    i, j = symbols("i j", integer=True)
    return [
        (i, j),                      # F2P test_Identity: distinct symbols -> DEFERRED
        (i, i),                      # EQ_TRUE  -> ONE
        (Integer(0), Integer(1)),    # EQ_FALSE -> ZERO
        (i, i + 1),                  # EQ_FALSE via arithmetic
        (i, i + 0),                  # EQ_TRUE via structural collapse
        (i, Integer(0)),             # EQ_UNKNOWN: symbol vs literal
    ]


def fuzz_corpus(rng, sympy_ns, size):
    """Randomly built integer index expressions (the concrete carrier)."""
    Symbol = sympy_ns["Symbol"]
    Integer = sympy_ns["Integer"]
    syms = [Symbol(c, integer=True) for c in "ijklpqrs"]

    def build(depth):
        if depth >= 2 or rng.random() < 0.35:
            if rng.random() < 0.6:
                return rng.choice(syms)
            return Integer(rng.randint(-4, 8))
        a = build(depth + 1)
        b = build(depth + 1)
        op = rng.randint(0, 3)
        if op == 0:
            return a + b
        if op == 1:
            return a - b
        if op == 2:
            return rng.randint(-3, 4) * a
        return a + rng.randint(-5, 5)

    return [build(0) for _ in range(size)]


# --- the differential -------------------------------------------------------
def check_pair(a, b, entry, ns, stats, use_getitem=None):
    """One input: shadow tag vs oracle-value-inverted tag, plus the forward
    value leg and the DEFERRED-injectivity guard. Returns an error string on
    disagreement, else None."""
    Eq, S, KroneckerDelta = ns["Eq"], ns["S"], ns["KroneckerDelta"]

    shadow = shadow_entry(a, b, Eq, S)                  # model impl, verbatim
    oracle_value = entry(a, b)                          # REAL patched _entry
    oracle_tag = tag_of_value(oracle_value, S, KroneckerDelta)

    stats["class"][real_eq_class(a, b, Eq, S)] += 1
    stats["tag"][shadow] += 1

    if oracle_tag is None:
        return ("DISAGREE (unmappable oracle value): i=%r j=%r shadow=%s "
                "oracle=%r (type %s)"
                % (a, b, TAG_NAME[shadow], oracle_value,
                   type(oracle_value).__name__))
    if shadow != oracle_tag:
        return ("DISAGREE (tag): i=%r j=%r eq_class=%s shadow=%s oracle=%s (%r)"
                % (a, b, CLASS_NAME[real_eq_class(a, b, Eq, S)],
                   TAG_NAME[shadow], TAG_NAME[oracle_tag], oracle_value))

    # second leg: model tag -> concrete value, structural equality
    shadow_value = value_of_tag(shadow, a, b, S, KroneckerDelta)
    if shadow_value != oracle_value:
        return ("DISAGREE (value): i=%r j=%r shadow=%s->%r oracle=%r"
                % (a, b, TAG_NAME[shadow], shadow_value, oracle_value))

    # bridge injectivity: on an undecided pair the deferred cell must be
    # observably distinct from both numeric cells (mapping.md §2).
    if shadow == DEFERRED:
        if oracle_value == S.One or oracle_value == S.Zero:
            return ("DISAGREE (degenerate bridge): i=%r j=%r DEFERRED cell "
                    "collapsed to a numeric cell %r" % (a, b, oracle_value))
        stats["deferred_distinct"] += 1

    # the public accessor path the F2P test drives, on boundary inputs.
    # `MatrixExpr.__getitem__` (matexpr.py:244) applies its own UNCHANGED bounds
    # validation before delegating to `_entry` and raises IndexError for an
    # index it cannot place in range (e.g. a negative-assumption symbol). That
    # validation sits upstream of the modeled decision and is not part of this
    # bundle's model, so a rejected index is skipped on this leg (counted) —
    # never treated as agreement on the modeled function, which was already
    # compared through `_entry` directly above.
    if use_getitem is not None:
        try:
            via_item = use_getitem[a, b]
        except IndexError:
            stats["accessor_rejected"] += 1
        else:
            stats["accessor_checked"] += 1
            if via_item != oracle_value:
                return ("DISAGREE (accessor): i=%r j=%r _entry=%r "
                        "Identity(n)[i,j]=%r" % (a, b, oracle_value, via_item))
    return None


def oracle_is_patched(matexpr_mod):
    """Refuse to run against pre-patch code: the gate applies patch.diff, and a
    silent pass against the unpatched oracle would certify nothing."""
    import inspect
    try:
        src = inspect.getsource(matexpr_mod.Identity._entry)
    except (OSError, TypeError):
        return None          # cannot read source; do not block the check
    return "Eq(" in src and "KroneckerDelta(" in src


def main():
    import sympy
    from sympy import (Eq, S, Symbol, symbols, Integer, Identity, floor, Abs)
    from sympy.functions.special.tensor_functions import KroneckerDelta
    from sympy.matrices.expressions import matexpr as matexpr_mod

    ns = {"Eq": Eq, "S": S, "Symbol": Symbol, "symbols": symbols,
          "Integer": Integer, "floor": floor, "Abs": Abs,
          "KroneckerDelta": KroneckerDelta}

    patched = oracle_is_patched(matexpr_mod)
    if patched is False:
        print("G-CONF ERROR: oracle Identity._entry is NOT the patched body "
              "(no Eq/KroneckerDelta in source) — refusing to compare.")
        print('{"checked": 0, "disagreements": 0, '
              '"error": "oracle not patched"}')
        return 1

    n = Symbol("n", integer=True, positive=True)
    In = Identity(n)                       # patched Identity (gold applied)
    entry = In._entry                      # THE modeled repo symbol, called

    stats = {"class": {EQ_FALSE: 0, EQ_TRUE: 0, EQ_UNKNOWN: 0},
             "tag": {ZERO: 0, ONE: 0, DEFERRED: 0},
             "deferred_distinct": 0,
             "accessor_checked": 0, "accessor_rejected": 0}
    problems = []
    checked = 0

    # --- boundary: F2P shape + one witness per branch, via the accessor too
    for a, b in f2p_pairs(ns):
        err = check_pair(a, b, entry, ns, stats, use_getitem=In)
        checked += 1
        if err:
            problems.append("boundary/F2P " + err)

    # --- boundary: exhaustive ordered sweep of the hand-built pool
    pool = boundary_pool(ns)
    for a, b in itertools.product(pool, repeat=2):
        err = check_pair(a, b, entry, ns, stats, use_getitem=In)
        checked += 1
        if err:
            problems.append("boundary/sweep " + err)
            if len(problems) >= DISAGREE_CAP:
                break

    # --- seeded fuzz over randomly built index expressions
    if len(problems) < DISAGREE_CAP:
        rng = random.Random(SEED)
        corpus = fuzz_corpus(rng, ns, FUZZ_CORPUS)
        for _ in range(N_FUZZ):
            a = rng.choice(corpus)
            b = rng.choice(corpus)
            err = check_pair(a, b, entry, ns, stats)
            checked += 1
            if err:
                problems.append("fuzz " + err)
                if len(problems) >= DISAGREE_CAP:
                    break

    if problems:
        print("G-CONF FAIL: %d disagreement(s) between the model.py impl "
              "shadow and the real patched Identity._entry over %d inputs "
              "(seed=%d):" % (len(problems), checked, SEED))
        for p in problems:
            print("  " + p)
        print('{"checked": %d, "disagreements": %d, "seed": %d, '
              '"shadow": "direct (contract-stripped impl region)", '
              '"oracle": "sympy.matrices.expressions.matexpr.Identity._entry '
              '(called, gold-patched)", "status": "fail"}'
              % (checked, len(problems), SEED))
        return 1

    print("G-CONF OK: model.py impl-region shadow (eq_class -> REAL Eq/S.true/"
          "S.false) == real patched Identity._entry on %d index pairs "
          "(1156 boundary sweep + %d fuzz, seed=%d); classes "
          "EQ_TRUE=%d EQ_FALSE=%d EQ_UNKNOWN=%d, tags ONE=%d ZERO=%d "
          "DEFERRED=%d, %d DEFERRED cells confirmed distinct from both numeric "
          "cells; %d boundary inputs also agreed through the public "
          "Identity(n)[i,j] accessor (%d rejected upstream by its unchanged "
          "bounds check); 0 disagreements on both bridge legs (sympy %s)."
          % (checked, N_FUZZ, SEED,
             stats["class"][EQ_TRUE], stats["class"][EQ_FALSE],
             stats["class"][EQ_UNKNOWN], stats["tag"][ONE], stats["tag"][ZERO],
             stats["tag"][DEFERRED], stats["deferred_distinct"],
             stats["accessor_checked"], stats["accessor_rejected"],
             sympy.__version__))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)", '
          '"oracle": "sympy.matrices.expressions.matexpr.Identity._entry '
          '(called, gold-patched)", '
          '"eq_true": %d, "eq_false": %d, "eq_unknown": %d, '
          '"deferred_distinct": %d, "accessor_checked": %d, "status": "pass"}'
          % (checked, SEED, stats["class"][EQ_TRUE], stats["class"][EQ_FALSE],
             stats["class"][EQ_UNKNOWN], stats["deferred_distinct"],
             stats["accessor_checked"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
