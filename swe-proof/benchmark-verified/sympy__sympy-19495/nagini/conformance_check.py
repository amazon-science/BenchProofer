#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19495 (nagini).

SHADOW  -- the `# impl-start` / `# impl-end` regions of `model.py`, copied
           VERBATIM with only the contract calls stripped. The model IS
           Python, so nothing is transliterated: `Result0.__init__` loses its
           four `Ensures(Acc(...))` lines, `build` loses its `Requires`/
           `Ensures` block, and `replace_free_parameter`'s impl is the single
           call `return build(self_sym, cond_after, base_after, base_kind,
           listed_kind, listed_base, merged_sym, merged_base)`. The
           `# pure-start` region is empty in this bundle (no `@Pure` helpers)
           and the `# axioms-start` region declares no `@ContractOnly`
           callee, so there is no axiom to re-point at a repo function and no
           `PSeq` carrier to shim -- the model's carriers are plain `int`s
           plus the three-field `Result0`.

ORACLE  -- the REAL patched repo method, CALLED, not reimplemented:
           `ConditionSet._eval_subs(self, old, new)` in
           `sympy/sets/conditionset.py:208` @ base_commit (mapping.md §1),
           on its `old != sym` branch, which the gold patch rewrites at
           lines 243-247. The gate applies the gold patch and sets
           PYTHONPATH=/testbed before this script runs, so `_eval_subs` here
           is the post-patch method. Every input additionally cross-checks
           that the public `cs.subs(old, new)` dispatches to the same value,
           i.e. that the modeled branch is the reachable behaviour and not a
           dead private path. The unchanged callees the model folds in
           (`Basic.subs` on the condition and on the base set, and the
           `ConditionSet` constructor reached through `self.func`) are the
           real ones on the oracle side; on the shadow side the two `.subs`
           calls are the real ones too (mapping.md §2 folds them into the
           `cond_after` / `base_after` arguments) and the constructor's
           reduction is `build`, the deep model under test.

BRIDGE  -- mapping.md §2, inverted. Concrete inputs are generated first (a
           real `ConditionSet`, a real free symbol `old`, a real replacement
           `new`); the real `.subs` calls then produce `cond_after` and
           `base_after`, and those are ABSTRACTED into the model's carriers:
           a SymPy `Symbol` / `Set` becomes an interned `int` identity id
           (equal objects share an id, distinct objects get distinct ids),
           and the substituted predicate becomes the `int` truth tag
           COND_FALSE / COND_TRUE / COND_OPEN -- the truth status the
           constructor ITSELF assigns to the predicate, i.e. the one it
           branches on, which it fixes by first normalizing the predicate to
           a truth value (`condition = as_Boolean(condition)`,
           `sympy/sets/conditionset.py:136` @ base_commit, preceded by the
           explicit-listing-of-expressions rewrite at lines 125-134 -- both
           untouched by the gold patch, which shifts them by -2 only because
           it deletes two docstring lines) and only then testing
           `is S.false` / `is S.true` (lines 144 and 146). Reading the tag off
           the raw expression instead would
           mis-tag a predicate handed over as a number, or as a symbol whose
           vanishing its assumptions already decide, as if it were still a
           restriction: `as_Boolean` maps `1`/`0` to true/false and a
           `Symbol` to true/false whenever `.is_zero` is known
           (`sympy/logic/boolalg.py:20-58`), so those ARE decided predicates
           and the constructor reduces on them. `normalized_cond` replays
           exactly those two normalization steps with the repo's own helpers,
           a folded-in unchanged callee like the two `.subs` calls and the
           `sift`/`fuzzy_bool` listing decision below, and -- for a base
           domain that is itself a `ConditionSet` -- the condition-MERGING
           branch (`conditionset.py:161-179`), replayed by `merged_outcome`
           into the `merged_sym` / `merged_base` carriers.
           The oracle's return value is abstracted into (kind, sym id, base id,
           cond tag): `S.EmptySet` -> K_EMPTY; a value EQUAL to the
           replacement-applied base domain -> K_BASE with that domain as the
           base; otherwise a `ConditionSet` -> K_SET with its `.sym` /
           `.base_set`, and anything else -> K_BASE with the value itself.
           The base-domain test comes BEFORE the `ConditionSet` test on
           purpose: the model's `kind` classifies the REDUCTION's outcome, not
           the Python type of the value, and when the base domain is itself a
           restricted object `condition is S.true` hands that very object back
           (`conditionset.py:146`) -- that outcome is `K_BASE`
           ("the base domain passes through"), not a newly built `K_SET`.
           Reading it off the type alone was wrong: it re-tagged a pass-through
           as a construction. A `Dummy` bound variable abstracts to one
           reserved id (`sym_id`): the merge mints a fresh internal name no
           caller can write (`Dummy('lambda')`), so all such names are
           identified -- the load-bearing distinction, a result keyed on the
           replacement value, is a NAMED symbol and is unaffected.
           The shadow's `Result0` is then compared field for field, and only on
           the fields the spec's `Ensures` actually observe: K_EMPTY pins
           `kind` alone, K_BASE pins `kind` and `base`, K_SET pins `kind`,
           `sym` and `base`, plus `cond == COND_OPEN` on every base-domain
           shape EXCEPT the merge -- for which the spec deliberately claims no
           truth status, because the merge runs no further reduction and the
           object it builds really can carry an identically false conjoined
           predicate (measured: `ConditionSet(z, z < y, Union(Interval(0, y),
           ConditionSet(z, z >= -1, Reals)))` at `y -> -1` really yields
           `ConditionSet(z, False, Reals)`).

