# refinement.md — django__django-11066

Maps every operation in `implementation_renameContentType` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `renameContentType` (`RenameContentType._rename`)

Post-patch repo code (`patch.diff`, `__init__.py:13-36`):
```python
def _rename(self, apps, schema_editor, old_model, new_model):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    db = schema_editor.connection.alias
    if not router.allow_migrate_model(db, ContentType):
        return
    try:
        content_type = ContentType.objects.db_manager(db).get_by_natural_key(self.app_label, old_model)
    except ContentType.DoesNotExist:
        pass
    else:
        content_type.model = new_model
        try:
            with transaction.atomic(using=db):
                content_type.save(using=db, update_fields={'model'})   # changed line
        except IntegrityError:
            content_type.model = old_model
        else:
            ContentType.objects.clear_cache()
```

Lean impl (`implementation_renameContentType`):
```lean
def implementation_renameContentType
    (world : Alias → List ContentTypeRec)
    (db routerChoice : Alias)
    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
  if !hasKey (world db) appLabel oldModel then
    return world
  let target := saveTarget routerChoice (some db)
  if renameConflicts (world target) appLabel oldModel newModel then
    return world
  let mut updated := world
  updated := fun a =>
    if a = target then renameInStore (world target) appLabel oldModel newModel
    else world a
  return updated
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `world : Alias → List ContentTypeRec` (input carrier) | the multi-database state read/written by the ORM | **R** | each alias ↔ one database's `django_content_type` rows (touched columns `app_label`, `model`); `Alias` ↔ alias string by an injective `Nat` encoding (only equality observed). See mapping.md. |
| 2 | `if !hasKey (world db) appLabel oldModel then return world` | `content_type = ContentType.objects.db_manager(db).get_by_natural_key(self.app_label, old_model); except DoesNotExist: pass` | **R** | the read is explicitly directed at `db` (`db_manager(db)`); `hasKey (world db) …` ↔ "a row with that natural key exists on `db`". `DoesNotExist` ↔ `hasKey = false`, in which case nothing changes (early return = identity). Unchanged by the patch. |
| 3 | `let target := saveTarget routerChoice (some db)` | `content_type.save(using=db, update_fields={'model'})` | **I** (deep model of the changed op) | **the fixed operation.** `saveTarget` reproduces the routing decision: `some db` (an explicit `using=db`) ⇒ the write lands on `db`, overriding the router; `none` (no `using=`) ⇒ the router's free `routerChoice` decides. The post-patch line passes `using=db`, so the impl passes `some db` ⇒ `target = db`. This is the heart of the fix. (`transaction.atomic(using=db)` is the surrounding context manager; per the issue/hints it does NOT route the query, so it has no effect on the write target and is not modeled.) |
| 3b | `if renameConflicts (world target) appLabel oldModel newModel then return world` | `try: with transaction.atomic(using=db): …save… except IntegrityError: content_type.model = old_model` | **R** | the receiving database's unique `(app_label, model)` constraint rejects a rename whose destination key `(appLabel, newModel)` already exists there (with `newModel ≠ oldModel`; an UPDATE to the same value collides only with the row being renamed itself, which is not a violation). `IntegrityError` ⇒ the `atomic(using=db)` block rolls the write back and the except branch restores the in-memory `model` — nothing is persisted anywhere ⇒ result = input world. UNCHANGED by the patch; exercised by the P2P test `test_content_type_rename_conflict` (both rows survive the migration). |
| 4 | `updated := fun a => if a = target then renameInStore (world target) … else world a` | `content_type.model = new_model; content_type.save(…)` | **R** | the save persists the renamed row to the target database (`world target`), leaving all other databases untouched. `renameInStore` ↔ setting the located row's `model` to `newModel`; with `target = db` and the row present on `db`, this updates exactly `db`. |
| 5 | `renameInStore store appLabel oldModel newModel` (pure helper) | `content_type.model = new_model` applied to the located row | **R** | maps each row to itself unless it matches `(appLabel, oldModel)`, in which case its `model` becomes `newModel`. Natural keys are unique, so at most one row is affected (mapping.md). |
| 6 | `return updated` | end of `_rename` (post-call database state) | **R** | the resulting `world'` ↔ the post-call state of every database. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `_rename` routing.

## Callee provenance (no consumed axiom)

- `router.allow_migrate_model(db, ContentType)` — the early-return guard on
  `__init__.py:16`, UNCHANGED by the patch and not on the routing path. The F2P
  test runs with migration allowed. Not modeled; its omission constrains no
  output component the spec leaves free (the spec pins the full resulting world).
- `transaction.atomic(using=db)` — the surrounding context manager. Per the issue
  + hints it does not route the query (only `save(using=…)` does), so it has no
  effect on the modeled write target and is not modeled.
- `get_by_natural_key` / `db_manager(db)` — the read, explicitly on `db`; captured
  directly by `hasKey (world db) appLabel oldModel`. `DoesNotExist` ↔ `false`.
- The `IntegrityError` fallback (`content_type.model = old_model`) together with
  the `transaction.atomic(using=db)` rollback IS modeled, by the
  `renameConflicts` guard: a rename whose destination natural key already exists
  in the database receiving the write is rejected and rolled back, leaving every
  database untouched. It is unchanged by the patch but observable (P2P test
  `test_content_type_rename_conflict`), so the spec must — and does — pin it.

## Soundness check (verify ⟹ correct)

- `problem_spec_renameContentType` pins the result EXACTLY at every alias `a`
  (full extensional equality to an input-grounded expression) — directive 5
  (frame): every database's post-state is determined by the input `world`, the
  natural key, and `db`. No output component is left unconstrained; the outcome is
  pinned to be INDEPENDENT of `routerChoice` (it never appears on the spec's RHS).
  The conflict branch (`renameConflicts (world db) …` ⇒ result = input world)
  matches the real repo's `IntegrityError`/atomic-rollback behavior, so the spec
  never demands a world that violates the DB's unique natural-key constraint.
  No ungrounded oracle (directive 8) — the postcondition is dischargeable only by
  actually locating the row on `db`, checking the collision, and applying
  `renameInStore` to `db`.
- The prepatch impl reproduces the PRE-FIX routing: it passes `saveTarget
  routerChoice none = routerChoice`, modeling `save()` without `using=` (the
  router's `db_for_write` chooses the write target). It violates the spec on the
  discriminating clause `routerChoice ≠ db` with the row present on `db`: the spec
  requires the rename to land on `db` and `routerChoice` to be untouched, but the
  prepatch writes to `routerChoice` and leaves `db` unchanged. Its carried gold
  proof cannot close (G-DIFF/G-PANEL).
- This discriminating case is precisely the FAIL_TO_PASS assertion added by the
  test patch (`test_existing_content_type_rename_other_database`): a router
  directs writes to `'default'` while the migration runs on `'other'` (db); the
  test asserts the renamed content type is present **on `'other'`**. Pre-fix the
  write leaked to `'default'`; post-fix `using=db` lands it on `'other'`.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `_rename` routing over hand-picked edge cases (including `routerChoice ≠ db`
  with the row present on `db`, the row absent ⇒ DoesNotExist, and the row present
  only on a non-`db` database) plus ≥1e5 fuzzed multi-database worlds.
