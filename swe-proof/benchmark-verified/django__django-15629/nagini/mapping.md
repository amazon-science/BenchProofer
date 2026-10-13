# mapping.md — django__django-15629

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 694cf458f16b8d340a3195244196980b2dec34fd`, states the type
abstraction, and records the provenance and G-AX evidence for each deep model.

Repo files under change:
`django/db/models/fields/related.py`, `django/db/backends/base/schema.py`,
`django/db/backends/sqlite3/schema.py`, `django/db/backends/oracle/features.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reported_reference_parameters(target_params, own_type, own_check)` | `ForeignKey.db_parameters(self, connection)` — `django/db/models/fields/related.py:1182` | modeled changed function: the relational field's reported DB parameters now carry the referenced column's collation |
| `references_need_rebuild(old_type, new_type, old_collation, new_collation)` | the re-derive trigger inside `BaseDatabaseSchemaEditor._alter_field` — `django/db/backends/base/schema.py:826-833` (`drop_foreign_keys`) and the mirrored `sqlite3` guard at `django/db/backends/sqlite3/schema.py:458` | modeled changed decision: columns referencing an altered column are dropped/rebuilt when the referenced type OR collation differs |
| `key_type()` / `key_check()` / `key_collation()` | the `"type"` / `"check"` / `"collation"` keys of a `db_parameters` dict (`django/db/models/fields/__init__.py:817-828`, `1185-1188`) | pure spec: parameter-name tokens |
| `none_value()` | the empty/absent collation value `None` returned by `dict.get("collation")` | pure spec: empty-collation sentinel |
| `emits_collation_clause(params)` | the COLLATE-emitting branch of `_iter_column_sql` — `django/db/backends/base/schema.py:282-283` (`if collation := field_db_params.get("collation"): yield self._collate_sql(collation)`) | pure spec: a column SQL emits a collation clause iff its params declare a non-empty collation |

Repo callees the modeled functions invoke but do NOT change (read in the
worktree; relied on only structurally, not axiomatized):
- `ForeignKey.db_type` (`related.py:1179`) and `db_check` (`related.py:1176`) —
  supply the FK's own `type`/`check`; unchanged by the patch.
- `self.target_field.db_parameters(connection)` — the referenced column's
  parameters; for a `CharField`/`TextField` PK this dict carries `"collation"`
  (`django/db/models/fields/__init__.py:1185-1188`, `2369-2372`). The fix reads
  `target_db_parameters.get("collation")` from it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `db_parameters` dict `{"type":…, "check":…, "collation":…}` | `Dict[int, int]` keyed by the constant tokens `key_type()/key_check()/key_collation()` | a string/identity value ↔ a distinct `int`; the empty value `None` ↔ `none_value()`; a **missing key** ↔ key ABSENT from the dict (membership `k in d`) |
| a collation name `str` (e.g. `"utf8_bin"`, `"nocase"`) or `None` | `int` identity, `None` ↔ `none_value()` | only equality/membership are observed (the code does `old_collation != new_collation` and `field_db_params.get("collation")` truthiness), so integer identity is a faithful carrier |
| a `type` string (e.g. `"varchar(10)"`) | `int` identity | only `old_type != new_type` and dict membership are observed |
| `dict.get("collation")` returning `None` when the key is absent | `key_collation() in d` is False (so the value is "not reported") vs. present-with-`none_value()` ("reported empty") | the regression IS the key being absent; the carrier distinguishes absent (membership False) from present-empty |

`str` indexing is banned in Nagini and is irrelevant here: no collation or type
string is ever decomposed — only compared for equality and tested for presence.

## 3. Deep-model provenance (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `reported_reference_parameters` ↔ `ForeignKey.db_parameters` (A-reference)
**Callee modeled deeply (not axiomatized):** `ForeignKey.db_parameters`. Gold
post-patch source (`related.py:1182`):
```python
def db_parameters(self, connection):
    target_db_parameters = self.target_field.db_parameters(connection)
    return {
        "type": self.db_type(connection),
        "check": self.db_check(connection),
        "collation": target_db_parameters.get("collation"),
    }
