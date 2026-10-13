# mapping.md — django__django-11299

## Symbol binding (file:line @ base_commit 6866c91b638de5368c18713fa851bfe56253ea55)

- Modeled function: `Query._add_q`
  — `django/db/models/sql/query.py:1327-1353` (recursive Q-tree walk).
- Entry point that fixes the global flag: `Query.build_where`
  — `django/db/models/sql/query.py:1324-1325` calls
    `self._add_q(q_object, used_aliases=set(), allow_joins=False, simple_col=True)[0]`.
- Per-leaf column constructor: `_get_col`
  — `django/db/models/sql/query.py:71-...` → `SimpleCol(target, field)` when
    `simple_col` else `Col(alias, target, field)`.
- Column classes: `Col` / `SimpleCol`
  — `django/db/models/expressions.py:711` / `:742`. `Col.as_sql` emits
    `"alias"."column"` (table-qualified); `SimpleCol.as_sql` emits `"column"`
    (bare). `SimpleCol` exists specifically to avoid the table prefix in check
    constraints.
- Leaf lowering: `Query.build_filter`
  — `django/db/models/sql/query.py:~1200-1302`, takes a `simple_col` kwarg and
    passes it to `_get_col`.

## The fix
`_add_q` recurses on nested `Node` children (`isinstance(child, Node)`). At
base_commit the recursive call (line 1339-1341) omits the `simple_col` argument,
so it defaults to `False` for every sub-node — leaves below the first nesting
level are lowered to table-qualified `Col` even when the top-level call asked for
`SimpleCol`. The gold patch threads `simple_col` into that recursive call so the
flag is GLOBAL: every leaf at every depth uses the same form.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Lean | Python |
|---|---|
| `QTree.leaf field` | a single field lookup, e.g. `Q(num__gt=2)` (a `(key,val)` child) |
| `QTree.node children` | a `Q(...)`/`Node` grouping with those children |
| `bare : Bool` | the global `simple_col` flag (`build_where` fixes it `True`) |
| `ColTree.col field true` | a leaf lookup whose lhs is a `SimpleCol` (bare) |
| `ColTree.col field false` | a leaf lookup whose lhs is a `Col` (table-qualified) |
| `ColTree.node children` | a `WhereNode` grouping the lowered children |
| `buildLeaf bare field` | `_get_col(target, field, alias, simple_col=bare)` |
| `result = expectedCol bare q` | every leaf lowered with the SAME global form |

Abstraction note: the model ignores join setup, lookup classes, negation
bookkeeping, and join promotion — none of which the fix touches. The single
observable the fix governs is the per-leaf column FORM (SimpleCol vs Col) as a
function of the global flag and nesting depth; that is exactly what `QTree →
ColTree` captures. Connector (AND/OR) and negation are modeled as opaque grouping
(`node`) because they do not affect the column form.

## Callee provenance + flag deps
- `_get_col` / `SimpleCol` / `Col`: UNCHANGED by the patch; modeled deeply as
  `buildLeaf` (A-reference, but the proof needs no axiom — see refinement.md /
  axiom_check.py skip).
- Flag dependency: the column form is governed solely by `simple_col`; `Col`
  additionally needs an `alias`, `SimpleCol` does not — irrelevant to the form
  decision, so dropped from the model.

## G-CONF fuzz seed
`SEED = 11299`, `N = 100000`. Generator: random nested `Q` trees over the
non-relational fields {num, name} of a synthetic model, with AND/OR connectors
and random negation, depth up to 5. Driver runs the REAL patched
`Query.build_where` and walks the resulting `WhereNode` collecting each leaf's
column form in order; shadow predicts all-bare (the impl threads the flag).
Verified: FAIL 100000/100000 at base_commit, OK 0/100000 with gold applied.
