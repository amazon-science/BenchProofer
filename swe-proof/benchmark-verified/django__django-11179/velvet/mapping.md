# mapping.md — django__django-11179

Binds `Solution.lean` symbols to the repo at
`base_commit = 19fc6376ce67d01ca37a91ef2f55ef769f50513a`.

Repo file under change: `django/db/models/deletion.py`
(`Collector.delete`, the single-object no-dependency short-circuit).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fastDelete (mut pk : Option Int) (removed : Nat)` | `Collector.delete(self)` — the `len(self.data)==1 and len(instances)==1` + `can_fast_delete(instance)` short-circuit, `django/db/models/deletion.py:275-281` | the modeled short-circuit (single standalone record, fast path) |
| `pk` (`mut`) | `instance.<model._meta.pk.attname>` — the instance's primary-key attribute (read as `instance.pk`, written via `setattr(instance, model._meta.pk.attname, None)`) | the mutable identity handle the fix clears |
| `removed` | `count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)` — the number of rows the batch removal deleted | the (unchanged) batch removal count |
| `count` (return) | the first element of `return count, {model._meta.label: count}` | the reported deletion count |

Precondition modeled: the short-circuit body is entered **only** when
`len(self.data) == 1 and len(instances) == 1 and self.can_fast_delete(instance)`
— i.e. a single instance with **no dependencies** ("fast delete"). The model
scopes itself to exactly this branch; no `require` is needed because every
field the branch reads (`pk`, `removed`) is supplied directly as an input.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `instance.pk` : an int (present while the row exists) / `None` (cleared) | `Option Int` | `some k` ↔ an integer PK value `k`; `none` ↔ `None`. `setattr(instance, pk.attname, None)` ↔ `pk := none`. |
| `model._meta.pk.attname` (the PK attribute *name*) | (subsumed) | the attribute the handle lives under; the model observes only the handle's value, so the name is an R detail, not a separate carrier. |
| `count` : `int` (≥0, rows removed) | `Nat` | non-negative; exact. `delete_batch(...)` ↔ the input `removed`; `return count, {...}` ↔ `return removed`. |

## 3. Callee provenance

None (no axioms, no A-reference deep models). The two operations the branch
performs are:
- `sql.DeleteQuery(model).delete_batch(...)` — **UNCHANGED** by the fix; its
  result is taken as the input `removed` (not re-derived, not axiomatized).
- `setattr(instance, model._meta.pk.attname, None)` — the **CHANGED** op, modeled
  deeply as the assignment `pk := none` (I-tagged, see refinement.md). No outside
  contract is consumed.

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The impl region's executable
content is the deep state assignment `pk := none` — clearing a live ORM model
instance's primary-key attribute *after a real database fast-delete*. There is
no DB-free R/I shadow to differential-test:

- The only observable the fix produces is a **side effect on a live model
  instance** (`instance.pk` becomes `None`) that materializes solely after
  `Collector.delete()` has run the `sql.DeleteQuery(...).delete_batch(...)`
  removal against a real backend, inside `transaction.mark_for_rollback_on_error`.
  Reproducing it requires standing up a Django model + DB connection + a saved
  instance and calling `.delete()` — i.e. the F2P integration test itself
  (`test_fast_delete_instance_set_pk_none`), not a pure transliteration this
  gate can fuzz.
- The changed op's content (`pk := none`) is a pure state mutation whose only
  R/I shadow would be the constant `None`; diffing `None == None` carries no
  information. There is no input-dependent computation to refute.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the impl region is the deep state
mutation of a live ORM instance with no DB-free R/I shadow, set
`meta.json conf_skip=true` and ship a `status=skip` stub. Soundness of the
modeled mutation is carried instead by **G-VERIFY** (the spec provably forces
`pk = none` on return) and **G-DIFF** (the prepatch, which never assigns `pk`,
fails exactly the `pk = none` clause — see refinement.md §B). The unchanged
count frame (`count = removed`) is likewise pinned by the spec.

## 5. Notes

The model is the genuine-`mut` form (directive 5 showcase): `pk` is declared
`mut`, assigned `pk := none`, and its post-state pinned to the exact value
`none`. The unchanged frame (the count) is pinned by `count = removed`. The
input/output `Option`-only form is an equivalent alternative; the `mut` form was
chosen because the fix *is* a state mutation and it exercises directive 5
directly. Both verify cleanly.
