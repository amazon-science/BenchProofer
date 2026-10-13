"""G-AX soundness check for sympy__sympy-19495.

This bundle consumes NO @ContractOnly axiom. Two operations are modelled
DEEPLY and are validated here against the real SymPy code (A-reference):

  1. `build(sym, cond, base, base_kind, listed_kind, listed_base, merged_sym,
     merged_base)` -- the reduction rule of the solution set constructor. Which
     reduction applies depends on the predicate's truth AND on the base
     domain's SHAPE: a false predicate -> the empty domain; an empty base
     domain -> the empty domain; a true predicate -> the base domain itself; an
     explicitly listed base domain -> the member-by-member outcome; a base
     domain that is itself a restricted object -> the MERGE of the two
     restrictions, over the inner base domain and keyed on the bound variable
     the merge settles on; otherwise a restricted object keyed on `sym`. This
     mirrors `ConditionSet.__new__`'s reductions
     (`condition is S.false -> S.EmptySet`, `condition is S.true -> base_set`,
     `isinstance(base_set, EmptySet) -> base_set`, the `FiniteSet` sifting, the
     `isinstance(base_set, cls)` merging branch at lines 161-179, else a
     `ConditionSet`), which the patch does NOT change.

  2. `replace_free_parameter(self_sym, new, cond_after, base_after, base_kind,
     listed_kind, listed_base, merged_sym, merged_base)` -- the FREE-symbol
     branch of
     `ConditionSet._eval_subs` AFTER the patch: it rebuilds the canonical
     object keyed on the ORIGINAL bound symbol (never `new`) under the same
     shape-dependent reduction, so a predicate that collapses to true yields
     the base domain.

We exercise the real objects over boundary + fuzz inputs and assert every
observation agrees with the model's Ensures. Sections [3] and [4] pin the point
mapping.md §1.1 makes: the truth status the model's `cond` carrier abstracts is
the one the CONSTRUCTION assigns, after its own listing rewrite and
`as_Boolean` normalization -- not the shape of the expression as written -- and
they also pin the two shapes mapping.md §3.1 declares outside the model.
Section [5] pins the merging branch: the four binder outcomes it can settle on,
the fact that it stands over the INNER base domain, that the two truth
reductions pre-empt it, and that it performs no further reduction (so the object
it delivers can carry an identically false predicate).
stdlib + sympy only; exit 0 iff sound. (Run in the instance's container,
post-patch, where sympy is importable.)
"""
import sys
import itertools

from sympy import (S, Symbol, Dummy, Interval, Contains, ConditionSet, Lambda,
                   pi, asin, oo, imageset, Eq, And, FiniteSet, Union)
from sympy.sets.sets import Set, EmptySet
from sympy.core.numbers import Rational
from sympy.core.logic import fuzzy_bool
from sympy.logic.boolalg import as_Boolean
from sympy.utilities.iterables import sift

# Model tags (kept in sync with model.py).
COND_FALSE, COND_TRUE, COND_OPEN = 0, 1, 2
K_EMPTY, K_BASE, K_SET = 0, 1, 2
BASE_EMPTY, BASE_LISTED, BASE_PLAIN, BASE_MERGED = 0, 1, 2, 3


def classify_result(res, base):
    """Map a real subs/ConditionSet result back to the model's (kind, sym?).

    `kind` classifies the REDUCTION's outcome, not the Python type of the value:
    a result equal to the base domain is K_BASE ("the base domain passes
    through") even when that domain is itself a restricted object, which is
    exactly what `condition is S.true` hands back (conditionset.py:146)."""
    if res == S.EmptySet or res is S.EmptySet:
        return (K_EMPTY, None)
    if base is not None and res == base:
        return (K_BASE, None)
    if isinstance(res, ConditionSet):
        return (K_SET, res.sym)
    # not a ConditionSet and not empty => the base domain passed through
    return (K_BASE, None)


def same_binder(a, b):
    """Bound-variable identity as the model's `sym` carrier sees it: two fresh
    internal names are the same carrier value. The merge can mint
    `Dummy('lambda')` (conditionset.py:174-179), an object no caller can name
    and whose identity differs between evaluations; the load-bearing
    distinction (a result keyed on the replacement value) is a named Symbol."""
    if isinstance(a, Dummy) and isinstance(b, Dummy):
        return True
    return a == b


