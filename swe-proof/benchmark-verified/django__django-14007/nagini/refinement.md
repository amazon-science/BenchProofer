# refinement.md — django__django-14007

The operation-by-operation correspondence between `model.py`'s implementation
(the `execute_returning` impl region, the `apply_row` helper, the deep
`fold_chain` model, and the `step` axiom) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**,
the deep model is validated `==` the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit`, confirmed; it is the real correctness oracle, G-RESOLVE).

## A. The change site — `SQLInsertCompiler.execute_sql` (`compiler.py:1403`)

Gold hunk (semantically): the three backend-gated branches that previously each
`return`ed the raw rows are turned into assignments to a local `rows`, and after
the `with self.connection.cursor()` block the patch adds:

```python
cols = [field.get_col(opts.db_table) for field in self.returning_fields]
converters = self.get_converters(cols)
if converters:
    rows = list(self.apply_converters(rows, converters))
return rows
```

i.e. the freshly returned raw rows are now run through the per-column converter
pipeline before being returned (previously they were returned raw).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rows: PSeq[PSeq[int]]` | the local `rows` assigned by one of the three backend-gated row-source branches (`fetch_returned_insert_rows` / `[fetch_returned_insert_columns(...)]` / `[(last_insert_id(...),)]`) | R | iterable-of-row-tuples-of-DB-values ↔ `PSeq[PSeq[int]]` (mapping.md §2). The branch selection is UNCHANGED, backend-feature-gated, and only produces these raw rows; modeled as an input. |
| A2 | parameter `chains: PSeq[PSeq[int]]`, `ncols` | `converters = self.get_converters(cols)` where `cols = [field.get_col(opts.db_table) for field in self.returning_fields]` | R | one converter chain per returning column; `chains[p]` (ids) ↔ the `convs` list at position `p`; an empty chain ↔ a column `get_converters` omits; `ncols` ↔ `len(self.returning_fields)` (mapping.md §1, §2). |
| A3 | result is `execute_returning(rows, chains, ncols)`: per row `j`, per column `p`, `Result()[j][p] == fold_chain(chains[p], rows[j][p])`, computed by the verified outer/inner loops | `rows = list(self.apply_converters(rows, converters))` (guarded by `if converters:`; a no-op when there are none) | A-reference | the changed operation — *running the returned rows through the converter pipeline* — is modeled DEEPLY: `fold_chain` (the spelled-out per-column left-fold) + `apply_row` + the verified loop in `execute_returning` ARE the conversion. There is no consumed `apply_converters` axiom. The deep model is validated `==` the real `apply_converters` out-of-band by G-AX (axiom_check.py runs the real callee on boundary + 20 000 fuzz, asserts equality). The `if converters:` guard is captured by empty chains acting as the identity (mapping.md §3.2). |
| A4 | `step(converter_id, value)` inside `fold_chain` | one converter application `converter(value, expression, connection)` inside `apply_converters` | A-consumed | `step` is the weakest contract (`Ensures(True)`) on one value converter (an unchanged callee, `field.from_db_value` for the F2P field). The proof consumes it only as an opaque value→value map; G-AX confirms representative real converters meet it (mapping.md §3.1). |
| A5 | `return out` (the converted `PSeq[PSeq[int]]`) | `return rows` (the converted list of rows) | I | identical: return the converted rows. Row count and width preserved (the `len(Result())==len(rows)` / per-row-width clauses). |

The discriminating content of the change — that the returned rows are passed
through the converters rather than returned raw — lives in step A3's
postcondition `Result()[j][p] == fold_chain(chains[p], rows[j][p])`. The
pre-patch returned the raw rows (`return rows`); `model_prepatch.py` reproduces
that (the impl re-emits each raw row unchanged) and **fails** that postcondition
on any non-empty converter chain, because `fold_chain` over a non-empty chain
invokes the opaque `step` (not provably equal to the raw value). This is exactly
the spec sensing the change (G-DIFF). The F2P `test_auto_field_subclass_create`
asserts the created object's id is a `MyWrapper`, i.e. `from_db_value` (one
non-empty chain) WAS applied — precisely the converted-vs-raw distinction.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
applying the converter pipeline to the insert-returning rows — is modeled
**deeply** (the spelled-out per-column left-fold `fold_chain` consumed in
`apply_row`/`execute_returning`, step A3, an **A-reference**), not hidden behind
an axiom about the function under change: there is no consumed `apply_converters`
axiom. The only consumed axiom, `step` (**A-consumed**, A4), covers an
**unchanged** callee — a single value converter the new code invokes — and is
the weakest possible (`Ensures(True)`); the `apply_converters` callee appears
only as the **A-reference** that G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`execute_returning` verifies only if its output equals, per row and column, the
left-fold of that column's converter chain over the raw value (A3) — i.e. the
returned rows have been run through the converter pipeline, identity where a
column has no converter. By R (rows ↔ `PSeq[PSeq[int]]`, converter lists ↔
chains, `ncols` ↔ `len(returning_fields)`) and A (the `step` value-converter
axiom, A-consumed; the `apply_converters` deep model, A-reference validated by
G-AX) the verified function equals
`list(self.apply_converters(rows, self.get_converters(cols)))` on the tested
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX, here trivial for `step` + the `apply_converters` equality
check) and refinement fidelity (this document, G-EQ).
