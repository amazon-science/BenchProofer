# mapping.md — sympy__sympy-15809

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 28d913d3cead6c5646307ffa6540b21d65059dfd`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/functions/elementary/miscellaneous.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `lattice_reduce(operands, identity, zero, single, aggregate)` | `MinMaxBase.__new__(cls, *args, **assumptions)` — `sympy/functions/elementary/miscellaneous.py:341` | the modeled changed function (the Min/Max constructor / lattice fold) |
| `operands: List[int]` | the variadic `*args` (sympified operand collection) | the operand collection; cardinality is what the change observes |
| `identity: int` | `cls.identity` — `Min.identity = S.Infinity` (`:796`), `Max.identity = S.NegativeInfinity` (`:731`) | the lattice's neutral element (returned for the empty canonical set) |
| `zero: int` | `cls.zero` — `Min.zero = S.NegativeInfinity` (`:795`), `Max.zero = S.Infinity` (`:730`) | the lattice's absorbing element / annihilator (returned on short-circuit) |
| `single: int` | `list(args).pop()` — `miscellaneous.py:365` | the sole canonical survivor, returned as itself |
| `aggregate: int` | the assembled `Expr.__new__(cls, _args, ...)` object — `miscellaneous.py:367-371` | the constructed aggregate when ≥2 operands survive |
| `has_noncomparable_operand(operands)` *(axiom — A-consumed)* | the comparability `raise ValueError` path of `cls._new_args_filter(args)` — raised at `miscellaneous.py:521-523`, NOT caught (propagates out of `__new__`) | unchanged ordered scan: whether its **FIRST decisive event** is a non-comparable operand (NOT containment — see the exclusivity note below) |
| `has_absorbing_operand(operands)` *(axiom — A-consumed)* | the `ShortCircuit` path of `cls._new_args_filter(args)` — raised at `miscellaneous.py:526`, caught at `:351-352` → `return cls.zero` | unchanged ordered scan: whether its **FIRST decisive event** is the absorbing operand `cls.zero` |
| `canonical_reduction_defined(operands)` *(axiom — A-consumed)* | whether the unchanged chain `cls._collapse_arguments` (`:356`) + `cls._find_localzeros` (`:359`) YIELDS a set at all — `_find_localzeros` (`:536-560`) compares survivors against one another through `_is_connected` (`:552`, `:563-583`), whose `r = hit(x >= y, Max, Min)` (`:574`) can propagate out of `Expr.__ge__` (`sympy/core/expr.py:295`) | unchanged canonical-set pass: its DEFINEDNESS. A **different observation** from the scan above — see the two-observations note below |
| `canonical_count(operands)` *(axiom — A-consumed, PARTIAL)* | `len(args)` after `cls._collapse_arguments` (`:356`) + `cls._find_localzeros` (`:359`) — the `if not args` / `if len(args) == 1` tests at `:361,:364` | unchanged canonical-set reduction: the surviving-operand count, defined only where the pass above is (hence `Requires(canonical_reduction_defined(operands))`) |
| `EmptyReductionRejected` | the removed `raise ValueError("The Max/Min functions must have arguments.")` — `miscellaneous.py:342-343` (DELETED by the patch) | user-defined stand-in for the rejection a stale impl performs on the empty collection |
| `ReductionUndefined` | whatever error the canonical-set chain propagates — `TypeError("Invalid comparison of complex %s")` from `Expr.__ge__` (`sympy/core/expr.py:295`) via `_is_connected` (`:574`), or the `NotImplementedError` where the relational is undecided | user-defined stand-in for that propagated failure (a builtin exception in an `Exsures` crashes the Nagini translator) |

**Both scan predicates read the SAME single ordered scan** (`_new_args_filter`,
`:519-526`), which stops at its first decisive event. They are therefore
**mutually exclusive**, and neither is a containment test: a collection may carry
a non-comparable operand and still not be rejected because the scan collapsed
earlier on an absorbing one. `Min(-oo, I)` → `-oo` (absorbing first) while
`Min(I, -oo)` → `ValueError`; `Max(oo, I)` → `oo` while `Max(I, oo)` →
`ValueError`. The model encodes this as
`Ensures(Implies(Result(), not has_noncomparable_operand(operands)))` on
`has_absorbing_operand`, and `axiom_check.py` checks it on both orders of
`{absorbing, non-comparable}` against the real scan.

**Two DIFFERENT observations, not one.** The ordered scan judges each operand
**alone** (`arg.is_real is False or (arg.is_number and not arg.is_comparable)`,
`:521-523`); the canonical-set pass compares the survivors **against one
another** (`_is_connected`, `:552`/`:574`). They part company on operands the
scan passes over that still cannot be placed against another survivor: `x + I`
has `is_real is None` and is not a number, so the scan passes it over, yet
`Min(x, x + I)` propagates `TypeError('Invalid comparison of complex I')` out of
`x >= x + I`. `Min(sign(x), Order(x))` propagates `NotImplementedError` the same
way. A model with only the scan's observation would predict a normal return
there; hence the separate `canonical_reduction_defined` axiom, the partial
`canonical_count`, and the `ReductionUndefined` leg. The failure is UNCHANGED by
the patch — the base and patched constructors agree on this whole class; only the
empty collection differs.

The pre-patch repo lines the change removes (for the refinement audit, not
referenced from the consumer spec view): the guard

```python
if not args:
    raise ValueError("The Max/Min functions must have arguments.")
