# refinement.md — django__django-12708

The operation-by-operation correspondence between `model.py`'s implementation
(the `selected_for_removal` impl region, the deep `selects` / `count_selected`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed site — `alter_index_together` deletion kwargs

Gold hunk (`django/db/backends/base/schema.py:394-396`):
```
  for fields in olds.difference(news):
-     self._delete_composed_index(model, fields, {'index': True}, self.sql_delete_index)
+     self._delete_composed_index(
+         model,
+         fields,
+         {'index': True, 'unique': False},
+         self.sql_delete_index,
+     )
```

The changed operation is the `constraint_kwargs` dict the index-deletion passes;
that dict is consumed verbatim by `_constraint_names` as its `index` / `unique`
keyword filters (`schema.py:1156,1160`). The post-patch filter keeps a candidate
iff `infodict['index'] == True and infodict['unique'] == False`; the pre-patch
filter keeps a candidate iff `infodict['index'] == True` (no `unique` conjunct).
`_delete_composed_index` then raises iff the kept-count is not 1.

| # | model.py impl op (`selected_for_removal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `constraints: List[int]` (attribute codes) | the candidate constraints on the columns that `_constraint_names` iterates (`schema.py:1154`), after the column-match + exclude that both patches share | R | each introspection `infodict` ↔ a 2-bit code; `code & 1` = `infodict['index']`, `code & 2` = `infodict['unique']` (mapping.md §2). The column/exclude pre-filter is identical in both patches and abstracted away. |
| A2 | `if is_index(code) and not is_unique(code): selected += 1` | the kept-test under `index=True, unique=False` (`schema.py:1156+1160`) driven by the post-patch `{'index': True, 'unique': False}` kwargs | A-reference | the changed selection is modeled **deeply** (`selects` + the verified counting loop ARE the filter). There is no consumed filter axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `_constraint_names` and asserts `selects`/`count_selected` == its result under exactly these kwargs (mapping.md §3.1). |
| A3 | `Result()` = `selected` (the count) | `len(constraint_names)`, which `_delete_composed_index` compares to 1 (`schema.py:410`) | R | the model returns the count of selected constraints; the real code raises `ValueError` iff that count != 1. Excluding the co-located unique constraint is exactly what makes the count 1 (no error) in the tested scenario. |

The discriminating content of the change — excluding a co-located UNIQUE
constraint from an index removal — lives in the `not is_unique(code)` conjunct
of `selects` (model) ⇔ the added `'unique': False` filter (real). The pre-patch
omitted it; `model_prepatch.py` reproduces that (`if is_index(code):`, the
over-broad `keeps_any_index` selection) and **fails** the postcondition
`Result() == count_selected(ToSeq(constraints))`, which is exactly the spec
sensing the change (G-DIFF) — they diverge precisely on a candidate set that
contains a unique-and-index code (code 3) alongside a plain index (code 1),
i.e. the exact `unique_together` + `index_together`-on-same-columns scenario the
F2P test sets up.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely *changed*
— the per-constraint selection filter — is modeled **deeply** (the spelled-out
`selects` predicate and the verified `count_selected` fold), not hidden behind
an axiom about the function under change. There is **no consumed `@ContractOnly`
axiom** in this bundle: the `axioms` region is empty by design (the only callee,
`_constraint_names`, is the carrier of the change, so it is an **A-reference**
G-AX validates the deep model against, never an A-consumed contract). Tagging:
A2 is **A-reference**; A1 and A3 are **R**; there are no **A-consumed** or **I**
or kind-3 steps.

## C. verify(model) ⇒ resolved

`selected_for_removal` verifies only if its returned count equals
`count_selected` — the count of candidates that are an index AND not unique
(A2), with the co-located unique constraint excluded. By R (introspection
`infodict` ↔ attribute code; `len(constraint_names)` ↔ the count; the shared
column/exclude pre-filter) the verified count equals the post-patch
`len(self._constraint_names(... index=True, unique=False))` on the candidates;
by G-AX the deep model `selects`/`count_selected` equals the real
`_constraint_names` filter under exactly those kwargs (A-reference). Therefore a
model satisfying this spec, refined by the map above, makes
`_delete_composed_index` select exactly the non-unique index (count 1, no
`ValueError`) in the presence of a co-located unique constraint — which is the
gold patch up to type refinement and the audited A-reference, and the gold patch
resolves (G-RESOLVE). The trust point is exactly the one of PLAN §1.1 that
applies here: refinement fidelity (this document, G-EQ) plus the A-reference
soundness check (G-AX); there is no consumed axiom to trust.
