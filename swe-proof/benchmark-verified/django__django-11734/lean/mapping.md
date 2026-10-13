# mapping.md — django__django-11734

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`999891bd80b3d02dd916731a7a239e1036174885`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_relocateFilterIntoSubquery` / `problem_spec_relocateFilterIntoSubquery` / `correct_relocateFilterIntoSubquery` | the filter-expression rewrite at the head of `Query.split_exclude` | `django/db/models/sql/query.py:1704-1706` |
| `reanchor` (spec helper) | the per-RHS dispatch the rewrite performs (`F` → `OuterRef(name)`, post-patch `OuterRef` → `OuterRef(outerref)`) | `django/db/models/sql/query.py:1705-1706` (base) / patched hunk |
| `FilterRHS.value` | a direct literal value RHS (no `resolve_expression`) | n/a |
| `FilterRHS.colRef` | an `F` expression RHS (same-query column reference) | `django/db/models/expressions.py:516` (`class F`) |
| `FilterRHS.outerRef` | an `OuterRef` expression RHS (outer-query reference, nesting level) | `django/db/models/expressions.py:565` (`class OuterRef`) |

## The observable behavior

`Query.split_exclude` builds an auxiliary nested subquery to evaluate a negated
filter over an N-to-many relation. Its first action is to re-anchor the filter
condition's right-hand side so it still resolves against the intended query once
the condition has been pushed one query boundary deeper.

At `base_commit`:

```python
filter_lhs, filter_rhs = filter_expr
if isinstance(filter_rhs, F):
    filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
```

The gold patch adds an explicit prior branch:

```python
if isinstance(filter_rhs, OuterRef):
    filter_expr = (filter_lhs, OuterRef(filter_rhs))
elif isinstance(filter_rhs, F):
    filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
```

### Why the base branch is wrong (the "wrong model" bug)

`class OuterRef(F)` — an outer-query reference IS a subclass of a column
reference (`django/db/models/expressions.py:565`). So at `base_commit` an
`OuterRef` RHS satisfies `isinstance(filter_rhs, F)` and is rebuilt as
`OuterRef(filter_rhs.name)` — a fresh **level-one** outer reference that
**discards** the level the original `OuterRef` already carried.

`OuterRef.resolve_expression` (`expressions.py:566-570`) shows the nesting
semantics: when an `OuterRef` is wrapped in another `OuterRef`, resolving the
outer one returns the inner `OuterRef` (peeling one level), so each wrapping adds
exactly one boundary the reference must cross outward. The post-patch
`OuterRef(filter_rhs)` therefore *adds one level* to the existing reference;
the base `OuterRef(filter_rhs.name)` *resets it to one level*. Since the subquery
that `split_exclude` builds is itself nested inside the original outer query, the
relocated `OuterRef('pk')` needs to reach out **two** levels, not one — exactly
the failure the issue reports ("OuterRef resolves to V0.id instead of
queries_number.id"; `ValueError: … reference to an outer query …`).

### The two supporting hunks (behavior-preserving for the modeled observable)

The gold patch also touches two other sites. Both are guard-condition refactors
that make the single-column-relation normalization branch skip ANY expression
RHS (not just direct values), so that an `OuterRef` carried through is not
mangled by value normalization:

- `django/db/models/fields/related_lookups.py:104` — `RelatedLookupMixin.get_prep_lookup`:
  `self.rhs_is_direct_value()` (`= not hasattr(self.rhs, 'as_sql')`,
  `django/db/models/lookups.py:98-99`) is replaced by
  `not hasattr(self.rhs, 'resolve_expression')`. An `OuterRef`/`F` has
  `resolve_expression` (`expressions.py:529, 566`), so the normalization branch
  is now skipped for them. Both predicates already excluded direct values from
  the *expression* case in the same direction for the modeled observable; this
  tightens the skip to all resolvable expressions.
- `django/db/models/fields/__init__.py:2335-2338` — removal of
  `AutoField.get_prep_value`, an override that special-cased `OuterRef` by
  returning it unprepped. With the `related_lookups.py` guard now skipping
  expressions before `get_prep_value` is ever reached for them, the override is
  dead and removed.

Neither supporting hunk changes the re-anchoring observable that the F2P test
exercises; they remove the now-redundant `OuterRef` special-casing downstream of
the `split_exclude` fix. They are recorded as A-reference-free sibling-site
refactors in refinement.md and are not separately modeled. patch.diff applies all
three hunks verbatim so the harness resolves.

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| `filter_expr` = `(filter_lhs, filter_rhs)` | `(lhs : String, rhs : FilterRHS)` | left-hand side carried as an opaque name; RHS modeled by shape |
| direct literal RHS (no `resolve_expression`) | `FilterRHS.value (v : Int)` | a representative literal payload |
| `F(name)` RHS | `FilterRHS.colRef name` | same-query column reference |
| `OuterRef(...)` with nesting depth `k` | `FilterRHS.outerRef (level := k) name` | `level` = how many query boundaries outward the reference reaches (`≥ 1`); wrapping in another `OuterRef` ↦ `level + 1` |
| `OuterRef(filter_rhs.name)` (base, `F` branch) | `outerRef 1 name` | rebuilds at level one, dropping any prior level |
| `OuterRef(filter_rhs)` (patched, `OuterRef` branch) | `outerRef (lvl+1) name` | adds one level to the existing reference |
| relocated `filter_expr` returned | `result : String × FilterRHS` | `(lhs unchanged, reanchored rhs)` |

`reanchor` is the POST-patch (correct/desired) rewrite: literal unchanged,
column reference → level-one outer reference, existing outer reference →
one-further-level outer reference. It lives in the spec view (it is the behavior
the issue demands, stated abstractly — no patched symbol named). The buggy
per-shape dispatch that the *implementation* performs lives in the impl region,
so the prepatch encodes the base_commit behavior (an existing outer reference is
collapsed to level one) without altering the frozen spec.

## Callee provenance / flag deps

- No UNCHANGED callee needs an axiom. The re-anchoring is modeled DEEPLY with
  concrete Lean operations (a three-way shape match and a `level + 1`
  adjustment). → `axioms` region is EMPTY; `axiom_check.py` is a skip stub.
- `Query(self.model)`, `add_filter`, `trim_start`, `build_filter`, etc. (the
  remainder of `split_exclude` that consumes the rewritten `filter_expr`) are
  unchanged by the patch and orthogonal to the re-anchoring observable; they are
  abstracted out of the modeled state.
- No flag dependency: the dispatch is purely on the RHS shape
  (`isinstance(filter_rhs, OuterRef)` / `isinstance(filter_rhs, F)`).

## G-CONF fuzz seed

Pinned seed: **20240625**. `conformance_check.py` builds the Python shadow of the
re-anchoring (transliteration of `reanchor`/`implementation_…`) and diffs it
against the REAL patched `split_exclude` rewrite — exercised in-container by
constructing `OuterRef`/`F`/literal RHS values, running the patched branch logic,
and observing the nesting depth of the resulting `OuterRef` (via repeated
`resolve_expression`) — over the full discrete shape matrix plus ≥10⁵ randomized
draws over `(shape, level, name/value)`.
