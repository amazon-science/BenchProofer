# mapping.md — django__django-16315

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7d5329852f19c6ae78c6f6f3d3e41835377bf295`, states the type
abstraction, and gives the provenance of the deep-model reference (there is no
consumed `@ContractOnly` axiom).

Repo files under change: `django/db/models/query.py` and
`django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `conflict_columns(requested, field_names, field_columns)` | the conflict-target identifier list assembled for the backend: the resolution of `update_fields` / `unique_fields` in `QuerySet.bulk_create` (`django/db/models/query.py:746`) composed with the `f.column` projection in `SQLInsertCompiler.as_sql` (`django/db/models/sql/compiler.py:1688`, call at line 1725) | the modeled changed behaviour: per requested field-name, the storage identifier handed to `on_conflict_suffix_sql` |
| `lookup(name, field_names, field_columns)` | `Options.get_field(name)` (`django/db/models/options.py:657`) composed with `Field.column` (`django/db/models/fields/__init__.py:855`) | runtime resolution of one requested name to its storage identifier |
| `column_for(name, names, columns)` *(deep model — A-reference)* | `Options.get_field(name).column` — `get_field` (`options.py:657`) + `Field.get_attname_column`/`Field.column` (`fields/__init__.py:894-897`) | pure spec: the storage identifier the requested name designates |
| `name_present(name, names)` | the success domain of `Options.get_field` (the requested name designates a declared field; otherwise `FieldDoesNotExist`) | pure spec: the name is registered |

The pre-patch dataflow the change removes (for the refinement audit, not
referenced from the consumer spec view): in `bulk_create` the `update_fields` /
`unique_fields` lists were passed to `_batched_insert` → `_insert` →
`InsertQuery` as the *name strings* (only `unique_fields` had `pk` substituted),
so `self.query.update_fields` / `self.query.unique_fields` held **field-name
strings**; `SQLInsertCompiler.as_sql` passed those strings directly to
`on_conflict_suffix_sql`, which quotes each verbatim
(`map(self.quote_name, unique_fields)` —
`django/db/backends/postgresql/operations.py:352-364`). The local
`update_fields = [get_field(name) ...]` / `unique_fields = [get_field(name) ...]`
conversions inside `_check_bulk_create_options` (`query.py:723,735`) were
validation-only and did not affect the lists that reached the query.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a field-name `str` (an element of `update_fields` / `unique_fields`) | an `int` identifier | the discriminator is *which* identifier is selected (name vs column), not its text; equal names ↔ equal ints, distinct names ↔ distinct ints |
| a `Field`'s `.column` (`str`, = `db_column or name`) | an `int` identifier (the field's column slot) | column override set ⇒ `column != name` (distinct ints); no override ⇒ `column == name` (equal ints) |
| `update_fields` / `unique_fields` (a `list[str]` of requested names) | `requested: List[int]` | element-wise int ↔ name; `len`/order preserved; specification over `PSeq[int]` via `ToSeq` |
| `self.model._meta` field registry (name → `Field`, each `Field` carrying `.name` and `.column`) | parallel lists `field_names: List[int]`, `field_columns: List[int]` with `field_columns[k]` the column of the field named `field_names[k]` | `get_field(name)` ↔ `find first k with field_names[k]==name`; `Field.column` ↔ `field_columns[k]`; `len(field_columns)==len(field_names)` is the one-column-per-field well-formedness |
| `[f.column for f in resolved]` handed to `on_conflict_suffix_sql` (`compiler.py:1728-1729`) | `Result()`, element i = `column_for(requested[i], field_names, field_columns)` | the produced identifier list, element-wise |
| `get_field(name)` raising `FieldDoesNotExist` for an unknown name | precondition `name_present(...)` (the requested names are all registered) | the patch is reached only after `_check_bulk_create_options`; the F2P inputs name declared fields, so resolution does not raise |

`str` indexing/iteration is banned in Nagini, so names/columns are modelled as
`int` identifiers; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `column_for` / `conflict_columns` deep model ↔ `get_field(name).column`
**Callees (both UNCHANGED):**
- `Options.get_field(name)` (`django/db/models/options.py:657`) — resolves a
  field name to its `Field` via `_forward_fields_map` / `fields_map`; raises
  `FieldDoesNotExist` for an unknown name.
- `Field.column` (`django/db/models/fields/__init__.py:855`, set by
  `set_attributes_from_name` from `get_attname_column`, lines 894-897:
  `column = self.db_column or attname`) — the field's storage identifier, equal
  to its declared `db_column` override when one is configured and to the field's
  own name otherwise.

The changed behaviour is **which attribute is selected** for the conflict
clause: the storage `column`, not the in-memory `name`. That selection is
modelled DEEPLY (`column_for` resolves the name over the registry and reads the
matching slot's *column*); there is **no `get_field`/`column` axiom the proof
consumes**. The deep model is validated equal to the real pipeline out-of-band
by `axiom_check.py` (G-AX): for every requested-name subset of two real models
(one with mixed-case `db_column` overrides so `column != name`, one without),
it asserts `conflict_columns(requested, names, columns)` equals the real
`[model._meta.get_field(n).column for n in requested]`, at the identifier level,
with the override slots required to disagree from the field name (no
double-masking). Docs: `Field.db_column`
https://docs.djangoproject.com/en/4.2/ref/models/fields/#db-column.

**No flag dependency:** `Field.column` is unconditional; the only configuration
that matters is whether `db_column` is set, which the check exercises on both
sides.

## 4. No consumed axioms

`model.py`'s `axioms` region contains no `@ContractOnly` declaration. The
name→field resolution and the column projection are the UNCHANGED callees the
fix composes; they are modelled deeply (the A-reference of §3.1), validated by
G-AX. The proof of `conflict_columns` consumes only the deep model
(`column_for`) and the runtime `lookup` it is paired with — no opaque callee
contract.
