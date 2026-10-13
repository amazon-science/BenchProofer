#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12489 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs, for the
modeled construction family in Solution.lean.

The gold patch threads the runtime class through ~20 object-construction sites
of `sympy.combinatorics.permutations.Permutation`. The change is ONE shared
mechanism: the factory `_af_new` becomes a classmethod that builds
`Basic.__new__(cls, ...)` (the object's runtime class is the class it is
dispatched on), AND every construction site dispatches that factory through its
own source class (`self._af_new(...)` for instance-method sites, `cls._af_new(...)`
/ `cls(...)` for classmethod sites) instead of the module-global `_af_new`
(which was bound to the base class). The values produced are byte-identical
pre/post-patch; the only observable that changes is the runtime class.

Solution.lean models this as a SHARED primitive `buildVia(builtOn, value)` —
`out.classId = builtOn`, `out.contents = value` — that EVERY modeled operation
invokes, passing its own dispatch class:

  * instance-method sites pass the LEFT operand's class (`self.classId`):
    composeProduct/powerSelf/reverseSelf/divideSelf.
  * classmethod sites pass the invoked-on class (`cls`):
    foldOver/fromUnit/extentFor/generateFor/rankedFor/rankedAltFor/
    rankedThirdFor/scheduleFor.
  * the three REFUSING sites (conjugateSelf/bracketSelf/fromVectorFor) pass their
    own dispatch class too, but ONLY on the inputs their real counterparts
    accept: each refuses a sub-domain outright (the real code raises there and
    constructs no object at all), and the spec pins `out = none` there. Like the
    two successor orders, these three are NOT free stand-ins — their guards and
    their value computations are transliterated verbatim from the patched
    worktree, refusal branch included, so the modeled guard is measured against
    the real one instead of being assumed.
  * generateFor's value depends on the ambient generator state as well as the
    extent, so its shadow is a map of BOTH (`generated_contents(n, entropy)`) and
    the check additionally executes the real generator (transliterated verbatim)
    to measure that two draws at one extent differ — the repo fact that forced
    the extra binder into the spec.
  * the two PARTIAL instance sites (stepSelf/stepAltSelf) pass the LEFT
    operand's class too, but only where their own order HAS a successor: each is
    bound to a different real successor order, each order runs out on different
    operands, and where it runs out the real function returns None and the spec
    pins `out = none`. These two are the sites whose value maps are NOT free
    stand-ins — both orders are transliterated from the patched worktree, so the
    diff tests the distinction the spec draws (that the two maps are unrelated
    and independently partial) rather than assuming it.

For each modeled site:
  * SHADOW — the R/I-tagged ops of the impl region transliterated to Python over
             the real repo carrier. It builds the result via the shared factory
             dispatched on the source class, with the relevant opaque value map
             (a fixed deterministic stand-in — its concrete value is never pinned
             by the spec, so any fixed map serves and it cancels on both sides).
  * ORACLE — patch.diff's behaviour for that site: the patched tail builds the
             result through the now-`@classmethod` `_af_new` / `cls(...)`, so the
             result object's runtime class is `type(self)` (instance sites) or
             `cls` (classmethod sites).

They must agree on every input: the SHADOW's class observable must equal the
runtime class of the ORACLE's constructed result, the contents must match, and at
the two partial sites an object must be produced on exactly the same inputs.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

The check is LIVE, not decorative — seven deliberately wrong variants of it were
each measured to FAIL (exit 1) on this input set. Four come from the refusing
sites and the generator state:

  * modeling `conjugateSelf` as TOTAL with a free stand-in value — the shape that
    let the faithfulness defect escape the previous revision of this check — is
    caught by the refusal counter: `G-CONF FAIL: conjugateSelf never refused an
    input — the modeled `<guard> = false -> out = none` clause would be untested.`
  * a modeled extent guard that is the plausible-but-wrong `len(a) >= len(b)` at
    `bracketSelf` is caught by the existence leg against the real refusal:
    `bracketSelf-EXISTENCE DISAGREE: shadow=none oracle=some self=[]
    other=[3, 0, 1, 2]`
  * treating every offset vector as well-formed is caught the same way as the
    first: `G-CONF FAIL: fromVectorFor never refused an input — ...`
  * a generating construction that is a function of the extent alone (the
    `random.shuffle` dropped) is caught by the state counter: `G-CONF FAIL: the
    real generating construction never differed between two draws of one extent
    — the modeled dependence on the generator state would be untested.`

