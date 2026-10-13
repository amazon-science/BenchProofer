# mapping.md — django__django-11066

## Symbol binding (file:line @ base_commit 4b45b6c8e4d7c9701a332e80d3b1c84209dc36e2)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_renameContentType` / `problem_spec_renameContentType` | `RenameContentType._rename` | `django/contrib/contenttypes/management/__init__.py:13-36` |
| `saveTarget` (pure helper) | the persistence-routing decision of `Model.save(using=…)` vs the database router | the changed line `content_type.save(using=db, update_fields={'model'})` (`__init__.py:27`) |
| `renameInStore` (pure helper) | `content_type.model = new_model` followed by `content_type.save(update_fields={'model'})` — updating the located row's model name | `__init__.py:24-27` |
| `renameConflicts` (pure helper) | the `IntegrityError` raised when the save collides with `ContentType`'s unique `(app_label, model)` constraint, plus the `transaction.atomic(using=db)` rollback and the `except IntegrityError: content_type.model = old_model` fallback — nothing is persisted | `__init__.py:26-31` (the `try/atomic/except IntegrityError` around the save) |
| `ContentTypeRec` (pure helper) | one `ContentType` row, restricted to the touched columns `app_label`, `model` | the row returned by `get_by_natural_key` |
| `Alias` (`Nat`) | a database connection alias (`schema_editor.connection.alias`, the router's write target) | `__init__.py:15` |

The modeled function is `RenameContentType._rename`. It is the only function whose
behavior changes and the only one observed by the FAIL_TO_PASS test
(`test_existing_content_type_rename_other_database`), which migrates on a
non-default database `'other'` while a router directs writes to `'default'`, then
asserts the renamed content type is present **on `'other'`**.

### What the function does (base_commit)

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
                content_type.save(update_fields={'model'})      # <-- the changed line
        except IntegrityError:
            content_type.model = old_model
        else:
            ContentType.objects.clear_cache()
```

Step by step:
1. `db = schema_editor.connection.alias` — the database this migration runs against.
2. read the `ContentType` row for `(app_label, old_model)` **from `db`**
   (`db_manager(db).get_by_natural_key(...)`); on `DoesNotExist`, do nothing.
3. set the row's `model` field to `new_model`;
4. persist the row **inside `transaction.atomic(using=db)`**; if the write
   collides with `ContentType`'s unique `(app_label, model)` constraint
   (a row keyed `(app_label, new_model)` already exists in the database
   receiving the write), `IntegrityError` is raised, the atomic block rolls
   the write back, and the `except IntegrityError` branch restores
   `content_type.model = old_model` — nothing is persisted anywhere
   (exercised by the P2P test `test_content_type_rename_conflict`).

The read in step 2 is explicitly directed at `db` (`db_manager(db)`). The save in
step 4, at base_commit, supplies **no** explicit target database. `Model.save()`
without `using=` consults the database router (`db_for_write`) to choose the write
target, which need not be `db`. So the read happens on `db` but the write can be
routed to a different database (in the test, the router returns `'default'` while
`db == 'other'`); the rename therefore never lands on `db`. The post-patch line
passes `using=db`, which directs the write to `db` and skips router routing,
matching the database the row was read from.

### Lean modeling

- A multi-database world is modeled as a total function `world : Alias → List
  ContentTypeRec` — each alias maps to that database's content-type rows. `Alias`
  is `Nat` (an injective encoding of the distinct alias strings; only equality is
  observed).
- `db : Alias` is the connection alias the migration runs against
  (`schema_editor.connection.alias`).
- `routerChoice : Alias` is the alias the router's `db_for_write` would pick for a
  routed (un-targeted) write. It is a free input — the proof needs no property of
  it; the fix turns precisely on whether the save consults it.
- `saveTarget routerChoice using?` is the persistence-routing decision:
  `some d ⇒ d` (an explicit target overrides the router), `none ⇒ routerChoice`
  (no explicit target ⇒ the router decides). The post-patch impl passes
  `some db`; the pre-patch impl passes `none`.
- `renameInStore store appLabel oldModel newModel` is steps 3–4's effect on the
  store the write lands in: the row matching `(appLabel, oldModel)` has its
  `model` set to `newModel`; all other rows are untouched. When no row matches,
  it is the identity (covers the `DoesNotExist` branch).
- `renameConflicts store appLabel oldModel newModel` is the unique-constraint
  check on the store receiving the write: the rename collides iff
  `newModel ≠ oldModel` and a row keyed `(appLabel, newModel)` already exists
  there. On collision the real code's `IntegrityError`/`atomic` rollback leaves
  every database untouched; the model returns `world` unchanged. (When
  `newModel = oldModel` the "colliding" row is the row being renamed itself —
  an UPDATE to the same value never violates the constraint.)

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| the set of database connection aliases | `Alias` (`Nat`) | each distinct alias string ↔ a distinct `Nat`. |
| a database's `django_content_type` table (touched columns only) | `List ContentTypeRec` | each row ↔ one `ContentTypeRec ⟨app_label, model⟩`; row order is the table's iteration order. |
| `schema_editor.connection.alias` | `db : Alias` | the alias the migration targets. |
| `router.db_for_write(ContentType)` | `routerChoice : Alias` | the alias a routed write would land on. |
| `Model.save(using=db, …)` vs `Model.save(…)` | `saveTarget routerChoice (some db)` vs `saveTarget routerChoice none` | explicit target vs router-routed target. |
| `content_type.model = new_model; content_type.save(update_fields={'model'})` | `renameInStore store appLabel oldModel newModel` | update the matching row's `model` column; leave the rest. |
| `try: with transaction.atomic(using=db): …save… except IntegrityError: content_type.model = old_model` | `renameConflicts store appLabel oldModel newModel` guard (conflict ⇒ result = input world) | unique `(app_label, model)` collision ⇒ rollback, nothing persisted. |
| `self.app_label`, `old_model`, `new_model` | `appLabel`, `oldModel`, `newModel : Nat` | encoded label/model-name identities (equality observed). |

The result of `_rename` is the post-call state of every database. We model it as
the resulting `world' : Alias → List ContentTypeRec`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — which database
  the save is directed to — is modeled DEEPLY by `saveTarget` over the explicit
  target (`Option Alias`) and the router's choice (SPEC_GUIDE §3: a deeply-modeled
  changed decision is never axiomatized). The row update is modeled deeply by
  `renameInStore`. No property of an external callee is consumed by the proof, so
  the `axioms` region is empty and **G-AX skips**.
