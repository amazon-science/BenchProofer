# mapping.md — pydata__xarray-3677

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ef6e6a7b86f8479b9a1fecf15ad5b88a2326b31e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo file under change: `xarray/core/dataset.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineKeyed (base : KeyedMap) (other : Operand)` | the body of `Dataset.merge` from the operand-handling line through the core-combine call — `xarray/core/dataset.py:3597-3613` (the `merge_result = dataset_merge_method(self, other, ...)` site and the operand it feeds) | the modeled changed function (the added operand-normalization step + the core-combine call) |
| `base : KeyedMap` | `self` — the receiving `Dataset` | the receiver's variable mapping `{name: variable}` ↔ a `List (Nat × Int)` (mapping.md §2) |
| `other : Operand` | `other` — the merge operand, a `Dataset`/mapping (`keyed`) **or** a `DataArray` (`single`) | `keyed es ↔` a `Dataset`/mapping exposing `.items()`; `single k v ↔` a `DataArray` named `k` carrying value `v`, which has no `.items()` |
| `coerceOperand` | `other.to_dataset() if isinstance(other, xr.DataArray) else other` (`dataset.py:3607`, the added line) | the **changed** op: normalize a lone keyed value into a one-variable collection; pass a collection through |
| `combineCore` *(deep model — A-reference)* | `dataset_merge_method(self, other, ...)` (`xarray/core/merge.py:798`) and its downstream `coerce_pandas_values` (`merge.py:369`, the `for k, v in obj.items()` loop) — the unchanged core-combine machinery | pure spec: fuse the base mapping with the operand's key/value pairs; **undefined on an operand exposing no `.items()`** (a `DataArray`), validated == real `dataset_merge_method` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `combineSpec` | the intended behavior of `Dataset.merge`'s operand-handling tail | pure spec the method's `ensures` pins |

The pre-patch behavior the change fixes (refinement audit only, not named in the
consumer spec view): `other` was fed **directly** to `dataset_merge_method`,
whose `coerce_pandas_values` iterates `obj.items()`; a `DataArray` has no
`.items()`, raising `AttributeError: 'DataArray' object has no attribute
'items'` (the reported crash, `merge.py:394`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Dataset`'s variable mapping `{name: value}` | `KeyedMap = List (Nat × Int)` | a variable named `n` holding scalar value `v` ↔ `(id n, v)`, where `id` is any injective name tag (only name equality and value identity are observed by the F2P test `assert_identical`) |
| the merge operand `other` | `Operand` | a `Dataset`/dict mapping ↔ `.keyed entries`; a `DataArray` named `k` holding scalar `v` ↔ `.single (id k) v` |
| `other.to_dataset()` | `coerceOperand (.single k v) = .keyed [(k,v)]` | a named `DataArray` becomes a one-variable `Dataset` `{name: that array}` ↔ a one-entry mapping `[(k, v)]`; a `Dataset` operand is unchanged ↔ `coerceOperand (.keyed es) = .keyed es` |
| `dataset_merge_method(self, op, ...)` on a mapping operand | `combineCore base (.keyed es) = .ok (base ++ es)` | the no-conflict union of the two variable mappings (base entries first) — the regime the F2P scenario exercises (disjoint names `a`, `b`) |
| `dataset_merge_method(self, da, ...)` on a raw `DataArray` | `combineCore base (.single _ _) = .error .notKeyed` | the real call raises `AttributeError` inside `coerce_pandas_values` (`obj.items()`) ↔ the modeled `.notKeyed` failure |
| the dtype/shape/attrs of a variable | dropped (`Int` value tag only) | the F2P scenario merges scalar int variables; only presence-by-name and value are observed by `assert_identical`, so richer structure is observationally irrelevant and not modeled (avoids over-claiming) |

Names are modeled as `Nat` tags: the operand-handling tail only ever asks "is
this operand a collection exposing key/value pairs, or a lone keyed value?" and,
on the union, juxtaposes the two mappings — it never inspects name internals. A
`Nat` tag is a faithful, total carrier for "which variable name".

The modeled domain is the **no-conflict / disjoint-name** regime
(`combineEntries = base ++ es`), which is exactly the F2P scenario
(`Dataset({"a": 0})` merged with a `DataArray(name="b")`): the change is about
*reaching* the combine at all for a `DataArray` operand, not about conflict
resolution among shared names. Conflict handling (`compat`) is unchanged by this
patch and is not modeled.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `combineCore` deep model ↔ `dataset_merge_method` / `coerce_pandas_values` (A-reference)
**Callee:** `xarray.core.merge.dataset_merge_method` (→ `merge_core` →
`coerce_pandas_values`), unchanged by this patch. The operand-handling tail
invokes it on whatever operand it is handed. Its two observable behaviors on the
modeled (disjoint-name) inputs:

* on a mapping/`Dataset` operand exposing key/value pairs, the merge succeeds and
  the result `Dataset` holds the union of the two variable mappings —
  `combineCore base (.keyed es) = .ok (base ++ es)`;
* on a raw `DataArray` operand (no `.items()`), the merge raises
  `AttributeError: 'DataArray' object has no attribute 'items'` inside
  `coerce_pandas_values` — the crash the issue reports —
  `combineCore base (.single _ _) = .error .notKeyed`.

This is an **A-reference**, not a consumed axiom: the core-combine operation is
modeled deeply (`combineCore`) and validated against the real callee by G-AX,
which constructs real `xarray` objects and asserts (a) `dataset_merge_method`
applied to a `Dataset` operand yields the union of variable names/values, and
(b) `dataset_merge_method` applied to a raw `DataArray` raises `AttributeError`.

The patched function under spec (`combineKeyed` ↔ `Dataset.merge`'s tail) is
**never** axiomatized — only the unchanged core-combine callee is modeled
(SPEC_GUIDE §0.7). The `.to_dataset()` re-expression that the patch ADDS is the
changed op; it is modeled concretely as `coerceOperand` (an **I** step in
refinement.md), not axiomatized.

### 3.2 Flag/branch dependency
`coerceOperand` re-expresses exactly when the operand is a lone keyed value
(`.single` ↔ `isinstance(other, xr.DataArray)`); a collection passes through
(`.keyed` ↔ the `else` branch). G-AX therefore exercises `dataset_merge_method`
on both configurations the impl reaches: a `Dataset` operand (post-coercion, the
success leg) and a raw `DataArray` operand (the pre-coercion crash that motivates
the re-expression).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`3677`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`combineSpec` / the impl's branch selection (coerce-then-combine) to Python and
bridges I/O via the §2 bijection, leaving the A-tagged callee behavior
(`dataset_merge_method` success / `DataArray` crash) as the real observable
outcome. It diffs the shadow against `patch.diff`'s patched-`Dataset.merge`
behavior over ≥10⁵ fuzzed `(base mapping, operand)` pairs in the disjoint-name
regime.
