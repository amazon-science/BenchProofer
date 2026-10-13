# refinement.md — django__django-11087

Maps every operation in `implementation_collectFieldSelection` to its
`patch.diff` counterpart in `Collector.collect`
(`django/db/models/deletion.py`, the `collect_related` field-selection arm).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch field-selection arm)
```python
else:
    related_model = related.related_model
    # ... (the restriction is skipped when select_related or signals present) ...
    if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):
        referenced_fields = set(chain.from_iterable(
            (rf.attname for rf in rel.field.foreign_related_fields)
            for rel in get_candidate_relations_to_delete(related_model._meta)
        ))
        sub_objs = sub_objs.only(*tuple(referenced_fields))
    if sub_objs:
        field.remote_field.on_delete(self, field, sub_objs, self.using)
```
The modeled value is the COLUMN SELECTION that `sub_objs` carries into the
`on_delete` handler: what the restricted queryset actually loads on the restricted
branch, and what the untouched `sub_objs` loads on the other one. Both are read
off the real query, not assumed — see mapping.md §4 for the four ways
`.only(*referenced)` differs from "loads exactly `referenced`", and mapping.md §3
for the measured carrier states.

## Operation correspondence
| # | Lean op (`implementation_collectFieldSelection`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut loaded := defaultColumns` | on the else-of-the-guard, `sub_objs` is handed on UNTOUCHED to `field.remote_field.on_delete(...)`, so it loads its own default column set | R | the accumulator starts at what the incoming fetch loads if nothing is done to it. That is the whole row only when the incoming queryset carries no deferral state; a related model whose `_base_manager` defers a column arrives with fewer (mapping.md §3 rows 4, 5). Modelling this leg as `allFields` was the pre-repair defect on the pass-through branch. |
| 2 | `if !(guardA \|\| guardB) then` | `if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):` | R | `sub_objs.query.select_related` truthiness ↔ `guardA : Bool`; `self._has_signal_listeners(related_model)` ↔ `guardB : Bool`; Python `not (a or b)` ↔ Lean `!(a \|\| b)`. Type bijection in mapping.md §2. The spec view leaves both flags uninterpreted (mapping.md §7). |
| 3 | `referencedColumns candidateRelations` (inside `loadedColumns`) | `referenced_fields = set(chain.from_iterable((rf.attname for rf in rel.field.foreign_related_fields) for rel in get_candidate_relations_to_delete(related_model._meta)))` | R/I | `chain.from_iterable` ↔ `List.flatten`; `set(...)` (membership-dedup) ↔ `List.dedup`. The per-relation target-attname lists enter as the `candidateRelations` data (mapping.md); the gather is modeled deeply, not axiomatized. G-CONF compares as sets so the list↔set refinement is exact. |
| 4 | `restrictionNames skippedNames candidateRelations` (inside `loadedColumns`) | the field-name set `.only(...)` ends up requesting: `field_names.difference(existing)` in `Query.add_immediate_loading` (`sql/query.py:1971-1976`) when the incoming queryset is in the defer state | R | `set.difference` ↔ `List.filter (fun c => !skippedNames.contains c)`. A raw string difference over the names as stored, so `defer('origin')` does not cancel a referenced `origin_id` while `defer('origin_id')` does — both measured (mapping.md §3 rows 7, 8; §4). The difference is taken on the REQUEST, not merely consulted for an emptiness test: with two referenced columns and one of them already deferred the request shrinks to the other and the real load is `{other, pk}` (mapping.md §3 row 11, measured `{b,id}`). This step is what the pre-repair model omitted on the restricted branch. |
| 5 | `loaded := loadedColumns pkColumn allFields skippedNames candidateRelations` | `sub_objs = sub_objs.only(*tuple(referenced_fields))` | R | the loaded column set AFTER the restriction. `.only(*cols)` is not the identity on `cols`: with the REQUEST non-empty the SELECT loads `request ∪ {pk}` (`deferred_to_data` seeds `must_include` with `orig_opts.pk`, `sql/query.py:660`) and with the request EMPTY it is a no-op loading the whole row, including columns that had been deferred (`deferred_to_data` returns early on an empty field-name set, `sql/query.py:656`). `loadedColumns` composes those two with row 4, so the postcondition asserts what the real callee guarantees rather than "loads exactly `referenced`". Measured against the real callee (mapping.md §3: 13 carrier states — including the partial-overlap state row 11, the already-skipped identifying column row 12 where the real fetch loads the pk anyway, and the skip-covers-referenced state row 13 — plus a 33,856-input exhaustive sweep, 0 disagreements) and re-checked mechanically by G-CONF, whose oracle drives the real `.only()` on real incoming querysets and, in its first leg, real `.delete()` cascades. |
| 6 | `return loaded` | the column set `sub_objs` carries into `field.remote_field.on_delete(...)` | I | return the chosen column set. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — `get_candidate_relations_to_delete` / `foreign_related_fields`
enter as data per mapping.md). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs
(124,255 comparisons in four legs: real cascade deletes, the patched arm over
every prior deferral state of a model zoo, the real `.only()` over random
requests × prior states, and the pure list↔set plumbing).
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the arm is simply `elif sub_objs: field.remote_field.on_delete(...)`
— the related-objects queryset is handed on exactly as fetched, so it loads its
own default columns, always. The prepatch impl
(`implementation_collectFieldSelection := return defaultColumns`,
unconditionally) is exactly this: it never restricts to the referenced columns.
It therefore cannot satisfy `problem_spec_collectFieldSelection` on the
discriminating clause
(`guardA = false ∧ guardB = false → result = loadedColumns …`)
whenever `loadedColumns pkColumn allFields skippedNames candidateRelations ≠
defaultColumns` — precisely the case the FAIL_TO_PASS test
`test_only_referenced_fields_selected` exercises (a `Referrer` row whose
`large_field` column must NOT be selected during cascade deletion of its
`Origin`, while `id`/`unique_field` — the referenced columns — must be).

The carried prepatch proof fails to typecheck against the buggy impl (G-DIFF),
and the failure is attributable to the spec rather than to a tactic mismatch: the
only error is the restricted-branch goal
`defaultColumns = loadedColumns pkColumn allFields skippedNames candidateRelations`,
which `rfl` reports as not definitionally equal, and two independent
`example : ¬ problem_spec_collectFieldSelection … (implementation_… …)`
refutations — one at the F2P-shaped input, one at the measured carrier state of
mapping.md §3 row 1 — elaborate against the prepatch impl by `decide`, i.e. the
spec is provably violated there rather than merely unproven.
