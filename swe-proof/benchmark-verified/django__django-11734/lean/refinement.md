# refinement.md — django__django-11734

Operation correspondence between the Lean `implementation_relocateFilterIntoSubquery`
skeleton and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed**
(proof uses an axiom's property), **A-reference** (deep model validated == real
callee by G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the re-anchoring is modeled deeply with
concrete Lean operations. Every row is **R** or **I**. (G-AX is therefore a skip
stub; the R/I legs are differential-tested by G-CONF.)

## What the gold patch changes

The titular, F2P-observable change is the filter-expression rewrite at the head
of `Query.split_exclude` (`django/db/models/sql/query.py:1704-1706`). The patch
inserts a new branch BEFORE the existing `F` branch:

```python
filter_lhs, filter_rhs = filter_expr
if isinstance(filter_rhs, OuterRef):          # NEW
    filter_expr = (filter_lhs, OuterRef(filter_rhs))
elif isinstance(filter_rhs, F):
    filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
```

Because `class OuterRef(F)` (expressions.py:565), at base_commit an `OuterRef`
RHS fell into the `F` branch and was rebuilt as `OuterRef(filter_rhs.name)` — a
fresh level-one outer reference that DROPPED the nesting level the original
`OuterRef` carried, resolving against the wrong query. The new branch wraps the
existing `OuterRef` in another `OuterRef`, adding one level.

The Lean impl models the rewrite with the three-way shape dispatch folded into a
`match` on `FilterRHS`; the `OuterRef` arm adds one level (`outerRef (lvl+1)`),
the `F` arm produces a level-one outer reference (`outerRef 1`), and the literal
arm is unchanged.

## `implementation_relocateFilterIntoSubquery` ↔ `Query.split_exclude` rewrite

| Lean op | patch.diff / base counterpart | tag | note |
|---|---|---|---|
| `let mut newRhs := rhs` | `filter_lhs, filter_rhs = filter_expr` (rhs starts as itself; lhs untouched) | I | accumulator init; default keeps the literal case unchanged |
| `match rhs with \| .outerRef lvl name => newRhs := .outerRef (lvl+1) name` | `if isinstance(filter_rhs, OuterRef): filter_expr = (filter_lhs, OuterRef(filter_rhs))` | R | wrapping an `OuterRef` in another `OuterRef` ↦ `level + 1` (one added boundary, per `OuterRef.resolve_expression`, expressions.py:566-570) |
| `\| .colRef name => newRhs := .outerRef 1 name` | `elif isinstance(filter_rhs, F): filter_expr = (filter_lhs, OuterRef(filter_rhs.name))` | R | `F(name)` rebuilt as a level-one `OuterRef(name)` |
| `\| .value _ => pure ()` | neither branch taken; `filter_expr` keeps its literal RHS | R | a direct literal (no `resolve_expression`) is carried unchanged |
| `return (lhs, newRhs)` | `filter_expr = (filter_lhs, <rewritten rhs>)` | I | the rewritten condition; lhs returned verbatim (frame: directive 5) |

## Prepatch (the real bug)

`Solution_prepatch.lean` collapses the `.outerRef` arm to `outerRef 1 name`
(matching base_commit's `OuterRef(filter_rhs.name)` via the `F` branch), discarding
the existing level. Its carried gold proof fails on the `outerRef` case: the spec
requires `outerRef (lvl+1)` but the impl yields `outerRef 1`, i.e. an unsolvable
`lvl = 0` goal. This is exactly the FAIL_TO_PASS behavior
(`test_subquery_exclude_outerref`): an `OuterRef` inside an `exclude()` must reach
out the extra level to the correct outer query.

## Sibling-site refactors (not separately modeled)

The gold patch also edits two sites that are behavior-preserving for the modeled
observable and not exercised by the F2P beyond enabling the `split_exclude` fix:

- `django/db/models/fields/related_lookups.py:104` — `RelatedLookupMixin.get_prep_lookup`
  changes its guard from `self.rhs_is_direct_value()` to
  `not hasattr(self.rhs, 'resolve_expression')`, so the single-column-relation
  value-normalization branch is skipped for ANY resolvable expression RHS
  (`F`/`OuterRef`), not just direct values. This keeps a carried `OuterRef` from
  being mangled by `get_normalized_value` / `get_prep_value`.
- `django/db/models/fields/__init__.py:2335-2338` — removal of the now-dead
  `AutoField.get_prep_value` override that special-cased `OuterRef`; with the
  guard above skipping expressions upstream, the override is unreachable.

Both are downstream cleanups of the same OuterRef-handling story; they change no
observable the spec models. They are applied verbatim by patch.diff (so the
harness resolves) but carry no Lean op — recorded here as R-free sibling sites.

## Tag summary

- **A-consumed:** none.
- **A-reference:** none.
- **R:** the three-way shape dispatch + the literal pass-through (the type
  refinement `OuterRef nesting depth ↔ outerRef level`).
- **I:** accumulator init and the final tuple return.

Impl region is NOT all-A-tagged ⇒ `conf_skip = false`; the R/I legs are
differential-tested by `conformance_check.py` (G-CONF).