DOMAIN  -- every compared input satisfies the model's `Requires`
           (`cond_after in {COND_FALSE, COND_TRUE, COND_OPEN}`) plus the
           guards of the modeled branch (`old != cs.sym`, and a bound
           variable that is a `Symbol` -- the carrier mapping.md §2 row 1
           declares), and stays inside the base-domain scope mapping.md §3.1
           declares for the deep `build` model -- which is now every `Set`
           shape the substitution can produce, the condition-MERGING branch
           included: `base_kind` has a fourth value BASE_MERGED for a base
           domain that is itself a `ConditionSet`, and the bound variable the
           merge settles on is compared like any other field. Nothing is
           excluded by base shape any more, so the `domain_rejected` counter
           below is 0 by measurement rather than by construction. A merge whose
           SETTLED bound variable the constructor then refuses
           (`conditionset.py:181-185`) is the one merge outcome with no result
           to compare, and it is counted under `merge_refused`: the merge can
           ADOPT the inner object's bound variable, which may be a compound
           `Expr` even when the caller's is an ordinary `Symbol`, so this
           refusal is reachable without any non-`Symbol` input from the caller.
           It is scoped to the refusal ITSELF, not to compound bound variables
           generally -- a compound settled bound variable the merged predicate
           still mentions is ACCEPTED, compared, and keyed on as usual. Four
           further shapes are
           counted and reported as out-of-domain rather than compared,
           because on them the operation DELIVERS NO object at all and the
           model's totality claim is therefore not made about them (the model
           admits an input only when the predicate HAS one of the three truth
           tags, and only for a `Symbol` bound variable):
             * a predicate the constructor refuses to read as a truth value
               (`as_Boolean` raises `TypeError`, e.g. a substituted `2` or
               `nan`) -- there is no tag for it;
             * a bound variable that is a non-`Symbol` `Expr` (e.g. `x + 1`),
               which the constructor may refuse outright
               (`ValueError('non-symbol dummy not recognized in condition')`,
               conditionset.py:181-185);
             * a replacement on which the operation ITSELF raises -- either the
               substitution (e.g. `nan` or `I` into an inequality) or the
               constructor's own member-by-member decision over an explicit
               listing (e.g. a predicate symbol reused as a listed real
               member). Excluding these is not assumed: the script REQUIRES
               the real `cs._eval_subs(old, new)` to refuse the input with the
               identical exception, and reports a disagreement if it instead
               delivers a result. The public `cs.subs(old, new)` was measured
               to raise identically too, so no object reaches a caller either
               way.
           All three refusals are the UNCHANGED code's own, byte-identical at
           base_commit with and without the gold patch (measured; mapping.md
           §3.1), so nothing about the behaviour under specification hides in
           them. Every exclusion is counted and printed in the summary rather
           than dropped silently.

INPUTS  -- the modeled input space is infinite (arbitrary SymPy predicates
           and domains), so: boundary cases first -- the issue-17341 headline
           input, the F2P regression
           `ConditionSet(n, n < x, Interval(-oo, 0)).subs(x, p)`, each of the
           impl's three branches (COND_FALSE / COND_TRUE / COND_OPEN) over
           each base-domain family, the predicates whose truth only the
           constructor's own normalization decides (a substituted `1` / `0`,
           a replacement symbol whose `.is_zero` is known either way, and a
           predicate handed over as an explicit listing of expressions), and
           -- for the merge -- a base domain given as a `Union` one of whose
           parts COLLAPSES under the replacement so that the bare inner
           `ConditionSet` is what reaches the constructor, in all four
           binder outcomes the merge can reach (keep the outer variable
           because it equals the inner one, keep it because the inner
           predicate does not mention it, adopt the inner one, and mint
           `Symbol('lambda')` / a fresh `Dummy` when each variable occurs in
           the other's predicate) --
           then seeded fuzz over a pool of real `ConditionSet`s crossed with
           16 replacement values until >= 100000 in-domain comparisons are
           made. Pinned seed: 19495 (recorded in mapping.md §G-CONF),
           matching the two sibling bundles.

CONTROL -- run with the gold patch withheld, the same generator and seed
           disagree already inside the boundary set (measured: 10
           disagreements in the first 104 comparisons; the run stops early
           after 5), every one of them on
           the COND_TRUE path (`tag=1`), including the issue-17341 headline
           input, the F2P regression and the replacement-collides-with-the-
           bound-variable case. The withheld line returned
           `ConditionSet(new, Contains(new, base), base)`, keying the result
           on the replacement value instead of delivering the base domain.
           The check therefore discriminates the behaviour under
           specification rather than passing vacuously.

stdlib + the testbed's sympy only. Exit 0 iff zero disagreements.
"""
import random
import sys

from sympy import (S, Symbol, Dummy, Interval, Contains, Eq, Mod, And, Lambda,
                   asin, sin, pi, oo, imageset, Rational, FiniteSet, Union)
from sympy.core.expr import Expr  # the modeled branch's own guard (asserted below)
from sympy.core.logic import fuzzy_bool
from sympy.logic.boolalg import as_Boolean
from sympy.sets import ConditionSet
from sympy.sets.sets import Set, EmptySet
from sympy.utilities.iterables import sift

SEED = 19495
N_TARGET = 100_000

# ---------------------------------------------------------------------------
# model.py, verbatim minus contracts
# ---------------------------------------------------------------------------
# Constants (model.py lines 68-88).
COND_FALSE = 0
COND_TRUE = 1
COND_OPEN = 2

K_EMPTY = 0
K_BASE = 1
K_SET = 2
K_REFUSED = 3

BASE_EMPTY = 0
BASE_LISTED = 1
BASE_PLAIN = 2
BASE_MERGED = 3

MERGE_REFUSED = 0


class Result0:
    """model.py Result0 -- the four `Ensures(Acc(...))` lines stripped."""

    def __init__(self, kind, sym, base, cond):
        self.kind = kind  # type: int
        self.sym = sym    # type: int
        self.base = base  # type: int
        self.cond = cond  # type: int


def build(sym, cond, base, base_kind, listed_kind, listed_base,
          merged_sym, merged_base):
    # impl-start  (model.py build impl region, verbatim)
    if cond == COND_FALSE:
        return Result0(K_EMPTY, sym, base, cond)
    elif base_kind == BASE_EMPTY:
        return Result0(K_EMPTY, sym, base, cond)
    elif cond == COND_TRUE:
        return Result0(K_BASE, sym, base, cond)
    elif base_kind == BASE_LISTED:
        return Result0(listed_kind, sym, listed_base, cond)
    elif base_kind == BASE_MERGED:
        if merged_sym == MERGE_REFUSED:
            return Result0(K_REFUSED, merged_sym, merged_base, cond)
        return Result0(K_SET, merged_sym, merged_base, cond)
    else:
        return Result0(K_SET, sym, base, cond)
    # impl-end


def replace_free_parameter(self_sym, new, cond_after, base_after, base_kind,
                           listed_kind, listed_base, merged_sym, merged_base):
    # impl-start  (model.py replace_free_parameter impl region, verbatim)
    return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                 listed_base, merged_sym, merged_base)
    # impl-end


# ---------------------------------------------------------------------------
# Type bridge (mapping.md §2)
# ---------------------------------------------------------------------------
_IDS = {}


def obj_id(o):
    """Intern a SymPy Symbol / Set as an `int` identity id: equal objects get
    the same id, distinct objects distinct ids (mapping.md §2 rows 1 and 3)."""
    try:
        key = (type(o).__name__, o)
        hash(key)
    except TypeError:
        key = (type(o).__name__, str(o))
    if key not in _IDS:
        _IDS[key] = len(_IDS) + 1
    return _IDS[key]


# The one reserved id for a FRESH INTERNAL bound-variable name. The merging
# branch can mint `Dummy('lambda')` (conditionset.py:174-179), an object no
# caller can name and whose identity differs between two evaluations of the same
# input, so every such name abstracts to a single id. This does not blur the
# load-bearing distinction: the behaviour under specification is about a result
# keyed on the REPLACEMENT VALUE, which is always a named `Symbol`.
_FRESH_SYM = -1


def sym_id(s):
    """A bound variable -> the model's `sym` carrier id, identifying every
    fresh internal name (mapping.md §2 row 1)."""
    return _FRESH_SYM if isinstance(s, Dummy) else obj_id(s)


def normalized_cond(c):
    """The predicate as the real constructor reads it BEFORE it branches on
    its truth, replayed with the repo's own helpers (a folded-in unchanged
    callee, exactly like the two `.subs` calls and `sift`/`fuzzy_bool`):

      * a predicate handed over as an explicit listing of expressions becomes
        the conjunction of their vanishing (conditionset.py:122-131);
      * the result is then read as a truth value by `as_Boolean`
        (conditionset.py:134 -> boolalg.py:20-58), which yields `S.true` /
        `S.false` for a predicate given as a number or as a symbol whose
        `.is_zero` is known, and returns the predicate unchanged when it is
        still an undecided restriction.

    Returns None when the constructor refuses the predicate outright
    (`as_Boolean` raises `TypeError`): such an input has no truth tag, so the
    model does not admit it (see DOMAIN)."""
    if isinstance(c, FiniteSet):
        c = And(*[Eq(lhs, 0) for lhs in c])
    try:
        return as_Boolean(c)
    except TypeError:
        return None


def cond_tag(c):
    """A SymPy predicate -> the model's 3-valued truth tag (mapping.md §2
    row 2): the truth status the constructor assigns to it, i.e. `is S.true` /
    `is S.false` / otherwise applied to `normalized_cond(c)`, which is what
    the constructor's own branches test. None when there is no such status."""
    n = normalized_cond(c)
    if n is None:
        return None
    if n is S.true:
        return COND_TRUE
    if n is S.false:
        return COND_FALSE
    return COND_OPEN