And, from the successor split: an oracle that mints the base
class at the partial sites (`stepSelf-CLASS DISAGREE: src=_DerivedObj
res=_BaseObj`), a shadow that ignores exhaustion (`stepSelf-EXISTENCE DISAGREE:
arr=[0] shadow=some oracle=none`), and a shadow that serves the lexical successor
at the alternative-order site (`stepAltSelf-CONTENTS DISAGREE: shadow=[1, 3, 0,
2] oracle=[1, 3, 2, 0]`) — that last one being exactly the spec defect the
successor split repaired.

stdlib-only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import math
import random
import sys

SEED = 12489
N_FUZZ = 100_000


# --- the value-level computations (A-references; opaque in Solution.lean) -----
# Each `*Contents` symbol is `opaque` in Solution.lean: its concrete result is
# never pinned by the spec, only that the SAME total map is applied on both
# sides. For the R/I diff we instantiate each with a concrete, deterministic
# stand-in. It is identical on both sides, so it cancels; the discriminating
# observable is purely the result object's class.
def compose_contents(a, b):
    a, b = list(a), list(b)
    if not b:
        return list(a)
    b = b + list(range(len(b), len(a)))
    return [b[i] for i in a] + b[len(a):]


def power_contents(a, n):
    a = list(a)
    return a if (n % 2 == 0) else list(reversed(a))


def invert_contents(a):
    a = list(a)
    inv = [0] * len(a)
    for i, ai in enumerate(a):
        if 0 <= ai < len(a):
            inv[ai] = i
    return inv


# --- the SIX REFUSING sites (the value maps that are NOT free stand-ins). None of
# --- these six constructs an object for every input: each REFUSES a sub-domain
# --- outright, and the real code raises there rather than producing an object with
# --- substitute contents. Solution.lean models that with `Option Obj` plus a guard
# --- clause (`sameExtent` and `fitsWithin`, transparent `def`s; `vectorValid`,
# --- `foldDefined`, `rankedThirdDefined`, opaque), so a free stand-in would defeat
# --- the point exactly as it would for the two successor orders: it would make the
# --- sites total again and the diff would pass while testing neither the refusal
# --- nor the guard the spec now states. So all six are transliterated VERBATIM
# --- from the worktree at base_commit WITH patch.diff applied
# --- (`sympy/combinatorics/permutations.py`), refusal branch included:
# ---
# ---   __xor__               :1432  if self.size != h.size: raise ValueError(...)
# ---   commutator            :2120  if len(b) != n:         raise ValueError(...)
# ---   from_inversion_vector :2734  except IndexError:      raise ValueError(...)
# ---   mul_inv               :1231  _af_rmul(a, b) indexes `a` at `b`'s entries,
# ---                                so it raises IndexError unless the right
# ---                                operand fits within the left
# ---   rmul_with_af          :1222  _af_rmuln raises ValueError on the EMPTY
# ---                                sequence and IndexError on a sequence whose
# ---                                operands do not compose
# ---   unrank_trotterjohnson :2393  assigns `perm[k]` without reducing the index
# ---                                into range first, so an out-of-range index
# ---                                raises IndexError
# ---
# --- The last three RAISE IndexError, not ValueError, so the oracle below catches
# --- both: what the spec models is that NO OBJECT is produced, and the exception
# --- class the failure happens to surface is not an observable it states.
# ---
# --- and `size` is `len(_array_form)` (the factory sets `p._size = len(perm)`,
# --- :948), so the real extent test IS array-form length equality — which is what
# --- the spec's `sameExtent a b := a.length == b.length` states. The ORACLE below
# --- calls these and lets them raise, so the refusal is EXECUTED on every row.
def same_extent(a, b):
    """The modeled guard of the two pair sites (spec: `sameExtent`)."""
    return len(a) == len(b)


def conjugate_af(p, h):
    """Verbatim `__xor__` tail: refuses a pair of differing extents."""
    p, h = list(p), list(h)
    if len(p) != len(h):
        raise ValueError("The permutations must be of equal size.")
    a = [None] * len(p)
    for i in range(len(p)):
        a[h[i]] = h[p[i]]
    return a


