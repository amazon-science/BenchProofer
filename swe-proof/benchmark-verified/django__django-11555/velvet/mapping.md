# mapping.md — django__django-11555

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8dd5877f58f84f2b11126afbd0813e24545919ed`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of each modeled/free callee.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `expandOrdering (items) (resolve)` | the default-ordering expansion loop inside `SQLCompiler.find_ordering_name` — `django/db/models/sql/compiler.py:723–726` (the `results = []` / `for item in opts.ordering: results.extend(...)` / `return results` block) | the modeled changed code: builds the expanded list of resolved ordering entries from a model's default ordering specification |
| `Item` (`expr` / `name`) | one element of `opts.ordering` — either an `OrderBy` (an order *expression*; `django.db.models.expressions.OrderBy`) or a `str` field-name lookup (`'field1__…__fieldN'`) | the kind of a single default-ordering element |
| `Pair := Expr × Bool` | one resolved ordering entry `(OrderBy(...), False)` produced by `find_ordering_name` (`compiler.py:729`) | a resolved ordering entry: the order expression + its trailing `default_order_applied=False` flag |
| `resolve : Name → List Pair` *(free input — not an axiom)* | the recursive call `self.find_ordering_name(item, opts, alias, order, already_seen)` applied to a *name* item (`compiler.py:725–726`) | the UNCHANGED recursive resolution of a field-name lookup into its resolved ordering entries; modeled as an arbitrary total function (no contract owed) |
| `itemContribution` / `expandItems` *(deep model)* | the per-iteration body + the accumulated `results` of the loop | pure spec: what one item contributes, and the in-order concatenation of all contributions |

The patch inserts, as the first statement of the loop body, a guard that routes
an order-expression item straight into the result and skips the recursive
resolution (`compiler.py:725–727` post-patch):

```python
results = []
for item in opts.ordering:
    if isinstance(item, OrderBy):      # <- inserted
        results.append((item, False))  # <- inserted
        continue                       # <- inserted
    results.extend(self.find_ordering_name(item, opts, alias, order, already_seen))
return results
```

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `opts.ordering` (a tuple/list of items) | `List Item` | `tuple`/`list` ↔ `List`; `len` ↔ `.length`; element order preserved; element `i` ↔ index `i` |
| an `OrderBy` element | `Item.expr e` | the `OrderBy` object ↔ `expr e`, where `e : Int` is a stable identity standing in for the object (G-CONF assigns each distinct object a distinct `Int`); content is opaque and unchanged, so only object *identity* is observed |
| a `str` field-name element | `Item.name n` | the lookup string ↔ `name n`, where `n : Int` is the string's identity (distinct strings ↦ distinct `Int`) |
| a resolved entry `(OrderBy(col,…), False)` | `Pair = Expr × Bool` | the resulting `(expr, flag)` tuple ↔ `(e, b)`; `False` ↔ `false` |
| `results.extend(self.find_ordering_name(item, …))` for a `str` item | `resolve n` | the recursive call's returned `list` of entries ↔ `resolve n : List Pair`. The call is UNCHANGED by the patch; both pre- and post-patch invoke it identically on a name item, so it is a free total function, not a contract. |
| `results.append((item, False))` for an `OrderBy` item | `[(e, false)]` (singleton) | `append` of one entry ↔ a one-element `List`; the `item` is carried by identity (`e`), `False` ↔ `false` |
| `results.extend(L)` accumulation | `++` (list concatenation) | `extend` appends in order ↔ `++` right-fold; `append(x)` ≡ `extend([x])` |

The recursion-guard fields (`field.is_relation`, `opts.ordering`, the join/loop
machinery at `compiler.py:715–722`) are NOT modeled: they are the unchanged outer
guard that merely decides *whether* this expansion loop runs at all (it is the
exact same guard pre- and post-patch). The bundle models the loop body — the only
code the patch edits — and the unchanged recursive resolution of a name item is
abstracted into the free `resolve` (the SAME function on both the model and the
G-CONF oracle, so the only thing under differential test is the per-item branch
the patch actually adds).

## 3. Callee provenance

### 3.1 `resolve` — free input, no contract (NOT an axiom)
`resolve : Name → List Pair` models the recursive call
`self.find_ordering_name(item, opts, alias, order, already_seen)` on a *name*
item. The patch does not change this call: pre-patch every item went through it;
post-patch every *non-expression* item still goes through it, unchanged. The
postcondition `out = expandItems resolve items` holds for **every** total
`resolve`, so no `Requires`/`Ensures` is owed on it (directive 7: a free input is
strictly weaker than any concrete callee). There is therefore **no `axiom`** in
this bundle, and **no A-reference deep model** of a library callee — `resolve` is
universally quantified, not pinned. Consequently G-AX has nothing to check
(`axiom_check.py` is a status=skip stub; meta.json `axioms: []`,
`deep_model_references: []`).

### 3.2 Why an order expression is never handed to `resolve`
The behavioural content of the fix: an `OrderBy` element is itself a complete
order expression — it has no field-name string to parse — so it is appended
directly as `(item, False)`. The pre-patch code instead handed it to the
field-name resolution path (`self.find_ordering_name(item, …)`), whose very first
step parses the item as a string (`get_order_dir(name, …)` indexes `name[0]`),
which raises `TypeError` on a non-string `OrderBy` — the reported crash. In the
model this is the `.expr e => [(e, false)]` branch (post-patch) versus
`.expr e => resolve e` (the prepatch skeleton, which routes the expression
through name resolution and so fails the frozen postcondition).

## 4. G-CONF decision (conf_skip = false; seed pinned)

The impl region is R/I (no A-tagged op appears in the computed `out`: `resolve`
is a free function supplied identically to both shadow and oracle, so it is an R
input, not an A callee whose contract is consumed). G-CONF therefore runs
(`conf_skip = false`).

`conformance_check.py` builds the **shadow** = `expandItems`/`itemContribution`
transliterated to Python over the §2 bijection (`Item.expr`/`Item.name` ↔ tagged
synthetic items; `resolve` ↔ a fixed pure closure handed to both sides), and the
**oracle** = the gold-patched loop body transliterated verbatim with its real
control flow:

```python
results = []
for item in ordering:
    if is_orderby(item):            # isinstance(item, OrderBy)
        results.append((expr_id(item), False))
        continue
    results.extend(resolve(name_id(item)))
return results
```

The SAME `resolve` closure is handed to both, so the only thing under
differential test is the per-item `OrderBy` branch the patch adds (mirrors the
django__django-12858 oracle choice: transliterate the patched control flow, not
stand up the ORM, because the recursive resolution is unchanged and standing up a
live model graph + `alias_map` + join machinery merely to read back the list is
the F2P integration test, not a pure R/I shadow). It fuzzes random
specifications mixing `OrderBy` and name items (boundary cases first, incl. the
F2P scenario: a default ordering containing an `OrderBy(F(...))` expression).
`conformance_check.py` seeds its `random.Random` with **`11555`** for a
reproducible verdict. Exit 0 iff zero disagreements.
