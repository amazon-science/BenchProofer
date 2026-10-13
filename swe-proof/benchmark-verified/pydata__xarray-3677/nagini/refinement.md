# refinement.md — pydata__xarray-3677

The operation-by-operation correspondence between `model.py`'s implementation
(the `merge_method` impl region and the deep `as_mapping` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, proof uses the axiom's
`Ensures`, and **A-reference**, a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The merge site — `Dataset.merge` (`xarray/core/dataset.py:3548`)

Gold hunk (`dataset.py`, inside `merge`, just before `dataset_merge_method`):
```
  _check_inplace(inplace)
+ other = other.to_dataset() if isinstance(other, xr.DataArray) else other
  merge_result = dataset_merge_method(
      self, other, overwrite_vars=..., compat=..., join=..., fill_value=...,
  )
```
With the default `overwrite_vars=frozenset()`, `dataset_merge_method` builds
`objs = [dataset, other]` (`merge.py:817-819`) and passes them to `merge_core`,
which iterates each non-Dataset operand's `.items()` (`merge.py:394`). The fix
ensures the `other` operand is mapping-shaped (a Dataset) before that.

| # | model.py impl op (`merge_method`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `receiver: Operand`, `other: Operand` | `self` (a `Dataset`) and `other` (the `CoercibleMapping`/`DataArray` arg) of `merge` | R | `Dataset`/`DataArray` ↔ `Operand`; `is_mapping`/`name`/`value` are the touched fields (mapping.md §1-2). |
| A2 | `is_array_shaped(other)` == `not other.is_mapping` | `isinstance(other, xr.DataArray)` | R + I | a DataArray is exactly the array-shaped (non-mapping) operand; a Dataset is mapping-shaped (mapping.md §2). The boolean test is the identical control decision. |
| A3 | `second = as_mapping(other)` when array-shaped, else `second = other` (the unchanged operand object) | `other = other.to_dataset() if isinstance(...) else other` | R + A-reference + I | Array-shaped arm (`then`): `to_dataset()` (no `dim`) → a one-variable Dataset keyed by the array's name (`_to_dataset_whole`, `dataarray.py:462`); modeled **deeply** as `as_mapping` (an ordinary verified fn producing a mapping-shaped operand with the same name/value); no consumed axiom; validated **== the real `DataArray.to_dataset()`** out-of-band by G-AX (axiom_check.py): the product is a `Dataset` (has `.items()`) carrying the same single `{name: value}` variable (mapping.md §3.1) — this is the R + A-reference part. Mapping-shaped arm (`else`): `second = other` keeps the **identical object** the gold `else` keeps (the existing Dataset, untouched) — the identical concrete no-op (the I part). The model PINS this with `Implies(not Old(is_array_shaped(other)), Result()[1] is other)`, so a refined impl may not rebuild `other` on the no-op arm (which under the bijection would drop a multi-variable Dataset's later variables — the lossy-rebuild hole §B). |
| A4 | `result = [receiver, second]` | the operand list `objs = [dataset, other]` that `dataset_merge_method` builds and hands to the core merge (`merge.py:817-819, 834`) | R + I | building the two-operand list, receiver first, normalized second operand second — the identical data flow into the core routine. The second element is `second` from A3: either `as_mapping(other)` (array-shaped arm) or `other` itself (mapping-shaped arm, identity-pinned per A3). |

The discriminating content of the change — every operand reaching the core
exposes the named-entry interface — lives in the postconditions
`Result()[1].is_mapping` (the normalized second operand) together with the
preservation clause `Result()[1].name == other.name and Result()[1].value ==
other.value` (it carries the same single variable) and the identity clause
`Implies(not Old(is_array_shaped(other)), Result()[1] is other)` (the
already-mapping-shaped operand passes through as the same object, closing the
lossy-rebuild hole — §B). When `other` is array-shaped the pre-patch passes it
through unconverted; `model_prepatch.py` reproduces that (`second = other`, no
`as_mapping`) and **fails** the postcondition `Result()[1].is_mapping`, which is
exactly the spec sensing the change (G-DIFF). At runtime that unconverted
array-shaped operand is what triggers the gold traceback `AttributeError:
'DataArray' object has no attribute 'items'`.

## B. Why the postcondition is tight (verify ⟹ correct)

The postcondition pins behaviour structurally on the actual inputs, not on an
oracle:
* `len(Result()) == 2` and `Result()[0] is receiver` — the receiver passes
  through; an impl cannot drop it or pad the list.
* `Result()[0].is_mapping and Result()[1].is_mapping` — EVERY operand handed to
  the core is mapping-shaped (the property the bug violates).
* `Result()[1].name == other.name and Result()[1].value == other.value` — the
  second operand carries the second input's single named name/value. NOTE
  (scope): the `Operand` carrier abstracts an entire mapping-shaped operand to
  ONE `(name, value)` pair, so this clause alone witnesses only that one pair —
  it does NOT, by itself, forbid an impl that *rebuilds* a fresh single-entry
  operand from `other` on the already-mapping-shaped branch (which, refined,
  drops every variable of a multi-variable Dataset beyond the first). That
  lossy-rebuild cheat verifies against name/value preservation alone.
* `Implies(not Old(is_array_shaped(other)), Result()[1] is other)` — the
  IDENTITY-pass-through clause that closes the gap above. On the
  already-mapping-shaped branch (`other` is a Dataset, the gold patch's `else`
  arm leaving `other` untouched) the second result operand must be the *same
  object* as the input `other`, not a reconstruction. Because object identity
  is unforgeable, a lossy rebuild — which under the bijection (mapping.md §2)
  produces a *different* Dataset carrying only `other`'s first variable — cannot
  satisfy it. This is the cheap, correct lever for the lossy-abstraction class
  (one carrier object abstracting an N>1-element container): pin identity on the
  no-op branch rather than try to witness every dropped element through a
  single-pair carrier. The `Old(...)` framing is required: the shape test must
  read the pre-state (Nagini re-evaluates the bare `is_array_shaped(other)` in
  the post-state's pure-frame and the gold-faithful impl then fails to discharge
  the clause). On the array-shaped branch the clause is vacuously true and the
  conversion (A3) governs instead.
* read-only inputs are required AND ensured at fractional permission
  (`Acc(receiver.*, 1/2)`/`1/4`, `Acc(other.*, 1/2)`/`1/4`) — directive 5 — so a
  wrong impl cannot satisfy the spec by overwriting an input.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the conditional normalization of the second operand — is modeled
**directly** (the `is_array_shaped`/`as_mapping`/list-build sequence in
`merge_method`). The conversion callee `to_dataset()` it calls is **unchanged**,
modeled **deeply** as `as_mapping` (an **A-reference**, G-AX-checked) rather than
behind an axiom about the function under change. There is no consumed axiom.

## D. verify(model) ⇒ resolved

`merge_method` verifies only if its second result operand is mapping-shaped (A3)
and carries `other`'s name and value (preservation), for both the
already-mapping and the array-shaped input. By R (Dataset/DataArray ↔ Operand,
`isinstance` ↔ shape tag) and by G-AX (the deep `as_mapping` == the real
`DataArray.to_dataset()`, A-reference), the verified routine equals the gold
patch's `other = other.to_dataset() if isinstance(other, xr.DataArray) else
other` followed by the unchanged `objs = [dataset, other]` construction.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited conversion — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
