# mapping.md — sympy__sympy-24213

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e8c22f6eac7314be8d92590bfff92ced79ee03e2`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `sympy/physics/units/unitsystem.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineAddends (first : Addend) (rest : List Addend)` | the `Add` branch of `UnitSystem._collect_factor_and_dimension` — `sympy/physics/units/unitsystem.py:173-184` (the `for addend in expr.args[1:]:` loop) | the modeled changed function: combine a sum's addends into one (factor, dimension) |
| `Addend.factor`, `Addend.dim` | the `(addend_factor, addend_dim)` pair returned by the recursive `self._collect_factor_and_dimension(addend)` call (`unitsystem.py:176-177`); `first` = the `args[0]` collection (`:174`) | read-only sub-results of the UNCHANGED recursive sub-collection |
| `Dim.deps` | the canonical dimensional-dependency signature of a dimension: `DimensionSystem.get_dimensional_dependencies(dim)` — `sympy/physics/units/dimensions.py:422` | what dimensional *equivalence* compares |
| `Dim.surf` | the surface-expression identity of a `Dimension` object: structural `Dimension.__eq__` (a `Basic` `Add`/`Mul`/`Pow` of `Dimension(...)` names) — the `dim != addend_dim` test at `unitsystem.py:178` (pre-patch) | what surface `==`/`!=` compares |
| `checkStep refDeps a rest` / `checkAddends refDeps rest` *(deep model — A-reference)* | the per-addend guard `self.get_dimension_system().equivalent_dims(dim, addend_dim)` at `unitsystem.py:178` (post-patch), evaluated inside the `for addend in expr.args[1:]` walk so the FIRST addend it cannot carry through is the one that decides | pure spec: three-valued — every addend equivalent to the reference / the test ran and returned "not equivalent" / the test could not run because a dimension in play admits no signature. Validated `== equivalent_dims` by G-AX |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the surface comparison `dim != addend_dim`
(`unitsystem.py:178`, pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a scale factor (a SymPy numeric/expression that the addends accumulate with `+=`) | `Int` | order-only model: the factor's *identity* under `+`. The combination step only sums factors and never inspects their magnitude relative to the dimension test, so an exact integer carrier is faithful to the tested behaviour (the F2P checks only that no error is raised). `int_factor` ↔ `factor`. |
| a `Dimension` object's surface expression identity | `Dim.surf : Int` | an identity key for structural `Dimension.__eq__`: two `Dimension` objects compare structurally equal (`==`) iff equal `surf`. `surf_key(dim)` ↔ `surf` (§2.1). |
| a `Dimension`'s canonical dependency signature `get_dimensional_dependencies(dim)` (a `dict` of base-dimension → power), **or its absence** — the reduction is PARTIAL and raises `TypeError` on an `Add`-named or non-Symbol-power dimension (`dimensions.py:383-395`) | `Dim.deps : Option Int` | `some k` ↔ the reduction succeeds with signature key `k`; `none` ↔ the reduction raises `TypeError`, so the dimension has no signature. `equivalent_dims` calls the reduction on BOTH arguments before comparing, so an absent signature means the test cannot run at all rather than returning `False`. `deps_key(ds, dim)` ↔ `deps` (§2.1). |
| the list `expr.args[1:]` of remaining addends | `rest : List Addend` | `args[1:]` ↔ `rest`; `len(args[1:])` ↔ `rest.length`; element order preserved (the loop is order-insensitive for the dimension test but the factor sum is commutative). |
| the reported `(factor, dim)` of the `Add` branch, when one is reported | `Combined.reported f d` | `Combined.reported f d` ↔ the returned `(factor, dim)`. |
| the `Add` branch reporting a DIMENSIONAL DISAGREEMENT: the guard's comparison ran, on signatures it had, and came back "not equivalent", so the branch reports that the addends' dimensions do not agree (`unitsystem.py:179-182`) | `Combined.disagreement` | this is a REQUIRED observation, not interchangeable with the row below. What a caller is handed here is specifically the claim that the dimensions were compared and disagree, and the repository's own consistency checks grade sums by receiving exactly this report — five of them in the P2P set assert it by CLASS. So the carrier must keep it distinct. |
| the `Add` branch reporting NO verdict at all: the reduction `equivalent_dims` performs raises before any comparison, on a dimension that admits no signature (`dimensions.py:383-395`), and the combination is abandoned | `Combined.noSignature` | a DIFFERENT observation from the row above: nothing about dimensional agreement was established. What the spec fixes is only that no value is reported AND that this is not reported as a disagreement; the particular manner in which the abandonment surfaces is deliberately left free, because nothing in the graded behaviour observes it. That asymmetry is measured, not assumed — see §2.2. |

`surf` and `deps` are modeled as distinct `Int` identity keys precisely because
the surface identity and the canonical signature are **different** observations of
the same `Dimension`: equal `surf` ⇒ equal `deps` (same expression ⇒ same
signature), but **not** conversely — two surface-distinct dimensions
(`acceleration*time` and `velocity`) can share a signature. This non-implication is
the entire content of the change and the discriminator the prepatch fails on.

### 2.1 The two identity keys — quotients of the REAL comparisons

`surf` and `deps` are `Int` **quotient keys**: each stands for an equivalence
class of the Python comparison it abstracts, so `Int` equality in Lean must hold
**exactly** when the corresponding SymPy comparison returns `True`. Both keys are
therefore built by structural traversal, per the rules the real comparisons use.
`axiom_check.py` (G-AX) carries the executable definitions and validates them.

**Why not `hash(...)`.** SymPy deliberately makes `==` COARSER than `hash`:
`Integer(2) == Float(2.0)` is `True` while `hash(Integer(2)) = 2` differs from
`hash(Float(2.0))`, and `Float('2.0',5) == Float('2.0',50)` is `True` while their
hashes differ (`Float.__eq__` compares `_mpf_` exactly and ignores `_prec`;
`Float.__hash__` mixes `_prec` in). A `frozenset`/`hash` key buckets by hash
first, so it is STRICTLY FINER than the dict `==` that `equivalent_dims`
performs, and would split classes the real callee merges. Python's `hash` is also
not injective enough to key on directly: `hash(-1) == hash(-2) == -2`, which would
MERGE the inequivalent `Dimension(1/acceleration)` and `Dimension(velocity**-2)`.
The keys below use a SHA-256 digest of a structural encoding for that reason.

* **`struct_key(e)`** — a key for structural `Basic.__eq__`
  (`sympy/core/basic.py:350-389`). Recurses on `args`, tagging each node with its
  class, and reproduces the two rules that comparison applies: a **nested**
  `Number` keeps its TYPE (`if a.is_Number and type(a) != type(b): return False`,
  so `2*n ≠ 2.0*n`), and two `Float`s are keyed on `_mpf_` alone
  (`sympy/core/numbers.py:1386`, "comparison is exact"), which is precision-
  insensitive exactly as `==` is.
* **`top_key(v)`** — a key for `==` applied at TOP level, e.g. to a dependency
  dict VALUE. There `Basic.__eq__`'s guard `not (self.is_Number and
  other.is_Number)` is BYPASSED, so numbers compare ACROSS type: every
  `Float`/`Rational` collapses to `Rational(v)`; anything else falls back to
  `struct_key`.
* **`deps_key(ds, dim)`** = digest of the `{struct_key(k): top_key(v)}` mapping of
  `get_dimensional_dependencies(dim)` — because `equivalent_dims` compares the two
  dicts with `==`, i.e. same key set and per-key values equal at top level.
* **`surf_key(dim)`** = `digest(struct_key(dim))` — a `Dimension` is not a
  `Number`, so `Dimension.__eq__` is structural throughout, with no numeric-type
  collapse: `Dimension(length**2) ≠ Dimension(length**2.0)` while the two ARE
  dimensionally equivalent. That pair is a second, independent witness to the
  non-implication above, alongside `velocity` / `acceleration*time`.

Two notes on the domain this bridge covers. First, the powers a signature carries
are not always numbers: a symbolic exponent yields `{length: n}`, and a nested one
yields `{length: 2*n}` where `2*n` and `2.0*n` are NOT equal — which is why
`top_key` falls back to the structural rule instead of numericizing recursively.
Second, `get_dimensional_dependencies` is PARTIAL: on an `Add`-named or
non-Symbol-power dimension it raises `TypeError`
(`sympy/physics/units/dimensions.py:383-395`) rather than returning a signature.
That class is **inside** the modeled domain and is carried by `deps = none`, for
two reasons.

*It is reachable through the changed line.* Post-patch, `unitsystem.py:178` calls
`equivalent_dims`, which reduces BOTH arguments (`dimensions.py:429-430`) before
comparing. So a no-signature dimension on either side makes the reduction raise
inside the guard the patch introduced, and the `Add` branch reports no value.
Pre-patch the guard was the surface test `dim != addend_dim`, which never reduces
anything, so it could not raise there.

*The patch CHANGES behaviour on it.* With a reference dimension that admits no
signature but whose addends are surface-identical, pre-patch accepts and returns a
value while post-patch reports none. Measured at `base_commit` and at
`base_commit + patch.diff`, with `b1`, `b2` quantities of dimension
`Dimension(length+time)` and scale factors 1 and 2:

| input | pre-patch (`base_commit`) | post-patch |
|---|---|---|
| `b1 + b2` (same no-signature surface) | `(3, Dimension(Dimension(length, L) + Dimension(time, T)))` | `TypeError` — no value |
| `b1 + l1` (no-signature reference, `l1` of dimension `length`) | `ValueError` — no value | `TypeError` — no value |
| `l1 + b1` (no-signature addend) | `ValueError` — no value | `TypeError` — no value |

The first row is a genuine patch delta, so treating the class as out-of-domain
would leave a leg of the changed behaviour unmodeled. `checkStep` therefore
attempts the reduction on the reference and on the addend BEFORE any comparison,
so an absent signature on either side yields `Check.unreducible` — and every row
above reports no value.

### 2.2 Why the two value-less outcomes are asymmetric

A single value-less inhabitant would leave a real choice FREE, and that freedom is
what an earlier revision of this bundle got wrong: the two rows above were mapped
onto one, so an implementation that answered every abandoned combination with the
disagreement report satisfied the whole contract while being observably different
from the real routine. The carrier is therefore three-valued. But the two rows are
NOT symmetric, and pinning them symmetrically would over-fit. Measured on the
graded test set, at `base_commit + patch.diff`, by rebuilding the branch four ways
and running the instance's own tests:

| the branch's Add leg | graded result |
|---|---|
| as patched (gold) | all pass |
| as at `base_commit` | 1 failure, and it is the F2P test |
| the DISAGREEMENT report replaced by the other class | 1 failure, and it is a P2P consistency test |
| the ABANDONED leg's manner of surfacing changed, disagreement left alone | all pass |

So the disagreement report is GRADED — a consistency test in the P2P set asserts
it by class, five times over — while the abandoned leg's manner of surfacing is
not observed by anything in the graded set. The spec follows the measurement: it
REQUIRES `Combined.disagreement` where a verdict was established, and for the
abandoned leg it requires only that no value comes back and that it is not
reported as a disagreement. A clause demanding a particular manner for the
abandoned leg would be true of gold but false of correct alternatives, which is
exactly the over-fitting this bundle must avoid.

Which of the two holds when BOTH are reachable in one sum is not free either. The
real branch walks `expr.args[1:]` in order and evaluates the guard per addend, so
it stops at the FIRST addend it cannot carry through and the outcome is the one
that addend produced; a later disagreement does not override an earlier missing
signature, nor the reverse. Measured on the patched tree with three addends whose
sum reaches both failures, the two orders give different classes, so the ordering
is observable and `checkStep` is leftmost-failure by construction.

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `checkStep` deep model ↔ `DimensionSystem.equivalent_dims` (A-reference)
**Callee:** `DimensionSystem.equivalent_dims(dim1, dim2)` —
`sympy/physics/units/dimensions.py:428`:

```python
def equivalent_dims(self, dim1, dim2):
    deps1 = self.get_dimensional_dependencies(dim1)
    deps2 = self.get_dimensional_dependencies(dim2)
    return deps1 == deps2