def abstract_result(real, base_after=None):
    """The real returned object -> (kind, sym id or None, base id or None, cond
    tag or None) (mapping.md §2 row 4).

    `kind` classifies the REDUCTION's outcome, not the Python type of the
    value, so a value equal to the replacement-applied base domain is K_BASE
    ("the base domain passes through") even when that domain is itself a
    `ConditionSet` -- which is exactly what `condition is S.true` hands back
    (conditionset.py:146). Testing `isinstance(real, ConditionSet)` first would
    re-tag that pass-through as a freshly built restricted object."""
    if real is S.EmptySet or isinstance(real, EmptySet):
        return (K_EMPTY, None, None, None)
    if base_after is not None and real == base_after:
        return (K_BASE, None, obj_id(real), None)
    if isinstance(real, ConditionSet):
        return (K_SET, sym_id(real.sym), obj_id(real.base_set),
                cond_tag(real.condition))
    return (K_BASE, None, obj_id(real), None)


def base_tag(b):
    """A SymPy base Set -> the model's 4-valued base-domain SHAPE tag. The
    reduction the real constructor performs depends on this, so it is an
    observed model input (mapping.md §2). The four values are exactly the four
    shapes `__new__` dispatches on: empty (line 148), an explicit finite
    listing (line 152), a restricted object to MERGE with (line 161), and
    anything else."""
    if b is S.EmptySet or isinstance(b, EmptySet):
        return BASE_EMPTY
    if isinstance(b, FiniteSet):
        return BASE_LISTED
    if isinstance(b, ConditionSet):
        return BASE_MERGED
    return BASE_PLAIN


def listed_outcome(sym, cond, fbase):
    """The member-by-member decision the real constructor performs over an
    explicitly listed base domain, replayed with the REPO's own helpers
    (`sift` + `fuzzy_bool`, conditionset.py's own imports) and abstracted into
    the model's (listed_kind, listed_base) carriers (mapping.md §2). This is a
    folded-in unchanged callee, exactly like the two `.subs` calls."""
    sifted = sift(fbase, lambda _: fuzzy_bool(cond.subs(sym, _)))
    if sifted[None]:
        know = FiniteSet(*sifted[True])
        undecided = FiniteSet(*sifted[None])
        if not sifted[True]:
            return (K_SET, obj_id(undecided))
        return (K_BASE, obj_id(Union(know, ConditionSet(sym, cond, undecided))))
    res = FiniteSet(*sifted[True])
    if not sifted[True]:
        return (K_EMPTY, 0)
    return (K_BASE, obj_id(res))


def merged_outcome(sym, cond, cbase):
    """The condition-MERGE the real constructor performs when the base domain
    is ITSELF a restricted object, replayed line for line from
    `conditionset.py:161-179` @ base_commit and abstracted into the model's
    (merged_sym, merged_base) carriers. A folded-in unchanged callee, exactly
    like the two `.subs` calls and the `sift`/`fuzzy_bool` listing decision.

    The four branches settle the bound variable: keep it when it IS the inner
    one; keep it when the inner predicate does not mention it; adopt the inner
    one when the outer predicate does not mention THAT; otherwise mint
    `Symbol('lambda')`, or a fresh `Dummy` when the name is already taken. The
    merged object stands over the INNER base domain. No truth status is
    replayed for the conjoined predicate because the constructor performs no
    further reduction on it (it falls through to `Basic.__new__`, line 187), so
    the model claims none.

    The merge is followed by the constructor's OWN check on the bound variable
    it has just settled on (`conditionset.py:181-185` @ base_commit), replayed
    here because the merge can hand that check a non-`Symbol`: branch 3 ADOPTS
    the inner object's bound variable, and an inner bound variable may be a
    compound `Expr` even when the caller's is an ordinary `Symbol`. The check is
    NOT `isinstance(sym, Symbol)` -- a compound bound variable is refused only
    when substituting a fresh `Dummy` for it leaves NO trace in the conjoined
    predicate:

        if not isinstance(sym, Symbol):
            s = Dummy('lambda')
            if s not in condition.xreplace({sym: s}).free_symbols:
                raise ValueError('non-symbol dummy not recognized in condition')

    So a compound bound variable the merged predicate still mentions is ACCEPTED
    and the object stands keyed on it. Only the refusing case has no result to
    compare, and it is reported as MERGE_REFUSED rather than assumed: the caller
    requires the real method to refuse it with the identical exception."""
    s, c, inner_base = cbase.args
    if sym == s:
        merged_cond = And(cond, c)
        msym = sym
    elif sym not in c.free_symbols:
        merged_cond = And(cond, c.xreplace({s: sym}))
        msym = sym
    elif s not in cond.free_symbols:
        merged_cond = And(cond.xreplace({sym: s}), c)
        msym = s
    else:
        dum = Symbol('lambda')
        if dum in cond.free_symbols or dum in c.free_symbols:
            dum = Dummy(str(dum))
        merged_cond = And(cond.xreplace({sym: dum}), c.xreplace({s: dum}))
        msym = dum
    if not isinstance(msym, Symbol):
        probe = Dummy('lambda')
        if probe not in merged_cond.xreplace({msym: probe}).free_symbols:
            return (MERGE_REFUSED, 0)
    return (sym_id(msym), obj_id(inner_base))