def normalized_cond(c):
    """The predicate as `ConditionSet.__new__` reads it BEFORE it branches on
    the truth: an explicit listing of expressions becomes the conjunction of
    their vanishing (conditionset.py:125-134), then `as_Boolean` turns a number
    or an assumption-decided symbol into a truth value (line 136 ->
    boolalg.py:20-58). None when the construction refuses the predicate."""
    if isinstance(c, FiniteSet):
        c = And(*[Eq(lhs, 0) for lhs in c])
    try:
        return as_Boolean(c)
    except TypeError:
        return None


def cond_tag(c):
    """The truth status the CONSTRUCTION assigns to the predicate -- the one it
    branches on at conditionset.py:144/146 -- i.e. applied to the normalized
    predicate, not to the expression as written (mapping.md §1.1). None when the
    construction refuses to read it as a truth value at all."""
    n = normalized_cond(c)
    if n is None:
        return None
    if n is S.true:
        return COND_TRUE
    if n is S.false:
        return COND_FALSE
    return COND_OPEN


def base_tag(b):
    """The base domain's SHAPE, which selects the constructor's reduction: the
    four values are the four shapes `__new__` dispatches on (empty at line 148,
    an explicit listing at 152, a restricted object to merge with at 161, else
    the fall-through)."""
    if b is S.EmptySet or isinstance(b, EmptySet):
        return BASE_EMPTY
    if isinstance(b, FiniteSet):
        return BASE_LISTED
    if isinstance(b, ConditionSet):
        return BASE_MERGED
    return BASE_PLAIN


def merged_outcome(sym, cond, cbase):
    """The MERGE the constructor performs when the base domain is itself a
    restricted object, replayed line for line from conditionset.py:161-179, as
    the model's (merged_sym, merged_base) carriers. No truth status is replayed
    for the conjoined predicate: the branch falls through to `Basic.__new__`
    (line 187) with no further reduction, so the model claims none."""
    s, c, inner_base = cbase.args
    if sym == s:
        msym = sym
    elif sym not in c.free_symbols:
        msym = sym
    elif s not in cond.free_symbols:
        msym = s
    else:
        dum = Symbol('lambda')
        if dum in cond.free_symbols or dum in c.free_symbols:
            dum = Dummy(str(dum))
        msym = dum
    return (msym, inner_base)


def listed_outcome(sym, cond, fbase):
    """The member-by-member decision the real constructor performs over an
    explicit finite listing, replayed with the repo's own sift/fuzzy_bool."""
    sifted = sift(fbase, lambda _: fuzzy_bool(cond.subs(sym, _)))
    if sifted[None]:
        undecided = FiniteSet(*sifted[None])
        if not sifted[True]:
            return (K_SET, undecided)
        return (K_BASE, Union(FiniteSet(*sifted[True]),
                              ConditionSet(sym, cond, undecided)))
    if not sifted[True]:
        return (K_EMPTY, None)
    return (K_BASE, FiniteSet(*sifted[True]))


fail = 0


def check(label, ok):
    global fail
    if not ok:
        fail += 1
        print("VIOLATION:", label)


# ---------------------------------------------------------------------------
# 1. Validate the `build` reduction rule against ConditionSet.__new__.
# Pick a fixed bound symbol `s` and a base domain; vary the predicate's truth.
print("[1] build() == ConditionSet.__new__ reduction")
x = Symbol('x')
y = Symbol('y')
z_ = Symbol('z')
# Every base-domain SHAPE the model distinguishes, so no reduction branch of
# __new__ is left unexercised: plain (non-enumerated) domains, an EMPTY domain
# (the short-circuit), and explicit finite listings (the sifting branch).
plain_bases = [S.Integers, S.Reals, Interval(0, oo), Interval(-1, 1)]
empty_bases = [S.EmptySet, Interval(3, 1), Interval(0, 0, True, True)]
listed_bases = [FiniteSet(1, 2, 3), FiniteSet(1, 2, z_), FiniteSet(z_),
                FiniteSet(Rational(1, 3), S.Half)]
