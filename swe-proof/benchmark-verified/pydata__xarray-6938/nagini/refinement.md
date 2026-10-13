# refinement.md — pydata__xarray-6938

The operation-by-operation correspondence between `model.py`'s implementation
(`to_index_variable` → `copy_coord`, plus the sibling `to_base_variable`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses a `@ContractOnly` axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX, NOT consumed), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fix site — `IndexVariable.to_index_variable` (`variable.py:2882`)

Gold hunk:
```
 def to_index_variable(self) -> IndexVariable:
     """Return this variable as an xarray.IndexVariable"""
-    return self
+    return self.copy()
```

| # | model.py impl op (`to_index_variable` / `copy_coord`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `self: CoordVar`, field `dims: List[int]` | `self: IndexVariable`, `self._dims: tuple[Hashable, ...]` | R | object ↔ `CoordVar`; dimension-name tuple ↔ `List[int]` of name codes; tuple equality ↔ `ToSeq` equality (mapping.md §2). |
| A2 | `return copy_coord(self)` | `return self.copy()` | A-reference | the changed operation (alias → independent copy) is modeled **deeply**: `copy_coord` builds a fresh `CoordVar` (`res = CoordVar(new_dims)` with `new_dims` a freshly-allocated element-wise copy of `self.dims`) and hands it full write permission, exactly as `IndexVariable.copy` → `Variable._replace` allocates `type(self)(copy.copy(self._dims), ...)`. There is no consumed axiom; the deep model is validated == the real callee by G-AX. |
| A3 | the element-copy loop in `copy_coord` (`new_dims.append(self.dims[i])`, invariant `ToSeq(new_dims) == s_old.take(i)`) | `copy.copy(self._dims)` inside `_replace` (`variable.py:985`) | R + I | a fresh sequence with the same elements; `copy.copy` of a tuple yields an equal, independent tuple (mapping.md §3.1). The loop is the spelled-out per-element copy over the `List[int]` carrier. |
| A4 | `CoordVar(new_dims)` returned, with `Result() is not self`, `Result().dims is not self.dims`, `Acc(Result().dims)` full | `type(self)(...)` fresh allocation returned by `_replace` | A-reference | distinct allocation ⇔ disjoint full write permission to the result's `dims`. The post-patch `_replace` constructs a new object; the model's permission separation is the faithful, machine-checked image of that. |
| A5 | `Requires(MustTerminate(3))` on `to_index_variable` (and `MustTerminate(2)`/`MustTerminate(1)` on `copy_coord`/the constructor; loop measures `len(dims) - i + 1`) | `return self.copy()` — a straight-line bounded copy that always returns | R | total correctness. The real callee has no loop and always returns; `swap_dims` (`dataset.py:3775-3776`) depends on `to_index_variable` RETURNING before it reassigns `var.dims`, and the F2P would time out (not pass) under a diverging implementation. Nagini's obligation system rejects any same-spec implementation that can loop or recurse forever (obligation leak check), closing the vacuous-satisfaction hole a partial-correctness spec admits. |

The discriminating content of the change — the result must be a **distinct
object with independent `dims` storage**, not the receiver — lives in the
postcondition triple `Result() is not self` / `Result().dims is not self.dims` /
full `Acc(Result().dims)` while the receiver keeps only `Acc(self.dims, 1/2)`.
The pre-patch `return self` reproduces the alias; `model_prepatch.py` returns
`self` and **fails** the postcondition `insufficient permission to access
Result().dims` (3/2 > 1) — exactly the spec sensing the change (G-DIFF). The
F2P test `test_to_index_variable_copy` checks precisely `a is not b` and that
`b.dims = ("y",)` leaves `a.dims == ("x",)`.

## B. The call site — `Dataset.swap_dims` (`dataset.py:3774`)

Gold hunk: an added local annotation `var: Variable` (annotation-only) above
the existing `var = v.to_index_variable(); var.dims = dims`. No runtime
behaviour changes here; this is the site that *consumes* the fix: it reassigns
`var.dims` right after the re-presentation, so the re-presentation aliasing the
original `v` is exactly what corrupted the source dataset (the issue). The model
captures the obligation that makes this safe: `to_index_variable` returns an
object whose `dims` may be reassigned without touching the receiver
(`to_index_variable` ensures `Result().dims is not self.dims` and full write
permission). No separate `model_prepatch` is needed for this annotation-only
hunk; site A's prepatch already exercises the aliasing the call site depends on.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `to_index_variable` ensures `Result().dims is not self.dims` + full `Acc(Result().dims)` | `var = v.to_index_variable(); var.dims = dims` (`dataset.py:3775-3776`) | I (obligation) | the post `var.dims = dims` is a write to the result's dims; the spec guarantees that write does not touch `self.dims`. This is the property the swap_dims fix relies on. |

## C. The sibling re-presentation — `Variable.to_base_variable` (`variable.py:539`)

Gold hunk: `self.dims` → `self._dims` (and `-> Variable` annotation). The `dims`
property returns `self._dims` (`variable.py:572-575`), so the read value is
identical (a micro-read change, no behaviour delta).

| # | model.py impl op (`to_base_variable`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | element-copy loop building `base_dims`, then `CoordVar(base_dims)` | `Variable(self._dims, ...)` (already a fresh `Variable`, `variable.py:541-543`) | R + I | `to_base_variable` already returned a fresh object pre- and post-patch; modeled as a fresh `CoordVar` carrying the same dim names. The `self.dims`→`self._dims` edit reads the identical value, so the model reads `self.dims` (= the same names). |

`to_base_variable` is included to pin the sibling re-presentation's value
semantics (result carries the receiver's dimension names); it is not an
independently-fixed behaviour, so it has no failing prepatch.

## D. Annotation-only hunks (no model node)

The return-type annotations (`-> Variable`, `-> IndexVariable`, `-> pd.Index`,
`-> Hashable`, `-> NoReturn`, `-> list[str] | None`), the `NoReturn` import in
`variable.py`, and the `var: Variable` local annotation in `dataset.py` are
type annotations with no runtime effect. They are recorded in mapping.md §1 and
have no operation in the model — nothing to refine (tag: not applicable; no
behaviour).

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — returning an independent copy instead of the receiver — is modeled
**deeply** via Nagini's permission discipline (the distinct-allocation /
disjoint-write-permission postcondition consumed in `to_index_variable` /
`copy_coord`, steps A2/A4, an **A-reference**), not hidden behind an axiom about
the function under change. There are **no consumed axioms** (no `@ContractOnly`
in the model). axiom_check.py validates the deep model == the real post-patch
callee (G-AX).

## F. verify(model) ⇒ resolved

`to_index_variable` verifies only if it returns a distinct object with full,
independent write permission to its own `dims` while keeping the receiver
read-only and unchanged (A2/A4) — which forbids the aliasing `return self`. By
R (object ↔ `CoordVar`, dim tuple ↔ `List[int]`, the `dims` setter ↔ field
reassignment) the verified model equals the gold `return self.copy()` on the
tested inputs; by G-AX the deep "independent allocation" model equals the real
`IndexVariable.to_index_variable` (A-reference) on the F2P scenario + 2000 fuzz
cases. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited deep-model reference — and the
gold patch resolves (G-RESOLVE). The trust point is exactly one of PLAN §1.1:
refinement fidelity (this document, G-EQ) plus the A-reference deep-model check
(G-AX); there is no axiom-soundness trust point because there is no consumed
axiom.