def in_build_domain(b):
    """mapping.md §3.1's declared scope for the deep `build` model: every base
    domain the operation can hand the constructor. The model carries the base
    domain's SHAPE (empty / explicitly listed / itself a restricted object /
    plain) plus the folded outcome of the two shape-specific decisions, so all
    four of `__new__`'s dispatches -- the EmptySet short-circuit, the FiniteSet
    sifting, the condition-MERGING branch that can rename the bound variable,
    and the plain fall-through -- are MODELLED rather than excluded. Nothing is
    excluded by base shape; the guard is only that the substituted domain is a
    `Set` at all, which is the constructor's own precondition (line 141)."""
    return isinstance(b, Set)


def agrees(shadow, real, base_after, btag):
    """Compare the shadow's Result0 against the abstracted oracle value on
    exactly the fields `replace_free_parameter`'s Ensures observe.

    `cond == COND_OPEN` is part of the K_SET obligation on every base-domain
    shape but the merge: there the constructor conjoins the two predicates and
    falls through with no further reduction, so the object it delivers really
    can carry an identically false predicate, and the spec claims no truth
    status for it (measured -- see the BRIDGE note)."""
    rk, rsym, rbase, rcond = abstract_result(real, base_after)
    if shadow.kind != rk:
        return False
    if rk == K_EMPTY:
        return True                      # Ensures pins only kind == K_EMPTY
    if rk == K_BASE:
        return shadow.base == rbase      # ... and base == base_after
    if not (shadow.sym == rsym and shadow.base == rbase):
        return False
    if btag == BASE_MERGED:
        return True
    return shadow.cond == COND_OPEN and rcond == COND_OPEN


# ---------------------------------------------------------------------------
# Input generation
# ---------------------------------------------------------------------------
x = Symbol('x'); y = Symbol('y'); z = Symbol('z'); w = Symbol('w')
k = Symbol('k'); m = Symbol('m'); t = Symbol('t')
n_neg = Symbol('n', negative=True)
p_pos = Symbol('p', positive=True)

BINDERS = [x, z, w, k, m, t, Symbol('a'), Symbol('b'), n_neg, p_pos]
FREES = [y, Symbol('q'), Symbol('u'), Symbol('v')]
# Replacement values. The `is_zero`-decided symbols and the bare 1/0 are the
# ones whose truth only the constructor's own normalization settles, so they
# exercise the tag bridge's normalization on the bare-symbol predicates below.
NEWS = [Rational(1, 3), Rational(-2, 5), S.One, S.Zero, S.Half, S(5), S(-7),
        Symbol('r'), Symbol('rp', positive=True), Symbol('rn', negative=True),
        z, w, p_pos, n_neg, Symbol('rz', zero=True),
        Symbol('rnz', nonzero=True)]

N_CONDS = 11
N_BASES = 22


def make_cond(sym, fv, i):
    if i == 0:
        return sym < fv
    if i == 1:
        return Contains(fv, Interval(-1, 1))
    if i == 2:
        return Contains(fv, Interval(0, 5))
    if i == 3:
        return Eq(Mod(sym, 2), 0) & Contains(fv, Interval(-1, 1))
    if i == 4:
        return Eq(sym, fv)
    if i == 5:
        return (sym < fv) | Contains(fv, Interval(0, oo))
    if i == 6:
        return fv < sym
    # Predicates that are (or contain) a bare symbol: an undecided symbol is a
    # restriction, but once the replacement makes it a number, or a symbol whose
    # vanishing its assumptions decide, the construction DECIDES it. Their truth
    # status is exactly the one only the constructor's normalization settles.
    if i == 7:
        return fv
    if i == 8:
        return And(fv, sym < 1)
    if i == 9:
        return fv | Contains(sym, Interval(0, 5))
    return Contains(fv, S.Integers)


def make_base(fv, i):
    if i == 0:
        return Interval(-oo, 0)
    if i == 1:
        return Interval(0, oo)
    if i == 2:
        return Interval(-1, 1)
    if i == 3:
        return S.Integers
    if i == 4:
        return S.Reals
    if i == 5:
        return S.Naturals
    if i == 6:
        return imageset(Lambda(k, 2 * k * pi + asin(fv)), S.Integers)
    if i == 7:
        return imageset(Lambda(m, m * pi + sin(fv)), S.Integers)
    if i == 8:
        return Interval(0, fv)
    if i == 9:
        return Interval(fv, fv + 2)
    # base-domain shapes the model now covers: an Interval that COLLAPSES to
    # the empty domain under the replacement, explicit finite listings whose
    # members the predicate decides one by one, and an already-empty domain.
    if i == 10:
        return Interval(fv, 1)
    if i == 11:
        return FiniteSet(1, 2, 3)
    if i == 12:
        return FiniteSet(1, 2, z)
    if i == 13:
        return FiniteSet(fv, 2, 3)
    if i == 14:
        return FiniteSet(fv, z, w)
    if i == 15:
        return FiniteSet(fv)
    if i == 16:
        return S.EmptySet
    if i == 17:
        return Interval(0, fv, True, True)
    if i == 18:
        return FiniteSet(S.Half, Rational(1, 3), z)
    # Base domains that COLLAPSE under the replacement to a bare restricted
    # object, so the constructor's condition-MERGING branch
    # (conditionset.py:161-179) is what runs: a Union whose interval part
    # empties out whenever the replacement is negative. The three inner objects
    # differ in which variables their predicate mentions, which is what the
    # merge's four binder branches turn on: `x + z > 0` mentions the outer
    # binder x (so the merge adopts z, or mints a name when the outer predicate
    # mentions z too), `z < 2` mentions neither (so the outer binder is kept),
    # and the third also moves the merged object onto a different inner domain.
    if i == 19:
        return Union(Interval(0, fv), ConditionSet(z, x + z > 0, S.Reals))
    if i == 20:
        return Union(Interval(0, fv), ConditionSet(z, z < 2, S.Reals))
    return Union(Interval(0, fv),
                 ConditionSet(w, w + x > 0, Interval(-3, 3)))