# base domains that are THEMSELVES restricted objects: the merging branch. The
# three differ in which variables the inner predicate mentions and in the inner
# base domain, which is what the merge's binder branches turn on.
v_ = Symbol('v')
merged_bases = [ConditionSet(z_, x + z_ > 0, S.Reals),
                ConditionSet(z_, z_ < 2, S.Reals),
                ConditionSet(v_, v_ + x > 0, Interval(-3, 3))]

for base in plain_bases:
    # false predicate -> empty
    r = ConditionSet(x, S.false, base)
    k, sym = classify_result(r, base)
    check("build false->EMPTY %r" % base, k == K_EMPTY)
    # true predicate -> base domain
    r = ConditionSet(x, S.true, base)
    k, sym = classify_result(r, base)
    check("build true->BASE %r" % base, k == K_BASE and r == base)
    # open predicate over a non-enumerated domain -> restricted object on x
    r = ConditionSet(x, x < y, base)
    k, sym = classify_result(r, base)
    check("build open->SET sym=x %r" % base,
          k == K_SET and sym == x and r.base_set == base
          and cond_tag(r.condition) == COND_OPEN)

# An EMPTY base domain collapses to the empty domain for EVERY predicate,
# including a true or still-open one (__new__'s EmptySet short-circuit).
for base in empty_bases:
    check("base_tag empty %r" % base, base_tag(base) == BASE_EMPTY)
    for cond in (S.false, S.true, x < y):
        r = ConditionSet(x, cond, base)
        k, sym = classify_result(r, base)
        check("build emptybase->EMPTY %r cond=%r" % (base, cond), k == K_EMPTY)

# An explicitly LISTED base domain: false/true reduce as usual; an open
# predicate is decided member by member and must match listed_outcome, with any
# surviving restricted object still keyed on the SAME bound variable.
for base in listed_bases:
    check("base_tag listed %r" % base, base_tag(base) == BASE_LISTED)
    check("build false->EMPTY listed %r" % base,
          classify_result(ConditionSet(x, S.false, base), base)[0] == K_EMPTY)
    r = ConditionSet(x, S.true, base)
    check("build true->BASE listed %r" % base,
          classify_result(r, base)[0] == K_BASE and r == base)
    for cond in (x < y, Eq(x, y), x < 2, Eq(x, 2), x < -5):
        if cond_tag(cond) != COND_OPEN:
            continue
        r = ConditionSet(x, cond, base)
        want_kind, want_base = listed_outcome(x, cond, base)
        k, sym = classify_result(r, base)
        check("build listed kind %r cond=%r" % (base, cond), k == want_kind)
        if want_kind == K_BASE:
            check("build listed base %r cond=%r" % (base, cond), r == want_base)
        if want_kind == K_SET:
            check("build listed base %r cond=%r" % (base, cond),
                  r.base_set == want_base)
            check("build listed sym is x %r cond=%r" % (base, cond), sym == x)
            check("build listed cond open %r cond=%r" % (base, cond),
                  cond_tag(r.condition) == COND_OPEN)

# A base domain that is ITSELF a restricted object: false/true reduce first (the
# true reduction hands that object straight back, a pass-through), and otherwise
# the two restrictions MERGE -- over the inner base domain, keyed on the bound
# variable the merge settles on, which need not be the outer one.
for base in merged_bases:
    check("base_tag merged %r" % base, base_tag(base) == BASE_MERGED)
    check("build false->EMPTY merged %r" % base,
          classify_result(ConditionSet(x, S.false, base), base)[0] == K_EMPTY)
    r = ConditionSet(x, S.true, base)
    check("build true->BASE merged %r" % base,
          classify_result(r, base)[0] == K_BASE and r == base)
    for cond in (x < 5, x < z_, Eq(x, y)):
        if cond_tag(cond) != COND_OPEN:
            continue
        r = ConditionSet(x, cond, base)
        want_sym, want_base = merged_outcome(x, normalized_cond(cond), base)
        k, sym = classify_result(r, base)
        check("build merged->SET %r cond=%r" % (base, cond), k == K_SET)
        check("build merged sym %r cond=%r" % (base, cond),
              same_binder(sym, want_sym))
        check("build merged base is the INNER domain %r cond=%r"
              % (base, cond), r.base_set == want_base)

# ---------------------------------------------------------------------------
# 2. Validate the patched free-symbol branch of _eval_subs.
# Construct ConditionSet(sym, condition, base) where `old` is a FREE symbol
# (old != sym), subs(old, new), and compare to the model's prediction:
#   result == build(self.sym, cond_after, base_after)  (bound var unchanged).
print("[2] _eval_subs free-symbol branch == replace_free_parameter model")