```

at `miscellaneous.py:342-343`, which is deleted so control falls through to the
empty-canonical-set branch `if not args: return cls.identity` (`:361-362`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the variadic `*args` operand collection (a SymPy `Expr` tuple) | `List[int]` of opaque operand ids | only cardinality is observed by the change: `len(args)` ↔ `len(operands)`; `not args` ↔ `len(operands) == 0` |
| `cls.identity` / `cls.zero` / a single survivor / a constructed aggregate | distinct opaque `int` sentinels `identity` / `zero` / `single` / `aggregate` | each of the four possible return values ↦ a distinct sentinel (the precondition pins them pairwise-distinct so each postcondition clause selects exactly one branch). For `Min`: `identity = oo`, `zero = -oo`; for `Max`: `identity = -oo`, `zero = oo`. |
| `cls._new_args_filter` raising `ValueError("...is not comparable.")` (UNCAUGHT — propagates out of `__new__`) | the boolean `has_noncomparable_operand(operands)` + `raise NonComparableOperand()` | the comparability-rejection outcome ↦ a boolean predicate; the propagated `ValueError` ↦ the user-defined `NonComparableOperand` (a builtin exception in an `Exsures` crashes Nagini), the absorbing-operand pre-filter, §3.0 |
| `cls._new_args_filter` raising `ShortCircuit` (→ `return cls.zero`) | the boolean `has_absorbing_operand(operands)` | the short-circuit outcome ↦ a boolean predicate over the collection (the absorbing-operand pre-filter, §3.1) |
| whether `_collapse_arguments` + `_find_localzeros` yields a set at all, vs. propagating the comparison error `_is_connected` (`:552`/`:574`) gets from `Expr.__ge__` (`expr.py:295`) | the boolean `canonical_reduction_defined(operands)` | the canonical-set pass's DEFINEDNESS ↦ a boolean predicate over the collection (the canonical-set pass, §3.3) |
| `len(args)` after `_collapse_arguments` + `_find_localzeros` | `canonical_count(operands)` | the surviving-operand count ↦ a non-negative int, **partial**: defined only where the pass above is (the canonical-set reduction, §3.2) |
| the error the canonical-set pass propagates instead of a set — `TypeError("Invalid comparison of complex I")` from `x >= x + I`, or `NotImplementedError` for `Min(sign(x), Order(x))` | `raise ReductionUndefined()` | one user-defined exception class stands for the whole propagated-failure outcome; the model observes only *that the reduction failed there rather than returning a value* (the conformance bridge collapses every such exception type to this one outcome and records the real type for the shadow log) |
| `raise ValueError(...)` (the deleted guard) / `raise NotImplementedError`-class deferral | `raise EmptyReductionRejected()` | a builtin exception in an `Exsures` crashes Nagini, so the rejection is a user-defined exception class; the discriminating observable is *whether the empty collection is rejected at all* |

`Min` and `Max` are the two concrete lattices; both are the same modeled
function `lattice_reduce` with the `identity`/`zero` sentinels swapped (the
F2P tests `test_Min` and `test_Max` exercise the two instantiations of the one
changed `MinMaxBase.__new__`). The change is identical for both — a single
deleted guard — so one `model_prepatch.py` discriminates both behaviours.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All four axioms are about UNCHANGED callees that `__new__` invokes *before* the
result-branch logic; none is the operation that changed (the change is the
removal of the empty-args guard, modeled directly as the absence of that
specific `raise` in the impl). The comparability raise and the short-circuit
raise both live in the SAME unchanged callee, `_new_args_filter`, and the patch
does not touch either: a non-comparable operand STILL raises `ValueError`, which
the F2P tests `test_Min` / `test_Max` continue to assert (`raises(ValueError,
lambda: Min(I))`, `Max(S.ComplexInfinity, 1)`, `Min(cos(x), sin(x)).subs(x, I)`,
etc.). The canonical-set pass that follows (`_collapse_arguments` +
`_find_localzeros`) is likewise unchanged and likewise still able to FAIL, on a
disjoint class of collections. The model therefore must NOT claim unconditional
totality: it pins the non-comparable rejection with an `Exsures`, pins the
canonical-set pass's failure with a second `Exsures`, and conditions the
four-outcome totality on the absence of a non-comparable first event AND the
definedness of that pass.

### 3.0 `has_noncomparable_operand` ↔ the comparability pre-filter (A-consumed)
**Callee:** `MinMaxBase._new_args_filter` (`miscellaneous.py:508-534`), whose
per-arg comparability guard

```python
if not isinstance(arg, Expr) or arg.is_real is False or (
        arg.is_number and not arg.is_comparable):
    raise ValueError("The argument '%s' is not comparable." % arg)
