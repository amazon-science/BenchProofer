# refinement.md — astropy__astropy-13236

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_column_kind` impl region, plus the deep `selected_kind` reference
in the `pure` region) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The modeled site — `Table._convert_data_to_col` (`astropy/table/table.py:1179`)

The patch is a single hunk that DELETES the structured-ndarray clause
(`table.py:1242-1247` at base_commit):

```
-        # Structured ndarray gets viewed as a mixin unless already a valid
-        # mixin class
-        if (not isinstance(data, Column) and not data_is_mixin
-                and isinstance(data, np.ndarray) and len(data.dtype) > 1):
-            data = data.view(NdarrayMixin)
-            data_is_mixin = True
```

After deletion the value of `data_is_mixin` reaching the class-selection
if/elif chain (`table.py:1259-1313`) is exactly the one produced by the
unchanged handler block above the deleted clause, and the chain then runs
unchanged. The model abstracts each branch of that chain to the column *kind*
it produces (the only test-observable distinction; the exact subclass upgrade
done inside a branch is unchanged by the patch and outside the modeled delta —
see mapping.md §1, §3).

### A.1 The classification inputs (booleans)

| # | model.py construct | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `is_column: bool` | `isinstance(data, Column)` (`table.py:1244,1252,1259`) | R | one runtime instance test ↔ one boolean bit (mapping.md §2). |
| A2 | param `is_mixin: bool` | `data_is_mixin` as set by the unchanged handler block (`table.py:1218,1235`) — i.e. the value BEFORE the deleted clause | R | the mixin classification bit; the deleted clause is the only thing between the handler block and the if/elif chain that could change it, and the model omits it exactly as the patch does (see A.2). |
| A3 | param `data0_is_mixin: bool` | `data0_is_mixin = self._is_mixin_for_table(data[0])` (`table.py:1224`) | R | "first element is a mixin" bit. |
| A4 | params `is_ndarray`, `is_structured` | `isinstance(data, np.ndarray)`, `len(data.dtype) > 1` (in the DELETED clause) | R | these two bits appear in the model ONLY as inputs the post-patch result must be independent of; the post-patch repo never consults them (the clause is gone). See A.2. |
| A5 | param `is_masked: bool` | `isinstance(data, (np.ma.MaskedArray, Masked))` (`table.py:1286`) | R | one instance test ↔ one bit. |
| A6 | param `is_none`, `has_dtype` | `data is None` (`table.py:1292`), `hasattr(data, 'dtype')` (`table.py:1300`) | R | branch guards downstream; in the modeled tests they are false (a structured/masked ndarray is neither None nor lacking a dtype), encoded by the `Requires` domain facts (mapping.md §4). |
| A6b | param `seq_masked: bool` | `isinstance(_convert_sequence_data_to_array(data, dtype), np.ma.MaskedArray)` — the class pick inside the no-dtype branch (`table.py:1300-1310`) | R | one bit: whether the dtype-less input's sequence conversion yields a masked array (list with embedded masked entries). The branch (and `_convert_sequence_data_to_array`) is UNCHANGED by the patch; the bit is carried so the model's total cascade matches the real chain on dtype-less inputs (`seq_masked ⇒ not has_dtype`, mapping.md §4). |

### A.2 The decision (the deleted clause and the surviving cascade)

| # | model.py impl op (`select_column_kind`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A7 | `data_is_mixin = is_mixin` (no structured override) | the DELETION of the `if (... isinstance(data, np.ndarray) and len(data.dtype) > 1): data = data.view(NdarrayMixin); data_is_mixin = True` clause | I | the model's post-patch impl simply does NOT contain the structured override, exactly matching the patch's deletion: `data_is_mixin` keeps the value from the handler block. The pre-patch override is reproduced verbatim only in `model_prepatch.py` (which therefore fails the spec — G-DIFF). |
| A8 | `if data_is_mixin: return KIND_MIXIN()` | `elif data_is_mixin:` → `col = col_copy(...)/data; return col` (`table.py:1268-1273`) | I + R | identical control-flow guard; the branch body (return the object as its mixin class) is abstracted to the result kind code `KIND_MIXIN` (R, mapping.md §1). |
| A9 | `if (not is_column) and data0_is_mixin: return KIND_SEQ_MIXIN()` | `elif data0_is_mixin:` → `data[0].__class__(data)` (`table.py:1275-1280`) | I + R | same guard (reached only when not a Column and not a mixin); body → `KIND_SEQ_MIXIN`. |
| A10 | `if is_masked: return KIND_MASKED()` | `elif isinstance(data, (np.ma.MaskedArray, Masked)): col_cls = masked_col_cls` → builds a `MaskedColumn` (`table.py:1286-1290,1315-1316`) | I + R | same guard; body → `KIND_MASKED`. This is the branch a masked structured ndarray now reaches post-patch (`test_structured_masked_column`). |
| A10b | `if (not is_none) and (not has_dtype) and seq_masked: return KIND_MASKED()` | `elif not hasattr(data, 'dtype'): data = _convert_sequence_data_to_array(data, dtype); col_cls = masked_col_cls if isinstance(data, np.ma.MaskedArray) else self.ColumnClass` (`table.py:1300-1310`), masked-conversion half | I + R | same guard position (after the None check in the real chain; the model's `not is_none` conjunct encodes that the None branch wins first); the masked half of the body → `KIND_MASKED`. Unchanged by the patch — carried so the model's cascade is faithful on dtype-less inputs (e.g. a list with embedded masked entries → `MaskedColumn`). |
| A11 | `else: return KIND_COLUMN()` | the `else: col_cls = self.ColumnClass` (`table.py:1312-1313`), and the None / Column-upgrade branches and the unmasked half of the no-dtype branch, all building a plain `Column`/`ColumnClass` | I + R | the catch-all; body → `KIND_COLUMN`. This is the branch an unmasked structured ndarray now reaches post-patch (`test_ndarray_mixin[False]`). |

The branch guards (A8–A11) are evaluated in the same first-match order as the
real `if/elif` chain; the model's `selected_kind` pure function encodes that
exact order and the post-patch impl returns it (the `Result() == selected_kind`
postcondition). Because `selected_kind` does **not** mention `is_structured` /
`is_ndarray`, the spec pins the load-bearing property of the patch: the result
is independent of structured-ness (postconditions A.3 below).

## B. The discriminating content (what G-DIFF senses)

The change's whole effect is: a structured (multi-field) ndarray that is
neither an existing `Column` nor a mixin must be classified by the SAME cascade
as any plain array — `KIND_MASKED` when masked, `KIND_COLUMN` otherwise —
rather than being diverted into `KIND_MIXIN`.

- model.py postconditions:
  `Implies(is_structured and is_ndarray and not is_column and not is_mixin and not data0_is_mixin and is_masked, Result() == KIND_MASKED())`
  and the `not is_masked → KIND_COLUMN()` twin.
- `model_prepatch.py` reproduces the deleted override (`if (not is_column) and
  (not data_is_mixin) and is_ndarray and is_structured: data_is_mixin = True`)
  and therefore returns `KIND_MIXIN` for such inputs, FAILING
  `Result() == selected_kind(...)` (verifier reports exactly this clause).
- The two F2P tests are the two halves of this: `test_ndarray_mixin[False]`
  (unmasked structured ndarray → `Column`, i.e. `KIND_COLUMN`) and
  `test_structured_masked_column` (masked structured ndarray → `MaskedColumn`,
  i.e. `KIND_MASKED`).

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axiom

Every step above is R or I. The changed operation — a control-flow decision
over boolean classification bits — is modeled **deeply**: the cascade is
spelled out in the impl and in the `selected_kind` reference, with no opaque
callee consumed inside an `Ensures`. There is therefore **no `@ContractOnly`
axiom** (A-consumed) and **no A-reference deep model of a stdlib callee**: the
`axioms` region is empty. The booleans the cascade branches on are
R-refinements of unchanged `isinstance`/predicate evaluations (A1–A6), not
axiomatized callees. `axiom_check.py` (G-AX) instead validates that the real
`Table._convert_data_to_col` produces the model's decided kind on the F2P
inputs and on a structured-ndarray fuzz of the classification bits.

## C.1 Termination (`MustTerminate`) — an obligation, tag I

The precondition also states `MustTerminate(1)`. This is not a bit, not a
domain restriction and not a narrowing: it obliges the implementation to reach
a decision on every input already admitted.

- **TRUE of the real function.** `Table._convert_data_to_col`
  (`astropy/table/table.py:1179-1324` at `base_commit`) contains **zero loops
  and zero self-recursive calls** (checked by walking the AST of the function at
  `base_commit`): it is a straight-line `if`/`elif` chain over
  `isinstance`/`hasattr`/`len(dtype)` probes. It therefore terminates on every
  admissible input, before and after the patch — and since the gold patch is a
  pure DELETION (it only removes the structured-ndarray clause), it cannot
  introduce divergence. Tag **I**: the model's obligation matches a property the
  real operation has.
- **Why it is load-bearing.** Nagini proves PARTIAL correctness unless a method
  demands otherwise. Without this obligation every clause in §B is claimed only
  of runs that reach the `return`, so an implementation that never returns on
  the structured-ndarray family satisfies them **vacuously there** and VERIFIES,
  while its faithful patch hangs `test_ndarray_mixin[False]` — a direct
  `verify`-does-not-`resolve` break. This was measured on this cell, not
  hypothesised: the rival verified as shipped and is rejected once the
  obligation is present (`Obligation leak check failed. Loop might not take all
  unsatisfied obligations from the context.`). It is frozen as the
  `properties.py` reject case `weak-nonterminating-on-structured`.
- **It over-fits nothing.** The obligation costs the gold-faithful `model.py`
  nothing (it still verifies) and the structurally-different positive control
  still verifies, so correct alternative implementations are unaffected. It also
  does not rescue `model_prepatch.py`, whose divergence is a wrong VALUE
  (`KIND_MIXIN` where the cascade demands `KIND_COLUMN`/`KIND_MASKED`) rather
  than a hang: the twin still fails on the master postcondition.

## D. verify(model) ⇒ resolved

`select_column_kind` verifies only if it TERMINATES (§C.1 — so the guarantee is
about a decision actually reached, not a vacuous claim about a run that never
returns) and its result equals the first-match cascade
`selected_kind` (which never consults structured-ness) — so a verifying impl
classifies a non-column, non-mixin structured ndarray by mask-status alone
(`KIND_MASKED` / `KIND_COLUMN`), exactly the gold patch's behaviour (A7–A11).
By R (each boolean ↔ its runtime predicate; each kind code ↔ the column class
that branch builds, mapping.md §1–§2) the verified decision equals the gold
patch's post-deletion class selection on the tested inputs, and the gold patch
resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point because no axiom is
consumed (G-AX reduces to the executable decision-equivalence check).
