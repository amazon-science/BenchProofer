# mapping.md — django__django-11299

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6866c91b638de5368c18713fa851bfe56253ea55`, states the type
abstraction, and gives the provenance of the deep model (validated against the
real callee by axiom_check.py / G-AX).

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compile_children(head, plain)` | `Query._add_q(q_object, used_aliases, …, simple_col)` — `django/db/models/sql/query.py:1327` (the changed recursive child loop, body lines 1337–1353; the edited recursive call lines 1339–1341) | the modeled changed function: the recursive compiler that walks a condition tree's children and forwards the plain-column mode into nested groups |
| `plain` parameter | `simple_col` parameter of `_add_q` / `build_filter` (`query.py:1329`, `1185`) | the plain-column mode chosen once at the root; `Query.build_where` (`query.py:1324`) calls `_add_q(..., simple_col=True)` |
| `QNode` (`kind`, `inner`, `nxt`) | a `Q`/`WhereNode` tree node (`django.utils.tree.Node`: `connector`, `children`; `query.py:1337` iterates `q_object.children`) | the condition tree; a child is a `Node` (group → recurse) or a leaf comparison (→ `build_filter`) |
| `q_kind(n) == 0` (leaf) / `== 1` (group) | `isinstance(child, Node)` test (`query.py:1338`): False → leaf (`build_filter`, line 1344), True → group (recursive `_add_q`, line 1339) | leaf vs group dispatch |
| `leaf_modes(head, plain)` *(deep model — A-reference)* | the per-leaf column-form result of the whole `_add_q` traversal, observed via `SimpleCol` vs `Col` at each leaf lookup's `lhs`/`rhs` (`query.py:1274,1278,1300` via `_get_col`, `query.py:71`) | pure spec: the flag (True = `SimpleCol`) of every leaf in traversal order; validated `leaf_modes == build_where` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `compile_children`'s per-leaf output `bool` | `_get_col(target, field, alias, simple_col)` returning `SimpleCol(target, field)` when `simple_col` else `target.get_col(alias, field)` (`query.py:71–74`; `SimpleCol`/`Col` at `expressions.py:742`/`711`) | True ⟺ the bare table-name-free `SimpleCol`; False ⟺ the fully-qualified `Col` |

The pre-patch defect site (for the refinement audit): the recursive call at
`query.py:1339–1341` passes only `(child, used_aliases, branch_negated,
current_negated, allow_joins, split_subq)` and omits `simple_col`, so the
recursive `_add_q` receives `simple_col=False` (its default, `query.py:1329`).
Every leaf reached through a nested group therefore takes the `Col` branch of
`_get_col`. The gold patch appends `simple_col` to that call.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Q`/`WhereNode` tree (`Node.children`, a list of `Node`-or-leaf) | recursive `QNode` in sibling/inner linked form: `nxt` = next sibling in `children`, `inner` = head of a group child's own `children` | a child list `[c0, c1, …]` ↔ the `nxt`-chain `head → c1node → …`; a group child ↔ `kind==1` with `inner` = head of that group's `children`; a leaf child ↔ `kind==0` |
| `simple_col: bool` | `plain: bool` | identity |
| `_get_col(...) is SimpleCol` vs `Col` | `bool` flag (True = plain/`SimpleCol`) | `isinstance(col, SimpleCol)` ↔ flag True |
| the compiled `WhereNode` result tree | `List[bool]` of per-leaf flags in left-to-right traversal order | the test inspects each leaf lookup's `lhs`/`rhs` column class; only the column FORM (SimpleCol vs Col) at each leaf is observed, so the result is abstracted to the ordered flag list |

The other arguments threaded through `_add_q`/`build_filter`
(`used_aliases`, `branch_negated`, `current_negated`, `allow_joins`,
`split_subq`, join promotion) are orthogonal to the column-form decision the
F2P test observes and to the bug; they are omitted from the carrier (the model
keeps only the touched aspect — the plain-column mode and its propagation).
`build_filter`'s column-construction step (`_get_col`) is the single place
`simple_col` is consumed for a leaf; the model collapses a leaf to its one flag.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `leaf_modes` deep model ↔ `Query.build_where` (the real `_add_q`)
The changed traversal is modelled **deeply** by the `@Pure` fold `leaf_modes`
(with the recursive `q_pred` predicate and the verified `compile_children`);
there is **no consumed `@ContractOnly` axiom**. `leaf_modes(tree, plain)`
records, in traversal order, one flag per leaf, every flag equal to the top
`plain` mode regardless of nesting depth — because the mode is forwarded
unchanged through every descent into a group (`leaf_modes(head.inner, plain)`).

Real callee (post-patch source, `django/db/models/sql/query.py:1337–1353`):

```python
for child in q_object.children:
    if isinstance(child, Node):
        child_clause, needed_inner = self._add_q(
            child, used_aliases, branch_negated,
            current_negated, allow_joins, split_subq, simple_col)   # <- simple_col forwarded
        ...
    else:
        child_clause, needed_inner = self.build_filter(
            child, ..., simple_col=simple_col)                      # leaf uses current mode
```

with `_get_col` (`query.py:71`):
```python
def _get_col(target, field, alias, simple_col):
    if simple_col:
        return SimpleCol(target, field)   # bare column, no table name
    return target.get_col(alias, field)   # Col, fully qualified
```

`Query.build_where` (`query.py:1324`) sets the root mode `simple_col=True`, so
post-patch every leaf at every depth resolves to `SimpleCol` — i.e.
`leaf_modes(tree, True)` is all-True. Pre-patch the recursive call omits
`simple_col`, so nested leaves (depth ≥ 1) take the `Col` branch.

**Soundness check (G-AX):** `axiom_check.py` builds 8 condition trees of
varying shape and nesting depth (the issue's OR-of-AND, deeper `AND(OR,OR)`,
triple nesting, negated groups, F-expressions on both sides), runs the REAL
`Query.build_where`, walks the compiled `WhereNode` tree, and asserts every leaf
column is `SimpleCol` — i.e. the observed flag sequence equals
`leaf_modes(tree, True)` (all True) at every depth. It additionally reproduces
the pre-patch `_add_q` (mode not forwarded) and asserts it yields a nested `Col`
leaf — the divergence the frozen postcondition forbids and `model_prepatch.py`
predicts. Verified here against the real Django 3.0-dev: on the patched repo all
26 leaves over the 8 trees are `SimpleCol`; on the unpatched repo the OR-of-AND
tree yields `[False, False, True, True]` (nested-AND leaves are `Col`). Imports
are stdlib + Django (the repo under test); exit 0 iff sound.
