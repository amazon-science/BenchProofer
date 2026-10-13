# refinement.md — astropy__astropy-14539

The operation-by-operation correspondence between `model.py`'s implementation
(the `count_differing_rows` impl region, the two comparator helpers
`compare_row_aware` / `compare_elementwise`, and the deep pure models
`is_vla_descriptor`, `row_granular_count`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (the proof uses a
`@ContractOnly` axiom's `Ensures`), **A-reference** (a deep model validated `==`
the real callee by axiom_check.py / G-AX, NOT consumed), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `TableDataDiff._diff` (`astropy/io/fits/diff.py:1452`)

Gold hunk (the per-column comparator selection):
```
-            elif "P" in col.format:
+            elif "P" in col.format or "Q" in col.format:
                 diffs = (
                     [ idx for idx in range(len(arra))
                       if not np.allclose(arra[idx], arrb[idx], ...) ],
                 )
             else:
                 diffs = np.where(arra != arrb)
             self.diff_total += len(set(diffs[0]))
```

`col.format` is a column's FITS layout string (e.g. `"PI(2)"`, `"QJ(2)"`, `"D"`).
The two descriptor letters `P` (32-bit) and `Q` (64-bit) mark a variable-length
array (VLA) column: each row holds a whole sub-array and the column is stored as
an object array of sub-arrays. **Both real branches accumulate the SAME
quantity** — `self.diff_total += len(set(diffs[0]))` — which is the number of
distinct differing ROWS (row-granular). The only thing the patch changes is
*which comparator* a column routes to:

* the VLA `elif` body computes `diffs` with a row-by-row `np.allclose` list
  comprehension; this comparator is applicable only on its invocation domain
  (VLA columns): `np.allclose` raises on an ordinary column whose stored
  values are non-numeric (e.g. a character column), so routing an arbitrary
  column here is an error;
* the `else` body computes `diffs = np.where(arra != arrb)`; this comparator is
  applicable only to a regular (non-object) ndarray column. Handed a genuine
  VLA column (an object array of multi-element sub-arrays) it RAISES
  `ValueError: truth value of an array ... is ambiguous` (verified in-container,
  axiom_check.py A-ref 2c). For an ordinary fixed-width column (1-D scalar OR
  multi-dimensional fixed) it works and is ALSO row-granular: `set(diffs[0])`
  collapses the per-element index tuples to distinct rows.

Pre-patch, only `P` was recognised; a `Q`-marked VLA column fell through to the
`else` (`np.where`) comparator, which is not applicable to it.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fmt: List[int]` | `col.format` (a `str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2); membership of a character ↔ membership of its code point. |
| A2 | `is_vla_descriptor(ToSeq(fmt))` = `contains_cp(fmt,80) or contains_cp(fmt,81)` selecting the branch | `"P" in col.format or "Q" in col.format` selecting the `elif` vs `else` body | A-reference | the changed branch predicate is modelled **deeply** (the spelled-out membership of code points 80/81 in the pure region); there is NO consumed axiom. G-AX (axiom_check.py A-ref 1) validates `is_vla_descriptor == ("P" in fmt or "Q" in fmt)` on 25 boundary + 20000 fuzz format strings. `'P'→80`, `'Q'→81` (mapping.md §2). |
| A3 | `compare_row_aware(fmt, row_mismatches)` → `row_granular_count(row_mismatches)`, guarded by `Requires(is_vla_descriptor(ToSeq(fmt)))` (applicable only on its VLA invocation domain) | the `elif` body: `diffs = ([idx for idx in range(len(arra)) if not np.allclose(arra[idx],arrb[idx],...)],)`; then `self.diff_total += len(set(diffs[0]))` | A-reference | modelled deeply by `row_granular_count` (a row contributes 1 iff `row_mismatches[i] > 0`). `row_mismatches[i]` is grounded as the number of positions at which the two sub-arrays of row i disagree at the default exact tolerances, under the same alignment `np.allclose` itself uses (see A5). After `set(diffs[0])`, the real path counts exactly the rows that are not close — i.e. rows with ≥1 disagreeing aligned position. G-AX validates `row_granular_count == real diff_total` on the F2P data + 13 boundary + 20000 fuzz VLA columns whose per-side widths are drawn INDEPENDENTLY, so unequal-length rows are inside the validated domain (A-ref 2a). |
| A4 | `compare_elementwise(fmt, row_mismatches)` → `row_granular_count(row_mismatches)`, guarded by `Requires(not is_vla_descriptor(ToSeq(fmt)))` | the `else` body: `diffs = np.where(arra != arrb)`; `self.diff_total += len(set(diffs[0]))` | A-reference | modelled deeply by the SAME `row_granular_count`: the real `else` path is also row-granular — `len(set(np.where(arra!=arrb)[0]))` is the number of distinct differing rows even for a multi-dimensional fixed-width column (G-AX A-ref 2b confirms equality on multi-element fixed-width columns, where a naive element-sum would diverge). The `Requires(not is_vla_descriptor(...))` precondition encodes the comparator's **applicability**: on a genuine VLA (object-array, multi-element) column the real `np.where` comparator RAISES (G-AX A-ref 2c). It is the unforgeable control-flow discriminator: a verifying impl may route a column here only if the column is not VLA. |
| A5 | `np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)` (default tolerances) | rejection by `np.allclose`'s OWN per-position closeness verdict, under its OWN alignment of the two sub-arrays | R | at the constructor defaults `rtol=atol=0.0` (mapping.md §1) `np.allclose` reduces to the conjunction of its per-position `isclose` verdict, and `row_mismatches[i]` counts exactly the positions THAT verdict rejects, under the SAME alignment (numpy's), not under a hand-rolled length penalty. It is deliberately NOT exact equality: `allclose` evaluates in float64 regardless of tolerance, so on int64 magnitudes at/above `2**53` it is strictly COARSER than `!=` and calls neighbouring values close. Grounding this step in `!=` would make the spec claim differing rows the real comparator reports as identical, on exactly the 64-bit magnitudes the `Q` descriptor carries; grounding it in the comparator's own verdict is what makes `row_mismatches[i] == 0` mean `np.allclose(...) is True`. Two sub-arrays of unequal length that still align are therefore judged equal iff every aligned position agrees — a length difference alone is NOT a difference — and a pair with no alignment lies outside the comparison's domain (the real `np.allclose` raises, and the grounding raises identically rather than inventing a count). G-AX A-ref 2a exercises this class directly (per-side widths drawn independently). Precision is not the tested behaviour, so no float encoding is needed (tolerances are 0). |
| A6 | return `total` (an `int` count) | `self.diff_total += len(set(diffs[0]))` (the per-column contribution to the running total) | R | the modeled function returns the single column's contribution to `diff_total`; the real code accumulates it. The F2P tests observe `diff_total` and `diff_ratio = diff_total / total_values`; the per-column contribution is the only thing the change affects. |

