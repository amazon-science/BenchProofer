# mapping.md — pydata__xarray-3151

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 118f4d996e7711c9aced916e6049af9f28d5ec66`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `xarray/core/combine.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateOrdering (dims : List Dimension)` | the resulting-coordinate ordering check inside `combine_by_coords` — `xarray/core/combine.py:503-510` (the `for dim … if not (… monotonic …): raise ValueError` loop) | the modeled changed code: decides success/failure of the ordering validation |
| `Dimension.varies` | per-axis predicate `_infer_concat_order_from_coords` computes: `not all(index.equals(indexes[0]) for index in indexes[1:])` — `xarray/core/combine.py:74` — i.e. whether an axis is in the returned `concat_dims` (`combine.py:112`) | the "this axis is joined along (varies between inputs)" flag |
| `Dimension.index` | the resulting coordinate values along that axis: `concatenated.indexes.get(dim)` — `xarray/core/combine.py:505` (post-patch) | the ordered axis values whose monotonicity is tested |
| `isMonoInc` / `isMonoDec` *(deep model — A-reference)* | `pandas.Index.is_monotonic_increasing` / `is_monotonic_decreasing` — pandas, called at `combine.py:506-507` | pure spec of the order test; deep model of the unchanged callee, validated `== pandas` by axiom_check.py (G-AX) |
| `isMonotonic` | `indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing` — `combine.py:506-507` | acceptable-order predicate for one axis |
| `dimOK` / `allDimsOK` | the loop body's accept/reject decision and its conjunction over the iterated axes | success ⇔ no `ValueError` raised by the loop |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): the loop ranged over `concatenated.dims` filtered by
`if dim in concatenated` (`combine.py:502-504` pre-patch) — i.e. **all**
coordinate axes; the post-patch loop ranges over `concat_dims` — only the
**joined** axes (those for which `Dimension.varies` is true).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the list of coordinate axes of `concatenated` that the loop visits | `List Dimension` | one `Dimension` per coordinate dimension; list order is loop/iteration order (irrelevant — the decision is a conjunction, order-insensitive) |
| `dim in concat_dims` (axis is joined) vs identical across inputs | `Dimension.varies : Bool` | `True` ⇔ `dim ∈ concat_dims` ⇔ `not all(index.equals(indexes[0]) …)`; `False` ⇔ bystander axis (identical coord on every input) |
| `concatenated.indexes.get(dim)` — a `pandas.Index` of comparable values | `Dimension.index : List Int` | the axis values mapped to their **rank in a fixed total order** (`Int`); pandas monotonicity depends only on the order type of the values, so ranks are a faithful, order-preserving carrier. `len(index)` ↔ `index.length`. |
| `is_monotonic_increasing` (non-strict, equal neighbours allowed) | `isMonoInc` (`a ≤ b` pairwise) | pandas treats `[1,1,2]` as monotonic increasing; `isMonoInc` uses `≤` to match |
| `is_monotonic_decreasing` | `isMonoDec` (`a ≥ b` pairwise) | symmetric |
| `raise ValueError` vs return normally | `ok : Bool` (`false` ⇔ raises) | the loop raises iff some visited axis is non-monotonic; `validateOrdering` returns `false` in exactly that case |

A length-0 or length-1 axis is monotonic (both `isMonoInc`/`isMonoDec` return
`true` on `[]`/`[_]`), matching pandas (`pd.Index([])` and singletons are both
`is_monotonic_increasing` and `is_monotonic_decreasing`).

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `isMonoInc`/`isMonoDec` deep model ↔ pandas monotonicity (A-reference)
**Callee:** `pandas.Index.is_monotonic_increasing` / `.is_monotonic_decreasing`.
The order test is modeled **deeply** (`isMonoInc`/`isMonoDec` in the `pure`
region); there is **no consumed `monotonic` axiom**. pandas semantics: an index
is `is_monotonic_increasing` iff each element is `≤` the next (non-strict, so
repeats are allowed) and `is_monotonic_decreasing` iff each is `≥` the next.
This is exactly the front-recursive `≤`/`≥` pairwise scan the deep model encodes.

**Soundness check (G-AX):** `axiom_check.py` builds `pandas.Index` objects over
boundary cases (empty, singleton, sorted, reverse-sorted, with-repeats,
non-monotonic, the issue's `['a','c','b']` ordering) plus randomized fuzz, and
asserts `isMonoInc(values) == idx.is_monotonic_increasing` and
`isMonoDec(values) == idx.is_monotonic_decreasing` for each. Imports only
`pandas`. Exit 0 iff sound.

### 3.2 `Dimension.varies` ↔ `index.equals` across inputs (R, not axiom)
The flag is an **input** to the modeled code (a value `_infer_concat_order_from_coords`
already computed and returned as membership in `concat_dims`), not a callee the
modeled loop invokes. It is a type-refinement (R) carrier, not an axiom; G-CONF
exercises both its values.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`3151`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`dimOK`/`allDimsOK`/`isMonoInc`/`isMonoDec` (all I/R ops) to Python and compares
against `patch.diff`'s observable behaviour — does the patched
`combine_by_coords` raise the monotonic-global-indexes `ValueError`? — over a
grid of synthesized multi-axis datasets covering varying/non-varying ×
monotonic/non-monotonic axes.
