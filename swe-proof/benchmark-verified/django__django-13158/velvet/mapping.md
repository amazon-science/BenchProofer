# mapping.md — django__django-13158

## Symbol binding (file:line @ base_commit 7af8f4127397279d19ef7c7899e93018274e2f9b)

| Lean symbol | Python symbol | location |
|---|---|---|
| `emptyCombined` / `silenceAll` (modeled fix) | `django.db.models.sql.query.Query.set_empty` | `django/db/models/sql/query.py:1778-1779` (post-patch adds the operand loop at 1780-1781) |
| `silence b = {b with silenced := true}` | one operand's `set_empty()` (adds `NothingNode` to that operand's `where`) | `django/db/models/sql/query.py:1779` applied per operand |
| `Combined.topSilenced` | the combined query's own `self.where.add(NothingNode(), AND)` | `django/db/models/sql/query.py:1779` |
| `Combined.branches` | `Query.combined_queries` (tuple of operand `Query`s) | initialised `django/db/models/sql/query.py:210`; set in `QuerySet._combinator_query`, `django/db/models/query.py:994` |
| `combinedRows` | the rows a set-combined query yields (drawn from `combined_queries`, not the top-level `where`) | semantics of the compound SQL compiler / `SQLCompiler.get_combinator_sql` |
| (non-modeled, R/I bridge) `emptyCombined` value semantics | `Query.clone` deep-clone of `combined_queries` | `django/db/models/sql/query.py:288`; added line at 308 (post-patch) |

The modeled function is `set_empty`. It is the function whose behavioral CHANGE
is observable through the FAIL_TO_PASS test `test_union_none`: pre-patch,
`QuerySet.none()` on a `union()` queryset returns ALL rows (the operands keep
contributing); post-patch it returns the empty set because `set_empty` now
empties each operand. The coupled `clone` edit (deep-clone the operands) is the
aliasing repair that keeps `.none()` from corrupting the original shared
queryset; in Lean's value semantics that invariant is automatic (see
refinement.md "Coupled aliasing fix"), so `clone` is carried in `patch.diff`
verbatim but not separately modeled.

## The reproduction path (`QuerySet.none()` on a combined queryset)

`django/db/models/query.py`:
```python
def none(self):                       # line 919
    clone = self._chain()             #   -> _clone() -> Query.clone()  (the clone fix)
    clone.query.set_empty()           #   -> Query.set_empty()         (the set_empty fix)
    return clone
```
So `none()` (a) clones the query, then (b) calls `set_empty` on the clone. The
bug needs BOTH halves: without #3 (`set_empty` recursing) the clone still returns
all rows; without the clone deep-copy, `set_empty` mutates the operands SHARED
with the original, corrupting it. The F2P asserts both: `qs3.none() == []` (the
`set_empty` fix, modeled by `emptyCombined`) AND `qs3` still `== [0,1,8,9]` (the
`clone` fix, the directive-5 frame).

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `Query` (a set-combined query) | `Combined` | only the touched observations are carried: `combined_queries` ↔ `branches`; "top-level `where` has a `NothingNode`" ↔ `topSilenced`. |
| operand `Query` in `combined_queries` | `Branch` | `b.rows` ↔ the rows that operand contributes on its own; `b.silenced` ↔ "that operand's `where` has a `NothingNode`" (its row source forced empty). |
| rows a queryset yields (`sorted(o.num for o in qs)`) | `combinedRows branches` (sorted set) | the observable row multiset, compared as a sorted distinct list (UNION is set semantics). For an operand that is `silenced`, `branchRows b = []`. |
| `query.set_empty()` per operand | `silence b` | forces the operand empty, preserving its other state. |
| `clone()` deep-cloning `combined_queries` (no Lean analogue) | value semantics of `emptyCombined : Combined → Combined` | a fresh return value provably cannot mutate the read-only input `q`; G-CONF checks the original queryset is unchanged after `.none()`. |

`set_empty` is total (no precondition); `emptyCombined` quantifies over all
`q : Combined` with no hypotheses. The F2P union is one operand level deep; the
fold `silenceAll` silences every operand identically regardless of count, and a
nested combined operand silences by the same rule (its own `set_empty` recurses).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The empty-propagation is modeled DEEPLY as the
  pure `silenceAll`/`combinedRows` fold over the operand carrier, so there is no
  `axiom`/imperative-stub callee. (Per SPEC_GUIDE §3: a deeply-modeled changed op
  is NOT axiomatized.) Hence `axiom_check.py` is omitted and G-AX skips
  (gates.py: missing `axiom_check.py` ⇒ G-AX `skip`).
- No flag dependency: `set_empty` takes no arguments and its new behavior is
  unconditional (it empties every operand on every call). G-CONF runs the real
  default `union()` configuration.

## G-CONF fuzz seed

Pinned seed: **13158** (see `conformance_check.py` `SEED`). Corpus: every
disjoint low/high split `(num <= lo) | (num >= hi)` of the 0..9 fixture as the
boundary sweep (covers the issue's exact `id<2 | id>5` analogue
`num<=1 | num>=8`), plus randomized disjoint splits to ≥10⁵ evaluations. Each
evaluation builds a fresh `qs1.union(qs2)` over the shared in-memory table and
checks: `qs3.none()` is empty AND `qs3` still yields its full row set
(directive-5 frame / the clone fix).
