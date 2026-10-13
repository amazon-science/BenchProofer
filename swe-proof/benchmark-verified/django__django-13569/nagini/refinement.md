# refinement.md — django__django-13569

The operation-by-operation correspondence between `model.py`'s implementation
(the `random_group_by_cols` impl region, the `group_by_columns_for_ordering`
impl region, and the deep `offered_cols` / `gathered` models) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — split into **A-consumed**, where the proof uses an axiom's
`Ensures`, and **A-reference**, where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This bundle consumes **NO `@ContractOnly` axiom** (the `axioms` region holds only
a note). The two changed/observed operations are modelled **deeply**, so the real
callees they correspond to are **A-references**, validated by axiom_check.py
(G-AX), not consumed by the proof.

## A. The changed function — `Random.get_group_by_cols` (`django/db/models/functions/math.py`)

Gold hunk (added after `as_sqlite`, math.py:157):
```
+    def get_group_by_cols(self, alias=None):
+        return []
```

Pre-patch there is no such method: `Random` (a non-aggregate `Func` with
`arity = 0`) inherits `BaseExpression.get_group_by_cols`
(`django/db/models/expressions.py:349-355`), whose `not self.contains_aggregate`
branch returns `[self]` — so a `RANDOM()` expression is offered as a grouping
column and leaks into `GROUP BY ..., RANDOM()`.

`model.py` symbol: `random_group_by_cols(colid)`.

| # | model.py impl op (`random_group_by_cols`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `colid: int` | the receiver `self` (a `Random` instance) of `get_group_by_cols` | R | a `Random` ordering-term expression ↔ its column identity `colid` (mapping.md §2); the modelled distinction is "this term, were it deterministic, would offer column `colid`". |
| A2 | `result = []  # List[int]` ; `return result` | `return []` | R + I | the empty list of contributed grouping-column expressions ↔ the empty `List[int]` of column identities (mapping.md §2). Concretely identical (`[]`). |
| A3 | the result satisfies `len(Result()) == 0` and `ToSeq(Result()) == offered_cols(1, colid)` | the post-patch `Random.get_group_by_cols()` returns `[]` | A-reference | the changed operation is modelled **deeply**: `random_group_by_cols` returns the empty list and `offered_cols(is_nondet != 0, _)` returns the empty `PSeq`. No `@ContractOnly` axiom is consumed. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) asserts `Random().get_group_by_cols() == []` and, transitively, `OrderBy(Random()).get_group_by_cols() == []`. The model and the real callee compute the same function (empty). |

The discriminating content of the change — a non-deterministic ordering term
offers **no** grouping column rather than itself — lives in the postcondition
`len(Result()) == 0` (equivalently `ToSeq(Result()) == offered_cols(1, colid)`,
the empty sequence). The pre-patch inherited default offered `[self]`;
`model_prepatch.py` reproduces that (`result = [colid]`) and **fails** the
postcondition `len(Result()) == 0`, which is exactly the spec sensing the change
(G-DIFF). This is the single independently-fixed behaviour, so there is exactly
one `model_prepatch.py`.

## B. The observing caller — the order-by → group-by gathering loop (`compiler.py`)

The F2P test (`test_aggregation_random_ordering`) observes the change through
`SQLCompiler.get_group_by` (`django/db/models/sql/compiler.py:63`). The relevant
slice is the order-by gathering loop (compiler.py:128-131), which is **unchanged**
by the patch but is what turns "a `RANDOM()` term offers no column" into "the
GROUP BY is unbroken":
```python
for expr, (sql, params, is_ref) in order_by:
    if not is_ref:
        expressions.extend(expr.get_group_by_cols())
```
`model.py` symbol: `group_by_columns_for_ordering(nondet, ref, cols)`, gathering
the per-term contributions of a list of ordering terms.