n = Symbol('n', negative=True)
p = Symbol('p', positive=True)
w = Symbol('w')
z = Symbol('z')
k_ = Symbol('k')

cases = []
# (description, conditionset, old, new)
# Issue 17341: condition collapses to true, base is an ImageSet on asin(y).
img1 = imageset(Lambda(k_, 2 * k_ * pi + asin(y)), S.Integers)
img2 = imageset(Lambda(k_, 2 * k_ * pi + asin(Rational(1, 3))), S.Integers)
cases.append(("issue17341",
              ConditionSet(x, Contains(y, Interval(-1, 1)), img1),
              y, Rational(1, 3)))
# F2P regression: cond (n<x) becomes true; base unchanged -> base domain.
cases.append(("n<x true keeps base",
              ConditionSet(n, n < x, Interval(-oo, 0)),
              x, p))
# cond stays open: ConditionSet(x, x<y, S.Integers).subs(y, w)
cases.append(("open cond stays open",
              ConditionSet(x, x < y, S.Integers),
              y, w))
# cond becomes false-ish region; base maps. (n<x with x->p over [0,oo))
cases.append(("true over [0,oo)",
              ConditionSet(n, n < x, Interval(0, oo)),
              x, p))
# The base domain COLLAPSES to the empty domain under the replacement while the
# predicate stays a non-trivial restriction -> the real result is the empty
# domain, not a restricted object over an empty domain.
cases.append(("base collapses to empty",
              ConditionSet(x, x < y, Interval(0, y)), y, S(-1)))
cases.append(("base collapses to empty 2",
              ConditionSet(x, x < y, Interval(y, 1)), y, S(5)))
# Explicit finite listings: the predicate is decided member by member.
cases.append(("listed, all members decided",
              ConditionSet(x, Eq(x, y), FiniteSet(1, 2, 3)), y, S(2)))
cases.append(("listed, no member qualifies",
              ConditionSet(x, x < y, FiniteSet(1, 2, 3)), y, S(-1)))
cases.append(("listed, some undecided",
              ConditionSet(x, x < y, FiniteSet(1, 2, z)), y, S(2)))
cases.append(("listed, all undecided",
              ConditionSet(x, x < y, FiniteSet(1, 2, 3)), y, z))
# The replacement-applied base domain turns out to be itself a restricted object
# (a Union whose interval part empties out), so the rebuild MERGES -- the one
# shape whose bound variable the reduction, not the caller, settles.
mb1 = Union(Interval(0, y), ConditionSet(z, x + z > 0, S.Reals))
mb2 = Union(Interval(0, y), ConditionSet(z, z < 2, S.Reals))
mb3 = Union(Interval(0, y), ConditionSet(w, w + x > 0, Interval(-3, 3)))
mb4 = Union(Interval(0, y), ConditionSet(z, z >= -1, S.Reals))
cases.append(("merge adopts the inner binder",
              ConditionSet(x, x < y, mb1), y, S(-1)))
cases.append(("merge keeps the outer binder",
              ConditionSet(x, x < y, mb2), y, S(-1)))
cases.append(("merge over a different inner domain",
              ConditionSet(x, x < y, mb3), y, S(-1)))
cases.append(("merge where outer binder IS the inner one",
              ConditionSet(z, z < y, mb1), y, S(-1)))
cases.append(("merge mints a fresh name",
              ConditionSet(x, (x < z) & (x < y), mb1), y, S(-1)))
cases.append(("merge mints a fresh name on collision",
              ConditionSet(x, (x < z) & (Symbol('lambda') > 0) & (x < y), mb1),
              y, S(-1)))
cases.append(("merge pre-empted by a true predicate",
              ConditionSet(x, Contains(y, Interval(-2, 0)), mb1), y, S(-1)))
cases.append(("merge pre-empted by a false predicate",
              ConditionSet(x, Contains(y, Interval(1, 2)), mb1), y, S(-1)))
cases.append(("merge runs no further reduction",
              ConditionSet(z, z < y, mb4), y, S(-1)))

