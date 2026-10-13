# mapping.md — django__django-11299

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6866c91b638de5368c18713fa851bfe56253ea55`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/models/sql/query.py`.

## 1. The behavior being modeled

`Query._add_q` (`django/db/models/sql/query.py:1327`) recursively walks a
`Q`-object (a tree of `WhereNode`/`Node` group children and leaf filter
expressions), assembling a `WhereNode`. Each leaf is turned into a column
reference whose **form** depends on a Boolean parameter `simple_col`:

- `_get_col(target, field, alias, simple_col)` (`query.py:71`) returns a
  `SimpleCol(target, field)` when `simple_col` is truthy, else
  `target.get_col(alias, field)` (a table-qualified `Col`).
- A leaf is processed by `build_filter(..., simple_col=simple_col)`
  (`query.py:1344-1347`), which forwards `simple_col` down to `_get_col`.
- A **group** child (`isinstance(child, Node)`) is processed by a RECURSIVE
  call to `_add_q` (`query.py:1339-1341`).

`build_where` (`query.py:1324`) is the public entry that assembles a check
expression for a constraint; it calls `_add_q(..., simple_col=True)`, i.e. it
requests the **bare / unqualified** (`SimpleCol`) form for the whole tree
(table-qualified names are invalid inside a `CHECK (...)` clause that is moved
between tables during a table rebuild).

The defect: the recursive `_add_q` call on a group child does NOT forward
`simple_col`, so it falls back to the parameter default `simple_col=False`
(`query.py:1329`). Consequently leaves nested **inside a group** are given the
table-qualified `Col` form even when the top-level call requested `SimpleCol`.
The single-line change forwards `simple_col` into the recursive call.

The whole behavior reduces to: **a Boolean selector chosen at the top of the
walk must reach every leaf at every nesting depth.** Everything else about a
leaf — which field, alias, lookup, the join setup, negation bookkeeping,
`JoinPromoter` vote tallying — is UNCHANGED by the patch and does not affect
WHICH column form a leaf receives; the patch touches only the propagation of
`simple_col` into the recursive branch.

## 2. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assignColumnForms (bare : Bool) (conds : List Cond)` | `Query._add_q(self, q_object, …, simple_col)` — `query.py:1327` (the `for child in q_object.children` walk, lines 1337-1352) | the modeled changed function: the recursive condition-tree walk that assigns each leaf a column-reference form |
| `bare : Bool` | the `simple_col` parameter of `_add_q` / `build_filter` (`query.py:1329`, `1185`) | the column-form selector threaded through the walk |
| `Cond` (`atom` / `group`) | a `Q`-object child: a leaf filter expression (tuple), or a nested `Node` group (`query.py:1337-1338` `isinstance(child, Node)`) | the input condition tree (the top-level object is a group = `q_object.children`) |
| `ResolvedCond` (`atom ColForm` / `group …`) | the assembled `WhereNode` tree, each leaf carrying its column form (`SimpleCol` vs `Col`) | the output: structure preserved, each leaf tagged with its column form |
| `ColForm.bare` | `SimpleCol(target, field)` — `_get_col` `query.py:72-73` under `simple_col` truthy | the unqualified column form |
| `ColForm.qualified` | `target.get_col(alias, field)` — `_get_col` `query.py:74` under `simple_col` falsy | the table-qualified column form |
| `formOf (bare)` | `_get_col(target, field, alias, simple_col)`'s `simple_col`-branch selection (`query.py:71-74`) | maps the selector to the resulting column form for one leaf |
| `columnForm` / `columnForms` *(deep model)* | the recursive assembly itself: a group ↦ recurse on its children with the SAME selector; a leaf ↦ `_get_col(..., simple_col)` | pure spec: the column-form assignment for one condition / a forest |