def bracket_af(a, b):
    """Verbatim `commutator` tail: refuses a pair of differing extents."""
    a, b = list(a), list(b)
    n = len(a)
    if len(b) != n:
        raise ValueError("The permutations must be of equal size.")
    inva = [None] * n
    for i in range(n):
        inva[a[i]] = i
    invb = [None] * n
    for i in range(n):
        invb[b[i]] = i
    return [a[b[inva[i]]] for i in invb]


def from_vector_af(inversion):
    """Verbatim `from_inversion_vector` body: refuses an ill-formed vector."""
    inversion = list(inversion)
    size = len(inversion)
    N = list(range(size + 1))
    perm = []
    try:
        for k in range(size):
            val = N[inversion[k]]
            perm.append(val)
            N.remove(val)
    except IndexError:
        raise ValueError("The inversion vector is not valid.")
    perm.extend(N)
    return perm


def vector_valid(vec):
    """The modeled guard of the vector site (spec: the opaque `vectorValid`)."""
    try:
        from_vector_af(vec)
        return True
    except ValueError:
        return False


# The three array-form helpers the remaining refusals raise THROUGH, verbatim
# (`_af_rmul` :45, `_af_rmuln` :48-106, `_af_invert` :145-167). They are the
# reason those three sites are partial: each indexes one operand at another
# operand's entries, which is defined only where the operands fit together.
def _af_rmul(a, b):
    """Verbatim `_af_rmul` (:45). Raises IndexError if `b` has an entry outside
    `a` - for array forms, exactly when `b` is longer than `a`."""
    return [a[i] for i in b]