| # | model.py impl op (`group_by_columns_for_ordering`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | a list of ordering terms ↔ three index-aligned `List[int]` `nondet`/`ref`/`cols`; `Acc(list_pred(·), 1/2)` Required and Ensured on all three | the `order_by` list of 2-tuples `(expr, (sql, params, is_ref))`, read-only in the loop | R + (directive 5) | each tuple ↔ index `k`: `nondet[k] != 0` ⇔ the term's source is non-deterministic (`Random`); `ref[k] != 0` ⇔ `is_ref`; `cols[k]` ⇔ the column identity the term would offer if deterministic (mapping.md §2). The loop mutates none of `order_by`, so all three carriers are fractional read-only (directive 5). |
| B2 | `if ref[i-1] != 0: result = result` (skip) | `if not is_ref: ...` — a reference term contributes nothing | I | the `is_ref` skip is the identical control-flow predicate (mapping.md §2). |
| B3 | `elif nondet[i-1] != 0: contributed = random_group_by_cols(cols[i-1]); result = contributed + result` | `expressions.extend(expr.get_group_by_cols())` where `expr`'s source is a `Random` | A-reference + I | the `extend(get_group_by_cols())` is the identical gather; the per-term contribution of a non-deterministic term is the A-reference of §A (it is `[]`). |
| B4 | `else: result = [cols[i-1]] + result` | `expressions.extend(expr.get_group_by_cols())` where `expr`'s source is a deterministic leaf | A-reference + I | the identical `extend(get_group_by_cols())`; a deterministic leaf's `get_group_by_cols()` is the unchanged default `[self]` (`expressions.py:349`, or `RawSQL.get_group_by_cols` returning `[self]`, expressions.py:792) — one column. `offered_cols(0, c) == PSeq(c)` models exactly that. |
| B5 | postcondition `ToSeq(Result()) == gathered(ToSeq(nondet), ToSeq(ref), ToSeq(cols))` | the accumulated `expressions` after the loop | A-reference | `gathered` is the deep front-fold over the term list: skipping references, concatenating each term's `offered_cols`. Because a non-deterministic term offers nothing (§A), no `RANDOM()` column is ever gathered — so the GROUP BY equals what it would be without the random ordering. G-AX validates `gathered` == the real gathering loop over 3000 randomized term lists + boundary cases. |

`offered_cols` and `gathered` are deep models (an **A-reference**), not consumed
axioms: there is no `@ContractOnly` for `get_group_by_cols`. They are validated
== the real `Random.get_group_by_cols` / `OrderBy.get_group_by_cols` /
`RawSQL.get_group_by_cols` and the gathering loop by axiom_check.py (G-AX,
mapping.md §3).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — a non-deterministic ordering term's grouping-column contribution
going from `[self]` to `[]` — is modelled **deeply** (`random_group_by_cols`
returns `[]`; `offered_cols(is_nondet != 0, _)` returns the empty sequence; the
verified loop in `group_by_columns_for_ordering` gathers it), not hidden behind
an axiom about the function under change. There is no consumed axiom at all; the
real `get_group_by_cols` family appears only as the **A-references** that G-AX
validates the deep model against.

## D. verify(model) ⇒ resolved

`random_group_by_cols` verifies only if its output is empty (`len(Result()) == 0`,
step A3); `group_by_columns_for_ordering` verifies only if its gathered output
equals `gathered(...)` (step B5), which — because the non-deterministic term
offers nothing — never contains a `RANDOM()` column. By R (the `order_by`-tuple ↔
three-`List[int]` carrier, the contributed-expression-list ↔ `List[int]` of
column identities, the `is_ref` skip, the `extend(get_group_by_cols())` gather)
the verified model equals the gold-patched Django on the tested query: a
`Count` annotation ordered by `'?'` is grouped exactly as without the ordering.
By G-AX the deep model (`offered_cols` / `gathered` / `random_group_by_cols`)
equals the real callees (A-references). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
references — and the gold patch resolves (G-RESOLVE: F2P
`test_aggregation_random_ordering` passes, the 67 P2P aggregation tests still
pass). The trust points are exactly the two of PLAN §1.1: A-reference soundness
(G-AX) and refinement fidelity (this document, G-EQ).
