# mapping.md — django__django-15278

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0ab58c120939093fea90822f376e1866fc714d1f`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/backends/sqlite3/schema.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `add_column(col)` | `DatabaseSchemaEditor.add_field(self, model, field)` — `django/db/backends/sqlite3/schema.py:325` (predicate at line 330) | the modeled changed function (the in-place-append-vs-full-rebuild routing decision) |
| `ColumnSpec.primary_key` | `field.primary_key` (model `Field` attribute) | bool: column is a primary key |
| `ColumnSpec.unique` | `field.unique` (model `Field` attribute; `OneToOneField` forces `unique=True`, `related.py:1088`) | bool: column carries a uniqueness constraint |
| `ColumnSpec.nullable` | `field.null` (model `Field` attribute) | bool: column is nullable |
| `has_effective_default(col)` *(axiom — A-consumed)* | `self.effective_default(field) is not None` — `effective_default` at `django/db/backends/base/schema.py:332` (delegates to static `_effective_default`, line 308) | unchanged backend observation: whether the field has an effective DB default |
| `needs_full_rebuild(col)` | the gold `if (...)` predicate at `sqlite3/schema.py:325` post-patch | pure spec: the routing predicate |
| return `1` | `self._remake_table(model, create_field=field)` — `sqlite3/schema.py:145` | full-rebuild route (rebuilds the whole table; realises any constraint) |
| return `0` | `super().add_field(model, field)` — base `add_field`, `base/schema.py:491` (emits `ALTER TABLE … ADD COLUMN`) | in-place append route |

The pre-patch predicate the change extends (for the refinement audit, not
referenced from the consumer spec view): `if not field.null or
self.effective_default(field) is not None:` (`sqlite3/schema.py:330` pre-patch).
The gold patch prepends the two disjuncts `field.primary_key or field.unique`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a model `Field` object (rich: dozens of attributes, methods, DB params) | `ColumnSpec` carrying only the three touched boolean attributes | `field.primary_key` ↔ `col.primary_key`; `field.unique` ↔ `col.unique`; `field.null` ↔ `col.nullable`. No other field attribute is read by the changed predicate, so none is modelled. |
| the action `self._remake_table(model, create_field=field)` | the route discriminator `1` | the patch changes only WHICH branch is taken, not what either branch does; `_remake_table` is unchanged, so it is abstracted to its branch label. |
| the action `super().add_field(model, field)` | the route discriminator `0` | likewise unchanged; abstracted to its branch label. The in-place `ALTER TABLE … ADD COLUMN` path that fails on SQLite for key/unique/not-null/default columns. |
| `self.effective_default(field) is not None` | `has_effective_default(col): bool` (axiom) | the truth of the `is not None` test ↔ the axiom's boolean result (see §3). |

Modelling the route as an `int` discriminator (1 = rebuild, 0 = append) makes
the routing decision — the only thing the patch changes — directly observable
in the postcondition, without modelling the (unchanged, side-effecting) bodies
of either branch.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `has_effective_default` ↔ `effective_default(field) is not None` (A-consumed)
**Callee:** `BaseDatabaseSchemaEditor.effective_default(self, field)`
(`django/db/backends/base/schema.py:332`), which returns
`field.get_db_prep_save(self._effective_default(field), self.connection)`. The
static `_effective_default` (line 308) returns the field's default when it has
one (`field.has_default()`), an empty string/bytes for a non-null blank
empty-strings field, a timestamp for `auto_now`/`auto_now_add`, and otherwise
`None`. The predicate consumes only the boolean `effective_default(field) is not
None`.

**Axiom contract (the weakest):** `has_effective_default` carries **no
`Ensures`** — only a fractional read permission on the column flags. The proof
therefore never assumes any particular value; it only assumes the observation is
a pure boolean read of the column (so re-evaluating it in the routing predicate
and in `needs_full_rebuild` is consistent). This cannot over-claim the real
callee: there is nothing to over-claim.

**Why it is an UNCHANGED callee (so a legitimate axiom):** the
`self.effective_default(field) is not None` clause is byte-identical in the
pre- and post-patch predicate (`sqlite3/schema.py:330`); the patch adds only the
`field.primary_key or field.unique` disjuncts. So `effective_default` is a
genuine kind-A callee, not the operation under change.

**Soundness check (G-AX):** `axiom_check.py` configures Django against an
in-memory SQLite database and, over 14 real field witnesses — including the
discriminating nullable `OneToOneField` (`unique=True, null=True,
primary_key=False`, no default), plain nullable scalars/FK, non-null,
unique-scalar, primary-key, defaulted, and blank-non-null fields — asserts:
(1) `editor.effective_default(field) is not None` is deterministic across
re-evaluation and does not mutate the field's routing flags (so the @Pure,
no-`Ensures` modelling is sound); and (2) the real post-patch routing predicate
`field.primary_key or field.unique or not field.null or
self.effective_default(field) is not None` equals the model's
`needs_full_rebuild` over the four modelled signals. It imports only Django (the
package under test) and the standard library. Exit 0 iff sound.

### 3.2 No flag dependency
The predicate reads plain boolean field attributes and one boolean default
observation; there is no library call whose default flags (à la
`html.escape(quote=True)`) affect the result. The only configuration G-AX pins
is the backend (SQLite), which is the backend the patch and the F2P test target.