def build_pool():
    """Real ConditionSets whose bound symbol survived the constructor, paired
    with the free symbol that occurs in them."""
    pool = []
    for sym in BINDERS:
        for fv in FREES:
            for ci in range(N_CONDS):
                for bi in range(N_BASES):
                    try:
                        cs = ConditionSet(sym, make_cond(sym, fv, ci),
                                          make_base(fv, bi))
                    except Exception:
                        continue
                    # branch guards + declared carrier domain: a genuine
                    # ConditionSet whose bound variable is a Symbol (hence an
                    # Expr, the code's own guard) that the constructor did not
                    # rename
                    if not isinstance(cs, ConditionSet):
                        continue
                    if not isinstance(cs.sym, Symbol) or cs.sym != sym:
                        continue
                    pool.append((cs, fv))
    return pool


def boundary_cases():
    """Boundary inputs: the two documented regressions plus every impl branch
    (COND_FALSE / COND_TRUE / COND_OPEN) over every base-domain family."""
    cases = []
    img_y = imageset(Lambda(k, 2 * k * pi + asin(y)), S.Integers)
    # issue 17341 headline (mapping.md §3.2): condition collapses to true over
    # an ImageSet base.
    cases.append(("issue17341",
                  ConditionSet(x, Contains(y, Interval(-1, 1)), img_y),
                  y, Rational(1, 3)))
    # F2P regression: ConditionSet(n, n < x, Interval(-oo, 0)).subs(x, p).
    cases.append(("f2p_neg_interval",
                  ConditionSet(n_neg, n_neg < x, Interval(-oo, 0)), x, p_pos))
    cases.append(("f2p_pos_interval",
                  ConditionSet(n_neg, n_neg < x, Interval(0, oo)), x, p_pos))
    # base domain COLLAPSES to the empty domain while the predicate stays a
    # non-trivial restriction -> the real result is the empty domain
    cases.append(("base_collapses_empty",
                  ConditionSet(x, x < y, Interval(0, y)), y, S(-1)))
    cases.append(("base_collapses_empty2",
                  ConditionSet(x, x < y, Interval(y, 1)), y, S(5)))
    # explicit finite listing: the predicate is decided member by member
    cases.append(("listed_all_decided",
                  ConditionSet(x, Eq(x, y), FiniteSet(1, 2, 3)), y, S(2)))
    cases.append(("listed_none_qualify",
                  ConditionSet(x, x < y, FiniteSet(1, 2, 3)), y, S(-1)))
    cases.append(("listed_some_undecided",
                  ConditionSet(x, x < y, FiniteSet(1, 2, z)), y, S(2)))
    cases.append(("listed_all_undecided",
                  ConditionSet(x, x < y, FiniteSet(1, 2, 3)), y, z))
    # an already-empty base domain
    cases.append(("base_empty",
                  ConditionSet(x, x < y, Interval(3, 1)), y, S(2)))
    # Predicates whose truth ONLY the constructor's own normalization settles:
    # a bare symbol predicate that the replacement turns into a number, or into
    # a symbol whose vanishing its assumptions decide. The construction reduces
    # on them exactly as it does on an already-true / already-false predicate,
    # so the modeled reduction must tag them TRUE / FALSE, not OPEN.
    for bi in (4, 3, 0, 5, 6, 11):
        base = make_base(y, bi)
        cases.append(("symcond_one_base%d" % bi,
                      ConditionSet(x, y, base), y, S.One))
        cases.append(("symcond_zero_base%d" % bi,
                      ConditionSet(x, y, base), y, S.Zero))
        cases.append(("symcond_nonzero_base%d" % bi,
                      ConditionSet(x, y, base), y, Symbol('c', nonzero=True)))
        cases.append(("symcond_iszero_base%d" % bi,
                      ConditionSet(x, y, base), y, Symbol('d', zero=True)))
        cases.append(("symcond_undecided_base%d" % bi,
                      ConditionSet(x, y, base), y, Symbol('e')))
        cases.append(("symcond_and_base%d" % bi,
                      ConditionSet(x, And(y, x < 1), base), y, S.One))
    # a predicate handed over as an explicit listing of expressions: the
    # construction reads it as the conjunction of their vanishing
    cases.append(("listed_predicate_false",
                  ConditionSet(x, y, S.Reals), y, FiniteSet(1, 2)))
    cases.append(("listed_predicate_true",
                  ConditionSet(x, y, S.Reals), y, FiniteSet(0)))
    cases.append(("listed_predicate_open",
                  ConditionSet(x, y, S.Reals), y, FiniteSet(x - 1)))
    # Shapes on which the real operation DELIVERS NOTHING, so the model makes
    # no claim about them and they are counted as out-of-domain (see DOMAIN):
    # a predicate the construction refuses to read as a truth value, and a
    # replacement on which the substitution itself raises. Both are recorded to
    # show the exclusions are exercised rather than merely declared.
    cases.append(("predicate_refused_number",
                  ConditionSet(x, y, S.Reals), y, S(2)))
    cases.append(("subs_raises_nan",
                  ConditionSet(x, x < y, S.Reals), y, S.NaN))
    cases.append(("subs_raises_imaginary",
                  ConditionSet(x, x < y, S.Reals), y, S.ImaginaryUnit))
    # the replacement collides with the bound variable: the predicate is
    # decided by that collision, and the result must still be keyed on the
    # original bound variable / be the base domain, never a set on `new`
    cases.append(("new_is_binder_true",
                  ConditionSet(x, Eq(x, y), S.Reals), y, x))
    cases.append(("new_is_binder_false",
                  ConditionSet(x, x < y, S.Reals), y, x))
    # The condition-MERGE: a base domain that COLLAPSES under the replacement to
    # a bare restricted object, in each of the four binder outcomes the merge
    # can settle on, plus the two reductions that pre-empt it and the
    # no-further-reduction quirk. Measured against the real constructor:
    #   x<-1 over ConditionSet(z, x+z>0, Reals) -> ConditionSet(z, ...) : adopts z
    #   x<-1 over ConditionSet(z, z<2,    Reals) -> ConditionSet(x, ...) : keeps x
    #   z<-1 over ConditionSet(z, x+z>0,  Reals) -> ConditionSet(z, ...) : sym == s
    #   (x<-1)&(x<z) over the same           -> ConditionSet(lambda, ...)
    #   ... and with a symbol literally named `lambda` already present, a Dummy.
    lam = Symbol('lambda')
    mb1 = Union(Interval(0, y), ConditionSet(z, x + z > 0, S.Reals))
    mb2 = Union(Interval(0, y), ConditionSet(z, z < 2, S.Reals))
    mb3 = Union(Interval(0, y), ConditionSet(w, w + x > 0, Interval(-3, 3)))
    mb4 = Union(Interval(0, y), ConditionSet(z, z >= -1, S.Reals))
    cases.append(("merge_adopts_inner_sym",
                  ConditionSet(x, x < y, mb1), y, S(-1)))
    cases.append(("merge_keeps_outer_sym",
                  ConditionSet(x, x < y, mb2), y, S(-1)))
    cases.append(("merge_inner_base",
                  ConditionSet(x, x < y, mb3), y, S(-1)))
    cases.append(("merge_sym_is_inner",
                  ConditionSet(z, z < y, mb1), y, S(-1)))
    cases.append(("merge_mints_lambda",
                  ConditionSet(x, (x < z) & (x < y), mb1), y, S(-1)))
    cases.append(("merge_mints_dummy",
                  ConditionSet(x, (x < z) & (lam > 0) & (x < y), mb1),
                  y, S(-1)))
    # the predicate decides before the merge is reached: true hands back the
    # inner restricted object ITSELF (a pass-through, K_BASE), false empties
    cases.append(("merge_pre_empted_true",
                  ConditionSet(x, Contains(y, Interval(-2, 0)), mb1), y, S(-1)))
    cases.append(("merge_pre_empted_false",
                  ConditionSet(x, Contains(y, Interval(1, 2)), mb1), y, S(-1)))
    # no further reduction after the merge: the conjoined predicate is
    # identically false and the restricted object STILL stands
    cases.append(("merge_false_predicate_stands",
                  ConditionSet(z, z < y, mb4), y, S(-1)))
    # a negative replacement SYMBOL collapses the interval part too
    cases.append(("merge_negative_symbol",
                  ConditionSet(x, x < y, mb1), y, n_neg))
    # The merge ADOPTS a non-`Symbol` inner bound variable (branch 3), so the
    # constructor's own check on the settled bound variable
    # (conditionset.py:181-185) is what decides -- reached from a caller whose
    # OWN bound variable is an ordinary Symbol. Both outcomes of that check are
    # covered, because it is not a test of `isinstance(_, Symbol)`:
    #   * the conjoined predicate keeps a trace of the compound bound variable
    #     => ACCEPTED, and the object stands keyed on that compound expression
    #     (measured: ConditionSet(x + 1, (z < 5) & (x + 1 <= 0) & Contains(...),
    #     Reals));
    #   * the conjoined predicate collapses so no trace survives => REFUSED
    #     with ValueError, and there is no object to compare.
    for lbl, binder, icond in [
            ("contains", x + 1, (z < 5) & Contains(x + 1, Interval(0, 1))),
            ("sin", x + 1, (z < 5) & (sin(x + 1) > 0)),
            ("pow", x**2, (z < 5) & (sin(x**2) > 0)),
            ("mul", 2 * x, (z < 5) & Contains(2 * x, Interval(0, 1))),
    ]:
        cases.append(("merge_adopts_compound_binder_kept_%s" % lbl,
                      ConditionSet(z, z <= 0,
                                   Union(Interval(0, y),
                                         ConditionSet(binder, icond, S.Reals))),
                      y, S(-1)))
    for lbl, binder, icond in [
            ("add", x + 1, (z < 5) & (x + 1 > 0)),
            ("mul", 2 * x, (z < 5) & (2 * x > 0)),
            ("affine", 2 * x + 3, (z < 5) & (2 * x + 3 > 0)),
    ]:
        cases.append(("merge_adopts_compound_binder_refused_%s" % lbl,
                      ConditionSet(z, z <= 0,
                                   Union(Interval(0, y),
                                         ConditionSet(binder, icond, S.Reals))),
                      y, S(-1)))
    # ... and the same compound-binder inner object under a predicate that
    # collapses to TRUE, which pre-empts the merge at line 146 and hands the
    # inner object straight back: the constructor's bound-variable check is
    # never reached, so this input is DELIVERED and must stay in scope.
    cases.append(("merge_pre_empted_true_compound_binder",
                  ConditionSet(x, Contains(y, Interval(-2, 0)),
                               Union(Interval(0, y),
                                     ConditionSet(x + 1, (z < 5) & (x + 1 > 0),
                                                  S.Reals))),
                  y, S(-1)))
    for bi in range(N_BASES):
        base = make_base(y, bi)
        # COND_TRUE: Contains(y, [-1, 1]) with y -> 1/3
        cases.append(("true_base%d" % bi,
                      ConditionSet(x, Contains(y, Interval(-1, 1)), base),
                      y, Rational(1, 3)))
        # COND_FALSE: the same predicate with y -> 5
        cases.append(("false_base%d" % bi,
                      ConditionSet(x, Contains(y, Interval(-1, 1)), base),
                      y, S(5)))
        # COND_OPEN: x < y with y -> w
        cases.append(("open_base%d" % bi,
                      ConditionSet(x, x < y, base), y, w))
    out = []
    for label, cs, old, new in cases:
        if isinstance(cs, ConditionSet) and isinstance(cs.sym, Symbol) \
                and cs.sym != old:
            out.append((label, cs, old, new))
    return out