```

(`:521-523`) is raised from inside the `for arg in arg_sequence` loop and is
**NOT** caught in `__new__` (only `ShortCircuit` is caught at `:350-352`), so the
`ValueError` propagates out of the constructor. The axiom encodes the property
the proof needs for the empty-collection clause — **an empty operand collection
contains no operand, so the pre-filter can never reject it** —
`Implies(len(operands) == 0, not has_noncomparable_operand(...))`; and it
underpins the model's `Exsures(NonComparableOperand, has_noncomparable_operand)`,
which pins the unchanged rejection. Sound because the comparability raise fires
only from inside the per-arg loop body, which never executes on an empty
sequence (so the empty collection is never rejected), while a collection whose
scan REACHES a non-comparable operand as its first decisive event DOES raise
(verified by axiom_check.py against `I`, `S.ComplexInfinity`, `S.NaN`, and the
substituted `Min/Max(cos(x), sin(x)).subs(x, I)`). The propagated builtin
`ValueError` is modeled as the user-defined `NonComparableOperand` (a builtin
exception in an `Exsures` crashes Nagini, §2).

**Not a containment test.** The guard fires from inside the scan loop, which
`raise`s and so terminates at the first decisive operand. This predicate is
therefore "the scan's first decisive event is a non-comparable operand", NOT
"the collection contains one". On `[cls.zero, I]` the scan short-circuits on
`cls.zero` (`:525-526`) before it ever inspects `I`, so the reduction returns
`cls.zero` normally: `Min(-oo, I) == -oo`, whereas `Min(I, -oo)` raises. The
exclusivity clause on `has_absorbing_operand` (§3.1) records this, and the
axiom_check.py fuzz that mixes a non-comparable operand into a **comparable**
set (no absorbing operand present) is exactly the class where reaching it is
guaranteed.

### 3.1 `has_absorbing_operand` ↔ the `ShortCircuit` pre-filter (A-consumed)
**Callee:** `MinMaxBase._new_args_filter` (`miscellaneous.py:508-534`), whose
`if arg == cls.zero: raise ShortCircuit(arg)` (`:525-526`) is caught in
`__new__` (`:349-352`):

```python
try:
    args = frozenset(cls._new_args_filter(args))
except ShortCircuit:
    return cls.zero
```

The axiom encodes two properties the proof needs. First, **an empty operand
collection contains no operand, so the scan can never reach an absorbing
operand on it** — `Implies(len(operands) == 0, not has_absorbing_operand(...))`.
This is the weakest sufficient contract (the generator `_new_args_filter`
iterates over `arg_sequence`; with no args it yields nothing and raises
nothing). It is sound because the short-circuit is raised only from inside the
per-arg loop body, which never executes on an empty sequence.

Second, **EXCLUSIVITY** —
`Implies(has_absorbing_operand(...), not has_noncomparable_operand(...))`. Both
predicates are outcomes of the SAME single ordered scan over `arg_sequence`,
which `raise`s (and so terminates) at its first decisive operand; a scan has
exactly one first event, so at most one of the two outcomes is ever observed.
This is what makes the pair a faithful model rather than two independent
containment tests, and it is the clause that lets the proof discharge the
absorbing branch on a collection that ALSO carries a non-comparable operand
later — `Min(-oo, I) == -oo`, not a rejection. Checked against the real scan on
both orders of `{absorbing, non-comparable}` by `axiom_check.py`.

### 3.2 `canonical_count` ↔ the canonical-set reduction (A-consumed)
**Callees:** `cls._collapse_arguments` (`miscellaneous.py:373-506`) and
`cls._find_localzeros` (`:536-...`), which transform the surviving args into the
canonical set whose length the `if not args` / `if len(args) == 1` tests read
(`:361-365`):

```python
args = cls._collapse_arguments(args, **assumptions)
args = cls._find_localzeros(args, **assumptions)
if not args:
    return cls.identity
