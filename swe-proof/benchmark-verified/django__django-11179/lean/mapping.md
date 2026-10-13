# mapping.md — django__django-11179

## Modeled function
`Collector.delete` — `django/db/models/deletion.py:262` @ base_commit
`19fc6376ce67d01ca37a91ef2f55ef769f50513a`. The changed line is the addition at
`deletion.py:280` (post-patch), inside the single-object/no-dependency
early-return branch (`deletion.py:277-281`).

## What the function does (touched view)
`delete()` removes the objects collected in `self.data` (a dict
`model -> list[instance]`), returns `(total_deleted, {label: count})`, and — as a
side effect — sets each removed instance's primary-key attribute to `None` so the
in-memory Python object reflects that it no longer exists in the database.

Two paths:
* **Single-object optimization** (`len(self.data) == 1 and len(instances) == 1`
  and `self.can_fast_delete(instance)`): delete the one row directly via
  `delete_batch`, then return early.
* **General path**: an atomic block performs the deletes; afterwards a loop over
  every collected instance sets its primary-key attribute to `None`
  (`deletion.py:324-326`).

The bug: the single-object optimization returned **before** clearing the
instance's primary key, so an object deleted via that path kept its stale pk in
memory. The general path always cleared it. The fix inserts the same
pk-clearing into the optimization branch before its early return.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean | note |
|---|---|---|
| an instance, touched field only | `structure Instance where pk : Option Int` | `pk = some v` ↔ a live primary key value `v`; `pk = none` ↔ `instance.pk is None` |
| `model._meta.label` (str) | `Nat` (`Label`) | identity only; carried through, never compared |
| `self.data` (dict `model -> list[instance]`) | `List (Label × List Instance)` (`Group`) | one entry per collected model, in iteration order |
| `len(self.data) == 1 and len(instances) == 1` | `data` matches `[(label, [instance])]` | exactly one model whose instance list is a singleton |
| `self.can_fast_delete(instance)` | parameter `directlyDeletable : Instance → Bool` | unchanged callee; universally quantified (A-reference) |
| `count = delete_batch([instance.pk], using)` | parameter `directCount : Int` | unchanged callee's row count for the optimization path (A-reference) |
| general-path `sum(deleted_counter.values())` | parameter `generalTotal : Int` | unchanged deletion machinery's total (A-reference) |
| `setattr(instance, model._meta.pk.attname, None)` | `{ instance with pk := none }` | the modeled change (deep) |
| general-path pk-clear loop (`deletion.py:324-326`) | `clearAllPks data` (nested `.map`) | unchanged loop, modeled deeply |
| return `(count, {label: count})` / `(sum, dict)` | result `: (List Group) × Int` | total count modeled; label-keyed dict is the same count data (unchanged), not separately carried |

## Callee provenance + flag deps
* `can_fast_delete` (`deletion.py:158`) — UNCHANGED. Decides whether an instance
  has no dependent collections and can be removed by a single batch delete. Its
  decision depends on model relations, not on the instance's pk value, so it is
  left as a universally-quantified parameter `directlyDeletable` (A-reference);
  the spec holds for every such predicate and pins only that the correct branch
  clears the pk. No property of it is consumed by the proof.
* `sql.DeleteQuery(...).delete_batch` / `_raw_delete` — UNCHANGED. Produce the
  numeric row counts; abstracted as the parameters `directCount` / `generalTotal`.
* No flag dependency.

## Axioms
None consumed. The changed side effect (clearing the primary key) and the
general-path clearing loop are modeled deeply (`{ · with pk := none }` /
`clearAllPks`); SPEC_GUIDE §3 forbids axiomatizing the changed operation. The
unchanged callees are universally-quantified parameters, so the proof consumes no
callee property. `axiom_check.py` is therefore a skip stub.

## G-CONF
`conformance_check.py` shadows the R/I impl (branch selection + pk clearing) in
Python and differential-tests it against an in-process replica of the post-patch
`delete()` at the same abstraction (taking the fast-delete decision and the two
abstract counts as inputs, exactly as both legs receive them). Pinned fuzz seed:
**11179** (also in `conformance_check.py`).