```
Pre-patch it returned only `{"type": …, "check": …}` — no `"collation"` key, so
every consumer reading `db_params.get("collation")` saw `None`, dropping the
COLLATE clause on FK columns (the MySQL constraint error in the issue). The deep
model `reported_reference_parameters` spells out the three-entry dict with the collation
taken from the referenced column's parameters. **G-AX** (`axiom_check.py`) builds
real `(Pony CharField-pk with db_collation, Rider FK→Pony)` model pairs and
asserts the real `fk_field.db_parameters(connection)` carries `"collation"`
equal to the target column's collation (and `None` when none), over 6 boundary +
120 fuzz collation identities, and that the emitted FK column SQL carries a
COLLATE clause exactly when the target declares a collation (3.3).

### 3.2 `references_need_rebuild` ↔ `_alter_field` re-derive trigger (A-reference)
**Decision modeled deeply (not axiomatized):** the trigger that drops and
rebuilds columns referencing an altered PK/unique column. Gold post-patch
`base/schema.py:826-833`:
```python
old_collation = old_db_params.get("collation")
new_collation = new_db_params.get("collation")
drop_foreign_keys = (
    self.connection.features.supports_foreign_keys
    and ((old_field.primary_key and new_field.primary_key)
         or (old_field.unique and new_field.unique))
    and ((old_type != new_type) or (old_collation != new_collation))
)
```
and the mirrored `sqlite3/schema.py:458` guard
`if new_field.unique and (old_type != new_type or old_collation != new_collation)`.
Pre-patch both used `old_type != new_type` alone, so a PURE collation change
(type unchanged) did not re-derive the referencing columns and the FKs were left
with the old collation — the AlterField F2P failure. The deep model
`references_need_rebuild` isolates exactly the changed sub-expression
`(old_type != new_type) or (old_collation != new_collation)` (the connection
features and primary/unique guards are unchanged and out of scope). **G-AX**
asserts the gold-patched base-schema source contains this exact disjunction and
validates the boolean truth table over the full 3×3×3×3 (type × collation)
identity grid, including the discriminating pure-collation-change case.

### 3.3 `emits_collation_clause` ↔ `_iter_column_sql` COLLATE branch (A-reference, consequence)
`base/schema.py:282-283`:
```python
if collation := field_db_params.get("collation"):
    yield self._collate_sql(collation)
```
A column SQL carries a COLLATE clause iff `field_db_params.get("collation")` is
truthy — i.e. the key is present and non-empty. This is the create-time consumer
of §3.1: once the FK reports the target's collation, its column SQL gets the
matching COLLATE clause, which is what `test_create_fk_models_to_pk_field_db_collation`
observes. G-AX checks the real `schema_editor.column_sql(...)` COLLATE-token
presence tracks the referenced column's collation.

## 4. Why these two functions (faithful multi-site skeleton)

The gold patch has one root cause and three consumers:
- **Root cause** (`related.py`): `ForeignKey.db_parameters` must expose the
  target's collation → `reported_reference_parameters` (§3.1). Both F2P tests depend on it.
- **Consumer A — create** (`base/schema._iter_column_sql`): unchanged code that
  already emits COLLATE from `db_params["collation"]`; now fed the FK's
  collation → modeled as the consequence clause `emits_collation_clause` (§3.3).
- **Consumer B — alter** (`base/schema._alter_field`, `sqlite3/schema._alter_field`):
  the re-derive trigger gains the collation disjunct →
  `references_need_rebuild` (§3.2). The `rels_to_update` collation branch in
  `base/schema.py:1038-1056` and the `oracle/features.py` expected-failure entry
  are the same behaviour on other backends / a test-skip bookkeeping entry, with
  no independently-observable behaviour on the SQLite eval backend.

Both modeled functions are spelled out deeply; there is **no consumed axiom**.