if len(args) == 1:
    return list(args).pop()
```

The axiom is **PARTIAL**: `Requires(canonical_reduction_defined(operands))`
(§3.3). The two callees above do not always produce a set — `_find_localzeros`
compares the survivors against one another and can propagate that comparison's
own error instead (`:552`/`:574` → `Expr.__ge__`, `expr.py:295`) — and where they
do not, there is no `len(args)` for this axiom to name. Declaring it total would
be the unfaithful reading: it would assert a cardinality on collections whose
real pass never reaches `if not args`. Where the pass IS defined the axiom
encodes only: the canonical count is **non-negative**, and an **empty operand
collection reduces to the empty canonical set** —
`Implies(len(operands) == 0, canonical_count(...) == 0)`. Sound because
`_collapse_arguments` begins `if not args: return args` (`:402-403`) and
`_find_localzeros` likewise leaves an empty set empty; the empty input therefore
reaches `if not args: return cls.identity` with `len(args) == 0`. This is the
weakest contract the proof consumes (it does NOT claim the count for any
non-empty input — the change does not depend on it). The model reads
`canonical_count` only underneath the definedness antecedent, so the precondition
is discharged at every use site.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `sympy.Min` /
`sympy.Max` (the patched `MinMaxBase.__new__`) on the empty collection, single
operands, ≥2 operands, the non-comparable operands `I` / `S.ComplexInfinity` /
`S.NaN` (alone and mixed into comparable collections) and the substituted
`Min/Max(cos(x), sin(x)).subs(x, I)`, 2000 randomized symbolic collections, and
1000 randomized comparable-plus-one-non-comparable collections per lattice. It
asserts: the empty collection RETURNS the identity element (never raises, never
the annihilator `cls.zero`) — i.e. `has_noncomparable_operand([]) == False`,
`has_absorbing_operand([]) == False` and `canonical_count([]) == 0` all hold; a
single comparable survivor returns that operand; ≥2 survivors assemble an
aggregate of the same lattice; every collection whose scan REACHES a
non-comparable operand first is rejected with `ValueError` (the unchanged
comparability path — `has_noncomparable_operand(ops) == True`); and the two
decisive scan events are MUTUALLY EXCLUSIVE, checked on both orders of
`{absorbing, non-comparable}` (`[cls.zero, bad]` and `[bad, cls.zero]`, alone and
behind a comparable symbol) by consuming the real `_new_args_filter` and
requiring the constructor's observable to equal the scan's FIRST event —
`Min(-oo, I) == -oo` while `Min(I, -oo)` raises. It imports only `sympy` (the
library under test); SKIP-guarded (exit 0) when the host interpreter cannot
import this old sympy. Confirmed RC=0 in-container (gold applied) over 6208
observations. Exit 0 iff sound.

### 3.3 `canonical_reduction_defined` ↔ the canonical-set pass's definedness (A-consumed)
**Callees:** the same unchanged pair, taken as a partial map rather than a total
one. `cls._find_localzeros` (`miscellaneous.py:536-560`) walks the survivors and
asks `cls._is_connected(v, z)` (`:552`) for pairs of them; `_is_connected`
(`:563-583`) evaluates

```python
for i in range(2):
    r = hit(x >= y, Max, Min)
    if r is not None:
        return r
    x, y = y, x