for desc, cs, old, new in cases:
    assert old != cs.sym, desc  # we are testing the free-symbol branch
    self_sym = cs.sym
    cond_after = cs.condition.subs(old, new)
    base_after = cs.base_set.subs(old, new)
    ct = cond_tag(cond_after)
    assert ct is not None, desc      # every case here has a truth status
    bt = base_tag(base_after)

    # Model prediction: build(self_sym, ct, base_after, bt, listed_*). The
    # reduction depends on the base domain's shape as well as the predicate.
    pred_base = base_after
    if ct == COND_FALSE:
        pred_kind, pred_sym = K_EMPTY, None
    elif bt == BASE_EMPTY:
        pred_kind, pred_sym = K_EMPTY, None
    elif ct == COND_TRUE:
        pred_kind, pred_sym = K_BASE, None
    elif bt == BASE_LISTED:
        # the constructor sifts with the NORMALIZED predicate (it is the one it
        # stores and the one it substitutes members into)
        pred_kind, pred_base = listed_outcome(
            self_sym, normalized_cond(cond_after), base_after)
        pred_sym = self_sym if pred_kind == K_SET else None
    elif bt == BASE_MERGED:
        # the two restrictions merge: over the INNER base domain, keyed on the
        # bound variable the merge settles on (conditionset.py:161-179)
        pred_kind = K_SET
        pred_sym, pred_base = merged_outcome(
            self_sym, normalized_cond(cond_after), base_after)
    else:
        pred_kind, pred_sym = K_SET, self_sym

    real = cs.subs(old, new)
    rk, rsym = classify_result(real, base_after)

    check("%s: kind model=%d real=%d" % (desc, pred_kind, rk), rk == pred_kind)
    if pred_kind == K_BASE:
        # the predicted domain passes through (== base_after, or the sifted
        # survivors when the base domain was an explicit listing)
        check("%s: base==predicted" % desc,
              real == pred_base or real.dummy_eq(pred_base))
    if pred_kind == K_SET:
        # the bound symbol is the one the REDUCTION settles on -- the original
        # self_sym on every base-domain shape but the merge -- and never `new`
        check("%s: bound sym is the predicted one" % desc,
              same_binder(rsym, pred_sym))
        if bt != BASE_MERGED:
            check("%s: bound sym is self_sym" % desc, rsym == self_sym)
        check("%s: bound sym != new" % desc, rsym != new)
        check("%s: base==predicted" % desc, real.base_set == pred_base)
        if bt != BASE_MERGED:
            # the merge conjoins the two predicates and falls through with no
            # further reduction, so no truth status is claimed of the result
            check("%s: cond stays open" % desc,
                  cond_tag(real.condition) == COND_OPEN)

# The headline issue assertion (mirrors the added F2P test).
issue = ConditionSet(x, Contains(y, Interval(-1, 1)), img1).subs(y, Rational(1, 3))
check("issue17341 dummy_eq img2", issue.dummy_eq(img2))

# ---------------------------------------------------------------------------
# 3. The truth status the CONSTRUCTION assigns (mapping.md §1.1), and the three
# shapes mapping.md §3.1 declares outside the model. The construction does not
# branch on the predicate as written: it rewrites an explicit listing of
# expressions and normalizes with `as_Boolean` first, so a predicate given as a
# number, or as a symbol whose vanishing its assumptions decide, IS decided and
# the construction reduces on it. The model must therefore tag those TRUE/FALSE
# rather than OPEN, and this section pins that against the real constructor.
print("[3] the truth status ConditionSet.__new__ itself assigns")

c_nonzero = Symbol('c', nonzero=True)
d_zero = Symbol('d', zero=True)
e_undecided = Symbol('e')