def _refusal(cs, old, new, exc, what):
    """A folded-in unchanged callee refused this input, so the construction
    delivers nothing. NOT assumed: the oracle must refuse it with the identical
    exception, else this is a real disagreement."""
    try:
        cs._eval_subs(old, new)
    except Exception as oexc:
        if type(oexc) is type(exc) and str(oexc) == str(exc):
            return ("no-result", None, None)
        return ("diff", "%s raised %r but the real method raised %r"
                % (what, exc, oexc), None)
    return ("diff", "%s raised %r but the real method delivered a result"
            % (what, exc), None)


def check_one(cs, old, new):
    """Run one comparison. Returns (status, detail, info) where status is
    'ok' | 'diff' | 'subs-diff' | 'out-of-domain' | 'no-tag' | 'binder' |
    'no-result' | 'merge-refused' | 'raise', and info is (cond tag, base-shape tag, result kind,
    merge-renamed flag) for a comparison that was made (None otherwise). The
    last element records that the merge did NOT carry the outer bound variable
    over: those are the comparisons on which the new merged clause says
    something the plain-base clause does not, so they are counted and a run
    without them fails."""
    self_sym = cs.sym
    if old == self_sym:                                # branch guard
        return ("out-of-domain", None, None)
    if not isinstance(self_sym, Expr):    # the modeled branch's own guard
        return ("out-of-domain", None, None)
    if not isinstance(self_sym, Symbol):
        # declared carrier domain (mapping.md §2 row 1): the bound variable is
        # a Symbol. A non-Symbol Expr binder passes the code's own guard just
        # above but the construction may refuse it outright, delivering nothing
        # (see DOMAIN).
        return ("binder", None, None)
    try:
        cond_after = cs.condition.subs(old, new)       # real Basic.subs (R)
        base_after = cs.base_set.subs(old, new)        # real Basic.subs (R)
    except Exception:
        # The replacement makes the real substitution itself raise (e.g. a
        # comparison against `nan` / `I`), and the modeled branch performs
        # exactly these two calls, so the real operation delivers no object
        # either -- measured: `cs._eval_subs(old, new)` and `cs.subs(old, new)`
        # raise the identical exception on every such input. There is nothing to
        # compare; counted and reported as out-of-domain (see DOMAIN).
        return ("no-result", None, None)
    if not in_build_domain(base_after) or not in_build_domain(cs.base_set):
        return ("out-of-domain", None, None)
    tag = cond_tag(cond_after)                         # Requires by construction
    if tag is None:
        # the constructor refuses to read this predicate as a truth value, so
        # it has no COND_* tag and the model admits no such input (see DOMAIN)
        return ("no-tag", None, None)
    assert tag in (COND_FALSE, COND_TRUE, COND_OPEN)
    btag = base_tag(base_after)                        # base-domain SHAPE (R)
    assert btag in (BASE_EMPTY, BASE_LISTED, BASE_PLAIN, BASE_MERGED)
    # the member-by-member decision over an explicit listing, folded in from
    # the repo's own sift/fuzzy_bool exactly as the two .subs calls are. It is
    # run on the NORMALIZED predicate, which is the one the constructor sifts
    # with (and the one it stores in the surviving restricted object).
    listed_kind, listed_base = K_EMPTY, 0
    if tag == COND_OPEN and btag == BASE_LISTED:
        try:
            listed_kind, listed_base = listed_outcome(
                self_sym, normalized_cond(cond_after), base_after)
        except Exception as exc:
            # The member-by-member decision is the real constructor's OWN
            # (`sift` + `fuzzy_bool` over the same normalized predicate), so an
            # input it refuses is one on which the construction delivers
            # nothing -- checked against the oracle, never assumed.
            return _refusal(cs, old, new, exc, "listed reduction")
    # the condition-MERGE, folded in from conditionset.py:161-179 exactly as the
    # listing decision is, and run on the NORMALIZED predicate because the
    # constructor normalizes (line 136) before it merges (line 161).
    merged_sym, merged_base = 0, 0
    if tag == COND_OPEN and btag == BASE_MERGED:
        try:
            merged_sym, merged_base = merged_outcome(
                self_sym, normalized_cond(cond_after), base_after)
        except Exception as exc:
            return _refusal(cs, old, new, exc, "condition merge")
        if merged_sym == MERGE_REFUSED:
            # The constructor refuses the bound variable the merge settled on
            # (conditionset.py:181-185), so it delivers no domain -- and the
            # spec PINS that outcome as K_REFUSED rather than leaving it open.
            # So this is a COMPARISON, not an exclusion: the shadow must say
            # K_REFUSED here, and the real method must really refuse this input
            # with that very exception (checked via _refusal, never assumed).
            # Either half failing is a genuine disagreement.
            shadow = replace_free_parameter(
                obj_id(self_sym), obj_id(new), tag, obj_id(base_after), btag,
                listed_kind, listed_base, merged_sym, merged_base)
            if shadow.kind != K_REFUSED:
                return ("diff",
                        "merge refused but shadow delivered kind=%d"
                        % (shadow.kind,), None)
            st, detail, _ = _refusal(
                cs, old, new,
                ValueError('non-symbol dummy not recognized in condition'),
                "merge-settled bound variable")
            return ("merge-refused" if st == "no-result" else st, detail, None)

    shadow = replace_free_parameter(obj_id(self_sym), obj_id(new), tag,
                                    obj_id(base_after), btag, listed_kind,
                                    listed_base, merged_sym, merged_base)
    try:
        real = cs._eval_subs(old, new)                 # PATCHED repo method
        public = cs.subs(old, new)                     # reachability check
    except Exception as exc:
        return ("raise", "oracle raised: %r" % (exc,), None)

    if shadow.kind == K_REFUSED:
        # A refusal claimed on an input the real method answers would be the
        # mirror-image unfaithfulness, so it is checked in this direction too.
        return ("diff",
                "shadow refused but oracle delivered %r" % (real,), None)
    if not agrees(shadow, real, base_after, btag):
        return ("diff",
                "kind/sym/base mismatch: tag=%d btag=%d"
                " shadow=(kind=%d,sym=%d,base=%d)"
                " oracle=%r %r" % (tag, btag, shadow.kind, shadow.sym,
                                   shadow.base,
                                   abstract_result(real, base_after), real),
                None)
    if public != real and not (isinstance(public, ConditionSet)
                               and isinstance(real, ConditionSet)
                               and public.dummy_eq(real)):
        return ("subs-diff",
                "public .subs disagrees with _eval_subs: %r vs %r"
                % (public, real), None)
    renamed = btag == BASE_MERGED and merged_sym != obj_id(self_sym)
    return ("ok", None,
            (tag, btag, abstract_result(real, base_after)[0], renamed))


