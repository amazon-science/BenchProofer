# mapping.md — django__django-15280

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 973fa566521037ac140dcece73fceae50ee522f1`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every callee folded into a free input.

Repo file under change: `django/db/models/fields/related_descriptors.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `linkChildrenToParents (children : List Child) (lookup : Nat → Nat)` | `RelatedManager.get_prefetch_queryset` — the reverse-relation linking loop, `django/db/models/fields/related_descriptors.py:646-648` (inside the `create_reverse_many_to_one_manager` closure) | the modeled changed function (links each prefetched child object back to its parent) |
| `Child.key` | `rel_obj_attr(rel_obj)` = `self.field.get_local_related_value(rel_obj)` — `related_descriptors.py:642`, defined `related.py:675` | the grouping key by which a child row is matched to its parent |
| `Child.existingParent` | whether `rel_obj` already has the reverse relation cached, `self.field.is_cached(rel_obj)` — added at `related_descriptors.py:647`; `is_cached`/`get_cached_value` defined in `django/db/models/fields/mixins.py:21,12` (the field's `_state.fields_cache[cache_name]`) | the parent association the child already carries (`some p`) or not (`none`) |
| `lookup` | `instances_dict.__getitem__`, where `instances_dict = {instance_attr(inst): inst for inst in instances}` — `related_descriptors.py:639` | maps a child's grouping key to the parent object it belongs to |
| `resolveOne` / `resolvedSeq` | the per-`rel_obj` body of the `for rel_obj in queryset:` loop (post-patch), `related_descriptors.py:645-648` | pure spec: the parent each child ends up associated with, and the batch sequence |

The pre-patch repo behaviour the change corrects (refinement audit only, not in
the consumer spec view): the loop body
`instance = instances_dict[rel_obj_attr(rel_obj)]; setattr(rel_obj, self.field.name, instance)`
ran unconditionally, overwriting any reverse relation already populated on
`rel_obj` by a nested prefetch (`related_descriptors.py:649-650` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the prefetched child rows `queryset` (a `list` of model instances, in iteration order) | `children : List Child` | the `j`-th model instance ↔ `children[j]`; `len(queryset)` ↔ `children.length`; iteration order ↔ list order. Only the two observed projections (key, cached-parent) are carried; all other model state is orthogonal. |
| `rel_obj_attr(rel_obj)` — the child's local-related value (a hashable id / tuple) | `Child.key : Nat` | each distinct id value ↔ a distinct `Nat`; observed only by `instances_dict` lookup, i.e. by equality of keys. The concrete encoding is irrelevant: the model holds for every `lookup : Nat → Nat`. |
| `self.field.is_cached(rel_obj)` + the cached reverse object | `Child.existingParent : Option Nat` | `is_cached(rel_obj) == True` with cached parent `p` ↔ `some (id p)`; `is_cached(rel_obj) == False` ↔ `none`. The parent identity is observed only by which object the relation ends up pointing at. |
| `instances_dict[k]` — the parent for grouping key `k` | `lookup : Nat → Nat` (a free function input) | `instances_dict[k]` ↔ `lookup (id k)`; modeled as a total function because every child in `queryset` has a matching parent in `instances` by construction of the prefetch (`query = {'%s__in' % field.name: instances}`, `related_descriptors.py:643`). |
| the post-loop relation `getattr(rel_obj, self.field.name)` for each child, in order | `out : List Nat` | the `j`-th child's resulting parent identity ↔ `out[j]`. This is the observable the F2P test checks (`Room.house.is_cached(self.room) is True`, and accessing `house.rooms.first().house` issues no query). |

`is_cached`, `get_local_related_value`, and `instances_dict` are all UNCHANGED by
the patch; the patch only adds the `if not self.field.is_cached(rel_obj):` guard
around the existing two-line body. They are therefore folded into the free
inputs (`children.existingParent`, `children.key`, `lookup`) — the spec claims
nothing about how any of them is computed and holds for every value they take.

## 3. Callee provenance — why there are NO axioms and NO G-AX

The patch adds a control-flow guard; it introduces no new external computation
whose contract the proof must assume. Every value the modeled routine consults is
produced by machinery the patch does not touch:

- `self.field.is_cached(rel_obj)` → `Child.existingParent` is `some _` vs `none`.
  Unchanged (`mixins.py:21`); enters as a free input.
- `rel_obj_attr(rel_obj)` → `Child.key`. Unchanged (`related.py:675`); enters as a
  free input.
- `instances_dict[...]` → `lookup`. Unchanged (`related_descriptors.py:639`);
  enters as a free input.

Because the spec is **universally quantified** over `children` and `lookup` and
makes no claim about how any callee computes its value, there is nothing to check
against a real callee. Hence **no module-level `axiom`, no A-reference deep model
of an external callee, and no `axiom_check.py` / G-AX** (precedent:
django__django-16631, which likewise folds unchanged plumbing into free inputs
and ships no axioms). The whole behavioural content — "keep a pre-existing
association, otherwise look it up" — is modeled deeply in the `pure`/`impl`
regions and pinned by G-VERIFY; its discriminating power is exercised by G-DIFF
and G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15280`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `resolveOne`/`resolvedSeq` (the R/I ops) to Python — a child with
a pre-existing parent keeps it, a child without one is looked up — and diffs that
against the patched repo loop's observable (the per-child resulting parent) over
≥10⁵ fuzzed `(children, lookup)` batches. There are no A-tagged callees to leave
as real-repo calls (§3), so the shadow is pure R/I.