# (predicate as handed to the constructor, the tag the construction assigns)
normalizing = [
    (S.One, COND_TRUE),
    (S.Zero, COND_FALSE),
    (c_nonzero, COND_TRUE),
    (d_zero, COND_FALSE),
    (e_undecided, COND_OPEN),
    (FiniteSet(0), COND_TRUE),
    (FiniteSet(1, 2), COND_FALSE),
    (FiniteSet(x - 1), COND_OPEN),
    (And(c_nonzero, x < 1), COND_OPEN),
    (S.true, COND_TRUE),
    (S.false, COND_FALSE),
    (x < y, COND_OPEN),
]
for pred, want in normalizing:
    check("tag(%r) == %d" % (pred, want), cond_tag(pred) == want)
    for base in (S.Reals, S.Integers, Interval(0, oo), FiniteSet(1, 2, 3)):
        r = ConditionSet(x, pred, base)
        k, sym = classify_result(r, base)
        if want == COND_FALSE:
            check("__new__ %r over %r -> EMPTY" % (pred, base), k == K_EMPTY)
        elif want == COND_TRUE:
            check("__new__ %r over %r -> BASE" % (pred, base),
                  k == K_BASE and r == base)
        else:
            # an undecided predicate is a real restriction: either a restricted
            # object keyed on the same bound variable, or -- over an explicit
            # listing -- the member-by-member outcome
            want_kind, want_base = (K_SET, base)
            if base_tag(base) == BASE_LISTED:
                want_kind, want_base = listed_outcome(
                    x, normalized_cond(pred), base)
            check("__new__ %r over %r -> kind %d" % (pred, base, want_kind),
                  k == want_kind)
            if want_kind == K_SET:
                check("__new__ %r over %r keyed on x" % (pred, base), sym == x)

# Declared exclusion 2: a predicate the construction refuses to read as a truth
# value has NO tag, and the construction delivers no object at all.
for pred in (S(2), Rational(1, 2), S.NaN, S(-7)):
    check("no tag for %r" % pred, cond_tag(pred) is None)
    raised = False
    try:
        ConditionSet(x, pred, S.Reals)
    except TypeError:
        raised = True
    check("__new__ refuses %r" % pred, raised)

# Declared exclusion 3: a non-`Symbol` bound variable is outside the carrier.
raised = False
try:
    ConditionSet(x + 1, x < y, S.Reals)
except ValueError:
    raised = True
check("__new__ refuses a non-Symbol binder whose condition loses it", raised)

# A base domain that is itself a ConditionSet enters the condition-MERGING
# branch, which can RENAME the bound variable. That is MODELLED (BASE_MERGED,
# validated in [1], [2] and [5]), not excluded.
merged = ConditionSet(x, x < y, ConditionSet(y, x + y < 2, S.Integers))
check("ConditionSet base merges and may rename the binder",
      isinstance(merged, ConditionSet) and merged.sym != x)
check("the merged binder is what merged_outcome replays",
      same_binder(merged.sym,
                  merged_outcome(x, x < y,
                                 ConditionSet(y, x + y < 2, S.Integers))[0]))

# ---------------------------------------------------------------------------
# 4. The same normalization family reached through the modeled operation: a free
# parameter IS the whole predicate, so the replacement decides it. These are the
# inputs on which reading the tag off the raw expression would predict a
# restricted object while the real code delivers the base or the empty domain.
print("[4] _eval_subs over the normalization family")

for new, want in [(S.One, COND_TRUE), (S.Zero, COND_FALSE),
                  (c_nonzero, COND_TRUE), (d_zero, COND_FALSE),
                  (e_undecided, COND_OPEN), (FiniteSet(0), COND_TRUE),
                  (FiniteSet(1, 2), COND_FALSE)]:
    for base in (S.Reals, S.Integers, Interval(0, oo)):
        cs = ConditionSet(x, y, base)
        assert cs.sym == x and cs.condition == y
        cond_after = cs.condition.subs(y, new)
        check("subs tag %r == %d" % (new, want), cond_tag(cond_after) == want)
        real = cs.subs(y, new)
        priv = cs._eval_subs(y, new)
        check("subs == _eval_subs for %r over %r" % (new, base),
              real == priv or (isinstance(real, ConditionSet)
                               and isinstance(priv, ConditionSet)
                               and real.dummy_eq(priv)))
        k, sym = classify_result(real, base)
        if want == COND_TRUE:
            check("subs %r over %r -> BASE" % (new, base),
                  k == K_BASE and real == base)
        elif want == COND_FALSE:
            check("subs %r over %r -> EMPTY" % (new, base), k == K_EMPTY)
        else:
            check("subs %r over %r -> SET on x" % (new, base),
                  k == K_SET and sym == x and real.base_set == base)

