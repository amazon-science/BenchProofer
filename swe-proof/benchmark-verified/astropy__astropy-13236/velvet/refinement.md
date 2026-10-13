# refinement.md — astropy__astropy-13236

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `classifyColumn` `do` block and the deep `classify` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed** /
**A-reference** (axiom legs — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (no axioms), so G-AX is not applicable. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The classification — `_convert_data_to_col`'s column-class selection

Gold hunk (the patch DELETES the structured-ndarray auto-mixin branch):
```
-        # Structured ndarray gets viewed as a mixin unless already a valid
-        # mixin class
-        if (not isinstance(data, Column) and not data_is_mixin
-                and isinstance(data, np.ndarray) and len(data.dtype) > 1):
-            data = data.view(NdarrayMixin)
-            data_is_mixin = True
-
```
Effect: with the branch gone, a multi-field structured array is no longer routed
to the `elif data_is_mixin` arm; it falls through to the same array dispatch as
any other array — the masked arm (`MaskedColumn`) if it carries a mask, else the
trailing `else` (`self.ColumnClass`: `MaskedColumn` in a masked table, `Column`
otherwise).

The model takes TWO inputs: the value's shape (`InputShape`) and the host
table's masked-ness (`tableIsMasked` ↔ `self.ColumnClass is MaskedColumn`),
because three sinks of the selection depend on the latter
(`_get_col_cls_for_table`, `self.ColumnClass`) while `masked_col_cls` does not
(mapping.md §1 note).

| # | Solution.lean impl op (`classifyColumn`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `input : InputShape`, `tableIsMasked : Bool` | the value `data` reaching the selection block, reduced to the distinctions the block tests, plus the table's masked-ness | R | numpy/Column value ↔ `InputShape`, `self.ColumnClass is MaskedColumn` ↔ `tableIsMasked` (mapping.md §2). G-CONF bridges each (shape, masked-ness) pair to the arm it lands in. |
| A2 | `match … | .alreadyColumn => if tableIsMasked then .maskedColumnKind else .columnKind` | `if isinstance(data, Column): col_cls = self._get_col_cls_for_table(data)` | I | identical arm: an existing column is upgraded to `MaskedColumn` when the table's `ColumnClass` is `MaskedColumn` (masked table), else keeps the ordinary column family. |
| A3 | `| .alreadyMixin => .mixinKind` | `elif data_is_mixin: … return col` | I | identical arm: an already-mixin value is the only one kept as a mixin column. |
| A4 | `| .structuredPlain => if tableIsMasked then .maskedColumnKind else .columnKind` | (post-image) the trailing `else: col_cls = self.ColumnClass` | I | **the behavioural change**: with the deleted branch gone, an unmasked structured array (not a Column, not a mixin, not masked) falls to `else` → `self.ColumnClass` (`Column` in an unmasked table, `MaskedColumn` in a masked one). The pre-image routed it to the mixin arm. |
| A5 | `| .structuredMasked => .maskedColumnKind` | (post-image) `elif isinstance(data, (np.ma.MaskedArray, Masked)): col_cls = masked_col_cls` | I | **the behavioural change**: a masked structured array now lands in the masked arm → `MaskedColumn` (whatever the table's masked-ness), preserving its mask. The pre-image routed it to the mixin arm. |
| A6 | `| .plainMasked => .maskedColumnKind` | `elif isinstance(data, (np.ma.MaskedArray, Masked)): col_cls = masked_col_cls` | I | unchanged arm: a single-field masked array → `MaskedColumn`, whatever the table's masked-ness. |
| A7 | `| .plainOther => if tableIsMasked then .maskedColumnKind else .columnKind` | `else: col_cls = self.ColumnClass` | I | unchanged arm: any other plain array → `self.ColumnClass` (`MaskedColumn` iff table masked). |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The classification
is a pure dispatch over the input shape and the table flag, modeled deeply and
tagged **R/I**.

Discriminating content of the change — a multi-field structured array is
classified by the same rule as any other array of its masked-ness
(`.structuredPlain → self.ColumnClass`-kind, `.structuredMasked →
.maskedColumnKind`) instead of being auto-routed to the mixin class — lives in
the `classify` arms A4/A5 (model) ⇔ the deletion of the
`data.view(NdarrayMixin)` branch (real). The pre-patch routed both structured
shapes to the mixin class; `Solution_prepatch.lean` reproduces that and **fails**
the frozen spec's `(input = .structuredPlain ∧ tableIsMasked = false) → out =
.columnKind`, `input = .structuredMasked → out = .maskedColumnKind`, and
`out = .mixinKind → input = .alreadyMixin` clauses (G-DIFF).

## B. verify(Solution) ⇒ resolved

`classifyColumn` verifies only if its result equals `classify input
tableIsMasked` AND the four discriminating clauses hold:
`(input = .structuredPlain ∧ tableIsMasked = false) → out = .columnKind`,
`input = .structuredMasked → out = .maskedColumnKind`,
`input = .alreadyMixin → out = .mixinKind`, and
`out = .mixinKind → input = .alreadyMixin` (so a structured array can NEVER be a
mixin). By R (the `InputShape`/`tableIsMasked`/`ColumnKind` ↔
value/masked-ness/class-kind bijection, mapping.md §2) the verified
classification equals the patched selection of `_convert_data_to_col` on the
modeled inputs. The two F2P tests pin exactly this:
`test_ndarray_mixin[False]` asserts `isinstance(t['a'], Column)` for a
structured array added to an unmasked table (A4 with `tableIsMasked = false`),
and `test_structured_masked_column` asserts `isinstance(t['a'], MaskedColumn)`
with its per-field mask preserved for a masked structured array (A5). The
PASS_TO_PASS `test_ndarray_mixin[True]` (an explicitly `.view(NdarrayMixin)`-ed
input) corresponds to `.alreadyMixin → mixin` (A3) and is preserved.

By G-CONF the R/I transliteration of `classify` agrees with `patch.diff`'s
behaviour over the full finite input space plus fuzz, and the transliterated
oracle is itself empirically cross-checked against astropy 5.2.2 post-patch on
all 12 (shape × table-masked-ness) cells (mapping.md §2). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axiom trust
points (no axioms); the only trust point is refinement fidelity (this doc,
G-EQ + G-CONF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — how a structured
array is classified — is modeled **deeply** (the spelled-out `classify`
dispatch, A4/A5), not hidden behind an axiom about the function under change.
There are no consumed axioms and no A-reference deep models of outside callees.