## B. The discriminating clause (G-DIFF)

The fixed behaviour the spec senses: a column marked variable-length by EITHER
descriptor (`P` or `Q`) is routed to the row-aware comparator, never to the
element-wise comparator that is not applicable to it — and, symmetrically, a
column NOT so marked is routed to the element-wise comparator, never to the
row-aware comparator whose per-row inspection is not applicable to an
arbitrary ordinary column. The postcondition is the single row-granular
guarantee

  `Implies(True, Result() == row_granular_count(ToSeq(row_mismatches)))`

(both comparators yield it when applicable); the *discriminators* are the two
applicability preconditions — `compare_elementwise`'s
`Requires(not is_vla_descriptor(ToSeq(fmt)))` and `compare_row_aware`'s
`Requires(is_vla_descriptor(ToSeq(fmt)))`. Together they pin the routing to
EXACTLY the descriptor recognition: a verifying dispatcher must send a column
to the row-aware comparator iff its descriptor designates variable length
(over-broad routing, e.g. sending some ordinary columns row-aware, is rejected
just like the under-broad pre-patch routing).

All three functions additionally carry a `MustTerminate` obligation (total
correctness): the real per-column comparison is bounded work that always
returns, so a diverging implementation — which would satisfy the row-granular
postcondition only vacuously — is rejected by the obligation leak check. The
dispatcher holds measure 3 and each comparator measure 2, so the dispatch call
is permitted; each comparator's loop consumes the obligation with the strictly
decreasing, bounded-below measure `i`.

`model_prepatch.py` keeps the spec byte-identical (`same_spec` = True) and
reverts the impl's recognition to `contains_cp(ToSeq(fmt), 80)` (only `P`, the
pre-patch `"P" in col.format`). On a `Q`-only format the buggy impl takes the
`else` branch and calls `compare_elementwise`, whose applicability precondition
`not is_vla_descriptor(ToSeq(fmt))` is **violated** (the column IS VLA), so
verification **fails at that call site** — the spec sensing that the bug routes a
variable-length column through the inapplicable element-wise comparator. This is
exactly the real pre-patch failure: on the F2P `QJ(2)` column (uniform 2-element
rows) the real `else` path `np.where(arra != arrb)` RAISES, crashing `_diff` and
failing both `test_identical_tables` (the new identical `QJ(2)` column) and
`test_different_table_data` (the new differing `QJ(2)` column, which must lift
`diff_total` 13 → 15). One `model_prepatch.py` suffices: both F2P tests exercise
the single descriptor-recognition fix.

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R or A-reference. The one operation that genuinely *changed* — the
VLA-descriptor recognition and the comparator-applicability it governs — is
modelled **deeply** (`is_vla_descriptor`, `row_granular_count`, and the two
comparator functions in the pure/impl regions), not hidden behind an axiom about
the function under change. There is **no consumed `@ContractOnly` axiom** (the
`axioms` region is empty by design): the unchanged `np.allclose` primitive is
summarised by `row_mismatches`, which carries its OWN per-position verdicts at
the default tolerances rather than those of an idealised exact-equality test
(A5 — the verdict is strictly coarser than `!=` above `2**53`). The real callees (`"P"/"Q" in col.format`; the
`np.allclose`/`np.where`-based `diff_total`; the `np.where` raise on a VLA
column) appear only as **A-references** that G-AX validates the deep models
against.

## D. verify(model) ⇒ resolved

`count_differing_rows` verifies only if every column's contribution equals the
row-granular count (the single postcondition, met by both comparators) AND a
column is routed to `compare_elementwise` only when it is not VLA AND to
`compare_row_aware` only when it IS VLA (the two applicability
preconditions — the routing is pinned in both directions). By R (str ↔ List[int]; `np.allclose` at zero
tolerance ↔ element equality; per-column contribution ↔ `diff_total +=`) the
verified counter equals the patched `_diff` per-column accumulation on the tested
inputs; by G-AX the deep models equal the real layout test, the real row-aware
and element-wise comparators (both row-granular), and the real element-wise
comparator's raise on a VLA column (A-references). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited references — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom/reference soundness (G-AX) and refinement
fidelity (this document, G-EQ); there are no consumed axioms, so the first
reduces to the A-reference equalities and the applicability check in
axiom_check.py.