# ---------------------------------------------------------------------------
# 5. The condition-MERGING branch in its own right (conditionset.py:161-179):
# the four binder outcomes, the inner base domain, and the two properties that
# make the model's clause the shape it is -- the merge is pre-empted by both
# truth reductions, and it performs NO further reduction, so the object it
# delivers stands even when its conjoined predicate is identically false. If the
# merge re-reduced, the model would owe a truth status for the merged predicate;
# it does not, and this section is why.
print("[5] the condition-MERGING branch")

inner_a = ConditionSet(z, x + z > 0, S.Reals)      # mentions the outer binder x
inner_b = ConditionSet(z, z < 2, S.Reals)          # mentions neither x nor y
inner_c = ConditionSet(w, w + x > 0, Interval(-3, 3))
inner_d = ConditionSet(z, z >= -1, S.Reals)

# (label, outer binder, outer predicate, inner object, the binder branch taken)
merge_cases = [
    ("sym == s", z, z < -1, inner_a, z),
    ("outer binder not in the inner predicate", x, x < -1, inner_b, x),
    ("inner binder not in the outer predicate", x, x < -1, inner_a, z),
    ("different inner domain", x, x < -1, inner_c, w),
    ("both cross-occur -> a fresh name", x, (x < -1) & (x < z), inner_a,
     Symbol('lambda')),
    ("fresh name collides -> a Dummy", x,
     (x < -1) & (x < z) & (Symbol('lambda') > 0), inner_a, Dummy('lambda')),
]
for label, osym, ocond, inner, want_sym in merge_cases:
    r = ConditionSet(osym, ocond, inner)
    check("[5] %s: merged object is restricted" % label,
          isinstance(r, ConditionSet))
    check("[5] %s: binder" % label, same_binder(r.sym, want_sym))
    check("[5] %s: replay agrees" % label,
          same_binder(r.sym, merged_outcome(osym, ocond, inner)[0]))
    check("[5] %s: stands over the INNER domain" % label,
          r.base_set == inner.base_set)
    check("[5] %s: the predicate is the conjunction of both" % label,
          set(r.condition.args) and inner.condition.subs(
              inner.sym, r.sym) in r.condition.args)

# both truth reductions pre-empt the merge
check("[5] a true predicate hands the inner object back",
      ConditionSet(x, S.true, inner_a) == inner_a)
check("[5] a false predicate empties",
      ConditionSet(x, S.false, inner_a) == S.EmptySet)

# no further reduction: the conjoined predicate is identically false and the
# restricted object STILL stands (it does not collapse to the empty domain)
r = ConditionSet(z, z < -1, inner_d)
check("[5] no re-reduction: the object stands", isinstance(r, ConditionSet))
check("[5] no re-reduction: its predicate is identically false",
      normalized_cond(r.condition) is S.false)
check("[5] no re-reduction: it is NOT the empty domain", r != S.EmptySet)
check("[5] no re-reduction: still over the inner domain",
      r.base_set == inner_d.base_set)
# ... reached through the modeled operation, too
cs = ConditionSet(z, z < y, Union(Interval(0, y), inner_d))
rr = cs._eval_subs(y, S(-1))
check("[5] the operation reaches the standing false-predicate object",
      isinstance(rr, ConditionSet) and rr != S.EmptySet
      and normalized_cond(rr.condition) is S.false
      and rr.base_set == inner_d.base_set)
check("[5] subs agrees with _eval_subs there", cs.subs(y, S(-1)) == rr)

# ... and the operation delivers nothing when the replacement leaves a predicate
# the construction refuses, or when the substitution itself refuses to run.
for new in (S(2), Rational(1, 2)):
    raised = False
    try:
        ConditionSet(x, y, S.Reals)._eval_subs(y, new)
    except TypeError:
        raised = True
    check("_eval_subs delivers nothing for refused predicate %r" % new, raised)
for new in (S.NaN, S.ImaginaryUnit):
    cs = ConditionSet(x, x < y, S.Reals)
    e1 = e2 = None
    try:
        cs._eval_subs(y, new)
    except Exception as exc:
        e1 = repr(exc)
    try:
        cs.subs(y, new)
    except Exception as exc:
        e2 = repr(exc)
    check("_eval_subs and subs refuse %r identically" % new,
          e1 is not None and e1 == e2)

if fail:
    print("FAIL: %d violation(s)" % fail)
    sys.exit(1)
print("OK: deep models (build, replace_free_parameter) agree with real SymPy")
sys.exit(0)