- `router.allow_migrate_model(db, ContentType)` (the early-return guard on line
  16) is **unchanged** by the patch and does not bear on the routing fix; the F2P
  test runs with migration allowed. It is not modeled (modeling only the touched
  behavior; SPEC_GUIDE §3). Its omission constrains no output component the spec
  leaves free — the spec pins the full resulting world.
- `transaction.atomic(using=db)` is the context manager around the save; per the
  issue + hints it does **not** route the query (only `save(using=…)` does), so it
  has no effect on the modeled write target. Its ROLLBACK effect on a
  unique-constraint collision IS modeled, together with the
  `except IntegrityError` fallback, by the `renameConflicts` guard (conflict ⇒
  every database unchanged).
- `get_by_natural_key`/`db_manager(db)` is the read, explicitly on `db`; modeled
  as `(world db).find?` over the matching row. The `DoesNotExist` branch ↔
  `find? = none`.

## G-CONF fuzz seed

Pinned LCG seed: **11066** (see `conformance_check.py` `SEED`). Corpus: randomized
multi-database worlds (2–4 aliases; each database holds 0–6 `ContentTypeRec` rows
with `app_label`/`model` drawn from small ranges so the natural-key match actually
bites) crossed with `db` ∈ the alias set, `routerChoice` ∈ the alias set (so the
router both does and does not coincide with `db`), and `(appLabel, oldModel,
newModel)` drawn so the located row sometimes exists and sometimes does not, over
≥1e5 fuzzed inputs. The R/I shadow of `implementation_renameContentType` (save
target `= db`, conflict ⇒ rollback) is diffed against an in-process replica of the
POST-PATCH `_rename` routing (`save(using=db)` ⇒ write lands on `db`;
`IntegrityError` on a unique-key collision ⇒ atomic rollback, nothing persisted).
Hand-picked edge cases pin the discriminating clauses: `routerChoice ≠ db` with
the row present on `db`, and the collision case (`(appLabel, newModel)` already
present on `db`).
