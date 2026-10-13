# mapping.md — django__django-15563

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`, states the type
abstraction, and gives the provenance of the path-classification predicate the
deep model is validated against (A-reference, G-AX).

Repo files under change:
* `django/db/models/sql/compiler.py` — `SQLUpdateCompiler.pre_sql_setup`
* `django/db/models/sql/subqueries.py` — `UpdateQuery.get_related_updates`

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assign_columns(chain)` | the `fields` / `related_ids_index` construction loop inside `SQLUpdateCompiler.pre_sql_setup` (`django/db/models/sql/compiler.py:1819`, body lines 1836-1858 post-patch) | the modeled changed function: per related-update ancestor, decide the pre-selection column that identifies its rows |
| `chain[k]` (input flag, A-reference) | `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` (`compiler.py`, the new per-`related` test in `pre_sql_setup`); `Options.get_path_to_parent` lives at `django/db/models/options.py:722` | per-target boolean: the whole path up to ancestor `k` is a primary-key chain (so its identifying value coincides with the source row's own pk) |
| `Result()[k]` (column index) | the second element of `related_ids_index.append((related, <index>))` in `pre_sql_setup`, i.e. `0` (reuse `meta.pk`) or `len(fields)` (a fresh appended column) | the column from which target `k`'s identifying values are projected (`r[index] for r in rows`) |

The two patched call-sites whose correctness the column assignment delivers
(for the refinement audit, not referenced from the consumer spec view):

* `pre_sql_setup` (`compiler.py:1851-1858` post-patch): builds
  `related_ids = collections.defaultdict(list)`, and for every fetched row
  extends `related_ids[parent]` with `r[index]` for each `(parent, index)` in
  `related_ids_index`; stores `self.query.related_ids = related_ids` (a
  `dict[Model, list]`), replacing the pre-patch flat `idents` list.
* `UpdateQuery.get_related_updates` (`subqueries.py:124`, line 137):
  `query.add_filter("pk__in", self.related_ids[model])` — each ancestor update
  is filtered by ITS column's values, replacing the pre-patch
  `self.related_ids` (the single flat list).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the ordered list `self.query.related_updates` (a `dict[Model, list]`, iterated in insertion order) of ancestor targets to update | the index domain `0 .. len(chain)-1` | target `k` ↔ the `k`-th key of `related_updates` |
| `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` — a `bool` | `chain[k] ∈ {0,1}` (`int`) | `True` ↔ `1`, `False` ↔ `0` |
| the column index recorded in `related_ids_index` (`0` or `len(fields)`) | `Result()[k]` (`int`) | identity on the column index |
| `related_ids: dict[Model, list[int]]` (post-patch); the per-row projection `r[index]` | not modeled (a pure list-indexing read at the assigned column) | the projection step `related_ids[parent].extend(r[index] ...)` is a type-trivial `r[col]` read; its only behavioural content — *which* column — is exactly `Result()[k]` (refinement.md step P) |

`dict`-keyed `related_ids` is abstracted to a per-target column index because
the only behaviour the F2P tests can observe is *which source column's values
constrain each ancestor's UPDATE*; the dict is just the carrier mapping each
ancestor to its column's projected values.

## 3. The A-reference (checked by G-AX / axiom_check.py)

### 3.1 `chain[k]` ↔ `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))`

**Callee:** `Options.get_path_to_parent(parent)`
(`django/db/models/options.py:722`) returns the list of `PathInfo` hops from
the model up to `parent`; each `PathInfo.join_field` is the link field used for
that hop, and `join_field.primary_key` is `True` iff that link is itself the
primary key of the descendant (the canonical MTI `*_ptr` parent link that IS
the child's pk). The conjunction over the whole path is `True` iff every hop is
a primary-key link — i.e. the ancestor's identifying value equals the source
row's own primary key, so column 0 suffices; `False` iff some hop is a
non-primary-key parent link (a second/sibling base in a diamond MTI), so the
ancestor needs its OWN identifying column.

This predicate is an UNCHANGED Django primitive that the patched
`pre_sql_setup` *calls*; the model treats its value as the input flag `chain[k]`
and models the column-assignment logic deeply. It is therefore an
**A-reference**, validated == the real callee out of band, NOT a consumed
axiom.

**Soundness check (G-AX):** `axiom_check.py` builds the real concrete-MTI tree
the F2P tests exercise (`Politician`, `Congressman(Person, Politician)`,
`Senator(Congressman)`), and for each F2P update scenario
(`Congressman.objects.update(title=...)`, `Senator.objects.update(title=...)`)
drives the REAL `UpdateQuery.add_update_values` to populate `related_updates`,
then evaluates the REAL predicate
`all(p.join_field.primary_key for p in meta.get_path_to_parent(rel))` per
target. It reproduces the GOLD `fields`/`related_ids_index` column assignment
directly from those real predicate values and asserts it equals
`assign_columns(flags)` **at the index level**
(`model_index[k] == 0 ⇔ real_is_pk_chain[k]`; the predicate under test is not
applied to both sides of the checked equality — no double mask), plus that
non-chain targets occupy distinct positive columns. It enumerates both F2P
scenarios and fails loud if either is skipped or yields no related-update
target. 20 000 random flag vectors additionally pin the deep model ==
the gold construction. Verified end-to-end against real Django 4.x: the
title-bearing `Politician` ancestor is reached through a NON-primary-key link
(flag 0) in both scenarios, so it correctly receives its own positive column.
Docs: Django MTI parent links / `Options.get_path_to_parent`.
