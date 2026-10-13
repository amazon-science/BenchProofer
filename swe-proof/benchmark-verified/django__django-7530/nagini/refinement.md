# refinement.md — django__django-7530

The operation-by-operation correspondence between `model.py`'s implementation
(the `members_for_group` impl region and the deep `gathered` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed**, the proof uses the axiom's
`Ensures`, vs **A-reference**, where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed iteration — `makemigrations.Command.handle`

Gold hunk (`django/core/management/commands/makemigrations.py:108`):
```
- for model in apps.get_models(app_label)
+ for model in apps.get_app_config(app_label).get_models()
```
inside the `any(... router.allow_migrate(connection.alias, app_label,
model_name=model._meta.object_name) for app_label in consistency_check_labels
for model in <CHANGED> )` pre-check.

| # | model.py impl op (`members_for_group`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target: int` | the outer-loop `app_label` (`for app_label in consistency_check_labels`) | R | `str` app label ↔ `int` group id; the spec needs only equality of app ids (mapping.md §2). |
| A2 | parameters `owner: List[int]`, `member: List[int]` with `len(owner)==len(member)` | the project registry: each registered model and its owning app (`model._meta.app_label`, `model._meta.object_name`) | R | the project's models tagged with their owning app ↔ two aligned `List[int]` streams (mapping.md §2). |
| A3 | the result `== gathered(ToSeq(owner), ToSeq(member), target)`, the front-recursive filter keeping `member[k]` exactly when `owner[k] == target` | `apps.get_app_config(app_label).get_models()` | A-reference | the changed iterable is modeled **deeply**: `gathered` (the spelled-out per-position filter in the `pure` region) and the verified loop in `members_for_group` ARE the per-app selection. There is no consumed `get_models` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `apps.get_app_config(label).get_models()` and asserts it equals `gathered`. The real callee yields exactly the models whose owning app is `app_label` (mapping.md §3.1); the model loop and the real callee compute the same function. |
| A4 | each gathered `member[k]` becomes an element of `Result()`, later paired with `target` | each yielded `model` is paired with `app_label` as `router.allow_migrate(connection.alias, app_label, model_name=model._meta.object_name)` | I | the surrounding `router.allow_migrate(... app_label ... model ...)`, the `any(...)`, and `check_consistent_history` are UNCHANGED by the gold patch; the only change is which models the inner loop yields. The model isolates that iterable; the pairing with `app_label` is the identical concrete consumer. |

The discriminating content of the change — pairing `app_label` only with its
OWN app's models, never with foreign-app models — lives in the `owner[i] ==
target` guard of `members_for_group` (model) ⇔ the `get_app_config(app_label)`
narrowing of the real iterable (real). The pre-patch `apps.get_models(app_label)`
ignored `app_label` (its first positional arg binds to `include_auto_created`)
and returned the PROJECT-WIDE model list; `model_prepatch.py` reproduces that
(the guard is dropped, every member is appended) and **fails** the postcondition
`ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target)`, which is
exactly the spec sensing the change (G-DIFF). The fail is provable because the
prepatch's loop invariant establishes `ToSeq(result) == ToSeq(member).drop(i)`
(all members verbatim), which differs from `gathered` whenever any
`owner[k] != target`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — narrowing the model iterable from "the whole project" to "this app's
models" — is modeled **deeply** (the spelled-out per-position filter `gathered`
consumed in `members_for_group`, step A3, an **A-reference**), not hidden behind
an axiom about the function under change. There is **no consumed
`@ContractOnly` axiom** in this bundle (the `axioms` region is empty by design):
the only callee the patch introduces (`AppConfig.get_models()`) is the operation
under specification and is therefore an **A-reference** validated by G-AX, never
a consumed axiom.

## C. verify(model) ⇒ resolved

`members_for_group` verifies only if its output equals the exact per-app
selection `gathered` (A3) — every gathered member belongs to `target`
(soundness) and none is omitted (completeness). By R (str app label ↔ int,
registry ↔ aligned streams) the verified selection equals the set of models
`apps.get_app_config(app_label).get_models()` yields on the real registry; by
G-AX the deep model `gathered` equals that real callee (A-reference). The
surrounding `router.allow_migrate(... app_label ...)`/`any`/consistency check is
identical pre/post-patch (A4, I). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the G-AX-validated
deep model — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: the A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ); there is no consumed-axiom trust point here.
