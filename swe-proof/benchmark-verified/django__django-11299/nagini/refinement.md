# refinement.md — django__django-11299

The operation-by-operation correspondence between `model.py`'s implementation
(the `compile_children` impl region, the deep `leaf_modes` model, and the
`q_pred` tree predicate) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — the recursive child loop of `_add_q`

Gold hunk (`django/db/models/sql/query.py`, body of `_add_q`):
```
             if isinstance(child, Node):
                 child_clause, needed_inner = self._add_q(
                     child, used_aliases, branch_negated,
-                    current_negated, allow_joins, split_subq)
+                    current_negated, allow_joins, split_subq, simple_col)
```

The single changed token is the addition of `simple_col` to the recursive
`_add_q` call: pre-patch the recursive call receives `simple_col=False` (its
default); post-patch it receives the caller's `simple_col`, so the plain-column
mode is forwarded unchanged into every nested group.

| # | model.py impl op (`compile_children`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `head: Optional[QNode]` (the head of `q_object.children`) | the `q_object` whose `.children` `_add_q` iterates | R | a `Q`/`WhereNode` tree ↔ the recursive `QNode` sibling/inner structure; a child list ↔ the `nxt`-chain, a group's children ↔ `inner` (mapping.md §2). |
| A2 | parameter `plain: bool` | `simple_col: bool` | R | identity rename (mapping.md §2). `build_where` calls with `plain=True` ↔ `simple_col=True`. |
| A3 | `if head.kind == 0:` (leaf) vs the group branch | `if isinstance(child, Node):` (group) else leaf (`build_filter`) | R | leaf ↔ non-`Node` child handled by `build_filter`; group ↔ `Node` child handled by the recursive `_add_q` (mapping.md §1). |
| A4 | leaf branch: `result.append(plain)` — one flag at the current mode | `build_filter(child, …, simple_col=simple_col)` → `_get_col(…, simple_col)` returns `SimpleCol` iff `simple_col` | R + I | a leaf contributes exactly one column reference whose form is `SimpleCol` iff the current mode is set; the flag `plain` ↔ `isinstance(col, SimpleCol)` (mapping.md §1, §2). The mode passed to a leaf is the SAME in both patch and prepatch — leaves were never the bug. |
| A5 | group branch: `sub = compile_children(head.inner, plain)` — descend with the SAME mode | `self._add_q(child, …, split_subq, simple_col)` — the recursive call **with `simple_col` appended** (the gold edit) | I | THIS is the line the patch changes. The model forwards `plain` unchanged into the descent; the gold patch forwards `simple_col`. Identical control/data flow: a recursive call on the nested group carrying the mode. |
| A6 | group branch: `tail = compile_children(head.nxt, plain)` — continue the sibling list at the same mode | the loop's continuation to the next `child` of `q_object.children` (the mode is the function's own `simple_col`, unchanged across siblings) | R | iterating `q_object.children` ↔ recursing along the `nxt` chain; the surrounding `simple_col` is constant across the loop body. |
| A7 | `append_all(result, sub); append_all(result, tail)` — concatenate the per-leaf flags in traversal order | `target_clause.add(child_clause, connector)` accumulates each child's compiled `WhereNode` into the result tree, in order | R | the compiled result tree ↔ the ordered per-leaf flag list; only each leaf's column FORM is observed by the F2P test, so accumulation ↔ list concatenation (mapping.md §2). |

The discriminating content of the change — a leaf nested ≥ 1 level deep must
carry the top mode (`SimpleCol`) rather than reset to the default (`Col`) —
lives in step A5 (`compile_children(head.inner, plain)` vs the prepatch's
`compile_children(head.inner, False)`). `model_prepatch.py` reverts exactly A5
(the recursive descent uses `False` instead of `plain`) and **fails** the
postcondition `ToSeq(Result()) == leaf_modes(head, plain)`, which is precisely
the spec sensing the change (G-DIFF). All other regions are byte-identical.

## B. The deep model and the predicate (no consumed axiom)

| # | model.py construct | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| B1 | `leaf_modes(head, plain)` — pure fold: leaf → `PSeq(plain) + leaf_modes(nxt, plain)`; group → `leaf_modes(inner, plain) + leaf_modes(nxt, plain)` | the per-leaf column form produced by the whole `_add_q` traversal | A-reference | the changed traversal is modelled DEEPLY; `leaf_modes` and the verified `compile_children` ARE the per-leaf column-form function. There is **no consumed `@ContractOnly` axiom** — the proof depends on none. The deep model is validated **== the real callee** out-of-band: G-AX (`axiom_check.py`) runs `Query.build_where` on 8 trees of varying depth and asserts every leaf column equals `leaf_modes(tree, True)` (all `SimpleCol`). The crucial clause is that the GROUP case forwards `plain` unchanged — the exact semantic content of the gold edit. |
| B2 | `q_pred` recursive predicate + `q_kind` getter | the structural recursion over `q_object.children` and `isinstance(child, Node)` | R | the linked-tree predicate models the `Node` tree; `Unfold`/`Fold` mirror the structural descent. No repo callee corresponds — pure modeling scaffolding. |
| B3 | `append_all` helper | list accumulation `target_clause.add(...)` | R/I | append-in-order; `ToSeq(result) == Old + ToSeq(src)`. Verification scaffolding for the concatenation in A7; no behavioural content beyond ordered append. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — forwarding the plain-column mode into the recursive descent (A5) —
is modelled **deeply** (the `leaf_modes` group clause and the verified
`compile_children(head.inner, plain)` call), not hidden behind an axiom about
the function under change. There is **no consumed axiom**: the entire change is
pure tree-traversal logic Nagini expresses directly. The deep model is the
**A-reference** that G-AX validates against the real `build_where`.

## D. verify(model) ⇒ resolved

`compile_children` verifies only if its output equals
`leaf_modes(head, plain)`, i.e. only if every leaf — at every nesting depth —
carries the top mode (A5; the group descent must forward `plain`, not reset
it). By R (Q-tree ↔ `QNode`, `simple_col` ↔ `plain`, `SimpleCol`-vs-`Col`
↔ flag) the verified traversal equals the gold `_add_q` with `simple_col`
forwarded into the recursive call. By G-AX the deep model `leaf_modes` equals
the real `build_where` per-leaf column form (A-reference) over trees of every
shape and depth, including the issue's OR-of-AND. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement,
and the gold patch resolves (the F2P `test_simplecol_query` asserts each nested
leaf's `lhs`/`rhs` is a `SimpleCol`; G-RESOLVE). The sole trust point is
refinement fidelity (this document, G-EQ) plus the A-reference soundness check
(G-AX); there is no axiom to trust.