def main():
    rng = random.Random(SEED)
    pool = build_pool()
    if not pool:
        print("G-CONF ERROR: empty input pool")
        return 1

    checked = 0
    rejected = 0
    no_tag = 0
    binder = 0
    no_result = 0
    merge_refused = 0
    raised = 0
    tags = {COND_FALSE: 0, COND_TRUE: 0, COND_OPEN: 0}
    kinds = {K_EMPTY: 0, K_BASE: 0, K_SET: 0}
    btags = {BASE_EMPTY: 0, BASE_LISTED: 0, BASE_PLAIN: 0, BASE_MERGED: 0}
    merge_renamed = 0
    failures = []

    def record(label, cs, old, new):
        nonlocal checked, rejected, no_tag, binder, no_result, raised
        nonlocal merge_renamed, merge_refused
        status, detail, info = check_one(cs, old, new)
        if status == "out-of-domain":
            rejected += 1
            return
        if status == "no-tag":          # constructor refuses the predicate
            no_tag += 1
            return
        if status == "binder":          # bound variable is not a Symbol
            binder += 1
            return
        if status == "no-result":       # the substitution itself raises
            no_result += 1
            return
        if status == "merge-refused":
            # the constructor refuses the bound variable the merge settled on
            merge_refused += 1
            return
        if status == "raise":
            raised += 1
            failures.append((label, cs, old, new, detail))
            return
        checked += 1
        if info is not None:            # branch coverage of a comparison made
            tags[info[0]] += 1
            btags[info[1]] += 1
            kinds[info[2]] += 1
            merge_renamed += 1 if info[3] else 0
        if status != "ok":
            failures.append((label, cs, old, new, detail))

    # 1. boundary cases. `n_boundary` counts the ones actually COMPARED; the
    # deliberately excluded shapes land in the out-of-domain counters instead.
    n_boundary_total = 0
    for label, cs, old, new in boundary_cases():
        record(label, cs, old, new)
        n_boundary_total += 1
    n_boundary = checked

    # 2. seeded fuzz to the target count
    attempts = 0
    while checked < N_TARGET and attempts < N_TARGET * 8:
        attempts += 1
        cs, fv = pool[rng.randrange(len(pool))]
        old = fv if rng.random() < 0.9 else FREES[rng.randrange(len(FREES))]
        new = NEWS[rng.randrange(len(NEWS))]
        record("fuzz%d" % attempts, cs, old, new)
        if len(failures) >= 5:
            break

    if failures:
        print("G-CONF FAIL: %d disagreement(s) over %d comparisons (seed=%d)"
              % (len(failures), checked, SEED))
        for label, cs, old, new, detail in failures[:5]:
            print("  [%s] cs=%r old=%r new=%r" % (label, cs, old, new))
            print("        %s" % detail)
        print('{"checked": %d, "disagreements": %d, "seed": %d, '
              '"shadow": "direct (contract-stripped impl region)"}'
              % (checked, len(failures), SEED))
        return 1

    if checked < N_TARGET:
        print("G-CONF FAIL: only %d/%d comparisons reached (seed=%d)"
              % (checked, N_TARGET, SEED))
        return 1

    if merge_refused == 0:
        # The merge can ADOPT a non-Symbol inner bound variable, which the
        # constructor's own check (conditionset.py:181-185) then refuses. That
        # leg is the one the shipped spec previously claimed a delivered object
        # for, so a run that never reached it does not measure the repair.
        print("G-CONF FAIL: the merge-settled-bound-variable refusal was never "
              "reached, so the model's scope for it is untested")
        return 1

    if btags[BASE_MERGED] == 0 or merge_renamed == 0:
        # The merge is the shape whose bound variable the model claims the
        # REDUCTION settles rather than the caller, so a run that never reached
        # it -- or reached it only where it happens to keep the outer variable,
        # which the plain-base clause would already have got right -- measures a
        # strictly weaker claim than the one shipped.
        print("G-CONF FAIL: the condition-MERGING base-domain shape was "
              "compared %d time(s), of which %d actually renamed the bound "
              "variable" % (btags[BASE_MERGED], merge_renamed))
        return 1

    print("G-CONF OK: model.py impl shadow (replace_free_parameter -> build, "
          "copied verbatim minus contracts, over the int-id/truth-tag carrier) "
          "agrees with the real patched ConditionSet._eval_subs on %d "
          "comparisons (%d of %d boundary inputs + fuzz; branch coverage "
          "COND_FALSE=%d "
          "COND_TRUE=%d COND_OPEN=%d over base-domain shapes BASE_EMPTY=%d "
          "BASE_LISTED=%d BASE_PLAIN=%d BASE_MERGED=%d (of which %d did not "
          "carry the outer bound variable over) -> K_EMPTY=%d K_BASE=%d "
          "K_SET=%d; "
          "out-of-domain and reported, not dropped: %d samples outside "
          "mapping.md §3.1's declared base-domain scope (which now excludes no "
          "base shape at all, so this is 0 by measurement), %d whose predicate "
          "the construction refuses to read as a truth value (no COND_* tag), "
          "%d with a non-Symbol bound variable supplied by the caller, %d where "
          "the substitution "
          "itself raises so no object is delivered), seed=%d; and, checked in "
          "BOTH directions rather than excluded, %d where the merge settled on "
          "a bound variable the construction then refuses: on each the shadow "
          "was required to deliver the pinned K_REFUSED and the real method was "
          "required to raise that very refusal. 0 disagreements."
          % (checked, n_boundary, n_boundary_total,
             tags[COND_FALSE], tags[COND_TRUE], tags[COND_OPEN],
             btags[BASE_EMPTY], btags[BASE_LISTED], btags[BASE_PLAIN],
             btags[BASE_MERGED], merge_renamed,
             kinds[K_EMPTY], kinds[K_BASE], kinds[K_SET],
             rejected, no_tag, binder, no_result, SEED, merge_refused))
    print('{"checked": %d, "boundary": %d, "boundary_total": %d, '
          '"domain_rejected": %d, '
          '"predicate_refused": %d, "nonsymbol_binder": %d, '
          '"merge_refused_binder": %d, "substitution_raises": %d, '
          '"cond_false": %d, "cond_true": %d, "cond_open": %d, '
          '"base_empty": %d, "base_listed": %d, "base_plain": %d, '
          '"base_merged": %d, "merge_renamed_binder": %d, '
          '"disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)", '
          '"oracle": "ConditionSet._eval_subs (patched, called)"}'
          % (checked, n_boundary, n_boundary_total, rejected, no_tag, binder,
             merge_refused, no_result, tags[COND_FALSE], tags[COND_TRUE], tags[COND_OPEN],
             btags[BASE_EMPTY], btags[BASE_LISTED], btags[BASE_PLAIN],
             btags[BASE_MERGED], merge_renamed, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
