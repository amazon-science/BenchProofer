# refinement.md — django__django-11179

Maps every operation in `implementation_delete` to its `patch.diff` counterpart in
`Collector.delete` (`django/db/models/deletion.py:262`). Tags: **R** type
refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left as
the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch fast-delete branch)
```python
# Optimize for the case with a single obj and no dependencies
if len(self.data) == 1 and len(instances) == 1:
    instance = list(instances)[0]
    if self.can_fast_delete(instance):
        with transaction.mark_for_rollback_on_error():
            count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)
        setattr(instance, model._meta.pk.attname, None)   # <-- the fix
        return count, {model._meta.label: count}
```
The single added line clears the removed instance's primary-key attribute before
the early return. The general path (`deletion.py:324-326`) already cleared every
removed instance's pk:
```python
for model, instances in self.data.items():
    for instance in instances:
        setattr(instance, model._meta.pk.attname, None)
```

## Modeling decision
The observable result of `delete()` is `(removed_count, label_counts)` plus the
side effect on the in-memory instances (their pk attribute). We model the result
as `(groups, count)`:
* `groups : List RecGroup` carries the post-deletion state of each collected
  record's touched field (`pk : Option Int`); the side effect "instance.pk is now
  None" is `pk := none`.
* `count : Int` is the reported total.

The fast-delete eligibility (`len(self.data)==1 and len(instances)==1 and
can_fast_delete(instance)`) is the unchanged decision `isSingleFast` over the
data shape plus the universally-quantified predicate `directlyDeletable`
(standing for `can_fast_delete`). The two row tallies are unchanged counting
machinery, taken as `directCount` (fast-path `delete_batch` count) and
`generalTotal` (general-path `sum(deleted_counter.values())`).

The fix is the pk-clear on the fast path. So `clearAllPks` (the general path's
`setattr(... None)` loop, modeled deeply as nested `.map`) is applied on BOTH
paths in `implementation_delete`, and the spec pins `result.1 = clearAllPks data`
unconditionally — exactly "every removed record's key is cleared regardless of
path."

## Operation correspondence
| # | Lean op (`implementation_delete`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `match data with [(label,[inst])] => if directlyDeletable inst` | `len(self.data)==1 and len(instances)==1` + `if self.can_fast_delete(instance)` | R / A-reference | data-shape test is R (dict→`List RecGroup`); `can_fast_delete` is the unchanged A-reference, universally quantified — the spec holds for every predicate. |
| 2 | `return ([(label,[{inst with pk := none}])], directCount)` | `count = delete_batch(...)`; **`setattr(instance, pk.attname, None)`**; `return count, {label: count}` | R (count) + **modeled change** (pk clear) | `directCount ↔ delete_batch` count (A-reference numeral). The `pk := none` IS the fix — modeled deeply (never axiomatized, §3). |
| 3 | `return (clearAllPks data, generalTotal)` | general atomic-block deletes + `setattr(... None)` loop (`:324-326`); `return sum(deleted_counter.values()), dict(deleted_counter)` | R (count) + I (pk loop) | `generalTotal ↔ sum(...)` (A-reference numeral). `clearAllPks` ↔ the unchanged general-path clearing loop, modeled deeply. |

## R/I legs ⇒ G-CONF
Branch selection (op 1, R) and the two pk-clearing/return shapes (ops 2,3) are the
R/I content. `directlyDeletable`, `directCount`, `generalTotal` are A-reference
parameters fed identically to both legs in `conformance_check.py`; the differential
isolates the modeled pk-clearing + branch/count selection. `conf_skip = false`:
the impl region has genuine R/I content (the fix lives in op 2).

## No A-consumed row
The proof consumes no property of `directlyDeletable` / `directCount` /
`generalTotal` (all universally quantified), so `meta.json axioms = []`. There is
no `opaque`/`axiom` in `Solution.lean`; `axiom_check.py` is a skip stub.

## F2P alignment
`test_fast_delete_instance_set_pk_none` creates a single `User` (fast-deletable),
calls `u.delete()`, and asserts `u.pk is None`. This is exactly the fast path
(single group, single record, `directlyDeletable = true`). The discriminating
clause `result.1 = clearAllPks data` requires the fast path to clear the key; the
prepatch impl returns `[(label,[inst])]` (key NOT cleared) and so cannot satisfy
it — the real bug. `patch.diff` (gold verbatim) makes the harness resolve.
