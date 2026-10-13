# mapping.md — django__django-15732

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ce69e34bd646558bb44ea92cecfd98b345a0b3e0`, states the type
abstraction, and gives the provenance of the callees the changed operation
relies on.

Repo file under change: `django/db/backends/base/schema.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_constraint_to_remove(candidates, default_name, unique, feature_on)` | the constraint-name **selection** inside `BaseDatabaseSchemaEditor._delete_composed_index` — `django/db/backends/base/schema.py:559` (selection block at lines 565–580 pre-patch; lines 571–587 post-patch) | the modeled changed function: the disambiguating selection of the single constraint name to delete |
| `disambiguates(unique, feature_on, n_candidates)` | the post-patch guard `constraint_kwargs.get("unique") is True and constraint_names and self.connection.features.allows_multiple_constraints_on_same_fields` (gold hunk 2, `schema.py:574–578` post-patch) | pure spec: the condition under which a multi-candidate set may be narrowed to the rule's default name |
| `WrongConstraintCount` (exception) | the `raise ValueError("Found wrong number (%s) of constraints …")` at `schema.py:571–579` | user-defined stand-in for the wrong-count failure (a builtin exception in an `Exsures` crashes the Nagini translator) |
| input `candidates: List[int]` | `constraint_names` — the result of `self._constraint_names(model, columns, exclude=…, **constraint_kwargs)` (`schema.py:565`) | the discovered candidate constraint names (UNCHANGED callee; passed in as input) |
| input `default_name: int` | `str(self._unique_constraint_name(model._meta.db_table, columns, quote=False))` (gold hunk 2, post-patch `schema.py:580`) ⟶ `IndexName(table, columns, "_uniq", self._create_index_name)` (`schema.py:1574–1584` post-patch, `ddl_references.py:103` `IndexName.__str__`) | the composed rule's own default name (UNCHANGED name-generation callee; passed in as input) |
| input `unique: bool` | `constraint_kwargs.get("unique") is True` (gold hunk 2) — for `alter_unique_together` the kwargs are `{"unique": True, "primary_key": False}` (gold hunk 1, `schema.py:531`) | whether this is a uniqueness removal |
| input `feature_on: bool` | `self.connection.features.allows_multiple_constraints_on_same_fields` (`django/db/backends/base/features.py:296`, default `True`) | whether the backend permits several uniqueness constraints on the same column(s) |

The pre-patch repo symbols the change alters (for the refinement audit, not
referenced from the consumer spec view): `_delete_composed_index` pre-patch had
NO narrowing block — straight to `if len(constraint_names) != 1: raise`
(`schema.py:565–580` pre-patch). `alter_unique_together` pre-patch passed
`{"unique": True}` only (no `"primary_key": False`) (`schema.py:531` pre-patch).
`_create_unique_sql` built the name inline via a local `create_unique_name`
closure + `IndexName(...)` (`schema.py:1563,1572` pre-patch); the gold extracts
this into the new helper `_unique_constraint_name(table, columns, quote=True)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `constraint_names` — a `list[str]` of constraint-name strings | `List[int]` of distinct name identifiers | each distinct constraint-name string ↔ a distinct `int` id; list order/length preserved; `name in constraint_names` ↔ `id in ToSeq(candidates)`; `len(...)` ↔ `len(...)`; `constraint_names[0]` ↔ `candidates[0]`. Only NAME EQUALITY/MEMBERSHIP is observable in the selection — never the characters — so an id abstraction is faithful. |
| `default_name` — a `str` (the `_uniq` name) | one `int` id | the identifier of the composed rule's default name; equals the `_uniq`-suffixed candidate when present |
| `constraint_kwargs.get("unique") is True` | `unique: bool` | identity |
| `self.connection.features.allows_multiple_constraints_on_same_fields` | `feature_on: bool` | identity |
| `constraint_names = [default_name]` (the narrowing assignment) | the boolean flag `narrowed_to_default` selecting `default_name` as the unique result | a one-element list whose sole element is `default_name` ↔ returning `default_name`; observationally identical for the subsequent `len != 1` check and the `[0]` access |
| `self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))` (the side effect) | `return Result()` (the selected name) | the only observable of the side effect is WHICH name is deleted; modeled as the returned name. The SQL emission/execution is an unchanged downstream op (mapping.md §3). |

`str` constraint names are abstracted to integer identifiers because the
selection logic the patch changes inspects names only by equality and
membership; their characters never affect the decision.

## 3. Callee provenance (the unchanged operations the changed code relies on)

This bundle has **no consumed `@ContractOnly` axiom**. The changed operation —
the disambiguating selection — is modeled deeply and validated as an
**A-reference** by `axiom_check.py` (G-AX). The operations it relies on are
UNCHANGED and feed the model as inputs:

### 3.1 `self._constraint_names(...)` → `candidates` (input)
**Callee:** `BaseDatabaseSchemaEditor._constraint_names`
(`schema.py:1647`). Queries the live DB introspection for all constraint names
matching the columns and the `unique`/`primary_key`/… filters in
`constraint_kwargs`, excluding model-declared constraint/index names. UNCHANGED
by the patch. Its result (the candidate set) is the `candidates` input. The
gold's first hunk only changes the *filter* passed to it (adds
`"primary_key": False`) so PK constraints are excluded from the candidate set —
this is why the pk-field scenario discovers a single `_uniq` candidate.

### 3.2 `self._unique_constraint_name(table, columns, quote=False)` → `default_name` (input)
**Callee (new helper, but its VALUE is an unchanged computation):** post-patch
`_unique_constraint_name` (`schema.py:1606–1616`) returns
`IndexName(table, columns, "_uniq", create_unique_name)`; with `quote=False`,
`create_unique_name = self._create_index_name`, so
`str(IndexName(...)) == self._create_index_name(table, columns, "_uniq")`
(`ddl_references.py:111–112`: `IndexName.__str__` calls
`create_index_name(self.table, self.columns, self.suffix)`).
`_create_index_name(table, columns, "_uniq")` (`schema.py:1259–1289`) is the
SAME deterministic name-generation function Django has always used to name
`unique_together` constraints (table + columns + `names_digest` hash + `_uniq`
suffix; `django/db/backends/utils.py:254` `names_digest`). So `default_name` is
the exact name a `unique_together` rule generates for those columns — the basis
for recognizing the composed rule's own constraint among the candidates. This
computation is UNCHANGED behaviourally; it is merely refactored into a reusable
helper and reused with `quote=False`. Passed into the model as `default_name`.

### 3.3 A-reference soundness check (G-AX)
`axiom_check.py` re-expresses the gold patch's selection algorithm verbatim
(`gold_select`) and the model's verified impl (`model_select`) as pure
functions over `(candidates, default_name, unique, feature_on)` — the selection
needs no DB — and asserts they are observationally equal (same selected name,
same raise) on 72 boundary inputs (incl. the F2P unique-field and P2P pk-field
scenarios) plus 200 000 randomized fuzz inputs. This is the A-reference: the
deep model == the real changed selection logic. Exit 0 iff sound. stdlib-only.
