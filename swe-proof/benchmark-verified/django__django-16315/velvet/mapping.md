# mapping.md — django__django-16315

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7d5329852f19c6ae78c6f6f3d3e41835377bf295`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every callee touched by the change.

Repo files under change: `django/db/models/query.py`,
`django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `conflictColumns (fields : List Field)` | the conflict-target column list built in `SQLInsertCompiler.as_sql` — `django/db/models/sql/compiler.py:1725-1729` (the `update_fields` / `unique_fields` arguments to `on_conflict_suffix_sql`) | the modeled changed function: produce the column tokens for the conflict-resolution clause |
| `Field` *(structure)* | `django.db.models.fields.Field` — only the two observable string attributes `name`/`attname` (the model attribute name) and `column` (the DB column) are carried | rich-object abstraction (SPEC_GUIDE §2: structure with only the touched fields) |
| `Field.column` | `Field.column` — `django/db/models/fields/__init__.py:855,894` (`get_attname_column`: `column = self.db_column or attname`) | UNCHANGED projection: the DB column name of a field |
| `Field.attr` | `Field.name` / `Field.attname` — the model-side attribute name | UNCHANGED projection: the field name (what the buggy code used) |
| `dbColumns (fields : List Field)` | the comprehension `(f.column for f in fields)` — `compiler.py:1728-1729` (post-patch) | pure spec: the per-field DB-column expansion of the field list |

### Upstream callee NOT modeled (free-input boundary)
The patch's `query.py` hunks resolve the caller-supplied field-*name* strings
into `Field` objects via `self.model._meta.get_field(name)` and move that
resolution up into `bulk_create` so the `Field` objects (not strings) propagate
to the query (`query.py:782-789`; the duplicate resolution inside
`_check_bulk_create_options` at `query.py:720,731` is removed). `get_field`
itself is **unchanged** by the patch — only *where* it is called moves. The
modeled boundary (the conflict-suffix column extraction in `as_sql`) therefore
takes the **already-resolved** `Field` list as a free input, exactly as the
exemplar `django__django-11095` takes its `selected` registration list as a free
input. No axiom/deep-model is needed for `get_field`; §3 explains why this is
sound (the resolution is identical pre- and post-patch and cannot be the source
of a resolve/not-resolve divergence).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Django `Field` object (resolved) | `Field` structure | `f` ↔ `{ attr := f.name.toList, column := f.column.toList }`; only the two string attributes the suffix observes are carried |
| `f.column` (Python `str`) | `Field.column : List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `length`; empty `str` ↔ `[]` |
| `f.name` / `f.attname` (Python `str`) | `Field.attr : List Char` | as above |
| `(f.column for f in fields)` / `list(...)` (the comprehension consumed by `on_conflict_suffix_sql`) | `List (List Char)` | ordered list of column strings; Python list order ↔ `List` order; generator materialised to a list (the suffix builder joins it left-to-right) |
| `update_fields` argument position | `fields : List Field` | one application of `conflictColumns` |
| `unique_fields` argument position | `fields : List Field` | the SAME operation, applied to the second argument; one model covers both (refinement.md §A) |

A single Python character `ch` ↔ Lean `Char` via `Char.ofNat (ord ch)` (total
and exact on the BMP). `List Char` indexing is total and sound.

## 3. Why the modeled boundary is faithful (no over-/under-claim)

The patch changes exactly one observable thing: the strings handed to the
conflict-suffix builder (`on_conflict_suffix_sql`) for the `ON CONFLICT(...)`
target and the `DO UPDATE SET ...` assignments. Pre-patch those were the field
**names**; post-patch they are the field **columns** (`f.column`).

* The suffix builder itself (`on_conflict_suffix_sql`, which quotes and joins
  whatever tokens it is given) is **UNCHANGED** — it is downstream of the model
  and not modeled.
* `get_field` (name→Field resolution) is **UNCHANGED** — the patch only relocates
  the call so the `Field` objects reach the query; it resolves the same fields
  pre- and post-patch. It is upstream of the model (free-input boundary, §1) and
  cannot cause a resolve/not-resolve divergence, so it needs no axiom.
* `Field.column` (`get_attname_column`: `column = self.db_column or attname`) is
  **UNCHANGED** — it is a pure projection carried directly as the structure's
  `column` field via the bijection (§2); there is no algorithm to deep-model, so
  it is plain **R**, not an A-reference.

Hence there is **no axiom and no deep-model reference** in this bundle. The one
changed operation — "use `f.column`, not `f.name`, per field" — is modeled
**deeply and concretely** as the `dbColumns` fold over the `Field` structure,
all R/I. `meta.json`: `axioms: []`, `deep_model_references: []`, G-AX `skip`
(no `axiom_check.py`), `conf_skip: false`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16315`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the
`dbColumns` fold (`[f.column for f in fields]`). The ORACLE is built from **real
Django `Field` objects**: for each fuzzed (name, db_column) pair it constructs an
actual `IntegerField(db_column=...)`, runs `set_attributes_from_name(name)`, and
reads back the genuine `f.column` — i.e. it differential-tests the structure↔Field
bijection (§2) AND the patched comprehension `(f.column for f in fields)`
(`compiler.py:1728`) against the Lean fold. Stdlib + Django (already installed in
the instance image); no database connection required.