## 3. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the repo behavior.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Q`-object / `Node` group with children | `Cond.group (List Cond)` | a `Node` with `node.children = [c₀, c₁, …]` ↔ `Cond.group [⟦c₀⟧, ⟦c₁⟧, …]`; child order preserved |
| a leaf filter expression (a non-`Node` child, e.g. `('num__gt', 2)`) | `Cond.atom` | every leaf abstracts to the same `atom`: the patch does not distinguish leaves by content — only the column FORM a leaf receives changes, and that is governed solely by the propagated selector. The leaf's field/lookup/value is UNCHANGED machinery (folded out). |
| `simple_col` parameter (a Python truth value) | `bare : Bool` | `True` ↔ `true`, `False` ↔ `false` |
| `_get_col(...)` returning `SimpleCol` | `ColForm.bare` | identity of the column-reference class: `SimpleCol` instance ↔ `bare` |
| `_get_col(...)` returning `target.get_col(alias, field)` (a `Col`) | `ColForm.qualified` | identity of the column-reference class: `Col` instance ↔ `qualified` |
| the assembled `WhereNode` subtree at a leaf | `ResolvedCond.atom <ColForm>` | observable content = which column class the leaf's lookup `lhs` is (`SimpleCol` vs `Col`) — exactly what the F2P test asserts via `assertIsInstance(..., SimpleCol)` |
| a `WhereNode` group | `ResolvedCond.group (List ResolvedCond)` | grouping structure preserved, children recursively bridged |

The F2P test `queries.test_query.TestQuery.test_simplecol_query` constructs
`Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id'))` (an OR of an AND-group
and a leaf) and asserts via `build_where` (which passes `simple_col=True`) that
the leaves nested inside the AND-group are `SimpleCol` — precisely the
nested-leaf clause the deep model pins to `bare`.

## 4. Callee provenance (kind-A)

**One A-reference; no consumed axioms.**

| kind | model symbol | real callee (file:line @ base_commit) | encoded property | flag dep | checked by |
|---|---|---|---|---|---|
| **A-reference** | `formOf` (and the per-leaf column-form choice in `columnForm`) | `django.db.models.sql.query._get_col(target, field, alias, simple_col)` — `query.py:71-74` | `simple_col` truthy → `SimpleCol` (bare/unqualified column SQL) ↔ `ColForm.bare`; `simple_col` falsy → `Col` (alias-qualified column SQL) ↔ `ColForm.qualified` | the `simple_col` selector — both values fuzzed/exercised | `axiom_check.py` (G-AX): `formOf` deep model == real `_get_col` on both selector values |

`_get_col` is the column-reference machinery that the changed function
`Query._add_q` CALLS (transitively, via `build_filter`) but **does not change** —
the patch only forwards the existing `simple_col` selector into the recursive
branch. Per SPEC_GUIDE §3, a callee whose behavior is modeled **deeply and
concretely** (here `columnForm`/`columnForms`/`formOf` over the
`Cond`/`ResolvedCond`/`ColForm` carriers) is an **A-reference**: its fidelity is
validated **== the real callee** by G-AX, not consumed as an opaque `ensures`
(the `escapedSeq == html.escape` pattern of the exemplar). It is therefore NOT a
dead/consumed axiom.

The rest of the per-leaf resolution machinery (`solve_lookup_type`,
`setup_joins`, `build_lookup`, `JoinPromoter`) is UNCHANGED by the patch, does
not influence which column form a leaf gets, and is abstracted away (a leaf ↦
`atom`); the **propagation** of the selector through the tree is R/I structure,
differential-tested by G-CONF.

## 5. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`11299`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`columnForm`/`columnForms`/`formOf` to Python and differential-tests it against
an ORACLE that transliterates the **patched** `_add_q` recursion (the column-form
selector forwarded into the recursive branch; the unchanged per-leaf machinery
folded to "this leaf receives `_get_col(..., simple_col)`"). G-CONF tests the
R/I **propagation** structure and does not itself invoke the real callee; the
A-reference column-form bijection (`formOf` == `_get_col`) is validated
separately by G-AX (§4). `conf_skip=false` (the impl region is entirely R/I
structure: there is no all-A-tagged region).
