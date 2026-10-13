# mapping.md — django__django-13158

## Symbol binding (file:line @ base_commit 7af8f41)
| Lean symbol | Python symbol | file:line @ base | role |
|---|---|---|---|
| `implementation_makeEmpty` / `problem_spec_makeEmpty` / `correct_makeEmpty` | `Query.set_empty` | `django/db/models/sql/query.py:1778-1779` (post-patch `:1778-1781`) | the modeled changed function |
| `Query` (inductive) | `django.db.models.sql.query.Query` (the touched facets only) | `query.py` | the rich object under spec |
| `Query.selfEmpty : Bool` | "this query's own WHERE has been forced to match nothing", i.e. `is_empty()` would see a `NothingNode` among `self.where.children` | `query.py:1781-1782` (`is_empty`), `:1779` (`where.add(NothingNode(), AND)`) | the single touched fact per node |
| `Query.combined : List Query` | `self.combined_queries` (a tuple of `Query`) | `query.py:210` (init `= ()`), `:308` (deep-copied in `clone`, post-patch) | the sub-queries combined into this node's result (e.g. a `union()`) |
| `implementation_makeEmpty sub` (the recursive self-call) | `query.set_empty()` on each `query in self.combined_queries` | post-patch `query.py:1780-1781` | the fix: recurse into each combined sub-query |

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean | bijection |
|---|---|---|
| a `Query` object | `Query.mk selfEmpty combined` | `selfEmpty` ↔ "`is_empty()` is true for this node's own where" (a `NothingNode` is among `where.children`); `combined` ↔ `tuple(self.combined_queries)` as an ordered list |
| `self.combined_queries == ()` (leaf) | `combined = []` | empty list |
| `q.set_empty()` mutating `q` in place | `implementation_makeEmpty q` returning the updated tree | mutation modeled as a pure rebuild (Lean is referentially transparent — see refinement.md "aliasing note") |
| `is_empty()` over the whole combined tree | `YieldsNothing q` | a node returns no rows iff its own where is empty AND every combined sub-query returns no rows, recursively |
| the combination structure (nesting of `combined_queries`) | `toShape q` | erases `selfEmpty`, keeps the nested child-count structure |

### Why a `Query` node's only observable field is `selfEmpty`
`set_empty` touches exactly one piece of per-node state: it appends a
`NothingNode` to `self.where` (so `is_empty()` becomes true for that node). The
patch adds a second effect — doing the same to every node in
`self.combined_queries`, recursively. Every other field of `Query` is irrelevant
to the empty-result guarantee, so the model carries only `selfEmpty : Bool` plus
the `combined` children. The `clone` hunk (deep-copying `combined_queries`) is the
aliasing-safety half of the fix; under the no-aliasing Lean model it is automatic
(see refinement.md).

## Callee provenance + flag deps
- No unchanged callee is consumed as a `_prop` axiom. `where.add(NothingNode(),
  AND)` (the per-node "force empty") is modeled deeply as `selfEmpty := true`;
  the recursion is a self-call. So `axioms = []`, `deep_model_references = []`.
- No flag dependency: `set_empty` takes no flags; the recursion is unconditional
  over `self.combined_queries`.

## G-CONF fuzz seed
Pinned seed: **13158** (used by `conformance_check.py`).
