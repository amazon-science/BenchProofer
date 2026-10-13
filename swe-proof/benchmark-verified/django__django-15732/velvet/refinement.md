# refinement.md — django__django-15732

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `chooseTarget` `do` block, plus the pure `narrowed`/`selectedTarget`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs + narrative are audited by **G-EQ**. This bundle has **no A legs**
(no consumed axiom, no A-reference) — every helper result is taken as an opaque
method input — so the whole impl region is R/I and G-AX is vacuous.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The selection site — `_delete_composed_index` (`schema.py:559`)

Gold hunk (the inserted narrowing block, `schema.py:574-582` post-patch):
```python
if (
    constraint_kwargs.get("unique") is True
    and constraint_names
    and self.connection.features.allows_multiple_constraints_on_same_fields
):
    default_name = str(
        self._unique_constraint_name(model._meta.db_table, columns, quote=False)
    )
    if default_name in constraint_names:
        constraint_names = [default_name]
if len(constraint_names) != 1:
    raise ValueError(...)
self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))
```

| # | Solution.lean impl op (`chooseTarget`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `names : List String` parameter | `constraint_names` (result of `_constraint_names`) | R | `list[str]` ↔ `List String` (mapping.md §2); `_constraint_names` is unchanged, its value is the input. |
| A2 | `uniqueSel : Bool` parameter | `constraint_kwargs.get("unique") is True` | R | `bool` ↔ `Bool` (mapping.md §2). |
| A3 | `allowMultiple : Bool` parameter | `self.connection.features.allows_multiple_constraints_on_same_fields` | R | feature-flag `bool` ↔ `Bool`; F2P runs with it `true` (`@skipUnlessDBFeature`, mapping.md §3). |
| A4 | `canonical : String` parameter | `default_name = str(self._unique_constraint_name(table, columns, quote=False))` | R | `str` ↔ `String`; `_unique_constraint_name` is an introduced-but-pure helper, its value is the input (mapping.md §3, §B). |
| A5 | `if uniqueSel ∧ ns ≠ [] ∧ allowMultiple then (if canonical ∈ ns then ns := [canonical])` | the inserted `if (unique is True and constraint_names and allow_multiple): if default_name in constraint_names: constraint_names = [default_name]` | I | identical concrete control flow: the same four-way guard (`unique`, non-empty, multi-allowed, membership) and the same singleton replacement. `ns ≠ []` ↔ truthiness of the non-empty `constraint_names`. |
| A6 | `if ns.length = 1 then ns[0]? else none` | `if len(constraint_names) != 1: raise ValueError; ...constraint_names[0]` | R | `Option String`: `some n` (len==1 ⇒ act on `constraint_names[0]`) ↔ delete that constraint; `none` (len≠1) ↔ the `ValueError` raise. Observationally the operation succeeds on a unique target iff `some`. |

Discriminating content of the change — the **narrowing** step A5 — is what the
pre-patch lacked: pre-patch `constraint_names` flowed straight into the
`len(...) != 1` check, so a column with both a standalone unique constraint and
a unique_together constraint produced two candidates and `selectedTarget`
returned `none` (the `ValueError`). `Solution_prepatch.lean` reproduces that
(no narrowing: `let ns := names`) and **fails** `out = selectedTarget …` on the
case `uniqueSel ∧ names ≠ [] ∧ allowMultiple ∧ canonical ∈ names ∧ names.length ≠ 1`
(G-DIFF) — exactly the `test_remove_unique_together_on_unique_field` scenario.

## B. The `_unique_constraint_name` extraction (`schema.py:1577-1616`)

The gold patch also extracts the inline `IndexName(table, columns, "_uniq",
create_unique_name)` expression from `_create_unique_sql` into a new method
`_unique_constraint_name(table, columns, quote=True)`, and calls it from both
`_create_unique_sql` (`quote=True`, unchanged behaviour) and the new block above
(`quote=False`). This is a **pure refactor**: `_create_unique_sql` computes the
byte-identical `name` before and after (same `IndexName` with the same
`create_unique_name` closure when `quote=True`). It introduces **no observable
behaviour change** on its own; its only behaviour-bearing consumer is site A
(via the `canonical` value, A4). No separate prepatch is needed — a prepatch
must keep the spec byte-identical (G-DIFF), and this refactor changes no spec
clause. Modeled as the opaque `canonical` input (mapping.md §3).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — inserting
the narrowing decision — is modeled **directly** (step A5, an `I` op: the same
nested `if` over the same four conditions). There is **no axiom about the
function under change** and **no deep-model A-reference**: the helper results
(`_constraint_names`, `_unique_constraint_name`, the feature flag) are unchanged
callees whose *values* are method inputs, and the contract assumes nothing about
them. Hence no A-consumed and no A-reference rows; G-AX is vacuous.

## D. verify(Solution) ⇒ resolved

`chooseTarget` verifies only if its `out` equals `selectedTarget` — i.e. it
performs the narrowing A5 then the singleton decision A6. By R (`list[str] ↔
List String`, `bool ↔ Bool`, the `Option`/raise correspondence A6) the verified
selection equals the gold patch's `_delete_composed_index` selection on every
`(constraint_names, unique, allow_multiple, default_name)` tuple; by G-CONF the
R/I transliteration of `selectedTarget` agrees with the gold patch block's
behaviour on ≥10⁵ fuzzed tuples (0 disagreements). There are no axioms to keep
sound (G-AX vacuous). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point for this instance.
