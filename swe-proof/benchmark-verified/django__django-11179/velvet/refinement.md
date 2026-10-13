# refinement.md — django__django-11179

Correspondence between `Solution.lean`'s `fastDelete` impl and `patch.diff`
(the gold patch adds `setattr(instance, model._meta.pk.attname, None)` to the
single-object no-dependency fast-delete short-circuit of `Collector.delete`).
`patch.diff` is the gold verbatim (applies at base_commit, resolves — G-RESOLVE).

## A. The short-circuit — `Collector.delete` fast path

Gold hunk (context + added line):
```
             if self.can_fast_delete(instance):
                 with transaction.mark_for_rollback_on_error():
                     count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)
+                setattr(instance, model._meta.pk.attname, None)
                 return count, {model._meta.label: count}
```

| # | Solution.lean impl op (`fastDelete`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `removed : Nat` (the batch count, given) | `count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)` | R | UNCHANGED batch removal; its `int` result (rows removed, ≥0) ↔ input `removed : Nat` (mapping.md §2). Not re-derived, not axiomatized — taken as given. |
| A2 | `pk := none` (assign the mutable handle) | `setattr(instance, model._meta.pk.attname, None)` | **I** | identical concrete op: the CHANGED op, modeled deeply as the state assignment that clears the identity handle. `instance.<pk.attname> = None` ↔ `pk := none`; `None` ↔ `none` (mapping.md §2). This is the patch's only added line. |
| A3 | `return removed` | `return count, {model._meta.label: count}` | **I** | the reported deletion count is returned UNCHANGED. The first element `count` ↔ `removed`; the `{label: count}` dict is the same count re-keyed (not a distinct observable). Clearing the handle (A2) does not perturb it — pinned by `ensures count = removed`. |

No A (axiom) steps; no A-reference deep models; no kind-3 (changed inexpressible)
steps. The single changed op (A2) is the `setattr(..., None)` state mutation,
modeled deeply and tagged **I**. The unchanged count frame (A3) is **I**.

## B. verify(Solution) ⇒ resolved; prepatch fails

`fastDelete` verifies only if both `pk = none` (forced by A2) and
`count = removed` (forced by A3) hold. By R (mapping.md §2) the verified
post-state equals: `instance.pk is None` after the fast delete, and the returned
count equals `delete_batch(...)`. The F2P test
`test_fast_delete_instance_set_pk_none` asserts exactly `self.assertIsNone(u.pk)`
after `u.delete()` on a fast-deletable instance — the `pk = none` clause. The
PASS_TO_PASS suite (e.g. `test_model_delete_returns_num_rows`) requires the count
to remain correct — the `count = removed` clause. Both are pinned by the spec.

The prepatch (`Solution_prepatch.lean`) omits the `pk := none` assignment (the
buggy short-circuit returns the count but never clears the handle). With a `mut`
parameter left unassigned, its post-state is unconstrained (demonic), so
`prove_correct` fails on exactly the discriminating clause:
```
case «ensures_2: pk = none»
pkOld : Option ℤ
⊢ pkOld = none          -- unprovable: pk left at its pre-state pkOld
```
This is the precise bug the issue describes ("delete() ... doesn't clear PKs ...
should be set to None"). G-DIFF passes.

G-CONF is `conf_skip=true`: the impl region's executable content is the deep
state mutation `pk := none` on a live ORM instance, which has no DB-free R/I
shadow to differential-test (mapping.md §4). No axioms ⇒ no G-AX.
