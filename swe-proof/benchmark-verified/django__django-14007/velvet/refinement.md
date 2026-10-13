# refinement.md — django__django-14007

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `transformedResultRows` `do` block and the deep `convertRows`/`convertRow`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `SQLInsertCompiler.execute_sql` (`compiler.py:1402`)

Gold hunk (abridged): each `return <assembled rows>` becomes an assignment to a
local `rows`; after the cursor block the patch adds

```python
cols = [field.get_col(opts.db_table) for field in self.returning_fields]
converters = self.get_converters(cols)
if converters:
    rows = list(self.apply_converters(rows, converters))
return rows
```

So the rows the INSERT produced are now routed through the field converters
(`from_db_value`) before being returned, instead of returned raw.

| # | Solution.lean impl op (`transformedResultRows`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rows : List (List Int)` | the assembled `rows` local (from `fetch_returned_insert_rows` / `fetch_returned_insert_columns` / `last_insert_id`) | R | `list[tuple]` ↔ `List (List Int)` (mapping.md §2). The branch that ASSEMBLES `rows` is structurally unchanged by the patch (an effectful **I** preamble we do not re-model); the patch only changes what happens to `rows` afterward. |
| A2 | parameter `convs : List (Int → Int)` | `converters = self.get_converters(cols)`, `cols = [field.get_col(opts.db_table) for field in self.returning_fields]` | R | the per-column converter chains, presented as column→callable (mapping.md §2/§3). An empty `convs` ↔ `get_converters` returning `{}` (`if converters:` false). |
| A3 | result is `convertRows convs rows`: per-row, per-column application of `convs`, computed by the backward `while` fold | `rows = list(self.apply_converters(rows, converters))` (under `if converters:`); `return rows` | A-reference + I | the conversion is modeled **deeply**: `convertRow`/`convertRows` (pure region) and the verified loop ARE the per-position transform. No consumed `applyConverters` axiom. The fold ops (`convertRow convs row`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `apply_converters` is the **A-reference** G-AX validates. mapping.md §3.1. |

Note on the `if converters:` guard: when no returning field defines a converter,
`get_converters` returns `{}`, the guard is false, and `rows` is returned
unchanged. `convertRows convs rows` with `convs = []` reduces (by `convertRow`'s
short-list clause) to `rows` itself, so the deep model already covers the
no-converter case — one expression, no `else if` ladder.

Discriminating content of the change — the returned values are the converters'
output, not the raw fetched integers — lives in `out = convertRows convs rows`
(model) ⇔ `apply_converters(rows, converters)` (real). The pre-patch
`execute_sql` returned the raw `rows`; `Solution_prepatch.lean` reproduces that
(it prepends each `row` verbatim, never applying `convertRow`) and **fails**
`out = convertRows convs rows` on the discriminating clause (G-DIFF).

## B. No consumed axioms

There are no A-consumed rows. The only callee modeled is `apply_converters`, and
it is modeled **deeply** (the spelled-out `convertRows`/`convertRow` fold,
step A3, an A-reference + I), validated == the real callee by G-AX — not hidden
behind an opaque oracle the proof echoes (directive 8). No dead `axiom` ships.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
applying the field converters to the returned rows — is modeled **deeply**
(`convertRows`), not via an axiom about the function under change. The function
under spec (`execute_sql`'s return value) is exactly what we verify; the only
A-tagged symbol (`apply_converters`) is an UNCHANGED callee the patch newly
invokes.

## D. verify(Solution) ⇒ resolved

`transformedResultRows` verifies only if its output equals the exact per-row,
per-column transform of the assembled rows (A3). By R (`list[tuple] ↔ List (List
Int)`, converter-map ↔ `List (Int → Int)`) the verified result equals
`apply_converters(rows, get_converters(cols))` on the tested inputs; by G-AX the
deep model `convertRows` equals the real `apply_converters` (A-reference); by
G-CONF the R/I transliteration of the fold agrees with `patch.diff`'s conversion
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited callee — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: callee-model soundness (G-AX) and refinement fidelity (this doc,
G-EQ + G-CONF).