```

(`:571-577`), and `x >= y` is `Expr.__ge__` (`sympy/core/expr.py:295`), which
raises `TypeError("Invalid comparison of complex %s")` when a side turns out
non-real, or leaves the relational undecided so the walk propagates a
`NotImplementedError`. So the pass can END WITHOUT A CANONICAL SET, and the whole
reduction then fails.

**Why this is a SECOND observation and not the scan's.** The scan's guard
(`:521-523`) judges each operand ALONE: `x + I` has `is_real is None` (not
`False`) and `is_number` is False, so the scan passes it over — yet `x >= x + I`
cannot be decided, and `Min(x, x + I)` raises
`TypeError('Invalid comparison of complex I')` from `expr.py:295`.
`Min(sign(x), Order(x))` raises `NotImplementedError` the same way. A model with
only the scan's predicate would predict a normal four-outcome return on that whole
class. Both the base and the patched constructor behave this way — the class is
UNCHANGED by the change under specification — so the model must carry the leg,
not condition it away.

The axiom encodes only what the proof consumes: **an EMPTY operand collection
leaves this pass nothing to compare, so it cannot fail on it** —
`Implies(len(operands) == 0, canonical_reduction_defined(...))`. Sound because
`_collapse_arguments` returns immediately on empty (`:402-403`) and
`_find_localzeros` starts with `localzeros = set()` and never enters its
`for v in values` body, so no comparison is ever attempted; the empty collection
reaches `if not args: return cls.identity`. Nothing is claimed for any non-empty
collection — the predicate is left free there, which is exactly why the model's
totality/count clauses are conditioned on it and its failure leg is `Exsures`-
pinned rather than excluded. It is also vacuously true wherever the scan already
decided the outcome (the pass is never reached), which is what lets the absorbing
branch stay provable alongside such an operand.

**Soundness check (G-AX).** `axiom_check.py` drives the real constructors on the
class where the two observations part: operands `x + I`, `x + 2*I`, `x - I`,
`I*x`, `sign(x)`, `Order(x)`, each in 13 collection shapes per lattice (alone,
doubled, with a comparable symbol on either side, with the annihilator on either
side, with the identity element on either side, with the non-comparable `I` on
either side, and behind two comparable symbols). For each it consumes the REAL
`_new_args_filter` to get the scan's first event and asserts: where that event is
the non-comparable one the constructor raises `ValueError`; where it is the
absorbing one the constructor still returns the annihilator (the pass is never
reached, so definedness is vacuously true); and where the scan passed every
operand over, the constructor never raises the scan's OWN `ValueError` — so the
two observations really are distinct. It further asserts the predicate is
NON-TRIVIAL: `assert undefined_seen > 0`, i.e. at least one collection whose scan
is clean still FAILS in the pass. Measured in-container: **18** such collections,
so the model's reduction-undefined leg is reachable rather than dead.

## G-CONF (differential conformance: does the MODEL agree with the REAL patched code?)

`conformance_check.py` diffs the model's impl region against the REAL patched
repo function. This is the refinement leg no other gate covers (G-VERIFY checks
impl-vs-spec, G-PBT checks spec-vs-wrong-impls, neither reads the repository).

**Shadow.** The `# impl-start` .. `# impl-end` region of `model.py`
(`lattice_reduce`), copied **byte-identically** — verified with
`awk '/^    # impl-start$/,/^    # impl-end$/'` over both files producing zero
`diff` output. The model IS Python, so nothing is transliterated; the impl region
contains no contract calls of its own (the `Requires`/`Ensures`/`Exsures` live in
the separate pre/post-condition regions, which are what got stripped). The
`# pure-start` region declares no helpers, and no `PSeq` crosses the region (the
carrier is a plain `List[int]`), so no sequence shim is needed.

**The four `@ContractOnly` callees call the REAL repo code** they axiomatize
(§3), so the axioms are exercised rather than assumed:

| model symbol | real repo code driven |
|---|---|
| `has_noncomparable_operand` | `frozenset(cls._new_args_filter(sympify(a) for a in args))` (`:347-350`) — reports whether the comparability `ValueError` (`:521-523`) comes out |
| `has_absorbing_operand` | the same REAL generator — reports whether `ShortCircuit` (`:525-526`) comes out |
| `canonical_reduction_defined` | vacuously true where the REAL generator already decided; otherwise runs the REAL `cls._collapse_arguments` (`:373-506`) then `cls._find_localzeros` (`:536-560`) over the REAL filtered frozenset and reports whether they YIELDED a set instead of propagating the comparison error out of `_is_connected` (`:552`/`:574`) → `Expr.__ge__` (`expr.py:295`) |
| `canonical_count` | `len()` of that same REAL pair's result — the very value the patched `if not args` / `if len(args) == 1` tests read (`:361-365`). Called by the shadow only under the definedness antecedent, matching the axiom's `Requires` |

