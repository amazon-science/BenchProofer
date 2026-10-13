# refinement.md — django__django-16661

The operation-by-operation correspondence between `model.py`'s implementation
(the `retained_segments` impl region, plus the deep `keep_at` / `retained_mask`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed** / **A-
reference**), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit`, `git apply --check` OK, and is the real correctness oracle,
G-RESOLVE).

## The change site — `ModelAdmin.lookup_allowed` retention condition (`django/contrib/admin/options.py:467-471`)

Gold hunk (the only change):
```
-            # It is allowed to filter on values that would be found from local
-            # model anyways. For example, if you filter on employee__department__id,
-            # then the id value would be found already from employee__department_id.
             if not prev_field or (
                 prev_field.is_relation
-                and field not in prev_field.path_infos[-1].target_fields
+                and field not in model._meta.parents.values()
+                and field is not model._meta.auto_field
+                and (
+                    model._meta.auto_field is None
+                    or part not in getattr(prev_field, "to_fields", [])
+                )
             ):
                 relation_parts.append(part)
```

The patch replaces the single coarse test `field not in
prev_field.path_infos[-1].target_fields` with three precise tests. Everything
else in `lookup_allowed` — the segment loop scaffolding, the `get_field` /
`FieldDoesNotExist` break, the `path_infos` continuation, and the final
`len(relation_parts) <= 1` / `isdisjoint(valid_lookups)` membership test — is
untouched.

### Type / state abstraction (the R-refinements)

| repo reality (loop step for segment k) | model carrier | bijection |
|---|---|---|
| the segment sequence `lookup.split(LOOKUP_SEP)` | the index range `0..n-1` over the parallel fact vectors | one model entry per real segment, in order |
| `bool(prev_field) and prev_field.is_relation` | `prev_is_relation[k]: bool` | see mapping.md §2 |
| `field in model._meta.parents.values()` | `field_is_parent_link[k]: bool` | membership ↔ flag |
| `field is model._meta.auto_field` | `field_is_auto_identity[k]: bool` | object identity ↔ flag |
| `model._meta.auto_field is None` | `not model_has_auto_identity[k]` | "no synthesised identity" ↔ negated flag |
| `part in getattr(prev_field, "to_fields", [])` | `segment_targets_prior_hop[k]: bool` | membership ↔ flag |
| `field in prev_field.path_infos[-1].target_fields` (pre-patch) | `field_is_prior_hop_target[k]: bool` | membership ↔ flag (read-only input; unused by the post-patch impl) |
| `relation_parts.append(part)` taken vs not, across the loop | `Result()` retention mask entry `1` vs `0` | append decision ↔ mask flag |

### Operation correspondence

| # | model.py impl op (`retained_segments`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | iterate segments, prepending one mask flag per segment | `for part in lookup.split(LOOKUP_SEP): … relation_parts.append(part)` loop | R + I | the loop scaffolding is identical control flow; the carrier is the index range over the fact vectors (table above). The mask records, per segment, whether `append` fired. |
| 2 | first-segment branch `if i - 1 == 0: keep = True` | `if not prev_field or (…)` — the `not prev_field` disjunct (true for segment 0, where `prev_field is None`) | I | identical: the first segment is always retained. |
| 3 | non-first branch `keep = keep_at(prev_is_relation, field_is_parent_link, field_is_auto_identity, model_has_auto_identity, segment_targets_prior_hop)` | the `prev_field.is_relation and field not in model._meta.parents.values() and field is not model._meta.auto_field and (model._meta.auto_field is None or part not in getattr(prev_field, "to_fields", []))` conjunction | R + I | the post-patch boolean is transcribed term-for-term: `prev_is_relation` ↔ `prev_field.is_relation`; `not field_is_parent_link` ↔ `field not in model._meta.parents.values()`; `not field_is_auto_identity` ↔ `field is not model._meta.auto_field`; `(not model_has_auto_identity or not segment_targets_prior_hop)` ↔ `(model._meta.auto_field is None or part not in getattr(prev_field, "to_fields", []))`. Identical logical structure, refined to the boolean facts. |
| 4 | the retention mask `Result()` | the resulting `relation_parts` list | R | the mask is the characteristic vector of `relation_parts` over the segment positions: `Result()[k] == 1` iff segment k ∈ `relation_parts`. The unchanged membership test (`LOOKUP_SEP.join(relation_parts) … .isdisjoint(valid_lookups)`, `options.py:493-497`) consumes `relation_parts`; it is I (untouched by the gold) and is a deterministic function of which segments are retained, i.e. of the mask. So pinning the mask pins the lookup result. |

The comment block deleted by the gold (the `# It is allowed to filter …`
narration) carries no behaviour and has no model counterpart.

## Why no axioms (no A-consumed, no A-reference axiom)

The changed operation is a pure boolean decision over facts that are ALREADY
resolved by unchanged field-metadata accessors. There is no opaque library
callee *under specification*: the patch neither adds nor changes a callee, it
re-selects which of the already-available `field`/`model._meta` facts the
retention condition reads. Those facts are the model's inputs (mapping.md §2);
how they are produced (`get_field`, `is_relation`, `path_infos`,
`_meta.parents`, `_meta.auto_field`, `to_fields`) is unchanged and out of scope.
Hence the retention rule is modelled **deeply** (`keep_at` / `retained_mask`),
not behind any `@ContractOnly`. `axiom_check.py` is an executable sanity check
of that deep model against the intended `lookup_allowed` retention, NOT a
consumed axiom.

## Pre-patch differential (G-DIFF)

`model_prepatch.py` shares the spec **byte-for-byte** (verified: the
`axioms`/`pure`/`pre-conditions`/`post-conditions` regions diff empty) and
reverts step 3 to the pre-patch retention test:
```
keep = pr and not field_is_prior_hop_target[i - 1]
```
which is byte-for-byte the pre-fix `prev_field.is_relation and field not in
prev_field.path_infos[-1].target_fields`. It **fails** verification on the loop
invariant / postcondition
`ToSeq(Result()) == retained_mask(…, True)` — the spec sensing the change. The
discriminating witness is the foreign-key-as-primary-key family: a relation
segment that IS the prior hop's target (`field_is_prior_hop_target = True`, so
the pre-patch test drops it) but is neither a parent link nor a synthesised
identity field and whose reached model has no synthesised identity
(`field_is_parent_link = field_is_auto_identity = model_has_auto_identity =
False`, so the post-patch test retains it). On the concrete F2P scenario the
mask flips from the correct `[1, 1, 1]` to the buggy `[1, 0, 1]` (the `place`
segment dropped) — exactly `test_lookup_allowed_foreign_primary`.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The single changed operation — the retention
boolean — is modelled **deeply** as the spelled-out conjunction `keep_at`
folded by `retained_mask`. There is no axiom (consumed or reference).

## verify(model) ⇒ resolved

`retained_segments` verifies only if its mask equals the post-patch per-segment
retention fold (`retained_mask`, steps 2-3), and by R the mask is the
characteristic vector of the gold patch's `relation_parts` over every segment of
every path, including the discriminating FK-as-PK segment (step 4). The
unchanged membership test (I) maps equal `relation_parts` to equal
`lookup_allowed` verdicts. Therefore an implementation satisfying this spec,
refined by the map above, builds the same `relation_parts` as the gold patch and
returns the same verdict — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ); there are no axioms,
so G-AX is vacuous.
