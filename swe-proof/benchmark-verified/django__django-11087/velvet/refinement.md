# refinement.md — django__django-11087

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`columnsToFetch` `do` block and the deep `hasExposingSubscriber` / `mayNarrow` /
`columnsFetched` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — A-consumed / A-reference),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1, run in-container with the gold patch applied); the narrative is audited by
**G-EQ**. There are **no A-tagged ops** (no axioms, no deep-model references):
the changed behaviour calls only the added helper `_has_signal_listeners` and
the unchanged `QuerySet.only` / `select_related` observation, all modeled
deeply as closed boolean/list functions of the inputs.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The narrowing site — `Collector.collect` (`django/db/models/deletion.py`, the `else:` block at `:223` post-patch)

Gold hunk (the behavioural core):
```
-                    elif sub_objs:
-                        field.remote_field.on_delete(self, field, sub_objs, self.using)
+                    else:
+                        related_model = related.related_model
+                        if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):
+                            referenced_fields = set(chain.from_iterable(
+                                (rf.attname for rf in rel.field.foreign_related_fields)
+                                for rel in get_candidate_relations_to_delete(related_model._meta)
+                            ))
+                            sub_objs = sub_objs.only(*tuple(referenced_fields))
+                        if sub_objs:
+                            field.remote_field.on_delete(self, field, sub_objs, self.using)
```

| # | Solution.lean impl op (`columnsToFetch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `allColumns`, `referencedColumns : List Nat` | the dependent fetch's full column set vs. the `referenced_fields` set | R | column-set ↔ `List Nat` id list (mapping.md §2). G-CONF bridges to the real model's `attname` sets for `Referrer`. |
| A2 | param `widenedFetch : Bool` | `bool(sub_objs.query.select_related)` | R | truthy `select_related` ↔ `true` (mapping.md §2). |
| A3 | params `preDelete`, `postDelete : Bool` | `signals.pre_delete.has_listeners(related_model)`, `signals.post_delete.has_listeners(related_model)` (via `_has_signal_listeners`) | R | listener presence ↔ `Bool` (mapping.md §2, §3.1). G-CONF connects/disconnects real receivers. |
| A4 | `narrow := !(widenedFetch || (preDelete || postDelete))` (= `mayNarrow ...`) | `not (sub_objs.query.select_related or self._has_signal_listeners(related_model))` | I (deep model of the added guard) | the guard is spelled out: `_has_signal_listeners = pre_delete or post_delete` (A3) and the `not (... or ...)`. NOT a consumed axiom — G-CONF validates against the real helper. mapping.md §3.1–3.2. |
| A5 | `if narrow then return referencedColumns else return allColumns` (= `columnsFetched ...`) | `sub_objs = sub_objs.only(*referenced_fields)` when the guard holds, else `sub_objs` unchanged (full fetch) | I (deep model of the changed fetch) | the column choice: `.only(referenced)` ↔ `referencedColumns`; no `.only` ↔ `allColumns`. mapping.md §3.2. |

The post-condition pins this exactly: `out = columnsFetched ...` AND
`hasExposingSubscriber preDelete postDelete = (preDelete || postDelete)`. No
implementation that fetches the full set when narrowing is permitted (the
optimisation the F2P test demands), or that narrows when a subscriber is present
or the fetch was widened (which the F2P test forbids — full set required then),
can satisfy it.

## B. The refactored listener test — `can_fast_delete` / `_has_signal_listeners`

Gold hunks: a new `_has_signal_listeners(self, model)` helper is added
(`deletion.py:120` post-patch), and `can_fast_delete`'s inline
`pre_delete or post_delete or m2m_changed` test (`:138-140`) is replaced by a
call to it.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `hasExposingSubscriber preDelete postDelete = preDelete || postDelete` | the added `_has_signal_listeners` body | I (deep model of the added helper) | the helper is `pre_delete or post_delete`; modeled deeply, not axiomatized. The `m2m_changed` term that `can_fast_delete` USED to include is intentionally NOT part of the narrowing-relevant predicate (mapping.md §3.1): an m2m-changed subscriber never receives the dependent rows, so it imposes no column requirement. G-CONF confirms only pre/post gate the choice. |

The `can_fast_delete` refactor (replacing the inline 3-way test with the new
2-way helper) is behaviour-preserving FOR `can_fast_delete` (it drops
`m2m_changed` from `can_fast_delete`'s fast-path veto — a separately-observable
behavioural relaxation, but one the F2P test `test_only_referenced_fields_selected`
does not exercise; the F2P only observes the narrowing site's column list). It
is therefore not modeled as a separate failing prepatch: a prepatch must keep
the frozen spec byte-identical (G-DIFF), and the spec here pins the narrowing
decision, whose pre-image (site A, full-fetch-always) is the discriminating
defect the issue reports ("fetching a field not needed for the delete").

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operations that genuinely *changed* — adding the
referenced-only narrowing under a guard, and the `_has_signal_listeners`
helper — are modeled **deeply** (`mayNarrow`/`columnsFetched`/
`hasExposingSubscriber`), not behind an axiom about the function under change.
There is **no axiomatized callee** (G-AX skipped; `meta.json axioms = []`,
`deep_model_references = []`): `select_related` and `.only` are observed as the
boolean `widenedFetch` and the column-set choice respectively (R), and
`_has_signal_listeners` is the added helper (B1), not a pre-existing callee with
a contract to consume.

## D. verify(Solution) ⇒ resolved

`columnsToFetch` verifies only if its output is `columnsFetched ...` (A5): the
referenced-only set exactly when `mayNarrow` holds (no widening, no exposing
subscriber), the full set otherwise. By R (`select_related`/`has_listeners` ↔
the boolean inputs; column sets ↔ `List Nat`; `.only(referenced)` ↔
`referencedColumns`) the verified method equals the patched
`Collector.collect`'s column choice on every configuration. By G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs against the
REAL patched `_has_signal_listeners` + `signals` registry and the real
`Referrer` field sets (and disagrees against the pre-patch always-full-fetch,
confirming discrimination). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc +
G-CONF); there is no axiom-soundness trust point (no axioms).
