# mapping.md — django__django-16661

## Modeled function

`ModelAdmin.lookup_allowed(self, lookup, value)` —
`django/contrib/admin/options.py`, `def` at **line 439** @ base_commit
`d687febce5868545f99974d2499a91f81a32fef5`. The gold patch changes the
`relation_parts.append(part)` guard at **lines 461–469** (hunk header
`@@ -461,12 +461,14 @@`).

Lean triple: `problem_spec_lookupAllowed` / `implementation_lookupAllowed` /
`correct_lookupAllowed` in `Solution.lean`.

## What the function does (post-patch, base_commit source)

```
relation_parts = []
prev_field = None
for part in lookup.split(LOOKUP_SEP):
    try:
        field = model._meta.get_field(part)         # line 459
    except FieldDoesNotExist:
        break                                        # nonexistent -> stop
    if not prev_field or (
        prev_field.is_relation
        and field not in model._meta.parents.values()          # NOT a parent link
        and field is not model._meta.auto_field                # NOT the synth PK
        and (
            model._meta.auto_field is None                     # model has no synth PK
            or part not in getattr(prev_field, "to_fields", [])# OR not a prev target col
        )
    ):
        relation_parts.append(part)                  # line 471
    if not getattr(field, "path_infos", None):       # line 472: non-relational -> stop
        break
    prev_field = field                               # line 476
    model = field.path_infos[-1].to_opts.model       # line 477
if len(relation_parts) <= 1:
    return True                                       # local filter / nothing
valid_lookups = { self.date_hierarchy } ∪ { declared list_filter entries }
return not { SEP.join(relation_parts),
             SEP.join(relation_parts + [part]) }.isdisjoint(valid_lookups)
```

The `related_fkey_lookups` early-return loop (lines 446–452) is the FK raw-id
popup allowance; it is modeled as the single boolean input `fkeyAllowed`.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python (repo reality) | Lean model | notes |
|---|---|---|
| `lookup.split(LOOKUP_SEP)` — the chain of components, each resolved against the current model's `_meta` | `steps : List PathStep` | one `PathStep` per component, in order; each carries the metadata the walk reads at that component |
| a component's string name | `PathStep.part : Nat` | injective encoding of the distinct component strings; only equality observed |
| `model._meta.get_field(part)` succeeds (no `FieldDoesNotExist`) | `PathStep.exists_ : Bool` | `false` triggers the `break` (nonexistent field) |
| `field.is_relation` (of the field resolved AT this component; becomes `prev_field` for the NEXT one) | `PathStep.isRelation : Bool` | carried forward into the next step's `prev` |
| `getattr(field, "path_infos", None)` is truthy | `PathStep.hasPathInfos : Bool` | `false` triggers the non-relational `break` |
| `field in prev_field.path_infos[-1].target_fields` (PRE-patch discriminator only) | `PathStep.inTargetFields : Bool` | used ONLY by the prepatch buggy impl |
| `field in model._meta.parents.values()` | `PathStep.inParents : Bool` | concrete-inheritance parent link |
| `field is model._meta.auto_field` | `PathStep.isAutoField : Bool` | field IS this model's synthesised PK |
| `model._meta.auto_field is not None` | `PathStep.modelHasAutoField : Bool` | model has a synthesised PK |
| `part in getattr(prev_field, "to_fields", [])` | `PathStep.partInPrevToFields : Bool` | component names a prev relation target col |
| `prev_field` before the first relational hop (`None`) vs a resolved field | `LoopState.prev : Option Bool` | `none` = `None`; `some b` = a field whose `is_relation` is `b` |
| `relation_parts` | `LoopState.relationParts : List Nat` | list of appended component identities |
| the loop-final `part` (last processed component) | `LoopState.lastPart : Nat` | used in `relation_parts + [part]` |
| `break` taken | `LoopState.stopped : Bool` | once true, later components are skipped (matches `break`) |
| `valid_lookups` (declared allowed filter chains, split on SEP) | `validLookups : List (List Nat)` | `self.date_hierarchy` ∪ `list_filter` entries, each as a component-id list |
| `related_fkey_lookups` early `return True` | `fkeyAllowed : Bool` | the FK raw-id popup allowance |
| return value `True`/`False` | `result : Bool` | |
| `not {A, B}.isdisjoint(valid_lookups)` | `validLookups.contains A \|\| validLookups.contains B` | membership of the two join-keys |

### The three collapsing situations (post-patch `continuesLocal`)

`continuesLocal step = !inParents && !isAutoField && (!modelHasAutoField || !partInPrevToFields)`
is the Lean transcription of the added conjunction

```
field not in model._meta.parents.values()
and field is not model._meta.auto_field
and (model._meta.auto_field is None or part not in getattr(prev_field,"to_fields",[]))
```

The component is appended when `prev is none` OR
`prev.is_relation && continuesLocal step`.

The PRE-patch guard was `prev_field.is_relation and field not in target_fields`,
i.e. `prev && !inTargetFields` (the prepatch impl).

## F2P discriminating case (test_lookup_allowed_foreign_primary)

Chain `restaurant__place__country` over `Waiter`:
- `restaurant` → FK to `Restaurant`: `exists_`, `isRelation`, `hasPathInfos` all true;
  `prev = none` so it is appended. → `relationParts = [restaurant]`.
- `place` → `Restaurant.place` is a `OneToOneField(primary_key=True)`: it IS a
  relation and continues the walk. Under `Restaurant`'s metadata it is neither a
  parent link nor `auto_field` is unaffected here; crucially `Restaurant` has NO
  synthesised auto PK (its PK is the FK `place`), so `modelHasAutoField = false`
  ⇒ `continuesLocal = true` ⇒ **appended** (post-patch). Pre-patch:
  `field in target_fields` was TRUE ⇒ **dropped**.
- `country` → FK on `Place`: appended in both. 

Post-patch `relationParts = [restaurant, place, country]` (len 3) matches the
declared `list_filter` entry `restaurant__place__country` ⇒ **True**.
Pre-patch `relationParts = [restaurant, country]` (len 2), which is neither
`restaurant__country` nor `restaurant__country__<last>` in `list_filter` ⇒
**False** (the incorrect `DisallowedModelAdminLookup`).

Encoded in the G-CONF corpus and in the construction spec-probe.

## Callee provenance / flag deps

No unchanged callee contributes a proof-consumed property. `get_field`,
`.is_relation`, `.path_infos`, `._meta.parents`, `._meta.auto_field`,
`.to_fields` are all pure metadata reads whose OUTCOMES are abstracted into the
`PathStep` booleans (a structure restricted to the touched fields, SPEC_GUIDE §2)
and fed as inputs. The decision the patch changes (which components count as
relation parts) is modeled DEEPLY (`continuesLocal` / `stepFold`), never
axiomatized (SPEC_GUIDE §3, §0.7). Hence `axiom_check.py` is a skip stub.

## G-CONF fuzz seed

**Pinned seed: 16661.** `conformance_check.py` fuzzes ≥10⁵ random
`(steps, validLookups, fkeyAllowed)` inputs plus hand-picked edge cases
(including the F2P chain) and asserts the Python R/I shadow of
`implementation_lookupAllowed` agrees with an in-process oracle transcribing the
post-patch `lookup_allowed` control flow over the same abstracted metadata.
