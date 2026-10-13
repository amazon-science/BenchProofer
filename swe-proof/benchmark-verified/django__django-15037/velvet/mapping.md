# mapping.md — django__django-15037

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = dab48b7482295956973879d15bfd4d3bb0718772`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one outside callee the modeled decision consults.

Repo file under change:
`django/core/management/commands/inspectdb.py` (the `handle_inspection` loop body
inside `Command.handle`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `qualifyReference (isUniqueRef) (refColumn) (idKey)` | the relation branch `if is_relation:` of the per-column loop — `inspectdb.py:118-126` (the `rel_type`/`extra_params` decision the gold hunk edits) | the modeled changed decision: whether to attach an explicit target-column qualifier to a generated reference field, and which column it names |
| `targetQualifier` *(pure spec)* | the post-patch decision `extra_params['to_field'] = ref_db_column` guarded by `rel_type == 'ForeignKey'` and `ref_pk_column and ref_pk_column != ref_db_column` — `inspectdb.py:120-128` post-patch | pure spec: the explicit target-column qualifier as a structural function of the three inputs |
| `idKey` *(free input — A-reference)* | `connection.introspection.get_primary_key_column(cursor, ref_db_table)` — base impl `django/db/backends/base/introspection.py:166-173`; sqlite3 impl `django/db/backends/sqlite3/introspection.py:202-210` | UNCHANGED introspection callee that yields the referenced table's primary-key column name, or `None` when the table has no single-column PK. Taken as the free input `idKey`; validated == real callee behaviour by axiom_check.py (G-AX) |

Inputs decoded from the loop's local state (refinement audit; provenance only):

- `isUniqueRef` ↔ the pre-patch `rel_type` decision
  `extra_params.pop('unique', False) or extra_params.get('primary_key')`
  (`inspectdb.py:119`): `True` ⇒ `OneToOneField` (identity reference),
  `False` ⇒ `ForeignKey` (plain many-to-one). The gold patch attaches the
  qualifier only on the `ForeignKey` branch — i.e. only when `isUniqueRef` is
  `False`.
- `refColumn` ↔ `ref_db_column` = `relations[column_name][0]` post-patch
  (`inspectdb.py:119` post-patch unpacks `ref_db_column, ref_db_table =
  relations[column_name]`): the actual referenced column of the target table.
- `idKey` ↔ `ref_pk_column = get_primary_key_column(cursor, ref_db_table)`
  (`inspectdb.py:123` post-patch): the target table's primary-key column, or
  `None`.

The `rel_to` rewrite in the gold hunk (`relations[column_name][1]` → the
unpacked `ref_db_table`) is a **behaviour-preserving local-variable extraction**
(same value, new name); it produces no observable change and is not modeled
(refinement.md §B, tag I).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a column name `str` (`ref_db_column`, the PK column name) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty str `""` ↔ `[]`; name equality `a == b` ↔ `a = b` |
| `get_primary_key_column(...)` result: a column-name `str` or `None` | `Option (List Char)` | `None` ↔ `none`; a name `s` ↔ `some s.toList`. A table with no single-column PK gives `None`; modeled `none`. (An empty-string name, never produced by the real callee, is additionally treated as "no key" — see `idKey` non-empty guard — so the model is conservative.) |
| the `rel_type == 'ForeignKey'` vs `'OneToOneField'` decision | `Bool` `isUniqueRef` | `True` (one-to-one) ↔ `isUniqueRef = true`; `False` (plain FK) ↔ `isUniqueRef = false` |
| `extra_params['to_field'] = ref_db_column` set / not set | `Option (List Char)` `out` | qualifier attached with value `c` ↔ `some c.toList`; no `to_field` key set ↔ `none` |

Lean `List Char` indexing/equality is total and sound; the carrier is
`List Char` because the modeled decision compares two column **names** for
equality and emits one of them.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `idKey` ↔ `get_primary_key_column` (A-reference)
**Callee:** `connection.introspection.get_primary_key_column(cursor, table)`.
It is **UNCHANGED** by the patch and is *newly consulted* by the fix to learn the
referenced table's primary-key column. The decision treats its result as the
free input `idKey`: `None` ⇒ `none`, a column name ⇒ `some name`. The relied-on
reference properties:

  - (R1) the callee returns the name of the table's single-column primary key
    when one exists, and `None` when it does not (base impl iterates
    `get_constraints` for the `primary_key` constraint and returns
    `constraint['columns'][0]`; sqlite3 impl scans `PRAGMA table_info` for the
    `pk` flag);
  - (R2) the returned value, when present, is a non-empty column-name string —
    so the model's "present, non-empty" recognition matches the real callee
    (the real callee never returns an empty string).

**Soundness check (G-AX):** `axiom_check.py` stands up an in-memory sqlite
backend, creates tables whose primary key is `id`, a named non-`id` column, or
absent, and asserts `get_primary_key_column` returns exactly that column name
(or `None`) — over the boundary tables plus randomized fuzz schemas. It also
re-derives the gold decision `to_field = ref_db_column iff (ForeignKey and
ref_pk_column and ref_pk_column != ref_db_column)` from the real callee's output
and checks it equals `targetQualifier`. Imports only stdlib + `django.db`. Exit
0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15037`**. The R/I shadow
it builds transliterates `targetQualifier` to Python over the real `str`/`None`
carriers (per the §2 bijection) and diffs it against the gold patch's literal
decision expression (the `to_field` assignment guarded by the `ForeignKey`
branch and `ref_pk_column and ref_pk_column != ref_db_column`) over ≥10⁵ fuzzed
`(isUniqueRef, refColumn, idKey)` triples. `idKey` is the A-reference free input;
the gold decision reads it as the real callee's already-produced value, so this
gate isolates the R/I decision legs (the branch + equality), with G-AX carrying
the callee itself.
