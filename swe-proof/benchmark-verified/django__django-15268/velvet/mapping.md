# mapping.md — django__django-15268

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed for the migration-operation optimization-eligibility bundle.

All `file:line` references are at `base_commit`
`0ab58c120939093fea90822f376e1866fc714d1f`.

## 1. Modeled functions (Lean ↔ repo)

| Lean `method` | repo symbol | repo location @ base_commit | carrier |
|---|---|---|---|
| `reorderableBase` | `ModelOperation.can_reduce_through` (NEW; extraction of the inline expression in `ModelOperation.reduce`) | `django/db/migrations/operations/models.py` — added at `:34` reduce body; the new method lands right after `reduce` | `(self.name, operation) -> bool` |
| `reorderableTogether` | `AlterTogetherOptionOperation.can_reduce_through` (NEW override) | `django/db/migrations/operations/models.py:531` (new method appended to `AlterTogetherOptionOperation`, after `migration_name_fragment` at `:528`) | `(self.name, type(self), operation) -> bool` |
| `optimizeAgainst` | the `reduce(...)` decision an `AlterUniqueTogether`/`AlterIndexTogether` op runs (resolved through the MRO: `ModelOptionOperation.reduce` → `ModelOperation.reduce` → `Operation.reduce`) | `django/db/migrations/operations/models.py:34` (`ModelOperation.reduce`), `:409` (`ModelOptionOperation.reduce`), `base.py:123` (`Operation.reduce`) | `(self.name, type(self), operation) -> reduce-result` |

`ModelOperation.reduce` itself (`models.py:34`) is *modified* by the patch
(`not operation.references_model(...)` → `self.can_reduce_through(...)`), but
that edit is a behaviour-preserving **extraction**: the disjunct it now calls
(`can_reduce_through`) returns exactly the old inline expression at the
`ModelOperation` level. The single *behavioural* change is the new
`AlterTogetherOptionOperation.can_reduce_through` override.

## 2. Type bijection (G-CONF + G-AX use this table)

The decision `op.reduce(other, app_label)` for an `AlterFooTogether` `op`
observes only these features of `op` and `other`:

| repo reality | Lean model |
|---|---|
| a migration `Operation` `other`, as seen by an `AlterFooTogether.reduce` | `OtherOp` (inductive, `pure` region) |
| `AlterUniqueTogether` / `AlterIndexTogether` instance `other` named `n` | `OtherOp.together (name := n) (kind := .unique \| .index)` |
| `DeleteModel` instance `other` named `n` | `OtherOp.deleteModel (name := n)` |
| any other `Operation` `other` (whose `references_model(self.name)` is `b` and whose `elidable` attribute is `e`) | `OtherOp.generic (refsSelf := b) (elidable := e)` |
| `self.name_lower` (the model an `AlterFooTogether` targets) | `selfName : Nat` (model identity; lower-cased name ↔ a `Nat` id) |
| `type(self)` ∈ {`AlterUniqueTogether`, `AlterIndexTogether`} | `selfKind : TogetherKind` (`.unique` / `.index`) |
| `other.references_model(self.name, app_label)` | `affectsModel selfName other` (see below) |
| `isinstance(other, AlterTogetherOptionOperation)` | `isTogetherOp other` |
| `type(other) is type(self)` | `sameKind selfKind other` |
| `isinstance(other, (self.__class__, DeleteModel)) and self.name_lower == other.name_lower` (the `ModelOptionOperation.reduce` merge branch) **or** `other.elidable` (the `Operation.reduce` `elif operation.elidable: return [self]` branch, `base.py:131`) | `mergeable selfName selfKind other` |
| `reduce` returns a list (`[operation]` supersede / `[self]` elide-neighbour — either way the pair collapses to one op) | `OptimizeOutcome.merge` |
| `reduce` returns the bool `True` (may optimize across `other`) | `OptimizeOutcome.reorderable` |
| `reduce` returns the bool `False` (blocked) | `OptimizeOutcome.blocked` |

`AlterFooTogether`, `DeleteModel`, and every other declarative operation class
leave `elidable = False` (the `Operation` class default, `base.py:32`; only
`RunSQL`/`RunPython` expose an `elidable=` kwarg). `self.elidable` is therefore
always `False` (so `Operation.reduce`'s `if self.elidable: return [operation]`
branch is dead), and a `together`/`deleteModel` neighbour is never elidable —
the elidable answer is carried only on `OtherOp.generic`. An elidable `generic`
neighbour short-circuits `reduce` to `[self]` (merge) BEFORE
`can_reduce_through` is consulted, which is why `mergeable` (not the reorder
test) carries the bit.

