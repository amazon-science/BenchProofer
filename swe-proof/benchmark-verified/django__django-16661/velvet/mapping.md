# mapping.md — django__django-16661

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d687febce5868545f99974d2499a91f81a32fef5`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every per-hop fact the descent decision consults.

Repo file under change: `django/contrib/admin/options.py`.
Changed function: `ModelAdmin.lookup_allowed` (`options.py:439`); the touched
hunk is the per-segment append condition inside its
`for part in lookup.split(LOOKUP_SEP)` loop (`options.py:461-471`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `keptSegments (hops : List Hop)` | the per-segment `relation_parts.append(part)` decision walked over `lookup.split(LOOKUP_SEP)` inside `ModelAdmin.lookup_allowed` (`options.py:457-473`) | the modeled changed function: for each walked segment, decide whether it is RECORDED as a genuine relational descent |
| `keepSegment (h : Hop)` | the patched append guard `not prev_field or (prev_field.is_relation and field not in model._meta.parents.values() and field is not model._meta.auto_field and (model._meta.auto_field is None or part not in getattr(prev_field, "to_fields", [])))` (`options.py:464-470` post-patch) | pure spec: the keep/drop decision for ONE segment |
| `keepMask (hops : List Hop)` | the list `relation_parts` is built from — the per-segment expansion of the keep decisions (the appended-or-not flag of every walked segment) | pure spec: per-segment expansion, front-recursive |
| `Hop` (7 `Bool` fields) | the per-segment introspection state at one loop iteration (see §2) | the read-only per-hop input carrier |

No axiomatized callees. Every field of `Hop` is a single boolean fact obtained
from UNCHANGED Django field/`_meta` introspection (`Field.is_relation`,
`Options.parents`, `Options.auto_field`, `Field.to_fields`,
`PathInfo.target_fields`). The patch changes only how these facts are COMBINED
into the append decision; it changes none of the facts themselves. They are
therefore modeled as read-only per-hop inputs (tagged **R** in refinement.md),
not as contracts the proof consumes — hence no `axiom` and no `axiom_check.py`
(G-AX skips). `conf_skip = false`: the impl region's content (the `keepSegment`
boolean combination and the backward fold) is all R/I and is exercised by G-CONF.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo state. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality (per loop iteration) | Lean carrier | bijection |
|---|---|---|
| the walked lookup path `lookup.split(LOOKUP_SEP)` | `List Hop` | each segment ↔ one `Hop`; path length ↔ `hops.length`; order preserved |
| `not prev_field` (no prior step yet — first segment) | `Hop.isFirst : Bool` | `not prev_field` ↔ `isFirst = true` |
| `prev_field.is_relation` | `Hop.priorIsRelation : Bool` | truthy ↔ `true`. Only consulted when `not isFirst`; on the first segment `priorIsRelation` is irrelevant (the `isFirst` disjunct dominates) |
| `field in model._meta.parents.values()` | `Hop.concreteParentLink : Bool` | the field is the link to a concrete-inheritance ancestor record ↔ `true` |
| `field is model._meta.auto_field` | `Hop.redundantLocalValue : Bool` | abstract redundancy flag (A): the field is the record's auto-generated identity (PK) ↔ `true`. (Spec-view name is mechanism-free per directive 6; the repo meaning is recorded here.) |
| `model._meta.auto_field is not None` | `Hop.hasRedundantLocalValue : Bool` | abstract redundancy flag (B): the current record HAS an auto identity field ↔ `true`. |
| `part in getattr(prev_field, "to_fields", [])` | `Hop.priorAlreadyCovers : Bool` | abstract redundancy flag (C): the segment names a field the prior relation explicitly references (its `to_fields`) ↔ `true`. |
| `field in prev_field.path_infos[-1].target_fields` | `Hop.targetOfPrior : Bool` | the field is one of the prior relation's target fields — the PRE-patch redundancy criterion ↔ `true`. Modeled only so the prepatch skeleton can name the old rule; the patched `keepSegment` never reads it |

`bool` ↔ `Bool` is the identity bijection. Lean has no aliasing; `hops` is a
read-only input (`keptSegments` builds and returns a fresh `List Bool`, never
mutates `hops`) — the `mut`-frame obligation (SPEC_GUIDE §0.5) holds because no
parameter is `mut`.

### Bijection grounding (why the abstraction is faithful to lookup_allowed)
In the real loop, on iteration over segment `part`:
* `field = model._meta.get_field(part)` is the field reached by this segment;
* `prev_field` is the field from the previous iteration (`None` on the first);
* `model` is the model whose `_meta` is consulted THIS iteration (it is advanced
  to `field.path_infos[-1].to_opts.model` at the END of the iteration).

So all five patched sub-conditions read state available at the segment, and the
single `relation_parts.append(part)` happens iff the guard is true — which is
exactly `keepSegment h` for the `Hop h` abstracting that iteration. `relation_parts`
is the subsequence of recorded segments; `keepMask hops` is the per-segment
keep/drop flag stream from which `relation_parts` is the `filter (· = true)`
projection. The spec pins the full flag stream (stronger than the projected list:
it pins each segment's decision positionally), so no wrong per-segment rule can
satisfy it.

## 3. Provenance of the changed decision (no callee axioms)

The patched guard is transcribed directly from the gold hunk
(`options.py:464-470`, post-patch):

```python
if not prev_field or (
    prev_field.is_relation
    and field not in model._meta.parents.values()   # not a concrete-parent link
    and field is not model._meta.auto_field          # not the auto PK
    and (
        model._meta.auto_field is None               # no auto PK, OR
        or part not in getattr(prev_field, "to_fields", [])  # not already referenced
    )
):
    relation_parts.append(part)
```

`keepSegment` is the Boolean transliteration of this guard
(`isFirst ∨ (priorIsRelation ∧ ¬concreteParentLink ∧ ¬redundantLocalValue ∧
(¬hasRedundantLocalValue ∨ ¬priorAlreadyCovers))`); the spec-view field names are
mechanism-free (directive 6), their repo meaning is in §2 above. The discriminating case the F2P
test `test_lookup_allowed_foreign_primary` exercises: a FK-as-PK segment
(`restaurant__place__country`) where the field is the record's own PK but is
itself a ForeignKey — NOT an auto field and NOT a concrete-parent link — so the
patched guard records it (`country` is a genuine descent), whereas the pre-patch
guard (`field not in prev_field.path_infos[-1].target_fields`, i.e.
`¬targetOfPrior`) treated it as redundant and dropped it, mis-shortcutting the
path and raising `DisallowedModelAdminLookup`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16661`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`keepSegment` (the impl's Boolean decision) and the backward `while` fold
(building `result` by prepending) to Python; the oracle is the patched
append-guard transcribed INDEPENDENTLY from `patch.diff`'s `+` lines, applied
left-to-right. There are no A-tagged callees in the impl region, so the shadow is
pure R/I. The check is exhaustive over all 2⁷ = 128 single-segment `Hop`
configurations and fuzzes ≥10⁵ random `Hop` paths; exit 0 iff zero disagreements.