Because the bridge consumes the real generator in the real order, it inherits its
order-sensitivity rather than assuming the two pre-filters are independent:
`Min(-oo, I)` short-circuits on the absorbing `-oo` before the filter reaches the
non-comparable `I` (absorbing, not rejected), while `Min(I, -oo)` raises
`ValueError`. Both orders are in the boundary catalogue; a reimplemented
"contains a non-comparable operand?" predicate would have gotten them wrong.

**Oracle.** `MinMaxBase.__new__` (`sympy/functions/elementary/miscellaneous.py:341`,
§1) — **CALLED, not transliterated**, through its public entry points
`sympy.Max(*raw)` / `sympy.Min(*raw)` (the two concrete lattices of §2; the F2P
tests `test_Min` / `test_Max` exercise exactly those two instantiations). The gate
applies `patch.diff` to /testbed and sets `PYTHONPATH` before the script runs, so
the constructor under comparison is the PATCHED one; the script does not apply the
patch itself.

**Type bridge (§2, inverted).** A concrete operand collection `raw` (a list of
sympy `Expr`s) is presented to the shadow as the opaque id list
`list(range(len(raw)))` — order-preserving, `len(operands) == len(raw)` — and the
bridged callees resolve ids back to `raw` before calling the real code. The shadow
is fed the four pairwise-distinct sentinels `identity/zero/single/aggregate` =
`0/1/2/3` (satisfying the distinctness `Requires` by construction), and the
sentinel it returns is DECODED to the concrete repo value it stands for:
`cls.identity`, `cls.zero`, `list(args).pop()` (`:365`), and the repo's own
assembly lines `Expr.__new__(cls, _args); obj._argset = _args` (`:367-371`) over
the real canonical set. `NonComparableOperand` ↦ the propagated builtin
`ValueError`; `ReductionUndefined` ↦ whatever the canonical-set pass propagated,
and the bridge reports the REAL exception's type name so the shadow's failure is
compared against the oracle's actual failure type (`TypeError` /
`NotImplementedError`) rather than against "some error". Every generated input
satisfies the `Requires` (read permission is
vacuous outside Nagini; distinctness holds by construction), so no input is
filtered out and the domain is never narrowed.

**Inputs.** The modeled space is INFINITE (arbitrary sympy operand collections),
so a deterministic boundary catalogue runs first and seeded fuzz fills the count.
The catalogue takes every impl branch per lattice: the empty collection (the F2P
shape — `Min() == oo`, `Max() == -oo`, the identity branch the deleted guard used
to pre-empt), an empty canonical set arising for a DIFFERENT reason
(`cls.identity`-only operands, dropped by `_new_args_filter`), the absorbing
short-circuit, one survivor (duplicates, comparable numerics), ≥2 survivors
(including nested `Max`/`Min` flattening), the non-comparable rejection (`I`,
`zoo`, `nan`, `cos/sin` substituted at `I`, and non-comparable-vs-absorbing in
both orders), and the **undefined canonical-set pass** (`x + I`, `x + 2*I`,
`x - I`, `I*x`, `sign(x)`, `Order(x)` in 16 collection shapes each, plus the same
operands mixed into the fuzz pool). **Pinned seed: `SEED = 15809`**;
`N_FUZZ = 50_000` per lattice. Recorded run: **100282 comparisons, 0
disagreements**, every one of the SIX branches hit (`identity` 12922, `zero`
7437, `single` 23182, `aggregate` 33113, `reject` 21644, `undefined` 1984). A
branch never taken is reported as a FAIL, not a silent pass, so the generator
cannot dodge the behaviour under specification. The `undefined` branch is
compared against the ORACLE's real exception type (`TypeError` /
`NotImplementedError`), not merely against "it raised".

**Refutation capability (negative control).** Re-run against the UNPATCHED
/testbed (gold not applied) the same script FAILS: **12112 disagreements, exit
1**, every one of them on the empty collection —
`shadow=('VALUE', -oo, 'identity')` vs `oracle=('RAISE', 'ValueError')`. The
shadow's branch tally is unchanged there (the bridged callees are the unchanged
ones), so the entire divergence is the empty-collection outcome and nothing else:
the check exercises exactly the branch the gold patch changed, and is capable of
failing. Exit 0 iff zero disagreements.
