# mapping.md — django__django-14122

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bc04941bf811d1ea2c79fb7fc20457ed2c7e3410`, states the type
abstraction, and gives the provenance of the deep model (there are no consumed
axioms).

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_grouping_key(select_cols, order_cols, order_is_backref, trailing_cols, ordering_was_requested)` | `SQLCompiler.get_group_by(self, select, order_by)` — `django/db/models/sql/compiler.py:63` (changed hunk: body lines 120-135) | the modeled changed function (assembles the GROUP BY expression list) |
| `order_contrib(cols, refs)` *(deep model — A-reference)* | the `for expr, (sql, params, is_ref) in order_by:` loop body — `compiler.py:128-132` | pure spec: the grouping-column tokens the ordering source contributes (non-back-reference entries only); validated == the patched repo logic by axiom_check.py (G-AX), NOT a consumed axiom |
| `select_cols` | the `for expr, _, _ in select:` loop's contribution — `compiler.py:120-127` (each `expr.get_group_by_cols()`) | tokens contributed unconditionally by the SELECT source |
| `order_cols` / `order_is_backref` | the `order_by` list — each entry `(expr, (sql, params, is_ref))`; `order_cols[k]` ≙ `expr.get_group_by_cols()` token, `order_is_backref[k] != 0` ≙ the entry's `is_ref` truthy | the result-ordering source and its per-entry back-reference flag |
| `trailing_cols` | `having_group_by` appended at `compiler.py:133-135` | tokens contributed unconditionally after the ordering source |
| `ordering_was_requested` (bool) | `not bool(self._meta_ordering)` — `self._meta_ordering` set/`None` at `compiler.py:41` (init) and `:288` (set in `get_order_by`) | True iff the ordering was explicitly requested (extra/order_by/default-off) rather than taken from the model's default `Meta.ordering` |

The patched guard the bundle senses is the inserted `if not self._meta_ordering:`
wrapping the ordering loop (`compiler.py:128-132` post-patch). Pre-patch the
loop runs unconditionally.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a GROUP BY expression / column object (the elements of `expressions`) | `int` token identifier | each distinct grouping column ≙ a distinct `int`; the modeled operation is purely *which columns, in what order* enter the list — never the columns' internal structure |
| `expr.get_group_by_cols()` (a list of columns per `order_by` entry) | one token per entry (`order_cols[k]`) | the F2P-relevant ordering entries (`Meta.ordering` fields, e.g. `-pub_date`) each yield a single grouping column; the abstraction models one token per entry. The *change* is whether the loop runs at all, not the per-entry cardinality, so a one-token-per-entry carrier is faithful for the tested behaviour (axiom_check.py fuzzes the per-entry skip and the guard). |
| the `is_ref` boolean of an `order_by` entry | `order_is_backref[k]: int` (0 = not a ref → keep; non-0 = ref → skip) | mirrors `if not is_ref:` at `compiler.py:131`; an `int` carrier is used (Nagini `PSeq[bool]` folds are heavier and add nothing — 0/non-0 is the same two-valued test) |
| `self._meta_ordering` (None or a non-empty ordering list) | `ordering_was_requested: bool` | `_meta_ordering` is truthy **iff** the ordering came from `Meta.ordering` (`get_order_by`, `compiler.py:286-288`); the patched test `not self._meta_ordering` ≙ `ordering_was_requested`. The remaining `expressions` post-processing (`collapse_group_by`, dedup, `self.compile`) is identity on *which* tokens are present for the tested cases and is outside the changed hunk; omitted. |
| `expressions` list | `result: List[int]`; specification over `PSeq[int]` via `ToSeq` | list `append`/`extend` ↔ list `append`; order preserved |

`select`/`order_by`/`having` carriers are read-only and held at
`Acc(list_pred(·), 1/2)` (Required AND Ensured): `get_group_by` does not mutate
its inputs, it only reads them to build a fresh `expressions` list.

## 3. Deep model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `order_contrib` + `assemble_grouping_key` ↔ patched `get_group_by` (A-reference)
There is **no `@ContractOnly` axiom** in this bundle. The changed operation —
conditionally folding the ordering source into the grouping key — is modeled
**deeply** by `order_contrib` (the non-back-reference token fold) consumed in
`assemble_grouping_key` under the `ordering_was_requested` guard. The deep model is
validated equal to the real patched algorithm out-of-band by axiom_check.py
(G-AX), which transcribes the patched `get_group_by` at the token level:

```python
# compiler.py post-patch (lines 120-135), token-level:
expressions = []
for expr, _, _ in select:                 # -> append select tokens
    expressions.extend(expr.get_group_by_cols())
if not self._meta_ordering:               # the PATCHED guard
    for expr, (sql, params, is_ref) in order_by:
        if not is_ref:                     # skip back-references
            expressions.extend(expr.get_group_by_cols())
for expr in having_group_by:              # -> append trailing tokens
    expressions.append(expr)
```

The pre-patch source is identical except the `if not self._meta_ordering:`
guard is absent — the ordering loop runs unconditionally. axiom_check.py checks:
the deep model == the patched algorithm on 14 boundary + 50 000 fuzz inputs
(varying every list, the per-entry `is_ref` skip, and the flag), and confirms
the F2P-shaped default-ordering witness (`values('author').annotate(Count)` with
`Article.Meta.ordering = ['-pub_date']`, so `_meta_ordering` truthy ⇒
`ordering_was_requested = False`) drops the ordering token under the patch but
keeps it pre-patch — the exact aggregation-splitting bug the issue reports.

### 3.2 `_meta_ordering` semantics (provenance for the flag)
`get_order_by` (`compiler.py:271-290`) sets `self._meta_ordering = ordering`
ONLY in the `elif self.query.get_meta().ordering:` branch (`:286-288`), i.e.
when no extra-order-by, no explicit `order_by`, and `default_ordering` is on, so
the ordering is the model's `Meta.ordering`. In every other branch it stays
`None` (init at `:41`). Hence `bool(_meta_ordering)` is exactly "the ordering is
a default, not an explicit request", and the patched `not self._meta_ordering`
is `ordering_was_requested`. Docs / ticket: Django ticket #14357 and PR #14122
(linked from the problem statement).