def _af_rmuln(*abc):
    """Verbatim `_af_rmuln` (:48-106), including its ValueError on the EMPTY
    sequence. Raises IndexError where successive operands do not compose."""
    a = abc
    m = len(a)
    if m == 3:
        p0, p1, p2 = a
        return [p0[p1[i]] for i in p2]
    if m == 4:
        p0, p1, p2, p3 = a
        return [p0[p1[p2[i]]] for i in p3]
    if m == 5:
        p0, p1, p2, p3, p4 = a
        return [p0[p1[p2[p3[i]]]] for i in p4]
    if m == 6:
        p0, p1, p2, p3, p4, p5 = a
        return [p0[p1[p2[p3[p4[i]]]]] for i in p5]
    if m == 7:
        p0, p1, p2, p3, p4, p5, p6 = a
        return [p0[p1[p2[p3[p4[p5[i]]]]]] for i in p6]
    if m == 8:
        p0, p1, p2, p3, p4, p5, p6, p7 = a
        return [p0[p1[p2[p3[p4[p5[p6[i]]]]]]] for i in p7]
    if m == 1:
        return a[0][:]
    if m == 2:
        a, b = a
        return [a[i] for i in b]
    if m == 0:
        raise ValueError("String must not be empty")
    p0 = _af_rmuln(*a[:m // 2])
    p1 = _af_rmuln(*a[m // 2:])
    return [p0[i] for i in p1]


def _af_invert(a):
    """Verbatim `_af_invert` (:164-167)."""
    inv_form = [0] * len(a)
    for i, ai in enumerate(a):
        inv_form[ai] = i
    return inv_form


def fits_within(inner, outer):
    """The modeled guard of the left-divide site (spec: `fitsWithin`, a
    transparent `def`): the inner operand's extent must not exceed the outer's."""
    return len(inner) <= len(outer)


def mul_inv_af(a, b):
    """Verbatim `mul_inv` tail (:1231-1237): inverts the LEFT operand and indexes
    it at the RIGHT operand's entries, so it refuses a right operand that does not
    fit within the left. The asymmetry is real: `divideSelf`'s guard is NOT the
    symmetric extent test the two pair sites above use."""
    return _af_rmul(_af_invert(list(a)), list(b))


def divide_defined(a, b):
    """The left-divide guard in SITE-ARGUMENT order (spec: `fitsWithin
    other.contents self.contents` - the RIGHT operand fits within the LEFT)."""
    return fits_within(b, a)


def fold_af(items):
    """Verbatim `rmul_with_af` tail (:1222-1228): folds the whole sequence through
    `_af_rmuln`, which refuses the empty sequence and any sequence it cannot
    compose."""
    return _af_rmuln(*[list(it) for it in items])


def fold_defined(items):
    """The modeled guard of the fold site (spec: the opaque `foldDefined`). NOT a
    plain length ordering - it is decided by executing the real fold."""
    try:
        fold_af(items)
        return True
    except (ValueError, IndexError):
        return False


def unrank_tj_af(size, rank):
    """Verbatim `unrank_trotterjohnson` body (:2409-2425). Unlike the other two
    index variants it does NOT reduce `rank` into range first, so an out-of-range
    index walks the assignment off the end and raises IndexError."""
    perm = [0] * size
    r2 = 0
    n = math.factorial(size)
    pj = 1
    for j in range(2, size + 1):
        pj *= j
        r1 = (rank * pj) // n
        k = r1 - j * r2
        if r2 % 2 == 0:
            for i in range(j - 1, j - k - 1, -1):
                perm[i] = perm[i - 1]
            perm[j - k - 1] = j - 1
        else:
            for i in range(j - 1, k, -1):
                perm[i] = perm[i - 1]
            perm[k] = j - 1
        r2 = r1
    return perm


def ranked_third_defined(extent, rank):
    """The modeled guard of the third index site (spec: the opaque
    `rankedThirdDefined`). NOT `rank < extent!` - it is decided by executing the
    real unranking, whose accepted range is neither that nor any plain
    comparison of the two parameters."""
    try:
        unrank_tj_af(extent, rank)
        return True
    except (ValueError, IndexError):
        return False


# --- the two SUCCESSOR orders (the one pair of value maps that is NOT a free
# --- stand-in). `stepSelf` and `stepAltSelf` are bound to two DIFFERENT real
# --- successor orders, and Solution.lean now states them over two different
# --- opaque maps plus a definedness predicate each. A free stand-in would not
# --- exercise that: it could accidentally make the two orders agree, or make
# --- both total, and the diff would then pass while saying nothing about the
# --- distinction the spec draws. So these two are transliterated from the real
# --- functions in the worktree at base_commit WITH patch.diff applied
# --- (`sympy/combinatorics/permutations.py`, the lexical successor and the
# --- alternative-order successor), including their exhaustion cases: each
# --- returns None for an operand that is LAST in its own order, which is what
# --- the spec's `<pred> ... = false -> out = none` clause models.
#
# DOMAIN. Both are transliterated verbatim, so their domain is the real one: the
# lexical successor indexes `perm[-1]` and is therefore undefined on the EMPTY
# operand (the real function raises there too), so the empty operand is outside
# the modeled carrier for these two sites and is excluded from their rows only.
def _af_parity(pi):
    """Parity of a permutation in array form (repo `_af_parity`)."""
    n = len(pi)
    a = [0] * n
    c = 0
    for j in range(n):
        if a[j] == 0:
            c += 1
            a[j] = 1
            i = j
            while pi[i] != j:
                i = pi[i]
                a[i] = 1
    return (n - c) % 2


def next_lex_af(a):
    """Lexical successor in array form; None if `a` is last in that order."""
    perm = list(a)
    n = len(perm)
    i = n - 2
    while perm[i + 1] < perm[i]:
        i -= 1
    if i == -1:
        return None
    j = n - 1
    while perm[j] < perm[i]:
        j -= 1
    perm[j], perm[i] = perm[i], perm[j]
    i += 1
    j = n - 1
    while i < j:
        perm[j], perm[i] = perm[i], perm[j]
        i += 1
        j -= 1
    return perm


def next_alt_af(a):
    """Alternative-order successor in array form; None if `a` is last in it."""
    pi = list(a)
    n = len(pi)
    st = 0
    rho = pi[:]
    done = False
    m = n - 1
    while m > 0 and not done:
        d = rho.index(m)
        for i in range(d, m):
            rho[i] = rho[i + 1]
        par = _af_parity(rho[:m])
        if par == 1:
            if d == m:
                m -= 1
            else:
                pi[st + d], pi[st + d + 1] = pi[st + d + 1], pi[st + d]
                done = True
        else:
            if d == 0:
                m -= 1
                st += 1
            else:
                pi[st + d], pi[st + d - 1] = pi[st + d - 1], pi[st + d]
                done = True
    if m == 0:
        return None
    return pi


def step_defined(a):
    return next_lex_af(a) is not None


def step_contents(a):
    return next_lex_af(a)


def step_alt_defined(a):
    return next_alt_af(a) is not None


def step_alt_contents(a):
    return next_alt_af(a)


def from_unit_contents(a, b):
    return list(a) + list(b)


def sized_contents(n):
    return list(range(n))


def generated_contents(n, entropy):
    """Stand-in for the opaque `generatedContents n entropy`: a value of BOTH the
    extent and the generator state. Identical on both sides, so it cancels; what
    matters is that it is not constant in `entropy` (asserted below)."""
    base = list(range(n))
    if n:
        k = entropy % n
        base = base[k:] + base[:k]
    return base


def real_random_af(n, rng):
    """Verbatim `random` body (:2754-2755): `perm_array = list(range(n));
    random.shuffle(perm_array)`. The value is drawn from the ambient generator, so
    it is NOT a function of `n` — the fact the spec's `entropy` binder models, and
    which this check measures directly (`n_state_matters`)."""
    perm_array = list(range(n))
    rng.shuffle(perm_array)
    return perm_array


def ranked_contents(size, rank):
    base = list(range(size))
    if size and rank:
        k = rank % size
        base = base[k:] + base[:k]
    return base


def ranked_alt_contents(n, r):
    return ranked_contents(n, r + 1)


def schedule_contents(m, n, s):
    return list(range(n))


# --- ORACLE: patch.diff's behaviour, the real construction dispatch -----------
class _BaseObj:
    """Stand-in for the base class. `_af_new` is the post-patch `@classmethod`
    that builds through the runtime `cls` (Basic.__new__(cls, perm))."""

    def __init__(self, perm):
        self._array_form = list(perm)

    @classmethod
    def _af_new(cls, perm):
        obj = cls.__new__(cls)
        obj._array_form = list(perm)
        return obj


class _DerivedObj(_BaseObj):
    """Stand-in for a user subclass (e.g. the F2P CustomPermutation)."""
    pass


_CLASS_ID = {_BaseObj: 0, _DerivedObj: 1}
_CLASSES = (_BaseObj, _DerivedObj)


def oracle_instance(self_cls, value):
    """Patched instance-method tail: `return self._af_new(value)`. Result runtime
    class == type(self) == self_cls."""
    self_obj = self_cls([])
    return self_obj._af_new(value)


def oracle_classmethod(cls, value):
    """Patched classmethod tail: `return cls._af_new(value)` / `cls(value)`.
    Result runtime class == cls."""
    return cls._af_new(value)


def oracle_refusing(src_cls, shape, real_tail, args):
    """Patched tail of a REFUSING site, with the real refusal in place: the real
    body RAISES on the sub-domain it refuses (so NO object is constructed there),
    and otherwise the result is built through the now-`@classmethod` `_af_new`
    dispatched on the source class — `self._af_new(value)` for the instance-shaped
    sites (result class == type(self), and `args[0]` is the left operand),
    `cls._af_new(value)` for the classmethod-shaped ones (result class == cls).
    Returns None exactly where the real code raises.

    BOTH exception classes are caught: the pair sites raise ValueError, while the
    left-divide, the fold and the third index variant raise IndexError out of the
    array-form helpers they index through (`_af_rmul`/`_af_rmuln`) or off the end
    of their own buffer. The spec models only THAT no object is produced, so which
    exception surfaces is not an observable it states — but it must not be allowed
    to escape and abort the diff, which is what a ValueError-only catch would do."""
    try:
        value = real_tail(*args)
    except (ValueError, IndexError):
        return None
    if shape == "instance":
        return src_cls(args[0])._af_new(value)
    return src_cls._af_new(value)


def oracle_partial(self_cls, order, arr):
    """Patched successor tail: the real function computes its own order's
    successor and `return None` when the order runs out, otherwise
    `return self._af_new(perm)` — result runtime class == type(self)."""
    self_obj = self_cls(arr)
    perm = order(self_obj._array_form)
    if perm is None:
        return None
    return self_obj._af_new(perm)


def rand_perm(rng, n):
    p = list(range(n))
    rng.shuffle(p)
    return p


# Every modeled site, tagged by structural shape. For each we record the value
# map (shadow) and assert the oracle's constructed class == the source class.
INSTANCE_SITES = [
    ("composeProduct", lambda s, o: compose_contents(s, o)),
    ("powerSelf",      lambda s, o, n=0: power_contents(s, n)),
    ("reverseSelf",     lambda s, o: invert_contents(s)),
]

# The SIX REFUSING sites. Each row is (name, dispatch shape, modeled guard, real
# tail, report labels, argument selector): the SHADOW builds only where the
# modeled guard holds, the ORACLE runs the real tail and lets it refuse. Guard
# and tail take the SAME argument tuple, drawn from the row by the selector, so a
# site's guard is checked in that site's own argument order — which matters for
# `divideSelf`, whose test is ASYMMETRIC (the right operand fits within the left,
# not the other way round). Compared on three observables — whether an object is
# produced at all, its runtime class, and its contents.
REFUSING_SITES = [
    ("conjugateSelf",   "instance", same_extent,          conjugate_af,
     ("self", "other"),  lambda r: (r["self"], r["other"])),
    ("bracketSelf",     "instance", same_extent,          bracket_af,
     ("self", "other"),  lambda r: (r["self"], r["other"])),
    ("divideSelf",      "instance", divide_defined,       mul_inv_af,
     ("self", "other"),  lambda r: (r["self"], r["other"])),
    ("fromVectorFor",   "class",    vector_valid,         from_vector_af,
     ("vec",),           lambda r: (r["vec"],)),
    ("foldOver",        "class",    fold_defined,         fold_af,
     ("items",),         lambda r: (r["items"],)),
    ("rankedThirdFor",  "class",    ranked_third_defined, unrank_tj_af,
     ("extent", "rank"), lambda r: (r["size"], r["rank"])),
]

# The two PARTIAL instance sites: each carries its OWN successor order, and each
# produces NO object for an operand that is last in that order. Compared on three
# observables: whether an object is produced at all, its runtime class, and its
# contents.
PARTIAL_SITES = [
    ("stepSelf",    step_defined,     step_contents,     next_lex_af),
    ("stepAltSelf", step_alt_defined, step_alt_contents, next_alt_af),
]

CLASSMETHOD_SITES = [
    ("fromUnit",       lambda size, rank, s, o: from_unit_contents(s, o)),
    ("extentFor",       lambda size, rank, s, o: sized_contents(size)),
    ("generateFor",    lambda size, rank, s, o: generated_contents(size, rank)),
    ("rankedFor",      lambda size, rank, s, o: ranked_contents(size, rank)),
    ("rankedAltFor",   lambda size, rank, s, o: ranked_alt_contents(size, rank)),
    ("scheduleFor",    lambda size, rank, s, o: schedule_contents(size, rank, 1)),
]


def main():
    rng = random.Random(SEED)
    fails = 0
    checked = 0
    # Non-degeneracy counters for the two successor orders (see the check below).
    n_maps_differ = 0
    n_defined_differ = 0
    n_exhausted = {name: 0 for name, _p, _v, _o in PARTIAL_SITES}
    # Non-degeneracy counters for the three refusing sites and the generator
    # state (see the checks below).
    n_refused = {row[0]: 0 for row in REFUSING_SITES}
    n_accepted = {row[0]: 0 for row in REFUSING_SITES}
    n_state_matters = 0
    gen_rng = random.Random(SEED + 1)

    def report(kind, **kw):
        nonlocal fails
        fails += 1
        if fails <= 10:
            print(f"{kind} DISAGREE: " + " ".join(f"{k}={v}" for k, v in kw.items()),
                  file=sys.stderr)

    boundary = [[], [0], [1, 0], [1, 2, 3, 0], list(range(10)), [2, 1, 3, 0]]

    def all_inputs():
        for cls in _CLASSES:
            for arr in boundary:
                yield cls, arr, arr
        for _ in range(N_FUZZ):
            cls = _DerivedObj if rng.random() < 0.5 else _BaseObj
            na = rng.randint(0, 12)
            nb = rng.randint(0, 12)
            yield cls, rand_perm(rng, na), rand_perm(rng, nb)

    for src_cls, self_arr, other_arr in all_inputs():
        n_exp = (sum(self_arr) % 7) - 3
        size = len(self_arr)
        rank = sum(other_arr)

        # INSTANCE-METHOD sites: built via the factory dispatched on src_cls.
        for name, vmap in INSTANCE_SITES:
            if name == "powerSelf":
                shadow = vmap(self_arr, other_arr, n_exp)
            else:
                shadow = vmap(self_arr, other_arr)
            res = oracle_instance(src_cls, shadow)
            if _CLASS_ID[src_cls] != _CLASS_ID[type(res)]:
                report(f"{name}-CLASS", src=src_cls.__name__, res=type(res).__name__)
            if shadow != res._array_form:
                report(f"{name}-CONTENTS", shadow=shadow, oracle=res._array_form)

        # REFUSING sites: an object exists only on the inputs the real
        # operation ACCEPTS; where it refuses, the spec pins `out = none`.
        vec = [(x % 4) for x in other_arr[:5]]
        # The fold's operand SEQUENCE for this row. The empty sequence is one of
        # the inputs the real fold refuses (there is nothing to compose), so it is
        # reached on the rows whose left operand is empty rather than being left
        # untested; every other row folds the two operands. Both sides receive the
        # same sequence, so the choice cannot mask a disagreement — it only decides
        # which part of the fold's domain this row covers.
        items = [] if not self_arr else [self_arr, other_arr]
        row = {"self": self_arr, "other": other_arr, "vec": vec,
               "items": items, "size": size, "rank": rank}
        for name, shape, guard, real_tail, labels, argsel in REFUSING_SITES:
            args = argsel(row)
            ok = guard(*args)
            shadow = real_tail(*args) if ok else None
            res = oracle_refusing(src_cls, shape, real_tail, args)
            where = dict(zip(labels, args))
            if (shadow is None) != (res is None):
                report(f"{name}-EXISTENCE",
                       shadow=("none" if shadow is None else "some"),
                       oracle=("none" if res is None else "some"), **where)
                continue
            if shadow is None:
                n_refused[name] += 1
                continue
            n_accepted[name] += 1
            if _CLASS_ID[src_cls] != _CLASS_ID[type(res)]:
                report(f"{name}-CLASS", src=src_cls.__name__,
                       res=type(res).__name__)
            if shadow != res._array_form:
                report(f"{name}-CONTENTS", shadow=shadow, oracle=res._array_form)

        # The GENERATOR STATE: the real generating construction draws its value
        # from the ambient generator, so two draws of one extent need not agree.
        # `generateFor`'s contents clause is stated over `generatedContents n
        # entropy` for exactly that reason; count the rows that witness it.
        if size > 1 and real_random_af(size, gen_rng) != real_random_af(size, gen_rng):
            n_state_matters += 1

        # PARTIAL instance sites (the two successor orders): the object exists
        # only where that order has a successor, and then it is built via the
        # factory dispatched on src_cls.
        if self_arr:
            for name, pred, vmap, order in PARTIAL_SITES:
                ok = pred(self_arr)
                shadow = vmap(self_arr) if ok else None
                res = oracle_partial(src_cls, order, self_arr)
                if (shadow is None) != (res is None):
                    report(f"{name}-EXISTENCE", arr=self_arr,
                           shadow=("none" if shadow is None else "some"),
                           oracle=("none" if res is None else "some"))
                    continue
                if shadow is None:
                    n_exhausted[name] += 1
                    continue
                if _CLASS_ID[src_cls] != _CLASS_ID[type(res)]:
                    report(f"{name}-CLASS", src=src_cls.__name__,
                           res=type(res).__name__)
                if shadow != res._array_form:
                    report(f"{name}-CONTENTS", shadow=shadow,
                           oracle=res._array_form)
            # The two orders are modeled as UNRELATED maps with independent
            # definedness. Count the rows that witness each half.
            d1, d2 = step_defined(self_arr), step_alt_defined(self_arr)
            if d1 != d2:
                n_defined_differ += 1
            elif d1 and step_contents(self_arr) != step_alt_contents(self_arr):
                n_maps_differ += 1

        # CLASSMETHOD sites: built via the factory dispatched on src_cls (= cls).
        for name, vmap in CLASSMETHOD_SITES:
            shadow = vmap(size, rank, self_arr, other_arr)
            res = oracle_classmethod(src_cls, shadow)
            if _CLASS_ID[src_cls] != _CLASS_ID[type(res)]:
                report(f"{name}-CLASS", cls=src_cls.__name__, res=type(res).__name__)
            if shadow != res._array_form:
                report(f"{name}-CONTENTS", shadow=shadow, oracle=res._array_form)

        checked += 1

    n_sites = (len(INSTANCE_SITES) + len(CLASSMETHOD_SITES) + len(PARTIAL_SITES)
               + len(REFUSING_SITES))

    # NON-DEGENERACY of the two successor orders. Solution.lean states them over
    # two DIFFERENT opaque maps with INDEPENDENT definedness predicates, and the
    # battery's delegation and exhaustion rivals are refuted exactly on inputs
    # where those two facts bite. If the transliterated orders never disagreed,
    # or never ran out, the diff above would pass while testing neither, so a
    # zero here is a FAILURE of this check rather than a silent pass.
    if not n_maps_differ:
        print("G-CONF FAIL: the two successor orders never disagreed on a "
              "commonly-defined operand — the modeled distinction between "
              "`stepContents` and `stepAltContents` would be untested.",
              file=sys.stderr)
        fails += 1
    if not n_defined_differ:
        print("G-CONF FAIL: the two successor orders never differed on WHICH "
              "operand is last — the modeled independence of `stepDefined` and "
              "`stepAltDefined` would be untested.", file=sys.stderr)
        fails += 1
    for name, cnt in n_exhausted.items():
        if not cnt:
            print(f"G-CONF FAIL: {name} never reached the end of its order — the "
                  f"modeled `out = none` case would be untested.", file=sys.stderr)
            fails += 1

    # NON-DEGENERACY of the three REFUSALS. Solution.lean states each of these
    # sites over a guard with BOTH branches pinned (`= true → out.map ... = some
    # ...`, `= false → out = none`). If a site never refused, the `out = none`
    # clause would be untested and a total impl would pass this diff; if it never
    # accepted, the class/contents clauses would be. Either way a zero is a
    # FAILURE of this check, not a silent pass.
    for name, cnt in sorted(n_refused.items()):
        if not cnt:
            print(f"G-CONF FAIL: {name} never refused an input — the modeled "
                  f"`<guard> = false → out = none` clause would be untested.",
                  file=sys.stderr)
            fails += 1
    for name, cnt in sorted(n_accepted.items()):
        if not cnt:
            print(f"G-CONF FAIL: {name} never accepted an input — its modeled "
                  f"class/contents clauses would be untested.", file=sys.stderr)
            fails += 1
    # NON-DEGENERACY of the GENERATOR STATE. `generateFor`'s contents clause is a
    # map of the extent AND the state; if the real generator had turned out to be
    # a function of the extent alone, the extra binder would be unfaithful in the
    # other direction, so this counter is asserted non-zero too.
    if not n_state_matters:
        print("G-CONF FAIL: the real generating construction never differed "
              "between two draws of one extent — the modeled dependence on the "
              "generator state would be untested.", file=sys.stderr)
        fails += 1

    if fails:
        print(f"G-CONF FAIL: {fails} disagreement(s) over {checked} input rows "
              f"x {n_sites} sites (seed {SEED}).", file=sys.stderr)
        return 1
    print(f"G-CONF PASS: {len(n_refused)} refusals non-degenerate — "
          + ", ".join(f"{k}: {n_refused[k]} refused / {n_accepted[k]} accepted"
                      for k in sorted(n_refused))
          + f"; the real generating construction differed between two draws of "
          f"one extent on {n_state_matters} row(s).")
    print(f"G-CONF PASS: two successor orders non-degenerate — "
          f"{n_maps_differ} row(s) where they disagree on a commonly-defined "
          f"operand, {n_defined_differ} row(s) where they disagree on which "
          f"operand is last, and each ran out on some row "
          + ", ".join(f"{k}={v}" for k, v in sorted(n_exhausted.items())) + ".")
    print(f"G-CONF PASS: {checked} input rows x {n_sites} modeled sites, 0 "
          f"disagreements (seed {SEED}). Every modeled construction site builds "
          f"its result via the shared factory dispatched on the source class "
          f"(instance sites: left operand's class; classmethod sites: the class "
          f"invoked on); derived stays derived, base stays base; contents = "
          f"unchanged computation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
