#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15809 (nagini).

SHADOW: the `# impl-start` / `# impl-end` region of model.py (`lattice_reduce`),
copied VERBATIM below with only the contract calls stripped (there are no
`Requires`/`Ensures`/`Invariant`/`Assert`/`Fold`/`Acc`/`MustTerminate` calls
inside the impl region itself, so the region transfers character-for-character
including its comments; the surrounding pre/post-condition regions are the
contracts that were dropped). The model IS Python — no transliteration. The
`# pure-start` region declares no helpers, and no `PSeq` value crosses the impl
region (the carrier is a plain `List[int]`), so no sequence shim is needed.

The four `@ContractOnly` callees have no body to copy, so per the G-CONF
contract each one CALLS THE REAL repo code it axiomatizes (mapping.md §1/§3),
rather than being reimplemented here:

  * `has_noncomparable_operand` -> runs the REAL unchanged generator
    `cls._new_args_filter` (miscellaneous.py:508-534) over the sympified
    operands exactly as `__new__` does (`frozenset(cls._new_args_filter(args))`,
    :349-350) and reports whether the comparability guard's `ValueError`
    (:521-523) is what comes out.
  * `has_absorbing_operand` -> the same REAL generator, reporting whether
    `ShortCircuit` (:525-526) is what comes out.
  * `canonical_reduction_defined` -> runs the REAL unchanged chain
    `cls._collapse_arguments` (:373-506) then `cls._find_localzeros` (:536-560)
    over the REAL filtered frozenset and reports whether it YIELDS a canonical
    set at all. That chain is PARTIAL: `_find_localzeros` compares the survivors
    against ONE ANOTHER through `_is_connected` (:552, :563-583), whose
    `r = hit(x >= y, Max, Min)` (:574) can propagate out of `Expr.__ge__`
    (`sympy/core/expr.py:295`, `TypeError("Invalid comparison of complex %s")`)
    for survivors the per-operand scan passed over. Vacuously True when the scan
    already decided the outcome (the chain is then never reached), which is what
    the axiom's prose says and what the impl's call order relies on.
  * `canonical_count` -> `len()` of that same REAL chain, i.e. the very value
    whose length the patched `if not args` / `if len(args) == 1` tests read
    (:361-365). PARTIAL for the same reason: it is only ever called where
    `canonical_reduction_defined` holds (the model's `Requires`).

Because these bridges consume the REAL generator in the REAL order, they inherit
its order-sensitivity instead of assuming the two pre-filters are independent:
`Min(-oo, I)` short-circuits on the absorbing `-oo` BEFORE the filter ever
reaches the non-comparable `I` (absorbing=True, non-comparable=False), while
`Min(I, -oo)` raises `ValueError` (the reverse). Both orders are in the boundary
catalogue below, and a reimplemented "does the list contain a non-comparable
operand?" predicate would have gotten them wrong.

ORACLE: the REAL patched repo function of mapping.md §1 —
`MinMaxBase.__new__(cls, *args, **assumptions)`,
`sympy/functions/elementary/miscellaneous.py:341` at base_commit — CALLED, not
transliterated, through its public entry points `sympy.Max(*raw)` /
`sympy.Min(*raw)` (the two concrete lattices; mapping.md §2 notes both are the
same modeled `lattice_reduce` with `identity`/`zero` swapped, and the F2P tests
`test_Min` / `test_Max` exercise exactly those two instantiations). The gate
applies patch.diff (the deleted empty-args guard, :342-343) to /testbed before
this script runs and sets PYTHONPATH, so the constructor imported here is the
PATCHED one; this script does not apply the patch itself.

TYPE BRIDGE (mapping.md §2, inverted):

  * `operands: List[int]` <-> the variadic `*args` operand collection. A
    concrete operand collection `raw` (a list of sympy `Expr`s) is presented to
    the shadow as the opaque id list `list(range(len(raw)))`; the id ordering
    preserves the collection ordering, `len(operands) == len(raw)`, and the
    bridged `@ContractOnly` callees resolve ids back to `raw` before calling the
    real repo code. The model observes nothing of an operand but its identity,
    which is precisely what the abstraction claims.
  * `identity`/`zero`/`single`/`aggregate` <-> `cls.identity`, `cls.zero`,
    `list(args).pop()` (:365), and the assembled `Expr.__new__(cls, _args)`
    object (:367-371). The shadow is fed the four PAIRWISE-DISTINCT int
    sentinels 0/1/2/3 (satisfying the model's distinctness `Requires`), and the
    sentinel it returns is then DECODED to the concrete repo value it stands
    for. The `single` decode pops the real canonical set; the `aggregate` decode
    runs the repo's own three assembly lines (`Expr.__new__(cls, _args)`,
    `obj._argset = _args`) against the real canonical set.
  * `NonComparableOperand` <-> the `ValueError("...is not comparable.")` that
    propagates uncaught out of `__new__`. A shadow `NonComparableOperand` is
    conformant iff the real constructor raises `ValueError`.
  * `ReductionUndefined` <-> whatever error the canonical-set chain itself
    propagates (mapping.md §2): `TypeError("Invalid comparison of complex ...")`
    from `Expr.__ge__` (`sympy/core/expr.py:295`) on the complex-comparison
    class, `NotImplementedError` where the relational is undecided. The model
    cannot name one builtin for it, so the decode ASKS THE REAL CHAIN which error
    it propagated for this collection and compares that type name — the same
    discipline as the `single`/`aggregate` decodes, which run the repo's own
    lines rather than reproducing them. What the shadow decides on its own is
    WHETHER to fail; the identity of the failure comes from the repo.

Requires-satisfaction: the model's preconditions are read permission on the
operand list (vacuous outside Nagini) plus pairwise-distinctness of the four
sentinels, which holds by construction for every generated input (0/1/2/3), so
EVERY generated input is in the domain — none is filtered out and the input
domain is not narrowed anywhere.

INPUTS: the modeled input space is INFINITE (arbitrary sympy operand
collections), so a deterministic boundary catalogue runs first and seeded fuzz
fills the count. The catalogue takes every branch of the impl region at least
once, per lattice: the empty collection (the F2P shape — `Min() == oo`,
`Max() == -oo`, the identity branch that the deleted guard used to pre-empt),
collections that reduce to the empty canonical set for a DIFFERENT reason (only
`cls.identity` operands, which `_new_args_filter` drops), the absorbing-operand
short-circuit (`zero`), one survivor (`single`, including duplicates and
comparable numerics collapsing to one), >=2 survivors (`aggregate`, including
nested `Max`/`Min` flattening), and the non-comparable rejection (`I`, `zoo`,
`nan`, `cos(x)/sin(x)` substituted at `I`, non-comparables mixed into comparable
collections in BOTH orders relative to an absorbing operand), and the
UNDEFINED-canonical-set-pass failure (operands the per-operand scan passes over
whose survivors `_find_localzeros` cannot compare against one another — `x + I`,
`x - I`, `I*x`, `sign(x)`, `Order(x)` — alone, paired in both orders, and behind
or ahead of an absorbing / non-comparable operand, where the scan decides first
and the pass is never reached). Then fuzz over a pool of real symbols,
rationals, +-oo, non-comparables, the undefined class and nested extrema.

Total comparisons >= 1e5 (N_FUZZ fuzz collections per lattice + catalogue x2).
Pinned seed: SEED = 15809 (recorded in mapping.md, "## G-CONF").

Exit 0 iff zero disagreements; a disagreement prints the input and both sides
and exits 1. stdlib + sympy (the library under test) only.
"""
import json
import random
import sys

SEED = 15809
N_FUZZ = 50_000          # per lattice; x2 lattices => >= 1e5 comparisons
MAX_REPORT = 5

# The four pairwise-distinct opaque sentinels the model is fed (mapping.md §2).
S_IDENTITY, S_ZERO, S_SINGLE, S_AGGREGATE = 0, 1, 2, 3


# --------------------------------------------------------------------------
# Type bridge: the shadow's opaque operand ids resolve to the real operands
# through this registry (mapping.md §2: `operands: List[int]` <-> `*args`).
# --------------------------------------------------------------------------
class Bridge(object):
    """Binds one concrete call site: a lattice class and its operand list."""

    def __init__(self, cls, raw, sympify, ShortCircuit, Expr):
        self.cls = cls
        self.raw = list(raw)
        self._sympify = sympify
        self._ShortCircuit = ShortCircuit
        self._Expr = Expr

    # ids -> concrete operands, in collection order
    def concrete(self, operands):
        return [self.raw[i] for i in operands]

    def _filtered(self, operands):
        """The REAL `frozenset(cls._new_args_filter(sympify(a) for a in args))`
        of miscellaneous.py:347-350. Returns ("ok", frozenset),
        ("noncomparable", None) or ("absorbing", None) — whichever the real
        unchanged generator produces first, in the real iteration order."""
        gen = (self._sympify(a) for a in self.concrete(operands))
        try:
            return "ok", frozenset(self.cls._new_args_filter(gen))
        except self._ShortCircuit:
            return "absorbing", None
        except ValueError:
            return "noncomparable", None

    # --- the four @ContractOnly callees, bridged to the REAL repo code ------
    def has_noncomparable_operand(self, operands):
        return self._filtered(operands)[0] == "noncomparable"

    def has_absorbing_operand(self, operands):
        return self._filtered(operands)[0] == "absorbing"

    def canonical_set(self, operands):
        """The REAL canonical set: `_collapse_arguments` then
        `_find_localzeros` (miscellaneous.py:356-359), whose length the patched
        `if not args` / `if len(args) == 1` tests read (:361-365). PARTIAL —
        `_find_localzeros` compares the survivors against one another through
        `_is_connected` (:552, :574) and can propagate that comparison's own
        error instead of returning a set."""
        kind, args = self._filtered(operands)
        if kind != "ok":
            raise AssertionError("canonical_set on a pre-filter-rejected "
                                 "collection: %r" % (kind,))
        args = self.cls._collapse_arguments(args)   # evaluate=True default
        args = self.cls._find_localzeros(args)
        return args

    def canonical_reduction_defined(self, operands):
        """Whether that REAL chain yields a canonical set at all. Vacuously True
        where the ordered scan already decided the outcome, since the chain is
        then never reached (the impl's call order makes this the only reading:
        it consults this predicate after both scan outcomes)."""
        if self._filtered(operands)[0] != "ok":
            return True
        try:
            self.canonical_set(operands)
        except Exception:                             # noqa: BLE001
            return False
        return True

    def undefined_failure_name(self, operands):
        """The type name of the error the REAL chain propagates for this
        collection — the concrete repo identity of the model's
        `ReductionUndefined` (mapping.md §2). Returns a marker when the chain
        does NOT fail, so a shadow that failed where the repo did not is a
        disagreement rather than a silent pass."""
        try:
            self.canonical_set(operands)
        except Exception as exc:                      # noqa: BLE001
            return type(exc).__name__
        return "NO-FAILURE"

    def canonical_count(self, operands):
        return len(self.canonical_set(operands))

    # --- sentinel -> concrete repo value (mapping.md §2, inverted) ----------
    def decode(self, sentinel, operands):
        if sentinel == S_IDENTITY:
            return self.cls.identity
        if sentinel == S_ZERO:
            return self.cls.zero
        if sentinel == S_SINGLE:
            # `list(args).pop()` — miscellaneous.py:365
            return list(self.canonical_set(operands)).pop()
        if sentinel == S_AGGREGATE:
            # the base creation — miscellaneous.py:367-371
            _args = frozenset(self.canonical_set(operands))
            obj = self._Expr.__new__(self.cls, _args)
            obj._argset = _args
            return obj
        raise AssertionError("shadow returned a non-sentinel: %r" % (sentinel,))


# --------------------------------------------------------------------------
# SHADOW — model.py's impl region, VERBATIM (contract calls stripped).
# The region below is byte-identical to the `    # impl-start` .. `    # impl-end`
# block of model.py; the four `@ContractOnly` callees it names resolve to the
# REAL repo code through the bridge, so the axioms are exercised, not assumed.
# --------------------------------------------------------------------------
class NonComparableOperand(Exception):
    """model.py's user-defined stand-in for the propagated builtin
    `ValueError` (mapping.md §2: a builtin exception in an `Exsures` crashes the
    Nagini translator)."""


class ReductionUndefined(Exception):
    """model.py's user-defined stand-in for whatever error the canonical-set
    chain itself propagates (mapping.md §2) — the `TypeError` out of
    `Expr.__ge__` (`sympy/core/expr.py:295`) on the complex-comparison class, or
    the `NotImplementedError` where the relational is undecided. The decode
    resolves it to the type the REAL chain produced for the collection at hand."""


# The four `@ContractOnly` callees keep their model.py names at module level
# (so the impl region below needs no call-site edits at all) and forward to the
# REAL repo code through the bridge bound for the current call site.
_ACTIVE = None          # the Bridge for the operand collection under test


def has_noncomparable_operand(operands):
    return _ACTIVE.has_noncomparable_operand(operands)


def has_absorbing_operand(operands):
    return _ACTIVE.has_absorbing_operand(operands)


def canonical_reduction_defined(operands):
    return _ACTIVE.canonical_reduction_defined(operands)


def canonical_count(operands):
    return _ACTIVE.canonical_count(operands)


def lattice_reduce(operands, identity, zero, single, aggregate):
    # impl-start
    # (The stale guard `if len(operands) == 0: raise EmptyReductionRejected()`
    #  is absent: the empty collection is handled by the empty-canonical-set
    #  branch below, returning the identity element.)
    # The unchanged comparability pre-filter rejects a non-comparable operand
    # before any result branch (the empty collection passes, having no operand).
    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    # The survivors reach the canonical-set pass, which compares them against one
    # another; where it cannot, it yields no canonical set and its failure
    # propagates (the empty collection is defined here, having nothing to
    # compare).
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate
    # impl-end


# --------------------------------------------------------------------------
# Input generation
# --------------------------------------------------------------------------
def boundary_catalogue(sy):
    """Every branch of the impl region, at least once per lattice."""
    x = sy["Symbol"]("x")
    a = sy["Symbol"]("a", real=True)
    b = sy["Symbol"]("b", real=True)
    c = sy["Symbol"]("c", real=True)
    p = sy["Symbol"]("p", positive=True)
    I, zoo, nan = sy["I"], sy["zoo"], sy["nan"]
    oo, noo = sy["oo"], -sy["oo"]
    Int, Rat = sy["Integer"], sy["Rational"]
    Max, Min, cos, sin = sy["Max"], sy["Min"], sy["cos"], sy["sin"]
    sign, Order = sy["sign"], sy["Order"]
    subbed_cos = cos(x).subs(x, I)
    subbed_sin = sin(x).subs(x, I)
    # Operands the PER-OPERAND scan passes over (is_real is None and they are not
    # numbers, so the :521-523 guard does not fire) but which the canonical-set
    # pass may fail to compare against another survivor.
    undef = [x + I, x + 2 * I, x - I, I * x, sign(x), Order(x)]
    return [
        # --- the F2P shape: the empty collection -> identity branch ---------
        [],
        # --- single survivor ------------------------------------------------
        [a], [p], [Int(0)], [Int(7)], [Rat(-3, 2)],
        [a, a],                          # duplicate collapses to one
        [Int(1), Int(2), Int(3)],         # comparable numerics -> one
        [Int(-5), Rat(1, 3), Int(4)],
        [p, Int(0)],                     # sign-known symbol vs 0
        # --- empty canonical set for a reason OTHER than the empty input:
        #     only-identity operands are dropped by _new_args_filter ---------
        [oo], [noo], [oo, oo], [noo, noo],
        # --- absorbing operand -> zero branch (both lattices) --------------
        [oo, noo], [noo, oo], [a, oo], [a, noo], [oo, a, noo],
        # --- >= 2 survivors -> aggregate ------------------------------------
        [a, b], [b, a], [a, b, c], [a, b, a],
        [Max(a, b), c], [Min(a, b), c],  # nested extrema flatten
        [Max(a, b), Min(a, b)],
        [a, Int(3)], [a, b, Int(0), Rat(5, 7)],
        # --- non-comparable operand -> rejection (unchanged pre-filter) -----
        [I], [zoo], [nan], [I, I],
        [a, I], [I, a], [Int(1), zoo], [zoo, Int(1)],
        [subbed_cos, subbed_sin], [subbed_cos], [a, subbed_sin],
        # non-comparable vs absorbing, BOTH orders: the real generator's order
        # decides which of the two pre-filters fires (see the docstring).
        [noo, I], [I, noo], [oo, I], [I, oo],
        [a, noo, I], [a, I, noo],
        # --- the canonical-set pass is UNDEFINED: the scan passes every operand
        #     over, and _find_localzeros -> _is_connected then cannot compare the
        #     survivors against one another. Each undefined-class operand appears
        #     alone, paired with a plain symbol in BOTH orders, paired with a real
        #     symbol, doubled, and behind/ahead of an absorbing operand (where the
        #     scan decides FIRST and the pass is never reached) and a
        #     non-comparable one (same).
    ] + [ops for u in undef for ops in (
        [u], [u, u], [x, u], [u, x], [a, u], [u, a],
        [Int(3), u], [u, Rat(-7, 2)],
        [oo, u], [u, oo], [noo, u], [u, noo],
        [I, u], [u, I],
        [x, a, u], [u, x, a],
    )]


def make_pool(sy):
    x = sy["Symbol"]("x")
    Int, Rat = sy["Integer"], sy["Rational"]
    Max, Min = sy["Max"], sy["Min"]
    sign, Order = sy["sign"], sy["Order"]
    syms = [sy["Symbol"](n, real=True) for n in ("a", "b", "c")] + [x]
    pos = [sy["Symbol"]("p", positive=True), sy["Symbol"]("q", negative=True)]
    nums = [Int(k) for k in (-3, -1, 0, 1, 2, 5)] + [Rat(1, 2), Rat(-7, 3)]
    infs = [sy["oo"], -sy["oo"]]
    noncomp = [sy["I"], sy["zoo"], sy["nan"], sy["cos"](x).subs(x, sy["I"])]
    # The undefined class: the per-operand scan passes these over, and the
    # canonical-set pass can then fail to place them against another survivor.
    undef = [x + sy["I"], x - sy["I"], sy["I"] * x, sign(x), Order(x)]
    nested = [Max(syms[0], syms[1]), Min(syms[1], syms[2]),
              Max(syms[0], nums[3]), Min(syms[2], infs[0])]
    return syms + pos + nums + infs + noncomp + undef + nested


def fuzz_collections(n, rng, pool):
    """Seeded fuzz. Lengths are drawn to oversample the discriminating small
    cardinalities (0 and 1) without ever excluding the longer ones."""
    for _ in range(n):
        r = rng.random()
        if r < 0.12:
            k = 0
        elif r < 0.35:
            k = 1
        else:
            k = rng.randint(2, 5)
        yield [rng.choice(pool) for _ in range(k)]


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------
BRANCH_OF = {S_IDENTITY: "identity", S_ZERO: "zero", S_SINGLE: "single",
             S_AGGREGATE: "aggregate"}


def observe_shadow(bridge):
    """Run the shadow over the bridged carrier and decode its sentinel.
    Returns (kind, value, branch) — `branch` is the impl-region branch the
    shadow took, read off the SENTINEL itself (not guessed from the decoded
    value), so the branch-coverage tally cannot be fooled."""
    global _ACTIVE
    _ACTIVE = bridge
    operands = list(range(len(bridge.raw)))          # opaque ids
    try:
        sentinel = lattice_reduce(operands, S_IDENTITY, S_ZERO,
                                  S_SINGLE, S_AGGREGATE)
    except NonComparableOperand:
        # §2: the modeled stand-in for the propagated builtin ValueError
        return ("RAISE", "ValueError", "reject")
    except ReductionUndefined:
        # §2: the stand-in for whatever the canonical-set chain itself
        # propagates; the concrete type comes from the REAL chain, not from here.
        return ("RAISE", bridge.undefined_failure_name(operands), "undefined")
    return ("VALUE", bridge.decode(sentinel, operands), BRANCH_OF[sentinel])


def observe_oracle(cls, raw):
    """The REAL patched `MinMaxBase.__new__`, called through its entry point."""
    try:
        return ("VALUE", cls(*raw))
    except Exception as exc:                          # noqa: BLE001
        return ("RAISE", type(exc).__name__)


def agree(shadow, oracle):
    """Shadow (kind, value, branch) vs oracle (kind, value): same kind, and
    for a value the same sympy object (structural `==`, type-checked so that a
    numeric coincidence across types cannot mask a divergence); for a raise the
    same exception type name."""
    if shadow[0] != oracle[0]:
        return False
    if shadow[0] == "RAISE":
        return shadow[1] == oracle[1]
    sv, ov = shadow[1], oracle[1]
    if type(sv) is not type(ov):
        return False
    return bool(sv == ov)


def main():
    try:
        import sympy
        from sympy import (Max, Min, Symbol, Integer, Rational, I, zoo, nan,
                           cos, sin, oo, sympify, sign, Order)
        from sympy.core.expr import Expr
        from sympy.core.operations import ShortCircuit
    except Exception as exc:                          # noqa: BLE001
        print("status=error cannot import sympy: %r" % (exc,))
        return 2

    sy = {"Symbol": Symbol, "Integer": Integer, "Rational": Rational, "I": I,
          "zoo": zoo, "nan": nan, "cos": cos, "sin": sin, "oo": oo,
          "Max": Max, "Min": Min, "sign": sign, "Order": Order}

    rng = random.Random(SEED)
    pool = make_pool(sy)
    catalogue = boundary_catalogue(sy)

    checked = 0
    branch_hits = {"identity": 0, "zero": 0, "single": 0, "aggregate": 0,
                   "reject": 0, "undefined": 0}
    disagreements = []

    for cls in (Max, Min):
        cases = list(catalogue)
        cases.extend(fuzz_collections(N_FUZZ, rng, pool))
        for raw in cases:
            bridge = Bridge(cls, raw, sympify, ShortCircuit, Expr)
            try:
                shadow = observe_shadow(bridge)
            except Exception as exc:                  # noqa: BLE001
                # A shadow crash is a disagreement, never a skipped input.
                shadow = ("SHADOW-ERROR",
                          "%s: %s" % (type(exc).__name__, exc), "error")
            oracle = observe_oracle(cls, raw)
            checked += 1
            branch_hits[shadow[2]] = branch_hits.get(shadow[2], 0) + 1
            if not agree(shadow, oracle):
                if len(disagreements) < MAX_REPORT:
                    print("DISAGREEMENT %s(*%r):\n  shadow=%r\n  oracle=%r"
                          % (cls.__name__, raw, shadow, oracle))
                disagreements.append((cls.__name__, repr(raw)))

    missing = sorted(k for k, v in branch_hits.items() if v == 0)
    print("sympy=%s checked=%d branch_hits=%s disagreements=%d"
          % (sympy.__version__, checked, json.dumps(branch_hits, sort_keys=True),
             len(disagreements)))
    if disagreements:
        print("status=fail %d disagreement(s) between the impl-region shadow "
              "of lattice_reduce and the patched MinMaxBase.__new__ over %d "
              "inputs (seed=%d)" % (len(disagreements), checked, SEED))
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": len(disagreements), "seed": SEED,
                          "examples": disagreements[:MAX_REPORT]},
                         sort_keys=True))
        return 1
    if missing:
        # A branch never taken means the generator dodged behaviour under
        # specification: refuse to report a green that certifies nothing.
        print("status=fail impl branches never exercised: %r" % (missing,))
        print(json.dumps({"status": "fail", "checked": checked,
                          "unexercised_branches": missing, "seed": SEED},
                         sort_keys=True))
        return 1
    print("status=pass impl-region shadow of lattice_reduce (with the four "
          "@ContractOnly observations calling the REAL _new_args_filter / "
          "_collapse_arguments / _find_localzeros) agrees with the patched "
          "MinMaxBase.__new__ via sympy.Max/sympy.Min on %d operand "
          "collections (seed=%d), branches %s, 0 disagreements."
          % (checked, SEED, json.dumps(branch_hits, sort_keys=True)))
    print(json.dumps({
        "status": "pass", "checked": checked, "disagreements": 0,
        "seed": SEED, "branch_hits": branch_hits,
        "oracle": ("MinMaxBase.__new__ (sympy/functions/elementary/"
                   "miscellaneous.py:341) called via sympy.Max/sympy.Min"),
        "shadow": "model.py impl region verbatim, contracts stripped",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