Model names are lower-cased strings in Django; only equality on them is ever
observed (`references_model` and the merge name-check are both
`name.lower() == self.name_lower`), so a `Nat` identity is a faithful carrier
(string-equality ↔ `Nat`-equality bijection; G-CONF assigns each distinct model
name a distinct `Nat`).

### `references_model` (`affectsModel`)

`Operation.reduce` calls `other.references_model(self.name, app_label)`. This is
an **UNCHANGED callee**, but it is *not* axiomatized:

- For `AlterFooTogether` operations, `references_model` is literally
  `name.lower() == self.name_lower` (`models.py:31`), an inline field comparison
  transliterated as `Nat` equality — an **I (identical concrete op)** leg,
  covered by G-CONF (the real `references_model` is invoked by the oracle).
- For `DeleteModel`, `references_model` returns **`True` unconditionally**
  (`models.py:279` — "the deleted model could be referencing the specified model
  through related fields"), NOT name equality. So `affectsModel _ (.deleteModel _)
  = true`, while the *merge* branch (`mergeable`) still keys on name equality
  (`ModelOptionOperation.reduce`'s `self.name_lower == operation.name_lower`).
  This asymmetry was caught by G-CONF on the M1 self-check (a `DeleteModel` of a
  *different* model previously modeled as reorderable but is actually blocked)
  and fixed; it is an **I** leg (the real `DeleteModel.references_model` is run
  by the G-CONF oracle).
- For any *other* operation type, `references_model` may be anything (the base
  `Operation.references_model` returns `True`, `CreateModel`/`RenameModel`
  inspect bases/fields). We make **no claim** about it: `OtherOp.generic`
  carries its result `refsSelf` as a free input (the §0.7 "abstract the
  unchanged callee as a free input" pattern). Likewise the operation's
  (unchanged) `elidable` attribute is carried as the free input `elidable`.
  No axiom, hence **no G-AX**.

The patch adds behaviour ONLY for `isinstance(other, AlterTogetherOptionOperation)`,
so the decision for a `generic` `other` is unchanged pre- and post-patch (merge
if elidable, else reorderable iff `!refsSelf`) — there is no discriminator on
the `generic` branch, which is why leaving its `references_model` and `elidable`
free costs no spec strength.

## 3. Axioms / callee provenance

**No axioms.** Every callee the modeled decision touches is either transliterated
as a concrete op (I — `references_model` name-equality, `isinstance`/`type`
checks, the `name_lower` merge comparison, the `operation.elidable` merge
branch) or carried as a free input (`generic.refsSelf`, `generic.elidable`).
`axiom_check.py` therefore records `status="skip"`
(no axioms). G-AX is N/A for this bundle.

## 4. Discriminating behaviour (what the spec senses; G-DIFF)

For an `AlterFooTogether` `self` (name `m`, kind `k`) reducing against a
*different-type* `AlterFooTogether` `other` on the **same** model `m`:

- pre-patch: `reduce` bool branch = `not other.references_model(m)` = `not (m==m)`
  = `False` ⇒ `OptimizeOutcome.blocked` — the optimizer cannot move `self` across
  `other`, so the remove-then-add quadruple is NOT collapsed.
- post-patch: `can_reduce_through` = `... or (isinstance(other, AlterTogether)
  and type(other) is not type(self))` = `... or (True and True)` = `True`
  ⇒ `OptimizeOutcome.reorderable` — the optimizer reduces `AlterUnique(set()) …
  through AlterIndex(set())`, then merges the same-type pair, collapsing 4 ops
  to 2.

`Solution_prepatch.lean` reproduces the pre-patch `reorderableTogether`
(the `return base` body, no different-type disjunct) and fails the
`reorderableTogether` `ensures` on exactly this input (G-DIFF).

## 5. G-CONF

`conformance_check.py` instantiates the **real** patched operation classes
(`AlterUniqueTogether`, `AlterIndexTogether`, `DeleteModel`, plus real generic
ops: `AlterModelTable` for the non-elidable cases and `RunSQL` — including a
minimal `references_model`-overriding subclass — for the elidable cases) from
`django/db/migrations/operations` at `base_commit` with `patch.diff` applied,
calls the real `op.reduce(other, app_label)`, maps its result to
`OptimizeOutcome` (list⇒`merge`, `True`⇒`reorderable`, `False`⇒`blocked`),
and diffs against the Lean shadow over ≥10⁵ fuzzed `(selfName, selfKind, other)`
triples (boundary: same/different model, same/different together-kind,
DeleteModel, generic refs/no-refs × elidable/non-elidable). **Pinned fuzz seed:
`15268`.** Exit 0 iff zero disagreements.
