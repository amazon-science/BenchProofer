# mapping.md — django__django-15629

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 694cf458f16b8d340a3195244196980b2dec34fd`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

The behaviour at issue: when a field that is the target of foreign keys carries
an explicit column collation, the columns that reference it must adopt the SAME
collation, otherwise a reference-constraint between mismatched-collation columns
is rejected by the database. Two repository fix points are observable on the
harness backend (**sqlite3**, the engine `connection` resolves to in the test
images) and are modeled here. Two further gold hunks are inert on this backend
and are NOT modeled (see §3).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `foreignReferenceColumnDesc (refType refCheck targetCollation)` | `ForeignKey.db_parameters(self, connection)` — `django/db/models/fields/related.py:1182` | modeled changed function #1: the column descriptor a referencing field reports |
| `shouldReissueReferences (targetUnique oldType newType oldCollation newCollation)` | the rebuild predicate inside `DatabaseSchemaEditor._alter_field` — `django/db/backends/sqlite3/schema.py:458` | modeled changed function #2: whether referencing columns must be reissued when an altered column changes |
| `ColumnDesc` (structure) | a field's `db_parameters(connection)` dict — keys `type`, `check`, `collation` (base `django/db/models/fields/__init__.py:817`; collation added by `CharField`/`TextField` overrides at `:1185` and `:2369` via `db_params["collation"] = self.db_collation`) | the touched portion of a column descriptor |
| `referencingColumnDesc` | the post-patch dict literal returned by `ForeignKey.db_parameters` | pure spec for #1 |
| `referencesNeedReissue` | the post-patch boolean `new_field.unique and (old_type != new_type or old_collation != new_collation)` | pure spec for #2 |

There are **no axioms and no deep-model references**: both operations are pure
data-flow over their declared inputs (the field's own type/check, the referenced
column's collation, and the before/after descriptors of an altered column). The
values consumed are abstracted as plain inputs (§2), so there is no outside
callee to axiomatize or validate.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a column descriptor dict `{"type": str, "check": str\|None, "collation": str\|None}` | `ColumnDesc` (structure) | dict key `"type"` ↔ `sqlType : String`; `"check"` ↔ `check : Option String` (`None` ↔ `none`); `"collation"` ↔ `collation : Option String` (`None`/absent ↔ `none`, a present string ↔ `some s`) |
| a column collation, `str` or `None` | `Option String` | `None` ↔ `none`; a collation name string `s` ↔ `some s`. The empty string `""` is a distinct present value `some ""` (it never arises in practice but is fuzzed). |
| `new_field.unique` (bool) | `targetUnique : Bool` | identity. On the sqlite path the referenced field is the altered primary key / unique field; `unique` is true exactly when references may target it. |
| `old_type`/`new_type` (the column storage type `str`) | `oldType`/`newType : String` | identity on the rendered type string; `!=` ↔ Lean `!=` (`BEq` on `String`). |
| `old_collation`/`new_collation` (`str\|None`) | `oldCollation`/`newCollation : Option String` | as the collation row above; `!=` ↔ Lean `!=` (`BEq` on `Option String`). |
| `ForeignKey`'s own `db_type`/`db_check` (`str`/`str\|None`) | `refType`/`refCheck` | identity; these are the FK's storage type and check, UNCHANGED by the patch (it only adds the collation key). Abstracted as inputs. |

The referencing field's own type/check are unchanged by the patch; only the
added `"collation"` key is new behaviour, so the spec pins the reported
collation to equal the referenced column's collation while leaving type/check as
inputs.

## 3. Modeled vs inert change sites (provenance)

The gold patch touches four files. Two are observable on the sqlite harness
backend and are modeled; two are inert on it and are deliberately not modeled.

### 3.1 MODELED — `ForeignKey.db_parameters` (`related.py:1182`) — function #1
Pre-patch returns `{"type": …, "check": …}`. Post-patch additionally sets
`"collation"` to the target field's collation:
```python
target_db_parameters = self.target_field.db_parameters(connection)
return {
    "type": self.db_type(connection),
    "check": self.db_check(connection),
    "collation": target_db_parameters.get("collation"),
}
```
This is what makes a referencing column's `column_sql` emit the matching
`COLLATE` clause (`base/schema.py:_iter_column_sql:282` reads
`field_db_params.get("collation")`). It is the load-bearing change for BOTH F2P
tests (creation and alter): on sqlite the related tables are *remade* via
`column_sql`, so the FK column picks up the collation purely through this
descriptor. Modeled by `foreignReferenceColumnDesc`; the reported collation
equals `targetCollation`. **G-CONF site 1** runs the REAL patched
`ForeignKey.db_parameters` on a live `ForeignKey → CharField(db_collation=…)`.

### 3.2 MODELED — sqlite3 `_alter_field` rebuild predicate (`sqlite3/schema.py:458`) — function #2
Pre-patch: `if new_field.unique and old_type != new_type:` rebuilds tables with
FKs pointing at the altered field. Post-patch widens the trigger to a
collation-only change:
```python
old_collation = old_db_params.get("collation")
new_collation = new_db_params.get("collation")
if new_field.unique and (old_type != new_type or old_collation != new_collation):
```
On the alter F2P test the PK's type does not change (it stays `varchar(10)`),
only its collation does; without this widening the referencing tables are never
remade and never pick up the new collation. Modeled by
`shouldReissueReferences`. **G-CONF site 2** diffs the R/I shadow against the
patched predicate's literal decision expression (the django__django-15037
style: a pure boolean decision, no live introspection needed).

### 3.3 INERT — `base/schema.py` `_alter_field` (hunks at `:826`, `:917`, `:1038`)
The base (non-sqlite) `_alter_field` adds the same collation awareness to
`drop_foreign_keys` and to the `rels_to_update` loop. The sqlite backend
**fully overrides** `_alter_field` (`sqlite3/schema.py:425`) and never calls the
base method's body, so these hunks do not execute on the harness backend. They
are the MySQL/Postgres path of the same fix; not modeled because they are not
observable in resolution here.

### 3.4 INERT — `oracle/features.py` (hunk at `:104`)
Adds the new alter test to Oracle's `django_test_skips`. Pure test-skip
bookkeeping for a backend not used by the harness; no runtime behaviour.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15629`**. Site 1 builds
a real model graph per distinct collation (cached; the value space is tiny, 500
draws) and reads the real patched `ForeignKey.db_parameters`; site 2 carries the
≥10⁵ fuzz budget as a pure boolean decision. Both legs are R/I (no A-tagged
callees), so `conf_skip=false`.
