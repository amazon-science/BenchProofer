# mapping.md — django__django-16661

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d687febce5868545f99974d2499a91f81a32fef5`, states the type
abstraction, and gives the provenance of every modelled fact. There are no
`@ContractOnly` axioms (the retention rule is modelled deeply), so the "callee
provenance" section instead documents the structural facts the per-segment
field bundle resolves to.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `retained_segments(...)` | `ModelAdmin.lookup_allowed` — `django/contrib/admin/options.py:439`; the per-segment retention loop, lines 457-477 | the modelled changed function: the loop that builds the retained relation-segment list whose later membership test (lines 479-497) decides the lookup |
| `keep_at(...)` | the retention condition `if not prev_field or (...)` at `options.py:467-471` (post-patch body) | pure spec: whether a NON-first segment is retained, given its resolved structural facts |
| `retained_mask(...)` | the cumulative effect of `relation_parts.append(part)` across the loop (`options.py:455,471`) | pure spec: the per-segment retention outcome over the whole path, as a 0/1 mask, front-recursive |

The modelled observable is the **retention mask** — one flag per path segment,
1 iff that segment is appended to `relation_parts`. The mask determines exactly
which segments form `relation_parts`, hence the join the membership test at
`options.py:493-497` (`LOOKUP_SEP.join(relation_parts) … .isdisjoint(...)`)
checks; that membership test is UNCHANGED by the patch (an I-step, §refinement)
and consumes the mask. Pinning the mask therefore pins the only behaviour the
patch changes.

## 2. Type / state abstraction (the R-refinements)

Each iteration of the real loop resolves the segment `part` to a `Field`
object via `model._meta.get_field(part)` and reads a small bundle of structural
facts off `field`, `prev_field`, and `model._meta`. The model projects each
segment to one entry of six parallel `List[bool]` vectors (index = segment
position along the path):

| repo quantity (at the loop step for segment k) | model carrier | bijection |
|---|---|---|
| `bool(prev_field)` then `prev_field.is_relation` — whether the PRIOR segment resolved to a relation field (`options.py:467-468`) | `prev_is_relation[k]: bool` | True iff segment k-1's field exists and `is_relation`; for k=0 there is no prior field (`prev_field is None`), handled by the always-retain first-segment branch |
| `field in model._meta.parents.values()` — the field is a concrete-inheritance parent link of the reached model (`options.py:470`, post-patch) | `field_is_parent_link[k]: bool` | membership in the parent-link set ↔ the flag |
| `field is model._meta.auto_field` — the field IS the reached model's synthesised automatic identity field (`options.py:471`, post-patch) | `field_is_auto_identity[k]: bool` | object identity ↔ the flag |
| `model._meta.auto_field is None` (negated) — whether the reached model HAS a synthesised automatic identity field (`options.py:472-473`, post-patch) | `model_has_auto_identity[k]: bool` | `auto_field is not None` ↔ the flag |
| `part in getattr(prev_field, "to_fields", [])` — the segment is the explicit local column the prior hop targets (`options.py:474`, post-patch) | `segment_targets_prior_hop[k]: bool` | membership in the prior field's `to_fields` ↔ the flag |
| `field in prev_field.path_infos[-1].target_fields` — the field is one of the PRIOR relation hop's target fields (`options.py:469`, **pre-patch only**) | `field_is_prior_hop_target[k]: bool` | membership in the prior hop's `target_fields` ↔ the flag |

The first five facts are the ones the POST-patch condition reads; the sixth is
the one the PRE-patch condition read (`prev_field.path_infos[-1].target_fields`,
`options.py:469`). `field_is_prior_hop_target` is carried in the (frozen, shared)
spec signature as a read-only input so the pre-patch skeleton
(`model_prepatch.py`) can express its retention test with the IDENTICAL
signature; `model.py`'s verified (post-patch) impl does not consult it, faithful
to the gold patch having removed that reference.

All six vectors are read-only inputs, required and ensured at
`Acc(list_pred(·), 1/2)` (directive 5). The result mask is the only freshly
allocated, fully-owned object.

### How the F2P scenario projects (provenance of the facts)

Path `Waiter` → `restaurant` (FK→Restaurant) → `place`
(`OneToOneField(Place, primary_key=True)`) → `country` (FK on Place):

| seg | part | resolved facts (post-patch reads) | `field_is_prior_hop_target` (pre-patch read) |
|---|---|---|---|
| 0 | restaurant | first segment, `prev_field is None` → always retained | — |
| 1 | place | `prev_is_relation=True`; `field_is_parent_link=False` (Restaurant has no concrete parents); `field_is_auto_identity=False` (Restaurant's pk is the explicit OneToOne `place`, not a synthesised `AutoField`); `model_has_auto_identity=False` (`Restaurant._meta.auto_field is None`); `segment_targets_prior_hop=True` (the `restaurant` FK's defaulted `to_field` is the related pk name `"place"`, so `"place" ∈ restaurant.to_fields`) — but this is dominated by `model_has_auto_identity=False`, which makes the final guard vacuously satisfied, so the segment is retained | **True** — `place` is Restaurant's pk, which is exactly the target of the `restaurant` FK (`restaurant.path_infos[-1].target_fields == (Restaurant._meta.pk,) == (place,)`) |
| 2 | country | `prev_is_relation=True`; not a parent link / auto id; Place has an auto-id pk (`model_has_auto_identity=True`) but `country` does not target it (`segment_targets_prior_hop=False`) | False |

Post-patch retention mask `[1, 1, 1]` (every segment retained → join
`restaurant__place__country` ∈ `list_filter` → `lookup_allowed` returns True).
Pre-patch mask `[1, 0, 1]` (segment `place` dropped because it is the prior
hop's target → join shortened to `restaurant__country` ∉ `list_filter` →
returns False → the spurious `DisallowedModelAdminLookup`). This is exactly the
F2P test `test_lookup_allowed_foreign_primary`.

## 3. Callee provenance (axioms)

None consumed. The retention rule is pure boolean decision logic over the
per-segment facts above (`keep_at`) folded across the path (`retained_mask`),
modelled deeply. The field-resolution that PRODUCES the per-segment facts
(`model._meta.get_field`, `.is_relation`, `.path_infos`, `_meta.parents`,
`_meta.auto_field`, `.to_fields`) is UNCHANGED by the patch and is not modelled;
the patch changes only which of those already-available facts the retention
condition consults. `axiom_check.py` (stdlib-only) is the executable
A-reference-style sanity check: it transcribes both predicates, enumerates all
fact combinations, and confirms the two disagree exactly on the
foreign-key-as-primary-key family and that the concrete F2P scenario flips from
`[1,0,1]` (bug) to `[1,1,1]` (fix).

The `target_fields` test the patch removes is sound provenance for the bug:
`ForeignObject.path_infos` builds a `PathInfo` whose `target_fields` are the
related model's primary-key fields (`django/db/models/fields/related.py:825,845`
— `target_fields=self.foreign_related_fields` / `target_fields=(opts.pk,)`), so
a relation that is itself the reached model's pk satisfies `field in
prev_field.path_infos[-1].target_fields` and was wrongly treated as
locally-reachable.