```

The post-patch comparison is `self.get_dimension_system().equivalent_dims(dim,
addend_dim)`. The changed comparison operation is modeled **deeply**: `checkStep`
(pure region) applies the per-addend test `a.dim.deps == refDeps`, and
`checkAddends` folds it over the addends, where `deps` is the bijection image of
`get_dimensional_dependencies`. Note the ORDER inside the callee: it reduces both
arguments FIRST and compares SECOND, so a missing signature preempts any verdict —
which is why `checkStep` tests `deps.isNone` before testing equality. Equality of the canonical
dependency signatures **is** what `equivalent_dims` returns. There is **no
`equivalentDims` axiom** the proof consumes; G-AX validates the deep model against
the real callee:

- For dimensionally **equivalent** dimensions (e.g. `acceleration*time` vs
  `velocity`, `force` vs `mass*acceleration`, any dimension vs itself),
  `equivalent_dims` returns `True` ⇔ `deps` keys are equal in the model.
- For **inequivalent** dimensions (e.g. `length` vs `time`), `equivalent_dims`
  returns `False` ⇔ `deps` keys differ.
- The surface test `dim != addend_dim` (pre-patch) disagrees with `equivalent_dims`
  exactly on surface-distinct-but-equivalent pairs — the issue's `a1*t1 + v1`
  example. G-AX exhibits at least one such pair to confirm the discriminator is
  real (the modeled change is observable).

**Soundness check (G-AX):** `axiom_check.py` constructs the SI `DimensionSystem`
in-container, carries the §2.1 key definitions, and runs the real
`equivalent_dims` / `get_dimensional_dependencies` on boundary dimension pairs
(each dimension vs itself; the issue's velocity / acceleration*time pair; force vs
mass*acceleration; energy vs force*length; pressure vs force/area; inequivalent
pairs length/time/mass) plus randomized products/powers of base dimensions,
asserting

- (a) `equivalent_dims(d1,d2) == (deps_key(d1) == deps_key(d2))` — the deep model
  is exactly `equivalent_dims`;
- (a′) when both signatures reduced, the callee RETURNS a verdict rather than
  raising — the fact the modeled `disagreeing`/`unreducible` split rests on;
- (b) `bool(d1 == d2) == (surf_key(d1) == surf_key(d2))` — `surf` is exactly a key
  for structural `Dimension.__eq__`, so the prepatch's comparison is modeled as
  precisely as the patched one;
- (c) equal `surf` ⇒ equal `deps`, the implication the pure region states; and
- (d) at least one surface-distinct-but-equivalent pair exists for which surface
  `==` is `False` while `equivalent_dims` is `True` (the modeled change is
  observable).

Its exponent pool deliberately MIXES numeric types and `Float` precisions
(`Integer(2)`, `Float(2.0)`, `Rational(4,2)`, `Float('2.0',5)`, `Float('2.0',50)`,
`Rational(1,2)` / `Float(0.5)`, symbolic and nested-symbolic powers, and the
`-1`/`-2` pair that collides under Python's `hash`), because those are exactly the
inputs on which a naive hash key parts company with the real `==` — an
integer-exponent-only pool cannot see the split. Imports only
`sympy.physics.units`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`24213`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`combineAddends`/`checkAddends`/`checkStep`/`sumFactors` (R/I-tagged ops) to Python
over real SymPy `Dimension`s and diffs the THREE-outcome behaviour (a reported
`(factor, dim)` / a dimensional disagreement / an abandoned combination) against
`patch.diff`'s
`_collect_factor_and_dimension` Add branch (the A-tagged `equivalent_dims` callee
left as the real repo callee). Flag dependency: none (`equivalent_dims` takes no
flags). Callee provenance: `equivalent_dims` and `get_dimensional_dependencies` are
UNCHANGED by the gold patch (the patch touches only `unitsystem.py`).
