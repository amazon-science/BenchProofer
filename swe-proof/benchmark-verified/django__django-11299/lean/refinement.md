# refinement.md — django__django-11299

Maps every op in `implementation_resolveColumns` / `resolveChildren` to its
`patch.diff` counterpart in `Query._add_q`. Tags: **R** type refinement,
**A-consumed** proof uses axiom, **A-reference** deep-modeled callee (G-AX),
**I** identical concrete op.

The gold patch is a one-token fix: thread `simple_col` into the recursive
`_add_q` call. The Lean impl is the structural skeleton of that recursive walk;
the relevant op is the recursive descent on a node child.

| # | Lean op (`implementation_resolveColumns` / `resolveChildren`) | patch.diff / `_add_q` counterpart | tag |
|---|---|---|---|
| 1 | match on `QTree`: `.leaf` vs `.node children` | `for child in q_object.children:` with `isinstance(child, Node)` branch vs leaf branch | R (Q-tree node/leaf ↔ `QTree` ctor) |
| 2 | `.node children => .node (resolveChildren bare children)` | build a fresh `target_clause` (WhereNode) and add each lowered child | R (WhereNode ↔ `ColTree.node`) |
| 3 | iterate `child :: rest` in `resolveChildren`, in order | `for child in q_object.children:` (ordered) | I |
| 4 | leaf child: `buildLeaf bare field` | else-branch `build_filter(child, …, simple_col=simple_col)` → `_get_col(…, simple_col)` | A-reference (callee `_get_col`/`SimpleCol`/`Col` unchanged, modeled deeply as `buildLeaf`; no axiom consumed) |
| 5 | **node child: `implementation_resolveColumns bare child`** (THREAD the same `bare`) | **the patched recursive call `self._add_q(child, …, allow_joins, split_subq, simple_col)`** — the added `simple_col` argument | R + the fix site |
| 6 | recurse over `rest` | loop continues to next child | I |

Op #5 is the heart of the fix: the patch adds `simple_col` to the recursive
`_add_q` call so the flag is threaded uniformly. The prepatch
(`Solution_prepatch.lean`) drops it — `implementation_resolveColumns false child`
— exactly mirroring the missing argument defaulting to `simple_col=False`, so
deeply-nested leaves are rendered table-qualified. That is the observable bug.

`buildLeaf` (op #4) is an A-reference: `_get_col` and the `SimpleCol`/`Col`
classes are unchanged by the patch and the per-leaf column-form selection is
modeled deeply (a two-way boolean choice). No `axiom _prop` is consumed, so
`axiom_check.py` is a skip stub (see meta.json `gates.G-AX`).

No changed op is inexpressible; every op is R / A-reference / I.
