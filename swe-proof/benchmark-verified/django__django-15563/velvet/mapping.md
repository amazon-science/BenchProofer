# mapping.md — django__django-15563

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo files under change:
`django/db/models/sql/compiler.py`, `django/db/models/sql/subqueries.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `parentFilterIds (parents, rows)` | `SQLUpdateCompiler.pre_sql_setup` — `django/db/models/sql/compiler.py:1819` (changed body lines 1839, 1869-1875), together with the per-ancestor consumption in `UpdateQuery.get_related_updates` — `django/db/models/sql/subqueries.py:124` (changed line 137) | the modeled changed behavior: per-ancestor identity-value routing for a multi-table update |
| `Parent.sharesChildPk` *(free input)* | `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` — `compiler.py:1842` (post-patch) | whether a primary-key chain reaches the ancestor from the child, so the child's identity value also serves as the ancestor's |
| `rows : List (List Int)` *(free input)* | the fetched rows of the pre-select `for rows in query.get_compiler(self.using).execute_sql(MULTI)` — `compiler.py:1871` | the identity tuples fetched for the matched children; one inner list = one fetched row, one column = one selected identity field |
| `stepCol` *(deep model)* | the `for related in self.query.related_updates:` column-assignment loop building `fields` / `related_ids_index` — `compiler.py:1840-1875` (post-patch) | pure spec: thread the next free column, assigning column 0 to a shared-pk ancestor and a fresh appended column otherwise |
| `assignedColumns` *(deep model)* | the completed `related_ids_index` (the `(related, index)` pairs) — `compiler.py:1875` | pure spec: the fetched-row column index each ancestor's filter values are drawn from |
| `idColumn rows idx` *(deep model)* | `related_ids[parent].extend(r[index] for r in rows)` then `query.add_filter("pk__in", self.related_ids[model])` — `compiler.py:1874`, `subqueries.py:137` (post-patch) | pure spec: the filter id list for one ancestor = column `idx` of every fetched row |

The pre-patch repo behavior the change replaces (refinement audit only, not in
the consumer spec view): `query.add_fields([query.get_meta().pk.name])`
(`compiler.py:1839`) selecting only the child identity, `idents` a single flat
list (`compiler.py:1869-1872`), `self.query.related_ids = idents`
(`compiler.py:1875`), and `query.add_filter("pk__in", self.related_ids)`
(`subqueries.py:137`) — every ancestor filtered on the child identity column.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ordered ancestors needing a coalesced update (`self.query.related_updates`, a dict iterated in insertion order) | `List Parent` | one `Parent` per ancestor, in iteration order; `len(related_updates)` ↔ `parents.length` |
| `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` (a `bool`) | `Parent.sharesChildPk : Bool` | identity on `Bool`; `True` ↔ `true` |
| one fetched row tuple `r` from the MULTI cursor | `List Int` | `r[index]` ↔ `row[index]!`; a row has one column per entry of `fields` |
| the whole fetched block(s) `rows` | `List (List Int)` | row order ↔ list order; the value domain is identity (`int` ↔ `Int`) |
| a column index into `fields` | `Nat` | identity; column 0 ↔ `0` (the child identity), appended columns ↔ `1,2,…` |
| `related_ids[parent]` filter list (`subqueries.py:137`) | `idColumn rows idx : List Int` | the per-ancestor `pk__in` value list; element order = fetched-row order |

The result of `parentFilterIds` is the list, one per ancestor in order, of the
`pk__in` value list each ancestor's update query is filtered on — i.e. what
`get_related_updates` reads from `self.related_ids[model]` for each ancestor.

## 3. Callee provenance / free inputs (no consumed axioms; no G-AX)

There are **no axiomatized callees** in this bundle and no deep-model reference
to a real callee, so `axiom_check.py` is absent and G-AX is **skip**.

- `sharesChildPk` is a **free input**, not an axiom. The patch routes on the
  result of `all(path.join_field.primary_key for path in
  meta.get_path_to_parent(related))`. That predicate (path resolution +
  `join_field.primary_key`) is UNCHANGED by the patch; only HOW its boolean is
  threaded into the column assignment changes. The spec makes no behavioural
  claim about it and holds for EVERY value of it, so there is nothing to check
  against a real callee. (Per the worker prompt's "free input" pattern, cf.
  django-11820's schema accessors.)
- `rows` is a **free input**: the fetched identity tuples. The SQL pre-select
  (`execute_sql(MULTI)`) that produces them is unchanged; what the patch edits
  is which COLUMN of each row each ancestor reads, which is exactly the modeled
  routing. The spec holds for every fetched block.

**Flag dependency:** the only configuration that matters — whether a pk chain
reaches the ancestor — IS the `sharesChildPk` input; G-CONF fuzzes both values
and the two F2P scenarios (both non-shared) are in the boundary set.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15563`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `stepCol`/`assignedColumns`/`idColumn` (R/I-tagged ops) to Python
and uses the SAME free `sharesChildPk` flags and fetched `rows` as the oracle
(the gold-patched routing transcribed verbatim). No axiom model is involved.
