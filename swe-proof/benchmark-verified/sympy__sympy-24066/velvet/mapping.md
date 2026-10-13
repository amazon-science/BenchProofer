# mapping.md — sympy__sympy-24066

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 514579c655bf22e2af14f0743376ae1d7befe345`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `sympy/physics/units/unitsystem.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalizeDimensions (dims : List Dimension)` | the dimension-list post-processing of `UnitSystem._collect_factor_and_dimension`'s applied-function branch — `sympy/physics/units/unitsystem.py:192-196` (the `elif isinstance(expr, Function):` arm) | the modeled changed operation: per-argument dimension normalization |
| `Dimension` *(opaque type axiom)* | `sympy.physics.units.dimensions.Dimension` (`dimensions.py:95`) | a physical dimension value; only equality and dimensionless-ness are observed |
| `dimOne` *(opaque constant — A-consumed)* | `Dimension(1)` (`dimensions.py:95`; constructed at `unitsystem.py:195` post-patch) | the canonical dimensionless dimension (`Dimension(1)`) |
| `isDimensionless` *(opaque axiom — A-consumed)* | `self.get_dimension_system().is_dimensionless` — `DimensionSystem.is_dimensionless` (`dimensions.py:447`) | unchanged predicate deciding whether a dimension carries no physical dimension |
| `normDim (d : Dimension)` *(deep model — A-reference)* | the per-element map `Dimension(1) if self.get_dimension_system().is_dimensionless(d) else d` (`unitsystem.py:194` post-patch) | pure spec: canonicalize one argument's dimension |
| `normSeq (ds : List Dimension)` *(deep model — A-reference)* | the list comprehension `[Dimension(1) if ...is_dimensionless(d[1]) else d[1] for d in fds]` (`unitsystem.py:194` post-patch) | pure spec: canonicalize the whole argument-dimension list; deep model validated `normSeq == real comprehension` by axiom_check.py (G-AX), NOT a consumed equational axiom |

The pre-patch arm this change replaces (refinement audit only, not in the
consumer spec view): the applied-function branch returned the argument
dimensions verbatim — `return (expr.func(*(f[0] for f in fds)), *(d[1] for d in
fds))` (`unitsystem.py:195-196`), with no canonicalization of dimensionless
arguments.

The surrounding recursion `self._collect_factor_and_dimension(arg) for arg in
expr.args` (`unitsystem.py:193`) and the factor reconstruction
`expr.func(*(f[0] for f in fds))` (`unitsystem.py:195`) are UNCHANGED by the
patch; they produce the `dims` list that `normalizeDimensions` consumes and are
out of scope of the modeled operation (the patch leaves them byte-identical).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the argument-dimension list `[d[1] for d in fds]` (a sequence of `Dimension` objects) | `List Dimension` | the `k`-th `Dimension` object ↔ the `k`-th `List` element, by position; `len(dims)` ↔ `dims.length`; empty ↔ `[]` |
| one `Dimension` object | opaque Lean `Dimension` | object identity / `Dimension.__eq__` ↔ Lean `Eq`; only equality and dimensionless-ness are observed (mapping.md §3) |
| `Dimension(1)` (the canonical dimensionless dimension) | `dimOne` | the singleton canonical value; `d == Dimension(1)` ↔ `d = dimOne` |
| `self.get_dimension_system().is_dimensionless(d)` (a `bool`) | `isDimensionless d : Bool` | Python `True`/`False` ↔ Lean `true`/`false` |

The output tuple is `(expr.func(*factors), *dims_normalized)`. Only the
`dims_normalized` portion is modeled; the leading `expr.func(*factors)` factor
term is unchanged by the patch (mapping.md §1) and observationally identical
pre/post, so it is identity under refinement and omitted from the carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `normSeq` / `normDim` deep model ↔ the post-patch comprehension (A-reference)
The changed operation is modeled **deeply** by `normDim`/`normSeq` (pure region);
there is **no consumed equational axiom about the function under change**. The
post-patch source (`sympy/physics/units/unitsystem.py:192-196`):

```python
elif isinstance(expr, Function):
    fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
    dims = [Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
    return (expr.func(*(f[0] for f in fds)), *dims)
```

`normDim d = if isDimensionless d then dimOne else d` is exactly the
per-element rule `Dimension(1) if is_dimensionless(d) else d`; `normSeq` is the
front-recursive map of `normDim` over the list, i.e. exactly the list
comprehension. Because each element is decided independently and order is
preserved, the front-recursive fold equals the comprehension element-wise.

**Soundness check (G-AX):** `axiom_check.py` builds real `Dimension` lists from
sympy unit expressions (dimensionful, canonical-dimensionless, and
*non-canonical* dimensionless dimensions such as `Dimension(time/(capacitance*
impedance))`) and asserts `normSeq(dims) == [Dimension(1) if dimsys
.is_dimensionless(d) else d for d in dims]` (A-reference) over boundary +
randomized cases. Exit 0 iff sound.

### 3.2 `isDimensionless` ↔ `DimensionSystem.is_dimensionless` (A-consumed, opaque)
**Callee:** `self.get_dimension_system().is_dimensionless` (`dimensions.py:447`),
UNCHANGED by the patch. Modeled by an **opaque** `axiom isDimensionless :
Dimension → Bool` — the weakest sufficient contract is none (directive 7): the
proof only needs that the SAME predicate decides each element, never any
equational fact about it. Used inside the deep model `normDim`.

**Soundness check (G-AX):** `axiom_check.py` confirms `is_dimensionless` is a
total `Dimension → bool` on every fuzzed dimension, and exhibits the load-bearing
witness — there exist dimensions `d` with `is_dimensionless(d) == True` and `d
!= Dimension(1)` (e.g. `Dimension(time/(capacitance*impedance))`), so the
canonicalization genuinely changes the result (the bug). Imports only sympy
(the same module the patch lives in).

### 3.3 `dimOne` ↔ `Dimension(1)` (A-consumed, opaque constant)
**Callee/value:** `Dimension(1)` (`dimensions.py:95`), constructed UNCHANGED at
`unitsystem.py:195` post-patch. Modeled by an opaque `axiom dimOne : Dimension`.
G-AX confirms `Dimension(1)` is a stable singleton value and that
`is_dimensionless(Dimension(1)) == True` (`dimensions.py:453`, `name == 1`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24066`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `normDim`/`normSeq` (the R/I conditional-select-and-map ops) to
Python and leaves the A-tagged callees as the REAL repo callees: `isDimensionless`
→ `SI.get_dimension_system().is_dimensionless`, `dimOne` → `Dimension(1)`. The
oracle is the patched `_collect_factor_and_dimension`'s applied-function branch
output. Shadow and oracle share the unchanged recursion + factor terms, so the
test isolates the R/I normalization map.
